"""One permission-scoped population for HR charts, drill-down and work-directory XLSX."""
import io

import xlsxwriter

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class HrWorkspace(models.AbstractModel):
    _name = 'tp.hr.workspace'
    _description = 'TP HR overview and reports'

    @api.model
    def _tp_population_source(self):
        """Employee model and fixed row scope; a scoped adapter may narrow rows."""
        if not self.env.user.has_group('hr.group_hr_user'):
            raise AccessError(self.env._('Chỉ nhân sự được giao mới được xem báo cáo HR.'))
        employees = self.env['hr.employee'].with_context(active_test=False)
        employees.check_access('read')
        return employees, []

    @api.model
    def _tp_action_domain(self, employees, domain, extra_domain):
        return domain + (extra_domain or [])

    @api.model
    def _population(self, filters=None):
        employees, scope = self._tp_population_source()
        filters = filters or {}
        if not isinstance(filters, dict) or set(filters) - {'department_id', 'job_id', 'status', 'employment_kind', 'missing_basic'}:
            raise ValidationError(self.env._('Bộ lọc HR không hợp lệ.'))
        status = filters.get('status') or 'active'
        if status not in ('active', 'archived', 'all'):
            raise ValidationError(self.env._('Trạng thái hồ sơ không hợp lệ.'))
        domain = [('company_id', '=', self.env.company.id)] + scope
        if status != 'all':
            domain.append(('active', '=', status == 'active'))
        for field, model, label in [('department_id', 'hr.department', 'Đơn vị'), ('job_id', 'hr.job', 'Chức vụ')]:
            value = filters.get(field)
            if value in (None, False, ''):
                continue
            try:
                if isinstance(value, bool) or str(int(value)) != str(value) or int(value) <= 0:
                    raise ValueError  # noqa: TRY301 - one localized filter validation
                value = int(value)
            except (ValueError, TypeError) as exc:
                raise ValidationError(self.env._('%s không hợp lệ.', label)) from exc
            record = self.env[model].with_context(active_test=False).browse(value).exists()
            record.check_access('read')
            if not record or record.company_id not in (self.env.company, self.env['res.company']):
                raise AccessError(self.env._('%s nằm ngoài công ty đang xem.', label))
            domain.append((field, '=', value))
        kind = filters.get('employment_kind')
        if kind:
            if kind not in ('short_term', 'long_term', 'outsourced', 'unknown'):
                raise ValidationError(self.env._('Loại hình lao động không hợp lệ.'))
            domain.append(('tp_employment_kind', '=', False if kind == 'unknown' else kind))
        if filters.get('missing_basic') not in (None, False, True, '', '1'):
            raise ValidationError(self.env._('Bộ lọc hồ sơ cần bổ sung không hợp lệ.'))
        if filters.get('missing_basic'):
            domain += self.env['hr.employee']._tp_missing_domain()
        return employees, domain, status

    @api.model
    def get_overview(self, filters=None):
        employees, domain, _status = self._population(filters)
        total = employees.search_count(domain)
        groups = employees._read_group(domain, ['department_id'], ['__count'])
        departments = [
            {'id': department.id or 0, 'name': department.name if department else 'Chưa khai báo đơn vị',
             'count': count, 'percent': count / total * 100 if total else 0}
            for department, count in groups
        ]
        departments.sort(key=lambda row: row['name'].casefold())
        missing_domain = employees._tp_missing_domain()
        missing = employees.search_count(domain + missing_domain)
        linked = employees.search_count(domain + [('user_id', '!=', False)])
        job_groups = employees._read_group(domain, ['job_id'], ['__count'])
        jobs = [{'id': job.id or 0, 'name': job.name if job else 'Chưa khai báo chức vụ',
                 'count': count, 'percent': count / total * 100 if total else 0} for job, count in job_groups]
        jobs.sort(key=lambda row: (-row['count'], row['name'].casefold(), row['id']))
        linked_by_unit = dict(employees._read_group(domain + [('user_id', '!=', False)], ['department_id'], ['__count']))
        missing_by_unit = dict(employees._read_group(domain + missing_domain, ['department_id'], ['__count']))
        for row in departments:
            department = self.env['hr.department'].browse(row['id'])
            row.update(linked=linked_by_unit.get(department, 0), missing=missing_by_unit.get(department, 0))
            row['pending'] = row['count'] - row['linked']
        catalog_scope = [('company_id', 'in', [False, self.env.company.id])]

        def catalog(model):
            return [{'id': record.id, 'name': record.name} for record in
                    self.env[model].with_context(active_test=False).search(catalog_scope, order='name, id')]
        return {
            'total': total, 'units': sum(bool(row['id']) for row in departments),
            'departments': departments, 'missing_basic': missing, 'complete_basic': total - missing,
            'linked': linked, 'pending': total - linked, 'domain': domain,
            'jobs': jobs, 'catalog_departments': catalog('hr.department'), 'catalog_jobs': catalog('hr.job'),
            'can_create': self.env['hr.employee'].has_access('create'), 'employee_form_id': self.env.ref('tp_hr_workspace.employee_form').id,
            'missing_domain': employees._tp_missing_domain(),
            'missing_code': employees.search_count(domain + [('tp_employee_code', '=', False)]),
            'missing_department': employees.search_count(domain + [('department_id', '=', False)]),
            'locked': employees.search_count(domain + [('tp_account_status', '=', 'disabled')]),
            'missing_job': employees.search_count(domain + [('job_id', '=', False)]),
            'missing_contact': employees.search_count(domain + [('work_email', '=', False), ('work_phone', '=', False), ('mobile_phone', '=', False)]),
            'updated_at': fields.Datetime.context_timestamp(
                self.with_context(tz=self.env.context.get('tz') or self.env.user.tz or 'Asia/Ho_Chi_Minh'),
                fields.Datetime.now(),
            ).strftime('%d/%m/%Y %H:%M %Z'),
        }

    @api.model
    def action_employees(self, filters=None, extra_domain=None):
        employees, domain, _status = self._population(filters)
        if extra_domain is not None and not isinstance(extra_domain, list):
            raise ValidationError(self.env._('Bộ lọc danh sách không hợp lệ.'))
        action = self.env['ir.actions.actions']._for_xml_id('tp_hr_workspace.action_employees')
        action.update(domain=self._tp_action_domain(employees, domain, extra_domain), context={
            'active_test': False, 'tp_hr_leaf': 'tp_hr_workspace.menu_employees',
            'tp_hr_missing': [tuple(item) if isinstance(item, list) else item for item in (extra_domain or [])] == employees._tp_missing_domain(),
        })
        return action

    @api.model
    def _build_xlsx(self, filters=None):
        employees, domain, status = self._population(filters)
        records = employees.search(domain, order='department_id, sequence, id')
        overview = self.get_overview(filters)
        stream = io.BytesIO()
        # Runtime exporter follows the existing Odoo dependency; all text is written literally.
        book = xlsxwriter.Workbook(stream, {'in_memory': True, 'strings_to_formulas': False, 'strings_to_urls': False})
        header = book.add_format({'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#173A54', 'border': 1, 'text_wrap': True})
        text = book.add_format({'num_format': '@', 'valign': 'top', 'border': 1})
        integer = book.add_format({'num_format': '0', 'border': 1})
        percent = book.add_format({'num_format': '0.0%', 'border': 1})
        title = book.add_format({'bold': True, 'font_size': 16, 'font_color': '#173A54'})
        labels = {'active': 'Đang quản lý', 'archived': 'Lưu trữ', 'all': 'Tất cả'}
        department_name = 'Tất cả đơn vị trong quyền'
        if (filters or {}).get('department_id'):
            department_name = self.env['hr.department'].browse(int(filters['department_id'])).name
        metadata = f"{self.env.company.name} | {labels[status]} | {department_name} | Xuất {overview['updated_at']}"
        if (filters or {}).get('job_id'):
            metadata += ' | Chức vụ: ' + self.env['hr.job'].browse(int(filters['job_id'])).name
        if (filters or {}).get('employment_kind'):
            kind = filters['employment_kind']
            metadata += ' | Loại hình: ' + dict(employees._fields['tp_employment_kind']._description_selection(self.env)).get(kind, 'Chưa khai báo')
        if (filters or {}).get('missing_basic'):
            metadata += ' | Hồ sơ cần bổ sung cơ bản'
        for name in ('Tổng hợp đơn vị', 'Danh sách nhân viên'):
            sheet = book.add_worksheet(name)
            sheet.write_string(0, 0, 'TANPHAT ONE — TP HR', title)
            sheet.write_string(1, 0, metadata)
            sheet.write_string(2, 0, 'Kỳ: hiện trạng hồ sơ tại thời điểm xuất; không phải kỳ tính công/lương.')
            sheet.freeze_panes(5, 0)
            sheet.set_landscape()
            sheet.fit_to_pages(1, 0)
            sheet.repeat_rows(0, 4)
            sheet.set_column(0, 0, 20)
            sheet.set_column(1, 4, 32)
            sheet.set_column(5, 9, 26)
            if name == 'Tổng hợp đơn vị':
                sheet.write_row(4, 0, ['Đơn vị', 'Số hồ sơ', 'Tỷ lệ', 'Có tài khoản', 'Chưa có tài khoản', 'Thiếu cơ bản'], header)
                for row, item in enumerate(overview['departments'], 5):
                    sheet.write_string(row, 0, item['name'], text)
                    sheet.write_number(row, 1, item['count'], integer)
                    sheet.write_number(row, 2, item['count'] / overview['total'] if overview['total'] else 0, percent)
                    for column, key in enumerate(('linked', 'pending', 'missing'), 3):
                        sheet.write_number(row, column, item[key], integer)
                last = 5 + len(overview['departments'])
                sheet.write_string(last, 0, 'Tổng hồ sơ', header)
                if last > 5:
                    sheet.write_formula(last, 1, f'=SUM(B6:B{last})', integer, overview['total'])
                else:
                    sheet.write_number(last, 1, 0, integer)
                sheet.autofilter(4, 0, max(4, last - 1), 5)
                sheet.set_column(0, 0, 38)
            else:
                columns = ['Mã nhân viên', 'Họ và tên', 'Đơn vị', 'Chức vụ nguồn', 'Chức danh đã khai báo', 'Loại hình lao động', 'Hồ sơ lưu trữ', 'Tài khoản', 'Tình trạng', 'Cần bổ sung']
                sheet.write_row(4, 0, columns, header)
                for row, employee in enumerate(records, 5):
                    values = [employee.tp_employee_code or 'Chưa có thông tin', employee.name,
                              employee.department_id.name or 'Chưa có thông tin', employee.tp_source_title or 'Chưa có thông tin',
                              employee.job_id.name or 'Chưa có thông tin',
                              dict(employee._fields['tp_employment_kind']._description_selection(self.env)).get(employee.tp_employment_kind, 'Chưa khai báo'),
                              'Đang quản lý' if employee.active else 'Lưu trữ',
                              'Có tài khoản' if employee.user_id else 'Chưa có tài khoản',
                              dict(employee._fields['tp_account_status'].selection)[employee.tp_account_status],
                              employee.tp_missing_basic or 'Đủ ba tiêu chí cơ bản']
                    for column, value in enumerate(values):
                        sheet.write_string(row, column, value, text)
                sheet.autofilter(4, 0, max(4, 4 + len(records)), len(columns) - 1)
                sheet.write_string(6 + len(records), 0, f'Tổng hồ sơ: {len(records)}')
        book.close()
        return stream.getvalue()


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    tp_user_login = fields.Char(
        string='Tên đăng nhập',
        related='user_id.login',
        store=True,
        readonly=True,
        index=True,
    )
    tp_account_status = fields.Selection(
        [
            ('unlinked', 'Chưa có tài khoản'),
            ('active', 'Mở'),
            ('disabled', 'Khóa'),
        ],
        string='Tình trạng',
        compute='_compute_tp_account_status',
        store=True,
        index=True,
    )

    @api.depends('user_id', 'user_id.active', 'user_id.tp_hr_locked')
    def _compute_tp_account_status(self):
        for rec in self:
            if not rec.user_id:
                rec.tp_account_status = 'unlinked'
            elif rec.user_id.active and not rec.user_id.tp_hr_locked:
                rec.tp_account_status = 'active'
            else:
                rec.tp_account_status = 'disabled'

    def write(self, vals):
        if 'user_id' in vals and not self.env.su and not self.env.user.has_group('base.group_system'):
            raise AccessError(self.env._('Chỉ Quản trị viên hệ thống mới có quyền liên kết hoặc thay đổi tài khoản người dùng.'))
        return super().write(vals)

    def action_open_account_dialog(self):
        self.ensure_one()
        self.check_access('read')
        wizard = self.env['tp.hr.account.wizard'].create({
            'employee_id': self.id,
            'current_user_id': self.user_id.id if self.user_id else False,
            'expected_user_id': self.user_id.id if self.user_id else False,
        })
        if not self.user_id and self.env.user.has_group('base.group_system'):
            return wizard.action_prepare_credentials()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Tài khoản nhân viên — %s', self.name),
            'res_model': 'tp.hr.account.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'views': [(self.env.ref('tp_hr_workspace.view_tp_hr_account_wizard_form').id, 'form')],
        }

    def action_reset_user_password(self):
        self._tp_account_admin(existing=True)
        wizard = self.env['tp.hr.account.wizard'].create({'employee_id': self.id, 'expected_user_id': self.user_id.id})
        return wizard.action_prepare_credentials(reset=True)

    def action_open_versions(self):
        self.ensure_one()
        self.check_access('read')
        action = super().action_open_versions()
        # Native wage analytics aggregate technical defaults before wages are confirmed.
        action.update(view_mode='list', views=[(self.env.ref('tp_hr_workspace.version_list').id, 'list')])
        action['name'] = self.env._('Phiên bản hồ sơ — %s', self.name)
        return action

    def action_tp_credentials(self):
        self.ensure_one()
        self.check_access('read')
        if not self.env.user.has_group('hr.group_hr_user'):
            raise AccessError(self.env._('Chỉ nhân sự được giao mới được xem liên kết hồ sơ.'))
        if 'tp.credential' not in self.env:
            raise UserError(self.env._('Chưa có sổ chứng chỉ tổng hợp. Dùng kỹ năng và hồ sơ cá nhân được giao.'))
        credentials = self.env['tp.credential']
        if not credentials.has_access('read'):
            raise AccessError(self.env._('Bạn chưa được giao quyền đọc sổ chứng chỉ. Liên kết HR không cấp thêm quyền KH-KD.'))
        # No name matching: the native work contact is the only verified identity key.
        domain = [('subject_kind', '=', 'person'), ('subject_id', '=', self.work_contact_id.id), ('company_id', '=', self.company_id.id)]
        return {'type': 'ir.actions.act_window', 'name': self.env._('Chứng chỉ cá nhân có quyền xem'),
                'res_model': 'tp.credential', 'view_mode': 'list,form', 'domain': domain,
                'context': {'create': False, 'edit': False, 'delete': False}}


class ResourceResource(models.Model):
    _inherit = 'resource.resource'

    def write(self, vals):
        if 'user_id' in vals and not self.env.su and not self.env.user.has_group('base.group_system'):
            employees = self.env['hr.employee'].sudo().with_context(active_test=False).search([('resource_id', 'in', self.ids)])
            if employees:
                raise AccessError(self.env._('Chỉ Quản trị viên hệ thống mới có quyền thay đổi tài khoản người dùng gắn với nhân viên.'))
        return super().write(vals)


class HrImportBatch(models.Model):
    _inherit = 'tp.hr.import.batch'

    def action_open_lines(self):
        self.ensure_one()
        self._manager()
        return {'type': 'ir.actions.act_window', 'name': self.env._('Bảng đối chiếu nguồn'),
                'res_model': 'tp.hr.import.line', 'view_mode': 'list',
                'views': [(self.env.ref('tp_hr_workspace.import_lines').id, 'list')],
                'domain': [('batch_id', '=', self.id)],
                'context': {'create': False, 'delete': False, 'edit': self.state == 'preview'}}
