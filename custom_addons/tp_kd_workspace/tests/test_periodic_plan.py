from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from .test_allocation import TestAllocation
from .test_production import TestProduction


@tagged("post_install", "-at_install")
class TestPeriodicPlan(TestAllocation):
    # C1 is tested by TestAllocation, keep only this domain's additional cases.
    test_allocation_review_rounds_snapshot_and_version = None
    test_allocation_scope_reason_stale_and_no_direct_state = None
    test_allocation_parent_cycle_and_money_isolation = None
    test_submission_amount_export_and_expiry = None
    test_reviewer_self_and_assignment_revoke = None
    test_amount_unknown_zero_and_context_forgery = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for domain in ["production", "plan"]:
            for user, caps in [
                (cls.editor, ["prepare", "submit"]),
                (cls.reviewer, ["review"]),
            ]:
                for cap in caps:
                    cls.env["tp.kd.grant"].create(
                        {
                            "project_id": cls.project.id,
                            "department_id": cls.department.id,
                            "user_id": user.id,
                            "domain": domain,
                            "capability": cap,
                            "reason": "Synthetic D1",
                        },
                    )

    def plan(self):
        return (
            self.env["tp.periodic.plan"]
            .with_user(self.editor)
            .create(
                {
                    "code": "KD-AT-KH01",
                    "name": "Kế hoạch tháng11",
                    "project_id": self.project.id,
                    "scope": "Kế hoạch minh họa",
                    "owner_id": self.editor.id,
                    "reviewer_id": self.reviewer.id,
                    "period_kind": "month",
                    "period_from": "2026-11-01",
                    "period_to": "2026-11-30",
                },
            )
        )

    def test_plan_calendar_and_guard(self):
        self.assertIn("tp.periodic.plan", self.env)
        rec = self.plan()
        for vals in [
            {"period_to": "2026-11-29"},
            {"period_kind": "quarter"},
            {"period_kind": "year"},
        ]:
            with self.assertRaises(ValidationError), self.env.cr.savepoint():
                rec.write(dict(vals, version=rec.version))
        with self.assertRaises(AccessError):
            rec.with_user(self.reader).write(
                {"name": "Không quyền", "version": rec.version},
            )

    def test_plan_comparison_source_and_snapshot(self):
        self.assertIn("tp.periodic.plan", self.env)
        rec = self.plan()
        rec.write(
            {
                "amount_ids": [
                    (
                        0,
                        0,
                        {
                            "measure": "production",
                            "amount_state": "confirmed",
                            "value": 1000,
                            "tax_basis": "excluding_tax",
                        },
                    ),
                    (0, 0, {"measure": "revenue", "amount_state": "unconfirmed"}),
                ],
                "version": rec.version,
            },
        )
        line = rec.amount_ids.filtered(lambda a: a.measure == "production")
        self.assertEqual(line.source_status, "no_data")
        source = TestProduction.production(self)
        source.write(
            {
                "amount_ids": [
                    (
                        0,
                        0,
                        {
                            "amount_state": "confirmed",
                            "value": 125,
                            "tax_basis": "excluding_tax",
                        },
                    ),
                ],
                "version": source.version,
            },
        )
        self.transition(source, "submit")
        line.invalidate_recordset()
        self.assertEqual(line.source_status, "comparable")
        self.assertEqual(line.source_value, 125)
        action = rec.action_source_productions()
        self.assertEqual(
            self.env["tp.production"].with_user(self.editor).search(action["domain"]),
            source,
        )
        self.transition(rec, "submit")
        self.assertEqual(
            set(rec.event_ids.amount_ids.mapped("measure")),
            {"production", "revenue"},
        )
        self.assertEqual(
            self.env["tp.periodic.plan.amount"].with_user(self.reader).search_count([]),
            0,
        )
