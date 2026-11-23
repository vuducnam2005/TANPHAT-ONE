{
    'name': 'TANPHAT ONE – Trang chủ',
    'summary': 'Native Home: admin 7-item layout and user workspace (UI-HOME-004)',
    'description': 'Native Odoo home page for TANPHAT ONE (UI-HOME-004). See README.md.',
    'author': 'Tan Phat JSC',
    'version': '20.0.1.12.0',
    'license': 'LGPL-3',
    'depends': ['web', 'tp_web_login'],
    'data': [
        'views/tp_web_home_menus.xml',
        'views/tp_web_home_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tp_web_home/static/src/**/*',
        ],
        # UI-INPUT-001: the login pages read the same input tokens as the backend.
        'tp_web_login.assets_login': [
            'tp_web_home/static/src/inputs/input_tokens.css',
        ],
        'web.assets_unit_tests': [
            'tp_web_home/static/tests/**/*.test.js',
            'tp_web_home/static/tests/**/*.xml',
        ],
    },
    'installable': True,
    'application': False,
}
