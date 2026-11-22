"""Readable audit descriptions and password-confirmed removal from the working list."""
import re

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.http import request

from odoo.addons.tp_organization.models.employee_audit import TpHrEmployeeAudit

_HIDE = object()
_TECH_REASON = re.compile(r'^Cập nhật tài khoản/hồ sơ qua [a-z_.]+ #\d+$')
_LABELS = {
    'name': 'họ và tên', 'login': 'tên đăng nhập', 'email': 'email', 'phone': 'số điện thoại',
    'mobile': 'điện thoại di động', 'active': 'tình trạng tài khoản', 'tp_hr_locked': 'khóa tài khoản',
    'department_id': 'phòng ban', 'job_id': 'chức vụ', 'job_title': 'chức danh',
    'company_id': 'công ty', 'company_ids': 'phạm vi công ty', 'lang': 'ngôn ngữ', 'tz': 'múi giờ',
    'user_id': 'tài khoản của nhân viên', 'partner_id': 'liên hệ tài khoản',
    'resource_id': 'liên kết hồ sơ làm việc', 'employee_id': 'liên kết nhân viên',
    'work_contact_id': 'liên hệ công việc', 'work_email': 'email công việc',
    'work_phone': 'điện thoại công việc', 'mobile_phone': 'điện thoại di động',
}


class AuditCleanup(models.Model):
    _inherit = 'tp.hr.employee.audit'

    active = fields.Boolean(default=True, readonly=True)
    hidden_by_id = fields.Many2one('res.users', readonly=True, ondelete='set null')
    hidden_at = fields.Datetime(readonly=True)
    reason_display = fields.Text('Nội dung / Lý do', compute='_compute_reason_display')

    @api.depends('reason', 'snapshot', 'action')
    def _compute_reason_display(self):
        for row in self:
            if row.action != 'account_profile_change' or not _TECH_REASON.fullmatch(row.reason or ''):
                row.reason_display = row.reason
                continue
            data = row.snapshot or {}
            changes = data.get('changes') or {}
            labels = []
            for key in changes:
                if key.startswith('image_'):
                    continue
                label = _LABELS.get(key)
                if not label:
                    model = self.env.get(data.get('model', ''))
                    field = model._fields.get(key) if model is not None else None
                    label = field.string if field else 'thông tin hồ sơ'
                if label not in labels:
                    labels.append(label)
            if data.get('image_changed'):
                labels.append('ảnh đại diện')
            if data.get('credential_changed'):
                labels.append('thông tin đăng nhập hoặc xác thực')
            row.reason_display = 'Cập nhật ' + ', '.join(labels) + '.' if labels else 'Đồng bộ thông tin giữa hồ sơ nhân viên và tài khoản.'

    @api.model
    def _tp_removed_identities(self, company_id, source_codes=(), employee_codes=()):
        # Hidden deletion rows remain tombstones: imports must not recreate deleted people.
        return super(AuditCleanup, self.with_context(active_test=False))._tp_removed_identities(company_id, source_codes, employee_codes)

    def _tp_cleanup_rights(self):
        actor = self.env.user
        if not actor.active or actor.share or not actor.has_group('base.group_system'):
            raise AccessError(self.env._('Chỉ admin được xóa nhật ký khỏi danh sách.'))
        if hasattr(actor, '_tp_has_live_admin_grant') and not (
                actor._tp_is_original_admin() or actor._tp_has_live_admin_grant()):
            raise AccessError(self.env._('Quyền quản trị không còn hiệu lực.'))
        self.check_access('read')
        if any(row.company_id not in self.env.companies for row in self):
            raise AccessError(self.env._('Có nhật ký ngoài phạm vi công ty được phép.'))

    def action_hide_from_list(self):
        self._tp_cleanup_rights()
        if not self:
            raise UserError(self.env._('Vui lòng chọn ít nhất một dòng nhật ký.'))
        wizard = self.env['tp.hr.audit.cleanup'].create({'audit_ids': [fields.Command.set(self.ids)]})
        return {'type': 'ir.actions.act_window', 'name': 'Xóa nhật ký khỏi danh sách',
                'res_model': wizard._name, 'res_id': wizard.id, 'view_mode': 'form', 'target': 'new',
                'context': {'dialog_size': 'medium'}}

    def write(self, vals):
        if self.env.context.get('_tp_hide_audit') is _HIDE and set(vals) <= {'active', 'hidden_by_id', 'hidden_at'}:
            # Skip only the immutable base audit write, preserving native ORM validation.
            return super(TpHrEmployeeAudit, self).write(vals)
        return super().write(vals)


class AuditCleanupWizard(models.TransientModel):
    _name = 'tp.hr.audit.cleanup'
    _description = 'Xác nhận xóa nhật ký khỏi danh sách'

    audit_ids = fields.Many2many('tp.hr.employee.audit', readonly=True)
    count = fields.Integer(compute='_compute_count', string='Số dòng đã chọn')
    password = fields.Char(store=False, string='Mật khẩu của bạn')

    @api.depends('audit_ids')
    def _compute_count(self):
        for wizard in self:
            wizard.count = len(wizard.audit_ids)

    def action_confirm(self):
        self.ensure_one()
        if not request or request.session.uid != self.env.uid:
            raise AccessError(self.env._('Phiên đăng nhập không hợp lệ.'))
        self.check_access('write')
        if self.create_uid.id != self.env.uid:
            raise AccessError(self.env._('Chỉ được xác nhận yêu cầu do chính bạn tạo.'))
        rows = self.audit_ids.exists()
        rows._tp_cleanup_rights()
        password = self.env.context.get('password')
        if not isinstance(password, str) or not password:
            raise UserError(self.env._('Vui lòng nhập mật khẩu của tài khoản đang đăng nhập.'))
        failure = self.env['hr.employee']._tp_verify_admin_password(password)
        if failure:
            raise UserError(failure)
        rows._tp_cleanup_rights()
        rows.sudo().with_context(_tp_hide_audit=_HIDE).write({
            'active': False, 'hidden_by_id': self.env.uid, 'hidden_at': fields.Datetime.now(),
        })
        return {'type': 'ir.actions.client', 'tag': 'reload'}
