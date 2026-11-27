/** @odoo-module **/
import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";

const RAIL_PREF_KEY = "tp_enterprise_ops.sidebar_rail";
const MONTH_OPTIONS = [
    { value: "01", label: "Tháng 01" },
    { value: "02", label: "Tháng 02" },
    { value: "03", label: "Tháng 03" },
    { value: "04", label: "Tháng 04" },
    { value: "05", label: "Tháng 05" },
    { value: "06", label: "Tháng 06" },
    { value: "07", label: "Tháng 07" },
    { value: "08", label: "Tháng 08" },
    { value: "09", label: "Tháng 09" },
    { value: "10", label: "Tháng 10" },
    { value: "11", label: "Tháng 11" },
    { value: "12", label: "Tháng 12" },
];

function readRailPref() {
    try {
        return browser.localStorage.getItem(RAIL_PREF_KEY);
    } catch {
        return null;
    }
}

function writeRailPref(mode) {
    try {
        if (mode) {
            browser.localStorage.setItem(RAIL_PREF_KEY, mode);
        } else {
            browser.localStorage.removeItem(RAIL_PREF_KEY);
        }
    } catch {
        // Ignore storage quota / privacy mode errors.
    }
}

function foldSearchText(value) {
    return String(value || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/đ/g, "d")
        .replace(/Đ/g, "D")
        .toLowerCase()
        .trim();
}

class TpEnterpriseOpsBase extends Component {
    static template = "tp_enterprise_ops.Workspace";
    static components = { InlineErrors };
    props = useProps();
    initialTab = "recruitment";
    monthOptions = MONTH_OPTIONS;

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.menu = useService("menu");
        this.notification = useService("notification");

        const now = new Date();
        const curYear = now.getFullYear();
        const curMonth = String(now.getMonth() + 1).padStart(2, "0");
        this.yearOptions = [curYear - 2, curYear - 1, curYear, curYear + 1].map(String);

        const storedRail = readRailPref();
        this.state = proxy({
            tab: this.initialTab, // 'recruitment' | 'survey' | 'payroll' | 'ai'
            mobileNavOpen: false,
            // null = responsive default (rail at 768..1199px, expanded >=1200px), 'rail' = forced rail, 'expanded' = forced expanded
            railMode: storedRail === "rail" || storedRail === "expanded" ? storedRail : null,
            loading: true,
            busy: false,
            attempt: 0,
            fieldErrors: [],
            serverError: null,

            // Recruitment
            recFilters: { search: "", department_id: "0", stage_id: "0" },
            recData: null,
            showAddApplicant: false,
            showRequisitions: true,
            appForm: {
                partner_name: "",
                email_from: "",
                partner_phone: "",
                tp_national_id: "",
                department_id: "0",
                job_id: "0",
            },
            hireModalApp: null,

            // Survey Equipment Calibration (DEC-044 + modal)
            surveyGear: [],
            surveySearch: "",
            surveyStateFilter: "all",
            surveyPage: 1,
            surveyPageSize: 20,
            surveyTotalFiltered: 0,
            surveyTotalPages: 1,
            surveyKpis: { total: 0, valid: 0, expiring_soon: 0, expired: 0, unset: 0 },
            surveyCanManage: false,
            calModalGear: null,
            calForm: {
                tp_calibration_date: "",
                tp_calibration_due_date: "",
                tp_calibration_cert_no: "",
                tp_calibration_org: "",
            },
            calAttempt: 0,
            calFieldErrors: [],
            calServerError: null,

            // Payroll Input Reconciliation (Read-only load + DEC-044 filters + VN period picker)
            payrollYear: String(curYear),
            payrollMonthNum: curMonth,
            payrollMonth: `${curYear}-${curMonth}`,
            payrollSheetExists: false,
            payrollSheetId: 0,
            payrollSheetState: false,
            payrollLines: [],
            payrollDepartments: [],
            payrollPolicyNote: "",
            payrollSearch: "",
            payrollDeptFilter: "all",
            payrollDiffFilter: "all",

            // AI Assistant
            aiQuery: "",
            aiResult: null,
            aiDraftPrompt: "",
            aiDraftPreview: null,
        });

        onWillStart(() => this.reloadTab());
    }

    get sidebarClasses() {
        const classes = ["tp-ops-sidebar"];
        if (this.state.mobileNavOpen) {
            classes.push("is-open");
        }
        if (this.state.railMode === "rail") {
            classes.push("is-rail-forced");
        } else if (this.state.railMode === "expanded") {
            classes.push("is-expanded-forced");
        }
        return classes.join(" ");
    }

    toggleSidebarRail() {
        const vw = browser.innerWidth || 1280;
        const currentlyRail =
            this.state.railMode === "rail" ||
            (this.state.railMode === null && vw >= 768 && vw < 1200);
        const nextMode = currentlyRail ? "expanded" : "rail";
        this.state.railMode = nextMode;
        writeRailPref(nextMode);
    }

    goHome() {
        this.action.doAction("tp_web_home.action_home");
    }

    toggleMobileNav() {
        this.state.mobileNavOpen = !this.state.mobileNavOpen;
    }

    closeMobileNav() {
        this.state.mobileNavOpen = false;
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
                const data = await this.orm.call(
                    "maintenance.equipment",
                    "tp_survey_workspace_data",
                    [
                        {
                            search: this.state.surveySearch,
                            calibration_state: this.state.surveyStateFilter,
                            page: this.state.surveyPage,
                            page_size: this.state.surveyPageSize,
                        },
                    ]
                );
                this.state.surveyGear = data.items || [];
                this.state.surveyTotalFiltered = data.total_filtered || 0;
                this.state.surveyPage = data.page || 1;
                this.state.surveyTotalPages = data.total_pages || 1;
                this.state.surveyKpis = data.kpis || {
                    total: 0,
                    valid: 0,
                    expiring_soon: 0,
                    expired: 0,
                    unset: 0,
                };
                this.state.surveyCanManage = Boolean(data.can_manage);
            } else if (this.state.tab === "payroll") {
                // F-A03-0001: Strictly read-only load! Never create/write/unlink on view or month switch.
                const res = await this.orm.call(
                    "tp.payroll.input.sheet",
                    "tp_get_input_reconciliation",
                    [this.state.payrollMonth]
                );
                this.state.payrollSheetExists = Boolean(res.exists);
                this.state.payrollSheetId = res.sheet_id || 0;
                this.state.payrollSheetState = res.state || false;
                this.state.payrollPolicyNote = res.policy_note || "";
                this.state.payrollDepartments = res.departments || [];
                this.state.payrollLines = res.lines || [];
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
    get hasActiveRecFilters() {
        return Boolean(
            (this.state.recFilters.search || "").trim() ||
                this.state.recFilters.department_id !== "0" ||
                this.state.recFilters.stage_id !== "0"
        );
    }

    applicantsInStage(stageId) {
        return (this.state.recData?.applicants || []).filter((a) => a.stage_id === stageId);
    }

    onRecSearchInput(ev) {
        this.state.recFilters.search = ev.target.value;
    }

    onRecSearchKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.reloadTab();
        }
    }

    onRecFilter(key, ev) {
        this.state.recFilters[key] = ev.target.value;
        this.reloadTab();
    }

    clearRecFilters() {
        this.state.recFilters = { search: "", department_id: "0", stage_id: "0" };
        this.reloadTab();
    }

    toggleAddApplicant() {
        this.state.showAddApplicant = !this.state.showAddApplicant;
        this.state.fieldErrors = [];
        this.state.serverError = null;
    }

    toggleRequisitions() {
        this.state.showRequisitions = !this.state.showRequisitions;
    }

    async createApplicant() {
        const name = (this.state.appForm.partner_name || "").trim();
        if (!name) {
            this.state.attempt += 1;
            this.state.fieldErrors = [
                {
                    id: "app_name",
                    label: "Họ và tên ứng viên",
                    location: "Thêm ứng viên",
                    message: "Vui lòng nhập Họ và tên ứng viên.",
                },
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
            this.state.attempt += 1;
            this.state.serverError = saveError(err, { verb: "tạo ứng viên" });
        } finally {
            this.state.busy = false;
        }
    }

    async moveApplicantStage(appId, ev) {
        const nextStage = Number(ev.target.value || 0);
        if (!nextStage) {
            return;
        }
        try {
            // Changing stage NEVER auto-creates employee!
            await this.orm.call("hr.applicant", "tp_move_applicant_stage", [appId, nextStage]);
            await this.reloadTab();
        } catch (err) {
            this.state.attempt += 1;
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
        if (!app || this.state.busy) {
            return;
        }
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
            this.state.attempt += 1;
            this.state.serverError = saveError(err, { verb: "tiếp nhận nhân sự" });
        } finally {
            this.state.busy = false;
        }
    }

    // --------------------------------------------------------- Survey Equipment (DEC-044 + Calibration Modal)
    get hasActiveSurveyFilters() {
        return Boolean((this.state.surveySearch || "").trim() || this.state.surveyStateFilter !== "all");
    }

    onSurveySearchInput(ev) {
        this.state.surveySearch = ev.target.value;
    }

    onSurveySearchKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.state.surveyPage = 1;
            this.reloadTab();
        }
    }

    onSurveyStateChange(ev) {
        this.state.surveyStateFilter = ev.target.value;
        this.state.surveyPage = 1;
        this.reloadTab();
    }

    setSurveyQuickState(st) {
        this.state.surveyStateFilter = st;
        this.state.surveyPage = 1;
        this.reloadTab();
    }

    clearSurveyFilters() {
        this.state.surveySearch = "";
        this.state.surveyStateFilter = "all";
        this.state.surveyPage = 1;
        this.reloadTab();
    }

    onSurveyPageSizeChange(ev) {
        this.state.surveyPageSize = Number(ev.target.value) || 20;
        this.state.surveyPage = 1;
        this.reloadTab();
    }

    changeSurveyPage(delta) {
        const next = this.state.surveyPage + delta;
        if (next < 1 || next > this.state.surveyTotalPages) {
            return;
        }
        this.state.surveyPage = next;
        this.reloadTab();
    }

    openCalibrationModal(gear) {
        this.state.calModalGear = gear;
        this.state.calForm = {
            tp_calibration_date: gear.tp_calibration_date || "",
            tp_calibration_due_date: gear.tp_calibration_due_date || "",
            tp_calibration_cert_no: gear.tp_calibration_cert_no || "",
            tp_calibration_org: gear.tp_calibration_org || "",
        };
        this.state.calFieldErrors = [];
        this.state.calServerError = null;
    }

    closeCalibrationModal() {
        if (this.state.busy) {
            return;
        }
        this.state.calModalGear = null;
        this.state.calFieldErrors = [];
        this.state.calServerError = null;
    }

    async saveCalibrationModal() {
        const gear = this.state.calModalGear;
        if (!gear || this.state.busy) {
            return;
        }
        const due = (this.state.calForm.tp_calibration_due_date || "").trim();
        const calDate = (this.state.calForm.tp_calibration_date || "").trim();
        const errors = [];
        if (!due) {
            errors.push({
                id: "cal_due_date",
                label: "Hạn kiểm định tiếp theo",
                location: "Cập nhật kiểm định",
                message: "Vui lòng chọn Hạn kiểm định tiếp theo.",
            });
        } else if (calDate && due < calDate) {
            errors.push({
                id: "cal_due_date",
                label: "Hạn kiểm định tiếp theo",
                location: "Cập nhật kiểm định",
                message: "Hạn kiểm định tiếp theo phải lớn hơn hoặc bằng Ngày kiểm định gần nhất.",
            });
        }
        if (errors.length) {
            this.state.calAttempt += 1;
            this.state.calFieldErrors = errors;
            return;
        }

        this.state.busy = true;
        this.state.calFieldErrors = [];
        this.state.calServerError = null;
        try {
            await this.orm.call("maintenance.equipment", "tp_save_survey_calibration", [
                gear.id,
                this.state.calForm,
            ]);
            this.state.calModalGear = null;
            this.notification.add(`Đã cập nhật thông tin kiểm định cho ${gear.tp_code}.`, {
                type: "success",
            });
            await this.reloadTab();
        } catch (err) {
            this.state.calAttempt += 1;
            this.state.calServerError = saveError(err, { verb: "cập nhật hạn kiểm định" });
        } finally {
            this.state.busy = false;
        }
    }

    // --------------------------------------------------------- Payroll Input Reconciliation
    get payrollPeriodLabel() {
        return `Tháng ${this.state.payrollMonthNum}/${this.state.payrollYear}`;
    }

    get hasActivePayrollFilters() {
        return Boolean(
            (this.state.payrollSearch || "").trim() ||
                this.state.payrollDeptFilter !== "all" ||
                this.state.payrollDiffFilter !== "all"
        );
    }

    get filteredPayrollLines() {
        const needle = foldSearchText(this.state.payrollSearch);
        const deptFilter = this.state.payrollDeptFilter;
        const diffFilter = this.state.payrollDiffFilter;
        return (this.state.payrollLines || []).filter((ln) => {
            if (deptFilter !== "all" && String(ln.department_id) !== deptFilter) {
                return false;
            }
            if (diffFilter === "matched" && ln.has_discrepancy) {
                return false;
            }
            if (diffFilter === "discrepancy" && !ln.has_discrepancy) {
                return false;
            }
            if (needle) {
                const hit =
                    foldSearchText(ln.employee_code).includes(needle) ||
                    foldSearchText(ln.employee_name).includes(needle) ||
                    foldSearchText(ln.department_name).includes(needle);
                if (!hit) {
                    return false;
                }
            }
            return true;
        });
    }

    onPayrollMonthPartChange(part, ev) {
        if (part === "month") {
            this.state.payrollMonthNum = ev.target.value;
        } else {
            this.state.payrollYear = ev.target.value;
        }
        this.state.payrollMonth = `${this.state.payrollYear}-${this.state.payrollMonthNum}`;
        this.reloadTab();
    }

    onPayrollSearchInput(ev) {
        this.state.payrollSearch = ev.target.value;
    }

    onPayrollDeptChange(ev) {
        this.state.payrollDeptFilter = ev.target.value;
    }

    onPayrollDiffChange(ev) {
        this.state.payrollDiffFilter = ev.target.value;
    }

    clearPayrollFilters() {
        this.state.payrollSearch = "";
        this.state.payrollDeptFilter = "all";
        this.state.payrollDiffFilter = "all";
    }

    async generatePayrollReconciliation() {
        if (this.state.busy) {
            return;
        }
        this.state.busy = true;
        this.state.serverError = null;
        try {
            await this.orm.call("tp.payroll.input.sheet", "tp_generate_input_reconciliation", [
                this.state.payrollMonth,
            ]);
            this.notification.add(
                `Đã tổng hợp dữ liệu đối soát đầu vào lương ${this.payrollPeriodLabel}.`,
                { type: "success" }
            );
            await this.reloadTab();
        } catch (err) {
            this.state.attempt += 1;
            this.state.serverError = saveError(err, { verb: "tổng hợp đối soát đầu vào lương" });
        } finally {
            this.state.busy = false;
        }
    }

    // --------------------------------------------------------- AI Assistant (InlineErrors + SPA Citation Nav)
    onAiQueryInput(ev) {
        this.state.aiQuery = ev.target.value;
    }

    onAiQueryKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.reloadTab();
        }
    }

    onAiDraftInput(ev) {
        this.state.aiDraftPrompt = ev.target.value;
        if (this.state.fieldErrors.length) {
            this.state.fieldErrors = [];
        }
    }

    onAiDraftKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.previewAiDraft();
        }
    }

    async previewAiDraft() {
        const promptText = (this.state.aiDraftPrompt || "").trim();
        if (!promptText) {
            this.state.attempt += 1;
            this.state.fieldErrors = [
                {
                    id: "ai_draft_prompt",
                    label: "Nội dung dự thảo công việc",
                    location: "Soạn thảo dự thảo công việc",
                    message: "Vui lòng nhập nội dung cần soạn thành đầu việc nháp.",
                },
            ];
            return;
        }
        this.state.busy = true;
        this.state.fieldErrors = [];
        this.state.serverError = null;
        try {
            this.state.aiDraftPreview = await this.orm.call(
                "tp.ai.assistant",
                "tp_preview_draft_from_prompt",
                [promptText, "task"]
            );
        } catch (err) {
            this.state.attempt += 1;
            this.state.serverError = saveError(err, { verb: "tạo bản xem trước dự thảo", write: false });
        } finally {
            this.state.busy = false;
        }
    }

    async confirmAiDraftCreateTask() {
        const prev = this.state.aiDraftPreview?.preview;
        if (!prev || this.state.busy) {
            return;
        }
        this.state.busy = true;
        this.state.serverError = null;
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
            this.notification.add("Đã tạo công việc từ bản xem trước sau khi bạn xác nhận.", {
                type: "success",
            });
        } catch (err) {
            this.state.attempt += 1;
            this.state.serverError = saveError(err, { verb: "tạo công việc nháp" });
        } finally {
            this.state.busy = false;
        }
    }

    async openCitation(cit) {
        if (!cit) {
            return;
        }
        try {
            if (cit.open_mode === "form" && cit.model && cit.res_id) {
                await this.action.doAction({
                    type: "ir.actions.act_window",
                    res_model: cit.model,
                    res_id: cit.res_id,
                    views: [[false, "form"]],
                    target: "current",
                });
                return;
            }
            if (cit.action_xmlid) {
                await this.action.doAction(cit.action_xmlid, {
                    additionalContext: {
                        active_id: cit.res_id || false,
                        highlight_id: cit.res_id || false,
                    },
                });
                return;
            }
            if (cit.url) {
                await this.action.doAction({
                    type: "ir.actions.act_url",
                    url: cit.url,
                    target: "self",
                });
            }
        } catch (err) {
            this.state.attempt += 1;
            this.state.serverError = saveError(err, { verb: "mở nguồn trích dẫn", write: false });
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
