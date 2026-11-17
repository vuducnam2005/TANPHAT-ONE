"""HR-ATTENDANCE-001 parser: values only, strict layout, private codes kept as review items."""
import zipfile
from datetime import date, time
from io import BytesIO

from odoo.tests import BaseCase, tagged

from .common import report
from odoo.addons.tp_hr_attendance.models.attendance_parser import (
    AttendanceFormatError,
    parse_attendance,
    read_clock,
)

MONDAY = date(2026, 11, 9)


@tagged('post_install', '-at_install')
class TestAttendanceParser(BaseCase):
    def test_read_clock(self):
        self.assertEqual(read_clock('07:37')[:2], (time(7, 37), 'time'))
        self.assertEqual(read_clock(' 7:05 ')[:2], (time(7, 5), 'time'))
        self.assertEqual(read_clock(time(17, 5))[:2], (time(17, 5), 'time'))
        self.assertEqual(read_clock(None)[1], 'empty')
        self.assertEqual(read_clock('')[1], 'empty')
        self.assertEqual(read_clock('P')[1], 'code')
        self.assertEqual(read_clock('07:37 17:05')[1], 'multi')
        self.assertEqual(read_clock('25:99')[1], 'invalid')

    def test_parse_report_kinds_and_dates(self):
        data = report([
            {'code': '9901', 'name': 'Synthetic A', 'times': [('07:37', '17:05'), ('07:40', None), ('17:00', '08:00')]},
            {'code': '', 'name': 'Synthetic No Code', 'times': [('07:30', '17:00'), (None, None), (None, None)]},
        ], MONDAY, 3)
        [sheet] = parse_attendance(data)
        self.assertEqual(sheet['period'], (MONDAY, date(2026, 11, 11)))
        self.assertEqual(sheet['employees'], 2)
        kinds = [(event['work_date'], event['kind']) for event in sheet['events'] if event['machine_code'] == '9901']
        self.assertEqual(kinds, [(MONDAY, 'pair'), (date(2026, 11, 10), 'missing_out'), (date(2026, 11, 11), 'reversed')])
        no_code = [event for event in sheet['events'] if not event['machine_code']]
        self.assertEqual([event['kind'] for event in no_code], ['invalid'])
        self.assertEqual(sheet['empty_cells'], 2)
        self.assertEqual(sheet['events'][0]['cell'], 'G9:G10')
        self.assertEqual(sheet['events'][0]['group'], 'PHÒNG SYNTHETIC')

    def test_rejects_unrecognised_or_unsafe_files(self):
        with self.assertRaises(AttendanceFormatError):
            parse_attendance(b'plain text')
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('xl/workbook.xml', '<workbook/>')
            archive.writestr('xl/vbaProject.bin', b'macro')
        with self.assertRaises(AttendanceFormatError):
            parse_attendance(buffer.getvalue())
        with self.assertRaises(AttendanceFormatError):
            parse_attendance(report([], MONDAY, 1))
