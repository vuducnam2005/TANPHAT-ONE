from odoo.tests import tagged

from .common import DemoWorkspaceCommon


@tagged('post_install', '-at_install')
class TestDemoNavigation(DemoWorkspaceCommon):
    """Every native server leaf survives grouping; engineering never receives CRM/Bid."""

    def demo_leaves(self, actor):
        menus = self.env['ir.ui.menu'].with_user(actor).load_menus(False)
        root = self.env.ref('tp_demo_workspace.menu_demo_root').id
        result = {}

        def visit(menu_id):
            menu = menus[menu_id]
            if menu['action_id'] and not menu['children']:
                result[menu['xmlid']] = menu['action_id']
            for child in menu['children']:
                visit(child)

        visit(root)
        return result

    def test_all_existing_leaf_actions_survive_grouping(self):
        expected = {
            'dashboard': 'dashboard', 'projects': 'projects', 'project_overview': 'project_overview',
            'survey': 'survey', 'design': 'design', 'contracts': 'contracts', 'revisions': 'revisions',
            'contract_flow': 'contract_flow', 'tasks': 'tasks', 'employees': 'employees', 'staffing': 'staffing',
            'finance': 'finance', 'line_amounts': 'line_amounts', 'documents': 'documents', 'crm': 'crm',
            'bid': 'bid', 'request': 'request',
        }
        leaves = self.demo_leaves(self.lanhdao)
        self.assertEqual(set(leaves), {f'tp_demo_workspace.menu_demo_{key}' for key in expected})
        for key, action in expected.items():
            self.assertEqual(leaves[f'tp_demo_workspace.menu_demo_{key}'],
                             self.env.ref(f'tp_demo_workspace.action_demo_{action}').id)

    def test_engineer_menu_tree_keeps_contracts_and_finance_without_business(self):
        leader = self.demo_leaves(self.lanhdao)
        engineer = self.demo_leaves(self.kysu)
        denied = {'tp_demo_workspace.menu_demo_crm', 'tp_demo_workspace.menu_demo_bid'}
        self.assertEqual(set(engineer), set(leader) - denied)
        self.assertEqual(len(engineer), 15)
        for key in ('contracts', 'revisions', 'contract_flow', 'finance', 'line_amounts'):
            self.assertIn(f'tp_demo_workspace.menu_demo_{key}', engineer)
        visible = self.env['ir.ui.menu'].with_user(self.kysu).load_menus(False)
        self.assertNotIn(self.env.ref('tp_demo_workspace.menu_demo_business_root').id, visible)
