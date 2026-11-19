import { expect, test } from "@odoo/hoot";
import { credentialError, loginError } from "@tp_hr_workspace/profile/account_credentials";

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

