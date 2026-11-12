import { animationFrame, describe, expect, queryAll, queryAllTexts, queryOne, test } from "@odoo/hoot";
import {
    contains,
    defineMenus,
    getService,
    makeTestApp,
    MockServer,
    mountWithCleanup,
    patchWithCleanup,
} from "@web/../tests/web_test_helpers";
import { browser } from "@web/core/browser/browser";
import { user } from "@web/core/user";
import { HomeButton } from "@tp_web_home/home/home_button";
import {
    ALL_APPS_KEY,
    ADMIN_MODULES,
    buildAdminCatalog,
    buildCatalog,
    buildTiles,
    filterTiles,
    HOME_MENU_XMLID,
    homeSections,
    normalizeSearch,
} from "@tp_web_home/home/home_catalog";
import { HomeLauncher } from "@tp_web_home/home/home_launcher";

const HOME = { id: 2, xmlid: HOME_MENU_XMLID, name: "Trang chủ", actionID: 900, actionPath: "tp-home" };
const DISCUSS = { id: 3, xmlid: "mail.menu_root_discuss", name: "Discuss", actionID: 901, actionPath: "discuss" };
const CRM = { id: 4, xmlid: "crm.crm_menu_root", name: "CRM", actionID: 902, actionPath: "crm" };
const TP_ROOT = {
    id: 5,
    xmlid: "tp_core.menu_platform",
    name: "TANPHAT",
    actionID: 903,
    children: [
        { id: 51, xmlid: "tp_project.menu_tp_projects", name: "Projects", actionID: 903, actionPath: "tp-projects" },
        {
            id: 52,
            xmlid: "tp_core.menu_config",
            name: "Configuration",
            children: [{ id: 521, xmlid: "tp_core.menu_work_items", name: "Work Items", actionID: 904 }],
        },
    ],
};
const UNKNOWN = { id: 6, xmlid: "x_custom.menu_root", name: "Kho vật tư", actionID: 905 };
const NO_ACTION = { id: 7, xmlid: "x_custom.menu_empty", name: "Không có action" };
const SETTINGS = { id: 8, xmlid: "base.menu_administration", name: "Settings", actionID: 906, actionPath: "settings" };
const KD = { id: 9, xmlid: "tp_kd_workspace.menu_kd", name: "Kế hoạch Kinh doanh", actionID: 907 };
const CONTRACTS = { id: 10, xmlid: "tp_contract.menu_tp_contracts", name: "TP Contracts", actionID: 908 };
const PROJECT = { id: 11, xmlid: "project.menu_main_pm", name: "Project", actionID: 909, actionPath: "project" };
const TODO = { id: 12, xmlid: "project_todo.menu_todo_todos", name: "To-do", actionID: 910, actionPath: "to-do" };
const CALENDAR = { id: 13, xmlid: "calendar.mail_menu_calendar", name: "Calendar", actionID: 911, actionPath: "calendar" };
const APPS = { id: 14, xmlid: "base.menu_management", name: "Apps", actionID: 912, actionPath: "apps" };
const HR = { id: 15, xmlid: "hr.menu_hr_root", name: "Employees", actionID: 913, actionPath: "employees" };
const INVOICE = { id: 16, xmlid: "account.menu_finance", name: "Invoicing", actionID: 914 };

const PROPS = { props: { action: {}, actionId: 900 } };

function node(menu) {
    return { ...menu, childrenTree: (menu.children || []).map(node) };
}

function tree(...menus) {
    return { id: "root", childrenTree: menus.map(node) };
}

const keys = (tiles) => tiles.map((tile) => tile.xmlid || tile.key);

function asEmployee() {
    patchWithCleanup(user, { isSystem: false });
}

describe("catalog", () => {
    test("Home shows the workspace and personal tools only; other apps stay in the switcher", () => {
        const menus = tree(SETTINGS, APPS, UNKNOWN, PROJECT, CONTRACTS, HR, INVOICE, DISCUSS, KD, CALENDAR, TP_ROOT, TODO);
        const catalog = buildCatalog(menus, { isSystem: false });
        expect(keys(catalog.home)).toEqual([KD.xmlid, TODO.xmlid, CALENDAR.xmlid, DISCUSS.xmlid]);
        expect(catalog.system).toEqual([]);
        expect(catalog.all).toEqual([]);
        // Projects/Contracts/Work items, Project, HR, Invoicing, unknown, Settings and Apps.
        expect(catalog.otherApps).toBe(9);
        expect(homeSections(catalog).map((s) => [s.key, s.label])).toEqual([
            ["workspace", "Không gian làm việc"],
            ["personal", "Công cụ cá nhân"],
        ]);
        expect(catalog.home.map((t) => t.label)).toEqual([
            "Kế hoạch Kinh doanh", "Việc cá nhân", "Lịch làm việc", "Trao đổi",
        ]);
    });

    test("system administrators get Tất cả ứng dụng, Cài đặt and Quản lý ứng dụng", () => {
        const catalog = buildCatalog(tree(APPS, SETTINGS, CRM, DISCUSS, KD, UNKNOWN), { isSystem: true });
        expect(keys(catalog.system)).toEqual([ALL_APPS_KEY, SETTINGS.xmlid, APPS.xmlid]);
        expect(catalog.system.map((t) => t.label)).toEqual(["Tất cả ứng dụng", "Cài đặt", "Quản lý ứng dụng"]);
        expect(catalog.system[0].kind).toBe("panel");
        expect(catalog.system[0].href).toBe(undefined);
        // The panel lists the user's own menus only, in panel order (unknown apps keep server order).
        expect(keys(catalog.all)).toEqual([KD.xmlid, DISCUSS.xmlid, CRM.xmlid, UNKNOWN.xmlid, SETTINGS.xmlid, APPS.xmlid]);
        expect(catalog.otherApps).toBe(2);
        expect(homeSections(catalog).map((s) => s.key)).toEqual(["workspace", "personal", "system"]);
        // Admin entries require the user's own menus: no Settings/Apps without them.
        expect(keys(buildCatalog(tree(DISCUSS), { isSystem: true }).system)).toEqual([ALL_APPS_KEY]);
    });

    test("main search walks only what Home shows; hidden admin and switcher apps never match", () => {
        const menus = tree(SETTINGS, APPS, CRM, PROJECT, DISCUSS, KD, CALENDAR, TODO, TP_ROOT);
        const employee = buildCatalog(menus, { isSystem: false });
        const find = (catalog, query) => keys(homeSections(catalog, query).flatMap((s) => s.tiles));
        expect(find(employee, "khkd")).toEqual([KD.xmlid]);
        expect(find(employee, "kinh doanh")).toEqual([KD.xmlid]);
        expect(find(employee, "KẾ HOẠCH")).toEqual([KD.xmlid]);
        expect(find(employee, "lich")).toEqual([CALENDAR.xmlid]);
        expect(find(employee, "todo")).toEqual([TODO.xmlid]);
        expect(find(employee, "chat")).toEqual([DISCUSS.xmlid]);
        expect(find(employee, "cai dat")).toEqual([]);
        expect(find(employee, "settings")).toEqual([]);
        expect(find(employee, "tat ca ung dung")).toEqual([]);
        expect(find(employee, "crm")).toEqual([]);
        expect(find(employee, "hop dong")).toEqual([]);
        const admin = buildCatalog(menus, { isSystem: true });
        expect(find(admin, "cài đặt")).toEqual([SETTINGS.xmlid, APPS.xmlid]);
        expect(find(admin, "thiet lap")).toEqual([SETTINGS.xmlid]);
        // Words match from their start: "du an" is not inside "ứng dụng" or "quản".
        expect(find(admin, "du an")).toEqual([]);
        expect(find(admin, "ung")).toEqual([ALL_APPS_KEY, APPS.xmlid]);
        expect(find(admin, "tat ca")).toEqual([ALL_APPS_KEY]);
        expect(find(admin, "module")).toEqual([APPS.xmlid]);
        expect(find(admin, "crm")).toEqual([]);
        expect(keys(filterTiles(admin.all, "hop dong"))).toEqual([]);
        expect(keys(filterTiles(admin.all, "du an"))).toEqual(["tp_project.menu_tp_projects", PROJECT.xmlid]);
    });

    test("users without a workspace keep their tools; empty Home still counts switcher apps", () => {
        expect(keys(buildCatalog(tree(DISCUSS, CRM)).home)).toEqual([DISCUSS.xmlid]);
        const onlySwitcher = buildCatalog(tree(HR, INVOICE));
        expect(onlySwitcher.home).toEqual([]);
        expect(onlySwitcher.otherApps).toBe(2);
        expect(buildCatalog(tree(HOME)).otherApps).toBe(0);
        expect(buildCatalog(undefined)).toEqual({
            isAdmin: false,
            admin: null,
            home: [],
            system: [],
            all: [],
            otherApps: 0,
        });
    });

    test("menu identity prevents duplicates without merging shared actions or contexts", () => {
        const sibling = { ...UNKNOWN, id: 61, xmlid: "x_custom.other", name: "Another menu" };
        const tiles = buildTiles(tree(UNKNOWN, sibling, UNKNOWN));
        expect(tiles.map((t) => t.menu.id)).toEqual([UNKNOWN.id, sibling.id]);
        expect(tiles.map((t) => t.menu.actionID)).toEqual([905, 905]);
        expect(buildTiles(tree({ ...KD, actionID: false }))).toEqual([]);
        expect(buildTiles(tree(KD), "assets")[0].href).toBe("/odoo/action-907?debug=assets");
    });

    test("normalizes Vietnamese diacritics, đ/Đ, case and spaces", () => {
        expect(normalizeSearch("  ĐỒNG   Hồ Sơ ")).toBe("dong ho so");
        expect(normalizeSearch("Việc cá nhân")).toBe("viec ca nhan");
        expect(normalizeSearch(null)).toBe("");
    });

    test("roots become entries; Home, menus without action and TP duplicates are excluded", () => {
        const tiles = buildTiles(tree(HOME, DISCUSS, CRM, TP_ROOT, UNKNOWN, NO_ACTION, SETTINGS));
        expect(keys(tiles)).toEqual([
            "mail.menu_root_discuss",
            "tp_project.menu_tp_projects",
            "crm.crm_menu_root",
            "tp_core.menu_work_items",
            "x_custom.menu_root",
            "base.menu_administration",
        ]);
        expect(tiles.filter((tile) => tile.menu.actionID === 903)).toHaveLength(1);
        expect(tiles.find((tile) => tile.xmlid === "tp_core.menu_work_items").href).toBe("/odoo/action-904");
        expect(tiles.find((tile) => tile.xmlid === "crm.crm_menu_root").href).toBe("/odoo/crm");
    });

    test("unknown apps keep their native name and get a monogram icon", () => {
        const [tile] = buildTiles(tree(UNKNOWN));
        expect(tile.label).toBe("Kho vật tư");
        expect(tile.hint).toBe("");
        expect(tile.icon).toEqual({ type: "monogram", text: "KV" });
        expect(tile.group).toBe("apps");
    });

    test("icons follow native image data, then font icon, then monogram", () => {
        const [image, font, fallback] = buildTiles(
            tree(
                { ...DISCUSS, webIconData: "data:image/png;base64,AAAA" },
                { ...CRM, webIcon: "fa fa-star,#ffffff,#71639e" },
                { ...UNKNOWN, webIconData: "/web/static/img/default_icon_app.png" }
            )
        );
        expect(image.icon).toEqual({ type: "image", src: "data:image/png;base64,AAAA" });
        expect(font.icon).toEqual({ type: "font", icon: "fa fa-star", color: "#ffffff", background: "#71639e" });
        expect(fallback.icon.type).toBe("monogram");
    });
});

describe("launcher", () => {
    test("loading and failure never render cached entries; retry applies fresh menus", async () => {
        asEmployee();
        defineMenus([KD, SETTINGS]);
        await makeTestApp();
        const service = getService("menu");
        const reload = service.reload.bind(service);
        let release;
        const pending = new Promise((resolve) => { release = resolve; });
        patchWithCleanup(service, { reload: async () => { await pending; throw new Error("offline"); } });
        await mountWithCleanup(HomeLauncher, PROPS);
        expect(".o_tp_web_home_loading").toHaveCount(1);
        expect(".o_tp_web_home_tile").toHaveCount(0);
        expect(".o_tp_web_home_search_input").toHaveAttribute("disabled");
        release();
        await animationFrame();
        expect(".o_tp_web_home_error").toHaveCount(1);
        expect(".o_tp_web_home_tile").toHaveCount(0);
        expect(".o_tp_web_home_empty_title").toHaveText("Chưa tải được Trang chủ");
        MockServer.current.menus = [DISCUSS];
        patchWithCleanup(service, { reload });
        await contains(".o_tp_web_home_error button").click();
        expect(queryAllTexts(".o_tp_web_home_label")).toEqual(["Trao đổi"]);
        expect(queryAllTexts(".o_tp_web_home_group_title")).toEqual(["Công cụ cá nhân"]);
    });

    test("admin clicking active KH-KD selects menu and preserves current workspace", async () => {
        defineMenus([HOME, KD, HR]);
        patchWithCleanup(user, { isSystem: true });
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        patchWithCleanup(getService("menu"), {
            selectMenu: (menu) => expect.step(`select ${menu.xmlid}`),
        });
        await contains('[data-module="business"]').click();
        expect.verifySteps([`select ${KD.xmlid}`]);
    });

    test("admin clicking HR selects native menu when installed and authorized", async () => {
        defineMenus([HOME, KD, HR]);
        patchWithCleanup(user, { isSystem: true });
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        patchWithCleanup(getService("menu"), {
            selectMenu: (menu) => expect.step(`select ${menu.xmlid}`),
        });
        await contains('[data-module="hr"]').click();
        expect.verifySteps([`select ${HR.xmlid}`]);
    });

    test("employees see the workspace and personal tools, no administration, and a switcher note", async () => {
        asEmployee();
        defineMenus([HOME, SETTINGS, APPS, CRM, KD, DISCUSS, TODO, CALENDAR, TP_ROOT, HR, NO_ACTION]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        expect(".o_tp_web_home_brand").toHaveText("TANPHAT ONE");
        expect(".o_tp_web_home_search_input").toHaveAttribute("placeholder", "Tìm không gian hoặc công cụ…");
        expect(queryAllTexts(".o_tp_web_home_group_title")).toEqual(["Không gian làm việc", "Công cụ cá nhân"]);
        expect(queryAllTexts(".o_tp_web_home_label")).toEqual([
            "Kế hoạch Kinh doanh", "Việc cá nhân", "Lịch làm việc", "Trao đổi",
        ]);
        expect(queryAll(".o_tp_web_home_tile").map((el) => el.getAttribute("href"))).toEqual([
            "/odoo/action-907", "/odoo/to-do", "/odoo/calendar", "/odoo/discuss",
        ]);
        expect("[data-group=system]").toHaveCount(0);
        expect(".o_tp_web_home_panel_toggle").toHaveCount(0);
        expect(".o_tp_web_home_app").toHaveCount(0);
        expect(`[data-menu-xmlid="${HOME_MENU_XMLID}"]`).toHaveCount(0);
        expect(".o_tp_web_home_note").toHaveCount(1);
        expect("[role=status]").toHaveText("4 lối vào trên Trang chủ");
    });

    test("admin deep link hash #unit=... synchronizes placeholder and hash navigation", async () => {
        defineMenus([HOME, KD, HR]);
        patchWithCleanup(user, { isSystem: true });
        browser.location.hash = "";
        try {
            await mountWithCleanup(HomeLauncher, PROPS);
            await animationFrame();

            // Hash change to tech
            browser.location.hash = "#unit=tech";
            window.dispatchEvent(new HashChangeEvent("hashchange"));
            await animationFrame();
            expect("[data-detail-title]").toHaveText("Phòng Kỹ Thuật");
            expect("[data-detail-status]").toHaveText("Đang phát triển");

            // Hash change to BIM
            browser.location.hash = "#unit=bim";
            window.dispatchEvent(new HashChangeEvent("hashchange"));
            await animationFrame();
            expect("[data-detail-title]").toHaveText("Phòng BIM-QC");

            // Back to home
            await contains("[data-back]").click();
            await animationFrame();
            expect("[data-detail-title]").toHaveCount(0);
            expect("[data-module]").toHaveCount(7);
        } finally {
            browser.location.hash = "";
        }
    });

    test("Enter follows visible order and ignores IME composition", async () => {
        asEmployee();
        defineMenus([SETTINGS, DISCUSS, KD]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        patchWithCleanup(getService("menu"), { selectMenu: (menu) => expect.step(menu.xmlid) });
        const input = queryOne(".o_tp_web_home_search_input");
        input.dispatchEvent(new CompositionEvent("compositionstart", { bubbles: true }));
        input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true, isComposing: true }));
        expect.verifySteps([]);
        input.dispatchEvent(new CompositionEvent("compositionend", { bubbles: true }));
        await contains(".o_tp_web_home_search_input").press("Enter");
        expect.verifySteps([KD.xmlid]);
    });

    test("for employees, Enter never triggers a hidden administration entry", async () => {
        asEmployee();
        defineMenus([SETTINGS, APPS, DISCUSS]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        patchWithCleanup(getService("menu"), { selectMenu: (menu) => expect.step(menu.xmlid) });
        for (const query of ["cai dat", "settings", "quan ly ung dung", "tat ca ung dung"]) {
            await contains(".o_tp_web_home_search_input").edit(query, { confirm: false });
            await contains(".o_tp_web_home_search_input").press("Enter");
            expect(".o_tp_web_home_empty_title").toHaveText("Không có lối vào phù hợp trên Trang chủ");
        }
        expect(".o_tp_web_home_panel").toHaveCount(0);
        expect.verifySteps([]);
    });

    test("search filters, announces, shows the empty state and clears", async () => {
        asEmployee();
        defineMenus([KD, DISCUSS, CALENDAR]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        await contains(".o_tp_web_home_search_input").edit("lịch", { confirm: false });
        expect(queryAllTexts(".o_tp_web_home_label")).toEqual(["Lịch làm việc"]);
        expect("[role=status]").toHaveText("Tìm thấy 1 lối vào");
        expect(".o_tp_web_home_note").toHaveCount(0);
        await contains(".o_tp_web_home_search_input").edit("khongtimthay", { confirm: false });
        expect(".o_tp_web_home_tile").toHaveCount(0);
        expect(".o_tp_web_home_empty").toHaveAttribute("data-empty", "search");
        await contains(".o_tp_web_home_empty .btn").click();
        expect(".o_tp_web_home_tile").toHaveCount(3);
        expect(".o_tp_web_home_search_input").toHaveValue("");
        await contains(".o_tp_web_home_search_input").edit("chat", { confirm: false });
        await contains(".o_tp_web_home_search_input").press("Escape");
        expect(".o_tp_web_home_search_input").toHaveValue("");
        await contains(".o_tp_web_home_search_input").edit("crm", { confirm: false });
        await contains(".o_tp_web_home_search_clear").click();
        expect(".o_tp_web_home_tile").toHaveCount(3);
        expect(".o_tp_web_home_search_clear").toHaveCount(0);
    });

    test("an empty Home says apps remain in the switcher, unless none is granted", async () => {
        asEmployee();
        defineMenus([HOME, HR, INVOICE]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        expect(".o_tp_web_home_empty").toHaveAttribute("data-empty", "switcher");
        expect(".o_tp_web_home_empty_title").toHaveText("Trang chủ chưa có không gian làm việc cho tài khoản này");
        expect(".o_tp_web_home_empty").not.toHaveText(/chưa được cấp ứng dụng/);
        MockServer.current.menus = [HOME];
        await getService("menu").reload();
        await animationFrame();
        expect(".o_tp_web_home_empty").toHaveAttribute("data-empty", "none");
        expect(".o_tp_web_home_empty_title").toHaveText("Tài khoản này chưa được cấp ứng dụng nào.");
    });

    test("plain click selects the real menu; modified click keeps the native link", async () => {
        asEmployee();
        defineMenus([DISCUSS, CALENDAR]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        patchWithCleanup(getService("menu"), {
            selectMenu: (menu) => expect.step(`select ${menu.xmlid}`),
        });
        await contains(".o_tp_web_home_tile[data-menu-xmlid='calendar.mail_menu_calendar']").click();
        expect.verifySteps(["select calendar.mail_menu_calendar"]);

        let nativeDefault = null;
        const observe = (ev) => {
            nativeDefault = !ev.defaultPrevented;
            ev.preventDefault(); // keep the test page in place
        };
        document.addEventListener("click", observe);
        try {
            queryOne(".o_tp_web_home_tile[data-menu-xmlid='mail.menu_root_discuss']").dispatchEvent(
                new MouseEvent("click", { bubbles: true, cancelable: true, ctrlKey: true })
            );
        } finally {
            document.removeEventListener("click", observe);
        }
        expect(nativeDefault).toBe(true);
        expect.verifySteps([]);
    });

    test("a broken icon image falls back to a monogram", async () => {
        asEmployee();
        defineMenus([
            { ...DISCUSS, webIconData: "data:image/png;base64,broken" },
            { ...UNKNOWN, webIconData: "data:image/png;base64,broken" },
        ]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        queryOne("[data-group=personal] .o_tp_web_home_icon_img").dispatchEvent(new Event("error"));
        await animationFrame();
        expect("[data-group=personal] .o_tp_web_home_icon_monogram").toHaveText("TĐ");
    });

    test("menu reload drops a revoked entry", async () => {
        asEmployee();
        defineMenus([DISCUSS, CALENDAR]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        expect(".o_tp_web_home_tile").toHaveCount(2);
        MockServer.current.menus = [DISCUSS];
        await getService("menu").reload();
        await animationFrame();
        expect(queryAllTexts(".o_tp_web_home_label")).toEqual(["Trao đổi"]);
        await contains(".o_tp_web_home_search_input").edit("lich", { confirm: false });
        expect(".o_tp_web_home_tile").toHaveCount(0);
    });

    test("reload and search add no global listeners", async () => {
        asEmployee();
        defineMenus([DISCUSS, CRM]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        const added = [];
        for (const target of [browser, window, document]) {
            patchWithCleanup(target, { addEventListener: (type) => added.push(type) });
        }
        MockServer.current.menus = [DISCUSS];
        await getService("menu").reload();
        await animationFrame();
        // Native events: HOOT's edit()/click() helpers register listeners of their own.
        const input = queryOne(".o_tp_web_home_search_input");
        input.value = "trao";
        input.dispatchEvent(new Event("input", { bubbles: true }));
        await animationFrame();
        expect(".o_tp_web_home_tile").toHaveCount(1);
        input.value = "";
        input.dispatchEvent(new Event("input", { bubbles: true }));
        await animationFrame();
        expect(added).toEqual([]);
    });
});

describe("home button", () => {
    test("selects the Home menu, with a native href and accessible label", async () => {
        defineMenus([HOME, DISCUSS]);
        await mountWithCleanup(HomeButton);
        expect(".o_tp_web_home_button").toHaveAttribute("href", "/odoo/tp-home");
        expect(".o_tp_web_home_button").toHaveAttribute("aria-label", "Trang chủ");
        patchWithCleanup(getService("menu"), {
            selectMenu: (menu) => expect.step(`select ${menu.xmlid}`),
        });
        await contains(".o_tp_web_home_button").click();
        expect.verifySteps([`select ${HOME_MENU_XMLID}`]);
    });

    test("marks Home as current and hides when Home is not in the user's menus", async () => {
        defineMenus([HOME, DISCUSS]);
        await mountWithCleanup(HomeButton);
        expect(".o_tp_web_home_button").not.toHaveAttribute("aria-current");
        getService("menu").setCurrentMenu(HOME.id);
        await animationFrame();
        expect(".o_tp_web_home_button").toHaveAttribute("aria-current", "page");
        MockServer.current.menus = [DISCUSS];
        await getService("menu").reload();
        await animationFrame();
        expect(".o_tp_web_home_button").toHaveCount(0);
    });
});

describe("UI-HOME-004 admin layout", () => {
    test("buildAdminCatalog returns exactly 7 items: 5 departments and 2 hr", () => {
        const menus = tree(KD, HR);
        const admin = buildAdminCatalog(menus);
        expect(admin.modules).toHaveLength(7);
        expect(admin.departments.map((d) => d.name)).toEqual([
            "Kế hoạch Kinh doanh",
            "Phòng Thiết kế",
            "Phòng Kỹ Thuật",
            "Phòng BIM-QC",
            "TADIC",
        ]);
        expect(admin.hr.map((h) => h.name)).toEqual([
            "Quản lý nhân sự",
            "Tuyển dụng",
        ]);
        expect(admin.departments[0].badgeKind).toBe("active");
        expect(admin.departments[0].featured).toBe(true);
        expect(admin.departments[1].status).toBe("Đang phát triển");
        expect(admin.departments[2].status).toBe("Đang phát triển");
        expect(admin.departments[3].status).toBe("Đang phát triển");
        expect(admin.departments[4].status).toBe("Đang phát triển");
        expect(admin.hr[1].status).toBe("Đang phát triển");
    });

    test("admin launcher renders #tp-admin-home-design with exactly 7 module buttons and placeholder navigation", async () => {
        defineMenus([HOME, KD, HR]);
        patchWithCleanup(user, { isSystem: true });
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();

        expect("#tp-admin-home-design").toHaveCount(1);
        expect("[data-module]").toHaveCount(7);
        expect(queryAllTexts(".tp-name")).toEqual([
            "Kế hoạch Kinh doanh",
            "Phòng Thiết kế",
            "Phòng Kỹ Thuật",
            "Phòng BIM-QC",
            "TADIC",
            "Quản lý nhân sự",
            "Tuyển dụng",
        ]);
        expect(queryAllTexts("[data-home] .tp-badge").filter((t) => t === "Đang phát triển")).toHaveLength(5);

        // Click design placeholder
        await contains('[data-module="design"]').click();
        await animationFrame();
        expect("[data-detail-title]").toHaveText("Phòng Thiết kế");
        expect("[data-detail-status]").toHaveText("Đang phát triển");
        expect("[data-detail-copy]").toHaveText("Không gian này đang được chuẩn bị. Các chức năng sẽ được bổ sung sau.");

        // Back to home
        await contains("[data-back]").click();
        await animationFrame();
        expect("[data-detail-title]").toHaveCount(0);
        expect("[data-module]").toHaveCount(7);
    });

    test("UI-HOME-004 shell correction: single navbar, admin tools with panel toggle, and 7 valid SVG icons", async () => {
        defineMenus([HOME, KD, HR, SETTINGS, APPS, CRM]);
        patchWithCleanup(user, { isSystem: true });
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();

        // 1. Single navbar: no duplicate .tp-nav inside Home
        expect("#tp-admin-home-design .tp-nav").toHaveCount(0);
        expect("#tp-admin-home-design .tp-brand").toHaveCount(0);

        // 2. Admin tools: 3 controls next to heading
        expect(".tp-admin-tools [data-tool]").toHaveCount(3);
        expect(queryAllTexts(".tp-tool-btn")).toEqual(["Cài đặt", "Quản lý ứng dụng", "Tất cả ứng dụng"]);

        // Clicking all-apps opens the panel
        expect("#tp_home_all_apps").toHaveCount(0);
        await contains('[data-tool="all-apps"]').click();
        await animationFrame();
        expect("#tp_home_all_apps").toHaveCount(1);
        expect(".tp-tool-btn.is-active").toHaveCount(1);

        // Search inside panel
        await contains(".o_tp_web_home_panel_search input").edit("crm", { confirm: false });
        await animationFrame();
        expect(".o_tp_web_home_app").toHaveCount(1);
        expect(".o_tp_web_home_app .o_tp_web_home_label").toHaveText("CRM");

        // Close panel
        await contains(".o_tp_web_home_panel_close").click();
        await animationFrame();
        expect("#tp_home_all_apps").toHaveCount(0);

        // Clicking Settings calls selectMenu
        patchWithCleanup(getService("menu"), {
            selectMenu: (menu) => expect.step(`select ${menu.xmlid}`),
        });
        await contains('[data-tool="base.menu_administration"]').click();
        expect.verifySteps(["select base.menu_administration"]);

        // 3. Icons: exactly 0 circle fallbacks across all 7 module cards
        expect("[data-module] .tp-icon svg circle[r='10']").toHaveCount(0);
        expect('[data-module="business"] .tp-icon svg rect[x="2"][y="7"]').toHaveCount(1);
        expect('[data-module="design"] .tp-icon svg path[d*="21.3"]').toHaveCount(1);
        expect('[data-module="technical"] .tp-icon svg path[d*="18a1"]').toHaveCount(1);
        expect('[data-module="bim"] .tp-icon svg path[d*="12.92"]').toHaveCount(1);
        expect('[data-module="tadic"] .tp-icon svg rect[x="4"][y="2"]').toHaveCount(1);
        expect('[data-module="hr"] .tp-icon svg circle[cx="10"]').toHaveCount(1);
        expect('[data-module="recruitment"] .tp-icon svg line[x1="19"]').toHaveCount(1);
    });

    test("non-admin keeps the UI-HOME-003 layout and does not see #tp-admin-home-design or .tp-admin-tools", async () => {
        defineMenus([HOME, KD, TODO, CALENDAR, DISCUSS]);
        patchWithCleanup(user, { isSystem: false });
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();

        expect("#tp-admin-home-design").toHaveCount(0);
        expect(".tp-admin-tools").toHaveCount(0);
        expect(".o_tp_web_home_inner").toHaveCount(1);
        expect(".o_tp_web_home_brand").toHaveText("TANPHAT ONE");
        expect(queryAllTexts(".o_tp_web_home_group_title")).toEqual([
            "Không gian làm việc",
            "Công cụ cá nhân",
        ]);
    });
});
