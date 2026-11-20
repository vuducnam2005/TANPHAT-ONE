# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
import uuid
from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.addons.tp_hr_workspace.tests.test_hr_workspace import BaseHrWorkspace
from odoo.addons.tp_equipment.models.common import INTERNAL


@tagged("post_install", "-at_install")
class TestEmployeeDeleteAssetReturn(BaseHrWorkspace):
    """HR-DELETE-ASSET-RETURN-001: Automatic equipment return & history preservation on employee deletion."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Location = cls.env["tp.equipment.location"]
        # Ensure a default location exists for the test company
        cls.location = Location.search([
            ("company_id", "=", cls.company.id),
            ("active", "=", True),
        ], limit=1)
        if not cls.location:
            cls.location = Location.create({
                "name": "Kho thiết bị công ty",
                "code": "KHO-SYNTHETIC",
                "company_id": cls.company.id,
                "shared": True,
            })

    def _create_equipment(self, name, custody="stock", employee=None, tech_state="good", ownership="company", asset_class="device"):
        Equipment = self.env["maintenance.equipment"].with_context(active_test=False)
        vals = {
            "name": name,
            "company_id": self.company.id,
            "tp_lifecycle": "active",
            "tp_custody": custody,
            "tp_technical_state": tech_state,
            "tp_ownership": ownership,
            "tp_asset_class": asset_class,
            "serial_no": f"SN-{uuid.uuid4().hex[:6].upper()}",
        }
        if custody in ("employee", "loan"):
            vals["tp_employee_id"] = employee.id if employee else False
        elif custody == "location":
            vals["tp_location_id"] = self.location.id
        elif custody == "department":
            vals["tp_holder_department_id"] = self.department.id
        eq = Equipment.create(vals)
        eq.with_context(tp_equipment_move=INTERNAL).write({
            "tp_lifecycle": "active",
            "tp_registered_date": fields.Datetime.now(),
            "tp_registered_by_id": self.admin.id,
        })
        return eq

    def _make_audit_vals(self, employee):
        return [{
            "action": "permanent_delete",
            "employee_ref": employee.id,
            "employee_name": employee.name,
            "employee_code": employee.tp_employee_code,
            "source_code": employee.tp_source_code,
            "company_id": employee.company_id.id,
            "reason": "Test delete",
            "request_id": str(uuid.uuid4()),
            "account_action": "none",
            "snapshot": {},
        }]

    def test_01_equipment_return_on_permanent_delete(self):
        """Held equipment (custody employee & loan) are returned to stock, tech state preserved."""
        employee = self.env["hr.employee"].with_company(self.company).create({
            "name": "Synthetic Delete Asset Holder",
            "company_id": self.company.id,
            "department_id": self.department.id,
        })
        eq_laptop = self._create_equipment("Laptop Dell XPS", custody="employee", employee=employee, tech_state="good")
        eq_monitor = self._create_equipment("Monitor Dell 24", custody="loan", employee=employee, tech_state="broken")

        # 1. Preview
        preview = employee.with_user(self.admin).with_context(allowed_company_ids=[self.company.id]).tp_permanent_delete_preview()
        self.assertTrue(preview["hasAssetsToReturn"])
        self.assertEqual(preview["count"], 1)

        emp_row = preview["employees"][0]
        self.assertEqual(len(emp_row["assetsToReturn"]), 2)
        asset_codes = [a["code"] for a in emp_row["assetsToReturn"]]
        self.assertIn(eq_laptop.tp_code, asset_codes)
        self.assertIn(eq_monitor.tp_code, asset_codes)

        # Confirm no equipment blockers in block list
        for item in emp_row["block"]:
            self.assertNotIn("phiếu bàn giao", item["label"].lower())
            self.assertNotIn("người giữ", item["label"].lower())

        # 2. Execute deletion
        plan = employee._tp_delete_plan()
        audit_vals = self._make_audit_vals(employee)
        employee.with_context(tp_equipment_return_location_id=self.location.id)._tp_permanent_unlink(plan, audit_vals)

        # 3. Assert employee is deleted
        self.assertFalse(employee.exists(), "Employee must be deleted permanently")

        # 4. Assert equipments returned to stock and preserved condition
        eq_laptop.invalidate_recordset()
        eq_monitor.invalidate_recordset()
        self.assertEqual(eq_laptop.tp_custody, "stock")
        self.assertFalse(eq_laptop.tp_employee_id)
        self.assertEqual(eq_laptop.tp_location_id, self.location)
        self.assertEqual(eq_laptop.tp_technical_state, "good", "Tech state 'good' must be preserved")

        self.assertEqual(eq_monitor.tp_custody, "stock")
        self.assertFalse(eq_monitor.tp_employee_id)
        self.assertEqual(eq_monitor.tp_location_id, self.location)
        self.assertEqual(eq_monitor.tp_technical_state, "broken", "Tech state 'broken' must be preserved")

        # 5. Check return moves created
        Move = self.env["tp.equipment.move"]
        moves = Move.search([("company_id", "=", self.company.id), ("state", "=", "done")], order="id desc")
        return_moves = moves.filtered(lambda m: m.move_type in ("return", "loan_return"))
        self.assertTrue(return_moves, "Return moves must be created and done")

    def test_02_history_moves_preserved_when_no_assets_held(self):
        """Historical move documents (Trần Đức Lương scenario) are kept, snapshotted, and unlinked."""
        employee = self.env["hr.employee"].with_company(self.company).create({
            "name": "Synthetic Past Move Actor",
            "company_id": self.company.id,
            "department_id": self.department.id,
        })
        eq = self._create_equipment("Shared Projector", custody="stock")

        # Create past completed move where employee was target
        Move = self.env["tp.equipment.move"]
        past_move = Move.with_context(tp_equipment_move_internal=INTERNAL).create({
            "name": "PBG-SYNTHETIC-001",
            "move_type": "assign",
            "company_id": self.company.id,
            "date": fields.Date.context_today(self),
            "target_custody": "employee",
            "target_employee_id": employee.id,
            "state": "done",
            "line_ids": [(0, 0, {
                "equipment_id": eq.id,
                "from_custody": "stock",
                "to_custody": "employee",
                "to_employee_id": employee.id,
                "done_version": 1,
            })],
        })

        # Create another past completed move where employee was from_employee
        past_return = Move.with_context(tp_equipment_move_internal=INTERNAL).create({
            "name": "PBG-SYNTHETIC-002",
            "move_type": "return",
            "company_id": self.company.id,
            "date": fields.Date.context_today(self),
            "target_location_id": self.location.id,
            "state": "done",
            "line_ids": [(0, 0, {
                "equipment_id": eq.id,
                "from_custody": "employee",
                "from_employee_id": employee.id,
                "to_custody": "stock",
                "to_location_id": self.location.id,
                "done_version": 2,
            })],
        })

        # Preview: 0 held equipment, 0 blockers
        preview = employee.with_user(self.admin).with_context(allowed_company_ids=[self.company.id]).tp_permanent_delete_preview()
        emp_row = preview["employees"][0]
        self.assertEqual(len(emp_row["assetsToReturn"]), 0)
        self.assertFalse(emp_row["block"], "Past moves must NOT block deletion")
        self.assertTrue(len(emp_row["equipmentHistory"]) >= 2, "History moves must be tracked in preview")

        # Execute deletion
        plan = employee._tp_delete_plan()
        audit_vals = self._make_audit_vals(employee)
        employee._tp_permanent_unlink(plan, audit_vals)

        # Assert employee deleted
        self.assertFalse(employee.exists())

        # Assert past moves preserved snapshot
        past_move.invalidate_recordset()
        past_return.invalidate_recordset()
        self.assertFalse(past_move.target_employee_id)
        self.assertTrue(past_move.target_employee_deleted)
        self.assertEqual(past_move.target_employee_name, "Synthetic Past Move Actor")

        line_1 = past_move.line_ids[0]
        self.assertFalse(line_1.to_employee_id)
        self.assertTrue(line_1.to_employee_deleted)
        self.assertEqual(line_1.to_employee_name, "Synthetic Past Move Actor")
        self.assertIn("Synthetic Past Move Actor", line_1.to_text)
        self.assertIn("Nhân viên đã xóa", line_1.to_text)

        line_2 = past_return.line_ids[0]
        self.assertFalse(line_2.from_employee_id)
        self.assertTrue(line_2.from_employee_deleted)
        self.assertEqual(line_2.from_employee_name, "Synthetic Past Move Actor")
        self.assertIn("Synthetic Past Move Actor", line_2.from_text)
        self.assertIn("Nhân viên đã xóa", line_2.from_text)

    def test_03_equipment_transferred_to_other_not_returned(self):
        """Equipment previously used by employee but now held by someone else is NOT returned."""
        emp_a = self.env["hr.employee"].with_company(self.company).create({
            "name": "Synthetic Previous Holder A", "company_id": self.company.id,
        })
        emp_b = self.env["hr.employee"].with_company(self.company).create({
            "name": "Synthetic Current Holder B", "company_id": self.company.id,
        })
        # Eq is currently held by emp_b
        eq = self._create_equipment("Workstation HP", custody="employee", employee=emp_b)

        # Past move line had emp_a as from_employee
        Move = self.env["tp.equipment.move"]
        Move.with_context(tp_equipment_move_internal=INTERNAL).create({
            "name": "PBG-TRANSFER-001",
            "move_type": "transfer",
            "company_id": self.company.id,
            "target_custody": "employee",
            "target_employee_id": emp_b.id,
            "state": "done",
            "line_ids": [(0, 0, {
                "equipment_id": eq.id,
                "from_custody": "employee",
                "from_employee_id": emp_a.id,
                "to_custody": "employee",
                "to_employee_id": emp_b.id,
                "done_version": 1,
            })],
        })

        # Delete emp_a
        plan = emp_a._tp_delete_plan()
        audit_vals = self._make_audit_vals(emp_a)
        emp_a._tp_permanent_unlink(plan, audit_vals)

        # Assert eq remains held by emp_b
        eq.invalidate_recordset()
        self.assertEqual(eq.tp_custody, "employee")
        self.assertEqual(eq.tp_employee_id, emp_b, "Eq must remain with emp_b!")
        self.assertTrue(emp_b.exists())
        self.assertFalse(emp_a.exists())

    def test_04_department_shared_equipment_not_returned(self):
        """Department shared equipment is NOT returned when deleting a department member."""
        emp = self.env["hr.employee"].with_company(self.company).create({
            "name": "Synthetic Dept Member", "company_id": self.company.id, "department_id": self.department.id,
        })
        eq_dept = self._create_equipment("Office Printer Canon", custody="department")

        plan = emp._tp_delete_plan()
        emp_plan = plan["employees"][emp.id]
        self.assertEqual(len(emp_plan["assets_to_return"]), 0)

        audit_vals = self._make_audit_vals(emp)
        emp._tp_permanent_unlink(plan, audit_vals)

        eq_dept.invalidate_recordset()
        self.assertEqual(eq_dept.tp_custody, "department")
        self.assertEqual(eq_dept.tp_holder_department_id, self.department)

    def test_05_pending_move_cancelled_on_delete(self):
        """Pending / draft handover moves for the employee are cancelled to release reservations."""
        emp = self.env["hr.employee"].with_company(self.company).create({
            "name": "Synthetic Pending Handover Recipient", "company_id": self.company.id,
        })
        eq = self._create_equipment("Reserved Monitor", custody="stock")

        Move = self.env["tp.equipment.move"]
        pending_move = Move.with_context(tp_equipment_move_internal=INTERNAL).create({
            "name": "PBG-PENDING-001",
            "move_type": "assign",
            "company_id": self.company.id,
            "target_custody": "employee",
            "target_employee_id": emp.id,
            "state": "pending",
            "line_ids": [(0, 0, {
                "equipment_id": eq.id,
                "condition": "good",
            })],
        })

        plan = emp._tp_delete_plan()
        audit_vals = self._make_audit_vals(emp)
        emp._tp_permanent_unlink(plan, audit_vals)

        pending_move.invalidate_recordset()
        self.assertEqual(pending_move.state, "cancel", "Pending move must be cancelled")
        self.assertIn("Tự động hủy khi xóa vĩnh viễn", pending_move.reason)

    def test_06_personal_equipment_returned_to_owner(self):
        """Personal equipment is released and retired with returned_owner, NOT put in company stock."""
        emp = self.env["hr.employee"].with_company(self.company).create({
            "name": "Synthetic Personal Laptop Owner", "company_id": self.company.id,
        })
        eq_personal = self._create_equipment(
            "Personal MacBook Pro", custody="employee", employee=emp, ownership="personal"
        )

        plan = emp._tp_delete_plan()
        audit_vals = self._make_audit_vals(emp)
        emp._tp_permanent_unlink(plan, audit_vals)

        eq_personal.invalidate_recordset()
        self.assertEqual(eq_personal.tp_lifecycle, "retired")
        self.assertEqual(eq_personal.tp_retire_reason, "returned_owner")
        self.assertFalse(eq_personal.tp_employee_id)
        self.assertNotEqual(eq_personal.tp_custody, "stock", "Personal equipment must NOT be in stock")
