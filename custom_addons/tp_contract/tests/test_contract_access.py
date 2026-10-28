from odoo import fields
from odoo.exceptions import AccessError, ValidationError

from .common import TpContractCommon

FINANCIAL_MODELS = ('tp.contract.line.amount', 'tp.approval.reference.amount')
METADATA_MODELS = ('tp.contract', 'tp.contract.revision', 'tp.contract.line', 'tp.approval.reference')


class TestContractAccess(TpContractCommon):
    def _amounts(self, user, project=None):
        domain = [('project_id', '=', project.id)] if project else []
        return self.env['tp.contract.line.amount'].with_user(user).search(domain)

    def test_metadata_reader_sees_assigned_contract_without_amounts(self):
        Contract = self.env['tp.contract'].with_user(self.reader)
        self.assertEqual(Contract.search([]), self.contract_a)
        self.assertEqual(self.contract_a.with_user(self.reader).revision_ids, self.original | self.amendment)
        self.assertEqual(len(self.amendment.with_user(self.reader).line_ids), 2)
        self.assertEqual(self.amendment.with_user(self.reader).approval_reference_ids, self.approval)
        self.assertFalse(self.project_a.with_user(self.reader).tp_financial_read_granted)
        for model in FINANCIAL_MODELS:
            records = self.env[model].with_user(self.reader)
            self.assertFalse(records.search([]), model)
            self.assertFalse(records.search_read([], ['amount']), model)
            self.assertFalse(records.read_group([], aggregates=['amount:sum'])[0][0], model)
        with self.assertRaises(AccessError):
            self.env['tp.contract.line.amount'].search([('line_id', '=', self.line_x.id)]).with_user(self.reader).read(['amount'])
        with self.assertRaises(AccessError):
            self.approval_amount.with_user(self.reader).read(['amount'])

    def test_native_aggregates_and_export_hide_amounts(self):
        Amount = self.env['tp.contract.line.amount'].with_user(self.reader)
        groups = Amount.read_group([], ['project_id'], ['amount:sum'])
        self.assertEqual(groups, [])
        # The export right does not widen record access to amounts.
        for user in (self.reader, self.finance_b):
            self._link_group(user, 'base.group_allow_export')
        reader_rows = self.env['tp.contract.line.amount'].with_user(self.reader).search([]).export_data(['amount'])['datas']
        self.assertEqual(reader_rows, [])
        export_rows = self.env['tp.contract.line.amount'].with_user(self.finance_b).search([]).export_data(['project_id', 'amount'])['datas']
        self.assertEqual(len(export_rows), 1)
        self.assertEqual(export_rows[0][1], 25.0)

    def test_cross_project_contract_is_hidden(self):
        self.assertFalse(self.env['tp.contract'].with_user(self.reader).search([('id', '=', self.contract_b.id)]))
        for record in (self.contract_b, self.revision_b, self.line_b):
            with self.assertRaises(AccessError):
                record.with_user(self.reader).read(['display_name'])
        self.assertFalse(self.env['tp.contract'].with_user(self.outsider).search([]))

    def test_metadata_on_a_and_financial_on_b_only(self):
        self.assertEqual(self.env['tp.contract'].with_user(self.finance_b).search([]), self.contract_a | self.contract_b)
        visible = self._amounts(self.finance_b)
        self.assertEqual(visible.line_id, self.line_b)
        self.assertFalse(self._amounts(self.finance_b, self.project_a))
        self.assertEqual(
            self.env['tp.contract.line.amount'].with_user(self.finance_b).read_group([], ['project_id'], ['amount:sum']),
            [(self.project_b.id, 25.0)],
        )
        self.assertFalse(self.env['tp.approval.reference.amount'].with_user(self.finance_b).search([]))
        with self.assertRaises(AccessError):
            self.approval_amount.with_user(self.finance_b).read(['amount'])

    def test_financial_grant_holder_reads_amounts_of_granted_project(self):
        self.assertEqual(len(self._amounts(self.finance_a)), 4)
        self.assertEqual(self.approval_amount.with_user(self.finance_a).amount, 110)
        self.assertTrue(self.project_a.with_user(self.finance_a).tp_financial_read_granted)

    def test_grant_without_project_scope_is_not_enough(self):
        self.env['tp.project.assignment'].search([
            ('project_id', '=', self.project_a.id), ('user_id', '=', self.finance_a.id),
        ]).active = False
        self.assertFalse(self._amounts(self.finance_a))
        self.assertFalse(self.env['tp.contract'].with_user(self.finance_a).search([]))

    def test_revoked_grant_applies_to_next_read(self):
        self.assertTrue(self._amounts(self.finance_a))
        self.grant_a.active = False
        self.assertFalse(self._amounts(self.finance_a))
        with self.assertRaises(AccessError):
            self.financial_doc.with_user(self.finance_a).read(['file'])

    def test_expired_grant_is_ignored(self):
        self.grant_a.date_end = fields.Date.subtract(fields.Date.context_today(self.grant_a), days=1)
        self.assertFalse(self._amounts(self.finance_a))
        self.grant_a.date_end = fields.Date.context_today(self.grant_a)
        self.assertTrue(self._amounts(self.finance_a))

    def test_platform_manager_and_admin_get_no_money_by_default(self):
        for user in (self.manager, self.env.ref('base.user_admin')):
            with self.subTest(user=user.login):
                self.assertIn(self.contract_b, self.env['tp.contract'].with_user(user).search([]))
                self.assertFalse(self._amounts(user))
                self.assertFalse(self.env['tp.contract.document'].with_user(user).search([('confidentiality', '=', 'financial')]))

    def test_financial_attachment_requires_grant(self):
        Attachment = self.env['ir.attachment']
        attachment = Attachment.search([
            ('res_model', '=', 'tp.contract.document'), ('res_id', '=', self.financial_doc.id), ('res_field', '=', 'file'),
        ])
        self.assertEqual(len(attachment), 1)
        domain = [('res_model', '=', 'tp.contract.document'), ('res_id', '=', self.financial_doc.id), ('res_field', '=', 'file')]
        for user in (self.reader, self.finance_b, self.manager):
            with self.subTest(user=user.login):
                self.assertFalse(Attachment.with_user(user).search(domain))
                with self.assertRaises(AccessError):
                    attachment.with_user(user).read(['raw'])
                with self.assertRaises(AccessError):
                    self.financial_doc.with_user(user).read(['file', 'file_name'])
        self.assertTrue(attachment.with_user(self.finance_a).raw)
        self.assertTrue(self.financial_doc.with_user(self.finance_a).file)

    def test_general_attachment_follows_project_scope(self):
        self.assertTrue(self.general_doc.with_user(self.reader).file)
        with self.assertRaises(AccessError):
            self.general_doc.with_user(self.outsider).read(['file'])

    def test_no_group_can_write_contract_data(self):
        amount = self.env['tp.contract.line.amount'].search([('line_id', '=', self.line_x.id)])
        targets = (
            (self.contract_a, {'name': 'Changed'}), (self.amendment, {'review_state': 'draft'}),
            (self.line_x, {'name': 'Changed'}), (self.approval, {'decision': 'pending'}),
            (amount, {'amount': 1}), (self.approval_amount, {'amount': 1}), (self.general_doc, {'name': 'Changed'}),
        )
        for user in (self.reader, self.finance_a, self.manager):
            for record, vals in targets:
                with self.subTest(user=user.login, model=record._name):
                    with self.assertRaises(AccessError):
                        record.with_user(user).write(vals)
                    with self.assertRaises(AccessError):
                        record.with_user(user).unlink()
                    with self.assertRaises(AccessError):
                        record.with_user(user).copy()
        with self.assertRaises(AccessError):
            self.amendment.with_user(self.manager).write({'effectivity_status': 'not_effective'})
        with self.assertRaises(AccessError):
            self.approval.with_user(self.finance_a).write({'verification_state': 'verified'})

    def test_grants_are_not_self_service(self):
        Grant = self.env['tp.project.grant']
        self.assertEqual(Grant.with_user(self.finance_a).search([]), self.grant_a)
        self.assertEqual(Grant.with_user(self.manager).search([]), Grant.search([]))
        for user in (self.reader, self.manager):
            with self.subTest(user=user.login), self.assertRaises(AccessError):
                Grant.with_user(user).create({
                    'project_id': self.project_a.id, 'user_id': self.reader.id, 'capability': 'financial_read',
                    'reason': 'Unauthorized',
                })
        with self.assertRaises(AccessError):
            self.grant_a.with_user(self.manager).write({'active': False})

    def test_grant_scope_validation(self):
        other_company = self.env['res.company'].create({'name': 'Other Contract Test Company'})
        foreign = self.env['project.project'].create({
            'name': 'Foreign', 'company_id': other_company.id, 'tp_managed': True, 'tp_code': 'CTR-FOREIGN',
        })
        with self.assertRaises(ValidationError):
            self._grant(foreign, self.reader)
        native = self.env['project.project'].create({'name': 'Native', 'company_id': self.company.id})
        with self.assertRaises(ValidationError):
            self._grant(native, self.reader)

    def test_company_restriction_applies_to_platform_manager(self):
        other_company = self.env['res.company'].create({'name': 'Other Contract Company'})
        project = self.env['project.project'].create({
            'name': 'Foreign', 'company_id': other_company.id, 'tp_managed': True, 'tp_code': 'CTR-FOREIGN-2',
        })
        contract = self._contract(project, 'HD-FOREIGN')
        self.assertNotIn(contract, self.env['tp.contract'].with_user(self.manager).search([]))
        with self.assertRaises(AccessError):
            contract.with_user(self.manager).read(['name'])
