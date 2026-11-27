from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTpOrganizationSecurityAcl(TransactionCase):
    """AC-A03-0015: Verify unified Odoo 20 ir.access.csv restriction rows block regular staff at ORM level."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({'name': 'Synthetic ACL Check Co'})
        cls.staff_user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Synthetic Regular Staff ACL',
            'login': 'synthetic.org.acl.staff',
            'company_id': cls.company.id,
            'company_ids': [Command.set([cls.company.id])],
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })

    def test_regular_staff_blocked_from_import_and_audit_models(self):
        for model_name in ('tp.hr.import.batch', 'tp.hr.import.line', 'tp.hr.employee.audit'):
            scoped = self.env[model_name].with_user(self.staff_user).with_company(self.company)
            with self.assertRaises(AccessError):
                scoped.search_read([], ['id'])
            with self.assertRaises(AccessError):
                scoped.search([])
            with self.assertRaises(AccessError):
                scoped.check_access('read')
