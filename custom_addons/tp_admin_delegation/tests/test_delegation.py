
from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class DelegationCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        employee_model = cls.env['hr.employee']
        sequence = employee_model._tp_code_sequence()
        cls.env.cr.execute('SELECT last_value, is_called FROM ir_sequence_%03d' % sequence.id)
        cls.addClassCleanup(cls._restore_employee_sequence, sequence.id, *cls.env.cr.fetchone())
        employee_model._tp_reset_code_sequence(employee_model._tp_code_floor())
        cls.company = cls.env.company
        cls.admin = cls.env.ref('base.user_admin')
        cls.env['tp.admin.delegation']._migrate_admin_full_001()
        cls.departments = cls.env['hr.department'].create([
            {'name': name, 'company_id': cls.company.id}
            for name in ('Synthetic FullAdmin KD', 'Synthetic FullAdmin Design', 'Synthetic FullAdmin HR')
        ])
        cls.users = cls.env['res.users'].with_context(no_reset_password=True).create([
            {
                'name': f'Synthetic Admin Candidate {index}',
                'login': f'admin.full.synthetic.{index}',
                'company_id': cls.company.id,
                'company_ids': [Command.set(cls.company.ids)],
                'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
            }
            for index in range(3)
        ])
        cls.employees = cls.env['hr.employee'].create([
            {
                'name': user.name,
                'company_id': cls.company.id,
                'department_id': cls.departments[index].id,
                'job_title': f'Chức danh nhân viên {index}',
                'user_id': user.id,
                'date_version': fields.Date.today(),
            }
            for index, user in enumerate(cls.users)
        ])

    def grant(self, user=None, operation='grant'):
        return self.env['tp.admin.delegation'].with_user(self.admin)._change(
            user or self.users[0], self.company, operation, 'Synthetic reviewed full admin',
        )

    @classmethod
    def _restore_employee_sequence(cls, sequence_id, last_value, is_called):
        with cls.registry.cursor() as cr:
            cr.execute('SELECT setval(%s, %s, %s)', ['ir_sequence_%03d' % sequence_id, last_value, is_called])

    def actor(self, user=None):
        target = user or self.users[0]
        return target.with_user(target)


class TestAdminDelegation(DelegationCase):

    def test_open_grant_and_revoke_dialog_without_reason_does_not_grant(self):
        for method in ('action_tp_grant_admin', 'action_tp_revoke_admin'):
            action = getattr(self.employees[0].with_user(self.admin), method)()
            wizard = self.env[action['res_model']].with_user(self.admin).browse(action['res_id'])
            self.assertFalse(wizard.reason)
            self.assertEqual(wizard.expected_user_id, self.users[0])
            for reason in (False, '  \n '):
                wizard.reason = reason
                with self.assertRaises(UserError):
                    wizard.action_apply.__wrapped__(wizard)
            self.assertFalse(self.actor()._tp_is_granted_admin())
            self.assertFalse(self.actor().has_group('base.group_system'))

    def test_grant_gives_full_admin_keeps_hr_position_and_revoke_restores_exact_business_groups(self):
        user = self.users[0]
        emp = self.employees[0]
        before_dept = emp.department_id
        before_title = emp.job_title
        before_groups = set(user.group_ids.ids)
        token_before = user._compute_session_token('synthetic-sid-001')

        self.grant(user)
        self.assertTrue(user._tp_is_granted_admin())
        self.assertTrue(user._tp_is_main_admin())
        self.assertFalse(user._tp_is_original_admin())
        self.assertTrue(user.has_group('base.group_system'))
        self.assertTrue(user.has_group('hr.group_hr_manager'))
        self.assertTrue(user.has_group('tp_core.group_manager'))
        self.assertEqual(emp.department_id, before_dept)
        self.assertEqual(emp.job_title, before_title)

        token_granted = user._compute_session_token('synthetic-sid-001')
        self.assertNotEqual(token_granted, token_before)

        # Legitimate business group added while holding full admin must survive revocation!
        scoped_staff = self.env.ref('tp_kd_workspace.group_scoped_staff')
        user.with_user(self.admin).write({'group_ids': [Command.link(scoped_staff.id)]})

        own_profile = self.env['res.users'].with_user(user).tp_get_my_profile()
        self.assertEqual(own_profile['header']['admin_level'], 'Admin ủy quyền')

        self.grant(user, operation='revoke')
        self.assertFalse(user._tp_is_granted_admin())
        self.assertFalse(user._tp_is_main_admin())
        self.assertFalse(user.has_group('base.group_system'))
        self.assertFalse(user.has_group('base.group_erp_manager'))
        self.assertFalse(user.has_group('hr.group_hr_manager'))
        self.assertEqual(set(user.group_ids.ids), before_groups | {scoped_staff.id})

        token_revoked = user._compute_session_token('synthetic-sid-001')
        self.assertNotEqual(token_revoked, token_granted)

    def test_revoke_refuses_false_success_when_residual_admin_group_exists(self):
        user = self.users[1]
        self.grant(user)
        # Original admin manually attaches base.group_erp_manager directly: revoke must detect and roll back.
        erp_group = self.env.ref('base.group_erp_manager')
        user.with_user(self.admin).write({'group_ids': [Command.link(erp_group.id)]})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            self.grant(user, operation='revoke')
        # Ledger remains active because the savepoint rolled back.
        self.assertTrue(user._tp_has_live_admin_grant())
        user.with_user(self.admin).write({'group_ids': [Command.unlink(erp_group.id)]})
        self.grant(user, operation='revoke')
        self.assertFalse(user._tp_has_live_admin_grant())

    def test_dec054_granted_admin_cannot_provision_admin_or_escalate_via_any_vector(self):
        self.grant(self.users[0])
        granted = self.users[0]
        target = self.users[1]
        emp_target = self.employees[1].with_user(granted)

        self.assertFalse(emp_target.tp_can_manage_delegation)
        orig_group = self.env.ref('tp_admin_delegation.group_original_admin')
        full_group = self.env.ref('tp_admin_delegation.group_full_admin')
        sys_group = self.env.ref('base.group_system')
        erp_group = self.env.ref('base.group_erp_manager')
        user_group = self.env.ref('base.group_user')

        attempts = [
            # 1. Provisioning wizard / ledger / sudo _change
            emp_target.action_tp_grant_admin,
            self.employees[0].with_user(granted).action_tp_revoke_admin,
            lambda: self.env['tp.admin.delegation'].with_user(granted)._change(target, self.company, 'grant', 'Escalation'),
            lambda: self.env['tp.admin.delegation'].with_user(granted).sudo()._change(target, self.company, 'grant', 'Sudo escalation'),
            lambda: self.env['tp.admin.delegation.wizard'].with_user(granted).create({'employee_id': target.id, 'operation': 'grant'}),
            lambda: self.env['tp.admin.delegation'].with_user(granted).sudo().create({
                'user_id': target.id, 'company_id': self.company.id, 'state': 'active',
                'granted_by_id': granted.id, 'granted_at': fields.Datetime.now(), 'grant_reason': 'Direct ledger',
            }),
            # 2. res.users group_ids, role, self-linking, new user with admin, copy, default_group_ids, import load
            lambda: target.with_user(granted).write({'group_ids': [Command.link(sys_group.id)]}),
            lambda: target.with_user(granted).sudo().write({'group_ids': [Command.link(full_group.id)]}),
            lambda: target.with_user(granted).write({'group_ids': [Command.link(erp_group.id)]}),
            lambda: granted.with_user(granted).write({'group_ids': [Command.link(orig_group.id)]}),
            lambda: granted.with_user(granted).write({'group_ids': [Command.link(sys_group.id)]}),
            lambda: self.env['res.users'].with_user(granted).with_context(no_reset_password=True).create({
                'name': 'Illicit Admin', 'login': 'illicit.admin.create',
                'company_id': self.company.id, 'company_ids': [Command.set(self.company.ids)],
                'group_ids': [Command.set([sys_group.id])],
            }),
            lambda: self.env['res.users'].with_user(granted).with_context(
                no_reset_password=True, default_group_ids=[Command.set([sys_group.id])],
            ).create({'name': 'Default Admin', 'login': 'default.admin.create'}),
            lambda: self.admin.with_user(granted).copy({'login': 'copied.original.admin'}),
            # 3. res.groups membership & implied_ids tampering
            lambda: sys_group.with_user(granted).write({'user_ids': [Command.link(target.id)]}),
            lambda: full_group.with_user(granted).sudo().write({'user_ids': [Command.link(target.id)]}),
            lambda: user_group.with_user(granted).sudo().write({'implied_ids': [Command.link(sys_group.id)]}),
            lambda: self.env['res.groups'].with_user(granted).create({'name': 'New Group'}),
            # 4. Original admin & technical escalation vectors
            lambda: self.admin.with_user(granted).write({'email': 'hijack@example.invalid'}),
            lambda: self.admin.partner_id.with_user(granted).write({'email': 'hijack@example.invalid'}),
            lambda: self.admin.with_user(granted)._change_password('Hijacked-2026!'),
            lambda: self.admin.with_user(granted).action_reset_password(),
            lambda: self.env['ir.actions.server'].with_user(granted).create({
                'name': 'Illicit Python', 'model_id': self.env['ir.model']._get_id('res.users'), 'state': 'code', 'code': 'pass',
            }),
            lambda: self.env['ir.access'].with_user(granted).create({
                'name': 'Illicit ACL', 'model_id': self.env['ir.model']._get_id('tp.admin.delegation'), 'operation': 'crud',
            }),
            lambda: self.env.ref('base.user_admin').env['ir.model.data'].with_user(granted).search([
                ('module', '=', 'base'), ('name', '=', 'user_admin'),
            ]).write({'res_id': granted.id}),
            lambda: self.env['ir.module.module'].with_user(granted).search([('name', '=', 'tp_admin_delegation')]).button_immediate_uninstall(),
            lambda: self.env['ir.config_parameter'].with_user(granted).sudo().set_str('database.secret', 'tampered'),
        ]
        for attempt in attempts:
            with self.assertRaises((AccessError, UserError)), self.env.cr.savepoint():
                attempt()

        # Meanwhile, Granted Admin CAN assign normal business groups to normal employees!
        proj_user = self.env.ref('project.group_project_user')
        target.with_user(granted).write({'group_ids': [Command.link(proj_user.id)]})
        self.assertTrue(target.has_group('project.group_project_user'))

    def test_last_original_admin_protection_and_idempotent_migration(self):
        orig_group = self.env.ref('tp_admin_delegation.group_original_admin')
        # Keep the last-admin scenario independent of extra originals in the test DB.
        others = self.env['res.users'].with_context(active_test=False).search([
            ('id', '!=', self.admin.id), ('group_ids', 'in', orig_group.ids)])
        others.with_user(self.admin).write({'group_ids': [Command.unlink(orig_group.id)]})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            self.admin.with_user(self.admin).write({'group_ids': [Command.unlink(orig_group.id)]})

        # Simulate legacy active row without group_full_admin and run migration twice.
        full_group = self.env.ref('tp_admin_delegation.group_full_admin')
        self.grant(self.users[2])
        self.users[2].with_user(self.admin).write({'group_ids': [Command.unlink(full_group.id)]})
        self.assertFalse(self.users[2].has_group('base.group_system'))

        first = self.env['tp.admin.delegation']._migrate_admin_full_001()
        self.assertIn(self.users[2].id, first['migrated_user_ids'])
        self.assertTrue(self.users[2].has_group('base.group_system'))

        second = self.env['tp.admin.delegation']._migrate_admin_full_001()
        self.assertEqual(second['migrated_user_ids'], [])
        self.assertIn(self.users[2].id, second['already_full_user_ids'])
