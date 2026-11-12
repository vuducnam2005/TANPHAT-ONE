"""DASH-UI-001: owned snapshot/clone and drift-safe native dashboard operations."""
# ruff: noqa: T201
import argparse
import json
import subprocess
import sys
from pathlib import Path

import native_data003 as native
from dashboard_templates import render_connected

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/dash-ui001'


def inspect(env, target):
    bindings = native.inventory(env)['bindings']
    result = {'target': target, 'bindings': bindings}
    result['dashboards'] = []
    for key in ('dashboard_coordination', 'dashboard_finance_draft'):
        record = env.ref(native.OLD_NS[3] + '.' + key)
        result['dashboards'].append({
            'xmlid': native.OLD_NS[3] + '.' + key, 'id': record.id,
            'name': record.name, 'data': json.loads(record.spreadsheet_data),
            'users': record.allowed_user_ids.ids, 'groups': record.group_ids.ids,
            'companies': record.company_ids.ids, 'internal': record.tp_internal_only,
        })
    invoices = env['account.move'].browse([r['id'] for r in bindings if r['model'] == 'account.move'])
    result['invoices'] = invoices.read(['name', 'state', 'move_type', 'company_id', 'currency_id',
                                      'invoice_date', 'date', 'amount_untaxed', 'amount_total', 'write_date'])
    result['lines'] = invoices.invoice_line_ids.read(['move_id', 'display_type', 'price_subtotal',
                                                    'price_total', 'analytic_distribution', 'currency_id'])
    expenses = env['hr.expense'].browse([r['id'] for r in bindings if r['model'] == 'hr.expense'])
    result['expenses'] = expenses.read(['name', 'state', 'date', 'company_id', 'currency_id',
                                       'total_amount', 'total_amount_currency', 'analytic_distribution',
                                       'write_date', 'employee_id'])
    result['expense_tracking'] = []
    for message in env['mail.message'].search([('model', '=', 'hr.expense'), ('res_id', 'in', expenses.ids)], order='date,id'):
        result['expense_tracking'].append({'id': message.id, 'expense_id': message.res_id,
                                           'date': message.date, 'author': message.author_id.name,
                                           'type': message.message_type, 'body': str(message.body)})
    path = BASE / f'inspect-{target}.json'
    if not path.exists():
        native.write(path, result)
    else:
        native.write(BASE / f'inspect-{target}-current.json', result)
    env.cr.rollback()
    totals = {}
    for row in result['expenses']:
        totals[row['state']] = totals.get(row['state'], 0) + row['total_amount']
    print(json.dumps({'target': target, 'expense_states': totals,
                      'expense_total': sum(totals.values()),
                      'invoices': result['invoices'],
                      'dashboards': [{k: r[k] for k in ('id', 'name', 'users', 'internal')}
                                     for r in result['dashboards']]}, ensure_ascii=False, default=str))


def apply(env, target, mode):
    baseline = native.read(BASE / f'inspect-{target}.json')
    templates = render_connected(baseline['bindings'])
    changed = []
    for old in baseline['dashboards']:
        record = env.ref(old['xmlid'])
        native.require(record.id == old['id'], 'Dashboard identity drift.')
        native.require(record.allowed_user_ids.ids == old['users'] and record.group_ids.ids == old['groups']
                       and record.company_ids.ids == old['companies'] and record.tp_internal_only == old['internal'],
                       'Dashboard access drift; preserve and reconcile.')
        data = templates[old['xmlid'].split('.')[-1]]
        current = json.loads(record.spreadsheet_data)
        title = 'Tổng quan hóa đơn và chi phí' if data['settings']['tpDashboard']['kind'] == 'finance' else old['name']
        native.require(current in (old['data'], data), 'User spreadsheet drift; refusing overwrite.')
        native.require(record.name in (old['name'], title), 'User dashboard name drift.')
        if current != data or record.name != title:
            native.require(mode != 'verify', 'Dashboard update not applied.')
            changed.append(record.id)
            record.with_user(env.ref('base.user_admin')).write({'spreadsheet_data': json.dumps(data, ensure_ascii=False), 'name': title})
    if mode == 'apply':
        env.cr.commit()
    else:
        env.cr.rollback()
    result = {'target': target, 'mode': mode, 'updated': changed, 'created': 0}
    native.write(BASE / f'apply-{target}-{mode}.json', result)
    print(json.dumps(result))


def upgrade_dev():
    native.target_config('dev')
    log = (BASE / 'odoo-tests-release.log').read_text(encoding='utf-8')
    native.require('0 failed, 0 error(s) of 17 tests' in log, 'Passing clone Odoo tests required.')
    native.require(native.read(BASE / 'ui-clone/results.json')['passed'], 'Passing clone UI required.')
    native.require(native.read(BASE / 'zoom-clone-results.json')['passed'], 'Passing browser zoom required.')
    native.require(native.read(BASE / 'refresh-results.json')['passed'], 'Passing source refresh/restore required.')
    native.require(native.read(BASE / 'security-revocation.json')['passed'], 'Passing clone revoke/restore required.')
    running = native.dev.is_listening(18069)
    native.require(running, 'Expected existing dev Odoo.')
    try:
        native.dev.stop_server()  # Deliberately do not use dev.py stop (it also stops PostgreSQL).
        native.require(native.dev.is_listening(55432), 'PostgreSQL must remain running.')
        with (BASE / 'dev-upgrade-console.log').open('ab') as output:
            subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'odoo-bin'),
                            '-c', str(ROOT / '.local/odoo.conf'), '-d', 'tp_tanphat_dev',
                            '-u', 'tp_dashboard_privacy', '--stop-after-init', '--no-http',
                            '--logfile', str(BASE / 'dev-upgrade-success.log')], cwd=ROOT,
                           stdout=output, stderr=subprocess.STDOUT, check=True)
    finally:
        if running and not native.dev.is_listening(18069):
            native.dev.start_server()
    print('UPGRADE PASS: tp_dashboard_privacy only; dev18069 restarted, PostgreSQL kept running; no seed.')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    native.BASE = BASE
    native.DATABASE = 'tp_tanphat_dashui001_20261104'
    native.PORT = 18159
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['snapshot', 'clone', 'start', 'stop', 'inspect', 'apply', 'upgrade-dev'])
    parser.add_argument('--target', choices=['clone', 'dev'], default='clone')
    parser.add_argument('--mode', choices=['dry-run', 'apply', 'verify'], default='verify')
    args = parser.parse_args()
    if args.command == 'upgrade-dev':
        upgrade_dev()
    elif args.command in ('snapshot', 'clone'):
        getattr(native, args.command)()
    elif args.command in ('start', 'stop'):
        native.runtime(args.command)
    elif args.command == 'inspect':
        native.orm(args.target, lambda env: inspect(env, args.target))
    else:
        native.orm(args.target, lambda env: apply(env, args.target, args.mode))


if __name__ == '__main__':
    main()
