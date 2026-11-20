"""ENTI-ATTENDANCE-002 (synthetic data only, no network, no real ENTI account).

- ENTI HTTP client with a fake session: nested login tokens, refresh before expiry, 401 renewal, 429 Retry-After,
  bounded 5xx / network retries, invalid JSON, full pagination with de-duplication, partial board refused.
- One sync pass with a fake client: exact-name mapping only, date from ``ngay`` (never the slot), in-only day,
  unchanged poll writes nothing and wakes no screen, empty punch keeps old times, errors keep data and report
  health once, locked period untouched, mapping evidence and one ENTI key per employee.
- Excel file import closed: every public write RPC refuses, private helpers are not callable remotely, the
  history stays readable and exportable.
- Export template ("Bảng chấm công"): layout, time cells, symbols, totals, formula neutralisation; the employee
  note and the "10 newest marks" helper.
"""
import base64
import copy
import threading
from datetime import date, datetime, time, timedelta
from io import BytesIO
from types import SimpleNamespace

import requests
from openpyxl import load_workbook

from odoo.exceptions import AccessError, UserError
from odoo.models import get_public_method
from odoo.tests import tagged
from odoo.tests.common import BaseCase

from .common import AttendanceCase, report
from odoo.addons.tp_hr_attendance.models import enti_client as enti_client_module
from odoo.addons.tp_hr_attendance.models import enti_sync as enti_sync_module
from odoo.addons.tp_hr_attendance.models.attendance_common import DEFAULT_TZ, internal
from odoo.addons.tp_hr_attendance.models.attendance_export import (
    build_attendance_book,
    person_note,
)
from odoo.addons.tp_hr_attendance.models.attendance_figures import recent_people
from odoo.addons.tp_hr_attendance.models.attendance_import import IMPORT_CLOSED
from odoo.addons.tp_hr_attendance.models.enti_client import (
    EntiAuthError,
    EntiClient,
    EntiError,
)

BASE = 'https://enti.invalid'
D16, D17, D18 = date(2026, 11, 16), date(2026, 11, 17), date(2026, 11, 18)


# ---------------------------------------------------------------------------------------------- fake HTTP
class FakeResponse:
    def __init__(self, status=200, payload=None, headers=None):
        self.status_code = status
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        if self._payload is None:
            message = 'not json'
            raise ValueError(message)
        return self._payload


class FakeSession:
    """Replays ``script`` (responses or exceptions) and records every call (path, body, Authorization)."""

    def __init__(self, *script):
        self.script = list(script)
        self.calls = []

    def request(self, method, url, json=None, params=None, headers=None, timeout=None):
        self.calls.append({'method': method, 'path': url.removeprefix(BASE), 'json': json,
                           'auth': (headers or {}).get('Authorization')})
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


def ok(data=None, **extra):
    return FakeResponse(200, dict({'statusCode': 200, 'data': data if data is not None else []}, **extra))


class TestEntiClientFake(BaseCase):
    def setUp(self):
        super().setUp()
        self.sleeps = []
        # Only the client module sees the fake clock; nothing really waits.
        self.patch(enti_client_module, 'time', SimpleNamespace(sleep=self.sleeps.append))

    def client(self, *script, token='A1', refresh='R1', expires_in=3600):
        client = EntiClient(base_url=BASE)
        client.session = FakeSession(*script)
        client.access_token, client.refresh_token = token, refresh
        client.token_expires_at = datetime.now() + timedelta(seconds=expires_in) if token else None
        return client

    def test_login_reads_nested_tokens_and_sends_bearer(self):
        client = self.client(ok({'access_token': 'NEW', 'refresh_token': 'R2', 'expires_in': 900}), ok({'id': 1}),
                             token=None, refresh=None)
        client.login('0900000000', 'synthetic-secret')
        self.assertEqual((client.access_token, client.refresh_token), ('NEW', 'R2'))
        self.assertTrue(client.is_token_valid())
        client.get_me()
        login, me = client.session.calls
        self.assertEqual((login['path'], login['auth']), ('/__enti/api/v1/auth/login', None))
        self.assertEqual((me['path'], me['auth']), ('/__enti/api/v1/me', 'Bearer NEW'))
        with self.assertRaises(EntiAuthError):
            self.client(FakeResponse(200, {'statusCode': 401, 'message': 'Sai mật khẩu', 'data': {}}),
                        token=None).login('0900000000', 'wrong')

    def test_expired_token_is_refreshed_before_the_request(self):
        client = self.client(ok({'access_token': 'FRESH', 'expires_in': 900}), ok({'id': 1}), expires_in=30)
        client.get_me()
        refresh, me = client.session.calls
        self.assertEqual((refresh['path'], refresh['json']), ('/__enti/api/v1/auth/refresh', {'refresh_token': 'R1'}))
        self.assertEqual(me['auth'], 'Bearer FRESH')

    def test_401_renews_once_then_retries(self):
        client = self.client(FakeResponse(401), ok({'access_token': 'RENEWED', 'expires_in': 900}), ok({'id': 1}))
        client.get_me()
        self.assertEqual([call['path'] for call in client.session.calls],
                         ['/__enti/api/v1/me', '/__enti/api/v1/auth/refresh', '/__enti/api/v1/me'])
        self.assertEqual(client.session.calls[-1]['auth'], 'Bearer RENEWED')
        # Without any way to renew, a 401 is an authentication error (the sync drops its cached client).
        with self.assertRaises(EntiAuthError) as caught:
            self.client(FakeResponse(401), refresh=None).get_me()
        self.assertEqual(caught.exception.status_code, 401)

    def test_429_and_5xx_retry_with_bounded_wait(self):
        client = self.client(FakeResponse(429, headers={'Retry-After': '30'}), FakeResponse(503), ok([{'keyNV': 'k'}]))
        self.assertEqual(client.get_employees(), [{'keyNV': 'k'}])
        self.assertEqual(self.sleeps, [10, 4], 'Retry-After is honoured but capped at 10 s')
        self.sleeps.clear()
        with self.assertRaises(EntiError) as caught:
            self.client(FakeResponse(503), FakeResponse(502), FakeResponse(503)).get_employees()
        self.assertEqual(caught.exception.status_code, 503)
        self.assertEqual(self.sleeps, [2, 4])

    def test_network_errors_recover_or_fail_cleanly(self):
        client = self.client(requests.ConnectionError('synthetic reset'), ok([]))
        self.assertEqual(client.get_employees(), [])
        self.assertEqual(self.sleeps, [1])
        with self.assertRaises(EntiError) as caught:
            self.client(*(requests.Timeout('synthetic timeout') for _ in range(3))).get_employees()
        self.assertIn('Không thể kết nối', str(caught.exception))
        with self.assertRaises(EntiError):
            self.client(FakeResponse(200, None)).get_employees()

    def test_attendance_pagination_dedupes_and_refuses_a_partial_board(self):
        first = ok([{'keyNV': 'nv1'}, {'keyNV': 'nv2'}], numOfData=2, totalData=3, moreData=True)
        second = ok([{'keyNV': 'nv2'}, {'keyNV': 'nv3'}], numOfData=2, totalData=3, moreData=False)
        client = self.client(first, second)
        board = client.get_attendance(D16, D18, max_results_per_page=2)
        self.assertEqual([row['keyNV'] for row in board['data']], ['nv1', 'nv2', 'nv3'])
        self.assertEqual((board['total'], board['pages'], board['startDate'], board['endDate']),
                         (3, 2, '2026-11-16', '2026-11-18'))
        bodies = [call['json'] for call in client.session.calls]
        self.assertEqual([(b['searchResultPosition'], b['maxTotalResult']) for b in bodies], [(0, 2), (2, 2)])
        self.assertTrue(all(call['path'] == '/api/attendace/bang-cong' for call in client.session.calls))

        partial = self.client(ok([{'keyNV': 'nv1'}, {'keyNV': 'nv2'}], numOfData=2, totalData=3, moreData=True), ok([]))
        with self.assertRaises(EntiError) as caught:
            partial.get_attendance(D16, D18, max_results_per_page=2)
        self.assertIn('2/3', str(caught.exception))


# ---------------------------------------------------------------------------------------------- sync pass
def enti_row(key, name, days, code=''):
    row = {'keyNV': key, 'maNV': code, 'tenNV': name, 'tenBP': 'Synthetic ENTI Dept'}
    for slot, (work_date, clock_in, clock_out, late) in enumerate(days, 1):
        row[f'day{slot}'] = {'ngay': f'{work_date.isoformat()}T00:00:00', 'vaoDau': clock_in, 'raCuoi': clock_out,
                             'diMuon': late, 'congLam': 1 if clock_in and clock_out else 0}
    return row


class FakeEnti:
    def __init__(self, rows, error=None):
        self.rows, self.error, self.reads = rows, error, 0

    def get_employees(self):
        return [{key: row[key] for key in ('keyNV', 'maNV', 'tenNV', 'tenBP')} for row in self.rows]

    def get_attendance(self, start_date, end_date):
        self.reads += 1
        if self.error:
            raise self.error
        return {'data': copy.deepcopy(self.rows), 'total': len(self.rows), 'pages': 1}


@tagged('post_install', '-at_install')
class TestEntiSyncFake(AttendanceCase):
    def setUp(self):
        super().setUp()
        self.source = internal(self.env['tp.hr.attendance.source']).create({
            'name': 'Synthetic ENTI', 'namespace': 'synthetic-enti-sync', 'kind': 'enti_api',
            'company_id': self.company.id, 'timezone': DEFAULT_TZ, 'state': 'ready', 'live_enabled': True})
        self.addCleanup(enti_sync_module._PACE.pop, (self.env.cr.dbname, self.source.id), None)
        self.fake = FakeEnti([])
        self.notes = []
        entry = {'client': self.fake, 'lock': threading.Lock(), 'app_key': 'synthetic-app'}
        Source = type(self.source)
        self.patch(Source, '_tp_enti_entry', lambda rec: (entry, 'synthetic', 'synthetic', 'synthetic-app'))
        self.patch(Source, '_tp_enti_ready', lambda rec, *args: self.fake)
        self.patch(Source, '_tp_enti_notify',
                   lambda rec, dates=(), health=None: self.notes.append((sorted(dates), health)))
        self.Mapping = self.env['tp.hr.attendance.enti.mapping'].sudo()
        self.EntiDay = self.env['tp.hr.attendance.enti.day'].sudo()

    def sync(self, rows=None, error=None, start=D16, end=D18):
        if rows is not None:
            self.fake.rows = rows
        self.fake.error = error
        result = self.source._tp_run_enti(start, end, scope='range', origin='manual', wait=True)
        self.source.invalidate_recordset()
        return result

    def mapping(self, key):
        return self.Mapping.search([('source_id', '=', self.source.id), ('key_nv', '=', key)])

    def week_rows(self, late=12):
        # Slots on purpose out of date order: the work date always comes from "ngay".
        return [
            enti_row('syn-a', 'Synthetic  Người Một', [(D18, None, None, 0), (D17, '08:10', None, 0),
                                                      (D16, '08:42', '17:02', late), (D18 + timedelta(days=1), '08:00', '17:00', 0)]),
            enti_row('syn-x', 'Synthetic Nguoi Mot', [(D16, '08:00', '17:00', 0)], code='TP-X'),
        ]

    def test_first_sync_maps_exact_names_and_projects_days(self):
        result = self.sync(self.week_rows())
        self.assertTrue(result['success'], result)
        exact, similar = self.mapping('syn-a'), self.mapping('syn-x')
        self.assertEqual((exact.state, exact.employee_id), ('mapped', self.emp_a))
        self.assertIn('Khớp chính xác', exact.match_reason)
        # A name that only looks alike (no accents) is never matched automatically; the reason is shown to HR.
        self.assertEqual((similar.state, similar.employee_id.id), ('unmapped', False))
        self.assertIn('Không có nhân viên Odoo nào trùng chính xác', similar.match_reason)
        self.assertEqual(self.EntiDay.search([('key_nv', '=', 'syn-x')]).state, 'pending_map')
        self.assertEqual(self.EntiDay.search_count([('source_id', '=', self.source.id), ('work_date', '>', D18)]), 0)

        full, half = self.day(self.emp_a, D16), self.day(self.emp_a, D17)
        self.assertEqual((full.source_kind, full.in_time, full.out_time, full.data_state), ('enti', '08:42', '17:02', 'ok'))
        self.assertEqual((half.in_time, half.out_time, half.data_state), ('08:10', '', 'missing'))
        self.assertEqual(self.EntiDay.search([('key_nv', '=', 'syn-a'), ('work_date', '=', D16)]).di_muon, 12)
        self.assertTrue(self.source.last_success_at)
        self.assertFalse(self.source.last_error)
        self.assertEqual(len(self.notes), 1)
        self.assertEqual(self.notes[0][1], 'ok')
        self.assertLessEqual({D16, D17}, set(self.notes[0][0]))

        # Newest marks on the dashboard: the in-only day shows "Chưa ghi nhận" for the missing out time.
        overview = self.env_for(self.manager)['tp.hr.attendance.day'].tp_overview({'mode': 'day', 'date': D17.isoformat()})
        mine = [row for row in overview['recent'] if row['employee_id'] == self.emp_a.id]
        self.assertEqual([(row['kind'], row['time'], row['missing']) for row in mine], [('in', '08:10', 'Chưa ghi nhận')])
        self.assertLessEqual(len(overview['recent']), 10)

    def test_unchanged_poll_writes_nothing_and_wakes_no_screen(self):
        self.sync(self.week_rows())
        day = self.day(self.emp_a, D16)
        version, stamp = day.version, self.EntiDay.search([('key_nv', '=', 'syn-a'), ('work_date', '=', D16)]).changed_at
        sessions = self.env['tp.hr.attendance.session'].sudo().search_count([('employee_id', '=', self.emp_a.id)])
        notes = len(self.notes)
        result = self.sync(self.week_rows())
        self.assertTrue(result['success'])
        self.assertEqual((result['changed'], result['days_applied'], result['kept']), (0, 0, 0))
        day.invalidate_recordset()
        self.assertEqual(day.version, version)
        self.assertEqual(self.EntiDay.search([('key_nv', '=', 'syn-a'), ('work_date', '=', D16)]).changed_at, stamp)
        self.assertEqual(self.env['tp.hr.attendance.session'].sudo().search_count([('employee_id', '=', self.emp_a.id)]), sessions)
        self.assertEqual(len(self.notes), notes, 'no bus message when nothing changed')

        # A real change (ENTI late minutes stay ENTI's) is applied and wakes the screens once.
        rows = self.week_rows()
        rows[0]['day2']['raCuoi'] = '17:20'
        result = self.sync(rows)
        self.assertEqual((result['changed'], result['days_applied']), (1, 1))
        self.assertEqual(self.day(self.emp_a, D17).data_state, 'ok')
        self.assertEqual(self.notes[-1], ([D17], 'ok'))

    def test_errors_and_empty_answers_never_erase_attendance(self):
        self.sync(self.week_rows())
        # ENTI suddenly reports no punch for a recorded day: the stored times stay and the pass says so.
        rows = self.week_rows()
        rows[0]['day3'].update(vaoDau=None, raCuoi=None)
        result = self.sync(rows)
        self.assertTrue(result['success'])
        self.assertEqual(result['kept'], 1)
        full = self.day(self.emp_a, D16)
        self.assertEqual((full.in_time, full.out_time, full.data_state), ('08:42', '17:02', 'ok'))

        before = self.notes[:]
        failed = self.sync(self.week_rows(), error=EntiError('ENTI quá thời gian chờ (synthetic)'))
        self.assertFalse(failed['success'])
        self.assertIn('synthetic', self.source.last_error)
        self.assertTrue(self.source.last_error_at)
        self.assertEqual(self.notes[len(before):], [([], 'error')])
        self.assertEqual((self.day(self.emp_a, D16).in_time, self.day(self.emp_a, D17).in_time), ('08:42', '08:10'))
        # The same error again: no second "error" wake-up.
        self.sync(error=EntiError('ENTI quá thời gian chờ (synthetic)'))
        self.assertEqual(self.notes[len(before):], [([], 'error')])
        # An empty board is an error too (never "everyone absent"), and data stays.
        empty = self.sync([])
        self.assertFalse(empty['success'])
        self.assertIn('không trả nhân viên nào', empty['message'])
        self.assertTrue(self.day(self.emp_a, D16))
        # Recovery: success clears the error and tells the screens the source is healthy again.
        self.assertTrue(self.sync(self.week_rows())['success'])
        self.assertFalse(self.source.last_error)
        self.assertEqual(self.notes[-1][1], 'ok')
        logs = self.env['tp.hr.attendance.enti.sync.log'].sudo().search([('source_id', '=', self.source.id)])
        self.assertIn('error', logs.mapped('state'))

    def test_locked_period_keeps_its_values(self):
        self.sync(self.week_rows())
        period = self.env['tp.hr.attendance.period'].sudo().create({
            'name': 'Synthetic locked', 'company_id': self.company.id, 'date_from': D16, 'date_to': D16})
        internal(period).write({'state': 'locked'})
        rows = self.week_rows()
        rows[0]['day3'].update(vaoDau='07:55', raCuoi='17:30')
        self.assertTrue(self.sync(rows)['success'])
        day = self.day(self.emp_a, D16)
        self.assertEqual((day.in_time, day.out_time), ('08:42', '17:02'))
        self.assertEqual(self.EntiDay.search([('key_nv', '=', 'syn-a'), ('work_date', '=', D16)]).state, 'locked_period')

    def test_mapping_needs_evidence_and_one_key_per_employee(self):
        self.sync(self.week_rows())
        # Second ENTI key with the exact same name: never linked to an employee already linked.
        self.sync(self.week_rows() + [enti_row('syn-a2', 'Synthetic Người Một', [(D16, '08:00', '17:00', 0)])])
        twin = self.mapping('syn-a2')
        self.assertEqual((twin.state, twin.employee_id.id), ('suggested', False))
        self.assertIn('đã gắn với một mã ENTI khác', twin.match_reason)
        Manager = self.env_for(self.manager)['tp.hr.attendance.enti.mapping']
        twin_m = Manager.browse(twin.id)
        twin_m.employee_id = self.emp_a
        with self.assertRaises(UserError):
            twin_m.action_confirm_mapping()
        with self.assertRaises(AccessError):
            self.env_for(self.viewer)['tp.hr.attendance.enti.mapping'].browse(self.mapping('syn-x').id).action_confirm_mapping()

        # HR confirms the look-alike with written evidence: the stored ENTI days then reach the board.
        similar = Manager.browse(self.mapping('syn-x').id)
        similar.employee_id = self.emp_b
        reason = 'Synthetic: HR xác nhận cùng một người'
        similar.with_context(tp_mapping_reason=reason).action_confirm_mapping()
        self.assertEqual((similar.state, similar.match_reason), ('mapped', reason))
        self.assertEqual(self.day(self.emp_b, D16).in_time, '08:00')
        self.assertIn([D16], [note[0] for note in self.notes])


# ---------------------------------------------------------------------------------------------- Excel import closed
@tagged('post_install', '-at_install')
class TestExcelImportClosed(AttendanceCase):
    def test_public_import_paths_refuse_and_history_stays_readable(self):
        data = report([{'code': '9901', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05')]}], date(2026, 11, 9), 1)
        history = self.run_batch(data)
        self.assertEqual(history.state, 'applied')
        Batch = self.env_for(self.manager)['tp.hr.attendance.batch']
        upload = {'file_name': 'synthetic.xlsx', 'data': base64.b64encode(data).decode()}
        pair = {'batch_a_id': history.id, 'batch_b_id': 0}
        refused = [
            lambda: Batch.create({'name': 'Forged', 'company_id': self.company.id}),
            lambda: Batch.browse(history.id).action_preview(),
            lambda: Batch.browse(history.id).action_apply(),
            lambda: Batch.tp_upload_preview(upload),
            lambda: Batch.tp_upload_apply(history.id),
            lambda: Batch.tp_upload_files({'files': [upload]}),
            lambda: Batch.tp_apply_compare_valid(pair),
            lambda: Batch.tp_resolve_compare(dict(pair, items=[])),
            lambda: Batch.tp_resolve_compare_batch(dict(pair, items=[])),
        ]
        for call in refused:
            with self.assertRaises(UserError) as caught:
                call()
            self.assertEqual(str(caught.exception), IMPORT_CLOSED)
        for name in ('_tp_upload_files', '_tp_upload_preview', '_tp_upload_apply', '_tp_apply_file', '_tp_new_batch'):
            with self.assertRaises(AccessError):
                get_public_method(Batch, name)

        # History: matrix, compare and their exports still work, read-only.
        matrix = Batch.tp_matrix_data({'batch_id': history.id})
        self.assertFalse(matrix['batch']['can_apply'])
        self.assertFalse(matrix['can_import'])
        self.assertTrue(Batch.tp_export_matrix({'batch_id': history.id})['filename'].endswith('.xlsx'))
        compare = Batch.tp_compare_batches(pair)
        self.assertFalse(compare['can_apply_valid'])
        self.assertTrue(Batch.tp_export_compare(pair)['filename'].endswith('.xlsx'))
        # Old Excel days stay in the board export, marked as history.
        book = load_workbook(BytesIO(base64.b64decode(self.env_for(self.manager)['tp.hr.attendance.day'].tp_export_sheet(
            {'mode': 'range', 'from': '2026-11-09', 'to': '2026-11-09'})['data'])))
        sources = {row[10] for row in book['Chi tiết'].iter_rows(min_row=4, values_only=True) if row[0]}
        self.assertIn('Excel máy (lịch sử)', sources)

        # Import and history menu entries are retired; existing records remain readable and exportable.
        menus = self.env['ir.ui.menu'].with_user(self.manager)._visible_menu_ids()
        self.assertNotIn(self.env.ref('tp_hr_attendance.menu_import').id, menus)
        self.assertFalse(self.env.ref('tp_hr_attendance.menu_file_matrix', raise_if_not_found=False))

    def test_stale_preview_can_still_be_cancelled(self):
        data = report([{'code': '9901', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05')]}], date(2026, 11, 9), 1)
        Batch = self.env_for(self.manager)['tp.hr.attendance.batch']
        preview = Batch._tp_upload_preview({'file_name': 'synthetic.xlsx', 'data': base64.b64encode(data).decode()})
        self.assertEqual(Batch.tp_upload_cancel(preview['batch_id'])['state'], 'cancelled')
        self.assertFalse(self.env['tp.hr.attendance.session'].sudo().search([('employee_id', '=', self.emp_a.id)]))


# ---------------------------------------------------------------------------------------------- export template
class TestExportTemplate(BaseCase):
    DAYS = [D16 + timedelta(days=offset) for offset in range(7)]  # Mon 16 .. Sun 22/11/2026

    def book(self, detail=None):
        days = self.DAYS
        risky = {'code': 'TP1', 'name': '=HYPERLINK("http://synthetic.invalid")', 'job': '+Kỹ thuật',
                 'late': {'count': 1, 'minutes': 10}, 'absent': 1, 'note': '-Thiếu giờ ra: 17/11',
                 'cells': {days[0]: {'state': 'out_recorded', 'in': '08:40', 'out': '17:05', 'late': 10},
                           days[1]: {'state': 'missing', 'in': '08:20', 'out': ''},
                           days[2]: {'state': 'absent'}, days[3]: {'state': 'leave'}, days[4]: {'state': 'no_punch'},
                           days[5]: {'state': 'future'},
                           days[6]: {'state': 'out_recorded', 'in': '09:00', 'out': '11:00', 'late': 0}}}
        unknown = {'code': '', 'name': 'Synthetic B', 'job': '', 'late': {'count': None, 'minutes': None},
                   'absent': 0, 'note': '', 'cells': {}}
        content, totals = build_attendance_book({
            'company': 'Synthetic Co', 'title': 'BẢNG CHẤM CÔNG', 'period': 'Từ 16/11/2026 đến 22/11/2026',
            'scope': 'Toàn công ty', 'stamp': 'Xuất lúc 20/11/2026 10:00', 'days': days,
            'groups': [{'name': 'Synthetic Dept', 'people': [risky, unknown]}], 'legend': ['Ghi chú:', '@legend'],
            'detail': detail})
        return load_workbook(BytesIO(content)), totals

    def test_matrix_layout_symbols_and_totals(self):
        book, totals = self.book()
        self.assertEqual(book.sheetnames, ['Bảng chấm công'])
        sheet = book['Bảng chấm công']
        self.assertEqual(sheet['A1'].value, 'TANPHAT ONE · Synthetic Co')
        self.assertEqual((sheet.freeze_panes, sheet.page_setup.orientation), ('F9', 'landscape'))
        self.assertEqual([sheet.cell(7, 6 + i).value.date() for i in range(7)], self.DAYS)
        self.assertEqual([sheet.cell(8, 6 + i).value for i in range(7)], ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'])
        self.assertEqual(sheet['A9'].value, 'Synthetic Dept · 2 người')
        self.assertEqual((sheet['E10'].value, sheet['E11'].value), ('Vào', 'Ra'))
        self.assertEqual((sheet['F10'].value, sheet['F11'].value), (time(8, 40), time(17, 5)))
        self.assertEqual(sheet['F10'].number_format, 'hh:mm')
        self.assertTrue(sheet['F10'].fill.start_color.rgb.endswith('FED7AA'), 'late first-in is orange')
        self.assertEqual((sheet['G10'].value, sheet['G11'].value), (time(8, 20), '—'))
        self.assertTrue(sheet['G11'].fill.start_color.rgb.endswith('FEF08A'), 'missing out time is yellow')
        self.assertEqual((sheet['H10'].value, sheet['I10'].value, sheet['J10'].value), ('Vắng', 'Nghỉ', '—'))
        self.assertIn(sheet['K10'].value, (None, ''))
        self.assertEqual(sheet['L10'].value, time(9, 0), 'Sunday keeps its real times')
        self.assertEqual((sheet['M10'].value, sheet['N10'].value, sheet['O10'].value), (1, 10, 1))
        self.assertEqual((sheet['F12'].value, sheet['M12'].value, sheet['N12'].value, sheet['O12'].value), ('—', '—', '—', 0))
        self.assertEqual((sheet['M14'].value, sheet['N14'].value, sheet['O14'].value), (1, 10, 1))
        self.assertIn('1 người thiếu dữ liệu đi muộn', sheet['P14'].value)
        self.assertEqual(totals, {'count': 1, 'minutes': 10, 'absent': 1, 'late_unknown': 1})
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str):
                    self.assertFalse(cell.value.startswith(('=', '+', '-', '@')), cell.coordinate)
        self.assertEqual(sheet['C10'].value, '\'=HYPERLINK("http://synthetic.invalid")')

    def test_detail_sheet_rows(self):
        detail = {'title': 'Chi tiết synthetic', 'rows': [
            {'department': 'Synthetic Dept', 'code': 'TP1', 'name': '@Synthetic', 'job': '', 'date': D17,
             'in': '08:20', 'out': '', 'late': None, 'state': 'missing', 'state_label': 'Thiếu giờ ra', 'source': 'ENTI'},
        ]}
        book, _totals = self.book(detail)
        self.assertEqual(book.sheetnames, ['Bảng chấm công', 'Chi tiết'])
        rows = [row for row in book['Chi tiết'].iter_rows(min_row=4, values_only=True) if row[0]]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][:8], ('Synthetic Dept', 'TP1', "'@Synthetic", '—', datetime(2026, 11, 17), 'T3', time(8, 20), '—'))
        self.assertEqual(rows[0][8:], ('—', 'Thiếu giờ ra', 'ENTI'))
        self.assertEqual(book['Chi tiết'].freeze_panes, 'D4')

    def test_person_note_lists_only_what_needs_checking(self):
        days = self.DAYS
        cells = {days[0]: {'state': 'missing', 'in': '', 'out': '17:00'},
                 days[1]: {'state': 'missing', 'in': '08:00', 'out': ''},
                 days[2]: {'state': 'review', 'in': '08:00', 'out': '17:00'},
                 days[3]: {'state': 'out_recorded', 'in': '08:00', 'out': '17:00'}}
        note = person_note(cells, {'state': 'partial', 'text': 'Số đi muộn có ở tổng kỳ 09–15/11'}, {'unknown': 2},
                           archived=True)
        self.assertEqual(note.split('\n'), [
            'Thiếu giờ vào: 16/11', 'Thiếu giờ ra: 17/11', 'Cần kiểm tra: 18/11',
            'Chưa có dữ liệu 2 ngày làm (không tính vắng)', 'Đi muộn: Số đi muộn có ở tổng kỳ 09–15/11',
            'Hồ sơ đã lưu trữ, vẫn có dữ liệu trong kỳ'])
        excel = person_note({}, {'state': 'exact', 'source': 'Excel', 'note': 'tổng kỳ Excel 09–15/11'}, {})
        self.assertEqual(excel, 'Đi muộn lấy theo tổng kỳ Excel 09–15/11')
        self.assertEqual(person_note({days[3]: cells[days[3]]}, {'state': 'exact', 'source': 'ENTI'}, {'unknown': 0}), '')

    def test_recent_people_newest_first_distinct_and_capped(self):
        base = datetime(2026, 11, 20, 1, 0)
        by_person = {pid: [{'in_at': base + timedelta(minutes=pid), 'out_at': None}] for pid in range(1, 13)}
        by_person[3] = [{'in_at': base, 'out_at': None}, {'in_at': base, 'out_at': base + timedelta(hours=9)}]
        by_person[20] = [{'in_at': None, 'out_at': None}]
        rows = recent_people(by_person)
        self.assertEqual(len(rows), 10)
        self.assertEqual(len({row['employee_id'] for row in rows}), 10)
        self.assertEqual((rows[0]['employee_id'], rows[0]['kind']), (3, 'out'))
        self.assertEqual([row['employee_id'] for row in rows[1:]], [12, 11, 10, 9, 8, 7, 6, 5, 4])
        self.assertEqual([row['at'] for row in rows], sorted((row['at'] for row in rows), reverse=True))
        self.assertNotIn(20, [row['employee_id'] for row in rows])
