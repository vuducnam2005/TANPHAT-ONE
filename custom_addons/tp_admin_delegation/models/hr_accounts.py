"""Reuse the native HR account dialog with an unforgeable, target-checked adapter."""
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .guards import _ACCOUNT


class DelegatedEmployee(models.Model):
    _inherit = 'hr.employee'

    tp_can_manage_account = fields.Boolean(compute='_compute_tp_can_manage_account')

    @api.depends('user_id', 'company_id', 'department_id')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_tp_can_manage_account(self):
        for employee in self:
            try:
                employee._tp_delegated_account_check(existing=bool(employee.sudo().user_id), lock=False)
                employee.tp_can_manage_account = True
            except (AccessError, UserError):
                employee.tp_can_manage_account = self.env.user._tp_is_main_admin()

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        if operation == 'read':
            # HR field groups remain intact: own-department private fields never widen.
            return baseline | self.env.user._tp_delegation_domain(
                department_field='current_version_id.department_id')
        return baseline

    def _tp_delegated_account_check(self, existing=False, lock=True):
        self.ensure_one()
        if lock:
            self.env.cr.execute('SELECT id FROM hr_employee WHERE id=%s FOR SHARE', [self.id])
            self.env.cr.execute('SELECT id FROM hr_version WHERE employee_id=%s ORDER BY id FOR SHARE', [self.id])
        employee = self.sudo().with_context(version_id=False)
        actor = self.env.user
        if not actor._tp_delegated_other_department(
                employee.company_id, employee._get_version().department_id, lock=lock):
            raise AccessError(self.env._('Chỉ quản lý tài khoản thuộc phòng khác đã xác định trong phạm vi được ủy quyền.'))
        target = employee.user_id
        if existing and not target:
            raise UserError(self.env._('Nhân viên chưa có tài khoản.'))
        if not target:
            return employee
        target._tp_assert_delegated_account_target(lock=lock)
        # A shared/alternate identity is protected even if this one employee is outside.
        linked = self.env['hr.employee'].sudo().with_context(active_test=False, version_id=False).search([
            ('user_id', '=', target.id),
        ])
        for identity in linked:
            if not actor._tp_delegated_other_department(identity.company_id, identity._get_version().department_id, lock=lock):
                raise AccessError(self.env._('Một danh tính của tài khoản thuộc phòng được bảo vệ hoặc chưa xác định.'))
        return employee

    def _tp_account_admin(self, existing=False):
        if (not self.env.user._tp_is_main_admin()
                and self.env.context.get('_tp_delegated_account') is _ACCOUNT):
            return self._tp_delegated_account_check(existing)
        return super()._tp_account_admin(existing)

    def action_open_account_dialog(self):
        if self.env.user._tp_is_main_admin():
            return super().action_open_account_dialog()
        self._tp_delegated_account_check(existing=bool(self.sudo().user_id))
        self.check_access('read')
        wizard = self.env['tp.hr.account.wizard'].create({
            'employee_id': self.id, 'expected_user_id': self.sudo().user_id.id,
        })
        if not self.sudo().user_id:
            return wizard.action_prepare_credentials()
        return {'type': 'ir.actions.act_window', 'name': 'Tài khoản nhân viên', 'res_model': wizard._name,
                'res_id': wizard.id, 'view_mode': 'form', 'target': 'new',
                'views': [(self.env.ref('tp_hr_workspace.view_tp_hr_account_wizard_form').id, 'form')]}

    def action_reset_user_password(self):
        if self.env.user._tp_is_main_admin():
            return super().action_reset_user_password()
        self._tp_delegated_account_check(existing=True)
        wizard = self.env['tp.hr.account.wizard'].create({
            'employee_id': self.id, 'expected_user_id': self.sudo().user_id.id,
        })
        return wizard.action_prepare_credentials(reset=True)


class DelegatedAccountUser(models.Model):
    _inherit = 'res.users'

    @api.model
    def tp_get_my_profile(self):
        result = super().tp_get_my_profile()
        if result.get('has_employee'):
            capabilities = self.get_tp_admin_capabilities()
            result['header']['admin_level'] = {'main': 'Quản trị chính', 'delegated': 'Quản trị được ủy quyền',
                                              'business': 'Người dùng nghiệp vụ'}[capabilities['level']]
            result['header']['admin_scope'] = capabilities['scope'] or 'Theo vai trò và phân công nghiệp vụ hiện hành.'
        return result

    def _tp_assert_delegated_account_target(self, lock=True):
        self.ensure_one()
        if lock:
            self._tp_admin_lock()
        target = self.sudo()
        protected = self.env['res.users']
        for xmlid in ('base.user_root', 'base.user_admin', 'base.public_user',
                      'base.template_portal_user', 'base.default_user'):
            protected |= self.env.ref(xmlid, raise_if_not_found=False) or self.env['res.users']
        if target.id == self.env.uid or target in protected or target.share:
            raise AccessError(self.env._('Tài khoản hệ thống, tài khoản bên ngoài hoặc chính mình được bảo vệ.'))
        privileged = ('base.group_system', 'base.group_erp_manager', 'tp_core.group_manager', 'hr.group_hr_manager')
        if any(target.has_group(xmlid) for xmlid in privileged):
            raise AccessError(self.env._('Không quản lý thông tin đăng nhập của tài khoản đặc quyền.'))
        self.env.cr.execute("SELECT 1 FROM tp_admin_delegation WHERE user_id=%s AND state='active' LIMIT 1", [target.id])
        if self.env.cr.fetchone() or self.env['tp.kd.department.role'].sudo()._roles(target):
            raise AccessError(self.env._('Không quản lý tài khoản đang giữ quyền quản trị hoặc trưởng phòng.'))
        sensitive = {'res.users', 'res.groups', 'ir.access', 'ir.rule', 'ir.model.access',
                     'ir.config_parameter', 'ir.actions.server', 'ir.module.module'}
        self_only = self.env.ref('base.res_users_rule_write_self')
        if any(access != self_only and access.model_id.model in sensitive and any(op in access.operation for op in 'cud')
               for access in target.group_ids.all_implied_ids.access_ids):
            raise AccessError(self.env._('Tài khoản có quyền thay đổi bảo mật/hệ thống được bảo vệ.'))
        for company in target.company_ids:
            if company not in self.env.companies or not self.env.user._tp_has_admin_delegation(company, lock=lock):
                raise AccessError(self.env._('Tài khoản có công ty ngoài phạm vi ủy quyền.'))
        return target

    def _tp_set_account_lock(self, locked, reason):
        if self.env.user._tp_is_main_admin():
            return super()._tp_set_account_lock(locked, reason)
        if self.env.context.get('_tp_delegated_account') is not _ACCOUNT:
            raise AccessError(self.env._('Khóa/mở qua hộp quản lý tài khoản nhân viên đã kiểm phạm vi.'))
        target = self._tp_assert_delegated_account_target()
        if not isinstance(locked, bool) or not isinstance(reason, str) or not reason.strip():
            raise UserError(self.env._('Nhập lý do khóa hoặc mở tài khoản.'))
        self.env.cr.execute('SELECT id FROM res_users WHERE id=%s FOR UPDATE', [target.id])
        target.invalidate_recordset(['active', 'tp_hr_locked', 'tp_lock_revision'])
        if (locked and not target.active) or (not locked and target.active and not target.tp_hr_locked):
            raise UserError(self.env._('Tình trạng tài khoản đã thay đổi. Vui lòng mở lại hồ sơ.'))
        target.write({'active': not locked, 'tp_hr_locked': locked, 'tp_lock_revision': target.tp_lock_revision + 1})
        return True


class DelegatedAccountWizard(models.TransientModel):
    _inherit = 'tp.hr.account.wizard'

    def _tp_checked_account(self):
        if self.env.user._tp_is_main_admin():
            return self
        return self.with_context({'lang': self.env.lang, 'tz': self.env.user.tz,
                                  'allowed_company_ids': self.env.companies.ids,
                                  '_tp_delegated_account': _ACCOUNT})

    def _compute_info(self):
        super()._compute_info()
        for wizard in self:
            if not wizard.is_admin:
                wizard.is_admin = wizard.employee_id.tp_can_manage_account

    def _employee(self, existing=False):
        if self.env.user._tp_is_main_admin():
            return super()._employee(existing)
        checked = self._tp_checked_account()
        employee = super(DelegatedAccountWizard, checked)._employee(existing)
        return employee.sudo().with_context(_tp_delegated_account=_ACCOUNT)

    def action_set_password(self, password, confirmation):
        checked = self._tp_checked_account()
        return super(DelegatedAccountWizard, checked).action_set_password(password, confirmation)

    def action_create_user(self, login=None, password=None, confirmation=None):
        checked = self._tp_checked_account()
        return super(DelegatedAccountWizard, checked).action_create_user(login, password, confirmation)

    def _change_account_lock(self, locked):
        checked = self._tp_checked_account()
        return super(DelegatedAccountWizard, checked)._change_account_lock(locked)
