from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDelegatedReportingScope(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.main = cls.env.ref('base.user_admin')
        cls.departments = cls.env['hr.department'].create([
            {'name': 'Synthetic report scope ' + name, 'company_id': cls.company.id}
            for name in ('Own', 'Other')
        ])
        cls.actor, cls.coworker, cls.author = cls.env['res.users'].with_context(no_reset_password=True).create([
            {'name': 'Synthetic report scope ' + str(index), 'login': 'synthetic.report.scope.' + str(index),
             'company_id': cls.company.id, 'company_ids': [Command.set(cls.company.ids)],
             'group_ids': [Command.set([cls.env.ref('tp_reporting.group_reporting_user').id])]}
            for index in range(3)
        ])
        cls.employees = cls.env['hr.employee'].create([
            {'name': user.name, 'user_id': user.id, 'company_id': cls.company.id,
             'department_id': cls.departments[index // 2].id}
            for index, user in enumerate((cls.actor, cls.coworker, cls.author))
        ])

    def change(self, operation='grant'):
        self.env['tp.admin.delegation'].with_user(self.main)._change(
            self.actor, self.company, operation, 'Synthetic reporting source scope')

    def document(self, owner, start='2026-11-02', end='2026-11-08', **extra):
        department = self.departments[1] if owner == self.author else self.departments[0]
        return self.env['tp.report.document'].with_user(owner).create({
            'name': 'Synthetic scoped personal report', 'company_id': self.company.id,
            'department_id': department.id, 'owner_id': owner.id, 'period_type': 'week',
            'date_start': start, 'date_end': end, 'summary': 'Synthetic work result', **extra,
        })

    def test_plain_outside_read_only_and_own_baseline_preserved(self):
        own = self.document(self.actor).with_user(self.actor)
        coworker = self.document(self.coworker).with_user(self.actor)
        other = self.document(self.author).with_user(self.actor)
        self.assertTrue(own.has_access('read'))
        self.assertFalse(coworker.has_access('read'))
        self.assertFalse(other.has_access('read'))
        self.change()
        self.assertEqual(other.read(['summary'])[0]['summary'], 'Synthetic work result')
        self.assertTrue(own.has_access('read'))
        self.assertFalse(coworker.has_access('read'))
        with self.assertRaises(AccessError):
            other.with_context(tp_reporting_expected_version=other.version).write({'summary': 'Unauthorized edit'})
        with self.assertRaises(AccessError):
            other._require('review')
        self.change('revoke')
        self.assertFalse(other.has_access('read'))
        self.assertTrue(own.has_access('read'))
        self.assertFalse(coworker.has_access('read'))

    def test_task_line_source_closes_plain_report_scope(self):
        self.author.group_ids = [Command.link(self.env.ref('project.group_project_user').id)]
        project = self.env['project.project'].create({'name': 'Synthetic report task project'})
        task = self.env['project.task'].create({'name': 'Synthetic source task', 'project_id': project.id})
        document = self.document(self.author)
        self.env['tp.report.line'].with_user(self.author).create({
            'document_id': document.id, 'name': 'Synthetic task source', 'task_id': task.id,
            'work_date': '2026-11-03', 'contribution_key': 'synthetic-task-source',
        })
        self.change()
        self.assertFalse(document.with_user(self.actor).has_access('read'))

    def test_snapshot_and_financial_sources_remain_baseline(self):
        self.env['tp.report.assignment'].create({
            'name': 'Synthetic report reviewer', 'user_id': self.main.id, 'capability': 'review',
            'company_id': self.company.id, 'department_id': self.departments[1].id,
            'reason': 'Synthetic report workflow',
        })
        submitted = self.document(self.author, reviewer_id=self.main.id)
        submitted.action_submit()
        snapshot = submitted.current_snapshot_id
        self.author.group_ids = [Command.link(self.env.ref('tp_reporting.group_reporting_finance').id)]
        self.env['tp.report.assignment'].create({
            'name': 'Synthetic financial source', 'user_id': self.author.id, 'capability': 'finance_enter',
            'company_id': self.company.id, 'department_id': self.departments[1].id,
            'reason': 'Synthetic report value source',
        })
        document = self.document(self.author, '2026-11-09', '2026-11-15')
        metric = self.env['tp.report.metric'].create({
            'name': 'Synthetic report metric', 'code': 'AD-SYNTH-REPORT-SOURCE',
            'unit': 'VND', 'definition': 'Synthetic scope regression',
        })
        value = self.env['tp.report.value'].with_user(self.author).create({
            'name': 'Synthetic source value', 'document_id': document.id, 'metric_id': metric.id,
            'coverage_key': 'synthetic-report-source',
        })
        self.change()
        self.assertFalse(submitted.with_user(self.actor).has_access('read'))
        self.assertFalse(snapshot.with_user(self.actor).has_access('read'))
        self.assertFalse(document.with_user(self.actor).has_access('read'))
        self.assertFalse(value.with_user(self.actor).has_access('read'))

    def test_carried_historical_line_source_remains_baseline(self):
        origin_document = self.document(self.author)
        origin = self.env['tp.report.line'].with_user(self.author).create({
            'document_id': origin_document.id, 'name': 'Synthetic original result',
            'work_date': '2026-11-03', 'contribution_key': 'synthetic-carried-source',
            'result': 'Synthetic historical source payload',
        })
        document = self.document(self.author, '2026-11-09', '2026-11-15')
        carry = self.env['tp.report.carry.work'].with_user(self.author).with_context(
            tp_reporting_expected_version=document.version).create({
                'line_id': origin.id, 'target_document_id': document.id,
                'work_date': '2026-11-10', 'reason': 'Synthetic carry regression',
            })
        carry.action_carry()
        self.change()
        self.assertFalse(document.with_user(self.actor).has_access('read'))
