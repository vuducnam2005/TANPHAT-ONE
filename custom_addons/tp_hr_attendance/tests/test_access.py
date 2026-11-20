"""HR-ATTENDANCE-001 access: everybody reads the board, nobody edits hours, staging stays with assigned processors."""
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import AttendanceCase, report
from odoo.addons.tp_hr_attendance.models.attendance_common import can

MONDAY = date(2026, 11, 9)


@tagged('post_install', '-at_install')
class TestAttendanceAccess(AttendanceCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = report([
            {'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05')]},
            {'code': '992', 'name': 'Synthetic Người Hai', 'times': [('08:00', '12:00')]},
        ], MONDAY, 1)

    def setUp(self):
        super().setUp()
        self.applied = self.run_batch(self.data)
        self.day_a = self.day(self.emp_a, MONDAY)
        self.day_b = self.day(self.emp_b, MONDAY)

    def test_viewer_reads_shared_board_but_cannot_change_hours(self):
        env = self.env_for(self.viewer)
        Day, Session = env['tp.hr.attendance.day'], env['tp.hr.attendance.session']
        self.assertEqual(set(Day.search([('work_date', '=', MONDAY)]).ids), {self.day_a.id, self.day_b.id})
        colleague = Day.browse(self.day_b.id)
        self.assertEqual(colleague.in_time, '08:00')
        self.assertEqual((colleague.out_time, colleague.data_state), ('12:00', 'ok'))
        for operation in ('create', 'write', 'unlink'):
            self.assertFalse(Day.has_access(operation), operation)
            self.assertFalse(Session.has_access(operation), operation)
        with self.assertRaises(AccessError):
            Day.browse(self.day_a.id).write({'in_time': '07:00'})
        with self.assertRaises(AccessError):
            Day.browse(self.day_a.id).unlink()
        with self.assertRaises(AccessError):
            Session.create({'employee_id': self.emp_a.id, 'company_id': self.company.id, 'work_date': MONDAY,
                            'check_in': '2026-11-09 01:00:00', 'check_out': '2026-11-09 02:00:00'})
        own = Session.search([('employee_id', '=', self.emp_a.id)])
        self.assertEqual(len(own), 1)
        with self.assertRaises(AccessError):
            own.write({'check_out': '2026-11-09 11:00:00'})
        # Staging lineage and private processing data stay hidden.
        with self.assertRaises(AccessError):
            own.read(['batch_id'])
        with self.assertRaises(AccessError):
            own.read(['line_id'])
        with self.assertRaises(AccessError):
            colleague.read(['issue_ids'])
        for model in ('tp.hr.attendance.batch', 'tp.hr.attendance.line', 'tp.hr.attendance.log', 'tp.hr.attendance.code'):
            with self.assertRaises(AccessError, msg=model):
                env[model].search([])

    def test_export_only_own_rows_for_viewer(self):
        # Native export already needs base.group_allow_export; the attendance guard narrows it further.
        allow_export = self.env.ref('base.group_allow_export')
        (self.viewer | self.manager).write({'group_ids': [Command.link(allow_export.id)]})
        Day = self.env_for(self.viewer)['tp.hr.attendance.day']
        exported = Day.browse(self.day_a.id).export_data(['work_date', 'in_time'])
        self.assertEqual(exported['datas'][0][1], '07:37')
        for field in ('employee_id/parent_id/work_email', 'employee_id.parent_id.work_email',
                      'employee_id', 'issue_ids/message', 'create_uid/login', 'unknown_field'):
            with self.assertRaises(AccessError, msg=field):
                Day.browse(self.day_a.id).export_data([field])
        own_sessions = self.env_for(self.viewer)['tp.hr.attendance.session'].search([('employee_id', '=', self.emp_a.id)])
        self.assertTrue(own_sessions.export_data(['check_in'])['datas'])
        with self.assertRaises(AccessError):
            own_sessions.export_data(['employee_id/parent_id/work_email'])
        with self.assertRaises(AccessError):
            Day.browse([self.day_a.id, self.day_b.id]).export_data(['work_date'])
        colleague_sessions = self.env_for(self.viewer)['tp.hr.attendance.session'].search([('employee_id', '=', self.emp_b.id)])
        self.assertEqual(len(colleague_sessions), 1)
        with self.assertRaises(AccessError):
            colleague_sessions.export_data(['check_in'])
        manager_rows = self.env_for(self.manager)['tp.hr.attendance.day'].browse([self.day_a.id, self.day_b.id]).export_data(['work_date'])
        self.assertEqual(len(manager_rows['datas']), 2)

    def test_own_csv_ignores_forged_employee_and_fields(self):
        Day = self.env_for(self.viewer)['tp.hr.attendance.day']
        result = Day.tp_export_my_attendance({'month': '2026-11', 'employee_id': self.emp_b.id,
                                             'fields': ['requests', 'reason'], 'state': 'ok'})
        self.assertIn('07:37', result['content'])
        self.assertNotIn('08:00', result['content'])
        self.assertEqual(result['filename'], 'cong-cua-toi-2026-11.csv')
        with self.assertRaises(UserError):
            Day.tp_export_my_attendance({'month': '2026-11', 'state': 'forged'})

    def test_viewer_cannot_import_or_tamper_with_batches(self):
        with self.assertRaises(AccessError):
            self.batch(self.data, user=self.viewer)
        with self.assertRaises(AccessError):
            self.env_for(self.viewer)['tp.hr.attendance.log'].sudo(False).create({'action': 'forged'})
        log = self.env['tp.hr.attendance.log'].sudo().search([('company_id', '=', self.company.id)], limit=1)
        self.assertTrue(log)
        with self.assertRaises(AccessError):
            log.write({'action': 'forged'})
        with self.assertRaises(AccessError):
            log.unlink()
        with self.assertRaises(AccessError):
            self.env_for(self.manager)['tp.hr.attendance.batch'].browse(self.applied.id).write({'state': 'draft'})

    def test_assignments_drive_officer_group_and_capabilities(self):
        officer_group = self.env.ref('tp_hr_attendance.group_attendance_officer')
        self.assertNotIn(self.officer, officer_group.user_ids)
        Assignment = self.env_for(self.manager)['tp.hr.attendance.assignment']
        review = Assignment.create({'user_id': self.officer.id, 'company_id': self.company.id, 'can_review': True,
                                    'department_ids': [(6, 0, self.dept.ids)]})
        self.assertIn(self.officer, officer_group.user_ids)
        officer_env = self.env_for(self.officer)
        self.assertTrue(can(officer_env, 'review', self.company, self.dept))
        self.assertFalse(can(officer_env, 'review', self.company, self.dept_other))
        self.assertFalse(can(officer_env, 'import', self.company))
        self.assertFalse(officer_env.user.has_group('hr.group_hr_user'))
        # Officers read staging but cannot import without an import assignment.
        self.assertTrue(officer_env['tp.hr.attendance.line'].search([('batch_id', '=', self.applied.id)]))
        with self.assertRaises(AccessError):
            self.batch(self.data, user=self.officer)
        menu_import = self.env.ref('tp_hr_attendance.menu_import').id
        self.assertNotIn(menu_import, officer_env['ir.ui.menu']._visible_menu_ids())
        review.write({'can_import': True, 'department_ids': [(5, 0, 0)]})
        officer_env = self.env_for(self.officer)
        self.assertTrue(can(officer_env, 'import', self.company))
        self.assertNotIn(menu_import, officer_env['ir.ui.menu']._visible_menu_ids(), 'Excel import has no menu entry')
        batch = self.batch(self.data, user=self.officer)
        batch._tp_read_file()
        self.assertEqual(batch.duplicate_count, 2)
        review.write({'active': False})
        self.assertNotIn(self.officer, officer_group.user_ids)
        # The HR manager imports without an assignment but is not a reviewer by title.
        manager_env = self.env_for(self.manager)
        self.assertTrue(can(manager_env, 'import', self.company))
        self.assertFalse(can(manager_env, 'review', self.company, self.dept))

    def test_officer_sync_keeps_admin_delegation_guard(self):
        """Assignments move members from the user side; the group member list and admin accounts stay guarded."""
        if 'tp.admin.delegation' not in self.env:
            self.skipTest('tp_admin_delegation is not installed')
        officer_group = self.env.ref('tp_hr_attendance.group_attendance_officer')
        with self.assertRaises(AccessError):
            self.env_for(self.manager)['res.groups'].sudo().browse(officer_group.id).write(
                {'user_ids': [Command.link(self.officer.id)]})
        self.assertNotIn(self.officer, officer_group.user_ids)
        admin = self.env['res.users'].create({
            'name': 'att001.synthetic.admin', 'login': 'att001.synthetic.admin', 'company_id': self.company.id,
            'company_ids': [Command.set([self.company.id])],
            'group_ids': [Command.set([self.env.ref('base.group_user').id, self.env.ref('base.group_system').id])],
        })
        Assignment = self.env_for(self.manager)['tp.hr.attendance.assignment']
        with self.assertRaises(AccessError) as caught:
            Assignment.create({'user_id': admin.id, 'company_id': self.company.id})
        self.assertIn('Không cập nhật được quyền Chấm công', str(caught.exception))
        self.assertFalse(self.env['tp.hr.attendance.assignment'].search([('user_id', '=', admin.id)]))
        self.assertNotIn(admin, officer_group.user_ids)
        # Removing a plain employee from the group through the assignment still works for HR.
        assignment = Assignment.create({'user_id': self.officer.id, 'company_id': self.company.id})
        self.assertIn(self.officer, officer_group.user_ids)
        assignment.unlink()
        self.assertNotIn(self.officer, officer_group.user_ids)

    def test_menus_follow_rights(self):
        def visible(user):
            return self.env_for(user)['ir.ui.menu']._visible_menu_ids()

        board = self.env.ref('tp_hr_attendance.menu_board').id
        menu_import = self.env.ref('tp_hr_attendance.menu_import').id
        config = self.env.ref('tp_hr_attendance.menu_rules').id
        viewer_menus = visible(self.viewer)
        self.assertNotIn(board, viewer_menus)
        self.assertNotIn(menu_import, viewer_menus)
        self.assertNotIn(config, viewer_menus)
        manager_menus = visible(self.manager)
        self.assertNotIn(board, manager_menus)
        self.assertNotIn(menu_import, manager_menus)
        self.assertIn(config, manager_menus)
        # Import UI is removed; historical data remains in the canonical export.
        self.assertFalse(self.env.ref('tp_hr_attendance.menu_file_matrix', raise_if_not_found=False))

    def test_rejects_non_excel_and_macro_files(self):
        batch = self.batch(b'not an excel file')
        with self.assertRaisesRegex(UserError, 'xlsx'):
            batch._tp_read_file()
        self.assertEqual(batch.state, 'draft')
