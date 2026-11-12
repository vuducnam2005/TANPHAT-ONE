"""Owned KD-NATIVE-001 clone operations; credentials/evidence remain private.

Dev operations require the task's restored snapshot. Business data is written by ORM,
never by SQL. The runtime source on the clone is a separate custom-addon copy.
"""
# ruff: noqa: T201, PLC0415
import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import native_stabilize001 as stabilize

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/kd-native001'
DATABASE = 'tp_tanphat_kd001_20261106'
PORT = 18269


def bind():
    stabilize.BASE = BASE
    stabilize.DATABASE = DATABASE
    stabilize.PORT = PORT
    stabilize.bind()


def tests(modules, tags, *, install=False):
    native = stabilize.native
    config, database = native.target_config('clone')
    owner = native.read(BASE / 'owner.json')
    native.require(owner['http_port'] == PORT and database == DATABASE, 'Wrong owned clone.')
    opts = native.options(config)['options']
    native.require(str(BASE / 'source/custom_addons') in opts['addons_path'], 'Test source must be isolated.')
    native.require(not native.dev.is_listening(PORT), 'Stop owned clone before tests.')
    folder = BASE / 'odoo-tests'
    folder.mkdir(exist_ok=True)
    stamp = datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')
    log = folder / f'{stamp}.log'
    console = folder / f'{stamp}-console.log'
    started = datetime.now(UTC).replace(microsecond=0)
    args = [sys.executable, '-X', 'utf8', str(ROOT / 'odoo-bin'), '-c', str(config), '-d', database,
            '-i' if install else '-u', modules, '--test-enable', '--test-tags', tags,
            '--stop-after-init', '--no-http', '--logfile', str(log)]
    if install:
        args += ['-u', 'tp_contract']
    with console.open('xb') as output:
        completed = subprocess.run(args, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, check=False)
    text = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
    verdict = stabilize.evaluate_test_run(completed.returncode, text, database=database, tags=tags, started_at=started)
    verdict.update(log=str(log.relative_to(ROOT)), modules=modules, tags=tags, port=PORT)
    native.write(folder / f'{stamp}.json', verdict)
    print(json.dumps(verdict, ensure_ascii=False))
    return 0 if verdict['ok'] else 1


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    test = sub.add_parser('test')
    test.add_argument('--modules', default='tp_kd_workspace')
    test.add_argument('--tags', default='/tp_kd_workspace')
    test.add_argument('--install', action='store_true')
    sub.add_parser('start')
    sub.add_parser('stop')
    sub.add_parser('drift')
    args = parser.parse_args()
    bind()
    if args.command == 'test':
        return tests(args.modules, args.tags, install=args.install)
    if args.command in ('start', 'stop'):
        stabilize.native.runtime(args.command)
    else:
        stabilize.dev_drift()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
