import { animationFrame, describe, expect, queryAllTexts, queryOne, test } from "@odoo/hoot";
import {
    clearRegistry,
    contains,
    getService,
    mockService,
    mountWithCleanup,
    patchWithCleanup,
    serverState,
} from "@web/../tests/web_test_helpers";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { UserMenu } from "@web/webclient/user_menu/user_menu";
import { TpUserAccountMenu } from "@tp_web_home/identity/user_account_menu";
import { computeInitials } from "@tp_web_home/identity/identity_service";

const userMenuRegistry = registry.category("user_menuitems");

describe("UI-SHELL-UNIFY-001 identity and logout menu", () => {
    test("UserMenu dropdown presents only Đăng xuất while keeping underlying registry intact", async () => {
        patchWithCleanup(user, { partnerId: 34, name: "Chu Thị Thuỳ Anh", writeDate: "2026-11-14 01:00:00" });
        clearRegistry(userMenuRegistry);
        userMenuRegistry.add("support", () => ({
            type: "item",
            id: "support",
            description: "Hỗ trợ",
            callback: () => {},
            sequence: 10,
        }));
        userMenuRegistry.add("preferences", () => ({
            type: "item",
            id: "preferences",
            description: "Preferences",
            callback: () => {},
            sequence: 20,
        }));
        userMenuRegistry.add("separator", () => ({ type: "separator", sequence: 30 }));
        userMenuRegistry.add("log_out", () => ({
            type: "item",
            id: "logout",
            description: "Log out",
            callback: () => {},
            sequence: 70,
        }));

        await mountWithCleanup(UserMenu);
        expect(".o_user_menu").toHaveAttribute("title", "Chu Thị Thuỳ Anh");
        expect(".o_user_menu").toHaveAttribute("aria-label", "Chu Thị Thuỳ Anh");
        expect(".tp-shell-user-name").toHaveText("Chu Thị Thuỳ Anh");

        await contains("button.o_user_menu").click();
        await animationFrame();
        expect(".tp-shell-user-heading").toHaveCount(0);
        expect(".dropdown-divider").toHaveCount(0);
        expect(".o-dropdown--menu .dropdown-item").toHaveCount(2);
        expect(queryAllTexts(".o-dropdown--menu .dropdown-item")).toEqual([
            "Thông tin cá nhân",
            "Đăng xuất",
        ]);
        // Underlying registry stays untouched for other services/features.
        expect(userMenuRegistry.getEntries()).toHaveLength(4);
    });

    test("TpUserAccountMenu shows logged-in name, collapsed tooltip, monogram fallback, Thông tin cá nhân and Đăng xuất", async () => {
        patchWithCleanup(user, { partnerId: 34, name: "Chu Thị Thuỳ Anh", writeDate: "2026-11-14 01:00:00" });
        await mountWithCleanup(TpUserAccountMenu, { props: { collapsed: false } });

        expect(".tp-sb-user-btn").toHaveAttribute("title", "Chu Thị Thuỳ Anh");
        expect(".tp-sb-user-btn").toHaveAttribute("aria-label", "Chu Thị Thuỳ Anh");
        expect(".tp-sb-user-name").toHaveText("Chu Thị Thuỳ Anh");
        expect(".tp-identity-avatar-img").toHaveCount(1);

        // Broken avatar image falls back cleanly to monogram initials.
        queryOne(".tp-identity-avatar-img").dispatchEvent(new Event("error"));
        await animationFrame();
        expect(".tp-identity-avatar-img").toHaveCount(0);
        expect(".tp-identity-avatar-fallback").toHaveText(computeInitials("Chu Thị Thuỳ Anh"));

        await contains(".tp-sb-user-btn").click();
        await animationFrame();
        expect(".tp-logout-dropdown-menu .dropdown-item").toHaveCount(2);
        expect(queryAllTexts(".tp-logout-dropdown-menu .dropdown-item")).toEqual([
            "Thông tin cá nhân",
            "Đăng xuất",
        ]);
    });

    test("collapsed sidebar hides name label but keeps accessible name and 2-item dropdown", async () => {
        patchWithCleanup(user, { partnerId: null, name: "Nguyễn Văn Rất Dài Tên" });
        await mountWithCleanup(TpUserAccountMenu, { props: { collapsed: true } });

        expect(".tp-sb-user-name").toHaveCount(0);
        expect(".tp-identity-avatar-fallback").toHaveText("NT");
        expect(".tp-sb-user-btn").toHaveAttribute("title", "Nguyễn Văn Rất Dài Tên");
        expect(".tp-sb-user-btn").toHaveAttribute("aria-label", "Nguyễn Văn Rất Dài Tên");

        await contains(".tp-sb-user-btn").click();
        await animationFrame();
        expect(queryAllTexts(".tp-logout-dropdown-menu .dropdown-item")).toEqual([
            "Thông tin cá nhân",
            "Đăng xuất",
        ]);
    });

    test("clicking Thông tin cá nhân invokes registered tp_personal_profile handler", async () => {
        const profileRegistry = registry.category("tp_personal_profile");
        clearRegistry(profileRegistry);
        profileRegistry.add("handler", async () => {
            expect.step("opened_personal_profile");
            return true;
        });
        patchWithCleanup(user, { partnerId: 34, name: "Chu Thị Thuỳ Anh", writeDate: "2026-11-14 01:00:00" });
        await mountWithCleanup(TpUserAccountMenu, { props: { collapsed: false } });

        await contains(".tp-sb-user-btn").click();
        await animationFrame();
        await contains(".tp-profile-menu-item").click();
        await animationFrame();
        expect.verifySteps(["opened_personal_profile"]);
    });

    test("tp.identity/changed updates only when partner_id matches current logged-in user", async () => {
        let handler = null;
        mockService("bus_service", () => ({
            subscribe(type, fn) {
                if (type === "tp.identity/changed") {
                    handler = fn;
                }
                return () => {};
            },
        }));
        patchWithCleanup(user, { partnerId: 34, name: "Chu Thị Thuỳ Anh", writeDate: "2026-11-14 01:00:00" });
        await mountWithCleanup(TpUserAccountMenu, { props: { collapsed: false } });

        const identity = getService("tp_identity");
        expect(identity.name).toBe("Chu Thị Thuỳ Anh");

        // Another partner's update must be ignored (e.g. admin viewing another employee).
        handler({ partner_id: 999, name: "Người khác", write_date: "2026-11-14 02:00:00" });
        await animationFrame();
        expect(".tp-sb-user-name").toHaveText("Chu Thị Thuỳ Anh");

        // Matching partner update refreshes name & image token live without reload.
        handler({ partner_id: 34, name: "Chu Thị Thuỳ Anh (Mới)", write_date: "2026-11-14 03:00:00" });
        await animationFrame();
        expect(".tp-sb-user-name").toHaveText("Chu Thị Thuỳ Anh (Mới)");
        expect(identity.avatarUrl).toInclude("res.partner/34/avatar_128");
        expect(identity.avatarUrl).toInclude("2026-11-14");
    });

    test("logout failure displays danger notification and does not fake redirect", async () => {
        patchWithCleanup(user, { partnerId: 34, name: "Chu Thị Thuỳ Anh" });
        mockService("notification", {
            add(msg, opts) {
                expect.step(`notif:${opts.type}:${msg}`);
            },
        });
        serverState.partnerName = "Chu Thị Thuỳ Anh";
        await mountWithCleanup(TpUserAccountMenu, { props: { collapsed: false } });
        const origFetch = globalThis.fetch.bind(globalThis);
        patchWithCleanup(globalThis, {
            fetch: async (url, opts) => {
                if (String(url).includes("/web/session/logout")) {
                    throw new Error("network error");
                }
                return origFetch(url, opts);
            },
        });

        await contains(".tp-sb-user-btn").click();
        await animationFrame();
        await contains(".tp-logout-menu-item").click();
        await animationFrame();

        expect.verifySteps(["notif:danger:Không thể đăng xuất. Vui lòng thử lại."]);
    });
});
