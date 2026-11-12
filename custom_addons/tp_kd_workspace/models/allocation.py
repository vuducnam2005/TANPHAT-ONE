from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .workspace import open_records


class Allocation(models.Model):
    _name = "tp.allocation"
    _inherit = "tp.kd.review.document"
    _description = "Hồ sơ giao khoán"
    _kd_domain = "allocation"
    _kd_money_model = "tp.allocation.amount"
    _kd_snapshot_fields = (
        "allocation_kind",
        "parent_id",
        "recipient_department_id",
        "partner_id",
    )

    state = fields.Selection(
        [("draft", "Nháp"), ("in_review", "Đang rà soát"), ("returned", "Bị trả lại")],
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        string="Trạng thái hồ sơ",
    )
    allocation_kind = fields.Selection(
        [("internal", "Khoán nội bộ"), ("subcontract", "Thầu phụ")],
        required=True,
        string="Loại giao khoán",
    )
    parent_id = fields.Many2one(
        "tp.allocation",
        ondelete="restrict",
        check_company=True,
        string="Khoán cha (cấp 1)",
    )
    child_ids = fields.One2many("tp.allocation", "parent_id", string="Khoán cấp 2")
    recipient_department_id = fields.Many2one(
        "hr.department",
        ondelete="restrict",
        check_company=True,
        string="Đơn vị nhận nội bộ",
    )
    partner_id = fields.Many2one(
        "res.partner",
        ondelete="restrict",
        check_company=True,
        string="Đối tác thầu phụ",
    )
    amount_ids = fields.One2many(
        "tp.allocation.amount",
        "record_id",
        string="Giá trị khoán",
    )
    event_ids = fields.One2many(
        "tp.allocation.event",
        "record_id",
        string="Lịch sử lần trình",
    )
    overrun_warning = fields.Char(compute="_compute_overrun", string="Đối chiếu cấp 2")
    _code_unique = models.Constraint(
        "UNIQUE(company_id,code)",
        "Mã hồ sơ đã được dùng trong công ty.",
    )

    @api.constrains(
        "parent_id",
        "contract_id",
        "project_id",
        "allocation_kind",
        "recipient_department_id",
        "partner_id",
    )
    def _check_allocation(self):
        for rec in self:
            if (
                not rec.contract_id
                or (
                    rec.allocation_kind == "internal"
                    and not rec.recipient_department_id
                )
                or (rec.allocation_kind == "subcontract" and not rec.partner_id)
            ):
                raise ValidationError(
                    self.env._(
                        "Khoán cần hợp đồng nguồn và đơn vị/đối tác nhận phù hợp.",
                    ),
                )
            if rec.parent_id and (
                rec.parent_id == rec
                or rec.parent_id.parent_id
                or rec.child_ids
                or rec.parent_id.project_id != rec.project_id
                or rec.parent_id.contract_id != rec.contract_id
            ):
                raise ValidationError(
                    self.env._(
                        "Khoán cấp 2 cần cha cấp 1 cùng hợp đồng/dự án; không tạo vòng lặp.",
                    ),
                )

    def _kd_validate_sources(self):
        self._check_allocation()

    @api.depends_context("uid")
    def _compute_overrun(self):
        for rec in self:
            rec.overrun_warning = False
            if not rec._kd_money_allowed():
                continue
            parent = rec.amount_ids.filtered(lambda a: a.amount_state == "confirmed")
            children = rec.child_ids.amount_ids.filtered(
                lambda a: a.amount_state == "confirmed",
            )
            if parent and children:
                if all(
                    a.currency_id == parent.currency_id
                    and a.tax_basis == parent.tax_basis
                    for a in children
                ):
                    total = sum(children.mapped("value"))
                    rec.overrun_warning = (
                        "Cảnh báo minh họa: tổng cấp 2 vượt khoán cha; chưa chặn theo Q7."
                        if parent.currency_id.compare_amounts(total, parent.value) > 0
                        else "Cùng cơ sở; cấp 2 không cộng vào tổng công ty."
                    )
                else:
                    rec.overrun_warning = (
                        "Chưa đối chiếu: khác tiền tệ/cơ sở hoặc chưa xác nhận."
                    )


class AllocationAmount(models.Model):
    _name = "tp.allocation.amount"
    _inherit = "tp.kd.amount.mixin"
    _description = "Giá trị hồ sơ khoán có quyền riêng"
    record_id = fields.Many2one("tp.allocation", required=True, ondelete="cascade")
    project_id = fields.Many2one(related="record_id.project_id", store=True)
    company_id = fields.Many2one(related="record_id.company_id", store=True)
    _one_amount = models.Constraint(
        "UNIQUE(record_id)",
        "Một hồ sơ chỉ có một căn cứ giá trị.",
    )


class AllocationEvent(models.Model):
    _name = "tp.allocation.event"
    _inherit = "tp.kd.event.mixin"
    _description = "Lịch sử giao khoán bất biến"
    record_id = fields.Many2one("tp.allocation", required=True, ondelete="restrict")
    project_id = fields.Many2one(related="record_id.project_id", store=True)
    company_id = fields.Many2one(related="record_id.company_id", store=True)
    amount_ids = fields.One2many("tp.allocation.event.amount", "event_id")


class AllocationEventAmount(models.Model):
    _name = "tp.allocation.event.amount"
    _inherit = "tp.kd.amount.mixin"
    _description = "Giá trị bất biến tại lần trình khoán"
    event_id = fields.Many2one(
        "tp.allocation.event",
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

    def action_kd_allocations(self):
        self.ensure_one()
        self.check_access("read")
        return open_records(
            self.env,
            "tp.allocation",
            [("project_id", "=", self.id)],
            "Giao khoán và thầu phụ",
            {"default_project_id": self.id, "default_company_id": self.company_id.id},
        )


class Overview(models.TransientModel):
    _inherit = "tp.kd.overview"

    def action_allocations(self):
        return open_records(
            self.env,
            "tp.allocation",
            self._domain("tp.allocation"),
            "Giao khoán và thầu phụ",
        )
