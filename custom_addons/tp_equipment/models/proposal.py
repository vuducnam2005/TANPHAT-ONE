"""Đề xuất mua / sửa / nâng cấp / chuyển máy (EQUIP-001 part 3).

Three separate dimensions:
* review (rà soát kỹ thuật): Nháp → Đang rà soát → Trả lại (lý do) → Gửi lại → Hoàn tất rà soát;
* external approval (BASE / văn bản): recorded by the admin with evidence, never inferred from review
  or from the names printed on a source spreadsheet;
* execution progress, derived from linked receipts / repair requests / moves.

A proposal is not a purchase order, vendor bill, payment or fixed asset. Execution buttons only appear
when review is complete and an approval with evidence covers the line.
"""
from markupsafe import Markup
from psycopg2 import errors as pg_errors

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Domain
from odoo.tools import SQL

from .common import INTERNAL, check_admin

REVIEW_STATES = [
    ("draft", "Nháp"),
    ("review", "Đang rà soát"),
    ("returned", "Trả lại để sửa"),
    ("reviewed", "Hoàn tất rà soát"),
    ("cancel", "Đã hủy"),
]
APPROVAL_STATES = [
    ("unverified", "Chờ xác minh kết quả duyệt"),
    ("approved", "Đã duyệt (có căn cứ)"),
    ("partial", "Duyệt một phần"),
    ("rejected", "Không duyệt"),
]
APPROVAL_SOURCES = [
    ("base", "BASE"),
    ("document", "Văn bản / bản scan"),
    ("message", "Email / tin nhắn nội bộ"),
    ("other", "Nguồn khác"),
]
APPROVAL_CHECK = [
    ("original", "Đã đối chiếu bản gốc / trên hệ thống nguồn"),
    ("copy", "Chỉ có bản sao / ảnh chụp"),
]
LINE_KINDS = [
    ("purchase", "Mua mới"),
    ("repair", "Sửa máy cũ"),
    ("upgrade", "Nâng cấp / thay linh kiện"),
    ("transfer", "Chuyển máy cũ cho người / bộ phận khác"),
    ("dispose", "Đề xuất thanh lý / ngừng dùng"),
]
# EQUIP-SIMPLE-003: the three needs of the short form, mapped onto the existing line kinds (no new meaning):
# Mua mới = purchase without an old machine; Đổi máy = purchase that replaces the current machine
# (receipt sets tp_replaces_id); Sửa hoặc nâng cấp = repair / upgrade. Older transfer / dispose rows show "Khác".
NEED_TYPES = [
    ("purchase", "Mua mới"),
    ("swap", "Đổi máy"),
    ("repair", "Sửa hoặc nâng cấp"),
    ("other", "Khác (chuyển / thanh lý)"),
]
NEED_DOMAINS = {
    "purchase": [("kind", "=", "purchase"), ("equipment_id", "=", False)],
    "swap": [("kind", "=", "purchase"), ("equipment_id", "!=", False)],
    "repair": [("kind", "in", ("repair", "upgrade"))],
    "other": [("kind", "in", ("transfer", "dispose"))],
}


def need_of(kind, has_equipment):
    if kind == "purchase":
        return "swap" if has_equipment else "purchase"
    return "repair" if kind in ("repair", "upgrade") else "other"


def need_search_domain(operator, value):
    """Line domain (kind / equipment_id) for a need filter; proposals wrap it in ``line_ids any``."""
    if operator in ("=", "!="):
        value = [value]
    elif operator not in ("in", "not in"):
        return NotImplemented
    needs = [v for v in value if v in NEED_DOMAINS]
    domain = Domain.OR([
        Domain.AND([Domain(name, op, val) for name, op, val in NEED_DOMAINS[need]]) for need in needs
    ]) if needs else Domain.FALSE
    return ~domain if operator in ("!=", "not in") else domain


TAX_NOTE = [
    ("unknown", "Chưa rõ thuế"),
    ("included", "Đã gồm VAT"),
    ("excluded", "Chưa gồm VAT"),
]
PROGRESS = [
    ("waiting", "Chờ đủ điều kiện"),
    ("not_started", "Chưa thực hiện"),
    ("in_progress", "Đang thực hiện"),
    ("partial", "Nhận / xử lý một phần"),
    ("done", "Hoàn tất"),
    ("cancel", "Không thực hiện"),
]
REVIEW_ACTIONS = [
    ("submit", "Gửi rà soát"),
    ("return", "Trả lại"),
    ("resubmit", "Gửi lại"),
    ("reviewed", "Hoàn tất rà soát"),
    ("approval", "Ghi nhận kết quả duyệt"),
    ("cancel", "Hủy đề xuất"),
    ("line_cancel", "Dòng không thực hiện"),
]
EDITABLE_REVIEW = ("draft", "returned")


class TpEquipmentProposal(models.Model):
    _name = "tp.equipment.proposal"
    _description = "Đề xuất mua sắm / sửa chữa thiết bị"
    _inherit = ["tp.equipment.secure.mixin"]
    _order = "date desc, id desc"

    name = fields.Char("Số đề xuất", readonly=True, copy=False, default="/", index=True)
    title = fields.Char("Nội dung đề xuất", required=True, tracking=True)
    date = fields.Date("Ngày đề xuất", default=fields.Date.context_today, required=True, tracking=True)
    date_known = fields.Boolean("Ngày có trên chứng từ", default=True, tracking=True,
                                help="Tắt khi chứng từ nguồn không ghi ngày: Ngày đề xuất khi đó chỉ là ngày ghi hệ thống.")
    company_id = fields.Many2one("res.company", "Công ty", default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related="company_id.currency_id", string="Tiền tệ")
    responsible_id = fields.Many2one("res.users", "Người ghi trên hệ thống", default=lambda self: self.env.uid,
                                     readonly=True, copy=False)

    requester_employee_id = fields.Many2one("hr.employee", "Người cần", ondelete="restrict", tracking=True,
                                            context={"active_test": False})
    requester_department_id = fields.Many2one("hr.department", "Bộ phận cần", ondelete="restrict", tracking=True)
    requester_text = fields.Char("Người cần theo nguồn", help="Ghi nguyên văn khi chưa xác minh được nhân viên.")
    preparer_text = fields.Char("Người lập (thực tế)", tracking=True,
                                help="Thông tin nghiệp vụ theo chứng từ; không cấp quyền Kho thiết bị.")
    reviewer_text = fields.Char("Người xem xét (thực tế)", tracking=True)
    approver_text = fields.Char("Người duyệt (thực tế)", readonly=True, tracking=True)

    review_state = fields.Selection(REVIEW_STATES, "Rà soát", default="draft", required=True, readonly=True,
                                    copy=False, tracking=True, index=True)
    resubmit_count = fields.Integer("Số lần gửi lại", readonly=True, copy=False)
    return_reason = fields.Text("Lý do trả lại gần nhất", readonly=True, copy=False)
    cancel_reason = fields.Text("Lý do hủy", readonly=True, copy=False)
    review_ids = fields.One2many("tp.equipment.proposal.review", "proposal_id", "Nhật ký rà soát", readonly=True)

    approval_state = fields.Selection(APPROVAL_STATES, "Kết quả duyệt", default="unverified", required=True,
                                      readonly=True, copy=False, tracking=True, index=True)
    approval_source = fields.Selection(APPROVAL_SOURCES, "Nguồn duyệt", readonly=True, copy=False)
    approval_ref = fields.Char("Số / mã tham chiếu duyệt", readonly=True, copy=False)
    approval_date = fields.Date("Ngày duyệt", readonly=True, copy=False)
    approval_check = fields.Selection(APPROVAL_CHECK, "Mức kiểm chứng", readonly=True, copy=False)
    approval_note = fields.Text("Ghi chú kết quả duyệt", readonly=True, copy=False)
    approval_recorded_by_id = fields.Many2one("res.users", "Người ghi nhận kết quả", readonly=True, copy=False)
    approval_recorded_date = fields.Datetime("Thời điểm ghi nhận", readonly=True, copy=False)
    approval_attachment_ids = fields.Many2many("ir.attachment", "tp_equipment_proposal_approval_rel", "proposal_id",
                                               "attachment_id", "Tệp căn cứ duyệt", readonly=True, copy=False)

    line_ids = fields.One2many("tp.equipment.proposal.line", "proposal_id", "Dòng đề xuất", copy=True)
    line_count = fields.Integer("Số dòng", compute="_compute_totals", store=True, compute_sudo=False)
    amount_total = fields.Monetary("Tổng dự toán", currency_field="currency_id", compute="_compute_totals", store=True,
                                    compute_sudo=False)
    amount_total_known = fields.Boolean("Đủ dự toán mọi dòng", compute="_compute_totals", store=True, compute_sudo=False)
    progress = fields.Selection(PROGRESS, "Tiến độ thực hiện", compute="_compute_progress", store=True, index=True)
    note = fields.Text("Ghi chú")
    source_ref = fields.Char("Nguồn dữ liệu", readonly=True, copy=False)

    # ------------------------------------------------------------------ computes
    @api.depends("line_ids.estimate_amount", "line_ids.estimate_amount_known")
    def _compute_totals(self):
        for proposal in self:
            proposal.line_count = len(proposal.line_ids)
            proposal.amount_total = sum(proposal.line_ids.mapped("estimate_amount"))
            proposal.amount_total_known = bool(proposal.line_ids) and all(proposal.line_ids.mapped("estimate_amount_known"))

    @api.depends("line_ids.progress", "review_state", "approval_state")
    def _compute_progress(self):
        for proposal in self:
            lines = proposal.line_ids
            states = set(lines.mapped("progress"))
            if proposal.review_state == "cancel" or proposal.approval_state == "rejected":
                proposal.progress = "cancel"
            elif not lines or states == {"cancel"}:
                proposal.progress = "cancel" if lines else "waiting"
            elif states <= {"done", "cancel"}:
                proposal.progress = "done"
            elif states & {"done", "partial"}:
                proposal.progress = "partial"
            elif "in_progress" in states:
                proposal.progress = "in_progress"
            elif "not_started" in states:
                proposal.progress = "not_started"
            else:
                proposal.progress = "waiting"

    # ------------------------------------------------------------------ ORM
    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        internal = self.env.context.get("tp_proposal_internal") is INTERNAL
        for vals in vals_list:
            if not internal:
                for key in ("review_state", "approval_state", "approval_source", "approval_ref", "approval_date",
                            "approval_check", "approval_note", "approver_text", "approval_attachment_ids",
                            "approval_recorded_by_id", "approval_recorded_date", "responsible_id",
                            "resubmit_count", "return_reason", "cancel_reason", "review_ids"):
                    vals.pop(key, None)
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = self.env["ir.sequence"].sudo().next_by_code("tp.equipment.proposal") or "/"
        return super().create(vals_list)

    def write(self, vals):
        check_admin(self.env)
        if self.env.context.get("tp_proposal_internal") is not INTERNAL:
            free = {"note", "message_main_attachment_id"}
            guarded = {"review_state", "approval_state", "approval_source", "approval_ref", "approval_date",
                       "approval_check", "approval_note", "approver_text", "approval_attachment_ids",
                       "resubmit_count", "return_reason", "cancel_reason", "responsible_id",
                       "approval_recorded_by_id", "approval_recorded_date", "review_ids"}
            if guarded & set(vals):
                raise UserError(_("Dùng các nút rà soát / ghi nhận kết quả duyệt trên đề xuất."))
            locked = self.filtered(lambda p: p.review_state not in EDITABLE_REVIEW)
            if locked and set(vals) - free:
                raise UserError(_("Đề xuất %(name)s đang “%(state)s”: chỉ sửa được khi Nháp hoặc Trả lại.",
                                  name=locked[0].name, state=dict(REVIEW_STATES)[locked[0].review_state]))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_draft(self):
        check_admin(self.env)
        for proposal in self:
            if proposal.review_state != "draft" or proposal.review_ids:
                raise UserError(_("Chỉ xóa được đề xuất nháp chưa gửi rà soát; đề xuất khác dùng Hủy."))

    # ------------------------------------------------------------------ helpers
    def _tp_lock(self):
        check_admin(self.env)
        if not self:
            return
        if any(record.company_id not in self.env.companies for record in self):
            raise UserError(_('Công ty ngoài phạm vi được phép.'))
        self.env.cr.execute(SQL("SELECT id FROM tp_equipment_proposal WHERE id IN %s ORDER BY id FOR UPDATE", tuple(self.ids)))
        self.invalidate_recordset()
        self.line_ids._tp_lock()

    def _tp_log(self, action, reason=False, state_from=False, state_to=False):
        self.env["tp.equipment.proposal.review"].with_context(tp_proposal_internal=INTERNAL).create([{
            "proposal_id": proposal.id,
            "action": action,
            "reason": reason or False,
            "state_from": state_from or proposal.review_state,
            "state_to": state_to or proposal.review_state,
            "user_id": self.env.uid,
        } for proposal in self])

    def _tp_set_review(self, new_state, action, reason=False, extra=None):
        for proposal in self:
            old = proposal.review_state
            vals = dict(extra or {}, review_state=new_state)
            proposal.with_context(tp_proposal_internal=INTERNAL).write(vals)
            proposal._tp_log(action, reason, old, new_state)
            body = dict(REVIEW_ACTIONS)[action] + (f": {reason}" if reason else "")
            proposal.message_post(body=body, subtype_xmlid="mail.mt_note")

    def _tp_check_lines(self):
        for proposal in self:
            if not proposal.line_ids:
                raise UserError(_("Thêm ít nhất một dòng đề xuất."))
            for index, line in enumerate(proposal.line_ids, start=1):
                if not (line.description or "").strip():
                    raise UserError(_("Dòng %s: ghi đối tượng / nội dung cần.", index))
                if line.kind in ("repair", "upgrade", "transfer", "dispose") and not line.equipment_id:
                    raise UserError(_("Dòng %s: chọn thiết bị cũ đã xác minh (sửa / nâng cấp / chuyển / thanh lý).",
                                      index))

    # ------------------------------------------------------------------ review actions
    def action_submit(self):
        self._tp_lock()
        for proposal in self.filtered(lambda p: p.review_state == "draft"):
            proposal._tp_check_lines()
            proposal._tp_set_review("review", "submit")
        return True

    def action_resubmit(self):
        self._tp_lock()
        for proposal in self.filtered(lambda p: p.review_state == "returned"):
            proposal._tp_check_lines()
            proposal._tp_set_review("review", "resubmit", extra={"resubmit_count": proposal.resubmit_count + 1})
        return True

    def action_reviewed(self):
        self._tp_lock()
        for proposal in self.filtered(lambda p: p.review_state == "review"):
            proposal._tp_set_review("reviewed", "reviewed")
        return True

    def action_open_return(self):
        self.ensure_one()
        if self.review_state != "review":
            raise UserError(_("Chỉ trả lại đề xuất đang rà soát."))
        return self.env["tp.equipment.reason.wizard"]._tp_open(
            self, "return", _("Trả lại đề xuất"), _("Lý do được lưu vào nhật ký rà soát và hiện trên đề xuất."))

    def action_open_cancel(self):
        self.ensure_one()
        return self.env["tp.equipment.reason.wizard"]._tp_open(self, "cancel", _("Hủy đề xuất"))

    def _tp_apply_reason(self, action, reason):
        self._tp_lock()
        self.ensure_one()
        if action == "return":
            if self.review_state != "review":
                raise UserError(_("Chỉ trả lại đề xuất đang rà soát."))
            self._tp_set_review("returned", "return", reason, extra={"return_reason": reason})
            return True
        if action == "cancel":
            if self.review_state == "cancel":
                raise UserError(_("Đề xuất đã hủy."))
            started = self.line_ids.filtered(lambda line: line.progress in ("in_progress", "partial", "done"))
            if started:
                raise UserError(_("Đề xuất đã có dòng đang / đã thực hiện; đánh dấu từng dòng còn lại “không thực hiện”."))
            self._tp_set_review("cancel", "cancel", reason, extra={"cancel_reason": reason})
            return True
        raise UserError(_("Thao tác không hợp lệ."))

    def action_open_approval(self):
        check_admin(self.env)
        self.ensure_one()
        if self.review_state != "reviewed":
            raise UserError(_("Hoàn tất rà soát trước khi ghi nhận kết quả duyệt."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Ghi nhận kết quả duyệt"),
            "res_model": "tp.equipment.proposal.approval",
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.proposal_approval_form").id, "form")],
            "target": "new",
            "context": {"default_proposal_id": self.id},
        }

    need_type = fields.Selection(NEED_TYPES, "Nhu cầu", compute="_compute_need_type", search="_search_need_type",
                                 help="Tóm tắt nhu cầu của các dòng (Mua mới / Đổi máy / Sửa hoặc nâng cấp).")

    @api.depends("line_ids.kind", "line_ids.equipment_id")
    def _compute_need_type(self):
        for proposal in self:
            needs = {need_of(line.kind, bool(line.equipment_id)) for line in proposal.line_ids}
            proposal.need_type = needs.pop() if len(needs) == 1 else False

    def _search_need_type(self, operator, value):
        domain = need_search_domain(operator, value)
        if domain is NotImplemented:
            return NotImplemented
        return Domain("line_ids", "any", domain)

    @api.onchange("requester_employee_id")
    def _onchange_requester_department(self):
        # Short form: the department comes from HR (read only to fill the field; the admin may still change it).
        employee = self.requester_employee_id.sudo()
        if employee.department_id:
            self.requester_department_id = employee.department_id

    requester_summary = fields.Char("Người / bộ phận yêu cầu", compute="_compute_tp_ui_displays")
    date_display = fields.Char("Ngày chứng từ", compute="_compute_tp_ui_displays")
    amount_display = fields.Char("Chi phí dự kiến", compute="_compute_tp_ui_displays")

    @api.depends("requester_employee_id", "requester_department_id", "requester_text",
                 "date", "date_known", "amount_total", "amount_total_known", "currency_id")
    def _compute_tp_ui_displays(self):
        for proposal in self:
            parts = [p for p in (proposal.requester_employee_id.name, proposal.requester_department_id.name) if p]
            proposal.requester_summary = " · ".join(parts) if parts else (proposal.requester_text or "Chưa ghi nhận")
            if proposal.date_known and proposal.date:
                proposal.date_display = proposal.date.strftime("%d/%m/%Y")
            elif proposal.date:
                proposal.date_display = f"{proposal.date.strftime('%d/%m/%Y')} (ngày ghi)"
            else:
                proposal.date_display = "Chưa có"
            if proposal.amount_total_known:
                sym = proposal.currency_id.symbol or proposal.currency_id.name or "₫"
                proposal.amount_display = f"{round(proposal.amount_total or 0):,}".replace(",", ".") + f" {sym}"
            else:
                proposal.amount_display = "Chưa có"

    def action_open_detail(self):
        check_admin(self.env)
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": "tp.equipment.proposal",
            "res_id": self.id,
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.proposal_form").id, "form")],
            "target": "current",
            "context": {"tp_eq_leaf": "tp_equipment.menu_proposals"},
        }

    def action_print_summary(self):
        check_admin(self.env)
        self.ensure_one()
        return {"type": "ir.actions.act_url", "url": f"/tp_equipment/proposal/{self.id}/summary.xlsx", "target": "new"}


class TpEquipmentProposalLine(models.Model):
    _name = "tp.equipment.proposal.line"
    _description = "Dòng đề xuất thiết bị"
    _order = "proposal_id, sequence, id"

    proposal_id = fields.Many2one("tp.equipment.proposal", "Đề xuất", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    kind = fields.Selection(LINE_KINDS, "Phương án", required=True, default="purchase")
    description = fields.Char("Đối tượng / nội dung cần", required=True)
    equipment_id = fields.Many2one("maintenance.equipment", "Thiết bị cũ (đã xác minh)", ondelete="restrict",
                                   domain=[("tp_lifecycle", "=", "active")], index="btree_not_null",
                                   help="Với mua mới: máy được thay (nếu có). Sửa / nâng cấp / chuyển: máy cũ.")
    equipment_text = fields.Char("Thiết bị cũ theo nguồn", help="Ghi nguyên văn khi chưa xác minh đúng máy.")
    category_id = fields.Many2one("maintenance.equipment.category", "Phân loại", ondelete="restrict")
    current_state = fields.Text("Hiện trạng / lỗi")
    solution = fields.Text("Phương án chi tiết")
    desired_config = fields.Text("Cấu hình mong muốn")
    quantity = fields.Integer("Số lượng", help="0 = chưa xác nhận số lượng. Mua mới phải có số lượng trước khi nhận.")
    uom_text = fields.Char("Đơn vị", default="chiếc")
    currency_id = fields.Many2one(related="proposal_id.currency_id")
    estimate_amount = fields.Monetary("Dự toán (thành tiền)", currency_field="currency_id",
                                      help="Thành tiền theo đề xuất; không phải đơn giá, không phải giá mua thực tế.")
    estimate_amount_known = fields.Boolean("Đã xác nhận dự toán", help="Bật cả khi dự toán bằng 0; tắt nghĩa là chưa biết.")
    tax_note = fields.Selection(TAX_NOTE, "Thuế", default="unknown", required=True)
    target_employee_id = fields.Many2one("hr.employee", "Người nhận (chuyển máy)", ondelete="restrict")
    target_department_id = fields.Many2one("hr.department", "Bộ phận nhận (chuyển máy)", ondelete="restrict")
    approved = fields.Boolean("Dòng được duyệt", copy=False,
                              help="Chỉ dùng khi kết quả duyệt là “Duyệt một phần”.")
    not_executed = fields.Boolean("Không thực hiện", readonly=True, copy=False)
    not_executed_reason = fields.Text("Lý do không thực hiện", readonly=True, copy=False)
    source_ref = fields.Char("Nguồn dữ liệu", readonly=True, copy=False)

    receipt_line_ids = fields.One2many("tp.equipment.receipt.line", "proposal_line_id", "Dòng nhập kho", readonly=True)
    request_ids = fields.One2many("maintenance.request", "tp_proposal_line_id", "Phiếu sửa chữa", readonly=True)
    move_ids = fields.One2many("tp.equipment.move", "proposal_line_id", "Phiếu bàn giao", readonly=True)
    received_qty = fields.Integer("Đã nhận", compute="_compute_progress", store=True)
    reserved_qty = fields.Integer("Đang trên phiếu nhập nháp", compute="_compute_progress", store=True)
    remaining_qty = fields.Integer("Còn lại", compute="_compute_progress", store=True)
    progress = fields.Selection(PROGRESS, "Tiến độ", compute="_compute_progress", store=True, index=True)
    can_execute = fields.Boolean("Được thực hiện", compute="_compute_can_execute")
    review_state = fields.Selection(related="proposal_id.review_state", string="Rà soát")
    approval_state = fields.Selection(related="proposal_id.approval_state", string="Kết quả duyệt")
    new_equipment_ids = fields.Many2many("maintenance.equipment", compute="_compute_new_equipment",
                                         string="Thiết bị mới đã nhận")

    @api.depends("receipt_line_ids.state", "receipt_line_ids.equipment_id", "request_ids.tp_state", "move_ids.state",
                 "move_ids.reversed_by_id", "quantity", "not_executed", "kind", "approved",
                 "proposal_id.review_state", "proposal_id.approval_state")
    def _compute_progress(self):
        for line in self:
            received = len(line.receipt_line_ids.filtered(lambda r: r.state == "done"))
            reserved = len(line.receipt_line_ids.filtered(lambda r: r.state == "draft"))
            line.received_qty = received
            line.reserved_qty = reserved
            line.remaining_qty = max((line.quantity or 0) - received - reserved, 0)
            if line.not_executed:
                line.progress = "cancel"
                continue
            if line.kind == "purchase":
                if line.quantity and received >= line.quantity:
                    progress = "done"
                elif received:
                    progress = "partial"
                elif reserved:
                    progress = "in_progress"
                else:
                    progress = "not_started"
            elif line.kind in ("repair", "upgrade"):
                requests = line.request_ids.filtered(lambda r: r.tp_state != "cancel")
                if requests and all(r.tp_state == "done" for r in requests):
                    progress = "done"
                elif requests:
                    progress = "in_progress"
                else:
                    progress = "not_started"
            else:
                moves = line.move_ids.filtered(lambda m: m.state != "cancel" and not m.reversed_by_id)
                if moves.filtered(lambda m: m.state == "done"):
                    progress = "done"
                elif moves:
                    progress = "in_progress"
                else:
                    progress = "not_started"
            if progress == "not_started" and not line._tp_is_executable():
                progress = "waiting"
            line.progress = progress

    # Not stored and deliberately not depending on equipment_id: during the form onchange the chosen need
    # stays as typed; the inverse writes the real kind on save and every later read derives it again.
    need_type = fields.Selection(NEED_TYPES, "Nhu cầu", compute="_compute_need_type", inverse="_inverse_need_type",
                                 search="_search_need_type", readonly=False)

    @api.depends("kind")
    def _compute_need_type(self):
        for line in self:
            line.need_type = need_of(line.kind, bool(line.equipment_id))

    def _inverse_need_type(self):
        for line in self:
            vals = {}
            if line.need_type in ("purchase", "swap") and line.kind != "purchase":
                vals["kind"] = "purchase"
            elif line.need_type == "repair" and line.kind not in ("repair", "upgrade"):
                vals["kind"] = "repair"
            if line.need_type == "purchase" and line.equipment_id:
                vals["equipment_id"] = False
            if vals:
                line.write(vals)

    def _search_need_type(self, operator, value):
        return need_search_domain(operator, value)

    @api.onchange("category_id", "need_type")
    def _onchange_short_description(self):
        # Short form: "Nội dung cần" defaults to the machine type; the admin can overwrite it.
        if not (self.description or "").strip() and self.category_id:
            self.description = self.category_id.name

    estimate_display = fields.Char("Dự toán", compute="_compute_estimate_display")

    @api.depends("estimate_amount", "estimate_amount_known", "currency_id")
    def _compute_estimate_display(self):
        for line in self:
            if line.estimate_amount_known:
                sym = line.currency_id.symbol or line.currency_id.name or "₫"
                line.estimate_display = f"{round(line.estimate_amount or 0):,}".replace(",", ".") + f" {sym}"
            else:
                line.estimate_display = "Chưa có"

    def _tp_is_executable(self):
        self.ensure_one()
        proposal = self.proposal_id
        if self.not_executed or proposal.review_state != "reviewed":
            return False
        return proposal.approval_state == "approved" or (proposal.approval_state == "partial" and self.approved)

    def _compute_can_execute(self):
        for line in self:
            line.can_execute = line._tp_is_executable() and line.progress not in ("done", "cancel")

    def _compute_new_equipment(self):
        for line in self:
            line.new_equipment_ids = line.receipt_line_ids.equipment_id

    def _tp_refresh_progress(self):
        self.env.add_to_compute(self._fields["progress"], self)
        self.env.add_to_compute(self.proposal_id._fields["progress"], self.proposal_id)

    @api.constrains("quantity", "estimate_amount")
    def _check_values(self):
        for line in self:
            if line.quantity < 0 or (line.estimate_amount or 0) < 0:
                raise ValidationError(_("Số lượng và dự toán không được âm."))

    @api.constrains("kind", "equipment_id", "target_employee_id", "target_department_id")
    def _check_kind(self):
        for line in self:
            if line.kind == "transfer" and line.target_employee_id and line.target_department_id:
                raise ValidationError(_("Chuyển máy: chọn người nhận hoặc bộ phận nhận, không chọn cả hai."))

    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        if self.env.context.get("tp_proposal_internal") is not INTERNAL:
            proposals = self.env["tp.equipment.proposal"].browse(
                {v.get("proposal_id") for v in vals_list if v.get("proposal_id")})
            if proposals.filtered(lambda p: p.review_state not in EDITABLE_REVIEW):
                raise UserError(_("Chỉ thêm dòng khi đề xuất Nháp hoặc Trả lại."))
            for vals in vals_list:
                for field in ("approved", "not_executed", "not_executed_reason"):
                    vals.pop(field, None)
        return super().create(vals_list)

    def write(self, vals):
        check_admin(self.env)
        if self.env.context.get("tp_proposal_internal") is not INTERNAL:
            if "proposal_id" in vals:
                raise UserError(_("Không chuyển dòng sang đề xuất khác."))
            if {"not_executed", "not_executed_reason"} & set(vals):
                raise UserError(_("Dùng nút “Không thực hiện” trên dòng."))
            if "approved" in vals:
                raise UserError(_("Ghi nhận dòng được duyệt qua hồ sơ kết quả duyệt."))
            other = set(vals) - {"approved", "sequence"}
            locked = self.filtered(lambda line: line.proposal_id.review_state not in EDITABLE_REVIEW)
            if locked and other:
                raise UserError(_("Đề xuất đã gửi rà soát: trả lại đề xuất để sửa dòng."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_editable(self):
        if self.filtered(lambda line: line.proposal_id.review_state not in EDITABLE_REVIEW
                         or line.receipt_line_ids or line.request_ids or line.move_ids):
            raise UserError(_("Chỉ bỏ dòng của đề xuất Nháp / Trả lại chưa thực hiện."))

    def _tp_lock(self):
        if not self:
            return
        try:
            with self.env.cr.savepoint(flush=False):
                self.env.cr.execute(SQL("SELECT id FROM tp_equipment_proposal_line WHERE id IN %s FOR UPDATE NOWAIT",
                                        tuple(self.ids)))
        except pg_errors.LockNotAvailable:
            raise UserError(_("Dòng đề xuất đang được xử lý ở thao tác khác. Thử lại sau ít giây.")) from None
        self.invalidate_recordset()

    def _tp_check_execute(self, kinds):
        self.ensure_one()
        check_admin(self.env)
        if self.kind not in kinds:
            raise UserError(_("Phương án của dòng không dùng thao tác này."))
        if not self._tp_is_executable():
            raise UserError(_("Dòng chưa đủ điều kiện thực hiện: cần hoàn tất rà soát và có kết quả duyệt kèm căn cứ."))
        if self.progress in ("done", "cancel"):
            raise UserError(_("Dòng đã hoàn tất hoặc không thực hiện."))

    # ------------------------------------------------------------------ execution actions
    def action_create_receipt(self):
        """Purchase branch: a draft receipt with one row per remaining device (opened, not saved)."""
        self._tp_check_execute(("purchase",))
        if self.quantity <= 0:
            raise UserError(_("Xác nhận số lượng của dòng mua mới trước khi nhận (đề xuất trả lại để sửa)."))
        if self.remaining_qty <= 0:
            raise UserError(_("Đã nhận / đang nhận đủ số lượng của dòng. Không nhận vượt."))
        line_vals = {
            "category_id": self.category_id.id,
            "name": self.description,
            "config_note": self.desired_config or False,
            "proposal_line_id": self.id,
        }
        return {
            "type": "ir.actions.act_window",
            "name": _("Phiếu nhập theo đề xuất %s", self.proposal_id.name),
            "res_model": "tp.equipment.receipt",
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.receipt_form").id, "form")],
            "target": "current",
            "context": {
                "default_source": "purchase",
                "default_note": _("Theo đề xuất %(name)s – %(desc)s", name=self.proposal_id.name, desc=self.description),
                "default_line_ids": [(0, 0, dict(line_vals)) for _i in range(self.remaining_qty)],
                "tp_eq_leaf": "tp_equipment.menu_receipts",
            },
        }

    def action_create_request(self):
        """Repair / upgrade branch: keeps the same equipment ID (no new machine)."""
        self._tp_check_execute(("repair", "upgrade"))
        if self.request_ids.filtered(lambda r: r.tp_state in ("new", "in_progress", "vendor")):
            raise UserError(_("Dòng đã có phiếu sửa chữa đang mở."))
        kind = "upgrade" if self.kind == "upgrade" else "fault"
        action = self.equipment_id.with_context(tp_request_kind=kind).action_tp_new_request()
        action["context"].update({
            "default_tp_proposal_line_id": self.id,
            "default_tp_symptom": self.current_state or self.description,
            "default_name": _("%(kind)s – %(name)s (đề xuất %(proposal)s)",
                              kind=dict(LINE_KINDS)[self.kind], name=self.equipment_id.display_name,
                              proposal=self.proposal_id.name),
        })
        return action

    def action_create_move(self):
        """Transfer old machine / dispose branch: a move document, same equipment ID."""
        self._tp_check_execute(("transfer", "dispose"))
        if self.move_ids.filtered(lambda m: m.state in ("draft", "pending")):
            raise UserError(_("Dòng đã có phiếu đang mở."))
        equipment = self.equipment_id
        if self.kind == "transfer":
            move_type = "transfer" if equipment.tp_custody in ("employee", "department", "location") else "assign"
            context = {"default_target_custody": "department" if self.target_department_id else "employee",
                       "default_target_employee_id": self.target_employee_id.id,
                       "default_target_department_id": self.target_department_id.id}
        else:
            move_type = "retire"
            context = {"default_retire_reason": "scrapped"}
        context.update({
            "default_move_type": move_type,
            "default_line_ids": [(0, 0, {"equipment_id": equipment.id})],
            "default_proposal_line_id": self.id,
            "default_reason": _("Theo đề xuất %(name)s – %(desc)s", name=self.proposal_id.name, desc=self.description),
            "tp_eq_leaf": "tp_equipment.menu_moves",
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Lập phiếu"),
            "res_model": "tp.equipment.move",
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.move_form").id, "form")],
            "target": "current",
            "context": context,
        }

    def action_open_not_executed(self):
        self.ensure_one()
        check_admin(self.env)
        if self.progress == "done":
            raise UserError(_("Dòng đã hoàn tất."))
        return self.env["tp.equipment.reason.wizard"]._tp_open(self, "not_executed", _("Dòng không thực hiện"))

    def _tp_apply_reason(self, action, reason):
        check_admin(self.env)
        self.ensure_one()
        if action != "not_executed":
            raise UserError(_("Thao tác không hợp lệ."))
        if self.receipt_line_ids.filtered(lambda r: r.state == "draft") or \
                self.request_ids.filtered(lambda r: r.tp_state in ("new", "in_progress", "vendor")) or \
                self.move_ids.filtered(lambda m: m.state in ("draft", "pending")):
            raise UserError(_("Dòng còn phiếu nhập / sửa / bàn giao đang mở: xử lý phiếu đó trước."))
        self.with_context(tp_proposal_internal=INTERNAL).write({"not_executed": True, "not_executed_reason": reason})
        self.proposal_id._tp_log("line_cancel", f"{self.description}: {reason}")
        self.proposal_id.message_post(body=_("Dòng “%(desc)s” không thực hiện: %(reason)s",
                                             desc=self.description, reason=reason), subtype_xmlid="mail.mt_note")
        return True


class TpEquipmentProposalReview(models.Model):
    _name = "tp.equipment.proposal.review"
    _description = "Nhật ký rà soát đề xuất"
    _order = "date desc, id desc"

    proposal_id = fields.Many2one("tp.equipment.proposal", "Đề xuất", required=True, ondelete="cascade", index=True)
    date = fields.Datetime("Thời điểm", default=fields.Datetime.now, required=True, readonly=True)
    user_id = fields.Many2one("res.users", "Người thao tác trên hệ thống", required=True, readonly=True)
    action = fields.Selection(REVIEW_ACTIONS, "Thao tác", required=True, readonly=True)
    state_from = fields.Selection(REVIEW_STATES, "Từ", readonly=True)
    state_to = fields.Selection(REVIEW_STATES, "Sang", readonly=True)
    reason = fields.Text("Lý do / nội dung", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        if self.env.context.get("tp_proposal_internal") is not INTERNAL:
            raise UserError(_("Nhật ký chỉ tạo từ thao tác nghiệp vụ."))
        return super().create(vals_list)

    def write(self, vals):
        raise UserError(_("Nhật ký rà soát không sửa được."))

    @api.ondelete(at_uninstall=False)
    def _unlink_never(self):
        if self.env.context.get("tp_equipment_force_delete") is not INTERNAL:
            raise UserError(_("Nhật ký rà soát không xóa được."))


class TpEquipmentProposalApproval(models.TransientModel):
    _name = "tp.equipment.proposal.approval"
    _description = "Ghi nhận kết quả duyệt đề xuất"

    proposal_id = fields.Many2one("tp.equipment.proposal", "Đề xuất", required=True, readonly=True)
    approval_state = fields.Selection([s for s in APPROVAL_STATES if s[0] != "unverified"], "Kết quả duyệt",
                                      required=True)
    approval_source = fields.Selection(APPROVAL_SOURCES, "Nguồn duyệt", required=True, default="base")
    approval_ref = fields.Char("Số / mã tham chiếu")
    approval_date = fields.Date("Ngày duyệt", required=True)
    approver_text = fields.Char("Người duyệt (theo căn cứ)", required=True)
    approval_check = fields.Selection(APPROVAL_CHECK, "Mức kiểm chứng", required=True)
    approval_note = fields.Text("Ghi chú")
    attachment_ids = fields.Many2many("ir.attachment", string="Tệp căn cứ")
    line_ids = fields.Many2many("tp.equipment.proposal.line", string="Dòng được duyệt",
                                domain="[('proposal_id', '=', proposal_id)]")

    def action_confirm(self):
        check_admin(self.env)
        self.ensure_one()
        proposal = self.proposal_id
        proposal._tp_lock()
        if self.line_ids - proposal.line_ids:
            raise UserError(_("Dòng được duyệt phải thuộc đúng đề xuất."))
        if proposal.review_state != "reviewed":
            raise UserError(_("Hoàn tất rà soát trước khi ghi nhận kết quả duyệt."))
        if proposal.line_ids.filtered(lambda line: line.progress in ("in_progress", "partial", "done")):
            raise UserError(_("Đề xuất đã thực hiện; không ghi đè kết quả duyệt. Ghi chú bổ sung ở trao đổi."))
        if not (self.approval_ref or "").strip() and not self.attachment_ids:
            raise UserError(_("Cần số tham chiếu hoặc tệp căn cứ duyệt; không ghi nhận duyệt khi chưa có bằng chứng."))
        if self.approval_state == "partial" and not self.line_ids:
            raise UserError(_("Chọn các dòng được duyệt."))
        if self.approval_date > fields.Date.context_today(self):
            raise UserError(_("Ngày duyệt không được ở tương lai."))
        if self.attachment_ids:
            self.attachment_ids.sudo().write({"res_model": proposal._name, "res_id": proposal.id, "public": False})
        proposal.with_context(tp_proposal_internal=INTERNAL).write({
            "approval_state": self.approval_state,
            "approval_source": self.approval_source,
            "approval_ref": (self.approval_ref or "").strip() or False,
            "approval_date": self.approval_date,
            "approver_text": self.approver_text.strip(),
            "approval_check": self.approval_check,
            "approval_note": self.approval_note or False,
            "approval_recorded_by_id": self.env.uid,
            "approval_recorded_date": fields.Datetime.now(),
            "approval_attachment_ids": [(6, 0, self.attachment_ids.ids)],
        })
        proposal.line_ids.with_context(tp_proposal_internal=INTERNAL).write({"approved": False})
        if self.approval_state == "partial":
            self.line_ids.with_context(tp_proposal_internal=INTERNAL).write({"approved": True})
        summary = Markup("%s · %s · %s %s") % (
            dict(APPROVAL_STATES)[self.approval_state], dict(APPROVAL_SOURCES)[self.approval_source],
            self.approval_ref or _("(không số)"), self.approval_date.strftime("%d/%m/%Y"))
        proposal._tp_log("approval", str(summary))
        proposal.message_post(body=Markup("%s: %s") % (_("Ghi nhận kết quả duyệt"), summary),
                              subtype_xmlid="mail.mt_note")
        return {"type": "ir.actions.act_window_close"}
