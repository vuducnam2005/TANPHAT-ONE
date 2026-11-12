from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestOpportunityAccess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.department = cls.env['hr.department'].create({'name': 'Synthetic KD002', 'company_id': cls.env.company.id})
        cls.partner = cls.env['res.partner'].create({'name': 'Synthetic KD002 client'})
        cls.projects = cls.env['project.project'].create([{'name': 'Synthetic scope ' + str(i), 'tp_managed': True,
            'tp_code': 'KD002-TEST-' + str(i), 'company_id': cls.env.company.id, 'partner_id': cls.partner.id,
            'tp_department_id': cls.department.id} for i in range(2)])
        cls.owner = new_test_user(cls.env, login='kd002_owner', groups='tp_kd_workspace.group_scoped_staff')
        cls.other = new_test_user(cls.env, login='kd002_other', groups='tp_kd_workspace.group_scoped_staff')
        cls.support = new_test_user(cls.env, login='kd002_support', groups='tp_kd_workspace.group_scoped_staff')
        cls.grants = cls.env['tp.kd.grant']
        for user in (cls.owner, cls.other, cls.support):
            cls.env['tp.project.assignment'].create({'project_id': cls.projects[0].id, 'user_id': user.id})
            cls.grants |= cls.env['tp.kd.grant'].create({'project_id': cls.projects[0].id, 'department_id': cls.department.id,
                'user_id': user.id, 'domain': 'opportunity', 'capability': 'prepare', 'reason': 'Synthetic regression'})
        cls.money = cls.env['tp.project.grant'].create({'project_id': cls.projects[0].id, 'user_id': cls.owner.id,
            'capability': 'financial_read', 'reason': 'Synthetic regression'})

    def make(self, user=None, **extra):
        return self.env['crm.lead'].with_user(user or self.owner).create({'name': 'Synthetic KD002 lead',
            'type': 'opportunity', 'company_id': self.env.company.id, 'partner_id': self.partner.id,
            'tp_project_id': self.projects[0].id, 'user_id': (user or self.owner).id,
            'kd_source': 'synthetic', 'kd_scope': 'synthetic', 'kd_checklist': 'synthetic',
            'kd_deadline': '2030-01-01', 'kd_receipt': 'synthetic', **extra})

    def test_prepare_is_not_submit_and_owner_is_required(self):
        lead = self.make(self.support)
        lead.action_kd_prepare()
        with self.assertRaises(AccessError):
            lead.action_kd_record_submission()
        with self.assertRaises(AccessError):
            lead.with_user(self.other).write({'kd_scope': 'forged'})
        grant = self.env['tp.kd.grant'].create({'project_id': self.projects[0].id, 'department_id': self.department.id,
            'user_id': self.support.id, 'domain': 'opportunity', 'capability': 'submit', 'reason': 'Synthetic explicit submit'})
        self.grants.filtered(lambda g: g.user_id == self.support).active = False
        self.assertTrue(lead.kd_can_submit)
        self.assertFalse(lead.kd_can_edit)
        lead.action_kd_record_submission()
        with self.assertRaises(UserError):
            lead.write({'kd_receipt': 'changed evidence'})
        grant.active = False
        with self.assertRaises(AccessError):
            lead.action_kd_record_submission()

    def test_scope_defaults_context_copy_batch_and_state(self):
        lead = self.make()
        for vals in ({'tp_project_id': False}, {'tp_project_id': self.projects[1].id}, {'user_id': self.other.id},
                     {'company_id': False}, {'team_id': False, 'user_id': False}, {'active': False}):
            with self.assertRaises((AccessError, UserError)), self.env.cr.savepoint():
                lead.write(vals)
        with self.assertRaises(UserError):
            lead.copy()
        with self.assertRaises(AccessError):
            lead.unlink()
        with self.assertRaises(UserError):
            lead.with_context(_kd_internal=True).write({'kd_bid_state': 'submitted'})
        with self.assertRaises((AccessError, UserError)), self.env.cr.savepoint():
            self.make(self.support, kd_bid_state='submitted')
        outside = self.env['crm.lead'].create({'name': 'Synthetic outside', 'tp_project_id': self.projects[1].id,
            'company_id': self.env.company.id, 'partner_id': self.partner.id})
        self.assertNotIn(outside.id, self.env['crm.lead'].with_user(self.owner).search([]).ids)
        with self.assertRaises(AccessError):
            (lead | outside.with_user(self.owner)).read(['name'])

    def test_money_native_paths_and_live_revoke(self):
        lead = self.make()
        lead.sudo().expected_revenue = 7654321
        lead.invalidate_recordset()
        self.assertEqual(lead.read(['expected_revenue'])[0]['expected_revenue'], 7654321)
        support = lead.with_user(self.support)
        for field in ('expected_revenue', 'prorated_revenue', 'recurring_revenue', 'recurring_revenue_monthly',
                      'recurring_revenue_monthly_prorated', 'recurring_revenue_prorated'):
            with self.assertRaises(AccessError):
                support.read([field])
            with self.assertRaises(AccessError):
                support.search([(field, '>', 0)])
            with self.assertRaises(AccessError):
                support.search([], order=field)
            with self.assertRaises(AccessError):
                support.export_data([field])
            with self.assertRaises(AccessError):
                support._read_group([], [], [field + ':sum'])
        self.money.active = False
        with self.assertRaises(AccessError):
            lead.read(['expected_revenue'])
        with self.assertRaises(AccessError):
            _ = lead.expected_revenue
        self.money.write({'active': True, 'date_end': '2000-01-01'})
        with self.assertRaises(AccessError):
            lead.read(['expected_revenue'])
        self.money.write({'date_end': False})
        assignment = self.env['tp.project.assignment'].search([('user_id', '=', self.owner.id)])
        assignment.active = False
        with self.assertRaises(AccessError):
            lead.read(['expected_revenue'])

    def test_preproject_native_team_owner_department_and_revoke(self):
        team = self.env['crm.team'].create({'name': 'Synthetic pre-project', 'company_id': self.env.company.id,
            'kd_department_id': self.department.id, 'member_ids': [Command.set(self.owner.ids)]})
        lead = self.make(tp_project_id=False, team_id=team.id)
        self.assertIn(lead, lead.search([]))
        self.assertNotIn(lead.id, lead.with_user(self.other).search([]).ids)
        lead.action_kd_prepare()
        with self.assertRaises(AccessError):
            lead.read(['expected_revenue'])
        team.member_ids = [Command.clear()]
        self.env.transaction.invalidate_access_cache()
        self.assertNotIn(lead.id, lead.search([]).ids)

    def test_files_and_chatter_financial_parent(self):
        lead = self.make()
        attachment = self.env['ir.attachment'].create({'name': 'Synthetic CRM file', 'res_model': 'crm.lead',
            'res_id': lead.id, 'type': 'binary', 'raw': b'synthetic money 7654321'})
        self.assertTrue(attachment.with_user(self.owner).has_access('read'))
        message = self.env['mail.message'].create({'model': 'crm.lead', 'res_id': lead.id,
            'message_type': 'comment', 'body': 'Synthetic financial 7654321'})
        self.assertTrue(message.with_user(self.owner).read(['body']))
        with self.assertRaises(AccessError):
            message.with_user(self.support).read(['body'])
        with self.assertRaises(AccessError):
            attachment.with_user(self.other).write({'raw': b'forged'})
        with self.assertRaises(AccessError):
            attachment.with_user(self.support).write({'raw': b'forged'})
        with self.assertRaises(AccessError):
            attachment.with_user(self.support).read(['raw'])
        self.money.active = False
        with self.assertRaises(AccessError):
            attachment.with_user(self.owner).read(['raw'])

    def test_money_editor_rechecks_scope_owner_and_grants(self):
        lead = self.make()
        with self.assertRaises(AccessError):
            lead.action_kd_edit_money()
        self.env['tp.project.grant'].create({'project_id': self.projects[0].id, 'user_id': self.owner.id,
            'capability': 'financial_draft_edit', 'department_id': self.department.id, 'reason': 'Synthetic edit'})
        action = lead.action_kd_edit_money()
        wizard = self.env['tp.kd.opportunity.money'].with_user(self.owner).browse(action['res_id'])
        wizard.amount = 9876543
        wizard.action_confirm()
        self.assertEqual(lead.expected_revenue, 9876543)
        self.assertIn('9', lead.kd_money_display)
        self.money.active = False
        with self.assertRaises(AccessError):
            wizard.action_confirm()
        self.assertEqual(lead.sudo().expected_revenue, 9876543)

    def test_binary_tokens_and_public_files_keep_parent_scope(self):
        lead = self.make()
        attachment = self.env['ir.attachment'].create({'name': 'Synthetic shared file', 'res_model': 'crm.lead',
            'res_id': lead.id, 'raw': b'synthetic money', 'access_token': 'synthetic-kd002-token'})
        for user in (self.support, self.other):
            binary = self.env['ir.binary'].with_user(user)
            with self.assertRaises(AccessError):
                binary._find_record(res_id=attachment.id, access_token='synthetic-kd002-token', field='raw')
            attachment.public = True
            with self.assertRaises(AccessError):
                binary._find_record(res_id=attachment.id, field='raw')
        allowed = self.env['ir.binary'].with_user(self.owner)._find_record(
            res_id=attachment.id, access_token='synthetic-kd002-token', field='raw')
        self.assertEqual(allowed.id, attachment.id)
        self.money.active = False
        with self.assertRaises(AccessError):
            self.env['ir.binary'].with_user(self.owner)._find_record(
                res_id=attachment.id, access_token='synthetic-kd002-token', field='raw')

    def test_query_inference_mixed_grants_and_related_and_company(self):
        lead = self.make()
        lead.sudo().expected_revenue = 12
        self.env['tp.project.assignment'].create({'project_id': self.projects[1].id, 'user_id': self.owner.id})
        outside_money = self.env['crm.lead'].create({'name': 'Synthetic metadata-only', 'company_id': self.env.company.id,
            'partner_id': self.partner.id, 'tp_project_id': self.projects[1].id, 'expected_revenue': 99999})
        crm = self.env['crm.lead'].with_user(self.owner)
        self.assertIn(outside_money.id, crm.search([]).ids)
        for domain in ([('expected_revenue', '>', 1)], ['!', ('expected_revenue', '=', 0)],
                       ['|', ('expected_revenue', '>', 1), ('id', '=', outside_money.id)]):
            self.assertNotIn(outside_money.id, crm.search(domain).ids)
        self.assertNotIn(outside_money.id, crm.search([], order='expected_revenue desc').ids)
        self.assertEqual(crm._read_group([('id', 'in', (lead | outside_money).ids)], [], ['expected_revenue:sum']), [(12.0,)])
        with self.assertRaises(AccessError):
            (lead | outside_money.with_user(self.owner)).export_data(['expected_revenue'])
        company = self.env['res.company'].create({'name': 'Synthetic company KD002'})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.make(company_id=company.id)
        department = self.env['hr.department'].create({'name': 'Synthetic other department', 'company_id': self.env.company.id})
        team = self.env['crm.team'].create({'name': 'Synthetic other unit', 'company_id': self.env.company.id,
            'kd_department_id': department.id, 'member_ids': [Command.set(self.owner.ids)]})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.make(tp_project_id=False, team_id=team.id)
