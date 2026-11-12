from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestDepartmentHeadScope(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.head = new_test_user(cls.env, login='head_dynamic_scope', groups='tp_kd_workspace.group_scoped_staff')
        cls.staff = new_test_user(cls.env, login='head_scope_control', groups='tp_kd_workspace.group_scoped_staff')
        cls.department = cls.env['hr.department'].create({'name': 'Synthetic dynamic scope', 'company_id': cls.env.company.id})
        cls.other_department = cls.env['hr.department'].create({'name': 'Synthetic excluded scope', 'company_id': cls.env.company.id})
        cls.project = cls.env['project.project'].create({
            'name': 'Dynamic department dossier', 'tp_managed': True, 'tp_code': 'HEAD-DYN-001',
            'company_id': cls.env.company.id, 'tp_department_id': cls.department.id,
        })
        cls.team = cls.env['crm.team'].create({
            'name': 'Synthetic scoped team', 'company_id': cls.env.company.id, 'kd_department_id': cls.department.id,
        })
        cls.other_team = cls.env['crm.team'].create({
            'name': 'Synthetic excluded team', 'company_id': cls.env.company.id, 'kd_department_id': cls.other_department.id,
        })
        cls.role = cls.env['tp.kd.department.role'].create({
            'user_id': cls.head.id, 'company_id': cls.env.company.id, 'department_id': cls.department.id,
            'reason': 'Synthetic HEAD acceptance',
        })

    def test_head_scope_does_not_need_project_grants_or_native_team_membership(self):
        role = self.env['tp.kd.department.role'].with_user(self.head)
        self.assertEqual(role._project_ids(), self.project.ids)
        self.assertEqual(role._team_ids(), self.team.ids)
        self.assertEqual(role._head_users(self.project), self.head)
        project = self.project.with_user(self.head)
        self.assertTrue(project.has_access('read'))
        grant = self.env['tp.kd.grant'].with_user(self.head)
        for domain in grant._fields['domain'].get_values(self.env):
            for capability in ('prepare', 'submit', 'review'):
                self.assertTrue(grant._has(project, domain, capability), (domain, capability))
        self.assertFalse(grant._has(project, 'not_a_business_domain', 'prepare'))
        self.assertFalse(grant._has(project, 'opportunity', 'approve_legal'))
        self.assertFalse(self.project.with_user(self.staff).has_access('read'))
        self.assertFalse(self.env['tp.project.grant'].search([('user_id', '=', self.head.id)]))
        self.assertFalse(self.env['tp.kd.grant'].search([('user_id', '=', self.head.id)]))
        for capability in ('financial_read', 'financial_draft_edit', 'contract_draft_edit', 'contract_submit', 'contract_review_commercial'):
            self.assertTrue(self.env['tp.project.grant'].with_user(self.head)._tp_has_capability(
                project, capability, self.department if capability != 'financial_read' else None,
            ))
        self.assertFalse(self.env['tp.project.grant'].with_user(self.head)._tp_has_capability(project, 'financial_draft_edit', self.other_department))
        self.role.write({'active': False, 'reason': 'Synthetic immediate revoke'})
        self.assertFalse(project.has_access('read'))
        self.assertFalse(grant._has(project, 'opportunity', 'prepare'))
        self.assertFalse(role._team_ids())
        self.assertFalse(role._head_users(self.project))
        with self.assertRaises(AccessError):
            project.read(['name'])

    def test_legacy_assignment_and_grants_are_preserved_for_other_staff(self):
        self.env['tp.project.assignment'].create({'project_id': self.project.id, 'user_id': self.staff.id})
        self.env['tp.kd.grant'].create({
            'project_id': self.project.id, 'user_id': self.staff.id, 'department_id': self.department.id,
            'domain': 'opportunity', 'capability': 'prepare', 'reason': 'Synthetic control baseline',
        })
        project = self.project.with_user(self.staff)
        grant = self.env['tp.kd.grant'].with_user(self.staff)
        self.assertTrue(project.has_access('read'))
        self.assertTrue(grant._has(project, 'opportunity', 'prepare'))
        self.assertFalse(grant._has(project, 'opportunity', 'submit'))
        self.assertFalse(project.tp_financial_read_granted)
        self.role.write({'active': False, 'reason': 'Synthetic HEAD revoke preserves staff'})
        self.assertTrue(project.has_access('read'))
        self.assertTrue(grant._has(project, 'opportunity', 'prepare'))
        self.assertFalse(project._tp_head_allowed())

    def test_head_contact_guard_preserves_own_profile_and_business_command(self):
        partner = self.env['res.partner'].create({'name': 'Synthetic external directory contact'})
        bank = self.env['res.partner.bank'].create({'partner_id': partner.id, 'account_number': 'SYNTHETIC-ONLY'})
        actor = partner.with_user(self.head)
        for values in ({'name': 'Direct outside edit'}, {'vat': 'SYNTHETIC-TAX'}, {'bank_ids': [(4, bank.id)]}):
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                actor.write(values)
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.env['res.partner'].with_user(self.head).create({'name': 'Direct new contact'})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            bank.with_user(self.head).write({'account_number': 'FORBIDDEN'})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            actor.unlink()
        own = self.head.partner_id.with_user(self.head)
        own.write({'phone': 'Synthetic self-service'})
        self.assertEqual(own.phone, 'Synthetic self-service')
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            own.write({'vat': 'FORBIDDEN-OWN-TAX'})
        # The control actor retains its native self-service rights.
        other_own = self.staff.partner_id.with_user(self.staff)
        other_own.write({'phone': 'Synthetic staff self-service'})
        self.assertEqual(other_own.phone, 'Synthetic staff self-service')
        command = self.env['tp.kd.head.command'].with_user(self.head).create({
            'operation': 'partner', 'project_id': self.project.id, 'name': 'Synthetic scoped business contact',
            'reason': 'Synthetic scoped contact command',
        })
        command.action_confirm()
        self.assertEqual(command.result_partner_id.name, 'Synthetic scoped business contact')
