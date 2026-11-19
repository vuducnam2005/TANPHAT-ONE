"""Unified read-only HR workspace for internal employees (HR-UNIFIED-READONLY-UI-001).

Employees without an HR group keep the exact same visual workspace, overview,
grouped list (custom department & employee order), filter bar and profile
layout as administrators, strictly backed by the native ``hr.employee.public``
projection. Nothing here grants an HR group or uses ``sudo()`` to leak
private, contract, history or account data.
"""
from odoo import api, fields, models
from odoo.exceptions import AccessError, RedirectWarning, ValidationError

HR_GROUP = 'hr.group_hr_user'
_PUBLIC_FILTER_KEYS = frozenset({'department_id', 'job_id'})
_PUBLIC_EXTRA_FIELDS = frozenset({'department_id', 'job_id'})


def is_hr_officer(env):
    return env.su or env.user.has_group(HR_GROUP)


def _parse_optional_positive_id(env, value, label):
    if value in (None, False, ''):
        return None
    try:
        if isinstance(value, bool) or str(int(value)) != str(value) or int(value) <= 0:
            raise ValueError  # noqa: TRY301 - localized filter validation
        return int(value)
    except (ValueError, TypeError) as exc:
        raise ValidationError(env._('%s không hợp lệ.', label)) from exc


class HrWorkspaceDirectory(models.AbstractModel):
    _inherit = 'tp.hr.workspace'

    @api.model
    def _tp_entry_action(self):
        """TP HR entry: HR opens full overview; other internal employees open public read-only overview."""
        xmlid = (
            'tp_hr_workspace.action_overview'
            if is_hr_officer(self.env)
            else 'tp_hr_workspace.action_public_overview'
        )
        return self.env['ir.actions.actions']._for_xml_id(xmlid)

    @api.model
    def _public_population(self, filters=None):
        """Strict read-only population on ``hr.employee.public`` with caller's own access."""
        if not self.env.user._is_internal():
            raise AccessError(self.env._('Chỉ nhân viên nội bộ mới được xem không gian nhân sự.'))
        filters = filters or {}
        if not isinstance(filters, dict) or set(filters) - _PUBLIC_FILTER_KEYS:
            raise ValidationError(self.env._('Bộ lọc nhân sự không hợp lệ.'))
        public_employees = self.env['hr.employee.public'].sudo(False)
        public_employees.check_access('read')
        domain = [('company_id', '=', self.env.company.id), ('active', '=', True)]
        for field_name, model_name, label in (
            ('department_id', 'hr.department', 'Đơn vị'),
            ('job_id', 'hr.job', 'Chức vụ'),
        ):
            rec_id = _parse_optional_positive_id(self.env, filters.get(field_name), label)
            if rec_id is None:
                continue
            record = self.env[model_name].sudo(False).browse(rec_id).exists()
            record.check_access('read')
            if not record or record.company_id not in (self.env.company, self.env['res.company']):
                raise AccessError(self.env._('%s nằm ngoài công ty đang xem.', label))
            domain.append((field_name, '=', rec_id))
        return public_employees, domain

    @api.model
    def get_public_overview(self, filters=None):
        """Return only permitted public headcount & org structure metrics (no accounts/contracts/private data)."""
        employees, domain = self._public_population(filters)
        total = employees.search_count(domain)
        groups = employees._read_group(domain, ['department_id'], ['__count'])
        dept_records = self.env['hr.department'].sudo(False).search(
            [('company_id', 'in', [False, self.env.company.id]), ('active', '=', True)],
            order='tp_sequence, id',
        )
        dept_rank = {dept.id: (dept.tp_sequence, dept.id) for dept in dept_records}
        departments = [
            {
                'id': department.id or 0,
                'name': department.name if department else 'Chưa khai báo đơn vị',
                'count': count,
                'percent': count / total * 100 if total else 0,
            }
            for department, count in groups
        ]
        departments.sort(
            key=lambda row: (
                not bool(row['id']),
                dept_rank.get(row['id'], (999999, row['id']))[0],
                dept_rank.get(row['id'], (999999, row['id']))[1],
                row['name'].casefold(),
            ),
        )
        job_groups = employees._read_group(domain, ['job_id'], ['__count'])
        jobs = [
            {
                'id': job.id or 0,
                'name': job.name if job else 'Chưa khai báo chức vụ',
                'count': count,
                'percent': count / total * 100 if total else 0,
            }
            for job, count in job_groups
        ]
        jobs.sort(key=lambda row: (-row['count'], row['name'].casefold(), row['id']))
        job_records = self.env['hr.job'].sudo(False).search(
            [('company_id', 'in', [False, self.env.company.id]), ('active', '=', True)],
            order='name, id',
        )
        return {
            'readonly': True,
            'total': total,
            'units': sum(bool(row['id']) for row in departments),
            'departments': departments,
            'jobs': jobs,
            'catalog_departments': [{'id': d.id, 'name': d.name} for d in dept_records],
            'catalog_jobs': [{'id': j.id, 'name': j.name} for j in job_records],
            'can_create': False,
            'can_export': False,
            'updated_at': fields.Datetime.context_timestamp(
                self.with_context(tz=self.env.context.get('tz') or self.env.user.tz or 'Asia/Ho_Chi_Minh'),
                fields.Datetime.now(),
            ).strftime('%d/%m/%Y %H:%M %Z'),
        }

    @api.model
    def action_public_employees(self, filters=None, extra_domain=None):
        """Open the read-only unified employee list scoped strictly to validated public criteria."""
        _employees, domain = self._public_population(filters)
        validated_extra = []
        if extra_domain is not None:
            if not isinstance(extra_domain, list):
                raise ValidationError(self.env._('Bộ lọc danh sách không hợp lệ.'))
            for item in extra_domain:
                if not isinstance(item, (list, tuple)) or len(item) != 3:
                    raise ValidationError(self.env._('Bộ lọc danh sách không hợp lệ.'))
                field_name, operator, raw_value = item
                if field_name not in _PUBLIC_EXTRA_FIELDS or operator != '=':
                    raise ValidationError(self.env._('Trường lọc không được phép trong chế độ chỉ xem.'))
                if raw_value is False:
                    validated_extra.append((field_name, '=', False))
                else:
                    label = 'Đơn vị' if field_name == 'department_id' else 'Chức vụ'
                    rec_id = _parse_optional_positive_id(self.env, raw_value, label)
                    model_name = 'hr.department' if field_name == 'department_id' else 'hr.job'
                    rec = self.env[model_name].sudo(False).browse(rec_id).exists()
                    rec.check_access('read')
                    if not rec or rec.company_id not in (self.env.company, self.env['res.company']):
                        raise AccessError(self.env._('%s nằm ngoài công ty đang xem.', label))
                    validated_extra.append((field_name, '=', rec_id))
        action = self.env['ir.actions.actions']._for_xml_id('tp_hr_workspace.action_directory')
        action.update(
            domain=domain + validated_extra,
            context={
                'tp_filter_profile': 'directory',
                'tp_hr_leaf': 'tp_hr_workspace.menu_directory',
            },
        )
        return action


class HrEmployeePublicDirectory(models.Model):
    _inherit = 'hr.employee.public'

    tp_search_identity = fields.Char(
        string='Họ tên hoặc mã nhân viên',
        compute='_compute_tp_search_identity',
        search='_search_tp_search_identity',
    )

    def _compute_tp_search_identity(self):
        for rec in self:
            rec.tp_search_identity = ''

    def _search_tp_search_identity(self, operator, value):
        if operator not in ('ilike', 'not ilike', '=', '!=', 'like', 'not like'):
            return NotImplemented
        if not value:
            return [(1, '=', 1)] if operator in ('ilike', 'like', '!=') else [(0, '=', 1)]
        if operator in ('not ilike', 'not like', '!='):
            return ['&', ('name', operator, value), ('tp_employee_code', operator, value)]
        return ['|', ('name', operator, value), ('tp_employee_code', operator, value)]

    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_is_user(self):
        """Identify 'own profile' strictly by linked employee ID and user ID, never by name or login."""
        own = self.env.user._tp_main_employee()
        own_id = own.id if own else 0
        uid = self.env.uid
        for employee in self:
            employee.is_user = bool(own_id and employee.id == own_id and employee.user_id.id == uid)

    def action_tp_open_my_profile(self):
        self.ensure_one()
        own = self.env.user._tp_main_employee()
        if not own or self.id != own.id or self.user_id.id != self.env.uid:
            raise AccessError(self.env._('Bạn chỉ được mở Hồ sơ cá nhân của chính mình.'))
        return self.env['ir.actions.actions']._for_xml_id('tp_hr_workspace.action_my_profile')

    def export_data(self, fields_to_export):
        # Colleagues may be viewed, not bulk-exported (native button and direct RPC alike).
        if not is_hr_officer(self.env):
            raise AccessError(self.env._('Danh sách nhân viên ở chế độ chỉ xem; chỉ nhân sự được giao mới được xuất danh sách.'))
        return super().export_data(fields_to_export)


class HrEmployeeDirectoryRedirect(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_views(self, views, options=None):
        if not self.browse().has_access('read'):
            action = self.env.ref('tp_hr_workspace.action_directory', raise_if_not_found=False)
            if action:
                raise RedirectWarning(
                    message=self.env._('Tài khoản đang ở chế độ chỉ xem. Chuyển sang Danh sách nhân viên.'),
                    action=action.id,
                    button_text=self.env._('Mở Danh sách nhân viên'),
                )
        return super().get_views(views, options)


class IrUiMenuDirectory(models.Model):
    _inherit = 'ir.ui.menu'

    def _visible_menu_ids(self, debug=False):
        ids = set(super()._visible_menu_ids(debug))
        if self.env.user.has_group(HR_GROUP):
            # HR already has the full overview & employee list; read-only entries are for everybody else.
            for xmlid in ('tp_hr_workspace.menu_directory', 'tp_hr_workspace.menu_public_overview'):
                menu = self.env.ref(xmlid, raise_if_not_found=False)
                if menu:
                    ids.discard(menu.id)
        return ids


class IrHttpDirectory(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        if self.env.user._is_internal():
            result['tp_hr_readonly'] = not self.env.user.has_group(HR_GROUP)
        return result
