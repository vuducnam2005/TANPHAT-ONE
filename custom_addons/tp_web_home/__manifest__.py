{
    'name': 'TANPHAT ONE – Trang chủ',
    'summary': 'Native Home: admin 7-item layout and user workspace (UI-HOME-004)',
    'description': 'Native Odoo home page for TANPHAT ONE (UI-HOME-004). See README.md.',
    'author': 'Tan Phat JSC',
    'version': '20.0.1.5.0',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [
        'views/tp_web_home_menus.xml',
        'views/tp_web_home_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tp_web_home/static/src/**/*',
        ],
        'web.assets_unit_tests': [
            'tp_web_home/static/tests/**/*.test.js',
        ],
    },
    'installable': True,
    'application': False,
}
