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
        url: "/app/nhan-su",
        action_xml_id: "tp_hr_workspace.action_hr_entry",
        native_slug: "nhan-su",
        name: "Nhân sự",
        module: "tp_hr_workspace",
        has_detail: false,
        aliases: [],
    },
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
        url: "/app/nhan-su/tong-quan-danh-ba",
        action_xml_id: "tp_hr_workspace.action_public_overview",
        native_slug: "tp-hr-directory",
        name: "Tổng quan danh bạ nhân sự",
        module: "tp_hr_workspace",
        has_detail: false,
        aliases: ["/app/tp-hr-directory"],
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
    {
        url: "/app/nhan-su/chua-co-tai-khoan",
        action_xml_id: "tp_hr_workspace.action_pending",
        model: "hr.employee",
        name: "Nhân viên chưa có tài khoản",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/nhan-su/noi-lam-viec",
        action_xml_id: "tp_hr_workspace.action_locations",
        model: "hr.work.location",
        name: "Nơi làm việc",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/nhan-su/so-do-quan-ly",
        action_xml_id: "tp_hr_workspace.action_hierarchy",
        model: "hr.employee",
        name: "Sơ đồ quản lý đã khai báo",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/nhan-su/nhap-doi-chieu",
        action_xml_id: "tp_hr_workspace.action_import",
        model: "tp.hr.import.batch",
        name: "Nhập và đối chiếu",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/nhan-su/nhan-nhan-vien",
        action_xml_id: "tp_hr_workspace.action_categories",
        model: "hr.employee.category",
        name: "Nhãn nhân viên",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/nhan-su/danh-ba",
        action_xml_id: "tp_hr_workspace.action_directory",
        model: "hr.employee.public",
        native_slug: "danh-ba",
        name: "Danh bạ nhân sự",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: ["/app/danh-ba"],
    },
    {
        url: "/app/nhan-su/danh-muc-ngan-hang",
        action_xml_id: "tp_hr_bank.action_tp_bank",
        model: "tp.bank",
        native_slug: "nhan-su-danh-muc-ngan-hang",
        name: "Danh mục ngân hàng",
        module: "tp_hr_bank",
        has_detail: true,
        aliases: ["/app/danh-muc-ngan-hang", "/app/nhan-su/ngan-hang", "/app/nhan-su-danh-muc-ngan-hang"],
    },
    {
        url: "/app/nhan-su/ho-so-hop-dong",
        action_xml_id: "tp_hr_workspace.action_contract_documents",
        model: "tp.hr.contract.document",
        native_slug: "nhan-su-ho-so-hop-dong",
        name: "Hồ sơ hợp đồng lao động",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: ["/app/nhan-su-ho-so-hop-dong"],
    },
    {
        url: "/app/nhan-su/loai-ky-nang",
        action_xml_id: "tp_hr_workspace.action_skill_types",
        model: "hr.skill.type",
        native_slug: "nhan-su-loai-ky-nang",
        name: "Loại kỹ năng và cấp độ",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: ["/app/nhan-su-loai-ky-nang"],
    },
    {
        url: "/app/nhan-su/loai-qua-trinh",
        action_xml_id: "tp_hr_workspace.action_resume_types",
        model: "hr.resume.line.type",
        native_slug: "nhan-su-loai-qua-trinh",
        name: "Loại hồ sơ năng lực",
        module: "tp_hr_workspace",
        has_detail: true,
        aliases: ["/app/nhan-su-loai-qua-trinh"],
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
        native_slug: "cham-cong-anh-enti",
        name: "Nhật ký đồng bộ ảnh hồ sơ ENTI",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/cham-cong-anh-enti", "/app/nhan-su/cham-cong/dong-bo-anh"],
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
        action_xml_id: "tp_hr_attendance.action_board",
        action_tag: "tp_hr_attendance.board",
        native_slug: "cham-cong-bang-cong",
        name: "Bảng chấm công",
        module: "tp_hr_attendance",
        has_detail: false,
        aliases: ["/app/bang-cong", "/app/cham-cong-bang-cong", "/app/nhan-su/cham-cong/bang-cong"],
    },
    {
        url: "/app/cham-cong/ngay-cong",
        action_xml_id: "tp_hr_attendance.action_days",
        model: "tp.hr.attendance.day",
        native_slug: "cham-cong-ngay-cong",
        name: "Bảng ngày công",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/ngay-cong", "/app/cham-cong-ngay-cong", "/app/nhan-su/cham-cong/ngay-cong"],
    },
    {
        url: "/app/cham-cong/lich-su-nguon",
        action_xml_id: "tp_hr_attendance.action_file_matrix",
        action_tag: "tp_hr_attendance.file_matrix",
        native_slug: "cham-cong-lich-su-nguon",
        name: "Bảng dữ liệu theo file",
        module: "tp_hr_attendance",
        has_detail: false,
        aliases: ["/app/bang-cong-theo-file", "/app/cham-cong-lich-su-nguon"],
    },
    {
        url: "/app/cham-cong/nhap-excel",
        action_xml_id: "tp_hr_attendance.action_import",
        model: "tp.hr.attendance.batch",
        native_slug: "cham-cong-nhap-excel",
        name: "Lịch sử nhập Excel chấm công",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/nhap-cong", "/app/cham-cong-nhap-excel"],
    },
    {
        url: "/app/cham-cong/dong-nhap-excel",
        action_xml_id: "tp_hr_attendance.action_import_lines",
        model: "tp.hr.attendance.line",
        native_slug: "cham-cong-dong-nhap-excel",
        name: "Dòng nhập dữ liệu công",
        module: "tp_hr_attendance",
        has_detail: false,
        aliases: ["/app/cham-cong-dong-nhap-excel"],
    },
    {
        url: "/app/cham-cong/ban-ghi-nguon",
        action_xml_id: "tp_hr_attendance.action_source_records",
        model: "tp.hr.attendance.source",
        native_slug: "cham-cong-ban-ghi-nguon",
        name: "Nguồn API máy chấm công",
        module: "tp_hr_attendance",
        has_detail: true,
        aliases: ["/app/cham-cong-ban-ghi-nguon"],
    },
    {
        url: "/app/cham-cong/su-kien-cham-cong",
        action_xml_id: "tp_hr_attendance.action_events",
        model: "tp.hr.attendance.event",
        native_slug: "cham-cong-su-kien-cham-cong",
        name: "Sự kiện thô từ API máy",
        module: "tp_hr_attendance",
        has_detail: false,
        aliases: ["/app/cham-cong-su-kien", "/app/cham-cong-su-kien-cham-cong"],
    },
    {
        url: "/app/cham-cong/di-muon",
        action_xml_id: "tp_hr_attendance.action_late",
        model: "tp.hr.attendance.late",
        name: "Tổng đi muộn theo kỳ",
        module: "tp_hr_attendance",
        has_detail: false,
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
        has_detail: false,
        aliases: ["/app/nhan-su/cham-cong/nhat-ky-cham-cong"],
    },

    // 4. Kế hoạch Kinh doanh (khkd) & Hợp đồng
    {
        url: "/app/khkd/tong-quan",
        action_xml_id: "tp_kd_workspace.action_overview",
        model: "tp.kd.overview",
        name: "Tổng quan KH-KD",
        module: "tp_kd_workspace",
        has_detail: false,
        aliases: ["/app/ke-hoach-kinh-doanh", "/app/khkd"],
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
        extra_action_xml_ids: ["tp_contract.action_tp_contracts"],
        model: "tp.contract",
        native_slug: "khkd-hop-dong",
        name: "Hợp đồng",
        module: "tp_contract",
        has_detail: true,
        aliases: ["/app/hop-dong", "/app/khkd-hop-dong"],
    },
    {
        url: "/app/khkd/phien-ban-hop-dong",
        action_xml_id: "tp_contract.action_tp_contract_revisions",
        model: "tp.contract.revision",
        native_slug: "khkd-phien-ban-hop-dong",
        name: "Phiên bản hợp đồng",
        module: "tp_contract",
        has_detail: true,
        aliases: ["/app/khkd-phien-ban-hop-dong"],
    },
    {
        url: "/app/khkd/tai-lieu-hop-dong",
        action_xml_id: "tp_contract.action_tp_contract_documents",
        model: "tp.contract.document",
        native_slug: "khkd-tai-lieu-hop-dong",
        name: "Tài liệu hợp đồng",
        module: "tp_contract",
        has_detail: true,
        aliases: ["/app/khkd-tai-lieu-hop-dong"],
    },
    {
        url: "/app/khkd/lich-su-hop-dong",
        action_xml_id: "tp_contract.action_tp_contract_audits",
        model: "tp.contract.audit",
        native_slug: "khkd-lich-su-hop-dong",
        name: "Lịch sử hợp đồng",
        module: "tp_contract",
        has_detail: true,
        aliases: ["/app/khkd-lich-su-hop-dong"],
    },
    {
        url: "/app/khkd/hang-muc-so-tien",
        action_xml_id: "tp_contract.action_tp_contract_line_amounts",
        model: "tp.contract.line.amount",
        native_slug: "khkd-hang-muc-so-tien",
        name: "Số tiền theo dòng",
        module: "tp_contract",
        has_detail: true,
        aliases: ["/app/khkd-hang-muc-so-tien"],
    },
    {
        url: "/app/khkd/danh-muc-hang-muc",
        action_xml_id: "tp_core.action_work_items",
        model: "tp.work.item",
        native_slug: "danh-muc-hang-muc",
        name: "Danh mục hạng mục công việc",
        module: "tp_core",
        has_detail: true,
        aliases: ["/app/danh-muc-hang-muc", "/app/du-an/danh-muc-cong-viec"],
    },
    {
        url: "/app/khkd/tai-lieu-ho-so",
        action_xml_id: "tp_kd_workspace.action_dossier_documents",
        model: "tp.kd.document",
        native_slug: "khkd-tai-lieu-ho-so",
        name: "Tài liệu hồ sơ",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: ["/app/khkd-tai-lieu-ho-so"],
    },
    {
        url: "/app/khkd/lich-su-cong-viec",
        action_xml_id: "tp_kd_workspace.action_task_updates",
        model: "tp.task.update",
        native_slug: "khkd-lich-su-cong-viec",
        name: "Lịch sử thực hiện công việc",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: ["/app/khkd-lich-su-cong-viec"],
    },
    {
        url: "/app/khkd/quan-ly-du-an",
        action_xml_id: "tp_kd_workspace.action_management",
        model: "tp.project.perspective",
        name: "Quản lý dự án",
        module: "tp_kd_workspace",
        has_detail: false,
        aliases: [],
    },
    {
        url: "/app/khkd/quan-tri-du-an",
        action_xml_id: "tp_kd_workspace.action_governance",
        model: "tp.project.perspective",
        name: "Quản trị dự án",
        module: "tp_kd_workspace",
        has_detail: false,
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
    {
        url: "/app/khkd/du-an",
        action_xml_id: "tp_kd_workspace.action_projects",
        model: "project.project",
        native_slug: "khkd-du-an",
        name: "Dự án KH-KD",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: ["/app/khkd-du-an"],
    },
    {
        url: "/app/khkd/cong-viec",
        action_xml_id: "tp_kd_workspace.action_tasks",
        model: "project.task",
        native_slug: "khkd-cong-viec",
        name: "Công việc và tiến độ",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: ["/app/khkd-cong-viec"],
    },
    {
        url: "/app/khkd/giao-khoan",
        action_xml_id: "tp_kd_workspace.action_allocations",
        model: "tp.allocation",
        name: "Giao khoán và thầu phụ",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/khkd/san-luong",
        action_xml_id: "tp_kd_workspace.action_productions",
        model: "tp.production",
        name: "Sản lượng theo kỳ",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/khkd/nghiem-thu",
        action_xml_id: "tp_kd_workspace.action_acceptances",
        model: "tp.acceptance",
        name: "Hồ sơ nghiệm thu",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/khkd/thanh-toan",
        action_xml_id: "tp_kd_workspace.action_payments",
        model: "tp.payment.request",
        name: "Đề nghị thanh toán",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/khkd/ke-hoach-dinh-ky",
        action_xml_id: "tp_kd_workspace.action_plans",
        model: "tp.periodic.plan",
        name: "Kế hoạch định kỳ",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/khkd/nghia-vu",
        action_xml_id: "tp_kd_workspace.action_obligations",
        model: "tp.obligation",
        name: "Nghĩa vụ và hồ sơ còn thiếu",
        module: "tp_kd_workspace",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/khkd/nang-luc-chung-chi",
        action_xml_id: "tp_kd_workspace.action_credentials",
        model: "tp.credential",
        name: "Hồ sơ năng lực và chứng chỉ",
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
        url: "/app/thiet-bi/quet-ma",
        action_xml_id: "tp_equipment.action_scan",
        action_tag: "tp_equipment.scan",
        native_slug: "thiet-bi-quet-ma",
        name: "Quét mã thiết bị",
        module: "tp_equipment",
        has_detail: false,
        aliases: ["/app/thiet-bi-quet-ma"],
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
        native_slug: "thiet-bi-ton-kho",
        name: "Thiết bị tồn kho",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/ton-kho-thiet-bi", "/app/thiet-bi-ton-kho"],
    },
    {
        url: "/app/thiet-bi/san-sang",
        action_xml_id: "tp_equipment.action_equipment_available",
        model: "maintenance.equipment",
        native_slug: "thiet-bi-san-sang",
        name: "Sẵn sàng cấp phát",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/thiet-bi-san-sang"],
    },
    {
        url: "/app/thiet-bi/dang-dung",
        action_xml_id: "tp_equipment.action_equipment_in_use",
        model: "maintenance.equipment",
        native_slug: "thiet-bi-dang-dung",
        name: "Đang sử dụng",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/thiet-bi-dang-dung"],
    },
    {
        url: "/app/thiet-bi/can-chu-y",
        action_xml_id: "tp_equipment.action_equipment_attention",
        model: "maintenance.equipment",
        native_slug: "thiet-bi-can-chu-y",
        name: "Cần xử lý",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/thiet-bi-can-chu-y"],
    },
    {
        url: "/app/thiet-bi/ho-so-nhap",
        action_xml_id: "tp_equipment.action_equipment_draft",
        model: "maintenance.equipment",
        native_slug: "thiet-bi-ho-so-nhap",
        name: "Hồ sơ nháp",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/thiet-bi-ho-so-nhap"],
    },
    {
        url: "/app/thiet-bi/ngung-quan-ly",
        action_xml_id: "tp_equipment.action_equipment_retired",
        model: "maintenance.equipment",
        native_slug: "thiet-bi-ngung-quan-ly",
        name: "Ngừng quản lý",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/thiet-bi-ngung-quan-ly"],
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
        url: "/app/thiet-bi/cho-ban-giao",
        action_xml_id: "tp_equipment.action_moves_pending",
        model: "tp.equipment.move",
        native_slug: "thiet-bi-cho-ban-giao",
        name: "Phiếu chờ bàn giao",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/thiet-bi-cho-ban-giao"],
    },
    {
        url: "/app/thiet-bi/dong-ban-giao",
        action_xml_id: "tp_equipment.action_move_lines",
        model: "tp.equipment.move.line",
        native_slug: "thiet-bi-dong-ban-giao",
        name: "Lịch sử bàn giao theo thiết bị",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/thiet-bi-dong-ban-giao"],
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
    {
        url: "/app/thiet-bi/dong-kiem-ke",
        action_xml_id: "tp_equipment.action_inventory_lines",
        model: "tp.equipment.inventory.line",
        native_slug: "thiet-bi-dong-kiem-ke",
        name: "Dòng kiểm kê thiết bị",
        module: "tp_equipment",
        has_detail: false,
        aliases: ["/app/thiet-bi-dong-kiem-ke"],
    },
    {
        url: "/app/thiet-bi/dung-chung",
        action_xml_id: "tp_equipment.action_equipment_shared",
        model: "maintenance.equipment",
        native_slug: "thiet-bi-dung-chung",
        name: "Thiết bị dùng chung",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/thiet-bi-dung-chung"],
    },
    {
        url: "/app/thiet-bi/tat-ca",
        action_xml_id: "tp_equipment.action_equipment_all_records",
        model: "maintenance.equipment",
        native_slug: "ho-so-thiet-bi",
        name: "Tất cả hồ sơ thiết bị",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/ho-so-thiet-bi"],
    },
    {
        url: "/app/thiet-bi/nhom-thiet-bi",
        action_xml_id: "tp_equipment.action_category",
        model: "maintenance.equipment.category",
        native_slug: "thiet-bi-nhom",
        name: "Phân loại thiết bị",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/thiet-bi/phan-loai", "/app/thiet-bi-nhom"],
    },
    {
        url: "/app/thiet-bi/vi-tri-dat-may",
        action_xml_id: "tp_equipment.action_location",
        model: "tp.equipment.location",
        native_slug: "thiet-bi-vi-tri",
        name: "Vị trí đặt thiết bị",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/thiet-bi/vi-tri", "/app/thiet-bi-vi-tri"],
    },
    {
        url: "/app/thiet-bi/nhap-du-lieu",
        action_xml_id: "tp_equipment.action_import",
        model: "tp.equipment.import.batch",
        native_slug: "nhap-du-lieu-thiet-bi",
        name: "Nhập nguồn thiết bị",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/nhap-du-lieu-thiet-bi"],
    },
    {
        url: "/app/thiet-bi/dong-nguon-cho",
        action_xml_id: "tp_equipment.action_import_pending",
        model: "tp.equipment.import.line",
        native_slug: "dong-nguon-thiet-bi-cho",
        name: "Dòng nguồn chờ bổ sung",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/dong-nguon-thiet-bi-cho"],
    },
    {
        url: "/app/thiet-bi/anh-xa-nguon",
        action_xml_id: "tp_equipment.action_import_alias",
        model: "tp.equipment.import.alias",
        native_slug: "anh-xa-nguon-thiet-bi",
        name: "Ánh xạ tên đã xác nhận",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/anh-xa-nguon-thiet-bi"],
    },
    {
        url: "/app/thiet-bi/phieu-nhap-kho",
        action_xml_id: "tp_equipment.action_receipts",
        model: "tp.equipment.receipt",
        native_slug: "phieu-nhap-thiet-bi",
        name: "Phiếu nhập kho thiết bị",
        module: "tp_equipment",
        has_detail: true,
        aliases: ["/app/phieu-nhap-thiet-bi"],
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
    {
        url: "/app/bao-cao/viec-can-xu-ly",
        action_xml_id: "tp_reporting.action_directives",
        model: "tp.report.directive",
        native_slug: "bao-cao-directives",
        name: "Việc cần xử lý",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-directives"],
    },
    {
        url: "/app/bao-cao/lich-nhac-han",
        action_xml_id: "tp_reporting.action_schedules",
        model: "tp.report.schedule",
        native_slug: "bao-cao-schedules",
        name: "Lịch và nhắc hạn",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-schedules"],
    },
    {
        url: "/app/bao-cao/nghia-vu",
        action_xml_id: "tp_reporting.action_obligations",
        model: "tp.report.obligation",
        native_slug: "bao-cao-obligations",
        name: "Nghĩa vụ báo cáo",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-obligations"],
    },
    {
        url: "/app/bao-cao/mau-bao-cao",
        action_xml_id: "tp_reporting.action_templates",
        model: "tp.report.template",
        native_slug: "bao-cao-templates",
        name: "Mẫu báo cáo",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-templates"],
    },
    {
        url: "/app/bao-cao/muc-trong-mau",
        action_xml_id: "tp_reporting.action_sections",
        model: "tp.report.section",
        native_slug: "bao-cao-sections",
        name: "Mục trong mẫu",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-sections"],
    },
    {
        url: "/app/bao-cao/muc-theo-mau",
        action_xml_id: "tp_reporting.action_template_sections",
        model: "tp.report.section",
        name: "Mục theo mẫu",
        module: "tp_reporting",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/bao-cao/noi-dung-muc",
        action_xml_id: "tp_reporting.action_section_contents",
        model: "tp.report.section.content",
        name: "Nội dung theo mẫu",
        module: "tp_reporting",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/bao-cao/phan-quyen",
        action_xml_id: "tp_reporting.action_assignments",
        model: "tp.report.assignment",
        native_slug: "bao-cao-assignments",
        name: "Phân quyền theo phạm vi",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-assignments"],
    },
    {
        url: "/app/bao-cao/chi-tieu",
        action_xml_id: "tp_reporting.action_metrics",
        model: "tp.report.metric",
        native_slug: "bao-cao-metrics",
        name: "Danh mục chỉ tiêu",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-metrics"],
    },
    {
        url: "/app/bao-cao/gia-tri-nguon",
        action_xml_id: "tp_reporting.action_values",
        model: "tp.report.value",
        native_slug: "bao-cao-values",
        name: "Giá trị có nguồn",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-values"],
    },
    {
        url: "/app/bao-cao/muc-uu-tien",
        action_xml_id: "tp_reporting.action_priorities",
        model: "tp.report.priority",
        native_slug: "bao-cao-muc-uu-tien",
        name: "Mức ưu tiên",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-muc-uu-tien"],
    },
    {
        url: "/app/bao-cao/muc-danh-gia",
        action_xml_id: "tp_reporting.action_ratings",
        model: "tp.report.rating",
        native_slug: "bao-cao-muc-danh-gia",
        name: "Mức đánh giá",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-muc-danh-gia"],
    },
    {
        url: "/app/bao-cao/dong-ket-qua",
        action_xml_id: "tp_reporting.action_lines",
        model: "tp.report.line",
        native_slug: "bao-cao-lines",
        name: "Dòng kết quả",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-lines"],
    },
    {
        url: "/app/bao-cao/phien-ban",
        action_xml_id: "tp_reporting.action_snapshots",
        model: "tp.report.snapshot",
        native_slug: "bao-cao-snapshots",
        name: "Phiên bản báo cáo",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-snapshots"],
    },
    {
        url: "/app/bao-cao/lich-su",
        action_xml_id: "tp_reporting.action_events",
        model: "tp.report.event",
        native_slug: "bao-cao-events",
        name: "Lịch sử báo cáo",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-events"],
    },
    {
        url: "/app/bao-cao/lich-su-ke-hoach",
        action_xml_id: "tp_reporting.action_plan_events",
        model: "tp.report.event",
        native_slug: "bao-cao-plan-events",
        name: "Lịch sử kế hoạch",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-plan-events"],
    },
    {
        url: "/app/bao-cao/ke-hoach-phan-bo",
        action_xml_id: "tp_reporting.action_plan_children",
        model: "tp.report.plan",
        native_slug: "bao-cao-plan-children",
        name: "Kế hoạch phân bổ",
        module: "tp_reporting",
        has_detail: true,
        aliases: ["/app/bao-cao-plan-children"],
    },
    {
        url: "/app/bao-cao/nhan-xet",
        action_xml_id: "tp_reporting.action_reviews",
        model: "tp.report.review",
        name: "Nhận xét và phản hồi",
        module: "tp_reporting",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/bao-cao/nhan-xet-bao-cao",
        action_xml_id: "tp_reporting.action_document_reviews",
        model: "tp.report.review",
        name: "Nhận xét báo cáo",
        module: "tp_reporting",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/bao-cao/nhan-xet-dau-viec",
        action_xml_id: "tp_reporting.action_line_reviews",
        model: "tp.report.review",
        name: "Nhận xét đầu việc",
        module: "tp_reporting",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/bao-cao/chi-tieu-bao-cao",
        action_xml_id: "tp_reporting.action_document_values",
        model: "tp.report.value",
        name: "Chỉ tiêu có nguồn",
        module: "tp_reporting",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/bao-cao/nghia-vu-bao-cao",
        action_xml_id: "tp_reporting.action_document_obligations",
        model: "tp.report.obligation",
        name: "Nghĩa vụ báo cáo theo hồ sơ",
        module: "tp_reporting",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/bao-cao/nhat-ky-bao-cao",
        action_xml_id: "tp_reporting.action_document_events",
        model: "tp.report.event",
        name: "Nhật ký báo cáo",
        module: "tp_reporting",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/bao-cao/phien-ban-bao-cao",
        action_xml_id: "tp_reporting.action_document_snapshots",
        model: "tp.report.snapshot",
        name: "Phiên bản theo báo cáo",
        module: "tp_reporting",
        has_detail: true,
        aliases: [],
    },
    {
        url: "/app/bao-cao/cong-viec-bao-cao",
        action_xml_id: "tp_reporting.action_document_lines",
        model: "tp.report.line",
        name: "Công việc báo cáo",
        module: "tp_reporting",
        has_detail: true,
        aliases: [],
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
        model: "tp.request",
        native_slug: "de-nghi-cua-toi",
        name: "Đề nghị của tôi",
        module: "tp_request",
        has_detail: true,
        aliases: ["/app/de-nghi-cua-toi"],
    },
    {
        url: "/app/de-nghi/can-duyet",
        action_xml_id: "tp_request.action_to_approve",
        model: "tp.request",
        native_slug: "de-nghi-can-duyet",
        name: "Cần tôi duyệt",
        module: "tp_request",
        has_detail: true,
        aliases: ["/app/de-nghi-can-duyet"],
    },
    {
        url: "/app/de-nghi/can-thuc-hien",
        action_xml_id: "tp_request.action_to_execute",
        model: "tp.request",
        native_slug: "de-nghi-can-thuc-hien",
        name: "Cần thực hiện",
        module: "tp_request",
        has_detail: true,
        aliases: ["/app/de-nghi-can-thuc-hien"],
    },
    {
        url: "/app/de-nghi/theo-doi",
        action_xml_id: "tp_request.action_watching",
        model: "tp.request",
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
        extra_action_xml_ids: ["project_todo.project_task_action_todo"],
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
        action_xml_id: "base_setup.action_general_configuration",
        extra_action_xml_ids: ["base.action_res_config_settings"],
        model: "res.config.settings",
        native_slug: "settings",
        name: "Cài đặt hệ thống",
        module: "base_setup",
        has_detail: false,
        aliases: ["/app/settings"],
    },
    {
        url: "/app/quan-tri/hanh-dong-may-chu",
        action_xml_id: "base.action_server_action",
        model: "ir.actions.server",
        name: "Hành động máy chủ",
        module: "base",
        has_detail: true,
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
    {
        url: "/app/quan-tri/bao-cao-uy-quyen",
        action_xml_id: "tp_admin_delegation.action_delegated_reports",
        model: "tp.report.document",
        native_slug: "quan-tri-bao-cao-uy-quyen",
        name: "Báo cáo ủy quyền",
        module: "tp_admin_delegation",
        has_detail: true,
        aliases: ["/app/quan-tri-bao-cao-uy-quyen"],
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

    // 11. Điều hành & Dự án WBS / NAS (dieu-hanh, du-an)
    {
        url: "/app/dieu-hanh/tong-quan",
        action_xml_id: "tp_enterprise_governance.action_executive_dashboard",
        action_tag: "tp_enterprise_governance.executive_dashboard",
        native_slug: "dieu-hanh-tong-quan",
        name: "Điều hành Lãnh đạo",
        module: "tp_enterprise_governance",
        has_detail: false,
        aliases: ["/app/dieu-hanh", "/app/dieu-hanh/lanh-dao", "/app/dieu-hanh-tong-quan"],
    },
    {
        url: "/app/du-an/wbs-tien-do",
        action_xml_id: "tp_enterprise_governance.action_project_wbs_cpm",
        action_tag: "tp_enterprise_governance.project_wbs",
        native_slug: "du-an-wbs-tien-do",
        name: "Tiến độ WBS & Đường găng CPM",
        module: "tp_enterprise_governance",
        has_detail: false,
        aliases: ["/app/du-an", "/app/du-an-wbs-tien-do"],
    },
    {
        url: "/app/du-an/ho-so-nas",
        action_xml_id: "tp_enterprise_governance.action_project_dossier_nas",
        action_tag: "tp_enterprise_governance.project_dossiers",
        native_slug: "du-an-ho-so-nas",
        name: "Hồ sơ dự án & NAS",
        module: "tp_enterprise_governance",
        has_detail: false,
        aliases: ["/app/du-an-ho-so-nas"],
    },
    {
        url: "/app/du-an/danh-muc-nen",
        action_xml_id: "tp_project.action_tp_projects",
        model: "project.project",
        native_slug: "nen-du-an",
        name: "Danh mục nền dự án",
        module: "tp_project",
        has_detail: true,
        aliases: ["/app/nen-du-an"],
    },

    // 12. Tuyển dụng, Thiết bị khảo sát, Đối soát lương & Trợ lý AI
    {
        url: "/app/tuyen-dung",
        action_xml_id: "tp_enterprise_ops.action_recruitment_workspace",
        action_tag: "tp_enterprise_ops.recruitment",
        native_slug: "tuyen-dung",
        name: "Tuyển dụng nhân sự",
        module: "tp_enterprise_ops",
        has_detail: false,
        aliases: ["/app/tuyen-dung/ung-vien"],
    },
    {
        url: "/app/thiet-bi/khao-sat",
        action_xml_id: "tp_enterprise_ops.action_survey_equipment_workspace",
        action_tag: "tp_enterprise_ops.survey_equipment",
        native_slug: "thiet-bi-khao-sat",
        name: "Thiết bị khảo sát & Kiểm định",
        module: "tp_enterprise_ops",
        has_detail: false,
        aliases: ["/app/khao-sat/thiet-bi-kiem-dinh", "/app/thiet-bi-khao-sat"],
    },
    {
        url: "/app/nhan-su/doi-soat-luong",
        action_xml_id: "tp_enterprise_ops.action_payroll_reconcile_workspace",
        action_tag: "tp_enterprise_ops.payroll_reconcile",
        native_slug: "doi-soat-luong",
        name: "Đối soát đầu vào Tiền lương",
        module: "tp_enterprise_ops",
        has_detail: false,
        aliases: ["/app/doi-soat-luong"],
    },
    {
        url: "/app/dieu-hanh/tro-ly-ai",
        action_xml_id: "tp_enterprise_ops.action_ai_assistant_workspace",
        action_tag: "tp_enterprise_ops.ai_assistant",
        native_slug: "tro-ly-ai",
        name: "Trợ lý AI Điều hành",
        module: "tp_enterprise_ops",
        has_detail: false,
        aliases: ["/app/tro-ly-ai"],
    },
];

// Primary canonical URL fallback when an inline ir.actions.act_window has res_model without action id
export const MODEL_FALLBACK_URLS = {
    "hr.employee": "/app/nhan-su/nhan-vien",
    "hr.employee.public": "/app/nhan-su/danh-ba",
    "hr.department": "/app/nhan-su/phong-ban",
    "hr.job": "/app/nhan-su/chuc-vu",
    "hr.work.location": "/app/nhan-su/noi-lam-viec",
    "hr.employee.category": "/app/nhan-su/nhan-nhan-vien",
    "hr.skill.type": "/app/nhan-su/loai-ky-nang",
    "hr.resume.line.type": "/app/nhan-su/loai-qua-trinh",
    "tp.hr.contract.document": "/app/nhan-su/ho-so-hop-dong",
    "tp.hr.employee.audit": "/app/nhan-su/nhat-ky-ho-so",
    "tp.hr.import.batch": "/app/nhan-su/nhap-doi-chieu",
    "tp.bank": "/app/nhan-su/danh-muc-ngan-hang",
    "tp.hr.attendance.day": "/app/cham-cong/ngay-cong",
    "tp.hr.attendance.correction": "/app/cham-cong/dieu-chinh",
    "tp.hr.attendance.period": "/app/cham-cong/chot-ky",
    "tp.hr.attendance.late": "/app/cham-cong/di-muon",
    "tp.hr.attendance.rule": "/app/cham-cong/quy-tac",
    "tp.hr.attendance.code": "/app/cham-cong/ma-may",
    "tp.hr.attendance.assignment": "/app/cham-cong/phan-cong",
    "tp.hr.attendance.log": "/app/cham-cong/nhat-ky-cham-cong",
    "tp.hr.attendance.batch": "/app/cham-cong/nhap-excel",
    "tp.hr.attendance.line": "/app/cham-cong/dong-nhap-excel",
    "tp.hr.attendance.source": "/app/cham-cong/ban-ghi-nguon",
    "tp.hr.attendance.event": "/app/cham-cong/su-kien-cham-cong",
    "tp.hr.attendance.enti.mapping": "/app/cham-cong/doi-chieu-nhan-vien",
    "tp.hr.attendance.enti.sync.log": "/app/cham-cong/nhat-ky-dong-bo",
    "tp.hr.attendance.enti.employee.image": "/app/cham-cong/dong-bo-anh",
    "crm.lead": "/app/khkd/du-an-tiem-nang",
    "tp.bid.package": "/app/khkd/dau-thau",
    "tp.contract": "/app/khkd/hop-dong",
    "tp.contract.revision": "/app/khkd/phien-ban-hop-dong",
    "tp.contract.document": "/app/khkd/tai-lieu-hop-dong",
    "tp.contract.audit": "/app/khkd/lich-su-hop-dong",
    "tp.contract.line.amount": "/app/khkd/hang-muc-so-tien",
    "project.project": "/app/khkd/du-an",
    "project.task": "/app/khkd/cong-viec",
    "tp.allocation": "/app/khkd/giao-khoan",
    "tp.production": "/app/khkd/san-luong",
    "tp.acceptance": "/app/khkd/nghiem-thu",
    "tp.payment.request": "/app/khkd/thanh-toan",
    "tp.periodic.plan": "/app/khkd/ke-hoach-dinh-ky",
    "tp.obligation": "/app/khkd/nghia-vu",
    "tp.credential": "/app/khkd/nang-luc-chung-chi",
    "tp.work.item": "/app/khkd/danh-muc-hang-muc",
    "tp.kd.document": "/app/khkd/tai-lieu-ho-so",
    "tp.task.update": "/app/khkd/lich-su-cong-viec",
    "maintenance.equipment": "/app/thiet-bi/danh-sach",
    "maintenance.equipment.category": "/app/thiet-bi/nhom-thiet-bi",
    "tp.equipment.location": "/app/thiet-bi/vi-tri-dat-may",
    "tp.equipment.proposal": "/app/thiet-bi/de-xuat",
    "tp.equipment.move": "/app/thiet-bi/phieu-ban-giao",
    "tp.equipment.move.line": "/app/thiet-bi/dong-ban-giao",
    "maintenance.request": "/app/thiet-bi/sua-chua",
    "tp.equipment.inventory": "/app/thiet-bi/kiem-ke",
    "tp.equipment.inventory.line": "/app/thiet-bi/dong-kiem-ke",
    "tp.equipment.receipt": "/app/thiet-bi/phieu-nhap-kho",
    "tp.equipment.import.batch": "/app/thiet-bi/nhap-du-lieu",
    "tp.equipment.import.line": "/app/thiet-bi/dong-nguon-cho",
    "tp.equipment.import.alias": "/app/thiet-bi/anh-xa-nguon",
    "tp.report.plan": "/app/bao-cao/muc-tieu",
    "tp.report.document": "/app/bao-cao/ca-nhan",
    "tp.report.directive": "/app/bao-cao/viec-can-xu-ly",
    "tp.report.schedule": "/app/bao-cao/lich-nhac-han",
    "tp.report.obligation": "/app/bao-cao/nghia-vu",
    "tp.report.template": "/app/bao-cao/mau-bao-cao",
    "tp.report.section": "/app/bao-cao/muc-trong-mau",
    "tp.report.section.content": "/app/bao-cao/noi-dung-muc",
    "tp.report.assignment": "/app/bao-cao/phan-quyen",
    "tp.report.metric": "/app/bao-cao/chi-tieu",
    "tp.report.value": "/app/bao-cao/gia-tri-nguon",
    "tp.report.priority": "/app/bao-cao/muc-uu-tien",
    "tp.report.rating": "/app/bao-cao/muc-danh-gia",
    "tp.report.line": "/app/bao-cao/dong-ket-qua",
    "tp.report.snapshot": "/app/bao-cao/phien-ban",
    "tp.report.event": "/app/bao-cao/lich-su",
    "tp.report.review": "/app/bao-cao/nhan-xet",
    "tp.request": "/app/de-nghi/cua-toi",
    "calendar.event": "/app/ca-nhan/lich-lam-viec",
    "res.users": "/app/quan-tri/tai-khoan",
    "res.company": "/app/quan-tri/cong-ty",
    "ir.module.module": "/app/quan-tri/ung-dung",
    "res.config.settings": "/app/quan-tri/cai-dat",
    "ir.actions.server": "/app/quan-tri/hanh-dong-may-chu",
};

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
 * Find primary canonical route for a target Odoo model name.
 */
export function findRouteByModel(modelName) {
    if (!modelName || typeof modelName !== "string") {
        return null;
    }
    const targetUrl = MODEL_FALLBACK_URLS[modelName];
    if (targetUrl) {
        for (const r of ROUTE_DEFINITIONS) {
            if (r.url === targetUrl) {
                return r;
            }
        }
    }
    for (const r of ROUTE_DEFINITIONS) {
        if (r.model === modelName) {
            return r;
        }
    }
    return null;
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
        target = isNaN(raw) ? raw : parseInt(raw, 10);
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
            if ((r.extra_action_xml_ids || []).includes(xmlId)) {
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
 * Handles exact routes, /<id> details, /tao-moi & /new, aliases, action-<id>, and m-<model>.
 *
 * @param {string} pathname
 * @returns {{ route: object|null, resId: number|string|null, isNew: boolean, canonicalUrl: string|null }}
 */
export function parseBrandedUrl(pathname) {
    if (!pathname || typeof pathname !== "string") {
        return { route: null, resId: null, isNew: false, canonicalUrl: null };
    }
    syncFromSession();

    const clean = pathname.replace(/\/+$/, "") || "/";

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

    // 4. Backward compatibility: /app/m-<model>[/<resId>]
    const modelMatch = clean.match(/^\/app\/m-([a-z0-9_.]+)(?:\/(new|tao-moi|\d+))?$/);
    if (modelMatch) {
        const route = findRouteByModel(modelMatch[1]);
        const subRes = modelMatch[2];
        if (route) {
            let resId = null;
            let isNew = false;
            let canonical = route.url;
            if (subRes === "new" || subRes === "tao-moi") {
                resId = "new";
                isNew = true;
                if (route.has_detail) {
                    canonical += "/tao-moi";
                }
            } else if (subRes && /^\d+$/.test(subRes)) {
                resId = parseInt(subRes, 10);
                if (route.has_detail) {
                    canonical += `/${resId}`;
                }
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
