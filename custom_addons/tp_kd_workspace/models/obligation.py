from odoo import fields, models

from .workspace import open_records


class Obligation(models.Model):
    _name = "tp.obligation"
    _inherit = "tp.kd.review.document"
    _description = "Checklist nghĩa vụ và hồ sơ còn thiếu"
    _kd_domain = "obligation"
    _kd_snapshot_fields = (
        "obligation_kind",
        "document_checklist",
        "checklist_status",
        "checklist_update_reason",
    )
    state = fields.Selection(
        [("draft", "Nháp"), ("in_review", "Đang rà soát"), ("returned", "Bị trả lại")],
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        string="Trạng thái hồ sơ",
    )
    obligation_kind = fields.Selection(
        [
            ("contract_docs", "Hồ sơ hợp đồng/bàn giao"),
            ("retention", "Căn cứ giữ lại — chưa xác nhận"),
            ("warranty", "Hồ sơ bảo hành"),
            ("reconciliation", "Căn cứ công nợ — chưa xác nhận"),
        ],
        required=True,
        default="contract_docs",
        string="Nhóm nghĩa vụ",
    )
    document_checklist = fields.Text(
        required=True,
        string="Checklist / hồ sơ còn thiếu",
    )
    checklist_status = fields.Selection(
        [
            ("missing", "Còn thiếu hồ sơ"),
            ("collecting", "Đang thu thập"),
            ("internal_checked", "Đã kiểm danh mục nội bộ"),
        ],
        required=True,
        default="missing",
        string="Tình trạng checklist",
    )
    checklist_update_reason = fields.Text(
        required=True,
        string="Lý do cập nhật checklist",
    )
    event_ids = fields.One2many(
        "tp.obligation.event",
        "record_id",
        string="Lịch sử lần trình / checklist",
    )
    _code_unique = models.Constraint(
        "UNIQUE(company_id,code)",
        "Mã hồ sơ đã được dùng trong công ty.",
    )

    def write(self, vals):
        result = super().write(vals)
        if set(vals) & {
            "document_checklist",
            "checklist_status",
            "obligation_kind",
        } and not set(vals) & {"state"}:
            self._kd_event("update_checklist", self.state, self.checklist_update_reason)
        return result


class ObligationEvent(models.Model):
    _name = "tp.obligation.event"
    _inherit = "tp.kd.event.mixin"
    _description = "Lịch sử checklist nghĩa vụ"
    record_id = fields.Many2one("tp.obligation", required=True, ondelete="restrict")
    project_id = fields.Many2one(related="record_id.project_id", store=True)
    company_id = fields.Many2one(related="record_id.company_id", store=True)


class Project(models.Model):
    _inherit = "project.project"

    def action_kd_obligations(self):
        self.ensure_one()
        self.check_access("read")
        return open_records(
            self.env,
            "tp.obligation",
            [("project_id", "=", self.id)],
            "Nghĩa vụ và hồ sơ còn thiếu",
            {"default_project_id": self.id},
        )


class Overview(models.TransientModel):
    _inherit = "tp.kd.overview"

    def action_obligations(self):
        return open_records(
            self.env,
            "tp.obligation",
            self._domain("tp.obligation"),
            "Nghĩa vụ và hồ sơ còn thiếu",
        )
