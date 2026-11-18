from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDelegationBusinessBaseline(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.employee, cls.coworker = cls.env['hr.employee'].create([
            {
                'name': name,
                'company_id': cls.company.id,
                'department_id': cls.department.id,
                'user_id': user_id,
                'date_version': fields.Date.today(),
            }
            for name, user_id in ((cls.user.name, cls.user.id), ('Synthetic HR coworker', False))
        ])

    def grant(self, operation='grant'):
        self.env['tp.admin.delegation'].with_user(self.main)._change(
            self.user, self.company, operation, 'Synthetic baseline preservation',
        )

    def test_preexisting_hr_and_reporting_groups_preserved_across_grant_and_revoke(self):
        before_groups = set(self.user.group_ids.ids)
        self.grant('grant')
        self.employee.with_user(self.user).write({'job_title': 'Updated own dept description'})
        self.coworker.with_user(self.user).write({'job_title': 'Updated coworker description'})
        self.grant('revoke')
        self.assertEqual(set(self.user.group_ids.ids), before_groups)
        self.assertTrue(self.user.has_group('hr.group_hr_user'))
        self.assertTrue(self.user.has_group('tp_reporting.group_reporting_config'))
        self.assertFalse(self.user.has_group('base.group_system'))
