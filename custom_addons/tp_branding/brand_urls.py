# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""TANPHAT ONE public URL vocabulary (BRAND-WHITELABEL-002, SYSTEM-URL-001).

Pure helpers, no ORM access. They only ever rewrite the *path prefix* of a
local relative URL (``/...`` but not ``//...``); query string and fragment are
kept byte-for-byte. Absolute, protocol-relative, schemeful or empty values are
returned unchanged so nothing here can turn into an open redirect.
"""

from odoo.addons.tp_branding.brand_routes import (
    get_route_by_native_slug,
    get_route_by_url,
)

BRAND_NAME = 'TANPHAT ONE'
BRAND_CREDIT = 'Phát triển bởi TADIC'

APP_PATH = '/app'
LEGACY_APP_PATH = '/odoo'

LOGIN_PATH = '/dang-nhap'
TOTP_PATH = '/dang-nhap/xac-thuc'
SIGNUP_PATH = '/tao-tai-khoan'
RESET_PATH = '/quen-mat-khau'

# Native auth path -> branded path (exact match only).
AUTH_PATHS = {
    '/web/login': LOGIN_PATH,
    '/web/login/totp': TOTP_PATH,
    '/web/signup': SIGNUP_PATH,
    '/web/reset_password': RESET_PATH,
}
NATIVE_AUTH_PATHS = {branded: native for native, branded in AUTH_PATHS.items()}

# Native paths under /odoo that are real static routes, not webclient paths.
# They stay native: the service worker caches `/odoo/offline` by that key.
UNBRANDED_PATHS = frozenset({'/odoo/offline'})

AUTH_PAGE_PATHS = tuple(AUTH_PATHS) + tuple(NATIVE_AUTH_PATHS)


def _split(url):
    """Split ``url`` into (path, rest) where rest starts at ``?`` or ``#``."""
    cut = len(url)
    for sep in ('?', '#'):
        idx = url.find(sep)
        if idx != -1 and idx < cut:
            cut = idx
    return url[:cut], url[cut:]


def url_path(url):
    """Path part of a local URL (before ``?`` / ``#``), undecoded."""
    return _split(url)[0]


def _exact_key(path):
    # The Odoo router is built with strict_slashes=False: `/web/login/` is
    # served by the `/web/login` endpoint, so map it the same way.
    if len(path) > 1 and path.endswith('/'):
        return path.rstrip('/') or '/'
    return path


def is_local_url(url):
    return (
        isinstance(url, str)
        and url.startswith('/')
        and not url.startswith('//')
        and not url.startswith('/\\')
    )


def is_legacy_app_path(path):
    """True for ``/odoo`` and ``/odoo/...`` webclient paths (not ``/odoox``)."""
    if path in UNBRANDED_PATHS:
        return False
    return path == LEGACY_APP_PATH or path.startswith(LEGACY_APP_PATH + '/')


def is_app_path(path):
    """True for ``/app`` and ``/app/...`` (not ``/appx``)."""
    return path == APP_PATH or path.startswith(APP_PATH + '/')


LEGACY_ATTENDANCE_PREFIX = '/app/nhan-su/cham-cong'


def canonical_app_path(path):
    """Canonicalize a branded path or legacy alias to its business route URL."""
    clean = (path or '').rstrip('/') or '/'
    # Exact match on registered routes or their aliases
    route = get_route_by_url(clean)
    if route:
        return route['url']

    # Subpath check: /app/<slug>[/<id>] or <alias>[/<id>] -> canonical
    if clean.startswith(APP_PATH + '/'):
        sub = clean[len(APP_PATH) + 1:]
        parts = sub.split('/')
        if len(parts) >= 2 and (parts[-1].isdigit() or parts[-1] in ('new', 'tao-moi')):
            base_path = APP_PATH + '/' + '/'.join(parts[:-1])
            base_route = get_route_by_url(base_path)
            if base_route and base_route.get('has_detail'):
                suffix = '/tao-moi' if parts[-1] in ('new', 'tao-moi') else '/' + parts[-1]
                return base_route['url'] + suffix
        first_slug = parts[0]
        route = get_route_by_native_slug(first_slug)
        if route:
            suffix = '/' + '/'.join(parts[1:]) if len(parts) > 1 else ''
            # Normalize /new to /tao-moi
            if suffix == '/new':
                suffix = '/tao-moi'
            return route['url'] + suffix

    return path


def _canonical_legacy_attendance(key):
    canonical = canonical_app_path(key)
    if canonical != key:
        return canonical
    suffix = key[len(LEGACY_ATTENDANCE_PREFIX):]
    return '/app/cham-cong' + (suffix or '/tong-quan')


def brand_path(path):
    """Map one native or legacy attendance path to its TANPHAT ONE path, or return it unchanged."""
    key = _exact_key(path)
    if key == '/web':
        return APP_PATH
    if key in AUTH_PATHS:
        return AUTH_PATHS[key]
    if is_legacy_app_path(path):
        mapped = APP_PATH + path[len(LEGACY_APP_PATH):]
        mapped_key = _exact_key(mapped)
        if mapped_key == LEGACY_ATTENDANCE_PREFIX or mapped_key.startswith(LEGACY_ATTENDANCE_PREFIX + '/'):
            return _canonical_legacy_attendance(mapped_key)
        return mapped
    if key == LEGACY_ATTENDANCE_PREFIX or key.startswith(LEGACY_ATTENDANCE_PREFIX + '/'):
        return _canonical_legacy_attendance(key)
    return path


def native_path(path):
    """Inverse of :func:`brand_path` for the paths Odoo core must still see."""
    if path in NATIVE_AUTH_PATHS:
        return NATIVE_AUTH_PATHS[path]
    if is_app_path(path):
        return LEGACY_APP_PATH + path[len(APP_PATH):]
    return path


def brand_url(url):
    """Rewrite the path prefix of a local URL to the branded vocabulary."""
    if not is_local_url(url):
        return url
    path, rest = _split(url)
    return brand_path(path) + rest


def native_url(url):
    """Rewrite a branded local URL back to the native Odoo vocabulary."""
    if not is_local_url(url):
        return url
    path, rest = _split(url)
    return native_path(path) + rest


def brand_title(title):
    """Return ``"<page> | TANPHAT ONE"`` without doubling the suffix."""
    title = (title or '').strip()
    if not title or title in ('Odoo', BRAND_NAME):
        return BRAND_NAME
    if title.endswith('| ' + BRAND_NAME):
        return title
    return f'{title} | {BRAND_NAME}'
