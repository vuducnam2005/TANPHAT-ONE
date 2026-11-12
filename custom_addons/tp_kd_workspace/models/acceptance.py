from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .workspace import kd_leaf, open_records


class Acceptance(models.Model):
    _name = "tp.acceptance"
    _inherit = "tp.kd.review.document"
    _description = "Hồ sơ đợt nghiệm thu nội bộ"
    _kd_domain = "acceptance"
    _kd_money_model = "tp.acceptance.amount"
    _kd_snapshot_fields = (
        "production_id",
        "round_code",
        "counterparty_id",
        "quantity",
        "unit",
        "evidence_checklist",
    )
    state = fields.Selection(
        [("draft", "Nháp"), ("in_review", "Đang rà soát"), ("returned", "Bị trả lại")],
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        string="Trạng thái hồ sơ",
    )
    production_id = fields.Many2one(
        "tp.production",
        required=True,
        ondelete="restrict",
        check_company=True,
        string="Sản lượng nguồn",
    )
    round_code = fields.Char(required=True, string="Đợt nghiệm thu")
    counterparty_id = fields.Many2one(
        "res.partner",
        required=True,
        ondelete="restrict",
        check_company=True,
        string="Bên nhận hồ sơ",
    )
    quantity = fields.Float(string="Khối lượng đề xuất nghiệm thu", digits=(16, 3))
    unit = fields.Char(required=True, string="Đơn vị khối lượng")
    evidence_checklist = fields.Text(required=True, string="Kiểm kê căn cứ / hồ sơ")
    amount_ids = fields.One2many(
        "tp.acceptance.amount",
        "record_id",
        string="Giá trị đề xuất minh họa",
    )
    event_ids = fields.One2many(
        "tp.acceptance.event",
        "record_id",
        string="Lịch sử lần trình",
    )
    _code_unique = models.Constraint(
        "UNIQUE(company_id,code)",
        "Mã hồ sơ đã được dùng trong công ty.",
    )

    @api.constrains(
        "production_id",
        "project_id",
        "contract_id",
        "date",
        "period_from",
        "period_to",
        "quantity",
        "unit",
        "round_code",
        "evidence_checklist",
    )
    def _check_acceptance(self):
        for rec in self:
            source = rec.production_id
            source.check_access("read")
            if (
                not source
                or not rec.contract_id
                or source.project_id != rec.project_id
                or source.contract_id != rec.contract_id
                or not rec.period_from
                or not rec.period_to
                or rec.period_from < source.period_from
                or rec.period_to > source.period_to
                or rec.date < source.date
                or rec.quantity < 0
                or rec.quantity > source.quantity
                or rec.unit != source.unit
                or not (rec.round_code or "").strip()
                or not (rec.evidence_checklist or "").strip()
            ):
                raise ValidationError(
                    self.env._(
                        "Kiểm tra sản lượng cùng nguồn, kỳ/ngày, đơn vị và khối lượng không vượt nguồn; bổ sung đợt/căn cứ.",
                    ),
                )

    def _kd_validate_sources(self):
        self._check_acceptance()

    def action_production(self):
        self.ensure_one()
        self.production_id.check_access("read")
        return {
            "type": "ir.actions.act_window",
            "res_model": "tp.production",
            "res_id": self.production_id.id,
            "view_mode": "form",
            "context": kd_leaf("tp.production"),
        }


class AcceptanceAmount(models.Model):
    _name = "tp.acceptance.amount"
    _inherit = "tp.kd.amount.mixin"
    _description = "AcceptanceAmount"
    record_id = fields.Many2one("tp.acceptance", required=True, ondelete="cascade")
    project_id = fields.Many2one(related="record_id.project_id", store=True)
    company_id = fields.Many2one(related="record_id.company_id", store=True)
    _one_amount = models.Constraint(
        "UNIQUE(record_id)",
        "Một hồ sơ chỉ có một căn cứ giá trị.",
    )


class AcceptanceEvent(models.Model):
    _name = "tp.acceptance.event"
    _inherit = "tp.kd.event.mixin"
    _description = "AcceptanceEvent"
    record_id = fields.Many2one("tp.acceptance", required=True, ondelete="restrict")
    project_id = fields.Many2one(related="record_id.project_id", store=True)
    company_id = fields.Many2one(related="record_id.company_id", store=True)
    amount_ids = fields.One2many("tp.acceptance.event.amount", "event_id")


class AcceptanceEventAmount(models.Model):
    _name = "tp.acceptance.event.amount"
    _inherit = "tp.kd.amount.mixin"
    _description = "AcceptanceEventAmount"
    event_id = fields.Many2one(
        "tp.acceptance.event",
        required=True,
        ondelete="restrict",
    )
    project_id = fields.Many2one(related="event_id.project_id", store=True)
    company_id = fields.Many2one(related="event_id.company_id", store=True)

    def write(self, vals):
        raise AccessError(self.env._("Giá trị lần trình bất biến."))

    def unlink(self):
        raise AccessError(self.env._("Giữ nguyên giá trị lần trình."))


class Project(models.Model):
    _inherit = "project.project"

    def action_kd_acceptances(self):
        self.ensure_one()
        self.check_access("read")
        return open_records(
            self.env,
            "tp.acceptance",
            [("project_id", "=", self.id)],
            "Hồ sơ nghiệm thu",
            {"default_project_id": self.id},
        )


class Overview(models.TransientModel):
    _inherit = "tp.kd.overview"

    def action_acceptances(self):
        return open_records(
            self.env,
            "tp.acceptance",
            self._domain("tp.acceptance"),
            "Hồ sơ nghiệm thu",
        )


class ProductionSourceGuard(models.Model):
    _inherit = "tp.production"

    @api.constrains(
        "contract_id",
        "date",
        "period_from",
        "period_to",
        "quantity",
        "unit",
    )
    def _check_acceptance_source_stability(self):
        for rec in self:
            # Validate all downstream dossiers as technical integrity, never return their data.
            self.env["tp.acceptance"].sudo().search(
                [("production_id", "=", rec.id)],
            )._check_acceptance()
