import base64
import re
import secrets

from lxml import html

from odoo.tests import HttpCase, get_db_name, new_test_user, tagged

TOTP_ERROR = (
    'Chưa xác thực được mã. Vui lòng nhập mã mới nhất trên ứng dụng xác thực; '
    'nếu đã thử nhiều lần, chờ ít phút rồi thử lại.'
)


@tagged('post_install', '-at_install')
class TestNativeLogin(HttpCase):
    """AUTH-002 T10: native rendering, configuration and CSRF over real HTTP."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.password = secrets.token_urlsafe(32)
        cls.actor = new_test_user(
            cls.env, login='auth002.verify.httpcase', password=cls.password,
            groups='base.group_user', lang='en_US',
        )
        cls.actor.sudo().totp_secret = base64.b32encode(secrets.token_bytes(20)).decode()

    def _document(self, response):
        self.assertEqual(response.status_code, 200)
        document = html.fromstring(response.content)
        wordmark = document.xpath("//*[contains(@class, 'tp-native-wordmark')]")
        self.assertTrue(wordmark)
        wordmark_text = ' '.join(wordmark[0].text_content().split())
        self.assertIn('TANPHAT ONE', wordmark_text)
        self.assertIn('Vững Vàng Hội Nhập', wordmark_text)
        identity = document.xpath("//aside[contains(@class, 'tp-auth-identity')]")
        self.assertTrue(identity)
        identity_text = ' '.join(identity[0].text_content().split())
        self.assertIn('Hệ thống quản trị điều hành', identity_text)
        self.assertIn('copyright @by Tadic', identity_text)
        self.assertNotIn('Kết nối công việc', identity_text)
        tadic_link = document.xpath("//a[contains(@class, 'tp-auth-copyright-link')]")
        self.assertEqual(len(tadic_link), 1)
        self.assertEqual(tadic_link[0].get('href'), 'https://tanphatjsc.com/')
        self.assertEqual(tadic_link[0].get('target'), '_blank')
        self.assertEqual(tadic_link[0].get('rel'), 'noopener noreferrer')
        self.assertFalse(document.xpath("//*[contains(@class, 'tp-auth-brand-card')]"))
        self.assertNotIn('Powered by Odoo', ' '.join(document.text_content().split()))
        self.assertTrue(document.xpath("//input[@name='csrf_token' and @value]"))
        stylesheets = document.xpath("//link[contains(@href, '/web/assets/') and contains(@href, 'tp_web_login')]/@href")
        self.assertTrue(stylesheets)
        stylesheet = self.url_open(stylesheets[0])
        self.assertEqual(stylesheet.status_code, 200)
        self.assertIn('.tp-native-login', stylesheet.text)
        return document

    def _partial_login(self):
        response = self.url_open('/web/session/authenticate', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'db': get_db_name(), 'login': self.actor.login, 'password': self.password},
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()['result']['uid'])

    def test_login_keeps_native_fields_and_policy(self):
        document = self._document(self.url_open('/web/login', headers={'Accept-Language': 'en-US,en;q=0.9'}))
        self.assertTrue(document.xpath("//form[@data-captcha='login']"))
        self.assertTrue(document.xpath("//input[@name='login']"))
        self.assertTrue(document.xpath("//input[@name='password']"))
        self.assertTrue(document.xpath("//input[@name='redirect']"))
        parameters = self.env['ir.config_parameter'].sudo()
        self.assertEqual(bool(document.xpath("//a[starts-with(@href, '/web/signup') or starts-with(@href, '/tao-tai-khoan')]")),
                         parameters.get_str('auth_signup.invitation_scope', 'b2b') == 'b2c')
        self.assertEqual(bool(document.xpath("//a[starts-with(@href, '/web/reset_password') or starts-with(@href, '/quen-mat-khau')]")),
                         parameters.get_bool('auth_signup.reset_password'))
        if self.env['ir.module.module'].search([('name', '=', 'auth_passkey')]).state == 'installed':
            self.assertTrue(document.xpath("//input[@name='webauthn_response']"))
            passkey_links = document.xpath("//*[contains(@class, 'passkey_login_link')]")
            self.assertTrue(passkey_links)
            self.assertIn('Đăng nhập bằng khóa truy cập', ' '.join(passkey_links[0].text_content().split()))
            divider = document.xpath("//*[contains(@class, 'tp-auth-divider')]")
            self.assertTrue(divider)
            self.assertEqual(' '.join(divider[0].text_content().split()), 'Hoặc')
        self.assertEqual(document.xpath("//input[@name='login']/@type"), ['text'])
        self.assertTrue(document.xpath("//label[@for='login' and contains(text(),'Tên đăng nhập')]"))
        self.assertTrue(document.xpath("//button[@aria-label='Hiện mật khẩu']"))
        self.assertTrue(document.xpath("//aside[contains(@class,'tp-auth-identity')]"))

    def test_hr_lock_notice_password_privacy_and_feedback_placeholder(self):
        self.actor.sudo().totp_secret = False
        self.actor._tp_set_account_lock(True, 'Synthetic HTTP lock')
        response = self.url_open('/web/login')
        doc = html.fromstring(response.content)
        token = doc.xpath("//input[@name='csrf_token']/@value")[0]
        response = self.url_open('/web/login', data={
            'login': self.actor.login, 'password': 'wrong-synthetic', 'csrf_token': token,
        })
        self.assertNotIn('Tài khoản đã bị khóa', response.text)
        doc = html.fromstring(response.content)
        response = self.url_open('/web/login', data={
            'login': self.actor.login, 'password': self.password,
            'csrf_token': doc.xpath("//input[@name='csrf_token']/@value")[0],
        })
        self.assertIn('Tài khoản đã bị khóa. Vui lòng gửi phản hồi.', response.text)
        doc = html.fromstring(response.content)
        feedback = doc.xpath("//details[contains(@class,'tp-auth-feedback')]")
        self.assertEqual(len(feedback), 1)
        self.assertIn('Gửi phản hồi', feedback[0].text_content())
        self.assertFalse(feedback[0].xpath(".//form|.//a[@href]"))

    def test_hr_lock_revokes_session_even_after_unlock(self):
        self.actor.sudo().totp_secret = False
        self.authenticate(self.actor.login, self.password)
        before = self.actor._compute_session_token(self.session.sid)
        self.actor._tp_set_account_lock(True, 'Synthetic session lock')
        self.assertNotEqual(before, self.actor._compute_session_token(self.session.sid))
        self.actor._tp_set_account_lock(False, 'Synthetic session unlock')
        response = self.url_open('/web/session/get_session_info', json={
            'jsonrpc': '2.0', 'method': 'call', 'params': {}, 'id': 1,
        })
        self.assertIn('error', response.json())
        self.assertNotIn('result', response.json())

    def test_enabled_self_service_remains_native(self):
        parameters = self.env['ir.config_parameter'].sudo()
        parameters.set_str('auth_signup.invitation_scope', 'b2c')
        parameters.set_bool('auth_signup.reset_password', True)
        document = self._document(self.url_open('/web/login'))
        self.assertTrue(document.xpath("//a[starts-with(@href, '/web/signup') or starts-with(@href, '/tao-tai-khoan')]"))
        self.assertTrue(document.xpath("//a[starts-with(@href, '/web/reset_password') or starts-with(@href, '/quen-mat-khau')]"))
        for route in ('/web/signup', '/web/reset_password'):
            page = self._document(self.url_open(route))
            self.assertTrue(page.xpath("//form[@method='post' and @data-captcha]"))

    def test_password_login_csrf_redirect_and_logout(self):
        actor = new_test_user(self.env, login='shellauth.http.plain', password=self.password,
                              groups='base.group_user')
        document = self._document(self.url_open('/web/login'))
        bad = self.url_open('/web/login', method='POST', data={
            'csrf_token': 'invalid', 'login': actor.login, 'password': self.password,
        }, allow_redirects=False)
        self.assertEqual(bad.status_code, 400)
        response = self.url_open('/web/login', method='POST', data={
            'csrf_token': document.xpath("//input[@name='csrf_token']/@value")[0],
            'login': actor.login, 'password': self.password, 'type': 'password',
            'redirect': '/odoo/tp-home',
        }, allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        # tp_branding (BRAND-WHITELABEL-002) serves the webclient on /app.
        self.assertIn(response.headers['Location'], ('/odoo/tp-home', '/app/tp-home'))
        # The core local redirect normalizes external input to this origin.
        external = self.url_open('/web/login', params={'redirect': 'https://example.invalid/escape'},
                                 allow_redirects=False)
        self.assertNotIn('https://example.invalid', external.headers.get('Location', ''))
        page = self.url_open('/odoo/tp-home')
        token = re.search(r'csrf_token:\s*"([^"]+)"', page.text)
        self.assertIsNotNone(token)
        ended = self.url_open('/web/session/logout', method='POST', data={
            'csrf_token': token[1], 'redirect': '/web/login',
        }, allow_redirects=False)
        self.assertEqual(ended.status_code, 303)
        self.assertEqual(self.url_open('/api/v1/me').status_code, 401)

    def test_t10_totp_fixed_vietnamese_and_cancel_csrf(self):
        self._partial_login()
        redirect = '/odoo/action-tp_web_home.action_home?test=1#details'
        response = self.url_open('/web/login/totp', params={'redirect': redirect}, headers={'Accept-Language': 'en-US'})
        document = self._document(response)
        content = ' '.join(document.text_content().split())
        for text in (
            'Nhập mã xác thực', 'Mở ứng dụng xác thực để xem mã gồm 6 chữ số.',
            'Không hỏi lại trên thiết bị này', 'Xác nhận', 'Hủy và quay lại',
        ):
            self.assertIn(text, content)
        self.assertFalse(document.xpath("//input[@name='password']"))
        token = document.xpath("//input[@name='totp_token']")[0]
        self.assertEqual(token.get('placeholder'), 'Mã 6 chữ số')
        self.assertEqual(token.get('autocomplete'), 'one-time-code')
        self.assertEqual(token.get('inputmode'), 'numeric')
        self.assertTrue(document.xpath("//input[@name='remember' and @value='1']"))
        self.assertEqual(document.xpath("//form[@action='']/input[@name='redirect']/@value"), [redirect])
        cancel = document.xpath("//form[@action='/web/session/logout']")[0]
        self.assertEqual(cancel.get('method').upper(), 'POST')
        self.assertIn(cancel.xpath("input[@name='redirect']/@value"), (['/web/login'], ['/dang-nhap']))
        self.assertTrue(cancel.xpath("input[@name='csrf_token' and @value]"))
        bad_csrf = self.url_open('/web/session/logout', method='POST', data={
            'csrf_token': 'not-a-valid-csrf-token', 'redirect': '/web/login',
        }, allow_redirects=False)
        self.assertEqual(bad_csrf.status_code, 400)
        canceled = self.url_open('/web/session/logout', method='POST', data={
            'csrf_token': cancel.xpath("input[@name='csrf_token']/@value")[0], 'redirect': '/web/login',
        }, allow_redirects=False)
        self.assertEqual(canceled.status_code, 303)
        self.assertIn(canceled.headers['Location'], ('/web/login', '/dang-nhap'))

    def test_t10_totp_error_masks_native_server_message(self):
        self._partial_login()
        document = self._document(self.url_open('/web/login/totp', headers={'Accept-Language': 'en-US'}))
        # Non-numeric format deterministically exercises native error handling without a chance of a valid code.
        response = self.url_open('/web/login/totp', method='POST', headers={'Accept-Language': 'en-US'}, data={
            'csrf_token': document.xpath("//input[@name='csrf_token']/@value")[0],
            'redirect': '/work/projects', 'totp_token': 'invalid-format',
        })
        error = self._document(response).xpath("//*[@role='alert']")[0]
        self.assertEqual(error.text_content().strip(), TOTP_ERROR)
        self.assertNotIn('Invalid authentication code format', response.text)

    def test_single_active_session_replaces_old_cookie_and_preserves_winner_on_old_logout(self):
        actor = new_test_user(
            self.env, login='auth001.single.session', password=self.password,
            groups='base.group_user',
        )
        # Session A logs in via JSON-RPC
        res_a = self.url_open('/web/session/authenticate', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 10,
            'params': {'db': get_db_name(), 'login': actor.login, 'password': self.password},
        })
        self.assertEqual(res_a.json()['result']['uid'], actor.id)
        sid_a = self.opener.cookies.get('session_id')
        self.assertTrue(sid_a)

        # Wrong password from another session does not kick Session A
        self.opener.cookies.clear()
        bad_login = self.url_open('/web/session/authenticate', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 11,
            'params': {'db': get_db_name(), 'login': actor.login, 'password': 'wrong-password'},
        })
        self.assertIn('error', bad_login.json())
        self.opener.cookies.set('session_id', sid_a)
        still_ok = self.url_open('/api/v1/me')
        self.assertEqual(still_ok.status_code, 200)

        # Session B logs in with a fresh cookie jar -> replaces Session A
        self.opener.cookies.clear()
        res_b = self.url_open('/web/session/authenticate', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 12,
            'params': {'db': get_db_name(), 'login': actor.login, 'password': self.password},
        })
        self.assertEqual(res_b.json()['result']['uid'], actor.id)
        sid_b = self.opener.cookies.get('session_id')
        self.assertNotEqual(sid_a, sid_b)

        # Session A's old cookie is immediately rejected with session_replaced on API & JSON-RPC
        self.opener.cookies.set('session_id', sid_a)
        api_a = self.url_open('/api/v1/me')
        self.assertEqual(api_a.status_code, 401)
        self.assertEqual(api_a.json()['error']['code'], 'session_replaced')
        rpc_a = self.url_open('/web/session/check', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 13, 'params': {},
        })
        self.assertEqual(rpc_a.json()['error']['data']['context']['tp_session_reason'], 'session_replaced')

        # Session B stays active even after A's stale session was terminated
        self.opener.cookies.set('session_id', sid_b)
        self.assertEqual(self.url_open('/api/v1/me').status_code, 200)
