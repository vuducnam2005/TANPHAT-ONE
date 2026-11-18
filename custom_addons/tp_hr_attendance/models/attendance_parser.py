"""Reader for the machine attendance report: one Vào row and one Ra row per employee, one column per day.

Pure functions (no ORM) so the format rules stay unit-testable. Of the summary columns only the
"Đi muộn" group (Lần / Phút) is read, found by its two-level header and merged cells, never by a fixed
column letter; the machine's period total is kept as given and never recomputed from clock times.
Absent, early leave, totals, overtime and notes are ignored.
"""
import re
import unicodedata
import zipfile
from datetime import date, datetime, time, timedelta
from io import BytesIO

from openpyxl import load_workbook

MAX_BYTES = 5 * 1024 * 1024
MAX_SHEETS = 20
MAX_ROWS = 5000
TIME_RE = re.compile(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$')
PERIOD_RE = re.compile(r'(\d{1,2})/(\d{1,2})/(\d{4})\D+?(\d{1,2})/(\d{1,2})/(\d{4})')
CODE_RE = re.compile(r'^[A-Za-zĐđ]{1,6}$')
WEEKDAYS = {'t2': 0, 't3': 1, 't4': 2, 't5': 3, 't6': 4, 't7': 5, 'cn': 6}
HEADERS = {'stt': 'stt', 'ma nhan vien': 'source_code', 'ten nhan vien': 'name', 'id': 'machine_code', 'chuc vu': 'title'}
LATE_HEADERS = ('di muon', 'di tre')
LATE_COUNT = ('lan', 'so lan')
LATE_MINUTES = ('phut', 'so phut')
# Late states per person: ok, empty (no number), invalid (not a non-negative integer, or only one side),
# inconsistent (0 times with minutes or the reverse: kept as the source gave it, flagged for HR).
LATE_STATES = ('ok', 'empty', 'invalid', 'inconsistent')
# Event kinds. Only "pair" becomes a session; every other kind waits in staging for a person to check.
KINDS = ('pair', 'missing_out', 'missing_in', 'reversed', 'code', 'merged', 'multi', 'invalid')


class AttendanceFormatError(ValueError):
    """The file is not a readable attendance report."""


def fold(value):
    text = unicodedata.normalize('NFD', str(value or '')).replace('đ', 'd').replace('Đ', 'D')
    return ' '.join(''.join(ch for ch in text if unicodedata.category(ch) != 'Mn').casefold().split())


def column_letter(index):
    letters = ''
    while index:
        index, rest = divmod(index - 1, 26)
        letters = chr(65 + rest) + letters
    return letters


def read_clock(value):
    """Return ``(time or None, kind, raw)``; kind is empty/time/code/multi/invalid."""
    if value is None:
        return None, 'empty', ''
    if isinstance(value, bool):
        return None, 'invalid', str(value)
    if isinstance(value, datetime):
        return value.time().replace(microsecond=0), 'time', value.strftime('%H:%M')
    if isinstance(value, time):
        return value.replace(microsecond=0), 'time', value.strftime('%H:%M')
    if isinstance(value, (int, float)):
        # Excel stores a clock as a fraction of a day; anything else is not a time.
        if 0 <= value < 1:
            seconds = round(value * 86400)
            if seconds >= 86400:
                return None, 'invalid', str(value)
            clock = time(seconds // 3600, seconds % 3600 // 60, seconds % 60)
            return clock, 'time', clock.strftime('%H:%M')
        return None, 'invalid', str(value)
    raw = str(value).strip()
    if not raw:
        return None, 'empty', ''
    parts = raw.split()
    if len(parts) > 1 and all(TIME_RE.match(part) for part in parts):
        return None, 'multi', raw
    match = TIME_RE.match(raw)
    if match:
        hour, minute, second = int(match[1]), int(match[2]), int(match[3] or 0)
        if hour < 24 and minute < 60 and second < 60:
            return time(hour, minute, second), 'time', raw[:5] if len(raw) >= 5 else raw
        return None, 'invalid', raw
    if CODE_RE.match(raw):
        return None, 'code', raw.upper()
    return None, 'invalid', raw[:32]


def _check_container(data):
    if not data:
        msg = 'Chưa chọn tệp Excel.'
        raise AttendanceFormatError(msg)
    if len(data) > MAX_BYTES:
        msg = 'Tệp lớn hơn 5 MB; hãy tách theo tuần hoặc tháng.'
        raise AttendanceFormatError(msg)
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            names = set(archive.namelist())
    except zipfile.BadZipFile:
        msg = 'Chỉ nhận tệp .xlsx (báo cáo máy chấm công).'
        raise AttendanceFormatError(msg) from None
    if 'xl/workbook.xml' not in names:
        msg = 'Chỉ nhận tệp .xlsx (báo cáo máy chấm công).'
        raise AttendanceFormatError(msg)
    if any(name.lower().endswith('vbaproject.bin') for name in names):
        msg = 'Tệp có macro; hãy lưu lại dạng .xlsx không macro rồi nhập.'
        raise AttendanceFormatError(msg)


def _period(sheet, header_row):
    for row in sheet.iter_rows(min_row=1, max_row=max(1, header_row - 1), values_only=True):
        for value in row:
            if isinstance(value, str):
                match = PERIOD_RE.search(value)
                if match:
                    d1, m1, y1, d2, m2, y2 = map(int, match.groups())
                    try:
                        return date(y1, m1, d1), date(y2, m2, d2)
                    except ValueError:
                        return None
    return None


def _day_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (datetime, date)):
        return value.day
    if isinstance(value, (int, float)) and float(value).is_integer() and 1 <= value <= 31:
        return int(value)
    if isinstance(value, str) and value.strip().isdigit() and 1 <= int(value.strip()) <= 31:
        return int(value.strip())
    return None


def _code(value):
    if value is None or isinstance(value, bool):
        return ''
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).strip()
    return str(int(text)) if text.isdigit() and int(text) > 0 else ''


def read_late_number(value):
    """``(int or None, raw)``: a machine total must be a whole number >= 0; anything else is not guessed."""
    if value is None:
        return None, ''
    if isinstance(value, bool):
        return False, str(value)
    if isinstance(value, (int, float)):
        if float(value).is_integer() and value >= 0:
            return int(value), str(int(value))
        return False, str(value)
    raw = str(value).strip()
    if not raw:
        return None, ''
    if raw.isdigit():
        return int(raw), raw
    return False, raw[:32]


def late_state(count, minutes):
    """Classify a Lần / Phút pair read by :func:`read_late_number` (``None`` = empty, ``False`` = invalid)."""
    if count is None and minutes is None:
        return 'empty'
    if count is False or minutes is False or count is None or minutes is None:
        return 'invalid'
    if (count == 0) != (minutes == 0):
        return 'inconsistent'
    return 'ok'


def _merged_span(sheet, row, column):
    for merged in sheet.merged_cells.ranges:
        if merged.min_row <= row <= merged.max_row and merged.min_col <= column <= merged.max_col:
            return merged.min_row, merged.max_row, merged.min_col, merged.max_col
    return row, row, column, column


def find_late_columns(sheet, header_row, skip=()):
    """Locate the "Đi muộn" group under the header: ``{'state', 'count', 'minutes', 'ref', 'message'}``.

    The group label sits on the header row (or the row below when the header is shifted) and its
    Lần / Phút sub-labels on the next row inside the group's merged span (or the two cells below).
    """
    found = []
    for row in (header_row, header_row + 1):
        for column in range(1, sheet.max_column + 1):
            if column in skip:
                continue
            if fold(sheet.cell(row, column).value) in LATE_HEADERS:
                found.append((row, column))
    if not found:
        return {'state': 'no_column', 'count': None, 'minutes': None, 'ref': '',
                'message': 'Không có cột Đi muộn; số đi muộn: Chưa có số liệu.'}
    if len(found) > 1:
        refs = ', '.join(f'{column_letter(column)}{row}' for row, column in found)
        return {'state': 'ambiguous', 'count': None, 'minutes': None, 'ref': refs,
                'message': f'Có nhiều nhóm Đi muộn ({refs}); không tự chọn.'}
    row, column = found[0]
    _top, bottom, first, last = _merged_span(sheet, row, column)
    if last == first:
        last = min(sheet.max_column, first + 1)
    count = minutes = None
    for sub in range(first, last + 1):
        label = fold(sheet.cell(bottom + 1, sub).value)
        if label in LATE_COUNT and count is None:
            count = sub
        elif label in LATE_MINUTES and minutes is None:
            minutes = sub
    ref = f'{column_letter(first)}{row}:{column_letter(last)}{bottom + 1}'
    if not count or not minutes:
        return {'state': 'partial', 'count': None, 'minutes': None, 'ref': ref,
                'message': f'Nhóm Đi muộn ({ref}) thiếu cột Lần hoặc Phút; số đi muộn: Chưa có số liệu.'}
    return {'state': 'ok', 'count': count, 'minutes': minutes, 'ref': ref, 'label_row': bottom + 1, 'message': ''}


def map_day_columns(sheet, header_row, span, skip=()):
    """``({column: date}, [errors])`` for the numeric day headers, read left to right.

    A day number matches the next date of the period with that day (and the weekday label below it
    when present). When the same number could still mean two dates the cell is reported, not guessed.
    """
    columns = []
    for column in range(1, sheet.max_column + 1):
        if column in skip:
            continue
        number = _day_number(sheet.cell(header_row, column).value)
        if number is not None:
            columns.append((column, number, fold(sheet.cell(header_row + 1, column).value)))
    dates, errors = {}, []
    if len(columns) == len(span) and all(number == day.day for (_c, number, _l), day in zip(columns, span, strict=True)):
        for (column, _number, label), day in zip(columns, span, strict=True):
            if label in WEEKDAYS and WEEKDAYS[label] != day.weekday():
                errors.append(f'Thứ của ngày {day:%d/%m/%Y} ({label.upper()}, ô {column_letter(column)}{header_row + 1}) không khớp lịch.')
            else:
                dates[column] = day
        return dates, errors
    floor = None
    for column, number, label in columns:
        cell = f'{column_letter(column)}{header_row}'
        candidates = [day for day in span if day.day == number and (floor is None or day > floor)]
        if label in WEEKDAYS:
            matching = [day for day in candidates if day.weekday() == WEEKDAYS[label]]
            if candidates and not matching:
                errors.append(f'Thứ của ngày {number} ({label.upper()}, ô {column_letter(column)}{header_row + 1}) không khớp lịch.')
                continue
            candidates = matching
        if not candidates:
            errors.append(f'Cột ngày {number} (ô {cell}) không thuộc kỳ {span[0]:%d/%m/%Y}–{span[-1]:%d/%m/%Y}.')
            continue
        if len(candidates) > 1:
            choices = ' hoặc '.join(f'{day:%d/%m/%Y}' for day in candidates)
            errors.append(f'Ô {cell}: ngày {number} có thể là {choices}; header chưa đủ để xác định, cần xem lại.')
            continue
        dates[column] = floor = candidates[0]
    return dates, errors


def _person_late(sheet, row_number, out_row, late):
    """Read Lần / Phút on the Vào row (vertical merges keep the value there), else on the Ra row."""
    values = {}
    for key in ('count', 'minutes'):
        column = late[key]
        number, raw = read_late_number(sheet.cell(row_number, column).value)
        if number is None and out_row:
            number, raw = read_late_number(sheet.cell(out_row, column).value)
        values[key] = (number, raw)
    (count, raw_count), (minutes, raw_minutes) = values['count'], values['minutes']
    state = late_state(count, minutes)
    return {
        'late_state': state, 'late_count': count if state in ('ok', 'inconsistent') else None,
        'late_minutes': minutes if state in ('ok', 'inconsistent') else None,
        'late_raw_count': raw_count, 'late_raw_minutes': raw_minutes,
        'late_cell': f"{column_letter(late['count'])}{row_number}:{column_letter(late['minutes'])}{row_number}",
    }


def parse_sheet(sheet, sheet_index):
    """Return ``{'name', 'period', 'events', 'errors', 'employees', 'empty_cells'}`` for one sheet."""
    result = {'name': sheet.title, 'index': sheet_index, 'period': None, 'events': [], 'errors': [], 'employees': 0,
              'people': [], 'empty_cells': 0, 'late': {'state': 'no_column', 'ref': '', 'message': ''}}
    if sheet.max_row > MAX_ROWS:
        result['errors'].append(f'Trang có hơn {MAX_ROWS} dòng.')
        return result
    header_row, columns = None, {}
    for row_number, row in enumerate(sheet.iter_rows(min_row=1, max_row=min(sheet.max_row, 40), values_only=True), 1):
        folded = [fold(value) for value in row]
        if 'stt' in folded and 'id' in folded:
            header_row = row_number
            columns = {HEADERS[name]: index + 1 for index, name in enumerate(folded) if name in HEADERS}
            break
    if not header_row or 'machine_code' not in columns:
        result['errors'].append('Không tìm thấy dòng tiêu đề STT / Mã nhân viên / Tên nhân viên / ID.')
        return result
    period = _period(sheet, header_row)
    if not period or period[1] < period[0] or (period[1] - period[0]).days > 31:
        result['errors'].append('Không đọc được kỳ "Từ ngày … Đến ngày …" phía trên tiêu đề.')
        return result
    result['period'] = period
    span = [period[0] + timedelta(days=offset) for offset in range((period[1] - period[0]).days + 1)]
    late = find_late_columns(sheet, header_row, skip=set(columns.values()))
    skip = set(columns.values()) | ({late['count'], late['minutes']} if late['state'] == 'ok' else set())
    dates, errors = map_day_columns(sheet, header_row, span, skip=skip)
    result['errors'].extend(errors)
    result['late'] = {key: late[key] for key in ('state', 'ref', 'message')}
    if late['state'] == 'ok':
        result['late'].update(count_col=column_letter(late['count']), minutes_col=column_letter(late['minutes']))
    if result['errors']:
        return result
    if not dates:
        result['errors'].append('Không có cột ngày trong kỳ.')
        return result
    label_column = None
    for row in sheet.iter_rows(min_row=header_row + 1, max_row=sheet.max_row):
        for cell in row:
            if fold(cell.value) == 'vao':
                label_column = cell.column
                break
        if label_column:
            break
    if not label_column:
        result['errors'].append('Không tìm thấy cột Vào/Ra.')
        return result
    vertical = {(merged.min_row, merged.min_col) for merged in sheet.merged_cells.ranges
                if merged.max_row > merged.min_row and merged.min_col in dates}
    group = ''
    first_column = columns.get('stt') or min(columns.values())
    for row_number in range(header_row + 2, sheet.max_row + 1):
        label = fold(sheet.cell(row_number, label_column).value)
        first = sheet.cell(row_number, first_column).value
        if label != 'vao':
            if label != 'ra' and isinstance(first, str) and first.strip() and not _code(sheet.cell(row_number, columns['machine_code']).value):
                group = first.strip()
            continue
        out_row = row_number + 1 if fold(sheet.cell(row_number + 1, label_column).value) == 'ra' else None
        identity = {key: sheet.cell(row_number, index).value for key, index in columns.items()}
        machine_code = _code(identity.get('machine_code')) or _code(identity.get('source_code'))
        result['employees'] += 1
        person = {'row': row_number, 'machine_code': machine_code, 'name': str(identity.get('name') or '').strip(),
                  'source_code': _code(identity.get('source_code')), 'group': group}
        if late['state'] == 'ok':
            person.update(_person_late(sheet, row_number, out_row, late))
        result['people'].append(person)
        base = {
            'sheet': sheet.title, 'sheet_index': sheet_index, 'row': row_number, 'machine_code': machine_code,
            'source_code': _code(identity.get('source_code')), 'name': str(identity.get('name') or '').strip(),
            'title': str(identity.get('title') or '').strip(), 'group': group,
        }
        for column, work_date in sorted(dates.items()):
            clock_in, kind_in, raw_in = read_clock(sheet.cell(row_number, column).value)
            clock_out, kind_out, raw_out = read_clock(sheet.cell(out_row, column).value) if out_row else (None, 'empty', '')
            if kind_in == 'empty' and kind_out == 'empty':
                result['empty_cells'] += 1
                continue
            if 'multi' in (kind_in, kind_out):
                kind = 'multi'
            elif 'invalid' in (kind_in, kind_out) or not machine_code:
                kind = 'invalid'
            elif 'code' in (kind_in, kind_out):
                kind = 'code' if 'time' not in (kind_in, kind_out) else 'invalid'
            elif (row_number, column) in vertical:
                kind = 'merged'
            elif clock_in and clock_out:
                kind = 'pair' if clock_out > clock_in else 'reversed'
            else:
                kind = 'missing_out' if clock_in else 'missing_in'
            cell_end = f':{column_letter(column)}{out_row}' if out_row else ''
            result['events'].append(dict(
                base, column=column, cell=f'{column_letter(column)}{row_number}{cell_end}', work_date=work_date,
                kind=kind, clock_in=clock_in, clock_out=clock_out, raw_in=raw_in, raw_out=raw_out,
            ))
    if not result['employees']:
        result['errors'].append('Không có dòng nhân viên (Vào/Ra) dưới tiêu đề.')
    return result


def parse_attendance(data):
    _check_container(data)
    try:
        book = load_workbook(BytesIO(data), data_only=True, keep_links=False, keep_vba=False)
    except Exception as exc:
        msg = 'Không đọc được tệp Excel.'
        raise AttendanceFormatError(msg) from exc
    try:
        if len(book.worksheets) > MAX_SHEETS:
            msg = f'Tệp có hơn {MAX_SHEETS} trang.'
            raise AttendanceFormatError(msg)
        sheets = [parse_sheet(sheet, index) for index, sheet in enumerate(book.worksheets)]
    finally:
        book.close()
    if not any(sheet['events'] or sheet['employees'] for sheet in sheets):
        errors = '; '.join(f"{sheet['name']}: {' '.join(sheet['errors'])}" for sheet in sheets if sheet['errors'])
        raise AttendanceFormatError('Không nhận ra báo cáo chấm công. ' + errors)
    return sheets
