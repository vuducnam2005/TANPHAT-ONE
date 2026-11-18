"""A scalar native HR adapter: no private-field group or identity authority is implied."""
import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .guards import _PROFILE, _PROFILE_CREATE

PROFILE_FIELDS = ('name', 'work_email', 'work_phone', 'mobile_phone', 'job_title')


class ScopedHrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        if (view_type in ('list', 'form', 'search') and self.env.user._tp_has_admin_delegation()
                and not self.env.user.has_group('hr.group_hr_user')):
            # Same employee/action; only request fields the caller can actually read.
            view_id = self.env.ref('tp_admin_delegation.delegated_employee_' + view_type).id
        return super().get_view(view_id, view_type, **options)

    def action_tp_edit_delegated_profile(self):
        self.ensure_one()
        self._tp_delegated_account_check(existing=bool(self.sudo().user_id))
        wizard = self.env['tp.hr.delegated.profile.wizard'].create({'employee_id': self.id, 'operation': 'edit'})
        return {'type': 'ir.actions.act_window', 'name': 'Cập nhật hồ sơ ngoài phòng',
                'res_model': wizard._name, 'res_id': wizard.id, 'view_mode': 'form', 'target': 'new'}

    def action_tp_archive_delegated_profile(self):
        self.ensure_one()
        self._tp_delegated_account_check(existing=False)
        wizard = self.env['tp.hr.delegated.profile.wizard'].create({'employee_id': self.id, 'operation': 'archive'})
        return {'type': 'ir.actions.act_window', 'name': 'Lưu trữ hồ sơ chưa có tài khoản',
                'res_model': wizard._name, 'res_id': wizard.id, 'view_mode': 'form', 'target': 'new'}


class ScopedHrProfile(models.TransientModel):
    _name = 'tp.hr.delegated.profile.wizard'
    _description = 'Cập nhật hồ sơ nhân sự ngoài phòng'

    operation = fields.Selection([('edit', 'Cập nhật hồ sơ'), ('create', 'Tạo hồ sơ'),
                                  ('archive', 'Lưu trữ hồ sơ chưa có tài khoản')], default='create', required=True, string='Thao tác')
    employee_id = fields.Many2one('hr.employee', readonly=True, string='Hồ sơ hiện có')
    expected_write_date = fields.Datetime(readonly=True)
    expected_version_date = fields.Datetime(readonly=True)
    expected_resource_date = fields.Datetime(readonly=True)
    expected_digest = fields.Char(readonly=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, readonly=True, default=lambda self: self.env.company)
    allowed_department_ids = fields.Many2many('hr.department', compute='_compute_departments')
    department_id = fields.Many2one('hr.department', required=True, string='Phòng ban')
    name = fields.Char(required=True, string='Họ và tên')
    work_email = fields.Char(string='Email công việc')
    work_phone = fields.Char(string='Điện thoại công ty')
    mobile_phone = fields.Char(string='Di động', groups='hr.group_hr_user')
    job_title = fields.Char(string='Chức danh mô tả')
    reason = fields.Text(string='Lý do')

    @api.model
    def _allowed_profile_fields(self):
        employee_model = self.env['hr.employee'].sudo(False)
        wizard_model = self.sudo(False)
        return tuple(
            key for key in PROFILE_FIELDS
            if key in employee_model._fields
            and employee_model._has_field_access(employee_model._fields[key], 'read')
            and employee_model._has_field_access(employee_model._fields[key], 'write')
            and wizard_model._has_field_access(wizard_model._fields[key], 'read')
            and wizard_model._has_field_access(wizard_model._fields[key], 'write')
        )

    @api.model
    def _employee_digest(self, employee):
        employee = employee.with_context(version_id=False)
        values = {key: employee[key] for key in self._allowed_profile_fields()}
        values.update(company=employee.company_id.id, department=employee._get_version().department_id.id,
                      user=employee.user_id.id, version=employee.current_version_id.id,
                      employee_write=employee.write_date, version_write=employee._get_version().write_date,
                      resource_write=employee.resource_id.write_date)
        return hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode()).hexdigest()

    @api.model
    def default_get(self, fields_list):
        restricted = set(PROFILE_FIELDS) - set(self._allowed_profile_fields())
        if any(f'default_{key}' in self.env.context for key in restricted):
            raise AccessError(self.env._('Không có quyền ghi trường nhân sự bị giới hạn.'))
        return super().default_get([key for key in fields_list if key not in restricted])

    @api.depends('company_id')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_departments(self):
        for wizard in self:
            own, complete = self.env.user._tp_delegation_scope(wizard.company_id)
            wizard.allowed_department_ids = self.env['hr.department'].sudo().search([
                ('company_id', '=', wizard.company_id.id), ('id', 'not in', own.ids), ('active', '=', True),
            ]) if complete and self.env.user._tp_has_admin_delegation(wizard.company_id) else False

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user._tp_has_admin_delegation():
            raise AccessError(self.env._('Chức năng này cần quyền quản trị được ủy quyền còn hiệu lực.'))
        allowed = self._allowed_profile_fields()
        restricted = set(PROFILE_FIELDS) - set(allowed)
        if any(f'default_{key}' in self.env.context for key in restricted):
            raise AccessError(self.env._('Không có quyền ghi trường nhân sự bị giới hạn.'))
        for vals in vals_list:
            if set(vals) & restricted:
                raise AccessError(self.env._('Không có quyền ghi trường nhân sự bị giới hạn.'))
            employee = self.env['hr.employee'].browse(vals.get('employee_id')).exists()
            if employee:
                employee._tp_delegated_account_check(existing=bool(employee.sudo().user_id))
                employee.check_access('read')
                source = employee.sudo().with_context(version_id=False)
                vals.update({key: source[key] for key in allowed})
                vals.update(company_id=source.company_id.id, department_id=source._get_version().department_id.id,
                            expected_write_date=source.write_date,
                            expected_version_date=source._get_version().write_date,
                            expected_resource_date=source.resource_id.write_date, expected_digest=self._employee_digest(source))
            else:
                if vals.get('operation', 'create') != 'create':
                    raise UserError(self.env._('Cần chọn hồ sơ hiện có.'))
                vals.update(employee_id=False, expected_write_date=False, company_id=self.env.company.id)
        return super().create(vals_list)

    def write(self, vals):
        restricted = set(PROFILE_FIELDS) - set(self._allowed_profile_fields())
        if set(vals) & restricted:
            raise AccessError(self.env._('Không có quyền ghi trường nhân sự bị giới hạn.'))
        if set(vals) & {'employee_id', 'company_id', 'expected_write_date', 'expected_version_date', 'expected_resource_date', 'expected_digest', 'operation'}:
            raise AccessError(self.env._('Hồ sơ, công ty và thao tác được chốt khi mở cửa sổ.'))
        if 'department_id' in vals and any(wizard.operation != 'create' for wizard in self):
            raise AccessError(self.env._('Thay phòng ban phải dùng luồng Chuyển phòng ban của Quản trị chính.'))
        return super().write(vals)

    def action_apply(self):
        self.ensure_one()
        if not isinstance(self.reason, str) or not self.reason.strip() or not (self.name or '').strip():
            raise UserError(self.env._('Nhập họ tên và lý do thao tác.'))
        if not self.env.user._tp_delegated_other_department(self.company_id, self.department_id, lock=True):
            raise AccessError(self.env._('Phòng ban không thuộc phần quản trị được ủy quyền.'))
        employee = self.employee_id
        if self.operation != 'create':
            if not employee:
                raise AccessError(self.env._('Hồ sơ không còn tồn tại.'))
            employee = employee._tp_delegated_account_check(existing=bool(employee.sudo().user_id))
            self.env.cr.execute('SELECT id FROM hr_employee WHERE id=%s FOR UPDATE', [employee.id])
            self.env.cr.execute('SELECT id FROM resource_resource WHERE id=%s FOR UPDATE', [employee.resource_id.id])
            self.env.cr.execute('SELECT id FROM hr_version WHERE employee_id=%s ORDER BY id FOR UPDATE', [employee.id])
            employee.invalidate_recordset()
            if (employee.write_date != self.expected_write_date
                    or employee._get_version().write_date != self.expected_version_date
                    or employee.resource_id.write_date != self.expected_resource_date
                    or self._employee_digest(employee) != self.expected_digest):
                raise UserError(self.env._('Hồ sơ vừa được cập nhật. Hãy mở lại cửa sổ để đối chiếu.'))
            if employee.company_id != self.company_id or employee._get_version().department_id != self.department_id:
                raise AccessError(self.env._('Phạm vi hồ sơ đã thay đổi.'))
        allowed = self._allowed_profile_fields()
        values = {}
        for key in allowed:
            value = (self[key] or '').strip()
            if len(value) > 254:
                raise UserError(self.env._('Thông tin hồ sơ tối đa 254 ký tự mỗi trường.'))
            values[key] = value or False
        clean_ctx = {
            'lang': self.env.lang, 'tz': self.env.user.tz,
            'allowed_company_ids': [self.company_id.id],
            '_tp_delegated_profile': _PROFILE,
        }
        with self.env.cr.savepoint():
            if self.operation == 'create':
                employee = self.env['hr.employee'].sudo().with_context({
                    **clean_ctx, '_tp_delegated_profile_create': _PROFILE_CREATE,
                }).create({
                    **values, 'company_id': self.company_id.id, 'department_id': self.department_id.id,
                })
            elif self.operation == 'edit':
                employee.with_context(clean_ctx).write(values)
            elif self.operation == 'archive':
                if employee.user_id:
                    raise AccessError(self.env._('Chỉ lưu trữ qua ủy quyền khi hồ sơ chưa có tài khoản.'))
                employee.with_context(clean_ctx).write({'active': False})
            else:
                raise AccessError(self.env._('Thao tác hồ sơ không hợp lệ.'))
            employee.with_context(clean_ctx).message_post(
                body=self.env._('Quản trị được ủy quyền %(operation)s hồ sơ. Lý do: %(reason)s',
                                operation=dict(self._fields['operation'].selection)[self.operation],
                                reason=self.reason.strip()))
        return {'type': 'ir.actions.act_window_close'}
