import { describe, expect, test } from "@odoo/hoot";
import {
    assignDialogTestEnv,
    contains,
    defineModels,
    fields,
    mockService,
    models,
    mountView,
    mountWithCleanup,
    onRpc,
} from "@web/../tests/web_test_helpers";
import { AccountCredentials } from "@tp_hr_workspace/profile/account_credentials";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";

class IdentityFocusRow extends models.Model {
    _name = "identity.focus.row";
    password = fields.Char();
    _records = [{ id: 1, password: "" }];
}
defineModels([IdentityFocusRow]);
defineMailModels();

describe("HR-AUTH-FOCUS-009 credential dialog", () => {
    describe.current.tags("desktop");

    async function mountCredentials(reset) {
        assignDialogTestEnv();
        mockService("orm", { call: async () => { throw new Error("Unexpected credential write"); } });
        return mountWithCleanup(AccountCredentials, {
            props: {
                wizardId: 1,
                employeeName: "Synthetic employee",
                employeeCode: "SYNTHETIC",
                department: "Synthetic department",
                login: reset ? "synthetic.employee" : "",
                minLength: 8,
                reset,
                close: () => {},
            },
        });
    }

    test("create focuses employee login inside the native dialog", async () => {
        await mountCredentials(false);
        expect(".o_dialog #tp_account_login").toBeFocused();
        expect("#tp_account_login").toHaveAttribute("autocomplete", "username");
        await contains("#tp_account_login").fill("synthetic.employee");
        await contains("#tp_account_password").fill("Synthetic-only-009");
        expect("#tp_account_login").toHaveValue("synthetic.employee");
        expect("#tp_account_password").toBeFocused();
    });

    test("reset focuses the new password and preserves the readonly employee login", async () => {
        await mountCredentials(true);
        expect(".o_dialog #tp_account_password").toBeFocused();
        expect("#tp_account_login").toHaveAttribute("readonly");
        expect("#tp_account_login").toHaveValue("synthetic.employee");
        expect("#tp_account_password").toHaveAttribute("autocomplete", "new-password");
        expect("#tp_account_confirmation").toHaveAttribute("autocomplete", "new-password");
        await contains("#tp_account_password").fill("Synthetic-only-009");
        await contains("#tp_account_confirmation").fill("Synthetic-only-009");
        expect("#tp_account_confirmation").toBeFocused();
        expect("#tp_account_login").toHaveValue("synthetic.employee");
    });

    test("validation rerender keeps focus in the dialog and preserves password semantics", async () => {
        await mountCredentials(false);
        await contains("#tp_account_login").fill("synthetic.employee");
        await contains("#tp_account_password").fill("Synthetic-only-009");
        await contains("#tp_account_confirmation").fill("Different-synthetic-009");
        await contains(".modal-footer button[type='submit']").click();
        expect(".o_dialog .tp_validation_summary").toHaveText(/Nhập lại mật khẩu[\s\S]*chưa giống nhau/);
        expect("#tp_account_confirmation").toHaveAttribute("aria-invalid", "true");
        expect(".o_tp_hr_credential_field:has(#tp_account_confirmation) .tp_validation_inline").toHaveText(/chưa giống nhau/);
        expect(".modal-footer button[type='submit']").toBeFocused();
        expect("#tp_account_password").toHaveAttribute("type", "password");
        expect("#tp_account_password").toHaveAttribute("autocomplete", "new-password");
        expect("#tp_account_confirmation").toHaveAttribute("autocomplete", "new-password");
    });

    test("native identity submit moves focus from its disabled button before the RPC", async () => {
        onRpc("run_check", () => {
            expect('[name="password"] input').toBeFocused();
            expect.step("identity check called");
            return false;
        });
        await mountView({
            type: "form",
            resModel: "identity.focus.row",
            resId: 1,
            arch: `<form js_class="tp_identity_check">
                <header><button name="run_check" type="object" string="Confirm"/></header>
                <field name="password" widget="password" autocomplete="current-password"/>
            </form>`,
        });
        await contains('[name="password"] input').fill("Synthetic-wrong-password-009");
        await contains('button[name="run_check"]').click();
        expect.verifySteps(["identity check called"]);
        expect('[name="password"] input').toHaveAttribute("autocomplete", "current-password");
    });
});
