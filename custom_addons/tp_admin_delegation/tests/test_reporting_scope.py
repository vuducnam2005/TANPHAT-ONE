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

    def reviewer(self, capability='review'):
        return self.env['tp.report.assignment'].create({
            'name': 'Synthetic report ' + capability, 'user_id': self.main.id, 'capability': capability,
            'company_id': self.company.id, 'department_id': self.departments[1].id,
            'reason': 'Synthetic report workflow',
        })

    def test_submitted_outside_read_only_draft_and_own_baseline_preserved(self):
        self.reviewer()
        own = self.document(self.actor).with_user(self.actor)
        coworker = self.document(self.coworker).with_user(self.actor)
        draft = self.document(self.author).with_user(self.actor)
        submitted = self.document(self.author, '2026-11-09', '2026-11-15', reviewer_id=self.main.id)
        submitted.action_submit()
        other = submitted.with_user(self.actor)
        self.assertTrue(own.has_access('read'))
        self.assertFalse(coworker.has_access('read'))
        self.assertFalse(other.has_access('read'))
        self.change()
        self.assertEqual(other.read(['summary'])[0]['summary'], 'Synthetic work result')
        self.assertTrue(other.current_snapshot_id.has_access('read'))
        # Drafts stay private to their author, as for any scoped manager.
        self.assertFalse(draft.has_access('read'))
        self.assertTrue(own.has_access('read'))
        self.assertFalse(coworker.has_access('read'))
        with self.assertRaises(AccessError):
            other.with_context(tp_reporting_expected_version=other.version).write({'summary': 'Unauthorized edit'})
        with self.assertRaises(AccessError):
            other._require('review')
        with self.assertRaises(AccessError):
            other._require('finalize')
        self.change('revoke')
        self.assertFalse(other.has_access('read'))
        self.assertTrue(own.has_access('read'))
        self.assertFalse(coworker.has_access('read'))

    def test_plan_tree_obligation_directive_and_dashboard_share_scope(self):
        def plan(name, owner, department, period, parent=False):
            return self.env['tp.report.plan'].create({
                'name': name, 'owner_id': owner.id, 'company_id': self.company.id,
                'department_id': department.id, 'period_type': period, 'parent_id': parent and parent.id,
                'date_start': '2026-10-01', 'date_end': '2026-12-31', 'target': 10, 'unit': 'việc',
            })
        quarter = plan('Synthetic quarter', self.author, self.departments[1], 'quarter')
        month = plan('Synthetic month', self.author, self.departments[1], 'month', quarter)
        week = plan('Synthetic week', self.author, self.departments[1], 'week', month)
        obligations = self.env['tp.report.obligation'].create([
            {'name': 'Synthetic obligation ' + user.name, 'owner_id': user.id, 'company_id': self.company.id,
             'department_id': department.id, 'period_type': 'week',
             'date_start': '2026-11-02', 'date_end': '2026-11-08'}
            for user, department in ((self.author, self.departments[1]), (self.coworker, self.departments[0]))
        ])
        self.reviewer()
        self.reviewer('direct')
        source = self.document(self.author, reviewer_id=self.main.id)
        source.action_submit()
        directive = self.env['tp.report.directive'].with_user(self.main).create({
            'name': 'Synthetic directive', 'document_id': source.id, 'owner_id': self.author.id,
            'company_id': self.company.id, 'department_id': self.departments[1].id,
        })
        plans = self.env['tp.report.plan'].with_user(self.actor)
        self.change()
        self.assertEqual(plans.search([('id', 'in', (quarter | month | week).ids)]), quarter | month | week)
        visible = self.env['tp.report.obligation'].with_user(self.actor).search([('id', 'in', obligations.ids)])
        self.assertEqual(visible, obligations[0])
        self.assertTrue(directive.with_user(self.actor).has_access('read'))
        with self.assertRaises(AccessError):
            directive.with_user(self.actor).action_start()
        with self.assertRaises(AccessError):
            obligations[0].with_user(self.actor).write({'reason': 'Synthetic delegated exemption'})
        data = self.env['tp.report.dashboard'].with_user(self.actor).get_data('2026-10-01', '2026-12-31', 'quarter')
        self.assertTrue(data['delegated_scope'])
        self.assertEqual(data['submission']['total'], 1)
        # One own-department node closes the whole tree; nothing is half-opened.
        plan('Synthetic own branch', self.coworker, self.departments[0], 'week', month)
        self.assertFalse(plans.search([('id', 'in', (quarter | month | week).ids)]))
        self.change('revoke')
        self.assertFalse(directive.with_user(self.actor).has_access('read'))
        self.assertFalse(obligations[0].with_user(self.actor).has_access('read'))

    def test_main_admin_configures_without_business_authority(self):
        self.assertTrue(self.main.has_group('tp_reporting.group_reporting_config'))
        data = self.env['tp.report.dashboard'].with_user(self.main).get_data('2026-10-01', '2026-12-31', 'quarter')
        self.assertNotIn('delegated_scope', data)
        with self.assertRaises(AccessError):
            self.env['tp.report.assignment'].with_user(self.main).create({
                'name': 'Synthetic self grant', 'user_id': self.main.id, 'capability': 'finalize',
                'company_id': self.company.id, 'reason': 'Synthetic escalation attempt',
            })

    def test_task_line_source_closes_plain_report_scope(self):
        self.reviewer()
        self.author.group_ids = [Command.link(self.env.ref('project.group_project_user').id)]
        project = self.env['project.project'].create({'name': 'Synthetic report task project'})
        task = self.env['project.task'].create({'name': 'Synthetic source task', 'project_id': project.id})
        document = self.document(self.author, reviewer_id=self.main.id)
        self.env['tp.report.line'].with_user(self.author).create({
            'document_id': document.id, 'name': 'Synthetic task source', 'task_id': task.id,
            'work_date': '2026-11-03', 'contribution_key': 'synthetic-task-source',
        })
        document.action_submit()
        self.change()
        self.assertFalse(document.with_user(self.actor).has_access('read'))

    def test_traced_snapshot_opens_and_financial_source_remains_baseline(self):
        self.reviewer()
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
        # A signed snapshot whose payload traces to open sources is readable, never writable.
        self.assertTrue(submitted.with_user(self.actor).has_access('read'))
        self.assertTrue(snapshot.with_user(self.actor).has_access('read'))
        self.assertFalse(snapshot.with_user(self.actor).has_access('write'))
        self.assertFalse(document.with_user(self.actor).has_access('read'))
        self.assertFalse(value.with_user(self.actor).has_access('read'))

    def test_carried_historical_line_source_remains_baseline(self):
        self.reviewer()
        origin_document = self.document(self.author)
        origin = self.env['tp.report.line'].with_user(self.author).create({
            'document_id': origin_document.id, 'name': 'Synthetic original result',
            'work_date': '2026-11-03', 'contribution_key': 'synthetic-carried-source',
            'result': 'Synthetic historical source payload',
        })
        document = self.document(self.author, '2026-11-09', '2026-11-15', reviewer_id=self.main.id)
        carry = self.env['tp.report.carry.work'].with_user(self.author).with_context(
            tp_reporting_expected_version=document.version).create({
                'line_id': origin.id, 'target_document_id': document.id,
                'work_date': '2026-11-10', 'reason': 'Synthetic carry regression',
            })
        carry.action_carry()
        document.action_submit()
        self.change()
        self.assertFalse(document.with_user(self.actor).has_access('read'))
