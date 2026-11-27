"""Overview, sheet, person detail and own attendance (HR-ATTENDANCE-SIMPLE-002, DEC-055/056, ENTI-ATTENDANCE-002).

All screens read the same PostgreSQL data through ``_tp_presence``: canonical day summaries (ENTI API first,
approved corrections on top, older Excel imports as history), mapped device events and, only for days ENTI never
covered, the machine late totals per Excel source period. One main state per person and day and one meaning for
every figure (``attendance_figures``); nothing is invented — no 17:00 out, no leave from an empty cell, no 0 for
an unknown late value, and one punch is never an absence.
"""
import base64
import json
from collections import defaultdict
from datetime import UTC, datetime, time, timedelta

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
from .attendance_export import (
    build_attendance_book,
    export_late_totals,
    person_note,
    worked_days_count,
)
from .attendance_figures import (
    ATTENTION,
    GROUP_HINTS,
    GROUP_KEYS,
    GROUP_LABELS,
    NO_HALF_DAY,
    STATUS_ORDER,
    UNDRAWN,
    UNKNOWN_REASONS,
    absence_total,
    class_date,
    clock_has_seconds,
    daily_late,
    day_group,
    distribution,
    fold_text,
    group_counts,
    late_of,
    late_text,
    late_total,
    no_punch_state,
    parse_hours,
    recent_marks,
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
BG_STALE_AFTER = 2400  # seconds without a successful ENTI read outside fast hours before warning
RECENT_LIMIT = 10
GROUP_PAGE_SIZES = (10, 20, 50, 100)
RECENT_TITLES = {
    'events': ('10 lượt chấm công gần nhất', 'Mỗi dòng là một lượt chấm công do nguồn ghi nhận, mới nhất ở trên.'),
    'daily': ('Chấm công gần nhất', 'Hiển thị các mốc chấm công nguồn hiện cung cấp'),
}


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


def _page(rows, params, default_size=100, sizes=PAGE_SIZES):
    size = int(params.get('page_size') or default_size)
    size = size if size in sizes else default_size
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
        """``{(employee_id, date): label}`` of approved leave / business trip, or ``None`` when no source exists."""
        has_hr_leave = 'hr.leave' in self.env
        has_tp_request = 'tp.request' in self.env
        if not has_hr_leave and not has_tp_request:
            return None
        ids = list(employee_ids)
        result = {}
        if not ids:
            return result
        if has_hr_leave:
            Leave = self.env['hr.leave'].sudo()
            start_dt = fields.Datetime.to_datetime(start) - timedelta(days=1)
            end_dt = fields.Datetime.to_datetime(end) + timedelta(days=2)
            for leave in Leave.search([
                ('employee_id', 'in', ids), ('state', '=', 'validate'),
                ('date_from', '<=', end_dt), ('date_to', '>=', start_dt),
            ]):
                first = utc_to_local(leave.date_from).date()
                last = utc_to_local(leave.date_to).date()
                for day in dates_between(max(first, start), min(last, end)):
                    result[leave.employee_id.id, day] = 'Nghỉ đã xác nhận'
        if has_tp_request:
            Request = self.env['tp.request'].sudo()
            for req in Request.search([
                ('company_id', '=', company.id),
                ('requester_employee_id', 'in', ids),
                ('approval_state', '=', 'approved'),
                ('handler_kind', 'in', ('leave_request', 'business_trip')),
                ('leave_date_from', '!=', False),
                ('leave_date_to', '!=', False),
                ('leave_date_from', '<=', end),
                ('leave_date_to', '>=', start),
            ]):
                label = 'Công tác đã duyệt' if req.handler_kind == 'business_trip' else 'Nghỉ phép đã duyệt'
                first = max(req.leave_date_from, start)
                last = min(req.leave_date_to, end)
                if first <= last:
                    for day in dates_between(first, last):
                        result[req.requester_employee_id.id, day] = label
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
        (``None`` = unknown), the UTC first-in/last-out instants used for the newest marks, ``covered`` (a source
        answered for that person and day) and, for device events, the ``punches`` themselves. A day the
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
                {'id': event.id, 'at': event.timestamp, 'direction': event.direction, 'tz': event.tz})
        coverage = self.env['tp.hr.attendance.batch']._tp_coverage(company, start, end)
        plan = self._tp_plan(company, ids, start, end)
        now = utc_to_local(fields.Datetime.now())
        now_hour = now.hour + now.minute / 60
        for employee_id in ids:
            for work_date in dates_between(start, end):
                key = (employee_id, work_date)
                scheduled = plan.scheduled(employee_id, work_date)
                leave_label = (
                    leave.get(key, '') if isinstance(leave, dict)
                    else ('Nghỉ đã xác nhận' if (leave and key in leave) else '')
                )
                cell = {'in': '', 'out': '', 'source': '', 'day_id': False, 'late': None, 'early': None,
                        'in_at': None, 'out_at': None, 'scheduled': scheduled, 'covered': False,
                        'leave_note': '', 'conflict_note': ''}
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
                    cell.update(source='api', covered=True, punches=punches)
                    if leave_label and (cell['in'] or cell['out']):
                        cell['state'] = 'review'
                        cell['conflict_note'] = (
                            f"Xung đột: có {leave_label.lower()} nhưng vẫn ghi nhận giờ chấm máy "
                            f"({cell['in'] or '—'}–{cell['out'] or '—'})."
                        )
                elif punched:
                    src_kind = day.source_kind or 'excel'
                    cell.update(state=presence_from_day(day.data_state, day.in_time, day.out_time, work_date == today),
                                source=src_kind, day_id=day.id, in_at=day.first_in or None,
                                out_at=day.last_out or None, covered=True,
                                **{'in': day.in_time or '', 'out': day.out_time or ''})
                    # ENTI late belongs to ENTI's own first-in; a corrected first-in makes it unknown.
                    if rec and (rec.vao_dau or '') == (day.in_time or ''):
                        cell['late'], cell['early'] = rec.di_muon or 0, rec.ve_som or 0
                    if leave_label and src_kind != 'correction' and (cell['in'] or cell['out']):
                        cell['state'] = 'review'
                        cell['conflict_note'] = (
                            f"Xung đột: có {leave_label.lower()} nhưng vẫn ghi nhận giờ chấm máy "
                            f"({cell['in'] or '—'}–{cell['out'] or '—'})."
                        )
                elif day or rec or any(employee_id in people and first <= work_date <= last
                                       for first, last, people in coverage):
                    # A source covers the day and returned no punch at all.
                    cell['covered'] = True
                    finished = work_date < today or now_hour >= plan.end_hour(employee_id, work_date)
                    cell['state'] = no_punch_state(on_leave=bool(leave_label), scheduled=scheduled,
                                                   employed=plan.employed(employee_id, work_date), finished=finished)
                    if cell['state'] == LEAVE and leave_label:
                        cell['leave_note'] = leave_label
                    if day:
                        cell.update(source=day.source_kind or 'excel', day_id=day.id)
                    elif rec:
                        cell['source'] = 'enti'
                elif leave_label:
                    cell['state'] = LEAVE
                    cell['leave_note'] = leave_label
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
        tz_name = (live or enti_sources[:1]).timezone if enti_sources else DEFAULT_TZ
        tz_ctx = self.with_context(tz=tz_name or DEFAULT_TZ)

        def stamp(value, pattern='%H:%M:%S %d/%m/%Y'):
            return fields.Datetime.context_timestamp(tz_ctx, value).strftime(pattern) if value else ''

        latest_day = self.search([('company_id', '=', company.id), ('work_date', '<=', today)],
                                 order='work_date desc', limit=1).work_date
        latest_event = last_event.local_date if last_event and last_event.local_date <= today else None
        latest = max(filter(None, [latest_day, latest_event, latest_enti]), default=None)
        processor = self.env.user.has_group(HR_MANAGER) or self.env.user.has_group(OFFICER) or self.env.user.has_group('base.group_system')
        cron = self.env.ref('tp_hr_attendance.ir_cron_enti_attendance_sync', raise_if_not_found=False)
        cron_active = True if not cron else bool(cron.sudo().active)
        health, error_at, error, poll = 'off', '', '', 0
        if live and cron_active:
            poll = Source._tp_fast_settings()[0]
            error_newer = live.last_error_at and (not live.last_success_at or live.last_error_at > live.last_success_at)
            if error_newer:
                health = 'error'
                error_at = stamp(live.last_error_at)
                error = live.last_error if processor else 'Đồng bộ tự động đang gián đoạn; dữ liệu đã có được giữ nguyên.'
            elif not live.last_success_at:
                health = 'stale'
            else:
                age = (fields.Datetime.now() - live.last_success_at).total_seconds()
                stale_limit = STALE_AFTER if live._tp_fast_hours() else BG_STALE_AFTER
                health = 'stale' if age > stale_limit else 'ok'
        elif live and not cron_active:
            health = 'off'
        last_success = (live or enti_sources[:1]).last_success_at if enti_sources else False
        return {
            'kind': kind, 'label': SOURCE_LABELS.get(kind, 'Chưa có nguồn'),
            'connected': bool(enti_sources), 'auto': bool(live and cron_active), 'cron_active': cron_active,
            'health': health, 'poll_seconds': poll,
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
    @staticmethod
    def _tp_live_ok(strip, day, today):
        """False when ENTI is actively failing, or on today while a connected live source is paused/stale:
        a person without any mark is then "not determined", never "not started"."""
        if strip.get('connected') and strip.get('health') == 'error':
            return False
        return day != today or not strip.get('connected') or (strip['auto'] and strip['health'] == 'ok')

    @api.model
    def _tp_group_basis(self, mode, start, end, today):
        if mode == 'day':
            return 'day'
        if start <= today <= end:
            return 'today'
        return 'start' if start > today else 'latest'

    @api.model
    def _tp_groups(self, people, cells, day, today, strip, basis='day'):
        """Dashboard groups of the people in scope for one classification day (one group per person)."""
        live_ok = self._tp_live_ok(strip, day, today)
        counts, reasons, excluded = group_counts([cells[employee_id, day] for employee_id in people
                                                  if (employee_id, day) in cells], live_ok)
        notes = {
            'today': 'Thẻ tính theo hôm nay',
            'latest': 'Thẻ tính theo ngày gần nhất có chấm công trong kỳ',
            'start': 'Kỳ chưa đến; thẻ tính theo ngày đầu kỳ',
        }
        return {
            'date': day.isoformat(), 'date_label': day_label(day), 'is_today': day == today, 'basis': basis,
            'note': notes.get(basis, ''), 'people': len(people), 'total': sum(counts.values()), 'counts': counts,
            'reasons': {key: value for key, value in reasons.items() if value}, 'reason_labels': UNKNOWN_REASONS,
            'excluded': excluded, 'live_ok': live_ok, 'labels': GROUP_LABELS, 'hints': GROUP_HINTS,
        }

    @api.model
    def _tp_mark_seconds(self, company, employee_ids, day):
        """``{employee_id: (in has seconds, out has seconds)}`` from the raw source clocks of one day.

        Server side only: the raw payload is read here and never returned. A clock the source gave as ``HH:MM``
        has no seconds, so none are shown (never an invented ``:00``)."""
        result = {}
        if not employee_ids:
            return result
        for rec in self.env['tp.hr.attendance.enti.day'].sudo().search_fetch([
                ('company_id', '=', company.id), ('employee_id', 'in', list(employee_ids)), ('work_date', '=', day),
                ('state', 'in', ('applied', 'locked_period'))], ['employee_id', 'raw_json']):
            try:
                raw = json.loads(rec.raw_json or '{}')
            except ValueError:
                raw = {}
            if isinstance(raw, dict):
                result[rec.employee_id.id] = (clock_has_seconds(raw.get('vaoDau')), clock_has_seconds(raw.get('raCuoi')))
        return result

    @api.model
    def _tp_recent(self, company, people, cells, day, limit=RECENT_LIMIT):
        """Newest marks of one day, newest first: one row per mark the source really gives — every device punch
        when punches exist, else the day's first in and last out. Seconds only when the source has them; the
        place only when a source gives one (none does yet: ``''``). Never sorted by sync/receive times."""
        order = {employee_id: index for index, employee_id in enumerate(people)}
        day_cells = {employee_id: cells[employee_id, day] for employee_id in people if (employee_id, day) in cells}
        seconds = self._tp_mark_seconds(company, [employee_id for employee_id, cell in day_cells.items()
                                                  if cell['source'] == 'enti' and (cell['in'] or cell['out'])], day)
        marks = []
        for employee_id, cell in day_cells.items():
            if cell['state'] in UNDRAWN:
                continue
            if cell.get('punches'):
                for punch in cell['punches']:
                    local = utc_to_local(punch['at'], punch['tz'])
                    marks.append({'key': f"e{punch['id']}", 'employee_id': employee_id, 'event': True,
                                  'kind': 'in' if punch['direction'] == 'IN' else 'out', 'at': local,
                                  'time': local.strftime('%H:%M:%S' if local.second else '%H:%M'),
                                  'order': order[employee_id]})
                continue
            exact = seconds.get(employee_id, (False, False)) if cell['source'] == 'enti' else (False, False)
            for kind, instant, clock, precise in (('in', cell['in_at'], cell['in'], exact[0]),
                                                  ('out', cell['out_at'], cell['out'], exact[1])):
                if not clock:
                    continue
                local = utc_to_local(instant) if instant else None
                if not local or local.strftime('%H:%M') != clock:
                    hour, minute = (int(part) for part in clock.split(':')[:2])
                    local, precise = datetime.combine(day, time(hour, minute)), False
                marks.append({'key': f'{employee_id}:{day.isoformat()}:{kind}', 'employee_id': employee_id,
                              'event': False, 'kind': kind, 'at': local,
                              'time': local.strftime('%H:%M:%S') if precise else clock, 'order': order[employee_id]})
        rows = []
        for mark in recent_marks(marks, limit):
            person = people[mark['employee_id']]
            rows.append({'key': f"{mark['key']}:{mark['time']}", 'employee_id': person['id'], 'code': person['code'],
                         'name': person['name'], 'time': mark['time'], 'kind': mark['kind'], 'location': ''})
        mode = 'events' if marks and all(mark['event'] for mark in marks) else 'daily'
        title, hint = RECENT_TITLES[mode]
        return rows, {'mode': mode, 'title': title, 'hint': hint, 'date': day.isoformat(), 'date_label': day_label(day)}

    @api.model
    def tp_overview_group(self, params=None):
        """People of one dashboard group (Đang làm / Đã về / Chưa đi làm / Chưa xác định) on the classification day
        of the dashboard scope, with the dialog's own name/code search, department filter and paging.

        Same read policy, scope and classification as ``tp_overview``: before the dialog's own filters the list
        total is the card number. Rows never link to HR profiles and carry no private HR data."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        mode, _anchor, start, end, today = self._tp_period(params, OVERVIEW_MODES)
        department_id = int(params.get('department_id') or 0)
        term = (params.get('search') or '').strip()
        group = params.get('group') if params.get('group') in GROUP_KEYS else 'working'
        people = self._tp_people(company, department_id, term)
        ids = list(people)
        day = self._tp_parse_date(params.get('class_date'))
        if not day or not start <= day <= end:
            span, _has_leave = self._tp_presence(company, ids, start, end, today)
            marked = {work_date for (_employee_id, work_date), cell in span.items() if cell['in'] or cell['out']}
            day = class_date(start, end, today, marked)
        cells, _has_leave = self._tp_presence(company, ids, day, day, today)
        strip = self._tp_source_strip(company, today)
        summary = self._tp_groups(people, cells, day, today, strip, self._tp_group_basis(mode, start, end, today))
        members = []
        for employee_id in ids:
            found, reason = day_group(cells[employee_id, day], summary['live_ok'])
            if found == group:
                members.append((employee_id, reason))
        departments = {}
        for employee_id, _reason in members:
            person = people[employee_id]
            key = person['department_id'] or -1
            entry = departments.setdefault(key, {'id': key, 'name': person['department'] or 'Chưa có phòng ban', 'count': 0})
            entry['count'] += 1
        dept = int(params.get('dept') or 0)
        dept = dept if dept in departments else 0
        query = fold_text((params.get('q') or '').strip())
        rows = []
        for employee_id, reason in members:
            person, cell = people[employee_id], cells[employee_id, day]
            if dept and (person['department_id'] or -1) != dept:
                continue
            if query and query not in fold_text(person['name']) and query not in fold_text(person['code']):
                continue
            if group == 'working':
                note = 'Chưa ghi nhận giờ ra' if day == today else 'Thiếu giờ ra'
            elif group == 'done':
                note = 'Thiếu giờ vào' if not cell['in'] else ('Cần kiểm tra' if cell['state'] == 'review' else '')
            else:
                note = UNKNOWN_REASONS.get(reason, '')
            rows.append({'stt': len(rows) + 1, 'employee_id': employee_id, 'code': person['code'], 'name': person['name'],
                         'department': person['department'], 'date': day.isoformat(), 'in': cell['in'],
                         'out': cell['out'], 'note': note})
        page_rows, pager = _page(rows, params, default_size=20, sizes=GROUP_PAGE_SIZES)
        return dict({
            'group': group, 'label': GROUP_LABELS[group], 'hint': GROUP_HINTS[group], 'class_date': day.isoformat(),
            'date_label': day_label(day), 'is_today': day == today, 'group_total': len(members),
            'counts': summary['counts'], 'reasons': summary['reasons'], 'live_ok': summary['live_ok'],
            'departments': sorted(departments.values(), key=lambda entry: (entry['id'] == -1, entry['name'])),
            'dept': dept, 'q': (params.get('q') or '').strip(), 'rows': page_rows, 'sizes': list(GROUP_PAGE_SIZES),
            'updated_at': strip['updated_at'], 'health': strip['health'],
        }, **pager)

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
        strip = self._tp_source_strip(company, today)
        marked = {day for day in dates if any(cells[employee_id, day]['in'] or cells[employee_id, day]['out']
                                              for employee_id in ids)}
        group_day = class_date(start, end, today, marked)
        groups = self._tp_groups(people, cells, group_day, today, strip, self._tp_group_basis(mode, start, end, today))
        recent, recent_info = self._tp_recent(company, people, cells, group_day)
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
            day_groups = group_counts(day_cells, self._tp_live_ok(strip, work_date, today))[0]
            trend.append({
                'date': work_date.isoformat(), 'label': f'{work_date:%d/%m}', 'weekday': WEEKDAY_LABELS[work_date.weekday()],
                'weekday_full': WEEKDAY_FULL_LABELS[work_date.weekday()], 'future': work_date > today,
                'is_today': work_date == today, 'selected': start <= work_date <= end, 'sunday': work_date.weekday() == 6,
                'people': len(day_drawn), 'has_in': sum(1 for cell in day_drawn if cell['in']),
                'has_out': sum(1 for cell in day_drawn if cell['out']),
                'attention': day_counts['missing'] + day_counts['review'], 'absent': day_counts['absent'],
                'late_minutes': minutes, 'late_people': late_count, 'late_complete': complete, 'counts': day_counts,
                'groups': day_groups, 'group_day': work_date == group_day,
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
        page_rows, pager = _page(rows, params, default_size=100)
        return dict({
            'mode': mode, 'date': anchor.isoformat(), 'start': start.isoformat(), 'end': end.isoformat(),
            'today': today.isoformat(), 'period_label': period_title(mode, start, end), 'unit': unit,
            'trend_label': (f'Tuần {range_label(trend_start, trend_end)}' if per_day else period_title(mode, start, end)),
            'future': start > today, 'includes_today': start <= today <= end,
            'department_id': department_id, 'search': term, 'status': status,
            'kpis': kpis, 'statuses': statuses, 'trend': trend, 'groups': groups,
            'recent': recent, 'recent_info': recent_info,
            'rows': page_rows, 'labels': LABELS, 'has_leave_source': has_leave,
            'source': strip, 'departments': self._tp_departments(company),
        }, **pager, **self._tp_flags(company))

    # --------------------------------------------------------------- sheet
    @api.model
    def _tp_sheet_codes(self, company, employee_ids):
        # Only device IDs for an already-authorized employee scope, never raw ENTI identities.
        codes = defaultdict(list)
        for code in self.env['tp.hr.attendance.code'].sudo().search([
            ('company_id', '=', company.id), ('employee_id', 'in', employee_ids),
        ]):
            codes[code.employee_id.id].append(code.machine_code)
        return {employee_id: ' / '.join(values) for employee_id, values in codes.items()}

    @staticmethod
    def _tp_filter_sheet_people(ordered, cells, start, end, state_filter):
        """Filter employee rows on Bảng chấm công & Excel export across single-day and multi-day modes."""
        if not state_filter or not ordered:
            return ordered
        days = dates_between(start, end)
        if state_filter == 'attention':
            return [person for person in ordered if any(cells[person['id'], day]['state'] in ATTENTION for day in days)]
        return [person for person in ordered if any(cells[person['id'], day]['state'] == state_filter for day in days)]

    @api.model
    def tp_sheet(self, params=None):
        """Canonical Vào/Ra matrix, paginated by employee after applying the full server-side filter."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        mode, anchor, start, end, today = self._tp_period(params)
        department_id = int(params.get('department_id') or 0)
        term = (params.get('search') or '').strip()
        state_filter = (params.get('state') or '').strip()
        people = self._tp_people(company, department_id, term, start, end)
        ordered = list(people.values())
        result = {'mode': mode, 'date': anchor.isoformat(), 'start': start.isoformat(), 'end': end.isoformat(), 'today': today.isoformat(),
                  'labels': LABELS, 'departments': self._tp_departments(company), 'file_periods': self._tp_file_periods(company),
                  'source': self._tp_source_strip(company, today), 'state': state_filter}
        result.update(self._tp_flags(company))
        cells, has_leave = self._tp_presence(company, people, start, end, today)
        result['has_leave_source'] = has_leave
        filtered_people = self._tp_filter_sheet_people(ordered, cells, start, end, state_filter)
        if mode == 'day':
            rows = []
            for person in filtered_people:
                cell = cells[person['id'], start]
                rows.append(dict(person, date=start.isoformat(), day_label=day_label(start), **{'in': cell['in'], 'out': cell['out']},
                                 state=cell['state'], state_label=cell['label'], late_minutes=late_of(cell)))
            result.update(period_label=day_label(start), late_note=self._tp_day_late_note(company, people, cells, start))
        else:
            views = self._tp_late_views(company, list(people), cells, start, end)
            absence_note = self._tp_absence_note(company, start, end)
            absences = self._tp_absences(list(people), cells, start, end, absence_note == RULE_NOTE)
            rows = [dict(person, late=views[person['id']], absent=absences[person['id']]) for person in filtered_people]
            exact = [row for row in rows if row['late']['state'] == 'exact']
            sources = sorted({row['late']['note'] for row in exact if row['late']['note']})
            result.update(period_label=period_title(mode, start, end), late_source=' · '.join(sources),
                          late_summary={'people': len(exact), 'count': sum(row['late']['count'] for row in exact),
                                        'minutes': sum(row['late']['minutes'] for row in exact)} if exact else None,
                          absence_note=absence_note,
                          is_file_period=any(item['from'] == start.isoformat() and item['to'] == end.isoformat()
                                             for item in result['file_periods']))
        page_rows, pager = _page(rows, params)
        days = dates_between(start, end)
        views = self._tp_late_views(company, list(people), cells, start, end) if mode == 'day' else views
        absence_note = self._tp_absence_note(company, start, end)
        absences = self._tp_absences(list(people), cells, start, end, absence_note == RULE_NOTE) if mode == 'day' else absences
        codes = self._tp_sheet_codes(company, [row['id'] for row in page_rows])
        serials = defaultdict(int)
        for row in rows:
            serials[row['department_id']] += 1
            row['stt'] = serials[row['department_id']]
        for row in page_rows:
            row.update(machine_code=codes.get(row['id'], ''), late=views[row['id']], absent=absences[row['id']],
                       cells=[{'date': day.isoformat(), **{key: cells[row['id'], day][key]
                                                          for key in ('in', 'out', 'state', 'label', 'late', 'leave_note', 'conflict_note')}}
                              for day in days])
        result.update(day_columns=[{'date': day.isoformat(), 'label': str(day.day),
                                    'weekday': WEEKDAY_LABELS[day.weekday()], 'weekend': day.weekday() >= 5}
                                   for day in days], absence_note=absence_note)
        result.update(rows=page_rows, **pager)
        return result

    @api.model
    def _tp_person_data(self, company, person, start, end, today):
        cells, _has_leave = self._tp_presence(company, [person['id']], start, end, today)
        view = self._tp_late_views(company, [person['id']], cells, start, end)[person['id']]
        absence_note = self._tp_absence_note(company, start, end)
        absence = self._tp_absences([person['id']], cells, start, end, absence_note == RULE_NOTE)[person['id']]
        rows = []
        ordered_dates = sorted(
            dates_between(start, end),
            key=lambda d: (d > today, -d.toordinal() if d <= today else d.toordinal()),
        )
        for work_date in ordered_dates:
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
                'requested_in_float': req.requested_in, 'requested_out_float': req.requested_out,
                'reason': req.reason or '', 'evidence_name': req.evidence_name or '',
                'has_evidence': bool(req.evidence_file),
                'review_note': req.review_note or '', 'is_amendment': req.is_amendment,
                'withdraw_reason': req.withdraw_reason or '',
                'withdrawn_at': fields.Datetime.context_timestamp(
                    self.with_context(tz=DEFAULT_TZ), req.withdrawn_at,
                ).strftime('%d/%m/%Y %H:%M') if req.withdrawn_at else '',
                'can_withdraw': req.tp_can_withdraw,
            })
        Period = self.env['tp.hr.attendance.period']
        locked_ranges = Period._tp_locked_ranges([company.id])
        tz_ctx = self.with_context(tz=DEFAULT_TZ)
        all_rows = []
        ordered_dates = sorted(
            dates_between(start, end),
            key=lambda d: (d > today, -d.toordinal() if d <= today else d.toordinal()),
        )
        for work_date in ordered_dates:
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
            conflict_note = cell.get('conflict_note') or ''
            leave_note = cell.get('leave_note') or ''
            has_detail = bool(sessions or day_requests or locked or cell.get('source') or record or conflict_note or leave_note)
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
                'conflict_note': conflict_note,
                'leave_note': leave_note,
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
        page_rows, pager = _page(dataset['filtered_rows'], params, default_size=100)
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
    def _tp_duplicate_days(self, company, employee_ids, start, end):
        """Return ``{employee_id: {work_date}}`` where ENTI has >1 record for the same employee & day."""
        if not employee_ids:
            return {}
        seen = defaultdict(set)
        for rec in self.env['tp.hr.attendance.enti.day'].sudo().search_fetch([
                ('company_id', '=', company.id), ('employee_id', 'in', list(employee_ids)),
                ('work_date', '>=', start), ('work_date', '<=', end),
                ('state', 'in', ('applied', 'locked_period', 'superseded_correction'))],
                ['employee_id', 'work_date', 'key_nv']):
            seen[rec.employee_id.id, rec.work_date].add(rec.key_nv)
        dups = defaultdict(set)
        for (employee_id, work_date), keys in seen.items():
            if len(keys) > 1:
                dups[employee_id].add(work_date)
        return dups

    @api.model
    def _tp_export_book(self, company, people, start, end, today, *, mode, scope='', detail_dates=None, detail_note=''):
        """Build the ``Report`` attendance workbook for ``people`` over ``[start, end]``."""
        ids = [person['id'] for person in people]
        cells, _has_leave = self._tp_presence(company, ids, start, end, today)
        views = self._tp_late_views(company, ids, cells, start, end)
        days = dates_between(start, end)
        codes = self._tp_sheet_codes(company, ids)
        start_hour = parse_hours(self._tp_reference_hours())[0]
        dup_days = self._tp_duplicate_days(company, ids, start, end)
        groups, by_department = [], {}
        for person in people:
            key = person['department_id'] or 0
            if key not in by_department:
                by_department[key] = {'name': person['department'] or 'Chưa có phòng ban', 'people': []}
                groups.append(by_department[key])
            view = views[person['id']]
            person_cells = {
                day: (cells[person['id'], day] if (detail_dates is None or day in detail_dates) else {'state': 'future'})
                for day in days
            }
            late_count, late_minutes = export_late_totals(
                person_cells, None if detail_dates is not None else view, start_hour=start_hour, today=today,
            )
            worked_days = worked_days_count(person_cells)
            emp_dups = {day for day in dup_days.get(person['id'], ()) if detail_dates is None or day in detail_dates}
            by_department[key]['people'].append({
                'code': person['code'], 'name': person['name'], 'job': person.get('job') or '',
                'machine_code': codes.get(person['id'], ''),
                'cells': person_cells,
                'worked_days': worked_days,
                'late': {'count': late_count, 'minutes': late_minutes},
                'note': person_note(
                    person_cells, view, None, person.get('archived', False),
                    duplicate_days=emp_dups, today=today,
                ),
            })
        report = {
            'title': 'BẢNG CÔNG THÁNG',
            'period': f'Từ ngày {start:%d/%m/%Y} - Đến ngày {end:%d/%m/%Y}',
            'days': days,
            'groups': groups,
        }
        content, _totals = build_attendance_book(report)
        return content

    @api.model
    def _tp_book_result(self, name, start, end, content):
        return {'filename': f'{name}_{start:%d-%m-%Y}_den_{end:%d-%m-%Y}.xlsx',
                'data': base64.b64encode(content).decode()}

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
        departments = self.env['hr.department'].browse(
            {person['department_id'] for person in people.values() if person['department_id']})
        if not departments and department_id:
            departments = self.env['hr.department'].browse(department_id).exists()
        if not self._tp_can_export_shared(company, departments):
            raise AccessError(self.env._('Người chỉ đọc không xuất dữ liệu chung. HR hoặc người được giao xử lý công mới xuất.'))
        ordered = list(people.values())
        state_filter = (params.get('state') or '').strip()
        if state_filter and ordered:
            cells, _has_leave = self._tp_presence(company, [person['id'] for person in ordered], start, end, today)
            ordered = self._tp_filter_sheet_people(ordered, cells, start, end, state_filter)
        content = self._tp_export_book(company, ordered, start, end, today, mode=mode)
        self.env['tp.hr.attendance.log']._tp_log(self.env.company, 'sheet_export',
                                                 {'from': start, 'to': end, 'people': len(ordered), 'mode': mode})
        return self._tp_book_result('Bang_cong', start, end, content)

    @api.model
    def tp_export_mine(self, params=None):
        """Own attendance only (owner from the session, client ids ignored). Uses the same Report layout."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        employee = self.env['tp.hr.attendance.correction']._tp_own_employee(company)
        if not employee:
            raise UserError(self.env._('Tài khoản chưa gắn hồ sơ nhân viên trong công ty đang chọn; cần admin/HR gắn hồ sơ.'))
        dataset = self._tp_mine_dataset(company, employee, params)
        start, end = dataset['start'], dataset['end']
        applied = dataset['applied_filters']
        has_filter = bool(applied['state'] or applied['weekday'])
        person = {'id': employee.id, 'code': employee.tp_employee_code or '', 'name': employee.name or '',
                  'department': employee.department_id.name or '', 'department_id': employee.department_id.id or False,
                  'job': employee.job_title or employee.job_id.name or ''}
        filtered = {fields.Date.to_date(row['date']) for row in dataset['filtered_rows']}
        people_list = [] if (has_filter and not filtered) else [person]
        content = self._tp_export_book(
            company, people_list, start, end, dataset['today'], mode=dataset['mode'],
            detail_dates=filtered if has_filter else None)
        return self._tp_book_result('Cong_cua_toi', start, end, content)
