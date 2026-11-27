import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import * as passkeyLib from "@auth_passkey/../lib/simplewebauthn";
import { saveError } from "@tp_web_home/validation/validation";
import { PasskeyUnsupportedError, describePasskeyError, reportPasskeyFailure } from "./passkey_errors";

/**
 * Same native registration as `auth_passkey_key_create_view_form`
 * (startRegistration on the server options, then native `make_key`), with
 * visible Vietnamese inline errors inside the dialog and one ceremony at a time.
 */
export class TpPasskeyCreateController extends FormController {
    setup() {
        super.setup(...arguments);
        this.tpBusy = false;
    }

    async beforeExecuteActionButton(clickParams) {
        if (clickParams.name !== "make_key") {
            return super.beforeExecuteActionButton(...arguments);
        }
        if (this.tpBusy) {
            return false;
        }
        this.model.root._tpSaveError = null;
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
            const registration = await passkeyLib.startRegistration(
                this.props.context.registration
            );
            clickParams.args = JSON.stringify([registration]);
        } catch (error) {
            const { kind, message } = describePasskeyError(error, "register");
            reportPasskeyFailure("register", kind, error);
            const classified = error?.data?.name
                ? error
                : {
                      data: {
                          name: kind === "network" ? "ConnectionLostError" : "ValidationError",
                          message,
                      },
                  };
            this.model.root._tpSaveError = saveError(classified, {
                verb: "đăng ký khóa truy cập",
                write: false,
            });
            this.model.root._tpAttempts = (this.model.root._tpAttempts || 0) + 1;
            return false;
        } finally {
            this.tpBusy = false;
        }
        return super.beforeExecuteActionButton(...arguments);
    }
}

registry
    .category("views")
    .add("tp_passkey_create", { ...formView, Controller: TpPasskeyCreateController });
