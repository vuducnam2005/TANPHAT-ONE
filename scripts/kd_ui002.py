"""KD-UI-002 owned clone operations (sidebar + Tổng quan). Credentials/evidence stay private.

Commands:
  prepare   consistent snapshot of running dev (DB+filestore+config+dirty source) -> exact restore clone
            on port 18289 with an isolated custom_addons copy (dev never loads untested assets).
  test      Odoo tests on the stopped clone (-u tp_kd_workspace).
  start/stop owned clone runtime only (never PostgreSQL, never another clone).
  apply     copy the tested tp_kd_workspace to main, stop ONLY the dev Odoo process, upgrade the module,
            compare business rowsets before/after, start dev again.
  rollback  restore tp_kd_workspace source from the snapshot zip and upgrade dev (code/assets/menu delta only).
"""
# ruff: noqa: T201, PLC0415, S603
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import kd_native001 as kd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/kd-ui002'
DATABASE = 'tp_tanphat_kdui002_20261106'
PORT = 18289
MODULE = 'tp_kd_workspace'
SOURCE = BASE / 'source/custom_addons'
# Business tables whose rows must stay identical across the UI upgrade.
PRESERVED = [
    'res_users', 'res_groups_users_rel', 'res_partner', 'hr_department', 'project_project', 'project_task',
    'tp_project_assignment', 'tp_project_grant', 'tp_kd_grant', 'crm_lead', 'tp_contract', 'tp_contract_revision',
    'tp_contract_line', 'tp_contract_line_amount', 'tp_contract_submission', 'tp_contract_event',
    'tp_allocation', 'tp_allocation_amount', 'tp_production', 'tp_production_amount', 'tp_acceptance',
    'tp_acceptance_amount', 'tp_payment_request', 'tp_payment_request_amount', 'tp_periodic_plan',
    'tp_periodic_plan_amount', 'tp_credential', 'tp_obligation', 'account_move', 'account_payment', 'hr_expense',
]


def bind():
    kd.BASE = BASE
    kd.DATABASE = DATABASE
    kd.PORT = PORT
    kd.bind()
    return kd.stabilize.native


def tree_hashes(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def rowset(native, database):
    """Per-table multiset of row hashes (write_date/write_uid excluded: upgrades may touch them)."""
    from psycopg2 import sql
    result = {}
    with closing(native.connect(database)) as connection, connection.cursor() as cursor:
        for table in PRESERVED:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' "
                           'AND table_name=%s', (table,))
            columns = sorted({row[0] for row in cursor.fetchall()} - {'write_date', 'write_uid'})
            if not columns:
                continue
            cursor.execute(sql.SQL('SELECT {} FROM {}').format(
                sql.SQL(',').join(map(sql.Identifier, columns)), sql.Identifier(table)))
            result[table] = {'columns': columns, 'hashes': dict(Counter(
                hashlib.sha256(repr(row).encode()).hexdigest() for row in cursor.fetchall()))}
        connection.rollback()
    return result


def compare(before, after):
    report = {}
    for table, data in before.items():
        old, new = Counter(data['hashes']), Counter(after.get(table, {}).get('hashes', {}))
        report[table] = {'rows_before': sum(old.values()), 'rows_after': sum(new.values()),
                         'missing_or_changed': sum((old - new).values()), 'added': sum((new - old).values())}
    return report


def prepare(native):
    kd.stabilize.snapshot()
    snap = Path(native.read(BASE / 'owner.json')['snapshot'])
    shutil.copy2(ROOT / '.local/dev-secrets.json', snap / 'private/dev-secrets.json')  # private config, never Git
    native.write(snap / 'manifest.json', {k: v for k, v in tree_hashes(snap).items() if k != 'manifest.json'})
    native.clone()
    if SOURCE.exists():
        raise SystemExit('Isolated source already exists; reuse it.')
    shutil.copytree(ROOT / 'custom_addons', SOURCE, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    config = native.options(BASE / 'clone.conf')
    config['options']['addons_path'] = str(ROOT / 'addons') + ',' + str(SOURCE)
    with (BASE / 'clone.conf').open('w', encoding='utf-8') as output:
        config.write(output)
    print('KD-UI-002 SNAPSHOT + EXACT RESTORE + ISOLATED SOURCE READY:', DATABASE, PORT)


def upgrade_dev(native, label):
    native.target_config('dev')
    stamp = datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')
    logfile = BASE / f'dev-{label}-{stamp}.log'
    native.dev.stop_server()  # Odoo process of .local/odoo.conf only; PostgreSQL keeps running.
    native.require(not native.dev.is_listening(18069), 'Dev listener not stopped')
    before = rowset(native, 'tp_tanphat_dev')
    args = [sys.executable, '-X', 'utf8', str(ROOT / 'odoo-bin'), '-c', str(ROOT / '.local/odoo.conf'),
            '-d', 'tp_tanphat_dev', '-u', MODULE, '--no-http', '--stop-after-init', '--logfile', str(logfile)]
    with (BASE / f'dev-{label}-{stamp}-console.log').open('wb') as output:
        completed = subprocess.run(args, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, check=False)
    text = logfile.read_text(encoding='utf-8', errors='replace')
    errors = [line for line in text.splitlines() if ' ERROR ' in line or ' CRITICAL ' in line]
    report = compare(before, rowset(native, 'tp_tanphat_dev'))
    changed = {k: v for k, v in report.items() if v['missing_or_changed'] or v['added']}
    result = {'label': label, 'returncode': completed.returncode, 'errors': errors, 'log': str(logfile),
              'preservation': report, 'changed_tables': changed}
    native.write(BASE / f'dev-{label}-result.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'preservation'}, ensure_ascii=False))
    native.require(completed.returncode == 0 and not errors, 'Dev upgrade failed; dev kept stopped for rollback.')
    native.require(not changed, 'Business rowsets changed; dev kept stopped for review.')
    native.dev.start_server()


def apply(native):
    owner = native.read(BASE / 'owner.json')
    native.require(owner.get('rehearsal_passed'), 'Restore rehearsal missing.')
    tested = SOURCE / MODULE
    logs = sorted((BASE / 'odoo-tests').glob('*.json'))
    native.require(logs and native.read(logs[-1])['ok'], 'Latest clone test run is not green.')
    target = ROOT / 'custom_addons' / MODULE
    shutil.copytree(tested, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    stale = set(tree_hashes(target)) - set(tree_hashes(tested))
    for name in stale:
        (target / name).unlink()
    native.require(tree_hashes(target) == tree_hashes(tested), 'Main source differs from tested source.')
    upgrade_dev(native, 'apply')


def rollback(native):
    owner = native.read(BASE / 'owner.json')
    archive = Path(owner['snapshot']) / 'maintained-source.zip'
    target = ROOT / 'custom_addons' / MODULE
    with zipfile.ZipFile(archive) as bundle:
        members = [m for m in bundle.namelist() if m.startswith(f'custom_addons/{MODULE}/')]
        native.require(members, 'Snapshot has no module source.')
        shutil.rmtree(target)
        for member in members:
            bundle.extract(member, ROOT)
    upgrade_dev(native, 'rollback')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'test', 'start', 'stop', 'drift', 'apply', 'rollback'])
    parser.add_argument('--tags', default='/tp_kd_workspace')
    args = parser.parse_args()
    native = bind()
    if args.command == 'prepare':
        prepare(native)
    elif args.command == 'test':
        return kd.tests(MODULE, args.tags)
    elif args.command in ('start', 'stop'):
        native.runtime(args.command)
    elif args.command == 'drift':
        kd.stabilize.dev_drift()
    elif args.command == 'apply':
        apply(native)
    else:
        rollback(native)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
