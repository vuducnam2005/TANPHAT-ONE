"""Explicit HR lock using native inactive users, password checks and session tokens.

Passkey sign-in stays native (auth_passkey + vendored py_webauthn): this module
only validates the request shape and maps native AccessDenied reasons to safe
Vietnamese messages that never reveal whether an account exists.
"""
import json
import logging

from odoo import fields, models
from odoo.exceptions import AccessDenied, AccessError, UserError
from odoo.tools import SQL

from odoo.addons.auth_passkey._vendor.webauthn.helpers import (
    exceptions as webauthn_errors,
)

_logger = logging.getLogger(__name__)

LOCKED_MESSAGE = 'Tài khoản đã bị khóa. Vui lòng gửi phản hồi.'

PASSKEY_MESSAGES = {
    'unknown': 'Khóa truy cập này không còn hiệu lực trên hệ thống (đã bị thu hồi hoặc được tạo ở địa chỉ khác). Hãy đăng nhập bằng mật khẩu, rồi đăng ký khóa mới trong Tài khoản & Bảo mật.',
    'challenge': 'Phiên xác thực bằng khóa truy cập đã hết hạn hoặc đã được dùng. Hãy bấm lại “Đăng nhập bằng khóa truy cập”.',
    'origin': 'Khóa truy cập không khớp với địa chỉ hệ thống hiện tại. Hãy mở đúng địa chỉ chính thức; nếu khóa được tạo ở địa chỉ cũ, hãy đăng nhập bằng mật khẩu và đăng ký khóa mới.',
    'verification': 'Thiết bị chưa xác minh được bạn (vân tay, khuôn mặt hoặc mã PIN). Hãy thử lại và hoàn tất bước xác minh trên thiết bị.',
    'counter': 'Khóa truy cập bị từ chối vì bộ đếm xác thực bất thường. Hãy đăng nhập bằng mật khẩu, thu hồi khóa này và đăng ký khóa mới.',
    'cooldown': 'Đã có nhiều lần đăng nhập không thành công. Vui lòng chờ ít phút rồi thử lại.',
    'rejected': 'Không đăng nhập được bằng khóa truy cập này. Hãy thử lại hoặc đăng nhập bằng mật khẩu.',
}
# Native (untranslated) py_webauthn / auth_passkey reasons -> safe message key.
_PASSKEY_REASONS = (
    ('Cannot find a challenge for this session', 'challenge'),
    ('Client data challenge was not expected challenge', 'challenge'),
    ('Unexpected client data origin', 'origin'),
    ('Unexpected RP ID hash', 'origin'),
    ('User verification is required', 'verification'),
    ('User was not present', 'verification'),
    ('Response sign count of', 'counter'),
    # Native login cooldown (per source address, never per account), English or Vietnamese.
    ('Too many login failures', 'cooldown'),
    ('Bạn đã đăng nhập thất bại quá nhiều lần', 'cooldown'),
)
# Malformed assertions must end as a rejected login, never as a server error.
PASSKEY_PAYLOAD_ERRORS = (
    ValueError, KeyError, TypeError,
    webauthn_errors.InvalidJSONStructure,
    webauthn_errors.InvalidAuthenticatorDataStructure,
    webauthn_errors.InvalidCBORData,
    webauthn_errors.InvalidBackupFlags,
    webauthn_errors.InvalidPublicKeyStructure,
    webauthn_errors.UnsupportedPublicKeyType,
    webauthn_errors.UnsupportedAlgorithm,
    webauthn_errors.UnsupportedPublicKey,
    webauthn_errors.UnsupportedEC2Curve,
)


def passkey_failure_reason(error):
    """Classify a native passkey failure without exposing its raw text."""
    message = error.args[0] if error.args and isinstance(error.args[0], str) else ''
    for reason, text in PASSKEY_MESSAGES.items():
        if message == text:
            return reason
    for prefix, reason in _PASSKEY_REASONS:
        if message.startswith(prefix):
            return reason
    return 'rejected'


def passkey_credential_id(credential):
    """Credential id of a well-formed WebAuthn assertion, else None."""
    response = credential.get('webauthn_response')
    if not isinstance(response, str) or not response or len(response) > 65536:
        return None
    try:
        payload = json.loads(response)
    except ValueError:
        return None
    credential_id = payload.get('id') if isinstance(payload, dict) else None
    if isinstance(credential_id, str) and 0 < len(credential_id) <= 1024:
        return credential_id
    return None


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
        if credential.get('type') == 'webauthn':
            if not passkey_credential_id(credential):
                raise AccessDenied(PASSKEY_MESSAGES['rejected'])
            try:
                result = super()._check_credentials(credential, env)
            except AccessDenied as error:
                raise AccessDenied(PASSKEY_MESSAGES[passkey_failure_reason(error)]) from None
            except PASSKEY_PAYLOAD_ERRORS:
                raise AccessDenied(PASSKEY_MESSAGES['rejected']) from None
        else:
            result = super()._check_credentials(credential, env)
        if self.sudo().tp_hr_locked:
            raise AccessDenied(LOCKED_MESSAGE)
        return result

    def _tp_passkey_locked_owner(self, owner, credential, user_agent_env):
        """Same order as passwords: prove possession of the key, then disclose the lock.

        A valid assertion raises LOCKED_MESSAGE from _check_credentials; this
        method never returns normally, so a locked owner is never logged in.
        """
        with self._assert_can_auth(user=owner.login):
            owner.with_user(owner).sudo()._check_credentials(credential, user_agent_env)
        raise AccessDenied(PASSKEY_MESSAGES['rejected'])

    def _tp_passkey_login(self, credential, user_agent_env):
        credential_id = passkey_credential_id(credential)
        if not credential_id:
            _logger.info("Passkey login rejected: reason=malformed")
            raise AccessDenied(PASSKEY_MESSAGES['rejected'])
        self.env.cr.execute(SQL(
            "SELECT create_uid FROM auth_passkey_key WHERE credential_identifier = %s", credential_id,
        ))
        row = self.env.cr.fetchone()
        owner = self.sudo().with_context(active_test=False).browse(row[0] if row and row[0] else [])
        try:
            if owner and not owner.active and owner.tp_hr_locked:
                self._tp_passkey_locked_owner(owner, credential, user_agent_env)
            return super()._login(credential, user_agent_env)
        except AccessDenied as error:
            if error.args and error.args[0] == LOCKED_MESSAGE:
                raise
            reason = passkey_failure_reason(error) if owner else 'unknown'
            _logger.info("Passkey login rejected: reason=%s", reason)
            raise AccessDenied(PASSKEY_MESSAGES[reason]) from None

    def _login(self, credential, user_agent_env):
        if credential.get('type') == 'webauthn':
            return self._tp_passkey_login(credential, user_agent_env)
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
