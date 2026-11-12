"""Explicit HR lock using native inactive users, password checks and session tokens."""
from odoo import fields, models
from odoo.exceptions import AccessDenied, AccessError, UserError

LOCKED_MESSAGE = 'Tài khoản đã bị khóa. Vui lòng gửi phản hồi.'


class ResUsers(models.Model):
    _inherit = 'res.users'

    tp_hr_locked = fields.Boolean(copy=False, readonly=True, groups='base.group_system')
    tp_lock_revision = fields.Integer(default=0, copy=False, readonly=True, groups='base.group_system')

    def _tp_set_account_lock(self, locked, reason):
        self.ensure_one()
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(self.env._('Chỉ Quản trị viên hệ thống được khóa hoặc mở tài khoản.'))
        self.check_access('write')
        if not isinstance(locked, bool) or not isinstance(reason, str) or not reason.strip():
            raise UserError(self.env._('Vui lòng nhập lý do khóa hoặc mở tài khoản.'))
        protected = {self.env.uid}
        for xmlid in ('base.user_root', 'base.user_admin', 'base.public_user', 'base.template_portal_user', 'base.default_user'):
            record = self.env.ref(xmlid, raise_if_not_found=False)
            if record:
                protected.add(record.id)
        if self.id in protected or self.share:
            raise UserError(self.env._('Không được khóa/mở chính mình hoặc tài khoản hệ thống được bảo vệ.'))
        # Lock is global to the user: an operator must control every company affected.
        if set(self.company_ids.ids) - set(self.env.companies.ids):
            raise AccessError(self.env._('Tài khoản có công ty ngoài phạm vi đang quản lý.'))
        self.env.cr.execute('SELECT id FROM res_users WHERE id=%s FOR UPDATE', [self.id])
        self.invalidate_recordset(['active', 'tp_hr_locked', 'tp_lock_revision'])
        if (locked and not self.active) or (not locked and self.active and not self.tp_hr_locked):
            raise UserError(self.env._('Tình trạng tài khoản đã thay đổi. Vui lòng tải lại hồ sơ.'))
        self.write({'active': not locked, 'tp_hr_locked': locked, 'tp_lock_revision': self.tp_lock_revision + 1})

    def _get_session_token_fields(self):
        # A lock/unlock cycle must not revive a session issued before the lock.
        return super()._get_session_token_fields() | {'tp_lock_revision'}

    def _check_credentials(self, credential, env):
        result = super()._check_credentials(credential, env)
        if self.sudo().tp_hr_locked:
            raise AccessDenied(LOCKED_MESSAGE)
        return result

    def _login(self, credential, user_agent_env):
        # Native login ignores inactive users. Check only explicitly HR-locked
        # identities here, inside native rate limiting; never activate them.
        candidate = self.sudo().with_context(active_test=False).search([
            ('login', '=', credential.get('login')), ('active', '=', False), ('tp_hr_locked', '=', True),
        ], limit=1)
        if candidate:
            with self._assert_can_auth(user=credential.get('login')):
                candidate.with_user(candidate).sudo()._check_credentials(credential, user_agent_env)
            raise AccessDenied()
        return super()._login(credential, user_agent_env)
