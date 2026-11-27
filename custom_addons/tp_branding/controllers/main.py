# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""BRAND-WHITELABEL-002 (CHG-20261117-002): TANPHAT ONE URLs on native controllers.

Every override is cooperative (``super()``) so the merged controller keeps the
behaviour of web, auth_signup, auth_totp(_mail), portal, mail and bus.

* GET/HEAD on a legacy path (``/odoo...``, ``/web``, ``/web/login...``) answers
  a temporary 302 to the branded path. Query string is kept raw and the
  browser keeps the ``#fragment`` because Location carries none.
* POST/RPC/upload/logout/assets are never redirected: the native endpoints
  keep answering on their native URL and CSRF stays enforced by the router.
* Location headers emitted by the native code are rebranded only when they are
  local relative URLs (see :mod:`..brand_urls`).
"""

from urllib.parse import quote

from odoo import http
from odoo.http import request
from odoo.tools.urls import urljoin

from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.auth_totp.controllers.home import Home as TotpHome
from odoo.addons.http_routing.controllers.main import SessionWebsite
from odoo.addons.portal.controllers.web import Home as PortalHome
from odoo.addons.tp_branding.brand_urls import (
    APP_PATH,
    BRAND_NAME,
    LEGACY_APP_PATH,
    LOGIN_PATH,
    RESET_PATH,
    SIGNUP_PATH,
    TOTP_PATH,
    brand_path,
    brand_url,
    is_app_path,
    is_local_url,
    native_url,
    url_path,
)
from odoo.addons.web.controllers.utils import is_user_internal
from odoo.addons.web.controllers.webmanifest import WebManifest

BRAND_NAVY = '#061b40'
BRAND_ICON_PATH = 'tp_branding/static/img/icon-192.png'
BRAND_OG_IMAGE = '/tp_web_home/static/img/brand/tp_logo_full.png'

# Characters kept literally when re-quoting a decoded request path.
_PATH_SAFE = "/:@!$&'()*+,;=-._~"

_SW_SHARE_TARGET_NATIVE = 'Response.redirect("/odoo?share_target=trigger")'
_SW_SHARE_TARGET_BRANDED = 'Response.redirect("/app?share_target=trigger")'


def tp_legacy_redirect():
    """302 GET/HEAD requests on a legacy path to the TANPHAT ONE path."""
    httprequest = request.httprequest
    if httprequest.method not in ('GET', 'HEAD'):
        return None
    path = httprequest.path
    target = brand_path(path)
    if target == path:
        return None
    location = quote(target, safe=_PATH_SAFE)
    query_string = httprequest.query_string
    if query_string:
        location += '?' + query_string.decode('utf-8', 'replace')
    return request.redirect(location, code=302, local=True)


def tp_brand_location(response):
    """Rebrand the Location header of a native local redirect, in place."""
    status = getattr(response, 'status_code', None)
    if status and 300 <= status < 400:
        location = response.headers.get('Location')
        branded = brand_url(location)
        if branded != location:
            response.headers['Location'] = branded
    return response


class BrandHome(AuthSignupHome, TotpHome, PortalHome):

    # ------------------------------------------------------------------
    # Entry point and webclient
    # ------------------------------------------------------------------
    @http.route()
    def index(self, *args, **kw):
        uid = request.session.uid
        if uid and not is_user_internal(uid):
            # Portal user: native portal behaviour (/my).
            return super().index(*args, **kw)
        target = APP_PATH if uid else LOGIN_PATH
        return request.redirect_query(target, query=request.params)

    @http.route([
        '/web', '/odoo', '/odoo/<path:subpath>', '/scoped_app/<path:subpath>',
        APP_PATH, APP_PATH + '/<path:subpath>',
    ])
    def web_client(self, s_action=None, **kw):
        legacy = tp_legacy_redirect()
        if legacy:
            return legacy
        return tp_brand_location(super().web_client(s_action=s_action, **kw))

    # ------------------------------------------------------------------
    # Authentication pages
    # ------------------------------------------------------------------
    def _login_redirect(self, uid, redirect=None):
        if not redirect and uid and is_user_internal(uid):
            return '/app/trang-chu'
        return brand_url(super()._login_redirect(uid, redirect=redirect))

    @http.route(['/web/login', LOGIN_PATH])
    def web_login(self, redirect=None, **kw):
        legacy = tp_legacy_redirect()
        if legacy:
            return legacy
        # Native Open Graph logic only recognises /odoo deep links.
        native_redirect = redirect
        if is_local_url(redirect) and is_app_path(url_path(redirect)):
            native_redirect = native_url(redirect)
        response = super().web_login(redirect=native_redirect, **kw)
        qcontext = getattr(response, 'qcontext', None)
        if getattr(response, 'template', None) and isinstance(qcontext, dict):
            self._tp_brand_login_qcontext(qcontext, native_redirect)
        return tp_brand_location(response)

    def _tp_brand_login_qcontext(self, qcontext, native_redirect):
        if isinstance(qcontext.get('redirect'), str):
            qcontext['redirect'] = brand_url(qcontext['redirect'])
        if not qcontext.get('disable_opengraph'):
            return
        url_root = request.httprequest.url_root
        try:
            qcontext['og_url'] = urljoin(url_root, brand_url(native_redirect))
        except ValueError:
            qcontext['og_url'] = request.httprequest.url
        if qcontext.get('og_title') in (None, '', 'Odoo'):
            qcontext['og_title'] = BRAND_NAME
        qcontext['og_image_url'] = urljoin(url_root, BRAND_OG_IMAGE)

    @http.route(['/web/login/totp', TOTP_PATH])
    def web_totp(self, redirect=None, **kwargs):
        legacy = tp_legacy_redirect()
        if legacy:
            return legacy
        return tp_brand_location(super().web_totp(redirect=redirect, **kwargs))

    @http.route(['/web/signup', SIGNUP_PATH])
    def web_auth_signup(self, *args, **kw):
        legacy = tp_legacy_redirect()
        if legacy:
            return legacy
        return tp_brand_location(super().web_auth_signup(*args, **kw))

    @http.route(['/web/reset_password', RESET_PATH])
    def web_auth_reset_password(self, *args, **kw):
        legacy = tp_legacy_redirect()
        if legacy:
            return legacy
        return tp_brand_location(super().web_auth_reset_password(*args, **kw))


class BrandSession(SessionWebsite):

    @http.route()
    def logout(self, redirect=LEGACY_APP_PATH):
        target = brand_url(redirect or LEGACY_APP_PATH)
        if target in (APP_PATH, APP_PATH + '/'):
            # The webclient would only bounce an anonymous visitor to login.
            target = LOGIN_PATH
        return super().logout(redirect=target)


class BrandWebManifest(WebManifest):

    def _get_webmanifest(self):
        manifest = super()._get_webmanifest()
        app_name = request.env['ir.config_parameter'].sudo().get_str('web.web_app_name')
        name = app_name if app_name and app_name != 'Odoo' else BRAND_NAME
        manifest.update({
            # Keep the identity of PWAs installed while start_url was /odoo.
            'id': LEGACY_APP_PATH,
            'name': name,
            'short_name': name,
            'scope': APP_PATH,
            'start_url': APP_PATH,
            'background_color': BRAND_NAVY,
            'theme_color': BRAND_NAVY,
            'icons': [{
                'src': f'/tp_branding/static/img/icon-{size}.png',
                'sizes': f'{size}x{size}',
                'type': 'image/png',
                'purpose': 'any',
            } for size in (192, 512)],
        })
        for shortcut in manifest.get('shortcuts') or []:
            shortcut['url'] = brand_url(shortcut.get('url'))
        share_target = manifest.get('share_target')
        if share_target:
            share_target['action'] = brand_url(share_target.get('action'))
        return manifest

    @http.route()
    def service_worker(self):
        response = super().service_worker()
        # The worker is registered on /app; legacy /odoo registrations are
        # cleaned by the webclient patch, so allow both scopes.
        response.headers['Service-Worker-Allowed'] = '/'
        return response

    def _get_service_worker_content(self):
        body = super()._get_service_worker_content()
        # Share target lands on the branded app instead of a /odoo -> /app hop.
        return body.replace(_SW_SHARE_TARGET_NATIVE, _SW_SHARE_TARGET_BRANDED, 1)

    def _icon_path(self):
        return BRAND_ICON_PATH
