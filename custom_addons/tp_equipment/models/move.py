"""Equipment moves (EQUIP-001 part 2): bàn giao, thu hồi, điều chuyển, cho mượn, sửa ngoài, kết thúc.

Rules:
* draft → pending (reserved, one pending move per equipment) → done, or cancel.
* Equipment rows are locked (FOR UPDATE NOWAIT) and their ``tp_version`` must still match the version
  captured when the move was confirmed; otherwise the move must be re-checked.
* A done move is immutable. Mistakes are corrected by a reversal move, which only works while no later
  change touched the equipment.
* ``idempotency_key`` makes a replayed create (double submit, retried RPC) return the first document.
"""
import uuid

from markupsafe import Markup
from psycopg2 import errors as pg_errors

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL

from .common import (
    CUSTODY,
    INTERNAL,
    LIFECYCLE,
    RETIRE_REASON,
    TECH_STATE,
    check_admin,
    lock_records,
)

MOVE_TYPES = [
    ("opening", "Ghi nhận ban đầu"),
    ("assign", "Bàn giao / cấp phát"),
    ("transfer", "Điều chuyển"),
    ("return", "Thu hồi về kho"),
    ("loan", "Cho mượn"),
    ("loan_return", "Nhận lại thiết bị cho mượn"),
    ("send_repair", "Gửi sửa chữa bên ngoài"),
    ("repair_return", "Nhận về sau sửa chữa"),
    ("rental_return", "Trả thiết bị thuê"),
    ("retire", "Ngừng quản lý / thanh lý"),
    ("lost", "Báo mất"),
    ("adjust", "Điều chỉnh sau kiểm kê"),
    ("reversal", "Đảo phiếu"),
]
MOVE_STATES = [
    ("draft", "Nháp"),
    ("pending", "Chờ bàn giao"),
    ("done", "Đã hoàn tất"),
    ("cancel", "Đã hủy"),
]
TARGET_CUSTODY = [
    ("employee", "Nhân viên"),
    ("department", "Phòng ban dùng chung"),
    ("location", "Đặt tại vị trí"),
]
SYSTEM_TYPES = ("opening", "adjust", "reversal")
USER_TYPES = [item for item in MOVE_TYPES if item[0] not in SYSTEM_TYPES]
ALLOWED_FROM = {
    "assign": ("stock",),
    "transfer": ("employee", "department", "location"),
    "return": ("employee", "department", "location"),
    "loan": ("stock",),
    "loan_return": ("loan",),
    "send_repair": ("stock", "employee", "department", "location", "loan"),
    "repair_return": ("vendor",),
    "rental_return": ("stock", "vendor"),
    "retire": ("stock", "vendor"),
    "lost": ("stock", "employee", "department", "location", "loan", "vendor"),
}
END_TYPES = ("rental_return", "retire", "lost")
TITLES = {
    "opening": "BIÊN BẢN GHI NHẬN THIẾT BỊ",
    "assign": "BIÊN BẢN BÀN GIAO THIẾT BỊ",
    "transfer": "BIÊN BẢN ĐIỀU CHUYỂN THIẾT BỊ",
    "return": "BIÊN BẢN THU HỒI THIẾT BỊ",
    "loan": "BIÊN BẢN CHO MƯỢN THIẾT BỊ",
    "loan_return": "BIÊN BẢN NHẬN LẠI THIẾT BỊ CHO MƯỢN",
    "send_repair": "BIÊN BẢN GIAO THIẾT BỊ SỬA CHỮA",
    "repair_return": "BIÊN BẢN NHẬN THIẾT BỊ SAU SỬA CHỮA",
    "rental_return": "BIÊN BẢN TRẢ THIẾT BỊ THUÊ",
    "retire": "BIÊN BẢN NGỪNG QUẢN LÝ THIẾT BỊ",
    "lost": "BIÊN BẢN GHI NHẬN MẤT THIẾT BỊ",
    "adjust": "BIÊN BẢN ĐIỀU CHỈNH SAU KIỂM KÊ",
    "reversal": "BIÊN BẢN ĐẢO PHIẾU THIẾT BỊ",
}


class TpEquipmentMove(models.Model):
    _name = "tp.equipment.move"
    _description = "Phiếu bàn giao / thu hồi thiết bị"
    _inherit = ["tp.equipment.secure.mixin"]
    _order = "date desc, id desc"
    _rec_name = "name"

    name = fields.Char("Số phiếu", readonly=True, copy=False, default="/", index=True)
    move_type = fields.Selection(MOVE_TYPES, "Loại phiếu", required=True, default="assign", tracking=True)
    # What the admin picks on screen: only document types a person may create.
    request_type = fields.Selection(USER_TYPES, "Loại phiếu lập", compute="_compute_request_type",
                                    inverse="_inverse_request_type")
    state = fields.Selection(MOVE_STATES, "Trạng thái", default="draft", required=True, readonly=True, copy=False,
                             tracking=True, index=True)
    date = fields.Date("Ngày lập", default=fields.Date.context_today, required=True)
    date_done = fields.Datetime("Thời điểm hoàn tất", readonly=True, copy=False)
    done_by_id = fields.Many2one("res.users", "Người hoàn tất", readonly=True, copy=False)
    responsible_id = fields.Many2one("res.users", "Người lập phiếu", default=lambda self: self.env.uid,
                                     readonly=True, copy=False)
    company_id = fields.Many2one("res.company", "Công ty", default=lambda self: self.env.company, required=True)

    target_custody = fields.Selection(TARGET_CUSTODY, "Giao cho", default="employee")
    target_employee_id = fields.Many2one("hr.employee", "Nhân viên nhận", tracking=True, ondelete="restrict")
    target_employee_name = fields.Char("Snapshot nhân viên nhận", readonly=True, copy=False)
    target_employee_code = fields.Char("Snapshot mã nhân viên nhận", readonly=True, copy=False)
    target_employee_dept = fields.Char("Snapshot phòng ban nhân viên nhận", readonly=True, copy=False)
    target_employee_deleted = fields.Boolean("Nhân viên nhận đã xóa", readonly=True, copy=False)
    target_department_id = fields.Many2one("hr.department", "Phòng ban nhận", tracking=True, ondelete="restrict")
    target_location_id = fields.Many2one("tp.equipment.location", "Vị trí / kho", tracking=True, ondelete="restrict")
    target_partner_id = fields.Many2one("res.partner", "Đơn vị bên ngoài", tracking=True, ondelete="restrict",
                                        help="Đơn vị sửa chữa, bên cho thuê hoặc bên nhận thanh lý.")
    expected_return_date = fields.Date("Hẹn trả", tracking=True)
    retire_reason = fields.Selection(
        [r for r in RETIRE_REASON if r[0] in ("scrapped", "returned_owner", "other")], "Lý do ngừng quản lý")
    reason = fields.Text("Lý do / ghi chú")

    line_ids = fields.One2many("tp.equipment.move.line", "move_id", "Thiết bị", copy=True)
    line_count = fields.Integer("Số thiết bị", compute="_compute_line_count")
    preview_html = fields.Html("Xem trước", compute="_compute_preview_html", sanitize=False)
    has_blocking = fields.Boolean(compute="_compute_preview_html")

    idempotency_key = fields.Char("Khóa chống trùng", copy=False, readonly=True,
                                  default=lambda self: uuid.uuid4().hex)
    reversal_of_id = fields.Many2one("tp.equipment.move", "Đảo của phiếu", readonly=True, copy=False, index=True)
    reversed_by_id = fields.Many2one("tp.equipment.move", "Đã đảo bởi phiếu", readonly=True, copy=False)
    reversal_reason = fields.Text("Lý do đảo phiếu", readonly=True, copy=False)
    maintenance_request_id = fields.Many2one("maintenance.request", "Phiếu sửa chữa", ondelete="restrict",
                                             copy=False, index="btree_not_null",
                                             domain=[("tp_state", "in", ("new", "in_progress", "vendor"))])
    proposal_line_id = fields.Many2one("tp.equipment.proposal.line", "Dòng đề xuất", ondelete="set null",
                                       copy=False, index="btree_not_null", readonly=True)
    inventory_id = fields.Many2one("tp.equipment.inventory", "Kỳ kiểm kê", ondelete="restrict", copy=False,
                                   index="btree_not_null", readonly=True)

    # EQUIP-SIMPLE-003: Gán / Đổi máy / Trả về kho legs of one confirmation share one request key.
    tp_request_key = fields.Char("Mã yêu cầu thao tác nhanh", readonly=True, copy=False, index="btree_not_null")
    tp_request_hash = fields.Char("Dấu nội dung yêu cầu", readonly=True, copy=False)

    _idempotency_unique = models.UniqueIndex("(idempotency_key) WHERE idempotency_key IS NOT NULL",
                                             "Phiếu này đã được tạo (trùng khóa chống trùng).")

    # ------------------------------------------------------------------ computes
    @api.depends("move_type")
    def _compute_request_type(self):
        for move in self:
            move.request_type = move.move_type if move.move_type not in SYSTEM_TYPES else False

    def _inverse_request_type(self):
        for move in self:
            if move.request_type and move.request_type != move.move_type and move.state == "draft":
                move.move_type = move.request_type

    @api.onchange("request_type")
    def _onchange_request_type(self):
        if self.request_type:
            self.move_type = self.request_type

    @api.depends("line_ids")
    def _compute_line_count(self):
        for move in self:
            move.line_count = len(move.line_ids)

    @api.depends("move_type", "state", "target_custody", "target_employee_id", "target_department_id",
                 "target_location_id", "target_partner_id", "expected_return_date", "retire_reason", "reason",
                 "line_ids.equipment_id", "line_ids.condition")
    def _compute_preview_html(self):
        for move in self:
            if move.state in ("done", "cancel") or move.move_type in SYSTEM_TYPES:
                move.preview_html = False
                move.has_blocking = False
                continue
            issues = move._tp_check(strict=False)
            move.has_blocking = any(level == "error" for level, _line, _msg in issues)
            move.preview_html = move._tp_preview_markup(issues)

    # ------------------------------------------------------------------ helpers
    def _tp_custody_label(self, custody):
        return dict(CUSTODY).get(custody, custody or "")

    def _tp_holder_text(self, custody, employee, department, location, partner,
                        employee_name=None, employee_code=None, employee_dept=None, is_deleted=False):
        if custody in ("employee", "loan"):
            if employee:
                text = employee.name
                if employee.department_id:
                    text += f" ({employee.department_id.name})"
                return text
            if employee_name:
                text = employee_name
                if employee_dept:
                    text += f" ({employee_dept})"
                if is_deleted:
                    text += " (Nhân viên đã xóa)"
                return text
        if custody == "department" and department:
            return department.display_name
        if custody == "location" and location:
            return location.display_name
        if custody == "vendor":
            return partner.display_name if partner else _("Đơn vị bên ngoài")
        if custody == "stock":
            return _("Kho thiết bị") + (f" – {location.display_name}" if location else "")
        return self._tp_custody_label(custody)

    def _tp_target_custody(self):
        self.ensure_one()
        if self.move_type in ("assign", "transfer"):
            return self.target_custody or "employee"
        return {
            "return": "stock", "loan": "loan", "loan_return": "stock", "send_repair": "vendor",
            "repair_return": "stock", "rental_return": "none", "retire": "none", "lost": "none",
        }.get(self.move_type)

    def _tp_target_values(self, line):
        """Equipment values after this move for one line (header target, or line target for system moves)."""
        self.ensure_one()
        if self.move_type == "opening":
            return {}
        if self.move_type in ("reversal", "adjust"):
            vals = {
                "tp_custody": line.to_custody,
                "tp_employee_id": line.to_employee_id.id,
                "tp_holder_department_id": line.to_department_id.id,
                "tp_location_id": line.to_location_id.id,
                "tp_vendor_id": line.to_partner_id.id,
                "tp_lifecycle": line.to_lifecycle or "active",
                "tp_retire_reason": line.to_retire_reason or False,
                "tp_retire_date": line.to_retire_date or False,
            }
            if line.condition:
                vals["tp_technical_state"] = line.condition
            return vals
        custody = self._tp_target_custody()
        vals = {
            "tp_custody": custody,
            "tp_employee_id": False,
            "tp_holder_department_id": False,
            "tp_location_id": False,
            "tp_vendor_id": False,
        }
        if custody in ("employee", "loan"):
            vals["tp_employee_id"] = self.target_employee_id.id
            vals["tp_location_id"] = self.target_location_id.id if custody == "employee" else False
        elif custody == "department":
            vals["tp_holder_department_id"] = self.target_department_id.id
            vals["tp_location_id"] = self.target_location_id.id
        elif custody in ("location", "stock"):
            vals["tp_location_id"] = self.target_location_id.id
        elif custody == "vendor":
            vals["tp_vendor_id"] = self.target_partner_id.id
        elif custody == "none":
            reason = {"rental_return": "rental_returned", "lost": "lost"}.get(self.move_type, self.retire_reason)
            vals.update({
                "tp_lifecycle": "retired",
                "tp_retire_reason": reason,
                "tp_retire_date": fields.Date.context_today(self),
                "tp_retire_note": self.reason or False,
            })
        if line.condition:
            vals["tp_technical_state"] = line.condition
        return vals

    def _tp_check(self, strict=True):
        """Return [(level, line, message)]; level is 'error' or 'warning'. Errors block confirm / done."""
        self.ensure_one()
        issues = []
        move_type = self.move_type

        def err(message, line=None):
            issues.append(("error", line, message))

        def warn(message, line=None):
            issues.append(("warning", line, message))

        lines = self.line_ids.filtered("equipment_id")
        if not lines:
            err(_("Chọn ít nhất một thiết bị."))
        seen = set()
        for line in lines:
            if line.equipment_id.id in seen:
                err(_("Thiết bị %(name)s bị chọn hai lần.", name=line.equipment_id.display_name), line)
            seen.add(line.equipment_id.id)

        if move_type in ("assign", "transfer"):
            custody = self.target_custody
            if not custody:
                err(_("Chọn hình thức giao: nhân viên, phòng ban hoặc vị trí."))
            elif custody == "employee" and not self.target_employee_id:
                err(_("Chọn nhân viên nhận."))
            elif custody == "department" and not self.target_department_id:
                err(_("Chọn phòng ban nhận."))
            elif custody == "location" and not self.target_location_id:
                err(_("Chọn vị trí đặt thiết bị."))
        if move_type == "loan":
            if not self.target_employee_id:
                err(_("Chọn nhân viên mượn."))
            if not self.expected_return_date:
                err(_("Nhập ngày hẹn trả."))
            elif self.expected_return_date < self.date:
                err(_("Ngày hẹn trả phải sau ngày lập phiếu."))
        if self._tp_target_custody() in ("employee", "loan") and self.target_employee_id:
            employee = self.target_employee_id.sudo()
            if not employee.active:
                err(_("Nhân viên %(name)s đã nghỉ / lưu trữ hồ sơ, không nhận thiết bị được.", name=employee.name))
            elif employee.departure_date:
                warn(_("Nhân viên %(name)s có ngày nghỉ việc %(date)s.", name=employee.name,
                       date=employee.departure_date.strftime("%d/%m/%Y")))
        if move_type == "send_repair" and not self.target_partner_id:
            err(_("Chọn đơn vị sửa chữa."))
        if move_type == "retire":
            if not self.retire_reason:
                err(_("Chọn lý do ngừng quản lý."))
            if not (self.reason or "").strip():
                err(_("Ghi rõ lý do / căn cứ ngừng quản lý."))
        if move_type == "lost" and not (self.reason or "").strip():
            err(_("Ghi rõ hoàn cảnh mất thiết bị."))
        request = self.maintenance_request_id
        if request:
            if move_type not in ("send_repair", "repair_return"):
                err(_("Phiếu sửa chữa chỉ gắn với phiếu gửi sửa ngoài / nhận về sau sửa."))
            elif request.tp_state not in ("new", "in_progress", "vendor"):
                err(_("Phiếu sửa chữa %(name)s đã kết thúc.", name=request.tp_code or request.name))
            if request.equipment_id and request.equipment_id not in lines.equipment_id:
                err(_("Phiếu phải có thiết bị %(name)s của phiếu sửa chữa.", name=request.equipment_id.display_name))

        proposal_line = self.proposal_line_id
        if proposal_line and move_type != "reversal" and self.state in ("draft", "pending"):
            if strict:
                lock_records(proposal_line.proposal_id)
                proposal_line._tp_lock()
            if proposal_line.kind not in ("transfer", "dispose") or not proposal_line._tp_is_executable():
                err(_("Dòng đề xuất chưa đủ điều kiện thực hiện phiếu bàn giao / ngừng quản lý."))
            expected_type = "retire" if proposal_line.kind == "dispose" else ("assign", "transfer")
            if (move_type != expected_type if isinstance(expected_type, str) else move_type not in expected_type):
                err(_("Loại phiếu không khớp phương án của đề xuất."))
            if lines.equipment_id != proposal_line.equipment_id:
                err(_("Phiếu phải có đúng thiết bị đã xác minh trên dòng đề xuất."))
            other_moves = proposal_line.move_ids.filtered(lambda m: m != self and m.state in ("pending", "done")
                                                          and not m.reversed_by_id)
            if other_moves:
                err(_("Dòng đề xuất đã có phiếu đang chờ hoặc đã hoàn tất."))

        if move_type not in SYSTEM_TYPES:
            pending = self.env["tp.equipment.move.line"].search([
                ("equipment_id", "in", lines.equipment_id.ids), ("state", "=", "pending"),
                ("move_id", "not in", self.ids),
            ])
            pending_map = {pl.equipment_id.id: pl.move_id for pl in pending}
            to_custody = self._tp_target_custody()
            for line in lines:
                equipment = line.equipment_id
                label = equipment.display_name
                if equipment.tp_lifecycle == "draft":
                    err(_("%(name)s chưa đăng ký vào kho.", name=label), line)
                    continue
                if equipment.tp_lifecycle == "retired":
                    err(_("%(name)s đã ngừng quản lý.", name=label), line)
                    continue
                if move_type in ("assign", "loan") and equipment.tp_custody == "stock" and equipment.tp_employee_id:
                    # CHG-20261116-002: never hand over a row that says stock but still names a holder.
                    err(_("%(name)s ghi Trong kho nhưng vẫn còn người giữ: cần làm sạch dữ liệu trước khi bàn giao.",
                          name=label), line)
                allowed = ALLOWED_FROM.get(move_type, ())
                if equipment.tp_custody not in allowed:
                    err(_("%(name)s đang ở “%(custody)s”, không dùng loại phiếu này.", name=label,
                          custody=self._tp_custody_label(equipment.tp_custody)), line)
                if equipment.id in pending_map:
                    err(_("%(name)s đang chờ bàn giao ở phiếu %(move)s.", name=label,
                          move=pending_map[equipment.id].name), line)
                if to_custody in ("employee", "loan", "department", "location"):
                    if equipment.maintenance_ids.filtered(lambda r: r.tp_state in ("new", "in_progress", "vendor")):
                        err(_("%(name)s còn phiếu sửa chữa chưa kết thúc, chưa thể bàn giao sử dụng.", name=label), line)
                    state = line.condition or equipment.tp_technical_state
                    if state == "broken":
                        err(_("%(name)s đang hỏng, không bàn giao để sử dụng được.", name=label), line)
                    elif state == "unverified" or equipment.tp_verification == "source":
                        warn(_("%(name)s chưa kiểm tra thực tế: kiểm tra trước khi giao.", name=label), line)
                if move_type == "transfer" and equipment.tp_custody == to_custody:
                    same = (
                        (to_custody == "employee" and equipment.tp_employee_id == self.target_employee_id)
                        or (to_custody == "department"
                            and equipment.tp_holder_department_id == self.target_department_id)
                        or (to_custody == "location" and equipment.tp_location_id == self.target_location_id)
                    )
                    if same:
                        err(_("%(name)s đã ở đúng nơi nhận.", name=label), line)
                if move_type == "rental_return" and equipment.tp_ownership != "rented":
                    err(_("%(name)s không phải thiết bị thuê.", name=label), line)
                if move_type == "retire" and self.retire_reason == "scrapped" and equipment.tp_ownership != "company":
                    err(_("%(name)s không thuộc công ty; không thanh lý như tài sản công ty.", name=label), line)
                if move_type in ("retire", "rental_return") and equipment.maintenance_ids.filtered(
                        lambda r: r.tp_state in ("new", "in_progress", "vendor")):
                    err(_("%(name)s còn phiếu sửa chữa chưa kết thúc.", name=label), line)
                if equipment.tp_parent_id and equipment.tp_parent_id not in lines.equipment_id:
                    warn(_("%(name)s đang gắn vào %(parent)s; kiểm tra lại bộ máy.", name=label,
                           parent=equipment.tp_parent_id.display_name), line)
                if equipment.tp_employee_archived and move_type in ("return", "transfer", "lost"):
                    warn(_("%(name)s: người giữ đã nghỉ / lưu trữ hồ sơ.", name=label), line)
        if strict and any(level == "error" for level, _l, _m in issues):
            raise UserError("\n".join(message for level, _l, message in issues if level == "error"))
        return issues

    def _tp_preview_markup(self, issues):
        self.ensure_one()
        rows = []
        to_custody = self._tp_target_custody()
        for line in self.line_ids.filtered("equipment_id"):
            equipment = line.equipment_id
            before = self._tp_holder_text(equipment.tp_custody, equipment.tp_employee_id,
                                          equipment.tp_holder_department_id, equipment.tp_location_id,
                                          equipment.tp_vendor_id)
            if to_custody == "none":
                after = _("Ngừng quản lý")
            else:
                after = self._tp_holder_text(to_custody, self.target_employee_id, self.target_department_id,
                                             self.target_location_id, self.target_partner_id)
            line_issues = [(level, msg) for level, line, msg in issues if line and line.id == line.id]
            notes = Markup("").join(
                Markup('<div class="o_tp_eq_issue o_tp_eq_issue_%s">%s</div>') % (level, msg)
                for level, msg in line_issues)
            rows.append(Markup(
                "<tr><td><strong>%s</strong><div class='text-muted small'>%s</div></td>"
                "<td>%s</td><td aria-hidden='true'>→</td><td>%s</td><td>%s</td></tr>",
            ) % (equipment.tp_code or "", equipment.name or "", before, after, notes))
        general = [(level, msg) for level, line, msg in issues if not line]
        head = Markup("").join(
            Markup('<div class="o_tp_eq_issue o_tp_eq_issue_%s">%s</div>') % (level, msg) for level, msg in general)
        if not rows:
            return head or False
        errors = sum(1 for level, _l, _m in issues if level == "error")
        summary = (_("Còn %s lỗi cần xử lý trước khi xác nhận.", errors) if errors
                   else _("Kiểm tra xong: có thể xác nhận phiếu."))
        return Markup(
            "<div class='o_tp_eq_preview'>%s<p class='o_tp_eq_preview_summary'>%s</p>"
            "<div class='table-responsive'><table class='table table-sm o_tp_eq_preview_table'>"
            "<thead><tr><th>Thiết bị</th><th>Hiện tại</th><th><span class='visually-hidden'>chuyển sang</span></th>"
            "<th>Sau khi hoàn tất</th><th>Lưu ý</th></tr></thead><tbody>%s</tbody></table></div></div>",
        ) % (head, summary, Markup("").join(rows))

    def _tp_lock_equipment(self, equipments):
        if not equipments:
            return
        try:
            with self.env.cr.savepoint(flush=False):
                self.env.cr.execute(SQL("SELECT id FROM maintenance_equipment WHERE id IN %s FOR UPDATE NOWAIT",
                                        tuple(equipments.ids)))
        except pg_errors.LockNotAvailable:
            raise UserError(_("Thiết bị đang được xử lý ở thao tác khác. Thử lại sau ít giây.")) from None
        equipments.invalidate_recordset()

    def _tp_snapshot_from(self):
        for line in self.line_ids:
            equipment = line.equipment_id
            line.with_context(tp_equipment_move_internal=INTERNAL).write({
                "from_custody": equipment.tp_custody,
                "from_employee_id": equipment.tp_employee_id.id,
                "from_department_id": equipment.tp_holder_department_id.id,
                "from_location_id": equipment.tp_location_id.id,
                "from_partner_id": equipment.tp_vendor_id.id,
                "from_lifecycle": equipment.tp_lifecycle,
                "from_retire_reason": equipment.tp_retire_reason or False,
                "from_retire_date": equipment.tp_retire_date or False,
                "from_technical_state": equipment.tp_technical_state,
                "expected_version": equipment.tp_version,
            })

    # ------------------------------------------------------------------ ORM
    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        existing = self.browse()
        to_create = []
        for vals in vals_list:
            if self.env.context.get("tp_equipment_move_internal") is not INTERNAL:
                for field in ('done_by_id', 'date_done', 'reversal_of_id', 'reversed_by_id', 'inventory_id',
                              'tp_request_key', 'tp_request_hash'):
                    vals.pop(field, None)
            key = vals.get("idempotency_key")
            found = key and self.search([("idempotency_key", "=", key)], limit=1)
            if found:
                existing |= found
                continue
            if vals.get("move_type") in SYSTEM_TYPES and self.env.context.get("tp_equipment_move_internal") is not INTERNAL:
                raise UserError(_("Loại phiếu này do hệ thống tạo (đăng ký, kiểm kê, đảo phiếu)."))
            if vals.get("state", "draft") != "draft" and self.env.context.get("tp_equipment_move_internal") is not INTERNAL:
                vals["state"] = "draft"
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = self.env["ir.sequence"].sudo().next_by_code("tp.equipment.move") or "/"
            to_create.append(vals)
        return existing | super().create(to_create) if to_create else existing

    def write(self, vals):
        check_admin(self.env)
        lock_records(self)
        if self.env.context.get("tp_equipment_move_internal") is not INTERNAL:
            if {"state", "done_by_id", "date_done", "reversal_of_id", "reversed_by_id", "inventory_id",
                    "tp_request_key", "tp_request_hash"} & set(vals):
                raise UserError(_("Dùng các nút xử lý phiếu để thay đổi trạng thái và lịch sử."))
            free = {"reason", "expected_return_date", "message_main_attachment_id"}
            for move in self:
                if move.state in ("done", "cancel") and set(vals) - {"message_main_attachment_id"}:
                    raise UserError(_("Phiếu %(name)s đã %(state)s, không sửa được. Dùng Đảo phiếu nếu cần sửa sai.",
                                      name=move.name, state=dict(MOVE_STATES)[move.state].lower()))
                if move.state == "pending" and set(vals) - free:
                    raise UserError(_("Phiếu %(name)s đang chờ bàn giao: đưa về nháp để sửa thiết bị hoặc bên nhận.",
                                      name=move.name))
                if "move_type" in vals and vals["move_type"] in SYSTEM_TYPES:
                    raise UserError(_("Loại phiếu này do hệ thống tạo."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_draft(self):
        check_admin(self.env)
        for move in self:
            if move.state != "draft":
                raise UserError(_("Chỉ xóa được phiếu nháp. Phiếu %(name)s giữ lại để đối chiếu lịch sử.", name=move.name))

    # ------------------------------------------------------------------ actions
    def action_confirm(self):
        check_admin(self.env)
        lock_records(self)
        for move in self:
            if move.state != "draft":
                continue
            move._tp_lock_equipment(move.line_ids.equipment_id)
            move._tp_check(strict=True)
            move._tp_snapshot_from()
            move.with_context(tp_equipment_move_internal=INTERNAL).write({"state": "pending"})
            self.env.flush_all()
        return True

    def action_back_to_draft(self):
        check_admin(self.env)
        lock_records(self)
        for move in self.filtered(lambda m: m.state == "pending"):
            move.with_context(tp_equipment_move_internal=INTERNAL).write({"state": "draft"})
        return True

    def action_cancel(self):
        check_admin(self.env)
        lock_records(self)
        for move in self:
            if move.state == "done":
                raise UserError(_("Phiếu đã hoàn tất không hủy được; dùng Đảo phiếu."))
            if move.state in ("draft", "pending"):
                move.with_context(tp_equipment_move_internal=INTERNAL).write({"state": "cancel"})
        return True

    def action_done(self):
        check_admin(self.env)
        lock_records(self)
        for move in self:
            if move.state == "done":
                continue  # idempotent replay
            if move.state == "cancel":
                raise UserError(_("Phiếu %(name)s đã hủy.", name=move.name))
            equipments = move.line_ids.equipment_id
            move._tp_lock_equipment(equipments)
            if move.state == "draft":
                if move.move_type not in SYSTEM_TYPES:
                    move._tp_check(strict=True)
                if move.move_type != "opening":
                    move._tp_snapshot_from()
            else:
                if move.move_type not in SYSTEM_TYPES:
                    move._tp_check(strict=True)
                changed = move.line_ids.filtered(lambda line: line.equipment_id.tp_version != line.expected_version)
                if changed:
                    raise UserError(_(
                        "%(names)s đã thay đổi sau khi xác nhận phiếu. Đưa phiếu về nháp, kiểm tra lại rồi xác nhận.",
                        names=", ".join(changed.equipment_id.mapped("display_name"))))
            for line in move.line_ids:
                equipment = line.equipment_id
                vals = move._tp_target_values(line)
                if vals:
                    equipment.with_context(tp_equipment_move=INTERNAL).write(vals)
                line.with_context(tp_equipment_move_internal=INTERNAL).write({
                    "to_custody": equipment.tp_custody,
                    "to_employee_id": equipment.tp_employee_id.id,
                    "to_department_id": equipment.tp_holder_department_id.id,
                    "to_location_id": equipment.tp_location_id.id,
                    "to_partner_id": equipment.tp_vendor_id.id,
                    "to_lifecycle": equipment.tp_lifecycle,
                    "to_retire_reason": equipment.tp_retire_reason or False,
                    "to_retire_date": equipment.tp_retire_date or False,
                    "done_version": equipment.tp_version,
                })
                if move.move_type != "opening":
                    equipment.message_post(
                        body=Markup("%s: <a href='/app/thiet-bi/phieu-ban-giao/%s'>%s</a>") % (
                            dict(MOVE_TYPES)[move.move_type], move.id, move.name),
                        subtype_xmlid="mail.mt_note")
            move.with_context(tp_equipment_move_internal=INTERNAL).write({
                "state": "done", "date_done": fields.Datetime.now(), "done_by_id": self.env.uid,
            })
            if move.maintenance_request_id:
                move.maintenance_request_id._tp_on_move_done(move)
            if move.proposal_line_id:
                move.proposal_line_id._tp_refresh_progress()
        self.env.flush_all()
        return True

    def action_open_reverse(self):
        check_admin(self.env)
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Đảo phiếu %s", self.name),
            "res_model": "tp.equipment.move.reverse",
            "view_mode": "form",
            "target": "new",
            "context": {"default_move_id": self.id},
        }

    def _tp_reverse(self, reason):
        check_admin(self.env)
        self.ensure_one()
        lock_records(self)
        reason = (reason or "").strip()
        if not reason:
            raise UserError(_("Ghi lý do đảo phiếu."))
        if self.state != "done":
            raise UserError(_("Chỉ đảo được phiếu đã hoàn tất."))
        if self.reversed_by_id:
            raise UserError(_("Phiếu %(name)s đã được đảo bởi %(other)s.", name=self.name, other=self.reversed_by_id.name))
        if self.move_type in ("opening", "reversal"):
            raise UserError(_("Không đảo phiếu ghi nhận ban đầu hoặc phiếu đảo. Lập phiếu mới nếu cần."))
        self._tp_lock_equipment(self.line_ids.equipment_id)
        changed = self.line_ids.filtered(lambda line: line.equipment_id.tp_version != line.done_version)
        if changed:
            raise UserError(_(
                "%(names)s đã có thay đổi sau phiếu này. Đảo các phiếu mới hơn trước hoặc lập phiếu mới.",
                names=", ".join(changed.equipment_id.mapped("display_name"))))
        reversal = self.with_context(tp_equipment_move_internal=INTERNAL).create({
            "move_type": "reversal",
            "date": fields.Date.context_today(self),
            "reversal_of_id": self.id,
            "reason": reason,
            "maintenance_request_id": self.maintenance_request_id.id,
            "line_ids": [(0, 0, {
                "equipment_id": line.equipment_id.id,
                "to_custody": line.from_custody,
                "to_employee_id": line.from_employee_id.id,
                "to_department_id": line.from_department_id.id,
                "to_location_id": line.from_location_id.id,
                "to_partner_id": line.from_partner_id.id,
                "to_lifecycle": line.from_lifecycle,
                "to_retire_reason": line.from_retire_reason,
                "to_retire_date": line.from_retire_date,
                "condition": line.from_technical_state if line.condition else False,
                "note": _("Đảo dòng của phiếu %s", self.name),
            }) for line in self.line_ids],
        })
        reversal.with_context(tp_equipment_move_internal=INTERNAL).action_done()
        self.with_context(tp_equipment_move_internal=INTERNAL).write({
            "reversed_by_id": reversal.id, "reversal_reason": reason,
        })
        if self.proposal_line_id:
            self.proposal_line_id._tp_refresh_progress()
        self.message_post(body=_("Đã đảo bởi phiếu %(name)s. Lý do: %(reason)s", name=reversal.name, reason=reason),
                          subtype_xmlid="mail.mt_note")
        return {
            "type": "ir.actions.act_window",
            "res_model": "tp.equipment.move",
            "res_id": reversal.id,
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "current",
        }

    def action_print_handover(self):
        check_admin(self.env)
        self.ensure_one()
        if self.state not in ("pending", "done"):
            raise UserError(_("Xác nhận phiếu trước khi in biên bản."))
        return {"type": "ir.actions.act_url", "url": f"/tp_equipment/move/{self.id}/handover.pdf", "target": "new"}

    @api.model
    def _tp_create_opening(self, equipments):
        """Opening record created when equipment is registered: documents the initial holder."""
        for equipment in equipments:
            # Imported records: the opening documents the source snapshot, not a real handover.
            from_source = equipment.tp_verification == "source" and bool(
                self.env["tp.equipment.import.line"].search_count([("equipment_id", "=", equipment.id)], limit=1))
            move = self.with_context(tp_equipment_move_internal=INTERNAL).create({
                "move_type": "opening",
                "date": fields.Date.context_today(self),
                "reason": _("Ghi nhận ban đầu từ Excel, chưa đối chiếu bàn giao thực tế. Ngày phiếu là ngày ghi hệ thống.")
                if from_source else _("Ghi nhận nơi giữ ban đầu khi đăng ký vào kho."),
                "line_ids": [(0, 0, {
                    "equipment_id": equipment.id,
                    "to_custody": equipment.tp_custody,
                    "to_employee_id": equipment.tp_employee_id.id,
                    "to_department_id": equipment.tp_holder_department_id.id,
                    "to_location_id": equipment.tp_location_id.id,
                    "to_partner_id": equipment.tp_vendor_id.id,
                    "to_lifecycle": equipment.tp_lifecycle,
                })],
            })
            move.with_context(tp_equipment_move_internal=INTERNAL).action_done()
        return True


class TpEquipmentMoveLine(models.Model):
    _name = "tp.equipment.move.line"
    _description = "Dòng phiếu bàn giao thiết bị"
    _order = "move_id desc, id"

    move_id = fields.Many2one("tp.equipment.move", "Phiếu", required=True, ondelete="cascade", index=True)
    move_type = fields.Selection(related="move_id.move_type", store=True, string="Loại phiếu")
    state = fields.Selection(related="move_id.state", store=True, string="Trạng thái", index=True)
    date = fields.Date(related="move_id.date", store=True, string="Ngày lập")
    date_done = fields.Datetime(related="move_id.date_done", store=True, string="Hoàn tất lúc")
    equipment_id = fields.Many2one("maintenance.equipment", "Thiết bị", required=True, ondelete="restrict", index=True,
                                   domain=[("tp_lifecycle", "=", "active")])
    equipment_code = fields.Char(related="equipment_id.tp_code", string="Mã thiết bị")
    condition = fields.Selection([s for s in TECH_STATE if s[0] != "unverified"], "Tình trạng ghi nhận",
                                 help="Tình trạng kiểm tra lúc giao / nhận. Để trống nếu không kiểm tra lại.")
    accessories = fields.Char("Phụ kiện kèm theo")
    note = fields.Char("Ghi chú")

    from_custody = fields.Selection(CUSTODY, "Nơi giữ trước", readonly=True)
    from_employee_id = fields.Many2one("hr.employee", "Người giữ trước", readonly=True, ondelete="restrict")
    from_employee_name = fields.Char("Snapshot người giữ trước", readonly=True, copy=False)
    from_employee_code = fields.Char("Snapshot mã người giữ trước", readonly=True, copy=False)
    from_employee_dept = fields.Char("Snapshot phòng ban trước", readonly=True, copy=False)
    from_employee_deleted = fields.Boolean("Người giữ trước đã xóa", readonly=True, copy=False)
    from_department_id = fields.Many2one("hr.department", "Phòng ban trước", readonly=True, ondelete="restrict")
    from_location_id = fields.Many2one("tp.equipment.location", "Vị trí trước", readonly=True, ondelete="restrict")
    from_partner_id = fields.Many2one("res.partner", "Đơn vị ngoài trước", readonly=True, ondelete="restrict")
    from_lifecycle = fields.Selection(LIFECYCLE, "Vòng đời trước", readonly=True)
    from_retire_reason = fields.Selection(RETIRE_REASON, readonly=True)
    from_retire_date = fields.Date(readonly=True)
    from_technical_state = fields.Selection(TECH_STATE, "Tình trạng trước", readonly=True)
    to_custody = fields.Selection(CUSTODY, "Nơi giữ sau", readonly=True)
    to_employee_id = fields.Many2one("hr.employee", "Người giữ sau", readonly=True, ondelete="restrict")
    to_employee_name = fields.Char("Snapshot người giữ sau", readonly=True, copy=False)
    to_employee_code = fields.Char("Snapshot mã người giữ sau", readonly=True, copy=False)
    to_employee_dept = fields.Char("Snapshot phòng ban sau", readonly=True, copy=False)
    to_employee_deleted = fields.Boolean("Người giữ sau đã xóa", readonly=True, copy=False)
    to_department_id = fields.Many2one("hr.department", "Phòng ban sau", readonly=True, ondelete="restrict")
    to_location_id = fields.Many2one("tp.equipment.location", "Vị trí sau", readonly=True, ondelete="restrict")
    to_partner_id = fields.Many2one("res.partner", "Đơn vị ngoài sau", readonly=True, ondelete="restrict")
    to_lifecycle = fields.Selection(LIFECYCLE, "Vòng đời sau", readonly=True)
    to_retire_reason = fields.Selection(RETIRE_REASON, readonly=True)
    to_retire_date = fields.Date(readonly=True)
    expected_version = fields.Integer("Phiên bản khi xác nhận", readonly=True)
    done_version = fields.Integer("Phiên bản sau hoàn tất", readonly=True)
    from_text = fields.Char("Từ", compute="_compute_texts")
    to_text = fields.Char("Đến", compute="_compute_texts")

    _pending_unique = models.UniqueIndex("(equipment_id) WHERE state = 'pending'",
                                         "Thiết bị đang chờ bàn giao ở một phiếu khác.")

    def _compute_texts(self):
        Move = self.env["tp.equipment.move"]
        for line in self:
            line.from_text = Move._tp_holder_text(
                line.from_custody, line.from_employee_id, line.from_department_id,
                line.from_location_id, line.from_partner_id,
                employee_name=line.from_employee_name, employee_code=line.from_employee_code,
                employee_dept=line.from_employee_dept, is_deleted=line.from_employee_deleted,
            ) if line.from_custody else False
            if line.to_lifecycle == "retired":
                line.to_text = _("Ngừng quản lý (%s)", dict(RETIRE_REASON).get(line.to_retire_reason, ""))
            else:
                line.to_text = Move._tp_holder_text(
                    line.to_custody, line.to_employee_id, line.to_department_id,
                    line.to_location_id, line.to_partner_id,
                    employee_name=line.to_employee_name, employee_code=line.to_employee_code,
                    employee_dept=line.to_employee_dept, is_deleted=line.to_employee_deleted,
                ) if line.to_custody else False

    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        if self.env.context.get("tp_equipment_move_internal") is not INTERNAL:
            for values in vals_list:
                for key in list(values):
                    if key.startswith(('from_', 'to_')) or key in ('expected_version', 'done_version'):
                        values.pop(key)
            moves = self.env["tp.equipment.move"].browse({v.get("move_id") for v in vals_list if v.get("move_id")})
            lock_records(moves)
            if moves.filtered(lambda m: m.state != "draft"):
                raise UserError(_("Chỉ thêm thiết bị vào phiếu nháp."))
        return super().create(vals_list)

    def write(self, vals):
        check_admin(self.env)
        lock_records(self.move_id)
        if self.env.context.get("tp_equipment_move_internal") is not INTERNAL and "move_id" in vals:
            raise UserError(_('Không chuyển dòng sang phiếu khác.'))
        if self.env.context.get("tp_equipment_move_internal") is not INTERNAL and\
                self.filtered(lambda line: line.move_id.state != "draft"):
            raise UserError(_("Chỉ sửa thiết bị trên phiếu nháp."))
        if self.env.context.get("tp_equipment_move_internal") is not INTERNAL and any(
                key.startswith(('from_', 'to_')) or key in ('expected_version', 'done_version') for key in vals):
            raise UserError(_('Snapshot bàn giao do hệ thống ghi nhận khi xác nhận phiếu.'))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_draft(self):
        lock_records(self.move_id)
        if self.filtered(lambda line: line.move_id.state != "draft"):
            raise UserError(_("Chỉ bỏ thiết bị khỏi phiếu nháp."))


class TpEquipmentMoveReverse(models.TransientModel):
    _name = "tp.equipment.move.reverse"
    _description = "Đảo phiếu thiết bị"

    move_id = fields.Many2one("tp.equipment.move", "Phiếu cần đảo", required=True, readonly=True)
    reason = fields.Text("Lý do đảo phiếu", required=True)

    def action_confirm(self):
        check_admin(self.env)
        self.ensure_one()
        return self.move_id._tp_reverse(self.reason)
