from odoo.exceptions import AccessError
from odoo.tests import HttpCase, TransactionCase, new_test_user, tagged

HOME_RECORDS = {
    ('ir.actions.client', 'action_home'),
    ('ir.ui.menu', 'menu_home'),
    ('ir.ui.view', 'webclient_bootstrap_user_zoom'),
}


@tagged('post_install', '-at_install')
class TestHomeMenu(TransactionCase):
    """Home is one native client action + root menu; menus stay filtered per user on the server."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.home_menu = cls.env.ref('tp_web_home.menu_home')
        cls.home_action = cls.env.ref('tp_web_home.action_home')
        cls.employee = new_test_user(cls.env, login='home001.employee', groups='base.group_user')
        cls.manager = new_test_user(
            cls.env, login='home001.manager', groups='base.group_user,base.group_system')
        cls.portal = new_test_user(cls.env, login='home001.portal', groups='base.group_portal')

    def roots(self, user):
        return self.env['ir.ui.menu'].with_user(user).load_menus(False)

    def test_module_owns_only_the_home_action_and_menu(self):
        owned = self.env['ir.model.data'].search([('module', '=', 'tp_web_home')])
        self.assertEqual({(data.model, data.name) for data in owned}, HOME_RECORDS)

    def test_backend_viewport_keeps_user_zoom(self):
        # MOBILE-001: same device-width viewport as native, without user-scalable=no.
        arch = self.env.ref('web.webclient_bootstrap').get_combined_arch()
        self.assertIn('content="width=device-width, initial-scale=1"', arch)
        self.assertNotIn('user-scalable', arch)
        self.assertNotIn('maximum-scale', arch)

    def test_home_is_a_root_client_action_for_internal_users(self):
        self.assertFalse(self.home_menu.parent_id)
        self.assertEqual(self.home_menu.action, self.home_action)
        self.assertEqual(self.home_menu.group_ids, self.env.ref('base.group_user'))
        self.assertEqual(self.home_action.tag, 'tp_web_home.home')
        self.assertEqual(self.home_action.path, 'tp-home')

    def test_home_is_the_first_root_so_native_default_app_opens_it(self):
        for user in (self.employee, self.manager):
            menus = self.roots(user)
            self.assertEqual(menus['root']['children'][0], self.home_menu.id, user.login)
            home = menus[self.home_menu.id]
            self.assertEqual(home['xmlid'], 'tp_web_home.menu_home')
            self.assertEqual(home['action_path'], 'tp-home')

    def test_portal_user_does_not_receive_home(self):
        # Portal users cannot read backend menus at all, so they never get the Home menu either.
        with self.assertRaises(AccessError):
            self.env['ir.ui.menu'].with_user(self.portal).search([('id', '=', self.home_menu.id)])
        with self.assertRaises(AccessError):
            self.roots(self.portal)

    def test_two_actors_receive_their_own_apps_and_record_access_stays_blocked(self):
        settings = self.env.ref('base.menu_administration').id
        employee_roots = self.roots(self.employee)['root']['children']
        manager_roots = self.roots(self.manager)['root']['children']
        self.assertNotIn(settings, employee_roots)
        self.assertIn(settings, manager_roots)
        self.assertLess(set(employee_roots), set(manager_roots))
        # Home only lists what the menu service returns; it never widens record rights.
        with self.assertRaises(AccessError):
            self.env['ir.config_parameter'].with_user(self.employee).search_read([], ['key'])
        self.env['ir.config_parameter'].with_user(self.manager).search_read([], ['key'], limit=1)

    def test_administration_area_follows_group_system_not_access_rights(self):
        # UI-HOME-003: Home builds "Quản trị hệ thống" from the session flag is_system
        # (base.group_system). Access Rights (group_erp_manager, session is_admin) is not enough.
        rights = new_test_user(
            self.env, login='home003.rights', groups='base.group_user,base.group_erp_manager')
        self.assertTrue(rights._is_admin())
        self.assertFalse(rights._is_system())
        self.assertFalse(self.employee._is_system())
        self.assertTrue(self.manager._is_system())
        # The native switcher still receives Settings for that user; Home simply does not list it.
        settings = self.env.ref('base.menu_administration').id
        self.assertIn(settings, self.roots(rights)['root']['children'])

    def test_no_default_home_action_and_no_other_menu_points_to_home(self):
        # Existing administrators may explicitly assign Home; never forbid their settings.
        self.assertFalse((self.employee | self.manager | self.portal).filtered('action_id'))
        menus = self.env['ir.ui.menu'].with_context(active_test=False).search(
            [('action', '=', f'ir.actions.client,{self.home_action.id}')])
        self.assertEqual(menus, self.home_menu)

    def test_existing_user_home_action_is_kept(self):
        settings_action = self.env['ir.actions.actions'].browse(self.env.ref('base.action_res_users').id)
        self.manager.action_id = settings_action
        self.assertEqual(self.manager.action_id, settings_action)
        self.assertEqual(self.roots(self.manager)['root']['children'][0], self.home_menu.id)


@tagged('post_install', '-at_install')
class TestHomeHttp(HttpCase):
    """The Home route stays behind the native web client guards."""

    def test_public_is_redirected_to_login(self):
        response = self.url_open('/odoo/tp-home', allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))
        self.assertIn('/web/login', response.headers['Location'])

    def test_portal_has_no_backend(self):
        new_test_user(self.env, login='home001.portal.http', groups='base.group_portal')
        self.authenticate('home001.portal.http', 'home001.portal.http')
        response = self.url_open('/odoo/tp-home', allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))
        self.assertNotIn('/odoo', response.headers['Location'])

    def test_internal_user_gets_web_client_and_valid_assets(self):
        new_test_user(self.env, login='home001.http', groups='base.group_user')
        self.authenticate('home001.http', 'home001.http')
        response = self.url_open('/odoo/tp-home')
        self.assertEqual(response.status_code, 200)
        menus = self.url_open('/web/webclient/load_menus').json()
        home = self.env.ref('tp_web_home.menu_home').id
        self.assertEqual(menus['root']['children'][0], home)
        bundle = self.env['ir.qweb']._get_asset_bundle('web.assets_backend', assets_params={})
        js = bundle.js().raw.decode()
        self.assertIn('tp_web_home.home', js)
        self.assertIn('tp_web_home.home_button', js)
        css = bundle.css().raw.decode()
        self.assertIn('o_tp_web_home_tile', css)
        self.assertNotIn('CSS error message', css)
