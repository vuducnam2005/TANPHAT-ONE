from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFullAdminBusinessScope(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.admin = cls.env.ref('base.user_admin')
        cls.env['tp.admin.delegation']._migrate_admin_full_001()
        cls.departments = cls.env['hr.department'].create([
            {'name': 'Synthetic FullAdmin KD ' + name, 'company_id': cls.company.id}
            for name in ('Own', 'Other')
        ])
        cls.user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic KD Staff To Admin',
            'login': 'fulladmin.business.synthetic',
            'company_id': cls.company.id,
            'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref('tp_kd_workspace.group_scoped_staff').id])],
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': cls.user.name,
            'user_id': cls.user.id,
            'company_id': cls.company.id,
            'department_id': cls.departments[0].id,
        })
        cls.projects = cls.env['project.project'].create([
            {
                'name': f'Synthetic Project {i}',
                'tp_code': f'FA-SYNTH-{i}',
                'tp_managed': True,
                'company_id': cls.company.id,
                'tp_department_id': dept.id,
            }
            for i, dept in enumerate([cls.departments[0], cls.departments[0], cls.departments[1]])
        ])
        cls.env['tp.project.assignment'].create({
            'project_id': cls.projects[0].id,
            'user_id': cls.user.id,
            'role': 'reader',
        })

    def change(self, operation='grant'):
        self.env['tp.admin.delegation'].with_user(self.admin)._change(
            self.user, self.company, operation, 'Synthetic full admin KH-KD check',
        )

    def test_old_scoped_staff_role_never_blocks_full_admin_and_resumes_on_revoke(self):
        projects = self.env['project.project'].with_user(self.user).with_context(allowed_company_ids=self.company.ids)
        before_ids = set(projects.search([('id', 'in', self.projects.ids)]).ids)
        self.assertEqual(before_ids, {self.projects[0].id})

        self.change('grant')
        # Granted Full Admin sees and writes ALL projects across own and other departments!
        self.assertFalse(self.env['crm.lead'].with_user(self.user)._kd_scoped())
        after_ids = set(projects.search([('id', 'in', self.projects.ids)]).ids)
        self.assertEqual(after_ids, set(self.projects.ids))
        for proj in self.projects:
            self.assertTrue(proj.with_user(self.user).has_access('write'))

        self.change('revoke')
        self.assertTrue(self.env['crm.lead'].with_user(self.user)._kd_scoped())
        revoked_ids = set(projects.search([('id', 'in', self.projects.ids)]).ids)
        self.assertEqual(revoked_ids, before_ids)
