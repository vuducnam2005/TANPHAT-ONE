"""Reader for the machine attendance report: one Vào row and one Ra row per employee, one column per day.

Pure functions (no ORM) so the format rules stay unit-testable. Summary columns of the machine report
(late, absent, totals, notes) are never read; only the identity cells, the period header and day cells.
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


def parse_sheet(sheet, sheet_index):
    """Return ``{'name', 'period', 'events', 'errors', 'employees', 'empty_cells'}`` for one sheet."""
    result = {'name': sheet.title, 'index': sheet_index, 'period': None, 'events': [], 'errors': [], 'employees': 0,
              'people': [], 'empty_cells': 0}
    if sheet.max_row > MAX_ROWS:
        result['errors'].append(f'Trang có hơn {MAX_ROWS} dòng.')
        return result
    header_row, columns = None, {}
    for row_number, row in enumerate(sheet.iter_rows(min_row=1, max_row=min(sheet.max_row, 40), values_only=True), 1):
        folded = [fold(value) for value in row]
        if folded and folded[0] == 'stt' and 'id' in folded:
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
    dates = {}
    span = [period[0] + timedelta(days=offset) for offset in range((period[1] - period[0]).days + 1)]
    for column in range(1, sheet.max_column + 1):
        number = _day_number(sheet.cell(header_row, column).value)
        if number is None or column in columns.values():
            continue
        matches = [day for day in span if day.day == number]
        if len(matches) != 1:
            result['errors'].append(f'Cột ngày {number} ({column_letter(column)}) không thuộc kỳ {period[0]:%d/%m/%Y}–{period[1]:%d/%m/%Y}.')
            continue
        label = fold(sheet.cell(header_row + 1, column).value)
        if label in WEEKDAYS and WEEKDAYS[label] != matches[0].weekday():
            result['errors'].append(f'Thứ của ngày {matches[0]:%d/%m/%Y} ({label.upper()}) không khớp lịch.')
            continue
        dates[column] = matches[0]
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
    for row_number in range(header_row + 2, sheet.max_row + 1):
        label = fold(sheet.cell(row_number, label_column).value)
        first = sheet.cell(row_number, 1).value
        if label != 'vao':
            if label != 'ra' and isinstance(first, str) and first.strip() and not _code(sheet.cell(row_number, columns['machine_code']).value):
                group = first.strip()
            continue
        out_row = row_number + 1 if fold(sheet.cell(row_number + 1, label_column).value) == 'ra' else None
        identity = {key: sheet.cell(row_number, index).value for key, index in columns.items()}
        machine_code = _code(identity.get('machine_code')) or _code(identity.get('source_code'))
        result['employees'] += 1
        result['people'].append({'row': row_number, 'machine_code': machine_code, 'name': str(identity.get('name') or '').strip()})
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
