"""Shared attendance figures (ENTI-ATTENDANCE-002): one meaning for Tổng quan, Bảng công, Công của tôi and Excel.

Pure functions over the per person/day cells built by ``tp.hr.attendance.day._tp_presence`` (no ORM), so every
number can be unit-tested without a database:

* late — ENTI ``diMuon`` minutes of the day the board shows (count = days with minutes > 0, minutes = sum);
  a day without a known ENTI value is *unknown*, never 0, and a range total is exact only when every finished
  employed day of the range is known;
* absence — a whole scheduled working day with no punch at all, finished (past, or today after the end of
  hours), inside employment and not on approved leave; one punch is never an absence;
* groups — one dashboard group per person for one classification day (ATTENDANCE-DASH-004): ``done`` once an
  out is recorded, ``working`` with an in but no out, ``not_started`` only when a healthy source covers the day
  without any mark, else ``unknown`` with the reason; marks are never counted, people are;
* recent — the newest marks of that day, one row per mark the source really provides (no invented swipes,
  seconds or places).
"""
import unicodedata
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


# Dashboard groups: one per person and classification day; 'unknown' is never folded into 'not_started'.
DAY_GROUPS = ('working', 'done', 'not_started')
GROUP_KEYS = (*DAY_GROUPS, 'unknown')
GROUP_LABELS = {'working': 'Đang làm', 'done': 'Đã về', 'not_started': 'Chưa đi làm', 'unknown': 'Chưa xác định'}
GROUP_HINTS = {
    'working': 'Đang làm: đã ghi nhận vào, chưa ghi nhận ra.',
    'done': 'Đã về: đã ghi nhận giờ ra.',
    'not_started': 'Chưa đi làm: chưa ghi nhận chấm công trong ngày.',
    'unknown': 'Chưa xác định: nguồn chưa có dữ liệu cho người hoặc ngày này.',
}
UNKNOWN_REASONS = {
    'no_source': 'Chưa có dữ liệu nguồn cho ngày này (chưa ghép mã hoặc nguồn chưa trả)',
    'source_down': 'Chưa nhận được dữ liệu mới từ nguồn chấm công; chưa xác định được',
    'review': 'Dữ liệu ngày cần kiểm tra',
}


def day_group(cell, live_ok=True):
    """``(group, reason)`` of one person for one day; ``(None, '')`` when the day is not counted (future/off).

    Marks decide first (an out — with or without an in — is ``done``; an in alone is ``working``). Without any
    mark the person is ``not_started`` only when a source covers that day and, for today, the live source is
    healthy; otherwise the group is ``unknown`` with the reason, never a silent "not started".
    """
    state = cell['state']
    if state in UNDRAWN:
        return None, ''
    if cell.get('out'):
        return 'done', ''
    if cell.get('in'):
        return 'working', ''
    if state == 'review':
        return 'unknown', 'review'
    if not cell.get('covered'):
        return 'unknown', 'no_source'
    if not live_ok:
        return 'unknown', 'source_down'
    return 'not_started', ''


def group_counts(cells, live_ok=True):
    """``({group: people}, {reason: people}, excluded)`` over the cells of one day (one cell per person)."""
    counts = dict.fromkeys(GROUP_KEYS, 0)
    reasons = dict.fromkeys(UNKNOWN_REASONS, 0)
    excluded = 0
    for cell in cells:
        group, reason = day_group(cell, live_ok)
        if group is None:
            excluded += 1
            continue
        counts[group] += 1
        if reason:
            reasons[reason] += 1
    return counts, reasons, excluded


def class_date(start, end, today, marked=()):
    """The one day the dashboard groups describe: today inside the period, the start of a future period, else
    the newest day of a past period that has a mark (or the last working day when the period ends on a markless Sunday)."""
    if start <= today <= end:
        return today
    if start > today:
        return start
    days = [day for day in marked if start <= day <= end]
    if days:
        return max(days)
    if end.weekday() == 6 and start < end:
        return end - timedelta(days=1)
    return end


def clock_has_seconds(raw):
    """True when a raw source clock (``'08:10:23'``, ``'2026-11-20T08:10:23'``) really carries seconds."""
    text = str(raw or '').strip().replace('T', ' ').split('.')[0]
    if ' ' in text:
        text = text.split(' ', 1)[1]
    parts = text.split(':')
    return len(parts) >= 3 and parts[2][:2].isdigit()


def fold_text(text):
    """Lower-case text without Vietnamese accents (``'Đỗ Văn'`` → ``'do van'``) for forgiving name search."""
    text = unicodedata.normalize('NFD', str(text or '').replace('đ', 'd').replace('Đ', 'D'))
    return ''.join(char for char in text if not unicodedata.combining(char)).casefold()


def recent_marks(marks, limit=10):
    """Newest marks first, at most ``limit``; one row per real mark (the same ``key`` is kept once, real
    repeats of one person stay). ``marks``: dicts with ``key``, ``at`` (sortable instant) and ``order``."""
    seen, unique = set(), []
    for mark in marks:
        if mark['key'] in seen:
            continue
        seen.add(mark['key'])
        unique.append(mark)
    unique.sort(key=lambda mark: (mark['at'], mark['kind'] == 'out', -mark['order']), reverse=True)
    return unique[:limit]


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
