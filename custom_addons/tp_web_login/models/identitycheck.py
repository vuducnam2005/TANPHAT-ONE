import logging

from odoo import models
from odoo.exceptions import AccessDenied, UserError

from .res_users import PASSKEY_PAYLOAD_ERRORS, passkey_failure_reason
from odoo.addons.auth_passkey._vendor.webauthn.helpers.exceptions import (
    InvalidRegistrationResponse,
)

_logger = logging.getLogger(__name__)

PASSKEY_IDENTITY_MESSAGE = (
    'Chưa xác nhận được bằng khóa truy cập. Hãy thử lại với khóa đã đăng ký cho tài khoản này, '
    'hoặc chọn “Dùng mật khẩu”.'
)
PASSKEY_REGISTRATION_MESSAGES = {
    'missing': 'Chưa nhận được khóa truy cập từ thiết bị. Hãy bấm “Tạo khóa truy cập” và hoàn tất xác minh trên thiết bị.',
    'challenge': 'Phiên tạo khóa truy cập đã hết hạn hoặc đã được dùng. Hãy đóng hộp thoại và bấm “Thêm khóa truy cập” để làm lại.',
    'origin': 'Khóa truy cập vừa tạo không khớp với địa chỉ hệ thống hiện tại. Hãy mở đúng địa chỉ chính thức rồi tạo lại.',
    'verification': 'Thiết bị chưa xác minh được bạn (vân tay, khuôn mặt hoặc mã PIN). Hãy đóng hộp thoại và tạo lại.',
    'rejected': 'Máy chủ chưa chấp nhận khóa truy cập vừa tạo. Hãy đóng hộp thoại và bấm “Thêm khóa truy cập” để làm lại.',
}


class IdentityCheck(models.TransientModel):
    _inherit = 'res.users.identitycheck'

    def _check_identity(self):
        try:
            return super()._check_identity()
        except UserError as error:
            if self.auth_method == 'password':
                raise UserError(self.env._('Mật khẩu của bạn chưa đúng. Vui lòng nhập lại mật khẩu của tài khoản đang đăng nhập hoặc chọn Quên mật khẩu.')) from error
            if self.auth_method == 'webauthn':
                raise UserError(PASSKEY_IDENTITY_MESSAGE) from error
            raise


class PasskeyCreate(models.TransientModel):
    _inherit = 'auth.passkey.key.create'

    def make_key(self, registration=None):
        # The owner is always the session user (native writes through env.user).
        if not isinstance(registration, dict) or not registration:
            raise UserError(PASSKEY_REGISTRATION_MESSAGES['missing'])
        try:
            return super().make_key(registration)
        except AccessDenied as error:
            reason = passkey_failure_reason(error)
        except (InvalidRegistrationResponse, *PASSKEY_PAYLOAD_ERRORS) as error:
            reason = passkey_failure_reason(error)
        reason = reason if reason in PASSKEY_REGISTRATION_MESSAGES else 'rejected'
        _logger.info("Passkey registration rejected for uid %s: reason=%s", self.env.uid, reason)
        raise UserError(PASSKEY_REGISTRATION_MESSAGES[reason])
