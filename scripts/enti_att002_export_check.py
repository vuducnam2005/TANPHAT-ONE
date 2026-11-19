# ENTI-ATTENDANCE-002: open the generated "Bảng chấm công" workbook and reconcile it with the backend figures.
# Run through `odoo-bin shell` (local test DB, or the PC container for real data). READ-ONLY: every export call
# happens inside the shell transaction, which is rolled back at the end (no log row, no data change).
# Periods: TP_EXPORT_CHECK='[{"mode": "week", "date": "2026-11-09"}, ...]' (default: week 09-15/11, 01-19/11, 11/2026).
# Prints one JSON line per period and a final {"ok": true|false}.
# ruff: noqa: T201 - CLI report printed for the caller
import base64
import json
import os
import sys
from datetime import datetime, time
from io import BytesIO

from openpyxl import load_workbook

sys.stdout.reconfigure(encoding="utf-8")
env = env  # noqa: F821,PLW0127 - provided by odoo shell

from odoo.addons.tp_hr_attendance.models.attendance_figures import UNDRAWN  # noqa: E402
from odoo.addons.tp_hr_attendance.models.attendance_logic import (  # noqa: E402
    WEEKDAY_LABELS,
    dates_between,
)

DEFAULT = [{"mode": "week", "date": "2026-11-09"}, {"mode": "range", "from": "2026-11-01", "to": "2026-11-19"},
           {"mode": "month", "date": "2026-11-19"}]
periods = json.loads(os.environ.get("TP_EXPORT_CHECK") or "null") or DEFAULT
Day = env["tp.hr.attendance.day"]
company = env.company
FORMULA = ("=", "+", "-", "@")
all_ok = True


def as_clock(value):
    return value.strftime("%H:%M") if isinstance(value, time) else value


for params in periods:
    problems = []
    file = Day.tp_export_sheet(dict(params))
    book = load_workbook(BytesIO(base64.b64decode(file["data"])))
    mode, _anchor, start, end, today = Day._tp_period(dict(params))
    days = dates_between(start, end)
    if book.sheetnames != ["Bảng chấm công", "Chi tiết"]:
        problems.append(f"sheets {book.sheetnames}")
    ws = book["Bảng chấm công"]
    if "TANPHAT ONE" not in str(ws["A1"].value) or f"{start:%d/%m/%Y}" not in str(ws["A3"].value) \
            or f"{end:%d/%m/%Y}" not in str(ws["A3"].value):
        problems.append("period block")
    if ws.freeze_panes != "F9" or ws.page_setup.orientation != "landscape" or ws.print_title_rows.replace("$", "") != "7:8":
        problems.append(f"freeze/print {ws.freeze_panes} {ws.page_setup.orientation} {ws.print_title_rows}")
    head_days = [ws.cell(7, 6 + i).value for i in range(len(days))]
    if [value.date() if isinstance(value, datetime) else value for value in head_days] != days:
        problems.append("day header is not real dates of the period")
    if [ws.cell(8, 6 + i).value for i in range(len(days))] != [WEEKDAY_LABELS[d.weekday()] for d in days]:
        problems.append("weekday header")
    late_col, absent_col = 6 + len(days), 8 + len(days)

    # backend: same scope, same figures as the screens
    people = Day._tp_people(company, int(params.get("department_id") or 0), (params.get("search") or "").strip(), start, end)
    ids = list(people)
    cells, _ = Day._tp_presence(company, ids, start, end, today)
    views = Day._tp_late_views(company, ids, cells, start, end)
    note = Day._tp_absence_note(company, start, end)
    absences = Day._tp_absences(ids, cells, start, end, note.startswith("Đếm"))

    blocks = [r for r in range(9, ws.max_row + 1) if ws.cell(r, 5).value == "Vào"]
    order = [ws.cell(r, 3).value for r in blocks]
    if order != [people[i]["name"] for i in ids]:
        problems.append("employee order differs from the HR order")
    time_cells = checked = 0
    sums = {"count": 0, "minutes": 0, "absent": 0}
    for r, employee_id in zip(blocks, ids, strict=False):
        view, absence = views[employee_id], absences[employee_id]
        exact = view["state"] == "exact"
        got = (ws.cell(r, late_col).value, ws.cell(r, late_col + 1).value, ws.cell(r, absent_col).value)
        want = (view["count"] if exact else "—", view["minutes"] if exact else "—", absence["days"])
        if got != want:
            problems.append(f"{people[employee_id]['code']}: totals {got} != {want}")
        if exact:
            sums["count"] += view["count"]
            sums["minutes"] += view["minutes"]
        sums["absent"] += absence["days"]
        for i, day in enumerate(days):
            cell = cells[employee_id, day]
            shown = (ws.cell(r, 6 + i).value, ws.cell(r + 1, 6 + i).value)
            for offset, value in enumerate(shown):
                if isinstance(value, time):
                    time_cells += 1
                    if ws.cell(r + offset, 6 + i).number_format != "hh:mm":
                        problems.append(f"time cell without hh:mm format at row {r + offset}")
            checked += 1
            if cell["state"] in ("future", "off", "rest"):
                expect = (None, None)
            elif cell["state"] == "absent":
                expect = ("Vắng", "Vắng")
            elif cell["state"] == "leave":
                expect = ("Nghỉ", "Nghỉ")
            elif cell["state"] in ("no_source", "no_punch"):
                expect = ("—", "—")
            else:
                expect = (cell["in"] or "—", cell["out"] or "—")
            if tuple(as_clock(value) for value in shown) != tuple(expect):
                problems.append(f"{people[employee_id]['code']} {day}: {shown} != {expect}")
    total_row = blocks[-1] + 2 if blocks else 10
    any_exact = any(views[i]["state"] == "exact" for i in ids)
    want_total = (sums["count"] if any_exact else "—", sums["minutes"] if any_exact else "—", sums["absent"])
    if (ws.cell(total_row, late_col).value, ws.cell(total_row, late_col + 1).value,
            ws.cell(total_row, absent_col).value) != want_total:
        problems.append("totals row")
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith(FORMULA):
                problems.append(f"formula-like text {c.coordinate}")

    detail = book["Chi tiết"]
    detail_rows = [row for row in detail.iter_rows(min_row=4, values_only=True) if row[0] is not None]
    expected_rows = sum(1 for i in ids for d in days if d <= today and cells[i, d]["state"] not in UNDRAWN)
    if len(detail_rows) != expected_rows:
        problems.append(f"detail rows {len(detail_rows)} != {expected_rows}")

    # dashboard KPIs over the same scope agree with the file when every late value is known
    overview = Day.tp_overview(dict(params, page_size=10))
    kpi = overview["kpis"]
    if kpi["absent"]["value"] != sums["absent"]:
        problems.append(f"overview absent {kpi['absent']['value']} != file {sums['absent']}")
    if kpi["late"]["state"] == "exact" and kpi["late"]["minutes"] != sums["minutes"]:
        problems.append(f"overview late minutes {kpi['late']['minutes']} != file {sums['minutes']}")

    all_ok = all_ok and not problems
    print(json.dumps({"period": params, "file": file["filename"], "people": len(ids), "day_cells": checked,
                      "time_cells": time_cells, "late_count": sums["count"], "late_minutes": sums["minutes"],
                      "absent": sums["absent"], "detail_rows": len(detail_rows),
                      "late_unknown_people": sum(1 for i in ids if views[i]["state"] != "exact"),
                      "problems": problems[:12]}, ensure_ascii=False, default=str))
env.cr.rollback()
print(json.dumps({"ok": all_ok}))
