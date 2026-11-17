from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

from odoo.addons.tp_contract.exceptions import ContractWorkflowError


@tagged('post_install', '-at_install')
class TestDelegatedBusinessScope(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.admin = cls.env.ref('base.user_admin')
        cls.departments = cls.env['hr.department'].create([
            {'name': 'Synthetic AD Business ' + name, 'company_id': cls.company.id}
            for name in ('Own', 'Other')
        ])
        cls.user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic AD Business Actor', 'login': 'ad001.business.synthetic',
            'company_id': cls.company.id, 'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref('tp_kd_workspace.group_scoped_staff').id])],
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': cls.user.name, 'user_id': cls.user.id, 'company_id': cls.company.id,
            'department_id': cls.departments[0].id,
        })
        cls.projects = cls.env['project.project'].create([
            {'name': 'Synthetic AD Project ' + str(i), 'tp_code': f'AD-SYNTH-{i}',
             'tp_managed': True, 'company_id': cls.company.id, 'tp_department_id': department.id}
            for i, department in enumerate([cls.departments[0], cls.departments[0], cls.departments[1]])
        ])
        cls.env['tp.project.assignment'].create({
            'project_id': cls.projects[0].id, 'user_id': cls.user.id, 'role': 'reader',
        })

    def change(self, operation='grant'):
        self.env['tp.admin.delegation'].with_user(self.admin)._change(
            self.user, self.company, operation, 'Synthetic business acceptance')

    def model(self, name):
        return self.env[name].with_user(self.user).with_context(allowed_company_ids=self.company.ids)

    def test_own_project_read_count_money_unchanged_and_revoke(self):
        projects = self.model('project.project')
        before = set(projects.search([('id', 'in', self.projects.ids)]).ids)
        before_finance = [self.env['tp.project.grant'].with_user(self.user)._tp_has_capability(p, 'financial_read')
                          for p in self.projects[:2]]
        self.change()
        self.assertEqual(set(projects.search([('id', 'in', self.projects.ids)]).ids), before | {self.projects[2].id})
        self.assertEqual(projects.search_count([('id', 'in', self.projects.ids)]), len(before) + 1)
        for index, project in enumerate(self.projects[:2]):
            self.assertEqual(self.env['tp.project.grant'].with_user(self.user)._tp_has_capability(project, 'financial_read'),
                             before_finance[index])
        self.assertFalse(self.projects[1].with_user(self.user).has_access('read'))
        self.change('revoke')
        self.assertEqual(set(projects.search([('id', 'in', self.projects.ids)]).ids), before)
        self.assertFalse(self.projects[2].with_user(self.user).has_access('read'))

    def test_foreign_contract_workflow_draft_and_own_denied(self):
        self.change()
        workflow = self.model('tp.contract.workflow')
        payload = {'project_id': self.projects[2].id, 'code': 'AD-SYNTH-CONTRACT',
                   'name': 'Synthetic delegated contract', 'contract_type': 'owner',
                   'currency': self.company.currency_id.name}
        result = workflow._tp_run('create_contract', payload, key='synthetic-ad-create-contract')
        self.assertTrue(result['contract'].has_access('read'))
        self.assertEqual(result['contract'].department_id, self.departments[1])
        self.assertEqual(result['contract'].create_uid, self.user)
        self.assertFalse(self.env['tp.project.assignment'].search_count([
            ('project_id', '=', self.projects[2].id), ('user_id', '=', self.user.id)]))
        self.assertFalse(self.env['tp.project.grant'].search_count([('user_id', '=', self.user.id)]))
        with self.assertRaises(ContractWorkflowError):
            workflow._tp_run('create_contract', dict(payload, project_id=self.projects[0].id, code='AD-OWN'),
                             key='synthetic-ad-own-denied')
        self.change('revoke')
        with self.assertRaises(AccessError):
            result['contract'].read(['name'])

    def test_foreign_project_status_note_and_history_via_command(self):
        own = self.projects[0].with_user(self.user).with_context(allowed_company_ids=self.company.ids)
        own_before = (own._kd_money_read(), own.kd_can_status, own.kd_can_note)
        self.change()
        foreign = self.projects[2].with_user(self.user).with_context(allowed_company_ids=self.company.ids)
        self.assertTrue(foreign._kd_money_read())
        self.assertTrue(foreign.kd_can_status and foreign.kd_can_note)
        own.invalidate_recordset()
        self.assertEqual((own._kd_money_read(), own.kd_can_status, own.kd_can_note), own_before)
        wizard = self.model('tp.project.command').create({'project_id': self.projects[2].id, 'kind': 'status'})
        wizard.write({'target_state': 'executing', 'reason': 'Synthetic delegated status'})
        wizard.action_confirm()
        self.assertEqual(self.projects[2].kd_lifecycle, 'executing')
        note = self.model('tp.project.command').create({'project_id': self.projects[2].id, 'kind': 'note'})
        note.write({'reason': 'Synthetic delegated note'})
        note.action_confirm()
        history = self.model('tp.project.update').search([('project_id', '=', self.projects[2].id)])
        self.assertEqual(len(history), 2)
        self.assertEqual(history.actor_id, self.user)
        self.assertFalse(self.env['tp.project.assignment'].search_count([
            ('project_id', '=', self.projects[2].id), ('user_id', '=', self.user.id)]))
        self.assertFalse(self.env['tp.kd.grant'].search_count([('user_id', '=', self.user.id)]))
        with self.assertRaises(AccessError):
            self.model('tp.project.command').create({'project_id': self.projects[1].id, 'kind': 'status'})
        self.change('revoke')
        foreign.invalidate_recordset()
        self.assertFalse(foreign._kd_money_read())
        with self.assertRaises(AccessError):
            self.model('tp.project.command').create({'project_id': self.projects[2].id, 'kind': 'status'})
        self.assertFalse(self.model('tp.project.update').search_count([('project_id', '=', self.projects[2].id)]))

    def test_foreign_wbs_assignment_keeps_progress_with_assignee(self):
        self.env['tp.project.assignment'].create({
            'project_id': self.projects[2].id, 'user_id': self.admin.id, 'role': 'coordinator',
        })
        self.change()
        command = self.model('tp.task.command').create({'project_id': self.projects[2].id, 'operation': 'create'})
        command.write({'name': 'Synthetic delegated WBS', 'deliverable': 'Synthetic output',
                       'responsible_id': self.admin.id, 'reason': 'Synthetic delegated WBS'})
        command.action_confirm()
        task = self.env['project.task'].search([('project_id', '=', self.projects[2].id)])
        self.assertEqual((task.name, task.kd_responsible_id), ('Synthetic delegated WBS', self.admin))
        self.assertEqual(self.model('tp.task.update').search([('task_id', '=', task.id)]).actor_id, self.user)
        delegated = task.with_user(self.user).with_context(allowed_company_ids=self.company.ids)
        self.assertTrue(delegated.kd_can_wbs and delegated.kd_can_assign)
        # Progress is the assignee's report (or HEAD's); delegation never acts as either.
        self.assertFalse(delegated.kd_can_progress)
        progress = self.model('tp.task.command').create({
            'project_id': self.projects[2].id, 'task_id': task.id, 'operation': 'progress'})
        progress.write({'target_state': '1_done', 'reason': 'Synthetic progress'})
        with self.assertRaises(AccessError):
            progress.action_confirm()
        with self.assertRaises(AccessError):
            self.model('tp.task.command').create({'project_id': self.projects[0].id, 'operation': 'create'})

    def test_mixed_contract_source_and_unknown_crm_block_parent_union(self):
        self.env['tp.contract'].create({
            'name': 'Synthetic mixed contract', 'code': 'AD-MIXED', 'project_id': self.projects[2].id,
            'department_id': self.departments[0].id, 'contract_type': 'owner',
        })
        self.change()
        self.assertFalse(self.projects[2].with_user(self.user).has_access('read'))
        self.assertFalse(self.model('tp.contract').search_count([('code', '=', 'AD-MIXED')]))

    def test_archived_unknown_crm_source_blocks_parent_union(self):
        partner = self.env['res.partner'].create({'name': 'Synthetic archived CRM customer'})
        self.projects[2].partner_id = partner
        lead = self.env['crm.lead'].create({
            'name': 'Synthetic archived unknown-source CRM', 'type': 'opportunity',
            'company_id': self.company.id, 'tp_project_id': self.projects[2].id,
            'partner_id': partner.id,
        })
        lead.active = False
        self.change()
        self.assertFalse(self.projects[2].with_user(self.user).has_access('read'))
        self.assertFalse(lead.with_user(self.user).has_access('read'))

    def test_unknown_identity_and_second_department_fail_closed(self):
        self.change()
        self.assertTrue(self.projects[2].with_user(self.user).has_access('read'))
        alternate = self.env['tp.report.assignment'].create({
            'name': 'Synthetic additional department', 'user_id': self.user.id,
            'company_id': self.company.id, 'department_id': self.departments[1].id,
            'capability': 'read', 'reason': 'Synthetic multiple departments',
        })
        self.assertFalse(self.user.with_user(self.user)._tp_delegated_other_department(
            self.company, self.departments[1]))
        alternate.department_id = False
        self.env.transaction.invalidate_access_cache()
        self.assertFalse(self.projects[2].with_user(self.user).has_access('read'))

    def test_plain_internal_recipient_can_use_foreign_contract_workflow(self):
        self.user.group_ids = [Command.set([self.env.ref('base.group_user').id])]
        self.change()
        result = self.model('tp.contract.workflow')._tp_run('create_contract', {
            'project_id': self.projects[2].id, 'code': 'AD-PLAIN-INTERNAL',
            'name': 'Synthetic plain internal delegated contract', 'contract_type': 'owner',
            'currency': self.company.currency_id.name,
        }, key='synthetic-ad-plain-internal')
        self.assertTrue(result['contract'].has_access('read'))
        self.assertFalse(self.user.has_group('tp_core.group_user'))
        self.assertFalse(self.user.has_group('base.group_system'))

    def test_admin_assignment_source_transfer_refreshes_scope(self):
        self.change()
        self.assertTrue(self.projects[2].with_user(self.user).has_access('read'))
        previous_revision = self.user.tp_admin_scope_revision
        self.projects[0].tp_department_id = self.departments[1]
        self.user.invalidate_recordset(['tp_admin_scope_revision'])
        self.assertGreater(self.user.tp_admin_scope_revision, previous_revision)
        self.env.transaction.invalidate_access_cache()
        self.assertFalse(self.projects[2].with_user(self.user).has_access('read'))
        self.assertTrue(self.projects[0].with_user(self.user).has_access('read'))

    def test_source_transfer_and_nested_grants_not_opened(self):
        self.change()
        target = self.projects[2].with_user(self.user)
        for values in ({'tp_department_id': self.departments[0].id},
                       {'tp_assignment_ids': [Command.create({'user_id': self.user.id, 'role': 'coordinator'})]},
                       {'tp_managed': False}):
            with self.assertRaises(AccessError):
                target.write(values)
        self.assertEqual(self.projects[2].tp_department_id, self.departments[1])

    def test_grant_does_not_widen_business_groups_or_admin_authority(self):
        groups = self.user.group_ids
        self.change()
        self.assertEqual(self.user.group_ids, groups)
        self.assertFalse(self.user.has_group('base.group_system'))
        self.assertFalse(self.user.has_group('tp_core.group_manager'))
        self.assertFalse(self.model('res.users').get_tp_admin_capabilities()['can_manage_delegation'])
        self.assertFalse(self.model('ir.config_parameter').has_access('write'))
        self.assertEqual(self.employee.with_user(self.admin).tp_admin_level, 'delegated')
        self.change('revoke')
        self.assertEqual(self.employee.with_user(self.admin).tp_admin_level, 'business')
