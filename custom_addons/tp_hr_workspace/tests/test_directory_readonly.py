"""HR-DIRECTORY-READONLY-001: every internal employee may view colleagues, never manage them."""
from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

# Private HR data that must never reach the shared directory (checked when the field exists in this build).
PRIVATE_FIELDS = (
    'private_phone', 'private_email', 'private_street', 'private_city', 'birthday', 'place_of_birth',
    'identification_id', 'passport_id', 'ssnid', 'sinid', 'bank_account_id', 'emergency_contact',
    'emergency_phone', 'spouse_complete_name', 'children', 'wage', 'contract_id',
    'private_car_plate', 'permit_no', 'visa_no',
)
# Native hr.employee.public also carries mobile_phone/user_id/phone/email; the directory views never show them.
DIRECTORY_FIELDS = {
    'tp_employee_code', 'avatar_128', 'avatar_256', 'image_1920', 'name', 'department_id', 'job_id', 'job_title',
    'parent_id', 'work_email', 'work_phone', 'work_location_id', 'company_id', 'birthday_public_display_string',
}


@tagged('post_install', '-at_install')
class TestDirectoryReadonly(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({'name': 'Synthetic Directory Company'})
        cls.dept_x, cls.dept_y = cls.env['hr.department'].create([
            {'name': 'Synthetic Directory X', 'company_id': cls.company.id},
            {'name': 'Synthetic Directory Y', 'company_id': cls.company.id},
        ])

        def user(login, *groups):
            return cls.env['res.users'].create({
                'name': login, 'login': login,
                'company_id': cls.company.id, 'company_ids': [Command.set([cls.company.id])],
                'group_ids': [Command.set([cls.env.ref(group).id for group in groups])],
            })

        cls.viewer_a = user('dir001.synthetic.a', 'base.group_user')
        cls.viewer_b = user('dir001.synthetic.b', 'base.group_user')
        cls.hr = user('dir001.synthetic.hr', 'hr.group_hr_user', 'base.group_allow_export')
        cls.emp_a, cls.emp_b = cls.env['hr.employee'].with_company(cls.company).create([
            {'name': 'Synthetic Directory A', 'company_id': cls.company.id, 'department_id': cls.dept_x.id,
             'user_id': cls.viewer_a.id, 'work_email': 'a.synthetic@example.invalid',
             'private_phone': '0900000001', 'identification_id': 'SYN-PRIVATE-A'},
            {'name': 'Synthetic Directory B', 'company_id': cls.company.id, 'department_id': cls.dept_y.id,
             'user_id': cls.viewer_b.id, 'work_email': 'b.synthetic@example.invalid',
             'private_phone': '0900000002', 'identification_id': 'SYN-PRIVATE-B'},
        ])

    def model(self, user, name):
        return self.env[name].with_user(user).with_context(allowed_company_ids=[self.company.id])

    def test_viewer_sees_whole_company_through_whitelist_views(self):
        public = self.model(self.viewer_a, 'hr.employee.public')
        found = public.search([('company_id', '=', self.company.id)])
        self.assertEqual(set(found.ids), {self.emp_a.id, self.emp_b.id})
        colleague = public.browse(self.emp_b.id)
        self.assertEqual(colleague.work_email, 'b.synthetic@example.invalid')
        self.assertEqual(colleague.department_id, self.dept_y)
        employee_fields = self.env['hr.employee']._fields
        for fname in PRIVATE_FIELDS:
            if fname in employee_fields:
                self.assertNotIn(fname, public._fields, f'{fname} leaked into hr.employee.public')
        for xmlid, view_type in (('directory_list', 'list'), ('directory_kanban', 'kanban'), ('directory_form', 'form')):
            view = self.env.ref(f'tp_hr_workspace.{xmlid}')
            result = public.get_views([(view.id, view_type)])
            arch = etree.fromstring(result['views'][view_type]['arch'])
            names = {node.get('name') for node in arch.iter('field')}
            self.assertLessEqual(names, DIRECTORY_FIELDS, xmlid)
            if view_type != 'kanban':
                self.assertEqual(arch.get('create'), '0')
                self.assertEqual(arch.get('delete'), '0')

    def test_viewer_cannot_change_or_read_private_records(self):
        public = self.model(self.viewer_a, 'hr.employee.public')
        employees = self.model(self.viewer_a, 'hr.employee')
        for operation in ('create', 'write', 'unlink'):
            self.assertFalse(public.has_access(operation), operation)
            self.assertFalse(employees.has_access(operation), operation)
        self.assertFalse(employees.has_access('read'))
        with self.assertRaises(AccessError):
            public.create({'name': 'Synthetic forbidden'})
        with self.assertRaises(AccessError):
            public.browse(self.emp_b.id).write({'job_title': 'Synthetic forbidden'})
        with self.assertRaises(AccessError):
            public.browse(self.emp_b.id).unlink()
        # Native proxy: hr.employee answers a viewer from hr.employee.public, private fields stay closed.
        proxied = employees.search([('id', '=', self.emp_b.id)])
        self.assertEqual(proxied.ids, [self.emp_b.id])
        self.assertEqual(proxied.read(['name', 'work_email'])[0]['work_email'], 'b.synthetic@example.invalid')
        with self.assertRaises(AccessError):
            employees.search([('private_phone', '=', '0900000002')])
        with self.assertRaises(AccessError):
            employees.search_count([('identification_id', '=', 'SYN-PRIVATE-B')])
        with self.assertRaises(AccessError):
            employees.browse(self.emp_b.id).read(['private_phone', 'identification_id'])
        with self.assertRaises(AccessError):
            employees.browse(self.emp_b.id).read(['birthday'])
        with self.assertRaises(AccessError):
            employees.browse(self.emp_a.id).copy()
        before = self.env['hr.employee'].search_count([('company_id', '=', self.company.id)])
        result = public.load(['name'], [['Synthetic loaded']])
        self.assertFalse(result.get('ids'))
        self.assertEqual(self.env['hr.employee'].search_count([('company_id', '=', self.company.id)]), before)
        with self.assertRaises(ValueError):
            public.search_count([('private_phone', '=', '0900000002')])

    def test_export_only_for_hr(self):
        with self.assertRaises(AccessError):
            self.model(self.viewer_a, 'hr.employee.public').browse(self.emp_b.id).export_data(['name', 'work_email'])
        exported = self.model(self.hr, 'hr.employee.public').browse(self.emp_b.id).export_data(['name'])
        self.assertEqual(exported['datas'], [['Synthetic Directory B']])

    def test_entry_and_menus_follow_real_groups(self):
        entry = self.env.ref('tp_hr_workspace.action_hr_entry')
        viewer_action = entry.with_user(self.viewer_a).run()
        self.assertEqual(viewer_action['res_model'], 'hr.employee.public')
        self.assertEqual(viewer_action['id'], self.env.ref('tp_hr_workspace.action_directory').id)
        hr_action = entry.with_user(self.hr).run()
        self.assertEqual(hr_action['id'], self.env.ref('tp_hr_workspace.action_overview').id)
        self.assertFalse(self.viewer_a.has_group('hr.group_hr_user'))

        def visible(user):
            return self.env['ir.ui.menu'].with_user(user)._visible_menu_ids()

        def ids(*xmlids):
            return {self.env.ref(f'tp_hr_workspace.{xmlid}').id for xmlid in xmlids}

        viewer_menus = visible(self.viewer_a)
        self.assertLessEqual(ids('menu_hr', 'menu_directory'), viewer_menus)
        self.assertFalse(ids('menu_overview', 'menu_employees', 'menu_missing', 'menu_archived', 'menu_import') & viewer_menus)
        hr_menus = visible(self.hr)
        self.assertLessEqual(ids('menu_hr', 'menu_overview', 'menu_employees'), hr_menus)
        self.assertNotIn(self.env.ref('tp_hr_workspace.menu_directory').id, hr_menus)

    def test_hr_keeps_management_rights(self):
        employees = self.model(self.hr, 'hr.employee')
        self.assertTrue(employees.has_access('read'))
        self.assertTrue(employees.has_access('write'))
        self.assertEqual(employees.browse(self.emp_b.id).identification_id, 'SYN-PRIVATE-B')
