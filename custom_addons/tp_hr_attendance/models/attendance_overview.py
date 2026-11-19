"""Overview, sheet, person detail and own attendance (HR-ATTENDANCE-SIMPLE-002, DEC-055/056, ENTI-ATTENDANCE-002).

All screens read the same PostgreSQL data through ``_tp_presence``: canonical day summaries (ENTI API first,
approved corrections on top, older Excel imports as history), mapped device events and, only for days ENTI never
covered, the machine late totals per Excel source period. One main state per person and day and one meaning for
every figure (``attendance_figures``); nothing is invented — no 17:00 out, no leave from an empty cell, no 0 for
an unknown late value, and one punch is never an absence.
"""
import base64
from collections import defaultdict
from datetime import UTC, timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .attendance_common import (
    DEFAULT_TZ,
    HR_MANAGER,
    OFFICER,
    can,
    local_today,
    utc_to_local,
)
from .attendance_correction import clock_label
from .attendance_export import SOURCE_NAMES, build_attendance_book, person_note
from .attendance_export import legend as export_legend
from .attendance_figures import (
    ATTENTION,
    NO_HALF_DAY,
    STATUS_ORDER,
    UNDRAWN,
    absence_total,
    daily_late,
    distribution,
    late_of,
    late_text,
    late_total,
    no_punch_state,
    parse_hours,
    recent_people,
    week_of,
)
from .attendance_logic import (
    MINE_STATE_FILTERS,
    MINE_WEEKDAY_FILTERS,
    PRESENCE,
    WEEKDAY_FULL_LABELS,
    WEEKDAY_LABELS,
    dates_between,
    day_label,
    filter_mine_rows,
    mine_row_status,
    period_range,
    presence_from_day,
    presence_from_events,
    short_range,
    summarize_mine_rows,
)

PAGE_SIZES = (10, 20, 50, 100)
MAX_RANGE_DAYS = 62
SHEET_MODES = ('day', 'week', 'month', 'range')
OVERVIEW_MODES = SHEET_MODES
LEAVE = 'leave'
LABELS = dict(PRESENCE, leave='Nghỉ đã xác nhận')
STATE_ORDER = STATUS_ORDER
TABLE_FILTERS = ('attention', 'all', 'late', *STATUS_ORDER)
SOURCE_LABELS = {
    'excel': 'Excel máy chấm công (lịch sử)',
    'api': 'API máy chấm công',
    'enti': 'Tự động đồng bộ ENTI',
    'mixed': 'Tự động đồng bộ ENTI + lịch sử Excel',
    'none': 'Chưa có nguồn dữ liệu',
}
MINE_STATE_FILTER_LABELS = {
    'out_recorded': 'Đủ vào/ra',
    'working': 'Chờ ghi nhận giờ ra',
    'attention': 'Thiếu giờ / Cần kiểm tra',
    'missing_in': 'Thiếu giờ vào',
    'missing_out': 'Thiếu giờ ra',
    'review': 'Cần kiểm tra',
    'absent': 'Vắng theo lịch',
    'no_punch': 'Chưa chấm công',
    'rest': 'Nghỉ theo lịch',
    'no_source': 'Chưa có dữ liệu',
    'leave': 'Nghỉ đã xác nhận',
    'future': 'Ngày tương lai',
}
MINE_WEEKDAY_FILTER_LABELS = {
    'workdays': 'Thứ 2 – Thứ 6',
    'weekend': 'Thứ 7 – Chủ nhật',
    **{str(index): label for index, label in enumerate(WEEKDAY_FULL_LABELS)},
}
NO_LATE = 'Chưa có số liệu'
NO_EXACT = 'Chưa có tổng đúng kỳ'
ENTI_LATE_NOTE = 'Theo ENTI, cộng từng ngày'
NO_PUNCH_LATE_NOTE = 'Không có ngày có giờ chấm công trong kỳ'
RULE_NOTE = 'Đếm ngày vắng cả ngày theo quy tắc ca đã xác nhận; chưa tách buổi.'
DEFAULT_PLAN_NOTE = ('Chưa có quy tắc ca đã xác nhận: tạm coi Thứ 2 – Thứ 7 là ngày làm, giờ {hours}; '
                     'Chủ nhật là ngày nghỉ.')
STALE_AFTER = 600  # seconds without a successful ENTI read (during polling hours) before the strip warns
RECENT_LIMIT = 10


def range_label(start, end):
    """``09-15/11/2026``; the year is written once (twice only when the range crosses a year)."""
    label = short_range(start, end)
    return label if start.year != end.year else f'{label}/{end.year}'


def period_title(mode, start, end):
    if mode == 'day':
        return day_label(start)
    if mode == 'month':
        return f'Tháng {start:%m/%Y}'
    return range_label(start, end)


def _page(rows, params, default_size=20):
    size = int(params.get('page_size') or default_size)
    size = size if size in PAGE_SIZES else default_size
    count = max(1, -(-len(rows) // size))
    page = min(max(1, int(params.get('page') or 1)), count)
    return rows[(page - 1) * size:page * size], {'page': page, 'page_count': count, 'page_size': size, 'total': len(rows)}


def _stamp_ms(value):
    """Epoch milliseconds of a naive UTC datetime (for change highlighting in the browser)."""
    return int(value.replace(tzinfo=UTC).timestamp() * 1000) if value else 0


def _late_view(cover):
    """What a cell says about the Excel machine late total of one person for the viewed range."""
    if cover['state'] == 'exact':
        source = ' + '.join(piece['label'] for piece in cover['pieces'])
        return {'state': 'exact', 'count': cover['count'], 'minutes': cover['minutes'], 'text': '',
                'source': source, 'note': f'Excel máy · kỳ {source}'}
    hints = [hint['label'] for hint in cover['hints']]
    if cover['state'] == 'conflict':
        return {'state': 'conflict', 'count': None, 'minutes': None, 'text': f'{NO_EXACT} (các kỳ nguồn khác nhau)',
                'source': '', 'note': ''}
    if hints:
        return {'state': 'partial', 'count': None, 'minutes': None, 'source': '', 'note': '',
                'text': 'Số đi muộn có ở tổng kỳ ' + ', '.join(hints[:3]) + ('…' if len(hints) > 3 else '')}
    return {'state': 'none', 'count': None, 'minutes': None, 'text': NO_LATE, 'source': '', 'note': ''}


def late_view(total, cover=None):
    """One late answer for one person and exact range: ENTI day sums when every day is known, else an exact
    Excel period total, else the honest partial ENTI value (known days only, plus how many days are unknown)."""
    if total['state'] == 'exact' and total.get('real', True):
        return {'state': 'exact', 'count': total['count'], 'minutes': total['minutes'], 'text': '',
                'source': 'ENTI', 'note': ENTI_LATE_NOTE, 'unknown': 0}
    if cover and cover['state'] == 'exact':
        return dict(_late_view(cover), unknown=0)
    if total['state'] == 'exact':
        # Only days without any punch in the range: nobody can be late on them.
        return {'state': 'exact', 'count': 0, 'minutes': 0, 'text': '', 'source': '', 'unknown': 0,
                'note': NO_PUNCH_LATE_NOTE}
    if total['state'] == 'partial':
        return {'state': 'partial', 'count': None, 'minutes': None, 'source': 'ENTI', 'note': '',
                'unknown': total['unknown'], 'known_count': total['count'], 'known_minutes': total['minutes'],
                'text': f"{late_text(total)} · đã biết {total['count']} lần, {total['minutes']} phút"}
    view = _late_view(cover) if cover else {'state': 'none', 'count': None, 'minutes': None, 'text': NO_LATE,
                                            'source': '', 'note': ''}
    return dict(view, unknown=total['unknown'])


def _employee_value(employee, name):
    return employee[name] if name in employee._fields else False


class _Plan:
    """Working schedule and employment of the people in scope.

    A confirmed attendance rule decides working weekdays and the end of hours (a department rule wins over a
    company-wide one); without any confirmed rule Monday to Saturday are working days and the reference hours apply.
    Employment comes from the HR contract dates (no date = no limit).
    """

    def __init__(self, rules, employees, hours):
        self.rules = list(rules)
        self.department = {emp.id: emp.department_id for emp in employees}
        self.employment = {}
        for emp in employees:
            first = _employee_value(emp, 'first_contract_date') or _employee_value(emp, 'contract_date_start') or None
            last = _employee_value(emp, 'departure_date') or _employee_value(emp, 'contract_date_end') or None
            self.employment[emp.id] = (first, last)
        self.start_hour, self.default_end = hours
        self.has_rule = bool(self.rules)
        self._cache = {}

    def rule(self, employee_id, day):
        department = self.department.get(employee_id)
        key = (department.id if department else 0, day)
        if key not in self._cache:
            matched = [rule for rule in self.rules if rule.covers(day, department)]
            specific = [rule for rule in matched if rule.department_ids]
            self._cache[key] = (specific or matched or [None])[0]
        return self._cache[key]

    def scheduled(self, employee_id, day):
        rule = self.rule(employee_id, day)
        return bool(rule._weekday_on(day)) if rule else day.weekday() < 6

    def end_hour(self, employee_id, day):
        rule = self.rule(employee_id, day)
        return rule.end_hour if rule and rule.end_hour else self.default_end

    def employed(self, employee_id, day):
        first, last = self.employment.get(employee_id, (None, None))
        return (not first or day >= first) and (not last or day <= last)


class AttendanceDayOverview(models.Model):
    _inherit = 'tp.hr.attendance.day'

    # ------------------------------------------------------------- scope
    @api.model
    def _tp_period(self, params, modes=SHEET_MODES):
        mode = params.get('mode') if params.get('mode') in modes else 'day'
        today = local_today(DEFAULT_TZ)
        anchor = self._tp_parse_date(params.get('date')) or today
        if mode == 'range':
            start, end = self._tp_parse_date(params.get('from')), self._tp_parse_date(params.get('to'))
            if not start or not end or end < start:
                raise UserError(self.env._('Khoảng ngày không hợp lệ.'))
            if (end - start).days >= MAX_RANGE_DAYS:
                raise UserError(self.env._('Chỉ xem tối đa %(days)s ngày một lần.', days=MAX_RANGE_DAYS))
            anchor = start
        else:
            start, end = period_range(mode, anchor)
        return mode, anchor, start, end, today

    @api.model
    def _tp_people(self, company, department_id=0, term='', start=None, end=None):
        """Active HR employees of the company in scope (the KPI denominator), in the HR drag order (department
        order, then employee order inside it); with a range, archived people who still have day data in it are
        appended for the sheet (flagged ``archived``)."""
        Public = self.env['hr.employee.public']
        domain = [('company_id', '=', company.id)]
        if department_id:
            domain.append(('department_id', 'child_of', department_id))
        if term:
            domain += ['|', ('name', 'ilike', term), ('tp_employee_code', 'ilike', term)]
        found = Public.search(domain)
        rank = {}
        for emp in self.env['hr.employee'].sudo().browse(found.ids):
            department = emp.department_id
            rank[emp.id] = (not department, department.tp_sequence if department else 0, department.id or 0,
                            emp.sequence, emp.id)
        people = {}
        for emp in found.sorted(lambda record: rank.get(record.id, (True, 0, 0, 0, record.id))):
            people[emp.id] = {'id': emp.id, 'code': emp.tp_employee_code or '', 'name': emp.name or '',
                              'department': emp.department_id.name or '', 'department_id': emp.department_id.id or False,
                              'job': emp.job_title or emp.job_id.name or ''}
        if start and end:
            day_domain = [('company_id', '=', company.id), ('work_date', '>=', start), ('work_date', '<=', end),
                          ('employee_id', 'not in', list(people))]
            if department_id:
                day_domain.append(('department_id', 'child_of', department_id))
            if term:
                day_domain += ['|', ('employee_name', 'ilike', term), ('employee_code', 'ilike', term)]
            for day in self.search(day_domain, order='employee_code, employee_name, id'):
                people.setdefault(day.employee_id.id, {
                    'id': day.employee_id.id, 'code': day.employee_code or '', 'name': day.employee_name or '',
                    'department': day.department_id.name or '', 'department_id': day.department_id.id or False,
                    'job': '', 'archived': True})
        return people

    @api.model
    def _tp_leave_days(self, company, employee_ids, start, end):
        """``{(employee_id, date)}`` of HR-validated leave, or ``None`` when no leave source is installed."""
        if 'hr.leave' not in self.env:
            return None
        Leave = self.env['hr.leave'].sudo()
        result = set()
        start_dt = fields.Datetime.to_datetime(start) - timedelta(days=1)
        end_dt = fields.Datetime.to_datetime(end) + timedelta(days=2)
        for leave in Leave.search([('employee_id', 'in', list(employee_ids)), ('state', '=', 'validate'),
                                   ('date_from', '<=', end_dt), ('date_to', '>=', start_dt)]):
            first = utc_to_local(leave.date_from).date()
            last = utc_to_local(leave.date_to).date()
            for day in dates_between(max(first, start), min(last, end)):
                result.add((leave.employee_id.id, day))
        return result

    @api.model
    def _tp_reference_hours(self):
        return self.env['ir.config_parameter'].sudo().get_str('tp_hr_attendance.reference_hours') or '08:30-17:00'

    @api.model
    def _tp_rules(self, company, start, end):
        return self.env['tp.hr.attendance.rule'].sudo().search([
            ('company_id', '=', company.id), ('state', '=', 'confirmed'), ('date_from', '<=', end),
            '|', ('date_to', '=', False), ('date_to', '>=', start)], order='date_from desc, id desc')

    @api.model
    def _tp_plan(self, company, employee_ids, start, end):
        employees = self.env['hr.employee'].sudo().with_context(active_test=False).browse(list(employee_ids))
        return _Plan(self._tp_rules(company, start, end), employees, parse_hours(self._tp_reference_hours()))

    @api.model
    def _tp_absence_note(self, company, start, end):
        if self._tp_rules(company, start, end):
            return RULE_NOTE
        return f'{NO_HALF_DAY}. ' + DEFAULT_PLAN_NOTE.format(hours=self._tp_reference_hours())

    @api.model
    def _tp_presence(self, company, employee_ids, start, end, today):
        """``({(employee_id, date): cell}, has_leave_source)``; exactly one main state per person and day.

        A cell carries the shown clock times, the canonical day id, the ENTI late/early minutes of that same day
        (``None`` = unknown) and the UTC first-in/last-out instants used for the "newest marks" list. A day the
        sources cover without any punch is absent only when it is a finished scheduled working day inside the
        person's employment and not on approved leave (``no_punch_state``).
        """
        ids = list(employee_ids)
        result = {}
        leave = self._tp_leave_days(company, ids, start, end) if ids else None
        if not ids:
            return result, leave is not None
        days = self.search([('company_id', '=', company.id), ('employee_id', 'in', ids), ('work_date', '>=', start),
                            ('work_date', '<=', end)])
        day_map = {(day.employee_id.id, day.work_date): day for day in days}
        enti = {}
        for rec in self.env['tp.hr.attendance.enti.day'].sudo().search_fetch([
                ('company_id', '=', company.id), ('employee_id', 'in', ids), ('work_date', '>=', start),
                ('work_date', '<=', end), ('state', 'in', ('applied', 'locked_period', 'superseded_correction'))],
                ['employee_id', 'work_date', 'vao_dau', 'di_muon', 've_som']):
            enti[rec.employee_id.id, rec.work_date] = rec
        events = defaultdict(list)
        for event in self.env['tp.hr.attendance.event'].sudo().search([
                ('company_id', '=', company.id), ('employee_id', 'in', ids), ('state', '=', 'mapped'),
                ('local_date', '>=', start), ('local_date', '<=', end)], order='timestamp'):
            events[event.employee_id.id, event.local_date].append(
                {'at': event.timestamp, 'direction': event.direction, 'tz': event.tz})
        coverage = self.env['tp.hr.attendance.batch']._tp_coverage(company, start, end)
        plan = self._tp_plan(company, ids, start, end)
        now = utc_to_local(fields.Datetime.now())
        now_hour = now.hour + now.minute / 60
        for employee_id in ids:
            for work_date in dates_between(start, end):
                key = (employee_id, work_date)
                scheduled = plan.scheduled(employee_id, work_date)
                cell = {'in': '', 'out': '', 'source': '', 'day_id': False, 'late': None, 'early': None,
                        'in_at': None, 'out_at': None, 'scheduled': scheduled}
                day = day_map.get(key)
                rec = enti.get(key)
                punched = bool(day and (day.in_time or day.out_time or day.source_kind != 'enti'))
                if work_date > today:
                    cell['state'] = 'future'
                elif events.get(key):
                    punches = events[key]
                    cell['state'] = presence_from_events(punches, work_date == today)
                    ins = [punch for punch in punches if punch['direction'] == 'IN']
                    if ins:
                        cell['in'] = utc_to_local(ins[0]['at'], ins[0]['tz']).strftime('%H:%M')
                        cell['in_at'] = ins[0]['at']
                    if punches[-1]['direction'] == 'OUT':
                        cell['out'] = utc_to_local(punches[-1]['at'], punches[-1]['tz']).strftime('%H:%M')
                        cell['out_at'] = punches[-1]['at']
                    cell['source'] = 'api'
                elif punched:
                    cell.update(state=presence_from_day(day.data_state, day.in_time, day.out_time, work_date == today),
                                source=day.source_kind or 'excel', day_id=day.id, in_at=day.first_in or None,
                                out_at=day.last_out or None, **{'in': day.in_time or '', 'out': day.out_time or ''})
                    # ENTI late belongs to ENTI's own first-in; a corrected first-in makes it unknown.
                    if rec and (rec.vao_dau or '') == (day.in_time or ''):
                        cell['late'], cell['early'] = rec.di_muon or 0, rec.ve_som or 0
                elif day or rec or any(employee_id in people and first <= work_date <= last
                                       for first, last, people in coverage):
                    # A source covers the day and returned no punch at all.
                    finished = work_date < today or now_hour >= plan.end_hour(employee_id, work_date)
                    cell['state'] = no_punch_state(on_leave=bool(leave) and key in leave, scheduled=scheduled,
                                                   employed=plan.employed(employee_id, work_date), finished=finished)
                    if day:
                        cell.update(source=day.source_kind or 'excel', day_id=day.id)
                    elif rec:
                        cell['source'] = 'enti'
                elif leave and key in leave:
                    cell['state'] = LEAVE
                elif not plan.employed(employee_id, work_date):
                    cell['state'] = 'off'
                elif not scheduled:
                    cell['state'] = 'rest'
                else:
                    cell['state'] = 'no_source'
                cell['label'] = LABELS.get(cell['state'], '')
                result[key] = cell
        return result, leave is not None

    @api.model
    def _tp_late_views(self, company, people_ids, cells, start, end):
        """``{employee_id: late view}`` for exactly ``[start, end]`` (ENTI day sums, Excel period fallback)."""
        totals = {employee_id: late_total([cells[employee_id, day] for day in dates_between(start, end)
                                           if (employee_id, day) in cells]) for employee_id in people_ids}
        missing = [employee_id for employee_id, total in totals.items() if total['state'] != 'exact' or not total['real']]
        covers = self.env['tp.hr.attendance.late']._tp_cover(company, missing, start, end) if missing else {}
        return {employee_id: late_view(total, covers.get(employee_id)) for employee_id, total in totals.items()}

    @api.model
    def _tp_day_late_note(self, company, people, cells, day):
        """Where the late minutes of one day come from: ENTI day values, else the Excel period that holds them."""
        if any(cells[employee_id, day].get('late') is not None for employee_id in people):
            return ENTI_LATE_NOTE
        covers = self.env['tp.hr.attendance.late']._tp_cover(company, list(people), day, day) if people else {}
        hints = sorted({hint['label'] for cover in covers.values() for hint in cover['hints']})
        return ('Số đi muộn có ở tổng kỳ ' + ', '.join(hints[:3])) if hints else NO_LATE

    @api.model
    def _tp_absences(self, people_ids, cells, start, end, half_day_known=False):
        return {employee_id: absence_total([cells[employee_id, day] for day in dates_between(start, end)
                                            if (employee_id, day) in cells], half_day_known)
                for employee_id in people_ids}

    @api.model
    def _tp_source_strip(self, company, today):
        """Where the data comes from and how fresh it is; ENTI error details only for attendance processors."""
        updated, applied = self._tp_updated(company)
        Source = self.env['tp.hr.attendance.source'].sudo()
        sources = Source.search([('company_id', '=', company.id)])
        enti_sources = sources.filtered(lambda source: source.kind == 'enti_api')
        live = enti_sources.filtered(lambda source: source.live_enabled and source.state != 'paused')[:1]
        last_event = self.env['tp.hr.attendance.event'].sudo().search([('company_id', '=', company.id)],
                                                                      order='timestamp desc', limit=1)
        latest_enti = self.env['tp.hr.attendance.enti.day'].sudo().search(
            [('company_id', '=', company.id), ('work_date', '<=', today),
             '|', ('vao_dau', '!=', False), ('ra_cuoi', '!=', False)], order='work_date desc', limit=1).work_date
        if enti_sources:
            kind = 'mixed' if applied else 'enti'
        elif last_event:
            kind = 'mixed' if applied else 'api'
        else:
            kind = 'excel' if applied else 'none'
        tz_ctx = self.with_context(tz=self.env.user.tz or DEFAULT_TZ)

        def stamp(value, pattern='%H:%M:%S %d/%m/%Y'):
            return fields.Datetime.context_timestamp(tz_ctx, value).strftime(pattern) if value else ''

        latest_day = self.search([('company_id', '=', company.id), ('work_date', '<=', today)],
                                 order='work_date desc', limit=1).work_date
        latest_event = last_event.local_date if last_event and last_event.local_date <= today else None
        latest = max(filter(None, [latest_day, latest_event, latest_enti]), default=None)
        processor = self.env.user.has_group(HR_MANAGER) or self.env.user.has_group(OFFICER)
        health, error_at, error, poll = 'off', '', '', 0
        if live:
            poll = Source._tp_fast_settings()[0]
            error_newer = live.last_error_at and (not live.last_success_at or live.last_error_at > live.last_success_at)
            if error_newer:
                health = 'error'
                error_at = stamp(live.last_error_at)
                error = live.last_error if processor else 'Đồng bộ ENTI đang lỗi; dữ liệu đã có được giữ nguyên.'
            elif not live.last_success_at or (
                    live._tp_fast_hours() and (fields.Datetime.now() - live.last_success_at).total_seconds() > STALE_AFTER):
                health = 'stale'
            else:
                health = 'ok'
        last_success = (live or enti_sources[:1]).last_success_at if enti_sources else False
        return {
            'kind': kind, 'label': SOURCE_LABELS.get(kind, 'Chưa có nguồn'),
            'auto': bool(live), 'health': health, 'poll_seconds': poll,
            'updated_at': stamp(last_success) if last_success else (updated['at'] if updated else ''),
            'updated_ts': _stamp_ms(last_success),
            'error_at': error_at, 'error': error,
            'data_to': latest_enti.strftime('%d/%m/%Y') if latest_enti else (updated['to'] if updated else ''),
            'latest_date': latest.isoformat() if latest else '',
            'note': ('ENTI chỉ trả giờ vào đầu tiên và giờ ra cuối cùng mỗi ngày; Odoo không tự thêm lượt chấm.'
                     if enti_sources else
                     'Excel là ảnh chụp theo file đã nhập, không phải thời gian thực.' if applied else ''),
        }

    @api.model
    def _tp_departments(self, company):
        departments = self.env['hr.department'].search([('company_id', 'in', [company.id, False])], order='tp_sequence, id')
        return [{'id': dept.id, 'name': dept.complete_name or dept.name} for dept in departments]

    @api.model
    def _tp_file_periods(self, company, limit=12):
        """Distinct source periods of applied imports (newest first) for the "Kỳ theo file" picker."""
        seen = {}
        late = {(row.date_from.isoformat(), row.date_to.isoformat()) for row in self.env['tp.hr.attendance.late'].sudo().search_fetch(
            [('company_id', '=', company.id), ('state', '=', 'applied')], ['date_from', 'date_to'])}
        for batch in self.env['tp.hr.attendance.batch'].sudo().search(
                [('company_id', '=', company.id), ('state', 'in', ('applied', 'partial'))], order='period_to desc, id desc'):
            for sheet in batch.sheet_summary or []:
                if sheet.get('from') and sheet.get('to') and not sheet.get('errors'):
                    key = (sheet['from'], sheet['to'])
                    if key not in seen:
                        first, last = fields.Date.from_string(key[0]), fields.Date.from_string(key[1])
                        seen[key] = {'from': key[0], 'to': key[1], 'label': short_range(first, last), 'file': batch.file_name or '',
                                     'has_late': key in late}
        return sorted(seen.values(), key=lambda row: (row['to'], row['from']), reverse=True)[:limit]

    @api.model
    def _tp_flags(self, company):
        user = self.env.user
        return {
            'processor': user.has_group(HR_MANAGER) or user.has_group(OFFICER),
            'can_import': self.env['tp.hr.attendance.batch']._tp_can_import(company),
            'can_export': self._tp_can_export_shared(company),
            'reference_hours': self._tp_reference_hours(),
        }

    @api.model
    def _tp_can_export_shared(self, company, departments=None):
        if self.env.user.has_group(HR_MANAGER) or can(self.env, 'import', company):
            return True
        return departments is not None and bool(departments) and can(self.env, 'review', company, departments)

    # ------------------------------------------------------------ overview
    @api.model
    def _tp_recent(self, people, cells, dates, limit=RECENT_LIMIT):
        """Newest first-in/last-out marks: at most ``limit`` distinct people, newest punch first."""
        by_person = {employee_id: [cells[employee_id, day] for day in dates] for employee_id in people}
        rows = []
        for item in recent_people(by_person, limit):
            person, cell = people[item['employee_id']], item['cell']
            work_date = next(day for day in dates if cells[item['employee_id'], day] is cell)
            rows.append({
                'employee_id': person['id'], 'name': person['name'], 'code': person['code'],
                'department': person['department'],
                'avatar': f"/web/image/hr.employee.public/{person['id']}/avatar_128",
                'date': work_date.isoformat(), 'day_label': day_label(work_date),
                'in': cell['in'], 'out': cell['out'], 'kind': item['kind'],
                'kind_label': 'Ra' if item['kind'] == 'out' else 'Vào',
                'time': cell['out'] if item['kind'] == 'out' else cell['in'],
                'state': cell['state'], 'state_label': cell['label'],
                'missing': '' if cell['out'] else 'Chưa ghi nhận',
                'late': cell['late'], 'source': cell['source'],
                'stamp': _stamp_ms(item['at']),
                'key': f"{person['id']}:{work_date.isoformat()}:{item['kind']}:{_stamp_ms(item['at'])}",
            })
        return rows

    @api.model
    def tp_overview(self, params=None):
        """"Tổng quan chấm công" for one day / week / month / range. Period, department and name/code search
        scope everything (KPIs, donut, trend, newest marks, table); the status filter picks the table rows."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        mode, anchor, start, end, today = self._tp_period(params, OVERVIEW_MODES)
        department_id = int(params.get('department_id') or 0)
        term = (params.get('search') or '').strip()
        status = params.get('status') or params.get('drill') or 'attention'
        status = status if status in TABLE_FILTERS else 'attention'
        people = self._tp_people(company, department_id, term)
        ids = list(people)
        trend_start, trend_end = (week_of(anchor) if mode == 'day' else (start, end))
        span_start, span_end = min(start, trend_start), max(end, trend_end)
        cells, has_leave = self._tp_presence(company, ids, span_start, span_end, today)
        dates = dates_between(start, end)
        scope = [cells[employee_id, day] for employee_id in ids for day in dates]
        drawn = [cell for cell in scope if cell['state'] not in UNDRAWN]
        counts = distribution(drawn)
        total_drawn = sum(counts.values())
        statuses = [{'key': state, 'label': LABELS[state], 'value': counts[state],
                     'percent': round(counts[state] * 100 / total_drawn, 1) if total_drawn else 0}
                    for state in STATE_ORDER if counts[state] or state in ('out_recorded', 'missing')]
        late = late_total(scope)
        late_people = {employee_id for employee_id in ids for day in dates if (late_of(cells[employee_id, day]) or 0) > 0}
        absence_note = self._tp_absence_note(company, start, end)
        absence = absence_total(scope, half_day_known=absence_note == RULE_NOTE)
        per_day = mode == 'day'
        unit = 'người' if per_day else 'nhân viên-ngày'
        kpis = {
            'people': len(ids),
            'person_days': len(drawn),
            'unit': unit,
            'has_in': sum(1 for cell in drawn if cell['in']),
            'has_out': sum(1 for cell in drawn if cell['out']),
            'working': counts['working'],
            'attention': counts['missing'] + counts['review'],
            'missing': counts['missing'], 'review': counts['review'],
            'no_punch': counts['no_punch'], 'no_source': counts['no_source'],
            'late': {'state': late['state'], 'people': len(late_people), 'count': late['count'],
                     'minutes': late['minutes'], 'unknown': late['unknown'], 'text': late_text(late)},
            'absent': {'value': absence['days'], 'state': absence['state'], 'unknown': absence['unknown'],
                       'note': absence_note, 'rule': absence_note == RULE_NOTE},
            'leave': counts[LEAVE] if has_leave else None,
        }
        trend = []
        for work_date in dates_between(trend_start, trend_end):
            day_cells = [cells[employee_id, work_date] for employee_id in ids]
            day_drawn = [cell for cell in day_cells if cell['state'] not in UNDRAWN]
            minutes, late_count, complete = daily_late(day_cells)
            day_counts = distribution(day_drawn)
            trend.append({
                'date': work_date.isoformat(), 'label': f'{work_date:%d/%m}', 'weekday': WEEKDAY_LABELS[work_date.weekday()],
                'weekday_full': WEEKDAY_FULL_LABELS[work_date.weekday()], 'future': work_date > today,
                'is_today': work_date == today, 'selected': start <= work_date <= end, 'sunday': work_date.weekday() == 6,
                'people': len(day_drawn), 'has_in': sum(1 for cell in day_drawn if cell['in']),
                'has_out': sum(1 for cell in day_drawn if cell['out']),
                'attention': day_counts['missing'] + day_counts['review'], 'absent': day_counts['absent'],
                'late_minutes': minutes, 'late_people': late_count, 'late_complete': complete, 'counts': day_counts,
            })
        order = {employee_id: index for index, employee_id in enumerate(ids)}
        rows = []
        for work_date in reversed([day for day in dates if day <= today]):
            for employee_id in ids:
                cell = cells[employee_id, work_date]
                if cell['state'] in UNDRAWN:
                    continue
                if status == 'attention' and cell['state'] not in ATTENTION:
                    continue
                if status == 'late' and not (late_of(cell) or 0) > 0:
                    continue
                if status not in ('attention', 'all', 'late') and cell['state'] != status:
                    continue
                person = people[employee_id]
                rows.append({'employee_id': employee_id, 'name': person['name'], 'code': person['code'],
                             'department': person['department'], 'date': work_date.isoformat(),
                             'day_label': day_label(work_date), 'in': cell['in'], 'out': cell['out'],
                             'state': cell['state'], 'state_label': cell['label'], 'late': cell['late'],
                             'source': cell['source'], 'order': order[employee_id]})
        page_rows, pager = _page(rows, params, default_size=10)
        return dict({
            'mode': mode, 'date': anchor.isoformat(), 'start': start.isoformat(), 'end': end.isoformat(),
            'today': today.isoformat(), 'period_label': period_title(mode, start, end), 'unit': unit,
            'trend_label': (f'Tuần {range_label(trend_start, trend_end)}' if per_day else period_title(mode, start, end)),
            'future': start > today, 'includes_today': start <= today <= end,
            'department_id': department_id, 'search': term, 'status': status,
            'kpis': kpis, 'statuses': statuses, 'trend': trend,
            'recent': self._tp_recent(people, cells, dates),
            'rows': page_rows, 'labels': LABELS, 'has_leave_source': has_leave,
            'source': self._tp_source_strip(company, today), 'departments': self._tp_departments(company),
        }, **pager, **self._tp_flags(company))

    # --------------------------------------------------------------- sheet
    @api.model
    def tp_sheet(self, params=None):
        """Sheet: day → name/department/in/out/late; week/month/range → late and absence totals per person."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        mode, anchor, start, end, today = self._tp_period(params)
        department_id = int(params.get('department_id') or 0)
        term = (params.get('search') or '').strip()
        people = self._tp_people(company, department_id, term, start, end)
        ordered = list(people.values())
        result = {'mode': mode, 'date': anchor.isoformat(), 'start': start.isoformat(), 'end': end.isoformat(), 'today': today.isoformat(),
                  'labels': LABELS, 'departments': self._tp_departments(company), 'file_periods': self._tp_file_periods(company),
                  'source': self._tp_source_strip(company, today)}
        result.update(self._tp_flags(company))
        cells, _has_leave = self._tp_presence(company, people, start, end, today)
        if mode == 'day':
            state_filter = params.get('state') or ''
            rows = []
            for person in ordered:
                cell = cells[person['id'], start]
                if state_filter == 'attention' and cell['state'] not in ATTENTION:
                    continue
                if state_filter and state_filter != 'attention' and cell['state'] != state_filter:
                    continue
                rows.append(dict(person, date=start.isoformat(), day_label=day_label(start), **{'in': cell['in'], 'out': cell['out']},
                                 state=cell['state'], state_label=cell['label'], late_minutes=late_of(cell)))
            result.update(period_label=day_label(start), late_note=self._tp_day_late_note(company, people, cells, start),
                          state=state_filter)
        else:
            views = self._tp_late_views(company, list(people), cells, start, end)
            absence_note = self._tp_absence_note(company, start, end)
            absences = self._tp_absences(list(people), cells, start, end, absence_note == RULE_NOTE)
            rows = [dict(person, late=views[person['id']], absent=absences[person['id']]) for person in ordered]
            exact = [row for row in rows if row['late']['state'] == 'exact']
            sources = sorted({row['late']['note'] for row in exact if row['late']['note']})
            result.update(period_label=period_title(mode, start, end), late_source=' · '.join(sources),
                          late_summary={'people': len(exact), 'count': sum(row['late']['count'] for row in exact),
                                        'minutes': sum(row['late']['minutes'] for row in exact)} if exact else None,
                          absence_note=absence_note,
                          is_file_period=any(item['from'] == start.isoformat() and item['to'] == end.isoformat()
                                             for item in result['file_periods']))
        page_rows, pager = _page(rows, params)
        result.update(rows=page_rows, **pager)
        return result

    @api.model
    def _tp_person_data(self, company, person, start, end, today):
        cells, _has_leave = self._tp_presence(company, [person['id']], start, end, today)
        view = self._tp_late_views(company, [person['id']], cells, start, end)[person['id']]
        absence_note = self._tp_absence_note(company, start, end)
        absence = self._tp_absences([person['id']], cells, start, end, absence_note == RULE_NOTE)[person['id']]
        rows = []
        for work_date in dates_between(start, end):
            cell = cells[person['id'], work_date]
            rows.append({'date': work_date.isoformat(), 'day_label': day_label(work_date), 'in': cell['in'], 'out': cell['out'],
                         'state': cell['state'], 'state_label': cell['label'], 'weekend': work_date.weekday() >= 5,
                         'sunday': work_date.weekday() == 6, 'late': late_of(cell) if cell['state'] not in UNDRAWN else None,
                         'future': work_date > today, 'is_today': work_date == today})
        return {'employee': {key: person[key] for key in ('id', 'name', 'code', 'department')},
                'start': start.isoformat(), 'end': end.isoformat(), 'period_label': range_label(start, end),
                'late': view, 'absent': dict(absence, note=absence_note), 'rows': rows, 'today': today.isoformat(),
                'labels': LABELS}

    @api.model
    def tp_person(self, params=None):
        """Day times of one colleague for the viewed range (same shared read policy as the sheet)."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        mode, _anchor, start, end, today = self._tp_period(dict(params, mode=params.get('mode') or 'range'))
        if mode == 'day':
            start, end = period_range('week', start)
        employee_id = int(params.get('employee_id') or 0)
        people = self._tp_people(company, start=start, end=end)
        if employee_id not in people:
            raise UserError(self.env._('Không tìm thấy nhân viên trong công ty đang chọn.'))
        return self._tp_person_data(company, people[employee_id], start, end, today)

    # ----------------------------------------------------------- own view
    @api.model
    def _tp_mine_dataset(self, company, employee, params):
        """Build full personal attendance rows, period summary and filtered rows for the logged-in employee."""
        mode = params.get('mode') if params.get('mode') in ('week', 'month', 'range') else 'month'
        state_filter = (params.get('state') or '').strip()
        weekday_filter = str(params.get('weekday') or '').strip()
        if state_filter not in MINE_STATE_FILTERS or weekday_filter not in MINE_WEEKDAY_FILTERS:
            raise UserError(self.env._('Bộ lọc công cá nhân không hợp lệ.'))
        mode, _anchor, start, end, today = self._tp_period(dict(params, mode=mode))
        cells, has_leave = self._tp_presence(company, [employee.id], start, end, today)
        late = self._tp_late_views(company, [employee.id], cells, start, end)[employee.id]
        absence_note = self._tp_absence_note(company, start, end)
        absence = self._tp_absences([employee.id], cells, start, end, absence_note == RULE_NOTE)[employee.id]
        day_ids = [cell['day_id'] for cell in cells.values() if cell.get('day_id')]
        day_records = {day.id: day for day in self.browse(day_ids)} if day_ids else {}
        session_sources = dict(self.env['tp.hr.attendance.session']._fields['source'].selection)
        Correction = self.env['tp.hr.attendance.correction']
        request_states = dict(Correction._fields['state'].selection)
        requests = Correction.search([
            ('company_id', '=', company.id), ('employee_id', '=', employee.id),
            ('work_date', '>=', start), ('work_date', '<=', end),
        ])
        by_date_requests = defaultdict(list)
        for req in requests:
            by_date_requests[req.work_date].append({
                'id': req.id, 'name': req.name, 'state': req.state, 'state_label': request_states[req.state],
                'requested_in': clock_label(req.requested_in), 'requested_out': clock_label(req.requested_out),
                'review_note': req.review_note or '', 'is_amendment': req.is_amendment,
            })
        Period = self.env['tp.hr.attendance.period']
        locked_ranges = Period._tp_locked_ranges([company.id])
        tz_ctx = self.with_context(tz=self.env.user.tz or DEFAULT_TZ)
        all_rows = []
        for work_date in dates_between(start, end):
            cell = cells[employee.id, work_date]
            record = day_records.get(cell.get('day_id'))
            locked = Period._tp_is_locked(company.id, work_date, locked_ranges)
            sessions = []
            if record:
                for session in record.session_ids.sorted('check_in'):
                    sessions.append({
                        'in': utc_to_local(session.check_in).strftime('%H:%M') if session.check_in else '',
                        'out': utc_to_local(session.check_out).strftime('%H:%M') if session.check_out else '',
                        'hours': session.worked_hours,
                        'source': session.source,
                        'source_label': session_sources.get(session.source, ''),
                    })
            day_requests = by_date_requests.get(work_date, [])
            updated_at = ''
            if record and record.source_updated_at:
                stamp = fields.Datetime.context_timestamp(tz_ctx, record.source_updated_at)
                updated_at = stamp.strftime('%d/%m/%Y %H:%M')
            weekday_index = work_date.weekday()
            has_detail = bool(sessions or day_requests or locked or cell.get('source') or record)
            all_rows.append({
                'date': work_date.isoformat(),
                'day_label': day_label(work_date),
                'date_display': f'{work_date:%d/%m/%Y}',
                'weekday': WEEKDAY_LABELS[weekday_index],
                'weekday_full': WEEKDAY_FULL_LABELS[weekday_index],
                'weekday_index': weekday_index,
                'in': cell['in'],
                'out': cell['out'],
                'state': cell['state'],
                'state_label': cell['label'],
                'status_label': mine_row_status(cell['state'], cell['in'], cell['out']),
                'source': cell.get('source') or '',
                'late': late_of(cell) if cell['state'] not in UNDRAWN else None,
                'weekend': weekday_index >= 5,
                'sunday': weekday_index == 6,
                'future': work_date > today,
                'is_today': work_date == today,
                'lock_state': 'locked' if locked else 'open',
                'sessions': sessions,
                'requests': day_requests,
                'updated_at': updated_at,
                'has_detail': has_detail,
            })
        summary = summarize_mine_rows(all_rows)
        filtered_rows = filter_mine_rows(all_rows, state_filter, weekday_filter)
        return {
            'mode': mode, 'start': start, 'end': end, 'today': today,
            'has_leave_source': has_leave, 'late': late, 'absent': dict(absence, note=absence_note),
            'all_rows': all_rows, 'filtered_rows': filtered_rows, 'summary': summary,
            'applied_filters': {'state': state_filter, 'weekday': weekday_filter},
        }

    @api.model
    def tp_mine(self, params=None):
        """"Công của tôi": the employee always comes from the session user; client IDs are ignored."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        employee = self.env['tp.hr.attendance.correction']._tp_own_employee(company)
        today = local_today(DEFAULT_TZ)
        if not employee:
            return {'has_employee': False, 'today': today.isoformat(),
                    'message': self.env._('Tài khoản chưa gắn hồ sơ nhân viên trong công ty đang chọn; cần admin/HR gắn hồ sơ.')}
        dataset = self._tp_mine_dataset(company, employee, params)
        start, end = dataset['start'], dataset['end']
        page_rows, pager = _page(dataset['filtered_rows'], params, default_size=50)
        return dict({
            'has_employee': True,
            'employee': {
                'id': employee.id,
                'name': employee.name,
                'code': employee.tp_employee_code or '',
                'department': employee.department_id.name or '',
            },
            'mode': dataset['mode'],
            'date': start.isoformat(),
            'start': start.isoformat(),
            'end': end.isoformat(),
            'today': dataset['today'].isoformat(),
            'period_label': period_title(dataset['mode'], start, end),
            'range_display': f'{start:%d/%m/%Y} – {end:%d/%m/%Y}',
            'late': dataset['late'],
            'absent': dataset['absent'],
            'summary': dataset['summary'],
            'period_days': len(dataset['all_rows']),
            'has_leave_source': dataset['has_leave_source'],
            'applied_filters': dataset['applied_filters'],
            'reference_hours': self._tp_reference_hours(),
            'rows': page_rows,
            'labels': LABELS,
            'file_periods': self._tp_file_periods(company),
            'source': self._tp_source_strip(company, dataset['today']),
        }, **pager)

    # -------------------------------------------------------------- export
    @api.model
    def _tp_export_book(self, company, people, start, end, today, *, mode, scope, detail_dates=None, detail_note=''):
        """One "Bảng chấm công" workbook for ``people`` (ordered dicts of ``_tp_people``) over exactly
        ``[start, end]``: the same presence cells, late views and absences as the screens (``attendance_export``)."""
        ids = [person['id'] for person in people]
        cells, _has_leave = self._tp_presence(company, ids, start, end, today)
        views = self._tp_late_views(company, ids, cells, start, end)
        absence_note = self._tp_absence_note(company, start, end)
        absences = self._tp_absences(ids, cells, start, end, absence_note == RULE_NOTE)
        days = dates_between(start, end)
        groups, by_department = [], {}
        for person in people:
            key = person['department_id'] or 0
            if key not in by_department:
                by_department[key] = {'name': person['department'] or 'Chưa có phòng ban', 'people': []}
                groups.append(by_department[key])
            view, absence = views[person['id']], absences[person['id']]
            person_cells = {day: cells[person['id'], day] for day in days}
            exact = view['state'] == 'exact'
            by_department[key]['people'].append({
                'code': person['code'], 'name': person['name'], 'job': person.get('job') or '',
                'cells': person_cells, 'absent': absence['days'],
                'late': {'count': view['count'] if exact else None, 'minutes': view['minutes'] if exact else None},
                'note': person_note(person_cells, view, absence, person.get('archived', False)),
            })
        detail_rows = []
        for person in people:
            for day in days:
                cell = cells[person['id'], day]
                if day > today or cell['state'] in UNDRAWN or (detail_dates is not None and day not in detail_dates):
                    continue
                detail_rows.append({
                    'department': person['department'], 'code': person['code'], 'name': person['name'],
                    'job': person.get('job') or '', 'date': day, 'in': cell['in'], 'out': cell['out'],
                    'late': late_of(cell) if cell['in'] else '', 'state': cell['state'],
                    'state_label': mine_row_status(cell['state'], cell['in'], cell['out']),
                    'source': SOURCE_NAMES.get(cell.get('source'), ''),
                })
        tz_ctx = self.with_context(tz=self.env.user.tz or DEFAULT_TZ)
        exported = fields.Datetime.context_timestamp(tz_ctx, fields.Datetime.now())
        strip = self._tp_source_strip(company, today)
        synced = (f"Đồng bộ thành công lần cuối: {strip['updated_at']}" if strip['updated_at']
                  else 'Chưa có lần đồng bộ thành công')
        period = (f'Tháng {start:%m/%Y} · ' if mode == 'month' else '') + (
            f'Từ ngày {start:%d/%m/%Y} đến ngày {end:%d/%m/%Y} · {len(days)} ngày')
        report = {
            'company': company.name, 'title': 'BẢNG CHẤM CÔNG VÀO / RA', 'period': period, 'scope': scope,
            'stamp': f"Xuất lúc {exported:%d/%m/%Y %H:%M} · Nguồn: {strip['label']} · {synced}",
            'days': days, 'groups': groups,
            'legend': export_legend(f'{start:%d/%m/%Y} – {end:%d/%m/%Y}', self._tp_reference_hours(), absence_note),
            'detail': {'title': f'Chi tiết theo nhân viên / ngày · {start:%d/%m/%Y} – {min(end, today):%d/%m/%Y}'
                                f'{detail_note} · mỗi dòng một nhân viên một ngày, không gộp ô',
                       'rows': detail_rows},
        }
        content, _totals = build_attendance_book(report)
        return content

    @api.model
    def _tp_book_result(self, name, start, end, content):
        return {'filename': f'{name}-{start:%Y%m%d}-{end:%Y%m%d}.xlsx', 'data': base64.b64encode(content).decode()}

    @api.model
    def tp_export_sheet(self, params=None):
        """Shared export (whole filtered scope, never one page): HR manager, import assignee, or reviewer of every
        exported department only."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        mode, _anchor, start, end, today = self._tp_period(params)
        department_id = int(params.get('department_id') or 0)
        term = (params.get('search') or '').strip()
        people = self._tp_people(company, department_id, term, start, end)
        departments = self.env['hr.department'].browse({person['department_id'] for person in people.values() if person['department_id']})
        if not self._tp_can_export_shared(company, departments):
            raise AccessError(self.env._('Người chỉ đọc không xuất dữ liệu chung. HR hoặc người được giao xử lý công mới xuất.'))
        ordered = list(people.values())
        department = self.env['hr.department'].browse(department_id).exists() if department_id else None
        scope = ' · '.join(filter(None, [
            f'Phòng ban: {department.complete_name or department.name}' if department else 'Phạm vi: tất cả phòng ban',
            f'Tìm nhân viên: "{term}"' if term else '',
            f'{len(ordered)} nhân viên',
        ]))
        content = self._tp_export_book(company, ordered, start, end, today, mode=mode, scope=scope)
        self.env['tp.hr.attendance.log']._tp_log(self.env.company, 'sheet_export',
                                                 {'from': start, 'to': end, 'people': len(ordered), 'mode': mode})
        return self._tp_book_result('bang-cham-cong', start, end, content)

    @api.model
    def tp_export_mine(self, params=None):
        """Own attendance only (owner from the session, client ids ignored). The matrix covers the whole period;
        the state/weekday filters of the screen select the rows of the "Chi tiết" sheet (never only one page)."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        employee = self.env['tp.hr.attendance.correction']._tp_own_employee(company)
        if not employee:
            raise UserError(self.env._('Tài khoản chưa gắn hồ sơ nhân viên trong công ty đang chọn; cần admin/HR gắn hồ sơ.'))
        dataset = self._tp_mine_dataset(company, employee, params)
        start, end = dataset['start'], dataset['end']
        applied = dataset['applied_filters']
        filter_parts = []
        if applied['state']:
            filter_parts.append(f"Tình trạng: {MINE_STATE_FILTER_LABELS.get(applied['state'], applied['state'])}")
        if applied['weekday']:
            filter_parts.append(f"Ngày: {MINE_WEEKDAY_FILTER_LABELS.get(applied['weekday'], applied['weekday'])}")
        person = {'id': employee.id, 'code': employee.tp_employee_code or '', 'name': employee.name or '',
                  'department': employee.department_id.name or '', 'department_id': employee.department_id.id or False,
                  'job': employee.job_title or employee.job_id.name or ''}
        filtered = {fields.Date.to_date(row['date']) for row in dataset['filtered_rows']}
        content = self._tp_export_book(
            company, [person], start, end, dataset['today'], mode=dataset['mode'],
            scope=f"Công của tôi: {person['name']}" + (f" ({person['code']})" if person['code'] else ''),
            detail_dates=filtered if filter_parts else None,
            detail_note=(' · Bộ lọc: ' + '; '.join(filter_parts)) if filter_parts else '')
        return self._tp_book_result('cong-cua-toi', start, end, content)
