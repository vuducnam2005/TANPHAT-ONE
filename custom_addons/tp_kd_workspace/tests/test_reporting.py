from odoo.exceptions import AccessError
from odoo.tests import tagged

from .test_allocation import TestAllocation


@tagged("post_install", "-at_install")
class TestKdReporting(TestAllocation):
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
                        "domain": "obligation",
                        "capability": cap,
                        "reason": "Synthetic D3",
                    },
                )

    def obligation(self):
        return (
            self.env["tp.obligation"]
            .with_user(self.editor)
            .create(
                {
                    "code": "KD-AT-NV01",
                    "name": "Thu thập hồ sơ bàn giao",
                    "project_id": self.project.id,
                    "contract_id": self.contract.id,
                    "scope": "Hồ sơ khảo sát",
                    "owner_id": self.editor.id,
                    "reviewer_id": self.reviewer.id,
                    "date": "2026-11-01",
                    "date_due": "2026-11-04",
                    "obligation_kind": "contract_docs",
                    "document_checklist": "Còn thiếu biên bản",
                    "checklist_update_reason": "Khởi tạo tổng hợp",
                },
            )
        )

    def test_obligation_history_and_no_legal_clearance(self):
        self.assertIn("tp.obligation", self.env)
        rec = self.obligation()
        rec.write(
            {
                "checklist_status": "collecting",
                "checklist_update_reason": "Đang thu thập",
                "version": rec.version,
            },
        )
        self.assertEqual(rec.event_ids.action, "update_checklist")
        self.transition(rec, "submit")
        self.transition(rec, "return", self.reviewer, reason="Cần căn cứ")
        self.transition(rec, "rework", reason="Bổ sung")
        rec.write(
            {
                "document_checklist": "Đã có danh mục, chưa xác minh",
                "version": rec.version,
            },
        )
        self.transition(rec, "submit", fix_summary="Bổ sung")
        self.assertEqual(rec.state, "in_review")
        with self.assertRaises(AccessError):
            rec.with_user(self.reader).write(
                {"scope": "Không quyền", "version": rec.version},
            )

    def test_inbox_counts_drilldown_scope_and_ui_permission(self):
        self.assertIn("tp.obligation", self.env)
        rec = self.obligation()
        overview = (
            self.env["tp.kd.overview"]
            .with_user(self.editor)
            .create({"project_id": self.project.id})
        )
        domain = overview._inbox_domain("tp.obligation", "overdue")
        self.assertEqual(
            self.env["tp.obligation"].with_user(self.editor).search(domain),
            rec,
        )
        self.assertEqual(overview.obligation_overdue_count, 1)
        self.transition(rec, "submit")
        reviewer = (
            self.env["tp.kd.overview"]
            .with_user(self.reviewer)
            .create({"project_id": self.project.id})
        )
        self.assertEqual(reviewer.obligation_review_count, 1)
        self.assertEqual(overview.obligation_review_count, 0)
        action = reviewer.with_context(
            kd_source="tp.obligation",
            kd_query="review",
        ).action_inbox()
        self.assertEqual(
            self.env["tp.obligation"].with_user(self.reviewer).search(action["domain"]),
            rec,
        )
        self.assertTrue(
            self.env["tp.obligation"]
            .with_user(self.editor)
            .get_kd_ui_permissions()["create"],
        )
        self.assertFalse(
            self.env["tp.obligation"]
            .with_user(self.reader)
            .get_kd_ui_permissions()["create"],
        )

    def test_wbs_responsible_and_task_policy(self):
        self.env["tp.project.assignment"].create(
            {"project_id": self.project.id, "user_id": self.planner.id},
        )
        task = (
            self.env["project.task"]
            .with_user(self.planner)
            .create(
                {
                    "name": "Báo cáo tháng",
                    "project_id": self.project.id,
                    "kd_contract_id": self.contract.id,
                    "kd_responsible_id": self.editor.id,
                    "user_ids": [(6, 0, self.editor.ids)],
                    "kd_deliverable": "Báo cáo minh họa",
                },
            )
        )
        task.write({"name": "Báo cáo tháng cập nhật"})
        with self.assertRaises(AccessError):
            task.with_user(self.editor).write({"name": "Nhân viên vẫn bị chặn"})
        self.assertFalse(task.with_user(self.editor).get_kd_ui_permissions()["create"])
