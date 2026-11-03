from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import file_open
from odoo.tools.translate import translation_file_reader

CATALOG = 'tp_i18n_vi/i18n/vi.po'
GLOSSARY_APPS = {
    'mail.menu_root_discuss': 'Trao đổi',
    'project_todo.menu_todo_todos': 'Việc cá nhân',
    'calendar.mail_menu_calendar': 'Lịch làm việc',
    'contacts.menu_contacts': 'Khách hàng & đối tác',
    'hr_timesheet.timesheet_menu_root': 'Giờ làm việc',
    'hr.menu_hr_root': 'Nhân sự',
    'spreadsheet_dashboard.spreadsheet_dashboard_menu_root': 'Bảng tổng hợp',
    'base.menu_management': 'Ứng dụng Odoo',
}


@tagged('post_install', '-at_install')
class TestVietnameseCatalog(TransactionCase):

    def _rows(self):
        with file_open(CATALOG, 'rb') as fileobj:
            return [row for row in translation_file_reader(fileobj, fileformat='po') if row.get('type') == 'model']

    def test_catalog_matches_installed_source(self):
        rows = self._rows()
        self.assertGreater(len(rows), 40)
        for row in rows:
            xmlid = f"{row['module']}.{row['imd_name']}"
            record = self.env.ref(xmlid, raise_if_not_found=False)
            self.assertTrue(record, f'{xmlid} no longer exists')
            self.assertEqual(record._name, row['imd_model'], xmlid)
            field = row['name'].split(',')[1]
            self.assertEqual(record.with_context(lang='en_US')[field], row['src'], f'{xmlid} en_US source drifted')
            self.assertTrue(row['value'] and row['value'] != row['src'], xmlid)

    def test_overlay_wins_over_native_and_keeps_en_us(self):
        self.env['res.lang']._activate_lang('vi_VN')
        menus = {xmlid: self.env.ref(xmlid) for xmlid in GLOSSARY_APPS}
        before = {xmlid: (menu.id, menu.with_context(lang='en_US').name) for xmlid, menu in menus.items()}
        for menu in menus.values():
            menu.update_field_translations('name', {'vi_VN': 'Bản dịch native'})
        Module = self.env['ir.module.module']
        # a plain reload keeps whatever is stored; the documented upgrade uses overwrite
        Module._load_module_terms(['tp_i18n_vi'], ['vi_VN'], overwrite=False)
        self.env.invalidate_all()
        self.assertEqual(menus['hr.menu_hr_root'].with_context(lang='vi_VN').name, 'Bản dịch native')
        Module._load_module_terms(['tp_i18n_vi'], ['vi_VN'], overwrite=True)
        self.env.invalidate_all()
        for xmlid, expected in GLOSSARY_APPS.items():
            menu = self.env.ref(xmlid)
            self.assertEqual(menu.with_context(lang='vi_VN').name, expected, xmlid)
            self.assertEqual((menu.id, menu.with_context(lang='en_US').name), before[xmlid], xmlid)

    def test_overlay_loaded_after_overridden_modules(self):
        """In a full language reload the overlay is imported last, so its terms win within the import."""
        self.env['res.lang']._activate_lang('vi_VN')
        self.env.ref('mail.menu_root_discuss').update_field_translations('name', {'vi_VN': False})
        modules = self.env['ir.module.module'].search([('name', 'in', ['mail', 'tp_i18n_vi'])])
        modules._update_translations('vi_VN', overwrite=True)
        self.env.invalidate_all()
        self.assertEqual(self.env.ref('mail.menu_root_discuss').with_context(lang='vi_VN').name, 'Trao đổi')

    def test_translation_only_addon(self):
        owned = self.env['ir.model.data'].search([('module', '=', 'tp_i18n_vi')])
        self.assertFalse(owned, 'the overlay must not own models, views, menus, data or access rules')
