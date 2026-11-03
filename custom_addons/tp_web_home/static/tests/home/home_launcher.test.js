import { animationFrame, describe, expect, queryAll, queryAllTexts, queryOne, test } from "@odoo/hoot";
import {
    contains,
    defineMenus,
    getService,
    MockServer,
    mountWithCleanup,
    patchWithCleanup,
} from "@web/../tests/web_test_helpers";
import { browser } from "@web/core/browser/browser";
import { HomeButton } from "@tp_web_home/home/home_button";
import {
    buildTiles,
    filterTiles,
    groupTiles,
    HOME_MENU_XMLID,
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
const SETTINGS = { id: 8, xmlid: "base.menu_administration", name: "Settings", actionID: 906 };

function node(menu) {
    return { ...menu, childrenTree: (menu.children || []).map(node) };
}

function tree(...menus) {
    return { id: "root", childrenTree: menus.map(node) };
}

describe("catalog", () => {
    test("normalizes Vietnamese diacritics, đ/Đ, case and spaces", () => {
        expect(normalizeSearch("  ĐỒNG   Hồ Sơ ")).toBe("dong ho so");
        expect(normalizeSearch("Việc cá nhân")).toBe("viec ca nhan");
        expect(normalizeSearch(null)).toBe("");
    });

    test("roots become tiles; Home, menus without action and TP duplicates are excluded", () => {
        const tiles = buildTiles(tree(HOME, DISCUSS, CRM, TP_ROOT, UNKNOWN, NO_ACTION, SETTINGS));
        expect(tiles.map((tile) => tile.xmlid)).toEqual([
            "mail.menu_root_discuss",
            "crm.crm_menu_root",
            "tp_project.menu_tp_projects",
            "tp_core.menu_work_items",
            "x_custom.menu_root",
            "base.menu_administration",
        ]);
        expect(tiles.filter((tile) => tile.menu.actionID === 903)).toHaveLength(1);
        expect(tiles.find((tile) => tile.xmlid === "mail.menu_root_discuss").label).toBe("Trao đổi");
        expect(tiles.find((tile) => tile.xmlid === "tp_project.menu_tp_projects").label).toBe("TP Projects");
        expect(tiles.find((tile) => tile.xmlid === "tp_core.menu_work_items").href).toBe("/odoo/action-904");
        expect(tiles.find((tile) => tile.xmlid === "crm.crm_menu_root").href).toBe("/odoo/crm");
    });

    test("unknown apps keep their native name and get a monogram icon", () => {
        const [tile] = buildTiles(tree(UNKNOWN));
        expect(tile.label).toBe("Kho vật tư");
        expect(tile.hint).toBe("");
        expect(tile.icon).toEqual({ type: "monogram", text: "KV" });
        expect(tile.group).toBe("work");
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

    test("search matches with or without diacritics, English aliases, and only visible tiles", () => {
        const tiles = buildTiles(tree(DISCUSS, CRM, TP_ROOT, UNKNOWN, SETTINGS));
        const keys = (query) => filterTiles(tiles, query).map((tile) => tile.xmlid);
        expect(keys("trao đổi")).toEqual(["mail.menu_root_discuss"]);
        expect(keys("TRAO DOI")).toEqual(["mail.menu_root_discuss"]);
        expect(keys("discuss")).toEqual(["mail.menu_root_discuss"]);
        expect(keys("du an")).toEqual(["tp_project.menu_tp_projects"]);
        expect(keys("kho vat tu")).toEqual(["x_custom.menu_root"]);
        expect(keys("cài đặt")).toEqual(["base.menu_administration"]);
        expect(keys("settings")).toEqual(["base.menu_administration"]);
        expect(keys("   ")).toHaveLength(6);
        expect(keys("khongtimthay")).toEqual([]);
        // CRM is not in this user's tree: its aliases cannot surface it.
        const restricted = buildTiles(tree(DISCUSS, UNKNOWN));
        expect(filterTiles(restricted, "crm")).toEqual([]);
        expect(filterTiles(restricted, "pipeline")).toEqual([]);
    });

    test("groups split work apps from system tools and drop empty groups", () => {
        const groups = groupTiles(buildTiles(tree(DISCUSS, SETTINGS)));
        expect(groups.map((group) => [group.key, group.tiles.length])).toEqual([
            ["work", 1],
            ["system", 1],
        ]);
        expect(groupTiles(buildTiles(tree(DISCUSS))).map((group) => group.key)).toEqual(["work"]);
        expect(groupTiles([])).toEqual([]);
    });
});

describe("launcher", () => {
    test("renders permitted tiles from the menu service, with native hrefs", async () => {
        defineMenus([HOME, DISCUSS, CRM, TP_ROOT, NO_ACTION, SETTINGS]);
        await mountWithCleanup(HomeLauncher, { props: { action: {}, actionId: 900 } });
        expect(".o_tp_web_home_brand").toHaveText("TANPHAT ONE");
        expect(".o_tp_web_home_search_input").toHaveAttribute("placeholder", "Tìm ứng dụng…");
        expect(queryAllTexts(".o_tp_web_home_group_title")).toEqual([
            "Công việc & nghiệp vụ",
            "Công cụ hệ thống",
        ]);
        expect(queryAllTexts(".o_tp_web_home_label")).toEqual([
            "Trao đổi",
            "CRM",
            "TP Projects",
            "Danh mục công việc",
            "Cài đặt",
        ]);
        expect(queryAll(".o_tp_web_home_tile").map((el) => el.getAttribute("href"))).toEqual([
            "/odoo/discuss",
            "/odoo/crm",
            "/odoo/tp-projects",
            "/odoo/action-904",
            "/odoo/action-906",
        ]);
        expect(`.o_tp_web_home_tile[data-menu-xmlid="${HOME_MENU_XMLID}"]`).toHaveCount(0);
        expect(".o_tp_web_home_tile[href='#']").toHaveCount(0);
    });

    test("search filters, announces, shows the empty state and clears", async () => {
        defineMenus([DISCUSS, CRM, SETTINGS]);
        await mountWithCleanup(HomeLauncher, { props: { action: {}, actionId: 900 } });
        await contains(".o_tp_web_home_search_input").edit("cai dat", { confirm: false });
        expect(queryAllTexts(".o_tp_web_home_label")).toEqual(["Cài đặt"]);
        expect("[role=status]").toHaveText("Tìm thấy 1 ứng dụng");
        await contains(".o_tp_web_home_search_input").edit("khongtimthay", { confirm: false });
        expect(".o_tp_web_home_tile").toHaveCount(0);
        expect(".o_tp_web_home_empty_title").toHaveText("Không tìm thấy ứng dụng phù hợp");
        await contains(".o_tp_web_home_empty .btn").click();
        expect(".o_tp_web_home_tile").toHaveCount(3);
        expect(".o_tp_web_home_search_input").toHaveValue("");
        await contains(".o_tp_web_home_search_input").edit("crm", { confirm: false });
        await contains(".o_tp_web_home_search_clear").click();
        expect(".o_tp_web_home_tile").toHaveCount(3);
        expect(".o_tp_web_home_search_clear").toHaveCount(0);
    });

    test("plain click selects the real menu; modified click keeps the native link", async () => {
        defineMenus([DISCUSS, CRM]);
        await mountWithCleanup(HomeLauncher, { props: { action: {}, actionId: 900 } });
        patchWithCleanup(getService("menu"), {
            selectMenu: (menu) => expect.step(`select ${menu.xmlid}`),
        });
        await contains(".o_tp_web_home_tile[data-menu-xmlid='crm.crm_menu_root']").click();
        expect.verifySteps(["select crm.crm_menu_root"]);

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

    test("Enter opens the first match", async () => {
        defineMenus([DISCUSS, SETTINGS]);
        await mountWithCleanup(HomeLauncher, { props: { action: {}, actionId: 900 } });
        patchWithCleanup(getService("menu"), {
            selectMenu: (menu) => expect.step(`select ${menu.xmlid}`),
        });
        await contains(".o_tp_web_home_search_input").edit("settings", { confirm: false });
        await contains(".o_tp_web_home_search_input").press("Enter");
        expect.verifySteps(["select base.menu_administration"]);
    });

    test("a broken icon image falls back to a monogram", async () => {
        defineMenus([{ ...UNKNOWN, webIconData: "data:image/png;base64,broken" }]);
        await mountWithCleanup(HomeLauncher, { props: { action: {}, actionId: 900 } });
        queryOne(".o_tp_web_home_icon_img").dispatchEvent(new Event("error"));
        await animationFrame();
        expect(".o_tp_web_home_icon_img").toHaveCount(0);
        expect(".o_tp_web_home_icon_monogram").toHaveText("KV");
    });

    test("menu reload drops a revoked app", async () => {
        defineMenus([DISCUSS, CRM]);
        await mountWithCleanup(HomeLauncher, { props: { action: {}, actionId: 900 } });
        expect(".o_tp_web_home_tile").toHaveCount(2);
        MockServer.current.menus = [DISCUSS];
        await getService("menu").reload();
        await animationFrame();
        expect(queryAllTexts(".o_tp_web_home_label")).toEqual(["Trao đổi"]);
        await contains(".o_tp_web_home_search_input").edit("crm", { confirm: false });
        expect(".o_tp_web_home_tile").toHaveCount(0);
    });

    test("reload and search add no global listeners", async () => {
        defineMenus([DISCUSS, CRM]);
        await mountWithCleanup(HomeLauncher, { props: { action: {}, actionId: 900 } });
        const added = [];
        for (const target of [browser, window, document]) {
            patchWithCleanup(target, { addEventListener: (type) => added.push(type) });
        }
        MockServer.current.menus = [DISCUSS];
        await getService("menu").reload();
        await animationFrame();
        // Native input event: HOOT's edit() helper registers listeners of its own.
        const input = queryOne(".o_tp_web_home_search_input");
        input.value = "trao";
        input.dispatchEvent(new Event("input", { bubbles: true }));
        await animationFrame();
        expect(".o_tp_web_home_tile").toHaveCount(1);
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
