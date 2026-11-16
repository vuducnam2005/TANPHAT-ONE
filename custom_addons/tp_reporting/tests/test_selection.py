from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'corp_report001')
class TestReportingPeople(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.departments = cls.env['hr.department'].create([
            {'name': 'Picker fake A', 'company_id': cls.company.id},
            {'name': 'Picker fake B', 'company_id': cls.company.id},
        ])
        group = cls.env.ref('tp_reporting.group_reporting_user')
        cls.employee, cls.manager, cls.outside = cls.env['res.users'].create([{
            'name': 'Picker fake ' + role, 'login': 'selection-' + role,
            'company_id': cls.company.id, 'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set(group.ids)],
        } for role in ('employee', 'manager', 'outside')])
        for user, department in [(cls.employee, cls.departments[0]), (cls.manager, cls.departments[0]), (cls.outside, cls.departments[1])]:
            cls.env['hr.employee'].create({'name': user.name, 'user_id': user.id,
                'company_id': cls.company.id, 'department_id': department.id})
        cls.grant = cls.env['tp.report.assignment'].create({'name': 'Picker scoped plan',
            'user_id': cls.manager.id, 'company_id': cls.company.id, 'department_id': cls.departments[0].id,
            'capability': 'plan', 'date_start': '2020-01-01', 'reason': 'Synthetic test scope'})

    def options(self, user, purpose='plan', **kwargs):
        return self.env['tp.report.people'].with_user(user).get_options(purpose, company_id=self.company.id, **kwargs)

    def test_employee_only_own_identity_not_department_directory(self):
        rows = self.options(self.employee, department_id=self.departments[0].id)
        self.assertEqual([row['id'] for row in rows], self.employee.ids)
        self.assertEqual(set(rows[0]), {'id', 'display_name'})

    def test_manager_picker_stays_in_effective_department_and_revokes(self):
        rows = self.options(self.manager)
        ids = {row['id'] for row in rows}
        self.assertIn(self.employee.id, ids)
        self.assertNotIn(self.outside.id, ids)
        self.grant.active = False
        self.assertEqual([row['id'] for row in self.options(self.manager)], self.manager.ids)

    def test_subject_scope_does_not_widen_to_all_department(self):
        self.grant.subject_id = self.employee
        self.assertEqual([row['id'] for row in self.options(self.manager)], self.employee.ids)

    def test_config_requires_config_group_and_returns_only_names(self):
        with self.assertRaises(AccessError):
            self.options(self.employee, 'configuration')
        self.manager.group_ids = [Command.link(self.env.ref('tp_reporting.group_reporting_config').id)]
        rows = self.options(self.manager, 'configuration', department_id=self.departments[0].id)
        self.assertIn(self.employee.id, {row['id'] for row in rows})
        self.assertNotIn(self.outside.id, {row['id'] for row in rows})
        self.assertTrue(all(set(row) == {'id', 'display_name'} for row in rows))

    def test_unrecognized_purpose_model_and_crosscompany_are_rejected(self):
        with self.assertRaises(ValidationError):
            self.options(self.manager, 'arbitrary')
        with self.assertRaises(ValidationError):
            self.options(self.manager, model='res.users')
        with self.assertRaises(AccessError):
            self.env['tp.report.people'].with_user(self.manager).get_options('plan', company_id=999999)
        with self.assertRaises(AccessError):
            self.options(self.employee, 'directive')
