import { animationFrame, beforeEach, describe, expect, queryAll, queryAllTexts, queryOne, test } from "@odoo/hoot";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import {
    contains,
    defineMenus,
    getService,
    MockServer,
    mountWithCleanup,
    onRpc,
    patchWithCleanup,
} from "@web/../tests/web_test_helpers";
import { browser } from "@web/core/browser/browser";
import { user } from "@web/core/user";
import { session } from "@web/session";
import { HomeButton } from "@tp_web_home/home/home_button";
import {
    ALL_APPS_KEY,
    ADMIN_MODULES,
    buildAdminCatalog,
    buildCatalog,
    buildDrawerGroups,
    buildQuickGrid,
    buildTiles,
    filterTiles,
    HOME_MENU_XMLID,
    homeSections,
    normalizeSearch,
    registerHomeModule,
    registerHomeSection,
    SECTIONS,
} from "@tp_web_home/home/home_catalog";
import {
    buildDepartmentBarSpec,
    buildStatusDonutSpec,
} from "@tp_web_home/home/home_charts";
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
const ATT = { id: 21, xmlid: "tp_hr_attendance.menu_root", name: "Chấm công", actionID: 921 };
const EQP = { id: 24, xmlid: "tp_equipment.menu_root", name: "Kho thiết bị văn phòng", actionID: 924 };

const PROPS = { props: { action: {}, actionId: 900 } };

function node(menu) {
    return { ...menu, childrenTree: (menu.children || []).map(node) };
}

function tree(...menus) {
    return { id: "root", childrenTree: menus.map(node) };
}

const keys = (tiles) => tiles.map((tile) => tile.xmlid || tile.key);

function sampleDashboard(overrides = {}) {
    return {
        meta: {
            updated_at: "09:15:00 · 26/11/2026",
            updated_short: "09:15",
            timezone: "Asia/Ho_Chi_Minh",
        },
        kpis: {
            hr: {
                key: "hr",
                label: "Nhân sự",
                status: "ok",
                count: 42,
                badge_text: "Đang làm việc",
                badge_kind: "neutral",
                can_open: true,
                drilldown: { type: "rpc_action", method: "get_tp_home_hr_drilldown_action" },
            },
            requests: {
                key: "requests",
                label: "Yêu cầu phê duyệt",
                status: "ok",
                count: 5,
                badge_text: "Chờ bạn duyệt",
                badge_kind: "purple",
                can_open: true,
                drilldown: {
                    type: "client_action",
                    action_xmlid: "tp_request.action_to_approve",
                    menu_xmlid: "tp_request.menu_root",
                    request_mode: "to_approve",
                    request_tab: "all",
                },
            },
            tasks: {
                key: "tasks",
                label: "Công việc",
                status: "ok",
                count: 14,
                badge_text: "Phạm vi quản lý",
                badge_kind: "green",
                can_open: true,
                drilldown: { type: "rpc_action", method: "get_tp_home_task_drilldown_action" },
            },
            stock: {
                key: "stock",
                label: "Tồn kho",
                status: "no_access",
                count: null,
                status_text: "Không có quyền xem",
                can_open: false,
                drilldown: null,
            },
            ...(overrides.kpis || {}),
        },
        agenda: {
            status: "ok",
            today_display: "26/11/2026",
            timezone: "Asia/Ho_Chi_Minh",
            items: [
                {
                    uid_key: "event-10",
                    kind: "meeting",
                    kind_label: "Cuộc họp",
                    tone: "green",
                    id: 10,
                    title: "Họp điều phối dự án cầu đường",
                    time_label: "08:30 – 09:30",
                    status_label: "Lịch hôm nay",
                    res_model: "calendar.event",
                    res_id: 10,
                    route: "",
                    linked_task: null,
                },
            ],
            total_today: 1,
            has_more: false,
            ...(overrides.agenda || {}),
        },
        charts: {
            status: "ok",
            total: 14,
            scope_key: "managed",
            scope_label: "Phạm vi quản lý",
            scope_options: [
                { key: "managed", label: "Phạm vi quản lý" },
                { key: "my_work", label: "Công việc của tôi" },
            ],
            can_filter_department: true,
            department_key: "",
            department_label: "Tất cả phòng ban",
            department_options: [
                { key: "", label: "Tất cả phòng ban" },
                { key: "1", label: "KH-KD" },
            ],
            period_key: "this_month",
            period_label: "Tháng 11/2026",
            period_options: [
                { key: "this_month", label: "Tháng này" },
                { key: "this_week", label: "Tuần này" },
                { key: "all", label: "Tất cả kỳ" },
            ],
            period_rule_note: "Tính theo hạn hoàn thành trong Tháng 11/2026.",
            attribution_note: "Mỗi công việc thuộc đúng một nhóm phòng ban.",
            bar: {
                series: [
                    { key: "done", label: "Hoàn thành", color: "#4E7DE8" },
                    { key: "incomplete", label: "Chưa hoàn thành", color: "#BBD4FA" },
                ],
                rows: [
                    {
                        department_key: "1",
                        department_name: "KH-KD",
                        done_count: 8,
                        incomplete_count: 6,
                        total_count: 14,
                    },
                ],
            },
            donut: {
                center_count: 14,
                center_label: "Công việc",
                slices: [
                    { key: "done", label: "Hoàn thành", color: "#79BE81", count: 8, percent: 57, exact_percent: 57.1 },
                    { key: "in_progress", label: "Đang thực hiện", color: "#4E7DE8", count: 4, percent: 29, exact_percent: 28.6 },
                    { key: "waiting", label: "Chờ xử lý", color: "#E8AA40", count: 1, percent: 7, exact_percent: 7.1 },
                    { key: "overdue", label: "Quá hạn", color: "#DD6A64", count: 1, percent: 7, exact_percent: 7.1 },
                ],
            },
            ...(overrides.charts || {}),
        },
    };
}

defineMailModels();

beforeEach(() => patchWithCleanup(session, { tp_admin_delegation: false, tp_home_dashboard: false }));

function asEmployee() {
    patchWithCleanup(user, { isSystem: false });
}

describe("catalog & chart specs", () => {
    test("delegated equipment copy describes its checked scope", () => {
        const registered = ADMIN_MODULES.some((item) => item.key === "equipment");
        if (!registered) {
            ADMIN_MODULES.push({
                key: "equipment",
                group: "departments",
                name: "Kho thiết bị văn phòng",
                xmlid: "tp_equipment.menu_root",
                status: "Chỉ quản trị hệ thống",
            });
        }
        try {
            const catalog = buildAdminCatalog(
                tree({ id: 18, xmlid: "tp_equipment.menu_root", actionID: 916 }),
                { isSystem: false, isDelegated: true }
            );
            const equipment = catalog.modules.find((item) => item.key === "equipment");
            expect(equipment.status).toBe("Theo phạm vi ủy quyền");
            expect(equipment.description).toBe("Thiết bị ngoài phòng trong phạm vi được quản lý");
            expect(equipment.copy).not.toMatch(/Chỉ quản trị hệ thống/);
        } finally {
            if (!registered) {
                ADMIN_MODULES.pop();
            }
        }
    });

    test("delegated catalog shows developing departments without system tools", () => {
        const catalog = buildCatalog(tree(KD, HR), { isSystem: false, isDelegated: true });
        expect(catalog.entries.some((entry) => entry.key === "design")).toBe(true);
        expect(catalog.entries.some((entry) => entry.key === "technical")).toBe(true);
        expect(catalog.tools).toEqual([]);
        expect(catalog.system).toEqual([]);
        expect(catalog.all).toEqual([]);
        expect(catalog.isAdmin).toBe(false);
    });

    test("unified Home catalog exposes only authorized departments, HR (if granted), and personal tools", () => {
        const menus = tree(SETTINGS, APPS, UNKNOWN, PROJECT, CONTRACTS, INVOICE, DISCUSS, KD, CALENDAR, TP_ROOT, TODO);
        const catalog = buildCatalog(menus, { isSystem: false });
        expect(keys(catalog.entries)).toEqual([KD.xmlid, TODO.xmlid, CALENDAR.xmlid, DISCUSS.xmlid]);
        expect(catalog.tools).toEqual([]);
        expect(catalog.system).toEqual([]);
        expect(catalog.all).toEqual([]);
        expect(catalog.otherApps).toBe(8);
        expect(homeSections(catalog).map((s) => [s.key, s.label])).toEqual([
            ["departments", "Phòng ban và đơn vị"],
            ["personal", "Công cụ cá nhân"],
        ]);

        // Quick 10-slot department grid packs only authorized department tiles + Tất cả ứng dụng
        expect(catalog.quickGrid.map((g) => g.gridLabel)).toEqual([
            "Kế hoạch Kinh doanh",
            "Tất cả ứng dụng",
        ]);
        expect(catalog.quickGrid[0].primaryAccent).toBe(true);

        // Core Odoo Employees directory alone never unlocks Quản lý nhân sự on Home.
        const coreOnlyCatalog = buildCatalog(tree(KD, HR_CORE, DISCUSS), { isSystem: false });
        expect(homeSections(coreOnlyCatalog).map((s) => s.key)).toEqual(["departments", "personal"]);
        expect(coreOnlyCatalog.admin.hr).toEqual([]);

        // User with HR permission sees Nhân sự in quick grid & Nhân sự và chấm công in drawer.
        const hrCatalog = buildCatalog(tree(KD, HR, DISCUSS), { isSystem: false });
        expect(homeSections(hrCatalog).map((s) => s.key)).toEqual(["hr", "departments", "personal"]);
        expect(hrCatalog.quickGrid.map((g) => g.gridLabel)).toEqual([
            "Kế hoạch Kinh doanh",
            "Nhân sự",
            "Tất cả ứng dụng",
        ]);
    });

    test("system administrators get canonical 10-tile quick grid order and admin drawer tools", () => {
        const savedModules = ADMIN_MODULES.map((m) => ({ ...m }));
        try {
            registerHomeModule({
                key: "equipment",
                group: "warehouse",
                order: 10,
                requiresMenu: true,
                name: "Kho thiết bị văn phòng",
                icon: "monitor",
                xmlid: EQP.xmlid,
            });
            registerHomeModule({
                key: "attendance",
                group: "hr",
                order: 20,
                requiresMenu: true,
                name: "Chấm công",
                icon: "clock",
                xmlid: ATT.xmlid,
            });
            const catalog = buildCatalog(
                tree(APPS, SETTINGS, CRM, DISCUSS, KD, UNKNOWN, HR, EQP, ATT),
                { isSystem: true }
            );
            expect(keys(catalog.system)).toEqual([ALL_APPS_KEY, SETTINGS.xmlid, APPS.xmlid]);
            expect(catalog.tools.map((t) => t.label)).toEqual(["Cài đặt", "Quản lý ứng dụng", "Tất cả ứng dụng"]);
            expect(catalog.quickGrid.map((g) => g.gridLabel)).toEqual([
                "Kế hoạch Kinh doanh",
                "Nhân sự",
                "Thiết kế",
                "Kỹ thuật",
                "BIM-QC",
                "Kế toán",
                "TADIC",
                "Kho Thiết bị",
                "Chấm công",
                "Tất cả ứng dụng",
            ]);
            const drawerGroups = buildDrawerGroups(catalog);
            expect(drawerGroups.some((g) => g.key === "system")).toBe(true);
        } finally {
            ADMIN_MODULES.splice(0, ADMIN_MODULES.length, ...savedModules);
        }
    });

    test("searchableFunctions excludes system administration when isSystem is false", () => {
        const menus = tree(SETTINGS, APPS, CRM, PROJECT, DISCUSS, KD, CALENDAR, TODO, TP_ROOT);
        const employee = buildCatalog(menus, { isSystem: false });
        expect(filterTiles(employee.searchableFunctions, "cai dat")).toEqual([]);
        expect(filterTiles(employee.searchableFunctions, "settings")).toEqual([]);
        expect(filterTiles(employee.searchableFunctions, "thiet ke")).toEqual([]);
        expect(filterTiles(employee.searchableFunctions, "khkd").map((t) => t.key)).toEqual(["business"]);

        const admin = buildCatalog(menus, { isSystem: true });
        expect(filterTiles(admin.searchableFunctions, "thiet ke").map((t) => t.key)).toEqual(["design"]);
        expect(filterTiles(admin.searchableFunctions, "cai dat").map((t) => t.xmlid)).toEqual([
            SETTINGS.xmlid,
            APPS.xmlid,
        ]);
    });

    test("users without a workspace keep their tools; empty Home still counts switcher apps", () => {
        expect(keys(buildCatalog(tree(DISCUSS, CRM)).entries)).toEqual([DISCUSS.xmlid]);
        const onlySwitcher = buildCatalog(tree(CRM, INVOICE));
        expect(onlySwitcher.entries).toEqual([]);
        expect(onlySwitcher.otherApps).toBe(2);
        expect(onlySwitcher.quickGrid.map((g) => g.key)).toEqual([ALL_APPS_KEY]);
        expect(buildCatalog(tree(HOME)).quickGrid).toEqual([]);
        const empty = buildCatalog(undefined);
        expect(empty.entries).toEqual([]);
        expect(empty.quickGrid).toEqual([]);
    });

    test("menu identity, diacritics normalization, icons and canonical 5-group order stay intact", () => {
        const sibling = { ...UNKNOWN, id: 61, xmlid: "x_custom.other", name: "Another menu" };
        const tiles = buildTiles(tree(UNKNOWN, sibling, UNKNOWN));
        expect(tiles.map((t) => t.menu.id)).toEqual([UNKNOWN.id, sibling.id]);
        expect(normalizeSearch("  ĐỒNG   Hồ Sơ ")).toBe("dong ho so");
        expect(normalizeSearch(null)).toBe("");

        const [image, font, fallback] = buildTiles(
            tree(
                { ...DISCUSS, webIconData: "data:image/png;base64,AAAA" },
                { ...CRM, webIcon: "fa fa-star,#ffffff,#71639e" },
                { ...UNKNOWN, webIconData: "/web/static/img/default_icon_app.png" }
            )
        );
        expect(image.icon).toEqual({ type: "image", src: "data:image/png;base64,AAAA" });
        expect(font.icon).toEqual({ type: "font", icon: "fa fa-star", color: "#ffffff", background: "#71639e" });
        expect(fallback.icon).toEqual({ type: "monogram", text: "KV" });

        const REP = { id: 22, xmlid: "tp_reporting.menu_root", name: "Báo cáo", actionID: 922 };
        const REQ = { id: 23, xmlid: "tp_request.menu_root", name: "Yêu cầu phê duyệt", actionID: 923 };
        const savedSections = SECTIONS.map((s) => ({ ...s }));
        const savedModules = ADMIN_MODULES.map((m) => ({ ...m }));
        try {
            registerHomeSection({ key: "operations", label: "Vận hành nội bộ", order: 45 });
            registerHomeModule({ key: "equipment", group: "warehouse", order: 10, requiresMenu: true, name: "Kho thiết bị văn phòng", icon: "monitor", xmlid: EQP.xmlid });
            registerHomeModule({ key: "tp_request", group: "reporting", order: 20, requiresMenu: true, name: "Yêu cầu phê duyệt", icon: "request_check", xmlid: REQ.xmlid });
            registerHomeModule({ key: "reporting", group: "reporting", order: 10, requiresMenu: true, name: "Báo cáo", icon: "bar-chart", xmlid: REP.xmlid });
            registerHomeModule({ key: "attendance", group: "hr", order: 20, requiresMenu: true, name: "Chấm công", icon: "clock", xmlid: ATT.xmlid });

            const adminCat = buildCatalog(tree(HOME, EQP, DISCUSS, CALENDAR, TODO, REQ, REP, KD, ATT, HR), { isSystem: true });
            expect(homeSections(adminCat).map((s) => [s.key, s.label])).toEqual([
                ["hr", "Nhân sự và chấm công"],
                ["reporting", "Báo cáo và phê duyệt"],
                ["departments", "Phòng ban và đơn vị"],
                ["personal", "Công cụ cá nhân"],
                ["warehouse", "Kho"],
            ]);
            expect(buildQuickGrid(adminCat)).toHaveLength(10);
        } finally {
            SECTIONS.splice(0, SECTIONS.length, ...savedSections);
            ADMIN_MODULES.splice(0, ADMIN_MODULES.length, ...savedModules);
        }
    });

    test("chart spec builders handle active data and zero-task state cleanly", () => {
        const dash = sampleDashboard();
        const barSpec = buildDepartmentBarSpec(dash.charts);
        expect(barSpec.type).toBe("bar");
        expect(barSpec.data.labels).toEqual(["KH-KD"]);
        expect(barSpec.data.datasets.map((d) => [d.label, d.data])).toEqual([
            ["Hoàn thành", [8]],
            ["Chưa hoàn thành", [6]],
        ]);

        const donutSpec = buildStatusDonutSpec(dash.charts);
        expect(donutSpec.type).toBe("doughnut");
        expect(donutSpec.data.datasets[0].data).toEqual([8, 4, 1, 1]);

        const zeroDonut = buildStatusDonutSpec({
            ...dash.charts,
            total: 0,
            donut: { center_count: 0, center_label: "Công việc", slices: [] },
        });
        expect(zeroDonut.data.labels).toEqual(["Chưa có công việc"]);
        expect(buildDepartmentBarSpec({ ...dash.charts, bar: { rows: [] } })).toBe(null);
    });
});

describe("5-tier HomeLauncher", () => {
    test("delegated capability is refreshed on each Home load without system tools", async () => {
        asEmployee();
        defineMenus([HOME, KD, HR]);
        patchWithCleanup(session, { tp_admin_delegation: true });
        let delegated = true;
        onRpc("res.users", "get_tp_admin_capabilities", () => ({ delegated }));
        const home = await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        expect('[data-module="design"]').toHaveCount(1);
        expect(".tp-admin-inline-tools").toHaveCount(0);
        delegated = false;
        await home.loadMenus();
        await animationFrame();
        expect('[data-module="design"]').toHaveCount(0);
        expect(".tp-admin-inline-tools").toHaveCount(0);
    });

    test("loading and failure never render cached entries; retry applies fresh menus", async () => {
        asEmployee();
        defineMenus([HOME, KD, SETTINGS]);
        await mountWithCleanup(HomeButton);
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
        MockServer.current.menus = [KD, DISCUSS];
        patchWithCleanup(service, { reload });
        await contains(".o_tp_web_home_error button").click();
        await animationFrame();
        expect(queryAllTexts(".tp-dept-tile-name")).toEqual([
            "Kế hoạch Kinh doanh",
            "Tất cả ứng dụng",
        ]);
    });

    test("renders all 5 tiers, real KPIs, Stock no_access state (never 0), and drilldowns", async () => {
        asEmployee();
        defineMenus([HOME, KD, HR, DISCUSS, TODO, CALENDAR]);
        patchWithCleanup(session, { tp_home_dashboard: true });
        let lastTaskParams = null;
        onRpc("res.users", "get_tp_home_dashboard", ({ args }) => {
            lastTaskParams = args[0];
            return sampleDashboard();
        });
        onRpc("res.users", "get_tp_home_hr_drilldown_action", () => ({
            type: "ir.actions.act_window",
            res_model: "hr.employee.public",
            views: [[false, "list"]],
        }));

        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();

        // Tier A: Single light navbar
        expect(".tp-home-navbar").toHaveCount(1);
        expect(".tp-home-nav-title").toHaveText("Trang chủ");
        expect(".o_tp_web_home_search_input").toHaveAttribute(
            "placeholder",
            "Tìm kiếm chức năng, tài liệu…"
        );
        expect(".tp-home-help-btn").toHaveCount(1);
        expect(".tp-home-user-btn").toHaveCount(1);

        // Tier B: Welcome Banner with live user identity
        expect(".tp-home-banner .tp-banner-greeting").toHaveText("Chào mừng trở lại,");
        expect(".tp-home-banner .tp-banner-sub").toHaveText("Hệ thống quản trị nội bộ TANPHAT ONE");

        // Tier C: 4 KPI cards with exact labels & no_access on Stock
        expect(queryAllTexts(".tp-kpi-label")).toEqual([
            "Nhân sự",
            "Yêu cầu phê duyệt",
            "Công việc",
            "Tồn kho",
        ]);
        expect('[data-kpi="hr"] .tp-kpi-value').toHaveText("42");
        expect('[data-kpi="requests"] .tp-kpi-value').toHaveText("5");
        expect('[data-kpi="tasks"] .tp-kpi-value').toHaveText("14");
        expect('[data-kpi="stock"]').toHaveAttribute("data-kpi-status", "no_access");
        expect('[data-kpi="stock"] .tp-kpi-restricted').toHaveText("Không có quyền xem");
        expect('[data-kpi="stock"] .tp-kpi-value').toHaveCount(0);

        // Tier D: Quick Department Grid + Today's Agenda
        expect('[data-module="business"]').toHaveClass("is-primary-accent");
        expect(queryAllTexts(".tp-dept-tile-name")).toEqual([
            "Kế hoạch Kinh doanh",
            "Nhân sự",
            "Tất cả ứng dụng",
        ]);
        expect(".tp-agenda-panel .tp-agenda-title").toHaveText("Họp điều phối dự án cầu đường");
        expect(".tp-agenda-panel .tp-agenda-meta").toHaveText(/08:30 – 09:30/);

        // Tier E: Charts + Donut Legend + Filter synchronization
        expect(".tp-bar-panel .tp-panel-title").toHaveText("Tình hình công việc");
        expect(".tp-donut-panel .tp-panel-title").toHaveText("Tỷ lệ công việc");
        expect(".tp-donut-center-num").toHaveText("14");
        expect(queryAllTexts(".tp-donut-legend-name")).toEqual([
            "Hoàn thành",
            "Đang thực hiện",
            "Chờ xử lý",
            "Quá hạn",
        ]);
        expect(lastTaskParams.period).toBe("this_month");

        // Clicking authorized HR KPI triggers RPC drilldown action
        patchWithCleanup(getService("action"), {
            doAction: (act) => expect.step(`action:${act.res_model || act}`),
        });
        await contains('[data-kpi="hr"]').click();
        await contains('[data-kpi="requests"]').click();
        expect.verifySteps(["action:hr.employee.public", "action:tp_request.action_to_approve"]);
    });

    test("Hamburger drawer, Help dialog, and All Apps panel open and close via Escape", async () => {
        asEmployee();
        defineMenus([HOME, KD, DISCUSS, TODO, CALENDAR]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();

        // Hamburger drawer
        await contains(".tp-home-hamburger").click();
        await animationFrame();
        expect("#tp_home_nav_drawer").toHaveCount(1);
        expect(
            queryAll("#tp_home_nav_drawer .tp-home-nav-section-title").map((el) =>
                el.textContent.trim()
            )
        ).toEqual(["Phòng ban và đơn vị", "Công cụ cá nhân"]);
        queryOne("#tp_home_nav_drawer").dispatchEvent(
            new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
        );
        await animationFrame();
        expect("#tp_home_nav_drawer").toHaveCount(0);

        // Help dialog
        await contains(".tp-home-help-btn").click();
        await animationFrame();
        expect(".tp-home-help-dialog").toHaveCount(1);
        queryOne(".tp-home-help-dialog").dispatchEvent(
            new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
        );
        await animationFrame();
        expect(".tp-home-help-dialog").toHaveCount(0);

        // All Apps panel preserves personal tools not in the 10 department tiles
        await contains('[data-tool="all-apps"]').click();
        await animationFrame();
        expect("#tp_home_all_apps").toHaveCount(1);
        expect(queryAllTexts("#tp_home_all_apps .o_tp_web_home_label")).toEqual([
            "Kế hoạch Kinh doanh",
            "Việc cá nhân",
            "Lịch làm việc",
            "Trao đổi",
        ]);
        queryOne("#tp_home_all_apps").dispatchEvent(
            new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
        );
        await animationFrame();
        expect("#tp_home_all_apps").toHaveCount(0);
    });

    test("non-admin cannot forge #unit deep link hash; admin #unit hash synchronizes placeholder detail", async () => {
        asEmployee();
        defineMenus([HOME, KD]);
        browser.location.hash = "#unit=design";
        try {
            const empHome = await mountWithCleanup(HomeLauncher, PROPS);
            await animationFrame();
            expect("[data-detail-title]").toHaveCount(0);
            empHome.env.bus.trigger("test:cleanup");
        } finally {
            browser.location.hash = "";
        }

        patchWithCleanup(user, { isSystem: true });
        defineMenus([HOME, KD, HR]);
        browser.location.hash = "";
        try {
            await mountWithCleanup(HomeLauncher, PROPS);
            await animationFrame();

            browser.location.hash = "#unit=tech";
            window.dispatchEvent(new HashChangeEvent("hashchange"));
            await animationFrame();
            expect("[data-detail-title]").toHaveText("Phòng Kỹ Thuật");
            expect("[data-detail-status]").toHaveText("Đang phát triển");

            await contains("[data-back]").click();
            await animationFrame();
            expect("[data-detail-title]").toHaveCount(0);
        } finally {
            browser.location.hash = "";
        }
    });

    test("navbar search ignores IME composition, groups permitted functions, and never leaks admin items to employee", async () => {
        asEmployee();
        defineMenus([SETTINGS, APPS, DISCUSS, KD, CALENDAR]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();

        patchWithCleanup(getService("menu"), { selectMenu: (menu) => expect.step(menu.xmlid) });
        const input = queryOne(".o_tp_web_home_search_input");
        await contains(".o_tp_web_home_search_input").edit("kinh doanh", { confirm: false });
        expect(".tp-home-search-dropdown").toHaveCount(1);
        expect(queryAllTexts(".tp-search-hit-title")).toEqual(["Kế hoạch Kinh doanh"]);

        // IME composing Enter must not activate search result
        input.dispatchEvent(new CompositionEvent("compositionstart", { bubbles: true }));
        input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true, isComposing: true }));
        expect.verifySteps([]);
        input.dispatchEvent(new CompositionEvent("compositionend", { bubbles: true }));

        await contains(".o_tp_web_home_search_input").press("Enter");
        expect.verifySteps([KD.xmlid]);

        // Employee typing admin or ungranted placeholder keywords gets empty result
        for (const q of ["cai dat", "settings", "thiet ke", "tuyen dung"]) {
            await contains(".o_tp_web_home_search_input").edit(q, { confirm: false });
            await contains(".o_tp_web_home_search_input").press("Enter");
            expect(".tp-search-empty").toHaveCount(1);
        }
        expect.verifySteps([]);
    });

    test("plain click selects real menu; modified click preserves native link; broken icon falls back to monogram", async () => {
        patchWithCleanup(user, { isSystem: true });
        defineMenus([HOME, KD, { ...UNKNOWN, webIconData: "data:image/png;base64,broken" }]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();

        patchWithCleanup(getService("menu"), {
            selectMenu: (menu) => expect.step(`select ${menu.xmlid}`),
        });
        await contains('.tp-entry[data-menu-xmlid="tp_kd_workspace.menu_kd"]').click();
        expect.verifySteps(["select tp_kd_workspace.menu_kd"]);

        let nativeDefault = null;
        const observe = (ev) => {
            nativeDefault = !ev.defaultPrevented;
            ev.preventDefault();
        };
        document.addEventListener("click", observe);
        try {
            queryOne('.tp-entry[data-menu-xmlid="tp_kd_workspace.menu_kd"]').dispatchEvent(
                new MouseEvent("click", { bubbles: true, cancelable: true, ctrlKey: true })
            );
        } finally {
            document.removeEventListener("click", observe);
        }
        expect(nativeDefault).toBe(true);
        expect.verifySteps([]);

        await contains('[data-tool="all-apps"]').click();
        await animationFrame();
        queryOne("#tp_home_all_apps .o_tp_web_home_icon_img").dispatchEvent(new Event("error"));
        await animationFrame();
        expect("#tp_home_all_apps .o_tp_web_home_icon_monogram").toHaveText("KV");
    });

    test("menu reload drops revoked entry and adds no extra global listeners", async () => {
        asEmployee();
        defineMenus([KD, HR]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        expect(queryAllTexts(".tp-dept-tile-name")).toEqual([
            "Kế hoạch Kinh doanh",
            "Nhân sự",
            "Tất cả ứng dụng",
        ]);

        const added = [];
        for (const target of [browser, window, document]) {
            patchWithCleanup(target, { addEventListener: (type) => added.push(type) });
        }

        MockServer.current.menus = [KD];
        await getService("menu").reload();
        await animationFrame();
        expect(queryAllTexts(".tp-dept-tile-name")).toEqual([
            "Kế hoạch Kinh doanh",
            "Tất cả ứng dụng",
        ]);

        const input = queryOne(".o_tp_web_home_search_input");
        input.value = "nhan su";
        input.dispatchEvent(new Event("input", { bubbles: true }));
        await animationFrame();
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

    test("mounting HomeLauncher or navigating back to Home resets active app from workspace to Trang chủ", async () => {
        defineMenus([HOME, HR, DISCUSS]);
        const button = await mountWithCleanup(HomeButton);
        const menu = getService("menu");
        menu.setCurrentMenu(HR.id);
        expect(menu.getCurrentApp().xmlid).toBe(HR.xmlid);

        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();
        expect(menu.getCurrentApp().xmlid).toBe(HOME_MENU_XMLID);

        const actionService = getService("action");
        menu.setCurrentMenu(HR.id);
        await animationFrame();
        expect(".o_tp_web_home_button").not.toHaveAttribute("aria-current");

        patchWithCleanup(actionService, {
            currentController: {
                action: { id: HOME.actionID, tag: "tp_web_home.home", xml_id: false, res_model: false, path: "tp-home" },
            },
        });
        button.env.bus.trigger("ACTION_MANAGER:UI-UPDATED");
        await animationFrame();
        expect(menu.getCurrentApp().xmlid).toBe(HOME_MENU_XMLID);
        expect(".o_tp_web_home_button").toHaveAttribute("aria-current", "page");
    });
});
