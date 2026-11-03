import base64
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

    def test_t10_login_keeps_native_fields_and_disables_self_service(self):
        document = self._document(self.url_open('/web/login', headers={'Accept-Language': 'en-US,en;q=0.9'}))
        self.assertTrue(document.xpath("//form[@data-captcha='login']"))
        self.assertTrue(document.xpath("//input[@name='login']"))
        self.assertTrue(document.xpath("//input[@name='password']"))
        self.assertTrue(document.xpath("//input[@name='redirect']"))
        # T10's verification environment includes auth_passkey, as in V-C.
        self.assertEqual(self.env['ir.module.module'].search([('name', '=', 'auth_passkey')]).state, 'installed')
        self.assertTrue(document.xpath("//input[@name='webauthn_response']"))
        self.assertTrue(document.xpath("//*[contains(@class, 'passkey_login_link')]"))
        self.assertFalse(document.xpath("//a[starts-with(@href, '/web/signup')]"))
        self.assertFalse(document.xpath("//a[starts-with(@href, '/web/reset_password')]"))
        parameters = self.env['ir.config_parameter'].sudo()
        self.assertEqual(parameters.get_str('auth_signup.invitation_scope'), 'b2b')
        self.assertFalse(parameters.get_bool('auth_signup.reset_password'))
        self.assertEqual(self.url_open('/web/signup', allow_redirects=False).status_code, 404)
        self.assertEqual(self.url_open('/web/reset_password', allow_redirects=False).status_code, 404)

    def test_t10_totp_fixed_vietnamese_and_cancel_csrf(self):
        self._partial_login()
        redirect = '/work/projects?q=AUTH002#details'
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
        self.assertEqual(cancel.xpath("input[@name='redirect']/@value"), ['/work/'])
        self.assertTrue(cancel.xpath("input[@name='csrf_token' and @value]"))
        bad_csrf = self.url_open('/web/session/logout', method='POST', data={
            'csrf_token': 'not-a-valid-csrf-token', 'redirect': '/work/',
        }, allow_redirects=False)
        self.assertEqual(bad_csrf.status_code, 400)
        canceled = self.url_open('/web/session/logout', method='POST', data={
            'csrf_token': cancel.xpath("input[@name='csrf_token']/@value")[0], 'redirect': '/work/',
        }, allow_redirects=False)
        self.assertEqual(canceled.status_code, 303)
        self.assertEqual(canceled.headers['Location'], '/work/')

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
