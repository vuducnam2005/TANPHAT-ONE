from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class DelegationCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.admin = cls.env.ref('base.user_admin')
        cls.departments = cls.env['hr.department'].create([
            {'name': name, 'company_id': cls.company.id}
            for name in ('Synthetic Delegation KD', 'Synthetic Delegation Design', 'Synthetic Delegation HR')
        ])
        cls.users = cls.env['res.users'].with_context(no_reset_password=True).create([
            {'name': f'Synthetic Delegation {index}', 'login': f'admin.delegate.synthetic.{index}',
             'company_id': cls.company.id, 'company_ids': [Command.set(cls.company.ids)],
             'group_ids': [Command.set([cls.env.ref('base.group_user').id])]}
            for index in range(3)
        ])
        cls.employees = cls.env['hr.employee'].create([
            {'name': user.name, 'company_id': cls.company.id, 'department_id': cls.departments[index].id,
             'user_id': user.id, 'date_version': fields.Date.today()}
            for index, user in enumerate(cls.users)
        ])

    def grant(self, user=None, operation='grant'):
        return self.env['tp.admin.delegation'].with_user(self.admin)._change(
            user or self.users[0], self.company, operation, 'Synthetic reviewed delegation')

    def actor(self, user=None):
        return (user or self.users[0]).with_user(user or self.users[0])


class TestAdminDelegation(DelegationCase):

    def test_grant_revoke_preserve_business_groups_and_identity(self):
        before = [(user.id, user.group_ids.ids, user.company_ids.ids) for user in self.users]
        self.grant()
        self.grant(self.users[1])
        self.assertTrue(self.actor()._tp_has_admin_delegation())
        self.assertTrue(self.actor(self.users[1])._tp_has_admin_delegation())
        self.assertFalse(self.actor()._tp_is_main_admin())
        own_profile = self.env['res.users'].with_user(self.users[0]).tp_get_my_profile()
        self.assertEqual(own_profile['header']['admin_level'], 'Quản trị được ủy quyền')
        self.assertEqual(before, [(user.id, user.group_ids.ids, user.company_ids.ids) for user in self.users])
        self.grant(operation='revoke')
        self.assertFalse(self.actor()._tp_has_admin_delegation())
        self.assertEqual(before, [(user.id, user.group_ids.ids, user.company_ids.ids) for user in self.users])
        ledger = self.env['tp.admin.delegation'].search([('user_id', '=', self.users[0].id)])
        self.assertEqual(ledger.state, 'revoked')
        self.assertEqual(ledger.revoked_by_id, self.admin)
        self.assertTrue(ledger.revoked_at and ledger.grant_reason and ledger.revoke_reason)

    def test_only_main_admin_can_provision_and_ledger_is_immutable(self):
        with self.assertRaises(AccessError):
            self.env['tp.admin.delegation'].with_user(self.users[0])._change(
                self.users[1], self.company, 'grant', 'Synthetic escalation')
        with self.assertRaises(AccessError):
            self.env['tp.admin.delegation'].create({
                'user_id': self.users[0].id, 'company_id': self.company.id, 'state': 'active',
                'granted_by_id': self.admin.id, 'granted_at': fields.Datetime.now(), 'grant_reason': 'Fake',
            })
        self.grant()
        ledger = self.env['tp.admin.delegation'].search([('user_id', '=', self.users[0].id)])
        for operation in (lambda: ledger.write({'state': 'revoked'}), ledger.unlink):
            with self.assertRaises(AccessError):
                operation()
        with self.assertRaises(AccessError):
            self.grant(self.admin)
        with self.assertRaises(UserError):
            self.env['tp.admin.delegation'].with_user(self.admin)._change(self.users[1], self.company, 'grant', ' ')

    def test_all_live_departments_and_unknown_source_fail_closed(self):
        self.grant()
        actor = self.actor()
        self.assertFalse(actor._tp_delegated_other_department(self.company, self.departments[0]))
        self.assertTrue(actor._tp_delegated_other_department(self.company, self.departments[1]))
        self.assertFalse(actor._tp_delegated_other_department(self.company, self.departments[:2]))
        alternate = self.env['tp.report.assignment'].create({
            'name': 'Synthetic alternate business responsibility', 'company_id': self.company.id,
            'department_id': self.departments[1].id, 'user_id': self.users[0].id,
            'capability': 'read', 'reason': 'Synthetic multiple departments',
        })
        self.assertFalse(actor._tp_delegated_other_department(self.company, self.departments[1]))
        self.assertEqual(set(actor._tp_delegation_departments().ids), set(self.departments[:2].ids))
        alternate.department_id = False
        self.assertFalse(actor._tp_delegated_other_department(self.company, self.departments[2]))
        self.assertTrue(actor._tp_delegation_domain().is_false())

    def test_direct_sudo_context_nested_and_version_escalation_denied(self):
        self.grant()
        employee = self.employees[0].with_user(self.users[0])
        user = self.actor()
        attempts = [
            lambda: user.write({'group_ids': [Command.link(self.env.ref('base.group_system').id)]}),
            lambda: user.sudo().write({'company_ids': [Command.clear()]}),
            lambda: employee.sudo().write({'job_title': 'Unauthorized promotion'}),
            lambda: employee.sudo().write({'resource_id': self.employees[1].resource_id.id}),
            lambda: employee.sudo().write({'version_ids': [Command.update(employee.sudo().current_version_id.id, {'job_title': 'Nested'})]}),
            lambda: employee.sudo().current_version_id.write({'date_version': fields.Date.today()}),
            lambda: employee.sudo().resource_id.write({'user_id': self.users[1].id}),
            lambda: self.env['tp.project.assignment'].with_user(user).sudo().create({'user_id': self.users[1].id}),
            lambda: self.env['res.groups'].with_user(user).sudo().create({'name': 'Synthetic illicit group'}),
            lambda: self.env['hr.employee'].with_user(user).sudo().create({'name': 'Clone', 'resource_id': employee.sudo().resource_id.id}),
            lambda: employee.with_context(_tp_delegated_account=True)._tp_account_admin(existing=True),
            lambda: self.env['tp.hr.import.batch'].with_user(user).sudo().create({'name': 'Synthetic import'})._manager(),
        ]
        for operation in attempts:
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                operation()

    def test_native_reauth_required_and_delegate_cannot_grant(self):
        wizard = self.env['tp.admin.delegation.wizard'].with_user(self.admin).create({
            'employee_id': self.employees[0].id, 'operation': 'grant', 'reason': 'Synthetic authenticated action'})
        with self.assertRaises(UserError):
            wizard.action_apply()
        self.assertFalse(self.actor()._tp_has_admin_delegation())
        with self.assertRaises(AccessError):
            self.employees[0].with_user(self.users[0]).action_tp_grant_admin()

    def test_identity_context_defaults_cannot_bypass_create_guards(self):
        self.grant()
        actor_env = self.env(user=self.users[0], su=True)
        attempts = [
            lambda: actor_env['hr.version'].with_context(default_employee_id=self.employees[0].id).create({
                'department_id': self.departments[1].id, 'date_version': fields.Date.add(fields.Date.today(), days=1)}),
            lambda: actor_env['resource.resource'].with_context(default_user_id=self.users[0].id).create({'name': 'Synthetic identity clone'}),
            lambda: actor_env['hr.employee'].with_context(default_department_id=self.departments[0].id).create({
                'name': 'Synthetic own department clone', 'company_id': self.company.id}),
        ]
        for key, value in [('user_id', self.users[0].id), ('resource_id', self.employees[0].resource_id.id),
                           ('current_version_id', self.employees[0].current_version_id.id),
                           ('work_contact_id', self.admin.partner_id.id)]:
            attempts.append(lambda key=key, value=value: actor_env['hr.employee'].with_context(**{'default_' + key: value}).create({
                'name': 'Synthetic identity clone', 'company_id': self.company.id, 'department_id': self.departments[1].id}))
        for operation in attempts:
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                operation()

    def test_authority_default_subject_receives_scope_fence(self):
        self.grant()
        self.env.cr.execute('SELECT tp_admin_scope_revision FROM res_users WHERE id=%s', [self.users[0].id])
        before = self.env.cr.fetchone()[0]
        self.env['tp.report.assignment'].with_context(default_user_id=self.users[0].id).create({
            'name': 'Synthetic default subject responsibility', 'company_id': self.company.id,
            'department_id': self.departments[1].id, 'capability': 'read', 'reason': 'Synthetic scope fence',
        })
        self.env.cr.execute('SELECT tp_admin_scope_revision FROM res_users WHERE id=%s', [self.users[0].id])
        self.assertGreater(self.env.cr.fetchone()[0], before)

    def test_reporting_responsibility_protects_department_and_unknown_closes_scope(self):
        self.grant()
        assignment = self.env['tp.report.assignment'].create({
            'name': 'Synthetic report read responsibility', 'user_id': self.users[0].id,
            'capability': 'read', 'company_id': self.company.id,
            'department_id': self.departments[1].id, 'reason': 'Synthetic prior business assignment',
        })
        self.assertFalse(self.actor()._tp_delegated_other_department(self.company, self.departments[1]))
        self.assertTrue(self.actor()._tp_delegated_other_department(self.company, self.departments[2]))
        assignment.department_id = False
        self.assertFalse(self.actor()._tp_delegated_other_department(self.company, self.departments[2]))
        with self.assertRaises(AccessError):
            assignment.with_user(self.users[0]).sudo().write({'department_id': self.departments[2].id})

    def test_account_target_scope_and_privileged_identity_protection(self):
        self.grant()
        actor = self.users[0]
        other = self.employees[1].with_user(actor)
        self.assertEqual(other._tp_delegated_account_check(existing=True).id, other.id)
        with self.assertRaises(AccessError):
            self.employees[0].with_user(actor)._tp_delegated_account_check(existing=True)
        self.grant(self.users[1])
        with self.assertRaises(AccessError):
            other._tp_delegated_account_check(existing=True)

    def test_account_reset_lock_scope_rechecked_after_revoke(self):
        self.grant()
        actor = self.users[0]
        target = self.employees[1]
        wizard = self.env['tp.hr.account.wizard'].with_user(actor).create({
            'employee_id': target.id, 'expected_user_id': target.user_id.id, 'reason': 'Synthetic account lock'})
        wizard.action_lock()
        self.assertFalse(target.user_id.active)
        wizard.action_unlock()
        self.assertTrue(target.user_id.active)
        with patch.object(type(wizard), '_require_recent_identity', return_value=None):
            self.assertTrue(wizard.action_set_password('Synthetic-Strong-New-2026', 'Synthetic-Strong-New-2026'))
        self.grant(operation='revoke')
        with self.assertRaises(AccessError):
            wizard.action_lock()

    def test_native_navigation_uses_scoped_lists_without_system_tools(self):
        menus = self.env['ir.ui.menu'].with_user(self.users[0])
        before = menus.load_menus(False)
        self.grant()
        delegated = menus.load_menus(False)
        expected = {
            'tp_hr_workspace.menu_hr': 'tp_hr_workspace.action_employees',
            'tp_kd_workspace.menu_kd': 'tp_kd_workspace.action_projects',
            'tp_reporting.menu_root': 'tp_reporting.action_personal',
            'tp_equipment.menu_root': 'tp_equipment.action_equipment',
        }
        for menu_xmlid, action_xmlid in expected.items():
            menu_id = self.env.ref(menu_xmlid).id
            if menu_xmlid == 'tp_equipment.menu_root' and not self.env['maintenance.equipment'].with_user(self.users[0]).has_access('read'):
                self.assertNotIn(menu_id, delegated['root']['children'])
                continue
            self.assertIn(menu_id, delegated['root']['children'])
            self.assertEqual(delegated[menu_id]['action_id'], self.env.ref(action_xmlid).id)
        for xmlid in ('base.menu_administration', 'base.menu_management'):
            menu_id = self.env.ref(xmlid).id
            self.assertEqual(menu_id in delegated, menu_id in before)
        self.grant(operation='revoke')
        self.assertEqual(menus.load_menus(False), before)

    def test_team_and_department_source_changes_fence_scope_and_deny_delegate(self):
        team = self.env['crm.team'].create({
            'name': 'Synthetic source team', 'company_id': self.company.id,
            'kd_department_id': self.departments[1].id,
            'user_id': self.users[1].id,
        })
        self.env['crm.team.member'].create({'crm_team_id': team.id, 'user_id': self.users[0].id})
        self.grant()
        self.grant(self.users[1])
        self.assertFalse(self.actor()._tp_delegated_other_department(self.company, self.departments[1]))
        self.assertFalse(self.actor(self.users[1])._tp_delegated_other_department(self.company, self.departments[1]))
        self.env.cr.execute('SELECT tp_admin_scope_revision FROM res_users WHERE id=%s', [self.users[0].id])
        before = self.env.cr.fetchone()[0]
        team.write({'kd_department_id': self.departments[2].id})
        self.env.cr.execute('SELECT tp_admin_scope_revision FROM res_users WHERE id=%s', [self.users[0].id])
        after_team = self.env.cr.fetchone()[0]
        self.assertGreater(after_team, before)
        self.assertFalse(self.actor()._tp_delegated_other_department(self.company, self.departments[2]))
        self.assertFalse(self.actor(self.users[1])._tp_delegated_other_department(self.company, self.departments[2]))
        self.departments[2].write({'active': False})
        self.env.cr.execute('SELECT tp_admin_scope_revision FROM res_users WHERE id=%s', [self.users[0].id])
        self.assertGreater(self.env.cr.fetchone()[0], after_team)
        attempts = [
            lambda: team.with_user(self.users[0]).sudo().write({'kd_department_id': self.departments[1].id}),
            lambda: team.with_user(self.users[0]).sudo().write({'member_ids': [Command.clear()]}),
            lambda: team.with_user(self.users[0]).sudo().unlink(),
            lambda: self.departments[2].with_user(self.users[0]).sudo().write({'active': True}),
        ]
        for operation in attempts:
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                operation()
