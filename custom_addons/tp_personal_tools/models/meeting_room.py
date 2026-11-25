# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Meeting Room Directory & Availability Helpers (`tp.meeting.room`) for TANPHAT ONE.

Supports internal company meeting room management and concurrency-safe booking on `calendar.event`:
- Read access for all active internal users (`base.group_user`) in the same company.
- Create/Edit/Archive restricted to system/delegated administrators.
- Row-level PostgreSQL `FOR UPDATE` locking during booking is enforced in `personal_calendar.py`
  so two simultaneous bookings for the same room and overlapping time never both succeed.
"""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from odoo import api, fields, models
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Domain


def _room_user_tz(env):
    tz_name = env.user.tz or env.company.partner_id.tz or "Asia/Ho_Chi_Minh"
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


def _parse_slot_bounds_utc(env, start_iso, stop_iso, allday=False):
    tz = _room_user_tz(env)
    if allday:
        s_raw = str(start_iso or "")[:10]
        e_raw = str(stop_iso or start_iso or "")[:10]
        if not s_raw:
            return None, None
        try:
            d_start = datetime.strptime(s_raw, "%Y-%m-%d").date()
            d_stop = datetime.strptime(e_raw, "%Y-%m-%d").date()
        except ValueError:
            return None, None
        if d_stop < d_start:
            return None, None
        start_utc = (
            datetime.combine(d_start, time.min, tzinfo=tz)
            .astimezone(ZoneInfo("UTC"))
            .replace(tzinfo=None)
        )
        stop_utc = (
            datetime.combine(d_stop + timedelta(days=1), time.min, tzinfo=tz)
            .astimezone(ZoneInfo("UTC"))
            .replace(tzinfo=None)
        )
        return start_utc, stop_utc

    s_raw = str(start_iso or "").strip()
    e_raw = str(stop_iso or "").strip()
    if len(s_raw) < 16 or len(e_raw) < 16:
        return None, None
    try:
        fmt_s = "%Y-%m-%dT%H:%M" if "T" in s_raw else "%Y-%m-%d %H:%M"
        fmt_e = "%Y-%m-%dT%H:%M" if "T" in e_raw else "%Y-%m-%d %H:%M"
        st = datetime.strptime(s_raw[:16], fmt_s).replace(tzinfo=tz)
        en = datetime.strptime(e_raw[:16], fmt_e).replace(tzinfo=tz)
    except ValueError:
        return None, None
    start_utc = st.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    stop_utc = en.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    if stop_utc <= start_utc:
        return None, None
    return start_utc, stop_utc


class TpMeetingRoom(models.Model):
    _name = "tp.meeting.room"
    _description = "Phòng họp nội bộ TANPHAT ONE"
    _order = "sequence asc, name asc, id asc"

    code = fields.Char(
        string="Mã phòng họp",
        required=True,
        index=True,
        export_string_translation=False,
    )
    name = fields.Char(
        string="Tên phòng họp",
        required=True,
        export_string_translation=False,
    )
    sequence = fields.Integer(default=10, export_string_translation=False)
    company_id = fields.Many2one(
        "res.company",
        string="Công ty",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        export_string_translation=False,
    )
    location = fields.Char(
        string="Vị trí / Tầng",
        export_string_translation=False,
    )
    capacity = fields.Integer(
        string="Sức chứa (người)",
        default=10,
        required=True,
        export_string_translation=False,
    )
    equipment_note = fields.Char(
        string="Thiết bị hỗ trợ",
        export_string_translation=False,
    )
    active = fields.Boolean(default=True, export_string_translation=False)

    _code_company_uniq = models.Constraint(
        "UNIQUE(company_id, code)",
        "Mã phòng họp đã tồn tại trong cùng công ty.",
    )

    @api.constrains("capacity")
    def _check_capacity(self):
        for rec in self:
            if rec.capacity < 1:
                raise ValidationError(self.env._("Sức chứa phòng họp phải từ 1 người trở lên."))

    @api.model
    def _tp_can_manage_rooms(self):
        user = self.env.user
        return bool(
            user._is_internal()
            and user.active
            and (
                user.has_group("base.group_system")
                or user.has_group("tp_admin_delegation.group_full_admin")
            )
        )

    def _tp_serialize_room(self, conflict_info=None):
        self.ensure_one()
        return {
            "id": self.id,
            "code": self.code or "",
            "name": self.name or "",
            "location": self.location or "",
            "capacity": self.capacity or 0,
            "equipment_note": self.equipment_note or "",
            "active": bool(self.active),
            "display_label": (
                f"{self.name} ({self.capacity} chỗ"
                + (f" · {self.location}" if self.location else "")
                + ")"
            ),
            "is_available": conflict_info is None,
            "conflict_summary": conflict_info or "",
        }

    @api.model
    def tp_list_available_rooms(
        self, start_iso="", stop_iso="", allday=False, exclude_event_id=0
    ):
        """Return active company meeting rooms with live availability for the requested slot."""
        self.env["res.users"]._tp_require_internal_caller()
        rooms = self.search(
            [("active", "=", True), ("company_id", "in", self.env.companies.ids)],
            order="sequence asc, name asc, id asc",
        )
        if not rooms:
            return []

        start_utc, stop_utc = _parse_slot_bounds_utc(self.env, start_iso, stop_iso, allday=allday)
        conflict_by_room = {}
        if start_utc and stop_utc:
            tz = _room_user_tz(self.env)
            dom = (
                Domain("active", "=", True)
                & Domain("tp_room_id", "in", rooms.ids)
                & Domain("tp_room_booking_state", "=", "confirmed")
                & Domain("start", "<", stop_utc)
                & Domain("stop", ">", start_utc)
            )
            if exclude_event_id:
                dom &= Domain("id", "!=", int(exclude_event_id))
            overlapping = self.env["calendar.event"].sudo().search(dom, order="start asc")
            for ev_su in overlapping:
                rid = ev_su.tp_room_id.id
                if rid in conflict_by_room:
                    continue
                ev_user = ev_su.with_env(self.env)
                is_priv = ev_user._check_private_event_conditions()
                if ev_su.allday:
                    slot_lbl = "Cả ngày"
                else:
                    st_loc = ev_su.start.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                    en_loc = ev_su.stop.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                    slot_lbl = f"{st_loc.strftime('%H:%M')}–{en_loc.strftime('%H:%M')}"
                org_name = ev_su.user_id.name or ""
                title = "Khung giờ bận" if is_priv else (ev_su.name or "Đã đặt phòng")
                who_suffix = f" ({org_name})" if (org_name and not is_priv) else ""
                conflict_by_room[rid] = f"Đã đặt {slot_lbl}: {title}{who_suffix}"

        return [r._tp_serialize_room(conflict_by_room.get(r.id)) for r in rooms]

    @api.model
    def tp_save_meeting_room(self, room_id, vals, operation_token=""):
        """Create or update an internal meeting room (restricted to Admin / Full Admin)."""
        self.env["res.users"]._tp_require_internal_caller()
        if not self._tp_can_manage_rooms():
            raise AccessError(
                self.env._("Chỉ quản trị viên hệ thống mới có quyền thêm hoặc chỉnh sửa danh mục phòng họp.")
            )
        vals = dict(vals or {})
        name = str(vals.get("name") or "").strip()
        code = str(vals.get("code") or "").strip().upper()
        if not name:
            raise ValidationError(self.env._("Vui lòng nhập tên phòng họp."))
        if not code:
            raise ValidationError(self.env._("Vui lòng nhập mã phòng họp (ví dụ: PH-T3-01)."))
        try:
            capacity = int(vals.get("capacity") or 10)
        except (TypeError, ValueError) as exc:
            raise ValidationError(self.env._("Sức chứa phòng họp phải là số nguyên dương.")) from exc
        if capacity < 1:
            raise ValidationError(self.env._("Sức chứa phòng họp phải từ 1 người trở lên."))

        write_vals = {
            "code": code,
            "name": name,
            "capacity": capacity,
            "location": str(vals.get("location") or "").strip() or False,
            "equipment_note": str(vals.get("equipment_note") or "").strip() or False,
        }
        if "active" in vals:
            write_vals["active"] = bool(vals.get("active"))

        if room_id:
            room = self.with_context(active_test=False).browse(int(room_id)).exists()
            if not room:
                raise MissingError(self.env._("Phòng họp không tồn tại."))
            room.write(write_vals)
            return room._tp_serialize_room()

        op_log = self.env["tp.personal.operation.log"]
        existing, clean_token, fp = op_log.acquire_or_replay(
            "create_meeting_room",
            operation_token,
            {"code": code, "name": name, "company_id": self.env.company.id},
        )
        if existing:
            return existing._tp_serialize_room()

        write_vals["company_id"] = self.env.company.id
        room = self.sudo().create(write_vals).with_env(self.env)
        op_log.record_success("create_meeting_room", clean_token, fp, room)
        return room._tp_serialize_room()
