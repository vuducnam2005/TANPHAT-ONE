"""Manage only the isolated PostgreSQL/Odoo development runtime in .local/."""
# CLI output and deferred bootstrap imports are intentional.
# ruff: noqa: T201, PLC0415, EM101
import argparse
import configparser
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.local'
PGDATA = LOCAL / 'postgres' / 'data'
CONFIG = LOCAL / 'odoo.conf'
MODULES = 'tp_core,tp_organization,tp_project,tp_contract,tp_api,tp_planning_api'
DEV_DB = 'tp_tanphat_dev'
TEST_DB = 'tp_tanphat_test'
PG_PORT = 55432
HTTP_PORT = 18069


def run(args, **kwargs):
    return subprocess.run([str(arg) for arg in args], cwd=ROOT, check=True, **kwargs)


def pg_bin(explicit=None):
    if explicit:
        result = Path(explicit).resolve()
    elif (LOCAL / 'runtime-owner.json').exists():
        result = Path(json.loads((LOCAL / 'runtime-owner.json').read_text(encoding='utf-8'))['pg_bin'])
    else:
        candidates = [Path(f'C:/Program Files/PostgreSQL/{version}/bin') for version in (18, 17, 16)]
        result = next((path for path in candidates if (path / 'initdb.exe').exists()), None)
    if not result or not (result / 'pg_ctl.exe').exists():
        raise RuntimeError('Provide --pg-bin pointing to PostgreSQL 16+ bin on Windows.')
    return result


def secret_config():
    LOCAL.mkdir(exist_ok=True)
    path = LOCAL / 'dev-secrets.json'
    if not path.exists():
        if (PGDATA / 'PG_VERSION').exists():
            raise RuntimeError('The existing runtime is missing credentials. Restore .local/dev-secrets.json first.')
        values = {key: secrets.token_urlsafe(24) for key in ('pg_admin', 'pg_app', 'db_manager', 'admin', 'planner')}
        path.write_text(json.dumps(values, indent=2) + '\n', encoding='utf-8')
    return json.loads(path.read_text(encoding='utf-8'))


def is_listening(port):
    with socket.socket() as connection:
        return connection.connect_ex(('127.0.0.1', port)) == 0


def ensure_postgres(bin_path, values):
    marker = LOCAL / 'runtime-owner.json'
    if marker.exists():
        if json.loads(marker.read_text(encoding='utf-8'))['workspace'] != str(ROOT):
            raise RuntimeError('The local runtime belongs to another workspace. Refusing to manage it.')
    elif PGDATA.exists():
        raise RuntimeError('An unrecognized PostgreSQL directory already exists. Refusing to modify it.')
    else:
        marker.write_text(json.dumps({'workspace': str(ROOT), 'pg_bin': str(bin_path)}, indent=2), encoding='utf-8')
    (LOCAL / 'logs').mkdir(exist_ok=True)
    if not (PGDATA / 'PG_VERSION').exists():
        PGDATA.parent.mkdir(exist_ok=True)
        password_file = LOCAL / 'initdb-password.tmp'
        password_file.write_text(values['pg_admin'], encoding='utf-8')
        try:
            run([bin_path / 'initdb.exe', '-D', PGDATA, '-U', 'tp_dev_admin',
                 '--encoding=UTF8', '--locale=C', '--auth=scram-sha-256', f'--pwfile={password_file}'])
        finally:
            password_file.unlink(missing_ok=True)
    status = subprocess.run([str(bin_path / 'pg_ctl.exe'), 'status', '-D', str(PGDATA)], capture_output=True, check=False)
    if status.returncode != 0:
        if is_listening(PG_PORT):
            raise RuntimeError(f'Port {PG_PORT} is occupied by another process.')
        with (LOCAL / 'logs' / 'pg_ctl.log').open('ab') as output:
            run([bin_path / 'pg_ctl.exe', 'start', '-D', PGDATA, '-l', LOCAL / 'logs' / 'postgres.log',
                 '-o', f'-p {PG_PORT} -h 127.0.0.1', '-w', '-t', '30'],
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)


def ensure_databases(values):
    import psycopg2
    from psycopg2 import sql

    with closing(psycopg2.connect(host='127.0.0.1', port=PG_PORT, user='tp_dev_admin',
                                password=values['pg_admin'], dbname='postgres')) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'tp_odoo'")
            if not cursor.fetchone():
                cursor.execute('CREATE ROLE tp_odoo LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %s', (values['pg_app'],))
            for name in (DEV_DB, TEST_DB):
                cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', (name,))
                if not cursor.fetchone():
                    cursor.execute(sql.SQL("CREATE DATABASE {} OWNER tp_odoo TEMPLATE template0 ENCODING 'UTF8'").format(sql.Identifier(name)))


def write_config(values):
    config = configparser.ConfigParser(interpolation=None)
    config['options'] = {
        'addons_path': ','.join(str(ROOT / path) for path in ('addons', 'custom_addons')),
        'data_dir': str(LOCAL / 'odoo'),
        'db_host': '127.0.0.1', 'db_port': str(PG_PORT), 'db_user': 'tp_odoo', 'db_password': values['pg_app'],
        'db_name': DEV_DB, 'dbfilter': '^tp_tanphat_dev$', 'list_db': 'False',
        'admin_passwd': values['db_manager'],
        'http_interface': '127.0.0.1', 'http_port': str(HTTP_PORT),
        'workers': '0', 'max_cron_threads': '0', 'proxy_mode': 'False',
        'log_level': 'info',
    }
    with CONFIG.open('w', encoding='utf-8') as output:
        config.write(output)


def odoo_args(*args):
    return [sys.executable, ROOT / 'odoo-bin', '-c', CONFIG, *args]


def initialized(dbname, values):
    import psycopg2

    with psycopg2.connect(host='127.0.0.1', port=PG_PORT, user='tp_odoo', password=values['pg_app'], dbname=dbname) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.ir_module_module') IS NOT NULL")
            return cursor.fetchone()[0]


def install(dbname, values, *, test=False):
    flag = '-u' if initialized(dbname, values) else '-i'
    args = odoo_args('-d', dbname, '--db-filter', f'^{dbname}$', flag, MODULES, '--without-demo=True', '--stop-after-init')
    if test:
        if is_listening(18079):
            raise RuntimeError('Test HTTP port 18079 is already occupied.')
        args += ['--test-enable', '--test-tags', '/tp_project,/tp_contract,/tp_planning_api', '--http-port', '18079']
    else:
        args += ['--no-http']
    run(args)


def seed_dev(values):
    sys.path.insert(0, str(ROOT))
    import odoo
    from odoo import SUPERUSER_ID, Command, api
    from odoo.modules.registry import Registry

    odoo.tools.config.parse_config(['-c', str(CONFIG)], setup_logging=True)
    with Registry(DEV_DB).cursor() as cursor:
        env = api.Environment(cursor, SUPERUSER_ID, {})

        def seeded(model, key, data):
            xmlid = f'tp_core.dev_{key}'
            record = env.ref(xmlid, raise_if_not_found=False)
            if record:
                return record
            record = env[model].create(data)
            env['ir.model.data'].create({'module': 'tp_core', 'name': f'dev_{key}', 'model': model, 'res_id': record.id, 'noupdate': True})
            return record

        marker = env.ref('tp_core.dev_project', raise_if_not_found=False)
        if not marker:
            company = env.company
            currency = env.ref('base.VND')
            currency.active = True
            company.write({'name': 'Tan Phat Development', 'currency_id': currency.id, 'country_id': env.ref('base.vn').id})
            department = seeded('hr.department', 'department', {'name': 'Planning and Business - DEV', 'tp_code': 'KHKD', 'company_id': company.id})
            planner = seeded('res.users', 'planner', {
                'name': 'Planning Reader - DEV', 'login': 'planner.dev', 'password': values['planner'],
                'company_id': company.id, 'company_ids': [Command.set(company.ids)],
                'group_ids': [Command.set([env.ref('tp_core.group_user').id])], 'tz': 'Asia/Ho_Chi_Minh',
            })
            project = seeded('project.project', 'project', {
                'name': 'Development Project - Assigned', 'tp_managed': True, 'tp_code': 'DEV-001',
                'company_id': company.id, 'tp_department_id': department.id,
            })
            seeded('project.project', 'project_hidden', {
                'name': 'Development Project - Unassigned', 'tp_managed': True, 'tp_code': 'DEV-002', 'company_id': company.id,
            })
            seeded('tp.project.assignment', 'assignment', {'project_id': project.id, 'user_id': planner.id})
        if not env.ref('tp_core.dev_contract_a', raise_if_not_found=False):
            seed_dev_contracts(env, seeded)
        env.ref('base.user_admin').write({'password': values['admin'], 'tz': 'Asia/Ho_Chi_Minh'})
        planner = env.ref('tp_core.dev_planner', raise_if_not_found=False)
        if planner:
            planner.write({'password': values['planner'], 'tz': 'Asia/Ho_Chi_Minh'})
        cursor.commit()  # This bootstrap owns its registry cursor.


def seed_dev_contracts(env, seeded):
    """Synthetic TP Contracts fixtures (amounts in VND); never real business records."""
    import hashlib

    from odoo.tools import BinaryBytes

    project = env.ref('tp_core.dev_project')
    hidden = env.ref('tp_core.dev_project_hidden')
    admin = env.ref('base.user_admin')
    owner = seeded('res.partner', 'contract_owner', {'name': 'Chủ đầu tư giả lập - DEV', 'is_company': True})
    # Development only: lets the admin account exercise the financial path on DEV-001.
    seeded('tp.project.grant', 'grant_admin', {
        'project_id': project.id, 'user_id': admin.id, 'capability': 'financial_read',
        'reason': 'Development fixture: synthetic financial read on DEV-001 only.',
    })

    def revision(contract, sequence, *, previous=None, signed=None, effective=None):
        vals = {
            'contract_id': contract.id, 'sequence': sequence, 'revision_kind': 'amendment' if previous else 'original',
            'name': f'Phụ lục {sequence:02d}' if previous else 'Hợp đồng gốc', 'review_state': 'review_complete',
            'previous_revision_id': previous.id if previous else False,
        }
        if signed:
            vals.update(signature_status='signed_recorded', signed_date=signed)
        if effective:
            vals.update(effectivity_status='effective_recorded', effective_date=effective)
        return env['tp.contract.revision'].create(vals)

    def line(rev, key, name, change_kind, amount, previous=None):
        record = env['tp.contract.line'].create({
            'revision_id': rev.id, 'scope_key': key, 'name': name, 'change_kind': change_kind,
            'previous_line_id': previous.id if previous else False,
        })
        env['tp.contract.line.amount'].create({
            'line_id': record.id, 'amount_state': 'unconfirmed' if amount is None else 'confirmed', 'amount': amount or 0,
        })
        return record

    def approval(rev, amount, **vals):
        reference = env['tp.approval.reference'].create({
            'revision_id': rev.id, 'decision': 'approved', 'decided_by_name': 'Người duyệt BASE (giả lập)',
            'evidence_sha256': hashlib.sha256(f'synthetic evidence {rev.id}'.encode()).hexdigest(), **vals,
        })
        env['tp.approval.reference.amount'].create({'reference_id': reference.id, 'amount_state': 'confirmed', 'amount': amount})

    # C1: the amendment replaces the original snapshot from 2026-11-01 (100 -> 110 million, never 210).
    contract_a = seeded('tp.contract', 'contract_a', {
        'code': 'HD-DEV-001', 'name': 'Hợp đồng tư vấn khảo sát thiết kế (giả lập)', 'project_id': project.id,
        'partner_id': owner.id, 'contract_type': 'owner',
    })
    original = revision(contract_a, 0, signed='2026-01-05', effective='2026-01-10')
    survey = line(original, 'KS', 'Khảo sát địa hình (giả lập)', 'original', 60_000_000)
    design = line(original, 'TK', 'Thiết kế cơ sở (giả lập)', 'original', 40_000_000)
    amendment = revision(contract_a, 1, previous=original, signed='2026-10-10', effective='2026-11-01')
    line(amendment, 'KS', 'Khảo sát địa hình (giả lập)', 'amended', 70_000_000, survey)
    line(amendment, 'TK', 'Thiết kế cơ sở (giả lập)', 'unchanged', 40_000_000, design)
    approval(amendment, 110_000_000, reference_kind='manual', provenance='Ảnh chụp BASE giả lập',
             decided_at='2026-10-09 03:00:00')
    contract_a.lifecycle_state = 'effective'
    env['tp.contract.document'].create([
        {'contract_id': contract_a.id, 'revision_id': amendment.id, 'name': 'Phụ lục 01 đã ký (giả lập)',
         'document_kind': 'amendment', 'file': BinaryBytes(b'Synthetic signed amendment - DEV'), 'file_name': 'phu-luc-01-gia-lap.txt'},
        {'contract_id': contract_a.id, 'name': 'Đề cương kỹ thuật (giả lập)', 'document_kind': 'technical_scope',
         'confidentiality': 'general', 'file': BinaryBytes(b'Synthetic technical scope - DEV'), 'file_name': 'de-cuong-gia-lap.txt'},
    ])

    # BASE approved and verified, but neither signed nor effective; one amount is still unconfirmed.
    contract_c = seeded('tp.contract', 'contract_c', {
        'code': 'HD-DEV-003', 'name': 'Hợp đồng thí nghiệm vật liệu (giả lập)', 'project_id': project.id,
        'contract_type': 'subcontractor',
    })
    pending = revision(contract_c, 0)
    line(pending, 'TN', 'Thí nghiệm vật liệu (giả lập)', 'original', 45_000_000)
    line(pending, 'DP', 'Hạng mục chờ báo giá (giả lập)', 'original', None)
    approval(pending, 45_000_000, reference_kind='base_id', base_reference='BASE-DEV-0003',
             source_url='https://base.example.invalid/approvals/BASE-DEV-0003', decided_at='2026-10-20 02:00:00',
             verification_state='verified', verified_by_id=admin.id, verified_at='2026-10-21 02:00:00',
             authority_status='confirmed', authority_source='Văn bản ủy quyền giả lập - DEV')

    # Outside the planner's scope; admin sees the metadata but has no financial grant here.
    contract_b = seeded('tp.contract', 'contract_b', {
        'code': 'HD-DEV-002', 'name': 'Hợp đồng giám sát (giả lập)', 'project_id': hidden.id, 'contract_type': 'owner',
    })
    hidden_revision = revision(contract_b, 0, signed='2026-02-01', effective='2026-02-01')
    line(hidden_revision, 'GS', 'Giám sát thi công (giả lập)', 'original', 25_000_000)
    contract_b.lifecycle_state = 'effective'


def smoke(values):
    import requests

    base_url = f'http://127.0.0.1:{HTTP_PORT}'
    response = requests.get(base_url + '/api/v1/me', timeout=15, allow_redirects=False)
    assert response.status_code == 401, f'Unauthenticated status: {response.status_code}'
    with requests.Session() as session:
        response = session.post(base_url + '/web/session/authenticate', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'db': DEV_DB, 'login': 'planner.dev', 'password': values['planner']},
        }, timeout=30)
        assert response.status_code == 200 and response.json().get('result', {}).get('uid'), 'Development login failed.'
        projects = session.get(base_url + '/api/v1/projects', timeout=15)
        assert projects.status_code == 200, f'Projects status: {projects.status_code}'
        data = projects.json()['data']
        assert [row['code'] for row in data] == ['DEV-001'], 'Unexpected project scope for dev reader.'
        assert session.get(base_url + f"/api/v1/projects/{data[0]['id']}", timeout=15).status_code == 200
        contracts = session.get(base_url + '/api/v1/contracts', timeout=15).json()['data']
        assert [row['code'] for row in contracts] == ['HD-DEV-001', 'HD-DEV-003'], 'Unexpected contract scope for dev reader.'
        detail = session.get(base_url + f"/api/v1/contracts/{contracts[0]['id']}", timeout=15)
        assert detail.status_code == 200 and not detail.json()['data']['permissions']['financial_read']
        assert '"total"' not in detail.text and '"approved_amount"' not in detail.text, 'Dev reader received amounts.'
        kinds = {doc['confidentiality'] for doc in detail.json()['data']['documents']}
        assert kinds == {'general'}, 'Dev reader can list financial documents.'
    with requests.Session() as session:
        response = session.post(base_url + '/web/session/authenticate', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'db': DEV_DB, 'login': 'admin', 'password': values['admin']},
        }, timeout=30)
        assert response.json().get('result', {}).get('uid'), 'Development admin login failed.'
        contracts = {row['code']: row['id'] for row in session.get(base_url + '/api/v1/contracts', timeout=15).json()['data']}
        url = f"{base_url}/api/v1/contracts/{contracts['HD-DEV-001']}"
        totals = [session.get(url, params={'as_of': as_of}, timeout=15).json()['data']['effective_snapshot']['total']['value']
                  for as_of in ('2026-10-31', '2026-11-01')]
        assert totals == ['100000000', '110000000'], f'Unexpected C1 totals: {totals}'
        hidden = session.get(f"{base_url}/api/v1/contracts/{contracts['HD-DEV-002']}", timeout=15)
        assert not hidden.json()['data']['permissions']['financial_read'] and '"total"' not in hidden.text
    print('PASS: native session login, JSON 401, scoped project list/detail, contract scope and financial grant.')


def start_server():
    import requests

    if is_listening(HTTP_PORT):
        raise RuntimeError(f'Port {HTTP_PORT} is occupied. Use status to inspect it.')
    with (LOCAL / 'logs' / 'odoo.log').open('ab') as output:
        process = subprocess.Popen([str(arg) for arg in odoo_args()], cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    (LOCAL / 'odoo.pid').write_text(str(process.pid), encoding='ascii')
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError('Odoo stopped during startup. Inspect .local/logs/odoo.log.')
        if is_listening(HTTP_PORT):
            try:
                response = requests.get(f'http://127.0.0.1:{HTTP_PORT}/api/v1/me', timeout=2, allow_redirects=False)
                if response.status_code == 401 and response.headers.get('Content-Type', '').startswith('application/json'):
                    print(f'Odoo dev: http://127.0.0.1:{HTTP_PORT}/odoo (PID {process.pid})')
                    return
            except requests.RequestException:
                pass
        time.sleep(0.5)
    raise RuntimeError('Odoo startup timed out. Inspect .local/logs/odoo.log.')


def stop_server():
    pid_file = LOCAL / 'odoo.pid'
    if not pid_file.exists():
        return
    import psutil

    pid = int(pid_file.read_text(encoding='ascii'))
    try:
        process = psutil.Process(pid)
        args = process.cmdline()
        if str(ROOT / 'odoo-bin') not in args or str(CONFIG) not in args:
            raise RuntimeError('The saved Odoo PID belongs to another process. Refusing to stop it.')
        children = process.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        process.terminate()
        _, remaining = psutil.wait_procs([process, *children], timeout=15)
        if remaining:
            raise RuntimeError('An Odoo development process did not stop in time.')
    except psutil.NoSuchProcess:
        pass
    pid_file.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup', 'start', 'stop', 'status', 'test', 'upgrade', 'smoke', 'lock'])
    parser.add_argument('--pg-bin')
    args = parser.parse_args()
    if args.action == 'lock':
        result = run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True)
        (ROOT / 'ops' / 'requirements-windows-py312.lock.txt').write_text(result.stdout, encoding='utf-8')
        revision = run(['git', 'rev-parse', 'HEAD:odoo'], capture_output=True, text=True).stdout.strip()
        upstream = run(['git', 'rev-parse', 'f03f160f'], capture_output=True, text=True).stdout.strip()
        postgres = run([pg_bin(args.pg_bin) / 'postgres.exe', '--version'], capture_output=True, text=True).stdout.strip()
        (ROOT / 'ops' / 'runtime-baseline.json').write_text(json.dumps({'python': sys.version.split()[0], 'postgres': postgres, 'odoo_series': '20.0', 'upstream_commit': upstream, 'odoo_tree': revision}, indent=2) + '\n', encoding='utf-8')
        return
    if args.action == 'status':
        print(json.dumps({'odoo_url': f'http://127.0.0.1:{HTTP_PORT}/odoo', 'odoo_listening': is_listening(HTTP_PORT), 'postgres_listening': is_listening(PG_PORT), 'database': DEV_DB, 'config_exists': CONFIG.exists()}, indent=2))
        return
    if args.action == 'stop':
        stop_server()
        if PGDATA.exists():
            marker = json.loads((LOCAL / 'runtime-owner.json').read_text(encoding='utf-8'))
            if marker['workspace'] != str(ROOT):
                raise RuntimeError('Runtime ownership mismatch.')
            run([Path(marker['pg_bin']) / 'pg_ctl.exe', 'stop', '-D', PGDATA, '-m', 'fast', '-w'])
        return
    if args.action == 'smoke':
        smoke(secret_config())
        return
    values = secret_config()
    ensure_postgres(pg_bin(args.pg_bin), values)
    ensure_databases(values)
    write_config(values)
    if args.action in ('setup', 'upgrade'):
        if is_listening(HTTP_PORT):
            raise RuntimeError('Stop Odoo before setup/upgrade to avoid a concurrent schema change.')
        install(DEV_DB, values)
        seed_dev(values)
        print('Development database and foundation addons are ready. Credentials: .local/dev-secrets.json')
    elif args.action == 'test':
        install(TEST_DB, values, test=True)
    elif args.action == 'start':
        if not initialized(DEV_DB, values):
            raise RuntimeError('Run setup before start.')
        start_server()


if __name__ == '__main__':
    main()
