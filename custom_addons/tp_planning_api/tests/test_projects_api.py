from odoo import Command
from odoo.tests.common import HttpCase, new_test_user


class TestProjectsApi(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reader = new_test_user(cls.env, login='tp_api_reader', groups='tp_core.group_user')
        cls.outsider = new_test_user(cls.env, login='tp_api_outsider', groups='base.group_user')
        cls.project = cls.env['project.project'].create({
            'name': 'API Assigned Project', 'tp_managed': True, 'tp_code': 'API-001',
            'company_id': cls.reader.company_id.id,
            'tp_assignment_ids': [Command.create({'user_id': cls.reader.id})],
        })
        cls.hidden = cls.env['project.project'].create({
            'name': 'API Hidden Project', 'tp_managed': True, 'tp_code': 'API-002',
            'company_id': cls.reader.company_id.id,
        })

    def test_unauthenticated_api_is_json_401(self):
        self.authenticate(None, None)
        response = self.url_open('/api/v1/me', allow_redirects=False)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error']['code'], 'unauthenticated')

    def test_project_scope_and_hidden_detail(self):
        self.authenticate(self.reader.login, self.reader.login)
        response = self.url_open('/api/v1/projects')
        self.assertEqual(response.status_code, 200)
        ids = [item['id'] for item in response.json()['data']]
        self.assertIn(self.project.id, ids)
        self.assertNotIn(self.hidden.id, ids)
        self.assertEqual(self.url_open(f'/api/v1/projects/{self.project.id}').status_code, 200)
        self.assertEqual(self.url_open(f'/api/v1/projects/{self.hidden.id}').status_code, 404)

    def test_ordinary_internal_user_has_no_planning_api(self):
        self.authenticate(self.outsider.login, self.outsider.login)
        self.assertEqual(self.url_open('/api/v1/projects').status_code, 403)

    def test_input_allowlist_and_bootstrap(self):
        self.authenticate(self.reader.login, self.reader.login)
        self.assertEqual(self.url_open('/api/v1/projects?limit=101').status_code, 400)
        self.assertEqual(self.url_open('/api/v1/projects?domain=all').status_code, 400)
        response = self.url_open('/api/v1/me')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['data']['csrf_token'])
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
