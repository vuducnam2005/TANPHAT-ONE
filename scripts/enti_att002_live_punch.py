# ENTI-ATTENDANCE-002 live-update probe, LOCAL TEST DB ONLY (tp_tanphat_test).
# Run through `odoo-bin shell`: simulates ENTI reporting a new "last out" for one employee who is still at work
# today, through the real apply + success path (store, project to the canonical day, bus notification), then
# commits. Prints one JSON line {employee, out, committed_at} for scripts/enti_att002_live.cjs.
# ruff: noqa: T201, E402 - odoo shell script; prints one JSON line
import json
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
assert env.cr.dbname == "tp_tanphat_test", env.cr.dbname  # noqa: F821 - provided by odoo shell

import pytz

from odoo import fields

env = env  # noqa: F821,PLW0127
source = env["tp.hr.attendance.source"].sudo().search([("namespace", "=", "enti-local-test")], limit=1)
assert source, "seed the local ENTI test source first"
day_date = datetime.now(pytz.timezone(source.timezone or "Asia/Ho_Chi_Minh")).date()
open_day = env["tp.hr.attendance.day"].sudo().search([
    ("work_date", "=", day_date), ("in_time", "!=", False), ("in_time", "!=", ""),
    "|", ("out_time", "=", False), ("out_time", "=", ""),
], order="id", limit=1)
assert open_day, "no employee is still at work today in the test data"
mapping = env["tp.hr.attendance.enti.mapping"].sudo().search([
    ("source_id", "=", source.id), ("employee_id", "=", open_day.employee_id.id), ("state", "=", "mapped"),
], limit=1)
assert mapping, "employee has no confirmed ENTI mapping"

hour, minute = (int(part) for part in open_day.in_time.split(":"))
late = max(0, hour * 60 + minute - (8 * 60 + 30))
# Strictly newer than every out time already recorded today, so the probe's punch is the newest mark.
latest = max((d.out_time for d in env["tp.hr.attendance.day"].sudo().search([("work_date", "=", day_date)]) if d.out_time),
             default="17:00")
minutes = min(23 * 60 + 59, int(latest[:2]) * 60 + int(latest[3:5]) + 1)
out = f"{minutes // 60:02d}:{minutes % 60:02d}"
weekday = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"][day_date.weekday()]
row = {
    "keyNV": mapping.key_nv, "tenNV": mapping.ten_nv or open_day.employee_id.name, "maNV": mapping.ma_nv or "",
    "day1": {"ngay": day_date.isoformat(), "dayOfWeek": day_date.weekday(), "thuTrongTuan": weekday, "caLV": "HC",
             "vaoDau": open_day.in_time, "raCuoi": out, "diMuon": late, "veSom": 0},
}


class FakeEnti:
    def get_employees(self):
        return []

    def get_attendance(self, start, end):
        return {"data": [row], "pages": 1}


stats = source._tp_enti_apply(FakeEnti(), day_date, day_date, with_directory=False)
source._tp_enti_succeeded(stats, day_date, day_date, "today", "cron", time.monotonic(), fields.Datetime.now())
env.cr.commit()
print(json.dumps({"employee": open_day.employee_id.name, "out": out, "applied": stats["applied"],
                  "committed_at": datetime.now().timestamp()}, ensure_ascii=False))
