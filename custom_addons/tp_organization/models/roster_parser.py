"""Roster reader: only the first five source columns; never attendance cells."""
from collections import Counter
from decimal import Decimal, InvalidOperation
from io import BytesIO

from openpyxl import load_workbook


def source_code(value):
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        msg = 'Source code must be a positive integer.'
        raise ValueError(msg) from None
    if not number.is_finite() or number <= 0 or number != number.to_integral_value():
        msg = 'Source code must be a positive integer.'
        raise ValueError(msg)
    return str(int(number))


def employee_code(value):
    return f'TP{10000 + int(source_code(value))}'


def parse_roster(data):
    try:
        book = load_workbook(BytesIO(data), read_only=True, data_only=True)
    except Exception as exc:
        msg = 'Cannot read XLSX workbook.'
        raise ValueError(msg) from exc
    people, errors, count, locations = {}, [], 0, {}
    try:
        for sheet in book:
            rows = sheet.iter_rows(min_col=1, max_col=5, values_only=True)
            header, department = False, ''
            for row_number, row in enumerate(rows, 1):
                cells = [str(v).strip() if v is not None else '' for v in row]
                if cells[1] == 'Mã nhân viên' and cells[2] == 'Tên nhân viên':
                    header = True
                    continue
                if not header:
                    continue
                # Group rows have a title in A or B, but no employee name/ID.
                if not cells[0].isdigit() and not cells[2] and not cells[3] and (cells[0] or cells[1]):
                    title = cells[1] or cells[0]
                    if title.casefold() not in ('tổng', 'tổng cộng', 'stt'):
                        department = title
                    continue
                if not cells[1] or not cells[2]:
                    if cells[0].isdigit():
                        error = {'sheet': sheet.title, 'row': row_number, 'error': 'Missing source code or employee name'}
                        try:
                            error['source_code'] = source_code(row[1])
                        except ValueError:
                            pass
                        errors.append(error)
                        count += 1
                    continue
                try:
                    code = source_code(row[1])
                except ValueError:
                    # Ignore time/summary headings; numeric employee rows are validated below.
                    if cells[0].isdigit():
                        count += 1
                        errors.append({'sheet': sheet.title, 'row': row_number, 'error': 'Invalid source code'})
                    continue
                count += 1
                locations.setdefault(code, []).append({"sheet": sheet.title, "row": row_number})
                item = dict(source_code=code, name=cells[2], source_department=department, source_title=cells[4])
                try:
                    if code != source_code(row[3]):
                        msg = 'Columns B and D differ'
                        raise ValueError(msg)  # noqa: TRY301 - collect every invalid source row
                    if not department:
                        msg = 'Missing source department'
                        raise ValueError(msg)  # noqa: TRY301 - collect every invalid source row
                    if code in people and people[code] != item:
                        msg = 'Conflicting duplicate identity'
                        raise ValueError(msg)  # noqa: TRY301 - collect every invalid source row
                    people[code] = item
                except ValueError as exc:
                    errors.append({'sheet': sheet.title, 'row': row_number, 'source_code': code, 'error': str(exc)})
        if not count and not errors:
            msg = 'No employee rows found after roster header.'
            raise ValueError(msg)
        conflicted = {e.get('source_code') for e in errors}
        return {'rows': [p for code, p in people.items() if code not in conflicted], 'errors': errors,
                'locations': locations, 'row_count': count, 'groups': dict(Counter(p['source_department'] for code, p in people.items() if code not in conflicted))}
    finally:
        book.close()
