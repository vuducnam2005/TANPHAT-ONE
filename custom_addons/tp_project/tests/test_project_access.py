from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestProjectAccess(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reader = new_test_user(cls.env, login='tp_reader', groups='tp_core.group_user', company_id=cls.company.id)
        cls.other_reader = new_test_user(cls.env, login='tp_other_reader', groups='tp_core.group_user', company_id=cls.company.id)
        cls.manager = new_test_user(cls.env, login='tp_manager', groups='tp_core.group_manager', company_id=cls.company.id)
        cls.project = cls.env['project.project'].create({
            'name': 'Assigned Project', 'company_id': cls.company.id,
            'tp_managed': True, 'tp_code': 'TP-TEST-001', 'privacy_visibility': 'employees',
        })
        cls.hidden_project = cls.env['project.project'].create({
            'name': 'Other Project', 'company_id': cls.company.id,
            'tp_managed': True, 'tp_code': 'TP-TEST-002', 'privacy_visibility': 'employees',
        })
        cls.assignment = cls.env['tp.project.assignment'].create({
            'project_id': cls.project.id, 'user_id': cls.reader.id,
        })

    def test_reader_sees_only_assigned_project(self):
        projects = self.env['project.project'].with_user(self.reader).search([('tp_managed', '=', True)])
        self.assertIn(self.project.id, projects.ids)
        self.assertNotIn(self.hidden_project.id, projects.ids)
        with self.assertRaises(AccessError):
            self.hidden_project.with_user(self.reader).read(['name'])

    def test_reader_cannot_write_or_self_assign(self):
        with self.assertRaises(AccessError):
            self.project.with_user(self.reader).write({'name': 'Changed'})
        with self.assertRaises(AccessError):
            self.env['tp.project.assignment'].with_user(self.other_reader).create({
                'project_id': self.hidden_project.id, 'user_id': self.other_reader.id,
            })

    def test_native_project_manager_does_not_bypass_assignment_scope(self):
        self.reader.sudo().group_ids = [Command.link(self.env.ref('project.group_project_manager').id)]
        with self.assertRaises(AccessError):
            self.hidden_project.with_user(self.reader).read(['name'])

    def test_native_manager_cannot_promote_unmanaged_project(self):
        self.reader.sudo().group_ids = [Command.link(self.env.ref('project.group_project_manager').id)]
        project = self.env['project.project'].with_user(self.manager).create({'name': 'Native Project', 'company_id': self.company.id})
        with self.assertRaises(AccessError):
            project.with_user(self.reader).write({'tp_managed': True, 'tp_code': 'PROMOTED'})
        with self.assertRaises(AccessError):
            self.env['project.project'].with_user(self.reader).create({
                'name': 'Unauthorized Platform Project', 'company_id': self.company.id,
                'tp_managed': True, 'tp_code': 'BYPASS',
            })

    def test_revoked_assignment_removes_access(self):
        self.assignment.with_user(self.manager).active = False
        self.assertFalse(self.env['project.project'].with_user(self.reader).search([('id', '=', self.project.id)]))

    def test_platform_manager_still_respects_company_scope(self):
        other_company = self.env['res.company'].sudo().create({'name': 'Other Tan Phat Test Company'})
        foreign_project = self.env['project.project'].sudo().create({
            'name': 'Foreign Project', 'company_id': other_company.id,
            'tp_managed': True, 'tp_code': 'TP-FOREIGN-001',
        })
        self.assertEqual(self.project.with_user(self.manager).name, 'Assigned Project')
        with self.assertRaises(AccessError):
            foreign_project.with_user(self.manager).read(['name'])


class TestPrivateTodoAccess(BaseCommon):
    """Native To-dos (tasks without project) must keep native access under the TP task scope."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = new_test_user(cls.env, login='tp_todo_owner', groups='tp_core.group_user', company_id=cls.company.id)
        cls.colleague = new_test_user(cls.env, login='tp_todo_colleague', groups='tp_core.group_user', company_id=cls.company.id)
        cls.outsider = new_test_user(cls.env, login='tp_todo_outsider', groups='tp_core.group_user', company_id=cls.company.id)
        cls.manager = new_test_user(
            cls.env, login='tp_todo_manager', company_id=cls.company.id,
            groups='tp_core.group_manager,project.group_project_manager',
        )
        cls.project = cls.env['project.project'].create({
            'name': 'Assigned Project', 'company_id': cls.company.id,
            'tp_managed': True, 'tp_code': 'TP-TODO-001', 'privacy_visibility': 'employees',
        })
        cls.hidden_project = cls.env['project.project'].create({
            'name': 'Hidden Project', 'company_id': cls.company.id,
            'tp_managed': True, 'tp_code': 'TP-TODO-002', 'privacy_visibility': 'employees',
        })
        cls.env['tp.project.assignment'].create({'project_id': cls.project.id, 'user_id': cls.owner.id})

    def _create_todo(self, user, name='Private To-do'):
        return self.env['project.task'].with_user(user).create({'name': name, 'user_ids': [Command.set(user.ids)]})

    def test_owner_crud_and_personal_stage(self):
        todo = self._create_todo(self.owner)
        self.assertFalse(todo.project_id)
        self.assertEqual(todo.read(['name'])[0]['name'], 'Private To-do')
        self.assertIn(todo, self.env['project.task'].with_user(self.owner).search([('project_id', '=', False)]))
        stage = self.env['project.task.type'].with_user(self.owner).create({'name': 'Today', 'user_id': self.owner.id})
        todo.write({'name': 'Renamed To-do', 'personal_stage_type_id': stage.id})
        self.assertEqual(todo.personal_stage_type_id, stage)
        todo.unlink()
        self.assertFalse(todo.exists())

    def test_other_users_and_managers_cannot_access_private_todo(self):
        todo = self._create_todo(self.owner)
        for user in (self.colleague, self.manager):
            with self.assertRaises(AccessError):
                todo.with_user(user).read(['name'])
            with self.assertRaises(AccessError):
                todo.with_user(user).write({'name': 'Hijacked'})
            with self.assertRaises(AccessError):
                todo.with_user(user).unlink()
            self.assertFalse(self.env['project.task'].with_user(user).search([('id', '=', todo.id)]))

    def test_shared_todo_follows_native_assignees(self):
        todo = self._create_todo(self.owner)
        todo.write({'user_ids': [Command.link(self.colleague.id)]})
        self.assertEqual(todo.with_user(self.colleague).read(['name'])[0]['name'], 'Private To-do')
        with self.assertRaises(AccessError):
            todo.with_user(self.outsider).read(['name'])

    def test_todo_respects_company_scope(self):
        other_company = self.env['res.company'].sudo().create({'name': 'Other To-do Test Company'})
        foreign_todo = self.env['project.task'].sudo().create({
            'name': 'Foreign To-do', 'company_id': other_company.id, 'user_ids': [Command.set(self.owner.ids)],
        })
        with self.assertRaises(AccessError):
            foreign_todo.with_user(self.owner).read(['name'])

    def test_managed_tasks_keep_assignment_scope(self):
        assigned_task = self.env['project.task'].sudo().create({'name': 'Assigned Task', 'project_id': self.project.id})
        hidden_task = self.env['project.task'].sudo().create({'name': 'Hidden Task', 'project_id': self.hidden_project.id})
        self.assertEqual(assigned_task.with_user(self.owner).read(['name'])[0]['name'], 'Assigned Task')
        with self.assertRaises(AccessError):
            hidden_task.with_user(self.owner).read(['name'])
        with self.assertRaises(AccessError):
            assigned_task.with_user(self.owner).write({'name': 'Changed'})

    def test_unmanaged_project_tasks_keep_native_access(self):
        native_project = self.env['project.project'].sudo().create({
            'name': 'Native Project', 'company_id': self.company.id, 'privacy_visibility': 'employees',
        })
        task = self.env['project.task'].sudo().create({'name': 'Native Task', 'project_id': native_project.id})
        self.assertEqual(task.with_user(self.outsider).read(['name'])[0]['name'], 'Native Task')
        self.outsider.sudo().group_ids = [Command.link(self.env.ref('project.group_project_user').id)]
        task.with_user(self.outsider).write({'name': 'Native Task Updated'})
        self.assertEqual(task.name, 'Native Task Updated')
