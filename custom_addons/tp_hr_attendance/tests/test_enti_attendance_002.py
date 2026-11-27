"""ENTI-ATTENDANCE-002 (synthetic data only, no network, no real ENTI account).

- ENTI HTTP client with a fake session: nested login tokens, refresh before expiry, 401 renewal, 429 Retry-After,
  bounded 5xx / network retries, invalid JSON, full pagination with de-duplication, partial board refused.
- One sync pass with a fake client: exact-name mapping only, date from ``ngay`` (never the slot), in-only day,
  unchanged poll writes nothing and wakes no screen, empty punch keeps old times, errors keep data and report
  health once, locked period untouched, mapping evidence and one ENTI key per employee.
- Excel file import closed: every public write RPC refuses, private helpers are not callable remotely, the
  history stays readable and exportable.
- Export template ("Bảng chấm công"): layout, time cells, symbols, totals, formula neutralisation; the employee
  note.
- ATTENDANCE-DASH-004 dashboard: one group per person and day (in only → Đang làm, out → Đã về, nothing on a
  covered day → Chưa đi làm, no source / source down → Chưa xác định), card number = dialog list total, dialog
  search / department / paging, the employee read scope, newest marks from the source's real clocks (seconds
  only when the source has them, no invented place) and the helpers behind them.
"""
import base64
import copy
import threading
from datetime import date, datetime, timedelta
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

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
    export_late_totals,
    person_note,
    worked_days_count,
)
from odoo.addons.tp_hr_attendance.models.attendance_figures import (
    class_date,
    clock_has_seconds,
    day_group,
    fold_text,
    group_counts,
    recent_marks,
)
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

        # Newest marks on the dashboard: the in-only day gives one "in" mark (internal code, "HH:MM" as the source
        # gave it, no place) and puts the person in "Đang làm".
        overview = self.env_for(self.manager)['tp.hr.attendance.day'].tp_overview({'mode': 'day', 'date': D17.isoformat()})
        mine = [row for row in overview['recent'] if row['employee_id'] == self.emp_a.id]
        self.assertEqual([(row['kind'], row['time'], row['code'], row['location']) for row in mine],
                         [('in', '08:10', 'TP991', '')])
        self.assertLessEqual(len(overview['recent']), 10)
        self.assertEqual((overview['groups']['date'], overview['groups']['counts']['working']), (D17.isoformat(), 1))

    def test_dashboard_groups_match_dialog_lists_and_recent_marks_use_real_clocks(self):
        rows = [
            # A: 16/11 out only, 17/11 in only (the source clock carries real seconds), 18/11 nothing on a covered day.
            enti_row('syn-a', 'Synthetic Người Một', [(D16, None, '2026-11-16T17:02:05', 0),
                                                      (D17, '2026-11-17T08:10:23', None, 0), (D18, None, None, 0)]),
            # B: 17/11 in and out as "HH:MM" (no seconds may be invented); nothing at all for 16/11 and 18/11.
            enti_row('syn-b', 'Synthetic Người Hai', [(D17, '08:05', '17:30', 0)]),
            enti_row('syn-x', 'Synthetic Nguoi Mot', [(D17, '08:00', '17:00', 0)], code='TP-X'),
        ]
        self.assertTrue(self.sync(rows)['success'])
        Day = self.env_for(self.manager)['tp.hr.attendance.day']

        def scope(work_date, **extra):
            return dict({'mode': 'day', 'date': work_date.isoformat()}, **extra)

        def listed(work_date, group, **extra):
            return Day.tp_overview_group(scope(work_date, group=group, class_date=work_date.isoformat(), **extra))

        def members(work_date, group):
            return {row['employee_id']: row for row in listed(work_date, group, page_size=50)['rows']}

        expected = {D16: {'done': self.emp_a, 'unknown': self.emp_b},
                    D17: {'working': self.emp_a, 'done': self.emp_b},
                    D18: {'not_started': self.emp_a, 'unknown': self.emp_b}}
        for work_date, by_group in expected.items():
            overview = Day.tp_overview(scope(work_date))
            groups = overview['groups']
            self.assertEqual(groups['date'], work_date.isoformat())
            for group in ('working', 'done', 'not_started', 'unknown'):
                # On open, the card number is the dialog's list total (same scope, policy and classification).
                self.assertEqual(listed(work_date, group)['group_total'], groups['counts'][group], (work_date, group))
            for group, employee in by_group.items():
                self.assertIn(employee.id, members(work_date, group), (work_date, group))
        # Unmapped source rows never become anybody; an unknown person is never counted as "Chưa đi làm".
        self.assertEqual(members(D16, 'unknown')[self.emp_b.id]['note'],
                         'Chưa có dữ liệu nguồn cho ngày này (chưa ghép mã hoặc nguồn chưa trả)')
        self.assertNotIn(self.emp_b.id, members(D16, 'not_started'))
        out_only = members(D16, 'done')[self.emp_a.id]
        self.assertEqual((out_only['in'], out_only['out'], out_only['note']), ('', '17:02', 'Thiếu giờ vào'))
        self.assertEqual(members(D17, 'working')[self.emp_a.id]['note'], 'Thiếu giờ ra')

        # Newest marks of 17/11: newest first, one row per mark, real seconds only where the source has them.
        overview = Day.tp_overview(scope(D17))
        recent = [(row['employee_id'], row['kind'], row['time'], row['code'], row['location']) for row in overview['recent']]
        self.assertEqual(recent, [(self.emp_b.id, 'out', '17:30', 'TP992', ''), (self.emp_a.id, 'in', '08:10:23', 'TP991', ''),
                                  (self.emp_b.id, 'in', '08:05', 'TP992', '')])
        self.assertEqual(len({row['key'] for row in overview['recent']}), len(overview['recent']))
        self.assertEqual((overview['recent_info']['mode'], overview['recent_info']['title']), ('daily', 'Chấm công gần nhất'))
        self.assertNotIn('raw_json', str(overview))
        # The dialog's own search (accent-free), department filter and page sizes narrow only that group.
        self.assertEqual([row['employee_id'] for row in listed(D17, 'done', q='nguoi hai')['rows']], [self.emp_b.id])
        self.assertEqual(listed(D17, 'done', q='TP991')['total'], 0)
        other = listed(D17, 'done', dept=self.dept_other.id)
        self.assertEqual((other['dept'], [row['employee_id'] for row in other['rows']]), (self.dept_other.id, [self.emp_b.id]))
        # A department with nobody in the group is not offered and falls back to all (e.g. after a live update).
        stale = listed(D17, 'done', dept=self.dept.id)
        self.assertEqual((stale['dept'], stale['total'], [entry['id'] for entry in stale['departments']]),
                         (0, 1, [self.dept_other.id]))
        self.assertEqual(listed(D17, 'done', page_size=999)['page_size'], 20)
        self.assertEqual(listed(D17, 'done', page_size=50)['page_size'], 50)

        # An ordinary employee gets the same layout under the current read policy (company attendance days, read
        # only): counts and lists agree, and the rows carry no private HR data and no link to a profile.
        own = self.env_for(self.viewer)['tp.hr.attendance.day']
        mine = own.tp_overview(scope(D17))
        self.assertEqual(mine['groups']['counts'], overview['groups']['counts'])
        for group in ('working', 'done', 'not_started', 'unknown'):
            seen = own.tp_overview_group(scope(D17, group=group, page_size=50))
            self.assertEqual(seen['group_total'], mine['groups']['counts'][group], group)
            for row in seen['rows']:
                self.assertEqual(set(row), {'stt', 'employee_id', 'code', 'name', 'department', 'date', 'in', 'out', 'note'})
        self.assertEqual(set(mine['recent'][0]), {'key', 'employee_id', 'code', 'name', 'time', 'kind', 'location'})
        with self.assertRaises(AccessError):
            self.env(user=self.env.ref('base.public_user'))['tp.hr.attendance.day'].tp_overview_group(scope(D17))

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

        # HR confirms the look-alike with written evidence (both inline match_reason and context work): ENTI days reach the board.
        similar = Manager.browse(self.mapping('syn-x').id)
        similar.write({'employee_id': self.emp_b.id, 'match_reason': 'Synthetic: HR xác nhận trực tiếp trên danh sách'})
        similar.action_confirm_mapping()
        self.assertEqual((similar.state, similar.match_reason), ('mapped', 'Synthetic: HR xác nhận trực tiếp trên danh sách'))
        self.assertEqual(self.day(self.emp_b, D16).in_time, '08:00')
        self.assertIn([D16], [note[0] for note in self.notes])

    def test_approved_leave_and_punch_conflict_and_multiday_sheet_state_filter(self):
        """F-A04-0001 & F-A04-0009: approved leave without punch -> 'leave'; approved leave + machine punch -> 'review' + conflict_note; week state filter matches."""
        self.sync([
            enti_row('syn-a', 'Synthetic Người Một', [(D16, '08:15', '17:05', 0), (D18, None, None, 0)]),
        ])
        DayModel = type(self.env['tp.hr.attendance.day'])
        fake_leaves = {
            (self.emp_a.id, D16): 'Đơn xin nghỉ phép đã duyệt',
            (self.emp_a.id, D18): 'Đơn công tác đã duyệt',
        }
        with self.mock_patch_leave_days(DayModel, fake_leaves):
            DayMgr = self.env_for(self.manager)['tp.hr.attendance.day']
            sheet = DayMgr.tp_sheet({'mode': 'week', 'date': D16.isoformat(), 'state': 'review'})
            self.assertEqual([r['id'] for r in sheet['rows']], [self.emp_a.id])
            cells = {c['date']: c for c in sheet['rows'][0]['cells']}
            self.assertEqual(cells[D16.isoformat()]['state'], 'review')
            self.assertIn('Xung đột', cells[D16.isoformat()]['conflict_note'])
            self.assertEqual(cells[D18.isoformat()]['state'], 'leave')
            self.assertEqual(cells[D18.isoformat()]['leave_note'], 'Đơn công tác đã duyệt')

            mine = self.env_for(self.viewer)['tp.hr.attendance.day'].tp_mine({'mode': 'week', 'date': D16.isoformat()})
            mine_rows = {r['date']: r for r in mine['rows']}
            self.assertEqual(mine_rows[D16.isoformat()]['state'], 'review')
            self.assertIn('Xung đột', mine_rows[D16.isoformat()]['conflict_note'])
            self.assertEqual(mine_rows[D18.isoformat()]['state'], 'leave')
            self.assertEqual(mine_rows[D18.isoformat()]['leave_note'], 'Đơn công tác đã duyệt')

    @staticmethod
    def mock_patch_leave_days(day_cls, fake_map):
        return patch.object(day_cls, '_tp_leave_days', lambda _self, _company, _ids, _start, _end: dict(fake_map))

    # HR-EMPLOYEE-CODE-003 -------------------------------------------------------------------------------------
    def test_enti_code_never_picks_one_of_same_name_employees(self):
        # ENTI maNV and internal TP codes are separate number spaces: an ENTI code equal to one candidate's
        # internal code is not evidence, so two same-name employees stay "suggested" for HR.
        twin = self.env['hr.employee'].with_company(self.company).create({
            'name': 'Synthetic Người Một', 'company_id': self.company.id, 'tp_employee_code': 'TP993'})
        self.sync([enti_row('syn-same', 'Synthetic Người Một', [(D16, '08:00', '17:00', 0)], code='TP993')])
        same = self.mapping('syn-same')
        self.assertEqual((same.state, same.employee_id.id), ('suggested', False))
        self.assertIn('Có 2 nhân viên Odoo trùng họ tên', same.match_reason)
        self.assertFalse(self.day(twin, D16) or self.day(self.emp_a, D16))
        self.assertEqual((twin.tp_employee_code, self.emp_a.tp_employee_code), ('TP993', 'TP991'))

    def test_code_conversion_refreshes_attendance_copies_only(self):
        self.sync(self.week_rows())
        request = self.env_for(self.viewer)['tp.hr.attendance.correction'].create({
            'work_date': D18, 'requested_in': 8.0, 'requested_out': 17.0, 'reason': 'Synthetic private reason'})
        period = self.env['tp.hr.attendance.period'].sudo().create({
            'name': 'Synthetic locked', 'company_id': self.company.id, 'date_from': D16, 'date_to': D16})
        internal(period).write({'state': 'locked'})
        Day = self.env['tp.hr.attendance.day'].sudo()
        days = Day.search([('employee_id', '=', self.emp_a.id)])
        self.assertEqual(set(days.mapped('employee_code')), {'TP991'})

        def figures():
            return {d.id: (d.work_date, d.in_time, d.out_time, d.recorded_hours, d.units, d.units_state, d.data_state, d.version)
                    for d in Day.search([('employee_id', '=', self.emp_a.id)])}
        before = figures()
        # The profile and its stored copies as they were before the upgrade (former TP1nnnn form).
        self.env.cr.execute('UPDATE hr_employee SET tp_employee_code=%s WHERE id=%s', ['TP10991', self.emp_a.id])
        self.env.cr.execute('UPDATE tp_hr_attendance_day SET employee_code=%s WHERE employee_id=%s', ['TP10991', self.emp_a.id])
        self.env.cr.execute('UPDATE tp_hr_attendance_correction SET employee_code=%s WHERE id=%s', ['TP10991', request.id])
        self.env.invalidate_all()
        # The upgrade path (tp_organization conversion; the attendance override refreshes the copies).
        result = self.env['hr.employee']._tp_code_format_apply('Synthetic format conversion', self.emp_a | self.emp_b)
        self.assertEqual(result['changed'], [(self.emp_a.id, 'TP10991', 'TP991')])
        self.env.invalidate_all()
        self.assertEqual(set(Day.search([('employee_id', '=', self.emp_a.id)]).mapped('employee_code')), {'TP991'})
        self.assertEqual(request.sudo().employee_code, 'TP991')
        self.assertEqual(figures(), before)
        self.assertEqual(period.state, 'locked')
        self.assertEqual(result['kept'], 1)
        self.assertEqual(self.emp_b.tp_employee_code, 'TP992')
        # The attendance upgrade step finds nothing left to refresh.
        self.assertEqual(self.env['hr.employee'].search([('company_id', '=', self.company.id)])._tp_sync_attendance_code(), 0)
        # ENTI keeps its own key: the next cycle lands on the same profile, with no duplicate day and the new code.
        mapping = self.mapping('syn-a')
        self.assertTrue(self.sync(self.week_rows())['success'])
        self.assertEqual((self.mapping('syn-a'), self.mapping('syn-a').employee_id), (mapping, self.emp_a))
        self.assertEqual(set(figures()), set(before))
        self.assertFalse(Day.search_count([('employee_code', 'in', ['TP10991', 'TP10992'])]))
        overview = self.env_for(self.manager)['tp.hr.attendance.day'].tp_overview({'mode': 'day', 'date': D17.isoformat()})
        self.assertEqual({row['code'] for row in overview['recent'] if row['employee_id'] == self.emp_a.id}, {'TP991'})


# ---------------------------------------------------------------------------------------------- Excel import closed
@tagged('post_install', '-at_install')
class TestExcelImportClosed(AttendanceCase):
    def test_public_import_paths_refuse_and_history_stays_readable(self):
        data = report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05')]}], date(2026, 11, 9), 1)
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
        # Old Excel days stay in the Report export.
        book = load_workbook(BytesIO(base64.b64decode(self.env_for(self.manager)['tp.hr.attendance.day'].tp_export_sheet(
            {'mode': 'range', 'from': '2026-11-09', 'to': '2026-11-09'})['data'])))
        self.assertEqual(book.sheetnames, ['Report'])
        ws = book['Report']
        vao_rows = [r for r in range(7, ws.max_row + 1) if ws.cell(r, 6).value == 'Vào']
        self.assertTrue(any(ws.cell(r, 7).value == '07:37' and ws.cell(r + 1, 7).value == '17:05' for r in vao_rows))

        # Import and history menu entries are retired; existing records remain readable and exportable.
        menus = self.env['ir.ui.menu'].with_user(self.manager)._visible_menu_ids()
        self.assertNotIn(self.env.ref('tp_hr_attendance.menu_import').id, menus)
        self.assertFalse(self.env.ref('tp_hr_attendance.menu_file_matrix', raise_if_not_found=False))

    def test_stale_preview_can_still_be_cancelled(self):
        data = report([{'code': '991', 'name': 'Synthetic Người Một', 'times': [('07:37', '17:05')]}], date(2026, 11, 9), 1)
        Batch = self.env_for(self.manager)['tp.hr.attendance.batch']
        preview = Batch._tp_upload_preview({'file_name': 'synthetic.xlsx', 'data': base64.b64encode(data).decode()})
        self.assertEqual(Batch.tp_upload_cancel(preview['batch_id'])['state'], 'cancelled')
        self.assertFalse(self.env['tp.hr.attendance.session'].sudo().search([('employee_id', '=', self.emp_a.id)]))


# ---------------------------------------------------------------------------------------------- export template
class TestExportTemplate(BaseCase):
    DAYS = [D16 + timedelta(days=offset) for offset in range(7)]  # Mon 16 .. Sun 22/11/2026

    def book(self, days=None, groups=None):
        days = days or self.DAYS
        if groups is None:
            risky_cells = {
                days[0]: {'state': 'out_recorded', 'in': '08:40:25', 'out': '17:05:10', 'late': 10},
                days[1]: {'state': 'missing', 'in': '08:20', 'out': ''},
                days[2]: {'state': 'missing', 'in': '', 'out': '17:10'},
                days[3]: {'state': 'leave'},
                days[4]: {'state': 'absent'},
                days[5]: {'state': 'future'},
                days[6]: {'state': 'out_recorded', 'in': '09:00', 'out': '11:00', 'late': 30},
            }
            risky = {
                'code': 'TP1',
                'name': '=HYPERLINK("http://synthetic.invalid")',
                'machine_code': '11',
                'job': '+Kỹ thuật',
                'late': {'count': 1, 'minutes': 10},
                'worked_days': worked_days_count(risky_cells),
                'note': person_note(risky_cells, today=days[4]),
                'cells': risky_cells,
            }
            unknown_cells = {day: {'state': 'no_source'} for day in days if day.weekday() != 6}
            unknown = {
                'code': '',
                'name': 'Synthetic B',
                'machine_code': '',
                'job': '',
                'late': {'count': 0, 'minutes': 0},
                'worked_days': 0,
                'note': person_note(unknown_cells, today=days[-1]),
                'cells': unknown_cells,
            }
            groups = [{'name': 'Synthetic Dept', 'people': [risky, unknown]}]
        content, totals = build_attendance_book({
            'title': 'BẢNG CÔNG THÁNG',
            'period': f'Từ ngày {days[0]:%d/%m/%Y} - Đến ngày {days[-1]:%d/%m/%Y}',
            'days': days,
            'groups': groups,
        })
        return load_workbook(BytesIO(content)), totals

    def test_report_layout_symbols_and_totals(self):
        book, totals = self.book()
        self.assertEqual(book.sheetnames, ['Report'])
        sheet = book['Report']
        self.assertEqual(sheet['A2'].value, 'BẢNG CÔNG THÁNG')
        self.assertEqual(sheet['A3'].value, 'Từ ngày 16/11/2026 - Đến ngày 22/11/2026')
        self.assertEqual((sheet.freeze_panes, sheet.page_setup.orientation), ('G7', 'landscape'))
        self.assertEqual(sheet.print_title_rows.replace('$', ''), '5:6')
        self.assertTrue(bool(sheet.print_area))
        self.assertEqual([sheet.cell(5, c).value for c in range(1, 7)],
                         ['STT', 'Mã nhân viên', 'Tên nhân viên', 'ID', 'Chức vụ', 'Vào/Ra'])
        self.assertEqual([sheet.cell(5, 7 + i).value for i in range(7)], [16, 17, 18, 19, 20, 21, 22])
        self.assertEqual([sheet.cell(6, 7 + i).value for i in range(7)], ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'])
        self.assertEqual((sheet['N5'].value, sheet['N6'].value, sheet['O6'].value), ('Đi muộn', 'Lần', 'Phút'))
        self.assertEqual((sheet['P5'].value, sheet['Q5'].value), ('Số ngày', 'Ghi chú'))
        self.assertEqual(sheet['A7'].value, 'Synthetic Dept')

        # Employee 1: row 8 (Vào) and row 9 (Ra)
        self.assertEqual((sheet['A8'].value, sheet['B8'].value, sheet['D8'].value, sheet['F8'].value),
                         (1, 'TP1', 11, 'Vào'))
        self.assertIsNone(sheet['A9'].value)
        self.assertIsNone(sheet['B9'].value)
        self.assertIsNone(sheet['C9'].value)
        self.assertIsNone(sheet['D9'].value)
        self.assertIsNone(sheet['E9'].value)
        self.assertEqual(sheet['F9'].value, 'Ra')
        self.assertEqual(sheet['C8'].alignment.horizontal, 'left')
        self.assertEqual(sheet['E8'].alignment.horizontal, 'center')
        self.assertEqual((sheet['G8'].value, sheet['G9'].value), ('08:40', '17:05'))
        self.assertEqual((sheet['H8'].value, sheet['H9'].value), ('08:20', None))
        self.assertEqual((sheet['I8'].value, sheet['I9'].value), (None, '17:10'))
        self.assertIsNone(sheet['J8'].value)
        self.assertIsNone(sheet['K8'].value)
        self.assertIsNone(sheet['L8'].value)
        self.assertEqual((sheet['M8'].value, sheet['M9'].value), ('09:00', '11:00'))
        self.assertEqual((sheet['N8'].value, sheet['O8'].value, sheet['P8'].value), (1, 10, 3))
        self.assertIsNone(sheet['N9'].value)
        self.assertIsNone(sheet['O9'].value)
        self.assertIsNone(sheet['P9'].value)
        self.assertIn('Thiếu giờ vào: 18/11', sheet['Q8'].value)
        self.assertIn('Thiếu giờ ra: 17/11', sheet['Q8'].value)
        self.assertIn('Nghỉ: 19/11', sheet['Q8'].value)

        # Employee 2: row 10-11 (no data -> 0 late, 0 worked days)
        self.assertEqual((sheet['A10'].value, sheet['N10'].value, sheet['O10'].value, sheet['P10'].value),
                         (2, 0, 0, 0))
        self.assertEqual(sheet['Q10'].value, 'Không có dữ liệu trong kỳ')
        self.assertEqual(totals, {'people': 2, 'count': 1, 'minutes': 10, 'worked_days': 3})

        # Formula injection neutralized & no NaN/null/undefined
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str):
                    self.assertFalse(cell.value.startswith(('=', '+', '-', '@')), cell.coordinate)
                    self.assertNotIn('NaN', cell.value)
                    self.assertNotIn('undefined', cell.value)
        self.assertEqual(sheet['C8'].value, '\'=HYPERLINK("http://synthetic.invalid")')

    def test_empty_period_two_weeks_and_month_layouts(self):
        empty_book, totals = self.book(days=self.DAYS, groups=[])
        self.assertEqual(totals['people'], 0)
        self.assertEqual(empty_book['Report']['A7'].value, 'Không có dữ liệu trong kỳ đã chọn')

        two_weeks = [D16 + timedelta(days=offset) for offset in range(14)]
        two_week_book, _ = self.book(days=two_weeks, groups=[])
        self.assertEqual(two_week_book['Report'].cell(5, 7 + 13).value, 29)

        month_days = [date(2026, 11, 1) + timedelta(days=offset) for offset in range(30)]
        month_book, _ = self.book(days=month_days, groups=[])
        self.assertEqual(month_book['Report'].cell(5, 7 + 29).value, 30)
        self.assertEqual(month_book['Report'].cell(5, 7 + 30).value, 'Đi muộn')

    def test_late_and_worked_days_rules(self):
        days = self.DAYS
        cells = {
            days[0]: {'state': 'out_recorded', 'in': '08:30', 'out': '17:00', 'late': None, 'scheduled': True},
            days[1]: {'state': 'out_recorded', 'in': '08:42', 'out': '17:05', 'late': None, 'scheduled': True},
            days[2]: {'state': 'missing', 'in': '', 'out': '17:05', 'late': None, 'scheduled': True},
            days[3]: {'state': 'leave', 'scheduled': True},
            days[4]: {'state': 'out_recorded', 'in': '08:40', 'out': '17:00', 'late': 5, 'scheduled': True},
            days[6]: {'state': 'out_recorded', 'in': '09:30', 'out': '12:00', 'late': 60, 'scheduled': False},
        }
        # Exact 08:30 -> 0; 08:42 fallback -> 12 min; ENTI late=5 preserved; Sunday excluded; missing-in excluded.
        self.assertEqual(export_late_totals(cells, view={'state': 'partial'}, start_hour=8.5, today=days[6]), (2, 17))
        # Sunday is excluded from worked_days; days[0], days[1], days[2] (has out), days[4] count = 4.
        self.assertEqual(worked_days_count(cells), 4)
        # Pre-aggregated exact historical Excel source total is preserved without recalculation.
        self.assertEqual(
            export_late_totals(cells, view={'state': 'exact', 'source': '09-15/11', 'count': 4, 'minutes': 99}),
            (4, 99),
        )

    def test_person_note_lists_only_what_needs_checking(self):
        days = self.DAYS
        cells = {
            days[0]: {'state': 'missing', 'in': '', 'out': '17:00'},
            days[1]: {'state': 'missing', 'in': '08:00', 'out': ''},
            days[2]: {'state': 'review', 'in': '08:00', 'out': '17:00'},
            days[3]: {'state': 'out_recorded', 'in': '08:00', 'out': '17:00'},
        }
        note = person_note(cells, duplicate_days={days[2]}, archived=True)
        self.assertEqual(note.split('\n'), [
            'Thiếu giờ vào: 16/11',
            'Thiếu giờ ra: 17/11',
            'Có dữ liệu bất thường: 18/11',
            'Có bản ghi trùng cần đối chiếu: 18/11',
            'Hồ sơ đã lưu trữ',
        ])
        self.assertEqual(person_note({days[3]: cells[days[3]]}), '')

    def test_day_group_one_group_per_day_and_unknown_is_never_not_started(self):
        def cell(state='absent', clock_in='', clock_out='', covered=True):
            return {'state': state, 'in': clock_in, 'out': clock_out, 'covered': covered}

        cases = [
            (cell('missing', '08:00'), True, ('working', '')),             # in, no out
            (cell('ok', '08:00', '17:00'), True, ('done', '')),            # in and out
            (cell('missing', '', '17:00'), True, ('done', '')),            # out only (missing in noted in the list)
            (cell(), True, ('not_started', '')),                           # covered day, no mark at all
            (cell('no_data', covered=False), True, ('unknown', 'no_source')),  # unmapped / source never answered
            (cell(), False, ('unknown', 'source_down')),                   # today while the live source is down
            (cell('review'), True, ('unknown', 'review')),
            (cell('future'), True, (None, '')),
            (cell('off'), True, (None, '')),
        ]
        for value, live_ok, expected in cases:
            self.assertEqual(day_group(value, live_ok), expected, value)
        # Marks win over a down source: someone who punched in is "Đang làm" even when the source is stale.
        self.assertEqual(day_group(cell('missing', '08:00'), live_ok=False), ('working', ''))
        counts, reasons, excluded = group_counts([value for value, _live, _expected in cases])
        self.assertEqual(counts, {'working': 1, 'done': 2, 'not_started': 2, 'unknown': 2})
        self.assertEqual((reasons['no_source'], reasons['review'], reasons['source_down'], excluded), (1, 1, 0, 2))

    def test_class_date_seconds_search_and_recent_marks(self):
        today = date(2026, 11, 20)
        self.assertEqual(class_date(date(2026, 11, 16), date(2026, 11, 22), today), today)
        self.assertEqual(class_date(date(2026, 11, 23), date(2026, 11, 29), today), date(2026, 11, 23))
        self.assertEqual(class_date(D16, D18, today, {D16, D17, date(2026, 11, 1)}), D17)
        self.assertEqual(class_date(D16, D18, today), D18)
        # Past week ending on a markless Sunday steps back to Saturday (last working day).
        self.assertEqual(class_date(date(2026, 11, 9), date(2026, 11, 15), today), date(2026, 11, 14))
        for raw, expected in (('2026-11-17T08:10:23', True), ('2026-11-17T08:10:00', True), ('08:10:23', True),
                              ('08:10', False), ('', False), (None, False), ('2026-11-17T08:10', False)):
            self.assertEqual(clock_has_seconds(raw), expected, raw)
        self.assertEqual(fold_text('Đỗ Thị HƯƠNG'), 'do thi huong')
        self.assertIn(fold_text('huong'), fold_text('Nguyễn Thị Hương'))

        base = datetime(2026, 11, 20, 8, 0)
        marks = [{'key': f'm{index}', 'at': base + timedelta(minutes=index), 'kind': 'in', 'order': index}
                 for index in range(12)]
        marks.append(dict(marks[11]))                                              # the same event twice: kept once
        marks.append({'key': 'm11-out', 'at': marks[11]['at'], 'kind': 'out', 'order': 11})  # a real second mark
        rows = recent_marks(marks)
        self.assertEqual(len(rows), 10)
        self.assertEqual([row['key'] for row in rows[:3]], ['m11-out', 'm11', 'm10'])
        self.assertEqual(len({row['key'] for row in rows}), 10)
        self.assertEqual([row['at'] for row in rows], sorted((row['at'] for row in rows), reverse=True))
