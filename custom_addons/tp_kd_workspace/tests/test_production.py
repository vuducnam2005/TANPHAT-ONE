from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .test_allocation import TestAllocation


@tagged("post_install", "-at_install")
class TestProduction(TestAllocation):
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
                        "domain": "production",
                        "capability": cap,
                        "reason": "Synthetic C2",
                    },
                )

    def production(self, **extra):
        allocation = self.allocation()
        values = {
            "code": "KD-AT-SL01",
            "name": "Sản lượng khảo sát đợt 1",
            "project_id": self.project.id,
            "contract_id": self.contract.id,
            "allocation_id": allocation.id,
            "scope": "Khảo sát địa hình",
            "owner_id": self.editor.id,
            "reviewer_id": self.reviewer.id,
            "date": "2026-11-06",
            "period_from": "2026-11-01",
            "period_to": "2026-11-30",
            "quantity": 4.5,
            "unit": "km",
            "completion_percent": 45,
        }
        return (
            self.env["tp.production"]
            .with_user(self.editor)
            .create(dict(values, **extra))
        )

    def test_production_workflow_snapshot(self):
        self.assertIn("tp.production", self.env)
        rec = self.production()
        rec.write({"quantity": 5, "version": rec.version})
        w = self.transition(rec, "submit")
        n = len(rec.event_ids)
        w.action_confirm()
        self.assertEqual(len(rec.event_ids), n)
        snapshot = rec.event_ids.snapshot
        self.transition(rec, "return", self.reviewer, reason="Bổ sung căn cứ đo")
        self.transition(rec, "rework", reason="Bổ sung")
        rec.write({"scope": "Bổ sung mốc đo", "version": rec.version})
        self.transition(rec, "submit", fix_summary="Đã bổ sung")
        self.assertEqual(rec.state, "in_review")
        self.assertEqual(rec.event_ids[0].snapshot, snapshot)
        self.assertIn("quantity", snapshot)
        self.assertEqual(
            self.env["tp.production.amount"].with_user(self.reader).search_count([]),
            0,
        )

    def test_production_invalid_quantity_period_scope(self):
        self.assertIn("tp.production", self.env)
        rec = self.production()
        for values in [
            {"quantity": -1},
            {"completion_percent": 101},
            {"period_to": "2026-10-31"},
            {"period_from": False},
            {"contract_id": False},
        ]:
            with self.assertRaises(ValidationError), self.env.cr.savepoint():
                rec.write(dict(values, version=rec.version))

    def test_production_source_mutation_and_scope(self):
        rec = self.production()
        other_contract = self.env["tp.contract"].create(
            {
                "project_id": self.project.id,
                "code": "KD-AT-HD-OTHER",
                "name": "Hợp đồng nguồn khác",
                "contract_type": "owner",
                "currency_id": self.env.company.currency_id.id,
            },
        )
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            rec.allocation_id.with_user(self.editor).write(
                {
                    "contract_id": other_contract.id,
                    "version": rec.allocation_id.version,
                },
            )
        with self.assertRaises(AccessError):
            rec.with_user(self.reader).write(
                {"scope": "Ngoài quyền", "version": rec.version},
            )
        wizard = rec.action_submit()
        rec.write({"scope": "Thay đổi mới", "version": rec.version})
        with self.assertRaises(UserError):
            self.env["tp.kd.transition"].with_user(self.editor).browse(
                wizard["res_id"],
            ).action_confirm()
        self.env["tp.kd.grant"].search(
            [("user_id", "=", self.editor.id), ("domain", "=", "production")],
        ).date_end = "2000-01-01"
        with self.assertRaises(AccessError):
            rec.action_submit()
