from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFullAdminEquipmentScope(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.main = cls.env.ref('base.user_admin')
        cls.env['tp.admin.delegation']._migrate_admin_full_001()
        cls.departments = cls.env['hr.department'].create([
            {'name': name, 'company_id': cls.company.id}
            for name in ('Synthetic Equip Own', 'Synthetic Equip Other')
        ])
        cls.user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic Equipment Full Admin',
            'login': 'synthetic.equipment.fulladmin',
            'company_id': cls.company.id,
            'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': cls.user.name,
            'company_id': cls.company.id,
            'department_id': cls.departments[0].id,
            'user_id': cls.user.id,
            'date_version': fields.Date.today(),
        })
        cls.other_employee = cls.env['hr.employee'].create({
            'name': 'Synthetic Other Holder',
            'company_id': cls.company.id,
            'department_id': cls.departments[1].id,
            'date_version': fields.Date.today(),
        })
        cls.category = cls.env['maintenance.equipment.category'].create({'name': 'Synthetic Category'})
        cls.equipment = cls.env['maintenance.equipment'].create([
            {
                'name': name,
                'company_id': cls.company.id,
                'category_id': cls.category.id,
                'tp_custody': 'employee',
                'tp_employee_id': emp.id,
                'tp_technical_state': 'good',
            }
            for name, emp in [('Own Dept Machine', cls.employee), ('Other Dept Machine', cls.other_employee)]
        ])
        cls.equipment.action_tp_register()
        cls.stock = cls.env['maintenance.equipment'].create({
            'name': 'Shared Stock Machine',
            'company_id': cls.company.id,
            'category_id': cls.category.id,
        })
        cls.stock.action_tp_register()

    def grant(self, operation='grant'):
        self.env['tp.admin.delegation'].with_user(self.main)._change(
            self.user, self.company, operation, 'Synthetic equipment full admin',
        )

    def test_full_admin_manages_all_equipment_including_own_department_and_stock(self):
        model = self.env['maintenance.equipment'].with_user(self.user)
        with self.assertRaises(AccessError):
            self.equipment[0].with_user(self.user).read(['name'])

        self.grant('grant')
        all_target = self.equipment | self.stock
        self.assertEqual(set(model.search([('id', 'in', all_target.ids)]).ids), set(all_target.ids))
        for rec in all_target:
            self.assertTrue(rec.with_user(self.user).has_access('write'))
        dash = self.env['tp.equipment.dashboard'].with_user(self.user).get_dashboard()
        self.assertFalse(dash.get('delegated_scope'))

        self.grant('revoke')
        with self.assertRaises(AccessError):
            self.equipment[0].with_user(self.user).read(['name'])
