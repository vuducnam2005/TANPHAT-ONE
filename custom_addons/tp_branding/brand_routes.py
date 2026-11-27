# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Business route registry for TANPHAT ONE (SYSTEM-URL-001).

Maps business URLs to native Odoo actions, XML IDs, models, and action tags.
Shared specification between backend and frontend.
"""

# Route definitions for all active workspaces and user screens.
# Each entry defines:
#   url: The canonical business URL under /app
#   action_xml_id: External ID of the action (stable across all environments)
#   name: Human-readable Vietnamese name
#   module: Module that defines the action
#   action_tag: Client action tag (if ir.actions.client)
#   model: Target res_model (if ir.actions.act_window)
#   native_slug: Legacy or single-slug path in ir.actions.actions.path (if any)
#   has_detail: True if screen supports /<id> and /tao-moi
#   aliases: Legacy or shorthand URLs that canonicalize to this URL
ROUTE_DEFINITIONS = [
    {
        "url": "/app/tai-khoan/bao-mat",
        "action_xml_id": "tp_web_login.action_account_security",
        "action_tag": "tp_web_login.account_security",
        "native_slug": "tai-khoan-bao-mat",
        "name": "Tài khoản & Bảo mật",
        "module": "tp_web_login",
        "has_detail": False,
        "aliases": [],
    },
    # ------------------------------------------------------------------
    # 1. Trang chủ
    # ------------------------------------------------------------------
    {
        "url": "/app/trang-chu",
        "action_xml_id": "tp_web_home.action_home",
        "action_tag": "tp_web_home.home",
        "native_slug": "tp-home",
        "name": "Trang chủ",
        "module": "tp_web_home",
        "has_detail": False,
        "aliases": ["/app/tp-home"],
    },

    # ------------------------------------------------------------------
    # 2. Nhân sự (nhan-su)
    # ------------------------------------------------------------------
    {
        "url": "/app/nhan-su/tong-quan",
        "action_xml_id": "tp_hr_workspace.action_overview",
        "action_tag": "tp_hr_workspace.overview",
        "native_slug": "tp-hr",
        "name": "Tổng quan nhân sự",
        "module": "tp_hr_workspace",
        "has_detail": False,
        "aliases": ["/app/tp-hr", "/app/tp-hr-tong-quan"],
    },
    {
        "url": "/app/nhan-su/nhan-vien",
        "action_xml_id": "tp_hr_workspace.action_employees",
        "model": "hr.employee",
        "name": "Danh sách nhân viên",
        "module": "tp_hr_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/phong-ban",
        "action_xml_id": "tp_hr_workspace.action_departments",
        "model": "hr.department",
        "name": "Phòng ban và đơn vị",
        "module": "tp_hr_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/chuc-vu",
        "action_xml_id": "tp_hr_workspace.action_jobs",
        "model": "hr.job",
        "name": "Chức vụ",
        "module": "tp_hr_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/ho-so-can-bo-sung",
        "action_xml_id": "tp_hr_workspace.action_missing",
        "model": "hr.employee",
        "name": "Hồ sơ cần bổ sung",
        "module": "tp_hr_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/luu-tru",
        "action_xml_id": "tp_hr_workspace.action_archived",
        "model": "hr.employee",
        "name": "Lưu trữ nhân viên",
        "module": "tp_hr_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/ho-so-cua-toi",
        "action_xml_id": "tp_hr_workspace.action_my_profile",
        "action_tag": "tp_hr_workspace.my_profile",
        "native_slug": "my-profile",
        "name": "Hồ sơ của tôi",
        "module": "tp_hr_workspace",
        "has_detail": False,
        "aliases": ["/app/my-profile"],
    },
    {
        "url": "/app/nhan-su/phong-ban-cua-toi",
        "action_xml_id": "tp_hr_workspace.action_department_workspace",
        "action_tag": "tp_department_workspace",
        "name": "Phòng ban của tôi",
        "module": "tp_hr_workspace",
        "has_detail": False,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/nhat-ky-ho-so",
        "action_xml_id": "tp_hr_workspace.action_employee_audit",
        "model": "tp.hr.employee.audit",
        "name": "Nhật ký xóa hồ sơ và sửa mã",
        "module": "tp_hr_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/chua-co-tai-khoan",
        "action_xml_id": "tp_hr_workspace.action_pending",
        "model": "hr.employee",
        "name": "Nhân viên chưa có tài khoản",
        "module": "tp_hr_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/noi-lam-viec",
        "action_xml_id": "tp_hr_workspace.action_locations",
        "model": "hr.work.location",
        "name": "Nơi làm việc",
        "module": "tp_hr_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/so-do-quan-ly",
        "action_xml_id": "tp_hr_workspace.action_hierarchy",
        "model": "hr.employee",
        "name": "Sơ đồ quản lý đã khai báo",
        "module": "tp_hr_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/nhap-doi-chieu",
        "action_xml_id": "tp_hr_workspace.action_import",
        "model": "tp.hr.import.batch",
        "name": "Nhập và đối chiếu",
        "module": "tp_hr_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/nhan-nhan-vien",
        "action_xml_id": "tp_hr_workspace.action_categories",
        "model": "hr.employee.category",
        "name": "Nhãn nhân viên",
        "module": "tp_hr_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/danh-ba",
        "action_xml_id": "tp_hr_workspace.action_directory",
        "model": "hr.employee.public",
        "name": "Danh bạ nhân sự",
        "module": "tp_hr_workspace",
        "has_detail": True,
        "aliases": [],
    },

    # ------------------------------------------------------------------
    # 3. Chấm công (cham-cong; legacy /app/nhan-su/cham-cong/... kept as aliases)
    # ------------------------------------------------------------------
    {
        "url": "/app/cham-cong/tong-quan",
        "action_xml_id": "tp_hr_attendance.action_dashboard",
        "action_tag": "tp_hr_attendance.dashboard",
        "native_slug": "cham-cong",
        "name": "Tổng quan chấm công",
        "module": "tp_hr_attendance",
        "has_detail": False,
        "aliases": ["/app/cham-cong", "/app/nhan-su/cham-cong/tong-quan", "/app/nhan-su/cham-cong"],
    },
    {
        "url": "/app/cham-cong/cua-toi",
        "action_xml_id": "tp_hr_attendance.action_mine",
        "action_tag": "tp_hr_attendance.mine",
        "native_slug": "cong-cua-toi",
        "name": "Công của tôi",
        "module": "tp_hr_attendance",
        "has_detail": False,
        "aliases": ["/app/cong-cua-toi", "/app/nhan-su/cham-cong/cua-toi"],
    },
    {
        "url": "/app/cham-cong/quan-tri",
        "action_xml_id": "tp_hr_attendance.action_sources",
        "action_tag": "tp_hr_attendance.sources",
        "native_slug": "nguon-cham-cong",
        "name": "Tổng quan quản trị chấm công",
        "module": "tp_hr_attendance",
        "has_detail": False,
        "aliases": ["/app/nguon-cham-cong", "/app/nhan-su/cham-cong/quan-tri", "/app/nhan-su/cham-cong/nguon-du-lieu"],
    },
    {
        "url": "/app/cham-cong/cau-hinh",
        "action_xml_id": "tp_hr_attendance.action_enti_config",
        "model": "tp.hr.attendance.enti.config.wizard",
        "name": "Cấu hình kết nối chấm công",
        "module": "tp_hr_attendance",
        "has_detail": False,
        "aliases": ["/app/nhan-su/cham-cong/cau-hinh"],
    },
    {
        "url": "/app/cham-cong/doi-chieu-nhan-vien",
        "action_xml_id": "tp_hr_attendance.action_enti_mapping",
        "model": "tp.hr.attendance.enti.mapping",
        "name": "Đối chiếu nhân viên chấm công",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": ["/app/nhan-su/cham-cong/doi-chieu-nhan-vien"],
    },
    {
        "url": "/app/cham-cong/nhat-ky-dong-bo",
        "action_xml_id": "tp_hr_attendance.action_enti_logs",
        "model": "tp.hr.attendance.enti.sync.log",
        "name": "Nhật ký đồng bộ chấm công",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": ["/app/nhan-su/cham-cong/nhat-ky-dong-bo"],
    },
    {
        "url": "/app/cham-cong/dong-bo-anh",
        "action_xml_id": "tp_hr_attendance.action_enti_employee_images",
        "model": "tp.hr.attendance.enti.employee.image",
        "name": "Nhật ký đồng bộ ảnh hồ sơ ENTI",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": ["/app/nhan-su/cham-cong/dong-bo-anh"],
    },
    {
        "url": "/app/cham-cong/dieu-chinh",
        "action_xml_id": "tp_hr_attendance.action_review",
        "model": "tp.hr.attendance.correction",
        "name": "Xử lý điều chỉnh công",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": ["/app/nhan-su/cham-cong/dieu-chinh"],
    },
    {
        "url": "/app/cham-cong/yeu-cau-cua-toi",
        "action_xml_id": "tp_hr_attendance.action_my_requests",
        "name": "Yêu cầu điều chỉnh của tôi",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": ["/app/nhan-su/cham-cong/yeu-cau-cua-toi"],
    },
    {
        "url": "/app/cham-cong/chot-ky",
        "action_xml_id": "tp_hr_attendance.action_periods",
        "model": "tp.hr.attendance.period",
        "name": "Chốt kỳ công",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": ["/app/nhan-su/cham-cong/chot-ky"],
    },
    {
        "url": "/app/cham-cong/bang-cong",
        "action_xml_id": "tp_hr_attendance.action_days",
        "model": "tp.hr.attendance.day",
        "name": "Bảng ngày công",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": ["/app/nhan-su/cham-cong/bang-cong"],
    },
    {
        "url": "/app/cham-cong/di-muon",
        "action_xml_id": "tp_hr_attendance.action_late",
        "model": "tp.hr.attendance.late",
        "name": "Tổng đi muộn theo kỳ",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": ["/app/nhan-su/cham-cong/di-muon"],
    },
    {
        "url": "/app/cham-cong/quy-tac",
        "action_xml_id": "tp_hr_attendance.action_rules",
        "model": "tp.hr.attendance.rule",
        "name": "Quy tắc công",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": ["/app/nhan-su/cham-cong/quy-tac"],
    },
    {
        "url": "/app/cham-cong/ma-may",
        "action_xml_id": "tp_hr_attendance.action_codes",
        "model": "tp.hr.attendance.code",
        "name": "Mã máy chấm công",
        "module": "tp_hr_attendance",
        "has_detail": False,
        "aliases": ["/app/nhan-su/cham-cong/ma-may"],
    },
    {
        "url": "/app/cham-cong/phan-cong",
        "action_xml_id": "tp_hr_attendance.action_assignments",
        "model": "tp.hr.attendance.assignment",
        "name": "Phân công xử lý công",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": ["/app/nhan-su/cham-cong/phan-cong"],
    },
    {
        "url": "/app/cham-cong/nhat-ky-cham-cong",
        "action_xml_id": "tp_hr_attendance.action_logs",
        "model": "tp.hr.attendance.log",
        "name": "Nhật ký chấm công",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": ["/app/nhan-su/cham-cong/nhat-ky-cham-cong"],
    },

    # ------------------------------------------------------------------
    # 4. Kế hoạch Kinh doanh (khkd)
    # ------------------------------------------------------------------
    {
        "url": "/app/khkd/tong-quan",
        "action_xml_id": "tp_kd_workspace.action_overview",
        "model": "tp.kd.overview",
        "name": "Tổng quan KH-KD",
        "module": "tp_kd_workspace",
        "has_detail": False,
        "aliases": [],
    },
    {
        "url": "/app/khkd/du-an-tiem-nang",
        "action_xml_id": "tp_kd_workspace.action_opportunities",
        "model": "crm.lead",
        "name": "Dự án tiềm năng",
        "module": "tp_kd_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/khkd/dau-thau",
        "action_xml_id": "tp_kd_workspace.action_packages",
        "model": "tp.bid.package",
        "name": "Đấu thầu",
        "module": "tp_kd_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/khkd/ho-so-thau",
        "action_xml_id": "tp_kd_workspace.action_reconcile",
        "model": "crm.lead",
        "name": "Hồ sơ thầu",
        "module": "tp_kd_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/khkd/hop-dong",
        "action_xml_id": "tp_contract.action_tp_contracts_list",
        "model": "tp.contract",
        "name": "Hợp đồng",
        "module": "tp_contract",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/khkd/quan-ly-du-an",
        "action_xml_id": "tp_kd_workspace.action_management",
        "model": "tp.project.perspective",
        "name": "Quản lý dự án",
        "module": "tp_kd_workspace",
        "has_detail": False,
        "aliases": [],
    },
    {
        "url": "/app/khkd/quan-tri-du-an",
        "action_xml_id": "tp_kd_workspace.action_governance",
        "model": "tp.project.perspective",
        "name": "Quản trị dự án",
        "module": "tp_kd_workspace",
        "has_detail": False,
        "aliases": [],
    },
    {
        "url": "/app/khkd/bao-cao",
        "action_xml_id": "tp_kd_workspace.action_reports",
        "model": "tp.kd.report.center",
        "name": "Báo cáo KH-KD",
        "module": "tp_kd_workspace",
        "has_detail": False,
        "aliases": [],
    },
    {
        "url": "/app/khkd/wbs",
        "action_xml_id": "tp_kd_workspace.action_wbs",
        "model": "project.task",
        "name": "Hạng mục / WBS",
        "module": "tp_kd_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/khkd/du-an",
        "action_xml_id": "tp_kd_workspace.action_projects",
        "model": "project.project",
        "native_slug": "khkd-du-an",
        "name": "Dự án KH-KD",
        "module": "tp_kd_workspace",
        "has_detail": True,
        "aliases": ["/app/khkd-du-an"],
    },
    {
        "url": "/app/khkd/cong-viec",
        "action_xml_id": "tp_kd_workspace.action_tasks",
        "model": "project.task",
        "native_slug": "khkd-cong-viec",
        "name": "Công việc và tiến độ",
        "module": "tp_kd_workspace",
        "has_detail": True,
        "aliases": ["/app/khkd-cong-viec"],
    },
    {
        "url": "/app/khkd/giao-khoan",
        "action_xml_id": "tp_kd_workspace.action_allocations",
        "model": "tp.allocation",
        "name": "Giao khoán và thầu phụ",
        "module": "tp_kd_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/khkd/san-luong",
        "action_xml_id": "tp_kd_workspace.action_productions",
        "model": "tp.production",
        "name": "Sản lượng theo kỳ",
        "module": "tp_kd_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/khkd/nghiem-thu",
        "action_xml_id": "tp_kd_workspace.action_acceptances",
        "model": "tp.acceptance",
        "name": "Hồ sơ nghiệm thu",
        "module": "tp_kd_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/khkd/thanh-toan",
        "action_xml_id": "tp_kd_workspace.action_payments",
        "model": "tp.payment.request",
        "name": "Đề nghị thanh toán",
        "module": "tp_kd_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/khkd/ke-hoach-dinh-ky",
        "action_xml_id": "tp_kd_workspace.action_plans",
        "model": "tp.periodic.plan",
        "name": "Kế hoạch định kỳ",
        "module": "tp_kd_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/khkd/nghia-vu",
        "action_xml_id": "tp_kd_workspace.action_obligations",
        "model": "tp.obligation",
        "name": "Nghĩa vụ và hồ sơ còn thiếu",
        "module": "tp_kd_workspace",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/khkd/nang-luc-chung-chi",
        "action_xml_id": "tp_kd_workspace.action_credentials",
        "model": "tp.credential",
        "name": "Hồ sơ năng lực và chứng chỉ",
        "module": "tp_kd_workspace",
        "has_detail": True,
        "aliases": [],
    },

    # ------------------------------------------------------------------
    # 5. Thiết bị (thiet-bi)
    # ------------------------------------------------------------------
    {
        "url": "/app/thiet-bi/tong-quan",
        "action_xml_id": "tp_equipment.action_dashboard",
        "action_tag": "tp_equipment.dashboard",
        "native_slug": "tong-quan-thiet-bi",
        "name": "Tổng quan thiết bị",
        "module": "tp_equipment",
        "has_detail": False,
        "aliases": ["/app/tong-quan-thiet-bi"],
    },
    {
        "url": "/app/thiet-bi/danh-sach",
        "action_xml_id": "tp_equipment.action_equipment",
        "model": "maintenance.equipment",
        "native_slug": "kho-thiet-bi",
        "name": "Danh sách thiết bị",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": ["/app/kho-thiet-bi"],
    },
    {
        "url": "/app/thiet-bi/ton-kho",
        "action_xml_id": "tp_equipment.action_equipment_stock",
        "model": "maintenance.equipment",
        "native_slug": "ton-kho-thiet-bi",
        "name": "Thiết bị tồn kho",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": ["/app/ton-kho-thiet-bi"],
    },
    {
        "url": "/app/thiet-bi/de-xuat",
        "action_xml_id": "tp_equipment.action_proposals",
        "model": "tp.equipment.proposal",
        "native_slug": "de-xuat-thiet-bi",
        "name": "Yêu cầu đề xuất thiết bị",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": ["/app/de-xuat-thiet-bi"],
    },
    {
        "url": "/app/thiet-bi/phieu-ban-giao",
        "action_xml_id": "tp_equipment.action_moves",
        "model": "tp.equipment.move",
        "native_slug": "phieu-thiet-bi",
        "name": "Phiếu bàn giao / thu hồi",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": ["/app/phieu-thiet-bi"],
    },
    {
        "url": "/app/thiet-bi/sua-chua",
        "action_xml_id": "tp_equipment.action_repairs",
        "model": "maintenance.request",
        "native_slug": "sua-chua-thiet-bi",
        "name": "Sửa chữa / bảo trì",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": ["/app/sua-chua-thiet-bi"],
    },
    {
        "url": "/app/thiet-bi/kiem-ke",
        "action_xml_id": "tp_equipment.action_inventories",
        "model": "tp.equipment.inventory",
        "native_slug": "kiem-ke-thiet-bi",
        "name": "Kiểm kê thiết bị",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": ["/app/kiem-ke-thiet-bi"],
    },
    {
        "url": "/app/thiet-bi/dung-chung",
        "action_xml_id": "tp_equipment.action_equipment_shared",
        "model": "maintenance.equipment",
        "name": "Thiết bị dùng chung",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/thiet-bi/tat-ca",
        "action_xml_id": "tp_equipment.action_equipment_all_records",
        "model": "maintenance.equipment",
        "name": "Tất cả hồ sơ thiết bị",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/thiet-bi/phan-loai",
        "action_xml_id": "tp_equipment.action_category",
        "model": "maintenance.equipment.category",
        "name": "Phân loại thiết bị",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/thiet-bi/vi-tri",
        "action_xml_id": "tp_equipment.action_location",
        "model": "tp.equipment.location",
        "name": "Vị trí đặt thiết bị",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/thiet-bi/nhap-du-lieu",
        "action_xml_id": "tp_equipment.action_import",
        "model": "tp.equipment.import.batch",
        "native_slug": "nhap-du-lieu-thiet-bi",
        "name": "Nhập nguồn thiết bị",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": ["/app/nhap-du-lieu-thiet-bi"],
    },
    {
        "url": "/app/thiet-bi/dong-nguon-cho",
        "action_xml_id": "tp_equipment.action_import_pending",
        "model": "tp.equipment.import.line",
        "native_slug": "dong-nguon-thiet-bi-cho",
        "name": "Dòng nguồn chờ bổ sung",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": ["/app/dong-nguon-thiet-bi-cho"],
    },
    {
        "url": "/app/thiet-bi/anh-xa-nguon",
        "action_xml_id": "tp_equipment.action_import_alias",
        "model": "tp.equipment.import.alias",
        "native_slug": "anh-xa-nguon-thiet-bi",
        "name": "Ánh xạ tên đã xác nhận",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": ["/app/anh-xa-nguon-thiet-bi"],
    },
    {
        "url": "/app/thiet-bi/phieu-nhap-kho",
        "action_xml_id": "tp_equipment.action_receipts",
        "model": "tp.equipment.receipt",
        "name": "Phiếu nhập kho thiết bị",
        "module": "tp_equipment",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/du-an/danh-muc-cong-viec",
        "action_xml_id": "tp_core.action_work_items",
        "model": "tp.work.item",
        "name": "Danh mục công việc",
        "module": "tp_core",
        "has_detail": True,
        "aliases": [],
    },

    # ------------------------------------------------------------------
    # 6. Báo cáo (bao-cao)
    # ------------------------------------------------------------------
    {
        "url": "/app/bao-cao/tong-quan",
        "action_xml_id": "tp_reporting.action_dashboard",
        "action_tag": "tp_reporting.dashboard",
        "native_slug": "bao-cao-tong-quan",
        "name": "Tổng quan báo cáo",
        "module": "tp_reporting",
        "has_detail": False,
        "aliases": ["/app/bao-cao-tong-quan"],
    },
    {
        "url": "/app/bao-cao/muc-tieu",
        "action_xml_id": "tp_reporting.action_plans",
        "model": "tp.report.plan",
        "native_slug": "bao-cao-plans",
        "name": "Mục tiêu và kế hoạch",
        "module": "tp_reporting",
        "has_detail": True,
        "aliases": ["/app/bao-cao-plans"],
    },
    {
        "url": "/app/bao-cao/ca-nhan",
        "action_xml_id": "tp_reporting.action_personal",
        "model": "tp.report.document",
        "native_slug": "bao-cao-personal",
        "name": "Báo cáo cá nhân",
        "module": "tp_reporting",
        "has_detail": True,
        "aliases": ["/app/bao-cao-personal"],
    },
    {
        "url": "/app/bao-cao/phong-ban",
        "action_xml_id": "tp_reporting.action_department",
        "model": "tp.report.document",
        "native_slug": "bao-cao-department",
        "name": "Báo cáo phòng ban",
        "module": "tp_reporting",
        "has_detail": True,
        "aliases": ["/app/bao-cao-department"],
    },
    {
        "url": "/app/bao-cao/cong-ty",
        "action_xml_id": "tp_reporting.action_company",
        "model": "tp.report.document",
        "native_slug": "bao-cao-company",
        "name": "Báo cáo công ty",
        "module": "tp_reporting",
        "has_detail": True,
        "aliases": ["/app/bao-cao-company"],
    },
    {
        "url": "/app/bao-cao/cho-ra-soat",
        "action_xml_id": "tp_reporting.action_my_review",
        "model": "tp.report.document",
        "native_slug": "bao-cao-cho-ra-soat",
        "name": "Chờ tôi rà soát",
        "module": "tp_reporting",
        "has_detail": True,
        "aliases": ["/app/bao-cao-cho-ra-soat"],
    },

    # ------------------------------------------------------------------
    # 7. Yêu cầu phê duyệt (de-nghi)
    # ------------------------------------------------------------------
    {
        "url": "/app/de-nghi/tong-quan",
        "action_xml_id": "tp_request.action_overview",
        "action_tag": "tp_request.dashboard",
        "native_slug": "de-nghi-tong-quan",
        "name": "Tổng quan Yêu cầu phê duyệt",
        "module": "tp_request",
        "has_detail": False,
        "aliases": ["/app/de-nghi", "/app/de-nghi-tong-quan"],
    },
    {
        "url": "/app/de-nghi/cua-toi",
        "action_xml_id": "tp_request.action_mine",
        "native_slug": "de-nghi-cua-toi",
        "name": "Đề nghị của tôi",
        "module": "tp_request",
        "has_detail": True,
        "aliases": ["/app/de-nghi-cua-toi"],
    },
    {
        "url": "/app/de-nghi/can-duyet",
        "action_xml_id": "tp_request.action_to_approve",
        "native_slug": "de-nghi-can-duyet",
        "name": "Cần tôi duyệt",
        "module": "tp_request",
        "has_detail": True,
        "aliases": ["/app/de-nghi-can-duyet"],
    },
    {
        "url": "/app/de-nghi/can-thuc-hien",
        "action_xml_id": "tp_request.action_to_execute",
        "native_slug": "de-nghi-can-thuc-hien",
        "name": "Cần thực hiện",
        "module": "tp_request",
        "has_detail": True,
        "aliases": ["/app/de-nghi-can-thuc-hien"],
    },
    {
        "url": "/app/de-nghi/theo-doi",
        "action_xml_id": "tp_request.action_watching",
        "native_slug": "de-nghi-theo-doi",
        "name": "Theo dõi đề nghị",
        "module": "tp_request",
        "has_detail": True,
        "aliases": ["/app/de-nghi-theo-doi"],
    },
    {
        "url": "/app/de-nghi/quan-tri",
        "action_xml_id": "tp_request.action_admin",
        "action_tag": "tp_request.admin",
        "native_slug": "de-nghi-quan-tri",
        "name": "Quản trị Yêu cầu phê duyệt",
        "module": "tp_request",
        "has_detail": False,
        "aliases": ["/app/de-nghi-quan-tri"],
    },
    {
        "url": "/app/de-nghi/ho-so",
        "action_xml_id": "tp_request.action_detail",
        "action_tag": "tp_request.detail",
        "native_slug": "de-nghi-ho-so",
        "name": "Chi tiết hồ sơ đề nghị",
        "module": "tp_request",
        "has_detail": True,
        "aliases": ["/app/de-nghi-ho-so"],
    },

    # ------------------------------------------------------------------
    # 8. Công cụ cá nhân (ca-nhan)
    # ------------------------------------------------------------------
    {
        "url": "/app/ca-nhan/cong-viec",
        "action_xml_id": "tp_personal_tools.action_personal_todo",
        "action_tag": "tp_personal_tools.todo_workspace",
        "native_slug": "cong-viec-ca-nhan",
        "name": "Việc cá nhân",
        "module": "tp_personal_tools",
        "has_detail": True,
        "aliases": ["/app/to-do", "/app/cong-viec-ca-nhan"],
    },
    {
        "url": "/app/ca-nhan/lich-lam-viec",
        "action_xml_id": "calendar.action_calendar_event",
        "model": "calendar.event",
        "native_slug": "calendar",
        "name": "Lịch làm việc",
        "module": "calendar",
        "has_detail": True,
        "aliases": ["/app/calendar", "/app/lich-lam-viec"],
    },
    {
        "url": "/app/ca-nhan/trao-doi",
        "action_xml_id": "mail.action_discuss",
        "action_tag": "mail.action_discuss",
        "native_slug": "discuss",
        "name": "Trao đổi",
        "module": "mail",
        "has_detail": True,
        "aliases": ["/app/discuss", "/app/trao-doi"],
    },

    # ------------------------------------------------------------------
    # 9. Quản trị (quan-tri)
    # ------------------------------------------------------------------
    {
        "url": "/app/quan-tri/cai-dat",
        "action_xml_id": "base.action_server_action",
        "name": "Cài đặt hệ thống",
        "module": "base",
        "has_detail": False,
        "aliases": [],
    },
    {
        "url": "/app/quan-tri/tai-khoan",
        "action_xml_id": "base.action_res_users",
        "model": "res.users",
        "native_slug": "users",
        "name": "Người dùng / Tài khoản",
        "module": "base",
        "has_detail": True,
        "aliases": ["/app/users"],
    },
    {
        "url": "/app/quan-tri/ung-dung",
        "action_xml_id": "base.open_module_tree",
        "model": "ir.module.module",
        "native_slug": "apps",
        "name": "Ứng dụng",
        "module": "base",
        "has_detail": True,
        "aliases": ["/app/apps"],
    },
    {
        "url": "/app/quan-tri/cong-ty",
        "action_xml_id": "base.action_res_company_form",
        "model": "res.company",
        "native_slug": "companies",
        "name": "Công ty",
        "module": "base",
        "has_detail": True,
        "aliases": ["/app/companies"],
    },

    # ------------------------------------------------------------------
    # 10. Văn phòng số (van-phong-so)
    # ------------------------------------------------------------------
    {
        "url": "/app/van-phong-so/thong-bao",
        "action_xml_id": "tp_digital_office.action_announcements",
        "action_tag": "tp_digital_office.announcements",
        "native_slug": "thong-bao-noi-bo",
        "name": "Thông báo nội bộ",
        "module": "tp_digital_office",
        "has_detail": False,
        "aliases": ["/app/van-phong-so", "/app/thong-bao-noi-bo"],
    },
    {
        "url": "/app/van-phong-so/bien-ban-hop",
        "action_xml_id": "tp_digital_office.action_meeting_minutes",
        "action_tag": "tp_digital_office.meeting_minutes",
        "native_slug": "bien-ban-hop",
        "name": "Biên bản họp",
        "module": "tp_digital_office",
        "has_detail": False,
        "aliases": ["/app/bien-ban-hop"],
    },

    # ------------------------------------------------------------------
    # 11. Điều hành & Dự án WBS / NAS (dieu-hanh, du-an)
    # ------------------------------------------------------------------
    {
        "url": "/app/dieu-hanh/tong-quan",
        "action_xml_id": "tp_enterprise_governance.action_executive_dashboard",
        "action_tag": "tp_enterprise_governance.executive_dashboard",
        "native_slug": "dieu-hanh-tong-quan",
        "name": "Điều hành Lãnh đạo",
        "module": "tp_enterprise_governance",
        "has_detail": False,
        "aliases": ["/app/dieu-hanh"],
    },
    {
        "url": "/app/du-an/wbs-tien-do",
        "action_xml_id": "tp_enterprise_governance.action_project_wbs_cpm",
        "action_tag": "tp_enterprise_governance.project_wbs",
        "native_slug": "du-an-wbs-tien-do",
        "name": "Tiến độ WBS & Đường găng CPM",
        "module": "tp_enterprise_governance",
        "has_detail": False,
        "aliases": ["/app/du-an"],
    },
    {
        "url": "/app/du-an/ho-so-nas",
        "action_xml_id": "tp_enterprise_governance.action_project_dossier_nas",
        "action_tag": "tp_enterprise_governance.project_dossiers",
        "native_slug": "du-an-ho-so-nas",
        "name": "Hồ sơ dự án & NAS",
        "module": "tp_enterprise_governance",
        "has_detail": False,
        "aliases": [],
    },

    # ------------------------------------------------------------------
    # 12. Tuyển dụng, Thiết bị khảo sát, Đối soát lương & Trợ lý AI
    # ------------------------------------------------------------------
    {
        "url": "/app/tuyen-dung",
        "action_xml_id": "tp_enterprise_ops.action_recruitment_workspace",
        "action_tag": "tp_enterprise_ops.recruitment",
        "native_slug": "tuyen-dung",
        "name": "Tuyển dụng nhân sự",
        "module": "tp_enterprise_ops",
        "has_detail": False,
        "aliases": ["/app/tuyen-dung/ung-vien"],
    },
    {
        "url": "/app/thiet-bi/khao-sat",
        "action_xml_id": "tp_enterprise_ops.action_survey_equipment_workspace",
        "action_tag": "tp_enterprise_ops.survey_equipment",
        "native_slug": "thiet-bi-khao-sat",
        "name": "Thiết bị khảo sát & Kiểm định",
        "module": "tp_enterprise_ops",
        "has_detail": False,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/doi-soat-luong",
        "action_xml_id": "tp_enterprise_ops.action_payroll_reconcile_workspace",
        "action_tag": "tp_enterprise_ops.payroll_reconcile",
        "native_slug": "doi-soat-luong",
        "name": "Đối soát đầu vào Tiền lương",
        "module": "tp_enterprise_ops",
        "has_detail": False,
        "aliases": [],
    },
    {
        "url": "/app/dieu-hanh/tro-ly-ai",
        "action_xml_id": "tp_enterprise_ops.action_ai_assistant_workspace",
        "action_tag": "tp_enterprise_ops.ai_assistant",
        "native_slug": "tro-ly-ai",
        "name": "Trợ lý AI Điều hành",
        "module": "tp_enterprise_ops",
        "has_detail": False,
        "aliases": [],
    },
]


def get_all_action_xml_ids():
    """Return all unique action_xml_id strings in the registry."""
    xml_ids = set()
    for r in ROUTE_DEFINITIONS:
        xid = r.get("action_xml_id")
        if xid:
            xml_ids.add(xid)
    return sorted(xml_ids)


def get_route_by_url(path):
    """Find a route by its canonical business URL or alias."""
    clean = (path or "").rstrip("/") or "/"
    for r in ROUTE_DEFINITIONS:
        if r["url"] == clean:
            return r
        for alias in r.get("aliases", []):
            if alias == clean:
                return r
    return None


def get_route_by_action_xml_id(xml_id):
    """Find a route by its action XML ID."""
    if not xml_id:
        return None
    for r in ROUTE_DEFINITIONS:
        if r.get("action_xml_id") == xml_id:
            return r
    return None


def get_route_by_action_tag(tag):
    """Find a route by its action tag."""
    if not tag:
        return None
    for r in ROUTE_DEFINITIONS:
        if r.get("action_tag") == tag:
            return r
    return None


def get_route_by_native_slug(slug):
    """Find a route by its native action path slug."""
    if not slug:
        return None
    for r in ROUTE_DEFINITIONS:
        if r.get("native_slug") == slug:
            return r
    return None
