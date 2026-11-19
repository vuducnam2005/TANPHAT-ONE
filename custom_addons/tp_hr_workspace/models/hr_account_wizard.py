"""Dedicated employee identities; administrators never transfer existing users."""
import time

from psycopg2.errors import UniqueViolation

from odoo import SUPERUSER_ID, Command, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from odoo.addons.base.models.res_users import check_identity

_PERSONAL_ACCOUNT = object()


def validate_employee_login(env, raw_login, current_login=None):
    """Validate and normalize an employee login according to TANPHAT ONE login rules."""
    if not isinstance(raw_login, str) or not raw_login or not raw_login.strip():
        raise ValidationError(env._('Vui lòng nhập tên đăng nhập.'))
    login = raw_login.strip()
    if not login or len(login) > 254 or any(c.isspace() for c in login):
        raise ValidationError(env._('Nhập tên đăng nhập không chứa khoảng trắng, tối đa 254 ký tự.'))
    if not login.isprintable():
        raise ValidationError(env._('Tên đăng nhập không được chứa ký tự điều khiển hoặc ký tự ẩn.'))
    if current_login is not None and login == (current_login or ''):
        raise ValidationError(env._('Tên đăng nhập mới phải khác tên đăng nhập hiện tại.'))
    return login


def assert_unique_user_login(env, login, exclude_user_id=0):
    """Match native case-sensitive authentication, including inactive users and other companies."""
    env.cr.execute(
        'SELECT id FROM res_users WHERE login = %s AND id != %s LIMIT 1',
        [login, int(exclude_user_id or 0)],
    )
    if env.cr.fetchone():
        raise ValidationError(env._('Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác.'))


def record_employee_login_audit(env, employee, user, old_login, new_login):
    """Record immutable audit log and employee chatter history for a login rename (no secrets/tokens)."""
    tz_name = env.context.get('tz') or env.user.tz or 'Asia/Ho_Chi_Minh'
    now_utc = fields.Datetime.now()
    local_stamp = fields.Datetime.context_timestamp(employee.with_context(tz=tz_name), now_utc).strftime('%d/%m/%Y %H:%M:%S')
    env['tp.hr.employee.audit']._tp_record([{
        'action': 'login_change',
        'employee_ref': employee.id,
        'employee_name': employee.name,
        'employee_code': employee.tp_employee_code,
        'company_id': employee.company_id.id,
        'reason': env._('Đổi tên đăng nhập tài khoản #%(uid)s: %(old)s → %(new)s', uid=user.id, old=old_login, new=new_login),
        'account_action': 'kept',
        'account_ref': user.id,
        'account_login': new_login,
        'snapshot': {
            'user_id': user.id,
            'old_login': old_login,
            'new_login': new_login,
            'actor_id': env.user.id,
            'actor_name': env.user.name,
            'changed_at': fields.Datetime.to_string(now_utc),
        },
    }])
    employee.message_post(
        body=env._(
            'Đã đổi tên đăng nhập tài khoản (ID #%(uid)s): %(old)s → %(new)s. '
            'Người thực hiện: %(actor)s. Thời gian: %(stamp)s.',
            uid=user.id,
            old=old_login,
            new=new_login,
            actor=env.user.name,
            stamp=local_stamp,
        ),
    )


class TpHrAccountWizard(models.TransientModel):
    _name = 'tp.hr.account.wizard'
    _description = 'Tài khoản cá nhân của nhân viên'

    employee_id = fields.Many2one('hr.employee', required=True, readonly=True, string='Nhân viên')
    company_id = fields.Many2one(related='employee_id.company_id')
    employee_name = fields.Char(related='employee_id.name')
    tp_employee_code = fields.Char(related='employee_id.tp_employee_code')
    department_id = fields.Many2one(related='employee_id.department_id')
    job_id = fields.Many2one(related='employee_id.job_id')
    current_user_id = fields.Many2one(related='employee_id.user_id')
    expected_user_id = fields.Many2one('res.users', readonly=True)
    expected_login = fields.Char(readonly=True)
    can_change_login = fields.Boolean(related='employee_id.tp_can_change_login')
    current_login = fields.Char(related='employee_id.tp_user_login', string='Tên đăng nhập')
    account_status = fields.Selection(related='employee_id.tp_account_status', string='Tình trạng')
    is_linked = fields.Boolean(compute='_compute_info')
    is_admin = fields.Boolean(compute='_compute_info')
    reason = fields.Char(string='Lý do thao tác')
    new_user_login = fields.Char(string='Tên đăng nhập mới')

    @api.depends('employee_id.user_id')
    @api.depends_context('uid')
    def _compute_info(self):
        for rec in self:
            rec.is_linked = bool(rec.employee_id.user_id)
            rec.is_admin = self.env.user.has_group('base.group_system')

    def _employee(self, existing=False, login_rename=False):
        self.ensure_one()
        employee = self.employee_id
        employee._tp_account_admin(existing=existing, login_rename=login_rename)
        self.env.cr.execute('SELECT id FROM hr_employee WHERE id=%s FOR UPDATE', [employee.id])
        self.env.cr.execute('SELECT id FROM resource_resource WHERE id=%s FOR UPDATE', [employee.resource_id.id])
        employee.resource_id.invalidate_recordset(['user_id'])
        employee.invalidate_recordset(['user_id'])
        if employee.user_id != self.expected_user_id:
            raise UserError(self.env._('Tài khoản đã thay đổi. Vui lòng mở lại hộp thoại.'))
        employee._tp_account_admin(existing=existing, login_rename=login_rename)
        return employee

    @api.model
    def _tp_account_lang(self):
        # HR-CORRECTION-008: personal accounts start in Vietnamese, not the en_US default.
        installed = dict(self.env['res.lang'].get_installed())
        return 'vi_VN' if 'vi_VN' in installed else self.env.lang

    def action_link(self):
        raise AccessError(self.env._('Không còn hỗ trợ liên kết tài khoản có sẵn. Hãy tạo tài khoản riêng.'))

    def action_unlink(self):
        raise AccessError(self.env._('Không được gỡ hoặc chuyển tài khoản cá nhân. Hãy khóa tài khoản khi cần.'))

    def action_reset_password(self):
        return self.action_prepare_credentials(reset=True)

    def action_open_change_login(self):
        employee = self._employee(existing=True, login_rename=True)
        self.expected_login = employee.user_id.login
        return {
            'type': 'ir.actions.client',
            'tag': 'tp_hr_workspace.change_login',
            'params': {
                'wizardId': self.id,
                'employeeId': employee.id,
                'employeeName': employee.name,
                'employeeCode': employee.tp_employee_code or '',
                'department': employee.department_id.name or 'Chưa khai báo phòng ban',
                'currentLogin': employee.user_id.login or '',
            },
        }

    def action_change_login(self, login=None):
        self.ensure_one()
        employee = self._employee(existing=True, login_rename=True)
        raw_login = login if login is not None else self.new_user_login
        return employee._tp_change_user_login(raw_login, expected_login=self.expected_login)

    def action_prepare_credentials(self, reset=False):
        if not isinstance(reset, bool):
            raise ValidationError(self.env._('Thao tác tài khoản không hợp lệ.'))
        employee = self._employee(existing=reset)
        if employee.user_id and not reset:
            raise UserError(self.env._('Nhân viên đã có tài khoản riêng.'))
        if not request:
            raise UserError(self.env._('Vui lòng thao tác trong phiên đăng nhập trên trình duyệt.'))
        action = self._prepare_credentials_checked(reset)
        if action.get('res_model') == 'res.users.identitycheck':
            action['name'] = self.env._('Xác nhận danh tính quản trị viên')
        return action

    @check_identity
    def _prepare_credentials_checked(self, reset):
        employee = self._employee(existing=reset)
        if employee.user_id and not reset:
            raise UserError(self.env._('Nhân viên đã có tài khoản riêng.'))
        return {
            'type': 'ir.actions.client', 'tag': 'tp_hr_workspace.credentials',
            'params': {'wizardId': self.id, 'reset': reset, 'employeeName': employee.name,
                       'employeeCode': employee.tp_employee_code or '',
                       'department': employee.department_id.name or 'Chưa khai báo phòng ban',
                       'login': employee.user_id.login if reset else '',
                       'minLength': self.env['ir.config_parameter'].sudo().get_int('auth_password_policy.minlength')},
        }

    def _require_recent_identity(self):
        if not request or request.session.get('identity-check-last', 0) <= time.time() - 600:
            raise UserError(self.env._('Phiên xác thực quản trị viên đã hết hạn. Hãy đóng cửa sổ và mở lại để xác thực. Thông tin chưa được lưu.'))

    def _validate_password(self, password, confirmation):
        if not isinstance(password, str) or not password or not password.strip():
            raise ValidationError(self.env._('Vui lòng nhập mật khẩu mới.'))
        if password != confirmation:
            raise ValidationError(self.env._('Hai mật khẩu chưa giống nhau. Vui lòng nhập lại.'))
        if password != password.strip():
            raise ValidationError(self.env._('Mật khẩu không được bắt đầu hoặc kết thúc bằng khoảng trắng.'))
        minimum = self.env['ir.config_parameter'].sudo().get_int('auth_password_policy.minlength')
        if len(password) < minimum:
            raise ValidationError(self.env._('Mật khẩu cần có ít nhất %s ký tự.', minimum))

    def action_set_password(self, password, confirmation):
        employee = self._employee(existing=True)
        self._require_recent_identity()
        self._validate_password(password, confirmation)
        with self.env.cr.savepoint():
            employee.user_id._change_password(password)
            employee.message_post(body=self.env._('Đã đặt lại mật khẩu tài khoản %(login)s. Người thực hiện: %(actor)s.',
                                                 login=employee.user_id.login, actor=self.env.user.name))
        return True

    def _change_account_lock(self, locked):
        employee = self._employee(existing=True)
        employee.user_id._tp_set_account_lock(locked, self.reason)
        employee.message_post(body=self.env._(
            '%(action)s tài khoản %(login)s. Lý do: %(reason)s',
            action='Khóa' if locked else 'Mở', login=employee.user_id.login, reason=self.reason.strip(),
        ))
        return {'type': 'ir.actions.act_window_close'}

    def action_lock(self):
        return self._change_account_lock(True)

    def action_unlock(self):
        return self._change_account_lock(False)

    def action_create_user(self, login=None, password=None, confirmation=None):
        employee = self._employee()
        self._require_recent_identity()
        if employee.user_id:
            raise UserError(self.env._('Nhân viên đã có tài khoản riêng.'))
        login = validate_employee_login(self.env, login if login is not None else self.new_user_login)
        self._validate_password(password, confirmation)
        assert_unique_user_login(self.env, login)
        try:
            with self.env.cr.savepoint():
                user = self.env['res.users'].sudo().with_context(
                    no_reset_password=True,
                    _tp_personal_account=_PERSONAL_ACCOUNT,
                ).create({
                    'name': employee.name, 'login': login, 'password': password,
                    'lang': self._tp_account_lang(),
                    'company_id': employee.company_id.id,
                    'company_ids': [Command.set(employee.company_id.ids)],
                    'group_ids': [Command.set([self.env.ref('base.group_user').id])],
                })
                employee.with_context(_tp_personal_account=_PERSONAL_ACCOUNT).write({'user_id': user.id})
                employee._tp_sync_identity({'name', 'image_1920'})
                if employee._tp_role_supported():
                    user.write({'group_ids': [Command.link(self.env.ref('tp_kd_workspace.group_scoped_staff').id)]})
                employee.message_post(body=self.env._('Đã tạo tài khoản cá nhân %(login)s. Người thực hiện: %(actor)s.',
                                                     login=user.login, actor=self.env.user.name))
        except UniqueViolation as error:
            if error.diag.constraint_name == 'res_users_login_key':
                raise ValidationError(self.env._('Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác.')) from error
            raise
        return True


class PersonalEmployee(models.Model):
    _inherit = 'hr.employee'

    tp_can_change_login = fields.Boolean(compute='_compute_tp_can_change_login', groups='hr.group_hr_user,base.group_system')

    @api.depends('user_id', 'company_id')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_tp_can_change_login(self):
        for employee in self:
            try:
                employee.with_env(self.env(su=False))._tp_account_admin(existing=True, login_rename=True)
                employee.tp_can_change_login = True
            except (AccessError, UserError):
                employee.tp_can_change_login = False

    @api.onchange('work_email')
    def _onchange_work_email_link_user(self):
        # Native email matching would silently propose another existing identity.
        return None

    def action_send_invitation(self):
        raise AccessError(self.env._('Dùng Tạo tài khoản riêng trong Tài khoản & phân quyền.'))

    def action_reset_password(self):
        return self.action_reset_user_password()

    def action_copy_invitation_link(self):
        raise AccessError(self.env._('Dùng Đặt lại mật khẩu qua cửa sổ bảo mật của Odoo.'))

    def action_toggle_user_active(self):
        raise AccessError(self.env._('Khóa/mở tài khoản cần lý do trong hộp quản lý tài khoản.'))

    def action_deactivate_user_and_depart(self):
        raise AccessError(self.env._('Khóa tài khoản và kết thúc hồ sơ là hai thao tác riêng.'))

    def action_open_change_login_dialog(self):
        self._tp_account_admin(existing=True, login_rename=True)
        wizard = self.env['tp.hr.account.wizard'].create({
            'employee_id': self.id,
            'current_user_id': self.user_id.id,
            'expected_user_id': self.user_id.id,
        })
        return wizard.action_open_change_login()

    def action_change_user_login(self, new_login):
        return self._tp_change_user_login(new_login)

    def _tp_change_user_login(self, new_login, expected_login=None):
        self.ensure_one()
        self._tp_account_admin(existing=True, login_rename=True)
        self.env.cr.execute('SELECT id FROM hr_employee WHERE id=%s FOR UPDATE', [self.id])
        self.env.cr.execute('SELECT id FROM resource_resource WHERE id=%s FOR UPDATE', [self.resource_id.id])
        self.resource_id.invalidate_recordset(['user_id'])
        self.invalidate_recordset(['user_id', 'tp_user_login'])
        self._tp_account_admin(existing=True, login_rename=True)
        user = self.user_id.with_context(active_test=False)
        if not user:
            raise UserError(self.env._('Chưa có tài khoản.'))
        self.env.cr.execute('SELECT id FROM res_users WHERE id=%s FOR UPDATE', [user.id])
        user.invalidate_recordset(['login'])
        old_login = user.login or ''
        if expected_login is not None and expected_login != old_login:
            raise UserError(self.env._('Tên đăng nhập đã thay đổi. Vui lòng mở lại hộp thoại.'))
        cleaned = validate_employee_login(self.env, new_login, current_login=old_login)
        user.write({'login': cleaned})
        return {'ok': True, 'user_id': user.id, 'old_login': old_login, 'new_login': cleaned}

    def _tp_account_admin(self, existing=False, login_rename=False):
        self.ensure_one()
        actor_env = self.env(su=False)
        if not actor_env.user.has_group('base.group_system'):
            raise AccessError(self.env._('Chỉ Quản trị viên hệ thống được quản lý tài khoản và vai trò.'))
        self.with_env(actor_env).check_access('write')
        if self.company_id != self.env.company:
            raise AccessError(self.env._('Hồ sơ ngoài công ty đang quản lý.'))
        if existing:
            user = self.user_id
            if not user:
                raise UserError(self.env._('Chưa có tài khoản.'))
            orig_xmlids = ('base.user_root', 'base.user_admin')
            orig_ids = {
                rec.id for xmlid in orig_xmlids
                if (rec := self.env.ref(xmlid, raise_if_not_found=False))
            }
            is_orig_target = user.id in orig_ids or (
                hasattr(user, '_tp_is_original_admin') and user._tp_is_original_admin()
            )
            if is_orig_target and hasattr(self.env.user, '_tp_is_original_admin') and not self.env.user._tp_is_original_admin():
                raise AccessError(self.env._('Tài khoản Quản trị gốc được bảo vệ; chỉ Quản trị gốc được thay đổi.'))
            protected = {self.env.uid} | orig_ids
            for xmlid in ('base.public_user', 'base.template_portal_user', 'base.default_user'):
                record = self.env.ref(xmlid, raise_if_not_found=False)
                if record:
                    protected.add(record.id)
            original_manage = (hasattr(actor_env.user, '_tp_is_original_admin')
                               and actor_env.user._tp_is_original_admin())
            if hasattr(user, '_tp_can_manage_account_target') and not user._tp_can_manage_account_target():
                raise AccessError(self.env._('Chỉ admin gốc được thay đổi tài khoản hoặc hồ sơ của admin ủy quyền khác.'))
            if user.id in protected or user.share or (user.has_group('base.group_system') and not original_manage):
                raise UserError(self.env._('Tài khoản quản trị/hệ thống hoặc chính mình được bảo vệ.'))
            if set(user.company_ids.ids) - set(self.env.companies.ids):
                raise AccessError(self.env._('Tài khoản có công ty ngoài phạm vi quản lý.'))
        return self

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            for vals in vals_list:
                if 'tp_user_login' in vals:
                    raise AccessError(self.env._('Tên đăng nhập là trường đồng bộ từ tài khoản; không ghi trực tiếp trên hồ sơ nhân viên.'))
                resource = self.env['resource.resource'].sudo().browse(vals.get('resource_id')).exists()
                if vals.get('user_id') or resource.user_id:
                    raise AccessError(self.env._('Tạo hồ sơ trước, sau đó dùng Tạo tài khoản riêng.'))
        return super().create(vals_list)

    def write(self, vals):
        internal = self.env.context.get('_tp_personal_account') is _PERSONAL_ACCOUNT
        if not self.env.su and not internal:
            if 'tp_user_login' in vals:
                raise AccessError(self.env._('Tên đăng nhập là trường đồng bộ từ tài khoản; hãy dùng Đổi tên đăng nhập trong phần Tài khoản.'))
            if 'user_id' in vals and any(e.user_id.id != (vals['user_id'] or False) for e in self):
                raise AccessError(self.env._('Không được gán, gỡ hoặc chuyển tài khoản cá nhân qua thao tác ghi.'))
            if 'resource_id' in vals and any(e.resource_id.id != vals['resource_id'] for e in self):
                raise AccessError(self.env._('Không được thay tài nguyên danh tính của nhân viên.'))
            if 'company_id' in vals and any(e.user_id and e.company_id.id != vals['company_id'] for e in self):
                raise UserError(self.env._('Đổi công ty của danh tính đã cấp cần quy trình migration có kiểm chứng.'))
        return super().write(vals)


class PersonalResource(models.Model):
    _inherit = 'resource.resource'

    def write(self, vals):
        if not self.env.su and self.env.context.get('_tp_personal_account') is not _PERSONAL_ACCOUNT:
            employees = self.env['hr.employee'].sudo().with_context(active_test=False).search([('resource_id', 'in', self.ids)])
            if employees and ('user_id' in vals or 'company_id' in vals):
                if any(('user_id' in vals and r.user_id.id != (vals['user_id'] or False))
                       or ('company_id' in vals and r.company_id.id != vals['company_id']) for r in self):
                    raise AccessError(self.env._('Không được chuyển danh tính qua tài nguyên nhân viên.'))
        return super().write(vals)


class PersonalAccountUser(models.Model):
    _inherit = 'res.users'

    def write(self, vals):
        if 'login' not in vals or not self or self.env.uid == SUPERUSER_ID:
            return super().write(vals)
        actor_users = self.with_env(self.env(su=False)).with_context(active_test=False)
        if not actor_users.env.user.has_group('base.group_system'):
            raise AccessError(self.env._('Chỉ người có quyền quản lý tài khoản được đổi tên đăng nhập.'))
        self.ensure_one()
        employees = actor_users.env['hr.employee'].sudo().with_context(active_test=False).search([
            ('user_id', '=', self.id),
        ])
        employees = employees.with_env(actor_users.env)
        for employee in employees.sorted('id'):
            employee._tp_account_admin(existing=True, login_rename=True)
            self.env.cr.execute('SELECT id FROM hr_employee WHERE id=%s FOR UPDATE', [employee.id])
            self.env.cr.execute('SELECT id FROM resource_resource WHERE id=%s FOR UPDATE', [employee.resource_id.id])
            employee.resource_id.invalidate_recordset(['user_id'])
            employee.invalidate_recordset(['user_id'])
            employee._tp_account_admin(existing=True, login_rename=True)
            if employee.user_id.id != self.id:
                raise UserError(self.env._('Tài khoản đã thay đổi. Vui lòng mở lại hộp thoại.'))
        self.env.cr.execute('SELECT id FROM res_users WHERE id=%s FOR UPDATE', [self.id])
        self.invalidate_recordset(['login'])
        old_login = self.login
        cleaned = validate_employee_login(self.env, vals['login'])
        if cleaned == old_login:
            return super().write({**vals, 'login': cleaned})
        assert_unique_user_login(self.env, cleaned, exclude_user_id=self.id)
        try:
            with self.env.cr.savepoint():
                result = super().write({**vals, 'login': cleaned})
                self.flush_recordset(['login'])
                for employee in employees:
                    record_employee_login_audit(actor_users.env, employee, actor_users, old_login, cleaned)
        except UniqueViolation as error:
            if error.diag.constraint_name == 'res_users_login_key':
                raise ValidationError(self.env._('Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác.')) from error
            raise
        return result
