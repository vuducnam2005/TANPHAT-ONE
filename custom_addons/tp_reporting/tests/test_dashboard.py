from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'corp_report001')
class TestReportingDashboard(TransactionCase):
    def test_denominator_drilldown_privacy_and_missing_actual(self):
        company = self.env.company
        department = self.env['hr.department'].create({'name': 'Dashboard test', 'company_id': company.id})
        group = self.env.ref('tp_reporting.group_reporting_user')
        author, manager, outsider = self.env['res.users'].create([
            {'name': role, 'login': 'corp-dash-' + role,
             'company_id': company.id, 'company_ids': [Command.set(company.ids)],
             'group_ids': [Command.set(group.ids)]}
            for role in ('author', 'manager', 'outsider')
        ])
        for capability in ('read', 'review', 'consolidate', 'plan', 'plan_issue'):
            self.env['tp.report.assignment'].create({
                'name': 'Dashboard ' + capability, 'user_id': manager.id,
                'capability': capability, 'company_id': company.id,
                'department_id': department.id, 'date_start': '2020-01-01', 'reason': 'Test only',
            })
        documents = self.env['tp.report.document'].with_user(author)
        obligations = self.env['tp.report.obligation'].with_user(manager)
        linked = []
        for start, end in [('2026-11-02', '2026-11-08'), ('2026-11-09', '2026-11-15')]:
            doc = documents.create({'name': 'Dashboard draft', 'company_id': company.id,
                                    'department_id': department.id, 'owner_id': author.id,
                                    'reviewer_id': manager.id, 'summary': 'Test',
                                    'date_start': start, 'date_end': end})
            linked.append(doc)
            obligations.create({'name': 'Dashboard obligation', 'company_id': company.id,
                                'department_id': department.id, 'owner_id': author.id,
                                'period_type': 'week', 'date_start': start, 'date_end': end,
                                'document_id': doc.id})
        linked[0].action_submit(expected_version=linked[0].version)
        linked[0].with_user(manager).action_return(reason='Test returned', expected_version=linked[0].version)
        obligations.create({'name': 'Dashboard exempt', 'company_id': company.id,
                            'department_id': department.id, 'owner_id': author.id,
                            'period_type': 'week', 'date_start': '2026-11-16', 'date_end': '2026-11-22',
                            'state': 'exempt', 'reason': 'Test only'})
        plan = self.env['tp.report.plan'].with_user(manager).create({
            'name': 'Dashboard no actual', 'company_id': company.id, 'department_id': department.id,
            'owner_id': author.id, 'period_type': 'quarter', 'date_start': '2026-10-01',
            'date_end': '2026-12-31', 'target': 10, 'unit': 'hồ sơ',
        })
        plan.action_submit(expected_version=plan.version)
        plan.action_issue(expected_version=plan.version)
        dashboard = self.env['tp.report.dashboard'].with_user(manager)
        result = dashboard.get_data('2026-10-01', '2026-12-31')
        self.assertEqual(result['submission']['total'], 3)
        self.assertEqual({item['key']: item['count'] for item in result['submission']['items']},
                         {'submitted': 1, 'pending': 1, 'exempt': 1})
        for item in result['submission']['items']:
            self.assertEqual(self.env[item['model']].with_user(manager).search_count(item['domain']), item['count'])
        self.assertIsNone(result['plan_actual'][0]['actual'])
        outside = self.env['tp.report.dashboard'].with_user(outsider).get_data('2026-10-01', '2026-12-31')
        self.assertEqual(outside['submission']['total'], 0)
        self.assertFalse(outside['plan_actual'])
        self.assertFalse(outside['scopes'])

    def test_reject_invalid_period_inputs(self):
        dashboard = self.env['tp.report.dashboard']
        for args in [('2026-12-31', '2026-01-01'), ('2020-01-01', '2026-12-31'),
                     ('2026-01-01', '2026-12-31', 'invalid'),
                     ('2026-01-01', '2026-12-31', 'quarter', True)]:
            with self.assertRaises(ValidationError):
                dashboard.get_data(*args)
