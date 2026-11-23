"""Self-service security: session-derived identity and native, identity-checked actions."""
import base64
import binascii

from odoo import api, fields, models
from odoo.exceptions import AccessDenied, AccessError, UserError
from odoo.http import request
from odoo.http.session import STORED_SESSION_BYTES
from odoo.tools import SQL
from odoo.tools._vendor.useragents import UserAgent
from odoo.tools.date_utils import all_timezones

from odoo.addons.base.models.res_users import check_identity

_MOBILE_PLATFORMS = ('android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone', 'webos')
_PLATFORM_LABELS = {
    'windows': 'Windows',
    'macos': 'macOS',
    'linux': 'Linux',
    'android': 'Android',
    'iphone': 'iPhone (iOS)',
    'ipad': 'iPad (iPadOS)',
    'chromeos': 'ChromeOS',
}
_BROWSER_LABELS = {
    'chrome': 'Chrome',
    'firefox': 'Firefox',
    'safari': 'Safari',
    'edge': 'Microsoft Edge',
    'msie': 'Internet Explorer',
    'opera': 'Opera',
    'samsung': 'Samsung Internet',
}
_DURATION_LABELS_VI = {
    '1': '1 ngày',
    '7': '1 tuần',
    '30': '1 tháng',
    '90': '3 tháng',
    '180': '6 tháng',
    '365': '1 năm',
    '0': 'Không giới hạn',
}
_SCOPE_LABELS_VI = {
    'rpc': 'Kết nối RPC',
}


def _parse_user_agent(user_agent: str) -> dict:
    raw_platform, raw_browser, raw_version, _lang = UserAgent._parser(user_agent or '')
    plat_key = (raw_platform or '').strip().lower()
    brow_key = (raw_browser or '').strip().lower()
    platform = _PLATFORM_LABELS.get(plat_key) or (raw_platform.capitalize() if raw_platform else 'Không rõ')
    browser = _BROWSER_LABELS.get(brow_key) or (raw_browser.capitalize() if raw_browser else 'Không rõ')
    if raw_version and browser != 'Không rõ':
        major = str(raw_version).split('.', 1)[0]
        browser_display = f'{browser} {major}' if major.isdigit() else browser
    else:
        browser_display = browser
    device_type = 'mobile' if plat_key in _MOBILE_PLATFORMS else 'computer'
    name = f'{platform} · {browser_display}' if (platform != 'Không rõ' or browser_display != 'Không rõ') else 'Trình duyệt không rõ'
    return {
        'name': name,
        'platform': platform,
        'browser': browser_display,
        'device_type': device_type,
    }


def _format_session_row(row_id, user_agent, first_activity, last_activity, is_current, revoked) -> dict:
    parsed = _parse_user_agent(user_agent)
    if is_current:
        state = 'current'
        state_label = 'Thiết bị này · Đang hoạt động'
    elif revoked:
        state = 'revoked'
        state_label = 'Đã thu hồi'
    else:
        state = 'ended_uncleaned'
        state_label = 'Đã kết thúc (chưa dọn)'
    return {
        'id': int(row_id),
        'name': parsed['name'],
        'platform': parsed['platform'],
        'browser': parsed['browser'],
        'device_type': parsed['device_type'],
        'first_activity': fields.Datetime.to_string(first_activity) if first_activity else False,
        'last_activity': fields.Datetime.to_string(last_activity) if last_activity else False,
        'is_current': bool(is_current),
        'revoked': bool(revoked),
        'state': state,
        'state_label': state_label,
        'can_revoke': bool(not is_current and not revoked),
    }


class AccountSecurity(models.Model):
    _inherit = 'res.users'

    @api.model
    def action_get(self):
        return self.env.ref('tp_web_login.action_account_security').sudo().read()[0]

    def _tp_account_role_label(self):
        """Return (role_code, role_label) derived from authoritative backend groups."""
        self.ensure_one()
        if self.has_group('base.group_system'):
            return 'system_admin', 'Quản trị hệ thống'
        return 'employee', 'Nhân viên nội bộ'

    def _tp_can_manage_own_api_keys(self):
        self.ensure_one()
        if self.share or not self._is_internal():
            return False
        return bool(
            self.env['res.users.apikeys'].has_access('read')
            and self.env['res.users.apikeys.description'].has_access('create')
        )

    def _tp_session_history_payload(self, status, limit, offset):
        """Query deduplicated per-session history from res_device_log for self.env.uid only.

        Never returns session_identifier, cookie, nonce or token.
        """
        uid = int(self.env.uid)
        current_sid = request.session.sid[:STORED_SESSION_BYTES] if (request and getattr(request, 'session', None) and request.session.sid) else ''

        # Deduplicate res_device_log per session_identifier for this user:
        # - revoked is FALSE if any row for this session_identifier is not yet revoked (matches res.session)
        # - latest row supplies id, user_agent, last_activity; earliest row supplies first_activity
        cte = SQL(
            """
            WITH grouped AS (
                SELECT DISTINCT ON (session_identifier)
                    id,
                    session_identifier,
                    user_agent,
                    last_activity,
                    BOOL_AND(COALESCE(revoked, FALSE)) OVER (PARTITION BY session_identifier) AS all_revoked,
                    MIN(first_activity) OVER (PARTITION BY session_identifier) AS first_activity
                FROM res_device_log
                WHERE user_id = %(uid)s
                ORDER BY session_identifier, COALESCE(revoked, FALSE) ASC, last_activity DESC, id DESC
            )
            """,
            uid=uid,
        )

        # Summary counts across all distinct session_identifiers for this user.
        self.env.cr.execute(SQL(
            """
            %(cte)s
            SELECT
                COUNT(*) AS total_count,
                COUNT(*) FILTER (WHERE session_identifier = %(cur)s AND NOT all_revoked) AS current_count,
                COUNT(*) FILTER (WHERE session_identifier != %(cur)s AND NOT all_revoked) AS uncleaned_other_count,
                COUNT(*) FILTER (WHERE all_revoked) AS revoked_count
            FROM grouped
            """,
            cte=cte, cur=current_sid,
        ))
        total_history, _cur_cnt, uncleaned_other_count, revoked_history_count = self.env.cr.fetchone()

        # Current session card (strictly matched to current HTTP session identifier).
        current_session = None
        if current_sid:
            self.env.cr.execute(SQL(
                """
                %(cte)s
                SELECT id, user_agent, first_activity, last_activity, all_revoked
                FROM grouped
                WHERE session_identifier = %(cur)s
                LIMIT 1
                """,
                cte=cte, cur=current_sid,
            ))
            cur_row = self.env.cr.fetchone()
            if cur_row:
                current_session = _format_session_row(
                    cur_row[0], cur_row[1], cur_row[2], cur_row[3], True, False,
                )

        if status == 'current':
            where_sql = SQL("WHERE session_identifier = %(cur)s AND NOT all_revoked", cur=current_sid)
        elif status == 'uncleaned':
            where_sql = SQL("WHERE session_identifier != %(cur)s AND NOT all_revoked", cur=current_sid)
        elif status == 'revoked':
            where_sql = SQL("WHERE all_revoked IS TRUE")
        else:
            where_sql = SQL("")

        self.env.cr.execute(SQL(
            "%(cte)s SELECT COUNT(*) FROM grouped %(where_sql)s",
            cte=cte, where_sql=where_sql,
        ))
        filtered_count = int(self.env.cr.fetchone()[0] or 0)

        self.env.cr.execute(SQL(
            """
            %(cte)s
            SELECT id, user_agent, first_activity, last_activity,
                   (session_identifier = %(cur)s AND NOT all_revoked) AS is_current,
                   all_revoked
            FROM grouped
            %(where_sql)s
            ORDER BY (session_identifier = %(cur)s AND NOT all_revoked) DESC,
                     all_revoked ASC,
                     last_activity DESC,
                     id DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            cte=cte, cur=current_sid, where_sql=where_sql, limit=limit, offset=offset,
        ))
        rows = [
            _format_session_row(r[0], r[1], r[2], r[3], r[4], r[5])
            for r in self.env.cr.fetchall()
        ]

        return {
            'current_session': current_session,
            'other_active_session_count': 0,
            'single_session_policy': True,
            'session_summary': {
                'total_history_count': int(total_history or 0),
                'uncleaned_other_count': int(uncleaned_other_count or 0),
                'revoked_history_count': int(revoked_history_count or 0),
            },
            'sessions': rows,
            'session_count': filtered_count,
        }

    @api.model
    def tp_my_security(self, status='all', limit=100, offset=0):
        if self.env.user.share:
            raise AccessError(self.env._('Chức năng dành cho tài khoản nội bộ.'))
        if status not in ('all', 'current', 'uncleaned', 'revoked') or type(limit) is not int or limit not in (10, 20, 50, 100):
            raise UserError(self.env._('Bộ lọc phiên không hợp lệ.'))
        if type(offset) is not int or offset < 0:
            raise UserError(self.env._('Trang dữ liệu không hợp lệ.'))
        user = self.env.user
        role_code, role_label = user._tp_account_role_label()
        api_keys_allowed = user._tp_can_manage_own_api_keys()
        now = fields.Datetime.now()
        keys = user.api_key_ids if api_keys_allowed else []
        passkeys = user.auth_passkey_key_ids if 'auth_passkey_key_ids' in user._fields else []
        session_info = self._tp_session_history_payload(status, limit, offset)
        return {
            'name': user.name,
            'login': user.login,
            'user_id': user.id,
            'role_code': role_code,
            'role_label': role_label,
            'lang': user.lang,
            'tz': user.tz or 'Asia/Ho_Chi_Minh',
            'languages': self.env['res.lang'].get_installed(),
            'timezones': all_timezones,
            'totp_enabled': user.totp_enabled,
            'passkey_supported': 'auth_passkey_key_ids' in user._fields,
            'api_keys_allowed': api_keys_allowed,
            **session_info,
            'keys': [{
                'id': key.id,
                'name': key.name,
                'scope': key.scope or 'rpc',
                'scope_label': _SCOPE_LABELS_VI.get(key.scope or 'rpc', key.scope or 'RPC'),
                'created': fields.Datetime.to_string(key.create_date),
                'expires': fields.Datetime.to_string(key.expiration_date),
                'expired': bool(key.expiration_date and key.expiration_date <= now),
                'status_label': 'Đã hết hạn' if (key.expiration_date and key.expiration_date <= now) else 'Còn hiệu lực',
            } for key in keys],
            'passkeys': [{
                'id': key.id,
                'name': key.name,
                'created': fields.Datetime.to_string(key.create_date),
            } for key in passkeys],
        }

    @api.model
    def tp_change_my_password(self, old_password, new_password, confirm_password):
        """Change the current session user's own password via native Odoo verification & hashing."""
        if self.env.user.share:
            raise AccessError(self.env._('Chức năng dành cho tài khoản nội bộ.'))
        if not isinstance(old_password, str) or not old_password:
            raise UserError(self.env._('Vui lòng nhập mật khẩu hiện tại.'))
        if not isinstance(new_password, str) or not new_password.strip():
            raise UserError(self.env._('Vui lòng nhập mật khẩu mới.'))
        if not isinstance(confirm_password, str) or new_password != confirm_password:
            raise UserError(self.env._('Xác nhận mật khẩu mới chưa khớp.'))
        user = self.env.user.with_user(self.env.uid)
        try:
            with user._assert_can_auth(user=user.login):
                user.change_password(old_password, new_password)
        except AccessDenied as error:
            raise AccessDenied(self.env._('Mật khẩu hiện tại chưa đúng. Vui lòng kiểm tra lại.')) from error
        if request and getattr(request, 'session', None) and request.session.uid == self.env.uid:
            self.env.flush_all()
            self.env.transaction.invalidate_ormcache()
            request.session.session_token = user._compute_session_token(request.session.sid)
        return True

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
            'sessions_revoke': ('action_revoke_all_devices', 'Thu hồi các phiên khác'),
        }
        if operation in methods:
            method, title = methods[operation]
            if operation == 'passkey_create' and 'auth_passkey_key_ids' not in user._fields:
                raise UserError(self.env._('Khóa truy cập chưa được hỗ trợ.'))
            if operation == 'api_create' and not user._tp_can_manage_own_api_keys():
                raise AccessError(self.env._('Tài khoản không có quyền tạo khóa API.'))
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

    @check_identity
    def action_totp_disable(self):
        result = super().action_totp_disable()
        if isinstance(result, dict) and result.get('tag') == 'display_notification':
            params = dict(result.get('params') or {})
            params['message'] = self.env._('Đã tắt xác thực hai bước cho tài khoản %s.', ', '.join(self.mapped('name')))
            result['params'] = params
        return result


class AuthTotpWizardLocalized(models.TransientModel):
    _inherit = 'auth_totp.wizard'

    @check_identity
    def enable(self):
        try:
            result = super().enable()
        except UserError as error:
            msg = str(error)
            if 'only contain numbers' in msg:
                raise UserError(self.env._('Mã xác thực chỉ được chứa chữ số (6 số).')) from error
            if 'Verification failed' in msg:
                raise UserError(self.env._('Mã xác thực chưa đúng. Vui lòng kiểm tra lại mã 6 số trên ứng dụng xác thực.')) from error
            raise
        if isinstance(result, dict) and result.get('tag') == 'display_notification':
            params = dict(result.get('params') or {})
            params['message'] = self.env._('Đã bật xác thực hai bước thành công.')
            result['params'] = params
        return result


class ResUsersApikeysDescriptionLocalized(models.TransientModel):
    _inherit = 'res.users.apikeys.description'

    def _selection_duration(self):
        return [
            (code, _DURATION_LABELS_VI.get(code, label))
            for code, label in super()._selection_duration()
        ]

    @check_identity
    def make_key(self):
        result = super().make_key()
        if isinstance(result, dict) and result.get('res_model') == 'res.users.apikeys.show':
            result['name'] = self.env._('Lưu khóa API của bạn')
            result['context'] = dict(result.get('context') or {}, dialog_size='medium')
        return result
