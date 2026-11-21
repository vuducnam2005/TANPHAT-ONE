"""Passkey register -> login -> revoke for the three account roles (PASSKEY-001).

Synthetic identities only: base.user_admin and real accounts are never given a
key, a password or a session. The software authenticator proves the native
WebAuthn flow, not a real biometric device.
"""
import secrets

from odoo import Command
from odoo.tests import HttpCase, tagged

from odoo.addons.tp_web_login.models.res_users import PASSKEY_MESSAGES
from odoo.addons.tp_web_login.tests.passkey_authenticator import PasskeyHttpMixin

FOREIGN_SECURITY_MESSAGE = 'Không có quyền thao tác dữ liệu bảo mật này.'


@tagged('post_install', '-at_install', 'tp_passkey', 'tp_account_security')
class TestPasskeyRoles(PasskeyHttpMixin, HttpCase):
    def setUp(self):
        super().setUp()
        self.use_production_domain()
        self.env['ir.config_parameter'].sudo().set_str('base.login_cooldown_after', '0')
        self.clear_login_failures()
        self.addCleanup(self.clear_login_failures)
        admin = self.env.ref('base.user_admin')
        self.env['tp.admin.delegation']._migrate_admin_full_001()
        self.password = secrets.token_urlsafe(18)
        company = self.env.company
        self.employee, self.delegate, self.peer, self.original = self.env['res.users'].with_context(
            no_reset_password=True,
        ).create([{
            'name': f'Synthetic Passkey {name}', 'login': f'passkey001.role.{name}',
            'password': self.password, 'lang': 'vi_VN',
            'company_id': company.id, 'company_ids': [Command.set(company.ids)],
            'group_ids': [Command.set(self.env.ref('base.group_user').ids)],
        } for name in ('employee', 'delegate', 'peer', 'original')])
        self.original.with_user(admin).write({'group_ids': [
            Command.link(self.env.ref('base.group_system').id),
            Command.link(self.env.ref('tp_admin_delegation.group_original_admin').id),
        ]})
        for user in (self.delegate, self.peer):
            self.env['tp.admin.delegation'].with_user(admin)._change(
                user, company, 'grant', 'Synthetic passkey role check')
        self.expected_roles = {
            self.employee: 'employee', self.delegate: 'granted_admin',
            self.peer: 'granted_admin', self.original: 'original_admin',
        }

    def _groups(self, user):
        return user.sudo().with_context(active_test=False).all_group_ids

    def _register(self, user):
        self.authenticate(user.login, self.password)
        authenticator = self.register_passkey(user, self.password, name=f'Khóa {user.login}')
        self.opener.cookies.clear()
        key = user.sudo().auth_passkey_key_ids
        self.assertEqual(len(key), 1)
        self.assertEqual(key.create_uid, user, 'The key must belong to the session user.')
        return authenticator, key

    def _login(self, authenticator):
        self.opener.cookies.clear()
        return self.post_passkey_login(authenticator.assertion(self.start_auth()['challenge']))

    def test_each_role_registers_logs_in_with_same_identity_and_revokes_own_key(self):
        for user, role in self.expected_roles.items():
            if user == self.peer:
                continue
            with self.subTest(role=role):
                groups_before = self._groups(user)
                authenticator, key = self._register(user)

                response = self._login(authenticator)
                self.assertEqual(response.status_code, 303, 'A valid passkey must finish the native login.')
                payload = self.rpc_result('res.users', 'tp_my_security')
                self.assertEqual((payload['user_id'], payload['role_code']), (user.id, role))
                self.assertEqual([row['id'] for row in payload['passkeys']], key.ids)
                self.assertEqual(self.session_uid(), user.id)
                self.assertEqual(self._groups(user), groups_before, 'Passkey login must not change rights.')

                # Revoke from the account page; the identity check accepts this same key.
                self.expire_identity_check()
                response = self.security_action('passkey_remove', key.id, authenticator=authenticator)
                self.assertNotIn('error', response, response.get('error'))
                self.assertFalse(key.exists())

                response = self._login(authenticator)
                self.assertEqual(self.login_error(response), PASSKEY_MESSAGES['unknown'])
                self.assertIsNone(self.session_uid(), 'A revoked key must not open a session.')
                self.assertEqual(self._groups(user), groups_before)

    def test_delegate_cannot_touch_original_or_peer_keys(self):
        keys = {}
        for user in (self.original, self.peer, self.employee):
            keys[user] = self._register(user)[1]
        _authenticator, own_key = self._register(self.delegate)
        self.authenticate(self.delegate.login, self.password)
        for owner, key in keys.items():
            with self.subTest(owner=self.expected_roles[owner]):
                # The account page only ever acts on the session user's own keys.
                for operation in ('passkey_remove', 'passkey_rename'):
                    response = self.security_action(operation, key.id, password=self.password)
                    self.assertEqual(response['error']['data']['message'], FOREIGN_SECURITY_MESSAGE)
                if owner == self.employee:
                    continue  # Native admins may still revoke an employee key from the user form.
                for method, args in (('unlink', ()), ('write', ({'name': 'Khóa bị đổi tên'},)),
                                     ('write', ({'create_uid': self.delegate.id},))):
                    error = self.rpc_error('auth.passkey.key', method, key.ids, *args)
                    self.assertEqual(error['name'], 'odoo.exceptions.AccessError')
                error = self.rpc_error('res.users', 'write', owner.ids,
                                       {'auth_passkey_key_ids': [Command.unlink(key.id)]})
                self.assertEqual(error['name'], 'odoo.exceptions.AccessError')
        for owner, key in keys.items():
            self.assertTrue(key.exists())
            self.assertEqual((key.create_uid, key.name), (owner, f'Khóa {owner.login}'))

        # The delegate cannot hand their own key to another admin either; the
        # native ORM never lets a client set create_uid, so ownership stays put.
        error = self.rpc_error('auth.passkey.key', 'write', own_key.ids, {'create_uid': self.peer.id})
        self.assertEqual(error['name'], 'odoo.exceptions.AccessError')
        self.rpc('auth.passkey.key', 'write', own_key.ids, {'create_uid': self.employee.id})
        self.assertEqual(own_key.create_uid, self.delegate)
