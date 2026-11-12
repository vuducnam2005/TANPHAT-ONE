"""KD-UI-003 owned clone operations (bordered tables + detail layouts). Credentials/evidence stay private.

Commands:
  prepare   consistent snapshot of running dev (DB+filestore+config+dirty source) -> exact restore clone
            on port 18389 with an isolated custom_addons copy; also keeps a baseline copy of the KH-KD views.
  test      Odoo tests on the stopped clone (-u <modules>, default tp_kd_workspace).
  upgrade   -u tp_kd_workspace on the stopped clone without tests (fast UI iteration; tests still gate apply).
  start/stop owned clone runtime only (never PostgreSQL, never another clone).
  archdiff  compare the edited KH-KD views (isolated source) with the baseline: every field/button keeps its
            behaviour attributes and the invisible/groups conditions inherited from its containers.
  apply     copy the tested tp_kd_workspace to main, stop ONLY the dev Odoo process, upgrade the module,
            compare business rowsets before/after, start dev again.
  backup    fresh verified backup of running dev (DB dump/filestore/private config/source) right before apply.
  rollback  restore tp_kd_workspace source from the snapshot zip and upgrade dev (code/assets/view delta only).
"""
# ruff: noqa: T201, PLC0415, S603
import argparse
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import kd_native001 as kd
import kd_ui002 as previous

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/kd-ui003'
DATABASE = 'tp_tanphat_kdui003_20261106'
PORT = 18389
MODULE = 'tp_kd_workspace'
SOURCE = BASE / 'source/custom_addons'
BASELINE_VIEWS = BASE / 'baseline_views'
# Presentation-only attributes that KD-UI-003 may add or change.
LAYOUT_ATTRS = {'class', 'width', 'optional', 'nolabel', 'colspan', 'string', 'placeholder'}
# Agreed presentation exceptions (design §6 D): the task state moves to the title as a readonly badge.
ALLOWED_WIDGET_CHANGES = {('kd_task_form', 'state')}


def bind():
    previous.BASE = BASE
    previous.DATABASE = DATABASE
    previous.PORT = PORT
    previous.SOURCE = SOURCE
    return previous.bind()


def prepare(native):
    previous.prepare(native)
    if not BASELINE_VIEWS.exists():
        shutil.copytree(ROOT / 'custom_addons' / MODULE / 'views', BASELINE_VIEWS)
    print('KD-UI-003 READY:', DATABASE, PORT, 'baseline views:', BASELINE_VIEWS)


def backup(native):
    """Fresh pre-apply backup of the running dev without stopping it: consistent DB dump (exported
    snapshot), filestore blobs with sha1, private config and maintained source; then verified by
    re-hashing every file and listing the dump. The clone and owner.json snapshot stay untouched."""
    import zipfile
    from contextlib import closing
    from datetime import UTC, datetime

    import psycopg2.extensions

    st = kd.stabilize
    st.require(native.dev.is_listening(18069), 'Expected the existing dev runtime.')
    pid_before = st.dev_pid()
    folder = BASE / ('backup-pre-apply-' + datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ'))
    (folder / 'private').mkdir(parents=True)
    for name in ('odoo.conf', 'runtime-owner.json', 'dev-secrets.json'):
        shutil.copy2(ROOT / '.local' / name, folder / 'private' / name)
    with zipfile.ZipFile(folder / 'maintained-source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in (ROOT / 'custom_addons').rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                archive.write(path, path.relative_to(ROOT))
    secrets = native.read(ROOT / '.local/dev-secrets.json')
    pg_env = native.backup.pg_environment(secrets['pg_app'])
    with closing(native.connect(st.DEV_DB)) as connection:
        connection.set_session(isolation_level=psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ, readonly=True)
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_export_snapshot()')
            exported = cursor.fetchone()[0]
        native.backup.run([native.dev.pg_bin() / 'pg_dump.exe', '-h', '127.0.0.1', '-p', '55432', '-U', 'tp_odoo',
                           '-d', st.DEV_DB, '-Fc', '--no-owner', '--no-privileges', '--snapshot', exported,
                           '-f', folder / 'database.dump'], env=pg_env)
        tables = native.backup.table_inventory(connection)
        attachments = native.backup.attachment_inventory(connection, st.DEV_FILESTORE)
        connection.rollback()
    for item in attachments:
        destination = folder / 'filestore' / item['store_fname']
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copy2(st.DEV_FILESTORE / item['store_fname'], destination)
        st.require(native.backup.digest(destination, 'sha1') == item['sha1'], 'Copied blob differs from its checksum.')
    st.require(native.dev.is_listening(18069) and st.dev_pid() == pid_before, 'Dev runtime changed during backup.')
    native.write(folder / 'baseline.json', {'tables': tables, 'attachments': len(attachments), 'pg_snapshot': exported,
                                           'dev_pid': pid_before, 'dev_stopped': False})
    manifest = {p.relative_to(folder).as_posix(): native.backup.digest(p) for p in folder.rglob('*') if p.is_file()}
    native.write(folder / 'manifest.json', manifest)
    # Verify: every file re-hashes to the manifest and the dump is a readable custom-format archive.
    again = {p.relative_to(folder).as_posix(): native.backup.digest(p) for p in folder.rglob('*')
             if p.is_file() and p.name != 'manifest.json'}
    st.require(again == manifest, 'Backup checksum verification failed.')
    listing = subprocess.run([native.dev.pg_bin() / 'pg_restore.exe', '--list', folder / 'database.dump'],
                             capture_output=True, check=False)
    st.require(listing.returncode == 0 and b'TABLE DATA' in listing.stdout, 'Dump is not a readable archive.')
    owner = native.read(BASE / 'owner.json')
    owner['pre_apply_backup'] = str(folder)
    native.write(BASE / 'owner.json', owner)
    print(json.dumps({'backup': str(folder.relative_to(ROOT)), 'files': len(manifest), 'tables': len(tables),
                      'attachments': len(attachments), 'dev_pid': pid_before, 'verified': True}))


def _signatures(path):
    """{view record id: Counter(signature)} for every field/button of every arch in an XML data file."""
    from lxml import etree

    result = {}
    tree = etree.parse(str(path))
    for record in tree.iter('record'):
        if record.get('model') != 'ir.ui.view':
            continue
        arch = record.find("field[@name='arch']")
        if arch is None:
            continue
        signatures = Counter()
        for node in arch.iter('field', 'button'):
            if node.getparent() is record:  # the record's own <field name="arch">
                continue
            attrs = {k: v for k, v in node.attrib.items() if k not in LAYOUT_ATTRS}
            if (record.get('id'), node.get('name')) in ALLOWED_WIDGET_CHANGES:
                attrs.pop('widget', None)
            inherited = []
            parent = node.getparent()
            while parent is not None and parent is not arch:
                for key in ('invisible', 'groups'):
                    if parent.get(key):
                        inherited.append(f'{parent.tag}.{key}={parent.get(key)}')
                if parent.tag == 'field':  # x2many sub-view: keep the owning field in the signature
                    inherited.append(f'in:{parent.get("name")}')
                parent = parent.getparent()
            signatures[node.tag, node.get('name'), tuple(sorted(attrs.items())), tuple(sorted(inherited))] += 1
        result[record.get('id')] = signatures
    return result


def archdiff():
    edited = SOURCE / MODULE / 'views'
    problems, additions = {}, {}
    for base_file in sorted(BASELINE_VIEWS.glob('*.xml')):
        old = _signatures(base_file)
        new = _signatures(edited / base_file.name)
        for view_id, signature in old.items():
            if view_id not in new:
                problems[f'{base_file.name}:{view_id}'] = 'view record removed'
                continue
            lost, added = signature - new[view_id], new[view_id] - signature
            if lost:  # a field/button or one of its behaviour attributes disappeared or changed
                problems[f'{base_file.name}:{view_id}'] = {'lost': [repr(k) for k in lost],
                                                          'added': [repr(k) for k in added]}
            elif added:  # existing model fields shown as extra columns: listed for review (no money: Odoo test)
                additions[f'{base_file.name}:{view_id}'] = [repr(k) for k in added]
    new_views = sorted({f'{p.name}:{v}' for p in edited.glob('*.xml') for v in _signatures(p)}
                       - {f'{p.name}:{v}' for p in BASELINE_VIEWS.glob('*.xml') for v in _signatures(p)})
    print(json.dumps({'ok': not problems, 'changed_views': problems, 'added_columns': additions,
                      'new_views': new_views},
                     ensure_ascii=False, indent=1))
    return 0 if not problems else 1


def upgrade(native):
    """-u tp_kd_workspace on the stopped owned clone (no tests). Same isolation guards as kd.tests."""
    import subprocess
    from datetime import UTC, datetime

    config, database = native.target_config('clone')
    owner = native.read(BASE / 'owner.json')
    native.require(owner['http_port'] == PORT and database == DATABASE, 'Wrong owned clone.')
    native.require(str(SOURCE) in native.options(config)['options']['addons_path'], 'Source must be isolated.')
    native.require(not native.dev.is_listening(PORT), 'Stop owned clone before upgrade.')
    folder = BASE / 'upgrades'
    folder.mkdir(exist_ok=True)
    log = folder / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}.log"
    completed = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'odoo-bin'), '-c', str(config), '-d', database,
                                '-u', MODULE, '--stop-after-init', '--no-http', '--logfile', str(log)],
                               cwd=ROOT, check=False, capture_output=True)
    text = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
    bad = [line for line in text.splitlines() if ' ERROR ' in line or ' CRITICAL ' in line]
    print(json.dumps({'ok': completed.returncode == 0 and not bad, 'returncode': completed.returncode,
                      'errors': bad[:20], 'log': str(log.relative_to(ROOT))}, ensure_ascii=False))
    return 0 if completed.returncode == 0 and not bad else 1


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'test', 'upgrade', 'start', 'stop', 'drift', 'archdiff',
                                            'backup', 'apply', 'rollback'])
    parser.add_argument('--modules', default=MODULE)
    parser.add_argument('--tags', default='/tp_kd_workspace')
    args = parser.parse_args()
    native = bind()
    if args.command == 'prepare':
        prepare(native)
    elif args.command == 'test':
        return kd.tests(args.modules, args.tags)
    elif args.command == 'upgrade':
        return upgrade(native)
    elif args.command in ('start', 'stop'):
        native.runtime(args.command)
    elif args.command == 'drift':
        kd.stabilize.dev_drift()
    elif args.command == 'archdiff':
        return archdiff()
    elif args.command == 'backup':
        backup(native)
    elif args.command == 'apply':
        owner = native.read(BASE / 'owner.json')
        native.require(owner.get('pre_apply_backup'), 'Run `backup` right before `apply`.')
        previous.apply(native)
    else:
        previous.rollback(native)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
