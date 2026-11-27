"""HTTP API client for ENTI attendance service (ENTI-LIVE-001).

Communicates directly with https://enti.vn endpoints observed in live production.
Handles authentication, session cookies, app selection, token auto-refresh,
pagination, and safe error handling without leaking credentials.
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests

_logger = logging.getLogger(__name__)

ENTI_BASE_URL = "https://enti.vn"
DEFAULT_TIMEOUT = 30
MAX_PAGES = 50
DEFAULT_COMPANY_KEYWORD = "Tấn Phát"
RETRY_STATUS = (429, 500, 502, 503, 504)
DEFAULT_MAX_IMAGE_BYTES = 5 * 1024 * 1024
IMAGE_FIELD_CANDIDATES = (
    "anh",
    "avatar",
    "avatarUrl",
    "image",
    "imageUrl",
    "photo",
    "photoUrl",
    "hinhAnh",
)


def extract_employee_image_field(record):
    """Return ``(field_name, raw_value)`` from an ENTI employee dict.

    Real ENTI payloads use ``anh`` (observed on ``/api/nhan-vien/get-info`` and ``/api/nhan-vien/search``).
    Also checks documented alias candidates when ``anh`` is absent.
    """
    if not isinstance(record, dict):
        return "", ""
    first_present = ""
    for key in IMAGE_FIELD_CANDIDATES:
        if key in record:
            if not first_present:
                first_present = key
            val = record.get(key)
            if isinstance(val, str) and val.strip():
                return key, val.strip()
    return first_present, ""


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
                msg = "Phiên làm việc ENTI đã hết hạn hoặc thông tin đăng nhập không đúng."
                raise EntiAuthError(msg, status_code=401)

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
                msg = "Máy chủ ENTI không trả về dữ liệu định dạng JSON hợp lệ."
                raise EntiError(msg) from exc

            return data

        msg = "Đã hết số lần thử kết nối lại tới máy chủ ENTI."
        raise EntiError(msg)

    def login(self, phone, password):
        """Authenticate with phone and password. Returns dict with token info."""
        if not phone or not password:
            msg = "Thiếu số điện thoại hoặc mật khẩu đăng nhập ENTI."
            raise EntiAuthError(msg)

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
            except (EntiError, requests.RequestException, ValueError) as exc:
                _logger.info("ENTI refresh token endpoint failed: %s; falling back to re-login", exc)

        if self._phone and self._password:
            try:
                self.login(self._phone, self._password)
                if self.selected_app_key:
                    self.select_app(self.selected_app_key)
                return True
            except (EntiError, requests.RequestException, ValueError) as exc:
                _logger.error("ENTI re-login fallback failed: %s", exc)
                return False

        return False

    def _ensure_authenticated(self):
        if not self.is_token_valid():
            if not self._renew_token():
                msg = "Chưa có phiên đăng nhập ENTI hợp lệ hoặc phiên đã hết hạn."
                raise EntiAuthError(msg)

    def get_me(self):
        """Fetch logged-in user profile."""
        return self._request("GET", "/__enti/api/v1/me")

    def get_apps(self):
        """Fetch list of companies/applications available for this user."""
        res = self._request("GET", "/__enti/api/v1/apps/my")
        return res.get("data") or []

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
            msg = "Thiếu khóa ứng dụng (app_key) để chọn công ty trên ENTI."
            raise EntiError(msg)

        payload = {"app_key": app_key}
        res = self._request("POST", "/__enti/api/v1/session/select-app", json_data=payload)
        self.selected_app_key = app_key

        # Execute supplementary context endpoints observed during browser probe
        try:
            self._request("POST", "/api/apps/available", json_data={}, retry_count=0)
        except (EntiError, requests.RequestException, ValueError) as exc:
            _logger.debug("ENTI apps/available context call: %s", exc)

        try:
            self._request("POST", "/api/auth/get-acount-info", json_data={}, retry_count=0)
        except (EntiError, requests.RequestException, ValueError) as exc:
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

    def _paginate_post(self, path, max_results_per_page=100):
        """Fetch all pages of a POST list endpoint (``/api/nhan-vien/get-info`` or ``/api/nhan-vien/search``)."""
        rows = []
        seen_keys = set()
        search_pos = 0
        total_data = None
        for _page in range(MAX_PAGES):
            payload = {
                "data": [],
                "searchResultPosition": search_pos,
                "maxTotalResult": max_results_per_page,
            }
            res = self._request("POST", path, json_data=payload)
            if not isinstance(res, dict):
                break
            page_data = res.get("data") or []
            if res.get("totalData") is not None:
                total_data = int(res.get("totalData") or 0)
            num_of_data = int(res.get("numOfData") or len(page_data))
            more_data = bool(res.get("moreData"))
            for item in page_data:
                if not isinstance(item, dict):
                    continue
                key = (item.get("keyNV") or "").strip()
                if key:
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                rows.append(item)
            if not page_data or num_of_data <= 0:
                break
            search_pos += num_of_data
            if total_data is not None:
                if search_pos >= total_data:
                    break
            elif not more_data:
                break
        return rows

    def get_employees(self, max_results=300):
        """Fetch employees info list from ENTI."""
        payload = {
            "data": [],
            "searchResultPosition": 0,
            "maxTotalResult": max_results,
        }
        res = self._request("POST", "/api/nhan-vien/get-info", json_data=payload)
        return res.get("data") or []

    def get_employee_profiles(self, max_results_per_page=100):
        """Fetch employee directory with image field ``anh`` populated.

        Calls ``POST /api/nhan-vien/get-info`` first; if ``get-info`` returns empty ``anh`` values (as observed on
        live ENTI where ``get-info`` sets ``anh=''`` while ``POST /api/nhan-vien/search`` returns the actual
        ``data:image/jpeg;base64,...`` in ``anh``), queries ``POST /api/nhan-vien/search`` and merges by ``keyNV``.
        """
        info_rows = self._paginate_post("/api/nhan-vien/get-info", max_results_per_page=max_results_per_page)
        by_key = {}
        has_any_image = False
        for item in info_rows:
            key = (item.get("keyNV") or "").strip()
            if not key:
                continue
            by_key[key] = dict(item)
            if extract_employee_image_field(item)[1]:
                has_any_image = True

        if not has_any_image:
            try:
                search_rows = self._paginate_post("/api/nhan-vien/search", max_results_per_page=max_results_per_page)
            except EntiError as exc:
                if by_key:
                    _logger.info("ENTI /api/nhan-vien/search fallback unavailable (%s); using get-info only", exc)
                    search_rows = []
                else:
                    raise
            for item in search_rows:
                key = (item.get("keyNV") or "").strip()
                if not key:
                    continue
                target = by_key.setdefault(key, {})
                for field_key, value in item.items():
                    if value not in (None, "") or field_key not in target:
                        target[field_key] = value
        return list(by_key.values())

    def _allowed_image_hosts(self, extra_hosts=None):
        hosts = {"enti.vn"}
        base_host = (urlparse(self.base_url).hostname or "").lower()
        if base_host:
            hosts.add(base_host)
        for host in extra_hosts or ():
            cleaned = str(host or "").strip().lower()
            if cleaned:
                hosts.add(cleaned)
        return hosts

    def validate_image_url(self, image_url, allowed_hosts=None):
        """Validate and normalize an ENTI image URL (HTTP/HTTPS only, host inside configured ENTI hosts)."""
        raw = str(image_url or "").strip()
        if not raw:
            msg = "URL ảnh trống."
            raise EntiError(msg)
        if raw.startswith("/"):
            raw = urljoin(f"{self.base_url}/", raw.lstrip("/"))
        parsed = urlparse(raw)
        if parsed.scheme not in ("http", "https"):
            raise EntiError(f"Giao thức URL ảnh không hợp lệ ({parsed.scheme or 'trống'}); chỉ chấp nhận HTTP/HTTPS.")
        host = (parsed.hostname or "").lower()
        if not host:
            msg = "URL ảnh thiếu tên miền (host)."
            raise EntiError(msg)
        allowed = self._allowed_image_hosts(allowed_hosts)
        host_ok = any(host == candidate or host.endswith(f".{candidate}") for candidate in allowed)
        if not host_ok:
            raise EntiError(f"Tên miền ảnh '{host}' không nằm trong danh sách máy chủ ENTI được phép.")
        return raw

    def download_image(self, image_url, max_bytes=DEFAULT_MAX_IMAGE_BYTES, allowed_hosts=None, retry_count=2):
        """Download binary image from an allowed ENTI URL with bounded retry, safe redirect hops, and size checks."""
        url = self.validate_image_url(image_url, allowed_hosts=allowed_hosts)
        max_bytes = max(1024, int(max_bytes or DEFAULT_MAX_IMAGE_BYTES))
        base_host = (urlparse(self.base_url).hostname or "").lower()

        def _headers_for(target_url):
            req_headers = {"Accept": "image/*,*/*;q=0.8"}
            target_host = (urlparse(target_url).hostname or "").lower()
            if self.access_token and base_host and target_host == base_host:
                req_headers["Authorization"] = f"Bearer {self.access_token}"
            return req_headers

        renewed_once = False
        for attempt in range(retry_count + 1):
            current_url = url
            redirects = 0
            while True:
                try:
                    resp = self.session.request(
                        method="GET",
                        url=current_url,
                        headers=_headers_for(current_url),
                        timeout=self.timeout,
                        stream=True,
                        allow_redirects=False,
                    )
                except requests.RequestException as exc:
                    if attempt < retry_count:
                        time.sleep(1 * (attempt + 1))
                        break
                    raise EntiError(f"Lỗi mạng hoặc hết thời gian chờ khi tải ảnh ENTI: {exc}") from exc

                try:
                    if resp.status_code in (301, 302, 303, 307, 308):
                        location = (resp.headers.get("Location") or "").strip()
                        if not location:
                            msg = "Máy chủ ENTI trả mã chuyển hướng nhưng thiếu đích Location."
                            raise EntiError(msg)
                        redirects += 1
                        if redirects > 3:
                            msg = "Quá số bước chuyển hướng tối đa (3) khi tải ảnh ENTI."
                            raise EntiError(msg)
                        current_url = self.validate_image_url(
                            urljoin(current_url, location),
                            allowed_hosts=allowed_hosts,
                        )
                        continue

                    if resp.status_code == 401 and not renewed_once and (self._phone or self.refresh_token):
                        renewed_once = True
                        if self._renew_token():
                            continue
                        msg = "Phiên ENTI hết hạn khi tải ảnh."
                        raise EntiAuthError(msg, status_code=401)

                    if resp.status_code in RETRY_STATUS and attempt < retry_count:
                        retry_after = resp.headers.get("Retry-After")
                        sleep_sec = int(retry_after) if retry_after and retry_after.isdigit() else (2 * (attempt + 1))
                        time.sleep(min(sleep_sec, 10))
                        break

                    if resp.status_code >= 400:
                        raise EntiError(
                            f"Máy chủ ENTI trả lỗi HTTP {resp.status_code} khi tải ảnh.",
                            status_code=resp.status_code,
                        )

                    content_type = (resp.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
                    if not content_type.startswith("image/"):
                        raise EntiError(
                            f"Content-Type phản hồi không hợp lệ ({content_type or 'trống'}); yêu cầu image/*.",
                        )

                    content_len = resp.headers.get("Content-Length")
                    if content_len and content_len.strip().isdigit() and int(content_len.strip()) > max_bytes:
                        raise EntiError(
                            f"Dung lượng ảnh ({content_len.strip()} bytes) vượt quá giới hạn tối đa ({max_bytes} bytes).",
                        )

                    chunks = []
                    total = 0
                    for chunk in resp.iter_content(chunk_size=65536):
                        if not chunk:
                            continue
                        total += len(chunk)
                        if total > max_bytes:
                            raise EntiError(
                                f"Dung lượng ảnh vượt quá giới hạn tối đa ({max_bytes} bytes).",
                            )
                        chunks.append(chunk)
                    return b"".join(chunks), content_type
                finally:
                    resp.close()

        msg = "Đã hết số lần thử tải ảnh từ máy chủ ENTI."
        raise EntiError(msg)

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
