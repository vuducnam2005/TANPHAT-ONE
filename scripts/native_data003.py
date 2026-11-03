"""Owned fictional-data operations. Private snapshots/reports never enter Git.

No upstream changes, direct business SQL writes, role creation, or dev posting.
"""
# Operator output and deferred Odoo imports are intentional.
# ruff: noqa: T201, PLC0415, EM101
import argparse
import configparser
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import uuid
import zipfile
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import backup_restore as backup
import dev
import psutil
import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASE = ROOT / '.local/native-data003'
DATABASE = 'tp_tanphat_data003_20261102'
PORT = 18149
OLD_NS = ('tp_native_sample_20261102', 'tp_native_link_20261102',
          'tp_native_todo_20261102', 'tp_native_data002_20261102')
NEW_NS = 'tp_native_data003_20261102'
CTX = {'lang': 'vi_VN', 'tz': 'Asia/Ho_Chi_Minh', 'allowed_company_ids': [1],
       'mail_create_nosubscribe': True, 'mail_auto_subscribe_no_notify': True,
       'mail_notify_force_send': False, 'no_reset_password': True,
       'no_mail_to_attendees': True, 'dont_notify': True}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')


def merge_journal(entries, current_value):
    """Keep the original before value and the final after value for each field."""
    merged = {}
    for item in entries:
        key = (item['model'], item['id'], item['field'])
        if key not in merged:
            merged[key] = dict(item)
        merged[key]['after'] = current_value(*key)
    return list(merged.values())


def isolate_mail(env):
    """Native security alerts/expenses send synchronously even with notification contexts."""
    import odoo
    require(not env['ir.mail_server'].search_count([]), 'An SMTP server is configured; review isolated mail transport first.')
    require(not dev.is_listening(9), 'Loopback discard port is unexpectedly listening.')
    odoo.tools.config['smtp_server'] = '127.0.0.1'
    odoo.tools.config['smtp_port'] = 9


def private_root():
    if not BASE.exists():
        BASE.mkdir()
        if os.name == 'nt':
            sid = subprocess.check_output(['whoami', '/user', '/fo', 'csv', '/nh'], text=True).strip().split(',')[1].strip('"')
            subprocess.run(['icacls', str(BASE), '/inheritance:r', '/grant:r',
                            f'*{sid}:(OI)(CI)F', '*S-1-5-18:(OI)(CI)F', '*S-1-5-32-544:(OI)(CI)F'],
                           check=True, capture_output=True)
        else:
            BASE.chmod(0o700)
    require(subprocess.run(['git', 'check-ignore', str(BASE / 'probe')], cwd=ROOT,
                           capture_output=True, check=False).returncode == 0, 'Private root must be ignored.')


def options(path):
    config = configparser.ConfigParser(interpolation=None)
    config.read(path, encoding='utf-8-sig')
    return config


def connect(db, *, admin=False):
    values = read(ROOT / '.local/dev-secrets.json')
    return psycopg2.connect(host='127.0.0.1', port=55432, dbname=db,
                           user='tp_dev_admin' if admin else 'tp_odoo',
                           password=values['pg_admin' if admin else 'pg_app'],
                           application_name='tp_native_data003', connect_timeout=10)


def preflight():
    marker = read(ROOT / '.local/runtime-owner.json')
    require(Path(marker['workspace']).resolve() == ROOT, 'Foreign workspace.')
    cfg = options(ROOT / '.local/odoo.conf')['options']
    require((cfg['db_name'], cfg['db_host'], cfg['db_port'], cfg['http_port']) ==
            ('tp_tanphat_dev', '127.0.0.1', '55432', '18069'), 'Unexpected dev configuration.')
    require(Path(cfg['data_dir']).resolve() == ROOT / '.local/odoo', 'Foreign data directory.')
    with closing(connect('tp_tanphat_dev', admin=True)) as connection, connection.cursor() as cursor:
        cursor.execute('SHOW data_directory')
        require(Path(cursor.fetchone()[0]).resolve() == ROOT / '.local/postgres/data', 'Foreign cluster.')
        cursor.execute("SELECT value FROM ir_config_parameter WHERE key='database.uuid'")
        identity = cursor.fetchone()[0]
    require(not dev.is_listening(18109) and not dev.is_listening(18119), 'Retired demo port is active.')
    return identity


def target_config(target):
    identity = preflight()
    if target == 'dev':
        marker = read(BASE / 'owner.json')
        require(marker['workspace'] == str(ROOT) and marker['database'] == DATABASE
                and marker['source_uuid'] == identity and marker['rehearsal_passed'], 'Restore rehearsal required for this workspace.')
        return ROOT / '.local/odoo.conf', 'tp_tanphat_dev'
    owner = read(BASE / 'owner.json')
    require(owner['workspace'] == str(ROOT) and owner['database'] == DATABASE, 'Foreign clone owner.')
    cfg = BASE / 'clone.conf'
    require(options(cfg)['options']['db_name'] == DATABASE, 'Wrong clone database.')
    with closing(connect(DATABASE)) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT value FROM ir_config_parameter WHERE key='tp_native_data003.owner'")
        row = cursor.fetchone()
        require(row and row[0] == owner['token'], 'Clone DB ownership mismatch.')
    return cfg, DATABASE


def snapshot():
    private_root()
    identity = preflight()
    require(not (BASE / 'owner.json').exists(), 'An owned operation already exists; reuse it.')
    folder = BASE / ('snapshot-' + datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ'))
    folder.mkdir()
    (folder / 'private').mkdir()
    for name in ('odoo.conf', 'dev-secrets.json', 'runtime-owner.json', 'odoo.pid'):
        source = ROOT / '.local' / name
        if source.exists():
            shutil.copy2(source, folder / 'private' / name)
    with zipfile.ZipFile(folder / 'maintained-source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in ('custom_addons', 'scripts', 'docs', 'ops', 'contracts'):
            for path in (ROOT / name).rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                    archive.write(path, path.relative_to(ROOT))
        archive.write(ROOT / 'AGENTS.md', 'AGENTS.md')
    running = dev.is_listening(18069)
    require(running, 'Expected existing dev runtime.')
    try:
        dev.stop_server()
        require(not dev.is_listening(18069), 'Dev did not stop.')
        with closing(connect('tp_tanphat_dev', admin=True)) as connection, connection.cursor() as cursor:
            cursor.execute('SELECT count(*) FROM pg_stat_activity WHERE datname=%s AND pid<>pg_backend_pid()',
                           ('tp_tanphat_dev',))
            require(cursor.fetchone()[0] == 0, 'Other dev DB writers are connected; snapshot refused.')
            tables = backup.table_inventory(connection)
            attachments = backup.attachment_inventory(connection, ROOT / '.local/odoo/filestore/tp_tanphat_dev')
        pg_env = backup.pg_environment(read(ROOT / '.local/dev-secrets.json')['pg_app'])
        backup.run([dev.pg_bin() / 'pg_dump.exe', '-h', '127.0.0.1', '-p', '55432', '-U', 'tp_odoo',
                    '-d', 'tp_tanphat_dev', '-Fc', '--no-owner', '--no-privileges', '-f', folder / 'database.dump'], env=pg_env)
        source = ROOT / '.local/odoo/filestore/tp_tanphat_dev'
        for path in source.rglob('*'):
            if path.is_file() and backup.BLOB_NAME.fullmatch(path.relative_to(source).as_posix()):
                destination = folder / 'filestore' / path.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
        write(folder / 'baseline.json', {'tables': tables, 'attachments': attachments, 'source_uuid': identity})
    finally:
        if running and not dev.is_listening(18069):
            dev.start_server()
    hashes = {p.relative_to(folder).as_posix(): backup.digest(p) for p in folder.rglob('*') if p.is_file()}
    write(folder / 'manifest.json', hashes)
    write(BASE / 'owner.json', {'workspace': str(ROOT), 'database': DATABASE, 'http_port': PORT,
                              'source_uuid': identity, 'token': secrets.token_hex(32),
                              'snapshot': str(folder), 'rehearsal_passed': False})
    print('SNAPSHOT PASS:', folder, len(hashes), 'checksums; dev restarted without upgrade/seed.')


def clone():
    private_root()
    preflight()
    owner = read(BASE / 'owner.json')
    require(owner['workspace'] == str(ROOT) and owner['database'] == DATABASE, 'Foreign operation.')
    folder = Path(owner['snapshot'])
    require(folder.resolve().is_relative_to(BASE), 'Snapshot escapes operation.')
    require(all(backup.digest(folder / name) == digest for name, digest in read(folder / 'manifest.json').items()),
            'Snapshot checksum mismatch.')
    with closing(connect('postgres', admin=True)) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1 FROM pg_database WHERE datname=%s', (DATABASE,))
            exists = bool(cursor.fetchone())
            if not exists:
                cursor.execute(sql.SQL("CREATE DATABASE {} OWNER tp_odoo TEMPLATE template0 ENCODING 'UTF8'").format(sql.Identifier(DATABASE)))
    pg_env = backup.pg_environment(read(ROOT / '.local/dev-secrets.json')['pg_app'])
    if not exists:
        backup.run([dev.pg_bin() / 'pg_restore.exe', '-h', '127.0.0.1', '-p', '55432', '-U', 'tp_odoo',
                    '-d', DATABASE, '--no-owner', '--no-privileges', '--exit-on-error', folder / 'database.dump'], env=pg_env)
    destination = BASE / 'data/filestore' / DATABASE
    if not destination.exists():
        shutil.copytree(folder / 'filestore', destination)
    baseline = read(folder / 'baseline.json')
    with closing(connect(DATABASE)) as connection:
        require(backup.table_inventory(connection) == baseline['tables'], 'Restored rowsets differ.')
        require(backup.attachment_inventory(connection, destination) == baseline['attachments'], 'Restored blobs differ.')
    cfg = options(ROOT / '.local/odoo.conf')
    cfg['options'].update({'db_name': DATABASE, 'dbfilter': '^' + DATABASE + '$', 'data_dir': str(BASE / 'data'),
                           'http_port': str(PORT), 'smtp_server': '127.0.0.1', 'smtp_port': '9',
                           'max_cron_threads': '0', 'workers': '0'})
    with (BASE / 'clone.conf').open('w', encoding='utf-8') as output:
        cfg.write(output)
    import odoo
    from odoo import SUPERUSER_ID, api
    from odoo.modules.registry import Registry
    odoo.tools.config.parse_config(['-c', str(BASE / 'clone.conf'), '--no-http'], setup_logging=False)
    with Registry(DATABASE).cursor() as cursor:
        env = api.Environment(cursor, SUPERUSER_ID, CTX)
        env['ir.cron'].search([]).write({'active': False})
        env['ir.mail_server'].search([]).write({'active': False})
        for key, value in {'database.is_neutralized': 'True', 'database.uuid': str(uuid.uuid4()),
                           'web.base.url': f'http://127.0.0.1:{PORT}', 'tp_native_data003.owner': owner['token']}.items():
            record = env['ir.config_parameter'].search([('key', '=', key)])
            if record:
                record.write({'value': value})
            else:
                env['ir.config_parameter'].create({'key': key, 'value': value})
        cursor.commit()
    owner['rehearsal_passed'] = True
    write(BASE / 'owner.json', owner)
    write(BASE / 'restore-evidence.json', {'passed': True, 'database': DATABASE,
                                        'tables': len(baseline['tables']), 'blob_references': len(baseline['attachments']),
                                        'neutralized': True, 'source_snapshot': str(folder)})
    print('RESTORE PASS:', len(baseline['tables']), 'exact table rowsets,', len(baseline['attachments']), 'blob references; clone neutralized.')


def orm(target, callback):
    cfg, database = target_config(target)
    import odoo
    from odoo import SUPERUSER_ID, api
    from odoo.modules.registry import Registry
    odoo.tools.config.parse_config(['-c', str(cfg), '--no-http'], setup_logging=False)
    for attempt in range(3):
        try:
            with Registry(database).cursor() as cursor:
                cursor.execute('SELECT pg_advisory_xact_lock(%s)', (2026110203,))
                env = api.Environment(cursor, SUPERUSER_ID, CTX)
                return callback(env)
        except psycopg2.errors.SerializationFailure:
            if attempt == 2:
                raise
            time.sleep(0.2)
    raise RuntimeError('Unreachable retry state.')


def inventory(env, *, include_access=False):
    bindings = env['ir.model.data'].search([('module', 'in', OLD_NS)], order='module,name')
    require(len(bindings) == 188, 'Legacy binding set differs; investigate rather than reseed.')
    users_by_key = {key: env.ref(OLD_NS[0] + '.user_' + key) for key in
                    ('long', 'son', 'huong', 'khoa', 'lan', 'nam', 'khang')}
    accountant = env.ref(NEW_NS + '.user_bao', raise_if_not_found=False)
    if accountant:
        users_by_key['bao'] = accountant
    users_by_key['admin'] = env.ref('base.user_admin')
    planner = env['res.users'].search([('login', '=', 'planner.dev')], limit=1)
    if planner:
        users_by_key['planner.dev'] = planner
    rows = []
    for binding in bindings:
        record = env[binding.model].browse(binding.res_id).exists()
        require(len(record) == 1, 'Missing fixture binding.')
        values = {}
        for name in ('name', 'login', 'company_id', 'user_id', 'user_ids', 'employee_id', 'department_id',
                     'parent_id', 'expense_manager_id', 'manager_id', 'project_id', 'task_id', 'partner_id',
                     'account_id', 'account_move_id', 'analytic_distribution', 'state', 'approval_state',
                     'currency_id', 'total_amount', 'amount_total', 'unit_amount', 'tp_code', 'privacy_visibility',
                     'model', 'res_id', 'body', 'description', 'code', 'company_ids', 'partner_ids',
                     'channel_id', 'allowed_user_ids', 'group_ids', 'start', 'stop', 'date', 'date_deadline',
                     'stage_id', 'tp_project_id'):
            field = record._fields.get(name)
            if not field or (name == 'parent_id' and field.comodel_name != 'hr.employee'):
                continue
            value = record[name]
            values[name] = value.ids if field.type in ('many2one', 'many2many', 'one2many') else value
        routes = {'project.project': 'project', 'project.task': 'all-tasks' if values.get('project_id') else 'to-do',
                  'crm.lead': 'crm', 'hr.expense': 'expenses', 'account.move': 'customer-invoices',
                  'hr.employee': 'employees', 'res.partner': 'contacts', 'calendar.event': 'calendar',
                  'discuss.channel': 'discuss', 'mail.message': 'discuss', 'account.analytic.line': 'timesheets',
                  'spreadsheet.dashboard': 'dashboards'}
        route = routes.get(binding.model)
        url = f'/odoo/{route}/{record.id}' if route else '/odoo/tp-home'
        if binding.model == 'spreadsheet.dashboard':
            url = f'/odoo/dashboards?dashboard_id={record.id}'
        access = {key: {operation: record.with_user(user).has_access(operation) for operation in ('read', 'write')}
                  for key, user in users_by_key.items()} if include_access else {}
        rows.append({'xmlid': binding.complete_name, 'model': binding.model, 'id': record.id, 'fields': values,
                     'ui_url': url, 'access_basis': 'native ACL/rules intersect TP project scope; tested actor matrix in checks report',
                     'actor_record_access': access,
                     'access_limit': 'Record ACL/rule gate only; field/action/state conditions may further restrict writes.',
                     'disposition': 'reuse; per-batch field journal controls changes'})
    employees = env['hr.employee'].browse([r['id'] for r in rows if r['model'] == 'hr.employee'])
    users = employees.user_id
    details = [{'id': user.id, 'login': user.login, 'employee': user.employee_id.id,
                'groups': user.group_ids.get_external_id(), 'projects': env['tp.project.assignment'].search([
                    ('user_id', '=', user.id), ('active', '=', True)]).project_id.ids} for user in users]
    return {'bindings': rows, 'actors': details,
            'projects': env['project.project'].search([('id', 'in', [r['id'] for r in rows if r['model'] == 'project.project'])]).read(
                ['name', 'user_id', 'partner_id', 'account_id', 'tp_code', 'privacy_visibility']),
            'expenses': env['hr.expense'].browse([r['id'] for r in rows if r['model'] == 'hr.expense']).read(
                ['name', 'employee_id', 'manager_id', 'total_amount', 'payment_mode', 'state', 'account_move_id']),
            'counts': {m: sum(r['model'] == m for r in rows) for m in sorted({r['model'] for r in rows})}}


def migrate(env, target, mode):
    """One transaction per batch, with its field/action ledger committed in that transaction."""
    from odoo import Command

    require(mode in ('dry-run', 'apply', 'verify', 'fail-test'), 'Unknown migration mode.')
    isolate_mail(env)
    inventory(env)  # All legacy bindings must resolve before any write.
    admin = env.ref('base.user_admin')

    def owned(key):
        return env.ref(OLD_NS[0] + '.' + key)

    def new_owned(key):
        return env.ref(NEW_NS + '.' + key, raise_if_not_found=False)
    ledger_key = NEW_NS + '.bootstrap'
    marker = env['ir.config_parameter'].search([('key', '=', ledger_key)])
    saved = json.loads(marker.value) if marker else None
    journal = []
    created = []
    credentials_path = BASE / 'actor-secrets.json'
    credentials = read(credentials_path) if credentials_path.exists() else {}
    original_users = {key: owned('user_' + key) for key in ('long', 'son', 'huong', 'khoa', 'lan', 'nam', 'khang')}

    def bind(record, key):
        env['ir.model.data'].create({'module': NEW_NS, 'name': key, 'model': record._name,
                                     'res_id': record.id, 'noupdate': True})
        created.append({'xmlid': NEW_NS + '.' + key, 'model': record._name, 'id': record.id})
        return record

    def value(record, name):
        field = record._fields[name]
        current = record[name]
        if field.type == 'many2one':
            return current.id or False
        if field.type in ('many2many', 'one2many'):
            return sorted(current.ids)
        return current

    def update(record, values):
        changes = {}
        for name, expected in values.items():
            current = value(record, name)
            if current == expected:
                continue
            require(mode != 'verify', f'Verification drift: {record._name}/{record.id}/{name}')
            changes[name] = [Command.set(expected)] if record._fields[name].type == 'many2many' else expected
            journal.append({'model': record._name, 'id': record.id, 'field': name, 'before': current, 'after': expected})
        if changes:
            record.write(changes)

    accountant = new_owned('user_bao')
    if not accountant:
        require(mode != 'verify', 'Missing accountant.')
        employee = owned('employee_bao')
        require(not employee.user_id, 'Existing finance employee already has a user; investigate.')
        require(not env['res.users'].search_count([('login', '=', 'staff.bao@example.invalid')]), 'Duplicate fake login.')
        accountant = bind(env['res.users'].with_context(no_reset_password=True).create({
            'name': employee.name, 'login': 'staff.bao@example.invalid', 'email': 'bao@example.invalid',
            'company_id': 1, 'company_ids': [Command.set([1])],
            'group_ids': [Command.set([env.ref('tp_core.group_user').id, env.ref('project.group_project_user').id,
                                      env.ref('account.group_account_user').id])],
            'lang': 'vi_VN', 'tz': 'Asia/Ho_Chi_Minh', 'notification_type': 'inbox',
        }), 'user_bao')
        update(employee, {'user_id': accountant.id})
    original_users['bao'] = accountant
    require(all(user.login.endswith('@example.invalid') and user.id not in (1, 2) for user in original_users.values()),
            'Only proven fictional accounts may be enabled.')
    for key, user in original_users.items():
        update(user, {'lang': 'vi_VN', 'tz': 'Asia/Ho_Chi_Minh', 'notification_type': 'inbox'})
        enabled = env['ir.model.data'].search_count([('module', '=', NEW_NS), ('name', '=', 'enabled_' + key)])
        require(not enabled or key in credentials, 'Enabled actor credential file is missing; do not rotate silently.')
        if key not in credentials:
            require(mode != 'verify', 'Missing private actor credentials.')
            credentials[key] = {'login': user.login, 'password': secrets.token_urlsafe(30)}
            write(credentials_path, credentials)  # Persist before DB commit to survive interruption; no rotation on retry.
        require(credentials[key]['login'] == user.login, 'Credential ownership mismatch.')
        if not enabled:
            require(mode != 'verify', 'Fake actor has not been enabled.')
            user.write({'password': credentials[key]['password']})
            bind(user, 'enabled_' + key)
    for key in ('khoa', 'nam'):
        user = original_users[key]
        update(user, {'group_ids': sorted(set(user.group_ids.ids + [env.ref('hr_expense.group_hr_expense_team_approver').id]))})
    # The existing coordinator is allowed to view the CRM pipeline, without a project-manager group.
    user = original_users['nam']
    update(user, {'group_ids': sorted(set(user.group_ids.ids + [env.ref('sales_team.group_sale_salesman_all_leads').id]))})
    hierarchy = {'khoa': 'nam', 'lan': 'nam', 'huong': 'nam', 'long': 'khoa', 'son': 'khoa',
                 'phuc': 'khoa', 'linh': 'lan', 'tuan': 'lan'}
    for key, manager in hierarchy.items():
        update(owned('employee_' + key), {'parent_id': owned('employee_' + manager).id,
                                         'expense_manager_id': owned('user_' + manager).id})
    for project_key in ('cau', 'duong', 'nut', 'venbien'):
        project = owned('project_' + project_key)
        assignment = new_owned('assignment_bao_' + project_key)
        if not assignment:
            require(mode != 'verify', 'Missing accountant assignment.')
            bind(env['tp.project.assignment'].create({'project_id': project.id, 'user_id': accountant.id, 'role': 'reader'}),
                 'assignment_bao_' + project_key)
    if not env['tp.project.assignment'].search_count([('user_id', '=', original_users['nam'].id),
                                                    ('project_id', '=', owned('project_duong').id), ('active', '=', True)]):
        require(mode != 'verify', 'Missing manager scope for design team.')
        bind(env['tp.project.assignment'].create({'project_id': owned('project_duong').id,
                                                 'user_id': original_users['nam'].id, 'role': 'reader'}), 'assignment_nam_duong')
    # Existing personal work remains with admin. Add only relevant fake attendees/members.
    events = {'event_01': ('nam', 'khoa', 'lan'), 'event_02': ('khoa', 'long', 'nam'),
              'event_03': ('lan', 'nam'), 'event_04': ('khoa', 'son'), 'event_05': ('nam', 'khoa', 'lan'),
              'event_06': ('khoa', 'long'), 'event_07': ('huong', 'nam'), 'event_08': ('nam', 'khoa', 'lan')}
    for key, members in events.items():
        event = env.ref(OLD_NS[3] + '.' + key)
        require(event.privacy == 'private' and not event.alarm_ids, 'Unexpected calendar sharing/alarm.')
        update(event, {'partner_ids': sorted(set(event.partner_ids.ids + [original_users[m].partner_id.id for m in members]))})
    groups = {'channel_coordination': ('nam', 'khoa', 'lan'), 'channel_business': ('nam', 'huong'),
              'channel_survey_design': ('nam', 'khoa', 'lan', 'long', 'son')}
    for key, members in groups.items():
        channel = env.ref(OLD_NS[3] + '.' + key)
        require(channel.channel_type == 'group', 'Shared channel is outside scope.')
        for member in members:
            partner = original_users[member].partner_id
            if partner not in channel.channel_member_ids.partner_id:
                require(mode != 'verify', 'Missing group member.')
                record = env['discuss.channel.member'].create({'channel_id': channel.id, 'partner_id': partner.id})
                bind(record, key + '_' + member)
    for key, members in {'dashboard_coordination': ('nam', 'khoa'),
                         'dashboard_finance_draft': ('bao',)}.items():
        dashboard = env.ref(OLD_NS[3] + '.' + key)
        require(not dashboard.group_ids, 'Dashboard must remain user-allowlisted.')
        update(dashboard, {'allowed_user_ids': sorted(set([admin.id] + [original_users[m].id for m in members]))})
    for row in env['hr.expense'].browse([r['id'] for r in inventory(env)['bindings'] if r['model'] == 'hr.expense']):
        manager = row.employee_id.expense_manager_id
        require(manager and manager != row.employee_id.user_id, 'Missing independent fake approver.')
        update(row, {'manager_id': manager.id})
    require(not any(u.has_group('base.group_system') or u.has_group('tp_core.group_manager') for u in original_users.values()),
            'Privileged bypass detected.')
    if mode == 'fail-test':
        raise RuntimeError('DATA003_INJECTED_FAILURE')
    payload = {'journal': merge_journal(journal, lambda model, record_id, field: value(env[model].browse(record_id), field)),
               'created': created, 'actors': {key: user.id for key, user in original_users.items()}}
    if not marker and mode != 'verify':
        env['ir.config_parameter'].create({'key': ledger_key, 'value': json.dumps(payload, default=str)})
    elif marker:
        require(saved['actors'] == payload['actors'], 'Actor ledger differs.')
        cumulative = merge_journal(saved['journal'] + journal,
                                   lambda model, record_id, field: value(env[model].browse(record_id), field))
        merged = {**saved, 'journal': cumulative}
        if merged != json.loads(marker.value):
            require(mode != 'verify', 'Bootstrap journal needs reconciliation with a completed batch.')
            marker.write({'value': json.dumps(merged, default=str)})
    env.flush_all()
    result = {**payload, 'target': target, 'mode': mode, 'updated': len(journal), 'created_count': len(created)}
    if mode == 'apply':
        env.cr.commit()
    else:
        env.cr.rollback()
    return result


def native_actions(env, target, mode):
    """Native submit/approve under real fake actors; own-account receipts stay draft."""
    require(mode in ('dry-run', 'apply', 'verify', 'fail-test'), 'Unknown action mode.')
    # Local process only, never rewrite dev config/cron/SMTP. Native Expense.send() ignores notification contexts.
    # A refused loopback connection leaves an owned exception mail, with no retryable outgoing mail.
    isolate_mail(env)
    actors = read(BASE / f'actors-{target}-apply.json')['actors']
    mail_before = set(env['mail.mail'].search([]).ids)
    notification_before = set(env['mail.notification'].search([]).ids)
    posted_before = set(env['account.move'].search([('state', '=', 'posted')]).ids)
    payments_before = set(env['account.payment'].search([]).ids)
    bindings = inventory(env)['bindings']
    expenses = env['hr.expense'].browse([r['id'] for r in bindings if r['model'] == 'hr.expense']).sorted('id')
    require(len(expenses) == 6 and sum(expenses.mapped('total_amount')) == 7160000, 'Expense totals differ.')
    require(all(exp.payment_mode == 'own_account' for exp in expenses), 'Company-paid action could create a payment.')
    invariant_fields = ['employee_id', 'company_id', 'currency_id', 'total_amount', 'analytic_distribution']
    before = expenses.read(invariant_fields)
    events = []
    # Existing logistics/design receipts can be approved independently; survey proposals await review.
    for expense, expected in zip(expenses, ('submitted', 'approved', 'approved', 'draft', 'submitted', 'draft'), strict=True):
        actor = expense.employee_id.user_id
        manager = expense.manager_id
        require(actor.id in actors.values() and manager.id in actors.values() and manager != actor, 'Actor/approver outside fake scope.')
        for action, desired in ([('action_submit', 'submitted'), ('action_approve', 'approved')] if expected == 'approved'
                                else [('action_submit', 'submitted')] if expected == 'submitted' else []):
            key = NEW_NS + f'.action_{expense.id}_{action}'
            ledger = env['ir.config_parameter'].search([('key', '=', key)])
            if ledger:
                require(expense.state in ('submitted', 'approved') and
                        (desired != 'approved' or expense.state == 'approved'), 'Native action ledger/state drift.')
                continue
            require(mode != 'verify', 'Missing native action ledger.')
            acting = actor if action == 'action_submit' else manager
            record = expense.with_user(acting)
            require(not record.env.su, 'Actor must not run in superuser mode.')
            require(record.state == ('draft' if action == 'action_submit' else 'submitted'), 'Unexpected action precondition.')
            getattr(record, action)()
            env.flush_all()
            require(expense.state == desired, 'Unexpected native transition result.')
            event = {'expense': expense.id, 'action': action, 'actor': acting.id, 'after': desired,
                     'move': expense.account_move_id.id, 'move_state': expense.account_move_id.state}
            env['ir.config_parameter'].create({'key': key, 'value': json.dumps(event)})
            events.append(event)
            if mode == 'fail-test':
                raise RuntimeError('DATA003_NATIVE_INJECTED_FAILURE')
        require(expense.state == expected, 'Expense stage differs from scenario.')
        if expense.account_move_id:
            require(expense.account_move_id.state == 'draft' and not expense.account_move_id.origin_payment_id, 'Unsafe posting/payment side effect.')
            name = f'expense_move_{expense.id}'
            bound = env.ref(NEW_NS + '.' + name, raise_if_not_found=False)
            if not bound:
                require(mode != 'verify', 'Missing native side-effect ownership.')
                env['ir.model.data'].create({'module': NEW_NS, 'name': name, 'model': 'account.move',
                                             'res_id': expense.account_move_id.id, 'noupdate': True})
    new_mail = env['mail.mail'].search([('id', 'not in', sorted(mail_before))])
    require(all(mail.state == 'exception' and mail.email_to.endswith('@example.invalid') for mail in new_mail),
            'Unexpected external/queued mail side effect.')
    new_notifications = env['mail.notification'].search([('id', 'not in', sorted(notification_before))])
    fake_partners = env['res.users'].browse(list(actors.values())).partner_id
    require(not (new_notifications.res_partner_id - fake_partners), 'Notification to a non-fixture actor.')
    require(set(env['account.move'].search([('state', '=', 'posted')]).ids) == posted_before, 'Posting is outside scope.')
    require(set(env['account.payment'].search([]).ids) == payments_before, 'Payment is outside scope.')
    require(expenses.read(invariant_fields) == before, 'Expense amount/company/employee/analytic changed.')
    for mail in new_mail:
        env['ir.model.data'].create({'module': NEW_NS, 'name': f'native_mail_exception_{mail.id}',
                                     'model': 'mail.mail', 'res_id': mail.id, 'noupdate': True})
    result = {'events': events, 'target': target, 'mode': mode, 'actions_executed': len(events),
              'new_mail_exception_ids': new_mail.ids, 'notification_ids': new_notifications.ids,
              'expenses': expenses.read(['state', 'total_amount', 'account_move_id']),
              'dashboard': {key: env['hr.expense'].with_user(uid).get_expense_dashboard([('id', 'in', expenses.ids)])
                            for key, uid in actors.items()}}
    if mode == 'apply':
        env.cr.commit()
    else:
        env.cr.rollback()
    return result


def link_data(env, target, mode):
    import re
    require(env['ir.module.module'].search([('name', '=', 'tp_crm_project_bridge')]).state == 'installed', 'Install tested bridge first.')
    changes = []
    for project_key, lead_index in (('cau', 0), ('duong', 2), ('nut', 4), ('venbien', 7)):
        project = env.ref(OLD_NS[0] + '.project_' + project_key)
        lead = env.ref(OLD_NS[0] + f'.lead_{lead_index:02}')
        if lead.tp_project_id != project:
            require(mode != 'verify', 'CRM linkage drift.')
            changes.append({'model': 'crm.lead', 'id': lead.id, 'field': 'tp_project_id', 'before': lead.tp_project_id.id, 'after': project.id})
            lead.with_user(env.ref('base.user_admin')).write({'tp_project_id': project.id})
        coordinator = env.ref(OLD_NS[0] + '.user_nam')
        if lead.user_id != coordinator:
            require(mode != 'verify', 'CRM coordinator drift.')
            changes.append({'model': lead._name, 'id': lead.id, 'field': 'user_id', 'before': lead.user_id.id, 'after': coordinator.id})
            lead.write({'user_id': coordinator.id})
    for key in ('dashboard_coordination', 'dashboard_finance_draft'):
        dashboard = env.ref(OLD_NS[3] + '.' + key)
        if not dashboard.tp_internal_only:
            require(mode != 'verify', 'Dashboard public-share protection missing.')
            changes.append({'model': dashboard._name, 'id': dashboard.id, 'field': 'tp_internal_only', 'before': False, 'after': True})
            dashboard.write({'tp_internal_only': True})
    bindings = inventory(env)['bindings']
    replacements = {'__CID__': 1, '__EXPENSE_IDS__': [r['id'] for r in bindings if r['model'] == 'hr.expense'],
                    '__INVOICE_IDS__': [r['id'] for r in bindings if r['model'] == 'account.move']}
    text = (ROOT / 'docs/demo/dashboards/tp_invoice_expense_connected.template.json').read_text(encoding='utf-8')
    for key, value in replacements.items():
        text = text.replace('"' + key + '"', json.dumps(value))
    require(not re.search(r'__[A-Z_]+__', text), 'Unresolved dashboard domain tokens.')
    expected = json.dumps(json.loads(text), ensure_ascii=False)
    dashboard = env.ref(OLD_NS[3] + '.dashboard_finance_draft')
    current = json.dumps(json.loads(dashboard.spreadsheet_data), ensure_ascii=False)
    if current != expected:
        require(mode != 'verify', 'Dashboard source drift.')
        changes.append({'model': dashboard._name, 'id': dashboard.id, 'field': 'spreadsheet_data',
                        'before': current, 'after': expected})
        dashboard.with_user(env.ref('base.user_admin')).write({'spreadsheet_data': expected})
    key = NEW_NS + '.linkage'
    if not env['ir.config_parameter'].search_count([('key', '=', key)]):
        require(mode != 'verify', 'Missing linkage journal.')
        env['ir.config_parameter'].create({'key': key, 'value': json.dumps(changes)})
    elif changes:
        marker = env['ir.config_parameter'].search([('key', '=', key)])
        saved = json.loads(marker.value)
        for change in changes:
            previous = next((row for row in saved if (row['model'], row['id'], row['field']) ==
                             (change['model'], change['id'], change['field'])), None)
            if previous:
                previous['after'] = change['after']
            else:
                saved.append(change)
        marker.write({'value': json.dumps(saved)})
    env.flush_all()
    if mode == 'fail-test':
        raise RuntimeError('DATA003_LINK_INJECTED_FAILURE')
    if mode == 'apply':
        env.cr.commit()
    else:
        env.cr.rollback()
    return {'updated': len(changes), 'created': 0, 'target': target, 'mode': mode}


def runtime(command):
    cfg, database = target_config('clone')
    owner = read(BASE / 'owner.json')
    if command == 'start':
        require(not dev.is_listening(PORT), 'Clone port occupied; refusing reuse.')
        with (BASE / 'clone-server.log').open('ab') as output:
            process = subprocess.Popen([sys.executable, str(ROOT / 'odoo-bin'), '-c', str(cfg), '-d', database],
                                       cwd=ROOT, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        owner['pid'] = process.pid
        write(BASE / 'owner.json', owner)
        for _ in range(50):
            if dev.is_listening(PORT):
                print('CLONE HTTP READY:', PORT, 'owned wrapper PID', process.pid)
                return
            require(process.poll() is None, 'Clone exited; inspect private server log.')
            time.sleep(0.5)
        raise RuntimeError('Clone HTTP startup timed out.')
    require(owner.get('pid'), 'Missing owned runtime PID.')
    if psutil.pid_exists(owner['pid']):
        process = psutil.Process(owner['pid'])
        require(str(cfg).casefold() in ' '.join(process.cmdline()).casefold(), 'PID was reused by a foreign process.')
        children = process.children(recursive=True)
        for child in reversed(children):
            child.terminate()
        process.terminate()
        psutil.wait_procs([process, *children], timeout=10)
    require(not dev.is_listening(PORT), 'Owned clone listener did not stop.')
    print('CLONE STOPPED:', PORT)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['snapshot', 'clone', 'inventory', 'actors', 'actions', 'links', 'start', 'stop'])
    parser.add_argument('--target', choices=['clone', 'dev'], default='clone')
    parser.add_argument('--mode', choices=['dry-run', 'apply', 'verify', 'fail-test'], default='verify')
    args = parser.parse_args()
    if args.command == 'snapshot':
        snapshot()
    elif args.command == 'clone':
        clone()
    elif args.command in ('start', 'stop'):
        runtime(args.command)
    elif args.command == 'inventory':
        result = orm(args.target, lambda env: inventory(env, include_access=True))
        write(BASE / f'inventory-{args.target}.json', result)
        print(json.dumps({k: v for k, v in result.items() if k != 'bindings'}, ensure_ascii=False, default=str))
    elif args.command == 'actors':
        result = orm(args.target, lambda env: migrate(env, args.target, args.mode))
        write(BASE / f'actors-{args.target}-{args.mode}.json', result)
        print(json.dumps({k: v for k, v in result.items() if k not in ('journal', 'created')}, ensure_ascii=False))
    elif args.command == 'actions':
        result = orm(args.target, lambda env: native_actions(env, args.target, args.mode))
        write(BASE / f'actions-{args.target}-{args.mode}.json', result)
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        result = orm(args.target, lambda env: link_data(env, args.target, args.mode))
        write(BASE / f'links-{args.target}-{args.mode}.json', result)
        print(json.dumps(result))


if __name__ == '__main__':
    main()
