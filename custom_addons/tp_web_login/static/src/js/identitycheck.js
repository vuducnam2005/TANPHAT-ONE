import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { useBus, useService } from "@web/core/utils/hooks";
import * as passkeyLib from "@auth_passkey/../lib/simplewebauthn";
import { PasskeyUnsupportedError, describePasskeyError, reportPasskeyFailure } from "./passkey_errors";

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

/**
 * This view replaces the native passkey js_class on the identity check, so it
 * must also run the native passkey branch: start-auth -> browser assertion ->
 * `password` holds the assertion JSON -> native `run_check` verifies it.
 */
export class IdentityCheckController extends FormController {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
        this.tpPasskeyBusy = false;
    }

    async tpCollectPasskey() {
        if (this.tpPasskeyBusy) {
            return false;
        }
        this.tpPasskeyBusy = true;
        try {
            if (!passkeyLib.browserSupportsWebAuthn()) {
                throw new PasskeyUnsupportedError();
            }
            const serverOptions = await rpc("/auth/passkey/start-auth");
            const auth = await passkeyLib.startAuthentication(serverOptions);
            await this.model.root.update({ password: JSON.stringify(auth) });
            return true;
        } catch (error) {
            const { kind, message } = describePasskeyError(error, "identity");
            reportPasskeyFailure("identity", kind, error);
            this.notification.add(message, { type: "danger", sticky: false });
            return false;
        } finally {
            this.tpPasskeyBusy = false;
        }
    }

    async beforeExecuteActionButton(params) {
        const passkey = params.name === "run_check" && this.model.root.data.auth_method === "webauthn";
        if (passkey && !(await this.tpCollectPasskey())) {
            return false;
        }
        const result = await super.beforeExecuteActionButton(params);
        if (result !== false && params.name === "run_check" && !passkey) {
            // The native error dialog must restore an enabled input, not the disabled submit button.
            this.rootRef()?.querySelector('[name="password"] input')?.focus();
        }
        return result;
    }
}

registry.category("views").add("tp_identity_check", { ...formView, Controller: IdentityCheckController });
