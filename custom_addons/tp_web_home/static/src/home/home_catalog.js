import { router } from "@web/core/browser/router";

/**
 * Home entries are derived only from the menu tree the native menu service received for the
 * current user (/web/webclient/load_menus is filtered by groups on the server). Metadata below
 * enriches a node when its XML ID is actually present; it never grants access or creates routes.
 *
 * UI-HOME-006 & UI-HOME-007:
 * - Admin mode ("Ứng dụng theo phòng ban"): canonical 10-tile department & HR grid matching reference.
 * - Employee mode ("Ứng dụng của bạn"): compact grid of the user's real authorized daily apps &
 *   department workspaces (no fake blank tiles, no unauthorized department placeholders, no admin tools).
 * - Full authorized app drawer ("Tất cả ứng dụng" & Hamburger menu) preserves all 5 canonical sections,
 *   additional authorized apps, and restricts system administration tools strictly to `isSystem`.
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
    { key: "hr", label: "Nhân sự và chấm công", tabLabel: "Nhân sự", order: 10 },
    { key: "reporting", label: "Báo cáo và phê duyệt", tabLabel: "Báo cáo", order: 20 },
    { key: "departments", label: "Phòng ban và đơn vị", tabLabel: "Phòng ban", order: 30 },
    { key: "personal", label: "Công cụ cá nhân", tabLabel: "Cá nhân", order: 40 },
    { key: "warehouse", label: "Kho", tabLabel: "Kho", order: 50 },
];

/** Display order inside the "Tất cả ứng dụng" / navigation drawer. */
const PANEL_ORDER = ["hr", "reporting", "workspace", "personal", "warehouse", "apps", "system"];

/**
 * Deterministic display order inside each business group, independent of asset load order
 * when external addons call `registerHomeModule(...)`.
 */
const CANONICAL_MODULE_ORDER = {
    hr: 10,
    attendance: 20,
    recruitment: 30,
    reporting: 10,
    tp_request: 20,
    governance: 30,
    digital_office: 40,
    business: 10,
    design: 20,
    technical: 30,
    bim: 40,
    accounting: 50,
    tadic: 55,
    equipment: 10,
    maintenance: 20,
};

/**
 * Stable shortcut & app-switcher color palette mapping by XML ID and canonical module key
 * (UI-HOME-008..010 & UI-APPS-001). Never relies on DOM position (`nth-child`) or Vietnamese text.
 */
export const SHORTCUT_PALETTE_BY_XMLID = {
    "tp_kd_workspace.menu_kd": "business",
    "tp_hr_workspace.menu_hr": "hr",
    "tp_equipment.menu_root": "equipment",
    "tp_hr_attendance.menu_root": "attendance",
    "tp_request.menu_root": "requests",
    "tp_reporting.menu_root": "reporting",
    "project_todo.menu_todo_todos": "todo",
    "calendar.mail_menu_calendar": "calendar",
    "mail.menu_root_discuss": "discuss",
    "tp_hr_workspace.menu_department_workspace": "dept-workspace",
    "tp_digital_office.menu_digital_office_root": "digital-office",
    "tp_enterprise_ops.menu_recruitment_root": "recruitment",
    "hr_recruitment.menu_hr_recruitment_root": "recruitment",
    "tp_enterprise_governance.menu_governance_root": "governance",
    "maintenance.menu_maintenance_title": "maintenance",
    "tp_project.menu_tp_projects": "projects",
    "tp_contract.menu_tp_contracts": "contracts",
    "project.menu_main_pm": "project-pm",
    "tp_core.menu_work_items": "catalog",
    "crm.crm_menu_root": "crm",
    "contacts.menu_contacts": "contacts",
    "spreadsheet_dashboard.spreadsheet_dashboard_menu_root": "spreadsheet",
    "account.menu_finance": "invoicing",
    "hr_timesheet.timesheet_menu_root": "timesheet",
    "hr_expense.menu_hr_expense_root": "expense",
    "hr.menu_hr_root": "hr-core",
    "utm.menu_link_tracker_root": "utm",
    "base.menu_administration": "system",
    "base.menu_management": "system-apps",
};

export const SHORTCUT_PALETTE_BY_KEY = {
    business: "business",
    hr: "hr",
    design: "design",
    technical: "technical",
    bim: "bim",
    accounting: "accounting",
    tadic: "tadic",
    equipment: "equipment",
    maintenance: "maintenance",
    attendance: "attendance",
    [ALL_APPS_KEY]: "all-apps",
    tp_request: "requests",
    requests: "requests",
    reporting: "reporting",
    todo: "todo",
    calendar: "calendar",
    discuss: "discuss",
    dept_workspace: "dept-workspace",
    "dept-workspace": "dept-workspace",
    digital_office: "digital-office",
    "digital-office": "digital-office",
    recruitment: "recruitment",
    governance: "governance",
    projects: "projects",
    contracts: "contracts",
    "project-pm": "project-pm",
    catalog: "catalog",
    crm: "crm",
    contacts: "contacts",
    spreadsheet: "spreadsheet",
    invoicing: "invoicing",
    timesheet: "timesheet",
    expense: "expense",
    "hr-core": "hr-core",
    utm: "utm",
    system: "system",
    "system-apps": "system-apps",
};

export function resolveShortcutPalette(item) {
    if (!item) {
        return "default";
    }
    if (item.kind === "panel" || item.key === ALL_APPS_KEY || item.slotKey === ALL_APPS_KEY) {
        return "all-apps";
    }
    const byXmlid = item.xmlid && SHORTCUT_PALETTE_BY_XMLID[item.xmlid];
    if (byXmlid) {
        return byXmlid;
    }
    for (const k of [item.palette, item.entryKey, item.slotKey, item.key]) {
        if (k && SHORTCUT_PALETTE_BY_KEY[k]) {
            return SHORTCUT_PALETTE_BY_KEY[k];
        }
    }
    return "default";
}

/**
 * Admin Mode canonical 10-tile Quick Access Grid ("Ứng dụng theo phòng ban", Section 8).
 */
export const QUICK_GRID_SLOTS = [
    {
        slotKey: "business",
        entryKey: "business",
        xmlid: "tp_kd_workspace.menu_kd",
        gridLabel: "Kế hoạch Kinh doanh",
        gridIcon: "target",
        palette: "business",
    },
    {
        slotKey: "hr",
        entryKey: "hr",
        xmlid: "tp_hr_workspace.menu_hr",
        gridLabel: "Nhân sự",
        gridIcon: "users",
        palette: "hr",
    },
    {
        slotKey: "design",
        entryKey: "design",
        gridLabel: "Thiết kế",
        gridIcon: "layers",
        palette: "design",
    },
    {
        slotKey: "technical",
        entryKey: "technical",
        gridLabel: "Kỹ thuật",
        gridIcon: "hardhat",
        palette: "technical",
    },
    {
        slotKey: "bim",
        entryKey: "bim",
        gridLabel: "BIM-QC",
        gridIcon: "cube",
        palette: "bim",
    },
    {
        slotKey: "accounting",
        entryKey: "accounting",
        gridLabel: "Kế toán",
        gridIcon: "calculator",
        palette: "accounting",
    },
    {
        slotKey: "tadic",
        entryKey: "tadic",
        gridLabel: "TADIC",
        gridIcon: "building",
        palette: "tadic",
    },
    {
        slotKey: "equipment",
        entryKey: "equipment",
        xmlid: "tp_equipment.menu_root",
        gridLabel: "Kho Thiết bị",
        gridIcon: "box",
        palette: "equipment",
    },
    {
        slotKey: "attendance",
        entryKey: "attendance",
        xmlid: "tp_hr_attendance.menu_root",
        gridLabel: "Chấm công",
        gridIcon: "clock",
        palette: "attendance",
    },
    {
        slotKey: ALL_APPS_KEY,
        kind: "panel",
        gridLabel: "Tất cả ứng dụng",
        gridIcon: "grid-four",
        palette: "all-apps",
    },
];

/**
 * Employee Mode priority slots ("Ứng dụng của bạn", UI-HOME-007 Section 5).
 * Only entries backed by an authorized menu in the server-filtered menu tree are rendered.
 */
export const EMPLOYEE_GRID_SLOTS = [
    {
        slotKey: "hr",
        entryKey: "hr",
        xmlid: "tp_hr_workspace.menu_hr",
        gridLabel: "Nhân sự",
        gridIcon: "users",
        palette: "hr",
    },
    {
        slotKey: "attendance",
        entryKey: "attendance",
        xmlid: "tp_hr_attendance.menu_root",
        gridLabel: "Chấm công",
        gridIcon: "clock",
        palette: "attendance",
    },
    {
        slotKey: "requests",
        entryKey: "tp_request",
        xmlid: "tp_request.menu_root",
        gridLabel: "Yêu cầu phê duyệt",
        gridIcon: "kpi-requests",
        palette: "requests",
    },
    {
        slotKey: "reporting",
        entryKey: "reporting",
        xmlid: "tp_reporting.menu_root",
        gridLabel: "Báo cáo",
        gridIcon: "bar-chart",
        palette: "reporting",
    },
    {
        slotKey: "todo",
        xmlid: "project_todo.menu_todo_todos",
        gridLabel: "Việc cá nhân",
        gridIcon: "check-square",
        palette: "todo",
    },
    {
        slotKey: "calendar",
        xmlid: "calendar.mail_menu_calendar",
        gridLabel: "Lịch làm việc",
        gridIcon: "calendar",
        palette: "calendar",
    },
    {
        slotKey: "discuss",
        xmlid: "mail.menu_root_discuss",
        gridLabel: "Trao đổi",
        gridIcon: "message-circle",
        palette: "discuss",
    },
    {
        slotKey: "business",
        entryKey: "business",
        xmlid: "tp_kd_workspace.menu_kd",
        gridLabel: "Kế hoạch Kinh doanh",
        gridIcon: "target",
        palette: "business",
    },
    {
        slotKey: "dept_workspace",
        xmlid: "tp_hr_workspace.menu_department_workspace",
        gridLabel: "",
        gridIcon: "building",
        palette: "dept-workspace",
    },
    {
        slotKey: "equipment",
        entryKey: "equipment",
        xmlid: "tp_equipment.menu_root",
        gridLabel: "Kho Thiết bị",
        gridIcon: "box",
        palette: "equipment",
    },
    {
        slotKey: "digital_office",
        xmlid: "tp_digital_office.menu_digital_office_root",
        gridLabel: "Văn phòng số",
        gridIcon: "file-text",
        palette: "digital-office",
    },
    {
        slotKey: "recruitment",
        xmlid: "tp_enterprise_ops.menu_recruitment_root",
        gridLabel: "Tuyển dụng",
        gridIcon: "user-plus",
        palette: "recruitment",
    },
    {
        slotKey: "governance",
        xmlid: "tp_enterprise_governance.menu_governance_root",
        gridLabel: "Điều hành & Dự án",
        gridIcon: "bar-chart",
        palette: "governance",
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
    const canonicalOrder = CANONICAL_MODULE_ORDER[moduleDef.key];
    const normalized =
        canonicalOrder !== undefined ? { ...moduleDef, order: canonicalOrder } : moduleDef;
    const idx = ADMIN_MODULES.findIndex((m) => m.key === normalized.key);
    if (idx >= 0) {
        ADMIN_MODULES[idx] = { ...ADMIN_MODULES[idx], ...normalized };
        return;
    }
    ADMIN_MODULES.push(normalized);
}

export const APP_LABELS = {
    "tp_hr_workspace.menu_department_workspace": {
        label: "Phòng ban của tôi",
        hint: "Đang phát triển",
        group: "workspace",
        order: 60,
        icon: "building",
        aliases: "phong ban cua toi khong gian phong ban department workspace",
    },
    "tp_kd_workspace.menu_kd": {
        label: "Kế hoạch Kinh doanh",
        hint: "Dự án, đấu thầu, hợp đồng và báo cáo KH‑KD",
        group: "workspace",
        order: 10,
        icon: "target",
        aliases: "khkd kh-kd kh kd ke hoach kinh doanh workspace planning business",
    },
    "tp_hr_workspace.menu_hr": {
        label: "Quản lý nhân sự",
        hint: "Hồ sơ nhân viên, tổ chức và năng lực",
        group: "hr",
        order: 10,
        icon: "users",
        aliases: "tp hr nhan su quan ly nhan su ho so nhan vien to chuc nang luc",
    },
    "tp_hr_attendance.menu_root": {
        label: "Chấm công",
        hint: "Ngày công cá nhân, bảng công và đề nghị điều chỉnh",
        group: "hr",
        order: 20,
        icon: "clock",
        aliases: "cham cong bang cong cong cua toi attendance enti",
    },
    "tp_enterprise_ops.menu_recruitment_root": {
        label: "Tuyển dụng",
        hint: "Hồ sơ ứng viên và tiếp nhận nhân sự",
        group: "hr",
        order: 30,
        icon: "user-plus",
        aliases: "tuyen dung ung vien recruitment phong van tiep nhan",
    },
    "tp_reporting.menu_root": {
        label: "Báo cáo",
        hint: "Báo cáo cá nhân, phòng ban và công ty",
        group: "reporting",
        order: 10,
        icon: "bar-chart",
        aliases: "bao cao ke hoach chi tieu reporting",
    },
    "tp_request.menu_root": {
        label: "Yêu cầu phê duyệt",
        hint: "Đề nghị cá nhân và quy trình phê duyệt nội bộ",
        group: "reporting",
        order: 20,
        icon: "kpi-requests",
        aliases: "yeu cau phe duyet de nghi to trinh request approval",
    },
    "tp_enterprise_governance.menu_governance_root": {
        label: "Điều hành lãnh đạo",
        hint: "Tổng quan điều hành, WBS/CPM và Hồ sơ dự án NAS",
        group: "reporting",
        order: 30,
        icon: "compass",
        aliases: "dieu hanh lanh dao dieu hanh du an wbs cpm ho so nas governance",
    },
    "tp_digital_office.menu_digital_office_root": {
        label: "Văn phòng số",
        hint: "Thông báo nội bộ và biên bản họp",
        group: "reporting",
        order: 40,
        icon: "file-text",
        aliases: "van phong so thong bao noi bo bien ban hop digital office",
    },
    "tp_equipment.menu_root": {
        label: "Kho thiết bị văn phòng",
        hint: "Thiết bị, bàn giao và kiểm kê",
        group: "warehouse",
        order: 10,
        icon: "box",
        aliases: "kho thiet bi van phong tai san equipment may tinh",
    },
    "maintenance.menu_maintenance_title": {
        label: "Bảo dưỡng thiết bị",
        hint: "Yêu cầu bảo trì và theo dõi thiết bị",
        group: "warehouse",
        order: 20,
        icon: "wrench",
        aliases: "bao duong bao tri maintenance thiet bi oee",
    },
    "project_todo.menu_todo_todos": {
        label: "Việc cá nhân",
        hint: "Việc cần làm của bạn",
        group: "personal",
        order: 10,
        icon: "check-square",
        aliases: "viec ca nhan todo to-do ghi chu nhac viec cong viec cua toi",
    },
    "calendar.mail_menu_calendar": {
        label: "Lịch làm việc",
        hint: "Lịch và cuộc hẹn",
        group: "personal",
        order: 20,
        icon: "calendar",
        aliases: "lich lam viec calendar lich hop cuoc hen meeting phong hop",
    },
    "mail.menu_root_discuss": {
        label: "Trao đổi",
        hint: "Tin nhắn và kênh nội bộ",
        group: "personal",
        order: 30,
        icon: "message-circle",
        aliases: "trao doi discuss chat tin nhan thao luan kenh",
    },
    "base.menu_administration": {
        label: "Cài đặt",
        hint: "Thiết lập hệ thống",
        order: 10,
        group: "system",
        icon: "settings",
        aliases: "cai dat settings thiet lap cau hinh quan tri he thong",
    },
    "base.menu_management": {
        label: "Quản lý ứng dụng",
        hint: "Cài đặt hoặc gỡ ứng dụng",
        order: 20,
        group: "system",
        icon: "sliders",
        aliases: "quan ly ung dung apps module cai dat go odoo",
    },
    "tp_project.menu_tp_projects": {
        label: "TP Projects — Dự án cầu đường",
        hint: "Hồ sơ dự án cầu đường và phân công",
        order: 10,
        icon: "projects",
        aliases: "tp projects ho so du an cau duong project tanphat one",
    },
    "tp_contract.menu_tp_contracts": {
        label: "TP Contracts — Hợp đồng",
        hint: "Hợp đồng và phiên bản hồ sơ",
        order: 20,
        icon: "contracts",
        aliases: "tp contracts hop dong contract phu luc phien ban tanphat one",
    },
    "project.menu_main_pm": {
        label: "Quản lý dự án & Nhiệm vụ",
        order: 30,
        hint: "Không gian dự án và nhiệm vụ chung",
        icon: "kanban",
        aliases: "quan ly du an cong viec du an project nhiem vu task",
    },
    "crm.crm_menu_root": {
        label: "CRM — Cơ hội kinh doanh",
        hint: "Pipeline khách hàng tiềm năng và cơ hội bán hàng",
        order: 40,
        icon: "trending-up",
        aliases: "crm co hoi kinh doanh pipeline lead sales khach hang tiem nang",
    },
    "contacts.menu_contacts": {
        label: "Khách hàng & Đối tác",
        order: 50,
        hint: "Danh bạ đối tác, khách hàng và nhà cung cấp",
        icon: "contact",
        aliases: "khach hang va doi tac contacts lien he partner customer nha cung cap",
    },
    "tp_core.menu_work_items": {
        label: "Danh mục công việc",
        hint: "Danh mục hạng mục chuẩn",
        order: 60,
        icon: "catalog",
        aliases: "danh muc cong viec hang muc work item catalog tanphat one",
    },
    "hr.menu_hr_root": {
        label: "Danh bạ & Kỹ năng (Odoo HR)",
        hint: "Danh bạ nhân viên và kho kỹ năng cơ bản",
        order: 65,
        icon: "users",
        aliases: "nhan vien employees danh ba nhan vien ky nang chung chi hr",
    },
    "hr_recruitment.menu_hr_recruitment_root": {
        label: "Tuyển dụng (Cấu hình Odoo)",
        hint: "Vị trí công việc, ứng viên và kho nhân tài Odoo",
        order: 66,
        icon: "user-plus",
        aliases: "tuyen dung odoo recruitment talent pool ung vien",
    },
    "spreadsheet_dashboard.spreadsheet_dashboard_menu_root": {
        label: "Bảng tổng hợp số liệu",
        hint: "Bảng dữ liệu và biểu đồ tổng hợp",
        order: 70,
        icon: "grid-four",
        aliases: "bang tong hop so lieu dashboards dashboard spreadsheet",
    },
    "account.menu_finance": {
        label: "Hóa đơn & Công nợ",
        hint: "Hóa đơn bán hàng, mua hàng và thanh toán",
        order: 80,
        icon: "receipt",
        aliases: "hoa don cong no invoicing invoice bill thanh toan ke toan",
    },
    "hr_timesheet.timesheet_menu_root": {
        label: "Giờ làm việc (Timesheet)",
        hint: "Nhật ký thời gian theo dự án và nhiệm vụ",
        order: 90,
        icon: "clock",
        aliases: "gio lam viec timesheets timesheet nhat ky thoi gian",
    },
    "hr_expense.menu_hr_expense_root": {
        label: "Chi phí & Hoàn ứng",
        hint: "Đề nghị chi phí và hoàn ứng nhân viên",
        order: 110,
        icon: "wallet",
        aliases: "chi phi hoan ung expenses expense",
    },
    "utm.menu_link_tracker_root": {
        label: "Theo dõi liên kết (UTM)",
        hint: "Chiến dịch, nguồn và phương tiện liên kết",
        order: 120,
        icon: "link",
        aliases: "trinh theo doi lien ket utm link tracker chien dich",
    },
};

/**
 * Return the unified TANPHAT ONE Vietnamese display label for a menu/app node.
 */
export function resolveAppDisplayLabel(app) {
    if (!app) {
        return "";
    }
    if (app.xmlid === HOME_MENU_XMLID) {
        return "Trang chủ";
    }
    const meta = app.xmlid && APP_LABELS[app.xmlid];
    if (meta?.label) {
        return meta.label;
    }
    return app.name || app.label || "";
}

export function resolveSwitcherIcon(item) {
    if (!item) {
        return "";
    }
    if (typeof item.switcherIcon === "string" && item.switcherIcon) {
        return item.switcherIcon;
    }
    if (typeof item.svgIcon === "string" && item.svgIcon) {
        return item.svgIcon;
    }
    if (typeof item.icon === "string" && item.icon) {
        return item.icon;
    }
    const meta = item.xmlid && APP_LABELS[item.xmlid];
    if (meta?.icon) {
        return meta.icon;
    }
    return "";
}

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
        key: "accounting",
        group: "departments",
        order: 50,
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
        key: "tadic",
        group: "departments",
        order: 55,
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
        key: "hr",
        group: "hr",
        order: 10,
        name: "Quản lý nhân sự",
        description: "Hồ sơ nhân viên, tổ chức và năng lực",
        status: "Đang hoạt động",
        badgeKind: "active",
        icon: "users",
        xmlid: "tp_hr_workspace.menu_hr",
        aliases: "nhan su tp hr quan ly nhan su ho so nhan vien to chuc nang luc",
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
    {
        key: "reporting",
        group: "reporting",
        order: 10,
        requiresMenu: true,
        name: "Báo cáo",
        description: "Báo cáo cá nhân, phòng ban và công ty",
        status: "Đang hoạt động",
        badgeKind: "active",
        icon: "bar-chart",
        xmlid: "tp_reporting.menu_root",
        aliases: "bao cao ke hoach chi tieu reporting",
    },
    {
        key: "governance",
        group: "reporting",
        order: 30,
        requiresMenu: true,
        name: "Điều hành lãnh đạo",
        description: "Tổng quan điều hành, WBS/CPM và Hồ sơ dự án NAS",
        status: "Đang hoạt động",
        badgeKind: "active",
        icon: "compass",
        xmlid: "tp_enterprise_governance.menu_governance_root",
        aliases: "dieu hanh lanh dao dieu hanh du an wbs cpm ho so nas governance",
    },
    {
        key: "digital_office",
        group: "reporting",
        order: 40,
        requiresMenu: true,
        name: "Văn phòng số",
        description: "Thông báo nội bộ và biên bản họp",
        status: "Đang hoạt động",
        badgeKind: "active",
        icon: "file-text",
        xmlid: "tp_digital_office.menu_digital_office_root",
        aliases: "van phong so thong bao noi bo bien ban hop digital office",
    },
    {
        key: "maintenance",
        group: "warehouse",
        order: 20,
        requiresMenu: true,
        name: "Bảo dưỡng thiết bị",
        description: "Yêu cầu bảo trì và theo dõi thiết bị",
        status: "Đang hoạt động",
        badgeKind: "active",
        icon: "wrench",
        xmlid: "maintenance.menu_maintenance_title",
        aliases: "bao duong bao tri maintenance thiet bi oee",
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
 * Build the Employee Quick Grid ("Ứng dụng của bạn", UI-HOME-007 Section 5)
 * strictly from authorized menu entries for the logged-in employee.
 * - Never includes unauthorized department placeholders or system administration menus.
 * - Packs neatly without blank filler cells; caps shortcuts at 9 + "Tất cả ứng dụng" = 10 tiles.
 */
export function buildEmployeeQuickGrid(catalog, { includeAllApps = true } = {}) {
    const entries = catalog?.entries || [];
    const userApps = catalog?.userApps || [];
    const byKey = new Map();
    const byXmlid = new Map();

    for (const entry of entries) {
        if (entry.placeholderOnly && !entry.menu) {
            continue;
        }
        if (entry.key) {
            byKey.set(entry.key, entry);
        }
        if (entry.xmlid) {
            byXmlid.set(entry.xmlid, entry);
        }
    }
    for (const app of userApps) {
        if (app.group === "system") {
            continue;
        }
        if (app.xmlid && !byXmlid.has(app.xmlid)) {
            byXmlid.set(app.xmlid, app);
        }
    }

    const shortcuts = [];
    const usedMenuIds = new Set();
    const usedKeys = new Set();
    const maxShortcutSlots = includeAllApps ? 9 : 10;

    for (const slot of EMPLOYEE_GRID_SLOTS) {
        if (shortcuts.length >= maxShortcutSlots) {
            break;
        }
        const match =
            (slot.entryKey && byKey.get(slot.entryKey)) ||
            (slot.xmlid && byXmlid.get(slot.xmlid)) ||
            null;
        if (!match || !match.menu?.actionID) {
            continue;
        }
        const menuId = match.menu.id;
        if ((menuId && usedMenuIds.has(menuId)) || (match.key && usedKeys.has(match.key))) {
            continue;
        }
        if (menuId) {
            usedMenuIds.add(menuId);
        }
        if (match.key) {
            usedKeys.add(match.key);
        }
        const gridLabel = slot.gridLabel || match.name || match.label;
        shortcuts.push({
            ...match,
            gridLabel,
            gridIcon: slot.gridIcon || match.svgIcon || match.icon || "grid-four",
            palette: resolveShortcutPalette({ ...match, ...slot }),
        });
    }

    const hasAnyPermittedApp = entries.length > 0 || userApps.length > 0;
    if (includeAllApps && hasAnyPermittedApp) {
        shortcuts.push({
            ...allAppsEntry(),
            key: ALL_APPS_KEY,
            kind: "panel",
            name: "Tất cả ứng dụng",
            label: "Tất cả ứng dụng",
            gridLabel: "Tất cả ứng dụng",
            gridIcon: "grid-four",
            palette: "all-apps",
        });
    }

    return shortcuts;
}

/**
 * Build the Quick Access Grid for either Admin Mode ("Ứng dụng theo phòng ban", 10 canonical slots)
 * or Employee Mode ("Ứng dụng của bạn", authorized daily apps & workspaces).
 */
export function buildQuickGrid(catalog, { includeAllApps = true, homeMode = null } = {}) {
    const mode = homeMode || (catalog?.isAdmin || catalog?.isDelegated ? "admin" : "employee");
    if (mode === "employee") {
        return buildEmployeeQuickGrid(catalog, { includeAllApps });
    }

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
                    palette: resolveShortcutPalette(slot),
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
            palette: resolveShortcutPalette({ ...match, ...slot }),
        });
    }

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
                palette: resolveShortcutPalette(entry),
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

function enrichSwitcherItem(item) {
    return {
        ...item,
        palette: resolveShortcutPalette(item),
        switcherIcon: resolveSwitcherIcon(item),
    };
}

/**
 * Build grouped sections for the unified TANPHAT ONE App Switcher (9-dot Navbar Menu,
 * Home Navigation Menu, "Tất cả ứng dụng", and Mobile App Sheet).
 * Preserves all canonical business groups + extra permitted apps + admin-only system tools.
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
            tabLabel: s.tabLabel || s.label,
            items: s.tiles.map(enrichSwitcherItem),
        });
    }

    const extraApps = filterTiles(catalog.extraUserApps || [], query);
    if (extraApps.length) {
        groups.push({
            key: "other_apps",
            label: "Ứng dụng khác được cấp",
            tabLabel: "Ứng dụng khác",
            items: extraApps.map(enrichSwitcherItem),
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
                tabLabel: "Quản trị",
                items: sysTools.map(enrichSwitcherItem),
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
export function buildCatalog(
    rootTree,
    { debug = "", isSystem = false, isDelegated = false, homeMode = null } = {}
) {
    const apps = buildTiles(rootTree, debug);
    const modulesCatalog = buildAdminCatalog(rootTree, {
        debug,
        isSystem: Boolean(isSystem),
        isDelegated: Boolean(isDelegated),
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

    const effectiveMode = homeMode || (isSystem || isDelegated ? "admin" : "employee");
    const partialCatalog = {
        isAdmin: Boolean(isSystem),
        isDelegated: Boolean(isDelegated),
        homeMode: effectiveMode,
        admin: modulesCatalog,
        tools,
        entries,
        home: apps.filter((tile) => tile.group === "workspace" || tile.group === "personal"),
        system,
        all: isSystem ? apps : [],
        userApps: isSystem ? apps : nonSystemApps,
        extraUserApps,
        otherApps: apps.filter((tile) => !shownMenuIds.has(tile.menu?.id)).length,
    };

    return {
        ...partialCatalog,
        quickGrid: buildQuickGrid(partialCatalog, { homeMode: effectiveMode }),
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
