"""Raw daily aggregated attendance data from ENTI and canonical projection (ENTI-LIVE-001).

Records each employee-day returned by ENTI, preserving raw values, and projects
mapped records into the canonical day summary and sessions per business rules:
1) Approved corrections win over ENTI.
2) ENTI wins over Excel.
3) Incomplete days (in-only, out-only) update day status without creating invalid sessions.
ENTI-ATTENDANCE-002: a record is rewritten only when ENTI values changed (``raw_hash``) and the canonical day
is written only when its values differ, so an unchanged poll never bumps versions or wakes browsers.
"""
import logging
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from odoo import api, fields, models

from .attendance_common import DEFAULT_TZ, deny_direct, internal, is_internal

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
                hour=hour, minute=minute, second=second, tzinfo=zone,
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
    raw_json = fields.Text("Dữ liệu thô JSON", groups="base.group_no_one")
    received_at = fields.Datetime("Thời điểm nhận", default=fields.Datetime.now)
    raw_hash = fields.Char("Dấu dữ liệu ENTI", readonly=True,
                           help="Dấu của các giá trị ENTI đã lưu; lượt đồng bộ chỉ ghi lại khi dấu thay đổi.")
    changed_at = fields.Datetime("Thay đổi lần cuối", readonly=True, index=True,
                                 help="Lúc Odoo phát hiện giá trị ENTI của ngày này thay đổi.")

    _day_unique = models.Constraint(
        "UNIQUE(source_id, key_nv, work_date)",
        "Bản ghi ngày công ENTI đã tồn tại cho nhân viên và ngày này.",
    )

    def _check_direct_guard(self):
        if not self.env.su and not is_internal(self):
            deny_direct(self)

    @api.model_create_multi
    def create(self, vals_list):
        self._check_direct_guard()
        return super().create(vals_list)

    def write(self, vals):
        self._check_direct_guard()
        return super().write(vals)

    def unlink(self):
        self._check_direct_guard()
        return super().unlink()

    @api.model
    def _tp_project_for_mapping(self, mapping):
        """Retroactively project all stored days for this employee after mapping confirmation."""
        days = self.sudo().search([
            ("source_id", "=", mapping.source_id.id),
            ("key_nv", "=", mapping.key_nv),
        ])
        changed = self.browse()
        for day in days:
            if day.employee_id != mapping.employee_id:
                internal(day).write({"employee_id": mapping.employee_id.id})
            if day._tp_project_to_canonical():
                changed |= day
        return changed

    def _tp_project_to_canonical(self):
        """Project this ENTI day record into canonical tp.hr.attendance.day and session.

        Enforces rules:
        1. Approved correction exists -> Do NOT overwrite. Keep correction!
        2. Date is in a locked period -> Do NOT overwrite. Record locked!
        3. Valid employee -> Update canonical tp.hr.attendance.day.
           If both in and out valid -> create/update active session, data_state = 'ok'.
           If only in or only out -> data_state = 'missing', NO invalid session created.
        4. Disable any old Excel sessions for this employee & day (no double counting).

        Returns True when the canonical day or its session actually changed.
        """
        self.ensure_one()
        if not self.employee_id:
            self._tp_set_state("pending_map")
            return False

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
            self._tp_set_state("superseded_correction")
            return False

        # Check rule 2: Locked period protection
        Period = self.env["tp.hr.attendance.period"].sudo()
        locked_ranges = Period._tp_locked_ranges([company.id])
        if Period._tp_is_locked(company.id, work_date, locked_ranges):
            self._tp_set_state("locked_period")
            return False

        Day = internal(self.env["tp.hr.attendance.day"].sudo())
        Session = internal(self.env["tp.hr.attendance.session"].sudo())
        changed = False

        day = Day.search([
            ("employee_id", "=", employee.id),
            ("work_date", "=", work_date),
        ], limit=1)

        has_in = bool(self.check_in_dt and self.vao_dau)
        has_out = bool(self.check_out_dt and self.ra_cuoi)
        full_pair = has_in and has_out and (self.check_out_dt > self.check_in_dt)

        # Active non-correction sessions of the day (Excel or ENTI); they never stay active beside ENTI.
        old_sessions = Session.search([
            ("employee_id", "=", employee.id),
            ("work_date", "=", work_date),
            ("source", "!=", "correction"),
        ])

        recorded_hours = 0.0
        active_session = Session.browse()

        if full_pair:
            delta = self.check_out_dt - self.check_in_dt
            recorded_hours = round(delta.total_seconds() / 3600, 2)
            # Reuse the day's ENTI session, even one parked inactive while the day was half-punched.
            enti_session = Session.with_context(active_test=False).search([
                ("employee_id", "=", employee.id),
                ("work_date", "=", work_date),
                ("source", "=", "enti"),
            ], order="active desc, id", limit=1)
            session_vals = {"check_in": self.check_in_dt, "check_out": self.check_out_dt, "active": True}
            if enti_session:
                diff = _diff(enti_session, session_vals)
                if diff:
                    internal(enti_session).write(diff)
                    changed = True
                active_session = enti_session
            else:
                active_session = Session.create(dict(
                    session_vals, employee_id=employee.id, company_id=company.id, work_date=work_date, source="enti",
                ))
                changed = True
            stale = old_sessions - active_session
            if stale:
                internal(stale).write({
                    "active": False,
                    "superseded_reason": "Thay thế bằng dữ liệu chấm công ENTI",
                })
                changed = True
            data_state = "ok"
        else:
            # Half-punch or no punches: DO NOT create a dummy session
            if old_sessions:
                internal(old_sessions).write({
                    "active": False,
                    "superseded_reason": "Thay thế bằng dữ liệu chấm công ENTI (thiếu giờ)",
                })
                changed = True
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
        }

        if day:
            diff = _diff(day, day_vals)
            if diff:
                internal(day).write(dict(diff, version=day.version + 1, source_updated_at=fields.Datetime.now()))
                changed = True
        else:
            day = Day.create(dict(day_vals, version=1, source_updated_at=fields.Datetime.now()))
            changed = True

        if active_session and active_session.day_id != day:
            internal(active_session).write({"day_id": day.id})

        self._tp_set_state("applied")
        return changed

    def _tp_set_state(self, state):
        if self.state != state:
            internal(self).write({"state": state})


def _plain(record, name):
    value = record[name]
    if isinstance(value, models.BaseModel):
        return value.id or False
    return value or False


def _diff(record, vals):
    """Values of ``vals`` that differ from ``record`` (empty values compare equal: "", 0, False, None)."""
    out = {}
    for name, value in vals.items():
        current = _plain(record, name)
        new = value or False
        if isinstance(current, float) or isinstance(new, float):
            if abs(float(current or 0) - float(new or 0)) > 1e-6:
                out[name] = value
        elif current != new:
            out[name] = value
    return out
