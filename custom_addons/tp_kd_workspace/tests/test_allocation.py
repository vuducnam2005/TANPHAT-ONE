from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .test_workspace import TestKdWorkspace


@tagged("post_install", "-at_install")
class TestAllocation(TestKdWorkspace):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reviewer = new_test_user(
            cls.env,
            login="kd_at_reviewer",
            groups="tp_core.group_user",
        )
        values = {"project_id": cls.project.id, "user_id": cls.reviewer.id}
        if 'tp_cross_department' in cls.env['tp.project.assignment']._fields:
            cls.reviewer.group_ids = [Command.link(cls.env.ref('tp_kd_workspace.group_scoped_staff').id)]
            values.update(tp_cross_department=True, tp_cross_department_reason='Synthetic explicit reviewer scope')
        cls.env["tp.project.assignment"].create(values)
        for user, capabilities in (
            (cls.editor, ["prepare", "submit"]),
            (cls.reviewer, ["review"]),
        ):
            for cap in capabilities:
                cls.env["tp.kd.grant"].create(
                    {
                        "project_id": cls.project.id,
                        "department_id": cls.department.id,
                        "user_id": user.id,
                        "domain": "allocation",
                        "capability": cap,
                        "reason": "Synthetic C1 fixture",
                    },
                )
            for cap in ["financial_read"] + (
                ["financial_draft_edit"] if user == cls.editor else []
            ):
                cls.env["tp.project.grant"].create(
                    {
                        "project_id": cls.project.id,
                        "user_id": user.id,
                        "capability": cap,
                        "department_id": cls.department.id
                        if cap != "financial_read"
                        else False,
                        "reason": "Synthetic C1 money fixture",
                    },
                )
        cls.contract = cls.env["tp.contract"].create(
            {
                "project_id": cls.project.id,
                "code": "KD-AT-HD",
                "name": "Hợp đồng tổng hợp",
                "contract_type": "owner",
                "currency_id": cls.env.company.currency_id.id,
            },
        )

    def allocation(self, code="KD-AT-K01", **extra):
        return (
            self.env["tp.allocation"]
            .with_user(self.editor)
            .create(
                dict(
                    {
                        "code": code,
                        "name": "Khoán khảo sát",
                        "project_id": self.project.id,
                        "contract_id": self.contract.id,
                        "scope": "Khảo sát địa hình",
                        "owner_id": self.editor.id,
                        "reviewer_id": self.reviewer.id,
                        "date": "2026-11-06",
                        "date_due": "2026-12-01",
                        "allocation_kind": "internal",
                        "recipient_department_id": self.department.id,
                    },
                    **extra,
                ),
            )
        )

    def transition(self, record, action, user=None, **values):
        record = record.with_user(user or self.editor)
        result = getattr(record, "action_" + action)()
        wizard = (
            self.env["tp.kd.transition"]
            .with_user(user or self.editor)
            .browse(result["res_id"])
        )
        if values:
            wizard.write(values)
        wizard.action_confirm()
        return wizard

    def test_allocation_review_rounds_snapshot_and_version(self):
        self.assertIn("tp.allocation", self.env, "C1 model is not implemented")
        rec = self.allocation()
        rec.write({"name": "Khoán khảo sát địa hình", "version": rec.version})
        before = rec.version
        wizard = self.transition(rec, "submit")
        rec.invalidate_recordset()
        self.assertEqual(rec.state, "in_review")
        snapshot = rec.event_ids.filtered(lambda e: e.action == "submit").snapshot
        count = len(rec.event_ids)
        wizard.action_confirm()
        self.assertEqual(len(rec.event_ids), count)
        with self.assertRaises(UserError):
            rec.write({"name": "Không cho", "version": rec.version})
        with self.assertRaises(UserError):
            self.transition(rec, "return", self.reviewer)
        self.transition(rec, "return", self.reviewer, reason="Thiếu phạm vi bàn giao")
        self.transition(rec, "rework", reason="Bổ sung hồ sơ")
        rec.write({"scope": "Phạm vi đã bổ sung", "version": rec.version})
        self.transition(rec, "submit", fix_summary="Đã bổ sung phạm vi")
        self.assertEqual(rec.state, "in_review")
        self.assertEqual(
            rec.event_ids.filtered(lambda e: e.action == "submit")[0].snapshot,
            snapshot,
        )
        self.assertGreater(rec.version, before)
        with self.assertRaises(UserError):
            rec.unlink()

    def test_allocation_scope_reason_stale_and_no_direct_state(self):
        self.assertIn("tp.allocation", self.env, "C1 model is not implemented")
        rec = self.allocation()
        with self.assertRaises(UserError):
            rec.write({"state": "in_review", "version": rec.version})
        with self.assertRaises(AccessError):
            rec.with_user(self.reader).write({"name": "x", "version": rec.version})
        action = rec.action_submit()
        wizard = (
            self.env["tp.kd.transition"].with_user(self.editor).browse(action["res_id"])
        )
        rec.write({"scope": "Thay đổi trong phiên khác", "version": rec.version})
        with self.assertRaises(UserError):
            wizard.action_confirm()
        with self.assertRaises(AccessError):
            self.allocation("KD-AT-K02", project_id=self.other.id)
        with self.assertRaises(UserError):
            rec.write({"name": "Stale", "version": 1})
        self.env["tp.kd.grant"].search(
            [("user_id", "=", self.editor.id), ("domain", "=", "allocation")],
        ).write({"active": False})
        with self.assertRaises(AccessError):
            rec.action_submit()

    def test_allocation_parent_cycle_and_money_isolation(self):
        self.assertIn("tp.allocation", self.env, "C1 model is not implemented")
        parent = self.allocation()
        child = self.allocation("KD-AT-K02", parent_id=parent.id)
        with self.assertRaises(ValidationError):
            parent.write({"parent_id": child.id, "version": parent.version})
        parent.write(
            {
                "amount_ids": [
                    (
                        0,
                        0,
                        {
                            "amount_state": "confirmed",
                            "value": 100,
                            "tax_basis": "excluding_tax",
                        },
                    ),
                ],
                "version": parent.version,
            },
        )
        child.write(
            {
                "amount_ids": [
                    (
                        0,
                        0,
                        {
                            "amount_state": "confirmed",
                            "value": 120,
                            "tax_basis": "excluding_tax",
                        },
                    ),
                ],
                "version": child.version,
            },
        )
        self.assertTrue(parent.overrun_warning)
        self.assertEqual(parent.amount_ids.value, 100)
        amounts = self.env["tp.allocation.amount"].with_user(self.reader)
        self.assertEqual(amounts.search_count([]), 0)
        with self.assertRaises(AccessError):
            parent.amount_ids.with_user(self.reader).read(["value"])
        with self.assertRaises(UserError):
            parent.amount_ids.with_user(self.editor).write({"value": 200})
        self.env["tp.project.grant"].search(
            [("user_id", "=", self.editor.id), ("capability", "=", "financial_read")],
        ).write({"active": False})
        self.assertEqual(
            self.env["tp.allocation.amount"].with_user(self.editor).search_count([]),
            0,
        )

    def test_submission_amount_export_and_expiry(self):
        rec = self.allocation()
        rec.write(
            {
                "amount_ids": [
                    (
                        0,
                        0,
                        {
                            "amount_state": "confirmed",
                            "value": 0,
                            "tax_basis": "excluding_tax",
                        },
                    ),
                ],
                "version": rec.version,
            },
        )
        self.transition(rec, "submit")
        event = rec.event_ids.filtered(lambda e: e.action == "submit")
        protected = self.env["tp.allocation.event.amount"].with_user(self.reader)
        self.assertEqual(protected.search_count([]), 0)
        self.reader.group_ids = [
            Command.link(self.env.ref("base.group_allow_export").id),
        ]
        with self.assertRaises(AccessError):
            event.amount_ids.with_user(self.reader).export_data(["value"])
        self.assertNotIn('"value"', event.snapshot)
        snapshot_amount_id = event.amount_ids.with_user(self.editor).id
        self.assertEqual(event.amount_ids.with_user(self.editor).value, 0)
        self.assertEqual(
            event.amount_ids.with_user(self.editor).amount_state,
            "confirmed",
        )
        self.env["tp.project.grant"].search(
            [("user_id", "=", self.editor.id), ("capability", "=", "financial_read")],
        ).date_end = "2000-01-01"
        self.assertEqual(
            self.env["tp.allocation.event.amount"]
            .with_user(self.editor)
            .search_count([]),
            0,
        )
        with self.assertRaises(AccessError):
            self.env["tp.allocation.event.amount"].with_user(self.editor).browse(
                snapshot_amount_id,
            ).read(["value"])

    def test_reviewer_self_and_assignment_revoke(self):
        rec = self.allocation()
        with self.assertRaises(ValidationError):
            rec.write({"reviewer_id": self.editor.id, "version": rec.version})
        self.transition(rec, "submit")
        with self.assertRaises(AccessError):
            self.transition(rec, "return", self.reader, reason="Ngoài quyền")
        self.env["tp.project.assignment"].search(
            [("project_id", "=", self.project.id), ("user_id", "=", self.reviewer.id)],
        ).active = False
        with self.assertRaises(AccessError):
            self.transition(rec, "return", self.reviewer, reason="Đã mất phân công")

    def test_amount_unknown_zero_and_context_forgery(self):
        rec = self.allocation()
        with self.assertRaises(UserError):
            rec.with_context(_kd_internal=True).write(
                {"state": "in_review", "version": rec.version},
            )
        with self.assertRaises(ValidationError):
            rec.write(
                {
                    "amount_ids": [(0, 0, {"amount_state": "unconfirmed", "value": 1})],
                    "version": rec.version,
                },
            )
        with self.assertRaises(ValidationError):
            rec.write(
                {
                    "amount_ids": [
                        (
                            0,
                            0,
                            {
                                "amount_state": "confirmed",
                                "value": -1,
                                "tax_basis": "excluding_tax",
                            },
                        ),
                    ],
                    "version": rec.version,
                },
            )
        rec.write(
            {
                "amount_ids": [(0, 0, {"amount_state": "unconfirmed", "value": 0})],
                "version": rec.version,
            },
        )
        self.assertEqual(rec.amount_ids.amount_state, "unconfirmed")
        action = rec.action_submit()
        wizard = (
            self.env["tp.kd.transition"].with_user(self.editor).browse(action["res_id"])
        )
        with self.assertRaises(UserError):
            wizard.write({"target_id": self.contract.id})
        with self.assertRaises(AccessError):
            wizard.with_user(self.reader).read(["reason"])
