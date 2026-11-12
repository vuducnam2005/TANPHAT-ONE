"""HEAD intervention keeps the original actors and the four-eyes boundary."""
import json
from uuid import uuid4

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import new_test_user
from odoo.tools import BinaryBytes

from .test_allocation import TestAllocation
from odoo.addons.tp_contract.exceptions import ContractWorkflowError


class TestHeadDossiers(TestAllocation):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.head = new_test_user(cls.env, login="kd_head_dossier", groups="tp_core.group_user")
        cls.role = cls.env["tp.kd.department.role"].create({
            "user_id": cls.head.id, "company_id": cls.env.company.id,
            "department_id": cls.department.id, "reason": "Synthetic HEAD dossier acceptance",
        })
        cls.env["tp.project.grant"].create({
            "project_id": cls.project.id, "department_id": cls.department.id,
            "user_id": cls.reviewer.id, "capability": "contract_review_commercial",
            "reason": "Synthetic HEAD reviewer",
        })

    def run_contract(self, user, action, payload, contract=None, revision=None, key=None):
        data = dict(payload)
        reason = data.pop("reason", None) if action == "edit_draft" else None
        return self.env["tp.contract.workflow"].with_user(user)._tp_run(
            action, data, key=key or uuid4().hex, intervention_reason=reason,
            contract_id=contract.id if contract else None,
            revision_id=revision.id if revision else None,
        )

    def contract_draft(self, user=None):
        result = self.run_contract(user or self.head, "create_contract", {
            "project_id": self.project.id, "code": "HEAD-" + uuid4().hex[:10],
            "name": "Synthetic HEAD draft", "contract_type": "owner", "currency": "VND",
            "lines": [{"scope_key": "A", "name": "Scope", "amount": {
                "state": "confirmed", "value": "100", "tax_basis": "excluding_tax",
            }}],
        })
        return result["contract"], result["revision"]

    def test_head_edit_other_draft_reason_snapshot_and_revoke(self):
        rec = self.allocation().with_user(self.head)
        with self.assertRaises(UserError):
            rec.write({"scope": "Changed", "version": rec.version})
        previous = rec.version
        rec.write({"scope": "Changed", "version": previous,
                   "intervention_reason": "Complete missing scope for colleague"})
        self.assertEqual(rec.owner_id, self.editor)
        event = rec.event_ids.filtered(lambda e: e.action == "head_edit")
        self.assertEqual(event.actor_id, self.head)
        self.assertEqual(json.loads(event.snapshot_before)["scope"], "Khảo sát địa hình")
        self.assertEqual(json.loads(event.snapshot)["scope"], "Changed")
        self.assertEqual((event.version_before, event.version), (previous, previous + 1))
        self.role.sudo().write({"active": False, "reason": "Synthetic revoke"})
        with self.assertRaises(AccessError):
            rec.write({"scope": "Revoked", "version": rec.version,
                       "intervention_reason": "Must be denied"})

    def test_head_typed_takeover_and_contributor_cannot_review(self):
        rec = self.allocation()
        self.transition(rec, "submit")
        action = rec.with_user(self.head).action_take_review()
        wizard = self.env["tp.kd.transition"].with_user(self.head).browse(action["res_id"])
        wizard.reason = "Department review takeover"
        wizard.action_confirm()
        self.assertEqual(rec.reviewer_id, self.head)
        takeover = rec.event_ids.filtered(lambda e: e.action == "take_review")
        self.assertEqual(json.loads(takeover.snapshot_before)["reviewer_id"], self.reviewer.id)
        self.transition(rec, "return", self.head, reason="Missing evidence")
        self.transition(rec, "rework", self.head, reason="Complete evidence")
        rec.with_user(self.head).write({"scope": "HEAD authored scope", "version": rec.version,
                                       "intervention_reason": "Complete evidence"})
        rec.with_user(self.editor).write({"reviewer_id": self.reviewer.id, "version": rec.version})
        self.transition(rec, "submit", fix_summary="Evidence completed")
        with self.assertRaises(AccessError):
            rec.with_user(self.head).action_take_review()
        self.transition(rec, "return", self.reviewer, reason="New round required")
        self.transition(rec, "rework", self.editor, reason="Independent new version")
        rec.with_user(self.editor).write({"reviewer_id": self.head.id, "scope": "Independent updated scope", "version": rec.version})
        self.transition(rec, "submit", self.editor, fix_summary="Independent new version")
        self.transition(rec, "return", self.head, reason="Current version reviewed independently")

    def test_head_owner_reassignment_requires_valid_scope_and_audit(self):
        rec = self.allocation()
        action = rec.with_user(self.head).action_assign()
        wizard = self.env["tp.kd.transition"].with_user(self.head).browse(action["res_id"])
        wizard.write({"owner_id": self.head.id, "reviewer_id": self.reviewer.id,
                      "reason": "Head takes preparation responsibility"})
        wizard.action_confirm()
        self.assertEqual(rec.owner_id, self.head)
        self.assertEqual(rec.event_ids.filtered(lambda e: e.action == "assign").actor_id, self.head)
        self.assertFalse(rec._kd_review_eligible(self.editor), "Reassigning responsibility must not erase the previous preparer")
        with self.assertRaises(AccessError):
            rec.with_user(self.reader).action_assign()

    def test_head_management_across_remaining_six_typed_models(self):
        """Exercise each concrete model as a normal HEAD, beyond the shared allocation helper."""
        for domain in ("production", "acceptance", "payment", "plan", "credential", "obligation"):
            for user, capabilities in ((self.editor, ("prepare", "submit")), (self.reviewer, ("review",))):
                for capability in capabilities:
                    self.env["tp.kd.grant"].create({
                        "project_id": self.project.id, "department_id": self.department.id,
                        "user_id": user.id, "domain": domain, "capability": capability,
                        "reason": "Synthetic six-domain HEAD integration",
                    })
        partner = self.env["res.partner"].create({"name": "Synthetic HEAD dossier subject"})
        common = {
            "project_id": self.project.id, "contract_id": self.contract.id,
            "name": "Synthetic HEAD managed dossier", "scope": "Synthetic surveyed scope",
            "owner_id": self.editor.id, "reviewer_id": self.reviewer.id,
            "date": "2026-11-06", "date_due": "2026-11-20",
            "period_from": "2026-11-01", "period_to": "2026-11-30",
        }
        production_values = {"quantity": 5, "unit": "km", "completion_percent": 50}
        source = self.env["tp.production"].with_user(self.head).create({
            **common, **production_values, "code": "HEAD-SIX-SOURCE",
        })
        cases = (
            ("tp.production", production_values),
            ("tp.acceptance", {"production_id": source.id, "quantity": 2, "unit": "km",
                "round_code": "Synthetic round", "counterparty_id": partner.id,
                "evidence_checklist": "Synthetic measured evidence, unverified"}),
            ("tp.payment.request", {"direction": "receipt", "payment_basis": "advance",
                "partner_id": partner.id, "advance_basis": "Synthetic draft advance clause",
                "document_checklist": "Synthetic advance evidence, unverified"}),
            ("tp.periodic.plan", {"period_kind": "month"}),
            ("tp.credential", {"subject_id": partner.id, "subject_kind": "person",
                "credential_kind": "Synthetic survey qualification", "valid_from": "2026-01-01",
                "valid_to": "2026-12-31", "source_note": "Synthetic professional evidence, unverified"}),
            ("tp.obligation", {"obligation_kind": "contract_docs",
                "document_checklist": "Synthetic missing handover evidence",
                "checklist_update_reason": "Synthetic initial checklist"}),
        )
        for index, (model, extra) in enumerate(cases):
            with self.subTest(model=model):
                rec = self.env[model].with_user(self.head).create({
                    **common, **extra, "code": f"HEAD-SIX-{index}",
                })
                self.assertEqual(rec.owner_id, self.editor)
                self.assertEqual(rec.event_ids.filtered(lambda e: e.action == "head_create").actor_id, self.head)
                with self.assertRaises(UserError), self.env.cr.savepoint():
                    rec.write({"scope": "Unaudited change", "version": rec.version})
                changes = {"scope": "HEAD completed colleague scope", "version": rec.version,
                           "intervention_reason": "Synthetic colleague correction"}
                if rec._kd_money_model:
                    changes["amount_ids"] = [Command.create({
                        "amount_state": "confirmed", "value": 100, "tax_basis": "excluding_tax",
                        **({"measure": "production"} if model == "tp.periodic.plan" else {}),
                    })]
                rec.write(changes)
                self.assertEqual(rec.owner_id, self.editor)
                if rec._kd_money_model:
                    rec.write({"version": rec.version, "intervention_reason": "Synthetic confirmed zero",
                        "amount_ids": [Command.update(rec.amount_ids.id, {"value": 0})]})
                    self.assertEqual((rec.amount_ids.amount_state, rec.amount_ids.value), ("confirmed", 0))
                    event = rec.event_ids.filtered(lambda e: e.action == "head_edit")[-1:]
                    self.assertEqual(event.amount_ids.filtered(lambda a: a.snapshot_side == "before").value, 100)
                    self.assertEqual(event.amount_ids.filtered(lambda a: a.snapshot_side == "after").value, 0)
                self.transition(rec, "submit", self.head)
                self.assertEqual(rec.state, "in_review")
                with self.assertRaises(AccessError), self.env.cr.savepoint():
                    rec.action_take_review()
                self.transition(rec, "return", self.reviewer, reason="Synthetic independent review")
                self.transition(rec, "rework", self.editor, reason="Synthetic independent new round")
                rec.with_user(self.editor).write({"scope": "Independent staff new round", "version": rec.version})
                self.transition(rec, "submit", self.editor, fix_summary="Synthetic independent new scope")
                self.transition(rec, "take_review", self.head, reason="Synthetic department review takeover")
                self.assertEqual(rec.reviewer_id, self.head)
                takeover = rec.event_ids.filtered(lambda e: e.action == "take_review")[-1:]
                self.assertEqual(json.loads(takeover.snapshot_before)["reviewer_id"], self.reviewer.id)
                self.transition(rec, "return", self.head, reason="Synthetic HEAD reviewed new round")
                self.assertEqual(rec.state, "returned")

    def test_contract_intervention_money_snapshot_and_four_eyes(self):
        for capability in ("contract_draft_edit", "contract_submit", "financial_read", "financial_draft_edit"):
            if not self.env["tp.project.grant"].search_count([
                ("project_id", "=", self.project.id), ("user_id", "=", self.editor.id), ("capability", "=", capability),
            ]):
                self.env["tp.project.grant"].create({
                    "project_id": self.project.id, "department_id": self.department.id if capability != "financial_read" else False,
                    "user_id": self.editor.id, "capability": capability, "reason": "Synthetic contract author",
                })
        contract, revision = self.contract_draft(self.editor)
        payload = {"expected_version": contract.aggregate_version,
                   "lines": [{"scope_key": "A", "name": "Scope clarified", "amount": {
                       "state": "confirmed", "value": "0", "tax_basis": "excluding_tax"}}]}
        with self.assertRaises(ContractWorkflowError), self.env.cr.savepoint():
            self.run_contract(self.head, "edit_draft", payload, contract, revision)
        key = uuid4().hex
        payload["reason"] = "Correct draft value for colleague"
        self.run_contract(self.head, "edit_draft", payload, contract, revision, key)
        replay = self.run_contract(self.head, "edit_draft", payload, contract, revision, key)
        self.assertTrue(replay["replayed"])
        audit = self.env["tp.contract.audit"].search([
            ("revision_id", "=", revision.id), ("action", "=", "edit_draft")])
        amounts = self.env["tp.contract.audit.amount"].search([("audit_id", "=", audit.id)])
        self.assertEqual(amounts.before_snapshot["total"]["value"], "100")
        self.assertEqual(amounts.after_snapshot["total"]["value"], "0")
        self.assertEqual(revision.business_owner_id, self.editor)
        with self.assertRaises(ContractWorkflowError), self.env.cr.savepoint():
            self.run_contract(self.editor, "submit_review", {
                "expected_version": contract.aggregate_version, "reviewer_id": self.head.id,
            }, contract, revision)
        self.run_contract(self.editor, "submit_review", {
            "expected_version": contract.aggregate_version, "reviewer_id": self.reviewer.id,
        }, contract, revision)
        with self.assertRaises(ContractWorkflowError), self.env.cr.savepoint():
            self.run_contract(self.head, "take_review", {
                "expected_version": contract.aggregate_version, "reason": "Cannot review own edit",
            }, contract, revision)
        self.run_contract(self.reviewer, "return_review", {
            "expected_version": contract.aggregate_version, "reason": "Separate draft round",
        }, contract, revision)
        self.run_contract(self.editor, "begin_rework", {
            "expected_version": contract.aggregate_version, "reason": "Independent new draft version",
        }, contract, revision)
        self.run_contract(self.editor, "edit_draft", {
            "expected_version": contract.aggregate_version, "revision": {"name": "Independent corrected version"},
        }, contract, revision)
        self.run_contract(self.editor, "submit_review", {
            "expected_version": contract.aggregate_version, "reviewer_id": self.head.id,
            "fix_summary": "Independent updated version",
        }, contract, revision)
        self.run_contract(self.head, "return_review", {
            "expected_version": contract.aggregate_version, "reason": "Current version reviewed independently",
        }, contract, revision)

    def test_contract_takeover_preserves_original_and_blocks_author(self):
        contract, revision = self.contract_draft()
        self.run_contract(self.head, "submit_review", {
            "expected_version": contract.aggregate_version, "reviewer_id": self.reviewer.id,
        }, contract, revision)
        with self.assertRaises(ContractWorkflowError):
            self.run_contract(self.head, "take_review", {
                "expected_version": contract.aggregate_version, "reason": "Cannot self-review",
            }, contract, revision)
        # Another creator's untouched draft can be reviewed without changing its original reviewer.
        for cap in ("contract_draft_edit", "contract_submit", "financial_read", "financial_draft_edit"):
            self.env["tp.project.grant"].create({
                "project_id": self.project.id, "department_id": self.department.id if cap != "financial_read" else False,
                "user_id": self.editor.id, "capability": cap, "reason": "Synthetic contract author",
            }) if not self.env["tp.project.grant"].search_count([
                ("project_id", "=", self.project.id), ("user_id", "=", self.editor.id), ("capability", "=", cap),
            ]) else None
        other, rev = self.contract_draft(self.editor)
        self.run_contract(self.editor, "submit_review", {
            "expected_version": other.aggregate_version, "reviewer_id": self.reviewer.id,
        }, other, rev)
        submission = rev.sudo().submission_ids
        self.run_contract(self.head, "take_review", {
            "expected_version": other.aggregate_version, "reason": "Department supervision",
        }, other, rev)
        self.assertEqual(submission.reviewer_id, self.reviewer)
        self.assertEqual(submission.assigned_reviewer_id, self.head)
        reports = self.env["tp.kd.report.center"].with_user(self.head)
        for key in ("R01", "R05"):
            report = reports.get_kd_report(key, {"project_id": self.project.id}, page_size=100)
            row = next(row for row in report["rows"] if row["res_id"] == (other.id if key == "R01" else rev.id)
                       and row["res_model"] == ("tp.contract" if key == "R01" else "tp.contract.revision"))
            self.assertEqual(row["reviewer_label"], self.head.name)
            if key == "R05":
                self.assertTrue(row["is_my_review"])
        overview = self.env["tp.kd.overview"].with_user(self.head).create({})
        self.assertIn(rev.id, self.env["tp.contract.revision"].with_user(self.head).search(
            overview._inbox_domain("tp.contract.revision", "review")).ids)
        other_overview = self.env["tp.kd.overview"].with_user(self.reviewer).create({})
        self.assertNotIn(rev.id, self.env["tp.contract.revision"].with_user(self.reviewer).search(
            other_overview._inbox_domain("tp.contract.revision", "review")).ids)
        self.run_contract(self.head, "return_review", {
            "expected_version": other.aggregate_version, "reason": "Need clarification",
        }, other, rev)
        self.assertEqual(submission.returned_by_id, self.head)

    def test_typed_files_live_scope_stale_archive_and_submitted_evidence(self):
        rec = self.allocation().with_user(self.head)
        opened = rec.action_document_add()
        wizard = self.env["tp.kd.transition"].with_user(self.head).browse(opened["res_id"])
        wizard.write({"reason": "Complete colleague evidence", "document_name": "Scope evidence",
                      "file_name": "scope.txt", "file": BinaryBytes(b"typed evidence"), "confidentiality": "financial"})
        wizard.action_confirm()
        doc = self.env["tp.kd.document"].with_user(self.head).search([("target_model", "=", rec._name), ("target_id", "=", rec.id)])
        self.assertEqual(bytes(doc.file), b"typed evidence")
        self.assertEqual(rec.owner_id, self.editor)
        version = rec.version
        wizard.action_confirm()
        self.assertEqual(rec.version, version)
        with self.assertRaises(AccessError):
            doc.with_user(self.reader).read(["file"])
        attachment = self.env["ir.attachment"].sudo().search([
            ("res_model", "=", "tp.kd.document"), ("res_id", "=", doc.id), ("res_field", "=", "file")])
        self.assertTrue(attachment)
        with self.assertRaises(AccessError):
            attachment.with_user(self.head).write({"public": True})
        self.transition(rec, "submit", self.head)
        self.transition(rec, "return", self.reviewer, reason="Additional evidence")
        self.transition(rec, "rework", self.head, reason="Add separate evidence")
        action = rec.action_document_remove()
        removal = self.env["tp.kd.transition"].with_user(self.head).browse(action["res_id"])
        removal.write({"reason": "Keep submitted evidence", "document_id": doc.id})
        with self.assertRaises(UserError):
            removal.action_confirm()
        self.role.sudo().write({"active": False, "reason": "Synthetic revoke with cached binary"})
        with self.assertRaises(AccessError):
            doc.read(["file"])
        with self.assertRaises(AccessError):
            self.env["ir.binary"].with_user(self.head)._find_record(res_model="ir.attachment", res_id=attachment.id, access_token="old-token")

    def test_head_contract_files_are_versioned_audited_and_frozen(self):
        contract, revision = self.contract_draft()
        workflow = self.env["tp.contract.workflow"].with_user(self.head)
        self.assertNotIn("document_add", workflow._tp_available_actions(contract, revision)[0], "The REST action enum stays unchanged")
        self.assertIn("document_add", workflow._tp_available_actions(contract, revision, native=True)[0])
        for key in ("R01", "R05"):
            report = self.env["tp.kd.report.center"].with_user(self.head).get_kd_report(key, {"project_id": self.project.id}, page_size=100)
            row = next(row for row in report["rows"] if row["res_id"] == (contract.id if key == "R01" else revision.id)
                       and row["res_model"] == ("tp.contract" if key == "R01" else "tp.contract.revision"))
            self.assertEqual(row["owner_id"], self.head.id)
        wizard = self.env["tp.contract.native.return"].with_user(self.head).create({
            "contract_id": contract.id, "revision_id": revision.id, "operation": "document_add",
            "reason": "Attach draft evidence", "document_name": "Scope evidence",
            "file_name": "scope.txt", "file": BinaryBytes(b"synthetic evidence"),
            "document_kind": "technical_scope", "confidentiality": "general",
        })
        wizard.action_confirm()
        document = self.env["tp.contract.document"].search([("revision_id", "=", revision.id)])
        self.assertTrue(document)
        self.assertTrue(self.env["tp.contract.audit"].search([
            ("revision_id", "=", revision.id), ("action", "=", "document_add"),
        ]))
        self.run_contract(self.head, "submit_review", {
            "expected_version": contract.aggregate_version, "reviewer_id": self.reviewer.id,
        }, contract, revision)
        with self.assertRaises((UserError, ContractWorkflowError)):
            self.run_contract(self.head, "document_remove", {
                "expected_version": contract.aggregate_version, "reason": "Forbidden cleanup",
                "document_id": document.id,
            }, contract, revision)

    def test_contract_new_rework_document_can_archive_without_altering_prior_evidence(self):
        contract, revision = self.contract_draft()

        def upload(name):
            wizard = self.env["tp.contract.native.return"].with_user(self.head).create({
                "contract_id": contract.id, "revision_id": revision.id, "operation": "document_add",
                "reason": "Attach draft evidence", "document_name": name,
                "file_name": name + ".txt", "file": BinaryBytes(name.encode()),
                "document_kind": "other", "confidentiality": "financial"})
            wizard.action_confirm()
            return self.env["tp.contract.document"].search([("revision_id", "=", revision.id), ("name", "=", name)])
        original = upload("Original evidence")
        self.run_contract(self.head, "submit_review", {
            "expected_version": contract.aggregate_version, "reviewer_id": self.reviewer.id,
        }, contract, revision)
        self.run_contract(self.reviewer, "return_review", {
            "expected_version": contract.aggregate_version, "reason": "Additional separate evidence",
        }, contract, revision)
        self.run_contract(self.head, "begin_rework", {
            "expected_version": contract.aggregate_version, "reason": "New draft round",
        }, contract, revision)
        extra = upload("Extra draft evidence")
        self.run_contract(self.head, "document_remove", {
            "expected_version": contract.aggregate_version, "reason": "Accidental draft evidence",
            "document_id": extra.id,
        }, contract, revision)
        self.assertFalse(extra.active)
        self.assertEqual(bytes(extra.file), b"Extra draft evidence")
        with self.assertRaises(UserError), self.env.cr.savepoint():
            self.run_contract(self.head, "document_remove", {
                "expected_version": contract.aggregate_version, "reason": "Must retain submitted evidence",
                "document_id": original.id,
            }, contract, revision)
