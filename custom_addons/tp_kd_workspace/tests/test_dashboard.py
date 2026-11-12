from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .test_periodic_plan import TestPeriodicPlan
from .test_production import TestProduction


@tagged("post_install", "-at_install")
class TestKdDashboard(TestPeriodicPlan):
    """KD-UI-002 Overview helpers: every number equals its drilldown source in the actor env."""

    test_allocation_review_rounds_snapshot_and_version = None
    test_allocation_scope_reason_stale_and_no_direct_state = None
    test_allocation_parent_cycle_and_money_isolation = None
    test_submission_amount_export_and_expiry = None
    test_reviewer_self_and_assignment_revoke = None
    test_amount_unknown_zero_and_context_forgery = None
    test_plan_calendar_and_guard = None
    test_plan_comparison_source_and_snapshot = None
    test_project_child_actions_do_not_reuse_parent_form_or_defaults = None
    test_bid_actions_and_direct_route = None
    test_scope_grant_revoke_and_forged_state = None
    test_project_navigation_and_task_policy = None
    test_grants_not_self_manageable = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for user, caps in [(cls.editor, ["prepare", "submit"]), (cls.reviewer, ["review"])]:
            for cap in caps:
                cls.env["tp.kd.grant"].create({
                    "project_id": cls.project.id, "department_id": cls.department.id, "user_id": user.id,
                    "domain": "credential", "capability": cap, "reason": "Synthetic KD-UI-002",
                })
        cls.subject = cls.env["res.partner"].create({"name": "Chuyên viên tổng hợp"})
        cls.outsider = new_test_user(cls.env, login="kd_ui_outsider", groups="tp_core.group_user")
        cls.scope = {"project_id": cls.project.id}

    def overview(self, user):
        return self.env["tp.kd.overview"].with_user(user)

    def count(self, user, action):
        return self.env[action["res_model"]].with_user(user).search_count(action["domain"])

    def test_g01_states_kpis_and_my_work_match_sources(self):
        draft = self.allocation("KD-UI-K01")
        review = self.allocation("KD-UI-K02")
        returned = self.allocation("KD-UI-K03")
        self.transition(review, "submit")
        self.transition(returned, "submit")
        self.transition(returned, "return", self.reviewer, reason="Thiếu phạm vi")
        for user in (self.reviewer, self.editor):
            data = self.overview(user).get_kd_dashboard(self.scope)
            row = next(r for r in data["g01"]["rows"] if r["source"] == "allocation")
            self.assertEqual((row["draft"], row["in_review"], row["returned"], row["total"]), (1, 1, 1, 3))
            self.assertEqual(data["g01"]["totals"]["total"], sum(r["total"] for r in data["g01"]["rows"]))
            for state in ("draft", "in_review", "returned"):
                action = self.overview(user).action_kd_open("g01", self.scope, {"source": "allocation", "state": state})
                self.assertEqual(self.count(user, action), row[state])
        reviewer = self.overview(self.reviewer).get_kd_dashboard(self.scope)
        editor = self.overview(self.editor).get_kd_dashboard(self.scope)
        self.assertEqual(reviewer["kpis"]["review"], 1)
        self.assertEqual(editor["kpis"]["review"], 0)
        self.assertEqual(editor["kpis"]["returned"], 1)
        work = self.overview(self.reviewer).get_kd_my_work(self.scope, "review", 0, 10)
        self.assertEqual(work["total"], reviewer["kpis"]["review"])
        self.assertEqual([(r["source"], r["id"]) for r in work["rows"]], [("allocation", review.id)])
        work = self.overview(self.editor).get_kd_my_work(self.scope, "returned", 0, 1)
        self.assertEqual((work["total"], work["rows"][0]["id"]), (1, returned.id))
        action = self.overview(self.editor).action_kd_open("record", self.scope,
                                                           {"source": "allocation", "res_id": draft.id})
        self.assertEqual((action["res_model"], action["res_id"]), ("tp.allocation", draft.id))
        # Old inbox counters and the new source table read the same domains.
        table = self.overview(self.reviewer).get_kd_source_table(self.scope)
        old = self.overview(self.reviewer).new(self.scope)
        for row in table["rows"]:
            for query in ("all", "review", "returned", "overdue", "due"):
                self.assertEqual(row[query], old[f"{row['source']}_{query}_count"])

    def test_due_tab_is_overdue_plus_due_of_current_owner(self):
        today = fields.Date.context_today(self.env["tp.kd.overview"].with_user(self.editor))
        start = today - timedelta(days=10)
        self.allocation("KD-UI-D1", date=start, date_due=today - timedelta(days=1))
        self.allocation("KD-UI-D2", date=start, date_due=today + timedelta(days=3))
        self.allocation("KD-UI-D3", date=start, date_due=today + timedelta(days=4))
        data = self.overview(self.editor).get_kd_dashboard(self.scope)
        self.assertEqual((data["kpis"]["overdue"], data["kpis"]["due"]), (1, 1))
        # KD-UI-004 label "Đến hạn trong 3 ngày": the window is [today, today + 3] (D2 in, D3 out).
        self.assertEqual(data["kpis"]["due_window"], {"from": fields.Date.to_string(today),
                                                      "to": fields.Date.to_string(today + timedelta(days=3))})
        work = self.overview(self.editor).get_kd_my_work(self.scope, "due", 0, 10)
        self.assertEqual(work["total"], 2)
        self.assertEqual([r["code"] for r in work["rows"]], ["KD-UI-D1", "KD-UI-D2"])
        self.assertTrue(work["rows"][0]["overdue"])
        page = self.overview(self.editor).get_kd_my_work(self.scope, "due", 1, 1)
        self.assertEqual((page["total"], page["rows"][0]["code"]), (2, "KD-UI-D2"))
        self.assertEqual(self.overview(self.reviewer).get_kd_dashboard(self.scope)["kpis"]["overdue"], 0)

    def test_g02_task_buckets_are_disjoint_and_drill_down(self):
        now = fields.Datetime.now()
        task = self.env["project.task"]
        task.create({"name": "Đã xong quá hạn", "project_id": self.project.id, "state": "1_done",
                     "date_deadline": now - timedelta(days=2)})
        task.create({"name": "Quá hạn", "project_id": self.project.id, "date_deadline": now - timedelta(days=2)})
        task.create({"name": "Còn hạn", "project_id": self.project.id, "date_deadline": now + timedelta(days=5)})
        task.create({"name": "Không hạn", "project_id": self.project.id})
        data = self.overview(self.editor).get_kd_dashboard(self.scope)
        row = next(r for r in data["g02"]["rows"] if r["project_id"] == self.project.id)
        self.assertEqual((row["done"], row["overdue"], row["open"], row["total"]), (1, 1, 2, 4))
        self.assertGreaterEqual(data["g02"]["no_deadline"], 1)
        for bucket in ("done", "overdue", "open", "all"):
            action = self.overview(self.editor).action_kd_open(
                "task", self.scope, {"project_id": self.project.id, "bucket": bucket})
            self.assertEqual(self.count(self.editor, action), row[bucket if bucket != "all" else "total"])
        rows = self.overview(self.editor).get_kd_project_rows(self.scope, "KD-AT-A", "code", 0, 10)
        self.assertEqual(rows["total"], 1)
        self.assertEqual((rows["rows"][0]["task_open"], rows["rows"][0]["task_overdue"]), (3, 1))

    def test_g03_leads_by_route_and_bid_state(self):
        self.lead()
        direct = self.lead()
        direct.write({"kd_route": "direct"})
        data = self.overview(self.editor).get_kd_dashboard(self.scope)["g03"]
        self.assertEqual((data["bid"]["identified"], data["direct"], data["total"]), (1, 1, 2))
        action = self.overview(self.editor).action_kd_open("lead", self.scope,
                                                           {"route": "bid", "bid_state": "identified"})
        self.assertEqual(self.count(self.editor, action), 1)
        action = self.overview(self.editor).action_kd_open("lead", self.scope, {"route": "direct"})
        self.assertEqual(self.count(self.editor, action), 1)

    def test_g04_period_kind_unconfirmed_zero_and_money_scope(self):
        month = self.plan()
        month.write({"amount_ids": [(0, 0, {"measure": "production", "amount_state": "unconfirmed"})],
                     "version": month.version})
        quarter = self.env["tp.periodic.plan"].with_user(self.editor).create({
            "code": "KD-UI-Q4", "name": "Kế hoạch quý", "project_id": self.project.id, "scope": "Quý",
            "owner_id": self.editor.id, "reviewer_id": self.reviewer.id, "period_kind": "quarter",
            "period_from": "2026-10-01", "period_to": "2026-12-31",
            "amount_ids": [(0, 0, {"measure": "production", "amount_state": "confirmed", "value": 0,
                                   "tax_basis": "excluding_tax"})],
        })
        source = TestProduction.production(self)
        source.write({"amount_ids": [(0, 0, {"amount_state": "confirmed", "value": 125, "tax_basis": "excluding_tax"})],
                      "version": source.version})
        self.transition(source, "submit")
        data = self.overview(self.reviewer).get_kd_plan_compare(self.scope, "month")
        self.assertEqual([r["plan_id"] for r in data["rows"]], [month.id])
        row = data["rows"][0]
        self.assertIsNone(row["target_text"])  # unconfirmed is not 0
        self.assertEqual(row["basis_label"], "Chưa rõ cơ sở")
        self.assertEqual(row["target_state"], "unconfirmed")
        self.assertIsNone(row["source_text"])
        self.assertNotEqual(row["status"], "comparable")
        self.assertIsNone(row["ratio"])
        data = self.overview(self.reviewer).get_kd_plan_compare(self.scope, "quarter")
        self.assertEqual([r["plan_id"] for r in data["rows"]], [quarter.id])
        row = data["rows"][0]
        self.assertEqual(row["status"], "comparable")
        # Each row carries its own unit; the client never compares rows of different currency/basis.
        self.assertEqual((row["currency"], row["basis_label"]),
                         (self.env.company.currency_id.name, "Chưa thuế — giả định"))
        self.assertIsNotNone(row["target_text"])  # confirmed 0 stays a real 0
        self.assertIsNotNone(row["source_text"])
        self.assertIsNone(row["ratio"])  # zero denominator: no percentage
        # Reader is assigned but has no financial_read: no values, only the excluded count.
        data = self.overview(self.reader).get_kd_plan_compare(self.scope, "quarter")
        self.assertEqual((data["rows"], data["excluded"]), ([], data["in_scope"]))
        # Revocation applies on the next call; nothing cached server side.
        self.env["tp.project.grant"].search([("user_id", "=", self.reviewer.id),
                                             ("capability", "=", "financial_read")]).write({"active": False})
        self.assertEqual(self.overview(self.reviewer).get_kd_plan_compare(self.scope, "quarter")["rows"], [])
        with self.assertRaises(UserError):
            self.overview(self.reviewer).get_kd_plan_compare(self.scope, "week")
        action = self.overview(self.editor).action_kd_open("plan_sources", self.scope, {"plan_id": quarter.id})
        self.assertEqual(self.count(self.editor, action), 1)

    def test_g05_credential_date_boundaries(self):
        today = fields.Date.context_today(self.env["tp.kd.overview"].with_user(self.editor))
        for index, delta in enumerate((-1, 0, 30, 31)):
            self.env["tp.credential"].with_user(self.editor).create({
                "code": f"KD-UI-NL{index}", "name": "Năng lực", "project_id": self.project.id, "scope": "NL",
                "owner_id": self.editor.id, "reviewer_id": self.reviewer.id, "subject_id": self.subject.id,
                "subject_kind": "person", "credential_kind": "Khảo sát",
                "valid_from": today - timedelta(days=400), "valid_to": today + timedelta(days=delta),
                "source_note": "Tổng hợp chưa xác minh",
            })
        data = self.overview(self.editor).get_kd_credential_expiry(self.scope)
        self.assertEqual(data["buckets"], {"expired": 1, "soon": 2, "later": 1})
        self.assertEqual(data["bounds"], {"today": fields.Date.to_string(today),
                                          "soon_until": fields.Date.to_string(today + timedelta(days=30))})
        if hasattr(self.outsider, '_tp_can_kd_workspace'):
            with self.assertRaises(AccessError):
                self.overview(self.outsider).get_kd_credential_expiry({})
        else:
            self.assertEqual(self.overview(self.outsider).get_kd_credential_expiry({})["buckets"],
                             {"expired": 0, "soon": 0, "later": 0})
        self.assertEqual(len(data["soon"]), 2)
        for bucket, value in data["buckets"].items():
            action = self.overview(self.editor).action_kd_open("credential", self.scope, {"bucket": bucket})
            self.assertEqual(self.count(self.editor, action), value)

    def test_whitelist_scope_and_create_permissions(self):
        overview = self.overview(self.editor)
        for call in (
            lambda: overview.get_kd_dashboard({"domain": [("id", ">", 0)]}),
            lambda: overview.get_kd_dashboard({"date_from": "2026-12-01", "date_to": "2026-11-01"}),
            lambda: overview.get_kd_dashboard({"project_id": "1"}),
            lambda: overview.get_kd_project_rows(self.scope, "", "write_uid", 0, 10),
            lambda: overview.get_kd_project_rows(self.scope, "", "code", 0, 500),
            lambda: overview.get_kd_my_work(self.scope, "all", 0, 10),
            lambda: overview.action_kd_open("source", self.scope, {"source": "res.users", "query": "all"}),
            lambda: overview.action_kd_open("g01", self.scope, {"source": "allocation", "state": "done"}),
            lambda: overview.action_kd_open("record", self.scope, {"source": "res.partner", "res_id": 1}),
            lambda: overview.action_kd_open("unlink", self.scope, {}),
        ):
            with self.assertRaises(UserError):
                call()
        kinds = [k["kind"] for k in overview.get_kd_dashboard(self.scope)["create"]]
        self.assertIn("allocation", kinds)
        self.assertIn("opportunity", kinds)
        self.assertNotIn("task", kinds)
        self.assertNotIn("allocation", [k["kind"] for k in self.overview(self.reader).get_kd_dashboard()["create"]])
        with self.assertRaises(AccessError):
            self.overview(self.reader).action_kd_create("allocation", self.project.id)
        with self.assertRaises(AccessError):
            overview.action_kd_create("task", self.project.id)
        action = overview.action_kd_create("allocation", self.project.id)
        self.assertEqual((action["res_model"], action["context"]["default_project_id"]),
                         ("tp.allocation", self.project.id))
        self.assertNotIn("task", [k["kind"] for k in self.overview(self.planner).get_kd_dashboard()["create"]])
        self.env['tp.project.assignment'].create({'project_id': self.project.id, 'user_id': self.planner.id})
        self.env['tp.kd.grant'].create({'project_id': self.project.id, 'department_id': self.department.id,
            'user_id': self.planner.id, 'domain': 'wbs', 'capability': 'prepare', 'reason': 'Synthetic explicit WBS'})
        self.assertIn("task", [k["kind"] for k in self.overview(self.planner).get_kd_dashboard()["create"]])
        # Row shortcuts are existing project methods; each one re-checks access when called.
        methods = [a["method"] for a in overview.get_kd_dashboard(self.scope)["project_actions"]]
        self.assertIn("action_kd_allocations", methods)
        for method in methods:
            self.assertTrue(callable(getattr(self.env["project.project"], method)))
        project = self.project.with_user(self.editor)
        self.assertEqual(project.action_kd_allocations()["res_model"], "tp.allocation")
        # Outsider has no queue/money and opening other users' records stays scoped by record rules.
        self.allocation("KD-UI-O1")
        if hasattr(self.outsider, '_tp_can_kd_workspace'):
            for method, args in [('get_kd_dashboard', ()), ('get_kd_plan_compare', ({}, 'month'))]:
                with self.assertRaises(AccessError):
                    getattr(self.overview(self.outsider), method)(*args)
        else:
            outsider = self.overview(self.outsider).get_kd_dashboard()
            self.assertEqual((outsider["kpis"]["review"], outsider["kpis"]["returned"]), (0, 0))
            self.assertEqual(self.overview(self.outsider).get_kd_plan_compare({}, "month")["rows"], [])

    def test_ui007_page_sizes_and_merge_cap(self):
        overview = self.overview(self.editor)
        for limit in (10, 20, 50, 100):
            self.assertEqual(overview.get_kd_project_rows(self.scope, limit=limit)["limit"], limit)
            self.assertEqual(overview.get_kd_my_work(self.scope, limit=limit)["limit"], limit)
        for method in (overview.get_kd_project_rows, overview.get_kd_my_work):
            with self.assertRaises(UserError):
                method(self.scope, limit=101)
        with self.assertRaises(UserError):
            overview.get_kd_my_work(self.scope, offset=450, limit=100)
