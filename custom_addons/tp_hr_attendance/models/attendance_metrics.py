"""Dashboard arithmetic over the same board cells; no ORM, private text or payroll policy."""
import csv
import io
from collections import Counter

STATES = ('ok', 'missing', 'review', 'no_punch', 'no_source')


def metrics(rows, dates, today):
    counts = dict.fromkeys(STATES, 0)
    daily = {item['date']: dict.fromkeys(STATES, 0) for item in dates if item['date'] <= today}
    cells = []
    hours, units, confirmed, unconfirmed = 0.0, 0.0, 0, 0
    departments = {}
    for person in rows:
        for cell in person['cells']:
            if cell['date'] > today:
                continue
            state = cell['state']
            if state not in counts:
                continue
            counts[state] += 1
            daily[cell['date']][state] += 1
            hours += cell.get('hours') or 0
            if cell.get('units_state') == 'confirmed':
                units += cell.get('units_value') or 0
                confirmed += 1
            elif cell.get('day_id'):
                unconfirmed += 1
            dept = person.get('department') or 'Chưa khai báo phòng'
            departments.setdefault(dept, Counter())[state] += 1
            cells.append(dict(cell, employee_name=person['name'], employee_code=person['code'], department=dept, employee_id=person['id']))
    cells.sort(key=lambda row: (row['date'], row['employee_code']), reverse=True)
    return {'counts': counts, 'total': sum(counts.values()), 'employees': len(rows), 'hours': round(hours, 2),
            'units': round(units, 2) if confirmed else None, 'confirmed': confirmed, 'unconfirmed': unconfirmed,
            'daily': [{'date': day, 'counts': count} for day, count in daily.items()],
            'departments_chart': [{'name': name, 'counts': dict(count)} for name, count in sorted(departments.items())],
            'cells': cells}


def own_csv(rows, state='', lock=''):
    """Explicit public attendance columns only; never correction notes or evidence."""
    def safe(value):
        value = str(value) if value is not None else ''
        return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')) else value

    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['Ngày', 'Vào', 'Ra', 'Giờ ghi nhận', 'Công xác nhận', 'Tình trạng', 'Kỳ', 'Nguồn'])
    for row in rows:
        if (state and row['state'] != state) or (lock and row['lock'] != lock):
            continue
        writer.writerow([safe(value) for value in (
            row['date'], row.get('in_time', ''), row.get('out_time', ''),
            row.get('hours', '') if row.get('day_id') else '', row.get('units', ''),
            row['label'], 'Đã chốt' if row['lock'] == 'locked' else 'Đang mở',
            ', '.join(dict.fromkeys(session['source_label'] for session in row.get('sessions', []))),
        )])
    return '\ufeff' + output.getvalue()
