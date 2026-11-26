# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Permission-checked server-side data adapters for TANPHAT ONE Home (`tp_web_home`).

Design guarantees:
1. Zero circular dependencies: `tp_web_home` continues to depend only on `web` and
   `tp_web_login`. Installed business modules (`tp_hr_workspace`, `tp_request`,
   `tp_personal_tools`, `tp_equipment`, `tp_kd_workspace`, `tp_digital_office`,
   `tp_enterprise_governance`) are discovered dynamically via `self.env`.
2. Strictly read-only: Home queries never bootstrap personal stages, never mutate
   records, and never call external syncs (e.g. ENTI).
3. Permission-true states: Every block distinguishes `ok` (including valid `0`),
   `no_access`, `unconfigured`, and `error`. Unauthorized KPIs return `count: None`
   (never `0` and never leaked counts).
4. Unified dataset: Task KPI, Stacked Bar by Department, Donut by Status, and
   Task Drilldowns all evaluate the exact same distinct `project.task` population.
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

PERIOD_OPTIONS = (
    ("this_month", "Tháng này"),
    ("this_month_strict", "Có hạn trong tháng"),
    ("this_week", "Tuần này"),
    ("this_quarter", "Quý này"),
    ("all", "Tất cả kỳ"),
)

DONUT_BUCKETS = (
    ("done", "Hoàn thành", "#79BE81"),
    ("in_progress", "Đang thực hiện", "#4E7DE8"),
    ("waiting", "Chờ xử lý", "#E8AA40"),
    ("overdue", "Quá hạn", "#DD6A64"),
)
UNMAPPED_BUCKET = ("unmapped", "Trạng thái khác", "#94A3B8")

CROSS_DEPT_KEY = "cross_dept"
UNASSIGNED_DEPT_KEY = "unassigned_dept"


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
    # Caller & Role Capability Helpers
    # ------------------------------------------------------------------
    def _tp_home_require_internal(self):
        user = self.env.user
        if not user or not user.active or not user._is_internal():
            raise AccessError(
                self.env._("Chỉ tài khoản nội bộ đang hoạt động mới được truy cập Trang chủ."),
            )
        return user

    def _tp_home_is_full_admin(self, user=None, company=None):
        user = user or self.env.user
        company = company or self.env.company
        if hasattr(user, "_tp_is_main_admin"):
            if not user._tp_is_main_admin():
                return False
            if hasattr(user, "_tp_is_original_admin") and user._tp_is_original_admin():
                return True
            if hasattr(user, "_tp_is_granted_admin"):
                return bool(user._tp_is_granted_admin(company=company))
            return True
        return bool(user.active and not user.share and user.has_group("base.group_system"))

    # ------------------------------------------------------------------
    # 1. KPI: NHÂN SỰ
    # ------------------------------------------------------------------
    @api.model
    def _tp_home_kpi_hr(self):
        if "hr.employee" not in self.env:
            return {
                "key": "hr",
                "label": "Nhân sự",
                "status": "unconfigured",
                "count": None,
                "status_text": "Chưa cài đặt",
                "tooltip": "Phân hệ Nhân sự chưa được cài đặt trên môi trường này.",
                "can_open": False,
                "drilldown": None,
            }
        try:
            company = self.env.company
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
                        "label": "Nhân sự",
                        "status": "ok",
                        "count": int(count),
                        "badge_text": "Đang làm việc",
                        "badge_kind": "neutral",
                        "tooltip": "Nhân viên đang hoạt động trong phạm vi được phép xem",
                        "can_open": True,
                        "drilldown": {"type": "rpc_action", "method": "get_tp_home_hr_drilldown_action"},
                    }

            # Fallback when tp_hr_workspace is not installed
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
                            "label": "Nhân sự",
                            "status": "ok",
                            "count": int(count),
                            "badge_text": "Đang làm việc",
                            "badge_kind": "neutral",
                            "tooltip": "Nhân viên đang hoạt động trong phạm vi được phép xem",
                            "can_open": True,
                            "drilldown": {"type": "rpc_action", "method": "get_tp_home_hr_drilldown_action", "fallback_xmlid": xmlid},
                        }

            return {
                "key": "hr",
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
        if "tp.hr.workspace" in self.env:
            ws = self.env["tp.hr.workspace"]
            is_delegated_hr = bool(
                hasattr(ws, "_tp_delegated_hr") and ws._tp_delegated_hr(),
            )
            if self.env.user.has_group("hr.group_hr_user") or is_delegated_hr:
                return ws.action_employees({"status": "active"})
            if hasattr(ws, "action_public_employees"):
                return ws.action_public_employees({})
        company = self.env.company
        for model_name in ("hr.employee", "hr.employee.public"):
            if model_name in self.env and self.env[model_name].sudo(False).has_access("read"):
                return {
                    "type": "ir.actions.act_window",
                    "name": "Danh sách nhân viên",
                    "res_model": model_name,
                    "view_mode": "list,form",
                    "domain": [("company_id", "=", company.id), ("active", "=", True)],
                }
        raise AccessError(self.env._("Bạn không có quyền mở danh sách nhân sự."))

    # ------------------------------------------------------------------
    # 2. KPI: YÊU CẦU PHÊ DUYỆT
    # ------------------------------------------------------------------
    def _tp_home_is_request_approver_role(self, Req, company):
        user = self.env.user
        uid = user.id
        if self._tp_home_is_full_admin(user, company):
            return True
        if user.has_group("tp_request.group_request_manager"):
            return True
        # Live pending or historical step assignment
        if Req.search_count(Req._tp_mode_domain("to_approve")) > 0:
            return True
        if Req.search_count([("all_approver_ids", "in", [uid]), ("requester_user_id", "!=", uid)]) > 0:
            return True
        # Explicit approver role in org/project/type config
        if "hr.department" in self.env:
            if self.env["hr.department"].sudo().search_count(
                [("company_id", "=", company.id), ("active", "=", True), ("manager_id.user_id", "=", uid)],
            ):
                return True
        if "hr.employee" in self.env:
            if self.env["hr.employee"].sudo().search_count(
                [("company_id", "=", company.id), ("active", "=", True), ("parent_id.user_id", "=", uid)],
            ):
                return True
        if "tp.kd.department.role" in self.env:
            if self.env["tp.kd.department.role"]._roles(user=user):
                return True
        if "tp.request.type.step" in self.env:
            if self.env["tp.request.type.step"].sudo().search_count(
                [("type_id.active", "=", True), ("approver_user_ids", "in", [uid])],
            ):
                return True
        return False

    @api.model
    def _tp_home_kpi_requests(self):
        if "tp.request" not in self.env:
            return {
                "key": "requests",
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
                    "label": "Yêu cầu phê duyệt",
                    "status": "no_access",
                    "count": None,
                    "status_text": "Không có quyền xem",
                    "tooltip": "Tài khoản không có quyền xem Yêu cầu phê duyệt.",
                    "can_open": False,
                    "drilldown": None,
                }
            company = self.env.company
            uid = self.env.uid
            is_approver = self._tp_home_is_request_approver_role(Req, company)
            if is_approver:
                dom = Req._tp_mode_domain("to_approve")
                count = Req.search_count(dom)
                return {
                    "key": "requests",
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
                        "request_mode": "to_approve",
                        "request_tab": "all",
                    },
                }

            dom = [("requester_user_id", "=", uid), ("approval_state", "=", "pending")]
            count = Req.search_count(dom)
            return {
                "key": "requests",
                "label": "Yêu cầu phê duyệt",
                "status": "ok",
                "count": int(count),
                "role_mode": "mine_pending",
                "badge_text": "Đang chờ duyệt",
                "badge_kind": "purple",
                "tooltip": "Số đề nghị bạn đã gửi và hiện đang chờ cấp có thẩm quyền phê duyệt (không tính bản nháp).",
                "can_open": True,
                "drilldown": {
                    "type": "client_action",
                    "action_xmlid": "tp_request.action_mine",
                    "menu_xmlid": "tp_request.menu_root",
                    "request_mode": "mine",
                    "request_tab": "pending",
                },
            }
        except AccessError:
            return {
                "key": "requests",
                "label": "Yêu cầu phê duyệt",
                "status": "no_access",
                "count": None,
                "status_text": "Không có quyền xem",
                "tooltip": "Tài khoản không có quyền xem Yêu cầu phê duyệt.",
                "can_open": False,
                "drilldown": None,
            }
        except Exception:
            _logger.exception("TP Home: failed to compute Request KPI")
            return {
                "key": "requests",
                "label": "Yêu cầu phê duyệt",
                "status": "error",
                "count": None,
                "status_text": "Tạm lỗi nguồn",
                "tooltip": "Chưa tải được số liệu Yêu cầu phê duyệt. Vui lòng thử làm mới.",
                "can_open": False,
                "drilldown": None,
            }

    # ------------------------------------------------------------------
    # 3. KPI: TỒN KHO (maintenance.equipment)
    # ------------------------------------------------------------------
    @api.model
    def _tp_home_kpi_stock(self):
        if "maintenance.equipment" not in self.env:
            return {
                "key": "stock",
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
                    "label": "Tồn kho",
                    "status": "no_access",
                    "count": None,
                    "status_text": "Không có quyền xem",
                    "tooltip": "Tài khoản của bạn không có quyền xem số liệu Kho thiết bị.",
                    "can_open": False,
                    "drilldown": None,
                }

            if hasattr(Equipment, "tp_main_summary"):
                # tp_main_summary enforces check_admin(env, self) and returns exact STOCK_DOMAIN count
                summary = Equipment.tp_main_summary()
                stock_count = int(summary.get("stock", 0))
                free_count = int(summary.get("free", 0))
                return {
                    "key": "stock",
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

            count = Equipment.search_count([("company_id", "in", [False, self.env.company.id])])
            return {
                "key": "stock",
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
            # Strict requirement 7.4: NEVER return 0 or count to unauthorized accounts!
            return {
                "key": "stock",
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
        self._tp_home_require_internal()
        if "maintenance.equipment" not in self.env:
            raise AccessError(self.env._("Phân hệ Kho thiết bị chưa được cài đặt."))
        Equipment = self.env["maintenance.equipment"].sudo(False)
        Equipment.check_access("read")
        if hasattr(Equipment, "tp_main_summary"):
            # Re-verify Kho admin guard identically to tp_main_summary
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
        return {
            "type": "ir.actions.act_window",
            "name": "Thiết bị tồn kho",
            "res_model": "maintenance.equipment",
            "view_mode": "list,form",
            "domain": [("company_id", "in", [False, self.env.company.id])],
        }

    # ------------------------------------------------------------------
    # 4. TASK POPULATION, KPI & TWO CHARTS (Shared Dataset)
    # ------------------------------------------------------------------
    def _tp_home_task_management_context(self, Task, company):
        """Determine real task management authority from groups/roles/projects (never job title)."""
        user = self.env.user
        uid = user.id
        is_full_mgr = bool(
            self._tp_home_is_full_admin(user, company)
            or user.has_group("tp_core.group_manager")
            or user.has_group("project.group_project_manager"),
        )
        managed_project_ids = set()
        if not is_full_mgr and "project.project" in self.env:
            Project = self.env["project.project"].sudo(False)
            if Project.has_access("read"):
                own_projs = Project.search(
                    [("company_id", "in", [False, company.id]), ("user_id", "=", uid)],
                )
                managed_project_ids.update(own_projs.ids)
            if "tp.kd.department.role" in self.env:
                kd_role_model = self.env["tp.kd.department.role"]
                if hasattr(kd_role_model, "_project_ids") and kd_role_model._roles(user=user):
                    managed_project_ids.update(kd_role_model._project_ids(user))

        can_manage = is_full_mgr or bool(managed_project_ids)
        return {
            "can_manage": can_manage,
            "is_full_mgr": is_full_mgr,
            "managed_project_ids": sorted(managed_project_ids),
        }

    def _tp_home_my_work_domain(self, Task):
        uid = self.env.uid
        if hasattr(Task, "_tp_my_work_domain"):
            return Task._tp_my_work_domain(include_archived=False) & Domain(
                "state", "!=", "1_canceled",
            )
        non_proj = (
            Domain("project_id", "=", False)
            & Domain("parent_id", "=", False)
            & Domain("user_ids", "in", [uid])
        )
        proj = Domain("project_id", "!=", False) & Domain("user_ids", "in", [uid])
        dom = Domain("active", "=", True) & Domain("state", "!=", "1_canceled") & (non_proj | proj)
        if "is_template" in Task._fields:
            dom &= Domain("is_template", "=", False)
        return dom

    def _tp_home_period_bounds(self, period_key, tz, today_local):
        valid_keys = {k for k, _ in PERIOD_OPTIONS}
        pkey = period_key if period_key in valid_keys else "this_month"
        if pkey == "all":
            return pkey, "Tất cả kỳ", None, None, True
        if pkey == "this_week":
            start_d = today_local - timedelta(days=today_local.weekday())
            end_d = start_d + timedelta(days=6)
            label = f"Tuần này ({start_d.strftime('%d/%m')} – {end_d.strftime('%d/%m/%Y')})"
            s_utc, e_utc = _local_bounds_to_utc_naive(tz, start_d, end_d)
            return pkey, label, s_utc, e_utc, False
        if pkey == "this_quarter":
            q_idx = (today_local.month - 1) // 3
            start_m = q_idx * 3 + 1
            end_m = start_m + 2
            last_day = calendar.monthrange(today_local.year, end_m)[1]
            start_d = date(today_local.year, start_m, 1)
            end_d = date(today_local.year, end_m, last_day)
            label = f"Quý {q_idx + 1}/{today_local.year}"
            s_utc, e_utc = _local_bounds_to_utc_naive(tz, start_d, end_d)
            return pkey, label, s_utc, e_utc, False

        # this_month or this_month_strict
        last_day = calendar.monthrange(today_local.year, today_local.month)[1]
        start_d = date(today_local.year, today_local.month, 1)
        end_d = date(today_local.year, today_local.month, last_day)
        s_utc, e_utc = _local_bounds_to_utc_naive(tz, start_d, end_d)
        if pkey == "this_month_strict":
            label = f"Có hạn tháng {today_local.strftime('%m/%Y')}"
            return pkey, label, s_utc, e_utc, False
        label = f"Tháng {today_local.strftime('%m/%Y')}"
        return pkey, label, s_utc, e_utc, True

    def _tp_home_classify_task_bucket(self, task, now_utc):
        """Non-overlapping business state classification (Section 10.2)."""
        has_exec_field = "tp_exec_report_state" in task._fields
        exec_st = task.tp_exec_report_state if has_exec_field else False
        st = task.state or "01_in_progress"

        # 1. Completed: never inferred from personal Kanban column; reported_done stays pending verification
        is_done = bool(
            exec_st != "reported_done"
            and (st in ("1_done", "03_approved") or exec_st == "verified"),
        )
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
        """Attribute each task to exactly ONE department transparently (Section 10.1):
        1. `project_id.tp_department_id` (explicit executing lead department on project).
        2. `kd_responsible_id`'s active employee department in company.
        3. Unanimous department of `user_ids` in company (`len == 1`);
           if multiple departments -> `cross_dept` ("Liên phòng ban");
           if no department -> `unassigned_dept` ("Chưa gắn phòng ban").
        Never uses `create_uid` and never picks `user_ids[0]` arbitrarily.
        """
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

    def _tp_home_collect_task_dataset(self, params=None):
        """Return validated filter state and classified task records for KPI + Charts + Drilldown."""
        params = dict(params or {})
        Task = self.env["project.task"].sudo(False).with_context(active_test=True)
        if not Task.has_access("read"):
            raise AccessError(self.env._("Tài khoản không có quyền xem công việc."))

        company = self.env.company
        tz, tz_name = _user_tz(self.env)
        today_local = datetime.now(tz).date()
        now_utc = fields.Datetime.now()

        mgmt = self._tp_home_task_management_context(Task, company)
        can_manage = mgmt["can_manage"]

        requested_scope = str(params.get("task_scope") or "").strip()
        if can_manage:
            scope_key = requested_scope if requested_scope in ("managed", "my_work") else "managed"
            scope_options = [
                {"key": "managed", "label": "Phạm vi quản lý"},
                {"key": "my_work", "label": "Công việc của tôi"},
            ]
        else:
            scope_key = "my_work"
            scope_options = [{"key": "my_work", "label": "Công việc của tôi"}]

        my_dom = self._tp_home_my_work_domain(Task)
        if scope_key == "managed" and can_manage:
            proj_dom = (
                Domain("active", "=", True)
                & Domain("state", "!=", "1_canceled")
                & Domain("project_id", "!=", False)
                & Domain("company_id", "in", [False, company.id])
            )
            if "is_template" in Task._fields:
                proj_dom &= Domain("is_template", "=", False)
            if not mgmt["is_full_mgr"]:
                proj_dom &= Domain("project_id", "in", mgmt["managed_project_ids"] or [0])
            scope_dom = proj_dom | my_dom
        else:
            scope_dom = my_dom

        pkey, plabel, s_utc, e_utc, include_open_undated = self._tp_home_period_bounds(
            str(params.get("period") or "this_month").strip(), tz, today_local,
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
        task_dept_map, meta_by_dept = self._tp_home_attribute_task_departments(
            all_scope_tasks, company,
        )

        # Department filter options (only for managers, plus any departments actually present in scope)
        dept_options = [{"key": "", "label": "Tất cả phòng ban"}]
        if can_manage:
            all_company_depts = {}
            if mgmt["is_full_mgr"] and "hr.department" in self.env:
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
        active_dept_key = requested_dept if (can_manage and requested_dept in valid_dept_keys) else ""

        if active_dept_key:
            filtered_tasks = all_scope_tasks.filtered(
                lambda t: task_dept_map.get(t.id) == active_dept_key,
            )
        else:
            filtered_tasks = all_scope_tasks

        bucket_by_task = {}
        undated_included_count = 0
        for t in filtered_tasks:
            b = self._tp_home_classify_task_bucket(t, now_utc)
            bucket_by_task[t.id] = b
            if not t.date_deadline:
                undated_included_count += 1

        if pkey == "this_month":
            period_rule_note = (
                f"Tính theo hạn hoàn thành trong {plabel} ({tz_name})"
                + (
                    f", gồm {undated_included_count} việc đang mở chưa đặt hạn."
                    if undated_included_count
                    else " và các việc đang mở chưa đặt hạn (0 việc)."
                )
            )
        elif pkey == "all":
            period_rule_note = "Gồm toàn bộ công việc đang quản lý trong phạm vi đã chọn (có hoặc chưa đặt hạn)."
        else:
            period_rule_note = f"Chỉ tính công việc có hạn hoàn thành nằm trong {plabel} ({tz_name})."

        return {
            "tasks": filtered_tasks,
            "all_scope_tasks": all_scope_tasks,
            "task_dept_map": task_dept_map,
            "meta_by_dept": meta_by_dept,
            "bucket_by_task": bucket_by_task,
            "undated_included_count": undated_included_count,
            "scope_key": scope_key,
            "scope_label": {o["key"]: o["label"] for o in scope_options}.get(scope_key, ""),
            "scope_options": scope_options,
            "can_filter_department": can_manage,
            "department_key": active_dept_key,
            "department_label": {o["key"]: o["label"] for o in dept_options}.get(
                active_dept_key, "Tất cả phòng ban",
            ),
            "department_options": dept_options,
            "period_key": pkey,
            "period_label": plabel,
            "period_options": [{"key": k, "label": lbl} for k, lbl in PERIOD_OPTIONS],
            "period_rule_note": period_rule_note,
        }

    @api.model
    def _tp_home_build_tasks_and_charts(self, params=None):
        if "project.task" not in self.env:
            return (
                {
                    "key": "tasks",
                    "label": "Công việc",
                    "status": "unconfigured",
                    "count": None,
                    "status_text": "Chưa cài đặt",
                    "tooltip": "Phân hệ Công việc chưa được cài đặt.",
                    "can_open": False,
                    "drilldown": None,
                },
                {"status": "unconfigured"},
            )
        try:
            ds = self._tp_home_collect_task_dataset(params)
            tasks = ds["tasks"]
            bucket_by_task = ds["bucket_by_task"]
            task_dept_map = ds["task_dept_map"]
            meta_by_dept = ds["meta_by_dept"]
            total = len(tasks)

            # Donut classification (sum of slices ALWAYS equals total)
            bucket_defs = list(DONUT_BUCKETS)
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

            # Department stacked bar (sum of completed + incomplete across bars ALWAYS equals total)
            dept_Order_keys = sorted(
                {task_dept_map[t.id] for t in tasks},
                key=lambda dk: (
                    meta_by_dept[dk]["sort_key"],
                    meta_by_dept[dk]["name"].casefold(),
                ),
            )
            bar_rows = []
            for dkey in dept_Order_keys:
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
                },
            }
            charts = {
                "status": "ok",
                "total": total,
                "scope_key": ds["scope_key"],
                "scope_label": ds["scope_label"],
                "scope_options": ds["scope_options"],
                "can_filter_department": ds["can_filter_department"],
                "department_key": ds["department_key"],
                "department_label": ds["department_label"],
                "department_options": ds["department_options"],
                "period_key": ds["period_key"],
                "period_label": ds["period_label"],
                "period_options": ds["period_options"],
                "period_rule_note": ds["period_rule_note"],
                "attribution_note": (
                    "Phân bổ phòng ban mỗi công việc đúng 1 lần theo thứ tự ưu tiên: "
                    "(1) Phòng chủ trì của dự án, (2) Phòng của người chịu trách nhiệm chính, "
                    "(3) Phòng duy nhất của người được giao; việc nhiều phòng đưa vào 'Liên phòng ban', "
                    "chưa có phòng đưa vào 'Chưa gắn phòng ban'."
                ),
                "bar": {
                    "title": "Tình hình công việc",
                    "series": [
                        {"key": "done", "label": "Hoàn thành", "color": "#4E7DE8"},
                        {"key": "incomplete", "label": "Chưa hoàn thành", "color": "#BBD4FA"},
                    ],
                    "rows": bar_rows,
                },
                "donut": {
                    "title": "Tỷ lệ công việc",
                    "center_count": total,
                    "center_label": "Công việc",
                    "slices": donut_slices,
                },
            }
            return kpi, charts
        except AccessError:
            return (
                {
                    "key": "tasks",
                    "label": "Công việc",
                    "status": "no_access",
                    "count": None,
                    "status_text": "Không có quyền xem",
                    "tooltip": "Tài khoản không có quyền xem dữ liệu công việc.",
                    "can_open": False,
                    "drilldown": None,
                },
                {"status": "no_access"},
            )
        except Exception:
            _logger.exception("TP Home: failed to compute Task KPI & charts")
            return (
                {
                    "key": "tasks",
                    "label": "Công việc",
                    "status": "error",
                    "count": None,
                    "status_text": "Tạm lỗi nguồn",
                    "tooltip": "Chưa tải được dữ liệu Công việc. Vui lòng thử làm mới.",
                    "can_open": False,
                    "drilldown": None,
                },
                {"status": "error"},
            )

    @api.model
    def get_tp_home_task_drilldown_action(self, params=None):
        """Return an `ir.actions.act_window` on `project.task` whose count matches KPI / Bar / Donut 100%."""
        self._tp_home_require_internal()
        params = dict(params or {})
        ds = self._tp_home_collect_task_dataset(params)
        tasks = ds["tasks"]
        bucket_by_task = ds["bucket_by_task"]
        task_dept_map = ds["task_dept_map"]
        meta_by_dept = ds["meta_by_dept"]

        bar_dept_key = str(params.get("bar_department_key") or "").strip()
        bar_segment = str(params.get("bar_segment") or "").strip()
        donut_bucket = str(params.get("donut_bucket") or "").strip()

        title_parts = ["Công việc", ds["period_label"]]
        matched = list(tasks)

        if bar_dept_key:
            matched = [t for t in matched if task_dept_map.get(t.id) == bar_dept_key]
            dname = meta_by_dept.get(bar_dept_key, {}).get("name") or bar_dept_key
            title_parts.append(dname)
        elif ds["department_key"]:
            title_parts.append(ds["department_label"])

        if bar_segment == "done":
            matched = [t for t in matched if bucket_by_task.get(t.id) == "done"]
            title_parts.append("Hoàn thành")
        elif bar_segment == "incomplete":
            matched = [t for t in matched if bucket_by_task.get(t.id) != "done"]
            title_parts.append("Chưa hoàn thành")
        elif donut_bucket:
            matched = [t for t in matched if bucket_by_task.get(t.id) == donut_bucket]
            blabel = {
                k: lbl for k, lbl, _ in (*DONUT_BUCKETS, UNMAPPED_BUCKET)
            }.get(donut_bucket, donut_bucket)
            title_parts.append(blabel)

        matched_ids = [t.id for t in matched]
        return {
            "type": "ir.actions.act_window",
            "name": " · ".join(title_parts),
            "res_model": "project.task",
            "view_mode": "list,form",
            "views": [(False, "list"), (False, "form")],
            "domain": [("id", "in", matched_ids)],
            "context": {"create": False},
        }

    # ------------------------------------------------------------------
    # 5. AGENDA: CÔNG VIỆC HÔM NAY (Tasks due today + Calendar today)
    # ------------------------------------------------------------------
    def _tp_home_collect_today_agenda_items(self):
        tz, tz_name = _user_tz(self.env)
        now_local = datetime.now(tz)
        today_local = now_local.date()
        start_utc, stop_utc = _local_bounds_to_utc_naive(tz, today_local, today_local)
        now_utc = fields.Datetime.now()
        uid = self.env.uid
        my_pid = self.env.user.partner_id.id
        has_personal_tools = "tp_exec_report_state" in self.env.get("project.task", self.env["res.users"])._fields

        items = []
        linked_task_ids_in_events = set()

        # A. Today's Calendar Events / Meetings where user is organizer or participant
        if "calendar.event" in self.env:
            Event = self.env["calendar.event"].sudo(False)
            if Event.has_access("read"):
                ev_dom = (
                    Domain("active", "=", True)
                    & Domain("start", "<", stop_utc)
                    & Domain("stop", ">=", start_utc)
                    & (Domain("partner_ids", "in", [my_pid]) | Domain("user_id", "=", uid))
                )
                events = Event.search(ev_dom, order="allday desc, start asc, id asc", limit=100)
                for ev in events:
                    if hasattr(ev, "_check_private_event_conditions") and ev._check_private_event_conditions():
                        continue
                    my_att = ev.attendee_ids.filtered(lambda a: a.partner_id.id == my_pid)[:1]
                    if my_att and my_att.state == "declined":
                        continue

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
                        sort_key = (1, st_loc.strftime("%H:%M"), ev.id)

                    linked_task = None
                    if ev.res_model == "project.task" and ev.res_id and "project.task" in self.env:
                        t_rec = self.env["project.task"].sudo(False).browse(ev.res_id).exists()
                        if t_rec and t_rec.has_access("read") and t_rec.active:
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
                    self._tp_home_my_work_domain(Task)
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

                    tone_map = {
                        "done": "green",
                        "in_progress": "teal",
                        "waiting": "amber",
                        "overdue": "red",
                    }
                    status_map = {
                        "done": "Hoàn thành",
                        "in_progress": "Đang thực hiện",
                        "waiting": "Chờ xử lý",
                        "overdue": "Quá hạn",
                    }
                    items.append(
                        {
                            "uid_key": f"task-{task.id}",
                            "kind": "task",
                            "kind_label": "Công việc",
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
    def _tp_home_agenda_summary(self, preview_limit=5):
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

    # ------------------------------------------------------------------
    # 6. UNIFIED DASHBOARD ENDPOINT
    # ------------------------------------------------------------------
    @api.model
    def get_tp_home_dashboard(self, params=None):
        user = self._tp_home_require_internal()
        tz, tz_name = _user_tz(self.env)
        now_local = datetime.now(tz)

        hr_kpi = self._tp_home_kpi_hr()
        req_kpi = self._tp_home_kpi_requests()
        task_kpi, charts = self._tp_home_build_tasks_and_charts(params)
        stock_kpi = self._tp_home_kpi_stock()
        agenda = self._tp_home_agenda_summary(preview_limit=5)

        return {
            "meta": {
                "user_id": user.id,
                "company_id": self.env.company.id,
                "company_name": self.env.company.name,
                "timezone": tz_name,
                "updated_at": now_local.strftime("%H:%M:%S · %d/%m/%Y"),
                "updated_short": now_local.strftime("%H:%M"),
            },
            "kpis": {
                "hr": hr_kpi,
                "requests": req_kpi,
                "tasks": task_kpi,
                "stock": stock_kpi,
            },
            "agenda": agenda,
            "charts": charts,
        }

    # ------------------------------------------------------------------
    # 7. PERMISSION-CHECKED DOCUMENT / METADATA SEARCH FOR NAVBAR
    # ------------------------------------------------------------------
    @api.model
    def search_tp_home_global(self, query="", limit=8):
        """Search permitted documents & records by name/code/metadata without `ir.attachment.sudo()`.

        Every source checks both model read ACL and the source's own business-scope guard
        so unauthorized titles/codes never leak through search results.
        """
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
        company = self.env.company
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
                                    or (rec.project_id and hasattr(rec.project_id, "_tp_scope_allowed") and rec.project_id._tp_scope_allowed(self.env.user))
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

        # 5. Hồ sơ Yêu cầu phê duyệt (`tp.request`) — strictly caller-accessible requests
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
                        r_dom = ["|", ("requester_user_id", "=", uid), ("approval_state", "!=", "draft")]
                    else:
                        r_dom = [
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
        return result
