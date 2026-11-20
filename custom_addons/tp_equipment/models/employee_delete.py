# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""HR-DELETE-ASSET-RETURN-001: Automatic equipment return and move history preservation
upon permanent employee deletion.

Integrates with the guarded permanent deletion flow:
- Identifies equipment currently held by the employee and returns them to warehouse stock
  via native tp.equipment.move documents (type 'return' / 'loan_return').
- Preserves technical state, serial numbers, configurations and move history.
- Cancels pending / draft handover moves for the employee, releasing reservations.
- Takes snapshot of employee name, code, department on past completed move documents,
  then disassociates the FK (sets to NULL) so deletion is not blocked.
- Maintains atomicity: if any step fails, everything rolls back.
"""
import uuid

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from .common import INTERNAL, TECH_STATE, lock_records
from .move import MOVE_TYPES


class HrEmployeeEquipmentDelete(models.Model):
    _inherit = "hr.employee"

    @api.model
    def _tp_get_company_default_location(self, company_id):
        """Find the default equipment location / warehouse for a company."""
        Location = self.env["tp.equipment.location"]
        # Look for active locations in the company
        locations = Location.search([
            ("company_id", "=", company_id),
            ("active", "=", True),
        ], order="sequence, id")
        if not locations:
            return Location.browse()
        # Prefer location with shared=True or code/name containing 'kho' / 'vp' / 'stock'
        for loc in locations:
            name_lower = (loc.name or "").lower()
            code_lower = (loc.code or "").lower()
            if "kho" in name_lower or "kho" in code_lower or "stock" in name_lower or "vp" in name_lower:
                return loc
        return locations[:1]

    def _tp_equipment_plan_for_employees(self):
        """Collect equipment assets to return and history moves to preserve for self."""
        Equipment = self.env["maintenance.equipment"].with_context(active_test=False)
        Move = self.env["tp.equipment.move"]
        MoveLine = self.env["tp.equipment.move.line"]
        emp_ids = set(self.ids)

        plan = {}
        for employee in self:
            company = employee.company_id
            default_loc = self._tp_get_company_default_location(company.id)

            # 1. Equipment currently held by this employee
            held_equipments = Equipment.search([
                ("tp_employee_id", "=", employee.id),
                ("company_id", "=", company.id),
                ("tp_lifecycle", "=", "active"),
            ], order="tp_code, id")

            assets_to_return = []
            for eq in held_equipments:
                action_label = "Thu hồi về kho"
                target_loc = default_loc
                is_returnable = True

                if eq.tp_custody == "loan":
                    action_label = "Nhận lại thiết bị cho mượn"
                elif eq.tp_custody == "vendor":
                    action_label = "Giải phóng người giữ (thiết bị đang sửa ngoài)"
                    target_loc = eq.tp_location_id
                    is_returnable = False
                elif eq.tp_ownership == "personal":
                    action_label = "Trả lại cho chủ sở hữu cá nhân"
                    is_returnable = False
                elif eq.tp_asset_class == "service":
                    action_label = "Giải phóng phân công dịch vụ / license"
                    is_returnable = False

                assets_to_return.append({
                    "id": eq.id,
                    "code": eq.tp_code or "—",
                    "name": eq.name,
                    "serial": eq.serial_no or "—",
                    "tech_state": eq.tp_technical_state,
                    "tech_state_label": dict(TECH_STATE).get(eq.tp_technical_state, eq.tp_technical_state or "—"),
                    "custody": eq.tp_custody,
                    "ownership": eq.tp_ownership,
                    "asset_class": eq.tp_asset_class,
                    "location_id": target_loc.id if target_loc else False,
                    "location_name": target_loc.display_name if target_loc else "—",
                    "action_label": action_label,
                    "is_returnable": is_returnable,
                })

            # 2. Pending or draft moves for this employee (must cancel to release reservation)
            pending_moves = Move.search([
                ("target_employee_id", "=", employee.id),
                ("state", "in", ("draft", "pending")),
            ], order="id")
            cancelled_moves = []
            for m in pending_moves:
                cancelled_moves.append({
                    "id": m.id,
                    "name": m.name,
                    "move_type": m.move_type,
                    "move_type_label": dict(MOVE_TYPES).get(m.move_type, m.move_type),
                    "reason": "Tự động hủy phiếu chờ / nháp của nhân viên bị xóa",
                })

            # 3. Completed history moves (keep moves, snapshot data, detach FK)
            history_moves = Move.search([
                ("target_employee_id", "=", employee.id),
                ("state", "=", "done"),
            ], order="date desc, id desc")
            from_lines = MoveLine.search([
                ("from_employee_id", "=", employee.id),
                ("state", "=", "done"),
            ], order="date desc, id desc")
            to_lines = MoveLine.search([
                ("to_employee_id", "=", employee.id),
                ("state", "=", "done"),
            ], order="date desc, id desc")

            history_items = []
            if history_moves:
                history_items.append({
                    "category": "move_target",
                    "label": "Phiếu bàn giao / thu hồi – Nhân viên nhận",
                    "count": len(history_moves),
                    "details": ", ".join(history_moves.mapped("name")[:5]) + ("…" if len(history_moves) > 5 else ""),
                    "snapshot": f"Bảo toàn snapshot: {employee.name} (Mã: {employee.tp_employee_code or '—'})",
                })
            if from_lines:
                history_items.append({
                    "category": "line_from",
                    "label": "Dòng phiếu bàn giao – Người giữ trước",
                    "count": len(from_lines),
                    "details": ", ".join(from_lines.mapped("equipment_code")[:5]) + ("…" if len(from_lines) > 5 else ""),
                    "snapshot": f"Bảo toàn snapshot: {employee.name} (Mã: {employee.tp_employee_code or '—'})",
                })
            if to_lines:
                history_items.append({
                    "category": "line_to",
                    "label": "Dòng phiếu bàn giao – Người giữ sau",
                    "count": len(to_lines),
                    "details": ", ".join(to_lines.mapped("equipment_code")[:5]) + ("…" if len(to_lines) > 5 else ""),
                    "snapshot": f"Bảo toàn snapshot: {employee.name} (Mã: {employee.tp_employee_code or '—'})",
                })

            # Check available locations for company
            avail_locs = self.env["tp.equipment.location"].search([
                ("company_id", "=", company.id),
                ("active", "=", True),
            ], order="sequence, id")
            locations_data = [{
                "id": loc.id,
                "name": loc.display_name,
                "code": loc.code or "",
                "is_default": bool(default_loc and loc.id == default_loc.id),
            } for loc in avail_locs]

            plan[employee.id] = {
                "assets_to_return": assets_to_return,
                "cancelled_moves": cancelled_moves,
                "equipment_history": history_items,
                "available_locations": locations_data,
                "default_location_id": default_loc.id if default_loc else False,
            }

        return plan

    def _tp_delete_plan(self):
        """Override plan to replace equipment blockers with automatic return & history preservation."""
        res = super()._tp_delete_plan()
        eq_plan = self._tp_equipment_plan_for_employees()

        # Keywords of equipment labels that are automatically handled and must NOT block deletion
        HANDLED_LABELS = (
            "dòng phiếu bàn giao",
            "phiếu bàn giao",
            "người giữ trước",
            "người giữ sau",
            "nhân viên nhận",
            "nhân viên đang giữ",
            "thiết bị đang giữ",
            "đề xuất thiết bị",
            "người cần",
            "người nhận (chuyển máy)",
            "phiếu sửa chữa",
            "người báo / yêu cầu",
            "kiểm kê thiết bị",
            "người giữ theo sổ",
            "người giữ thực tế",
            "lô nhập thiết bị",
            "dòng nhập thiết bị",
        )

        for employee in self:
            emp_data = res["employees"].get(employee.id)
            if not emp_data:
                continue

            eq_info = eq_plan.get(employee.id, {})
            assets_to_return = eq_info.get("assets_to_return", [])
            history_items = eq_info.get("equipment_history", [])
            cancelled_moves = eq_info.get("cancelled_moves", [])

            # Filter out equipment-related items from 'block'
            new_blocks = []
            for item in emp_data.get("block", []):
                label_lower = (item[0] or "").lower()
                if any(kw in label_lower for kw in HANDLED_LABELS):
                    continue
                new_blocks.append(item)
            emp_data["block"] = new_blocks

            # Check if any returnable asset lacks a destination warehouse
            for asset in assets_to_return:
                if asset.get("is_returnable") and not asset.get("location_id"):
                    emp_data["block"].append([
                        "Kho nhận thu hồi thiết bị",
                        1,
                        _("Công ty %(company)s chưa có vị trí kho thiết bị để nhận tài sản %(code)s. Hãy tạo vị trí kho trước.",
                          company=employee.company_id.name, code=asset["code"]),
                    ])

            # Attach equipment plan to employee data
            emp_data["assets_to_return"] = assets_to_return
            emp_data["equipment_history"] = history_items
            emp_data["cancelled_moves"] = cancelled_moves

            # Add to 'keep' summary for transparency
            if assets_to_return:
                emp_data["keep"].append([
                    "Tài sản công ty cấp trực tiếp",
                    f"{len(assets_to_return)} thiết bị (tự động thu hồi về kho khi xác nhận)",
                ])
            if history_items:
                total_history = sum(item["count"] for item in history_items)
                emp_data["keep"].append([
                    "Lịch sử bàn giao / thu hồi thiết bị",
                    f"{total_history} phiếu / dòng (bảo toàn họ tên, mã nhân viên, phòng ban)",
                ])
            if cancelled_moves:
                emp_data["delete"].append([
                    "Phiếu bàn giao đang chờ / nháp",
                    f"{len(cancelled_moves)} phiếu (hủy để giải phóng giữ chỗ tài sản)",
                ])

        res["equipment_available_locations"] = {
            employee.id: eq_plan[employee.id]["available_locations"]
            for employee in self if employee.id in eq_plan
        }
        res["equipment_default_location_id"] = {
            employee.id: eq_plan[employee.id]["default_location_id"]
            for employee in self if employee.id in eq_plan
        }
        return res

    def _tp_permanent_unlink(self, plan, audit_vals_list):
        """Execute automatic equipment return and history preservation in the same transaction."""
        Move = self.env["tp.equipment.move"]
        MoveLine = self.env["tp.equipment.move.line"]
        Equipment = self.env["maintenance.equipment"].with_context(active_test=False)
        Location = self.env["tp.equipment.location"]

        custom_location_id = self.env.context.get("tp_equipment_return_location_id")

        for employee in self:
            company = employee.company_id
            emp_plan = plan.get("employees", {}).get(employee.id, {})
            assets_to_return = emp_plan.get("assets_to_return", [])

            # Destination location: custom_location_id if provided and in company, else default
            dest_location = False
            if custom_location_id:
                loc = Location.browse(int(custom_location_id))
                if loc.exists() and loc.company_id == company:
                    dest_location = loc
            if not dest_location:
                dest_location = self._tp_get_company_default_location(company.id)

            # 1. Cancel pending/draft moves for this employee
            pending_moves = Move.search([
                ("target_employee_id", "=", employee.id),
                ("state", "in", ("draft", "pending")),
            ])
            if pending_moves:
                pending_moves.with_context(tp_equipment_move_internal=INTERNAL).write({
                    "state": "cancel",
                    "reason": _("Tự động hủy khi xóa vĩnh viễn nhân viên %(name)s", name=employee.name),
                })

            # 2. Return active equipment held by this employee
            return_eq_ids = [a["id"] for a in assets_to_return if a.get("is_returnable")]
            if return_eq_ids:
                equipments = Equipment.browse(return_eq_ids)
                lock_records(equipments)

                loan_eqs = equipments.filtered(lambda e: e.tp_custody == "loan")
                return_eqs = equipments.filtered(lambda e: e.tp_custody != "loan")

                for move_type, eq_group in (("loan_return", loan_eqs), ("return", return_eqs)):
                    if not eq_group:
                        continue
                    key = f"del_return_{employee.id}_{move_type}_{uuid.uuid4().hex[:8]}"
                    reason_text = _("Thu hồi về kho khi xóa vĩnh viễn nhân viên %(name)s (%(code)s)",
                                    name=employee.name, code=employee.tp_employee_code or "—")
                    move_vals = {
                        "move_type": move_type,
                        "company_id": company.id,
                        "reason": reason_text,
                        "idempotency_key": key,
                        "target_location_id": dest_location.id if dest_location else False,
                        "line_ids": [(0, 0, {
                            "equipment_id": eq.id,
                            "condition": eq.tp_technical_state,
                        }) for eq in eq_group.sorted("id")],
                    }
                    move = Move.with_context(tp_equipment_move_internal=INTERNAL).create(move_vals)
                    move.action_done()

            # Handle non-returnable equipment held by employee
            # Personal equipment: release custody / return to owner
            personal_eqs = Equipment.search([
                ("tp_employee_id", "=", employee.id),
                ("tp_ownership", "=", "personal"),
            ])
            for eq in personal_eqs:
                eq.with_context(tp_equipment_move=INTERNAL).write({
                    "tp_custody": "none",
                    "tp_employee_id": False,
                    "tp_lifecycle": "retired",
                    "tp_retire_reason": "returned_owner",
                    "tp_retire_date": fields.Date.context_today(self),
                    "tp_retire_note": _("Trả lại cho chủ sở hữu cá nhân khi xóa vĩnh viễn nhân viên %(name)s",
                                        name=employee.name),
                })

            # Vendor / service equipment: disassociate holder
            other_held = Equipment.search([
                ("tp_employee_id", "=", employee.id),
                ("id", "not in", return_eq_ids + personal_eqs.ids),
            ])
            for eq in other_held:
                vals = {"tp_employee_id": False}
                if eq.tp_custody in ("employee", "loan"):
                    vals["tp_custody"] = "stock"
                    vals["tp_location_id"] = dest_location.id if dest_location else False
                eq.with_context(tp_equipment_move=INTERNAL).write(vals)

            # 3. Snapshot and disassociate completed history moves & lines
            # Move headers
            past_moves = Move.search([("target_employee_id", "=", employee.id)])
            if past_moves:
                past_moves.with_context(tp_equipment_move_internal=INTERNAL).write({
                    "target_employee_name": employee.name,
                    "target_employee_code": employee.tp_employee_code or "",
                    "target_employee_dept": employee.department_id.name or "",
                    "target_employee_deleted": True,
                    "target_employee_id": False,
                })

            # Move lines (from)
            from_lines = MoveLine.search([("from_employee_id", "=", employee.id)])
            if from_lines:
                from_lines.with_context(tp_equipment_move_internal=INTERNAL).write({
                    "from_employee_name": employee.name,
                    "from_employee_code": employee.tp_employee_code or "",
                    "from_employee_dept": employee.department_id.name or "",
                    "from_employee_deleted": True,
                    "from_employee_id": False,
                })

            # Move lines (to)
            to_lines = MoveLine.search([("to_employee_id", "=", employee.id)])
            if to_lines:
                to_lines.with_context(tp_equipment_move_internal=INTERNAL).write({
                    "to_employee_name": employee.name,
                    "to_employee_code": employee.tp_employee_code or "",
                    "to_employee_dept": employee.department_id.name or "",
                    "to_employee_deleted": True,
                    "to_employee_id": False,
                })

            # 4. Snapshot & disassociate proposals, repair requests, inventory lines, imports
            Proposal = self.env["tp.equipment.proposal"].sudo()
            proposals = Proposal.search([("requester_employee_id", "=", employee.id)])
            if proposals:
                proposals.write({
                    "requester_text": f"{employee.name} ({employee.tp_employee_code or '—'}) – Nhân viên đã xóa",
                    "requester_employee_id": False,
                })

            ProposalLine = self.env["tp.equipment.proposal.line"].sudo()
            prop_lines = ProposalLine.search([("target_employee_id", "=", employee.id)])
            if prop_lines:
                prop_lines.write({
                    "target_employee_name": employee.name,
                    "target_employee_id": False,
                })

            Repair = self.env["maintenance.request"].sudo()
            repairs = Repair.search([("tp_reporter_employee_id", "=", employee.id)])
            if repairs:
                repairs.write({
                    "tp_reporter_employee_name": employee.name,
                    "tp_reporter_employee_id": False,
                })

            InvLine = self.env["tp.equipment.inventory.line"].sudo()
            exp_invs = InvLine.search([("expected_employee_id", "=", employee.id)])
            if exp_invs:
                exp_invs.write({
                    "expected_employee_name": employee.name,
                    "expected_employee_id": False,
                })
            act_invs = InvLine.search([("actual_employee_id", "=", employee.id)])
            if act_invs:
                act_invs.write({
                    "actual_employee_name": employee.name,
                    "actual_employee_id": False,
                })

            ImportLine = self.env["tp.equipment.import.line"].sudo()
            imp_lines = ImportLine.search([("employee_id", "=", employee.id)])
            if imp_lines:
                imp_lines.write({"employee_id": False})

            ImportAlias = self.env["tp.equipment.import.alias"].sudo()
            imp_aliases = ImportAlias.search([("employee_id", "=", employee.id)])
            if imp_aliases:
                imp_aliases.write({"employee_id": False})

            # 5. Enrich audit snapshot
            for vals in audit_vals_list:
                if vals.get("employee_ref") == employee.id:
                    snap = vals.setdefault("snapshot", {})
                    snap["returned_equipment"] = [
                        {"code": a["code"], "name": a["name"], "serial": a["serial"], "action": a["action_label"]}
                        for a in assets_to_return
                    ]
                    snap["equipment_history_preserved"] = len(past_moves) + len(from_lines) + len(to_lines)

        self.env.invalidate_all()
        return super()._tp_permanent_unlink(plan, audit_vals_list)
