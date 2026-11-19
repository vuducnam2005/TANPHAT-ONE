import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { FormCompiler } from "@web/views/form/form_compiler";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
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
        this.rememberAccountOpener = useDialogOpener(this.rootRef);
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
    get isReadonlyProfile() {
        return Boolean(
            this.model.root.data.tp_account_profile_readonly ||
            this.props.resModel === "hr.employee.public"
        );
    }
    get actionMenuItems() {
        const items = super.actionMenuItems;
        return this.isReadonlyProfile ? {...items, action: [], print: []} : items;
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
    async beforeLeave(options = {}) {
        if (!options.forceLeave && !this.skipSaveOnLeave && await this.model.root.isDirty()
            && !await this.confirmChanges("Thay đổi chưa lưu", "Lưu thay đổi trước khi rời trang?", "Lưu và rời trang")) return false;
        return super.beforeLeave(options);
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
    "tp.hr.import.batch": "tp_hr_workspace.action_import",
})) {
    backFallbacks.add(model, xmlid, {force: true});
}
registry.category("views").add("tp_hr_catalog", {...formView, Controller: HrCatalogController});
