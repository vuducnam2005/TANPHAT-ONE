"""Imported punches (sessions) and the shared day summary every employee may read."""
import calendar
from datetime import date, datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .attendance_common import (
    DATA_STATES,
    DEFAULT_TZ,
    HR_MANAGER,
    LOCK_STATES,
    OFFICER,
    UNITS_STATES,
    can,
    deny_direct,
    internal,
    local_today,
    utc_to_local,
)
from .attendance_correction import clock_label
from .attendance_metrics import metrics, own_csv

WEEKDAY_LABELS = ('T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN')
CELL_LABELS = {
    'ok': 'Đủ dữ liệu', 'missing': 'Thiếu giờ vào/ra', 'review': 'Cần kiểm tra',
    'no_punch': 'Không có giờ vào/ra', 'no_source': 'Chưa có nguồn', 'future': 'Chưa đến',
}
PROCESSOR_GROUPS = f'{HR_MANAGER},{OFFICER}'


def _hours_overlap(start, end, window_start, window_end):
    return max(0.0, (min(end, window_end) - max(start, window_start)).total_seconds() / 3600)


def _clock(value):
    return utc_to_local(value).strftime('%H:%M') if value else ''


class AttendanceSession(models.Model):
    _name = 'tp.hr.attendance.session'
    _description = 'Phiên vào - ra'
    _order = 'check_in desc'
    _check_company_auto = True

    employee_id = fields.Many2one('hr.employee', 'Nhân viên', required=True, index=True, check_company=True, ondelete='restrict')
    company_id = fields.Many2one('res.company', 'Công ty', required=True, index=True)
    work_date = fields.Date('Ngày công', required=True, index=True)
    check_in = fields.Datetime('Giờ vào', required=True)
    check_out = fields.Datetime('Giờ ra', required=True)
    worked_hours = fields.Float('Giờ ghi nhận', compute='_compute_worked_hours', store=True)
    source = fields.Selection([('import', 'Nhập từ báo cáo máy'), ('correction', 'Điều chỉnh đã duyệt'), ('enti', 'API chấm công ENTI')], 'Nguồn', required=True, default='import')
    # A punch replaced by an approved correction is kept inactive (never deleted) so the original stays auditable.
    active = fields.Boolean('Đang hiệu lực', default=True, index=True)
    day_id = fields.Many2one('tp.hr.attendance.day', 'Ngày công tổng hợp', index=True, ondelete='set null')
    batch_id = fields.Many2one('tp.hr.attendance.batch', 'Lô nhập', groups=PROCESSOR_GROUPS, ondelete='restrict')
    line_id = fields.Many2one('tp.hr.attendance.line', 'Dòng nguồn', groups=PROCESSOR_GROUPS, ondelete='restrict')
    source_batch_ids = fields.Many2many(
        'tp.hr.attendance.batch', 'tp_hr_att_session_batch_rel', 'session_id', 'batch_id',
        string='Các lô nguồn chứng minh', groups=PROCESSOR_GROUPS, readonly=True,
    )
    source_line_ids = fields.Many2many(
        'tp.hr.attendance.line', 'tp_hr_att_session_line_rel', 'session_id', 'line_id',
        string='Các dòng nguồn chứng minh', groups=PROCESSOR_GROUPS, readonly=True,
    )
    correction_id = fields.Many2one('tp.hr.attendance.correction', 'Từ đề nghị', groups=PROCESSOR_GROUPS, readonly=True, ondelete='set null')
    superseded_by_id = fields.Many2one('tp.hr.attendance.correction', 'Được thay bởi đề nghị', groups=PROCESSOR_GROUPS, readonly=True,
                                       ondelete='set null')
    superseded_reason = fields.Char('Lý do thay nguồn', groups=PROCESSOR_GROUPS, readonly=True)

    _punch_unique = models.UniqueIndex('(employee_id, check_in, check_out)', 'Phiên vào-ra này đã được ghi nhận.')
    _order_valid = models.Constraint('CHECK(check_out > check_in)', 'Giờ ra phải sau giờ vào.')

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for session in self:
            delta = (session.check_out - session.check_in) if session.check_in and session.check_out else timedelta()
            session.worked_hours = round(delta.total_seconds() / 3600, 2)

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

    def export_data(self, fields_to_export):
        self.env['tp.hr.attendance.day']._tp_check_export(self, fields_to_export)
        return super().export_data(fields_to_export)


class AttendanceDay(models.Model):
    _name = 'tp.hr.attendance.day'
    _description = 'Ngày công'
    _order = 'work_date desc, employee_code, id'
    _check_company_auto = True

    employee_id = fields.Many2one('hr.employee', 'Nhân viên', required=True, index=True, check_company=True, ondelete='restrict')
    company_id = fields.Many2one('res.company', 'Công ty', required=True, index=True)
    work_date = fields.Date('Ngày công', required=True, index=True)
    weekday = fields.Char('Thứ', compute='_compute_labels')
    employee_code = fields.Char('Mã TP', readonly=True)
    employee_name = fields.Char('Tên nhân viên', readonly=True)
    department_id = fields.Many2one('hr.department', 'Phòng tại ngày công', readonly=True)
    first_in = fields.Datetime('Vào sớm nhất', readonly=True)
    last_out = fields.Datetime('Ra muộn nhất', readonly=True)
    in_time = fields.Char('Vào', readonly=True)
    out_time = fields.Char('Ra', readonly=True)
    session_count = fields.Integer('Số phiên', readonly=True)
    recorded_hours = fields.Float('Giờ ghi nhận', readonly=True, digits=(6, 2))
    scheduled_hours = fields.Float('Giờ theo lịch', readonly=True, digits=(6, 2))
    units = fields.Float('Số công', readonly=True, digits=(4, 2))
    units_state = fields.Selection(UNITS_STATES, 'Trạng thái công', readonly=True, default='unconfirmed', required=True)
    units_display = fields.Char('Công xác nhận', compute='_compute_labels')
    rule_id = fields.Many2one('tp.hr.attendance.rule', 'Quy tắc áp dụng', readonly=True)
    data_state = fields.Selection(DATA_STATES, 'Tình trạng dữ liệu', readonly=True, required=True, default='ok', index=True)
    source_kind = fields.Selection([('excel', 'Excel máy chấm công'), ('enti', 'API chấm công ENTI'), ('correction', 'Điều chỉnh đã duyệt')], string='Nguồn chuẩn', default='excel', index=True)
    lock_state = fields.Selection(LOCK_STATES, 'Trạng thái kỳ', compute='_compute_lock_state', search='_search_lock_state')
    source_updated_at = fields.Datetime('Cập nhật nguồn', readonly=True)
    version = fields.Integer('Phiên bản', readonly=True, default=1)
    session_ids = fields.One2many('tp.hr.attendance.session', 'day_id', 'Phiên vào-ra', readonly=True)
    issue_ids = fields.One2many('tp.hr.attendance.line', 'day_id', 'Dòng nguồn cần xử lý', readonly=True,
                                groups=PROCESSOR_GROUPS, domain=[('issue_open', '=', True)])

    _employee_day_unique = models.Constraint('UNIQUE(employee_id, work_date)', 'Mỗi nhân viên chỉ có một ngày công cho mỗi ngày.')

    @api.depends('work_date', 'units', 'units_state', 'employee_name')
    def _compute_labels(self):
        states = dict(UNITS_STATES)
        for day in self:
            day.weekday = WEEKDAY_LABELS[day.work_date.weekday()] if day.work_date else ''
            day.units_display = f'{day.units:.2f}'.replace('.', ',') if day.units_state == 'confirmed' else states.get(day.units_state, '')

    @api.depends('work_date', 'company_id')
    def _compute_lock_state(self):
        ranges = self.env['tp.hr.attendance.period']._tp_locked_ranges(self.company_id.ids)
        for day in self:
            locked = day.work_date and self.env['tp.hr.attendance.period']._tp_is_locked(day.company_id.id, day.work_date, ranges)
            day.lock_state = 'locked' if locked else 'open'

    def _search_lock_state(self, operator, value):
        values = {value} if isinstance(value, str) else set(value or [])
        if operator in ('!=', 'not in'):
            values = {'open', 'locked'} - values
        elif operator not in ('=', 'in'):
            return NotImplemented
        periods = self.env['tp.hr.attendance.period'].sudo().search([('state', '=', 'locked')])
        locked = ['|'] * (len(periods) - 1) if periods else []
        for period in periods:
            locked += ['&', '&', ('company_id', '=', period.company_id.id), ('work_date', '>=', period.date_from), ('work_date', '<=', period.date_to)]
        if values == {'locked'}:
            return locked or [('id', '=', 0)]
        if values == {'open'}:
            return ['!', *locked] if locked else []
        return [] if values else [('id', '=', 0)]

    @api.depends('employee_name', 'work_date')
    def _compute_display_name(self):
        for day in self:
            day.display_name = f"{day.employee_name or ''} · {day.work_date.strftime('%d/%m/%Y') if day.work_date else ''}"

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

    # ------------------------------------------------------------------ export
    @api.model
    def _tp_check_export(self, records, fields_to_export):
        records.check_access('read')
        user = self.env.user
        if user.has_group(HR_MANAGER):
            return True
        if records and all(can(self.env, 'import', company) for company in records.company_id):
            return True
        if records and records._name == 'tp.hr.attendance.day' and all(
                can(self.env, 'review', company, records.filtered(lambda r: r.company_id == company).department_id)
                for company in records.company_id):
            return True
        own = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)]).ids
        if own and all(record.sudo().employee_id.id in own for record in records):
            allowed = {
                'tp.hr.attendance.day': {
                    'work_date', 'weekday', 'employee_code', 'employee_name', 'first_in', 'last_out',
                    'in_time', 'out_time', 'session_count', 'recorded_hours', 'scheduled_hours',
                    'units', 'units_state', 'units_display', 'data_state', 'lock_state', 'source_updated_at', 'version',
                },
                'tp.hr.attendance.session': {'work_date', 'check_in', 'check_out', 'worked_hours', 'source'},
            }.get(records._name, set())
            if any(field not in allowed for field in fields_to_export):
                raise AccessError(self.env._('Chỉ được xuất các cột công cá nhân công khai; không xuất trường liên kết hoặc dữ liệu riêng.'))
            return True
        raise AccessError(self.env._('Chỉ được xuất công của chính mình. HR hoặc người phụ trách công xuất dữ liệu chung.'))

    def export_data(self, fields_to_export):
        self._tp_check_export(self, fields_to_export)
        return super().export_data(fields_to_export)

    # --------------------------------------------------------------- recompute
    @api.model
    def _tp_rule_for(self, company, work_date, department):
        rules = self.env['tp.hr.attendance.rule'].sudo().search([
            ('company_id', '=', company.id), ('state', '=', 'confirmed'), ('date_from', '<=', work_date),
            '|', ('date_to', '=', False), ('date_to', '>=', work_date)], order='date_from desc, id desc')
        rules = rules.filtered(lambda rule: rule.covers(work_date, department))
        # A department-specific rule wins over a company-wide one.
        return (rules.filtered('department_ids') or rules)[:1]

    @api.model
    def _tp_units(self, rule, work_date, sessions):
        if not rule._weekday_on(work_date):
            return 'off_schedule', 0.0, False
        base = datetime.combine(work_date, datetime.min.time())
        window = (base + timedelta(hours=rule.start_hour), base + timedelta(hours=rule.end_hour))
        pause = (base + timedelta(hours=rule.break_start), base + timedelta(hours=rule.break_end))
        scheduled = 0.0
        for session in sessions:
            start, end = utc_to_local(session.check_in), utc_to_local(session.check_out)
            scheduled += _hours_overlap(start, end, *window)
            if pause[1] > pause[0]:
                scheduled -= _hours_overlap(max(start, window[0]), min(end, window[1]), *pause) if end > window[0] and start < window[1] else 0.0
        scheduled = round(max(scheduled, 0.0), 2)
        return 'confirmed', scheduled, round(min(scheduled, rule.standard_hours) / rule.standard_hours, 2)

    @api.model
    def _tp_refresh(self, company, keys, allow_locked=False):
        """Create, update or drop day summaries for ``{(employee_id, work_date)}`` from sessions and open issues."""
        if not keys:
            return self.browse()
        Session = self.env['tp.hr.attendance.session'].sudo()
        Line = self.env['tp.hr.attendance.line'].sudo()
        Day = internal(self)
        employees = self.env['hr.employee'].sudo().with_context(active_test=False).browse({emp for emp, _day in keys})
        touched = Day.browse()
        for employee_id, work_date in sorted(keys, key=lambda key: (key[1], key[0])):
            employee = employees.browse(employee_id)
            day = Day.search([('employee_id', '=', employee_id), ('work_date', '=', work_date)])
            sessions = Session.search([('employee_id', '=', employee_id), ('work_date', '=', work_date)], order='check_in')
            if day and day.source_kind == 'enti' and not any(session.source == 'correction' for session in sessions):
                # ENTI wins over an Excel import; only an approved correction may replace an ENTI day.
                continue
            issues = Line.search([('employee_id', '=', employee_id), ('work_date', '=', work_date), ('issue_open', '=', True)])
            if not sessions and not issues:
                if day:
                    day.unlink()
                continue
            if not day:
                day = Day.create({
                    'employee_id': employee_id, 'company_id': company.id, 'work_date': work_date,
                    'employee_code': employee.tp_employee_code, 'employee_name': employee.name,
                    'department_id': employee.department_id.id,
                })
            touched |= day
            internal(sessions.filtered(lambda session, day=day: session.day_id != day)).write({'day_id': day.id})
            internal(issues.filtered(lambda line, day=day: line.day_id != day)).write({'day_id': day.id})
        touched._tp_recompute(allow_locked=allow_locked)
        return touched

    def _tp_recompute(self, allow_locked=False):
        now = fields.Datetime.now()
        ranges = self.env['tp.hr.attendance.period']._tp_locked_ranges(self.company_id.ids)
        for day in internal(self):
            sessions = day.session_ids.sorted('check_in')
            corrected = any(session.source == 'correction' for session in sessions)
            if day.source_kind == 'enti' and not corrected:
                continue
            if not allow_locked and self.env['tp.hr.attendance.period']._tp_is_locked(day.company_id.id, day.work_date, ranges):
                continue
            issues = day.sudo().issue_ids
            if any(issue.kind not in ('missing_in', 'missing_out') or issue.state == 'conflict' for issue in issues):
                data_state = 'review'
            elif issues:
                data_state = 'missing'
            else:
                data_state = 'ok'
            in_time, out_time = _clock(sessions[:1].check_in), _clock(sessions[-1:].check_out)
            if not sessions and data_state == 'missing':
                # Only clock times are shared; machine codes and notes stay with HR in staging.
                in_time = next((issue.raw_in for issue in issues if issue.kind == 'missing_out'), '')
                out_time = next((issue.raw_out for issue in issues if issue.kind == 'missing_in'), '')
            rule = self._tp_rule_for(day.company_id, day.work_date, day.department_id)
            units_state, scheduled, units = 'unconfirmed', 0.0, False
            if rule:
                units_state, scheduled, units = self._tp_units(rule, day.work_date, sessions)
                if data_state != 'ok' and units_state == 'confirmed':
                    units_state, units = 'pending', False
            vals = {
                'first_in': sessions[:1].check_in or False, 'last_out': sessions[-1:].check_out or False,
                'in_time': in_time or False, 'out_time': out_time or False, 'session_count': len(sessions),
                'recorded_hours': round(sum(sessions.mapped('worked_hours')), 2), 'scheduled_hours': scheduled,
                'units': units or 0.0, 'units_state': units_state, 'rule_id': rule.id, 'data_state': data_state,
            }
            if corrected:
                vals['source_kind'] = 'correction'
            changed = {key: value for key, value in vals.items()
                       if (day[key].id if isinstance(day[key], models.BaseModel) else day[key]) != value
                       and not (isinstance(value, bool) and not value and not day[key])}
            if changed:
                changed.update(source_updated_at=now, version=day.version + 1 if day.source_updated_at else day.version)
                day.write(changed)
            elif not day.source_updated_at:
                day.write({'source_updated_at': now})

    # ------------------------------------------------------------------ board
    @api.model
    def _tp_parse_date(self, value):
        try:
            return date.fromisoformat(value) if value else None
        except (TypeError, ValueError):
            raise UserError(self.env._('Ngày không hợp lệ.')) from None

    @api.model
    def _tp_month_range(self, month):
        try:
            year, number = (int(part) for part in month.split('-'))
            start = date(year, number, 1)
        except (TypeError, ValueError, AttributeError):
            raise UserError(self.env._('Tháng không hợp lệ.')) from None
        return start, date(year, number, calendar.monthrange(year, number)[1])

    @api.model
    def _tp_cell_factory(self, company, days, start, end, today):
        """Return ``(cell, day_map)``; ``cell(employee_id, date)`` gives the shared state shown on boards."""
        day_map = {(day.employee_id.id, day.work_date): day for day in days}
        coverage = self.env['tp.hr.attendance.batch']._tp_coverage(company, start, end)
        Period = self.env['tp.hr.attendance.period']
        locked_ranges = Period._tp_locked_ranges([company.id])

        def cell(employee_id, work_date):
            record = day_map.get((employee_id, work_date))
            if record:
                state = record.data_state
            elif work_date > today:
                state = 'future'
            elif any(employee_id in employees_ and first <= work_date <= last for first, last, employees_ in coverage):
                state = 'no_punch'
            else:
                state = 'no_source'
            locked = Period._tp_is_locked(company.id, work_date, locked_ranges)
            result = {'date': work_date.isoformat(), 'state': state, 'label': CELL_LABELS[state], 'lock': 'locked' if locked else 'open'}
            if record:
                result.update(day_id=record.id, in_time=record.in_time or '', out_time=record.out_time or '',
                              hours=record.recorded_hours, units=record.units_display, units_state=record.units_state,
                              units_value=record.units if record.units_state == 'confirmed' else None,
                              rule=record.rule_id.name or '', version=record.version)
            return result
        return cell, day_map

    @api.model
    def _tp_updated(self, company):
        """``({'to', 'at'} | None, applied batches)``: how far the imported source reaches and when it last changed."""
        applied = self.env['tp.hr.attendance.batch'].sudo().search(
            [('company_id', '=', company.id), ('state', 'in', ('applied', 'partial'))], order='applied_at desc')
        if not applied:
            return None, applied
        periods = [d for d in applied.mapped('period_to') if d]
        if not periods:
            return None, applied
        covered_to = max(periods)
        stamp = fields.Datetime.context_timestamp(self.with_context(tz=DEFAULT_TZ), applied[0].applied_at or applied[0].create_date)
        return {'to': covered_to.strftime('%d/%m/%Y'), 'at': stamp.strftime('%d/%m/%Y %H:%M')}, applied

    @api.model
    def tp_my_attendance(self, params=None):
        """Own month for "Công của tôi". The employee always comes from the session user; a client
        ``employee_id`` (or any other key) is ignored, so opening a colleague never changes the owner (AT06-A)."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        today = local_today(DEFAULT_TZ)
        Correction = self.env['tp.hr.attendance.correction']
        employee = Correction._tp_own_employee(company)
        if not employee:
            return {'has_employee': False, 'today': today.isoformat(),
                    'message': self.env._('Tài khoản chưa gắn hồ sơ nhân viên trong công ty đang chọn; cần admin/HR gắn hồ sơ.')}
        latest = self.search([('employee_id', '=', employee.id), ('work_date', '<=', today)], order='work_date desc', limit=1)
        anchor = latest.work_date or today
        month = params.get('month') or anchor.strftime('%Y-%m')
        start, end = self._tp_month_range(month)
        days = self.search([('employee_id', '=', employee.id), ('work_date', '>=', start), ('work_date', '<=', end)])
        cell, day_map = self._tp_cell_factory(company, days, start, end, today)
        requests = Correction.search([('employee_id', '=', employee.id), ('work_date', '>=', start), ('work_date', '<=', end)])
        sources = dict(self.env['tp.hr.attendance.session']._fields['source'].selection)
        request_states = dict(Correction._fields['state'].selection)
        by_date = {}
        for request in requests:
            by_date.setdefault(request.work_date, []).append({
                'id': request.id, 'name': request.name, 'state': request.state, 'state_label': request_states[request.state],
                'requested_in': clock_label(request.requested_in), 'requested_out': clock_label(request.requested_out),
                'review_note': request.review_note or '', 'is_amendment': request.is_amendment,
            })
        rows = []
        for offset in range((end - start).days + 1):
            work_date = start + timedelta(days=offset)
            item = cell(employee.id, work_date)
            record = day_map.get((employee.id, work_date))
            item.update(day=work_date.day, weekday=WEEKDAY_LABELS[work_date.weekday()], weekend=work_date.weekday() >= 5,
                        future=work_date > today, is_today=work_date == today, requests=by_date.get(work_date, []),
                        sessions=[{'in': _clock(session.check_in), 'out': _clock(session.check_out), 'hours': session.worked_hours,
                                   'source': session.source, 'source_label': sources[session.source]}
                                  for session in record.session_ids.sorted('check_in')] if record else [])
            rows.append(item)
        past = [row for row in rows if not row['future']]
        totals = {state: sum(1 for row in past if row['state'] == state) for state in CELL_LABELS}
        confirmed = [row for row in rows if row.get('units_state') == 'confirmed']
        totals.update(
            hours=round(sum(row.get('hours') or 0 for row in rows), 2),
            units=round(sum(day_map[employee.id, date.fromisoformat(row['date'])].units for row in confirmed), 2) if confirmed else None,
            unconfirmed=sum(1 for row in rows if row.get('day_id') and row.get('units_state') != 'confirmed'),
            pending=sum(1 for request in requests if request.state == 'submitted'),
            returned=sum(1 for request in requests if request.state == 'returned'),
        )
        periods = self.env['tp.hr.attendance.period'].search([
            ('company_id', '=', company.id), ('state', '=', 'locked'), ('date_from', '<=', end), ('date_to', '>=', start)])
        updated, _applied = self._tp_updated(company)
        return {
            'has_employee': True, 'month': month, 'start': start.isoformat(), 'end': end.isoformat(), 'today': today.isoformat(),
            'anchor': anchor.isoformat(), 'lead': start.weekday(), 'rows': rows, 'totals': totals, 'labels': CELL_LABELS,
            'employee': {'name': employee.name, 'code': employee.tp_employee_code or '', 'department': employee.department_id.name or ''},
            'locked_periods': [{'name': period.name, 'from': period.date_from.isoformat(), 'to': period.date_to.isoformat()} for period in periods],
            'updated': updated,
            'has_reviewer': bool(Correction._tp_reviewers_for(company, employee.department_id, self.env.user)),
            'has_rule': bool(self.env['tp.hr.attendance.rule'].sudo().search_count([('company_id', '=', company.id), ('state', '=', 'confirmed')])),
        }

    @api.model
    def tp_export_my_attendance(self, params=None):
        # Owner is resolved by tp_my_attendance from the current session, never client IDs.
        params = dict(params or {})
        data = self.tp_my_attendance({'month': params.get('month')})
        if not data.get('has_employee'):
            raise UserError(data['message'])
        state = params.get('state') or ''
        lock = params.get('lock') or ''
        if (state and state not in CELL_LABELS) or (lock and lock not in ('open', 'locked')):
            raise UserError(self.env._('Bộ lọc xuất công không hợp lệ.'))
        return {'filename': 'cong-cua-toi-' + data['month'] + '.csv',
                'content': own_csv(data['rows'], state, lock)}

    @api.model
    def tp_board(self, params=None):
        return self._tp_board_data(params)

    @api.model
    def tp_dashboard(self, params=None):
        params = dict(params or {})
        board = self._tp_board_data({'month': params.get('month'), 'department_id': params.get('department_id'),
                                     'search': params.get('search'), 'mode': 'month'}, paginate=False)
        result = metrics(board['rows'], board['dates'], board['today'])
        cells = result.pop('cells')
        selected = params.get('detail_state') or 'attention'
        if selected == 'attention':
            cells = [row for row in cells if row['state'] in ('missing', 'review')]
        elif selected in CELL_LABELS:
            cells = [row for row in cells if row['state'] == selected]
        chosen_date = params.get('detail_date') or ''
        if chosen_date:
            cells = [row for row in cells if row['date'] == chosen_date]
        lock = params.get('lock') or ''
        if lock in ('locked', 'open'):
            cells = [row for row in cells if row['lock'] == lock]
        size = int(params.get('page_size') or 100)
        size = size if size in (10, 20, 50, 100) else 100
        pages = max(1, -(-len(cells) // size))
        page = min(max(1, int(params.get('page') or 1)), pages)
        result.update(rows=cells[(page - 1) * size:page * size], detail_total=len(cells), page=page, page_count=pages, page_size=size,
                      month=board['month'], today=board['today'], updated=board['updated'], labels=board['labels'],
                      departments=board['departments'], has_rule=board['has_rule'])
        return result

    @api.model
    def _tp_board_data(self, params=None, paginate=True):
        """Month matrix / day table for every internal employee (read-only, record rules apply)."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        today = local_today(DEFAULT_TZ)
        user = self.env.user
        processor = user.has_group(HR_MANAGER) or user.has_group(OFFICER)
        latest = self.search([('company_id', '=', company.id), ('work_date', '<=', today)], order='work_date desc', limit=1)
        anchor = latest.work_date or today
        mode = 'day' if params.get('mode') == 'day' else 'month'
        if mode == 'day':
            start = end = self._tp_parse_date(params.get('date')) or anchor
            month = start.strftime('%Y-%m')
        else:
            month = params.get('month') or anchor.strftime('%Y-%m')
            start, end = self._tp_month_range(month)
        dates = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]

        department_id = int(params.get('department_id') or 0)
        term = (params.get('search') or '').strip()
        Public = self.env['hr.employee.public']
        emp_domain = [('company_id', '=', company.id)]
        day_domain = [('company_id', '=', company.id), ('work_date', '>=', start), ('work_date', '<=', end)]
        if department_id:
            emp_domain.append(('department_id', 'child_of', department_id))
            day_domain.append(('department_id', 'child_of', department_id))
        if term:
            emp_domain += ['|', ('name', 'ilike', term), ('tp_employee_code', 'ilike', term)]
            day_domain += ['|', ('employee_name', 'ilike', term), ('employee_code', 'ilike', term)]
        batch_id = int(params.get('batch_id') or 0) if processor else 0
        days = self.search(day_domain)
        employees = Public.search(emp_domain, order='tp_employee_code, name')
        people = {emp.id: {'id': emp.id, 'code': emp.tp_employee_code or '', 'name': emp.name, 'department': emp.department_id.name or ''} for emp in employees}
        for day in days:
            people.setdefault(day.employee_id.id, {'id': day.employee_id.id, 'code': day.employee_code or '', 'name': day.employee_name or '',
                                                   'department': day.department_id.name or '', 'archived': True})
        if batch_id:
            batch_days = self.sudo().search([('id', 'in', days.ids), '|', ('session_ids.batch_id', '=', batch_id), ('issue_ids.batch_id', '=', batch_id)])
            days = days & self.browse(batch_days.ids)
            people = {key: value for key, value in people.items() if key in set(days.employee_id.ids)}
        cell, day_map = self._tp_cell_factory(company, days, start, end, today)
        rows = []
        for person in sorted(people.values(), key=lambda row: (row['code'] or 'ZZZ', row['name'])):
            cells = [cell(person['id'], work_date) for work_date in dates]
            totals = {state: sum(1 for item in cells if item['state'] == state) for state in CELL_LABELS}
            confirmed = [item for item in cells if item.get('units_state') == 'confirmed']
            totals.update(
                hours=round(sum(item.get('hours') or 0 for item in cells), 2),
                units=round(sum(day_map[person['id'], date.fromisoformat(item['date'])].units for item in confirmed), 2) if confirmed else None,
                unconfirmed=sum(1 for item in cells if item.get('day_id') and item.get('units_state') != 'confirmed'),
            )
            rows.append(dict(person, cells=cells, totals=totals))
        counts = {state: 0 for state in CELL_LABELS}
        for row in rows:
            for state in CELL_LABELS:
                counts[state] += row['totals'][state] if mode == 'month' else int(row['cells'][0]['state'] == state)
        state_filter = params.get('state') if params.get('state') in CELL_LABELS else ''
        lock_filter = params.get('lock') if params.get('lock') in ('open', 'locked') else ''
        if state_filter:
            rows = [row for row in rows if any(item['state'] == state_filter for item in row['cells'])]
        if lock_filter:
            rows = [row for row in rows if any(item['lock'] == lock_filter and item.get('day_id') for item in row['cells'])]
        page_size = int(params.get('page_size') or 100)
        page_size = page_size if page_size in (10, 20, 50, 100) else 100
        page_count = max(1, -(-len(rows) // page_size))
        page = min(max(1, int(params.get('page') or 1)), page_count)
        updated, applied = self._tp_updated(company)
        departments = self.env['hr.department'].search([('company_id', 'in', [company.id, False])]).sorted(lambda d: d.complete_name or '')
        return {
            'mode': mode, 'month': month, 'date': start.isoformat() if mode == 'day' else '', 'start': start.isoformat(),
            'end': end.isoformat(), 'today': today.isoformat(), 'anchor': anchor.isoformat(),
            'dates': [{'date': d.isoformat(), 'day': d.day, 'weekday': WEEKDAY_LABELS[d.weekday()], 'weekend': d.weekday() >= 5,
                       'future': d > today} for d in dates],
            'rows': rows[(page - 1) * page_size: page * page_size] if paginate else rows, 'total': len(rows), 'page': page, 'page_size': page_size,
            'page_count': page_count, 'counts': counts, 'labels': CELL_LABELS, 'updated': updated,
            'departments': [{'id': dept.id, 'name': dept.complete_name or dept.name} for dept in departments],
            'batches': [{'id': batch.id, 'name': batch.name} for batch in applied] if processor else [],
            'processor': processor,
            'can_import': self.env['tp.hr.attendance.batch']._tp_can_import(company),
            'has_rule': bool(self.env['tp.hr.attendance.rule'].sudo().search_count([('company_id', '=', company.id), ('state', '=', 'confirmed')])),
        }
