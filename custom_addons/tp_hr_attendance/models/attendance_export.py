"""Attendance workbook "Report" matching the TANPHAT ONE timesheet template.

Pure layout and calculation helpers (no ORM): ``attendance_overview`` prepares one report dict from the
canonical backend figures and this module builds a single-sheet ``.xlsx`` named ``Report``.

Structure:
- Row 2: ``BẢNG CÔNG THÁNG``
- Row 3: ``Từ ngày dd/mm/yyyy - Đến ngày dd/mm/yyyy``
- Rows 5-6: two-tier header (STT, Mã nhân viên, Tên nhân viên, ID, Chức vụ, Vào/Ra, day number + weekday,
  Đi muộn [Lần, Phút], Số ngày, Ghi chú)
- Department group banner rows followed by two consecutive rows (Vào / Ra) per employee; identity, summary
  and note cells are vertically merged across the two rows so row 2 stays blank and values never repeat.
"""
from datetime import date, time
from io import BytesIO
from math import ceil

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import PageSetupProperties

from .attendance_logic import WEEKDAY_LABELS, xlsx_safe

FONT_NAME = 'Times New Roman'
HEADER_FILL = 'F2F2F2'
GROUP_FILL = 'F5F5F5'
GRID = Side(style='thin', color='000000')
BORDER = Border(left=GRID, right=GRID, top=GRID, bottom=GRID)
CENTER = Alignment(horizontal='center', vertical='center')
CENTER_WRAP = Alignment(horizontal='center', vertical='center', wrap_text=True)
LEFT = Alignment(horizontal='left', vertical='center')
LEFT_WRAP = Alignment(horizontal='left', vertical='center', wrap_text=True)

HEADER_ROW = 5             # rows 5-6: two-tier header; data starts at row 7
IDENTITY = ('STT', 'Mã nhân viên', 'Tên nhân viên', 'ID', 'Chức vụ', 'Vào/Ra')
IDENTITY_WIDTHS = (5, 13, 26, 8, 16, 7)
DAY_WIDTH = 6.5
LATE_COUNT_WIDTH = 7
LATE_MIN_WIDTH = 8
WORKED_DAYS_WIDTH = 9
NOTE_WIDTH = 34
DAYS_PER_PAGE = 16
NON_WORKED_STATES = ('future', 'off', 'rest', 'leave', 'absent', 'no_punch', 'no_source')
SOURCE_NAMES = {'enti': 'ENTI', 'excel': 'Excel máy (lịch sử)', 'correction': 'Điều chỉnh đã duyệt',
                'api': 'Máy chấm công'}
NOTE_DATES = 8


def _fill(color):
    return PatternFill('solid', start_color=color, end_color=color)


def _font(bold=False, color='000000', size=9, italic=False):
    return Font(name=FONT_NAME, size=size, bold=bold, italic=italic, color=color)


def as_time(text):
    """``'08:05'`` or ``'08:05:30'`` -> ``time(8, 5)``; ``None`` when blank or invalid."""
    try:
        raw = str(text or '').strip()
        if not raw:
            return None
        if 'T' in raw or ' ' in raw:
            raw = raw.replace('T', ' ').split(' ', 1)[1]
        parts = raw.split(':')
        if len(parts) < 2:
            return None
        hour, minute = int(parts[0]), int(parts[1])
        return time(hour, minute)
    except (TypeError, ValueError):
        return None


def format_clock(text):
    """Normalize a clock string to ``HH:mm`` (no seconds, no datetime); ``''`` when empty."""
    parsed = as_time(text)
    return f'{parsed.hour:02d}:{parsed.minute:02d}' if parsed else ''


def _machine_id_value(raw):
    text = str(raw or '').strip()
    if not text:
        return ''
    return int(text) if text.isdigit() else text


def worked_days_count(cells):
    """Count unique non-Sunday days in ``cells`` (``{date: cell}``) with a valid clock-in or clock-out."""
    count = 0
    for day in sorted(cells):
        if day.weekday() == 6:
            continue
        cell = cells[day] or {}
        if cell.get('state') in NON_WORKED_STATES:
            continue
        if as_time(cell.get('in')) is not None or as_time(cell.get('out')) is not None:
            count += 1
    return count


def export_late_totals(cells, view=None, start_hour=8.5, today=None):
    """Return ``(late_count, late_minutes)`` as non-negative integers.

    Uses exact pre-aggregated source totals when available (e.g. historical Excel period totals); otherwise
    uses ENTI daily ``late`` minutes when present and falls back to ``clock_in - start_hour`` (default 08:30)
    for scheduled non-Sunday working days that have a check-in clock.
    """
    view = view or {}
    if view.get('state') == 'exact' and view.get('source') not in ('', 'ENTI', None):
        return max(0, round(view.get('count') or 0)), max(0, round(view.get('minutes') or 0))

    ref_minutes = round(start_hour * 60)
    count = 0
    minutes = 0
    for day in sorted(cells):
        if day.weekday() == 6 or (today and day > today):
            continue
        cell = cells[day] or {}
        if cell.get('state') in NON_WORKED_STATES:
            continue
        if not cell.get('scheduled', True):
            continue
        t_in = as_time(cell.get('in'))
        if t_in is None:
            continue
        if cell.get('late') is not None:
            late_min = max(0, round(cell['late']))
        else:
            late_min = max(0, (t_in.hour * 60 + t_in.minute) - ref_minutes)
        if late_min > 0:
            count += 1
            minutes += late_min
    return count, minutes


def _dates(days):
    shown = ', '.join(f'{day:%d/%m}' for day in days[:NOTE_DATES])
    return shown + (f' … (+{len(days) - NOTE_DATES})' if len(days) > NOTE_DATES else '')


def person_note(cells, late=None, absence=None, archived=False, *, duplicate_days=None, today=None):
    """Concise Vietnamese note for one employee; returns ``''`` when nothing needs attention."""
    ordered = sorted(cells.items())
    missing_in = [day for day, cell in ordered
                  if cell.get('state') in ('missing', 'review') and as_time(cell.get('in')) is None]
    missing_out = [day for day, cell in ordered
                   if cell.get('state') in ('missing', 'review')
                   and as_time(cell.get('in')) is not None and as_time(cell.get('out')) is None]
    anomaly = [day for day, cell in ordered
               if cell.get('state') == 'review'
               and as_time(cell.get('in')) is not None and as_time(cell.get('out')) is not None]
    leave_days = [day for day, cell in ordered if cell.get('state') == 'leave']
    dup_days = sorted(duplicate_days or ())

    parts = []
    if missing_in:
        parts.append(f'Thiếu giờ vào: {_dates(missing_in)}')
    if missing_out:
        parts.append(f'Thiếu giờ ra: {_dates(missing_out)}')
    if anomaly:
        parts.append(f'Có dữ liệu bất thường: {_dates(anomaly)}')
    if dup_days:
        parts.append(f'Có bản ghi trùng cần đối chiếu: {_dates(dup_days)}')
    if leave_days:
        parts.append(f'Nghỉ: {_dates(leave_days)}')

    if not parts and worked_days_count(cells) == 0:
        past_workdays = [day for day, cell in ordered
                         if day.weekday() != 6 and (not today or day <= today)
                         and cell.get('state') in ('absent', 'no_punch', 'no_source')]
        if past_workdays:
            parts.append('Không có dữ liệu trong kỳ')

    if archived:
        parts.append('Hồ sơ đã lưu trữ')
    return '\n'.join(parts)


def _style(cell, *, font=None, fill=None, align=CENTER, border=True, number_format=None):
    cell.font = font or _font()
    if fill:
        cell.fill = _fill(fill)
    cell.alignment = align
    if border:
        cell.border = BORDER
    if number_format:
        cell.number_format = number_format


def _put(sheet, row, column, value, **style):
    safe_val = value if isinstance(value, (date, time)) else xlsx_safe(value)
    if isinstance(safe_val, str) and not safe_val:
        safe_val = None
    cell = sheet.cell(row, column, safe_val)
    _style(cell, **style)
    return cell


def _merge(sheet, first_row, first_col, last_row, last_col, value, **style):
    """Merge cells and apply uniform border/style across every cell in the merged region."""
    for row in range(first_row, last_row + 1):
        for column in range(first_col, last_col + 1):
            _style(sheet.cell(row, column), **style)
    if (first_row, first_col) != (last_row, last_col):
        sheet.merge_cells(start_row=first_row, start_column=first_col, end_row=last_row, end_column=last_col)
    return _put(sheet, first_row, first_col, value, **style)


def _pair_row_height(name_text, job_text, note_text, name_width, job_width, note_width):
    """Compute height per row of a 2-row employee block so wrapped text never overflows."""
    def _line_count(text, width):
        if not text:
            return 1
        eff = max(8, width * 0.95)
        return sum(max(1, ceil(len(part) / eff)) for part in str(text).split('\n'))

    max_lines = max(
        _line_count(name_text, name_width),
        _line_count(job_text, job_width),
        _line_count(note_text, note_width),
    )
    return max(15.5, ceil((max_lines * 12.5) / 2) + 2.5)


def _print_setup(sheet, title_rows, title_cols, pages_wide, print_area):
    sheet.page_setup.orientation = 'landscape'
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
    sheet.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    sheet.page_setup.fitToWidth = pages_wide
    sheet.page_setup.fitToHeight = 0
    sheet.print_title_rows = title_rows
    if title_cols:
        sheet.print_title_cols = title_cols
    sheet.print_area = print_area
    sheet.print_options.horizontalCentered = True
    sheet.page_margins.left = sheet.page_margins.right = 0.3
    sheet.page_margins.top = sheet.page_margins.bottom = 0.4
    sheet.oddFooter.center.text = 'Trang &P / &N'
    sheet.sheet_view.zoomScale = 100


def _report_sheet(sheet, report):
    days = report['days']
    first_day = len(IDENTITY) + 1
    late_col = first_day + len(days)
    days_col = late_col + 2
    note_col = days_col + 1
    last_col = note_col

    # ---- rows 1-4: minimalist title block matching sample template
    sheet.row_dimensions[1].height = 10
    _merge(sheet, 2, 1, 2, last_col, report.get('title') or 'BẢNG CÔNG THÁNG',
           font=_font(True, size=14), align=CENTER, border=False)
    sheet.row_dimensions[2].height = 24
    _merge(sheet, 3, 1, 3, last_col, report['period'],
           font=_font(True, size=10), align=CENTER, border=False)
    sheet.row_dimensions[3].height = 18
    sheet.row_dimensions[4].height = 8

    # ---- rows 5-6: two-tier table header
    head_font = _font(True, size=9)
    top, bottom = HEADER_ROW, HEADER_ROW + 1
    for column, label in enumerate(IDENTITY, 1):
        _merge(sheet, top, column, bottom, column, label, font=head_font, fill=HEADER_FILL, align=CENTER_WRAP)
    for offset, day in enumerate(days):
        column = first_day + offset
        _put(sheet, top, column, day.day, font=head_font, fill=HEADER_FILL, align=CENTER, number_format='0')
        _put(sheet, bottom, column, WEEKDAY_LABELS[day.weekday()], font=head_font, fill=HEADER_FILL, align=CENTER)
    _merge(sheet, top, late_col, top, late_col + 1, 'Đi muộn', font=head_font, fill=HEADER_FILL, align=CENTER)
    _put(sheet, bottom, late_col, 'Lần', font=head_font, fill=HEADER_FILL, align=CENTER)
    _put(sheet, bottom, late_col + 1, 'Phút', font=head_font, fill=HEADER_FILL, align=CENTER)
    _merge(sheet, top, days_col, bottom, days_col, 'Số ngày', font=head_font, fill=HEADER_FILL, align=CENTER_WRAP)
    _merge(sheet, top, note_col, bottom, note_col, 'Ghi chú', font=head_font, fill=HEADER_FILL, align=CENTER_WRAP)
    sheet.row_dimensions[top].height = 20
    sheet.row_dimensions[bottom].height = 18

    # ---- body: department groups & 2 rows per employee
    row = bottom + 1
    serial = 0
    totals = {'people': 0, 'count': 0, 'minutes': 0, 'worked_days': 0}
    max_name_len = len('Tên nhân viên')
    max_job_len = len('Chức vụ')
    max_note_len = 24

    groups = [group for group in report.get('groups', []) if group.get('people')]
    if not groups:
        _merge(sheet, row, 1, row, last_col, 'Không có dữ liệu trong kỳ đã chọn',
               font=_font(italic=True, size=9), align=CENTER)
        sheet.row_dimensions[row].height = 24
        last_row = row
    else:
        body_font = _font(size=9)
        group_font = _font(True, size=9)
        for group in groups:
            _merge(sheet, row, 1, row, last_col, group['name'],
                   font=group_font, fill=GROUP_FILL, align=LEFT)
            sheet.row_dimensions[row].height = 19
            row += 1
            for group_serial, person in enumerate(group['people'], 1):
                serial += 1
                name_text = person.get('name') or ''
                job_text = person.get('job') or ''
                note_text = person.get('note') or ''
                max_name_len = max(max_name_len, len(name_text))
                max_job_len = max(max_job_len, len(job_text))
                if note_text:
                    max_note_len = max(max_note_len, *(len(line) for line in note_text.split('\n')))

                identity_vals = (
                    group_serial,
                    person.get('code') or '',
                    name_text,
                    _machine_id_value(person.get('machine_code')),
                    job_text,
                )
                for column, value in enumerate(identity_vals, 1):
                    align = LEFT_WRAP if column == 3 else (CENTER_WRAP if column == 5 else CENTER)
                    _merge(sheet, row, column, row + 1, column, value, font=body_font, align=align)

                _put(sheet, row, len(IDENTITY), 'Vào', font=body_font, align=CENTER)
                _put(sheet, row + 1, len(IDENTITY), 'Ra', font=body_font, align=CENTER)

                cells = person.get('cells') or {}
                for offset, day in enumerate(days):
                    column = first_day + offset
                    cell = cells.get(day, {})
                    _put(sheet, row, column, format_clock(cell.get('in')), font=body_font, align=CENTER)
                    _put(sheet, row + 1, column, format_clock(cell.get('out')), font=body_font, align=CENTER)

                late = person.get('late') or {}
                late_count = max(0, round(late.get('count') or 0))
                late_minutes = max(0, round(late.get('minutes') or 0))
                worked_days = max(0, round(person.get('worked_days') or 0))
                totals['people'] += 1
                totals['count'] += late_count
                totals['minutes'] += late_minutes
                totals['worked_days'] += worked_days

                _merge(sheet, row, late_col, row + 1, late_col, late_count,
                       font=body_font, align=CENTER, number_format='0')
                _merge(sheet, row, late_col + 1, row + 1, late_col + 1, late_minutes,
                       font=body_font, align=CENTER, number_format='#,##0')
                _merge(sheet, row, days_col, row + 1, days_col, worked_days,
                       font=body_font, align=CENTER, number_format='0')
                _merge(sheet, row, note_col, row + 1, note_col, note_text,
                       font=body_font, align=LEFT_WRAP)

                row_h = _pair_row_height(name_text, job_text, note_text, 28, 18, NOTE_WIDTH)
                sheet.row_dimensions[row].height = row_h
                sheet.row_dimensions[row + 1].height = row_h
                row += 2
        last_row = row - 1

    # ---- column widths, freeze panes, print setup
    name_width = min(max(IDENTITY_WIDTHS[2], max_name_len + 3), 38)
    job_width = min(max(IDENTITY_WIDTHS[4], max_job_len + 3), 26)
    note_width = min(max(NOTE_WIDTH, max_note_len + 3), 46)
    widths = [IDENTITY_WIDTHS[0], IDENTITY_WIDTHS[1], name_width, IDENTITY_WIDTHS[3], job_width, IDENTITY_WIDTHS[5]]
    for column, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(column)].width = width
    for offset in range(len(days)):
        sheet.column_dimensions[get_column_letter(first_day + offset)].width = DAY_WIDTH
    sheet.column_dimensions[get_column_letter(late_col)].width = LATE_COUNT_WIDTH
    sheet.column_dimensions[get_column_letter(late_col + 1)].width = LATE_MIN_WIDTH
    sheet.column_dimensions[get_column_letter(days_col)].width = WORKED_DAYS_WIDTH
    sheet.column_dimensions[get_column_letter(note_col)].width = note_width

    sheet.freeze_panes = f'{get_column_letter(first_day)}{bottom + 1}'
    pages_wide = max(1, ceil(len(days) / DAYS_PER_PAGE))
    print_area = f'A1:{get_column_letter(last_col)}{last_row}'
    _print_setup(sheet, f'{top}:{bottom}', f'A:{get_column_letter(len(IDENTITY))}', pages_wide, print_area)
    return totals


def build_attendance_book(report):
    """``report`` -> ``(.xlsx bytes, totals)``. Single sheet named ``Report``."""
    book = Workbook()
    sheet = book.active
    sheet.title = 'Report'
    totals = _report_sheet(sheet, report)
    book.properties.title = report.get('title') or 'BẢNG CÔNG THÁNG'
    book.properties.creator = 'TANPHAT ONE'
    stream = BytesIO()
    book.save(stream)
    return stream.getvalue(), totals
