from datetime import date
from decimal import Decimal

from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tools import mute_logger

from .common import TpContractCommon


class TestContractModel(TpContractCommon):
    def test_c1_effective_snapshot_replaces_instead_of_adding(self):
        before, warnings = self.contract_a._effective_revision(date(2026, 10, 31))
        self.assertEqual(before, self.original)
        self.assertEqual(warnings, ['future_revision_recorded'])
        self.assertEqual(before._amount_summary()['value'], Decimal(100))
        after, warnings = self.contract_a._effective_revision(date(2026, 11, 1))
        self.assertEqual(after, self.amendment)
        self.assertEqual(warnings, [])
        self.assertEqual(after._amount_summary()['value'], Decimal(110))
        # The original snapshot stays readable after the amendment.
        self.assertEqual(self.original._amount_summary()['value'], Decimal(100))

    def test_no_effective_revision_before_any_effect(self):
        revision, warnings = self.contract_a._effective_revision(date(2026, 1, 9))
        self.assertFalse(revision)
        self.assertIn('no_effective_revision', warnings)

    def test_same_date_conflict_is_reported_not_resolved(self):
        self._revision(
            self.contract_a, 2, previous=self.amendment, signed='2026-10-11', effective='2026-11-01', kind='correction',
        )
        revision, warnings = self.contract_a._effective_revision(date(2026, 11, 15))
        self.assertFalse(revision)
        self.assertIn('effective_date_conflict', warnings)

    def test_base_approval_does_not_make_revision_signed_or_effective(self):
        pending = self._revision(self.contract_a, 2, previous=self.amendment, kind='amendment')
        self.env['tp.approval.reference'].create({
            'revision_id': pending.id, 'reference_kind': 'base_id', 'base_reference': 'BASE-SYN-001',
            'decision': 'approved', 'decided_by_name': 'Synthetic approver', 'decided_at': fields.Datetime.now(),
            'verification_state': 'verified', 'verified_by_id': self.manager.id, 'verified_at': fields.Datetime.now(),
            'authority_status': 'confirmed', 'authority_source': 'Synthetic delegation',
        })
        self.assertEqual(pending.signature_status, 'unsigned')
        self.assertEqual(pending.effectivity_status, 'not_effective')
        revision, _warnings = self.contract_a._effective_revision(date(2027, 1, 1))
        self.assertEqual(revision, self.amendment)

    def test_declared_base_result_is_not_verified(self):
        self.assertEqual(self.approval.decision, 'approved')
        self.assertEqual(self.approval.verification_state, 'pending')
        self.assertFalse(self.approval._is_verified_result())

    def test_c5_unconfirmed_amount_is_null_and_zero_is_zero(self):
        unconfirmed = self._revision(self.contract_a, 2, previous=self.amendment, kind='correction')
        self._line(unconfirmed, 'X', 'Survey package', change_kind='amended', previous=self.line_x2, state='unconfirmed')
        summary = unconfirmed._amount_summary()
        self.assertIsNone(summary['value'])
        self.assertEqual(summary['status'], 'incomplete')
        zero = self._revision(self.contract_a, 3, previous=unconfirmed, kind='correction')
        self._line(zero, 'X', 'Survey package', change_kind='added', amount=0)
        summary = zero._amount_summary()
        self.assertEqual(summary['value'], Decimal(0))
        self.assertEqual(summary['status'], 'confirmed')

    def test_mixed_tax_basis_is_not_totalled(self):
        self.env['tp.contract.line.amount'].search([('line_id', '=', self.line_y2.id)]).tax_basis = 'including_tax'
        summary = self.amendment._amount_summary()
        self.assertIsNone(summary['value'])
        self.assertEqual(summary['status'], 'mixed_basis')

    @mute_logger('odoo.sql_db')
    def test_amount_constraints(self):
        with self.assertRaises(IntegrityError):
            self.env['tp.contract.line.amount'].search([('line_id', '=', self.line_x.id)]).write({
                'amount_state': 'unconfirmed', 'amount': 5,
            })
            self.env.flush_all()
        with self.assertRaises(IntegrityError):
            self.env['tp.contract.line.amount'].search([('line_id', '=', self.line_x.id)]).amount = -1
            self.env.flush_all()

    @mute_logger('odoo.sql_db')
    def test_revision_evidence_constraints(self):
        with self.assertRaises(IntegrityError):
            self.env['tp.contract.revision'].create({
                'contract_id': self.contract_a.id, 'sequence': 5, 'revision_kind': 'amendment', 'name': 'Unsigned',
                'previous_revision_id': self.amendment.id, 'effectivity_status': 'effective_recorded',
                'effective_date': '2027-01-01',
            })
        with self.assertRaises(IntegrityError):
            self.env['tp.contract.revision'].create({
                'contract_id': self.contract_a.id, 'sequence': 6, 'revision_kind': 'amendment', 'name': 'No previous',
            })
        with self.assertRaises(IntegrityError):
            self.env['tp.contract.revision'].create({
                'contract_id': self.contract_a.id, 'sequence': 0, 'revision_kind': 'original', 'name': 'Second original',
            })

    def test_previous_revision_must_be_earlier_in_same_contract(self):
        with self.assertRaises(ValidationError):
            self._revision(self.contract_a, 4, previous=self.revision_b, kind='amendment')

    def test_line_provenance_follows_previous_revision(self):
        revision = self._revision(self.contract_a, 2, previous=self.amendment, kind='amendment')
        with self.assertRaises(ValidationError):
            self._line(revision, 'X', 'Survey package', change_kind='amended', previous=self.line_x, amount=80)
        with self.assertRaises(ValidationError):
            self._line(revision, 'Z', 'New package', change_kind='original', amount=5)

    @mute_logger('odoo.sql_db')
    def test_approval_reference_constraints(self):
        base = {'revision_id': self.amendment.id, 'reference_kind': 'manual', 'provenance': 'Synthetic'}
        for invalid in (
            {'reference_kind': 'base_id', 'provenance': False},
            {'source_url': 'http://base.example.test/1'},
            {'decision': 'rejected', 'decided_by_name': 'Synthetic', 'decided_at': fields.Datetime.now()},
            {'verification_state': 'verified'},
            {'authority_status': 'confirmed'},
            {'evidence_sha256': 'not-a-hash'},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(IntegrityError):
                self.env['tp.approval.reference'].create(dict(base, **invalid))

    def test_finalized_revision_cannot_be_deleted(self):
        with self.assertRaises(UserError):
            self.amendment.unlink()

    def test_lifecycle_requires_recorded_effectivity(self):
        contract = self._contract(self.project_a, 'HD-A-NOEFFECT')
        self._revision(contract, 0)
        with self.assertRaises(ValidationError):
            contract.lifecycle_state = 'effective'
        self.contract_a.lifecycle_state = 'effective'

    def test_financial_document_classification(self):
        with self.assertRaises(ValidationError):
            self.env['tp.contract.document'].create({
                'contract_id': self.contract_a.id, 'name': 'Signed', 'document_kind': 'signed_contract',
                'confidentiality': 'general',
            })
        self.assertEqual(
            self.env['tp.contract.document'].create({
                'contract_id': self.contract_a.id, 'name': 'Unclassified', 'document_kind': 'other',
            }).confidentiality,
            'financial',
        )

    def test_contract_requires_managed_project(self):
        native = self.env['project.project'].create({'name': 'Native project', 'company_id': self.company.id})
        with self.assertRaises(ValidationError):
            self._contract(native, 'HD-NATIVE')
