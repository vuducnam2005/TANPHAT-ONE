"""Concrete identity and authority boundaries, including callers using sudo()."""
from odoo import api, models
from odoo.exceptions import AccessError

from odoo.addons.tp_hr_workspace.models.my_profile import (
    SELF_EDITABLE_MANY2ONE_FIELDS,
    SELF_EDITABLE_SCALAR_FIELDS,
)

_ACCOUNT = object()
_PROFILE = object()
_PROFILE_CREATE = object()
_SELF_FIELDS = set(SELF_EDITABLE_SCALAR_FIELDS) | set(SELF_EDITABLE_MANY2ONE_FIELDS)
_JOB_METADATA = {'job_id', 'job_title'}
_EMPLOYEE_AUTHORITY = {
    'user_id', 'resource_id', 'company_id', 'department_id',
    'parent_id', 'coach_id', 'hr_responsible_id', 'current_version_id', 'version_id',
    'version_ids', 'work_contact_id', 'active', 'tp_employee_code', 'tp_source_code',
    'tp_source_department', 'tp_source_title', 'tp_source_snapshot', 'tp_import_batch_id',
}
_VERSION_AUTHORITY = {
    'employee_id', 'company_id', 'department_id', 'date_version',
    'active', 'contract_template_id', 'hr_responsible_id',
}
_USER_AUTHORITY = {
    'group_ids', 'groups_id', 'all_group_ids', 'company_id', 'company_ids', 'partner_id',
    'employee_ids', 'employee_id', 'resource_ids', 'active', 'share', 'login',
    'password', 'new_password', 'api_key_ids', 'totp_secret', 'totp_device_ids',
    'tp_hr_locked', 'tp_lock_revision',
    'tp_admin_scope_revision',
}


def delegate_actor(env, lock=False):
    """Guard is independent of client-selected companies and remains active in sudo."""
    user = env.user
    if user._tp_is_main_admin() or not user.active or user.share:
        return False
    if lock:
        user._tp_admin_lock()
    env.cr.execute("SELECT 1 FROM tp_admin_delegation WHERE user_id=%s AND state='active' LIMIT 1", [env.uid])
    return bool(env.cr.fetchone())


def deny_authority(env):
    if delegate_actor(env, lock=True):
        raise AccessError(env._('Quản trị được ủy quyền không được thay đổi danh tính, vai trò hoặc quyền bảo mật.'))


def lock_scope_users(env, users):
    """Main-admin work moves serialize with a delegated request for the subject."""
    for user in users.sudo().sorted('id'):
        user._tp_admin_lock(exclusive=True)


def lock_live_delegates(env):
    # Department ownership is shared by every responsibility source.
    env.cr.execute("SELECT DISTINCT user_id FROM tp_admin_delegation WHERE state='active' ORDER BY user_id")
    lock_scope_users(env, env['res.users'].browse([row[0] for row in env.cr.fetchall()]))


class ProtectedUser(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        if delegate_actor(self.env, lock=True) and self.env.context.get('_tp_delegated_account') is not _ACCOUNT:
            raise AccessError(self.env._('Tạo tài khoản qua hồ sơ nhân viên ngoài phòng đã kiểm quyền.'))
        return super().create(vals_list)

    def write(self, vals):
        authority = set(vals) & _USER_AUTHORITY or any(key.startswith(('in_group_', 'sel_groups_')) for key in vals)
        if self == self.env.user and set(vals) <= {'password', 'new_password', 'totp_secret'}:
            return super().write(vals)
        if authority:
            if delegate_actor(self.env, lock=True) and self.env.context.get('_tp_delegated_account') is not _ACCOUNT:
                raise AccessError(self.env._('Không đổi quyền, danh tính hoặc thông tin đăng nhập qua ghi tài khoản.'))
            if not delegate_actor(self.env):
                lock_scope_users(self.env, self)
        return super().write(vals)

    def unlink(self):
        deny_authority(self.env)
        return super().unlink()

    def _change_password(self, new_passwd):
        if (self != self.env.user and delegate_actor(self.env, lock=True)
                and self.env.context.get('_tp_delegated_account') is not _ACCOUNT):
            raise AccessError(self.env._('Đặt lại mật khẩu qua thao tác tài khoản nhân viên ngoài phòng.'))
        return super()._change_password(new_passwd)

    def action_reset_password(self):
        if self != self.env.user:
            deny_authority(self.env)
        return super().action_reset_password()

    def get_reset_password_link(self):
        deny_authority(self.env)
        return super().get_reset_password_link()


class ProtectedEmployee(models.Model):
    _inherit = 'hr.employee'

    def _tp_delegate_identity_guard(self, vals):
        if not delegate_actor(self.env, lock=True):
            if set(vals) & _EMPLOYEE_AUTHORITY:
                lock_scope_users(self.env, self.sudo().user_id)
            return
        trusted_account = self.env.context.get('_tp_delegated_account') is _ACCOUNT
        profile_archive = self.env.context.get('_tp_delegated_profile') is _PROFILE and set(vals) == {'active'}
        contact = self.env['res.partner'].sudo().browse(vals.get('work_contact_id')).exists()
        profile_contact = (self.env.context.get('_tp_delegated_profile_create') is _PROFILE_CREATE
                           and set(vals) == {'work_contact_id'} and contact and not contact.user_ids
                           and not contact.employee_ids and contact.create_uid.id == self.env.uid
                           and all(not employee.user_id and not employee.work_contact_id
                                   and employee.create_uid.id == self.env.uid
                                   and employee.company_id == contact.company_id for employee in self.sudo()))
        if set(vals) & _EMPLOYEE_AUTHORITY and not trusted_account and not profile_archive and not profile_contact:
            raise AccessError(self.env._('Chức vụ, phòng ban, vai trò và liên kết danh tính chỉ do Quản trị chính thay đổi.'))
        own = self.sudo().filtered(lambda employee: employee.user_id.id == self.env.uid)
        if own and set(vals) - _SELF_FIELDS:
            raise AccessError(self.env._('Hồ sơ của mình chỉ được sửa thông tin cá nhân trong danh sách cho phép.'))
        other = self.sudo() - own
        if other:
            caller = self.sudo(False)
            for key in vals:
                field = caller._fields.get(key)
                if field and not caller._has_field_access(field, 'write'):
                    raise AccessError(self.env._('Không có quyền ghi trường nhân sự bị giới hạn.'))
        if set(vals) & _JOB_METADATA and self.env.context.get('_tp_delegated_profile') is not _PROFILE:
            # A job label does not grant a business role. Preserve existing HR
            # write permission, including callers which entered through sudo.
            self.sudo(False).check_access('write')

    @api.model_create_multi
    def create(self, vals_list):
        if delegate_actor(self.env, lock=True):
            caller = self.sudo(False)
            for key, field in caller._fields.items():
                if f'default_{key}' in self.env.context and not caller._has_field_access(field, 'write'):
                    raise AccessError(self.env._('Không có quyền ghi trường nhân sự bị giới hạn.'))
            identity = {'user_id', 'resource_id', 'version_id', 'current_version_id', 'version_ids',
                        'work_contact_id', 'tp_source_code', 'tp_source_snapshot', 'tp_import_batch_id'}
            defaults = self.default_get([name for name in identity | {'company_id', 'department_id'} if name in self._fields])
            for vals in vals_list:
                for key in vals:
                    field = caller._fields.get(key)
                    if field and not caller._has_field_access(field, 'write'):
                        raise AccessError(self.env._('Không có quyền ghi trường nhân sự bị giới hạn.'))
                effective = defaults | vals
                if any(effective.get(name) for name in identity):
                    raise AccessError(self.env._('Không tạo hoặc sao chép danh tính/phiên bản qua dữ liệu lồng.'))
                company = self.env['res.company'].browse(effective.get('company_id') or self.env.company.id)
                department = self.env['hr.department'].browse(effective.get('department_id'))
                if not self.env.user._tp_delegated_other_department(company, department, lock=True):
                    # A delegate keeps an existing legitimate HR create permission.
                    if not self.sudo(False).has_access('create'):
                        raise AccessError(self.env._('Chưa xác định được phòng khác trong phạm vi tạo hồ sơ.'))
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) & _EMPLOYEE_AUTHORITY and not delegate_actor(self.env):
            self.env.cr.execute('SELECT id FROM hr_employee WHERE id IN %s ORDER BY id FOR UPDATE', [tuple(self.ids) or (0,)])
        self._tp_delegate_identity_guard(vals)
        return super().write(vals)

    def unlink(self):
        if delegate_actor(self.env, lock=True) and any(employee.user_id for employee in self.sudo()):
            raise AccessError(self.env._('Quản trị được ủy quyền không xóa danh tính đã có tài khoản.'))
        return super().unlink()


class ProtectedVersion(models.Model):
    _inherit = 'hr.version'

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(['employee_id'])
        if not delegate_actor(self.env):
            ids = sorted({(defaults | vals)['employee_id'] for vals in vals_list if (defaults | vals).get('employee_id')})
            if ids:
                self.env.cr.execute('SELECT id FROM hr_employee WHERE id IN %s ORDER BY id FOR UPDATE', [tuple(ids)])
        if delegate_actor(self.env, lock=True):
            for vals in vals_list:
                employee = self.env['hr.employee'].sudo().browse((defaults | vals).get('employee_id')).exists()
                if employee and employee.user_id:
                    raise AccessError(self.env._('Không tạo phiên bản/clone để đổi quyền hoặc danh tính đã có tài khoản.'))
        return super().create(vals_list)

    def write(self, vals):
        if delegate_actor(self.env, lock=True):
            profile_binding = False
            if self.env.context.get('_tp_delegated_profile_create') is _PROFILE_CREATE:
                target = self.env['hr.employee'].sudo().browse(vals.get('employee_id')).exists()
                profile_binding = bool(target and not target.user_id and target.create_uid.id == self.env.uid
                                       and all(not version.employee_id or version.employee_id == target for version in self)
                                       and all(version.create_uid.id == self.env.uid for version in self)
                                       and not (set(vals) & _VERSION_AUTHORITY - {
                                           'employee_id', 'department_id', 'company_id', 'date_version',
                                           'active', 'hr_responsible_id', 'contract_template_id'}))
                if profile_binding and (('active' in vals and vals['active'] is not True)
                                        or vals.get('contract_template_id')):
                    profile_binding = False
                if profile_binding and vals.get('company_id') and vals['company_id'] != target.company_id.id:
                    profile_binding = False
                if profile_binding and vals.get('department_id'):
                    profile_binding = self.env.user._tp_delegated_other_department(
                        target.company_id, self.env['hr.department'].browse(vals['department_id']), lock=True)
            if set(vals) & _VERSION_AUTHORITY and not profile_binding:
                raise AccessError(self.env._('Không đổi phạm vi hoặc kích hoạt phiên bản hồ sơ qua ủy quyền.'))
            if any(version.employee_id.user_id.id == self.env.uid for version in self.sudo()) and set(vals) - _SELF_FIELDS:
                raise AccessError(self.env._('Không sửa thẩm quyền hoặc thông tin quản lý của phiên bản hồ sơ chính mình.'))
            if set(vals) & _JOB_METADATA and self.env.context.get('_tp_delegated_profile') is not _PROFILE:
                self.sudo(False).check_access('write')
        elif set(vals) & _VERSION_AUTHORITY:
            lock_scope_users(self.env, self.sudo().employee_id.user_id)
        return super().write(vals)

    def unlink(self):
        deny_authority(self.env)
        return super().unlink()


class ProtectedResource(models.Model):
    _inherit = 'resource.resource'

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(['user_id'])
        if delegate_actor(self.env, lock=True) and any((defaults | vals).get('user_id') for vals in vals_list):
            raise AccessError(self.env._('Không tạo tài nguyên thay thế để liên kết tài khoản.'))
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) & {'user_id', 'company_id', 'active'}:
            profile_archive = self.env.context.get('_tp_delegated_profile') is _PROFILE and set(vals) == {'active'}
            profile_create = (self.env.context.get('_tp_delegated_profile_create') is _PROFILE_CREATE
                              and all(not resource.user_id and resource.create_uid.id == self.env.uid
                                      and (not vals.get('company_id') or vals['company_id'] == resource.company_id.id)
                                      for resource in self)
                              and not vals.get('user_id') and ('active' not in vals or vals['active'] is True))
            if (delegate_actor(self.env, lock=True)
                    and self.env.context.get('_tp_delegated_account') is not _ACCOUNT
                    and not profile_archive and not profile_create):
                raise AccessError(self.env._('Không đổi tài nguyên danh tính hoặc công ty qua ủy quyền.'))
            if not delegate_actor(self.env):
                lock_scope_users(self.env, self.sudo().user_id)
        return super().write(vals)

    def unlink(self):
        deny_authority(self.env)
        return super().unlink()


class ProtectedDepartment(models.Model):
    _inherit = 'hr.department'

    @api.model_create_multi
    def create(self, vals_list):
        if any(set(vals) & {'manager_id', 'parent_id', 'member_ids'} for vals in vals_list):
            deny_authority(self.env)
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) & {'manager_id', 'parent_id', 'company_id', 'active', 'member_ids'}:
            deny_authority(self.env)
        if set(vals) & {'company_id', 'active'}:
            lock_live_delegates(self.env)
        return super().write(vals)

    def unlink(self):
        deny_authority(self.env)
        lock_live_delegates(self.env)
        return super().unlink()


class ProtectedGroups(models.Model):
    _inherit = 'res.groups'

    @api.model_create_multi
    def create(self, vals_list):
        deny_authority(self.env)
        return super().create(vals_list)

    def write(self, vals):
        deny_authority(self.env)
        return super().write(vals)

    def unlink(self):
        deny_authority(self.env)
        return super().unlink()


class AuthorityGuard(models.AbstractModel):
    _name = 'tp.admin.authority.guard'
    _description = 'Concrete authority mutation boundary'

    @api.model_create_multi
    def create(self, vals_list):
        deny_authority(self.env)
        if 'user_id' in self._fields:
            defaults = self.default_get(['user_id'])
            lock_scope_users(self.env, self.env['res.users'].browse([
                (defaults | vals)['user_id'] for vals in vals_list if (defaults | vals).get('user_id')]))
        return super().create(vals_list)

    def write(self, vals):
        deny_authority(self.env)
        if 'user_id' in self._fields:
            lock_scope_users(self.env, self.sudo().user_id | self.env['res.users'].browse(vals.get('user_id')))
        return super().write(vals)

    def unlink(self):
        deny_authority(self.env)
        if 'user_id' in self._fields:
            lock_scope_users(self.env, self.sudo().user_id)
        return super().unlink()


class ProtectedAssignment(models.Model):
    _name = 'tp.project.assignment'
    _inherit = ['tp.project.assignment', 'tp.admin.authority.guard']


class ProtectedProjectGrant(models.Model):
    _name = 'tp.project.grant'
    _inherit = ['tp.project.grant', 'tp.admin.authority.guard']


class ProtectedKdGrant(models.Model):
    _name = 'tp.kd.grant'
    _inherit = ['tp.kd.grant', 'tp.admin.authority.guard']


class ProtectedDepartmentRole(models.Model):
    _name = 'tp.kd.department.role'
    _inherit = ['tp.kd.department.role', 'tp.admin.authority.guard']


class ProtectedTeamMember(models.Model):
    _name = 'crm.team.member'
    _inherit = ['crm.team.member', 'tp.admin.authority.guard']


class ProtectedTeam(models.Model):
    _inherit = 'crm.team'

    @api.model_create_multi
    def create(self, vals_list):
        deny_authority(self.env)
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) & {'kd_department_id', 'company_id', 'active', 'user_id',
                        'member_ids', 'crm_team_member_ids', 'crm_team_member_all_ids'}:
            deny_authority(self.env)
            members = self.env['crm.team.member'].sudo().with_context(active_test=False).search([
                ('crm_team_id', 'in', self.ids),
            ])
            lock_scope_users(self.env, members.user_id | self.sudo().user_id
                             | self.env['res.users'].browse(vals.get('user_id')))
        return super().write(vals)

    def unlink(self):
        deny_authority(self.env)
        members = self.env['crm.team.member'].sudo().with_context(active_test=False).search([
            ('crm_team_id', 'in', self.ids),
        ])
        lock_scope_users(self.env, members.user_id | self.sudo().user_id)
        return super().unlink()


class ProtectedReportingAssignment(models.Model):
    _name = 'tp.report.assignment'
    _inherit = ['tp.report.assignment', 'tp.admin.authority.guard']


class ProtectedAccess(models.Model):
    _name = 'ir.access'
    _inherit = ['ir.access', 'tp.admin.authority.guard']


class ProtectedServerAction(models.Model):
    _name = 'ir.actions.server'
    _inherit = ['ir.actions.server', 'tp.admin.authority.guard']


class ProtectedConfig(models.Model):
    _name = 'ir.config_parameter'
    _inherit = ['ir.config_parameter', 'tp.admin.authority.guard']


class ProtectedPartner(models.Model):
    _inherit = 'res.partner'

    def write(self, vals):
        if delegate_actor(self.env, lock=True):
            signup_cancel = (self.env.context.get('_tp_delegated_account') is _ACCOUNT
                             and set(vals) == {'signup_type'} and vals['signup_type'] in (None, False))
            if not signup_cancel and set(vals) & {'user_ids', 'employee_ids', 'signup_type', 'signup_token', 'signup_expiration'}:
                raise AccessError(self.env._('Không đổi liên kết danh tính hoặc token đăng nhập qua liên hệ.'))
            for target in self.sudo().user_ids:
                if target.id != self.env.uid:
                    target._tp_assert_delegated_account_target()
        return super().write(vals)


class ProtectedImport(models.Model):
    _inherit = 'tp.hr.import.batch'

    def _manager(self):
        deny_authority(self.env)
        return super()._manager()
