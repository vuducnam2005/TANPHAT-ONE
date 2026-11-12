from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .test_allocation import TestAllocation
from .test_production import TestProduction


@tagged("post_install", "-at_install")
class TestAcceptance(TestAllocation):
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
        for domain in ["production", "acceptance"]:
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
                            "reason": "Synthetic C3",
                        },
                    )
        cls.partner = cls.env["res.partner"].create({"name": "Chủ đầu tư tổng hợp"})

    def acceptance(self):
        source = TestProduction.production(self)
        return (
            self.env["tp.acceptance"]
            .with_user(self.editor)
            .create(
                {
                    "code": "KD-AT-NT01",
                    "name": "Đợt hồ sơ địa hình",
                    "project_id": self.project.id,
                    "contract_id": self.contract.id,
                    "production_id": source.id,
                    "scope": "Khảo sát địa hình đoạn1",
                    "owner_id": self.editor.id,
                    "reviewer_id": self.reviewer.id,
                    "date": "2026-11-06",
                    "period_from": "2026-11-01",
                    "period_to": "2026-11-30",
                    "quantity": 2,
                    "unit": "km",
                    "round_code": "Đợt1",
                    "counterparty_id": self.partner.id,
                    "evidence_checklist": "Bảng khối lượng, bản vẽ — chưa xác minh",
                },
            )
        )

    def test_acceptance_workflow(self):
        self.assertIn("tp.acceptance", self.env)
        rec = self.acceptance()
        self.transition(rec, "submit")
        snapshot = rec.event_ids.snapshot
        self.transition(rec, "return", self.reviewer, reason="Thiếu bảng khối lượng")
        self.transition(rec, "rework", reason="Chuẩn bị bảng khối lượng")
        rec.write(
            {
                "evidence_checklist": "Đã kê bảng khối lượng, chưa xác minh",
                "version": rec.version,
            },
        )
        self.transition(rec, "submit", fix_summary="Bổ sung kiểm kê tài liệu")
        self.assertEqual(rec.state, "in_review")
        self.assertEqual(rec.event_ids[0].snapshot, snapshot)
        self.assertEqual(
            self.env["tp.acceptance.amount"].with_user(self.reader).search_count([]),
            0,
        )

    def test_acceptance_scope_quantity_chronology(self):
        self.assertIn("tp.acceptance", self.env)
        rec = self.acceptance()
        for vals in [
            {"quantity": 5},
            {"quantity": -1},
            {"unit": "m3"},
            {"date": "2026-10-31"},
            {"period_to": "2026-12-01"},
            {"production_id": False},
        ]:
            with self.assertRaises(ValidationError), self.env.cr.savepoint():
                rec.write(dict(vals, version=rec.version))
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            rec.production_id.with_user(self.editor).write(
                {"quantity": 1, "version": rec.production_id.version},
            )
