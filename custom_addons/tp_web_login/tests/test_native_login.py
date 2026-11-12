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
        self.assertTrue(document.xpath("//*[contains(@class, 'tp-native-wordmark')]"))
        self.assertIn('TANPHAT ONE', document.text_content())
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
        self.assertEqual(bool(document.xpath("//a[starts-with(@href, '/web/signup')]")),
                         parameters.get_str('auth_signup.invitation_scope', 'b2b') == 'b2c')
        self.assertEqual(bool(document.xpath("//a[starts-with(@href, '/web/reset_password')]")),
                         parameters.get_bool('auth_signup.reset_password'))
        if self.env['ir.module.module'].search([('name', '=', 'auth_passkey')]).state == 'installed':
            self.assertTrue(document.xpath("//input[@name='webauthn_response']"))
            self.assertTrue(document.xpath("//*[contains(@class, 'passkey_login_link')]"))
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
        self.assertTrue(document.xpath("//a[starts-with(@href, '/web/signup')]"))
        self.assertTrue(document.xpath("//a[starts-with(@href, '/web/reset_password')]"))
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
        self.assertEqual(response.headers['Location'], '/odoo/tp-home')
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
        self.assertEqual(cancel.xpath("input[@name='redirect']/@value"), ['/web/login'])
        self.assertTrue(cancel.xpath("input[@name='csrf_token' and @value]"))
        bad_csrf = self.url_open('/web/session/logout', method='POST', data={
            'csrf_token': 'not-a-valid-csrf-token', 'redirect': '/web/login',
        }, allow_redirects=False)
        self.assertEqual(bad_csrf.status_code, 400)
        canceled = self.url_open('/web/session/logout', method='POST', data={
            'csrf_token': cancel.xpath("input[@name='csrf_token']/@value")[0], 'redirect': '/web/login',
        }, allow_redirects=False)
        self.assertEqual(canceled.status_code, 303)
        self.assertEqual(canceled.headers['Location'], '/web/login')

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
