"""Synthetic regression cases for peer-admin identity protection and independent locks."""
import json
import os
import subprocess
from pathlib import Path

from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import HttpCase, get_db_name, tagged

from .test_delegation import DelegationCase


@tagged('post_install', '-at_install', 'tp_admin_account_policy')
class TestAdminAccountPolicy(DelegationCase):
    def setUp(self):
        super().setUp()
        self.grant(self.users[0])
        self.grant(self.users[1])
        self.actor_user, self.peer, self.normal = self.users
        self.peer_employee = self.employees[1]

    def denied(self, operation):
        with self.assertRaises((AccessError, UserError)), self.env.cr.savepoint():
            operation()

    def test_original_lock_unlock_preserves_ledger_and_invalidates_sessions(self):
        peer = self.peer.with_user(self.admin)
        ledger = self.env['tp.admin.delegation'].search([
            ('user_id', '=', peer.id), ('state', '=', 'active')])
        before = ledger.read()
        groups = peer.group_ids
        token = peer._compute_session_token('synthetic-account-policy-session')
        employee = self.peer_employee.with_user(self.admin)
        self.assertTrue(employee.tp_can_manage_account)
        wizard = self.env['tp.hr.account.wizard'].with_user(self.admin).create({
            'employee_id': employee.id, 'expected_user_id': peer.id,
            'reason': 'Synthetic independent lock regression',
        })
        self.assertTrue(wizard.is_admin)
        wizard.action_lock()
        self.assertFalse(peer.active)
        self.assertTrue(peer.tp_hr_locked)
        self.assertEqual(employee.tp_account_status, 'disabled')
        self.assertNotEqual(peer._compute_session_token('synthetic-account-policy-session'), token)
        self.assertEqual(ledger.read(), before)
        self.assertEqual(peer.group_ids, groups)
        self.assertTrue(peer._tp_has_live_admin_grant())
        wizard.action_unlock()
        self.assertTrue(peer.active)
        self.assertFalse(peer.tp_hr_locked)
        self.assertEqual(employee.tp_account_status, 'active')
        self.assertEqual(ledger.read(), before)
        self.assertTrue(peer._tp_is_granted_admin())
        self.assertNotEqual(peer._compute_session_token('synthetic-account-policy-session'), token)
        audits = self.env['tp.hr.employee.audit'].search([
            ('account_ref', '=', peer.id), ('action', 'in', ['account_lock', 'account_unlock'])], order='id')
        self.assertEqual(audits.mapped('action'), ['account_lock', 'account_unlock'])
        for entry in audits:
            self.assertEqual(entry.actor_id, self.admin)
            self.assertEqual(entry.reason, 'Synthetic independent lock regression')
            self.assertEqual(entry.employee_ref, employee.id)
            self.assertEqual(entry.snapshot['after']['tp_hr_locked'], entry.action == 'account_lock')
            self.assertEqual(entry.snapshot['after']['active'], entry.action == 'account_unlock')
            self.assertGreater(entry.snapshot['after']['tp_lock_revision'], entry.snapshot['before']['tp_lock_revision'])
            self.assertNotIn('password', json.dumps(entry.snapshot))
            self.assertNotIn('token', json.dumps(entry.snapshot))

    def test_peer_all_account_fields_sudo_forged_context_and_inactive_target(self):
        values = [
            {'name': 'Forbidden peer name'}, {'signature': 'Forbidden signature'},
            {'email': 'peer@example.invalid'}, {'phone': '000'}, {'lang': 'en_US'},
            {'active': False}, {'login': 'forbidden.peer.login'}, {'password': 'Never-log-me-2026!'},
            {'partner_id': self.normal.partner_id.id},
            {'group_ids': [Command.link(self.env.ref('project.group_project_user').id)]},
        ]
        for locked in (False, True):
            if locked:
                self.peer.with_user(self.admin)._tp_set_account_lock(True, 'Synthetic inactive protection')
            for sudo in (False, True):
                peer = self.peer.with_user(self.actor_user).with_context(
                    active_test=False, _tp_admin_provision=True, _tp_admin_migrate=True,
                    _tp_personal_account=True, uid=self.admin.id)
                if sudo:
                    peer = peer.sudo()
                for vals in values:
                    with self.subTest(locked=locked, sudo=sudo, fields=list(vals)):
                        self.denied(lambda: peer.write(vals))
                self.denied(peer.unlink)
                self.denied(lambda: peer._tp_set_account_lock(not locked, 'Forbidden peer lock'))
                self.denied(peer.action_reset_password)
            self.assertTrue(self.peer._tp_has_live_admin_grant())

    def test_peer_profile_partner_resource_version_and_relink_are_protected(self):
        for actor, target, employee in (
            (self.actor_user, self.peer, self.peer_employee),
            (self.peer, self.actor_user, self.employees[0]),
        ):
            records = [
                (employee, {'name': 'Forbidden identity'}),
                (employee, {'mobile_phone': '000'}),
                (employee, {'work_email': 'forbidden@example.invalid'}),
                (employee, {'department_id': self.departments[2].id}),
                (employee, {'job_title': 'Forbidden title'}),
                (employee, {'active': False}), (employee, {'user_id': self.normal.id}),
                (target.partner_id, {'name': 'Forbidden contact'}),
                (target.partner_id, {'email': 'forbidden@example.invalid'}),
                (employee.resource_id, {'name': 'Forbidden resource'}),
                (employee.resource_id, {'user_id': self.normal.id}),
                (employee.current_version_id, {'job_title': 'Forbidden version'}),
                (employee.current_version_id, {'employee_id': self.employees[2].id}),
            ]
            for record, vals in records:
                with self.subTest(model=record._name, fields=list(vals), actor=actor.id):
                    self.denied(lambda: record.with_user(actor).sudo().with_context(
                        _tp_profile=True, _tp_personal_account=True).write(vals))
            for record in (employee, target.partner_id, employee.resource_id, employee.current_version_id):
                self.denied(record.with_user(actor).sudo().unlink)
            self.denied(lambda: self.employees[2].with_user(actor).sudo().write({'user_id': target.id}))

    def test_bulk_rejected_before_any_normal_record_write(self):
        for records, vals, field in (
            (self.normal | self.peer, {'signature': 'Forbidden mixed batch'}, 'signature'),
            (self.employees[2] | self.peer_employee, {'mobile_phone': '000'}, 'mobile_phone'),
            (self.normal.partner_id | self.peer.partner_id, {'phone': '000'}, 'phone'),
            (self.employees[2].resource_id | self.peer_employee.resource_id, {'name': 'Forbidden batch'}, 'name'),
        ):
            before = records.mapped(field)
            # Catch inside the transaction: a guard must inspect the whole batch before writing.
            with self.assertRaises((AccessError, UserError)):
                records.with_user(self.actor_user).sudo().write(vals)
            records.invalidate_recordset([field])
            self.assertEqual(records.mapped(field), before)

    def test_peer_wizard_and_direct_employee_actions_enforce_same_policy(self):
        for locked in (False, True):
            if locked:
                self.peer.with_user(self.admin)._tp_set_account_lock(True, 'Synthetic wizard locked peer')
            employee = self.peer_employee.with_user(self.actor_user)
            self.assertFalse(employee.tp_can_manage_account)
            self.assertFalse(employee.tp_can_change_login)
            self.denied(employee.action_open_change_login_dialog)
            self.denied(lambda: employee.action_change_user_login('forbidden.peer.rename'))
            # A guessed transient ID / direct RPC must still check the live target.
            wizard = self.env['tp.hr.account.wizard'].with_user(self.admin).create({
                'employee_id': employee.id, 'expected_user_id': self.peer.id,
                'reason': 'Forbidden peer wizard', 'expected_login': self.peer.login,
            }).with_user(self.actor_user).sudo()
            self.assertFalse(wizard.is_admin)
            for operation in (wizard.action_lock, wizard.action_unlock, wizard.action_reset_password,
                              lambda: wizard.action_change_login('forbidden.peer.rename')):
                self.denied(operation)

    def test_normal_management_and_personal_profile_remain_available(self):
        normal = self.normal.with_user(self.actor_user)
        normal.write({'signature': 'Normal staff remains managed'})
        self.employees[2].with_user(self.actor_user).write({'mobile_phone': '0912345000'})
        normal._tp_set_account_lock(True, 'Synthetic normal lock')
        normal._tp_set_account_lock(False, 'Synthetic normal unlock')
        saved = self.env['res.users'].with_user(self.actor_user).tp_save_my_profile({'mobile_phone': '0912345999'})
        self.assertEqual(saved['values']['mobile_phone'], '0912345999')
        for target, operation in ((self.normal, 'grant'), (self.peer, 'revoke')):
            self.denied(lambda: self.env['tp.admin.delegation'].with_user(self.actor_user).sudo()._change(
                target, self.company, operation, 'Forbidden peer provision'))

    def test_own_record_personal_fields_editable_in_place(self):
        """HR-SELF-EDIT-001: a granted admin edits their own personal data from the employee list form."""
        own = self.employees[0].with_user(self.actor_user)
        self.assertTrue(own.tp_account_profile_readonly)
        own.write({'private_phone': '0912000111', 'private_email': 'synthetic.self@example.invalid',
                   'emergency_contact': 'Synthetic Contact', 'marital': 'married'})
        self.assertEqual((self.employees[0].private_phone, self.employees[0].marital), ('0912000111', 'married'))
        # Fields Odoo stores on hr.version (address, ID, sex) save too, from the form and from "Thông tin cá nhân".
        own.write({'private_street': 'Synthetic Street 1', 'identification_id': 'SYN000111', 'sex': 'female'})
        self.env['res.users'].with_user(self.actor_user).tp_save_my_profile({'private_city': 'Synthetic City'})
        self.assertEqual((self.employees[0].private_street, self.employees[0].identification_id,
                          self.employees[0].private_city), ('Synthetic Street 1', 'SYN000111', 'Synthetic City'))
        self.assertEqual(self.employees[0].version_id.last_modified_uid, self.actor_user)
        for vals in ({'name': 'Forbidden self rename'}, {'job_title': 'Forbidden self title'},
                     {'department_id': self.departments[1].id}, {'barcode': 'SYN-SELF-001'}):
            self.denied(lambda: own.write(vals))
        version = self.employees[0].version_id.with_user(self.actor_user)
        self.denied(lambda: version.write({'marital': 'single', 'last_modified_uid': self.admin.id}))
        self.denied(lambda: version.write({'wage': 1}))
        self.assertEqual(self.employees[0].marital, 'married')
        self.assertEqual(self.employees[0].name, self.users[0].name)
        # The peer's record stays fully protected, personal fields included.
        self.denied(lambda: self.peer_employee.with_user(self.actor_user).write({'private_phone': '0912000222'}))

        arch = etree.fromstring(own.get_views([(False, 'form')])['views']['form']['arch'])
        fields_by_name = {node.get('name'): node for node in arch.xpath('//field[not(ancestor::field)]')}
        for name in ('private_phone', 'private_email', 'marital'):
            self.assertIn('tp_account_profile_readonly and user_id != uid', fields_by_name[name].get('readonly'))
        for name in ('name', 'job_title', 'department_id'):
            readonly = fields_by_name[name].get('readonly')
            self.assertTrue(readonly.endswith(' or tp_account_profile_readonly'), readonly)
        notice = arch.xpath("//div[contains(@class, 'o_tp_own_profile_notice')]")
        self.assertEqual(notice[0].get('invisible'), 'not tp_account_profile_readonly or user_id != uid')

    def test_original_can_lock_another_original_but_not_self_or_system(self):
        other = self.normal.with_user(self.admin)
        other.write({'group_ids': [
            Command.link(self.env.ref('base.group_system').id),
            Command.link(self.env.ref('tp_admin_delegation.group_original_admin').id),
        ]})
        self.assertTrue(other._tp_is_original_admin())
        self.assertTrue(self.employees[2].with_user(self.admin).tp_can_manage_account)
        other._tp_set_account_lock(True, 'Synthetic second original lock')
        self.assertTrue(other.tp_hr_locked)
        self.assertTrue(self.admin._tp_is_original_admin())
        other._tp_set_account_lock(False, 'Synthetic second original unlock')
        self.assertTrue(other._tp_is_original_admin())
        self.denied(lambda: other.with_user(self.actor_user).sudo().write({'name': 'Forbidden original'}))
        for target in (self.admin, self.env.ref('base.user_root'), self.env.ref('base.public_user')):
            self.denied(lambda: target.with_user(self.admin)._tp_set_account_lock(True, 'Forbidden system/self lock'))


@tagged('post_install', '-at_install', 'tp_admin_account_policy')
class TestAdminAccountLockHttp(HttpCase):
    def test_browser_original_lock_unlock_and_peer_readonly_desktop_mobile(self):
        admin = self.env.ref('base.user_admin')
        self.env['tp.admin.delegation']._migrate_admin_full_001()
        users = self.env['res.users'].with_context(no_reset_password=True).create([
            {'name': 'Synthetic Policy Browser ' + name, 'login': 'synthetic.policy.browser.' + name,
             'company_id': self.env.company.id, 'company_ids': [Command.set(self.env.company.ids)],
             'group_ids': [Command.set(self.env.ref('base.group_user').ids)]}
            for name in ('original', 'peer', 'target', 'normal')])
        users[0].with_user(admin).write({'group_ids': [Command.link(
            self.env.ref('tp_admin_delegation.group_original_admin').id),
            Command.link(self.env.ref('base.group_system').id),
            Command.link(self.env.ref('hr.group_hr_manager').id)]})
        employees = self.env['hr.employee'].create([
            {'name': user.name, 'user_id': user.id} for user in users])
        for user in users[1:3]:
            self.env['tp.admin.delegation'].with_user(admin)._change(
                user, self.env.company, 'grant', 'Synthetic browser policy')
        root = Path(__file__).resolve().parents[3]
        while not (root / 'scripts/tests/test_admin_account_policy.cjs').is_file():
            if root == root.parent:
                self.fail('Cannot locate admin policy browser test runner')
            root = root.parent
        output = root / '.local/admin-account-policy/browser'
        output.mkdir(parents=True, exist_ok=True)
        fixture_path = output / 'fixture-private.json'
        for mode, actor in (('original', users[0]), ('peer', users[1])):
            self.authenticate(actor.login, 'synthetic', session_extra={'context': {'lang': 'vi_VN'}})
            try:
                with self.allow_requests():
                    fixture_path.write_text(json.dumps({
                        'base': self.base_url(), 'mode': mode, 'employeeId': employees[2].id,
                        'targetUserId': users[2].id,
                        'employeeName': employees[2].name, 'originalEmployeeId': employees[0].id,
                        'normalEmployeeId': employees[3].id, 'ownEmployeeId': employees[1].id,
                        'output': str(output), 'cookies': [
                            {'name': 'session_id', 'value': self.session.sid, 'url': self.base_url(), 'httpOnly': True},
                            {'name': 'test_request_key', 'value': self.http_request_key, 'url': self.base_url()},
                        ],
                    }), encoding='utf-8')
                    result = subprocess.run(['node', str(root / 'scripts/tests/test_admin_account_policy.cjs')],
                        env={**os.environ, 'TP_ADMIN_POLICY_FIXTURE': str(fixture_path)},
                        capture_output=True, text=True, timeout=240, check=False)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            finally:
                fixture_path.unlink(missing_ok=True)
        # Peer mode saved the granted admin's own phone from the native form (desktop, then mobile).
        employees[1].invalidate_recordset()
        self.assertEqual(employees[1].private_phone, '0900000102')
        self.assertEqual(employees[1].name, users[1].name)
        users[2].invalidate_recordset()
        self.assertTrue(users[2].active)
        self.assertTrue(users[2]._tp_has_live_admin_grant())

    def test_locked_delegate_rejects_old_session_and_new_login_then_unlocks(self):
        password = 'Synthetic-Admin-Lock-2026!'
        admin = self.env.ref('base.user_admin')
        self.env['tp.admin.delegation']._migrate_admin_full_001()
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic Admin Lock HTTP', 'login': 'synthetic.admin.lock.http',
            'password': password, 'company_id': self.env.company.id,
            'company_ids': [Command.set(self.env.company.ids)],
            'group_ids': [Command.set(self.env.ref('base.group_user').ids)],
        })
        self.env['hr.employee'].create({'name': user.name, 'user_id': user.id})
        self.env['tp.admin.delegation'].with_user(admin)._change(user, self.env.company, 'grant', 'Synthetic HTTP')

        def rpc(path, params):
            return self.url_open(path, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'params': params}),
                                 headers={'Content-Type': 'application/json'}).json()

        def login():
            return rpc('/web/session/authenticate', {'db': get_db_name(), 'login': user.login, 'password': password})

        self.assertEqual(login()['result']['uid'], user.id)
        user.with_user(admin)._tp_set_account_lock(True, 'Synthetic HTTP lock')
        response = rpc('/web/dataset/call_kw/res.users/read', {
            'model': 'res.users', 'method': 'read', 'args': [[user.id], ['name']], 'kwargs': {}})
        self.assertIn('error', response)
        response = login()
        self.assertIn('error', response)
        self.assertIn('Tài khoản đã bị khóa', json.dumps(response, ensure_ascii=False))
        user.with_user(admin)._tp_set_account_lock(False, 'Synthetic HTTP unlock')
        self.assertEqual(login()['result']['uid'], user.id)
        self.assertTrue(user._tp_has_live_admin_grant())
