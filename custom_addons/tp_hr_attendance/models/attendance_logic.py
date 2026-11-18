"""Pure rules for HR-ATTENDANCE-SIMPLE-002 (no ORM): periods, machine late totals, presence and events.

Everything here works on plain dicts/dates so the meaning of every number on the dashboard and the
sheet can be unit-tested without a database.
"""
import hashlib
import re
from datetime import UTC, date, datetime, timedelta
from io import BytesIO
from zoneinfo import ZoneInfo

from openpyxl import Workbook
from openpyxl.styles import Font

DEFAULT_TZ = 'Asia/Ho_Chi_Minh'
WEEKDAY_LABELS = ('T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN')
DIRECTIONS = ('IN', 'OUT', 'UNKNOWN')
CODE_MAX = 64
# One main presence state per person and day (dashboard donut / chips); 'future' is never drawn.
PRESENCE = {
    'working': 'Đang làm (theo mốc nguồn)',
    'out_recorded': 'Đã ghi nhận ra',
    'missing': 'Thiếu giờ vào/ra',
    'review': 'Cần kiểm tra',
    'no_punch': 'Chưa chấm công',
    'no_source': 'Chưa có dữ liệu',
    'future': 'Chưa đến',
}
PRESENCE_ORDER = ('out_recorded', 'working', 'missing', 'review', 'no_punch', 'no_source')


# ---------------------------------------------------------------- periods
def week_range(day):
    start = day - timedelta(days=day.weekday())
    return start, start + timedelta(days=6)


def month_range(day):
    start = day.replace(day=1)
    following = (start + timedelta(days=32)).replace(day=1)
    return start, following - timedelta(days=1)


def period_range(mode, anchor):
    if mode == 'week':
        return week_range(anchor)
    if mode == 'month':
        return month_range(anchor)
    return anchor, anchor


def dates_between(start, end):
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def short_range(start, end):
    """``09-15/11`` style label used next to machine totals."""
    if start == end:
        return f'{start:%d/%m}'
    if start.year != end.year:
        return f'{start:%d/%m/%Y}–{end:%d/%m/%Y}'
    if start.month != end.month:
        return f'{start:%d/%m}–{end:%d/%m}'
    return f'{start:%d}–{end:%d/%m}'


def day_label(day):
    return f'{WEEKDAY_LABELS[day.weekday()]} {day:%d/%m/%Y}'


# ------------------------------------------------------- machine late totals
def late_cover(records, start, end):
    """Machine late total for ``[start, end]`` from period records, never split or guessed.

    ``records``: dicts with ``date_from``, ``date_to``, ``count``, ``minutes`` (applied, valid totals of
    one employee). Result ``state``:

    * ``exact`` — one record equals the range, or non-overlapping records tile it exactly
      (fewest pieces win; a week never adds to the month that contains it);
    * ``conflict`` — two tilings with the same number of pieces disagree;
    * ``none`` — nothing covers the range exactly; ``hints`` lists the source periods that touch it so
      the UI can say "Số đi muộn có ở tổng kỳ 09-15/11" instead of showing 0.
    """
    usable = [row for row in records if row['date_from'] >= start and row['date_to'] <= end]
    by_start = {}
    for row in usable:
        by_start.setdefault(row['date_from'], []).append(row)
    best = []

    def walk(cursor, chosen):
        if cursor == end + timedelta(days=1):
            best.append(list(chosen))
            return
        for row in by_start.get(cursor, []):
            chosen.append(row)
            walk(row['date_to'] + timedelta(days=1), chosen)
            chosen.pop()

    walk(start, [])
    hints = sorted({(row['date_from'], row['date_to']) for row in records if row['date_from'] <= end and row['date_to'] >= start})
    hint_list = [{'from': first.isoformat(), 'to': last.isoformat(), 'label': short_range(first, last)} for first, last in hints]
    if not best:
        return {'state': 'none', 'count': None, 'minutes': None, 'pieces': [], 'hints': hint_list}
    fewest = min(len(option) for option in best)
    options = [option for option in best if len(option) == fewest]
    totals = {(sum(row['count'] for row in option), sum(row['minutes'] for row in option)) for option in options}
    if len(totals) > 1:
        return {'state': 'conflict', 'count': None, 'minutes': None, 'pieces': [], 'hints': hint_list}
    count, minutes = totals.pop()
    pieces = [{'from': row['date_from'].isoformat(), 'to': row['date_to'].isoformat(), 'label': short_range(row['date_from'], row['date_to'])}
              for row in options[0]]
    return {'state': 'exact', 'count': count, 'minutes': minutes, 'pieces': pieces, 'hints': hint_list}


# ---------------------------------------------------------------- presence
def presence_from_events(events, is_today):
    """Main state of one person/day from punches ``[{'at': datetime, 'direction': 'IN'|'OUT'|'UNKNOWN'}]``.

    The latest valid punch decides: OUT then IN again is working again; a lunch OUT followed by IN and a
    final OUT is "out recorded". An IN without OUT is never closed with the current time. Any UNKNOWN
    direction, or an OUT with no IN before it, needs a person to check.
    """
    if not events:
        return 'no_punch'
    ordered = sorted(events, key=lambda event: event['at'])
    if any(event['direction'] not in ('IN', 'OUT') for event in ordered):
        return 'review'
    last = ordered[-1]
    if last['direction'] == 'IN':
        return 'working' if is_today else 'missing'
    if not any(event['direction'] == 'IN' for event in ordered[:-1]):
        return 'review'
    return 'out_recorded'


def presence_from_day(data_state, in_time, out_time, is_today):
    """Main state from an imported day summary (Excel). Historical files are a snapshot, not live presence."""
    if data_state == 'ok':
        return 'out_recorded'
    if data_state == 'missing':
        if in_time and not out_time:
            return 'working' if is_today else 'missing'
        return 'missing'
    return 'review'


# ------------------------------------------------------------------ events
_ISO_RE = re.compile(r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?([+-]\d{2}:?\d{2}|Z)?$')


class EventError(ValueError):
    """A device event that cannot be stored as given."""


def normalize_event(raw, namespace, default_tz=DEFAULT_TZ, received_at=None):
    """Validate one device event into the staging contract; never invents a code, time or direction.

    ``raw`` keys: ``external_code`` (string as the device sends it; leading zeros kept), ``timestamp``
    (ISO 8601, with offset, or naive local time in ``tz``), optional ``tz``, ``direction``
    (IN/OUT/UNKNOWN; anything else becomes UNKNOWN), optional ``event_id``.
    """
    if not namespace:
        msg = 'Thiếu namespace nguồn.'
        raise EventError(msg)
    code = raw.get('external_code')
    if isinstance(code, bool) or code is None or isinstance(code, float):
        msg = 'Mã chấm công phải là chuỗi.'
        raise EventError(msg)
    code = str(code).strip()
    if not code or len(code) > CODE_MAX or any(ch.isspace() for ch in code):
        msg = 'Mã chấm công trống, quá dài hoặc có khoảng trắng.'
        raise EventError(msg)
    tz_name = raw.get('tz') or default_tz
    try:
        zone = ZoneInfo(tz_name)
    except (KeyError, ValueError) as exc:
        msg = 'Múi giờ không hợp lệ.'
        raise EventError(msg) from exc
    stamp = raw.get('timestamp')
    if not isinstance(stamp, str) or not _ISO_RE.match(stamp.strip()):
        msg = 'Thời điểm phải theo ISO 8601.'
        raise EventError(msg)
    try:
        moment = datetime.fromisoformat(stamp.strip().replace('Z', '+00:00'))
    except ValueError as exc:
        msg = 'Thời điểm không hợp lệ.'
        raise EventError(msg) from exc
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=zone)
    utc = moment.astimezone(UTC).replace(tzinfo=None, microsecond=0)
    local = moment.astimezone(zone)
    direction = str(raw.get('direction') or '').strip().upper()
    direction = direction if direction in DIRECTIONS else 'UNKNOWN'
    event_id = raw.get('event_id')
    event_id = str(event_id).strip()[:128] if event_id not in (None, '') else ''
    return {
        'namespace': namespace, 'source_event_id': event_id, 'external_code': code, 'timestamp': utc, 'tz': tz_name,
        'local_date': local.date(), 'direction': direction, 'received_at': received_at or datetime.now(UTC).replace(tzinfo=None, microsecond=0),
    }


def fingerprint(event):
    """Stable identity: the device event ID inside its namespace, else namespace + code + instant + direction."""
    if event.get('source_event_id'):
        key = f"{event['namespace']}|id|{event['source_event_id']}"
    else:
        key = f"{event['namespace']}|{event['external_code']}|{event['timestamp']:%Y-%m-%dT%H:%M:%S}|{event['direction']}"
    return hashlib.sha256(key.encode()).hexdigest()


# -------------------------------------------------------------------- export
def xlsx_safe(value):
    """Cell text that a spreadsheet will never evaluate as a formula."""
    if value is None:
        return ''
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    text = str(value)
    if text.startswith(('=', '+', '-', '@', '\t', '\r', '\n')):
        return "'" + text
    return text


def build_xlsx(sheets):
    """``sheets``: ``[{'title', 'note', 'header': [...], 'rows': [[...]]}]`` → bytes of a .xlsx workbook."""
    book = Workbook()
    book.remove(book.active)
    for spec in sheets:
        sheet = book.create_sheet(spec['title'][:31])
        sheet.append([xlsx_safe(spec.get('note') or '')])
        sheet.append([xlsx_safe(item) for item in spec['header']])
        for cell in sheet[2]:
            cell.font = Font(bold=True)
        for row in spec['rows']:
            sheet.append([xlsx_safe(item) for item in row])
        for index, _ in enumerate(spec['header'], 1):
            sheet.column_dimensions[sheet.cell(2, index).column_letter].width = 18 if index > 1 else 30
    stream = BytesIO()
    book.save(stream)
    return stream.getvalue()


def to_date(value):
    return value if isinstance(value, date) else date.fromisoformat(value)
