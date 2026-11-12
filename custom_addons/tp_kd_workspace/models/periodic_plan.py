import calendar
from decimal import Decimal

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .workspace import open_records


class PeriodicPlan(models.Model):
    _name = "tp.periodic.plan"
    _inherit = "tp.kd.review.document"
    _description = "Kế hoạch tháng quý năm"
    _kd_domain = "plan"
    _kd_money_model = "tp.periodic.plan.amount"
    _kd_amount_snapshot_fields = ("measure",)
    _kd_snapshot_fields = ("period_kind",)
    state = fields.Selection(
        [("draft", "Nháp"), ("in_review", "Đang rà soát"), ("returned", "Bị trả lại")],
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        string="Trạng thái hồ sơ",
    )
    period_kind = fields.Selection(
        [("month", "Tháng"), ("quarter", "Quý"), ("year", "Năm")],
        required=True,
        default="month",
        string="Loại kỳ",
    )
    amount_ids = fields.One2many(
        "tp.periodic.plan.amount",
        "record_id",
        string="Mục tiêu kế hoạch",
    )
    event_ids = fields.One2many(
        "tp.periodic.plan.event",
        "record_id",
        string="Lịch sử lần trình",
    )
    _code_unique = models.Constraint(
        "UNIQUE(company_id,code)",
        "Mã hồ sơ đã được dùng trong công ty.",
    )
    _period_unique = models.Constraint(
        "UNIQUE(project_id,period_kind,period_from,period_to)",
        "Đã có kế hoạch cùng dự án/loại kỳ. Mở bản hiện có.",
    )

    @api.constrains("period_kind", "period_from", "period_to")
    def _check_plan(self):
        for rec in self:
            start, end = rec.period_from, rec.period_to
            months = {"month": 1, "quarter": 3, "year": 12}[rec.period_kind]
            if (
                not start
                or not end
                or start.day != 1
                or start.year != end.year
                or end.month != start.month + months - 1
                or end.day != calendar.monthrange(end.year, end.month)[1]
                or (rec.period_kind == "quarter" and start.month not in (1, 4, 7, 10))
                or (rec.period_kind == "year" and start.month != 1)
            ):
                raise ValidationError(
                    self.env._(
                        "Kỳ kế hoạch phải đúng đầu-cuối tháng/quý/năm lịch và cùng năm.",
                    ),
                )

    def _kd_validate_sources(self):
        self._check_plan()

    def _source_production_domain(self):
        self.ensure_one()
        return [
            ("project_id", "=", self.project_id.id),
            ("state", "=", "in_review"),
            ("period_from", ">=", self.period_from),
            ("period_to", "<=", self.period_to),
        ]

    def action_source_productions(self):
        self.ensure_one()
        self.check_access("read")
        return open_records(
            self.env,
            "tp.production",
            self._source_production_domain(),
            "Sản lượng đã gửi trong kỳ — chưa nghiệm thu ngoài",
        )


class PeriodicPlanAmount(models.Model):
    measure = fields.Selection(
        [
            ("production", "Mục tiêu sản lượng"),
            ("revenue", "Mục tiêu doanh thu kế hoạch"),
        ],
        required=True,
        string="Chỉ tiêu",
    )
    source_value = fields.Monetary(
        currency_field="currency_id",
        compute="_compute_source",
        string="Sản lượng đã gửi rà soát",
    )
    source_status = fields.Selection(
        [
            ("no_data", "Chưa có dữ liệu nguồn"),
            ("unknown", "Chưa đủ căn cứ so sánh"),
            ("comparable", "Cùng kỳ/tiền tệ/cơ sở"),
            ("no_posted_evidence", "Chưa có chứng từ ghi sổ liên kết đã kiểm"),
        ],
        compute="_compute_source",
        string="Tình trạng đối chiếu",
    )

    @api.depends_context("uid")
    def _compute_source(self):
        for line in self:
            line.source_value = 0
            line.source_status = "no_data"
            if not line.record_id._kd_money_allowed():
                raise AccessError(self.env._("Chưa có quyền đọc chỉ tiêu."))
            if line.measure == "revenue":
                line.source_status = "no_posted_evidence"
                continue
            sources = self.env["tp.production"].search(
                line.record_id._source_production_domain(),
            )
            if not sources:
                continue
            amounts = sources.amount_ids
            if (
                len(amounts) != len(sources)
                or line.amount_state != "confirmed"
                or any(
                    a.amount_state != "confirmed"
                    or a.currency_id != line.currency_id
                    or a.tax_basis != line.tax_basis
                    for a in amounts
                )
            ):
                line.source_status = "unknown"
                continue
            line.source_status = "comparable"
            line.source_value = line.currency_id.round(
                float(sum((Decimal(str(a.value)) for a in amounts), Decimal(0))),
            )

    _name = "tp.periodic.plan.amount"
    _inherit = "tp.kd.amount.mixin"
    _description = "PeriodicPlanAmount"
    record_id = fields.Many2one("tp.periodic.plan", required=True, ondelete="cascade")
    project_id = fields.Many2one(related="record_id.project_id", store=True)
    company_id = fields.Many2one(related="record_id.company_id", store=True)
    _one_amount = models.Constraint(
        "UNIQUE(record_id,measure)",
        "Một hồ sơ chỉ có một căn cứ giá trị.",
    )


class PeriodicPlanEvent(models.Model):
    _name = "tp.periodic.plan.event"
    _inherit = "tp.kd.event.mixin"
    _description = "PeriodicPlanEvent"
    record_id = fields.Many2one("tp.periodic.plan", required=True, ondelete="restrict")
    project_id = fields.Many2one(related="record_id.project_id", store=True)
    company_id = fields.Many2one(related="record_id.company_id", store=True)
    amount_ids = fields.One2many("tp.periodic.plan.event.amount", "event_id")


class PeriodicPlanEventAmount(models.Model):
    measure = fields.Selection(
        [
            ("production", "Mục tiêu sản lượng"),
            ("revenue", "Mục tiêu doanh thu kế hoạch"),
        ],
        required=True,
        string="Chỉ tiêu",
    )
    _name = "tp.periodic.plan.event.amount"
    _inherit = "tp.kd.amount.mixin"
    _description = "PeriodicPlanEventAmount"
    event_id = fields.Many2one(
        "tp.periodic.plan.event",
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

    def action_kd_plans(self):
        self.ensure_one()
        self.check_access("read")
        return open_records(
            self.env,
            "tp.periodic.plan",
            [("project_id", "=", self.id)],
            "Kế hoạch định kỳ",
            {"default_project_id": self.id},
        )


class Overview(models.TransientModel):
    _inherit = "tp.kd.overview"

    def action_plans(self):
        return open_records(
            self.env,
            "tp.periodic.plan",
            self._domain("tp.periodic.plan"),
            "Kế hoạch định kỳ",
        )
