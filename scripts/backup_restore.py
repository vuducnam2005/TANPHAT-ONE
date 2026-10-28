"""Back up the owned Windows dev runtime and rehearse in an isolated cluster.

Never restores into dev/test; private backup payloads stay under .local/ops-001.
"""
# Operator output, deferred dev imports, and concise validation messages are intentional.
# ruff: noqa: T201, PLC0415, EM101
import argparse
import configparser
import csv
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tarfile
import time
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import psycopg2
import requests
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/ops-001'
SOURCE_DB = 'tp_tanphat_dev'
RESTORE_DB = 'tp_tanphat_restore'
PG_PORT = 55442
HTTP_PORT = 18089
RUNTIME_PATHS = ('odoo', 'addons', 'custom_addons', 'frontend', 'contracts', 'ops/config',
                 'ops/runtime-baseline.json', 'ops/requirements-windows-py312.lock.txt',
                 'scripts/dev.py', 'scripts/dev.ps1', 'requirements.txt', 'odoo-bin')
BLOB_NAME = re.compile(r'^[0-9a-f]{2}/[0-9a-f]{40}$')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def beneath(root, name):
    """Validate even on Windows: reject absolute paths, traversal, ADS and links."""
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name,
            'Invalid relative path.')
    require(not name.startswith('/') and '..' not in name.split('/'), 'Unsafe relative path.')
    result = (root / name).resolve()
    require(result.is_relative_to(root.resolve()) and result != root.resolve(), 'Path escapes its root.')
    return result


def digest(path, algorithm='sha256'):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run(args, *, log=None, **kwargs):
    args = [str(value) for value in args]
    if log:
        with log.open('ab') as output:
            result = subprocess.run(args, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                    check=False, **kwargs)
    else:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, check=False, **kwargs)
    require(result.returncode == 0, f'{Path(args[0]).name} failed; inspect the private operation log.')
    return result


def private_directory(path):
    require(path.resolve().is_relative_to(BASE.resolve()), 'Private directory must be inside ops-001.')
    path.mkdir(parents=True, exist_ok=False)
    if os.name == 'nt':
        identity = run(['whoami', '/user', '/fo', 'csv', '/nh']).stdout.decode('utf-8-sig')
        sid = next(csv.reader(io.StringIO(identity.strip())))[1]
        run(['icacls', path, '/inheritance:r', '/grant:r', f'*{sid}:(OI)(CI)F',
             '*S-1-5-18:(OI)(CI)F', '*S-1-5-32-544:(OI)(CI)F'])
    else:
        path.chmod(0o700)


def new_operation(kind):
    target = BASE / kind / datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')
    private_directory(target)
    return target


def connect(dbname, user, password, port):
    return psycopg2.connect(host='127.0.0.1', port=port, user=user, password=password,
                            dbname=dbname, connect_timeout=10, application_name='tp_ops001')


def pg_environment(password):
    # Only the child process receives the password. Do not change the shell/global environment.
    env = {key: value for key, value in os.environ.items() if not key.startswith('PG')}
    env['PGPASSWORD'] = password
    return env


def table_inventory(connection):
    """Fingerprints of complete public rowsets, without logging row contents."""
    result = {}
    with connection.cursor() as cursor:
        cursor.execute("SET TIME ZONE 'UTC'")
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        tables = [row[0] for row in cursor.fetchall()]
        for name in tables:
            cursor.execute(sql.SQL("SELECT count(*), md5(COALESCE(string_agg(h, '' ORDER BY h), '')) "
                                   "FROM (SELECT md5(row_to_json(t)::text) h FROM public.{} t) rows").format(sql.Identifier(name)))
            count, fingerprint = cursor.fetchone()
            result[name] = {'rows': count, 'rowset_md5': fingerprint}
    return result


def attachment_inventory(connection, filestore):
    with connection.cursor() as cursor:
        cursor.execute('SELECT id, store_fname, checksum, file_size FROM ir_attachment '
                       'WHERE store_fname IS NOT NULL ORDER BY id')
        rows = cursor.fetchall()
    result = []
    for identifier, name, checksum, size in rows:
        require(BLOB_NAME.fullmatch(name), 'Unexpected attachment storage path.')
        path = beneath(filestore, name)
        require(path.is_file(), f'Missing attachment blob for ID {identifier}.')
        require(path.stat().st_size == size and digest(path, 'sha1') == checksum,
                f'Attachment checksum/size mismatch for ID {identifier}.')
        result.append({'id': identifier, 'store_fname': name, 'sha1': checksum, 'bytes': size})
    return result


def verify_backup(folder):
    require(folder.resolve().is_relative_to((BASE / 'backups').resolve()), 'Use a backup inside ops-001/backups.')
    manifest = read_json(folder / 'manifest.json')
    require(manifest.get('schema_version') == 1 and manifest.get('complete') is True, 'Backup is incomplete or unsupported.')
    require(manifest.get('source_database') == SOURCE_DB, 'Unexpected source database.')
    hashes = manifest['sha256']
    required = {'database.dump', 'source.tar.gz', 'snapshot.json', 'private/odoo.conf', 'private/dev-secrets.json'}
    require(required <= hashes.keys(), 'Backup payloads are missing from manifest.')
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()} - {'manifest.json'}
    require(actual == hashes.keys(), 'Unexpected/missing backup files.')
    for name, expected in hashes.items():
        path = beneath(folder, name)
        require(path.is_file() and digest(path) == expected, f'Backup checksum mismatch: {name}')
    return manifest


def extract_source(archive, target):
    with tarfile.open(archive, 'r:gz') as source:
        for member in source.getmembers():
            name = member.name.rstrip('/')
            if name:
                beneath(target, name)
            require(member.isfile() or member.isdir(), 'Source archive contains a link or special file.')
        source.extractall(target, filter='data')


def authenticate(base, database, login, password):
    session = requests.Session()
    response = session.post(base + '/web/session/authenticate', json={
        'jsonrpc': '2.0', 'method': 'call', 'id': 1,
        'params': {'db': database, 'login': login, 'password': password},
    }, timeout=45)
    require(response.status_code == 200 and response.json().get('result', {}).get('uid'), 'Native session login failed.')
    return session


def project_list(session, base):
    response = session.get(base + '/api/v1/projects?limit=100', timeout=30)
    require(response.status_code == 200, 'Project list failed.')
    require(not response.json()['meta']['pagination']['has_more'], 'Rehearsal currently supports at most 100 dev projects.')
    return response.json()['data']


def expected_scopes(values):
    base = 'http://127.0.0.1:18069'
    result = {}
    for key, login in (('planner', 'planner.dev'), ('admin', 'admin')):
        with authenticate(base, SOURCE_DB, login, values[key]) as session:
            result[key] = project_list(session, base)
    require(result['planner'] and {p['id'] for p in result['admin']} - {p['id'] for p in result['planner']},
            'Dev fixture needs an assigned project and another project hidden from reader.')
    return result


def source_preflight():
    import dev
    marker = read_json(ROOT / '.local/runtime-owner.json')
    require(Path(marker['workspace']).resolve() == ROOT, 'Runtime ownership mismatch.')
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / '.local/odoo.conf', encoding='utf-8-sig')
    options = config['options']
    require(options['db_name'] == SOURCE_DB and options['db_host'] == '127.0.0.1'
            and options['db_port'] == '55432' and options['http_port'] == '18069'
            and Path(options['data_dir']).resolve() == ROOT / '.local/odoo', 'Unexpected dev configuration.')
    require(dev.is_listening(18069) and dev.is_listening(55432), 'Start the existing dev runtime before backup.')
    values = read_json(ROOT / '.local/dev-secrets.json')
    with closing(connect(SOURCE_DB, 'tp_dev_admin', values['pg_admin'], 55432)) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SHOW data_directory')
            require(Path(cursor.fetchone()[0]).resolve() == ROOT / '.local/postgres/data', 'Connected to another cluster.')
    run(['git', 'diff', '--exit-code', 'HEAD', '--', *RUNTIME_PATHS])
    untracked = run(['git', 'ls-files', '--others', '--exclude-standard', '--', *RUNTIME_PATHS]).stdout
    require(not untracked.strip(), 'Commit runtime source additions before taking a committed-source backup.')
    require(run(['git', 'check-ignore', '.local/ops-001/probe']).stdout.strip(), 'Backup root must be ignored by Git.')
    return dev, Path(marker['pg_bin']), values


def backup():
    dev, binaries, values = source_preflight()
    scopes = expected_scopes(values)
    folder = new_operation('backups')
    log = folder.parent / f'{folder.name}.log'
    (folder / 'private').mkdir()
    for name in ('odoo.conf', 'dev-secrets.json'):
        shutil.copy2(ROOT / '.local' / name, folder / 'private' / name)
    revision = run(['git', 'rev-parse', 'HEAD']).stdout.decode().strip()
    run(['git', 'archive', '--format=tar.gz', '--output', folder / 'source.tar.gz', revision], log=log)
    pause_started = time.monotonic()
    try:
        dev.stop_server()  # Owns and validates its exact PID/config; PostgreSQL remains running.
        require(not dev.is_listening(18069), 'Dev HTTP listener did not stop.')
        with closing(connect(SOURCE_DB, 'tp_dev_admin', values['pg_admin'], 55432)) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT count(*) FROM pg_stat_activity WHERE datname=%s AND pid<>pg_backend_pid()', (SOURCE_DB,))
                require(cursor.fetchone()[0] == 0, 'Other clients still use dev; cannot freeze DB/filestore consistently.')
            inventory = table_inventory(connection)
            source_filestore = ROOT / '.local/odoo/filestore' / SOURCE_DB
            attachments = attachment_inventory(connection, source_filestore)
        run([binaries / 'pg_dump.exe', '-h', '127.0.0.1', '-p', '55432', '-U', 'tp_odoo', '-d', SOURCE_DB,
             '--format=custom', '--no-owner', '--no-privileges', '--file', folder / 'database.dump'],
            log=log, env=pg_environment(values['pg_app']))
        destination = folder / 'filestore'
        destination.mkdir()
        # Odoo's upload/checklist/.__gc files are transient; back up canonical content blobs.
        for path in source_filestore.rglob('*'):
            if path.is_file() and BLOB_NAME.fullmatch(path.relative_to(source_filestore).as_posix()):
                relative = path.relative_to(source_filestore).as_posix()
                target = beneath(destination, relative)
                target.parent.mkdir(exist_ok=True)
                shutil.copy2(path, target)
        write_json(folder / 'snapshot.json', {'tables': inventory, 'attachments': attachments, 'scopes': scopes})
    finally:
        if not dev.is_listening(18069):
            dev.start_server()  # No setup/upgrade/seed/config/password changes.
    interruption = round(time.monotonic() - pause_started, 2)
    manifest = {
        'schema_version': 1, 'complete': True, 'source_database': SOURCE_DB,
        'created_at': datetime.now(UTC).isoformat(), 'source_revision': revision,
        'source_method': 'git archive of committed runtime source; uncommitted tooling is not included',
        'python': sys.version.split()[0],
        'postgres': run([binaries / 'pg_dump.exe', '--version']).stdout.decode().strip(),
        'dev_pause_seconds': interruption,
        'sha256': {p.relative_to(folder).as_posix(): digest(p) for p in sorted(folder.rglob('*')) if p.is_file()},
    }
    write_json(folder / 'manifest.json', manifest)
    verify_backup(folder)
    print(f'BACKUP PASS: {folder}')
    print(f'{len(inventory)} tables; {len(attachments)} file attachment references; dev pause {interruption}s.')
    return folder


def restore_config(run_root, source, values):
    config = configparser.ConfigParser(interpolation=None)
    config['options'] = {
        'addons_path': ','.join(str(source / name) for name in ('addons', 'custom_addons')),
        'data_dir': str(run_root / 'runtime'), 'db_host': '127.0.0.1', 'db_port': str(PG_PORT),
        'db_user': 'tp_odoo', 'db_password': values['pg_app'], 'db_name': RESTORE_DB,
        'dbfilter': f'^{RESTORE_DB}$', 'list_db': 'False', 'admin_passwd': values['db_manager'],
        'http_interface': '127.0.0.1', 'http_port': str(HTTP_PORT), 'workers': '0',
        'max_cron_threads': '0', 'proxy_mode': 'False', 'log_level': 'info',
        'smtp_server': '127.0.0.1', 'smtp_port': '1',
    }
    path = run_root / 'restore.conf'
    with path.open('w', encoding='utf-8') as output:
        config.write(output)
    return path


def seed_restore_probes(source, config, run_root, snapshot, log):
    allowed = snapshot['scopes']['planner'][0]['id']
    hidden = next(p['id'] for p in snapshot['scopes']['admin'] if p['id'] not in {p['id'] for p in snapshot['scopes']['planner']})
    probe = (
        'import json\nfrom pathlib import Path\n'
        f'assert env.cr.dbname == {RESTORE_DB!r}\n'
        f'assert Path(odoo.tools.config["data_dir"]).resolve() == Path({str(run_root / "runtime")!r}).resolve()\n'
        'rows = []\n'
        f'for project_id in {(allowed, hidden)!r}:\n'
        '    doc = env["ir.attachment"].create({"name":"OPS-001 isolated probe.txt",'
        '"res_model":"project.project","res_id":project_id,"raw":b"OPS-001 isolated attachment probe",'
        '"mimetype":"text/plain","public":False})\n'
        '    rows.append({"id":doc.id,"project_id":project_id,"sha1":doc.checksum})\n'
        'env.cr.commit()\n'
        f'Path({str(run_root / "probes.json")!r}).write_text(json.dumps(rows), encoding="utf-8")\n'
    )
    run([sys.executable, source / 'odoo-bin', 'shell', '-c', config, '--no-http'],
        input=probe.encode(), log=log)


def restored_http_checks(snapshot, login_values, run_root):
    base = f'http://127.0.0.1:{HTTP_PORT}'
    checks = []
    require(requests.get(base + '/api/v1/me', timeout=15).status_code == 401, 'Anonymous API access was not rejected.')
    checks.append('anonymous API: 401')
    require(requests.get(base + '/web/login', timeout=30).status_code == 200, 'Native login page failed.')
    probes = read_json(run_root / 'probes.json')
    for key, login in (('planner', 'planner.dev'), ('admin', 'admin')):
        with authenticate(base, RESTORE_DB, login, login_values[key]) as session:
            require(project_list(session, base) == snapshot['scopes'][key], f'{key} project scope/DTO changed.')
            require(session.get(base + '/api/v1/me', timeout=15).status_code == 200, 'Session bootstrap failed.')
            for project in snapshot['scopes'][key]:
                response = session.get(base + f'/api/v1/projects/{project["id"]}', timeout=15)
                require(response.status_code == 200 and response.json()['data'] == project, 'Project detail changed.')
            require(session.get(base + '/api/v1/projects?unknown=1', timeout=15).status_code == 400, 'Invalid query accepted.')
            checks.append(f'{key}: login, me, exact list/detail DTO, query validation')
            if key == 'admin':
                for doc in snapshot['attachments']:
                    response = session.get(base + f'/web/content/{doc["id"]}?download=true', timeout=30)
                    require(response.status_code == 200 and len(response.content) == doc['bytes']
                            and hashlib.sha1(response.content).hexdigest() == doc['sha1'], 'Restored attachment download differs.')
                checks.append(f'admin: {len(snapshot["attachments"])} restored attachment downloads match SHA1/size')
            for index, probe in enumerate(probes):
                response = session.get(base + f'/web/content/{probe["id"]}?download=true', timeout=15)
                if key == 'admin' or index == 0:
                    require(response.status_code == 200 and hashlib.sha1(response.content).hexdigest() == probe['sha1'],
                            'Allowed attachment was not readable.')
                else:
                    require(response.status_code in (403, 404), 'Hidden project attachment was disclosed.')
                    require(session.get(base + f'/api/v1/projects/{probe["project_id"]}', timeout=15).status_code == 404,
                            'Hidden project detail was disclosed.')
            checks.append(f'{key}: project-linked private attachment scope')
    return checks


def verify_original_runtime(folder, snapshot):
    import dev
    values = read_json(ROOT / '.local/dev-secrets.json')
    with closing(connect(SOURCE_DB, 'tp_dev_admin', values['pg_admin'], 55432)) as connection:
        current = table_inventory(connection)
    for name in ('project_project', 'tp_project_assignment', 'tp_work_item', 'hr_department', 'ir_attachment'):
        require(current[name] == snapshot['tables'][name], f'Original business rowset changed: {name}')
    for name in ('odoo.conf', 'dev-secrets.json'):
        require(digest(ROOT / '.local' / name) == digest(folder / 'private' / name), 'Original configuration changed.')
    dev.smoke(values)


def finalize_report(run_root, report, folder, snapshot):
    """Never publish a passing report before cleanup AND original-runtime checks."""
    report['passed'] = False
    try:
        require(report.get('restored_checks_passed') and report.get('isolated_services_stopped'),
                'Restore checks or isolated cleanup did not pass.')
        verify_original_runtime(folder, snapshot)
        report['original_business_config_and_smoke_passed'] = True
        report['passed'] = True
    finally:
        report['finished_at'] = datetime.now(UTC).isoformat()
        write_json(run_root / 'report.json', report)


def rehearse(folder):
    import dev
    manifest = verify_backup(folder)
    require(not dev.is_listening(PG_PORT) and not dev.is_listening(HTTP_PORT), 'Rehearsal ports are already occupied.')
    binaries = dev.pg_bin()
    run_root = new_operation('rehearsals')
    log = run_root / 'operation.log'
    source = run_root / 'source'
    source.mkdir()
    print(f'RESTORE: extracting committed source into {source}', flush=True)
    extract_source(folder / 'source.tar.gz', source)
    values = {key: secrets.token_urlsafe(24) for key in ('pg_admin', 'pg_app', 'db_manager')}
    write_json(run_root / 'restore-secrets.json', values)
    config = restore_config(run_root, source, values)
    pgdata = run_root / 'postgres'
    password_file = run_root / 'initdb-password.tmp'
    password_file.write_text(values['pg_admin'], encoding='utf-8')
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    try:
        run([binaries / 'initdb.exe', '-D', pgdata, '-U', 'tp_restore_admin', '--encoding=UTF8',
             '--locale=C', '--auth=scram-sha-256', f'--pwfile={password_file}'], log=log, creationflags=flags)
    finally:
        password_file.unlink(missing_ok=True)
    started = False
    process = None
    report = {'backup': str(folder), 'source_revision': manifest['source_revision'], 'passed': False}
    try:
        run([binaries / 'pg_ctl.exe', 'start', '-D', pgdata, '-l', run_root / 'postgres.log',
             '-o', f'-p {PG_PORT} -h 127.0.0.1', '-w', '-t', '30'], log=log,
            stdin=subprocess.DEVNULL, creationflags=flags)
        started = True
        with closing(connect('postgres', 'tp_restore_admin', values['pg_admin'], PG_PORT)) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute('CREATE ROLE tp_odoo LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %s', (values['pg_app'],))
                cursor.execute(sql.SQL("CREATE DATABASE {} OWNER tp_odoo TEMPLATE template0 ENCODING 'UTF8'").format(sql.Identifier(RESTORE_DB)))
        run([binaries / 'pg_restore.exe', '-h', '127.0.0.1', '-p', PG_PORT, '-U', 'tp_odoo', '-d', RESTORE_DB,
             '--no-owner', '--no-privileges', '--exit-on-error', folder / 'database.dump'],
            env=pg_environment(values['pg_app']), log=log)
        restored_filestore = run_root / 'runtime/filestore' / RESTORE_DB
        shutil.copytree(folder / 'filestore', restored_filestore)
        snapshot = read_json(folder / 'snapshot.json')
        with closing(connect(RESTORE_DB, 'tp_odoo', values['pg_app'], PG_PORT)) as connection:
            require(table_inventory(connection) == snapshot['tables'], 'Restored table rowsets differ before neutralization.')
            require(attachment_inventory(connection, restored_filestore) == snapshot['attachments'], 'Restored filestore differs.')
        print('RESTORE: exact database rowsets and referenced filestore match; neutralizing copy.', flush=True)
        run([sys.executable, source / 'odoo-bin', 'neutralize', '-c', config], log=log)
        seed_restore_probes(source, config, run_root, snapshot, log)
        with (run_root / 'odoo.log').open('ab') as output:
            process = subprocess.Popen([sys.executable, str(source / 'odoo-bin'), '-c', str(config)],
                                       cwd=source, stdout=output, stderr=subprocess.STDOUT, creationflags=flags)
        deadline = time.monotonic() + 90
        while not dev.is_listening(HTTP_PORT):
            require(process.poll() is None and time.monotonic() < deadline, 'Restored Odoo did not start; inspect its private log.')
            time.sleep(0.5)
        report['checks'] = restored_http_checks(snapshot, read_json(folder / 'private/dev-secrets.json'), run_root)
        report.update({'restored_checks_passed': True, 'restored_tables': len(snapshot['tables']),
                       'restored_file_references': len(snapshot['attachments']),
                       'restored_from_committed_source': True, 'probe_records_only_in_restore': 2})
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=30)
        if started or (pgdata / 'postmaster.pid').is_file():
            require(pgdata.resolve().is_relative_to(run_root.resolve()) and run_root.is_relative_to(BASE.resolve()),
                    'Cannot stop a cluster outside this rehearsal.')
            status = subprocess.run([str(binaries / 'pg_ctl.exe'), 'status', '-D', str(pgdata)], capture_output=True, check=False)
            if status.returncode == 0:
                run([binaries / 'pg_ctl.exe', 'stop', '-D', pgdata, '-m', 'fast', '-w'], log=log, creationflags=flags)
        report['isolated_services_stopped'] = not dev.is_listening(PG_PORT) and not dev.is_listening(HTTP_PORT)
        report['finished_at'] = datetime.now(UTC).isoformat()
        write_json(run_root / 'report.json', report)
    finalize_report(run_root, report, folder, snapshot)
    print(f'REHEARSAL PASS: {run_root / "report.json"}')
    return run_root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('backup')
    restore = commands.add_parser('rehearse')
    restore.add_argument('backup', type=Path)
    args = parser.parse_args()
    if args.action == 'backup':
        backup()
    else:
        rehearse(args.backup.resolve())


if __name__ == '__main__':
    main()
