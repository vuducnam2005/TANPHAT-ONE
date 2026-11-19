"""HR account management and personal profile labels for Original and Granted Full Admins."""
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .delegation import (
    BUSINESS_USER_LABEL,
    GRANTED_ADMIN_LABEL,
    ORIGINAL_ADMIN_LABEL,
    _system_protected_users,
)
from .guards import _ACCOUNT, _is_protected_original_target


class DelegatedEmployee(models.Model):
    _inherit = 'hr.employee'

    tp_can_manage_account = fields.Boolean(compute='_compute_tp_can_manage_account')

    @api.depends('user_id', 'company_id', 'department_id')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_tp_can_manage_account(self):
        caller = self.env['res.users'].browse(self.env.uid)
        is_full_admin = bool(caller.exists() and caller._tp_is_main_admin())
        protected_users = _system_protected_users(self.env)
        for employee in self:
            if not is_full_admin:
                employee.tp_can_manage_account = False
                continue
            emp_sudo = employee.sudo()
            if emp_sudo.company_id != self.env.company:
                employee.tp_can_manage_account = False
                continue
            target = emp_sudo.user_id.with_context(active_test=False)
            if not target:
                employee.tp_can_manage_account = True
                continue
            # Self, system accounts, Original Admins, and active System Admins keep HR account
            # lock/reset protected (revoke admin grant first if managing a Granted Admin).
            if (target.id == caller.id or target in protected_users or target.share
                    or _is_protected_original_target(target) or target.has_group('base.group_system')):
                employee.tp_can_manage_account = False
                continue
            employee.tp_can_manage_account = not bool(
                set(target.company_ids.ids) - set(self.env.companies.ids),
            )

    def _access_domain(self, operation):
        return super()._access_domain(operation)

    def _tp_delegated_account_check(self, existing=False, lock=True):
        raise AccessError(self.env._('Mô hình ủy quyền theo phòng ban đã ngừng sử dụng; dùng quyền Quản trị viên toàn hệ thống.'))

    def _tp_account_admin(self, existing=False, login_rename=False):
        return super()._tp_account_admin(existing, login_rename=login_rename)

    def action_open_account_dialog(self):
        return super().action_open_account_dialog()

    def action_reset_user_password(self):
        return super().action_reset_user_password()


class DelegatedAccountUser(models.Model):
    _inherit = 'res.users'

    @api.model
    def tp_get_my_profile(self):
        result = super().tp_get_my_profile()
        if result.get('has_employee'):
            capabilities = self.get_tp_admin_capabilities()
            level_map = {
                'main': ORIGINAL_ADMIN_LABEL,
                'delegated': GRANTED_ADMIN_LABEL,
                'business': BUSINESS_USER_LABEL,
            }
            result['header']['admin_level'] = level_map[capabilities['level']]
            result['header']['admin_scope'] = (
                capabilities['scope'] or 'Theo vai trò và phân công nghiệp vụ hiện hành.'
            )
        return result

    def _tp_assert_delegated_account_target(self, lock=True):
        raise AccessError(self.env._('Mô hình ủy quyền theo phòng ban đã ngừng sử dụng.'))

    def _tp_set_account_lock(self, locked, reason):
        if _is_protected_original_target(self):
            raise UserError(self.env._('Tài khoản Quản trị gốc được bảo vệ, không được khóa.'))
        if self.sudo().with_context(active_test=False).has_group('base.group_system'):
            raise UserError(self.env._('Hãy thu hồi quyền Quản trị viên trước khi khóa tài khoản này.'))
        return super()._tp_set_account_lock(locked, reason)


class DelegatedAccountWizard(models.TransientModel):
    _inherit = 'tp.hr.account.wizard'

    def _compute_info(self):
        super()._compute_info()
        for wizard in self:
            wizard.is_admin = bool(wizard.employee_id.tp_can_manage_account)

    def _tp_checked_account(self):
        if self.env.user._tp_is_main_admin():
            return self
        return self.with_context({
            'lang': self.env.lang,
            'tz': self.env.user.tz,
            'allowed_company_ids': self.env.companies.ids,
            '_tp_delegated_account': _ACCOUNT,
        })
