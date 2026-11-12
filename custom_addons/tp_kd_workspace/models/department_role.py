from odoo import api, models
from odoo.exceptions import AccessError
from odoo.fields import Domain


class DepartmentRole(models.Model):
    _inherit = 'tp.kd.department.role'

    @api.model
    def _team_ids(self, user=None):
        roles = self._roles(user)
        scope = Domain.OR(Domain([('kd_department_id', '=', role.department_id.id), ('company_id', '=', role.company_id.id)])
                          for role in roles)
        return self.env['crm.team'].sudo().search(Domain('active', '=', True) & scope).ids


class Partner(models.Model):
    _inherit = 'res.partner'

    def _kd_head_contact_guard(self, values=None):
        if self.env.is_admin() or not self.env['tp.kd.department.role']._roles():
            return
        own_profile = self == self.env.user.partner_id
        if own_profile and values is not None and set(values) <= {
            'name', 'email', 'phone', 'image_1920', 'lang', 'tz',
        }:
            return
        raise AccessError(self.env._('HEAD cập nhật danh mục nghiệp vụ qua thao tác Đối tác trong dự án; không sửa danh bạ, ngân hàng hoặc thuế trực tiếp.'))

    @api.model_create_multi
    def create(self, vals_list):
        self._kd_head_contact_guard()
        return super().create(vals_list)

    def write(self, vals):
        self._kd_head_contact_guard(vals)
        return super().write(vals)

    def unlink(self):
        self._kd_head_contact_guard()
        return super().unlink()


class PartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    def _kd_head_bank_guard(self):
        if not self.env.is_admin() and self.env['tp.kd.department.role']._roles():
            raise AccessError(self.env._('Vai trò HEAD nghiệp vụ không cho sửa tài khoản ngân hàng.'))

    @api.model_create_multi
    def create(self, vals_list):
        self._kd_head_bank_guard()
        return super().create(vals_list)

    def write(self, vals):
        self._kd_head_bank_guard()
        return super().write(vals)

    def unlink(self):
        self._kd_head_bank_guard()
        return super().unlink()
