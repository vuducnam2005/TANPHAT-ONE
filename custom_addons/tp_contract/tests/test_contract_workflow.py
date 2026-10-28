import json
from contextlib import contextmanager
from unittest.mock import patch

import psycopg2

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tools import BinaryBytes, mute_logger

from .common import TpContractWorkflowCommon
from odoo.addons.tp_contract.exceptions import ContractWorkflowError

MONEY_TOKENS = ('100', '150', '"amount"', '"value"')


class TestContractWorkflow(TpContractWorkflowCommon):
    """CTR-002a-P1 on synthetic data: T1-T6, T-P01 and T-N01..T-N09 (except T-N07, see the API tests)."""

    def _fails(self, status, code, user, action, payload, **kwargs):
        # A failed request rolls its transaction back; the savepoint does the same here.
        with self.assertRaises(ContractWorkflowError) as caught, self.env.cr.savepoint():
            self._run(user, action, payload, **kwargs)
        self.assertEqual((caught.exception.status, caught.exception.code), (status, code), caught.exception.message)
        return caught.exception

    @contextmanager
    def _no_side_effects(self):
        models = ('tp.contract', 'tp.contract.revision', 'tp.contract.submission', 'tp.contract.audit',
                  'tp.contract.outbox', 'tp.contract.idempotency', 'tp.contract.line.amount')
        before = {model: self.env[model].sudo().with_context(active_test=False).search_count([]) for model in models}
        versions = dict(self.env['tp.contract'].sudo().search([]).mapped(lambda contract: (contract.id, contract.aggregate_version)))
        yield
        self.env.invalidate_all()
        after = {model: self.env[model].sudo().with_context(active_test=False).search_count([]) for model in models}
        self.assertEqual(after, before)
        self.assertEqual(
            dict(self.env['tp.contract'].sudo().search([]).mapped(lambda contract: (contract.id, contract.aggregate_version))),
            versions,
        )

    def _draft(self):
        result = self._new_contract()
        return result['contract'].sudo(), result['revision'].sudo()

    def _submitted(self):
        contract, revision = self._draft()
        self._run(self.editor, 'edit_draft', {
            'expected_version': 1,
            'lines': [
                {'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount('100')},
                {'scope_key': 'L2', 'name': 'Design', 'amount': self._amount('50')},
            ],
        }, contract=contract, revision=revision)
        result = self._run(self.editor, 'submit_review', {'expected_version': 2, 'reviewer_id': self.reviewer.id},
                           contract=contract, revision=revision)
        return contract, revision, result['submission'].sudo()

    def _audit(self, contract):
        return self.env['tp.contract.audit'].sudo().search([('contract_id', '=', contract.id)])

    # T-P01

    def test_p01_draft_submit_return_rework_resubmit(self):
        result = self._new_contract()
        contract, revision = result['contract'].sudo(), result['revision'].sudo()
        self.assertFalse(result['replayed'])
        self.assertEqual((contract.code, contract.department_id, contract.aggregate_version), ('HD-WF-01', self.dept_kd, 1))
        self.assertEqual((revision.revision_kind, revision.sequence, revision.review_state), ('original', 0, 'draft'))
        self.assertEqual(revision._amount_summary()['status'], 'incomplete')

        self._run(self.editor, 'edit_draft', {
            'expected_version': 1,
            'lines': [
                {'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount('100')},
                {'scope_key': 'L2', 'name': 'Design', 'amount': self._amount('50')},
            ],
        }, contract=contract, revision=revision)
        submit = self._run(self.editor, 'submit_review', {'expected_version': 2, 'reviewer_id': self.reviewer.id},
                           contract=contract, revision=revision)
        first = submit['submission'].sudo()
        self.assertEqual((revision.review_state, contract.aggregate_version), ('in_review', 3))
        self.assertEqual((first.sequence, first.outcome, first.reviewer_id, first.contract_version), (1, 'pending', self.reviewer, 2))
        financial = self.env['tp.contract.submission.amount'].sudo().search([('submission_id', '=', first.id)])
        self.assertEqual(financial.financial_snapshot['total'], {'value': '150', 'status': 'confirmed', 'tax_basis': 'excluding_tax'})
        for token in MONEY_TOKENS:
            self.assertNotIn(token, json.dumps(first.metadata_snapshot))

        self._run(self.reviewer, 'return_review', {
            'expected_version': 3, 'reason': 'Scope of L1 is unclear', 'issues': [{'scope_key': 'L1', 'note': 'Add survey area'}],
        }, contract=contract, revision=revision)
        self.assertEqual((revision.review_state, first.outcome, first.returned_by_id), ('returned', 'returned', self.reviewer))
        first_hash, first_metadata = first.payload_sha256, first.metadata_snapshot

        self._run(self.editor, 'begin_rework', {'expected_version': 4, 'reason': 'Fix L1 scope'}, contract=contract, revision=revision)
        self.assertEqual(revision.review_state, 'draft')
        self._run(self.editor, 'edit_draft', {
            'expected_version': 5,
            'lines': [{'scope_key': 'L1', 'name': 'Survey, 12 km'}, {'scope_key': 'L2', 'name': 'Design'}],
        }, contract=contract, revision=revision)
        resubmit = self._run(self.editor, 'submit_review', {
            'expected_version': 6, 'reviewer_id': self.reviewer.id, 'fix_summary': 'Survey area added to L1',
        }, contract=contract, revision=revision)
        second = resubmit['submission'].sudo()
        self.assertEqual((revision.review_state, contract.aggregate_version), ('in_review', 7))
        self.assertEqual((second.sequence, second.previous_submission_id, second.fix_summary), (2, first, 'Survey area added to L1'))
        self.assertEqual((first.payload_sha256, first.metadata_snapshot, first.outcome), (first_hash, first_metadata, 'returned'))
        self.assertEqual([line['name'] for line in first.metadata_snapshot['lines']], ['Survey', 'Design'])
        self.assertEqual([line['name'] for line in second.metadata_snapshot['lines']], ['Survey, 12 km', 'Design'])
        self.assertNotEqual(second.payload_sha256, first_hash)

        audit = self._audit(contract)
        self.assertEqual(audit.mapped('action'), [
            'create_contract', 'edit_draft', 'submit_review', 'return_review', 'begin_rework', 'edit_draft', 'resubmit_review',
        ])
        self.assertEqual(audit.mapped('version_after'), [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(audit.mapped('actor_id'), self.editor | self.reviewer)
        outbox = self.env['tp.contract.outbox'].sudo().search([('contract_id', '=', contract.id)])
        self.assertEqual([(event.event_type, event.recipient_id) for event in outbox], [
            ('submit_review', self.reviewer), ('return_review', self.editor), ('resubmit_review', self.reviewer),
        ])
        # The slice never touches BASE, signature, effectivity or the contract lifecycle.
        self.assertFalse(revision.approval_reference_ids)
        self.assertEqual(
            (revision.signature_status, revision.signature_authority_status, revision.effectivity_status, contract.lifecycle_state),
            ('unsigned', 'pending', 'not_effective', 'not_effective'),
        )

    def test_p01_amendment_draft_carries_scope_and_classifies_changes(self):
        result = self._run(self.editor, 'create_amendment', {'expected_version': 1, 'name': 'Amendment 2'}, contract=self.contract_a)
        amendment = result['revision'].sudo()
        self.assertEqual((amendment.sequence, amendment.previous_revision_id, amendment.review_state), (2, self.amendment, 'draft'))
        self.assertEqual(amendment.line_ids.mapped('change_kind'), ['unchanged', 'unchanged'])
        self.assertEqual(amendment._amount_summary()['value'], 110)

        # A metadata editor renames scope without touching money.
        self._run(self.meta_editor, 'edit_draft', {
            'expected_version': 2,
            'lines': [{'scope_key': 'X', 'name': 'Survey package'}, {'scope_key': 'Y', 'name': 'Design package, phase 2'}],
        }, contract=self.contract_a, revision=amendment)
        self.assertEqual(amendment.line_ids.mapped('change_kind'), ['unchanged', 'amended'])
        self.assertEqual(amendment._amount_summary()['value'], 110)
        self._run(self.editor, 'edit_draft', {
            'expected_version': 3,
            'lines': [
                {'scope_key': 'X', 'name': 'Survey package', 'amount': self._amount('75', tax_basis='unknown')},
                {'scope_key': 'Y', 'name': 'Design package', 'amount': self._amount('40', tax_basis='unknown')},
                {'scope_key': 'Z', 'name': 'Supervision', 'amount': self._amount('5', tax_basis='unknown')},
            ],
        }, contract=self.contract_a, revision=amendment)
        self.assertEqual(amendment.line_ids.mapped('change_kind'), ['amended', 'unchanged', 'added'])
        self.assertEqual(amendment._amount_summary()['value'], 120)
        # The signed revisions keep their own snapshot.
        self.assertEqual(self.amendment._amount_summary()['value'], 110)
        self._fails(409, 'invalid_state', self.editor, 'create_amendment', {'expected_version': 4, 'name': 'Second open'},
                    contract=self.contract_a)

    # T-N01 capability and scope

    def test_n01_capability_scope_and_assignment(self):
        contract, revision = self._draft()
        edit = {'expected_version': 1, 'revision': {'name': 'Renamed'}}
        with self._no_side_effects():
            self._fails(403, 'forbidden', self.reader, 'edit_draft', edit, contract=contract, revision=revision)
            self._fails(403, 'forbidden', self.other_dept, 'edit_draft', edit, contract=contract, revision=revision)
            self._fails(403, 'forbidden', self.meta_editor, 'submit_review',
                        {'expected_version': 1, 'reviewer_id': self.reviewer.id}, contract=contract, revision=revision)
            self._fails(403, 'forbidden', self.reviewer, 'edit_draft', edit, contract=contract, revision=revision)
            # Platform managers get no workflow capability from their group.
            self._fails(403, 'forbidden', self.manager, 'edit_draft', edit, contract=contract, revision=revision)
            self._fails(404, 'not_found', self.other_project, 'edit_draft', edit, contract=contract, revision=revision)
            self._fails(404, 'not_found', self.editor, 'edit_draft', edit, contract=self.contract_b, revision=self.revision_b)
            self._fails(403, 'forbidden', self.other_dept, 'create_contract', {
                'project_id': self.project_a.id, 'code': 'HD-X', 'name': 'X', 'contract_type': 'owner', 'currency': 'VND',
            })
            self._fails(404, 'not_found', self.editor, 'create_contract', {
                'project_id': self.project_b.id, 'code': 'HD-X', 'name': 'X', 'contract_type': 'owner', 'currency': 'VND',
            })
        # An ended assignment hides the project, whatever grants remain.
        self.env['tp.project.assignment'].search([('user_id', '=', self.editor.id)]).active = False
        with self._no_side_effects():
            self._fails(404, 'not_found', self.editor, 'edit_draft', edit, contract=contract, revision=revision)

    def test_n01_other_company_and_non_platform_users(self):
        contract, revision = self._draft()
        other_company = self.env['res.company'].create({'name': 'Synthetic other company'})
        foreign = self.env['res.users'].create({
            'login': 'tp_wf_foreign', 'name': 'Foreign', 'company_id': other_company.id, 'company_ids': [(6, 0, other_company.ids)],
            'group_ids': [(4, self.env.ref('tp_core.group_user').id)],
        })
        internal = self.env['res.users'].create({
            'login': 'tp_wf_internal', 'name': 'Internal', 'company_id': self.company.id,
            'group_ids': [(4, self.env.ref('base.group_user').id)],
        })
        edit = {'expected_version': 1, 'revision': {'name': 'Renamed'}}
        with self._no_side_effects():
            self._fails(404, 'not_found', foreign, 'edit_draft', edit, contract=contract, revision=revision)
            self._fails(403, 'forbidden', internal, 'edit_draft', edit, contract=contract, revision=revision)

    def test_n01_reviewer_must_be_eligible_and_assigned(self):
        contract, revision = self._draft()
        self._run(self.editor, 'edit_draft', {
            'expected_version': 1, 'lines': [{'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount('100')}],
        }, contract=contract, revision=revision)
        workflow = self.env['tp.contract.workflow'].with_user(self.editor)
        self.assertEqual(workflow._tp_eligible_reviewers(contract), self.reviewer)
        with self._no_side_effects():
            for user in (self.meta_editor, self.other_dept, self.editor, self.other_project):
                self._fails(422, 'reviewer_ineligible', self.editor, 'submit_review',
                            {'expected_version': 2, 'reviewer_id': user.id}, contract=contract, revision=revision)
        submission = self._run(self.editor, 'submit_review', {'expected_version': 2, 'reviewer_id': self.reviewer.id},
                               contract=contract, revision=revision)['submission']
        # Another reviewer with the same grants is not the assigned one.
        second = self.env['res.users'].create({
            'login': 'tp_wf_reviewer_2', 'name': 'Reviewer 2', 'company_id': self.company.id,
            'group_ids': [(4, self.env.ref('tp_core.group_user').id)],
        })
        self._assign(self.project_a, second)
        self._caps(second, 'contract_review_commercial', 'financial_read')
        with self._no_side_effects():
            self._fails(403, 'not_assigned_reviewer', second, 'return_review', {'expected_version': 3, 'reason': 'No'},
                        contract=contract, revision=revision)
        self.assertEqual(submission.sudo().outcome, 'pending')

    # T-N02 money boundary

    def test_n02_money_needs_financial_edit_and_is_rechecked(self):
        contract, revision = self._draft()
        money = {'expected_version': 1, 'lines': [{'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount('90')}]}
        drop_money = {'expected_version': 1, 'lines': [{'scope_key': 'L2', 'name': 'Design'}]}
        currency = {'expected_version': 1, 'contract': {'currency': 'USD'}}
        with self._no_side_effects():
            for payload in (money, drop_money, currency):
                error = self._fails(403, 'forbidden', self.meta_editor, 'edit_draft', payload, contract=contract, revision=revision)
                self.assertIn('financial_draft_edit', error.details['missing_capabilities'])
        # Names alone stay open to the metadata editor; amounts stay as they were.
        self._run(self.meta_editor, 'edit_draft', {
            'expected_version': 1, 'lines': [{'scope_key': 'L1', 'name': 'Survey A'}, {'scope_key': 'L2', 'name': 'Design'}],
        }, contract=contract, revision=revision)
        amounts = self.env['tp.contract.line.amount'].sudo().search([('revision_id', '=', revision.id)])
        self.assertEqual(amounts.mapped(lambda amount: (amount.amount_state, amount.amount)), [('confirmed', 100), ('unconfirmed', 0)])
        self.assertFalse(self.env['tp.contract.line.amount'].with_user(self.meta_editor).search([('revision_id', '=', revision.id)]))

        key = 'replay-after-revoke'
        payload = {'expected_version': 2, 'lines': [
            {'scope_key': 'L1', 'name': 'Survey A', 'amount': self._amount('90')}, {'scope_key': 'L2', 'name': 'Design'},
        ]}
        self._run(self.editor, 'edit_draft', payload, key=key, contract=contract, revision=revision)
        self.grants['editor'].filtered(lambda grant: grant.capability == 'financial_draft_edit').active = False
        with self._no_side_effects():
            self._fails(403, 'forbidden', self.editor, 'edit_draft', payload, key=key, contract=contract, revision=revision)
            self._fails(403, 'forbidden', self.editor, 'edit_draft', dict(payload, expected_version=3),
                        contract=contract, revision=revision)

    def test_n02_snapshots_and_history_carry_no_money_outside_the_financial_zone(self):
        contract, _revision, submission = self._submitted()
        self.assertFalse(self.env['tp.contract.submission.amount'].with_user(self.meta_editor).search([]))
        self.assertEqual(self.env['tp.contract.submission'].with_user(self.meta_editor).search([]), submission)
        self.assertTrue(self.env['tp.contract.submission.amount'].with_user(self.reviewer).search([]))
        for record, fields_ in ((submission, ['metadata_snapshot', 'return_issues', 'fix_summary']),
                                (self._audit(contract), ['reason', 'state_before', 'state_after', 'payload_sha256'])):
            text = json.dumps(record.read(fields_), default=str)
            for token in ('"amount"', '"value"', '"total"'):
                self.assertNotIn(token, text)

    # T-N03 state and validation

    def test_n03_state_reason_and_amount_validation(self):
        contract, revision = self._draft()
        with self._no_side_effects():
            self._fails(409, 'invalid_state', self.reviewer, 'return_review', {'expected_version': 1, 'reason': 'x'},
                        contract=contract, revision=revision)
            self._fails(409, 'invalid_state', self.editor, 'begin_rework', {'expected_version': 1, 'reason': 'x'},
                        contract=contract, revision=revision)
            self._fails(422, 'submission_incomplete', self.editor, 'submit_review',
                        {'expected_version': 1, 'reviewer_id': self.reviewer.id}, contract=contract, revision=revision)
            self._fails(422, 'unknown_currency', self.editor, 'edit_draft', {'expected_version': 1, 'contract': {'currency': 'XXX'}},
                        contract=contract, revision=revision)
            self._fails(409, 'duplicate_code', self.editor, 'edit_draft', {'expected_version': 1, 'contract': {'code': 'hd-a'}},
                        contract=contract, revision=revision)
            for amount, code in (
                (self._amount(None), 'amount_value_required'),
                (self._amount('5', state='unconfirmed'), 'amount_value_not_allowed'),
                (self._amount('-5'), 'amount_negative'),
                (self._amount('1.5'), 'amount_precision'),
                (self._amount('1234567890123456'), 'amount_too_large'),
            ):
                self._fails(422, code, self.editor, 'edit_draft', {
                    'expected_version': 1, 'lines': [{'scope_key': 'L1', 'name': 'Survey', 'amount': amount}],
                }, contract=contract, revision=revision)
            for value in ('1e5', 'abc', 100):
                self._fails(400, 'invalid_request', self.editor, 'edit_draft', {
                    'expected_version': 1, 'lines': [{'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount(value)}],
                }, contract=contract, revision=revision)
            self._fails(422, 'name_required', self.editor, 'edit_draft', {'expected_version': 1, 'revision': {'name': '  '}},
                        contract=contract, revision=revision)

        # Confirmed zero is a value; unconfirmed stays without one and blocks the total.
        self._run(self.editor, 'edit_draft', {'expected_version': 1, 'lines': [
            {'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount('0')},
            {'scope_key': 'L2', 'name': 'Design', 'amount': self._amount(None, state='unconfirmed')},
        ]}, contract=contract, revision=revision)
        self.assertEqual(revision.sudo()._amount_summary()['value'], None)
        self._run(self.editor, 'edit_draft', {'expected_version': 2, 'lines': [
            {'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount('0')},
        ]}, contract=contract, revision=revision)
        self.assertEqual(revision.sudo()._amount_summary()['value'], 0)
        self.assertEqual(revision.sudo()._amount_summary()['status'], 'confirmed')

        self._run(self.editor, 'submit_review', {'expected_version': 3, 'reviewer_id': self.reviewer.id},
                  contract=contract, revision=revision)
        with self._no_side_effects():
            self._fails(409, 'invalid_state', self.editor, 'edit_draft', {'expected_version': 4, 'revision': {'name': 'x'}},
                        contract=contract, revision=revision)
            self._fails(409, 'invalid_state', self.editor, 'submit_review',
                        {'expected_version': 4, 'reviewer_id': self.reviewer.id}, contract=contract, revision=revision)
            self._fails(422, 'reason_required', self.reviewer, 'return_review', {'expected_version': 4, 'reason': '   '},
                        contract=contract, revision=revision)
            self._fails(422, 'unknown_scope_key', self.reviewer, 'return_review', {
                'expected_version': 4, 'reason': 'x', 'issues': [{'scope_key': 'NOPE', 'note': 'x'}],
            }, contract=contract, revision=revision)
        self._run(self.reviewer, 'return_review', {'expected_version': 4, 'reason': 'Check L1'}, contract=contract, revision=revision)
        with self._no_side_effects():
            self._fails(422, 'reason_required', self.editor, 'begin_rework', {'expected_version': 5, 'reason': ''},
                        contract=contract, revision=revision)
        self._run(self.editor, 'begin_rework', {'expected_version': 5, 'reason': 'Recheck'}, contract=contract, revision=revision)
        with self._no_side_effects():
            self._fails(422, 'fix_summary_required', self.editor, 'submit_review',
                        {'expected_version': 6, 'reviewer_id': self.reviewer.id}, contract=contract, revision=revision)

    def test_n03_project_without_department_cannot_scope_contracts(self):
        self.project_a.tp_department_id = False
        with self._no_side_effects():
            self._fails(422, 'scope_incomplete', self.editor, 'create_contract', {
                'project_id': self.project_a.id, 'code': 'HD-X', 'name': 'X', 'contract_type': 'owner', 'currency': 'VND',
            })

    # T-N04 direct ORM writes

    def test_n04_orm_writes_outside_the_workflow_are_blocked(self):
        contract, revision, submission = self._submitted()
        line = revision.line_ids[0]
        with self.assertRaises(AccessError):
            revision.with_user(self.editor).write({'review_state': 'draft'})
        with self.assertRaises(AccessError):
            line.with_user(self.editor).write({'name': 'Changed'})
        with self.assertRaises(AccessError):
            self.env['tp.approval.reference'].with_user(self.editor).create({
                'revision_id': revision.id, 'reference_kind': 'manual', 'decision': 'approved',
            })
        blocked = [
            lambda: revision.write({'review_state': 'review_complete'}),
            lambda: revision.write({'name': 'Changed'}),
            lambda: line.write({'name': 'Changed'}),
            lambda: self.env['tp.contract.line'].create({'revision_id': revision.id, 'scope_key': 'L9', 'name': 'Injected'}),
            lambda: self.env['tp.contract.line.amount'].search([('line_id', '=', line.id)]).write({'amount': 1}),
            line.unlink,
            lambda: contract.write({'name': 'Changed header'}),
            lambda: contract.write({'aggregate_version': 99}),
            lambda: contract.write({'department_id': self.dept_other.id}),
            lambda: submission.write({'return_reason': 'Injected'}),
            submission.unlink,
            lambda: self.env['tp.contract.submission.amount'].search([('submission_id', '=', submission.id)]).write({'salt': 'x'}),
            lambda: self._audit(contract).write({'reason': 'Injected'}),
            lambda: self._audit(contract).unlink(),
            lambda: self.env['tp.contract.outbox'].search([('contract_id', '=', contract.id)]).write({'state': 'delivered'}),
        ]
        for attempt in blocked:
            with self.assertRaises(UserError), self.env.cr.savepoint():
                attempt()
        self.assertEqual((revision.review_state, contract.aggregate_version, submission.return_reason), ('in_review', 3, False))

    def test_n04_submitted_documents_and_binaries_are_immutable(self):
        contract, revision = self._draft()
        document = self.env['tp.contract.document'].create({
            'contract_id': contract.id, 'revision_id': revision.id, 'name': 'Scope drawing', 'document_kind': 'technical_scope',
            'confidentiality': 'general', 'file': BinaryBytes(b'synthetic drawing v1'), 'file_name': 'drawing.pdf',
        })
        self._run(self.editor, 'edit_draft', {'expected_version': 1, 'lines': [
            {'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount('100')},
        ]}, contract=contract, revision=revision)
        submission = self._run(self.editor, 'submit_review', {'expected_version': 2, 'reviewer_id': self.reviewer.id},
                               contract=contract, revision=revision)['submission'].sudo()
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'tp.contract.document'), ('res_id', '=', document.id), ('res_field', '=', 'file'),
        ])
        self.assertEqual(submission.metadata_snapshot['documents'][0]['sha1'], attachment.checksum)
        for attempt in (
            lambda: document.write({'file': BinaryBytes(b'synthetic drawing v2')}),
            document.unlink,
            lambda: attachment.write({'raw': b'replaced'}),
            attachment.unlink,
        ):
            with self.assertRaises(UserError), self.env.cr.savepoint():
                attempt()

    # T-N05 stale versions

    def test_n05_stale_versions_are_rejected(self):
        contract, revision = self._draft()
        self._run(self.editor, 'edit_draft', {'expected_version': 1, 'lines': [
            {'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount('100')},
        ]}, contract=contract, revision=revision)
        with self._no_side_effects():
            # A child line changed after the caller read version 1.
            error = self._fails(409, 'stale_version', self.meta_editor, 'edit_draft', {'expected_version': 1, 'revision': {'name': 'x'}},
                                contract=contract, revision=revision)
            self.assertEqual(error.details, {'current_version': 2})
            self._fails(409, 'stale_version', self.editor, 'submit_review', {'expected_version': 1, 'reviewer_id': self.reviewer.id},
                        contract=contract, revision=revision)
        self._run(self.editor, 'submit_review', {'expected_version': 2, 'reviewer_id': self.reviewer.id}, contract=contract, revision=revision)
        with self._no_side_effects():
            self._fails(409, 'stale_version', self.reviewer, 'return_review', {'expected_version': 2, 'reason': 'x'},
                        contract=contract, revision=revision)
            # A second submit of the same draft loses: the revision is no longer a draft.
            self._fails(409, 'invalid_state', self.editor, 'submit_review', {'expected_version': 3, 'reviewer_id': self.reviewer.id},
                        contract=contract, revision=revision)
        self._run(self.reviewer, 'return_review', {'expected_version': 3, 'reason': 'x'}, contract=contract, revision=revision)
        with self._no_side_effects():
            self._fails(409, 'stale_version', self.editor, 'begin_rework', {'expected_version': 3, 'reason': 'x'},
                        contract=contract, revision=revision)
        self._run(self.editor, 'begin_rework', {'expected_version': 4, 'reason': 'x'}, contract=contract, revision=revision)
        with self._no_side_effects():
            self._fails(409, 'invalid_state', self.editor, 'begin_rework', {'expected_version': 5, 'reason': 'again'},
                        contract=contract, revision=revision)
            self._fails(409, 'stale_version', self.editor, 'submit_review',
                        {'expected_version': 4, 'reviewer_id': self.reviewer.id, 'fix_summary': 'x'}, contract=contract, revision=revision)

    # T-N06 idempotency

    def test_n06_retries_replay_without_duplicates(self):
        payload = {'project_id': self.project_a.id, 'code': 'HD-RETRY', 'name': 'Retry', 'contract_type': 'owner', 'currency': 'VND',
                   'lines': [{'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount('100')}]}
        first = self._run(self.editor, 'create_contract', payload, key='create-retry-1')
        again = self._run(self.editor, 'create_contract', payload, key='create-retry-1')
        self.assertTrue(again['replayed'])
        self.assertEqual(again['contract'], first['contract'])
        self.assertEqual(self.env['tp.contract'].search_count([('code', '=', 'HD-RETRY')]), 1)
        contract, revision = first['contract'].sudo(), first['revision'].sudo()

        steps = [
            (self.editor, 'submit_review', {'expected_version': 1, 'reviewer_id': self.reviewer.id}),
            (self.reviewer, 'return_review', {'expected_version': 2, 'reason': 'x'}),
            (self.editor, 'begin_rework', {'expected_version': 3, 'reason': 'x'}),
            (self.editor, 'submit_review', {'expected_version': 4, 'reviewer_id': self.reviewer.id, 'fix_summary': 'x'}),
        ]
        for index, (user, action, step) in enumerate(steps):
            key = f'retry-step-{index}'
            done = self._run(user, action, step, key=key, contract=contract, revision=revision)
            with self._no_side_effects():
                # The version moved on, yet the retry gets its result instead of a false stale_version.
                replay = self._run(user, action, step, key=key, contract=contract, revision=revision)
            self.assertTrue(replay['replayed'])
            self.assertEqual((replay['revision'], replay['submission']), (done['revision'], done['submission']))
        self.assertEqual(len(revision.submission_ids), 2)
        self.assertEqual(len(self._audit(contract)), 5)
        self.assertEqual(self.env['tp.contract.outbox'].sudo().search_count([('contract_id', '=', contract.id)]), 3)

        with self._no_side_effects():
            self._fails(409, 'idempotency_conflict', self.editor, 'create_contract', dict(payload, name='Other'), key='create-retry-1')
            self._fails(409, 'idempotency_conflict', self.reviewer, 'return_review', {'expected_version': 2, 'reason': 'changed'},
                        key='retry-step-1', contract=contract, revision=revision)
            self._fails(400, 'invalid_request', self.editor, 'create_contract', payload, key='short')
        # Keys are per user: the same key from another actor is a new request.
        self._fails(403, 'forbidden', self.meta_editor, 'submit_review', steps[0][2], key='retry-step-0',
                    contract=contract, revision=revision)

    # T-N08 write failure and delivery

    def test_n08_history_write_failure_rolls_the_action_back(self):
        contract, revision = self._draft()
        self._run(self.editor, 'edit_draft', {'expected_version': 1, 'lines': [
            {'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount('100')},
        ]}, contract=contract, revision=revision)
        for model in ('tp.contract.audit', 'tp.contract.outbox', 'tp.contract.idempotency'):
            with self._no_side_effects(), patch.object(type(self.env[model]), 'create', side_effect=RuntimeError(model)):
                with self.assertRaises(RuntimeError), self.env.cr.savepoint():
                    self._run(self.editor, 'submit_review', {'expected_version': 2, 'reviewer_id': self.reviewer.id},
                              contract=contract, revision=revision)
            self.assertEqual((revision.review_state, len(revision.submission_ids)), ('draft', 0))

    @mute_logger('odoo.addons.tp_contract.models.tp_contract_audit', 'odoo.sql_db')
    def test_n08_delivery_failure_keeps_the_event_and_dedupes(self):
        _contract, _revision, _submission = self._submitted()
        Outbox = self.env['tp.contract.outbox']
        event = Outbox.sudo().search([], order='id desc', limit=1)
        with patch.object(type(Outbox), '_tp_send', side_effect=RuntimeError('channel down')):
            Outbox._tp_deliver_pending()
        self.assertEqual((event.state, event.attempt_count, event.last_error), ('pending', 1, 'channel down'))
        Outbox._tp_deliver_pending()
        self.assertEqual(event.state, 'delivered')
        self.assertTrue(event.delivered_at <= fields.Datetime.now())
        with self.assertRaises(psycopg2.IntegrityError), self.env.cr.savepoint():
            Outbox.sudo().create({
                'event_id': event.event_id, 'audit_id': event.audit_id.id, 'event_type': event.event_type,
                'recipient_id': event.recipient_id.id, 'contract_id': event.contract_id.id,
            })
        self.assertEqual(Outbox.with_user(self.reviewer).search([]), event)
        self.assertFalse(Outbox.with_user(self.meta_editor).search([]))

    # T-N09 allowlist

    def test_n09_unknown_fields_and_out_of_slice_actions(self):
        contract, revision = self._draft()
        base = {'project_id': self.project_a.id, 'code': 'HD-X', 'name': 'X', 'contract_type': 'owner', 'currency': 'VND'}
        with self._no_side_effects():
            for payload in (base | {'review_state': 'review_complete'}, base | {'lifecycle_state': 'effective'},
                            base | {'department_id': self.dept_other.id},
                            base | {'lines': [{'scope_key': 'L1', 'name': 'x', 'change_kind': 'unchanged'}]},
                            base | {'lines': [{'scope_key': 'L1', 'name': 'x', 'amount': self._amount('1') | {'approved': True}}]}):
                self._fails(400, 'invalid_request', self.editor, 'create_contract', payload)
            for payload in ({'expected_version': 1, 'revision': {'signature_status': 'signed_recorded'}},
                            {'expected_version': 1, 'revision': {'effective_date': '2026-11-01'}},
                            {'expected_version': 1, 'contract': {'project_id': self.project_b.id}},
                            {'expected_version': 1, 'approval': {'decision': 'approved'}},
                            {'expected_version': 1}):
                self._fails(400, 'invalid_request', self.editor, 'edit_draft', payload, contract=contract, revision=revision)
            self._fails(400, 'invalid_request', self.editor, 'create_amendment', {'expected_version': 1, 'name': 'x', 'lines': []},
                        contract=self.contract_a)
            self._fails(400, 'invalid_request', self.editor, 'submit_review',
                        {'expected_version': 1, 'reviewer_id': self.reviewer.id, 'grant': 'financial_read'},
                        contract=contract, revision=revision)
            for action in ('cancel_revision', 'approve_base', 'record_signature', 'record_effectivity', 'record_payment'):
                with self.assertRaises(ValueError):
                    self._run(self.editor, action, {}, contract=contract, revision=revision)
