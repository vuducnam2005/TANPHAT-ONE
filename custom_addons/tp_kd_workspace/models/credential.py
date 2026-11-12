from datetime import timedelta

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .workspace import open_records


class Credential(models.Model):
    _name = "tp.credential"
    _inherit = "tp.kd.review.document"
    _description = "Hồ sơ năng lực và chứng chỉ tổng hợp"
    _kd_domain = "credential"
    _kd_snapshot_fields = (
        "subject_id",
        "subject_kind",
        "credential_kind",
        "valid_from",
        "valid_to",
        "source_note",
    )
    state = fields.Selection(
        [("draft", "Nháp"), ("in_review", "Đang rà soát"), ("returned", "Bị trả lại")],
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        string="Trạng thái hồ sơ",
    )
    subject_id = fields.Many2one(
        "res.partner",
        required=True,
        ondelete="restrict",
        check_company=True,
        string="Tổ chức / cá nhân tổng hợp",
    )
    subject_kind = fields.Selection(
        [("organization", "Tổ chức"), ("person", "Cá nhân")],
        required=True,
        default="organization",
        string="Loại chủ thể",
    )
    credential_kind = fields.Char(required=True, string="Loại năng lực / chứng chỉ")
    valid_from = fields.Date(required=True, string="Hiệu lực dự kiến")
    valid_to = fields.Date(required=True, string="Hết hạn dự kiến")
    source_note = fields.Text(required=True, string="Nguồn / tình trạng xác minh")
    expiry_status = fields.Char(compute="_compute_expiry", string="Cảnh báo minh họa")
    event_ids = fields.One2many(
        "tp.credential.event",
        "record_id",
        string="Lịch sử lần trình",
    )
    _code_unique = models.Constraint(
        "UNIQUE(company_id,code)",
        "Mã hồ sơ đã được dùng trong công ty.",
    )

    @api.depends("valid_to")
    def _compute_expiry(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.expiry_status = (
                "Chưa có ngày"
                if not rec.valid_to
                else "Đã hết hạn"
                if rec.valid_to < today
                else "Còn30ngày — ngưỡng minh họa"
                if rec.valid_to <= today + timedelta(days=30)
                else "Còn hạn — chưa xác minh"
            )

    @api.constrains("valid_from", "valid_to", "credential_kind", "source_note")
    def _check_credential(self):
        for rec in self:
            if (
                not rec.valid_from
                or not rec.valid_to
                or rec.valid_to < rec.valid_from
                or not (rec.credential_kind or "").strip()
                or not (rec.source_note or "").strip()
            ):
                raise ValidationError(
                    self.env._(
                        "Điền loại, nguồn chưa xác minh và ngày hiệu lực/hết hạn hợp lệ.",
                    ),
                )

    def _kd_validate_sources(self):
        self._check_credential()

    def action_used_opportunities(self):
        self.ensure_one()
        self.check_access("read")
        ids = (
            self.env["crm.lead"]
            .sudo()
            .search([("kd_credential_link_ids", "in", self.ids)])
            .ids
        )
        return open_records(
            self.env,
            "crm.lead",
            [("id", "in", ids)],
            "Hồ sơ dự án sử dụng hồ sơ năng lực",
        )


class CredentialEvent(models.Model):
    _name = "tp.credential.event"
    _inherit = "tp.kd.event.mixin"
    _description = "Lịch sử hồ sơ năng lực"
    record_id = fields.Many2one("tp.credential", required=True, ondelete="restrict")
    project_id = fields.Many2one(related="record_id.project_id", store=True)
    company_id = fields.Many2one(related="record_id.company_id", store=True)


class Opportunity(models.Model):
    _inherit = "crm.lead"
    kd_credential_link_ids = fields.Many2many(
        "tp.credential",
        "tp_crm_credential_rel",
        "lead_id",
        "credential_id",
        groups="base.group_system",
        copy=False,
    )
    kd_credential_ids = fields.Many2many(
        "tp.credential",
        compute="_compute_credential_ids",
        inverse="_inverse_credential_ids",
        string="Năng lực sử dụng có quyền xem",
    )

    @api.depends_context("uid")
    @api.depends("kd_credential_link_ids")
    def _compute_credential_ids(self):
        for lead in self:
            ids = lead.sudo().kd_credential_link_ids.ids
            lead.kd_credential_ids = self.env["tp.credential"].search(
                [("id", "in", ids)],
            )

    def _inverse_credential_ids(self):
        for lead in self:
            lead._kd_require()
            visible = lead.kd_credential_ids
            visible.check_access("read")
            if any(c.project_id != lead.tp_project_id for c in visible):
                raise ValidationError(self.env._("Năng lực và hồ sơ dự án phải cùng dự án."))
            # Preserve private links that this actor could not see, never overwrite them.
            current = lead.sudo().kd_credential_link_ids
            hidden = current - self.env["tp.credential"].search(
                [("id", "in", current.ids)],
            )
            lead.sudo().write(
                {"kd_credential_link_ids": [Command.set((hidden | visible).ids)]},
            )

    @api.model
    def _check_credential_commands(self, vals):
        if "kd_credential_link_ids" in vals and not self.env.su:
            raise AccessError(self.env._("Liên kết gốc do máy chủ quản lý."))
        for command in vals.get("kd_credential_ids", []):
            if command[0] not in (3, 4, 5, 6):
                raise AccessError(
                    self.env._("Chỉ chọn hồ sơ năng lực đã có quyền xem."),
                )
            ids = (
                command[2]
                if command[0] == 6
                else [command[1]]
                if command[0] in (3, 4)
                else []
            )
            self.env["tp.credential"].browse(ids).check_access("read")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_credential_commands(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._check_credential_commands(vals)
        result = super().write(vals)
        if "tp_project_id" in vals:
            for rec in self:
                if any(
                    c.project_id != rec.tp_project_id
                    for c in rec.sudo().kd_credential_link_ids
                ):
                    raise ValidationError(
                        self.env._("Dự án mới không khớp năng lực đang sử dụng."),
                    )
        return result


class Project(models.Model):
    _inherit = "project.project"

    def action_kd_credentials(self):
        self.ensure_one()
        self.check_access("read")
        return open_records(
            self.env,
            "tp.credential",
            [("project_id", "=", self.id)],
            "Năng lực và chứng chỉ",
            {"default_project_id": self.id},
        )


class Overview(models.TransientModel):
    _inherit = "tp.kd.overview"

    def action_credentials(self):
        return open_records(
            self.env,
            "tp.credential",
            self._domain("tp.credential"),
            "Năng lực và chứng chỉ",
        )
