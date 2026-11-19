"""Backend enforcement of DEC-054 (Original-Admin-only admin provisioning & security boundaries)
and preservation of HR-DELEGATE-FIX-001 field-group privacy for non-HR users.

- Granted Full Administrators operate across all departments and business modules with full native
  admin rights, EXCEPT they cannot grant/revoke admin rights, tamper with Original Administrators
  or other Administrators, alter protected admin/security groups, or bypass DEC-054 via technical
  code/ACL/module/XMLID vectors — even when entering through `.sudo()`, import, copy, or defaults.
- System always preserves at least one active Original Administrator.
"""
from odoo import SUPERUSER_ID, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.http import request

from .delegation import (
    LOCK_NAMESPACE,
    _system_protected_users,
)
from odoo.addons.tp_hr_workspace.models.my_profile import (
    SELF_EDITABLE_MANY2ONE_FIELDS,
    SELF_EDITABLE_SCALAR_FIELDS,
)

# Retained sentinels imported by HR/adapter modules.
_ACCOUNT = object()
_PROFILE = object()
_PROFILE_CREATE = object()
_SETTINGS_EXEC = object()

_SELF_FIELDS = set(SELF_EDITABLE_SCALAR_FIELDS) | set(SELF_EDITABLE_MANY2ONE_FIELDS)
_PROTECTED_ADMIN_GROUP_XMLIDS = (
    'tp_admin_delegation.group_original_admin',
    'tp_admin_delegation.group_full_admin',
    'base.group_system',
    'base.group_erp_manager',
)
_SENSITIVE_PARAM_EXACT = frozenset({
    'database.secret',
    'web.base.url',
    'web.base.url.freeze',
    'auth_signup.allow_uninvited',
    'auth_signup.reset_password',
    'base.login_cooldown_after',
    'base.login_cooldown_duration',
})
_SENSITIVE_PARAM_PREFIXES = ('tp_admin',)
_SENSITIVE_XMLID_MODELS = frozenset({
    'res.users',
    'res.groups',
    'res.groups.privilege',
    'ir.access',
    'ir.actions.server',
    'ir.cron',
    'ir.module.module',
    'ir.ui.view',
    'ir.ui.menu',
    'tp.admin.delegation',
})


def account_actor_uid(env):
    """sudo/context must never replace the authenticated HTTP actor."""
    if request and request.session and request.session.uid:
        return request.session.uid
    return env.uid


def _is_trusted_original_or_cli(env):
    actor_uid = account_actor_uid(env)
    if actor_uid == SUPERUSER_ID and not request:
        return True  # Module loader / server-side CLI, not an administrator identity.
    caller = env['res.users'].sudo().with_context(active_test=False).browse(actor_uid)
    return bool(caller.exists() and caller._tp_is_original_admin())


def account_target_kind(user):
    user.ensure_one()
    user = user.sudo().with_context(active_test=False)
    if _is_protected_original_target(user):
        return 'original_admin'
    full_group = user.env.ref('tp_admin_delegation.group_full_admin', raise_if_not_found=False)
    if user._tp_has_live_admin_grant() or (full_group and full_group.sudo() in user.all_group_ids):
        return 'granted_admin'
    return 'employee'


def can_manage_account_target(env, user, allow_self=False):
    """Shared account/profile boundary; callers must also check business capability."""
    if _is_trusted_original_or_cli(env):
        return True
    if user.id == account_actor_uid(env):
        return bool(allow_self and account_target_kind(user) != 'original_admin')
    return account_target_kind(user) == 'employee'


def _lock_account_targets(env, users):
    """Serialize identity writes with grants without changing the session revision."""
    if env.cr.readonly or not users:
        return
    users = users.sudo().with_context(active_test=False).sorted('id')
    for user in users:
        env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [LOCK_NAMESPACE, user.id])
    env.cr.execute('SELECT id FROM res_users WHERE id IN %s ORDER BY id FOR UPDATE', [tuple(users.ids)])
    users.invalidate_recordset(['active', 'share', 'company_ids', 'group_ids', 'all_group_ids'])


def assert_can_manage_account_targets(env, users, allow_self=False):
    _lock_account_targets(env, users)
    if any(not can_manage_account_target(env, user, allow_self=allow_self)
           for user in users.sudo().with_context(active_test=False)):
        raise AccessError(env._(
            'Chỉ admin gốc được thay đổi tài khoản hoặc hồ sơ của admin ủy quyền khác.',
        ))


def _require_original_admin(env, message=None):
    if not _is_trusted_original_or_cli(env):
        raise AccessError(
            message
            or env._('Thao tác quản trị bảo mật/cấp quyền quản trị này chỉ dành cho Quản trị gốc.'),
        )


def _protected_admin_groups(env):
    """Every group that directly is, or transitively implies, any system/admin authority."""
    anchors = env['res.groups'].sudo().browse()
    for xmlid in _PROTECTED_ADMIN_GROUP_XMLIDS:
        grp = env.ref(xmlid, raise_if_not_found=False)
        if grp and grp._name == 'res.groups':
            anchors |= grp.sudo()
    if not anchors:
        return anchors
    all_groups = env['res.groups'].sudo().search([])
    return all_groups.filtered(lambda g: bool(g.all_implied_ids & anchors))


def _is_protected_original_target(user):
    user = user.sudo().with_context(active_test=False)
    if not user:
        return False
    for xmlid in ('base.user_root', 'base.user_admin'):
        ref = user.env.ref(xmlid, raise_if_not_found=False)
        if ref and ref.id == user.id:
            return True
    orig_group = user.env.ref('tp_admin_delegation.group_original_admin', raise_if_not_found=False)
    if orig_group and orig_group.sudo() in user.all_group_ids and not user._tp_has_live_admin_grant():
        return True
    return user._tp_is_original_admin()


def _assert_at_least_one_original_admin(env):
    """Prevent locking, archiving, deleting, or stripping the last active Original Admin."""
    orig_group = env.ref('tp_admin_delegation.group_original_admin', raise_if_not_found=False)
    group_system = env.ref('base.group_system', raise_if_not_found=False)
    if not orig_group or not group_system:
        return
    env.flush_all()
    candidates = env['res.users'].sudo().search([
        ('active', '=', True),
        ('share', '=', False),
    ])
    live_originals = [u for u in candidates if u._tp_is_original_admin()]
    if not live_originals:
        raise UserError(env._('Hệ thống phải luôn giữ ít nhất một Quản trị gốc đang hoạt động.'))


def delegate_actor(env, lock=False):
    """Compatibility helper: limited-department delegation is retired; returns False."""
    return False


def deny_authority(env):
    """Enforce Original-Admin-only boundary for security/provisioning mutations."""
    _require_original_admin(env)


def lock_scope_users(env, users):
    for user in users.sudo().sorted('id'):
        if not env.cr.readonly:
            user._tp_admin_lock(exclusive=True)


def lock_live_delegates(env):
    if env.cr.readonly:
        return
    env.cr.execute("SELECT DISTINCT user_id FROM tp_admin_delegation WHERE state='active' ORDER BY user_id")
    lock_scope_users(env, env['res.users'].browse([row[0] for row in env.cr.fetchall()]))


class ProtectedUser(models.Model):
    _inherit = 'res.users'

    def _tp_can_manage_account_target(self, allow_self=False):
        self.ensure_one()
        return can_manage_account_target(self.env, self, allow_self=allow_self)

    def _tp_admin_group_state(self, protected_groups):
        u = self.sudo().with_context(active_test=False)
        return (
            frozenset((u.group_ids & protected_groups).ids),
            frozenset((u.all_group_ids & protected_groups).ids),
        )

    @api.model_create_multi
    def create(self, vals_list):
        trusted = _is_trusted_original_or_cli(self.env)
        if not trusted:
            for vals in vals_list:
                _assert_profile_commands(self.env, vals)
                partner_id = vals.get('partner_id', self.env.context.get('default_partner_id'))
                if partner_id:
                    self.env['res.partner'].browse(partner_id)._tp_check_partner_admin_boundary(vals=vals)
        users = super().create(vals_list)
        if not trusted:
            protected_groups = _protected_admin_groups(self.env)
            for user in users.sudo().with_context(active_test=False):
                direct_adm, eff_adm = user._tp_admin_group_state(protected_groups)
                if direct_adm or eff_adm:
                    raise AccessError(self.env._(
                        'Chỉ Quản trị gốc được tạo tài khoản có quyền quản trị hệ thống.',
                    ))
        return users

    def write(self, vals):
        if not self:
            return super().write(vals)
        trusted = _is_trusted_original_or_cli(self.env)
        protected_groups = _protected_admin_groups(self.env)
        targets = self.sudo().with_context(active_test=False)

        _lock_account_targets(self.env, targets)
        touches_orig = any(_is_protected_original_target(u) for u in targets)
        if touches_orig and not self.env.cr.readonly:
            self.env.cr.execute(
                'SELECT id FROM res_users WHERE id IN %s ORDER BY id FOR UPDATE',
                [tuple(sorted(targets.ids))],
            )

        if not trusted:
            for target in targets:
                if _is_protected_original_target(target):
                    raise AccessError(self.env._(
                        'Tài khoản Quản trị gốc được bảo vệ; chỉ Quản trị gốc được thay đổi.',
                    ))
                # Another administrator (e.g. a peer Granted Admin) cannot be locked, edited,
                # or have credentials/groups altered by a non-Original-Admin.
                if target.id == account_actor_uid(self.env) and account_target_kind(target) == 'granted_admin':
                    allowed = {'email', 'phone', 'mobile', 'lang', 'tz', 'signature', 'password', 'new_password',
                               'image_1920', 'image_1024', 'image_512', 'image_256', 'image_128',
                               'totp_secret', 'totp_trusted_device_ids'}
                    if set(vals) - allowed:
                        raise AccessError(self.env._('Tài khoản của mình chỉ được sửa qua chức năng cá nhân được phép.'))
                _dir, eff = target._tp_admin_group_state(protected_groups)
                if target.id != account_actor_uid(self.env) and (eff or account_target_kind(target) == 'granted_admin'):
                    raise AccessError(self.env._(
                        'Chỉ admin gốc được thay đổi tài khoản hoặc hồ sơ của admin ủy quyền khác.',
                    ))

        if not trusted:
            _assert_profile_commands(self.env, vals)
        if not trusted and vals.get('partner_id'):
            self.env['res.partner'].browse(vals['partner_id'])._tp_check_partner_admin_boundary(vals=vals)
        audit_before = _profile_audit_snapshot(self, vals)
        before_states = {u.id: u._tp_admin_group_state(protected_groups) for u in targets}
        res = super().write(vals)

        if not trusted:
            protected_after = _protected_admin_groups(self.env)
            for target in targets:
                target.invalidate_recordset(['group_ids', 'all_group_ids', 'role'])
                after_state = target._tp_admin_group_state(protected_after)
                if after_state != before_states[target.id]:
                    raise AccessError(self.env._(
                        'Chỉ Quản trị gốc được cấp hoặc thu hồi quyền quản trị hệ thống.',
                    ))

        if touches_orig or ('active' in vals or 'group_ids' in vals or 'role' in vals
                            or any(k.startswith(('in_group_', 'sel_groups_')) for k in vals)):
            _assert_at_least_one_original_admin(self.env)

        _record_profile_audit(self, vals, audit_before)
        return res

    def unlink(self):
        targets = self.sudo().with_context(active_test=False)
        protected_users = _system_protected_users(self.env)
        if any(_is_protected_original_target(u) or u in protected_users for u in targets):
            raise AccessError(self.env._('Không được xóa tài khoản hệ thống hoặc Quản trị gốc.'))
        if not _is_trusted_original_or_cli(self.env):
            protected_groups = _protected_admin_groups(self.env)
            if any((account_target_kind(u) != 'employee' or bool(u.all_group_ids & protected_groups)) for u in targets):
                raise AccessError(self.env._('Chỉ Quản trị gốc được xóa hoặc gỡ tài khoản quản trị viên.'))
        res = super().unlink()
        _assert_at_least_one_original_admin(self.env)
        return res

    def _change_password(self, new_passwd):
        if not _is_trusted_original_or_cli(self.env):
            protected_groups = _protected_admin_groups(self.env)
            for target in self.sudo().with_context(active_test=False):
                if target.id == account_actor_uid(self.env):
                    continue
                if _is_protected_original_target(target) or (account_target_kind(target) != 'employee' or bool(target.all_group_ids & protected_groups)):
                    raise AccessError(self.env._(
                        'Không được đổi mật khẩu của Quản trị gốc hoặc Quản trị viên khác.',
                    ))
        return super()._change_password(new_passwd)

    def action_reset_password(self):
        if not _is_trusted_original_or_cli(self.env):
            protected_groups = _protected_admin_groups(self.env)
            for target in self.sudo().with_context(active_test=False):
                if target.id == account_actor_uid(self.env):
                    continue
                if _is_protected_original_target(target) or (account_target_kind(target) != 'employee' or bool(target.all_group_ids & protected_groups)):
                    raise AccessError(self.env._(
                        'Không được đặt lại mật khẩu của Quản trị gốc hoặc Quản trị viên khác.',
                    ))
        return super().action_reset_password()

    def get_reset_password_link(self):
        if not _is_trusted_original_or_cli(self.env):
            protected_groups = _protected_admin_groups(self.env)
            for target in self.sudo().with_context(active_test=False):
                if target.id == account_actor_uid(self.env):
                    continue
                if _is_protected_original_target(target) or (account_target_kind(target) != 'employee' or bool(target.all_group_ids & protected_groups)):
                    raise AccessError(self.env._(
                        'Không được lấy liên kết đặt lại mật khẩu của Quản trị gốc hoặc Quản trị viên khác.',
                    ))
        return super().get_reset_password_link()


class ProtectedChangePasswordWizard(models.TransientModel):
    _inherit = 'change.password.wizard'

    def change_password_button(self):
        if not _is_trusted_original_or_cli(self.env):
            protected_groups = _protected_admin_groups(self.env)
            for line in self.sudo().user_ids:
                target = line.user_id
                if target and target.id != account_actor_uid(self.env) and (
                    _is_protected_original_target(target) or (account_target_kind(target) != 'employee' or bool(target.all_group_ids & protected_groups))
                ):
                    raise AccessError(self.env._(
                        'Chỉ Quản trị gốc được đặt lại mật khẩu của tài khoản quản trị.',
                    ))
        return super().change_password_button()


class ProtectedChangePasswordUser(models.TransientModel):
    _inherit = 'change.password.user'

    def change_password_button(self):
        if not _is_trusted_original_or_cli(self.env):
            protected_groups = _protected_admin_groups(self.env)
            for line in self.sudo():
                target = line.user_id
                if target and target.id != account_actor_uid(self.env) and (
                    _is_protected_original_target(target) or (account_target_kind(target) != 'employee' or bool(target.all_group_ids & protected_groups))
                ):
                    raise AccessError(self.env._(
                        'Chỉ Quản trị gốc được đặt lại mật khẩu của tài khoản quản trị.',
                    ))
        return super().change_password_button()


class ProtectedApiKeys(models.Model):
    _inherit = 'res.users.apikeys'

    def _remove(self):
        if not _is_trusted_original_or_cli(self.env):
            for key in self.sudo():
                if key.user_id.id != account_actor_uid(self.env) and account_target_kind(key.user_id) != 'employee':
                    raise AccessError(self.env._('Không được gỡ khóa API của Quản trị gốc.'))
        return super()._remove()


class ProtectedTotpDevice(models.Model):
    _inherit = 'auth_totp.device'

    def _remove(self):
        if not _is_trusted_original_or_cli(self.env):
            for dev in self.sudo():
                if dev.user_id.id != account_actor_uid(self.env) and account_target_kind(dev.user_id) != 'employee':
                    raise AccessError(self.env._('Không được gỡ thiết bị xác thực của Quản trị gốc.'))
        return super()._remove()


class ProtectedGroups(models.Model):
    _inherit = 'res.groups'

    def _tp_group_security_snapshot(self):
        protected = _protected_admin_groups(self.env)
        full_group = self.env.ref('tp_admin_delegation.group_full_admin', raise_if_not_found=False)
        orig_group = self.env.ref('tp_admin_delegation.group_original_admin', raise_if_not_found=False)
        return {
            'protected_ids': frozenset(protected.ids),
            'memberships': {g.id: frozenset(g.sudo().with_context(active_test=False).user_ids.ids) for g in protected},
            'full_implied': frozenset(full_group.sudo().implied_ids.ids) if full_group else frozenset(),
            'orig_implied': frozenset(orig_group.sudo().implied_ids.ids) if orig_group else frozenset(),
        }

    @api.model_create_multi
    def create(self, vals_list):
        _require_original_admin(
            self.env,
            self.env._('Tạo nhóm quyền bảo mật mới chỉ dành cho Quản trị gốc.'),
        )
        return super().create(vals_list)

    def write(self, vals):
        trusted = _is_trusted_original_or_cli(self.env)
        if not trusted:
            protected = _protected_admin_groups(self.env)
            if self.sudo() & protected:
                raise AccessError(self.env._('Nhóm quyền quản trị hệ thống chỉ do Quản trị gốc thay đổi.'))
            if set(vals) - {'implied_ids'}:
                raise AccessError(self.env._('Sửa cấu trúc hoặc thành viên nhóm quyền chỉ dành cho Quản trị gốc.'))
            before = self._tp_group_security_snapshot()
            res = super().write(vals)
            self.env.flush_all()
            self.env.invalidate_all()
            after = self._tp_group_security_snapshot()
            if after != before:
                raise AccessError(self.env._('Không được thêm quyền quản trị hệ thống qua nhóm kế thừa.'))
            return res

        res = super().write(vals)
        _assert_at_least_one_original_admin(self.env)
        return res

    def unlink(self):
        _require_original_admin(
            self.env,
            self.env._('Xóa nhóm quyền bảo mật chỉ dành cho Quản trị gốc.'),
        )
        for xmlid in _PROTECTED_ADMIN_GROUP_XMLIDS:
            grp = self.env.ref(xmlid, raise_if_not_found=False)
            if grp and grp in self:
                raise AccessError(self.env._('Không được xóa nhóm quyền quản trị cốt lõi của hệ thống.'))
        res = super().unlink()
        _assert_at_least_one_original_admin(self.env)
        return res


class ProtectedGroupsPrivilege(models.Model):
    _inherit = 'res.groups.privilege'

    @api.model_create_multi
    def create(self, vals_list):
        _require_original_admin(self.env)
        return super().create(vals_list)

    def write(self, vals):
        _require_original_admin(self.env)
        return super().write(vals)

    def unlink(self):
        _require_original_admin(self.env)
        return super().unlink()


class ProtectedEmployee(models.Model):
    _inherit = 'hr.employee'

    def _tp_assert_not_original_admin_employee(self, vals=None):
        if _is_trusted_original_or_cli(self.env):
            return
        assert_can_manage_account_targets(self.env, self.sudo().mapped('user_id'), allow_self=True)
        own = self.sudo().filtered(lambda emp: emp.user_id.id == account_actor_uid(self.env)
                                  and account_target_kind(emp.user_id) == 'granted_admin')
        if own and vals and set(vals) - _SELF_FIELDS:
            raise AccessError(self.env._('Hồ sơ của mình chỉ được sửa thông tin cá nhân trong danh sách cho phép.'))
        if vals:
            _assert_profile_links(self.env, vals)

    @api.model_create_multi
    def create(self, vals_list):
        if not _is_trusted_original_or_cli(self.env):
            for vals in vals_list:
                _assert_profile_links(self.env, vals, defaults=True)
        # Preserve HR-DELEGATE-FIX-001: non-HR actors cannot inject restricted fields (e.g. mobile_phone)
        # via create values or default_* context even through sudo().
        if self.env.uid != SUPERUSER_ID and not self.env.user.has_group('hr.group_hr_user'):
            caller = self.sudo(False)
            for key, field in caller._fields.items():
                if f'default_{key}' in self.env.context and not caller._has_field_access(field, 'write'):
                    raise AccessError(self.env._('Không có quyền ghi trường nhân sự bị giới hạn.'))
            for vals in vals_list:
                for key in vals:
                    field = caller._fields.get(key)
                    if field and not caller._has_field_access(field, 'write'):
                        raise AccessError(self.env._('Không có quyền ghi trường nhân sự bị giới hạn.'))
        return super().create(vals_list)

    def write(self, vals):
        self._tp_assert_not_original_admin_employee(vals)
        # Preserve HR-DELEGATE-FIX-001: non-HR actors cannot write restricted fields on other employees,
        # while keeping self-service profile updates (`tp_save_my_profile`) intact.
        if self.env.uid != SUPERUSER_ID and not self.env.user.has_group('hr.group_hr_user'):
            own = self.sudo().filtered(lambda emp: emp.user_id.id == self.env.uid)
            if own and set(vals) - _SELF_FIELDS:
                raise AccessError(self.env._('Hồ sơ của mình chỉ được sửa thông tin cá nhân trong danh sách cho phép.'))
            other = self.sudo() - own
            if other:
                caller = self.sudo(False)
                for key in vals:
                    field = caller._fields.get(key)
                    if field and not caller._has_field_access(field, 'write'):
                        raise AccessError(self.env._('Không có quyền ghi trường nhân sự bị giới hạn.'))
        audit_before = _profile_audit_snapshot(self, vals)
        result = super().write(vals)
        _record_profile_audit(self, vals, audit_before)
        return result

    def unlink(self):
        assert_can_manage_account_targets(self.env, self.sudo().mapped('user_id'), allow_self=False)
        self._tp_assert_not_original_admin_employee()
        return super().unlink()


class ProtectedPartner(models.Model):
    _inherit = 'res.partner'

    def _tp_check_partner_admin_boundary(self, vals=None, unlink=False):
        if _is_trusted_original_or_cli(self.env):
            return
        if vals:
            _assert_profile_commands(self.env, vals)
        partners = self.sudo().with_context(active_test=False)
        users = partners.mapped('user_ids')
        employees = self.env['hr.employee'].sudo().with_context(active_test=False).search([
            ('work_contact_id', 'in', partners.ids),
        ])
        assert_can_manage_account_targets(self.env, users | employees.mapped('user_id'), allow_self=not unlink)
        own = (users | employees.mapped('user_id')).filtered(lambda u: u.id == account_actor_uid(self.env) and account_target_kind(u) == 'granted_admin')
        if own and vals:
            allowed = {'email', 'phone', 'mobile', 'lang', 'tz', 'image_1920', 'image_1024', 'image_512',
                       'image_256', 'image_128', 'signup_type', 'signup_token', 'signup_expiration'}
            if set(vals) - allowed:
                raise AccessError(self.env._('Thông tin của mình chỉ được sửa qua chức năng cá nhân được phép.'))
        if vals and vals.get('user_ids'):
            raise AccessError(self.env._('Không được đổi liên kết tài khoản đăng nhập trực tiếp từ liên hệ.'))

    @api.model_create_multi
    def create(self, vals_list):
        if not _is_trusted_original_or_cli(self.env):
            for vals in vals_list:
                _assert_profile_commands(self.env, vals)
                if vals.get('user_ids') or self.env.context.get('default_user_ids'):
                    raise AccessError(self.env._('Không được đổi liên kết tài khoản đăng nhập trực tiếp từ liên hệ.'))
        return super().create(vals_list)

    def write(self, vals):
        self._tp_check_partner_admin_boundary(vals=vals, unlink=False)
        audit_before = _profile_audit_snapshot(self, vals)
        result = super().write(vals)
        _record_profile_audit(self, vals, audit_before)
        return result

    def unlink(self):
        self._tp_check_partner_admin_boundary(unlink=True)
        return super().unlink()


_AUDIT_PROFILE_FIELDS = frozenset({
    'name', 'login', 'email', 'phone', 'mobile', 'work_email', 'work_phone', 'mobile_phone',
    'active', 'tp_hr_locked', 'partner_id', 'user_id', 'resource_id', 'employee_id',
    'work_contact_id', 'department_id', 'job_id', 'job_title', 'company_id', 'company_ids',
    'lang', 'tz', 'image_1920', 'image_1024', 'image_512', 'image_256', 'image_128',
})


def _profile_audit_snapshot(records, vals):
    keys = set(vals) & (_AUDIT_PROFILE_FIELDS | _SELF_FIELDS) & set(records._fields)

    def value(record, key):
        if key.startswith('image_'):
            return bool(record[key])
        field = record._fields[key]
        if field.relational:
            return record[key].ids
        value = record[key]
        return value.isoformat() if hasattr(value, 'isoformat') else value
    return {record.id: {key: value(record, key) for key in keys} for record in records.sudo()}


def _record_profile_audit(records, vals, before):
    after = _profile_audit_snapshot(records, vals)
    actor = records.env['res.users'].sudo().browse(account_actor_uid(records.env))
    rows = []
    for record in records.sudo():
        old, new = before.get(record.id, {}), after.get(record.id, {})
        changed = {key: {'before': old[key], 'after': new[key]} for key in old if old[key] != new[key]}
        # Binary contents and credentials never enter the audit payload.
        credential_changed = bool(set(vals) & {'password', 'new_password', 'totp_secret'})
        if not changed and not credential_changed and not any(key.startswith('image_') for key in vals):
            continue
        if record._name == 'hr.employee':
            employees = record
        elif record._name == 'hr.version':
            employees = record.employee_id
        else:
            field = {'res.users': 'user_id', 'res.partner': 'work_contact_id',
                     'resource.resource': 'resource_id'}[record._name]
            employees = records.env['hr.employee'].sudo().with_context(active_test=False).search([(field, '=', record.id)])
        if record._name == 'res.partner' and not employees and not record.with_context(active_test=False).user_ids:
            continue
        user = record if record._name == 'res.users' else (employees[:1].user_id if employees else records.env['res.users'])
        if not user and record._name == 'res.partner':
            user = record.with_context(active_test=False).user_ids[:1]
        if not user and record._name == 'resource.resource':
            user = record.user_id
        company = employees[:1].company_id if employees else records.env.company
        rows.append({
            'action': 'account_profile_change', 'employee_ref': employees[:1].id or 0,
            'employee_name': employees[:1].name if employees else '',
            'company_id': company.id, 'actor_id': actor.id, 'actor_name': actor.name,
            'account_ref': user.id or 0, 'account_login': user.login if user else '',
            'reason': records.env._('Cập nhật tài khoản/hồ sơ qua %(model)s #%(id)s', model=record._name, id=record.id),
            'snapshot': {'model': record._name, 'record_id': record.id, 'changes': changed,
                         'image_changed': any(key.startswith('image_') for key in vals),
                         'credential_changed': credential_changed},
        })
    if rows:
        records.env['tp.hr.employee.audit']._tp_record(rows)


class AccountProfileAudit(models.Model):
    _inherit = 'tp.hr.employee.audit'

    action = fields.Selection(selection_add=[('account_profile_change', 'Thay đổi tài khoản/hồ sơ')],
                              ondelete={'account_profile_change': 'cascade'})


def _assert_profile_commands(env, vals):
    """Preflight profile inverse commands before their parent can write any fields."""
    for field, model in (('employee_ids', 'hr.employee'), ('version_ids', 'hr.version')):
        commands = vals.get(field, env.context.get('default_' + field, ()))
        for command in commands or ():
            operation = command[0]
            ids = command[2] if operation == 6 else ([command[1]] if operation in (1, 2, 3, 4) else [])
            if ids:
                records = env[model].sudo().with_context(active_test=False).browse(ids)
                users = records.mapped('user_id' if model == 'hr.employee' else 'employee_id.user_id')
                assert_can_manage_account_targets(env, users, allow_self=False)
            if operation in (0, 1) and isinstance(command[2], dict):
                _assert_profile_links(env, command[2])


def _assert_profile_links(env, vals, defaults=False):
    _assert_profile_commands(env, vals)
    for field, model in (('user_id', 'res.users'), ('resource_id', 'resource.resource'),
                         ('employee_id', 'hr.employee'), ('work_contact_id', 'res.partner')):
        value = vals.get(field, env.context.get('default_' + field) if defaults else None)
        if not value:
            continue
        linked = env[model].sudo().with_context(active_test=False).browse(value)
        if model == 'res.partner':
            linked._tp_check_partner_admin_boundary()
        else:
            users = linked if model == 'res.users' else linked.mapped('user_id')
            assert_can_manage_account_targets(env, users, allow_self=False)


class ProtectedResource(models.Model):
    _inherit = 'resource.resource'

    @api.model_create_multi
    def create(self, vals_list):
        if not _is_trusted_original_or_cli(self.env):
            for vals in vals_list:
                _assert_profile_links(self.env, vals, defaults=True)
        return super().create(vals_list)

    def write(self, vals):
        assert_can_manage_account_targets(self.env, self.sudo().mapped('user_id'), allow_self=True)
        if not _is_trusted_original_or_cli(self.env):
            own = self.sudo().filtered(lambda r: r.user_id.id == account_actor_uid(self.env) and account_target_kind(r.user_id) == 'granted_admin')
            if own and set(vals) - {'tz'}:
                raise AccessError(self.env._('Không được tự sửa tài nguyên định danh ngoài chức năng cá nhân.'))
        if not _is_trusted_original_or_cli(self.env):
            _assert_profile_links(self.env, vals)
        audit_before = _profile_audit_snapshot(self, vals)
        result = super().write(vals)
        _record_profile_audit(self, vals, audit_before)
        return result

    def unlink(self):
        assert_can_manage_account_targets(self.env, self.sudo().mapped('user_id'), allow_self=False)
        return super().unlink()


class ProtectedHrVersion(models.Model):
    _inherit = 'hr.version'

    @api.model_create_multi
    def create(self, vals_list):
        if not _is_trusted_original_or_cli(self.env):
            for vals in vals_list:
                _assert_profile_links(self.env, vals, defaults=True)
        return super().create(vals_list)

    def write(self, vals):
        assert_can_manage_account_targets(self.env, self.sudo().mapped('employee_id.user_id'), allow_self=True)
        if not _is_trusted_original_or_cli(self.env):
            own = self.sudo().filtered(lambda r: r.employee_id.user_id.id == account_actor_uid(self.env)
                                      and account_target_kind(r.employee_id.user_id) == 'granted_admin')
            if own and set(vals) - _SELF_FIELDS:
                raise AccessError(self.env._('Hồ sơ của mình chỉ được sửa thông tin cá nhân trong danh sách cho phép.'))
        if not _is_trusted_original_or_cli(self.env):
            _assert_profile_links(self.env, vals)
        audit_before = _profile_audit_snapshot(self, vals)
        result = super().write(vals)
        _record_profile_audit(self, vals, audit_before)
        return result

    def unlink(self):
        assert_can_manage_account_targets(self.env, self.sudo().mapped('employee_id.user_id'), allow_self=False)
        return super().unlink()


class OriginalAdminOnlyMixin(models.AbstractModel):
    _name = 'tp.admin.original.only.mixin'
    _description = 'Restrict technical privilege-escalation models to Original Admin (DEC-054)'

    @api.model_create_multi
    def create(self, vals_list):
        _require_original_admin(self.env)
        return super().create(vals_list)

    def write(self, vals):
        _require_original_admin(self.env)
        return super().write(vals)

    def unlink(self):
        _require_original_admin(self.env)
        return super().unlink()


class ProtectedAccess(models.Model):
    _name = 'ir.access'
    _inherit = ['ir.access', 'tp.admin.original.only.mixin']


class ProtectedServerAction(models.Model):
    _name = 'ir.actions.server'
    _inherit = ['ir.actions.server', 'tp.admin.original.only.mixin']


class ProtectedCron(models.Model):
    _name = 'ir.cron'
    _inherit = ['ir.cron', 'tp.admin.original.only.mixin']

    def method_direct_trigger(self):
        _require_original_admin(self.env)
        return super().method_direct_trigger()


class ProtectedModelMeta(models.Model):
    _name = 'ir.model'
    _inherit = ['ir.model', 'tp.admin.original.only.mixin']


class ProtectedModelFields(models.Model):
    _name = 'ir.model.fields'
    _inherit = ['ir.model.fields', 'tp.admin.original.only.mixin']


class ProtectedUiView(models.Model):
    _name = 'ir.ui.view'
    _inherit = ['ir.ui.view', 'tp.admin.original.only.mixin']


class ProtectedAsset(models.Model):
    _name = 'ir.asset'
    _inherit = ['ir.asset', 'tp.admin.original.only.mixin']


class ProtectedUiMenu(models.Model):
    _name = 'ir.ui.menu'
    _inherit = ['ir.ui.menu', 'tp.admin.original.only.mixin']


class ProtectedModelData(models.Model):
    _inherit = 'ir.model.data'

    @api.model_create_multi
    def create(self, vals_list):
        if not _is_trusted_original_or_cli(self.env):
            if any(vals.get('model') in _SENSITIVE_XMLID_MODELS
                   or vals.get('module') in ('base', 'tp_admin_delegation', 'tp_core', 'hr')
                   for vals in vals_list):
                raise AccessError(self.env._('Định danh hệ thống/bảo mật chỉ do Quản trị gốc thay đổi.'))
        return super().create(vals_list)

    def write(self, vals):
        _require_original_admin(self.env, self.env._('Định danh hệ thống/bảo mật chỉ do Quản trị gốc thay đổi.'))
        return super().write(vals)

    def unlink(self):
        _require_original_admin(self.env, self.env._('Định danh hệ thống/bảo mật chỉ do Quản trị gốc thay đổi.'))
        return super().unlink()


class ProtectedModule(models.Model):
    _inherit = 'ir.module.module'

    def _tp_require_module_admin(self):
        _require_original_admin(
            self.env,
            self.env._('Cài đặt, nâng cấp hoặc gỡ ứng dụng hệ thống chỉ dành cho Quản trị gốc.'),
        )

    @api.model_create_multi
    def create(self, vals_list):
        self._tp_require_module_admin()
        return super().create(vals_list)

    def write(self, vals):
        self._tp_require_module_admin()
        return super().write(vals)

    def unlink(self):
        self._tp_require_module_admin()
        return super().unlink()

    def button_install(self):
        self._tp_require_module_admin()
        return super().button_install()

    def button_immediate_install(self):
        self._tp_require_module_admin()
        return super().button_immediate_install()

    def button_upgrade(self):
        self._tp_require_module_admin()
        return super().button_upgrade()

    def button_immediate_upgrade(self):
        self._tp_require_module_admin()
        return super().button_immediate_upgrade()

    def button_uninstall(self):
        self._tp_require_module_admin()
        return super().button_uninstall()

    def button_immediate_uninstall(self):
        self._tp_require_module_admin()
        return super().button_immediate_uninstall()

    def module_uninstall(self):
        self._tp_require_module_admin()
        return super().module_uninstall()


class ProtectedModuleUpdate(models.TransientModel):
    _inherit = 'base.module.update'

    def update_module(self):
        _require_original_admin(
            self.env,
            self.env._('Cập nhật danh sách ứng dụng hệ thống chỉ dành cho Quản trị gốc.'),
        )
        return super().update_module()


class ProtectedModuleUpgrade(models.TransientModel):
    _inherit = 'base.module.upgrade'

    def upgrade_module(self):
        _require_original_admin(
            self.env,
            self.env._('Áp dụng nâng cấp/gỡ ứng dụng hệ thống chỉ dành cho Quản trị gốc.'),
        )
        return super().upgrade_module()


class ProtectedModuleUninstall(models.TransientModel):
    _inherit = 'base.module.uninstall'

    def action_uninstall(self):
        _require_original_admin(
            self.env,
            self.env._('Gỡ ứng dụng hệ thống chỉ dành cho Quản trị gốc.'),
        )
        return super().action_uninstall()


class ProtectedConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def execute(self):
        return super(
            ProtectedConfigSettings,
            self.with_context(_tp_settings_execute=_SETTINGS_EXEC),
        ).execute()


class ProtectedConfig(models.Model):
    _inherit = 'ir.config_parameter'

    def _tp_is_sensitive_key(self, key):
        if not key:
            return False
        return key in _SENSITIVE_PARAM_EXACT or key.startswith(_SENSITIVE_PARAM_PREFIXES)

    @api.model_create_multi
    def create(self, vals_list):
        if not _is_trusted_original_or_cli(self.env):
            in_settings = self.env.context.get('_tp_settings_execute') is _SETTINGS_EXEC
            if not in_settings or any(self._tp_is_sensitive_key(v.get('key')) for v in vals_list):
                raise AccessError(self.env._('Tham số cấu hình bảo mật/hệ thống chỉ dành cho Quản trị gốc.'))
        return super().create(vals_list)

    def write(self, vals):
        if not _is_trusted_original_or_cli(self.env):
            in_settings = self.env.context.get('_tp_settings_execute') is _SETTINGS_EXEC
            if not in_settings:
                raise AccessError(self.env._('Tham số cấu hình hệ thống trực tiếp chỉ dành cho Quản trị gốc.'))
            for rec in self.sudo():
                new_key = vals.get('key', rec.key)
                if self._tp_is_sensitive_key(rec.key) or self._tp_is_sensitive_key(new_key):
                    new_val = vals.get('value', rec.value)
                    if new_key != rec.key or (new_val or '') != (rec.value or ''):
                        raise AccessError(self.env._('Tham số bảo mật hệ thống chỉ dành cho Quản trị gốc.'))
        return super().write(vals)

    def unlink(self):
        if not _is_trusted_original_or_cli(self.env):
            in_settings = self.env.context.get('_tp_settings_execute') is _SETTINGS_EXEC
            if not in_settings or any(self._tp_is_sensitive_key(rec.key) for rec in self.sudo()):
                raise AccessError(self.env._('Không được xóa tham số cấu hình bảo mật/hệ thống.'))
        return super().unlink()
