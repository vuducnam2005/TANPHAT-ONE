"""ENTI-LIVE-001 / ENTI-ATTENDANCE-002: projection of one stored ENTI day into the canonical attendance board.

Covers the real ``tp.hr.attendance.enti.day`` API (synthetic people and hours only):
- ``_parse_time_str``: local clock → (HH:MM, naive UTC) and empty values → ("", False).
- A full in/out pair gives one active ENTI session and an "ok" day; in-only / out-only days are "missing" and never
  get an invented session or a 17:00 out time.
- Priority: approved correction > ENTI > Excel; a locked period is never rewritten.
- Re-projecting unchanged values writes nothing (no version bump, no duplicate session).
The HTTP client and the full sync pass are covered with fakes in ``test_enti_attendance_002``.
"""
from datetime import date, datetime, timedelta

from odoo.tests import tagged
from odoo.tests.common import BaseCase

from .common import AttendanceCase, report
from odoo.addons.tp_hr_attendance.models.attendance_common import DEFAULT_TZ, internal
from odoo.addons.tp_hr_attendance.models.enti_day import _parse_time_str

MONDAY = date(2026, 11, 9)


class TestEntiParse(BaseCase):
    def test_parse_time_str(self):
        day = date(2026, 11, 18)
        # 08:15 in Asia/Ho_Chi_Minh (UTC+7) is 01:15 UTC, stored naive like every Odoo datetime.
        self.assertEqual(_parse_time_str("08:15", day, "Asia/Ho_Chi_Minh"), ("08:15", datetime(2026, 11, 18, 1, 15)))
        self.assertEqual(_parse_time_str("08:15:30", day), ("08:15", datetime(2026, 11, 18, 1, 15, 30)))
        self.assertEqual(_parse_time_str("2026-11-18T17:05:00", day), ("17:05", datetime(2026, 11, 18, 10, 5)))
        for empty in (None, "", "   ", "null", "None", "-"):
            self.assertEqual(_parse_time_str(empty, day), ("", False), empty)
        # An unreadable value is never turned into a moment (so it never counts as a punch).
        self.assertIs(_parse_time_str("invalid", day)[1], False)


@tagged('post_install', '-at_install')
class TestEntiProjection(AttendanceCase):
    def setUp(self):
        super().setUp()
        self.source = internal(self.env['tp.hr.attendance.source']).create({
            'name': 'Synthetic ENTI projection', 'namespace': 'synthetic-enti-projection',
            'kind': 'enti_api', 'company_id': self.company.id, 'timezone': DEFAULT_TZ, 'state': 'ready',
            'live_enabled': True})
        self.EntiDay = self.env['tp.hr.attendance.enti.day'].sudo()
        self.Session = self.env['tp.hr.attendance.session'].sudo()

    def enti_day(self, employee, work_date, clock_in, clock_out, key='synthetic-key-a'):
        vals = {'source_id': self.source.id, 'key_nv': key, 'work_date': work_date, 'employee_id': employee.id}
        for text_field, moment_field, clock in (('vao_dau', 'check_in_dt', clock_in), ('ra_cuoi', 'check_out_dt', clock_out)):
            vals[text_field], vals[moment_field] = _parse_time_str(clock, work_date)
        return self.EntiDay.create(vals)

    def sessions(self, employee, work_date, **extra):
        return self.Session.with_context(**extra).search([('employee_id', '=', employee.id), ('work_date', '=', work_date)])

    def test_full_pair_projects_one_enti_session_and_is_idempotent(self):
        work_date = date(2026, 11, 18)
        record = self.enti_day(self.emp_a, work_date, '08:00', '17:30')
        self.assertTrue(record._tp_project_to_canonical())
        day = self.day(self.emp_a, work_date)
        self.assertEqual((day.source_kind, day.in_time, day.out_time, day.data_state, day.session_count),
                         ('enti', '08:00', '17:30', 'ok', 1))
        self.assertAlmostEqual(day.recorded_hours, 9.5)
        session = self.sessions(self.emp_a, work_date)
        self.assertEqual((len(session), session.source, session.day_id), (1, 'enti', day))
        self.assertGreater(session.check_out, session.check_in)
        self.assertEqual(record.state, 'applied')

        version = day.version
        self.assertFalse(record._tp_project_to_canonical(), 'unchanged ENTI values never rewrite the day')
        day.invalidate_recordset()
        self.assertEqual(day.version, version)
        self.assertEqual(len(self.day(self.emp_a, work_date)), 1)
        self.assertEqual(len(self.sessions(self.emp_a, work_date)), 1)

    def test_in_only_and_out_only_are_missing_without_invented_session(self):
        in_only, out_only = date(2026, 11, 17), date(2026, 11, 16)
        self.enti_day(self.emp_a, in_only, '08:15', None)._tp_project_to_canonical()
        self.enti_day(self.emp_a, out_only, None, '17:45')._tp_project_to_canonical()
        first = self.day(self.emp_a, in_only)
        self.assertEqual((first.in_time, first.out_time, first.data_state, first.session_count, first.recorded_hours),
                         ('08:15', '', 'missing', 0, 0.0))
        self.assertTrue(first.first_in)
        self.assertFalse(first.last_out, 'no 17:00 or other out time is invented')
        second = self.day(self.emp_a, out_only)
        self.assertEqual((second.in_time, second.out_time, second.data_state), ('', '17:45', 'missing'))
        self.assertFalse(self.sessions(self.emp_a, in_only) | self.sessions(self.emp_a, out_only))

        # The out punch arrives later: the same ENTI day now gives one full session.
        record = self.EntiDay.search([('source_id', '=', self.source.id), ('work_date', '=', in_only)])
        clock, moment = _parse_time_str('17:10', in_only)
        record.write({'ra_cuoi': clock, 'check_out_dt': moment})
        self.assertTrue(record._tp_project_to_canonical())
        first.invalidate_recordset()
        self.assertEqual((first.out_time, first.data_state, first.session_count), ('17:10', 'ok', 1))
        self.assertEqual(len(self.sessions(self.emp_a, in_only)), 1)

    def test_enti_replaces_excel_session_without_double_counting(self):
        self.run_batch(report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05')]}], MONDAY, 1))
        excel = self.sessions(self.emp_a, MONDAY)
        self.assertEqual(excel.source, 'import')
        self.enti_day(self.emp_a, MONDAY, '07:40', '17:06')._tp_project_to_canonical()
        active = self.sessions(self.emp_a, MONDAY)
        self.assertEqual((len(active), active.source), (1, 'enti'))
        excel.invalidate_recordset()
        self.assertFalse(excel.active)
        self.assertIn('ENTI', excel.superseded_reason)
        day = self.day(self.emp_a, MONDAY)
        self.assertEqual((day.source_kind, day.in_time, day.out_time), ('enti', '07:40', '17:06'))

    def test_approved_correction_and_locked_period_win_over_enti(self):
        corrected, locked = date(2026, 11, 12), date(2026, 11, 13)
        correction = self.env_for(self.viewer)['tp.hr.attendance.correction'].create({
            'work_date': corrected, 'requested_in': 8.0, 'requested_out': 17.0, 'reason': 'Synthetic reason'})
        # The approval itself is covered in test_correction; here only its outcome matters.
        internal(correction).write({'state': 'approved'})
        record = self.enti_day(self.emp_a, corrected, '09:00', '18:00')
        self.assertFalse(record._tp_project_to_canonical())
        self.assertEqual(record.state, 'superseded_correction')
        self.assertFalse(self.sessions(self.emp_a, corrected).filtered(lambda s: s.source == 'enti'))

        period = self.env['tp.hr.attendance.period'].sudo().create({
            'name': 'Synthetic locked', 'company_id': self.company.id, 'date_from': locked, 'date_to': locked})
        internal(period).write({'state': 'locked'})
        record = self.enti_day(self.emp_a, locked, '08:00', '17:00')
        self.assertFalse(record._tp_project_to_canonical())
        self.assertEqual(record.state, 'locked_period')
        self.assertFalse(self.day(self.emp_a, locked))
        self.assertFalse(self.sessions(self.emp_a, locked))

    def test_unmapped_day_waits_for_mapping(self):
        record = self.EntiDay.create({'source_id': self.source.id, 'key_nv': 'synthetic-unmapped',
                                      'work_date': MONDAY + timedelta(days=1), 'vao_dau': '08:00'})
        self.assertFalse(record._tp_project_to_canonical())
        self.assertEqual(record.state, 'pending_map')
