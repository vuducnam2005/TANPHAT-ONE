{
    'name': 'TANPHAT ONE – Demo Workspace',
    'summary': 'Leadership demo of TANPHAT ONE on an isolated database with synthetic data (UI-DEMO-001)',
    'description': 'Native Odoo leadership demo of TANPHAT ONE (UI-DEMO-001). See README.md.',
    'author': 'Tan Phat JSC',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['tp_project', 'tp_contract', 'project', 'hr', 'crm', 'web'],
    'data': [
        'security/tp_demo_workspace_security.xml',
        'security/ir.access.csv',
        'views/tp_demo_actions.xml',
        'views/project_views.xml',
        'views/task_views.xml',
        'views/contract_views.xml',
        'views/document_views.xml',
        'views/crm_views.xml',
        'views/hr_views.xml',
        'views/tp_demo_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tp_demo_workspace/static/src/**/*',
        ],
        'web.assets_unit_tests': [
            'tp_demo_workspace/static/tests/navigation/**/*.test.js',
        ],
    },
    'installable': True,
    'application': True,
}
