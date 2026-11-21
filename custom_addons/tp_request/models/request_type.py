# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Request types and sequential approval route configuration."""
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .request_common import (
    APPROVAL_POLICIES,
    APPROVER_RULES,
    EXECUTOR_MODES,
    HANDLER_KINDS,
    PRIORITIES,
    SUBMITTER_SCOPES,
    active_internal_users,
    live_admin_users,
    require_request_manager,
)


class TpRequestType(models.Model):
    _name = 'tp.request.type'
    _description = 'Loại đề nghị & cấu hình quy trình'
    _order = 'sequence, id'

    code = fields.Char(string='Mã loại', required=True, index=True, copy=False)
    name = fields.Char(string='Tên loại đề nghị', required=True, index=True)
    description = fields.Text(string='Mô tả mục đích')
    guidance = fields.Text(string='Hướng dẫn điền')
    icon = fields.Char(string='Biểu tượng', default='assignment', required=True)
    color = fields.Char(string='Màu nhận diện', default='#2563EB', required=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    active = fields.Boolean(string='Đang hoạt động', default=True, index=True)
    company_id = fields.Many2one('res.company', string='Công ty áp dụng', ondelete='restrict', index=True,
                                 help='Để trống để áp dụng cho mọi công ty.')
    config_version = fields.Integer(string='Phiên bản cấu hình', default=1, readonly=True, copy=False)

    handler_kind = fields.Selection(HANDLER_KINDS, string='Loại nghiệp vụ', required=True, default='general')
    submitter_scope = fields.Selection(SUBMITTER_SCOPES, string='Đối tượng được gửi', required=True, default='all_internal')
    allowed_department_ids = fields.Many2many(
        'hr.department', 'tp_req_type_dept_rel', 'type_id', 'department_id', string='Phòng ban được phép gửi',
    )
    allowed_user_ids = fields.Many2many(
        'res.users', 'tp_req_type_user_rel', 'type_id', 'user_id', string='Người dùng được phép gửi',
        domain=[('share', '=', False), ('active', '=', True)],
    )

    require_reason = fields.Boolean(string='Bắt buộc nội dung / lý do', default=True)
    require_attachment = fields.Boolean(string='Bắt buộc tệp đính kèm', default=False)
    allow_attachment = fields.Boolean(string='Cho phép đính kèm tệp', default=True)
    max_attachments = fields.Integer(string='Số tệp tối đa', default=10)
    require_needed_date = fields.Boolean(string='Bắt buộc ngày cần đáp ứng', default=False)
    show_project_field = fields.Boolean(string='Hiển thị chọn Dự án liên quan', default=False)
    allow_reject = fields.Boolean(string='Cho phép từ chối', default=True)
    allow_return = fields.Boolean(string='Cho phép trả lại bổ sung', default=True)
    allow_withdraw = fields.Boolean(string='Cho phép người gửi rút đề nghị', default=True)

    sla_hours = fields.Float(string='Thời hạn xử lý mặc định (giờ làm việc)', default=24.0)
    default_priority = fields.Selection(PRIORITIES, string='Độ ưu tiên mặc định', default='normal', required=True)

    requires_execution = fields.Boolean(string='Có bước thực hiện sau duyệt', default=False)
    executor_mode = fields.Selection(EXECUTOR_MODES, string='Cách xác định người thực hiện', required=True, default='none')
    executor_user_ids = fields.Many2many(
        'res.users', 'tp_req_type_exec_user_rel', 'type_id', 'user_id', string='Người thực hiện cụ thể',
        domain=[('share', '=', False), ('active', '=', True)],
    )
    executor_department_id = fields.Many2one('hr.department', string='Bộ phận thực hiện', ondelete='set null')

    step_ids = fields.One2many('tp.request.type.step', 'type_id', string='Tuyến duyệt tuần tự', copy=True)
    request_count = fields.Integer(string='Số hồ sơ đã lập', compute='_compute_request_count')
    is_config_ready = fields.Boolean(string='Sẵn sàng sử dụng', compute='_compute_config_status')
    config_warning = fields.Text(string='Cảnh báo thiếu cấu hình', compute='_compute_config_status')

    _code_company_unique = models.UniqueIndex(
        '(COALESCE(company_id, 0), upper(btrim(code)))',
        'Mã loại đề nghị đã tồn tại trong phạm vi công ty.',
    )

    @api.constrains('code', 'sla_hours', 'max_attachments')
    def _check_basics(self):
        for rec in self:
            if not (rec.code or '').strip():
                raise ValidationError(_('Mã loại đề nghị không được để trống.'))
            if rec.sla_hours < 0:
                raise ValidationError(_('Thời hạn xử lý không được âm.'))
            if rec.max_attachments < 0 or rec.max_attachments > 50:
                raise ValidationError(_('Số tệp đính kèm tối đa phải từ 0 đến 50.'))

    @api.constrains('requires_execution', 'executor_mode')
    def _check_executor_mode(self):
        for rec in self:
            if rec.requires_execution and rec.executor_mode == 'none':
                raise ValidationError(_('Loại đề nghị có bước thực hiện sau duyệt phải chọn cách xác định người thực hiện.'))

    def _compute_request_count(self):
        counts = dict(
            self.env['tp.request'].sudo()._read_group(
                [('type_id', 'in', self.ids)], ['type_id'], ['__count'],
            )
        )
        for rec in self:
            rec.request_count = counts.get(rec, 0)

    def _compute_config_status(self):
        company = self.env.company
        for rec in self:
            warnings = rec._tp_static_config_warnings(company=company)
            rec.config_warning = '\n'.join(warnings) if warnings else False
            rec.is_config_ready = not bool(warnings)

    def _tp_static_config_warnings(self, company=None):
        """Return list of configuration gaps visible to Admin (without guessing any person)."""
        self.ensure_one()
        company = company or self.company_id or self.env.company
        warnings = []
        steps = self.step_ids.sorted(lambda s: (s.sequence, s.id))
        if not steps:
            warnings.append(_('Chưa cấu hình bước duyệt nào.'))
        for idx, step in enumerate(steps, start=1):
            if step.approver_rule == 'specific_users':
                valid = active_internal_users(step.approver_user_ids, company=company)
                if not valid:
                    warnings.append(_('Bước %(idx)s (%(name)s): chưa chọn người duyệt cụ thể đang hoạt động.', idx=idx, name=step.name))
            elif step.approver_rule == 'admin_group':
                admins = live_admin_users(self.env, company=company)
                if not admins:
                    warnings.append(_('Bước %(idx)s (%(name)s): công ty chưa có Admin gốc hoặc Admin ủy quyền hiệu lực.', idx=idx, name=step.name))
            elif step.approver_rule == 'department_manager':
                depts = self.env['hr.department'].sudo().search([('company_id', '=', company.id), ('active', '=', True)])
                missing = depts.filtered(lambda d: not (d.manager_id and d.manager_id.user_id and d.manager_id.user_id.active and not d.manager_id.user_id.share))
                if missing:
                    warnings.append(_(
                        'Bước %(idx)s (%(name)s): %(miss)s/%(total)s phòng ban chưa gắn Trưởng phòng có tài khoản hoạt động (phòng thiếu sẽ bị chặn gửi).',
                        idx=idx, name=step.name, miss=len(missing), total=len(depts),
                    ))
            elif step.approver_rule == 'direct_manager':
                emps = self.env['hr.employee'].sudo().search([('company_id', '=', company.id), ('active', '=', True), ('user_id', '!=', False)])
                missing = emps.filtered(lambda e: not (e.parent_id and e.parent_id.user_id and e.parent_id.user_id.active and not e.parent_id.user_id.share))
                if missing:
                    warnings.append(_(
                        'Bước %(idx)s (%(name)s): %(miss)s/%(total)s nhân viên có tài khoản chưa khai báo Quản lý trực tiếp có tài khoản.',
                        idx=idx, name=step.name, miss=len(missing), total=len(emps),
                    ))
        if self.requires_execution:
            executors = self._tp_resolve_executors(company=company)
            if not executors:
                warnings.append(_('Chưa xác định được người thực hiện sau duyệt cho loại đề nghị này.'))
        return warnings

    def _tp_user_can_submit(self, user, employee=None):
        """Check whether user is allowed to submit this request type."""
        self.ensure_one()
        user = user.sudo().with_context(active_test=False)
        if not self.active or not user.active or user.share or not user.has_group('base.group_user'):
            return False
        if self.submitter_scope == 'all_internal':
            return True
        if self.submitter_scope == 'users':
            return user in self.allowed_user_ids
        if self.submitter_scope == 'departments':
            emp = employee or self.env['hr.employee'].sudo().search([
                ('user_id', '=', user.id), ('company_id', '=', (self.company_id or self.env.company).id),
            ], limit=1)
            return bool(emp and emp.department_id and emp.department_id in self.allowed_department_ids)
        return False

    def _tp_resolve_executors(self, company=None):
        """Resolve authorized post-approval executors strictly from configured data."""
        self.ensure_one()
        if not self.requires_execution or self.executor_mode == 'none':
            return self.env['res.users']
        company = company or self.company_id or self.env.company
        if self.executor_mode == 'admin_group':
            return live_admin_users(self.env, company=company)
        if self.executor_mode == 'specific_users':
            return active_internal_users(self.executor_user_ids, company=company)
        if self.executor_mode == 'department_members' and self.executor_department_id:
            emps = self.env['hr.employee'].sudo().search([
                ('department_id', '=', self.executor_department_id.id),
                ('company_id', '=', company.id),
                ('active', '=', True),
                ('user_id', '!=', False),
            ])
            return active_internal_users(emps.mapped('user_id'), company=company)
        return self.env['res.users']

    def _tp_resolve_route_preview(self, requester_user, company=None, employee=None, project=None):
        """Resolve every sequential step for a specific requester/employee/project.

        Never guesses from job_title text and never picks a random real person.
        Removes requester_user from eligible approvers to enforce anti-self-approval.
        """
        self.ensure_one()
        company = company or self.company_id or self.env.company
        requester = requester_user.sudo().with_context(active_test=False)
        if employee is None:
            employee = self.env['hr.employee'].sudo().search([
                ('user_id', '=', requester.id),
                ('company_id', '=', company.id),
            ], limit=1)
        else:
            employee = employee.sudo()

        steps_data = []
        missing_steps = []
        ordered_steps = self.step_ids.sorted(lambda s: (s.sequence, s.id))
        if not ordered_steps:
            missing_steps.append(_('Loại đề nghị chưa có bước duyệt nào được cấu hình.'))

        for idx, step in enumerate(ordered_steps, start=1):
            users, missing_reason = step._tp_resolve_approvers(
                requester=requester, employee=employee, company=company, project=project,
            )
            # Enforce anti-self-approval: requester can never approve their own request
            self_excluded = requester in users
            eligible = users - requester
            if not eligible and not missing_reason:
                if self_excluded:
                    missing_reason = _(
                        'Người duyệt cấu hình trùng với người gửi (%(name)s). Hệ thống không cho phép tự duyệt và không tự thay thế người duyệt.',
                        name=requester.name,
                    )
                else:
                    missing_reason = _('Chưa xác định được người duyệt hợp lệ cho bước này.')
            if missing_reason:
                missing_steps.append(f'Bước {idx} ({step.name}): {missing_reason}')
            steps_data.append({
                'step_template_id': step.id,
                'sequence': step.sequence,
                'order': idx,
                'name': step.name,
                'approver_rule': step.approver_rule,
                'approver_rule_label': dict(APPROVER_RULES).get(step.approver_rule, step.approver_rule),
                'approval_policy': step.approval_policy,
                'approval_policy_label': dict(APPROVAL_POLICIES).get(step.approval_policy, ''),
                'sla_hours': step.sla_hours or self.sla_hours or 24.0,
                'can_return': bool(step.can_return and self.allow_return),
                'can_reject': bool(step.can_reject and self.allow_reject),
                'approver_ids': eligible.ids,
                'approvers': [{'id': u.id, 'name': u.name} for u in eligible],
                'missing_reason': missing_reason or '',
                'ready': not bool(missing_reason),
            })

        executors = self._tp_resolve_executors(company=company)
        exec_missing = ''
        if self.requires_execution and not executors:
            exec_missing = _('Chưa cấu hình người thực hiện hợp lệ sau phê duyệt.')
            missing_steps.append(exec_missing)

        return {
            'type_id': self.id,
            'config_version': self.config_version,
            'steps': steps_data,
            'requires_execution': self.requires_execution,
            'executor_mode': self.executor_mode,
            'executor_mode_label': dict(EXECUTOR_MODES).get(self.executor_mode, ''),
            'executor_ids': executors.ids,
            'executors': [{'id': u.id, 'name': u.name} for u in executors],
            'executor_missing': exec_missing,
            'can_submit': not bool(missing_steps),
            'missing_reasons': missing_steps,
        }

    # ------------------------------------------------------------------ ORM guards
    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            require_request_manager(self.env)
        for vals in vals_list:
            if vals.get('code'):
                vals['code'] = vals['code'].strip().upper()
            vals['config_version'] = 1
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su:
            require_request_manager(self.env)
        vals = dict(vals)
        if vals.get('code'):
            vals['code'] = vals['code'].strip().upper()
        # Bump config_version on substantive config change (never mutates already-submitted requests)
        versioned_keys = {
            'name', 'handler_kind', 'submitter_scope', 'allowed_department_ids', 'allowed_user_ids',
            'require_reason', 'require_attachment', 'require_needed_date', 'show_project_field',
            'allow_reject', 'allow_return', 'allow_withdraw', 'sla_hours', 'requires_execution',
            'executor_mode', 'executor_user_ids', 'executor_department_id', 'step_ids',
        }
        if versioned_keys & set(vals) and 'config_version' not in vals:
            for rec in self:
                super(TpRequestType, rec).write(dict(vals, config_version=rec.config_version + 1))
            return True
        return super().write(vals)

    def unlink(self):
        raise AccessError(_('Không xóa loại đề nghị để giữ toàn vẹn hồ sơ lịch sử. Hãy chuyển sang "Ngừng sử dụng".'))


class TpRequestTypeStep(models.Model):
    _name = 'tp.request.type.step'
    _description = 'Bước duyệt trong loại đề nghị'
    _order = 'type_id, sequence, id'

    type_id = fields.Many2one('tp.request.type', string='Loại đề nghị', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(string='Thứ tự bước', default=10, required=True)
    name = fields.Char(string='Tên bước duyệt', required=True)
    approver_rule = fields.Selection(APPROVER_RULES, string='Quy tắc xác định người duyệt', required=True, default='specific_users')
    approver_user_ids = fields.Many2many(
        'res.users', 'tp_req_step_user_rel', 'step_id', 'user_id', string='Người duyệt cụ thể',
        domain=[('share', '=', False), ('active', '=', True)],
    )
    approval_policy = fields.Selection(APPROVAL_POLICIES, string='Cơ chế duyệt nhiều người', required=True, default='any_one')
    sla_hours = fields.Float(string='Hạn xử lý bước (giờ làm việc)', default=24.0)
    can_return = fields.Boolean(string='Được trả lại bổ sung', default=True)
    can_reject = fields.Boolean(string='Được từ chối', default=True)

    @api.constrains('sla_hours')
    def _check_sla(self):
        for rec in self:
            if rec.sla_hours < 0:
                raise ValidationError(_('Hạn xử lý bước duyệt không được âm.'))

    def _tp_resolve_approvers(self, requester, employee, company, project=None):
        """Return (res.users recordset, missing_reason_str) strictly from valid structured data."""
        self.ensure_one()
        Users = self.env['res.users']
        rule = self.approver_rule

        if rule == 'specific_users':
            users = active_internal_users(self.approver_user_ids, company=company)
            if not users:
                return Users, _('Chưa cấu hình người duyệt cụ thể cho bước này trong màn Quản trị.')
            return users, ''

        if rule == 'admin_group':
            admins = live_admin_users(self.env, company=company)
            if not admins:
                return Users, _('Công ty chưa có Quản trị gốc hoặc Quản trị ủy quyền đang hiệu lực.')
            return admins, ''

        if rule == 'direct_manager':
            if not employee:
                return Users, _('Tài khoản người gửi chưa liên kết hồ sơ nhân viên nên chưa xác định được quản lý trực tiếp.')
            manager_emp = employee.parent_id
            if not manager_emp:
                return Users, _('Hồ sơ nhân sự chưa khai báo Quản lý trực tiếp (parent_id).')
            mgr_user = active_internal_users(manager_emp.user_id, company=company)
            if not mgr_user:
                return Users, _(
                    'Quản lý trực tiếp (%(name)s) chưa có tài khoản đăng nhập đang hoạt động.',
                    name=manager_emp.name,
                )
            return mgr_user, ''

        if rule == 'department_manager':
            if not employee or not employee.department_id:
                return Users, _('Hồ sơ nhân sự chưa gắn phòng ban nên chưa xác định được Trưởng phòng.')
            dept = employee.department_id.sudo()
            if not dept.manager_id:
                return Users, _(
                    'Phòng ban “%(dept)s” chưa cấu hình Trưởng phòng trong danh mục Nhân sự.',
                    dept=dept.name,
                )
            mgr_user = active_internal_users(dept.manager_id.user_id, company=company)
            if not mgr_user:
                return Users, _(
                    'Trưởng phòng “%(dept)s” (%(name)s) chưa có tài khoản đăng nhập đang hoạt động.',
                    dept=dept.name, name=dept.manager_id.name,
                )
            return mgr_user, ''

        if rule == 'project_lead':
            if not project:
                return Users, _('Cần chọn Dự án liên quan để xác định Chủ trì dự án.')
            proj = project.sudo()
            candidates = Users
            if proj.user_id:
                candidates |= proj.user_id
            if 'tp.project.assignment' in self.env:
                coords = self.env['tp.project.assignment'].sudo().search([
                    ('project_id', '=', proj.id),
                    ('active', '=', True),
                    ('role', '=', 'coordinator'),
                ]).mapped('user_id')
                candidates |= coords
            valid = active_internal_users(candidates, company=company)
            if not valid:
                return Users, _(
                    'Dự án “%(proj)s” chưa có Chủ trì / điều phối dự án hợp lệ.',
                    proj=proj.display_name,
                )
            return valid, ''

        return Users, _('Quy tắc người duyệt không hợp lệ.')

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            require_request_manager(self.env)
        records = super().create(vals_list)
        if not self.env.su:
            for rtype in records.mapped('type_id'):
                super(TpRequestType, rtype).write({'config_version': rtype.config_version + 1})
        return records

    def write(self, vals):
        if not self.env.su:
            require_request_manager(self.env)
        res = super().write(vals)
        if not self.env.su:
            for rtype in self.mapped('type_id'):
                super(TpRequestType, rtype).write({'config_version': rtype.config_version + 1})
        return res

    def unlink(self):
        if not self.env.su:
            require_request_manager(self.env)
        types = self.mapped('type_id')
        res = super().unlink()
        if not self.env.su:
            for rtype in types.exists():
                super(TpRequestType, rtype).write({'config_version': rtype.config_version + 1})
        return res
