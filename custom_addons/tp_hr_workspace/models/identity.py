"""Identity follows verified employee/user relations, never a display-name match."""
import hashlib
import json
import re

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

_IDENTITY = object()


def image_kind(record):
    image = record.with_context(bin_size=False).image_1920
    if not image:
        return 'empty'
    generated = re.fullmatch(rb'<\?xml version="1.0" encoding="UTF-8" \?><svg height="180" width="180" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><rect fill="#[0-9A-Fa-f]{6}" height="180" width="180"/><text fill="#ffffff" font-size="96" text-anchor="middle" x="90" y="125" font-family="sans-serif">.+</text></svg>', bytes(image))
    return 'generated' if bytes(image) == bytes(record._avatar_generate_svg()) or generated else 'photo'


class EmployeeIdentity(models.Model):
    _inherit = 'hr.employee'

    def _inverse_work_contact_details(self):
        # Native falls back to private_email; a work identity must never publish it.
        missing = self.env['hr.employee']
        for employee in self:
            if not employee.work_contact_id:
                missing += employee
            elif len(employee.work_contact_id.employee_ids) <= 1:
                partner = employee.work_contact_id
                if not employee.user_id and not partner.user_ids:
                    partner = partner.sudo()
                partner.write({'email': employee.work_email, 'phone': employee.work_phone})
        if missing:
            missing.sudo()._create_work_contacts()

    def _tp_assert_identity_mapping(self):
        for employee in self.filtered('user_id'):
            linked = self.sudo().with_context(active_test=False).search([('user_id', '=', employee.user_id.id)])
            if linked != employee or employee.work_contact_id != employee.user_id.partner_id or employee.user_id.partner_id.user_ids != employee.user_id:
                raise UserError(self.env._('Liên kết danh tính chưa duy nhất hoặc liên hệ công việc khác liên hệ của tài khoản. Quản trị viên cần đối chiếu hồ sơ trước khi đồng bộ.'))

    def _compute_avatar(self, avatar_field, image_field):
        super()._compute_avatar(avatar_field, image_field)
        for employee in self:
            if employee.user_id and not employee[image_field]:
                employee[avatar_field] = employee.user_id.partner_id[avatar_field]

    def _tp_identity_state(self):
        self.ensure_one()
        user = self.user_id.sudo()
        return {'employee': self.id, 'code': self.tp_employee_code, 'resource': self.resource_id.id,
                'user': user.id, 'partner': user.partner_id.id, 'work_contact': self.work_contact_id.id,
                'name': self.name, 'user_name': user.name,
                'employee_image': hashlib.sha256(self.with_context(bin_size=False).image_1920 or b'').hexdigest(),
                'user_image': hashlib.sha256(user.with_context(bin_size=False).image_1920 or b'').hexdigest()}

    def _tp_sync_identity(self, keys):
        if not keys:
            return
        self._tp_assert_identity_mapping()
        for employee in self.filtered('user_id').with_context(bin_size=False):
            user = employee.user_id.sudo()
            # This is the account's partner, not an arbitrary work/customer contact.
            values = {}
            if 'name' in keys and user.name != employee.name:
                values['name'] = employee.name
            if 'image_1920' in keys and bytes(user.image_1920 or b'') != bytes(employee.image_1920 or b''):
                values['image_1920'] = employee.image_1920
            if values:
                user.with_context(_tp_identity=_IDENTITY).write(values)

    def write(self, vals):
        internal = self.env.context.get('_tp_identity') is _IDENTITY
        if 'work_contact_id' in vals and any(e.user_id and vals['work_contact_id'] != e.user_id.partner_id.id for e in self):
            raise AccessError(self.env._('Liên hệ công việc phải khớp liên hệ của tài khoản đã liên kết.'))
        if not internal and set(vals) & {'name', 'image_1920'}:
            self.check_access('write')
        result = super().write(vals)
        if not internal:
            self._tp_sync_identity(set(vals) & {'name', 'image_1920'})
        return result

    def action_reconcile_identity(self):
        self._tp_account_admin(existing=True)
        wizard = self.env['tp.hr.identity.wizard'].create({'employee_id': self.id})
        return wizard.action_preview()


class UserIdentity(models.Model):
    _inherit = 'res.users'

    @api.model
    def action_get(self):
        return self.env.ref('tp_web_login.action_account_security').sudo().read()[0]

    def _get_employee_fields_to_sync(self):
        # Native only copies photos to empty employees and lets preferences rename HR.
        return [f for f in super()._get_employee_fields_to_sync() if f not in {'name', 'image_1920'}]

    def write(self, vals):
        if 'partner_id' in vals:
            employees = self.env['hr.employee'].sudo().with_context(active_test=False).search([('user_id', 'in', self.ids)])
            if any(e.user_id.partner_id.id != vals['partner_id'] for e in employees):
                raise AccessError(self.env._('Không được thay liên hệ định danh của tài khoản nhân viên đã liên kết.'))
        return super().write(vals)


class PartnerIdentity(models.Model):
    _inherit = 'res.partner'

    def write(self, vals):
        internal = self.env.context.get('_tp_identity') is _IDENTITY
        employees = self.env['hr.employee'].sudo().with_context(active_test=False, bin_size=False).search([
            ('user_id.partner_id', 'in', self.ids),
        ]) if not internal and set(vals) & {'name', 'image_1920'} else self.env['hr.employee']
        if 'name' in vals and any(e.name != vals['name'] for e in employees):
            raise AccessError(self.env._('Họ tên chính thức được quản lý tại hồ sơ nhân viên. Vui lòng liên hệ bộ phận Nhân sự.'))
        # Native access is checked before the narrow employee synchronization.
        if employees:
            employees._tp_assert_identity_mapping()
        result = super().write(vals)
        if 'image_1920' in vals:
            for employee in employees:
                image = employee.user_id.partner_id.with_context(bin_size=False).image_1920
                if bytes(employee.image_1920 or b'') != bytes(image or b''):
                    employee.with_context(_tp_identity=_IDENTITY).write({'image_1920': image})
        if set(vals) & {'name', 'image_1920'}:
            for partner in self.filtered('user_ids'):
                partner._bus_send('tp.identity/changed', {'partner_id': partner.id, 'name': partner.name,
                                                         'write_date': str(partner.write_date)})
        return result


class ResourceIdentity(models.Model):
    _inherit = 'resource.resource'

    def write(self, vals):
        employees = self.env['hr.employee'].sudo().with_context(active_test=False).search([
            ('resource_id', 'in', self.ids), ('user_id', '!=', False),
        ]) if 'name' in vals else self.env['hr.employee']
        if employees and not self.env.su:
            employees.with_env(self.env).check_access('write')
        result = super().write(vals)
        if employees:
            employees._tp_sync_identity({'name'})
        return result


class IdentityWizard(models.TransientModel):
    _name = 'tp.hr.identity.wizard'
    _description = 'Đối chiếu danh tính tài khoản nhân viên'

    employee_id = fields.Many2one('hr.employee', required=True, readonly=True, string='Hồ sơ nhân viên')
    employee_code = fields.Char(related='employee_id.tp_employee_code', string='Mã nhân viên')
    account_name = fields.Char(related='employee_id.user_id.name', string='Tên tài khoản')
    employee_image = fields.Image(related='employee_id.image_128', readonly=True)
    account_image = fields.Image(related='employee_id.user_id.image_128', readonly=True)
    choice = fields.Selection([('employee', 'Giữ ảnh hồ sơ nhân viên'), ('account', 'Giữ ảnh tài khoản')], string='Ảnh thống nhất')
    reason = fields.Text(required=True, string='Lý do', default='Đối chiếu tên và ảnh giữa hồ sơ nhân viên và tài khoản')
    preview = fields.Text(readonly=True, string='Kết quả đối chiếu')
    expected_digest = fields.Char(readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.pop('preview', None)
            vals.pop('expected_digest', None)
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) & {'preview', 'expected_digest'} and self.env.context.get('_tp_identity') is not _IDENTITY:
            raise AccessError(self.env._('Bản đối chiếu phải do máy chủ tạo.'))
        return super().write(vals)

    def _digest(self, employee):
        return hashlib.sha256(json.dumps([employee._tp_identity_state(), self.choice, self.reason], sort_keys=True).encode()).hexdigest()

    def action_preview(self):
        self.ensure_one()
        employee = self.employee_id._tp_account_admin(existing=True).with_context(bin_size=False)
        employee._tp_assert_identity_mapping()
        partner = employee.user_id.sudo().partner_id
        left, right = image_kind(employee), image_kind(partner)
        if not self.choice:
            if left == 'photo' and right != 'photo':
                self.choice = 'employee'
            elif right == 'photo' and left != 'photo':
                self.choice = 'account'
            elif bytes(employee.image_1920 or b'') == bytes(partner.image_1920 or b'') or (left != 'photo' and right != 'photo'):
                self.choice = 'employee'
        kinds = {'empty': 'Chưa có ảnh', 'generated': 'Ảnh chữ cái tự tạo', 'photo': 'Ảnh đã tải lên'}
        text = f'Ảnh hồ sơ: {kinds[left]}.\nẢnh tài khoản: {kinds[right]}.'
        text += ('\nHọ tên hồ sơ và tài khoản đã khớp.' if employee.name == partner.name
                 else f'\nTên tài khoản sẽ được đổi từ “{partner.name}” thành “{employee.name}”.')
        text += '\nTên đăng nhập, mật khẩu và xác thực hai bước được giữ nguyên.'
        if not self.choice:
            text += '\nHai bên có ảnh thật khác nhau: admin cần chọn ảnh, không tự ghi đè.'
        self.with_context(_tp_identity=_IDENTITY).write({'preview': text, 'expected_digest': self._digest(employee)})
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id,
                'view_mode': 'form', 'target': 'new', 'name': 'Đối chiếu danh tính'}

    def action_apply(self):
        self.ensure_one()
        employee = self.employee_id._tp_account_admin(existing=True).with_context(bin_size=False)
        employee._tp_assert_identity_mapping()
        self.env.cr.execute('SELECT id FROM hr_employee WHERE id=%s FOR UPDATE', [employee.id])
        self.env.cr.execute('SELECT id FROM resource_resource WHERE id=%s FOR UPDATE', [employee.resource_id.id])
        self.env.cr.execute('SELECT id FROM res_partner WHERE id=%s FOR UPDATE', [employee.user_id.partner_id.id])
        self.env.invalidate_all()
        if not self.choice or not (self.reason or '').strip() or self.expected_digest != self._digest(employee):
            raise UserError(self.env._('Chọn ảnh, nhập lý do và xem trước lại trước khi xác nhận.'))
        with self.env.registry.cursor() as current_cr:
            current_cr.execute('SET TRANSACTION READ ONLY')
            current_env = api.Environment(current_cr, self.env.uid, dict(self.env.context))
            current = current_env['hr.employee'].browse(employee.id).exists()
            if current and self._digest(current) != self._digest(employee):
                raise UserError(self.env._('Danh tính vừa đổi từ phiên khác. Hãy xem trước lại.'))
        before = employee._tp_identity_state()
        with self.env.cr.savepoint():
            image = employee.image_1920 if self.choice == 'employee' else employee.user_id.sudo().image_1920
            employee.with_context(_tp_identity=_IDENTITY).write({'image_1920': image})
            employee._tp_sync_identity({'name', 'image_1920'})
            self.env['tp.hr.employee.audit']._tp_record([{
                'action': 'identity', 'employee_ref': employee.id, 'employee_name': employee.name,
                'employee_code': employee.tp_employee_code, 'company_id': employee.company_id.id,
                'reason': self.reason, 'snapshot': {'before': before, 'preview': self.preview, 'after': employee._tp_identity_state()},
            }])
            employee.message_post(body=self.env._('Đã đồng bộ tên và ảnh hồ sơ với tài khoản. Lý do: %s', self.reason))
            self.with_context(_tp_identity=_IDENTITY).write({'expected_digest': False})
        return {'type': 'ir.actions.act_window_close'}
