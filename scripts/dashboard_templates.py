"""Render connected templates by stable fixture bindings, shared by current apply tools."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render_connected(bindings):
    refs = {row['xmlid'].split('.')[-1]: row['id'] for row in bindings}
    replacements = {'__CID__': 1,
                    '__PROJECT_IDS__': [r['id'] for r in bindings if r['model'] == 'project.project'],
                    '__INVOICE_IDS__': [r['id'] for r in bindings if r['model'] == 'account.move'],
                    '__EXPENSE_IDS__': [r['id'] for r in bindings if r['model'] == 'hr.expense']}
    for key in ('cau', 'duong', 'nut', 'venbien'):
        replacements['__PID_' + key.upper() + '__'] = refs['project_' + key]
    result = {}
    for key, filename in (('dashboard_finance_draft', 'tp_invoice_expense_connected'),
                          ('dashboard_coordination', 'tp_project_coordination')):
        text = (ROOT / 'docs/demo/dashboards' / (filename + '.template.json')).read_text(encoding='utf-8')
        for token, value in replacements.items():
            text = text.replace('"' + token + '"', json.dumps(value)).replace(token, str(value))
        if re.search(r'__[A-Z_]+__', text):
            message = 'Unresolved connected dashboard tokens.'
            raise ValueError(message)
        result[key] = json.loads(text)
    return result
