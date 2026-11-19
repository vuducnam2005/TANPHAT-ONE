"""Immutable per-file source snapshots, multi-file upload, matrix view/filter/export (HR-ATTENDANCE-MATRIX-003, DEC-058).

Design invariants:
1. Raw source data (employee row, raw TP0xx Excel code, machine ID, title, source group, Vào/Ra cells including blanks,
   machine Đi muộn Lần/Phút and optional Vắng mặt source column) is stored once per batch + sheet and is strictly
   immutable afterwards.
2. HR mapping, locked periods and canonical comparison states are computed as a separate live status layer so neither
   changing HR records nor applying another batch ever mutates the stored source file snapshot.
3. Every RPC enforces ``import`` capability + company scope + record access on ``tp.hr.attendance.batch``; regular
   employees never read raw import batches.
"""
import base64
import json
from collections import defaultdict
from datetime import date
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .attendance_common import (
    DEFAULT_TZ,
    deny_direct,
    fold,
    internal,
    local_to_utc,
    require,
)
from .attendance_import import (
    ADVISORY_KEY,
    KIND_MESSAGES,
    LINE_STATES,
    UPLOAD_MAX_B64,
    consistent,
)
from .attendance_logic import short_range, xlsx_safe
from .attendance_parser import (
    ABSENT_STATES,
    LATE_STATES,
    PARSER_VERSION,
    SNAPSHOT_CELL_KINDS,
    AttendanceFormatError,
    parse_attendance,
)

MATRIX_PAGE_SIZES = (10, 20, 50, 100)
# Parser version that first persisted snapshot rows (MATRIX-003). Used when existing rows have lost their version flag.
SNAPSHOT_FIRST_PARSER_VERSION = 2
MAX_FILES_UPLOAD = 20
EMPTY_GROUP_KEY = '__EMPTY__'

BATCH_STATE_LABELS = {
    'draft': 'Chọn tệp',
    'preview': 'Đã đọc/Lưu nguồn – Chưa áp dụng vào bảng tổng hợp',
    'partial': 'Đã cập nhật một phần – Còn dữ liệu cần kiểm tra',
    'applied': 'Đã áp dụng vào bảng tổng hợp',
    'cancelled': 'Đã bỏ qua nguồn – Không áp dụng',
}

CELL_STATUS_META = {
    'empty': ('Ô trống trong kỳ', ''),
    'applied': ('Đã áp dụng vào bảng công', 'Đã áp'),
    'valid': ('Mới hợp lệ – sẵn sàng áp dụng', 'Mới'),
    'duplicate': ('Trùng giờ đã có – không nhân đôi', 'Trùng'),
    'conflict': ('Khác giờ với dữ liệu đang áp dụng – chờ chọn nguồn', 'Khác giờ'),
    'missing': ('Thiếu giờ Vào hoặc Ra', 'Thiếu giờ'),
    'review': ('Ký hiệu / giờ cần HR kiểm tra', 'Kiểm tra'),
    'unmapped': ('Chưa đối chiếu được hồ sơ HR', 'Chưa map'),
    'name_conflict': ('Mã máy khớp nhưng họ tên khác hồ sơ HR', 'Khác tên'),
    'locked': ('Thuộc kỳ công đã chốt', 'Kỳ chốt'),
}

FILTER_STATUS_OPTIONS = [
    ('new', 'Mới hợp lệ'),
    ('applied', 'Đã áp dụng'),
    ('duplicate', 'Trùng giờ đã có'),
    ('conflict', 'Khác dữ liệu / Xung đột'),
    ('missing', 'Thiếu giờ Vào/Ra'),
    ('review', 'Ký hiệu / Cần kiểm tra'),
    ('unmapped', 'Chưa map HR / Khác tên'),
    ('locked', 'Kỳ đã chốt'),
    ('all_empty', 'Toàn ô trống trong kỳ'),
]


def _binary_bytes(value):
    """Extract raw workbook bytes from an Odoo Binary field across context modes."""
    if not value:
        return b''
    if hasattr(value, 'content'):
        return value.content or b''
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
        return raw if raw[:2] == b'PK' else base64.b64decode(raw)
    if isinstance(value, str):
        return base64.b64decode(value)
    return b''


def _parse_iso_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        msg = 'Ngày lọc không hợp lệ.'
        raise UserError(msg) from None


def _fmt_date(value):
    if not value:
        return ''
    if isinstance(value, str):
        value = date.fromisoformat(value)
    return value.strftime('%d/%m/%Y')


def _fmt_short_day(value):
    if not value:
        return ''
    if isinstance(value, str):
        value = date.fromisoformat(value)
    return value.strftime('%d/%m')


class AttendanceSnapshotPerson(models.Model):
    _name = 'tp.hr.attendance.snapshot.person'
    _description = 'Ảnh chụp nhân viên theo tệp nguồn chấm công'
    _order = 'batch_id desc, sheet_index, person_seq, id'
    _check_company_auto = True

    batch_id = fields.Many2one('tp.hr.attendance.batch', 'Lô nguồn', required=True, index=True, ondelete='cascade', readonly=True)
    company_id = fields.Many2one(related='batch_id.company_id', store=True, index=True, string='Công ty', readonly=True)
    sheet_index = fields.Integer('Thứ tự trang', required=True, index=True, readonly=True)
    sheet_name = fields.Char('Trang tính', required=True, readonly=True)
    person_seq = fields.Integer('Thứ tự trong trang', required=True, readonly=True)
    stt_raw = fields.Char('STT nguồn', readonly=True)
    in_row_number = fields.Integer('Dòng Vào', required=True, readonly=True)
    out_row_number = fields.Integer('Dòng Ra', readonly=True)
    raw_source_code = fields.Char('Mã NV (Excel)', index=True, readonly=True)
    raw_machine_code = fields.Char('ID máy (raw)', readonly=True)
    machine_code = fields.Char('ID máy chuẩn hóa', index=True, readonly=True)
    source_name = fields.Char('Tên nhân viên (nguồn)', readonly=True)
    source_title = fields.Char('Chức vụ (nguồn)', readonly=True)
    source_group = fields.Char('Đơn vị (nguồn)', index=True, readonly=True)
    group_seq = fields.Integer('Thứ tự nhóm', default=0, readonly=True)
    period_from = fields.Date('Từ ngày', readonly=True)
    period_to = fields.Date('Đến ngày', readonly=True)
    late_source_state = fields.Selection(
        [('no_column', 'Không có cột'), *[(s, s) for s in LATE_STATES]],
        string='Trạng thái Đi muộn nguồn', default='no_column', readonly=True,
    )
    late_count = fields.Integer('Đi muộn (Lần)', readonly=True)
    late_minutes = fields.Integer('Đi muộn (Phút)', readonly=True)
    late_raw_count = fields.Char('Lần (raw)', readonly=True)
    late_raw_minutes = fields.Char('Phút (raw)', readonly=True)
    late_cell_ref = fields.Char('Ô Đi muộn', readonly=True)
    absent_source_state = fields.Selection(
        [(s, s) for s in ABSENT_STATES],
        string='Trạng thái Vắng mặt nguồn', default='no_column', readonly=True,
    )
    absent_raw = fields.Char('Vắng mặt (Excel kỳ nguồn)', readonly=True)
    absent_cell_ref = fields.Char('Ô Vắng mặt', readonly=True)
    nonempty_count = fields.Integer('Số ngày có giờ', default=0, readonly=True)
    empty_count = fields.Integer('Số ngày trống', default=0, readonly=True)
    cell_ids = fields.One2many('tp.hr.attendance.snapshot.cell', 'person_id', 'Ô ngày nguồn', readonly=True)
    source_values = fields.Json('Giá trị và kiểu ô nguồn', readonly=True)

    _person_sheet_unique = models.UniqueIndex(
        '(batch_id, sheet_index, in_row_number)',
        'Mỗi dòng nhân viên trong trang tính chỉ lưu một bản chụp nguồn.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        deny_direct(self)
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._('Dữ liệu nguồn theo tệp Excel là bất biến, không được chỉnh sửa.'))

    def unlink(self):
        deny_direct(self)
        if any(rec.batch_id.state != 'draft' for rec in self.sudo()):
            raise AccessError(self.env._('Không xóa dữ liệu nguồn của lô đã lưu.'))
        return super().unlink()


class AttendanceSnapshotCell(models.Model):
    _name = 'tp.hr.attendance.snapshot.cell'
    _description = 'Ảnh chụp ô ngày Vào/Ra theo tệp nguồn chấm công'
    _order = 'person_id, column_index'
    _check_company_auto = True

    person_id = fields.Many2one('tp.hr.attendance.snapshot.person', 'Nhân viên nguồn', required=True, index=True, ondelete='cascade', readonly=True)
    batch_id = fields.Many2one('tp.hr.attendance.batch', 'Lô nguồn', required=True, index=True, ondelete='cascade', readonly=True)
    company_id = fields.Many2one(related='batch_id.company_id', store=True, index=True, string='Công ty', readonly=True)
    sheet_index = fields.Integer('Thứ tự trang', required=True, index=True, readonly=True)
    column_index = fields.Integer('Cột', required=True, readonly=True)
    cell_ref = fields.Char('Tọa độ ô', readonly=True)
    work_date = fields.Date('Ngày công', required=True, index=True, readonly=True)
    kind = fields.Selection([(k, k) for k in SNAPSHOT_CELL_KINDS], 'Loại ô', required=True, readonly=True)
    raw_in = fields.Char('Vào (raw)', readonly=True)
    raw_out = fields.Char('Ra (raw)', readonly=True)
    norm_in = fields.Char('Vào chuẩn hóa', readonly=True)
    norm_out = fields.Char('Ra chuẩn hóa', readonly=True)
    check_in = fields.Datetime('Giờ vào UTC', readonly=True)
    check_out = fields.Datetime('Giờ ra UTC', readonly=True)
    source_values = fields.Json('Giá trị và kiểu ô nguồn', readonly=True)

    _cell_unique = models.UniqueIndex(
        '(person_id, column_index)',
        'Mỗi cột ngày của nhân viên chỉ lưu một ô nguồn.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        deny_direct(self)
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._('Ô dữ liệu nguồn theo tệp Excel là bất biến, không được chỉnh sửa.'))

    def unlink(self):
        deny_direct(self)
        if any(rec.batch_id.state != 'draft' for rec in self.sudo()):
            raise AccessError(self.env._('Không xóa ô dữ liệu nguồn của lô đã lưu.'))
        return super().unlink()


class AttendanceBatchMatrix(models.Model):
    _inherit = 'tp.hr.attendance.batch'

    snapshot_person_ids = fields.One2many('tp.hr.attendance.snapshot.person', 'batch_id', 'Ảnh chụp nhân viên theo tệp', readonly=True)

    # --------------------------------------------------- snapshot construction
    def _tp_build_snapshot(self, sheets=None):
        """Persist immutable per-person and per-day-cell source rows once for this batch."""
        self.ensure_one()
        self._lock()
        Person = internal(self.env['tp.hr.attendance.snapshot.person'])
        Cell = internal(self.env['tp.hr.attendance.snapshot.cell'])
        if Person.search_count([('batch_id', '=', self.id)], limit=1):
            # Stored rows are immutable and complete; only the batch flags can be missing (e.g. the columns were
            # dropped by a module downgrade and recreated empty). Mark the existing snapshot ready instead of
            # leaving the batch 'pending' forever, which would re-lock the batch on every matrix/compare/export read.
            if self.snapshot_state != 'ready' or not self.snapshot_version:
                internal(self).write({
                    'snapshot_state': 'ready',
                    'snapshot_version': self.snapshot_version or SNAPSHOT_FIRST_PARSER_VERSION,
                    'snapshot_note': False,
                })
            return True
        if sheets is None:
            raw = _binary_bytes(self.with_context(bin_size=False).sudo().file_data)
            if not raw:
                internal(self).write({
                    'snapshot_state': 'unavailable',
                    'snapshot_note': self.env._(
                        'Lô cũ không còn tệp Excel gốc đính kèm; chỉ có các dòng staging đã lưu, không giả phục dựng ô trống từ HR hiện tại.',
                    ),
                })
                return False
            try:
                sheets = parse_attendance(raw)
            except AttendanceFormatError as exc:
                internal(self).write({
                    'snapshot_state': 'unavailable',
                    'snapshot_note': str(exc)[:240],
                })
                return False

        tz = self.tz or DEFAULT_TZ
        person_vals_list = []
        per_person_cells = []
        updated_summary = list(self.sheet_summary or [])
        summary_by_idx = dict(enumerate(updated_summary))
        summary_changed = False

        for sheet in sheets:
            idx = sheet['index']
            if idx in summary_by_idx and not summary_by_idx[idx].get('day_columns') and sheet.get('day_columns'):
                summary_by_idx[idx] = dict(
                    summary_by_idx[idx],
                    absent=sheet.get('absent') or {},
                    day_columns=[
                        {
                            'column': col['column'], 'col_letter': col['col_letter'],
                            'date': col['date'].isoformat(), 'header_day': col['header_day'],
                            'header_weekday': col['header_weekday'], 'weekday': col['weekday'],
                        }
                        for col in sheet['day_columns']
                    ],
                )
                summary_changed = True
            if sheet['errors'] or not sheet['period']:
                continue
            p_from, p_to = sheet['period']
            for person in sheet['people']:
                cells = person.get('cells') or []
                empty_cnt = sum(1 for c in cells if c['kind'] == 'empty')
                person_vals_list.append({
                    'source_values': person.get('source_values') or {},
                    'batch_id': self.id,
                    'sheet_index': idx,
                    'sheet_name': sheet['name'],
                    'person_seq': person['person_seq'],
                    'stt_raw': person.get('stt_raw') or '',
                    'in_row_number': person['row'],
                    'out_row_number': person.get('out_row') or 0,
                    'raw_source_code': person.get('raw_source_code') or '',
                    'raw_machine_code': person.get('raw_machine_code') or '',
                    'machine_code': person.get('machine_code') or '',
                    'source_name': person.get('name') or '',
                    'source_title': person.get('title') or '',
                    'source_group': person.get('group') or '',
                    'group_seq': person.get('group_seq') or 0,
                    'period_from': p_from,
                    'period_to': p_to,
                    'late_source_state': person.get('late_state') or 'no_column',
                    'late_count': person.get('late_count') or 0,
                    'late_minutes': person.get('late_minutes') or 0,
                    'late_raw_count': person.get('late_raw_count') or '',
                    'late_raw_minutes': person.get('late_raw_minutes') or '',
                    'late_cell_ref': person.get('late_cell') or '',
                    'absent_source_state': person.get('absent_state') or 'no_column',
                    'absent_raw': person.get('absent_raw') or '',
                    'absent_cell_ref': person.get('absent_cell') or '',
                    'nonempty_count': len(cells) - empty_cnt,
                    'empty_count': empty_cnt,
                })
                per_person_cells.append((idx, cells))

        if person_vals_list:
            created_people = Person.create(person_vals_list)
            cell_vals_list = []
            for rec, (idx, cells) in zip(created_people, per_person_cells, strict=True):
                for cell in cells:
                    check_in = local_to_utc(cell['work_date'], cell['clock_in'], tz) if cell['clock_in'] else False
                    check_out = local_to_utc(cell['work_date'], cell['clock_out'], tz) if cell['clock_out'] else False
                    cell_vals_list.append({
                        'person_id': rec.id,
                        'batch_id': self.id,
                        'sheet_index': idx,
                        'column_index': cell['column'],
                        'cell_ref': cell['cell'],
                        'work_date': cell['work_date'],
                        'kind': cell['kind'],
                        'raw_in': cell['raw_in'] or '',
                        'raw_out': cell['raw_out'] or '',
                        'norm_in': cell['norm_in'] or '',
                        'norm_out': cell['norm_out'] or '',
                        'check_in': check_in,
                        'check_out': check_out,
                        'source_values': cell.get('source_values') or {},
                    })
            if cell_vals_list:
                Cell.create(cell_vals_list)

        vals = {
            'snapshot_version': PARSER_VERSION,
            'snapshot_state': 'ready',
            'snapshot_note': False,
        }
        if summary_changed:
            vals['sheet_summary'] = [summary_by_idx[i] for i in range(len(updated_summary))]
        internal(self).write(vals)
        return True

    # --------------------------------------------------------- navigation actions
    def action_open_matrix(self):
        self.ensure_one()
        self._tp_require()
        return {
            'type': 'ir.actions.client',
            'name': self.env._('Bảng dữ liệu theo file'),
            'tag': 'tp_hr_attendance.file_matrix',
            'params': {'batch_id': self.id, 'mode': 'matrix'},
        }

    def action_open_compare(self):
        self.ensure_one()
        self._tp_require()
        return {
            'type': 'ir.actions.client',
            'name': self.env._('Đối chiếu hai file chấm công'),
            'tag': 'tp_hr_attendance.file_matrix',
            'params': {'batch_id': self.id, 'batch_a_id': self.id, 'mode': 'compare'},
        }

    # --------------------------------------------------- multi-file upload & discard
    def _tp_stamp(self, dt_value):
        if not dt_value:
            return ''
        tz_env = self.with_context(tz=self.env.user.tz or DEFAULT_TZ)
        return fields.Datetime.context_timestamp(tz_env, dt_value).strftime('%d/%m/%Y %H:%M')

    def _tp_batch_selector_item(self):
        self.ensure_one()
        batch = self.sudo()
        code = batch.batch_code or f'LÔ-{batch.id:05d}'
        period_label = short_range(batch.period_from, batch.period_to) if batch.period_from and batch.period_to else ''
        period_full = f'{_fmt_date(batch.period_from)} – {_fmt_date(batch.period_to)}' if batch.period_from and batch.period_to else ''
        sheets = []
        total_people = 0
        for idx, sh in enumerate(batch.sheet_summary or []):
            s_from = fields.Date.from_string(sh['from']) if sh.get('from') else None
            s_to = fields.Date.from_string(sh['to']) if sh.get('to') else None
            emp_cnt = sh.get('employees') or 0
            total_people += emp_cnt
            sheets.append({
                'index': idx,
                'name': sh.get('name') or f'Sheet {idx + 1}',
                'from': sh.get('from') or '',
                'to': sh.get('to') or '',
                'period_label': short_range(s_from, s_to) if s_from and s_to else '',
                'employees': emp_cnt,
                'events': sh.get('events') or 0,
                'empty': sh.get('empty') or 0,
                'errors': sh.get('errors') or [],
                'has_absent': (sh.get('absent') or {}).get('state') == 'ok',
                'has_late': (sh.get('late') or {}).get('state') == 'ok',
            })
        uploaded_at = self._tp_stamp(batch.create_date)
        applied_at = self._tp_stamp(batch.applied_at)
        file_display = batch.file_name or batch.name or code
        selector_label = ' · '.join(filter(None, [
            code,
            file_display,
            f'Kỳ {period_label}' if period_label else '',
            f'Tải {uploaded_at}' if uploaded_at else '',
        ]))
        return {
            'id': batch.id,
            'batch_code': code,
            'name': batch.name,
            'file_name': batch.file_name or '',
            'checksum_short': (batch.checksum or '')[:12],
            'source_namespace': batch.source_namespace or 'excel-machine',
            'state': batch.state,
            'state_label': BATCH_STATE_LABELS.get(batch.state, batch.state),
            'can_apply': batch.state == 'preview',
            'can_discard': batch.state == 'preview',
            'period_from': fields.Date.to_string(batch.period_from) if batch.period_from else '',
            'period_to': fields.Date.to_string(batch.period_to) if batch.period_to else '',
            'period_label': period_label,
            'period_full': period_full,
            'people_count': total_people,
            'matched_count': len(batch.employee_ids),
            'uploaded_by': batch.create_uid.name or '',
            'uploaded_at': uploaded_at,
            'applied_by': batch.applied_by.name or '',
            'applied_at': applied_at,
            'cancel_reason': batch.cancel_reason or '',
            'same_file_batch_id': batch.same_file_batch_id.id or 0,
            'same_file_code': batch.same_file_batch_id.batch_code or batch.same_file_batch_id.name or '',
            'snapshot_state': batch.snapshot_state,
            'snapshot_note': batch.snapshot_note or '',
            'sheets': sheets,
            'selector_label': selector_label,
        }

    @api.model
    def tp_upload_files(self, params=None):
        """Persist each file and update attendance from its newest valid source, atomically per file."""
        params = dict(params or {})
        company = self.env.company
        require(self.env, 'import', company)
        files = params.get('files')
        if not isinstance(files, list) or not files:
            raise UserError(self.env._('Chưa chọn tệp Excel nào để tải lên.'))
        if len(files) > MAX_FILES_UPLOAD:
            raise UserError(self.env._('Mỗi lần tải tối đa %(max)s tệp Excel.', max=MAX_FILES_UPLOAD))

        # Allocate upload order under the same company lock as the canonical writers.
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [ADVISORY_KEY, company.id])
        results, created_ids = [], []
        for idx, item in enumerate(files):
            if not isinstance(item, dict):
                results.append({'ok': False, 'index': idx, 'file_name': f'Tệp #{idx + 1}', 'error': 'Dữ liệu tệp không hợp lệ.'})
                continue
            file_name = str(item.get('file_name') or '').strip()[:200] or f'tep-{idx + 1}.xlsx'
            data = item.get('data') or ''
            if not file_name.lower().endswith('.xlsx'):
                results.append({'ok': False, 'index': idx, 'file_name': file_name,
                                'error': self.env._('Chỉ nhận tệp định dạng .xlsx xuất từ máy chấm công.')})
                continue
            if not data or not isinstance(data, str):
                results.append({'ok': False, 'index': idx, 'file_name': file_name, 'error': self.env._('Tệp rỗng hoặc chưa đọc được nội dung.')})
                continue
            if len(data) > UPLOAD_MAX_B64:
                results.append({'ok': False, 'index': idx, 'file_name': file_name, 'error': self.env._('Tệp vượt quá giới hạn 15 MB.')})
                continue
            try:
                with self.env.cr.savepoint():
                    batch = self.create({
                        'name': self.env._('Excel máy · %(file)s', file=file_name),
                        'file_name': file_name,
                        'file_data': data,
                        'company_id': company.id,
                    })
                    batch.action_preview()
                    sync = batch._tp_apply_latest_file()
                    info = dict(batch._tp_batch_selector_item(), sync=sync)
                created_ids.append(info['id'])
                results.append(dict(info, ok=True, index=idx))
            except (AttendanceFormatError, UserError, ValidationError, AccessError) as exc:
                results.append({'ok': False, 'index': idx, 'file_name': file_name, 'error': str(exc)})
        return {
            'results': results,
            'created_ids': created_ids,
            'success_count': len(created_ids),
            'error_count': len(results) - len(created_ids),
        }

    def _tp_apply_latest_file(self):
        """Newest upload owns each mapped employee/day; keep immutable sources and all lock guards.

        Reuse the comparison writers for replacement/idempotency. Blank cells in the new file clear
        imported hours for that day; people/dates absent from the file stay untouched. Never replace
        approved corrections or device events. Ambiguous rows inside one workbook need HR review.
        """
        self.ensure_one()
        self._tp_require()
        self._lock()
        if self.state not in ('preview', 'partial', 'applied'):
            raise UserError(self.env._('Tệp nguồn chưa sẵn sàng để cập nhật bảng công.'))
        if not self._tp_build_snapshot():
            raise UserError(self.env._('Không còn tệp nguồn để cập nhật bảng công.'))
        company = self.company_id
        Period = self.env['tp.hr.attendance.period']
        locked = Period._tp_locked_ranges([company.id])
        Session = internal(self.env['tp.hr.attendance.session'])
        Line = internal(self.env['tp.hr.attendance.line'])
        resolver, _codes = self._tp_mapper()
        newer = defaultdict(list)
        for person in self.env['tp.hr.attendance.snapshot.person'].sudo().search([
                ('company_id', '=', company.id), ('batch_id', '>', self.id),
                ('batch_id.state', 'in', ('applied', 'partial'))]):
            employee, _candidate, problem, _message = resolver(person.machine_code, person.source_name)
            if employee and not problem:
                newer[employee.id].append((person.period_from, person.period_to))
        days, totals = defaultdict(list), defaultdict(list)
        stats = {'updated': 0, 'late_updated': 0, 'needs_review': 0, 'protected': 0, 'older_source': 0}
        for index, _sheet in enumerate(self.sheet_summary or []):
            evaluated = self._tp_evaluate_sheet_matrix(index)
            for person in evaluated['people']:
                if person['mapping_state'] != 'mapped':
                    stats['needs_review'] += 1
                    continue
                for cell in person['cells']:
                    days[person['employee_id'], fields.Date.from_string(cell['date'])].append((index, person, cell))
                late = person['late']
                if late['source_state'] == 'ok':
                    totals[person['employee_id'], fields.Date.from_string(evaluated['from']),
                           fields.Date.from_string(evaluated['to'])].append((index, person, late))
        touched = set()
        reason = self.env._('Cập nhật theo tệp tải lên mới nhất: %(file)s', file=self.file_name)
        for (employee_id, work_date), entries in days.items():
            if any(first <= work_date <= last for first, last in newer[employee_id]):
                stats['older_source'] += 1
                continue
            protected = Period._tp_is_locked(company.id, work_date, locked) or Session.search_count([
                ('employee_id', '=', employee_id), ('work_date', '=', work_date), ('source', '=', 'correction')])
            protected = protected or self.env['tp.hr.attendance.event'].sudo().search_count([
                ('company_id', '=', company.id), ('employee_id', '=', employee_id),
                ('local_date', '=', work_date), ('state', '=', 'mapped')])
            if protected:
                stats['protected'] += 1
                continue
            index, person, cell = entries[0]
            signatures = {(entry[2]['kind'], entry[2]['raw_in'], entry[2]['raw_out']) for entry in entries}
            if len(signatures) != 1 or cell['kind'] not in ('pair', 'missing_in', 'missing_out', 'empty'):
                stats['needs_review'] += 1
                continue
            if cell['kind'] == 'empty':
                Session.search([('employee_id', '=', employee_id), ('work_date', '=', work_date)]).write(
                    {'active': False, 'superseded_reason': reason})
                Line.search([('employee_id', '=', employee_id), ('work_date', '=', work_date), ('issue_open', '=', True)]).write(
                    {'issue_open': False, 'resolution': reason})
            else:
                self._tp_apply_cell_to_canonical(company, self, index, person, cell, [self], [], reason=reason)
            touched.add((employee_id, work_date))
            stats['updated'] += 1
        for (employee_id, first, last), entries in totals.items():
            if any(first <= end and last >= start for start, end in newer[employee_id]):
                continue
            if any(first <= end and last >= start for start, end in locked.get(company.id, [])):
                continue
            if len({(entry[2]['count'], entry[2]['minutes']) for entry in entries}) != 1:
                stats['needs_review'] += 1
                continue
            index, person, late = entries[0]
            self._tp_apply_late_to_canonical(company, employee_id, first, last, self, index, person, late, [self], reason=reason)
            stats['late_updated'] += 1
        self.env['tp.hr.attendance.day']._tp_refresh(company, touched)
        self._tp_classify()
        internal(self).write({'state': 'partial' if stats['needs_review'] or stats['protected'] else 'applied',
                              'applied_by': self.env.uid, 'applied_at': fields.Datetime.now(), 'result': json.dumps(stats)})
        self.env['tp.hr.attendance.log']._tp_log(self, 'import_latest_file', stats)
        return stats

    @api.model
    def tp_discard_batch(self, batch_id, reason=''):
        """Explicitly discard an unapplied source batch with audit log; never deletes applied records."""
        batch = self._tp_upload_batch(batch_id)
        batch.action_cancel(reason=reason)
        return batch._tp_batch_selector_item()

    @api.model
    def tp_matrix_batches(self, params=None):
        """Return source batches visible to the current import officer in the active company."""
        params = dict(params or {})
        company = self.env.company
        require(self.env, 'import', company)
        self.check_access('read')
        domain = [('company_id', '=', company.id), ('state', '!=', 'draft')]
        if not params.get('include_cancelled'):
            domain.append(('state', '!=', 'cancelled'))
        batches = self.search(domain, order='id desc', limit=200)
        return {'batches': [batch._tp_batch_selector_item() for batch in batches]}

    # --------------------------------------------------- live matrix evaluation
    def _tp_accessible_batch(self, batch_id):
        company = self.env.company
        require(self.env, 'import', company)
        self.check_access('read')
        batch = self.browse(int(batch_id or 0)).exists()
        if not batch or batch.company_id != company:
            raise AccessError(self.env._('Lô nguồn không tồn tại hoặc nằm ngoài phạm vi công ty đang chọn.'))
        batch.check_access('read')
        return batch

    def _tp_evaluate_sheet_matrix(self, sheet_index=0):
        """Read-only evaluation of one sheet's immutable source rows + live HR mapping & canonical status."""
        self.ensure_one()
        batch = self.sudo()
        company = batch.company_id
        summaries = batch.sheet_summary or []
        if not summaries:
            return {
                'sheet_index': 0, 'sheet_name': '', 'from': '', 'to': '', 'period_label': '',
                'errors': ['Lô chưa có thông tin trang tính.'], 'day_columns': [], 'people': [],
                'group_options': [], 'has_late': False, 'has_absent': False,
            }
        sheet_index = min(max(0, int(sheet_index or 0)), len(summaries) - 1)
        sh = summaries[sheet_index]
        s_from = fields.Date.from_string(sh['from']) if sh.get('from') else None
        s_to = fields.Date.from_string(sh['to']) if sh.get('to') else None

        Person = self.env['tp.hr.attendance.snapshot.person'].sudo()
        Cell = self.env['tp.hr.attendance.snapshot.cell'].sudo()
        people_recs = Person.search([('batch_id', '=', batch.id), ('sheet_index', '=', sheet_index)], order='person_seq, id')
        cell_recs = Cell.search([('batch_id', '=', batch.id), ('sheet_index', '=', sheet_index)], order='person_id, column_index')
        cells_by_person = defaultdict(list)
        for c in cell_recs:
            cells_by_person[c.person_id.id].append(c)

        day_columns = []
        for col in sh.get('day_columns') or []:
            d_obj = fields.Date.from_string(col['date'])
            day_columns.append({
                'column': col['column'],
                'col_letter': col.get('col_letter') or '',
                'date': col['date'],
                'day_month': d_obj.strftime('%d/%m'),
                'header_day': col.get('header_day') or str(d_obj.day),
                'weekday': col.get('weekday') or '',
                'weekend': d_obj.weekday() >= 5,
            })
        if not day_columns and cell_recs:
            seen_cols = {}
            for c in cell_recs:
                if c.column_index not in seen_cols:
                    seen_cols[c.column_index] = c.work_date
            weekday_names = ('T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN')
            for col_idx, d_obj in sorted(seen_cols.items()):
                day_columns.append({
                    'column': col_idx,
                    'col_letter': get_column_letter(col_idx),
                    'date': d_obj.isoformat(),
                    'day_month': d_obj.strftime('%d/%m'),
                    'header_day': str(d_obj.day),
                    'weekday': weekday_names[d_obj.weekday()],
                    'weekend': d_obj.weekday() >= 5,
                })

        resolve, _codes = self._tp_mapper()
        Period = self.env['tp.hr.attendance.period']
        locked_ranges = Period._tp_locked_ranges([company.id])

        # Index stored lines and lates of this batch + sheet
        lines_by_coord = {}
        for line in batch.line_ids.filtered(lambda line: line.sheet_index == sheet_index):
            lines_by_coord[line.row_number, line.column_index] = line
        lates_by_row = {}
        for late_rec in batch.late_ids.filtered(lambda r: r.sheet_index == sheet_index):
            lates_by_row[late_rec.row_number] = late_rec

        # Prefetch canonical sessions and applied late totals for live status evaluation
        mapped_emp_ids = set()
        resolved_map = {}
        for p in people_recs:
            emp, cand, prob, msg = resolve(p.machine_code, p.source_name)
            resolved_map[p.id] = (emp, cand, prob, msg)
            if emp and not prob:
                mapped_emp_ids.add(emp.id)

        sessions_by_emp_day = defaultdict(list)
        open_issues_by_emp_day = defaultdict(list)
        canonical_lates = {}
        if mapped_emp_ids and s_from and s_to:
            for sess in self.env['tp.hr.attendance.session'].sudo().with_context(active_test=False).search([
                ('company_id', '=', company.id),
                ('employee_id', 'in', list(mapped_emp_ids)),
                ('work_date', '>=', s_from),
                ('work_date', '<=', s_to),
            ]):
                sessions_by_emp_day[sess.employee_id.id, sess.work_date].append(sess)
            for iss in self.env['tp.hr.attendance.line'].sudo().search([
                ('company_id', '=', company.id),
                ('employee_id', 'in', list(mapped_emp_ids)),
                ('work_date', '>=', s_from),
                ('work_date', '<=', s_to),
                ('issue_open', '=', True),
                ('batch_id', '!=', batch.id),
            ]):
                open_issues_by_emp_day[iss.employee_id.id, iss.work_date].append(iss)
            for app_late in self.env['tp.hr.attendance.late'].sudo().search([
                ('company_id', '=', company.id),
                ('employee_id', 'in', list(mapped_emp_ids)),
                ('date_from', '=', s_from),
                ('date_to', '=', s_to),
                ('state', '=', 'applied'),
            ]):
                canonical_lates[app_late.employee_id.id] = app_late

        line_state_labels = dict(LINE_STATES)
        late_state_labels = dict(self.env['tp.hr.attendance.late']._fields['state'].selection)
        group_seen = {}
        people_rows = []

        for p in people_recs:
            emp, cand, prob, msg = resolved_map[p.id]
            if emp and not prob:
                mapping_state = 'mapped'
                mapping_label = 'Đã khớp HR'
            elif prob == 'name_conflict':
                mapping_state = 'name_conflict'
                mapping_label = 'Khác tên HR'
            else:
                mapping_state = 'unmapped'
                mapping_label = 'Chưa map HR'

            grp_key = p.source_group or EMPTY_GROUP_KEY
            grp_label = p.source_group or 'Chưa phân nhóm trong tệp'
            if grp_key not in group_seen:
                group_seen[grp_key] = {'key': grp_key, 'label': grp_label, 'seq': p.group_seq, 'count': 0}
            group_seen[grp_key]['count'] += 1

            # Evaluate cells in day_columns order
            p_cells_map = {c.column_index: c for c in cells_by_person.get(p.id, [])}
            row_cells = []
            for col in day_columns:
                c = p_cells_map.get(col['column'])
                w_date = fields.Date.from_string(col['date'])
                if not c or c.kind == 'empty':
                    status = 'empty'
                    explanation = ''
                else:
                    line = lines_by_coord.get((p.in_row_number, col['column']))
                    is_locked = Period._tp_is_locked(company.id, w_date, locked_ranges)
                    if line and line.session_id and not line.session_id.active:
                        status = 'conflict'
                        explanation = line.message or 'Nguồn lịch sử đã được thay thế; xem dữ liệu hiệu lực trong Đối chiếu.'
                    elif line and line.state == 'applied' and line.session_id.active:
                        status = 'applied'
                        explanation = line.message or 'Đã ghi nhận vào bảng công.'
                    elif mapping_state != 'mapped':
                        status = mapping_state
                        explanation = msg
                    elif is_locked:
                        status = 'locked'
                        explanation = 'Kỳ công đã chốt; cần đính chính có duyệt.'
                    else:
                        # Live evaluation against current canonical sessions
                        day_sessions = sessions_by_emp_day.get((emp.id, w_date), [])
                        active_sessions = [s for s in day_sessions if s.active]
                        if c.kind == 'pair':
                            if any(s.check_in == c.check_in and s.check_out == c.check_out for s in day_sessions):
                                status = 'duplicate'
                                explanation = 'Giờ Vào/Ra trùng với phiên đã ghi nhận (chỉ tính một lần).'
                            elif active_sessions or open_issues_by_emp_day.get((emp.id, w_date)):
                                status = 'conflict'
                                explanation = 'Cùng ngày đang có giờ khác trên bảng công; chờ đối chiếu chọn nguồn.'
                            else:
                                status = 'valid'
                                explanation = 'Dòng mới hợp lệ, sẵn sàng áp dụng.'
                        else:
                            if line and active_sessions and any(consistent(line, s.check_in, s.check_out) for s in active_sessions):
                                status = 'duplicate'
                                explanation = 'Giờ đơn lẻ đã nằm trong phiên đủ Vào/Ra đang áp dụng.'
                            elif active_sessions or open_issues_by_emp_day.get((emp.id, w_date)):
                                status = 'conflict'
                                explanation = 'Cùng ngày đã có dữ liệu khác; cần kiểm tra đối chiếu.'
                            elif c.kind in ('missing_in', 'missing_out'):
                                status = 'missing'
                                explanation = KIND_MESSAGES.get(c.kind, '')
                            else:
                                status = 'review'
                                explanation = KIND_MESSAGES.get(c.kind, '')

                status_title, badge = CELL_STATUS_META.get(status, (line_state_labels.get(status, status), status))
                row_cells.append({
                    'column': col['column'],
                    'date': col['date'],
                    'cell_ref': c.cell_ref if c else '',
                    'kind': c.kind if c else 'empty',
                    'raw_in': c.raw_in if c else '',
                    'raw_out': c.raw_out if c else '',
                    'norm_in': c.norm_in if c else '',
                    'norm_out': c.norm_out if c else '',
                    'status': status,
                    'status_label': status_title,
                    'badge': badge,
                    'message': explanation,
                })

            # Evaluate period-level late total
            late_rec = lates_by_row.get(p.in_row_number)
            late_status = 'none'
            late_msg = ''
            if p.late_source_state == 'no_column':
                late_status = 'no_column'
            elif late_rec and late_rec.state in ('applied', 'superseded'):
                late_status = late_rec.state
                late_msg = late_rec.message or late_rec.supersede_reason or ''
            elif mapping_state != 'mapped':
                late_status = mapping_state
                late_msg = msg
            elif p.late_source_state in ('empty', 'invalid'):
                late_status = 'missing'
                late_msg = late_rec.message if late_rec else 'Chưa có số liệu đi muộn hợp lệ.'
            elif p.late_source_state == 'inconsistent':
                late_status = 'review'
                late_msg = late_rec.message if late_rec else 'Số lần và số phút lệch nhau (một bên bằng 0).'
            elif s_from and s_to and any(s_from <= end and s_to >= start for start, end in locked_ranges.get(company.id, [])):
                late_status = 'locked'
                late_msg = 'Kỳ công đã chốt.'
            elif emp.id in canonical_lates:
                can_late = canonical_lates[emp.id]
                if (can_late.late_count, can_late.late_minutes) == (p.late_count, p.late_minutes):
                    late_status = 'applied' if can_late.batch_id.id == batch.id else 'duplicate'
                    late_msg = 'Đang áp dụng' if late_status == 'applied' else 'Cùng số liệu với bản đang áp dụng.'
                else:
                    late_status = 'conflict'
                    late_msg = f'Đang áp dụng {can_late.late_count} lần / {can_late.late_minutes} phút; cần đối chiếu chọn nguồn.'
            else:
                late_status = 'valid'

            people_rows.append({
                'snapshot_person_id': p.id,
                'person_seq': p.person_seq,
                'stt': p.stt_raw or str(p.person_seq),
                'in_row': p.in_row_number,
                'out_row': p.out_row_number,
                'raw_source_code': p.raw_source_code or '',
                'raw_machine_code': p.raw_machine_code or p.machine_code or '',
                'machine_code': p.machine_code or '',
                'source_name': p.source_name or '',
                'source_title': p.source_title or '',
                'source_group': p.source_group or '',
                'group_key': grp_key,
                'group_label': grp_label,
                'group_seq': p.group_seq,
                'employee_id': emp.id if (emp and not prob) else 0,
                'candidate_hr_name': cand.name if cand else '',
                'hr_code': emp.tp_employee_code if (emp and not prob) else '',
                'hr_name': emp.name if (emp and not prob) else '',
                'hr_department': emp.department_id.name if (emp and not prob and emp.department_id) else '',
                'mapping_state': mapping_state,
                'mapping_label': mapping_label,
                'mapping_message': msg or '',
                'cells': row_cells,
                'late': {
                    'source_state': p.late_source_state,
                    'count': p.late_count if p.late_source_state in ('ok', 'inconsistent') else None,
                    'minutes': p.late_minutes if p.late_source_state in ('ok', 'inconsistent') else None,
                    'raw_count': p.late_raw_count or '',
                    'raw_minutes': p.late_raw_minutes or '',
                    'cell_ref': p.late_cell_ref or '',
                    'status': late_status,
                    'status_label': late_state_labels.get(late_status, late_status),
                    'message': late_msg,
                },
                'absent': {
                    'source_state': p.absent_source_state,
                    'raw': p.absent_raw or '',
                    'cell_ref': p.absent_cell_ref or '',
                },
            })

        return {
            'sheet_index': sheet_index,
            'sheet_name': sh.get('name') or f'Sheet {sheet_index + 1}',
            'from': sh.get('from') or '',
            'to': sh.get('to') or '',
            'period_label': short_range(s_from, s_to) if s_from and s_to else '',
            'period_full': f'{_fmt_date(s_from)} – {_fmt_date(s_to)}' if s_from and s_to else '',
            'errors': sh.get('errors') or [],
            'day_columns': day_columns,
            'people': people_rows,
            'group_options': list(group_seen.values()),
            'has_late': (sh.get('late') or {}).get('state') == 'ok',
            'late_info': sh.get('late') or {},
            'has_absent': (sh.get('absent') or {}).get('state') == 'ok',
        }

    @staticmethod
    def _tp_person_matches_status(person, visible_cells, statuses):
        """OR across selected status criteria for one employee within the active date window."""
        wanted = set(statuses)
        if not wanted:
            return True
        cell_states = {c['status'] for c in visible_cells}
        late_state = person['late']['status']
        if 'new' in wanted and ('valid' in cell_states or late_state == 'valid'):
            return True
        if 'applied' in wanted and ('applied' in cell_states or late_state == 'applied'):
            return True
        if 'duplicate' in wanted and ('duplicate' in cell_states or late_state == 'duplicate'):
            return True
        if 'conflict' in wanted and ('conflict' in cell_states or late_state == 'conflict'):
            return True
        if 'missing' in wanted and 'missing' in cell_states:
            return True
        if 'review' in wanted and ('review' in cell_states or late_state == 'review'):
            return True
        if 'unmapped' in wanted and person['mapping_state'] in ('unmapped', 'name_conflict'):
            return True
        if 'locked' in wanted and ('locked' in cell_states or late_state == 'locked'):
            return True
        return bool('all_empty' in wanted and visible_cells and all(c['kind'] == 'empty' for c in visible_cells))

    def _tp_filter_matrix(self, evaluated, params, paginate=True):
        """Apply DEC-044 server-side filters, build active chips, compute counts and paginate by employee."""
        d_from = _parse_iso_date(params.get('date_from'))
        d_to = _parse_iso_date(params.get('date_to'))
        if d_from and d_to and d_to < d_from:
            raise UserError(self.env._('Ngày kết thúc lọc phải sau hoặc bằng ngày bắt đầu.'))

        sheet_from = _parse_iso_date(evaluated['from']) if evaluated['from'] else None
        sheet_to = _parse_iso_date(evaluated['to']) if evaluated['to'] else None
        day_columns = evaluated['day_columns']
        if d_from:
            day_columns = [col for col in day_columns if fields.Date.from_string(col['date']) >= d_from]
        if d_to:
            day_columns = [col for col in day_columns if fields.Date.from_string(col['date']) <= d_to]
        visible_col_set = {col['column'] for col in day_columns}
        is_sub_range = bool(
            (d_from and sheet_from and d_from > sheet_from)
            or (d_to and sheet_to and d_to < sheet_to),
        )

        source_group = str(params.get('source_group') or '').strip()
        search_raw = str(params.get('search') or '').strip()
        search_fold = fold(search_raw)
        raw_status = params.get('status') or ''
        if isinstance(raw_status, str):
            statuses = [s.strip() for s in raw_status.split(',') if s.strip()]
        elif isinstance(raw_status, list):
            statuses = [str(s).strip() for s in raw_status if str(s).strip()]
        else:
            statuses = []
        valid_status_keys = {k for k, _lbl in FILTER_STATUS_OPTIONS}
        statuses = [s for s in statuses if s in valid_status_keys]

        matched = []
        summary_counts = {
            'employees': 0, 'mapped': 0, 'unmapped': 0, 'all_empty': 0,
            'valid': 0, 'applied': 0, 'duplicate': 0, 'conflict': 0, 'missing': 0, 'review': 0, 'locked': 0, 'empty_cells': 0,
        }

        for person in evaluated['people']:
            if source_group and person['group_key'] != source_group:
                continue
            if search_fold:
                haystack = ' '.join([
                    fold(person['source_name']),
                    fold(person['raw_source_code']),
                    fold(person['machine_code']),
                    fold(person['raw_machine_code']),
                    fold(person['hr_code']),
                    fold(person['hr_name']),
                ])
                if search_fold not in haystack:
                    continue
            visible_cells = [c for c in person['cells'] if c['column'] in visible_col_set]
            if statuses and not self._tp_person_matches_status(person, visible_cells, statuses):
                continue

            item = dict(person, cells=visible_cells, all_empty=bool(visible_cells) and all(c['kind'] == 'empty' for c in visible_cells))
            matched.append(item)
            summary_counts['employees'] += 1
            if item['mapping_state'] == 'mapped':
                summary_counts['mapped'] += 1
            else:
                summary_counts['unmapped'] += 1
            if item['all_empty']:
                summary_counts['all_empty'] += 1
            for c in visible_cells:
                st = c['status']
                if st == 'empty':
                    summary_counts['empty_cells'] += 1
                elif st in summary_counts:
                    summary_counts[st] += 1

        size = int(params.get('page_size') or 20)
        size = size if size in MATRIX_PAGE_SIZES else 20
        total = len(matched)
        page_count = max(1, -(-total // size))
        page = min(max(1, int(params.get('page') or 1)), page_count)
        sliced = matched[(page - 1) * size: page * size] if paginate else matched

        # Group consecutive/same-group employees into source unit bands without counting bands as employees
        groups = []
        by_group = {}
        for person in sliced:
            gkey = person['group_key']
            if gkey not in by_group:
                band = {
                    'key': gkey,
                    'label': person['group_label'],
                    'seq': person['group_seq'],
                    'people': [],
                }
                by_group[gkey] = band
                groups.append(band)
            by_group[gkey]['people'].append(person)

        # Build applied filter chips for UI (DEC-044)
        status_map = dict(FILTER_STATUS_OPTIONS)
        group_map = {g['key']: g['label'] for g in evaluated['group_options']}
        chips = []
        if d_from or d_to:
            chips.append({
                'key': 'date_range',
                'label': f"Ngày: {_fmt_short_day(d_from or sheet_from)}–{_fmt_short_day(d_to or sheet_to)}",
            })
        if source_group:
            chips.append({
                'key': 'source_group',
                'label': f"Đơn vị (tệp): {group_map.get(source_group, source_group)}",
            })
        if search_raw:
            chips.append({'key': 'search', 'label': f'Tìm: "{search_raw}"'})
        for st in statuses:
            chips.append({'key': f'status:{st}', 'label': f"Tình trạng: {status_map.get(st, st)}"})

        return {
            'day_columns': day_columns,
            'is_sub_range': is_sub_range,
            'rows': sliced,
            'groups': groups,
            'summary': summary_counts,
            'chips': chips,
            'applied_filters': {
                'date_from': d_from.isoformat() if d_from else '',
                'date_to': d_to.isoformat() if d_to else '',
                'source_group': source_group,
                'search': search_raw,
                'status': statuses,
            },
            'total': total,
            'page': page,
            'page_size': size,
            'page_count': page_count,
        }

    @api.model
    def tp_matrix_data(self, params=None):
        """Full matrix payload for one source batch + sheet with DEC-044 filtering & employee pagination."""
        params = dict(params or {})
        company = self.env.company
        require(self.env, 'import', company)
        self.check_access('read')

        include_cancelled = bool(params.get('include_cancelled'))
        batch_domain = [('company_id', '=', company.id), ('state', '!=', 'draft')]
        if not include_cancelled:
            batch_domain.append(('state', '!=', 'cancelled'))
        batches = self.search(batch_domain, order='id desc', limit=200)

        requested_id = int(params.get('batch_id') or 0)
        selected = self.browse()
        if requested_id:
            selected = self._tp_accessible_batch(requested_id)
            if selected not in batches:
                batches = selected | batches
        elif batches:
            selected = batches[0]

        selector_items = [b._tp_batch_selector_item() for b in batches]
        ref_hours = (self.env['ir.config_parameter'].sudo().get_str('tp_hr_attendance.reference_hours') or '08:30-17:00')
        if not selected:
            return {
                'has_batches': False,
                'batches': selector_items,
                'batch': None,
                'status_options': [{'key': k, 'label': lbl} for k, lbl in FILTER_STATUS_OPTIONS],
                'reference_hours': ref_hours,
                'can_import': True,
                'can_export': True,
            }

        # Ensure snapshot exists if a batch was created via legacy form flow without snapshot
        if selected.sudo().snapshot_state == 'pending':
            selected._tp_build_snapshot()

        batch_info = selected._tp_batch_selector_item()
        evaluated = selected._tp_evaluate_sheet_matrix(sheet_index=params.get('sheet_index', 0))
        filtered = selected._tp_filter_matrix(evaluated, params, paginate=True)

        return {
            'has_batches': True,
            'batches': selector_items,
            'batch': batch_info,
            'sheet': {
                'index': evaluated['sheet_index'],
                'name': evaluated['sheet_name'],
                'from': evaluated['from'],
                'to': evaluated['to'],
                'period_label': evaluated['period_label'],
                'period_full': evaluated['period_full'],
                'errors': evaluated['errors'],
                'has_late': evaluated['has_late'],
                'late_info': evaluated['late_info'],
                'has_absent': evaluated['has_absent'],
                'total_in_sheet': len(evaluated['people']),
            },
            'group_options': evaluated['group_options'],
            'status_options': [{'key': k, 'label': lbl} for k, lbl in FILTER_STATUS_OPTIONS],
            'reference_hours': ref_hours,
            'can_import': True,
            'can_export': True,
            **filtered,
        }

    # --------------------------------------------------- faithful Excel export
    @api.model
    def tp_export_matrix(self, params=None):
        """Export the currently filtered source file matrix (2 rows Vào/Ra per employee, formula-safe)."""
        params = dict(params or {})
        batch = self._tp_accessible_batch(params.get('batch_id'))
        if batch.sudo().snapshot_state == 'pending':
            batch._tp_build_snapshot()
        batch_info = batch._tp_batch_selector_item()
        evaluated = batch._tp_evaluate_sheet_matrix(sheet_index=params.get('sheet_index', 0))
        filtered = batch._tp_filter_matrix(evaluated, params, paginate=False)

        show_machine_id = bool(params.get('show_machine_id'))
        show_title = bool(params.get('show_title'))
        show_hr_code = bool(params.get('show_hr_code'))
        show_absent = bool(params.get('show_absent')) and evaluated['has_absent']

        wb = Workbook()
        ws = wb.active
        ws.title = (evaluated['sheet_name'] or 'Bang theo file')[:31]

        bold_font = Font(bold=True, color='17324D')
        head_fill = PatternFill('solid', fgColor='EAF2FB')
        group_fill = PatternFill('solid', fgColor='F1F5F9')
        weekend_fill = PatternFill('solid', fgColor='FAFBFD')
        thin = Side(border_style='thin', color='D7E2EF')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        center = Alignment(horizontal='center', vertical='center', wrap_text=True)
        left_align = Alignment(horizontal='left', vertical='center', wrap_text=True)

        stamp = self._tp_stamp(fields.Datetime.now())
        range_note = (
            f"Khoảng lọc ngày: {_fmt_date(filtered['applied_filters']['date_from'] or evaluated['from'])} – "
            f"{_fmt_date(filtered['applied_filters']['date_to'] or evaluated['to'])}"
            if filtered['is_sub_range'] else f"Kỳ nguồn đầy đủ: {evaluated['period_full']}"
        )
        ws.append([xlsx_safe(
            f"BẢNG CÔNG THEO TỆP NGUỒN · {batch_info['batch_code']} · Tệp: {batch_info['file_name'] or batch_info['name']} · "
            f"Trang: {evaluated['sheet_name']} · {batch_info['state_label']}",
        )])
        ws.append([xlsx_safe(
            f"{range_note} · Đi muộn Lần/Phút là tổng cả kỳ nguồn {evaluated['period_label']} theo Excel máy (không chia ngày) · "
            f"Số nhân viên khớp lọc: {filtered['total']}/{len(evaluated['people'])} · Xuất lúc {stamp}",
        )])
        ws.cell(1, 1).font = Font(bold=True, size=12, color='17324D')
        ws.cell(2, 1).font = Font(italic=True, size=10, color='546A82')

        # Build 2-tier header starting at row 4
        fixed_cols = [('STT', 6), ('Mã NV (Excel)', 14)]
        if show_hr_code:
            fixed_cols.append(('Mã HR', 12))
        fixed_cols.append(('Tên nhân viên (nguồn)', 26))
        if show_machine_id:
            fixed_cols.append(('ID máy', 10))
        if show_title:
            fixed_cols.append(('Chức vụ (nguồn)', 18))
        fixed_cols.append(('Vào/Ra', 9))

        h_row1 = 4
        h_row2 = 5
        col_cursor = 1
        for title, width in fixed_cols:
            ws.cell(h_row1, col_cursor, xlsx_safe(title))
            ws.merge_cells(start_row=h_row1, start_column=col_cursor, end_row=h_row2, end_column=col_cursor)
            ws.column_dimensions[get_column_letter(col_cursor)].width = width
            col_cursor += 1

        day_start_col = col_cursor
        for dcol in filtered['day_columns']:
            ws.cell(h_row1, col_cursor, xlsx_safe(dcol['day_month']))
            ws.cell(h_row2, col_cursor, xlsx_safe(dcol['weekday']))
            ws.column_dimensions[get_column_letter(col_cursor)].width = 8
            col_cursor += 1

        late_col = None
        if evaluated['has_late']:
            late_col = col_cursor
            late_title = f"Đi muộn (kỳ {evaluated['period_label']})"
            ws.cell(h_row1, col_cursor, xlsx_safe(late_title))
            ws.merge_cells(start_row=h_row1, start_column=col_cursor, end_row=h_row1, end_column=col_cursor + 1)
            ws.cell(h_row2, col_cursor, 'Lần')
            ws.cell(h_row2, col_cursor + 1, 'Phút')
            ws.column_dimensions[get_column_letter(col_cursor)].width = 9
            ws.column_dimensions[get_column_letter(col_cursor + 1)].width = 10
            col_cursor += 2

        absent_col = None
        if show_absent:
            absent_col = col_cursor
            ws.cell(h_row1, col_cursor, 'Vắng mặt (Excel kỳ)')
            ws.merge_cells(start_row=h_row1, start_column=col_cursor, end_row=h_row2, end_column=col_cursor)
            ws.column_dimensions[get_column_letter(col_cursor)].width = 14
            col_cursor += 1

        status_col = col_cursor
        ws.cell(h_row1, col_cursor, 'Đối chiếu HR')
        ws.merge_cells(start_row=h_row1, start_column=col_cursor, end_row=h_row2, end_column=col_cursor)
        ws.column_dimensions[get_column_letter(col_cursor)].width = 16
        total_cols = col_cursor

        for r in (h_row1, h_row2):
            for c in range(1, total_cols + 1):
                cell = ws.cell(r, c)
                cell.font = bold_font
                cell.fill = head_fill
                cell.border = border
                cell.alignment = center

        row_cursor = 6
        for group in filtered['groups']:
            ws.cell(row_cursor, 1, xlsx_safe(f"{group['label']} ({len(group['people'])} nhân viên)"))
            ws.merge_cells(start_row=row_cursor, start_column=1, end_row=row_cursor, end_column=total_cols)
            for c in range(1, total_cols + 1):
                gcell = ws.cell(row_cursor, c)
                gcell.font = bold_font
                gcell.fill = group_fill
                gcell.border = border
                gcell.alignment = left_align
            row_cursor += 1

            for person in group['people']:
                r_in = row_cursor
                r_out = row_cursor + 1
                id_values = [person['stt'], person['raw_source_code']]
                if show_hr_code:
                    id_values.append(person['hr_code'] or '—')
                id_values.append(person['source_name'])
                if show_machine_id:
                    id_values.append(person['raw_machine_code'])
                if show_title:
                    id_values.append(person['source_title'])

                for offset, val in enumerate(id_values, 1):
                    ws.cell(r_in, offset, xlsx_safe(val))
                    ws.merge_cells(start_row=r_in, start_column=offset, end_row=r_out, end_column=offset)

                inout_col = len(id_values) + 1
                ws.cell(r_in, inout_col, 'Vào')
                ws.cell(r_out, inout_col, 'Ra')

                for d_idx, cell_data in enumerate(person['cells']):
                    c_idx = day_start_col + d_idx
                    ws.cell(r_in, c_idx, xlsx_safe(cell_data['raw_in']))
                    ws.cell(r_out, c_idx, xlsx_safe(cell_data['raw_out']))
                    if filtered['day_columns'][d_idx]['weekend']:
                        ws.cell(r_in, c_idx).fill = weekend_fill
                        ws.cell(r_out, c_idx).fill = weekend_fill

                if late_col:
                    late = person['late']
                    c_val = late['count'] if late['count'] is not None else (late['raw_count'] or '')
                    m_val = late['minutes'] if late['minutes'] is not None else (late['raw_minutes'] or '')
                    ws.cell(r_in, late_col, xlsx_safe(c_val))
                    ws.cell(r_in, late_col + 1, xlsx_safe(m_val))
                    ws.merge_cells(start_row=r_in, start_column=late_col, end_row=r_out, end_column=late_col)
                    ws.merge_cells(start_row=r_in, start_column=late_col + 1, end_row=r_out, end_column=late_col + 1)

                if absent_col:
                    ws.cell(r_in, absent_col, xlsx_safe(person['absent']['raw']))
                    ws.merge_cells(start_row=r_in, start_column=absent_col, end_row=r_out, end_column=absent_col)

                ws.cell(r_in, status_col, xlsx_safe(person['mapping_label']))
                ws.merge_cells(start_row=r_in, start_column=status_col, end_row=r_out, end_column=status_col)

                for r in (r_in, r_out):
                    for c in range(1, total_cols + 1):
                        cell = ws.cell(r, c)
                        cell.border = border
                        cell.alignment = left_align if c <= len(id_values) and c > 1 else center
                row_cursor += 2

        stream = BytesIO()
        wb.save(stream)
        safe_code = (batch_info['batch_code'] or f"lo-{batch.id}").lower().replace(' ', '-')
        filename = f"bang-cong-nguon-{safe_code}-sheet{evaluated['sheet_index'] + 1}.xlsx"
        self.env['tp.hr.attendance.log']._tp_log(batch, 'matrix_export', {
            'sheet_index': evaluated['sheet_index'], 'employees': filtered['total'],
        })
        return {
            'filename': filename,
            'data': base64.b64encode(stream.getvalue()).decode(),
        }


def _tp_migrate_matrix_003(env):
    """Idempotent backfill of batch codes, multi-source provenance links and immutable file snapshots.

    Never re-imports or alters canonical sessions, day summaries, approved corrections, period locks or HR rows.
    """
    Batch = env['tp.hr.attendance.batch'].sudo()
    Session = internal(env['tp.hr.attendance.session']).with_context(active_test=False)
    Line = env['tp.hr.attendance.line'].sudo()
    Late = internal(env['tp.hr.attendance.late'])

    for batch in Batch.search([], order='id'):
        vals = {}
        if not batch.batch_code:
            vals['batch_code'] = f'LÔ-{batch.id:05d}'
        if not batch.source_namespace:
            vals['source_namespace'] = 'excel-machine'
        if vals:
            internal(batch).write(vals)
        if batch.state != 'draft' and batch.snapshot_version < PARSER_VERSION:
            batch._tp_build_snapshot()
        if batch.state == 'applied' and (batch.conflict_count or batch.late_conflict_count):
            internal(batch).write({'state': 'partial'})

    # Backfill provenance M2M on existing sessions and applied late records without altering values
    for sess in Session.search([('batch_id', '!=', False)]):
        add_batches = {sess.batch_id.id}
        add_lines = {sess.line_id.id} if sess.line_id else set()
        dup_lines = Line.search([
            ('employee_id', '=', sess.employee_id.id),
            ('work_date', '=', sess.work_date),
            ('kind', '=', 'pair'),
            ('check_in', '=', sess.check_in),
            ('check_out', '=', sess.check_out),
            ('batch_id.state', 'in', ('applied', 'partial')),
        ])
        for dl in dup_lines:
            add_batches.add(dl.batch_id.id)
            add_lines.add(dl.id)
            if not dl.session_id:
                internal(dl).write({'session_id': sess.id})
        missing_b = add_batches - set(sess.source_batch_ids.ids)
        missing_l = add_lines - set(sess.source_line_ids.ids)
        if missing_b or missing_l:
            sess.write({
                'source_batch_ids': [(4, bid) for bid in sorted(missing_b)],
                'source_line_ids': [(4, lid) for lid in sorted(missing_l)],
            })

    for app_late in Late.search([('state', '=', 'applied')]):
        add_batches = {app_late.batch_id.id}
        dup_lates = Late.search([
            ('company_id', '=', app_late.company_id.id),
            ('employee_id', '=', app_late.employee_id.id),
            ('date_from', '=', app_late.date_from),
            ('date_to', '=', app_late.date_to),
            ('state', '=', 'duplicate'),
            ('late_count', '=', app_late.late_count),
            ('late_minutes', '=', app_late.late_minutes),
            ('batch_id.state', 'in', ('applied', 'partial')),
        ])
        for dl in dup_lates:
            add_batches.add(dl.batch_id.id)
            if not dl.canonical_late_id:
                dl.write({'canonical_late_id': app_late.id})
        missing_b = add_batches - set(app_late.source_batch_ids.ids)
        if missing_b:
            app_late.write({'source_batch_ids': [(4, bid) for bid in sorted(missing_b)]})
