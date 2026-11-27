/** @odoo-module **/
import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";

class TpEnterpriseOpsBase extends Component {
    static template = "tp_enterprise_ops.Workspace";
    static components = { InlineErrors };
    props = useProps();
    initialTab = "recruitment";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.menu = useService("menu");
        this.notification = useService("notification");

        this.state = proxy({
            tab: this.initialTab, // 'recruitment' | 'survey' | 'payroll' | 'ai'
            mobileNavOpen: false,
            loading: true,
            busy: false,
            attempt: 0,
            fieldErrors: [],
            serverError: null,

            // Recruitment
            recFilters: { search: "", department_id: "0", stage_id: "0" },
            recData: null,
            showAddApplicant: false,
            appForm: {
                partner_name: "",
                email_from: "",
                partner_phone: "",
                tp_national_id: "",
                department_id: "0",
                job_id: "0",
            },
            hireModalApp: null,

            // Survey Equipment Calibration
            surveyGear: [],
            surveySearch: "",

            // Payroll Input Reconciliation
            payrollMonth: new Date().toISOString().slice(0, 7),
            payrollLines: [],
            payrollPolicyNote: "",

            // AI Assistant
            aiQuery: "",
            aiResult: null,
            aiDraftPrompt: "",
            aiDraftPreview: null,
        });

        onWillStart(() => this.reloadTab());
    }

    goHome() {
        this.action.doAction("tp_web_home.action_home");
    }

    toggleMobileNav() {
        this.state.mobileNavOpen = !this.state.mobileNavOpen;
    }

    isGovernanceTab() {
        return this.state.tab === "survey" || this.state.tab === "ai";
    }

    hasMenu(xmlid) {
        return Boolean(this.menu?.getAll?.().some((m) => m.xmlid === xmlid));
    }

    async switchTab(target) {
        this.state.mobileNavOpen = false;
        const map = {
            executive: "tp_enterprise_governance.action_executive_dashboard",
            wbs: "tp_enterprise_governance.action_project_wbs_cpm",
            dossiers: "tp_enterprise_governance.action_project_dossier_nas",
            recruitment: "tp_enterprise_ops.action_recruitment_workspace",
            survey: "tp_enterprise_ops.action_survey_equipment_workspace",
            payroll: "tp_enterprise_ops.action_payroll_reconcile_workspace",
            ai: "tp_enterprise_ops.action_ai_assistant_workspace",
        };
        await this.action.doAction(map[target] || map.recruitment, { clearBreadcrumbs: true });
    }

    async reloadTab() {
        this.state.loading = true;
        this.state.serverError = null;
        try {
            if (this.state.tab === "recruitment") {
                this.state.recData = await this.orm.call(
                    "hr.applicant",
                    "tp_recruitment_workspace_data",
                    [this.state.recFilters]
                );
            } else if (this.state.tab === "survey") {
                const dom = [["tp_is_survey_gear", "=", true]];
                if (this.state.surveySearch.trim()) {
                    dom.push(["name", "ilike", this.state.surveySearch.trim()]);
                }
                this.state.surveyGear = await this.orm.searchRead(
                    "maintenance.equipment",
                    dom,
                    [
                        "tp_code",
                        "name",
                        "tp_technical_state",
                        "tp_custody",
                        "tp_calibration_date",
                        "tp_calibration_due_date",
                        "tp_calibration_cert_no",
                        "tp_calibration_state",
                    ],
                    { limit: 100 }
                );
            } else if (this.state.tab === "payroll") {
                const policies = await this.orm.searchRead(
                    "tp.payroll.policy",
                    [],
                    ["name", "state", "pending_questions_note"],
                    { limit: 1 }
                );
                this.state.payrollPolicyNote = policies[0]?.pending_questions_note || "";
                const res = await this.orm.call("tp.payroll.input.sheet", "tp_generate_input_reconciliation", [
                    this.state.payrollMonth,
                ]);
                this.state.payrollLines = await this.orm.searchRead(
                    "tp.payroll.input.line",
                    [["sheet_id", "=", res.sheet_id]],
                    [
                        "employee_id",
                        "recorded_punch_days",
                        "confirmed_work_units",
                        "approved_leave_days",
                        "approved_trip_days",
                        "net_pay_status",
                    ]
                );
            } else {
                this.state.aiResult = await this.orm.call("tp.ai.assistant", "tp_grounded_query", [
                    this.state.aiQuery,
                ]);
            }
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tải dữ liệu phân hệ", write: false });
        } finally {
            this.state.loading = false;
        }
    }

    // --------------------------------------------------------- Recruitment
    applicantsInStage(stageId) {
        return (this.state.recData?.applicants || []).filter((a) => a.stage_id === stageId);
    }

    onRecFilter(key, ev) {
        this.state.recFilters[key] = ev.target.value;
        this.reloadTab();
    }

    toggleAddApplicant() {
        this.state.showAddApplicant = !this.state.showAddApplicant;
    }

    async createApplicant() {
        const name = (this.state.appForm.partner_name || "").trim();
        if (!name) {
            this.state.attempt += 1;
            this.state.fieldErrors = [
                { id: "app_name", label: "Họ và tên ứng viên", location: "Thêm ứng viên", message: "Vui lòng nhập Họ và tên ứng viên." },
            ];
            return;
        }
        this.state.busy = true;
        this.state.fieldErrors = [];
        try {
            await this.orm.call("hr.applicant", "tp_create_applicant", [this.state.appForm]);
            this.state.showAddApplicant = false;
            this.state.appForm = {
                partner_name: "",
                email_from: "",
                partner_phone: "",
                tp_national_id: "",
                department_id: "0",
                job_id: "0",
            };
            this.notification.add("Đã tạo hồ sơ ứng viên trong bảng tuyển dụng.", { type: "success" });
            await this.reloadTab();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tạo ứng viên" });
        } finally {
            this.state.busy = false;
        }
    }

    async moveApplicantStage(appId, ev) {
        const nextStage = Number(ev.target.value || 0);
        if (!nextStage) return;
        try {
            // Changing stage NEVER auto-creates employee!
            await this.orm.call("hr.applicant", "tp_move_applicant_stage", [appId, nextStage]);
            await this.reloadTab();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "chuyển vòng tuyển dụng" });
        }
    }

    openHireConfirm(app) {
        this.state.hireModalApp = app;
        this.state.serverError = null;
    }

    closeHireConfirm() {
        this.state.hireModalApp = null;
    }

    async confirmHireApplicant() {
        const app = this.state.hireModalApp;
        if (!app || this.state.busy) return;
        this.state.busy = true;
        try {
            const res = await this.orm.call("hr.applicant", "tp_hire_applicant_to_employee", [
                app.id,
                true,
                0,
                0,
            ]);
            this.state.hireModalApp = null;
            this.notification.add(
                `Đã lập Hồ sơ nhân viên ${res.employee_code || "#" + res.employee_id} (không tự tạo tài khoản đăng nhập / quyền admin).`,
                { type: "success" }
            );
            await this.reloadTab();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tiếp nhận nhân sự" });
        } finally {
            this.state.busy = false;
        }
    }

    // --------------------------------------------------------- Survey & Payroll & AI
    onSurveySearchInput(ev) {
        this.state.surveySearch = ev.target.value;
    }

    onPayrollMonthInput(ev) {
        this.state.payrollMonth = ev.target.value;
    }

    onAiQueryInput(ev) {
        this.state.aiQuery = ev.target.value;
    }

    onAiDraftInput(ev) {
        this.state.aiDraftPrompt = ev.target.value;
    }

    async previewAiDraft() {
        if (!this.state.aiDraftPrompt.trim()) return;
        this.state.aiDraftPreview = await this.orm.call("tp.ai.assistant", "tp_preview_draft_from_prompt", [
            this.state.aiDraftPrompt,
            "task",
        ]);
    }

    async confirmAiDraftCreateTask() {
        const prev = this.state.aiDraftPreview?.preview;
        if (!prev || this.state.busy) return;
        this.state.busy = true;
        try {
            await this.orm.create("project.task", [
                {
                    name: prev.title,
                    description: prev.description,
                    tp_source_kind: "self",
                },
            ]);
            this.state.aiDraftPreview = null;
            this.state.aiDraftPrompt = "";
            this.notification.add("Đã tạo công việc từ bản xem trước sau khi bạn xác nhận.", { type: "success" });
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tạo công việc nháp" });
        } finally {
            this.state.busy = false;
        }
    }

    openCitation(url) {
        if (url) {
            browser.location.assign(url);
        }
    }
}

export class TpRecruitmentWorkspace extends TpEnterpriseOpsBase {
    initialTab = "recruitment";
}

export class TpSurveyEquipmentWorkspace extends TpEnterpriseOpsBase {
    initialTab = "survey";
}

export class TpPayrollReconcileWorkspace extends TpEnterpriseOpsBase {
    initialTab = "payroll";
}

export class TpAiAssistantWorkspace extends TpEnterpriseOpsBase {
    initialTab = "ai";
}

registry.category("actions").add("tp_enterprise_ops.recruitment", TpRecruitmentWorkspace);
registry.category("actions").add("tp_enterprise_ops.survey_equipment", TpSurveyEquipmentWorkspace);
registry.category("actions").add("tp_enterprise_ops.payroll_reconcile", TpPayrollReconcileWorkspace);
registry.category("actions").add("tp_enterprise_ops.ai_assistant", TpAiAssistantWorkspace);
