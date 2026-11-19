"""Overview, minimal sheet, person detail and own attendance (HR-ATTENDANCE-SIMPLE-002, DEC-055/056).

All screens read the same PostgreSQL data: imported day summaries (Excel), mapped device events (API,
none until a device is connected) and the machine late totals per source period. One main presence
state per person and day; nothing is invented (no 17:00 out, no leave from an empty cell, no late
total split over days or added to an overlapping period).
"""
import base64
from collections import defaultdict
from datetime import timedelta

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
from .attendance_logic import (
    MINE_STATE_FILTERS,
    MINE_WEEKDAY_FILTERS,
    PRESENCE,
    PRESENCE_ORDER,
    WEEKDAY_FULL_LABELS,
    WEEKDAY_LABELS,
    build_xlsx,
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
OVERVIEW_MODES = ('day', 'week', 'month')
LEAVE = 'leave'
LABELS = dict(PRESENCE, leave='Nghỉ đã xác nhận')
STATE_ORDER = (*PRESENCE_ORDER, LEAVE)
ATTENTION = ('missing', 'review')
SOURCE_LABELS = {'excel': 'Excel máy chấm công', 'api': 'API máy chấm công', 'mixed': 'Excel + API máy', 'none': 'Chưa có nguồn dữ liệu'}
MINE_STATE_FILTER_LABELS = {
    'out_recorded': 'Đủ vào/ra',
    'working': 'Chờ ghi nhận giờ ra',
    'attention': 'Thiếu giờ / Cần kiểm tra',
    'missing_in': 'Thiếu giờ vào',
    'missing_out': 'Thiếu giờ ra',
    'review': 'Cần kiểm tra',
    'no_punch': 'Chưa chấm công',
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


def range_label(start, end):
    """``09-15/11/2026``; the year is written once (twice only when the range crosses a year)."""
    label = short_range(start, end)
    return label if start.year != end.year else f'{label}/{end.year}'


def _page(rows, params, default_size=20):
    size = int(params.get('page_size') or default_size)
    size = size if size in PAGE_SIZES else default_size
    count = max(1, -(-len(rows) // size))
    page = min(max(1, int(params.get('page') or 1)), count)
    return rows[(page - 1) * size:page * size], {'page': page, 'page_count': count, 'page_size': size, 'total': len(rows)}


def _late_view(cover):
    """What a sheet cell says about the machine late total of one person for the viewed range."""
    if cover['state'] == 'exact':
        return {'state': 'exact', 'count': cover['count'], 'minutes': cover['minutes'], 'text': '',
                'source': ' + '.join(piece['label'] for piece in cover['pieces'])}
    hints = [hint['label'] for hint in cover['hints']]
    if cover['state'] == 'conflict':
        return {'state': 'conflict', 'count': None, 'minutes': None, 'text': f'{NO_EXACT} (các kỳ nguồn khác nhau)', 'source': ''}
    if hints:
        return {'state': 'partial', 'count': None, 'minutes': None, 'source': '',
                'text': 'Số đi muộn có ở tổng kỳ ' + ', '.join(hints[:3]) + ('…' if len(hints) > 3 else '')}
    return {'state': 'none', 'count': None, 'minutes': None, 'text': NO_LATE, 'source': ''}


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
        """Active HR employees of the company in scope (the KPI denominator); with a range, archived people
        who still have day data in it are appended for the sheet (flagged ``archived``)."""
        Public = self.env['hr.employee.public']
        domain = [('company_id', '=', company.id)]
        if department_id:
            domain.append(('department_id', 'child_of', department_id))
        if term:
            domain += ['|', ('name', 'ilike', term), ('tp_employee_code', 'ilike', term)]
        people = {}
        for emp in Public.search(domain, order='tp_employee_code, name'):
            people[emp.id] = {'id': emp.id, 'code': emp.tp_employee_code or '', 'name': emp.name or '',
                              'department': emp.department_id.name or '', 'department_id': emp.department_id.id or False}
        if start and end:
            day_domain = [('company_id', '=', company.id), ('work_date', '>=', start), ('work_date', '<=', end),
                          ('employee_id', 'not in', list(people))]
            if department_id:
                day_domain.append(('department_id', 'child_of', department_id))
            if term:
                day_domain += ['|', ('employee_name', 'ilike', term), ('employee_code', 'ilike', term)]
            for day in self.search(day_domain):
                people.setdefault(day.employee_id.id, {
                    'id': day.employee_id.id, 'code': day.employee_code or '', 'name': day.employee_name or '',
                    'department': day.department_id.name or '', 'department_id': day.department_id.id or False, 'archived': True})
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
    def _tp_presence(self, company, employee_ids, start, end, today):
        """``({(employee_id, date): cell}, has_leave_source)``; one main state per person and day."""
        ids = list(employee_ids)
        days = self.search([('company_id', '=', company.id), ('employee_id', 'in', ids), ('work_date', '>=', start),
                            ('work_date', '<=', end)]) if ids else self.browse()
        day_map = {(day.employee_id.id, day.work_date): day for day in days}
        events = defaultdict(list)
        if ids:
            for event in self.env['tp.hr.attendance.event'].sudo().search([
                    ('company_id', '=', company.id), ('employee_id', 'in', ids), ('state', '=', 'mapped'),
                    ('local_date', '>=', start), ('local_date', '<=', end)], order='timestamp'):
                events[event.employee_id.id, event.local_date].append(
                    {'at': event.timestamp, 'direction': event.direction, 'tz': event.tz})
        coverage = self.env['tp.hr.attendance.batch']._tp_coverage(company, start, end)
        leave = self._tp_leave_days(company, ids, start, end) if ids else None
        result = {}
        for employee_id in ids:
            for work_date in dates_between(start, end):
                key = (employee_id, work_date)
                cell = {'in': '', 'out': '', 'source': '', 'day_id': False}
                if work_date > today:
                    cell['state'] = 'future'
                elif events.get(key):
                    punches = events[key]
                    cell['state'] = presence_from_events(punches, work_date == today)
                    ins = [punch for punch in punches if punch['direction'] == 'IN']
                    cell['in'] = utc_to_local(ins[0]['at'], ins[0]['tz']).strftime('%H:%M') if ins else ''
                    if punches[-1]['direction'] == 'OUT':
                        cell['out'] = utc_to_local(punches[-1]['at'], punches[-1]['tz']).strftime('%H:%M')
                    cell['source'] = 'api'
                elif key in day_map:
                    day = day_map[key]
                    cell.update(state=presence_from_day(day.data_state, day.in_time, day.out_time, work_date == today),
                                source='excel', day_id=day.id, **{'in': day.in_time or '', 'out': day.out_time or ''})
                elif leave and key in leave:
                    cell['state'] = LEAVE
                elif any(employee_id in people and first <= work_date <= last for first, last, people in coverage):
                    cell['state'] = 'no_punch'
                else:
                    cell['state'] = 'no_source'
                cell['label'] = LABELS.get(cell['state'], '')
                result[key] = cell
        return result, leave is not None

    @api.model
    def _tp_source_strip(self, company, today):
        updated, applied = self._tp_updated(company)
        Event = self.env['tp.hr.attendance.event'].sudo()
        sources = self.env['tp.hr.attendance.source'].sudo().search([('company_id', '=', company.id)])
        last_event = Event.search([('company_id', '=', company.id)], order='timestamp desc', limit=1)
        kind = 'mixed' if applied and last_event else 'api' if last_event else 'excel' if applied else 'none'
        states = dict(self.env['tp.hr.attendance.source']._fields['state'].selection)
        latest_day = self.search([('company_id', '=', company.id), ('work_date', '<=', today)], order='work_date desc', limit=1).work_date
        latest_event = last_event.local_date if last_event and last_event.local_date <= today else None
        latest = max(filter(None, [latest_day, latest_event]), default=None)
        return {
            'kind': kind, 'label': SOURCE_LABELS[kind], 'updated_at': updated['at'] if updated else '',
            'data_to': updated['to'] if updated else '', 'file': applied[:1].file_name or '' if applied else '',
            'api': ', '.join(f'{source.name}: {states[source.state]}' for source in sources) or 'Chưa cấu hình',
            'live': False, 'latest_date': latest.isoformat() if latest else '',
            'note': 'Excel là ảnh chụp theo file đã nhập, không phải thời gian thực.' if kind in ('excel', 'mixed') else '',
        }

    @api.model
    def _tp_departments(self, company):
        departments = self.env['hr.department'].search([('company_id', 'in', [company.id, False])]).sorted(lambda d: d.complete_name or '')
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
            'reference_hours': (self.env['ir.config_parameter'].sudo().get_str('tp_hr_attendance.reference_hours') or '08:30-17:00'),
        }

    @api.model
    def _tp_can_export_shared(self, company, departments=None):
        if self.env.user.has_group(HR_MANAGER) or can(self.env, 'import', company):
            return True
        return departments is not None and bool(departments) and can(self.env, 'review', company, departments)

    # ------------------------------------------------------------ overview
    @api.model
    def tp_overview(self, params=None):
        """Dashboard for one day / week (Mon-Sun) / month; KPIs, chips, chart and drill list share one scope."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        mode, anchor, start, end, today = self._tp_period(params, OVERVIEW_MODES)
        department_id = int(params.get('department_id') or 0)
        people = self._tp_people(company, department_id)
        ids = list(people)
        cells, has_leave = self._tp_presence(company, ids, start, end, today)
        dates = dates_between(start, end)
        past = [day for day in dates if day <= today]
        distinct = {state: set() for state in STATE_ORDER}
        daily = []
        for work_date in dates:
            counts = dict.fromkeys(STATE_ORDER, 0)
            for employee_id in ids:
                state = cells[employee_id, work_date]['state']
                if state in counts:
                    counts[state] += 1
                    distinct[state].add(employee_id)
            daily.append({'date': work_date.isoformat(), 'day': work_date.day, 'weekday': WEEKDAY_LABELS[work_date.weekday()],
                          'future': work_date > today, 'is_today': work_date == today, 'counts': counts})
        if mode == 'day':
            counts = daily[0]['counts']
            value = {state: counts[state] for state in STATE_ORDER}
        else:
            value = {state: len(distinct[state]) for state in STATE_ORDER}
        attention = len(distinct['missing'] | distinct['review']) if mode != 'day' else value['missing'] + value['review']
        kpis = {
            'total': len(ids),
            'leave': value[LEAVE] if has_leave else None,
            'out': value['out_recorded'],
            'out_label': 'Đã ghi nhận ra' if mode == 'day' else 'Người có ghi nhận ra trong kỳ',
            'out_note': ('Theo lượt ra hợp lệ mới nhất; có thể còn quay lại.' if start == today else 'Ngày đã qua theo dữ liệu nguồn.')
            if mode == 'day' else 'Số người khác nhau có ít nhất một ngày đủ giờ ra.',
        }
        chips = [
            {'key': 'working', 'label': LABELS['working'] if mode == 'day' else 'Đang làm hôm nay', 'value': value['working']},
            {'key': 'no_punch', 'label': LABELS['no_punch'] if mode == 'day' else 'Người có ngày chưa chấm công', 'value': value['no_punch']},
            {'key': 'attention', 'label': 'Cần kiểm tra' if mode == 'day' else 'Người có ngày cần kiểm tra', 'value': attention,
             'detail': f"{value['missing']} thiếu giờ · {value['review']} cần kiểm tra"},
        ]
        if not has_leave:
            chips.append({'key': 'no_source', 'label': LABELS['no_source'] if mode == 'day' else 'Người có ngày chưa có dữ liệu',
                          'value': value['no_source']})
        donut = []
        if mode == 'day' and past:
            donut = [{'key': state, 'label': LABELS[state], 'value': value[state]} for state in STATE_ORDER
                     if value[state] and (state != LEAVE or has_leave)]
        # Late chip only when the view matches source periods exactly (never split / summed across overlaps).
        covers = self.env['tp.hr.attendance.late']._tp_cover(company, ids, start, end)
        exact = [cover for cover in covers.values() if cover['state'] == 'exact']
        late = None
        if exact:
            late = {'people': len(exact), 'late_people': sum(1 for cover in exact if cover['count']),
                    'count': sum(cover['count'] for cover in exact), 'minutes': sum(cover['minutes'] for cover in exact),
                    'label': short_range(start, end), 'source': 'Theo Excel máy'}
        hints = sorted({hint['label'] for cover in covers.values() if cover['state'] != 'exact' for hint in cover['hints']})
        # Drill list: same scope as the KPIs, then the search term.
        drill = params.get('drill') or ('all' if mode == 'day' else 'attention')
        drill_date = self._tp_parse_date(params.get('drill_date')) if params.get('drill_date') else None
        term = (params.get('search') or '').strip().casefold()
        wanted = {'all': set(STATE_ORDER), 'attention': set(ATTENTION)}.get(drill, {drill} if drill in STATE_ORDER else set(STATE_ORDER))
        order = {state: index for index, state in enumerate(STATE_ORDER)}
        rows = []
        for work_date in (past if mode != 'day' else dates[:1]):
            if drill_date and work_date != drill_date:
                continue
            for employee_id in ids:
                cell = cells[employee_id, work_date]
                person = people[employee_id]
                if cell['state'] not in wanted:
                    continue
                if term and term not in person['name'].casefold() and term not in person['code'].casefold():
                    continue
                rows.append({'employee_id': employee_id, 'name': person['name'], 'code': person['code'], 'department': person['department'],
                             'date': work_date.isoformat(), 'day_label': day_label(work_date), 'in': cell['in'], 'out': cell['out'],
                             'state': cell['state'], 'state_label': cell['label'], 'source': cell['source']})
        rows.sort(key=lambda row: (row['code'] or 'ZZZ', row['name']))
        rows.sort(key=lambda row: order.get(row['state'], 99))
        if mode != 'day':
            rows.sort(key=lambda row: row['date'], reverse=True)
        page_rows, pager = _page(rows, params)
        week = period_range('week', anchor)
        return dict({
            'mode': mode, 'date': anchor.isoformat(), 'start': start.isoformat(), 'end': end.isoformat(), 'today': today.isoformat(),
            'week': {'from': week[0].isoformat(), 'to': week[1].isoformat()},
            'period_label': day_label(start) if mode == 'day' else range_label(start, end) if mode == 'week' else f'Tháng {start:%m/%Y}',
            'future': start > today, 'includes_today': start <= today <= end,
            'kpis': kpis, 'chips': chips, 'donut': donut, 'daily': daily if mode != 'day' else [],
            'late': late, 'late_hints': hints[:4], 'labels': LABELS, 'has_leave_source': has_leave,
            'drill': drill, 'drill_date': drill_date.isoformat() if drill_date else '', 'rows': page_rows,
            'source': self._tp_source_strip(company, today), 'departments': self._tp_departments(company),
        }, **pager, **self._tp_flags(company))

    # --------------------------------------------------------------- sheet
    @api.model
    def tp_sheet(self, params=None):
        """Minimal sheet: day → name/department/day/in/out; week/month/range → name/department/late totals."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        mode, anchor, start, end, today = self._tp_period(params)
        department_id = int(params.get('department_id') or 0)
        term = (params.get('search') or '').strip()
        people = self._tp_people(company, department_id, term, start, end)
        ordered = sorted(people.values(), key=lambda row: (row['code'] or 'ZZZ', row['name']))
        result = {'mode': mode, 'date': anchor.isoformat(), 'start': start.isoformat(), 'end': end.isoformat(), 'today': today.isoformat(),
                  'labels': LABELS, 'departments': self._tp_departments(company), 'file_periods': self._tp_file_periods(company),
                  'source': self._tp_source_strip(company, today)}
        result.update(self._tp_flags(company))
        if mode == 'day':
            cells, _has_leave = self._tp_presence(company, people, start, start, today)
            state_filter = params.get('state') or ''
            rows = []
            for person in ordered:
                cell = cells[person['id'], start]
                if state_filter == 'attention' and cell['state'] not in ATTENTION:
                    continue
                if state_filter and state_filter != 'attention' and cell['state'] != state_filter:
                    continue
                rows.append(dict(person, date=start.isoformat(), day_label=day_label(start), **{'in': cell['in'], 'out': cell['out']},
                                 state=cell['state'], state_label=cell['label']))
            records = self.env['tp.hr.attendance.late']._tp_records(company, list(people), start, start)
            labels = sorted({short_range(row['date_from'], row['date_to']) for items in records.values() for row in items})
            result.update(period_label=day_label(start), late_note='Số đi muộn có ở tổng kỳ ' + ', '.join(labels) if labels else '',
                          state=state_filter)
        else:
            covers = self.env['tp.hr.attendance.late']._tp_cover(company, list(people), start, end)
            rows = [dict(person, late=_late_view(covers[person['id']])) for person in ordered]
            exact = [row for row in rows if row['late']['state'] == 'exact']
            sources = sorted({row['late']['source'] for row in exact})
            label = f'Tháng {start:%m/%Y}' if mode == 'month' else range_label(start, end)
            result.update(period_label=label, late_source=('Theo Excel máy · kỳ ' + ', '.join(sources)) if sources else '',
                          late_summary={'people': len(exact), 'count': sum(row['late']['count'] for row in exact),
                                        'minutes': sum(row['late']['minutes'] for row in exact)} if exact else None,
                          is_file_period=any(item['from'] == start.isoformat() and item['to'] == end.isoformat() for item in result['file_periods']))
        page_rows, pager = _page(rows, params)
        result.update(rows=page_rows, **pager)
        return result

    @api.model
    def _tp_person_data(self, company, person, start, end, today):
        cells, _has_leave = self._tp_presence(company, [person['id']], start, end, today)
        cover = self.env['tp.hr.attendance.late']._tp_cover(company, [person['id']], start, end)[person['id']]
        rows = []
        for work_date in dates_between(start, end):
            cell = cells[person['id'], work_date]
            rows.append({'date': work_date.isoformat(), 'day_label': day_label(work_date), 'in': cell['in'], 'out': cell['out'],
                         'state': cell['state'], 'state_label': cell['label'], 'weekend': work_date.weekday() >= 5,
                         'future': work_date > today, 'is_today': work_date == today})
        return {'employee': {key: person[key] for key in ('id', 'name', 'code', 'department')},
                'start': start.isoformat(), 'end': end.isoformat(), 'period_label': range_label(start, end),
                'late': _late_view(cover), 'rows': rows, 'today': today.isoformat(), 'labels': LABELS}

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
        cover = self.env['tp.hr.attendance.late']._tp_cover(company, [employee.id], start, end)[employee.id]
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
                'weekend': weekday_index >= 5,
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
            'has_leave_source': has_leave, 'late': _late_view(cover),
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
        period_label = f'Tháng {start:%m/%Y}' if dataset['mode'] == 'month' else range_label(start, end)
        ref_hours = self.env['ir.config_parameter'].sudo().get_str('tp_hr_attendance.reference_hours') or '08:30-17:00'
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
            'period_label': period_label,
            'range_display': f'{start:%d/%m/%Y} – {end:%d/%m/%Y}',
            'late': dataset['late'],
            'summary': dataset['summary'],
            'period_days': len(dataset['all_rows']),
            'has_leave_source': dataset['has_leave_source'],
            'applied_filters': dataset['applied_filters'],
            'reference_hours': ref_hours,
            'rows': page_rows,
            'labels': LABELS,
            'file_periods': self._tp_file_periods(company),
            'source': self._tp_source_strip(company, dataset['today']),
        }, **pager)

    # -------------------------------------------------------------- export
    @api.model
    def _tp_xlsx_result(self, name, start, end, sheets):
        content = build_xlsx(sheets)
        return {'filename': f'{name}-{start:%Y%m%d}-{end:%Y%m%d}.xlsx', 'data': base64.b64encode(content).decode()}

    @api.model
    def _tp_export_sheets(self, company, people, start, end, today, title):
        cells, _has_leave = self._tp_presence(company, [person['id'] for person in people], start, end, today)
        covers = self.env['tp.hr.attendance.late']._tp_cover(company, [person['id'] for person in people], start, end)
        stamp = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz or DEFAULT_TZ), fields.Datetime.now())
        note = (f'{title} · Khoảng ngày {start:%d/%m/%Y} – {end:%d/%m/%Y} · Nguồn: báo cáo máy chấm công · '
                f'Xuất lúc {stamp:%d/%m/%Y %H:%M} · Thiếu giờ ghi "—", không tự điền.')
        day_rows = []
        for person in people:
            for work_date in dates_between(start, min(end, today)):
                cell = cells[person['id'], work_date]
                day_rows.append([person['name'], person['code'], person['department'], day_label(work_date),
                                 cell['in'] or '—', cell['out'] or '—', cell['label']])
        sheets = [{'title': 'Giờ theo ngày', 'note': note,
                   'header': ['Nhân viên', 'Mã NV', 'Phòng ban', 'Thứ/ngày', 'Giờ vào', 'Giờ ra', 'Tình trạng'], 'rows': day_rows}]
        late_rows = []
        for person in people:
            view = _late_view(covers[person['id']])
            if view['state'] == 'exact':
                late_rows.append([person['name'], person['code'], person['department'], view['source'], view['count'], view['minutes']])
        if late_rows:
            sheets.append({'title': 'Tổng đi muộn', 'note': f'Theo Excel máy, đúng kỳ nguồn trong {start:%d/%m/%Y} – {end:%d/%m/%Y}; '
                                                            'không chia theo ngày, không tự tính lại.',
                           'header': ['Nhân viên', 'Mã NV', 'Phòng ban', 'Kỳ nguồn', 'Số lần đi muộn', 'Tổng phút muộn'], 'rows': late_rows})
        return sheets

    @api.model
    def tp_export_sheet(self, params=None):
        """Shared export: HR manager, import assignee, or reviewer of every exported department only."""
        self.check_access('read')
        params = dict(params or {})
        company = self.env.company
        mode, _anchor, start, end, today = self._tp_period(params)
        people = self._tp_people(company, int(params.get('department_id') or 0), (params.get('search') or '').strip(), start, end)
        departments = self.env['hr.department'].browse({person['department_id'] for person in people.values() if person['department_id']})
        if not self._tp_can_export_shared(company, departments):
            raise AccessError(self.env._('Người chỉ đọc không xuất dữ liệu chung. HR hoặc người được giao xử lý công mới xuất.'))
        ordered = sorted(people.values(), key=lambda row: (row['code'] or 'ZZZ', row['name']))
        sheets = self._tp_export_sheets(company, ordered, start, end, today, 'Bảng chấm công')
        self.env['tp.hr.attendance.log']._tp_log(self.env.company, 'sheet_export',
                                                 {'from': start, 'to': end, 'people': len(ordered), 'mode': mode})
        return self._tp_xlsx_result('bang-cham-cong', start, end, sheets)

    @api.model
    def tp_export_mine(self, params=None):
        """Export ALL matching personal rows for the applied filters (never only the active page); owner from session."""
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
        filter_note = (' · Bộ lọc đang áp: ' + '; '.join(filter_parts)) if filter_parts else ''
        stamp = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz or DEFAULT_TZ), fields.Datetime.now())
        note = (f'Công của tôi · Khoảng ngày {start:%d/%m/%Y} – {end:%d/%m/%Y}{filter_note} · '
                f'Nguồn: báo cáo máy chấm công · Xuất lúc {stamp:%d/%m/%Y %H:%M} · Thiếu giờ ghi "—", không tự điền.')
        code = employee.tp_employee_code or ''
        dept = employee.department_id.name or ''
        day_rows = [
            [employee.name, code, dept, row['day_label'], row['in'] or '—', row['out'] or '—', row['status_label']]
            for row in dataset['filtered_rows']
        ]
        sheets = [{'title': 'Giờ theo ngày', 'note': note,
                   'header': ['Nhân viên', 'Mã NV', 'Phòng ban', 'Thứ/ngày', 'Giờ vào', 'Giờ ra', 'Tình trạng'], 'rows': day_rows}]
        late = dataset['late']
        if late['state'] == 'exact':
            sheets.append({
                'title': 'Tổng đi muộn',
                'note': (f'Theo Excel máy, đúng kỳ nguồn trong {start:%d/%m/%Y} – {end:%d/%m/%Y}; '
                         'không chia theo ngày, không tính lại theo bộ lọc ngày.'),
                'header': ['Nhân viên', 'Mã NV', 'Phòng ban', 'Kỳ nguồn', 'Số lần đi muộn', 'Tổng phút muộn'],
                'rows': [[employee.name, code, dept, late['source'], late['count'], late['minutes']]],
            })
        return self._tp_xlsx_result('cong-cua-toi', start, end, sheets)
