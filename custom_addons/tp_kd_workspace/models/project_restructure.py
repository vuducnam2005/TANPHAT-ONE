"""Two native perspectives over one project, with explicit scoped commands."""

import hashlib
import json
import uuid

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import SQL
from odoo.tools.misc import formatLang

from .workspace import _INTERNAL, child_context, open_records

LIFECYCLE = [
    ("tracking", "Đang theo dõi"),
    ("executing", "Đang thực hiện"),
    ("paused", "Tạm dừng"),
    ("ended", "Kết thúc"),
]
BID_STAGE = [
    ("tracking", "Theo dõi"),
    ("participating", "Đang tham gia"),
    ("awaiting_result", "Chờ kết quả"),
]
OUTCOME = [
    ("unknown", "Chưa xác định"),
    ("won", "Trúng thầu"),
    ("lost", "Không trúng"),
    ("cancelled", "Gói bị hủy"),
    ("not_participating", "Không tham gia"),
]
ROLES = [
    ("investor", "Chủ đầu tư"),
    ("inviter", "Bên mời thầu"),
    ("counterparty", "Tổng thầu / bên ký trực tiếp"),
    ("consortium_lead", "Liên danh chủ trì"),
    ("consortium_member", "Liên danh thành viên"),
    ("coordinator", "Phối hợp"),
    ("subcontractor", "Thầu phụ"),
]
NEW_DOMAINS = [
    (k, v)
    for k, v in [
        ("project_metadata", "Thông tin dự án"),
        ("project_status", "Tình trạng dự án"),
        ("project_note", "Ghi chú dự án"),
        ("project_reopen", "Mở lại dự án"),
        ("bid", "Gói thầu"),
        ("wbs", "Cấu trúc WBS"),
        ("task_assignment", "Giao việc"),
        ("task_progress", "Tiến độ công việc"),
    ]
]


class PackageValue(fields.Monetary):
    def __get__(self, record, owner=None):
        if record is not None and record and not record.env.su:
            record._kd_read_guard()
        return super().__get__(record, owner)


class Grant(models.Model):
    _inherit = "tp.kd.grant"
    domain = fields.Selection(
        selection_add=NEW_DOMAINS,
        ondelete={k: "cascade" for k, _ in NEW_DOMAINS},
    )


class Project(models.Model):
    _inherit = "project.project"
    kd_investor_id = fields.Many2one(
        "res.partner",
        string="Chủ đầu tư",
        check_company=True,
        ondelete="restrict",
    )
    kd_lifecycle = fields.Selection(
        LIFECYCLE,
        default="tracking",
        required=True,
        copy=False,
        string="Tình trạng dự án",
    )
    kd_version = fields.Integer(default=1, readonly=True, copy=False)
    kd_participation_ids = fields.One2many(
        "tp.project.participation",
        "project_id",
        string="Các bên tham gia",
    )
    kd_package_ids = fields.One2many(
        "tp.bid.package",
        "project_id",
        string="Các gói thầu",
    )
    kd_partner_summary = fields.Char(compute="_compute_kd_summary", string="Đối tác")
    kd_last_note = fields.Char(compute="_compute_kd_summary", string="Ghi chú gần nhất")
    kd_can_status = fields.Boolean(compute="_compute_kd_commands")
    kd_can_note = fields.Boolean(compute="_compute_kd_commands")
    kd_can_metadata = fields.Boolean(compute="_compute_kd_commands")
    kd_read_hint = fields.Char(compute="_compute_kd_commands", string="Quyền thao tác")

    def _kd_has(self, domain):
        self.ensure_one()
        return bool(
            self.tp_managed
            and self.company_id in self.env.companies
            and self.env["tp.kd.grant"]._has(self, domain, "prepare"),
        )

    def _kd_money_read(self):
        self.ensure_one()
        return self.has_access("read") and bool(
            self._tp_scope_allowed()
            and self.env["tp.project.grant"]._tp_has_capability(self, "financial_read"),
        )

    @api.depends_context("uid")
    def _compute_kd_commands(self):
        for p in self:
            p.kd_can_status = p._kd_has("project_status") and p._kd_money_read()
            p.kd_can_note = p._kd_has("project_note") and p._kd_money_read()
            p.kd_can_metadata = p._kd_has("project_metadata")
            p.kd_read_hint = (
                "Chọn nút thao tác; thanh tình trạng chỉ hiển thị."
                if p.kd_can_status or p.kd_can_note or p.kd_can_metadata
                else "Bạn đang xem hồ sơ. Thao tác cần capability theo dự án; chức danh không tự cấp quyền. Liên hệ người phụ trách để đối chiếu phân công."
            )

    @api.depends_context("uid")
    def _compute_kd_summary(self):
        for p in self:
            p.kd_partner_summary = "; ".join(
                f"{r.partner_id.display_name} ({dict(ROLES)[r.role]})"
                for r in p.kd_participation_ids.filtered(lambda x: not x.package_id)
            )
            note = (
                self.env["tp.project.update"].search(
                    [("project_id", "=", p.id)],
                    order="id desc",
                    limit=1,
                )
                if p._kd_money_read()
                else False
            )
            p.kd_last_note = note.reason[:180] if note else False

    def _read_format(self, fnames, load="_classic_read"):
        self.invalidate_recordset(
            [
                n
                for n in fnames
                if n.startswith("kd_can_")
                or n in ("kd_last_note", "kd_read_hint", "kd_partner_summary")
            ],
        )
        return super()._read_format(fnames, load=load)

    def write(self, vals):
        if (
            set(vals) & {"kd_investor_id", "kd_lifecycle", "kd_version"}
            and not self.env.su
            and self.env.context.get("_kd_internal") is not _INTERNAL
        ):
            raise AccessError(
                self.env._("Dùng thao tác cập nhật dự án có phiên bản và lịch sử."),
            )
        return super().write(vals)

    def _kd_apply(
        self,
        kind,
        reason,
        expected_version,
        key,
        payload=None,
        package=None,
    ):
        self.ensure_one()
        self.check_access("read")
        payload = payload or {}
        domains = {
            "status": "project_status",
            "note": "project_note",
            "metadata": "project_metadata",
            "bid": "bid",
            "amount": "bid",
            "party": "project_metadata",
            "party_revoke": "project_metadata",
        }
        if kind not in domains or not self._kd_has(domains[kind]):
            raise AccessError(
                self.env._("Chưa được cấp capability thao tác trong dự án này."),
            )
        if kind in ("status", "note", "bid", "amount") and not self._kd_money_read():
            raise AccessError(
                self.env._("Nhật ký nội dung chưa phân loại cần quyền tiền hiện hành."),
            )
        if (
            not (reason or "").strip()
            or not isinstance(key, str)
            or not 8 <= len(key) <= 128
        ):
            raise UserError(self.env._("Cần ghi chú/căn cứ và mã thao tác hợp lệ."))
        if package:
            package.check_access("read")
            if package.project_id != self or (
                package.owner_id != self.env.user
                and not self._kd_has("project_metadata")
            ):
                raise AccessError(
                    self.env._("Gói thầu không thuộc trách nhiệm của bạn."),
                )
        fingerprint = hashlib.sha256(
            json.dumps(
                [kind, reason, payload, package.id if package else None],
                sort_keys=True,
            ).encode(),
        ).hexdigest()
        self.env.flush_all()
        self.env.cr.execute(
            SQL("SELECT id FROM project_project WHERE id=%s FOR UPDATE", self.id),
        )
        self.invalidate_recordset()
        events = self.env["tp.project.update"].sudo()
        old = events.search(
            [
                ("project_id", "=", self.id),
                ("actor_id", "=", self.env.uid),
                ("request_key", "=", key),
            ],
            limit=1,
        )
        if old:
            if old.payload_hash != fingerprint:
                raise UserError(self.env._("Mã thao tác đã dùng với nội dung khác."))
            return old.id
        if expected_version != self.kd_version:
            raise UserError(
                self.env._("Dự án vừa thay đổi. Tải lại và mở thao tác mới."),
            )
        before, after = self.kd_lifecycle, self.kd_lifecycle
        if kind == "status":
            after = payload.get("state")
            if after not in dict(LIFECYCLE) or after == before:
                raise UserError(self.env._("Chọn tình trạng khác hợp lệ."))
            if before == "ended" and not self._kd_has("project_reopen"):
                raise AccessError(self.env._("Mở lại dự án cần capability riêng."))
            self.sudo().with_context(_kd_internal=_INTERNAL).write(
                {"kd_lifecycle": after},
            )
        elif kind == "metadata":
            if set(payload) - {"kd_investor_id", "kd_scope", "name"}:
                raise AccessError(
                    self.env._(
                        "Chỉ cập nhật tên, phạm vi và chủ đầu tư; không đổi owner/company.",
                    ),
                )
            if payload.get("kd_investor_id"):
                partner = self.env["res.partner"].browse(payload["kd_investor_id"])
                partner.check_access("read")
                if partner.company_id and partner.company_id != self.company_id:
                    raise ValidationError(
                        self.env._(
                            "Chủ đầu tư phải cùng công ty hoặc danh bạ dùng chung.",
                        ),
                    )
            self.sudo().with_context(_kd_internal=_INTERNAL).write(payload)
        elif kind == "bid":
            if not package or set(payload) - {"stage", "outcome"}:
                raise UserError(self.env._("Cần đúng gói thầu và nội dung cập nhật."))
            before = f"{package.stage}/{package.outcome}"
            stage = payload.get("stage", package.stage)
            outcome = payload.get("outcome", package.outcome)
            if stage not in dict(BID_STAGE) or outcome not in dict(OUTCOME):
                raise UserError(self.env._("Tình trạng hoặc kết quả không hợp lệ."))
            index = {k: i for i, (k, _) in enumerate(BID_STAGE)}
            if abs(index[stage] - index[package.stage]) > 1:
                raise UserError(
                    self.env._(
                        "Cập nhật từng chặng dự thầu; kết quả cần căn cứ riêng.",
                    ),
                )
            package.sudo().with_context(_kd_internal=_INTERNAL).write(
                {"stage": stage, "outcome": outcome},
            )
            after = f"{stage}/{outcome}"
        elif kind == "party_revoke":
            relation = self.env["tp.project.participation"].browse(
                payload.get("participation_id"),
            )
            relation.check_access("read")
            if relation.project_id != self or not relation.active:
                raise UserError(self.env._("Quan hệ đã ngừng hoặc không cùng dự án."))
            before = f"{relation.partner_id.id}/{relation.role}/active"
            relation.sudo().with_context(_kd_internal=_INTERNAL).write(
                {"active": False},
            )
            after = f"{relation.partner_id.id}/{relation.role}/revoked"
        elif kind in ("amount", "party"):
            before = json.dumps(
                payload.get("before"),
                ensure_ascii=False,
                sort_keys=True,
            )
            after = json.dumps(payload.get("after"), ensure_ascii=False, sort_keys=True)
        correction = payload.get("correction_id") if kind == "note" else False
        if correction:
            corrected = events.browse(correction)
            if not corrected.exists() or corrected.project_id != self:
                raise AccessError(self.env._("Chỉ đính chính nhật ký của cùng dự án."))
        event = events.with_context(_kd_internal=_INTERNAL).create(
            {
                "project_id": self.id,
                "package_id": package.id if package else False,
                "actor_id": self.env.uid,
                "kind": kind,
                "state_before": before,
                "state_after": after,
                "reason": reason.strip(),
                "version": self.kd_version + 1,
                "request_key": key,
                "payload_hash": fingerprint,
                "correction_id": correction,
            },
        )
        self.sudo().with_context(_kd_internal=_INTERNAL).write(
            {"kd_version": self.kd_version + 1},
        )
        self.invalidate_recordset()
        return event.id

    def _kd_wizard(self, kind, package=None):
        self.ensure_one()
        self.check_access("read")
        wizard = self.env["tp.project.command"].create(
            {
                "project_id": self.id,
                "kind": kind,
                "package_id": package.id if package else False,
            },
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "views": [
                (self.env.ref("tp_kd_workspace.project_command_form").id, "form"),
            ],
            "target": "new",
            "name": dict(wizard._fields["kind"].selection)[kind],
        }

    def action_kd_status(self):
        return self._kd_wizard("status")

    def action_kd_note(self):
        return self._kd_wizard("note")

    def action_kd_metadata(self):
        return self._kd_wizard("metadata")

    def action_kd_history(self):
        self.ensure_one()
        self.check_access("read")
        if not self._kd_money_read():
            raise AccessError(
                self.env._("Nhật ký chưa phân loại cần quyền tiền hiện hành."),
            )
        return open_records(
            self.env,
            "tp.project.update",
            [("project_id", "=", self.id)],
            "Lịch sử dự án",
        )

    def _kd_perspective(self, mode):
        self.ensure_one()
        self.check_access("read")
        view = self.env.ref(
            "tp_kd_workspace.project_management_form"
            if mode == "management"
            else "tp_kd_workspace.project_governance_form",
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Quản lý dự án" if mode == "management" else "Quản trị dự án",
            "res_model": self._name,
            "res_id": self.id,
            "views": [(view.id, "form")],
            "context": {
                **child_context(self.env),
                "tp_kd_leaf": "tp_kd_workspace.menu_management"
                if mode == "management"
                else "tp_kd_workspace.menu_governance",
            },
        }

    def action_kd_management(self):
        return self._kd_perspective("management")

    def action_kd_governance(self):
        return self._kd_perspective("governance")

    def action_kd_packages(self):
        self.ensure_one()
        return open_records(
            self.env,
            "tp.bid.package",
            [("project_id", "=", self.id)],
            "Đấu thầu",
            {"default_project_id": self.id},
        )

    def action_kd_parties(self):
        self.ensure_one()
        self.check_access("read")
        return open_records(
            self.env,
            "tp.project.participation",
            [("project_id", "=", self.id)],
            "Các bên tham gia",
            {"default_project_id": self.id},
        )


class Participation(models.Model):
    _name = "tp.project.participation"
    _description = "Các bên tham gia dự án theo vai trò"
    _check_company_auto = True
    _rec_name = "partner_id"
    project_id = fields.Many2one(
        "project.project",
        required=True,
        check_company=True,
        ondelete="restrict",
    )
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    package_id = fields.Many2one(
        "tp.bid.package",
        check_company=True,
        ondelete="restrict",
        string="Gói thầu",
    )
    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        check_company=True,
        ondelete="restrict",
        string="Đối tác",
    )
    role = fields.Selection(ROLES, required=True, string="Vai trò")
    reason = fields.Text(required=True, string="Căn cứ / ghi chú")
    active = fields.Boolean(default=True, readonly=True)
    can_revoke = fields.Boolean(compute="_compute_can_revoke")

    @api.depends_context("uid")
    def _compute_can_revoke(self):
        for r in self:
            r.can_revoke = r.active and r.project_id._kd_has("project_metadata")

    _unique_role = models.UniqueIndex(
        "(project_id, COALESCE(package_id, 0), partner_id, role) WHERE active IS TRUE",
        "Quan hệ cùng dự án/gói/bên/vai trò đã có.",
    )

    @api.constrains("project_id", "package_id", "partner_id", "reason")
    def _check_scope(self):
        for r in self:
            if (
                not r.project_id.tp_managed
                or (r.package_id and r.package_id.project_id != r.project_id)
                or not (r.reason or "").strip()
            ):
                raise ValidationError(
                    self.env._("Cần dự án TANPHAT, gói cùng dự án và căn cứ."),
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            p = self.env["project.project"].browse(
                vals.get("project_id") or self.env.context.get("default_project_id"),
            )
            p.check_access("read")
            self.env["res.partner"].browse(vals.get("partner_id")).check_access("read")
            if not self.env.su and not p._kd_has("project_metadata"):
                raise AccessError(
                    self.env._("Cần capability cập nhật các bên tham gia."),
                )
            self.env.cr.execute(
                SQL("SELECT id FROM project_project WHERE id=%s FOR UPDATE", p.id),
            )
            if self.search_count(
                [
                    ("project_id", "=", p.id),
                    ("package_id", "=", vals.get("package_id") or False),
                    ("partner_id", "=", vals.get("partner_id")),
                    ("role", "=", vals.get("role")),
                ],
                limit=1,
            ):
                raise ValidationError(
                    self.env._("Quan hệ cùng dự án/gói/bên/vai trò đã có."),
                )
        records = super().create(vals_list)
        for r in records:
            r.project_id._kd_apply(
                "party",
                r.reason,
                r.project_id.kd_version,
                uuid.uuid4().hex,
                {
                    "before": None,
                    "after": {"id": r.id, "partner": r.partner_id.id, "role": r.role},
                },
                r.package_id,
            )
        return records

    def write(self, vals):
        if self.env.context.get("_kd_internal") is _INTERNAL and set(vals) == {
            "active",
        }:
            return super().write(vals)
        raise UserError(
            self.env._(
                "Giữ quan hệ có căn cứ; sửa sai bằng nhật ký đính chính, không đổi vai âm thầm.",
            ),
        )

    def action_kd_revoke(self):
        self.ensure_one()
        action = self.project_id._kd_wizard("party_revoke")
        self.env["tp.project.command"].browse(action["res_id"]).write(
            {"participation_id": self.id},
        )
        return action

    def unlink(self):
        raise UserError(
            self.env._("Không xóa quan hệ đã lưu; ghi đính chính để đối chiếu."),
        )

    @api.model
    def get_kd_ui_permissions(self):
        self.check_access("read")
        return {
            "create": any(
                p._kd_has("project_metadata")
                for p in self.env["project.project"].search([("tp_managed", "=", True)])
            ),
        }


class BidPackage(models.Model):
    _name = "tp.bid.package"
    _description = "Gói thầu thuộc dự án"
    _check_company_auto = True
    _order = "deadline, id desc"
    code = fields.Char(required=True, string="Mã gói thầu")
    name = fields.Char(required=True, string="Gói thầu")
    project_id = fields.Many2one(
        "project.project",
        required=True,
        ondelete="restrict",
        check_company=True,
        string="Dự án",
    )
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    investor_id = fields.Many2one(
        related="project_id.kd_investor_id",
        string="Chủ đầu tư",
    )
    owner_id = fields.Many2one(
        "res.users",
        required=True,
        default=lambda self: self.env.user,
        string="Người phụ trách",
    )
    inviter_id = fields.Many2one(
        "res.partner",
        check_company=True,
        string="Bên mời thầu",
    )
    scope = fields.Text(required=True, string="Phạm vi")
    deadline = fields.Date(string="Hạn chuẩn bị / nộp")
    stage = fields.Selection(
        BID_STAGE,
        default="tracking",
        required=True,
        readonly=True,
        string="Tình trạng dự thầu",
    )
    outcome = fields.Selection(
        OUTCOME,
        default="unknown",
        required=True,
        readonly=True,
        string="Kết quả khai báo",
    )
    lead_ids = fields.One2many("crm.lead", "kd_package_id", string="Các lần tham gia")
    participation_ids = fields.One2many(
        "tp.project.participation",
        "package_id",
        string="Các bên tham gia",
    )
    amount_ids = fields.One2many(
        "tp.bid.package.amount",
        "package_id",
        string="Giá trị theo từng nghĩa",
    )
    partner_summary = fields.Char(compute="_compute_summary", string="Đối tác")
    budget_display = fields.Char(
        compute="_compute_summary",
        string="Dự kiến giá trị gói",
    )
    last_note = fields.Char(compute="_compute_summary", string="Ghi chú")
    can_edit = fields.Boolean(compute="_compute_summary")
    can_note = fields.Boolean(compute="_compute_summary")
    can_update_status = fields.Boolean(compute="_compute_summary")
    can_read_money = fields.Boolean(compute="_compute_summary")
    can_edit_money = fields.Boolean(compute="_compute_summary")
    _code_unique = models.Constraint(
        "UNIQUE(company_id,code)",
        "Mã gói phải duy nhất trong công ty.",
    )

    @api.depends_context("uid")
    def _compute_summary(self):
        for r in self:
            r.partner_summary = "; ".join(
                f"{x.partner_id.display_name} ({dict(ROLES)[x.role]})"
                for x in r.participation_ids
            )
            r.can_edit = r.project_id._kd_has("bid") and (r.owner_id == self.env.user or r.project_id._tp_head_allowed())
            r.can_read_money = r.project_id._kd_money_read()
            responsible = r.owner_id == self.env.user or r.project_id._kd_has(
                "project_metadata",
            )
            r.can_note = (
                r.can_read_money
                and responsible
                and r.project_id._kd_has("project_note")
            )
            r.can_update_status = (
                r.can_read_money and responsible and r.project_id._kd_has("bid")
            )
            r.can_edit_money = (
                r.can_edit
                and r.can_read_money
                and self.env["tp.project.grant"]._tp_has_capability(
                    r.project_id,
                    "financial_draft_edit",
                    r.project_id.tp_department_id,
                )
            )
            r.budget_display = self.env._("Không có quyền xem tiền")
            r.last_note = False
            if r.project_id._kd_money_read():
                amount = self.env["tp.bid.package.amount"].search(
                    [("package_id", "=", r.id), ("kind", "=", "package_total")],
                    limit=1,
                )
                r.budget_display = (
                    formatLang(self.env, amount.value, currency_obj=amount.currency_id)
                    if amount and amount.amount_state != "unknown"
                    else self.env._("Chưa xác định")
                )
                note = self.env["tp.project.update"].search(
                    [("package_id", "=", r.id)],
                    order="id desc",
                    limit=1,
                )
                r.last_note = note.reason[:180] if note else False

    def _read_format(self, fnames, load="_classic_read"):
        self.invalidate_recordset(
            [
                n
                for n in fnames
                if n
                in (
                    "can_edit",
                    "can_note",
                    "can_update_status",
                    "can_read_money",
                    "can_edit_money",
                    "budget_display",
                    "last_note",
                )
            ],
        )
        return super()._read_format(fnames, load=load)

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for supplied in vals_list:
            vals = {
                **self.default_get(["project_id", "owner_id", "stage", "outcome"]),
                **supplied,
            }
            p = self.env["project.project"].browse(vals.get("project_id"))
            p.check_access("read")
            if not p.tp_managed:
                raise ValidationError(self.env._("Gói thầu cần dự án TANPHAT."))
            if not self.env.su and (
                not p._kd_has("bid") or (vals.get("owner_id") != self.env.uid and not p._tp_head_allowed())
            ):
                raise AccessError(
                    self.env._("Chỉ tạo gói do mình phụ trách trong scope được cấp."),
                )
            if (
                vals.get("stage", "tracking") != "tracking"
                or vals.get("outcome", "unknown") != "unknown"
            ):
                raise UserError(self.env._("Tạo gói theo dõi, chưa xác định kết quả."))
            prepared.append(vals)
        return super().create(prepared)

    def write(self, vals):
        if self.env.context.get("_kd_internal") is not _INTERNAL:
            if set(vals) & {
                "project_id",
                "company_id",
                "owner_id",
                "stage",
                "outcome",
                "amount_ids",
            }:
                raise AccessError(
                    self.env._(
                        "Phạm vi/owner/tình trạng/tiền phải qua thao tác riêng.",
                    ),
                )
            for r in self:
                if not r.project_id._kd_has("bid") or (r.owner_id != self.env.user and not r.project_id._tp_head_allowed()):
                    raise AccessError(
                        self.env._("Chưa có quyền sửa gói thầu của mình."),
                    )
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._("Không xóa gói thầu có mã/lịch sử."))

    def action_kd_status(self):
        self.ensure_one()
        return self.project_id._kd_wizard("bid", self)

    def action_kd_note(self):
        self.ensure_one()
        return self.project_id._kd_wizard("note", self)

    def action_kd_history(self):
        self.ensure_one()
        action = self.project_id.action_kd_history()
        action["domain"] = [
            ("project_id", "=", self.project_id.id),
            ("package_id", "=", self.id),
        ]
        return action

    def action_kd_attempts(self):
        self.ensure_one()
        return open_records(
            self.env,
            "crm.lead",
            [("kd_package_id", "=", self.id)],
            "Các lần tham gia",
            {
                "default_tp_project_id": self.project_id.id,
                "default_kd_package_id": self.id,
                "default_partner_id": self.project_id.partner_id.id,
                "default_company_id": self.company_id.id,
                "default_type": "opportunity",
            },
        )

    def action_kd_amounts(self):
        self.ensure_one()
        self.check_access("read")
        if not self.project_id._kd_money_read():
            raise AccessError(self.env._("Chưa có quyền đọc giá trị gói."))
        return open_records(
            self.env,
            "tp.bid.package.amount",
            [("package_id", "=", self.id)],
            "Giá trị theo từng nghĩa",
            {"default_package_id": self.id},
        )

    @api.model
    def get_kd_ui_permissions(self):
        self.check_access("read")
        return {
            "create": any(
                p._kd_has("bid")
                for p in self.env["project.project"].search([("tp_managed", "=", True)])
            ),
        }


class PackageAmount(models.Model):
    _name = "tp.bid.package.amount"
    _description = "Giá gói, giá chào và phần việc công ty tách biệt"
    _check_company_auto = True
    package_id = fields.Many2one(
        "tp.bid.package",
        required=True,
        ondelete="restrict",
        check_company=True,
    )
    project_id = fields.Many2one(related="package_id.project_id", store=True)
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    kind = fields.Selection(
        [
            ("package_total", "Tổng dự kiến giá gói"),
            ("company_offer", "Giá công ty chào"),
            ("company_share", "Phần việc công ty dự kiến nhận"),
        ],
        required=True,
    )
    amount_state = fields.Selection(
        [("unknown", "Chưa xác định"), ("estimated", "Ước tính có nguồn")],
        default="unknown",
        required=True,
    )
    value = PackageValue(string="Giá trị", prefetch=False)
    display_value = fields.Char(compute="_compute_display_value", string="Giá trị")
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    tax_basis = fields.Selection(
        [
            ("unknown", "Chưa xác định"),
            ("excluding_tax", "Chưa thuế"),
            ("including_tax", "Đã thuế"),
        ],
        default="unknown",
        required=True,
    )
    source = fields.Char(required=True, string="Nguồn ước tính")
    estimate_date = fields.Date(required=True, string="Ngày ước tính")
    version = fields.Integer(default=1, readonly=True, copy=False)
    _kind_unique = models.Constraint(
        "UNIQUE(package_id,kind)",
        "Mỗi nghĩa tiền chỉ có một giá hiện tại cho gói.",
    )

    def _compute_display_value(self):
        for r in self:
            r.display_value = (
                self.env._("Chưa xác định")
                if r.amount_state == "unknown"
                else formatLang(self.env, r.value, currency_obj=r.currency_id)
            )

    def _kd_read_guard(self):
        if not self.env.su:
            for r in self:
                if not r.sudo().project_id.with_env(self.env)._kd_money_read():
                    raise AccessError(
                        self.env._("Bạn không còn quyền đọc giá gói trong dự án."),
                    )

    def read(self, fields=None, load="_classic_read"):
        self._kd_read_guard()
        return super().read(fields=fields, load=load)

    def export_data(self, fields_to_export):
        self._kd_read_guard()
        return super().export_data(fields_to_export)

    def _require_edit(self):
        for r in self:
            r.project_id.check_access("read")
            if not self.env.su and (
                not r.project_id._kd_has("bid")
                or (r.package_id.owner_id != self.env.user and not r.project_id._tp_head_allowed())
                or not r.project_id._kd_money_read()
                or not self.env["tp.project.grant"]._tp_has_capability(
                    r.project_id,
                    "financial_draft_edit",
                    r.project_id.tp_department_id,
                )
            ):
                raise AccessError(
                    self.env._(
                        "Cần quyền lập gói, đọc tiền và sửa tiền của đúng dự án.",
                    ),
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "version" in vals:
                raise AccessError(self.env._("Phiên bản do máy chủ quản lý."))
            self.new(vals)._require_edit()
        records = super().create(vals_list)
        for r in records:
            r._record_change(None)
        return records

    def _snapshot(self):
        self.ensure_one()
        return {
            key: str(self[key])
            for key in (
                "kind",
                "amount_state",
                "value",
                "currency_id",
                "tax_basis",
                "source",
                "estimate_date",
                "version",
            )
        }

    def _record_change(self, before):
        p = self.project_id
        p.invalidate_recordset()
        p._kd_apply(
            "amount",
            self.source,
            p.kd_version,
            uuid.uuid4().hex,
            {"before": before, "after": self._snapshot()},
            self.package_id,
        )

    def write(self, vals):
        if vals.get("amount_state") == "unknown":
            vals = {**vals, "value": 0}
        self._require_edit()
        if set(vals) & {"package_id", "project_id", "company_id", "kind"}:
            raise AccessError(self.env._("Không chuyển scope hoặc nghĩa số tiền."))
        for r in self:
            self.env.cr.execute(
                SQL(
                    "SELECT id FROM project_project WHERE id=%s FOR UPDATE",
                    r.project_id.id,
                ),
            )
            self.env.cr.execute(
                SQL(
                    "SELECT id FROM tp_bid_package_amount WHERE id=%s FOR UPDATE",
                    r.id,
                ),
            )
            r.invalidate_recordset()
            if vals.get("version") != r.version:
                raise UserError(self.env._("Giá vừa thay đổi. Tải lại trước khi sửa."))
            before = r._snapshot()
            super(PackageAmount, r).write({**vals, "version": r.version + 1})
            r._record_change(before)
        return True

    def unlink(self):
        raise AccessError(self.env._("Không xóa dữ liệu tiền đã ghi nguồn."))

    @api.model
    def get_kd_ui_permissions(self):
        self.check_access("read")
        packages = self.env["tp.bid.package"].search([])
        return {"create": any(p.can_edit_money for p in packages)}

    @api.constrains("value", "amount_state", "source", "estimate_date")
    def _check_amount(self):
        for r in self:
            if (
                r.value < 0
                or (r.amount_state == "unknown" and r.value != 0)
                or not (r.source or "").strip()
            ):
                raise ValidationError(self.env._("Giá ước tính không âm và cần nguồn."))


class ProjectUpdate(models.Model):
    _name = "tp.project.update"
    _description = "Nhật ký quản trị dự án append-only"
    _order = "id desc"
    project_id = fields.Many2one("project.project", required=True, ondelete="restrict")
    package_id = fields.Many2one("tp.bid.package", ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    actor_id = fields.Many2one("res.users", required=True)
    kind = fields.Selection(
        [
            ("status", "Tình trạng"),
            ("note", "Ghi chú / đính chính"),
            ("metadata", "Thông tin"),
            ("bid", "Dự thầu"),
            ("amount", "Giá trị gói"),
            ("party", "Các bên tham gia"),
            ("party_revoke", "Ngừng quan hệ tham gia"),
        ],
        required=True,
    )
    state_before = fields.Char()
    state_after = fields.Char()
    reason = fields.Text(required=True, string="Nội dung / căn cứ")
    version = fields.Integer(required=True)
    request_key = fields.Char(required=True)
    payload_hash = fields.Char(required=True)
    correction_id = fields.Many2one(
        "tp.project.update",
        ondelete="restrict",
        string="Đính chính mục",
    )
    _key_unique = models.Constraint(
        "UNIQUE(project_id,actor_id,request_key)",
        "Mã thao tác đã tồn tại.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("_kd_internal") is not _INTERNAL:
            raise AccessError(self.env._("Nhật ký chỉ sinh từ thao tác backend."))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._("Nhật ký không được sửa."))

    def unlink(self):
        raise AccessError(self.env._("Nhật ký không được xóa."))


class ProjectCommand(models.TransientModel):
    _name = "tp.project.command"
    _description = "Cập nhật dự án theo capability"
    project_id = fields.Many2one("project.project", required=True, readonly=True)
    package_id = fields.Many2one("tp.bid.package", readonly=True)
    kind = fields.Selection(
        [
            ("status", "Cập nhật tình trạng"),
            ("note", "Thêm ghi chú"),
            ("metadata", "Cập nhật thông tin"),
            ("bid", "Cập nhật dự thầu"),
            ("party_revoke", "Ngừng quan hệ tham gia"),
        ],
        required=True,
        readonly=True,
    )
    participation_id = fields.Many2one(
        "tp.project.participation",
        string="Quan hệ cần ngừng",
    )
    expected_version = fields.Integer(readonly=True)
    request_key = fields.Char(readonly=True)
    target_state = fields.Selection(LIFECYCLE, string="Tình trạng mới")
    bid_stage = fields.Selection(BID_STAGE, string="Tiến trình")
    bid_outcome = fields.Selection(OUTCOME, string="Kết quả khai báo")
    investor_id = fields.Many2one("res.partner", string="Chủ đầu tư")
    project_name = fields.Char(string="Tên dự án")
    scope = fields.Text(string="Phạm vi / đầu ra")
    reason = fields.Text(string="Ghi chú / căn cứ")
    correction_id = fields.Many2one("tp.project.update", string="Đính chính mục trước")

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for supplied in vals_list:
            p = self.env["project.project"].browse(supplied.get("project_id"))
            p.check_access("read")
            package = self.env["tp.bid.package"].browse(supplied.get("package_id"))
            if package and package.project_id != p:
                raise AccessError(self.env._("Gói phải cùng dự án."))
            prepared.append(
                {
                    **supplied,
                    "expected_version": p.kd_version,
                    "request_key": uuid.uuid4().hex,
                    "project_name": p.name,
                    "investor_id": p.kd_investor_id.id,
                    "scope": p.kd_scope,
                    "bid_stage": package.stage if package else False,
                    "bid_outcome": package.outcome if package else False,
                },
            )
        return super().create(prepared)

    def write(self, vals):
        if set(vals) & {
            "project_id",
            "package_id",
            "kind",
            "expected_version",
            "request_key",
        }:
            raise AccessError(self.env._("Đích và phiên bản do máy chủ quản lý."))
        return super().write(vals)

    def action_confirm(self):
        self.ensure_one()
        self.check_access("read")
        payload = {
            "status": {"state": self.target_state},
            "note": {"correction_id": self.correction_id.id},
            "metadata": {
                "name": self.project_name,
                "kd_investor_id": self.investor_id.id,
                "kd_scope": self.scope,
            },
            "bid": {"stage": self.bid_stage, "outcome": self.bid_outcome},
            "party_revoke": {"participation_id": self.participation_id.id},
        }[self.kind]
        self.project_id._kd_apply(
            self.kind,
            self.reason,
            self.expected_version,
            self.request_key,
            payload,
            self.package_id,
        )
        return {"type": "ir.actions.act_window_close"}


class Opportunity(models.Model):
    _inherit = "crm.lead"
    kd_package_id = fields.Many2one(
        "tp.bid.package",
        check_company=True,
        ondelete="restrict",
        string="Gói thầu",
    )
    kd_investor_id = fields.Many2one(
        related="tp_project_id.kd_investor_id",
        string="Chủ đầu tư",
    )

    @api.constrains("tp_project_id", "kd_package_id", "kd_route")
    def _check_package(self):
        for lead in self.filtered("kd_package_id"):
            lead.kd_package_id.check_access("read")
            if (
                lead.kd_route != "bid"
                or lead.kd_package_id.project_id != lead.tp_project_id
            ):
                raise ValidationError(
                    self.env._(
                        "Gói thầu phải cùng dự án; giao trực tiếp không dùng gói thầu giả.",
                    ),
                )
