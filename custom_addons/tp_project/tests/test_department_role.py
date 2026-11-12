"""Department scope must be dynamic, bounded and revocable without a new login."""

from datetime import date, timedelta
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon


@tagged('post_install', '-at_install')
class TestDepartmentRole(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.head = new_test_user(cls.env, login='department_head_test', groups='tp_core.group_user,base.group_allow_export', company_id=cls.company.id)
        cls.staff = new_test_user(cls.env, login='department_staff_test', groups='tp_core.group_user', company_id=cls.company.id)
        cls.department = cls.env['hr.department'].create({'name': 'Synthetic KH-KD', 'company_id': cls.company.id})
        cls.other_department = cls.env['hr.department'].create({'name': 'Synthetic unrelated department', 'company_id': cls.company.id})
        cls.project = cls.env['project.project'].create({
            'name': 'Department project', 'company_id': cls.company.id, 'tp_managed': True,
            'tp_code': 'HEAD-SCOPE-001', 'tp_department_id': cls.department.id, 'privacy_visibility': 'employees',
        })
        cls.other_project = cls.env['project.project'].create({
            'name': 'Other department project', 'company_id': cls.company.id, 'tp_managed': True,
            'tp_code': 'HEAD-SCOPE-002', 'tp_department_id': cls.other_department.id, 'privacy_visibility': 'employees',
        })
        cls.role = cls.env['tp.kd.department.role'].create({
            'user_id': cls.head.id, 'company_id': cls.company.id, 'department_id': cls.department.id,
            'reason': 'Synthetic department responsibility',
        })

    def test_dynamic_projects_and_exact_department(self):
        project = self.project.with_user(self.head)
        self.assertTrue(project.has_access('read'))
        self.assertTrue(project.tp_scope_access)
        self.assertTrue(project.tp_financial_read_granted)
        self.assertFalse(self.other_project.with_user(self.head).has_access('read'))
        self.assertFalse(self.project.with_user(self.staff).has_access('read'))
        new_project = self.env['project.project'].sudo().create({
            'name': 'Created after HEAD provisioning', 'company_id': self.company.id,
            'tp_managed': True, 'tp_code': 'HEAD-SCOPE-NEW', 'tp_department_id': self.department.id,
        })
        self.assertTrue(new_project.with_user(self.head).has_access('read'))
        found = self.env['project.project'].with_user(self.head).search([('tp_managed', '=', True)])
        self.assertEqual(set(found.ids), {self.project.id, new_project.id})
        grouped = found._read_group([('tp_managed', '=', True)], ['company_id'], ['__count'])
        self.assertEqual([(company.id, count) for company, count in grouped], [(self.company.id, 2)])
        self.assertEqual(len(found.export_data(['tp_code'])['datas']), 2)
        self.assertEqual(self.env['tp.kd.department.role']._head_users(self.project), self.head)

    def test_revoke_and_expiry_close_cached_access_and_money(self):
        project = self.project.with_user(self.head)
        self.assertTrue(project.has_access('read'))
        self.assertTrue(project.tp_financial_read_granted)
        self.role.sudo().write({'active': False, 'reason': 'Synthetic revocation'})
        self.assertFalse(project.has_access('read'))
        self.assertFalse(project._tp_scope_allowed())
        self.assertFalse(self.env['tp.project.grant'].with_user(self.head)._tp_has_capability(project, 'financial_read'))
        self.assertFalse(self.env['project.project'].with_user(self.head).search([('tp_financial_read_granted', '=', True)]))
        with self.assertRaises(AccessError):
            project.export_data(['name'])
        self.role.sudo().write({'active': True, 'reason': 'Synthetic restoration'})
        self.assertTrue(project.has_access('read'))
        tomorrow = date.today() + timedelta(days=1)
        self.role.sudo().write({'date_end': date.today(), 'reason': 'Synthetic expiry boundary'})
        with patch('odoo.addons.tp_project.models.department_role.fields.Date.context_today', return_value=tomorrow):
            self.env.invalidate_all()
            self.env.transaction.invalidate_access_cache()
            self.assertFalse(project.has_access('read'))
            self.assertFalse(project._tp_head_allowed())
            self.assertFalse(project.tp_financial_read_granted)
        events = self.env['tp.kd.department.role.event'].sudo().search([('role_id', '=', self.role.id)])
        self.assertEqual(len(events), 4)
        self.assertIn('Synthetic revocation', events[1].after)
        with self.assertRaises(UserError):
            events[1].write({'reason': 'Rewritten audit'})

    def test_role_does_not_allow_generic_project_write_or_security_administration(self):
        for project in (self.project, self.project | self.other_project):
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                project.with_user(self.head).write({'name': 'Generic write denied'})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.role.with_user(self.head).write({'active': False, 'reason': 'Self administered'})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env['tp.kd.department.role'].with_user(self.head).create({
                'user_id': self.head.id, 'company_id': self.company.id,
                'department_id': self.other_department.id, 'reason': 'Self escalation',
            })
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.role.sudo().write({'active': False})
        with self.assertRaises(UserError):
            self.role.unlink()
        self.assertFalse(self.env['tp.project.assignment'].sudo().search([('user_id', '=', self.head.id)]))
        self.assertFalse(self.env['tp.project.grant'].sudo().search([('user_id', '=', self.head.id)]))

    def test_role_company_user_activity_and_start_date_are_live(self):
        self.role.sudo().write({'date_start': date.today() + timedelta(days=1), 'reason': 'Synthetic future appointment'})
        self.assertFalse(self.project.with_user(self.head)._tp_head_allowed())
        self.role.sudo().write({'date_start': date.today(), 'reason': 'Synthetic effective appointment'})
        self.assertTrue(self.project.with_user(self.head)._tp_head_allowed())
        self.head.sudo().active = False
        self.assertFalse(self.project.with_user(self.head)._tp_head_allowed())
        self.head.sudo().active = True
        self.assertTrue(self.project.with_user(self.head)._tp_head_allowed())
        foreign = self.env['res.company'].sudo().create({'name': 'Synthetic foreign company'})
        foreign_department = self.env['hr.department'].sudo().create({'name': 'Foreign KH-KD', 'company_id': foreign.id})
        foreign_project = self.env['project.project'].sudo().create({
            'name': 'Foreign project', 'company_id': foreign.id, 'tp_managed': True,
            'tp_code': 'HEAD-FOREIGN', 'tp_department_id': foreign_department.id,
        })
        self.assertFalse(foreign_project.with_user(self.head)._tp_head_allowed())
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env['tp.kd.department.role'].sudo().create({
                'user_id': self.head.id, 'company_id': self.company.id,
                'department_id': foreign_department.id, 'reason': 'Wrong company scope',
            })
