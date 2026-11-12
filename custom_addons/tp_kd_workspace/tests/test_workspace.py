from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged("post_install", "-at_install")
class TestKdWorkspace(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.department = cls.env["hr.department"].create(
            {"name": "KD synthetic", "company_id": cls.env.company.id},
        )
        cls.partner = cls.env["res.partner"].create({"name": "Khách hàng tổng hợp"})
        cls.project = cls.env["project.project"].create(
            {
                "name": "Cầu thử nghiệm",
                "tp_code": "KD-AT-A",
                "tp_managed": True,
                "tp_department_id": cls.department.id,
                "partner_id": cls.partner.id,
                "company_id": cls.env.company.id,
                "privacy_visibility": "employees",
            },
        )
        cls.other = cls.env["project.project"].create(
            {
                "name": "Ngoài phạm vi",
                "tp_code": "KD-AT-B",
                "tp_managed": True,
                "tp_department_id": cls.department.id,
                "company_id": cls.env.company.id,
            },
        )
        cls.editor = new_test_user(
            cls.env,
            login="kd_unit_editor",
            groups="tp_core.group_user,sales_team.group_sale_salesman_all_leads",
        )
        cls.reader = new_test_user(
            cls.env,
            login="kd_unit_reader",
            groups="tp_core.group_user,sales_team.group_sale_salesman_all_leads",
        )
        cls.planner = new_test_user(
            cls.env,
            login="kd_unit_planner",
            groups="tp_core.group_manager",
        )
        for user in (cls.editor, cls.reader):
            values = {"project_id": cls.project.id, "user_id": user.id}
            if 'tp_cross_department' in cls.env['tp.project.assignment']._fields:
                user.group_ids = [Command.link(cls.env.ref('tp_kd_workspace.group_scoped_staff').id)]
                values.update(tp_cross_department=True, tp_cross_department_reason='Synthetic explicit workspace scope')
            cls.env["tp.project.assignment"].create(values)
        cls.grant = cls.env["tp.kd.grant"].create(
            {
                "project_id": cls.project.id,
                "department_id": cls.department.id,
                "user_id": cls.editor.id,
                "domain": "opportunity",
                "capability": "prepare",
                "reason": "Synthetic acceptance",
            },
        )
        cls.env['tp.kd.grant'].create({'project_id': cls.project.id, 'department_id': cls.department.id,
            'user_id': cls.editor.id, 'domain': 'opportunity', 'capability': 'submit', 'reason': 'Synthetic explicit submit'})

    def lead(self):
        return (
            self.env["crm.lead"]
            .with_user(self.editor)
            .create(
                {
                    "name": "Cơ hội tổng hợp",
                    "type": "opportunity",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                    "tp_project_id": self.project.id,
                    "user_id": self.editor.id,
                    "kd_source": "Tình huống tổng hợp",
                    "kd_scope": "Khảo sát cầu",
                    "kd_deadline": "2026-11-30",
                    "kd_checklist": "Phạm vi; tiến độ; năng lực",
                },
            )
        )

    def test_project_child_actions_do_not_reuse_parent_form_or_defaults(self):
        project = self.project.with_user(self.editor).with_context(
            form_view_ref="tp_kd_workspace.project_form",
            default_tp_managed=True,
            search_default_parent_only=1,
            active_model="project.project",
            active_id=self.project.id,
        )
        for method in (
            "action_kd_allocations", "action_kd_productions", "action_kd_acceptances",
            "action_kd_payments", "action_kd_plans", "action_kd_credentials",
            "action_kd_obligations", "action_kd_opportunities", "action_kd_tasks", "action_kd_contracts",
        ):
            action = getattr(project, method)()
            context = action["context"]
            self.assertNotEqual(context.get("form_view_ref"), "tp_kd_workspace.project_form")
            for key in ("default_tp_managed", "search_default_parent_only", "active_model", "active_id"):
                self.assertNotIn(key, context)
            key = "default_tp_project_id" if action["res_model"] == "crm.lead" else "default_project_id"
            self.assertEqual(context[key], self.project.id)

    def test_bid_actions_and_direct_route(self):
        lead = self.lead()
        with self.assertRaises(UserError):
            lead.write({"kd_bid_state": "submitted"})
        lead.action_kd_prepare()
        self.assertEqual(lead.kd_bid_state, "preparation")
        with self.assertRaises(UserError):
            lead.action_kd_record_submission()
        lead.kd_receipt = "Ghi chú nội bộ chưa xác minh"
        lead.action_kd_record_submission()
        lead.action_kd_record_submission()
        self.assertEqual(lead.kd_bid_state, "submitted")
        direct = self.lead()
        direct.kd_route = "direct"
        direct.action_kd_prepare()
        with self.assertRaises(UserError):
            direct.action_kd_record_submission()

    def test_scope_grant_revoke_and_forged_state(self):
        lead = self.lead()
        with self.assertRaises(AccessError):
            lead.with_user(self.reader).write({"kd_scope": "khác"})
        with self.assertRaises(AccessError):
            lead.write({"tp_project_id": self.other.id})
        self.grant.active = False
        with self.assertRaises(AccessError):
            lead.action_kd_prepare()
        with self.assertRaises(UserError):
            self.env["crm.lead"].create({"name": "Forged", "kd_bid_state": "submitted"})

    def test_project_navigation_and_task_policy(self):
        project = self.project.with_user(self.editor)
        self.assertEqual(
            project.action_kd_opportunities()["domain"],
            [("tp_project_id", "=", project.id)],
        )
        action = project.action_kd_contracts()
        self.assertEqual(action["domain"], [("project_id", "=", project.id)])
        task = (
            self.env["project.task"]
            .with_user(self.planner)
            .create(
                {
                    "name": "Đầu việc",
                    "project_id": project.id,
                    "user_ids": [Command.set(self.editor.ids)],
                    "kd_deliverable": "Bộ hồ sơ",
                },
            )
        )
        with self.assertRaises(AccessError):
            task.with_user(self.editor).write({"state": "1_done"})
        task.with_user(self.planner).write({"kd_deliverable": "Đầu ra đã chỉnh"})
        self.assertEqual(task.kd_deliverable, "Đầu ra đã chỉnh")

    def test_grants_not_self_manageable(self):
        with self.assertRaises(AccessError):
            self.grant.with_user(self.editor).write({"capability": "review"})
        self.grant.date_end = "2000-01-01"
        self.assertFalse(
            self.env["tp.kd.grant"]
            .with_user(self.editor)
            ._has(self.project, "opportunity", "prepare"),
        )
