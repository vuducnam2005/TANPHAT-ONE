
import re
import uuid
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .common import (
    ASSET_CLASS,
    AVAILABILITY,
    CUSTODY,
    GENERIC_DENIED,
    HOLDING_CUSTODY,
    INTERNAL,
    LIFECYCLE,
    OWNERSHIP,
    RETIRE_REASON,
    TECH_STATE,
    VERIFICATION,
    WARRANTY_BASIS,
    WARRANTY_STATE,
    admin_user_domain,
    check_admin,
    fold_text,
    guard_native_mail,
    is_admin,
    lock_records,
)

# Fields that only a move document (bàn giao / thu hồi / điều chuyển ...) may change once the
# equipment is registered. Draft records keep them editable as "opening data from the source".
CUSTODY_FIELDS = (
    "tp_custody",
    "tp_employee_id",
    "tp_holder_department_id",
    "tp_location_id",
    "tp_vendor_id",
    "tp_lifecycle",
    "tp_retire_reason",
    "tp_retire_date",
)
VERSIONED_FIELDS = CUSTODY_FIELDS + ("tp_technical_state", "tp_verification")


QR_URL_RE = re.compile(r"/tp_equipment/qr/([0-9a-fA-F]{32})(?:[/?#]|$)")
TOKEN_ONLY_RE = re.compile(r"^([0-9a-fA-F]{32})$")


def _clean(value):
    return (value or "").strip() or False


@guard_native_mail
class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"
    _order = "tp_code desc, id desc"

    tp_code = fields.Char("Mã thiết bị", readonly=True, copy=False, index=True, tracking=True)
    tp_asset_class = fields.Selection(ASSET_CLASS, "Loại quản lý", default="device", required=True, tracking=True)
    tp_brand = fields.Char("Hãng sản xuất", tracking=True)
    tp_ownership = fields.Selection(OWNERSHIP, "Thuộc sở hữu", default="company", required=True, tracking=True)
    tp_owner_partner_id = fields.Many2one(
        "res.partner", "Bên sở hữu / cho thuê", tracking=True,
        help="Chỉ ghi khi thiết bị không thuộc công ty (thuê, cá nhân, đơn vị khác).")
    tp_owner_note = fields.Char("Ghi chú sở hữu", help="Ghi nguyên văn nguồn khi chưa xác minh bên sở hữu.")

    tp_lifecycle = fields.Selection(LIFECYCLE, "Vòng đời", default="draft", required=True, tracking=True, index=True)
    tp_registered_date = fields.Datetime("Ngày đăng ký", readonly=True, copy=False)
    tp_registered_by_id = fields.Many2one("res.users", "Người đăng ký", readonly=True, copy=False)
    tp_retire_reason = fields.Selection(RETIRE_REASON, "Lý do ngừng quản lý", tracking=True, copy=False)
    tp_retire_date = fields.Date("Ngày ngừng quản lý", tracking=True, copy=False)
    tp_retire_note = fields.Text("Ghi chú ngừng quản lý", copy=False)

    tp_custody = fields.Selection(CUSTODY, "Nơi giữ hiện tại", default="stock", required=True, tracking=True, index=True)
    tp_employee_id = fields.Many2one(
        "hr.employee", "Nhân viên đang giữ", ondelete="restrict", tracking=True, index="btree_not_null",
        copy=False, context={"active_test": False})
    tp_holder_department_id = fields.Many2one(
        "hr.department", "Phòng ban dùng chung", ondelete="restrict", tracking=True, copy=False,
        help="Dùng khi thiết bị giao cho cả phòng ban, không cho một nhân viên.")
    tp_location_id = fields.Many2one("tp.equipment.location", "Vị trí", ondelete="restrict", tracking=True, copy=False)
    tp_vendor_id = fields.Many2one("res.partner", "Đơn vị bên ngoài đang giữ", ondelete="restrict", tracking=True,
                                   copy=False, help="Đơn vị sửa chữa / bên cho thuê đang giữ thiết bị.")
    tp_move_line_ids = fields.One2many("tp.equipment.move.line", "equipment_id", "Lịch sử bàn giao", readonly=True)
    tp_pending_move_id = fields.Many2one("tp.equipment.move", "Phiếu chờ bàn giao", compute="_compute_tp_pending_move")
    tp_move_count = fields.Integer("Số phiếu bàn giao", compute="_compute_tp_pending_move")
    tp_holder_text = fields.Char("Đang ở", compute="_compute_tp_holder_text")
    # Not stored on purpose: an HR department change must never write equipment rows (and HR
    # officers have no equipment rights). The department is read from HR at display time.
    tp_current_department_id = fields.Many2one(
        "hr.department", "Phòng ban hiện tại", compute="_compute_tp_current_department",
        search="_search_tp_current_department")
    tp_employee_archived = fields.Boolean("Nhân viên giữ đã lưu trữ", compute="_compute_tp_employee_archived",
                                          search="_search_tp_employee_archived")

    tp_technical_state = fields.Selection(TECH_STATE, "Tình trạng kỹ thuật", default="unverified", required=True,
                                          tracking=True, index=True)
    tp_replacement_needed = fields.Boolean("Cần thay thế / nâng cấp", tracking=True,
                                           help="Nhu cầu thay thế độc lập với tình trạng kỹ thuật.")
    tp_condition_note = fields.Text("Ghi chú tình trạng")
    tp_verification = fields.Selection(VERIFICATION, "Mức xác minh", default="source", required=True, tracking=True)
    tp_verified_date = fields.Date("Ngày xác minh", copy=False)
    tp_availability = fields.Selection(AVAILABILITY, "Khả dụng", compute="_compute_tp_availability", store=True,
                                       index=True)

    tp_purchase_date = fields.Date("Ngày mua / nhận", tracking=True)
    tp_first_use_date = fields.Date("Ngày đưa vào sử dụng", tracking=True)
    tp_date_source = fields.Char("Ngày theo nguồn", help="Ghi nguyên văn nguồn (ví dụ “trước 2026”); không tự đổi thành ngày.")
    tp_currency_id = fields.Many2one(related="company_id.currency_id", string="Tiền tệ")
    tp_purchase_value = fields.Monetary("Giá trị mua", currency_field="tp_currency_id", tracking=True,
                                        help="Để trống khi chưa có chứng từ; không ghi 0 thay cho “chưa rõ”.")
    tp_purchase_value_known = fields.Boolean("Đã xác nhận giá trị mua", tracking=True,
                                             help="Bật cả khi giá trị xác nhận bằng 0; tắt nghĩa là chưa biết.")
    tp_supplier_id = fields.Many2one("res.partner", "Nhà cung cấp", tracking=True)

    tp_warranty_basis = fields.Selection(WARRANTY_BASIS, "Căn cứ bảo hành", default="unknown", required=True, tracking=True)
    tp_warranty_start = fields.Date("Bắt đầu bảo hành")
    tp_warranty_months = fields.Integer("Thời hạn bảo hành (tháng)")
    tp_warranty_end = fields.Date("Hết bảo hành", compute="_compute_tp_warranty_end", store=True)
    tp_warranty_meter_limit = fields.Integer("Giới hạn số đếm bảo hành")
    tp_warranty_meter_unit = fields.Char("Đơn vị số đếm", default="bản chụp")
    tp_warranty_source = fields.Char("Bảo hành theo nguồn", help="Ghi nguyên văn nguồn (ví dụ “Còn BH”, “trọn gói”).")
    tp_warranty_state = fields.Selection(WARRANTY_STATE, "Trạng thái bảo hành", compute="_compute_tp_warranty_state",
                                         search="_search_tp_warranty_state")
    tp_warranty_days_left = fields.Integer("Số ngày bảo hành còn lại", compute="_compute_tp_warranty_state")

    tp_cpu = fields.Char("CPU")
    tp_ram = fields.Char("RAM")
    tp_storage = fields.Char("Ổ lưu trữ")
    tp_gpu = fields.Char("Card đồ họa")
    tp_mainboard = fields.Char("Bo mạch chủ")
    tp_screen = fields.Char("Màn hình")
    tp_config_note = fields.Text("Cấu hình khác / theo nguồn")
    tp_software_ids = fields.One2many("tp.equipment.software", "equipment_id", "Phần mềm", copy=True)
    tp_meter_ids = fields.One2many("tp.equipment.meter", "equipment_id", "Chỉ số đếm")
    tp_meter_last = fields.Integer("Chỉ số đếm gần nhất", compute="_compute_tp_meter_last")
    tp_meter_last_date = fields.Date("Ngày đọc gần nhất", compute="_compute_tp_meter_last")

    tp_parent_id = fields.Many2one("maintenance.equipment", "Thuộc bộ máy / gắn vào", ondelete="restrict",
                                   index="btree_not_null", copy=False)
    tp_child_ids = fields.One2many("maintenance.equipment", "tp_parent_id", "Linh kiện / phụ kiện đi kèm")
    tp_replaces_id = fields.Many2one("maintenance.equipment", "Thay thế cho thiết bị", ondelete="set null", copy=False)

    tp_image = fields.Image("Ảnh thiết bị", max_width=1024, max_height=1024)
    tp_version = fields.Integer("Phiên bản dữ liệu", default=1, readonly=True, copy=False)
    tp_qr_token = fields.Char("Mã QR", readonly=True, copy=False, index=True, groups="base.group_system")
    tp_qr_url = fields.Char("Đường dẫn QR", compute="_compute_tp_qr_url", groups="base.group_system")
    tp_qr_image_url = fields.Char("Ảnh QR", compute="_compute_tp_qr_url", groups="base.group_system")
    tp_source_ref = fields.Char("Nguồn dữ liệu", readonly=True, copy=False,
                                help="Lô nhập / tệp / dòng nguồn tạo ra hồ sơ này.")

    tp_search = fields.Char("Tìm nhanh", compute="_compute_tp_search", search="_search_tp_search")

    _tp_code_unique = models.UniqueIndex("(tp_code) WHERE tp_code IS NOT NULL", "Mã thiết bị đã tồn tại.")
    _tp_qr_unique = models.UniqueIndex("(tp_qr_token) WHERE tp_qr_token IS NOT NULL", "Mã QR đã tồn tại.")
    _tp_serial_verified_unique = models.UniqueIndex(
        "(company_id, lower(coalesce(tp_brand, '')), lower(coalesce(model, '')), lower(serial_no)) "
        "WHERE tp_verification = 'verified' AND serial_no IS NOT NULL AND serial_no != ''",
        "Serial đã xác minh trùng trong cùng công ty, hãng và model.")

    # ------------------------------------------------------------------ computes
    @api.depends("tp_code", "name")
    def _compute_display_name(self):
        for equipment in self:
            name = equipment.name or ""
            equipment.display_name = f"{equipment.tp_code} · {name}" if equipment.tp_code else name

    def _compute_tp_search(self):
        for equipment in self:
            equipment.tp_search = False

    def _search_tp_search(self, operator, value):
        if operator not in ("ilike", "not ilike", "=", "like"):
            return NotImplemented
        positive = operator != "not ilike"
        op = "ilike" if operator in ("ilike", "not ilike") else operator
        # EQUIP-UI-002: one backend box over device name/code/serial/model/brand and the HR holder name/code.
        domain = ["|", "|", "|", "|", "|", "|", ("name", op, value), ("tp_code", op, value), ("serial_no", op, value),
                  ("model", op, value), ("tp_brand", op, value), ("tp_employee_id.name", op, value),
                  ("tp_employee_id.tp_employee_code", op, value)]
        # Vietnamese names are typed with or without marks and with either tone placement
        # ("thùy", "thuy" -> "Thuỳ"); ILIKE alone misses those, so also match the
        # folded text. Office-scale tables (tens to a few thousand rows), read once per search.
        extra = self._tp_folded_search_leaves(value) if op == "ilike" else []
        if extra:
            domain = ["|"] * len(extra) + domain + extra
        return domain if positive else ["!"] + domain

    def _tp_folded_search_leaves(self, value):
        needle = fold_text(value) if isinstance(value, str) else ""
        if not needle:
            return []
        employees = self.env["hr.employee"].with_context(active_test=False).search_fetch(
            [], ["name", "tp_employee_code"])
        employee_ids = [employee.id for employee in employees
                        if needle in fold_text(employee.name) or needle in fold_text(employee.tp_employee_code)]
        records = self.with_context(active_test=False).search_fetch(
            [], ["name", "tp_code", "serial_no", "model", "tp_brand"])
        equipment_ids = [record.id for record in records
                         if any(needle in fold_text(text) for text in
                                (record.name, record.tp_code, record.serial_no, record.model, record.tp_brand))]
        leaves = []
        if employee_ids:
            leaves.append(("tp_employee_id", "in", employee_ids))
        if equipment_ids:
            leaves.append(("id", "in", equipment_ids))
        return leaves

    @api.depends("tp_custody", "tp_employee_id", "tp_holder_department_id", "tp_location_id")
    def _compute_tp_current_department(self):
        for equipment in self:
            department = self.env["hr.department"]
            if equipment.tp_custody in ("employee", "loan") and equipment.tp_employee_id:
                department = equipment.tp_employee_id.sudo().department_id
            elif equipment.tp_custody == "department":
                department = equipment.tp_holder_department_id
            elif equipment.tp_custody == "location":
                department = equipment.tp_location_id.department_id
            equipment.tp_current_department_id = department

    def _search_tp_current_department(self, operator, value):
        if operator not in ("=", "in", "!=", "not in"):
            return NotImplemented
        positive = operator in ("=", "in")
        value = list(value) if operator in ("in", "not in") else [value]
        if False in value or None in value:
            value = [v for v in value if v]
            domain = [
                "|", "|", "|",
                "&", ("tp_custody", "in", ("employee", "loan")), ("tp_employee_id.department_id", "=", False),
                "&", ("tp_custody", "=", "department"), ("tp_holder_department_id", "=", False),
                "&", ("tp_custody", "=", "location"), ("tp_location_id.department_id", "=", False),
                ("tp_custody", "not in", ("employee", "loan", "department", "location")),
            ]
            if value:
                domain = ["|"] + domain + self._search_tp_current_department("in", value)
        else:
            domain = [
                "|", "|",
                "&", ("tp_custody", "in", ("employee", "loan")), ("tp_employee_id.department_id", "in", value),
                "&", ("tp_custody", "=", "department"), ("tp_holder_department_id", "in", value),
                "&", ("tp_custody", "=", "location"), ("tp_location_id.department_id", "in", value),
            ]
        return domain if positive else ["!"] + domain

    @api.depends("tp_employee_id")
    def _compute_tp_employee_archived(self):
        for equipment in self:
            equipment.tp_employee_archived = bool(equipment.tp_employee_id and not equipment.tp_employee_id.active)

    def _search_tp_employee_archived(self, operator, value):
        if operator in ("in", "not in"):
            values = set(value)
            if values == {True, False}:
                return [] if operator == "in" else [("id", "=", 0)]
            value = next(iter(values), False)
            operator = "=" if operator == "in" else "!="
        if operator not in ("=", "!=") or value not in (True, False):
            return NotImplemented
        archived = self.env["hr.employee"].with_context(active_test=False)._search([("active", "=", False)])
        if (operator == "=") == value:
            return [("tp_employee_id", "in", archived)]
        return ["|", ("tp_employee_id", "=", False), ("tp_employee_id", "not in", archived)]

    def _tp_availability_extra(self):
        """Open repair requests: in progress / at vendor → "repair"; only reported and in stock → "check"."""
        result = {}
        for equipment in self:
            states = set(equipment.maintenance_ids.mapped("tp_state"))
            if states & {"in_progress", "vendor"}:
                result[equipment.id] = "repair"
            elif "new" in states and equipment.tp_custody == "stock":
                result[equipment.id] = "check"
        return result

    @api.depends("tp_lifecycle", "tp_custody", "tp_technical_state", "tp_verification", "tp_move_line_ids.state",
                 "maintenance_ids.tp_state")
    def _compute_tp_availability(self):
        extra = self._tp_availability_extra()
        for equipment in self:
            if equipment.tp_lifecycle == "retired":
                value = "retired"
            elif equipment.tp_lifecycle == "draft":
                value = "draft"
            elif any(line.state == "pending" for line in equipment.tp_move_line_ids):
                value = "reserved"
            elif equipment.id in extra:
                value = extra[equipment.id]
            elif equipment.tp_custody == "vendor":
                value = "repair"
            elif equipment.tp_custody in HOLDING_CUSTODY:
                value = "in_use"
            elif equipment.tp_technical_state == "broken":
                value = "blocked"
            elif equipment.tp_technical_state == "unverified" or equipment.tp_verification == "source":
                value = "check"
            else:
                value = "available"
            equipment.tp_availability = value

    @api.depends("tp_move_line_ids.state")
    def _compute_tp_pending_move(self):
        for equipment in self:
            lines = equipment.tp_move_line_ids
            equipment.tp_pending_move_id = lines.filtered(lambda line: line.state == "pending")[:1].move_id
            equipment.tp_move_count = len(lines.move_id)

    @api.depends("tp_custody", "tp_employee_id", "tp_holder_department_id", "tp_location_id", "tp_vendor_id",
                 "tp_lifecycle")
    def _compute_tp_holder_text(self):
        Move = self.env["tp.equipment.move"]
        for equipment in self:
            if equipment.tp_lifecycle == "retired":
                equipment.tp_holder_text = _("Ngừng quản lý")
            else:
                equipment.tp_holder_text = Move._tp_holder_text(
                    equipment.tp_custody, equipment.tp_employee_id, equipment.tp_holder_department_id,
                    equipment.tp_location_id, equipment.tp_vendor_id)

    @api.depends("tp_qr_token")
    def _compute_tp_qr_url(self):
        base = self.get_base_url() if self else ""
        for equipment in self:
            if equipment.tp_qr_token and equipment.tp_lifecycle != "draft":
                url = f"{base}/tp_equipment/qr/{equipment.tp_qr_token}"
                equipment.tp_qr_url = url
                equipment.tp_qr_image_url = f"/tp_equipment/qr_image/{equipment.tp_qr_token}"
            else:
                equipment.tp_qr_url = False
                equipment.tp_qr_image_url = False

    tp_employee_image_128 = fields.Image(
        "Ảnh nhân viên", related="tp_employee_id.image_128", groups="base.group_system")
    tp_employee_job_title = fields.Char(
        "Chức danh", related="tp_employee_id.job_title", groups="base.group_system")
    # EQUIP-UI-002: HR identity shown in the users table, always read from the linked HR record (no copy).
    tp_employee_code = fields.Char(
        "Mã nhân viên", related="tp_employee_id.tp_employee_code", groups="base.group_system")
    tp_department_name = fields.Char("Phòng ban (HR)", compute="_compute_tp_department_name")
    tp_display_subtitle = fields.Char("Mô tả ngắn", compute="_compute_tp_ui_helpers")
    tp_holder_summary = fields.Char("Người / nơi giữ", compute="_compute_tp_ui_helpers")
    tp_stock_location_display = fields.Char("Vị trí kho", compute="_compute_tp_ui_helpers")

    @api.depends("tp_brand", "model", "serial_no", "tp_custody", "tp_holder_text", "tp_location_id")
    def _compute_tp_ui_helpers(self):
        for equipment in self:
            parts = [p for p in (equipment.tp_brand, equipment.model) if p]
            if not parts and equipment.serial_no:
                parts = [f"S/N: {equipment.serial_no}"]
            equipment.tp_display_subtitle = " · ".join(parts) if parts else False
            equipment.tp_holder_summary = equipment.tp_holder_text or "Chưa gán"
            if equipment.tp_location_id:
                equipment.tp_stock_location_display = equipment.tp_location_id.name
            elif equipment.tp_custody == "stock":
                equipment.tp_stock_location_display = "Kho văn phòng (chưa gắn kệ)"
            else:
                equipment.tp_stock_location_display = "—"

    @api.depends("tp_current_department_id", "tp_custody")
    def _compute_tp_department_name(self):
        for equipment in self:
            department = equipment.tp_current_department_id
            if department:
                equipment.tp_department_name = department.sudo().display_name
            elif equipment.tp_custody in ("employee", "loan", "department"):
                equipment.tp_department_name = "Chưa có phòng ban"
            else:
                # EQUIP-SIMPLE-003: stock / location / vendor rows have no department; leave the cell empty.
                equipment.tp_department_name = False

    def action_tp_open_detail(self):
        check_admin(self.env, self)
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("tp_equipment.action_equipment_all_records")
        action.update({
            "name": self.display_name,
            "res_id": self.id,
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.equipment_form").id, "form")],
            "target": "current",
            "context": {"tp_eq_leaf": "tp_equipment.menu_equipment_all"},
        })
        return action

    def tp_refresh_availability(self):
        self.sudo()._compute_tp_availability()

    @api.depends("tp_warranty_basis", "tp_warranty_start", "tp_warranty_months", "warranty_date")
    def _compute_tp_warranty_end(self):
        for equipment in self:
            end = False
            if equipment.tp_warranty_basis in ("duration", "date_or_meter") and equipment.tp_warranty_start\
                    and equipment.tp_warranty_months > 0:
                end = equipment.tp_warranty_start + relativedelta(months=equipment.tp_warranty_months) - timedelta(days=1)
            elif equipment.tp_warranty_basis in ("date", "date_or_meter"):
                end = equipment.warranty_date
            equipment.tp_warranty_end = end

    def _tp_warning_days(self):
        value = self.env["ir.config_parameter"].sudo().get_str("tp_equipment.warranty_warning_days")
        try:
            return max(int(value), 0) if value not in (None, False, "") else 30
        except (TypeError, ValueError):
            return 30

    def _tp_warranty_values(self):
        today = fields.Date.context_today(self)
        warn_days = self._tp_warning_days()
        result = {}
        for equipment in self:
            basis = equipment.tp_warranty_basis
            state, days = "unknown", 0
            if basis == "none":
                state = "none"
            elif basis in ("date", "duration", "meter", "date_or_meter"):
                states = []
                end = equipment.tp_warranty_end
                if basis in ("date", "duration", "date_or_meter") and end:
                    days = (end - today).days
                    states.append("expired" if days < 0 else "expiring" if days <= warn_days else "active")
                limit = equipment.tp_warranty_meter_limit
                if basis in ("meter", "date_or_meter") and limit > 0 and equipment.tp_meter_ids:
                    last = equipment.tp_meter_last
                    states.append("expired" if last >= limit else "expiring" if last >= limit * 0.9 else "active")
                if states:
                    # "whichever comes first": the worst state wins.
                    state = max(states, key=["active", "expiring", "expired"].index)
            result[equipment.id] = (state, days)
        return result

    @api.depends("tp_warranty_basis", "tp_warranty_end", "tp_warranty_meter_limit", "tp_meter_ids.value")
    def _compute_tp_warranty_state(self):
        values = self._tp_warranty_values()
        for equipment in self:
            equipment.tp_warranty_state, equipment.tp_warranty_days_left = values.get(equipment.id, ("unknown", 0))

    def _search_tp_warranty_state(self, operator, value):
        if operator not in ("=", "!=", "in", "not in"):
            return NotImplemented
        wanted = set(value) if operator in ("in", "not in") else {value}
        records = self.with_context(active_test=False).search([])
        values = records._tp_warranty_values()
        ids = [rid for rid, (state, _days) in values.items() if state in wanted]
        return [("id", "in" if operator in ("=", "in") else "not in", ids)]

    @api.depends("tp_meter_ids.value", "tp_meter_ids.date")
    def _compute_tp_meter_last(self):
        for equipment in self:
            last = equipment.tp_meter_ids.sorted(lambda m: (m.date, m.id))[-1:] if equipment.tp_meter_ids else False
            equipment.tp_meter_last = last.value if last else 0
            equipment.tp_meter_last_date = last.date if last else False

    # ------------------------------------------------------------------ constraints
    @api.constrains("tp_custody", "tp_employee_id", "tp_holder_department_id", "tp_location_id")
    def _check_tp_custody(self):
        for equipment in self:
            custody = equipment.tp_custody
            if custody in ("employee", "loan") and not equipment.tp_employee_id:
                raise ValidationError(_("%(name)s: chọn nhân viên đang giữ.", name=equipment.display_name))
            if custody == "department" and not equipment.tp_holder_department_id:
                raise ValidationError(_("%(name)s: chọn phòng ban dùng chung.", name=equipment.display_name))
            if custody == "location" and not equipment.tp_location_id:
                raise ValidationError(_("%(name)s: chọn vị trí đặt thiết bị.", name=equipment.display_name))

    @api.constrains("tp_parent_id")
    def _check_tp_parent(self):
        if self._has_cycle("tp_parent_id"):
            raise ValidationError(_("Không thể gắn thiết bị vào chính nó hoặc vào linh kiện của nó."))

    @api.constrains("tp_warranty_months", "tp_warranty_meter_limit", "tp_purchase_value")
    def _check_tp_positive(self):
        for equipment in self:
            if equipment.tp_warranty_months < 0 or equipment.tp_warranty_meter_limit < 0:
                raise ValidationError(_("Thời hạn và số đếm bảo hành không được âm."))
            if equipment.tp_purchase_value and equipment.tp_purchase_value < 0:
                raise ValidationError(_("Giá trị mua không được âm."))

    @api.constrains("owner_user_id", "technician_user_id")
    def _check_tp_admin_users(self):
        for equipment in self:
            for user in equipment.owner_user_id | equipment.technician_user_id:
                if user.share or not user.has_group("base.group_system"):
                    raise ValidationError(_("Người phụ trách hồ sơ thiết bị phải là quản trị hệ thống."))

    @api.constrains("tp_retire_reason", "tp_lifecycle")
    def _check_tp_retire(self):
        for equipment in self:
            if equipment.tp_lifecycle == "retired" and not equipment.tp_retire_reason:
                raise ValidationError(_("Thiết bị ngừng quản lý phải có lý do."))

    # ------------------------------------------------------------------ ORM
    def _tp_prepare_vals(self, vals):
        for key in ("serial_no", "tp_brand", "model", "tp_cpu", "tp_ram", "tp_storage", "tp_gpu", "tp_screen"):
            if key in vals and isinstance(vals[key], str):
                vals[key] = _clean(vals[key])
        if vals.get("tp_custody") and vals["tp_custody"] not in ("employee", "loan"):
            vals.setdefault("tp_employee_id", False)
        if vals.get("tp_custody") and vals["tp_custody"] != "department":
            vals.setdefault("tp_holder_department_id", False)
        if vals.get("tp_custody") and vals["tp_custody"] != "vendor":
            vals.setdefault("tp_vendor_id", False)
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env, self)
        sequence = self.env["ir.sequence"].sudo()
        for vals in vals_list:
            self._tp_prepare_vals(vals)
            vals["tp_lifecycle"] = "draft"
            vals["tp_version"] = 1
            for key in ("tp_registered_date", "tp_registered_by_id", "tp_retire_date", "tp_retire_reason"):
                vals.pop(key, None)
            vals.setdefault("owner_user_id", self.env.uid if is_admin(self.env) and not self.env.su else False)
            if not vals.get("tp_code"):
                vals["tp_code"] = sequence.next_by_code("tp.equipment") or "/"
            vals["tp_qr_token"] = uuid.uuid4().hex
        return super().create(vals_list)

    def write(self, vals):
        check_admin(self.env, self)
        vals = self._tp_prepare_vals(dict(vals))
        if "tp_version" in vals:
            raise UserError(_("Phiên bản hồ sơ do hệ thống quản lý."))
        if {"tp_lifecycle", "tp_registered_date", "tp_registered_by_id", "tp_retire_date", "tp_retire_reason"} & set(vals) and\
                self.env.context.get("tp_equipment_move") is not INTERNAL:
            raise UserError(_("Dùng Đăng ký hoặc phiếu nghiệp vụ để đổi vòng đời hồ sơ."))
        if any(key in vals for key in VERSIONED_FIELDS):
            lock_records(self)
        protected = [key for key in CUSTODY_FIELDS if key in vals]
        if protected and self.env.context.get("tp_equipment_move") is not INTERNAL:
            locked = self.filtered(lambda e: e.tp_lifecycle != "draft")
            if locked:
                raise UserError(_(
                    "%(names)s đã đăng ký: đổi người giữ, vị trí hoặc ngừng quản lý phải lập phiếu bàn giao / "
                    "điều chuyển / ngừng quản lý để giữ lịch sử.",
                    names=", ".join(locked[:3].mapped("display_name"))))
        if "tp_qr_token" in vals and self.env.context.get("tp_equipment_rotate_qr") is not INTERNAL:
            vals.pop("tp_qr_token")
        if any(key in vals for key in VERSIONED_FIELDS):
            for equipment in self:
                super(MaintenanceEquipment, equipment).write(dict(vals, tp_version=equipment.tp_version + 1))
            return True
        return super().write(vals)

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default)
        for equipment, vals in zip(self, vals_list):
            vals.update({
                "name": default.get("name") or _("%s (bản sao)", equipment.name),
                "tp_lifecycle": "draft",
                "tp_custody": "stock",
                "tp_technical_state": "unverified",
                "tp_verification": "source",
                "tp_replacement_needed": False,
                "tp_source_ref": False,
                "serial_no": False,
                "tp_verified_date": False,
                "tp_purchase_value_known": False,
                "tp_purchase_value": 0,
                "tp_purchase_date": False,
                "warranty_date": False,
                "tp_warranty_basis": "unknown",
                "tp_warranty_start": False,
                "tp_warranty_months": 0,
                "tp_warranty_meter_limit": 0,
                "tp_software_ids": [],
            })
        return vals_list

    def _tp_history_counts(self):
        """Hook for later slices: records that make an equipment non-deletable."""
        self.ensure_one()
        return {
            _("Phiếu sửa chữa / bảo trì"): len(self.with_context(active_test=False).maintenance_ids),
            _("Linh kiện / phụ kiện gắn kèm"): len(self.with_context(active_test=False).tp_child_ids),
            _("Chỉ số đếm"): len(self.tp_meter_ids),
            _("Phiếu bàn giao / nhập kho"): len(self.tp_move_line_ids),
        }

    @api.ondelete(at_uninstall=False)
    def _unlink_tp_only_clean_drafts(self):
        if self.env.su and (self.env.context.get("tp_equipment_force_delete") is INTERNAL):
            return
        check_admin(self.env, self)
        for equipment in self:
            if equipment.tp_lifecycle != "draft":
                raise UserError(_("%(name)s đã đăng ký: dùng Ngừng quản lý, không xóa hồ sơ.", name=equipment.display_name))
            used = [label for label, count in equipment._tp_history_counts().items() if count]
            if used:
                raise UserError(_("%(name)s đã có %(what)s nên không xóa được.",
                                  name=equipment.display_name, what=", ".join(used)))

    # ------------------------------------------------------------------ actions
    def action_tp_register(self):
        check_admin(self.env, self)
        lock_records(self)
        for equipment in self:
            if equipment.tp_lifecycle != "draft":
                raise UserError(_("%(name)s không ở trạng thái nháp.", name=equipment.display_name))
            if not equipment.category_id:
                raise UserError(_("%(name)s: chọn phân loại trước khi đăng ký.", name=equipment.display_name))
            reg_vals = {
                "tp_lifecycle": "active",
                "tp_registered_date": fields.Datetime.now(),
                "tp_registered_by_id": self.env.uid,
            }
            reg_ctx = {"tp_equipment_move": INTERNAL}
            if not equipment.tp_qr_token:
                reg_vals["tp_qr_token"] = uuid.uuid4().hex
                reg_ctx["tp_equipment_rotate_qr"] = INTERNAL
            equipment.with_context(**reg_ctx).write(reg_vals)
            equipment._tp_after_register()
            equipment.message_post(body=_("Đăng ký vào Kho thiết bị văn phòng."), subtype_xmlid="mail.mt_note")
        return True

    def _tp_after_register(self):
        """Opening move: documents where the equipment was when it entered the register."""
        self.env["tp.equipment.move"]._tp_create_opening(self)
        return True

    def action_tp_mark_verified(self):
        check_admin(self.env, self)
        lock_records(self)
        self.write({"tp_verification": "verified", "tp_verified_date": fields.Date.context_today(self)})
        return True

    def action_tp_rotate_qr(self):
        check_admin(self.env, self)
        for equipment in self:
            equipment.with_context(tp_equipment_rotate_qr=INTERNAL).write({"tp_qr_token": uuid.uuid4().hex})
            equipment.message_post(body=_("Đã cấp lại mã QR; nhãn cũ không còn hiệu lực."), subtype_xmlid="mail.mt_note")
        return True

    def action_tp_open_children(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("tp_equipment.action_equipment_all_records")
        action.update({
            "name": _("Linh kiện / phụ kiện của %s", self.display_name),
            "view_mode": "list,form",
            "views": [(self.env.ref("tp_equipment.equipment_list").id, "list"),
                      (self.env.ref("tp_equipment.equipment_form").id, "form")],
            "domain": [("tp_parent_id", "=", self.id)],
            "context": {"default_tp_parent_id": self.id, "default_tp_asset_class": "component",
                        "tp_filter_profile": "equipment"},
        })
        return action

    def action_tp_new_move(self):
        """Open a pre-filled move document (header buttons, list action). Nothing is saved here."""
        check_admin(self.env, self)
        move_type = self.env.context.get("tp_move_type") or "assign"
        if move_type in ("opening", "adjust", "reversal"):
            raise UserError(_("Loại phiếu này do hệ thống tạo."))
        if not self:
            raise UserError(_("Chọn ít nhất một thiết bị."))
        context = {
            "default_move_type": move_type,
            "default_line_ids": [(0, 0, {"equipment_id": equipment.id}) for equipment in self],
            "tp_eq_leaf": "tp_equipment.menu_moves",
        }
        if move_type == "rental_return" and len(self.tp_owner_partner_id) == 1:
            context["default_target_partner_id"] = self.tp_owner_partner_id.id
        if move_type == "repair_return" and len(self.tp_vendor_id) == 1:
            context["default_target_partner_id"] = self.tp_vendor_id.id
        action = self.env["ir.actions.act_window"]._for_xml_id("tp_equipment.action_moves")
        action.update({
            "name": _("Lập phiếu"),
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.move_form").id, "form")],
            "target": "current",
            "context": context,
        })
        return action

    def action_tp_open_pending_move(self):
        check_admin(self.env, self)
        self.ensure_one()
        if not self.tp_pending_move_id:
            raise UserError(_("Thiết bị không có phiếu chờ bàn giao."))
        action = self.env["ir.actions.act_window"]._for_xml_id("tp_equipment.action_moves_pending")
        action.update({
            "res_id": self.tp_pending_move_id.id,
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.move_form").id, "form")],
            "target": "current",
        })
        return action

    def action_tp_open_moves(self):
        check_admin(self.env, self)
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("tp_equipment.action_moves")
        action.update({
            "name": _("Phiếu của %s", self.display_name),
            "view_mode": "list,form",
            "views": [(self.env.ref("tp_equipment.move_list").id, "list"),
                      (self.env.ref("tp_equipment.move_form").id, "form")],
            "domain": [("line_ids.equipment_id", "=", self.id)],
            "context": {"tp_filter_profile": "move", "tp_eq_leaf": "tp_equipment.menu_equipment_all"},
        })
        return action

    def action_tp_print_labels(self):
        check_admin(self.env, self)
        equipments = self.filtered(lambda e: e.tp_lifecycle != "draft")
        if not equipments:
            raise UserError(_("Chỉ in nhãn cho thiết bị đã đăng ký vào kho."))
        if len(equipments) > 240:
            raise UserError(_("In tối đa 240 nhãn mỗi lần (10 trang A4)."))
        ids = ",".join(str(i) for i in equipments.ids)
        return {"type": "ir.actions.act_url", "url": f"/tp_equipment/labels.pdf?ids={ids}", "target": "new"}

    @api.model
    def tp_scan_lookup(self, value):
        """Keyboard-wedge / camera scanner input: QR URL, bare token, equipment code or serial."""
        check_admin(self.env, self)
        value = (value or "").strip()
        if not value or len(value) > 512:
            return {"error": _("Quét hoặc nhập mã thiết bị.")}
        Equipment = self.with_context(active_test=False)
        match = QR_URL_RE.search(value) or TOKEN_ONLY_RE.match(value)
        if match:
            equipment = Equipment.search([("tp_qr_token", "=", match.group(1).lower())], limit=1)
            if not equipment:
                return {"error": _("Mã QR không khớp thiết bị nào hoặc nhãn đã được cấp lại.")}
        else:
            equipment = Equipment.search([("tp_code", "=", value.upper())], limit=2)\
                or Equipment.search([("serial_no", "=", value)], limit=2)
            if len(equipment) > 1:
                return {"error": _("Có nhiều thiết bị cùng serial %s; tìm theo mã thiết bị.", value)}
            if not equipment:
                return {"error": _("Không tìm thấy thiết bị với mã / serial “%s”.", value)}
        return {"id": equipment.id, "name": equipment.display_name, "availability": equipment.tp_availability}

    @api.model
    def tp_admin_user_domain(self):
        return admin_user_domain(self.env)


@guard_native_mail
class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env, self)
        return super().create(vals_list)

    def write(self, vals):
        check_admin(self.env, self)
        return super().write(vals)

    @api.constrains("owner_user_id", "user_ids")
    def _check_tp_admin_users(self):
        for request in self:
            for user in request.owner_user_id | request.user_ids:
                if user.share or not user.has_group("base.group_system"):
                    raise ValidationError(_("Người phụ trách phiếu sửa chữa phải là quản trị hệ thống; ghi kỹ thuật viên "
                                            "bên ngoài ở mục Người / đơn vị thực hiện."))


class MaintenanceEquipmentCategory(models.Model):
    _inherit = "maintenance.equipment.category"
    _order = "tp_sequence, name"

    tp_sequence = fields.Integer("Thứ tự", default=10)
    tp_code = fields.Char("Mã phân loại")
    tp_asset_class = fields.Selection(ASSET_CLASS, "Loại quản lý mặc định", default="device", required=True)
    tp_has_config = fields.Boolean("Có cấu hình máy tính", help="Hiện các trường CPU / RAM / ổ lưu trữ.")
    tp_has_meter = fields.Boolean("Theo dõi số đếm", help="Máy in / photocopy: ghi chỉ số đếm bản chụp.")
    active = fields.Boolean(default=True)

    def _make_access_error_message(self, operation, domain):

        if not is_admin(self.env):
            return AccessError(GENERIC_DENIED)
        return super()._make_access_error_message(operation, domain)

    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env, self)
        for vals in vals_list:
            vals.setdefault("technician_user_id", False)
        return super().create(vals_list)

    def write(self, vals):
        check_admin(self.env, self)
        return super().write(vals)


class TpEquipmentLocation(models.Model):
    _name = "tp.equipment.location"
    _description = "Vị trí đặt thiết bị"
    _inherit = ["tp.equipment.secure.mixin"]
    _order = "sequence, name"

    name = fields.Char("Tên vị trí", required=True, tracking=True)
    code = fields.Char("Mã vị trí")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", "Công ty", default=lambda self: self.env.company, required=True)
    work_location_id = fields.Many2one("hr.work.location", "Địa điểm làm việc (HR)")
    department_id = fields.Many2one("hr.department", "Phòng ban phụ trách vị trí")
    shared = fields.Boolean("Vị trí dùng chung", default=True)
    note = fields.Text("Ghi chú")
    equipment_ids = fields.One2many("maintenance.equipment", "tp_location_id", "Thiết bị")
    equipment_count = fields.Integer("Số thiết bị", compute="_compute_equipment_count")

    _code_unique = models.UniqueIndex("(company_id, lower(code)) WHERE code IS NOT NULL", "Mã vị trí đã tồn tại.")

    def _compute_equipment_count(self):
        counts = dict(self.env["maintenance.equipment"]._read_group(
            [("tp_location_id", "in", self.ids)], ["tp_location_id"], ["__count"]))
        for location in self:
            location.equipment_count = counts.get(location, 0)


class TpEquipmentSoftware(models.Model):
    _name = "tp.equipment.software"
    _description = "Phần mềm trên thiết bị"
    _order = "equipment_id, kind, id"

    equipment_id = fields.Many2one("maintenance.equipment", "Thiết bị", required=True, ondelete="cascade", index=True)
    kind = fields.Selection([("os", "Hệ điều hành"), ("office", "Bộ văn phòng"), ("other", "Phần mềm khác")],
                            "Loại", default="os", required=True)
    name = fields.Char("Tên / phiên bản", required=True)
    license_declared = fields.Selection(
        [("licensed", "Nguồn ghi có bản quyền"), ("unlicensed", "Nguồn ghi không bản quyền"),
         ("unknown", "Nguồn ghi không xác minh / chưa rõ")],
        "Khai báo nguồn", default="unknown", required=True,
        help="Khai báo theo tệp nguồn, không phải kết luận pháp lý về bản quyền.")
    license_check = fields.Selection(
        [("not_checked", "Chưa kiểm tra"), ("evidence", "Đã kiểm tra – có chứng từ"),
         ("no_evidence", "Đã kiểm tra – chưa có chứng từ")],
        "Kết quả kiểm tra", default="not_checked", required=True)
    evidence_ref = fields.Char("Chứng từ / số license", groups="base.group_system")
    checked_date = fields.Date("Ngày kiểm tra")
    note = fields.Char("Ghi chú")

    @api.constrains("license_check", "evidence_ref")
    def _check_evidence(self):
        for line in self:
            if line.license_check == "evidence" and not (line.evidence_ref or "").strip():
                raise ValidationError(_("Ghi số chứng từ / license khi chọn “có chứng từ”."))


class TpEquipmentMeter(models.Model):
    _name = "tp.equipment.meter"
    _description = "Chỉ số đếm thiết bị"
    _order = "date desc, id desc"

    equipment_id = fields.Many2one("maintenance.equipment", "Thiết bị", required=True, ondelete="cascade", index=True)
    date = fields.Date("Ngày đọc", required=True, default=fields.Date.context_today)
    value = fields.Integer("Chỉ số", required=True)
    unit = fields.Char("Đơn vị", default="bản chụp")
    source = fields.Selection([("manual", "Đọc trực tiếp"), ("vendor", "Nhà cung cấp báo"), ("inventory", "Kiểm kê"),
                               ("repair", "Phiếu sửa chữa")], "Nguồn", default="manual", required=True)
    note = fields.Char("Ghi chú")

    @api.constrains("value", "equipment_id", "date")
    def _check_value(self):
        for reading in self:
            if reading.value < 0:
                raise ValidationError(_("Chỉ số đếm không được âm."))
            earlier = self.search([("equipment_id", "=", reading.equipment_id.id), ("id", "!=", reading.id),
                                   ("date", "<=", reading.date), ("value", ">", reading.value)], limit=1)
            if earlier:
                raise ValidationError(_("Chỉ số %(value)s thấp hơn chỉ số đã ghi ngày %(date)s; kiểm tra lại hoặc ghi chú "
                                        "thay bộ đếm.", value=reading.value, date=earlier.date))
