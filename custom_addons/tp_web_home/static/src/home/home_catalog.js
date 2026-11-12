/**
 * Home entries are derived only from the menu tree the native menu service received for the
 * current user (/web/webclient/load_menus is filtered by groups on the server). Labels below
 * enrich a node when its XML ID is actually present; they never create a destination.
 *
 * UI-HOME-003: Home shows a short, opt-in set of entries (workspaces, personal tools and, for
 * system administrators, an administration area). Every other granted app stays in the native
 * app switcher; it is not removed from the menu service.
 */
export const HOME_MENU_XMLID = "tp_web_home.menu_home";
export const ALL_APPS_KEY = "all-apps";

const DEFAULT_ICON = "/web/static/img/default_icon_app.png";

/** Roots replaced by their own action leaves, so a root and its first leaf never show twice. */
const EXPANDED_ROOTS = new Set(["tp_core.menu_platform"]);

/** Home sections, in display order. Only entries whose metadata names a section appear. */
export const SECTIONS = [
    { key: "workspace", label: "Không gian làm việc" },
    { key: "personal", label: "Công cụ cá nhân" },
    { key: "system", label: "Quản trị hệ thống" },
];

/** Display order inside the administrators' "Tất cả ứng dụng" panel. */
const PANEL_ORDER = ["workspace", "personal", "apps", "system"];

export const APP_LABELS = {
    "tp_hr_workspace.menu_department_workspace": {
        hint: "Đang phát triển", group: "workspace", order: 10, icon: "workspace",
    },
    "tp_kd_workspace.menu_kd": {
        // U+2011 keeps "KH‑KD" on one line; the alias keeps the ASCII spelling searchable.
        label: "Kế hoạch Kinh doanh", hint: "Hồ sơ, kế hoạch và điều hành KH‑KD",
        group: "workspace", order: 10, icon: "workspace",
        aliases: "khkd kh-kd kh kd ke hoach kinh doanh workspace planning business",
    },
    "project_todo.menu_todo_todos": {
        label: "Việc cá nhân",
        hint: "Việc cần làm của bạn", group: "personal", order: 10,
        aliases: "todo to-do ghi chu nhac viec",
    },
    "calendar.mail_menu_calendar": {
        label: "Lịch làm việc",
        hint: "Lịch và cuộc hẹn", group: "personal", order: 20,
        aliases: "calendar lich hop cuoc hen meeting",
    },
    "mail.menu_root_discuss": {
        label: "Trao đổi",
        hint: "Tin nhắn và kênh nội bộ", group: "personal", order: 30,
        aliases: "discuss chat tin nhan thao luan kenh",
    },
    "base.menu_administration": {
        label: "Cài đặt",
        hint: "Thiết lập hệ thống", order: 20,
        group: "system", aliases: "settings thiet lap cau hinh quan tri",
    },
    "base.menu_management": {
        label: "Quản lý ứng dụng",
        hint: "Cài đặt hoặc gỡ ứng dụng", order: 30,
        group: "system", aliases: "apps module cai dat go odoo",
    },
    // Apps below are reached from the native switcher (and the administrators' panel).
    "contacts.menu_contacts": {
        label: "Khách hàng và đối tác", order: 50,
        hint: "Thông tin liên hệ",
        aliases: "contacts lien he partner customer nha cung cap",
    },
    "crm.crm_menu_root": {
        label: "CRM",
        hint: "Cơ hội kinh doanh",
        order: 40, aliases: "pipeline lead sales khach hang tiem nang",
    },
    "project.menu_main_pm": {
        label: "Công việc dự án", order: 30,
        hint: "Công việc và tiến độ dự án",
        aliases: "project du an task nhiem vu",
    },
    "tp_project.menu_tp_projects": {
        label: "TP Projects",
        hint: "Hồ sơ dự án và phân công", order: 10, icon: "projects",
        aliases: "du an cau duong project",
    },
    "tp_contract.menu_tp_contracts": {
        label: "TP Contracts", hint: "Hợp đồng và phiên bản hồ sơ", order: 20, icon: "contracts",
        aliases: "hop dong contract contracts phien ban",
    },
    "tp_core.menu_work_items": {
        label: "Danh mục công việc",
        hint: "Danh mục hạng mục", order: 60, icon: "catalog",
        aliases: "hang muc work item catalog",
    },
    "hr.menu_hr_root": {
        label: "Nhân sự",
        hint: "Hồ sơ nhân viên", order: 100,
        aliases: "employees nhan vien hr phong ban",
    },
    "hr_timesheet.timesheet_menu_root": {
        label: "Giờ làm việc",
        hint: "Thời gian theo công việc", order: 90,
        aliases: "timesheets timesheet thoi gian",
    },
    "hr_expense.menu_hr_expense_root": {
        label: "Chi phí",
        hint: "Chi phí nhân viên", order: 110,
        aliases: "expenses expense hoan ung",
    },
    "account.menu_finance": {
        label: "Hóa đơn",
        hint: "Hồ sơ hóa đơn", order: 80,
        aliases: "invoicing invoice bill",
    },
    "spreadsheet_dashboard.spreadsheet_dashboard_menu_root": {
        label: "Bảng tổng hợp",
        hint: "Báo cáo và bảng dữ liệu", order: 70,
        aliases: "dashboards dashboard spreadsheet",
    },
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

function menuIcon(menu, label, meta) {
    if (meta.icon) {
        return { type: "image", src: `/tp_web_home/static/img/${meta.icon}.svg` };
    }
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
        kind: "menu",
        menu,
        xmlid: menu.xmlid,
        label,
        hint,
        group: meta.group || "apps",
        order: meta.order ?? 1000,
        href: menuHref(menu, debug),
        icon: menuIcon(menu, label, meta),
        search: normalizeSearch([label, hint, menu.name, meta.aliases].filter(Boolean).join(" ")),
    };
}

/** Opens the in-page panel; it is never a menu and has no destination of its own. */
function allAppsEntry() {
    const label = "Tất cả ứng dụng";
    const hint = "Mọi ứng dụng được cấp";
    return {
        key: ALL_APPS_KEY,
        kind: "panel",
        label,
        hint,
        group: "system",
        order: 10,
        icon: { type: "image", src: "/tp_web_home/static/img/apps.svg" },
        search: normalizeSearch(`${label} ${hint} all apps danh sach ung dung`),
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
 * Every app the user can open, in panel order; unknown apps retain their server order.
 * @param {Object} rootTree `menuService.getMenuAsTree("root")`
 * @param {string} [debug] current debug mode, kept in hrefs like the native apps menu
 */
export function buildTiles(rootTree, debug = "") {
    const tiles = [];
    const seen = new Set();
    for (const app of rootTree?.childrenTree || []) {
        if (app.xmlid === HOME_MENU_XMLID) {
            continue;
        }
        const leaves = EXPANDED_ROOTS.has(app.xmlid) ? actionLeaves(app) : [];
        for (const menu of leaves.length ? leaves : [app]) {
            if (menu.actionID && !seen.has(menu.id)) {
                seen.add(menu.id);
                tiles.push(makeTile(menu, debug));
            }
        }
    }
    // Array.prototype.sort is stable: equal keys keep the server menu sequence.
    return tiles.sort((a, b) =>
        PANEL_ORDER.indexOf(a.group) - PANEL_ORDER.indexOf(b.group) || a.order - b.order
    );
}

/**
 * Admin Home (UI-HOME-004 / DEC-036): exactly 7 items in two groups.
 * Group 1: Phòng ban và đơn vị (5 items: KH-KD, Thiết kế, Kỹ Thuật, BIM-QC, TADIC)
 * Group 2: Nhân sự và tuyển dụng (2 items: Quản lý nhân sự, Tuyển dụng)
 */
export const ADMIN_MODULES = [
    {
        key: "business",
        group: "departments",
        name: "Kế hoạch Kinh doanh",
        description: "Dự án, đấu thầu, hợp đồng và báo cáo KH-KD",
        status: "Đang hoạt động",
        badgeKind: "active",
        icon: "briefcase",
        featured: true,
        xmlid: "tp_kd_workspace.menu_kd",
        copy: "Lối vào không gian KH-KD hiện có: quản lý và quản trị dự án, đấu thầu, hợp đồng, kế hoạch và báo cáo. Khi áp dụng lên hệ thống, mục này tiếp tục mở workspace đang sử dụng.",
    },
    {
        key: "design",
        group: "departments",
        name: "Phòng Thiết kế",
        description: "Không gian chuyên môn thiết kế",
        status: "Đang phát triển",
        badgeKind: "developing",
        icon: "ruler",
        copy: "Không gian này đang được chuẩn bị. Các chức năng sẽ được bổ sung sau.",
    },
    {
        key: "technical",
        group: "departments",
        name: "Phòng Kỹ Thuật",
        description: "Không gian chuyên môn kỹ thuật",
        status: "Đang phát triển",
        badgeKind: "developing",
        icon: "hardhat",
        copy: "Không gian này đang được chuẩn bị. Các chức năng sẽ được bổ sung sau.",
    },
    {
        key: "bim",
        group: "departments",
        name: "Phòng BIM-QC",
        description: "Không gian BIM và kiểm soát chất lượng",
        status: "Đang phát triển",
        badgeKind: "developing",
        icon: "boxes",
        copy: "Không gian này đang được chuẩn bị. Các chức năng sẽ được bổ sung sau.",
    },
    {
        key: "tadic",
        group: "departments",
        name: "TADIC",
        description: "Không gian đơn vị TADIC",
        status: "Đang phát triển",
        badgeKind: "developing",
        icon: "building",
        copy: "Không gian này đang được chuẩn bị. Các chức năng sẽ được bổ sung sau.",
    },
    {
        key: "hr",
        group: "hr",
        name: "Quản lý nhân sự",
        description: "Hồ sơ nhân viên, tổ chức và năng lực",
        status: "Đang hoạt động",
        badgeKind: "active",
        icon: "users",
        xmlid: "tp_hr_workspace.menu_hr",
        copy: "Bắt đầu từ hồ sơ nhân viên, phòng ban, chức danh và năng lực. Dữ liệu nguồn đã đối chiếu sẽ được nhập qua bước kiểm tra riêng; tài khoản đăng nhập và quyền truy cập được quản lý độc lập.",
    },
    {
        key: "recruitment",
        group: "hr",
        name: "Tuyển dụng",
        description: "Vị trí tuyển dụng và hồ sơ ứng viên",
        status: "Đang phát triển",
        badgeKind: "developing",
        icon: "user-plus",
        xmlid: "hr_recruitment.menu_hr_recruitment_root",
        copy: "Không gian tuyển dụng sẽ được bổ sung sau nền nhân sự: nhu cầu tuyển, vị trí, ứng viên và các vòng xử lý.",
    },
];

export function buildAdminCatalog(rootTree, { debug = "" } = {}) {
    const menuMap = new Map();
    function walk(node) {
        if (!node) return;
        if (node.xmlid) menuMap.set(node.xmlid, node);
        for (const child of node.childrenTree || []) {
            walk(child);
        }
    }
    walk(rootTree);

    const items = ADMIN_MODULES.map((tpl) => {
        const item = { ...tpl };
        if (item.key === "hr" && !menuMap.has(item.xmlid) && menuMap.has("hr.menu_hr_root")) item.xmlid = "hr.menu_hr_root";
        if (item.xmlid && menuMap.has(item.xmlid)) {
            item.menu = menuMap.get(item.xmlid);
            item.href = menuHref(item.menu, debug);
        }
        return item;
    });

    return {
        modules: items,
        departments: items.filter((m) => m.group === "departments"),
        hr: items.filter((m) => m.group === "hr"),
    };
}

/**
 * Splits the user's own apps into what Home shows and what stays in the native switcher.
 * The administration area and the full app list exist only for system administrators
 * (`user.isSystem`, i.e. base.group_system); for anyone else they are not built at all,
 * so neither the main search nor the DOM can reach them.
 *
 * @returns {{home: Object[], system: Object[], all: Object[], otherApps: number, admin: Object}}
 */
export function buildCatalog(rootTree, { debug = "", isSystem = false } = {}) {
    const apps = buildTiles(rootTree, debug);
    const home = apps.filter((tile) => tile.group === "workspace" || tile.group === "personal");
    const admin = isSystem ? buildAdminCatalog(rootTree, { debug }) : null;
    const system = isSystem
        ? [allAppsEntry(), ...apps.filter((tile) => tile.group === "system")]
        : [];
    const shown = new Set([...home, ...system].map((tile) => tile.key));
    return {
        isAdmin: Boolean(isSystem),
        admin,
        home,
        system,
        all: isSystem ? apps : [],
        otherApps: apps.filter((tile) => !shown.has(tile.key)).length,
    };
}

/**
 * Every typed word must start a word of the entry (label, hint, native name or alias), so
 * "du an" finds "dự án" but not "ứng dụng" / "quản".
 */
export function filterTiles(tiles, query) {
    const words = normalizeSearch(query).split(" ").filter(Boolean);
    if (!words.length) {
        return tiles;
    }
    return tiles.filter((tile) => {
        const text = ` ${tile.search}`;
        return words.every((word) => text.includes(` ${word}`));
    });
}

/** Home sections in display order; the main search walks exactly this list. */
export function homeSections(catalog, query = "") {
    const entries = filterTiles([...catalog.home, ...catalog.system], query);
    return SECTIONS.map((section) => ({
        ...section,
        tiles: entries
            .filter((tile) => tile.group === section.key)
            .sort((a, b) => a.order - b.order),
    })).filter((section) => section.tiles.length);
}
