import json

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import MONEY_TOKENS, DemoWorkspaceCommon
from odoo.addons.tp_contract.exceptions import ContractWorkflowError


@tagged('post_install', '-at_install')
class TestDemoProjection(DemoWorkspaceCommon):
    """What each demo actor receives from the read projection behind the client actions."""

    def test_overview_actor_dashboard(self):
        data = self.projection(self.lanhdao).get_dashboard()
        kpis = {kpi['key']: kpi['value'] for kpi in data['kpis']}
        self.assertEqual(kpis, {'projects': 3, 'open_tasks': 16, 'overdue_tasks': 4, 'reviews': 3,
                                'documents': 4, 'opportunities': 9})
        self.assertEqual((data['viewer']['project_count'], data['viewer']['financial_project_count']), (3, 3))
        self.assertTrue(data['viewer']['business'])
        # A KPI click opens the same domain it counted.
        for kpi in data['kpis']:
            model = self.env['ir.actions.act_window']._for_xml_id(kpi['action'])['res_model']
            self.assertEqual(self.env[model].with_user(self.lanhdao).search_count(kpi['domain']), kpi['value'], kpi['key'])
        self.assertEqual({item['key'].split('-')[0] for item in data['attention']}, {'returned', 'review', 'task', 'unassigned'})

    def test_restricted_actor_dashboard(self):
        data = self.projection(self.kysu).get_dashboard()
        kpis = {kpi['key']: kpi['value'] for kpi in data['kpis']}
        self.assertEqual(kpis, {'projects': 1, 'open_tasks': 5, 'overdue_tasks': 1, 'reviews': 1, 'documents': 1})
        self.assertEqual([chain['code'] for chain in data['chains']], ['DEMO-DUONG-02'])
        self.assertNotIn('opportunity', [node['key'] for chain in data['chains'] for node in chain['nodes']])
        self.assertEqual([lens['key'] for lens in data['lenses']], ['executive', 'delivery', 'finance'])
        locked = [module['key'] for lane in data['lanes'] for module in lane['modules'] if module['locked']]
        self.assertIn('crm', locked)
        self.assertIn('bid', locked)

    def test_restricted_actor_never_receives_amounts(self):
        Projection = self.projection(self.kysu)
        project = self.projects['duong']
        payloads = {
            'dashboard': Projection.get_dashboard(),
            'overview': Projection.get_project_overview(project.id),
            'flow': Projection.get_contract_flow(),
            'finance': Projection.get_finance(),
            'request': Projection.get_showcase('request'),
            'staffing': Projection.get_showcase('staffing'),
        }
        for name, payload in payloads.items():
            text = json.dumps(payload, ensure_ascii=False)
            for token in MONEY_TOKENS:
                self.assertNotIn(token, text, f'{name} leaks {token}')
        overview = payloads['overview']
        self.assertFalse(overview['project']['financial_read'])
        self.assertEqual({doc['confidentiality'] for doc in overview['documents']}, {'general'})
        self.assertIsNone(overview['contracts'][0]['revision']['value'])
        finance = payloads['finance']['projects']
        self.assertEqual([(p['code'], p['financial_read'], p['rows'], p['totals']) for p in finance],
                         [('DEMO-DUONG-02', False, [], [])])
        amounts = {row['key']: row['columns']['amount'] for row in payloads['request']['rows']}
        self.assertEqual(set(amounts), {'RQ-DEMO-003', 'RQ-DEMO-004'})
        self.assertEqual(amounts['RQ-DEMO-003'], 'Cần quyền financial.read')

    def test_restricted_actor_cannot_open_other_projects(self):
        Projection = self.projection(self.kysu)
        denied = Projection.get_project_overview(self.projects['cau'].id)
        self.assertTrue(denied['denied'])
        self.assertIsNone(denied['project'])
        self.assertEqual([p['code'] for p in denied['projects']], ['DEMO-DUONG-02'])
        flow = Projection.get_contract_flow()
        self.assertEqual({row['project'] for row in flow['revisions']}, {'DEMO-DUONG-02'})
        self.assertEqual({row['project'] for row in Projection.get_showcase('survey')['rows']}, {'DEMO-DUONG-02'})
        with self.assertRaises(AccessError):
            Projection.get_showcase('bid')

    def test_overview_actor_finance_keeps_currencies_and_review_state_apart(self):
        finance = self.projection(self.lanhdao).get_finance()
        by_code = {row['code']: row for project in finance['projects'] for row in project['rows']}
        self.assertTrue(by_code['DEMO-HD-CAU-01']['reviewed'])
        self.assertFalse(by_code['DEMO-HD-CAU-02']['reviewed'])
        self.assertIsNone(by_code['DEMO-HD-NUT-01']['value'])
        self.assertEqual(by_code['DEMO-HD-NUT-01']['value_status'], 'Chưa đủ số tiền xác nhận')
        totals = {project['code']: project['totals'] for project in finance['projects']}
        # Only the reviewed contract counts; draft, returned and in-review values stay out of every total.
        self.assertEqual([total['currency'] for total in totals['DEMO-CAU-01']], ['VND'])
        self.assertEqual(totals['DEMO-DUONG-02'], [])
        self.assertEqual(totals['DEMO-NUT-03'], [])
        self.assertIsNone(by_code['DEMO-HD-CAU-02']['accepted'])
        self.assertEqual({source['nature'] for source in finance['sources']}, {'real', 'illustrative', 'absent'})

    def test_unknown_screen_and_non_viewer(self):
        with self.assertRaises(UserError):
            self.projection(self.lanhdao).get_showcase('payroll')
        with self.assertRaises(AccessError):
            self.projection(self.drafter).get_dashboard()


@tagged('post_install', '-at_install')
class TestDemoSecurity(DemoWorkspaceCommon):
    """Native search, read_group, export and writes keep the canonical rules for demo actors."""

    def test_restricted_actor_native_reads(self):
        user = self.kysu
        Amount = self.env['tp.contract.line.amount'].with_user(user)
        self.assertFalse(Amount.search([]))
        [(total, count)] = Amount.read_group([], [], ['amount:sum', '__count'])
        self.assertFalse(total)
        self.assertEqual(count, 0)
        Document = self.env['tp.contract.document'].with_user(user)
        documents = Document.search([])
        self.assertEqual(set(documents.mapped('confidentiality')), {'general'})
        with self.assertRaises(UserError):
            documents.export_data(['name'])  # demo actors have no export right at all
        # Even with the export right, export reads through the same record rules.
        user.group_ids += self.env.ref('base.group_allow_export')
        exported = Document.search([]).export_data(['name', 'project_id/tp_code'])['datas']
        financial = self.env['tp.contract.document'].search([('confidentiality', '=', 'financial')])
        self.assertTrue(financial)
        self.assertEqual({row[1] for row in exported}, {'DEMO-DUONG-02'})
        self.assertFalse({row[0] for row in exported} & set(financial.mapped('name')))
        groups = Document.read_group([], ['confidentiality'], ['__count'])
        self.assertEqual([group[0] for group in groups], ['general'])
        # Public read_group returns ids; private to-dos (no project) are not project data.
        tasks = self.env['project.task'].with_user(user).read_group([('project_id', '!=', False)], ['project_id'], ['__count'])
        self.assertEqual([group[0] for group in tasks], [self.projects['duong'].id])
        with self.assertRaises(AccessError):
            self.env['crm.lead'].with_user(user).search([])
        hidden = self.contracts['returned']
        with self.assertRaises(AccessError):
            hidden.with_user(user).read(['code'])

    def test_overview_actor_sees_amounts_through_the_grant(self):
        amounts = self.env['tp.contract.line.amount'].with_user(self.lanhdao).search([])
        self.assertEqual(set(amounts.mapped('project_id.tp_code')), {'DEMO-CAU-01', 'DEMO-DUONG-02', 'DEMO-NUT-03'})
        financial = self.env['tp.contract.document'].with_user(self.lanhdao).search([('confidentiality', '=', 'financial')])
        self.assertEqual(len(financial), 2)
        self.assertTrue(self.env['crm.lead'].with_user(self.lanhdao).search_count([]))

    def test_direct_writes_are_blocked(self):
        task = self.env['project.task'].search([('project_id', '=', self.projects['duong'].id)], limit=1)
        contract = self.contracts['in_review']
        revision = contract.revision_ids[-1:]
        lead = self.env['crm.lead'].search([('name', 'ilike', '(DEMO)')], limit=1)
        project = self.projects['duong']
        for user in (self.lanhdao, self.kysu):
            for record, values in ((task, {'name': 'x'}), (contract, {'name': 'x'}), (revision, {'review_state': 'review_complete'}),
                                   (contract, {'lifecycle_state': 'effective'}), (project, {'name': 'x'})):
                with self.subTest(user=user.login, model=record._name, field=next(iter(values))), self.assertRaises(AccessError):
                    record.with_user(user).write(values)
            with self.assertRaises(AccessError):
                self.env['tp.project.grant'].with_user(user).create({
                    'project_id': project.id, 'user_id': user.id, 'capability': 'financial_read', 'reason': 'self grant',
                })
        with self.assertRaises(AccessError):
            lead.with_user(self.lanhdao).write({'name': 'x'})
        self.assertEqual(revision.review_state, 'in_review')

    def test_demo_actors_cannot_drive_the_workflow(self):
        draft = self.contracts['draft']
        revision = draft.revision_ids[-1:]
        for user in (self.lanhdao, self.kysu):
            with self.subTest(user=user.login), self.assertRaises(ContractWorkflowError), self.env.cr.savepoint():
                self.env['tp.contract.workflow'].with_user(user)._tp_run(
                    'submit_review', {'expected_version': draft.aggregate_version, 'reviewer_id': self.reviewer.id},
                    key=f'demo-test-{user.id}-submit', contract_id=draft.id, revision_id=revision.id)
        self.assertEqual(revision.review_state, 'draft')
