"""Department HEAD commands use a normal actor, including future project data."""
from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import new_test_user
from odoo.tools import BinaryBytes

from .test_opportunity_access import TestOpportunityAccess
from odoo.addons.mail.tools.discuss import Store


@tagged('post_install', '-at_install')
class TestHeadOperations(TestOpportunityAccess):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.head = new_test_user(cls.env, login='synthetic_head_ops', groups='tp_kd_workspace.group_scoped_staff')
        cls.role = cls.env['tp.kd.department.role'].create({
            'user_id': cls.head.id, 'company_id': cls.env.company.id,
            'department_id': cls.department.id, 'reason': 'Synthetic authorized HEAD',
        })
        cls.team = cls.env['crm.team'].create({'name': 'Synthetic HEAD team',
            'company_id': cls.env.company.id, 'kd_department_id': cls.department.id,
            'member_ids': [Command.set((cls.owner | cls.head | cls.support).ids)]})

    def test_new_project_command_and_dynamic_staff_project(self):
        head = self.env['tp.kd.head.command'].with_user(self.head)
        cmd = head.create({'operation': 'project_create', 'company_id': self.env.company.id,
            'department_id': self.department.id, 'name': 'Synthetic new HEAD project',
            'code': 'HEAD-NEW-001', 'reason': 'Synthetic intake'})
        result = cmd.action_confirm()
        project = self.env['project.project'].with_user(self.head).browse(result['res_id'])
        self.assertTrue(project._tp_head_allowed())
        self.assertTrue(project.action_kd_management())
        self.assertTrue(project.action_kd_governance())
        later = self.env['project.project'].create({'name': 'Synthetic later project',
            'tp_managed': True, 'tp_code': 'HEAD-LATER-001', 'company_id': self.env.company.id,
            'tp_department_id': self.department.id})
        self.assertIn(later.id, project.search([]).ids)
        self.assertNotIn(later.id, later.with_user(self.support).search([]).ids)
        with self.assertRaises(AccessError):
            head.with_user(self.support).create({'operation': 'project_create',
                'company_id': self.env.company.id, 'department_id': self.department.id,
                'name': 'Forged', 'code': 'HEAD-FORGED', 'reason': 'Forged'})

    def test_preproject_other_owner_money_files_and_live_revoke(self):
        lead = self.make(tp_project_id=False, team_id=self.team.id)
        actor = lead.with_user(self.head)
        self.assertTrue(actor.has_access('read'))
        actor.write({'kd_scope': 'HEAD intervened', 'kd_head_version': actor.kd_head_version,
            'kd_intervention_reason': 'Synthetic correction'})
        wizard = self.env['tp.kd.opportunity.money'].with_user(self.head).browse(
            actor.action_kd_edit_money()['res_id'])
        wizard.write({'amount': 0, 'reason': 'Synthetic zero estimate'})
        wizard.action_confirm()
        self.assertEqual(actor.expected_revenue, 0)
        content = self.env['tp.kd.head.command'].with_user(self.head).create({
            'operation': 'lead_document_add', 'lead_id': lead.id, 'file_name': 'Synthetic preproject.txt',
            'file': BinaryBytes(b'HEAD synthetic only'), 'reason': 'Synthetic supporting evidence'})
        content.action_confirm()
        attachment = actor.kd_head_document_ids
        self.assertEqual(bytes(attachment.raw), b'HEAD synthetic only')
        self.role.write({'active': False, 'reason': 'Synthetic revocation'})
        with self.assertRaises(AccessError):
            attachment.read(['raw'])
        with self.assertRaises(AccessError):
            actor.read(['expected_revenue'])

    def test_crm_content_commands_reason_version_replay_and_archive(self):
        actor = self.make(tp_project_id=False, team_id=self.team.id).with_user(self.head)
        commands = self.env['tp.kd.head.command'].with_user(self.head)
        value = {'operation': 'lead_document_add', 'lead_id': actor.id,
            'file_name': 'Synthetic command.txt', 'file': BinaryBytes(b'HEAD content evidence')}
        missing_reason = commands.create({**value, 'reason': ' '})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            missing_reason.action_confirm()
        upload = commands.create({**value, 'reason': 'Synthetic file reason'})
        stale = commands.create({'operation': 'lead_comment', 'lead_id': actor.id,
            'scope': 'Synthetic old version', 'reason': 'Synthetic stale comment'})
        initial = actor.kd_head_version
        upload.action_confirm()
        upload.action_confirm()
        self.assertEqual(actor.kd_head_version, initial + 1)
        attachment = actor._head_documents()
        self.assertEqual(len(attachment), 1)
        self.assertEqual(bytes(attachment.raw), b'HEAD content evidence')
        with self.assertRaises(UserError), self.env.cr.savepoint():
            stale.action_confirm()
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env['ir.attachment'].with_user(self.head).create({
                'res_model': 'crm.lead', 'res_id': actor.id, 'name': 'Unaudited.txt', 'raw': b'No'})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            attachment.write({'name': 'Unaudited rename'})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            actor.message_post(body='Unaudited chatter')
        comment = commands.create({'operation': 'lead_comment', 'lead_id': actor.id,
            'scope': '<Synthetic plain text>', 'reason': 'Synthetic comment reason'})
        comment.action_confirm()
        message = actor.kd_head_message_ids
        self.assertEqual(message.author_id, self.head.partner_id)
        self.assertIn('&lt;Synthetic plain text&gt;', str(message.body))
        self.assertFalse(message.notification_ids)
        foreign = self.make(tp_project_id=False, team_id=self.team.id)
        invalid = commands.create({'operation': 'lead_document_remove', 'lead_id': foreign.id,
            'document_id': attachment.id, 'reason': 'Synthetic wrong parent'})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            invalid.action_confirm()
        checksum = attachment.checksum
        remove = commands.create({'operation': 'lead_document_remove', 'lead_id': actor.id,
            'document_id': attachment.id, 'reason': 'Synthetic archive reason'})
        remove.action_confirm()
        self.assertFalse(actor._head_documents())
        self.assertEqual(attachment.checksum, checksum)
        self.assertEqual(bytes(attachment.raw), b'HEAD content evidence')
        # Older native chatter files remain eligible through their message parent.
        old_file = self.env['ir.attachment'].create({'res_model': 'mail.message', 'res_id': message.id,
            'name': 'Synthetic older chatter.txt', 'raw': b'Older content'})
        archive_old = commands.create({'operation': 'lead_document_remove', 'lead_id': actor.id,
            'document_id': old_file.id, 'reason': 'Synthetic older chatter archive'})
        self.assertIn(old_file.id, archive_old.eligible_document_ids.ids)
        archive_old.action_confirm()
        self.assertTrue(old_file.kd_head_archived)
        revoked = commands.create({'operation': 'lead_comment', 'lead_id': actor.id,
            'scope': 'Synthetic revoked', 'reason': 'Synthetic forbidden comment'})
        self.role.write({'active': False, 'reason': 'Synthetic immediate revoke'})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            revoked.action_confirm()

    def test_other_draft_reason_stale_and_transfer_audit(self):
        actor = self.make().with_user(self.head)
        initial = actor.kd_head_version
        with self.assertRaises(UserError):
            actor.write({'kd_scope': 'No reason', 'kd_head_version': initial})
        actor.write({'kd_scope': 'Audited', 'kd_head_version': initial,
            'kd_intervention_reason': 'Synthetic reason'})
        with self.assertRaises(UserError):
            actor.write({'kd_scope': 'Stale', 'kd_head_version': initial,
                'kd_intervention_reason': 'Synthetic reason'})
        cmd = self.env['tp.kd.head.command'].with_user(self.head).create({
            'operation': 'lead_assign', 'lead_id': actor.id, 'owner_id': self.support.id,
            'reason': 'Synthetic handover'})
        cmd.action_confirm()
        self.assertEqual(actor.user_id, self.support)
        self.assertGreaterEqual(self.env['tp.kd.head.event'].with_user(self.head).search_count([
            ('lead_id', '=', actor.id)]), 2)
        actor.action_kd_prepare()
        actor.action_kd_record_submission()
        with self.assertRaises(UserError):
            actor.write({'kd_scope': 'Locked', 'kd_head_version': actor.kd_head_version,
                'kd_intervention_reason': 'Forbidden'})

    def test_task_progress_on_behalf_preserves_assignee(self):
        p = self.projects[0].with_user(self.head)
        wizard = self.env['tp.task.command'].with_user(self.head).create({
            'project_id': p.id, 'operation': 'create'})
        wizard.write({'name': 'Synthetic HEAD task', 'deliverable': 'Synthetic output',
            'responsible_id': self.owner.id, 'reason': 'Synthetic assignment'})
        wizard.action_confirm()
        task = self.env['project.task'].with_user(self.head).search([('project_id', '=', p.id),
            ('name', '=', 'Synthetic HEAD task')])
        progress = self.env['tp.task.command'].with_user(self.head).create({
            'project_id': p.id, 'task_id': task.id, 'operation': 'progress'})
        progress.write({'target_state': '1_done', 'reason': 'Synthetic on behalf'})
        progress.action_confirm()
        self.assertEqual(task.user_ids, self.owner)
        event = self.env['tp.task.update'].with_user(self.head).search([
            ('task_id', '=', task.id), ('operation', '=', 'progress')])
        self.assertEqual(event.actor_id, self.head)

    def test_command_context_defaults_are_checked_and_retries_do_not_duplicate(self):
        command = self.env['tp.kd.head.command'].with_user(self.head).with_context(
            default_operation='project_create', default_company_id=self.env.company.id,
            default_department_id=self.department.id,
        )
        values = {'name': 'Synthetic default command', 'code': 'HEAD-DEFAULT-CHECK', 'reason': 'Synthetic intake'}
        wizard = command.create(values)
        first = wizard.action_confirm()
        self.assertEqual(first['res_id'], wizard.action_confirm()['res_id'])
        self.assertEqual(self.env['project.project'].search_count([('tp_code', '=', values['code'])]), 1)
        wizard.name = 'Changed after confirmation'
        with self.assertRaises(UserError):
            wizard.action_confirm()
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            command.with_context(default_result_project_id=self.projects[0].id).create(values)
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            command.with_context(default_project_id=self.projects[0].id).create(values)
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            command.with_context(default_department_id=False).create(values)

    def test_new_project_assignment_requires_existing_security_scope(self):
        command = self.env['tp.kd.head.command'].with_user(self.head)
        values = {'operation': 'project_create', 'company_id': self.env.company.id,
            'department_id': self.department.id, 'name': 'Synthetic restricted delegation',
            'code': 'HEAD-DELEGATION', 'reason': 'Synthetic create'}
        denied = command.create({**values, 'owner_id': self.support.id})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            denied.action_confirm()
        created = command.create(values)
        project = self.env['project.project'].with_user(self.head).browse(created.action_confirm()['res_id'])
        task_command = self.env['tp.task.command'].with_user(self.head)
        task = task_command.create({'operation': 'create', 'project_id': project.id})
        task.write({'name': 'Synthetic no new access', 'deliverable': 'Synthetic output',
            'responsible_id': self.support.id, 'reason': 'Synthetic denied recipient'})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            task.action_confirm()
        task.write({'responsible_id': self.head.id, 'reason': 'Synthetic valid HEAD recipient'})
        task.action_confirm()
        created_task = self.env['project.task'].with_user(self.head).search([
            ('project_id', '=', project.id), ('name', '=', 'Synthetic no new access')])
        self.assertEqual(created_task.user_ids, self.head)
        self.assertFalse(project.with_user(self.support).has_access('read'))

    def test_partner_update_respects_shared_uses_and_create_retry(self):
        command = self.env['tp.kd.head.command'].with_user(self.head)
        wizard = command.create({'operation': 'partner', 'project_id': self.projects[0].id,
            'name': 'Synthetic created contact', 'email': 'synthetic@example.invalid', 'reason': 'Synthetic new business contact'})
        wizard.action_confirm()
        result = wizard.result_partner_id
        wizard.action_confirm()
        self.assertEqual(wizard.result_partner_id, result)
        self.assertEqual(self.env['res.partner'].search_count([('name', '=', 'Synthetic created contact')]), 1)
        other_department = self.env['hr.department'].create({'name': 'Synthetic external partner use', 'company_id': self.env.company.id})
        self.env['project.project'].create({'name': 'External project with shared partner',
            'tp_managed': True, 'tp_code': 'HEAD-PARTNER-EXTERNAL', 'company_id': self.env.company.id,
            'tp_department_id': other_department.id, 'partner_id': self.partner.id})
        edit = command.create({'operation': 'partner', 'project_id': self.projects[0].id,
            'partner_id': self.partner.id, 'name': 'Would change shared directory', 'reason': 'Synthetic forbidden edit'})
        with self.assertRaises(AccessError):
            edit.action_confirm()
        self.assertEqual(self.partner.name, 'Synthetic KD002 client')

    def test_create_recipients_require_existing_project_or_preproject_scope(self):
        outsider = new_test_user(self.env, login='synthetic_head_outside_recipient', groups='tp_kd_workspace.group_scoped_staff')
        self.team.write({'member_ids': [Command.link(outsider.id)]})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.make(self.head, tp_project_id=False, team_id=self.team.id, user_id=outsider.id)
        lead = self.make(self.head, tp_project_id=False, team_id=self.team.id, user_id=self.support.id)
        self.assertEqual(lead.user_id, self.support)
        self.assertTrue(lead.with_user(self.support).has_access('read'))
        transfer = self.env['tp.kd.head.command'].with_user(self.head).create({
            'operation': 'lead_assign', 'lead_id': lead.id, 'owner_id': outsider.id,
            'reason': 'Synthetic team membership does not grant access'})
        self.assertNotIn(outsider, transfer.eligible_owner_ids)
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            transfer.action_confirm()
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.make(self.head, team_id=self.team.id, user_id=outsider.id)
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.make(self.head, team_id=self.team.id, user_id=False)
        linked = self.make(self.head, team_id=self.team.id, user_id=self.owner.id)
        self.assertEqual(linked.user_id, self.owner)
        packages = self.env['tp.bid.package'].with_user(self.head)
        self.assertFalse(packages.new().can_head_intervene)
        values = {'project_id': self.projects[0].id, 'code': 'HEAD-RECIPIENT-PACKAGE',
            'name': 'Synthetic scoped package', 'scope': 'Synthetic business scope'}
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            packages.create({**values, 'owner_id': outsider.id})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            packages.create({**values, 'version': 17})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            packages.with_context(default_version=17).create(values)
        package = packages.create({**values, 'owner_id': self.owner.id})
        self.assertEqual(package.owner_id, self.owner)
        old_version = package.version
        package.write({'code': 'HEAD-RECIPIENT-UPDATED', 'inviter_id': self.partner.id,
            'version': old_version, 'intervention_reason': 'Synthetic full business snapshot'})
        event = self.env['tp.kd.head.event'].with_user(self.head).search([
            ('project_id', '=', self.projects[0].id), ('operation', '=', 'bid_update')], limit=1)
        self.assertEqual(event.before_values['code'], values['code'])
        self.assertEqual(event.after_values['code'], 'HEAD-RECIPIENT-UPDATED')
        self.assertFalse(event.before_values['inviter_id'])
        self.assertEqual(event.after_values['inviter_id'], self.partner.id)
        self.assertEqual(package.version, old_version + 1)
        self.env['tp.kd.grant'].create({'project_id': self.projects[0].id, 'user_id': self.owner.id,
            'department_id': self.department.id, 'domain': 'bid', 'capability': 'prepare',
            'reason': 'Synthetic existing package preparer'})
        staff_package = package.with_user(self.owner)
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            staff_package.write({'version': 99})
        loaded_version = package.version
        staff_package.write({'scope': 'Synthetic simultaneous staff update'})
        self.assertEqual(package.version, loaded_version + 1)
        with self.assertRaises(UserError), self.env.cr.savepoint():
            package.write({'scope': 'Would overwrite staff update', 'version': loaded_version,
                'intervention_reason': 'Synthetic stale HEAD form'})
        self.assertEqual(package.scope, 'Synthetic simultaneous staff update')
        self.assertFalse(self.projects[0].with_user(outsider).has_access('read'))

    def test_native_chatter_head_flags_preserve_staff_and_recheck_revoke(self):
        lead = self.make()

        def thread_values(actor):
            data = Store().add(lead.with_user(actor), '_store_thread_fields', as_thread=True,
                fields_params={'request_list': []})._build_result()
            return data['mail.thread'][0]

        head = thread_values(self.head)
        self.assertTrue(head['tpKdHeadContentCommand'])
        self.assertFalse(head['hasWriteAccess'])
        self.assertFalse(head['canPostOnReadonly'])
        staff = thread_values(self.owner)
        self.assertFalse(staff['tpKdHeadContentCommand'])
        self.assertTrue(staff['hasWriteAccess'])
        self.role.write({'active': False, 'reason': 'Synthetic live chatter flag revocation'})
        self.assertFalse(thread_values(self.head)['tpKdHeadContentCommand'])
