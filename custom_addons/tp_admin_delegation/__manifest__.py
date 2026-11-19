{
    'name': 'TANPHAT ONE — Quản trị viên toàn hệ thống',
    'version': '20.0.2.0.2',
    'license': 'LGPL-3',
    'author': 'Tan Phat JSC',
    'depends': ['tp_hr_workspace', 'tp_equipment', 'tp_reporting'],
    'data': [
        'security/admin_full_security.xml',
        'security/ir.access.csv',
        'security/ir.access-equipment.csv',
        'data/reporting_admin.xml',
        'data/full_admin_access.xml',
        'views/admin_delegation_views.xml',
        'views/native_navigation.xml',
        'views/hr_profile.xml',
        'views/reporting_navigation.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tp_admin_delegation/static/src/my_profile.xml',
            'tp_admin_delegation/static/src/hr_overview_patch.js',
        ],
    },
    'post_init_hook': '_post_init_admin_full',
    'installable': True,
}
