import json

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.tp_reporting.models.completion import dated_facts


@tagged('post_install', '-at_install', 'corp_report001')
class TestCompletion(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.department = cls.env['hr.department'].create({'name': 'Completion fake department', 'company_id': cls.company.id})
        group = cls.env.ref('tp_reporting.group_reporting_user')
        cls.author, cls.manager = cls.env['res.users'].create([{
            'name': name, 'login': 'completion-' + name, 'company_id': cls.company.id,
            'company_ids': [Command.set(cls.company.ids)], 'group_ids': [Command.set(group.ids)],
        } for name in ('author', 'manager')])
        for capability in ('read', 'review', 'plan', 'plan_issue', 'consolidate'):
            cls.env['tp.report.assignment'].create({'name': 'Completion ' + capability,
                'company_id': cls.company.id, 'department_id': cls.department.id,
                'user_id': cls.manager.id, 'capability': capability, 'date_start': '2020-01-01', 'reason': 'Synthetic test'})

    def document(self, start, end, period='week'):
        return self.env['tp.report.document'].with_user(self.author).create({
            'name': 'Completion synthetic', 'company_id': self.company.id, 'department_id': self.department.id,
            'owner_id': self.author.id, 'reviewer_id': self.manager.id, 'period_type': period,
            'date_start': start, 'date_end': end, 'summary': 'Synthetic result',
        })

    def test_crossmonth_fact_partition_and_conflict(self):
        facts = [{'contribution_key': 'stable', 'work_date': '2026-11-30', 'unit': 'item', 'quantity': 2},
                 {'contribution_key': 'stable', 'work_date': '2026-12-01', 'unit': 'item', 'quantity': 3}]
        self.assertEqual(len(dated_facts([{'lines': facts}, {'lines': facts}], '2026-11-01', '2026-11-30')), 1)
        conflict = dict(facts[0], quantity=7)
        with self.assertRaises(ValidationError):
            dated_facts([{'lines': facts}, {'lines': [conflict]}], '2026-11-01', '2026-11-30')

    def test_personal_rollup_requires_request_and_uses_snapshot(self):
        weekly = self.document('2026-11-30', '2026-12-06')
        self.env['tp.report.line'].with_user(self.author).create([
            {'document_id': weekly.id, 'name': 'November', 'work_date': '2026-11-30', 'quantity': 2, 'unit': 'item', 'contribution_key': 'shared'},
            {'document_id': weekly.id, 'name': 'December', 'work_date': '2026-12-01', 'quantity': 3, 'unit': 'item', 'contribution_key': 'shared'},
        ])
        weekly.action_submit()
        monthly = self.document('2026-11-01', '2026-11-30', 'month')
        with self.assertRaises(ValidationError):
            monthly.action_aggregate()
        self.env['tp.report.obligation'].with_user(self.manager).create({
            'name': 'Requested month', 'company_id': self.company.id, 'department_id': self.department.id,
            'owner_id': self.author.id, 'period_type': 'month', 'date_start': monthly.date_start, 'date_end': monthly.date_end,
        })
        monthly.action_aggregate()
        self.assertEqual(len(monthly.line_ids), 1)
        self.assertEqual(monthly.line_ids.quantity, 2)
        self.assertIn(weekly.current_snapshot_id, monthly.dependency_ids)
        monthly.action_aggregate()
        self.assertEqual(len(monthly.line_ids), 1)

    def test_carry_does_not_copy_actual_and_is_idempotent(self):
        source = self.document('2026-11-02', '2026-11-08')
        line = self.env['tp.report.line'].with_user(self.author).create({
            'document_id': source.id, 'name': 'Unfinished', 'work_date': source.date_start,
            'quantity': 5, 'unit': 'item', 'contribution_key': 'stable-source', 'work_status': 'partial',
        })
        target = self.document('2026-11-09', '2026-11-15')
        wizard = self.env['tp.report.carry.work'].with_user(self.author).create({
            'line_id': line.id, 'target_document_id': target.id, 'work_date': target.date_start, 'reason': 'Still pending',
        })
        wizard = wizard.with_context(tp_reporting_expected_version=target.version)
        wizard.action_carry()
        wizard.action_carry()
        self.assertEqual(len(target.line_ids), 1)
        carried = target.line_ids
        self.assertEqual(carried.stable_key, line.stable_key)
        self.assertEqual(carried.contribution_key, line.contribution_key)
        self.assertFalse(carried.quantity_known)
        self.assertIsNone(carried._fact()['quantity'])

    def test_required_template_content_is_snapshotted(self):
        template = self.env['tp.report.template'].create({'name': 'Required template', 'code': 'COMPLETION_REQUIRED', 'level': 'personal'})
        section = self.env['tp.report.section'].create({'name': 'Required specialist input', 'template_id': template.id, 'required': True})
        doc = self.document('2026-11-02', '2026-11-08')
        doc.with_context(tp_reporting_expected_version=doc.version).write({'template_id': template.id})
        with self.assertRaises(ValidationError):
            doc.action_submit()
        content = self.env['tp.report.section.content'].with_user(self.author).create({
            'document_id': doc.id, 'section_id': section.id, 'content': 'Specialist detail', 'design_stage': 'bvtc',
        })
        doc.action_submit()
        payload = json.loads(doc.current_snapshot_id.payload)
        self.assertEqual(payload['section_contents'][0]['content'], 'Specialist detail')
        with self.assertRaises(AccessError):
            content.write({'content': 'Rewrite submitted content'})

    def test_emergent_work_requires_reason_and_assigner(self):
        doc = self.document('2026-11-02', '2026-11-08')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['tp.report.line'].with_user(self.author).create({
                'document_id': doc.id, 'name': 'Emergent', 'work_date': doc.date_start,
                'contribution_key': 'emergent', 'is_emergent': True,
            })

    def test_provenance_cannot_be_forged_in_rpc_or_nested_lines(self):
        doc = self.document('2026-11-02', '2026-11-08')
        values = {'name': 'Forged', 'work_date': doc.date_start, 'contribution_key': 'forged', 'rollup_source': True}
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env['tp.report.line'].with_user(self.author).create(dict(values, document_id=doc.id))
        with self.assertRaises(AccessError), self.cr.savepoint():
            doc.with_context(tp_reporting_expected_version=doc.version).write({'line_ids': [Command.create(values)]})

    def test_copy_tree_new_period_draft_and_retry(self):
        plan_model = self.env['tp.report.plan'].with_user(self.manager)
        quarter = plan_model.create({'name': 'Source quarter', 'company_id': self.company.id,
            'department_id': self.department.id, 'owner_id': self.manager.id, 'period_type': 'quarter',
            'date_start': '2026-10-01', 'date_end': '2026-12-31', 'target': 10, 'unit': 'item'})
        plan_model.create({'name': 'Source month', 'company_id': self.company.id,
            'department_id': self.department.id, 'owner_id': self.manager.id, 'period_type': 'month',
            'date_start': '2026-11-01', 'date_end': '2026-11-30', 'parent_id': quarter.id, 'target': 3, 'unit': 'item'})
        wizard = self.env['tp.report.copy.plan'].with_user(self.manager).create({'source_id': quarter.id, 'target_start': '2027-01-01'})
        action = wizard.action_copy()
        self.assertEqual(wizard.action_copy()['res_id'], action['res_id'])
        copied = plan_model.browse(action['res_id'])
        self.assertEqual(str(copied.date_start), '2027-01-01')
        self.assertEqual(copied.state, 'draft')
        self.assertFalse(copied.baseline)
        self.assertEqual(len(copied.child_ids), 1)
        self.assertEqual(str(copied.child_ids.date_start), '2027-02-01')
