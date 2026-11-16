"""Equipment receipts (phiếu nhập): one line = one physical device, registered on validation."""
import uuid

from psycopg2 import errors as pg_errors

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import SQL

from .common import (
    ASSET_CLASS,
    INTERNAL,
    OWNERSHIP,
    TECH_STATE,
    WARRANTY_BASIS,
    check_admin,
    lock_records,
)

RECEIPT_SOURCE = [
    ("purchase", "Mua mới"),
    ("rental", "Thuê"),
    ("transfer_in", "Nhận từ đơn vị khác"),
    ("gift", "Được tặng / tài trợ"),
    ("found", "Phát hiện khi kiểm kê"),
    ("other", "Khác"),
]
RECEIPT_STATES = [("draft", "Nháp"), ("done", "Đã nhập kho"), ("cancel", "Đã hủy")]


class TpEquipmentReceipt(models.Model):
    _name = "tp.equipment.receipt"
    _description = "Phiếu nhập thiết bị"
    _inherit = ["tp.equipment.secure.mixin"]
    _order = "date desc, id desc"

    name = fields.Char("Số phiếu", readonly=True, copy=False, default="/", index=True)
    date = fields.Date("Ngày nhập", required=True, default=fields.Date.context_today, tracking=True)
    source = fields.Selection(RECEIPT_SOURCE, "Nguồn nhập", required=True, default="purchase", tracking=True)
    supplier_id = fields.Many2one("res.partner", "Nhà cung cấp / bên giao", tracking=True, ondelete="restrict")
    document_ref = fields.Char("Số chứng từ", tracking=True,
                               help="Hóa đơn, phiếu giao hàng, hợp đồng thuê… Để trống nếu chưa có chứng từ.")
    location_id = fields.Many2one("tp.equipment.location", "Nhập vào vị trí / kho", tracking=True,
                                  ondelete="restrict")
    note = fields.Text("Ghi chú")
    state = fields.Selection(RECEIPT_STATES, "Trạng thái", default="draft", required=True, readonly=True,
                             copy=False, tracking=True, index=True)
    done_date = fields.Datetime("Thời điểm nhập kho", readonly=True, copy=False)
    done_by_id = fields.Many2one("res.users", "Người nhập kho", readonly=True, copy=False)
    company_id = fields.Many2one("res.company", "Công ty", default=lambda self: self.env.company, required=True)
    line_ids = fields.One2many("tp.equipment.receipt.line", "receipt_id", "Thiết bị nhập", copy=True)
    line_count = fields.Integer("Số thiết bị", compute="_compute_counts")
    equipment_count = fields.Integer("Thiết bị đã tạo", compute="_compute_counts")
    idempotency_key = fields.Char("Khóa chống trùng", copy=False, readonly=True,
                                  default=lambda self: uuid.uuid4().hex)

    _idempotency_unique = models.UniqueIndex("(idempotency_key) WHERE idempotency_key IS NOT NULL",
                                             "Phiếu nhập này đã được tạo.")

    @api.depends("line_ids", "line_ids.equipment_id")
    def _compute_counts(self):
        for receipt in self:
            receipt.line_count = len(receipt.line_ids)
            receipt.equipment_count = len(receipt.line_ids.equipment_id)

    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        existing = self.browse()
        to_create = []
        for vals in vals_list:
            key = vals.get("idempotency_key")
            found = key and self.search([("idempotency_key", "=", key)], limit=1)
            if found:
                existing |= found
                continue
            vals["state"] = "draft"
            vals.pop("done_date", None)
            vals.pop("done_by_id", None)
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = self.env["ir.sequence"].sudo().next_by_code("tp.equipment.receipt") or "/"
            to_create.append(vals)
        return existing | super().create(to_create) if to_create else existing

    def write(self, vals):
        check_admin(self.env)
        lock_records(self)
        if self.env.context.get("tp_equipment_receipt_internal") is not INTERNAL:
            if {"state", "done_date", "done_by_id", "idempotency_key"} & set(vals):
                raise UserError(_("Dùng nút Nhập kho / Hủy để đổi trạng thái phiếu."))
            for receipt in self:
                if receipt.state != "draft" and set(vals) - {"note", "message_main_attachment_id"}:
                    raise UserError(_("Phiếu nhập %(name)s đã %(state)s, không sửa được.", name=receipt.name,
                                      state=dict(RECEIPT_STATES)[receipt.state].lower()))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_draft(self):
        check_admin(self.env)
        for receipt in self:
            if receipt.state != "draft":
                raise UserError(_("Chỉ xóa được phiếu nhập nháp."))

    def _tp_lock(self):
        try:
            with self.env.cr.savepoint(flush=False):
                self.env.cr.execute(SQL("SELECT id FROM tp_equipment_receipt WHERE id IN %s FOR UPDATE NOWAIT",
                                        tuple(self.ids)))
        except pg_errors.LockNotAvailable:
            raise UserError(_("Phiếu nhập đang được xử lý ở thao tác khác. Thử lại sau ít giây.")) from None
        self.invalidate_recordset()

    def _tp_check_lines(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("Thêm ít nhất một thiết bị vào phiếu nhập."))
        proposals = self.line_ids.proposal_line_id.sorted("id")
        if proposals:
            lock_records(proposals.proposal_id.sorted("id"))
            proposals._tp_lock()
            proposals.invalidate_recordset()
            for proposal in proposals:
                proposal._tp_check_execute(("purchase",))
                received = self.env["tp.equipment.receipt.line"].search_count([
                    ("proposal_line_id", "=", proposal.id), ("state", "=", "done"),
                ])
                incoming = len(self.line_ids.filtered(lambda line: line.proposal_line_id == proposal))
                if proposal.quantity <= 0 or received + incoming > proposal.quantity:
                    raise UserError(_("Dòng đề xuất %(line)s: nhập vượt số lượng được phép.",
                                      line=proposal.description))
                if proposal.proposal_id.company_id != self.company_id or self.source != "purchase":
                    raise UserError(_("Phiếu nhận theo đề xuất mua phải cùng công ty và có nguồn Mua mới."))
        serials = {}
        for index, line in enumerate(self.line_ids, start=1):
            missing = []
            if not (line.name or "").strip():
                missing.append(_("tên thiết bị"))
            if not line.category_id:
                missing.append(_("phân loại"))
            if not line.technical_state:
                missing.append(_("tình trạng kiểm tra khi nhận"))
            if missing:
                raise UserError(_("Dòng %(index)s: thiếu %(what)s.", index=index, what=", ".join(missing)))
            serial = (line.serial_no or "").strip()
            if serial:
                if serial in serials:
                    raise UserError(_("Serial %(serial)s lặp ở dòng %(a)s và %(b)s.", serial=serial,
                                      a=serials[serial], b=index))
                serials[serial] = index
        if serials:
            clash = self.env["maintenance.equipment"].with_context(active_test=False).search(
                [("serial_no", "in", list(serials))], limit=1)
            if clash:
                raise UserError(_("Serial %(serial)s đã có ở thiết bị %(name)s.", serial=clash.serial_no,
                                  name=clash.display_name))

    def action_done(self):
        check_admin(self.env)
        lock_records(self)
        for receipt in self:
            if receipt.state == "done":
                continue  # idempotent replay
            if receipt.state == "cancel":
                raise UserError(_("Phiếu nhập %(name)s đã hủy.", name=receipt.name))
            receipt._tp_lock()
            if receipt.state == "done":
                continue
            receipt._tp_check_lines()
            Equipment = self.env["maintenance.equipment"]
            for index, line in enumerate(receipt.line_ids, start=1):
                equipment = Equipment.create(line._tp_equipment_vals(index))
                equipment.action_tp_register()
                line.with_context(tp_equipment_receipt_internal=INTERNAL).write({"equipment_id": equipment.id})
            receipt.with_context(tp_equipment_receipt_internal=INTERNAL).write({
                "state": "done", "done_date": fields.Datetime.now(), "done_by_id": self.env.uid,
            })
            receipt.message_post(body=_("Đã nhập kho %s thiết bị.", len(receipt.line_ids)),
                                 subtype_xmlid="mail.mt_note")
        return True

    def action_cancel(self):
        check_admin(self.env)
        lock_records(self)
        for receipt in self:
            if receipt.state == "done":
                raise UserError(_("Phiếu đã nhập kho không hủy được; xử lý từng thiết bị bằng phiếu trả / ngừng quản lý."))
            receipt.with_context(tp_equipment_receipt_internal=INTERNAL).write({"state": "cancel"})
        return True

    def action_open_equipment(self):
        check_admin(self.env)
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Thiết bị của %s", self.name),
            "res_model": "maintenance.equipment",
            "view_mode": "list,form",
            "views": [(self.env.ref("tp_equipment.equipment_list").id, "list"),
                      (self.env.ref("tp_equipment.equipment_form").id, "form")],
            "domain": [("id", "in", self.line_ids.equipment_id.ids)],
            "context": {"tp_filter_profile": "equipment", "tp_eq_leaf": "tp_equipment.menu_receipts"},
        }


class TpEquipmentReceiptLine(models.Model):
    _name = "tp.equipment.receipt.line"
    _description = "Dòng phiếu nhập thiết bị"
    _order = "receipt_id, sequence, id"

    receipt_id = fields.Many2one("tp.equipment.receipt", "Phiếu nhập", required=True, ondelete="cascade", index=True)
    state = fields.Selection(related="receipt_id.state", store=True, string="Trạng thái")
    sequence = fields.Integer(default=10)
    category_id = fields.Many2one("maintenance.equipment.category", "Phân loại", required=True, ondelete="restrict")
    asset_class = fields.Selection(ASSET_CLASS, "Loại quản lý", compute="_compute_asset_class", store=True,
                                   readonly=False, required=True, precompute=True)
    name = fields.Char("Tên thiết bị", required=True)
    brand = fields.Char("Hãng")
    model = fields.Char("Model")
    serial_no = fields.Char("Serial")
    cpu = fields.Char("CPU")
    ram = fields.Char("RAM")
    storage = fields.Char("Ổ lưu trữ")
    config_note = fields.Char("Cấu hình khác")
    accessories = fields.Char("Phụ kiện kèm theo")
    ownership = fields.Selection(OWNERSHIP, "Thuộc sở hữu", compute="_compute_ownership", store=True,
                                 readonly=False, required=True, precompute=True)
    owner_partner_id = fields.Many2one("res.partner", "Bên sở hữu / cho thuê", ondelete="restrict")
    currency_id = fields.Many2one(related="receipt_id.company_id.currency_id")
    purchase_value = fields.Monetary("Giá trị", currency_field="currency_id",
                                     help="Để trống khi chưa có chứng từ giá.")
    purchase_value_known = fields.Boolean("Đã xác nhận giá trị", help="Phân biệt chưa biết với giá trị bằng 0.")
    warranty_basis = fields.Selection(WARRANTY_BASIS, "Căn cứ bảo hành", default="unknown", required=True)
    warranty_start = fields.Date("Bắt đầu bảo hành")
    warranty_months = fields.Integer("Bảo hành (tháng)")
    warranty_date = fields.Date("Hết bảo hành (theo chứng từ)")
    warranty_meter_limit = fields.Integer("Giới hạn số đếm")
    technical_state = fields.Selection(TECH_STATE, "Tình trạng khi nhận", required=True,
                                       help="Kiểm tra thực tế lúc nhận; hệ thống không tự ghi “Tốt”.")
    note = fields.Char("Ghi chú")
    equipment_id = fields.Many2one("maintenance.equipment", "Thiết bị đã tạo", readonly=True, ondelete="restrict")
    proposal_line_id = fields.Many2one("tp.equipment.proposal.line", "Dòng đề xuất mua", ondelete="restrict",
                                       copy=False, index=True)

    def _tp_check_proposal_capacity(self):
        proposals = self.proposal_line_id.sorted("id")
        if proposals:
            lock_records(proposals.proposal_id.sorted("id"))
            proposals._tp_lock()
        for proposal in proposals:
            proposal._tp_check_execute(("purchase",))
            lines = self.search([("proposal_line_id", "=", proposal.id), ("state", "in", ("draft", "done"))])
            if proposal.quantity <= 0 or len(lines) > proposal.quantity:
                raise ValidationError(_("Dòng đề xuất %(line)s đã đủ số lượng nhận / đang nhận.",
                                        line=proposal.description))
            if lines.filtered(lambda line: line.receipt_id.company_id != proposal.proposal_id.company_id
                              or line.receipt_id.source != "purchase"):
                raise ValidationError(_("Phiếu nhập và đề xuất mua phải cùng công ty, nguồn Mua mới."))

    @api.depends("category_id")
    def _compute_asset_class(self):
        for line in self:
            line.asset_class = line.category_id.tp_asset_class or line.asset_class or "device"

    @api.depends("receipt_id.source")
    def _compute_ownership(self):
        for line in self:
            if not line.ownership or line.ownership in ("company", "rented"):
                line.ownership = "rented" if line.receipt_id.source == "rental" else "company"

    @api.constrains("warranty_months", "warranty_meter_limit", "purchase_value")
    def _check_positive(self):
        for line in self:
            if line.warranty_months < 0 or line.warranty_meter_limit < 0 or (line.purchase_value or 0) < 0:
                raise ValidationError(_("Giá trị, thời hạn và số đếm bảo hành không được âm."))

    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        if self.env.context.get("tp_equipment_receipt_internal") is not INTERNAL:
            for vals in vals_list:
                vals.pop("equipment_id", None)
        receipts = self.env["tp.equipment.receipt"].browse({v.get("receipt_id") for v in vals_list if v.get("receipt_id")})
        lock_records(receipts)
        if receipts.filtered(lambda r: r.state != "draft"):
            raise UserError(_("Chỉ thêm thiết bị vào phiếu nhập nháp."))
        lines = super().create(vals_list)
        lines._tp_check_proposal_capacity()
        return lines

    def write(self, vals):
        check_admin(self.env)
        lock_records(self.receipt_id)
        if self.env.context.get("tp_equipment_receipt_internal") is not INTERNAL and "receipt_id" in vals:
            raise UserError(_('Không chuyển dòng sang phiếu khác.'))
        if self.env.context.get("tp_equipment_receipt_internal") is not INTERNAL and\
                self.filtered(lambda line: line.receipt_id.state != "draft"):
            raise UserError(_("Chỉ sửa dòng của phiếu nhập nháp."))
        if "equipment_id" in vals and self.env.context.get("tp_equipment_receipt_internal") is not INTERNAL:
            raise UserError(_("Thiết bị được tạo khi xác nhận nhập kho."))
        result = super().write(vals)
        if {"proposal_line_id", "receipt_id"} & set(vals):
            self._tp_check_proposal_capacity()
        return result

    @api.ondelete(at_uninstall=False)
    def _unlink_only_draft(self):
        lock_records(self.receipt_id)
        if self.filtered(lambda line: line.receipt_id.state != "draft"):
            raise UserError(_("Chỉ bỏ dòng khỏi phiếu nhập nháp."))

    def _tp_equipment_vals(self, index):
        self.ensure_one()
        receipt = self.receipt_id
        basis = self.warranty_basis
        notes = [part for part in (self.config_note, self.accessories and _("Phụ kiện: %s", self.accessories)) if part]
        return {
            "name": self.name.strip(),
            "category_id": self.category_id.id,
            "tp_asset_class": self.asset_class,
            "tp_brand": self.brand,
            "model": self.model,
            "serial_no": self.serial_no,
            "tp_cpu": self.cpu,
            "tp_ram": self.ram,
            "tp_storage": self.storage,
            "tp_config_note": "\n".join(notes) or False,
            "tp_ownership": self.ownership,
            "tp_owner_partner_id": self.owner_partner_id.id,
            "tp_supplier_id": receipt.supplier_id.id,
            "tp_purchase_date": receipt.date,
            "tp_purchase_value": self.purchase_value or False,
            "tp_purchase_value_known": self.purchase_value_known,
            "tp_warranty_basis": basis,
            "tp_warranty_start": (self.warranty_start or receipt.date) if basis in ("duration", "date_or_meter") else False,
            "tp_warranty_months": self.warranty_months if basis in ("duration", "date_or_meter") else 0,
            "warranty_date": self.warranty_date if basis in ("date", "date_or_meter") else False,
            "tp_warranty_meter_limit": self.warranty_meter_limit if basis in ("meter", "date_or_meter") else 0,
            "tp_technical_state": self.technical_state,
            "tp_condition_note": self.note or False,
            "tp_verification": "verified",
            "tp_verified_date": receipt.date,
            "tp_custody": "stock",
            "tp_location_id": receipt.location_id.id,
            "tp_source_ref": _("%(receipt)s · dòng %(index)s", receipt=receipt.name, index=index),
            "tp_replaces_id": self.proposal_line_id.equipment_id.id,
        }
