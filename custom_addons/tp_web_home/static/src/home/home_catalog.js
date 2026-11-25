import { router } from "@web/core/browser/router";

/**
 * Home entries are derived only from the menu tree the native menu service received for the
 * current user (/web/webclient/load_menus is filtered by groups on the server). Metadata below
 * enriches a node when its XML ID is actually present; it never grants access or creates routes.
 *
 * UI-SHELL-UNIFY-001: One shared Home catalog and layout for all accounts. Groups render only
 * when they contain at least one permitted entry; developing placeholders stay restricted to
 * system administrators and live delegated administrators.
 */
export const HOME_MENU_XMLID = "tp_web_home.menu_home";
export const ALL_APPS_KEY = "all-apps";

const DEFAULT_ICON = "/web/static/img/default_icon_app.png";

/** Roots replaced by their own action leaves, so a root and its first leaf never show twice. */
const EXPANDED_ROOTS = new Set(["tp_core.menu_platform"]);

/**
 * Unified Home sections in canonical top-to-bottom display order.
 * Empty sections (0 permitted entries) are omitted automatically.
 */
export const SECTIONS = [
    { key: "hr", label: "Nhân sự và chấm công", order: 10 },
    { key: "reporting", label: "Báo cáo và phê duyệt", order: 20 },
    { key: "departments", label: "Phòng ban và đơn vị", order: 30 },
    { key: "personal", label: "Công cụ cá nhân", order: 40 },
    { key: "warehouse", label: "Kho", order: 50 },
];

/** Display order inside the administrators' "Tất cả ứng dụng" panel. */
const PANEL_ORDER = ["hr", "reporting", "workspace", "personal", "warehouse", "apps", "system"];

/**
 * Register or update a Home section deterministically without relying on asset load order.
 */
export function registerHomeSection(section) {
    if (!section?.key) {
        return;
    }
    const existing = SECTIONS.find((s) => s.key === section.key);
    if (existing) {
        if (section.label) {
            existing.label = section.label;
        }
        if (section.order !== undefined) {
            existing.order = section.order;
        }
        return;
    }
    SECTIONS.push({ order: 500, ...section });
    SECTIONS.sort((a, b) => (a.order ?? 500) - (b.order ?? 500));
}

/**
 * Register or update an ADMIN_MODULES entry deterministically by key.
 */
export function registerHomeModule(moduleDef) {
    if (!moduleDef?.key) {
        return;
    }
    const idx = ADMIN_MODULES.findIndex((m) => m.key === moduleDef.key);
    if (idx >= 0) {
        ADMIN_MODULES[idx] = { ...ADMIN_MODULES[idx], ...moduleDef };
        return;
    }
    ADMIN_MODULES.push(moduleDef);
}

export const APP_LABELS = {
    "tp_hr_workspace.menu_department_workspace": {
        hint: "Đang phát triển", group: "workspace", order: 20, icon: "building",
    },
    "tp_kd_workspace.menu_kd": {
        // U+2011 keeps "KH‑KD" on one line; the alias keeps the ASCII spelling searchable.
        label: "Kế hoạch Kinh doanh", hint: "Dự án, đấu thầu, hợp đồng và báo cáo KH‑KD",
        group: "workspace", order: 10, icon: "briefcase",
        aliases: "khkd kh-kd kh kd ke hoach kinh doanh workspace planning business",
    },
    "tp_hr_workspace.menu_hr": {
        label: "Quản lý nhân sự", hint: "Hồ sơ nhân viên, tổ chức và năng lực",
        group: "hr", order: 10, icon: "users",
        aliases: "hr nhan su ho so nhan vien to chuc nang luc",
    },
    "hr.menu_hr_root": {
        label: "Nhân viên", hint: "Danh bạ nhân viên Odoo",
        order: 60,
        aliases: "employees danh ba nhan vien",
    },
    "project_todo.menu_todo_todos": {
        label: "Việc cá nhân",
        hint: "Việc cần làm của bạn", group: "personal", order: 10, icon: "check-square",
        aliases: "todo to-do ghi chu nhac viec",
    },
    "calendar.mail_menu_calendar": {
        label: "Lịch làm việc",
        hint: "Lịch và cuộc hẹn", group: "personal", order: 20, icon: "calendar",
        aliases: "calendar lich hop cuoc hen meeting",
    },
    "mail.menu_root_discuss": {
        label: "Trao đổi",
        hint: "Tin nhắn và kênh nội bộ", group: "personal", order: 30, icon: "message-circle",
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
    const href = router.stateToUrl({ action: menu.actionPath || menu.actionID });
    return debug ? `${href}?debug=${encodeURIComponent(debug)}` : href;
}

function menuIcon(menu, label, meta) {
    if (meta.icon && ["workspace", "projects", "contracts", "catalog", "apps"].includes(meta.icon)) {
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
 * Department & HR catalog definitions (used for unified cards and admin placeholders).
 */
export const ADMIN_MODULES = [
    {
        key: "business",
        group: "departments",
        order: 10,
        name: "Kế hoạch Kinh doanh",
        description: "Dự án, đấu thầu, hợp đồng và báo cáo KH-KD",
        status: "Đang hoạt động",
        badgeKind: "active",
        icon: "briefcase",
        featured: true,
        xmlid: "tp_kd_workspace.menu_kd",
        aliases: "khkd kh-kd kh kd ke hoach kinh doanh workspace planning business",
        copy: "Lối vào không gian KH-KD hiện có: quản lý và quản trị dự án, đấu thầu, hợp đồng, kế hoạch và báo cáo. Khi áp dụng lên hệ thống, mục này tiếp tục mở workspace đang sử dụng.",
    },
    {
        key: "design",
        group: "departments",
        order: 20,
        placeholderOnly: true,
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
        order: 30,
        placeholderOnly: true,
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
        order: 40,
        placeholderOnly: true,
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
        order: 50,
        placeholderOnly: true,
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
        order: 10,
        name: "Quản lý nhân sự",
        description: "Hồ sơ nhân viên, tổ chức và năng lực",
        status: "Đang hoạt động",
        badgeKind: "active",
        icon: "users",
        xmlid: "tp_hr_workspace.menu_hr",
        aliases: "nhan su hr ho so nhan vien to chuc nang luc",
        copy: "Bắt đầu từ hồ sơ nhân viên, phòng ban, chức danh và năng lực. Dữ liệu nguồn đã đối chiếu sẽ được nhập qua bước kiểm tra riêng; tài khoản đăng nhập và quyền truy cập được quản lý độc lập.",
    },
    {
        key: "recruitment",
        group: "hr",
        order: 30,
        placeholderOnly: true,
        name: "Tuyển dụng",
        description: "Vị trí tuyển dụng và hồ sơ ứng viên",
        status: "Đang phát triển",
        badgeKind: "developing",
        icon: "user-plus",
        xmlid: "hr_recruitment.menu_hr_recruitment_root",
        aliases: "tuyen dung ung vien recruitment",
        copy: "Không gian tuyển dụng sẽ được bổ sung sau nền nhân sự: nhu cầu tuyển, vị trí, ứng viên và các vòng xử lý.",
    },
];

function orderedSections() {
    const seen = new Set();
    const list = [];
    for (let i = 0; i < SECTIONS.length; i++) {
        const s = SECTIONS[i];
        if (!s?.key || seen.has(s.key)) {
            continue;
        }
        seen.add(s.key);
        list.push({ ...s, _idx: i });
    }
    list.sort((a, b) => (a.order ?? 500) - (b.order ?? 500) || a._idx - b._idx);
    return list.map(({ _idx, ...rest }) => rest);
}

function sectionRankMap() {
    const ranks = new Map();
    orderedSections().forEach((s, idx) => ranks.set(s.key, idx));
    return ranks;
}

function sortAndDedupeEntries(entries) {
    const ranks = sectionRankMap();
    const seenKeys = new Set();
    const seenMenus = new Set();
    const filtered = [];
    for (let i = 0; i < entries.length; i++) {
        const entry = entries[i];
        if (!entry) {
            continue;
        }
        const entryKey = entry.key || entry.xmlid;
        if (entryKey && seenKeys.has(entryKey)) {
            continue;
        }
        const menuId = entry.menu?.id;
        if (menuId && seenMenus.has(menuId)) {
            continue;
        }
        if (entryKey) {
            seenKeys.add(entryKey);
        }
        if (menuId) {
            seenMenus.add(menuId);
        }
        filtered.push({ entry, idx: i });
    }
    filtered.sort((a, b) => {
        const gA = ranks.get(a.entry.group) ?? 999;
        const gB = ranks.get(b.entry.group) ?? 999;
        if (gA !== gB) {
            return gA - gB;
        }
        const oA = a.entry.order ?? 500;
        const oB = b.entry.order ?? 500;
        if (oA !== oB) {
            return oA - oB;
        }
        return a.idx - b.idx;
    });
    return filtered.map((item) => item.entry);
}

function indexMenuTree(rootTree) {
    const menuMap = new Map();
    function walk(node) {
        if (!node) {
            return;
        }
        if (node.xmlid) {
            menuMap.set(node.xmlid, node);
        }
        for (const child of node.childrenTree || []) {
            walk(child);
        }
    }
    walk(rootTree);
    return menuMap;
}

function attachSearch(entry, extraText = "") {
    return {
        ...entry,
        search: normalizeSearch(
            [entry.name, entry.description, entry.menu?.name, entry.aliases, extraText].filter(Boolean).join(" ")
        ),
    };
}

/**
 * Resolve department and HR entries against the server-filtered menu tree.
 * Without `isSystem`, only entries backed by an authorized menu in `rootTree` are returned.
 */
export function buildAdminCatalog(rootTree, { debug = "", isSystem = true, isDelegated = false } = {}) {
    const menuMap = indexMenuTree(rootTree);
    const rawItems = [];
    for (const tpl of ADMIN_MODULES) {
        const matchedMenu =
            (tpl.xmlid && menuMap.get(tpl.xmlid)) ||
            (tpl.fallbackXmlid && menuMap.get(tpl.fallbackXmlid)) ||
            null;
        const hasActionMenu = Boolean(matchedMenu && matchedMenu.actionID);
        if (tpl.requiresMenu && !hasActionMenu) {
            continue;
        }
        if (!hasActionMenu && !isSystem && !(isDelegated && tpl.placeholderOnly)) {
            continue;
        }
        const item = { ...tpl };
        if (isDelegated && !isSystem && item.key === "equipment") {
            item.status = "Theo phạm vi ủy quyền";
            item.description = "Thiết bị ngoài phòng trong phạm vi được quản lý";
            item.copy = "Xem và cập nhật thiết bị thuộc phòng khác theo quyền được ủy quyền. Thiết bị dùng chung, kho chưa xác định phòng và thao tác chưa được cấp giữ quyền nghiệp vụ hiện hành.";
        }
        if (matchedMenu) {
            item.xmlid = matchedMenu.xmlid;
            item.menu = matchedMenu;
            if (matchedMenu.actionID) {
                item.href = menuHref(matchedMenu, debug);
            }
        }
        rawItems.push(attachSearch(item));
    }

    const deptWsMenu = menuMap.get("tp_hr_workspace.menu_department_workspace");
    if (deptWsMenu && deptWsMenu.actionID) {
        rawItems.push(
            attachSearch({
                key: `menu-${deptWsMenu.id}`,
                group: "departments",
                order: 60,
                name: deptWsMenu.name || "Không gian phòng ban",
                description: "Đang phát triển",
                status: "Đang phát triển",
                badgeKind: "developing",
                icon: "building",
                xmlid: deptWsMenu.xmlid,
                menu: deptWsMenu,
                href: menuHref(deptWsMenu, debug),
            })
        );
    }

    const items = sortAndDedupeEntries(rawItems);
    return {
        modules: items,
        departments: items.filter((m) => m.group === "departments"),
        hr: items.filter((m) => m.group === "hr"),
    };
}

function personalEntries(apps) {
    return apps
        .filter((tile) => tile.group === "personal")
        .map((tile) => {
            const meta = APP_LABELS[tile.xmlid] || {};
            return attachSearch({
                key: tile.key,
                group: "personal",
                order: meta.order ?? tile.order ?? 500,
                name: tile.label,
                description: tile.hint || "",
                icon: meta.icon || "circle",
                aliases: meta.aliases || "",
                xmlid: tile.xmlid,
                menu: tile.menu,
                href: tile.href,
                tile,
            });
        });
}

/**
 * Build the unified Home catalog from the server-filtered menu tree.
 * Backend permissions remain the source of truth: no unauthorized routes or menus are created.
 */
export function buildCatalog(rootTree, { debug = "", isSystem = false, isDelegated = false } = {}) {
    const apps = buildTiles(rootTree, debug);
    const modulesCatalog = buildAdminCatalog(rootTree, { debug, isSystem: Boolean(isSystem), isDelegated });
    const personal = personalEntries(apps);
    const validGroups = new Set(orderedSections().map((s) => s.key));
    const entries = sortAndDedupeEntries([
        ...modulesCatalog.modules.filter((m) => validGroups.has(m.group)),
        ...personal,
    ]);

    const system = isSystem
        ? [allAppsEntry(), ...apps.filter((tile) => tile.group === "system")]
        : [];
    const tools = isSystem
        ? [
              system.find((t) => t.xmlid === "base.menu_administration"),
              system.find((t) => t.xmlid === "base.menu_management"),
              system.find((t) => t.key === ALL_APPS_KEY),
          ].filter(Boolean)
        : [];

    const shownMenuIds = new Set([
        ...entries.map((entry) => entry.menu?.id).filter(Boolean),
        ...system.map((tile) => tile.menu?.id).filter(Boolean),
    ]);

    return {
        isAdmin: Boolean(isSystem),
        admin: modulesCatalog,
        tools,
        entries,
        home: apps.filter((tile) => tile.group === "workspace" || tile.group === "personal"),
        system,
        all: isSystem ? apps : [],
        otherApps: apps.filter((tile) => !shownMenuIds.has(tile.menu?.id)).length,
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
        const text = ` ${tile.search || ""}`;
        return words.every((word) => text.includes(` ${word}`));
    });
}

/** Unified Home sections in canonical display order; empty groups are omitted. */
export function homeSections(catalog, query = "") {
    const entries = sortAndDedupeEntries(filterTiles(catalog.entries || [], query));
    return orderedSections()
        .map((section) => ({
            ...section,
            tiles: entries.filter((entry) => entry.group === section.key),
        }))
        .filter((section) => section.tiles.length > 0);
}
