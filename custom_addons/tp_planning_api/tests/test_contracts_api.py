from odoo.tests.common import HttpCase, new_test_user

from odoo.addons.tp_contract.tests.common import TpContractCommon

MONEY_KEYS = ('"total"', '"amount"', '"approved_amount"')


class TestContractsApi(HttpCase, TpContractCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.internal = new_test_user(cls.env, login='tp_ctr_api_internal', groups='base.group_user')

    def _get(self, url):
        response = self.url_open(url, allow_redirects=False)
        self.assertEqual(response.headers.get('Cache-Control'), 'no-store', url)
        return response

    def _login(self, user):
        self.authenticate(user.login, user.login)

    def test_authentication_and_platform_group(self):
        self.authenticate(None, None)
        self.assertEqual(self._get('/api/v1/contracts').status_code, 401)
        self._login(self.internal)
        self.assertEqual(self._get('/api/v1/contracts').status_code, 403)

    def test_metadata_reader_gets_no_money_anywhere(self):
        self._login(self.reader)
        listing = self._get('/api/v1/contracts')
        self.assertEqual(listing.status_code, 200)
        self.assertEqual([item['id'] for item in listing.json()['data']], [self.contract_a.id])
        self.assertFalse(listing.json()['meta']['pagination']['has_more'])

        detail = self._get(f'/api/v1/contracts/{self.contract_a.id}?as_of=2026-11-01')
        self.assertEqual(detail.status_code, 200)
        data = detail.json()['data']
        self.assertFalse(data['permissions']['financial_read'])
        self.assertEqual(data['effective_snapshot']['revision_id'], self.amendment.id)
        self.assertEqual([doc['id'] for doc in data['documents']], [self.general_doc.id])
        revision = self._get(f'/api/v1/contracts/{self.contract_a.id}/revisions/{self.amendment.id}')
        self.assertEqual(revision.status_code, 200)
        self.assertEqual([line['scope_key'] for line in revision.json()['data']['lines']], ['X', 'Y'])
        for response in (listing, detail, revision):
            for key in MONEY_KEYS:
                self.assertNotIn(key, response.text)

    def test_cross_project_contract_is_not_found(self):
        self._login(self.reader)
        self.assertEqual(self._get(f'/api/v1/contracts/{self.contract_b.id}').status_code, 404)
        self.assertEqual(self._get(f'/api/v1/contracts/{self.contract_b.id}/revisions/{self.revision_b.id}').status_code, 404)
        self.assertEqual(self._get(f'/api/v1/contracts?project_id={self.project_b.id}').json()['data'], [])

    def test_c1_effective_total_is_replaced_not_added(self):
        self._login(self.finance_a)
        before = self._get(f'/api/v1/contracts/{self.contract_a.id}?as_of=2026-10-31').json()['data']
        after = self._get(f'/api/v1/contracts/{self.contract_a.id}?as_of=2026-11-01').json()['data']
        self.assertTrue(before['permissions']['financial_read'])
        self.assertEqual(before['effective_snapshot']['revision_id'], self.original.id)
        self.assertEqual(before['effective_snapshot']['warnings'], ['future_revision_recorded'])
        self.assertEqual(before['effective_snapshot']['total'], {
            'value': '100', 'currency': 'VND', 'status': 'confirmed', 'tax_basis': 'unknown',
        })
        self.assertEqual(after['effective_snapshot']['revision_id'], self.amendment.id)
        self.assertEqual(after['effective_snapshot']['total']['value'], '110')
        approval = after['revisions'][1]['base_references'][0]
        self.assertEqual(approval['decision'], 'approved')
        self.assertEqual(approval['verification_state'], 'pending')
        self.assertFalse(approval['verified_result'])
        self.assertEqual(approval['approved_amount']['value'], '110')
        lines = self._get(f'/api/v1/contracts/{self.contract_a.id}/revisions/{self.amendment.id}').json()['data']['lines']
        self.assertEqual([line['amount']['value'] for line in lines], ['70', '40'])

    def test_metadata_on_a_and_financial_on_b(self):
        self._login(self.finance_b)
        contract_a = self._get(f'/api/v1/contracts/{self.contract_a.id}?as_of=2026-11-01')
        self.assertFalse(contract_a.json()['data']['permissions']['financial_read'])
        for key in MONEY_KEYS:
            self.assertNotIn(key, contract_a.text)
        contract_b = self._get(f'/api/v1/contracts/{self.contract_b.id}?as_of=2026-11-01').json()['data']
        self.assertTrue(contract_b['permissions']['financial_read'])
        self.assertEqual(contract_b['effective_snapshot']['total']['value'], '25')

    def test_unconfirmed_amount_is_null_not_zero(self):
        self.env['tp.contract.line.amount'].search([('line_id', '=', self.line_y2.id)]).write({
            'amount_state': 'unconfirmed', 'amount': 0,
        })
        self._login(self.finance_a)
        data = self._get(f'/api/v1/contracts/{self.contract_a.id}/revisions/{self.amendment.id}').json()['data']
        self.assertEqual(data['lines'][1]['amount'], {
            'value': None, 'currency': 'VND', 'status': 'unconfirmed', 'tax_basis': 'unknown',
        })
        self.assertEqual(data['total']['value'], None)
        self.assertEqual(data['total']['status'], 'incomplete')

    def test_revoked_grant_hides_money_on_next_request(self):
        self._login(self.finance_a)
        url = f'/api/v1/contracts/{self.contract_a.id}'
        self.assertIn('"total"', self._get(url).text)
        self.grant_a.active = False
        response = self._get(url)
        self.assertFalse(response.json()['data']['permissions']['financial_read'])
        self.assertNotIn('"total"', response.text)

    def test_revision_must_belong_to_contract(self):
        self._login(self.finance_b)
        self.assertEqual(self._get(f'/api/v1/contracts/{self.contract_a.id}/revisions/{self.revision_b.id}').status_code, 404)

    def test_input_validation(self):
        self._login(self.reader)
        base = f'/api/v1/contracts/{self.contract_a.id}'
        for url in (f'{base}?as_of=31/10/2026', f'{base}?company_id=1', '/api/v1/contracts?limit=0',
                    '/api/v1/contracts?project_id=x', f'{base}/revisions/{self.original.id}?as_of=2026-11-01'):
            with self.subTest(url=url):
                response = self._get(url)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()['error']['code'], 'invalid_request')

    def test_search_filters_metadata_only(self):
        self._login(self.finance_b)
        self.assertEqual([item['code'] for item in self._get('/api/v1/contracts?q=hd-b').json()['data']], ['HD-B'])
        projects = self._get(f'/api/v1/contracts?project_id={self.project_a.id}').json()['data']
        self.assertEqual([item['id'] for item in projects], [self.contract_a.id])

    def test_financial_document_download_requires_grant(self):
        url = f'/api/v1/contracts/{self.contract_a.id}/documents/{self.financial_doc.id}/content'
        for user in (self.reader, self.finance_b):
            with self.subTest(user=user.login):
                self._login(user)
                self.assertEqual(self._get(url).status_code, 404)
        self._login(self.finance_a)
        response = self._get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'synthetic signed amendment')
        self.assertIn('attachment', response.headers['Content-Disposition'])
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')

    def test_general_document_follows_project_scope(self):
        url = f'/api/v1/contracts/{self.contract_a.id}/documents/{self.general_doc.id}/content'
        self._login(self.reader)
        response = self._get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'synthetic scope')
        self._login(self.outsider)
        self.assertEqual(self._get(url).status_code, 404)
