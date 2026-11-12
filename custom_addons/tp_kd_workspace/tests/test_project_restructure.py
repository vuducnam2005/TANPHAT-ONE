"""Project identity, package economics and capability command acceptance."""

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .test_opportunity_access import TestOpportunityAccess
from odoo.addons.tp_kd_workspace.migration_mapping import (
    apply_mapping,
    rollback_mapping,
)


@tagged("post_install", "-at_install")
class TestProjectRestructure(TestOpportunityAccess):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if 'tp_cross_department' in cls.env['tp.project.assignment']._fields:
            cls.env['tp.project.assignment'].search([('user_id', '=', cls.owner.id)]).write({
                'tp_cross_department': True, 'tp_cross_department_reason': 'Synthetic explicit workspace scope',
            })
        for domain in (
            "project_metadata",
            "project_status",
            "project_note",
            "bid",
            "wbs",
            "task_assignment",
            "task_progress",
        ):
            cls.env["tp.kd.grant"].create(
                {
                    "project_id": cls.projects[0].id,
                    "department_id": cls.department.id,
                    "user_id": cls.owner.id,
                    "domain": domain,
                    "capability": "prepare",
                    "reason": "Synthetic target HEAD",
                },
            )
        cls.env["tp.project.grant"].create(
            {
                "project_id": cls.projects[0].id,
                "department_id": cls.department.id,
                "user_id": cls.owner.id,
                "capability": "financial_draft_edit",
                "reason": "Synthetic money edit",
            },
        )

    def package(self, code="TEST-G01"):
        return (
            self.env["tp.bid.package"]
            .with_user(self.owner)
            .create(
                {
                    "project_id": self.projects[0].id,
                    "code": code,
                    "name": "Synthetic package",
                    "scope": "Synthetic source",
                    "deadline": "2030-01-01",
                },
            )
        )

    def test_investor_a_counterparty_b_same_project(self):
        p = self.projects[0].with_user(self.owner)
        investor = self.env["res.partner"].create({"name": "Synthetic investor A"})
        p._kd_apply(
            "metadata",
            "Synthetic evidence",
            p.kd_version,
            "metadata-key-01",
            {"kd_investor_id": investor.id},
        )
        lead = self.make()
        self.assertEqual(lead.kd_investor_id, investor)
        self.assertEqual(lead.partner_id, self.partner)
        self.assertEqual(p.partner_id, self.partner)
        contract = self.env["tp.contract"].create(
            {
                "code": "KDPROJECT-TEST-A03",
                "name": "Synthetic contract B",
                "project_id": p.id,
                "company_id": p.company_id.id,
                "partner_id": self.partner.id,
                "contract_type": "owner",
            },
        )
        self.assertEqual(contract.partner_id, self.partner)

    def test_multiple_packages_attempts_direct_and_outcome_isolation(self):
        a, b = self.package(), self.package("TEST-G02")
        one, two = self.make(kd_package_id=a.id), self.make(kd_package_id=a.id)
        self.assertEqual(one.tp_project_id, two.tp_project_id)
        self.assertEqual(len(a.lead_ids), 2)
        p = a.project_id
        p._kd_apply(
            "bid",
            "Synthetic result source",
            p.kd_version,
            "bid-result-key",
            {"stage": "participating", "outcome": "won"},
            a,
        )
        self.assertEqual(a.outcome, "won")
        self.assertEqual(b.outcome, "unknown")
        self.assertEqual(p.kd_lifecycle, "tracking")
        self.make(kd_route="direct")
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.make(kd_route="direct", kd_package_id=a.id)
        with self.assertRaises(AccessError):
            a.write({"stage": "awaiting_result"})

    def test_partners_many_roles_and_duplicate_scope(self):
        p = self.projects[0]
        model = self.env["tp.project.participation"].with_user(self.owner)
        vals = {
            "project_id": p.id,
            "partner_id": self.partner.id,
            "role": "investor",
            "reason": "Synthetic evidence",
        }
        first = model.create(vals)
        model.create({**vals, "role": "counterparty"})
        model.create({**vals, "package_id": self.package().id})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            model.create(vals)
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            model.with_user(self.support).create({**vals, "role": "coordinator"})
        with self.assertRaises(UserError):
            first.unlink()

    def test_money_unknown_zero_separate_meanings_and_revocation(self):
        package = self.package()
        model = self.env["tp.bid.package.amount"].with_user(self.owner)
        vals = {
            "package_id": package.id,
            "kind": "package_total",
            "amount_state": "estimated",
            "value": 10_000_000_000,
            "currency_id": self.env.company.currency_id.id,
            "tax_basis": "excluding_tax",
            "source": "Synthetic estimate",
            "estimate_date": "2026-11-09",
        }
        total = model.create(vals)
        share = model.create({**vals, "kind": "company_share", "value": 3_000_000_000})
        offer = model.create(
            {**vals, "kind": "company_offer", "amount_state": "unknown", "value": 0},
        )
        self.assertEqual(total.value, 10_000_000_000)
        self.assertEqual(share.value, 3_000_000_000)
        self.assertEqual(offer.amount_state, "unknown")
        offer.write({"amount_state": "estimated", "version": offer.version})
        self.assertEqual(offer.value, 0)
        with self.assertRaises(UserError):
            offer.write({"value": 1, "version": 1})
        self.assertEqual(
            self.env["tp.project.update"].search_count(
                [("package_id", "=", package.id), ("kind", "=", "amount")],
            ),
            4,
        )
        support = total.with_user(self.support)
        with self.assertRaises(AccessError):
            support.read(["value"])
        with self.assertRaises(AccessError):
            support.export_data(["value"])
        self.assertFalse(model.with_user(self.support).search([("value", ">", 0)]))
        self.assertFalse(
            model.with_user(self.support)._read_group([], [], ["value:sum"])[0][0],
        )
        self.money.active = False
        with self.assertRaises(AccessError):
            _ = total.value
        self.assertEqual(package.budget_display, "Không có quyền xem tiền")

    def test_status_reason_version_retry_and_reopen(self):
        p = self.projects[0].with_user(self.owner)
        version = p.kd_version
        event = p._kd_apply(
            "status",
            "Synthetic reason",
            version,
            "status-key-001",
            {"state": "executing"},
        )
        self.assertEqual(p.kd_lifecycle, "executing")
        self.assertEqual(
            p._kd_apply(
                "status",
                "Synthetic reason",
                version,
                "status-key-001",
                {"state": "executing"},
            ),
            event,
        )
        with self.assertRaises(UserError):
            p._kd_apply(
                "status",
                "changed",
                p.kd_version,
                "status-key-001",
                {"state": "paused"},
            )
        with self.assertRaises(UserError):
            p._kd_apply(
                "status",
                "stale",
                version,
                "status-key-002",
                {"state": "paused"},
            )
        with self.assertRaises(AccessError):
            p.with_user(self.support)._kd_apply(
                "status",
                "denied",
                p.kd_version,
                "status-key-003",
                {"state": "paused"},
            )
        p._kd_apply(
            "status",
            "Synthetic end",
            p.kd_version,
            "status-key-end",
            {"state": "ended"},
        )
        with self.assertRaises(AccessError):
            p._kd_apply(
                "status",
                "Synthetic reopen",
                p.kd_version,
                "reopen-key-001",
                {"state": "tracking"},
            )
        with self.assertRaises(AccessError):
            p.write({"kd_lifecycle": "tracking"})

    def test_append_only_notes_preserve_submitted_snapshot(self):
        lead = self.make()
        lead.action_kd_prepare()
        self.env["tp.kd.grant"].create(
            {
                "project_id": self.projects[0].id,
                "department_id": self.department.id,
                "user_id": self.owner.id,
                "domain": "opportunity",
                "capability": "submit",
                "reason": "Synthetic submit",
            },
        )
        lead.action_kd_record_submission()
        before = lead.read(["kd_scope", "kd_receipt", "kd_bid_state"])
        p = self.projects[0].with_user(self.owner)
        eid = p._kd_apply(
            "note",
            "Synthetic supplemental note",
            p.kd_version,
            "note-key-001",
        )
        p._kd_apply(
            "note",
            "Synthetic correction",
            p.kd_version,
            "note-key-002",
            {"correction_id": eid},
        )
        event = self.env["tp.project.update"].with_user(self.owner).browse(eid)
        with self.assertRaises(AccessError):
            event.write({"reason": "overwrite"})
        with self.assertRaises(AccessError):
            event.unlink()
        with self.assertRaises(AccessError):
            event.with_user(self.support).read(["reason"])
        self.assertEqual(lead.read(["kd_scope", "kd_receipt", "kd_bid_state"]), before)

    def test_task_capabilities_are_separate_from_money_and_generic_write(self):
        p = self.projects[0]
        command = (
            self.env["tp.task.command"]
            .with_user(self.owner)
            .create({"project_id": p.id, "operation": "create"})
        )
        command.write(
            {
                "name": "Synthetic WBS",
                "deliverable": "Synthetic output",
                "reason": "Synthetic work scope",
            },
        )
        command.action_confirm()
        task = self.env["project.task"].search(
            [("name", "=", "Synthetic WBS"), ("project_id", "=", p.id)],
        )
        self.assertEqual(len(task), 1)
        command.action_confirm()
        self.assertEqual(len(task), 1)
        with self.assertRaises(AccessError):
            task.with_user(self.owner).write({"name": "generic bypass"})
        progress = (
            self.env["tp.task.command"]
            .with_user(self.owner)
            .create({"project_id": p.id, "task_id": task.id, "operation": "progress"})
        )
        progress.write(
            {"target_state": "1_done", "reason": "Synthetic output delivered"},
        )
        self.money.active = False
        progress.action_confirm()
        self.assertEqual(task.state, "1_done")
        with self.assertRaises(AccessError):
            task.with_user(self.support).action_kd_progress()

    def test_expired_and_revoked_capability(self):
        p = self.projects[0].with_user(self.owner)
        g = self.env["tp.kd.grant"].search(
            [
                ("project_id", "=", p.id),
                ("user_id", "=", self.owner.id),
                ("domain", "=", "project_status"),
            ],
        )
        g.date_end = "2000-01-01"
        with self.assertRaises(AccessError):
            p._kd_apply(
                "status",
                "expired",
                p.kd_version,
                "expired-key-01",
                {"state": "executing"},
            )
        g.write({"date_end": False, "active": False})
        with self.assertRaises(AccessError):
            p._kd_apply(
                "status",
                "revoked",
                p.kd_version,
                "revoked-key-01",
                {"state": "executing"},
            )

    def test_two_perspectives_same_project_and_filtered_drilldown(self):
        self.package()
        p = self.projects[0]
        self.env["project.task"].create(
            {"name": "Synthetic output", "project_id": p.id, "state": "1_done"},
        )
        view = self.env["tp.project.perspective"].with_user(self.owner)
        management = view.get_perspective("management", p.id, 10, 0)
        governance = view.get_perspective("governance", p.id)
        self.assertEqual(management["selected"], governance["selected"])
        self.assertEqual(management["total"], 1)
        self.assertEqual(management["counts"][1]["count"], 1)
        self.assertEqual(governance["counts"][0]["count"], 1)
        self.assertEqual(len(governance["rows"]), 7)
        a = view.switch_perspective("management", p.id, True)
        b = view.switch_perspective("governance", p.id, True)
        self.assertEqual(a["res_id"], b["res_id"])
        self.assertNotEqual(a["views"], b["views"])
        source = view.open_perspective_source("management", "done", p.id)
        self.assertIn(("project_id", "in", [p.id]), source["domain"])
        self.assertIn(("state", "=", "1_done"), source["domain"])
        with self.assertRaises(AccessError):
            view.get_perspective("governance", self.projects[1].id)
        with self.assertRaises(UserError):
            view.get_perspective("management", p.id, 11)

    def test_task_stale_foreign_parent_and_recipient_without_assignment(self):
        model = self.env["tp.task.command"].with_user(self.owner)
        t = self.env["project.task"].create(
            {
                "name": "Synthetic original",
                "project_id": self.projects[0].id,
                "kd_responsible_id": self.owner.id,
                "user_ids": [(6, 0, self.owner.ids)],
            },
        )
        first = model.create(
            {"project_id": t.project_id.id, "task_id": t.id, "operation": "edit"},
        )
        stale = model.create(
            {"project_id": t.project_id.id, "task_id": t.id, "operation": "edit"},
        )
        first.write(
            {
                "name": "Synthetic updated",
                "deliverable": "Synthetic output",
                "reason": "Synthetic source",
            },
        )
        first.action_confirm()
        event = self.env["tp.task.update"].search([("task_id", "=", t.id)], limit=1)
        self.assertEqual(event.before_values["name"], "Synthetic original")
        self.assertEqual(event.after_values["name"], "Synthetic updated")
        self.assertEqual(event.after_values["deliverable"], "Synthetic output")
        with self.assertRaises(AccessError):
            event.with_user(self.owner).write({"reason": "overwrite"})
        stale.write(
            {
                "name": "Synthetic overwrite",
                "deliverable": "Synthetic output",
                "reason": "Synthetic stale",
            },
        )
        with self.assertRaises(UserError):
            stale.action_confirm()
        assignment = self.env["tp.project.assignment"].search(
            [("user_id", "=", self.other.id)],
        )
        assignment.active = False
        assign = model.create(
            {"project_id": t.project_id.id, "task_id": t.id, "operation": "assign"},
        )
        assign.write(
            {"responsible_id": self.other.id, "reason": "Synthetic denied recipient"},
        )
        with self.assertRaises(AccessError):
            assign.action_confirm()
        foreign = self.env["project.task"].create(
            {"name": "Synthetic outside", "project_id": self.projects[1].id},
        )
        edit = model.create(
            {"project_id": t.project_id.id, "task_id": t.id, "operation": "edit"},
        )
        edit.write(
            {
                "parent_id": foreign.id,
                "deliverable": "Synthetic output",
                "reason": "Synthetic foreign parent",
            },
        )
        with self.assertRaises((AccessError, ValidationError)):
            edit.action_confirm()

    def test_explicit_mapping_dry_run_idempotency_exact_rollback(self):

        lead = self.make()
        package = self.package()
        mapping = [
            {
                "lead_id": lead.id,
                "project_id": package.project_id.id,
                "package_id": package.id,
                "source": "Synthetic ID evidence",
                "verified_by": "Synthetic verifier",
            },
        ]
        journal = []
        before = lead.read(
            ["tp_project_id", "kd_package_id", "user_id", "company_id", "kd_bid_state"],
        )
        self.assertEqual(
            apply_mapping(self.env, mapping)[0]["delta"],
            {"kd_package_id": package.id},
        )
        self.assertEqual(
            lead.read(
                [
                    "tp_project_id",
                    "kd_package_id",
                    "user_id",
                    "company_id",
                    "kd_bid_state",
                ],
            ),
            before,
        )

        apply_mapping(self.env, mapping, dry_run=False, journal=journal)
        self.assertEqual(lead.kd_package_id, package)
        apply_mapping(self.env, mapping, dry_run=False, journal=journal)
        self.assertEqual(len(journal), 1)
        with self.assertRaises(AccessError):
            apply_mapping(self.env(user=self.support), mapping, dry_run=False)
        rollback_mapping(self.env, journal)
        rollback_mapping(self.env, journal)
        self.assertEqual(
            lead.read(
                [
                    "tp_project_id",
                    "kd_package_id",
                    "user_id",
                    "company_id",
                    "kd_bid_state",
                ],
            ),
            before,
        )

    def test_direct_project_only_mapping_without_fake_package(self):
        lead = self.env["crm.lead"].create(
            {
                "name": "Synthetic unlinked direct",
                "type": "opportunity",
                "company_id": self.projects[0].company_id.id,
                "partner_id": self.partner.id,
                "kd_route": "direct",
            },
        )
        mapping = [
            {
                "lead_id": lead.id,
                "project_id": self.projects[0].id,
                "package_id": False,
                "source": "Synthetic explicit mapping",
                "verified_by": "Synthetic verifier",
            },
        ]
        journal = []
        self.assertEqual(
            apply_mapping(self.env, mapping)[0]["delta"],
            {"tp_project_id": self.projects[0].id},
        )
        apply_mapping(self.env, mapping, dry_run=False, journal=journal)
        apply_mapping(self.env, mapping, dry_run=False, journal=journal)
        self.assertFalse(lead.kd_package_id)
        self.assertEqual(len(journal), 1)
        rollback_mapping(self.env, journal)
        self.assertFalse(lead.tp_project_id)

    def test_overview_task_create_uses_capability_command(self):
        overview = self.env["tp.kd.overview"].with_user(self.owner)
        action = overview.action_kd_create("task", self.projects[0].id)
        self.assertEqual(action["res_model"], "tp.task.command")
        with self.assertRaises(UserError):
            overview.action_kd_create("task")
        with self.assertRaises(AccessError):
            overview.with_user(self.support).action_kd_create(
                "task",
                self.projects[0].id,
            )

    def test_package_context_cannot_supply_result_without_command(self):
        with self.assertRaises(UserError), self.env.cr.savepoint():
            self.env["tp.bid.package"].with_user(self.owner).with_context(
                default_stage="awaiting_result",
                default_outcome="won",
            ).create(
                {
                    "project_id": self.projects[0].id,
                    "code": "SYN-CONTEXT-DENIED",
                    "name": "Synthetic denied result",
                    "scope": "Synthetic",
                },
            )

    def test_mapping_missing_counterparty_is_reconcile_in_dry_run_and_apply(self):
        lead = self.env["crm.lead"].create(
            {
                "name": "Synthetic missing counterparty",
                "type": "opportunity",
                "company_id": self.projects[0].company_id.id,
                "kd_route": "direct",
            },
        )
        mapping = [
            {
                "lead_id": lead.id,
                "project_id": self.projects[0].id,
                "package_id": False,
                "source": "Synthetic ID evidence",
                "verified_by": "Synthetic verifier",
            },
        ]
        journal = []
        for dry in (True, False):
            with self.assertRaises(UserError):
                apply_mapping(self.env, mapping, dry_run=dry, journal=journal)
        self.assertFalse(journal)
        self.assertFalse(lead.tp_project_id)
