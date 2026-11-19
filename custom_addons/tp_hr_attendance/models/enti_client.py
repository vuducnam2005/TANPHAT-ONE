"""HTTP API client for ENTI attendance service (ENTI-LIVE-001).

Communicates directly with https://enti.vn endpoints observed in live production.
Handles authentication, session cookies, app selection, token auto-refresh,
pagination, and safe error handling without leaking credentials.
"""
import logging
import threading
import time
from datetime import datetime, timedelta

import requests

_logger = logging.getLogger(__name__)

ENTI_BASE_URL = "https://enti.vn"
DEFAULT_TIMEOUT = 30
MAX_PAGES = 50
DEFAULT_COMPANY_KEYWORD = "Tấn Phát"
RETRY_STATUS = (429, 500, 502, 503, 504)
# One authenticated client per (database, source, account): the cron and the "sync now" button reuse the
# token and session cookies instead of logging in every minute (ENTI-ATTENDANCE-002). Process memory only:
# tokens never reach the database, logs or the browser.
_CLIENT_CACHE = {}
_CLIENT_CACHE_LOCK = threading.Lock()


class EntiError(Exception):
    """Base exception for ENTI API communication errors."""

    def __init__(self, message, status_code=None, error_code=None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class EntiAuthError(EntiError):
    """Authentication or authorization failure on ENTI."""


class EntiClient:
    """Session-based HTTP client for the ENTI attendance API."""

    def __init__(self, base_url=ENTI_BASE_URL, timeout=DEFAULT_TIMEOUT):
        self.base_url = (base_url or ENTI_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.selected_app_key = None
        self.selected_app_name = None
        self._phone = None
        self._password = None

    def _safe_url(self, path):
        path = path.lstrip("/")
        return f"{self.base_url}/{path}"

    def _auth_headers(self):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def is_token_valid(self):
        if not self.access_token or not self.token_expires_at:
            return False
        # Token valid if at least 60s remain before expiration
        return datetime.now() < (self.token_expires_at - timedelta(seconds=60))

    def _request(self, method, path, json_data=None, params=None, need_auth=True, retry_count=2):
        """Execute an HTTP request with retry, backoff, and auth renewal."""
        if need_auth and not self.is_token_valid():
            self._ensure_authenticated()

        url = self._safe_url(path)
        headers = self._auth_headers() if need_auth else {"Content-Type": "application/json"}

        for attempt in range(retry_count + 1):
            try:
                resp = self.session.request(
                    method=method,
                    url=url,
                    json=json_data,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                if attempt < retry_count:
                    time.sleep(1 * (attempt + 1))
                    continue
                _logger.error("ENTI request network failure: %s %s", method, path)
                raise EntiError(f"Không thể kết nối tới máy chủ ENTI: {exc}") from exc

            # If 401 Unauthorized, try refresh or re-login once
            if resp.status_code == 401 and need_auth and attempt == 0:
                _logger.info("ENTI returned 401, renewing token...")
                renewed = self._renew_token()
                if renewed:
                    headers = self._auth_headers()
                    continue
                raise EntiAuthError("Phiên làm việc ENTI đã hết hạn hoặc thông tin đăng nhập không đúng.", status_code=401)

            # Handle 429 Too Many Requests or 5xx server errors with bounded backoff
            if resp.status_code in RETRY_STATUS and attempt < retry_count:
                retry_after = resp.headers.get("Retry-After")
                sleep_sec = int(retry_after) if retry_after and retry_after.isdigit() else (2 * (attempt + 1))
                time.sleep(min(sleep_sec, 10))
                continue

            if resp.status_code >= 400:
                _logger.warning("ENTI HTTP error: %s %s -> %s", method, path, resp.status_code)
                raise EntiError(
                    f"Máy chủ ENTI phản hồi lỗi HTTP {resp.status_code}.",
                    status_code=resp.status_code,
                )

            try:
                data = resp.json()
            except ValueError as exc:
                raise EntiError("Máy chủ ENTI không trả về dữ liệu định dạng JSON hợp lệ.") from exc

            return data

        raise EntiError("Đã hết số lần thử kết nối lại tới máy chủ ENTI.")

    def login(self, phone, password):
        """Authenticate with phone and password. Returns dict with token info."""
        if not phone or not password:
            raise EntiAuthError("Thiếu số điện thoại hoặc mật khẩu đăng nhập ENTI.")

        self._phone = phone
        self._password = password
        payload = {"phone": phone, "password": password}

        data = self._request(
            method="POST",
            path="/__enti/api/v1/auth/login",
            json_data=payload,
            need_auth=False,
        )

        login_data = data.get("data") or {}
        access_token = login_data.get("access_token")
        refresh_token = login_data.get("refresh_token")
        expires_in = login_data.get("expires_in") or 900

        if not access_token:
            msg = data.get("message") or "Đăng nhập ENTI không thành công: thiếu access_token."
            raise EntiAuthError(msg, status_code=data.get("statusCode"))

        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
        _logger.info("ENTI login successful, token expires in %s seconds", expires_in)

        return login_data

    def _renew_token(self):
        """Attempt to refresh token, fallback to re-login."""
        if self.refresh_token:
            try:
                data = self._request(
                    method="POST",
                    path="/__enti/api/v1/auth/refresh",
                    json_data={"refresh_token": self.refresh_token},
                    need_auth=False,
                    retry_count=0,
                )
                refresh_data = data.get("data") or {}
                new_token = refresh_data.get("access_token")
                if new_token:
                    self.access_token = new_token
                    expires_in = refresh_data.get("expires_in") or 900
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    if refresh_data.get("refresh_token"):
                        self.refresh_token = refresh_data.get("refresh_token")
                    _logger.info("ENTI token refreshed successfully")
                    return True
            except Exception as exc:
                _logger.info("ENTI refresh token endpoint failed: %s; falling back to re-login", exc)

        if self._phone and self._password:
            try:
                self.login(self._phone, self._password)
                if self.selected_app_key:
                    self.select_app(self.selected_app_key)
                return True
            except Exception as exc:
                _logger.error("ENTI re-login fallback failed: %s", exc)
                return False

        return False

    def _ensure_authenticated(self):
        if not self.is_token_valid():
            if not self._renew_token():
                raise EntiAuthError("Chưa có phiên đăng nhập ENTI hợp lệ hoặc phiên đã hết hạn.")

    def get_me(self):
        """Fetch logged-in user profile."""
        return self._request("GET", "/__enti/api/v1/me")

    def get_apps(self):
        """Fetch list of companies/applications available for this user."""
        res = self._request("GET", "/__enti/api/v1/apps/my")
        apps = res.get("data") or []
        return apps

    def find_app_for_company(self, target_name=DEFAULT_COMPANY_KEYWORD):
        """Find the ENTI application of the company; never guess between several applications."""
        apps = self.get_apps()
        if not apps:
            return None
        targets = [name.lower() for name in {target_name or "", DEFAULT_COMPANY_KEYWORD} if name]
        for app in apps:
            name = (app.get("name") or app.get("app_name") or app.get("ten") or "").lower()
            if any(target in name for target in targets):
                return app
        # A single application on the account is unambiguous; several without a name match are not.
        return apps[0] if len(apps) == 1 else None

    def select_app(self, app_key):
        """Select active company context and establish session cookies."""
        if not app_key:
            raise EntiError("Thiếu khóa ứng dụng (app_key) để chọn công ty trên ENTI.")

        payload = {"app_key": app_key}
        res = self._request("POST", "/__enti/api/v1/session/select-app", json_data=payload)
        self.selected_app_key = app_key

        # Execute supplementary context endpoints observed during browser probe
        try:
            self._request("POST", "/api/apps/available", json_data={}, retry_count=0)
        except Exception as exc:
            _logger.debug("ENTI apps/available context call: %s", exc)

        try:
            self._request("POST", "/api/auth/get-acount-info", json_data={}, retry_count=0)
        except Exception as exc:
            _logger.debug("ENTI get-acount-info context call: %s", exc)

        _logger.info("ENTI application selected: app_key=%s", app_key)
        return res

    def get_departments(self, max_results=300):
        """Fetch departments list from ENTI."""
        payload = {
            "data": [],
            "searchResultPosition": 0,
            "maxTotalResult": max_results,
        }
        res = self._request("POST", "/api/bo-phan/search", json_data=payload)
        return res.get("data") or []

    def get_employees(self, max_results=300):
        """Fetch employees info list from ENTI."""
        payload = {
            "data": [],
            "searchResultPosition": 0,
            "maxTotalResult": max_results,
        }
        res = self._request("POST", "/api/nhan-vien/get-info", json_data=payload)
        return res.get("data") or []

    def get_attendance(self, start_date, end_date, max_results_per_page=50):
        """Fetch attendance report for the date range with full pagination handling.

        Keeps exact endpoint spelling: /api/attendace/bang-cong. Pages follow ``moreData`` and
        ``totalData``; a repeated employee key is kept once. When ENTI announces more employees than it
        returns, the call fails instead of handing a partial board to the sync (old data stays).
        """
        rows = {}
        search_pos = 0
        total_data = None
        pages = 0

        start_str = start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else str(start_date)[:10]
        end_str = end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else str(end_date)[:10]

        for page in range(MAX_PAGES):
            payload = {
                "typeData": "deptkey",
                "data": [],
                "startDate": start_str,
                "endDate": end_str,
                "searchResultPosition": search_pos,
                "maxTotalResult": max_results_per_page,
            }

            res = self._request("POST", "/api/attendace/bang-cong", json_data=payload)
            pages = page + 1
            page_data = res.get("data") or []
            if res.get("totalData") is not None:
                total_data = int(res.get("totalData") or 0)
            num_of_data = int(res.get("numOfData") or len(page_data))
            more_data = bool(res.get("moreData"))

            for item in page_data:
                key = (item or {}).get("keyNV")
                if key and key not in rows:
                    rows[key] = item

            if not page_data or num_of_data <= 0:
                break
            search_pos += num_of_data
            if total_data is not None:
                if search_pos >= total_data:
                    break
            elif not more_data:
                break

        if total_data is not None and len(rows) < total_data:
            raise EntiError(
                f"ENTI chỉ trả {len(rows)}/{total_data} nhân viên cho {start_str}–{end_str}; giữ nguyên dữ liệu cũ, thử lại lượt sau.",
            )
        _logger.info("ENTI attendance %s..%s: %s employees in %s page(s)", start_str, end_str, len(rows), pages)
        return {
            "data": list(rows.values()),
            "total": len(rows),
            "pages": pages,
            "startDate": start_str,
            "endDate": end_str,
        }


def cached_client(cache_key):
    """Return the shared client for ``cache_key`` (created on first use) and its lock."""
    with _CLIENT_CACHE_LOCK:
        entry = _CLIENT_CACHE.get(cache_key)
        if entry is None:
            entry = _CLIENT_CACHE[cache_key] = {"client": EntiClient(), "lock": threading.Lock(), "app_key": None}
        return entry


def drop_cached_client(cache_key):
    """Forget a client (credentials changed or the session is unusable); the next run logs in again."""
    with _CLIENT_CACHE_LOCK:
        _CLIENT_CACHE.pop(cache_key, None)
