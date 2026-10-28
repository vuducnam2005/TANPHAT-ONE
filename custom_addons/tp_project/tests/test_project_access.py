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
