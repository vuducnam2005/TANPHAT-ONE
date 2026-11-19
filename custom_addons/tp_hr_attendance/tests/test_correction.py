"""AT02-C/AT03-C/AT06-A-D + CHG-20261119-005 (Original Admin approves every correction).

Synthetic fixtures only: run in an explicitly authorized test DB; nothing here touches real employees.
"""
import base64
from datetime import date
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import AttendanceCase, report
from odoo.addons.tp_organization.models.hr_employee import _ROSTER_WRITE

DAY = date(2026, 11, 9)


@tagged('post_install', '-at_install', 'attendance_correction')
class TestAttendanceCorrection(AttendanceCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)

        def admin(login):
            # Same shape as the seeded Original Admin: internal, system rights, explicit original-admin group.
            return Users.create({
                'name': login, 'login': login, 'company_id': cls.company.id, 'company_ids': [Command.set([cls.company.id])],
                'group_ids': [Command.set([cls.env.ref(xmlid).id for xmlid in (
                    'base.group_user', 'base.group_system', 'tp_admin_delegation.group_original_admin')])],
            })

        cls.admin_factory = staticmethod(admin)
        cls.root = admin('att005.synthetic.root')

    def request(self, user=None, **vals):
        return self.env_for(user or self.viewer)['tp.hr.attendance.correction'].create(dict(
            work_date=DAY, requested_in=8.0, requested_out=17.0, reason='Synthetic private reason', **vals))

    def assign(self, **vals):
        return self.env['tp.hr.attendance.assignment'].with_company(self.company).create(dict(
            dict(user_id=self.officer.id, company_id=self.company.id, can_review=True), **vals))

    def employee(self, **vals):
        return self.env['hr.employee'].with_company(self.company).with_context(_tp_roster_write=_ROSTER_WRITE).create(
            dict(company_id=self.company.id, **vals))

    def as_user(self, user, request):
        return self.env_for(user)['tp.hr.attendance.correction'].browse(request.id)

    def upload(self, clock_in, clock_out):
        raw = report([{'code': '9901', 'name': 'Synthetic Người Một', 'times': [(clock_in, clock_out)], 'late': (1, 7)}],
                     DAY, 1, late=True)
        result = self.env_for(self.manager)['tp.hr.attendance.batch'].tp_upload_files({
            'files': [{'file_name': 'synthetic.xlsx', 'data': base64.b64encode(raw).decode()}]})
        self.assertEqual(result['error_count'], 0, result)

    def delegate(self):
        """A Full Admin granted through tp_admin_delegation by the synthetic Original Admin."""
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'att005.synthetic.delegate', 'login': 'att005.synthetic.delegate', 'company_id': self.company.id,
            'company_ids': [Command.set([self.company.id])], 'group_ids': [Command.set([self.env.ref('base.group_user').id])]})
        self.env['tp.admin.delegation'].with_user(self.root).with_context(allowed_company_ids=[self.company.id])._change(
            user, self.company, 'grant', 'Synthetic delegated full admin')
        self.assertTrue(user._tp_has_live_admin_grant(company=self.company))
        self.assertTrue(user.has_group('hr.group_hr_manager'))
        self.assertFalse(user._tp_is_original_admin())
        return user

    # ----------------------------------------------------------------- owner
    def test_at06a_owner_is_session_even_with_foreign_id(self):
        own = self.env_for(self.viewer)['tp.hr.attendance.day'].tp_my_attendance({'employee_id': self.emp_b.id, 'month': '2026-11'})
        self.assertEqual(own['employee']['code'], self.emp_a.tp_employee_code)
        with self.assertRaises(AccessError):
            self.request(employee_id=self.emp_b.id)
        with self.assertRaises(AccessError):
            self.request(state='approved')
        request = self.request()
        with self.assertRaises(AccessError):
            request.write({'employee_id': self.emp_b.id})
        for vals in ({'state': 'approved'}, {'reviewer_id': self.viewer.id}, {'session_id': False, 'state': 'submitted'}):
            with self.assertRaises(AccessError):
                request.write(vals)
        with self.assertRaises(AccessError):
            self.env_for(self.viewer)['tp.hr.attendance.session'].create({
                'employee_id': self.emp_a.id, 'company_id': self.company.id, 'work_date': DAY,
                'check_in': '2026-11-09 01:00:00', 'check_out': '2026-11-09 10:00:00', 'source': 'correction'})

    def test_admin005_no_original_admin_means_no_submit_and_no_substitute(self):
        # The only Original Admin loses the role: nobody inherits it, the draft stays a draft.
        self.root.write({'group_ids': [Command.unlink(self.env.ref('tp_admin_delegation.group_original_admin').id)]})
        self.assign()
        request = self.request()
        with self.assertRaisesRegex(UserError, 'admin chính'):
            request.action_submit()
        self.assertEqual(request.state, 'draft')
        self.assertFalse(request.reviewer_user_ids)

    # ---------------------------------------------------------------- privacy
    def test_at02c_private_search_export_file(self):
        request = self.request()
        attachment = self.env_for(self.viewer)['ir.attachment'].create({'name': 'synthetic.txt', 'raw': b'synthetic',
            'res_model': request._name, 'res_id': request.id})
        request.action_submit()
        self.assertEqual(request.reviewer_user_ids, self.root)
        foreign = self.env_for(self.colleague)['tp.hr.attendance.correction']
        self.assertFalse(foreign.search([('reason', 'ilike', 'Synthetic')]))
        self.assertEqual(foreign.search_count([('id', '=', request.id)]), 0)
        with self.assertRaises(AccessError):
            foreign.browse(request.id).read(['reason', 'evidence_file'])
        with self.assertRaises(AccessError):
            attachment.with_user(self.colleague).read(['raw'])
        with self.assertRaises(AccessError):
            attachment.generate_access_token()
        with self.assertRaises(AccessError):
            attachment.write({'public': True})
        with self.assertRaises(AccessError):
            attachment.write({'res_model': 'res.partner'})
        self.assertEqual(self.as_user(self.root, request).reason, 'Synthetic private reason')

    # ------------------------------------------------------- who may approve
    def test_at03c_roles_never_approve_only_original_admin(self):
        """HR manager, review assignee, department head and delegated Full Admin are refused in the backend."""
        self.assign()
        head_user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'att005.synthetic.head', 'login': 'att005.synthetic.head', 'company_id': self.company.id,
            'company_ids': [Command.set([self.company.id])], 'group_ids': [Command.set([self.env.ref('hr.group_hr_user').id])]})
        head = self.employee(name='Synthetic Trưởng Phòng', department_id=self.dept.id, user_id=head_user.id)
        self.dept.manager_id = head
        delegate = self.delegate()
        request = self.request()
        request.action_submit()
        self.assertEqual(request.reviewer_user_ids, self.root)
        self.assertTrue(self.as_user(self.manager, request).read(['reason']))
        self.assertTrue(self.as_user(delegate, request).read(['reason']))
        for user in (self.manager, self.officer, head_user, delegate):
            record = self.as_user(user, request)
            with self.assertRaises(AccessError):
                record.action_approve()
            with self.assertRaises(AccessError):
                record.action_return('Synthetic return')
            with self.assertRaises(AccessError):
                record.action_open_approve()
            with self.assertRaises(AccessError):
                self.env_for(user)['tp.hr.attendance.review.wizard'].create(
                    {'correction_id': request.id, 'decision': 'approve'}).action_confirm()
        request.invalidate_recordset()
        self.assertEqual(request.state, 'submitted')
        self.assertTrue(self.as_user(self.root, request).tp_can_review)
        self.assertFalse(self.as_user(delegate, request).tp_can_review)
        self.assertTrue(self.env_for(self.manager)['tp.hr.attendance.rule'].has_access('create'))

    def test_admin005_menu_follows_original_admin(self):
        menu = self.env.ref('tp_hr_attendance.menu_review')
        self.assign()
        self.assertNotIn(menu.id, self.env_for(self.officer)['ir.ui.menu']._visible_menu_ids())
        self.assertIn(menu.id, self.env_for(self.root)['ir.ui.menu']._visible_menu_ids())
        # HR managers keep the read-only oversight entry they had before.
        self.assertIn(menu.id, self.env_for(self.manager)['ir.ui.menu']._visible_menu_ids())

    # --------------------------------------------------------------- flows
    def test_at06b_own_only_draft_return_and_resubmit(self):
        request = self.request()
        request.write({'reason': 'Updated synthetic'})
        request.action_submit()
        self.assertEqual(dict(request._fields['state'].selection)[request.state], 'Chờ admin duyệt')
        with self.assertRaises(UserError):
            request.write({'requested_out': 18.0})
        admin = self.as_user(self.root, request)
        with self.assertRaises(UserError):
            admin.action_return(' ')
        wizard = self.env_for(self.root)['tp.hr.attendance.review.wizard'].create(
            {'correction_id': request.id, 'decision': 'return', 'note': 'Bổ sung căn cứ'})
        self.assertEqual(wizard.action_confirm()['params']['type'], 'success')
        request.invalidate_recordset()
        self.assertEqual((request.state, request.reviewer_id, request.review_note), ('returned', self.root, 'Bổ sung căn cứ'))
        self.assertTrue(request.reviewed_at)
        mine = self.env_for(self.viewer)['tp.hr.attendance.correction'].search_read(
            [('id', '=', request.id)], ['state', 'reviewer_id', 'reviewed_at', 'review_note'])
        self.assertEqual(mine[0]['review_note'], 'Bổ sung căn cứ')
        request.write({'requested_out': 18.0})
        request.action_submit()
        self.assertFalse(request.review_note)
        request.action_cancel()
        self.assertEqual(request.state, 'cancelled')
        with self.assertRaises(UserError):
            request.unlink()

    def test_at06c_self_approval_retry_and_preserved_punch(self):
        self.run_batch(report([{'code': '9901', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05')]}], DAY, 1))
        # The Original Admin's own request cannot go to themselves; a second Original Admin handles it.
        self.employee(name='Synthetic Admin Chính', department_id=self.dept_other.id, user_id=self.root.id)
        own = self.request(user=self.root)
        with self.assertRaises(UserError):
            own.action_submit()
        second = self.admin_factory('att005.synthetic.root2')
        own.action_submit()
        self.assertEqual(own.reviewer_user_ids, second)
        with self.assertRaises(AccessError):
            own.action_approve()
        request = self.request()
        request.action_submit()
        self.assertEqual(request.reviewer_user_ids, self.root | second)
        with self.assertRaises(AccessError):
            request.action_approve()
        admin = self.as_user(self.root, request)
        admin.action_approve()
        for user in (self.root, second):
            with self.assertRaises(UserError):
                self.as_user(user, request).action_approve()
        sessions = self.env['tp.hr.attendance.session'].with_context(active_test=False).search([('employee_id', '=', self.emp_a.id)])
        self.assertEqual(len(sessions), 2)
        self.assertEqual(len(sessions.filtered('active')), 1)
        self.assertEqual(sessions.filtered('active').source, 'correction')

    def test_admin005_approval_persists_and_every_screen_reads_it(self):
        Late = self.env['tp.hr.attendance.late'].sudo()
        self.upload('07:37', '17:05')
        late_before = Late.search([('employee_id', '=', self.emp_a.id), ('state', '=', 'applied')]).read(['late_count', 'late_minutes'])
        request = self.request()
        self.assertEqual(self.day(self.emp_a, DAY).in_time, '07:37')  # A draft never changes the sheet.
        request.action_submit()
        self.assertEqual((request.current_in, request.current_out), ('07:37', '17:05'))
        self.assertEqual(self.day(self.emp_a, DAY).in_time, '07:37')  # Neither does a pending request.
        wizard = self.env_for(self.root)['tp.hr.attendance.review.wizard'].create({'correction_id': request.id, 'decision': 'approve'})
        result = wizard.action_confirm()
        self.assertEqual((result['tag'], result['params']['next']['type']), ('display_notification', 'ir.actions.act_window_close'))
        request.invalidate_recordset()
        self.assertEqual((request.state, request.reviewer_id), ('approved', self.root))
        self.assertTrue(request.reviewed_at and request.submitted_at and request.session_id)
        self.assertIn('07:37–17:05', request.replaced_times)
        day = self.day(self.emp_a, DAY)
        self.assertEqual((day.in_time, day.out_time, request.day_id), ('08:00', '17:00', day))
        mine = self.env_for(self.viewer)['tp.hr.attendance.day'].tp_mine({'mode': 'month', 'date': DAY.isoformat()})
        row = next(row for row in mine['rows'] if row['date'] == DAY.isoformat())
        self.assertEqual((row['in'], row['out'], row['requests'][0]['state']), ('08:00', '17:00', 'approved'))
        sheet = self.env_for(self.viewer)['tp.hr.attendance.day'].tp_sheet({'mode': 'day', 'date': DAY.isoformat()})
        cell = next(row for row in sheet['rows'] if row['id'] == self.emp_a.id)
        self.assertEqual((cell['in'], cell['out']), ('08:00', '17:00'))
        self.assertTrue(self.env_for(self.viewer)['tp.hr.attendance.day'].tp_overview({'mode': 'day', 'date': DAY.isoformat()}))
        # Late totals stay those of the file; a later Excel never overwrites the approved correction.
        self.assertEqual(Late.search([('employee_id', '=', self.emp_a.id), ('state', '=', 'applied')]).read(
            ['late_count', 'late_minutes']), late_before)
        self.upload('07:50', '17:20')
        day.invalidate_recordset()
        self.assertEqual((day.in_time, day.out_time), ('08:00', '17:00'))
        active = self.env['tp.hr.attendance.session'].search([('employee_id', '=', self.emp_a.id), ('work_date', '=', DAY)])
        self.assertEqual(active.source, 'correction')
        logs = self.env['tp.hr.attendance.log'].sudo().search([('model', '=', request._name), ('res_id', '=', request.id)])
        self.assertIn('correction_approve', logs.mapped('action'))

    def test_admin005_failed_approval_rolls_back_everything(self):
        self.upload('07:37', '17:05')
        request = self.request()
        request.action_submit()
        admin = self.as_user(self.root, request)
        Day = type(self.env['tp.hr.attendance.day'])
        original = Day._tp_refresh

        failure = 'Synthetic failure after day refresh'

        def broken(self, *args, **kwargs):
            original(self, *args, **kwargs)
            raise UserError(failure)

        with patch.object(Day, '_tp_refresh', broken), self.assertRaises(UserError), self.env.cr.savepoint():
            admin.action_approve()
        request.invalidate_recordset()
        self.env.invalidate_all()
        self.assertEqual(request.state, 'submitted')
        self.assertEqual(self.day(self.emp_a, DAY).in_time, '07:37')
        self.assertFalse(self.env['tp.hr.attendance.session'].search([
            ('employee_id', '=', self.emp_a.id), ('work_date', '=', DAY), ('source', '=', 'correction')]))

    def test_at06d_lock_amendment_and_reopen_require_reason(self):
        self.assign(can_lock=True)
        Period = self.env_for(self.officer)['tp.hr.attendance.period']
        period = Period.create({'name': 'Synthetic period', 'company_id': self.company.id, 'date_from': DAY, 'date_to': DAY})
        period._tp_lock()
        request = self.request()
        request.action_submit()
        # A lock assignee is not an approver; the Original Admin still needs the existing lock right to amend.
        with self.assertRaises(AccessError):
            self.as_user(self.officer, request).action_approve('Synthetic amendment basis')
        admin = self.as_user(self.root, request)
        self.assertFalse(admin.tp_can_review)
        with self.assertRaises(AccessError):
            admin.action_approve('Synthetic amendment basis')
        self.assign(user_id=self.root.id, can_review=False, can_lock=True)
        admin.invalidate_recordset()
        self.assertTrue(admin.tp_can_review)
        with self.assertRaises(UserError):
            admin.action_approve(' ')
        admin.action_approve('Synthetic amendment basis')
        period.invalidate_recordset()
        self.assertEqual(period.version, 3)
        self.assertTrue(admin.is_amendment)
        with self.assertRaises(AccessError):
            period.write({'state': 'open'})
        with self.assertRaises(UserError):
            period._tp_unlock(' ')
        period._tp_unlock('Synthetic reopen basis')
        self.assertEqual(period.state, 'open')
