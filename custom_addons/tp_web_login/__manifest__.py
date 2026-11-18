{
    'name': 'TANPHAT ONE Login',
    'author': 'Tan Phat JSC',
    'version': '20.0.2.0.1',
    'license': 'LGPL-3',
    'depends': ['web', 'auth_totp', 'auth_signup', 'bus'],
    'assets': {
        'web.assets_backend': [
            'tp_web_login/static/src/css/identitycheck.scss',
            'tp_web_login/static/src/js/identitycheck.js',
            'tp_web_login/static/src/css/session_guard.scss',
            'tp_web_login/static/src/xml/session_guard.xml',
            'tp_web_login/static/src/js/session_guard.js',
        ],
        'tp_web_login.assets_login': [
            'tp_web_login/static/src/css/login.css',
        ],
        'web.assets_frontend': [
            'tp_web_login/static/src/js/auth_ui.js',
            'tp_web_login/static/src/xml/user_switch.xml',
        ],
    },
    'data': [
        'views/login_templates.xml',
        'views/identitycheck.xml',
    ],
}
