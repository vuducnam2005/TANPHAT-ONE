"""Raw daily aggregated attendance data from ENTI and canonical projection (ENTI-LIVE-001).

Records each employee-day returned by ENTI, preserving raw values, and projects
mapped records into the canonical day summary and sessions per business rules:
1) Approved corrections win over ENTI.
2) ENTI wins over Excel.
3) Incomplete days (in-only, out-only) update day status without creating invalid sessions.
"""
import json
import logging
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from odoo import api, fields, models
from odoo.exceptions import AccessError

from .attendance_common import DEFAULT_TZ

_logger = logging.getLogger(__name__)

ENTI_DAY_STATES = [
    ("applied", "Đã áp dụng vào bảng công"),
    ("pending_map", "Chờ đối chiếu nhân viên"),
    ("superseded_correction", "Giữ điều chỉnh đã duyệt"),
    ("locked_period", "Kỳ đã chốt"),
    ("ignored", "Bỏ qua"),
]


def _parse_time_str(time_val, work_date, tz_name=DEFAULT_TZ):
    """Parse time string like '08:15', '08:15:30', or ISO '2026-11-16T08:15:00' to (HH:MM string, UTC datetime)."""
    if not time_val:
        return "", False
    time_str = str(time_val).strip()
    if not time_str or time_str in ("null", "None", "-"):
        return "", False

    zone = ZoneInfo(tz_name or DEFAULT_TZ)

    # If full datetime string
    if "T" in time_str or " " in time_str:
        clean = time_str.replace("T", " ").split(".")[0]
        try:
            dt = datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
            dt = dt.replace(tzinfo=zone)
            utc_dt = dt.astimezone(UTC).replace(tzinfo=None)
            clock_str = dt.strftime("%H:%M")
            return clock_str, utc_dt
        except ValueError:
            pass

    # If HH:MM or HH:MM:SS
    parts = time_str.split(":")
    if len(parts) >= 2:
        try:
            hour = int(parts[0])
            minute = int(parts[1])
            second = int(parts[2]) if len(parts) > 2 else 0
            clock_str = f"{hour:02d}:{minute:02d}"
            local_dt = datetime.combine(work_date, datetime.min.time()).replace(
                hour=hour, minute=minute, second=second, tzinfo=zone
            )
            utc_dt = local_dt.astimezone(UTC).replace(tzinfo=None)
            return clock_str, utc_dt
        except (ValueError, TypeError):
            pass

    return time_str[:5], False


class AttendanceEntiDay(models.Model):
    _name = "tp.hr.attendance.enti.day"
    _description = "Dữ liệu chấm công theo ngày ENTI"
    _order = "work_date desc, id desc"
    _check_company_auto = True

    source_id = fields.Many2one(
        "tp.hr.attendance.source",
        "Nguồn dữ liệu",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="source_id.company_id",
        store=True,
        string="Công ty",
        index=True,
    )
    key_nv = fields.Char("Khóa nhân viên ENTI", required=True, index=True)
    work_date = fields.Date("Ngày công", required=True, index=True)
    employee_id = fields.Many2one(
        "hr.employee",
        "Nhân viên Odoo",
        check_company=True,
        index=True,
        ondelete="set null",
    )

    ca_lv = fields.Char("Ca làm việc")
    vao_dau = fields.Char("Giờ vào")
    ra_cuoi = fields.Char("Giờ ra")
    check_in_dt = fields.Datetime("Thời điểm vào (UTC)")
    check_out_dt = fields.Datetime("Thời điểm ra (UTC)")

    day_of_week = fields.Integer("Thứ số")
    thu_trong_tuan = fields.Char("Ký hiệu thứ")
    di_muon = fields.Integer("Đi muộn (phút)")
    ve_som = fields.Integer("Về sớm (phút)")
    lam_chinh = fields.Float("Làm chính (phút)")
    lam_them = fields.Float("Làm thêm (phút)")
    cong_lam = fields.Float("Công làm ENTI ghi nhận")
    ky_hieu = fields.Char("Ký hiệu")

    state = fields.Selection(
        ENTI_DAY_STATES,
        "Trạng thái áp dụng",
        default="pending_map",
        required=True,
        index=True,
    )
    raw_json = fields.Text("Dữ liệu thô JSON")
    received_at = fields.Datetime("Thời điểm nhận", default=fields.Datetime.now)

    _day_unique = models.Constraint(
        "UNIQUE(source_id, key_nv, work_date)",
        "Bản ghi ngày công ENTI đã tồn tại cho nhân viên và ngày này.",
    )

    @api.model
    def _tp_project_for_mapping(self, mapping):
        """Retroactively project all stored days for this employee after mapping confirmation."""
        days = self.search([
            ("source_id", "=", mapping.source_id.id),
            ("key_nv", "=", mapping.key_nv),
        ])
        for day in days:
            day.sudo().write({"employee_id": mapping.employee_id.id})
            day._tp_project_to_canonical()

    def _tp_project_to_canonical(self):
        """Project this ENTI day record into canonical tp.hr.attendance.day and session.

        Enforces rules:
        1. Approved correction exists -> Do NOT overwrite. Keep correction!
        2. Date is in a locked period -> Do NOT overwrite. Record locked!
        3. Valid employee -> Update canonical tp.hr.attendance.day.
           If both in and out valid -> create/update active session, data_state = 'ok'.
           If only in or only out -> data_state = 'missing', NO invalid session created.
        4. Disable any old Excel sessions for this employee & day (no double counting).
        """
        self.ensure_one()
        if not self.employee_id:
            self.state = "pending_map"
            return

        company = self.company_id
        employee = self.employee_id
        work_date = self.work_date

        # Check rule 1: Approved correction protection
        Correction = self.env["tp.hr.attendance.correction"].sudo()
        approved_corr = Correction.search([
            ("company_id", "=", company.id),
            ("employee_id", "=", employee.id),
            ("work_date", "=", work_date),
            ("state", "=", "approved"),
        ], limit=1)

        if approved_corr:
            self.write({"state": "superseded_correction"})
            _logger.info(
                "ENTI sync preserved approved correction for %s on %s",
                employee.name,
                work_date,
            )
            return

        # Check rule 2: Locked period protection
        Period = self.env["tp.hr.attendance.period"].sudo()
        locked_ranges = Period._tp_locked_ranges([company.id])
        if Period._tp_is_locked(company.id, work_date, locked_ranges):
            self.write({"state": "locked_period"})
            _logger.info(
                "ENTI sync preserved locked period for %s on %s",
                employee.name,
                work_date,
            )
            return

        Day = self.env["tp.hr.attendance.day"].sudo()
        Session = self.env["tp.hr.attendance.session"].sudo()
        now = fields.Datetime.now()

        # Find or create Day summary
        day = Day.search([
            ("employee_id", "=", employee.id),
            ("work_date", "=", work_date),
        ], limit=1)

        has_in = bool(self.check_in_dt and self.vao_dau)
        has_out = bool(self.check_out_dt and self.ra_cuoi)
        full_pair = has_in and has_out and (self.check_out_dt > self.check_in_dt)

        # Deactivate any existing Excel sessions for this employee & day so they never conflict
        old_sessions = Session.search([
            ("employee_id", "=", employee.id),
            ("work_date", "=", work_date),
            ("source", "!=", "correction"),
        ])

        recorded_hours = 0.0
        active_session = False

        if full_pair:
            delta = self.check_out_dt - self.check_in_dt
            recorded_hours = round(delta.total_seconds() / 3600, 2)
            # Find existing ENTI session or create new
            enti_session = old_sessions.filtered(lambda s: s.source == "enti")[:1]
            if enti_session:
                enti_session.write({
                    "check_in": self.check_in_dt,
                    "check_out": self.check_out_dt,
                    "worked_hours": recorded_hours,
                    "active": True,
                })
                active_session = enti_session
            else:
                active_session = Session.create({
                    "employee_id": employee.id,
                    "company_id": company.id,
                    "work_date": work_date,
                    "check_in": self.check_in_dt,
                    "check_out": self.check_out_dt,
                    "worked_hours": recorded_hours,
                    "source": "enti",
                    "active": True,
                })
            # Inactivate any non-ENTI sessions
            (old_sessions - active_session).write({
                "active": False,
                "superseded_reason": "Thay thế bằng dữ liệu chấm công ENTI",
            })
            data_state = "ok"
        else:
            # Half-punch or no punches: DO NOT create a dummy session
            old_sessions.write({
                "active": False,
                "superseded_reason": "Thay thế bằng dữ liệu chấm công ENTI (thiếu giờ)",
            })
            data_state = "missing"

        # Calculate standard units based on rules
        rule = Day._tp_rule_for(company, work_date, employee.department_id)
        units_state, scheduled, units = "unconfirmed", 0.0, False
        if rule and active_session:
            units_state, scheduled, units = Day._tp_units(rule, work_date, active_session)
        elif not full_pair:
            units_state = "pending"
            units = 0.0

        day_vals = {
            "employee_id": employee.id,
            "company_id": company.id,
            "work_date": work_date,
            "employee_code": employee.tp_employee_code or "",
            "employee_name": employee.name,
            "department_id": employee.department_id.id,
            "first_in": self.check_in_dt if has_in else False,
            "last_out": self.check_out_dt if has_out else False,
            "in_time": self.vao_dau or "",
            "out_time": self.ra_cuoi or "",
            "session_count": 1 if full_pair else 0,
            "recorded_hours": recorded_hours,
            "scheduled_hours": scheduled,
            "units": units or 0.0,
            "units_state": units_state,
            "rule_id": rule.id if rule else False,
            "data_state": data_state,
            "source_kind": "enti",
            "source_updated_at": now,
        }

        if day:
            day.write(dict(day_vals, version=day.version + 1))
        else:
            day = Day.create(dict(day_vals, version=1))

        if active_session:
            active_session.write({"day_id": day.id})

        self.write({"state": "applied"})
