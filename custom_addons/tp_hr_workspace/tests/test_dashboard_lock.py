import secrets
from io import BytesIO

from openpyxl import load_workbook

from odoo import Command
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

from .test_hr_workspace import TestHrWorkspace
from odoo.addons.tp_web_login.models.res_users import LOCKED_MESSAGE


class TestDashboardLock(TestHrWorkspace):
    def test_job_filter_quality_catalog_export(self):
        job = self.env['hr.job'].create({'name': 'Synthetic Role', 'company_id': self.company.id})
        other_job = self.env['hr.job'].create({'name': 'Other Company Role', 'company_id': self.other.id})
        self.employees[0].write({'job_id': job.id, 'mobile_phone': '0900000000'})
        data = self.report().get_overview({'job_id': job.id})
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['missing_contact'], 0)
        self.assertEqual(sum(row['count'] for row in data['jobs']), 1)
        self.assertEqual(sum(row['count'] for row in data['departments']), 1)
        self.assertEqual(data['complete_basic'] + data['missing_basic'], data['total'])
        self.assertEqual(data['linked'] + data['pending'], data['total'])
        empty = self.report().get_overview({'job_id': job.id, 'status': 'archived'})
        self.assertEqual(empty['total'], 0)
        self.assertIn(job.id, [row['id'] for row in empty['catalog_jobs']])
        self.assertNotIn(other_job.id, [row['id'] for row in data['catalog_jobs']])
        with self.assertRaises(AccessError):
            self.report().get_overview({'job_id': other_job.id})
        with self.assertRaises(ValidationError):
            self.report().get_overview({'job_id': True})
        action = self.report().action_employees({'job_id': job.id})
        self.assertIn(('job_id', '=', job.id), action['domain'])
        workbook = load_workbook(BytesIO(self.report()._build_xlsx({'job_id': job.id})))
        self.assertIn(job.name, workbook['Danh sách nhân viên']['A2'].value)
        self.assertEqual(workbook['Danh sách nhân viên']['B6'].value, self.employees[0].name)
        self.assertEqual(workbook['Danh sách nhân viên']['H6'].value, 'Chưa có tài khoản')
        self.assertEqual(workbook['Tổng hợp đơn vị']['B7'].value, '=SUM(B6:B6)')
        workbook.close()

    def lock_fixture(self):
        password = secrets.token_urlsafe(24)
        user = self.env['res.users'].create({
            'name': 'Synthetic Lock User', 'login': 'hrdash.lock.synthetic', 'password': password,
            'company_id': self.company.id, 'company_ids': [Command.set([self.company.id])],
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        employee = self.employees[0]
        employee.user_id = user
        wizard = self.env['tp.hr.account.wizard'].with_user(self.admin).with_context(
            allowed_company_ids=[self.company.id],
        ).create({'employee_id': employee.id, 'expected_user_id': user.id, 'reason': 'Synthetic lock check'})
        return user, employee, wizard, password

    def test_lock_login_audit_and_sessions(self):
        user, employee, wizard, password = self.lock_fixture()
        groups = user.group_ids
        token = user._compute_session_token('synthetic-sid')
        wizard.action_lock()
        self.assertFalse(user.active)
        self.assertTrue(user.tp_hr_locked)
        self.assertTrue(employee.active)
        self.assertEqual(employee.tp_account_status, 'disabled')
        self.assertNotEqual(token, user._compute_session_token('synthetic-sid'))
        credential = {'type': 'password', 'login': user.login, 'password': password}
        with self.assertRaisesRegex(AccessDenied, LOCKED_MESSAGE):
            self.env['res.users']._login(credential, {'interactive': True})
        with self.assertRaises(AccessDenied) as failure:
            self.env['res.users']._login({**credential, 'password': 'wrong-password'}, {'interactive': True})
        self.assertNotIn(LOCKED_MESSAGE, str(failure.exception))
        self.assertIn('Synthetic lock check', str(employee.message_ids.mapped('body')))
        wizard.action_unlock()
        self.assertTrue(user.active)
        self.assertEqual(employee.tp_account_status, 'active')
        self.assertEqual(groups, user.group_ids)
        self.assertNotEqual(token, user._compute_session_token('synthetic-sid'))
        self.assertEqual(self.env['res.users']._login(credential, {'interactive': True})['uid'], user.id)

    def test_lock_denied_reason_scope_self_stale_and_context_bypass(self):
        user, employee, wizard, _password = self.lock_fixture()
        with self.assertRaises(AccessError):
            wizard.with_user(self.hr).action_lock()
        with self.assertRaises(AccessError):
            employee.with_user(self.hr).with_context(_tp_account_admin=True).write({'user_id': False})
        wizard.reason = False
        with self.assertRaises(UserError):
            wizard.action_lock()
        wizard.reason = 'Synthetic reason'
        with self.assertRaises(AccessError):
            wizard.with_context(allowed_company_ids=[self.other.id]).action_lock()
        employee.user_id = False
        with self.assertRaises(UserError):
            wizard.action_lock()
        employee.user_id = user
        user.company_ids = [Command.link(self.other.id)]
        with self.assertRaises(AccessError):
            wizard.action_lock()
        with self.assertRaises(UserError):
            self.admin.with_user(self.admin)._tp_set_account_lock(True, 'Synthetic self lock')
        self.assertTrue(user.active)
