# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Cross-tool sharing & Discuss helpers for TANPHAT ONE Personal Tools.

Allows users to share links to permitted Personal Tasks or Calendar Events into
Direct Messages, Groups, or Channels they belong to, without auto-posting on save
and without leaking private content to unauthorized members.
"""

import html
from datetime import datetime
from zoneinfo import ZoneInfo

from markupsafe import Markup

from odoo import api, models
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Domain


def _user_tz(env):
    tz_name = env.user.tz or env.company.partner_id.tz or "Asia/Ho_Chi_Minh"
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


class PersonalDiscussChannel(models.Model):
    _inherit = "discuss.channel"

    @api.model
    def tp_list_share_targets(self, query="", limit=30):
        """Return active conversations (`chat`, `group`, `channel`) the caller can post to."""
        self.env["res.users"]._tp_require_internal_caller()
        safe_limit = max(1, min(int(limit or 30), 60))
        odoobot_id = self.env["ir.model.data"]._xmlid_to_res_id("base.partner_root") or 0

        domain = Domain("active", "=", True) & Domain("is_member", "=", True)
        channels = self.search(domain, order="last_interest_dt desc, id desc", limit=120)
        q = (query or "").strip().lower()
        results = []
        type_labels = {
            "chat": "Tin trực tiếp",
            "group": "Nhóm trao đổi",
            "channel": "Kênh nội bộ",
        }
        for ch in channels:
            if ch.channel_type == "chat" and odoobot_id:
                member_pids = ch.sudo().channel_member_ids.mapped("partner_id").ids
                if odoobot_id in member_pids:
                    continue
            label = (ch.display_name or ch.name or "").strip()
            if not label:
                continue
            if q and q not in label.lower():
                continue
            results.append(
                {
                    "id": ch.id,
                    "name": label,
                    "channel_type": ch.channel_type,
                    "type_label": type_labels.get(ch.channel_type, "Hội thoại"),
                    "member_count": ch.member_count or 0,
                }
            )
            if len(results) >= safe_limit:
                break
        return results

    @api.model
    def tp_list_shareable_personal_items(self, kind="todo", query="", limit=25):
        """List caller's own permitted Personal Tasks or Calendar Events for link insertion."""
        self.env["res.users"]._tp_require_internal_caller()
        safe_limit = max(1, min(int(limit or 25), 50))
        q = (query or "").strip()
        tz = _user_tz(self.env)

        if kind == "calendar":
            dom = Domain("active", "=", True) & (
                Domain("user_id", "=", self.env.uid)
                | Domain("partner_ids", "in", [self.env.user.partner_id.id])
            )
            if q:
                dom &= Domain("name", "ilike", q)
            events = self.env["calendar.event"].search(dom, order="start desc, id desc", limit=safe_limit)
            items = []
            for ev in events:
                if ev._check_private_event_conditions():
                    continue
                if ev.allday:
                    sub = ev.start_date.strftime("%d/%m/%Y") + " · Cả ngày" if ev.start_date else "Cả ngày"
                else:
                    st = ev.start.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz) if ev.start else None
                    sub = st.strftime("%d/%m/%Y %H:%M") if st else ""
                items.append(
                    {
                        "id": ev.id,
                        "model": "calendar.event",
                        "title": ev.name or "Lịch làm việc",
                        "subtitle": sub,
                        "url": f"/app/ca-nhan/lich-lam-viec/{ev.id}",
                    }
                )
            return items

        # Default: personal tasks
        Task = self.env["project.task"]
        dom = Task._tp_base_personal_domain(include_archived=False)
        if q:
            dom &= Domain("name", "ilike", q)
        tasks = Task.search(dom, order="is_closed asc, id desc", limit=safe_limit)
        items = []
        for t in tasks:
            sub = "Hoàn thành" if t.is_closed else "Đang thực hiện"
            if t.date_deadline:
                dl = t.date_deadline.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                sub += f" · Hạn {dl.strftime('%d/%m/%Y')}"
            items.append(
                {
                    "id": t.id,
                    "model": "project.task",
                    "title": t.name or "Công việc cá nhân",
                    "subtitle": sub,
                    "url": f"/app/ca-nhan/cong-viec/{t.id}",
                }
            )
        return items

    @api.model
    def tp_share_record_to_channel(
        self, channel_id, target_model, target_id, note="", operation_token=""
    ):
        """Post a safe internal link to a Personal Task or Calendar Event into a Discuss channel.

        Does NOT leak private descriptions, private event titles, or participant lists:
        recipients must pass backend ACL when opening the link.
        """
        self.env["res.users"]._tp_require_internal_caller()
        if target_model not in ("project.task", "calendar.event"):
            raise ValidationError(self.env._("Loại liên kết chia sẻ không được hỗ trợ."))

        cid = int(channel_id or 0)
        tid = int(target_id or 0)
        channel = self.browse(cid).exists()
        if not channel or not channel.active:
            raise MissingError(self.env._("Hội thoại không tồn tại hoặc đã đóng."))
        channel.check_access("read")
        if not channel.is_member and channel.channel_type != "channel":
            raise AccessError(self.env._("Bạn không phải thành viên của hội thoại này."))

        record = self.env[target_model].browse(tid).exists()
        if not record:
            raise MissingError(self.env._("Mục cần chia sẻ không tồn tại."))

        if target_model == "project.task":
            record._tp_assert_personal_task_access(mode="read")
            url = f"/app/ca-nhan/cong-viec/{record.id}"
            kind_label = "Công việc cá nhân"
            # Do not embed private title if task is only assigned to self unless note says so:
            # show generic safe anchor `#ID` + link so unauthorized members in a group see zero private details!
            link_label = f"Việc cá nhân #{record.id}"
        else:
            record.check_access("read")
            if record._check_private_event_conditions():
                raise AccessError(self.env._("Bạn không có quyền chia sẻ lịch riêng tư của người khác."))
            url = f"/app/ca-nhan/lich-lam-viec/{record.id}"
            kind_label = "Lịch làm việc"
            is_private = record.effective_privacy == "private"
            link_label = (
                f"Lịch hẹn #{record.id}"
                if is_private
                else (record.name or f"Lịch hẹn #{record.id}")
            )

        clean_note = str(note or "").strip()
        op_log = self.env["tp.personal.operation.log"]
        existing, clean_token, fp = op_log.acquire_or_replay(
            "share_record_to_channel",
            operation_token,
            {
                "channel_id": channel.id,
                "model": target_model,
                "id": record.id,
                "note": clean_note,
            },
        )
        if existing:
            return {"message_id": existing.id, "channel_id": channel.id, "url": url}

        parts = []
        if clean_note:
            parts.append(
                Markup("<p>%s</p>")
                % Markup("<br/>").join(html.escape(line) for line in clean_note.splitlines())
            )
        parts.append(
            Markup(
                '<p><strong>%s:</strong> <a href="%s">%s</a></p>'
            )
            % (html.escape(kind_label), html.escape(url), html.escape(link_label))
        )
        msg = channel.message_post(
            body=Markup("").join(parts),
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )
        op_log.record_success("share_record_to_channel", clean_token, fp, msg)
        return {"message_id": msg.id, "channel_id": channel.id, "url": url}

    @api.model
    def tp_create_internal_channel(self, name, description="", operation_token=""):
        """Create an internal company channel (`group_public_id = base.group_user`) idempotently."""
        self.env["res.users"]._tp_require_internal_caller()
        clean_name = str(name or "").strip()
        if not clean_name:
            raise ValidationError(self.env._("Vui lòng nhập tên kênh nội bộ."))
        clean_desc = str(description or "").strip()
        internal_group = self.env.ref("base.group_user", raise_if_not_found=False)

        op_log = self.env["tp.personal.operation.log"]
        existing, clean_token, fp = op_log.acquire_or_replay(
            "create_internal_channel",
            operation_token,
            {"name": clean_name, "description": clean_desc},
        )
        if existing:
            return {"id": existing.id, "name": existing.name}

        vals = {
            "name": clean_name,
            "description": clean_desc or False,
            "channel_type": "channel",
            "group_public_id": internal_group.id if internal_group else False,
        }
        channel = self.create(vals)
        note = Markup('<div class="o_mail_notification">%s</div>') % html.escape(
            self.env._("đã tạo kênh trao đổi nội bộ.")
        )
        channel.message_post(
            body=note, message_type="notification", subtype_xmlid="mail.mt_comment"
        )
        op_log.record_success("create_internal_channel", clean_token, fp, channel)
        return {"id": channel.id, "name": channel.name}

