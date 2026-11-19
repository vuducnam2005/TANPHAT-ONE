"""Synchronization service and audit logs for ENTI attendance integration (ENTI-LIVE-001).

Manages credentials securely (secrets file, environment variables, or encrypted params),
orchestrates EntiClient fetching, employee mapping, raw day storage, canonical projection,
locking against concurrent jobs, and bus notification for live UI updates.
"""
import json
import logging
import os
import time
from datetime import date, datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .attendance_common import DEFAULT_TZ, internal, local_today
from .enti_client import EntiAuthError, EntiClient, EntiError
from .enti_day import _parse_time_str

_logger = logging.getLogger(__name__)

ADVISORY_KEY_ENTI = 761129
SECRETS_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".local", "enti_secrets.json")


def _get_enti_credentials(env):
    """Retrieve credentials securely without exposing them in logs or to browser.

    Checks:
    1. .local/enti_secrets.json on disk
    2. Environment variables: ENTI_PHONE, ENTI_PASSWORD, ENTI_APP_KEY
    3. ir.config_parameter (system parameters)
    """
    phone, password, app_key = None, None, None

    # Check local secrets file
    try:
        norm_path = os.path.abspath(SECRETS_FILE_PATH)
        if os.path.isfile(norm_path):
            with open(norm_path, encoding="utf-8") as f:
                data = json.load(f)
                phone = (data.get("phone") or "").strip()
                password = (data.get("password") or "").strip()
                app_key = (data.get("app_key") or "").strip()
    except Exception as exc:
        _logger.warning("Could not read local ENTI secrets file: %s", exc)

    # Check environment variables
    if not phone or not password:
        phone = os.environ.get("ENTI_PHONE") or os.environ.get("TP_ENTI_PHONE") or phone
        password = os.environ.get("ENTI_PASSWORD") or os.environ.get("TP_ENTI_PASSWORD") or password
        app_key = os.environ.get("ENTI_APP_KEY") or os.environ.get("TP_ENTI_APP_KEY") or app_key

    # Check ir.config_parameter
    if not phone or not password:
        Param = env["ir.config_parameter"].sudo()
        get_val = getattr(Param, "get_str", None) or getattr(Param, "get_param", None)
        if get_val:
            p_phone = get_val("tp_hr_attendance.enti_phone")
            p_pass = get_val("tp_hr_attendance.enti_password")
            p_app = get_val("tp_hr_attendance.enti_app_key")
            phone = phone or (p_phone.strip() if p_phone else None)
            password = password or (p_pass.strip() if p_pass else None)
            app_key = app_key or (p_app.strip() if p_app else None)

    return phone, password, app_key


def _save_enti_credentials(env, phone, password, app_key=None):
    """Save credentials to local secrets file and/or ir.config_parameter."""
    try:
        norm_path = os.path.abspath(SECRETS_FILE_PATH)
        os.makedirs(os.path.dirname(norm_path), exist_ok=True)
        data = {
            "phone": phone.strip(),
            "password": password.strip(),
            "app_key": (app_key or "").strip(),
            "updated_at": fields.Datetime.now().isoformat(),
        }
        with open(norm_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as exc:
        _logger.warning("Could not write to local ENTI secrets file: %s", exc)

    Param = env["ir.config_parameter"].sudo()
    set_val = getattr(Param, "set_str", None) or getattr(Param, "set_param", None)
    if set_val:
        set_val("tp_hr_attendance.enti_phone", phone.strip())
        set_val("tp_hr_attendance.enti_password", password.strip())
        if app_key:
            set_val("tp_hr_attendance.enti_app_key", app_key.strip())


class AttendanceEntiSyncLog(models.Model):
    _name = "tp.hr.attendance.enti.sync.log"
    _description = "Nhật ký đồng bộ ENTI"
    _order = "synced_at desc, id desc"
    _check_company_auto = True

    source_id = fields.Many2one(
        "tp.hr.attendance.source",
        "Nguồn dữ liệu",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="source_id.company_id",
        store=True,
        string="Công ty",
        index=True,
    )
    start_date = fields.Date("Từ ngày", required=True)
    end_date = fields.Date("Đến ngày", required=True)
    synced_at = fields.Datetime("Thời điểm đồng bộ", default=fields.Datetime.now, required=True)
    duration_seconds = fields.Float("Thời gian thực hiện (giây)", digits=(6, 2))

    employee_count = fields.Integer("Số nhân viên ENTI trả về")
    mapped_count = fields.Integer("Số nhân viên đã khớp Odoo")
    unmapped_count = fields.Integer("Số nhân viên chưa đối chiếu")
    days_received = fields.Integer("Số bản ghi ngày nhận được")
    days_applied = fields.Integer("Số bản ghi ngày áp dụng")

    state = fields.Selection([("success", "Thành công"), ("error", "Lỗi")], "Kết quả", required=True)
    message = fields.Text("Thông báo / Ghi chú")


class AttendanceSourceEnti(models.Model):
    _inherit = "tp.hr.attendance.source"

    def _lock_enti_sync(self):
        self.ensure_one()
        self.env.cr.execute("SELECT id FROM tp_hr_attendance_source WHERE id=%s FOR UPDATE", [self.id])
        self.invalidate_recordset()
        self.env.cr.execute("SELECT pg_advisory_xact_lock(%s, %s)", [ADVISORY_KEY_ENTI, self.id])

    def action_sync_enti_now(self, start_date=None, end_date=None):
        """Action for Admin / HR to trigger an immediate sync."""
        self.ensure_one()
        if not self.env.user.has_group("hr.group_hr_manager") and not self.env.su:
            raise AccessError(self.env._("Chỉ Quản lý nhân sự hoặc Admin mới được kích hoạt đồng bộ."))
        return self._tp_execute_sync(start_date=start_date, end_date=end_date)

    @api.model
    def action_sync_enti_quick(self):
        """Quick sync action invoked from UI button without needing recordset ID."""
        if not self.env.user.has_group("hr.group_hr_manager") and not self.env.su:
            raise AccessError(self.env._("Chỉ Quản lý nhân sự hoặc Admin mới được kích hoạt đồng bộ."))
        company = self.env.company
        source = self.search([("kind", "=", "enti_api"), ("company_id", "=", company.id)], limit=1)
        if not source:
            source = self.search([("kind", "=", "device_api"), ("company_id", "=", company.id)], limit=1)
        if not source:
            phone, password, _ = _get_enti_credentials(self.env)
            if phone and password:
                source = internal(self).create({
                    "name": "API máy chấm công ENTI",
                    "namespace": "enti-tanphat",
                    "kind": "enti_api",
                    "company_id": company.id,
                    "timezone": DEFAULT_TZ,
                    "state": "ready",
                    "live_enabled": True,
                })
            else:
                raise UserError(self.env._("Chưa cấu hình tài khoản ENTI. Vui lòng vào Cấu hình kết nối ENTI trước."))
        return source.action_sync_enti_now()

    @api.model
    def _tp_cron_enti_sync(self):
        """Cron entry point for automatic scheduled ENTI sync."""
        sources = self.search([
            ("kind", "in", ("enti_api", "device_api")),
            ("live_enabled", "=", True),
            ("state", "in", ("ready", "connected")),
        ])
        for source in sources:
            try:
                # Sync today and recent 5 days to capture late clock-outs / adjustments
                today = local_today(source.timezone or DEFAULT_TZ)
                start = max(date(today.year, today.month, 1), today - timedelta(days=5))
                source._tp_execute_sync(start_date=start, end_date=today)
            except Exception as exc:
                _logger.error("Cron ENTI sync error for source %s: %s", source.name, exc)

    def _tp_execute_sync(self, start_date=None, end_date=None):
        """Execute full ENTI synchronization cycle."""
        self.ensure_one()
        self._lock_enti_sync()

        start_time = time.time()
        now = fields.Datetime.now()
        company = self.company_id
        today = local_today(self.timezone or DEFAULT_TZ)

        if not end_date:
            end_date = today
        if not start_date:
            # Default to 1st of current month
            start_date = date(end_date.year, end_date.month, 1)

        phone, password, app_key = _get_enti_credentials(self.env)
        if not phone or not password:
            msg = "Chưa cấu hình thông tin xác thực ENTI trên máy chủ hoặc biến môi trường."
            internal(self).write({
                "state": "not_configured",
                "last_error_at": now,
                "last_error": msg,
            })
            raise UserError(self.env._(msg))

        client = EntiClient()
        Log = self.env["tp.hr.attendance.enti.sync.log"].sudo()
        Mapping = self.env["tp.hr.attendance.enti.mapping"].sudo()
        EntiDay = self.env["tp.hr.attendance.enti.day"].sudo()

        try:
            # 1. Login
            client.login(phone, password)

            # 2. Select application
            if not app_key:
                app = client.find_app_for_company(company.name or "Tấn Phát")
                if not app:
                    raise EntiError("Không tìm thấy ứng dụng công ty Tấn Phát trên tài khoản ENTI này.")
                app_key = app.get("app_key") or app.get("key") or app.get("id")

            client.select_app(app_key)

            # 3. Fetch departments & employees metadata for mapping
            try:
                enti_emps = client.get_employees()
            except Exception as exc:
                _logger.warning("Could not fetch ENTI employees info: %s; will parse from board", exc)
                enti_emps = []

            for emp_info in enti_emps:
                Mapping.tp_suggest_mapping(self, emp_info)

            # 4. Fetch attendance board with pagination
            att_result = client.get_attendance(start_date, end_date)
            board_data = att_result.get("data") or []

            days_received = 0
            days_applied = 0

            # Process each employee returned by ENTI
            for emp_board in board_data:
                key_nv = emp_board.get("keyNV")
                if not key_nv:
                    continue

                # Ensure mapping exists for this employee
                mapping = Mapping.tp_suggest_mapping(self, emp_board)
                employee_id = mapping.employee_id.id if (mapping and mapping.state == "mapped") else False

                # Process day1 through day32
                for day_idx in range(1, 33):
                    day_key = f"day{day_idx}"
                    day_obj = emp_board.get(day_key)
                    if not day_obj or not isinstance(day_obj, dict):
                        continue

                    # MANDATORY: Extract date from field 'ngay', NEVER assume day1 is 1st of month
                    raw_ngay = day_obj.get("ngay")
                    if not raw_ngay:
                        continue

                    try:
                        work_date = datetime.fromisoformat(str(raw_ngay).split("T")[0]).date()
                    except (ValueError, TypeError):
                        continue

                    days_received += 1

                    # Parse clock times
                    vao_dau = day_obj.get("vaoDau")
                    ra_cuoi = day_obj.get("raCuoi")
                    in_clock, in_utc = _parse_time_str(vao_dau, work_date, self.timezone)
                    out_clock, out_utc = _parse_time_str(ra_cuoi, work_date, self.timezone)

                    enti_day_vals = {
                        "source_id": self.id,
                        "key_nv": key_nv,
                        "work_date": work_date,
                        "employee_id": employee_id,
                        "ca_lv": day_obj.get("caLV") or "",
                        "vao_dau": in_clock,
                        "ra_cuoi": out_clock,
                        "check_in_dt": in_utc,
                        "check_out_dt": out_utc,
                        "day_of_week": day_obj.get("dayOfWeek") or 0,
                        "thu_trong_tuan": day_obj.get("thuTrongTuan") or "",
                        "di_muon": int(day_obj.get("diMuon") or 0),
                        "ve_som": int(day_obj.get("veSom") or 0),
                        "lam_chinh": float(day_obj.get("lamChinh") or 0.0),
                        "lam_them": float(day_obj.get("lamThem") or 0.0),
                        "cong_lam": float(day_obj.get("congLam") or 0.0),
                        "ky_hieu": day_obj.get("kyHieu") or "",
                        "raw_json": json.dumps(day_obj, ensure_ascii=False),
                        "received_at": now,
                    }

                    existing_day = EntiDay.search([
                        ("source_id", "=", self.id),
                        ("key_nv", "=", key_nv),
                        ("work_date", "=", work_date),
                    ], limit=1)

                    if existing_day:
                        existing_day.write(enti_day_vals)
                        day_record = existing_day
                    else:
                        day_record = EntiDay.create(enti_day_vals)

                    # Project into canonical day summary if employee is mapped
                    if employee_id:
                        day_record._tp_project_to_canonical()
                        days_applied += 1

            # Recount mappings
            all_mappings = Mapping.search([("source_id", "=", self.id)])
            mapped_count = all_mappings.filtered(lambda m: m.state == "mapped")
            unmapped_count = all_mappings - mapped_count

            duration = round(time.time() - start_time, 2)

            # Update source state
            internal(self).write({
                "state": "ready",
                "live_enabled": True,
                "last_success_at": now,
                "latest_event_at": now,
                "watermark": end_date.isoformat(),
                "last_error": False,
            })

            # Create sync log
            log = Log.create({
                "source_id": self.id,
                "start_date": start_date,
                "end_date": end_date,
                "synced_at": now,
                "duration_seconds": duration,
                "employee_count": len(board_data),
                "mapped_count": len(mapped_count),
                "unmapped_count": len(unmapped_count),
                "days_received": days_received,
                "days_applied": days_applied,
                "state": "success",
                "message": f"Đồng bộ thành công {len(board_data)} nhân viên, {days_applied} ngày công đã áp dụng.",
            })

            # Broadcast live update event to frontend via bus
            try:
                self.env["bus.bus"]._sendone(
                    "tp_hr_attendance_channel",
                    "enti_sync_completed",
                    {
                        "source_id": self.id,
                        "synced_at": now.isoformat(),
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "days_applied": days_applied,
                    },
                )
            except Exception as exc:
                _logger.warning("Could not broadcast bus message: %s", exc)

            return {
                "success": True,
                "employees": len(board_data),
                "mapped": len(mapped_count),
                "unmapped": len(unmapped_count),
                "days_applied": days_applied,
                "duration": duration,
            }

        except Exception as exc:
            duration = round(time.time() - start_time, 2)
            err_msg = str(exc)
            _logger.error("ENTI sync failed: %s", err_msg)
            internal(self).write({
                "last_error_at": now,
                "last_error": err_msg[:240],
            })
            Log.create({
                "source_id": self.id,
                "start_date": start_date,
                "end_date": end_date,
                "synced_at": now,
                "duration_seconds": duration,
                "state": "error",
                "message": err_msg,
            })
            raise UserError(self.env._("Đồng bộ ENTI thất bại: %(err)s", err=err_msg)) from exc
