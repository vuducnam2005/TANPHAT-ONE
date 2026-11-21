"""Self-service security: session-derived identity and native, identity-checked actions."""
import base64
import binascii

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.http import request
from odoo.http.session import STORED_SESSION_BYTES
from odoo.tools.date_utils import all_timezones

from odoo.addons.base.models.res_users import check_identity


class AccountSecurity(models.Model):
    _inherit = 'res.users'

    @api.model
    def action_get(self):
        return self.env.ref('tp_web_login.action_account_security').sudo().read()[0]

    @api.model
    def tp_my_security(self, status='all', limit=10, offset=0):
        if self.env.user.share:
            raise AccessError(self.env._('Chức năng dành cho tài khoản nội bộ.'))
        if status not in ('all', 'current', 'revoked') or type(limit) is not int or limit not in (10, 20, 50):
            raise UserError(self.env._('Bộ lọc phiên không hợp lệ.'))
        if type(offset) is not int or offset < 0:
            raise UserError(self.env._('Trang dữ liệu không hợp lệ.'))
        user = self.env.user
        domain = [('user_id', '=', self.env.uid)]
        if status == 'current':
            # is_current has no search method; use the trusted HTTP session internally.
            domain.append(('session_identifier', '=', request.session.sid[:STORED_SESSION_BYTES] if request else ''))
        elif status == 'revoked':
            domain.append(('revoked', '=', True))
        sessions = self.env['res.session'].search(domain, limit=limit, offset=offset)
        now = fields.Datetime.now()
        keys = user.api_key_ids
        passkeys = user.auth_passkey_key_ids if 'auth_passkey_key_ids' in user._fields else []
        return {
            'name': user.name, 'login': user.login, 'user_id': user.id,
            'lang': user.lang, 'tz': user.tz or 'Asia/Ho_Chi_Minh',
            'languages': self.env['res.lang'].get_installed(),
            'timezones': all_timezones,
            'totp_enabled': user.totp_enabled,
            'passkey_supported': 'auth_passkey_key_ids' in user._fields,
            'sessions': [{
                'id': row.id, 'name': row.display_name,
                'last_activity': fields.Datetime.to_string(row.last_activity),
                'is_current': row.is_current, 'revoked': row.revoked,
            } for row in sessions],
            'session_count': self.env['res.session'].search_count(domain),
            'keys': [{
                'id': key.id, 'name': key.name,
                'created': fields.Datetime.to_string(key.create_date),
                'expires': fields.Datetime.to_string(key.expiration_date),
                'expired': bool(key.expiration_date and key.expiration_date <= now),
            } for key in keys],
            'passkeys': [{'id': key.id, 'name': key.name} for key in passkeys],
        }

    @api.model
    def tp_save_my_preferences(self, values):
        if self.env.user.share or not isinstance(values, dict) or set(values) - {'lang', 'tz', 'image_1920'}:
            raise AccessError(self.env._('Chỉ được cập nhật tùy chọn cá nhân được phép.'))
        if 'tz' in values and values['tz'] not in all_timezones:
            raise UserError(self.env._('Múi giờ không hợp lệ.'))
        if 'lang' in values and values['lang'] not in dict(self.env['res.lang'].get_installed()):
            raise UserError(self.env._('Ngôn ngữ chưa được kích hoạt.'))
        if 'image_1920' in values:
            image = values['image_1920']
            if not isinstance(image, str) or len(image) > 7 * 1024 * 1024:
                raise UserError(self.env._('Ảnh không hợp lệ hoặc vượt quá 5 MB.'))
            try:
                decoded = base64.b64decode(image, validate=True)
            except (ValueError, binascii.Error) as error:
                raise UserError(self.env._('Ảnh không hợp lệ hoặc vượt quá 5 MB.')) from error
            if len(decoded) > 5 * 1024 * 1024:
                raise UserError(self.env._('Ảnh không hợp lệ hoặc vượt quá 5 MB.'))
        user = self.env.user.with_user(self.env.uid)
        if 'image_1920' in values and hasattr(user, 'tp_save_my_profile') and user.employee_id:
            user.tp_save_my_profile({'image_1920': values['image_1920']})
            values = {key: value for key, value in values.items() if key != 'image_1920'}
        if values:
            user.write(values)
        return True

    @api.model
    @check_identity
    def tp_security_action(self, operation, record_id=None):
        if self.env.user.share:
            raise AccessError(self.env._('Chức năng dành cho tài khoản nội bộ.'))
        user = self.env.user.with_user(self.env.uid)
        if not isinstance(operation, str):
            raise UserError(self.env._('Thao tác không hợp lệ.'))
        methods = {
            'password': ('preference_change_password', 'Đổi mật khẩu'),
            'totp_enable': ('action_totp_enable_wizard', 'Bật xác thực hai bước'),
            'totp_disable': ('action_totp_disable', 'Tắt xác thực hai bước'),
            'api_create': ('api_key_wizard', 'Tạo khóa API'),
            'passkey_create': ('action_create_passkey', 'Thêm khóa truy cập'),
            'sessions_revoke': ('action_revoke_all_devices', 'Đăng xuất các phiên khác'),
        }
        if operation in methods:
            method, title = methods[operation]
            if operation == 'passkey_create' and 'auth_passkey_key_ids' not in user._fields:
                raise UserError(self.env._('Khóa truy cập chưa được hỗ trợ.'))
            result = getattr(user, method)()
            if isinstance(result, dict) and result.get('type') == 'ir.actions.act_window':
                result['name'] = title
                result['context'] = dict(result.get('context') or {}, dialog_size='medium')
            return result
        targets = {
            'session_revoke': ('res.session', 'user_id', 'revoke'),
            'api_remove': ('res.users.apikeys', 'user_id', 'remove'),
            'passkey_remove': ('auth.passkey.key', 'create_uid', 'action_delete_passkey'),
            'passkey_rename': ('auth.passkey.key', 'create_uid', 'action_rename_passkey'),
        }
        if operation not in targets or type(record_id) is not int or record_id <= 0:
            raise UserError(self.env._('Thao tác không hợp lệ.'))
        model, owner, method = targets[operation]
        if model not in self.env:
            raise UserError(self.env._('Chức năng chưa được hỗ trợ.'))
        record = self.env[model].search([('id', '=', record_id), (owner, '=', self.env.uid)], limit=1)
        if not record:
            raise AccessError(self.env._('Không có quyền thao tác dữ liệu bảo mật này.'))
        if operation == 'session_revoke' and record.is_current:
            raise UserError(self.env._('Dùng chức năng Đăng xuất để kết thúc phiên hiện tại.'))
        return getattr(record, method)()
