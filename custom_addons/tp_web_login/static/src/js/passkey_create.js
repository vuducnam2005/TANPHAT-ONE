import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { useService } from "@web/core/utils/hooks";
import * as passkeyLib from "@auth_passkey/../lib/simplewebauthn";
import { PasskeyUnsupportedError, describePasskeyError, reportPasskeyFailure } from "./passkey_errors";

/**
 * Same native registration as `auth_passkey_key_create_view_form`
 * (startRegistration on the server options, then native `make_key`), with
 * visible Vietnamese errors and one ceremony at a time.
 */
export class TpPasskeyCreateController extends FormController {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
        this.tpBusy = false;
    }

    async beforeExecuteActionButton(clickParams) {
        if (clickParams.name !== "make_key") {
            return super.beforeExecuteActionButton(...arguments);
        }
        if (this.tpBusy) {
            return false;
        }
        const input = this.rootRef()?.querySelector("div[name='name'] input");
        const name = (input?.value ?? this.model.root.data.name ?? "").trim();
        if (!name) {
            // Native required-field validation explains the missing name.
            return super.beforeExecuteActionButton(...arguments);
        }
        this.tpBusy = true;
        try {
            if (!passkeyLib.browserSupportsWebAuthn()) {
                throw new PasskeyUnsupportedError();
            }
            const registration = await passkeyLib.startRegistration(this.props.context.registration);
            clickParams.args = JSON.stringify([registration]);
        } catch (error) {
            const { kind, message } = describePasskeyError(error, "register");
            reportPasskeyFailure("register", kind, error);
            this.notification.add(message, { type: "danger" });
            return false;
        } finally {
            this.tpBusy = false;
        }
        return super.beforeExecuteActionButton(...arguments);
    }
}

registry.category("views").add("tp_passkey_create", { ...formView, Controller: TpPasskeyCreateController });
