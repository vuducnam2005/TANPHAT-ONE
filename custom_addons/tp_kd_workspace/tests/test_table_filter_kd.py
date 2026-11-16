import io

import openpyxl

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged("post_install", "-at_install")
class TestTableFilterKd(TransactionCase):
    """Verify S2/S3 search views, template priority isolation, financial field security & export parity."""

    def test_01_project_template_isolation_and_kd_task_search(self):
        tmpl_action = self.env.ref("project.open_view_project_template")
        tmpl_search = self.env["project.project"].get_views(
            [(False, "list"), (tmpl_action.search_view_id.id or False, "search")],
        )["views"]["search"]
        self.assertNotEqual(
            tmpl_search.get("id"),
            self.env.ref("tp_kd_workspace.project_search_restructure").id,
            "Native project templates must never leak project_search_restructure.",
        )

        kd_proj_act = self.env.ref("tp_kd_workspace.action_projects")
        self.assertEqual(kd_proj_act.search_view_id.id, self.env.ref("tp_kd_workspace.project_search_restructure").id)

        kd_task_search = self.env.ref("tp_kd_workspace.kd_task_search")
        for action_xmlid in ("tp_kd_workspace.action_wbs", "tp_kd_workspace.action_tasks"):
            act = self.env.ref(action_xmlid)
            self.assertEqual(act.search_view_id.id, kd_task_search.id, action_xmlid)
            arch = self.env["project.task"].get_views([(False, "list"), (kd_task_search.id, "search")])["views"]["search"]["arch"]
            self.assertIn("kd_responsible_id", arch)

    def test_02_all_smart_button_and_native_s3_search_views(self):
        models = (
            "tp.work.item",
            "tp.contract.revision",
            "tp.contract.document",
            "tp.contract.line.amount",
            "tp.contract.audit",
            "tp.project.participation",
            "tp.bid.package.amount",
            "tp.project.update",
            "tp.task.update",
            "tp.kd.document",
            "crm.tag",
            "spreadsheet.dashboard.group",
            "res.company",
            "res.country.group",
        )
        for model_name in models:
            views = self.env[model_name].get_views([(False, "list"), (False, "search")])
            self.assertTrue(views["views"]["search"].get("id"), f"Missing explicit search view for {model_name}")

    def test_03_report_center_invalid_date_and_scoped_export(self):
        company = self.env.company
        dept = self.env["hr.department"].create({"name": "Synthetic Filter KD Dept", "company_id": company.id})
        staff = new_test_user(
            self.env,
            login="test_filter_kd_staff",
            groups="tp_kd_workspace.group_scoped_staff,base.group_allow_export",
        )
        proj = self.env["project.project"].create({
            "name": "Synthetic Filter Project",
            "company_id": company.id,
            "tp_managed": True,
            "tp_department_id": dept.id,
            "tp_code": "SYN-FLT-01",
        })
        assign_vals = {"project_id": proj.id, "user_id": staff.id}
        if "tp_cross_department" in self.env["tp.project.assignment"]._fields:
            assign_vals.update(tp_cross_department=True, tp_cross_department_reason="Synthetic Filter Test")
        self.env["tp.project.assignment"].create(assign_vals)
        self.env["tp.kd.grant"].create({
            "project_id": proj.id,
            "department_id": dept.id,
            "user_id": staff.id,
            "domain": "opportunity",
            "capability": "prepare",
            "reason": "Synthetic Filter Test",
        })

        partner = self.env["res.partner"].create({"name": "Synthetic Filter Partner"})
        contract = self.env["tp.contract"].create({
            "code": "SYN-FLT-HD-01",
            "name": "Hợp đồng kiểm tra lọc báo cáo",
            "project_id": proj.id,
            "company_id": company.id,
            "partner_id": partner.id,
            "contract_type": "owner",
            "lifecycle_state": "not_effective",
        })

        report_model = self.env["tp.kd.report.center"].with_user(staff)
        with self.assertRaises(ValidationError):
            report_model.get_kd_report("R01", {"date_from": "2026-11-20", "date_to": "2026-11-01"})

        res = report_model.get_kd_report("R01", {"project_id": proj.id})
        self.assertEqual(res["pagination"]["total_rows"], 1)
        self.assertEqual(res["rows"][0]["res_id"], contract.id)
        self.assertEqual(res["rows"][0]["original_money"]["state"], "forbidden")

        exported = report_model._build_xlsx_download("R01", {"project_id": proj.id})
        self.assertEqual(exported["row_count"], 1)
        wb = openpyxl.load_workbook(io.BytesIO(exported["content"]), data_only=True)
        ws = wb.active
        self.assertIn("SYN-FLT-HD-01", [str(ws.cell(r, c).value or "") for r in range(1, ws.max_row + 1) for c in range(1, ws.max_column + 1)])
