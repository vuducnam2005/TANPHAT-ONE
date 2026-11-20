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

    # ------------------------------------------------------------------
    # 3. Chấm công (nhan-su/cham-cong)
    # ------------------------------------------------------------------
    {
        "url": "/app/nhan-su/cham-cong/tong-quan",
        "action_xml_id": "tp_hr_attendance.action_dashboard",
        "action_tag": "tp_hr_attendance.dashboard",
        "native_slug": "cham-cong",
        "name": "Tổng quan chấm công",
        "module": "tp_hr_attendance",
        "has_detail": False,
        "aliases": ["/app/cham-cong"],
    },
    {
        "url": "/app/nhan-su/cham-cong/cua-toi",
        "action_xml_id": "tp_hr_attendance.action_mine",
        "action_tag": "tp_hr_attendance.mine",
        "native_slug": "cong-cua-toi",
        "name": "Công của tôi",
        "module": "tp_hr_attendance",
        "has_detail": False,
        "aliases": ["/app/cong-cua-toi"],
    },
    {
        "url": "/app/nhan-su/cham-cong/cau-hinh",
        "action_xml_id": "tp_hr_attendance.action_enti_config",
        "model": "tp.hr.attendance.enti.config.wizard",
        "name": "Cấu hình kết nối chấm công",
        "module": "tp_hr_attendance",
        "has_detail": False,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/cham-cong/doi-chieu-nhan-vien",
        "action_xml_id": "tp_hr_attendance.action_enti_mapping",
        "model": "tp.hr.attendance.enti.mapping",
        "name": "Đối chiếu nhân viên chấm công",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/cham-cong/nhat-ky-dong-bo",
        "action_xml_id": "tp_hr_attendance.action_enti_logs",
        "model": "tp.hr.attendance.enti.log",
        "name": "Nhật ký đồng bộ chấm công",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": ["/app/nguon-cham-cong"],
    },
    {
        "url": "/app/nhan-su/cham-cong/dieu-chinh",
        "action_xml_id": "tp_hr_attendance.action_review",
        "model": "tp.hr.attendance.correction",
        "name": "Xử lý điều chỉnh công",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/cham-cong/chot-ky",
        "action_xml_id": "tp_hr_attendance.action_periods",
        "model": "tp.hr.attendance.period",
        "name": "Chốt kỳ công",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/cham-cong/bang-cong",
        "action_xml_id": "tp_hr_attendance.action_days",
        "model": "tp.hr.attendance.day",
        "name": "Bảng ngày công",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/nhan-su/cham-cong/di-muon",
        "action_xml_id": "tp_hr_attendance.action_late",
        "model": "tp.hr.attendance.late",
        "name": "Tổng đi muộn theo kỳ",
        "module": "tp_hr_attendance",
        "has_detail": True,
        "aliases": [],
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
        "has_detail": True,
        "aliases": [],
    },
    {
        "url": "/app/khkd/quan-tri-du-an",
        "action_xml_id": "tp_kd_workspace.action_governance",
        "model": "tp.project.perspective",
        "name": "Quản trị dự án",
        "module": "tp_kd_workspace",
        "has_detail": True,
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
    # 7. Quản trị (quan-tri)
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
