import hashlib
import json
from pathlib import Path

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'corp_report001')
class TestReporting(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.department = cls.env['hr.department'].create({'name': 'CORP-REPORT Test department', 'company_id': cls.company.id})
        group = cls.env.ref('tp_reporting.group_reporting_user')
        cls.author, cls.manager, cls.outsider = cls.env['res.users'].create([{'name': name, 'login': 'corp-report-' + name, 'company_id': cls.company.id, 'company_ids': [Command.set(cls.company.ids)], 'group_ids': [Command.set([group.id])]} for name in ('author', 'manager', 'outsider')])
        for cap in ('read', 'review', 'finalize', 'plan', 'plan_issue', 'consolidate', 'direct'):
            cls.env['tp.report.assignment'].create({'name': 'Test ' + cap, 'user_id': cls.manager.id, 'capability': cap, 'company_id': cls.company.id, 'department_id': cls.department.id, 'date_start': '2020-01-01', 'reason': 'Automated test'})

    def _document(self, **extra):
        values = {'name': 'CORP-REPORT test', 'company_id': self.company.id, 'department_id': self.department.id, 'owner_id': self.author.id, 'reviewer_id': self.manager.id, 'period_type': 'week', 'date_start': '2026-11-02', 'date_end': '2026-11-08', 'summary': 'Kết quả thử'}
        values.update(extra)
        return self.env['tp.report.document'].with_user(self.author).create(values)

    def _plan(self, period, start, end, parent=None, target=10):
        return self.env['tp.report.plan'].with_user(self.manager).create({'name': 'Plan ' + period, 'company_id': self.company.id, 'department_id': self.department.id, 'owner_id': self.author.id, 'period_type': period, 'date_start': start, 'date_end': end, 'parent_id': parent.id if parent else False, 'unit': 'hồ sơ', 'target': target})

    def test_draft_privacy_and_scope_identity(self):
        doc = self._document()
        self.assertFalse(self.env['tp.report.document'].with_user(self.manager).search([('id', '=', doc.id)]))
        self.assertFalse(self.env['tp.report.document'].with_user(self.outsider).search([('id', '=', doc.id)]))
        with self.assertRaises(AccessError):
            doc.with_context(tp_reporting_expected_version=doc.version).write({'state': 'finalized'})
        with self.assertRaises(AccessError):
            doc.with_context(tp_reporting_expected_version=doc.version).write({'owner_id': self.outsider.id})
        with self.assertRaises(AccessError):
            doc.with_context(tp_reporting_expected_version=doc.version).write({'date_start': '2026-11-09'})

    def test_submit_return_snapshot_and_idempotency(self):
        doc = self._document()
        original = doc.version
        doc.action_submit(expected_version=original, request_key='submit-one')
        snapshot = doc.current_snapshot_id
        payload = snapshot.payload
        self.assertFalse(doc.action_submit(expected_version=original, request_key='submit-one'))
        self.assertEqual(len(doc.snapshot_ids), 1)
        with self.assertRaises(UserError):
            doc.action_submit(expected_version=original, request_key='submit-different')
        with self.assertRaises(AccessError):
            snapshot.write({'payload': '{}'})
        doc.with_user(self.manager).action_return(reason='Bổ sung minh chứng', expected_version=doc.version)
        doc.with_context(tp_reporting_expected_version=doc.version).write({'summary': 'Đã bổ sung'})
        doc.action_submit(expected_version=doc.version)
        self.assertEqual(snapshot.payload, payload)
        self.assertEqual(len(doc.snapshot_ids), 2)
        doc.with_user(self.manager).action_finalize(expected_version=doc.version)
        with self.assertRaises(AccessError):
            doc.unlink()

    def test_reviewer_required_and_no_self_review(self):
        doc = self._document(reviewer_id=False)
        choices = doc.get_reviewer_choices()
        self.assertIn({'id': self.manager.id, 'display_name': self.manager.name}, choices)
        self.assertNotIn(self.author.id, [choice['id'] for choice in choices])
        self.assertTrue(all(set(choice) == {'id', 'display_name'} for choice in choices))
        with self.assertRaises(ValidationError):
            doc.action_submit()
        doc.with_context(tp_reporting_expected_version=doc.version).write({'reviewer_id': self.manager.id})
        doc.action_submit()
        with self.assertRaises(AccessError):
            doc.action_finalize()

    def test_plan_period_allocation_baseline(self):
        quarter = self._plan('quarter', '2026-10-01', '2026-12-31')
        quarter.action_submit()
        quarter.action_issue()
        month = self._plan('month', '2026-11-01', '2026-11-30', quarter, target=11)
        month.action_submit()
        with self.assertRaises(ValidationError):
            month.action_issue()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self._plan('week', '2026-11-02', '2026-11-08')
        baseline = dict(quarter.baseline)
        quarter.action_revise(reason='Điều chỉnh thử')
        quarter.with_context(tp_reporting_expected_version=quarter.version).write({'target': 12})
        quarter.action_submit()
        quarter.action_issue()
        self.assertEqual(quarter.baseline, baseline)
        self.assertEqual(len(quarter.baseline_history), 2)

    def test_reviews_immutable_replies_and_work_state(self):
        doc = self._document()
        line = self.env['tp.report.line'].with_user(self.author).create({'document_id': doc.id, 'name': 'Hồ sơ', 'work_date': '2026-11-03', 'quantity': 0, 'unit': 'hồ sơ', 'contribution_key': 'source-a', 'work_status': 'in_progress'})
        doc.action_submit()
        self.assertIn('"quantity": 0.0', doc.current_snapshot_id.payload)
        review = self.env['tp.report.review'].with_user(self.manager).create({'document_id': doc.id, 'line_id': line.id, 'comment': 'Cần bổ sung', 'assessment': 'needs_change'})
        self.assertEqual(review.version, doc.current_snapshot_id.version)
        with self.assertRaises(AccessError):
            review.with_user(self.author).write({'comment': 'Đã đạt'})
        reply = self.env['tp.report.review'].with_user(self.author).create({'document_id': doc.id, 'parent_id': review.id, 'comment': 'Tôi sẽ bổ sung'})
        self.assertEqual(reply.actor_id, self.author)
        internal = self.env['tp.report.review'].with_user(self.manager).create({'document_id': doc.id, 'comment': 'Nội bộ', 'audience': 'internal'})
        self.assertFalse(self.env['tp.report.review'].with_user(self.author).search([('id', '=', internal.id)]))
        doc.with_user(self.manager).action_finalize()
        self.assertEqual(line.work_status, 'in_progress')

    def test_source_day_and_finance_no_access(self):
        doc = self._document()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['tp.report.line'].with_user(self.author).create({'document_id': doc.id, 'name': 'Sai ngày', 'work_date': '2026-11-09', 'contribution_key': 'late'})
        with self.assertRaises(AccessError):
            self.env['tp.report.value'].with_user(self.author).search([])
        with self.assertRaises(AccessError):
            doc._require('finance_read')
        with self.assertRaises(AccessError):
            doc.with_user(self.outsider)._require('review')
        self.assertTrue(fields.Date.to_date('2026-11-02').weekday() == 0)

    def test_draft_version_guards_and_obligations(self):
        doc = self._document()
        old = doc.version
        doc.with_context(tp_reporting_expected_version=old).write({'summary': 'Tab 1'})
        with self.assertRaises(UserError):
            doc.with_context(tp_reporting_expected_version=old).write({'summary': 'Tab 2'})
        obligation = self.env['tp.report.obligation'].with_user(self.manager).create({'name': 'Test obligation', 'company_id': self.company.id, 'department_id': self.department.id, 'owner_id': self.author.id, 'period_type': 'week', 'date_start': doc.date_start, 'date_end': doc.date_end, 'deadline': '2026-11-09 10:00:00'})
        with self.assertRaises(AccessError):
            obligation.with_user(self.author).unlink()
        with self.assertRaises(ValidationError):
            obligation.with_user(self.manager).action_exempt()
        obligation.with_user(self.manager).write({'reason': 'Test approved exception', 'state': 'exempt'})
        self.assertEqual(obligation.status, 'exempt')

    def test_finance_separate_confirmation_and_snapshot(self):
        finance = self.env.ref('tp_reporting.group_reporting_finance')
        self.author.group_ids = [Command.link(finance.id)]
        self.manager.group_ids = [Command.link(finance.id)]
        for user, cap in [(self.author, 'finance_enter'), (self.author, 'finance_read'), (self.author, 'finance_confirm'), (self.manager, 'finance_read'), (self.manager, 'finance_confirm')]:
            self.env['tp.report.assignment'].create({'name': 'Money test', 'user_id': user.id, 'capability': cap, 'company_id': self.company.id, 'department_id': self.department.id, 'date_start': '2020-01-01', 'reason': 'Test only'})
        doc = self._document()
        metric = self.env['tp.report.metric'].create({'name': 'Production test', 'code': 'TEST-PRODUCTION', 'unit': 'VND', 'definition': 'Test independent production metric', 'currency_id': self.company.currency_id.id, 'tax_basis': 'na'})
        value = self.env['tp.report.value'].with_user(self.author).create({'name': 'Confirmed zero', 'document_id': doc.id, 'metric_id': metric.id, 'amount': 0, 'currency_id': metric.currency_id.id, 'tax_basis': 'na', 'coverage_key': 'source-A', 'status': 'pending', 'source_reference': 'Test source', 'source_date': '2026-11-03'})
        evidence = self.env['ir.attachment'].with_user(self.author).create({'name': 'finance.txt', 'raw': b'test', 'res_model': 'tp.report.value', 'res_id': value.id})
        value.write({'evidence_ids': [Command.link(evidence.id)]})
        with self.assertRaises(AccessError):
            value.action_confirm()
        value.with_user(self.manager).action_confirm()
        self.assertEqual(value.amount, 0)
        self.assertEqual(value.status, 'confirmed')
        with self.assertRaises(Exception), self.cr.savepoint():
            value.copy({'coverage_key': 'source-A'})
        doc.action_submit()
        self.assertIn(doc.current_snapshot_id, value.snapshot_ids)
        self.assertNotIn('Confirmed zero', doc.current_snapshot_id.payload)
        with self.assertRaises(AccessError):
            value.write({'amount': 10})
        with self.assertRaises(AccessError):
            evidence.write({'raw': b'changed'})
        with self.assertRaises(AccessError):
            evidence.with_user(self.outsider)._can_return_content()

    def test_scoped_assignment_expiry_revocation_and_no_selfgrant(self):
        doc = self._document()
        doc.action_submit()
        assignments = self.env['tp.report.assignment'].search([('user_id', '=', self.manager.id)])
        assignments.write({'date_end': '2020-01-02'})
        self.env.invalidate_all()
        with self.assertRaises(AccessError):
            doc.with_user(self.manager)._require('review')
        with self.assertRaises(AccessError):
            doc.with_user(self.manager).action_review()
        config = self.env.ref('tp_reporting.group_reporting_config')
        self.outsider.group_ids = [Command.link(config.id)]
        with self.assertRaises(AccessError):
            self.env['tp.report.assignment'].with_user(self.outsider).create({'name': 'Escalation', 'user_id': self.outsider.id, 'capability': 'finalize', 'company_id': self.company.id, 'reason': 'Unauthorized self grant'})

    def test_rollup_dependencies_dedup_and_money_unit(self):
        quarter = self._plan('quarter', '2026-10-01', '2026-12-31', target=20)
        quarter.action_submit()
        quarter.action_issue()
        month = self._plan('month', '2026-11-01', '2026-11-30', quarter, target=10)
        month.action_submit()
        month.action_issue()
        week = self._plan('week', '2026-11-02', '2026-11-08', month, target=5)
        week.action_submit()
        week.action_issue()
        doc = self._document()
        self.env['tp.report.line'].with_user(self.author).create({'name': 'Shared source', 'document_id': doc.id, 'plan_id': week.id, 'work_date': '2026-11-03', 'quantity': 2, 'unit': 'hồ sơ', 'contribution_key': 'one-output'})
        doc.action_submit()
        self.assertEqual(quarter.with_user(self.manager)._report_actual()[0]['quantity'], 2)
        department_report = self.env['tp.report.document'].with_user(self.manager).create({'name': 'Department test', 'level': 'department', 'company_id': self.company.id, 'department_id': self.department.id, 'owner_id': self.manager.id, 'period_type': 'month', 'date_start': '2026-11-01', 'date_end': '2026-11-30', 'reviewer_id': self.author.id})
        department_report.action_aggregate()
        self.assertEqual(department_report.dependency_ids, doc.current_snapshot_id)
        self.assertEqual(sum(department_report.line_ids.mapped('quantity')), 2)
        old_dependency = department_report.dependency_ids
        doc.with_user(self.manager).action_return(reason='new version')
        doc.with_context(tp_reporting_expected_version=doc.version).write({'summary': 'Revised'})
        doc.action_submit()
        self.assertEqual(department_report.dependency_ids, old_dependency)

    def test_directive_retry_owner_result_and_history(self):
        doc = self._document()
        doc.action_submit()
        values = {'name': 'Action test', 'document_id': doc.id, 'company_id': self.company.id, 'department_id': self.department.id, 'owner_id': self.author.id, 'request_key': 'directive-test', 'description': 'Solve test issue'}
        directive = self.env['tp.report.directive'].with_user(self.manager).create(values)
        repeated = self.env['tp.report.directive'].with_user(self.manager).create(values)
        self.assertEqual(directive, repeated)
        with self.assertRaises(UserError):
            self.env['tp.report.directive'].with_user(self.manager).create(dict(values, name='Changed payload'))
        directive = directive.with_user(self.author)
        directive.action_start(expected_version=directive.version, request_key='start-once')
        directive.action_start(expected_version=1, request_key='start-once')
        with self.assertRaises(ValidationError):
            directive.action_done(expected_version=directive.version)
        directive.with_context(tp_reporting_expected_version=directive.version).write({'result': 'Solved on web'})
        with self.assertRaises(UserError):
            directive.action_start(expected_version=1, request_key='start-once')
        directive.action_done(expected_version=directive.version, request_key='done-once')
        self.assertEqual(directive.state, 'done')
        self.assertEqual([event['action'] for event in directive.history], ['create', 'in_progress', 'done'])
        with self.assertRaises(AccessError):
            directive.with_context(tp_reporting_expected_version=directive.version).write({'result': 'Rewrite'})

    def test_overlap_week_fact_dates_and_unknown_zero(self):
        doc = self._document(date_start='2026-11-30', date_end='2026-12-06')
        self.env['tp.report.line'].with_user(self.author).create([{'name': 'November fact', 'document_id': doc.id, 'work_date': '2026-11-30', 'quantity': 0, 'unit': 'hồ sơ', 'contribution_key': 'nov-fact'}, {'name': 'December fact', 'document_id': doc.id, 'work_date': '2026-12-01', 'quantity': 8, 'unit': 'hồ sơ', 'contribution_key': 'dec-fact'}, {'name': 'Missing fact', 'document_id': doc.id, 'work_date': '2026-11-30', 'unit': 'hồ sơ', 'contribution_key': 'missing'}])
        doc.action_submit()
        facts = json.loads(doc.current_snapshot_id.payload)['lines']
        self.assertEqual(facts[0]['quantity'], 0)
        self.assertIsNone(facts[2]['quantity'])
        aggregate = self.env['tp.report.document'].with_user(self.manager).create({'name': 'November department', 'company_id': self.company.id, 'department_id': self.department.id, 'owner_id': self.manager.id, 'level': 'department', 'period_type': 'month', 'date_start': '2026-11-01', 'date_end': '2026-11-30'})
        aggregate.action_aggregate()
        self.assertEqual(len(aggregate.line_ids), 2)
        self.assertNotIn('December fact', aggregate.line_ids.mapped('name'))
        self.assertEqual(len(aggregate.line_ids.filtered('quantity_known')), 1)

    def test_department_grant_does_not_open_company_report(self):
        self.env['tp.report.assignment'].create({'name': 'Company author test', 'user_id': self.env.uid, 'capability': 'consolidate', 'company_id': self.company.id, 'date_start': '2020-01-01', 'reason': 'Automated test'})
        doc = self.env['tp.report.document'].create({'name': 'Company scope test', 'level': 'company', 'owner_id': self.env.user.id, 'company_id': self.company.id, 'department_id': self.department.id, 'period_type': 'month', 'date_start': '2041-11-01', 'date_end': '2041-11-30', 'summary': 'Company data'})
        self.assertFalse(doc.department_id)
        self.assertFalse(self.env['tp.report.document'].with_user(self.manager).search([('id', '=', doc.id)]))
        with self.assertRaises(AccessError):
            doc.with_user(self.manager)._require('consolidate')

    def test_multicompany_allowed_context_never_replaces_assignment(self):
        other_company = self.env['res.company'].create({'name': 'CORP-REPORT other company'})
        group = self.env.ref('tp_reporting.group_reporting_user')
        other_author, other_manager = self.env['res.users'].create([{'name': name, 'login': 'corp-report-' + name, 'company_id': other_company.id, 'company_ids': [Command.set(other_company.ids)], 'group_ids': [Command.set(group.ids)]} for name in ('other-author', 'other-manager')])
        self.env['tp.report.assignment'].create({'name': 'Other reviewer', 'user_id': other_manager.id, 'capability': 'review', 'company_id': other_company.id, 'date_start': '2020-01-01', 'reason': 'Automated test'})
        doc = self.env['tp.report.document'].with_user(other_author).with_context(allowed_company_ids=other_company.ids).create({'name': 'Other company private', 'company_id': other_company.id, 'owner_id': other_author.id, 'department_id': False, 'reviewer_id': other_manager.id, 'period_type': 'week', 'date_start': '2026-11-02', 'date_end': '2026-11-08', 'summary': 'Other company data'})
        doc.action_submit()
        self.manager.company_ids = [Command.link(other_company.id)]
        self.env['tp.report.assignment'].create({'name': 'Other scope reader', 'user_id': self.manager.id, 'capability': 'read', 'company_id': other_company.id, 'date_start': '2020-01-01', 'reason': 'Automated test', 'level': 'personal'})
        selected = self.env['tp.report.document'].with_user(self.manager).with_context(allowed_company_ids=other_company.ids)
        self.assertEqual(selected.search([('id', '=', doc.id)]).ids, doc.ids)
        unselected = selected.with_context(allowed_company_ids=self.company.ids)
        self.assertFalse(unselected.search([('id', '=', doc.id)]))
        self.env['tp.report.assignment'].search([('user_id', '=', self.manager.id), ('company_id', '=', other_company.id)]).unlink()
        outsider_context = self.env['tp.report.document'].with_user(self.manager).with_context(allowed_company_ids=[self.company.id, other_company.id])
        self.assertFalse(outsider_context.search([('id', '=', doc.id)]))
        with self.assertRaises(AccessError):
            outsider_context.browse(doc.id).check_access('read')
        with self.assertRaises((ValidationError, AccessError)), self.cr.savepoint():
            self._document(company_id=other_company.id, department_id=False)

    def test_attachment_current_permission_revoke_and_private_paths(self):
        doc = self._document()
        attachment = self.env['ir.attachment'].with_user(self.author).create({'name': 'report-proof.txt', 'raw': b'proof', 'res_model': 'tp.report.document', 'res_id': doc.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env['ir.attachment'].with_user(self.author).create({'name': 'public-proof.txt', 'raw': b'proof', 'res_model': 'tp.report.document', 'res_id': doc.id, 'public': True})
        doc.action_submit()
        attachment.with_user(self.manager)._can_return_content()
        self.env['tp.report.assignment'].search([('user_id', '=', self.manager.id)]).write({'active': False})
        self.env.invalidate_all()
        with self.assertRaises(AccessError):
            attachment.with_user(self.manager)._can_return_content(access_token='previous-url')
        with self.assertRaises(AccessError):
            attachment.with_user(self.author).unlink()

    def test_attachment_snapshot_bytes_and_failed_transaction(self):
        doc = self._document()
        attachment = self.env['ir.attachment'].with_user(self.author).create({'name': 'immutable-bytes.txt', 'raw': b'CORP-REPORT immutable snapshot proof', 'res_model': 'tp.report.document', 'res_id': doc.id})
        attachment.flush_recordset()
        path = Path(attachment._full_path(attachment.store_fname))
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        doc.action_submit()
        with self.assertRaises(AccessError), self.cr.savepoint():
            attachment.with_user(self.author).write({'raw': b'overwrite submitted proof'})
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
        created_id = None
        with self.assertRaisesRegex(RuntimeError, 'rollback probe'):
            with self.cr.savepoint():
                temporary = self.env['ir.attachment'].with_user(self.author).create({'name': 'transaction-only.txt', 'raw': b'CORP-REPORT rollback probe private bytes', 'res_model': 'tp.report.document', 'res_id': 0})
                created_id = temporary.id
                failure_message = 'rollback probe'
                raise RuntimeError(failure_message)
        self.assertFalse(self.env['ir.attachment'].browse(created_id).exists())
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
        # Odoo filestore may retain an unreferenced new blob until GC; this is not a GC/restore test.
