"""UI-CTR-NATIVE-001a acceptance tests on synthetic data.

Maps docs/architecture/TP_UI_CTR_NATIVE_001_SPEC.md section 14: AT-01..AT-11 and
AT-14..AT-18 run here; AT-12 (browser) and AT-13 (regression) run outside Odoo
tests. Every check names its user; the test methods themselves run as superuser.
"""
import re
from contextlib import contextmanager
from unittest.mock import patch

from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError, MissingError, RedirectWarning, UserError
from odoo.service.model import call_kw
from odoo.tests.common import freeze_time, new_test_user
from odoo.tools.safe_eval import safe_eval

from .common import TpContractWorkflowCommon
from odoo.addons.tp_contract.exceptions import ContractWorkflowError

MODELS = {
    'draft': 'tp.contract.native.draft',
    'line': 'tp.contract.native.draft.line',
    'amount': 'tp.contract.native.amount.input',
    'amendment': 'tp.contract.native.amendment',
    'submit': 'tp.contract.native.submit',
    'return': 'tp.contract.native.return',
    'issue': 'tp.contract.native.return.issue',
    'rework': 'tp.contract.native.rework',
}
HEADERS = ('draft', 'amendment', 'submit', 'return', 'rework')
ACL_SUFFIX = {
    'draft': 'draft', 'line': 'draft_line', 'amount': 'amount_input', 'amendment': 'amendment',
    'submit': 'submit', 'return': 'return', 'issue': 'return_issue', 'rework': 'rework',
}
WRITABLE = {
    'draft': ('revision_name', 'Forged'), 'line': ('name', 'Forged'), 'amount': ('value', '1'),
    'amendment': ('name', 'Forged'), 'submit': ('fix_summary', 'Forged'), 'return': ('reason', 'Forged'),
    'issue': ('note', 'Forged'), 'rework': ('reason', 'Forged'),
}
L1_AMOUNT = '7654321'
NEW_AMOUNT = '1234567'
MONEY_TOKENS = ('7654321', '7,654,321', '7.654.321', '1234567', '1,234,567', '1.234.567')
VIETNAMESE = r'[ăâđêôơưàảãáạằẳẵắặầẩẫấậèẻẽéẹềểễếệìỉĩíịòỏõóọồổỗốộờởỡớợùủũúụừửữứựỳỷỹýỵ]'
RAW_MONEY_FIELDS = {'amount', 'amount_ids', 'amount_id', 'financial_snapshot', 'amount_input_ids'}
DRAFT_SPEC = {
    'mode': {}, 'revision_name': {},
    'line_ids': {'fields': {'scope_key': {}, 'name': {}, 'current_amount_text': {}}},
}
DRAFT_MONEY_SPEC = DRAFT_SPEC | {
    'amount_input_ids': {'fields': {'scope_key': {}, 'amount_state': {}, 'value': {}, 'tax_basis': {}}},
}


class TestContractNativeUi(TpContractWorkflowCommon):
    """UI-CTR-NATIVE-001a: native Odoo wizards over the CTR-002a workflow (DEC-030)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        def actor(login, groups='tp_core.group_user', project=None):
            user = new_test_user(cls.env, login=login, groups=groups, company_id=cls.company.id)
            if project:
                cls._assign(project, user)
            return user

        full = ('contract_draft_edit', 'contract_submit', 'financial_read', 'financial_draft_edit')
        cls.editor2 = actor('tp_nat_editor2', project=cls.project_a)
        cls._caps(cls.editor2, *full)
        cls.reviewer2 = actor('tp_nat_reviewer2', project=cls.project_a)
        cls._caps(cls.reviewer2, 'contract_review_commercial', 'financial_read', 'contract_submit', 'contract_draft_edit')
        cls.fin_meta = actor('tp_nat_fin_meta', project=cls.project_a)
        cls._caps(cls.fin_meta, 'contract_draft_edit', 'financial_read')
        cls.mgr_actor = actor('tp_nat_manager', groups='tp_core.group_user,tp_core.group_manager', project=cls.project_a)
        cls._caps(cls.mgr_actor, *full)
        cls.hr_expense_groups = [
            xmlid for xmlid in ('hr_expense.group_hr_expense_user', 'hr_expense.group_hr_expense_team_approver')
            if cls.env.ref(xmlid, raise_if_not_found=False)
        ]
        power_groups = ['tp_core.group_user', 'tp_core.group_manager', 'base.group_system', *cls.hr_expense_groups]
        cls.power = actor('tp_nat_power', groups=','.join(power_groups), project=cls.project_a)
        cls._caps(cls.power, *full)
        # Exercise export's record rules, rather than stopping at its separate UI permission.
        for user in (cls.reader | cls.finance_a | cls.finance_b | cls.manager | cls.editor | cls.editor2
                     | cls.reviewer | cls.reviewer2 | cls.meta_editor | cls.fin_meta | cls.mgr_actor | cls.power):
            cls._link_group(user, 'base.group_allow_export')
        # Project C: the editor may draft there but holds no financial.read.
        cls.project_c = cls._project('CTR-TEST-C')
        cls.project_c.tp_department_id = cls.dept_kd
        cls._assign(cls.project_c, cls.editor)
        cls._caps(cls.editor, 'contract_draft_edit', project=cls.project_c)
        # A managed project without a lead department cannot scope contracts.
        cls.project_nodept = cls._project('CTR-TEST-ND')
        cls._assign(cls.project_nodept, cls.editor)

    # Helpers

    def _native(self, key):
        model = MODELS[key]
        self.assertIn(model, self.env.registry, f'UI-CTR-NATIVE-001a model {model} is missing')
        return self.env[model]

    def _need_fields(self, model, *names):
        missing = [name for name in names if name not in self.env[model]._fields]
        self.assertFalse(missing, f'{model} lacks the native UI fields {missing}')

    def _ref(self, xmlid):
        record = self.env.ref(xmlid, raise_if_not_found=False)
        self.assertTrue(record, f'{xmlid} is missing')
        return record

    def _assert_no_money(self, text):
        for token in MONEY_TOKENS:
            self.assertNotIn(token, text)

    def _new_request(self):
        # The next HTTP request starts a new transaction: no record or access cache survives.
        self.env.flush_all()
        self.env.clear()

    def _draft_contract(self, code='HD-NAT-01', *, user=None, complete=False):
        result = self._run(user or self.editor, 'create_contract', {
            'project_id': self.project_a.id, 'code': code, 'name': f'Native {code}', 'contract_type': 'owner',
            'currency': 'VND',
            'lines': [
                {'scope_key': 'L1', 'name': 'Survey', 'amount': self._amount(L1_AMOUNT)},
                {'scope_key': 'L2', 'name': 'Design',
                 'amount': self._amount('100') if complete else self._amount(None, state='unconfirmed')},
            ],
        })
        return result['contract'].sudo(), result['revision'].sudo()

    def _submitted(self, code, *, reviewer=None):
        contract, revision = self._draft_contract(code, complete=True)
        result = self._run(self.editor, 'submit_review', {
            'expected_version': contract.aggregate_version, 'reviewer_id': (reviewer or self.reviewer).id,
        }, contract=contract, revision=revision)
        return contract, revision, result['submission'].sudo()

    def _edit(self, user, contract, revision, **vals):
        return self._native('draft').with_user(user).create({'contract_id': contract.id, 'revision_id': revision.id, **vals})

    def _header(self, key, user, contract, revision=None, **vals):
        target = {'contract_id': contract.id} | ({'revision_id': revision.id} if revision else {})
        return self._native(key).with_user(user).create(target | vals)

    def _amount_input(self, wizard, scope_key='L1', value=NEW_AMOUNT, *, state='confirmed', tax_basis='excluding_tax'):
        return self._native('amount').with_user(wizard.env.user).create({
            'wizard_id': wizard.id, 'scope_key': scope_key, 'amount_state': state, 'value': value, 'tax_basis': tax_basis,
        })

    def _audits(self, contract, action=None):
        domain = [('contract_id', '=', contract.id)] + ([('action', '=', action)] if action else [])
        return self.env['tp.contract.audit'].sudo().search(domain)

    def _assignment(self, user, project):
        return self.env['tp.project.assignment'].with_context(active_test=False).search([
            ('project_id', '=', project.id), ('user_id', '=', user.id),
        ])

    def _amount_texts(self, wizard):
        return dict(wizard.line_ids.mapped(lambda line: (line.scope_key, line.current_amount_text)))

    @contextmanager
    def _no_side_effects(self):
        models = ('tp.contract', 'tp.contract.revision', 'tp.contract.line', 'tp.contract.line.amount',
                  'tp.contract.submission', 'tp.contract.submission.amount', 'tp.contract.audit',
                  'tp.contract.outbox', 'tp.contract.idempotency')

        def snapshot():
            self.env.invalidate_all()
            counts = {model: self.env[model].sudo().with_context(active_test=False).search_count([]) for model in models}
            versions = dict(self.env['tp.contract'].sudo().search([]).mapped(lambda c: (c.id, c.aggregate_version)))
            return counts, versions

        before = snapshot()
        yield
        self.assertEqual(snapshot(), before)

    @contextmanager
    def _spy_run(self, *, forbid=False):
        Workflow = type(self.env['tp.contract.workflow'])
        original = Workflow._tp_run
        calls = []

        def spy(this, action, payload, **kwargs):
            calls.append((action, payload, kwargs))
            if forbid:
                message = '_tp_run must not be reached'
                raise AssertionError(message)
            return original(this, action, payload, **kwargs)

        with patch.object(Workflow, '_tp_run', spy):
            yield calls

    def _confirm_fails(self, wizard, exc, code=None):
        with self.assertRaises(exc) as caught, self.env.cr.savepoint():
            wizard.action_confirm()
        error = caught.exception
        if exc is UserError:
            self.assertNotIsInstance(error, AccessError)
        if code:
            cause = error.__cause__
            self.assertIsInstance(cause, ContractWorkflowError, f'{type(error).__name__} carries no workflow cause')
            self.assertEqual(cause.code, code, cause.message)
        self._assert_no_money(repr(error.args))
        return error

    def _menu_action(self, menu, user):
        action = menu.action
        if action._name == 'ir.actions.server':
            result = action.with_user(user).run()
        else:
            result = self.env['ir.actions.actions'].with_user(user)._for_xml_id(action.get_external_id()[action.id])
        context = result.get('context') or {}
        result['context'] = safe_eval(context) if isinstance(context, str) else context
        return result

    def _field_names(self, arch):
        return {node.get('name') for node in etree.fromstring(arch).iter('field')}

    # AT-01 menu and list

    def test_at01_menu_list_and_empty_state(self):
        menu = self._ref('tp_contract.menu_tp_contracts')
        self.assertEqual(menu.parent_id, self.env.ref('tp_core.menu_platform'))
        self.assertIn(self.env.ref('tp_core.group_user'), menu.group_ids)
        for user in (self.reader, self.outsider, self.editor):
            with self.subTest(user=user.login):
                self.assertIn(menu.id, self.env['ir.ui.menu'].with_user(user).load_menus(False))

        reader_action = self._menu_action(menu, self.reader)
        self.assertEqual(reader_action['res_model'], 'tp.contract')
        self.assertTrue(reader_action.get('help'), 'the list needs its empty-state text')
        self.assertFalse(reader_action['context'].get('tp_can_create_contract'))
        self.assertTrue(self._menu_action(menu, self.editor)['context'].get('tp_can_create_contract'))

        domain = reader_action.get('domain') or []
        Contract = self.env['tp.contract']
        visible = Contract.with_user(self.reader).search(domain)
        self.assertIn(self.contract_a, visible)
        self.assertNotIn(self.contract_b, visible)
        self.assertFalse(Contract.with_user(self.outsider).search(domain))

        views = Contract.with_user(self.reader).get_views([tuple(view) for view in reader_action['views']])
        list_arch = views['views']['list']['arch']
        names = self._field_names(list_arch)
        self.assertLessEqual({'code', 'name', 'project_id', 'tp_latest_review_state'}, names)
        self.assertFalse(names & RAW_MONEY_FIELDS)
        root = etree.fromstring(list_arch)
        for attribute in ('create', 'delete', 'edit'):
            self.assertIn(root.get(attribute), ('0', 'false', 'False'), attribute)

    # AT-02 money in lists, forms, groups and exports

    def test_at02_money_follows_grants_in_views_groups_and_exports(self):
        self._need_fields('tp.contract.revision', 'tp_amount_summary_text')
        for model in ('tp.contract', 'tp.contract.revision'):
            views = self.env[model].with_user(self.finance_a).get_views([(False, 'list'), (False, 'form')])
            for view_type, view in views['views'].items():
                with self.subTest(model=model, view=view_type):
                    self.assertFalse(self._field_names(view['arch']) & RAW_MONEY_FIELDS)

        admin = self.env.ref('base.user_admin')
        for user in (self.reader, self.finance_b, self.manager, admin):
            with self.subTest(user=user.login):
                revision = self.amendment.with_user(user)
                self.assertFalse(revision.tp_amount_summary_text)
                exported = revision.export_data(['tp_amount_summary_text'])['datas']
                self.assertFalse(exported[0][0])
        self.assertIn('110', self.amendment.with_user(self.finance_a).tp_amount_summary_text)
        self.assertIn('110', self.amendment.with_user(self.finance_a).export_data(['tp_amount_summary_text'])['datas'][0][0])

        groups = self.env['tp.contract'].with_user(self.reader).read_group([], ['project_id'], ['__count'])
        self.assertEqual([group[0] for group in groups], [self.project_a.id])

    # AT-03 create a contract draft

    def _create_vals(self, code, project=None, **extra):
        return {
            'project_id': (project or self.project_a).id, 'code': code, 'name': f'Native {code}', 'contract_type': 'owner',
            'currency_id': self.currency.id, 'revision_name': 'Original', 'revision_reference': f'SO-{code}',
            'line_ids': [Command.create({'scope_key': 'L1', 'name': 'Survey'}),
                         Command.create({'scope_key': 'L2', 'name': 'Design'})],
        } | extra

    def test_at03_create_contract_draft(self):
        Draft = self._native('draft')
        preview = Draft.with_user(self.editor).new({'mode': 'create'})
        self.assertFalse(preview.can_edit_money)
        preview.project_id = self.project_a
        self.assertTrue(preview.can_edit_money)
        wizard = Draft.with_user(self.editor).create(self._create_vals('HD-NAT-03'))
        self.assertEqual((wizard.mode, wizard.contract_id, wizard.project_id), ('create', self.env['tp.contract'], self.project_a))
        self.assertIn(self.project_a, wizard.allowed_project_ids)
        self._amount_input(wizard, 'L1', NEW_AMOUNT)
        result = wizard.action_confirm()
        contract = self.env['tp.contract'].search([('code', '=', 'HD-NAT-03')])
        revision = contract.revision_ids
        self.assertEqual((result['res_model'], result['res_id']), ('tp.contract.revision', revision.id))
        self.assertEqual((wizard.state, wizard.result_revision_id), ('done', revision))
        self.assertEqual(revision.line_ids.mapped('scope_key'), ['L1', 'L2'])
        self.assertEqual((revision.name, revision.reference, contract.department_id), ('Original', 'SO-HD-NAT-03', self.dept_kd))
        amounts = self.env['tp.contract.line.amount'].search([('revision_id', '=', revision.id)])
        self.assertEqual([(a.line_id.scope_key, a.amount_state, a.amount) for a in amounts], [('L1', 'confirmed', 1234567)])
        self.assertEqual(len(self._audits(contract, 'create_contract')), 1)
        self._assert_no_money(repr(result))

        meta = Draft.with_user(self.meta_editor).create(self._create_vals('HD-NAT-03M'))
        meta.action_confirm()
        self.assertTrue(self.env['tp.contract'].search([('code', '=', 'HD-NAT-03M')]))
        meta_money = Draft.with_user(self.meta_editor).create(self._create_vals('HD-NAT-03N'))
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self._amount_input(meta_money, 'L1')

        fin_meta = Draft.with_user(self.fin_meta).create(self._create_vals('HD-NAT-03F'))
        self._amount_input(fin_meta, 'L1')
        cases = (
            (fin_meta, AccessError, 'forbidden'),
            (Draft.with_user(self.other_dept).create(self._create_vals('HD-NAT-03D')), AccessError, 'forbidden'),
            (Draft.with_user(self.editor).create(self._create_vals('HD-NAT-03X', project=self.project_nodept)),
             UserError, 'scope_incomplete'),
            (Draft.with_user(self.editor).create(self._create_vals('HD-A')), UserError, 'duplicate_code'),
        )
        for wizard, exc, code in cases:
            with self.subTest(code=code, user=wizard.env.user.login), self._no_side_effects():
                self._confirm_fails(wizard, exc, code)
                self.assertEqual(wizard.state, 'draft')

    # AT-04 edit a draft

    def test_at04_edit_draft_version_header_and_state(self):
        # Odoo omits readonly defaults on create unless force_save is explicit:
        # retain the version seen when the form opened, even if saved much later.
        for key in HEADERS:
            arch = self._native(key).with_user(self.editor).get_views([(False, 'form')])['views']['form']['arch']
            tokens = etree.fromstring(arch).xpath('.//field[@name="expected_version"]')
            self.assertTrue(tokens and all(node.get('force_save') == '1' for node in tokens))
        contract, revision = self._draft_contract()
        wizard = self._edit(self.editor, contract, revision)
        self.assertEqual((wizard.mode, wizard.expected_version), ('edit', 1))
        self.assertEqual(wizard.line_ids.mapped('scope_key'), ['L1', 'L2'])
        self.assertEqual(wizard.revision_name, revision.name)
        wizard.revision_name = 'Original v2'
        result_action = wizard.with_context(default_expected_version=1).action_confirm()
        self.env.invalidate_all()
        self.assertEqual((contract.aggregate_version, revision.name), (2, 'Original v2'))
        self.assertEqual(len(self._audits(contract, 'edit_draft')), 1)
        self.assertEqual(result_action['context']['tp_native_version'], 2)
        self.assertFalse(any(key.startswith('default_') for key in result_action['context']))

        # Odoo caches unsaved defaults by model/context. Reopening an action after
        # a workflow transition must carry the version currently shown in the form.
        for xmlid, token in (('view_contract_form', 'aggregate_version'),
                             ('view_revision_form', 'tp_contract_version')):
            arch = etree.fromstring(self._ref('tp_contract.' + xmlid).arch_db)
            self.assertTrue(arch.xpath(f'.//field[@name="{token}"]'))
            for button in arch.xpath('.//header/button[@type="action"]'):
                context = safe_eval(button.get('context'), {
                    'id': revision.id, 'contract_id': contract.id, token: contract.aggregate_version,
                })
                self.assertEqual(context['default_expected_version'], 2)
        self.assertEqual(revision.with_user(self.editor).tp_contract_version, 2)
        reopened = self._native('draft').with_user(self.editor).with_context(
            default_contract_id=contract.id, default_revision_id=revision.id, default_expected_version=2,
        )
        defaults = reopened.default_get(['contract_id', 'revision_id', 'expected_version', 'revision_name'])
        self.assertEqual((defaults['expected_version'], defaults['revision_name']), (2, 'Original v2'))

        stale = self._edit(self.editor, contract, revision)
        self._run(self.editor, 'edit_draft', {'expected_version': 2, 'revision': {'name': 'Elsewhere'}},
                  contract=contract, revision=revision)
        stale.revision_name = 'Mine'
        with self._no_side_effects():
            error = self._confirm_fails(stale, RedirectWarning, 'stale_version')
        self.assertEqual(error.args[1]['res_model'], 'tp.contract.revision')

        version = self.contract_a.aggregate_version
        amendment = self._run(self.editor, 'create_amendment', {'expected_version': version, 'name': 'Native amendment'},
                              contract=self.contract_a)['revision'].sudo()
        locked = self._edit(self.editor, self.contract_a, amendment)
        self.assertFalse(locked.can_edit_header)
        locked.name = 'Header change'
        with self._no_side_effects():
            self._confirm_fails(locked, UserError, 'header_locked')

        contract2, revision2, _submission = self._submitted('HD-NAT-04B')
        self.assertFalse(revision2.with_user(self.editor).tp_can_edit_draft)
        self.assertTrue(revision.with_user(self.editor).tp_can_edit_draft)
        late = self._edit(self.editor, contract2, revision2)
        late.revision_name = 'Too late'
        with self._no_side_effects():
            self._confirm_fails(late, RedirectWarning, 'invalid_state')

    # AT-05 submit and resubmit

    def test_at05_submit_and_resubmit(self):
        self._need_fields('tp.contract.revision', 'tp_can_submit_review')
        contract, revision = self._draft_contract()
        self.assertTrue(revision.with_user(self.editor).tp_can_submit_review)
        self.assertFalse(revision.with_user(self.meta_editor).tp_can_submit_review)
        wizard = self._header('submit', self.editor, contract, revision)
        self.assertIn(self.reviewer, wizard.eligible_reviewer_ids)
        # The unsaved native form may not fetch project_id. Reviewer hints must still work.
        preview = self._native('submit').with_user(self.editor).new({
            'contract_id': contract.id, 'revision_id': revision.id,
        })
        self.assertIn(self.reviewer, preview.eligible_reviewer_ids._origin)
        self.assertNotIn(self.editor, wizard.eligible_reviewer_ids)
        self.assertFalse(wizard.is_resubmit)
        self.assertFalse(self._header('submit', self.meta_editor, contract, revision).eligible_reviewer_ids)
        wizard.reviewer_id = self.reviewer
        with self._no_side_effects():
            error = self._confirm_fails(wizard, UserError, 'submission_incomplete')
        self.assertIn('amounts_not_confirmed', error.__cause__.details['problems'])
        self.assertNotEqual(error.args[0], error.__cause__.message, 'the wizard shows its own message, not the API text')
        with self._no_side_effects():
            vi_error = self._confirm_fails(wizard.with_context(lang='vi_VN'), UserError, 'submission_incomplete')
        self.assertRegex(vi_error.args[0], VIETNAMESE, 'the user sees a Vietnamese message')

        fix = self._edit(self.editor, contract, revision)
        self._amount_input(fix, 'L2', '0')
        fix.action_confirm()
        submit = self._header('submit', self.editor, contract, revision, reviewer_id=self.reviewer.id)
        first = submit.action_confirm()
        again = submit.action_confirm()
        self.assertEqual((first['res_model'], first['res_id']), (again['res_model'], again['res_id']))
        self.assertEqual(len(revision.submission_ids), 1)
        self.assertEqual(len(self._audits(contract, 'submit_review')), 1)
        outbox = self.env['tp.contract.outbox'].sudo().search([('contract_id', '=', contract.id), ('event_type', '=', 'submit_review')])
        self.assertEqual(outbox.recipient_id, self.reviewer)

        self._run(self.reviewer, 'return_review', {
            'expected_version': contract.aggregate_version, 'reason': 'Clarify survey', 'issues': [],
        }, contract=contract, revision=revision)
        self._run(self.editor, 'begin_rework', {'expected_version': contract.aggregate_version, 'reason': 'Fixing'},
                  contract=contract, revision=revision)
        resubmit = self._header('submit', self.editor, contract, revision, reviewer_id=self.reviewer.id)
        self.assertTrue(resubmit.is_resubmit)
        self.assertEqual(resubmit.last_return_reason, 'Clarify survey')
        with self._no_side_effects():
            self._confirm_fails(resubmit, UserError, 'fix_summary_required')
        resubmit.fix_summary = 'Survey clarified'
        resubmit.action_confirm()
        self.assertEqual(len(self._audits(contract, 'resubmit_review')), 1)
        self.assertEqual(revision.review_state, 'in_review')

    # AT-06 return for rework

    def test_at06_return_review(self):
        self._need_fields('tp.contract.revision', 'tp_can_return_review')
        contract, revision, submission = self._submitted('HD-NAT-06')
        self.assertTrue(revision.with_user(self.reviewer).tp_can_return_review)
        for user in (self.editor, self.reviewer2, self.reader):
            with self.subTest(user=user.login):
                self.assertFalse(revision.with_user(user).tp_can_return_review)

        other = self._header('return', self.reviewer2, contract, revision, reason='Not mine')
        blank = self._header('return', self.reviewer, contract, revision)
        unknown = self._header('return', self.reviewer, contract, revision, reason='Check scope',
                               issue_ids=[Command.create({'scope_key': 'ZZ', 'note': 'Unknown line'})])
        for wizard, exc, code in ((other, AccessError, 'not_assigned_reviewer'), (blank, UserError, 'reason_required'),
                                  (unknown, UserError, 'unknown_scope_key')):
            with self.subTest(code=code), self._no_side_effects():
                self._confirm_fails(wizard, exc, code)

        good = self._header('return', self.reviewer, contract, revision, reason='Fix line L1',
                            issue_ids=[Command.create({'scope_key': 'L1', 'note': 'Clarify survey scope'})])
        self.assertIn('L1', good.available_scope_keys)
        good.action_confirm()
        self.assertEqual((revision.review_state, submission.outcome, submission.return_reason),
                         ('returned', 'returned', 'Fix line L1'))
        self.assertEqual(submission.return_issues[0]['scope_key'], 'L1')
        Outbox = self.env['tp.contract.outbox']
        domain = [('contract_id', '=', contract.id), ('event_type', '=', 'return_review')]
        self.assertEqual(Outbox.with_user(self.editor).search(domain).recipient_id, self.editor)
        self.assertFalse(Outbox.with_user(self.reviewer2).search(domain))

    # AT-07 begin rework

    def test_at07_begin_rework(self):
        self._need_fields('tp.contract.revision', 'tp_can_begin_rework')
        contract, revision, submission = self._submitted('HD-NAT-07')
        self._run(self.reviewer, 'return_review', {'expected_version': contract.aggregate_version, 'reason': 'Fix'},
                  contract=contract, revision=revision)
        self.assertTrue(revision.with_user(self.meta_editor).tp_can_begin_rework)
        blank = self._header('rework', self.editor, contract, revision)
        with self._no_side_effects():
            self._confirm_fails(blank, UserError, 'reason_required')
        wizard = self._header('rework', self.editor, contract, revision, reason='Start fixing')
        wizard.action_confirm()
        self.assertEqual(revision.review_state, 'draft')
        self.assertEqual((submission.rework_started_by_id, submission.rework_reason), (self.editor, 'Start fixing'))
        self.assertFalse(revision.with_user(self.editor).tp_can_begin_rework)
        again = self._header('rework', self.editor, contract, revision, reason='Again')
        with self._no_side_effects():
            self._confirm_fails(again, RedirectWarning, 'invalid_state')
        self.assertEqual(submission.rework_reason, 'Start fixing')

    # AT-08 documents

    def test_at08_documents_follow_confidentiality(self):
        self._need_fields('tp.contract', 'tp_document_count')
        Document = self.env['tp.contract.document']
        action = self.contract_a.with_user(self.reader).action_tp_open_documents()
        self.assertEqual(action['res_model'], 'tp.contract.document')
        self.assertEqual(Document.with_user(self.reader).search(action['domain']), self.general_doc)
        self.assertEqual(Document.with_user(self.finance_a).search(action['domain']), self.general_doc | self.financial_doc)
        self.assertEqual(self.contract_a.with_user(self.reader).tp_document_count, 1)
        self.assertEqual(self.contract_a.with_user(self.finance_a).tp_document_count, 2)
        self.assertNotIn('amendment.pdf', repr(Document.with_user(self.reader).search_read(action['domain'], ['file_name'])))
        views = Document.with_user(self.reader).get_views([(False, 'list')])
        self.assertIn(etree.fromstring(views['views']['list']['arch']).get('create'), ('0', 'false', 'False'))

        Binary = self.env['ir.binary']
        for user in (self.reader, self.manager):
            with self.subTest(user=user.login), self.assertRaises((AccessError, MissingError)):
                Binary.with_user(user)._find_record(res_model='tp.contract.document', res_id=self.financial_doc.id, field='file')
        self.assertEqual(
            Binary.with_user(self.reader)._find_record(res_model='tp.contract.document', res_id=self.general_doc.id, field='file'),
            self.general_doc,
        )
        with self.assertRaises((AccessError, MissingError)):
            Binary.with_user(self.outsider)._find_record(res_model='tp.contract.document', res_id=self.general_doc.id, field='file')

    # AT-09 direct RPC

    def test_at09_direct_rpc_stays_narrow(self):
        contract, revision = self._draft_contract()
        workflow = self.env['tp.contract.workflow'].with_user(self.editor)
        for name in ('_tp_run', '_tp_edit_draft', '_tp_capabilities'):
            with self.subTest(method=name), self.assertRaises(AccessError):
                call_kw(workflow, name, [[], 'edit_draft', {}], {})
        Draft = self._native('draft').with_user(self.editor)
        wizard = self._edit(self.editor, contract, revision)
        for name in ('_tp_amount_display_allowed', '_tp_payload', '_tp_check_target'):
            with self.subTest(method=name), self.assertRaises(AccessError):
                call_kw(Draft, name, [wizard.ids], {})

        with self.assertRaises(AccessError):
            revision.with_user(self.editor).write({'review_state': 'in_review'})
        for attempt in (lambda: revision.write({'review_state': 'in_review'}),
                        lambda: contract.write({'aggregate_version': 9})):
            with self.assertRaises(UserError), self.env.cr.savepoint():
                attempt()
        with self.assertRaises(AccessError):
            self._edit(self.editor, self.contract_b, self.revision_b)

        wizard.revision_name = 'Renamed'
        with self._no_side_effects():
            with self.assertRaises(TypeError), self.env.cr.savepoint():
                call_kw(Draft, 'action_confirm', [wizard.ids, {'expected_version': 1}], {})
            with self.assertRaises(TypeError), self.env.cr.savepoint():
                call_kw(Draft, 'action_confirm', [wizard.ids], {'payload': {'lines': []}})
        self.assertEqual(wizard.state, 'draft')

        meta = self._edit(self.meta_editor, contract, revision)
        meta.write({'line_ids': [Command.delete(meta.line_ids.filtered(lambda line: line.scope_key == 'L1').id)]})
        forged = {'context': {'tp_contract_workflow': True, 'active_test': False, 'tp_skip_capabilities': True}}
        with self._no_side_effects(), self.assertRaises(AccessError) as caught, self.env.cr.savepoint():
            call_kw(self._native('draft').with_user(self.meta_editor), 'action_confirm', [meta.ids], forged)
        self.assertEqual(caught.exception.__cause__.code, 'forbidden')

        with self.assertRaises(UserError):
            wizard.copy()

    # AT-10a..AT-10d revoked money in the wizard

    def _money_wizard(self, user):
        contract, revision = self._draft_contract()
        values = self._native('draft').with_user(user).web_save({
            'contract_id': contract.id, 'revision_id': revision.id, 'revision_name': 'Renamed by A',
            'amount_input_ids': [Command.create({
                'scope_key': 'L1', 'amount_state': 'confirmed', 'value': NEW_AMOUNT, 'tax_basis': 'excluding_tax',
            })],
        }, DRAFT_MONEY_SPEC)
        wizard = self._native('draft').with_user(user).browse(values[0]['id'])
        self.assertEqual(len(values[0]['amount_input_ids']), 1)
        texts = self._amount_texts(wizard)
        self.assertTrue(any(token in (texts['L1'] or '') for token in MONEY_TOKENS), 'precondition: A sees money')
        return contract, revision, wizard

    def _assert_amount_input_closed(self, user, wizard):
        amount = self._native('amount').sudo().search([('wizard_id', '=', wizard.id)])
        self.assertEqual(len(amount), 1, 'the stored input stays, only closed')
        Amount = self._native('amount').with_user(user)
        record = amount.with_user(user)
        with self.assertRaises(AccessError):
            record.read(['value'])
        self.assertFalse(Amount.search([('id', '=', amount.id)]))
        self.assertFalse(Amount.search_read([('wizard_id', '=', wizard.id)], ['value']))
        self.assertEqual(Amount.search_count([('id', '=', amount.id)]), 0)
        self.assertEqual(Amount.read_group([('id', '=', amount.id)], [], ['__count'])[0][0], 0)
        with self.assertRaises(AccessError):
            record.export_data(['value'])
        with self.assertRaises(AccessError):
            record.web_read({'value': {}})
        for attempt in (lambda: record.write({'value': '1'}), record.unlink, lambda: Amount.create({
            'wizard_id': wizard.id, 'scope_key': 'L2', 'amount_state': 'confirmed', 'value': '5', 'tax_basis': 'excluding_tax',
        })):
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                attempt()

    def _assert_metadata_without_money(self, user, wizard, contract, revision):
        header = wizard.with_user(user)
        data = header.web_read(DRAFT_SPEC)[0]
        self.assertEqual([line['scope_key'] for line in data['line_ids']], ['L1', 'L2'])
        self.assertFalse(any(line['current_amount_text'] for line in data['line_ids']))
        self._assert_no_money(repr(data))
        try:
            nested = header.web_read(DRAFT_MONEY_SPEC)[0]
        except AccessError:
            nested = None
        if nested is not None:
            self.assertEqual(nested['amount_input_ids'], [])
            self._assert_no_money(repr(nested))
        Draft = self._native('draft').with_user(user).with_context(
            default_contract_id=contract.id, default_revision_id=revision.id,
        )
        self._assert_no_money(repr(Draft.default_get(list(Draft._fields))))
        self._assert_no_money(repr(Draft.onchange({}, [], DRAFT_MONEY_SPEC)))

    def _assert_base_money(self, user, revision, *, readable):
        found = self.env['tp.contract.line.amount'].with_user(user).search([('revision_id', '=', revision.id)])
        self.assertEqual(bool(found), readable)

    def test_at10a_revoked_financial_read_closes_wizard_money(self):
        contract, revision, wizard = self._money_wizard(self.editor)
        self.grants['editor'].filtered(lambda grant: grant.capability == 'financial_read').active = False
        self._new_request()
        self._assert_amount_input_closed(self.editor, wizard)
        self._assert_metadata_without_money(self.editor, wizard, contract, revision)
        with self._no_side_effects():
            self._confirm_fails(wizard.with_user(self.editor), AccessError, 'forbidden')
        self._assert_base_money(self.editor, revision, readable=False)

    def test_at10b_expired_financial_read_closes_wizard_money(self):
        contract, revision, wizard = self._money_wizard(self.editor)
        grant = self.grants['editor'].filtered(lambda grant: grant.capability == 'financial_read')
        grant.date_end = '2026-01-01'
        self._new_request()
        self._assert_amount_input_closed(self.editor, wizard)
        self._assert_metadata_without_money(self.editor, wizard, contract, revision)
        with self._no_side_effects():
            self._confirm_fails(wizard.with_user(self.editor), AccessError, 'forbidden')
        self._assert_base_money(self.editor, revision, readable=False)

    def test_at10c_staff_without_assignment_loses_the_wizard(self):
        _contract, revision, wizard = self._money_wizard(self.editor)
        self._assignment(self.editor, self.project_a).active = False
        self._new_request()
        self.assertFalse(self.project_a.with_user(self.editor).has_access('read'))
        header = wizard.with_user(self.editor)
        with self.assertRaises(AccessError):
            header.read(['revision_name'])
        Line = self._native('line').with_user(self.editor)
        for line in self._native('line').sudo().search([('wizard_id', '=', wizard.id)]):
            with self.assertRaises(AccessError):
                line.with_user(self.editor).read(['name', 'current_amount_text'])
            self.assertEqual(Line.search_count([('id', '=', line.id)]), 0)
        self._assert_amount_input_closed(self.editor, wizard)
        with self._spy_run(forbid=True) as calls, self._no_side_effects():
            self._confirm_fails(header, AccessError)
        self.assertFalse(calls)
        self._assert_base_money(self.editor, revision, readable=False)

    def test_at10d_manager_without_assignment_keeps_metadata_only(self):
        contract, revision, wizard = self._money_wizard(self.mgr_actor)
        self._assignment(self.mgr_actor, self.project_a).active = False
        self._new_request()
        self.assertTrue(self.project_a.with_user(self.mgr_actor).has_access('read'))
        self._assert_metadata_without_money(self.mgr_actor, wizard, contract, revision)
        self._assert_amount_input_closed(self.mgr_actor, wizard)
        with self._no_side_effects():
            self._confirm_fails(wizard.with_user(self.mgr_actor), AccessError, 'forbidden')
        # G7 baseline, unchanged by this slice: the base ACL still shows base money to this manager.
        self._assert_base_money(self.mgr_actor, revision, readable=True)
        # Control: without the capability guard the wizard would show that money.
        with patch.object(type(self._native('draft')), '_tp_amount_display_allowed', lambda self: True):
            self._new_request()
            texts = self._amount_texts(wizard.with_user(self.mgr_actor))
            self.assertTrue(any(token in (texts['L1'] or '') for token in MONEY_TOKENS))

    # AT-10e no stored baseline; cleanup after success

    def test_at10e_no_money_baseline_and_cleanup(self):
        for key in ('draft', 'amendment', 'submit', 'return', 'rework', 'line', 'issue'):
            Model = self._native(key)
            for name, field in Model._fields.items():
                if not field.store or not field.column_type:
                    continue
                with self.subTest(model=Model._name, field=name):
                    self.assertNotIn(field.type, ('monetary', 'float', 'json', 'binary'))
                    self.assertFalse(re.search(r'amount|payload|value|total', name))
        current = self._native('line')._fields['current_amount_text']
        self.assertEqual((current.store, current.compute_sudo), (False, False))

        contract, revision = self._draft_contract()
        wizard = self._edit(self.editor, contract, revision)
        self._amount_input(wizard, 'L1', NEW_AMOUNT)
        first = wizard.action_confirm()
        self.assertEqual(self._native('amount').sudo().search_count([('wizard_id', '=', wizard.id)]), 0)
        self.assertEqual(wizard.state, 'done')
        with self._no_side_effects():
            again = wizard.action_confirm()
        self.assertEqual(again['res_id'], first['res_id'])
        self.assertEqual(len(self._audits(contract, 'edit_draft')), 1)
        claim = self.env['tp.contract.idempotency'].sudo().search([('key', '=', wizard.key)])
        self.assertEqual(len(claim), 1)
        self.assertRegex(claim.fingerprint, r'^[0-9a-f]{64}$')
        self._assert_no_money(repr(claim.read()))
        self._assert_no_money(repr(self._audits(contract).read()))

    # AT-10f relink

    def test_at10f_targets_cannot_be_relinked(self):
        contract, revision = self._draft_contract()
        other_contract, other_revision = self._draft_contract('HD-NAT-10F')
        wizard = self._edit(self.editor, contract, revision)
        amount = self._amount_input(wizard)
        other = self._edit(self.editor, other_contract, other_revision)
        for vals in ({'contract_id': other_contract.id}, {'revision_id': other_revision.id},
                     {'project_id': self.project_c.id}, {'company_id': self.company.id}, {'mode': 'create'},
                     {'key': 'native-forged-key-0001'}, {'expected_version': 99}, {'state': 'done'},
                     {'result_revision_id': revision.id}):
            with self.subTest(vals=vals), self.assertRaises(UserError), self.env.cr.savepoint():
                wizard.write(vals)
        for record in (wizard.line_ids[0], amount):
            with self.subTest(model=record._name), self.assertRaises(UserError), self.env.cr.savepoint():
                record.write({'wizard_id': other.id})
        no_grant = self._native('draft').with_user(self.editor).create(self._create_vals('HD-NAT-10C', project=self.project_c))
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self._amount_input(no_grant)

        plain = self._edit(self.editor, contract, revision, revision_name='Moved')
        self.env.flush_all()
        self.env.cr.execute('UPDATE tp_contract_native_draft SET project_id = %s WHERE id = %s', (self.project_c.id, plain.id))
        self.env.invalidate_all()
        with self._spy_run(forbid=True) as calls, self._no_side_effects():
            self._confirm_fails(plain, AccessError)
        self.assertFalse(calls)

    # AT-10g metadata flow without financial.read

    def test_at10g_metadata_flow_without_financial_read(self):
        contract, revision = self._draft_contract()
        Draft = self._native('draft').with_user(self.meta_editor).with_context(
            default_contract_id=contract.id, default_revision_id=revision.id,
        )
        self._assert_no_money(repr(Draft.default_get(list(Draft._fields))))
        self._assert_no_money(repr(Draft.onchange({}, [], DRAFT_SPEC)))
        wizard = Draft.create({'contract_id': contract.id, 'revision_id': revision.id})
        data = wizard.web_read(DRAFT_SPEC)[0]
        self.assertFalse(any(line['current_amount_text'] for line in data['line_ids']))
        self._assert_no_money(repr(data))
        self.assertFalse(wizard.can_edit_money)

        before = [(a.line_id.scope_key, a.amount_state, a.amount)
                  for a in self.env['tp.contract.line.amount'].search([('revision_id', '=', revision.id)])]
        wizard.revision_name = 'Renamed by metadata editor'
        wizard.line_ids.filtered(lambda line: line.scope_key == 'L2').name = 'Design (renamed)'
        with self._spy_run() as calls:
            wizard.action_confirm()
        action, payload, _kwargs = calls[0]
        self.assertEqual(action, 'edit_draft')
        self.assertNotIn('contract', payload)
        self.assertTrue(payload['lines'])
        self.assertFalse([line for line in payload['lines'] if 'amount' in line])
        self.env.invalidate_all()
        self.assertEqual(revision.name, 'Renamed by metadata editor')
        self.assertEqual(revision.line_ids.filtered(lambda line: line.scope_key == 'L2').name, 'Design (renamed)')
        after = [(a.line_id.scope_key, a.amount_state, a.amount)
                 for a in self.env['tp.contract.line.amount'].search([('revision_id', '=', revision.id)])]
        self.assertEqual(after, before)
        self.assertEqual(self._audits(contract, 'edit_draft').actor_id, self.meta_editor)

    # AT-11 out of scope

    def test_at11_out_of_scope_actions_are_absent(self):
        native = set(MODELS.values())
        navigation = {'action_tp_open_documents', 'action_tp_open_audit', 'action_tp_open_amounts'}
        for model in ('tp.contract', 'tp.contract.revision'):
            views = self.env[model].with_user(self.editor).get_views([(False, 'list'), (False, 'form')])
            for view_type, view in views['views'].items():
                for button in etree.fromstring(view['arch']).iter('button'):
                    with self.subTest(model=model, view=view_type, button=button.get('name')):
                        if button.get('type') == 'action':
                            action = self.env['ir.actions.actions'].browse(int(button.get('name')))
                            self.assertIn(self.env[action.type].browse(action.id).res_model, native)
                        else:
                            self.assertIn(button.get('name'), navigation)
        Base = type(self.env['base'])
        for key in HEADERS:
            cls = type(self._native(key))
            extra = {name for name in dir(cls) if name.startswith('action_') and not hasattr(Base, name)}
            self.assertEqual(extra, {'action_confirm'}, MODELS[key])
        with self.assertRaises(AccessError):
            self.contract_a.with_user(self.editor).write({'lifecycle_state': 'effective'})

    # AT-14 owner across ORM and RPC

    def _owned_records(self, owner):
        contract, revision = self._draft_contract('HD-NAT-OWN')
        ready, ready_revision, _submission = self._submitted('HD-NAT-OWN2')
        draft = self._edit(owner, contract, revision)
        returned = self._header('return', owner, ready, ready_revision, reason='Owner reason',
                                issue_ids=[Command.create({'scope_key': 'L1', 'note': 'Owner note'})])
        return {
            'draft': draft, 'line': draft.line_ids[:1], 'amount': self._amount_input(draft),
            'amendment': self._header('amendment', owner, self.contract_a, name='Owner amendment'),
            'submit': self._header('submit', owner, contract, revision),
            'return': returned, 'issue': returned.issue_ids,
            'rework': self._header('rework', owner, ready, ready_revision, reason='Owner rework'),
        }

    def _assert_foreign(self, user, key, record):
        Model = self._native(key).with_user(user)
        foreign = record.with_user(user)
        field, value = WRITABLE[key]
        with self.assertRaises(AccessError):
            foreign.read([field])
        self.assertFalse(Model.search([('id', '=', record.id)]))
        self.assertFalse(Model.search_read([('id', '=', record.id)], [field]))
        self.assertEqual(Model.search_count([('id', '=', record.id)]), 0)
        self.assertEqual(Model.read_group([('id', '=', record.id)], [], ['__count'])[0][0], 0)
        with self.assertRaises(AccessError):
            foreign.web_read({field: {}})
        with self.assertRaises(AccessError):
            foreign.export_data([field])
        for attempt in (lambda: foreign.write({field: value}), foreign.unlink, foreign.copy):
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                attempt()
        if key in HEADERS:
            with self._no_side_effects(), self.assertRaises(AccessError), self.env.cr.savepoint():
                call_kw(Model, 'action_confirm', [record.ids], {})

    def _assert_children_closed(self, user, records):
        for key, vals in (
            ('line', {'wizard_id': records['draft'].id, 'scope_key': 'L9', 'name': 'Injected'}),
            ('issue', {'wizard_id': records['return'].id, 'note': 'Injected'}),
            ('amount', {'wizard_id': records['draft'].id, 'scope_key': 'L2', 'amount_state': 'confirmed', 'value': '9',
                        'tax_basis': 'excluding_tax'}),
        ):
            with self.subTest(create=key), self.assertRaises(AccessError), self.env.cr.savepoint():
                self._native(key).with_user(user).create(vals)

    def test_at14_wizards_belong_to_their_owner(self):
        records = self._owned_records(self.editor)
        for key, record in records.items():
            with self.subTest(model=MODELS[key]):
                self._assert_foreign(self.editor2, key, record)
        self._assert_children_closed(self.editor2, records)
        self.assertTrue(records['draft'].read(['revision_name']))

    # AT-15 group combinations

    def test_at15_group_combinations_do_not_bypass_the_owner(self):
        self.assertTrue(self.power.has_group('base.group_system'))
        self.assertTrue(self.power.has_group('tp_core.group_manager'))
        for xmlid in self.hr_expense_groups:
            self.assertTrue(self.power.has_group(xmlid), xmlid)
        records = self._owned_records(self.editor)
        for key, record in records.items():
            with self.subTest(model=MODELS[key], step='groups'):
                self._assert_foreign(self.power, key, record)

        IrModel = self.env['ir.model']
        self.env['ir.access'].create([{
            'name': f'AT-15 broad permission {model}', 'model_id': IrModel._get_id(model),
            'group_id': self.env.ref('base.group_system').id, 'operation': 'crud',
        } for model in MODELS.values()])
        self._new_request()
        for key, record in records.items():
            with self.subTest(model=MODELS[key], step='broad permission'):
                self._assert_foreign(self.power, key, record)
        self._assert_children_closed(self.power, records)

        # Control: without the owner restrictions the broad permission would open A's wizards.
        owners = self.env['ir.access'].browse([self._ref(f'tp_contract.native_{ACL_SUFFIX[key]}_owner').id for key in MODELS])
        owners.unlink()
        self._new_request()
        self.assertTrue(records['draft'].with_user(self.power).read(['revision_name']))
        self.assertTrue(records['issue'].with_user(self.power).read(['note']))

    # AT-16 forged targets and payloads

    def test_at16_forged_targets_and_payloads(self):
        contract, revision = self._draft_contract()
        Draft = self._native('draft').with_user(self.editor)
        company2 = self.env['res.company'].create({'name': 'Synthetic other company AT-16'})
        project2 = self.env['project.project'].create({
            'name': 'Project CTR-OC', 'company_id': company2.id, 'tp_managed': True, 'tp_code': 'CTR-OC',
            'privacy_visibility': 'employees',
        })
        contract2 = self.env['tp.contract'].create({
            'code': 'HD-OC', 'name': 'Other company', 'project_id': project2.id, 'contract_type': 'owner',
            'currency_id': self.currency.id,
        })
        revision2 = self._revision(contract2, 0)
        forged = (
            ('draft', {'contract_id': contract.id, 'revision_id': self.original.id}),
            ('draft', {'contract_id': self.contract_b.id, 'revision_id': self.revision_b.id}),
            ('draft', {'contract_id': contract2.id, 'revision_id': revision2.id}),
            ('draft', self._create_vals('HD-NAT-16B', project=self.project_b)),
            ('submit', {'contract_id': contract.id, 'revision_id': self.revision_b.id}),
            ('amendment', {'contract_id': self.contract_b.id}),
            ('return', {'contract_id': contract2.id, 'revision_id': revision2.id}),
            ('rework', {'contract_id': self.contract_b.id, 'revision_id': self.revision_b.id}),
        )
        for key, vals in forged:
            with self.subTest(model=MODELS[key], vals=vals), self.assertRaises(AccessError), self.env.cr.savepoint():
                self._native(key).with_user(self.editor).create(vals)

        wizard = Draft.create({
            'contract_id': contract.id, 'revision_id': revision.id, 'project_id': self.project_c.id,
            'company_id': company2.id, 'key': 'client-chosen-key-0001', 'state': 'done', 'mode': 'create',
            'result_revision_id': self.original.id,
        })
        self.assertEqual((wizard.project_id, wizard.company_id, wizard.mode, wizard.state, wizard.result_revision_id),
                         (self.project_a, self.company, 'edit', 'draft', self.env['tp.contract.revision']))
        self.assertRegex(wizard.key, r'^native-[0-9a-f]{32}$')

        for scope_key, value in (('ZZ', '5'), ('L1', '1.5'), ('L1', 'abc')):
            probe = self._edit(self.editor, contract, revision)
            self._amount_input(probe, scope_key, value)
            with self.subTest(scope_key=scope_key, value=value), self._spy_run(forbid=True) as calls, \
                    self._no_side_effects():
                self._confirm_fails(probe, UserError)
            self.assertFalse(calls)
        twice = self._edit(self.editor, contract, revision)
        self._amount_input(twice, 'L1', '5')
        self._amount_input(twice, 'L1', '6')
        with self._spy_run(forbid=True) as calls, self._no_side_effects():
            self._confirm_fails(twice, UserError)
        self.assertFalse(calls)

        context = {
            'default_contract_id': contract.id, 'default_revision_id': revision.id, 'default_value': NEW_AMOUNT,
            'default_amount_state': 'confirmed',
            'default_amount_input_ids': [Command.create({
                'scope_key': 'L1', 'amount_state': 'confirmed', 'value': NEW_AMOUNT, 'tax_basis': 'excluding_tax',
            })],
        }
        self._assert_no_money(repr(Draft.with_context(context).default_get(list(Draft._fields))))
        seeded = Draft.with_context(context).create({'contract_id': contract.id, 'revision_id': revision.id})
        self.assertEqual(self._native('amount').sudo().search_count([('wizard_id', '=', seeded.id)]), 0)
        typed = self._native('amount').with_user(self.editor).with_context(context).create({
            'wizard_id': seeded.id, 'scope_key': 'L1',
        })
        self.assertFalse(typed.value)

    # AT-17 natural expiry at midnight (G8)

    def test_at17_natural_grant_expiry_applies_the_next_day(self):
        grant = self.grants['editor'].filtered(lambda grant: grant.capability == 'financial_read')
        with freeze_time('2026-11-06 12:00:00'):
            grant.date_end = '2026-11-06'
            contract, revision = self._draft_contract()
            wizard = self._edit(self.editor, contract, revision)
            amount = self._amount_input(wizard)
            self._new_request()
            # Same day: still valid, and every cache is warm.
            self.assertTrue(amount.with_user(self.editor).read(['value']))
            self._assert_base_money(self.editor, revision, readable=True)
            self.assertTrue(self._amount_texts(wizard.with_user(self.editor))['L1'])
        with freeze_time('2026-11-07 12:00:00'):
            self._new_request()
            self.assertEqual(str(self.env['tp.project.grant'].sudo().browse(grant.id).date_end), '2026-11-06')
            Amount = self._native('amount').with_user(self.editor)
            self.assertFalse(Amount.search([('wizard_id', '=', wizard.id)]))
            with self.assertRaises(AccessError):
                amount.with_user(self.editor).read(['value'])
            self._assert_base_money(self.editor, revision, readable=False)
            self.assertFalse(any(self._amount_texts(wizard.with_user(self.editor)).values()))

    # AT-18 owner without project access loses the child rows (D1)

    def test_at18_owner_without_project_access_loses_child_rows(self):
        owner = self.reviewer2
        contract, revision = self._draft_contract('HD-NAT-18')
        draft = self._edit(owner, contract, revision)
        line = draft.line_ids.filtered(lambda line: line.scope_key == 'L1')
        ready, ready_revision, _submission = self._submitted('HD-NAT-18B', reviewer=owner)
        returned = self._header('return', owner, ready, ready_revision, reason='Owner reason',
                                issue_ids=[Command.create({'scope_key': 'L1', 'note': 'Confidential issue note'})])
        issue = returned.issue_ids
        self._assignment(owner, self.project_a).active = False
        self._new_request()
        self.assertFalse(self.project_a.with_user(owner).has_access('read'))

        children = (
            ('line', line, draft, {'scope_key': 'L9', 'name': 'Injected'}, 'name'),
            ('issue', issue, returned, {'note': 'Injected'}, 'note'),
        )
        for key, record, header, create_vals, field in children:
            with self.subTest(model=MODELS[key]):
                Model = self._native(key).with_user(owner)
                child = record.with_user(owner)
                with self.assertRaises(AccessError):
                    child.read([field])
                self.assertFalse(Model.search([('id', '=', record.id)]))
                self.assertEqual(Model.search_count([('id', '=', record.id)]), 0)
                self.assertFalse(Model.search_read([('id', '=', record.id)], [field]))
                self.assertEqual(Model.read_group([('id', '=', record.id)], [], ['__count'])[0][0], 0)
                try:
                    exported = child.export_data([field])['datas']
                except AccessError:
                    exported = []
                self.assertFalse(exported)
                with self.assertRaises(AccessError):
                    child.web_read({field: {}})
                for attempt in (lambda: child.write({field: 'Changed'}), child.unlink,
                                lambda: Model.create(create_vals | {'wizard_id': header.id})):
                    with self.assertRaises(AccessError), self.env.cr.savepoint():
                        attempt()
        for header, spec in ((draft, {'line_ids': {'fields': {'name': {}}}}),
                             (returned, {'issue_ids': {'fields': {'note': {}}}})):
            with self.subTest(header=header._name):
                with self.assertRaises(AccessError):
                    header.with_user(owner).read(list(spec))
                with self.assertRaises(AccessError):
                    header.with_user(owner).web_read(spec)

        # Control: drop only the child scope restrictions; owner and company stay.
        scopes = self.env['ir.access'].browse([self._ref(f'tp_contract.native_{ACL_SUFFIX[key]}_scope').id
                                               for key in ('line', 'issue')])
        self.assertTrue(all(access.domain and 'wizard_id' in access.domain and 'access' in access.domain
                            for access in scopes))
        scopes.unlink()
        self._new_request()
        for key, record, _header, _vals, field in children:
            with self.subTest(control=MODELS[key]):
                self.assertTrue(record.with_user(owner).read([field]))
                self.assertEqual(self._native(key).with_user(owner).search_count([('id', '=', record.id)]), 1)
