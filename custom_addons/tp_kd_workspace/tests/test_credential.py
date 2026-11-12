from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from .test_allocation import TestAllocation


@tagged("post_install", "-at_install")
class TestCredential(TestAllocation):
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
        for domain in ["credential", "opportunity"]:
            for user, caps in [
                (cls.editor, ["prepare", "submit"]),
                (cls.reviewer, ["review"]),
            ]:
                for cap in caps:
                    if cls.env["tp.kd.grant"].search_count(
                        [
                            ("project_id", "=", cls.project.id),
                            ("user_id", "=", user.id),
                            ("domain", "=", domain),
                            ("capability", "=", cap),
                        ],
                    ):
                        continue
                    cls.env["tp.kd.grant"].create(
                        {
                            "project_id": cls.project.id,
                            "department_id": cls.department.id,
                            "user_id": user.id,
                            "domain": domain,
                            "capability": cap,
                            "reason": "Synthetic D2",
                        },
                    )
        cls.subject = cls.env["res.partner"].create({"name": "Chuyên viên tổng hợp"})

    def credential(self):
        return (
            self.env["tp.credential"]
            .with_user(self.editor)
            .create(
                {
                    "code": "KD-AT-NL01",
                    "name": "Năng lực khảo sát tổng hợp",
                    "project_id": self.project.id,
                    "scope": "Khảo sát địa hình",
                    "owner_id": self.editor.id,
                    "reviewer_id": self.reviewer.id,
                    "subject_id": self.subject.id,
                    "subject_kind": "person",
                    "credential_kind": "Khảo sát địa hình",
                    "valid_from": "2026-01-01",
                    "valid_to": "2026-11-20",
                    "source_note": "Hồ sơ tổng hợp chưa xác minh",
                },
            )
        )

    def test_edit_visible_links_preserves_hidden_person_credential(self):
        visible = self.credential()
        private = self.env["tp.credential"].create({
            "code": "BP005-PRIVATE", "name": "Hồ sơ cá nhân riêng tư tổng hợp",
            "project_id": self.project.id, "scope": "Giả lập",
            "owner_id": self.reader.id, "reviewer_id": self.reviewer.id,
            "subject_id": self.subject.id, "subject_kind": "person",
            "credential_kind": "Khảo sát", "valid_from": "2026-01-01",
            "valid_to": "2027-01-01", "source_note": "Chưa xác minh",
        })
        lead = self.env["crm.lead"].create({
            "name": "BP005 opportunity", "type": "opportunity",
            "user_id": self.editor.id,
            "tp_project_id": self.project.id, "partner_id": self.project.partner_id.id,
            "company_id": self.project.company_id.id,
            "kd_credential_link_ids": [(6, 0, (visible | private).ids)],
        })
        actor_lead = lead.with_user(self.editor)
        self.assertEqual(actor_lead.kd_credential_ids, visible)
        actor_lead.write({"kd_credential_ids": [(6, 0, [])]})
        self.assertFalse(actor_lead.kd_credential_ids)
        self.assertEqual(lead.sudo().kd_credential_link_ids, private)
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            actor_lead.write({"kd_credential_ids": [(4, private.id)]})

    def test_credential_person_and_dates(self):
        self.assertIn("tp.credential", self.env)
        rec = self.credential()
        self.assertEqual(
            rec.with_user(self.reader).search_count([("id", "=", rec.id)]),
            0,
        )
        with self.assertRaises(AccessError):
            rec.with_user(self.reader).read(["subject_id"])
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            rec.write({"valid_to": "2025-01-01", "version": rec.version})
        self.transition(rec, "submit")
        self.transition(rec, "return", self.reviewer, reason="Kiểm tra nguồn")
        self.transition(rec, "rework", reason="Bổ sung")
        rec.write(
            {"source_note": "Nguồn bổ sung chưa xác minh", "version": rec.version},
        )
        self.transition(rec, "submit", fix_summary="Bổ sung nguồn")
        self.assertEqual(len(rec.event_ids), 4)

    def test_credential_bid_usage_and_forged_command(self):
        self.assertIn("tp.credential", self.env)
        rec = self.credential()
        lead = (
            self.env["crm.lead"]
            .with_user(self.editor)
            .create(
                {
                    "name": "Gói thầu tổng hợp",
                    "tp_project_id": self.project.id,
                    "company_id": self.project.company_id.id,
                    "partner_id": self.project.partner_id.id,
                    "kd_credential_ids": [(6, 0, rec.ids)],
                },
            )
        )
        self.assertEqual(
            self.env["crm.lead"]
            .with_user(self.editor)
            .search(rec.action_used_opportunities()["domain"]),
            lead,
        )
        self.assertFalse(lead.with_user(self.reader).kd_credential_ids)
        self.assertEqual(lead.sudo().kd_credential_link_ids, rec.sudo())
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            lead.with_user(self.reader).write({"kd_credential_ids": [(6, 0, rec.ids)]})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            lead.write(
                {"kd_credential_ids": [(0, 0, {"name": "Không được tạo từ M2M"})]},
            )
