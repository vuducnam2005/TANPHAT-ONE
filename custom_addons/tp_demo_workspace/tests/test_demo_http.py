from odoo.tests import HttpCase, tagged

from .common import MONEY_TOKENS, DemoWorkspaceCommon


@tagged('post_install', '-at_install')
class TestDemoHttp(HttpCase, DemoWorkspaceCommon):
    """Native session, JSON-RPC and direct file download as the restricted demo actor."""

    def call(self, model, method, *args, **kwargs):
        return self.url_open(f'/web/dataset/call_kw/{model}/{method}', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'model': model, 'method': method, 'args': list(args), 'kwargs': kwargs},
        })

    def documents(self, confidentiality):
        return self.env['tp.contract.document'].search([
            ('project_id', '=', self.projects['duong'].id), ('confidentiality', '=', confidentiality)])

    def test_restricted_actor_rpc_and_download(self):
        self.authenticate('demo.kysu', self.passwords['demo.kysu'])
        for method, args in (('get_dashboard', ()), ('get_finance', ()), ('get_contract_flow', ()),
                             ('get_project_overview', (self.projects['duong'].id,))):
            response = self.call('tp.demo.workspace', method, *args)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('"error"', response.text, method)
            for token in MONEY_TOKENS:
                self.assertNotIn(token, response.text, f'{method} leaks {token}')
        denied = self.call('crm.lead', 'search_read', [], fields=['name', 'expected_revenue'])
        self.assertIn('AccessError', denied.text)
        self.assertNotIn('(DEMO)', denied.text)
        bid = self.call('tp.demo.workspace', 'get_showcase', 'bid')
        self.assertIn('AccessError', bid.text)

        financial, general = self.documents('financial'), self.documents('general')
        self.assertTrue(financial and general)
        blocked = self.url_open(f'/web/content/tp.contract.document/{financial.id}/file')
        self.assertIn(blocked.status_code, (403, 404))
        self.assertNotIn('vùng tài chính', blocked.text)
        allowed = self.url_open(f'/web/content/tp.contract.document/{general.id}/file')
        self.assertEqual(allowed.status_code, 200)
        self.assertIn('Phạm vi kỹ thuật giả lập', allowed.content.decode())

    def test_overview_actor_downloads_financial_file(self):
        self.authenticate('demo.lanhdao', self.passwords['demo.lanhdao'])
        response = self.url_open(f"/web/content/tp.contract.document/{self.documents('financial').id}/file")
        self.assertEqual(response.status_code, 200)
        self.assertIn('vùng tài chính', response.content.decode())

    def test_demo_actor_home_is_the_dashboard(self):
        self.authenticate('demo.kysu', self.passwords['demo.kysu'])
        response = self.url_open('/odoo')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.kysu.action_id.id, self.env.ref('tp_demo_workspace.action_demo_dashboard').id)
