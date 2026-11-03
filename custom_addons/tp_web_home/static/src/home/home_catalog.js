/**
 * Home tiles are derived only from the menu tree the native menu service received for the
 * current user (/web/webclient/load_menus is filtered by groups on the server). Labels below
 * enrich a node when its XML ID is actually present; they never create a destination.
 */
export const HOME_MENU_XMLID = "tp_web_home.menu_home";

const DEFAULT_ICON = "/web/static/img/default_icon_app.png";

/** Roots replaced by their own action leaves, so a root and its first leaf never show twice. */
const EXPANDED_ROOTS = new Set(["tp_core.menu_platform"]);

export const GROUPS = [
    { key: "work", label: "Công việc & nghiệp vụ" },
    { key: "system", label: "Công cụ hệ thống" },
];

export const APP_LABELS = {
    "mail.menu_root_discuss": {
        label: "Trao đổi",
        hint: "Discuss",
        aliases: "chat tin nhan thao luan kenh",
    },
    "project_todo.menu_todo_todos": {
        label: "Việc cá nhân",
        hint: "To-do",
        aliases: "todo ghi chu nhac viec",
    },
    "calendar.mail_menu_calendar": {
        label: "Lịch làm việc",
        hint: "Calendar",
        aliases: "lich hop cuoc hen meeting",
    },
    "contacts.menu_contacts": {
        label: "Khách hàng & đối tác",
        hint: "Contacts",
        aliases: "lien he partner customer nha cung cap",
    },
    "crm.crm_menu_root": {
        label: "CRM",
        hint: "Cơ hội kinh doanh",
        aliases: "pipeline lead sales khach hang tiem nang",
    },
    "project.menu_main_pm": {
        label: "Project",
        hint: "Công việc dự án",
        description: "Công việc & tiến độ",
        aliases: "du an task nhiem vu",
    },
    "tp_project.menu_tp_projects": {
        label: "TP Projects",
        hint: "Hồ sơ dự án",
        description: "Hồ sơ & phân công",
        aliases: "du an cau duong project",
    },
    "tp_core.menu_work_items": {
        label: "Danh mục công việc",
        hint: "Work Item Catalog",
        aliases: "hang muc",
    },
    "hr.menu_hr_root": {
        label: "Nhân sự",
        hint: "Employees",
        aliases: "nhan vien hr phong ban",
    },
    "hr_timesheet.timesheet_menu_root": {
        label: "Giờ làm việc",
        hint: "Timesheets",
        aliases: "cham cong timesheet",
    },
    "hr_expense.menu_hr_expense_root": {
        label: "Chi phí",
        hint: "Expenses",
        aliases: "expense hoan ung",
    },
    "account.menu_finance": {
        label: "Hóa đơn",
        hint: "Invoicing",
        aliases: "invoice bill",
    },
    "spreadsheet_dashboard.spreadsheet_dashboard_menu_root": {
        label: "Bảng tổng hợp",
        hint: "Dashboards",
        aliases: "dashboard spreadsheet",
    },
    "base.menu_management": {
        label: "Ứng dụng Odoo",
        hint: "Apps",
        group: "system",
        aliases: "module",
    },
    "base.menu_administration": {
        label: "Cài đặt",
        hint: "Settings",
        group: "system",
        aliases: "thiet lap cau hinh quan tri",
    },
    "base.menu_tests": { group: "system" },
    "utm.menu_link_tracker_root": { group: "system" },
};

export function normalizeSearch(value) {
    return String(value || "")
        .normalize("NFD")
        .replace(/[̀-ͯ]/g, "")
        .replace(/[đĐ]/g, "d")
        .toLowerCase()
        .replace(/\s+/g, " ")
        .trim();
}

export function monogram(label) {
    const words = label.split(/[\s·&/,-]+/).filter(Boolean);
    return words
        .slice(0, 2)
        .map((word) => word[0])
        .join("")
        .toUpperCase();
}

function menuHref(menu, debug) {
    const href = `/odoo/${menu.actionPath || "action-" + menu.actionID}`;
    return debug ? `${href}?debug=${encodeURIComponent(debug)}` : href;
}

function menuIcon(menu, label) {
    if (menu.webIconData && menu.webIconData !== DEFAULT_ICON) {
        return { type: "image", src: menu.webIconData };
    }
    const [icon, color, background] = (menu.webIcon || "").split(",");
    if (icon && background) {
        return { type: "font", icon, color, background };
    }
    return { type: "monogram", text: monogram(label) };
}

function makeTile(menu, debug) {
    const meta = APP_LABELS[menu.xmlid] || {};
    const label = meta.label || menu.name;
    const hint = meta.hint && meta.hint !== label ? meta.hint : "";
    return {
        key: String(menu.id),
        menu,
        xmlid: menu.xmlid,
        label,
        hint,
        description: meta.description || "",
        group: meta.group || (menu.xmlid?.startsWith("base.") ? "system" : "work"),
        href: menuHref(menu, debug),
        icon: menuIcon(menu, label),
        search: normalizeSearch(
            [label, hint, meta.description, menu.name, meta.aliases].filter(Boolean).join(" ")
        ),
    };
}

function actionLeaves(menu) {
    const children = menu.childrenTree || [];
    if (!children.length) {
        return menu.actionID ? [menu] : [];
    }
    return children.flatMap(actionLeaves);
}

/**
 * @param {Object} rootTree `menuService.getMenuAsTree("root")`
 * @param {string} [debug] current debug mode, kept in hrefs like the native apps menu
 * @returns {Object[]} tiles in server (sequence) order
 */
export function buildTiles(rootTree, debug = "") {
    const tiles = [];
    for (const app of rootTree?.childrenTree || []) {
        if (app.xmlid === HOME_MENU_XMLID) {
            continue;
        }
        const leaves = EXPANDED_ROOTS.has(app.xmlid) ? actionLeaves(app) : [];
        for (const menu of leaves.length ? leaves : [app]) {
            if (menu.actionID) {
                tiles.push(makeTile(menu, debug));
            }
        }
    }
    return tiles;
}

export function filterTiles(tiles, query) {
    const words = normalizeSearch(query).split(" ").filter(Boolean);
    if (!words.length) {
        return tiles;
    }
    return tiles.filter((tile) => words.every((word) => tile.search.includes(word)));
}

export function groupTiles(tiles) {
    return GROUPS.map((group) => ({
        ...group,
        tiles: tiles.filter((tile) => tile.group === group.key),
    })).filter((group) => group.tiles.length);
}
