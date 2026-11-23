{
    'name': 'TANPHAT ONE – Trung tâm Báo cáo',
    'summary': 'Mục tiêu quý, kế hoạch tháng/tuần và báo cáo có phiên bản theo quyền',
    'version': '20.0.1.2.0',
    'author': 'Tan Phat JSC',
    'license': 'LGPL-3',
    'depends': ['hr', 'project', 'tp_web_home', 'tp_organization', 'tp_hr_workspace'],
    'external_dependencies': {'python': ['xlsxwriter', 'reportlab']},
    'data': [
        'security/reporting_security.xml',
        'security/ir.access.csv',
        'data/reporting_data.xml',
        'data/catalog_data.xml',
        'views/reporting_views.xml',
        'views/completion_views.xml',
        'views/reporting_menus.xml',
    ],
    'assets': {
        'web.assets_backend': ['tp_reporting/static/src/**/*'],
        'web.assets_unit_tests': ['tp_reporting/static/tests/**/*.test.js'],
    },
    'installable': True,
    'application': True,
}
