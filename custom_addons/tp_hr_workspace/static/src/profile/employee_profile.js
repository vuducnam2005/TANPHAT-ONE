import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { FormCompiler } from "@web/views/form/form_compiler";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { user } from "@web/core/user";
import { askUnsavedChoice } from "@tp_web_home/back/back_navigation";
import { useDialogOpener } from "@tp_web_login/js/identitycheck";

export class HrProfileCompiler extends FormCompiler {
    compile(node, params) {
        const result = super.compile(node, params);
        const icons = {page_overview: "grid_view", work_information: "work", personal_information: "person",
            page_account: "verified_user", tp_history: "history", tp_contract: "description",
            tp_equipment: "widgets"};
        for (const notebook of result.querySelectorAll("Notebook")) {
            const pages = {};
            for (const slot of notebook.children) {
                const name = slot.getAttribute("name")?.replaceAll('`', '');
                if (icons[name]) pages[slot.getAttribute("t-set-slot")] = icons[name];
            }
            notebook.setAttribute("icons", JSON.stringify(pages));
        }
        const history = result.querySelector(".o_tp_hr_history");
        const chatter = result.querySelector(".o-mail-Form-chatter");
        if (history && chatter) {
            history.append(chatter);
            chatter.setAttribute("t-if", "!__comp__.env.inDialog");
            chatter.removeAttribute("t-attf-class");
            const component = chatter.querySelector("t[t-component]");
            component?.setAttribute("isChatterAside", "false");
            component?.setAttribute("isInFormSheetBg", "true");
        }
        return result;
    }
}

export class HrProfileController extends FormController {
    static template = "tp_hr_workspace.EmployeeProfile";
    setup() {
        super.setup();
        this.disableSaveOnVisibilityChange = true;
        this.rememberAccountOpener = useDialogOpener(this.rootRef);
    }
    async beforeVisibilityChange() {
        // Explicit [Lưu] / [Hủy] workflow: never silently auto-save or create draft records on tab switch.
    }
    async beforeExecuteActionButton(params) {
        const result = await super.beforeExecuteActionButton(params);
        if (result !== false && ["action_open_account_dialog", "action_reset_user_password", "action_open_change_login_dialog"].includes(params.name)) {
            this.rememberAccountOpener(params.name);
        }
        return result;
    }
    get className() {
        return {...super.className, o_tp_hr_profile_view: true};
    }
    get modelParams() {
        const params = super.modelParams;
        if (this.props.resId && !this.props.state?.modelState) params.config.mode = this.props.context?.form_view_initial_mode || "readonly";
        return params;
    }
    /** Protected admin record (another admin's, or one's own): no action/print menu. */
    get isProtectedProfile() {
        return Boolean(
            this.model.root.data.tp_account_profile_readonly ||
            this.props.resModel === "hr.employee.public"
        );
    }
    /** HR-SELF-EDIT-001: the logged-in account's own employee record (real user link, never the name). */
    get isOwnProfile() {
        const value = this.model.root.data.user_id;
        const userId = Array.isArray(value) ? value[0] : value?.id;
        return this.props.resModel === "hr.employee" && Boolean(userId) && userId === user.userId;
    }
    /** Own record stays editable; the view keeps every non-personal field read-only on it. */
    get isReadonlyProfile() {
        return this.isProtectedProfile && !this.isOwnProfile;
    }
    get actionMenuItems() {
        const items = super.actionMenuItems;
        return this.isProtectedProfile ? {...items, action: [], print: []} : items;
    }
    async editProfile() {
        if (this.isReadonlyProfile) return;
        await this.model.root.switchMode("edit");
    }
    async saveProfile() {
        if (await this.saveButtonClicked()) await this.model.root.switchMode("readonly");
    }
    async cancelProfile() {
        if (await this.model.root.isDirty() && !await this.confirmChanges("Bỏ thay đổi chưa lưu?", "Các thay đổi của bạn chưa được lưu.", "Bỏ thay đổi")) return;
        await this.discard();
        if (!this.model.root.isNew) await this.model.root.switchMode("readonly");
    }
    confirmChanges(title, body, confirmLabel) {
        return new Promise(resolve => this.dialogService.add(ConfirmationDialog, {
            title, body, confirmLabel, cancelLabel: "Tiếp tục chỉnh sửa",
            confirm: () => resolve(true), cancel: () => resolve(false), dismiss: () => resolve(false),
        }));
    }
    promptUnsavedLeave() {
        return askUnsavedChoice(this.dialogService, {
            body: "Bản ghi này có thay đổi chưa lưu. Bạn muốn làm gì trước khi rời trang?",
            saveLabel: "Lưu và rời trang",
        });
    }
    hasPendingInputChanges() {
        const root = this.model?.root;
        if (!root) {
            return false;
        }
        if (root.dirty) {
            return true;
        }
        const active = document.activeElement;
        const container = this.rootRef?.el;
        if (
            active &&
            container?.contains(active) &&
            active.matches("input, textarea, select, [contenteditable='true']")
        ) {
            return active.value !== active.defaultValue;
        }
        return false;
    }
    beforeUnload(ev) {
        if (!this.skipSaveOnLeave && this.hasPendingInputChanges()) {
            ev.preventDefault();
            ev.returnValue = "";
        }
    }
    async beforeLeave(options = {}) {
        if (options.forceLeave || this.skipSaveOnLeave || !(await this.model.root.isDirty())) {
            return true;
        }
        const choice = await this.promptUnsavedLeave();
        if (choice === "save") {
            return this.save({
                reload: false,
                onError: (error, opts) => this.onSaveError(error, opts, true),
            });
        }
        if (choice === "discard") {
            await this.discard();
            return true;
        }
        return false;
    }
}

registry.category("views").add("tp_hr_profile", {...formView, Controller: HrProfileController, Compiler: HrProfileCompiler});

export class HrCatalogController extends HrProfileController {
    get className() { return {...super.className, o_tp_hr_catalog_view: true}; }
}

// UI-BACK-001: deep-link fallbacks of the shared "Quay lại" (no previous screen in the action stack).
const backFallbacks = registry.category("tp_back_fallbacks");
for (const [model, xmlid] of Object.entries({
    "hr.employee": "tp_hr_workspace.action_employees",
    "hr.employee.public": "tp_hr_workspace.action_directory",
    "hr.department": "tp_hr_workspace.action_departments",
    "hr.job": "tp_hr_workspace.action_jobs",
    "hr.work.location": "tp_hr_workspace.action_locations",
    "hr.employee.category": "tp_hr_workspace.action_categories",
    "hr.skill.type": "tp_hr_workspace.action_categories",
    "hr.resume.line.type": "tp_hr_workspace.action_categories",
    "tp.hr.import.batch": "tp_hr_workspace.action_import",
    "tp.hr.import.line": "tp_hr_workspace.action_import",
    "tp.hr.employee.audit": "tp_hr_workspace.action_employee_audit",
    "tp.bank": "tp_hr_bank.action_tp_bank",
    "tp.hr.contract.document": "tp_hr_workspace.action_contract_documents",
    "hr.version": "tp_hr_workspace.action_employees",
    "res.partner.bank": "tp_hr_workspace.action_employees",
})) {
    backFallbacks.add(model, xmlid, {force: true});
}
registry.category("views").add("tp_hr_catalog", {...formView, Controller: HrCatalogController});
