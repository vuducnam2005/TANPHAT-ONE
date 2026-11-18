from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFullAdminReportingScope(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.main = cls.env.ref('base.user_admin')
        cls.env['tp.admin.delegation']._migrate_admin_full_001()
        cls.department = cls.env['hr.department'].create({
            'name': 'Synthetic Reporting Dept',
            'company_id': cls.company.id,
        })
        cls.actor, cls.coworker = cls.env['res.users'].with_context(no_reset_password=True).create([
            {
                'name': f'Synthetic Report Actor {idx}',
                'login': f'synthetic.report.fulladmin.{idx}',
                'company_id': cls.company.id,
                'company_ids': [Command.set(cls.company.ids)],
                'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
            }
            for idx in range(2)
        ])

    def change(self, operation='grant'):
        self.env['tp.admin.delegation'].with_user(self.main)._change(
            self.actor, self.company, operation, 'Synthetic reporting full admin',
        )

    def test_full_admin_receives_reporting_config_like_current_admin_and_keeps_self_grant_guard(self):
        self.assertFalse(self.actor.has_group('tp_reporting.group_reporting_config'))
        self.change('grant')
        self.assertTrue(self.actor.has_group('tp_reporting.group_reporting_config'))
        self.assertTrue(self.actor.has_group('tp_reporting.group_reporting_user'))
        dash = self.env['tp.report.dashboard'].with_user(self.actor).get_data('2026-10-01', '2026-12-31', 'quarter')
        self.assertFalse(dash.get('delegated_scope'))

        # Can assign reporting responsibility to another user, but self-grant remains blocked like main admin.
        assigned = self.env['tp.report.assignment'].with_user(self.actor).create({
            'name': 'Synthetic coworker reporting read',
            'user_id': self.coworker.id,
            'capability': 'read',
            'company_id': self.company.id,
            'department_id': self.department.id,
            'reason': 'Assigned by full admin',
        })
        self.assertTrue(assigned.exists())
        with self.assertRaises(AccessError):
            self.env['tp.report.assignment'].with_user(self.actor).create({
                'name': 'Self reporting assignment',
                'user_id': self.actor.id,
                'capability': 'review',
                'company_id': self.company.id,
                'reason': 'Blocked self-grant',
            })

        self.change('revoke')
        self.assertFalse(self.actor.has_group('tp_reporting.group_reporting_config'))
