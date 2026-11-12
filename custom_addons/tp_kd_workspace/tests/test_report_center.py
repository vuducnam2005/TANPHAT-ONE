# ruff: noqa: E501, PLC0415
import io
from datetime import timedelta

import openpyxl

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .test_periodic_plan import TestPeriodicPlan
from .test_production import TestProduction
from odoo.addons.tp_kd_workspace.models.workspace import _INTERNAL


@tagged("post_install", "-at_install")
class TestKdReportCenter(TestPeriodicPlan):
    """KD-REPORT-001 comprehensive backend, reconciliation, security, pagination & Excel export tests."""

    test_allocation_review_rounds_snapshot_and_version = None
    test_allocation_scope_reason_stale_and_no_direct_state = None
    test_allocation_parent_cycle_and_money_isolation = None
    test_submission_amount_export_and_expiry = None
    test_reviewer_self_and_assignment_revoke = None
    test_amount_unknown_zero_and_context_forgery = None
    test_plan_calendar_and_guard = None
    test_plan_comparison_source_and_snapshot = None
    test_project_child_actions_do_not_reuse_parent_form_or_defaults = None
    test_bid_actions_and_direct_route = None
    test_scope_grant_revoke_and_forged_state = None
    test_project_navigation_and_task_policy = None
    test_grants_not_self_manageable = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.outsider = new_test_user(cls.env, login="kd_rc_outsider", groups="tp_core.group_user")
        cls.support_user = new_test_user(
            cls.env,
            login="kd_rc_support",
            groups="tp_kd_workspace.group_scoped_staff,base.group_allow_export",
        )
        values = {"project_id": cls.project.id, "user_id": cls.support_user.id}
        if 'tp_cross_department' in cls.env['tp.project.assignment']._fields:
            values.update(tp_cross_department=True, tp_cross_department_reason='Synthetic explicit report scope')
        cls.env["tp.project.assignment"].create(values)
        cls.preproject_team = cls.env["crm.team"].create({
            "name": "Đội KH-KD Tiền dự án test",
            "company_id": cls.department.company_id.id,
            "kd_department_id": cls.department.id,
            "member_ids": [(6, 0, [cls.editor.id, cls.support_user.id])],
        })
        for domain in ("opportunity", "credential", "obligation", "acceptance", "payment"):
            for user, caps in [(cls.editor, ["prepare", "submit"]), (cls.reviewer, ["review"]), (cls.support_user, ["prepare"])]:
                for cap in caps:
                    exists = cls.env["tp.kd.grant"].search_count([
                        ("project_id", "=", cls.project.id),
                        ("user_id", "=", user.id),
                        ("domain", "=", domain),
                        ("capability", "=", cap),
                        ("active", "=", True),
                    ])
                    if not exists:
                        cls.env["tp.kd.grant"].create({
                            "project_id": cls.project.id,
                            "department_id": cls.department.id,
                            "user_id": user.id,
                            "domain": domain,
                            "capability": cap,
                            "reason": "Synthetic KD-REPORT-001",
                        })
        # Grant financial_read on cls.project to editor and reviewer, NOT to support_user
        cls.editor_fin_grant = cls.env["tp.project.grant"].search([
            ("project_id", "=", cls.project.id),
            ("user_id", "=", cls.editor.id),
            ("capability", "=", "financial_read"),
        ], limit=1)
        if not cls.editor_fin_grant:
            cls.editor_fin_grant = cls.env["tp.project.grant"].create({
                "project_id": cls.project.id,
                "user_id": cls.editor.id,
                "capability": "financial_read",
                "reason": "Synthetic KD-REPORT-001 financial_read",
            })

    def rc(self, user):
        return self.env["tp.kd.report.center"].with_user(user)

    def set_dossier_amount(self, record, amount_state="confirmed", value=0, tax_basis="excluding_tax", measure=None):
        if record._name == "tp.periodic.plan":
            vals = {
                "measure": measure or "production",
                "amount_state": amount_state,
                "value": value,
                "tax_basis": tax_basis,
            }
        else:
            vals = {
                "amount_state": amount_state,
                "value": value,
                "tax_basis": tax_basis,
            }
        existing = record.amount_ids[:1]
        if existing:
            existing.sudo().write(vals)
        else:
            record.sudo().write({
                "amount_ids": [(0, 0, vals)],
                "version": record.version,
            })

    def production(self, **extra):
        return TestProduction.production(self, **extra)

    def test_01_menu_and_action_separation(self):
        menu_ov = self.env.ref("tp_kd_workspace.menu_overview")
        menu_rp = self.env.ref("tp_kd_workspace.menu_reports")
        act_ov = self.env.ref("tp_kd_workspace.action_overview")
        act_rp = self.env.ref("tp_kd_workspace.action_reports")
        view_rp = self.env.ref("tp_kd_workspace.report_center_view")

        self.assertEqual(menu_ov.action, act_ov)
        self.assertEqual(menu_rp.action, act_rp)
        self.assertNotEqual(menu_ov.action.id, menu_rp.action.id)
        self.assertEqual(act_ov.res_model, "tp.kd.overview")
        self.assertEqual(act_rp.res_model, "tp.kd.report.center")
        self.assertEqual(act_rp.view_id, view_rp)
        self.assertIn('js_class="tp_kd_report_center"', view_rp.arch_db)

    def test_02_r01_contract_revision_traps_and_money_security(self):
        # Create a contract with original (1B), effective amendment (1.2B), and draft amendment (9.9B)
        contract = self.env["tp.contract"].create({
            "code": "RC-HD-01",
            "name": "=SUM(1,2) Hợp đồng bẫy revision",
            "project_id": self.project.id,
            "company_id": self.project.company_id.id,
            "partner_id": self.partner.id,
            "contract_type": "owner",
            "lifecycle_state": "not_effective",
        })
        rev0 = self.env["tp.contract.revision"].with_context(tp_contract_workflow=True).create({
            "contract_id": contract.id,
            "sequence": 0,
            "revision_kind": "original",
            "name": "HĐ Gốc",
            "review_state": "draft",
            "signature_status": "unsigned",
            "signature_authority_status": "pending",
            "effectivity_status": "not_effective",
        })
        line0 = self.env["tp.contract.line"].create({
            "revision_id": rev0.id,
            "sequence": 10,
            "scope_key": "L0",
            "name": "Gốc",
            "change_kind": "original",
        })
        self.env["tp.contract.line.amount"].create({
            "line_id": line0.id,
            "amount_state": "confirmed",
            "tax_basis": "excluding_tax",
            "amount": 1_000_000_000,
        })
        rev0.with_context(tp_contract_workflow=True).write({
            "review_state": "review_complete",
            "signature_status": "signed_recorded",
            "signature_authority_status": "confirmed",
            "effectivity_status": "effective_recorded",
            "signed_date": "2026-11-01",
            "effective_date": "2026-11-01",
        })

        rev1 = self.env["tp.contract.revision"].with_context(tp_contract_workflow=True).create({
            "contract_id": contract.id,
            "sequence": 1,
            "revision_kind": "amendment",
            "previous_revision_id": rev0.id,
            "name": "Phụ lục 1 hiệu lực",
            "review_state": "draft",
            "signature_status": "unsigned",
            "signature_authority_status": "pending",
            "effectivity_status": "not_effective",
        })
        line1 = self.env["tp.contract.line"].create({
            "revision_id": rev1.id,
            "sequence": 10,
            "scope_key": "L0",
            "name": "Phụ lục 1",
            "change_kind": "amended",
            "previous_line_id": line0.id,
        })
        self.env["tp.contract.line.amount"].create({
            "line_id": line1.id,
            "amount_state": "confirmed",
            "tax_basis": "excluding_tax",
            "amount": 1_200_000_000,
        })
        rev1.with_context(tp_contract_workflow=True).write({
            "review_state": "review_complete",
            "signature_status": "signed_recorded",
            "signature_authority_status": "confirmed",
            "effectivity_status": "effective_recorded",
            "signed_date": "2026-11-05",
            "effective_date": "2026-11-05",
        })

        rev2_draft = self.env["tp.contract.revision"].with_context(tp_contract_workflow=True).create({
            "contract_id": contract.id,
            "sequence": 2,
            "revision_kind": "amendment",
            "previous_revision_id": rev1.id,
            "name": "Phụ lục 2 nháp",
            "review_state": "draft",
            "signature_status": "unsigned",
            "signature_authority_status": "pending",
            "effectivity_status": "not_effective",
        })
        line2 = self.env["tp.contract.line"].create({
            "revision_id": rev2_draft.id,
            "sequence": 10,
            "scope_key": "L0",
            "name": "Phụ lục 2 nháp",
            "change_kind": "amended",
            "previous_line_id": line1.id,
        })
        self.env["tp.contract.line.amount"].create({
            "line_id": line2.id,
            "amount_state": "confirmed",
            "tax_basis": "excluding_tax",
            "amount": 9_999_999_999,
        })

        # Transition contract lifecycle_state to effective
        contract.with_context(tp_contract_workflow=True).write({"lifecycle_state": "effective"})

        res_editor = self.rc(self.editor).get_kd_report("R01", {"project_id": self.project.id})
        row = next(r for r in res_editor["rows"] if r["res_id"] == contract.id)
        # Original is 1B, Effective is 1.2B (rev1), NOT 1B + 1.2B + 9.9B!
        self.assertEqual(row["original_money"]["amount"], 1_000_000_000.0)
        self.assertEqual(row["effective_money"]["amount"], 1_200_000_000.0)
        self.assertNotEqual(row["effective_money"]["amount"], 9_999_999_999.0)

        # Support user has project assignment but NO financial_read grant
        res_support = self.rc(self.support_user).get_kd_report("R01", {"project_id": self.project.id})
        s_row = next(r for r in res_support["rows"] if r["res_id"] == contract.id)
        self.assertEqual(s_row["original_money"]["state"], "forbidden")
        self.assertEqual(s_row["original_money"]["display"], "Không có quyền xem tiền")
        self.assertIsNone(s_row["original_money"]["amount"])
        self.assertEqual(s_row["effective_money"]["state"], "forbidden")
        self.assertEqual(res_support["totals_row"]["cells"]["effective_money"]["display"], "Không có quyền xem tiền")

        if hasattr(self.outsider, '_tp_can_kd_workspace'):
            with self.assertRaises(AccessError):
                self.rc(self.outsider).get_kd_report("R01")
        else:
            res_out = self.rc(self.outsider).get_kd_report("R01")
            self.assertEqual(res_out["pagination"]["total_rows"], 0)

    def test_03_r03_stages_never_summed_together_and_plan_compare(self):
        plan_rec = self.plan()
        self.set_dossier_amount(plan_rec, amount_state="confirmed", value=400_000_000, measure="production")
        self.transition(plan_rec, "submit")

        prod_rec = self.production()
        self.set_dossier_amount(prod_rec, amount_state="confirmed", value=200_000_000)
        self.transition(prod_rec, "submit")

        acc_rec = self.env["tp.acceptance"].with_user(self.editor).create({
            "code": "RC-NT-01",
            "name": "Nghiệm thu đợt 1",
            "project_id": self.project.id,
            "contract_id": self.contract.id,
            "production_id": prod_rec.id,
            "counterparty_id": self.partner.id,
            "period_from": "2026-11-01",
            "period_to": "2026-11-30",
            "date": "2026-11-15",
            "round_code": "Đợt 1",
            "quantity": 2.0,
            "unit": "km",
            "evidence_checklist": "Biên bản nghiệm thu đợt 1",
            "scope": "Nghiệm thu hoàn thành",
            "owner_id": self.editor.id,
            "reviewer_id": self.reviewer.id,
            "date_due": "2026-11-20",
        })
        self.set_dossier_amount(acc_rec, amount_state="confirmed", value=180_000_000)

        pay_in = self.env["tp.payment.request"].with_user(self.editor).create({
            "code": "RC-TT-IN",
            "name": "Đề nghị thu",
            "project_id": self.project.id,
            "contract_id": self.contract.id,
            "acceptance_id": acc_rec.id,
            "partner_id": self.partner.id,
            "direction": "receipt",
            "payment_basis": "acceptance",
            "document_checklist": "Hồ sơ đề nghị thanh toán thu",
            "date": "2026-11-18",
            "date_due": "2026-11-25",
            "scope": "Thu tiền chủ đầu tư",
            "owner_id": self.editor.id,
            "reviewer_id": self.reviewer.id,
        })
        self.set_dossier_amount(pay_in, amount_state="confirmed", value=150_000_000)

        pay_out_unconf = self.env["tp.payment.request"].with_user(self.editor).create({
            "code": "RC-TT-OUT",
            "name": "Đề nghị chi chưa xác nhận",
            "project_id": self.project.id,
            "contract_id": self.contract.id,
            "partner_id": self.partner.id,
            "direction": "disbursement",
            "payment_basis": "advance",
            "advance_basis": "Tạm ứng nhà thầu phụ",
            "document_checklist": "Hồ sơ tạm ứng",
            "date": "2026-11-19",
            "date_due": "2026-11-25",
            "scope": "Chi",
            "owner_id": self.editor.id,
            "reviewer_id": self.reviewer.id,
        })
        self.set_dossier_amount(pay_out_unconf, amount_state="unconfirmed", value=0)

        rep = self.rc(self.editor).get_kd_report("R03", {"project_id": self.project.id})
        t_cells = rep["totals_row"]["cells"]
        self.assertEqual(t_cells["plan_money"]["single_amount"], 400_000_000.0)
        self.assertEqual(t_cells["production_money"]["single_amount"], 200_000_000.0)
        self.assertEqual(t_cells["acceptance_money"]["single_amount"], 180_000_000.0)
        self.assertEqual(t_cells["payment_receipt_money"]["single_amount"], 150_000_000.0)
        # Unconfirmed payment disbursement must NOT be converted to 0 or added to confirmed total
        self.assertEqual(t_cells["payment_disbursement_money"]["state"], "unconfirmed")
        self.assertIsNone(t_cells["payment_disbursement_money"]["single_amount"])

        plan_row = next(r for r in rep["rows"] if r["stage_key"] == "plan" and r["res_id"] == plan_rec.id)
        self.assertIn("50.0%", plan_row["comparison_note"])

    def test_04_r04_parent_child_allocation_never_summed_together(self):
        parent_alloc = self.allocation("RC-GK-P1")
        self.set_dossier_amount(parent_alloc, amount_state="confirmed", value=500_000_000)

        child1 = self.env["tp.allocation"].with_user(self.editor).create({
            "code": "RC-GK-C1",
            "name": "Phân bổ con 1",
            "project_id": self.project.id,
            "contract_id": self.contract.id,
            "parent_id": parent_alloc.id,
            "allocation_kind": "internal",
            "recipient_department_id": self.department.id,
            "scope": "Con 1",
            "owner_id": self.editor.id,
            "reviewer_id": self.reviewer.id,
            "date": "2026-11-06",
            "date_due": "2026-11-15",
        })
        self.set_dossier_amount(child1, amount_state="confirmed", value=300_000_000)

        child2 = self.env["tp.allocation"].with_user(self.editor).create({
            "code": "RC-GK-C2",
            "name": "Phân bổ con 2",
            "project_id": self.project.id,
            "contract_id": self.contract.id,
            "parent_id": parent_alloc.id,
            "allocation_kind": "internal",
            "recipient_department_id": self.department.id,
            "scope": "Con 2",
            "owner_id": self.editor.id,
            "reviewer_id": self.reviewer.id,
            "date": "2026-11-06",
            "date_due": "2026-11-15",
        })
        self.set_dossier_amount(child2, amount_state="confirmed", value=250_000_000)

        rep = self.rc(self.editor).get_kd_report("R04", {"project_id": self.project.id})
        t_cells = rep["totals_row"]["cells"]
        # Level 1 total = 500M, Level 2 total = 550M; NEVER 1,050M!
        self.assertEqual(t_cells["level1_money"]["single_amount"], 500_000_000.0)
        self.assertEqual(t_cells["level2_money"]["single_amount"], 550_000_000.0)
        p_row = next(r for r in rep["rows"] if r["res_id"] == parent_alloc.id)
        self.assertTrue(p_row["overrun_warning"])

    def test_05_r05_and_r06_non_duplication_and_person_credential_scope(self):
        today = fields.Date.context_today(self.env["tp.kd.report.center"])
        # Overdue + in_review allocation
        alloc = self.allocation("RC-WF-01")
        alloc.write({"date_due": today - timedelta(days=2), "version": alloc.version})
        self.transition(alloc, "submit")

        rep5 = self.rc(self.reviewer).get_kd_report("R05", {"project_id": self.project.id})
        matching = [r for r in rep5["rows"] if r["source_key"] == "allocation" and r["res_id"] == alloc.id]
        self.assertEqual(len(matching), 1)
        self.assertTrue(matching[0]["is_overdue"])
        self.assertTrue(matching[0]["is_my_review"])

        # R06: One credential linked to 3 opportunities -> distinct_creds == 1, usage_count == 3
        cred_org = self.env["tp.credential"].with_user(self.editor).create({
            "code": "RC-CC-ORG",
            "name": "@cmd Chứng chỉ tổ chức gắn 3 cơ hội",
            "project_id": self.project.id,
            "subject_id": self.partner.id,
            "subject_kind": "organization",
            "credential_kind": "Hạng I",
            "valid_from": str(today - timedelta(days=30)),
            "valid_to": str(today + timedelta(days=10)),
            "scope": "Cầu đường",
            "source_note": "Nội bộ",
            "date_due": str(today + timedelta(days=5)),
            "owner_id": self.editor.id,
            "reviewer_id": self.reviewer.id,
        })
        cred_person = self.env["tp.credential"].with_user(self.editor).create({
            "code": "RC-CC-PER",
            "name": "Chứng chỉ cá nhân hạn chế quyền",
            "project_id": self.project.id,
            "subject_id": self.partner.id,
            "subject_kind": "person",
            "credential_kind": "Chủ nhiệm khảo sát",
            "valid_from": str(today - timedelta(days=30)),
            "valid_to": str(today - timedelta(days=1)),
            "scope": "Cá nhân",
            "source_note": "Nội bộ",
            "date_due": str(today + timedelta(days=5)),
            "owner_id": self.editor.id,
            "reviewer_id": self.reviewer.id,
        })
        for idx in range(3):
            lead = self.env["crm.lead"].with_user(self.editor).create({
                "name": f"RC Cơ hội gắn chứng chỉ {idx + 1}",
                "type": "opportunity",
                "tp_project_id": self.project.id,
                "company_id": self.project.company_id.id,
                "partner_id": self.partner.id,
                "user_id": self.editor.id,
                "kd_route": "bid",
                "kd_source": "Nguồn",
                "kd_scope": "Phạm vi",
                "kd_checklist": "Checklist",
                "kd_deadline": str(today + timedelta(days=15)),
            })
            lead.sudo().write({"kd_credential_link_ids": [(6, 0, [cred_org.id])]})

        rep6_editor = self.rc(self.editor).get_kd_report("R06", {"project_id": self.project.id, "sub_filter": "credential"})
        # Editor sees both org and person credential (2 distinct credentials, NOT 3+1=4)
        self.assertEqual(rep6_editor["pagination"]["total_rows"], 2)
        org_row = next(r for r in rep6_editor["rows"] if r["res_id"] == cred_org.id)
        self.assertEqual(org_row["usage_count"], 3)
        self.assertEqual(org_row["status_bucket"], "expiring_30d")

        # Support user is neither owner nor reviewer of cred_person -> only sees cred_org
        rep6_support = self.rc(self.support_user).get_kd_report("R06", {"project_id": self.project.id, "sub_filter": "credential"})
        self.assertEqual([r["res_id"] for r in rep6_support["rows"]], [cred_org.id])
        with self.assertRaises(AccessError):
            self.rc(self.support_user).action_kd_report_open("record", {"model": "tp.credential", "res_id": cred_person.id})

    def test_06_r02_pagination_over_100_excel_export_and_formula_injection_protection(self):
        today = fields.Date.context_today(self.env["tp.kd.report.center"])
        lead_vals = [{
            "name": f"=HYPERLINK(\"http://evil\", \"RC-100-{i:03d}\")" if i == 0 else f"+cmd RC-100-{i:03d}",
            "type": "opportunity",
            "tp_project_id": self.project.id,
            "company_id": self.project.company_id.id,
            "partner_id": self.partner.id,
            "user_id": self.editor.id,
            "kd_route": "bid",
            "kd_source": "Đấu thầu",
            "kd_scope": "Khảo sát",
            "kd_checklist": "Đủ",
            "kd_deadline": str(today + timedelta(days=i % 20)),
            "kd_receipt": f"-cmd BN-{i:03d}",
            "expected_revenue": 10_000_000 + i * 100_000,
        } for i in range(105)]
        # Also 1 pre-project opportunity (tp_project_id = False) with preproject team
        lead_vals.append({
            "name": "@cmd Cơ hội tiền dự án chưa gắn mã dự án",
            "type": "opportunity",
            "tp_project_id": False,
            "company_id": self.project.company_id.id,
            "partner_id": self.partner.id,
            "user_id": self.editor.id,
            "team_id": self.preproject_team.id,
            "kd_route": "bid",
            "kd_source": "Sơ bộ",
            "kd_scope": "Tiền dự án",
            "kd_checklist": "Sơ bộ",
            "kd_deadline": str(today + timedelta(days=5)),
        })
        leads = self.env["crm.lead"].with_user(self.editor).create(lead_vals)
        # Transition half to preparation / submitted via _INTERNAL
        for idx, lead in enumerate(leads[:105]):
            state = "submitted" if idx % 2 == 0 else "preparation"
            lead.with_context(_kd_internal=_INTERNAL).write({"kd_bid_state": state})

        # Page 1 with page_size=20 returns 20 rows, but total_rows is >= 106
        page1 = self.rc(self.editor).get_kd_report("R02", {}, page=1, page_size=20)
        self.assertEqual(len(page1["rows"]), 20)
        self.assertGreaterEqual(page1["pagination"]["total_rows"], 106)
        self.assertGreaterEqual(page1["pagination"]["total_pages"], 6)

        # Unassigned project filter returns only pre-project lead
        pre_only = self.rc(self.editor).get_kd_report("R02", {"project_id": "unassigned"})
        self.assertEqual(pre_only["pagination"]["total_rows"], 1)
        self.assertEqual(pre_only["rows"][0]["expected_money"]["state"], "forbidden")

        # Excel export exports ALL filtered rows (> 100), not just the 20 rows on page 1!
        dl = self.rc(self.editor)._build_xlsx_download("R02", {})
        self.assertEqual(dl["row_count"], page1["pagination"]["total_rows"])
        wb = openpyxl.load_workbook(io.BytesIO(dl["content"]))
        ws = wb.active
        all_cell_texts = [
            str(ws.cell(r, c).value or "")
            for r in range(1, ws.max_row + 1)
            for c in range(1, ws.max_column + 1)
        ]
        # Formula injection strings must be prefixed with a single quote '
        self.assertTrue(any(val.startswith("'=HYPERLINK") for val in all_cell_texts))
        self.assertTrue(any(val.startswith("'+cmd") for val in all_cell_texts))
        self.assertTrue(any(val.startswith("'@cmd") for val in all_cell_texts))
        self.assertFalse(any(val.startswith("=HYPERLINK") for val in all_cell_texts))

        # Support user's Excel export must never contain expected_revenue numbers
        dl_support = self.rc(self.support_user)._build_xlsx_download("R02", {"project_id": self.project.id})
        wb_supp = openpyxl.load_workbook(io.BytesIO(dl_support["content"]))
        ws_supp = wb_supp.active
        supp_texts = [
            str(ws_supp.cell(r, c).value or "")
            for r in range(1, ws_supp.max_row + 1)
            for c in range(1, ws_supp.max_column + 1)
        ]
        self.assertIn("Không có quyền xem tiền", supp_texts)

    def test_07_validation_and_mid_session_grant_revocation(self):
        rc_editor = self.rc(self.editor)
        with self.assertRaises(ValidationError):
            rc_editor.get_kd_report("R99")
        with self.assertRaises(ValidationError):
            rc_editor.get_kd_report("R01", {"date_from": "2026-12-10", "date_to": "2026-11-01"})
        with self.assertRaises(ValidationError):
            rc_editor.get_kd_report("R01", page_size=75)
        with self.assertRaises(ValidationError):
            rc_editor.action_kd_report_open("record", {"model": "res.users", "res_id": 1})

        # Mid-session financial_read grant revocation
        alloc = self.allocation("RC-REVOKE-01")
        self.set_dossier_amount(alloc, amount_state="confirmed", value=333_000_000)
        before = rc_editor.get_kd_report("R04", {"project_id": self.project.id})
        row_before = next(r for r in before["rows"] if r["res_id"] == alloc.id)
        self.assertEqual(row_before["level1_money"]["state"], "confirmed")

        self.editor_fin_grant.active = False
        self.env.invalidate_all()
        after = rc_editor.get_kd_report("R04", {"project_id": self.project.id})
        row_after = next(r for r in after["rows"] if r["res_id"] == alloc.id)
        self.assertEqual(row_after["level1_money"]["state"], "forbidden")
        self.assertEqual(row_after["level1_money"]["display"], "Không có quyền xem tiền")
