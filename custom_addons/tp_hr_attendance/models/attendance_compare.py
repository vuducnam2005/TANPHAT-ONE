"""A/B source file comparison, multi-source provenance & audited conflict resolution (HR-ATTENDANCE-MATRIX-003, DEC-058).

Key invariants enforced in PostgreSQL transactions:
1. Same normalized hours across A and B produce ONE canonical ``tp.hr.attendance.session`` linked to both
   source batches/lines via ``source_batch_ids`` / ``source_line_ids`` (never double-counted).
2. Different hours/totals NEVER auto-overwrite by newest upload and NEVER splice Vào from A with Ra from B.
   An authorized import user must pick ``keep_current`` / ``use_a`` / ``use_b`` / ``defer`` with an explicit
   scope and reason (when changing already-applied data).
3. Locked periods and approved corrections (``source='correction'``) cannot be overwritten from file comparison.
4. Before applying or resolving, the backend recomputes state and verifies CAS ``expected_digest`` under lock so
   concurrent tabs or retries never apply stale comparisons or duplicate rows.
"""
import base64
import hashlib
import json
from collections import defaultdict
from datetime import time as dt_time
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .attendance_common import (
    DEFAULT_TZ,
    deny_direct,
    fold,
    internal,
    local_to_utc,
    require,
    utc_to_local,
)
from .attendance_import import COUNTED, LATE_COUNTED
from .attendance_logic import short_range, xlsx_safe
from .attendance_matrix import (
    EMPTY_GROUP_KEY,
    MATRIX_PAGE_SIZES,
    _fmt_date,
    _parse_iso_date,
)

COMPARE_GROUPS = [
    ('same', 'Giống nhau'),
    ('only_a', 'Chỉ có ở A'),
    ('only_b', 'Chỉ có ở B'),
    ('diff', 'Khác giờ hoặc số liệu'),
    ('unready', 'Chưa đủ căn cứ / Thiếu mapping'),
]
COMPARE_GROUP_LABELS = dict(COMPARE_GROUPS)

SCOPE_LABELS = {
    'in_period': 'Trong kỳ nguồn',
    'blank_in_period': 'Ô trống trong kỳ',
    'out_of_scope': 'Ngoài phạm vi file',
    'not_in_file': 'Không có trong file',
    'no_batch_b': 'Chưa chọn file B',
}

DECISIONS = [
    ('keep_current', 'Giữ dữ liệu đang áp dụng'),
    ('use_a', 'Dùng bản A'),
    ('use_b', 'Dùng bản B'),
    ('defer', 'Để xử lý sau'),
]

UNREADY_KINDS = {'code', 'merged', 'multi', 'invalid', 'reversed'}


def cell_norm_signature(cell):
    """Normalized comparison key for a non-empty snapshot cell; raw text stays separate for display."""
    if not cell or cell.get('kind') in (None, '', 'empty'):
        return None
    kind = cell.get('kind')
    if kind in ('pair', 'missing_in', 'missing_out', 'reversed'):
        return (kind, cell.get('norm_in') or '', cell.get('norm_out') or '')
    return (kind, (cell.get('raw_in') or '').strip().upper(), (cell.get('raw_out') or '').strip().upper())


def _cell_matches_canonical(cell, canonical):
    if not canonical or not canonical.get('exists'):
        return True
    c_kind = canonical.get('kind')
    kind = cell.get('kind')
    if c_kind == 'pair' and kind == 'pair':
        return (cell.get('norm_in') or '') == (canonical.get('norm_in') or '') and (cell.get('norm_out') or '') == (canonical.get('norm_out') or '')
    if c_kind == 'pair' and kind == 'missing_out':
        return (cell.get('norm_in') or '') == (canonical.get('norm_in') or '')
    if c_kind == 'pair' and kind == 'missing_in':
        return (cell.get('norm_out') or '') == (canonical.get('norm_out') or '')
    if c_kind in ('missing_in', 'missing_out') and kind == c_kind:
        return (cell.get('norm_in') or '') == (canonical.get('norm_in') or '') and (cell.get('norm_out') or '') == (canonical.get('norm_out') or '')
    return False


def classify_day_comparison(mapping_state, a_scope, a_cell, b_scope, b_cell, canonical):
    """Pure decision function for one employee + day cell across A, B and canonical data.

    Returns ``(group, reason)`` where ``group`` is one of ``same``, ``only_a``, ``only_b``,
    ``diff``, ``unready``, or ``blank``.
    """
    a_has = a_scope == 'in_period' and bool(a_cell) and a_cell.get('kind') != 'empty'
    b_has = b_scope == 'in_period' and bool(b_cell) and b_cell.get('kind') != 'empty'

    if not a_has and not b_has:
        return 'blank', ''

    if mapping_state != 'mapped':
        if mapping_state == 'name_conflict':
            return 'unready', 'Mã máy khớp nhưng họ tên khác hồ sơ HR; chưa đủ căn cứ áp dụng.'
        return 'unready', 'Chưa đối chiếu được hồ sơ HR; không tự ghép theo họ tên.'

    if a_has and b_has:
        sig_a = cell_norm_signature(a_cell)
        sig_b = cell_norm_signature(b_cell)
        if sig_a == sig_b:
            if a_cell.get('kind') in UNREADY_KINDS:
                return 'unready', 'Hai file có cùng ký hiệu/dữ liệu lỗi; cần HR kiểm tra trực tiếp.'
            if canonical.get('exists') and not _cell_matches_canonical(a_cell, canonical):
                return 'diff', 'File A và B giống nhau nhưng khác dữ liệu đang áp dụng trên hệ thống.'
            return 'same', 'File A và B có cùng giờ chuẩn hóa.'
        return 'diff', 'File A và B khác giờ hoặc loại dữ liệu (không tự nối Vào/Ra từ hai file).'

    if a_has:
        if a_cell.get('kind') in UNREADY_KINDS:
            return 'unready', 'Chỉ có ở A nhưng chứa ký hiệu hoặc giờ lỗi cần kiểm tra.'
        if canonical.get('exists') and not _cell_matches_canonical(a_cell, canonical):
            return 'diff', 'Dữ liệu file A khác dữ liệu đang áp dụng trên hệ thống.'
        if b_scope == 'out_of_scope':
            return 'only_a', 'Ngày ngoài phạm vi file B; giữ nguyên dữ liệu A.'
        if b_scope == 'blank_in_period':
            return 'only_a', 'Ô trống trong kỳ ở B (thiếu ô ở B không tự xóa giờ hợp lệ của A).'
        if b_scope == 'not_in_file':
            return 'only_a', 'Nhân viên không có trong file B (không coi là nghỉ).'
        return 'only_a', 'Chỉ có ở file A.'

    # b_has and not a_has
    if b_cell.get('kind') in UNREADY_KINDS:
        return 'unready', 'Chỉ có ở B nhưng chứa ký hiệu hoặc giờ lỗi cần kiểm tra.'
    if canonical.get('exists') and not _cell_matches_canonical(b_cell, canonical):
        return 'diff', 'Dữ liệu file B khác dữ liệu đang áp dụng trên hệ thống.'
    if a_scope == 'out_of_scope':
        return 'only_b', 'Ngày ngoài phạm vi file A.'
    if a_scope == 'blank_in_period':
        return 'only_b', 'Ô trống trong kỳ ở A.'
    return 'only_b', 'Nhân viên không có trong file A.'


def classify_late_comparison(mapping_state, a_late, b_late, canonical_late):
    """Pure decision function for one employee + exact source period late total (Lần / Phút)."""
    a_ok = bool(a_late) and a_late.get('source_state') == 'ok'
    b_ok = bool(b_late) and b_late.get('source_state') == 'ok'
    a_bad = bool(a_late) and a_late.get('source_state') in ('invalid', 'inconsistent')
    b_bad = bool(b_late) and b_late.get('source_state') in ('invalid', 'inconsistent')

    if not a_ok and not b_ok and not a_bad and not b_bad:
        return 'blank', ''
    if mapping_state != 'mapped':
        return 'unready', 'Chưa đối chiếu hồ sơ HR cho tổng đi muộn.'
    if a_bad or b_bad:
        return 'unready', 'Số Đi muộn trong file không hợp lệ hoặc bất nhất (một bên bằng 0).'

    def _matches_can(side):
        if not canonical_late or not canonical_late.get('exists'):
            return True
        return (side.get('count'), side.get('minutes')) == (canonical_late.get('count'), canonical_late.get('minutes'))

    if a_ok and b_ok:
        if (a_late['count'], a_late['minutes']) == (b_late['count'], b_late['minutes']):
            if not _matches_can(a_late):
                return 'diff', 'A và B giống nhau nhưng khác tổng Đi muộn đang áp dụng.'
            return 'same', 'Hai file có cùng tổng Đi muộn cho đúng kỳ nguồn.'
        return 'diff', 'Hai file có tổng Đi muộn khác nhau cho cùng kỳ nguồn; cần chọn nguồn.'
    if a_ok:
        if not _matches_can(a_late):
            return 'diff', 'Tổng Đi muộn ở A khác tổng đang áp dụng.'
        return 'only_a', 'Tổng Đi muộn chỉ có ở A.'
    if not _matches_can(b_late):
        return 'diff', 'Tổng Đi muộn ở B khác tổng đang áp dụng.'
    return 'only_b', 'Tổng Đi muộn chỉ có ở B.'


def _canonical_day_digest(company_id, employee_id, work_date, canonical):
    payload = {
        'c': company_id, 'e': employee_id, 'd': work_date.isoformat(),
        'sessions': canonical.get('session_sig') or [],
        'issues': canonical.get('issue_sig') or [],
        'locked': bool(canonical.get('locked')),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]


def _canonical_late_digest(company_id, employee_id, d_from, d_to, canonical_late):
    payload = {
        'c': company_id, 'e': employee_id, 'f': d_from.isoformat(), 't': d_to.isoformat(),
        'late': canonical_late.get('sig') if canonical_late else None,
        'locked': bool(canonical_late.get('locked')) if canonical_late else False,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]


class AttendanceResolution(models.Model):
    _name = 'tp.hr.attendance.resolution'
    _description = 'Lịch sử chọn nguồn đối chiếu chấm công'
    _order = 'id desc'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Công ty', required=True, index=True, readonly=True)
    batch_a_id = fields.Many2one('tp.hr.attendance.batch', 'Lô nguồn A', required=True, index=True, ondelete='restrict', readonly=True)
    batch_b_id = fields.Many2one('tp.hr.attendance.batch', 'Lô nguồn B', index=True, ondelete='restrict', readonly=True)
    sheet_a_index = fields.Integer('Trang A', default=0, readonly=True)
    sheet_b_index = fields.Integer('Trang B', default=0, readonly=True)
    target_kind = fields.Selection([('day', 'Ô ngày Vào/Ra'), ('late', 'Tổng đi muộn cả kỳ')], 'Phạm vi', required=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Nhân viên', required=True, index=True, readonly=True)
    work_date = fields.Date('Ngày công', index=True, readonly=True)
    late_date_from = fields.Date('Kỳ muộn từ', readonly=True)
    late_date_to = fields.Date('Kỳ muộn đến', readonly=True)
    decision = fields.Selection(DECISIONS, 'Quyết định', required=True, index=True, readonly=True)
    reason = fields.Text('Lý do / căn cứ', readonly=True)
    actor_id = fields.Many2one('res.users', 'Người quyết định', required=True, readonly=True)
    decided_at = fields.Datetime('Thời điểm', required=True, readonly=True)
    before_snapshot = fields.Json('Dữ liệu trước', readonly=True)
    after_snapshot = fields.Json('Dữ liệu sau', readonly=True)
    target_version = fields.Integer('Phiên bản sau xử lý', default=1, readonly=True)
    is_latest = fields.Boolean('Quyết định mới nhất cho khóa này', default=True, index=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        deny_direct(self)
        return super().create(vals_list)

    def write(self, vals):
        if not set(vals) <= {'is_latest'}:
            raise AccessError(self.env._('Nhật ký chọn nguồn đối chiếu không được chỉnh sửa.'))
        deny_direct(self)
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('Nhật ký chọn nguồn đối chiếu không được xóa.'))


class AttendanceBatchCompare(models.Model):
    _inherit = 'tp.hr.attendance.batch'

    # --------------------------------------------------- compare engine
    def _tp_build_compare_context(self, batch_a, sheet_a_index, batch_b, sheet_b_index):
        """Evaluate A, B and live canonical state in one deterministic structure."""
        company = batch_a.company_id
        if batch_a.sudo().snapshot_state == 'pending':
            batch_a._tp_build_snapshot()
        eval_a = batch_a._tp_evaluate_sheet_matrix(sheet_index=sheet_a_index)

        eval_b = None
        if batch_b:
            if batch_b.company_id != company:
                raise AccessError(self.env._('Hai tệp đối chiếu phải thuộc cùng công ty.'))
            if batch_b.sudo().snapshot_state == 'pending':
                batch_b._tp_build_snapshot()
            eval_b = batch_b._tp_evaluate_sheet_matrix(sheet_index=sheet_b_index)

        a_from = _parse_iso_date(eval_a['from']) if eval_a['from'] else None
        a_to = _parse_iso_date(eval_a['to']) if eval_a['to'] else None
        b_from = _parse_iso_date(eval_b['from']) if eval_b and eval_b['from'] else None
        b_to = _parse_iso_date(eval_b['to']) if eval_b and eval_b['to'] else None

        # Union of dates covered by A and B
        date_meta = {}
        for col in eval_a['day_columns']:
            d_obj = fields.Date.from_string(col['date'])
            date_meta[col['date']] = {'date': col['date'], 'day_month': col['day_month'], 'weekday': col['weekday'], 'weekend': d_obj.weekday() >= 5}
        if eval_b:
            for col in eval_b['day_columns']:
                d_obj = fields.Date.from_string(col['date'])
                date_meta.setdefault(col['date'], {'date': col['date'], 'day_month': col['day_month'], 'weekday': col['weekday'], 'weekend': d_obj.weekday() >= 5})
        union_dates = [date_meta[k] for k in sorted(date_meta)]
        a_date_set = {col['date'] for col in eval_a['day_columns']}
        b_date_set = {col['date'] for col in eval_b['day_columns']} if eval_b else set()

        # Key people safely: mapped -> ('emp', employee_id); unmapped -> never merge by name!
        # Only align unmapped machine codes if both batches explicitly belong to the same non-generic confirmed namespace.
        confirmed_ns = (
            batch_b is not None
            and batch_a.source_namespace
            and batch_a.source_namespace != 'excel-machine'
            and batch_a.source_namespace == batch_b.source_namespace
        )

        people_entries = {}
        entry_order = []

        def _person_key(side_tag, p):
            if p['mapping_state'] == 'mapped' and p['employee_id']:
                return ('emp', p['employee_id'])
            if confirmed_ns and p['machine_code']:
                return ('ns_code', batch_a.source_namespace, p['machine_code'])
            return ('raw', side_tag, p['snapshot_person_id'])

        for p in eval_a['people']:
            k = _person_key('a', p)
            if k not in people_entries:
                people_entries[k] = {'key': k, 'a': None, 'b': None}
                entry_order.append(k)
            if people_entries[k]['a'] is None:
                people_entries[k]['a'] = p

        if eval_b:
            for p in eval_b['people']:
                k = _person_key('b', p)
                if k not in people_entries:
                    people_entries[k] = {'key': k, 'a': None, 'b': None}
                    entry_order.append(k)
                if people_entries[k]['b'] is None:
                    people_entries[k]['b'] = p

        mapped_emp_ids = [k[1] for k in entry_order if k[0] == 'emp']
        date_objs = [fields.Date.from_string(d['date']) for d in union_dates]

        # Prefetch canonical active sessions, corrections, days, locks, late totals, and latest resolutions
        Period = self.env['tp.hr.attendance.period']
        locked_ranges = Period._tp_locked_ranges([company.id])
        sessions_map = defaultdict(list)
        open_issues_map = defaultdict(list)
        day_map = {}
        approved_corr_days = set()
        late_canonical_map = {}
        latest_res_day = {}
        latest_res_late = {}

        if mapped_emp_ids and date_objs:
            min_d, max_d = min(date_objs), max(date_objs)
            for sess in self.env['tp.hr.attendance.session'].sudo().search([
                ('company_id', '=', company.id),
                ('employee_id', 'in', mapped_emp_ids),
                ('work_date', '>=', min_d),
                ('work_date', '<=', max_d),
                ('active', '=', True),
            ], order='check_in'):
                sessions_map[sess.employee_id.id, sess.work_date].append(sess)
                if sess.source == 'correction':
                    approved_corr_days.add((sess.employee_id.id, sess.work_date))
            for day_rec in self.env['tp.hr.attendance.day'].sudo().search([
                ('company_id', '=', company.id),
                ('employee_id', 'in', mapped_emp_ids),
                ('work_date', '>=', min_d),
                ('work_date', '<=', max_d),
            ]):
                day_map[day_rec.employee_id.id, day_rec.work_date] = day_rec
            for iss in self.env['tp.hr.attendance.line'].sudo().search([
                ('company_id', '=', company.id),
                ('employee_id', 'in', mapped_emp_ids),
                ('work_date', '>=', min_d),
                ('work_date', '<=', max_d),
                ('issue_open', '=', True),
            ]):
                open_issues_map[iss.employee_id.id, iss.work_date].append(iss)
            for corr in self.env['tp.hr.attendance.correction'].sudo().search([
                ('company_id', '=', company.id),
                ('employee_id', 'in', mapped_emp_ids),
                ('work_date', '>=', min_d),
                ('work_date', '<=', max_d),
                ('state', '=', 'approved'),
            ]):
                approved_corr_days.add((corr.employee_id.id, corr.work_date))

        if mapped_emp_ids:
            period_pairs = set()
            if a_from and a_to:
                period_pairs.add((a_from, a_to))
            if b_from and b_to:
                period_pairs.add((b_from, b_to))
            if period_pairs:
                for lr in self.env['tp.hr.attendance.late'].sudo().search([
                    ('company_id', '=', company.id),
                    ('employee_id', 'in', mapped_emp_ids),
                    ('state', '=', 'applied'),
                ]):
                    if (lr.date_from, lr.date_to) in period_pairs:
                        late_canonical_map[lr.employee_id.id, lr.date_from, lr.date_to] = lr

            for res in self.env['tp.hr.attendance.resolution'].sudo().search([
                ('company_id', '=', company.id),
                ('employee_id', 'in', mapped_emp_ids),
                ('is_latest', '=', True),
            ]):
                if res.target_kind == 'day' and res.work_date:
                    latest_res_day[res.employee_id.id, res.work_date] = {
                        'id': res.id, 'decision': res.decision,
                        'decision_label': dict(DECISIONS).get(res.decision, res.decision),
                        'reason': res.reason or '', 'actor': res.actor_id.name or '',
                        'decided_at': self._tp_stamp(res.decided_at),
                    }
                elif res.target_kind == 'late' and res.late_date_from and res.late_date_to:
                    latest_res_late[res.employee_id.id, res.late_date_from, res.late_date_to] = {
                        'id': res.id, 'decision': res.decision,
                        'decision_label': dict(DECISIONS).get(res.decision, res.decision),
                        'reason': res.reason or '', 'actor': res.actor_id.name or '',
                        'decided_at': self._tp_stamp(res.decided_at),
                    }

        def _canonical_day_info(emp_id, w_date):
            is_locked = Period._tp_is_locked(company.id, w_date, locked_ranges)
            has_corr = (emp_id, w_date) in approved_corr_days
            active_sess = sessions_map.get((emp_id, w_date), [])
            open_iss = open_issues_map.get((emp_id, w_date), [])
            day_rec = day_map.get((emp_id, w_date))

            sess_sig = [(s.id, s.check_in.isoformat(), s.check_out.isoformat(), s.source) for s in active_sess]
            iss_sig = [(i.id, i.kind, i.raw_in or '', i.raw_out or '') for i in open_iss]

            if active_sess:
                first_in = utc_to_local(active_sess[0].check_in).strftime('%H:%M')
                last_out = utc_to_local(active_sess[-1].check_out).strftime('%H:%M')
                prov_codes = []
                for s in active_sess:
                    for sb in s.source_batch_ids:
                        prov_codes.append(sb.batch_code or f'LÔ-{sb.id:05d}')
                if not prov_codes and active_sess[0].batch_id:
                    prov_codes.append(active_sess[0].batch_id.batch_code or f'LÔ-{active_sess[0].batch_id.id:05d}')
                info = {
                    'exists': True, 'kind': 'pair', 'norm_in': first_in, 'norm_out': last_out,
                    'source': active_sess[0].source,
                    'source_label': 'Điều chỉnh duyệt' if active_sess[0].source == 'correction' else 'Đã nhập Excel',
                    'provenance': list(dict.fromkeys(prov_codes)),
                    'locked': is_locked, 'has_approved_correction': has_corr,
                    'version': day_rec.version if day_rec else 0,
                    'session_sig': sess_sig, 'issue_sig': iss_sig,
                }
            elif open_iss:
                first_i = open_iss[0]
                info = {
                    'exists': True, 'kind': first_i.kind,
                    'norm_in': utc_to_local(first_i.check_in).strftime('%H:%M') if first_i.check_in else (first_i.raw_in or ''),
                    'norm_out': utc_to_local(first_i.check_out).strftime('%H:%M') if first_i.check_out else (first_i.raw_out or ''),
                    'source': 'import', 'source_label': 'Chờ xử lý từ nhập trước',
                    'provenance': [first_i.batch_id.batch_code or f'LÔ-{first_i.batch_id.id:05d}'],
                    'locked': is_locked, 'has_approved_correction': has_corr,
                    'version': day_rec.version if day_rec else 0,
                    'session_sig': sess_sig, 'issue_sig': iss_sig,
                }
            else:
                info = {
                    'exists': False, 'kind': 'none', 'norm_in': '', 'norm_out': '',
                    'source': '', 'source_label': 'Chưa có dữ liệu', 'provenance': [],
                    'locked': is_locked, 'has_approved_correction': has_corr,
                    'version': day_rec.version if day_rec else 0,
                    'session_sig': sess_sig, 'issue_sig': iss_sig,
                }
            info['digest'] = _canonical_day_digest(company.id, emp_id, w_date, info) if emp_id else ''
            return info

        def _canonical_late_info(emp_id, p_from, p_to):
            rec = late_canonical_map.get((emp_id, p_from, p_to)) if emp_id and p_from and p_to else None
            is_locked = bool(p_from and p_to and any(Period._tp_is_locked(company.id, d, locked_ranges) for d in (p_from, p_to)))
            if rec:
                prov = [b.batch_code or f'LÔ-{b.id:05d}' for b in rec.source_batch_ids] or [rec.batch_id.batch_code or f'LÔ-{rec.batch_id.id:05d}']
                info = {
                    'exists': True, 'id': rec.id, 'count': rec.late_count, 'minutes': rec.late_minutes,
                    'provenance': list(dict.fromkeys(prov)), 'version': rec.version,
                    'locked': is_locked, 'sig': (rec.id, rec.late_count, rec.late_minutes, rec.version),
                }
            else:
                info = {
                    'exists': False, 'id': 0, 'count': None, 'minutes': None,
                    'provenance': [], 'version': 0, 'locked': is_locked, 'sig': None,
                }
            info['digest'] = _canonical_late_digest(company.id, emp_id, p_from, p_to, info) if (emp_id and p_from and p_to) else ''
            return info

        same_period = bool(eval_b and a_from and a_to and b_from and b_to and (a_from, a_to) == (b_from, b_to))
        people_rows = []
        group_options = {}

        for k in entry_order:
            pair = people_entries[k]
            pa, pb = pair['a'], pair['b']
            ref_p = pa or pb
            emp_id = ref_p['employee_id'] if ref_p['mapping_state'] == 'mapped' else 0
            mapping_state = ref_p['mapping_state']
            mapping_label = ref_p['mapping_label']

            a_cells = {c['date']: c for c in pa['cells']} if pa else {}
            b_cells = {c['date']: c for c in pb['cells']} if pb else {}

            # Group filter option uses A's source group (or B's if not in A)
            grp_label = (pa and pa['group_label']) or (pb and pb['group_label']) or 'Chưa phân nhóm'
            grp_key = (pa and pa['group_key']) or (pb and pb['group_key']) or EMPTY_GROUP_KEY
            if grp_key not in group_options:
                group_options[grp_key] = {'key': grp_key, 'label': grp_label, 'count': 0}
            group_options[grp_key]['count'] += 1

            day_items = []
            person_groups = set()
            for d_meta in union_dates:
                d_iso = d_meta['date']
                w_date = fields.Date.from_string(d_iso)

                if not pa:
                    a_scope = 'out_of_scope' if d_iso not in a_date_set else 'not_in_file'
                    a_cell = None
                elif d_iso not in a_date_set:
                    a_scope = 'out_of_scope'
                    a_cell = None
                else:
                    a_cell = a_cells.get(d_iso)
                    a_scope = 'blank_in_period' if (not a_cell or a_cell['kind'] == 'empty') else 'in_period'

                if not eval_b:
                    b_scope = 'no_batch_b'
                    b_cell = None
                elif not pb:
                    b_scope = 'out_of_scope' if d_iso not in b_date_set else 'not_in_file'
                    b_cell = None
                elif d_iso not in b_date_set:
                    b_scope = 'out_of_scope'
                    b_cell = None
                else:
                    b_cell = b_cells.get(d_iso)
                    b_scope = 'blank_in_period' if (not b_cell or b_cell['kind'] == 'empty') else 'in_period'

                canonical = _canonical_day_info(emp_id, w_date) if emp_id else {
                    'exists': False, 'kind': 'none', 'norm_in': '', 'norm_out': '',
                    'source': '', 'source_label': '', 'provenance': [], 'locked': False,
                    'has_approved_correction': False, 'version': 0, 'digest': '',
                }
                a_eval_scope = 'in_period' if a_scope == 'in_period' else a_scope
                b_eval_scope = 'in_period' if b_scope == 'in_period' else b_scope
                grp, reason = classify_day_comparison(mapping_state, a_eval_scope, a_cell, b_eval_scope, b_cell, canonical)
                if grp != 'blank':
                    person_groups.add(grp)

                blocked_reason = ''
                if mapping_state != 'mapped':
                    blocked_reason = 'Chưa đối chiếu hồ sơ HR.'
                elif canonical['locked']:
                    blocked_reason = 'Kỳ công đã chốt; không ghi đè trực tiếp.'
                elif canonical['has_approved_correction']:
                    blocked_reason = 'Ngày đã có điều chỉnh được duyệt; không ghi đè trực tiếp.'

                can_use_a = bool(
                    not blocked_reason and a_cell and a_cell.get('kind') in ('pair', 'missing_in', 'missing_out'),
                )
                can_use_b = bool(
                    not blocked_reason and b_cell and b_cell.get('kind') in ('pair', 'missing_in', 'missing_out'),
                )
                latest_res = latest_res_day.get((emp_id, w_date)) if emp_id else None

                day_items.append({
                    'date': d_iso,
                    'day_month': d_meta['day_month'],
                    'weekday': d_meta['weekday'],
                    'weekend': d_meta['weekend'],
                    'a_scope': a_scope,
                    'a_scope_label': SCOPE_LABELS.get(a_scope, a_scope),
                    'a_cell': a_cell,
                    'b_scope': b_scope,
                    'b_scope_label': SCOPE_LABELS.get(b_scope, b_scope),
                    'b_cell': b_cell,
                    'canonical': canonical,
                    'group': grp,
                    'group_label': COMPARE_GROUP_LABELS.get(grp, 'Ô trống hai bên'),
                    'reason': reason,
                    'blocked_reason': blocked_reason,
                    'can_choose': bool(not blocked_reason and grp in ('diff', 'only_a', 'only_b', 'same')),
                    'can_use_a': can_use_a,
                    'can_use_b': can_use_b,
                    'latest_resolution': latest_res,
                    'target_digest': canonical['digest'],
                })

            # Late total comparison (per exact period, never cross-period sum/split)
            late_items = []
            if same_period and a_from and a_to:
                a_late = pa['late'] if pa else None
                b_late = pb['late'] if pb else None
                can_late = _canonical_late_info(emp_id, a_from, a_to)
                l_grp, l_reason = classify_late_comparison(mapping_state, a_late, b_late, can_late)
                if l_grp != 'blank':
                    person_groups.add(l_grp)
                l_blocked = ''
                if mapping_state != 'mapped':
                    l_blocked = 'Chưa đối chiếu hồ sơ HR.'
                elif can_late['locked']:
                    l_blocked = 'Kỳ công đã chốt; tổng đi muộn không ghi đè.'
                if l_grp != 'blank':
                    late_items.append({
                        'side_mode': 'same_period',
                        'date_from': a_from.isoformat(),
                        'date_to': a_to.isoformat(),
                        'period_label': short_range(a_from, a_to),
                        'a_late': a_late,
                        'b_late': b_late,
                        'canonical_late': can_late,
                        'group': l_grp,
                        'group_label': COMPARE_GROUP_LABELS.get(l_grp, l_grp),
                        'reason': l_reason,
                        'blocked_reason': l_blocked,
                        'can_choose': bool(not l_blocked and l_grp in ('diff', 'only_a', 'only_b', 'same')),
                        'can_use_a': bool(not l_blocked and a_late and a_late.get('source_state') == 'ok'),
                        'can_use_b': bool(not l_blocked and b_late and b_late.get('source_state') == 'ok'),
                        'latest_resolution': latest_res_late.get((emp_id, a_from, a_to)) if emp_id else None,
                        'target_digest': can_late['digest'],
                    })
            else:
                if pa and a_from and a_to and pa['late'].get('source_state') in ('ok', 'invalid', 'inconsistent'):
                    can_la = _canonical_late_info(emp_id, a_from, a_to)
                    lg_a, lr_a = classify_late_comparison(mapping_state, pa['late'], None, can_la)
                    if eval_b and b_from and b_to:
                        lr_a = f"{lr_a} (Kỳ file A khác file B — so riêng từng kỳ, không cộng chồng hoặc tách lẻ.)"
                    if lg_a != 'blank':
                        person_groups.add(lg_a)
                        l_blocked = 'Chưa đối chiếu hồ sơ HR.' if mapping_state != 'mapped' else ('Kỳ công đã chốt.' if can_la['locked'] else '')
                        late_items.append({
                            'side_mode': 'period_a',
                            'date_from': a_from.isoformat(),
                            'date_to': a_to.isoformat(),
                            'period_label': short_range(a_from, a_to),
                            'a_late': pa['late'],
                            'b_late': None,
                            'canonical_late': can_la,
                            'group': lg_a,
                            'group_label': COMPARE_GROUP_LABELS.get(lg_a, lg_a),
                            'reason': lr_a,
                            'blocked_reason': l_blocked,
                            'can_choose': bool(not l_blocked and lg_a in ('diff', 'only_a', 'same')),
                            'can_use_a': bool(not l_blocked and pa['late'].get('source_state') == 'ok'),
                            'can_use_b': False,
                            'latest_resolution': latest_res_late.get((emp_id, a_from, a_to)) if emp_id else None,
                            'target_digest': can_la['digest'],
                        })
                if eval_b and pb and b_from and b_to and pb['late'].get('source_state') in ('ok', 'invalid', 'inconsistent'):
                    can_lb = _canonical_late_info(emp_id, b_from, b_to)
                    lg_b, lr_b = classify_late_comparison(mapping_state, None, pb['late'], can_lb)
                    if a_from and a_to:
                        lr_b = f"{lr_b} (Kỳ file B khác file A — so riêng từng kỳ, không cộng chồng hoặc tách lẻ.)"
                    if lg_b != 'blank':
                        person_groups.add(lg_b)
                        l_blocked = 'Chưa đối chiếu hồ sơ HR.' if mapping_state != 'mapped' else ('Kỳ công đã chốt.' if can_lb['locked'] else '')
                        late_items.append({
                            'side_mode': 'period_b',
                            'date_from': b_from.isoformat(),
                            'date_to': b_to.isoformat(),
                            'period_label': short_range(b_from, b_to),
                            'a_late': None,
                            'b_late': pb['late'],
                            'canonical_late': can_lb,
                            'group': lg_b,
                            'group_label': COMPARE_GROUP_LABELS.get(lg_b, lg_b),
                            'reason': lr_b,
                            'blocked_reason': l_blocked,
                            'can_choose': bool(not l_blocked and lg_b in ('diff', 'only_b', 'same')),
                            'can_use_a': False,
                            'can_use_b': bool(not l_blocked and pb['late'].get('source_state') == 'ok'),
                            'latest_resolution': latest_res_late.get((emp_id, b_from, b_to)) if emp_id else None,
                            'target_digest': can_lb['digest'],
                        })

            people_rows.append({
                'row_key': '|'.join(map(str, k)),
                'employee_id': emp_id,
                'hr_code': ref_p['hr_code'],
                'hr_name': ref_p['hr_name'],
                'hr_department': ref_p['hr_department'],
                'display_name': ref_p['hr_name'] or ref_p['source_name'],
                'source_name_a': pa['source_name'] if pa else '',
                'source_name_b': pb['source_name'] if pb else '',
                'raw_code_a': pa['raw_source_code'] if pa else '',
                'raw_code_b': pb['raw_source_code'] if pb else '',
                'machine_code': ref_p['machine_code'] or ref_p['raw_machine_code'],
                'group_key': grp_key,
                'group_label': grp_label,
                'mapping_state': mapping_state,
                'mapping_label': mapping_label,
                'in_a': bool(pa),
                'in_b': bool(pb),
                'days': day_items,
                'late_items': late_items,
                'groups': sorted(person_groups),
            })

        return {
            'eval_a': eval_a,
            'eval_b': eval_b,
            'same_period': same_period,
            'union_dates': union_dates,
            'people_rows': people_rows,
            'group_options': list(group_options.values()),
        }

    @api.model
    def tp_compare_batches(self, params=None):
        """Return A/B file comparison payload with server-side filters and employee pagination."""
        params = dict(params or {})
        company = self.env.company
        require(self.env, 'import', company)
        self.check_access('read')

        batches = self.search([('company_id', '=', company.id), ('state', 'not in', ('draft', 'cancelled'))], order='id desc', limit=200)
        batch_a_id = int(params.get('batch_a_id') or 0)
        batch_b_id = int(params.get('batch_b_id') or 0)
        sheet_a_index = int(params.get('sheet_a_index') or 0)
        sheet_b_index = int(params.get('sheet_b_index') or 0)

        batch_a = self._tp_accessible_batch(batch_a_id) if batch_a_id else (batches[:1])
        batch_b = self._tp_accessible_batch(batch_b_id) if batch_b_id else self.browse()
        if not batch_a:
            return {'has_batches': False, 'batches': [], 'rows': [], 'total': 0, 'page': 1, 'page_size': 20, 'page_count': 1}

        ctx = self._tp_build_compare_context(batch_a, sheet_a_index, batch_b, sheet_b_index)

        # Filters: only_diff, group, source_group, search, work_date
        only_diff = bool(params.get('only_diff'))
        group_filter = str(params.get('group') or '').strip()
        if group_filter and group_filter not in COMPARE_GROUP_LABELS:
            group_filter = ''
        source_group = str(params.get('source_group') or '').strip()
        search_fold = fold(params.get('search') or '')
        filter_date = _parse_iso_date(params.get('work_date'))
        filter_date_iso = filter_date.isoformat() if filter_date else ''

        # Count cells across full scope before pagination (strictly inside company & role ACL)
        cell_counts = {k: 0 for k, _lbl in COMPARE_GROUPS}
        late_counts = {k: 0 for k, _lbl in COMPARE_GROUPS}
        for p in ctx['people_rows']:
            for d in p['days']:
                if filter_date_iso and d['date'] != filter_date_iso:
                    continue
                if d['group'] in cell_counts:
                    cell_counts[d['group']] += 1
            for li in p['late_items']:
                if li['group'] in late_counts:
                    late_counts[li['group']] += 1

        # Determine which days & lates match the active filters; keep table columns 1-to-1 aligned
        matched_rows = []
        active_date_isos = set()
        for p in ctx['people_rows']:
            if source_group and p['group_key'] != source_group:
                continue
            if search_fold:
                hay = ' '.join([
                    fold(p['display_name']), fold(p['source_name_a']), fold(p['source_name_b']),
                    fold(p['raw_code_a']), fold(p['raw_code_b']), fold(p['hr_code']), fold(p['machine_code']),
                ])
                if search_fold not in hay:
                    continue

            day_matches = []
            for d in p['days']:
                if filter_date_iso and d['date'] != filter_date_iso:
                    continue
                is_match = (
                    (not only_diff or d['group'] in ('diff', 'only_a', 'only_b', 'unready'))
                    and (not group_filter or d['group'] == group_filter)
                )
                if is_match:
                    day_matches.append(d['date'])
            visible_lates = [
                li for li in p['late_items']
                if (not only_diff or li['group'] in ('diff', 'only_a', 'only_b', 'unready'))
                and (not group_filter or li['group'] == group_filter)
            ]
            if (only_diff or group_filter or filter_date_iso) and not day_matches and not visible_lates:
                continue
            if only_diff or group_filter:
                active_date_isos.update(day_matches)
            matched_rows.append((p, set(day_matches), visible_lates))

        visible_dates = [d for d in ctx['union_dates'] if not filter_date_iso or d['date'] == filter_date_iso]
        if (only_diff or group_filter) and active_date_isos:
            visible_dates = [d for d in visible_dates if d['date'] in active_date_isos]

        filtered = []
        for p, match_set, visible_lates in matched_rows:
            by_d = {d['date']: d for d in p['days']}
            aligned_days = []
            for vcol in visible_dates:
                d_item = by_d.get(vcol['date'])
                if d_item:
                    aligned_days.append(dict(d_item, matches_filter=vcol['date'] in match_set))
            filtered.append(dict(p, days=aligned_days, late_items=visible_lates))

        size = int(params.get('page_size') or 20)
        size = size if size in MATRIX_PAGE_SIZES else 20
        total = len(filtered)
        page_count = max(1, -(-total // size))
        page = min(max(1, int(params.get('page') or 1)), page_count)
        page_rows = filtered[(page - 1) * size: page * size]

        selector_batches = [b._tp_batch_selector_item() for b in batches]
        return {
            'has_batches': True,
            'batches': selector_batches,
            'batch_a': batch_a._tp_batch_selector_item(),
            'batch_b': batch_b._tp_batch_selector_item() if batch_b else None,
            'sheet_a': {'index': ctx['eval_a']['sheet_index'], 'name': ctx['eval_a']['sheet_name'],
                        'period_label': ctx['eval_a']['period_label'], 'period_full': ctx['eval_a']['period_full']},
            'sheet_b': {'index': ctx['eval_b']['sheet_index'], 'name': ctx['eval_b']['sheet_name'],
                        'period_label': ctx['eval_b']['period_label'], 'period_full': ctx['eval_b']['period_full']} if ctx['eval_b'] else None,
            'same_period': ctx['same_period'],
            'union_dates': ctx['union_dates'],
            'visible_dates': visible_dates,
            'group_options': ctx['group_options'],
            'compare_groups': [{'key': k, 'label': lbl, 'cells': cell_counts[k], 'lates': late_counts[k]} for k, lbl in COMPARE_GROUPS],
            'cell_counts': cell_counts,
            'late_counts': late_counts,
            'can_apply_valid': bool(cell_counts['same'] + cell_counts['only_a'] + cell_counts['only_b'] + late_counts['same'] + late_counts['only_a'] + late_counts['only_b']),
            'rows': page_rows,
            'total': total,
            'total_all_people': len(ctx['people_rows']),
            'page': page,
            'page_size': size,
            'page_count': page_count,
        }

    # --------------------------------------------------- transactional apply & resolve
    def _tp_ensure_line_for_cell(self, batch, sheet_index, person_data, cell_data):
        """Return existing ``tp.hr.attendance.line`` or create one inside internal write if needed."""
        Line = self.env['tp.hr.attendance.line'].sudo()
        line = Line.search([
            ('batch_id', '=', batch.id),
            ('sheet_index', '=', sheet_index),
            ('row_number', '=', person_data['in_row']),
            ('column_index', '=', cell_data['column']),
        ], limit=1)
        if line:
            return line
        w_date = fields.Date.from_string(cell_data['date'])
        tz = batch.tz or DEFAULT_TZ
        c_in = local_to_utc(w_date, dt_time.fromisoformat(cell_data['norm_in']), tz) if cell_data.get('norm_in') else False
        c_out = local_to_utc(w_date, dt_time.fromisoformat(cell_data['norm_out']), tz) if cell_data.get('norm_out') else False
        return internal(Line).create({
            'batch_id': batch.id,
            'sheet_name': batch.sheet_summary[sheet_index]['name'] if batch.sheet_summary and sheet_index < len(batch.sheet_summary) else '',
            'sheet_index': sheet_index,
            'row_number': person_data['in_row'],
            'column_index': cell_data['column'],
            'cell_ref': cell_data.get('cell_ref') or '',
            'machine_code': person_data.get('machine_code') or '',
            'raw_source_code': person_data.get('raw_source_code') or '',
            'source_name': person_data.get('source_name') or '',
            'source_title': person_data.get('source_title') or '',
            'source_group': person_data.get('source_group') or '',
            'employee_id': person_data.get('employee_id') or False,
            'work_date': w_date,
            'raw_in': cell_data.get('raw_in') or '',
            'raw_out': cell_data.get('raw_out') or '',
            'check_in': c_in,
            'check_out': c_out,
            'kind': cell_data['kind'],
            'state': 'review',
        })

    def _tp_apply_cell_to_canonical(self, company, batch, sheet_index, person_data, cell_data, provenance_batches, provenance_lines, reason=''):
        """Write or link canonical attendance for one verified (employee, work_date) inside an advisory lock."""
        emp_id = person_data['employee_id']
        w_date = fields.Date.from_string(cell_data['date'])
        tz = batch.tz or DEFAULT_TZ
        c_in = local_to_utc(w_date, dt_time.fromisoformat(cell_data['norm_in']), tz) if cell_data.get('norm_in') else False
        c_out = local_to_utc(w_date, dt_time.fromisoformat(cell_data['norm_out']), tz) if cell_data.get('norm_out') else False

        Session = internal(self.env['tp.hr.attendance.session']).with_context(active_test=False)
        Line = self.env['tp.hr.attendance.line'].sudo()
        chosen_line = self._tp_ensure_line_for_cell(batch, sheet_index, person_data, cell_data)

        batch_cmds = [(4, b.id) for b in provenance_batches if b]
        line_cmds = [(4, line.id) for line in provenance_lines if line]
        if chosen_line:
            line_cmds.append((4, chosen_line.id))

        if cell_data['kind'] == 'pair':
            existing = Session.search([
                ('employee_id', '=', emp_id),
                ('work_date', '=', w_date),
            ], order='check_in')
            same_sess = existing.filtered(lambda s: s.check_in == c_in and s.check_out == c_out)[:1]
            others_active = existing.filtered(lambda s: s.active and s != same_sess)
            if others_active:
                others_active.write({'active': False, 'superseded_reason': reason or self.env._('Thay bằng nguồn đối chiếu %(code)s', code=batch.batch_code or batch.name)})
            if same_sess:
                vals = {'source_batch_ids': batch_cmds, 'source_line_ids': line_cmds}
                if not same_sess.active:
                    vals.update(active=True, superseded_reason=False)
                same_sess.write(vals)
                session = same_sess
            else:
                session = Session.create({
                    'employee_id': emp_id,
                    'company_id': company.id,
                    'work_date': w_date,
                    'check_in': c_in,
                    'check_out': c_out,
                    'source': 'import',
                    'batch_id': batch.id,
                    'line_id': chosen_line.id if chosen_line else False,
                    'source_batch_ids': batch_cmds,
                    'source_line_ids': line_cmds,
                })
            open_issues = Line.search([
                ('employee_id', '=', emp_id),
                ('work_date', '=', w_date),
                ('issue_open', '=', True),
            ])
            if open_issues:
                internal(open_issues).write({
                    'issue_open': False,
                    'resolved_by_line_id': chosen_line.id if chosen_line else False,
                    'resolution': self.env._('Đã chọn nguồn %(code)s.', code=batch.batch_code or batch.name),
                })
            internal(chosen_line).write({
                'state': 'applied',
                'session_id': session.id,
                'issue_open': False,
                'employee_id': emp_id,
            })
        else:
            # missing_in / missing_out: never invent missing punch; deactivate conflicting active pair if replaced
            active_sess = Session.search([
                ('employee_id', '=', emp_id),
                ('work_date', '=', w_date),
                ('active', '=', True),
            ])
            if active_sess:
                active_sess.write({'active': False, 'superseded_reason': reason or self.env._('Thay bằng nguồn đối chiếu %(code)s', code=batch.batch_code or batch.name)})
            other_issues = Line.search([
                ('employee_id', '=', emp_id),
                ('work_date', '=', w_date),
                ('issue_open', '=', True),
                ('id', '!=', chosen_line.id),
            ])
            if other_issues:
                internal(other_issues).write({'issue_open': False, 'resolution': self.env._('Thay bởi nguồn %(code)s.', code=batch.batch_code or batch.name)})
            internal(chosen_line).write({
                'state': 'missing',
                'issue_open': True,
                'employee_id': emp_id,
            })
        return chosen_line

    def _tp_apply_late_to_canonical(self, company, emp_id, d_from, d_to, chosen_batch, sheet_index, person_data, late_data, provenance_batches, reason=''):
        Late = self.env['tp.hr.attendance.late'].sudo()
        chosen_row = Late.search([
            ('batch_id', '=', chosen_batch.id),
            ('sheet_index', '=', sheet_index),
            ('row_number', '=', person_data['in_row']),
            ('date_from', '=', d_from),
            ('date_to', '=', d_to),
        ], limit=1)
        if not chosen_row:
            chosen_row = internal(Late).create({
                'batch_id': chosen_batch.id,
                'sheet_name': chosen_batch.sheet_summary[sheet_index]['name'] if chosen_batch.sheet_summary and sheet_index < len(chosen_batch.sheet_summary) else '',
                'sheet_index': sheet_index,
                'row_number': person_data['in_row'],
                'cell_ref': late_data.get('cell_ref') or '',
                'machine_code': person_data.get('machine_code') or '',
                'raw_source_code': person_data.get('raw_source_code') or '',
                'source_name': person_data.get('source_name') or '',
                'employee_id': emp_id,
                'date_from': d_from,
                'date_to': d_to,
                'late_count': late_data['count'] or 0,
                'late_minutes': late_data['minutes'] or 0,
                'raw_count': late_data.get('raw_count') or '',
                'raw_minutes': late_data.get('raw_minutes') or '',
                'source_state': 'ok',
                'state': 'preview',
            })

        current = Late.search([
            ('company_id', '=', company.id),
            ('employee_id', '=', emp_id),
            ('date_from', '=', d_from),
            ('date_to', '=', d_to),
            ('state', '=', 'applied'),
        ], limit=1)
        batch_cmds = [(4, b.id) for b in provenance_batches if b]
        batch_cmds.append((4, chosen_batch.id))

        if current and (current.late_count, current.late_minutes) == (late_data['count'], late_data['minutes']):
            internal(current).write({'source_batch_ids': batch_cmds})
            if chosen_row != current:
                internal(chosen_row).write({'state': 'duplicate', 'canonical_late_id': current.id, 'employee_id': emp_id})
            return current

        if current:
            # Must move old applied record to 'superseded' before setting chosen_row to 'applied' (unique index guard)
            internal(current).write({
                'state': 'superseded',
                'superseded_by_id': chosen_row.id,
                'superseded_by_user_id': self.env.user.id,
                'superseded_at': fields.Datetime.now(),
                'supersede_reason': reason,
                'version': current.version + 1,
            })
            current.flush_recordset(['state'])

        internal(chosen_row).write({
            'state': 'applied',
            'employee_id': emp_id,
            'source_batch_ids': batch_cmds,
            'version': chosen_row.version + 1,
            'message': self.env._('Áp dụng từ nguồn %(code)s.', code=chosen_batch.batch_code or chosen_batch.name),
        })
        return chosen_row

    def _tp_recount_batch_after_resolution(self, batch):
        """Recompute stored batch line/late counters and promote partial -> applied only when 0 conflicts/defers remain."""
        batch = batch.sudo()
        lines = batch.line_ids
        lates = batch.late_ids
        counts = {s: 0 for s in COUNTED}
        for line in lines:
            if line.state in counts:
                counts[line.state] += 1
        late_counts = {s: 0 for s in LATE_COUNTED}
        for row in lates:
            if row.state in late_counts:
                late_counts[row.state] += 1

        vals = {f'{s}_count': v for s, v in counts.items()}
        vals.update({f'late_{s}_count': v for s, v in late_counts.items()})
        if batch.state in ('applied', 'partial') or batch.applied_at:
            unresolved = batch._tp_unresolved_conflict_count()
            vals['state'] = 'partial' if unresolved else 'applied'
            if not batch.applied_by:
                vals['applied_by'] = self.env.user.id
            if not batch.applied_at:
                vals['applied_at'] = fields.Datetime.now()
        internal(batch).write(vals)

    @api.model
    def tp_apply_compare_valid(self, params=None):
        """Apply all non-conflicting same/only_a/only_b valid pair cells and exact late totals from comparison.

        Runs inside advisory + row lock, re-evaluates fresh DB state, leaves conflicts/unready/locked intact,
        and marks batches ``partial`` whenever unresolved conflicts remain.
        """
        params = dict(params or {})
        batch_a = self._tp_accessible_batch(params.get('batch_a_id'))
        batch_b = self._tp_accessible_batch(params.get('batch_b_id')) if params.get('batch_b_id') else self.browse()
        sheet_a_index = int(params.get('sheet_a_index') or 0)
        sheet_b_index = int(params.get('sheet_b_index') or 0)

        batch_a._lock()
        if batch_b and batch_b != batch_a:
            batch_b._lock()
        ctx = self._tp_build_compare_context(batch_a, sheet_a_index, batch_b, sheet_b_index)
        company = batch_a.company_id
        touched_days = set()
        applied_cells = 0
        applied_lates = 0
        skipped_locked = 0

        pa_by_emp = {p['employee_id']: p for p in ctx['eval_a']['people'] if p['mapping_state'] == 'mapped' and p['employee_id']}
        pb_by_emp = {p['employee_id']: p for p in ctx['eval_b']['people'] if p['mapping_state'] == 'mapped' and p['employee_id']} if ctx['eval_b'] else {}

        for p in ctx['people_rows']:
            if p['mapping_state'] != 'mapped' or not p['employee_id']:
                continue
            emp_id = p['employee_id']
            pa = pa_by_emp.get(emp_id)
            pb = pb_by_emp.get(emp_id)

            for d in p['days']:
                if d['group'] not in ('same', 'only_a', 'only_b'):
                    continue
                if d['blocked_reason']:
                    skipped_locked += 1
                    continue
                if d['group'] == 'same':
                    if d['a_cell']['kind'] != 'pair':
                        continue
                    prov_batches = [batch_a, batch_b] if batch_b else [batch_a]
                    line_a = self._tp_ensure_line_for_cell(batch_a, sheet_a_index, pa, d['a_cell'])
                    prov_lines = [line_a]
                    if batch_b and pb and d.get('b_cell'):
                        line_b = self._tp_ensure_line_for_cell(batch_b, sheet_b_index, pb, d['b_cell'])
                        prov_lines.append(line_b)
                    self._tp_apply_cell_to_canonical(company, batch_a, sheet_a_index, pa, d['a_cell'], prov_batches, prov_lines)
                    touched_days.add((emp_id, fields.Date.from_string(d['date'])))
                    applied_cells += 1
                elif d['group'] == 'only_a' and d['a_cell']['kind'] in ('pair', 'missing_in', 'missing_out'):
                    self._tp_apply_cell_to_canonical(company, batch_a, sheet_a_index, pa, d['a_cell'], [batch_a], [])
                    touched_days.add((emp_id, fields.Date.from_string(d['date'])))
                    applied_cells += 1
                elif d['group'] == 'only_b' and batch_b and pb and d['b_cell']['kind'] in ('pair', 'missing_in', 'missing_out'):
                    self._tp_apply_cell_to_canonical(company, batch_b, sheet_b_index, pb, d['b_cell'], [batch_b], [])
                    touched_days.add((emp_id, fields.Date.from_string(d['date'])))
                    applied_cells += 1

            for li in p['late_items']:
                if li['group'] not in ('same', 'only_a', 'only_b') or li['blocked_reason']:
                    continue
                d_from = fields.Date.from_string(li['date_from'])
                d_to = fields.Date.from_string(li['date_to'])
                if li['group'] == 'same' and pa and pb and batch_b:
                    self._tp_apply_late_to_canonical(company, emp_id, d_from, d_to, batch_a, sheet_a_index, pa, li['a_late'], [batch_a, batch_b])
                    applied_lates += 1
                elif li['group'] in ('same', 'only_a') and pa and li.get('a_late'):
                    self._tp_apply_late_to_canonical(company, emp_id, d_from, d_to, batch_a, sheet_a_index, pa, li['a_late'], [batch_a])
                    applied_lates += 1
                elif li['group'] == 'only_b' and batch_b and pb and li.get('b_late'):
                    self._tp_apply_late_to_canonical(company, emp_id, d_from, d_to, batch_b, sheet_b_index, pb, li['b_late'], [batch_b])
                    applied_lates += 1

        if touched_days:
            self.env['tp.hr.attendance.day']._tp_refresh(company, touched_days)

        unique_batches = [batch_a] + ([batch_b] if batch_b and batch_b != batch_a else [])
        for b in unique_batches:
            # Reclassify any remaining lines/lates against updated canonical state before recounting
            b._tp_classify()
            if b.state == 'preview' and (applied_cells or applied_lates):
                internal(b).write({'applied_by': self.env.user.id, 'applied_at': fields.Datetime.now()})
            self._tp_recount_batch_after_resolution(b)

        self.env['tp.hr.attendance.log']._tp_log(batch_a, 'compare_apply_valid', {
            'batch_b_id': batch_b.id if batch_b else 0,
            'applied_cells': applied_cells,
            'applied_lates': applied_lates,
            'skipped_locked': skipped_locked,
        })
        return {
            'applied_cells': applied_cells,
            'applied_lates': applied_lates,
            'skipped_locked': skipped_locked,
            'compare': self.tp_compare_batches(params),
        }

    def _tp_apply_compare_item_decision(
        self, company, ctx, batch_a, batch_b, sheet_a_index, sheet_b_index,
        pa_by_emp, pb_by_emp, by_emp, target, decision, reason, touched_days, now,
    ):
        """Execute a single day/late resolution choice inside an active batch lock + CAS digest check."""
        if decision not in dict(DECISIONS):
            raise UserError(self.env._('Quyết định xử lý không hợp lệ.'))
        if decision == 'use_b' and not batch_b:
            raise UserError(self.env._('Chưa chọn tệp B để áp dụng bản B.'))

        Res = internal(self.env['tp.hr.attendance.resolution'])
        Line = self.env['tp.hr.attendance.line'].sudo()
        Late = self.env['tp.hr.attendance.late'].sudo()

        t_kind = target.get('target_kind') or 'day'
        emp_id = int(target.get('employee_id') or 0)
        if emp_id not in by_emp:
            raise UserError(self.env._('Nhân viên chưa được đối chiếu hồ sơ HR hoặc không có trong phạm vi tệp.'))
        p_row = by_emp[emp_id]
        expected_digest = target.get('expected_digest') or ''

        if t_kind == 'day':
            w_iso = str(target.get('work_date') or '')
            day_item = next((d for d in p_row['days'] if d['date'] == w_iso), None)
            if not day_item:
                raise UserError(self.env._('Không tìm thấy ô ngày %(day)s trong bảng đối chiếu.', day=w_iso))
            if expected_digest and day_item['target_digest'] != expected_digest:
                raise UserError(self.env._(
                    'Dữ liệu ngày %(day)s đã thay đổi sau lúc bạn tải bảng đối chiếu; vui lòng tải lại trước khi xác nhận.',
                    day=_fmt_date(w_iso),
                ))
            canonical = day_item['canonical']
            w_date = fields.Date.from_string(w_iso)
            chosen_line = self.env['tp.hr.attendance.line']
            if decision in ('use_a', 'use_b'):
                if canonical['locked']:
                    raise UserError(self.env._('Ngày %(day)s thuộc kỳ công đã chốt; không ghi đè trực tiếp.', day=_fmt_date(w_iso)))
                if canonical['has_approved_correction']:
                    raise UserError(self.env._('Ngày %(day)s đã có điều chỉnh được duyệt; không ghi đè từ file.', day=_fmt_date(w_iso)))
                src_cell = day_item['a_cell'] if decision == 'use_a' else day_item['b_cell']
                src_batch = batch_a if decision == 'use_a' else batch_b
                src_sheet = sheet_a_index if decision == 'use_a' else sheet_b_index
                src_person = pa_by_emp.get(emp_id) if decision == 'use_a' else pb_by_emp.get(emp_id)
                if not src_cell or src_cell.get('kind') not in ('pair', 'missing_in', 'missing_out') or not src_person:
                    raise UserError(self.env._('Bản được chọn cho ngày %(day)s không có giờ hợp lệ để áp dụng.', day=_fmt_date(w_iso)))
                if canonical['exists'] and not _cell_matches_canonical(src_cell, canonical) and not reason:
                    raise UserError(self.env._('Cần nhập lý do khi thay đổi dữ liệu đã áp dụng ở ngày %(day)s.', day=_fmt_date(w_iso)))
                chosen_line = self._tp_apply_cell_to_canonical(
                    company, src_batch, src_sheet, src_person, src_cell,
                    [batch_a, batch_b] if day_item['group'] == 'same' and batch_b else [src_batch],
                    [], reason=reason,
                )
                touched_days.add((emp_id, w_date))
                after_snap = {'source_batch': src_batch.batch_code, 'in': src_cell['norm_in'], 'out': src_cell['norm_out'], 'kind': src_cell['kind']}
            elif decision == 'keep_current':
                after_snap = {'kept_in': canonical['norm_in'], 'kept_out': canonical['norm_out'], 'kind': canonical['kind']}
            else:
                after_snap = {'deferred': True}

            old_res = Res.search([
                ('company_id', '=', company.id), ('target_kind', '=', 'day'),
                ('employee_id', '=', emp_id), ('work_date', '=', w_date), ('is_latest', '=', True),
            ])
            if old_res:
                old_res.write({'is_latest': False})
            new_res = Res.create({
                'company_id': company.id,
                'batch_a_id': batch_a.id,
                'batch_b_id': batch_b.id if batch_b else False,
                'sheet_a_index': sheet_a_index,
                'sheet_b_index': sheet_b_index,
                'target_kind': 'day',
                'employee_id': emp_id,
                'work_date': w_date,
                'decision': decision,
                'reason': reason or False,
                'actor_id': self.env.user.id,
                'decided_at': now,
                'before_snapshot': {'in': canonical['norm_in'], 'out': canonical['norm_out'], 'kind': canonical['kind'], 'version': canonical['version']},
                'after_snapshot': after_snap,
                'target_version': canonical['version'] + (1 if decision in ('use_a', 'use_b') else 0),
                'is_latest': True,
            })
            if decision != 'defer':
                b_ids = [b.id for b in (batch_a, batch_b) if b]
                conflict_lines = Line.search([
                    ('batch_id', 'in', b_ids), ('employee_id', '=', emp_id), ('work_date', '=', w_date),
                ])
                for cl in conflict_lines:
                    vals = {'resolved_by_resolution_id': new_res.id}
                    if cl != chosen_line and cl.state == 'conflict':
                        vals['resolution'] = self.env._('Đã xử lý (%(choice)s)', choice=dict(DECISIONS)[decision])
                        vals['issue_open'] = False
                    internal(cl).write(vals)
            return True

        if t_kind == 'late':
            f_iso = str(target.get('date_from') or '')
            t_iso = str(target.get('date_to') or '')
            late_item = next((li for li in p_row['late_items'] if li['date_from'] == f_iso and li['date_to'] == t_iso), None)
            if not late_item:
                raise UserError(self.env._('Không tìm thấy tổng Đi muộn cho kỳ %(from_d)s – %(to_d)s.', from_d=f_iso, to_d=t_iso))
            if expected_digest and late_item['target_digest'] != expected_digest:
                raise UserError(self.env._('Tổng Đi muộn đã thay đổi sau lúc tải đối chiếu; vui lòng tải lại.'))
            can_late = late_item['canonical_late']
            d_from = fields.Date.from_string(f_iso)
            d_to = fields.Date.from_string(t_iso)
            if decision in ('use_a', 'use_b'):
                if can_late['locked']:
                    raise UserError(self.env._('Kỳ công đã chốt; không thay đổi tổng Đi muộn.'))
                src_late = late_item['a_late'] if decision == 'use_a' else late_item['b_late']
                src_batch = batch_a if decision == 'use_a' else batch_b
                src_sheet = sheet_a_index if decision == 'use_a' else sheet_b_index
                src_person = pa_by_emp.get(emp_id) if decision == 'use_a' else pb_by_emp.get(emp_id)
                if not src_late or src_late.get('source_state') != 'ok' or not src_person:
                    raise UserError(self.env._('Bản được chọn không có tổng Đi muộn hợp lệ.'))
                if can_late['exists'] and (can_late['count'], can_late['minutes']) != (src_late['count'], src_late['minutes']) and not reason:
                    raise UserError(self.env._('Cần nhập lý do khi thay tổng Đi muộn đã áp dụng.'))
                self._tp_apply_late_to_canonical(
                    company, emp_id, d_from, d_to, src_batch, src_sheet, src_person, src_late,
                    [batch_a, batch_b] if late_item['group'] == 'same' and batch_b else [src_batch],
                    reason=reason or self.env._('Chọn nguồn đối chiếu %(code)s', code=src_batch.batch_code or src_batch.name),
                )
                after_snap = {'source_batch': src_batch.batch_code, 'count': src_late['count'], 'minutes': src_late['minutes']}
            elif decision == 'keep_current':
                after_snap = {'kept_count': can_late['count'], 'kept_minutes': can_late['minutes']}
            else:
                after_snap = {'deferred': True}

            old_res = Res.search([
                ('company_id', '=', company.id), ('target_kind', '=', 'late'),
                ('employee_id', '=', emp_id), ('late_date_from', '=', d_from), ('late_date_to', '=', d_to), ('is_latest', '=', True),
            ])
            if old_res:
                old_res.write({'is_latest': False})
            new_res = Res.create({
                'company_id': company.id,
                'batch_a_id': batch_a.id,
                'batch_b_id': batch_b.id if batch_b else False,
                'sheet_a_index': sheet_a_index,
                'sheet_b_index': sheet_b_index,
                'target_kind': 'late',
                'employee_id': emp_id,
                'late_date_from': d_from,
                'late_date_to': d_to,
                'decision': decision,
                'reason': reason or False,
                'actor_id': self.env.user.id,
                'decided_at': now,
                'before_snapshot': {'count': can_late['count'], 'minutes': can_late['minutes'], 'version': can_late['version']},
                'after_snapshot': after_snap,
                'target_version': can_late['version'] + (1 if decision in ('use_a', 'use_b') else 0),
                'is_latest': True,
            })
            if decision != 'defer':
                b_ids = [b.id for b in (batch_a, batch_b) if b]
                conflict_lates = Late.search([
                    ('batch_id', 'in', b_ids), ('employee_id', '=', emp_id),
                    ('date_from', '=', d_from), ('date_to', '=', d_to),
                ])
                internal(conflict_lates).write({'resolved_by_resolution_id': new_res.id})
            return True

        raise UserError(self.env._('Loại đối tượng đối chiếu không hợp lệ.'))

    @api.model
    def tp_resolve_compare(self, params=None):
        """Apply one explicit source decision for selected day cells or period late totals under lock + CAS."""
        params = dict(params or {})
        decision = params.get('decision')
        reason = str(params.get('reason') or '').strip()
        targets = params.get('targets') or []
        if not isinstance(targets, list) or not targets:
            raise UserError(self.env._('Chưa chọn phạm vi nhân viên / ngày cần xử lý.'))
        items = [dict(t, decision=decision, reason=t.get('reason') if t.get('reason') is not None else reason) for t in targets]
        return self.tp_resolve_compare_batch(dict(params, items=items))

    @api.model
    def tp_resolve_compare_batch(self, params=None):
        """Apply mixed per-item source decisions atomically inside one advisory/row lock + CAS transaction."""
        params = dict(params or {})
        default_reason = str(params.get('reason') or '').strip()
        items = params.get('items') or []
        if not isinstance(items, list) or not items:
            raise UserError(self.env._('Chưa có lựa chọn xử lý sai khác nào được gửi lên.'))

        batch_a = self._tp_accessible_batch(params.get('batch_a_id'))
        batch_b = self._tp_accessible_batch(params.get('batch_b_id')) if params.get('batch_b_id') else self.browse()
        sheet_a_index = int(params.get('sheet_a_index') or 0)
        sheet_b_index = int(params.get('sheet_b_index') or 0)

        batch_a._lock()
        if batch_b and batch_b != batch_a:
            batch_b._lock()
        company = batch_a.company_id
        ctx = self._tp_build_compare_context(batch_a, sheet_a_index, batch_b, sheet_b_index)

        by_emp = {p['employee_id']: p for p in ctx['people_rows'] if p['mapping_state'] == 'mapped' and p['employee_id']}
        pa_by_emp = {p['employee_id']: p for p in ctx['eval_a']['people'] if p['mapping_state'] == 'mapped' and p['employee_id']}
        pb_by_emp = {p['employee_id']: p for p in ctx['eval_b']['people'] if p['mapping_state'] == 'mapped' and p['employee_id']} if ctx['eval_b'] else {}

        touched_days = set()
        now = fields.Datetime.now()
        resolved_count = 0
        applied_any = False

        for item in items:
            dec = item.get('decision')
            item_reason = str(item.get('reason') if item.get('reason') is not None else default_reason).strip()
            self._tp_apply_compare_item_decision(
                company, ctx, batch_a, batch_b, sheet_a_index, sheet_b_index,
                pa_by_emp, pb_by_emp, by_emp, item, dec, item_reason, touched_days, now,
            )
            if dec in ('use_a', 'use_b'):
                applied_any = True
            resolved_count += 1

        if touched_days:
            self.env['tp.hr.attendance.day']._tp_refresh(company, touched_days)

        unique_batches = [batch_a] + ([batch_b] if batch_b and batch_b != batch_a else [])
        for b in unique_batches:
            b._tp_classify()
            if b.state == 'preview' and applied_any:
                internal(b).write({'applied_by': self.env.user.id, 'applied_at': now})
            self._tp_recount_batch_after_resolution(b)

        self.env['tp.hr.attendance.log']._tp_log(batch_a, 'compare_resolve', {
            'batch_b_id': batch_b.id if batch_b else 0,
            'targets': resolved_count,
            'reason': default_reason[:160],
        })
        return {
            'resolved': resolved_count,
            'compare': self.tp_compare_batches(params),
        }

    @api.model
    def tp_export_compare(self, params=None):
        """Export filtered A/B comparison (day cells + period late totals) to a formula-safe .xlsx workbook."""
        params = dict(params or {})
        params['page'] = 1
        params['page_size'] = 100
        # Build full filtered rows without pagination cap for export
        company = self.env.company
        require(self.env, 'import', company)
        self.check_access('read')
        batch_a = self._tp_accessible_batch(params.get('batch_a_id'))
        batch_b = self._tp_accessible_batch(params.get('batch_b_id')) if params.get('batch_b_id') else self.browse()
        sheet_a_index = int(params.get('sheet_a_index') or 0)
        sheet_b_index = int(params.get('sheet_b_index') or 0)
        ctx = self._tp_build_compare_context(batch_a, sheet_a_index, batch_b, sheet_b_index)

        only_diff = bool(params.get('only_diff'))
        group_filter = str(params.get('group') or '').strip()
        if group_filter and group_filter not in COMPARE_GROUP_LABELS:
            group_filter = ''
        source_group = str(params.get('source_group') or '').strip()
        search_fold = fold(params.get('search') or '')
        filter_date = _parse_iso_date(params.get('work_date'))
        filter_date_iso = filter_date.isoformat() if filter_date else ''

        wb = Workbook()
        ws_day = wb.active
        ws_day.title = 'Doi chieu theo ngay'
        ws_late = wb.create_sheet('Doi chieu di muon ky')

        bold_font = Font(bold=True, color='17324D')
        head_fill = PatternFill('solid', fgColor='EAF2FB')
        thin = Side(border_style='thin', color='D7E2EF')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        left_align = Alignment(horizontal='left', vertical='center', wrap_text=True)

        a_label = f"{batch_a.batch_code or batch_a.id} ({batch_a.file_name or batch_a.name})"
        b_label = f"{batch_b.batch_code or batch_b.id} ({batch_b.file_name or batch_b.name})" if batch_b else 'Chưa chọn tệp B'
        stamp = self._tp_stamp(fields.Datetime.now())

        ws_day.append([xlsx_safe(f"ĐỐI CHIẾU CHẤM CÔNG · A: {a_label} · B: {b_label} · Xuất lúc {stamp}")])
        ws_day.append([xlsx_safe(
            f"Trang A: {ctx['eval_a']['sheet_name']} ({ctx['eval_a']['period_full']}) · "
            f"Trang B: {ctx['eval_b']['sheet_name'] + ' (' + ctx['eval_b']['period_full'] + ')' if ctx['eval_b'] else '—'}",
        )])
        ws_day.append([
            'Nhân viên', 'Mã Excel (A)', 'Mã Excel (B)', 'Mã HR', 'Ngày', 'Thứ',
            'Nguồn A', 'Nguồn B', 'Đang hiệu lực', 'Nhóm đối chiếu', 'Quyết định gần nhất', 'Ghi chú',
        ])
        for c in range(1, 13):
            cell = ws_day.cell(3, c)
            cell.font = bold_font
            cell.fill = head_fill
            cell.border = border
            cell.alignment = left_align
            ws_day.column_dimensions[get_column_letter(c)].width = 22 if c in (1, 7, 8, 9, 10, 12) else 14

        ws_late.append([xlsx_safe(f"ĐỐI CHIẾU TỔNG ĐI MUỘN (NGUYÊN EXCEL ĐÚNG KỲ) · A: {a_label} · B: {b_label}")])
        ws_late.append([xlsx_safe("Không cộng chồng tuần–tháng; chỉ so sánh trực tiếp khi hai tệp có cùng kỳ nguồn.")])
        ws_late.append([
            'Nhân viên', 'Mã HR', 'Kỳ nguồn', 'Nguồn A (Lần / Phút)', 'Nguồn B (Lần / Phút)',
            'Đang hiệu lực (Lần / Phút)', 'Nhóm đối chiếu', 'Quyết định gần nhất', 'Ghi chú',
        ])
        for c in range(1, 10):
            cell = ws_late.cell(3, c)
            cell.font = bold_font
            cell.fill = head_fill
            cell.border = border
            cell.alignment = left_align
            ws_late.column_dimensions[get_column_letter(c)].width = 22 if c in (1, 4, 5, 6, 7, 9) else 15

        def _fmt_side_cell(scope, cell):
            if scope == 'in_period' and cell:
                return f"{cell.get('raw_in') or '—'} / {cell.get('raw_out') or '—'}"
            return SCOPE_LABELS.get(scope, scope)

        def _fmt_late_side(late):
            if not late:
                return '—'
            if late.get('source_state') == 'ok':
                return f"{late.get('count')} lần / {late.get('minutes')} phút"
            return f"{late.get('raw_count') or '—'} / {late.get('raw_minutes') or '—'} ({late.get('source_state')})"

        day_count = 0
        late_count = 0
        for p in ctx['people_rows']:
            if source_group and p['group_key'] != source_group:
                continue
            if search_fold:
                hay = ' '.join([
                    fold(p['display_name']), fold(p['source_name_a']), fold(p['source_name_b']),
                    fold(p['raw_code_a']), fold(p['raw_code_b']), fold(p['hr_code']), fold(p['machine_code']),
                ])
                if search_fold not in hay:
                    continue

            for d in p['days']:
                if filter_date_iso and d['date'] != filter_date_iso:
                    continue
                if only_diff and d['group'] not in ('diff', 'only_a', 'only_b', 'unready'):
                    continue
                if group_filter and d['group'] != group_filter:
                    continue
                if d['group'] == 'blank' and not filter_date_iso:
                    continue
                can = d['canonical']
                can_txt = f"{can.get('norm_in') or '—'} / {can.get('norm_out') or '—'} ({can.get('source_label') or ''})" if can.get('exists') else 'Chưa có'
                res_txt = f"{d['latest_resolution']['decision_label']} ({d['latest_resolution']['actor']})" if d.get('latest_resolution') else ''
                ws_day.append([
                    xlsx_safe(p['display_name']),
                    xlsx_safe(p['raw_code_a'] or '—'),
                    xlsx_safe(p['raw_code_b'] or '—'),
                    xlsx_safe(p['hr_code'] or '—'),
                    xlsx_safe(_fmt_date(d['date'])),
                    xlsx_safe(d['weekday']),
                    xlsx_safe(_fmt_side_cell(d['a_scope'], d['a_cell'])),
                    xlsx_safe(_fmt_side_cell(d['b_scope'], d['b_cell'])),
                    xlsx_safe(can_txt),
                    xlsx_safe(d['group_label']),
                    xlsx_safe(res_txt),
                    xlsx_safe(d['blocked_reason'] or d['reason']),
                ])
                day_count += 1

            for li in p['late_items']:
                if only_diff and li['group'] not in ('diff', 'only_a', 'only_b', 'unready'):
                    continue
                if group_filter and li['group'] != group_filter:
                    continue
                can_l = li['canonical_late']
                can_l_txt = f"{can_l['count']} lần / {can_l['minutes']} phút" if can_l.get('exists') else 'Chưa có'
                res_l_txt = f"{li['latest_resolution']['decision_label']} ({li['latest_resolution']['actor']})" if li.get('latest_resolution') else ''
                ws_late.append([
                    xlsx_safe(p['display_name']),
                    xlsx_safe(p['hr_code'] or '—'),
                    xlsx_safe(li['period_label']),
                    xlsx_safe(_fmt_late_side(li.get('a_late'))),
                    xlsx_safe(_fmt_late_side(li.get('b_late'))),
                    xlsx_safe(can_l_txt),
                    xlsx_safe(li['group_label']),
                    xlsx_safe(res_l_txt),
                    xlsx_safe(li['blocked_reason'] or li['reason']),
                ])
                late_count += 1

        stream = BytesIO()
        wb.save(stream)
        self.env['tp.hr.attendance.log']._tp_log(batch_a, 'compare_export', {
            'batch_b_id': batch_b.id if batch_b else 0,
            'day_rows': day_count,
            'late_rows': late_count,
        })
        code_a = (batch_a.batch_code or f'lo-{batch_a.id}').lower().replace(' ', '-')
        code_b = (batch_b.batch_code or f'lo-{batch_b.id}').lower().replace(' ', '-') if batch_b else 'he-thong'
        return {
            'filename': f"doi-chieu-{code_a}-vs-{code_b}.xlsx",
            'data': base64.b64encode(stream.getvalue()).decode(),
        }
