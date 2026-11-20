"""HR-ATTENDANCE-001 import: preview → apply, dedup across sheets/files, conflicts and half-punches never overwrite."""
from datetime import date, datetime, timedelta

from odoo.tests import tagged

from .common import AttendanceCase, report
from odoo.addons.tp_hr_attendance.models.attendance_common import internal

MONDAY = date(2026, 11, 9)


@tagged('post_install', '-at_install')
class TestAttendanceImport(AttendanceCase):
    def test_duplicate_sheets_and_reimport_never_double_count(self):
        people = [
            {'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05'), ('07:50', '17:00')]},
            {'code': '992', 'name': 'SYNTHETIC NGUOI HAI', 'times': [('08:00', '17:30'), (None, None)]},
        ]
        data = report(people, MONDAY, 2, sheets=('Tuần 1', 'Tuan 2'))
        batch = self.batch(data)
        batch._tp_read_file()
        self.assertEqual(batch.state, 'preview')
        self.assertEqual((batch.line_count, batch.valid_count, batch.duplicate_count), (6, 3, 3))
        self.assertEqual(batch.empty_count, 2)
        self.assertFalse(self.env['tp.hr.attendance.session'].sudo().search([('employee_id', 'in', (self.emp_a + self.emp_b).ids)]))
        batch._tp_apply_file()
        sessions = self.env['tp.hr.attendance.session'].sudo().search([('employee_id', 'in', (self.emp_a + self.emp_b).ids)])
        self.assertEqual(len(sessions), 3)
        self.assertEqual(batch.applied_count, 3)
        # Applying again (double click / retry) changes nothing.
        batch._tp_apply_file()
        self.assertEqual(self.env['tp.hr.attendance.session'].sudo().search_count([('id', 'not in', sessions.ids), ('employee_id', 'in', (self.emp_a + self.emp_b).ids)]), 0)
        # The same file in a new batch is recognised and only produces duplicates.
        again = self.batch(data, name='Synthetic batch again')
        again._tp_read_file()
        self.assertEqual(again.same_file_batch_id, batch)
        self.assertEqual((again.valid_count, again.duplicate_count), (0, 6))
        again._tp_apply_file()
        self.assertEqual(self.env['tp.hr.attendance.session'].sudo().search_count([('employee_id', 'in', (self.emp_a + self.emp_b).ids)]), 3)
        # No employee was created or renamed by the import; codes were mapped automatically.
        self.assertEqual(self.emp_b.name, 'Synthetic Người Hai')
        codes = self.env['tp.hr.attendance.code'].sudo().search([('company_id', '=', self.company.id)])
        self.assertEqual(set(codes.mapped('machine_code')), {'991', '992'})
        self.assertEqual(set(codes.mapped('source')), {'auto'})

    def test_times_are_utc_and_workday_is_local(self):
        self.run_batch(report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05')]}], MONDAY, 1))
        session = self.env['tp.hr.attendance.session'].sudo().search([('employee_id', '=', self.emp_a.id)])
        self.assertEqual(session.check_in, datetime(2026, 11, 9, 0, 37))
        self.assertEqual(session.check_out, datetime(2026, 11, 9, 10, 5))
        self.assertEqual(session.work_date, MONDAY)
        self.assertAlmostEqual(session.worked_hours, 9.47, places=2)
        day = self.day(self.emp_a, MONDAY)
        self.assertEqual((day.in_time, day.out_time, day.data_state), ('07:37', '17:05', 'ok'))
        self.assertEqual(day.employee_code, self.emp_a.tp_employee_code)
        self.assertEqual(day.department_id, self.dept)

    def test_conflict_is_kept_for_correction_not_overwritten(self):
        self.run_batch(report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05')]}], MONDAY, 1))
        second = self.run_batch(report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:40', '17:10')]}], MONDAY, 1))
        line = self.lines(second)
        self.assertEqual(line.state, 'conflict')
        self.assertTrue(line.issue_open)
        sessions = self.env['tp.hr.attendance.session'].sudo().search([('employee_id', '=', self.emp_a.id)])
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions.check_in, datetime(2026, 11, 9, 0, 37))
        day = self.day(self.emp_a, MONDAY)
        self.assertEqual(day.data_state, 'review')
        self.assertEqual(day.in_time, '07:37')

    def test_unmapped_and_name_mismatch_never_create_employees(self):
        before = self.env['hr.employee'].sudo().with_context(active_test=False).search_count([])
        batch = self.run_batch(report([
            {'code': '9990', 'name': 'Synthetic Không Có', 'times': [('07:30', '17:00')]},
            {'code': '992', 'name': 'Synthetic Tên Khác', 'times': [('07:30', '17:00')]},
            {'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:30', '17:00')]},
        ], MONDAY, 1))
        self.assertEqual(self.lines(batch, machine_code='9990').state, 'unmapped')
        # The form's attention tab lists only lines HR still has to resolve, never applied ones.
        self.assertEqual(set(batch.sudo().attention_line_ids.mapped('state')), {'unmapped', 'name_conflict'})
        self.assertEqual(self.lines(batch, machine_code='991').state, 'applied')
        mismatch = self.lines(batch, machine_code='992')
        self.assertEqual(mismatch.state, 'name_conflict')
        self.assertEqual(mismatch.candidate_employee_id, self.emp_b)
        self.assertFalse(mismatch.employee_id)
        self.assertEqual(self.env['hr.employee'].sudo().with_context(active_test=False).search_count([]), before)
        self.assertFalse(self.env['tp.hr.attendance.session'].sudo().search([('employee_id', '=', self.emp_b.id)]))
        self.assertFalse(self.env['tp.hr.attendance.code'].sudo().search([('machine_code', 'in', ('9990', '992')), ('company_id', '=', self.company.id)]))

    def test_half_punch_waits_then_completes_with_matching_pair(self):
        first = self.run_batch(report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', None)]}], MONDAY, 1))
        line = self.lines(first)
        self.assertEqual((line.kind, line.state, line.issue_open), ('missing_out', 'missing', True))
        day = self.day(self.emp_a, MONDAY)
        self.assertEqual((day.data_state, day.in_time, day.out_time, day.session_count), ('missing', '07:37', False, 0))
        self.assertEqual(day.units_state, 'unconfirmed')
        second = self.run_batch(report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05')]}], MONDAY, 1))
        self.assertEqual(self.lines(second).state, 'applied')
        self.assertFalse(line.issue_open)
        self.assertEqual(line.resolved_by_line_id, self.lines(second))
        day.invalidate_recordset()
        self.assertEqual((day.data_state, day.in_time, day.out_time, day.session_count), ('ok', '07:37', '17:05', 1))
        self.assertGreater(day.version, 1)

    def test_code_cells_stay_private_and_need_review(self):
        batch = self.run_batch(report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [('P', 'P')]}], MONDAY, 1))
        line = self.lines(batch)
        self.assertEqual((line.kind, line.state), ('code', 'review'))
        day = self.day(self.emp_a, MONDAY)
        self.assertEqual(day.data_state, 'review')
        self.assertFalse(day.in_time)
        self.assertFalse(day.out_time)

    def test_units_need_a_confirmed_rule(self):
        self.run_batch(report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05'), ('08:30', '12:30')]}], MONDAY, 2))
        day = self.day(self.emp_a, MONDAY)
        self.assertEqual(day.units_state, 'unconfirmed')
        self.assertEqual(day.units_display, 'Chưa xác nhận')
        Rule = self.env_for(self.manager)['tp.hr.attendance.rule']
        rule = Rule.create({'name': 'Synthetic office hours', 'company_id': self.company.id, 'date_from': date(2026, 11, 1)})
        self.assertEqual(day.units_state, 'unconfirmed')
        rule.action_confirm()
        day.invalidate_recordset()
        self.assertEqual((day.units_state, day.scheduled_hours, day.units), ('confirmed', 8.0, 1.0))
        tuesday = self.day(self.emp_a, MONDAY + timedelta(days=1))
        self.assertEqual((tuesday.scheduled_hours, tuesday.units), (3.5, 0.44))
        rule.action_reset()
        day.invalidate_recordset()
        self.assertEqual(day.units_state, 'unconfirmed')

    def test_locked_period_rejects_new_lines(self):
        Period = self.env['tp.hr.attendance.period'].sudo()
        period = Period.create({'name': 'Synthetic locked', 'company_id': self.company.id, 'date_from': MONDAY, 'date_to': MONDAY})
        internal(period).write({'state': 'locked'})
        batch = self.run_batch(report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05')]}], MONDAY, 1))
        self.assertEqual(self.lines(batch).state, 'locked')
        self.assertFalse(self.env['tp.hr.attendance.session'].sudo().search([('employee_id', '=', self.emp_a.id)]))

    def test_board_month_and_day(self):
        self.run_batch(report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05'), (None, None)]},
                               {'code': '992', 'name': 'Synthetic Người Hai', 'times': [(None, None), ('07:45', None)]}], MONDAY, 2))
        Day = self.env_for(self.viewer)['tp.hr.attendance.day'].with_company(self.company)
        board = Day.tp_board({'mode': 'month', 'month': '2026-11', 'page_size': 50})
        self.assertEqual(len(board['dates']), 30)
        rows = {row['id']: row for row in board['rows']}
        self.assertIn(self.emp_a.id, rows)
        cells = {cell['date']: cell for cell in rows[self.emp_a.id]['cells']}
        self.assertEqual(cells['2026-11-09']['state'], 'ok')
        self.assertEqual(cells['2026-11-10']['state'], 'no_punch')
        self.assertEqual(cells['2026-11-01']['state'], 'no_source')
        colleague = {cell['date']: cell for cell in rows[self.emp_b.id]['cells']}
        self.assertEqual(colleague['2026-11-10']['state'], 'missing')
        self.assertEqual(colleague['2026-11-10']['in_time'], '07:45')
        self.assertIsNone(rows[self.emp_a.id]['totals']['units'])
        self.assertFalse(board['processor'])
        self.assertFalse(board['can_import'])
        self.assertEqual(board['batches'], [])
        day = Day.tp_board({'mode': 'day', 'date': '2026-11-10', 'state': 'missing'})
        self.assertEqual([row['id'] for row in day['rows']], [self.emp_b.id])
        self.assertEqual(day['updated']['to'], '10/11/2026')
