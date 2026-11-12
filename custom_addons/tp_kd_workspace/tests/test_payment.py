from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .test_acceptance import TestAcceptance
from .test_allocation import TestAllocation


@tagged("post_install", "-at_install")
class TestPayment(TestAllocation):
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
        for domain in ["production", "acceptance", "payment"]:
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
                            "reason": "Synthetic C4",
                        },
                    )
        cls.partner = cls.env["res.partner"].create({"name": "Bên đề nghị tổng hợp"})

    def payment(self, basis="advance"):
        values = {
            "code": "KD-AT-TT01",
            "name": "Đề nghị đợt1",
            "project_id": self.project.id,
            "contract_id": self.contract.id,
            "scope": "Phạm vi khảo sát",
            "owner_id": self.editor.id,
            "reviewer_id": self.reviewer.id,
            "date": "2026-11-06",
            "date_due": "2026-11-20",
            "direction": "receipt",
            "payment_basis": basis,
            "partner_id": self.partner.id,
            "advance_basis": "Điều khoản tạm ứng dự thảo, chưa có hiệu lực",
            "document_checklist": "Kiểm kê hồ sơ, chưa xác minh",
        }
        if basis == "acceptance":
            values["acceptance_id"] = TestAcceptance.acceptance(self).id
        return self.env["tp.payment.request"].with_user(self.editor).create(values)

    def test_payment_advance_workflow(self):
        self.assertIn("tp.payment.request", self.env)
        rec = self.payment()
        self.assertFalse(rec.acceptance_id)
        self.transition(rec, "submit")
        snapshot = rec.event_ids.snapshot
        self.transition(rec, "return", self.reviewer, reason="Bổ sung dự kiến hạn")
        self.transition(rec, "rework", reason="Sửa hạn")
        rec.write({"date_due": "2026-11-22", "version": rec.version})
        self.transition(rec, "submit", fix_summary="Đã bổ sung")
        self.assertEqual(rec.state, "in_review")
        self.assertEqual(rec.event_ids[0].snapshot, snapshot)
        self.assertNotIn("paid", dict(rec._fields["state"].selection))
        self.assertEqual(
            self.env["tp.payment.request.amount"]
            .with_user(self.reader)
            .search_count([]),
            0,
        )

    def test_payment_acceptance_source_and_basis(self):
        self.assertIn("tp.payment.request", self.env)
        rec = self.payment("acceptance")
        for vals in [
            {"acceptance_id": False},
            {"date": "2026-11-01"},
            {"payment_basis": "advance", "advance_basis": False},
            {"contract_id": False},
            {"date_due": False},
        ]:
            with self.assertRaises(ValidationError), self.env.cr.savepoint():
                rec.write(dict(vals, version=rec.version))
