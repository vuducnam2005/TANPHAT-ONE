// Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
/**
 * Business Route Registry for TANPHAT ONE webclient (SYSTEM-URL-001).
 * Mirrors `tp_branding/brand_routes.py`.
 */

import { session } from "@web/session";

export const ROUTE_DEFINITIONS = [
    {
        url: "/app/tai-khoan/bao-mat",
        action_xml_id: "tp_web_login.action_account_security",
        action_tag: "tp_web_login.account_security",
        native_slug: "tai-khoan-bao-mat",
        name: "Tài khoản & Bảo mật",
        module: "tp_web_login",
        has_detail: false,
        aliases: [],
    },
    // 1. Trang chủ
    {
        url: "/app/trang-chu",
        action_xml_id: "tp_web_home.action_home",
        action_tag: "tp_web_home.home",
        native_slug: "tp-home",
        name: "Trang chủ",
        module: "tp_web_home",
        has_detail: false,
        aliases: ["/app/tp-home"],
    },

    // 2. Nhân sự (nhan-su)
    {
        url: "/app/nhan-su/tong-quan",
        action_xml_id: "tp_hr_workspace.action_overview",
        action_tag: "tp_hr_workspace.overview",
        native_slug: "tp-hr",
        name: "Tổng quan nhân sự",
        module: "tp_hr_workspace",
        has_detail: false,
        aliases: ["/app/tp-hr", "/app/tp-hr-tong-quan"],
    },
    {
        url: "/app/nhan-su/nhan-vien",
        action_xml_id: "tp_hr_workspace.action_employees",
        model: "hr.employee",
        name: "Danh sách nhân viên",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/nhan-su/phong-ban",
        action_xml_id: "tp_hr_workspace.action_departments",
        model: "hr.department",
        name: "Phòng ban và đơn vị",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/nhan-su/chuc-vu",
        action_xml_id: "tp_hr_workspace.action_jobs",
        model: "hr.job",
        name: "Chức vụ",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/nhan-su/ho-so-can-bo-sung",
        action_xml_id: "tp_hr_workspace.action_missing",
        model: "hr.employee",
        name: "Hồ sơ cần bổ sung",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/nhan-su/luu-tru",
        action_xml_id: "tp_hr_workspace.action_archived",
        model: "hr.employee",
        name: "Lưu trữ nhân viên",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/nhan-su/ho-so-cua-toi",
        action_xml_id: "tp_hr_workspace.action_my_profile",
        action_tag: "tp_hr_workspace.my_profile",
        native_slug: "my-profile",
        name: "Hồ sơ của tôi",
        module: "tp_hr_workspace",
        has_detail: false,
        aliases: ["/app/my-profile"],
    },
    {
        url: "/app/nhan-su/phong-ban-cua-toi",
        action_xml_id: "tp_hr_workspace.action_department_workspace",
        action_tag: "tp_department_workspace",
        name: "Phòng ban của tôi",
        module: "tp_hr_workspace",
        has_detail: false,
        aliases: [],
    },
    {
        url: "/app/nhan-su/nhat-ky-ho-so",
        action_xml_id: "tp_hr_workspace.action_employee_audit",
        model: "tp.hr.employee.audit",
        name: "Nhật ký xóa hồ sơ và sửa mã",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: [],
    },

    // 3. Chấm công (cham-cong; legacy /app/nhan-su/cham-cong/... kept as aliases)
    {
        url: "/app/cham-cong/tong-quan",
        action_xml_id: "tp_hr_attendance.action_dashboard",
        action_tag: "tp_hr_attendance.dashboard",
        native_slug: "cham-cong",
        name: "Tổng quan chấm công",
        module: "tp_hr_attendance",
        has_detail: false,
        aliases: ["/app/cham-cong", "/app/nhan-su/cham-cong/tong-quan", "/app/nhan-su/cham-cong"],
    },
    {
        url: "/app/cham-cong/cua-toi",
        action_xml_id: "tp_hr_attendance.action_mine",
        action_tag: "tp_hr_attendance.mine",
        native_slug: "cong-cua-toi",
        name: "Công của tôi",
        module: "tp_hr_attendance",
        has_detail: false,
        aliases: ["/app/cong-cua-toi", "/app/nhan-su/cham-cong/cua-toi"],
    },
    {
        url: "/app/cham-cong/quan-tri",
        action_xml_id: "tp_hr_attendance.action_sources",
        action_tag: "tp_hr_attendance.sources",
        native_slug: "nguon-cham-cong",
        name: "Tổng quan quản trị chấm công",
        module: "tp_hr_attendance",
        has_detail: false,
        aliases: ["/app/nguon-cham-cong", "/app/nhan-su/cham-cong/quan-tri", "/app/nhan-su/cham-cong/nguon-du-lieu"],
    },
    {
        url: "/app/cham-cong/cau-hinh",
        action_xml_id: "tp_hr_attendance.action_enti_config",
        model: "tp.hr.attendance.enti.config.wizard",
        name: "Cấu hình kết nối chấm công",
        module: "tp_hr_attendance",
        has_detail: false,
        aliases: ["/app/nhan-su/cham-cong/cau-hinh"],
    },
    {
        url: "/app/cham-cong/doi-chieu-nhan-vien",
        action_xml_id: "tp_hr_attendance.action_enti_mapping",
        model: "tp.hr.attendance.enti.mapping",
        name: "Đối chiếu nhân viên chấm công",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/nhan-su/cham-cong/doi-chieu-nhan-vien"],
    },
    {
        url: "/app/cham-cong/nhat-ky-dong-bo",
        action_xml_id: "tp_hr_attendance.action_enti_logs",
        model: "tp.hr.attendance.enti.sync.log",
        name: "Nhật ký đồng bộ chấm công",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/nhan-su/cham-cong/nhat-ky-dong-bo"],
    },
    {
        url: "/app/cham-cong/dong-bo-anh",
        action_xml_id: "tp_hr_attendance.action_enti_employee_images",
        model: "tp.hr.attendance.enti.employee.image",
        name: "Nhật ký đồng bộ ảnh hồ sơ ENTI",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/nhan-su/cham-cong/dong-bo-anh"],
    },
    {
        url: "/app/cham-cong/dieu-chinh",
        action_xml_id: "tp_hr_attendance.action_review",
        model: "tp.hr.attendance.correction",
        name: "Xử lý điều chỉnh công",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/nhan-su/cham-cong/dieu-chinh"],
    },
    {
        url: "/app/cham-cong/yeu-cau-cua-toi",
        action_xml_id: "tp_hr_attendance.action_my_requests",
        name: "Yêu cầu điều chỉnh của tôi",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/nhan-su/cham-cong/yeu-cau-cua-toi"],
    },
    {
        url: "/app/cham-cong/chot-ky",
        action_xml_id: "tp_hr_attendance.action_periods",
        model: "tp.hr.attendance.period",
        name: "Chốt kỳ công",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/nhan-su/cham-cong/chot-ky"],
    },
    {
        url: "/app/cham-cong/bang-cong",
        action_xml_id: "tp_hr_attendance.action_days",
        model: "tp.hr.attendance.day",
        name: "Bảng ngày công",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/nhan-su/cham-cong/bang-cong"],
    },
    {
        url: "/app/cham-cong/di-muon",
        action_xml_id: "tp_hr_attendance.action_late",
        model: "tp.hr.attendance.late",
        name: "Tổng đi muộn theo kỳ",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/nhan-su/cham-cong/di-muon"],
    },
    {
        url: "/app/cham-cong/quy-tac",
        action_xml_id: "tp_hr_attendance.action_rules",
        model: "tp.hr.attendance.rule",
        name: "Quy tắc công",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/nhan-su/cham-cong/quy-tac"],
    },
    {
        url: "/app/cham-cong/ma-may",
        action_xml_id: "tp_hr_attendance.action_codes",
        model: "tp.hr.attendance.code",
        name: "Mã máy chấm công",
        module: "tp_hr_attendance",
        has_detail: false,
        aliases: ["/app/nhan-su/cham-cong/ma-may"],
    },
    {
        url: "/app/cham-cong/phan-cong",
        action_xml_id: "tp_hr_attendance.action_assignments",
        model: "tp.hr.attendance.assignment",
        name: "Phân công xử lý công",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/nhan-su/cham-cong/phan-cong"],
    },
    {
        url: "/app/cham-cong/nhat-ky-cham-cong",
        action_xml_id: "tp_hr_attendance.action_logs",
        model: "tp.hr.attendance.log",
        name: "Nhật ký chấm công",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/nhan-su/cham-cong/nhat-ky-cham-cong"],
    },

    // 4. Kế hoạch Kinh doanh (khkd)
    {
        url: "/app/khkd/tong-quan",
        action_xml_id: "tp_kd_workspace.action_overview",
        model: "tp.kd.overview",
        name: "Tổng quan KH-KD",
        module: "tp_kd_workspace",
        has_detail: false,
        aliases: [],
    },
    {
        url: "/app/khkd/du-an-tiem-nang",
        action_xml_id: "tp_kd_workspace.action_opportunities",
        model: "crm.lead",
        name: "Dự án tiềm năng",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/khkd/dau-thau",
        action_xml_id: "tp_kd_workspace.action_packages",
        model: "tp.bid.package",
        name: "Đấu thầu",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/khkd/ho-so-thau",
        action_xml_id: "tp_kd_workspace.action_reconcile",
        model: "crm.lead",
        name: "Hồ sơ thầu",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/khkd/hop-dong",
        action_xml_id: "tp_contract.action_tp_contracts_list",
        model: "tp.contract",
        name: "Hợp đồng",
        module: "tp_contract",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/khkd/quan-ly-du-an",
        action_xml_id: "tp_kd_workspace.action_management",
        model: "tp.project.perspective",
        name: "Quản lý dự án",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/khkd/quan-tri-du-an",
        action_xml_id: "tp_kd_workspace.action_governance",
        model: "tp.project.perspective",
        name: "Quản trị dự án",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/khkd/bao-cao",
        action_xml_id: "tp_kd_workspace.action_reports",
        model: "tp.kd.report.center",
        name: "Báo cáo KH-KD",
        module: "tp_kd_workspace",
        has_detail: false,
        aliases: [],
    },
    {
        url: "/app/khkd/wbs",
        action_xml_id: "tp_kd_workspace.action_wbs",
        model: "project.task",
        name: "Hạng mục / WBS",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: [],
    },

    // 5. Thiết bị (thiet-bi)
    {
        url: "/app/thiet-bi/tong-quan",
        action_xml_id: "tp_equipment.action_dashboard",
        action_tag: "tp_equipment.dashboard",
        native_slug: "tong-quan-thiet-bi",
        name: "Tổng quan thiết bị",
        module: "tp_equipment",
        has_detail: false,
        aliases: ["/app/tong-quan-thiet-bi"],
    },
    {
        url: "/app/thiet-bi/danh-sach",
        action_xml_id: "tp_equipment.action_equipment",
        model: "maintenance.equipment",
        native_slug: "kho-thiet-bi",
        name: "Danh sách thiết bị",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/kho-thiet-bi"],
    },
    {
        url: "/app/thiet-bi/ton-kho",
        action_xml_id: "tp_equipment.action_equipment_stock",
        model: "maintenance.equipment",
        native_slug: "ton-kho-thiet-bi",
        name: "Thiết bị tồn kho",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/ton-kho-thiet-bi"],
    },
    {
        url: "/app/thiet-bi/de-xuat",
        action_xml_id: "tp_equipment.action_proposals",
        model: "tp.equipment.proposal",
        native_slug: "de-xuat-thiet-bi",
        name: "Yêu cầu đề xuất thiết bị",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/de-xuat-thiet-bi"],
    },
    {
        url: "/app/thiet-bi/phieu-ban-giao",
        action_xml_id: "tp_equipment.action_moves",
        model: "tp.equipment.move",
        native_slug: "phieu-thiet-bi",
        name: "Phiếu bàn giao / thu hồi",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/phieu-thiet-bi"],
    },
    {
        url: "/app/thiet-bi/sua-chua",
        action_xml_id: "tp_equipment.action_repairs",
        model: "maintenance.request",
        native_slug: "sua-chua-thiet-bi",
        name: "Sửa chữa / bảo trì",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/sua-chua-thiet-bi"],
    },
    {
        url: "/app/thiet-bi/kiem-ke",
        action_xml_id: "tp_equipment.action_inventories",
        model: "tp.equipment.inventory",
        native_slug: "kiem-ke-thiet-bi",
        name: "Kiểm kê thiết bị",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/kiem-ke-thiet-bi"],
    },

    // 6. Báo cáo (bao-cao)
    {
        url: "/app/bao-cao/tong-quan",
        action_xml_id: "tp_reporting.action_dashboard",
        action_tag: "tp_reporting.dashboard",
        native_slug: "bao-cao-tong-quan",
        name: "Tổng quan báo cáo",
        module: "tp_reporting",
        has_detail: false,
        aliases: ["/app/bao-cao-tong-quan"],
    },
    {
        url: "/app/bao-cao/muc-tieu",
        action_xml_id: "tp_reporting.action_plans",
        model: "tp.report.plan",
        native_slug: "bao-cao-plans",
        name: "Mục tiêu và kế hoạch",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-plans"],
    },
    {
        url: "/app/bao-cao/ca-nhan",
        action_xml_id: "tp_reporting.action_personal",
        model: "tp.report.document",
        native_slug: "bao-cao-personal",
        name: "Báo cáo cá nhân",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-personal"],
    },
    {
        url: "/app/bao-cao/phong-ban",
        action_xml_id: "tp_reporting.action_department",
        model: "tp.report.document",
        native_slug: "bao-cao-department",
        name: "Báo cáo phòng ban",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-department"],
    },
    {
        url: "/app/bao-cao/cong-ty",
        action_xml_id: "tp_reporting.action_company",
        model: "tp.report.document",
        native_slug: "bao-cao-company",
        name: "Báo cáo công ty",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-company"],
    },
    {
        url: "/app/bao-cao/cho-ra-soat",
        action_xml_id: "tp_reporting.action_my_review",
        model: "tp.report.document",
        native_slug: "bao-cao-cho-ra-soat",
        name: "Chờ tôi rà soát",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-cho-ra-soat"],
    },

    // 7. Yêu cầu phê duyệt (de-nghi)
    {
        url: "/app/de-nghi/tong-quan",
        action_xml_id: "tp_request.action_overview",
        action_tag: "tp_request.dashboard",
        native_slug: "de-nghi-tong-quan",
        name: "Tổng quan Yêu cầu phê duyệt",
        module: "tp_request",
        has_detail: false,
        aliases: ["/app/de-nghi", "/app/de-nghi-tong-quan"],
    },
    {
        url: "/app/de-nghi/cua-toi",
        action_xml_id: "tp_request.action_mine",
        native_slug: "de-nghi-cua-toi",
        name: "Đề nghị của tôi",
        module: "tp_request",
        has_detail: true,
        aliases: ["/app/de-nghi-cua-toi"],
    },
    {
        url: "/app/de-nghi/can-duyet",
        action_xml_id: "tp_request.action_to_approve",
        native_slug: "de-nghi-can-duyet",
        name: "Cần tôi duyệt",
        module: "tp_request",
        has_detail: true,
        aliases: ["/app/de-nghi-can-duyet"],
    },
    {
        url: "/app/de-nghi/can-thuc-hien",
        action_xml_id: "tp_request.action_to_execute",
        native_slug: "de-nghi-can-thuc-hien",
        name: "Cần thực hiện",
        module: "tp_request",
        has_detail: true,
        aliases: ["/app/de-nghi-can-thuc-hien"],
    },
    {
        url: "/app/de-nghi/theo-doi",
        action_xml_id: "tp_request.action_watching",
        native_slug: "de-nghi-theo-doi",
        name: "Theo dõi đề nghị",
        module: "tp_request",
        has_detail: true,
        aliases: ["/app/de-nghi-theo-doi"],
    },
    {
        url: "/app/de-nghi/quan-tri",
        action_xml_id: "tp_request.action_admin",
        action_tag: "tp_request.admin",
        native_slug: "de-nghi-quan-tri",
        name: "Quản trị Yêu cầu phê duyệt",
        module: "tp_request",
        has_detail: false,
        aliases: ["/app/de-nghi-quan-tri"],
    },
    {
        url: "/app/de-nghi/ho-so",
        action_xml_id: "tp_request.action_detail",
        action_tag: "tp_request.detail",
        native_slug: "de-nghi-ho-so",
        name: "Chi tiết hồ sơ đề nghị",
        module: "tp_request",
        has_detail: true,
        aliases: ["/app/de-nghi-ho-so"],
    },

    // 8. Công cụ cá nhân (ca-nhan)
    {
        url: "/app/ca-nhan/cong-viec",
        action_xml_id: "tp_personal_tools.action_personal_todo",
        action_tag: "tp_personal_tools.todo_workspace",
        native_slug: "cong-viec-ca-nhan",
        name: "Việc cá nhân",
        module: "tp_personal_tools",
        has_detail: true,
        aliases: ["/app/to-do", "/app/cong-viec-ca-nhan"],
    },
    {
        url: "/app/ca-nhan/lich-lam-viec",
        action_xml_id: "calendar.action_calendar_event",
        model: "calendar.event",
        native_slug: "calendar",
        name: "Lịch làm việc",
        module: "calendar",
        has_detail: true,
        aliases: ["/app/calendar", "/app/lich-lam-viec"],
    },
    {
        url: "/app/ca-nhan/trao-doi",
        action_xml_id: "mail.action_discuss",
        action_tag: "mail.action_discuss",
        native_slug: "discuss",
        name: "Trao đổi",
        module: "mail",
        has_detail: true,
        aliases: ["/app/discuss", "/app/trao-doi"],
    },

    // 9. Quản trị (quan-tri)
    {
        url: "/app/quan-tri/cai-dat",
        action_xml_id: "base.action_server_action",
        name: "Cài đặt hệ thống",
        module: "base",
        has_detail: false,
        aliases: [],
    },
    {
        url: "/app/quan-tri/tai-khoan",
        action_xml_id: "base.action_res_users",
        model: "res.users",
        native_slug: "users",
        name: "Người dùng / Tài khoản",
        module: "base",
        has_detail: true,
        aliases: ["/app/users"],
    },
    {
        url: "/app/quan-tri/ung-dung",
        action_xml_id: "base.open_module_tree",
        model: "ir.module.module",
        native_slug: "apps",
        name: "Ứng dụng",
        module: "base",
        has_detail: true,
        aliases: ["/app/apps"],
    },
    {
        url: "/app/quan-tri/cong-ty",
        action_xml_id: "base.action_res_company_form",
        model: "res.company",
        native_slug: "companies",
        name: "Công ty",
        module: "base",
        has_detail: true,
        aliases: ["/app/companies"],
    },

    // 10. Văn phòng số (van-phong-so)
    {
        url: "/app/van-phong-so/thong-bao",
        action_xml_id: "tp_digital_office.action_announcements",
        action_tag: "tp_digital_office.announcements",
        native_slug: "thong-bao-noi-bo",
        name: "Thông báo nội bộ",
        module: "tp_digital_office",
        has_detail: false,
        aliases: ["/app/van-phong-so", "/app/thong-bao-noi-bo"],
    },
    {
        url: "/app/van-phong-so/bien-ban-hop",
        action_xml_id: "tp_digital_office.action_meeting_minutes",
        action_tag: "tp_digital_office.meeting_minutes",
        native_slug: "bien-ban-hop",
        name: "Biên bản họp",
        module: "tp_digital_office",
        has_detail: false,
        aliases: ["/app/bien-ban-hop"],
    },
];

// Runtime maps for dynamic action ID resolution
const dynamicActionIdMap = new Map(); // id -> xml_id
const dynamicXmlIdMap = new Map(); // xml_id -> id

/**
 * Register a known action ID <-> XML ID pair (e.g. from /web/action/load or session).
 */
export function registerActionId(id, xmlId) {
    if (typeof id === "number" && typeof xmlId === "string" && xmlId.includes(".")) {
        dynamicActionIdMap.set(id, xmlId);
        dynamicXmlIdMap.set(xmlId, id);
    }
}

/**
 * Read session_info mapping if available.
 */
function syncFromSession() {
    const info =
        session?.tp_action_routes ||
        window.odoo?.session_info?.tp_action_routes ||
        window.odoo?.__session_info__?.tp_action_routes;
    if (info) {
        if (info.id_to_xml) {
            for (const [idStr, xmlId] of Object.entries(info.id_to_xml)) {
                registerActionId(parseInt(idStr, 10), xmlId);
            }
        }
        if (info.xml_to_id) {
            for (const [xmlId, id] of Object.entries(info.xml_to_id)) {
                registerActionId(id, xmlId);
            }
        }
    }
}

/**
 * Look up XML ID for a numeric action ID.
 */
export function getXmlIdByActionId(id) {
    if (typeof id !== "number") {
        return null;
    }
    syncFromSession();
    return dynamicActionIdMap.get(id) || null;
}

/**
 * Look up numeric action ID for an XML ID.
 */
export function getActionIdByXmlId(xmlId) {
    if (!xmlId) {
        return null;
    }
    syncFromSession();
    return dynamicXmlIdMap.get(xmlId) || null;
}

/**
 * Find route matching an action identifier (numeric ID, XML ID, tag, native slug, or action-ID).
 */
export function findRouteByAction(identifier) {
    if (!identifier) {
        return null;
    }
    syncFromSession();

    let target = identifier;
    if (typeof target === "string" && target.startsWith("action-")) {
        const raw = target.slice(7);
        target = isNaN(raw) ? raw : parseInt(raw);
    }

    // 1. If numeric ID, resolve to XML ID
    let xmlId = null;
    if (typeof target === "number") {
        xmlId = dynamicActionIdMap.get(target);
    } else if (typeof target === "string" && target.includes(".")) {
        xmlId = target;
    }

    if (xmlId) {
        for (const r of ROUTE_DEFINITIONS) {
            if (r.action_xml_id === xmlId) {
                return r;
            }
        }
    }

    // 2. String comparison: tag, native_slug, or alias path
    if (typeof target === "string") {
        for (const r of ROUTE_DEFINITIONS) {
            if (r.action_tag === target || r.native_slug === target) {
                return r;
            }
            if (r.url === `/app/${target}`) {
                return r;
            }
            for (const alias of r.aliases || []) {
                if (alias === `/app/${target}` || alias === target) {
                    return r;
                }
            }
        }
    }

    return null;
}

/**
 * Parse an incoming pathname under /app and match it against registered routes.
 * Handles exact routes, /<id> details, /tao-moi & /new, and aliases.
 *
 * @param {string} pathname
 * @returns {{ route: object|null, resId: number|string|null, isNew: boolean, canonicalUrl: string|null }}
 */
export function parseBrandedUrl(pathname) {
    if (!pathname || typeof pathname !== "string") {
        return { route: null, resId: null, isNew: false, canonicalUrl: null };
    }
    syncFromSession();

    let clean = pathname.replace(/\/+$/, "") || "/";

    // 1. Check exact match on route.url or aliases
    for (const r of ROUTE_DEFINITIONS) {
        if (r.url === clean) {
            return { route: r, resId: null, isNew: false, canonicalUrl: r.url };
        }
        for (const alias of r.aliases || []) {
            if (alias === clean) {
                return { route: r, resId: null, isNew: false, canonicalUrl: r.url };
            }
        }
    }

    // 2. Check suffix: /tao-moi, /new, or /<id>
    const parts = clean.split("/").filter(Boolean);
    if (parts.length >= 2) {
        const lastPart = parts.at(-1);
        const basePath = "/" + parts.slice(0, -1).join("/");

        let matchedRoute = null;
        for (const r of ROUTE_DEFINITIONS) {
            if (r.url === basePath) {
                matchedRoute = r;
                break;
            }
            for (const alias of r.aliases || []) {
                if (alias === basePath) {
                    matchedRoute = r;
                    break;
                }
            }
        }

        if (matchedRoute && matchedRoute.has_detail) {
            if (lastPart === "tao-moi" || lastPart === "new") {
                return {
                    route: matchedRoute,
                    resId: "new",
                    isNew: true,
                    canonicalUrl: `${matchedRoute.url}/tao-moi`,
                };
            }
            if (/^\d+$/.test(lastPart)) {
                const numericId = parseInt(lastPart, 10);
                return {
                    route: matchedRoute,
                    resId: numericId,
                    isNew: false,
                    canonicalUrl: `${matchedRoute.url}/${numericId}`,
                };
            }
        }
    }

    // 3. Backward compatibility: /app/action-<id>[/<resId>]
    const actionMatch = clean.match(/^\/app\/action-(\d+)(?:\/(new|tao-moi|\d+))?$/);
    if (actionMatch) {
        const actionNum = parseInt(actionMatch[1], 10);
        const subRes = actionMatch[2];
        const route = findRouteByAction(actionNum);
        if (route) {
            let resId = null;
            let isNew = false;
            let canonical = route.url;
            if (subRes === "new" || subRes === "tao-moi") {
                resId = "new";
                isNew = true;
                canonical += "/tao-moi";
            } else if (subRes && /^\d+$/.test(subRes)) {
                resId = parseInt(subRes, 10);
                canonical += `/${resId}`;
            }
            return { route, resId, isNew, canonicalUrl: canonical };
        }
    }

    return { route: null, resId: null, isNew: false, canonicalUrl: null };
}

/**
 * Build canonical business URL for a route and optional record / state.
 */
export function buildBrandedUrl(route, options = {}) {
    if (!route || !route.url) {
        return null;
    }
    const { resId, isNew } = options;
    if ((isNew || resId === "new") && route.has_detail) {
        return `${route.url}/tao-moi`;
    }
    if (typeof resId === "number" && route.has_detail) {
        return `${route.url}/${resId}`;
    }
    return route.url;
}
