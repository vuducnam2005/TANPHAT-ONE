from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .workspace import child_context, kd_leaf, open_records


class Production(models.Model):
    _name = "tp.production"
    _inherit = "tp.kd.review.document"
    _description = "Hồ sơ sản lượng theo kỳ"
    _kd_domain = "production"
    _kd_money_model = "tp.production.amount"
    _kd_snapshot_fields = (
        "allocation_id",
        "quantity",
        "unit",
        "completion_percent",
        "reconciliation_state",
    )
    state = fields.Selection(
        [("draft", "Nháp"), ("in_review", "Đang rà soát"), ("returned", "Bị trả lại")],
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        string="Trạng thái hồ sơ",
    )
    allocation_id = fields.Many2one(
        "tp.allocation",
        ondelete="restrict",
        check_company=True,
        string="Khoán nguồn",
    )
    quantity = fields.Float(string="Khối lượng tự khai", digits=(16, 3))
    unit = fields.Char(required=True, string="Đơn vị khối lượng")
    completion_percent = fields.Float(string="Tỷ lệ hoàn thành (%)")
    reconciliation_state = fields.Selection(
        [("unreconciled", "Chưa đối chiếu"), ("needs_evidence", "Cần bổ sung căn cứ")],
        required=True,
        default="unreconciled",
        string="Đối chiếu nội bộ",
    )
    amount_ids = fields.One2many(
        "tp.production.amount",
        "record_id",
        string="Giá trị sản lượng minh họa",
    )
    event_ids = fields.One2many(
        "tp.production.event",
        "record_id",
        string="Lịch sử lần trình",
    )
    _code_unique = models.Constraint(
        "UNIQUE(company_id,code)",
        "Mã hồ sơ đã được dùng trong công ty.",
    )

    @api.constrains(
        "allocation_id",
        "contract_id",
        "project_id",
        "quantity",
        "unit",
        "completion_percent",
        "period_from",
        "period_to",
    )
    def _check_production(self):
        for rec in self:
            if (
                not rec.contract_id
                or not rec.period_from
                or not rec.period_to
                or not (rec.unit or "").strip()
                or rec.quantity < 0
                or not 0 <= rec.completion_percent <= 100
                or (
                    rec.allocation_id
                    and (
                        rec.allocation_id.project_id != rec.project_id
                        or rec.allocation_id.contract_id != rec.contract_id
                    )
                )
            ):
                raise ValidationError(
                    self.env._(
                        "Cần kỳ, hợp đồng, đơn vị/khối lượng hợp lệ và khoán cùng dự án/hợp đồng.",
                    ),
                )

    def _kd_validate_sources(self):
        self._check_production()

    def action_allocation(self):
        self.ensure_one()
        if not self.allocation_id:
            return False
        self.allocation_id.check_access("read")
        return {
            "type": "ir.actions.act_window",
            "res_model": "tp.allocation",
            "res_id": self.allocation_id.id,
            "view_mode": "form",
            "views": [(self.env.ref("tp_kd_workspace.allocation_form").id, "form")],
            "target": "current",
            "context": {**child_context(self.env), **kd_leaf("tp.allocation")},
        }


class ProductionAmount(models.Model):
    _name = "tp.production.amount"
    _inherit = "tp.kd.amount.mixin"
    _description = "ProductionAmount"
    record_id = fields.Many2one("tp.production", required=True, ondelete="cascade")
    project_id = fields.Many2one(related="record_id.project_id", store=True)
    company_id = fields.Many2one(related="record_id.company_id", store=True)
    _one_amount = models.Constraint(
        "UNIQUE(record_id)",
        "Một hồ sơ chỉ có một căn cứ giá trị.",
    )


class ProductionEvent(models.Model):
    _name = "tp.production.event"
    _inherit = "tp.kd.event.mixin"
    _description = "ProductionEvent"
    record_id = fields.Many2one("tp.production", required=True, ondelete="restrict")
    project_id = fields.Many2one(related="record_id.project_id", store=True)
    company_id = fields.Many2one(related="record_id.company_id", store=True)
    amount_ids = fields.One2many("tp.production.event.amount", "event_id")


class ProductionEventAmount(models.Model):
    _name = "tp.production.event.amount"
    _inherit = "tp.kd.amount.mixin"
    _description = "ProductionEventAmount"
    event_id = fields.Many2one(
        "tp.production.event",
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

    def action_kd_productions(self):
        self.ensure_one()
        self.check_access("read")
        return open_records(
            self.env,
            "tp.production",
            [("project_id", "=", self.id)],
            "Sản lượng theo kỳ",
            {"default_project_id": self.id},
        )


class Overview(models.TransientModel):
    _inherit = "tp.kd.overview"

    def action_productions(self):
        return open_records(
            self.env,
            "tp.production",
            self._domain("tp.production"),
            "Sản lượng theo kỳ",
        )


class AllocationSourceGuard(models.Model):
    _inherit = "tp.allocation"

    @api.constrains("contract_id")
    def _check_production_source_stability(self):
        for rec in self:
            if (
                self.env["tp.production"]
                .sudo()
                .search_count(
                    [
                        ("allocation_id", "=", rec.id),
                        ("contract_id", "!=", rec.contract_id.id),
                    ],
                    limit=1,
                )
            ):
                raise ValidationError(
                    self.env._(
                        "Khoán đã có sản lượng liên kết; giữ hợp đồng nguồn nhất quán.",
                    ),
                )
