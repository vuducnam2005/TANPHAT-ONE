{
    'name': 'TANPHAT ONE — Quản trị được ủy quyền',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'Tan Phat JSC',
    'depends': ['tp_hr_workspace', 'tp_equipment', 'tp_reporting'],
    'data': [
        'security/ir.access.csv',
        'security/ir.access-equipment.csv',
        'views/admin_delegation_views.xml',
        'views/native_navigation.xml',
        'views/hr_profile.xml',
    ],
    'assets': {
        'web.assets_backend': ['tp_admin_delegation/static/src/my_profile.xml'],
    },
    'installable': True,
}
