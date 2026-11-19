"""HR account management and personal profile labels for Original and Granted Full Admins."""
from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import AccessError

from .delegation import (
    BUSINESS_USER_LABEL,
    GRANTED_ADMIN_LABEL,
    ORIGINAL_ADMIN_LABEL,
    _system_protected_users,
)
from .guards import (
    _ACCOUNT,
    account_actor_uid,
    account_target_kind,
    assert_can_manage_account_targets,
    can_manage_account_target,
)


class DelegatedEmployee(models.Model):
    _inherit = 'hr.employee'

    tp_can_manage_account = fields.Boolean(compute='_compute_tp_can_manage_account')

    @api.depends('user_id', 'company_id', 'department_id')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_tp_can_manage_account(self):
        caller = self.env['res.users'].browse(account_actor_uid(self.env))
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
            if (target.id == caller.id or target in protected_users or target.share
                    or not can_manage_account_target(self.env, target)):
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

    tp_account_profile_readonly = fields.Boolean(compute='_compute_tp_account_profile_readonly')

    @api.depends('group_ids', 'active')
    @api.depends_context('uid')
    def _compute_tp_account_profile_readonly(self):
        actor = self.env['res.users'].browse(account_actor_uid(self.env))
        for target in self:
            target.tp_account_profile_readonly = bool(
                actor._tp_is_main_admin() and target.id != actor.id
                and not can_manage_account_target(self.env, target),
            )

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        result = super().get_view(view_id, view_type, **options)
        if view_type == 'form':
            arch = etree.fromstring(result['arch'])
            arch.set('js_class', 'tp_admin_protected_user_form')
            for node in arch.xpath("//field[not(ancestor::field)]"):
                previous = node.get('readonly', 'False')
                node.set('readonly', f'({previous}) or tp_account_profile_readonly')
            for node in arch.xpath("//button[not(ancestor::field)]"):
                previous = node.get('invisible', 'False')
                node.set('invisible', f'({previous}) or tp_account_profile_readonly')
            sheet = arch.find('sheet')
            if sheet is not None:
                sheet.insert(0, etree.Element('field', name='tp_account_profile_readonly', invisible='1'))
                notice = etree.Element('div', {'class': 'alert alert-info', 'role': 'status',
                                              'invisible': 'not tp_account_profile_readonly'})
                notice.text = 'Chỉ admin gốc được thay đổi tài khoản hoặc hồ sơ của admin ủy quyền khác.'
                sheet.insert(1, notice)
            result['arch'] = etree.tostring(arch, encoding='unicode')
            result['models'] = {**result['models'], self._name: (
                set(result['models'].get(self._name, ())) | {'tp_account_profile_readonly'}
            )}
        return result

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
        self.ensure_one()
        assert_can_manage_account_targets(self.env, self)
        with self.env.cr.savepoint():
            self.env.cr.execute('SELECT id FROM res_users WHERE id=%s FOR UPDATE', [self.id])
            self.invalidate_recordset(['active', 'tp_hr_locked', 'tp_lock_revision'])
            before = {key: self[key] for key in ('active', 'tp_hr_locked', 'tp_lock_revision')}
            result = super()._tp_set_account_lock(locked, reason)
            actor = self.env['res.users'].sudo().browse(account_actor_uid(self.env))
            employees = self.env['hr.employee'].sudo().with_context(active_test=False).search([
                ('user_id', '=', self.id),
            ])
            employee = employees[:1]
            self.env['tp.hr.employee.audit']._tp_record([{
                'action': 'account_lock' if locked else 'account_unlock',
                'employee_ref': employee.id or 0, 'employee_name': employee.name or '',
                'employee_code': employee.tp_employee_code or '',
                'company_id': (employee.company_id or self.company_id).id,
                'actor_id': actor.id, 'actor_name': actor.name,
                'account_ref': self.id, 'account_login': self.login,
                'account_action': 'locked' if locked else 'kept', 'reason': reason.strip(),
                'snapshot': {'before': before, 'after': {
                    key: self[key] for key in before
                }},
            }])
        return result


class DelegatedAccountWizard(models.TransientModel):
    _inherit = 'tp.hr.account.wizard'

    account_kind = fields.Selection([('original_admin', 'Admin gốc'),
                                     ('granted_admin', 'Admin ủy quyền'),
                                     ('employee', 'Nhân viên')], compute='_compute_info', string='Loại tài khoản')
    profile_readonly = fields.Boolean(related='employee_id.tp_account_profile_readonly')

    def _compute_info(self):
        super()._compute_info()
        for wizard in self:
            wizard.is_admin = bool(wizard.employee_id.tp_can_manage_account)
            target = wizard.employee_id.sudo().with_context(active_test=False).user_id
            wizard.account_kind = account_target_kind(target) if target else 'employee'

    def _tp_checked_account(self):
        if self.env.user._tp_is_main_admin():
            return self
        return self.with_context({
            'lang': self.env.lang,
            'tz': self.env.user.tz,
            'allowed_company_ids': self.env.companies.ids,
            '_tp_delegated_account': _ACCOUNT,
        })


class AccountLockAudit(models.Model):
    _inherit = 'tp.hr.employee.audit'

    action = fields.Selection(selection_add=[('account_lock', 'Khóa tài khoản'),
                                             ('account_unlock', 'Mở tài khoản')],
                              ondelete={'account_lock': 'cascade', 'account_unlock': 'cascade'})
