"""HR-ATTENDANCE-SIMPLE-002 parser: 1-3 week and 28-31 day files, month/year crossing, machine late group.

Workbooks are generated in memory with synthetic names and hours; no real export is read or stored.
"""
from datetime import date, timedelta

from odoo.tests import BaseCase, tagged

from .common import report
from odoo.addons.tp_hr_attendance.models.attendance_parser import parse_attendance

MONDAY = date(2026, 11, 9)


def person(code, days, late=None, **extra):
    times = [('07:3%d' % (offset % 10), '17:0%d' % (offset % 10)) if offset % 3 else (None, None) for offset in range(days)]
    return dict({'code': code, 'name': f'Synthetic {code}', 'times': times, 'late': late}, **extra)


@tagged('post_install', '-at_install')
class TestAttendanceParserPeriods(BaseCase):
    def test_week_multiples_and_month_lengths(self):
        cases = [(MONDAY, 7), (MONDAY, 14), (MONDAY, 21), (date(2027, 2, 1), 28), (date(2028, 2, 1), 29),
                 (date(2026, 11, 1), 30), (date(2026, 12, 1), 31)]
        for start, days in cases:
            with self.subTest(start=start, days=days):
                [sheet] = parse_attendance(report([person('9901', days)], start, days))
                self.assertEqual(sheet['errors'], [])
                self.assertEqual(sheet['period'], (start, start + timedelta(days=days - 1)))
                work_dates = sorted({event['work_date'] for event in sheet['events']})
                self.assertEqual(work_dates[0], start + timedelta(days=1))
                self.assertLessEqual(work_dates[-1], start + timedelta(days=days - 1))

    def test_month_and_year_crossing(self):
        for start, days in ((date(2026, 10, 26), 14), (date(2026, 12, 28), 7)):
            with self.subTest(start=start):
                [sheet] = parse_attendance(report([person('9901', days)], start, days))
                self.assertEqual(sheet['errors'], [])
                dates = {event['work_date'] for event in sheet['events']}
                self.assertTrue(any(day.month != start.month for day in dates))
                self.assertTrue(all(start <= day <= start + timedelta(days=days - 1) for day in dates))

    def test_multiple_sheets_are_read_separately(self):
        sheets = parse_attendance(report([person('9901', 7)], MONDAY, 7, sheets=('Tuần 1', 'Tuần 2')))
        self.assertEqual([sheet['name'] for sheet in sheets], ['Tuần 1', 'Tuần 2'])
        self.assertTrue(all(sheet['period'] == (MONDAY, MONDAY + timedelta(days=6)) for sheet in sheets))

    def test_empty_cell_is_not_leave_and_no_out_time_is_invented(self):
        people = [{'code': '9901', 'name': 'Synthetic A', 'times': [('07:37', None), (None, None), ('07:40', '17:05')]}]
        [sheet] = parse_attendance(report(people, MONDAY, 3))
        events = {event['work_date']: event for event in sheet['events']}
        self.assertEqual(events[MONDAY]['kind'], 'missing_out')
        self.assertIsNone(events[MONDAY]['clock_out'])
        self.assertNotIn(MONDAY + timedelta(days=1), events)
        self.assertEqual(sheet['empty_cells'], 1)
        self.assertEqual(events[MONDAY + timedelta(days=2)]['kind'], 'pair')

    def test_late_group_values_are_kept_exactly(self):
        people = [person('9901', 7, late=(3, 47)), person('9902', 7, late=(0, 0)), person('9903', 7, late=(None, None))]
        [sheet] = parse_attendance(report(people, MONDAY, 7, late=True))
        self.assertEqual(sheet['late']['state'], 'ok')
        self.assertEqual(sheet['late']['ref'], 'N6:O7')
        by_code = {row['machine_code']: row for row in sheet['people']}
        self.assertEqual((by_code['9901']['late_state'], by_code['9901']['late_count'], by_code['9901']['late_minutes']), ('ok', 3, 47))
        self.assertEqual((by_code['9902']['late_state'], by_code['9902']['late_count']), ('ok', 0))
        self.assertEqual(by_code['9903']['late_state'], 'empty')
        self.assertIsNone(by_code['9903']['late_count'])
        self.assertEqual(by_code['9901']['late_cell'], 'N9:O9')
        # The late columns are never read as day columns.
        self.assertTrue(all(event['column'] < 14 for event in sheet['events']))

    def test_late_invalid_and_inconsistent_values_are_not_guessed(self):
        people = [person('9901', 7, late=('ba', 47)), person('9902', 7, late=(0, 12)), person('9903', 7, late=(2, None)),
                  person('9904', 7, late=(1.5, 10))]
        [sheet] = parse_attendance(report(people, MONDAY, 7, late=True))
        states = {row['machine_code']: row['late_state'] for row in sheet['people']}
        self.assertEqual(states, {'9901': 'invalid', '9902': 'inconsistent', '9903': 'invalid', '9904': 'invalid'})
        raw = {row['machine_code']: row['late_raw_count'] for row in sheet['people']}
        self.assertEqual(raw['9901'], 'ba')

    def test_missing_ambiguous_or_partial_late_group(self):
        [plain] = parse_attendance(report([person('9901', 7)], MONDAY, 7))
        self.assertEqual(plain['late']['state'], 'no_column')
        self.assertIn('Chưa có số liệu', plain['late']['message'])
        self.assertNotIn('late_state', plain['people'][0])
        [twice] = parse_attendance(report([person('9901', 7, late=(1, 5))], MONDAY, 7, late=True, late_groups=2))
        self.assertEqual(twice['late']['state'], 'ambiguous')
        [partial] = parse_attendance(report([person('9901', 7, late=(1, 5))], MONDAY, 7, late=True, late_labels=('Lần', 'Ghi chú')))
        self.assertEqual(partial['late']['state'], 'partial')
        self.assertEqual(partial['errors'], [])
