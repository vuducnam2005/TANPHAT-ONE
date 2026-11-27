from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

from .test_delegation import pick_free_employee_codes


@tagged('post_install', '-at_install')
class TestDelegationBusinessBaseline(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        employee_model = cls.env['hr.employee']
        sequence = employee_model._tp_code_sequence()
        cls.env.cr.execute('SELECT last_value, is_called FROM ir_sequence_%03d' % sequence.id)
        cls.addClassCleanup(cls._restore_employee_sequence, sequence.id, *cls.env.cr.fetchone())
        cls.company = cls.env.company
        cls.main = cls.env.ref('base.user_admin')
        cls.env['tp.admin.delegation']._migrate_admin_full_001()
        cls.department = cls.env['hr.department'].create({
            'name': 'Synthetic HR baseline', 'company_id': cls.company.id,
        })
        cls.user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic preexisting HR officer',
            'login': 'synthetic.delegate.hr.baseline',
            'company_id': cls.company.id,
            'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref(xmlid).id for xmlid in (
                'base.group_user', 'hr.group_hr_user', 'tp_reporting.group_reporting_config',
            )])],
        })
        free_codes = pick_free_employee_codes(cls.env, 2)
        cls.employee, cls.coworker = cls.env['hr.employee'].create([
            {
                'name': name,
                'company_id': cls.company.id,
                'department_id': cls.department.id,
                'user_id': user_id,
                'tp_employee_code': code,
                'date_version': fields.Date.today(),
            }
            for (name, user_id), code in zip(
                ((cls.user.name, cls.user.id), ('Synthetic HR coworker', False)),
                free_codes,
            )
        ])

    @classmethod
    def _restore_employee_sequence(cls, sequence_id, last_value, is_called):
        with cls.registry.cursor() as cr:
            cr.execute('SELECT setval(%s, %s, %s)', ['ir_sequence_%03d' % sequence_id, last_value, is_called])

    def grant(self, operation='grant'):
        self.env['tp.admin.delegation'].with_user(self.main)._change(
            self.user, self.company, operation, 'Synthetic baseline preservation',
        )

    def test_preexisting_hr_and_reporting_groups_preserved_across_grant_and_revoke(self):
        before_groups = set(self.user.group_ids.ids)
        self.grant('grant')
        with self.assertRaises(AccessError):
            self.employee.with_user(self.user).write({'job_title': 'Forbidden self appointment'})
        self.coworker.with_user(self.user).write({'job_title': 'Updated coworker description'})
        self.grant('revoke')
        self.assertEqual(set(self.user.group_ids.ids), before_groups)
        self.assertTrue(self.user.has_group('hr.group_hr_user'))
        self.assertTrue(self.user.has_group('tp_reporting.group_reporting_config'))
        self.assertFalse(self.user.has_group('base.group_system'))
        self.employee.with_user(self.user).write({'job_title': 'Updated after revoke HR description'})
