"""Kiểm kê thiết bị (EQUIP-001 part 3).

* Starting a count freezes a snapshot of the scope (expected holder, place, state, data version).
* Counting marks lines found / missing, records the actual holder / place / state / meter, or adds
  extra devices found outside the snapshot (scan or manual).
* Closing only freezes the results: it never writes custody or state of equipment, so moves done
  after the snapshot are not overwritten.
* Corrections go through the adjust wizard (preview + reason + version check) which creates a system
  "Điều chỉnh sau kiểm kê" move. Missing devices are only suggested for "Báo mất"; unknown extra
  devices are suggested for a receipt "Phát hiện khi kiểm kê".
"""
from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .common import CUSTODY, INTERNAL, TECH_STATE, check_admin, lock_records

INVENTORY_STATES = [
    ("draft", "Nháp"),
    ("counting", "Đang kiểm kê"),
    ("closed", "Đã chốt"),
    ("cancel", "Đã hủy"),
]
SCOPES = [
    ("all", "Toàn bộ thiết bị đang quản lý"),
    ("location", "Theo vị trí / kho"),
    ("department", "Theo phòng ban đang dùng"),
    ("category", "Theo phân loại"),
]
COUNT_STATES = [
    ("pending", "Chưa đếm"),
    ("found", "Có mặt"),
    ("missing", "Không thấy"),
]
RESULTS = [
    ("not_counted", "Chưa đếm"),
    ("ok", "Khớp sổ"),
    ("wrong_place", "Sai nơi giữ / vị trí"),
    ("state_diff", "Khác tình trạng"),
    ("missing", "Thiếu"),
    ("extra", "Thừa / ngoài phạm vi"),
]
COUNT_CUSTODY = [item for item in CUSTODY if item[0] not in ("none",)]
ACTUAL_STATE = [item for item in TECH_STATE if item[0] != "unverified"]


class TpEquipmentInventory(models.Model):
    _name = "tp.equipment.inventory"
    _description = "Kỳ kiểm kê thiết bị"
    _inherit = ["tp.equipment.secure.mixin"]
    _order = "date desc, id desc"

    name = fields.Char("Số kiểm kê", readonly=True, copy=False, default="/", index=True)
    title = fields.Char("Tên kỳ kiểm kê", required=True, tracking=True)
    date = fields.Date("Ngày kiểm kê", required=True, default=fields.Date.context_today, tracking=True)
    company_id = fields.Many2one("res.company", "Công ty", default=lambda self: self.env.company, required=True)
    responsible_id = fields.Many2one("res.users", "Người ghi trên hệ thống", default=lambda self: self.env.uid,
                                     readonly=True)
    team_text = fields.Char("Người kiểm kê (thực tế)", help="Thông tin nghiệp vụ; không cấp quyền Kho thiết bị.")
    scope = fields.Selection(SCOPES, "Phạm vi", required=True, default="all", tracking=True)
    location_ids = fields.Many2many("tp.equipment.location", string="Vị trí / kho")
    department_ids = fields.Many2many("hr.department", string="Phòng ban")
    category_ids = fields.Many2many("maintenance.equipment.category", string="Phân loại")
    include_components = fields.Boolean("Gồm linh kiện / phụ kiện quản lý riêng", default=True)
    state = fields.Selection(INVENTORY_STATES, "Trạng thái", default="draft", required=True, readonly=True,
                             copy=False, tracking=True, index=True)
    snapshot_date = fields.Datetime("Chụp sổ lúc", readonly=True, copy=False)
    closed_date = fields.Datetime("Chốt lúc", readonly=True, copy=False)
    closed_by_id = fields.Many2one("res.users", "Người chốt", readonly=True, copy=False)
    cancel_reason = fields.Text("Lý do hủy", readonly=True, copy=False)
    note = fields.Text("Ghi chú")
    line_ids = fields.One2many("tp.equipment.inventory.line", "inventory_id", "Dòng kiểm kê", copy=False)
    move_ids = fields.One2many("tp.equipment.move", "inventory_id", "Phiếu điều chỉnh", readonly=True)
    scan_input = fields.Char("Quét / nhập mã", compute="_compute_scan_input", readonly=False, store=False,
                             help="Quét QR, nhập mã thiết bị hoặc serial: dòng tương ứng được đánh dấu có mặt.")

    expected_count = fields.Integer("Theo sổ", compute="_compute_counts")
    found_count = fields.Integer("Có mặt", compute="_compute_counts")
    pending_count = fields.Integer("Chưa đếm", compute="_compute_counts")
    missing_count = fields.Integer("Thiếu", compute="_compute_counts")
    extra_count = fields.Integer("Thừa", compute="_compute_counts")
    wrong_place_count = fields.Integer("Sai nơi giữ", compute="_compute_counts")
    state_diff_count = fields.Integer("Khác tình trạng", compute="_compute_counts")
    changed_after_count = fields.Integer("Đổi sau khi chụp sổ", compute="_compute_counts")
    adjust_count = fields.Integer("Phiếu điều chỉnh", compute="_compute_counts")

    @api.depends("line_ids.result", "line_ids.is_extra", "line_ids.count_state", "move_ids")
    def _compute_counts(self):
        for inventory in self:
            lines = inventory.line_ids
            expected = lines.filtered(lambda row: not row.is_extra)
            inventory.expected_count = len(expected)
            inventory.found_count = len(lines.filtered(lambda row: row.count_state == "found"))
            inventory.pending_count = len(expected.filtered(lambda row: row.count_state == "pending"))
            inventory.missing_count = len(lines.filtered(lambda row: row.result == "missing"))
            inventory.extra_count = len(lines.filtered(lambda row: row.is_extra))
            inventory.wrong_place_count = len(lines.filtered(lambda row: row.result == "wrong_place"))
            inventory.state_diff_count = len(lines.filtered(lambda row: row.result == "state_diff"))
            inventory.changed_after_count = len(lines.filtered("changed_after")) if inventory.id else 0
            inventory.adjust_count = len(inventory.move_ids)

    # ------------------------------------------------------------------ ORM
    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        for vals in vals_list:
            vals.update(state="draft", responsible_id=self.env.uid, snapshot_date=False,
                        closed_date=False, closed_by_id=False, cancel_reason=False)
            vals.pop("line_ids", None)
            vals.pop("move_ids", None)
            vals["name"] = self.env["ir.sequence"].sudo().next_by_code("tp.equipment.inventory") or "/"
        records = super().create(vals_list)
        records._tp_check_scope_company()
        return records

    @api.constrains("company_id", "location_ids", "department_ids", "category_ids")
    def _tp_check_scope_company(self):
        for inventory in self:
            for record in inventory.location_ids:
                if record.company_id != inventory.company_id:
                    raise ValidationError(_("Vị trí kiểm kê phải cùng công ty."))
            for record in inventory.department_ids:
                if record.company_id and record.company_id != inventory.company_id:
                    raise ValidationError(_("Phòng ban kiểm kê phải cùng công ty."))
            for record in inventory.category_ids:
                if record.company_id and record.company_id != inventory.company_id:
                    raise ValidationError(_("Phân loại kiểm kê phải cùng công ty."))

    def write(self, vals):
        check_admin(self.env)
        lock_records(self)
        if self.env.context.get("tp_inventory_internal") is not INTERNAL:
            if {"name", "responsible_id", "move_ids", "state", "snapshot_date", "closed_date", "closed_by_id", "cancel_reason"} & set(vals):
                raise UserError(_("Dùng các nút Bắt đầu / Chốt / Hủy trên kỳ kiểm kê."))
            scope_keys = {"company_id", "scope", "location_ids", "department_ids", "category_ids", "include_components", "date"}
            for inventory in self:
                if inventory.state != "draft" and scope_keys & set(vals):
                    raise UserError(_("Đã chụp sổ: không đổi phạm vi / ngày kiểm kê. Hủy và lập kỳ mới nếu cần."))
                if inventory.state in ("closed", "cancel") and set(vals) - {"note", "message_main_attachment_id"}:
                    raise UserError(_("Kỳ kiểm kê đã chốt / hủy: chỉ thêm ghi chú."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_draft(self):
        check_admin(self.env)
        lock_records(self)
        if self.filtered(lambda i: i.state != "draft"):
            raise UserError(_("Chỉ xóa được kỳ kiểm kê nháp; kỳ khác dùng Hủy."))

    # ------------------------------------------------------------------ scope
    def _tp_scope_domain(self):
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id), ("tp_lifecycle", "=", "active"), ("tp_asset_class", "!=", "service")]
        if not self.include_components:
            domain.append(("tp_asset_class", "=", "device"))
        if self.scope == "location":
            if not self.location_ids:
                raise UserError(_("Chọn vị trí / kho cần kiểm kê."))
            domain.append(("tp_location_id", "in", self.location_ids.ids))
        elif self.scope == "department":
            if not self.department_ids:
                raise UserError(_("Chọn phòng ban cần kiểm kê."))
            domain.append(("tp_current_department_id", "in", self.department_ids.ids))
        elif self.scope == "category":
            if not self.category_ids:
                raise UserError(_("Chọn phân loại cần kiểm kê."))
            domain.append(("category_id", "in", self.category_ids.ids))
        return domain

    @api.model
    def _tp_expected_vals(self, equipment):
        return {
            "equipment_id": equipment.id,
            "expected_custody": equipment.tp_custody,
            "expected_employee_id": equipment.tp_employee_id.id,
            "expected_department_id": equipment.tp_holder_department_id.id,
            "expected_location_id": equipment.tp_location_id.id,
            "expected_partner_id": equipment.tp_vendor_id.id,
            "expected_state": equipment.tp_technical_state,
            "snapshot_version": equipment.tp_version,
        }

    # ------------------------------------------------------------------ actions
    def action_start(self):
        check_admin(self.env)
        lock_records(self)
        for inventory in self:
            if inventory.state != "draft":
                continue
            equipments = self.env["maintenance.equipment"].search(inventory._tp_scope_domain(), order="tp_code")
            if not equipments:
                raise UserError(_("Phạm vi đã chọn không có thiết bị đang quản lý."))
            self.env["tp.equipment.move"]._tp_lock_equipment(equipments)
            self.env["tp.equipment.inventory.line"].with_context(tp_inventory_internal=INTERNAL).create([
                dict(self._tp_expected_vals(equipment), inventory_id=inventory.id) for equipment in equipments
            ])
            inventory.with_context(tp_inventory_internal=INTERNAL).write({
                "state": "counting", "snapshot_date": fields.Datetime.now()})
            inventory.message_post(body=_("Bắt đầu kiểm kê: chụp sổ %s thiết bị.", len(equipments)),
                                   subtype_xmlid="mail.mt_note")
        return True

    def _compute_scan_input(self):
        for inventory in self:
            inventory.scan_input = False

    @api.onchange("scan_input")
    def _onchange_scan_input(self):
        value = (self.scan_input or "").strip()
        if not value:
            return None
        self.scan_input = False
        if self.state != "counting":
            return {"warning": {"title": _("Chưa bắt đầu kiểm kê"), "message": _("Bấm “Bắt đầu kiểm kê” trước khi quét.")}}
        found = self.env["maintenance.equipment"].tp_scan_lookup(value)
        if found.get("error"):
            return {"warning": {"title": _("Không nhận được mã"), "message": found["error"]}}
        equipment = self.env["maintenance.equipment"].browse(found["id"])
        line = self.line_ids.filtered(lambda row: row.equipment_id.id == equipment.id)[:1]
        if line:
            if line.count_state != "found":
                line.count_state = "found"
                line._tp_fill_actual()
            return None
        if equipment.tp_lifecycle != "active":
            return {"warning": {"title": _("Thiết bị không còn quản lý"),
                                "message": _("%s đang ở trạng thái %s; ghi chú ở kỳ kiểm kê nếu thấy thực tế.",
                                             equipment.display_name,
                                             dict(equipment._fields["tp_lifecycle"].selection)[equipment.tp_lifecycle])}}
        vals = dict(self._tp_expected_vals(equipment), is_extra=True, count_state="found")
        new_line = self.line_ids.new(vals)
        new_line._tp_fill_actual()
        self.line_ids |= new_line
        return {"warning": {"title": _("Thiết bị ngoài phạm vi chụp sổ"),
                            "message": _("Đã thêm %s vào danh sách “thừa / ngoài phạm vi”. Ghi nơi thấy thực tế.",
                                         equipment.display_name)}}

    def action_mark_pending_missing(self):
        check_admin(self.env)
        lock_records(self)
        for inventory in self.filtered(lambda i: i.state == "counting"):
            pending = inventory.line_ids.filtered(lambda row: row.count_state == "pending" and not row.is_extra)
            pending.write({"count_state": "missing"})
        return True

    def action_close(self):
        check_admin(self.env)
        lock_records(self)
        for inventory in self:
            if inventory.state != "counting":
                continue
            meter_lines = inventory.line_ids.filtered(
                lambda row: row.count_state == "found" and row.actual_meter and row.equipment_id)
            self.env["tp.equipment.move"]._tp_lock_equipment(meter_lines.equipment_id)
            for line in meter_lines:
                if line.equipment_id.tp_version != line.snapshot_version:
                    raise UserError(_("Thiết bị đã thay đổi sau chụp sổ: bỏ chỉ số đếm cũ và xác minh lại."))
                self.env["tp.equipment.meter"].create({
                    "equipment_id": line.equipment_id.id, "date": inventory.date, "value": line.actual_meter,
                    "source": "inventory", "note": inventory.name,
                })
            inventory.with_context(tp_inventory_internal=INTERNAL).write({
                "state": "closed", "closed_date": fields.Datetime.now(), "closed_by_id": self.env.uid})
            inventory.message_post(body=_(
                "Chốt kiểm kê: %(found)s có mặt, %(missing)s thiếu, %(pending)s chưa đếm, %(extra)s thừa, "
                "%(wrong)s sai nơi giữ, %(diff)s khác tình trạng. Hồ sơ thiết bị chưa bị thay đổi; dùng Điều chỉnh "
                "cho từng chênh lệch đã xác minh.",
                found=inventory.found_count, missing=inventory.missing_count, pending=inventory.pending_count,
                extra=inventory.extra_count, wrong=inventory.wrong_place_count, diff=inventory.state_diff_count),
                subtype_xmlid="mail.mt_note")
        return True

    def action_open_cancel(self):
        self.ensure_one()
        if self.state in ("closed", "cancel"):
            raise UserError(_("Kỳ kiểm kê đã chốt / hủy."))
        return self.env["tp.equipment.reason.wizard"]._tp_open(self, "cancel", _("Hủy kỳ kiểm kê"))

    def _tp_apply_reason(self, action, reason):
        check_admin(self.env)
        self.ensure_one()
        lock_records(self)
        if not (reason or "").strip():
            raise UserError(_("Ghi lý do hủy."))
        if action != "cancel" or self.state in ("closed", "cancel"):
            raise UserError(_("Thao tác không hợp lệ."))
        self.with_context(tp_inventory_internal=INTERNAL).write({"state": "cancel", "cancel_reason": reason})
        self.message_post(body=_("Hủy kỳ kiểm kê: %s", reason), subtype_xmlid="mail.mt_note")
        return True

    def action_open_adjust(self):
        check_admin(self.env)
        self.ensure_one()
        if self.state != "closed":
            raise UserError(_("Chốt kiểm kê trước khi điều chỉnh hồ sơ."))
        lines = self.line_ids.filtered("can_adjust")
        if not lines:
            raise UserError(_("Không còn chênh lệch nơi giữ / tình trạng cần điều chỉnh."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Điều chỉnh sau kiểm kê"),
            "res_model": "tp.equipment.inventory.adjust",
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.inventory_adjust_form").id, "form")],
            "target": "new",
            "context": {"default_inventory_id": self.id, "default_line_ids": [(6, 0, lines.ids)]},
        }

    def action_open_moves(self):
        check_admin(self.env)
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("tp_equipment.action_moves")
        action.update({
            "name": _("Phiếu điều chỉnh của %s", self.name),
            "view_mode": "list,form",
            "views": [(self.env.ref("tp_equipment.move_list").id, "list"),
                      (self.env.ref("tp_equipment.move_form").id, "form")],
            "domain": [("inventory_id", "=", self.id)],
            "context": {"tp_filter_profile": "move", "tp_eq_leaf": "tp_equipment.menu_inventories"},
        })
        return action

    def action_open_lines(self):
        check_admin(self.env)
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("tp_equipment.action_inventory_lines")
        action.update({
            "name": _("Dòng kiểm kê %s", self.name),
            "view_mode": "list",
            "views": [(self.env.ref("tp_equipment.inventory_line_list").id, "list")],
            "search_view_id": self.env.ref("tp_equipment.inventory_line_search").id,
            "domain": [("inventory_id", "=", self.id)],
            "context": {"tp_filter_profile": "inventory_line", "tp_eq_leaf": "tp_equipment.menu_inventories",
                        "default_inventory_id": self.id},
        })
        return action


class TpEquipmentInventoryLine(models.Model):
    _name = "tp.equipment.inventory.line"
    _description = "Dòng kiểm kê thiết bị"
    _order = "inventory_id, is_extra, equipment_code, id"

    inventory_id = fields.Many2one("tp.equipment.inventory", "Kỳ kiểm kê", required=True, ondelete="cascade",
                                   index=True)
    inventory_state = fields.Selection(related="inventory_id.state", string="Trạng thái kỳ")
    equipment_id = fields.Many2one("maintenance.equipment", "Thiết bị", ondelete="restrict", index="btree_not_null",
                                   context={"active_test": False})
    equipment_code = fields.Char(related="equipment_id.tp_code", store=True, string="Mã")
    category_id = fields.Many2one(related="equipment_id.category_id", string="Phân loại")
    is_extra = fields.Boolean("Thừa / ngoài phạm vi", readonly=True)
    extra_description = fields.Char("Mô tả thiết bị thừa",
                                    help="Thiết bị thấy thực tế nhưng chưa có hồ sơ: ghi tên / serial để lập phiếu nhập.")
    extra_serial = fields.Char("Serial thấy thực tế")

    expected_custody = fields.Selection(CUSTODY, "Nơi giữ theo sổ", readonly=True)
    expected_employee_id = fields.Many2one("hr.employee", "Người giữ theo sổ", readonly=True, ondelete="restrict",
                                           context={"active_test": False})
    expected_employee_name = fields.Char("Snapshot người giữ theo sổ", readonly=True, copy=False)
    expected_department_id = fields.Many2one("hr.department", "Phòng ban theo sổ", readonly=True, ondelete="restrict")
    expected_location_id = fields.Many2one("tp.equipment.location", "Vị trí theo sổ", readonly=True,
                                           ondelete="restrict")
    expected_partner_id = fields.Many2one("res.partner", "Đơn vị ngoài theo sổ", readonly=True, ondelete="restrict")
    expected_state = fields.Selection(TECH_STATE, "Tình trạng theo sổ", readonly=True)
    expected_text = fields.Char("Theo sổ", compute="_compute_texts")
    snapshot_version = fields.Integer("Phiên bản lúc chụp sổ", readonly=True)

    count_state = fields.Selection(COUNT_STATES, "Kiểm đếm", default="pending", required=True)
    actual_custody = fields.Selection(COUNT_CUSTODY, "Nơi giữ thực tế")
    actual_employee_id = fields.Many2one("hr.employee", "Người giữ thực tế", ondelete="restrict")
    actual_employee_name = fields.Char("Snapshot người giữ thực tế", readonly=True, copy=False)
    actual_department_id = fields.Many2one("hr.department", "Phòng ban thực tế", ondelete="restrict")
    actual_location_id = fields.Many2one("tp.equipment.location", "Vị trí thực tế", ondelete="restrict")
    actual_state = fields.Selection(ACTUAL_STATE, "Tình trạng thực tế")
    actual_meter = fields.Integer("Chỉ số đếm")
    actual_text = fields.Char("Thực tế", compute="_compute_texts")
    note = fields.Char("Ghi chú")
    counted_date = fields.Datetime("Đếm lúc", readonly=True)
    counted_by_id = fields.Many2one("res.users", "Người ghi", readonly=True)

    result = fields.Selection(RESULTS, "Kết quả", compute="_compute_result", store=True, index=True)
    changed_after = fields.Boolean("Đổi sau khi chụp sổ", compute="_compute_changed_after",
                                   help="Hồ sơ thiết bị đã có phiếu / thay đổi sau thời điểm chụp sổ.")
    adjust_move_id = fields.Many2one("tp.equipment.move", "Phiếu điều chỉnh", readonly=True, ondelete="restrict")
    can_adjust = fields.Boolean("Cần điều chỉnh", compute="_compute_can_adjust")

    @api.depends("count_state", "is_extra", "actual_custody", "actual_employee_id", "actual_department_id",
                 "actual_location_id", "actual_state", "expected_custody", "expected_employee_id",
                 "expected_department_id", "expected_location_id", "expected_state")
    def _compute_result(self):
        for line in self:
            if line.is_extra:
                line.result = "extra"
            elif line.count_state == "pending":
                line.result = "not_counted"
            elif line.count_state == "missing":
                line.result = "missing"
            elif line._tp_place_differs():
                line.result = "wrong_place"
            elif line.actual_state and line.actual_state != line.expected_state:
                line.result = "state_diff"
            else:
                line.result = "ok"

    def _tp_place_differs(self):
        self.ensure_one()
        if not self.actual_custody:
            return False
        return (self.actual_custody != self.expected_custody
                or self.actual_employee_id != self.expected_employee_id
                or self.actual_department_id != self.expected_department_id
                or (self.actual_location_id != self.expected_location_id))

    def _compute_changed_after(self):
        for line in self:
            line.changed_after = bool(line.equipment_id and line.snapshot_version
                                      and line.equipment_id.tp_version != line.snapshot_version)

    def _compute_can_adjust(self):
        for line in self:
            line.can_adjust = bool(
                line.inventory_id.state == "closed" and line.equipment_id and not line.adjust_move_id
                and line.count_state == "found"
                and (line.result in ("wrong_place", "state_diff") or (line.is_extra and line.actual_custody)))

    @api.depends("expected_custody", "expected_employee_id", "expected_department_id", "expected_location_id",
                 "actual_custody", "actual_employee_id", "actual_department_id", "actual_location_id",
                 "count_state", "is_extra", "extra_description")
    def _compute_texts(self):
        custody = dict(CUSTODY)
        for line in self:
            def holder(c, emp, dep, loc, partner=None):
                if not c:
                    return ""
                parts = [custody.get(c, c)]
                for record in (emp, dep, partner):
                    if record:
                        parts.append(record.display_name)
                if loc:
                    parts.append(loc.display_name)
                return " · ".join(parts)
            line.expected_text = holder(line.expected_custody, line.expected_employee_id, line.expected_department_id,
                                        line.expected_location_id, line.expected_partner_id) \
                if not line.is_extra else _("Ngoài phạm vi chụp sổ")
            if line.count_state == "missing":
                line.actual_text = _("Không thấy")
            elif line.count_state == "pending":
                line.actual_text = ""
            else:
                line.actual_text = holder(line.actual_custody, line.actual_employee_id, line.actual_department_id,
                                          line.actual_location_id) or _("Có mặt")

    def _tp_fill_actual(self):
        for line in self:
            if not line.actual_custody:
                line.actual_custody = line.expected_custody if line.expected_custody in dict(COUNT_CUSTODY) else False
                line.actual_employee_id = line.expected_employee_id
                line.actual_department_id = line.expected_department_id
                line.actual_location_id = line.expected_location_id
            if not line.actual_state and line.expected_state in dict(ACTUAL_STATE):
                line.actual_state = line.expected_state

    @api.onchange("count_state")
    def _onchange_count_state(self):
        if self.count_state == "found":
            self._tp_fill_actual()

    @api.onchange("actual_custody")
    def _onchange_actual_custody(self):
        if self.actual_custody not in ("employee", "loan"):
            self.actual_employee_id = False
        if self.actual_custody != "department":
            self.actual_department_id = False

    _equipment_once = models.UniqueIndex(
        "(inventory_id, equipment_id) WHERE equipment_id IS NOT NULL",
        "Thiết bị chỉ có một dòng trong cùng kỳ kiểm kê.")

    @api.constrains("inventory_id", "equipment_id", "actual_employee_id", "actual_department_id", "actual_location_id")
    def _check_actual_company(self):
        for line in self:
            company = line.inventory_id.company_id
            for record in (line.equipment_id, line.actual_employee_id, line.actual_department_id, line.actual_location_id):
                if record and record.company_id and record.company_id != company:
                    raise ValidationError(_("Thiết bị, người giữ, phòng ban và vị trí phải thuộc công ty kiểm kê."))

    @api.constrains("actual_meter")
    def _check_meter(self):
        for line in self:
            if line.actual_meter < 0:
                raise ValidationError(_("Chỉ số đếm không được âm."))

    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        if self.env.context.get("tp_inventory_internal") is not INTERNAL:
            for vals in vals_list:
                vals["inventory_id"] = vals.get("inventory_id") or self.env.context.get("default_inventory_id")
                if not vals["inventory_id"]:
                    raise UserError(_("Chọn kỳ kiểm kê đang mở."))
            inventories = self.env["tp.equipment.inventory"].browse(
                {v.get("inventory_id") for v in vals_list if v.get("inventory_id")})
            lock_records(inventories)
            if inventories.filtered(lambda i: i.state != "counting"):
                raise UserError(_("Chỉ thêm dòng khi đang kiểm kê."))
            Equipment = self.env["maintenance.equipment"]
            for vals in vals_list:
                # Manual rows are always "extra": the snapshot is the only source of expected rows.
                inventory = self.env["tp.equipment.inventory"].browse(vals.get("inventory_id"))
                equipment = Equipment.browse(vals.get("equipment_id") or [])
                if equipment and equipment in inventory.line_ids.equipment_id:
                    raise UserError(_("%s đã có trong danh sách kiểm kê.", equipment.display_name))
                if not inventory.exists():
                    raise UserError(_("Chọn kỳ kiểm kê đang mở."))
                if equipment:
                    self.env["tp.equipment.move"]._tp_lock_equipment(equipment)
                vals.update(adjust_move_id=False, counted_date=False, counted_by_id=False)
                expected = self.env["tp.equipment.inventory"]._tp_expected_vals(equipment) if equipment else {}
                for key in ("expected_custody", "expected_employee_id", "expected_department_id",
                            "expected_location_id", "expected_partner_id", "expected_state", "snapshot_version"):
                    vals[key] = expected.get(key, False)
                vals["is_extra"] = True
                vals.setdefault("count_state", "found")
                if not equipment and not (vals.get("extra_description") or "").strip():
                    raise UserError(_("Thiết bị thừa chưa có hồ sơ: ghi mô tả để lập phiếu nhập sau."))
        lines = super().create(vals_list)
        lines.filtered(lambda row: row.count_state != "pending")._tp_stamp()
        return lines

    def write(self, vals):
        check_admin(self.env)
        if self.env.context.get("tp_inventory_internal") is not INTERNAL:
            lock_records(self.inventory_id)
            protected = {"inventory_id", "equipment_id", "is_extra", "snapshot_version", "adjust_move_id",
                         "counted_date", "counted_by_id"} | {k for k in vals if k.startswith("expected_")}
            if protected & set(vals):
                raise UserError(_("Dữ liệu chụp sổ không sửa được."))
            if self.filtered(lambda row: row.inventory_id.state != "counting") and set(vals) - {"note"}:
                raise UserError(_("Chỉ ghi kết quả khi kỳ kiểm kê đang mở."))
        result = super().write(vals)
        if self.env.context.get("tp_inventory_internal") is not INTERNAL and \
                {"count_state", "actual_custody", "actual_employee_id", "actual_department_id",
                 "actual_location_id", "actual_state", "actual_meter"} & set(vals):
            self._tp_stamp()
        return result

    def _tp_stamp(self):
        self.with_context(tp_inventory_internal=INTERNAL).write({
            "counted_date": fields.Datetime.now(), "counted_by_id": self.env.uid})

    @api.ondelete(at_uninstall=False)
    def _unlink_only_extra(self):
        check_admin(self.env)
        lock_records(self.inventory_id)
        if self.env.context.get("tp_inventory_internal") is INTERNAL:
            return
        for line in self:
            if line.inventory_id.state not in ("draft", "counting") or not line.is_extra:
                raise UserError(_("Chỉ bỏ được dòng thừa thêm tay khi đang kiểm kê."))

    def action_mark_found(self):
        check_admin(self.env)
        lock_records(self.inventory_id)
        for line in self.filtered(lambda row: row.inventory_id.state == "counting"):
            vals = {"count_state": "found"}
            if not line.actual_custody and line.expected_custody in dict(COUNT_CUSTODY):
                vals.update({
                    "actual_custody": line.expected_custody,
                    "actual_employee_id": line.expected_employee_id.id,
                    "actual_department_id": line.expected_department_id.id,
                    "actual_location_id": line.expected_location_id.id,
                })
            if not line.actual_state and line.expected_state in dict(ACTUAL_STATE):
                vals["actual_state"] = line.expected_state
            line.write(vals)
        return True

    def action_mark_missing(self):
        check_admin(self.env)
        lock_records(self.inventory_id)
        self.filtered(lambda row: row.inventory_id.state == "counting" and not row.is_extra).write({"count_state": "missing"})
        return True

    def action_suggest_lost(self):
        """Open (not save) a "Báo mất" move for a missing device after verification."""
        check_admin(self.env)
        self.ensure_one()
        if self.result != "missing" or self.inventory_id.state != "closed":
            raise UserError(_("Chỉ đề xuất báo mất cho thiết bị thiếu của kỳ đã chốt."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Báo mất (theo kiểm kê)"),
            "res_model": "tp.equipment.move",
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.move_form").id, "form")],
            "target": "current",
            "context": {
                "default_move_type": "lost",
                "default_line_ids": [(0, 0, {"equipment_id": self.equipment_id.id})],
                "default_reason": _("Không thấy khi kiểm kê %(name)s (%(date)s). Đã xác minh lại trước khi báo mất.",
                                    name=self.inventory_id.name, date=self.inventory_id.date.strftime("%d/%m/%Y")),
                "tp_eq_leaf": "tp_equipment.menu_inventories",
            },
        }

    def action_suggest_receipt(self):
        """Open (not save) a receipt "Phát hiện khi kiểm kê" for an extra device without a record."""
        check_admin(self.env)
        self.ensure_one()
        if not self.is_extra or self.equipment_id:
            raise UserError(_("Chỉ lập phiếu nhập cho thiết bị thừa chưa có hồ sơ."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Phiếu nhập (phát hiện khi kiểm kê)"),
            "res_model": "tp.equipment.receipt",
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.receipt_form").id, "form")],
            "target": "current",
            "context": {
                "default_source": "found",
                "default_location_id": self.actual_location_id.id,
                "default_note": _("Phát hiện khi kiểm kê %s", self.inventory_id.name),
                "default_line_ids": [(0, 0, {"name": self.extra_description, "serial_no": self.extra_serial or False,
                                             "note": self.note or False})],
                "tp_eq_leaf": "tp_equipment.menu_receipts",
            },
        }


class TpEquipmentInventoryAdjust(models.TransientModel):
    _name = "tp.equipment.inventory.adjust"
    _description = "Điều chỉnh hồ sơ sau kiểm kê"

    inventory_id = fields.Many2one("tp.equipment.inventory", "Kỳ kiểm kê", required=True, readonly=True)
    line_ids = fields.Many2many("tp.equipment.inventory.line", string="Chênh lệch điều chỉnh",
                                domain="[('inventory_id', '=', inventory_id)]")
    reason = fields.Text("Lý do điều chỉnh", required=True,
                         help="Ví dụ: đã xác minh lại với người giữ, chuyển chỗ không lập phiếu…")
    preview_html = fields.Html("Xem trước", compute="_compute_preview", sanitize=False)

    @api.depends("line_ids")
    def _compute_preview(self):
        custody = dict(CUSTODY)
        state = dict(TECH_STATE)
        for wizard in self:
            rows = []
            for line in wizard.line_ids:
                issue = ""
                if line.changed_after:
                    issue = _("Hồ sơ đã đổi sau khi chụp sổ — sẽ bị chặn, kiểm tra phiếu mới hơn.")
                elif line.actual_custody in ("employee", "loan") and not line.actual_employee_id:
                    issue = _("Thiếu người giữ thực tế.")
                elif line.actual_custody == "department" and not line.actual_department_id:
                    issue = _("Thiếu phòng ban thực tế.")
                elif line.actual_custody == "vendor":
                    issue = _("Thiết bị ở bên ngoài: dùng phiếu gửi sửa chữa, không điều chỉnh.")
                after = " · ".join(filter(None, [
                    custody.get(line.actual_custody, ""), line.actual_employee_id.display_name or "",
                    line.actual_department_id.display_name or "", line.actual_location_id.display_name or "",
                    state.get(line.actual_state, "") if line.actual_state else ""]))
                before = " · ".join(filter(None, [line.expected_text, state.get(line.expected_state, "")]))
                rows.append(Markup("<tr class='%s'><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>") % (
                    "table-danger" if issue else "", line.equipment_id.display_name or "", before, after, issue))
            wizard.preview_html = Markup(
                "<table class='table table-sm o_tp_eq_preview_table'><thead><tr><th>Thiết bị</th><th>Theo sổ</th>"
                "<th>Sau điều chỉnh</th><th>Lưu ý</th></tr></thead><tbody>%s</tbody></table>",
            ) % Markup("").join(rows) if rows else Markup("<p>%s</p>") % escape(_("Chọn dòng cần điều chỉnh."))

    def action_confirm(self):
        check_admin(self.env)
        self.ensure_one()
        reason = (self.reason or "").strip()
        if not reason:
            raise UserError(_("Ghi lý do điều chỉnh."))
        inventory = self.inventory_id
        lock_records(inventory)
        if inventory.state != "closed":
            raise UserError(_("Chỉ điều chỉnh kỳ kiểm kê đã chốt."))
        lines = self.line_ids
        if any(line.inventory_id != inventory for line in lines):
            raise UserError(_("Dòng điều chỉnh không thuộc kỳ kiểm kê đã chọn."))
        lock_records(lines)
        if lines.filtered(lambda line: not line.can_adjust):
            raise UserError(_("Có dòng không còn đủ điều kiện điều chỉnh. Mở lại bản xem trước."))
        lines._check_actual_company()
        if not lines:
            raise UserError(_("Không còn dòng cần điều chỉnh (đã điều chỉnh hoặc không có chênh lệch)."))
        Move = self.env["tp.equipment.move"]
        Move._tp_lock_equipment(lines.equipment_id)
        for line in lines:
            equipment = line.equipment_id
            if equipment.tp_version != line.snapshot_version:
                raise UserError(_("%(name)s đã thay đổi sau khi chụp sổ kiểm kê. Kiểm tra phiếu mới hơn; không điều "
                                  "chỉnh đè.", name=equipment.display_name))
            if equipment.tp_lifecycle != "active" or equipment.tp_pending_move_id:
                raise UserError(_("%(name)s đang có phiếu chờ hoặc không còn quản lý.", name=equipment.display_name))
            if not line.actual_custody:
                raise UserError(_("Ghi nơi giữ thực tế trước khi điều chỉnh."))
            if line.actual_custody == "vendor":
                raise UserError(_("%(name)s: thiết bị ở bên ngoài dùng phiếu gửi sửa chữa.", name=equipment.display_name))
            if line.actual_custody in ("employee", "loan") and not line.actual_employee_id:
                raise UserError(_("%(name)s: ghi người giữ thực tế.", name=equipment.display_name))
            if line.actual_custody == "department" and not line.actual_department_id:
                raise UserError(_("%(name)s: ghi phòng ban thực tế.", name=equipment.display_name))
        move = Move.with_context(tp_equipment_move_internal=INTERNAL).create({
            "move_type": "adjust",
            "company_id": inventory.company_id.id,
            "date": fields.Date.context_today(self),
            "inventory_id": inventory.id,
            "reason": _("Điều chỉnh theo kiểm kê %(name)s: %(reason)s", name=inventory.name, reason=reason),
            "line_ids": [(0, 0, {
                "equipment_id": line.equipment_id.id,
                "to_custody": line.actual_custody or line.expected_custody,
                "to_employee_id": line.actual_employee_id.id if line.actual_custody in ("employee", "loan") else False,
                "to_department_id": line.actual_department_id.id if line.actual_custody == "department" else False,
                "to_location_id": line.actual_location_id.id,
                "to_partner_id": False,
                "to_lifecycle": "active",
                "condition": line.actual_state or False,
                "note": line.note or False,
            }) for line in lines],
        })
        move.with_context(tp_equipment_move_internal=INTERNAL).action_done()
        lines.with_context(tp_inventory_internal=INTERNAL).write({"adjust_move_id": move.id})
        inventory.message_post(body=Markup("%s <a href='/app/thiet-bi/phieu-ban-giao/%s'>%s</a>: %s") % (
            _("Đã điều chỉnh"), move.id, move.name, reason), subtype_xmlid="mail.mt_note")
        action = self.env["ir.actions.act_window"]._for_xml_id("tp_equipment.action_moves")
        action.update({
            "res_id": move.id,
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.move_form").id, "form")],
            "target": "current",
        })
        return action
