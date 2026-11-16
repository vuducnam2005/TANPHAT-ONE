from odoo import api, fields, models
from odoo.exceptions import AccessError

_AUDIT_WRITE = object()
# Actions whose ``employee_code``/``source_code`` identify a removed profile.
DELETE_ACTIONS = ('delete', 'permanent_delete')


class TpHrEmployeeAudit(models.Model):
    """Append-only log of employee deletions and code corrections.

    HR-CORRECTION-008 introduced it; HR-DELETE-010 adds permanent deletion
    with request id, account action and verification result. It keeps no
    foreign key to ``hr.employee`` so the entry outlives the deleted record;
    rows are written only by backend flows and never store a password.
    """

    _name = 'tp.hr.employee.audit'
    _description = 'Nhật ký xóa hồ sơ và sửa mã nhân viên'
    _order = 'id desc'
    _rec_name = 'employee_name'

    action = fields.Selection([('delete', 'Xóa hồ sơ nhập nhầm'), ('permanent_delete', 'Xóa vĩnh viễn'),
                               ('code_correction', 'Sửa mã nhân viên')],
                              string='Thao tác', required=True, readonly=True)
    employee_ref = fields.Integer(string='ID hồ sơ', required=True, readonly=True, index=True)
    employee_name = fields.Char(string='Họ và tên', readonly=True)
    employee_code = fields.Char(string='Mã nhân viên', readonly=True, index=True)
    source_code = fields.Char(string='Mã nguồn', readonly=True, index=True)
    new_code = fields.Char(string='Mã sau khi sửa', readonly=True, index=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, readonly=True, ondelete='restrict')
    reason = fields.Text(string='Lý do', required=True, readonly=True)
    actor_id = fields.Many2one('res.users', string='Người thực hiện', readonly=True, ondelete='set null',
                               default=lambda self: self.env.user)
    actor_name = fields.Char(string='Tên người thực hiện', readonly=True, default=lambda self: self.env.user.name)
    request_id = fields.Char(string='Mã yêu cầu', readonly=True, index=True, copy=False)
    account_action = fields.Selection([('none', 'Không có tài khoản'), ('kept', 'Giữ tài khoản'), ('locked', 'Đã khóa tài khoản'),
                                       ('already_locked', 'Tài khoản đã khóa từ trước')],
                                      string='Tài khoản', readonly=True)
    account_ref = fields.Integer(string='ID tài khoản', readonly=True)
    account_login = fields.Char(string='Tên đăng nhập', readonly=True)
    verification = fields.Char(string='Xác minh', readonly=True)
    snapshot = fields.Json(string='Dữ liệu tại thời điểm thực hiện', readonly=True)

    _tp_request_unique = models.Constraint('UNIQUE(request_id, employee_ref)', 'Yêu cầu xóa này đã được ghi nhận.')

    @api.model
    def _tp_record(self, vals_list):
        actor = self.env.user
        for vals in vals_list:
            vals.setdefault('actor_id', actor.id)
            vals.setdefault('actor_name', actor.name)
        return self.sudo().with_context(_tp_audit_write=_AUDIT_WRITE).create(vals_list)

    @api.model
    def _tp_removed_identities(self, company_id, source_codes=(), employee_codes=()):
        """Deleted profiles of ``company_id`` matching a source or TP code.

        Codes of deleted profiles are never issued again and a later roster
        import must not silently recreate them.
        """
        source_codes, employee_codes = [c for c in source_codes if c], [c for c in employee_codes if c]
        if not source_codes and not employee_codes:
            return self.browse()
        domain = [('company_id', '=', company_id), ('action', 'in', DELETE_ACTIONS)]
        if source_codes and employee_codes:
            domain += ['|', ('source_code', 'in', source_codes), ('employee_code', 'in', employee_codes)]
        elif source_codes:
            domain.append(('source_code', 'in', source_codes))
        else:
            domain.append(('employee_code', 'in', employee_codes))
        return self.sudo().search(domain)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('_tp_audit_write') is not _AUDIT_WRITE:
            raise AccessError(self.env._('Nhật ký hồ sơ nhân viên chỉ được ghi bởi hệ thống.'))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._('Nhật ký hồ sơ nhân viên không được sửa.'))

    def unlink(self):
        raise AccessError(self.env._('Nhật ký hồ sơ nhân viên không được xóa.'))
