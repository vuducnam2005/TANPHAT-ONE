# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Backend RBAC, formula consistency, and drilldown alignment tests for UI-HOME-006."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from odoo import Command, fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestHomeDashboard(TransactionCase):
    """Verify live Home KPIs, charts, agenda, global search, and RBAC across roles."""

    @classmethod
    def _restore_employee_sequence(cls, sequence_id, last_value, is_called):
        with cls.registry.cursor() as cr:
            cr.execute(
                "SELECT setval(%s, %s, %s)",
                [f"ir_sequence_{sequence_id:03d}", last_value, is_called],
            )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if "hr.employee" in cls.env and hasattr(cls.env["hr.employee"], "_tp_code_sequence"):
            emp_model = cls.env["hr.employee"]
            seq = emp_model._tp_code_sequence()
            cls.env.cr.execute(f"SELECT last_value, is_called FROM ir_sequence_{seq.id:03d}")
            cls.addClassCleanup(cls._restore_employee_sequence, seq.id, *cls.env.cr.fetchone())
            emp_model._tp_reset_code_sequence(emp_model._tp_code_floor())

        cls.company = cls.env.company
        cls.tz = ZoneInfo("Asia/Ho_Chi_Minh")

        # Original Admin actor (`base.user_admin` complies with tp_admin_delegation guards)
        cls.admin_user = cls.env.ref("base.user_admin")
        if "tp.admin.delegation" in cls.env:
            cls.env["tp.admin.delegation"]._migrate_admin_full_001()

        cls.delegated_user = new_test_user(
            cls.env,
            login="home006.delegated",
            groups="base.group_user",
            company_id=cls.company.id,
        )

        mgr_groups = ["base.group_user"]
        if cls.env.ref("project.group_project_manager", raise_if_not_found=False):
            mgr_groups.append("project.group_project_manager")
        cls.manager_user = new_test_user(
            cls.env,
            login="home006.manager",
            groups=",".join(mgr_groups),
            company_id=cls.company.id,
        )

        cls.emp_a = new_test_user(
            cls.env,
            login="home006.emp_a",
            groups="base.group_user",
            company_id=cls.company.id,
        )
        cls.emp_b = new_test_user(
            cls.env,
            login="home006.emp_b",
            groups="base.group_user",
            company_id=cls.company.id,
        )
        cls.emp_zero = new_test_user(
            cls.env,
            login="home006.zero",
            groups="base.group_user",
            company_id=cls.company.id,
        )
        cls.portal_user = new_test_user(
            cls.env,
            login="home006.portal",
            groups="base.group_portal",
            company_id=cls.company.id,
        )

        for u in (cls.admin_user, cls.delegated_user, cls.manager_user, cls.emp_a, cls.emp_b, cls.emp_zero):
            u.sudo().tz = "Asia/Ho_Chi_Minh"

        # Departments & Employees if hr installed
        cls.dept_kd = False
        cls.dept_tech = False
        if "hr.department" in cls.env and "hr.employee" in cls.env:
            Dept = cls.env["hr.department"].sudo()
            Emp = cls.env["hr.employee"].sudo()
            cls.dept_kd = Dept.create({"name": "Home006 KH-KD", "company_id": cls.company.id})
            cls.dept_tech = Dept.create({"name": "Home006 Kỹ thuật", "company_id": cls.company.id})
            extra = {"date_version": fields.Date.today()} if "date_version" in Emp._fields else {}
            Emp.create({"name": "NV Ủy quyền", "user_id": cls.delegated_user.id, "department_id": cls.dept_kd.id, "company_id": cls.company.id, **extra})
            Emp.create({"name": "NV A", "user_id": cls.emp_a.id, "department_id": cls.dept_kd.id, "company_id": cls.company.id, **extra})
            Emp.create({"name": "NV B", "user_id": cls.emp_b.id, "department_id": cls.dept_tech.id, "company_id": cls.company.id, **extra})
            Emp.create({"name": "Quản lý M", "user_id": cls.manager_user.id, "department_id": cls.dept_kd.id, "company_id": cls.company.id, **extra})

        if "tp.admin.delegation" in cls.env:
            cls.env["tp.admin.delegation"].with_user(cls.admin_user)._change(
                cls.delegated_user,
                cls.company,
                "grant",
                "Test UI-HOME-006 delegated full admin",
            )

        # Remove auto-generated project_todo welcome tasks for synthetic test users so counts start deterministic
        if "project.task" in cls.env:
            cls.env["project.task"].sudo().with_context(active_test=False).search(
                [("user_ids", "in", [cls.emp_a.id, cls.emp_b.id, cls.emp_zero.id])],
            ).unlink()

    def test_portal_and_inactive_users_rejected_on_all_home_rpcs(self):
        inactive_emp = new_test_user(
            self.env, login="home006.inactive", groups="base.group_user", company_id=self.company.id,
        )
        inactive_emp.sudo().active = False

        for bad_user in (self.portal_user, inactive_emp):
            model = self.env["res.users"].with_user(bad_user)
            with self.assertRaises(AccessError):
                model.get_tp_home_dashboard({})
            with self.assertRaises(AccessError):
                model.get_tp_home_agenda_page(1, 10)
            with self.assertRaises(AccessError):
                model.search_tp_home_global("test")
            with self.assertRaises(AccessError):
                model.get_tp_home_hr_drilldown_action()
            with self.assertRaises(AccessError):
                model.get_tp_home_stock_drilldown_action()
            with self.assertRaises(AccessError):
                model.get_tp_home_task_drilldown_action({})

    def test_stock_kpi_strict_rbac_and_exact_drilldown(self):
        if "maintenance.equipment" not in self.env or not hasattr(
            self.env["maintenance.equipment"], "tp_main_summary",
        ):
            self.skipTest("tp_equipment is not installed in this test DB")

        # Regular employee & project manager MUST receive no_access + count=None (NEVER 0)
        for u in (self.emp_a, self.manager_user, self.emp_zero):
            dash = self.env["res.users"].with_user(u).get_tp_home_dashboard({})
            stock = dash["kpis"]["stock"]
            self.assertEqual(stock["status"], "no_access", u.login)
            self.assertIsNone(stock["count"], u.login)
            self.assertFalse(stock["can_open"], u.login)
            with self.assertRaises(AccessError):
                self.env["res.users"].with_user(u).get_tp_home_stock_drilldown_action()

        # Original Admin gets real stock count matching tp_main_summary()['stock']
        admin_dash = self.env["res.users"].with_user(self.admin_user).get_tp_home_dashboard({})
        admin_stock = admin_dash["kpis"]["stock"]
        self.assertEqual(admin_stock["status"], "ok")
        expected_stock = self.env["maintenance.equipment"].with_user(self.admin_user).tp_main_summary()["stock"]
        self.assertEqual(admin_stock["count"], expected_stock)

        act = self.env["res.users"].with_user(self.admin_user).get_tp_home_stock_drilldown_action()
        self.assertEqual(act["res_model"], "maintenance.equipment")
        self.assertEqual(act["context"].get("search_default_seg_stock"), 1)

        # Delegated full admin also gets ok when tp_admin_delegation is active
        if self.env.ref("tp_admin_delegation.group_full_admin", raise_if_not_found=False):
            del_dash = self.env["res.users"].with_user(self.delegated_user).get_tp_home_dashboard({})
            self.assertEqual(del_dash["kpis"]["stock"]["status"], "ok")
            self.assertEqual(del_dash["kpis"]["stock"]["count"], expected_stock)

    def test_hr_kpi_matches_drilldown_count_across_roles(self):
        if "hr.employee" not in self.env:
            self.skipTest("hr is not installed in this test DB")

        for actor in (self.admin_user, self.emp_a):
            dash = self.env["res.users"].with_user(actor).get_tp_home_dashboard({})
            hr_kpi = dash["kpis"]["hr"]
            self.assertEqual(hr_kpi["status"], "ok")
            self.assertIsInstance(hr_kpi["count"], int)
            self.assertGreaterEqual(hr_kpi["count"], 3)

            act = self.env["res.users"].with_user(actor).get_tp_home_hr_drilldown_action()
            res_model = act["res_model"]
            dom = act.get("domain") or []
            drill_count = self.env[res_model].with_user(actor).search_count(dom)
            self.assertEqual(hr_kpi["count"], drill_count, f"HR KPI mismatch for {actor.login}")

    def test_zero_task_and_zero_request_user_renders_valid_zeros(self):
        dash = self.env["res.users"].with_user(self.emp_zero).get_tp_home_dashboard({"period": "all"})
        if "tp.request" in self.env:
            req = dash["kpis"]["requests"]
            self.assertEqual(req["status"], "ok")
            self.assertEqual(req["count"], 0)
            self.assertEqual(req["role_mode"], "mine_pending")

        if "project.task" in self.env:
            tasks_kpi = dash["kpis"]["tasks"]
            self.assertEqual(tasks_kpi["status"], "ok")
            self.assertEqual(tasks_kpi["count"], 0)
            charts = dash["charts"]
            self.assertEqual(charts["status"], "ok")
            self.assertEqual(charts["total"], 0)
            self.assertEqual(charts["donut"]["center_count"], 0)
            self.assertEqual(sum(s["percent"] for s in charts["donut"]["slices"]), 0)
            self.assertEqual(charts["bar"]["rows"], [])

    def test_task_kpi_bar_donut_drilldown_and_privacy_invariants(self):
        if "project.task" not in self.env or "project.project" not in self.env:
            self.skipTest("project is not installed in this test DB")

        Project = self.env["project.project"].sudo()
        Task = self.env["project.task"].sudo()
        today_local = datetime.now(self.tz).date()
        utc = ZoneInfo("UTC")

        due_future = (
            datetime.combine(today_local + timedelta(days=2), time(15, 0), tzinfo=self.tz)
            .astimezone(utc)
            .replace(tzinfo=None)
        )
        due_past = (
            datetime.combine(today_local - timedelta(days=2), time(10, 0), tzinfo=self.tz)
            .astimezone(utc)
            .replace(tzinfo=None)
        )

        proj_vals = {"name": "Home006 Test Project", "company_id": self.company.id, "user_id": self.manager_user.id}
        if self.dept_kd and "tp_department_id" in Project._fields:
            proj_vals["tp_department_id"] = self.dept_kd.id
        proj = Project.create(proj_vals)

        proj_cross = Project.create(
            {"name": "Home006 Unassigned Dept Project", "company_id": self.company.id, "user_id": self.manager_user.id},
        )

        # 1. Completed task
        t_done = Task.create(
            {
                "name": "Home006 Done Task",
                "project_id": proj.id,
                "user_ids": [Command.set([self.emp_a.id])],
                "date_deadline": due_future,
                "state": "1_done",
            },
        )
        # 2. Overdue task
        t_overdue = Task.create(
            {
                "name": "Home006 Overdue Task",
                "project_id": proj.id,
                "user_ids": [Command.set([self.emp_a.id])],
                "date_deadline": due_past,
                "state": "01_in_progress",
            },
        )
        # 3. Cross-department multi-assignee task (must be counted ONCE in cross_dept, never twice)
        t_cross = Task.create(
            {
                "name": "Home006 Cross Dept Task",
                "project_id": proj_cross.id,
                "user_ids": [Command.set([self.emp_a.id, self.emp_b.id])],
                "date_deadline": due_future,
                "state": "01_in_progress",
            },
        )
        # 4. Reported-done task (if tp_personal_tools installed) must stay in 'waiting', NOT 'done'
        t_reported_vals = {
            "name": "Home006 Reported Done Awaiting Verify",
            "project_id": proj.id,
            "user_ids": [Command.set([self.emp_a.id])],
            "date_deadline": due_future,
            "state": "01_in_progress",
        }
        if "tp_exec_report_state" in Task._fields:
            t_reported_vals["tp_exec_report_state"] = "reported_done"
        else:
            t_reported_vals["state"] = "04_waiting_normal"
        t_waiting = Task.create(t_reported_vals)

        # 5. Private personal task of emp_b (project_id = False) — MUST NEVER appear in Admin's managed scope!
        t_private_b = Task.create(
            {
                "name": "Home006 Secret Personal Todo of B",
                "project_id": False,
                "user_ids": [Command.set([self.emp_b.id])],
                "date_deadline": due_future,
                "state": "01_in_progress",
            },
        )

        # Verify Admin managed scope invariants
        admin_dash = self.env["res.users"].with_user(self.admin_user).get_tp_home_dashboard({"period": "all", "task_scope": "managed"})
        kpi_cnt = admin_dash["kpis"]["tasks"]["count"]
        charts = admin_dash["charts"]
        self.assertEqual(kpi_cnt, charts["total"])
        self.assertEqual(kpi_cnt, charts["donut"]["center_count"])
        self.assertEqual(kpi_cnt, sum(s["count"] for s in charts["donut"]["slices"]))
        self.assertEqual(kpi_cnt, sum(r["total_count"] for r in charts["bar"]["rows"]))
        if kpi_cnt > 0:
            self.assertEqual(sum(s["percent"] for s in charts["donut"]["slices"]), 100)

        drill_all = self.env["res.users"].with_user(self.admin_user).get_tp_home_task_drilldown_action(
            {"period": "all", "task_scope": "managed"},
        )
        drill_ids = set(self.env["project.task"].with_user(self.admin_user).search(drill_all["domain"]).ids)
        self.assertEqual(len(drill_ids), kpi_cnt)
        self.assertTrue({t_done.id, t_overdue.id, t_cross.id, t_waiting.id}.issubset(drill_ids))
        # Private personal task of emp_b is strictly excluded from Admin's managed scope
        self.assertNotIn(t_private_b.id, drill_ids)

        # Verify reported_done/waiting task is in 'waiting' donut bucket, not 'done'
        drill_waiting = self.env["res.users"].with_user(self.admin_user).get_tp_home_task_drilldown_action(
            {"period": "all", "task_scope": "managed", "donut_bucket": "waiting"},
        )
        waiting_ids = set(self.env["project.task"].with_user(self.admin_user).search(drill_waiting["domain"]).ids)
        self.assertIn(t_waiting.id, waiting_ids)

        # Verify cross-department task is attributed to 'cross_dept' when departments exist
        if self.dept_kd and self.dept_tech:
            drill_cross = self.env["res.users"].with_user(self.admin_user).get_tp_home_task_drilldown_action(
                {"period": "all", "task_scope": "managed", "bar_department_key": "cross_dept"},
            )
            cross_ids = set(self.env["project.task"].with_user(self.admin_user).search(drill_cross["domain"]).ids)
            self.assertIn(t_cross.id, cross_ids)

        # Verify Employee A sees only my_work scope (cannot escalate to managed via RPC param)
        emp_dash = self.env["res.users"].with_user(self.emp_a).get_tp_home_dashboard(
            {"period": "all", "task_scope": "managed"},
        )
        self.assertEqual(emp_dash["charts"]["scope_key"], "my_work")
        self.assertFalse(emp_dash["charts"]["can_filter_department"])
        self.assertEqual(emp_dash["kpis"]["tasks"]["count"], 4)

    def test_today_agenda_timezone_and_event_task_deduplication(self):
        if "calendar.event" not in self.env or "project.task" not in self.env:
            self.skipTest("calendar or project is not installed in this test DB")

        today_local = datetime.now(self.tz).date()
        utc = ZoneInfo("UTC")
        ev_start = datetime.combine(today_local, time(14, 0), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None)
        ev_stop = datetime.combine(today_local, time(15, 0), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None)
        task_dl = datetime.combine(today_local, time(16, 30), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None)

        t_linked = self.env["project.task"].sudo().create(
            {
                "name": "Home006 Linked Task Today",
                "project_id": False,
                "user_ids": [Command.set([self.emp_a.id])],
                "date_deadline": task_dl,
            },
        )
        t_standalone = self.env["project.task"].sudo().create(
            {
                "name": "Home006 Standalone Task Today",
                "project_id": False,
                "user_ids": [Command.set([self.emp_a.id])],
                "date_deadline": task_dl,
            },
        )
        ev = self.env["calendar.event"].sudo().create(
            {
                "name": "Home006 Họp liên kết việc",
                "user_id": self.emp_a.id,
                "partner_ids": [Command.set([self.emp_a.partner_id.id])],
                "start": ev_start,
                "stop": ev_stop,
                "res_model_id": self.env["ir.model"]._get_id("project.task"),
                "res_id": t_linked.id,
            },
        )

        dash = self.env["res.users"].with_user(self.emp_a).get_tp_home_dashboard({})
        agenda = dash["agenda"]
        self.assertEqual(agenda["status"], "ok")
        uid_keys = [i["uid_key"] for i in agenda["items"]]
        # Event is shown with linked_task; t_linked is NOT duplicated as a separate task row!
        self.assertIn(f"event-{ev.id}", uid_keys)
        self.assertNotIn(f"task-{t_linked.id}", uid_keys)
        self.assertIn(f"task-{t_standalone.id}", uid_keys)

        ev_item = next(i for i in agenda["items"] if i["uid_key"] == f"event-{ev.id}")
        self.assertEqual(ev_item["time_label"], "14:00 – 15:00")
        self.assertEqual(ev_item["linked_task"]["id"], t_linked.id)

        page_data = self.env["res.users"].with_user(self.emp_a).get_tp_home_agenda_page(1, 10)
        self.assertEqual(page_data["total"], agenda["total_today"])

    def test_global_document_search_validation_and_permission_isolation(self):
        with self.assertRaises(ValidationError):
            self.env["res.users"].with_user(self.emp_a).search_tp_home_global("x" * 121)

        empty = self.env["res.users"].with_user(self.emp_a).search_tp_home_global("   ")
        self.assertEqual(empty, {"documents": []})

        if "tp.request" in self.env and "tp.request.type" in self.env:
            rtype = self.env["tp.request.type"].sudo().search([("active", "=", True)], limit=1)
            if rtype:
                secret_req = self.env["tp.request"].with_user(self.emp_b).create(
                    {
                        "title": "HOME006_SECRET_REQ_B_ONLY",
                        "type_id": rtype.id,
                    },
                )
                # emp_b sees own draft request in search; unrelated emp_a NEVER sees it
                hits_b = self.env["res.users"].with_user(self.emp_b).search_tp_home_global("HOME006_SECRET_REQ_B_ONLY")
                hits_a = self.env["res.users"].with_user(self.emp_a).search_tp_home_global("HOME006_SECRET_REQ_B_ONLY")
                self.assertTrue(any(d["key"] == f"req-{secret_req.id}" for d in hits_b["documents"]))
                self.assertEqual(hits_a["documents"], [])
