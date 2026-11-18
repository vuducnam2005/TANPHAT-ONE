"""HR-ATTENDANCE-SIMPLE-002 pure rules (no database): periods, machine late totals, presence, events, export."""
from datetime import date, datetime
from io import BytesIO

from openpyxl import load_workbook

from odoo.tests import BaseCase, tagged

from odoo.addons.tp_hr_attendance.models.attendance_logic import (
    EventError,
    build_xlsx,
    day_label,
    fingerprint,
    late_cover,
    month_range,
    normalize_event,
    period_range,
    presence_from_day,
    presence_from_events,
    short_range,
    week_range,
    xlsx_safe,
)

MONDAY = date(2026, 11, 9)


def total(start, end, count, minutes):
    return {'date_from': start, 'date_to': end, 'count': count, 'minutes': minutes}


@tagged('post_install', '-at_install')
class TestAttendanceLogic(BaseCase):
    def test_periods_week_is_monday_to_sunday_and_months_cross_years(self):
        self.assertEqual(week_range(date(2026, 11, 15)), (MONDAY, date(2026, 11, 15)))
        self.assertEqual(week_range(MONDAY), (MONDAY, date(2026, 11, 15)))
        self.assertEqual(week_range(date(2027, 1, 1)), (date(2026, 12, 28), date(2027, 1, 3)))
        self.assertEqual(month_range(date(2028, 2, 10)), (date(2028, 2, 1), date(2028, 2, 29)))
        self.assertEqual(month_range(date(2026, 12, 31)), (date(2026, 12, 1), date(2026, 12, 31)))
        self.assertEqual(period_range('day', MONDAY), (MONDAY, MONDAY))
        self.assertEqual(day_label(MONDAY), 'T2 09/11/2026')
        self.assertEqual(day_label(date(2026, 11, 15)), 'CN 15/11/2026')

    def test_short_range_labels(self):
        self.assertEqual(short_range(MONDAY, date(2026, 11, 15)), '09–15/11')
        self.assertEqual(short_range(date(2026, 10, 26), date(2026, 11, 1)), '26/10–01/11')
        self.assertEqual(short_range(date(2026, 12, 28), date(2027, 1, 3)), '28/12/2026–03/01/2027')
        self.assertEqual(short_range(MONDAY, MONDAY), '09/11')

    def test_late_exact_period_is_kept_as_given(self):
        week = total(MONDAY, date(2026, 11, 15), 3, 47)
        result = late_cover([week], MONDAY, date(2026, 11, 15))
        self.assertEqual((result['state'], result['count'], result['minutes']), ('exact', 3, 47))
        self.assertEqual([piece['label'] for piece in result['pieces']], ['09–15/11'])

    def test_late_day_or_partial_range_is_never_zero_or_split(self):
        week = total(MONDAY, date(2026, 11, 15), 3, 47)
        for start, end in ((MONDAY, MONDAY), (date(2026, 11, 10), date(2026, 11, 12))):
            result = late_cover([week], start, end)
            self.assertEqual(result['state'], 'none')
            self.assertIsNone(result['count'])
            self.assertEqual([hint['label'] for hint in result['hints']], ['09–15/11'])
        # A month that only contains one weekly file has no exact total either (no guessing for other weeks).
        month = late_cover([week], date(2026, 11, 1), date(2026, 11, 30))
        self.assertEqual(month['state'], 'none')
        self.assertEqual(month['hints'][0]['from'], '2026-11-09')

    def test_late_multi_period_only_from_exact_tiling(self):
        first = total(date(2026, 11, 2), date(2026, 11, 8), 1, 5)
        second = total(MONDAY, date(2026, 11, 15), 2, 20)
        tiled = late_cover([first, second], date(2026, 11, 2), date(2026, 11, 15))
        self.assertEqual((tiled['state'], tiled['count'], tiled['minutes']), ('exact', 3, 25))
        self.assertEqual(len(tiled['pieces']), 2)
        gap = late_cover([first, total(date(2026, 11, 10), date(2026, 11, 15), 2, 20)], date(2026, 11, 2), date(2026, 11, 15))
        self.assertEqual(gap['state'], 'none')
        overlap = late_cover([first, total(date(2026, 11, 7), date(2026, 11, 15), 2, 20)], date(2026, 11, 2), date(2026, 11, 15))
        self.assertEqual(overlap['state'], 'none')

    def test_late_month_never_adds_the_week_inside_it(self):
        month = total(date(2026, 11, 1), date(2026, 11, 30), 9, 120)
        week = total(MONDAY, date(2026, 11, 15), 3, 47)
        result = late_cover([month, week], date(2026, 11, 1), date(2026, 11, 30))
        self.assertEqual((result['state'], result['count'], result['minutes']), ('exact', 9, 120))
        week_view = late_cover([month, week], MONDAY, date(2026, 11, 15))
        self.assertEqual((week_view['state'], week_view['count']), ('exact', 3))

    def test_late_conflicting_tilings_are_reported(self):
        a = total(MONDAY, date(2026, 11, 15), 3, 47)
        b = total(MONDAY, date(2026, 11, 15), 4, 50)
        result = late_cover([a, b], MONDAY, date(2026, 11, 15))
        self.assertEqual(result['state'], 'conflict')
        self.assertIsNone(result['count'])
        same = late_cover([a, dict(a)], MONDAY, date(2026, 11, 15))
        self.assertEqual((same['state'], same['count']), ('exact', 3))

    def test_presence_from_events(self):
        def at(hour, minute=0):
            return datetime(2026, 11, 9, hour, minute)

        self.assertEqual(presence_from_events([], True), 'no_punch')
        self.assertEqual(presence_from_events([{'at': at(1), 'direction': 'IN'}], True), 'working')
        self.assertEqual(presence_from_events([{'at': at(1), 'direction': 'IN'}], False), 'missing')
        lunch = [{'at': at(1), 'direction': 'IN'}, {'at': at(5), 'direction': 'OUT'}, {'at': at(6), 'direction': 'IN'}]
        self.assertEqual(presence_from_events(lunch, True), 'working')
        self.assertEqual(presence_from_events([*lunch, {'at': at(10), 'direction': 'OUT'}], True), 'out_recorded')
        self.assertEqual(presence_from_events([{'at': at(10), 'direction': 'OUT'}], True), 'review')
        self.assertEqual(presence_from_events([{'at': at(1), 'direction': 'UNKNOWN'}], True), 'review')

    def test_presence_from_imported_day_never_invents_an_out_time(self):
        self.assertEqual(presence_from_day('ok', '07:37', '17:05', False), 'out_recorded')
        self.assertEqual(presence_from_day('missing', '07:37', '', True), 'working')
        self.assertEqual(presence_from_day('missing', '07:37', '', False), 'missing')
        self.assertEqual(presence_from_day('missing', '', '17:05', False), 'missing')
        self.assertEqual(presence_from_day('conflict', '07:37', '17:05', False), 'review')

    def test_normalize_event_keeps_codes_and_converts_to_utc(self):
        event = normalize_event({'external_code': '0042', 'timestamp': '2026-11-09T07:37:00', 'direction': 'in'}, 'may-1')
        self.assertEqual(event['external_code'], '0042')
        self.assertEqual(event['timestamp'], datetime(2026, 11, 9, 0, 37))
        self.assertEqual(event['local_date'], MONDAY)
        self.assertEqual(event['direction'], 'IN')
        late_night = normalize_event({'external_code': '7', 'timestamp': '2026-11-09T23:30:00+07:00', 'direction': 'OUT'}, 'may-1')
        self.assertEqual(late_night['local_date'], MONDAY)
        odd = normalize_event({'external_code': '7', 'timestamp': '2026-11-09T08:00:00Z', 'direction': 'swipe'}, 'may-1')
        self.assertEqual(odd['direction'], 'UNKNOWN')
        for raw in ({'external_code': 42.0, 'timestamp': '2026-11-09T07:37:00'},
                    {'external_code': 'a b', 'timestamp': '2026-11-09T07:37:00'},
                    {'external_code': '42', 'timestamp': '09/11/2026 07:37'},
                    {'external_code': '42', 'timestamp': '2026-11-09T07:37:00', 'tz': 'Mars/Base'}):
            with self.assertRaises(EventError):
                normalize_event(raw, 'may-1')
        with self.assertRaises(EventError):
            normalize_event({'external_code': '42', 'timestamp': '2026-11-09T07:37:00'}, '')

    def test_fingerprint_dedupes_inside_a_namespace_only(self):
        raw = {'external_code': '0042', 'timestamp': '2026-11-09T07:37:00', 'direction': 'IN'}
        first, again = normalize_event(raw, 'may-1'), normalize_event(dict(raw), 'may-1')
        self.assertEqual(fingerprint(first), fingerprint(again))
        self.assertNotEqual(fingerprint(first), fingerprint(normalize_event(raw, 'may-2')))
        with_id = normalize_event(dict(raw, event_id='E-1'), 'may-1')
        moved = normalize_event(dict(raw, event_id='E-1', timestamp='2026-11-09T07:38:00'), 'may-1')
        self.assertEqual(fingerprint(with_id), fingerprint(moved))

    def test_export_is_formula_safe(self):
        self.assertEqual(xlsx_safe('=HYPERLINK("x")'), '\'=HYPERLINK("x")')
        self.assertEqual(xlsx_safe('-1+2'), "'-1+2")
        self.assertEqual(xlsx_safe(5), 5)
        self.assertEqual(xlsx_safe(None), '')
        content = build_xlsx([
            {'title': 'Theo ngày', 'note': 'Synthetic', 'header': ['Nhân viên', 'Giờ vào'], 'rows': [['=cmd', '07:37']]},
            {'title': 'Tổng đi muộn', 'note': '', 'header': ['Nhân viên', 'Số lần'], 'rows': [['Synthetic', 3]]},
        ])
        book = load_workbook(BytesIO(content))
        self.assertEqual(book.sheetnames, ['Theo ngày', 'Tổng đi muộn'])
        self.assertEqual(book['Theo ngày'].cell(3, 1).value, "'=cmd")
        self.assertEqual(book['Tổng đi muộn'].cell(3, 2).value, 3)
