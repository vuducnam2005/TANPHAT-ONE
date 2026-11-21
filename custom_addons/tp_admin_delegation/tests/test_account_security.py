"""Security boundaries across real role types, using rolled-back synthetic identities."""
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .test_delegation import DelegationCase
from odoo.addons.base.models.res_device import ResSession
from odoo.addons.tp_web_login.models.account_security import AccountSecurity


@tagged('post_install', '-at_install', 'tp_account_security')
class TestAccountSecurity(DelegationCase):
    def setUp(self):
        super().setUp()
        self.grant(self.users[0])
        self.grant(self.users[1])
        self.actor_user, self.peer, self.normal = self.users

    def test_dashboard_always_uses_current_user_and_safe_fields(self):
        for user in (self.admin, self.actor_user, self.peer, self.normal):
            payload = self.env['res.users'].with_user(user).tp_my_security()
            self.assertEqual(payload['user_id'], user.id)
            self.assertEqual(payload['login'], user.login)
            self.assertEqual(self.env['res.users'].with_user(user).action_get()['tag'], 'tp_web_login.account_security')
            self.assertNotIn('password', payload)
            self.assertNotIn('totp_secret', payload)
            for row in payload['sessions']:
                self.assertNotIn('session_identifier', row)
            self.assertEqual(set(payload['keys'][0]) if payload['keys'] else set(),
                             {'id', 'name', 'created', 'expires', 'expired'} if payload['keys'] else set())

    def test_preferences_reject_identity_and_privilege_injection(self):
        for user in (self.actor_user, self.normal):
            service = self.env['res.users'].with_user(user)
            for vals in ({'user_id': self.peer.id}, {'group_ids': []}, {'password': 'not-a-real-secret'},
                         {'login': 'changed'}, {'totp_secret': 'no'}):
                with self.assertRaises(AccessError), self.env.cr.savepoint():
                    service.tp_save_my_preferences(vals)
            self.assertTrue(service.tp_save_my_preferences({'tz': 'Asia/Ho_Chi_Minh'}))

    def test_session_revoke_denies_peer_and_original_before_side_effect(self):
        for target in (self.peer, self.admin):
            log = self.env['res.device.log'].sudo().create({
                'user_id': target.id, 'session_identifier': 'synthetic-security-session-' + str(target.id),
                'ip_address': '127.0.0.1', 'user_agent': 'Synthetic security test',
                'first_activity': fields.Datetime.now(), 'last_activity': fields.Datetime.now(),
            })
            session = self.env['res.session'].browse(log.id)
            for sudo in (False, True):
                candidate = session.with_user(self.actor_user)
                if sudo:
                    candidate = candidate.sudo()
                with patch.object(ResSession, '_revoke') as native:
                    with self.assertRaises(AccessError), self.env.cr.savepoint():
                        candidate._revoke()
                    native.assert_not_called()
            with patch.object(ResSession, '_revoke', return_value=True) as native:
                session.with_user(self.admin)._revoke()
                native.assert_called_once()

    def test_employee_cannot_revoke_other_employee_and_own_session_is_allowed(self):
        with patch.object(ResSession, '_revoke', return_value=True) as native:
            self.normal.with_user(self.normal)._action_revoke_all_devices()
            native.assert_called_once()
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env['res.users'].with_user(self.normal).browse(self.peer.id)._action_revoke_all_devices()

    def test_self_service_action_rejects_cross_account_record_ids(self):
        # Bypass only the interactive identity decorator for this transaction test;
        # the protected method itself must reject the foreign record before native actions.
        action = AccountSecurity.tp_security_action.__wrapped__
        log = self.env['res.device.log'].sudo().create({
            'user_id': self.peer.id, 'session_identifier': 'synthetic-foreign-session',
            'ip_address': '127.0.0.1', 'user_agent': 'Synthetic',
            'first_activity': fields.Datetime.now(), 'last_activity': fields.Datetime.now(),
        })
        for user in (self.normal, self.actor_user, self.admin):
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                action(self.env['res.users'].with_user(user), 'session_revoke', log.id)

    def test_passkey_peer_unlink_write_and_ownership_change_blocked(self):
        key = self.env['auth.passkey.key'].sudo().create({
            'name': 'Synthetic peer passkey', 'credential_identifier': 'synthetic-not-an-authenticator',
            'create_uid': self.peer.id,
        })
        for sudo in (False, True):
            candidate = key.with_user(self.actor_user)
            if sudo:
                candidate = candidate.sudo()
            for operation in (candidate.unlink, lambda: candidate.write({'name': 'Forbidden'}),
                              lambda: candidate.write({'create_uid': self.actor_user.id})):
                with self.assertRaises(AccessError), self.env.cr.savepoint():
                    operation()

    def test_api_key_direct_unlink_cannot_bypass_peer_guard(self):
        keys = self.env['res.users.apikeys'].with_user(self.peer)
        keys._generate('rpc', 'Synthetic peer API key', fields.Datetime.now() + timedelta(days=1))
        record = keys.search([('user_id', '=', self.peer.id), ('name', '=', 'Synthetic peer API key')])
        for sudo in (False, True):
            candidate = record.with_user(self.actor_user)
            if sudo:
                candidate = candidate.sudo()
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                candidate.unlink()

    def test_filters_and_invalid_preferences(self):
        service = self.env['res.users'].with_user(self.normal)
        for args in ({'limit': 10000}, {'status': 'other-user'}, {'offset': -1}):
            with self.assertRaises(UserError):
                service.tp_my_security(**args)
        with self.assertRaises(UserError):
            service.tp_save_my_preferences({'image_1920': 'not-base64'})

    def test_delegate_native_totp_counter_is_self_only(self):
        # NO_ACCESS still forbids RPC writes; the native verified OTP flow writes in sudo.
        self.actor_user.with_user(self.actor_user).sudo().write({'totp_last_counter': 12345})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.peer.with_user(self.actor_user).sudo().write({'totp_last_counter': 12345})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.peer.with_user(self.actor_user).sudo().with_context(_tp_native_mfa=True).write({'totp_last_counter': 12345})
