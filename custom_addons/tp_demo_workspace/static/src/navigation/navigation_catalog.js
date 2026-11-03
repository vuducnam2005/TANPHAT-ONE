/** Labels enrich only nodes returned by the native, permission-filtered menu service. */
export const DEMO_APP_XMLID = "tp_demo_workspace.menu_demo_root";
const NS = "tp_demo_workspace.";

export const MODULES = [
    { key: "dashboard", group: "overview", label: "Điều hành doanh nghiệp", name: "TP Dashboard", icon: "bar_chart", description: "Xem tổng quan dự án, công việc và các mục cần chú ý.", menus: ["menu_demo_dashboard"], aliases: "tong quan dashboard" },
    { key: "projects", group: "delivery", label: "Dự án", name: "TP Projects", icon: "business", description: "Tra cứu dự án được giao và mở tổng quan từng dự án.", menus: ["menu_demo_projects", "menu_demo_project_overview"], aliases: "project du an" },
    { key: "survey", group: "delivery", label: "Khảo sát hiện trường", name: "TP Survey", icon: "location_on", description: "Xem mẫu kế hoạch khảo sát, vị trí và nhật ký hiện trường.", menus: ["menu_demo_survey"], illustrative: true, aliases: "survey khao sat" },
    { key: "design", group: "delivery", label: "Hồ sơ thiết kế", name: "TP Design", icon: "design_services", description: "Xem mẫu bộ bản vẽ, kiểm tra và bàn giao hồ sơ thiết kế.", menus: ["menu_demo_design"], illustrative: true, aliases: "design ban ve ho so" },
    { key: "tasks", group: "delivery", label: "Tiến độ và giao việc", name: "TP Tasks", icon: "task", description: "Theo dõi công việc, người phụ trách và thời hạn thực hiện.", menus: ["menu_demo_tasks"], aliases: "task cong viec tien do" },
    { key: "contracts", group: "records", label: "Hợp đồng", name: "TP Contracts", icon: "description", description: "Tra cứu hợp đồng, phiên bản và luồng rà soát hồ sơ.", menus: ["menu_demo_contracts", "menu_demo_revisions", "menu_demo_contract_flow"], aliases: "contract hop dong phien ban ra soat" },
    { key: "documents", group: "records", label: "Tài liệu và hồ sơ", name: "TP Documents", icon: "folder_open", description: "Mở tài liệu hợp đồng và tệp hồ sơ trong phạm vi được xem.", menus: ["menu_demo_documents"], aliases: "document ho so tai lieu tep" },
    { key: "crm", group: "business", label: "Cơ hội kinh doanh", name: "CRM", icon: "handshake", description: "Theo dõi cơ hội, khách hàng và giai đoạn phát triển dự án.", menus: ["menu_demo_crm"], aliases: "crm co hoi khach hang" },
    { key: "bid", group: "business", label: "Dự thầu", name: "Bid", icon: "work", description: "Xem mẫu gói thầu, hồ sơ dự thầu và thời hạn nộp.", menus: ["menu_demo_bid"], illustrative: true, aliases: "bid dau thau du thau goi thau" },
    { key: "hr", group: "resources", label: "Nhân sự", name: "TP HR", icon: "group", description: "Tra cứu danh bạ; năng lực và phân bổ là phần minh họa.", menus: ["menu_demo_employees", "menu_demo_staffing"], aliases: "hr nhan su nhan vien nang luc phan bo" },
    { key: "finance", group: "resources", label: "Tài chính và chi phí", name: "TP Finance", icon: "account_balance", description: "Đọc số tiền hợp đồng theo quyền; nghiệm thu và tiền thu chỉ minh họa.", menus: ["menu_demo_finance", "menu_demo_line_amounts"], aliases: "finance tai chinh chi phi so tien" },
    { key: "request", group: "request", label: "Đề nghị nội bộ", name: "Request", icon: "send", description: "Xem mẫu đề nghị. BASE vẫn là nơi phê duyệt chính thức.", menus: ["menu_demo_request"], illustrative: true, aliases: "request de nghi yeu cau base" },
];

export const GROUPS = [
    { key: "overview", label: "Tổng quan" },
    { key: "delivery", label: "Dự án & công việc" },
    { key: "records", label: "Hợp đồng & hồ sơ" },
    { key: "business", label: "Kinh doanh" },
    { key: "resources", label: "Nguồn lực" },
    { key: "request", label: "Đề nghị" },
];

const LEAF_NOTES = {
    menu_demo_survey: "Minh họa",
    menu_demo_design: "Minh họa",
    menu_demo_staffing: "Minh họa",
    menu_demo_bid: "Minh họa",
    menu_demo_request: "Minh họa · duyệt chính thức tại BASE",
    menu_demo_finance: "Số hợp đồng từ Odoo; nghiệm thu và tiền thu minh họa",
};

export function normalizeMenuSearch(value) {
    return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "")
        .replace(/[đĐ]/g, "d").toLowerCase().replace(/\s+/g, " ").trim();
}

export function buildCatalog(appTree) {
    if (appTree?.xmlid !== DEMO_APP_XMLID) {
        return [];
    }
    const visible = new Map();
    const visit = (menu) => {
        if (menu.actionID && !(menu.childrenTree || []).length) {
            visible.set(menu.xmlid, menu);
        }
        for (const child of menu.childrenTree || []) {
            visit(child);
        }
    };
    visit(appTree);
    const modules = MODULES.map((metadata) => {
        const leaves = metadata.menus.flatMap((id) => {
            const menu = visible.get(NS + id);
            return menu ? [{ menu, label: menu.name, note: LEAF_NOTES[id] || "" }] : [];
        });
        return { ...metadata, leaves };
    }).filter((item) => item.leaves.length);
    return GROUPS.map((group) => ({
        ...group,
        modules: modules.filter((item) => item.group === group.key),
    })).filter((group) => group.modules.length);
}

export function filterCatalog(catalog, query) {
    const words = normalizeMenuSearch(query).split(" ").filter(Boolean);
    if (!words.length) {
        return catalog;
    }
    return catalog.map((group) => ({
        ...group,
        modules: group.modules.flatMap((item) => {
            const moduleText = normalizeMenuSearch([item.label, item.name, item.description, item.aliases].join(" "));
            const leaves = item.leaves.filter((leaf) => {
                const text = moduleText + " " + normalizeMenuSearch(leaf.label + " " + leaf.note);
                return words.every((word) => text.includes(word));
            });
            return leaves.length ? [{ ...item, leaves }] : [];
        }),
    })).filter((group) => group.modules.length);
}

/** Read native action identity. Never dispatch a second action to synchronize selection. */
export function activeDestination(catalog, action) {
    const all = catalog.flatMap((group) => group.modules.flatMap((item) =>
        item.leaves.map((leaf) => ({ group: group.key, module: item.key, menu: leaf.menu }))));
    const match = all.find(({ menu }) => String(menu.actionID) === String(action?.id)) ||
        all.find(({ menu }) => action?.path && menu.actionPath === action.path);
    if (match) {
        return match;
    }
    // Native form links opened from the demo dashboard have no menu action id.
    const byModel = {
        "project.project": "projects", "project.task": "tasks", "tp.contract": "contracts",
        "tp.contract.revision": "contracts", "tp.contract.document": "documents",
        "tp.contract.line.amount": "finance", "hr.employee.public": "hr", "crm.lead": "crm",
    };
    return all.find((item) => item.module === byModel[action?.res_model]) || null;
}
