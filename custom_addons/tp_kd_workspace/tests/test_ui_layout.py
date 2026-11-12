"""KD-UI-003 — presentation contract of the KH-KD tables and detail screens.

These tests pin the layout hooks (classes, paging, optional columns, page names) and, more
importantly, that the re-layout did not drop or loosen anything: money stays out of lists, the
money page keeps its read gate, and TP Contracts inherits only add CSS classes.
"""

from lxml import etree

from odoo.tests import TransactionCase, tagged

from odoo.addons.tp_kd_workspace.models.workspace import (
    LEAF_BY_MODEL,
    child_context,
    kd_leaf,
)

KD_LISTS = (
    "kd_task_list",
    "opportunity_list",
    "kd_project_list",
    "allocation_list",
    "production_list",
    "acceptance_list",
    "payment_list",
    "plan_list",
    "credential_list",
    "obligation_list",
)
DOSSIER_FORMS = (
    "allocation_form",
    "production_form",
    "acceptance_form",
    "payment_form",
    "plan_form",
    "credential_form",
    "obligation_form",
)
MONEY_FORMS = set(DOSSIER_FORMS) - {"credential_form", "obligation_form"}
CONTRACT_LISTS = {
    "view_contract_list": [
        "code", "name", "project_id", "partner_id", "contract_type",
        "department_id", "lifecycle_state", "tp_latest_review_state",
    ],
    "view_revision_list": ["contract_id", "sequence", "revision_kind", "name", "reference", "review_state"],
}
MONEY_TYPES = {"monetary"}


@tagged("post_install", "-at_install")
class TestKdUiLayout(TransactionCase):
    def _arch(self, xmlid):
        view = self.env.ref(xmlid)
        return view, etree.fromstring(self.env[view.model].get_view(view.id, view.type)["arch"])

    def _columns(self, root):
        # Rendered columns only; a column_invisible copy (e.g. company_id for domains) is not one.
        return [node for node in root if node.tag == "field" and node.get("column_invisible") not in ("True", "1")]

    def test_lists_are_bordered_paged_and_wrap_the_name(self):
        for xmlid in KD_LISTS:
            with self.subTest(view=xmlid):
                _view, root = self._arch(f"tp_kd_workspace.{xmlid}")
                self.assertIn("tp_kd_table", (root.get("class") or "").split())
                self.assertEqual(root.get("limit"), "20")
                name = root.find("field[@name='name']")
                self.assertIsNotNone(name)
                self.assertIn("tp_kd_wrap", (name.get("class") or "").split())
                for column in self._columns(root):
                    width = column.get("width") or ""
                    # Odoo syntax: "[min]" or "[min,max]"; native columns may carry a fixed "20px".
                    if width.startswith("["):
                        parts = [int(part) for part in width.strip("[]").split(",")]
                        self.assertLessEqual(parts[0], parts[-1], column.get("name"))

    def test_lists_never_show_money(self):
        for xmlid in KD_LISTS:
            with self.subTest(view=xmlid):
                view, root = self._arch(f"tp_kd_workspace.{xmlid}")
                model = self.env[view.model]
                for column in root.iter("field"):
                    field = model._fields.get(column.get("name"))
                    if field is None:
                        continue
                    self.assertNotIn(field.type, MONEY_TYPES, f"{xmlid}: {field.name}")
                    self.assertNotEqual(field.name, "amount_ids", xmlid)

    def test_secondary_columns_are_optional(self):
        expected_hidden = {
            "kd_task_list": {"parent_id", "kd_deliverable"},
            "opportunity_list": {"tp_project_id", "kd_source", "kd_scope"},
            "kd_project_list": {"tp_department_id", "company_id", "last_update_status", "stage_id"},
            "allocation_list": {"owner_id", "recipient_department_id", "partner_id", "parent_id"},
            "production_list": {"owner_id", "allocation_id", "reconciliation_state"},
            "acceptance_list": {"owner_id", "production_id", "counterparty_id"},
            "payment_list": {"payment_basis", "reconciliation_state", "acceptance_id", "owner_id"},
            "plan_list": {"owner_id", "date_due"},
            "credential_list": {"project_id", "subject_kind", "owner_id"},
            "obligation_list": {"contract_id", "owner_id"},
        }
        for xmlid, names in expected_hidden.items():
            with self.subTest(view=xmlid):
                _view, root = self._arch(f"tp_kd_workspace.{xmlid}")
                present = {c.get("name") for c in self._columns(root)}
                hidden = {c.get("name") for c in self._columns(root) if c.get("optional") == "hide"}
                # Columns behind a group the test user lacks (multi-company, stages) are not rendered.
                self.assertLessEqual(names & present, hidden)
                self.assertTrue(names & present)
                # The record name and the state stay always visible.
                visible = {c.get("name") for c in self._columns(root) if not c.get("optional")}
                self.assertIn("name", visible)
                if root.find("field[@name='state']") is not None:
                    self.assertIn("state", visible)

    def test_dossier_forms_keep_gates_and_order_pages(self):
        for xmlid in DOSSIER_FORMS:
            with self.subTest(view=xmlid):
                _view, root = self._arch(f"tp_kd_workspace.{xmlid}")
                self.assertIn("tp_kd_form", root.get("class").split())
                self.assertIn("tp_kd_dossier", root.get("class").split())
                titles = [group.get("string") for group in root.iter("group") if group.get("string")]
                self.assertIn("Căn cứ và dự án", titles)
                self.assertIn("Phụ trách và hạn", titles)
                self.assertIsNotNone(root.find(".//group[@name='kd_business']"))
                pages = [page.get("name") for page in root.iter("page")]
                self.assertEqual(pages[0], "kd_scope_page")
                self.assertEqual(pages[-1], "kd_history_page")
                money = root.find(".//page[@name='kd_money_page']")
                if xmlid in MONEY_FORMS:
                    self.assertIsNotNone(money)
                    self.assertEqual(money.get("invisible"), "not can_read_money")
                    self.assertIsNotNone(money.find(".//field[@name='amount_ids']"))
                else:
                    self.assertIsNone(money)
                # Current values stay on the gated page; immutable event values have the same
                # grant gate and a readonly popup, including their relation filter/pager.
                for field in root.iter("field"):
                    if field.get("name") == "amount_ids":
                        if field.getparent() is money:
                            continue
                        self.assertEqual(field.get("invisible"), "not parent.can_read_money")
                        self.assertEqual(field.get("readonly"), "1")
                        self.assertEqual(field.get("widget"), "tp_kd_relation")
                        popup = field.getparent().getparent()
                        self.assertEqual(popup.tag, "form")
                        self.assertEqual(popup.get("edit"), "false")
                        self.assertEqual(popup.get("delete"), "false")
                        self.assertEqual(popup.getparent().get("name"), "event_ids")
                for action in ("action_submit", "action_return", "action_rework"):
                    self.assertIsNotNone(root.find(f"header/button[@name='{action}']"), action)

    def test_transition_dialog_is_styled(self):
        _view, root = self._arch("tp_kd_workspace.transition_form")
        self.assertIn("tp_kd_form", root.get("class").split())

    def test_contract_inherits_only_add_classes(self):
        for xmlid, names in CONTRACT_LISTS.items():
            with self.subTest(view=xmlid):
                _view, root = self._arch(f"tp_contract.{xmlid}")
                self.assertIn("tp_kd_table", root.get("class").split())
                self.assertEqual([c.get("name") for c in self._columns(root)], names)
                self.assertFalse(any(c.get("width") or c.get("optional") for c in self._columns(root)))
                self.assertIsNone(root.get("limit"))
        for xmlid in ("view_contract_form", "view_revision_form", "view_native_draft_form",
                      "view_native_submit_form", "view_native_return_form"):
            with self.subTest(view=xmlid):
                _view, root = self._arch(f"tp_contract.{xmlid}")
                self.assertIn("tp_kd_form", root.get("class").split())
        inherits = self.env["ir.ui.view"].search(
            [("name", "=like", "kd.ui003.%"), ("inherit_id", "!=", False)],
        )
        self.assertTrue(inherits)
        for view in inherits:
            arch = etree.fromstring(view.arch_db)
            for spec in arch if arch.tag == "data" else [arch]:
                self.assertEqual(spec.get("position"), "attributes", view.name)
                self.assertEqual([attr.get("name") for attr in spec], ["class"], view.name)

    def test_leaf_hint_is_presentation_only(self):
        self.assertEqual(kd_leaf("tp.payment.request"), {"tp_kd_leaf": "tp_kd_workspace.menu_payments"})
        self.assertEqual(kd_leaf("res.partner"), {})
        for leaf in set(LEAF_BY_MODEL.values()):
            self.assertTrue(self.env.ref(f"tp_kd_workspace.{leaf}"), leaf)
        env = self.env(context={"tp_kd_leaf": "tp_kd_workspace.menu_tasks", "lang": "vi_VN"})
        self.assertNotIn("tp_kd_leaf", child_context(env))

    def test_project_screens_use_kd_views(self):
        action = self.env.ref("tp_kd_workspace.action_projects")
        self.assertEqual(action.view_id, self.env.ref("tp_kd_workspace.kd_project_list"))
        result = self.env["tp.kd.overview"].create({}).action_projects()
        views = {kind: view_id for view_id, kind in result["views"]}
        self.assertEqual(views["list"], self.env.ref("tp_kd_workspace.kd_project_list").id)
        self.assertEqual(views["form"], self.env.ref("tp_kd_workspace.project_governance_form").id)
        self.assertEqual(result["context"]["tp_kd_leaf"], "tp_kd_workspace.menu_projects")

    def test_business_project_compiled_inheritance_and_search_bindings(self):
        # All seven downstream inherit views must still find button_box after the re-layout.
        _view, project = self._arch("tp_kd_workspace.project_form")
        expected = {"action_kd_" + name for name in (
            "opportunities", "contracts", "tasks", "allocations", "productions",
            "acceptances", "payments", "plans", "credentials", "obligations",
        )}
        expected.update({'action_kd_management', 'action_kd_governance'})
        names = [b.get("name") for b in project.iter("button")]
        self.assertEqual(set(names), expected)
        self.assertEqual(len(names), 12)
        box = project.find(".//div[@name='button_box']")
        self.assertIsNotNone(box)
        self.assertEqual(len(list(box.iter("button"))), 7)
        raw = etree.fromstring(self.env.ref("tp_kd_workspace.project_form").arch_db)
        assignment = raw.find(".//page[@name='kd_assignment_page']")
        self.assertEqual(assignment.get("groups"), "tp_core.group_manager")
        _view, lead = self._arch("tp_kd_workspace.opportunity_form")
        self.assertIsNone(lead.find(".//field[@name='kd_credential_link_ids']"))
        credentials = lead.find(".//field[@name='kd_credential_ids']")
        self.assertIn("no_create", credentials.get("options"))
        self.assertEqual(credentials.get("domain"), "[('project_id','=',tp_project_id)]")
        self.assertEqual(lead.find("header/field[@name='kd_bid_state']").get("widget"), "statusbar")
        self.assertEqual(self.env["crm.lead"]._fields["kd_checklist"].type, "text")
        self.assertEqual(self.env["crm.lead"]._fields["kd_receipt"].type, "char")
        action = self.env.ref("tp_kd_workspace.action_opportunities")
        search = self.env.ref("tp_kd_workspace.opportunity_search")
        self.assertEqual(action.search_view_id, search)
        opened = self.env["tp.kd.overview"].create({}).action_opportunities()
        self.assertEqual(opened["search_view_id"], search.id)
        self.assertIn("tp_kd_project_list", self._arch("tp_kd_workspace.kd_project_list")[1].get("js_class"))
