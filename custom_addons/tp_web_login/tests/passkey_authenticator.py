"""Test-only software authenticator and HTTP helpers for passkey flows.

The authenticator builds genuine ES256 attestation ("none") and assertion
payloads, so the native py_webauthn checks (challenge, origin, RP ID hash,
user presence/verification flags, sign counter and signature) all run
unmodified on the server. It proves the software flow only, never a real
biometric device. Keys live in memory for one test and are never logged.
"""
import hashlib
import json
import os
import struct

import cbor2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from lxml import html

from odoo.http.session import session_store

from odoo.addons.auth_passkey._vendor.webauthn.helpers import bytes_to_base64url

FLAG_UP, FLAG_UV, FLAG_AT = 0x01, 0x04, 0x40
PRODUCTION_ORIGIN = 'https://tpone.tadic.vn'


def b64(data):
    return bytes_to_base64url(data)


class SoftAuthenticator:
    """One discoverable ES256 credential bound to ``rp_id``/``origin``."""

    def __init__(self, rp_id, origin, user_handle=b''):
        self.rp_id = rp_id
        self.origin = origin
        self.user_handle = user_handle
        self._private_key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = os.urandom(32)
        self.sign_count = 0

    @property
    def id(self):
        return b64(self.credential_id)

    def _cose_public_key(self):
        numbers = self._private_key.public_key().public_numbers()
        return cbor2.dumps({
            1: 2, 3: -7, -1: 1,
            -2: numbers.x.to_bytes(32, 'big'),
            -3: numbers.y.to_bytes(32, 'big'),
        })

    def _client_data(self, ceremony, challenge, origin):
        return json.dumps({
            'type': ceremony, 'challenge': challenge,
            'origin': origin or self.origin, 'crossOrigin': False,
        }, separators=(',', ':')).encode()

    def _authenticator_data(self, flags, rp_id, count, attested=b''):
        rp_hash = hashlib.sha256((rp_id or self.rp_id).encode()).digest()
        return rp_hash + bytes([flags]) + struct.pack('>I', count) + attested

    def register(self, challenge, *, origin=None, rp_id=None, user_verified=True):
        flags = FLAG_UP | FLAG_AT | (FLAG_UV if user_verified else 0)
        attested = (bytes(16) + struct.pack('>H', len(self.credential_id))
                    + self.credential_id + self._cose_public_key())
        auth_data = self._authenticator_data(flags, rp_id, 0, attested)
        attestation = cbor2.dumps({'fmt': 'none', 'attStmt': {}, 'authData': auth_data})
        return {
            'id': self.id, 'rawId': self.id, 'type': 'public-key',
            'response': {
                'attestationObject': b64(attestation),
                'clientDataJSON': b64(self._client_data('webauthn.create', challenge, origin)),
                'transports': ['internal'],
            },
            'clientExtensionResults': {}, 'authenticatorAttachment': 'platform',
        }

    def assertion(self, challenge, *, origin=None, rp_id=None, user_verified=True,
                  count=None, bad_signature=False):
        """Sign ``challenge``; by default the counter moves forward like real hardware."""
        if count is None:
            self.sign_count += 1
            count = self.sign_count
        flags = FLAG_UP | (FLAG_UV if user_verified else 0)
        auth_data = self._authenticator_data(flags, rp_id, count)
        client_data = self._client_data('webauthn.get', challenge, origin)
        signature = self._private_key.sign(
            auth_data + hashlib.sha256(client_data).digest(), ec.ECDSA(hashes.SHA256()))
        if bad_signature:
            signature = signature[:-1] + bytes([signature[-1] ^ 0x01])
        return {
            'id': self.id, 'rawId': self.id, 'type': 'public-key',
            'response': {
                'authenticatorData': b64(auth_data),
                'clientDataJSON': b64(client_data),
                'signature': b64(signature),
                'userHandle': b64(self.user_handle),
            },
            'clientExtensionResults': {}, 'authenticatorAttachment': 'platform',
        }


class PasskeyHttpMixin:
    """Drives the native endpoints exactly like the browser code does (HttpCase only)."""

    def use_production_domain(self):
        # Same RP ID / origin as https://tpone.tadic.vn; frozen so a system-user
        # login over the test server address cannot rewrite it.
        parameters = self.env['ir.config_parameter'].sudo()
        parameters.set_str('web.base.url', PRODUCTION_ORIGIN)
        parameters.set_bool('web.base.url.freeze', True)

    def new_authenticator(self, user):
        return SoftAuthenticator('tpone.tadic.vn', PRODUCTION_ORIGIN, str(user.id).encode())

    def rpc(self, model, method, *args, **kwargs):
        return self.url_open('/web/dataset/call_kw', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'model': model, 'method': method, 'args': list(args), 'kwargs': kwargs},
        }).json()

    def rpc_result(self, model, method, *args, **kwargs):
        response = self.rpc(model, method, *args, **kwargs)
        self.assertNotIn('error', response, response.get('error'))
        return response['result']

    def rpc_error(self, model, method, *args, **kwargs):
        response = self.rpc(model, method, *args, **kwargs)
        self.assertNotIn('result', response)
        return response['error']['data']

    def start_auth(self):
        response = self.url_open('/auth/passkey/start-auth', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': {},
        }).json()
        return response['result']

    def login_token(self):
        page = html.fromstring(self.url_open('/web/login').content)
        return page.xpath("//input[@name='csrf_token']/@value")[0]

    def post_passkey_login(self, assertion, **extra):
        data = {
            'type': 'webauthn',
            'webauthn_response': assertion if isinstance(assertion, str) else json.dumps(assertion),
            'csrf_token': self.login_token(), 'password': '', 'login': '',
        }
        data.update(extra)
        return self.url_open('/web/login', data=data, allow_redirects=False)

    def login_error(self, response):
        self.assertEqual(response.status_code, 200, 'A rejected passkey must re-render the login page.')
        alerts = html.fromstring(response.content).xpath(
            "//form[contains(@class,'oe_login_form')]//*[contains(@class,'alert-danger')]")
        self.assertEqual(len(alerts), 1, 'Exactly one Vietnamese error must be shown in the login form.')
        return ' '.join(alerts[0].text_content().split())

    def session_check(self):
        """One authenticated read/write JSON-RPC call with the current cookie.

        HttpCase cannot run the single-session winner check from readonly
        routes (e.g. /web/session/check), so a read/write method is used."""
        return self.rpc('res.users', 'tp_my_security')

    def session_uid(self):
        if 'error' in self.session_check():
            return None
        return session_store().get(self.opener.cookies.get('session_id'), keep_sid=True).uid

    def clear_login_failures(self):
        failures = getattr(self.registry, '_login_failures', None)
        if failures is not None:
            failures.clear()

    def expire_identity_check(self):
        """Force the next protected action to ask again (identity window is per session)."""
        store = session_store()
        session = store.get(self.opener.cookies.get('session_id'), keep_sid=True)
        session['identity-check-last'] = 0
        store.save(session)

    def security_action(self, operation, *args, password=None, authenticator=None):
        """``tp_security_action`` as the account page calls it; if the native identity
        check is asked, pass it by password ("Dùng mật khẩu") or by passkey."""
        response = self.rpc('res.users', 'tp_security_action', operation, *args)
        action = response.get('result')
        if isinstance(action, dict) and action.get('res_model') == 'res.users.identitycheck':
            wizard = [action['res_id']]
            if authenticator:
                proof = json.dumps(authenticator.assertion(self.start_auth()['challenge']))
            else:
                self.rpc_result('res.users.identitycheck', 'action_use_password', wizard)
                proof = password
            response = self.rpc('res.users.identitycheck', 'run_check', wizard, context={'password': proof})
        return response

    def registration_options(self, password):
        response = self.security_action('passkey_create', password=password)
        self.assertNotIn('error', response, response.get('error'))
        options = response['result']['context']['registration']
        self.assertEqual(options['rp']['id'], 'tpone.tadic.vn')
        self.assertEqual(options['authenticatorSelection']['userVerification'], 'required')
        self.assertEqual(options['authenticatorSelection']['residentKey'], 'required')
        return options

    def make_key(self, registration, name='Máy thử nghiệm', **rpc_context):
        wizard_id = self.rpc_result('auth.passkey.key.create', 'create', {'name': name})
        return self.rpc('auth.passkey.key.create', 'make_key', [wizard_id], registration, context=rpc_context)

    def register_passkey(self, user, password, name='Máy thử nghiệm', **rpc_context):
        """Identity check -> native registration options -> native make_key, in the user's session."""
        authenticator = self.new_authenticator(user)
        options = self.registration_options(password)
        response = self.make_key(authenticator.register(options['challenge']), name, **rpc_context)
        self.assertIs(response.get('result'), True, response.get('error'))
        return authenticator
