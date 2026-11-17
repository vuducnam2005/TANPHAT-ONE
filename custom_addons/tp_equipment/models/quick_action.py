"""EQUIP-SIMPLE-003 (DEC-047): Gán / Đổi máy / Trả về kho, one business RPC per confirmation.

The popup only collects the choice. ``maintenance.equipment.tp_quick_action`` checks rights,
company, recipient, holder and version under row locks (stable id order), then runs the existing
handover documents (``tp.equipment.move`` + ``action_done``) in the same transaction: a swap
either returns A *and* assigns B, or changes nothing. JavaScript never writes custody fields.
"""
import ast
import hashlib
import json
import re
import uuid

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import clean_context

from .common import HOLDING_CUSTODY, INTERNAL, TECH_STATE, check_admin, lock_records

TAKEN_MSG = "Thiết bị đã có người sử dụng hoặc không còn trong kho, vui lòng chọn thiết bị khác"
CHANGED_MSG = "Máy đã thay đổi, vui lòng tải lại"
NONE_FREE_MSG = "Không có thiết bị trong kho chưa được gán"
MODES = [("assign", "Gán thiết bị"), ("swap", "Đổi máy"), ("return", "Trả về kho")]
RETURN_REASONS = [("swap", "Đổi máy"), ("leave", "Nghỉ việc"), ("other", "Thu hồi khác")]
OPEN_REPAIR = ("new", "in_progress", "vendor")
USAGE_STATUS = [
    ("in_use", "Đang sử dụng"),
    ("stock", "Trong kho"),
    ("shared", "Dùng chung"),
    ("location", "Đặt tại vị trí"),
    ("vendor", "Đang sửa ngoài"),
    ("cleanup", "Cần làm sạch: trong kho nhưng còn người giữ"),
    ("unknown", "Chưa rõ người giữ"),
    ("draft", "Nháp"),
    ("retired", "Ngừng quản lý"),
]
# The single "Thiết bị" list: same leaves as the segmented control filters in equipment_views.xml.
IN_USE_DOMAIN = [("tp_custody", "in", ("employee", "loan")), ("tp_employee_id", "!=", False)]
STOCK_DOMAIN = [("tp_custody", "=", "stock"), ("tp_employee_id", "=", False)]
REQUEST_KEY = re.compile(r"^[0-9a-f]{16,64}$")


def free_domain(env):
    """Machines that may be assigned or swapped in: in stock AND no holder AND fit to hand over."""
    return STOCK_DOMAIN + [
        ("tp_lifecycle", "=", "active"),
        ("tp_asset_class", "in", ("device", "component")),
        ("tp_parent_id", "=", False),
        ("tp_technical_state", "!=", "broken"),
        ("tp_move_line_ids", "not any", [("state", "=", "pending")]),
        ("maintenance_ids", "not any", [("tp_state", "in", OPEN_REPAIR)]),
        ("company_id", "in", env.companies.ids),
    ]


def _command_ids(value):
    ids = []
    for item in value or []:
        if isinstance(item, int):
            ids.append(item)
        elif isinstance(item, (list, tuple)) and item:
            if item[0] == 6 and len(item) > 2:
                ids.extend(item[2] or [])
            elif item[0] == 4 and len(item) > 1:
                ids.append(item[1])
    return ids


def _positive_id(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else False


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    tp_usage_status = fields.Selection(USAGE_STATUS, "Trạng thái sử dụng", compute="_compute_tp_usage_status")
    tp_short_config = fields.Char("Cấu hình", compute="_compute_tp_short_config")
    tp_can_assign = fields.Boolean("Gán được", compute="_compute_tp_quick_flags")
    tp_can_swap = fields.Boolean("Đổi máy được", compute="_compute_tp_quick_flags")
    tp_can_return = fields.Boolean("Trả kho được", compute="_compute_tp_quick_flags")

    @api.depends("tp_lifecycle", "tp_custody", "tp_employee_id")
    def _compute_tp_usage_status(self):
        for equipment in self:
            custody = equipment.tp_custody
            if equipment.tp_lifecycle in ("draft", "retired"):
                status = equipment.tp_lifecycle
            elif custody == "stock":
                status = "cleanup" if equipment.tp_employee_id else "stock"
            elif custody in ("employee", "loan"):
                status = "in_use" if equipment.tp_employee_id else "unknown"
            else:
                status = {"department": "shared", "location": "location", "vendor": "vendor"}.get(custody, "unknown")
            equipment.tp_usage_status = status

    @api.depends("tp_cpu", "tp_ram", "tp_storage", "tp_brand", "model")
    def _compute_tp_short_config(self):
        for equipment in self:
            parts = [p for p in (equipment.tp_cpu, equipment.tp_ram, equipment.tp_storage) if p]
            if not parts:
                parts = [p for p in (equipment.tp_brand, equipment.model) if p]
            equipment.tp_short_config = " · ".join(parts) if parts else False

    @api.depends("tp_lifecycle", "tp_custody", "tp_employee_id", "tp_technical_state", "tp_asset_class",
                 "tp_parent_id", "tp_move_line_ids.state", "maintenance_ids.tp_state")
    def _compute_tp_quick_flags(self):
        for equipment in self:
            held = equipment.tp_lifecycle == "active" and not equipment._tp_has_pending()
            equipment.tp_can_assign = not equipment._tp_assign_problem()
            equipment.tp_can_swap = held and equipment.tp_custody in ("employee", "loan") and bool(
                equipment.tp_employee_id)
            equipment.tp_can_return = held and equipment.tp_custody in HOLDING_CUSTODY

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # "Thêm thiết bị" popup: a valid save registers the machine through the existing backend step
        # (opening move, version, chatter); code and draft state come from the base create.
        if self.env.context.get("tp_quick_register") and records:
            records.with_context(tp_quick_register=False).action_tp_register()
        return records

    def _tp_has_pending(self):
        self.ensure_one()
        return any(line.state == "pending" for line in self.tp_move_line_ids)

    def _tp_assign_problem(self):
        """False when this machine may be handed to a person; otherwise why not (re-checked under lock)."""
        self.ensure_one()
        name = self.display_name
        if self.tp_custody != "stock" or self.tp_employee_id:
            return "%s (%s)." % (TAKEN_MSG, name)
        if self.tp_lifecycle == "draft":
            return _("%(name)s chưa đăng ký vào kho.", name=name)
        if self.tp_lifecycle != "active":
            return _("%(name)s đã ngừng quản lý.", name=name)
        if self.tp_asset_class == "service":
            return _("%(name)s là dịch vụ / đường truyền, không gán cho người dùng.", name=name)
        if self.tp_parent_id:
            return _("%(name)s đang gắn vào máy khác; tháo khỏi bộ máy trước khi gán.", name=name)
        if self.tp_technical_state == "broken":
            return _("%(name)s đang hỏng, không gán được.", name=name)
        if self._tp_has_pending():
            return _("%(name)s đang chờ bàn giao ở phiếu khác.", name=name)
        if any(request.tp_state in OPEN_REPAIR for request in self.maintenance_ids):
            return _("%(name)s còn phiếu sửa chữa chưa kết thúc.", name=name)
        if self.company_id not in self.env.companies:
            return _("%(name)s không thuộc công ty đang thao tác.", name=name)
        return False

    def _tp_is_unverified(self):
        self.ensure_one()
        return self.tp_technical_state == "unverified" or self.tp_verification == "source"

    # ------------------------------------------------------------------ list header
    @api.model
    def tp_main_summary(self):
        """Counts of the default scope; the scope is read from the list action itself (one domain)."""
        check_admin(self.env, self)
        action = self.env.ref("tp_equipment.action_equipment")
        scope = ast.literal_eval(action.domain or "[]")
        stock_with_holder = [("tp_custody", "=", "stock"), ("tp_employee_id", "!=", False)]
        return {
            "total": self.search_count(scope),
            "in_use": self.search_count(scope + IN_USE_DOMAIN),
            "stock": self.search_count(scope + STOCK_DOMAIN),
            "free": self.search_count(free_domain(self.env)),
            "cleanup": self.search_count(scope + stock_with_holder),
        }

    # ------------------------------------------------------------------ popup openers (nothing is saved)
    def _tp_quick_open(self, mode, **defaults):
        check_admin(self.env)
        context = {f"default_{key}": value for key, value in defaults.items() if value}
        context["default_mode"] = mode
        return {
            "type": "ir.actions.act_window",
            "name": dict(MODES)[mode],
            "res_model": "tp.equipment.quick.action",
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.quick_action_form").id, "form")],
            "target": "new",
            "context": context,
        }

    def action_tp_quick_assign(self):
        return self._tp_quick_open("assign", assign_equipment_ids=self.filtered("tp_can_assign").ids)

    def action_tp_quick_swap(self):
        self.ensure_one()
        return self._tp_quick_open("swap", employee_id=self.tp_employee_id.id, old_equipment_id=self.id)

    def action_tp_quick_return(self):
        employee = self.tp_employee_id
        if len(employee) > 1:
            raise UserError(_("Chọn các máy của cùng một người để trả về kho trong một lần."))
        return self._tp_quick_open("return", employee_id=employee.id, return_equipment_ids=self.ids)

    def action_tp_quick_edit(self):
        """"Sửa": the short form in a dialog. Holder/custody are not on it (only Gán / Đổi máy / Trả về kho)."""
        check_admin(self.env)
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Sửa thông tin thiết bị"),
            "res_model": "maintenance.equipment",
            "res_id": self.id,
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.equipment_quick_form").id, "form")],
            "target": "new",
            "context": {"tp_eq_leaf": "tp_equipment.menu_equipment_all"},
        }

    # ------------------------------------------------------------------ the business RPC
    @api.model
    def tp_quick_action(self, payload):
        """Run one Gán / Đổi máy / Trả về kho confirmation. Same key + same payload = same result."""
        check_admin(self.env)
        # Drop the popup's default_* keys so they never leak into the move documents.
        return self.with_context(clean_context(self.env.context))._tp_quick_run(payload)

    def _tp_quick_run(self, payload):
        data = self._tp_quick_normalize(payload)
        key = data.pop("request_key")
        digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        Move = self.env["tp.equipment.move"]
        previous = Move.search([("tp_request_key", "=", key)], order="id")
        if previous:
            if any(move.tp_request_hash != digest for move in previous):
                raise UserError(_("%s (mã yêu cầu đã dùng cho nội dung khác).", CHANGED_MSG))
            return self._tp_quick_result(data, previous)

        mode = data["mode"]
        Equipment = self.with_context(active_test=False)
        employee = self.env["hr.employee"].with_context(active_test=False).browse(data["employee_id"] or [])
        if employee and not employee.exists():
            raise UserError(_("%s (người sử dụng không còn tồn tại).", CHANGED_MSG))
        if mode == "assign":
            olds, targets = Equipment.browse(), Equipment.browse(data["equipment_ids"])
            if not targets:
                raise UserError(_("Chọn ít nhất một thiết bị trong kho."))
        elif mode == "swap":
            olds = Equipment.browse(data["old_equipment_id"] or [])
            targets = Equipment.browse(data["new_equipment_id"] or [])
            if not olds:
                raise UserError(_("Chọn máy đang dùng cần đổi."))
            if not targets:
                raise UserError(_("Chọn máy mới trong kho."))
            if olds == targets:
                raise UserError(_("Máy mới phải khác máy đang dùng."))
        else:
            olds, targets = Equipment.browse(data["equipment_ids"]), Equipment.browse()
            if not olds:
                raise UserError(_("Chọn ít nhất một thiết bị cần trả về kho."))
            if not data["reason"]:
                raise UserError(_("Chọn lý do trả về kho."))
        if mode in ("assign", "swap") and not employee:
            raise UserError(_("Chọn người sử dụng."))
        machines = olds | targets
        if len(machines.exists()) != len(machines):
            raise UserError(_("%s (thiết bị không còn tồn tại).", CHANGED_MSG))

        lock_records(machines)  # ORDER BY id FOR UPDATE NOWAIT, then the cache is refreshed
        self._tp_quick_check(data, employee, olds, targets)

        reason_text = self._tp_quick_reason(data, employee, olds, targets, key)
        company = machines[:1].company_id
        legs = {}
        for machine in olds.sorted("id"):
            legs.setdefault("loan_return" if machine.tp_custody == "loan" else "return", []).append(machine.id)
        if targets:
            legs["assign"] = targets.sorted("id").ids
        InternalMove = Move.with_context(tp_equipment_move_internal=INTERNAL)
        moves = Move.browse()
        for move_type in ("return", "loan_return", "assign"):
            if move_type not in legs:
                continue
            vals = {
                "move_type": move_type,
                "company_id": company.id,
                "reason": reason_text,
                "idempotency_key": f"{key}:{move_type}",
                "tp_request_key": key,
                "tp_request_hash": digest,
                "target_location_id": False,
                "line_ids": [(0, 0, {"equipment_id": equipment_id}) for equipment_id in legs[move_type]],
            }
            if move_type == "assign":
                vals.update({"target_custody": "employee", "target_employee_id": employee.id})
            moves |= Move.browse(InternalMove.create(vals).ids)
        for move in moves:  # return leg first, then assign; any error rolls back the whole RPC
            move.action_done()
        return self._tp_quick_result(data, moves)

    @api.model
    def _tp_quick_normalize(self, payload):
        if not isinstance(payload, dict):
            raise UserError(_("Yêu cầu không hợp lệ."))
        mode = payload.get("mode")
        if mode not in dict(MODES):
            raise UserError(_("Thao tác không hợp lệ."))
        key = payload.get("request_key")
        if not isinstance(key, str) or not REQUEST_KEY.match(key):
            raise UserError(_("Thiếu mã yêu cầu; mở lại cửa sổ thao tác."))
        raw_ids = payload.get("equipment_ids") or []
        if not isinstance(raw_ids, list) or not all(_positive_id(value) for value in raw_ids):
            raise UserError(_("Danh sách thiết bị không hợp lệ."))
        versions = payload.get("expected_versions") or {}
        if not isinstance(versions, dict):
            raise UserError(_("Phiên bản thiết bị không hợp lệ."))
        try:
            versions = {str(int(k)): int(v) for k, v in versions.items()}
        except (TypeError, ValueError):
            raise UserError(_("Phiên bản thiết bị không hợp lệ.")) from None
        reason = payload.get("reason") or False
        if reason and reason not in dict(RETURN_REASONS):
            raise UserError(_("Lý do trả về kho không hợp lệ."))
        note = payload.get("note") or ""
        if not isinstance(note, str):
            raise UserError(_("Ghi chú không hợp lệ."))
        ids = sorted(set(raw_ids))
        old_id = _positive_id(payload.get("old_equipment_id")) if mode == "swap" else False
        new_id = _positive_id(payload.get("new_equipment_id")) if mode == "swap" else False
        involved = {str(i) for i in ids + [old_id, new_id] if i}
        return {
            "mode": mode,
            "employee_id": _positive_id(payload.get("employee_id")),
            "equipment_ids": ids if mode != "swap" else [],
            "old_equipment_id": old_id,
            "new_equipment_id": new_id,
            "reason": reason if mode == "return" else ("swap" if mode == "swap" else False),
            "note": note.strip()[:2000],
            "confirm_unverified": bool(payload.get("confirm_unverified")),
            "expected_versions": {k: v for k, v in versions.items() if k in involved},
            "request_key": key,
        }

    def _tp_quick_check(self, data, employee, olds, targets):
        """Every rule again after the lock; state errors before the version check."""
        companies = self.env.companies
        hr = employee.sudo()  # HR fields read only to validate the recipient, never to write
        if employee and hr.company_id not in companies:
            raise UserError(_("Người sử dụng không thuộc công ty đang thao tác."))
        if data["mode"] in ("assign", "swap") and not hr.active:
            raise UserError(_("%(name)s đã nghỉ / lưu trữ hồ sơ, không nhận thiết bị được.", name=hr.name))
        for machine in olds | targets:
            if machine.company_id not in companies or (employee and machine.company_id != hr.company_id):
                raise UserError(_("%(name)s không cùng công ty với người sử dụng.", name=machine.display_name))
        for machine in targets:  # CHG-20261116-002 hard rule: stock AND no holder, then fitness
            problem = machine._tp_assign_problem()
            if problem:
                raise UserError(problem)
        for machine in olds:
            if machine.tp_lifecycle != "active":
                raise UserError(_("%(name)s không còn được quản lý.", name=machine.display_name))
            allowed = ("employee", "loan") if data["mode"] == "swap" else HOLDING_CUSTODY
            if machine.tp_custody not in allowed or machine.tp_employee_id != employee:
                raise UserError(_("%(msg)s: %(name)s không còn ở người / nơi đã chọn.",
                                  msg=CHANGED_MSG, name=machine.display_name))
            if machine._tp_has_pending():
                raise UserError(_("%(name)s đang chờ bàn giao ở phiếu khác.", name=machine.display_name))
        unverified = targets.filtered(lambda m: m._tp_is_unverified())
        if unverified and not data["confirm_unverified"]:
            raise UserError(_("%(names)s chưa xác minh tình trạng thực tế. Đánh dấu xác nhận trong cửa sổ để tiếp "
                              "tục; hệ thống không tự đánh dấu đã xác minh.",
                              names=", ".join(unverified.mapped("display_name"))))
        versions = data["expected_versions"]
        stale = (olds | targets).filtered(lambda m: versions.get(str(m.id)) != m.tp_version)
        if stale:
            raise UserError(CHANGED_MSG)

    def _tp_quick_reason(self, data, employee, olds, targets, key):
        mode = data["mode"]
        if mode == "assign":
            head = _("Gán thiết bị")
        elif mode == "swap":
            head = _("Đổi máy: trả %(old)s về kho, nhận %(new)s", old=olds.display_name, new=targets.display_name)
        else:
            head = _("Trả về kho – %s", dict(RETURN_REASONS)[data["reason"]])
        parts = [head]
        if data["note"]:
            parts.append(data["note"])
        parts.append(_("Mã yêu cầu: %s", key))
        return "\n".join(parts)

    @api.model
    def _tp_quick_result(self, data, moves):
        lines = moves.line_ids
        codes = ", ".join(lines.equipment_id.mapped(lambda e: e.tp_code or e.name))
        names = ", ".join(moves.mapped("name"))
        mode = data["mode"]
        if mode == "assign":
            message = _("Đã gán %(codes)s (phiếu %(moves)s).", codes=codes, moves=names)
        elif mode == "swap":
            message = _("Đã đổi máy (phiếu %(moves)s).", moves=names)
        else:
            message = _("Đã trả về kho %(codes)s (phiếu %(moves)s).", codes=codes, moves=names)
        return {"title": dict(MODES)[mode], "message": message, "moves": moves.mapped("name"),
                "move_ids": moves.ids}


class TpEquipmentQuickAction(models.TransientModel):
    _name = "tp.equipment.quick.action"
    _description = "Gán / đổi / trả thiết bị"

    mode = fields.Selection(MODES, "Thao tác", required=True, default="assign")
    employee_id = fields.Many2one("hr.employee", "Người sử dụng", ondelete="cascade",
                                  domain=lambda self: [("company_id", "in", self.env.companies.ids)])
    assign_equipment_ids = fields.Many2many(
        "maintenance.equipment", "tp_eq_quick_assign_rel", "wizard_id", "equipment_id", "Thiết bị trong kho",
        domain=lambda self: free_domain(self.env))
    return_equipment_ids = fields.Many2many(
        "maintenance.equipment", "tp_eq_quick_return_rel", "wizard_id", "equipment_id", "Thiết bị trả về kho")
    old_equipment_id = fields.Many2one("maintenance.equipment", "Máy đang dùng", ondelete="cascade")
    new_equipment_id = fields.Many2one("maintenance.equipment", "Máy mới trong kho", ondelete="cascade",
                                       domain=lambda self: free_domain(self.env))
    reason = fields.Selection(RETURN_REASONS, "Lý do")
    note = fields.Text("Ghi chú")
    confirm_unverified = fields.Boolean("Tôi đã biết máy chưa xác minh tình trạng thực tế và vẫn giao")
    expected_versions = fields.Char("Phiên bản khi mở")
    request_key = fields.Char("Mã yêu cầu", default=lambda self: uuid.uuid4().hex)

    summary_html = fields.Html("Tóm tắt", compute="_compute_tp_summary", sanitize=False)
    has_unverified = fields.Boolean(compute="_compute_tp_summary")
    employee_archived = fields.Boolean(compute="_compute_tp_summary")
    free_count = fields.Integer(compute="_compute_tp_summary")

    @api.model
    def default_get(self, fields_list):
        check_admin(self.env)
        res = super().default_get(fields_list)
        ids = set(_command_ids(res.get("assign_equipment_ids")) + _command_ids(res.get("return_equipment_ids")))
        for name in ("old_equipment_id", "new_equipment_id"):
            if _positive_id(res.get(name)):
                ids.add(res[name])
        if "expected_versions" in fields_list:
            res["expected_versions"] = self._tp_versions_json(self.env["maintenance.equipment"].browse(sorted(ids)))
        return res

    @api.model
    def _tp_versions_json(self, machines):
        return json.dumps({str(m.id): m.tp_version for m in machines.exists()}, sort_keys=True)

    @api.onchange("assign_equipment_ids", "return_equipment_ids", "old_equipment_id", "new_equipment_id")
    def _onchange_tp_versions(self):
        machines = (self.assign_equipment_ids | self.return_equipment_ids | self.old_equipment_id
                    | self.new_equipment_id)._origin
        self.expected_versions = self._tp_versions_json(machines)

    @api.depends("mode", "employee_id", "assign_equipment_ids", "return_equipment_ids", "old_equipment_id",
                 "new_equipment_id", "reason", "note")
    def _compute_tp_summary(self):
        free_count = None
        for wizard in self:
            if wizard.mode in ("assign", "swap") and free_count is None:
                free_count = self.env["maintenance.equipment"].search_count(free_domain(self.env))
            wizard.free_count = (free_count or 0) if wizard.mode in ("assign", "swap") else 0
            hr = wizard.employee_id.sudo()
            wizard.employee_archived = bool(hr and not hr.active)
            targets = wizard._tp_targets()
            wizard.has_unverified = any(machine._tp_is_unverified() for machine in targets)
            wizard.summary_html = wizard._tp_summary_markup()

    def _tp_targets(self):
        self.ensure_one()
        if self.mode == "assign":
            return self.assign_equipment_ids
        return self.new_equipment_id if self.mode == "swap" else self.env["maintenance.equipment"]

    def _tp_olds(self):
        self.ensure_one()
        if self.mode == "return":
            return self.return_equipment_ids
        return self.old_equipment_id if self.mode == "swap" else self.env["maintenance.equipment"]

    def _tp_machine_markup(self, machine):
        tech = dict(TECH_STATE).get(machine.tp_technical_state, "")
        state_class = {"good": "ok", "limited": "check", "broken": "broken"}.get(machine.tp_technical_state, "check")
        config = machine.tp_short_config or machine.category_id.name or ""
        return Markup(
            "<li><strong>%s</strong> %s<span class='o_tp_eq_qs_meta'>%s</span>"
            "<span class='o_tp_eq_qs_badge o_tp_eq_qs_%s'>%s</span></li>",
        ) % (machine.tp_code or "", machine.name or "", config, state_class, tech)

    def _tp_summary_markup(self):
        self.ensure_one()
        rows = []
        hr = self.employee_id.sudo()
        if hr:
            meta = " · ".join(p for p in (hr.tp_employee_code or "", hr.department_id.name or "") if p)
            rows.append(Markup("<div class='o_tp_eq_qs_row'><span>%s</span><div><strong>%s</strong>"
                               "<span class='o_tp_eq_qs_meta'>%s</span></div></div>") % (
                _("Người sử dụng"), hr.name, meta))
        olds, targets = self._tp_olds(), self._tp_targets()
        if olds:
            label = _("Máy trả về kho") if self.mode == "return" else _("Máy đang dùng → về kho")
            rows.append(Markup("<div class='o_tp_eq_qs_row'><span>%s</span><ul>%s</ul></div>") % (
                label, Markup("").join(self._tp_machine_markup(m) for m in olds)))
        if targets:
            label = _("Máy mới nhận") if self.mode == "swap" else _("Máy sẽ gán (%s)", len(targets))
            rows.append(Markup("<div class='o_tp_eq_qs_row'><span>%s</span><ul>%s</ul></div>") % (
                label, Markup("").join(self._tp_machine_markup(m) for m in targets)))
        if self.mode == "return" and self.reason:
            rows.append(Markup("<div class='o_tp_eq_qs_row'><span>%s</span><div>%s</div></div>") % (
                _("Lý do"), dict(RETURN_REASONS)[self.reason]))
        notes = []
        if self.mode == "return":
            notes.append(_("Sau khi xác nhận: máy về Trong kho, bỏ người giữ; tình trạng kỹ thuật giữ nguyên."))
        elif self.mode == "swap":
            notes.append(_("Một lần xác nhận: trả máy cũ về kho và gán máy mới; lỗi bất kỳ thì không đổi gì."))
        if hr and not hr.active:
            notes.append(_("Người đã nghỉ/cần thu hồi."))
        if not rows:
            return Markup("<p class='text-muted mb-0'>%s</p>") % _("Chọn người và thiết bị để xem tóm tắt.")
        return Markup("<div class='o_tp_eq_quick_summary'>%s%s</div>") % (
            Markup("").join(rows),
            Markup("").join(Markup("<p class='o_tp_eq_qs_note'>%s</p>") % note for note in notes))

    def _tp_payload(self):
        self.ensure_one()
        if self.mode == "assign":
            ids = self.assign_equipment_ids.ids
        elif self.mode == "return":
            ids = self.return_equipment_ids.ids
        else:
            ids = []
        try:
            versions = json.loads(self.expected_versions or "{}")
        except ValueError:
            versions = {}
        return {
            "mode": self.mode,
            "employee_id": self.employee_id.id or False,
            "equipment_ids": ids,
            "old_equipment_id": self.old_equipment_id.id or False,
            "new_equipment_id": self.new_equipment_id.id or False,
            "reason": self.reason or False,
            "note": self.note or "",
            "confirm_unverified": bool(self.confirm_unverified),
            "expected_versions": versions if isinstance(versions, dict) else {},
            "request_key": self.request_key or "",
        }

    def action_confirm(self):
        self.ensure_one()
        check_admin(self.env)
        result = self.env["maintenance.equipment"].tp_quick_action(self._tp_payload())
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"type": "success", "title": result["title"], "message": result["message"],
                       "sticky": False, "next": {"type": "ir.actions.act_window_close"}},
        }
