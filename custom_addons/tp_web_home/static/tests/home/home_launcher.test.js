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
const HR = { id: 15, xmlid: "tp_hr_workspace.menu_hr", name: "TP HR", actionID: 913, actionPath: "tp-hr" };
const HR_CORE = { id: 17, xmlid: "hr.menu_hr_root", name: "Employees", actionID: 915, actionPath: "employees" };
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
    test("unified Home shows only authorized departments, HR (if granted), and personal tools", () => {
        const menus = tree(SETTINGS, APPS, UNKNOWN, PROJECT, CONTRACTS, INVOICE, DISCUSS, KD, CALENDAR, TP_ROOT, TODO);
        const catalog = buildCatalog(menus, { isSystem: false });
        expect(keys(catalog.entries)).toEqual([KD.xmlid, TODO.xmlid, CALENDAR.xmlid, DISCUSS.xmlid]);
        expect(catalog.tools).toEqual([]);
        expect(catalog.system).toEqual([]);
        expect(catalog.all).toEqual([]);
        // Projects/Contracts/Work items, Project, Invoicing, unknown, Settings and Apps stay out of Home.
        expect(catalog.otherApps).toBe(8);
        expect(homeSections(catalog).map((s) => [s.key, s.label])).toEqual([
            ["departments", "Phòng ban và đơn vị"],
            ["personal", "Công cụ cá nhân"],
        ]);
        expect(catalog.entries.map((t) => t.name)).toEqual([
            "Kế hoạch Kinh doanh", "Việc cá nhân", "Lịch làm việc", "Trao đổi",
        ]);

        // Core Odoo Employees directory alone never unlocks Quản lý nhân sự on Home.
        const coreOnlyCatalog = buildCatalog(tree(KD, HR_CORE, DISCUSS), { isSystem: false });
        expect(homeSections(coreOnlyCatalog).map((s) => s.key)).toEqual(["departments", "personal"]);
        expect(coreOnlyCatalog.admin.hr).toEqual([]);

        // User with HR permission sees Quản lý nhân sự under Nhân sự và tuyển dụng (without placeholders).
        const hrCatalog = buildCatalog(tree(KD, HR, DISCUSS), { isSystem: false });
        expect(homeSections(hrCatalog).map((s) => s.key)).toEqual(["departments", "hr", "personal"]);
        expect(hrCatalog.admin.hr.map((h) => h.name)).toEqual(["Quản lý nhân sự"]);
    });

    test("system administrators get header tools (Cài đặt, Quản lý ứng dụng, Tất cả ứng dụng) and placeholders", () => {
        const catalog = buildCatalog(tree(APPS, SETTINGS, CRM, DISCUSS, KD, UNKNOWN, HR), { isSystem: true });
        expect(keys(catalog.system)).toEqual([ALL_APPS_KEY, SETTINGS.xmlid, APPS.xmlid]);
        expect(catalog.tools.map((t) => t.label)).toEqual(["Cài đặt", "Quản lý ứng dụng", "Tất cả ứng dụng"]);
        expect(catalog.tools[2].kind).toBe("panel");
        expect(catalog.tools[2].href).toBe(undefined);
        // The panel lists the user's own menus only, in panel order (unknown apps keep server order).
        expect(keys(catalog.all)).toEqual([
            KD.xmlid, HR.xmlid, DISCUSS.xmlid, CRM.xmlid, UNKNOWN.xmlid, SETTINGS.xmlid, APPS.xmlid,
        ]);
        expect(homeSections(catalog).map((s) => s.key)).toEqual(["departments", "hr", "personal"]);
        // Admin tools require the user's own menus: no Settings/Apps without them.
        expect(keys(buildCatalog(tree(DISCUSS), { isSystem: true }).tools)).toEqual([ALL_APPS_KEY]);
    });

    test("main search walks only what Home shows; hidden placeholders and switcher apps never match", () => {
        const menus = tree(SETTINGS, APPS, CRM, PROJECT, DISCUSS, KD, CALENDAR, TODO, TP_ROOT);
        const employee = buildCatalog(menus, { isSystem: false });
        const find = (catalog, query) =>
            homeSections(catalog, query)
                .flatMap((s) => s.tiles)
                .map((t) => t.key || t.xmlid);
        expect(find(employee, "khkd")).toEqual(["business"]);
        expect(find(employee, "kinh doanh")).toEqual(["business"]);
        expect(find(employee, "KẾ HOẠCH")).toEqual(["business"]);
        expect(find(employee, "lich")).toEqual([String(CALENDAR.id)]);
        expect(find(employee, "todo")).toEqual([String(TODO.id)]);
        expect(find(employee, "chat")).toEqual([String(DISCUSS.id)]);
        expect(find(employee, "thiet ke")).toEqual([]);
        expect(find(employee, "tuyen dung")).toEqual([]);
        expect(find(employee, "cai dat")).toEqual([]);
        expect(find(employee, "settings")).toEqual([]);
        expect(find(employee, "tat ca ung dung")).toEqual([]);
        expect(find(employee, "crm")).toEqual([]);

        const admin = buildCatalog(menus, { isSystem: true });
        expect(find(admin, "thiet ke")).toEqual(["design"]);
        expect(find(admin, "tuyen dung")).toEqual(["recruitment"]);
        expect(find(admin, "crm")).toEqual([]);
        expect(keys(filterTiles(admin.all, "tai chinh"))).toEqual([]);
        expect(keys(filterTiles(admin.all, "du an"))).toEqual([
            KD.xmlid, "tp_project.menu_tp_projects", PROJECT.xmlid,
        ]);
    });

    test("users without a workspace keep their tools; empty Home still counts switcher apps", () => {
        expect(keys(buildCatalog(tree(DISCUSS, CRM)).entries)).toEqual([DISCUSS.xmlid]);
        const onlySwitcher = buildCatalog(tree(CRM, INVOICE));
        expect(onlySwitcher.entries).toEqual([]);
        expect(onlySwitcher.otherApps).toBe(2);
        expect(buildCatalog(tree(HOME)).otherApps).toBe(0);
        const empty = buildCatalog(undefined);
        expect(empty.entries).toEqual([]);
        expect(empty.tools).toEqual([]);
        expect(empty.otherApps).toBe(0);
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
        const pending = new Promise((resolve) => {
            release = resolve;
        });
        patchWithCleanup(service, {
            reload: async () => {
                await pending;
                throw new Error("offline");
            },
        });
        await mountWithCleanup(HomeLauncher, PROPS);
        expect(".o_tp_web_home_loading").toHaveCount(1);
        expect(".tp-entry").toHaveCount(0);
        expect(".o_tp_web_home_search_input").toHaveAttribute("disabled");
        release();
        await animationFrame();
        expect(".o_tp_web_home_error").toHaveCount(1);
        expect(".tp-entry").toHaveCount(0);
        expect(".o_tp_web_home_empty_title").toHaveText("Chưa tải được Trang chủ");
        MockServer.current.menus = [DISCUSS];
        patchWithCleanup(service, { reload });
        await contains(".o_tp_web_home_error button").click();
        expect(queryAllTexts(".tp-name")).toEqual(["Trao đổi"]);
        expect(queryAllTexts(".tp-home-section h2")).toEqual(["Công cụ cá nhân"]);
    });

    test("admin and employee share one unified layout, title and KH-KD card styling", async () => {
        asEmployee();
        defineMenus([HOME, SETTINGS, APPS, CRM, KD, DISCUSS, TODO, CALENDAR, TP_ROOT, NO_ACTION]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        expect("#tp-unified-home").toHaveCount(1);
        expect("#tp-unified-home .tp-bg-waves").toHaveCount(1);
        expect("#tp-unified-home h1").toHaveText("Trang chủ");
        expect(".tp-subtitle").toHaveText("Không gian làm việc của TANPHAT ONE");
        expect(".tp-foot").not.toHaveText(/quản trị hệ thống/);
        expect(".tp-admin-tools").toHaveCount(0);
        expect(queryAllTexts(".tp-home-section h2")).toEqual(["Phòng ban và đơn vị", "Công cụ cá nhân"]);
        expect(queryAllTexts(".tp-name")).toEqual([
            "Kế hoạch Kinh doanh",
            "Việc cá nhân",
            "Lịch làm việc",
            "Trao đổi",
        ]);
        expect('[data-module="business"]').toHaveClass("tp-featured");
        expect(queryAll(".tp-entry").map((el) => el.getAttribute("href"))).toEqual([
            "/odoo/action-907",
            "/odoo/to-do",
            "/odoo/calendar",
            "/odoo/discuss",
        ]);
        expect(".o_tp_web_home_note").toHaveCount(1);
        expect("[role=status]").toHaveText("4 lối vào trên Trang chủ");
    });

    test("employee with HR permission sees Nhân sự và tuyển dụng without admin placeholders", async () => {
        asEmployee();
        defineMenus([HOME, KD, HR, DISCUSS]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        expect(queryAllTexts(".tp-home-section h2")).toEqual([
            "Phòng ban và đơn vị",
            "Nhân sự và tuyển dụng",
            "Công cụ cá nhân",
        ]);
        expect(queryAllTexts(".tp-name")).toEqual([
            "Kế hoạch Kinh doanh",
            "Quản lý nhân sự",
            "Trao đổi",
        ]);
        expect('[data-module="hr"] .tp-badge').toHaveText("Đang hoạt động");
        expect('[data-module="design"]').toHaveCount(0);
        expect('[data-module="recruitment"]').toHaveCount(0);
    });

    test("admin clicking active KH-KD or HR selects menu", async () => {
        defineMenus([HOME, KD, HR]);
        patchWithCleanup(user, { isSystem: true });
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        patchWithCleanup(getService("menu"), {
            selectMenu: (menu) => expect.step(`select ${menu.xmlid}`),
        });
        await contains('[data-module="business"]').click();
        await contains('[data-module="hr"]').click();
        expect.verifySteps([`select ${KD.xmlid}`, `select ${HR.xmlid}`]);
    });

    test("non-admin cannot forge #unit deep link hash", async () => {
        asEmployee();
        defineMenus([HOME, KD]);
        browser.location.hash = "#unit=design";
        try {
            await mountWithCleanup(HomeLauncher, PROPS);
            await animationFrame();
            expect("[data-detail-title]").toHaveCount(0);
        } finally {
            browser.location.hash = "";
        }
    });

    test("admin deep link hash #unit=... synchronizes placeholder detail view", async () => {
        defineMenus([HOME, KD, HR]);
        patchWithCleanup(user, { isSystem: true });
        browser.location.hash = "";
        try {
            await mountWithCleanup(HomeLauncher, PROPS);
            await animationFrame();

            browser.location.hash = "#unit=tech";
            window.dispatchEvent(new HashChangeEvent("hashchange"));
            await animationFrame();
            expect("[data-detail-title]").toHaveText("Phòng Kỹ Thuật");
            expect("[data-detail-status]").toHaveText("Đang phát triển");

            browser.location.hash = "#unit=bim";
            window.dispatchEvent(new HashChangeEvent("hashchange"));
            await animationFrame();
            expect("[data-detail-title]").toHaveText("Phòng BIM-QC");

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

    test("for employees, Enter never triggers a hidden administration entry or placeholder", async () => {
        asEmployee();
        defineMenus([SETTINGS, APPS, DISCUSS]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        patchWithCleanup(getService("menu"), { selectMenu: (menu) => expect.step(menu.xmlid) });
        for (const query of ["cai dat", "settings", "thiet ke", "tuyen dung", "tat ca ung dung"]) {
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
        expect(queryAllTexts(".tp-name")).toEqual(["Lịch làm việc"]);
        expect("[role=status]").toHaveText("Tìm thấy 1 lối vào");
        expect(".o_tp_web_home_note").toHaveCount(0);
        await contains(".o_tp_web_home_search_input").edit("khongtimthay", { confirm: false });
        expect(".tp-entry").toHaveCount(0);
        expect(".o_tp_web_home_empty").toHaveAttribute("data-empty", "search");
        await contains(".o_tp_web_home_empty .btn").click();
        expect(".tp-entry").toHaveCount(3);
        expect(".o_tp_web_home_search_input").toHaveValue("");
        await contains(".o_tp_web_home_search_input").edit("chat", { confirm: false });
        await contains(".o_tp_web_home_search_input").press("Escape");
        expect(".o_tp_web_home_search_input").toHaveValue("");
        await contains(".o_tp_web_home_search_input").edit("crm", { confirm: false });
        await contains(".o_tp_web_home_search_clear").click();
        expect(".tp-entry").toHaveCount(3);
        expect(".o_tp_web_home_search_clear").toHaveCount(0);
    });

    test("an empty Home says apps remain in the switcher, unless none is granted", async () => {
        asEmployee();
        defineMenus([HOME, CRM, INVOICE]);
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
        await contains('.tp-entry[data-menu-xmlid="calendar.mail_menu_calendar"]').click();
        expect.verifySteps(["select calendar.mail_menu_calendar"]);

        let nativeDefault = null;
        const observe = (ev) => {
            nativeDefault = !ev.defaultPrevented;
            ev.preventDefault();
        };
        document.addEventListener("click", observe);
        try {
            queryOne('.tp-entry[data-menu-xmlid="mail.menu_root_discuss"]').dispatchEvent(
                new MouseEvent("click", { bubbles: true, cancelable: true, ctrlKey: true })
            );
        } finally {
            document.removeEventListener("click", observe);
        }
        expect(nativeDefault).toBe(true);
        expect.verifySteps([]);
    });

    test("a broken icon image in All Apps panel falls back to a monogram", async () => {
        patchWithCleanup(user, { isSystem: true });
        defineMenus([HOME, { ...UNKNOWN, webIconData: "data:image/png;base64,broken" }]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        await contains('[data-tool="all-apps"]').click();
        await animationFrame();
        queryOne("#tp_home_all_apps .o_tp_web_home_icon_img").dispatchEvent(new Event("error"));
        await animationFrame();
        expect("#tp_home_all_apps .o_tp_web_home_icon_monogram").toHaveText("KV");
    });

    test("menu reload drops a revoked entry", async () => {
        asEmployee();
        defineMenus([DISCUSS, CALENDAR]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        expect(".tp-entry").toHaveCount(2);
        MockServer.current.menus = [DISCUSS];
        await getService("menu").reload();
        await animationFrame();
        expect(queryAllTexts(".tp-name")).toEqual(["Trao đổi"]);
        await contains(".o_tp_web_home_search_input").edit("lich", { confirm: false });
        expect(".tp-entry").toHaveCount(0);
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
        const input = queryOne(".o_tp_web_home_search_input");
        input.value = "trao";
        input.dispatchEvent(new Event("input", { bubbles: true }));
        await animationFrame();
        expect(".tp-entry").toHaveCount(1);
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

describe("unified admin tools and icons", () => {
    test("buildAdminCatalog returns 7 items when isSystem=true", () => {
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
        expect(admin.hr.map((h) => h.name)).toEqual(["Quản lý nhân sự", "Tuyển dụng"]);
        expect(admin.departments[0].badgeKind).toBe("active");
        expect(admin.departments[0].featured).toBe(true);
    });

    test("admin gets tools, panel toggle, placeholder detail navigation, and 7 valid SVG icons", async () => {
        defineMenus([HOME, KD, HR, SETTINGS, APPS, CRM]);
        patchWithCleanup(user, { isSystem: true });
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();

        expect(".tp-admin-tools [data-tool]").toHaveCount(3);
        expect(queryAllTexts(".tp-tool-btn")).toEqual(["Cài đặt", "Quản lý ứng dụng", "Tất cả ứng dụng"]);

        await contains('[data-tool="all-apps"]').click();
        await animationFrame();
        expect("#tp_home_all_apps").toHaveCount(1);
        await contains(".o_tp_web_home_panel_search input").edit("crm", { confirm: false });
        await animationFrame();
        expect(".o_tp_web_home_app .o_tp_web_home_label").toHaveText("CRM");
        await contains(".o_tp_web_home_panel_close").click();
        await animationFrame();
        expect("#tp_home_all_apps").toHaveCount(0);

        patchWithCleanup(getService("menu"), {
            selectMenu: (menu) => expect.step(`select ${menu.xmlid}`),
        });
        await contains('[data-tool="base.menu_administration"]').click();
        expect.verifySteps(["select base.menu_administration"]);

        // Placeholder click
        await contains('[data-module="design"]').click();
        await animationFrame();
        expect("[data-detail-title]").toHaveText("Phòng Thiết kế");
        await contains("[data-back]").click();
        await animationFrame();
        expect("[data-module]").toHaveCount(7);
        expect("[data-module] .tp-icon svg circle[r='10']").toHaveCount(0);
    });
});
