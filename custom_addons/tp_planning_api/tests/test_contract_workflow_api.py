from uuid import uuid4

from odoo.tests.common import HttpCase, new_test_user

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
        self.assertTrue(response.json()['meta']['request_id'])
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

    def _create_payload(self, code, **changes):
        payload = {
            'project_id': self.project_a.id, 'code': code, 'name': 'Synthetic HTTP contract',
            'contract_type': 'owner', 'currency': 'VND',
            'lines': [
                {'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount('100')},
            ],
        }
        payload.update(changes)
        return payload

    def _workflow_counts(self):
        models = (
            'tp.contract', 'tp.contract.revision', 'tp.contract.line', 'tp.contract.line.amount',
            'tp.contract.submission', 'tp.contract.submission.amount', 'tp.contract.audit',
            'tp.contract.outbox', 'tp.contract.idempotency',
        )
        return tuple(self.env[model].sudo().search_count([]) for model in models)

    def _dual_capability_actor(self):
        user = new_test_user(
            self.env, login='tp_wf_http_dual', groups='tp_core.group_user', company_id=self.company.id,
        )
        self._assign(self.project_a, user)
        self._caps(
            user, 'contract_draft_edit', 'contract_submit', 'contract_review_commercial',
            'financial_read', 'financial_draft_edit',
        )
        return user

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

    def test_v01_invalid_enums_are_controlled_and_side_effect_free(self):
        self._login(self.editor)
        Contract = self.env['tp.contract']
        invalid_values = ([], {}, None, True, False)
        enum_inputs = (
            ('contract_type', 'body.contract_type', 'contract.contract_type'),
            ('state', 'lines[0].amount.state', 'lines[0].amount.state'),
            ('tax_basis', 'lines[0].amount.tax_basis', 'lines[0].amount.tax_basis'),
        )
        created = self._ok(self._create('HD-HTTP-V01-PATCH-BASE'), 201)
        revision_url = self._revision_url(created)
        version = created['version']
        test_index = 0

        for enum_name, post_field, patch_field in enum_inputs:
            for invalid_value in invalid_values:
                with self.subTest(enum=enum_name, value=invalid_value):
                    test_index += 1
                    code = f'HD-HTTP-V01-{test_index:02d}'
                    key = f'http-v01-post-{test_index:02d}'
                    payload_changes = {}
                    amount = self._amount('100')
                    if enum_name == 'contract_type':
                        payload_changes['contract_type'] = invalid_value
                    else:
                        amount[enum_name] = invalid_value
                        payload_changes['lines'] = [{'scope_key': 'L1', 'name': 'Survey', 'amount': amount}]
                    payload = self._create_payload(code, **payload_changes)
                    before = self._workflow_counts()
                    response = self._send('/api/v1/contracts', payload, key=key)
                    error = self._problem(response, 400, 'invalid_request')
                    self.assertEqual(error['details'], {'field': post_field})
                    self.assertTrue(response.json()['meta']['request_id'])
                    self.assertFalse(Contract.search([('code', '=', code)]))
                    self.assertEqual(self._workflow_counts(), before)

                    valid_payload = self._create_payload(code)
                    created_retry = self._ok(self._send('/api/v1/contracts', valid_payload, key=key), 201)
                    self.assertEqual(created_retry['review_state'], 'draft')
                    after_create = self._workflow_counts()
                    replay = self._send('/api/v1/contracts', valid_payload, key=key)
                    self.assertEqual(replay.headers.get('Idempotency-Replayed'), 'true')
                    self.assertEqual(self._workflow_counts(), after_create)

                    patch_key = f'http-v01-patch-{test_index:02d}'
                    patch_amount = self._amount('100')
                    patch_contract = {}
                    patch_lines = None
                    if enum_name == 'contract_type':
                        patch_contract['contract_type'] = invalid_value
                    else:
                        patch_amount[enum_name] = invalid_value
                        patch_lines = [{'scope_key': 'L1', 'name': 'Survey', 'amount': patch_amount}]
                    bad_patch = {'expected_version': version}
                    if patch_contract:
                        bad_patch['contract'] = patch_contract
                    if patch_lines:
                        bad_patch['lines'] = patch_lines
                    before_patch = self._workflow_counts()
                    before_version = Contract.browse(created['contract_id']).aggregate_version
                    response = self._send(revision_url, bad_patch, method='PATCH', key=patch_key)
                    error = self._problem(response, 400, 'invalid_request')
                    self.assertEqual(error['details'], {'field': patch_field})
                    self.assertTrue(response.json()['meta']['request_id'])
                    self.assertEqual(self._workflow_counts(), before_patch)
                    self.assertEqual(Contract.browse(created['contract_id']).aggregate_version, before_version)

                    valid_patch = {'expected_version': version, 'revision': {'name': f'Valid retry {test_index}'}}
                    patched = self._ok(self._send(revision_url, valid_patch, method='PATCH', key=patch_key))
                    self.assertEqual(patched['version'], version + 1)
                    after_patch = self._workflow_counts()
                    replay = self._send(revision_url, valid_patch, method='PATCH', key=patch_key)
                    self.assertEqual(replay.headers.get('Idempotency-Replayed'), 'true')
                    self.assertEqual(self._workflow_counts(), after_patch)
                    version += 1

    def test_v02_currency_validation_rolls_back_and_allows_same_key_retry(self):
        self._login(self.editor)
        Contract = self.env['tp.contract']
        blank_values = ('', '   ', '\t\n', None)
        for index, blank_value in enumerate(blank_values, start=1):
            with self.subTest(blank=repr(blank_value)):
                code = f'HD-HTTP-V02-BLANK-{index}'
                key = f'http-v02-postblank-{index}'
                before = self._workflow_counts()
                error = self._problem(self._send(
                    '/api/v1/contracts', self._create_payload(code, currency=blank_value), key=key,
                ), 400, 'invalid_request')
                self.assertEqual(error['details'], {'field': 'body.currency'})
                self.assertFalse(Contract.search([('code', '=', code)]))
                self.assertEqual(self._workflow_counts(), before)
                created = self._ok(self._send('/api/v1/contracts', self._create_payload(code), key=key), 201)
                self.assertEqual(created['review_state'], 'draft')
                after_create = self._workflow_counts()
                replay = self._send('/api/v1/contracts', self._create_payload(code), key=key)
                self.assertEqual(replay.headers.get('Idempotency-Replayed'), 'true')
                self.assertEqual(self._workflow_counts(), after_create)

                revision_url = self._revision_url(created)
                version = created['version']
                patch_key = f'http-v02-patchblank-{index}'
                before_patch = self._workflow_counts()
                error = self._problem(self._send(revision_url, {
                    'expected_version': version, 'contract': {'currency': blank_value},
                }, method='PATCH', key=patch_key), 400, 'invalid_request')
                self.assertEqual(error['details'], {'field': 'contract.currency'})
                contract = Contract.browse(created['contract_id'])
                self.assertEqual(self._workflow_counts(), before_patch)
                self.assertEqual((contract.currency_id.name, contract.aggregate_version), ('VND', version))
                valid_patch = self._ok(self._send(revision_url, {
                    'expected_version': version, 'contract': {'name': f'Valid retry {index}'},
                }, method='PATCH', key=patch_key))
                self.assertEqual(valid_patch['version'], version + 1)
                after_patch = self._workflow_counts()
                replay = self._send(revision_url, {
                    'expected_version': version, 'contract': {'name': f'Valid retry {index}'},
                }, method='PATCH', key=patch_key)
                self.assertEqual(replay.headers.get('Idempotency-Replayed'), 'true')
                self.assertEqual(self._workflow_counts(), after_patch)

        unknown_code = 'HD-HTTP-V02-UNKNOWN'
        unknown_key = 'http-v02-unknown'
        before_unknown = self._workflow_counts()
        unknown = self._problem(
            self._send('/api/v1/contracts', self._create_payload(unknown_code, currency='ZZZ'), key=unknown_key),
            422, 'unknown_currency',
        )
        self.assertEqual(unknown['details'], {'field': 'currency'})
        self.assertFalse(Contract.search([('code', '=', unknown_code)]))
        self.assertEqual(self._workflow_counts(), before_unknown)
        retried = self._ok(self._send('/api/v1/contracts', self._create_payload(unknown_code), key=unknown_key), 201)
        self.assertEqual(retried['review_state'], 'draft')
        after_unknown_retry = self._workflow_counts()
        replay = self._send('/api/v1/contracts', self._create_payload(unknown_code), key=unknown_key)
        self.assertEqual(replay.headers.get('Idempotency-Replayed'), 'true')
        self.assertEqual(self._workflow_counts(), after_unknown_retry)

        revision_url = self._revision_url(retried)
        version = retried['version']
        before_unknown_patch = self._workflow_counts()
        unknown_patch = self._problem(self._send(revision_url, {
            'expected_version': version, 'contract': {'currency': 'ZZZ'},
        }, method='PATCH', key='http-v02-patch-unknown'), 422, 'unknown_currency')
        self.assertEqual(unknown_patch['details'], {'field': 'currency'})
        contract = Contract.browse(retried['contract_id'])
        self.assertEqual(self._workflow_counts(), before_unknown_patch)
        self.assertEqual((contract.currency_id.name, contract.aggregate_version), ('VND', version))
        normalized = self._ok(self._send(revision_url, {
            'expected_version': version, 'contract': {'currency': 'vnd'},
        }, method='PATCH', key='http-v02-patch-unknown'))
        self.assertEqual(normalized['version'], version + 1)
        self.assertEqual(Contract.browse(retried['contract_id']).currency_id.name, 'VND')

        omitted = self._ok(self._send(revision_url, {
            'expected_version': normalized['version'], 'contract': {'name': 'Currency omitted stays VND'},
        }, method='PATCH', key='http-v02-patch-omitted'))
        self.assertEqual(Contract.browse(retried['contract_id']).currency_id.name, 'VND')
        self.assertEqual(omitted['version'], normalized['version'] + 1)

    def test_dual_capability_actor_cannot_self_review_submit_resubmit_or_legacy_pending(self):
        dual = self._dual_capability_actor()
        self._login(dual)
        created = self._ok(self._create('HD-HTTP-DUAL'), 201)
        revision_url = self._revision_url(created)
        reviewers = self._get(f"/api/v1/contracts/{created['contract_id']}/reviewers")
        self.assertEqual(reviewers, [{'id': self.reviewer.id, 'name': self.reviewer.name}])

        before_self_submit = self._workflow_counts()
        self_error = self._problem(self._send(f'{revision_url}/submit', {
            'expected_version': created['version'], 'reviewer_id': dual.id,
        }), 422, 'reviewer_ineligible')
        self.assertEqual(self_error['details'], {'field': 'reviewer_id'})
        self.assertEqual(self._workflow_counts(), before_self_submit)
        draft = self._get(revision_url)
        self.assertEqual((draft['review_state'], draft['contract_version'], draft['submissions']),
                         ('draft', created['version'], []))

        submitted = self._ok(self._send(f'{revision_url}/submit', {
            'expected_version': created['version'], 'reviewer_id': self.reviewer.id,
        }))
        self._login(self.reviewer)
        returned = self._ok(self._send(f'{revision_url}/return', {
            'expected_version': submitted['version'], 'reason': 'Clarify the synthetic scope',
        }))
        self._login(dual)
        reworked = self._ok(self._send(f'{revision_url}/rework', {
            'expected_version': returned['version'], 'reason': 'Clarified the synthetic scope',
        }))
        before_self_resubmit = self._workflow_counts()
        resubmit_error = self._problem(self._send(f'{revision_url}/submit', {
            'expected_version': reworked['version'], 'reviewer_id': dual.id, 'fix_summary': 'Clarified scope',
        }), 422, 'reviewer_ineligible')
        self.assertEqual(resubmit_error['details'], {'field': 'reviewer_id'})
        self.assertEqual(self._workflow_counts(), before_self_resubmit)
        draft = self._get(revision_url)
        self.assertEqual((draft['review_state'], draft['contract_version']), ('draft', reworked['version']))
        self.assertEqual([(item['sequence'], item['outcome']) for item in draft['submissions']], [(1, 'returned')])

        # A pre-fix pending submission can exist in a legacy database. Simulate
        # that state without invoking a currently forbidden workflow action.
        legacy = self._ok(self._create('HD-HTTP-DUAL-LEGACY'), 201)
        legacy_url = self._revision_url(legacy)
        legacy_submission = self._ok(self._send(f'{legacy_url}/submit', {
            'expected_version': legacy['version'], 'reviewer_id': self.reviewer.id,
        }))
        self.env.flush_all()
        self.env.cr.execute(
            'UPDATE tp_contract_submission SET reviewer_id = %s WHERE id = %s',
            (dual.id, legacy_submission['submission_id']),
        )
        self.env.flush_all()
        self.env.invalidate_all()
        self._login(dual)
        pending = self._get(legacy_url)
        self.assertNotIn('return_review', pending['allowed_actions'])
        before_legacy_return = self._workflow_counts()
        legacy_error = self._problem(self._send(f'{legacy_url}/return', {
            'expected_version': legacy_submission['version'], 'reason': 'Legacy self-review stays blocked',
        }), 422, 'reviewer_ineligible')
        self.assertEqual(legacy_error['details'], {'field': 'reviewer_id'})
        self.assertEqual(self._workflow_counts(), before_legacy_return)

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
