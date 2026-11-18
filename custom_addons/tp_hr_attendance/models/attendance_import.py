"""Preview → apply import of the machine attendance report; duplicates and conflicts never overwrite.

HR-ATTENDANCE-SIMPLE-002 adds the drag-and-drop upload RPCs on top of the same batch flow and stores the
machine "Đi muộn" totals of each source period (``tp.hr.attendance.late``) next to the day punches.
"""
import hashlib
from collections import defaultdict

from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .attendance_common import (
    DEFAULT_TZ,
    can,
    deny_direct,
    fold,
    internal,
    is_internal,
    local_to_utc,
    require,
)
from .attendance_logic import dates_between, short_range
from .attendance_parser import AttendanceFormatError, parse_attendance

ADVISORY_KEY = 761120
KINDS = [
    ('pair', 'Đủ giờ vào - ra'), ('missing_out', 'Thiếu giờ ra'), ('missing_in', 'Thiếu giờ vào'),
    ('reversed', 'Giờ ra trước giờ vào'), ('code', 'Ký hiệu thay giờ'), ('merged', 'Ô Vào/Ra bị gộp'),
    ('multi', 'Nhiều mốc giờ trong một ô'), ('invalid', 'Không đọc được'),
]
LINE_STATES = [
    ('valid', 'Hợp lệ, sẽ ghi nhận'), ('duplicate', 'Trùng, bỏ qua'), ('conflict', 'Xung đột, chờ điều chỉnh'),
    ('unmapped', 'Chưa đối chiếu được nhân viên'), ('name_conflict', 'Mã máy khớp nhưng tên khác'),
    ('missing', 'Thiếu giờ vào/ra'), ('review', 'Cần kiểm tra'), ('locked', 'Kỳ đã chốt'), ('applied', 'Đã ghi nhận'),
]
KIND_MESSAGES = {
    'missing_out': 'Thiếu giờ ra.', 'missing_in': 'Thiếu giờ vào.', 'reversed': 'Giờ ra trước giờ vào.',
    'code': 'Ô có ký hiệu thay cho giờ; cần HR xác nhận.', 'merged': 'Ô Vào/Ra bị gộp; cần kiểm tra.',
    'multi': 'Một ô có nhiều mốc giờ.', 'invalid': 'Giá trị không đọc được.',
}
ISSUE_STATES = ('missing', 'review', 'conflict')
COUNTED = ('valid', 'duplicate', 'conflict', 'unmapped', 'name_conflict', 'missing', 'review', 'locked', 'applied')
LATE_COUNTED = ('valid', 'duplicate', 'conflict', 'unmapped', 'name_conflict', 'missing', 'review', 'locked', 'applied')
LATE_MESSAGES = {
    'empty': 'Ô Đi muộn trống: Chưa có số liệu, không coi là 0.',
    'invalid': 'Số đi muộn không phải số nguyên không âm (hoặc thiếu Lần/Phút): Chưa có số liệu.',
    'inconsistent': 'Lần và Phút không khớp nhau (một bên 0); giữ số nguồn, cần HR xem lại.',
}
PREVIEW_ATTENTION = 60
UPLOAD_MAX_B64 = 20 * 1024 * 1024  # ≈ 15 MB of .xlsx once base64-encoded


def signature(employee_id, work_date, kind, check_in=None, check_out=None, raw_in='', raw_out=''):
    if kind == 'pair':
        return f'{employee_id}|{work_date}|pair|{check_in}|{check_out}'
    return f'{employee_id}|{work_date}|{kind}|{raw_in or ""}|{raw_out or ""}'


def fmt(iso_date):
    return f'{iso_date[8:10]}/{iso_date[5:7]}/{iso_date[:4]}' if iso_date else ''


def consistent(line, check_in, check_out):
    """A half-punch agrees with a full pair when its known side is the same instant."""
    if line.kind == 'missing_out':
        return line.check_in == check_in
    if line.kind == 'missing_in':
        return line.check_out == check_out
    return False


class AttendanceBatch(models.Model):
    _name = 'tp.hr.attendance.batch'
    _description = 'Lô nhập dữ liệu công'
    _order = 'id desc'
    _check_company_auto = True

    name = fields.Char('Tên lô', default='Nhập báo cáo máy chấm công', required=True)
    company_id = fields.Many2one('res.company', 'Công ty', required=True, default=lambda self: self.env.company)
    file_data = fields.Binary('Tệp Excel (.xlsx)', attachment=True)
    file_name = fields.Char('Tên tệp')
    checksum = fields.Char('Mã băm tệp', readonly=True, copy=False)
    same_file_batch_id = fields.Many2one('tp.hr.attendance.batch', 'Tệp đã nhập ở lô', readonly=True, copy=False)
    tz = fields.Char('Múi giờ', default=DEFAULT_TZ, readonly=True)
    batch_code = fields.Char('Mã lô', readonly=True, copy=False, index=True)
    source_namespace = fields.Char('Không gian nguồn', default='excel-machine', readonly=True, copy=False)
    state = fields.Selection([
        ('draft', 'Chọn tệp'),
        ('preview', 'Đã đọc/Lưu nguồn – Chưa áp dụng'),
        ('partial', 'Đã áp dụng một phần – Còn khác biệt'),
        ('applied', 'Đã áp dụng vào bảng tổng hợp'),
        ('cancelled', 'Đã bỏ qua nguồn'),
    ], 'Trạng thái', default='draft', readonly=True, required=True, index=True)
    snapshot_version = fields.Integer('Phiên bản snapshot nguồn', default=0, readonly=True, copy=False)
    snapshot_state = fields.Selection([
        ('pending', 'Chưa tạo'),
        ('ready', 'Đầy đủ nguồn'),
        ('unavailable', 'Thiếu tệp gốc'),
    ], 'Trạng thái snapshot', default='pending', readonly=True, copy=False)
    snapshot_note = fields.Char('Ghi chú snapshot', readonly=True, copy=False)
    cancel_reason = fields.Char('Lý do bỏ qua nguồn', readonly=True, copy=False)
    cancelled_by = fields.Many2one('res.users', 'Người bỏ qua', readonly=True, copy=False)
    cancelled_at = fields.Datetime('Thời điểm bỏ qua', readonly=True, copy=False)
    sheet_summary = fields.Json('Tóm tắt trang', readonly=True, copy=False)
    period_from = fields.Date('Từ ngày', readonly=True)
    period_to = fields.Date('Đến ngày', readonly=True)
    employee_ids = fields.Many2many('hr.employee', string='Nhân viên có trong tệp', readonly=True, copy=False)
    line_ids = fields.One2many('tp.hr.attendance.line', 'batch_id', 'Dòng xem trước', readonly=True)
    attention_line_ids = fields.One2many('tp.hr.attendance.line', 'batch_id', 'Dòng cần chú ý', readonly=True,
                                         domain=[('state', 'not in', ('valid', 'applied', 'duplicate'))])
    line_count = fields.Integer('Dòng dữ liệu', readonly=True)
    valid_count = fields.Integer('Hợp lệ', readonly=True)
    duplicate_count = fields.Integer('Trùng', readonly=True)
    conflict_count = fields.Integer('Xung đột', readonly=True)
    unmapped_count = fields.Integer('Chưa đối chiếu', readonly=True)
    name_conflict_count = fields.Integer('Tên khác hồ sơ', readonly=True)
    missing_count = fields.Integer('Thiếu giờ', readonly=True)
    review_count = fields.Integer('Cần kiểm tra', readonly=True)
    locked_count = fields.Integer('Kỳ đã chốt', readonly=True)
    applied_count = fields.Integer('Đã ghi nhận', readonly=True)
    empty_count = fields.Integer('Ô trống', readonly=True)
    late_ids = fields.One2many('tp.hr.attendance.late', 'batch_id', 'Tổng đi muộn theo kỳ', readonly=True)
    late_valid_count = fields.Integer('Tổng muộn hợp lệ', readonly=True)
    late_duplicate_count = fields.Integer('Tổng muộn trùng', readonly=True)
    late_conflict_count = fields.Integer('Tổng muộn xung đột', readonly=True)
    late_unmapped_count = fields.Integer('Tổng muộn chưa đối chiếu', readonly=True)
    late_name_conflict_count = fields.Integer('Tổng muộn tên khác hồ sơ', readonly=True)
    late_missing_count = fields.Integer('Tổng muộn chưa có số liệu', readonly=True)
    late_review_count = fields.Integer('Tổng muộn cần kiểm tra', readonly=True)
    late_locked_count = fields.Integer('Tổng muộn kỳ đã chốt', readonly=True)
    late_applied_count = fields.Integer('Tổng muộn đã ghi nhận', readonly=True)
    applied_by = fields.Many2one('res.users', 'Người áp dụng', readonly=True)
    applied_at = fields.Datetime('Thời điểm áp dụng', readonly=True)
    result = fields.Text('Kết quả', readonly=True)
    summary_html = fields.Html('Theo trang tính', compute='_compute_summary_html', sanitize=False)

    _SYSTEM_FIELDS = {'batch_code', 'source_namespace', 'checksum', 'same_file_batch_id', 'tz', 'state', 'sheet_summary',
                      'snapshot_version', 'snapshot_state', 'snapshot_note', 'cancel_reason', 'cancelled_by', 'cancelled_at',
                      'period_from', 'period_to', 'employee_ids',
                      'line_ids', 'attention_line_ids', 'applied_by', 'applied_at', 'result', 'line_count', 'empty_count',
                      'late_ids'} | {f'{s}_count' for s in COUNTED} | {f'late_{s}_count' for s in LATE_COUNTED}

    @api.depends('sheet_summary')
    def _compute_summary_html(self):
        head = Markup('<table class="table table-sm o_tp_att_sheet_summary"><thead><tr><th>Trang</th><th>Từ ngày</th><th>Đến ngày</th>'
                      '<th>Nhân viên</th><th>Mốc dữ liệu</th><th>Ô trống</th><th>Ghi chú</th></tr></thead><tbody>')
        for batch in self:
            rows = []
            for sheet in batch.sheet_summary or []:
                errors = '; '.join(sheet.get('errors') or []) or 'Đọc đủ'
                cells = [sheet.get('name'), fmt(sheet.get('from')), fmt(sheet.get('to')), sheet.get('employees'), sheet.get('events'),
                         sheet.get('empty'), errors]
                rows.append(Markup('<tr>%s</tr>') % Markup('').join(Markup('<td>%s</td>') % escape(cell if cell is not None else '') for cell in cells))
            batch.summary_html = head + Markup('').join(rows) + Markup('</tbody></table>') if rows else False

    # ------------------------------------------------------------- guards
    @api.model
    def _tp_can_import(self, company=None):
        return can(self.env, 'import', company or self.env.company)

    def _tp_require(self):
        for company in self.company_id or self.env.company:
            require(self.env, 'import', company)

    def check_access(self, operation):
        if not self.env.su:
            require(self.env, 'import', self.env.company)
            for company in self.sudo().company_id:
                require(self.env, 'import', company)
        return super().check_access(operation)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if set(vals) & self._SYSTEM_FIELDS:
                raise AccessError(self.env._('Kết quả nhập chỉ được hệ thống cập nhật.'))
            company = self.env['res.company'].browse(vals.get('company_id')) if vals.get('company_id') else self.env.company
            require(self.env, 'import', company)
        records = super().create(vals_list)
        for batch in records:
            if not batch.batch_code:
                internal(batch).write({'batch_code': f'LÔ-{batch.id:05d}'})
        return records

    def write(self, vals):
        if not is_internal(self):
            if set(vals) & self._SYSTEM_FIELDS:
                raise AccessError(self.env._('Kết quả nhập chỉ được hệ thống cập nhật.'))
            if any(batch.state != 'draft' for batch in self) and set(vals) - {'name'}:
                raise UserError(self.env._('Tạo lô nhập mới để thay tệp nguồn đã xem trước.'))
            self._tp_require()
        return super().write(vals)

    def unlink(self):
        if any(batch.state != 'draft' for batch in self):
            raise UserError(self.env._('Không xóa lịch sử nhập; dùng Hủy lô khi chưa áp dụng.'))
        self._tp_require()
        return super().unlink()

    def _lock(self):
        self.ensure_one()
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [ADVISORY_KEY, self.company_id.id])
        self.env.cr.execute('SELECT id FROM tp_hr_attendance_batch WHERE id=%s FOR UPDATE', [self.id])
        self.invalidate_recordset()

    # ------------------------------------------------------------- mapping
    def _tp_mapper(self):
        company = self.company_id
        codes = {code.machine_code: code for code in self.env['tp.hr.attendance.code'].sudo().search([('company_id', '=', company.id)])}
        Employee = self.env['hr.employee'].sudo().with_context(active_test=False)
        cache = {}

        def resolve(machine_code, name):
            if not machine_code:
                return Employee, Employee, 'unmapped', self.env._('Thiếu mã máy (cột ID).')
            if machine_code in codes:
                code = codes[machine_code]
                employee = code.employee_id
                if code.source == 'auto' and fold(employee.name) != fold(name):
                    return Employee, employee, 'name_conflict', self.env._('Tên trong tệp khác hồ sơ đã gắn mã máy; cần HR đối chiếu.')
                if not employee.active:
                    return Employee, employee, 'unmapped', self.env._('Hồ sơ gắn mã máy đã lưu trữ.')
                return employee, employee, None, ''
            if machine_code not in cache:
                cache[machine_code] = Employee.search([('company_id', '=', company.id), ('tp_source_code', '=', machine_code), ('active', '=', True)])
            found = cache[machine_code]
            if len(found) == 1 and fold(found.name) == fold(name):
                return found, found, None, ''
            if len(found) == 1:
                return Employee, found, 'name_conflict', self.env._('Mã máy trùng mã nguồn nhưng họ tên khác; không tự ghép.')
            return Employee, Employee, 'unmapped', self.env._('Chưa có hồ sơ mang mã này; HR khai báo Mã máy chấm công nếu cần.')
        return resolve, codes

    # ------------------------------------------------------------- preview
    def action_preview(self):
        self.ensure_one()
        self._tp_require()
        self._lock()
        if self.state != 'draft':
            return True
        data = self.file_data.content if self.file_data else b''
        try:
            sheets = parse_attendance(data)
        except AttendanceFormatError as exc:
            raise UserError(str(exc)) from exc
        resolve, _codes = self._tp_mapper()
        tz = self.tz or DEFAULT_TZ
        lines, lates, summary, coverage, empty = [], [], [], set(), 0
        for sheet in sheets:
            employees = set()
            for person in sheet['people']:
                employee, _candidate, problem, _msg = resolve(person['machine_code'], person['name'])
                if employee and not problem:
                    employees.add(employee.id)
            coverage |= employees
            empty += sheet['empty_cells']
            summary.append({
                'name': sheet['name'], 'from': sheet['period'][0].isoformat() if sheet['period'] else None,
                'to': sheet['period'][1].isoformat() if sheet['period'] else None, 'employees': sheet['employees'],
                'events': len(sheet['events']), 'empty': sheet['empty_cells'], 'errors': sheet['errors'],
                'employee_ids': sorted(employees), 'late': sheet.get('late') or {},
                'absent': sheet.get('absent') or {},
                'day_columns': [
                    {
                        'column': col['column'], 'col_letter': col['col_letter'],
                        'date': col['date'].isoformat(), 'header_day': col['header_day'],
                        'header_weekday': col['header_weekday'], 'weekday': col['weekday'],
                    }
                    for col in (sheet.get('day_columns') or [])
                ],
            })
            if sheet['period'] and not sheet['errors']:
                for person in sheet['people']:
                    if 'late_state' not in person:
                        continue
                    lates.append({
                        'batch_id': self.id, 'sheet_name': sheet['name'], 'sheet_index': sheet['index'], 'row_number': person['row'],
                        'cell_ref': person['late_cell'], 'machine_code': person['machine_code'],
                        'raw_source_code': person.get('raw_source_code') or '', 'source_name': person['name'],
                        'date_from': sheet['period'][0], 'date_to': sheet['period'][1],
                        'late_count': person['late_count'] or 0, 'late_minutes': person['late_minutes'] or 0,
                        'raw_count': person['late_raw_count'], 'raw_minutes': person['late_raw_minutes'],
                        'source_state': person['late_state'], 'state': 'preview',
                    })
            for event in sheet['events']:
                check_in = local_to_utc(event['work_date'], event['clock_in'], tz) if event['clock_in'] else False
                check_out = local_to_utc(event['work_date'], event['clock_out'], tz) if event['clock_out'] else False
                lines.append({
                    'batch_id': self.id, 'sheet_name': event['sheet'], 'sheet_index': event['sheet_index'], 'row_number': event['row'],
                    'column_index': event['column'], 'cell_ref': event['cell'], 'machine_code': event['machine_code'],
                    'raw_source_code': event.get('raw_source_code') or '',
                    'source_name': event['name'], 'source_title': event['title'], 'source_group': event['group'],
                    'work_date': event['work_date'], 'raw_in': event['raw_in'], 'raw_out': event['raw_out'],
                    'check_in': check_in, 'check_out': check_out, 'kind': event['kind'], 'state': 'review',
                })
        internal(self.env['tp.hr.attendance.line']).create(lines)
        internal(self.env['tp.hr.attendance.late']).create(lates)
        periods = [sheet['period'] for sheet in sheets if sheet['period']]
        checksum = hashlib.sha256(data).hexdigest()
        same = self.sudo().search([('id', '!=', self.id), ('company_id', '=', self.company_id.id), ('checksum', '=', checksum),
                                   ('state', 'in', ('applied', 'partial'))], limit=1)
        internal(self).write({
            'checksum': checksum, 'same_file_batch_id': same.id, 'sheet_summary': summary, 'empty_count': empty,
            'period_from': min(p[0] for p in periods) if periods else False, 'period_to': max(p[1] for p in periods) if periods else False,
            'employee_ids': [(6, 0, sorted(coverage))], 'state': 'preview',
            'batch_code': self.batch_code or f'LÔ-{self.id:05d}',
        })
        if hasattr(self, '_tp_build_snapshot'):
            self._tp_build_snapshot(sheets)
        self._tp_classify()
        self.env['tp.hr.attendance.log']._tp_log(self, 'import_preview', {'file': self.file_name, 'checksum': checksum[:16], 'lines': len(lines),
                                                                         'late': len(lates)})
        return True

    def _tp_classify(self):
        """(Re)assign every line's state against the database as it is now; nothing is written to sessions here."""
        self.ensure_one()
        Line = self.env['tp.hr.attendance.line'].sudo()
        Period = self.env['tp.hr.attendance.period']
        resolve, _codes = self._tp_mapper()
        ranges = Period._tp_locked_ranges([self.company_id.id])
        lines = self.sudo().line_ids.sorted(lambda line: (line.sheet_index, line.row_number, line.column_index))
        decided, groups = {}, defaultdict(list)
        for line in lines:
            if line.state == 'applied' or line.source_choice == 'keep':
                continue
            employee, candidate, problem, message = resolve(line.machine_code, line.source_name)
            base = {'employee_id': employee.id or False, 'candidate_employee_id': candidate.id or False}
            if problem:
                decided[line] = dict(base, state=problem, message=message, signature=False)
                continue
            sig = signature(employee.id, line.work_date, line.kind, line.check_in, line.check_out, line.raw_in, line.raw_out)
            if Period._tp_is_locked(self.company_id.id, line.work_date, ranges):
                decided[line] = dict(base, state='locked', message=self.env._('Kỳ công đã chốt; cần đính chính có duyệt.'), signature=sig)
                continue
            decided[line] = dict(base, signature=sig)
            groups[employee.id, line.work_date].append(line)
        if groups:
            employee_ids = list({key[0] for key in groups})
            work_dates = list({key[1] for key in groups})
            sessions, issues, handled = defaultdict(list), defaultdict(list), defaultdict(set)
            # Punches replaced by an approved correction stay inactive; they still count as already recorded.
            for session in self.env['tp.hr.attendance.session'].sudo().with_context(active_test=False).search([
                    ('employee_id', 'in', employee_ids), ('work_date', 'in', work_dates)]):
                sessions[session.employee_id.id, session.work_date].append(session)
            for issue in Line.search([('employee_id', 'in', employee_ids), ('work_date', 'in', work_dates),
                                      ('issue_open', '=', True), ('batch_id', '!=', self.id)]):
                issues[issue.employee_id.id, issue.work_date].append(issue)
            # Issues already settled (completed by a later import or by an approved correction) must not reopen on re-import.
            for issue in Line.search([('employee_id', 'in', employee_ids), ('work_date', 'in', work_dates), ('issue_open', '=', False),
                                      ('state', 'in', ISSUE_STATES), ('batch_id.state', 'in', ('applied', 'partial')), ('batch_id', '!=', self.id)]):
                handled[issue.employee_id.id, issue.work_date].add(issue.signature)
            for key, members in groups.items():
                decisions = self._tp_decide(members, sessions.get(key, []), issues.get(key, []), decided, handled.get(key, set()))
                for line, (state, message) in decisions.items():
                    decided[line].update(state=state, message=message)
        for line, vals in decided.items():
            internal(line).write(vals)
        counts = {state: 0 for state in COUNTED}
        for line in lines:
            counts[line.state] += 1
        internal(self).write(dict({f'{state}_count': value for state, value in counts.items()}, line_count=len(lines)))
        self._tp_classify_late(resolve, ranges)

    def _tp_classify_late(self, resolve, ranges):
        """Machine late totals: same employee + same source period already applied → duplicate when equal,
        conflict when different (never last-write-wins). Missing/invalid numbers stay "Chưa có số liệu"."""
        _ = self.env._
        Late = self.env['tp.hr.attendance.late'].sudo()
        Period = self.env['tp.hr.attendance.period']
        rows = self.sudo().late_ids.sorted(lambda row: (row.sheet_index, row.row_number))
        decided, keyed = {}, defaultdict(list)
        for row in rows:
            if row.state in ('applied', 'superseded') or row.source_choice == 'keep':
                continue
            employee, candidate, problem, message = resolve(row.machine_code, row.source_name)
            vals = {'employee_id': employee.id or False, 'candidate_employee_id': candidate.id or False}
            if problem:
                decided[row] = dict(vals, state=problem, message=message)
            elif row.source_state in ('empty', 'invalid'):
                decided[row] = dict(vals, state='missing', message=_(LATE_MESSAGES[row.source_state]))
            elif row.source_state == 'inconsistent':
                decided[row] = dict(vals, state='review', message=_(LATE_MESSAGES['inconsistent']))
            elif any(Period._tp_is_locked(self.company_id.id, day, ranges) for day in dates_between(row.date_from, row.date_to)):
                decided[row] = dict(vals, state='locked', message=_('Kỳ công đã chốt; tổng đi muộn không ghi đè.'))
            else:
                decided[row] = vals
                keyed[employee.id, row.date_from, row.date_to].append(row)
        if keyed:
            known = {}
            for old in Late.search([('company_id', '=', self.company_id.id), ('state', '=', 'applied'),
                                    ('employee_id', 'in', list({key[0] for key in keyed}))]):
                known[old.employee_id.id, old.date_from, old.date_to] = (old.late_count, old.late_minutes)
            for key, members in keyed.items():
                values = {(row.late_count, row.late_minutes) for row in members}
                label = short_range(key[1], key[2])
                if key in known:
                    same = values == {known[key]}
                    for row in members:
                        decided[row].update(state='duplicate' if same else 'conflict', message=_(
                            'Tổng kỳ %(period)s đã nhập với cùng số.', period=label) if same else _(
                            'Tổng kỳ %(period)s đã nhập với số khác; không ghi đè, HR cần đối chiếu.', period=label))
                elif len(values) > 1:
                    for row in members:
                        decided[row].update(state='conflict', message=_('Các trang trong tệp có tổng kỳ %(period)s khác nhau.', period=label))
                else:
                    for index, row in enumerate(members):
                        decided[row].update(state='duplicate' if index else 'valid',
                                            message=_('Trùng trang khác trong cùng tệp.') if index else '')
        for row, vals in decided.items():
            internal(row).write(vals)
        counts = {state: 0 for state in LATE_COUNTED}
        for row in rows:
            if row.state in counts:
                counts[row.state] += 1
        internal(self).write({f'late_{state}_count': value for state, value in counts.items()})

    def _tp_decide(self, members, sessions, issues, decided, handled=frozenset()):
        _ = self.env._
        recorded = {signature(s.employee_id.id, s.work_date, 'pair', s.check_in, s.check_out) for s in sessions}
        sessions = [session for session in sessions if session.active]
        known = recorded | {issue.signature for issue in issues} | set(handled)
        result = {}
        for line in members:
            if decided[line]['signature'] in known:
                result[line] = ('duplicate', _('Đã có trong dữ liệu đã nhập hoặc đã xử lý trước đó.'))
        fresh = [line for line in members if line not in result]
        if not fresh:
            return result
        conflict = _('Cùng ngày đã có giờ khác hoặc ký hiệu cần kiểm tra; không ghi đè, cần đề nghị điều chỉnh.')
        if sessions:
            for line in fresh:
                if line.kind != 'pair' and any(consistent(line, s.check_in, s.check_out) for s in sessions):
                    result[line] = ('duplicate', _('Giờ này đã nằm trong phiên đã nhập.'))
                else:
                    result[line] = ('conflict', conflict)
            return result
        pair_sigs = list(dict.fromkeys(decided[line]['signature'] for line in fresh if line.kind == 'pair'))
        other_sigs = list(dict.fromkeys(decided[line]['signature'] for line in fresh if line.kind != 'pair'))
        if len(pair_sigs) > 1:
            result.update({line: ('conflict', _('Các trang hoặc dòng có giờ khác nhau cho cùng ngày.')) for line in fresh})
            return result
        if pair_sigs:
            pair = next(line for line in fresh if line.kind == 'pair')
            others = [line for line in fresh if line.kind != 'pair'] + list(issues)
            if any(not consistent(other, pair.check_in, pair.check_out) for other in others):
                result.update({line: ('conflict', conflict) for line in fresh})
                return result
            for line in fresh:
                if line == pair:
                    result[line] = ('valid', _('Hoàn thiện giờ còn thiếu từ lần nhập trước.') if issues else '')
                elif line.kind == 'pair':
                    result[line] = ('duplicate', _('Trùng dòng khác trong cùng tệp.'))
                else:
                    result[line] = ('duplicate', _('Đã có đủ giờ vào - ra ở trang khác của tệp.'))
            return result
        if len(other_sigs) > 1 or issues:
            result.update({line: ('conflict', conflict) for line in fresh})
            return result
        for index, line in enumerate(fresh):
            if index:
                result[line] = ('duplicate', _('Trùng dòng khác trong cùng tệp.'))
            else:
                state = 'missing' if line.kind in ('missing_in', 'missing_out') else 'review'
                result[line] = (state, KIND_MESSAGES.get(line.kind, ''))
        return result

    # --------------------------------------------------------------- apply
    def action_apply(self):
        self.ensure_one()
        self._tp_require()
        self._lock()
        if self.state == 'applied':
            return True
        if self.state not in ('preview', 'partial'):
            raise UserError(self.env._('Hãy xem trước tệp trước khi áp dụng.'))
        self._tp_classify()
        Session = internal(self.env['tp.hr.attendance.session'])
        Line = self.env['tp.hr.attendance.line'].sudo()
        Late = self.env['tp.hr.attendance.late'].sudo()
        _resolve, codes = self._tp_mapper()
        keys, new_codes = set(), {}
        lines = self.sudo().line_ids
        for line in lines.filtered(lambda line: line.state == 'valid'):
            session = Session.create({
                'employee_id': line.employee_id.id, 'company_id': self.company_id.id, 'work_date': line.work_date,
                'check_in': line.check_in, 'check_out': line.check_out, 'source': 'import', 'batch_id': self.id, 'line_id': line.id,
                'source_batch_ids': [(4, self.id)], 'source_line_ids': [(4, line.id)],
            })
            completed = Line.search([('employee_id', '=', line.employee_id.id), ('work_date', '=', line.work_date),
                                     ('issue_open', '=', True), ('batch_id', '!=', self.id)])
            internal(completed).write({'issue_open': False, 'resolved_by_line_id': line.id,
                                       'resolution': self.env._('Đã đủ giờ vào - ra từ lô %(batch)s.', batch=self.name)})
            internal(line).write({'state': 'applied', 'session_id': session.id})
            keys.add((line.employee_id.id, line.work_date))
            if line.machine_code not in codes:
                new_codes[line.machine_code] = line.employee_id.id
        # Identical hours in a second file attach provenance to the single canonical session without double-counting.
        for line in lines.filtered(lambda line: line.state == 'duplicate' and line.kind == 'pair' and line.employee_id):
            matched = Session.search([
                ('employee_id', '=', line.employee_id.id), ('work_date', '=', line.work_date),
                ('check_in', '=', line.check_in), ('check_out', '=', line.check_out),
            ], limit=1)
            if matched:
                matched.write({'source_batch_ids': [(4, self.id)], 'source_line_ids': [(4, line.id)]})
                internal(line).write({'session_id': matched.id})
        for line in lines.filtered(lambda line: line.state in ISSUE_STATES and line.employee_id):
            internal(line).write({'issue_open': True})
            keys.add((line.employee_id.id, line.work_date))
        if new_codes:
            internal(self.env['tp.hr.attendance.code']).create([
                {'machine_code': code, 'employee_id': employee_id, 'company_id': self.company_id.id, 'source': 'auto',
                 'note': self.env._('Tự đối chiếu mã nguồn và họ tên khi nhập lô %(batch)s.', batch=self.name)}
                for code, employee_id in new_codes.items()])
        self.env['tp.hr.attendance.day']._tp_refresh(self.company_id, keys)
        late_rows = self.sudo().late_ids.filtered(lambda row: row.state == 'valid')
        internal(late_rows).write({'state': 'applied', 'source_batch_ids': [(4, self.id)]})
        for dup_late in self.sudo().late_ids.filtered(lambda row: row.state == 'duplicate' and row.employee_id):
            canonical = Late.search([
                ('company_id', '=', self.company_id.id), ('employee_id', '=', dup_late.employee_id.id),
                ('date_from', '=', dup_late.date_from), ('date_to', '=', dup_late.date_to), ('state', '=', 'applied'),
            ], limit=1)
            if canonical and (canonical.late_count, canonical.late_minutes) == (dup_late.late_count, dup_late.late_minutes):
                internal(canonical).write({'source_batch_ids': [(4, self.id)]})
                internal(dup_late).write({'canonical_late_id': canonical.id})
        late_counts = {state: 0 for state in LATE_COUNTED}
        for row in self.sudo().late_ids:
            if row.state in late_counts:
                late_counts[row.state] += 1
        internal(self).write({f'late_{state}_count': value for state, value in late_counts.items()})
        counts = {state: 0 for state in COUNTED}
        for line in lines:
            counts[line.state] += 1
        summary = {key: value for key, value in counts.items() if value}
        unresolved = self._tp_unresolved_conflict_count()
        final_state = 'partial' if unresolved else 'applied'
        internal(self).write(dict({f'{state}_count': value for state, value in counts.items()}, state=final_state,
                                  applied_by=self.env.user.id, applied_at=fields.Datetime.now(), result=str(summary)))
        self.env['tp.hr.attendance.log']._tp_log(self, 'import_apply', dict(summary, state=final_state, days=len(keys), late=len(late_rows)))
        return True

    def _tp_unresolved_conflict_count(self):
        self.ensure_one()
        batch = self.sudo()
        line_conflicts = len(batch.line_ids.filtered(lambda row: row.state == 'conflict' and not row.resolved_by_resolution_id))
        late_conflicts = len(batch.late_ids.filtered(lambda r: r.state == 'conflict' and not r.resolved_by_resolution_id))
        deferred = 0
        if 'tp.hr.attendance.resolution' in self.env:
            Res = self.env['tp.hr.attendance.resolution'].sudo()
            deferred = Res.search_count([
                '|', ('batch_a_id', '=', batch.id), ('batch_b_id', '=', batch.id),
                ('is_latest', '=', True), ('decision', '=', 'defer'),
            ])
        return line_conflicts + late_conflicts + deferred

    def action_cancel(self, reason=''):
        self.ensure_one()
        self._tp_require()
        self._lock()
        if self.state != 'preview':
            raise UserError(self.env._('Chỉ bỏ qua được lô nguồn chưa áp dụng vào bảng tổng hợp.'))
        clean_reason = (reason or '').strip()[:240]
        internal(self).write({
            'state': 'cancelled',
            'cancel_reason': clean_reason or False,
            'cancelled_by': self.env.user.id,
            'cancelled_at': fields.Datetime.now(),
        })
        internal(self.sudo().late_ids.filtered(lambda row: row.state != 'applied')).write({'state': 'cancelled'})
        self.env['tp.hr.attendance.log']._tp_log(self, 'import_cancel', {'reason': clean_reason})
        return True

    def action_open_lines(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('tp_hr_attendance.action_import_lines')
        action['domain'] = [('batch_id', '=', self.id)]
        action['context'] = {'tp_filter_profile': 'import_lines'}
        action['display_name'] = self.env._('Dòng nhập — %(batch)s', batch=self.name)
        return action

    # ----------------------------------------------------- drag-and-drop upload
    @api.model
    def tp_upload_preview(self, params=None):
        """Create a batch from an uploaded .xlsx and read it at once; returns what the dialog shows.

        Same guards as the form flow: ``create`` and ``action_preview`` require the import capability; a
        format error raises and the whole request (batch included) is rolled back.
        """
        params = dict(params or {})
        file_name = str(params.get('file_name') or '').strip()[:200]
        data = params.get('data') or ''
        if not file_name.lower().endswith('.xlsx'):
            raise UserError(self.env._('Chỉ nhận tệp .xlsx xuất từ máy chấm công.'))
        if not data or not isinstance(data, str):
            raise UserError(self.env._('Chưa chọn tệp Excel.'))
        if len(data) > UPLOAD_MAX_B64:
            raise UserError(self.env._('Tệp quá lớn (tối đa 15 MB).'))
        company = self.env.company
        require(self.env, 'import', company)
        batch = self.create({'name': self.env._('Excel máy · %(file)s', file=file_name), 'file_name': file_name,
                             'file_data': data, 'company_id': company.id})
        batch.action_preview()
        return batch._tp_preview_payload()

    @api.model
    def _tp_upload_batch(self, batch_id):
        batch = self.browse(int(batch_id or 0)).exists()
        if not batch:
            raise UserError(self.env._('Không tìm thấy lô nhập.'))
        batch.check_access('read')
        batch._tp_require()
        return batch

    @api.model
    def tp_upload_apply(self, batch_id):
        batch = self._tp_upload_batch(batch_id)
        batch.action_apply()
        return batch._tp_preview_payload()

    @api.model
    def tp_upload_cancel(self, batch_id):
        batch = self._tp_upload_batch(batch_id)
        if batch.state == 'preview':
            batch.action_cancel()
        return {'batch_id': batch.id, 'state': batch.state}

    def _tp_preview_payload(self):
        self.ensure_one()
        batch = self.sudo()
        line_states = dict(LINE_STATES)
        late_states = dict(self.env['tp.hr.attendance.late']._fields['state'].selection)
        sheets = []
        for sheet in batch.sheet_summary or []:
            late = sheet.get('late') or {}
            sheets.append({
                'name': sheet.get('name'), 'from': sheet.get('from'), 'to': sheet.get('to'),
                'label': short_range(fields.Date.from_string(sheet['from']), fields.Date.from_string(sheet['to'])) if sheet.get('from') and sheet.get('to') else '',
                'employees': sheet.get('employees') or 0, 'matched': len(sheet.get('employee_ids') or []), 'events': sheet.get('events') or 0,
                'empty': sheet.get('empty') or 0, 'errors': sheet.get('errors') or [], 'late_state': late.get('state') or 'no_column',
                'late_ref': late.get('ref') or '', 'late_message': late.get('message') or '',
            })
        attention = batch.line_ids.filtered(lambda line: line.state not in ('valid', 'applied', 'duplicate'))
        late_attention = batch.late_ids.filtered(lambda row: row.state not in ('valid', 'applied', 'duplicate', 'preview'))
        return {
            'batch_id': batch.id, 'batch_code': batch.batch_code or f'LÔ-{batch.id:05d}',
            'name': batch.name, 'file_name': batch.file_name or '', 'state': batch.state,
            'period': {'from': fields.Date.to_string(batch.period_from), 'to': fields.Date.to_string(batch.period_to),
                       'label': short_range(batch.period_from, batch.period_to) if batch.period_from and batch.period_to else ''},
            'sheets': sheets, 'matched': len(batch.employee_ids), 'people': sum(sheet['employees'] for sheet in sheets),
            'counts': {state: batch[f'{state}_count'] for state in COUNTED}, 'line_count': batch.line_count, 'empty': batch.empty_count,
            'late': {state: batch[f'late_{state}_count'] for state in LATE_COUNTED}, 'late_total': len(batch.late_ids),
            'labels': line_states, 'late_labels': late_states,
            'same_file': batch.same_file_batch_id.name or '',
            'same_file_code': batch.same_file_batch_id.batch_code or '',
            'attention': [{'sheet': line.sheet_name, 'cell': line.cell_ref, 'code': line.machine_code or '', 'name': line.source_name or '',
                           'date': fields.Date.to_string(line.work_date), 'state': line.state, 'state_label': line_states.get(line.state, ''),
                           'message': line.message or ''} for line in attention[:PREVIEW_ATTENTION]],
            'attention_total': len(attention),
            'late_attention': [{'sheet': row.sheet_name, 'cell': row.cell_ref, 'code': row.machine_code or '', 'name': row.source_name or '',
                                'state': row.state, 'state_label': late_states.get(row.state, ''), 'message': row.message or ''}
                               for row in late_attention[:PREVIEW_ATTENTION]],
            'late_attention_total': len(late_attention),
            'can_apply': batch.state == 'preview',
            'uploaded_at': fields.Datetime.to_string(batch.create_date) if batch.create_date else '',
            'uploaded_by': batch.create_uid.name or '',
            'applied_at': fields.Datetime.to_string(batch.applied_at) if batch.applied_at else '',
        }

    @api.model
    def _tp_coverage(self, company, start, end):
        """``[(from, to, {employee ids})]`` per applied sheet: the file listed these people for these days."""
        batches = self.sudo().search([('company_id', '=', company.id), ('state', 'in', ('applied', 'partial')),
                                      ('period_from', '<=', end), ('period_to', '>=', start)])
        result = []
        for batch in batches:
            for sheet in batch.sheet_summary or []:
                if sheet.get('from') and sheet.get('to') and not sheet.get('errors'):
                    result.append((fields.Date.from_string(sheet['from']), fields.Date.from_string(sheet['to']), set(sheet.get('employee_ids') or [])))
        return result


class AttendanceLine(models.Model):
    _name = 'tp.hr.attendance.line'
    _description = 'Dòng nhập dữ liệu công'
    _order = 'batch_id desc, sheet_index, row_number, column_index'
    _check_company_auto = True

    batch_id = fields.Many2one('tp.hr.attendance.batch', 'Lô nhập', required=True, index=True, ondelete='cascade')
    company_id = fields.Many2one(related='batch_id.company_id', store=True, string='Công ty')
    sheet_name = fields.Char('Trang', readonly=True)
    sheet_index = fields.Integer(readonly=True)
    row_number = fields.Integer('Dòng', readonly=True)
    column_index = fields.Integer(readonly=True)
    cell_ref = fields.Char('Ô', readonly=True)
    machine_code = fields.Char('Mã máy', readonly=True, index=True)
    raw_source_code = fields.Char('Mã NV trong tệp', readonly=True, index=True)
    source_name = fields.Char('Tên trong tệp', readonly=True)
    source_title = fields.Char('Chức vụ trong tệp', readonly=True)
    source_group = fields.Char('Nhóm trong tệp', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Nhân viên', readonly=True, index=True)
    candidate_employee_id = fields.Many2one('hr.employee', 'Hồ sơ gợi ý', readonly=True)
    work_date = fields.Date('Ngày công', readonly=True, index=True)
    raw_in = fields.Char('Vào (nguồn)', readonly=True)
    raw_out = fields.Char('Ra (nguồn)', readonly=True)
    check_in = fields.Datetime('Giờ vào', readonly=True)
    check_out = fields.Datetime('Giờ ra', readonly=True)
    kind = fields.Selection(KINDS, 'Loại dòng', readonly=True, required=True)
    state = fields.Selection(LINE_STATES, 'Kết quả', readonly=True, required=True, index=True)
    message = fields.Char('Giải thích', readonly=True)
    signature = fields.Char(readonly=True, index=True)
    session_id = fields.Many2one('tp.hr.attendance.session', 'Phiên đã ghi', readonly=True)
    day_id = fields.Many2one('tp.hr.attendance.day', 'Ngày công tổng hợp', readonly=True, index=True, ondelete='set null')
    issue_open = fields.Boolean('Đang chờ xử lý', readonly=True, index=True)
    resolved_by_line_id = fields.Many2one('tp.hr.attendance.line', 'Được hoàn thiện bởi', readonly=True)
    resolved_by_resolution_id = fields.Many2one('tp.hr.attendance.resolution', 'Quyết định đối chiếu', readonly=True, ondelete='set null')
    resolution = fields.Char('Cách xử lý', readonly=True)
    source_choice = fields.Selection([('selected', 'Chọn nguồn'), ('keep', 'Giữ dữ liệu hiện tại')], readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        deny_direct(self)
        return super().create(vals_list)

    def write(self, vals):
        deny_direct(self)
        return super().write(vals)

    def unlink(self):
        deny_direct(self)
        return super().unlink()
