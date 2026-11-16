"""Báo hỏng / bảo trì / sửa chữa / nâng cấp (EQUIP-001 part 3) on native ``maintenance.request``.

* The admin records a request on behalf of an employee: the reporter and the real technician are
  business information (employee / text / partner), never native assignees or followers.
* ``tp_state`` is the module's progress; native ``state`` / ``stage_id`` are kept in sync so the native
  Maintenance app (admin-only) stays consistent.
* Closing needs an explicit result and technical state; nothing turns "Tốt" by itself. The equipment
  stays unavailable while a request is in progress or at the vendor.
* Upgrades store the configuration before (snapshot at creation) and after; applying it writes the
  equipment record with an audit note.
"""
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import SQL

from .common import INTERNAL, TECH_STATE, check_admin

TP_REQUEST_KIND = [
    ("fault", "Báo hỏng / sự cố"),
    ("maintenance", "Bảo trì định kỳ"),
    ("upgrade", "Nâng cấp / thay linh kiện"),
    ("warranty", "Bảo hành (gửi hãng)"),
]
TP_REQUEST_STATE = [
    ("new", "Mới ghi nhận"),
    ("in_progress", "Đang xử lý"),
    ("vendor", "Đang ở bên sửa ngoài"),
    ("done", "Đã có kết quả"),
    ("cancel", "Đã hủy"),
]
TP_OPEN_STATES = ("new", "in_progress", "vendor")
TP_RESULT = [
    ("fixed", "Đã khắc phục"),
    ("limited", "Khắc phục một phần"),
    ("not_fixed", "Không khắc phục được"),
    ("no_fault", "Không phát hiện lỗi"),
    ("upgraded", "Đã nâng cấp / thay xong"),
]
COST_KNOWN = [
    ("unknown", "Chưa biết chi phí"),
    ("known", "Đã biết chi phí"),
    ("free", "Không mất phí (bảo hành / nội bộ)"),
]
STATE_AFTER = [s for s in TECH_STATE if s[0] != "unverified"]
STAGE_BY_STATE = {
    "new": "maintenance.stage_0",
    "in_progress": "maintenance.stage_1",
    "vendor": "maintenance.stage_1",
    "done": "maintenance.stage_3",
}
CONFIG_FIELDS = (("tp_cpu", "CPU"), ("tp_ram", "RAM"), ("tp_storage", "Ổ lưu trữ"), ("tp_gpu", "Card đồ họa"))


class MaintenanceRequestTp(models.Model):
    _inherit = "maintenance.request"

    tp_code = fields.Char("Số phiếu", readonly=True, copy=False, index=True)
    tp_kind = fields.Selection(TP_REQUEST_KIND, "Loại yêu cầu", default="fault", required=True, tracking=True)
    tp_state = fields.Selection(TP_REQUEST_STATE, "Tiến trình", default="new", required=True, readonly=True,
                                copy=False, tracking=True, index=True)
    tp_reporter_employee_id = fields.Many2one(
        "hr.employee", "Người báo / yêu cầu", ondelete="restrict", tracking=True, context={"active_test": False},
        help="Thông tin nghiệp vụ: người báo lỗi không được mở Kho thiết bị.")
    tp_report_date = fields.Date("Ngày báo", default=fields.Date.context_today, required=True)
    tp_symptom = fields.Text("Hiện tượng / nội dung yêu cầu")
    tp_technician_text = fields.Char(
        "Người / đơn vị thực hiện", tracking=True,
        help="Kỹ thuật viên thực tế (nội bộ hoặc bên ngoài). Chỉ là thông tin, không cấp quyền hay theo dõi phiếu.")
    tp_vendor_id = fields.Many2one("res.partner", "Đơn vị sửa chữa / hãng", ondelete="restrict", tracking=True)
    tp_deadline = fields.Date("Hạn xử lý", tracking=True)
    tp_overdue = fields.Boolean("Quá hạn", compute="_compute_tp_overdue", search="_search_tp_overdue")
    tp_diagnosis = fields.Text("Chẩn đoán / nguyên nhân")
    tp_work_done = fields.Text("Công việc đã làm")
    tp_parts = fields.Text("Linh kiện thay / bổ sung")

    tp_config_before = fields.Text("Cấu hình trước", readonly=True, copy=False)
    tp_cpu_after = fields.Char("CPU sau")
    tp_ram_after = fields.Char("RAM sau")
    tp_storage_after = fields.Char("Ổ lưu trữ sau")
    tp_gpu_after = fields.Char("Card đồ họa sau")
    tp_apply_config = fields.Boolean("Cập nhật cấu hình thiết bị khi hoàn tất",
                                     help="Ghi các giá trị “sau” vào hồ sơ thiết bị; lịch sử giữ cấu hình trước.")

    tp_currency_id = fields.Many2one(related="company_id.currency_id", string="Tiền tệ")
    tp_cost_known = fields.Selection(COST_KNOWN, "Chi phí", default="unknown", required=True, tracking=True)
    tp_cost = fields.Monetary("Chi phí thực tế", currency_field="tp_currency_id", tracking=True,
                              help="Chi phí sửa chữa thực tế; khác dự toán đề xuất và giá mua.")
    tp_cost_ref = fields.Char("Chứng từ chi phí")
    tp_meter_value = fields.Integer("Chỉ số đếm lúc xử lý", help="Máy in / photocopy: ghi vào lịch sử số đếm khi hoàn tất.")

    tp_result = fields.Selection(TP_RESULT, "Kết quả", tracking=True)
    tp_state_after = fields.Selection(STATE_AFTER, "Tình trạng thiết bị sau xử lý", tracking=True,
                                      help="Bắt buộc chọn khi hoàn tất; hệ thống không tự ghi “Tốt”.")
    tp_result_note = fields.Text("Ghi chú kết quả")
    tp_done_date = fields.Datetime("Thời điểm hoàn tất", readonly=True, copy=False)
    tp_done_by_id = fields.Many2one("res.users", "Người ghi kết quả", readonly=True, copy=False)
    tp_cancel_reason = fields.Text("Lý do hủy", readonly=True, copy=False)

    tp_move_ids = fields.One2many("tp.equipment.move", "maintenance_request_id", "Phiếu gửi / nhận sửa", readonly=True)
    tp_proposal_line_id = fields.Many2one("tp.equipment.proposal.line", "Từ dòng đề xuất", readonly=True, copy=False,
                                          ondelete="set null", index="btree_not_null")
    tp_equipment_code = fields.Char(related="equipment_id.tp_code", string="Mã thiết bị")
    tp_equipment_custody = fields.Selection(related="equipment_id.tp_custody", string="Nơi giữ thiết bị")
    tp_equipment_lifecycle = fields.Selection(related="equipment_id.tp_lifecycle", string="Vòng đời thiết bị")
    tp_has_config = fields.Boolean(related="equipment_id.category_id.tp_has_config")
    tp_has_meter = fields.Boolean(related="equipment_id.category_id.tp_has_meter")

    _tp_code_unique = models.UniqueIndex("(tp_code) WHERE tp_code IS NOT NULL", "Số phiếu sửa chữa đã tồn tại.")

    # ------------------------------------------------------------------ computes
    @api.depends("tp_deadline", "tp_state")
    def _compute_tp_overdue(self):
        today = fields.Date.context_today(self)
        for request in self:
            request.tp_overdue = bool(request.tp_deadline and request.tp_state in TP_OPEN_STATES
                                      and request.tp_deadline < today)

    def _search_tp_overdue(self, operator, value):
        if operator in ("in", "not in"):
            values = set(value)
            if values == {True, False}:
                return [] if operator == "in" else [("id", "=", 0)]
            value = next(iter(values), False)
            operator = "=" if operator == "in" else "!="
        today = fields.Date.context_today(self)
        domain = [("tp_deadline", "<", today), ("tp_state", "in", TP_OPEN_STATES)]
        if (operator == "=") == bool(value):
            return domain
        return ["|", "|", ("tp_deadline", "=", False), ("tp_deadline", ">=", today), ("tp_state", "not in", TP_OPEN_STATES)]

    @api.constrains("tp_cost", "tp_cost_known")
    def _check_tp_cost(self):
        for request in self:
            if (request.tp_cost or 0) < 0:
                raise ValidationError(_("Chi phí không được âm."))
            if request.tp_cost_known == "free" and request.tp_cost:
                raise ValidationError(_("Đã chọn “không mất phí” thì để trống chi phí."))

    @api.constrains("tp_meter_value")
    def _check_tp_meter(self):
        for request in self:
            if request.tp_meter_value < 0:
                raise ValidationError(_("Chỉ số đếm không được âm."))

    @api.onchange("tp_result")
    def _onchange_tp_result(self):
        """Suggestion only: the admin still confirms the technical state before closing."""
        if self.tp_result in ("not_fixed",) and not self.tp_state_after:
            self.tp_state_after = "broken"
        elif self.tp_result == "limited" and not self.tp_state_after:
            self.tp_state_after = "limited"

    @api.onchange("equipment_id")
    def _onchange_tp_equipment(self):
        if self.equipment_id and not self.tp_reporter_employee_id and self.equipment_id.tp_employee_id:
            self.tp_reporter_employee_id = self.equipment_id.tp_employee_id
        if self.equipment_id and not self.name:
            self.name = _("%(kind)s – %(name)s", kind=dict(TP_REQUEST_KIND)[self.tp_kind or "fault"],
                          name=self.equipment_id.display_name)

    # ------------------------------------------------------------------ helpers
    @api.model
    def _tp_config_text(self, equipment):
        parts = [f"{label}: {equipment[field]}" for field, label in CONFIG_FIELDS if equipment[field]]
        if equipment.tp_config_note:
            parts.append(equipment.tp_config_note)
        return "\n".join(parts) or _("(chưa ghi cấu hình)")

    def _tp_sync_native(self, tp_state):
        vals = {"tp_state": tp_state}
        xmlid = STAGE_BY_STATE.get(tp_state)
        stage = xmlid and self.env.ref(xmlid, raise_if_not_found=False)
        if stage:
            vals["stage_id"] = stage.id
        if tp_state == "done":
            vals["state"] = "done"
        elif tp_state == "cancel":
            vals["state"] = "cancelled"
        else:
            vals["state"] = "normal"
        self.with_context(tp_request_internal=INTERNAL).write(vals)

    def _tp_schedule_deadline_activity(self):
        for request in self.filtered(lambda r: r.tp_deadline and r.tp_state in TP_OPEN_STATES):
            owner = request.owner_user_id or self.env.user
            request.activity_unlink(["mail.mail_activity_data_todo"])
            request.with_context(mail_activity_quick_update=True).activity_schedule(
                "mail.mail_activity_data_todo", date_deadline=request.tp_deadline, user_id=owner.id,
                summary=_("Hạn xử lý %s", request.tp_code or request.name))

    # ------------------------------------------------------------------ ORM
    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        Equipment = self.env["maintenance.equipment"]
        for values in vals_list:
            if values.get('tp_proposal_line_id'):
                line = self.env['tp.equipment.proposal.line'].browse(values['tp_proposal_line_id'])
                line.proposal_id._tp_lock()
                line._tp_check_execute(('repair', 'upgrade'))
                if line.equipment_id.id != values.get('equipment_id'):
                    raise UserError(_('Thiết bị sửa chữa không khớp dòng đề xuất.'))
                if line.request_ids.filtered(lambda request: request.tp_state not in ('done', 'cancel')):
                    raise UserError(_('Dòng đề xuất đã có phiếu sửa chữa đang mở.'))
        sequence = self.env["ir.sequence"].sudo()
        for vals in vals_list:
            if self.env.context.get("tp_request_internal") is not INTERNAL:
                for key in ("state", "stage_id", "tp_done_date", "tp_done_by_id", "tp_cancel_reason"):
                    vals.pop(key, None)
            vals.setdefault("tp_state", "new")
            if vals["tp_state"] != "new" and self.env.context.get("tp_request_internal") is not INTERNAL:
                vals["tp_state"] = "new"
            vals.setdefault("tp_code", sequence.next_by_code("tp.equipment.repair") or False)
            equipment = Equipment.browse(vals.get("equipment_id"))
            if equipment:
                vals.setdefault("tp_config_before", self._tp_config_text(equipment))
                if vals.get("tp_kind") == "maintenance":
                    vals.setdefault("maintenance_type", "preventive")
            # Real technicians are text metadata; native assignees stay admin users only.
            vals.setdefault("user_ids", [(6, 0, [])])
        requests = super().create(vals_list)
        requests._tp_schedule_deadline_activity()
        requests.equipment_id.tp_refresh_availability()
        return requests

    def write(self, vals):
        check_admin(self.env)
        internal = self.env.context.get("tp_request_internal") is INTERNAL
        if not internal:
            # Native kanban / buttons (stage drag, done, cancel, reset) would bypass the result,
            # vendor-custody and reason checks: progress only moves through this module's buttons.
            if {"tp_state", "state", "stage_id", "tp_done_date", "tp_done_by_id", "tp_cancel_reason"} & set(vals):
                raise UserError(_("Dùng các nút trên phiếu sửa chữa của Kho thiết bị để đổi tiến trình "
                                  "(bắt đầu, gửi sửa ngoài, hoàn tất, hủy)."))
            locked = self.filtered(lambda r: r.tp_state in ("done", "cancel"))
            free = {"tp_result_note", "tp_cost_ref", "message_main_attachment_id", "color", "priority"}
            if locked and set(vals) - free:
                raise UserError(_("Phiếu %(name)s đã kết thúc, chỉ bổ sung ghi chú / chứng từ.",
                                  name=locked[0].tp_code or locked[0].name))
            if "equipment_id" in vals and self.filtered(lambda r: r.tp_state != "new"):
                raise UserError(_("Không đổi thiết bị của phiếu đang xử lý; hủy và lập phiếu mới."))
        res = super().write(vals)
        if "tp_deadline" in vals:
            self._tp_schedule_deadline_activity()
        if {"tp_state", "state", "equipment_id"} & set(vals):
            self.equipment_id.tp_refresh_availability()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_tp_only_new(self):
        check_admin(self.env)
        for request in self:
            if request.tp_state != "new" or request.tp_move_ids:
                raise UserError(_("Chỉ xóa được phiếu mới ghi nhận chưa xử lý; phiếu khác dùng Hủy để giữ lịch sử."))

    def message_new(self, msg_dict, custom_values=None):
        # No request is created from inbound e-mail: the register is admin-only and in-app.
        raise UserError(_("Kho thiết bị văn phòng không nhận yêu cầu qua email."))

    # ------------------------------------------------------------------ actions
    def _tp_lock(self):
        check_admin(self.env)
        if not self:
            return
        if any(record.company_id not in self.env.companies for record in self):
            raise UserError(_('Công ty ngoài phạm vi được phép.'))
        self.env.cr.execute(SQL("SELECT id FROM maintenance_request WHERE id IN %s ORDER BY id FOR UPDATE", tuple(self.ids)))
        self.invalidate_recordset()

    def action_tp_start(self):
        self._tp_lock()
        for request in self:
            if request.tp_state != "new":
                continue
            if not request.equipment_id:
                raise UserError(_("Chọn thiết bị trước khi bắt đầu xử lý."))
            if request.equipment_id.tp_lifecycle != "active":
                raise UserError(_("%(name)s chưa đăng ký hoặc đã ngừng quản lý.", name=request.equipment_id.display_name))
            request._tp_sync_native("in_progress")
        return True

    def _tp_open_move(self, move_type):
        self.ensure_one()
        check_admin(self.env)
        if not self.equipment_id:
            raise UserError(_("Phiếu chưa có thiết bị."))
        context = {
            "default_move_type": move_type,
            "default_line_ids": [(0, 0, {"equipment_id": self.equipment_id.id})],
            "default_maintenance_request_id": self.id,
            "default_reason": _("Theo phiếu sửa chữa %s", self.tp_code or self.name),
            "tp_eq_leaf": "tp_equipment.menu_repairs",
        }
        partner = self.tp_vendor_id or (self.equipment_id.tp_vendor_id if move_type == "repair_return" else False)
        if partner:
            context["default_target_partner_id"] = partner.id
        return {
            "type": "ir.actions.act_window",
            "name": _("Lập phiếu"),
            "res_model": "tp.equipment.move",
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.move_form").id, "form")],
            "target": "current",
            "context": context,
        }

    def action_tp_send_vendor(self):
        if self.tp_state not in ("new", "in_progress"):
            raise UserError(_("Chỉ gửi sửa ngoài khi phiếu đang xử lý."))
        return self._tp_open_move("send_repair")

    def action_tp_receive_back(self):
        if self.equipment_id.tp_custody != "vendor":
            raise UserError(_("Thiết bị không ở bên sửa ngoài."))
        return self._tp_open_move("repair_return")

    def _tp_on_move_done(self, move):
        """Called by a done move linked to this request (send_repair / repair_return / reversal)."""
        self._tp_lock()
        kind = move.move_type
        if kind == "reversal":
            kind = {"send_repair": "repair_return", "repair_return": "send_repair"}.get(move.reversal_of_id.move_type)
        for request in self.filtered(lambda r: r.tp_state in TP_OPEN_STATES):
            if kind == "send_repair":
                request._tp_sync_native("vendor")
            elif kind == "repair_return" and request.tp_state == "vendor":
                request._tp_sync_native("in_progress")
            request.message_post(body=Markup("%s: <a href='/odoo/phieu-thiet-bi/%s'>%s</a>") % (
                dict(move._fields["move_type"].selection)[move.move_type], move.id, move.name),
                subtype_xmlid="mail.mt_note")

    def action_tp_done(self):
        self._tp_lock()
        for request in self:
            if request.tp_state == "done":
                continue  # idempotent replay
            if request.tp_state not in ("new", "in_progress"):
                raise UserError(_("Phiếu %(name)s: nhận thiết bị về trước khi ghi kết quả.",
                                  name=request.tp_code or request.name))
            equipment = request.equipment_id
            missing = []
            if not equipment:
                missing.append(_("thiết bị"))
            if not request.tp_result:
                missing.append(_("kết quả"))
            if not request.tp_state_after:
                missing.append(_("tình trạng thiết bị sau xử lý"))
            if missing:
                raise UserError(_("Bổ sung %s trước khi hoàn tất.", ", ".join(missing)))
            if equipment.tp_custody == "vendor":
                raise UserError(_("%(name)s còn ở bên sửa ngoài: lập phiếu nhận về trước.", name=equipment.display_name))
            if request.tp_move_ids.filtered(lambda m: m.state == "pending"):
                raise UserError(_("Phiếu gửi / nhận sửa đang chờ bàn giao; hoàn tất hoặc hủy phiếu đó trước."))
            if request.tp_result == "fixed" and request.tp_state_after == "broken":
                raise UserError(_("Kết quả “đã khắc phục” không đi cùng tình trạng “Hỏng”."))
            if equipment.tp_lifecycle == "active":
                vals = {
                    "tp_technical_state": request.tp_state_after,
                    "tp_verification": "verified",
                    "tp_verified_date": fields.Date.context_today(request),
                }
                note = Markup("")
                if request.tp_apply_config:
                    after = {field: (request[f"{field}_after"] or "").strip() for field, _label in CONFIG_FIELDS}
                    changes = {field: value for field, value in after.items() if value and value != equipment[field]}
                    vals.update(changes)
                    if changes:
                        note = Markup("<br/>%s<br/>%s") % (
                            _("Cấu hình trước: %s", request.tp_config_before or ""),
                            _("Cấu hình sau: %s", "; ".join(
                                f"{label}: {changes[field]}" for field, label in CONFIG_FIELDS if field in changes)))
                equipment.write(vals)
                equipment.message_post(body=Markup("%s <a href='/odoo/sua-chua-thiet-bi/%s'>%s</a>: %s%s") % (
                    _("Kết quả phiếu"), request.id, request.tp_code or request.name,
                    dict(TP_RESULT)[request.tp_result], note), subtype_xmlid="mail.mt_note")
            if request.tp_meter_value and equipment:
                self.env["tp.equipment.meter"].create({
                    "equipment_id": equipment.id, "value": request.tp_meter_value, "source": "repair",
                    "note": request.tp_code or request.name,
                })
            request.with_context(tp_request_internal=INTERNAL).write({
                "tp_done_date": fields.Datetime.now(), "tp_done_by_id": self.env.uid,
            })
            request._tp_sync_native("done")
            request.activity_unlink(["mail.mail_activity_data_todo"])
            if request.tp_proposal_line_id:
                request.tp_proposal_line_id._tp_refresh_progress()
        return True

    def action_tp_open_cancel(self):
        check_admin(self.env)
        self.ensure_one()
        return self.env["tp.equipment.reason.wizard"]._tp_open(self, "cancel", _("Hủy phiếu sửa chữa"))

    def _tp_apply_reason(self, action, reason):
        self._tp_lock()
        self.ensure_one()
        if action != "cancel":
            raise UserError(_("Thao tác không hợp lệ."))
        if self.tp_state in ("done", "cancel"):
            raise UserError(_("Phiếu đã kết thúc."))
        if self.tp_state == "vendor" or (self.equipment_id.tp_custody == "vendor" and self.tp_move_ids.filtered(
                lambda m: m.state == "done" and m.move_type == "send_repair")):
            raise UserError(_("Thiết bị còn ở bên sửa ngoài: lập phiếu nhận về trước khi hủy."))
        if self.tp_move_ids.filtered(lambda m: m.state == "pending"):
            raise UserError(_("Hủy hoặc hoàn tất phiếu gửi / nhận sửa đang chờ trước."))
        self.with_context(tp_request_internal=INTERNAL).write({"tp_cancel_reason": reason})
        self._tp_sync_native("cancel")
        self.activity_unlink(["mail.mail_activity_data_todo"])
        self.message_post(body=_("Đã hủy. Lý do: %s", reason), subtype_xmlid="mail.mt_note")
        if self.tp_proposal_line_id:
            self.tp_proposal_line_id._tp_refresh_progress()
        return True

    def action_tp_open_equipment(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "maintenance.equipment",
            "res_id": self.equipment_id.id,
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.equipment_form").id, "form")],
            "target": "current",
        }


class MaintenanceEquipmentRepair(models.Model):
    _inherit = "maintenance.equipment"

    tp_open_request_count = fields.Integer("Phiếu sửa đang mở", compute="_compute_tp_open_requests")

    @api.depends("maintenance_ids.tp_state")
    def _compute_tp_open_requests(self):
        for equipment in self:
            equipment.tp_open_request_count = len(
                equipment.maintenance_ids.filtered(lambda r: r.tp_state in TP_OPEN_STATES))

    def action_tp_new_request(self):
        """Open a pre-filled repair / maintenance / upgrade request. Nothing is saved here."""
        check_admin(self.env)
        self.ensure_one()
        kind = self.env.context.get("tp_request_kind") or "fault"
        return {
            "type": "ir.actions.act_window",
            "name": _("Phiếu sửa chữa"),
            "res_model": "maintenance.request",
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.repair_form").id, "form")],
            "target": "current",
            "context": {
                "default_equipment_id": self.id,
                "default_tp_kind": kind,
                "default_name": _("%(kind)s – %(name)s", kind=dict(TP_REQUEST_KIND)[kind], name=self.display_name),
                "default_tp_reporter_employee_id": self.tp_employee_id.id,
                "default_maintenance_type": "preventive" if kind == "maintenance" else "corrective",
                "tp_eq_leaf": "tp_equipment.menu_repairs",
            },
        }

    def action_tp_open_requests(self):
        check_admin(self.env)
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Sửa chữa của %s", self.display_name),
            "res_model": "maintenance.request",
            "view_mode": "list,form",
            "views": [(self.env.ref("tp_equipment.repair_list").id, "list"),
                      (self.env.ref("tp_equipment.repair_form").id, "form")],
            "search_view_id": self.env.ref("tp_equipment.repair_search").id,
            "domain": [("equipment_id", "=", self.id)],
            "context": {"default_equipment_id": self.id, "tp_filter_profile": "repair",
                        "tp_eq_leaf": "tp_equipment.menu_repairs"},
        }
