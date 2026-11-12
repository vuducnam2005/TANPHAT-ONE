import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { FormCompiler } from "@web/views/form/form_compiler";
import { useDialogOpener } from "@tp_web_login/js/identitycheck";

export class HrProfileCompiler extends FormCompiler {
    compile(node, params) {
        const result = super.compile(node, params);
        const icons = {page_overview: "grid_view", work_information: "work", personal_information: "person",
            page_account: "verified_user", tp_history: "history"};
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
        if (result !== false && ["action_open_account_dialog", "action_reset_user_password"].includes(params.name)) {
            this.rememberAccountOpener(params.name);
        }
        return result;
    }
    get className() {
        return {...super.className, o_tp_hr_profile_view: true};
    }
    get modelParams() {
        const params = super.modelParams;
        if (this.props.resId && !this.props.state?.modelState) params.config.mode = "readonly";
        return params;
    }
    async editProfile() {
        await this.model.root.switchMode("edit");
    }
    async saveProfile() {
        if (await this.saveButtonClicked()) await this.model.root.switchMode("readonly");
    }
    async cancelProfile() {
        await this.discard();
        if (!this.model.root.isNew) await this.model.root.switchMode("readonly");
    }
    async backToEmployees() {
        // The native action manager owns unsaved-change confirmation.
        return this.actionService.doAction("tp_hr_workspace.action_employees");
    }
}

registry.category("views").add("tp_hr_profile", {...formView, Controller: HrProfileController, Compiler: HrProfileCompiler});
