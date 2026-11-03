{
    'name': 'TANPHAT ONE – Việt hóa giao diện',
    'summary': 'Vietnamese glossary overlay for native Odoo app names, menus and state labels (VI-001)',
    'description': 'Translation-only addon: i18n/vi.po overrides native vi_VN terms that differ from the '
                   'TANPHAT ONE glossary. No model, view, data, access rule or asset. See README.md.',
    'author': 'Tan Phat JSC',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',
    # every module whose terms the catalog overrides: loaded after them in topological order
    'depends': [
        'account', 'calendar', 'contacts', 'hr', 'hr_calendar', 'hr_expense', 'hr_skills', 'hr_timesheet',
        'iap', 'mail', 'project', 'project_todo', 'spreadsheet_dashboard',
    ],
    'data': [],
    'installable': True,
    'application': False,
}
