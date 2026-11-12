"""UI-HOME-002: isolated Home clone, verified backup and module-only dev upgrade.

Reuses the existing snapshot/restore/ownership guards. Never stops PostgreSQL.
Evidence and private configuration stay in .local/ui-home002.
"""
# ruff: noqa: T201
import argparse
import hashlib
import io
import re
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

import kd_native001 as kd
import kd_ui003 as previous
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/ui-home002'
DATABASE = 'tp_tanphat_home002_20261107'
PORT = 18589
MODULE = 'tp_web_home'
SOURCE = BASE / 'source/custom_addons'


def bind():
    previous.BASE = BASE
    previous.DATABASE = DATABASE
    previous.PORT = PORT
    previous.SOURCE = SOURCE
    previous.MODULE = MODULE
    previous.previous.MODULE = MODULE
    previous.previous.PRESERVED = list(dict.fromkeys(previous.previous.PRESERVED + [
        'res_groups', 'res_groups_implied_rel', 'ir_access',
        'res_company_users_rel', 'ir_ui_menu_group_rel',
        'ir_act_window_group_rel', 'ir_act_server_group_rel',
        'ir_ui_view_group_rel', 'ir_model_fields_group_rel',
    ]))
    return previous.bind()


def check_access_snapshot(native):
    """Compare actual Odoo 20 ACL/domain rows to the pre-apply dump, excluding audit timestamps."""
    owner = native.read(BASE / 'owner.json')
    folder = Path(owner['pre_apply_backup'])
    dumped = subprocess.run([native.dev.pg_bin() / 'pg_restore.exe', '--data-only', '--table=ir_access', '--file=-',
                             folder / 'database.dump'], capture_output=True, check=True).stdout.decode('utf-8')
    match = re.search(r'COPY public\.ir_access \((.*?)\) FROM stdin;\r?\n(.*?)\r?\n\\\.', dumped, re.S)
    native.require(match is not None, 'ACL COPY section missing from verified dump.')
    columns = match[1].split(', ')
    kept = [i for i, column in enumerate(columns) if column not in ('write_date', 'write_uid')]
    before = Counter(tuple(line.split('\t')[i] for i in kept) for line in match[2].splitlines())
    with native.connect('tp_tanphat_dev') as connection, connection.cursor() as cursor:
        output = io.StringIO()
        query = sql.SQL('COPY (SELECT {} FROM ir_access) TO STDOUT').format(
            sql.SQL(',').join(sql.Identifier(columns[i]) for i in kept))
        cursor.copy_expert(query.as_string(connection), output)
        after = Counter(tuple(line.split('\t')) for line in output.getvalue().splitlines())
        tables = native.backup.table_inventory(connection)
    baseline = native.read(folder / 'baseline.json')['tables']
    group_tables = ['ir_act_window_group_rel', 'ir_act_server_group_rel',
                    'ir_ui_view_group_rel', 'ir_model_fields_group_rel']
    same_groups = all(baseline[k] == tables[k] for k in group_tables)
    result = {'acl_rows': sum(before.values()), 'acl_domains_equal': before == after,
              'group_tables_equal': same_groups, 'group_tables': group_tables,
              'excluded_acl_columns': ['write_date', 'write_uid']}
    native.write(BASE / 'security-preservation.json', result)
    native.require(before == after and same_groups, 'Security rows changed; review security-preservation.json.')
    print('SECURITY PASS:', sum(before.values()), 'ACL/domain rows and 4 action/view/field group tables.')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'test', 'upgrade', 'start', 'stop',
                                            'backup', 'apply', 'rollback', 'preserve-before', 'preserve-after'])
    args = parser.parse_args()
    native = bind()
    if args.command == 'prepare':
        previous.previous.prepare(native)
    elif args.command == 'test':
        result = kd.tests(MODULE, '/tp_web_home')
        if result == 0:
            native.write(BASE / 'tested-source.json', previous.previous.tree_hashes(SOURCE / MODULE))
        return result
    elif args.command == 'upgrade':
        return previous.upgrade(native)
    elif args.command in ('start', 'stop'):
        native.runtime(args.command)
    elif args.command == 'backup':
        previous.backup(native)
    elif args.command == 'apply':
        owner = native.read(BASE / 'owner.json')
        native.require(owner.get('pre_apply_backup'), 'Run backup before apply.')
        result = native.read(BASE / 'shots/clone-after/result.json')
        native.require(result.get('ok') and not result.get('errors'), 'Browser checks must pass.')
        hashes = previous.previous.tree_hashes(SOURCE / MODULE)
        native.require(native.read(BASE / 'tested-source.json') == hashes, 'Source changed after Odoo tests.')
        native.require(result.get('source_hashes') == hashes, 'Source changed after browser checks.')
        hoot = native.read(BASE / 'shots/clone-hoot/result.json')
        native.require(hoot.get('ok') and hoot.get('source_hashes') == hashes, 'HOOT must pass for current source.')
        prefix = f'custom_addons/{MODULE}/'
        with zipfile.ZipFile(Path(owner['snapshot']) / 'maintained-source.zip') as archive:
            original = {name[len(prefix):]: hashlib.sha256(archive.read(name)).hexdigest()
                        for name in archive.namelist() if name.startswith(prefix) and not name.endswith('/')}
        native.require(previous.previous.tree_hashes(ROOT / 'custom_addons' / MODULE) == original,
                       'Main Home source changed since snapshot; review concurrent edits before apply.')
        previous.previous.apply(native)
    elif args.command.startswith('preserve-'):
        rows = previous.previous.rowset(native, 'tp_tanphat_dev')
        native.write(BASE / f'{args.command}.json', rows)
        if args.command == 'preserve-after':
            report = previous.previous.compare(native.read(BASE / 'preserve-before.json'), rows)
            changed = {k: v for k, v in report.items() if v['missing_or_changed'] or v['added']}
            native.write(BASE / 'preservation-result.json', {'tables': len(report), 'changed': changed})
            native.require(not changed, 'Dev records changed; review preservation-result.json.')
            print('PRESERVATION PASS:', len(report), 'tables, no changed rows.')
            check_access_snapshot(native)
    else:
        previous.previous.rollback(native)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
