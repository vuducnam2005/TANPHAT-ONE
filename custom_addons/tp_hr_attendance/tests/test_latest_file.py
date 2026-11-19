"""Latest-file import replaces open Excel days, keeps lineage, and enforces existing access."""
import base64
from datetime import date

from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import AttendanceCase, report
from odoo.addons.tp_hr_attendance.models.attendance_common import internal

MONDAY = date(2026, 11, 9)


@tagged('post_install', '-at_install', 'attendance_latest')
class TestLatestFile(AttendanceCase):
    def upload(self, times, late=(0, 0), name='source.xlsx', user=None):
        raw = report([{'code': '9901', 'name': 'Synthetic Người Một', 'times': times, 'late': late}],
                     MONDAY, len(times), late=True)
        result = self.env_for(user or self.manager)['tp.hr.attendance.batch'].tp_upload_files({
            'files': [{'file_name': name, 'data': base64.b64encode(raw).decode()}]})
        self.assertEqual(result['error_count'], 0, result)
        return self.env['tp.hr.attendance.batch'].browse(result['created_ids'][0])

    def test_latest_replaces_without_double_count_and_keeps_original(self):
        first = self.upload([('08:30', '17:00'), ('08:31', '17:01')], (1, 1))
        old = self.env['tp.hr.attendance.session'].search([('employee_id', '=', self.emp_a.id), ('work_date', '=', MONDAY)])
        latest = self.upload([('08:40', '17:10'), ('08:31', '17:01')], (2, 10))
        self.assertEqual(self.day(self.emp_a, MONDAY).in_time, '08:40')
        self.assertEqual(self.day(self.emp_a, MONDAY).session_count, 1)
        self.assertFalse(old.active)
        self.assertTrue(old.exists())
        self.assertTrue(self.env['tp.hr.attendance.snapshot.person'].search_count([('batch_id', '=', first.id)]))
        latest.with_user(self.manager).with_company(self.company)._tp_apply_latest_file()
        self.assertEqual(self.day(self.emp_a, MONDAY).session_count, 1)
        # An older source cannot win if applied again after the latest upload.
        first.with_user(self.manager).with_company(self.company)._tp_apply_latest_file()
        self.assertEqual(self.day(self.emp_a, MONDAY).in_time, '08:40')
        canonical = self.env['tp.hr.attendance.late'].search([('employee_id', '=', self.emp_a.id), ('state', '=', 'applied')])
        self.assertEqual((canonical.late_count, canonical.late_minutes), (2, 10))

    def test_missing_and_blank_replace_only_the_file_scope(self):
        self.upload([('08:30', '17:00'), ('08:31', '17:01')])
        self.upload([('08:45', None)])
        self.assertEqual((self.day(self.emp_a, MONDAY).in_time, self.day(self.emp_a, MONDAY).out_time), ('08:45', False))
        self.assertEqual(self.day(self.emp_a, date(2026, 11, 10)).in_time, '08:31')
        self.upload([(None, None)])
        self.assertFalse(self.day(self.emp_a, MONDAY))
        self.assertEqual(self.day(self.emp_a, date(2026, 11, 10)).in_time, '08:31')

    def test_viewer_cannot_trigger_latest_import(self):
        with self.assertRaises(AccessError):
            self.upload([('08:30', '17:00')], user=self.viewer)

    def test_multiple_files_use_upload_order_and_keep_valid_file_on_error(self):
        files = []
        for name, clock in [('first.xlsx', '08:30'), ('last.xlsx', '08:45')]:
            raw = report([{'code': '9901', 'name': 'Synthetic Người Một', 'times': [(clock, '17:00')]}], MONDAY, 1)
            files.append({'file_name': name, 'data': base64.b64encode(raw).decode()})
        files.insert(1, {'file_name': 'broken.xlsx', 'data': base64.b64encode(b'not a workbook').decode()})
        result = self.env_for(self.manager)['tp.hr.attendance.batch'].tp_upload_files({'files': files})
        self.assertEqual((result['success_count'], result['error_count']), (2, 1))
        self.assertEqual(self.day(self.emp_a, MONDAY).in_time, '08:45')
        self.assertEqual(self.day(self.emp_a, MONDAY).session_count, 1)

    def test_locked_day_and_invalid_hours_keep_current_values(self):
        self.upload([('08:30', '17:00'), ('08:31', '17:01')])
        period = self.env_for(self.manager)['tp.hr.attendance.period'].create({
            'name': 'Synthetic locked day', 'company_id': self.company.id,
            'date_from': MONDAY, 'date_to': MONDAY})
        internal(period).write({'state': 'locked'})
        latest = self.upload([('09:00', '18:00'), ('18:00', '08:00')])
        self.assertEqual(self.day(self.emp_a, MONDAY).in_time, '08:30')
        self.assertEqual(self.day(self.emp_a, date(2026, 11, 10)).in_time, '08:31')
        self.assertEqual(latest.state, 'partial')
