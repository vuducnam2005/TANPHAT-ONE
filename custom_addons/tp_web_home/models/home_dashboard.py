# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Permission-checked server-side data adapters for TANPHAT ONE Home (`tp_web_home`).

Design guarantees (UI-HOME-006 & UI-HOME-007):
1. Zero circular dependencies: `tp_web_home` continues to depend only on `web` and
   `tp_web_login`. Installed business modules (`tp_admin_delegation`, `tp_hr_workspace`,
   `tp_hr_attendance`, `tp_request`, `tp_personal_tools`, `tp_equipment`,
   `tp_kd_workspace`, `tp_digital_office`, `tp_enterprise_governance`) are discovered
   dynamically via `self.env`.
2. Strictly read-only: Home queries never bootstrap personal stages, never create punches,
   never mutate records, and never call external syncs (e.g. ENTI).
3. Two server-verified Home modes sharing one visual design:
   - `admin`: Original Admin (`group_original_admin`) or live Granted Full Admin
     (`tp.admin.delegation` active in current company). Shows executive KPIs
     (`Nhân sự`, `Yêu cầu phê duyệt`, `Công việc`, `Tồn kho`) and department task analytics.
   - `employee`: Every other active internal account (including department heads and
     business approvers, without turning Home into company-wide admin mode). Never queries
     or returns Stock KPI; shows 4 rich personal cards (`Việc chưa hoàn thành`,
     `Yêu cầu của tôi chờ duyệt`, `Lịch hẹn hôm nay`, `Chấm công hôm nay`) and personal
     daily task bar + status donut charts.
4. Backend-only identity & scope: ignores any `home_mode`, `user_id`, `employee_id`, or
   `company_id` sent by the browser; re-verifies permissions on every read and drilldown.
"""

import calendar
import logging
import re
import unicodedata
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Domain

_logger = logging.getLogger(__name__)

DEFAULT_TZ_NAME = "Asia/Ho_Chi_Minh"
WEEKDAY_VI = ("T2", "T3", "T4", "T5", "T6", "T7", "CN")

PERIOD_OPTIONS = (
    ("this_week", "Trong tuần này"),
    ("this_week_strict", "Có hạn trong tuần"),
    ("this_month", "Trong tháng này"),
    ("this_month_strict", "Có hạn trong tháng"),
    ("this_quarter", "Trong quý này"),
    ("all", "Tất cả kỳ"),
)

DONUT_BUCKETS_ADMIN = (
    ("done", "Hoàn thành", "#79BE81"),
    ("in_progress", "Đang thực hiện", "#4E7DE8"),
    ("waiting", "Chờ xử lý", "#E8AA40"),
    ("overdue", "Quá hạn", "#DD6A64"),
)

DONUT_BUCKETS_EMPLOYEE = (
    ("done", "Hoàn thành", "#79BE81"),
    ("in_progress", "Đang thực hiện", "#4E7DE8"),
    ("waiting", "Chờ xử lý / xác nhận", "#E8AA40"),
    ("overdue", "Quá hạn", "#DD6A64"),
)
UNMAPPED_BUCKET = ("unmapped", "Trạng thái khác", "#94A3B8")

CROSS_DEPT_KEY = "cross_dept"
UNASSIGNED_DEPT_KEY = "unassigned_dept"
UNDATED_DAY_KEY = "undated"

SOURCE_SHORT_LABELS = {
    "self": "Tự tạo",
    "project": "Dự án",
    "meeting": "Cuộc họp",
    "request": "Yêu cầu",
    "chat": "Trao đổi",
}


def _fold_text(value):
    text = (
        unicodedata.normalize("NFD", str(value or ""))
        .replace("đ", "d")
        .replace("Đ", "D")
    )
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text).strip().lower()


def _user_tz(env):
    tz_name = (
        env.context.get("tz")
        or env.user.tz
        or (env.company.partner_id.tz if env.company and env.company.partner_id else "")
        or DEFAULT_TZ_NAME
    )
    try:
        return ZoneInfo(tz_name), tz_name
    except (ZoneInfoNotFoundError, KeyError, ValueError):
        return ZoneInfo(DEFAULT_TZ_NAME), DEFAULT_TZ_NAME


def _local_bounds_to_utc_naive(tz, start_date, end_date_inclusive):
    start_local = datetime.combine(start_date, time.min, tzinfo=tz)
    end_local = datetime.combine(
        end_date_inclusive + timedelta(days=1), time.min, tzinfo=tz,
    )
    utc = ZoneInfo("UTC")
    return (
        start_local.astimezone(utc).replace(tzinfo=None),
        end_local.astimezone(utc).replace(tzinfo=None),
    )


def _largest_remainder_percents(counts):
    """Return integer percentages summing to 100 when total > 0 (0s when total == 0)."""
    total = sum(counts)
    if total <= 0:
        return [0 for _ in counts]
    raw = [(c * 100.0) / total for c in counts]
    floors = [int(x) for x in raw]
    remainder = 100 - sum(floors)
    order = sorted(
        range(len(counts)),
        key=lambda idx: (raw[idx] - floors[idx], counts[idx], -idx),
        reverse=True,
    )
    for idx in order[: max(0, remainder)]:
        floors[idx] += 1
    return floors


class ResUsersHomeDashboard(models.Model):
    _inherit = "res.users"

    # ------------------------------------------------------------------
    # Caller & Mode Authority Helpers (Never trusts client flags/IDs)
    # ------------------------------------------------------------------
    def _tp_home_require_internal(self):
        user = self.env.user
        if not user or not user.active or not user._is_internal():
            raise AccessError(
                self.env._("Chỉ tài khoản nội bộ đang hoạt động mới được truy cập Trang chủ."),
            )
        return user

    def _tp_home_allowed_company(self):
        """Return active allowed company strictly from session environment."""
        company = self.env.company
        allowed = self.env.user.company_ids & self.env.companies
        if allowed and company not in allowed:
            company = allowed[:1]
        return company

    def _tp_home_is_full_admin(self, user=None, company=None):
        """True ONLY for Original Admin or active Granted Full Admin in `company` (DEC-053/054)."""
        user = user or self.env.user
        company = company or self._tp_home_allowed_company()
        if hasattr(user, "_tp_is_main_admin"):
            if not user._tp_is_main_admin():
                return False
            if hasattr(user, "_tp_is_original_admin") and user._tp_is_original_admin():
                return True
            if hasattr(user, "_tp_is_granted_admin"):
                return bool(user._tp_is_granted_admin(company=company))
            return False
        return bool(user.active and not user.share and user.has_group("base.group_system"))

    def _tp_home_mode(self, user=None, company=None):
        return "admin" if self._tp_home_is_full_admin(user=user, company=company) else "employee"

    # ==================================================================
    # ADMIN MODE KPIs (1. Nhân sự, 2. Yêu cầu phê duyệt, 4. Tồn kho)
    # ==================================================================
    @api.model
    def _tp_home_kpi_hr(self, company):
        if "hr.employee" not in self.env:
            return {
                "key": "hr",
                "card_kind": "metric",
                "label": "Nhân sự",
                "status": "unconfigured",
                "count": None,
                "status_text": "Chưa cài đặt",
                "tooltip": "Phân hệ Nhân sự chưa được cài đặt trên môi trường này.",
                "can_open": False,
                "drilldown": None,
            }
        try:
            if "tp.hr.workspace" in self.env:
                ws = self.env["tp.hr.workspace"]
                is_delegated_hr = bool(
                    hasattr(ws, "_tp_delegated_hr") and ws._tp_delegated_hr(),
                )
                if self.env.user.has_group("hr.group_hr_user") or is_delegated_hr:
                    employees, domain, _st = ws._population({"status": "active"})
                    count = employees.search_count(domain)
                    return {
                        "key": "hr",
                        "card_kind": "metric",
                        "label": "Nhân sự",
                        "status": "ok",
                        "count": int(count),
                        "badge_text": "Đang làm việc",
                        "badge_kind": "neutral",
                        "tooltip": "Nhân viên đang hoạt động trong phạm vi được phép xem",
                        "can_open": True,
                        "drilldown": {"type": "rpc_action", "method": "get_tp_home_hr_drilldown_action"},
                    }
                if (
                    hasattr(ws, "_public_population")
                    and "hr.employee.public" in self.env
                    and self.env["hr.employee.public"].sudo(False).has_access("read")
                ):
                    pub_emp, domain = ws._public_population({})
                    count = pub_emp.search_count(domain)
                    return {
                        "key": "hr",
                        "card_kind": "metric",
                        "label": "Nhân sự",
                        "status": "ok",
                        "count": int(count),
                        "badge_text": "Đang làm việc",
                        "badge_kind": "neutral",
                        "tooltip": "Nhân viên đang hoạt động trong phạm vi được phép xem",
                        "can_open": True,
                        "drilldown": {"type": "rpc_action", "method": "get_tp_home_hr_drilldown_action"},
                    }

            for model_name, xmlid in (
                ("hr.employee", "hr.open_view_employee_list_my"),
                ("hr.employee.public", "hr.hr_employee_public_action"),
            ):
                if model_name in self.env:
                    Model = self.env[model_name].sudo(False)
                    if Model.has_access("read"):
                        dom = [("company_id", "=", company.id), ("active", "=", True)]
                        count = Model.search_count(dom)
                        return {
                            "key": "hr",
                            "card_kind": "metric",
                            "label": "Nhân sự",
                            "status": "ok",
                            "count": int(count),
                            "badge_text": "Đang làm việc",
                            "badge_kind": "neutral",
                            "tooltip": "Nhân viên đang hoạt động trong phạm vi được phép xem",
                            "can_open": True,
                            "drilldown": {
                                "type": "rpc_action",
                                "method": "get_tp_home_hr_drilldown_action",
                                "fallback_xmlid": xmlid,
                            },
                        }

            return {
                "key": "hr",
                "card_kind": "metric",
                "label": "Nhân sự",
                "status": "no_access",
                "count": None,
                "status_text": "Không có quyền xem",
                "tooltip": "Tài khoản chưa được cấp quyền xem danh bạ nhân sự.",
                "can_open": False,
                "drilldown": None,
            }
        except AccessError:
            return {
                "key": "hr",
                "card_kind": "metric",
                "label": "Nhân sự",
                "status": "no_access",
                "count": None,
                "status_text": "Không có quyền xem",
                "tooltip": "Tài khoản không có quyền xem dữ liệu nhân sự trong phạm vi hiện tại.",
                "can_open": False,
                "drilldown": None,
            }
        except Exception:
            _logger.exception("TP Home: failed to compute HR KPI")
            return {
                "key": "hr",
                "card_kind": "metric",
                "label": "Nhân sự",
                "status": "error",
                "count": None,
                "status_text": "Tạm lỗi nguồn",
                "tooltip": "Chưa tải được số liệu Nhân sự. Vui lòng thử làm mới.",
                "can_open": False,
                "drilldown": None,
            }

    @api.model
    def get_tp_home_hr_drilldown_action(self):
        self._tp_home_require_internal()
        company = self._tp_home_allowed_company()
        if "tp.hr.workspace" in self.env:
            ws = self.env["tp.hr.workspace"]
            is_delegated_hr = bool(
                hasattr(ws, "_tp_delegated_hr") and ws._tp_delegated_hr(),
            )
            if self.env.user.has_group("hr.group_hr_user") or is_delegated_hr:
                return ws.action_employees({"status": "active"})
            if hasattr(ws, "action_public_employees"):
                return ws.action_public_employees({})
        fallback_xmlids = {
            "hr.employee": ("tp_hr_workspace.action_employees", "hr.open_view_employee_list_my"),
            "hr.employee.public": ("tp_hr_workspace.action_directory",),
        }
        for model_name in ("hr.employee", "hr.employee.public"):
            if model_name in self.env and self.env[model_name].sudo(False).has_access("read"):
                dom = [("company_id", "=", company.id), ("active", "=", True)]
                for xmlid in fallback_xmlids.get(model_name, ()):
                    if self.env.ref(xmlid, raise_if_not_found=False):
                        action = self.env["ir.actions.actions"]._for_xml_id(xmlid)
                        action["domain"] = dom
                        return action
                return {
                    "type": "ir.actions.act_window",
                    "name": "Danh sách nhân viên",
                    "res_model": model_name,
                    "view_mode": "list,form",
                    "domain": dom,
                }
        raise AccessError(self.env._("Bạn không có quyền mở danh sách nhân sự."))

    @api.model
    def _tp_home_kpi_admin_requests(self, company):
        if "tp.request" not in self.env:
            return {
                "key": "requests",
                "card_kind": "metric",
                "label": "Yêu cầu phê duyệt",
                "status": "unconfigured",
                "count": None,
                "status_text": "Chưa cài đặt",
                "tooltip": "Phân hệ Yêu cầu phê duyệt chưa được cài đặt.",
                "can_open": False,
                "drilldown": None,
            }
        try:
            Req = self.env["tp.request"].sudo(False)
            if not Req.has_access("read"):
                return {
                    "key": "requests",
                    "card_kind": "metric",
                    "label": "Yêu cầu phê duyệt",
                    "status": "no_access",
                    "count": None,
                    "status_text": "Không có quyền xem",
                    "tooltip": "Tài khoản không có quyền xem Yêu cầu phê duyệt.",
                    "can_open": False,
                    "drilldown": None,
                }
            dom = Domain(Req._tp_mode_domain("to_approve")) & Domain("company_id", "=", company.id)
            count = Req.search_count(dom)
            return {
                "key": "requests",
                "card_kind": "metric",
                "label": "Yêu cầu phê duyệt",
                "status": "ok",
                "count": int(count),
                "role_mode": "to_approve",
                "badge_text": "Chờ bạn duyệt",
                "badge_kind": "purple",
                "tooltip": "Số hồ sơ đề nghị đã gửi đang đến lượt bạn phê duyệt (không tính bản nháp và không tính phiếu của chính bạn).",
                "can_open": True,
                "drilldown": {
                    "type": "client_action",
                    "action_xmlid": "tp_request.action_to_approve",
                    "menu_xmlid": "tp_request.menu_root",
                    "leaf_xmlid": "tp_request.menu_to_approve",
                    "request_mode": "to_approve",
                    "request_tab": "all",
                },
            }
        except AccessError:
            return {
                "key": "requests",
                "card_kind": "metric",
                "label": "Yêu cầu phê duyệt",
                "status": "no_access",
                "count": None,
                "status_text": "Không có quyền xem",
                "tooltip": "Tài khoản không có quyền xem Yêu cầu phê duyệt.",
                "can_open": False,
                "drilldown": None,
            }
        except Exception:
            _logger.exception("TP Home: failed to compute Admin Request KPI")
            return {
                "key": "requests",
                "card_kind": "metric",
                "label": "Yêu cầu phê duyệt",
                "status": "error",
                "count": None,
                "status_text": "Tạm lỗi nguồn",
                "tooltip": "Chưa tải được số liệu Yêu cầu phê duyệt. Vui lòng thử làm mới.",
                "can_open": False,
                "drilldown": None,
            }

    @api.model
    def _tp_home_kpi_stock(self, company):
        if "maintenance.equipment" not in self.env:
            return {
                "key": "stock",
                "card_kind": "metric",
                "label": "Tồn kho",
                "status": "unconfigured",
                "count": None,
                "status_text": "Chưa cài đặt",
                "tooltip": "Phân hệ Kho thiết bị chưa được cài đặt.",
                "can_open": False,
                "drilldown": None,
            }
        try:
            Equipment = self.env["maintenance.equipment"].sudo(False)
            if not Equipment.has_access("read"):
                return {
                    "key": "stock",
                    "card_kind": "metric",
                    "label": "Tồn kho",
                    "status": "no_access",
                    "count": None,
                    "status_text": "Không có quyền xem",
                    "tooltip": "Tài khoản của bạn không có quyền xem số liệu Kho thiết bị.",
                    "can_open": False,
                    "drilldown": None,
                }

            if hasattr(Equipment, "tp_main_summary"):
                summary = Equipment.tp_main_summary()
                stock_count = int(summary.get("stock", 0))
                free_count = int(summary.get("free", 0))
                return {
                    "key": "stock",
                    "card_kind": "metric",
                    "label": "Tồn kho",
                    "status": "ok",
                    "count": stock_count,
                    "free_count": free_count,
                    "badge_text": f"Sẵn sàng: {free_count}",
                    "badge_kind": "amber",
                    "tooltip": (
                        f"Thiết bị đang quản lý lưu tại kho và chưa có người giữ ({stock_count} máy; "
                        f"trong đó sẵn sàng cấp phát ngay: {free_count} máy)."
                    ),
                    "can_open": True,
                    "drilldown": {"type": "rpc_action", "method": "get_tp_home_stock_drilldown_action"},
                }

            count = Equipment.search_count([("company_id", "in", [False, company.id])])
            return {
                "key": "stock",
                "card_kind": "metric",
                "label": "Tồn kho",
                "status": "ok",
                "count": int(count),
                "badge_text": "Hiện tại",
                "badge_kind": "neutral",
                "tooltip": "Thiết bị trong phạm vi được phép xem.",
                "can_open": True,
                "drilldown": {"type": "rpc_action", "method": "get_tp_home_stock_drilldown_action"},
            }
        except AccessError:
            return {
                "key": "stock",
                "card_kind": "metric",
                "label": "Tồn kho",
                "status": "no_access",
                "count": None,
                "status_text": "Không có quyền xem",
                "tooltip": "Tài khoản của bạn không có quyền xem số liệu Kho thiết bị.",
                "can_open": False,
                "drilldown": None,
            }
        except Exception:
            _logger.exception("TP Home: failed to compute Stock KPI")
            return {
                "key": "stock",
                "card_kind": "metric",
                "label": "Tồn kho",
                "status": "error",
                "count": None,
                "status_text": "Tạm lỗi nguồn",
                "tooltip": "Chưa tải được số liệu Tồn kho. Vui lòng thử làm mới.",
                "can_open": False,
                "drilldown": None,
            }

    @api.model
    def get_tp_home_stock_drilldown_action(self):
        user = self._tp_home_require_internal()
        company = self._tp_home_allowed_company()
        if not self._tp_home_is_full_admin(user=user, company=company):
            if "maintenance.equipment" not in self.env:
                raise AccessError(self.env._("Bạn không có quyền truy cập Kho thiết bị."))
            Equipment = self.env["maintenance.equipment"].sudo(False)
            Equipment.check_access("read")
            if hasattr(Equipment, "tp_main_summary"):
                Equipment.tp_main_summary()
            else:
                raise AccessError(self.env._("Bạn không có quyền xem thống kê Tồn kho."))
        if "maintenance.equipment" not in self.env:
            raise AccessError(self.env._("Phân hệ Kho thiết bị chưa được cài đặt."))
        Equipment = self.env["maintenance.equipment"].sudo(False)
        Equipment.check_access("read")
        if hasattr(Equipment, "tp_main_summary"):
            Equipment.tp_main_summary()
            action = self.env["ir.actions.actions"]._for_xml_id("tp_equipment.action_equipment")
            base_ctx = action.get("context")
            if isinstance(base_ctx, str):
                base_ctx = {}
            action["context"] = {
                **(base_ctx or {}),
                "tp_filter_profile": "equipment_main",
                "tp_eq_leaf": "tp_equipment.menu_equipment_all",
                "search_default_seg_stock": 1,
                "create": False,
            }
            return action
        for xmlid in (
            "tp_equipment.action_equipment_stock",
            "tp_equipment.action_equipment",
            "maintenance.hr_equipment_action",
        ):
            if self.env.ref(xmlid, raise_if_not_found=False):
                action = self.env["ir.actions.actions"]._for_xml_id(xmlid)
                action["domain"] = [("company_id", "in", [False, company.id])]
                return action
        return {
            "type": "ir.actions.act_window",
            "name": "Thiết bị tồn kho",
            "res_model": "maintenance.equipment",
            "view_mode": "list,form",
            "domain": [("company_id", "in", [False, company.id])],
        }

    # ==================================================================
    # EMPLOYEE MODE PERSONAL CARDS (Ô 2, Ô 3, Ô 4; Ô 1 shares task dataset)
    # ==================================================================
    @api.model
    def _tp_home_kpi_employee_requests(self, company):
        """Ô 2 — Yêu cầu của tôi chờ duyệt (strictly caller's own submitted pending requests)."""
        uid = self.env.uid
        if "tp.request" in self.env:
            try:
                Req = self.env["tp.request"].sudo(False)
                if not Req.has_access("read"):
                    return {
                        "key": "emp_requests",
                        "card_kind": "metric",
                        "label": "Yêu cầu của tôi chờ duyệt",
                        "status": "no_access",
                        "count": None,
                        "status_text": "Chưa được cấp quyền",
                        "tooltip": "Tài khoản chưa có quyền truy cập phân hệ Yêu cầu phê duyệt.",
                        "can_open": False,
                        "drilldown": None,
                    }
                # Only submitted pending requests of the caller in the allowed company.
                # Excludes draft, withdrawn, returned, rejected, and approved (even if execution_state is open).
                # Deduplicates attendance_correction_id so 1-1 attendance bridge is never counted twice.
                recs = Req.search(
                    [
                        ("company_id", "=", company.id),
                        ("requester_user_id", "=", uid),
                        ("approval_state", "=", "pending"),
                    ],
                )
                seen_corr_ids = set()
                unique_ids = []
                has_corr_field = "attendance_correction_id" in Req._fields
                for r in recs:
                    corr_id = r.attendance_correction_id.id if (has_corr_field and r.attendance_correction_id) else 0
                    if corr_id:
                        if corr_id in seen_corr_ids:
                            continue
                        seen_corr_ids.add(corr_id)
                    unique_ids.append(r.id)
                count = len(unique_ids)
                return {
                    "key": "emp_requests",
                    "card_kind": "metric",
                    "label": "Yêu cầu của tôi chờ duyệt",
                    "status": "ok",
                    "count": int(count),
                    "role_mode": "mine_pending",
                    "badge_text": "Đang chờ duyệt" if count > 0 else "Không có phiếu chờ",
                    "badge_kind": "purple" if count > 0 else "neutral",
                    "tooltip": (
                        "Số phiếu đề nghị của chính bạn đã gửi và đang trong bước chờ phê duyệt "
                        "(không tính nháp, thu hồi, trả lại hoặc phiếu đã duyệt đang chờ thực hiện)."
                    ),
                    "can_open": True,
                    "drilldown": {
                        "type": "client_action",
                        "action_xmlid": "tp_request.action_mine",
                        "menu_xmlid": "tp_request.menu_root",
                        "leaf_xmlid": "tp_request.menu_mine",
                        "request_mode": "mine",
                        "request_tab": "pending",
                    },
                }
            except AccessError:
                return {
                    "key": "emp_requests",
                    "card_kind": "metric",
                    "label": "Yêu cầu của tôi chờ duyệt",
                    "status": "no_access",
                    "count": None,
                    "status_text": "Chưa được cấp quyền",
                    "tooltip": "Tài khoản chưa có quyền xem Yêu cầu phê duyệt.",
                    "can_open": False,
                    "drilldown": None,
                }
            except Exception:
                _logger.exception("TP Home: failed to compute Employee Request KPI")
                return {
                    "key": "emp_requests",
                    "card_kind": "metric",
                    "label": "Yêu cầu của tôi chờ duyệt",
                    "status": "error",
                    "count": None,
                    "status_text": "Tạm lỗi nguồn",
                    "tooltip": "Chưa tải được số lượng yêu cầu của bạn. Vui lòng thử làm mới.",
                    "can_open": False,
                    "drilldown": None,
                }

        # Fallback when tp_request is not installed on minimal environments
        if "tp.hr.attendance.correction" in self.env:
            try:
                Corr = self.env["tp.hr.attendance.correction"].sudo(False)
                if Corr.has_access("read"):
                    count = Corr.search_count(
                        [
                            ("company_id", "=", company.id),
                            ("employee_id.user_id", "=", uid),
                            ("state", "=", "submitted"),
                        ],
                    )
                    return {
                        "key": "emp_requests",
                        "card_kind": "metric",
                        "label": "Yêu cầu của tôi chờ duyệt",
                        "status": "ok",
                        "count": int(count),
                        "role_mode": "mine_pending",
                        "badge_text": "Đang chờ duyệt" if count > 0 else "Không có phiếu chờ",
                        "badge_kind": "purple" if count > 0 else "neutral",
                        "tooltip": "Số đề nghị điều chỉnh công đã gửi đang chờ phê duyệt.",
                        "can_open": True,
                        "drilldown": {
                            "type": "client_action",
                            "action_xmlid": "tp_hr_attendance.action_my_requests",
                            "menu_xmlid": "tp_hr_attendance.menu_root",
                        },
                    }
            except Exception:
                _logger.exception("TP Home: failed to compute fallback correction requests")

        return {
            "key": "emp_requests",
            "card_kind": "metric",
            "label": "Yêu cầu của tôi chờ duyệt",
            "status": "unconfigured",
            "count": None,
            "status_text": "Chưa cài đặt",
            "tooltip": "Phân hệ Yêu cầu phê duyệt chưa được cài đặt.",
            "can_open": False,
            "drilldown": None,
        }

    def _tp_home_collect_today_calendar_events(self):
        """Return `(valid_events_sorted, today_local, tz, tz_name)` strictly for the caller's own calendar today.

        Rules (Section 4.3):
        - Local day in caller's timezone.
        - All-day events matched strictly by `[start_date, stop_date]` containing `today_local`.
        - Timed & overnight events crossing midnight matched by `start < stop_utc` and `stop > start_utc`
          (plus zero-duration reminders at `[start_utc, stop_utc)`).
        - Recurring events evaluated on their real `calendar.event` occurrence rows.
        - Excludes archived (`active=False`), declined invitations (`my_att.state == 'declined'`),
          and private events of other users (`_check_private_event_conditions()`).
        - Never includes company/colleague events where caller is neither organizer nor participant.
        """
        tz, tz_name = _user_tz(self.env)
        today_local = datetime.now(tz).date()
        start_utc, stop_utc = _local_bounds_to_utc_naive(tz, today_local, today_local)
        uid = self.env.uid
        my_pid = self.env.user.partner_id.id

        Event = self.env["calendar.event"].sudo(False).with_context(active_test=True)
        if not Event.has_access("read"):
            raise AccessError(self.env._("Tài khoản không có quyền xem Lịch làm việc."))

        allday_overlap = (
            Domain("allday", "=", True)
            & Domain("start_date", "<=", today_local)
            & Domain("stop_date", ">=", today_local)
        )
        timed_overlap = (
            Domain("allday", "=", False)
            & Domain("start", "<", stop_utc)
            & (
                Domain("stop", ">", start_utc)
                | (Domain("start", ">=", start_utc) & Domain("stop", "=", start_utc))
            )
        )
        participant_dom = Domain("partner_ids", "in", [my_pid]) | Domain("user_id", "=", uid)
        ev_dom = Domain("active", "=", True) & participant_dom & (allday_overlap | timed_overlap)

        candidates = Event.search(ev_dom, order="allday desc, start asc, id asc", limit=200)
        valid_events = []
        seen_ids = set()
        for ev in candidates:
            if ev.id in seen_ids:
                continue
            if hasattr(ev, "_check_private_event_conditions") and ev._check_private_event_conditions():
                continue
            my_att = ev.attendee_ids.filtered(lambda a: a.partner_id.id == my_pid)[:1]
            if my_att and my_att.state == "declined":
                continue
            seen_ids.add(ev.id)
            valid_events.append(ev)
        return valid_events, today_local, tz, tz_name

    @api.model
    def _tp_home_kpi_employee_calendar(self):
        """Ô 3 — Lịch hẹn hôm nay (personal meetings & events today)."""
        if "calendar.event" not in self.env:
            return {
                "key": "emp_calendar",
                "card_kind": "metric",
                "label": "Lịch hẹn hôm nay",
                "status": "unconfigured",
                "count": None,
                "status_text": "Chưa cài đặt",
                "tooltip": "Phân hệ Lịch làm việc chưa được cài đặt.",
                "can_open": False,
                "drilldown": None,
            }
        try:
            events, today_local, tz, tz_name = self._tp_home_collect_today_calendar_events()
            count = len(events)
            now_utc = fields.Datetime.now()
            badge_text = "Trống lịch"
            badge_kind = "neutral"
            if count > 0:
                badge_kind = "green"
                upcoming_timed = [
                    ev for ev in events if not ev.allday and ev.stop and ev.stop >= now_utc
                ]
                if upcoming_timed:
                    st_loc = upcoming_timed[0].start.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                    if st_loc.date() < today_local:
                        badge_text = "Đang diễn ra"
                    else:
                        badge_text = f"Lịch {st_loc.strftime('%H:%M')}"
                elif any(ev.allday for ev in events):
                    badge_text = "Cả ngày"
                else:
                    badge_text = "Trong hôm nay"

            return {
                "key": "emp_calendar",
                "card_kind": "metric",
                "label": "Lịch hẹn hôm nay",
                "status": "ok",
                "count": int(count),
                "badge_text": badge_text,
                "badge_kind": badge_kind,
                "tooltip": (
                    f"Sự kiện và cuộc họp hôm nay ({today_local.strftime('%d/%m/%Y')} · {tz_name}) "
                    "mà bạn là người chủ trì hoặc tham gia (không tính lịch đã hủy hoặc lời mời đã từ chối)."
                ),
                "can_open": True,
                "drilldown": {
                    "type": "rpc_action",
                    "method": "get_tp_home_calendar_drilldown_action",
                },
            }
        except AccessError:
            return {
                "key": "emp_calendar",
                "card_kind": "metric",
                "label": "Lịch hẹn hôm nay",
                "status": "no_access",
                "count": None,
                "status_text": "Chưa được cấp quyền",
                "tooltip": "Tài khoản chưa được cấp quyền xem Lịch làm việc.",
                "can_open": False,
                "drilldown": None,
            }
        except Exception:
            _logger.exception("TP Home: failed to compute Employee Calendar KPI")
            return {
                "key": "emp_calendar",
                "card_kind": "metric",
                "label": "Lịch hẹn hôm nay",
                "status": "error",
                "count": None,
                "status_text": "Tạm lỗi nguồn",
                "tooltip": "Chưa tải được lịch hẹn hôm nay. Vui lòng thử làm mới.",
                "can_open": False,
                "drilldown": None,
            }

    @api.model
    def get_tp_home_calendar_drilldown_action(self):
        """Open Lịch làm việc focused at today, filtered strictly to caller's today events."""
        self._tp_home_require_internal()
        if "calendar.event" not in self.env:
            raise AccessError(self.env._("Phân hệ Lịch làm việc chưa được cài đặt."))
        events, today_local, _tz, _tz_name = self._tp_home_collect_today_calendar_events()
        event_ids = [ev.id for ev in events]
        title = f"Lịch hẹn hôm nay · {today_local.strftime('%d/%m/%Y')}"
        ctx = {
            "default_mode": "day",
            "initial_date": today_local.isoformat(),
        }
        if self.env.ref("calendar.action_calendar_event", raise_if_not_found=False):
            action = self.env["ir.actions.actions"]._for_xml_id("calendar.action_calendar_event")
            base_ctx = action.get("context") if isinstance(action.get("context"), dict) else {}
            action.update(
                name=title,
                res_model="calendar.event",
                view_mode="calendar,list,form",
                views=[(False, "calendar"), (False, "list"), (False, "form")],
                domain=[("id", "in", event_ids)],
                context={**base_ctx, **ctx},
            )
            return action
        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": "calendar.event",
            "view_mode": "calendar,list,form",
            "views": [(False, "calendar"), (False, "list"), (False, "form")],
            "domain": [("id", "in", event_ids)],
            "context": ctx,
        }

    @api.model
    def _tp_home_kpi_employee_attendance(self, company):
        """Ô 4 — Chấm công hôm nay (status card reusing canonical `tp.hr.attendance.day._tp_presence`).

        Guarantees (Section 4.4):
        - Never creates punches and never triggers ENTI HTTP sync.
        - Resolves employee strictly via `user_id == env.uid` in `company` (never matches by name).
        - Evaluates strictly `today` (never shows yesterday's attendance as today).
        - Distinguishes working, out_recorded, missing, review, leave, rest, no_punch, absent, no_source, off,
          and unlinked_employee without inventing a separate classification formula.
        """
        if "tp.hr.attendance.day" not in self.env or "tp.hr.attendance.correction" not in self.env:
            return {
                "key": "emp_attendance",
                "card_kind": "status",
                "label": "Chấm công hôm nay",
                "status": "unconfigured",
                "count": None,
                "display_text": "Chưa cài đặt",
                "sub_text": "Phân hệ Chấm công chưa được kích hoạt",
                "badge_text": "",
                "badge_kind": "neutral",
                "tooltip": "Phân hệ Chấm công chưa được cài đặt trên môi trường này.",
                "can_open": False,
                "drilldown": None,
            }
        try:
            Day = self.env["tp.hr.attendance.day"].sudo(False)
            if not Day.has_access("read"):
                return {
                    "key": "emp_attendance",
                    "card_kind": "status",
                    "label": "Chấm công hôm nay",
                    "status": "no_access",
                    "count": None,
                    "display_text": "Chưa được cấp quyền",
                    "sub_text": "",
                    "badge_text": "",
                    "badge_kind": "neutral",
                    "tooltip": "Tài khoản chưa có quyền xem ngày công cá nhân.",
                    "can_open": False,
                    "drilldown": None,
                }

            tz, _tz_name = _user_tz(self.env)
            today = datetime.now(tz).date()
            employee = self.env["tp.hr.attendance.correction"]._tp_own_employee(company)
            drilldown = {
                "type": "client_action",
                "action_xmlid": "tp_hr_attendance.action_mine",
                "menu_xmlid": "tp_hr_attendance.menu_root",
                "leaf_xmlid": "tp_hr_attendance.menu_mine",
                "attendance_today": today.isoformat(),
            }

            if not employee:
                return {
                    "key": "emp_attendance",
                    "card_kind": "status",
                    "label": "Chấm công hôm nay",
                    "status": "unlinked_employee",
                    "count": None,
                    "display_text": "Chưa xác định hồ sơ nhân viên",
                    "sub_text": "Liên hệ người quản lý tài khoản / HR để gắn hồ sơ",
                    "badge_text": "",
                    "badge_kind": "amber",
                    "tooltip": (
                        "Tài khoản đang đăng nhập chưa được gắn với hồ sơ nhân viên trong công ty hiện tại. "
                        "Vui lòng liên hệ quản trị viên hoặc bộ phận Nhân sự để gắn hồ sơ."
                    ),
                    "can_open": True,
                    "drilldown": drilldown,
                }

            cells, _has_leave = Day._tp_presence(company, [employee.id], today, today, today)
            cell = cells.get((employee.id, today)) or {
                "state": "no_source",
                "in": "",
                "out": "",
                "label": "Chưa có dữ liệu",
                "day_id": False,
            }
            st = cell.get("state") or "no_source"
            in_str = str(cell.get("in") or "").strip()
            out_str = str(cell.get("out") or "").strip()

            updated_short = ""
            if cell.get("day_id"):
                day_rec = Day.browse(cell["day_id"]).exists()
                if day_rec and day_rec.source_updated_at:
                    stamp_loc = day_rec.source_updated_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                    updated_short = stamp_loc.strftime("%H:%M %d/%m")
            if not updated_short and hasattr(Day, "_tp_source_strip"):
                strip = Day._tp_source_strip(company, today)
                updated_short = strip.get("updated_at") or ""

            if st == "working":
                display_text = "Đang làm"
                time_summary = f"Vào: {in_str}" if in_str else "Chờ giờ ra"
                badge_kind = "green"
            elif st == "out_recorded":
                display_text = "Đã về" if (in_str and out_str) else "Đủ vào/ra"
                time_summary = f"{in_str} – {out_str}" if (in_str and out_str) else "Đủ giờ vào/ra"
                badge_kind = "green"
            elif st == "missing":
                if in_str and not out_str:
                    display_text = "Thiếu giờ ra"
                    time_summary = f"Vào: {in_str}"
                elif out_str and not in_str:
                    display_text = "Thiếu giờ vào"
                    time_summary = f"Ra: {out_str}"
                else:
                    display_text = "Thiếu giờ vào/ra"
                    time_summary = "Cần bổ sung"
                badge_kind = "amber"
            elif st == "review":
                display_text = "Cần kiểm tra"
                time_summary = f"{in_str} – {out_str}".strip(" –") or "Kiểm tra lượt chấm"
                badge_kind = "amber"
            elif st == "leave":
                display_text = "Nghỉ đã xác nhận"
                time_summary = "Theo đơn đã duyệt"
                badge_kind = "purple"
            elif st == "rest":
                display_text = "Nghỉ theo lịch"
                time_summary = "Ngày nghỉ ca"
                badge_kind = "neutral"
            elif st == "no_punch":
                display_text = "Chưa chấm công"
                time_summary = "Chưa có giờ vào"
                badge_kind = "neutral"
            elif st == "absent":
                display_text = "Vắng theo lịch"
                time_summary = "Không có lượt chấm"
                badge_kind = "red"
            elif st == "off":
                display_text = "Ngoài kỳ làm việc"
                time_summary = "Theo hợp đồng"
                badge_kind = "neutral"
            else:
                display_text = "Chưa có dữ liệu"
                time_summary = "Chờ đồng bộ nguồn"
                badge_kind = "neutral"

            tooltip_parts = [
                f"Chấm công hôm nay ({today.strftime('%d/%m/%Y')}): {display_text}",
            ]
            if in_str or out_str:
                tooltip_parts.append(f"Giờ ghi nhận: {in_str or '—'} – {out_str or '—'}")
            if updated_short:
                tooltip_parts.append(f"Cập nhật nguồn: {updated_short}")
            tooltip_parts.append("Bấm để mở Công của tôi tại ngày hôm nay.")

            return {
                "key": "emp_attendance",
                "card_kind": "status",
                "label": "Chấm công hôm nay",
                "status": "ok",
                "attendance_state": st,
                "count": None,
                "display_text": display_text,
                "in_time": in_str,
                "out_time": out_str,
                "updated_at": updated_short,
                "sub_text": time_summary,
                "badge_text": time_summary,
                "badge_kind": badge_kind,
                "tooltip": " · ".join(tooltip_parts),
                "can_open": True,
                "drilldown": drilldown,
            }
        except AccessError:
            return {
                "key": "emp_attendance",
                "card_kind": "status",
                "label": "Chấm công hôm nay",
                "status": "no_access",
                "count": None,
                "display_text": "Chưa được cấp quyền",
                "sub_text": "",
                "badge_text": "",
                "badge_kind": "neutral",
                "tooltip": "Tài khoản không có quyền xem dữ liệu công cá nhân.",
                "can_open": False,
                "drilldown": None,
            }
        except Exception:
            _logger.exception("TP Home: failed to compute Employee Attendance card")
            return {
                "key": "emp_attendance",
                "card_kind": "status",
                "label": "Chấm công hôm nay",
                "status": "error",
                "count": None,
                "display_text": "Tạm lỗi nguồn",
                "sub_text": "Vui lòng thử làm mới",
                "badge_text": "",
                "badge_kind": "neutral",
                "tooltip": "Chưa tải được trạng thái chấm công hôm nay.",
                "can_open": False,
                "drilldown": None,
            }

    # ==================================================================
    # SHARED TASK DATASET & ANALYTICS (Admin Mode vs Employee Personal Mode)
    # ==================================================================
    def _tp_home_my_work_domain(self, Task, company):
        uid = self.env.uid
        if hasattr(Task, "_tp_my_work_domain"):
            dom = Task._tp_my_work_domain(include_archived=False) & Domain(
                "state", "!=", "1_canceled",
            )
        else:
            non_proj = (
                Domain("project_id", "=", False)
                & Domain("parent_id", "=", False)
                & Domain("user_ids", "in", [uid])
            )
            proj = Domain("project_id", "!=", False) & Domain("user_ids", "in", [uid])
            dom = Domain("active", "=", True) & Domain("state", "!=", "1_canceled") & (non_proj | proj)
            if "is_template" in Task._fields:
                dom &= Domain("is_template", "=", False)
        return dom & Domain("company_id", "in", [False, company.id])

    def _tp_home_period_bounds(self, period_key, default_key, tz, today_local):
        valid_keys = {k for k, _ in PERIOD_OPTIONS}
        pkey = period_key if period_key in valid_keys else default_key
        if pkey == "all":
            return pkey, "Tất cả kỳ", "Tất cả kỳ", None, None, None, None, True
        if pkey in ("this_week", "this_week_strict"):
            start_d = today_local - timedelta(days=today_local.weekday())
            end_d = start_d + timedelta(days=6)
            s_utc, e_utc = _local_bounds_to_utc_naive(tz, start_d, end_d)
            if pkey == "this_week_strict":
                label = f"Có hạn tuần ({start_d.strftime('%d/%m')}–{end_d.strftime('%d/%m')})"
                short_badge = "Có hạn trong tuần"
                return pkey, label, short_badge, start_d, end_d, s_utc, e_utc, False
            label = f"Tuần này ({start_d.strftime('%d/%m')}–{end_d.strftime('%d/%m')})"
            short_badge = "Trong tuần này"
            return pkey, label, short_badge, start_d, end_d, s_utc, e_utc, True
        if pkey == "this_quarter":
            q_idx = (today_local.month - 1) // 3
            start_m = q_idx * 3 + 1
            end_m = start_m + 2
            last_day = calendar.monthrange(today_local.year, end_m)[1]
            start_d = date(today_local.year, start_m, 1)
            end_d = date(today_local.year, end_m, last_day)
            label = f"Quý {q_idx + 1}/{today_local.year}"
            short_badge = "Trong quý này"
            s_utc, e_utc = _local_bounds_to_utc_naive(tz, start_d, end_d)
            return pkey, label, short_badge, start_d, end_d, s_utc, e_utc, False

        # this_month or this_month_strict
        last_day = calendar.monthrange(today_local.year, today_local.month)[1]
        start_d = date(today_local.year, today_local.month, 1)
        end_d = date(today_local.year, today_local.month, last_day)
        s_utc, e_utc = _local_bounds_to_utc_naive(tz, start_d, end_d)
        if pkey == "this_month_strict":
            label = f"Có hạn tháng {today_local.strftime('%m/%Y')}"
            short_badge = "Có hạn trong tháng"
            return pkey, label, short_badge, start_d, end_d, s_utc, e_utc, False
        label = f"Tháng {today_local.strftime('%m/%Y')}"
        short_badge = "Trong tháng này"
        return pkey, label, short_badge, start_d, end_d, s_utc, e_utc, True

    def _tp_home_classify_task_bucket(self, task, now_utc):
        """Non-overlapping business state classification (never inferred from personal Kanban column)."""
        has_exec_field = "tp_exec_report_state" in task._fields
        exec_st = task.tp_exec_report_state if has_exec_field else False
        st = task.state or "01_in_progress"
        req_verify = bool(
            hasattr(task, "_tp_requires_verification") and task._tp_requires_verification(),
        )

        # 1. Completed: tasks reported done awaiting verification NEVER count as completed!
        if exec_st == "reported_done":
            is_done = False
        elif req_verify and has_exec_field:
            is_done = bool(exec_st == "verified" or st in ("1_done", "03_approved"))
        else:
            is_done = bool(st in ("1_done", "03_approved") or exec_st == "verified")

        if is_done:
            return "done"

        # 2. Uncompleted & past deadline -> Overdue
        if task.date_deadline and task.date_deadline < now_utc:
            return "overdue"

        # 3. Waiting / Changes requested / Reported done awaiting verification -> Waiting
        if st in ("04_waiting_normal", "02_changes_requested") or exec_st == "reported_done":
            return "waiting"

        # 4. Active In Progress
        if st == "01_in_progress":
            return "in_progress"

        return "unmapped"

    def _tp_home_attribute_task_departments(self, tasks, company):
        """Attribute each task to exactly ONE department transparently (Admin Mode)."""
        if not tasks:
            return {}, {}

        has_kd_resp = "kd_responsible_id" in tasks._fields
        candidate_uids = set(tasks.mapped("user_ids").ids)
        if has_kd_resp:
            candidate_uids.update(tasks.mapped("kd_responsible_id").ids)

        emp_dept_by_uid = {}
        dept_names = {
            CROSS_DEPT_KEY: "Liên phòng ban",
            UNASSIGNED_DEPT_KEY: "Chưa gắn phòng ban",
        }
        dept_seq = {
            CROSS_DEPT_KEY: (999990, 999990),
            UNASSIGNED_DEPT_KEY: (999995, 999995),
        }

        if candidate_uids and "hr.employee" in self.env:
            emps = (
                self.env["hr.employee"]
                .sudo()
                .with_context(version_id=False)
                .search(
                    [
                        ("user_id", "in", list(candidate_uids)),
                        ("company_id", "=", company.id),
                        ("active", "=", True),
                    ],
                )
            )
            for emp in emps:
                dept = emp.department_id
                if dept and emp.user_id:
                    dkey = str(dept.id)
                    emp_dept_by_uid[emp.user_id.id] = dkey
                    dept_names[dkey] = dept.name
                    seq = getattr(dept, "tp_sequence", 100) or 100
                    dept_seq[dkey] = (seq, dept.id)

        task_dept_map = {}
        for task in tasks:
            chosen_key = None
            proj = task.project_id
            if proj and "tp_department_id" in proj._fields:
                pdept = proj.sudo().tp_department_id
                if pdept and (not pdept.company_id or pdept.company_id == company):
                    chosen_key = str(pdept.id)
                    dept_names[chosen_key] = pdept.name
                    seq = getattr(pdept, "tp_sequence", 100) or 100
                    dept_seq[chosen_key] = (seq, pdept.id)

            if not chosen_key and has_kd_resp and task.kd_responsible_id:
                chosen_key = emp_dept_by_uid.get(task.kd_responsible_id.id)

            if not chosen_key:
                assignee_depts = {
                    emp_dept_by_uid[u.id]
                    for u in task.user_ids
                    if u.id in emp_dept_by_uid
                }
                if len(assignee_depts) == 1:
                    chosen_key = next(iter(assignee_depts))
                elif len(assignee_depts) > 1:
                    chosen_key = CROSS_DEPT_KEY
                else:
                    chosen_key = UNASSIGNED_DEPT_KEY

            task_dept_map[task.id] = chosen_key

        meta_by_dept = {
            k: {
                "key": k,
                "id": int(k) if k.isdigit() else k,
                "name": dept_names[k],
                "sort_key": dept_seq.get(k, (500, 500)),
            }
            for k in set(task_dept_map.values())
        }
        return task_dept_map, meta_by_dept

    def _tp_home_build_employee_day_bars(self, tasks, bucket_by_task, task_day_map, start_d, end_d):
        """Build personal daily stacked bar rows (`Công việc của tôi theo ngày`, Section 7.1).

        - Tasks with deadlines map strictly to their local deadline date (`YYYY-MM-DD`).
        - Tasks without deadlines NEVER get assigned to today; if present, they appear in
          an explicit `'Chưa đặt hạn'` bar (`day_key = 'undated'`).
        - When `total == 0`, returns `[]` so the UI renders a clean empty state.
        - When `total > 0` and `[start_d, end_d]` is at most 31 days (e.g. `this_week` or `this_month`),
          includes every real calendar day in `[start_d, end_d]` with valid `0` counts on days without tasks.
        - When `[start_d, end_d]` is unbounded or > 31 days, shows chronological dates that have tasks.
        """
        if not tasks:
            return []

        by_day = {}
        for t in tasks:
            dkey = task_day_map[t.id]
            by_day.setdefault(dkey, []).append(t)

        rows = []
        if start_d and end_d and (end_d - start_d).days <= 31:
            span_days = (end_d - start_d).days + 1
            is_short_week = span_days <= 7
            for offset in range(span_days):
                cur_d = start_d + timedelta(days=offset)
                d_iso = cur_d.isoformat()
                d_tasks = by_day.get(d_iso, [])
                done_cnt = sum(1 for t in d_tasks if bucket_by_task[t.id] == "done")
                open_cnt = len(d_tasks) - done_cnt
                lbl = (
                    f"{WEEKDAY_VI[cur_d.weekday()]} {cur_d.strftime('%d/%m')}"
                    if is_short_week
                    else cur_d.strftime("%d/%m")
                )
                rows.append(
                    {
                        "day_key": d_iso,
                        "day_label": lbl,
                        "full_label": f"{WEEKDAY_VI[cur_d.weekday()]} {cur_d.strftime('%d/%m/%Y')}",
                        "done_count": done_cnt,
                        "incomplete_count": open_cnt,
                        "total_count": len(d_tasks),
                    },
                )
        else:
            dated_keys = sorted(k for k in by_day if k != UNDATED_DAY_KEY)
            for d_iso in dated_keys:
                cur_d = date.fromisoformat(d_iso)
                d_tasks = by_day[d_iso]
                done_cnt = sum(1 for t in d_tasks if bucket_by_task[t.id] == "done")
                open_cnt = len(d_tasks) - done_cnt
                rows.append(
                    {
                        "day_key": d_iso,
                        "day_label": cur_d.strftime("%d/%m"),
                        "full_label": f"{WEEKDAY_VI[cur_d.weekday()]} {cur_d.strftime('%d/%m/%Y')}",
                        "done_count": done_cnt,
                        "incomplete_count": open_cnt,
                        "total_count": len(d_tasks),
                    },
                )

        if UNDATED_DAY_KEY in by_day:
            u_tasks = by_day[UNDATED_DAY_KEY]
            done_cnt = sum(1 for t in u_tasks if bucket_by_task[t.id] == "done")
            open_cnt = len(u_tasks) - done_cnt
            rows.append(
                {
                    "day_key": UNDATED_DAY_KEY,
                    "day_label": "Chưa đặt hạn",
                    "full_label": "Công việc chưa đặt ngày hạn",
                    "done_count": done_cnt,
                    "incomplete_count": open_cnt,
                    "total_count": len(u_tasks),
                },
            )
        return rows

    def _tp_home_collect_task_dataset(self, params=None, home_mode=None, company=None):
        """Return validated filter state and classified task records for KPI + Charts + Drilldown."""
        params = dict(params or {})
        company = company or self._tp_home_allowed_company()
        home_mode = home_mode or self._tp_home_mode(company=company)

        Task = self.env["project.task"].sudo(False).with_context(active_test=True)
        if not Task.has_access("read"):
            raise AccessError(self.env._("Tài khoản không có quyền xem công việc."))

        tz, tz_name = _user_tz(self.env)
        today_local = datetime.now(tz).date()
        now_utc = fields.Datetime.now()

        is_admin_mode = home_mode == "admin"
        requested_scope = str(params.get("task_scope") or "").strip()
        if is_admin_mode:
            scope_key = requested_scope if requested_scope in ("managed", "my_work") else "managed"
            scope_options = [
                {"key": "managed", "label": "Phạm vi quản lý"},
                {"key": "my_work", "label": "Công việc của tôi"},
            ]
        else:
            # Employee mode ALWAYS uses personal task scope on Home (Section 1, 4.1, 7)
            scope_key = "my_work"
            scope_options = [{"key": "my_work", "label": "Công việc của tôi"}]

        my_dom = self._tp_home_my_work_domain(Task, company)
        if is_admin_mode and scope_key == "managed":
            proj_dom = (
                Domain("active", "=", True)
                & Domain("state", "!=", "1_canceled")
                & Domain("project_id", "!=", False)
                & Domain("company_id", "in", [False, company.id])
            )
            if "is_template" in Task._fields:
                proj_dom &= Domain("is_template", "=", False)
            scope_dom = proj_dom | my_dom
        else:
            scope_dom = my_dom

        default_period = "this_month" if is_admin_mode else "this_week"
        raw_period = str(params.get("period") or "").strip()
        pkey, plabel, pshort, start_d, end_d, s_utc, e_utc, include_open_undated = (
            self._tp_home_period_bounds(raw_period, default_period, tz, today_local)
        )

        if s_utc and e_utc:
            in_range = Domain("date_deadline", ">=", s_utc) & Domain("date_deadline", "<", e_utc)
            if include_open_undated:
                open_undated = Domain("date_deadline", "=", False) & Domain(
                    "state", "not in", ["1_done", "03_approved", "1_canceled"],
                )
                if "tp_exec_report_state" in Task._fields:
                    open_undated &= Domain("tp_exec_report_state", "!=", "verified")
                period_dom = in_range | open_undated
            else:
                period_dom = in_range
            full_dom = scope_dom & period_dom
        else:
            full_dom = scope_dom

        all_scope_tasks = Task.search(full_dom, order="id asc")

        task_dept_map, meta_by_dept = ({}, {})
        dept_options = [{"key": "", "label": "Tất cả phòng ban"}]
        active_dept_key = ""

        if is_admin_mode:
            task_dept_map, meta_by_dept = self._tp_home_attribute_task_departments(
                all_scope_tasks, company,
            )
            all_company_depts = {}
            if "hr.department" in self.env:
                for d in (
                    self.env["hr.department"]
                    .sudo()
                    .search([("company_id", "=", company.id), ("active", "=", True)], order="id asc")
                ):
                    seq = getattr(d, "tp_sequence", 100) or 100
                    all_company_depts[str(d.id)] = {
                        "key": str(d.id),
                        "label": d.name,
                        "sort_key": (seq, d.id),
                    }
            for dkey, dmeta in meta_by_dept.items():
                if dkey not in all_company_depts:
                    all_company_depts[dkey] = {
                        "key": dkey,
                        "label": dmeta["name"],
                        "sort_key": dmeta["sort_key"],
                    }
            for item in sorted(
                all_company_depts.values(),
                key=lambda x: (x["sort_key"], x["label"].casefold()),
            ):
                dept_options.append({"key": item["key"], "label": item["label"]})

            requested_dept = str(params.get("department_key") or "").strip()
            valid_dept_keys = {opt["key"] for opt in dept_options}
            active_dept_key = requested_dept if requested_dept in valid_dept_keys else ""

        if active_dept_key:
            filtered_tasks = all_scope_tasks.filtered(
                lambda t: task_dept_map.get(t.id) == active_dept_key,
            )
        else:
            filtered_tasks = all_scope_tasks

        bucket_by_task = {}
        task_day_map = {}
        undated_included_count = 0
        for t in filtered_tasks:
            bucket_by_task[t.id] = self._tp_home_classify_task_bucket(t, now_utc)
            if t.date_deadline:
                dl_loc = t.date_deadline.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                task_day_map[t.id] = dl_loc.date().isoformat()
            else:
                task_day_map[t.id] = UNDATED_DAY_KEY
                undated_included_count += 1

        if pkey in ("this_week", "this_month"):
            period_rule_note = (
                f"Phân bố công việc theo ngày hạn hoàn thành trong {plabel} ({tz_name})"
                + (
                    f"; gồm {undated_included_count} việc đang mở chưa đặt hạn (tách riêng cột 'Chưa đặt hạn', không gán vào hôm nay)."
                    if undated_included_count
                    else " và các việc đang mở chưa đặt hạn (0 việc)."
                )
            )
        elif pkey == "all":
            period_rule_note = "Gồm toàn bộ công việc trong phạm vi đã chọn (phân theo hạn hoàn thành; việc chưa có hạn tách cột riêng)."
        else:
            period_rule_note = f"Chỉ tính công việc có hạn hoàn thành nằm trong {plabel} ({tz_name})."

        return {
            "home_mode": home_mode,
            "tasks": filtered_tasks,
            "all_scope_tasks": all_scope_tasks,
            "task_dept_map": task_dept_map,
            "meta_by_dept": meta_by_dept,
            "task_day_map": task_day_map,
            "bucket_by_task": bucket_by_task,
            "undated_included_count": undated_included_count,
            "start_d": start_d,
            "end_d": end_d,
            "scope_key": scope_key,
            "scope_label": {o["key"]: o["label"] for o in scope_options}.get(scope_key, ""),
            "scope_options": scope_options,
            "can_filter_department": is_admin_mode,
            "department_key": active_dept_key,
            "department_label": {o["key"]: o["label"] for o in dept_options}.get(
                active_dept_key, "Tất cả phòng ban",
            ),
            "department_options": dept_options,
            "period_key": pkey,
            "period_label": plabel,
            "period_short_badge": pshort,
            "period_options": [{"key": k, "label": lbl} for k, lbl in PERIOD_OPTIONS],
            "period_rule_note": period_rule_note,
        }

    @api.model
    def _tp_home_build_tasks_and_charts(self, params=None, home_mode="admin", company=None):
        is_admin_mode = home_mode == "admin"
        kpi_key = "tasks" if is_admin_mode else "emp_tasks"
        kpi_label = "Công việc" if is_admin_mode else "Việc chưa hoàn thành"

        if "project.task" not in self.env:
            return (
                {
                    "key": kpi_key,
                    "card_kind": "metric",
                    "label": kpi_label,
                    "status": "unconfigured",
                    "count": None,
                    "status_text": "Chưa cài đặt",
                    "tooltip": "Phân hệ Công việc chưa được cài đặt.",
                    "can_open": False,
                    "drilldown": None,
                },
                {"status": "unconfigured", "mode": home_mode},
            )
        try:
            ds = self._tp_home_collect_task_dataset(
                params=params, home_mode=home_mode, company=company,
            )
            tasks = ds["tasks"]
            bucket_by_task = ds["bucket_by_task"]
            total = len(tasks)
            done_total = sum(1 for t in tasks if bucket_by_task[t.id] == "done")
            incomplete_total = total - done_total

            bucket_defs = list(DONUT_BUCKETS_ADMIN if is_admin_mode else DONUT_BUCKETS_EMPLOYEE)
            unmapped_cnt = sum(1 for t in tasks if bucket_by_task[t.id] == "unmapped")
            if unmapped_cnt > 0:
                bucket_defs.append(UNMAPPED_BUCKET)

            raw_counts = [
                sum(1 for t in tasks if bucket_by_task[t.id] == bkey)
                for bkey, _blbl, _bcol in bucket_defs
            ]
            rounded_pcts = _largest_remainder_percents(raw_counts)
            donut_slices = []
            for idx, (bkey, blabel, bcolor) in enumerate(bucket_defs):
                cnt = raw_counts[idx]
                exact_pct = round((cnt * 100.0) / total, 1) if total > 0 else 0.0
                donut_slices.append(
                    {
                        "key": bkey,
                        "label": blabel,
                        "color": bcolor,
                        "count": cnt,
                        "percent": rounded_pcts[idx],
                        "exact_percent": exact_pct,
                    },
                )

            if is_admin_mode:
                task_dept_map = ds["task_dept_map"]
                meta_by_dept = ds["meta_by_dept"]
                dept_order_keys = sorted(
                    {task_dept_map[t.id] for t in tasks},
                    key=lambda dk: (
                        meta_by_dept[dk]["sort_key"],
                        meta_by_dept[dk]["name"].casefold(),
                    ),
                )
                bar_rows = []
                for dkey in dept_order_keys:
                    d_tasks = [t for t in tasks if task_dept_map[t.id] == dkey]
                    done_cnt = sum(1 for t in d_tasks if bucket_by_task[t.id] == "done")
                    open_cnt = len(d_tasks) - done_cnt
                    bar_rows.append(
                        {
                            "department_key": dkey,
                            "department_name": meta_by_dept[dkey]["name"],
                            "done_count": done_cnt,
                            "incomplete_count": open_cnt,
                            "total_count": len(d_tasks),
                        },
                    )
                kpi = {
                    "key": "tasks",
                    "card_kind": "metric",
                    "label": "Công việc",
                    "status": "ok",
                    "count": total,
                    "badge_text": ds["scope_label"],
                    "badge_kind": "green",
                    "tooltip": f"{ds['scope_label']} · {ds['period_label']}. {ds['period_rule_note']}",
                    "can_open": True,
                    "drilldown": {
                        "type": "rpc_action",
                        "method": "get_tp_home_task_drilldown_action",
                        "params": {},
                    },
                }
                bar_payload = {
                    "kind": "department",
                    "title": "Tình hình công việc",
                    "subtitle": "",
                    "series": [
                        {"key": "done", "label": "Hoàn thành", "color": "#4E7DE8"},
                        {"key": "incomplete", "label": "Chưa hoàn thành", "color": "#BBD4FA"},
                    ],
                    "rows": bar_rows,
                }
                donut_payload = {
                    "title": "Tỷ lệ công việc",
                    "subtitle": "",
                    "center_count": total,
                    "center_label": "Công việc",
                    "slices": donut_slices,
                }
                attribution_note = (
                    "Phân bổ phòng ban mỗi công việc đúng 1 lần theo thứ tự ưu tiên: "
                    "(1) Phòng chủ trì của dự án, (2) Phòng của người chịu trách nhiệm chính, "
                    "(3) Phòng duy nhất của người được giao; việc nhiều phòng đưa vào 'Liên phòng ban', "
                    "chưa có phòng đưa vào 'Chưa gắn phòng ban'."
                )
            else:
                day_rows = self._tp_home_build_employee_day_bars(
                    tasks,
                    bucket_by_task,
                    ds["task_day_map"],
                    ds["start_d"],
                    ds["end_d"],
                )
                diff_note = (
                    f"Ô 'Việc chưa hoàn thành' đếm các việc đang mở ({incomplete_total} việc); "
                    f"tâm biểu đồ tròn hiển thị tổng cả việc đã hoàn thành và chưa hoàn thành trong kỳ ({total} việc)."
                )
                kpi = {
                    "key": "emp_tasks",
                    "card_kind": "metric",
                    "label": "Việc chưa hoàn thành",
                    "status": "ok",
                    "count": incomplete_total,
                    "total_in_period": total,
                    "done_in_period": done_total,
                    "badge_text": ds["period_short_badge"],
                    "badge_kind": "blue",
                    "tooltip": f"{ds['period_label']}. {diff_note} {ds['period_rule_note']}",
                    "can_open": True,
                    "drilldown": {
                        "type": "rpc_action",
                        "method": "get_tp_home_task_drilldown_action",
                        "params": {"bar_segment": "incomplete"},
                    },
                }
                bar_payload = {
                    "kind": "daily",
                    "title": "Công việc của tôi theo ngày",
                    "subtitle": "Phân bố theo hạn hoàn thành trong kỳ (việc chưa có hạn tách riêng)",
                    "series": [
                        {"key": "done", "label": "Hoàn thành", "color": "#4E7DE8"},
                        {"key": "incomplete", "label": "Chưa hoàn thành", "color": "#BBD4FA"},
                    ],
                    "rows": day_rows,
                }
                donut_payload = {
                    "title": "Tỷ lệ công việc của tôi",
                    "subtitle": f"Tổng {total} việc (chưa xong: {incomplete_total})",
                    "note": diff_note,
                    "center_count": total,
                    "center_label": "Công việc",
                    "slices": donut_slices,
                }
                attribution_note = diff_note

            charts = {
                "status": "ok",
                "mode": home_mode,
                "total": total,
                "done_total": done_total,
                "incomplete_total": incomplete_total,
                "scope_key": ds["scope_key"],
                "scope_label": ds["scope_label"],
                "scope_options": ds["scope_options"],
                "can_filter_department": ds["can_filter_department"],
                "department_key": ds["department_key"],
                "department_label": ds["department_label"],
                "department_options": ds["department_options"],
                "period_key": ds["period_key"],
                "period_label": ds["period_label"],
                "period_short_badge": ds["period_short_badge"],
                "period_options": ds["period_options"],
                "period_rule_note": ds["period_rule_note"],
                "attribution_note": attribution_note,
                "bar": bar_payload,
                "donut": donut_payload,
            }
            return kpi, charts
        except AccessError:
            return (
                {
                    "key": kpi_key,
                    "card_kind": "metric",
                    "label": kpi_label,
                    "status": "no_access",
                    "count": None,
                    "status_text": "Không có quyền xem",
                    "tooltip": "Tài khoản không có quyền xem dữ liệu công việc.",
                    "can_open": False,
                    "drilldown": None,
                },
                {"status": "no_access", "mode": home_mode},
            )
        except Exception:
            _logger.exception("TP Home: failed to compute Task KPI & charts")
            return (
                {
                    "key": kpi_key,
                    "card_kind": "metric",
                    "label": kpi_label,
                    "status": "error",
                    "count": None,
                    "status_text": "Tạm lỗi nguồn",
                    "tooltip": "Chưa tải được dữ liệu Công việc. Vui lòng thử làm mới.",
                    "can_open": False,
                    "drilldown": None,
                },
                {"status": "error", "mode": home_mode},
            )

    @api.model
    def get_tp_home_task_drilldown_action(self, params=None):
        """Return an `ir.actions.act_window` on `project.task` whose count matches KPI / Bar / Donut 100%."""
        user = self._tp_home_require_internal()
        company = self._tp_home_allowed_company()
        home_mode = self._tp_home_mode(user=user, company=company)
        params = dict(params or {})

        ds = self._tp_home_collect_task_dataset(
            params=params, home_mode=home_mode, company=company,
        )
        tasks = ds["tasks"]
        bucket_by_task = ds["bucket_by_task"]
        task_dept_map = ds["task_dept_map"]
        meta_by_dept = ds["meta_by_dept"]
        task_day_map = ds["task_day_map"]

        bar_dept_key = str(params.get("bar_department_key") or "").strip() if home_mode == "admin" else ""
        bar_day_key = str(params.get("bar_day_key") or "").strip()
        bar_segment = str(params.get("bar_segment") or "").strip()
        donut_bucket = str(params.get("donut_bucket") or "").strip()

        base_title = "Công việc" if home_mode == "admin" else "Công việc của tôi"
        title_parts = [base_title, ds["period_label"]]
        matched = list(tasks)

        if bar_dept_key:
            matched = [t for t in matched if task_dept_map.get(t.id) == bar_dept_key]
            dname = meta_by_dept.get(bar_dept_key, {}).get("name") or bar_dept_key
            title_parts.append(dname)
        elif home_mode == "admin" and ds["department_key"]:
            title_parts.append(ds["department_label"])

        if bar_day_key:
            matched = [t for t in matched if task_day_map.get(t.id) == bar_day_key]
            if bar_day_key == UNDATED_DAY_KEY:
                title_parts.append("Chưa đặt hạn")
            else:
                try:
                    d_obj = date.fromisoformat(bar_day_key)
                    title_parts.append(d_obj.strftime("%d/%m/%Y"))
                except ValueError:
                    title_parts.append(bar_day_key)

        if bar_segment == "done":
            matched = [t for t in matched if bucket_by_task.get(t.id) == "done"]
            title_parts.append("Hoàn thành")
        elif bar_segment == "incomplete":
            matched = [t for t in matched if bucket_by_task.get(t.id) != "done"]
            title_parts.append("Chưa hoàn thành")
        elif donut_bucket:
            matched = [t for t in matched if bucket_by_task.get(t.id) == donut_bucket]
            bucket_catalog = DONUT_BUCKETS_ADMIN if home_mode == "admin" else DONUT_BUCKETS_EMPLOYEE
            blabel = {
                k: lbl for k, lbl, _ in (*bucket_catalog, UNMAPPED_BUCKET)
            }.get(donut_bucket, donut_bucket)
            title_parts.append(blabel)

        matched_ids = [t.id for t in matched]
        title = " · ".join(title_parts)
        if home_mode == "admin" and self.env.ref("tp_kd_workspace.action_tasks", raise_if_not_found=False):
            action = self.env["ir.actions.actions"]._for_xml_id("tp_kd_workspace.action_tasks")
            base_ctx = action.get("context")
            if not isinstance(base_ctx, dict):
                base_ctx = {}
            action.update(
                name=title,
                domain=[("id", "in", matched_ids)],
                context={
                    **base_ctx,
                    "tp_kd_leaf": "tp_kd_workspace.menu_tasks",
                    "create": False,
                },
            )
            return action
        for xmlid in (
            "project_todo.project_task_action_todo",
            "tp_kd_workspace.action_tasks",
            "project.action_view_my_task",
        ):
            if self.env.ref(xmlid, raise_if_not_found=False):
                action = self.env["ir.actions.actions"]._for_xml_id(xmlid)
                base_ctx = action.get("context") if isinstance(action.get("context"), dict) else {}
                action.update(
                    name=title,
                    res_model="project.task",
                    view_mode="list,form",
                    views=[(False, "list"), (False, "form")],
                    domain=[("id", "in", matched_ids)],
                    context={**base_ctx, "create": False},
                )
                return action
        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": "project.task",
            "view_mode": "list,form",
            "views": [(False, "list"), (False, "form")],
            "domain": [("id", "in", matched_ids)],
            "context": {"create": False},
        }

    # ==================================================================
    # AGENDA: CÔNG VIỆC HÔM NAY (Personal Tasks due today + Calendar today)
    # ==================================================================
    def _tp_home_collect_today_agenda_items(self):
        company = self._tp_home_allowed_company()
        tz, tz_name = _user_tz(self.env)
        now_local = datetime.now(tz)
        today_local = now_local.date()
        start_utc, stop_utc = _local_bounds_to_utc_naive(tz, today_local, today_local)
        now_utc = fields.Datetime.now()
        has_personal_tools = (
            "project.task" in self.env
            and "tp_exec_report_state" in self.env["project.task"]._fields
        )

        items = []
        linked_task_ids_in_events = set()

        # A. Today's Calendar Events / Meetings where caller is organizer or participant
        if "calendar.event" in self.env:
            try:
                events, _td, _tz_obj, _tz_n = self._tp_home_collect_today_calendar_events()
            except AccessError:
                events = []

            for ev in events:
                if ev.allday:
                    time_label = "Cả ngày"
                    sort_key = (0, "00:00", ev.id)
                else:
                    st_loc = ev.start.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                    en_loc = ev.stop.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                    if st_loc.date() == today_local and en_loc.date() == today_local:
                        time_label = f"{st_loc.strftime('%H:%M')} – {en_loc.strftime('%H:%M')}"
                    else:
                        time_label = f"{st_loc.strftime('%d/%m %H:%M')} – {en_loc.strftime('%d/%m %H:%M')}"
                    sort_key = (1, st_loc.strftime("%H:%M") if st_loc.date() == today_local else "00:01", ev.id)

                linked_task = None
                if ev.res_model == "project.task" and ev.res_id and "project.task" in self.env:
                    t_rec = self.env["project.task"].sudo(False).browse(ev.res_id).exists()
                    if t_rec and t_rec.has_access("read") and t_rec.active:
                        can_read_personal = (
                            not hasattr(t_rec, "_tp_is_user_involved")
                            or t_rec._tp_is_user_involved()
                            or self.env.user.partner_id in t_rec.message_partner_ids
                        )
                        if can_read_personal:
                            linked_task_ids_in_events.add(t_rec.id)
                            linked_task = {
                                "id": t_rec.id,
                                "name": t_rec.name or f"Công việc #{t_rec.id}",
                                "route": f"/app/ca-nhan/cong-viec/{t_rec.id}" if has_personal_tools else "",
                            }

                ev_kind = getattr(ev, "tp_event_kind", "meeting") or "meeting"
                is_past = bool(not ev.allday and ev.stop and ev.stop < now_utc)
                items.append(
                    {
                        "uid_key": f"event-{ev.id}",
                        "kind": "meeting",
                        "kind_label": "Cuộc họp" if ev_kind == "meeting" else "Lịch hẹn",
                        "source_label": "",
                        "tone": "green" if not is_past else "muted",
                        "id": ev.id,
                        "title": ev.name or "(Chưa đặt tiêu đề)",
                        "time_label": time_label,
                        "status_label": "Đã qua khung giờ" if is_past else "Lịch hôm nay",
                        "res_model": "calendar.event",
                        "res_id": ev.id,
                        "route": f"/app/ca-nhan/lich-lam-viec/{ev.id}" if has_personal_tools else "",
                        "linked_task": linked_task,
                        "_sort": sort_key,
                    },
                )

        # B. Today's Tasks in caller's personal/assigned work scope (deduplicated against linked events)
        if "project.task" in self.env:
            Task = self.env["project.task"].sudo(False).with_context(active_test=True)
            if Task.has_access("read"):
                t_dom = (
                    self._tp_home_my_work_domain(Task, company)
                    & Domain("date_deadline", ">=", start_utc)
                    & Domain("date_deadline", "<", stop_utc)
                )
                today_tasks = Task.search(t_dom, order="date_deadline asc, priority desc, id asc", limit=100)
                for task in today_tasks:
                    if task.id in linked_task_ids_in_events:
                        continue
                    bucket = self._tp_home_classify_task_bucket(task, now_utc)
                    dl_local = task.date_deadline.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
                    has_clock_hour = not (
                        dl_local.hour in (0, 23) and dl_local.minute in (0, 59)
                    )
                    if has_clock_hour:
                        time_label = f"Hạn {dl_local.strftime('%H:%M')}"
                        sort_clock = dl_local.strftime("%H:%M")
                    else:
                        time_label = "Hạn hôm nay"
                        sort_clock = "23:59"

                    eff_source = (
                        task._tp_effective_source_kind()
                        if hasattr(task, "_tp_effective_source_kind")
                        else ("project" if task.project_id else "self")
                    )
                    exec_st = getattr(task, "tp_exec_report_state", False)
                    tone_map = {
                        "done": "green",
                        "in_progress": "teal",
                        "waiting": "amber",
                        "overdue": "red",
                    }
                    status_map = {
                        "done": "Hoàn thành",
                        "in_progress": "Đang thực hiện",
                        "waiting": "Chờ xác nhận" if exec_st == "reported_done" else "Chờ xử lý",
                        "overdue": "Quá hạn",
                    }
                    items.append(
                        {
                            "uid_key": f"task-{task.id}",
                            "kind": "task",
                            "kind_label": "Công việc",
                            "source_label": SOURCE_SHORT_LABELS.get(eff_source, "Tự tạo"),
                            "tone": tone_map.get(bucket, "teal"),
                            "id": task.id,
                            "title": task.name or f"Công việc #{task.id}",
                            "time_label": time_label,
                            "status_label": status_map.get(bucket, "Cần làm"),
                            "is_done": bucket == "done",
                            "res_model": "project.task",
                            "res_id": task.id,
                            "route": f"/app/ca-nhan/cong-viec/{task.id}" if has_personal_tools else "",
                            "linked_task": None,
                            "_sort": (2 if bucket == "done" else 1, sort_clock, task.id),
                        },
                    )

        items.sort(key=lambda r: r["_sort"])
        for r in items:
            r.pop("_sort", None)
        return items, today_local, tz_name

    @api.model
    def _tp_home_agenda_summary(self, preview_limit=4):
        if "project.task" not in self.env and "calendar.event" not in self.env:
            return {"status": "unconfigured", "items": [], "total_today": 0}
        try:
            items, today_local, tz_name = self._tp_home_collect_today_agenda_items()
            return {
                "status": "ok",
                "today_iso": today_local.isoformat(),
                "today_display": today_local.strftime("%d/%m/%Y"),
                "timezone": tz_name,
                "items": items[:preview_limit],
                "total_today": len(items),
                "has_more": len(items) > preview_limit,
            }
        except AccessError:
            return {"status": "no_access", "items": [], "total_today": 0}
        except Exception:
            _logger.exception("TP Home: failed to load today agenda")
            return {"status": "error", "items": [], "total_today": 0}

    @api.model
    def get_tp_home_agenda_page(self, page=1, page_size=10):
        """Paginated 'Xem tất cả' list for Today's Work & Meetings."""
        self._tp_home_require_internal()
        page = max(1, int(page or 1))
        page_size = int(page_size or 10)
        if page_size not in (10, 20, 50):
            page_size = 10
        items, today_local, tz_name = self._tp_home_collect_today_agenda_items()
        total = len(items)
        max_page = max(1, (total + page_size - 1) // page_size)
        if page > max_page:
            page = max_page
        offset = (page - 1) * page_size
        return {
            "status": "ok",
            "today_display": today_local.strftime("%d/%m/%Y"),
            "timezone": tz_name,
            "items": items[offset : offset + page_size],
            "total": total,
            "page": page,
            "page_size": page_size,
            "max_page": max_page,
        }

    # ==================================================================
    # UNIFIED DASHBOARD ENDPOINT (Server-Authoritative Admin / Employee)
    # ==================================================================
    @api.model
    def get_tp_home_dashboard(self, params=None):
        user = self._tp_home_require_internal()
        company = self._tp_home_allowed_company()
        home_mode = self._tp_home_mode(user=user, company=company)
        tz, tz_name = _user_tz(self.env)
        now_local = datetime.now(tz)

        # Strip any spoofed client identity/mode keys before reading filter params
        raw_params = dict(params or {}) if isinstance(params, dict) else {}
        clean_params = {
            "period": raw_params.get("period", ""),
            "task_scope": raw_params.get("task_scope", ""),
            "department_key": raw_params.get("department_key", ""),
        }

        agenda = self._tp_home_agenda_summary(preview_limit=4)

        if home_mode == "admin":
            hr_kpi = self._tp_home_kpi_hr(company)
            req_kpi = self._tp_home_kpi_admin_requests(company)
            task_kpi, charts = self._tp_home_build_tasks_and_charts(
                params=clean_params, home_mode="admin", company=company,
            )
            stock_kpi = self._tp_home_kpi_stock(company)
            cards = [
                {**hr_kpi, "theme": "blue", "icon_name": "kpi-hr"},
                {**req_kpi, "theme": "purple", "icon_name": "kpi-requests"},
                {**task_kpi, "theme": "green", "icon_name": "kpi-tasks"},
                {**stock_kpi, "theme": "amber", "icon_name": "kpi-stock"},
            ]
            kpis_map = {
                "hr": hr_kpi,
                "requests": req_kpi,
                "tasks": task_kpi,
                "stock": stock_kpi,
            }
            apps_title = "Ứng dụng theo phòng ban"
        else:
            # Employee mode: NEVER calls Stock KPI, NEVER queries company-wide department bars
            emp_task_kpi, charts = self._tp_home_build_tasks_and_charts(
                params=clean_params, home_mode="employee", company=company,
            )
            emp_req_kpi = self._tp_home_kpi_employee_requests(company)
            emp_cal_kpi = self._tp_home_kpi_employee_calendar()
            emp_att_kpi = self._tp_home_kpi_employee_attendance(company)
            cards = [
                {**emp_task_kpi, "theme": "blue", "icon_name": "kpi-tasks"},
                {**emp_req_kpi, "theme": "purple", "icon_name": "kpi-requests"},
                {**emp_cal_kpi, "theme": "green", "icon_name": "calendar"},
                {**emp_att_kpi, "theme": "amber", "icon_name": "clock"},
            ]
            kpis_map = {
                "emp_tasks": emp_task_kpi,
                "emp_requests": emp_req_kpi,
                "emp_calendar": emp_cal_kpi,
                "emp_attendance": emp_att_kpi,
            }
            apps_title = "Ứng dụng của bạn"

        return {
            "home_mode": home_mode,
            "apps_title": apps_title,
            "meta": {
                "home_mode": home_mode,
                "user_id": user.id,
                "company_id": company.id,
                "company_name": company.name,
                "timezone": tz_name,
                "updated_at": now_local.strftime("%H:%M:%S · %d/%m/%Y"),
                "updated_short": now_local.strftime("%H:%M"),
            },
            "cards": cards,
            "kpis": kpis_map,
            "agenda": agenda,
            "charts": charts,
        }

    # ==================================================================
    # PERMISSION-CHECKED DOCUMENT / METADATA SEARCH FOR NAVBAR
    # ==================================================================
    @api.model
    def search_tp_home_global(self, query="", limit=8):
        """Search permitted documents & records by name/code/metadata without `ir.attachment.sudo()`."""
        self._tp_home_require_internal()
        raw_q = str(query or "").strip()
        if not raw_q:
            return {"documents": []}
        if len(raw_q) > 120:
            raise ValidationError(self.env._("Từ khóa tìm kiếm quá dài."))

        needle = _fold_text(raw_q)
        if not needle:
            return {"documents": []}
        words = [w for w in needle.split(" ") if w]
        max_items = max(1, min(int(limit or 8), 20))
        company = self._tp_home_allowed_company()
        results = []

        def _matches(*values):
            hay = " " + _fold_text(" ".join(str(v or "") for v in values))
            return all(w in hay for w in words)

        # 1. Hồ sơ dự án & NAS (`tp.project.dossier`)
        if "tp.project.dossier" in self.env and len(results) < max_items:
            Dossier = self.env["tp.project.dossier"].sudo(False)
            if Dossier.has_access("read"):
                try:
                    for rec in Dossier.search([("company_id", "=", company.id)], order="id desc", limit=80):
                        try:
                            if hasattr(rec, "_tp_check_project_read"):
                                rec._tp_check_project_read()
                        except AccessError:
                            continue
                        if _matches(rec.code, rec.name, rec.nas_relative_path):
                            results.append(
                                {
                                    "key": f"dossier-{rec.id}",
                                    "kind_label": "Hồ sơ dự án",
                                    "code": rec.code or "",
                                    "title": rec.name or rec.code,
                                    "subtitle": rec.project_id.name if rec.project_id else "",
                                    "action_xmlid": "tp_enterprise_governance.action_project_dossier_nas",
                                    "menu_xmlid": "tp_enterprise_governance.menu_governance_root",
                                    "route": "/app/du-an/ho-so-nas",
                                },
                            )
                            if len(results) >= max_items:
                                break
                except AccessError:
                    pass

        # 2. Thông báo nội bộ (`tp.announcement`)
        if "tp.announcement" in self.env and len(results) < max_items:
            Ann = self.env["tp.announcement"].sudo(False)
            if Ann.has_access("read"):
                try:
                    for rec in Ann.search([("company_id", "=", company.id)], order="id desc", limit=80):
                        if hasattr(rec, "_tp_is_user_in_audience") and not rec._tp_is_user_in_audience(self.env.user):
                            continue
                        if _matches(rec.code, rec.name):
                            results.append(
                                {
                                    "key": f"ann-{rec.id}",
                                    "kind_label": "Thông báo nội bộ",
                                    "code": rec.code or "",
                                    "title": rec.name or rec.code,
                                    "subtitle": f"Phiên bản v{rec.version}",
                                    "action_xmlid": "tp_digital_office.action_announcements",
                                    "menu_xmlid": "tp_digital_office.menu_digital_office_root",
                                    "route": "/app/van-phong-so/thong-bao",
                                },
                            )
                            if len(results) >= max_items:
                                break
                except AccessError:
                    pass

        # 3. Biên bản họp (`tp.meeting.minute`)
        if "tp.meeting.minute" in self.env and len(results) < max_items:
            Minute = self.env["tp.meeting.minute"].sudo(False)
            if Minute.has_access("read"):
                try:
                    uid = self.env.uid
                    for rec in Minute.search([("company_id", "=", company.id)], order="id desc", limit=80):
                        can_see = bool(
                            (hasattr(rec, "_tp_can_manage") and rec._tp_can_manage(self.env.user))
                            or (
                                rec.state != "draft"
                                and (
                                    uid in rec.attendee_user_ids.ids
                                    or (
                                        rec.project_id
                                        and hasattr(rec.project_id, "_tp_scope_allowed")
                                        and rec.project_id._tp_scope_allowed(self.env.user)
                                    )
                                )
                            ),
                        )
                        if not can_see:
                            continue
                        if _matches(rec.code, rec.name):
                            results.append(
                                {
                                    "key": f"minute-{rec.id}",
                                    "kind_label": "Biên bản họp",
                                    "code": rec.code or "",
                                    "title": rec.name or rec.code,
                                    "subtitle": rec.department_id.name if rec.department_id else "",
                                    "action_xmlid": "tp_digital_office.action_meeting_minutes",
                                    "menu_xmlid": "tp_digital_office.menu_digital_office_root",
                                    "route": "/app/van-phong-so/bien-ban-hop",
                                },
                            )
                            if len(results) >= max_items:
                                break
                except AccessError:
                    pass

        # 4. Hợp đồng (`tp.contract`) — code & name only, never financial amounts
        if "tp.contract" in self.env and len(results) < max_items:
            Contract = self.env["tp.contract"].sudo(False)
            if Contract.has_access("read"):
                try:
                    for rec in Contract.search(
                        [("company_id", "=", company.id)], order="id desc", limit=80,
                    ):
                        if _matches(rec.code, rec.name):
                            results.append(
                                {
                                    "key": f"contract-{rec.id}",
                                    "kind_label": "Hợp đồng",
                                    "code": rec.code or "",
                                    "title": rec.name or rec.code,
                                    "subtitle": rec.project_id.name if rec.project_id else "",
                                    "res_model": "tp.contract",
                                    "res_id": rec.id,
                                },
                            )
                            if len(results) >= max_items:
                                break
                except AccessError:
                    pass

        # 5. Hồ sơ Yêu cầu phê duyệt (`tp.request`) — strictly caller-accessible requests in company
        if "tp.request" in self.env and len(results) < max_items:
            Req = self.env["tp.request"].sudo(False)
            if Req.has_access("read"):
                try:
                    uid = self.env.uid
                    is_mgr = bool(
                        self._tp_home_is_full_admin(self.env.user, company)
                        or self.env.user.has_group("tp_request.group_request_manager"),
                    )
                    if is_mgr:
                        r_dom = [
                            "&",
                            ("company_id", "=", company.id),
                            "|",
                            ("requester_user_id", "=", uid),
                            ("approval_state", "!=", "draft"),
                        ]
                    else:
                        r_dom = [
                            "&",
                            ("company_id", "=", company.id),
                            "|",
                            ("requester_user_id", "=", uid),
                            "&",
                            ("approval_state", "!=", "draft"),
                            "|",
                            ("follower_user_ids", "in", [uid]),
                            "|",
                            ("all_approver_ids", "in", [uid]),
                            "|",
                            ("executor_user_ids", "in", [uid]),
                            ("assigned_executor_id", "=", uid),
                        ]
                    for rec in Req.search(r_dom, order="id desc", limit=80):
                        if _matches(rec.code, rec.title):
                            results.append(
                                {
                                    "key": f"req-{rec.id}",
                                    "kind_label": "Yêu cầu phê duyệt",
                                    "code": rec.code or "",
                                    "title": rec.title or rec.code,
                                    "subtitle": rec.type_id.name if rec.type_id else "",
                                    "action_xmlid": "tp_request.action_detail",
                                    "menu_xmlid": "tp_request.menu_root",
                                    "action_params": {"request_id": rec.id},
                                    "route": f"/app/de-nghi/ho-so/{rec.id}",
                                },
                            )
                            if len(results) >= max_items:
                                break
                except AccessError:
                    pass

        return {"documents": results[:max_items]}


class TpHomeSession(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super().session_info()
        result["tp_home_dashboard"] = True
        user = self.env.user
        if user and not user._is_public() and user.active and not user.share:
            try:
                result["tp_home_is_admin"] = bool(user._tp_home_is_full_admin())
                has_delegation = getattr(user, "_tp_has_admin_delegation", None)
                result["tp_home_is_delegated"] = bool(has_delegation()) if callable(has_delegation) else False
            except (AccessError, AttributeError):
                result["tp_home_is_admin"] = bool(user.has_group("base.group_system"))
                result["tp_home_is_delegated"] = False
        return result
