# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
import os
import re

from odoo.tests import BaseCase, tagged

from odoo.addons.tp_branding.brand_routes import (
    MODEL_FALLBACK_URLS,
    ROUTE_DEFINITIONS,
    get_all_action_xml_ids,
    get_route_by_action_tag,
    get_route_by_action_xml_id,
    get_route_by_model,
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
        """All registered routes must comply with naming and uniqueness rules."""
        url_regex = re.compile(r'^/app/[a-z0-9-]+(/[a-z0-9-]+)*$')
        seen_urls = set()
        seen_aliases = set()
        seen_slugs = set()

        valid_prefixes = (
            '/app/trang-chu',
            '/app/tai-khoan',
            '/app/nhan-su',
            '/app/cham-cong',
            '/app/khkd',
            '/app/thiet-bi',
            '/app/de-nghi',
            '/app/bao-cao',
            '/app/ca-nhan',
            '/app/van-phong-so',
            '/app/du-an',
            '/app/dieu-hanh',
            '/app/tuyen-dung',
            '/app/quan-tri',
        )

        for route in ROUTE_DEFINITIONS:
            url = route['url']
            self.assertRegex(url, url_regex, f"URL {url} must be lowercase alphanumeric with hyphens")
            self.assertNotIn(url, seen_urls, f"Duplicate canonical URL: {url}")
            seen_urls.add(url)

            self.assertTrue(
                url.startswith(valid_prefixes),
                f"URL {url} must start with one of {valid_prefixes}",
            )
            self.assertNotIn('/khkh/', url, "Never typo khkd as khkh")

            slug = route.get('native_slug')
            if slug:
                self.assertNotIn(slug, seen_slugs, f"Duplicate native_slug: {slug}")
                seen_slugs.add(slug)

        for route in ROUTE_DEFINITIONS:
            for alias in route.get('aliases') or ():
                self.assertRegex(alias, url_regex, f"Alias {alias} must match /app/... format")
                self.assertNotIn(alias, seen_urls, f"Alias {alias} collides with canonical URL")
                self.assertNotIn(alias, seen_aliases, f"Duplicate alias: {alias}")
                seen_aliases.add(alias)

        for model_name, target_url in MODEL_FALLBACK_URLS.items():
            self.assertIn(target_url, seen_urls, f"MODEL_FALLBACK_URLS[{model_name}] points to unknown {target_url}")

    def test_route_lookup_helpers(self):
        """Lookup helpers must find registered routes correctly."""
        r1 = get_route_by_url('/app/nhan-su/nhan-vien')
        self.assertIsNotNone(r1)
        self.assertEqual(r1['action_xml_id'], 'tp_hr_workspace.action_employees')

        r2 = get_route_by_url('/app/tp-home')
        self.assertIsNotNone(r2)
        self.assertEqual(r2['url'], '/app/trang-chu')

        r3 = get_route_by_action_xml_id('tp_hr_attendance.action_dashboard')
        self.assertIsNotNone(r3)
        self.assertEqual(r3['url'], '/app/cham-cong/tong-quan')

        r3_legacy = get_route_by_url('/app/nhan-su/cham-cong/tong-quan')
        self.assertIsNotNone(r3_legacy)
        self.assertEqual(r3_legacy['url'], '/app/cham-cong/tong-quan')

        r4 = get_route_by_action_tag('tp_equipment.dashboard')
        self.assertIsNotNone(r4)
        self.assertEqual(r4['url'], '/app/thiet-bi/tong-quan')

        r5 = get_route_by_native_slug('users')
        self.assertIsNotNone(r5)
        self.assertEqual(r5['url'], '/app/quan-tri/tai-khoan')

        # System settings vs server actions split
        r_settings = get_route_by_url('/app/quan-tri/cai-dat')
        self.assertIsNotNone(r_settings)
        self.assertEqual(r_settings['action_xml_id'], 'base_setup.action_general_configuration')
        self.assertEqual(get_route_by_native_slug('settings')['url'], '/app/quan-tri/cai-dat')
        self.assertEqual(
            get_route_by_action_xml_id('base.action_server_action')['url'],
            '/app/quan-tri/hanh-dong-may-chu',
        )

        # Attendance board vs days split
        self.assertEqual(
            get_route_by_action_xml_id('tp_hr_attendance.action_board')['url'],
            '/app/cham-cong/bang-cong',
        )
        self.assertEqual(
            get_route_by_action_tag('tp_hr_attendance.board')['url'],
            '/app/cham-cong/bang-cong',
        )
        self.assertEqual(
            get_route_by_action_xml_id('tp_hr_attendance.action_days')['url'],
            '/app/cham-cong/ngay-cong',
        )

        # Secondary XML IDs & model fallback
        self.assertEqual(
            get_route_by_action_xml_id('tp_contract.action_tp_contracts')['url'],
            '/app/khkd/hop-dong',
        )
        self.assertEqual(
            get_route_by_action_xml_id('project_todo.project_task_action_todo')['url'],
            '/app/ca-nhan/cong-viec',
        )
        self.assertEqual(get_route_by_model('tp.contract')['url'], '/app/khkd/hop-dong')
        self.assertEqual(get_route_by_model('tp.bank')['url'], '/app/nhan-su/danh-muc-ngan-hang')
        self.assertEqual(
            get_route_by_action_xml_id('tp_kd_workspace.action_dossier_documents')['url'],
            '/app/khkd/tai-lieu-ho-so',
        )
        self.assertEqual(
            get_route_by_action_xml_id('tp_kd_workspace.action_task_updates')['url'],
            '/app/khkd/lich-su-cong-viec',
        )
        self.assertEqual(
            get_route_by_action_xml_id('tp_equipment.action_inventory_lines')['url'],
            '/app/thiet-bi/dong-kiem-ke',
        )
        self.assertFalse(
            get_route_by_action_xml_id('tp_equipment.action_inventory_lines')['has_detail'],
        )
        self.assertFalse(get_route_by_action_xml_id('tp_hr_attendance.action_late')['has_detail'])
        self.assertFalse(get_route_by_action_xml_id('tp_hr_attendance.action_logs')['has_detail'])
        self.assertEqual(get_route_by_native_slug('ho-so-thiet-bi')['url'], '/app/thiet-bi/tat-ca')
        self.assertIsNone(
            get_route_by_action_xml_id('tp_hr_workspace.action_public_overview').get('action_tag'),
        )

    def test_canonical_app_path(self):
        """Aliases (including legacy /app/nhan-su/cham-cong/...) canonicalize to business route URLs."""
        self.assertEqual(canonical_app_path('/app/tp-home'), '/app/trang-chu')
        self.assertEqual(canonical_app_path('/app/settings'), '/app/quan-tri/cai-dat')
        self.assertEqual(canonical_app_path('/app/dieu-hanh/lanh-dao'), '/app/dieu-hanh/tong-quan')
        self.assertEqual(canonical_app_path('/app/dieu-hanh/tong-quan'), '/app/dieu-hanh/tong-quan')
        self.assertEqual(canonical_app_path('/app/khao-sat/thiet-bi-kiem-dinh'), '/app/thiet-bi/khao-sat')
        self.assertEqual(canonical_app_path('/app/thiet-bi/khao-sat'), '/app/thiet-bi/khao-sat')
        self.assertEqual(canonical_app_path('/app/tro-ly-ai'), '/app/dieu-hanh/tro-ly-ai')
        self.assertEqual(canonical_app_path('/app/dieu-hanh/tro-ly-ai'), '/app/dieu-hanh/tro-ly-ai')
        self.assertEqual(canonical_app_path('/app/ke-hoach-kinh-doanh'), '/app/khkd/tong-quan')
        self.assertEqual(canonical_app_path('/app/hop-dong'), '/app/khkd/hop-dong')
        self.assertEqual(canonical_app_path('/app/hop-dong/15'), '/app/khkd/hop-dong/15')
        self.assertEqual(canonical_app_path('/app/cham-cong'), '/app/cham-cong/tong-quan')
        self.assertEqual(canonical_app_path('/app/nhan-su/cham-cong'), '/app/cham-cong/tong-quan')
        self.assertEqual(canonical_app_path('/app/nhan-su/cham-cong/tong-quan'), '/app/cham-cong/tong-quan')
        self.assertEqual(canonical_app_path('/app/cong-cua-toi'), '/app/cham-cong/cua-toi')
        self.assertEqual(canonical_app_path('/app/nhan-su/cham-cong/cua-toi'), '/app/cham-cong/cua-toi')
        self.assertEqual(canonical_app_path('/app/nguon-cham-cong'), '/app/cham-cong/quan-tri')
        self.assertEqual(canonical_app_path('/app/nhan-su/cham-cong/quan-tri'), '/app/cham-cong/quan-tri')
        self.assertEqual(canonical_app_path('/app/ngay-cong'), '/app/cham-cong/ngay-cong')
        self.assertEqual(canonical_app_path('/app/bang-cong'), '/app/cham-cong/bang-cong')
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
        self.assertGreater(len(xml_ids), 100)
        self.assertIn('tp_contract.action_tp_contracts', xml_ids)
        self.assertIn('project_todo.project_task_action_todo', xml_ids)
        for xid in xml_ids:
            self.assertIn('.', xid, f"XML ID must contain dot: {xid}")
            mod, name = xid.split('.', 1)
            self.assertTrue(len(mod) > 0 and len(name) > 0)

    def test_python_and_js_registry_parity(self):
        """Frontend and backend must have the exact same list of canonical URLs and XML IDs."""
        test_dir = os.path.dirname(os.path.abspath(__file__))
        js_path = os.path.normpath(os.path.join(test_dir, '..', 'static', 'src', 'brand_routes.js'))
        self.assertTrue(os.path.exists(js_path), f"JS file must exist: {js_path}")

        with open(js_path, encoding='utf-8') as f:
            js_content = f.read()

        js_urls = re.findall(r'url:\s*"(.*?)"', js_content)
        py_urls = [r['url'] for r in ROUTE_DEFINITIONS]

        self.assertEqual(
            sorted(js_urls),
            sorted(py_urls),
            "JS Route Registry and Python Route Registry must have identical canonical URLs!",
        )

        js_xml_ids = re.findall(r'action_xml_id:\s*"(.*?)"', js_content)
        py_xml_ids = [r['action_xml_id'] for r in ROUTE_DEFINITIONS if r.get('action_xml_id')]

        self.assertEqual(
            sorted(js_xml_ids),
            sorted(py_xml_ids),
            "JS Route Registry and Python Route Registry must have identical action_xml_ids!",
        )
