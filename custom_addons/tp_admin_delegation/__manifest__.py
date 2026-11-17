{
    'name': 'TANPHAT ONE — Quản trị được ủy quyền',
    'version': '20.0.1.2.0',
    'license': 'LGPL-3',
    'author': 'Tan Phat JSC',
    'depends': ['tp_hr_workspace', 'tp_equipment', 'tp_reporting'],
    'data': [
        'security/ir.access.csv',
        'security/ir.access-equipment.csv',
        'data/reporting_admin.xml',
        'views/admin_delegation_views.xml',
        'views/native_navigation.xml',
        'views/hr_profile.xml',
        'views/reporting_navigation.xml',
    ],
    'assets': {
        'web.assets_backend': ['tp_admin_delegation/static/src/my_profile.xml'],
    },
    'installable': True,
}
