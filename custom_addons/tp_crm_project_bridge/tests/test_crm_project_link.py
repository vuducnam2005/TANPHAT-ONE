from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestCrmProjectLink(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        groups = 'tp_core.group_user,project.group_project_user,sales_team.group_sale_salesman_all_leads'
        cls.seller = new_test_user(cls.env, login='bridge_seller', groups=groups, company_id=cls.company.id)
        cls.outside = new_test_user(cls.env, login='bridge_outside', groups=groups, company_id=cls.company.id)
        cls.reader = new_test_user(cls.env, login='bridge_reader', groups='tp_core.group_user,project.group_project_user', company_id=cls.company.id)
        cls.partner = cls.env['res.partner'].create({'name': 'Bridge fictional customer'})
        cls.other_partner = cls.env['res.partner'].create({'name': 'Bridge other fictional customer'})
        cls.project = cls.env['project.project'].create({
            'name': 'Bridge protected project', 'company_id': cls.company.id,
            'partner_id': cls.partner.id, 'tp_managed': True, 'tp_code': 'BRIDGE-TEST',
        })
        for user in (cls.seller, cls.reader):
            cls.env['tp.project.assignment'].create({'project_id': cls.project.id, 'user_id': user.id})
        cls.lead = cls.env['crm.lead'].create({
            'name': 'Bridge protected opportunity', 'company_id': cls.company.id,
            'partner_id': cls.partner.id, 'tp_project_id': cls.project.id,
        })

    def test_linked_scope_positive_and_view(self):
        self.assertEqual(self.lead.with_user(self.seller).read(['tp_project_id'])[0]['tp_project_id'][0], self.project.id)
        self.assertIn('tp_project_id', self.env['crm.lead'].with_user(self.seller).get_view(view_type='form')['arch'])
        self.assertEqual(self.project.with_user(self.reader).read(['name'])[0]['id'], self.project.id)

    def test_crm_outside_cannot_read_search_group_or_clear(self):
        leads = self.env['crm.lead'].with_user(self.outside)
        self.assertFalse(leads.search([('id', '=', self.lead.id)]))
        self.assertFalse(leads.name_search('Bridge protected opportunity'))
        self.assertFalse(leads._read_group([('id', '=', self.lead.id)], ['tp_project_id'], ['__count']))
        for operation in (lambda: self.lead.with_user(self.outside).read(['tp_project_id']),
                          lambda: self.lead.with_user(self.outside).write({'tp_project_id': False})):
            with self.assertRaises(AccessError), self.cr.savepoint():
                operation()
        self.assertFalse(self.env['project.project'].with_user(self.outside).name_search('Bridge protected project'))

    def test_project_reader_has_no_crm_access(self):
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.lead.with_user(self.reader).read(['name', 'tp_project_id'])

    def test_cannot_link_unreadable_project(self):
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env['crm.lead'].with_user(self.outside).create({
                'name': 'Forbidden link', 'company_id': self.company.id,
                'partner_id': self.partner.id, 'tp_project_id': self.project.id,
            })
        unlinked = self.env['crm.lead'].with_user(self.outside).create({
            'name': 'Unlinked own opportunity', 'company_id': self.company.id, 'partner_id': self.partner.id,
        })
        with self.assertRaises(AccessError), self.cr.savepoint():
            unlinked.write({'tp_project_id': self.project.id})

    def test_customer_and_company_integrity(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.lead.write({'partner_id': self.other_partner.id})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.project.write({'partner_id': self.other_partner.id})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.lead.write({'company_id': False})
        company = self.env['res.company'].create({'name': 'Bridge other fake company'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.lead.write({'company_id': company.id})

    def test_unlinked_native_and_copy(self):
        copied = self.lead.copy()
        self.assertFalse(copied.tp_project_id)
        self.assertTrue(copied.with_user(self.outside).read(['name']))
        self.assertFalse(self.project.with_user(self.reader)._fields.get('tp_crm_ids'))

    def test_project_deletion_restricted(self):
        self.project.collaborator_ids.unlink()
        with self.assertRaises(IntegrityError) as raised, self.cr.savepoint():
            self.project.unlink()
        self.assertEqual(raised.exception.diag.constraint_name, 'crm_lead_tp_project_id_fkey')
