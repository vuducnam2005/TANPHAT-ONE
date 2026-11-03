{
    'name': 'TANPHAT ONE Login',
    'author': 'Tan Phat JSC',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['web', 'auth_totp', 'auth_signup'],
    'assets': {
        'tp_web_login.assets_login': [
            'tp_web_login/static/src/css/login.css',
        ],
    },
    'data': [
        'data/ir_config_parameter_data.xml',
        'views/login_templates.xml',
    ],
}
