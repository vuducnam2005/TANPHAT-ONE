"""ACCOUNT_SECURITY passkey flow over real HTTP with native auth_passkey.

A software authenticator (tests only) signs genuine WebAuthn payloads for the
production RP ID ``tpone.tadic.vn``; every check stays native. These tests
prove the software flow, not a physical biometric device.
"""
import json
import secrets

from lxml import html

from odoo.tests import HttpCase, get_db_name, new_test_user, tagged
from odoo.tools import mute_logger

from .passkey_authenticator import PasskeyHttpMixin, SoftAuthenticator
from odoo.addons.tp_web_login.models.identitycheck import (
    PASSKEY_IDENTITY_MESSAGE,
    PASSKEY_REGISTRATION_MESSAGES,
)
from odoo.addons.tp_web_login.models.res_users import LOCKED_MESSAGE, PASSKEY_MESSAGES

HINT = 'Dùng khóa truy cập đã đăng ký cho tài khoản trên thiết bị hoặc trình quản lý mật khẩu của bạn.'
OLD_ORIGIN = 'https://tpone-old.trycloudflare.com'


@tagged('post_install', '-at_install', 'tp_passkey')
class TestPasskeyFlow(PasskeyHttpMixin, HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.password = secrets.token_urlsafe(32)
        cls.actor = new_test_user(cls.env, login='passkey001.flow.actor', password=cls.password,
                                  groups='base.group_user')
        cls.other = new_test_user(cls.env, login='passkey001.flow.other', password=cls.password,
                                  groups='base.group_user')

    def setUp(self):
        super().setUp()
        self.use_production_domain()
        # Failure cases are checked one by one; the cooldown has its own test.
        self.env['ir.config_parameter'].sudo().set_str('base.login_cooldown_after', '0')
        self.clear_login_failures()
        self.addCleanup(self.clear_login_failures)

    def _key(self, authenticator):
        return self.env['auth.passkey.key'].sudo().search([('credential_identifier', '=', authenticator.id)])

    def _registered(self, user=None):
        user = user or self.actor
        self.authenticate(user.login, self.password)
        authenticator = self.register_passkey(user, self.password)
        self.opener.cookies.clear()
        return authenticator

    def _fresh_browser(self):
        self.opener.cookies.clear()
        self.clear_login_failures()

    def _assert_rejected(self, response, reason, key=None, sign_count=None):
        self.assertEqual(self.login_error(response), PASSKEY_MESSAGES[reason])
        self.assertIsNone(self.session_uid(), 'A rejected passkey must not leave a logged-in session.')
        if key is not None:
            self.assertEqual(key.sign_count, sign_count, 'A rejected passkey must not move the counter.')

    def test_login_page_hint_and_native_fields(self):
        page = html.fromstring(self.url_open('/web/login').content)
        self.assertEqual(' '.join(page.xpath("string(//*[contains(@class,'tp-passkey-hint')])").split()), HINT)
        self.assertEqual(' '.join(page.xpath("string(//*[contains(@class,'passkey_login_link')])").split()),
                         'Đăng nhập bằng khóa truy cập')
        self.assertTrue(page.xpath("//*[contains(@class,'tp-passkey-feedback') and @aria-live='polite']"))
        self.assertTrue(page.xpath("//input[@name='password']"), 'Password login must stay available.')
        self.assertTrue(page.xpath("//input[@name='webauthn_response']"))
        options = self.start_auth()
        self.assertEqual(options['rpId'], 'tpone.tadic.vn')
        self.assertEqual(options['userVerification'], 'required')
        self.assertFalse(options.get('allowCredentials'), 'Discoverable login must not list credentials.')

    def test_register_login_rename_revoke_with_native_session(self):
        authenticator = self._registered()
        key = self._key(authenticator)
        self.assertEqual(key.create_uid, self.actor)
        self.assertEqual(key.name, 'Máy thử nghiệm')
        self.assertEqual(key.sign_count, 0)

        response = self.post_passkey_login(authenticator.assertion(self.start_auth()['challenge']))
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.session_uid(), self.actor.id)
        self.assertEqual(key.sign_count, 1)

        # A fresh passkey session asks the identity check again; it defaults to the passkey.
        response = self.security_action('passkey_rename', key.id, authenticator=authenticator)
        self.assertEqual(response['result']['res_model'], 'auth.passkey.key')
        self.assertEqual(key.sign_count, 2)
        self.rpc_result('auth.passkey.key', 'write', [key.id], {'name': 'Máy đổi tên'})
        self.assertEqual(key.name, 'Máy đổi tên')

        self.expire_identity_check()
        response = self.security_action('passkey_remove', key.id, authenticator=authenticator)
        self.assertNotIn('error', response, response.get('error'))
        self.assertFalse(key.exists())

        self._fresh_browser()
        response = self.post_passkey_login(authenticator.assertion(self.start_auth()['challenge']))
        self._assert_rejected(response, 'unknown')

    def test_login_cannot_choose_another_owner(self):
        authenticator = self._registered()
        response = self.post_passkey_login(authenticator.assertion(self.start_auth()['challenge']),
                                           login=self.other.login)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.session_uid(), self.actor.id)

    @mute_logger('odoo.addons.tp_web_login.models.res_users')
    def test_login_failures_are_specific_and_leave_no_session(self):
        authenticator = self._registered()
        key = self._key(authenticator)
        stale = authenticator.assertion(self.start_auth()['challenge'])
        self.assertEqual(self.post_passkey_login(stale).status_code, 303)
        count = key.sign_count

        def signed(**options):
            return authenticator.assertion(self.start_auth()['challenge'], **options)

        cases = [
            ('challenge', lambda: stale),  # no challenge in this browser session
            ('challenge', lambda: self.start_auth() and stale),  # replay against a new challenge
            ('origin', lambda: signed(origin=OLD_ORIGIN)),  # key made on an old address
            ('origin', lambda: signed(rp_id='localhost')),
            ('verification', lambda: signed(user_verified=False)),
            ('counter', lambda: signed(count=count)),
            ('rejected', lambda: signed(bad_signature=True)),
            ('unknown', lambda: self.new_authenticator(self.actor).assertion(self.start_auth()['challenge'])),
        ]
        for reason, build in cases:
            with self.subTest(reason=reason):
                self._fresh_browser()
                self._assert_rejected(self.post_passkey_login(build()), reason, key, count)

        for payload in ('not json', json.dumps({'id': 5}), json.dumps([]),
                        json.dumps({'id': authenticator.id, 'response': {}})):
            with self.subTest(payload=payload[:20]):
                self._fresh_browser()
                self.start_auth()
                self._assert_rejected(self.post_passkey_login(payload), 'rejected', key, count)

    @mute_logger('odoo.addons.tp_web_login.models.res_users', 'odoo.addons.base.models.res_users')
    def test_native_cooldown_applies_and_is_explained(self):
        authenticator = self._registered()
        self.env['ir.config_parameter'].sudo().set_str('base.login_cooldown_after', '2')
        for _attempt in range(2):
            self.opener.cookies.clear()
            assertion = authenticator.assertion(self.start_auth()['challenge'], bad_signature=True)
            self.assertEqual(self.login_error(self.post_passkey_login(assertion)), PASSKEY_MESSAGES['rejected'])
        self.opener.cookies.clear()
        response = self.post_passkey_login(authenticator.assertion(self.start_auth()['challenge']))
        self._assert_rejected(response, 'cooldown')

    @mute_logger('odoo.addons.tp_web_login.models.res_users')
    def test_locked_account_needs_a_valid_key_before_lock_notice(self):
        authenticator = self._registered()
        self.actor._tp_set_account_lock(True, 'Synthetic passkey lock')
        forged = authenticator.assertion(self.start_auth()['challenge'], bad_signature=True)
        response = self.post_passkey_login(forged)
        self.assertNotIn('Tài khoản đã bị khóa', response.text, 'No lock disclosure without the key.')
        self.assertIsNone(self.session_uid())

        self._fresh_browser()
        response = self.post_passkey_login(authenticator.assertion(self.start_auth()['challenge']))
        self.assertEqual(self.login_error(response), LOCKED_MESSAGE)
        self.assertIsNone(self.session_uid())
        self.assertFalse(self.actor.active, 'A passkey must never re-activate a locked account.')

        self.actor._tp_set_account_lock(False, 'Synthetic passkey unlock')
        self._fresh_browser()
        response = self.post_passkey_login(authenticator.assertion(self.start_auth()['challenge']))
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.session_uid(), self.actor.id)

    @mute_logger('odoo.addons.tp_web_login.models.res_users')
    def test_single_session_is_replaced_only_after_successful_passkey(self):
        authenticator = self._registered()
        self.url_open('/web/session/authenticate', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'db': get_db_name(), 'login': self.actor.login, 'password': self.password},
        })
        old_sid = self.opener.cookies.get('session_id')
        self.assertEqual(self.session_uid(), self.actor.id)

        self.opener.cookies.clear()
        failed = authenticator.assertion(self.start_auth()['challenge'], user_verified=False)
        self._assert_rejected(self.post_passkey_login(failed), 'verification')
        self.opener.cookies.clear()
        self.opener.cookies.set('session_id', old_sid)
        self.assertEqual(self.session_uid(), self.actor.id, 'A failed passkey must not end the active session.')

        self.opener.cookies.clear()
        self.assertEqual(self.post_passkey_login(authenticator.assertion(self.start_auth()['challenge'])).status_code, 303)
        new_sid = self.opener.cookies.get('session_id')
        self.assertNotEqual(new_sid, old_sid)
        self.assertEqual(self.session_uid(), self.actor.id)
        self.opener.cookies.clear()
        self.opener.cookies.set('session_id', old_sid)
        check = self.session_check()
        self.assertEqual(check['error']['data']['context']['tp_session_reason'], 'session_replaced')

    @mute_logger('odoo.addons.tp_web_login.models.identitycheck')
    def test_registration_errors_are_vietnamese_and_owner_is_session_user(self):
        self.authenticate(self.actor.login, self.password)
        authenticator = self.new_authenticator(self.actor)
        error = self.make_key({})['error']['data']
        self.assertEqual(error['message'], PASSKEY_REGISTRATION_MESSAGES['missing'])

        options = self.registration_options(self.password)
        registration = authenticator.register(options['challenge'], origin=OLD_ORIGIN)
        self.assertEqual(self.make_key(registration)['error']['data']['message'], PASSKEY_REGISTRATION_MESSAGES['origin'])

        options = self.registration_options(self.password)
        registration = authenticator.register(options['challenge'], user_verified=False)
        self.assertEqual(self.make_key(registration)['error']['data']['message'],
                         PASSKEY_REGISTRATION_MESSAGES['verification'])

        options = self.registration_options(self.password)
        broken = dict(authenticator.register(options['challenge']), response={'clientDataJSON': 'e30'})
        self.assertEqual(self.make_key(broken)['error']['data']['message'], PASSKEY_REGISTRATION_MESSAGES['rejected'])
        self.assertFalse(self.actor.auth_passkey_key_ids)

        # The client cannot pick the owner: native make_key always writes on the session user.
        options = self.registration_options(self.password)
        response = self.make_key(authenticator.register(options['challenge']),
                                 default_create_uid=self.other.id, create_uid=self.other.id)
        self.assertIs(response.get('result'), True, response.get('error'))
        self.assertEqual(self._key(authenticator).create_uid, self.actor)
        self.assertFalse(self.other.auth_passkey_key_ids)

        # A used registration challenge cannot be replayed (native single-use challenge).
        replay = self.new_authenticator(self.actor).register(options['challenge'])
        self.assertEqual(self.make_key(replay)['error']['data']['message'], PASSKEY_REGISTRATION_MESSAGES['challenge'])
        self.assertEqual(len(self.actor.auth_passkey_key_ids), 1)

    @mute_logger('odoo.addons.tp_web_login.models.identitycheck')
    def test_passkey_identity_check_rejects_wrong_key_in_vietnamese(self):
        authenticator = self._registered()
        self.assertEqual(self.post_passkey_login(authenticator.assertion(self.start_auth()['challenge'])).status_code, 303)
        key = self._key(authenticator)
        count = key.sign_count
        wizard = self.rpc_result('res.users', 'tp_security_action', 'passkey_rename', key.id)
        self.assertEqual(wizard['res_model'], 'res.users.identitycheck')
        for assertion in (
            authenticator.assertion(self.start_auth()['challenge'], bad_signature=True),
            SoftAuthenticator('tpone.tadic.vn', 'https://tpone.tadic.vn').assertion(self.start_auth()['challenge']),
        ):
            error = self.rpc_error('res.users.identitycheck', 'run_check', [wizard['res_id']],
                                   context={'password': json.dumps(assertion)})
            self.assertEqual(error['name'], 'odoo.exceptions.UserError')
            self.assertEqual(error['message'], PASSKEY_IDENTITY_MESSAGE)
        self.assertEqual(key.sign_count, count)

    def test_client_event_accepts_only_whitelisted_enums(self):
        def event(**params):
            return self.url_open('/tp_web_login/passkey/client-event', json={
                'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': params,
            }).json()['result']

        with self.assertLogs('odoo.addons.tp_web_login.controllers.passkey', 'INFO') as logs:
            self.assertIs(event(phase='login', kind='not_allowed', name='NotAllowedError', code='x y'), True)
        self.assertIn('kind=not_allowed name=NotAllowedError code=-', logs.output[0])
        self.assertIs(event(phase='login', kind='<script>'), False)
        self.assertIs(event(phase='admin', kind='unknown'), False)
