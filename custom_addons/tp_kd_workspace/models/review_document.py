"""Code reuse for typed KD dossiers; no shared business transaction table."""

import hashlib
import json
import uuid

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Domain
from odoo.tools import SQL

from .workspace import _INTERNAL, kd_leaf

TYPED_MODELS = ("tp.allocation", "tp.production", "tp.acceptance", "tp.payment.request",
                "tp.periodic.plan", "tp.credential", "tp.obligation")


class ReviewDocument(models.AbstractModel):
    _name = "tp.kd.review.document"
    _description = "Typed dossier review helpers"
    _check_company_auto = True
    _order = "date desc, id desc"
    _kd_domain = None
    _kd_money_model = None
    _kd_snapshot_fields = ()
    _kd_amount_snapshot_fields = ()

    code = fields.Char(string="Mã hồ sơ", required=True, copy=False, index=True)
    name = fields.Char(string="Tên hồ sơ", required=True)
    project_id = fields.Many2one(
        "project.project",
        required=True,
        ondelete="restrict",
        check_company=True,
        string="Dự án",
    )
    company_id = fields.Many2one(
        related="project_id.company_id",
        store=True,
        precompute=True,
    )
    department_id = fields.Many2one(
        related="project_id.tp_department_id",
        store=True,
        string="Phòng chủ trì",
    )
    owner_id = fields.Many2one(
        "res.users",
        required=True,
        default=lambda self: self.env.user,
        ondelete="restrict",
        string="Người phụ trách",
    )
    reviewer_id = fields.Many2one(
        "res.users",
        required=True,
        ondelete="restrict",
        string="Người rà soát",
    )
    date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        string="Ngày hồ sơ",
    )
    date_due = fields.Date(string="Hạn xử lý")
    period_from = fields.Date(string="Từ kỳ")
    period_to = fields.Date(string="Đến kỳ")
    scope = fields.Text(required=True, string="Phạm vi / đầu ra")
    contract_id = fields.Many2one(
        "tp.contract",
        ondelete="restrict",
        check_company=True,
        string="Hợp đồng nguồn",
    )
    task_id = fields.Many2one(
        "project.task",
        ondelete="restrict",
        check_company=True,
        string="Công việc nguồn",
    )
    version = fields.Integer(default=1, readonly=True, copy=False)
    last_reason = fields.Text(readonly=True, string="Ý kiến / lý do gần nhất")
    intervention_reason = fields.Text(string="Lý do can thiệp nháp", store=False)
    can_manage = fields.Boolean(compute="_compute_kd_allowed")
    can_take_review = fields.Boolean(compute="_compute_kd_allowed")
    can_prepare = fields.Boolean(compute="_compute_kd_allowed")
    can_submit = fields.Boolean(compute="_compute_kd_allowed")
    can_review = fields.Boolean(compute="_compute_kd_allowed")
    can_read_money = fields.Boolean(compute="_compute_kd_allowed")
    eligible_reviewer_ids = fields.Many2many("res.users", compute="_compute_kd_allowed")

    @api.depends_context("uid")
    @api.depends("project_id", "owner_id", "reviewer_id")
    def _compute_kd_allowed(self):
        for rec in self:
            grant = self.env["tp.kd.grant"]
            head = rec._kd_is_head()
            rec.can_manage = head
            rec.can_take_review = bool(head and rec.state == "in_review" and rec._kd_review_eligible() and rec.reviewer_id != self.env.user)
            rec.can_prepare = bool(
                rec.project_id
                and (rec.owner_id == self.env.user or head)
                and grant._has(rec.project_id, self._kd_domain, "prepare"),
            )
            rec.can_submit = bool(
                rec.project_id
                and (rec.owner_id == self.env.user or head)
                and grant._has(rec.project_id, self._kd_domain, "submit"),
            )
            rec.can_review = bool(
                rec.project_id
                and rec.reviewer_id == self.env.user
                and rec._kd_review_eligible()
                and grant._has(rec.project_id, self._kd_domain, "review"),
            )
            rec.can_read_money = rec._kd_money_allowed()
            candidates = (
                self.env["tp.kd.grant"]
                .sudo()
                .search(
                    [
                        ("project_id", "=", rec.project_id.id),
                        ("domain", "=", self._kd_domain),
                        ("capability", "=", "review"),
                        ("active", "=", True),
                    ],
                )
                .user_id
            )
            candidates |= self.env["tp.kd.department.role"]._head_users(rec.project_id) if rec.project_id else self.env["res.users"]
            rec.eligible_reviewer_ids = candidates.filtered(
                lambda u: (
                    u != rec.owner_id
                    and rec._kd_review_eligible(u)
                    and grant._has(rec.project_id, self._kd_domain, "review", u)
                ),
            )

    @api.model
    def get_kd_ui_permissions(self):
        self.check_access("read")
        grants = (
            self.env["tp.kd.grant"]
            .sudo()
            .search(
                [
                    ("user_id", "=", self.env.uid),
                    ("domain", "=", self._kd_domain),
                    ("capability", "=", "prepare"),
                    ("active", "=", True),
                ],
            )
        )
        return {
            "create": bool(self.env["tp.kd.department.role"]._project_ids()) or any(
                self.env["tp.kd.grant"]._has(p, self._kd_domain, "prepare")
                for p in grants.project_id
            ),
        }

    def _kd_is_head(self, user=None):
        self.ensure_one()
        return bool(self.project_id and self.env["tp.kd.department.role"]._is_head(project=self.project_id, user=user))

    def _kd_review_eligible(self, user=None):
        self.ensure_one()
        user = user or self.env.user
        events = self.sudo().event_ids
        submitted = events.filtered(lambda e: e.action == "submit")[-1:]
        boundary = events.filtered(lambda e: e.action == "rework")[-1:]
        current = events.filtered(lambda e: e.id > (boundary.id or 0))
        authors = current.filtered(lambda e: e.action in (
            "head_edit", "head_create", "head_document_add", "head_document_remove")).actor_id
        previous_owners = {json.loads(e.snapshot_before or "{}").get("owner_id") for e in current if e.action == "assign"}
        return bool(user != self.owner_id and user.id not in previous_owners and user not in authors
                    and (not submitted or submitted.actor_id != user))

    def _kd_snapshot(self):
        self.ensure_one()
        values = {name: self[name].id if self._fields[name].type == "many2one" else self[name]
                for name in ("code", "name", "project_id", "owner_id", "reviewer_id", "date", "date_due",
                             "period_from", "period_to", "scope", "contract_id", "task_id", *self._kd_snapshot_fields)}
        documents = self.env["tp.kd.document"].sudo().with_context(active_test=False).search([
            ("target_model", "=", self._name), ("target_id", "=", self.id)])
        values["documents"] = [{"id": doc.id, "checksum": doc.checksum, "active": doc.active,
                                "confidentiality": doc.confidentiality} for doc in documents if doc.confidentiality == "general"]
        return values

    def _kd_money_snapshot(self):
        self.ensure_one()
        return [{"amount_state": amount.amount_state, "value": amount.value, "tax_basis": amount.tax_basis,
                 "currency_id": amount.currency_id.id, **{key: amount[key] for key in self._kd_amount_snapshot_fields}}
                for amount in self.sudo().amount_ids] if self._kd_money_model else []

    def _kd_money_allowed(self, edit=False):
        self.ensure_one()
        if not self.project_id or not self.project_id.has_access("read"):
            return False
        return (
            self.env["tp.project.grant"]._tp_has_capability(
                self.project_id,
                "financial_read",
            )
            and (self._kd_is_head() or bool(
                self.env["tp.project.assignment"]
                .sudo()
                .search_count(
                    [
                        ("project_id", "=", self.project_id.id),
                        ("user_id", "=", self.env.uid),
                        ("active", "=", True),
                    ],
                    limit=1,
                ),
            ))
            and (
                not edit
                or self.env["tp.project.grant"]._tp_has_capability(
                    self.project_id,
                    "financial_draft_edit",
                    self.department_id,
                )
            )
        )

    def _kd_require(self, capability, owner=False):
        self.check_access("read")
        for rec in self:
            if not self.env["tp.kd.grant"]._has(
                rec.project_id,
                self._kd_domain,
                capability,
            ) or (owner and rec.owner_id != self.env.user and not rec._kd_is_head()):
                raise AccessError(
                    self.env._(
                        "Bạn chưa có quyền thao tác hồ sơ này trong dự án được phân công.",
                    ),
                )

    @api.model
    def _kd_check_targets(self, vals):
        for name, field in self._fields.items():
            if (
                name in vals
                and field.type == "many2one"
                and vals[name]
                and field.comodel_name
                not in ("res.users", "res.company", "res.currency")
            ):
                self.env[field.comodel_name].browse(vals[name]).check_access("read")

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(
            ["project_id", "owner_id", "reviewer_id", "contract_id", "task_id"],
        )
        prepared = []
        for supplied in vals_list:
            vals = {**defaults, **supplied}
            if (
                set(vals) & {"last_reason", "event_ids", "company_id", "department_id"}
                or vals.get("state", "draft") != "draft"
                or vals.get("version", 1) != 1
            ):
                raise UserError(
                    self.env._("Trạng thái, phiên bản và lịch sử do máy chủ quản lý."),
                )
            self._kd_check_targets(vals)
            project = self.env["project.project"].browse(vals.get("project_id"))
            if not self.env.su and (
                (vals.get("owner_id") != self.env.uid and not self.env["tp.kd.department.role"]._is_head(project=project))
                or not self.env["tp.kd.grant"]._has(project, self._kd_domain, "prepare")
            ):
                raise AccessError(
                    self.env._("Cần quyền lập hồ sơ và phải là người phụ trách."),
                )
            if not self.env.su and vals.get("owner_id") != self.env.uid:
                owner = self.env["res.users"].sudo().browse(vals.get("owner_id")).exists()
                if not owner.active or not self.env["tp.kd.grant"]._has(project, self._kd_domain, "prepare", owner):
                    raise AccessError(self.env._("Người phụ trách phải còn quyền lập hồ sơ cùng dự án/phòng."))
            vals["code"] = (vals.get("code") or "").strip().upper()
            prepared.append(vals)
        records = (
            super(ReviewDocument, self.with_context(_kd_internal=_INTERNAL))
            .create(
                prepared,
            )
            .with_env(self.env)
        )
        for record in records:
            if record._kd_is_head():
                record._kd_event("head_create", "draft", "Lập hồ sơ trong phòng")
        return records

    def _kd_lock(self):
        self.ensure_one()
        self.env.flush_all()
        self.env.cr.execute(
            SQL(
                "SELECT version FROM %s WHERE id=%s FOR UPDATE",
                SQL.identifier(self._table),
                self.id,
            ),
        )
        self.env.invalidate_all()

    def write(self, vals):
        if self.env.context.get("_kd_internal") is _INTERNAL:
            return super().write(vals)
        self.ensure_one()
        self.check_access("write")
        self._kd_require("prepare", owner=True)
        if set(vals) & {
            "state",
            "project_id",
            "company_id",
            "department_id",
            "owner_id",
            "event_ids",
            "last_reason",
        }:
            raise UserError(
                self.env._("Không đổi trực tiếp trạng thái, phạm vi hoặc lịch sử."),
            )
        self._kd_lock()
        self._kd_require("prepare", owner=True)
        if self.state != "draft" or vals.get("version") != self.version:
            raise UserError(
                self.env._("Hồ sơ đã gửi hoặc phiên bản đã cũ. Tải lại trước khi sửa."),
            )
        supplied = dict(vals)
        reason = (supplied.pop("intervention_reason", "") or "").strip()
        head_edit = self._kd_is_head()
        if head_edit and self.owner_id != self.env.user and not reason:
            raise UserError(self.env._("Nhập lý do can thiệp nháp của người khác."))
        before = self._kd_snapshot() if head_edit else None
        money_before = self._kd_money_snapshot() if head_edit else None
        version_before = self.version
        self._kd_check_targets(supplied)
        values = dict(supplied, version=self.version + 1)
        if "code" in values:
            values["code"] = (values["code"] or "").strip().upper()
        result = super(ReviewDocument, self.with_context(_kd_internal=_INTERNAL)).write(values)
        if head_edit:
            self._kd_event("head_edit", "draft", reason or "Cập nhật nháp của mình",
                           snapshot_before=before, version_before=version_before, money_before=money_before)
        return result

    def unlink(self):
        self.check_access("unlink")
        self._kd_require("prepare", owner=True)
        if any(rec.state != "draft" or rec.event_ids for rec in self):
            raise UserError(self.env._("Hồ sơ có lịch sử trình không được xóa vật lý."))
        return super().unlink()

    def copy(self, default=None):
        raise UserError(
            self.env._("Tạo hồ sơ nháp mới với mã riêng; không sao chép lịch sử."),
        )

    @api.constrains(
        "project_id",
        "contract_id",
        "task_id",
        "owner_id",
        "reviewer_id",
        "date",
        "date_due",
        "period_from",
        "period_to",
        "code",
        "scope",
    )
    def _kd_check_integrity(self):
        for rec in self:
            if (
                not rec.project_id.tp_managed
                or not rec.department_id
                or not (rec.code or "").strip()
                or not (rec.scope or "").strip()
                or rec.company_id not in rec.owner_id.company_ids
                or rec.company_id not in rec.reviewer_id.company_ids
                or rec.owner_id == rec.reviewer_id
                or (rec.contract_id and rec.contract_id.project_id != rec.project_id)
                or (rec.task_id and rec.task_id.project_id != rec.project_id)
                or (rec.date_due and rec.date_due < rec.date)
                or bool(rec.period_from) != bool(rec.period_to)
                or (rec.period_from and rec.period_to < rec.period_from)
            ):
                raise ValidationError(
                    self.env._(
                        "Kiểm tra mã/phạm vi, phòng, người lập/rà soát, ngày/kỳ và nguồn cùng dự án.",
                    ),
                )

    def _kd_open_transition(self, action):
        self.ensure_one()
        if action in ("assign", "take_review", "document_add", "document_remove"):
            if not self._kd_is_head() or (action == "take_review" and not self._kd_review_eligible()):
                raise AccessError(self.env._("Cần HEAD đúng phòng và người rà soát độc lập."))
        else:
            self._kd_require(
                "review"
                if action == "return"
                else "submit"
                if action == "submit"
                else "prepare",
                owner=action != "return",
            )
            if action == "return" and self.reviewer_id != self.env.user:
                raise AccessError(
                    self.env._("Chỉ người rà soát được chỉ định mới được trả hồ sơ."),
                )
        wizard = self.env["tp.kd.transition"].create(
            {
                "target_model": self._name,
                "target_id": self.id,
                "action": action,
                "expected_version": self.env.context.get(
                    "kd_expected_version",
                    self.version,
                ),
            },
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "tp.kd.transition",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
            "name": "Thao tác hồ sơ",
        }

    def action_documents(self):
        self.ensure_one()
        self.check_access("read")
        return {"type": "ir.actions.act_window", "name": "Tài liệu hồ sơ", "res_model": "tp.kd.document",
                "view_mode": "list,form", "domain": [("target_model", "=", self._name), ("target_id", "=", self.id)]}

    def action_document_add(self):
        return self._kd_open_transition("document_add")

    def action_document_remove(self):
        return self._kd_open_transition("document_remove")

    def action_assign(self):
        return self._kd_open_transition("assign")

    def action_take_review(self):
        return self._kd_open_transition("take_review")

    def action_submit(self):
        return self._kd_open_transition("submit")

    def action_return(self):
        return self._kd_open_transition("return")

    def action_rework(self):
        return self._kd_open_transition("rework")

    def action_project(self):
        self.ensure_one()
        self.project_id.check_access("read")
        return {
            "type": "ir.actions.act_window",
            "res_model": "project.project",
            "res_id": self.project_id.id,
            "view_mode": "form",
            "views": [(self.env.ref("tp_kd_workspace.project_governance_form").id, "form")],
            "target": "current",
            "context": kd_leaf("project.project"),
        }

    def _kd_event(self, action, before, reason=None, fix_summary=None, *, snapshot_before=None,
                  version_before=None, money_before=None):
        values = self._kd_snapshot()
        event = (
            self.env[self._name + ".event"]
            .sudo()
            .with_context(_kd_internal=_INTERNAL)
            .create(
                {
                    "record_id": self.id,
                    "actor_id": self.env.uid,
                    "action": action,
                    "state_before": before,
                    "state_after": self.state,
                    "version": self.version,
                    "reason": reason,
                    "fix_summary": fix_summary,
                    "snapshot": json.dumps(values, default=str, ensure_ascii=False),
                    "snapshot_before": json.dumps(snapshot_before, default=str, ensure_ascii=False) if snapshot_before is not None else False,
                    "version_before": version_before if version_before is not None else (0 if action == "head_create" else max(1, self.version - 1)),
                },
            )
        )
        if action == "submit" and self._kd_money_model:
            for amount in self.sudo().amount_ids:
                self.env[self._name + ".event.amount"].sudo().with_context(
                    _kd_internal=_INTERNAL,
                ).create(
                    {
                        "event_id": event.id,
                        "amount_state": amount.amount_state,
                        "value": amount.value,
                        "tax_basis": amount.tax_basis,
                        "currency_id": amount.currency_id.id,
                        **{key: amount[key] for key in self._kd_amount_snapshot_fields},
                    },
                )
        if action == "head_edit" and self._kd_money_model:
            for side, amounts in (("before", money_before or []), ("after", self._kd_money_snapshot())):
                for amount in amounts:
                    self.env[self._name + ".event.amount"].sudo().with_context(_kd_internal=_INTERNAL).create(
                        dict(amount, event_id=event.id, snapshot_side=side))
        return event

    def _kd_validate_sources(self):
        """Typed models recheck their source integrity at submission."""

    def _kd_transition(self, wizard):
        self.ensure_one()
        with self.env.cr.savepoint():
            if wizard.action in ("document_add", "document_remove"):
                return self._kd_document_change(wizard)
            if wizard.action in ("assign", "take_review"):
                return self._kd_coordinate(wizard)
            self._kd_require(
                "review"
                if wizard.action == "return"
                else "submit"
                if wizard.action == "submit"
                else "prepare",
                owner=wizard.action != "return",
            )
            self._kd_lock()
            self._kd_require("review" if wizard.action == "return" else "submit" if wizard.action == "submit" else "prepare",
                             owner=wizard.action != "return")
            if wizard.action == "return" and (self.reviewer_id != self.env.user or not self._kd_review_eligible()):
                raise AccessError(
                    self.env._("Chỉ người rà soát được chỉ định được trả lại."),
                )
            if wizard.expected_version != self.version:
                raise UserError(
                    self.env._("Hồ sơ vừa thay đổi. Tải lại và mở thao tác mới."),
                )
            target = {
                "submit": ("draft", "in_review"),
                "return": ("in_review", "returned"),
                "rework": ("returned", "draft"),
            }
            before, after = target[wizard.action]
            if self.state != before:
                raise UserError(
                    self.env._("Trạng thái hồ sơ đã thay đổi. Tải lại để tiếp tục."),
                )
            if (
                wizard.action in ("return", "rework")
                and not (wizard.reason or "").strip()
            ):
                raise UserError(self.env._("Cần nhập lý do trước khi xác nhận."))
            if wizard.action == "submit":
                if not self._kd_review_eligible(self.reviewer_id) or not self.env["tp.kd.grant"]._has(
                    self.project_id,
                    self._kd_domain,
                    "review",
                    self.reviewer_id,
                ):
                    raise UserError(
                        self.env._("Người rà soát không còn đủ quyền trong dự án."),
                    )
                if (
                    self.event_ids.filtered(lambda e: e.action == "return")
                    and not (wizard.fix_summary or "").strip()
                ):
                    raise UserError(
                        self.env._("Mô tả nội dung đã bổ sung trước khi gửi lại."),
                    )
                self._kd_check_integrity()
                self._kd_validate_sources()
            self.with_context(_kd_internal=_INTERNAL).write(
                {
                    "state": after,
                    "version": self.version + 1,
                    **(
                        {"last_reason": wizard.reason}
                        if wizard.action in ("return", "rework")
                        else {}
                    ),
                },
            )
            self._kd_event(wizard.action, before, wizard.reason, wizard.fix_summary)
        return None

    def _kd_document_change(self, wizard):
        if not self._kd_is_head():
            raise AccessError(self.env._("Chỉ HEAD đúng phòng được quản lý tài liệu hồ sơ."))
        self._kd_require("prepare", owner=True)
        self._kd_lock()
        if not self._kd_is_head():
            raise AccessError(self.env._("Quyền HEAD đã bị thu hồi."))
        self._kd_require("prepare", owner=True)
        if self.state != "draft" or self.version != wizard.expected_version:
            raise UserError(self.env._("Tài liệu chỉ thay đổi trên nháp đúng phiên bản đã mở."))
        if not (wizard.reason or "").strip():
            raise UserError(self.env._("Cần lý do thay tài liệu nháp."))
        before = self._kd_snapshot()
        version = self.version
        Document = self.env["tp.kd.document"].sudo().with_context(_kd_internal=_INTERNAL)
        if wizard.action == "document_add":
            if not wizard.file or not wizard.file_name or not (wizard.document_name or "").strip():
                raise UserError(self.env._("Chọn tệp và nhập tên tài liệu."))
            if wizard.confidentiality == "financial" and not self._kd_money_allowed(edit=True):
                raise AccessError(self.env._("Cần quyền sửa tiền nháp để thêm tài liệu tài chính."))
            if wizard.file.size > 20_000_000:
                raise UserError(self.env._("Tệp tối đa 20 MB."))
            document = Document.create({"target_model": self._name, "target_id": self.id,
                "project_id": self.project_id.id, "name": wizard.document_name, "file_name": wizard.file_name,
                "confidentiality": wizard.confidentiality, "file": wizard.file,
                "added_version": version + 1, "actor_id": self.env.uid, "reason": wizard.reason,
                "checksum": hashlib.sha256(bytes(wizard.file)).hexdigest()})
        else:
            document = wizard.document_id
            document.check_access("read")
            if document.target_model != self._name or document.target_id != self.id or not document.active:
                raise AccessError(self.env._("Tài liệu không thuộc hồ sơ nháp này."))
            if document.confidentiality == "financial" and not self._kd_money_allowed(edit=True):
                raise AccessError(self.env._("Cần quyền sửa tiền nháp để gỡ tài liệu tài chính."))
            if document.added_version <= max(self.event_ids.filtered(lambda e: e.action == "submit").mapped("version"), default=0):
                raise UserError(self.env._("Tài liệu đã làm căn cứ lần trình phải được giữ nguyên."))
            document.sudo().with_context(_kd_internal=_INTERNAL).write({"active": False,
                "archived_by_id": self.env.uid, "archived_at": fields.Datetime.now(), "archive_reason": wizard.reason})
        self.with_context(_kd_internal=_INTERNAL).write({"version": version + 1})
        action = "head_" + wizard.action if self._kd_is_head() else wizard.action
        self._kd_event(action, "draft", wizard.reason, snapshot_before=before, version_before=version)
        return

    def _kd_coordinate(self, wizard):
        if not self._kd_is_head():
            raise AccessError(self.env._("Chỉ HEAD trong phòng được điều phối hồ sơ."))
        self._kd_lock()
        if not self._kd_is_head():
            raise AccessError(self.env._("Quyền HEAD đã bị thu hồi."))
        if wizard.expected_version != self.version:
            raise UserError(self.env._("Hồ sơ vừa thay đổi. Tải lại trước khi điều phối."))
        if not (wizard.reason or "").strip():
            raise UserError(self.env._("Cần lý do điều phối."))
        before, version = self._kd_snapshot(), self.version
        if wizard.action == "take_review":
            if self.state != "in_review" or not self._kd_review_eligible():
                raise AccessError(self.env._("Không nhận rà soát hồ sơ do mình lập/gửi/can thiệp."))
            values = {"reviewer_id": self.env.uid}
        else:
            if self.state not in ("draft", "returned"):
                raise UserError(self.env._("Chỉ điều phối nháp hoặc hồ sơ đã trả lại."))
            owner, reviewer = wizard.owner_id, wizard.reviewer_id
            grant = self.env["tp.kd.grant"]
            if (not owner.active or not reviewer.active or owner == reviewer
                    or not grant._has(self.project_id, self._kd_domain, "prepare", owner)
                    or not grant._has(self.project_id, self._kd_domain, "review", reviewer)
                    or not self._kd_review_eligible(reviewer)):
                raise AccessError(self.env._("Người xử lý/rà soát phải có quyền cùng dự án/phòng và độc lập."))
            values = {"owner_id": owner.id, "reviewer_id": reviewer.id}
        self.with_context(_kd_internal=_INTERNAL).write(dict(values, version=version + 1))
        self._kd_event(wizard.action, self.state, wizard.reason, snapshot_before=before, version_before=version)


class Transition(models.TransientModel):
    _name = "tp.kd.transition"
    _description = "Thao tác hồ sơ KH-KD"
    target_model = fields.Char(readonly=True, required=True)
    target_id = fields.Integer(readonly=True, required=True)
    project_id = fields.Many2one("project.project", readonly=True, required=True)
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    action = fields.Selection(
        [("submit", "Gửi rà soát"), ("return", "Trả lại"), ("rework", "Mở bản sửa"), ("assign", "Phân công"), ("take_review", "Nhận rà soát"), ("document_add", "Thêm tài liệu nháp"), ("document_remove", "Gỡ tài liệu nháp")],
        required=True,
        readonly=True,
    )
    expected_version = fields.Integer(readonly=True, required=True)
    key = fields.Char(readonly=True)
    done = fields.Boolean(readonly=True)
    reason = fields.Text(string="Lý do / ý kiến")
    fix_summary = fields.Text(string="Nội dung đã bổ sung")
    owner_id = fields.Many2one("res.users", string="Người phụ trách mới")
    reviewer_id = fields.Many2one("res.users", string="Người rà soát mới")
    eligible_owner_ids = fields.Many2many("res.users", compute="_compute_recipients")
    eligible_reviewer_ids = fields.Many2many("res.users", compute="_compute_recipients")
    document_id = fields.Many2one("tp.kd.document", string="Tài liệu cần gỡ")
    document_name = fields.Char(string="Tên tài liệu")
    confidentiality = fields.Selection([("financial", "Tài chính"), ("general", "Thông thường")], default="financial", required=True)
    file = fields.Binary(string="Tệp")
    file_name = fields.Char(string="Tên tệp")

    @api.depends("target_model", "target_id", "owner_id")
    @api.depends_context("uid", "allowed_company_ids")
    def _compute_recipients(self):
        for wizard in self:
            owners = reviewers = self.env["res.users"]
            if wizard.target_model in TYPED_MODELS and wizard.target_id:
                record = self.env[wizard.target_model].browse(wizard.target_id)
                record.check_access("read")
                candidates = self.env["tp.project.assignment"].sudo().search([
                    ("project_id", "=", record.project_id.id), ("active", "=", True)]).user_id
                candidates |= self.env["tp.kd.department.role"]._head_users(record.project_id)
                grant = self.env["tp.kd.grant"]
                owners = candidates.filtered(lambda user: user.active and
                    grant._has(record.project_id, record._kd_domain, "prepare", user))
                reviewers = candidates.filtered(lambda user: user.active and user != wizard.owner_id
                    and record._kd_review_eligible(user) and grant._has(record.project_id, record._kd_domain, "review", user))
            wizard.eligible_owner_ids, wizard.eligible_reviewer_ids = owners, reviewers

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for vals in vals_list:
            if vals.get("target_model") not in TYPED_MODELS:
                raise AccessError(self.env._("Loại hồ sơ không được phép."))
            record = self.env[vals["target_model"]].browse(vals.get("target_id"))
            record.check_access("read")
            prepared.append(
                dict(
                    vals,
                    project_id=record.project_id.id,
                    key=uuid.uuid4().hex,
                    done=False,
                    owner_id=record.owner_id.id,
                    reviewer_id=record.reviewer_id.id,
                ),
            )
        return super().create(prepared).with_env(self.env)

    def write(self, vals):
        self.check_access("write")
        if self.env.context.get("_kd_internal") is not _INTERNAL and set(vals) - {
            "reason",
            "fix_summary", "owner_id", "reviewer_id", "document_id", "document_name", "confidentiality", "file", "file_name",
        }:
            raise UserError(
                self.env._("Đích và phiên bản thao tác do máy chủ quản lý."),
            )
        if (
            any(self.mapped("done"))
            and self.env.context.get("_kd_internal") is not _INTERNAL
        ):
            raise UserError(self.env._("Thao tác đã hoàn tất; mở thao tác mới."))
        return super().write(vals)

    def action_confirm(self):
        self.ensure_one()
        self.check_access("write")
        if self.create_uid != self.env.user:
            raise AccessError(self.env._("Hộp thao tác thuộc phiên khác."))
        record = self.env[self.target_model].browse(self.target_id)
        record.check_access("read")
        if self.action in ("assign", "take_review"):
            if not record._kd_is_head():
                raise AccessError(self.env._("Quyền HEAD đã bị thu hồi hoặc ngoài phòng."))
        else:
            record._kd_require(
                "review"
                if self.action == "return"
                else "submit"
                if self.action == "submit"
                else "prepare",
                owner=self.action != "return",
            )
        # Serialize duplicate confirmations of this server-created immutable key.
        self.env.flush_all()
        self.env.cr.execute(
            SQL("SELECT id FROM tp_kd_transition WHERE id=%s FOR UPDATE", self.id),
        )
        self.invalidate_recordset()
        if not self.done:
            record._kd_transition(self)
            self.with_context(_kd_internal=_INTERNAL).write({"done": True})
        return {
            "type": "ir.actions.act_window",
            "res_model": record._name,
            "res_id": record.id,
            "view_mode": "form",
            "target": "current",
            "context": dict(self.env.context, kd_loaded_version=record.version, **kd_leaf(record._name)),
        }

    def copy(self, default=None):
        raise UserError(self.env._("Mở thao tác mới từ hồ sơ."))


class Event(models.AbstractModel):
    _name = "tp.kd.event.mixin"
    _description = "Immutable typed dossier audit helper"
    _order = "id"
    actor_id = fields.Many2one(
        "res.users",
        required=True,
        readonly=True,
        string="Người thực hiện",
    )
    acted_at = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
        string="Thời điểm",
    )
    action = fields.Char(readonly=True, string="Thao tác")
    state_before = fields.Char(readonly=True, string="Trước")
    state_after = fields.Char(readonly=True, string="Sau")
    version = fields.Integer(readonly=True, string="Phiên bản")
    reason = fields.Text(readonly=True, string="Lý do")
    fix_summary = fields.Text(readonly=True, string="Bổ sung")
    snapshot = fields.Text(readonly=True)
    snapshot_before = fields.Text(readonly=True)
    version_before = fields.Integer(readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("_kd_internal") is not _INTERNAL:
            raise AccessError(self.env._("Lịch sử chỉ do action tạo."))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._("Lịch sử bất biến."))

    def unlink(self):
        raise AccessError(self.env._("Giữ nguyên lịch sử hồ sơ."))


class Amount(models.AbstractModel):
    _name = "tp.kd.amount.mixin"
    _description = "Protected typed amount helper"
    snapshot_side = fields.Selection([("before", "Trước"), ("after", "Sau")], default="after", readonly=True)
    amount_state = fields.Selection(
        [
            ("unconfirmed", "Chưa xác nhận"),
            ("confirmed", "Đã xác nhận trong tình huống"),
        ],
        default="unconfirmed",
        required=True,
        string="Căn cứ giá trị",
    )
    value = fields.Monetary(currency_field="currency_id", string="Giá trị minh họa")
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
        string="Tiền tệ",
    )
    tax_basis = fields.Selection(
        [
            ("unknown", "Chưa rõ cơ sở"),
            ("excluding_tax", "Chưa thuế — giả định"),
            ("including_tax", "Gồm thuế — giả định"),
        ],
        default="unknown",
        required=True,
        string="Cơ sở thuế",
    )

    def _kd_read_guard(self):
        if self.env.su:
            return
        for amount in self:
            project = amount.sudo().project_id.with_env(self.env)
            if (
                not project.has_access("read")
                or not self.env["tp.project.grant"]._tp_has_capability(
                    project,
                    "financial_read",
                )
                or (not project._tp_head_allowed() and not self.env["tp.project.assignment"]
                .sudo()
                .search_count(
                    [
                        ("project_id", "=", project.id),
                        ("user_id", "=", self.env.uid),
                        ("active", "=", True),
                    ],
                    limit=1,
                ))
            ):
                raise AccessError(
                    self.env._("Bạn không còn quyền đọc giá trị hồ sơ trong dự án."),
                )

    def read(self, fields=None, load="_classic_read"):
        self._kd_read_guard()
        return super().read(fields=fields, load=load)

    def export_data(self, fields_to_export):
        self._kd_read_guard()
        return super().export_data(fields_to_export)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("_kd_internal") is not _INTERNAL:
            raise UserError(
                self.env._(
                    "Sửa giá trị qua hồ sơ có phiên bản; không ghi trực tiếp dòng tiền.",
                ),
            )
        if not self.env.su:
            for vals in vals_list:
                record = self.env[self._fields["record_id"].comodel_name].browse(
                    vals.get("record_id"),
                )
                if not record._kd_money_allowed(edit=True):
                    raise AccessError(self.env._("Chưa có quyền sửa giá trị."))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get("_kd_internal") is not _INTERNAL or set(vals) & {
            "record_id",
            "event_id",
        }:
            raise UserError(self.env._("Sửa giá trị qua hồ sơ có phiên bản."))
        if not self.env.su and any(
            not rec.record_id._kd_money_allowed(edit=True) for rec in self
        ):
            raise AccessError(self.env._("Chưa có quyền sửa giá trị."))
        return super().write(vals)

    def unlink(self):
        if self.env.context.get("_kd_internal") is not _INTERNAL:
            raise UserError(self.env._("Không xóa trực tiếp giá trị."))
        if not self.env.su and any(
            not rec.record_id._kd_money_allowed(edit=True) for rec in self
        ):
            raise AccessError(self.env._("Chưa có quyền sửa giá trị."))
        return super().unlink()

    @api.constrains("value", "amount_state", "tax_basis")
    def _check_value(self):
        for amount in self:
            if (
                amount.value < 0
                or (amount.amount_state == "unconfirmed" and amount.value)
                or (
                    amount.amount_state == "confirmed" and amount.tax_basis == "unknown"
                )
            ):
                raise ValidationError(
                    self.env._(
                        "Giá trị không âm; chưa xác nhận thì để trống, đã xác nhận cần cơ sở thuế.",
                    ),
                )


class GuardedDocumentBinary(fields.Binary):
    def __get__(self, record, owner=None):
        if record is not None and record:
            record._kd_read_guard()
        return super().__get__(record, owner)


class KdDocument(models.Model):
    _name = "tp.kd.document"
    _description = "Versioned typed dossier evidence"
    _order = "id desc"
    kd_accessible = fields.Boolean(compute="_compute_accessible", search="_search_kd_accessible")
    target_model = fields.Char(required=True, readonly=True)
    target_id = fields.Integer(required=True, readonly=True)
    project_id = fields.Many2one("project.project", required=True, readonly=True, ondelete="restrict")
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    active = fields.Boolean(default=True, readonly=True)
    name = fields.Char(required=True, readonly=True)
    confidentiality = fields.Selection([("financial", "Tài chính"), ("general", "Thông thường")],
                                      required=True, default="financial", readonly=True)
    file = GuardedDocumentBinary(attachment=True, readonly=True)
    file_name = fields.Char(required=True, readonly=True)
    checksum = fields.Char(required=True, readonly=True)
    actor_id = fields.Many2one("res.users", required=True, readonly=True, ondelete="restrict")
    added_at = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)
    added_version = fields.Integer(required=True, readonly=True)
    reason = fields.Text(required=True, readonly=True)
    archived_by_id = fields.Many2one("res.users", readonly=True, ondelete="restrict")
    archived_at = fields.Datetime(readonly=True)
    archive_reason = fields.Text(readonly=True)

    @api.depends_context("uid")
    def _compute_accessible(self):
        for document in self:
            raw = document.sudo()
            document.kd_accessible = bool(raw.target_model in TYPED_MODELS and
                self.env[raw.target_model].browse(raw.target_id).has_access("read"))

    @api.model
    def _search_kd_accessible(self, operator, value):
        if operator != "in" or set(value) != {True}:
            return NotImplemented
        domain = Domain.FALSE
        for model in TYPED_MODELS:
            domain |= Domain("target_model", "=", model) & Domain("target_id", "in", self.env[model]._search([]))
        return domain

    def _kd_read_guard(self):
        if self.env.su:
            return
        if not self.env.user._is_internal():
            raise AccessError(self.env._("Không chia sẻ tài liệu hồ sơ ra bên ngoài."))
        self.check_access("read")
        for document in self:
            if document.target_model not in TYPED_MODELS:
                raise AccessError(self.env._("Loại hồ sơ không được phép."))
            target = self.env[document.target_model].browse(document.target_id)
            target.check_access("read")
            if document.project_id != target.project_id or (document.confidentiality == "financial" and not target._kd_money_allowed()):
                raise AccessError(self.env._("Không có quyền xem tài liệu của hồ sơ này."))

    def read(self, fields=None, load="_classic_read"):
        self._kd_read_guard()
        return super().read(fields=fields, load=load)

    def export_data(self, fields_to_export):
        self._kd_read_guard()
        return super().export_data(fields_to_export)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("_kd_internal") is not _INTERNAL:
            raise AccessError(self.env._("Thêm tài liệu qua thao tác hồ sơ có phiên bản."))
        for vals in vals_list:
            if vals.get("target_model") not in TYPED_MODELS:
                raise AccessError(self.env._("Loại hồ sơ không được phép."))
            target = self.env[vals["target_model"]].browse(vals.get("target_id")).exists()
            if target.project_id.id != vals.get("project_id") or target.state != "draft":
                raise AccessError(self.env._("Tài liệu phải thuộc nháp đúng dự án."))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get("_kd_internal") is not _INTERNAL or set(vals) - {
            "active", "archived_by_id", "archived_at", "archive_reason"} or vals.get("active") is not False:
            raise AccessError(self.env._("Tài liệu bất biến; gỡ nháp có lý do và giữ tệp."))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._("Giữ nguyên tài liệu và lịch sử hồ sơ."))


class DossierAttachment(models.Model):
    _inherit = "ir.attachment"

    def _kd_dossier_parent(self, mutate=False):
        for attachment in self.sudo():
            if attachment.res_model == "tp.kd.document" and attachment.res_id:
                document = self.env["tp.kd.document"].sudo(False).browse(attachment.res_id).exists()
                document._kd_read_guard()
                if mutate and self.env.context.get("_kd_internal") is not _INTERNAL:
                    raise AccessError(self.env._("Tài liệu hồ sơ chỉ thay đổi qua nháp có phiên bản."))

    def read(self, fields=None, load="_classic_read"):
        self._kd_dossier_parent()
        return super().read(fields=fields, load=load)

    def export_data(self, fields_to_export):
        self._kd_dossier_parent()
        return super().export_data(fields_to_export)

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(["res_model", "res_id", "public", "access_token"])
        for supplied in vals_list:
            values = {**defaults, **supplied}
            if values.get("res_model") == "tp.kd.document" and values.get("res_id"):
                if self.env.context.get("_kd_internal") is not _INTERNAL or values.get("public") or values.get("access_token"):
                    raise AccessError(self.env._("Không tải trực tiếp hoặc chia sẻ công khai tài liệu hồ sơ."))
        return super().create(vals_list)

    def write(self, vals):
        self._kd_dossier_parent(mutate=True)
        if vals.get("res_model") == "tp.kd.document":
            raise AccessError(self.env._("Không chuyển liên kết tài liệu hồ sơ."))
        return super().write(vals)

    def unlink(self):
        self._kd_dossier_parent(mutate=True)
        return super().unlink()


class DossierBinary(models.AbstractModel):
    _inherit = "ir.binary"

    def _find_record(self, xmlid=None, res_model="ir.attachment", res_id=None, access_token=None, field=None):
        record = (self.env.ref(xmlid, False) if xmlid else
                  self.env[res_model].browse(res_id).exists() if res_id and res_model in self.env else None)
        if record and record._name == "ir.attachment":
            record._kd_dossier_parent()
        elif record and record._name == "tp.kd.document":
            record.sudo(False)._kd_read_guard()
        return super()._find_record(xmlid, res_model, res_id, access_token, field)
