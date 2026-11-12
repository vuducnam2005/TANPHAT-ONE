"""UI-SHELL-AUTH-001: reuse owned snapshot/restore; deploy only two sealed UI addons."""
# ruff: noqa: T201, PLC0415
import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import kd_ui003 as prior

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/ui-shell-auth001'
SOURCE = BASE / 'source/custom_addons'
DB = 'tp_tanphat_shellauth001_20261109'
PORT = 19189
MODULES = ('tp_web_home', 'tp_web_login')


def bind():
    prior.BASE, prior.DATABASE, prior.PORT, prior.SOURCE = BASE, DB, PORT, SOURCE
    return prior.bind()


def hashes(folder=None):
    folder = SOURCE if folder is None else folder
    return {m: prior.previous.tree_hashes(folder / m) for m in MODULES}


def preservation(native, target, label):
    from psycopg2 import sql
    tables = list(dict.fromkeys(prior.previous.PRESERVED + [
        'res_groups', 'res_groups_implied_rel', 'res_company_users_rel', 'ir_access',
        'ir_ui_menu_group_rel', 'ir_act_window_group_rel', 'ir_act_server_group_rel',
        'ir_ui_view_group_rel', 'ir_model_fields_group_rel', 'res_company',
        'tp_crm_credential_rel',
    ]))
    prior.previous.PRESERVED = tables
    database = DB if target == 'clone' else 'tp_tanphat_dev'
    result = {'rows': prior.previous.rowset(native, database)}
    with native.connect(database) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT key,value FROM ir_config_parameter ORDER BY key" if target == 'dev' else
                       "SELECT key,value FROM ir_config_parameter WHERE key NOT IN "
                       "('web.base.url','database.is_neutralized','database.uuid','tp_native_data003.owner') ORDER BY key")
        result['config'] = cursor.fetchall()
        cursor.execute("SELECT name,state,latest_version FROM ir_module_module ORDER BY name")
        result['modules'] = cursor.fetchall()
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='ir_attachment' "
                       "AND table_schema='public' ORDER BY column_name")
        cols = [r[0] for r in cursor.fetchall() if r[0] not in ('write_date', 'write_uid')]
        cursor.execute(sql.SQL("SELECT {} FROM ir_attachment WHERE COALESCE(url,'') NOT LIKE '/web/assets/%'").format(
            sql.SQL(',').join(map(sql.Identifier, cols))))
        import hashlib
        result['attachments'] = dict(Counter(hashlib.sha256(repr(row).encode()).hexdigest() for row in cursor.fetchall()))
        filestore = BASE / 'data/filestore' / DB if target == 'clone' else ROOT / '.local/odoo/filestore/tp_tanphat_dev'
        result['blobs'] = native.backup.attachment_inventory(connection, filestore)
    # Asset references may be rebuilt; compare nonasset metadata above and original blobs separately.
    native.write(BASE / f'preserve-{target}-{label}.json', result)
    before_file = BASE / f'preserve-{target}-before.json'
    if label != 'before':
        before = native.read(before_file)
        result = native.read(BASE / f'preserve-{target}-{label}.json')
        changed = {k: v for k, v in prior.previous.compare(before['rows'], result['rows']).items()
                   if v['missing_or_changed'] or v['added']}
        oldmods = {r[0]: r[1:] for r in before['modules']}
        newmods = {r[0]: r[1:] for r in result['modules']}
        moddelta = {m: [oldmods.get(m), v] for m, v in newmods.items() if oldmods.get(m) != v}
        original_blobs = {(x['store_fname'], x['sha1']) for x in before['blobs']}
        live_blobs = {(x['store_fname'], x['sha1']) for x in result['blobs']}
        # Check original blob bytes even when Odoo removes superseded asset metadata.
        blobs_kept = all((filestore / name).is_file() and native.backup.digest(filestore / name, 'sha1') == digest
                         for name, digest in original_blobs)
        report = {'changed_tables': changed, 'config_equal': before['config'] == result['config'],
                  'nonasset_attachments_equal': before['attachments'] == result['attachments'],
                  'original_blobs_valid': blobs_kept, 'module_delta': moddelta,
                  'tables': len(before['rows']), 'rows': sum(sum(v['hashes'].values()) for v in before['rows'].values()),
                  'live_blob_references': len(live_blobs)}
        native.write(BASE / f'preservation-{target}-{label}-result.json', report)
        native.require(not changed and report['config_equal'] and report['nonasset_attachments_equal'] and blobs_kept
                       and set(moddelta) <= set(MODULES), 'Preservation differs: inspect private report.')
        print(json.dumps(report))
    else:
        print('PRESERVATION BASELINE:', target, len(tables), 'tables; private config/users/blob evidence saved.')


def run_odoo(native, target, *, tests=False):
    cfg, database = native.target_config(target)
    if target == 'clone':
        native.require(not native.dev.is_listening(PORT), 'Stop owned clone first.')
    stamp = datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')
    log = BASE / f'{target}-odoo-{stamp}.log'
    with native.connect(database) as conn, conn.cursor() as cur:
        cur.execute("SELECT state FROM ir_module_module WHERE name='tp_web_login'")
        installed = cur.fetchone()[0] == 'installed'
    args = [sys.executable, '-X', 'utf8', str(ROOT / 'odoo-bin'), '-c', str(cfg), '-d', database,
            '-u', ','.join(MODULES) if installed else 'tp_web_home', '--stop-after-init', '--no-http', '--logfile', str(log)]
    if not installed:
        args += ['-i', 'tp_web_login']
    started = datetime.now(UTC).replace(microsecond=0)
    tags = '/tp_web_home,/tp_web_login,/tp_kd_workspace'
    if tests:
        args += ['--test-enable', '--test-tags', tags]
    with log.with_suffix('.console.log').open('wb') as out:
        done = subprocess.run(args, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, check=False)
    content = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
    if tests:
        result = prior.kd.stabilize.evaluate_test_run(done.returncode, content, database=database, tags=tags, started_at=started)
    else:
        bad = [s for s in content.splitlines() if ' ERROR ' in s or ' CRITICAL ' in s]
        result = {'ok': done.returncode == 0 and not bad, 'returncode': done.returncode, 'errors': bad}
    result.update(log=str(log.relative_to(ROOT)), source_hashes=hashes(SOURCE if target == 'clone' else ROOT / 'custom_addons'))
    native.write(BASE / f'{target}-odoo-result.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'source_hashes'}))
    native.require(result['ok'], 'Odoo failed: inspect private log.')


def verify_backup(native):
    """Restore the fresh backup to a new owned DB and compare every table, before any dev apply."""
    from psycopg2 import sql
    backup = Path(native.read(BASE / 'owner.json')['pre_apply_backup'])
    database = 'tp_tanphat_shellauth001_backup_' + datetime.now(UTC).strftime('%H%M%S')
    with closing(native.connect('postgres', admin=True)) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM pg_database WHERE datname=%s', (database,))
            native.require(not cur.fetchone(), 'Verification DB already exists; refusing foreign reuse.')
            native.write(BASE / 'backup-restore-owner.json', {'database': database, 'backup': str(backup), 'owned': True})
            cur.execute(sql.SQL("CREATE DATABASE {} OWNER tp_odoo TEMPLATE template0 ENCODING 'UTF8'").format(sql.Identifier(database)))
    pg_env = native.backup.pg_environment(native.read(ROOT / '.local/dev-secrets.json')['pg_app'])
    native.backup.run([native.dev.pg_bin() / 'pg_restore.exe', '-h', '127.0.0.1', '-p', '55432', '-U', 'tp_odoo',
                      '-d', database, '--no-owner', '--no-privileges', '--exit-on-error', backup / 'database.dump'], env=pg_env)
    baseline = native.read(backup / 'baseline.json')
    with native.connect(database) as conn:
        native.require(native.backup.table_inventory(conn) == baseline['tables'], 'Fresh backup restored rows differ.')
        blobs = native.backup.attachment_inventory(conn, backup / 'filestore')
        native.require(len(blobs) == baseline['attachments'], 'Restored attachment references differ.')
    native.write(BASE / 'backup-restore-result.json', {'ok': True, 'backup': str(backup), 'database': database,
                 'tables': len(baseline['tables']), 'attachment_references': len(blobs)})
    print('FRESH BACKUP RESTORE PASS:', len(baseline['tables']), 'tables;', len(blobs), 'attachment references.')


def rollback(native, target):
    """Reverse only newly installed login + Home source/views; never restore the entire database."""
    native.require(target in ('dev', 'clone'), 'Unknown rollback target.')
    config, database = native.target_config(target)
    folder = SOURCE if target == 'clone' else ROOT / 'custom_addons'
    native.require(hashes(folder) == native.read(BASE / 'sealed-source.json'), 'Concurrent source edits: reconcile first.')
    if target == 'dev':
        native.dev.stop_server()
    else:
        native.runtime('stop')
    preservation(native, target, 'pre-rollback')
    # Login adds no models/business rows; refuse uninstall if another installed addon depends on it.
    log = BASE / f'{target}-rollback-uninstall.log'
    code = """
m=env['ir.module.module'].search([('name','=','tp_web_login')])
dependents=env['ir.module.module.dependency'].search([('name','=','tp_web_login')]).mapped('module_id').filtered(lambda r:r.state=='installed')
assert not dependents, 'Installed dependent addon: stop rollback and reconcile'
assert m.state=='installed'
m.button_immediate_uninstall()
env.cr.commit()
"""
    done = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'odoo-bin'), 'shell', '-c', str(config),
                           '-d', database, '--no-http', '--logfile', str(log)], input=code, text=True,
                          encoding='utf-8', cwd=ROOT, capture_output=True, check=False)
    log.with_suffix('.console.log').write_text(done.stdout + done.stderr, encoding='utf-8')
    native.require(done.returncode == 0, 'Login rollback failed; inspect private log before proceeding.')
    snapshot = Path(native.read(BASE / 'owner.json')['snapshot'])
    with zipfile.ZipFile(snapshot / 'maintained-source.zip') as bundle:
        for module in MODULES:
            prefix = f'custom_addons/{module}/'
            original = {name[len(prefix):]: bundle.read(name) for name in bundle.namelist()
                        if name.startswith(prefix) and not name.endswith('/')}
            destination = (folder / module).resolve()
            native.require(destination.parent == folder.resolve(), 'Unsafe rollback source target.')
            for stale in set(prior.previous.tree_hashes(destination)) - set(original):
                (destination / stale).unlink()
            for name, data in original.items():
                file = (destination / name).resolve()
                native.require(file.is_relative_to(destination), 'Snapshot source escapes addon.')
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(data)
    log = BASE / f'{target}-rollback-home.log'
    done = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'odoo-bin'), '-c', str(config), '-d', database,
                           '-u', 'tp_web_home', '--no-http', '--stop-after-init', '--logfile', str(log)],
                          cwd=ROOT, capture_output=True, check=False)
    native.require(done.returncode == 0 and ' ERROR ' not in log.read_text(encoding='utf-8'), 'Home rollback failed.')
    preservation(native, target, 'rolled-back')
    native.dev.start_server() if target == 'dev' else native.runtime('start')
    print('UI delta rollback complete; verify native login/logout before accepting runtime.')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['prepare', 'start', 'stop', 'test', 'upgrade', 'backup', 'preserve', 'seal', 'apply', 'rollback'])
    p.add_argument('--target', choices=['clone', 'dev'], default='clone')
    p.add_argument('--label', default='before')
    args = p.parse_args()
    native = bind()
    if args.command == 'prepare':
        prior.previous.prepare(native)
        native.write(BASE / 'baseline-source.json', hashes(ROOT / 'custom_addons'))
    elif args.command in ('start', 'stop'):
        native.runtime(args.command)
    elif args.command in ('test', 'upgrade'):
        native.require(args.target == 'clone', 'Dev changes only through sealed apply.')
        run_odoo(native, 'clone', tests=args.command == 'test')
    elif args.command == 'preserve':
        preservation(native, args.target, args.label)
    elif args.command == 'backup':
        prior.backup(native)
        verify_backup(native)
    elif args.command == 'rollback':
        rollback(native, args.target)
    elif args.command == 'seal':
        for filename in ('clone-odoo-result.json', 'clone-browser.json'):
            r = native.read(BASE / filename)
            native.require(r['ok'] and r['source_hashes'] == hashes(), 'Green tests for exact current source required.')
        for filename in ('extra-result.json', 'policy-result.json', 'passkey-result.json', 'zoom-result.json'):
            native.require(native.read(BASE / filename)['ok'], f'{filename} must pass before seal.')
        native.write(BASE / 'sealed-source.json', hashes())
        print('SEALED exact Odoo/browser source.')
    elif args.command == 'apply':
        native.require(args.target == 'dev', 'Explicit --target dev required.')
        owner = native.read(BASE / 'owner.json')
        backup = Path(owner['pre_apply_backup'])
        restored = native.read(BASE / 'backup-restore-result.json')
        native.require(restored['ok'] and restored['backup'] == str(backup), 'Fresh backup restore verification required.')
        native.require(backup.resolve().is_relative_to(BASE.resolve()) and owner['rehearsal_passed'], 'Owned verified restore required.')
        native.require(0 <= datetime.now(UTC).timestamp() - (backup / 'manifest.json').stat().st_mtime < 900, 'Fresh backup required.')
        native.require(native.read(BASE / 'sealed-source.json') == hashes(), 'Source changed after seal.')
        current = hashes(ROOT / 'custom_addons')
        previous_apply = BASE / 'dev-odoo-result.json'
        expected = native.read(previous_apply) if previous_apply.exists() else None
        native.require(native.read(BASE / 'baseline-source.json') == current or
                       (expected and expected['ok'] and expected['source_hashes'] == current),
                       'Main source changed concurrently.')
        native.dev.stop_server()
        native.require(not native.dev.is_listening(18069), 'Dev still running.')
        preservation(native, 'dev', 'before')
        for module in MODULES:
            target = (ROOT / 'custom_addons' / module).resolve()
            native.require(target.parent == (ROOT / 'custom_addons').resolve(), 'Unsafe source destination.')
            shutil.copytree(SOURCE / module, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            for stale in set(prior.previous.tree_hashes(target)) - set(prior.previous.tree_hashes(SOURCE / module)):
                (target / stale).unlink()
        native.require(hashes(ROOT / 'custom_addons') == hashes(), 'Applied source differs.')
        run_odoo(native, 'dev')
        preservation(native, 'dev', 'after-upgrade')
        native.dev.start_server()


if __name__ == '__main__':
    main()
