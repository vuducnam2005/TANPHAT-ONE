"""AT02-C/AT03-C/AT06-A-D + CHG-20261119-005/-012 (admins, Original or live delegated, approve corrections).

Synthetic fixtures only: run in an explicitly authorized test DB; nothing here touches real employees.
"""
import base64
from datetime import date
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import AttendanceCase, report
from odoo.addons.tp_hr_attendance.models.attendance_common import correction_admins
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
        raw = report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [(clock_in, clock_out)], 'late': (1, 7)}],
                     DAY, 1, late=True)
        result = self.env_for(self.manager)['tp.hr.attendance.batch']._tp_upload_files({
            'files': [{'file_name': 'synthetic.xlsx', 'data': base64.b64encode(raw).decode()}]})
        self.assertEqual(result['error_count'], 0, result)

    def delegate(self, login='att005.synthetic.delegate', companies=None):
        """A Full Admin granted through tp_admin_delegation by the synthetic Original Admin."""
        companies = companies or self.company
        user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': login, 'login': login, 'company_id': self.company.id,
            'company_ids': [Command.set(companies.ids)], 'group_ids': [Command.set([self.env.ref('base.group_user').id])]})
        self.delegation(user, 'grant')
        self.assertTrue(user._tp_has_live_admin_grant(company=self.company))
        self.assertTrue(user.has_group('hr.group_hr_manager'))
        self.assertFalse(user._tp_is_original_admin())
        return user

    def delegation(self, user, operation):
        self.env['tp.admin.delegation'].with_user(self.root).with_context(allowed_company_ids=[self.company.id])._change(
            user, self.company, operation, f'Synthetic {operation} full admin')

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
        # The only admin loses the role: nobody inherits it (system rights or assignments alone do not count).
        self.root.write({'group_ids': [Command.unlink(self.env.ref('tp_admin_delegation.group_original_admin').id)]})
        self.assertTrue(self.root.has_group('base.group_system'))
        self.assign()
        request = self.request()
        with self.assertRaisesRegex(UserError, 'admin gốc hoặc admin được ủy quyền'):
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
    def test_at03c_roles_never_approve_only_admins(self):
        """HR manager, review assignee and department head are refused in the backend; a delegated Full Admin approves."""
        self.assign()
        head_user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'att005.synthetic.head', 'login': 'att005.synthetic.head', 'company_id': self.company.id,
            'company_ids': [Command.set([self.company.id])], 'group_ids': [Command.set([self.env.ref('hr.group_hr_user').id])]})
        head = self.employee(name='Synthetic Trưởng Phòng', department_id=self.dept.id, user_id=head_user.id)
        self.dept.manager_id = head
        delegate = self.delegate()
        request = self.request()
        request.action_submit()
        self.assertEqual(request.reviewer_user_ids, self.root | delegate)
        self.assertTrue(self.as_user(self.manager, request).read(['reason']))
        self.assertTrue(self.as_user(delegate, request).read(['reason']))
        for user in (self.manager, self.officer, head_user):
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
        self.assertFalse(self.as_user(self.manager, request).tp_can_review)
        self.assertTrue(self.as_user(self.root, request).tp_can_review)
        self.assertTrue(self.as_user(delegate, request).tp_can_review)
        self.assertTrue(self.env_for(self.manager)['tp.hr.attendance.rule'].has_access('create'))
        # Full admin rights include handling corrections: the delegate approves through the same dialog.
        self.as_user(delegate, request).action_open_approve()
        wizard = self.env_for(delegate)['tp.hr.attendance.review.wizard'].create({'correction_id': request.id, 'decision': 'approve'})
        self.assertEqual(wizard.action_confirm()['params']['type'], 'success')
        request.invalidate_recordset()
        self.assertEqual((request.state, request.reviewer_id), ('approved', delegate))
        self.assertEqual(request.session_id.source, 'correction')
        with self.assertRaisesRegex(UserError, 'không còn chờ duyệt'):
            self.as_user(self.root, request).action_approve()

    def test_admin012_delegate_returns_own_blocked_and_revoke_is_immediate(self):
        other = self.env['res.company'].create({'name': 'Synthetic ADM012 Other Company'})
        self.root.write({'company_ids': [Command.link(other.id)]})
        delegate = self.delegate(companies=self.company | other)
        # The grant is per company: same user, system rights and access to the other company, but no grant there.
        self.assertIn(delegate, correction_admins(self.env, self.company))
        self.assertNotIn(delegate, correction_admins(self.env, other))
        request = self.request()
        request.action_submit()
        record = self.as_user(delegate, request)
        with self.assertRaises(UserError):
            record.action_return(' ')
        self.assertTrue(record.action_return('Synthetic bổ sung căn cứ'))
        request.invalidate_recordset()
        self.assertEqual((request.state, request.reviewer_id, request.review_note), ('returned', delegate, 'Synthetic bổ sung căn cứ'))
        # The delegate's own request goes to the other admins only; self-approval stays blocked.
        self.employee(name='Synthetic Admin Ủy Quyền', department_id=self.dept_other.id, user_id=delegate.id)
        own = self.request(user=delegate)
        own.action_submit()
        self.assertEqual(own.reviewer_user_ids, self.root)
        with self.assertRaises(AccessError):
            own.action_approve()
        # Revoke by the Original Admin: no approval, no return, no private read, list recomputed on next submit.
        request.action_submit()
        self.assertEqual(request.reviewer_user_ids, self.root | delegate)
        self.delegation(delegate, 'revoke')
        self.assertFalse(delegate._tp_has_live_admin_grant(company=self.company))
        stale = self.as_user(delegate, request)
        for call in (stale.action_approve, lambda: stale.action_return('Synthetic'), stale.action_open_approve,
                     lambda: stale.read(['reason'])):
            with self.assertRaises(AccessError):
                call()
        self.assertNotIn(delegate, correction_admins(self.env, self.company))
        request.invalidate_recordset()
        self.assertEqual(request.state, 'submitted')
        self.as_user(self.root, request).action_approve()
        request.invalidate_recordset()
        self.assertEqual((request.state, request.reviewer_id, request.reviewer_user_ids), ('approved', self.root, self.root))

    def test_admin005_menu_follows_admin_right(self):
        menu = self.env.ref('tp_hr_attendance.menu_review')
        self.assign()
        self.assertNotIn(menu.id, self.env_for(self.officer)['ir.ui.menu']._visible_menu_ids())
        self.assertIn(menu.id, self.env_for(self.root)['ir.ui.menu']._visible_menu_ids())
        self.assertIn(menu.id, self.env_for(self.delegate())['ir.ui.menu']._visible_menu_ids())
        # System rights without the Original Admin role or a live grant do not open the queue.
        plain = self.admin_factory('att012.synthetic.plain.system')
        plain.write({'group_ids': [Command.unlink(self.env.ref('tp_admin_delegation.group_original_admin').id)]})
        self.assertNotIn(menu.id, self.env_for(plain)['ir.ui.menu']._visible_menu_ids())
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
        # Submitted requests must be withdrawn (not cancelled directly); reopen to draft allows cancel.
        with self.assertRaises(UserError):
            request.action_cancel()
        request.action_withdraw('Synthetic nhầm giờ')
        self.assertEqual(request.state, 'withdrawn')
        self.assertEqual((request.withdrawn_by_id, request.withdraw_reason), (self.viewer, 'Synthetic nhầm giờ'))
        self.assertTrue(request.withdrawn_at)
        request.action_reopen_draft()
        self.assertEqual(request.state, 'draft')
        request.action_cancel()
        self.assertEqual(request.state, 'cancelled')
        with self.assertRaises(UserError):
            request.unlink()

    def test_at06c_self_approval_retry_and_preserved_punch(self):
        self.run_batch(report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05')]}], DAY, 1))
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
        self.assertTrue(period.tp_can_lock)
        self.assertFalse(self.env_for(self.manager)['tp.hr.attendance.period'].browse(period.id).tp_can_lock)
        with self.assertRaises(AccessError):
            self.env_for(self.manager)['tp.hr.attendance.period'].browse(period.id)._tp_lock('HR manager without lock right')
        lock_wiz = self.env_for(self.root)['tp.hr.attendance.period.wizard'].create({
            'period_id': period.id, 'operation': 'lock', 'reason': 'Synthetic lock with pending',
        })
        lock_res = lock_wiz.action_confirm()
        self.assertEqual((lock_res['tag'], lock_res['params']['type']), ('display_notification', 'success'))
        period.invalidate_recordset()
        self.assertEqual(period.state, 'locked')
        request = self.request()
        request.action_submit()
        # A lock assignee and HR manager are not approvers; Original Admin has full lock & amendment rights (DEC-053/061)
        # and still requires a written amendment basis.
        with self.assertRaises(AccessError):
            self.as_user(self.officer, request).action_approve('Synthetic amendment basis')
        with self.assertRaises(AccessError):
            self.as_user(self.manager, request).action_approve('Synthetic amendment basis')
        admin = self.as_user(self.root, request)
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

    def test_one_click_submit_withdraw_and_queue_rules(self):
        self.upload('07:37', '17:05')
        Corr = self.env_for(self.viewer)['tp.hr.attendance.correction']
        review_domain = [('state', '=', 'submitted')]

        # 1. Failed one-click submit (empty reason) rolls back without leaving a draft.
        with self.assertRaises(UserError):
            Corr.tp_save_and_submit({
                'work_date': DAY, 'requested_in': 8.0, 'requested_out': 17.0, 'reason': '   ',
            }, False, True)
        self.assertFalse(Corr.search([('work_date', '=', DAY)]))

        # 2. Valid one-click submit creates and submits in one transaction; appears in admin queue.
        res = Corr.tp_save_and_submit({
            'work_date': DAY, 'requested_in': 8.0, 'requested_out': 17.0, 'reason': 'Synthetic quên chấm',
        }, False, True)
        req = Corr.browse(res['id'])
        self.assertEqual(req.state, 'submitted')
        self.assertEqual(self.day(self.emp_a, DAY).in_time, '07:37')  # Day untouched before approval.
        self.assertIn(req.id, self.env_for(self.root)['tp.hr.attendance.correction'].search(review_domain).ids)

        # 3. Cannot create a second submitted request for the same employee & day.
        with self.assertRaises(UserError):
            Corr.tp_save_and_submit({
                'work_date': DAY, 'requested_in': 8.5, 'requested_out': 17.5, 'reason': 'Synthetic trùng ngày',
            }, False, True)

        # 4. Admin and other users cannot withdraw on behalf of the creator.
        with self.assertRaises(AccessError):
            self.as_user(self.root, req).action_withdraw('Admin không được thu hồi thay')
        with self.assertRaises(AccessError):
            self.as_user(self.colleague, req).action_withdraw('Người khác không được thu hồi')

        # 5. Owner withdraws -> withdrawn, disappears from admin queue, attendance untouched, history logged.
        req.action_withdraw('')
        self.assertEqual(req.state, 'withdrawn')
        self.assertEqual(req.withdrawn_by_id, self.viewer)
        self.assertTrue(req.withdrawn_at)
        self.assertEqual(self.day(self.emp_a, DAY).in_time, '07:37')
        self.assertNotIn(req.id, self.env_for(self.root)['tp.hr.attendance.correction'].search(review_domain).ids)
        logs = self.env['tp.hr.attendance.log'].sudo().search([('model', '=', req._name), ('res_id', '=', req.id)])
        self.assertIn('correction_withdraw', logs.mapped('action'))

        # 6. From withdrawn, owner can reopen as draft, edit and resubmit, OR create a new request.
        req.action_reopen_draft()
        self.assertEqual(req.state, 'draft')
        self.assertNotIn(req.id, self.env_for(self.root)['tp.hr.attendance.correction'].search(review_domain).ids)
        req.write({'requested_out': 17.5})
        req.action_submit()
        self.assertEqual(req.state, 'submitted')

        # 7. Cannot withdraw when period is locked.
        req.action_withdraw('Thu hồi trước khi chốt kỳ')
        req.action_reopen_draft()
        self.assign(can_lock=True)
        period = self.env_for(self.officer)['tp.hr.attendance.period'].create({
            'name': 'Synthetic lock withdraw', 'company_id': self.company.id, 'date_from': DAY, 'date_to': DAY,
        })
        period._tp_lock('Synthetic lock before submit')
        req.action_submit()
        self.assertFalse(req.tp_can_withdraw)
        with self.assertRaisesRegex(UserError, 'kỳ công đã chốt'):
            req.action_withdraw('Sau chốt kỳ')
        period._tp_unlock('Synthetic reopen for approve test')

        # 8. Approved request cannot be withdrawn.
        self.as_user(self.root, req).action_approve()
        req.invalidate_recordset()
        self.assertEqual(req.state, 'approved')
        self.assertFalse(req.tp_can_withdraw)
        with self.assertRaises(UserError):
            req.action_withdraw('Sau duyệt')

    def test_one_click_retries_reuse_draft_and_submitted_requests(self):
        Corr = self.env_for(self.viewer)['tp.hr.attendance.correction']
        vals = {'work_date': DAY, 'requested_in': 0.0, 'requested_out': 1.0}
        create_token, submit_token = '0123456789abcdef', 'fedcba9876543210'
        for missing in (None, False, ''):
            with self.assertRaises(ValidationError):
                Corr.tp_save_and_submit(dict(vals, requested_in=missing), False, False, create_token)
        with self.assertRaises(ValidationError):
            Corr.tp_save_and_submit({'work_date': DAY, 'requested_out': 1.0}, False, False, create_token)
        self.assertFalse(Corr.search([('work_date', '=', DAY)]))

        draft = Corr.tp_save_and_submit(vals, False, False, create_token)
        self.assertEqual(draft, Corr.tp_save_and_submit(vals, False, False, create_token))
        edited = dict(vals, reason='Synthetic updated explanation', requested_out=1.5)
        with self.assertRaisesRegex(UserError, 'đã được ghi nhận'):
            Corr.tp_save_and_submit(edited, False, True, create_token)
        with self.assertRaisesRegex(UserError, 'giải trình'):
            Corr.tp_save_and_submit(dict(edited, reason=''), draft['id'], True, submit_token)
        record = Corr.browse(draft['id'])
        self.assertEqual((record.state, record.requested_out), ('draft', 1.0))

        submitted = Corr.tp_save_and_submit(edited, record.id, True, submit_token)
        self.assertEqual((submitted['id'], submitted['state']), (record.id, 'submitted'))
        self.assertEqual(submitted, Corr.tp_save_and_submit(edited, record.id, True, submit_token))
        self.assertEqual((record.requested_in, record.requested_out), (0.0, 1.5))
        with self.assertRaisesRegex(UserError, 'đã được ghi nhận'):
            Corr.tp_save_and_submit(dict(edited, requested_out=2.0), record.id, True, submit_token)

        self.as_user(self.root, record).action_approve()
        self.assertEqual(Corr.tp_save_and_submit(edited, record.id, True, submit_token)['state'], 'approved')
        self.assertEqual(Corr.tp_save_and_submit(vals, False, False, create_token)['id'], record.id)
        self.assertEqual(Corr.search_count([('work_date', '=', DAY)]), 1)

        other = self.env_for(self.colleague)['tp.hr.attendance.correction']
        with self.assertRaises(AccessError):
            other.tp_save_and_submit(edited, record.id, True, submit_token)
        self.assertNotEqual(other.tp_save_and_submit(vals, False, False, create_token)['id'], record.id)

    def test_one_click_submit_retry_after_withdrawal_keeps_one_private_request(self):
        Corr = self.env_for(self.viewer)['tp.hr.attendance.correction']
        vals = {'work_date': DAY, 'requested_in': 8.0, 'requested_out': 17.0, 'reason': 'Synthetic correction'}
        token = '0123456789abcdef'
        result = Corr.tp_save_and_submit(vals, False, True, token)
        record = Corr.browse(result['id'])
        self.assertEqual(result, Corr.tp_save_and_submit(vals, False, True, token))
        self.assign()
        reason = 'Private withdrawal basis'
        record.action_withdraw(reason)
        self.assertEqual(record.withdraw_reason, reason)
        officer = self.env_for(self.officer)
        log = officer['tp.hr.attendance.log'].search([
            ('model', '=', record._name), ('res_id', '=', record.id), ('action', '=', 'correction_withdraw'),
        ])
        self.assertEqual(len(log), 1)
        self.assertNotIn(reason, log.detail)
        with self.assertRaises(AccessError):
            officer[record._name].browse(record.id).read(['withdraw_reason'])
        replay = Corr.tp_save_and_submit(vals, False, True, token)
        self.assertEqual((replay['id'], replay['state']), (record.id, 'withdrawn'))
        self.assertEqual(Corr.search_count([('work_date', '=', DAY)]), 1)
