"""AT02-C/AT03-C/AT06-A-D. Synthetic fixtures: run only in an explicitly authorized test DB."""
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import AttendanceCase, report

DAY = date(2026, 11, 9)


@tagged('post_install', '-at_install')
class TestAttendanceCorrection(AttendanceCase):
    def request(self, user=None, **vals):
        return self.env_for(user or self.viewer)['tp.hr.attendance.correction'].create(dict(
            work_date=DAY, requested_in=8.0, requested_out=17.0, reason='Synthetic private reason', **vals))

    def assign(self, **vals):
        return self.env['tp.hr.attendance.assignment'].with_company(self.company).create(dict(
            user_id=self.officer.id, company_id=self.company.id, can_review=True, **vals))

    def test_at06a_owner_is_session_even_with_foreign_id(self):
        own = self.env_for(self.viewer)['tp.hr.attendance.day'].tp_my_attendance({'employee_id': self.emp_b.id, 'month': '2026-11'})
        self.assertEqual(own['employee']['code'], self.emp_a.tp_employee_code)
        with self.assertRaises(AccessError):
            self.request(employee_id=self.emp_b.id)
        request = self.request()
        with self.assertRaises(AccessError):
            request.write({'employee_id': self.emp_b.id})
        with self.assertRaises(AccessError):
            request.write({'state': 'approved'})
        with self.assertRaises(UserError):
            request.action_submit()  # No reviewer must be actionable, never a fake approval.

    def test_at02c_private_search_export_file_and_revocation(self):
        assignment = self.assign()
        request = self.request()
        attachment = self.env_for(self.viewer)['ir.attachment'].create({'name': 'synthetic.txt', 'datas': 'c3ludGhldGlj',
            'res_model': request._name, 'res_id': request.id})
        request.action_submit()
        foreign = self.env_for(self.colleague)['tp.hr.attendance.correction']
        self.assertFalse(foreign.search([('reason', 'ilike', 'Synthetic')]))
        self.assertEqual(foreign.search_count([('id', '=', request.id)]), 0)
        with self.assertRaises(AccessError):
            foreign.browse(request.id).read(['reason', 'evidence_file'])
        with self.assertRaises(AccessError):
            attachment.with_user(self.colleague).read(['datas'])
        with self.assertRaises(AccessError):
            attachment.generate_access_token()
        with self.assertRaises(AccessError):
            attachment.write({'public': True})
        with self.assertRaises(AccessError):
            attachment.write({'res_model': 'res.partner'})
        reviewer = self.env_for(self.officer)['tp.hr.attendance.correction'].browse(request.id)
        self.assertEqual(reviewer.reason, 'Synthetic private reason')
        assignment.write({'active': False})
        with self.assertRaises(AccessError):
            reviewer.read(['reason'])

    def test_at03c_manager_keeps_oversight_without_implicit_review(self):
        self.assign()
        request = self.request()
        request.action_submit()
        manager_request = self.env_for(self.manager)['tp.hr.attendance.correction'].browse(request.id)
        self.assertTrue(manager_request.read(['reason']))
        with self.assertRaises(AccessError):
            manager_request.action_approve()
        self.assertTrue(self.env_for(self.manager)['tp.hr.attendance.rule'].has_access('create'))

    def test_at06b_own_only_draft_return_and_submit(self):
        self.assign()
        request = self.request()
        request.write({'reason': 'Updated synthetic'})
        request.action_submit()
        with self.assertRaises(UserError):
            request.write({'requested_out': 18.0})
        reviewer = self.env_for(self.officer)['tp.hr.attendance.correction'].browse(request.id)
        with self.assertRaises(UserError):
            reviewer.action_return(' ')
        reviewer.action_return('Bổ sung căn cứ')
        request.invalidate_recordset()
        self.assertEqual(request.state, 'returned')
        request.write({'requested_out': 18.0})
        request.action_submit()
        request.action_cancel()
        self.assertEqual(request.state, 'cancelled')
        with self.assertRaises(UserError):
            request.unlink()

    def test_at06c_scope_self_approval_retry_and_preserved_punch(self):
        assignment = self.assign(department_ids=[Command.set([self.dept_other.id])])
        request = self.request()
        with self.assertRaises(UserError):
            request.action_submit()
        assignment.write({'department_ids': [Command.set([self.dept.id])]})
        self.env['tp.hr.attendance.assignment'].create({'user_id': self.viewer.id, 'company_id': self.company.id, 'can_review': True})
        self.run_batch(report([{'code': '9901', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05')]}], DAY, 1))
        request.action_submit()
        with self.assertRaises(AccessError):
            request.action_approve()
        reviewer = self.env_for(self.officer)['tp.hr.attendance.correction'].browse(request.id)
        reviewer.action_approve()
        with self.assertRaises(UserError):
            reviewer.action_approve()
        sessions = self.env['tp.hr.attendance.session'].with_context(active_test=False).search([('employee_id', '=', self.emp_a.id)])
        self.assertEqual(len(sessions), 2)
        self.assertEqual(len(sessions.filtered('active')), 1)
        self.assertEqual(sessions.filtered('active').source, 'correction')

    def test_at06d_lock_amendment_and_reopen_require_reason(self):
        self.assign(can_lock=True)
        Period = self.env_for(self.officer)['tp.hr.attendance.period']
        period = Period.create({'name': 'Synthetic period', 'company_id': self.company.id, 'date_from': DAY, 'date_to': DAY})
        period._tp_lock()
        request = self.request()
        request.action_submit()
        reviewer = self.env_for(self.officer)['tp.hr.attendance.correction'].browse(request.id)
        with self.assertRaises(UserError):
            reviewer.action_approve(' ')
        reviewer.action_approve('Synthetic amendment basis')
        period.invalidate_recordset()
        self.assertEqual(period.version, 3)
        self.assertTrue(reviewer.is_amendment)
        with self.assertRaises(AccessError):
            period.write({'state': 'open'})
        with self.assertRaises(UserError):
            period._tp_unlock(' ')
        period._tp_unlock('Synthetic reopen basis')
        self.assertEqual(period.state, 'open')
