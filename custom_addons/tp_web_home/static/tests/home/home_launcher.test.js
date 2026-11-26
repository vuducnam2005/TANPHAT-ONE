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
    buildEmployeeQuickGrid,
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
const REP = { id: 22, xmlid: "tp_reporting.menu_root", name: "Báo cáo", actionID: 922 };
const REQ = { id: 23, xmlid: "tp_request.menu_root", name: "Yêu cầu phê duyệt", actionID: 923 };
const EQP = { id: 24, xmlid: "tp_equipment.menu_root", name: "Kho thiết bị văn phòng", actionID: 924 };

const PROPS = { props: { action: {}, actionId: 900 } };

function node(menu) {
    return { ...menu, childrenTree: (menu.children || []).map(node) };
}

function tree(...menus) {
    return { id: "root", childrenTree: menus.map(node) };
}

const keys = (tiles) => tiles.map((tile) => tile.xmlid || tile.key);

function sampleAdminDashboard(overrides = {}) {
    return {
        home_mode: "admin",
        apps_title: "Ứng dụng theo phòng ban",
        meta: {
            home_mode: "admin",
            updated_at: "09:15:00 · 26/11/2026",
            updated_short: "09:15",
            timezone: "Asia/Ho_Chi_Minh",
        },
        cards: [
            {
                key: "hr",
                card_kind: "metric",
                label: "Nhân sự",
                status: "ok",
                count: 39,
                badge_text: "Đang làm việc",
                badge_kind: "neutral",
                can_open: true,
                theme: "blue",
                icon_name: "kpi-hr",
                drilldown: { type: "rpc_action", method: "get_tp_home_hr_drilldown_action" },
            },
            {
                key: "requests",
                card_kind: "metric",
                label: "Yêu cầu phê duyệt",
                status: "ok",
                count: 5,
                badge_text: "Chờ bạn duyệt",
                badge_kind: "purple",
                can_open: true,
                theme: "purple",
                icon_name: "kpi-requests",
                drilldown: {
                    type: "client_action",
                    action_xmlid: "tp_request.action_to_approve",
                    menu_xmlid: "tp_request.menu_root",
                    request_mode: "to_approve",
                    request_tab: "all",
                },
            },
            {
                key: "tasks",
                card_kind: "metric",
                label: "Công việc",
                status: "ok",
                count: 14,
                badge_text: "Phạm vi quản lý",
                badge_kind: "green",
                can_open: true,
                theme: "green",
                icon_name: "kpi-tasks",
                drilldown: { type: "rpc_action", method: "get_tp_home_task_drilldown_action", params: {} },
            },
            {
                key: "stock",
                card_kind: "metric",
                label: "Tồn kho",
                status: "ok",
                count: 7,
                badge_text: "Sẵn sàng: 7",
                badge_kind: "amber",
                can_open: true,
                theme: "amber",
                icon_name: "kpi-stock",
                drilldown: { type: "rpc_action", method: "get_tp_home_stock_drilldown_action" },
            },
        ],
        kpis: {},
        agenda: {
            status: "ok",
            today_display: "26/11/2026",
            timezone: "Asia/Ho_Chi_Minh",
            items: [
                {
                    uid_key: "event-10",
                    kind: "meeting",
                    kind_label: "Cuộc họp",
                    source_label: "",
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
            mode: "admin",
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
                { key: "this_week", label: "Trong tuần này" },
                { key: "this_month", label: "Trong tháng này" },
                { key: "all", label: "Tất cả kỳ" },
            ],
            bar: {
                kind: "department",
                title: "Tình hình công việc",
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
                title: "Tỷ lệ công việc",
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
        ...overrides,
    };
}

function sampleEmployeeDashboard(overrides = {}) {
    return {
        home_mode: "employee",
        apps_title: "Ứng dụng của bạn",
        meta: {
            home_mode: "employee",
            updated_at: "09:20:00 · 26/11/2026",
            updated_short: "09:20",
            timezone: "Asia/Ho_Chi_Minh",
        },
        cards: [
            {
                key: "emp_tasks",
                card_kind: "metric",
                label: "Việc chưa hoàn thành",
                status: "ok",
                count: 3,
                badge_text: "Trong tuần này",
                badge_kind: "blue",
                can_open: true,
                theme: "blue",
                icon_name: "kpi-tasks",
                drilldown: {
                    type: "rpc_action",
                    method: "get_tp_home_task_drilldown_action",
                    params: { bar_segment: "incomplete" },
                },
            },
            {
                key: "emp_requests",
                card_kind: "metric",
                label: "Yêu cầu của tôi chờ duyệt",
                status: "ok",
                count: 2,
                badge_text: "Đang chờ duyệt",
                badge_kind: "purple",
                can_open: true,
                theme: "purple",
                icon_name: "kpi-requests",
                drilldown: {
                    type: "client_action",
                    action_xmlid: "tp_request.action_mine",
                    menu_xmlid: "tp_request.menu_root",
                    request_mode: "mine",
                    request_tab: "pending",
                },
            },
            {
                key: "emp_calendar",
                card_kind: "metric",
                label: "Lịch hẹn hôm nay",
                status: "ok",
                count: 1,
                badge_text: "Lịch 14:00",
                badge_kind: "green",
                can_open: true,
                theme: "green",
                icon_name: "calendar",
                drilldown: {
                    type: "rpc_action",
                    method: "get_tp_home_calendar_drilldown_action",
                },
            },
            {
                key: "emp_attendance",
                card_kind: "status",
                label: "Chấm công hôm nay",
                status: "ok",
                count: null,
                display_text: "Đang làm",
                badge_text: "Vào: 08:26",
                badge_kind: "green",
                can_open: true,
                theme: "amber",
                icon_name: "clock",
                drilldown: {
                    type: "client_action",
                    action_xmlid: "tp_hr_attendance.action_mine",
                    menu_xmlid: "tp_hr_attendance.menu_root",
                    attendance_today: "2026-11-26",
                },
            },
        ],
        kpis: {},
        agenda: {
            status: "ok",
            today_display: "26/11/2026",
            timezone: "Asia/Ho_Chi_Minh",
            items: [
                {
                    uid_key: "task-55",
                    kind: "task",
                    kind_label: "Công việc",
                    source_label: "Dự án",
                    tone: "amber",
                    id: 55,
                    title: "Bàn giao bản vẽ mặt cắt",
                    time_label: "Hạn hôm nay",
                    status_label: "Chờ xác nhận",
                    res_model: "project.task",
                    res_id: 55,
                    route: "/app/ca-nhan/cong-viec/55",
                    linked_task: null,
                },
            ],
            total_today: 1,
            has_more: false,
        },
        charts: {
            status: "ok",
            mode: "employee",
            total: 5,
            done_total: 2,
            incomplete_total: 3,
            scope_key: "my_work",
            scope_label: "Công việc của tôi",
            scope_options: [{ key: "my_work", label: "Công việc của tôi" }],
            can_filter_department: false,
            department_key: "",
            department_label: "Tất cả phòng ban",
            department_options: [{ key: "", label: "Tất cả phòng ban" }],
            period_key: "this_week",
            period_label: "Tuần này (23/11–29/11)",
            period_options: [
                { key: "this_week", label: "Trong tuần này" },
                { key: "this_month", label: "Trong tháng này" },
                { key: "all", label: "Tất cả kỳ" },
            ],
            bar: {
                kind: "daily",
                title: "Công việc của tôi theo ngày",
                subtitle: "Phân bố theo hạn hoàn thành trong kỳ (việc chưa có hạn tách riêng)",
                rows: [
                    { day_key: "2026-11-23", day_label: "T2 23/11", full_label: "T2 23/11/2026", done_count: 1, incomplete_count: 0, total_count: 1 },
                    { day_key: "2026-11-24", day_label: "T3 24/11", full_label: "T3 24/11/2026", done_count: 0, incomplete_count: 0, total_count: 0 },
                    { day_key: "2026-11-26", day_label: "T5 26/11", full_label: "T5 26/11/2026", done_count: 1, incomplete_count: 2, total_count: 3 },
                    { day_key: "undated", day_label: "Chưa đặt hạn", full_label: "Công việc chưa đặt ngày hạn", done_count: 0, incomplete_count: 1, total_count: 1 },
                ],
            },
            donut: {
                title: "Tỷ lệ công việc của tôi",
                subtitle: "Tổng 5 việc (chưa xong: 3)",
                center_count: 5,
                center_label: "Công việc",
                slices: [
                    { key: "done", label: "Hoàn thành", color: "#79BE81", count: 2, percent: 40, exact_percent: 40.0 },
                    { key: "in_progress", label: "Đang thực hiện", color: "#4E7DE8", count: 1, percent: 20, exact_percent: 20.0 },
                    { key: "waiting", label: "Chờ xử lý / xác nhận", color: "#E8AA40", count: 1, percent: 20, exact_percent: 20.0 },
                    { key: "overdue", label: "Quá hạn", color: "#DD6A64", count: 1, percent: 20, exact_percent: 20.0 },
                ],
            },
        },
        ...overrides,
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

    test("employee quick grid exposes authorized daily apps without unauthorized placeholders or system tools", () => {
        const menus = tree(SETTINGS, APPS, UNKNOWN, PROJECT, CONTRACTS, INVOICE, DISCUSS, KD, ATT, REQ, REP, CALENDAR, TP_ROOT, TODO);
        const catalog = buildCatalog(menus, { isSystem: false, homeMode: "employee" });
        expect(catalog.tools).toEqual([]);
        expect(catalog.system).toEqual([]);
        expect(catalog.all).toEqual([]);
        expect(catalog.quickGrid.map((g) => g.gridLabel)).toEqual([
            "Chấm công",
            "Yêu cầu phê duyệt",
            "Báo cáo",
            "Việc cá nhân",
            "Lịch làm việc",
            "Trao đổi",
            "Kế hoạch Kinh doanh",
            "Tất cả ứng dụng",
        ]);
        expect(catalog.quickGrid[0].primaryAccent).toBe(true);

        // Employee with only 2 apps packs cleanly without blank filler slots
        const minimalCat = buildCatalog(tree(ATT, TODO), { isSystem: false, homeMode: "employee" });
        expect(buildEmployeeQuickGrid(minimalCat).map((g) => g.gridLabel)).toEqual([
            "Chấm công",
            "Việc cá nhân",
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
                { isSystem: true, homeMode: "admin" }
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

    test("chart spec builders handle both admin department bars and employee daily bars", () => {
        const adminDash = sampleAdminDashboard();
        const deptSpec = buildDepartmentBarSpec(adminDash.charts);
        expect(deptSpec.data.labels).toEqual(["KH-KD"]);

        const empDash = sampleEmployeeDashboard();
        const dailySpec = buildDepartmentBarSpec(empDash.charts);
        expect(dailySpec.data.labels).toEqual(["T2 23/11", "T3 24/11", "T5 26/11", "Chưa đặt hạn"]);
        expect(dailySpec.data.datasets[0].data).toEqual([1, 0, 1, 0]);
        expect(dailySpec.data.datasets[1].data).toEqual([0, 0, 2, 1]);

        const zeroDonut = buildStatusDonutSpec({
            ...empDash.charts,
            total: 0,
            donut: { center_count: 0, center_label: "Công việc", slices: [] },
        });
        expect(zeroDonut.data.labels).toEqual(["Chưa có công việc"]);
        expect(buildDepartmentBarSpec({ ...empDash.charts, bar: { kind: "daily", rows: [] } })).toBe(null);
    });
});

describe("5-tier HomeLauncher (Admin & Employee Modes)", () => {
    test("Admin mode renders executive KPIs, department grid, and department charts", async () => {
        patchWithCleanup(user, { isSystem: true });
        defineMenus([HOME, KD, HR, EQP, ATT, DISCUSS, TODO, CALENDAR]);
        patchWithCleanup(session, { tp_home_dashboard: true });
        onRpc("res.users", "get_tp_home_dashboard", () => sampleAdminDashboard());
        onRpc("res.users", "get_tp_home_hr_drilldown_action", () => ({
            type: "ir.actions.act_window",
            res_model: "hr.employee",
            views: [[false, "list"]],
        }));

        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();

        expect(".o_tp_web_home").toHaveAttribute("data-home-mode", "admin");
        expect("#tp_home_dept_apps_heading").toHaveText("Ứng dụng theo phòng ban");
        expect(queryAllTexts(".tp-kpi-label")).toEqual([
            "Nhân sự",
            "Yêu cầu phê duyệt",
            "Công việc",
            "Tồn kho",
        ]);
        expect('[data-kpi="stock"] .tp-kpi-value').toHaveText("7");
        expect(".tp-bar-panel .tp-panel-title").toHaveText("Tình hình công việc");
        expect(".tp-donut-panel .tp-panel-title").toHaveText("Tỷ lệ công việc");

        patchWithCleanup(getService("action"), {
            doAction: (act) => expect.step(`action:${act.res_model || act}`),
        });
        await contains('[data-kpi="hr"]').click();
        await contains('[data-kpi="requests"]').click();
        expect.verifySteps(["action:hr.employee", "action:tp_request.action_to_approve"]);
    });

    test("Employee mode renders 4 personal cards (including Attendance status), Ứng dụng của bạn, and daily personal charts without Stock", async () => {
        asEmployee();
        defineMenus([HOME, HR, ATT, REQ, REP, TODO, CALENDAR, DISCUSS]);
        patchWithCleanup(session, { tp_home_dashboard: true });

        let drillTaskArgs = null;
        onRpc("res.users", "get_tp_home_dashboard", () => sampleEmployeeDashboard());
        onRpc("res.users", "get_tp_home_task_drilldown_action", ({ args }) => {
            drillTaskArgs = args[0];
            return {
                type: "ir.actions.act_window",
                res_model: "project.task",
                views: [[false, "list"]],
            };
        });
        onRpc("res.users", "get_tp_home_calendar_drilldown_action", () => ({
            type: "ir.actions.act_window",
            res_model: "calendar.event",
            views: [[false, "calendar"]],
        }));

        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();

        expect(".o_tp_web_home").toHaveAttribute("data-home-mode", "employee");
        expect('[data-kpi="stock"]').toHaveCount(0);
        expect(queryAllTexts(".tp-kpi-label")).toEqual([
            "Việc chưa hoàn thành",
            "Yêu cầu của tôi chờ duyệt",
            "Lịch hẹn hôm nay",
            "Chấm công hôm nay",
        ]);
        expect('[data-kpi="emp_tasks"] .tp-kpi-value').toHaveText("3");
        expect('[data-kpi="emp_tasks"] .tp-kpi-pill').toHaveText("Trong tuần này");
        expect('[data-kpi="emp_requests"] .tp-kpi-value').toHaveText("2");
        expect('[data-kpi="emp_calendar"] .tp-kpi-value').toHaveText("1");
        expect('[data-kpi="emp_attendance"] .tp-kpi-status-value').toHaveText("Đang làm");
        expect('[data-kpi="emp_attendance"] .tp-kpi-pill').toHaveText("Vào: 08:26");

        expect("#tp_home_dept_apps_heading").toHaveText("Ứng dụng của bạn");
        expect(queryAllTexts(".tp-dept-tile-name")).toEqual([
            "Nhân sự",
            "Chấm công",
            "Yêu cầu phê duyệt",
            "Báo cáo",
            "Việc cá nhân",
            "Lịch làm việc",
            "Trao đổi",
            "Tất cả ứng dụng",
        ]);

        expect(".tp-bar-panel .tp-panel-title").toHaveText("Công việc của tôi theo ngày");
        expect(".tp-donut-panel .tp-panel-title").toHaveText("Tỷ lệ công việc của tôi");
        expect(".tp-donut-center-num").toHaveText("5");

        patchWithCleanup(getService("action"), {
            doAction: (act) => expect.step(`action:${act.res_model || act}`),
        });
        await contains('[data-kpi="emp_tasks"]').click();
        expect(drillTaskArgs.bar_segment).toBe("incomplete");
        await contains('[data-kpi="emp_requests"]').click();
        await contains('[data-kpi="emp_calendar"]').click();
        await contains('[data-kpi="emp_attendance"]').click();
        expect.verifySteps([
            "action:project.task",
            "action:tp_request.action_mine",
            "action:calendar.event",
            "action:tp_hr_attendance.action_mine",
        ]);
    });

    test("unlinked employee account renders clear attendance message without crashing Home", async () => {
        asEmployee();
        defineMenus([HOME, ATT, TODO]);
        patchWithCleanup(session, { tp_home_dashboard: true });
        const unlinkedPayload = sampleEmployeeDashboard();
        unlinkedPayload.cards[3] = {
            key: "emp_attendance",
            card_kind: "status",
            label: "Chấm công hôm nay",
            status: "unlinked_employee",
            count: null,
            display_text: "Chưa xác định hồ sơ nhân viên",
            sub_text: "Liên hệ người quản lý tài khoản / HR để gắn hồ sơ",
            badge_text: "",
            can_open: true,
            theme: "amber",
            icon_name: "clock",
            drilldown: { type: "client_action", action_xmlid: "tp_hr_attendance.action_mine" },
        };
        onRpc("res.users", "get_tp_home_dashboard", () => unlinkedPayload);

        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();

        expect('[data-kpi="emp_attendance"]').toHaveAttribute("data-kpi-status", "unlinked_employee");
        expect('[data-kpi="emp_attendance"] .tp-kpi-status-value').toHaveText("Chưa xác định hồ sơ nhân viên");
        expect('[data-kpi="emp_attendance"] .tp-kpi-sub-hint').toHaveText(/Liên hệ người quản lý/);
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
        MockServer.current.menus = [KD, DISCUSS];
        patchWithCleanup(service, { reload });
        await contains(".o_tp_web_home_error button").click();
        await animationFrame();
        expect(queryAllTexts(".tp-dept-tile-name")).toEqual([
            "Trao đổi",
            "Kế hoạch Kinh doanh",
            "Tất cả ứng dụng",
        ]);
    });

    test("Hamburger drawer, Help dialog, and All Apps panel open and close via Escape", async () => {
        asEmployee();
        defineMenus([HOME, KD, DISCUSS, TODO, CALENDAR]);
        await mountWithCleanup(HomeLauncher, PROPS);
        await animationFrame();

        await contains(".tp-home-hamburger").click();
        await animationFrame();
        expect("#tp_home_nav_drawer").toHaveCount(1);
        queryOne("#tp_home_nav_drawer").dispatchEvent(
            new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
        );
        await animationFrame();
        expect("#tp_home_nav_drawer").toHaveCount(0);

        await contains(".tp-home-help-btn").click();
        await animationFrame();
        expect(".tp-home-help-dialog").toHaveCount(1);
        queryOne(".tp-home-help-dialog").dispatchEvent(
            new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
        );
        await animationFrame();
        expect(".tp-home-help-dialog").toHaveCount(0);

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

        input.dispatchEvent(new CompositionEvent("compositionstart", { bubbles: true }));
        input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true, isComposing: true }));
        expect.verifySteps([]);
        input.dispatchEvent(new CompositionEvent("compositionend", { bubbles: true }));

        await contains(".o_tp_web_home_search_input").press("Enter");
        expect.verifySteps([KD.xmlid]);

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
            "Nhân sự",
            "Kế hoạch Kinh doanh",
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
            selectMenu: (menu) => expect.step(`select ${HOME_MENU_XMLID}`),
        });
        await contains(".o_tp_web_home_button").click();
        expect.verifySteps([`select ${HOME_MENU_XMLID}`]);
    });
});
