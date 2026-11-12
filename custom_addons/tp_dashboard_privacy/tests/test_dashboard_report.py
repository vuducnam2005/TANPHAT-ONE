import json

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestConnectedDashboard(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref('tp_core.group_manager') | cls.env.ref('spreadsheet_dashboard.group_dashboard_manager')
        cls.projects = cls.env['project.project'].create([
            {'name': 'Fictional A', 'tp_code': 'DASH-TEST-A', 'company_id': cls.env.company.id},
            {'name': 'Fictional B', 'tp_code': 'DASH-TEST-B', 'company_id': cls.env.company.id},
        ])
        for project in cls.projects:
            project._create_analytic_account()
        cls.invoice = cls.init_invoice('out_invoice', amounts=[100], taxes=cls.env['account.tax'])
        cls.invoice.invoice_line_ids.analytic_distribution = {
            str(cls.projects[0].account_id.id): 60, str(cls.projects[1].account_id.id): 40,
        }
        cls.config = {'version': 1, 'kind': 'finance', 'company_id': cls.env.company.id,
                      'project_ids': cls.projects.ids, 'invoice_ids': cls.invoice.ids, 'expense_ids': []}
        cls.reader = new_test_user(cls.env, login='dash_ui_reader', groups='base.group_user')
        cls.outside = new_test_user(cls.env, login='dash_ui_outside', groups='base.group_user')
        cls.dashboard = cls.env['spreadsheet.dashboard'].create({
            'name': 'Fictional report', 'dashboard_group_id': cls.env['spreadsheet.dashboard.group'].create({'name': 'Test'}).id,
            'group_ids': [Command.clear()], 'allowed_user_ids': [Command.set([cls.reader.id])],
            'company_ids': [Command.set([cls.env.company.id])], 'tp_internal_only': True,
            'spreadsheet_data': json.dumps({'settings': {'tpDashboard': cls.config}}),
        })
        binding = cls.env['ir.model.data'].search([
            ('module', '=', 'tp_native_data002_20261102'), ('name', '=', 'dashboard_finance_draft')])
        if binding:
            binding.res_id = cls.dashboard.id
        else:
            cls.env['ir.model.data'].create({'module': 'tp_native_data002_20261102',
                                            'name': 'dashboard_finance_draft',
                                            'model': 'spreadsheet.dashboard', 'res_id': cls.dashboard.id})

    def test_split_allocation_unique_count_and_scoped_drilldown(self):
        report = self.dashboard.tp_dashboard_report()
        self.assertEqual(report['raw']['invoice'], 100)
        self.assertEqual(report['raw']['invoice_count'], 1)
        self.assertEqual([i['value'] for i in report['charts'][0]['items']], [60, 40])
        for project, amount in zip(self.projects, [60, 40], strict=True):
            scoped = self.dashboard.tp_dashboard_report({'project_id': project.id})
            self.assertEqual(scoped['raw']['invoice'], amount)
            action = self.dashboard.tp_dashboard_action('invoices', {'project_id': project.id})
            self.assertEqual(action['domain'], [('id', 'in', self.invoice.ids)])

    def test_empty_date_and_refresh_are_live(self):
        self.assertTrue(self.dashboard.tp_dashboard_report({'date_from': '2100-01-01'})['empty'])
        self.invoice.invoice_line_ids.price_unit = 200
        self.assertEqual(self.dashboard.tp_dashboard_report()['raw']['invoice'], 200)
        self.assertEqual(self.dashboard.tp_dashboard_action('invoices', {'date_from': '2100-01-01'})['domain'], [('id', 'in', [])])

    def test_currency_rounding_split_preserves_total_and_filters(self):
        self.invoice.invoice_line_ids.price_unit = 0.01
        self.invoice.invoice_line_ids.analytic_distribution = {str(p.account_id.id): 50 for p in self.projects}
        all_values = [item['value'] for item in self.dashboard.tp_dashboard_report()['charts'][0]['items']]
        self.assertAlmostEqual(sum(all_values), self.invoice.amount_total)
        for project, expected in zip(self.projects, all_values, strict=True):
            self.assertEqual(self.dashboard.tp_dashboard_report({'project_id': project.id})['raw']['invoice'], expected)

    def test_dates_and_scope_are_validated(self):
        for filters in ({'date_from': 'broken'}, {'date_from': '2026-02-02', 'date_to': '2026-01-01'}, {'unknown': 1}):
            with self.assertRaises(ValidationError):
                self.dashboard.tp_dashboard_report(filters)
        with self.assertRaises(AccessError):
            self.dashboard.tp_dashboard_report({'project_id': 99999999})
        with self.assertRaises(ValidationError):
            self.dashboard.tp_dashboard_action('invoices', {'project_id': self.projects[0].id}, self.projects[1].id)

    def test_outside_denied_report_and_drilldown(self):
        for method, args in (('tp_dashboard_report', []), ('tp_dashboard_action', ['invoices'])):
            with self.assertRaises(AccessError):
                getattr(self.dashboard.with_user(self.outside), method)(*args)

    def test_source_acl_failure_is_not_zero(self):
        with self.assertRaises(AccessError):
            self.dashboard.with_user(self.reader).tp_dashboard_report()

    def test_ambiguous_combined_analytic_key_fails(self):
        self.invoice.invoice_line_ids.analytic_distribution = {','.join(str(p.account_id.id) for p in self.projects): 100}
        with self.assertRaises(UserError):
            self.dashboard.tp_dashboard_report()

    def test_zero_allocation_is_not_a_scoped_document(self):
        self.invoice.invoice_line_ids.analytic_distribution = {str(self.projects[0].account_id.id): 0}
        self.assertEqual(self.dashboard.tp_dashboard_report()['raw']['invoice_count'], 0)

    def test_shared_project_analytic_account_is_rejected(self):
        self.projects[1].account_id = self.projects[0].account_id
        with self.assertRaises(UserError):
            self.dashboard.tp_dashboard_report()

    def test_other_company_context_is_rejected(self):
        config = {**self.config, 'company_id': self.env['res.company'].create({'name': 'Other fictional company'}).id}
        self.dashboard.spreadsheet_data = json.dumps({'settings': {'tpDashboard': config}})
        with self.assertRaises(AccessError):
            self.dashboard.with_context(allowed_company_ids=[self.config['company_id']]).tp_dashboard_report()

    def test_currency_mismatch_fails(self):
        self.invoice.currency_id = self.env.ref('base.EUR') if self.env.company.currency_id != self.env.ref('base.EUR') else self.env.ref('base.USD')
        with self.assertRaises(UserError):
            self.dashboard.tp_dashboard_report()

    def test_forged_kind_or_unbound_dashboard_denied(self):
        copy = self.dashboard.copy()
        with self.assertRaises(ValidationError):
            copy.tp_dashboard_report()
        self.dashboard.spreadsheet_data = json.dumps({'settings': {'tpDashboard': {**self.config, 'kind': 'unknown'}}})
        with self.assertRaises(ValidationError):
            self.dashboard.tp_dashboard_report()

    def test_native_dashboard_keeps_native_payload(self):
        native = self.dashboard.copy({'spreadsheet_data': '{"sheets": []}', 'tp_internal_only': False})
        result = json.loads(native.with_user(self.reader)._get_serialized_readonly_dashboard())
        self.assertEqual(result['tp_dashboard'], {'kind': None, 'internal': False})

    def test_action_invalid_source_and_state(self):
        for source, state in (('unsafe', None), ('invoices', 'draft'), ('expenses', 'paid'), ([], None), ('expenses', ['draft'])):
            with self.assertRaises(ValidationError):
                self.dashboard.tp_dashboard_action(source, state=state)

    def test_expense_metrics_exclude_refused_and_state_their_scope(self):
        # NATIVE-STABILIZE-001: expense metrics are requests in draft/submitted/approved only,
        # never refused/posted/paid, and the metric text must say so instead of implying cash paid.
        # Fixture rows are created as superuser; the report itself still runs with the
        # synthetic test user's own rights (expense manager, so its search sees the rows).
        self.env.user.group_ids |= self.env.ref('hr_expense.group_hr_expense_manager')
        employee = self.env['hr.employee'].sudo().create({'name': 'Fictional expense employee', 'company_id': self.env.company.id})
        # A no-cost expense product, as hr_expense requires one outside draft (cf. product_c in core tests).
        product = self.env['product.product'].sudo().create({'name': 'Fictional expense product', 'can_be_expensed': True,
                                                             'taxes_id': [Command.clear()], 'supplier_taxes_id': [Command.clear()]})
        expenses = self.env['hr.expense'].sudo().create([{
            'name': name, 'employee_id': employee.id, 'company_id': self.env.company.id, 'product_id': product.id,
            'total_amount_currency': amount, 'analytic_distribution': {str(self.projects[0].account_id.id): 100},
        } for name, amount in (('Draft fictional', 10), ('Approved fictional', 20), ('Refused fictional', 40))])
        expenses[1].approval_state = 'approved'
        expenses[2].approval_state = 'refused'
        self.assertEqual(expenses.mapped('state'), ['draft', 'approved', 'refused'])
        self.dashboard.spreadsheet_data = json.dumps({'settings': {'tpDashboard': {**self.config, 'expense_ids': expenses.ids}}})
        report = self.dashboard.tp_dashboard_report()
        self.assertEqual(report['raw']['expense_count'], 2)
        self.assertEqual((report['raw']['draft'], report['raw']['submitted'], report['raw']['approved']), (10, 0, 20))
        count, total = [m for m in report['metrics'] if m['source'] == 'expenses']
        for metric in (count, total):
            self.assertIn('không gồm', metric['detail'])
            self.assertIn('Bị từ chối', metric['detail'])
        self.assertTrue(total['detail'].startswith('Chưa phải số đã chi.'))
        action = self.dashboard.tp_dashboard_action('expenses')
        self.assertEqual(action['domain'], [('id', 'in', sorted(expenses[:2].ids))])
