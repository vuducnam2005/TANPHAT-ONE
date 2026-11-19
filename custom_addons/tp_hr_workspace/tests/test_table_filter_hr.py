from io import BytesIO

from openpyxl import load_workbook

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestTableFilterHr(HttpCase):
    """Verify S1/S3 HR search views, contextual isolation, and Overview <-> Export parity."""

    def test_01_specialized_employee_and_catalog_search_views(self):
        actions = [
            ("tp_hr_workspace.action_missing", "hr.employee", "tp_hr_workspace.missing_employee_search"),
            ("tp_hr_workspace.action_archived", "hr.employee", "tp_hr_workspace.archived_employee_search"),
            ("tp_hr_workspace.action_pending", "hr.employee", "tp_hr_workspace.pending_employee_search"),
            ("tp_hr_workspace.action_locations", "hr.work.location", "tp_hr_workspace.hr_work_location_search"),
            ("tp_hr_workspace.action_categories", "hr.employee.category", "tp_hr_workspace.hr_employee_category_search"),
            ("tp_hr_workspace.action_resume_types", "hr.resume.line.type", "tp_hr_workspace.hr_resume_type_search"),
            ("tp_hr_workspace.action_skill_types", "hr.skill.type", "tp_hr_workspace.hr_skill_type_search"),
            ("tp_hr_workspace.action_employee_audit", "tp.hr.employee.audit", "tp_hr_workspace.hr_employee_audit_search"),
        ]
        for action_xmlid, model_name, expected_search_xmlid in actions:
            action = self.env.ref(action_xmlid)
            self.assertEqual(action.search_view_id.id, self.env.ref(expected_search_xmlid).id, action_xmlid)
            views = self.env[model_name].get_views([(False, "list"), (action.search_view_id.id, "search")])
            arch = views["views"]["search"]["arch"]
            self.assertIn("<search", arch)
            if action_xmlid == "tp_hr_workspace.action_pending":
                self.assertNotIn("tp_account_status", arch)
            if action_xmlid == "tp_hr_workspace.action_missing":
                self.assertIn("miss_code", arch)

        # Models without explicit act_window search_view_id must still resolve custom non-AUTO search views.
        for model_name in (
            "tp.hr.import.line",
            "tp.hr.contract.document",
            "hr.employee.type",
            "hr.departure.reason",
            "calendar.calendar",
            "calendar.event.type",
        ):
            views = self.env[model_name].get_views([(False, "list"), (False, "search")])
            self.assertTrue(views["views"]["search"].get("id"), f"Missing search view id for {model_name}")

        # Training attendances inherit hr_skills.view_resume_lines_filter cleanly.
        training_act = self.env.ref("hr_skills.hr_resume_lines_training_action")
        views = self.env["hr.resume.line"].get_views([(False, "list"), (training_act.search_view_id.id, "search")])
        self.assertIn("employee_id", views["views"]["search"]["arch"])
        self.assertIn("course_type", views["views"]["search"]["arch"])

    def test_02_hr_overview_export_matches_filtered_population(self):
        company = self.env.company
        dept = self.env["hr.department"].create({"name": "Synthetic Filter Dept", "company_id": company.id})
        emp_a = self.env["hr.employee"].create({
            "name": "Synthetic Export One",
            "company_id": company.id,
            "department_id": dept.id,
            "tp_employment_kind": "long_term",
        })
        self.env["hr.employee"].create({
            "name": "Synthetic Export Two",
            "company_id": company.id,
            "department_id": dept.id,
            "tp_employment_kind": "outsourced",
        })
        overview = self.env["tp.hr.workspace"].get_overview({
            "department_id": dept.id,
            "employment_kind": "long_term",
            "status": "active",
        })
        self.assertEqual(overview["total"], 1)

        self.authenticate("admin", "admin")
        resp = self.url_open(f"/tp_hr/export?department_id={dept.id}&employment_kind=long_term&status=active")
        self.assertEqual(resp.status_code, 200)
        wb = load_workbook(BytesIO(resp.content), data_only=True)
        ws = wb["Danh sách nhân viên"]
        names = [row[2] for row in ws.iter_rows(min_row=7, values_only=True) if isinstance(row[0], int)]
        self.assertEqual(names, [emp_a.name])

        # Non-HR user must still fail overview backend permission check
        non_hr = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Staff No HR",
            "login": "staff_no_hr_tf001",
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        with self.assertRaises(AccessError):
            self.env["tp.hr.workspace"].with_user(non_hr).get_overview()
