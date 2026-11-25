# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Backend for Lịch làm việc (Work Calendar) in TANPHAT ONE.

Reuses native `calendar.event`, `calendar.attendee`, `calendar.recurrence`,
`calendar.calendar`, `calendar.user`, and `calendar.alarm`.

Key guarantees enforced at ORM/backend level:
1. View-only / invited attendees do NOT automatically gain permission to edit,
   drag/resize, or delete the organizer's event (`_tp_can_modify_event`, `write`, `unlink`).
2. Invited attendees retain full permission to respond (`accepted`/`declined`/`tentative`)
   for their own invitation only.
3. Private events of other users never leak title, description, notes, location,
   videocall link, or participant list through `_fetch_query`, `_search` side-channels,
   conflict checks, or Agenda/Popover RPCs — showing strictly `'Bận'` for busy slots.
"""

import html
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Domain
from odoo.tools import html2plaintext, html_sanitize

PRIVATE_SEARCH_SENSITIVE_ROOTS = frozenset(
    {
        "name",
        "description",
        "notes",
        "location",
        "videocall_location",
        "categ_ids",
        "res_model",
        "res_id",
    }
)

ATTENDEE_STATE_LABELS = {
    "accepted": "Đã chấp nhận",
    "declined": "Đã từ chối",
    "tentative": "Chưa chắc chắn",
    "needsAction": "Chờ phản hồi",
}

PRIVACY_LABELS = {
    "public": "Công khai nội bộ",
    "confidential": "Chỉ nội bộ công ty",
    "members_only": "Chỉ thành viên lịch",
    "private": "Riêng tư (chỉ hiện Bận)",
}


def _user_tz(env):
    tz_name = env.user.tz or env.company.partner_id.tz or "Asia/Ho_Chi_Minh"
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


def _parse_local_iso_to_utc(env, iso_str):
    raw = str(iso_str or "").strip()
    if not raw:
        return False
    tz = _user_tz(env)
    try:
        if "T" in raw:
            dt_local = datetime.strptime(raw[:16], "%Y-%m-%dT%H:%M").replace(tzinfo=tz)
        else:
            dt_local = datetime.strptime(raw[:16], "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    except ValueError as exc:
        raise ValidationError(env._("Định dạng ngày giờ sự kiện chưa hợp lệ.")) from exc
    return dt_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)


class PersonalCalendarAttendee(models.Model):
    _inherit = "calendar.attendee"

    def _tp_assert_attendee_mutation(self):
        if self.env.su:
            return
        my_partner = self.env.user.partner_id
        for att in self:
            if att.partner_id == my_partner:
                continue
            if att.event_id and att.event_id._tp_can_modify_event():
                continue
            raise AccessError(
                self.env._(
                    "Bạn chỉ được phản hồi trạng thái tham gia của chính mình hoặc khi là người chủ trì cuộc họp."
                )
            )

    def write(self, vals):
        self._tp_assert_attendee_mutation()
        return super().write(vals)

    def unlink(self):
        self._tp_assert_attendee_mutation()
        return super().unlink()


class PersonalCalendarEvent(models.Model):
    _inherit = "calendar.event"

    def _tp_is_admin_actor(self):
        return bool(
            self.env.user.has_group("base.group_system")
            or self.env.user.has_group("tp_admin_delegation.group_full_admin")
        )

    def _tp_can_modify_event(self):
        """Return True ONLY for organizer, creator (without organizer), calendar owner/writer, or admin on non-private events.

        Being an invited attendee (`partner_ids`) does NOT grant event edit/drag/delete rights.
        """
        self.ensure_one()
        if self.env.su:
            return True
        user = self.env.user
        if not user.active or not user._is_internal():
            return False
        if self.user_id and self.user_id == user:
            return True
        if not self.user_id and self.create_uid == user:
            return True
        if self.calendar_id:
            if self.calendar_id.owner_id == user:
                return True
            if (
                self.calendar_id.id in user.writable_calendar_ids.ids
                and self.effective_privacy != "private"
            ):
                return True
        if self._tp_is_admin_actor() and self.effective_privacy != "private":
            return True
        return False

    @api.depends("partner_ids", "calendar_id", "user_id", "privacy")
    @api.depends_context("uid")
    def _compute_user_can_edit(self):
        for event in self:
            if not event.id:
                event.user_can_edit = True
            else:
                event.user_can_edit = event._tp_can_modify_event()

    @api.depends("privacy", "user_id")
    @api.depends_context("uid")
    def _compute_display_name(self):
        hidden = self.filtered(lambda ev: ev._check_private_event_conditions())
        hidden.display_name = "Bận"
        super(PersonalCalendarEvent, self - hidden)._compute_display_name()

    def _fetch_query(self, query, fields):
        events = super()._fetch_query(query, fields)
        if self.env.su:
            return events
        others_private = events.filtered(lambda ev: ev._check_private_event_conditions())
        if others_private and self._fields["name"] in fields:
            replacement = self._fields["name"].convert_to_cache("Bận", others_private)
            self._fields["name"]._update_cache(others_private, replacement)
        return events

    def read(self, fields=None, load="_classic_read"):
        rows = super().read(fields=fields, load=load)
        if self.env.su or not rows:
            return rows
        public_fnames = set(self._get_public_fields()) | {"id"}
        by_id = {ev.id: ev for ev in self}
        for row in rows:
            ev = by_id.get(row.get("id"))
            if ev and ev._check_private_event_conditions():
                for fname in list(row.keys()):
                    if fname in ("name", "display_name"):
                        row[fname] = "Bận"
                    elif fname not in public_fnames:
                        fld = self._fields.get(fname)
                        row[fname] = [] if (fld and fld.type in ("many2many", "one2many")) else False
        return rows

    def _tp_private_visible_domain_for_caller(self):
        """Domain matching events whose full details (not just 'Bận') are visible to current user."""
        uid = self.env.uid
        pid = self.env.user.partner_id.id
        return (
            Domain("effective_privacy", "in", ["public", "confidential"])
            | Domain("user_id", "=", uid)
            | Domain("create_uid", "=", uid)
            | Domain("partner_ids", "in", [pid])
            | Domain(
                "calendar_id.calendar_user_ids",
                "any",
                [("user_id", "=", uid), ("access_role", "=", "owner")],
            )
            | (
                Domain("effective_privacy", "=", "members_only")
                & Domain(
                    "calendar_id.calendar_user_ids",
                    "any",
                    [("user_id", "=", uid), ("access_role", "in", ["owner", "writer"])],
                )
            )
        )

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, *, active_test=True, bypass_access=False):
        """Prevent search side-channel leaks on private events when querying text/private fields."""
        dom = Domain(domain)
        if not self.env.su and not bypass_access and not dom.is_true() and not dom.is_false():
            touches_sensitive = False
            for cond in dom.iter_conditions():
                root_field = (cond.field_expr or "").split(".", 1)[0]
                if root_field in PRIVATE_SEARCH_SENSITIVE_ROOTS:
                    touches_sensitive = True
                    break
            if touches_sensitive:
                dom = dom & self._tp_private_visible_domain_for_caller()
        return super()._search(
            dom,
            offset=offset,
            limit=limit,
            order=order,
            active_test=active_test,
            bypass_access=bypass_access,
        )

    def write(self, vals):
        if not self.env.su and vals:
            # Allow internal videocall channel attachment only if permitted; block non-editors on business fields
            for event in self:
                if not event._tp_can_modify_event():
                    raise AccessError(
                        self.env._(
                            "Bạn không có quyền sửa lịch của người chủ trì. Bạn vẫn có thể phản hồi lời mời tham gia."
                        )
                    )
        return super().write(vals)

    def unlink(self):
        if not self.env.su:
            for event in self:
                if not event._tp_can_modify_event():
                    raise AccessError(
                        self.env._("Chỉ người chủ trì hoặc chủ sở hữu lịch mới có quyền xóa sự kiện này.")
                    )
        return super().unlink()

    @api.model
    def tp_get_calendar_bootstrap(self):
        """Return user's owned/shared calendars, alarms, tags, and timezone info."""
        self.env["res.users"]._tp_require_internal_caller()
        user = self.env.user
        # Ensure primary calendar exists cleanly via native helper
        primary_cal = user._find_or_create_primary_calendar()

        cal_users = self.env["calendar.user"].search(
            [("user_id", "=", user.id)], order="is_primary desc, id asc"
        )
        my_calendars = []
        shared_calendars = []
        for cu in cal_users:
            cal = cu.calendar_id
            if not cal:
                continue
            item = {
                "calendar_user_id": cu.id,
                "id": cal.id,
                "name": cal.display_name or cal.name or "Lịch làm việc",
                "color": cu.filter_color or 1,
                "checked": bool(cu.is_filter_checked),
                "is_primary": bool(cu.is_primary),
                "access_role": cu.access_role,
                "owner_name": cal.owner_id.name if cal.owner_id else "",
                "can_write": cu.access_role in ("owner", "writer"),
            }
            if cu.access_role == "owner":
                my_calendars.append(item)
            else:
                shared_calendars.append(item)

        alarms = self.env["calendar.alarm"].search([], order="interval asc, duration asc", limit=30)
        tags = self.env["calendar.event.type"].search([], order="name asc", limit=50)

        partner_filters = self.env["calendar.filters"].search(
            [("user_id", "=", user.id)], order="id asc", limit=40
        )
        colleague_users = partner_filters.mapped("partner_id.user_ids").filtered(
            lambda u: u.active and not u.share
        )
        colleague_by_pid = {
            c["partner_id"]: c for c in self.env["res.users"]._tp_format_colleagues(colleague_users)
        }
        colleague_filters = []
        for pf in partner_filters:
            if pf.partner_id.id == user.partner_id.id:
                continue
            meta = colleague_by_pid.get(pf.partner_id.id)
            colleague_filters.append(
                {
                    "filter_id": pf.id,
                    "partner_id": pf.partner_id.id,
                    "name": pf.partner_id.name or "",
                    "department": meta["department"] if meta else "",
                    "active": bool(pf.active),
                    "avatar_url": f"/web/image/res.partner/{pf.partner_id.id}/avatar_128",
                }
            )

        tz_name = user.tz or self.env.company.partner_id.tz or "Asia/Ho_Chi_Minh"
        return {
            "primary_calendar_id": primary_cal.id if primary_cal else False,
            "my_calendars": my_calendars,
            "shared_calendars": shared_calendars,
            "colleague_filters": colleague_filters,
            "alarms": [{"id": a.id, "name": a.name} for a in alarms],
            "tags": [{"id": t.id, "name": t.name, "color": t.color or 0} for t in tags],
            "tz": tz_name,
            "self_partner_id": user.partner_id.id,
            "self_user_id": user.id,
        }

    @api.model
    def tp_toggle_calendar_visibility(self, calendar_user_id, checked):
        self.env["res.users"]._tp_require_internal_caller()
        cu = self.env["calendar.user"].search(
            [("id", "=", int(calendar_user_id or 0)), ("user_id", "=", self.env.uid)], limit=1
        )
        if not cu:
            raise AccessError(self.env._("Không tìm thấy cấu hình hiển thị lịch của bạn."))
        cu.write({"is_filter_checked": bool(checked), "is_filter_active": True})
        return {"id": cu.calendar_id.id, "checked": bool(cu.is_filter_checked)}

    @api.model
    def tp_manage_colleague_filter(self, action, partner_id, active=True):
        """Add, toggle, or remove a colleague in the user's Calendar sidebar filter."""
        self.env["res.users"]._tp_require_internal_caller()
        pid = int(partner_id or 0)
        if not pid:
            raise ValidationError(self.env._("Đồng nghiệp không hợp lệ."))
        Filter = self.env["calendar.filters"]
        existing = Filter.search(
            [("user_id", "=", self.env.uid), ("partner_id", "=", pid)], limit=1
        )
        if action == "remove":
            if existing:
                existing.unlink()
            return {"removed": True}
        if existing:
            existing.write({"active": bool(active)})
            return {"filter_id": existing.id, "active": bool(existing.active)}
        created = Filter.create(
            {"user_id": self.env.uid, "partner_id": pid, "active": bool(active)}
        )
        return {"filter_id": created.id, "active": bool(created.active)}

    @api.model
    def tp_create_user_calendar(self, name, color=2, default_privacy="public", share_user_ids=None):
        """Allow user to create an additional personal/shared `calendar.calendar`."""
        self.env["res.users"]._tp_require_internal_caller()
        clean_name = str(name or "").strip()
        if not clean_name:
            raise ValidationError(self.env._("Vui lòng nhập tên lịch mới."))
        if default_privacy not in ("public", "private", "confidential", "members_only"):
            default_privacy = "public"
        cal = self.env["calendar.calendar"].create(
            {
                "name": clean_name,
                "calendar_default_privacy": default_privacy,
            }
        )
        if cal.calendar_user_id:
            cal.calendar_user_id.write(
                {
                    "name": clean_name,
                    "filter_color": max(1, min(int(color or 2), 11)),
                    "is_filter_checked": True,
                    "is_filter_active": True,
                }
            )
        extra_uids = [
            int(u)
            for u in (share_user_ids or [])
            if str(u).isdigit() and int(u) != self.env.uid
        ]
        if extra_uids:
            valid_users = self.env["res.users"].sudo().search(
                [("id", "in", extra_uids), ("active", "=", True), ("share", "=", False)]
            )
            if valid_users:
                cal.write({"share_user_ids": [Command.set(valid_users.ids)]})
        return self.tp_get_calendar_bootstrap()

    @api.model
    def tp_check_schedule_conflicts(
        self, start_iso, stop_iso, allday=False, partner_ids=None, exclude_event_id=0
    ):
        """Return permitted busy-time conflict warnings without leaking private event details."""
        self.env["res.users"]._tp_require_internal_caller()
        tz = _user_tz(self.env)
        if allday:
            try:
                d_start = datetime.strptime(str(start_iso)[:10], "%Y-%m-%d").date()
                d_stop = datetime.strptime(str(stop_iso or start_iso)[:10], "%Y-%m-%d").date()
            except ValueError:
                return []
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
        else:
            start_utc = _parse_local_iso_to_utc(self.env, start_iso)
            stop_utc = _parse_local_iso_to_utc(self.env, stop_iso)
            if not start_utc or not stop_utc or stop_utc <= start_utc:
                return []

        pids = list(
            {
                self.env.user.partner_id.id,
                *[int(p) for p in (partner_ids or []) if str(p).isdigit()],
            }
        )
        dom = (
            Domain("active", "=", True)
            & Domain("show_as", "=", "busy")
            & Domain("start", "<", stop_utc)
            & Domain("stop", ">", start_utc)
            & Domain("partner_ids", "in", pids)
        )
        if exclude_event_id:
            dom &= Domain("id", "!=", int(exclude_event_id))

        # sudo search ONLY to check busy intervals of invited internal colleagues,
        # then strictly mask private fields via _check_private_event_conditions()!
        overlapping = self.sudo().search(dom, order="start asc", limit=30)
        partner_names = {
            p.id: p.name for p in self.env["res.partner"].sudo().browse(pids).exists()
        }
        conflicts = []
        for ev_su in overlapping:
            ev_user = ev_su.with_env(self.env)
            is_private_to_caller = ev_user._check_private_event_conditions()
            # Ignore declined invitations
            active_att_pids = set(
                ev_su.attendee_ids.filtered(lambda a: a.state != "declined").mapped("partner_id").ids
            )
            if not active_att_pids:
                active_att_pids = set(ev_su.partner_ids.ids)
            matched_pids = [pid for pid in pids if pid in active_att_pids]
            if not matched_pids:
                continue

            if ev_su.allday:
                range_str = (
                    f"{ev_su.start_date.strftime('%d/%m')} (Cả ngày)"
                    if ev_su.start_date
                    else "Cả ngày"
                )
            else:
                st_loc = ev_su.start.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                en_loc = ev_su.stop.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                range_str = f"{st_loc.strftime('%H:%M')} – {en_loc.strftime('%H:%M')} ({st_loc.strftime('%d/%m')})"

            who_names = ", ".join(partner_names.get(pid, "") for pid in matched_pids if partner_names.get(pid))
            conflicts.append(
                {
                    "event_id": ev_su.id,
                    "who": who_names,
                    "time_label": range_str,
                    "title": "Bận" if is_private_to_caller else (ev_su.name or "Bận"),
                    "is_private": is_private_to_caller,
                }
            )
        return conflicts

    def _tp_serialize_event_card(self):
        self.ensure_one()
        tz = _user_tz(self.env)
        is_masked = self._check_private_event_conditions()

        if self.allday:
            s_date = self.start_date or (self.start.date() if self.start else date.today())
            e_date = self.stop_date or s_date
            start_iso = s_date.strftime("%Y-%m-%dT08:30")
            stop_iso = e_date.strftime("%Y-%m-%dT17:00")
            start_date_str = s_date.strftime("%Y-%m-%d")
            stop_date_str = e_date.strftime("%Y-%m-%d")
            if s_date == e_date:
                time_display = f"{s_date.strftime('%d/%m/%Y')} · Cả ngày"
                short_time = "Cả ngày"
            else:
                time_display = f"{s_date.strftime('%d/%m/%Y')} – {e_date.strftime('%d/%m/%Y')} · Cả ngày"
                short_time = "Cả ngày"
            day_key = s_date.isoformat()
        else:
            st_loc = self.start.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
            en_loc = self.stop.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
            start_iso = st_loc.strftime("%Y-%m-%dT%H:%M")
            stop_iso = en_loc.strftime("%Y-%m-%dT%H:%M")
            start_date_str = st_loc.strftime("%Y-%m-%d")
            stop_date_str = en_loc.strftime("%Y-%m-%d")
            if st_loc.date() == en_loc.date():
                time_display = f"{st_loc.strftime('%d/%m/%Y')} · {st_loc.strftime('%H:%M')} – {en_loc.strftime('%H:%M')}"
            else:
                time_display = f"{st_loc.strftime('%d/%m/%Y %H:%M')} – {en_loc.strftime('%d/%m/%Y %H:%M')}"
            short_time = f"{st_loc.strftime('%H:%M')} – {en_loc.strftime('%H:%M')}"
            day_key = st_loc.date().isoformat()

        if is_masked:
            # Strict privacy mask: expose ONLY time & busy status, zero metadata!
            return {
                "id": self.id,
                "name": "Bận",
                "is_masked_private": True,
                "allday": bool(self.allday),
                "start_iso": start_iso,
                "stop_iso": stop_iso,
                "start_date": start_date_str,
                "stop_date": stop_date_str,
                "day_key": day_key,
                "time_display": time_display,
                "short_time": short_time,
                "organizer": {"id": 0, "name": "", "avatar_url": ""},
                "attendees": [],
                "location": "",
                "videocall_location": "",
                "notes_text": "",
                "privacy": "private",
                "privacy_label": PRIVACY_LABELS["private"],
                "show_as": self.show_as or "busy",
                "calendar_id": False,
                "calendar_name": "",
                "calendar_color": 0,
                "user_can_edit": False,
                "is_attendee": False,
                "my_status": "",
                "my_status_label": "",
                "recurrency": False,
                "linked_task": None,
                "alarm_ids": [],
                "categ_ids": [],
            }

        org_partner = self.sudo().user_id.partner_id
        organizer = {
            "user_id": self.user_id.id if self.user_id else 0,
            "partner_id": org_partner.id if org_partner else 0,
            "name": org_partner.name if org_partner else "",
            "avatar_url": f"/web/image/res.partner/{org_partner.id}/avatar_128" if org_partner else "",
        }

        my_pid = self.env.user.partner_id.id
        my_status = ""
        attendees = []
        for att in self.attendee_ids:
            p = att.partner_id
            st = att.state or "needsAction"
            if p.id == my_pid:
                my_status = st
            attendees.append(
                {
                    "attendee_id": att.id,
                    "partner_id": p.id,
                    "user_id": p.user_ids[:1].id if p.user_ids else 0,
                    "name": p.name or att.common_name or "",
                    "state": st,
                    "state_label": ATTENDEE_STATE_LABELS.get(st, "Chờ phản hồi"),
                    "is_organizer": bool(org_partner and p.id == org_partner.id),
                    "avatar_url": f"/web/image/res.partner/{p.id}/avatar_128" if p else "",
                }
            )

        linked_task = None
        if self.res_model == "project.task" and self.res_id:
            task = self.env["project.task"].browse(self.res_id).exists()
            if task and task.has_access("read"):
                is_personal = not task.project_id and not task.parent_id and not task.is_template
                linked_task = {
                    "id": task.id,
                    "name": task.name or f"Công việc #{task.id}",
                    "is_done": task.state == "1_done",
                    "url": f"/app/ca-nhan/cong-viec/{task.id}" if is_personal else "",
                }

        eff_priv = self.effective_privacy or "public"
        notes_plain = html2plaintext(self.notes or self.description or "").strip()

        return {
            "id": self.id,
            "name": self.name or "(Chưa đặt tiêu đề)",
            "is_masked_private": False,
            "allday": bool(self.allday),
            "start_iso": start_iso,
            "stop_iso": stop_iso,
            "start_date": start_date_str,
            "stop_date": stop_date_str,
            "day_key": day_key,
            "time_display": time_display,
            "short_time": short_time,
            "organizer": organizer,
            "attendees": attendees,
            "location": self.location or "",
            "videocall_location": self.videocall_location or "",
            "videocall_source": self.videocall_source or "",
            "notes_text": notes_plain,
            "privacy": self.privacy or eff_priv,
            "effective_privacy": eff_priv,
            "privacy_label": PRIVACY_LABELS.get(eff_priv, "Công khai nội bộ"),
            "show_as": self.show_as or "busy",
            "calendar_id": self.calendar_id.id if self.calendar_id else False,
            "calendar_name": self.calendar_id.display_name if self.calendar_id else "Lịch cá nhân",
            "calendar_color": self.calendar_color or 1,
            "user_can_edit": self._tp_can_modify_event(),
            "is_attendee": bool(my_status) and len(attendees) > 1,
            "my_status": my_status,
            "my_status_label": ATTENDEE_STATE_LABELS.get(my_status, ""),
            "recurrency": bool(self.recurrency),
            "rrule_type_ui": self.rrule_type_ui or "weekly",
            "interval": self.interval or 1,
            "end_type": self.end_type or "count",
            "count": self.count or 5,
            "until": self.until.isoformat() if self.until else "",
            "linked_task": linked_task,
            "alarm_ids": self.alarm_ids.ids,
            "alarm_names": [a.name for a in self.alarm_ids],
            "categ_ids": [{"id": c.id, "name": c.name, "color": c.color or 0} for c in self.categ_ids],
        }

    @api.model
    def tp_get_event_detail_card(self, event_id):
        self.env["res.users"]._tp_require_internal_caller()
        ev = self.browse(int(event_id or 0)).exists()
        if not ev:
            raise MissingError(self.env._("Sự kiện lịch không tồn tại hoặc đã bị xóa."))
        ev.check_access("read")
        return ev._tp_serialize_event_card()

    @api.model
    def tp_save_calendar_event(self, event_id, vals, operation_token=""):
        """Create or update a `calendar.event` with timezone accuracy, recurrence policy, and idempotency."""
        self.env["res.users"]._tp_require_internal_caller()
        vals = dict(vals or {})
        name = str(vals.get("name") or "").strip()
        if not name:
            raise ValidationError(self.env._("Vui lòng nhập tiêu đề lịch làm việc."))

        allday = bool(vals.get("allday"))
        if allday:
            s_date_raw = str(vals.get("start_date") or vals.get("start_iso") or "")[:10]
            e_date_raw = str(vals.get("stop_date") or vals.get("stop_iso") or s_date_raw)[:10]
            try:
                s_date = datetime.strptime(s_date_raw, "%Y-%m-%d").date()
                e_date = datetime.strptime(e_date_raw, "%Y-%m-%d").date()
            except ValueError as exc:
                raise ValidationError(self.env._("Vui lòng chọn ngày bắt đầu và kết thúc hợp lệ.")) from exc
            if e_date < s_date:
                raise ValidationError(self.env._("Ngày kết thúc không được trước ngày bắt đầu."))
            time_vals = {
                "allday": True,
                "start_date": s_date,
                "stop_date": e_date,
            }
        else:
            start_utc = _parse_local_iso_to_utc(self.env, vals.get("start_iso"))
            stop_utc = _parse_local_iso_to_utc(self.env, vals.get("stop_iso"))
            if not start_utc or not stop_utc:
                raise ValidationError(self.env._("Vui lòng chọn thời gian bắt đầu và kết thúc."))
            if stop_utc <= start_utc:
                raise ValidationError(self.env._("Giờ kết thúc phải sau giờ bắt đầu."))
            time_vals = {
                "allday": False,
                "start": start_utc,
                "stop": stop_utc,
            }

        my_pid = self.env.user.partner_id.id
        supplied_pids = [int(p) for p in (vals.get("partner_ids") or []) if str(p).isdigit()]
        if my_pid not in supplied_pids:
            supplied_pids.insert(0, my_pid)
        valid_partners = self.env["res.partner"].sudo().search([("id", "in", supplied_pids)])

        privacy = vals.get("privacy") or "public"
        if privacy not in ("public", "private", "confidential", "members_only"):
            privacy = "public"
        show_as = vals.get("show_as") or "busy"
        if show_as not in ("busy", "free"):
            show_as = "busy"

        notes_raw = str(vals.get("notes") or "").strip()
        notes_html = (
            html_sanitize(
                "".join(
                    f"<p>{html.escape(line) if line.strip() else '<br/>'}</p>"
                    for line in notes_raw.splitlines()
                )
            )
            if notes_raw
            else False
        )

        alarm_ids = [int(a) for a in (vals.get("alarm_ids") or []) if str(a).isdigit()]
        categ_ids = [int(c) for c in (vals.get("categ_ids") or []) if str(c).isdigit()]

        write_vals = {
            "name": name,
            **time_vals,
            "partner_ids": [Command.set(valid_partners.ids)],
            "location": str(vals.get("location") or "").strip() or False,
            "notes": notes_html,
            "description": notes_html,
            "privacy": privacy,
            "show_as": show_as,
            "alarm_ids": [Command.set(alarm_ids)],
        }
        if categ_ids or "categ_ids" in vals:
            write_vals["categ_ids"] = [Command.set(categ_ids)]

        cal_id = int(vals.get("calendar_id") or 0)
        if cal_id:
            cal = self.env["calendar.calendar"].browse(cal_id).exists()
            if cal and (cal.owner_id == self.env.user or cal.id in self.env.user.writable_calendar_ids.ids):
                write_vals["calendar_id"] = cal.id

        # Video call link handling (native Discuss meeting room or custom URL)
        use_discuss_call = bool(vals.get("use_discuss_videocall"))
        custom_video_url = str(vals.get("videocall_location") or "").strip()
        if custom_video_url and not use_discuss_call:
            write_vals["videocall_location"] = custom_video_url
        elif "videocall_location" in vals and not custom_video_url and not use_discuss_call:
            write_vals["videocall_location"] = False

        # Recurrence fields
        recurrency = bool(vals.get("recurrency"))
        if "recurrency" in vals:
            write_vals["recurrency"] = recurrency
            if recurrency:
                rrule_ui = vals.get("rrule_type_ui") or "weekly"
                if rrule_ui not in ("daily", "weekly", "monthly", "yearly"):
                    rrule_ui = "weekly"
                write_vals["rrule_type_ui"] = rrule_ui
                write_vals["rrule_type"] = rrule_ui
                write_vals["interval"] = max(1, int(vals.get("interval") or 1))
                if rrule_ui == "weekly":
                    weekday_fields = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
                    if not any(bool(vals.get(wf)) for wf in weekday_fields):
                        local_d = (
                            s_date
                            if allday
                            else start_utc.replace(tzinfo=ZoneInfo("UTC"))
                            .astimezone(_user_tz(self.env))
                            .date()
                        )
                        write_vals[weekday_fields[local_d.weekday()]] = True
                end_type = vals.get("end_type") or "count"
                if end_type == "end_date" and vals.get("until"):
                    write_vals["end_type"] = "end_date"
                    write_vals["until"] = str(vals["until"])[:10]
                else:
                    write_vals["end_type"] = "count"
                    write_vals["count"] = max(1, min(int(vals.get("count") or 5), 365))

        if event_id:
            ev = self.browse(int(event_id)).exists()
            if not ev:
                raise MissingError(self.env._("Sự kiện lịch không tồn tại."))
            if not ev._tp_can_modify_event():
                raise AccessError(
                    self.env._("Bạn không có quyền sửa lịch của người chủ trì.")
                )
            if ev.recurrency:
                rec_policy = vals.get("recurrence_update") or "self_only"
                if rec_policy not in ("self_only", "future_events", "all_events"):
                    rec_policy = "self_only"
                write_vals["recurrence_update"] = rec_policy
            ev.write(write_vals)
            if use_discuss_call and not ev.videocall_location:
                ev.set_discuss_videocall_location()
            ev_latest = ev.exists() or self.search([("recurrence_id", "=", ev.recurrence_id.id)], limit=1)
            return ev_latest._tp_serialize_event_card() if ev_latest else {"id": int(event_id)}

        # Create path (idempotent via operation_token)
        if vals.get("res_model") and vals.get("res_id"):
            target_rec = self.env[vals["res_model"]].browse(int(vals["res_id"])).exists()
            if target_rec:
                target_rec.check_access("read")
                write_vals["res_model_id"] = self.env["ir.model"]._get_id(vals["res_model"])
                write_vals["res_id"] = target_rec.id

        op_payload = {
            "name": name,
            "allday": allday,
            "start": str(write_vals.get("start") or write_vals.get("start_date")),
            "stop": str(write_vals.get("stop") or write_vals.get("stop_date")),
            "partners": sorted(valid_partners.ids),
            "res_model": str(vals.get("res_model") or ""),
            "res_id": int(vals.get("res_id") or 0),
        }
        op_log = self.env["tp.personal.operation.log"]
        existing, clean_token, fp = op_log.acquire_or_replay(
            "create_calendar_event", operation_token, op_payload
        )
        if existing:
            return existing._tp_serialize_event_card()

        ev = self.create(write_vals)
        if use_discuss_call and not ev.videocall_location:
            ev.set_discuss_videocall_location()
        op_log.record_success("create_calendar_event", clean_token, fp, ev)
        return ev._tp_serialize_event_card()

    @api.model
    def tp_get_calendar_agenda(self, params=None):
        """Paginated, privacy-safe Agenda / List view grouped by local day."""
        self.env["res.users"]._tp_require_internal_caller()
        params = dict(params or {})
        tz = _user_tz(self.env)
        today_loc = datetime.now(tz).date()

        date_from_raw = str(params.get("date_from") or "").strip()[:10]
        date_to_raw = str(params.get("date_to") or "").strip()[:10]
        if not date_from_raw:
            d_from = today_loc - timedelta(days=today_loc.weekday())
        else:
            d_from = datetime.strptime(date_from_raw, "%Y-%m-%d").date()
        if not date_to_raw:
            d_to = d_from + timedelta(days=30)
        else:
            d_to = datetime.strptime(date_to_raw, "%Y-%m-%d").date()
        if d_to < d_from:
            raise ValidationError(self.env._("Khoảng ngày lọc không hợp lệ (Từ ngày lớn hơn Đến ngày)."))

        start_utc = (
            datetime.combine(d_from, time.min, tzinfo=tz)
            .astimezone(ZoneInfo("UTC"))
            .replace(tzinfo=None)
        )
        stop_utc = (
            datetime.combine(d_to + timedelta(days=1), time.min, tzinfo=tz)
            .astimezone(ZoneInfo("UTC"))
            .replace(tzinfo=None)
        )

        dom = (
            Domain("active", "=", True)
            & Domain("start", "<", stop_utc)
            & Domain("stop", ">=", start_utc)
        )

        # Scope to checked calendars + user's own events + checked colleagues unless explicitly filtered
        cal_ids = [int(c) for c in (params.get("calendar_ids") or []) if str(c).isdigit()]
        partner_filter_ids = [int(p) for p in (params.get("partner_ids") or []) if str(p).isdigit()]
        my_pid = self.env.user.partner_id.id
        if cal_ids or partner_filter_ids:
            scope_or = Domain("partner_ids", "in", [my_pid] + partner_filter_ids)
            if cal_ids:
                scope_or |= Domain("calendar_id", "in", cal_ids)
            dom &= scope_or
        else:
            dom &= Domain("partner_ids", "in", [my_pid]) | Domain("user_id", "=", self.env.uid)

        q = str(params.get("q") or "").strip()
        if q:
            # Our `_search` override automatically restricts sensitive text search to visible non-private events!
            dom &= (
                Domain("name", "ilike", q)
                | Domain("location", "ilike", q)
                | Domain("description", "ilike", q)
            )

        organizer_id = int(params.get("organizer_id") or 0)
        if organizer_id:
            dom &= Domain("user_id", "=", organizer_id)

        attendee_pid = int(params.get("attendee_partner_id") or 0)
        if attendee_pid:
            dom &= Domain("partner_ids", "in", [attendee_pid])

        privacy_filter = str(params.get("privacy") or "").strip()
        if privacy_filter in ("public", "private", "confidential", "members_only"):
            dom &= Domain("effective_privacy", "in", [privacy_filter])

        response_state = str(params.get("response_state") or "").strip()
        if response_state in ("accepted", "declined", "tentative", "needsAction"):
            dom &= Domain(
                "attendee_ids",
                "any",
                [("partner_id", "=", my_pid), ("state", "=", response_state)],
            )

        page = max(1, int(params.get("page") or 1))
        page_size = int(params.get("page_size") or 100)
        if page_size not in (10, 20, 50, 100):
            page_size = 100

        total_count = self.search_count(dom)
        offset = (page - 1) * page_size
        if offset >= total_count and total_count > 0:
            page = max(1, (total_count - 1) // page_size + 1)
            offset = (page - 1) * page_size

        events = self.search(dom, order="start asc, id asc", offset=offset, limit=page_size)
        cards = [ev._tp_serialize_event_card() for ev in events]

        weekday_names = [
            "Thứ hai",
            "Thứ ba",
            "Thứ tư",
            "Thứ năm",
            "Thứ sáu",
            "Thứ bảy",
            "Chủ nhật",
        ]
        groups = []
        group_map = {}
        for c in cards:
            dk = c["day_key"]
            if dk not in group_map:
                d_obj = datetime.strptime(dk, "%Y-%m-%d").date()
                wd = weekday_names[d_obj.weekday()]
                suffix = " · Hôm nay" if d_obj == today_loc else ""
                grp = {
                    "day_key": dk,
                    "day_label": f"{wd}, {d_obj.strftime('%d/%m/%Y')}{suffix}",
                    "is_today": d_obj == today_loc,
                    "events": [],
                }
                group_map[dk] = grp
                groups.append(grp)
            group_map[dk]["events"].append(c)

        return {
            "groups": groups,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "date_from": d_from.isoformat(),
            "date_to": d_to.isoformat(),
            "today_iso": today_loc.isoformat(),
        }
