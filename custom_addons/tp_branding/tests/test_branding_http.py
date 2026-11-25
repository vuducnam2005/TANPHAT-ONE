# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
import re
import secrets
from urllib.parse import parse_qs, urlsplit

from lxml import html

from odoo.tests import HttpCase, new_test_user, tagged


def _location(response):
    """Path + query of a redirect, whatever the host form of Location."""
    parts = urlsplit(response.headers.get('Location', ''))
    return parts.path + (f'?{parts.query}' if parts.query else '')


@tagged('post_install', '-at_install')
class TestBrandingHttp(HttpCase):
    """BRAND-WHITELABEL-002 over real HTTP: branded URLs, legacy redirects,
    untouched POST/CSRF and server-rendered identity. Synthetic users only."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.password = secrets.token_urlsafe(24)
        cls.internal = new_test_user(
            cls.env, login='brand002.internal', password=cls.password, groups='base.group_user')
        cls.portal = new_test_user(
            cls.env, login='brand002.portal', password=cls.password, groups='base.group_portal')

    def _get(self, url, **kw):
        return self.url_open(url, allow_redirects=False, **kw)

    def _assert_redirect(self, response, location, codes=(302,)):
        self.assertIn(response.status_code, codes, response.headers.get('Location'))
        self.assertEqual(_location(response), location)
        netloc = urlsplit(response.headers['Location']).netloc
        self.assertIn(netloc, ('', urlsplit(self.base_url()).netloc))

    def _csrf_from_login(self, url='/dang-nhap'):
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        return html.fromstring(response.content).xpath("//input[@name='csrf_token']/@value")[0]

    @staticmethod
    def _title(response):
        titles = html.fromstring(response.content).xpath('//head/title')
        return ' '.join(titles[0].text_content().split()) if titles else ''

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def test_root_follows_the_session(self):
        self.assertIn(self._get('/').status_code, (302, 303))
        self.assertEqual(urlsplit(_location(self._get('/'))).path, '/dang-nhap')
        self.authenticate(self.internal.login, self.password)
        self.assertEqual(urlsplit(_location(self._get('/'))).path, '/app')
        self.authenticate(self.portal.login, self.password)
        self.assertEqual(urlsplit(_location(self._get('/'))).path, '/my')
        self.assertEqual(urlsplit(_location(self._get('/app'))).path, '/my')

    # ------------------------------------------------------------------
    # Legacy GET/HEAD -> temporary redirect, query kept byte for byte
    # ------------------------------------------------------------------
    def test_legacy_login_get_and_head_redirect(self):
        query = 'redirect=%2Fodoo%2Faction-12%3Fa%3D1&x=%C3%A1'
        self._assert_redirect(self._get(f'/web/login?{query}'), f'/dang-nhap?{query}')
        self._assert_redirect(self._get(f'/web/login?{query}', method='HEAD'), f'/dang-nhap?{query}')
        self._assert_redirect(self._get('/web/login/'), '/dang-nhap')
        self._assert_redirect(self._get('/web/login/totp?redirect=%2Fodoo'), '/dang-nhap/xac-thuc?redirect=%2Fodoo')
        self._assert_redirect(self._get('/web/reset_password'), '/quen-mat-khau')
        self._assert_redirect(self._get('/web/signup'), '/tao-tai-khoan')

    def test_legacy_webclient_paths_redirect(self):
        self._assert_redirect(self._get('/odoo/action-tp_web_home.action_home?debug=1'),
                              '/app/action-tp_web_home.action_home?debug=1')
        self._assert_redirect(self._get('/odoo/tp-home/5'), '/app/tp-home/5')
        self._assert_redirect(self._get('/odoo'), '/app')
        self._assert_redirect(self._get('/web'), '/app')
        self._assert_redirect(self._get('/web?debug=assets'), '/app?debug=assets')
        self.authenticate(self.internal.login, self.password)
        self._assert_redirect(self._get('/odoo/tp-home'), '/app/tp-home')
        self.assertEqual(self.url_open('/odoo/tp-home').url, self.base_url() + '/app/tp-home')
        # Legacy attendance paths redirect cleanly to /app/cham-cong/... without loops, keeping query & detail ID.
        self._assert_redirect(
            self._get('/app/nhan-su/cham-cong/tong-quan?dept=5'),
            '/app/cham-cong/tong-quan?dept=5',
        )
        self._assert_redirect(
            self._get('/app/nhan-su/cham-cong/dieu-chinh/12?state=submitted'),
            '/app/cham-cong/dieu-chinh/12?state=submitted',
        )
        self.assertEqual(self._get('/app/cham-cong/tong-quan?dept=5').status_code, 200)

    def test_not_legacy_paths_are_not_redirected(self):
        offline = self._get('/odoo/offline')
        self.assertEqual(offline.status_code, 200)
        self.assertEqual(self._title(offline), 'Ngoại tuyến | TANPHAT ONE')
        self.assertIn('Bạn đang ngoại tuyến', offline.text)
        self.assertNotIn('/app', _location(self._get('/odoox')))
        self.assertEqual(self._get('/web/health').status_code, 200)
        not_found = self._get('/tp-brand002-khong-ton-tai')
        self.assertEqual(not_found.status_code, 404)
        self.assertTrue(self._title(not_found).endswith('TANPHAT ONE'), self._title(not_found))
        self.assertNotIn('Powered by', not_found.text)

    # ------------------------------------------------------------------
    # Authentication pages
    # ------------------------------------------------------------------
    def test_branded_login_page_keeps_the_approved_layout(self):
        response = self._get('/dang-nhap')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._title(response), 'Đăng nhập | TANPHAT ONE')
        document = html.fromstring(response.content)
        self.assertTrue(document.xpath("//*[contains(@class, 'tp-native-wordmark')]"))
        self.assertEqual(document.xpath("//form[contains(@class, 'oe_login_form')]/@action"), ['/dang-nhap'])
        self.assertTrue(document.xpath("//input[@name='csrf_token' and @value]"))
        self.assertFalse(document.xpath("//a[contains(@href, 'odoo.com')]"))
        text = ' '.join(document.text_content().split())
        self.assertTrue('by Tadic' in text or 'TADIC' in text, text)
        self.assertNotIn('Powered by', text)
        # Link preview metadata (native: only for a webclient deep link).
        shared = html.fromstring(self._get('/dang-nhap?redirect=%2Fapp%2Ftp-home').content)
        self.assertEqual(shared.xpath("//meta[@property='og:site_name']/@content"), ['TANPHAT ONE'])
        self.assertTrue(shared.xpath("//meta[@property='og:url']/@content")[0].endswith('/app/tp-home'))
        self.assertTrue(shared.xpath("//meta[@property='og:image']/@content")[0].endswith('/tp_logo_full.png'))
        self.assertFalse(shared.xpath("//meta[@name='twitter:site']"))
        metas = ' '.join(shared.xpath("//meta/@content"))
        self.assertNotIn('Odoo', metas)
        self.assertNotIn('All your business', metas)

    def test_post_is_never_redirected_and_csrf_stays(self):
        for path in ('/web/login', '/dang-nhap'):
            bad = self._get(path, method='POST', data={
                'csrf_token': 'invalid', 'login': self.internal.login, 'password': self.password,
            })
            self.assertEqual(bad.status_code, 400, path)

    def test_login_on_branded_path_lands_on_app(self):
        token = self._csrf_from_login()
        response = self._get('/dang-nhap', method='POST', data={
            'csrf_token': token, 'login': self.internal.login, 'password': self.password,
            'type': 'password', 'redirect': '/odoo/tp-home?x=1',
        })
        self._assert_redirect(response, '/app/tp-home?x=1', codes=(303,))
        page = self.url_open('/app/tp-home')
        self.assertEqual(page.status_code, 200)
        self.assertEqual(self._title(page), 'TANPHAT ONE')
        self.assertTrue(re.search(r'csrf_token:\s*"[^"]+"', page.text))

    def test_backend_bundle_ships_the_adapters(self):
        bundle = self.env['ir.qweb']._get_asset_bundle('web.assets_backend', assets_params={})
        js = bundle.js().raw.decode()
        for module in ('@tp_branding/brand_routes', '@tp_branding/brand_urls', '@tp_branding/router_patch', '@tp_branding/title_patch',
                       '@tp_branding/webclient_patch', '@tp_branding/dialog_patch', '@tp_branding/links_patch',
                       '@tp_branding/webview_error_guard'):
            self.assertIn(module, js)

    def test_frontend_bundle_ships_webview_error_guard(self):
        bundle = self.env['ir.qweb']._get_asset_bundle('web.assets_frontend', assets_params={})
        js = bundle.js().raw.decode()
        self.assertIn('@tp_branding/webview_error_guard', js)

    def test_anonymous_app_goes_to_branded_login(self):
        response = self._get('/app/tp-home?x=1')
        self.assertIn(response.status_code, (302, 303))
        location = urlsplit(_location(response))
        self.assertEqual(location.path, '/dang-nhap')
        self.assertTrue(parse_qs(location.query)['redirect'][0].startswith('/app/tp-home?x=1'))

    def test_logout_lands_on_branded_login(self):
        self.authenticate(self.internal.login, self.password)
        page = self.url_open('/app/tp-home')
        token = re.search(r'csrf_token:\s*"([^"]+)"', page.text)[1]
        ended = self._get('/web/session/logout', method='POST', data={'csrf_token': token, 'redirect': '/app'})
        self._assert_redirect(ended, '/dang-nhap', codes=(303,))
        self.assertIn(urlsplit(_location(self._get('/app'))).path, ('/dang-nhap',))

    def test_totp_alias_without_pending_login(self):
        response = self._get('/dang-nhap/xac-thuc')
        self.assertIn(response.status_code, (302, 303))
        self.assertEqual(urlsplit(_location(response)).path, '/dang-nhap')

    def test_self_service_policy_is_unchanged(self):
        parameters = self.env['ir.config_parameter'].sudo()
        parameters.set_str('auth_signup.invitation_scope', 'b2b')
        parameters.set_bool('auth_signup.reset_password', False)
        self.assertEqual(self._get('/tao-tai-khoan').status_code, 404)
        self.assertEqual(self._get('/quen-mat-khau').status_code, 404)
        login = html.fromstring(self._get('/dang-nhap').content)
        self.assertFalse(login.xpath("//a[starts-with(@href, '/tao-tai-khoan') or starts-with(@href, '/web/signup')]"))
        self.assertFalse(login.xpath(
            "//a[starts-with(@href, '/quen-mat-khau') or starts-with(@href, '/web/reset_password')]"))
        parameters.set_str('auth_signup.invitation_scope', 'b2c')
        parameters.set_bool('auth_signup.reset_password', True)
        login = html.fromstring(self._get('/dang-nhap').content)
        self.assertTrue(login.xpath("//a[starts-with(@href, '/tao-tai-khoan')]"))
        self.assertTrue(login.xpath("//a[starts-with(@href, '/quen-mat-khau')]"))
        for path, title in (('/tao-tai-khoan', 'Tạo tài khoản'), ('/quen-mat-khau', 'Đặt lại mật khẩu')):
            page = self._get(path)
            self.assertEqual(page.status_code, 200, path)
            self.assertEqual(self._title(page), f'{title} | TANPHAT ONE')
            self.assertTrue(html.fromstring(page.content).xpath("//form[@method='post']"))

    # ------------------------------------------------------------------
    # PWA
    # ------------------------------------------------------------------
    def test_manifest_and_service_worker(self):
        manifest = self._get('/web/manifest.webmanifest').json()
        self.assertEqual(manifest['id'], '/odoo')
        self.assertEqual(manifest['scope'], '/app')
        self.assertEqual(manifest['start_url'], '/app')
        app_name = self.env['ir.config_parameter'].sudo().get_str('web.web_app_name')
        if not app_name or app_name == 'Odoo':
            self.assertEqual(manifest['name'], 'TANPHAT ONE')
        self.assertNotIn('Odoo', manifest['name'])
        for icon in manifest['icons']:
            self.assertTrue(icon['src'].startswith('/tp_branding/static/img/icon-'))
            image = self._get(icon['src'])
            self.assertEqual(image.status_code, 200)
            self.assertEqual(image.headers['Content-Type'], 'image/png')
        for shortcut in manifest.get('shortcuts', []):
            self.assertFalse(shortcut['url'].startswith('/odoo'), shortcut)
        worker = self._get('/web/service-worker.js')
        self.assertEqual(worker.status_code, 200)
        self.assertEqual(worker.headers['Service-Worker-Allowed'], '/')
        self.assertNotIn('Response.redirect("/odoo?share_target=trigger")', worker.text)

    # ------------------------------------------------------------------
    # SYSTEM-URL-001: Hierarchical Business Routes & Deep Links
    # ------------------------------------------------------------------
    def test_anonymous_hierarchical_deep_link_redirects_to_login(self):
        """Anonymous access to /app/nhan-su/nhan-vien/44 redirects to branded login with redirect param."""
        response = self._get('/app/nhan-su/nhan-vien/44')
        self.assertIn(response.status_code, (302, 303))
        location = urlsplit(_location(response))
        self.assertEqual(location.path, '/dang-nhap')
        self.assertEqual(parse_qs(location.query)['redirect'][0].rstrip('?'), '/app/nhan-su/nhan-vien/44')

    def test_authenticated_hierarchical_deep_link_returns_webclient(self):
        """Authenticated user accessing /app/nhan-su/nhan-vien/44 receives webclient HTML."""
        self.authenticate(self.internal.login, self.password)
        page = self.url_open('/app/nhan-su/nhan-vien/44')
        self.assertEqual(page.status_code, 200)
        self.assertEqual(self._title(page), 'TANPHAT ONE')

    def test_login_redirect_preserves_business_deep_link(self):
        """Login with redirect to a business route redirects directly to that business URL."""
        token = self._csrf_from_login()
        response = self._get('/dang-nhap', method='POST', data={
            'csrf_token': token,
            'login': self.internal.login,
            'password': self.password,
            'type': 'password',
            'redirect': '/app/khkd/du-an-tiem-nang/12',
        })
        self._assert_redirect(response, '/app/khkd/du-an-tiem-nang/12', codes=(303,))

    def test_ir_http_session_info_has_route_map(self):
        """IrHttp session_info exposes tp_action_routes dictionary."""
        self.authenticate(self.internal.login, self.password)
        response = self.url_open(
            '/web/session/get_session_info',
            headers={'Content-Type': 'application/json'},
            data='{}',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json().get('result', {})
        self.assertIn('tp_action_routes', data)
        self.assertIn('xml_to_id', data['tp_action_routes'])
        self.assertIn('id_to_xml', data['tp_action_routes'])
