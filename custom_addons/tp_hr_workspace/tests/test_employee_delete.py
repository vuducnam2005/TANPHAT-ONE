import json
import time
import uuid

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import HttpCase, tagged

from .test_hr_workspace import TestHrWorkspace
from odoo.addons.tp_hr_workspace.models.employee_delete import COOLDOWN, WRONG_PASSWORD

# Synthetic test-only credentials, never a real account.
ADMIN_PASSWORD = 'Synthetic-Admin-HR010-Only'
MANAGER_PASSWORD = 'Synthetic-Manager-HR010-Only'


class TestEmployeeDeleteEntry(TestHrWorkspace):
    """HR-DELETE-010 entry points and preview without HTTP (synthetic data)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = cls.env['res.users'].create({
            'name': 'Synthetic Delete HR Manager', 'login': 'hr010.synthetic.dialog.manager',
            'company_id': cls.company.id, 'company_ids': [Command.set([cls.company.id])],
            'group_ids': [Command.set([cls.env.ref('hr.group_hr_manager').id])],
        })

    def scoped(self, records, actor=None):
        return records.with_user(actor or self.admin).with_context(allowed_company_ids=[self.company.id])

    def test_entries_open_the_password_dialog_only(self):
        self.assertNotIn('tp.hr.employee.delete.wizard', self.env, 'the reason-only wizard is gone')
        server_action = self.env.ref('tp_hr_workspace.action_server_delete_mistaken')
        self.assertEqual(server_action.name, 'Xóa vĩnh viễn nhân viên')
        self.assertEqual(server_action.group_ids, self.env.ref('base.group_system'))
        self.assertEqual(server_action.binding_model_id.model, 'hr.employee')
        self.assertFalse(self.env.ref('hr_timesheet.unlink_employee_action').binding_model_id)
        employee = self.employees[1]
        for action in (self.scoped(employee).action_unlink_wizard(), self.scoped(employee).action_tp_delete_mistaken(),
                       server_action.with_user(self.admin).with_context(active_model='hr.employee', active_ids=employee.ids,
                                                                        allowed_company_ids=[self.company.id]).run()):
            self.assertEqual((action['type'], action['tag']), ('ir.actions.client', 'tp_hr_workspace.employee_delete'))
            self.assertEqual(action['params'], {'employeeIds': employee.ids})
        for actor in (self.hr, self.manager):
            with self.assertRaises(AccessError):
                self.scoped(employee, actor).action_tp_permanent_delete()
            with self.assertRaises(AccessError):
                self.scoped(employee, actor).tp_permanent_delete_preview()
        views = self.env['hr.employee'].get_views([(False, 'form')])
        self.assertIn('delete="0"', views['views']['form']['arch'])
        archive = self.scoped(self.employees[0]).action_archive
        self.assertTrue(callable(archive), 'Lưu trữ stays a separate native action')

    def test_execute_needs_the_callers_http_session(self):
        employee = self.employees[1]
        with self.assertRaises(AccessError):
            self.scoped(employee).tp_permanent_delete_execute(ADMIN_PASSWORD, 'Synthetic', False, 'x', str(uuid.uuid4()))
        self.assertTrue(employee.exists())

    def test_preview_shows_identity_and_account_blockers(self):
        own = self.scoped(self.env['hr.employee']).create({'name': 'Synthetic Own Profile', 'company_id': self.company.id})
        own.sudo().user_id = self.admin
        preview = self.scoped(self.employees[1:] | own).tp_permanent_delete_preview()
        self.assertEqual(preview['count'], 3)
        self.assertEqual(preview['adminLogin'], self.admin.login)
        self.assertNotIn('password', json.dumps(preview).lower())
        rows = {row['id']: row for row in preview['employees']}
        archived = rows[self.employees[2].id]
        self.assertFalse(archived['active'])
        self.assertFalse(archived['block'], 'archived profiles can be deleted')
        self.assertIn('tài khoản bạn đang dùng', ' '.join(item['label'] for item in rows[own.id]['block']))
        self.assertTrue(rows[own.id]['lockBlock'], 'admin accounts are never locked from here')


@tagged('post_install', '-at_install')
class TestEmployeeDeleteHttp(HttpCase):
    """HR-DELETE-010 through the real JSON-RPC session (synthetic data and passwords)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({'name': 'Synthetic HR010 Company'})
        cls.other = cls.env['res.company'].create({'name': 'Synthetic HR010 Other'})
        cls.department = cls.env['hr.department'].create({'name': 'Synthetic HR010 Unit', 'company_id': cls.company.id})
        groups = [cls.env.ref('base.group_system').id, cls.env.ref('hr.group_hr_manager').id]
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        cls.admin = Users.create({
            'name': 'Synthetic HR010 Admin', 'login': 'hr010.synthetic.admin', 'password': ADMIN_PASSWORD,
            'company_id': cls.company.id, 'company_ids': [Command.set([cls.company.id, cls.other.id])],
            'group_ids': [Command.set(groups)],
        })
        cls.manager = Users.create({
            'name': 'Synthetic HR010 Manager', 'login': 'hr010.synthetic.manager', 'password': MANAGER_PASSWORD,
            'company_id': cls.company.id, 'company_ids': [Command.set([cls.company.id])],
            'group_ids': [Command.set([cls.env.ref('hr.group_hr_manager').id])],
        })
        Employee = cls.env['hr.employee'].with_company(cls.company)
        cls.first, cls.second = Employee.create([
            {'name': 'Synthetic HR010 First', 'company_id': cls.company.id, 'department_id': cls.department.id},
            {'name': 'Synthetic HR010 Second', 'company_id': cls.company.id, 'department_id': cls.department.id},
        ])
        cls.foreign = cls.env['hr.employee'].with_company(cls.other).create({'name': 'Synthetic HR010 Foreign', 'company_id': cls.other.id})

    def setUp(self):
        super().setUp()
        failures = getattr(self.registry, '_login_failures', None)
        if failures is not None:
            failures.clear()
            self.addCleanup(failures.clear)

    def rpc(self, method, ids, *args, company=None):
        response = self.url_open(f'/web/dataset/call_kw/hr.employee/{method}', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'model': 'hr.employee', 'method': method, 'args': [ids, *args],
                       'kwargs': {'context': {'allowed_company_ids': [(company or self.company).id]}}},
        })
        self.assertEqual(response.status_code, 200)
        return response.json()

    def preview(self, employees, company=None):
        result = self.rpc('tp_permanent_delete_preview', employees.ids, company=company)
        self.assertNotIn('error', result, result.get('error'))
        return result['result']

    def execute(self, employees, password, digest, request_id=None, reason='Synthetic duplicate profile', lock=False):
        return self.rpc('tp_permanent_delete_execute', employees.ids, password, reason, lock, digest, request_id or str(uuid.uuid4()))

    def audits(self, employees):
        return self.env['tp.hr.employee.audit'].sudo().search([('employee_ref', 'in', employees.ids)])

    def test_password_checked_on_every_request_and_retry_is_idempotent(self):
        # A fresh native identity check (10-minute window) must not be reused.
        self.authenticate(self.admin.login, ADMIN_PASSWORD, session_extra={'identity-check-last': time.time()})
        digest = self.preview(self.first)['digest']
        wrong = self.execute(self.first, 'Synthetic-wrong-HR010', digest)['result']
        self.assertEqual(wrong, {'ok': False, 'field': 'password', 'message': WRONG_PASSWORD})
        empty = self.execute(self.first, '', digest)['result']
        self.assertEqual((empty['ok'], empty['field']), (False, 'password'))
        self.env.invalidate_all()
        self.assertTrue(self.first.exists())
        self.assertFalse(self.audits(self.first))
        request_id = str(uuid.uuid4())
        done = self.execute(self.first, ADMIN_PASSWORD, digest, request_id)
        self.assertEqual(done['result']['ok'], True, done)
        self.assertEqual(done['result']['count'], 1)
        self.assertNotIn(ADMIN_PASSWORD, json.dumps(done))
        self.env.invalidate_all()
        self.assertFalse(self.env['hr.employee'].with_context(active_test=False).search([('id', '=', self.first.id)]))
        audit = self.audits(self.first)
        self.assertEqual((audit.action, audit.request_id, audit.actor_id, audit.account_action), ('permanent_delete', request_id, self.admin, 'none'))
        self.assertIn('xác minh lại', audit.verification)
        self.assertNotIn(ADMIN_PASSWORD, json.dumps(audit.read()[0], default=str))
        # The same request again (double click/retry): password checked, nothing deleted twice.
        again = self.execute(self.first, ADMIN_PASSWORD, digest, request_id)['result']
        self.assertEqual((again['ok'], again.get('already')), (True, True))
        self.assertEqual(self.execute(self.first, 'Synthetic-wrong-HR010', digest, request_id)['result']['ok'], False)
        self.assertEqual(len(self.audits(self.first)), 1)
        # Right after a successful delete, the next one asks again.
        digest = self.preview(self.second)['digest']
        self.assertEqual(self.execute(self.second, 'Synthetic-wrong-HR010', digest)['result']['ok'], False)
        self.env.invalidate_all()
        self.assertTrue(self.second.exists())

    def test_native_login_throttle_applies(self):
        # Native setting (main/test use 10 failures / 60 s); pinned here so the test is deterministic.
        self.env['ir.config_parameter'].sudo().set_int('base.login_cooldown_after', 3)
        self.env['ir.config_parameter'].sudo().set_int('base.login_cooldown_duration', 60)
        self.authenticate(self.admin.login, ADMIN_PASSWORD)
        digest = self.preview(self.first)['digest']
        for _attempt in range(3):
            self.assertEqual(self.execute(self.first, 'Synthetic-wrong-HR010', digest)['result']['message'], WRONG_PASSWORD)
        blocked = self.execute(self.first, ADMIN_PASSWORD, digest)['result']
        self.assertEqual((blocked['ok'], blocked['message']), (False, COOLDOWN))
        self.env.invalidate_all()
        self.assertTrue(self.first.exists())
        self.assertFalse(self.audits(self.first))

    def test_other_users_companies_and_forged_flags_are_denied(self):
        self.authenticate(self.manager.login, MANAGER_PASSWORD)
        denied = self.rpc('tp_permanent_delete_preview', self.first.ids)
        self.assertIn('AccessError', denied['error']['data']['name'])
        denied = self.rpc('tp_permanent_delete_execute', self.first.ids, MANAGER_PASSWORD, 'Synthetic', False, 'x', str(uuid.uuid4()))
        self.assertIn('AccessError', denied['error']['data']['name'])
        self.authenticate(self.admin.login, ADMIN_PASSWORD)
        foreign = self.rpc('tp_permanent_delete_preview', self.foreign.ids)
        self.assertIn('AccessError', foreign['error']['data']['name'])
        forged = self.url_open('/web/dataset/call_kw/hr.employee/unlink', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'model': 'hr.employee', 'method': 'unlink', 'args': [self.first.ids],
                       'kwargs': {'context': {'allowed_company_ids': [self.company.id], '_tp_employee_delete': True, 'is_admin': True}}},
        }).json()
        self.assertIn('error', forged)
        invalid = self.rpc('tp_permanent_delete_execute', self.first.ids, ADMIN_PASSWORD, 'Synthetic', False, 'x', 'not-a-request-id')
        self.assertIn('error', invalid)
        self.env.invalidate_all()
        self.assertTrue(self.first.exists() and self.foreign.exists())
        self.assertFalse(self.audits(self.first | self.foreign))

    def test_stale_preview_and_blockers_delete_nothing(self):
        self.authenticate(self.admin.login, ADMIN_PASSWORD)
        digest = self.preview(self.first | self.second)['digest']
        report = self.env['hr.employee'].create({'name': 'Synthetic HR010 Report', 'company_id': self.company.id, 'parent_id': self.second.id})
        stale = self.execute(self.first | self.second, ADMIN_PASSWORD, digest)
        self.assertIn('đã thay đổi sau khi xem trước', stale['error']['data']['message'])
        preview = self.preview(self.first | self.second)
        blocked_row = next(row for row in preview['employees'] if row['id'] == self.second.id)
        self.assertIn('đổi người quản lý', ' '.join(item['hint'] for item in blocked_row['block']))
        blocked = self.execute(self.first | self.second, ADMIN_PASSWORD, preview['digest'])
        self.assertIn('không hồ sơ nào bị xóa', blocked['error']['data']['message'])
        self.env.invalidate_all()
        self.assertTrue(self.first.exists() and self.second.exists() and report.parent_id == self.second)
        self.assertFalse(self.audits(self.first | self.second))

    def test_account_kept_by_default_or_locked_on_request(self):
        kd = self.env['hr.department'].create({'name': 'Synthetic HR010 KD', 'company_id': self.company.id})
        self.env['crm.team'].create({'name': 'Synthetic HR010 Team', 'company_id': self.company.id, 'kd_department_id': kd.id})
        scoped = self.env.ref('tp_kd_workspace.group_scoped_staff')
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic HR010 Account', 'login': 'hr010.synthetic.account', 'password': 'Synthetic-Account-HR010-Only',
            'company_id': self.company.id, 'company_ids': [Command.set([self.company.id])],
            'group_ids': [Command.set([self.env.ref('base.group_user').id, scoped.id])],
        })
        employee = self.env['hr.employee'].create({'name': user.name, 'company_id': self.company.id, 'department_id': kd.id})
        employee.sudo().user_id = user
        role = self.env['tp.kd.department.role'].create({'user_id': user.id, 'department_id': kd.id,
                                                         'company_id': self.company.id, 'reason': 'Synthetic HR010 head'})
        revision = user.tp_lock_revision
        self.authenticate(self.admin.login, ADMIN_PASSWORD)
        preview = self.preview(employee)
        self.assertEqual(preview['accountCount'], 1)
        self.assertTrue(preview['employees'][0]['keepBlock'], 'a live role cannot be left hanging')
        kept = self.execute(employee, ADMIN_PASSWORD, preview['digest'])
        self.assertIn('không hồ sơ nào bị xóa', kept['error']['data']['message'])
        done = self.execute(employee, ADMIN_PASSWORD, preview['digest'], lock=True)['result']
        self.assertEqual((done['ok'], done['locked']), (True, 1))
        self.env.invalidate_all()
        self.assertFalse(employee.exists())
        self.assertTrue(user.exists(), 'the account is never deleted')
        self.assertFalse(user.active)
        self.assertTrue(user.tp_hr_locked)
        self.assertGreater(user.tp_lock_revision, revision)
        self.assertFalse(role.active)
        self.assertNotIn(scoped, user.group_ids)
        audit = self.audits(employee)
        self.assertEqual((audit.account_action, audit.account_ref, audit.account_login), ('locked', user.id, user.login))
        self.assertIn(role.id, audit.snapshot['revoked']['roles'])
        self.assertTrue(self.admin.active and not self.admin.tp_hr_locked)
