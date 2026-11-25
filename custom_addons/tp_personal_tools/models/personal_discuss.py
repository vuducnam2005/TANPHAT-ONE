# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Cross-tool sharing, Scoped Project/Department Channels, & Message-to-Task conversion.

Guarantees:
1. Scoped Project / Department channels (`tp_channel_scope` in `('department', 'project')`):
   - Explicit source link (`tp_department_id` or `tp_project_id`) and explicit manager (`tp_manager_user_id`).
   - Initial members resolved strictly from active department employees or active project participants/assignees.
   - NEVER adds the whole company automatically and NEVER auto-adds technical admins into conversations.
2. Convert Message to Task (`tp_preview_message_for_task` / `tp_create_task_from_message`):
   - Strictly verifies caller read access & membership on the source `mail.message` and `discuss.channel`.
   - Requires explicit preview/confirm payload; stores `tp_source_message_id` + `tp_source_channel_id`.
   - Idempotent via `operation_token` (`tp.personal.operation.log`).
"""

import html
from zoneinfo import ZoneInfo

from markupsafe import Markup

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Domain
from odoo.tools import html2plaintext


def _user_tz(env):
    tz_name = env.user.tz or env.company.partner_id.tz or "Asia/Ho_Chi_Minh"
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


class PersonalDiscussChannel(models.Model):
    _inherit = "discuss.channel"

    tp_channel_scope = fields.Selection(
        [
            ("general", "Kênh nội bộ chung"),
            ("department", "Nhóm / Kênh phòng ban"),
            ("project", "Nhóm / Kênh dự án"),
        ],
        string="Phạm vi hội thoại",
        default="general",
        index=True,
        export_string_translation=False,
    )
    tp_department_id = fields.Many2one(
        "hr.department",
        string="Phòng ban nguồn",
        ondelete="set null",
        index=True,
        export_string_translation=False,
    )
    tp_project_id = fields.Many2one(
        "project.project",
        string="Dự án nguồn",
        ondelete="set null",
        index=True,
        export_string_translation=False,
    )
    tp_manager_user_id = fields.Many2one(
        "res.users",
        string="Người quản lý hội thoại",
        ondelete="set null",
        index=True,
        export_string_translation=False,
    )

    def _tp_assert_caller_can_read_channel(self):
        self.ensure_one()
        self.check_access("read")
        if self.channel_type in ("chat", "group") and not self.is_member:
            raise AccessError(self.env._("Bạn không phải thành viên của hội thoại riêng tư này."))
        if self.channel_type == "channel" and self.group_public_id:
            if self.group_public_id not in self.env.user.all_group_ids and not self.is_member:
                raise AccessError(self.env._("Bạn không có quyền truy cập kênh nội bộ này."))
        elif self.channel_type == "channel" and not self.group_public_id and not self.is_member:
            # Private scoped channel (group_public_id = False) requires explicit membership!
            if self.tp_channel_scope in ("department", "project"):
                raise AccessError(self.env._("Kênh theo dự án/phòng ban chỉ dành cho thành viên thuộc phạm vi."))

    @api.model
    def _tp_resolve_department_users(self, department):
        """Return active internal `res.users` belonging to `department` (plus manager + caller).

        Never adds the whole company and never auto-adds technical admins.
        """
        emps = self.env["hr.employee"].sudo().search(
            [
                ("active", "=", True),
                ("department_id", "=", department.id),
                ("user_id", "!=", False),
            ]
        )
        users = emps.mapped("user_id").filtered(lambda u: u.active and not u.share)
        if department.sudo().manager_id and department.sudo().manager_id.user_id:
            mgr_u = department.sudo().manager_id.user_id
            if mgr_u.active and not mgr_u.share:
                users |= mgr_u
        users |= self.env.user
        return users

    @api.model
    def _tp_resolve_project_users(self, project):
        """Return active internal `res.users` assigned to `project` (PM + participants + task assignees + caller).

        Never adds the whole company and never auto-adds technical admins.
        """
        users = self.env.user
        proj_su = project.sudo()
        if proj_su.user_id and proj_su.user_id.active and not proj_su.user_id.share:
            users |= proj_su.user_id

        if "tp.project.participation" in self.env:
            parts = self.env["tp.project.participation"].sudo().search(
                [("project_id", "=", project.id), ("active", "=", True)]
            )
            part_users = parts.mapped("user_id").filtered(lambda u: u.active and not u.share)
            users |= part_users

        proj_tasks = self.env["project.task"].sudo().search(
            [("project_id", "=", project.id), ("active", "=", True)]
        )
        task_users = proj_tasks.mapped("user_ids").filtered(lambda u: u.active and not u.share)
        users |= task_users
        return users

    @api.model
    def tp_get_channel_creation_options(self):
        """Return caller's permitted departments and projects for creating linked channels."""
        self.env["res.users"]._tp_require_internal_caller()
        depts = self.env["hr.department"].search([("active", "=", True)], order="name asc", limit=100)
        projects = self.env["project.project"].search([("active", "=", True)], order="name asc", limit=150)
        return {
            "departments": [{"id": d.id, "name": d.name or ""} for d in depts],
            "projects": [
                {
                    "id": p.id,
                    "name": p.name or "",
                    "code": getattr(p, "tp_code", "") or "",
                }
                for p in projects
            ],
        }

    @api.model
    def tp_preview_scoped_members(self, scope, source_id):
        """Preview exact members that will be added from a department or project before creating."""
        self.env["res.users"]._tp_require_internal_caller()
        sid = int(source_id or 0)
        if not sid:
            return []
        if scope == "department":
            dept = self.env["hr.department"].browse(sid).exists()
            if not dept:
                return []
            dept.check_access("read")
            users = self._tp_resolve_department_users(dept)
        elif scope == "project":
            proj = self.env["project.project"].browse(sid).exists()
            if not proj:
                return []
            proj.check_access("read")
            users = self._tp_resolve_project_users(proj)
        else:
            return []
        return self.env["res.users"]._tp_format_colleagues(users)

    @api.model
    def tp_create_scoped_channel(self, vals, operation_token=""):
        """Create a Project-linked or Department-linked private group/channel with rule-based members."""
        self.env["res.users"]._tp_require_internal_caller()
        vals = dict(vals or {})
        scope = str(vals.get("scope") or "").strip()
        if scope not in ("department", "project"):
            raise ValidationError(self.env._("Loại nhóm liên kết phải là Phòng ban hoặc Dự án."))

        source_id = int(vals.get("source_id") or 0)
        clean_name = str(vals.get("name") or "").strip()
        clean_desc = str(vals.get("description") or "").strip()

        dept = False
        proj = False
        if scope == "department":
            dept = self.env["hr.department"].browse(source_id).exists()
            if not dept:
                raise ValidationError(self.env._("Vui lòng chọn phòng ban liên kết hợp lệ."))
            dept.check_access("read")
            if not clean_name:
                clean_name = f"Phòng {dept.name}"
            member_users = self._tp_resolve_department_users(dept)
        else:
            proj = self.env["project.project"].browse(source_id).exists()
            if not proj:
                raise ValidationError(self.env._("Vui lòng chọn dự án liên kết hợp lệ."))
            proj.check_access("read")
            if not clean_name:
                code_prefix = f"[{proj.tp_code}] " if getattr(proj, "tp_code", False) else ""
                clean_name = f"Dự án {code_prefix}{proj.name}"
            member_users = self._tp_resolve_project_users(proj)

        extra_uids = [int(u) for u in (vals.get("extra_user_ids") or []) if str(u).isdigit()]
        if extra_uids:
            extra_valid = self.env["res.users"].sudo().search(
                [("id", "in", extra_uids), ("active", "=", True), ("share", "=", False)]
            )
            member_users |= extra_valid

        op_log = self.env["tp.personal.operation.log"]
        existing, clean_token, fp = op_log.acquire_or_replay(
            "create_scoped_channel",
            operation_token,
            {
                "scope": scope,
                "source_id": source_id,
                "name": clean_name,
                "members": sorted(member_users.ids),
            },
        )
        if existing:
            return {
                "id": existing.id,
                "name": existing.name,
                "scope": existing.tp_channel_scope,
                "member_count": len(existing.sudo().channel_member_ids),
            }

        # Create as a private group (`channel_type='group'`) so ONLY explicit members can read/post!
        channel = self._create_group(member_users, name=clean_name)
        channel.sudo().write(
            {
                "description": clean_desc or False,
                "tp_channel_scope": scope,
                "tp_department_id": dept.id if dept else False,
                "tp_project_id": proj.id if proj else False,
                "tp_manager_user_id": self.env.uid,
            }
        )
        source_lbl = (
            f"phòng ban {dept.name}" if dept else f"dự án {proj.name}"
        )
        note = Markup('<div class="o_mail_notification">%s</div>') % html.escape(
            self.env._(
                "đã khởi tạo hội thoại liên kết %(src)s (%(cnt)s thành viên theo phân công).",
                src=source_lbl,
                cnt=len(member_users),
            )
        )
        channel.message_post(
            body=note, message_type="notification", subtype_xmlid="mail.mt_comment"
        )
        op_log.record_success("create_scoped_channel", clean_token, fp, channel)
        return {
            "id": channel.id,
            "name": channel.name,
            "scope": scope,
            "member_count": len(member_users),
        }

    @api.model
    def tp_sync_scoped_channel_members(self, channel_id):
        """Synchronize newly added active department/project members on manager request.

        Policy (Section F3):
        - Adds active members newly assigned to the source department/project.
        - Does NOT silently delete historical messages; returns `departed_partner_ids` so the
          channel manager can explicitly review/remove transferred members if desired.
        """
        self.env["res.users"]._tp_require_internal_caller()
        ch = self.browse(int(channel_id or 0)).exists()
        if not ch:
            raise MissingError(self.env._("Hội thoại không tồn tại."))
        ch._tp_assert_caller_can_read_channel()
        is_mgr = (
            ch.tp_manager_user_id == self.env.user
            or self.env.user.has_group("base.group_system")
            or self.env.user.has_group("tp_admin_delegation.group_full_admin")
        )
        if not is_mgr:
            raise AccessError(self.env._("Chỉ người quản lý hội thoại mới được đồng bộ danh sách thành viên."))

        if ch.tp_channel_scope == "department" and ch.tp_department_id:
            expected_users = self._tp_resolve_department_users(ch.tp_department_id)
        elif ch.tp_channel_scope == "project" and ch.tp_project_id:
            expected_users = self._tp_resolve_project_users(ch.tp_project_id)
        else:
            raise ValidationError(self.env._("Hội thoại này không gắn với nguồn Phòng ban hoặc Dự án."))

        expected_pids = set(expected_users.mapped("partner_id").ids)
        current_pids = set(ch.sudo().channel_member_ids.mapped("partner_id").ids)
        to_add_pids = list(expected_pids - current_pids)
        if to_add_pids:
            ch.sudo().add_members(partner_ids=to_add_pids)
        departed_pids = list(
            current_pids - expected_pids - {ch.tp_manager_user_id.partner_id.id if ch.tp_manager_user_id else 0}
        )
        return {
            "channel_id": ch.id,
            "added_count": len(to_add_pids),
            "departed_partner_ids": departed_pids,
        }

    @api.model
    def tp_preview_message_for_task(self, message_id):
        """Return safe preview payload for converting a Discuss `mail.message` into a task."""
        self.env["res.users"]._tp_require_internal_caller()
        mid = int(message_id or 0)
        msg = self.env["mail.message"].sudo().browse(mid).exists()
        if not msg or msg.model != "discuss.channel" or not msg.res_id:
            raise MissingError(self.env._("Tin nhắn nguồn không tồn tại hoặc không thuộc hội thoại."))

        channel = self.browse(msg.res_id).exists()
        if not channel:
            raise MissingError(self.env._("Hội thoại nguồn không tồn tại."))
        channel._tp_assert_caller_can_read_channel()

        plain = html2plaintext(msg.body or "").strip()
        if not plain and msg.attachment_ids:
            plain = "Xử lý tệp đính kèm: " + ", ".join(a.name for a in msg.attachment_ids if a.name)
        first_line = (plain.splitlines()[0] if plain else "").strip()
        suggested_title = (first_line[:110] + "…") if len(first_line) > 110 else (first_line or "Công việc từ trao đổi")

        default_assignees = self.env["res.users"]._tp_format_colleagues(self.env.user)
        tz = _user_tz(self.env)
        sent_label = (
            msg.date.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz).strftime("%d/%m/%Y %H:%M")
            if msg.date
            else ""
        )
        project_info = None
        if channel.tp_project_id and channel.tp_project_id.has_access("read"):
            project_info = {
                "id": channel.tp_project_id.id,
                "name": channel.tp_project_id.name or "",
            }

        return {
            "message_id": msg.id,
            "channel_id": channel.id,
            "channel_name": channel.display_name or channel.name or "Trao đổi",
            "author_name": msg.author_id.name or "Đồng nghiệp",
            "sent_label": sent_label,
            "suggested_title": suggested_title,
            "body_text": plain,
            "default_assignees": default_assignees,
            "linked_project": project_info,
        }

    @api.model
    def tp_create_task_from_message(self, message_id, vals, operation_token=""):
        """Convert a permitted Discuss `mail.message` into a `project.task` idempotently.

        Enforces:
        - Caller must have read/member access on the message's channel.
        - Stores `tp_source_kind = 'chat'`, `tp_source_message_id`, `tp_source_channel_id`,
          `tp_assigner_user_id = env.uid`.
        - Prevents duplicate task creation via `operation_token`.
        """
        self.env["res.users"]._tp_require_internal_caller()
        preview = self.tp_preview_message_for_task(message_id)
        channel = self.browse(preview["channel_id"])
        vals = dict(vals or {})

        name = str(vals.get("name") or "").strip()
        if not name:
            raise ValidationError(self.env._("Vui lòng nhập tiêu đề công việc cần tạo."))

        supplied_uids = [int(u) for u in (vals.get("user_ids") or []) if str(u).isdigit()]
        if not supplied_uids:
            supplied_uids = [self.env.uid]
        valid_users = self.env["res.users"].sudo().search(
            [("id", "in", supplied_uids), ("active", "=", True), ("share", "=", False)]
        )
        if not valid_users:
            raise ValidationError(self.env._("Vui lòng chọn ít nhất một người nhận công việc hợp lệ."))

        Task = self.env["project.task"]
        deadline_utc = Task._tp_parse_local_datetime_input(vals.get("deadline_iso"))
        priority = str(vals.get("priority") or "0")
        if priority not in ("0", "1", "2", "3"):
            priority = "0"
        deliverable = str(vals.get("deliverable") or "").strip()
        note_raw = str(vals.get("note_text") or preview["body_text"] or "").strip()

        op_log = self.env["tp.personal.operation.log"]
        existing, clean_token, fp = op_log.acquire_or_replay(
            "create_task_from_message",
            operation_token,
            {
                "message_id": int(message_id),
                "name": name,
                "users": sorted(valid_users.ids),
                "deadline": str(deadline_utc or ""),
                "deliverable": deliverable,
            },
        )
        if existing:
            stages = Task._tp_ensure_my_personal_stages()
            return existing._tp_serialize_tasks(stages)[0]

        from .personal_task import _compose_description_html

        desc_lines = []
        if note_raw:
            desc_lines.append(note_raw)
        desc_lines.append(
            f"[Nguồn Trao đổi: {preview['channel_name']} — {preview['author_name']} ({preview['sent_label']})]"
        )
        desc_html = _compose_description_html("\n\n".join(desc_lines), [])

        has_other_assignee = any(u.id != self.env.uid for u in valid_users)
        create_vals = {
            "name": name,
            "project_id": False,
            "parent_id": False,
            "is_template": False,
            "user_ids": [Command.set(valid_users.ids)],
            "priority": priority,
            "date_deadline": deadline_utc,
            "tp_deliverable": deliverable or False,
            "tp_source_kind": "chat",
            "tp_source_message_id": int(message_id),
            "tp_source_channel_id": channel.id,
            "tp_assigner_user_id": self.env.uid,
            "tp_verifier_user_id": self.env.uid if has_other_assignee else False,
            "tp_exec_report_state": "in_progress",
            "description": desc_html,
            "state": "01_in_progress",
        }
        task = Task.with_context(
            default_project_id=False,
            default_parent_id=False,
            mail_create_nosubscribe=False,
        ).create(create_vals)

        stages = Task._tp_ensure_my_personal_stages()
        if self.env.user in valid_users:
            Task._tp_ensure_personal_stage_rels(task, stages)

        if vals.get("notify_channel"):
            task_url = f"/app/ca-nhan/cong-viec/{task.id}"
            assignee_names = ", ".join(u.name for u in valid_users)
            post_body = Markup(
                '<p>Đã tạo công việc từ tin nhắn: <a href="%s"><strong>#%s</strong></a> · Người thực hiện: %s</p>'
            ) % (html.escape(task_url), task.id, html.escape(assignee_names))
            channel.message_post(
                body=post_body,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )

        op_log.record_success("create_task_from_message", clean_token, fp, task)
        return task._tp_serialize_tasks(stages)[0]

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
            scope_lbl = type_labels.get(ch.channel_type, "Hội thoại")
            if ch.tp_channel_scope == "project":
                scope_lbl = "Nhóm dự án"
            elif ch.tp_channel_scope == "department":
                scope_lbl = "Nhóm phòng ban"
            results.append(
                {
                    "id": ch.id,
                    "name": label,
                    "channel_type": ch.channel_type,
                    "type_label": scope_lbl,
                    "member_count": ch.member_count or 0,
                }
            )
            if len(results) >= safe_limit:
                break
        return results

    @api.model
    def tp_list_shareable_personal_items(self, kind="todo", query="", limit=25):
        """List caller's own permitted Tasks or Calendar Events for link insertion."""
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

        Task = self.env["project.task"]
        dom = Task._tp_my_work_domain(include_archived=False)
        if q:
            dom &= Domain("name", "ilike", q)
        tasks = Task.search(dom, order="is_closed asc, id desc", limit=safe_limit)
        items = []
        for t in tasks:
            sub = "Hoàn thành" if t.is_closed else "Đang thực hiện"
            if t.project_id:
                sub = f"[{t.project_id.name}] · {sub}"
            if t.date_deadline:
                dl = t.date_deadline.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                sub += f" · Hạn {dl.strftime('%d/%m/%Y')}"
            items.append(
                {
                    "id": t.id,
                    "model": "project.task",
                    "title": t.name or "Công việc",
                    "subtitle": sub,
                    "url": f"/app/ca-nhan/cong-viec/{t.id}",
                }
            )
        return items

    @api.model
    def tp_share_record_to_channel(
        self, channel_id, target_model, target_id, note="", operation_token=""
    ):
        """Post a safe internal link to a Task or Calendar Event into a Discuss channel."""
        self.env["res.users"]._tp_require_internal_caller()
        if target_model not in ("project.task", "calendar.event"):
            raise ValidationError(self.env._("Loại liên kết chia sẻ không được hỗ trợ."))

        cid = int(channel_id or 0)
        tid = int(target_id or 0)
        channel = self.browse(cid).exists()
        if not channel or not channel.active:
            raise MissingError(self.env._("Hội thoại không tồn tại hoặc đã đóng."))
        channel._tp_assert_caller_can_read_channel()

        record = self.env[target_model].browse(tid).exists()
        if not record:
            raise MissingError(self.env._("Mục cần chia sẻ không tồn tại."))

        if target_model == "project.task":
            record._tp_assert_personal_task_access(mode="read")
            url = f"/app/ca-nhan/cong-viec/{record.id}"
            kind_label = "Công việc"
            link_label = f"Công việc #{record.id}"
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
            Markup('<p><strong>%s:</strong> <a href="%s">%s</a></p>')
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
            "tp_channel_scope": "general",
            "tp_manager_user_id": self.env.uid,
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
