"""HR-ATTENDANCE-SIMPLE-002 (ORM): upload → preview → import, machine late totals, sheet / overview / own view,
export rights and the API staging foundation. Synthetic company, people and hours only."""
import base64
from datetime import date, timedelta
from io import BytesIO

from openpyxl import load_workbook

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import AttendanceCase, report

MONDAY = date(2026, 11, 9)
SUNDAY = MONDAY + timedelta(days=6)
WEEK = {'mode': 'range', 'from': '2026-11-09', 'to': '2026-11-15'}
PEOPLE = [
    {'code': '9901', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05'), ('07:50', None)], 'late': (3, 47)},
    {'code': '9902', 'name': 'SYNTHETIC NGUOI HAI', 'times': [('08:00', '17:30')], 'late': (0, 0)},
]


def payload(data, name='synthetic.xlsx'):
    return {'file_name': name, 'data': base64.b64encode(data).decode()}


@tagged('post_install', '-at_install')
class TestAttendanceUpload(AttendanceCase):
    def setUp(self):
        super().setUp()
        self.data = report(PEOPLE, MONDAY, 7, late=True)
        self.Batch = self.env_for(self.manager)['tp.hr.attendance.batch']
        self.Late = self.env['tp.hr.attendance.late'].sudo()
        self.Session = self.env['tp.hr.attendance.session'].sudo()
        self.both = (self.emp_a + self.emp_b).ids

    def import_week(self):
        preview = self.Batch.tp_upload_preview(payload(self.data))
        return self.Batch.tp_upload_apply(preview['batch_id'])

    def test_upload_preview_then_import_keeps_machine_late_totals(self):
        with self.assertRaises(AccessError):
            self.env_for(self.viewer)['tp.hr.attendance.batch'].tp_upload_preview(payload(self.data))
        with self.assertRaises(UserError):
            self.Batch.tp_upload_preview(payload(self.data, 'synthetic.xls'))
        with self.assertRaises(UserError):
            self.Batch.tp_upload_preview(payload(b'not a workbook'))
        preview = self.Batch.tp_upload_preview(payload(self.data))
        self.assertEqual(preview['state'], 'preview')
        self.assertEqual(preview['period'], {'from': '2026-11-09', 'to': '2026-11-15', 'label': '09–15/11'})
        self.assertEqual((preview['matched'], preview['people'], preview['line_count'], preview['empty']), (2, 2, 3, 11))
        self.assertEqual((preview['counts']['valid'], preview['counts']['missing']), (2, 1))
        self.assertEqual((preview['late']['valid'], preview['late_total']), (2, 2))
        self.assertEqual((preview['sheets'][0]['late_state'], preview['sheets'][0]['late_ref']), ('ok', 'N6:O7'))
        self.assertTrue(preview['can_apply'])
        # Nothing is written before "Nhập dữ liệu".
        self.assertFalse(self.Session.search([('employee_id', 'in', self.both)]))
        self.assertFalse(self.Late.search([('employee_id', 'in', self.both), ('state', '=', 'applied')]))
        applied = self.Batch.tp_upload_apply(preview['batch_id'])
        self.assertEqual((applied['state'], applied['late']['applied'], applied['can_apply']), ('applied', 2, False))
        stored = self.Late.search([('employee_id', '=', self.emp_a.id), ('state', '=', 'applied')])
        self.assertEqual((stored.date_from, stored.date_to, stored.late_count, stored.late_minutes), (MONDAY, SUNDAY, 3, 47))
        self.assertEqual(len(self.Session.search([('employee_id', 'in', self.both)])), 2)

    def test_reimport_never_doubles_and_changed_totals_are_conflicts(self):
        first = self.import_week()
        again = self.Batch.tp_upload_preview(payload(self.data, 'synthetic-again.xlsx'))
        self.assertTrue(again['same_file'])
        self.assertEqual(again['counts']['valid'], 0)
        self.assertGreaterEqual(again['counts']['duplicate'], 2)
        self.assertEqual((again['late']['valid'], again['late']['duplicate']), (0, 2))
        self.Batch.tp_upload_apply(again['batch_id'])
        self.assertEqual(self.Late.search_count([('employee_id', 'in', self.both), ('state', '=', 'applied')]), 2)
        self.assertEqual(self.Session.search_count([('employee_id', 'in', self.both)]), 2)
        # Same period, different machine total: kept as a conflict for HR, never last-write-wins.
        changed = report([dict(PEOPLE[0], late=(4, 50)), PEOPLE[1]], MONDAY, 7, late=True)
        conflict = self.Batch.tp_upload_preview(payload(changed, 'synthetic-changed.xlsx'))
        self.assertEqual((conflict['late']['conflict'], conflict['late']['duplicate']), (1, 1))
        self.assertEqual([row['code'] for row in conflict['late_attention']], ['9901'])
        self.Batch.tp_upload_apply(conflict['batch_id'])
        kept = self.Late.search([('employee_id', '=', self.emp_a.id), ('state', '=', 'applied')])
        self.assertEqual((kept.late_count, kept.late_minutes, kept.batch_id.id), (3, 47, first['batch_id']))

    def test_cancel_writes_nothing(self):
        preview = self.Batch.tp_upload_preview(payload(self.data))
        self.assertEqual(self.Batch.tp_upload_cancel(preview['batch_id'])['state'], 'cancelled')
        self.assertFalse(self.Session.search([('employee_id', 'in', self.both)]))
        self.assertFalse(self.Late.search([('employee_id', 'in', self.both), ('state', '=', 'applied')]))
        with self.assertRaises(UserError):
            self.Batch.tp_upload_apply(preview['batch_id'])

    def test_sheet_and_overview_follow_source_periods(self):
        self.import_week()
        Day = self.env_for(self.manager)['tp.hr.attendance.day']
        week = Day.tp_sheet(WEEK)
        rows = {row['id']: row['late'] for row in week['rows']}
        self.assertEqual((rows[self.emp_a.id]['state'], rows[self.emp_a.id]['count'], rows[self.emp_a.id]['minutes']), ('exact', 3, 47))
        self.assertEqual(rows[self.emp_a.id]['source'], '09–15/11')
        self.assertEqual((rows[self.emp_b.id]['state'], rows[self.emp_b.id]['count']), ('exact', 0))
        self.assertTrue(week['is_file_period'])
        self.assertEqual(week['late_summary'], {'people': 2, 'count': 3, 'minutes': 47})
        # A month that only holds one weekly file: never 0, never split, points to the source period.
        month = {row['id']: row['late'] for row in Day.tp_sheet({'mode': 'month', 'date': '2026-11-09'})['rows']}
        self.assertEqual((month[self.emp_a.id]['state'], month[self.emp_a.id]['count']), ('partial', None))
        self.assertEqual(month[self.emp_a.id]['text'], 'Số đi muộn có ở tổng kỳ 09–15/11')
        monday = Day.tp_sheet({'mode': 'day', 'date': '2026-11-09'})
        self.assertEqual(monday['late_note'], 'Số đi muộn có ở tổng kỳ 09–15/11')
        cells = {row['id']: row for row in monday['rows']}
        self.assertEqual((cells[self.emp_a.id]['in'], cells[self.emp_a.id]['out']), ('07:37', '17:05'))
        tuesday = {row['id']: row for row in Day.tp_sheet({'mode': 'day', 'date': '2026-11-10'})['rows']}
        self.assertEqual((tuesday[self.emp_a.id]['state'], tuesday[self.emp_a.id]['out']), ('missing', ''))
        # An empty cell in a file that lists the person is "not recorded", never leave.
        self.assertEqual(tuesday[self.emp_b.id]['state'], 'no_punch')
        # Dashboard: one main state per person, donut adds up to the KPI total; a day has no exact late total.
        overview = Day.tp_overview({'mode': 'day', 'date': '2026-11-09'})
        self.assertEqual(sum(item['value'] for item in overview['donut']), overview['kpis']['total'])
        if not overview['has_leave_source']:
            self.assertIsNone(overview['kpis']['leave'])
        self.assertIsNone(overview['late'])
        self.assertEqual(overview['late_hints'], ['09–15/11'])
        weekly = Day.tp_overview({'mode': 'week', 'date': '2026-11-11'})
        self.assertEqual({key: weekly['late'][key] for key in ('people', 'late_people', 'count', 'minutes')},
                         {'people': 2, 'late_people': 1, 'count': 3, 'minutes': 47})
        self.assertEqual(len(weekly['daily']), 7)
        with self.assertRaises(UserError):
            Day.tp_sheet({'mode': 'range', 'from': '2026-11-15', 'to': '2026-11-09'})

    def test_own_view_and_export_rights(self):
        self.import_week()
        Mine = self.env_for(self.viewer)['tp.hr.attendance.day']
        mine = Mine.tp_mine(dict(WEEK, employee_id=self.emp_b.id))
        self.assertTrue(mine['has_employee'])
        self.assertEqual(mine['employee']['id'], self.emp_a.id)
        self.assertEqual((mine['late']['state'], mine['late']['count'], mine['late']['minutes']), ('exact', 3, 47))
        self.assertEqual(len(mine['rows']), 7)
        self.assertEqual((mine['page_size'], mine['total'], mine['period_days']), (50, 7, 7))
        self.assertEqual((mine['summary']['recorded_days'], mine['summary']['attention_days']), (2, 1))
        filtered = Mine.tp_mine(dict(WEEK, state='missing_out', employee_id=self.emp_b.id))
        self.assertEqual((filtered['employee']['id'], filtered['total'], len(filtered['rows'])), (self.emp_a.id, 1, 1))
        self.assertEqual(filtered['rows'][0]['date'], '2026-11-10')
        # Period summary and Excel late totals stay full-period even when rows are filtered.
        self.assertEqual((filtered['summary']['recorded_days'], filtered['late']['count']), (2, 3))
        with self.assertRaises(UserError):
            Mine.tp_mine(dict(WEEK, state='forged_state'))
        own = load_workbook(BytesIO(base64.b64decode(Mine.tp_export_mine(WEEK)['data'])))
        self.assertEqual(own.sheetnames, ['Giờ theo ngày', 'Tổng đi muộn'])
        self.assertEqual({row[0] for row in own['Giờ theo ngày'].iter_rows(min_row=3, values_only=True)}, {self.emp_a.name})
        own_filtered = load_workbook(BytesIO(base64.b64decode(Mine.tp_export_mine(dict(WEEK, state='missing_out', page=1, page_size=10))['data'])))
        self.assertEqual(own_filtered.sheetnames, ['Giờ theo ngày', 'Tổng đi muộn'])
        self.assertEqual(list(own_filtered['Giờ theo ngày'].iter_rows(min_row=3, values_only=True)), [
            (self.emp_a.name, self.emp_a.tp_employee_code, self.dept_a.name, 'T3 10/11/2026', '07:50', '—', 'Thiếu giờ ra'),
        ])
        # Read-only users cannot export shared data; HR can, with the late sheet for exact periods only.
        with self.assertRaises(AccessError):
            Mine.tp_export_sheet(WEEK)
        shared = self.env_for(self.manager)['tp.hr.attendance.day'].tp_export_sheet(WEEK)
        book = load_workbook(BytesIO(base64.b64decode(shared['data'])))
        self.assertEqual(book.sheetnames, ['Giờ theo ngày', 'Tổng đi muộn'])
        self.assertEqual(sorted(row[4] for row in book['Tổng đi muộn'].iter_rows(min_row=3, values_only=True)), [0, 3])
        month = self.env_for(self.manager)['tp.hr.attendance.day'].tp_export_sheet({'mode': 'month', 'date': '2026-11-09'})
        self.assertEqual(load_workbook(BytesIO(base64.b64decode(month['data']))).sheetnames, ['Giờ theo ngày'])

    def test_api_staging_dedupes_maps_by_namespace_and_stays_offline(self):
        env = self.env_for(self.manager)
        Source = env['tp.hr.attendance.source']
        with self.assertRaises(AccessError):
            self.env_for(self.viewer)['tp.hr.attendance.source'].tp_sources_overview({})
        overview = Source.tp_sources_overview({})
        self.assertEqual((overview['api']['label'], overview['api']['live'], overview['api']['events']), ('Chưa cấu hình', False, 0))
        self.assertTrue(overview['checklist'])
        source = Source.create({'name': 'Synthetic device', 'namespace': 'synthetic-device-1', 'company_id': self.company.id})
        self.assertEqual((source.state, source.live_enabled), ('not_configured', False))
        events = [
            {'external_code': '0042', 'timestamp': '2026-11-09T07:37:00', 'direction': 'IN', 'event_id': 'E-1'},
            {'external_code': '0042', 'timestamp': '2026-11-09T17:05:00', 'direction': 'OUT', 'event_id': 'E-2'},
            {'external_code': '0077', 'timestamp': '2026-11-09T07:40:00', 'direction': 'IN'},
            {'external_code': '', 'timestamp': '2026-11-09T07:40:00'},
            'not an object',
        ]
        with self.assertRaises(UserError):
            source.tp_ingest(events)
        source.write({'state': 'ready'})
        env['tp.hr.attendance.source.code'].create({'source_id': source.id, 'external_code': '0042', 'employee_id': self.emp_a.id})
        first = source.tp_ingest(events, watermark='cursor-1')
        self.assertEqual({key: first[key] for key in ('received', 'created', 'duplicate', 'rejected', 'unmapped')},
                         {'received': 5, 'created': 3, 'duplicate': 0, 'rejected': 2, 'unmapped': 1})
        self.assertEqual(source.watermark, 'cursor-1')
        again = source.tp_ingest(events[:3], watermark='cursor-2')
        self.assertEqual((again['created'], again['duplicate']), (0, 3))
        stored = self.env['tp.hr.attendance.event'].sudo().search([('source_id', '=', source.id)])
        self.assertEqual(len(stored), 3)
        self.assertEqual(set(stored.mapped('external_code')), {'0042', '0077'})
        self.assertEqual(stored.filtered(lambda event: event.external_code == '0042').employee_id, self.emp_a)
        # A code declared later maps the waiting events (namespace + company only, never by name).
        env['tp.hr.attendance.source.code'].create({'source_id': source.id, 'external_code': '0077', 'employee_id': self.emp_b.id})
        self.assertEqual(set(stored.mapped('state')), {'mapped'})
        with self.assertRaises(AccessError):
            stored[:1].write({'direction': 'OUT'})
        with self.assertRaises(AccessError):
            stored[:1].unlink()
        for vals in ({'live_enabled': True}, {'watermark': 'forged'}):
            with self.assertRaises(AccessError):
                source.write(vals)
        with self.assertRaises(ValidationError):
            source.write({'credential_ref': 'paste-the-secret-here'})
        with self.assertRaises(AccessError):
            source.with_user(self.viewer).tp_ingest(events[:1])
        after = Source.tp_sources_overview({})
        self.assertEqual((after['api']['label'], after['api']['events'], after['api']['live']), ('1 nguồn đã khai báo', 3, False))
