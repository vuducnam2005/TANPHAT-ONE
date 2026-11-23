# Reconcile the generated "Report" workbook with the backend figures.
# Run through `odoo-bin shell` (local test DB, or the PC container for real data). READ-ONLY: every export call
# happens inside the shell transaction, which is rolled back at the end (no log row, no data change).
# Periods: TP_EXPORT_CHECK='[{"mode": "week", "date": "2026-11-16"}, ...]'
# Prints one JSON line per period and a final {"ok": true|false}.
# ruff: noqa: T201 - CLI report printed for the caller
import base64
import json
import os
import sys
from io import BytesIO

from openpyxl import load_workbook

sys.stdout.reconfigure(encoding="utf-8")
env = env  # noqa: F821,PLW0127 - provided by odoo shell

from odoo.addons.tp_hr_attendance.models.attendance_export import (  # noqa: E402
    export_late_totals,
    format_clock,
    worked_days_count,
)
from odoo.addons.tp_hr_attendance.models.attendance_figures import (  # noqa: E402
    parse_hours,
)
from odoo.addons.tp_hr_attendance.models.attendance_logic import (  # noqa: E402
    WEEKDAY_LABELS,
    dates_between,
)

DEFAULT = [
    {"mode": "week", "date": "2026-11-16"},
    {"mode": "range", "from": "2026-11-09", "to": "2026-11-22"},
    {"mode": "month", "date": "2026-11-16"},
]
periods = json.loads(os.environ.get("TP_EXPORT_CHECK") or "null") or DEFAULT
Day = env["tp.hr.attendance.day"]
company = env.company
FORMULA = ("=", "+", "-", "@")
all_ok = True
start_hour = parse_hours(Day._tp_reference_hours())[0]

for params in periods:
    problems = []
    file = Day.tp_export_sheet(dict(params))
    book = load_workbook(BytesIO(base64.b64decode(file["data"])))
    mode, _anchor, start, end, today = Day._tp_period(dict(params))
    days = dates_between(start, end)
    if book.sheetnames != ["Report"]:
        problems.append(f"sheets {book.sheetnames}")
    ws = book["Report"]
    if ws["A2"].value != "BẢNG CÔNG THÁNG" or ws["A3"].value != f"Từ ngày {start:%d/%m/%Y} - Đến ngày {end:%d/%m/%Y}":
        problems.append(f"title/period mismatch: {ws['A2'].value!r} / {ws['A3'].value!r}")
    if ws.freeze_panes != "G7" or ws.page_setup.orientation != "landscape" or ws.print_title_rows.replace("$", "") != "5:6":
        problems.append(f"freeze/print {ws.freeze_panes} {ws.page_setup.orientation} {ws.print_title_rows}")
    if not ws.print_area:
        problems.append("missing print_area")
    if [ws.cell(5, 7 + i).value for i in range(len(days))] != [d.day for d in days]:
        problems.append("day number header mismatch")
    if [ws.cell(6, 7 + i).value for i in range(len(days))] != [WEEKDAY_LABELS[d.weekday()] for d in days]:
        problems.append("weekday header mismatch")
    late_col, days_col = 7 + len(days), 9 + len(days)

    people = Day._tp_people(company, int(params.get("department_id") or 0), (params.get("search") or "").strip(), start, end)
    ids = list(people)
    cells, _ = Day._tp_presence(company, ids, start, end, today)
    views = Day._tp_late_views(company, ids, cells, start, end)

    blocks = [r for r in range(7, ws.max_row + 1) if ws.cell(r, 6).value == "Vào"]
    order = [ws.cell(r, 3).value for r in blocks]
    if order != [people[i]["name"] for i in ids]:
        problems.append("employee order differs from HR order")

    time_cells = checked = 0
    sums = {"count": 0, "minutes": 0, "worked_days": 0}
    for r, employee_id in zip(blocks, ids, strict=False):
        emp_cells = {d: cells[employee_id, d] for d in days}
        want_late = export_late_totals(emp_cells, views[employee_id], start_hour=start_hour, today=today)
        want_days = worked_days_count(emp_cells)
        got = (ws.cell(r, late_col).value, ws.cell(r, late_col + 1).value, ws.cell(r, days_col).value)
        want = (want_late[0], want_late[1], want_days)
        if got != want:
            problems.append(f"{people[employee_id]['code']}: totals {got} != {want}")
        sums["count"] += want_late[0]
        sums["minutes"] += want_late[1]
        sums["worked_days"] += want_days
        for i, day in enumerate(days):
            cell = cells[employee_id, day]
            shown = (ws.cell(r, 7 + i).value, ws.cell(r + 1, 7 + i).value)
            for value in shown:
                if value is not None:
                    time_cells += 1
                    if not (isinstance(value, str) and len(value) == 5 and value[2] == ":"):
                        problems.append(f"bad clock {value!r} at {people[employee_id]['code']} {day}")
            checked += 1
            expect = (format_clock(cell.get("in")) or None, format_clock(cell.get("out")) or None)
            if shown != expect:
                problems.append(f"{people[employee_id]['code']} {day}: {shown} != {expect}")

    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and (c.value.startswith(FORMULA) or "NaN" in c.value or "undefined" in c.value):
                problems.append(f"unsafe text {c.coordinate}: {c.value!r}")

    all_ok = all_ok and not problems
    print(json.dumps({
        "period": params,
        "file": file["filename"],
        "people": len(ids),
        "day_cells": checked,
        "time_cells": time_cells,
        "late_count": sums["count"],
        "late_minutes": sums["minutes"],
        "worked_days": sums["worked_days"],
        "problems": problems[:12],
    }, ensure_ascii=False, default=str))
env.cr.rollback()
print(json.dumps({"ok": all_ok}))
