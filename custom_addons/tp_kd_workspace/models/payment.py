from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .workspace import child_context, kd_leaf, open_records


class PaymentRequest(models.Model):
    _name = "tp.payment.request"
    _inherit = "tp.kd.review.document"
    _description = "Đề nghị thanh toán và đối chiếu"
    _kd_domain = "payment"
    _kd_money_model = "tp.payment.request.amount"
    _kd_snapshot_fields = (
        "acceptance_id",
        "direction",
        "payment_basis",
        "partner_id",
        "advance_basis",
        "document_checklist",
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
    direction = fields.Selection(
        [("receipt", "Đề nghị thu"), ("disbursement", "Đề nghị chi")],
        required=True,
        default="receipt",
        string="Chiều đề nghị",
    )
    payment_basis = fields.Selection(
        [("advance", "Tạm ứng"), ("acceptance", "Theo đợt nghiệm thu")],
        required=True,
        default="advance",
        string="Căn cứ đề nghị",
    )
    acceptance_id = fields.Many2one(
        "tp.acceptance",
        ondelete="restrict",
        check_company=True,
        string="Hồ sơ nghiệm thu nguồn",
    )
    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        ondelete="restrict",
        check_company=True,
        string="Đối tác",
    )
    advance_basis = fields.Text(string="Căn cứ tạm ứng dự kiến")
    document_checklist = fields.Text(required=True, string="Kiểm kê chứng từ / hồ sơ")
    reconciliation_state = fields.Selection(
        [
            ("pending", "Chưa đối chiếu"),
            ("missing_documents", "Cần bổ sung hồ sơ"),
            ("internal_checked", "Đã kiểm nội bộ — chưa phê duyệt"),
        ],
        required=True,
        default="pending",
        string="Tình trạng đối chiếu",
    )
    amount_ids = fields.One2many(
        "tp.payment.request.amount",
        "record_id",
        string="Số tiền đề nghị minh họa",
    )
    event_ids = fields.One2many(
        "tp.payment.request.event",
        "record_id",
        string="Lịch sử lần trình",
    )
    _code_unique = models.Constraint(
        "UNIQUE(company_id,code)",
        "Mã hồ sơ đã được dùng trong công ty.",
    )

    @api.constrains(
        "acceptance_id",
        "project_id",
        "contract_id",
        "date",
        "date_due",
        "payment_basis",
        "advance_basis",
        "document_checklist",
    )
    def _check_payment(self):
        for rec in self:
            source = rec.acceptance_id
            if (
                not rec.contract_id
                or not rec.date_due
                or not (rec.document_checklist or "").strip()
                or (
                    rec.payment_basis == "advance"
                    and (not (rec.advance_basis or "").strip() or source)
                )
                or (rec.payment_basis == "acceptance" and not source)
                or (
                    source
                    and (
                        source.project_id != rec.project_id
                        or source.contract_id != rec.contract_id
                        or rec.date < source.date
                    )
                )
            ):
                raise ValidationError(
                    self.env._(
                        "Cần hợp đồng, hạn, hồ sơ và nguồn đúng dự án/ngày. Tạm ứng cần căn cứ riêng và không ghép nghiệm thu.",
                    ),
                )

    def _kd_validate_sources(self):
        self._check_payment()

    def action_acceptance(self):
        self.ensure_one()
        if not self.acceptance_id:
            return False
        self.acceptance_id.check_access("read")
        return {
            "type": "ir.actions.act_window",
            "res_model": "tp.acceptance",
            "res_id": self.acceptance_id.id,
            "view_mode": "form",
            "views": [(self.env.ref("tp_kd_workspace.acceptance_form").id, "form")],
            "target": "current",
            "context": {**child_context(self.env), **kd_leaf("tp.acceptance")},
        }


class PaymentRequestAmount(models.Model):
    _name = "tp.payment.request.amount"
    _inherit = "tp.kd.amount.mixin"
    _description = "PaymentRequestAmount"
    record_id = fields.Many2one("tp.payment.request", required=True, ondelete="cascade")
    project_id = fields.Many2one(related="record_id.project_id", store=True)
    company_id = fields.Many2one(related="record_id.company_id", store=True)
    _one_amount = models.Constraint(
        "UNIQUE(record_id)",
        "Một hồ sơ chỉ có một căn cứ giá trị.",
    )


class PaymentRequestEvent(models.Model):
    _name = "tp.payment.request.event"
    _inherit = "tp.kd.event.mixin"
    _description = "PaymentRequestEvent"
    record_id = fields.Many2one(
        "tp.payment.request",
        required=True,
        ondelete="restrict",
    )
    project_id = fields.Many2one(related="record_id.project_id", store=True)
    company_id = fields.Many2one(related="record_id.company_id", store=True)
    amount_ids = fields.One2many("tp.payment.request.event.amount", "event_id")


class PaymentRequestEventAmount(models.Model):
    _name = "tp.payment.request.event.amount"
    _inherit = "tp.kd.amount.mixin"
    _description = "PaymentRequestEventAmount"
    event_id = fields.Many2one(
        "tp.payment.request.event",
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

    def action_kd_payments(self):
        self.ensure_one()
        self.check_access("read")
        return open_records(
            self.env,
            "tp.payment.request",
            [("project_id", "=", self.id)],
            "Đề nghị thanh toán",
            {"default_project_id": self.id},
        )


class Overview(models.TransientModel):
    _inherit = "tp.kd.overview"

    def action_payments(self):
        return open_records(
            self.env,
            "tp.payment.request",
            self._domain("tp.payment.request"),
            "Đề nghị thanh toán",
        )


class AcceptanceSourceGuard(models.Model):
    _inherit = "tp.acceptance"

    @api.constrains("contract_id", "date")
    def _check_payment_source_stability(self):
        for rec in self:
            self.env["tp.payment.request"].sudo().search(
                [("acceptance_id", "=", rec.id)],
            )._check_payment()
