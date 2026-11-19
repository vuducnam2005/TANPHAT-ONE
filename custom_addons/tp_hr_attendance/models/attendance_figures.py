"""Shared attendance figures (ENTI-ATTENDANCE-002): one meaning for Tổng quan, Bảng công, Công của tôi and Excel.

Pure functions over the per person/day cells built by ``tp.hr.attendance.day._tp_presence`` (no ORM), so every
number can be unit-tested without a database:

* late — ENTI ``diMuon`` minutes of the day the board shows (count = days with minutes > 0, minutes = sum);
  a day without a known ENTI value is *unknown*, never 0, and a range total is exact only when every finished
  employed day of the range is known;
* absence — a whole scheduled working day with no punch at all, finished (past, or today after the end of
  hours), inside employment and not on approved leave; one punch is never an absence;
* recent — the newest first-in/last-out mark per person (ENTI only gives the first in and the last out).
"""
from datetime import timedelta

# Exclusive day states, in the order of the donut / legend. 'future' and 'off' (outside employment) are never drawn.
STATUS_ORDER = ('out_recorded', 'working', 'missing', 'review', 'absent', 'no_punch', 'rest', 'leave', 'no_source')
ATTENTION = ('missing', 'review')
UNDRAWN = ('future', 'off')
# Days without any punch: nobody is late on them, so their late value is a known 0 even without an ENTI row.
LATE_FREE = ('absent', 'no_punch', 'rest', 'leave')
DEFAULT_HOURS = '08:30-17:00'
NO_HALF_DAY = 'Chưa đủ dữ liệu xác định số buổi vắng'


def parse_hours(text, default=DEFAULT_HOURS):
    """``'08:30-17:00'`` → (8.5, 17.0); a malformed value falls back to the default hours."""
    for candidate in (text, default):
        try:
            first, last = (part.strip() for part in (candidate or '').split('-', 1))
            start = int(first.split(':')[0]) + int(first.split(':')[1]) / 60
            end = int(last.split(':')[0]) + int(last.split(':')[1]) / 60
        except (ValueError, IndexError, AttributeError):
            continue
        if 0 <= start < end <= 24:
            return start, end
    return 8.5, 17.0


def no_punch_state(*, on_leave, scheduled, employed, finished):
    """State of a day the sources cover but that has no punch at all."""
    if not employed:
        return 'off'
    if on_leave:
        return 'leave'
    if not scheduled:
        return 'rest'
    return 'absent' if finished else 'no_punch'


def late_of(cell):
    """Late minutes of one day cell: the ENTI value, 0 for a day without any punch, ``None`` when unknown."""
    if cell.get('late') is not None:
        return cell['late']
    return 0 if cell['state'] in LATE_FREE else None


def late_total(cells):
    """Late figures of one person over cells of one range: ``{state, count, minutes, known, unknown}``.

    Only finished-or-today employed days count (future/off days are skipped). ``exact`` needs every counted
    day known; ``partial`` keeps the known sums and how many days are unknown; ``none`` when nothing is known.
    """
    counted = [cell for cell in cells if cell['state'] not in UNDRAWN]
    values = [late_of(cell) for cell in counted]
    known = [value for value in values if value is not None]
    unknown = len(counted) - len(known)
    count = sum(1 for value in known if value > 0)
    minutes = sum(known)
    real = any(cell.get('late') is not None for cell in counted)
    if not counted or not known:
        state = 'none'
    elif not unknown:
        state = 'exact'
    else:
        # Only "no punch → 0" days known and the rest unknown: nothing was really measured.
        state = 'partial' if real else 'none'
    return {'state': state, 'count': count if known else None, 'minutes': minutes if known else None,
            'known': len(known), 'unknown': unknown, 'real': real}


def absence_total(cells, half_day_known=False):
    """Absent whole days of one person; ``exact`` only when no counted scheduled day lacks a source."""
    counted = [cell for cell in cells if cell['state'] not in UNDRAWN]
    days = sum(1 for cell in counted if cell['state'] == 'absent')
    unknown = sum(1 for cell in counted if cell['state'] == 'no_source' and cell.get('scheduled'))
    return {'days': days, 'unknown': unknown, 'state': 'exact' if not unknown else 'partial',
            'note': '' if half_day_known else NO_HALF_DAY}


def late_text(total):
    if total['state'] == 'exact':
        return ''
    if total['state'] == 'partial':
        return f"Thiếu dữ liệu đi muộn {total['unknown']} ngày"
    return 'Chưa có số liệu đi muộn'


def distribution(cells):
    """``{state: count}`` over drawable cells (each cell is exactly one state)."""
    counts = dict.fromkeys(STATUS_ORDER, 0)
    for cell in cells:
        if cell['state'] in counts:
            counts[cell['state']] += 1
    return counts


def latest_mark(cell):
    """(UTC datetime, 'in'|'out') of the newest mark of a day cell, or (None, '')."""
    marks = [(cell.get('out_at'), 'out'), (cell.get('in_at'), 'in')]
    marks = [mark for mark in marks if mark[0]]
    return max(marks, key=lambda mark: mark[0]) if marks else (None, '')


def recent_people(cells_by_person, limit=10):
    """Newest marks: at most ``limit`` distinct people, newest punch first (ties: person id)."""
    best = []
    for employee_id, cells in cells_by_person.items():
        newest = None
        for cell in cells:
            at, kind = latest_mark(cell)
            if at and (newest is None or at > newest[0]):
                newest = (at, kind, cell)
        if newest:
            best.append((newest[0], employee_id, newest[1], newest[2]))
    best.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    return [{'employee_id': employee_id, 'at': at, 'kind': kind, 'cell': cell} for at, employee_id, kind, cell in best[:limit]]


def daily_late(cells):
    """(minutes, late people, complete) for one day across people; minutes is None when no value is known."""
    counted = [cell for cell in cells if cell['state'] not in UNDRAWN]
    known = [value for value in (late_of(cell) for cell in counted) if value is not None]
    if not known or not any(cell['state'] not in LATE_FREE for cell in counted):
        return None, None, False
    return sum(known), sum(1 for value in known if value > 0), len(known) == len(counted)


def week_of(day):
    start = day - timedelta(days=day.weekday())
    return start, start + timedelta(days=6)
