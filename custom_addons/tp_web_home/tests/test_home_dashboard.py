# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Backend RBAC, 13-scenario Employee/Admin mode, formula, and drilldown tests (UI-HOME-006 / UI-HOME-007)."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from odoo import Command, fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged

try:
    from odoo.addons.tp_hr_attendance.models.attendance_common import (
        internal as att_internal,
    )
except ImportError:
    att_internal = None


@tagged("post_install", "-at_install")
class TestHomeDashboard(TransactionCase):
    """Verify Admin & Employee Home modes, 4 personal cards, daily bars, RBAC, and grant/revoke transitions."""

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

        cls.admin_user = cls.env.ref("base.user_admin")
        if "tp.admin.delegation" in cls.env:
            cls.env["tp.admin.delegation"]._migrate_admin_full_001()

        cls.delegated_user = new_test_user(
            cls.env,
            login="home007.delegated",
            groups="base.group_user",
            company_id=cls.company.id,
        )

        mgr_groups = ["base.group_user"]
        if cls.env.ref("project.group_project_manager", raise_if_not_found=False):
            mgr_groups.append("project.group_project_manager")
        if cls.env.ref("tp_request.group_request_manager", raise_if_not_found=False):
            mgr_groups.append("tp_request.group_request_manager")
        cls.manager_user = new_test_user(
            cls.env,
            login="home007.manager",
            groups=",".join(mgr_groups),
            company_id=cls.company.id,
        )

        cls.emp_a = new_test_user(
            cls.env,
            login="home007.emp_a",
            groups="base.group_user",
            company_id=cls.company.id,
        )
        cls.emp_b = new_test_user(
            cls.env,
            login="home007.emp_b",
            groups="base.group_user",
            company_id=cls.company.id,
        )
        cls.emp_zero = new_test_user(
            cls.env,
            login="home007.zero",
            groups="base.group_user",
            company_id=cls.company.id,
        )
        # Internal user intentionally NOT linked to any hr.employee (even with matching name!)
        cls.emp_unlinked = new_test_user(
            cls.env,
            login="home007.unlinked",
            name="NV A",
            groups="base.group_user",
            company_id=cls.company.id,
        )
        cls.portal_user = new_test_user(
            cls.env,
            login="home007.portal",
            groups="base.group_portal",
            company_id=cls.company.id,
        )

        for u in (
            cls.admin_user,
            cls.delegated_user,
            cls.manager_user,
            cls.emp_a,
            cls.emp_b,
            cls.emp_zero,
            cls.emp_unlinked,
        ):
            u.sudo().tz = "Asia/Ho_Chi_Minh"

        cls.dept_kd = False
        cls.dept_tech = False
        cls.emp_rec_a = False
        if "hr.department" in cls.env and "hr.employee" in cls.env:
            Dept = cls.env["hr.department"].sudo()
            Emp = cls.env["hr.employee"].sudo()
            cls.dept_kd = Dept.create({"name": "Home007 KH-KD", "company_id": cls.company.id})
            cls.dept_tech = Dept.create({"name": "Home007 Kỹ thuật", "company_id": cls.company.id})
            extra = {"date_version": fields.Date.today()} if "date_version" in Emp._fields else {}
            Emp.create({"name": "NV Ủy quyền", "user_id": cls.delegated_user.id, "department_id": cls.dept_kd.id, "company_id": cls.company.id, **extra})
            cls.emp_rec_a = Emp.create({"name": "NV A", "user_id": cls.emp_a.id, "department_id": cls.dept_kd.id, "company_id": cls.company.id, **extra})
            Emp.create({"name": "NV B", "user_id": cls.emp_b.id, "department_id": cls.dept_tech.id, "company_id": cls.company.id, **extra})
            Emp.create({"name": "NV Zero", "user_id": cls.emp_zero.id, "department_id": cls.dept_tech.id, "company_id": cls.company.id, **extra})
            Emp.create({"name": "Quản lý M", "user_id": cls.manager_user.id, "department_id": cls.dept_kd.id, "company_id": cls.company.id, **extra})

        if "tp.admin.delegation" in cls.env:
            cls.env["tp.admin.delegation"].with_user(cls.admin_user)._change(
                cls.delegated_user,
                cls.company,
                "grant",
                "Test UI-HOME-007 delegated full admin",
            )

        if "project.task" in cls.env:
            cls.env["project.task"].sudo().with_context(active_test=False).search(
                [
                    (
                        "user_ids",
                        "in",
                        [cls.emp_a.id, cls.emp_b.id, cls.emp_zero.id, cls.emp_unlinked.id, cls.manager_user.id],
                    ),
                ],
            ).unlink()

    def test_01_portal_and_inactive_users_rejected_on_all_home_rpcs(self):
        inactive_emp = new_test_user(
            self.env, login="home007.inactive", groups="base.group_user", company_id=self.company.id,
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
            with self.assertRaises(AccessError):
                model.get_tp_home_calendar_drilldown_action()

    def test_02_admin_original_delegated_and_grant_revoke_mode_switch(self):
        """Scenarios 1, 2, 7, 10: Original Admin & Delegated Admin get Admin Home; Employee never gets Stock; revoke switches mode."""
        admin_dash = self.env["res.users"].with_user(self.admin_user).get_tp_home_dashboard({})
        self.assertEqual(admin_dash["home_mode"], "admin")
        self.assertEqual(admin_dash["apps_title"], "Ứng dụng theo phòng ban")
        self.assertEqual([c["key"] for c in admin_dash["cards"]], ["hr", "requests", "tasks", "stock"])
        self.assertEqual(admin_dash["charts"]["bar"]["kind"], "department")
        self.assertEqual(admin_dash["charts"]["period_key"], "this_month")

        if "maintenance.equipment" in self.env and hasattr(self.env["maintenance.equipment"], "tp_main_summary"):
            expected_stock = self.env["maintenance.equipment"].with_user(self.admin_user).tp_main_summary()["stock"]
            self.assertEqual(admin_dash["kpis"]["stock"]["status"], "ok")
            self.assertEqual(admin_dash["kpis"]["stock"]["count"], expected_stock)

        # Employee & Manager: home_mode == 'employee', NEVER receives Stock KPI, direct Stock drilldown blocked
        for non_admin in (self.emp_a, self.manager_user, self.emp_zero):
            dash = self.env["res.users"].with_user(non_admin).get_tp_home_dashboard(
                {"home_mode": "admin", "user_id": self.admin_user.id, "task_scope": "managed"},
            )
            self.assertEqual(dash["home_mode"], "employee", non_admin.login)
            self.assertEqual(dash["apps_title"], "Ứng dụng của bạn", non_admin.login)
            self.assertNotIn("stock", dash["kpis"], non_admin.login)
            self.assertEqual(
                [c["key"] for c in dash["cards"]],
                ["emp_tasks", "emp_requests", "emp_calendar", "emp_attendance"],
            )
            self.assertEqual(dash["charts"]["mode"], "employee")
            self.assertEqual(dash["charts"]["scope_key"], "my_work")
            self.assertEqual(dash["charts"]["bar"]["kind"], "daily")
            self.assertEqual(dash["charts"]["period_key"], "this_week")
            if "maintenance.equipment" in self.env:
                with self.assertRaises(AccessError):
                    self.env["res.users"].with_user(non_admin).get_tp_home_stock_drilldown_action()

        # Delegated Admin live grant -> Admin mode; after revoke -> immediately Employee mode!
        if "tp.admin.delegation" in self.env and self.env.ref("tp_admin_delegation.group_full_admin", raise_if_not_found=False):
            del_dash = self.env["res.users"].with_user(self.delegated_user).get_tp_home_dashboard({})
            self.assertEqual(del_dash["home_mode"], "admin")
            self.assertIn("stock", del_dash["kpis"])

            self.env["tp.admin.delegation"].with_user(self.admin_user)._change(
                self.delegated_user,
                self.company,
                "revoke",
                "Revoke test UI-HOME-007",
            )
            revoked_dash = self.env["res.users"].with_user(self.delegated_user).get_tp_home_dashboard(
                {"home_mode": "admin", "task_scope": "managed"},
            )
            self.assertEqual(revoked_dash["home_mode"], "employee")
            self.assertNotIn("stock", revoked_dash["kpis"])
            self.assertEqual(revoked_dash["charts"]["scope_key"], "my_work")

    def test_03_employee_zero_data_and_unlinked_employee_attendance(self):
        """Scenarios 4, 5: Zero-data employee gets honest 0s & empty chart; unlinked user gets clear message & never matches by name."""
        zero_dash = self.env["res.users"].with_user(self.emp_zero).get_tp_home_dashboard({})
        self.assertEqual(zero_dash["home_mode"], "employee")
        if "project.task" in self.env:
            self.assertEqual(zero_dash["kpis"]["emp_tasks"]["count"], 0)
            self.assertEqual(zero_dash["charts"]["total"], 0)
            self.assertEqual(zero_dash["charts"]["donut"]["center_count"], 0)
            self.assertEqual(sum(s["percent"] for s in zero_dash["charts"]["donut"]["slices"]), 0)
            self.assertEqual(zero_dash["charts"]["bar"]["rows"], [])
        if "tp.request" in self.env:
            self.assertEqual(zero_dash["kpis"]["emp_requests"]["count"], 0)
        if "calendar.event" in self.env:
            self.assertEqual(zero_dash["kpis"]["emp_calendar"]["count"], 0)

        # Unlinked account named "NV A" MUST NOT match NV A's employee record by name!
        unlinked_dash = self.env["res.users"].with_user(self.emp_unlinked).get_tp_home_dashboard({})
        att_card = unlinked_dash["kpis"]["emp_attendance"]
        if "tp.hr.attendance.day" in self.env:
            self.assertEqual(att_card["status"], "unlinked_employee")
            self.assertEqual(att_card["display_text"], "Chưa xác định hồ sơ nhân viên")
            self.assertIsNone(att_card["count"])

    def test_04_employee_attendance_today_never_uses_yesterday_and_reuses_presence(self):
        """Scenario 3 & Section 4.4: Today's attendance shows real check-in/out; yesterday's punch never masquerades as today."""
        if "tp.hr.attendance.event" not in self.env or not self.emp_rec_a:
            self.skipTest("tp_hr_attendance is not installed")

        today_local = datetime.now(self.tz).date()
        yesterday = today_local - timedelta(days=1)
        utc = ZoneInfo("UTC")

        Event = self.env["tp.hr.attendance.event"].sudo()
        Source = self.env["tp.hr.attendance.source"].sudo()
        if att_internal:
            Event = att_internal(Event)
            Source = att_internal(Source)
        src = Source.create(
            {
                "name": "Home007 Device Source",
                "company_id": self.company.id,
                "namespace": "home007-test",
            },
        )
        now_rx = fields.Datetime.now()
        # Yesterday completed punches only -> Today MUST NOT show 'Đã về' or yesterday's hours!
        Event.create(
            [
                {
                    "source_id": src.id,
                    "employee_id": self.emp_rec_a.id,
                    "namespace": "home007-test",
                    "source_event_id": "y_in",
                    "external_code": "H007A",
                    "timestamp": datetime.combine(yesterday, time(8, 15), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None),
                    "tz": "Asia/Ho_Chi_Minh",
                    "local_date": yesterday,
                    "direction": "IN",
                    "received_at": now_rx,
                    "fingerprint": "h007_y_in",
                    "state": "mapped",
                },
                {
                    "source_id": src.id,
                    "employee_id": self.emp_rec_a.id,
                    "namespace": "home007-test",
                    "source_event_id": "y_out",
                    "external_code": "H007A",
                    "timestamp": datetime.combine(yesterday, time(17, 10), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None),
                    "tz": "Asia/Ho_Chi_Minh",
                    "local_date": yesterday,
                    "direction": "OUT",
                    "received_at": now_rx,
                    "fingerprint": "h007_y_out",
                    "state": "mapped",
                },
            ],
        )
        dash_before = self.env["res.users"].with_user(self.emp_a).get_tp_home_dashboard({})
        att_before = dash_before["kpis"]["emp_attendance"]
        self.assertNotIn(att_before["display_text"], ("Đang làm", "Đã về"))
        self.assertEqual(att_before.get("in_time") or "", "")

        # Today IN punch -> 'Đang làm' + 'Vào: 08:26'
        Event.create(
            {
                "source_id": src.id,
                "employee_id": self.emp_rec_a.id,
                "namespace": "home007-test",
                "source_event_id": "t_in",
                "external_code": "H007A",
                "timestamp": datetime.combine(today_local, time(8, 26), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None),
                "tz": "Asia/Ho_Chi_Minh",
                "local_date": today_local,
                "direction": "IN",
                "received_at": now_rx,
                "fingerprint": "h007_t_in",
                "state": "mapped",
            },
        )
        dash_working = self.env["res.users"].with_user(self.emp_a).get_tp_home_dashboard({})
        att_working = dash_working["kpis"]["emp_attendance"]
        self.assertEqual(att_working["display_text"], "Đang làm")
        self.assertEqual(att_working["badge_text"], "Vào: 08:26")

        # Today OUT punch -> 'Đã về' + '08:26 - 17:03'
        Event.create(
            {
                "source_id": src.id,
                "employee_id": self.emp_rec_a.id,
                "namespace": "home007-test",
                "source_event_id": "t_out",
                "external_code": "H007A",
                "timestamp": datetime.combine(today_local, time(17, 3), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None),
                "tz": "Asia/Ho_Chi_Minh",
                "local_date": today_local,
                "direction": "OUT",
                "received_at": now_rx,
                "fingerprint": "h007_t_out",
                "state": "mapped",
            },
        )
        dash_out = self.env["res.users"].with_user(self.emp_a).get_tp_home_dashboard({})
        att_out = dash_out["kpis"]["emp_attendance"]
        self.assertEqual(att_out["display_text"], "Đã về")
        self.assertEqual(att_out["badge_text"], "08:26 – 17:03")

    def test_05_employee_personal_tasks_verification_daily_bars_and_drilldowns(self):
        """Scenarios 3, 6, 9, 11: Employee incomplete KPI vs Donut total, reported_done & personal Kanban column, daily bars & undated bar."""
        if "project.task" not in self.env or "project.project" not in self.env:
            self.skipTest("project is not installed")

        Project = self.env["project.project"].sudo()
        Task = self.env["project.task"].sudo()
        today_local = datetime.now(self.tz).date()
        week_start = today_local - timedelta(days=today_local.weekday())
        utc = ZoneInfo("UTC")

        day1_dl = datetime.combine(week_start, time(15, 0), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None)
        day2_dl = datetime.combine(week_start + timedelta(days=1), time(16, 0), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None)

        proj = Project.create({"name": "Home007 Project", "company_id": self.company.id, "user_id": self.manager_user.id})

        # 1. Completed task in this week
        t_done = Task.create(
            {
                "name": "H007 Done Task",
                "project_id": proj.id,
                "user_ids": [Command.set([self.emp_a.id, self.emp_b.id])],
                "date_deadline": day1_dl,
                "state": "1_done",
            },
        )
        # 2. Reported-done task awaiting verification -> MUST NOT count as completed!
        t_rep_vals = {
            "name": "H007 Reported Done Pending Verify",
            "project_id": proj.id,
            "user_ids": [Command.set([self.emp_a.id])],
            "date_deadline": day2_dl,
            "state": "01_in_progress",
        }
        if "tp_exec_report_state" in Task._fields:
            t_rep_vals["tp_exec_report_state"] = "reported_done"
        else:
            t_rep_vals["state"] = "04_waiting_normal"
        t_reported = Task.create(t_rep_vals)

        # 3. Undated personal task dragged into personal Kanban column named 'Hoàn thành' -> STILL incomplete, in 'undated' bar!
        t_undated = Task.create(
            {
                "name": "H007 Undated In Personal Done Column",
                "project_id": False,
                "user_ids": [Command.set([self.emp_a.id])],
                "date_deadline": False,
                "state": "01_in_progress",
            },
        )
        if "project.task.stage.personal" in self.env:
            done_personal_stage = (
                self.env["project.task.type"]
                .sudo()
                .create({"name": "Hoàn thành", "user_id": self.emp_a.id})
            )
            rel = self.env["project.task.stage.personal"].sudo().search(
                [("user_id", "=", self.emp_a.id), ("task_id", "=", t_undated.id)], limit=1,
            )
            if rel:
                rel.write({"stage_id": done_personal_stage.id})
            else:
                self.env["project.task.stage.personal"].sudo().create(
                    {"user_id": self.emp_a.id, "task_id": t_undated.id, "stage_id": done_personal_stage.id},
                )

        # 4. Private task of emp_b -> isolated from emp_a!
        Task.create(
            {
                "name": "H007 Private Task of B",
                "project_id": False,
                "user_ids": [Command.set([self.emp_b.id])],
                "date_deadline": day1_dl,
                "state": "01_in_progress",
            },
        )

        dash_a = self.env["res.users"].with_user(self.emp_a).get_tp_home_dashboard({"period": "this_week"})
        emp_tasks_kpi = dash_a["kpis"]["emp_tasks"]
        charts = dash_a["charts"]

        # Total = 3 (t_done + t_reported + t_undated); Incomplete = 2 (t_reported + t_undated)!
        self.assertEqual(emp_tasks_kpi["count"], 2)
        self.assertEqual(charts["total"], 3)
        self.assertEqual(charts["donut"]["center_count"], 3)
        self.assertEqual(sum(s["count"] for s in charts["donut"]["slices"]), 3)
        self.assertEqual(sum(s["percent"] for s in charts["donut"]["slices"]), 100)

        # Daily bar has 7 real week days (with valid 0s on empty days) + 1 'undated' bar (NOT assigned to today!)
        bar_rows = charts["bar"]["rows"]
        self.assertEqual(len(bar_rows), 8)
        self.assertEqual(sum(r["total_count"] for r in bar_rows), 3)
        self.assertEqual(sum(r["incomplete_count"] for r in bar_rows), 2)
        undated_row = next(r for r in bar_rows if r["day_key"] == "undated")
        self.assertEqual(undated_row["day_label"], "Chưa đặt hạn")
        self.assertEqual(undated_row["incomplete_count"], 1)

        # Drilldown on KPI 1 ('Việc chưa hoàn thành') matches count == 2
        kpi_dd = emp_tasks_kpi["drilldown"]
        act_open = self.env["res.users"].with_user(self.emp_a).get_tp_home_task_drilldown_action(
            {"period": "this_week", **kpi_dd["params"]},
        )
        open_ids = set(self.env["project.task"].with_user(self.emp_a).search(act_open["domain"]).ids)
        self.assertEqual(open_ids, {t_reported.id, t_undated.id})

        # Drilldown on 'undated' daily bar matches count == 1
        act_undated = self.env["res.users"].with_user(self.emp_a).get_tp_home_task_drilldown_action(
            {"period": "this_week", "bar_day_key": "undated"},
        )
        undated_ids = set(self.env["project.task"].with_user(self.emp_a).search(act_undated["domain"]).ids)
        self.assertEqual(undated_ids, {t_undated.id})

        # Drilldown on day1 'done' segment matches t_done
        act_d1_done = self.env["res.users"].with_user(self.emp_a).get_tp_home_task_drilldown_action(
            {"period": "this_week", "bar_day_key": week_start.isoformat(), "bar_segment": "done"},
        )
        d1_ids = set(self.env["project.task"].with_user(self.emp_a).search(act_d1_done["domain"]).ids)
        self.assertEqual(d1_ids, {t_done.id})

    def test_06_employee_requests_own_pending_only_and_approver_stays_employee_mode(self):
        """Scenario 8 & Section 4.2: Approver stays in employee mode; own pending excludes draft/approved-in-exec & deduplicates bridge."""
        if "tp.request" not in self.env or "tp.request.type" not in self.env:
            self.skipTest("tp_request is not installed")

        rtype = self.env["tp.request.type"].sudo().search([("active", "=", True)], limit=1)
        if not rtype:
            self.skipTest("No active tp.request.type")

        Req = self.env["tp.request"].sudo()
        # 1. Draft request of manager_user -> NOT counted
        r_draft = self.env["tp.request"].with_user(self.manager_user).create(
            {"title": "H007 Draft Req", "type_id": rtype.id},
        )
        self.assertEqual(r_draft.approval_state, "draft")

        # 2. Submitted pending request of manager_user -> COUNTED ONCE
        r_pending = self.env["tp.request"].with_user(self.manager_user).create(
            {"title": "H007 Pending Req", "type_id": rtype.id},
        )
        Req.browse(r_pending.id).with_context(_tp_request_internal=object()).write(
            {"approval_state": "pending"},
        ) if False else None
        # Update state via SQL in test transaction to avoid coupling to specific type step config
        self.env.cr.execute(
            "UPDATE tp_request SET approval_state = 'pending' WHERE id = %s",
            [r_pending.id],
        )
        # 3. Approved request still in execution -> NOT counted!
        r_exec = self.env["tp.request"].with_user(self.manager_user).create(
            {"title": "H007 Approved In Execution", "type_id": rtype.id},
        )
        self.env.cr.execute(
            "UPDATE tp_request SET approval_state = 'approved', execution_state = 'in_progress' WHERE id = %s",
            [r_exec.id],
        )
        # 4. Another employee's pending request where manager_user is current approver -> NOT counted in manager's own card!
        r_other = self.env["tp.request"].with_user(self.emp_a).create(
            {"title": "H007 Emp A Req Assigned To Manager", "type_id": rtype.id},
        )
        self.env.cr.execute(
            "UPDATE tp_request SET approval_state = 'pending' WHERE id = %s",
            [r_other.id],
        )
        self.env.invalidate_all()

        mgr_dash = self.env["res.users"].with_user(self.manager_user).get_tp_home_dashboard({})
        self.assertEqual(mgr_dash["home_mode"], "employee")
        self.assertEqual(mgr_dash["kpis"]["emp_requests"]["role_mode"], "mine_pending")
        self.assertEqual(mgr_dash["kpis"]["emp_requests"]["count"], 1)

    def test_07_calendar_today_allday_midnight_declined_and_deduplication(self):
        """Scenario 3, 11 & Section 4.3 / 6: All-day boundary, overnight event, declined invite excluded, colleague busy excluded, drilldown matches."""
        if "calendar.event" not in self.env or "project.task" not in self.env:
            self.skipTest("calendar or project is not installed")

        today_local = datetime.now(self.tz).date()
        yesterday = today_local - timedelta(days=1)
        utc = ZoneInfo("UTC")

        Event = self.env["calendar.event"].sudo()
        # 1. Yesterday's all-day event MUST NOT leak into today in UTC+7!
        Event.create(
            {
                "name": "H007 Yesterday Allday",
                "allday": True,
                "start_date": yesterday,
                "stop_date": yesterday,
                "user_id": self.emp_a.id,
                "partner_ids": [Command.set([self.emp_a.partner_id.id])],
            },
        )
        # 2. Today's all-day event -> COUNTED
        ev_allday = Event.create(
            {
                "name": "H007 Today Allday",
                "allday": True,
                "start_date": today_local,
                "stop_date": today_local,
                "user_id": self.emp_a.id,
                "partner_ids": [Command.set([self.emp_a.partner_id.id])],
            },
        )
        # 3. Overnight event crossing midnight (23:30 yesterday -> 01:00 today) -> COUNTED
        ev_overnight = Event.create(
            {
                "name": "H007 Overnight Crossing Midnight",
                "allday": False,
                "start": datetime.combine(yesterday, time(23, 30), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None),
                "stop": datetime.combine(today_local, time(1, 0), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None),
                "user_id": self.emp_a.id,
                "partner_ids": [Command.set([self.emp_a.partner_id.id, self.emp_b.partner_id.id])],
            },
        )
        # 4. Declined invitation -> EXCLUDED
        ev_declined = Event.create(
            {
                "name": "H007 Declined Invite",
                "allday": False,
                "start": datetime.combine(today_local, time(10, 0), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None),
                "stop": datetime.combine(today_local, time(11, 0), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None),
                "user_id": self.emp_b.id,
                "partner_ids": [Command.set([self.emp_b.partner_id.id, self.emp_a.partner_id.id])],
            },
        )
        ev_declined.attendee_ids.filtered(lambda a: a.partner_id == self.emp_a.partner_id).write({"state": "declined"})

        # 5. Colleague's own public meeting (emp_a not invited) -> EXCLUDED
        Event.create(
            {
                "name": "H007 Colleague B Own Meeting",
                "allday": False,
                "start": datetime.combine(today_local, time(9, 0), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None),
                "stop": datetime.combine(today_local, time(10, 0), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None),
                "user_id": self.emp_b.id,
                "partner_ids": [Command.set([self.emp_b.partner_id.id])],
            },
        )

        # 6. Linked task + event today -> deduplicated in Agenda!
        task_dl = datetime.combine(today_local, time(16, 0), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None)
        t_linked = self.env["project.task"].sudo().create(
            {
                "name": "H007 Linked Task Today",
                "project_id": False,
                "user_ids": [Command.set([self.emp_a.id])],
                "date_deadline": task_dl,
            },
        )
        ev_linked = Event.create(
            {
                "name": "H007 Meeting With Linked Task",
                "allday": False,
                "start": datetime.combine(today_local, time(14, 0), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None),
                "stop": datetime.combine(today_local, time(15, 0), tzinfo=self.tz).astimezone(utc).replace(tzinfo=None),
                "user_id": self.emp_a.id,
                "partner_ids": [Command.set([self.emp_a.partner_id.id])],
                "res_model_id": self.env["ir.model"]._get_id("project.task"),
                "res_id": t_linked.id,
            },
        )

        dash = self.env["res.users"].with_user(self.emp_a).get_tp_home_dashboard({})
        cal_card = dash["kpis"]["emp_calendar"]
        self.assertEqual(cal_card["count"], 3)

        cal_act = self.env["res.users"].with_user(self.emp_a).get_tp_home_calendar_drilldown_action()
        cal_ids = set(self.env["calendar.event"].with_user(self.emp_a).search(cal_act["domain"]).ids)
        self.assertEqual(cal_ids, {ev_allday.id, ev_overnight.id, ev_linked.id})

        agenda_uids = [i["uid_key"] for i in dash["agenda"]["items"]]
        self.assertIn(f"event-{ev_linked.id}", agenda_uids)
        self.assertNotIn(f"task-{t_linked.id}", agenda_uids)

    def test_08_global_document_search_validation_and_permission_isolation(self):
        with self.assertRaises(ValidationError):
            self.env["res.users"].with_user(self.emp_a).search_tp_home_global("x" * 121)

        empty = self.env["res.users"].with_user(self.emp_a).search_tp_home_global("   ")
        self.assertEqual(empty, {"documents": []})

        if "tp.request" in self.env and "tp.request.type" in self.env:
            rtype = self.env["tp.request.type"].sudo().search([("active", "=", True)], limit=1)
            if rtype:
                secret_req = self.env["tp.request"].with_user(self.emp_b).create(
                    {
                        "title": "HOME007_SECRET_REQ_B_ONLY",
                        "type_id": rtype.id,
                    },
                )
                hits_b = self.env["res.users"].with_user(self.emp_b).search_tp_home_global("HOME007_SECRET_REQ_B_ONLY")
                hits_a = self.env["res.users"].with_user(self.emp_a).search_tp_home_global("HOME007_SECRET_REQ_B_ONLY")
                self.assertTrue(any(d["key"] == f"req-{secret_req.id}" for d in hits_b["documents"]))
                self.assertEqual(hits_a["documents"], [])
