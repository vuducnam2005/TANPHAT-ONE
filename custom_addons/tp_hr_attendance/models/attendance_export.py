"""Attendance workbook "Bảng chấm công" (ENTI-ATTENDANCE-002).

Pure layout code, no ORM: the model (``attendance_overview``) prepares one report dict from the same figures the
screens show, and this module turns it into an .xlsx. It follows the structure of the HR reference sheet (period
block, department group rows, two rows Vào / Ra per employee, days across, late count/minutes, absence) without its
overtime / worked-hour columns, plus an optional flat "Chi tiết" sheet (one row per employee and day, no merges).

Rules kept here: times and dates are real Excel values, a missing time is "—" (never 00:00), unknown numbers are
"—" (never 0), every text goes through ``xlsx_safe`` (no formula injection), Sunday keeps its real times.
"""
from datetime import date, time
from io import BytesIO
from math import ceil

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import PageSetupProperties

from .attendance_logic import WEEKDAY_LABELS, xlsx_safe

MISSING = '—'
FONT_NAME = 'Arial'
HEADER = '1E3A8A'          # dark blue header, white text
HEADER_SUNDAY = '475569'   # Sunday header column
DEPARTMENT = 'DBEAFE'      # department group rows
STRIPE = 'F1F5F9'          # every second employee
SUNDAY = 'E5E7EB'          # Sunday cells (light grey)
LATE = 'FED7AA'            # first-in later than the reference hour (ENTI late minutes > 0)
ATTENTION = 'FEF08A'       # missing time / needs checking
ABSENT = 'FECACA'          # absence established by the schedule
LEAVE = 'E0F2FE'           # approved leave
GRID = Side(style='thin', color='94A3B8')
BORDER = Border(left=GRID, right=GRID, top=GRID, bottom=GRID)
CENTER = Alignment(horizontal='center', vertical='center')
CENTER_WRAP = Alignment(horizontal='center', vertical='center', wrap_text=True)
LEFT = Alignment(horizontal='left', vertical='center')
LEFT_WRAP = Alignment(horizontal='left', vertical='center', wrap_text=True)

HEADER_ROW = 7             # rows 7-8: two header rows; data from row 9
IDENTITY = ('STT', 'Mã nhân viên', 'Tên nhân viên', 'ID', 'Chức vụ', 'Vào / Ra')
IDENTITY_WIDTHS = (5, 14, 25, 8, 16, 7)
DAY_WIDTH = 7
NOTE_WIDTH = 44
DAYS_PER_PAGE = 16         # print: a month spreads over two landscape pages instead of shrinking to one


def _fill(color):
    return PatternFill('solid', start_color=color, end_color=color)


def _font(bold=False, color='0F172A', size=9, italic=False):
    return Font(name=FONT_NAME, size=size, bold=bold, italic=italic, color=color)


def as_time(text):
    """``'08:05'`` → ``time(8, 5)``; ``None`` for an empty or unreadable clock (shown as "—")."""
    try:
        hour, minute = (int(part) for part in (text or '').split(':')[:2])
        return time(hour, minute)
    except (TypeError, ValueError):
        return None


def _day_marks(cell):
    """``(in_value, out_value, fill)`` for one employee/day cell of the matrix."""
    state = cell.get('state')
    if state in ('future', 'off', 'rest'):
        return '', '', None
    if state == 'absent':
        return 'Vắng', 'Vắng', ABSENT
    if state == 'leave':
        return 'Nghỉ', 'Nghỉ', LEAVE
    if state in ('no_source', 'no_punch'):
        return MISSING, MISSING, None
    attention = state in ('missing', 'review')
    first, last = as_time(cell.get('in')), as_time(cell.get('out'))
    return (first or MISSING, last or MISSING, ATTENTION if attention else None)


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
    cell = sheet.cell(row, column, xlsx_safe(value) if not isinstance(value, (date, time)) else value)
    _style(cell, **style)
    return cell


def _merge(sheet, first_row, first_col, last_row, last_col, value, **style):
    """Merged block with borders on every covered cell (Excel draws merged borders per cell)."""
    for row in range(first_row, last_row + 1):
        for column in range(first_col, last_col + 1):
            _style(sheet.cell(row, column), **style)
    if (first_row, first_col) != (last_row, last_col):
        sheet.merge_cells(start_row=first_row, start_column=first_col, end_row=last_row, end_column=last_col)
    return _put(sheet, first_row, first_col, value, **style)


def _note_height(text, width=NOTE_WIDTH):
    """Height (points) of each of the two rows of an employee so the merged note never overflows."""
    lines = sum(max(1, ceil(len(part) / (width * 1.05))) for part in (text or '').split('\n'))
    return max(15.0, ceil(lines * 12 / 2) + 2.0)


def _matrix(sheet, report):
    days = report['days']
    first_day = len(IDENTITY) + 1
    late_col = first_day + len(days)
    absent_col, note_col = late_col + 2, late_col + 3
    last_col = note_col

    # ---- period block (rows 1-5)
    blocks = [
        (f"TANPHAT ONE · {report['company']}", _font(True, '1E3A8A', 11), 18),
        (report['title'], _font(True, '0F172A', 15), 24),
        (report['period'], _font(True, '0F172A', 10), 16),
        (report['scope'], _font(False, '334155', 9), 15),
        (report['stamp'], _font(False, '334155', 9), 15),
    ]
    for row, (text, font, height) in enumerate(blocks, 1):
        _merge(sheet, row, 1, row, last_col, text, font=font, align=LEFT, border=False)
        sheet.row_dimensions[row].height = height
    sheet.row_dimensions[6].height = 6

    # ---- two header rows
    head = _font(True, 'FFFFFF')
    top, bottom = HEADER_ROW, HEADER_ROW + 1
    for column, label in enumerate(IDENTITY, 1):
        _merge(sheet, top, column, bottom, column, label, font=head, fill=HEADER, align=CENTER_WRAP)
    for offset, day in enumerate(days):
        column = first_day + offset
        fill = HEADER_SUNDAY if day.weekday() == 6 else HEADER
        _put(sheet, top, column, day, font=head, fill=fill, number_format='dd/mm')
        _put(sheet, bottom, column, WEEKDAY_LABELS[day.weekday()], font=head, fill=fill)
    _merge(sheet, top, late_col, top, late_col + 1, 'Đi muộn', font=head, fill=HEADER)
    _put(sheet, bottom, late_col, 'Số lần', font=head, fill=HEADER)
    _put(sheet, bottom, late_col + 1, 'Tổng phút', font=head, fill=HEADER)
    _put(sheet, top, absent_col, 'Vắng', font=head, fill=HEADER)
    _put(sheet, bottom, absent_col, 'Số ngày', font=head, fill=HEADER)
    _merge(sheet, top, note_col, bottom, note_col, 'Ghi chú cần kiểm tra', font=head, fill=HEADER, align=CENTER_WRAP)
    sheet.row_dimensions[top].height = 18
    sheet.row_dimensions[bottom].height = 18

    # ---- department groups, two rows per employee
    row = bottom + 1
    serial = 0
    totals = {'count': 0, 'minutes': 0, 'absent': 0, 'late_unknown': 0}
    for group in report['groups']:
        _merge(sheet, row, 1, row, last_col, f"{group['name']} · {len(group['people'])} người",
               font=_font(True, '1E3A8A', 10), fill=DEPARTMENT, align=LEFT)
        sheet.row_dimensions[row].height = 17
        row += 1
        for group_serial, person in enumerate(group['people'], 1):
            serial += 1
            stripe = STRIPE if serial % 2 == 0 else None
            body = _font()
            for column, value in enumerate((group_serial, person['code'] or MISSING, person['name'],
                                             person.get('machine_code') or MISSING, person['job'] or MISSING), 1):
                _merge(sheet, row, column, row + 1, column, value, font=body, fill=stripe,
                       align=LEFT_WRAP if column in (3, 5) else CENTER_WRAP)
            _put(sheet, row, len(IDENTITY), 'Vào', font=_font(True, '0F766E'), fill=stripe)
            _put(sheet, row + 1, len(IDENTITY), 'Ra', font=_font(True, '6D28D9'), fill=stripe)
            for offset, day in enumerate(days):
                column = first_day + offset
                cell = person['cells'].get(day, {})
                first, last, fill = _day_marks(cell)
                base = SUNDAY if day.weekday() == 6 else stripe
                first_fill = fill or base
                if isinstance(first, time) and (cell.get('late') or 0) > 0:
                    first_fill = LATE
                for target, value, color in ((row, first, first_fill), (row + 1, last, fill or base)):
                    is_time = isinstance(value, time)
                    font = _font(color='94A3B8') if value == MISSING else (
                        _font(True, 'B91C1C') if value == 'Vắng' else body)
                    _put(sheet, target, column, value, font=font, fill=color, number_format='hh:mm' if is_time else None)
            late = person['late']
            known = late.get('count') is not None
            if known:
                totals['count'] += late['count']
                totals['minutes'] += late['minutes']
            else:
                totals['late_unknown'] += 1
            totals['absent'] += person['absent']
            _merge(sheet, row, late_col, row + 1, late_col, late['count'] if known else MISSING, font=body, fill=stripe)
            _merge(sheet, row, late_col + 1, row + 1, late_col + 1, late['minutes'] if known else MISSING,
                   font=body, fill=stripe, number_format='#,##0' if known else None)
            _merge(sheet, row, absent_col, row + 1, absent_col, person['absent'],
                   font=_font(True, 'B91C1C') if person['absent'] else body, fill=stripe)
            _merge(sheet, row, note_col, row + 1, note_col, person['note'], font=_font(color='334155', size=8),
                   fill=stripe, align=LEFT_WRAP)
            height = _note_height(person['note'])
            sheet.row_dimensions[row].height = height
            sheet.row_dimensions[row + 1].height = height
            row += 2

    # ---- totals of the exported scope (same values as the rows above, for reconciliation)
    total_font = _font(True)
    _merge(sheet, row, 1, row, late_col - 1, f'Tổng cộng {serial} nhân viên', font=total_font, fill=DEPARTMENT,
           align=Alignment(horizontal='right', vertical='center'))
    known_any = serial > totals['late_unknown']
    _put(sheet, row, late_col, totals['count'] if known_any else MISSING, font=total_font, fill=DEPARTMENT)
    _put(sheet, row, late_col + 1, totals['minutes'] if known_any else MISSING, font=total_font, fill=DEPARTMENT,
         number_format='#,##0' if known_any else None)
    _put(sheet, row, absent_col, totals['absent'], font=total_font, fill=DEPARTMENT)
    unknown = totals['late_unknown']
    _put(sheet, row, note_col, (f'Tổng đi muộn chưa gồm {unknown} người thiếu dữ liệu đi muộn' if unknown else ''),
         font=_font(color='334155', size=8), fill=DEPARTMENT, align=LEFT_WRAP)
    sheet.row_dimensions[row].height = 18
    row += 2

    # ---- legend / notes
    for line in report['legend']:
        _merge(sheet, row, 1, row, last_col, line, font=_font(color='334155', size=8), align=LEFT_WRAP, border=False)
        sheet.row_dimensions[row].height = 13 * max(1, ceil(len(line) / 230))
        row += 1

    # ---- widths, freeze, print
    for column, width in enumerate(IDENTITY_WIDTHS, 1):
        sheet.column_dimensions[get_column_letter(column)].width = width
    for offset in range(len(days)):
        sheet.column_dimensions[get_column_letter(first_day + offset)].width = DAY_WIDTH
    sheet.column_dimensions[get_column_letter(late_col)].width = 8
    sheet.column_dimensions[get_column_letter(late_col + 1)].width = 10
    sheet.column_dimensions[get_column_letter(absent_col)].width = 8
    sheet.column_dimensions[get_column_letter(note_col)].width = NOTE_WIDTH
    sheet.freeze_panes = f'{get_column_letter(first_day)}{bottom + 1}'
    _print_setup(sheet, f'{top}:{bottom}', f'A:{get_column_letter(len(IDENTITY))}', max(1, ceil(len(days) / DAYS_PER_PAGE)))
    return totals


def _print_setup(sheet, title_rows, title_cols, pages_wide):
    sheet.page_setup.orientation = 'landscape'
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
    sheet.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    sheet.page_setup.fitToWidth = pages_wide
    sheet.page_setup.fitToHeight = 0
    sheet.print_title_rows = title_rows
    if title_cols:
        sheet.print_title_cols = title_cols
    sheet.print_options.horizontalCentered = True
    sheet.page_margins.left = sheet.page_margins.right = 0.3
    sheet.page_margins.top = sheet.page_margins.bottom = 0.5
    sheet.oddFooter.center.text = 'Trang &P / &N'
    sheet.sheet_view.zoomScale = 100


DETAIL_HEADER = ('Phòng ban', 'Mã NV', 'Họ và tên', 'Chức vụ', 'Ngày', 'Thứ', 'Giờ vào', 'Giờ ra',
                 'Phút đi muộn', 'Tình trạng', 'Nguồn')
DETAIL_WIDTHS = (22, 10, 25, 16, 12, 6, 9, 9, 12, 22, 22)


def _detail(sheet, report):
    detail = report['detail']
    _merge(sheet, 1, 1, 1, len(DETAIL_HEADER), detail['title'], font=_font(True, '1E3A8A', 11), align=LEFT, border=False)
    sheet.row_dimensions[1].height = 18
    head = _font(True, 'FFFFFF')
    for column, label in enumerate(DETAIL_HEADER, 1):
        _put(sheet, 3, column, label, font=head, fill=HEADER, align=CENTER_WRAP)
    sheet.row_dimensions[3].height = 18
    row = 4
    longest = [len(label) + 2 for label in DETAIL_HEADER]
    for item in detail['rows']:
        sunday = item['date'].weekday() == 6
        fill = SUNDAY if sunday else None
        values = (item['department'] or MISSING, item['code'] or MISSING, item['name'], item['job'] or MISSING,
                  item['date'], WEEKDAY_LABELS[item['date'].weekday()], as_time(item['in']) or MISSING,
                  as_time(item['out']) or MISSING, MISSING if item['late'] is None else item['late'],
                  item['state_label'], item['source'] or MISSING)
        for column, value in enumerate(values, 1):
            number_format = 'dd/mm/yyyy' if isinstance(value, date) else 'hh:mm' if isinstance(value, time) else None
            cell_fill = fill
            if column == 7 and isinstance(value, time) and (item['late'] or 0) > 0:
                cell_fill = LATE
            elif column in (7, 8) and value == MISSING and item['state'] in ('missing', 'review'):
                cell_fill = ATTENTION
            elif column == 10 and item['state'] == 'absent':
                cell_fill = ABSENT
            _put(sheet, row, column, value, font=_font(color='94A3B8') if value == MISSING else _font(),
                 fill=cell_fill, align=LEFT if column in (1, 3, 4, 10, 11) else CENTER, number_format=number_format)
            if isinstance(value, str):
                longest[column - 1] = max(longest[column - 1], len(value) + 2)
        row += 1
    for column, width in enumerate(DETAIL_WIDTHS, 1):
        # Wide enough for the longest text (no cut text / "####"), capped so one long name never dominates.
        sheet.column_dimensions[get_column_letter(column)].width = min(max(width, longest[column - 1]), 48)
    sheet.freeze_panes = 'D4'
    if row > 4:
        sheet.auto_filter.ref = f'A3:{get_column_letter(len(DETAIL_HEADER))}{row - 1}'
    _print_setup(sheet, '3:3', None, 1)


SOURCE_NAMES = {'enti': 'ENTI', 'excel': 'Excel máy (lịch sử)', 'correction': 'Điều chỉnh đã duyệt',
                'api': 'Máy chấm công'}
NOTE_DATES = 8


def _dates(days):
    shown = ', '.join(f'{day:%d/%m}' for day in days[:NOTE_DATES])
    return shown + (f' … (+{len(days) - NOTE_DATES})' if len(days) > NOTE_DATES else '')


def person_note(cells, late, absence, archived=False):
    """"Ghi chú cần kiểm tra" of one employee: what is missing or uncertain in the exported range, nothing else.

    ``cells`` ``{date: cell}``; ``late`` the late view (``state``/``text``/``note``/``source``); ``absence`` the
    absence total (``unknown`` = scheduled days without any source, never counted as absent)."""
    ordered = sorted(cells.items())
    missing_in = [day for day, cell in ordered if cell['state'] in ('missing', 'review') and not cell.get('in')]
    missing_out = [day for day, cell in ordered
                   if cell['state'] in ('missing', 'review') and cell.get('in') and not cell.get('out')]
    review = [day for day, cell in ordered if cell['state'] == 'review' and cell.get('in') and cell.get('out')]
    parts = []
    if missing_in:
        parts.append(f'Thiếu giờ vào: {_dates(missing_in)}')
    if missing_out:
        parts.append(f'Thiếu giờ ra: {_dates(missing_out)}')
    if review:
        parts.append(f'Cần kiểm tra: {_dates(review)}')
    if absence.get('unknown'):
        parts.append(f"Chưa có dữ liệu {absence['unknown']} ngày làm (không tính vắng)")
    if late['state'] != 'exact':
        parts.append(f"Đi muộn: {late.get('text') or 'chưa có số liệu'}")
    elif late.get('source') and late['source'] != 'ENTI':
        parts.append(f"Đi muộn lấy theo {late['note']}")
    if archived:
        parts.append('Hồ sơ đã lưu trữ, vẫn có dữ liệu trong kỳ')
    return '\n'.join(parts)


def legend(period, hours, absence_note):
    return [
        'Ghi chú:',
        (f'• Giờ làm tham chiếu {hours}. ENTI chỉ trả giờ vào đầu tiên và giờ ra cuối cùng mỗi ngày; '
         'Odoo không tự thêm lượt chấm và không tự điền giờ.'),
        ('• Ký hiệu: "—" = chưa có giờ / thiếu dữ liệu (không ghi 00:00); "Vắng" = vắng theo lịch đã xác định; '
         '"Nghỉ" = nghỉ đã xác nhận; ô trống = ngày chưa đến, ngày nghỉ theo lịch hoặc ngoài thời gian làm việc.'),
        ('• Màu: cam = giờ vào đi muộn theo ENTI; vàng = thiếu giờ / cần kiểm tra; đỏ nhạt = vắng đã xác định; '
         'xám = Chủ nhật (vẫn giữ giờ thực tế nếu có).'),
        (f'• Đi muộn: "Số lần" = số ngày có phút đi muộn > 0; "Tổng phút" = tổng phút muộn đúng khoảng {period}. '
         '"—" = chưa đủ dữ liệu, không tính là 0.'),
        (f'• Vắng: {absence_note} Không tính Chủ nhật, ngày chưa đến, ngày trước khi vào làm hoặc sau khi nghỉ việc, '
         'ngày nghỉ đã duyệt; chỉ có một giờ vào hoặc một giờ ra không tính là vắng.'),
    ]


def build_attendance_book(report):
    """``report`` → .xlsx bytes. Keys: company, title, period, scope, stamp, days [date], groups [{name, people}],
    legend [str], detail ({title, rows} or None). A person: code, name, job, cells {date: cell}, late {count,
    minutes} (``None`` = unknown), absent (int), note."""
    book = Workbook()
    sheet = book.active
    sheet.title = 'Bảng chấm công'
    totals = _matrix(sheet, report)
    if report.get('detail') is not None:
        _detail(book.create_sheet('Chi tiết'), report)
    book.properties.title = report['title']
    book.properties.creator = 'TANPHAT ONE'
    stream = BytesIO()
    book.save(stream)
    return stream.getvalue(), totals
