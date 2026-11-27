{
    'name': 'TANPHAT ONE – Trang chủ',
    'summary': 'Native Home: executive & workspace dashboard with real-time KPIs, shortcuts, agenda and task analytics',
    'description': 'Native Odoo home page & unified app switcher for TANPHAT ONE (UI-HOME-006..010, UI-APPS-001). See README.md.',
    'author': 'Tan Phat JSC',
    'version': '20.0.3.0.4',
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
