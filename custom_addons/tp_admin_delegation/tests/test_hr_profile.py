from unittest.mock import patch

from lxml import etree

from odoo.exceptions import AccessError
from odoo.tests import tagged

from .test_delegation import DelegationCase


@tagged('post_install', '-at_install')
class TestFullAdminHrAndNormalPrivacy(DelegationCase):

    def test_granted_full_admin_gets_native_hr_views_all_departments_and_mobile_phone(self):
        self.employees[0].mobile_phone = '0901112222'
        self.employees[1].mobile_phone = '0903334444'
        self.grant(self.users[0])

        hr_emp = self.env['hr.employee'].with_user(self.users[0])
        specs = [(self.env.ref('tp_hr_workspace.employee_' + kind).id, kind) for kind in ('list', 'form', 'search')]
        gv = hr_emp.get_views(specs)
        visible_fields = gv['models']['hr.employee']['fields']
        self.assertIn('mobile_phone', visible_fields)
        self.assertIn('private_email', visible_fields)
        for kind, view in gv['views'].items():
            self.assertEqual(view['id'], self.env.ref('tp_hr_workspace.employee_' + kind).id)

        # Full admin sees and edits employees in BOTH own department and other departments!
        found = hr_emp.search([('id', 'in', self.employees.ids)])
        self.assertEqual(set(found.ids), set(self.employees.ids))

        overview = self.env['tp.hr.workspace'].with_user(self.users[0]).get_overview()
        self.assertTrue(overview['can_create'])
        self.assertFalse(overview.get('delegated_scope'))
        dept_ids = {row['id'] for row in overview['catalog_departments']}
        self.assertIn(self.departments[0].id, dept_ids)
        self.assertIn(self.departments[1].id, dept_ids)

        # Full admin manages normal accounts even in their own department!
        coworker_same_dept = self.env['hr.employee'].with_user(self.users[0]).create({
            'name': 'Synthetic Same Dept Coworker',
            'company_id': self.company.id,
            'department_id': self.departments[0].id,
            'mobile_phone': '0919888777',
        })
        self.assertTrue(coworker_same_dept.tp_can_manage_account)
        wizard = self.env['tp.hr.account.wizard'].with_user(self.users[0]).create({
            'employee_id': coworker_same_dept.id,
            'expected_user_id': False,
            'new_user_login': 'synthetic.same.dept.coworker',
        })
        with patch.object(type(wizard), '_require_recent_identity', return_value=None):
            wizard.action_create_user(password='Synthetic-Pass-2026!', confirmation='Synthetic-Pass-2026!')
        self.assertTrue(coworker_same_dept.user_id)
        self.assertFalse(coworker_same_dept.user_id.has_group('base.group_system'))

    def test_normal_employee_mobile_phone_patch_and_self_profile_preserved(self):
        normal = self.users[1]
        other_emp = self.employees[0]
        other_emp.mobile_phone = '0912345678'

        # Public directory views have 0 missing metadata fields and hide mobile_phone
        pub = self.env['hr.employee.public'].with_user(normal)
        pub_action = self.env.ref('tp_hr_workspace.action_directory').sudo()
        pub_views = pub.get_views([(v.view_id.id, v.view_mode) for v in pub_action.view_ids])
        pub_fields = pub_views['models']['hr.employee.public']['fields']
        self.assertNotIn('mobile_phone', pub_fields)
        for v in pub_views['views'].values():
            xml_fields = set(etree.fromstring(v['arch']).xpath('//field/@name'))
            self.assertFalse(xml_fields - set(pub_fields))

        # Non-HR user cannot read/write mobile_phone of another employee even via sudo/default context
        with self.assertRaises(AccessError):
            other_emp.with_user(normal).read(['mobile_phone'])
        with self.assertRaises(AccessError):
            other_emp.with_user(normal).sudo().write({'mobile_phone': '0000000000'})
        with self.assertRaises(AccessError):
            self.env['hr.employee'].with_user(normal).sudo().with_context(default_mobile_phone='0000000000').create({
                'name': 'Blocked Default Mobile',
                'company_id': self.company.id,
                'department_id': self.departments[1].id,
            })

        # Self-profile mobile_phone remains editable by the owner
        saved = self.env['res.users'].with_user(normal).tp_save_my_profile({'mobile_phone': '0988777666'})
        self.assertEqual(saved['values']['mobile_phone'], '0988777666')
