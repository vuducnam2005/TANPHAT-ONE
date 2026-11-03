from types import SimpleNamespace

from odoo.tests import tagged

from .common import DemoWorkspaceCommon
from odoo.addons.tp_demo_workspace import demo_seed

COUNTED = {
    'project.project': [('tp_code', '=like', 'DEMO-%')],
    'project.task': [('project_id.tp_code', '=like', 'DEMO-%')],
    'tp.contract': [('code', '=like', 'DEMO-%')],
    'tp.contract.revision': [('contract_id.code', '=like', 'DEMO-%')],
    'tp.contract.submission': [('contract_id.code', '=like', 'DEMO-%')],
    'tp.contract.document': [('contract_id.code', '=like', 'DEMO-%')],
    'tp.contract.audit': [('contract_id.code', '=like', 'DEMO-%')],
    'tp.project.assignment': [('project_id.tp_code', '=like', 'DEMO-%')],
    'tp.project.grant': [('project_id.tp_code', '=like', 'DEMO-%')],
    'crm.lead': [('name', 'ilike', '(DEMO)')],
    'hr.employee': [('name', 'ilike', '(DEMO)')],
    'hr.department': [('name', 'ilike', '(DEMO)')],
    'res.users': [('name', 'ilike', '(DEMO)')],
    'res.partner': [('name', 'ilike', '(DEMO)'), ('is_company', '=', True)],
}


@tagged('post_install', '-at_install')
class TestDemoSeed(DemoWorkspaceCommon):

    def counts(self):
        self.env.invalidate_all()
        return {model: self.env[model].with_context(active_test=False).search_count(domain)
                for model, domain in COUNTED.items()}

    def test_volume_matches_the_spec(self):
        counts = self.counts()
        self.assertEqual(counts['project.project'], 3)
        self.assertEqual(counts['project.task'], 20)
        self.assertEqual(counts['tp.contract'], 4)
        self.assertEqual(counts['crm.lead'], 10)
        self.assertEqual(counts['hr.employee'], 12)

    def test_reseed_creates_no_duplicates(self):
        before = self.counts()
        demo_seed.seed(self.env, self.passwords)
        demo_seed.seed(self.env)
        self.assertEqual(self.counts(), before)

    def test_refuses_foreign_databases(self):
        for name in ('tp_tanphat_dev', 'tp_tanphat_test', 'tp_tanphat_restore', 'production'):
            env = SimpleNamespace(cr=SimpleNamespace(dbname=name), su=True)
            with self.subTest(db=name), self.assertRaisesRegex(RuntimeError, 'Refusing'):
                demo_seed.seed(env)

    def test_only_demo_actors_get_passwords(self):
        with self.assertRaises(ValueError):
            demo_seed.seed(self.env, {'nv.khoa.demo': 'secret-value-123'})

    def test_review_states_come_from_the_workflow(self):
        legacy, returned, in_review, draft = (self.contracts[key] for key in ('legacy', 'returned', 'in_review', 'draft'))
        latest = {key: contract.revision_ids.sorted('sequence')[-1] for key, contract in self.contracts.items()}
        self.assertEqual({key: revision.review_state for key, revision in latest.items()}, {
            'legacy': 'review_complete', 'returned': 'returned', 'in_review': 'in_review', 'draft': 'draft',
        })
        self.assertTrue(legacy.legacy_unverified)
        self.assertEqual(legacy.lifecycle_state, 'effective')
        self.assertEqual({c.lifecycle_state for c in returned | in_review | draft}, {'not_effective'})
        Audit = self.env['tp.contract.audit']
        self.assertEqual(Audit.search([('contract_id', '=', returned.id)], order='id').mapped('action'),
                         ['create_contract', 'submit_review', 'return_review'])
        self.assertEqual(Audit.search([('contract_id', '=', in_review.id)], order='id').mapped('action'),
                         ['create_contract', 'submit_review'])
        self.assertFalse(Audit.search([('contract_id', '=', legacy.id)]))
        submission = latest['returned'].submission_ids
        self.assertEqual(submission.outcome, 'returned')
        self.assertEqual((submission.submitted_by_id, submission.returned_by_id), (self.drafter, self.reviewer))
        self.assertIn('đơn giá khoan', submission.return_reason)
        # Notifications stay in the TP outbox; nothing is queued for e-mail.
        self.assertTrue(self.env['tp.contract.outbox'].search([('contract_id', '=', returned.id)]))
        self.assertFalse(self.env['mail.mail'].search([('body_html', 'ilike', 'DEMO-HD-')]))

    def test_actor_scope_and_grants(self):
        Project = self.env['project.project']
        self.assertEqual(sorted(Project.with_user(self.lanhdao).search([('tp_code', '=like', 'DEMO-%')]).mapped('tp_code')),
                         ['DEMO-CAU-01', 'DEMO-DUONG-02', 'DEMO-NUT-03'])
        self.assertEqual(Project.with_user(self.kysu).search([('tp_code', '=like', 'DEMO-%')]).mapped('tp_code'),
                         ['DEMO-DUONG-02'])
        grants = self.env['tp.project.grant'].search([('user_id', 'in', (self.lanhdao | self.kysu).ids)])
        self.assertEqual(set(grants.mapped('capability')), {'financial_read'})
        self.assertEqual(grants.user_id, self.lanhdao)
        for actor in (self.lanhdao, self.kysu):
            self.assertFalse(actor.has_group('base.group_system'))
            self.assertFalse(actor.has_group('tp_core.group_manager'))
            self.assertFalse(actor.has_group('project.group_project_manager'))
        self.assertFalse(self.kysu.has_group('tp_demo_workspace.group_demo_business'))
