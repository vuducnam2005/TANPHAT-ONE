from odoo import models
from odoo.exceptions import UserError


class IdentityCheck(models.TransientModel):
    _inherit = 'res.users.identitycheck'

    def _check_identity(self):
        try:
            return super()._check_identity()
        except UserError as error:
            if self.auth_method == 'password':
                raise UserError(self.env._('Mật khẩu của bạn chưa đúng. Vui lòng nhập lại mật khẩu của tài khoản đang đăng nhập hoặc chọn Quên mật khẩu.')) from error
            raise
