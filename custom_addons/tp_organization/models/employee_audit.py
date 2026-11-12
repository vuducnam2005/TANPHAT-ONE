from odoo import api, fields, models
from odoo.exceptions import AccessError

_AUDIT_WRITE = object()


class TpHrEmployeeAudit(models.Model):
    """Append-only log of employee deletions and code corrections (HR-CORRECTION-008).

    It keeps no foreign key to ``hr.employee`` so the entry outlives the
    deleted record; rows are written only by backend flows.
    """

    _name = 'tp.hr.employee.audit'
    _description = 'Nhật ký xóa hồ sơ và sửa mã nhân viên'
    _order = 'id desc'
    _rec_name = 'employee_name'

    action = fields.Selection([('delete', 'Xóa hồ sơ nhập nhầm'), ('code_correction', 'Sửa mã nhân viên')],
                              string='Thao tác', required=True, readonly=True)
    employee_ref = fields.Integer(string='ID hồ sơ', required=True, readonly=True, index=True)
    employee_name = fields.Char(string='Họ và tên', readonly=True)
    employee_code = fields.Char(string='Mã nhân viên', readonly=True, index=True)
    new_code = fields.Char(string='Mã sau khi sửa', readonly=True, index=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, readonly=True, ondelete='restrict')
    reason = fields.Text(string='Lý do', required=True, readonly=True)
    actor_id = fields.Many2one('res.users', string='Người thực hiện', readonly=True, ondelete='set null',
                               default=lambda self: self.env.user)
    actor_name = fields.Char(string='Tên người thực hiện', readonly=True, default=lambda self: self.env.user.name)
    snapshot = fields.Json(string='Dữ liệu tại thời điểm thực hiện', readonly=True)

    @api.model
    def _tp_record(self, vals_list):
        actor = self.env.user
        for vals in vals_list:
            vals.setdefault('actor_id', actor.id)
            vals.setdefault('actor_name', actor.name)
        return self.sudo().with_context(_tp_audit_write=_AUDIT_WRITE).create(vals_list)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('_tp_audit_write') is not _AUDIT_WRITE:
            raise AccessError(self.env._('Nhật ký hồ sơ nhân viên chỉ được ghi bởi hệ thống.'))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._('Nhật ký hồ sơ nhân viên không được sửa.'))

    def unlink(self):
        raise AccessError(self.env._('Nhật ký hồ sơ nhân viên không được xóa.'))
