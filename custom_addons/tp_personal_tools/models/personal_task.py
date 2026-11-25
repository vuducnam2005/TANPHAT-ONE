# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Backend for Việc cá nhân / Công việc của tôi in TANPHAT ONE.

Aggregates into a single unified workspace ("Công việc của tôi") WITHOUT copying records:
1. Self-created personal tasks (`project_id = False`, `tp_source_kind = 'self'`).
2. Project / plan tasks assigned to the user (`project_id != False`, `user_ids` or `kd_responsible_id`).
3. Tasks created from Meeting Minutes (`tp_source_kind = 'meeting'`).
4. Tasks linked from Approval Requests (`tp_source_kind = 'request'`).
5. Tasks converted from Discuss messages (`tp_source_kind = 'chat'`, `tp_source_message_id`).

Key guarantees:
- Per-user Kanban stage & manual sequence live strictly in `project.task.stage.personal`
  (`user_id = env.uid`), so dragging/reordering in "Công việc của tôi" NEVER mutates
  another user's board and NEVER alters `project.task.stage_id` or KH-KD workflow state.
- Distinguishes simple completion for self-created tasks vs two-step
  `reported_done` ("Người thực hiện báo xong") and `verified` ("Kết quả được xác nhận")
  for assigned / project tasks without overriding KH-KD `tp.task.command` governance.
"""

import base64
import html
import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from markupsafe import Markup

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Domain
from odoo.tools import SQL, html2plaintext, html_sanitize

MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024  # 25 MB server limit

PRIORITY_LABELS = {
    "0": "Bình thường",
    "1": "Trung bình",
    "2": "Cao",
    "3": "Khẩn cấp",
}

SOURCE_KIND_LABELS = {
    "self": "Tự tạo",
    "project": "Dự án",
    "meeting": "Cuộc họp",
    "request": "Yêu cầu",
    "chat": "Trao đổi",
}

EXEC_REPORT_LABELS = {
    "in_progress": "Đang thực hiện",
    "reported_done": "Đã báo xong (chờ xác nhận)",
    "verified": "Đã xác nhận kết quả",
}

DEFAULT_VI_STAGES = (
    (10, "Cần làm", False),
    (20, "Đang thực hiện", False),
    (30, "Chờ phản hồi", False),
    (40, "Hoàn thành", True),
)

_CHECKLIST_UL_RE = re.compile(
    r'<ul[^>]*class="[^"]*\bo_checklist\b[^"]*"[^>]*>(.*?)</ul>',
    re.IGNORECASE | re.DOTALL,
)
_CHECKLIST_LI_RE = re.compile(
    r"<li([^>]*)>(.*?)</li>",
    re.IGNORECASE | re.DOTALL,
)


def _user_tz(env):
    tz_name = env.user.tz or env.company.partner_id.tz or "Asia/Ho_Chi_Minh"
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


def _local_day_bounds_utc(env, target_date):
    tz = _user_tz(env)
    start_local = datetime.combine(target_date, time.min, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return (
        start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
        end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
    )


def _parse_description_and_checklist(raw_html):
    """Split native Odoo `description` HTML into clean text/HTML note and checklist items."""
    content = str(raw_html or "")
    items = []

    def _extract_ul(match):
        ul_inner = match.group(1) or ""
        for li_match in _CHECKLIST_LI_RE.finditer(ul_inner):
            attrs = li_match.group(1) or ""
            inner = li_match.group(2) or ""
            checked = "o_checked" in attrs
            text = html2plaintext(inner).strip()
            if text:
                items.append({"text": text, "checked": checked})
        return ""

    remaining_html = _CHECKLIST_UL_RE.sub(_extract_ul, content).strip()
    plain_note = html2plaintext(remaining_html).strip() if remaining_html else ""
    return plain_note, items


def _compose_description_html(note_text, checklist_items):
    """Compose sanitized HTML preserving both note paragraphs and native `<ul class="o_checklist">`."""
    parts = []
    clean_note = (note_text or "").strip()
    if clean_note:
        paragraphs = [
            f"<p>{html.escape(line) if line.strip() else '<br/>'}</p>"
            for line in clean_note.splitlines()
        ]
        parts.append("".join(paragraphs))

    valid_items = []
    for item in checklist_items or []:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        checked = bool(item.get("checked"))
        li_cls = ' class="o_checked"' if checked else ""
        valid_items.append(f"<li{li_cls}>{html.escape(text)}</li>")

    if valid_items:
        parts.append(f'<ul class="o_checklist">{"".join(valid_items)}</ul>')

    if not parts:
        return False
    return html_sanitize("".join(parts))


class ProjectTaskStagePersonalOrder(models.Model):
    _inherit = "project.task.stage.personal"

    tp_personal_sequence = fields.Integer(
        string="Thứ tự cá nhân",
        default=10,
        index=True,
        export_string_translation=False,
    )


class PersonalProjectTask(models.Model):
    _inherit = "project.task"

    tp_personal_sequence = fields.Integer(
        string="Thứ tự cá nhân",
        compute="_compute_tp_personal_sequence",
        export_string_translation=False,
    )
    tp_deliverable = fields.Char(
        string="Đầu ra cần đạt",
        export_string_translation=False,
    )
    tp_source_kind = fields.Selection(
        [
            ("self", "Việc tự tạo"),
            ("project", "Dự án / Kế hoạch"),
            ("meeting", "Từ cuộc họp"),
            ("request", "Từ yêu cầu"),
            ("chat", "Từ trao đổi"),
        ],
        string="Nguồn công việc",
        default="self",
        index=True,
        export_string_translation=False,
    )
    tp_source_message_id = fields.Many2one(
        "mail.message",
        string="Tin nhắn nguồn",
        ondelete="set null",
        index=True,
        export_string_translation=False,
    )
    tp_source_channel_id = fields.Many2one(
        "discuss.channel",
        string="Hội thoại nguồn",
        ondelete="set null",
        index=True,
        export_string_translation=False,
    )
    tp_source_request_id = fields.Integer(
        string="ID Yêu cầu nguồn",
        index=True,
        export_string_translation=False,
    )
    tp_assigner_user_id = fields.Many2one(
        "res.users",
        string="Người giao việc",
        ondelete="set null",
        index=True,
        export_string_translation=False,
    )
    tp_verifier_user_id = fields.Many2one(
        "res.users",
        string="Người xác nhận kết quả",
        ondelete="set null",
        index=True,
        export_string_translation=False,
    )
    tp_exec_report_state = fields.Selection(
        [
            ("in_progress", "Đang thực hiện"),
            ("reported_done", "Đã báo xong"),
            ("verified", "Đã xác nhận kết quả"),
        ],
        string="Trạng thái kết quả thực hiện",
        default="in_progress",
        index=True,
        export_string_translation=False,
    )
    tp_reported_result = fields.Text(
        string="Kết quả thực hiện / Đầu ra bàn giao",
        export_string_translation=False,
    )
    tp_reported_at = fields.Datetime(
        string="Thời điểm báo xong",
        readonly=True,
        export_string_translation=False,
    )
    tp_verified_at = fields.Datetime(
        string="Thời điểm xác nhận kết quả",
        readonly=True,
        export_string_translation=False,
    )
    tp_verified_by_id = fields.Many2one(
        "res.users",
        string="Người đã xác nhận",
        readonly=True,
        ondelete="set null",
        export_string_translation=False,
    )

    @api.depends_context("uid")
    @api.depends("personal_stage_id.tp_personal_sequence")
    def _compute_tp_personal_sequence(self):
        rels = self.env["project.task.stage.personal"].search(
            [("user_id", "=", self.env.uid), ("task_id", "in", self.ids)]
        )
        seq_by_task = {r.task_id.id: r.tp_personal_sequence for r in rels}
        for task in self:
            task.tp_personal_sequence = seq_by_task.get(task.id, task.sequence or 10)

    @api.model
    def _get_default_personal_stage_create_vals(self, user_id):
        """Initialize concise Vietnamese personal stages for new accounts without touching existing ones."""
        return [
            {"sequence": seq, "name": name, "user_id": user_id, "fold": fold}
            for seq, name, fold in DEFAULT_VI_STAGES
        ]

    @api.model
    def _tp_ensure_my_personal_stages(self):
        stages = self.env["project.task.type"].search(
            [("user_id", "=", self.env.uid), ("project_ids", "=", False)],
            order="sequence asc, id asc",
        )
        if not stages:
            vals_list = self._get_default_personal_stage_create_vals(self.env.uid)
            stages = (
                self.env["project.task.type"]
                .with_context(default_project_id=False, default_project_ids=False)
                .create(vals_list)
            )
        return stages

    @api.model
    def _tp_ensure_personal_stage_rels(self, tasks, stages):
        """Ensure each permitted task has a per-user `project.task.stage.personal` row for `env.uid`.

        Writes ONLY to `project.task.stage.personal` (never mutating `project.task.stage_id`
        or `project.task.state`), so even read-only KH-KD project tasks can be organized
        cleanly on the user's personal Kanban board.
        """
        if not tasks or not stages:
            return
        default_stage = stages[:1]
        Rel = self.env["project.task.stage.personal"].sudo()
        existing = Rel.search(
            [("user_id", "=", self.env.uid), ("task_id", "in", tasks.ids)]
        )
        have_tids = set(existing.mapped("task_id").ids)
        missing_vals = [
            {
                "user_id": self.env.uid,
                "task_id": t.id,
                "stage_id": default_stage.id,
                "tp_personal_sequence": t.sequence or 10,
            }
            for t in tasks
            if t.id not in have_tids
        ]
        if missing_vals:
            Rel.create(missing_vals)

    @api.model
    def _tp_my_work_domain(self, include_archived=False, source_filter=""):
        """Unified 'Công việc của tôi' scope: own tasks + permitted assigned project/meeting/request/chat tasks."""
        uid = self.env.uid
        non_project_cond = (
            Domain("project_id", "=", False)
            & Domain("parent_id", "=", False)
            & (
                Domain("user_ids", "in", [uid])
                | Domain("tp_assigner_user_id", "=", uid)
                | Domain("tp_verifier_user_id", "=", uid)
            )
        )
        proj_member_cond = (
            Domain("user_ids", "in", [uid])
            | Domain("tp_assigner_user_id", "=", uid)
            | Domain("tp_verifier_user_id", "=", uid)
        )
        if "kd_responsible_id" in self._fields:
            proj_member_cond |= Domain("kd_responsible_id", "=", uid)
        project_cond = Domain("project_id", "!=", False) & proj_member_cond

        dom = Domain("is_template", "=", False) & (non_project_cond | project_cond)
        if include_archived:
            dom &= Domain("active", "=", False)
        else:
            dom &= Domain("active", "=", True)

        sf = str(source_filter or "").strip()
        if sf == "self":
            dom &= Domain("project_id", "=", False) & Domain(
                "tp_source_kind", "in", [False, "self"]
            )
        elif sf == "project":
            dom &= Domain("project_id", "!=", False) | Domain("tp_source_kind", "=", "project")
        elif sf in ("meeting", "request", "chat"):
            dom &= Domain("tp_source_kind", "=", sf)
        return dom

    @api.model
    def _tp_base_personal_domain(self, include_archived=False):
        return self._tp_my_work_domain(include_archived=include_archived)

    def _tp_effective_source_kind(self):
        self.ensure_one()
        raw = self.tp_source_kind or "self"
        if raw in ("meeting", "request", "chat"):
            return raw
        if self.project_id:
            return "project"
        return raw

    def _tp_requires_verification(self):
        """Return True if task completion requires two-step `reported_done` -> `verified`."""
        self.ensure_one()
        if self.project_id:
            return True
        if self.tp_verifier_user_id and self.tp_verifier_user_id.id != self.create_uid.id:
            return True
        if (
            self.tp_assigner_user_id
            and self.tp_assigner_user_id.id not in (t.id for t in self.user_ids)
        ):
            return True
        if self._tp_effective_source_kind() in ("meeting", "request"):
            return True
        return False

    def _tp_is_user_involved(self, user=None):
        self.ensure_one()
        u = user or self.env.user
        if u in self.user_ids:
            return True
        if self.tp_assigner_user_id == u or self.tp_verifier_user_id == u:
            return True
        if "kd_responsible_id" in self._fields and self.kd_responsible_id == u:
            return True
        return False

    def _tp_can_verify_result(self):
        self.ensure_one()
        u = self.env.user
        if self.tp_verifier_user_id and self.tp_verifier_user_id == u:
            return True
        if not self.project_id and self.tp_assigner_user_id and self.tp_assigner_user_id == u:
            return True
        if self.project_id:
            proj = self.project_id
            if proj.user_id == u:
                return True
            if hasattr(proj, "_tp_head_allowed") and proj._tp_head_allowed():
                return True
        return False

    def _tp_can_edit_core_fields(self):
        """Return True only when caller can directly edit core fields (`name`, `deadline`, `user_ids`).

        Project tasks managed by KH-KD keep their WBS fields protected under `tp.task.command`.
        """
        self.ensure_one()
        if self.project_id:
            return False
        return bool(
            self.env.user in self.user_ids
            or self.tp_assigner_user_id == self.env.user
        )

    def _tp_assert_personal_task_access(self, mode="read"):
        """Enforce backend ACL + personal/assigned scope for 'Công việc của tôi'."""
        self.ensure_one()
        if not self.env.user._is_internal() or not self.env.user.active:
            raise AccessError(self.env._("Tài khoản không có quyền truy cập công việc."))
        if self.is_template:
            raise AccessError(self.env._("Bản ghi mẫu không thuộc phạm vi Công việc của tôi."))

        if mode == "read":
            self.check_access("read")
            allowed = (
                self._tp_is_user_involved()
                or self.env.user.partner_id in self.message_partner_ids
            )
            if not allowed:
                raise AccessError(
                    self.env._("Bạn không có quyền truy cập công việc riêng của người khác.")
                )
            return

        if mode == "personal_board":
            # Reordering on caller's personal Kanban board requires read + involvement
            self.check_access("read")
            if not self._tp_is_user_involved():
                raise AccessError(
                    self.env._("Bạn chỉ có thể sắp xếp các công việc được giao cho mình.")
                )
            return

        if self.project_id:
            raise AccessError(
                self.env._(
                    "Công việc thuộc dự án được quản lý theo phân quyền WBS của dự án; không sửa/xóa trực tiếp như việc tự tạo."
                )
            )
        self.check_access(mode)
        if not self._tp_can_edit_core_fields():
            raise AccessError(
                self.env._("Bạn không có quyền chỉnh sửa công việc riêng của người khác.")
            )

    def _tp_deadline_info(self, deadline_dt, is_closed, today_local):
        if is_closed:
            if not deadline_dt:
                return {"status": "done", "label": "Hoàn thành", "formatted": "", "date_only": "", "iso_local": ""}
            local_dt = deadline_dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(_user_tz(self.env))
            return {
                "status": "done",
                "label": "Hoàn thành",
                "formatted": local_dt.strftime("%d/%m/%Y %H:%M"),
                "date_only": local_dt.strftime("%d/%m/%Y"),
                "iso_local": local_dt.strftime("%Y-%m-%dT%H:%M"),
            }
        if not deadline_dt:
            return {"status": "none", "label": "", "formatted": "", "date_only": "", "iso_local": ""}
        tz = _user_tz(self.env)
        now_local = datetime.now(tz)
        local_dt = deadline_dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
        local_date = local_dt.date()
        time_str = local_dt.strftime("%H:%M")
        date_str = local_dt.strftime("%d/%m/%Y")
        has_meaningful_time = not (local_dt.hour in (0, 23) and local_dt.minute in (0, 59))
        short_str = f"{local_dt.strftime('%d/%m')} · {time_str}" if has_meaningful_time else local_dt.strftime("%d/%m/%Y")

        if local_dt < now_local and local_date < today_local:
            return {
                "status": "overdue",
                "label": f"Quá hạn · {short_str}",
                "formatted": f"{date_str} {time_str}".strip(),
                "date_only": date_str,
                "iso_local": local_dt.strftime("%Y-%m-%dT%H:%M"),
            }
        if local_date == today_local:
            is_past_time = has_meaningful_time and local_dt < now_local
            return {
                "status": "overdue" if is_past_time else "today",
                "label": f"{'Quá hạn hôm nay' if is_past_time else 'Hôm nay'}"
                + (f" · {time_str}" if has_meaningful_time else ""),
                "formatted": f"{date_str} {time_str}".strip(),
                "date_only": date_str,
                "iso_local": local_dt.strftime("%Y-%m-%dT%H:%M"),
            }
        return {
            "status": "upcoming",
            "label": short_str,
            "formatted": f"{date_str} {time_str}".strip(),
            "date_only": date_str,
            "iso_local": local_dt.strftime("%Y-%m-%dT%H:%M"),
        }

    def _tp_serialize_tasks(self, stages):
        if not self:
            return []
        tz = _user_tz(self.env)
        today_local = datetime.now(tz).date()
        default_stage = stages[:1]

        rels = self.env["project.task.stage.personal"].sudo().search(
            [("user_id", "=", self.env.uid), ("task_id", "in", self.ids)]
        )
        rel_by_task = {r.task_id.id: r for r in rels}

        att_groups = self.env["ir.attachment"]._read_group(
            [("res_model", "=", "project.task"), ("res_id", "in", self.ids)],
            ["res_id"],
            ["__count"],
        )
        att_counts = {res_id: cnt for res_id, cnt in att_groups}

        odoobot_id = self.env["ir.model.data"]._xmlid_to_res_id("base.partner_root") or 0
        msg_domain = [
            ("model", "=", "project.task"),
            ("res_id", "in", self.ids),
            ("message_type", "in", ["comment", "email"]),
        ]
        if odoobot_id:
            msg_domain.append(("author_id", "!=", odoobot_id))
        msg_groups = self.env["mail.message"]._read_group(
            msg_domain,
            ["res_id"],
            ["__count"],
        )
        msg_counts = {res_id: cnt for res_id, cnt in msg_groups}

        cal_groups = self.env["calendar.event"]._read_group(
            [("res_model", "=", "project.task"), ("res_id", "in", self.ids), ("active", "=", True)],
            ["res_id"],
            ["__count"],
        )
        cal_counts = {res_id: cnt for res_id, cnt in cal_groups}

        all_users = (
            self.mapped("user_ids")
            | self.mapped("tp_assigner_user_id")
            | self.mapped("tp_verifier_user_id")
        )
        colleague_map = {
            c["user_id"]: c for c in self.env["res.users"]._tp_format_colleagues(all_users)
        }

        rows = []
        for task in self:
            rel = rel_by_task.get(task.id)
            stage = rel.stage_id if (rel and rel.stage_id) else default_stage
            personal_seq = rel.tp_personal_sequence if rel else (task.sequence or 10)
            req_verify = task._tp_requires_verification()
            exec_state = task.tp_exec_report_state or (
                "verified" if task.state == "1_done" else "in_progress"
            )
            if task.state == "1_done" and exec_state == "in_progress":
                exec_state = "verified"

            is_done = bool(task.state == "1_done" or exec_state == "verified")
            is_closed = bool(task.is_closed or exec_state == "verified")
            dl = task._tp_deadline_info(task.date_deadline, is_closed, today_local)
            note_preview, checklist = _parse_description_and_checklist(task.description)
            assignees = [
                colleague_map[u.id]
                for u in task.user_ids
                if u.id in colleague_map
            ]
            other_assignees = [a for a in assignees if a["user_id"] != self.env.uid]
            eff_source = task._tp_effective_source_kind()
            kd_deliv = getattr(task, "kd_deliverable", "") or ""
            deliverable = task.tp_deliverable or kd_deliv or ""

            project_info = None
            if task.project_id:
                project_info = {
                    "id": task.project_id.id,
                    "name": task.project_id.name or f"Dự án #{task.project_id.id}",
                    "code": getattr(task.project_id, "tp_code", "") or "",
                    "stage_name": task.stage_id.name if task.stage_id else "",
                }

            assigner_info = (
                colleague_map.get(task.tp_assigner_user_id.id)
                if task.tp_assigner_user_id
                else None
            )
            verifier_info = (
                colleague_map.get(task.tp_verifier_user_id.id)
                if task.tp_verifier_user_id
                else None
            )

            rows.append(
                {
                    "id": task.id,
                    "name": task.name or "",
                    "active": bool(task.active),
                    "state": task.state,
                    "is_done": is_done,
                    "is_closed": is_closed,
                    "priority": task.priority or "0",
                    "priority_label": PRIORITY_LABELS.get(task.priority or "0", "Bình thường"),
                    "stage_id": stage.id if stage else False,
                    "stage_name": stage.name if stage else "Chưa phân loại",
                    "personal_sequence": personal_seq,
                    "deadline": dl,
                    "source_kind": eff_source,
                    "source_label": SOURCE_KIND_LABELS.get(eff_source, "Tự tạo"),
                    "project": project_info,
                    "deliverable": deliverable,
                    "assigner": assigner_info,
                    "verifier": verifier_info,
                    "requires_verification": req_verify,
                    "exec_report_state": exec_state,
                    "exec_report_label": EXEC_REPORT_LABELS.get(exec_state, "Đang thực hiện"),
                    "reported_result": task.tp_reported_result or "",
                    "can_edit_core": task._tp_can_edit_core_fields(),
                    "can_report_done": bool(
                        self.env.user in task.user_ids
                        or (
                            "kd_responsible_id" in self._fields
                            and task.kd_responsible_id == self.env.user
                        )
                    ),
                    "can_verify": task._tp_can_verify_result(),
                    "tags": [
                        {"id": tg.id, "name": tg.name, "color": tg.color or 0}
                        for tg in task.tag_ids
                    ],
                    "assignees": assignees,
                    "other_assignees": other_assignees,
                    "is_shared": len(assignees) > 1 or bool(project_info),
                    "attachment_count": att_counts.get(task.id, 0),
                    "comment_count": msg_counts.get(task.id, 0),
                    "calendar_count": cal_counts.get(task.id, 0),
                    "checklist_total": len(checklist),
                    "checklist_done": sum(1 for c in checklist if c["checked"]),
                    "note_preview": note_preview[:140] if note_preview else "",
                    "write_date": str(task.write_date or ""),
                }
            )
        return rows

    @api.model
    def _tp_parse_local_datetime_input(self, value, end_of_day=False):
        """Parse `YYYY-MM-DDTHH:MM` or `YYYY-MM-DD` in user timezone into naive UTC datetime."""
        raw = str(value or "").strip()
        if not raw:
            return False
        tz = _user_tz(self.env)
        try:
            if "T" in raw:
                dt_local = datetime.strptime(raw[:16], "%Y-%m-%dT%H:%M").replace(tzinfo=tz)
            elif len(raw) >= 16 and " " in raw:
                dt_local = datetime.strptime(raw[:16], "%Y-%m-%d %H:%M").replace(tzinfo=tz)
            else:
                d = datetime.strptime(raw[:10], "%Y-%m-%d").date()
                t = time(23, 59, 59) if end_of_day else time(17, 0, 0)
                dt_local = datetime.combine(d, t, tzinfo=tz)
        except ValueError as exc:
            raise ValidationError(
                self.env._("Định dạng ngày/giờ hạn hoàn thành chưa hợp lệ.")
            ) from exc
        return dt_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    @api.model
    def tp_get_personal_workspace(self, params=None):
        """Load complete workspace state for Công việc của tôi (summary, stages, filtered tasks)."""
        self.env["res.users"]._tp_require_internal_caller()
        params = dict(params or {})
        stages = self._tp_ensure_my_personal_stages()

        tz = _user_tz(self.env)
        now_local = datetime.now(tz)
        today_local = now_local.date()
        today_start_utc, tomorrow_start_utc = _local_day_bounds_utc(self.env, today_local)
        now_utc = fields.Datetime.now()

        source_filter = str(params.get("source_kind") or "").strip()

        base_open_tasks = self.with_context(active_test=True).search(
            self._tp_my_work_domain(include_archived=False), limit=1000
        )
        if base_open_tasks:
            self._tp_ensure_personal_stage_rels(base_open_tasks, stages)

        active_base = self._tp_my_work_domain(include_archived=False, source_filter=source_filter)
        closed_cond = Domain("is_closed", "=", True) | Domain("tp_exec_report_state", "=", "verified")
        open_cond = Domain("is_closed", "=", False) & Domain(
            "tp_exec_report_state", "in", [False, "in_progress", "reported_done"]
        )
        open_dom = active_base & open_cond

        today_stage_ids = [
            s.id
            for s in stages
            if (s.name or "").strip().lower() in ("hôm nay", "hom nay", "today")
        ]
        today_cond = Domain("date_deadline", ">=", today_start_utc) & Domain(
            "date_deadline", "<", tomorrow_start_utc
        )
        if today_stage_ids:
            today_cond |= Domain("personal_stage_type_id", "in", today_stage_ids)

        overdue_cond = Domain("date_deadline", "!=", False) & Domain("date_deadline", "<", now_utc)
        upcoming_cond = Domain("date_deadline", ">=", tomorrow_start_utc)

        today_count = self.search_count(open_dom & today_cond)
        overdue_count = self.search_count(open_dom & overdue_cond)
        upcoming_count = self.search_count(open_dom & upcoming_cond)
        all_open_count = self.search_count(open_dom)
        done_total_count = self.search_count(active_base & closed_cond)
        archived_count = self.with_context(active_test=False).search_count(
            self._tp_my_work_domain(include_archived=True, source_filter=source_filter)
        )

        # Count by source for quick source filter pills
        all_active_unfiltered = self._tp_my_work_domain(include_archived=False) & open_cond
        source_counts = {
            "all": self.search_count(all_active_unfiltered),
            "self": self.search_count(
                self._tp_my_work_domain(include_archived=False, source_filter="self") & open_cond
            ),
            "project": self.search_count(
                self._tp_my_work_domain(include_archived=False, source_filter="project") & open_cond
            ),
            "meeting": self.search_count(
                self._tp_my_work_domain(include_archived=False, source_filter="meeting") & open_cond
            ),
            "request": self.search_count(
                self._tp_my_work_domain(include_archived=False, source_filter="request") & open_cond
            ),
            "chat": self.search_count(
                self._tp_my_work_domain(include_archived=False, source_filter="chat") & open_cond
            ),
        }

        bucket = str(params.get("bucket") or "all").strip()
        is_archived_bucket = bucket == "archived"
        ctx_self = self.with_context(active_test=not is_archived_bucket)
        domain = self._tp_my_work_domain(
            include_archived=is_archived_bucket, source_filter=source_filter
        )

        if bucket == "today":
            domain &= open_cond & today_cond
        elif bucket == "upcoming":
            domain &= open_cond & upcoming_cond
        elif bucket == "overdue":
            domain &= open_cond & overdue_cond
        elif bucket == "done":
            domain &= closed_cond
        elif bucket == "all":
            completion_filter = str(params.get("completion") or "").strip()
            if not completion_filter:
                domain &= open_cond

        q = str(params.get("q") or "").strip()
        if q:
            domain &= (
                Domain("name", "ilike", q)
                | Domain("description", "ilike", q)
                | Domain("tp_deliverable", "ilike", q)
                | Domain("tag_ids.name", "ilike", q)
                | Domain("project_id.name", "ilike", q)
            )

        date_from = str(params.get("date_from") or "").strip()
        date_to = str(params.get("date_to") or "").strip()
        if date_from and date_to and date_from > date_to:
            raise ValidationError(
                self.env._("Ngày bắt đầu lọc hạn hoàn thành không được lớn hơn ngày kết thúc.")
            )
        if date_from:
            d_from = datetime.strptime(date_from[:10], "%Y-%m-%d").date()
            from_utc, _ = _local_day_bounds_utc(self.env, d_from)
            domain &= Domain("date_deadline", ">=", from_utc)
        if date_to:
            d_to = datetime.strptime(date_to[:10], "%Y-%m-%d").date()
            _, to_exclusive_utc = _local_day_bounds_utc(self.env, d_to)
            domain &= Domain("date_deadline", "<", to_exclusive_utc)

        priority = str(params.get("priority") or "").strip()
        if priority in ("0", "1", "2", "3"):
            domain &= Domain("priority", "=", priority)

        tag_ids = [int(t) for t in (params.get("tag_ids") or []) if str(t).isdigit()]
        if tag_ids:
            domain &= Domain("tag_ids", "in", tag_ids)

        stage_id = int(params.get("stage_id") or 0)
        if stage_id:
            rel_tids = (
                self.env["project.task.stage.personal"]
                .sudo()
                .search([("user_id", "=", self.env.uid), ("stage_id", "=", stage_id)])
                .mapped("task_id")
                .ids
            )
            domain &= Domain("id", "in", rel_tids)

        completion = str(params.get("completion") or "").strip()
        if completion == "open":
            domain &= open_cond
        elif completion == "reported_done":
            domain &= Domain("tp_exec_report_state", "=", "reported_done")
        elif completion == "done":
            domain &= closed_cond

        assignee_id = int(params.get("assignee_id") or 0)
        if assignee_id:
            domain &= Domain("user_ids", "in", [assignee_id])

        done_in_scope_dom = active_base & closed_cond
        if date_from:
            d_from = datetime.strptime(date_from[:10], "%Y-%m-%d").date()
            from_utc, _ = _local_day_bounds_utc(self.env, d_from)
            done_in_scope_dom &= Domain("date_deadline", ">=", from_utc)
        if date_to:
            d_to = datetime.strptime(date_to[:10], "%Y-%m-%d").date()
            _, to_exclusive_utc = _local_day_bounds_utc(self.env, d_to)
            done_in_scope_dom &= Domain("date_deadline", "<", to_exclusive_utc)
        if q:
            done_in_scope_dom &= (
                Domain("name", "ilike", q)
                | Domain("description", "ilike", q)
                | Domain("tag_ids.name", "ilike", q)
            )
        done_in_range_count = self.search_count(done_in_scope_dom)

        view_mode = str(params.get("view_mode") or "board").strip()
        sort_by = str(params.get("sort_by") or "manual").strip()
        page = max(1, int(params.get("page") or 1))
        page_size = int(params.get("page_size") or 100)
        if page_size not in (10, 20, 50, 100):
            page_size = 100

        matching_tasks = ctx_self.search(domain, order="id desc", limit=1000)
        if matching_tasks and not is_archived_bucket:
            self._tp_ensure_personal_stage_rels(matching_tasks, stages)
        serialized = matching_tasks._tp_serialize_tasks(stages)

        if sort_by == "deadline":
            serialized.sort(
                key=lambda r: (
                    1 if r["is_closed"] else 0,
                    0 if r["deadline"]["iso_local"] else 1,
                    r["deadline"]["iso_local"] or "9999-99-99",
                    -int(r["priority"]),
                    r["personal_sequence"],
                    -r["id"],
                )
            )
        elif sort_by == "priority":
            serialized.sort(
                key=lambda r: (
                    1 if r["is_closed"] else 0,
                    -int(r["priority"]),
                    0 if r["deadline"]["iso_local"] else 1,
                    r["deadline"]["iso_local"] or "9999-99-99",
                    r["personal_sequence"],
                    -r["id"],
                )
            )
        elif sort_by == "recent":
            serialized.sort(key=lambda r: (r["write_date"], r["id"]), reverse=True)
        else:
            stage_order_map = {s.id: idx for idx, s in enumerate(stages)}
            serialized.sort(
                key=lambda r: (
                    stage_order_map.get(r["stage_id"], 999),
                    r["personal_sequence"],
                    -r["id"],
                )
            )

        total_count = len(serialized)
        if view_mode == "list":
            offset = (page - 1) * page_size
            if offset >= total_count and total_count > 0:
                page = max(1, (total_count - 1) // page_size + 1)
                offset = (page - 1) * page_size
            paged_tasks = serialized[offset : offset + page_size]
        else:
            paged_tasks = serialized

        tags = self.env["project.tags"].search(
            [("project_ids", "=", False)], order="name asc", limit=100
        )

        return {
            "summary": {
                "today": today_count,
                "overdue": overdue_count,
                "upcoming": upcoming_count,
                "all_open": all_open_count,
                "done": done_total_count,
                "done_in_range": done_in_range_count,
                "archived": archived_count,
            },
            "source_counts": source_counts,
            "stages": [
                {
                    "id": s.id,
                    "name": s.name,
                    "sequence": s.sequence,
                    "fold": bool(s.fold),
                }
                for s in stages
            ],
            "tags": [{"id": tg.id, "name": tg.name, "color": tg.color or 0} for tg in tags],
            "tasks": paged_tasks,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "manual_sort_enabled": sort_by == "manual",
            "today_iso": today_local.isoformat(),
        }

    @api.model
    def tp_get_personal_task_detail(self, task_id):
        """Return full drawer detail for one task in 'Công việc của tôi' after strict ACL check."""
        self.env["res.users"]._tp_require_internal_caller()
        tid = int(task_id or 0)
        task = self.with_context(active_test=False).browse(tid).exists()
        if not task:
            raise MissingError(self.env._("Công việc không tồn tại hoặc đã bị xóa."))
        task._tp_assert_personal_task_access(mode="read")

        stages = self._tp_ensure_my_personal_stages()
        if task.active and task._tp_is_user_involved():
            self._tp_ensure_personal_stage_rels(task, stages)
        card_list = task._tp_serialize_tasks(stages)
        card = card_list[0]
        note_text, checklist = _parse_description_and_checklist(task.description)

        attachments = self.env["ir.attachment"].search(
            [("res_model", "=", "project.task"), ("res_id", "=", task.id)],
            order="id desc",
        )
        can_edit_core = task._tp_can_edit_core_fields()
        att_items = [
            {
                "id": a.id,
                "name": a.name or "Tệp đính kèm",
                "mimetype": a.mimetype or "application/octet-stream",
                "file_size": a.file_size or 0,
                "is_image": bool((a.mimetype or "").startswith("image/")),
                "download_url": f"/web/content/{a.id}?download=true",
                "preview_url": f"/web/image/{a.id}"
                if (a.mimetype or "").startswith("image/")
                else f"/web/content/{a.id}",
                "can_delete": bool(task.active and (can_edit_core or a.create_uid == self.env.user)),
            }
            for a in attachments
        ]

        events = self.env["calendar.event"].search(
            [
                ("res_model", "=", "project.task"),
                ("res_id", "=", task.id),
                ("active", "=", True),
            ],
            order="start asc",
            limit=20,
        )
        tz = _user_tz(self.env)
        linked_events = []
        for ev in events:
            if not ev.has_access("read") or ev._check_private_event_conditions():
                continue
            if ev.allday:
                when_label = (
                    ev.start_date.strftime("%d/%m/%Y") + " (Cả ngày)" if ev.start_date else "Cả ngày"
                )
            else:
                st = ev.start.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz) if ev.start else None
                en = ev.stop.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz) if ev.stop else None
                when_label = (
                    f"{st.strftime('%d/%m/%Y %H:%M')} – {en.strftime('%H:%M')}"
                    if (st and en)
                    else ""
                )
            linked_events.append(
                {
                    "id": ev.id,
                    "name": ev.name or "Lịch hẹn",
                    "when_label": when_label,
                    "url": f"/app/ca-nhan/lich-lam-viec/{ev.id}",
                }
            )

        source_message_info = None
        if task.tp_source_message_id:
            msg_su = task.tp_source_message_id.sudo()
            chan = task.tp_source_channel_id
            can_see_chan = bool(chan and chan.exists() and chan.has_access("read"))
            source_message_info = {
                "message_id": msg_su.id,
                "channel_id": chan.id if can_see_chan else 0,
                "channel_name": (chan.display_name or chan.name) if can_see_chan else "Hội thoại nội bộ",
                "channel_url": f"/app/ca-nhan/trao-doi/{chan.id}" if can_see_chan else "",
                "author_name": msg_su.author_id.name or "",
            }

        odoobot_id = self.env["ir.model.data"]._xmlid_to_res_id("base.partner_root") or 0
        msg_dom = [
            ("model", "=", "project.task"),
            ("res_id", "=", task.id),
            ("message_type", "in", ["comment", "notification"]),
        ]
        if odoobot_id:
            msg_dom.append(("author_id", "!=", odoobot_id))
        messages = self.env["mail.message"].search(msg_dom, order="date desc, id desc", limit=40)
        msg_items = []
        for m in messages:
            plain = html2plaintext(m.body or "").strip()
            if not plain and not m.attachment_ids:
                continue
            dt_local = (
                m.date.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz).strftime("%d/%m/%Y %H:%M")
                if m.date
                else ""
            )
            author = m.author_id
            msg_items.append(
                {
                    "id": m.id,
                    "author_name": author.name or "Hệ thống",
                    "author_avatar": (
                        f"/web/image/res.partner/{author.id}/avatar_128" if author else ""
                    ),
                    "date_label": dt_local,
                    "body_text": plain,
                    "is_note": m.message_type == "notification",
                }
            )

        return {
            **card,
            "note_text": note_text,
            "checklist": checklist,
            "attachments": att_items,
            "linked_events": linked_events,
            "source_message_info": source_message_info,
            "messages": msg_items,
            "can_write": can_edit_core,
            "can_upload_evidence": bool(
                task.active and (can_edit_core or card["can_report_done"] or card["can_verify"])
            ),
            "stages": [
                {"id": s.id, "name": s.name, "fold": bool(s.fold)}
                for s in stages
            ],
        }

    @api.model
    def tp_create_personal_task(self, vals, operation_token=""):
        """Create a personal/assigned task (`idempotent` via `operation_token`)."""
        self.env["res.users"]._tp_require_internal_caller()
        vals = dict(vals or {})
        name = str(vals.get("name") or "").strip()
        if not name:
            raise ValidationError(self.env._("Vui lòng nhập tiêu đề công việc."))

        stages = self._tp_ensure_my_personal_stages()
        requested_stage_id = int(vals.get("stage_id") or 0)
        stage = stages.filtered(lambda s: s.id == requested_stage_id)[:1] or stages[:1]

        extra_user_ids = [
            int(u)
            for u in (vals.get("user_ids") or [])
            if str(u).isdigit() and int(u) != self.env.uid
        ]
        valid_extra_users = self.env["res.users"].sudo().search(
            [
                ("id", "in", extra_user_ids),
                ("active", "=", True),
                ("share", "=", False),
            ]
        )
        all_user_ids = [self.env.uid] + [u.id for u in valid_extra_users if u.id != self.env.uid]

        deadline_utc = self._tp_parse_local_datetime_input(vals.get("deadline_iso"))
        priority = str(vals.get("priority") or "0")
        if priority not in ("0", "1", "2", "3"):
            priority = "0"
        tag_ids = [int(t) for t in (vals.get("tag_ids") or []) if str(t).isdigit()]
        deliverable = str(vals.get("deliverable") or "").strip()
        description_html = _compose_description_html(
            vals.get("note_text", ""), vals.get("checklist", [])
        )

        op_payload = {
            "name": name,
            "stage_id": stage.id,
            "users": sorted(all_user_ids),
            "deadline": str(deadline_utc or ""),
            "priority": priority,
            "tags": sorted(tag_ids),
            "deliverable": deliverable,
        }
        op_log = self.env["tp.personal.operation.log"]
        existing, clean_token, fp = op_log.acquire_or_replay(
            "create_personal_task", operation_token, op_payload
        )
        if existing:
            return existing._tp_serialize_tasks(stages)[0]

        min_seq_rel = self.env["project.task.stage.personal"].sudo().search(
            [("user_id", "=", self.env.uid), ("stage_id", "=", stage.id)],
            order="tp_personal_sequence asc, id asc",
            limit=1,
        )
        next_seq = (min_seq_rel.tp_personal_sequence - 10) if min_seq_rel else 10

        is_done = bool(vals.get("is_done"))
        create_vals = {
            "name": name,
            "project_id": False,
            "parent_id": False,
            "is_template": False,
            "user_ids": [Command.set(all_user_ids)],
            "priority": priority,
            "date_deadline": deadline_utc,
            "tp_deliverable": deliverable or False,
            "tp_source_kind": "self",
            "tp_assigner_user_id": self.env.uid,
            "tp_exec_report_state": "verified" if is_done else "in_progress",
            "description": description_html,
            "state": "1_done" if is_done else "01_in_progress",
        }
        if vals.get("verifier_user_id"):
            v_uid = int(vals["verifier_user_id"])
            v_user = self.env["res.users"].sudo().browse(v_uid).exists()
            if v_user and v_user.active and not v_user.share:
                create_vals["tp_verifier_user_id"] = v_user.id
        if tag_ids:
            create_vals["tag_ids"] = [Command.set(tag_ids)]

        task = (
            self.with_context(
                default_project_id=False,
                default_parent_id=False,
                mail_create_nosubscribe=False,
            )
            .create(create_vals)
        )
        self._tp_ensure_personal_stage_rels(task, stages)
        rel = self.env["project.task.stage.personal"].sudo().search(
            [("user_id", "=", self.env.uid), ("task_id", "=", task.id)],
            limit=1,
        )
        if rel:
            rel.write({"stage_id": stage.id, "tp_personal_sequence": next_seq})

        op_log.record_success("create_personal_task", clean_token, fp, task)
        return task._tp_serialize_tasks(stages)[0]

    @api.model
    def tp_create_personal_tag(self, name, color=1):
        """Create a personal tag (`project_ids = False`) if none with same name exists."""
        self.env["res.users"]._tp_require_internal_caller()
        clean = str(name or "").strip()
        if not clean:
            raise ValidationError(self.env._("Vui lòng nhập tên nhãn."))
        existing = self.env["project.tags"].search(
            [("name", "=ilike", clean), ("project_ids", "=", False)], limit=1
        )
        if existing:
            return {"id": existing.id, "name": existing.name, "color": existing.color or 1}
        tag = self.env["project.tags"].create(
            {"name": clean, "color": max(1, min(int(color or 1), 11))}
        )
        return {"id": tag.id, "name": tag.name, "color": tag.color or 1}

    @api.model
    def tp_save_personal_task(self, task_id, vals):
        """Update fields of an existing non-project personal task with full access validation."""
        self.env["res.users"]._tp_require_internal_caller()
        task = self.with_context(active_test=False).browse(int(task_id or 0)).exists()
        if not task:
            raise MissingError(self.env._("Công việc không tồn tại hoặc đã bị xóa."))

        vals = dict(vals or {})
        # Allow moving personal stage even on project tasks without mutating `project.task`
        if task.project_id and set(vals.keys()) <= {"stage_id"}:
            task._tp_assert_personal_task_access(mode="personal_board")
            if vals.get("stage_id"):
                self.tp_move_personal_task(task.id, int(vals["stage_id"]), [task.id])
            return self.tp_get_personal_task_detail(task.id)

        task._tp_assert_personal_task_access(mode="write")
        write_vals = {}

        if "name" in vals:
            name = str(vals.get("name") or "").strip()
            if not name:
                raise ValidationError(self.env._("Vui lòng nhập tiêu đề công việc."))
            write_vals["name"] = name

        if "deliverable" in vals:
            write_vals["tp_deliverable"] = str(vals.get("deliverable") or "").strip() or False

        if "reported_result" in vals:
            write_vals["tp_reported_result"] = str(vals.get("reported_result") or "").strip() or False

        if "priority" in vals:
            prio = str(vals.get("priority") or "0")
            if prio not in ("0", "1", "2", "3"):
                raise ValidationError(self.env._("Mức ưu tiên không hợp lệ."))
            write_vals["priority"] = prio

        if "is_done" in vals and not task._tp_requires_verification():
            done_flag = bool(vals.get("is_done"))
            write_vals["state"] = "1_done" if done_flag else "01_in_progress"
            write_vals["tp_exec_report_state"] = "verified" if done_flag else "in_progress"

        if "deadline_iso" in vals:
            write_vals["date_deadline"] = self._tp_parse_local_datetime_input(
                vals.get("deadline_iso")
            )

        if "tag_ids" in vals:
            tag_ids = [int(t) for t in (vals.get("tag_ids") or []) if str(t).isdigit()]
            write_vals["tag_ids"] = [Command.set(tag_ids)]

        if "user_ids" in vals:
            supplied_uids = [int(u) for u in (vals.get("user_ids") or []) if str(u).isdigit()]
            if self.env.uid not in supplied_uids and task.tp_assigner_user_id != self.env.user:
                supplied_uids.insert(0, self.env.uid)
            valid_users = self.env["res.users"].sudo().search(
                [("id", "in", supplied_uids), ("active", "=", True), ("share", "=", False)]
            )
            if not valid_users:
                raise ValidationError(self.env._("Công việc phải có ít nhất một người phụ trách."))
            write_vals["user_ids"] = [Command.set(valid_users.ids)]

        if "note_text" in vals or "checklist" in vals:
            cur_note, cur_checks = _parse_description_and_checklist(task.description)
            new_note = vals.get("note_text", cur_note)
            new_checks = vals.get("checklist", cur_checks)
            write_vals["description"] = _compose_description_html(new_note, new_checks)

        if write_vals:
            task.write(write_vals)

        stages = self._tp_ensure_my_personal_stages()
        self._tp_ensure_personal_stage_rels(task, stages)

        if "stage_id" in vals and vals.get("stage_id"):
            stage_id = int(vals["stage_id"])
            stage = self.env["project.task.type"].search(
                [("id", "=", stage_id), ("user_id", "=", self.env.uid)], limit=1
            )
            if not stage:
                raise ValidationError(self.env._("Giai đoạn cá nhân không hợp lệ."))
            rel = self.env["project.task.stage.personal"].sudo().search(
                [("user_id", "=", self.env.uid), ("task_id", "=", task.id)], limit=1
            )
            if rel and rel.stage_id.id != stage.id:
                rel.write({"stage_id": stage.id})

        return self.tp_get_personal_task_detail(task.id)

    @api.model
    def tp_report_or_verify_task(self, task_id, action, result_text="", operation_token=""):
        """Two-step execution reporting (`report_done` vs `verify` vs `reopen`).

        - On project/KH-KD tasks, `report_done` and `verify` update ONLY the execution-result
          tracking fields (`tp_exec_report_state`, `tp_reported_result`, `tp_verified_*`) and
          post a chatter trace WITHOUT overriding `project.task.state` or `stage_id` controlled
          by KH-KD WBS governance!
        - On non-project assigned tasks, `verify` marks `state = '1_done'` and `reopen`
          restores `state = '01_in_progress'`.
        """
        self.env["res.users"]._tp_require_internal_caller()
        task = self.with_context(active_test=False).browse(int(task_id or 0)).exists()
        if not task:
            raise MissingError(self.env._("Công việc không tồn tại."))
        task._tp_assert_personal_task_access(mode="read")

        if action not in ("report_done", "verify", "reopen"):
            raise ValidationError(self.env._("Thao tác xác nhận kết quả không hợp lệ."))

        clean_result = str(result_text or "").strip()
        self.env.flush_all()
        self.env.cr.execute(SQL("SELECT id FROM project_task WHERE id = %s FOR UPDATE", task.id))
        task.invalidate_recordset()

        now_utc = fields.Datetime.now()
        updates = {}
        log_msg = ""

        if action == "report_done":
            can_report = bool(
                self.env.user in task.user_ids
                or ("kd_responsible_id" in self._fields and task.kd_responsible_id == self.env.user)
            )
            if not can_report:
                raise AccessError(
                    self.env._("Chỉ người được giao thực hiện mới có quyền báo hoàn thành công việc này.")
                )
            updates["tp_exec_report_state"] = "reported_done"
            updates["tp_reported_at"] = now_utc
            if clean_result:
                updates["tp_reported_result"] = clean_result
            log_msg = "đã báo hoàn thành công việc" + (f": {clean_result}" if clean_result else ".")

        elif action == "verify":
            if not task._tp_can_verify_result():
                raise AccessError(
                    self.env._("Chỉ người giao việc, người xác nhận hoặc phụ trách dự án mới được xác nhận kết quả.")
                )
            updates["tp_exec_report_state"] = "verified"
            updates["tp_verified_at"] = now_utc
            updates["tp_verified_by_id"] = self.env.uid
            if clean_result:
                updates["tp_reported_result"] = clean_result
            if not task.project_id:
                updates["state"] = "1_done"
            log_msg = "đã xác nhận kết quả công việc" + (f": {clean_result}" if clean_result else ".")

        elif action == "reopen":
            if not (task._tp_can_verify_result() or self.env.user in task.user_ids):
                raise AccessError(self.env._("Bạn không có quyền mở lại trạng thái kết quả này."))
            updates["tp_exec_report_state"] = "in_progress"
            updates["tp_verified_at"] = False
            updates["tp_verified_by_id"] = False
            if not task.project_id:
                updates["state"] = "01_in_progress"
            log_msg = "đã chuyển công việc về trạng thái đang thực hiện" + (
                f" ({clean_result})" if clean_result else "."
            )

        # Write via sudo ONLY after strict ACL + row lock above so `group_scoped_staff`
        # executors can submit their execution report without opening full write ACL on `project.task`.
        task.sudo().with_context(tracking_disable=True, mail_create_nosubscribe=True).write(updates)
        if log_msg:
            safe_note = Markup("<p><strong>%s</strong> %s</p>") % (
                html.escape(self.env.user.name or ""),
                html.escape(log_msg),
            )
            task.sudo().message_post(
                body=safe_note,
                author_id=self.env.user.partner_id.id,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )

        return self.tp_get_personal_task_detail(task.id)

    @api.model
    def tp_toggle_personal_task_done(self, task_id, is_done):
        """Toggle completion state for self-created tasks, or toggle `reported_done` on assigned/project tasks."""
        self.env["res.users"]._tp_require_internal_caller()
        task = self.with_context(active_test=False).browse(int(task_id or 0)).exists()
        if not task:
            raise MissingError(self.env._("Công việc không tồn tại."))

        if task._tp_requires_verification():
            if is_done:
                if task._tp_can_verify_result() and task.tp_exec_report_state == "reported_done":
                    self.tp_report_or_verify_task(task.id, "verify")
                else:
                    self.tp_report_or_verify_task(task.id, "report_done")
            else:
                self.tp_report_or_verify_task(task.id, "reopen")
            stages = self._tp_ensure_my_personal_stages()
            return task._tp_serialize_tasks(stages)[0]

        task._tp_assert_personal_task_access(mode="write")
        done_flag = bool(is_done)
        task.write(
            {
                "state": "1_done" if done_flag else "01_in_progress",
                "tp_exec_report_state": "verified" if done_flag else "in_progress",
            }
        )
        stages = self._tp_ensure_my_personal_stages()
        return task._tp_serialize_tasks(stages)[0]

    @api.model
    def tp_move_personal_task(self, task_id, target_stage_id, ordered_task_ids=None):
        """Move and/or resequence a task ONLY in the current user's personal stage table.

        NEVER touches `project.task.stage_id` (project stage), `project.task.state`,
        `project.task.kd_command_version`, or `project.task.sequence`, so dragging a
        project task or shared task on the user's personal Kanban board has ZERO side effects
        on the project WBS or other colleagues' boards!
        """
        self.env["res.users"]._tp_require_internal_caller()
        task = self.browse(int(task_id or 0)).exists()
        if not task:
            raise MissingError(self.env._("Công việc không tồn tại hoặc đã lưu trữ."))
        task._tp_assert_personal_task_access(mode="personal_board")

        stage = self.env["project.task.type"].search(
            [
                ("id", "=", int(target_stage_id or 0)),
                ("user_id", "=", self.env.uid),
                ("project_ids", "=", False),
            ],
            limit=1,
        )
        if not stage:
            raise ValidationError(
                self.env._("Giai đoạn cá nhân đích không tồn tại hoặc không thuộc tài khoản của bạn.")
            )

        stages = self._tp_ensure_my_personal_stages()
        self._tp_ensure_personal_stage_rels(task, stages)
        Rel = self.env["project.task.stage.personal"].sudo()
        target_rel = Rel.search(
            [("user_id", "=", self.env.uid), ("task_id", "=", task.id)], limit=1
        )
        if not target_rel:
            raise ValidationError(self.env._("Không tìm thấy trạng thái giai đoạn cá nhân của công việc."))

        ordered_ids = [int(tid) for tid in (ordered_task_ids or []) if str(tid).isdigit()]
        if task.id not in ordered_ids:
            ordered_ids.append(task.id)

        stage_rels = Rel.search(
            [
                ("user_id", "=", self.env.uid),
                "|",
                ("stage_id", "=", stage.id),
                ("task_id", "in", ordered_ids),
            ],
            order="tp_personal_sequence asc, id desc",
        )
        rel_by_tid = {r.task_id.id: r for r in stage_rels}
        target_rel.write({"stage_id": stage.id})

        existing_order = [
            r.task_id.id
            for r in stage_rels
            if r.task_id.id != task.id and r.stage_id.id == stage.id
        ]
        merged_order = []
        seen = set()
        for tid in ordered_ids:
            if tid in rel_by_tid and tid not in seen:
                merged_order.append(tid)
                seen.add(tid)
        for tid in existing_order:
            if tid in rel_by_tid and tid not in seen:
                merged_order.append(tid)
                seen.add(tid)

        for idx, tid in enumerate(merged_order, start=1):
            rel = rel_by_tid[tid]
            new_seq = idx * 10
            updates = {}
            if tid == task.id and rel.stage_id.id != stage.id:
                updates["stage_id"] = stage.id
            if rel.tp_personal_sequence != new_seq:
                updates["tp_personal_sequence"] = new_seq
            if updates:
                rel.write(updates)

        return task._tp_serialize_tasks(stages)[0]

    @api.model
    def tp_manage_personal_stage(self, action, stage_id=0, vals=None):
        """Create, rename, fold, reorder, or delete the current user's personal stages."""
        self.env["res.users"]._tp_require_internal_caller()
        vals = dict(vals or {})
        Stage = self.env["project.task.type"]

        if action == "create":
            name = str(vals.get("name") or "").strip()
            if not name:
                raise ValidationError(self.env._("Vui lòng nhập tên giai đoạn mới."))
            my_stages = self._tp_ensure_my_personal_stages()
            max_seq = max((s.sequence for s in my_stages), default=0)
            st = Stage.with_context(default_project_id=False, default_project_ids=False).create(
                {
                    "name": name,
                    "user_id": self.env.uid,
                    "sequence": max_seq + 10,
                    "fold": False,
                }
            )
            return {"id": st.id, "name": st.name, "sequence": st.sequence, "fold": bool(st.fold)}

        if action == "reorder":
            ordered_ids = [int(sid) for sid in (vals.get("stage_ids") or []) if str(sid).isdigit()]
            my_stages = Stage.search(
                [("user_id", "=", self.env.uid), ("project_ids", "=", False)],
                order="sequence asc, id asc",
            )
            stage_map = {s.id: s for s in my_stages}
            seq = 10
            for sid in ordered_ids:
                if sid in stage_map:
                    stage_map[sid].write({"sequence": seq})
                    seq += 10
            return True

        stage = Stage.search(
            [
                ("id", "=", int(stage_id or 0)),
                ("user_id", "=", self.env.uid),
                ("project_ids", "=", False),
            ],
            limit=1,
        )
        if not stage:
            raise AccessError(self.env._("Bạn chỉ có thể chỉnh sửa giai đoạn cá nhân của chính mình."))

        if action == "rename":
            name = str(vals.get("name") or "").strip()
            if not name:
                raise ValidationError(self.env._("Tên giai đoạn không được để trống."))
            stage.write({"name": name})
        elif action == "toggle_fold":
            stage.write({"fold": not stage.fold})
        elif action == "delete":
            stage.unlink()
        else:
            raise ValidationError(self.env._("Thao tác giai đoạn không hợp lệ."))
        return True

    @api.model
    def tp_archive_personal_task(self, task_id, active=False):
        self.env["res.users"]._tp_require_internal_caller()
        task = self.with_context(active_test=False).browse(int(task_id or 0)).exists()
        if not task:
            raise MissingError(self.env._("Công việc không tồn tại."))
        task._tp_assert_personal_task_access(mode="write")
        task.write({"active": bool(active)})
        return {"id": task.id, "active": bool(task.active)}

    @api.model
    def tp_delete_personal_task(self, task_id):
        self.env["res.users"]._tp_require_internal_caller()
        task = self.with_context(active_test=False).browse(int(task_id or 0)).exists()
        if not task:
            raise MissingError(self.env._("Công việc không tồn tại."))
        task._tp_assert_personal_task_access(mode="unlink")
        task.unlink()
        return {"deleted": True}

    @api.model
    def tp_upload_personal_task_attachment(self, task_id, filename, base64_data, mimetype=""):
        """Attach a file/evidence to a task via native `ir.attachment` (`public=False`)."""
        self.env["res.users"]._tp_require_internal_caller()
        task = self.browse(int(task_id or 0)).exists()
        if not task:
            raise MissingError(self.env._("Công việc không tồn tại."))
        task._tp_assert_personal_task_access(mode="read")
        if not task._tp_is_user_involved():
            raise AccessError(self.env._("Chỉ người thực hiện hoặc người phụ trách mới được đính kèm tệp minh chứng."))

        clean_name = str(filename or "").strip() or "tep-dinh-kem"
        if not base64_data:
            raise ValidationError(self.env._("Nội dung tệp tải lên đang trống."))
        try:
            raw_bytes = base64.b64decode(base64_data, validate=False)
        except Exception as exc:
            raise ValidationError(self.env._("Không đọc được định dạng tệp tải lên.")) from exc

        if len(raw_bytes) > MAX_ATTACHMENT_BYTES:
            raise ValidationError(
                self.env._("Dung lượng tệp vượt quá giới hạn cho phép (25 MB).")
            )

        att_vals = {
            "name": clean_name,
            "raw": raw_bytes,
            "res_model": "project.task",
            "res_id": task.id,
            "public": False,
            "company_id": self.env.company.id,
        }
        if mimetype:
            att_vals["mimetype"] = str(mimetype)
        # If task is a KH-KD project task where direct write on project.task is restricted,
        # create the non-public attachment under sudo while keeping create_uid = caller via context/check
        if task.project_id and not task.has_access("write"):
            att = self.env["ir.attachment"].sudo().create(att_vals)
        else:
            att = self.env["ir.attachment"].create(att_vals)
        return {
            "id": att.id,
            "name": att.name,
            "mimetype": att.mimetype or "application/octet-stream",
            "file_size": att.file_size or len(raw_bytes),
            "is_image": bool((att.mimetype or "").startswith("image/")),
            "download_url": f"/web/content/{att.id}?download=true",
            "preview_url": f"/web/image/{att.id}"
            if (att.mimetype or "").startswith("image/")
            else f"/web/content/{att.id}",
            "can_delete": True,
        }

    @api.model
    def tp_delete_personal_task_attachment(self, task_id, attachment_id):
        self.env["res.users"]._tp_require_internal_caller()
        task = self.browse(int(task_id or 0)).exists()
        if not task:
            raise MissingError(self.env._("Công việc không tồn tại."))
        task._tp_assert_personal_task_access(mode="read")
        att = self.env["ir.attachment"].browse(int(attachment_id or 0)).exists()
        if not att or att.res_model != "project.task" or att.res_id != task.id:
            raise MissingError(self.env._("Tệp đính kèm không tồn tại trên công việc này."))
        if not (task._tp_can_edit_core_fields() or att.create_uid == self.env.user):
            raise AccessError(self.env._("Bạn chỉ có thể xóa tệp minh chứng do chính mình tải lên."))
        att.sudo().unlink() if task.project_id else att.unlink()
        return {"deleted": True}

    @api.model
    def tp_post_personal_task_comment(self, task_id, body, operation_token=""):
        """Post a comment on a permitted task using native `message_post`."""
        self.env["res.users"]._tp_require_internal_caller()
        task = self.browse(int(task_id or 0)).exists()
        if not task:
            raise MissingError(self.env._("Công việc không tồn tại."))
        task._tp_assert_personal_task_access(mode="read")

        clean_body = str(body or "").strip()
        if not clean_body:
            raise ValidationError(self.env._("Vui lòng nhập nội dung trao đổi."))

        op_log = self.env["tp.personal.operation.log"]
        existing, clean_token, fp = op_log.acquire_or_replay(
            "post_task_comment",
            operation_token,
            {"task_id": task.id, "body": clean_body},
        )
        if not existing:
            safe_html = Markup("<p>%s</p>") % Markup("<br/>").join(
                html.escape(line) for line in clean_body.splitlines()
            )
            poster = task.sudo() if (task.project_id and not task.has_access("write")) else task
            msg = poster.message_post(
                body=safe_html,
                author_id=self.env.user.partner_id.id,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )
            op_log.record_success("post_task_comment", clean_token, fp, msg)
        return self.tp_get_personal_task_detail(task.id)

    @api.model
    def tp_schedule_personal_task(self, task_id, vals, operation_token=""):
        """Create a linked `calendar.event` (`res_model='project.task'`, `res_id=task.id`).

        Never creates a duplicate task and never silently mutates the task's deadline.
        """
        self.env["res.users"]._tp_require_internal_caller()
        task = self.browse(int(task_id or 0)).exists()
        if not task:
            raise MissingError(self.env._("Công việc không tồn tại."))
        task._tp_assert_personal_task_access(mode="read")
        self.env["calendar.event"].check_access("create")

        vals = dict(vals or {})
        event_vals = {
            "name": str(vals.get("name") or task.name or "").strip(),
            "allday": bool(vals.get("allday")),
            "start_iso": vals.get("start_iso"),
            "stop_iso": vals.get("stop_iso"),
            "start_date": vals.get("start_date"),
            "stop_date": vals.get("stop_date"),
            "location": vals.get("location") or "",
            "notes": vals.get("notes") or "",
            "privacy": vals.get("privacy") or "private",
            "calendar_id": vals.get("calendar_id") or False,
            "partner_ids": vals.get("partner_ids") or [],
            "project_id": task.project_id.id if task.project_id else False,
            "res_model": "project.task",
            "res_id": task.id,
        }
        return self.env["calendar.event"].tp_save_calendar_event(
            False, event_vals, operation_token=operation_token
        )
