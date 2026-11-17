"""Preview → apply import of the machine attendance report; duplicates and conflicts never overwrite."""
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
    state = fields.Selection([('draft', 'Chọn tệp'), ('preview', 'Xem trước'), ('applied', 'Đã áp dụng'), ('cancelled', 'Đã hủy')],
                             'Trạng thái', default='draft', readonly=True, required=True, index=True)
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
    applied_by = fields.Many2one('res.users', 'Người áp dụng', readonly=True)
    applied_at = fields.Datetime('Thời điểm áp dụng', readonly=True)
    result = fields.Text('Kết quả', readonly=True)
    summary_html = fields.Html('Theo trang tính', compute='_compute_summary_html', sanitize=False)

    _SYSTEM_FIELDS = {'checksum', 'same_file_batch_id', 'tz', 'state', 'sheet_summary', 'period_from', 'period_to', 'employee_ids',
                      'line_ids', 'attention_line_ids', 'applied_by', 'applied_at', 'result', 'line_count', 'empty_count'} | {f'{s}_count' for s in COUNTED}

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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if set(vals) & self._SYSTEM_FIELDS:
                raise AccessError(self.env._('Kết quả nhập chỉ được hệ thống cập nhật.'))
            company = self.env['res.company'].browse(vals.get('company_id')) if vals.get('company_id') else self.env.company
            require(self.env, 'import', company)
        return super().create(vals_list)

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
        self.env.cr.execute('SELECT id FROM tp_hr_attendance_batch WHERE id=%s FOR UPDATE', [self.id])
        self.invalidate_recordset()
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [ADVISORY_KEY, self.company_id.id])

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
        lines, summary, coverage, empty = [], [], set(), 0
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
                'employee_ids': sorted(employees),
            })
            for event in sheet['events']:
                check_in = local_to_utc(event['work_date'], event['clock_in'], tz) if event['clock_in'] else False
                check_out = local_to_utc(event['work_date'], event['clock_out'], tz) if event['clock_out'] else False
                lines.append({
                    'batch_id': self.id, 'sheet_name': event['sheet'], 'sheet_index': event['sheet_index'], 'row_number': event['row'],
                    'column_index': event['column'], 'cell_ref': event['cell'], 'machine_code': event['machine_code'],
                    'source_name': event['name'], 'source_title': event['title'], 'source_group': event['group'],
                    'work_date': event['work_date'], 'raw_in': event['raw_in'], 'raw_out': event['raw_out'],
                    'check_in': check_in, 'check_out': check_out, 'kind': event['kind'], 'state': 'review',
                })
        internal(self.env['tp.hr.attendance.line']).create(lines)
        periods = [sheet['period'] for sheet in sheets if sheet['period']]
        checksum = hashlib.sha256(data).hexdigest()
        same = self.sudo().search([('id', '!=', self.id), ('company_id', '=', self.company_id.id), ('checksum', '=', checksum),
                                   ('state', '=', 'applied')], limit=1)
        internal(self).write({
            'checksum': checksum, 'same_file_batch_id': same.id, 'sheet_summary': summary, 'empty_count': empty,
            'period_from': min(p[0] for p in periods) if periods else False, 'period_to': max(p[1] for p in periods) if periods else False,
            'employee_ids': [(6, 0, sorted(coverage))], 'state': 'preview',
        })
        self._tp_classify()
        self.env['tp.hr.attendance.log']._tp_log(self, 'import_preview', {'file': self.file_name, 'checksum': checksum[:16], 'lines': len(lines)})
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
            sessions, issues = defaultdict(list), defaultdict(list)
            for session in self.env['tp.hr.attendance.session'].sudo().search([
                    ('employee_id', 'in', employee_ids), ('work_date', 'in', work_dates)]):
                sessions[session.employee_id.id, session.work_date].append(session)
            for issue in Line.search([('employee_id', 'in', employee_ids), ('work_date', 'in', work_dates),
                                      ('issue_open', '=', True), ('batch_id', '!=', self.id)]):
                issues[issue.employee_id.id, issue.work_date].append(issue)
            for key, members in groups.items():
                for line, (state, message) in self._tp_decide(members, sessions.get(key, []), issues.get(key, []), decided).items():
                    decided[line].update(state=state, message=message)
        for line, vals in decided.items():
            internal(line).write(vals)
        counts = {state: 0 for state in COUNTED}
        for line in lines:
            counts[line.state] += 1
        internal(self).write(dict({f'{state}_count': value for state, value in counts.items()}, line_count=len(lines)))

    def _tp_decide(self, members, sessions, issues, decided):
        _ = self.env._
        recorded = {signature(s.employee_id.id, s.work_date, 'pair', s.check_in, s.check_out) for s in sessions}
        open_sigs = {issue.signature for issue in issues}
        result = {}
        for line in members:
            if decided[line]['signature'] in recorded | open_sigs:
                result[line] = ('duplicate', _('Đã có trong dữ liệu đã nhập trước đó.'))
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
        if self.state != 'preview':
            raise UserError(self.env._('Hãy xem trước tệp trước khi áp dụng.'))
        self._tp_classify()
        Session = internal(self.env['tp.hr.attendance.session'])
        Line = self.env['tp.hr.attendance.line'].sudo()
        _resolve, codes = self._tp_mapper()
        keys, new_codes = set(), {}
        lines = self.sudo().line_ids
        for line in lines.filtered(lambda line: line.state == 'valid'):
            session = Session.create({
                'employee_id': line.employee_id.id, 'company_id': self.company_id.id, 'work_date': line.work_date,
                'check_in': line.check_in, 'check_out': line.check_out, 'source': 'import', 'batch_id': self.id, 'line_id': line.id,
            })
            completed = Line.search([('employee_id', '=', line.employee_id.id), ('work_date', '=', line.work_date),
                                     ('issue_open', '=', True), ('batch_id', '!=', self.id)])
            internal(completed).write({'issue_open': False, 'resolved_by_line_id': line.id,
                                       'resolution': self.env._('Đã đủ giờ vào - ra từ lô %(batch)s.', batch=self.name)})
            internal(line).write({'state': 'applied', 'session_id': session.id})
            keys.add((line.employee_id.id, line.work_date))
            if line.machine_code not in codes:
                new_codes[line.machine_code] = line.employee_id.id
        for line in lines.filtered(lambda line: line.state in ISSUE_STATES and line.employee_id):
            internal(line).write({'issue_open': True})
            keys.add((line.employee_id.id, line.work_date))
        if new_codes:
            internal(self.env['tp.hr.attendance.code']).create([
                {'machine_code': code, 'employee_id': employee_id, 'company_id': self.company_id.id, 'source': 'auto',
                 'note': self.env._('Tự đối chiếu mã nguồn và họ tên khi nhập lô %(batch)s.', batch=self.name)}
                for code, employee_id in new_codes.items()])
        self.env['tp.hr.attendance.day']._tp_refresh(self.company_id, keys)
        counts = {state: 0 for state in COUNTED}
        for line in lines:
            counts[line.state] += 1
        summary = {key: value for key, value in counts.items() if value}
        internal(self).write(dict({f'{state}_count': value for state, value in counts.items()}, state='applied',
                                  applied_by=self.env.user.id, applied_at=fields.Datetime.now(), result=str(summary)))
        self.env['tp.hr.attendance.log']._tp_log(self, 'import_apply', dict(summary, days=len(keys)))
        return True

    def action_cancel(self):
        self.ensure_one()
        self._tp_require()
        self._lock()
        if self.state != 'preview':
            raise UserError(self.env._('Chỉ hủy được lô đang xem trước.'))
        internal(self).write({'state': 'cancelled'})
        self.env['tp.hr.attendance.log']._tp_log(self, 'import_cancel', {})
        return True

    def action_open_lines(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('tp_hr_attendance.action_import_lines')
        action['domain'] = [('batch_id', '=', self.id)]
        action['context'] = {'tp_filter_profile': 'import_lines'}
        action['display_name'] = self.env._('Dòng nhập — %(batch)s', batch=self.name)
        return action

    @api.model
    def _tp_coverage(self, company, start, end):
        """``[(from, to, {employee ids})]`` per applied sheet: the file listed these people for these days."""
        batches = self.sudo().search([('company_id', '=', company.id), ('state', '=', 'applied'),
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
    resolution = fields.Char('Cách xử lý', readonly=True)

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
