import { router } from "@web/core/browser/router";

/**
 * Home entries are derived only from the menu tree the native menu service received for the
 * current user (/web/webclient/load_menus is filtered by groups on the server). Metadata below
 * enriches a node when its XML ID is actually present; it never grants access or creates routes.
 *
 * UI-HOME-006: Shared 5-tier Home layout for all accounts:
 * - Quick department grid (up to 10 compact tiles in canonical reference order, filtered strictly by permission).
 * - Full authorized app drawer ("Tất cả ứng dụng" & Hamburger menu) preserving all 5 canonical sections,
 *   additional authorized apps, and restricting system administration tools strictly to `isSystem`.
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

/** Display order inside the "Tất cả ứng dụng" / navigation drawer. */
const PANEL_ORDER = ["hr", "reporting", "workspace", "personal", "warehouse", "apps", "system"];

/**
 * Canonical 10-tile Quick Access Grid order ("Ứng dụng theo phòng ban", Section 8).
 * Each slot renders ONLY when the current user actually has permission to open it.
 */
export const QUICK_GRID_SLOTS = [
    {
        slotKey: "business",
        entryKey: "business",
        xmlid: "tp_kd_workspace.menu_kd",
        gridLabel: "Kế hoạch Kinh doanh",
        gridIcon: "target",
        tone: "primary",
        primaryAccent: true,
    },
    {
        slotKey: "hr",
        entryKey: "hr",
        xmlid: "tp_hr_workspace.menu_hr",
        gridLabel: "Nhân sự",
        gridIcon: "users",
        tone: "blue",
    },
    {
        slotKey: "design",
        entryKey: "design",
        gridLabel: "Thiết kế",
        gridIcon: "layers",
        tone: "indigo",
    },
    {
        slotKey: "technical",
        entryKey: "technical",
        gridLabel: "Kỹ thuật",
        gridIcon: "hardhat",
        tone: "amber",
    },
    {
        slotKey: "bim",
        entryKey: "bim",
        gridLabel: "BIM-QC",
        gridIcon: "cube",
        tone: "purple",
    },
    {
        slotKey: "accounting",
        entryKey: "accounting",
        gridLabel: "Kế toán",
        gridIcon: "calculator",
        tone: "blue",
    },
    {
        slotKey: "tadic",
        entryKey: "tadic",
        gridLabel: "TADIC",
        gridIcon: "building",
        tone: "blue",
    },
    {
        slotKey: "equipment",
        entryKey: "equipment",
        xmlid: "tp_equipment.menu_root",
        gridLabel: "Kho Thiết bị",
        gridIcon: "box",
        tone: "purple",
    },
    {
        slotKey: "attendance",
        entryKey: "attendance",
        xmlid: "tp_hr_attendance.menu_root",
        gridLabel: "Chấm công",
        gridIcon: "clock-briefcase",
        tone: "blue",
    },
    {
        slotKey: ALL_APPS_KEY,
        kind: "panel",
        gridLabel: "Tất cả ứng dụng",
        gridIcon: "grid-four",
        tone: "blue",
    },
];

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
        hint: "Đang phát triển",
        group: "workspace",
        order: 20,
        icon: "building",
    },
    "tp_kd_workspace.menu_kd": {
        label: "Kế hoạch Kinh doanh",
        hint: "Dự án, đấu thầu, hợp đồng và báo cáo KH‑KD",
        group: "workspace",
        order: 10,
        icon: "briefcase",
        aliases: "khkd kh-kd kh kd ke hoach kinh doanh workspace planning business",
    },
    "tp_hr_workspace.menu_hr": {
        label: "Quản lý nhân sự",
        hint: "Hồ sơ nhân viên, tổ chức và năng lực",
        group: "hr",
        order: 10,
        icon: "users",
        aliases: "hr nhan su ho so nhan vien to chuc nang luc",
    },
    "tp_enterprise_ops.menu_recruitment_root": {
        label: "Tuyển dụng",
        hint: "Hồ sơ ứng viên và tiếp nhận nhân sự",
        group: "hr",
        order: 5,
        icon: "user-plus",
        aliases: "tuyen dung ung vien recruitment phong van",
    },
    "tp_digital_office.menu_digital_office_root": {
        label: "Văn phòng số",
        hint: "Thông báo nội bộ và biên bản họp",
        group: "apps",
        order: 5,
        icon: "file-text",
        aliases: "van phong so thong bao noi bo bien ban hop digital office",
    },
    "tp_enterprise_governance.menu_governance_root": {
        label: "Điều hành & Dự án",
        hint: "WBS/CPM, Hồ sơ dự án NAS và Tổng quan điều hành",
        group: "apps",
        order: 6,
        icon: "bar-chart",
        aliases: "dieu hanh du an wbs cpm ho so nas lanh dao",
    },
    "hr.menu_hr_root": {
        label: "Nhân viên",
        hint: "Danh bạ nhân viên Odoo",
        order: 60,
        aliases: "employees danh ba nhan vien",
    },
    "project_todo.menu_todo_todos": {
        label: "Việc cá nhân",
        hint: "Việc cần làm của bạn",
        group: "personal",
        order: 10,
        icon: "check-square",
        aliases: "todo to-do ghi chu nhac viec cong viec cua toi",
    },
    "calendar.mail_menu_calendar": {
        label: "Lịch làm việc",
        hint: "Lịch và cuộc hẹn",
        group: "personal",
        order: 20,
        icon: "calendar",
        aliases: "calendar lich hop cuoc hen meeting phong hop",
    },
    "mail.menu_root_discuss": {
        label: "Trao đổi",
        hint: "Tin nhắn và kênh nội bộ",
        group: "personal",
        order: 30,
        icon: "message-circle",
        aliases: "discuss chat tin nhan thao luan kenh",
    },
    "base.menu_administration": {
        label: "Cài đặt",
        hint: "Thiết lập hệ thống",
        order: 20,
        group: "system",
        aliases: "settings thiet lap cau hinh quan tri",
    },
    "base.menu_management": {
        label: "Quản lý ứng dụng",
        hint: "Cài đặt hoặc gỡ ứng dụng",
        order: 30,
        group: "system",
        aliases: "apps module cai dat go odoo",
    },
    "contacts.menu_contacts": {
        label: "Khách hàng và đối tác",
        order: 50,
        hint: "Thông tin liên hệ",
        aliases: "contacts lien he partner customer nha cung cap",
    },
    "crm.crm_menu_root": {
        label: "CRM",
        hint: "Cơ hội kinh doanh",
        order: 40,
        aliases: "pipeline lead sales khach hang tiem nang",
    },
    "project.menu_main_pm": {
        label: "Công việc dự án",
        order: 30,
        hint: "Công việc và tiến độ dự án",
        aliases: "project du an task nhiem vu",
    },
    "tp_project.menu_tp_projects": {
        label: "TP Projects",
        hint: "Hồ sơ dự án và phân công",
        order: 10,
        icon: "projects",
        aliases: "du an cau duong project",
    },
    "tp_contract.menu_tp_contracts": {
        label: "TP Contracts",
        hint: "Hợp đồng và phiên bản hồ sơ",
        order: 20,
        icon: "contracts",
        aliases: "hop dong contract contracts phien ban",
    },
    "tp_core.menu_work_items": {
        label: "Danh mục công việc",
        hint: "Danh mục hạng mục",
        order: 60,
        icon: "catalog",
        aliases: "hang muc work item catalog",
    },
    "hr_timesheet.timesheet_menu_root": {
        label: "Giờ làm việc",
        hint: "Thời gian theo công việc",
        order: 90,
        aliases: "timesheets timesheet thoi gian",
    },
    "hr_expense.menu_hr_expense_root": {
        label: "Chi phí",
        hint: "Chi phí nhân viên",
        order: 110,
        aliases: "expenses expense hoan ung",
    },
    "account.menu_finance": {
        label: "Hóa đơn",
        hint: "Hồ sơ hóa đơn",
        order: 80,
        aliases: "invoicing invoice bill",
    },
    "spreadsheet_dashboard.spreadsheet_dashboard_menu_root": {
        label: "Bảng tổng hợp",
        hint: "Báo cáo và bảng dữ liệu",
        order: 70,
        aliases: "dashboards dashboard spreadsheet",
    },
};

export function normalizeSearch(value) {
    return String(value || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[đĐ]/g, "d")
        .toLowerCase()
        .replace(/\s+/g, " ")
        .trim();
}

export function monogram(label) {
    const words = String(label || "")
        .split(/[\s·&/,-]+/)
        .filter(Boolean);
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
        name: label,
        hint,
        group: meta.group || "apps",
        order: meta.order ?? 1000,
        href: menuHref(menu, debug),
        icon: menuIcon(menu, label, meta),
        svgIcon: meta.icon || "",
        search: normalizeSearch([label, hint, menu.name, meta.aliases].filter(Boolean).join(" ")),
    };
}

/** Opens the in-page / drawer all-apps panel; never grants unauthorized routes. */
function allAppsEntry() {
    const label = "Tất cả ứng dụng";
    const hint = "Mọi ứng dụng được cấp";
    return {
        key: ALL_APPS_KEY,
        kind: "panel",
        label,
        name: label,
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
    return tiles.sort(
        (a, b) =>
            PANEL_ORDER.indexOf(a.group) - PANEL_ORDER.indexOf(b.group) || a.order - b.order
    );
}

/**
 * Department & HR catalog definitions (used for unified entries and admin placeholders).
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
        aliases: "thiet ke phong thiet ke design",
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
        aliases: "ky thuat phong ky thuat technical",
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
        aliases: "bim qc bim-qc phong bim",
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
        aliases: "tadic don vi tadic",
        copy: "Không gian này đang được chuẩn bị. Các chức năng sẽ được bổ sung sau.",
    },
    {
        key: "accounting",
        group: "departments",
        order: 55,
        placeholderOnly: true,
        name: "Phòng Kế toán",
        description: "Không gian tài chính và kế toán",
        status: "Chưa phát triển",
        badgeKind: "unstarted",
        icon: "calculator",
        aliases: "ke toan phong ke toan tai chinh accounting finance",
        copy: "Không gian Phòng Kế toán chưa phát triển. Các chức năng sẽ được xây dựng trong giai đoạn tiếp theo.",
    },
    {
        key: "recruitment",
        group: "hr",
        order: 5,
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
        label: entry.label || entry.name,
        search: normalizeSearch(
            [entry.name, entry.label, entry.description, entry.menu?.name, entry.aliases, extraText]
                .filter(Boolean)
                .join(" ")
        ),
    };
}

/**
 * Resolve department and HR entries against the server-filtered menu tree.
 * Without `isSystem`, only entries backed by an authorized menu in `rootTree` are returned
 * (except live delegated admins who keep developing department placeholders).
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
        const isInactiveState =
            Boolean(item.placeholderOnly) ||
            item.badgeKind === "developing" ||
            item.badgeKind === "unstarted";
        item.featured = Boolean(item.href) && !isInactiveState;
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
                featured: false,
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
                status: "Đang hoạt động",
                badgeKind: "active",
                featured: Boolean(tile.href),
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
 * Build the 10-slot Quick Department Grid ("Ứng dụng theo phòng ban", Section 8)
 * strictly from authorized entries in `catalog`.
 */
export function buildQuickGrid(catalog, { includeAllApps = true } = {}) {
    const entries = catalog?.entries || [];
    const byKey = new Map();
    const byXmlid = new Map();
    for (const entry of entries) {
        if (entry.key) {
            byKey.set(entry.key, entry);
        }
        if (entry.xmlid) {
            byXmlid.set(entry.xmlid, entry);
        }
    }

    const shortcuts = [];
    const usedKeys = new Set();

    for (const slot of QUICK_GRID_SLOTS) {
        if (slot.kind === "panel") {
            const hasAnyPermittedApp =
                entries.length > 0 || (catalog?.userApps?.length || 0) > 0;
            if (includeAllApps && hasAnyPermittedApp) {
                shortcuts.push({
                    ...allAppsEntry(),
                    key: ALL_APPS_KEY,
                    kind: "panel",
                    name: slot.gridLabel,
                    label: slot.gridLabel,
                    gridLabel: slot.gridLabel,
                    gridIcon: slot.gridIcon,
                    tone: slot.tone,
                    primaryAccent: false,
                });
            }
            continue;
        }
        const match =
            (slot.entryKey && byKey.get(slot.entryKey)) ||
            (slot.xmlid && byXmlid.get(slot.xmlid)) ||
            null;
        if (!match) {
            continue;
        }
        usedKeys.add(match.key);
        shortcuts.push({
            ...match,
            gridLabel: slot.gridLabel,
            gridIcon: slot.gridIcon,
            tone: slot.tone,
            primaryAccent: Boolean(slot.primaryAccent && match.featured),
        });
    }

    // Preserve employee's own developing department card ("Phòng ban của tôi") if granted
    for (const entry of entries) {
        if (
            entry.xmlid === "tp_hr_workspace.menu_department_workspace" &&
            !usedKeys.has(entry.key)
        ) {
            const insertIdx = shortcuts.findIndex((s) => s.kind === "panel");
            const extraCard = {
                ...entry,
                gridLabel: entry.name,
                gridIcon: "building",
                tone: "blue",
                primaryAccent: false,
            };
            if (insertIdx >= 0) {
                shortcuts.splice(insertIdx, 0, extraCard);
            } else {
                shortcuts.push(extraCard);
            }
        }
    }

    return shortcuts;
}

/**
 * Build grouped sections for the "Tất cả ứng dụng" panel and Hamburger navigation drawer.
 * Preserves all 5 canonical groups + extra permitted apps + admin-only system tools.
 */
export function buildDrawerGroups(catalog, query = "") {
    if (!catalog) {
        return [];
    }
    const groups = [];
    const baseSections = homeSections(catalog, query);
    for (const s of baseSections) {
        groups.push({
            key: s.key,
            label: s.label,
            items: s.tiles,
        });
    }

    const extraApps = filterTiles(catalog.extraUserApps || [], query);
    if (extraApps.length) {
        groups.push({
            key: "other_apps",
            label: "Phân hệ và ứng dụng khác",
            items: extraApps,
        });
    }

    if (catalog.isAdmin) {
        const sysTools = filterTiles(
            (catalog.system || []).filter((t) => t.kind !== "panel"),
            query
        );
        if (sysTools.length) {
            groups.push({
                key: "system",
                label: "Quản trị hệ thống",
                items: sysTools,
            });
        }
    }

    return groups;
}

/**
 * Build searchable function entries from permitted Home modules, apps, and action sub-menus.
 * System administration menus are strictly excluded when `isSystem` is false.
 */
export function buildSearchableFunctions(rootTree, catalog, { debug = "", isSystem = false } = {}) {
    const items = [];
    const seenMenuIds = new Set();
    const seenKeys = new Set();

    // 1. Canonical Home entries (including authorized placeholders for admins)
    for (const entry of catalog?.entries || []) {
        const k = entry.key || entry.xmlid;
        if (k && !seenKeys.has(k)) {
            seenKeys.add(k);
            if (entry.menu?.id) {
                seenMenuIds.add(entry.menu.id);
            }
            items.push({
                ...entry,
                categoryLabel: SECTIONS.find((s) => s.key === entry.group)?.label || "Chức năng",
            });
        }
    }

    // 2. Permitted non-system apps & leaf menus in rootTree
    for (const app of rootTree?.childrenTree || []) {
        if (!app || app.xmlid === HOME_MENU_XMLID) {
            continue;
        }
        const appMeta = APP_LABELS[app.xmlid] || {};
        if (appMeta.group === "system" && !isSystem) {
            continue;
        }
        const appName = appMeta.label || app.name || "Ứng dụng";
        if (app.actionID && !seenMenuIds.has(app.id)) {
            seenMenuIds.add(app.id);
            const tile = makeTile(app, debug);
            items.push({
                ...tile,
                categoryLabel: appMeta.group === "system" ? "Quản trị hệ thống" : "Ứng dụng",
            });
        }
        // Walk up to depth 2 children with actions so users can search concrete features
        const walkLeaves = (node, trail) => {
            for (const child of node.childrenTree || []) {
                const cMeta = APP_LABELS[child.xmlid] || {};
                if (cMeta.group === "system" && !isSystem) {
                    continue;
                }
                const cName = cMeta.label || child.name || "";
                if (child.actionID && !seenMenuIds.has(child.id)) {
                    seenMenuIds.add(child.id);
                    items.push({
                        key: `submenu-${child.id}`,
                        kind: "menu",
                        menu: child,
                        xmlid: child.xmlid,
                        name: cName,
                        label: cName,
                        hint: trail,
                        categoryLabel: trail,
                        href: menuHref(child, debug),
                        search: normalizeSearch(`${cName} ${trail} ${cMeta.aliases || ""}`),
                    });
                }
                if (child.childrenTree?.length) {
                    walkLeaves(child, `${trail} › ${cName}`);
                }
            }
        };
        walkLeaves(app, appName);
    }

    return items;
}

/**
 * Build the unified Home catalog from the server-filtered menu tree.
 * Backend permissions remain the source of truth: no unauthorized routes or menus are created.
 */
export function buildCatalog(rootTree, { debug = "", isSystem = false, isDelegated = false } = {}) {
    const apps = buildTiles(rootTree, debug);
    const modulesCatalog = buildAdminCatalog(rootTree, {
        debug,
        isSystem: Boolean(isSystem),
        isDelegated,
    });
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

    const nonSystemApps = apps.filter((tile) => tile.group !== "system");
    const entryMenuIds = new Set(entries.map((e) => e.menu?.id).filter(Boolean));
    const extraUserApps = nonSystemApps.filter((tile) => !entryMenuIds.has(tile.menu?.id));

    const shownMenuIds = new Set([
        ...entryMenuIds,
        ...system.map((tile) => tile.menu?.id).filter(Boolean),
    ]);

    const partialCatalog = {
        isAdmin: Boolean(isSystem),
        admin: modulesCatalog,
        tools,
        entries,
        home: apps.filter((tile) => tile.group === "workspace" || tile.group === "personal"),
        system,
        // Keep `all` admin-only for legacy contract, while `userApps` exposes each user's own permitted apps
        all: isSystem ? apps : [],
        userApps: isSystem ? apps : nonSystemApps,
        extraUserApps,
        otherApps: apps.filter((tile) => !shownMenuIds.has(tile.menu?.id)).length,
    };

    return {
        ...partialCatalog,
        quickGrid: buildQuickGrid(partialCatalog),
        searchableFunctions: buildSearchableFunctions(rootTree, partialCatalog, {
            debug,
            isSystem: Boolean(isSystem),
        }),
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
