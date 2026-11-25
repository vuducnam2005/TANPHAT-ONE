/** @odoo-module **/
import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";

class TpGovernanceBase extends Component {
    static template = "tp_enterprise_governance.Workspace";
    static components = { InlineErrors };
    props = useProps();
    initialTab = "wbs";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = proxy({
            tab: this.initialTab, // 'executive' | 'wbs' | 'dossiers'
            mobileNavOpen: false,
            loading: true,
            busy: false,
            attempt: 0,
            fieldErrors: [],
            serverError: null,

            // Executive Dashboard
            periodFilter: "",
            execData: null,
            showFinEntryModal: false,
            finForm: {
                period_label: new Date().toISOString().slice(0, 7),
                metric_kind: "contract_value",
                amount: "",
                data_state: "confirmed",
                source_ref: "",
                note: "",
            },

            // Project WBS & CPM
            selectedProjectId: 0,
            wbsData: null,
            baselineName: "",
            baselineReason: "",
            adjustTaskId: 0,
            adjustNewDate: "",
            adjustReason: "",

            // Project Dossiers & NAS
            dossierData: null,
            dossierFilters: {
                search: "",
                project_id: "0",
                phase_stage: "",
                state: "",
                page: 1,
                page_size: 20,
            },
            showCreateDossier: false,
            newDossier: {
                project_id: "0",
                phase_stage: "tkkt",
                name: "",
            },
        });

        onWillStart(() => this.reloadCurrentTab());
    }

    goHome() {
        this.action.doAction("tp_web_home.action_home");
    }

    toggleMobileNav() {
        this.state.mobileNavOpen = !this.state.mobileNavOpen;
    }

    async switchTab(target) {
        this.state.mobileNavOpen = false;
        const map = {
            executive: "tp_enterprise_governance.action_executive_dashboard",
            wbs: "tp_enterprise_governance.action_project_wbs_cpm",
            dossiers: "tp_enterprise_governance.action_project_dossier_nas",
        };
        await this.action.doAction(map[target] || map.wbs, { clearBreadcrumbs: true });
    }

    openUrl(url) {
        if (url) {
            browser.location.assign(url);
        }
    }

    async reloadCurrentTab() {
        this.state.loading = true;
        this.state.serverError = null;
        try {
            if (this.state.tab === "executive") {
                this.state.execData = await this.orm.call(
                    "tp.financial.summary.entry",
                    "tp_get_executive_dashboard_data",
                    [this.state.periodFilter]
                );
            } else if (this.state.tab === "wbs") {
                this.state.wbsData = await this.orm.call(
                    "project.project",
                    "tp_wbs_workspace_data",
                    [this.state.selectedProjectId]
                );
                if (this.state.wbsData?.selected_project) {
                    this.state.selectedProjectId = this.state.wbsData.selected_project.id;
                }
            } else {
                this.state.dossierData = await this.orm.call(
                    "tp.project.dossier",
                    "tp_dossier_list_data",
                    [this.state.dossierFilters]
                );
            }
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tải dữ liệu điều hành", write: false });
        } finally {
            this.state.loading = false;
        }
    }

    // --------------------------------------------------------- Executive Actions
    onPeriodInput(ev) {
        this.state.periodFilter = ev.target.value;
    }

    toggleFinForm() {
        this.state.showFinEntryModal = !this.state.showFinEntryModal;
        this.state.fieldErrors = [];
    }

    async saveFinEntry() {
        if (this.state.busy) return;
        this.state.busy = true;
        this.state.attempt += 1;
        this.state.fieldErrors = [];
        this.state.serverError = null;
        try {
            const res = await this.orm.call("tp.financial.summary.entry", "tp_record_financial_entry", [
                this.state.finForm,
            ]);
            if (!res?.ok) {
                this.state.fieldErrors = res?.field_errors || [];
                return;
            }
            this.state.showFinEntryModal = false;
            this.state.finForm.amount = "";
            this.state.finForm.source_ref = "";
            this.notification.add("Đã ghi nhận chỉ tiêu tài chính quản trị kèm nguồn chứng từ.", { type: "success" });
            await this.reloadCurrentTab();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "ghi nhận chỉ tiêu tài chính" });
        } finally {
            this.state.busy = false;
        }
    }

    // --------------------------------------------------------- WBS & CPM Actions
    onSelectWbsProject(ev) {
        this.state.selectedProjectId = Number(ev.target.value) || 0;
        this.reloadCurrentTab();
    }

    async applyTemplate(kind) {
        if (!this.state.selectedProjectId || this.state.busy) return;
        this.state.busy = true;
        try {
            const res = await this.orm.call(
                "project.project",
                "action_apply_engineering_wbs_template",
                [[this.state.selectedProjectId], kind]
            );
            this.notification.add(`Đã khởi tạo ${res?.created_count || 0} giai đoạn WBS gợi ý và tính CPM.`, {
                type: "success",
            });
            await this.reloadCurrentTab();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "áp mẫu WBS" });
        } finally {
            this.state.busy = false;
        }
    }

    async recomputeCpm() {
        if (!this.state.selectedProjectId || this.state.busy) return;
        this.state.busy = true;
        try {
            await this.orm.call("project.project", "action_recompute_cpm", [[this.state.selectedProjectId]]);
            this.notification.add("Đã tính lại đường găng thực tế (ES/EF/LS/LF/Float).", { type: "success" });
            await this.reloadCurrentTab();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tính đường găng CPM" });
        } finally {
            this.state.busy = false;
        }
    }

    async captureBaseline() {
        if (!this.state.selectedProjectId || this.state.busy) return;
        this.state.busy = true;
        try {
            const res = await this.orm.call("project.project", "action_capture_baseline", [
                [this.state.selectedProjectId],
                this.state.baselineName,
                this.state.baselineReason,
            ]);
            this.state.baselineName = "";
            this.state.baselineReason = "";
            this.notification.add(`Đã đóng băng Baseline v${res?.version || 1}.`, { type: "success" });
            await this.reloadCurrentTab();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "chốt Baseline" });
        } finally {
            this.state.busy = false;
        }
    }

    startAdjustMilestone(taskRow) {
        this.state.adjustTaskId = taskRow.id;
        this.state.adjustNewDate = taskRow.planned_end_iso || "";
        this.state.adjustReason = "";
    }

    cancelAdjustMilestone() {
        this.state.adjustTaskId = 0;
    }

    async submitAdjustMilestone() {
        if (!this.state.selectedProjectId || !this.state.adjustTaskId || this.state.busy) return;
        this.state.busy = true;
        try {
            await this.orm.call("project.project", "action_adjust_milestone", [
                [this.state.selectedProjectId],
                this.state.adjustTaskId,
                this.state.adjustNewDate,
                this.state.adjustReason,
            ]);
            this.state.adjustTaskId = 0;
            this.notification.add("Đã lưu điều chỉnh mốc tiến độ vào nhật ký kiểm toán.", { type: "success" });
            await this.reloadCurrentTab();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "điều chỉnh mốc tiến độ" });
        } finally {
            this.state.busy = false;
        }
    }

    // --------------------------------------------------------- Dossiers & NAS Actions
    onDossierFilter(key, ev) {
        this.state.dossierFilters[key] = ev.target.value;
        this.state.dossierFilters.page = 1;
        this.reloadCurrentTab();
    }

    resetDossierFilters() {
        this.state.dossierFilters.search = "";
        this.state.dossierFilters.project_id = "0";
        this.state.dossierFilters.phase_stage = "";
        this.state.dossierFilters.state = "";
        this.state.dossierFilters.page = 1;
        this.reloadCurrentTab();
    }

    toggleCreateDossier() {
        this.state.showCreateDossier = !this.state.showCreateDossier;
    }

    async createDossier() {
        if (this.state.busy) return;
        const projId = Number(this.state.newDossier.project_id || 0);
        const name = (this.state.newDossier.name || "").trim();
        if (!projId || !name) {
            this.state.attempt += 1;
            this.state.fieldErrors = [
                ...(projId ? [] : [{ id: "dos_proj", label: "Dự án", location: "Tạo hồ sơ", message: "Vui lòng chọn Dự án." }]),
                ...(name ? [] : [{ id: "dos_name", label: "Tên bộ hồ sơ", location: "Tạo hồ sơ", message: "Vui lòng nhập Tên bộ hồ sơ." }]),
            ];
            return;
        }
        this.state.busy = true;
        this.state.fieldErrors = [];
        try {
            await this.orm.create("tp.project.dossier", [
                {
                    project_id: projId,
                    phase_stage: this.state.newDossier.phase_stage || "tkkt",
                    name,
                },
            ]);
            this.state.showCreateDossier = false;
            this.state.newDossier.name = "";
            this.notification.add("Đã khởi tạo danh mục hồ sơ giao nộp và đường dẫn chuẩn NAS.", { type: "success" });
            await this.reloadCurrentTab();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "khởi tạo hồ sơ dự án" });
        } finally {
            this.state.busy = false;
        }
    }

    async enqueueNasStructure(projId) {
        const targetProj = Number(projId || this.state.dossierFilters.project_id || 0);
        if (!targetProj || this.state.busy) return;
        this.state.busy = true;
        try {
            const res = await this.orm.call("tp.nas.folder.job", "tp_enqueue_project_nas_structure", [targetProj]);
            this.notification.add(
                res?.created_new_root
                    ? `Đã chuẩn bị cây thư mục gốc ${res.root_folder_path}.`
                    : `Dự án đã có cây thư mục chuẩn ${res.root_folder_path} (không tạo trùng).`,
                { type: "success" }
            );
            await this.reloadCurrentTab();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "khởi tạo cây thư mục NAS" });
        } finally {
            this.state.busy = false;
        }
    }

    async uploadDossierVersion(dossierId, ev) {
        const file = ev.target.files?.[0];
        ev.target.value = "";
        if (!file || this.state.busy) return;
        this.state.busy = true;
        try {
            const fd = new FormData();
            fd.append("file", file);
            fd.append("csrf_token", odoo?.csrf_token || "");
            const resp = await fetch(`/tp/dossier/${dossierId}/upload`, { method: "POST", body: fd });
            const json = await resp.json();
            if (!resp.ok || !json.ok) {
                throw new Error(json.error || "Tải phiên bản thất bại.");
            }
            this.notification.add(`Đã lưu phiên bản v${json.version_no} (SHA-256 đã kiểm chứng).`, { type: "success" });
            await this.reloadCurrentTab();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tải phiên bản hồ sơ" });
        } finally {
            this.state.busy = false;
        }
    }
}

export class TpExecutiveDashboardAction extends TpGovernanceBase {
    initialTab = "executive";
}

export class TpProjectWbsAction extends TpGovernanceBase {
    initialTab = "wbs";
}

export class TpProjectDossiersAction extends TpGovernanceBase {
    initialTab = "dossiers";
}

registry.category("actions").add("tp_enterprise_governance.executive_dashboard", TpExecutiveDashboardAction);
registry.category("actions").add("tp_enterprise_governance.project_wbs", TpProjectWbsAction);
registry.category("actions").add("tp_enterprise_governance.project_dossiers", TpProjectDossiersAction);
