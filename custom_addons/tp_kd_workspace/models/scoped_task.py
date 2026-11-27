"""Narrow task commands; generic native writes stay under the original policy."""

import hashlib
import json
import uuid

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import SQL

from .workspace import _INTERNAL, child_context, kd_leaf


class Task(models.Model):
    _inherit = "project.task"
    kd_command_version = fields.Integer(default=1, readonly=True, copy=False)
    kd_can_wbs = fields.Boolean(compute="_compute_kd_task_commands")
    kd_can_assign = fields.Boolean(compute="_compute_kd_task_commands")
    kd_can_progress = fields.Boolean(compute="_compute_kd_task_commands")

    def _kd_snapshot(self):
        self.ensure_one()
        return {
            "name": self.name,
            "parent_id": self.parent_id.id,
            "assignees": self.user_ids.ids,
            "responsible_id": self.kd_responsible_id.id,
            "deadline": str(self.date_deadline),
            "deliverable": self.kd_deliverable,
            "description": str(self.description),
            "state": self.state,
        }

    @api.depends_context("uid")
    def _compute_kd_task_commands(self):
        for t in self:
            t.kd_can_wbs = bool(t.project_id and t.project_id._kd_has("wbs"))
            t.kd_can_assign = bool(
                t.project_id and t.project_id._kd_has("task_assignment"),
            )
            t.kd_can_progress = bool(
                t.project_id
                and t.project_id._kd_has("task_progress")
                and (self.env.user in t.user_ids or t.project_id._tp_head_allowed()),
            )

    def _kd_task_dialog(self, operation):
        self.ensure_one()
        self.check_access("read")
        w = self.env["tp.task.command"].create(
            {
                "project_id": self.project_id.id,
                "task_id": self.id,
                "operation": operation,
            },
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Công việc dự án",
            "res_model": w._name,
            "res_id": w.id,
            "views": [(self.env.ref("tp_kd_workspace.task_command_form").id, "form")],
            "target": "new",
        }

    def action_kd_edit_task(self):
        return self._kd_task_dialog("edit")

    def action_kd_assign_task(self):
        return self._kd_task_dialog("assign")

    def action_kd_progress(self):
        return self._kd_task_dialog("progress")

    def action_kd_task_history(self):
        self.ensure_one()
        self.check_access("read")
        action = self.env["ir.actions.actions"]._for_xml_id("tp_kd_workspace.action_task_updates")
        action.update({
            "name": "Lịch sử thực hiện",
            "domain": [("task_id", "=", self.id)],
            "context": {**child_context(self.env), **kd_leaf("project.task")},
        })
        return action


class Project(models.Model):
    _inherit = "project.project"
    kd_can_wbs = fields.Boolean(compute="_compute_kd_can_wbs")

    @api.depends_context("uid")
    def _compute_kd_can_wbs(self):
        for p in self:
            p.kd_can_wbs = p._kd_has("wbs")

    def action_kd_wbs(self):
        action = self.action_kd_tasks()
        action["name"] = "Hạng mục / WBS"
        action["context"].update(
            group_by="parent_id",
            tp_kd_leaf="tp_kd_workspace.menu_wbs",
        )
        return action

    def action_kd_new_task(self):
        self.ensure_one()
        self.check_access("read")
        if not self._kd_has("wbs"):
            raise AccessError(self.env._("Tạo WBS cần capability riêng."))
        w = self.env["tp.task.command"].create(
            {"project_id": self.id, "operation": "create"},
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Thêm hạng mục / công việc",
            "res_model": w._name,
            "res_id": w.id,
            "views": [(self.env.ref("tp_kd_workspace.task_command_form").id, "form")],
            "target": "new",
        }


class TaskCommand(models.TransientModel):
    _name = "tp.task.command"
    _description = "Thao tác WBS, giao việc, tiến độ theo capability riêng"
    project_id = fields.Many2one("project.project", required=True, readonly=True)
    task_id = fields.Many2one("project.task", readonly=True)
    operation = fields.Selection(
        [
            ("create", "Tạo công việc"),
            ("edit", "Sửa hạng mục"),
            ("assign", "Giao việc"),
            ("progress", "Cập nhật tiến độ"),
        ],
        required=True,
        readonly=True,
    )
    expected_version = fields.Integer(readonly=True)
    expected_write_date = fields.Datetime(readonly=True)
    request_key = fields.Char(readonly=True)
    name = fields.Char(string="Công việc / hạng mục")
    parent_id = fields.Many2one("project.task", string="Hạng mục cha")
    responsible_id = fields.Many2one("res.users", string="Người phụ trách")
    deadline = fields.Datetime(string="Hạn hoàn thành")
    deliverable = fields.Char(string="Đầu ra bàn giao")
    description = fields.Html(string="Nội dung")
    target_state = fields.Selection(
        [
            ("01_in_progress", "Đang thực hiện"),
            ("04_waiting_normal", "Chờ xử lý"),
            ("1_done", "Hoàn tất công việc"),
        ],
        string="Tiến độ mới",
    )
    reason = fields.Text(string="Căn cứ / lý do")

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for supplied in vals_list:
            p = self.env["project.project"].browse(supplied.get("project_id"))
            p.check_access("read")
            domain = {
                "create": "wbs",
                "edit": "wbs",
                "assign": "task_assignment",
                "progress": "task_progress",
            }.get(supplied.get("operation"))
            if not domain or not p._kd_has(domain):
                raise AccessError(
                    self.env._("Chưa có capability thao tác công việc trong dự án."),
                )
            t = self.env["project.task"].browse(supplied.get("task_id"))
            if t:
                t.check_access("read")
                if t.project_id != p:
                    raise AccessError(self.env._("Công việc không cùng dự án."))
            if supplied.get("operation") != "create" and not t:
                raise ValidationError(self.env._("Chọn công việc cần cập nhật."))
            prepared.append(
                {
                    **supplied,
                    "expected_version": t.kd_command_version if t else 0,
                    "expected_write_date": t.write_date if t else False,
                    "request_key": uuid.uuid4().hex,
                    "name": t.name if t else False,
                    "parent_id": t.parent_id.id if t else False,
                    "responsible_id": t.kd_responsible_id.id if t else self.env.uid,
                    "deadline": t.date_deadline if t else False,
                    "deliverable": t.kd_deliverable if t else False,
                    "description": t.description if t else False,
                },
            )
        return super().create(prepared)

    def write(self, vals):
        if set(vals) & {
            "project_id",
            "task_id",
            "operation",
            "expected_version",
            "expected_write_date",
            "request_key",
        }:
            raise AccessError(
                self.env._("Đích, phiên bản và mã thao tác do máy chủ quản lý."),
            )
        return super().write(vals)

    def action_confirm(self):
        self.ensure_one()
        self.check_access("read")
        p, t = self.project_id, self.task_id
        domain = {
            "create": "wbs",
            "edit": "wbs",
            "assign": "task_assignment",
            "progress": "task_progress",
        }[self.operation]
        if not p._kd_has(domain):
            raise AccessError(
                self.env._("Chưa có capability thực hiện thao tác công việc."),
            )
        if not (self.reason or "").strip():
            raise UserError(self.env._("Cần căn cứ / lý do."))
        payload = {
            "operation": self.operation,
            "name": self.name,
            "parent": self.parent_id.id,
            "responsible": self.responsible_id.id,
            "deadline": str(self.deadline),
            "deliverable": self.deliverable,
            "description": str(self.description),
            "target_state": self.target_state,
            "reason": self.reason,
        }
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode(),
        ).hexdigest()
        self.env.flush_all()
        # Project lock also serializes creates with the same request key.
        self.env.cr.execute(
            SQL("SELECT id FROM project_project WHERE id=%s FOR UPDATE", p.id),
        )
        events = self.env["tp.task.update"].sudo()
        old = events.search(
            [
                ("project_id", "=", p.id),
                ("actor_id", "=", self.env.uid),
                ("request_key", "=", self.request_key),
            ],
            limit=1,
        )
        if old:
            if old.payload_hash != fingerprint:
                raise UserError(self.env._("Mã thao tác đã dùng với nội dung khác."))
            return {"type": "ir.actions.act_window_close"}
        if t:
            t.check_access("read")
            self.env.cr.execute(
                SQL("SELECT id FROM project_task WHERE id=%s FOR UPDATE", t.id),
            )
            t.invalidate_recordset()
            if (
                t.kd_command_version != self.expected_version
                or t.write_date != self.expected_write_date
            ):
                raise UserError(
                    self.env._("Công việc vừa thay đổi. Tải lại trước khi cập nhật."),
                )
            if t.state in ("03_approved", "1_canceled"):
                raise UserError(
                    self.env._(
                        "Không dùng tiến độ để sửa công việc đã duyệt hoặc hủy.",
                    ),
                )
        before = t.state if t else False
        snapshot_before = t._kd_snapshot() if t else None
        if self.operation == "progress":
            if (self.env.user not in t.user_ids and not p._tp_head_allowed()) or self.target_state not in (
                "01_in_progress",
                "04_waiting_normal",
                "1_done",
            ):
                raise AccessError(
                    self.env._(
                        "Chỉ người được giao và có capability được báo tiến độ.",
                    ),
                )
            vals = {
                "state": self.target_state,
                "kd_command_version": t.kd_command_version + 1,
            }
        elif self.operation == "assign":
            vals = {
                "kd_responsible_id": self.responsible_id.id,
                "user_ids": [Command.set(self.responsible_id.ids)],
                "kd_command_version": t.kd_command_version + 1,
            }
        else:
            if not (self.name or "").strip() or not (self.deliverable or "").strip():
                raise ValidationError(self.env._("Cần tên và đầu ra công việc."))
            if self.parent_id:
                self.parent_id.check_access("read")
                if self.parent_id.project_id != p or self.parent_id == t:
                    raise ValidationError(
                        self.env._(
                            "Hạng mục cha phải cùng dự án và không là chính công việc.",
                        ),
                    )
            vals = {
                "name": self.name,
                "parent_id": self.parent_id.id,
                "date_deadline": self.deadline,
                "kd_deliverable": self.deliverable,
                "description": self.description,
                "kd_command_version": (t.kd_command_version + 1) if t else 1,
            }
            if self.operation == "create":
                if (
                    not p._kd_has("task_assignment")
                    and self.responsible_id != self.env.user
                ):
                    raise AccessError(
                        self.env._(
                            "Giao cho người khác cần capability giao việc riêng.",
                        ),
                    )
                vals.update(
                    project_id=p.id,
                    company_id=p.company_id.id,
                    kd_responsible_id=self.responsible_id.id,
                    user_ids=[Command.set(self.responsible_id.ids)],
                )
        if self.operation in ("assign", "create"):
            if (
                not self.responsible_id
                or not self.responsible_id.active
                or not p._tp_scope_allowed(user=self.responsible_id)
            ):
                raise AccessError(
                    self.env._("Người nhận phải còn phân công đúng dự án."),
                )
        # No notifications to followers outside the project; event retains the original actor.
        target = t.sudo().with_context(
            tracking_disable=True,
            mail_create_nosubscribe=True,
        )
        if self.operation == "create":
            target = (
                self.env["project.task"]
                .sudo()
                .with_context(tracking_disable=True, mail_create_nosubscribe=True)
                .create(vals)
            )
        else:
            target.write(vals)
        events.with_context(_kd_internal=_INTERNAL).create(
            {
                "project_id": p.id,
                "task_id": target.id,
                "actor_id": self.env.uid,
                "operation": self.operation,
                "reason": self.reason,
                "state_before": before,
                "state_after": target.state,
                "version": target.kd_command_version,
                "request_key": self.request_key,
                "payload_hash": fingerprint,
                "before_values": snapshot_before,
                "after_values": target._kd_snapshot(),
            },
        )
        return {"type": "ir.actions.act_window_close"}


class TaskUpdate(models.Model):
    _name = "tp.task.update"
    _description = "Lịch sử thực hiện công việc append-only"
    _order = "id desc"
    project_id = fields.Many2one("project.project", required=True, ondelete="restrict")
    task_id = fields.Many2one("project.task", required=True, ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    actor_id = fields.Many2one("res.users", required=True)
    operation = fields.Char(required=True)
    reason = fields.Text(required=True)
    state_before = fields.Char()
    state_after = fields.Char()
    version = fields.Integer(required=True)
    request_key = fields.Char(required=True)
    payload_hash = fields.Char(required=True)
    before_values = fields.Json(readonly=True)
    after_values = fields.Json(readonly=True)
    _key_unique = models.Constraint(
        "UNIQUE(project_id,actor_id,request_key)",
        "Mã thao tác đã tồn tại.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("_kd_internal") is not _INTERNAL:
            raise AccessError(self.env._("Lịch sử chỉ được sinh từ action."))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._("Không sửa lịch sử."))

    def unlink(self):
        raise AccessError(self.env._("Không xóa lịch sử."))
