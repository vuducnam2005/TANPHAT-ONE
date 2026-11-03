from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestTimesheetScope(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        groups = 'tp_core.group_user,project.group_project_user,hr_timesheet.group_hr_timesheet_user,base.group_allow_export'
        cls.member = new_test_user(cls.env, login='scope_member', groups=groups)
        cls.outside = new_test_user(cls.env, login='scope_outside', groups=groups)
        for user in (cls.member, cls.outside):
            cls.env['hr.employee'].create({'name': user.name, 'user_id': user.id, 'company_id': cls.env.company.id})
        cls.project = cls.env['project.project'].create({
            'name': 'Private managed timesheet fixture', 'tp_managed': True, 'tp_code': 'TIME-SCOPE',
            'company_id': cls.env.company.id, 'allow_timesheets': True,
        })
        cls.env['tp.project.assignment'].create({'project_id': cls.project.id, 'user_id': cls.member.id})
        cls.task = cls.env['project.task'].create({'name': 'Scope task', 'project_id': cls.project.id,
                                                  'user_ids': [Command.set([cls.member.id])]})

    def line(self, user, project=None, task=None):
        return self.env['account.analytic.line'].with_user(user).create({
            'name': 'Fictional scope hours', 'project_id': (project or self.project).id,
            'task_id': (task or self.task).id, 'unit_amount': 1, 'employee_id': user.employee_id.id,
        })

    def test_assigned_user_can_create_and_edit_own_hours(self):
        line = self.line(self.member)
        line.write({'unit_amount': 1.5})
        self.assertEqual(line.unit_amount, 1.5)
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.task.with_user(self.member).write({'name': 'Still forbidden'})

    def test_cross_scope_create_denied(self):
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.line(self.outside)

    def test_read_search_group_and_export_denied_after_assignment_removed(self):
        line = self.line(self.member)
        self.env['tp.project.assignment'].search([('user_id', '=', self.member.id)]).write({'active': False})
        model = self.env['account.analytic.line'].with_user(self.member)
        self.assertFalse(model.search([('id', '=', line.id)]))
        self.assertFalse(model._read_group([('id', '=', line.id)], ['project_id'], ['unit_amount:sum']))
        with self.assertRaises(AccessError), self.cr.savepoint():
            line.read(['name'])
        with self.assertRaises(AccessError), self.cr.savepoint():
            line.export_data(['name', 'unit_amount'])

    def test_repoint_denied_and_unmanaged_preserved(self):
        native = self.env['project.project'].create({'name': 'Native project', 'allow_timesheets': True,
                                                      'company_id': self.env.company.id})
        native_task = self.env['project.task'].create({'name': 'Native task', 'project_id': native.id})
        line = self.line(self.outside, native, native_task)
        with self.assertRaises(AccessError), self.cr.savepoint():
            line.write({'project_id': self.project.id, 'task_id': self.task.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            line.write({'task_id': self.task.id})

    def test_company_isolation(self):
        company = self.env['res.company'].create({'name': 'Timesheet other fictional company'})
        project = self.env['project.project'].with_company(company).create({
            'name': 'Other company project', 'tp_managed': True, 'tp_code': 'TIME-OTHER', 'company_id': company.id,
            'allow_timesheets': True,
        })
        other_task = self.env['project.task'].with_company(company).create({'name': 'Other company task', 'project_id': project.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.line(self.member, project, other_task)
