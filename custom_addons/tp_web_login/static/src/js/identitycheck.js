import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { useBus, useService } from "@web/core/utils/hooks";

/** Native buttons are disabled before a dialog mounts, so native focus capture can see body. */
export function useDialogOpener(rootRef) {
    const ui = useService("ui");
    let opener;
    useBus(ui.bus, "active-element-changed", () => {
        if (opener?.isConnected && !opener.disabled && ui.activeElement.contains(opener)) {
            opener.focus();
            opener = null;
        }
    });
    return name => { opener = rootRef()?.querySelector(`button[name="${name}"]`); };
}

export class IdentityCheckController extends FormController {
    async beforeExecuteActionButton(params) {
        const result = await super.beforeExecuteActionButton(params);
        if (result !== false && params.name === "run_check") {
            // The native error dialog must restore an enabled input, not the disabled submit button.
            this.rootRef()?.querySelector('[name="password"] input')?.focus();
        }
        return result;
    }
}

registry.category("views").add("tp_identity_check", { ...formView, Controller: IdentityCheckController });
