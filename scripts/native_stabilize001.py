"""NATIVE-STABILIZE-001: owned isolated clone and read-only audit of the native Odoo foundation.

The snapshot never stops dev 18069: it exports one REPEATABLE READ snapshot, fingerprints every
public rowset inside that same transaction and lets pg_dump import it. All write/failure probes
run on the owned clone in transactions that are rolled back. Credentials and evidence stay in
the git-ignored, ACL-restricted operation folder.
"""
# Operator output and deferred Odoo imports are intentional.
# ruff: noqa: T201, PLC0415, EM101
import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import native_data003 as native
import psycopg2.extensions

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/native-stabilize001'
DATABASE = 'tp_tanphat_stab001_20261105'
PORT = 18169
DEV_DB = 'tp_tanphat_dev'
DEV_FILESTORE = ROOT / '.local/odoo/filestore' / DEV_DB
DASHBOARDS = {'coordination': 'tp_native_data002_20261102.dashboard_coordination',
              'finance': 'tp_native_data002_20261102.dashboard_finance_draft'}
ACTORS = ('admin', 'long', 'son', 'huong', 'khoa', 'lan', 'nam', 'khang', 'bao')
require = native.require


def bind():
    native.BASE = BASE
    native.DATABASE = DATABASE
    native.PORT = PORT


def dev_pid():
    path = ROOT / '.local/odoo.pid'
    return path.read_text(encoding='utf-8').strip() if path.exists() else None


def snapshot():
    """Consistent dump of the running dev database without stopping or restarting it."""
    native.private_root()
    identity = native.preflight()
    require(not (BASE / 'owner.json').exists(), 'An owned operation already exists; reuse it.')
    require(not native.dev.is_listening(PORT), 'Clone port already in use by another process.')
    require(native.dev.is_listening(18069), 'Expected the existing dev runtime.')
    with closing(native.connect('postgres', admin=True)) as connection, connection.cursor() as cursor:
        cursor.execute('SELECT 1 FROM pg_database WHERE datname=%s', (DATABASE,))
        require(not cursor.fetchone(), 'Clone database name already exists; refusing to reuse a database not created here.')
    pid_before = dev_pid()
    folder = BASE / ('snapshot-' + datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ'))
    folder.mkdir()
    (folder / 'private').mkdir()
    for name in ('odoo.conf', 'runtime-owner.json'):
        shutil.copy2(ROOT / '.local' / name, folder / 'private' / name)
    with zipfile.ZipFile(folder / 'maintained-source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in ('custom_addons', 'scripts', 'docs', 'ops', 'contracts'):
            for path in (ROOT / name).rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                    archive.write(path, path.relative_to(ROOT))
        archive.write(ROOT / 'AGENTS.md', 'AGENTS.md')
    secrets = native.read(ROOT / '.local/dev-secrets.json')
    pg_env = native.backup.pg_environment(secrets['pg_app'])
    with closing(native.connect(DEV_DB)) as connection:
        connection.set_session(isolation_level=psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ, readonly=True)
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_export_snapshot()')
            exported = cursor.fetchone()[0]
        native.backup.run([native.dev.pg_bin() / 'pg_dump.exe', '-h', '127.0.0.1', '-p', '55432', '-U', 'tp_odoo',
                           '-d', DEV_DB, '-Fc', '--no-owner', '--no-privileges', '--snapshot', exported,
                           '-f', folder / 'database.dump'], env=pg_env)
        tables = native.backup.table_inventory(connection)
        attachments = native.backup.attachment_inventory(connection, DEV_FILESTORE)
        connection.rollback()
    for item in attachments:
        destination = folder / 'filestore' / item['store_fname']
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():  # Deduplicated content: several attachments share one read-only blob.
            shutil.copy2(DEV_FILESTORE / item['store_fname'], destination)
        require(native.backup.digest(destination, 'sha1') == item['sha1'], 'Copied blob differs from its checksum.')
    require(native.dev.is_listening(18069) and dev_pid() == pid_before, 'Dev runtime changed during snapshot.')
    native.write(folder / 'baseline.json', {'tables': tables, 'attachments': attachments, 'source_uuid': identity,
                                           'pg_snapshot': exported, 'dev_pid': pid_before, 'dev_stopped': False})
    hashes = {p.relative_to(folder).as_posix(): native.backup.digest(p) for p in folder.rglob('*') if p.is_file()}
    native.write(folder / 'manifest.json', hashes)
    native.write(BASE / 'owner.json', {'workspace': str(ROOT), 'database': DATABASE, 'http_port': PORT,
                                      'source_uuid': identity, 'token': native.secrets.token_hex(32),
                                      'snapshot': str(folder), 'rehearsal_passed': False})
    print('SNAPSHOT PASS:', folder.name, len(tables), 'tables,', len(attachments), 'blobs,', len(hashes),
          'checksums; dev 18069 kept running (PID unchanged).')


def dev_drift():
    """Read-only comparison of current dev rowsets with the snapshot baseline."""
    owner = native.read(BASE / 'owner.json')
    baseline = native.read(Path(owner['snapshot']) / 'baseline.json')
    with closing(native.connect(DEV_DB)) as connection:
        connection.set_session(isolation_level=psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ, readonly=True)
        current = native.backup.table_inventory(connection)
        connection.rollback()
    changed = sorted(name for name in set(current) | set(baseline['tables'])
                     if current.get(name) != baseline['tables'].get(name))
    result = {'checked_at': datetime.now(UTC).isoformat(), 'tables': len(current), 'changed': changed,
              'row_deltas': {name: (baseline['tables'].get(name, {}).get('rows'), current.get(name, {}).get('rows'))
                             for name in changed}}
    native.write(BASE / 'dev-drift.json', result)
    print(json.dumps(result, ensure_ascii=False))


# --------------------------------------------------------------------------------------------
# Read-only ORM audit (clone). Every probe runs in the callback transaction, rolled back at the end.
# --------------------------------------------------------------------------------------------

def actor_users(env):
    users = {'admin': env.ref('base.user_admin')}
    for key in ACTORS[1:]:
        namespace = native.NEW_NS if key == 'bao' else native.OLD_NS[0]
        users[key] = env.ref(f'{namespace}.user_{key}')
    return users


def home_audit(env, users):
    """Every menu a user receives must open a destination the same user can read (no tile that only errors)."""
    result = {}
    for key, user in users.items():
        menus = env['ir.ui.menu'].with_user(user).load_web_menus(False)
        checked, blocked = {}, []
        for menu_id, menu in menus.items():
            if menu_id == 'root' or not menu.get('actionID'):
                continue
            model = None
            if menu['actionModel'] == 'ir.actions.act_window':
                model = env['ir.actions.act_window'].browse(menu['actionID']).res_model
            readable = env[model].with_user(user).has_access('read') if model and model in env else None
            checked[menu_id] = readable
            if readable is False or (model and model not in env):
                blocked.append({'menu': menu['xmlid'] or menu['name'], 'model': model})
        apps = [{'xmlid': menus[i]['xmlid'], 'name': menus[i]['name'], 'action_model': menus[i]['actionModel'],
                 'readable': checked.get(i)} for i in menus['root']['children']]
        empty = [a['xmlid'] for a in apps if not a['action_model']]
        result[key] = {'apps': apps, 'empty_apps': empty, 'blocked': blocked, 'menus_with_action': len(checked)}
    return result


def money(value):
    return str(Decimal(str(value)).quantize(Decimal(1)))


def finance_truth(env, user, dashboard, config, project_id=False, dates=(None, None)):
    """Independent recomputation from source rows readable by the actor (plain read(), no report code)."""
    projects = env['project.project'].with_user(user).search([('id', 'in', config['project_ids'])])
    accounts = {p.account_id.id: p.id for p in projects if p.account_id}
    selected = {project_id} if project_id else set(projects.ids)
    domain = [('id', 'in', config['invoice_ids']), ('state', '=', 'draft'), ('move_type', '=', 'out_invoice')]
    if dates[0]:
        domain.append(('invoice_date', '>=', dates[0]))
    if dates[1]:
        domain.append(('invoice_date', '<=', dates[1]))
    invoices = env['account.move'].with_user(user).search(domain)
    invoice_total = Decimal(0)
    invoice_ids = set()
    for line in invoices.invoice_line_ids.filtered(lambda line: line.display_type == 'product'):
        for key, pct in (line.analytic_distribution or {}).items():
            hits = [accounts[int(a)] for a in key.split(',') if int(a) in accounts]
            if hits and hits[0] in selected:
                invoice_total += Decimal(str(line.price_total)) * Decimal(str(pct)) / 100
                invoice_ids.add(line.move_id.id)
    domain = [('id', 'in', config['expense_ids']), ('state', 'in', ['draft', 'submitted', 'approved'])]
    if dates[0]:
        domain.append(('date', '>=', dates[0]))
    if dates[1]:
        domain.append(('date', '<=', dates[1]))
    expenses = env['hr.expense'].with_user(user).search(domain)
    by_state = {'draft': Decimal(0), 'submitted': Decimal(0), 'approved': Decimal(0)}
    expense_ids = set()
    for expense in expenses:
        for key, pct in (expense.analytic_distribution or {}).items():
            hits = [accounts[int(a)] for a in key.split(',') if int(a) in accounts]
            if hits and hits[0] in selected:
                by_state[expense.state] += Decimal(str(expense.total_amount)) * Decimal(str(pct)) / 100
                expense_ids.add(expense.id)
    # Records in the bound set that exist but are outside the three counted states (shown to explain labels).
    excluded = env['hr.expense'].with_user(user).search_read(
        [('id', 'in', config['expense_ids']), ('state', 'not in', ['draft', 'submitted', 'approved'])], ['state', 'total_amount'])
    return {'invoice': money(invoice_total), 'invoice_count': len(invoice_ids), 'expense_count': len(expense_ids),
            **{k: money(v) for k, v in by_state.items()}, 'excluded_expenses': excluded,
            'all_out_invoices_in_company': env['account.move'].with_user(user).search_count(
                [('move_type', '=', 'out_invoice'), ('company_id', '=', config['company_id'])]),
            'bound_invoice_ids': len(config['invoice_ids']), 'bound_expense_ids': len(config['expense_ids'])}


def coordination_truth(env, user, config, project_id=False):
    projects = env['project.project'].with_user(user).search([('id', 'in', config['project_ids'])])
    selected = [project_id] if project_id else projects.ids
    tasks = env['project.task'].with_user(user).search([('project_id', 'in', selected)])
    lines = env['account.analytic.line'].with_user(user).search([('project_id', 'in', selected)])
    return {'tasks': len(tasks), 'done': len(tasks.filtered(lambda t: t.state == '1_done')),
            'hours': str(Decimal(str(sum(lines.mapped('unit_amount')))).quantize(Decimal('0.01'))),
            'superuser_tasks': env['project.task'].search_count([('project_id', 'in', selected)]),
            'superuser_hours': str(Decimal(str(sum(env['account.analytic.line'].search(
                [('project_id', 'in', selected)]).mapped('unit_amount')))).quantize(Decimal('0.01')))}


def call(func):
    try:
        return {'ok': func()}
    except Exception as error:  # noqa: BLE001 - the audit records the denial class, never a stack.
        return {'error': type(error).__name__, 'message': str(error)[:200]}


def dashboard_audit(env, users):
    result = {}
    for kind, xmlid in DASHBOARDS.items():
        dashboard = env.ref(xmlid)
        config = json.loads(dashboard.spreadsheet_data)['settings']['tpDashboard']
        result[kind] = {'id': dashboard.id, 'config_keys': sorted(config), 'actors': {}}
        for key, user in users.items():
            board = dashboard.with_user(user)
            entry = {'can_read_dashboard': board.has_access('read')}
            report = call(lambda board=board: board.tp_dashboard_report({}))
            entry['report'] = report.get('error') or 'ok'
            if 'ok' in report:
                data = report['ok']
                entry['raw'] = {k: (money(v) if kind == 'finance' and k not in ('invoice_count', 'expense_count')
                                    else v) for k, v in data['raw'].items()}
                entry['projects'] = [p['code'] for p in data['projects']]
                payload = json.dumps(data, ensure_ascii=False, default=str)
                entry['payload_has_money'] = '₫' in payload or 'VND' in payload
                if kind == 'finance':
                    truth = call(lambda user=user: finance_truth(env, user, dashboard, config))
                else:
                    truth = call(lambda user=user: coordination_truth(env, user, config))
                entry['truth'] = truth.get('ok') or truth
                # Per-project drilldown ids must equal what the same actor can open in the source list.
                drill = {}
                for project in data['projects']:
                    for source in (('invoices', 'expenses') if kind == 'finance' else ('tasks', 'done', 'hours')):
                        action = call(lambda b=board, s=source, p=project['id']: b.tp_dashboard_action(s, {}, p, False))
                        if 'ok' in action:
                            ids = action['ok']['domain'][0][2]
                            visible = env[action['ok']['res_model']].with_user(user).search_count([('id', 'in', ids)])
                            drill[f"{project['code']}:{source}"] = {'ids': len(ids), 'readable': visible}
                        else:
                            drill[f"{project['code']}:{source}"] = action
                entry['drill'] = drill
                entry['drill_mismatch'] = [k for k, v in drill.items() if 'ids' in v and v['ids'] != v['readable']]
                # A project the actor cannot read must be refused, not silently widened.
                hidden = set(config['project_ids']) - {p['id'] for p in data['projects']}
                if hidden:
                    denied = call(lambda b=board, h=min(hidden): b.tp_dashboard_report({'project_id': h}))
                    entry['hidden_project_filter'] = denied.get('error', 'LEAK')
            elif report.get('error') not in ('AccessError',):
                entry['report_message'] = report.get('message')
            result[kind]['actors'][key] = entry
        # Revocation, using an actor who really has access before. Writes are flushed like a committed
        # request and the whole transaction is rolled back afterwards (the audit itself writes nothing).
        actor = 'khoa' if kind == 'coordination' else 'bao'
        user = users[actor]
        board = dashboard.with_user(user)
        source = 'tasks' if kind == 'coordination' else 'expenses'
        before = call(lambda b=board: b.tp_dashboard_report({}))
        via = {'allowed_user': user in dashboard.allowed_user_ids,
               'groups': sorted((dashboard.group_ids & user.all_group_ids).get_external_id().values())}
        try:
            dashboard.write({'allowed_user_ids': [(3, user.id)],
                             'group_ids': [(3, group.id) for group in dashboard.group_ids & user.all_group_ids]})
            env.flush_all()
            env.invalidate_all()
            # Odoo 20 caches read access per transaction; a new HTTP request starts with an empty cache.
            env.transaction.invalidate_access_cache()
            after = call(lambda b=board: b.tp_dashboard_report({}))
            drill_after = call(lambda b=board, s=source: b.tp_dashboard_action(s, {}, False, False))
            serialized_after = call(lambda b=board: b._get_serialized_readonly_dashboard())
        finally:
            env.cr.rollback()
            env.invalidate_all()
        result[kind]['dashboard_revoked'] = {'actor': actor, 'access_via': via, 'before': before.get('error', 'ok'),
                                             'report_after': after.get('error', 'ok'),
                                             'drill_after': drill_after.get('error', 'ok'),
                                             'open_after': serialized_after.get('error', 'ok')}
        # Other project: drop one assignment only; totals must equal what the actor can still read.
        assignments = env['tp.project.assignment'].search([('user_id', '=', user.id), ('active', '=', True)], order='project_id')
        dropped = assignments[:1]
        try:
            dropped.write({'active': False})
            env.flush_all()
            env.invalidate_all()
            env.transaction.invalidate_access_cache()
            after = call(lambda b=board: b.tp_dashboard_report({}))
            truth = call(lambda u=user: finance_truth(env, u, dashboard, config) if kind == 'finance'
                         else coordination_truth(env, u, config))
            hidden = call(lambda b=board, p=dropped.project_id.id: b.tp_dashboard_report({'project_id': p}))
            drill_hidden = call(lambda b=board, p=dropped.project_id.id, s=source: b.tp_dashboard_action(s, {}, p, False))
        finally:
            env.cr.rollback()
            env.invalidate_all()
        result[kind]['one_project_revoked'] = {
            'actor': actor, 'project': dropped.project_id.tp_code,
            'report_after': after.get('error') or {'raw': after['ok']['raw'],
                                                   'projects': [p['code'] for p in after['ok']['projects']]},
            'truth_after': truth.get('ok') or truth, 'filter_hidden_project': hidden.get('error', 'LEAK'),
            'drill_hidden_project': drill_hidden.get('error', 'LEAK')}
        # Source ACL: an actor allowed on the dashboard but without rights on the source model gets a denial, not money.
        if kind == 'finance':
            outsider = users['khoa']  # expense team approver, no accounting group
            try:
                dashboard.write({'allowed_user_ids': [(4, outsider.id)]})
                env.flush_all()
                env.invalidate_all()
                env.transaction.invalidate_access_cache()
                report = call(lambda b=dashboard.with_user(outsider): b.tp_dashboard_report({}))
                truth = call(lambda u=outsider: finance_truth(env, u, dashboard, config))
                drill = call(lambda b=dashboard.with_user(outsider): b.tp_dashboard_action('invoices', {}, False, False))
            finally:
                env.cr.rollback()
                env.invalidate_all()
            result[kind]['allowed_without_accounting_group'] = {
                'actor': 'khoa', 'report': report.get('error') or report['ok']['raw'],
                'truth': truth.get('ok') or truth,
                'invoice_drill_ids': drill.get('error') or len(drill['ok']['domain'][0][2])}
            # An actor without any account.move read ACL must be refused (no zero, no money).
            try:
                dashboard.write({'allowed_user_ids': [(4, users['long'].id)]})
                env.flush_all()
                env.invalidate_all()
                env.transaction.invalidate_access_cache()
                denied = call(lambda b=dashboard.with_user(users['long']): b.tp_dashboard_report({}))
            finally:
                env.cr.rollback()
                env.invalidate_all()
            result[kind]['allowed_without_source_acl'] = {'actor': 'long', 'report': denied.get('error', 'LEAK')}
        # Project assignment revocation: the dashboard must shrink to what the actor can still read.
        assignments = env['tp.project.assignment'].search([('user_id', '=', user.id), ('active', '=', True)])
        try:
            assignments.write({'active': False})
            env.flush_all()
            env.invalidate_all()
            # Odoo 20 caches read access per transaction; a new HTTP request starts with an empty cache.
            env.transaction.invalidate_access_cache()
            after = call(lambda b=board: b.tp_dashboard_report({}))
            truth = call(lambda u=user: finance_truth(env, u, dashboard, config) if kind == 'finance'
                         else coordination_truth(env, u, config))
            drill_after = call(lambda b=board, s=source: b.tp_dashboard_action(s, {}, False, False))
        finally:
            env.cr.rollback()
            env.invalidate_all()
        result[kind]['assignments_revoked'] = {
            'actor': actor, 'assignments': len(assignments),
            'report_after': after.get('error') or {'raw': after['ok']['raw'],
                                                   'projects': [p['code'] for p in after['ok']['projects']]},
            'truth_after': truth.get('ok') or truth,
            'drill_after': drill_after.get('error') or len(drill_after['ok']['domain'][0][2])}
    return result


def links_audit(env):
    """FK/ID walk of the fictional connected data; reports gaps, never repairs them."""
    projects = env['project.project'].search([('tp_code', '!=', False)])
    rows = []
    for project in projects:
        leads = env['crm.lead'].with_context(active_test=False).search([('tp_project_id', '=', project.id)])
        tasks = env['project.task'].search([('project_id', '=', project.id)])
        lines = env['account.analytic.line'].search([('project_id', '=', project.id)])
        expenses = env['hr.expense'].search([]).filtered(
            lambda e, p=project: p.account_id and any(str(p.account_id.id) in k.split(',') for k in (e.analytic_distribution or {})))
        invoice_lines = env['account.move.line'].search([('move_id.move_type', '=', 'out_invoice'), ('display_type', '=', 'product')]).filtered(
            lambda line, p=project: p.account_id and any(str(p.account_id.id) in k.split(',') for k in (line.analytic_distribution or {})))
        assignments = env['tp.project.assignment'].search([('project_id', '=', project.id), ('active', '=', True)])
        rows.append({
            'id': project.id, 'code': project.tp_code, 'company': project.company_id.id,
            'partner': project.partner_id.id or None, 'analytic_account': project.account_id.id or None,
            'crm_leads': leads.ids,
            'crm_partner_mismatch': leads.filtered(lambda lead, p=project: p.partner_id and lead.partner_id.commercial_partner_id
                                                   != p.partner_id.commercial_partner_id).ids,
            'crm_company_mismatch': leads.filtered(lambda lead, p=project: lead.company_id and lead.company_id != p.company_id).ids,
            'tasks': len(tasks),
            'tasks_other_company': tasks.filtered(lambda t, p=project: t.company_id != p.company_id).ids,
            'timesheets': len(lines), 'timesheets_without_task': lines.filtered(lambda line: not line.task_id).ids,
            'timesheet_task_project_mismatch': lines.filtered(lambda line, p=project: line.task_id and line.task_id.project_id != p).ids,
            'timesheet_account_mismatch': lines.filtered(lambda line, p=project: line.account_id != p.account_id).ids,
            'expenses': expenses.ids, 'invoices': sorted(set(invoice_lines.move_id.ids)),
            'invoice_partner_mismatch': sorted({line.move_id.id for line in invoice_lines
                                                if project.partner_id and line.move_id.partner_id.commercial_partner_id
                                                != project.partner_id.commercial_partner_id}),
            'assignments': [(a.user_id.login, a.role) for a in assignments],
        })
    leads = env['crm.lead'].with_context(active_test=False).search([])
    unlinked_leads = leads.filtered(lambda lead: not lead.tp_project_id)
    lead_fields = [name for name, field in env['crm.lead']._fields.items()
                   if field.type == 'many2one' and field.comodel_name == 'project.project']
    project_lead_fields = [name for name, field in env['project.project']._fields.items()
                           if field.type in ('many2one', 'one2many') and field.comodel_name == 'crm.lead']
    project_models = [model for model in env if model.startswith('tp.') and 'project' in model]
    return {'projects': rows, 'crm_leads': len(leads),
            'crm_without_project': [(lead.id, lead.stage_id.name, lead.active) for lead in unlinked_leads],
            'crm_to_project_fields': lead_fields,
            'project_to_crm_fields': project_lead_fields, 'tp_project_models': project_models}


def audit(env):
    users = actor_users(env)
    result = {'home': home_audit(env, users), 'dashboards': dashboard_audit(env, users), 'links': links_audit(env),
              'actors': {key: {'id': user.id, 'login': user.login,
                               'groups': sorted(user.group_ids.get_external_id().values())}
                         for key, user in users.items()}}
    env.cr.rollback()
    native.write(BASE / 'audit-clone.json', result)
    summary = {
        'home': {k: {'apps': [a['xmlid'] for a in v['apps']], 'empty': v['empty_apps'], 'blocked': v['blocked']}
                 for k, v in result['home'].items()},
        'dashboards': {kind: {actor: {k: entry.get(k) for k in ('report', 'raw', 'drill_mismatch', 'hidden_project_filter',
                                                              'payload_has_money')}
                              for actor, entry in data['actors'].items()} for kind, data in result['dashboards'].items()},
    }
    print(json.dumps(summary, ensure_ascii=False, default=str))


LOG_STAMP = r'(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \d+ (?P<level>[A-Z]+) (?P<logdb>\S+) '
# odoo/service/server.py logs "<report> when loading database %r"; odoo/tests/result.py formats the report.
SUMMARY_LINE = re.compile(LOG_STAMP + r"odoo\.tests\.result: (?P<failed>\d+) failed, (?P<errors>\d+) error\(s\) "
                          r"of (?P<total>\d+) tests when loading database '(?P<db>[^']+)'$")
# OdooTestResult.startTest logs "Starting <test> ..." on the test module logger, once per test run.
STARTED_LINE = re.compile(LOG_STAMP + r'odoo\.addons\.(?P<module>\w+)\.tests[\w.]*: Starting .+ \.\.\.$')
LEVEL_LINE = re.compile(LOG_STAMP)


def tag_modules(tags):
    """Modules named by the positive ``--test-tags`` specs ``[-][tag][/module][:class][.method]``.

    Returns (modules, unscoped): positive specs without a module only add the global total > 0 rule.
    """
    modules, unscoped = [], []
    for spec in (part.strip() for part in tags.split(',')):
        if not spec or spec.startswith('-'):
            continue
        if '/' not in spec:
            unscoped.append(spec)
            continue
        module = re.split(r'[:.\[]', spec.split('/', 1)[1], maxsplit=1)[0]
        if module and module not in modules:
            modules.append(module)
    return modules, unscoped


def _log_time(stamp):
    return datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S,%f').replace(tzinfo=UTC)


def evaluate_test_run(returncode, log_text, *, database, tags, started_at, expect_tests=None):
    """Pure verdict on one odoo-bin test run; ``ok`` only when every rule holds.

    Odoo writes log timestamps in UTC. ``started_at`` must be the aware UTC time taken just before
    the process started, so lines from an earlier run in the same file count as stale.
    """
    problems = []
    lines = log_text.splitlines()
    modules, unscoped = tag_modules(tags)
    if not modules and not unscoped:
        problems.append('no_positive_tags')
    if returncode != 0:
        problems.append('process_exit_nonzero')
    summaries = [match for line in lines if (match := SUMMARY_LINE.match(line))]
    started = [match for line in lines if (match := STARTED_LINE.match(line))]
    stale = [match for match in summaries + started if _log_time(match['ts']) < started_at]
    if stale:
        problems.append('stale_log_lines')
    total = failed = errors = None
    if not summaries:
        problems.append('summary_missing')
    elif len(summaries) > 1:
        problems.append('summary_multiple')
    else:
        summary = summaries[0]
        total, failed, errors = int(summary['total']), int(summary['failed']), int(summary['errors'])
        if summary['db'] != database or summary['logdb'] != database:
            problems.append('summary_wrong_database')
        if failed:
            problems.append('tests_failed')
        if errors:
            problems.append('tests_errored')
        if total == 0:
            problems.append('no_tests')
        if expect_tests is not None and total != expect_tests:
            problems.append('unexpected_test_count')
    per_module = {module: 0 for module in modules}
    for match in started:
        if match['logdb'] != database:
            problems.append('test_line_wrong_database')
            break
    for match in started:
        if match['module'] in per_module:
            per_module[match['module']] += 1
    problems.extend(f'no_tests_for_tag:{module}' for module, count in per_module.items() if not count)
    if total is not None and len(started) != total:
        problems.append('started_count_mismatch')
    error_lines = [line for line in lines
                   if (match := LEVEL_LINE.match(line)) and match['level'] in ('ERROR', 'CRITICAL')]
    if error_lines:
        problems.append('error_log_lines')
    return {'ok': not problems, 'problems': problems, 'returncode': returncode, 'database': database,
            'total': total, 'failed': failed, 'errors': errors, 'started': len(started), 'per_module': per_module,
            'unscoped_tags': unscoped, 'summary': [match.string for match in summaries][-3:],
            'error_lines': error_lines[:20]}


def odoo_tests(modules, tags, expect_tests=None):
    """Run addon tests against the stopped, owned clone; return 0 only on a verified pass.

    Each run writes a new private log; an existing path is refused so no older run can be read.
    """
    cfg, database = native.target_config('clone')
    owner = native.read(BASE / 'owner.json')
    clone_options = native.options(cfg)['options']
    require(database == DATABASE and owner.get('database') == DATABASE, 'Test target is not the owned clone database.')
    require(owner.get('http_port') == PORT and clone_options.get('http_port') == str(PORT),
            'Clone owner/config port does not match this operation.')
    require(not native.dev.is_listening(PORT), 'Stop the clone HTTP runtime before running tests.')
    runs = BASE / 'odoo-tests'
    runs.mkdir(exist_ok=True)
    stamp = datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')
    log, console, verdict_path = (runs / f'run-{stamp}{suffix}' for suffix in ('.log', '-console.log', '.json'))
    require(not any(path.exists() for path in (log, console, verdict_path)), 'Test run log already exists; refusing to reuse it.')
    started_at = datetime.now(UTC).replace(microsecond=0)
    with console.open('xb') as output:
        completed = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'odoo-bin'), '-c', str(cfg), '-d', database,
                                    '-u', modules, '--test-enable', '--test-tags', tags, '--stop-after-init',
                                    '--no-http', '--logfile', str(log)], cwd=ROOT, stdout=output,
                                   stderr=subprocess.STDOUT, check=False)
    text = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
    verdict = evaluate_test_run(completed.returncode, text, database=database, tags=tags, started_at=started_at,
                                expect_tests=expect_tests)
    verdict |= {'log': str(log.relative_to(ROOT)), 'modules': modules, 'tags': tags, 'port': PORT}
    native.write(verdict_path, verdict)
    print(json.dumps(verdict, ensure_ascii=False))
    return 0 if verdict['ok'] else 1


def task001(env):
    """TASK-001 stays denied: an assigned staff user reads a managed task but cannot write its state."""
    long = actor_users(env)['long']
    project = env['project.project'].search([('tp_code', '=', 'DA-2026-001')], limit=1)
    task = env['project.task'].search([('project_id', '=', project.id), ('user_ids', 'in', long.ids),
                                       ('state', '!=', '1_done')], limit=1, order='id')
    require(task, 'No open managed task assigned to Long on DA-2026-001.')
    before = task.state
    try:
        result = {'task_id': task.id, 'project': project.tp_code, 'state_before': before,
                  'read': call(lambda: task.with_user(long).read(['state'])[0]['state']),
                  'write_state': call(lambda: task.with_user(long).write({'state': '1_done'}))}
        env.flush_all()
        env.invalidate_all()
        result['state_after'] = task.state
    finally:
        env.cr.rollback()
    native.write(BASE / 'task001-clone.json', result)
    print(json.dumps(result, ensure_ascii=False, default=str))


def access_toggle(actor, kind, action):
    """Browser revocation probe on the owned clone only: remove/re-add one user on one TP dashboard."""
    state_file = BASE / 'revocations.json'

    def run(env):
        from odoo import Command
        user = actor_users(env)[actor]
        dashboard = env.ref(DASHBOARDS[kind])
        state = json.loads(state_file.read_text(encoding='utf-8')) if state_file.exists() else {}
        key = f'{actor}:{kind}'
        if action == 'revoke':
            require(key not in state and user in dashboard.allowed_user_ids, 'Nothing to revoke or revocation pending.')
            dashboard.allowed_user_ids = [Command.unlink(user.id)]
            state[key] = {'dashboard_id': dashboard.id, 'user_id': user.id, 'at': datetime.now(UTC).isoformat()}
        else:
            require(key in state and state[key]['user_id'] == user.id, 'No pending revocation to restore.')
            dashboard.allowed_user_ids = [Command.link(user.id)]
            del state[key]
        env.cr.commit()
        native.write(state_file, state)
        print(json.dumps({'action': action, 'actor': actor, 'dashboard_id': dashboard.id,
                          'allowed': user in dashboard.allowed_user_ids}))
    native.orm('clone', run)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    bind()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['snapshot', 'clone', 'start', 'stop', 'audit', 'dev-drift', 'odoo-tests',
                                                'revoke', 'restore', 'task001'])
    parser.add_argument('--actor', choices=ACTORS)
    parser.add_argument('--kind', choices=sorted(DASHBOARDS))
    parser.add_argument('--modules', default='tp_dashboard_privacy,tp_web_home')
    parser.add_argument('--tags', default='/tp_dashboard_privacy,/tp_web_home')
    parser.add_argument('--expect-tests', type=int, help='Optional exact test count; every tagged module must run tests.')
    args = parser.parse_args()
    if args.command == 'snapshot':
        snapshot()
    elif args.command == 'clone':
        native.clone()
    elif args.command in ('start', 'stop'):
        native.runtime(args.command)
    elif args.command == 'audit':
        native.orm('clone', audit)
    elif args.command == 'dev-drift':
        dev_drift()
    elif args.command == 'task001':
        native.orm('clone', task001)
    elif args.command in ('revoke', 'restore'):
        require(args.actor and args.kind, '--actor and --kind are required.')
        access_toggle(args.actor, args.kind, args.command)
    else:
        sys.exit(odoo_tests(args.modules, args.tags, args.expect_tests))


if __name__ == '__main__':
    main()
