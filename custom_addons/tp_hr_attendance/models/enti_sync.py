"""Synchronization service and audit logs for ENTI attendance integration (ENTI-LIVE-001, ENTI-ATTENDANCE-002).

One backend job talks to ENTI; browsers never do. The cron keeps one authenticated client per database and
source in process memory (token and session cookies are never stored), reads the recent window every
``FULL_EVERY`` seconds and "today" every ``enti_fast_poll_seconds`` (default 15 s) during working hours, writes
only the employee-days whose ENTI values changed, projects them into the canonical day (approved correction >
locked period > ENTI > Excel) and wakes browsers through the bus only when something changed. A failed or
partial answer never deletes stored attendance.

Measured latency is "punch time reported by ENTI -> Odoo detected the change": it includes the machine -> ENTI
upload and the machine clock, which Odoo cannot separate.
"""
import hashlib
import json
import logging
import os
import statistics
import time
from datetime import date, timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .attendance_common import DEFAULT_TZ, internal, local_today
from .enti_client import EntiAuthError, EntiError, cached_client, drop_cached_client
from .enti_day import _parse_time_str

_logger = logging.getLogger(__name__)

ADVISORY_KEY_ENTI = 761129
SECRETS_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".local", "enti_secrets.json")
CRON_XMLID = "tp_hr_attendance.ir_cron_enti_attendance_sync"
PARAM_FAST_SECONDS = "tp_hr_attendance.enti_fast_poll_seconds"
PARAM_FAST_WINDOW = "tp_hr_attendance.enti_fast_poll_window"
DEFAULT_FAST_SECONDS = 15
MIN_FAST_SECONDS = 10
DEFAULT_FAST_WINDOW = 50
MAX_FAST_WINDOW = 100
FAST_HOURS = (5, 22)            # local hours [from, to) polled every few seconds; otherwise once per cron minute
RECENT_DAYS = 5                 # the recent window re-read for late corrections and yesterday's out time
FULL_EVERY = 300                # seconds between two reads of the recent window
HEARTBEAT_EVERY = 1800          # an unchanged successful window read is logged at most every 30 minutes
ERROR_LOG_EVERY = 900           # the same error is logged again at most every 15 minutes
LATENCY_HORIZON = 6 * 3600      # older punches are backfill, not live latency
BUS_TYPE = "tp_hr_attendance/updated"
DAY_KEYS = ("caLV", "vaoDau", "raCuoi", "diMuon", "veSom", "lamChinh", "lamThem", "congLam", "kyHieu",
            "dayOfWeek", "thuTrongTuan")
# (dbname, source id) -> pacing and counters of this process; restarting Odoo simply starts with a full read.
_PACE = {}


class EntiNotConfigured(EntiError):
    """No ENTI account is configured on the server."""


def _digest(day_obj):
    payload = {key: day_obj.get(key) for key in DAY_KEYS}
    return hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _number(value, cast=float):
    try:
        return cast(float(value or 0))
    except (TypeError, ValueError):
        return cast(0)


def _same(old, new):
    if isinstance(old, float) or isinstance(new, float):
        return abs(float(old or 0) - float(new or 0)) < 1e-6
    return (old or False) == (new or False)


def _error_text(exc):
    if isinstance(exc, EntiError):
        return str(exc)
    return f"Lỗi xử lý dữ liệu ENTI ({type(exc).__name__}); giữ nguyên dữ liệu cũ."


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
    origin = fields.Selection([("cron", "Tự động"), ("manual", "Thủ công")], "Kích hoạt", default="cron")
    scope = fields.Selection([("window", "Khoảng gần đây"), ("today", "Hôm nay"), ("range", "Khoảng chọn")], "Phạm vi")

    employee_count = fields.Integer("Số nhân viên ENTI trả về")
    mapped_count = fields.Integer("Số nhân viên đã khớp Odoo")
    unmapped_count = fields.Integer("Số nhân viên chưa đối chiếu")
    days_received = fields.Integer("Số bản ghi ngày nhận được")
    days_applied = fields.Integer("Số ngày công cập nhật vào bảng công")
    changed_count = fields.Integer("Số ngày ENTI thay đổi")
    kept_count = fields.Integer("Số ngày giữ giờ cũ",
                                help="ENTI trả ngày trống cho ngày đang có giờ chấm; Odoo giữ giờ cũ để không mất dữ liệu.")
    polls = fields.Integer("Số lượt hỏi ENTI thành công từ lần ghi trước")
    latency_max_seconds = fields.Float("Độ trễ giờ chấm → Odoo lớn nhất (giây)", digits=(8, 1))
    latency_median_seconds = fields.Float("Độ trễ giờ chấm → Odoo trung vị (giây)", digits=(8, 1))

    state = fields.Selection([("success", "Thành công"), ("error", "Lỗi")], "Kết quả", required=True)
    message = fields.Text("Thông báo / Ghi chú")

    @api.autovacuum
    def _gc_quiet_logs(self):
        """Unchanged successful reads older than 30 days carry no history; changes and errors are kept."""
        limit = fields.Datetime.now() - timedelta(days=30)
        self.sudo().search([
            ("synced_at", "<", limit), ("state", "=", "success"), ("changed_count", "=", 0), ("kept_count", "=", 0),
        ]).unlink()


class AttendanceSourceEnti(models.Model):
    _inherit = "tp.hr.attendance.source"

    # ------------------------------------------------------------------ locking / client
    def _lock_enti_sync(self):
        self.ensure_one()
        self.env.cr.execute("SELECT id FROM tp_hr_attendance_source WHERE id=%s FOR UPDATE", [self.id])
        self.invalidate_recordset()
        self.env.cr.execute("SELECT pg_advisory_xact_lock(%s, %s)", [ADVISORY_KEY_ENTI, self.id])

    def _tp_try_lock_enti(self):
        """Non-blocking variant for the cron: skip this round when a manual sync holds the source."""
        self.ensure_one()
        self.env.cr.execute("SELECT pg_try_advisory_xact_lock(%s, %s)", [ADVISORY_KEY_ENTI, self.id])
        if not self.env.cr.fetchone()[0]:
            return False
        self.env.cr.execute("SELECT id FROM tp_hr_attendance_source WHERE id=%s FOR UPDATE", [self.id])
        self.invalidate_recordset()
        return True

    def _tp_pace(self):
        return _PACE.setdefault((self.env.cr.dbname, self.id), {
            "poll": None, "window": None, "heartbeat": None, "error_log": None, "polls": 0, "fails": 0,
            "healthy": None,
        })

    def _tp_enti_entry(self):
        """Cached client entry for this source; a credential change starts a fresh client (fresh login)."""
        phone, password, app_key = _get_enti_credentials(self.env)
        if not phone or not password:
            raise EntiNotConfigured("Chưa cấu hình tài khoản ENTI trên máy chủ (tệp bí mật, biến môi trường hoặc tham số hệ thống).")
        key = (self.env.cr.dbname, self.id)
        fingerprint = hashlib.sha256("\x00".join((phone, password, app_key or "")).encode()).hexdigest()
        entry = cached_client(key)
        if entry.get("fingerprint") not in (None, fingerprint):
            drop_cached_client(key)
            entry = cached_client(key)
        entry["fingerprint"] = fingerprint
        return entry, phone, password, app_key

    def _tp_enti_ready(self, entry, phone, password, app_key):
        """Log in only when the cached client has no session; select the company application once."""
        client = entry["client"]
        if not client.access_token:
            client.login(phone, password)
            entry["app_key"] = None
        if not entry.get("app_key"):
            chosen = app_key
            if not chosen:
                app = client.find_app_for_company(self.company_id.name)
                if not app:
                    raise EntiError(
                        "Không xác định được duy nhất ứng dụng công ty Tấn Phát trên tài khoản ENTI; "
                        "cần khai báo app_key trong Cấu hình kết nối ENTI.",
                    )
                chosen = app.get("app_key") or app.get("key") or app.get("id")
            client.select_app(chosen)
            entry["app_key"] = chosen
        return client

    # ------------------------------------------------------------------ public entry points
    def action_sync_enti_now(self, start_date=None, end_date=None):
        """Action for Admin / HR to trigger an immediate sync. Returns the result (``success`` False on error)."""
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

    def _tp_execute_sync(self, start_date=None, end_date=None):
        """Manual full sync of [start_date, end_date] (default: this month up to today)."""
        self.ensure_one()
        today = local_today(self.timezone or DEFAULT_TZ)
        end_date = min(end_date or today, today)
        start_date = start_date or date(end_date.year, end_date.month, 1)
        return self._tp_run_enti(start_date, end_date, scope="range", origin="manual", wait=True)

    @api.model
    def _tp_live_enti_sources(self):
        return self.search([
            ("kind", "=", "enti_api"),
            ("live_enabled", "=", True),
            ("state", "!=", "paused"),
        ])

    @api.model
    def _tp_fast_settings(self):
        """(seconds between "today" polls, seconds one cron run keeps polling); 0 disables fast polling."""
        Param = self.env["ir.config_parameter"].sudo()
        # Odoo 20 typed parameters; a missing or invalid value falls back to the default.
        interval = _number(Param.get_int(PARAM_FAST_SECONDS, DEFAULT_FAST_SECONDS), int)
        window = _number(Param.get_int(PARAM_FAST_WINDOW, DEFAULT_FAST_WINDOW), int)
        if interval <= 0:
            return 0, 0
        interval = max(interval, MIN_FAST_SECONDS)
        return interval, min(max(window, interval), MAX_FAST_WINDOW)

    def _tp_fast_hours(self):
        hour = fields.Datetime.context_timestamp(self.with_context(tz=self.timezone or DEFAULT_TZ), fields.Datetime.now()).hour
        return FAST_HOURS[0] <= hour < FAST_HOURS[1]

    def _tp_poll_wait(self, interval):
        """Seconds until this source may be read again: the poll interval, longer after failures (30/60/120 s)."""
        pace = self._tp_pace()
        if pace["poll"] is None:
            return 0.0
        gap = max(interval, min(15 * 2 ** pace["fails"], 120)) if pace["fails"] else interval
        return max(0.0, pace["poll"] + gap - time.monotonic())

    @api.model
    def _tp_cron_enti_sync(self):
        """Cron entry point. Inside the cron it keeps polling "today" every few seconds for about one minute,
        committing after every round, then re-arms itself so the next run starts right after the other jobs."""
        in_cron = bool(self.env.context.get("cron_id"))
        interval, window = self._tp_fast_settings() if in_cron else (0, 0)
        deadline = time.monotonic() + window
        rounds = 0
        while True:
            sources = self._tp_live_enti_sources()
            if rounds:
                sources = sources.filtered(lambda s: s._tp_fast_hours())
            wait = 0.0
            if interval and sources:
                waits = {source.id: source._tp_poll_wait(interval) for source in sources}
                sources = sources.filtered(lambda s: time.monotonic() + waits[s.id] <= deadline)
                wait = max((waits[source.id] for source in sources), default=0.0)
            if not sources:
                break
            if wait:
                time.sleep(wait)
                self.env.invalidate_all()
            for source in sources:
                source._tp_cron_pass()
                if in_cron:
                    self.env["ir.cron"]._commit_progress()
                    self.env.invalidate_all()
            rounds += 1
            if not interval:
                break
        if interval and rounds and self._tp_live_enti_sources().filtered(lambda s: s._tp_fast_hours()):
            cron = self.env.ref(CRON_XMLID, raise_if_not_found=False)
            if cron:
                cron.sudo()._trigger()

    def _tp_cron_pass(self):
        """One cron read: the recent window every FULL_EVERY seconds, otherwise only today."""
        self.ensure_one()
        pace = self._tp_pace()
        today = local_today(self.timezone or DEFAULT_TZ)
        full = pace["window"] is None or time.monotonic() - pace["window"] >= FULL_EVERY
        start = today - timedelta(days=RECENT_DAYS) if full else today
        return self._tp_run_enti(start, today, scope="window" if full else "today", origin="cron", wait=False)

    # ------------------------------------------------------------------ one sync
    def _tp_run_enti(self, start_date, end_date, *, scope, origin, wait):
        """Fetch, store and project [start_date, end_date]; never raises for ENTI/data errors."""
        self.ensure_one()
        started = time.monotonic()
        now = fields.Datetime.now()
        if wait:
            self._lock_enti_sync()
        elif not self._tp_try_lock_enti():
            return {"success": False, "skipped": True, "message": "Đang có lượt đồng bộ ENTI khác chạy."}

        try:
            entry, phone, password, app_key = self._tp_enti_entry()
        except EntiNotConfigured as exc:
            if self.state != "not_configured":
                internal(self).write({"state": "not_configured"})
            return self._tp_enti_failed(exc, start_date, end_date, scope, origin, started, now)

        if not entry["lock"].acquire(timeout=90):
            return {"success": False, "skipped": True, "message": "Phiên ENTI đang bận; thử lại lượt sau."}
        try:
            with self.env.cr.savepoint():
                client = self._tp_enti_ready(entry, phone, password, app_key)
                stats = self._tp_enti_apply(client, start_date, end_date, with_directory=scope != "today")
        except Exception as exc:  # noqa: BLE001 - every failure keeps stored data and is reported
            if isinstance(exc, EntiAuthError):
                drop_cached_client((self.env.cr.dbname, self.id))
            if not isinstance(exc, EntiError):
                _logger.exception("ENTI sync processing failed for source %s", self.id)
            self.env.invalidate_all()
            return self._tp_enti_failed(exc, start_date, end_date, scope, origin, started, now)
        finally:
            entry["lock"].release()
        return self._tp_enti_succeeded(stats, start_date, end_date, scope, origin, started, now)

    def _tp_enti_day_values(self, work_date, day_obj, tz):
        in_clock, in_utc = _parse_time_str(day_obj.get("vaoDau"), work_date, tz)
        out_clock, out_utc = _parse_time_str(day_obj.get("raCuoi"), work_date, tz)
        return {
            "ca_lv": day_obj.get("caLV") or "",
            "vao_dau": in_clock,
            "ra_cuoi": out_clock,
            "check_in_dt": in_utc or False,
            "check_out_dt": out_utc or False,
            "day_of_week": _number(day_obj.get("dayOfWeek"), int),
            "thu_trong_tuan": day_obj.get("thuTrongTuan") or "",
            "di_muon": _number(day_obj.get("diMuon"), int),
            "ve_som": _number(day_obj.get("veSom"), int),
            "lam_chinh": _number(day_obj.get("lamChinh")),
            "lam_them": _number(day_obj.get("lamThem")),
            "cong_lam": _number(day_obj.get("congLam")),
            "ky_hieu": day_obj.get("kyHieu") or "",
        }

    def _tp_enti_apply(self, client, start_date, end_date, *, with_directory):
        """Read the ENTI board for the range and store what changed. Raises on any ENTI error (caller rolls back)."""
        self.ensure_one()
        Mapping = self.env["tp.hr.attendance.enti.mapping"].sudo()
        EntiDay = self.env["tp.hr.attendance.enti.day"].sudo()
        tz = self.timezone or DEFAULT_TZ
        now = fields.Datetime.now()
        index = Mapping._tp_name_index(self.company_id)
        mappings = {m.key_nv: m for m in Mapping.search([("source_id", "=", self.id)])}

        if with_directory:
            try:
                directory = client.get_employees()
            except EntiError as exc:
                _logger.warning("ENTI employee directory unavailable (%s); mapping from the board only", exc)
                directory = []
            for info in directory:
                key = (info.get("keyNV") or "").strip()
                if key:
                    mappings[key] = Mapping.tp_suggest_mapping(self, info, index=index, existing=mappings.get(key))

        board = client.get_attendance(start_date, end_date)
        rows = board.get("data") or []
        if not rows:
            raise EntiError(f"ENTI không trả nhân viên nào cho {start_date:%d/%m}–{end_date:%d/%m}; giữ nguyên dữ liệu cũ.")

        stored = {
            (day.key_nv, day.work_date): day
            for day in EntiDay.search([
                ("source_id", "=", self.id), ("work_date", ">=", start_date), ("work_date", "<=", end_date),
            ])
        }
        stats = {"employees": len(rows), "pages": board.get("pages") or 1, "received": 0, "changed": 0,
                 "applied": 0, "kept": 0, "latencies": [], "dates": set()}

        for row in rows:
            key_nv = (row.get("keyNV") or "").strip()
            if not key_nv:
                continue
            mapping = Mapping.tp_suggest_mapping(self, row, index=index, existing=mappings.get(key_nv))
            mappings[key_nv] = mapping
            employee_id = mapping.employee_id.id if mapping.state == "mapped" and mapping.employee_id else False

            for slot in range(1, 33):
                day_obj = row.get(f"day{slot}")
                if not isinstance(day_obj, dict) or not day_obj.get("ngay"):
                    continue
                # MANDATORY: the date comes from 'ngay', never from the slot number
                try:
                    work_date = date.fromisoformat(str(day_obj["ngay"])[:10])
                except ValueError:
                    continue
                if not start_date <= work_date <= end_date:
                    continue
                stats["received"] += 1
                self._tp_enti_store_day(stored, key_nv, work_date, day_obj, employee_id, tz, now, stats)

        stats["mapped"] = Mapping.search_count([("source_id", "=", self.id), ("state", "=", "mapped")])
        stats["unmapped"] = Mapping.search_count([("source_id", "=", self.id), ("state", "!=", "mapped")])
        return stats

    def _tp_enti_store_day(self, stored, key_nv, work_date, day_obj, employee_id, tz, now, stats):
        EntiDay = self.env["tp.hr.attendance.enti.day"].sudo()
        digest = _digest(day_obj)
        old = stored.get((key_nv, work_date))
        if old and old.raw_hash == digest and old.employee_id.id == employee_id and (
            not employee_id or old.state != "pending_map"
        ):
            return
        vals = self._tp_enti_day_values(work_date, day_obj, tz)
        if old and (old.vao_dau or old.ra_cuoi) and not (vals["vao_dau"] or vals["ra_cuoi"]):
            # ENTI suddenly reports no punch for a day that had one: keep ours, never erase attendance.
            stats["kept"] += 1
            return
        old_in, old_out = (old.vao_dau, old.ra_cuoi) if old else ("", "")
        if old:
            changed = not all(_same(old[name], value) for name, value in vals.items())
            write = {"raw_hash": digest}
            if changed:
                write.update(vals, raw_json=json.dumps(day_obj, ensure_ascii=False), received_at=now, changed_at=now)
            if old.employee_id.id != employee_id:
                write["employee_id"] = employee_id
            old.write(write)
            record = old
        else:
            record = EntiDay.create(dict(
                vals,
                source_id=self.id,
                key_nv=key_nv,
                work_date=work_date,
                employee_id=employee_id,
                raw_hash=digest,
                raw_json=json.dumps(day_obj, ensure_ascii=False),
                received_at=now,
                changed_at=now,
            ))
            stored[key_nv, work_date] = record
            changed = True

        if changed:
            stats["changed"] += 1
            for clock, moment, before in ((vals["vao_dau"], vals["check_in_dt"], old_in),
                                          (vals["ra_cuoi"], vals["check_out_dt"], old_out)):
                if clock and moment and clock != before:
                    lag = (now - moment).total_seconds()
                    if 0 <= lag <= LATENCY_HORIZON:
                        stats["latencies"].append(lag)
        if record._tp_project_to_canonical() if employee_id else record._tp_set_state("pending_map"):
            stats["applied"] += 1
            stats["dates"].add(work_date)

    # ------------------------------------------------------------------ outcome
    def _tp_enti_succeeded(self, stats, start_date, end_date, scope, origin, started, now):
        pace = self._tp_pace()
        duration = round(time.monotonic() - started, 2)
        moment = time.monotonic()
        pace["poll"] = moment
        pace["polls"] += 1
        pace["fails"] = 0
        if scope != "today":
            pace["window"] = moment
        changed = bool(stats["changed"] or stats["applied"] or stats["kept"])

        source_vals = {"last_success_at": now, "watermark": end_date.isoformat()}
        if self.state != "ready":
            source_vals["state"] = "ready"
        if self.last_error:
            source_vals["last_error"] = False
        if stats["applied"]:
            source_vals["latest_event_at"] = now
        internal(self).write(source_vals)

        latencies = stats["latencies"]
        heartbeat_due = pace["heartbeat"] is None or moment - pace["heartbeat"] >= HEARTBEAT_EVERY
        if origin == "manual" or changed or (scope == "window" and heartbeat_due):
            parts = [f"{stats['employees']} nhân viên ENTI ({stats['pages']} trang)",
                     f"{stats['changed']} ngày ENTI thay đổi",
                     f"{stats['applied']} ngày công cập nhật"]
            if stats["kept"]:
                parts.append(f"{stats['kept']} ngày ENTI trả trống nên giữ giờ cũ, cần kiểm tra trên ENTI")
            if latencies:
                parts.append(f"độ trễ giờ chấm → Odoo tối đa {max(latencies):.0f} giây (gồm máy → ENTI)")
            self.env["tp.hr.attendance.enti.sync.log"].sudo().create({
                "source_id": self.id,
                "start_date": start_date,
                "end_date": end_date,
                "synced_at": now,
                "duration_seconds": duration,
                "origin": origin,
                "scope": scope,
                "employee_count": stats["employees"],
                "mapped_count": stats["mapped"],
                "unmapped_count": stats["unmapped"],
                "days_received": stats["received"],
                "days_applied": stats["applied"],
                "changed_count": stats["changed"],
                "kept_count": stats["kept"],
                "polls": pace["polls"],
                "latency_max_seconds": max(latencies) if latencies else 0.0,
                "latency_median_seconds": statistics.median(latencies) if latencies else 0.0,
                "state": "success",
                "message": "Đồng bộ thành công: " + "; ".join(parts) + ".",
            })
            pace["heartbeat"] = moment
            pace["polls"] = 0

        if stats["applied"] or pace["healthy"] is False:
            self._tp_enti_notify(dates=stats["dates"], health="ok")
        pace["healthy"] = True
        return {
            "success": True,
            "employees": stats["employees"],
            "mapped": stats["mapped"],
            "unmapped": stats["unmapped"],
            "days_applied": stats["applied"],
            "changed": stats["changed"],
            "kept": stats["kept"],
            "duration": duration,
            "message": f"Đồng bộ ENTI thành công: {stats['employees']} nhân viên, {stats['applied']} ngày công cập nhật.",
        }

    def _tp_enti_failed(self, exc, start_date, end_date, scope, origin, started, now):
        pace = self._tp_pace()
        message = _error_text(exc)
        moment = time.monotonic()
        pace["poll"] = moment
        pace["fails"] += 1
        repeated = (self.last_error or "") == message[:240]
        log_due = pace["error_log"] is None or moment - pace["error_log"] >= ERROR_LOG_EVERY
        internal(self).write({"last_error_at": now, "last_error": message[:240]})
        if origin == "manual" or not repeated or log_due:
            self.env["tp.hr.attendance.enti.sync.log"].sudo().create({
                "source_id": self.id,
                "start_date": start_date,
                "end_date": end_date,
                "synced_at": now,
                "duration_seconds": round(moment - started, 2),
                "origin": origin,
                "scope": scope,
                "polls": pace["polls"],
                "state": "error",
                "message": message,
            })
            pace["error_log"] = moment
        _logger.warning("ENTI sync failed for source %s: %s", self.id, message)
        if pace["healthy"] is not False:
            self._tp_enti_notify(health="error")
        pace["healthy"] = False
        return {"success": False, "message": message, "duration": round(moment - started, 2)}

    def _tp_enti_notify(self, dates=(), health=None):
        """Wake the attendance screens of internal users. Payload has no personal data; screens re-read through
        their own access rules."""
        group = self.env.ref("base.group_user", raise_if_not_found=False)
        if not group:
            return
        changed = sorted({d.isoformat() for d in dates})
        payload = {
            "source_id": self.id,
            "at": fields.Datetime.now().isoformat(),
            # Up to 62 changed days; more than that (a long resync) is sent as "any day" so no screen misses it.
            "dates": changed if len(changed) <= 62 else [],
        }
        if health:
            payload["health"] = health
        try:
            self.env["bus.bus"].sudo()._sendone(group, BUS_TYPE, payload)
        except Exception as exc:  # noqa: BLE001 - a bus hiccup must not undo stored attendance
            _logger.warning("Could not broadcast attendance update: %s", exc)
