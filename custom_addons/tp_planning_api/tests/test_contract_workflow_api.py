from uuid import uuid4

from odoo.tests.common import HttpCase

from odoo.addons.tp_contract.tests.common import TpContractWorkflowCommon

MONEY_KEYS = ('"total"', '"amount"', '"approved_amount"')


class TestContractWorkflowApi(HttpCase, TpContractWorkflowCommon):
    """CTR-002a write endpoints with synthetic actors (DEC-020)."""

    def _login(self, user):
        self.authenticate(user.login, user.login)
        me = self.url_open('/api/v1/me', allow_redirects=False)
        self.assertEqual(me.status_code, 200)
        self.csrf = me.json()['data']['csrf_token']

    def _send(self, url, payload, *, method='POST', key=None, headers=None, csrf=True):
        sent = {'Idempotency-Key': key or f'http-{uuid4().hex}'}
        if csrf:
            sent['X-CSRF-Token'] = self.csrf
        sent |= headers or {}
        response = self.url_open(url, json=payload, headers=sent, method=method, allow_redirects=False)
        self.assertEqual(response.headers.get('Cache-Control'), 'no-store', url)
        return response

    def _ok(self, response, status=200):
        self.assertEqual(response.status_code, status, response.text)
        return response.json()['data']

    def _problem(self, response, status, code):
        self.assertEqual(response.status_code, status, response.text)
        error = response.json()['error']
        self.assertEqual(error['code'], code)
        return error

    def _get(self, url):
        return self._ok(self.url_open(url, allow_redirects=False))

    def _create(self, code='HD-HTTP-01', **headers):
        return self._send('/api/v1/contracts', {
            'project_id': self.project_a.id, 'code': code, 'name': 'Synthetic HTTP contract',
            'contract_type': 'owner', 'currency': 'VND',
            'lines': [
                {'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount('100')},
                {'scope_key': 'L2', 'name': 'Design', 'amount': self._amount('50')},
            ],
        }, headers=headers or None)

    @staticmethod
    def _revision_url(data, suffix=''):
        return f"/api/v1/contracts/{data['contract_id']}/revisions/{data['revision_id']}{suffix}"

    def test_p01_draft_submit_return_rework_resubmit_over_http(self):
        self._login(self.editor)
        created = self._ok(self._create(), 201)
        self.assertEqual((created['review_state'], created['submission_id'], created['replayed']), ('draft', None, False))
        contract = self._get(f"/api/v1/contracts/{created['contract_id']}")
        self.assertEqual(contract['version'], created['version'])
        self.assertEqual(contract['department'], {'id': self.dept_kd.id, 'name': self.dept_kd.name})
        self.assertEqual(contract['working_revision_id'], created['revision_id'])
        self.assertEqual(contract['allowed_actions'], [])
        self.assertTrue(contract['permissions']['draft_edit'] and contract['permissions']['submit'])
        self.assertFalse(contract['permissions']['review_commercial'])
        revision = self._get(self._revision_url(created))
        self.assertEqual(revision['allowed_actions'], ['edit_draft', 'submit_review'])
        self.assertEqual([line['amount']['value'] for line in revision['lines']], ['100', '50'])

        edited = self._ok(self._send(self._revision_url(created), {
            'expected_version': created['version'], 'revision': {'name': 'R0 after edit'},
        }, method='PATCH'))
        self.assertEqual(edited['version'], created['version'] + 1)
        self.assertEqual(self._get(f"/api/v1/contracts/{created['contract_id']}/reviewers"),
                         [{'id': self.reviewer.id, 'name': self.reviewer.name}])

        submit = {'expected_version': edited['version'], 'reviewer_id': self.reviewer.id}
        key = f'http-{uuid4().hex}'
        submitted = self._send(self._revision_url(created, '/submit'), submit, key=key)
        first = self._ok(submitted)
        self.assertEqual(first['review_state'], 'in_review')
        self.assertIsNone(submitted.headers.get('Idempotency-Replayed'))
        replay = self._send(self._revision_url(created, '/submit'), submit, key=key)
        self.assertEqual(replay.headers.get('Idempotency-Replayed'), 'true')
        self.assertEqual(self._ok(replay) | {'replayed': False}, first)
        self._problem(self._send(self._revision_url(created, '/submit'), submit | {'fix_summary': 'other'}, key=key),
                      409, 'idempotency_conflict')

        self._login(self.reviewer)
        revision = self._get(self._revision_url(created))
        self.assertEqual(revision['allowed_actions'], ['return_review'])
        self.assertEqual([(item['sequence'], item['outcome']) for item in revision['submissions']], [(1, 'pending')])
        returned_url = self._revision_url(created, '/return')
        self._problem(self._send(returned_url, {'expected_version': first['version'], 'reason': '  '}), 422, 'reason_required')
        stale = self._problem(self._send(returned_url, {'expected_version': edited['version'], 'reason': 'x'}), 409, 'stale_version')
        self.assertEqual(stale['details'], {'current_version': first['version']})
        returned = self._ok(self._send(returned_url, {
            'expected_version': first['version'], 'reason': 'Design scope unclear',
            'issues': [{'scope_key': 'L2', 'note': 'Split design phases'}],
        }))
        self.assertEqual(returned['review_state'], 'returned')

        self._login(self.editor)
        reworked = self._ok(self._send(self._revision_url(created, '/rework'), {
            'expected_version': returned['version'], 'reason': 'Fix design scope',
        }))
        self.assertEqual(reworked['review_state'], 'draft')
        resubmit = {'expected_version': reworked['version'], 'reviewer_id': self.reviewer.id}
        self._problem(self._send(self._revision_url(created, '/submit'), resubmit), 422, 'fix_summary_required')
        again = self._ok(self._send(self._revision_url(created, '/submit'), resubmit | {'fix_summary': 'Design split'}))
        self.assertEqual(again['review_state'], 'in_review')
        history = self._get(self._revision_url(created))['submissions']
        self.assertEqual([(item['sequence'], item['outcome']) for item in history], [(1, 'returned'), (2, 'pending')])
        self.assertEqual(history[0]['return_issues'], [{'scope_key': 'L2', 'note': 'Split design phases'}])
        self.assertEqual(history[0]['rework_reason'], 'Fix design scope')

    def test_n07_authentication_csrf_origin_and_body_guards(self):
        Contract = self.env['tp.contract']
        self.authenticate(None, None)
        self._problem(self.url_open('/api/v1/contracts', json={}, method='POST', allow_redirects=False), 401, 'unauthenticated')

        self._login(self.editor)
        guarded = [
            ({}, False, 403, 'csrf_invalid'),
            ({'X-CSRF-Token': 'not-a-token'}, False, 403, 'csrf_invalid'),
            ({'Origin': 'https://attacker.example'}, True, 403, 'cross_origin'),
            ({'Sec-Fetch-Site': 'cross-site'}, True, 403, 'cross_origin'),
            ({'Idempotency-Key': 'short'}, True, 400, 'invalid_request'),
        ]
        for headers, csrf, status, code in guarded:
            with self.subTest(headers=headers):
                self._problem(self._send('/api/v1/contracts', {'project_id': self.project_a.id}, headers=headers, csrf=csrf),
                              status, code)
        common = {'X-CSRF-Token': self.csrf, 'Idempotency-Key': f'http-{uuid4().hex}'}
        plain = self.url_open('/api/v1/contracts', data='{}', method='POST', allow_redirects=False,
                              headers=common | {'Content-Type': 'text/plain'})
        self._problem(plain, 415, 'unsupported_media_type')
        for body in ('{not json', '[]'):
            response = self.url_open('/api/v1/contracts', data=body, method='POST', allow_redirects=False,
                                     headers=common | {'Content-Type': 'application/json'})
            self._problem(response, 400, 'invalid_request')
        self._problem(self._send('/api/v1/contracts?project_id=1', {}), 400, 'invalid_request')
        self.assertFalse(Contract.search_count([('code', '=like', 'HD-HTTP-%')]))

        same_origin = self._create(Origin=self.base_url(), **{'Sec-Fetch-Site': 'same-origin'})
        self._ok(same_origin, 201)
        self.assertEqual(Contract.search_count([('code', '=like', 'HD-HTTP-%')]), 1)

    def test_n01_n02_scope_capability_and_money_over_http(self):
        self._login(self.editor)
        created = self._ok(self._create(), 201)

        self._login(self.meta_editor)
        revision = self.url_open(self._revision_url(created), allow_redirects=False)
        data = self._ok(revision)
        self.assertEqual(data['allowed_actions'], ['edit_draft'])
        self.assertEqual(data['permissions'], {
            'financial_read': False, 'draft_edit': True, 'financial_draft_edit': False,
            'submit': False, 'review_commercial': False,
        })
        for key in MONEY_KEYS:
            self.assertNotIn(key, revision.text)
        money = {
            'expected_version': data['contract_version'],
            'lines': [{'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount('120')}],
        }
        error = self._problem(self._send(self._revision_url(created), money, method='PATCH'), 403, 'forbidden')
        self.assertEqual(error['details'], {'missing_capabilities': ['financial_read', 'financial_draft_edit']})
        self._problem(self.url_open(f"/api/v1/contracts/{created['contract_id']}/reviewers", allow_redirects=False),
                      403, 'forbidden')
        edited = self._send(self._revision_url(created), {
            'expected_version': data['contract_version'],
            'lines': [{'scope_key': 'L1', 'name': 'Survey (renamed)'}, {'scope_key': 'L2', 'name': 'Design'}],
        }, method='PATCH')
        self._ok(edited)
        for key in MONEY_KEYS:
            self.assertNotIn(key, edited.text)

        self._login(self.reviewer)
        self._problem(self._send(self._revision_url(created, '/submit'), {
            'expected_version': data['contract_version'] + 1, 'reviewer_id': self.reviewer.id,
        }), 403, 'forbidden')

        self._login(self.other_project)
        self._problem(self.url_open(f"/api/v1/contracts/{created['contract_id']}", allow_redirects=False), 404, 'not_found')
        self._problem(self._send(self._revision_url(created, '/submit'), {
            'expected_version': data['contract_version'] + 1, 'reviewer_id': self.reviewer.id,
        }), 404, 'not_found')
