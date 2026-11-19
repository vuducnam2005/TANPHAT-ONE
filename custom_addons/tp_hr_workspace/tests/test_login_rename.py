import json
import os
import subprocess
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from openpyxl import load_workbook

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import HttpCase, get_db_name, tagged

from .test_hr_workspace import BaseHrWorkspace


@tagged('post_install', '-at_install')
class TestEmployeeLoginRename(BaseHrWorkspace):
    def setUp(self):
        super().setUp()
        self.user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic Rename Account', 'login': 'rename.synthetic.before',
            'password': 'Synthetic-Rename-2026', 'company_id': self.company.id,
            'company_ids': [Command.set(self.company.ids)],
            'group_ids': [Command.set(self.env.ref('base.group_user').ids)],
        })
        self.employee = self.employees[0]
        self.employee.write({'user_id': self.user.id})
        self.operator = self.employee.with_user(self.admin).with_context(allowed_company_ids=self.company.ids)

    def snapshot(self):
        self.env.flush_all()
        self.env.cr.execute('SELECT password FROM res_users WHERE id=%s', [self.user.id])
        return (self.env.cr.fetchone()[0], self.user.id, self.user.partner_id.id,
                self.user.group_ids.ids, self.user.company_ids.ids,
                self.employee.resource_id.id, self.employee.department_id.id,
                self.employee.job_id.id, bytes(self.employee.image_1920 or b''), self.user.active)

    def test_rename_preserves_identity_password_permissions_and_export(self):
        before = self.snapshot()
        audit = self.env['tp.hr.employee.audit']
        self.assertTrue(self.operator.tp_can_change_login)
        self.assertFalse(self.employee.with_user(self.staff).tp_can_change_login)
        self.assertFalse(self.employee.with_user(self.hr).tp_can_change_login)
        action = self.operator.action_open_change_login_dialog()
        wizard = self.env['tp.hr.account.wizard'].with_user(self.admin).with_context(
            allowed_company_ids=self.company.ids).browse(action['params']['wizardId'])
        result = wizard.action_change_login('  Rename.Synthetic.After  ')
        self.assertEqual(result['user_id'], self.user.id)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.employee.tp_user_login, 'Rename.Synthetic.After')
        self.assertEqual(self.user.login, 'Rename.Synthetic.After')
        self.assertEqual(wizard.current_login, self.user.login)
        row = self.env['hr.employee'].with_user(self.admin).with_context(
            allowed_company_ids=self.company.ids).search_read([('id', '=', self.employee.id)], ['tp_user_login'])
        self.assertEqual(row[0]['tp_user_login'], self.user.login)
        entries = audit.search([('employee_ref', '=', self.employee.id), ('action', '=', 'login_change')])
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries.actor_id, self.admin)
        self.assertEqual(entries.snapshot['old_login'], 'rename.synthetic.before')
        self.assertEqual(entries.snapshot['new_login'], self.user.login)
        with self.assertRaises(AccessError):
            entries.write({'reason': 'tamper'})
        content = self.env['tp.hr.workspace'].with_user(self.admin).with_context(
            allowed_company_ids=self.company.ids)._build_xlsx(options={
                'domain': [('id', '=', self.employee.id)], 'scope': 'filtered'})
        workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
        values = [v for sheet in workbook for row in sheet.values for v in row]
        self.assertIn(self.user.login, values)
        self.assertNotIn('rename.synthetic.before', values)
        self.assertNotIn('Synthetic-Rename-2026', str(entries.snapshot))
        self.assertIn('login', self.user._get_session_token_fields())

    def test_original_admin_can_rename_granted_admin_but_other_actors_cannot(self):
        if 'tp.admin.delegation' not in self.env:
            self.skipTest('Admin delegation addon is not installed')
        delegation = self.env['tp.admin.delegation'].with_user(self.admin).with_context(
            allowed_company_ids=self.company.ids)
        delegation._change(self.user, self.company, 'grant', 'Synthetic login visibility regression')
        grant = delegation.search([('user_id', '=', self.user.id), ('state', '=', 'active')])
        delegation._change(self.staff, self.company, 'grant', 'Synthetic peer admin')
        before = self.snapshot()
        self.assertTrue(self.operator.tp_can_change_login)
        self.assertFalse(self.operator.tp_can_manage_account)
        with self.assertRaises(UserError):
            self.operator._tp_account_admin(existing=True)
        for actor in (self.staff, self.user, self.hr):
            self.assertFalse(self.operator.with_user(actor).tp_can_change_login)
            with self.assertRaises((AccessError, UserError)):
                self.operator.with_user(actor).action_change_user_login('rename.granted.forbidden')
            with self.assertRaises((AccessError, UserError)):
                self.user.with_user(actor).sudo().write({'login': 'rename.granted.sudo'})
        action = self.operator.action_open_change_login_dialog()
        wizard = self.env['tp.hr.account.wizard'].with_user(self.admin).with_context(
            allowed_company_ids=self.company.ids).browse(action['params']['wizardId'])
        self.assertTrue(wizard.can_change_login)
        self.assertFalse(wizard.is_admin)
        wizard.action_change_login('Rename.Granted.After')
        self.assertEqual(self.user.login, 'Rename.Granted.After')
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(grant.state, 'active')
        self.assertEqual(self.env['tp.hr.employee.audit'].search_count([
            ('employee_ref', '=', self.employee.id), ('action', '=', 'login_change')]), 1)

    def test_invalid_duplicate_archived_and_other_company_are_atomic(self):
        old = self.user.login
        duplicate = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic Archived Duplicate', 'login': 'rename.synthetic.taken',
            'company_id': self.other.id, 'company_ids': [Command.set(self.other.ids)], 'active': False,
        })
        for login in ['', '   ', 'has space', 'bad\x00login', 'bad\u200blogin', 'x' * 255, duplicate.login, old]:
            with self.subTest(login=repr(login)), self.assertRaises(ValidationError):
                self.operator.action_change_user_login(login)
            self.assertEqual(self.user.login, old)
        self.assertFalse(self.env['tp.hr.employee.audit'].search([
            ('employee_ref', '=', self.employee.id), ('action', '=', 'login_change')]))
        for state in [{'active': True}, {'active': False, 'tp_hr_locked': True}]:
            duplicate.write(state)
            with self.assertRaises(ValidationError):
                self.operator.action_change_user_login(duplicate.login)

    def test_direct_write_and_import_share_policy_and_audit(self):
        for actor in [self.staff, self.hr, self.user]:
            target = self.user.with_user(actor).with_context(allowed_company_ids=self.company.ids)
            with self.assertRaises(AccessError):
                target.write({'login': 'rename.synthetic.forbidden'})
            with self.assertRaises(AccessError):
                target.sudo().write({'login': 'rename.synthetic.sudo'})
        with self.assertRaises(AccessError):
            self.employee.with_user(self.admin).write({'tp_user_login': 'rename.synthetic.related'})
        target = self.user.with_user(self.admin).with_context(allowed_company_ids=self.company.ids)
        target.write({'login': 'rename.synthetic.direct'})
        self.assertEqual(self.employee.tp_user_login, 'rename.synthetic.direct')
        self.assertEqual(self.env['tp.hr.employee.audit'].search_count([
            ('employee_ref', '=', self.employee.id), ('action', '=', 'login_change')]), 1)
        result = target.load(['.id', 'login'], [[str(self.user.id), 'rename.synthetic.import']])
        self.assertFalse(result['messages'])
        self.assertEqual(self.employee.tp_user_login, 'rename.synthetic.import')

    def test_stale_audit_failure_and_original_admin_protected(self):
        action = self.operator.action_open_change_login_dialog()
        wizard = self.env['tp.hr.account.wizard'].with_user(self.admin).with_context(
            allowed_company_ids=self.company.ids).browse(action['params']['wizardId'])
        self.operator.action_change_user_login('rename.synthetic.first')
        with self.assertRaises(UserError):
            wizard.action_change_login('rename.synthetic.stale')
        with patch.object(type(self.employee), 'message_post', side_effect=UserError('Synthetic audit failure')):
            with self.assertRaises(UserError):
                self.operator.action_change_user_login('rename.synthetic.rollback')
        self.assertEqual(self.user.login, 'rename.synthetic.first')
        self.assertFalse(self.env['tp.hr.employee.audit'].search([
            ('employee_ref', '=', self.employee.id), ('account_login', '=', 'rename.synthetic.rollback')]))
        original = self.env.ref('base.user_admin').with_user(self.user)
        with self.assertRaises(AccessError):
            original.write({'login': 'rename.synthetic.original'})
        full_admin = self.env.ref('tp_admin_delegation.group_full_admin', raise_if_not_found=False)
        if full_admin:
            delegate = self.env['res.users'].create({
                'name': 'Synthetic Rename Granted Admin', 'login': 'rename.synthetic.delegate',
                'company_id': self.company.id, 'company_ids': [Command.set(self.company.ids)],
                'group_ids': [Command.set(full_admin.ids)],
            })
            with self.assertRaises(AccessError):
                self.env.ref('base.user_admin').with_user(delegate).write({'login': 'rename.synthetic.original'})
            self.operator.with_user(delegate).action_change_user_login('rename.synthetic.delegated')
        self.assertFalse(self.employees[1].with_user(self.admin).with_context(
            allowed_company_ids=self.company.ids).tp_can_change_login)


@tagged('post_install', '-at_install')
class TestEmployeeLoginRenameHttp(HttpCase):
    def test_browser_dialog_validation_save_reload_and_mobile(self):
        group = self.env.ref('base.group_system') | self.env.ref('hr.group_hr_manager')
        original = self.env.ref('tp_admin_delegation.group_original_admin', raise_if_not_found=False)
        if original:
            group |= original
        operator = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic Rename Browser Admin', 'login': 'rename.browser.operator',
            'company_id': self.env.company.id, 'company_ids': [Command.set(self.env.company.ids)],
            'group_ids': [Command.set(group.ids)],
        })
        user, taken = self.env['res.users'].with_context(no_reset_password=True).create([
            {'name': 'Synthetic Rename Browser Target', 'login': 'rename.browser.before'},
            {'name': 'Synthetic Rename Browser Duplicate', 'login': 'rename.browser.taken'},
        ])
        employee = self.env['hr.employee'].create({'name': user.name, 'user_id': user.id})
        if original:
            self.env['tp.admin.delegation'].with_user(self.env.ref('base.user_admin'))._change(
                user, self.env.company, 'grant', 'Synthetic browser granted-admin target')
        self.authenticate(operator.login, 'synthetic')
        root = Path(__file__).resolve().parents[3]
        # A release candidate lives under .local; locate the repository owning its test runner.
        while not (root / 'scripts/tests/test_hr_login_rename.cjs').is_file():
            if root == root.parent:
                self.fail('Cannot locate the browser test runner')
            root = root.parent
        output = root / '.local/hr-login-rename-impl001/browser'
        output.mkdir(parents=True, exist_ok=True)
        fixture_path = output / 'fixture-private.json'
        with self.allow_requests():
            fixture_path.write_text(json.dumps({
                'base': self.base_url(), 'employeeId': employee.id, 'employeeName': employee.name,
                'oldLogin': user.login, 'newLogin': 'Rename.Browser.After', 'takenLogin': taken.login,
                'output': str(output), 'grantedAdmin': bool(original), 'cookies': [
                    {'name': 'session_id', 'value': self.session.sid, 'url': self.base_url(), 'httpOnly': True},
                    {'name': 'test_request_key', 'value': self.http_request_key, 'url': self.base_url()},
                ],
            }), encoding='utf-8')
            try:
                result = subprocess.run(['node', str(root / 'scripts/tests/test_hr_login_rename.cjs')],
                                        env={**os.environ, 'TP_LOGIN_RENAME_FIXTURE': str(fixture_path)},
                                        capture_output=True, text=True, timeout=210, check=False)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            finally:
                fixture_path.unlink(missing_ok=True)
        self.assertEqual(employee.tp_user_login, 'Rename.Browser.After')

    def test_real_authentication_old_session_new_login_and_same_password(self):
        password = 'Synthetic-Rename-HTTP-2026'
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic Rename HTTP', 'login': 'rename.http.before', 'password': password,
            'company_id': self.env.company.id, 'company_ids': [Command.set(self.env.company.ids)],
            'group_ids': [Command.set(self.env.ref('base.group_user').ids)],
        })
        employee = self.env['hr.employee'].create({'name': user.name, 'user_id': user.id})

        def login(name):
            return self.url_open('/web/session/authenticate', data=json.dumps({
                'jsonrpc': '2.0', 'id': 1, 'params': {
                    'db': get_db_name(), 'login': name, 'password': password,
                },
            }), headers={'Content-Type': 'application/json'}).json()

        self.assertEqual(login('rename.http.before')['result']['uid'], user.id)
        sid = self.opener.cookies.get('session_id')
        self.assertTrue(sid)
        old_token = user._compute_session_token(sid)
        employee.with_user(self.env.ref('base.user_admin')).action_change_user_login('Rename.HTTP.After')
        self.assertNotEqual(user._compute_session_token(sid), old_token)
        # Authenticate independently of the now-invalid native session cookie.
        for cookie in list(self.opener.cookies):
            if cookie.name == 'session_id':
                self.opener.cookies.clear(cookie.domain, cookie.path, cookie.name)
        self.assertIn('error', login('rename.http.before'))
        self.assertIn('error', login('rename.http.after'))
        self.assertEqual(login('Rename.HTTP.After')['result']['uid'], user.id)
        user.invalidate_recordset(['login'])
        self.assertEqual(employee.tp_user_login, 'Rename.HTTP.After')
