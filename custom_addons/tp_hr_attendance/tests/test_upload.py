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
    {'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05'), ('07:50', None)], 'late': (3, 47)},
    {'code': '992', 'name': 'SYNTHETIC NGUOI HAI', 'times': [('08:00', '17:30')], 'late': (0, 0)},
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
        preview = self.Batch._tp_upload_preview(payload(self.data))
        return self.Batch._tp_upload_apply(preview['batch_id'])

    def test_upload_preview_then_import_keeps_machine_late_totals(self):
        with self.assertRaises(AccessError):
            self.env_for(self.viewer)['tp.hr.attendance.batch']._tp_upload_preview(payload(self.data))
        with self.assertRaises(UserError):
            self.Batch._tp_upload_preview(payload(self.data, 'synthetic.xls'))
        with self.assertRaises(UserError):
            self.Batch._tp_upload_preview(payload(b'not a workbook'))
        preview = self.Batch._tp_upload_preview(payload(self.data))
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
        applied = self.Batch._tp_upload_apply(preview['batch_id'])
        self.assertEqual((applied['state'], applied['late']['applied'], applied['can_apply']), ('applied', 2, False))
        stored = self.Late.search([('employee_id', '=', self.emp_a.id), ('state', '=', 'applied')])
        self.assertEqual((stored.date_from, stored.date_to, stored.late_count, stored.late_minutes), (MONDAY, SUNDAY, 3, 47))
        self.assertEqual(len(self.Session.search([('employee_id', 'in', self.both)])), 2)

    def test_reimport_never_doubles_and_changed_totals_are_conflicts(self):
        first = self.import_week()
        again = self.Batch._tp_upload_preview(payload(self.data, 'synthetic-again.xlsx'))
        self.assertTrue(again['same_file'])
        self.assertEqual(again['counts']['valid'], 0)
        self.assertGreaterEqual(again['counts']['duplicate'], 2)
        self.assertEqual((again['late']['valid'], again['late']['duplicate']), (0, 2))
        self.Batch._tp_upload_apply(again['batch_id'])
        self.assertEqual(self.Late.search_count([('employee_id', 'in', self.both), ('state', '=', 'applied')]), 2)
        self.assertEqual(self.Session.search_count([('employee_id', 'in', self.both)]), 2)
        # Same period, different machine total: the preview flags it for HR; applying the newer file follows the
        # latest-file policy (test_latest_file) and still keeps exactly one applied total per person and period.
        changed = report([dict(PEOPLE[0], late=(4, 50)), PEOPLE[1]], MONDAY, 7, late=True)
        conflict = self.Batch._tp_upload_preview(payload(changed, 'synthetic-changed.xlsx'))
        self.assertEqual((conflict['late']['conflict'], conflict['late']['duplicate']), (1, 1))
        self.assertEqual([row['code'] for row in conflict['late_attention']], ['991'])
        self.Batch._tp_upload_apply(conflict['batch_id'])
        kept = self.Late.search([('employee_id', '=', self.emp_a.id), ('state', '=', 'applied')])
        self.assertEqual((kept.late_count, kept.late_minutes, kept.batch_id.id), (4, 50, conflict['batch_id']))
        self.assertNotEqual(first['batch_id'], conflict['batch_id'])
        self.assertEqual(self.Late.search_count([('employee_id', 'in', self.both), ('state', '=', 'applied')]), 2)

    def test_cancel_writes_nothing(self):
        preview = self.Batch._tp_upload_preview(payload(self.data))
        self.assertEqual(self.Batch.tp_upload_cancel(preview['batch_id'])['state'], 'cancelled')
        self.assertFalse(self.Session.search([('employee_id', 'in', self.both)]))
        self.assertFalse(self.Late.search([('employee_id', 'in', self.both), ('state', '=', 'applied')]))
        with self.assertRaises(UserError):
            self.Batch._tp_upload_apply(preview['batch_id'])

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
        # A past working day with no punch at all for a listed person is an absence (ENTI-ATTENDANCE-002 rule), never leave.
        self.assertEqual(tuesday[self.emp_b.id]['state'], 'absent')
        # Dashboard: one main state per counted person-day, so the status split adds up to the person-days shown.
        overview = Day.tp_overview({'mode': 'day', 'date': '2026-11-09'})
        self.assertEqual(sum(item['value'] for item in overview['statuses']), overview['kpis']['person_days'])
        if not overview['has_leave_source']:
            self.assertIsNone(overview['kpis']['leave'])
        # Late minutes on the dashboard come from ENTI per day; a weekly Excel total is never spread over days or shown as 0.
        self.assertEqual(overview['kpis']['late']['state'], 'none')
        weekly = Day.tp_overview({'mode': 'week', 'date': '2026-11-11'})
        self.assertEqual((weekly['kpis']['late']['state'], weekly['kpis']['late']['text']), ('none', 'Chưa có số liệu đi muộn'))
        self.assertEqual(len(weekly['trend']), 7)
        self.assertEqual(sum(item['value'] for item in weekly['statuses']), weekly['kpis']['person_days'])
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
        self.assertEqual((mine['page_size'], mine['total'], mine['period_days']), (100, 7, 7))
        self.assertEqual((mine['summary']['recorded_days'], mine['summary']['attention_days']), (2, 1))
        filtered = Mine.tp_mine(dict(WEEK, state='missing_out', employee_id=self.emp_b.id))
        self.assertEqual((filtered['employee']['id'], filtered['total'], len(filtered['rows'])), (self.emp_a.id, 1, 1))
        self.assertEqual(filtered['rows'][0]['date'], '2026-11-10')
        # Period summary and Excel late totals stay full-period even when rows are filtered.
        self.assertEqual((filtered['summary']['recorded_days'], filtered['late']['count']), (2, 3))
        with self.assertRaises(UserError):
            Mine.tp_mine(dict(WEEK, state='forged_state'))
        # Redesign: single sheet "Report" matching the sample timesheet template.
        sheets = ['Report']
        own_res = Mine.tp_export_mine(WEEK)
        self.assertEqual(own_res['filename'], 'Cong_cua_toi_09-11-2026_den_15-11-2026.xlsx')
        own = load_workbook(BytesIO(base64.b64decode(own_res['data'])))
        self.assertEqual(own.sheetnames, sheets)
        ws_own = own['Report']
        self.assertEqual([ws_own.cell(row, 3).value for row in range(7, ws_own.max_row + 1)
                          if ws_own.cell(row, 6).value == 'Vào'], [self.emp_a.name])
        own_filtered_res = Mine.tp_export_mine(dict(WEEK, state='missing_out', page=1, page_size=10))
        own_filtered = load_workbook(BytesIO(base64.b64decode(own_filtered_res['data'])))
        self.assertEqual(own_filtered.sheetnames, sheets)
        ws_filt = own_filtered['Report']
        # Day 2 (2026-11-10 -> col 8) is the missing_out day; other days are blank under the filter.
        vao_rows = [row for row in range(7, ws_filt.max_row + 1) if ws_filt.cell(row, 6).value == 'Vào']
        self.assertEqual(len(vao_rows), 1)
        self.assertEqual(ws_filt.cell(vao_rows[0], 8).value, '07:50')
        self.assertIsNone(ws_filt.cell(vao_rows[0] + 1, 8).value)
        self.assertIsNone(ws_filt.cell(vao_rows[0], 7).value)
        # Read-only users cannot export shared data; HR can.
        with self.assertRaises(AccessError):
            Mine.tp_export_sheet(WEEK)
        shared = self.env_for(self.manager)['tp.hr.attendance.day'].tp_export_sheet(WEEK)
        self.assertEqual(shared['filename'], 'Bang_cong_09-11-2026_den_15-11-2026.xlsx')
        book = load_workbook(BytesIO(base64.b64decode(shared['data'])))
        self.assertEqual(book.sheetnames, sheets)
        grid = book['Report']
        blocks = [row for row in range(7, grid.max_row + 1) if grid.cell(row, 6).value == 'Vào']
        self.assertEqual(sorted(grid.cell(row, 7 + 7).value for row in blocks), [0, 3])
        month = self.env_for(self.manager)['tp.hr.attendance.day'].tp_export_sheet({'mode': 'month', 'date': '2026-11-09'})
        month_book = load_workbook(BytesIO(base64.b64decode(month['data'])))
        self.assertEqual(month_book.sheetnames, sheets)
        month_grid = month_book['Report']
        late_col = 7 + 30
        partial = [month_grid.cell(row, late_col).value for row in range(7, month_grid.max_row + 1)
                   if month_grid.cell(row, 6).value == 'Vào']
        self.assertTrue(all(isinstance(val, int) and val >= 0 for val in partial))

        # Department, employee search, day-state and empty-result export scope parity.
        DayMgr = self.env_for(self.manager)['tp.hr.attendance.day']
        by_emp = DayMgr.tp_export_sheet(dict(WEEK, department_id=self.dept.id, search=self.emp_a.tp_employee_code))
        emp_ws = load_workbook(BytesIO(base64.b64decode(by_emp['data'])))['Report']
        self.assertEqual([emp_ws.cell(r, 3).value for r in range(7, emp_ws.max_row + 1)
                          if emp_ws.cell(r, 6).value == 'Vào'], [self.emp_a.name])

        day_missing = DayMgr.tp_export_sheet({'mode': 'day', 'date': '2026-11-10', 'state': 'missing'})
        day_ws = load_workbook(BytesIO(base64.b64decode(day_missing['data'])))['Report']
        day_sheet = DayMgr.tp_sheet({'mode': 'day', 'date': '2026-11-10', 'state': 'missing'})
        self.assertEqual(
            [day_ws.cell(r, 3).value for r in range(7, day_ws.max_row + 1) if day_ws.cell(r, 6).value == 'Vào'],
            [row['name'] for row in day_sheet['rows']],
        )

        empty_res = DayMgr.tp_export_sheet(dict(WEEK, search='KHONG_TON_TAI_XYZ'))
        empty_ws = load_workbook(BytesIO(base64.b64decode(empty_res['data'])))['Report']
        self.assertEqual(empty_ws['A7'].value, 'Không có dữ liệu trong kỳ đã chọn')

        mine_empty = Mine.tp_export_mine(dict(WEEK, state='leave'))
        mine_empty_ws = load_workbook(BytesIO(base64.b64decode(mine_empty['data'])))['Report']
        self.assertEqual(mine_empty_ws['A7'].value, 'Không có dữ liệu trong kỳ đã chọn')

    def test_mine_rows_reverse_chronological(self):
        self.import_week()
        Mine = self.env_for(self.viewer)['tp.hr.attendance.day']
        mine = Mine.tp_mine(WEEK)
        dates = [row['date'] for row in mine['rows']]
        today = mine['today']
        elapsed = [d for d in dates if d <= today]
        self.assertEqual(elapsed, sorted(elapsed, reverse=True))
        if elapsed:
            self.assertEqual(elapsed[0], mine['rows'][0]['date'])

    def test_api_staging_dedupes_maps_by_namespace_and_stays_offline(self):
        env = self.env_for(self.manager)
        Source = env['tp.hr.attendance.source']
        with self.assertRaises(AccessError):
            self.env_for(self.viewer)['tp.hr.attendance.source'].tp_sources_overview({})
        overview = Source.tp_sources_overview({})
        self.assertEqual((overview['api']['label'], overview['api']['live'], overview['api']['events']), ('Chưa cấu hình', False, 0))
        self.assertNotIn('excel', overview, 'The administration no longer exposes file-import summaries')
        self.assertNotIn('history', overview)
        self.assertEqual(overview['health'], 'off')
        self.assertTrue(overview['can_export'])
        self.assertFalse(overview['can_review'], 'HR title does not grant correction approval')
        self.assertEqual(overview['sync_logs'], [])
        self.assertEqual(overview['mapping'], {'suggested': 0, 'unmapped': 0})
        self.assertIn(self.dept.id, [item['id'] for item in overview['departments']])
        self.assertTrue(overview['checklist'])
        source = Source.create({'name': 'Synthetic device', 'namespace': 'synthetic-device-1', 'company_id': self.company.id})
        self.env['tp.hr.attendance.enti.sync.log'].sudo().create([
            {'source_id': source.id, 'start_date': MONDAY, 'end_date': MONDAY,
             'state': 'success', 'days_received': value, 'days_applied': value, 'message': 'Private debug details'}
            for value in range(7)
        ])
        log_preview = Source.tp_sources_overview({})['sync_logs']
        self.assertEqual(len(log_preview), 5)
        self.assertEqual([item['days_received'] for item in log_preview], [6, 5, 4, 3, 2])
        self.assertTrue(all('message' not in item for item in log_preview))
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
