"""HR-UNIFIED-READONLY-UI-001: unified read-only HR workspace, custom ordering, overview, and 3-tab colleague protection."""
import json
import os
import subprocess
from pathlib import Path

from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError, RedirectWarning, ValidationError
from odoo.tests import HttpCase, TransactionCase, tagged

# Private HR, contract, account and history data that must never reach the shared directory.
PRIVATE_FIELDS = (
    'private_phone', 'private_email', 'private_street', 'private_city', 'birthday', 'place_of_birth',
    'identification_id', 'passport_id', 'ssnid', 'sinid', 'bank_account_id', 'emergency_contact',
    'emergency_phone', 'spouse_complete_name', 'children', 'wage', 'contract_id',
    'private_car_plate', 'permit_no', 'visa_no',
    'tp_employment_kind', 'tp_contract_document_id', 'tp_contract_document_ids',
    'tp_user_login', 'tp_account_status', 'tp_business_role', 'tp_role_scope', 'tp_extra_access',
)
# Explicit whitelist of public fields rendered by unified read-only directory views.
DIRECTORY_FIELDS = {
    'sequence', 'tp_employee_code', 'avatar_128', 'avatar_256', 'image_1920', 'name', 'department_id',
    'job_id', 'job_title', 'parent_id', 'coach_id', 'child_ids', 'work_email', 'work_phone',
    'work_location_id', 'address_id', 'company_id', 'birthday_public_display_string',
    'is_user',
}
FORBIDDEN_TAB_NAMES = {'tp_contract', 'tp_history', 'page_account', 'personal_information', 'tp_equipment'}
FORBIDDEN_TAB_LABELS = ('Hợp đồng lao động', 'Lịch sử hoạt động', 'Tài khoản và phân quyền')


@tagged('post_install', '-at_install')
class TestDirectoryReadonly(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        employee_model = cls.env['hr.employee']
        employee_model._tp_reset_code_sequence(employee_model._tp_code_floor())

        cls.company = cls.env['res.company'].create({'name': 'Synthetic Directory Company'})
        cls.other_company = cls.env['res.company'].create({'name': 'Synthetic Directory Other'})
        cls.dept_x, cls.dept_y = cls.env['hr.department'].create([
            {'name': 'Synthetic Directory X', 'company_id': cls.company.id, 'tp_sequence': 20},
            {'name': 'Synthetic Directory Y', 'company_id': cls.company.id, 'tp_sequence': 10},
        ])
        cls.other_dept = cls.env['hr.department'].create({
            'name': 'Synthetic Outside Dept', 'company_id': cls.other_company.id,
        })
        cls.job_dev, cls.job_lead = cls.env['hr.job'].create([
            {'name': 'Synthetic Kỹ sư', 'company_id': cls.company.id},
            {'name': 'Synthetic Trưởng nhóm', 'company_id': cls.company.id},
        ])

        def user(login, *groups):
            return cls.env['res.users'].create({
                'name': login, 'login': login,
                'company_id': cls.company.id, 'company_ids': [Command.set([cls.company.id])],
                'group_ids': [Command.set([cls.env.ref(group).id for group in groups])],
            })

        cls.viewer_a = user('dir001.synthetic.a', 'base.group_user')
        cls.viewer_b = user('dir001.synthetic.b', 'base.group_user')
        cls.kd_head = user('dir001.synthetic.kdhead', 'tp_kd_workspace.group_scoped_staff')
        cls.hr = user('dir001.synthetic.hr', 'hr.group_hr_user', 'base.group_allow_export')

        cls.emp_a, cls.emp_b, cls.emp_c = cls.env['hr.employee'].with_company(cls.company).create([
            {
                'name': 'Synthetic Directory A', 'company_id': cls.company.id,
                'department_id': cls.dept_x.id, 'job_id': cls.job_dev.id,
                'user_id': cls.viewer_a.id, 'work_email': 'a.synthetic@example.invalid',
                'private_phone': '0900000001', 'identification_id': 'SYN-PRIVATE-A',
            },
            {
                'name': 'Synthetic Directory B', 'company_id': cls.company.id,
                'department_id': cls.dept_y.id, 'job_id': cls.job_lead.id,
                'user_id': cls.viewer_b.id, 'work_email': 'b.synthetic@example.invalid',
                'private_phone': '0900000002', 'identification_id': 'SYN-PRIVATE-B',
            },
            {
                'name': 'Synthetic Directory C', 'company_id': cls.company.id,
                'department_id': cls.dept_y.id, 'job_id': cls.job_dev.id,
                'user_id': cls.kd_head.id, 'work_email': 'c.synthetic@example.invalid',
                'private_phone': '0900000003', 'identification_id': 'SYN-PRIVATE-C',
            },
        ])
        cls.emp_archived = cls.env['hr.employee'].with_company(cls.company).create({
            'name': 'Synthetic Directory Archived', 'company_id': cls.company.id,
            'department_id': cls.dept_x.id, 'active': False,
        })
        cls.emp_outside = cls.env['hr.employee'].with_company(cls.other_company).create({
            'name': 'Synthetic Outside Secret', 'company_id': cls.other_company.id,
            'department_id': cls.other_dept.id,
        })
        # Make kd_head a real KH-KD department head to verify headship never grants HR admin rights.
        cls.env['crm.team'].create({
            'name': 'Synthetic KD Team', 'company_id': cls.company.id, 'kd_department_id': cls.dept_y.id,
        })
        cls.env['tp.kd.department.role'].create({
            'user_id': cls.kd_head.id, 'company_id': cls.company.id,
            'department_id': cls.dept_y.id, 'reason': 'Synthetic KD head test',
        })


    def model(self, user, name):
        return self.env[name].with_user(user).with_context(allowed_company_ids=[self.company.id])

    def test_viewer_sees_whole_company_through_unified_whitelist_views(self):
        public = self.model(self.viewer_a, 'hr.employee.public')
        found = public.search([('company_id', '=', self.company.id)])
        self.assertEqual(set(found.ids), {self.emp_a.id, self.emp_b.id, self.emp_c.id})
        colleague = public.browse(self.emp_b.id)
        self.assertEqual(colleague.work_email, 'b.synthetic@example.invalid')
        self.assertEqual(colleague.department_id, self.dept_y)
        self.assertEqual(colleague.job_id, self.job_lead)

        employee_fields = self.env['hr.employee']._fields
        for fname in PRIVATE_FIELDS:
            if fname in employee_fields:
                self.assertNotIn(fname, public._fields, f'{fname} leaked into hr.employee.public')

        for xmlid, view_type in (('directory_list', 'list'), ('directory_kanban', 'kanban'), ('directory_form', 'form')):
            view = self.env.ref(f'tp_hr_workspace.{xmlid}')
            result = public.get_views([(view.id, view_type)])
            arch_str = result['views'][view_type]['arch']
            arch = etree.fromstring(arch_str)
            names = {node.get('name') for node in arch.iter('field')}
            self.assertLessEqual(names, DIRECTORY_FIELDS, xmlid)
            if view_type == 'list':
                self.assertEqual(arch.get('js_class'), 'tp_hr_table')
                self.assertEqual(arch.get('default_order'), 'sequence, id')
                self.assertEqual(arch.get('expand'), '1')
                self.assertEqual(arch.get('create'), '0')
                self.assertEqual(arch.get('edit'), '0')
                self.assertEqual(arch.get('delete'), '0')
                self.assertEqual(arch.get('import'), '0')
                self.assertEqual(arch.get('export_xlsx'), '0')
                self.assertRegex(arch_str, r'<field[^>]*name="name"[^>]*widget="tp_hr_identity"')
            elif view_type == 'form':
                self.assertEqual(arch.get('js_class'), 'tp_hr_profile')
                self.assertIn('o_tp_hr_employee_form', arch.get('class', ''))
                self.assertEqual(arch.get('create'), '0')
                self.assertEqual(arch.get('edit'), '0')
                self.assertEqual(arch.get('delete'), '0')
                self.assertEqual(arch.get('duplicate'), '0')
                pages = {p.get('name') for p in arch.xpath('//page')}
                self.assertFalse(pages & FORBIDDEN_TAB_NAMES)
                self.assertEqual(pages, {'page_overview', 'work_information'})
                for label in FORBIDDEN_TAB_LABELS:
                    self.assertNotIn(label, arch_str)
                self.assertNotIn('<chatter', arch_str)

    def test_custom_department_and_employee_order_parity(self):
        # Reorder employees inside dept_y as HR (put emp_c before emp_b)
        hr_emp = self.model(self.hr, 'hr.employee')
        hr_emp.tp_reorder_in_department(self.emp_c.id, self.dept_y.id, before_id=self.emp_b.id)
        self.env.flush_all()

        # Verify dept_y (tp_sequence=10) precedes dept_x (tp_sequence=20), and emp_c precedes emp_b for viewer
        public = self.model(self.viewer_a, 'hr.employee.public')
        groups = public._read_group(
            [('company_id', '=', self.company.id), ('active', '=', True)],
            ['department_id'],
            ['__count'],
            order='department_id',
        )
        dept_order = [dept.id for dept, _cnt in groups]
        self.assertEqual(dept_order, [self.dept_y.id, self.dept_x.id])

        dept_y_members = public.search([('company_id', '=', self.company.id), ('department_id', '=', self.dept_y.id)])
        admin_members = hr_emp.search([('company_id', '=', self.company.id), ('department_id', '=', self.dept_y.id)])
        self.assertEqual(dept_y_members.ids, [self.emp_c.id, self.emp_b.id])
        self.assertEqual(dept_y_members.ids, admin_members.ids)

        # Normal employee & KD head cannot reorder employees or departments
        for actor in (self.viewer_a, self.kd_head):
            with self.assertRaises(AccessError):
                self.model(actor, 'hr.employee').tp_reorder_in_department(
                    self.emp_b.id, self.dept_y.id, before_id=self.emp_c.id,
                )
            with self.assertRaises(AccessError):
                self.model(actor, 'hr.department').browse(self.dept_y.id).write({'tp_sequence': 99})

    def test_search_identity_code_and_name_without_private_probing(self):
        public = self.model(self.viewer_a, 'hr.employee.public')
        by_code = public.search([
            ('company_id', '=', self.company.id),
            ('tp_search_identity', 'ilike', self.emp_b.tp_employee_code),
        ])
        self.assertEqual(by_code.ids, [self.emp_b.id])
        by_name = public.search([
            ('company_id', '=', self.company.id),
            ('tp_search_identity', 'ilike', 'Directory C'),
        ])
        self.assertEqual(by_name.ids, [self.emp_c.id])

        # Direct probing of private/account/contract fields must be blocked
        employees = self.model(self.viewer_a, 'hr.employee')
        for forbidden_field in (
            'private_phone', 'identification_id', 'birthday', 'tp_employment_kind',
            'tp_user_login', 'tp_account_status', 'tp_business_role', 'tp_role_scope',
            'tp_can_change_login', 'tp_contract_document_id',
        ):
            with self.assertRaises(AccessError, msg=f'Field {forbidden_field} should be blocked'):
                employees.browse(self.emp_b.id).read([forbidden_field])
        with self.assertRaises(AccessError):
            employees.search([('tp_user_login', 'ilike', 'dir001')])

    def test_three_hidden_tabs_backend_protection_and_own_profile_id_check(self):
        doc = self.env['tp.hr.contract.document'].with_user(self.hr).with_context(
            allowed_company_ids=[self.company.id],
        ).create({
            'name': 'Synthetic Confidential Contract', 'employee_id': self.emp_b.id, 'kind': 'labor',
        })
        msg = self.emp_b.message_post(body='Synthetic Confidential Colleague History')
        att = self.env['ir.attachment'].create({
            'name': 'Synthetic Colleague Attachment', 'raw': b'CONFIDENTIAL',
            'res_model': 'hr.employee', 'res_id': self.emp_b.id,
        })

        for actor in (self.viewer_a, self.kd_head):
            # 1. Contract tab backend blocked
            with self.assertRaises(AccessError):
                self.model(actor, 'tp.hr.contract.document').browse(doc.id).read(['name'])
            with self.assertRaises(AccessError):
                self.model(actor, 'hr.version').search([('employee_id', '=', self.emp_b.id)])
            with self.assertRaises(AccessError):
                self.model(actor, 'hr.employee').browse(self.emp_b.id).action_tp_contract_documents()
            # 2. Activity history / chatter & attachment blocked
            with self.assertRaises(AccessError):
                self.model(actor, 'mail.message').browse(msg.id).read(['body'])
            with self.assertRaises(AccessError):
                self.model(actor, 'ir.attachment').browse(att.id).read(['raw'])
            # 3. Account & permissions tab backend blocked
            with self.assertRaises(AccessError):
                self.model(actor, 'tp.hr.account.wizard').create({'employee_id': self.emp_b.id})
            with self.assertRaises(AccessError):
                self.model(actor, 'tp.hr.role.wizard').create({'employee_id': self.emp_b.id, 'reason': 'No'})
            with self.assertRaises(AccessError):
                self.model(actor, 'tp.hr.employee.audit').search([])
            with self.assertRaises(AccessError):
                self.model(actor, 'hr.employee').browse(self.emp_b.id).action_open_account_dialog()
            with self.assertRaises(AccessError):
                self.model(actor, 'hr.employee').browse(self.emp_b.id).action_open_change_login_dialog()
            # Direct hr.employee get_views redirects safely to action_directory
            with self.assertRaises(RedirectWarning) as ctx:
                self.model(actor, 'hr.employee').get_views([(False, 'form')])
            self.assertEqual(ctx.exception.args[1], self.env.ref('tp_hr_workspace.action_directory').id)

        # Own profile detection uses real linked ID/user_id, NEVER name comparison
        same_name_colleague = self.env['hr.employee'].with_company(self.company).create({
            'name': self.emp_a.name, 'company_id': self.company.id, 'department_id': self.dept_x.id,
        })
        pub_a = self.model(self.viewer_a, 'hr.employee.public')
        self.assertTrue(pub_a.browse(self.emp_a.id).is_user)
        self.assertFalse(pub_a.browse(same_name_colleague.id).is_user)
        self.assertFalse(pub_a.browse(self.emp_b.id).is_user)
        own_action = pub_a.browse(self.emp_a.id).action_tp_open_my_profile()
        self.assertEqual(own_action['tag'], 'tp_hr_workspace.my_profile')
        with self.assertRaises(AccessError):
            pub_a.browse(same_name_colleague.id).action_tp_open_my_profile()
        with self.assertRaises(AccessError):
            pub_a.browse(self.emp_b.id).action_tp_open_my_profile()

        # Self-service My Profile still works for viewer_a
        profile = self.model(self.viewer_a, 'res.users').tp_get_my_profile()
        self.assertTrue(profile['has_employee'])
        self.assertEqual(profile['header']['id'], self.emp_a.id)

    def test_public_overview_and_drilldown_strictly_scoped(self):
        for actor in (self.viewer_a, self.kd_head):
            ws = self.model(actor, 'tp.hr.workspace')
            overview = ws.get_public_overview()
            self.assertTrue(overview['readonly'])
            self.assertFalse(overview['can_create'])
            self.assertFalse(overview['can_export'])
            self.assertEqual(overview['total'], 3)
            self.assertEqual(overview['units'], 2)
            # Custom department order respected: dept_y (10) then dept_x (20)
            self.assertEqual([d['id'] for d in overview['departments']], [self.dept_y.id, self.dept_x.id])
            # Zero HR/account/missing/contract stats leaked
            for forbidden_key in (
                'linked', 'pending', 'locked', 'missing_basic', 'complete_basic',
                'missing_code', 'missing_department', 'missing_job', 'missing_contact', 'employee_form_id',
            ):
                self.assertNotIn(forbidden_key, overview)
            # Filtered overview matches exact count
            filtered = ws.get_public_overview({'department_id': self.dept_y.id})
            self.assertEqual(filtered['total'], 2)
            # Invalid/forbidden filter keys and cross-company departments rejected
            for bad in ({'status': 'archived'}, {'employment_kind': 'long_term'}, {'missing_basic': True}):
                with self.assertRaises(ValidationError):
                    ws.get_public_overview(bad)
            with self.assertRaises(AccessError):
                ws.get_public_overview({'department_id': self.other_dept.id})
            # Drilldown action opens action_directory on hr.employee.public
            action = ws.action_public_employees({'department_id': self.dept_y.id}, [['job_id', '=', self.job_lead.id]])
            self.assertEqual(action['res_model'], 'hr.employee.public')
            self.assertEqual(action['id'], self.env.ref('tp_hr_workspace.action_directory').id)
            with self.assertRaises(ValidationError):
                ws.action_public_employees({}, [['user_id', '!=', False]])
            with self.assertRaises(ValidationError):
                ws.action_public_employees({}, [['tp_account_status', '=', 'disabled']])
            # Admin overview & export stay strictly denied
            with self.assertRaises(AccessError):
                ws.get_overview()
            with self.assertRaises(AccessError):
                ws._build_xlsx()

    def test_viewer_cannot_change_or_export(self):
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
        with self.assertRaises(AccessError):
            employees.browse(self.emp_a.id).copy()
        before = self.env['hr.employee'].search_count([('company_id', '=', self.company.id)])
        result = public.load(['name'], [['Synthetic loaded']])
        self.assertFalse(result.get('ids'))
        self.assertEqual(self.env['hr.employee'].search_count([('company_id', '=', self.company.id)]), before)
        with self.assertRaises(AccessError):
            public.browse(self.emp_b.id).export_data(['name', 'work_email'])
        exported = self.model(self.hr, 'hr.employee.public').browse(self.emp_b.id).export_data(['name'])
        self.assertEqual(exported['datas'], [['Synthetic Directory B']])

    def test_entry_and_menus_follow_real_groups(self):
        entry = self.env.ref('tp_hr_workspace.action_hr_entry')
        for actor in (self.viewer_a, self.kd_head):
            viewer_action = entry.with_user(actor).run()
            self.assertEqual(viewer_action['id'], self.env.ref('tp_hr_workspace.action_public_overview').id)
            self.assertFalse(actor.has_group('hr.group_hr_user'))
        hr_action = entry.with_user(self.hr).run()
        self.assertEqual(hr_action['id'], self.env.ref('tp_hr_workspace.action_overview').id)

        self.assertEqual(self.env.ref('tp_hr_workspace.action_directory').name, 'Danh sách nhân viên')
        self.assertEqual(self.env.ref('tp_hr_workspace.menu_directory').name, 'Danh sách nhân viên')
        self.assertEqual(self.env.ref('tp_hr_workspace.menu_public_overview').name, 'Tổng quan')

        def visible(user):
            return self.env['ir.ui.menu'].with_user(user)._visible_menu_ids()

        def ids(*xmlids):
            return {self.env.ref(f'tp_hr_workspace.{xmlid}').id for xmlid in xmlids}

        viewer_menus = visible(self.viewer_a)
        self.assertLessEqual(ids('menu_hr', 'menu_public_overview', 'menu_directory'), viewer_menus)
        self.assertFalse(
            ids('menu_overview', 'menu_employees', 'menu_missing', 'menu_archived',
                'menu_import', 'menu_group_organization', 'menu_group_config', 'menu_employee_audit') & viewer_menus,
        )
        hr_menus = visible(self.hr)
        self.assertLessEqual(ids('menu_hr', 'menu_overview', 'menu_employees'), hr_menus)
        self.assertFalse(ids('menu_directory', 'menu_public_overview') & hr_menus)

    def test_hr_keeps_management_rights(self):
        employees = self.model(self.hr, 'hr.employee')
        self.assertTrue(employees.has_access('read'))
        self.assertTrue(employees.has_access('write'))
        self.assertEqual(employees.browse(self.emp_b.id).identification_id, 'SYN-PRIVATE-B')

    def test_hr_config_menu_only_contains_categories(self):
        self.assertFalse(self.env.ref('tp_hr_workspace.menu_skill_types', raise_if_not_found=False))
        self.assertFalse(self.env.ref('tp_hr_workspace.menu_resume_types', raise_if_not_found=False))
        categories_menu = self.env.ref('tp_hr_workspace.menu_categories', raise_if_not_found=False)
        self.assertTrue(categories_menu)
        self.assertEqual(categories_menu.parent_id, self.env.ref('tp_hr_workspace.menu_group_config'))


@tagged('post_install', '-at_install', 'tp_unified_readonly_browser')
class TestUnifiedReadonlyBrowserHttp(HttpCase):
    def test_browser_admin_vs_employee_parity_and_hidden_tabs_desktop_mobile(self):
        employee_model = self.env['hr.employee']

        def _reset_seq():
            self.env['hr.employee']._tp_reset_code_sequence(self.env['hr.employee']._tp_code_floor())

        self.addCleanup(_reset_seq)
        employee_model._tp_reset_code_sequence(employee_model._tp_code_floor())

        dept_first, dept_second = self.env['hr.department'].create([
            {'name': 'Synthetic Phòng Ưu Tiên 1', 'company_id': self.env.company.id, 'tp_sequence': 1},
            {'name': 'Synthetic Phòng Ưu Tiên 2', 'company_id': self.env.company.id, 'tp_sequence': 2},
        ])
        job_a, job_b = self.env['hr.job'].create([
            {'name': 'Synthetic Kỹ sư cầu đường', 'company_id': self.env.company.id},
            {'name': 'Synthetic Chuyên viên dự án', 'company_id': self.env.company.id},
        ])
        staff_user, colleague_user = self.env['res.users'].with_context(no_reset_password=True).create([
            {
                'name': 'Synthetic Nhân Viên Xem', 'login': 'synthetic.unified.viewer',
                'password': 'synthetic',
                'company_id': self.env.company.id, 'company_ids': [Command.set(self.env.company.ids)],
                'group_ids': [Command.set(self.env.ref('base.group_user').ids)],
            },
            {
                'name': 'Synthetic Đồng Nghiệp B', 'login': 'synthetic.unified.colleague',
                'password': 'synthetic',
                'company_id': self.env.company.id, 'company_ids': [Command.set(self.env.company.ids)],
                'group_ids': [Command.set(self.env.ref('base.group_user').ids)],
            },
        ])
        emp_self, emp_colleague, _emp_colleague2 = self.env['hr.employee'].create([
            {
                'name': 'Synthetic Nhân Viên Xem', 'user_id': staff_user.id,
                'department_id': dept_first.id, 'job_id': job_a.id,
                'work_email': 'viewer.synthetic@example.invalid', 'work_phone': '0243000111',
            },
            {
                'name': 'Synthetic Đồng Nghiệp B', 'user_id': colleague_user.id,
                'department_id': dept_first.id, 'job_id': job_b.id,
                'work_email': 'colleague.synthetic@example.invalid', 'work_phone': '0243000222',
                'identification_id': 'SYN-SECRET-CCCD-999',
            },
            {
                'name': 'Synthetic Đồng Nghiệp C',
                'department_id': dept_second.id, 'job_id': job_a.id,
                'work_email': 'colleague2.synthetic@example.invalid',
            },
        ])
        # Put emp_colleague BEFORE emp_self inside dept_first via real reorder action
        self.env['hr.employee'].tp_reorder_in_department(emp_colleague.id, dept_first.id, before_id=emp_self.id)
        # Attach confidential contract & chatter history to emp_colleague
        self.env['tp.hr.contract.document'].create({
            'name': 'SYN-SECRET-CONTRACT-DOC', 'number': 'HD-SYN-999',
            'employee_id': emp_colleague.id, 'kind': 'labor',
        })
        emp_colleague.message_post(body='SYN-SECRET-HISTORY-NOTE')
        self.env.flush_all()

        root = Path(__file__).resolve().parents[3]
        while not (root / 'scripts/tests/test_hr_unified_readonly_ui.cjs').is_file():
            if root == root.parent:
                self.fail('Cannot locate scripts/tests/test_hr_unified_readonly_ui.cjs')
            root = root.parent
        output = root / '.local/hr-unified-readonly001/browser'
        output.mkdir(parents=True, exist_ok=True)
        fixture_path = output / 'fixture-private.json'
        admin = self.env.ref('base.user_admin')

        for role, login, pwd in (('admin', 'admin', 'admin'), ('employee', staff_user.login, 'synthetic')):
            self.authenticate(login, pwd, session_extra={'context': {'lang': 'vi_VN'}})
            try:
                with self.allow_requests():
                    fixture_path.write_text(json.dumps({
                        'base': self.base_url(),
                        'role': role,
                        'selfEmployeeId': emp_self.id,
                        'colleagueId': emp_colleague.id,
                        'colleagueCode': emp_colleague.tp_employee_code,
                        'colleagueName': emp_colleague.name,
                        'selfName': emp_self.name,
                        'deptFirstName': dept_first.name,
                        'deptSecondName': dept_second.name,
                        'orderedFirstDeptIds': [emp_colleague.id, emp_self.id],
                        'output': str(output),
                        'cookies': [
                            {'name': 'session_id', 'value': self.session.sid, 'url': self.base_url(), 'httpOnly': True},
                            {'name': 'test_request_key', 'value': self.http_request_key, 'url': self.base_url()},
                        ],
                    }), encoding='utf-8')
                    result = subprocess.run(
                        ['node', str(root / 'scripts/tests/test_hr_unified_readonly_ui.cjs')],
                        env={**os.environ, 'TP_HR_UNIFIED_FIXTURE': str(fixture_path)},
                        capture_output=True, text=True, timeout=240, check=False,
                    )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            finally:
                fixture_path.unlink(missing_ok=True)
