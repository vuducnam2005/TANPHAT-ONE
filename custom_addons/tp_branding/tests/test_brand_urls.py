# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
import os
import re
from odoo.tests import BaseCase, tagged

from odoo.addons.tp_branding.brand_routes import (
    ROUTE_DEFINITIONS,
    get_all_action_xml_ids,
    get_route_by_action_tag,
    get_route_by_action_xml_id,
    get_route_by_native_slug,
    get_route_by_url,
)
from odoo.addons.tp_branding.brand_urls import (
    brand_path,
    brand_title,
    brand_url,
    canonical_app_path,
    is_app_path,
    is_legacy_app_path,
    native_path,
    native_url,
)


@tagged('post_install', '-at_install')
class TestBrandUrls(BaseCase):
    """BRAND-WHITELABEL-002, SYSTEM-URL-001: URL mapping and business routes."""

    def test_app_prefix(self):
        self.assertEqual(brand_path('/odoo'), '/app')
        self.assertEqual(brand_path('/odoo/'), '/app/')
        self.assertEqual(brand_path('/odoo/tp-home'), '/app/tp-home')
        self.assertEqual(brand_path('/odoo/action-12/5'), '/app/action-12/5')
        self.assertEqual(brand_path('/odoo/m-res.partner/new'), '/app/m-res.partner/new')
        self.assertEqual(brand_path('/web'), '/app')
        self.assertEqual(brand_path('/web/'), '/app')

    def test_not_a_prefix_match(self):
        for path in ('/odoox', '/odoo-x', '/odoo.png', '/web/assets/1/x.js', '/web/webclient/load_menus',
                     '/web/session/logout', '/web/login/extra', '/web/loginx', '/my', '/', '',
                     '/odoo/offline', '/tp_web_home/static/img/brand/favicon.ico', '/scoped_app/x'):
            self.assertEqual(brand_path(path), path, path)

    def test_auth_paths(self):
        self.assertEqual(brand_path('/web/login'), '/dang-nhap')
        self.assertEqual(brand_path('/web/login/'), '/dang-nhap')
        self.assertEqual(brand_path('/web/login/totp'), '/dang-nhap/xac-thuc')
        self.assertEqual(brand_path('/web/reset_password'), '/quen-mat-khau')
        self.assertEqual(brand_path('/web/signup'), '/tao-tai-khoan')
        self.assertEqual(native_path('/dang-nhap'), '/web/login')
        self.assertEqual(native_path('/dang-nhap/xac-thuc'), '/web/login/totp')
        self.assertEqual(native_path('/app/action-12'), '/odoo/action-12')
        self.assertEqual(native_path('/apps'), '/apps')

    def test_query_and_fragment_are_kept_byte_for_byte(self):
        self.assertEqual(
            brand_url('/odoo/action-12?debug=assets&next=%2Fodoo%2Fx#id=5&odoo=1'),
            '/app/action-12?debug=assets&next=%2Fodoo%2Fx#id=5&odoo=1',
        )
        self.assertEqual(
            brand_url('/web/login?redirect=%2Fodoo%2Faction-12%3Fa%3D1'),
            '/dang-nhap?redirect=%2Fodoo%2Faction-12%3Fa%3D1',
        )
        self.assertEqual(brand_url('/web#action=12&id=5'), '/app#action=12&id=5')
        self.assertEqual(native_url('/app/x?y=/app#/app'), '/odoo/x?y=/app#/app')

    def test_external_and_ambiguous_urls_are_untouched(self):
        for url in ('https://example.invalid/odoo', '//example.invalid/odoo', '/\\example.invalid/odoo',
                    'odoo/action-1', 'javascript:alert(1)', '', None, 42):
            self.assertEqual(brand_url(url), url)
            self.assertEqual(native_url(url), url)

    def test_predicates(self):
        self.assertTrue(is_app_path('/app'))
        self.assertTrue(is_app_path('/app/x'))
        self.assertTrue(is_app_path('/app/nhan-su/nhan-vien/44'))
        self.assertFalse(is_app_path('/apps'))
        self.assertTrue(is_legacy_app_path('/odoo/x'))
        self.assertFalse(is_legacy_app_path('/odoo/offline'))
        self.assertFalse(is_legacy_app_path('/odoox'))

    def test_title(self):
        self.assertEqual(brand_title(''), 'TANPHAT ONE')
        self.assertEqual(brand_title('Odoo'), 'TANPHAT ONE')
        self.assertEqual(brand_title('Dự án'), 'Dự án | TANPHAT ONE')
        self.assertEqual(brand_title('Dự án | TANPHAT ONE'), 'Dự án | TANPHAT ONE')

    # ------------------------------------------------------------------
    # SYSTEM-URL-001 Route Registry Tests
    # ------------------------------------------------------------------
    def test_route_definitions_standard(self):
        """All registered routes must comply with the 8 naming rules."""
        url_regex = re.compile(r'^/app/[a-z0-9-]+(/[a-z0-9-]+)*$')
        seen_urls = set()

        for route in ROUTE_DEFINITIONS:
            url = route['url']
            self.assertRegex(url, url_regex, f"URL {url} must be lowercase alphanumeric with hyphens")
            self.assertNotIn(url, seen_urls, f"Duplicate canonical URL: {url}")
            seen_urls.add(url)

            # Check module prefix rule: khkd, nhan-su, cham-cong, thiet-bi, de-nghi, bao-cao, quan-tri, trang-chu
            valid_prefixes = (
                '/app/trang-chu',
                '/app/tai-khoan',
                '/app/nhan-su',
                '/app/cham-cong',
                '/app/khkd',
                '/app/thiet-bi',
                '/app/de-nghi',
                '/app/bao-cao',
                '/app/quan-tri',
            )
            self.assertTrue(
                url.startswith(valid_prefixes),
                f"URL {url} must start with one of {valid_prefixes}"
            )
            # Must not confuse khkd with khkh
            self.assertNotIn('/khkh/', url, "Never typo khkd as khkh")

    def test_route_lookup_helpers(self):
        """Lookup helpers must find registered routes correctly."""
        # By canonical URL
        r1 = get_route_by_url('/app/nhan-su/nhan-vien')
        self.assertIsNotNone(r1)
        self.assertEqual(r1['action_xml_id'], 'tp_hr_workspace.action_employees')

        # By alias
        r2 = get_route_by_url('/app/tp-home')
        self.assertIsNotNone(r2)
        self.assertEqual(r2['url'], '/app/trang-chu')

        # By XML ID (standalone Chấm công canonical URL)
        r3 = get_route_by_action_xml_id('tp_hr_attendance.action_dashboard')
        self.assertIsNotNone(r3)
        self.assertEqual(r3['url'], '/app/cham-cong/tong-quan')

        # Legacy attendance alias resolves to standalone Chấm công route
        r3_legacy = get_route_by_url('/app/nhan-su/cham-cong/tong-quan')
        self.assertIsNotNone(r3_legacy)
        self.assertEqual(r3_legacy['url'], '/app/cham-cong/tong-quan')

        # By action tag
        r4 = get_route_by_action_tag('tp_equipment.dashboard')
        self.assertIsNotNone(r4)
        self.assertEqual(r4['url'], '/app/thiet-bi/tong-quan')

        # By native slug
        r5 = get_route_by_native_slug('users')
        self.assertIsNotNone(r5)
        self.assertEqual(r5['url'], '/app/quan-tri/tai-khoan')

    def test_canonical_app_path(self):
        """Aliases (including legacy /app/nhan-su/cham-cong/...) canonicalize to business route URLs."""
        self.assertEqual(canonical_app_path('/app/tp-home'), '/app/trang-chu')
        self.assertEqual(canonical_app_path('/app/cham-cong'), '/app/cham-cong/tong-quan')
        self.assertEqual(canonical_app_path('/app/nhan-su/cham-cong'), '/app/cham-cong/tong-quan')
        self.assertEqual(canonical_app_path('/app/nhan-su/cham-cong/tong-quan'), '/app/cham-cong/tong-quan')
        self.assertEqual(canonical_app_path('/app/cong-cua-toi'), '/app/cham-cong/cua-toi')
        self.assertEqual(canonical_app_path('/app/nhan-su/cham-cong/cua-toi'), '/app/cham-cong/cua-toi')
        self.assertEqual(canonical_app_path('/app/nguon-cham-cong'), '/app/cham-cong/quan-tri')
        self.assertEqual(canonical_app_path('/app/nhan-su/cham-cong/quan-tri'), '/app/cham-cong/quan-tri')
        self.assertEqual(canonical_app_path('/app/nhan-su/cham-cong/dieu-chinh/12'), '/app/cham-cong/dieu-chinh/12')
        self.assertEqual(canonical_app_path('/app/nhan-su/cham-cong/dieu-chinh/new'), '/app/cham-cong/dieu-chinh/tao-moi')
        self.assertEqual(brand_url('/app/nhan-su/cham-cong/dieu-chinh/12?filter=pending#top'), '/app/cham-cong/dieu-chinh/12?filter=pending#top')
        self.assertEqual(brand_path('/app/cham-cong/dieu-chinh/12'), '/app/cham-cong/dieu-chinh/12')
        self.assertEqual(canonical_app_path('/app/kho-thiet-bi'), '/app/thiet-bi/danh-sach')
        self.assertEqual(canonical_app_path('/app/kho-thiet-bi/44'), '/app/thiet-bi/danh-sach/44')
        self.assertEqual(canonical_app_path('/app/kho-thiet-bi/new'), '/app/thiet-bi/danh-sach/tao-moi')
        self.assertEqual(canonical_app_path('/app/users'), '/app/quan-tri/tai-khoan')
        self.assertEqual(canonical_app_path('/app/users/2'), '/app/quan-tri/tai-khoan/2')
        self.assertEqual(canonical_app_path('/app/unknown-custom-page'), '/app/unknown-custom-page')

    def test_xml_ids_integrity(self):
        """All xml_ids must be well-formed strings with module.name."""
        xml_ids = get_all_action_xml_ids()
        self.assertGreater(len(xml_ids), 20)
        for xid in xml_ids:
            self.assertIn('.', xid, f"XML ID must contain dot: {xid}")
            mod, name = xid.split('.', 1)
            self.assertTrue(len(mod) > 0 and len(name) > 0)

    def test_python_and_js_registry_parity(self):
        """Frontend and backend must have the exact same list of canonical URLs."""
        # Locate brand_routes.js relative to this test file
        test_dir = os.path.dirname(os.path.abspath(__file__))
        js_path = os.path.normpath(os.path.join(test_dir, '..', 'static', 'src', 'brand_routes.js'))
        self.assertTrue(os.path.exists(js_path), f"JS file must exist: {js_path}")

        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()

        js_urls = re.findall(r'url:\s*"(.*?)"', js_content)
        py_urls = [r['url'] for r in ROUTE_DEFINITIONS]

        self.assertEqual(
            sorted(js_urls),
            sorted(py_urls),
            "JS Route Registry and Python Route Registry must have identical canonical URLs!"
        )

        js_xml_ids = re.findall(r'action_xml_id:\s*"(.*?)"', js_content)
        py_xml_ids = [r['action_xml_id'] for r in ROUTE_DEFINITIONS if r.get('action_xml_id')]

        self.assertEqual(
            sorted(js_xml_ids),
            sorted(py_xml_ids),
            "JS Route Registry and Python Route Registry must have identical action_xml_ids!"
        )
