import { expect, test } from "@odoo/hoot";
import { animationFrame } from "@odoo/hoot-dom";
import {
    assignDialogTestEnv,
    contains,
    makeServerError,
    mockService,
    mountWithCleanup,
} from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import {
    AccountCredentials,
    credentialError,
    credentialErrors,
    loginError,
} from "@tp_hr_workspace/profile/account_credentials";

defineMailModels();

test("Account input validation explains empty, mismatch and password policy in Vietnamese", () => {
    expect(credentialError({login:"a b", password:"strong12345", confirmation:"strong12345"}, 8, false)).toInclude("Tên".toLowerCase());
    expect(credentialError({login:"employee", password:"", confirmation:""}, 8, false)).toBe("Vui lòng nhập mật khẩu mới.");
    expect(credentialError({login:"employee", password:"short", confirmation:"short"}, 8, false)).toInclude("8 ký tự");
    expect(credentialError({login:"employee", password:"strong12345", confirmation:"different"}, 8, false)).toInclude("chưa giống nhau");
    expect(credentialError({login:"employee", password:"strong12345", confirmation:"strong12345"}, 8, false)).toBe("");
});

test("Login rename preserves native case and rejects blank, whitespace, controls and same login", () => {
    expect(loginError("  ")).toInclude("Vui lòng");
    expect(loginError("a b")).toInclude("khoảng trắng");
    expect(loginError("a\u200bb")).toInclude("ký tự");
    expect(loginError("a".repeat(255))).toInclude("254");
    expect(loginError("old", "old")).toInclude("phải khác");
    expect(loginError("  Nguyen.VanA  ", "old")).toBe("");
});

test("Account dialog lists every missing credential at once with its own field", () => {
    expect(credentialErrors({ login: "", password: "", confirmation: "" }, 8, false).map((e) => [e.id, e.message])).toEqual([
        ["tp_account_login", "Vui lòng nhập tên đăng nhập."],
        ["tp_account_password", "Vui lòng nhập mật khẩu mới."],
        ["tp_account_confirmation", "Vui lòng nhập lại mật khẩu mới."],
    ]);
    expect(credentialErrors({ login: "x", password: "strong12345", confirmation: "strong1234" }, 8, true).map((e) => e.id))
        .toEqual(["tp_account_confirmation"]);
    expect(credentialErrors({ login: "employee", password: "strong12345", confirmation: "strong12345" }, 8, false)).toEqual([]);
});

test.tags("desktop");
test("Account dialog keeps errors and server rejection inside the open dialog", async () => {
    assignDialogTestEnv();
    let calls = 0;
    mockService("orm", { call: async () => {
        calls++;
        throw makeServerError({ type: "AccessError", description: "Bạn không có quyền cấp tài khoản cho hồ sơ này." });
    } });
    await mountWithCleanup(AccountCredentials, { props: {
        wizardId: 1, employeeName: "Synthetic employee", employeeCode: "SYNTHETIC", department: "Synthetic department",
        login: "", minLength: 8, reset: false, close: () => { throw new Error("dialog must stay open"); },
    } });
    await contains(".o_dialog button[type='submit'], .o_dialog .btn-primary").click();
    await animationFrame();
    expect(calls).toBe(0);
    expect(".o_dialog .tp_validation_summary li").toHaveCount(3);
    expect("#tp_account_login").toHaveAttribute("aria-invalid", "true");
    await contains(".o_dialog .tp_validation_summary button.tp_validation_link:eq(1)").click();
    expect("#tp_account_password").toBeFocused();
    await contains("#tp_account_login").fill("synthetic.employee", { confirm: false });
    await contains("#tp_account_password").fill("Synthetic-only-022", { confirm: false });
    await contains("#tp_account_confirmation").fill("Synthetic-only-022", { confirm: false });
    expect(".o_dialog .tp_validation_summary").toHaveCount(0);
    await contains(".o_dialog button[type='submit'], .o_dialog .btn-primary").click();
    await animationFrame();
    expect(calls).toBe(1);
    expect(".o_dialog .tp_validation_server").toHaveAttribute("data-kind", "access");
    expect(".o_dialog .tp_validation_server").toHaveText(/Bạn không có quyền cấp tài khoản cho hồ sơ này\./);
    expect("#tp_account_login").toHaveValue("synthetic.employee");
});
