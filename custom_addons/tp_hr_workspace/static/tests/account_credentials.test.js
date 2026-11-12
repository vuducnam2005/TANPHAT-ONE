import { expect, test } from "@odoo/hoot";
import { credentialError } from "@tp_hr_workspace/profile/account_credentials";

test("Account input validation explains empty, mismatch and password policy in Vietnamese", () => {
    expect(credentialError({login:"a b", password:"strong12345", confirmation:"strong12345"}, 8, false)).toInclude("Tên".toLowerCase());
    expect(credentialError({login:"employee", password:"", confirmation:""}, 8, false)).toBe("Vui lòng nhập mật khẩu mới.");
    expect(credentialError({login:"employee", password:"short", confirmation:"short"}, 8, false)).toInclude("8 ký tự");
    expect(credentialError({login:"employee", password:"strong12345", confirmation:"different"}, 8, false)).toInclude("chưa giống nhau");
    expect(credentialError({login:"employee", password:"strong12345", confirmation:"strong12345"}, 8, false)).toBe("");
});

