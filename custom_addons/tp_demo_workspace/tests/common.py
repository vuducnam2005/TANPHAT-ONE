from odoo.tests import TransactionCase

from odoo.addons.tp_demo_workspace import demo_seed

# Formatted or raw pieces of every synthetic amount the restricted actor must never receive.
MONEY_TOKENS = (
    '640,000', '640.000', '640000000', '1,380', '1.380', '1380000000', '2,020', '2.020', '2020000000',
    '420,000', '420.000', '420000000', '85,000', '85.000', '85000000', '310,000', '310.000', '310000000',
    '18,500', '18.500', '18500000', '1,250', '1.250', '1,850', '1.850', '3,100', '3.100',
)


class DemoWorkspaceCommon(TransactionCase):
    """The UI-DEMO-001 dataset, seeded through the same entry point as scripts/ui_demo.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.passwords = {login: f'{login}-ui001-test' for login in demo_seed.ACTOR_LOGINS}
        cls.data = demo_seed.seed(cls.env, cls.passwords)
        cls.projects = cls.data['projects']
        cls.contracts = cls.data['contracts']
        cls.lanhdao = cls.data['actors']['lanhdao']
        cls.kysu = cls.data['actors']['kysu']
        cls.drafter = cls.data['actors']['drafter']
        cls.reviewer = cls.data['actors']['reviewer']

    def projection(self, user):
        return self.env['tp.demo.workspace'].with_user(user)
