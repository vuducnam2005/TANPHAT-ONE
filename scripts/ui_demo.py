"""Prepare, start and stop the isolated UI-DEMO-001 Odoo runtime under .local/ui-demo-001/.

The demo reuses the local PostgreSQL cluster of scripts/dev.py (after its ownership check) but owns only its
own databases, config, data dir, credentials and Odoo process. It never touches the dev/test databases.
"""
# CLI output and deferred Odoo imports are intentional.
# ruff: noqa: T201, PLC0415, EM101, EM102
import argparse
import configparser
import datetime
import importlib.util
import json
import os
import secrets
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local' / 'ui-demo-001'
CONFIG = BASE / 'odoo.conf'
OWNER = BASE / 'owner.json'
CREDENTIALS = BASE / 'credentials.json'
PID_FILE = BASE / 'odoo.pid'
DEMO_DB = 'tp_tanphat_demo_ui001'
TEST_DB = 'tp_tanphat_demo_ui001_test'
DB_PREFIX = 'tp_tanphat_demo_'
# Databases of other runtimes; the demo tool refuses them whatever the prefix check says.
FOREIGN_DBS = frozenset({'tp_tanphat_dev', 'tp_tanphat_test', 'tp_tanphat_restore', 'postgres', 'template0', 'template1'})
HTTP_PORT = 18109
TEST_HTTP_PORT = 18119
# Only the demo addon is installed; its manifest pulls tp_project, tp_contract, project, hr and crm.
MODULES = 'tp_demo_workspace'
TOKEN_PARAM = 'tp_demo_workspace.owner_token'
ACTOR_LOGINS = ('demo.lanhdao', 'demo.kysu')

_spec = importlib.util.spec_from_file_location('tp_dev_runtime', ROOT / 'scripts' / 'dev.py')
dev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dev)


def check_database(name):
    if name in FOREIGN_DBS or not name.startswith(DB_PREFIX):
        raise RuntimeError(f'Refusing database {name!r}: the demo tool only manages {DB_PREFIX}* databases.')
    return name


def read_owner():
    if not OWNER.exists():
        return None
    owner = json.loads(OWNER.read_text(encoding='utf-8'))
    if owner.get('workspace') != str(ROOT):
        raise RuntimeError('.local/ui-demo-001 belongs to another workspace. Refusing to manage it.')
    return owner


def ensure_owner():
    BASE.mkdir(parents=True, exist_ok=True)
    owner = read_owner()
    if owner is None:
        owner = {'workspace': str(ROOT), 'token': secrets.token_urlsafe(24), 'databases': [],
                 'created_at': datetime.datetime.now(datetime.UTC).isoformat(timespec='seconds')}
        write_json(OWNER, owner)
    return owner


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def credentials():
    """Generated demo passwords, kept only in the ignored local folder and reused on later runs."""
    BASE.mkdir(parents=True, exist_ok=True)
    values = json.loads(CREDENTIALS.read_text(encoding='utf-8')) if CREDENTIALS.exists() else {}
    changed = False
    for key in ('admin', 'db_manager', *ACTOR_LOGINS):
        if not values.get(key):
            values[key] = secrets.token_urlsafe(18)
            changed = True
    if changed:
        write_json(CREDENTIALS, values)
    return values


def admin_connection(pg_values, dbname='postgres'):
    import psycopg2

    return closing(psycopg2.connect(host='127.0.0.1', port=dev.PG_PORT, user='tp_dev_admin',
                                    password=pg_values['pg_admin'], dbname=dbname))


def database_exists(pg_values, name):
    with admin_connection(pg_values) as connection, connection.cursor() as cursor:
        cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', (name,))
        return bool(cursor.fetchone())


def database_token(pg_values, name):
    """The owner token stored in the demo database, or None while it is not tagged yet (install or seed pending)."""
    with admin_connection(pg_values, name) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('public.ir_config_parameter') IS NOT NULL")
        if not cursor.fetchone()[0]:
            return None
        cursor.execute('SELECT value FROM ir_config_parameter WHERE key = %s', (TOKEN_PARAM,))
        row = cursor.fetchone()
        return row[0] if row else None


def check_ownership(pg_values, owner, name):
    """Allow only databases this tool created (recorded in owner.json) and, once installed, tagged with its token."""
    check_database(name)
    if not database_exists(pg_values, name):
        return False
    if name not in owner['databases']:
        raise RuntimeError(f'Database {name!r} already exists but was not created by the demo tool. Refusing to use it.')
    token = database_token(pg_values, name)
    if token is not None and token != owner['token']:
        raise RuntimeError(f'Database {name!r} carries another owner token. Refusing to use it.')
    return True


def create_database(pg_values, owner, name):
    from psycopg2 import sql

    check_database(name)
    owner['databases'] = sorted({*owner['databases'], name})
    write_json(OWNER, owner)
    with admin_connection(pg_values) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE DATABASE {} OWNER tp_odoo TEMPLATE template0 ENCODING 'UTF8'").format(
                sql.Identifier(name)))


def write_config(pg_values, values):
    BASE.mkdir(parents=True, exist_ok=True)
    (BASE / 'logs').mkdir(exist_ok=True)
    config = configparser.ConfigParser(interpolation=None)
    config['options'] = {
        'addons_path': ','.join(str(ROOT / path) for path in ('addons', 'custom_addons')),
        'data_dir': str(BASE / 'data'),
        'db_host': '127.0.0.1', 'db_port': str(dev.PG_PORT), 'db_user': 'tp_odoo', 'db_password': pg_values['pg_app'],
        'db_name': DEMO_DB, 'dbfilter': f'^{DEMO_DB}$', 'list_db': 'False',
        'admin_passwd': values['db_manager'],
        'http_interface': '127.0.0.1', 'http_port': str(HTTP_PORT),
        'workers': '0', 'max_cron_threads': '0', 'proxy_mode': 'False',
        'smtp_server': '127.0.0.1', 'smtp_port': '9',
        'log_level': 'info',
    }
    with CONFIG.open('w', encoding='utf-8') as output:
        config.write(output)


def odoo_args(*args):
    return [sys.executable, ROOT / 'odoo-bin', '-c', CONFIG, *args]


def run_logged(args, name):
    log = BASE / 'logs' / f'{name}.log'
    with log.open('ab') as output:
        result = subprocess.run([str(arg) for arg in args], cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                check=False, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    if result.returncode:
        raise RuntimeError(f'{name} failed (exit {result.returncode}). Inspect {log.relative_to(ROOT)}.')


def installed(pg_values, name):
    """True once tp_demo_workspace is installed in the database (seeding may still be pending)."""
    with admin_connection(pg_values, name) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('public.ir_module_module') IS NOT NULL")
        if not cursor.fetchone()[0]:
            return False
        cursor.execute("SELECT 1 FROM ir_module_module WHERE name = %s AND state = 'installed'", (MODULES,))
        return bool(cursor.fetchone())


def install(pg_values, name, *, test=False):
    flag = '-u' if installed(pg_values, name) else '-i'
    args = odoo_args('-d', name, '--db-filter', f'^{name}$', flag, MODULES, '--without-demo=True',
                     '--load-language=vi_VN', '--stop-after-init')
    if test:
        if dev.is_listening(TEST_HTTP_PORT):
            raise RuntimeError(f'Test HTTP port {TEST_HTTP_PORT} is already occupied.')
        args += ['--test-enable', '--test-tags', '/tp_demo_workspace', '--http-port', str(TEST_HTTP_PORT)]
    else:
        args += ['--no-http']
    run_logged(args, 'test' if test else 'install')


def seed(owner, values):
    """Load the fixtures, apply demo passwords, tag the database and neutralize outgoing services."""
    sys.path.insert(0, str(ROOT))
    import odoo
    from odoo import SUPERUSER_ID, api
    from odoo.modules.neutralize import neutralize_database
    from odoo.modules.registry import Registry

    odoo.tools.config.parse_config(['-c', str(CONFIG)], setup_logging=False)
    with Registry(DEMO_DB).cursor() as cursor:
        env = api.Environment(cursor, SUPERUSER_ID, {})
        from odoo.addons.tp_demo_workspace import demo_seed

        result = demo_seed.seed(env, {login: values[login] for login in ACTOR_LOGINS})
        admin = env.ref('base.user_admin')
        admin.tz = 'Asia/Ho_Chi_Minh'
        demo_seed.set_password(admin, values['admin'])
        env['ir.config_parameter'].set_str(TOKEN_PARAM, owner['token'])
        env['ir.cron'].with_context(active_test=False).search([]).write({'active': False})
        env.flush_all()
        neutralize_database(cursor)
        counts = {
            'projects': len(result['projects']),
            'contracts': env['tp.contract'].search_count([('code', '=like', 'DEMO-%')]),
            'tasks': env['project.task'].search_count([('project_id.tp_code', '=like', 'DEMO-%')]),
            'opportunities': env['crm.lead'].search_count([('name', 'ilike', '(DEMO)')]),
            'employees': env['hr.employee'].search_count([('name', 'ilike', '(DEMO)')]),
        }
        cursor.commit()  # This bootstrap owns its registry cursor.
    return counts


def own_process():
    """The Odoo process started by this tool, or None. Raises if the PID file points at another program."""
    if not PID_FILE.exists():
        return None
    import psutil

    pid = int(PID_FILE.read_text(encoding='ascii'))
    try:
        process = psutil.Process(pid)
        args = process.cmdline()
    except psutil.NoSuchProcess:
        PID_FILE.unlink(missing_ok=True)
        return None
    if str(ROOT / 'odoo-bin') not in args or str(CONFIG) not in args:
        raise RuntimeError('The saved demo PID belongs to another process. Refusing to manage it.')
    return process


def start_server():
    import requests

    if own_process():
        print(f'Demo already running: http://127.0.0.1:{HTTP_PORT}/odoo')
        return
    if dev.is_listening(HTTP_PORT):
        raise RuntimeError(f'Port {HTTP_PORT} is occupied by a process this tool did not start. Refusing to start.')
    with (BASE / 'logs' / 'odoo.log').open('ab') as output:
        process = subprocess.Popen([str(arg) for arg in odoo_args()], cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    PID_FILE.write_text(str(process.pid), encoding='ascii')
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if process.poll() is not None:
            PID_FILE.unlink(missing_ok=True)
            raise RuntimeError('Odoo stopped during startup. Inspect .local/ui-demo-001/logs/odoo.log.')
        if dev.is_listening(HTTP_PORT):
            try:
                response = requests.get(f'http://127.0.0.1:{HTTP_PORT}/web/login', timeout=5)
                if response.status_code == 200:
                    print(f'Demo: http://127.0.0.1:{HTTP_PORT}/odoo (PID {process.pid})')
                    return
            except requests.RequestException:
                pass
        time.sleep(0.5)
    raise RuntimeError('Demo startup timed out. Inspect .local/ui-demo-001/logs/odoo.log.')


def stop_server():
    import psutil

    process = own_process()
    if process is None:
        print('No demo Odoo process started by this tool is running.')
        return
    children = process.children(recursive=True)
    for child in children:
        try:
            child.terminate()
        except psutil.NoSuchProcess:
            pass
    process.terminate()
    _, remaining = psutil.wait_procs([process, *children], timeout=15)
    if remaining:
        raise RuntimeError('The demo Odoo process did not stop in time.')
    PID_FILE.unlink(missing_ok=True)
    print('Demo Odoo stopped. PostgreSQL is shared with the dev runtime and stays as it is.')


def status():
    owner = read_owner()
    try:
        process = own_process()
    except RuntimeError as error:
        process, problem = None, str(error)
    else:
        problem = ''
    return {
        'url': f'http://127.0.0.1:{HTTP_PORT}/odoo',
        'database': DEMO_DB,
        'owner_recorded': owner is not None,
        'odoo_pid': process.pid if process else None,
        'odoo_listening': dev.is_listening(HTTP_PORT),
        'port_owned': bool(process) or not dev.is_listening(HTTP_PORT),
        'postgres_listening': dev.is_listening(dev.PG_PORT),
        'credentials_file': str(CREDENTIALS.relative_to(ROOT)) if CREDENTIALS.exists() else None,
        'problem': problem,
    }


def prepare_runtime(name):
    owner = ensure_owner()
    values = credentials()
    pg_values = dev.secret_config()
    dev.ensure_postgres(dev.pg_bin(), pg_values)
    if not check_ownership(pg_values, owner, name):
        create_database(pg_values, owner, name)
    write_config(pg_values, values)
    return owner, values, pg_values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'seed', 'start', 'status', 'stop', 'test'])
    args = parser.parse_args()
    if args.action == 'status':
        print(json.dumps(status(), indent=2))
        return
    if args.action == 'stop':
        read_owner()
        stop_server()
        return
    if args.action == 'test':
        _, _, pg_values = prepare_runtime(TEST_DB)
        install(pg_values, TEST_DB, test=True)
        print(f'PASS: tp_demo_workspace tests on {TEST_DB}. Log: .local/ui-demo-001/logs/test.log')
        return
    owner, values, pg_values = prepare_runtime(DEMO_DB)
    if args.action in ('prepare', 'seed'):
        if dev.is_listening(HTTP_PORT):
            raise RuntimeError('Stop the demo Odoo before prepare/seed to avoid a concurrent schema change.')
        if args.action == 'prepare':
            install(pg_values, DEMO_DB)
        elif not installed(pg_values, DEMO_DB):
            raise RuntimeError('Run prepare before seed.')
        counts = seed(owner, values)
        print(f'Demo database {DEMO_DB} is ready: {json.dumps(counts)}. Credentials: .local/ui-demo-001/credentials.json')
    elif args.action == 'start':
        if not installed(pg_values, DEMO_DB):
            raise RuntimeError('Run prepare before start.')
        start_server()


if __name__ == '__main__':
    main()
