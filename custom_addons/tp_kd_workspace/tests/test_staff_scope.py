"""Scoped staff cannot inherit Odoo's general employee project/task visibility."""
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestStaffScope(TransactionCase):
    def test_staff_scope_preserves_legacy_reader_and_rechecks_assignment(self):
        staff = new_test_user(self.env, login='kd_scope_staff', groups='tp_kd_workspace.group_scoped_staff,base.group_allow_export')
        legacy = new_test_user(self.env, login='kd_scope_legacy', groups='tp_core.group_user')
        general = self.env['project.project'].create({'name': 'General employee project', 'privacy_visibility': 'employees'})
        project = self.env['project.project'].create({
            'name': 'Scoped synthetic', 'tp_code': 'KD-STAFF-SCOPE', 'tp_managed': True,
            'company_id': self.env.company.id, 'privacy_visibility': 'employees'})
        assignment = self.env['tp.project.assignment'].create({'project_id': project.id, 'user_id': staff.id})
        task = self.env['project.task'].create({'name': 'General task', 'project_id': general.id,
                                               'user_ids': [Command.set(staff.ids)]})
        self.assertTrue(general.with_user(legacy).has_access('read'))
        self.assertFalse(general.with_user(staff).has_access('read'))
        self.assertFalse(task.with_user(staff).has_access('read'))
        self.assertEqual(self.env['project.project'].with_user(staff).search([]), project)
        with self.assertRaises(AccessError):
            general.with_user(staff).export_data(['name'])
        assignment.active = False
        self.env.transaction.invalidate_access_cache()
        self.assertFalse(project.with_user(staff).has_access('read'))
