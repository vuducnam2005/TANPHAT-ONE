{
    'name': 'TP Dashboard Internal Access',
    'author': 'Tan Phat JSC',
    'version': '20.0.1.1.0',
    'license': 'LGPL-3',
    'depends': ['spreadsheet_dashboard', 'tp_project', 'hr_timesheet', 'hr_expense'],
    'data': ['views/dashboard_search_views.xml'],
    'assets': {
        'spreadsheet.o_spreadsheet': [
            'tp_dashboard_privacy/static/src/dashboard.js',
            'tp_dashboard_privacy/static/src/dashboard.xml',
        ],
        'web.assets_backend': ['tp_dashboard_privacy/static/src/dashboard.scss'],
    },
}
