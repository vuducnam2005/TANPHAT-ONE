{
    'name': 'TANPHAT ONE – Trang chủ',
    'summary': 'Native app launcher home page built from the permission-filtered menu tree (UI-HOME-001)',
    'description': 'Native Odoo home page for TANPHAT ONE (UI-HOME-001). See README.md.',
    'author': 'Tan Phat JSC',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [
        'views/tp_web_home_menus.xml',
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
