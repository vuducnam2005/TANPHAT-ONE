from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

from odoo.addons.tp_organization.models.hr_import import _INTERNAL


@tagged('post_install', '-at_install')
class TestHrUi(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({'name': 'Synthetic UI011 Company'})
        cls.department = cls.env['hr.department'].create({'name': 'Synthetic UI011 Unit', 'company_id': cls.company.id})
        cls.job = cls.env['hr.job'].create({'name': 'Synthetic UI011 Job', 'company_id': cls.company.id})
        cls.category = cls.env['hr.employee.category'].create({'name': 'Synthetic UI011 Tag'})
        cls.officer = cls.env['res.users'].create({
            'name': 'Synthetic UI011 Officer', 'login': 'test.ui011.officer',
            'company_id': cls.company.id, 'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref('hr.group_hr_user').id])],
        })
        cls.staff = cls.env['res.users'].create({
            'name': 'Synthetic UI011 Staff', 'login': 'test.ui011.staff',
            'company_id': cls.company.id, 'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })
        cls.employees = cls.env['hr.employee'].with_company(cls.company).create([
            {'name': 'Synthetic UI011 Visible', 'company_id': cls.company.id, 'department_id': cls.department.id,
             'job_id': cls.job.id, 'category_ids': [Command.set(cls.category.ids)]},
            {'name': 'Synthetic UI011 Hidden', 'company_id': cls.company.id, 'department_id': cls.department.id,
             'job_id': cls.job.id, 'category_ids': [Command.set(cls.category.ids)]},
            {'name': 'Synthetic UI011 Archived', 'company_id': cls.company.id, 'active': False,
             'department_id': cls.department.id, 'job_id': cls.job.id, 'category_ids': [Command.set(cls.category.ids)]},
        ])

    def test_counts_and_drilldowns_apply_record_rules_active_and_company(self):
        self.env['ir.access'].create({'name': 'Synthetic UI011 hide one', 'model_id': self.env['ir.model']._get_id('hr.employee'),
                                      'operation': 'r', 'domain': str([('id', '!=', self.employees[1].id)])})
        for record in (self.department, self.job, self.category):
            scoped = record.with_user(self.officer).with_context(allowed_company_ids=self.company.ids, active_test=False)
            self.assertEqual(scoped.tp_visible_employee_count, 1)
            action = scoped.action_tp_employees()
            actual = self.env['hr.employee'].with_user(self.officer).with_context(**action['context'], allowed_company_ids=self.company.ids).search(action['domain'])
            self.assertEqual(actual, self.employees[:1])
            self.assertEqual(action['views'][0][1], 'list')
        self.assertEqual(self.department.tp_manager_label, 'Chưa khai báo')
        with self.assertRaises(AccessError):
            self.category.with_user(self.staff).read(['tp_visible_employee_count'])

    def test_preserved_actions_menus_and_readonly_profile_action(self):
        for name in ('menu_records', 'menu_group_records'):
            self.assertFalse(self.env.ref('tp_hr_workspace.' + name).active)
        self.assertEqual(self.env.ref('tp_hr_workspace.action_employees').name, 'Danh sách nhân viên')
        self.assertEqual(self.env.ref('tp_hr_workspace.action_categories').name, 'Nhãn nhân viên')
        employee = self.employees[0].with_user(self.officer).with_context(allowed_company_ids=self.company.ids)
        action = employee.action_tp_profile()
        self.assertEqual(action['res_id'], employee.id)
        self.assertEqual(action['views'][0][0], self.env.ref('tp_hr_workspace.employee_form').id)
        with self.assertRaises(AccessError):
            self.employees[0].with_user(self.staff).action_tp_profile()

    def test_import_counts_keep_backend_states(self):
        batch = self.env['tp.hr.import.batch'].with_company(self.company).create({'name': 'Synthetic UI011 Batch'})
        self.env['tp.hr.import.line'].with_context(_tp_import_internal=_INTERNAL).create([
            {'batch_id': batch.id, 'name': 'Synthetic', 'action': action} for action in ('create', 'update', 'skip', 'conflict', 'conflict')
        ])
        self.assertEqual([batch.tp_create_count, batch.tp_update_count, batch.tp_skip_count, batch.tp_conflict_count], [1, 1, 1, 2])
        self.assertEqual([key for key, _label in batch._fields['state'].selection], ['draft', 'preview', 'applied'])

    def test_employee_list_hides_action_column_and_form_hides_versions_timeline_bar(self):
        Employee = self.env['hr.employee'].with_context(allowed_company_ids=self.company.ids)
        list_view = Employee.get_view(self.env.ref('tp_hr_workspace.employee_list').id, view_type='list')
        list_arch = list_view['arch']
        self.assertNotIn('Quản lý tài khoản', list_arch)
        self.assertNotIn('Tạo tài khoản', list_arch)
        self.assertIn('action_tp_complete_profile', list_arch)
        self.assertRegex(list_arch, r'<field[^>]*name="name"[^>]*widget="tp_hr_identity"')

        form_view = Employee.get_view(self.env.ref('tp_hr_workspace.employee_form').id, view_type='form')
        form_arch = form_view['arch']
        self.assertIn('action_open_account_dialog', form_arch)
        self.assertRegex(form_arch, r'<field[^>]*name="version_id"[^>]*widget="versions_timeline"[^>]*invisible="1"|<field[^>]*widget="versions_timeline"[^>]*name="version_id"[^>]*invisible="1"')

    def test_hierarchy_orders_leadership_first_and_filters_department(self):
        board = self.env['hr.department'].create({'name': 'Ban Giám đốc', 'company_id': self.company.id})
        tech = self.env['hr.department'].create({'name': 'Kỹ thuật', 'company_id': self.company.id})
        ceo_job = self.env['hr.job'].create({'name': 'Tổng giám đốc', 'sequence': 20, 'company_id': self.company.id})
        chair_job = self.env['hr.job'].create({'name': 'Chủ tịch', 'sequence': 10, 'company_id': self.company.id})
        lead_job = self.env['hr.job'].create({'name': 'Trưởng phòng', 'sequence': 50, 'company_id': self.company.id})
        staff_job = self.env['hr.job'].create({'name': 'Chuyên viên', 'sequence': 10, 'company_id': self.company.id})
        emps = self.env['hr.employee'].with_company(self.company).create([
            {'name': 'An Nhân Viên', 'company_id': self.company.id, 'department_id': tech.id, 'job_id': staff_job.id},
            {'name': 'Zoe Tổng Giám Đốc', 'company_id': self.company.id, 'department_id': board.id, 'job_id': ceo_job.id},
            {'name': 'Trung Chủ Tịch', 'company_id': self.company.id, 'department_id': board.id, 'job_id': chair_job.id},
            {'name': 'Bình Trưởng Phòng', 'company_id': self.company.id, 'department_id': tech.id, 'job_id': lead_job.id},
        ])
        Employee = self.env['hr.employee'].with_user(self.officer).with_context(allowed_company_ids=self.company.ids, tp_hr_hierarchy=True)
        rows = Employee.hierarchy_read([('id', 'in', emps.ids)], {'id': {}, 'name': {}, 'parent_id': {'fields': {'display_name': {}}}}, 'parent_id', 'child_ids')
        self.assertEqual([r['id'] for r in rows], [emps[2].id, emps[1].id, emps[3].id, emps[0].id])
        tech_rows = Employee.hierarchy_read([('id', 'in', emps.ids), ('department_id', '=', tech.id)], {'id': {}, 'name': {}, 'parent_id': {'fields': {'display_name': {}}}}, 'parent_id', 'child_ids')
        self.assertEqual([r['id'] for r in tech_rows], [emps[3].id, emps[0].id])

    def test_employee_personal_information_tab_is_card_structured_and_vietnamese(self):
        Employee = self.env['hr.employee'].with_user(self.officer).with_context(allowed_company_ids=self.company.ids)
        form_view = Employee.get_view(self.env.ref('tp_hr_workspace.employee_form').id, view_type='form')
        arch = form_view['arch']
        self.assertIn('o_tp_hr_personal_grid', arch)
        for heading in (
            'Liên hệ cá nhân &amp; Ngân hàng',
            'Thông tin nhân thân',
            'Quốc tịch &amp; Giấy tờ tùy thân',
            'Thị thực &amp; Giấy phép lao động',
            'Liên hệ khẩn cấp',
            'Địa chỉ thường trú',
            'Gia đình &amp; Di chuyển',
            'Học vấn &amp; Tài liệu cá nhân',
        ):
            self.assertIn(heading, arch)
        for forbidden in (
            'VISA &amp; WORK PERMIT',
            'Visa &amp; Work Permit',
            'Show Birthday To Employees',
            'Salary Allocation',
            'Untrusted',
            'Issued by Government',
            'Expires on',
        ):
            self.assertNotIn(forbidden, arch)

        finfo = Employee.fields_get([
            'sex', 'birthday_public_display', 'legal_name', 'bank_account_ids',
            'identification_id', 'certificate', 'marital',
        ])
        self.assertEqual(finfo['sex']['string'], 'Giới tính')
        self.assertEqual(dict(finfo['sex']['selection']), {'male': 'Nam', 'female': 'Nữ'})
        self.assertEqual(finfo['birthday_public_display']['string'], 'Hiển thị ngày sinh nội bộ')
        self.assertEqual(finfo['legal_name']['string'], 'Họ tên pháp lý')
        self.assertIn('pháp lý', finfo['legal_name']['help'])
        self.assertEqual(finfo['identification_id']['string'], 'Số CCCD / CMND')
        self.assertEqual(finfo['certificate']['string'], 'Trình độ học vấn')
        self.assertEqual(dict(finfo['certificate']['selection'])['bachelor'], 'Cử nhân / Đại học')
        self.assertEqual(dict(finfo['marital']['selection'])['married'], 'Đã kết hôn')

    def test_new_employee_form_never_asks_for_the_computed_version(self):
        """A new employee has no version yet; a visible required version blocked every create."""
        form = self.env.ref('tp_hr_workspace.employee_form')
        employees = self.env['hr.employee'].with_user(self.officer).with_context(allowed_company_ids=self.company.ids)
        arch = employees.get_views([(form.id, 'form')])['views']['form']['arch']
        nodes = etree.fromstring(arch).xpath("//field[@name='version_id'][not(ancestor::field)]")
        self.assertGreaterEqual(len(nodes), 2)
        for node in nodes:
            self.assertIn(node.get('invisible'), ('1', 'True', 'not id'))
