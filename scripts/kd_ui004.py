"""KD-UI-004 owned clone operations (Tổng quan redesign). Credentials/evidence stay private.

Same audited chain as KD-UI-003 (kd_ui003 -> kd_ui002 -> kd_native001), rebound to a fresh clone of the
current dev: own DB, port 18489, isolated custom_addons copy and private evidence under .local/kd-ui004.

Commands:
  prepare   consistent snapshot of running dev -> exact restore clone + isolated source (dev never loads
            untested assets).
  test      Odoo tests on the stopped clone (-u <modules>, default tp_kd_workspace).
  upgrade   -u tp_kd_workspace on the stopped clone without tests (UI iteration; tests still gate apply).
  start/stop owned clone runtime only (never PostgreSQL, never another clone or dev).
  backup    fresh verified backup of running dev (DB dump/filestore/private config/source) right before apply.
  apply     copy the tested tp_kd_workspace to main, stop ONLY the dev Odoo process, upgrade the module,
            compare business rowsets before/after, start dev again.
  rollback  restore tp_kd_workspace source from the snapshot zip and upgrade dev (code/assets delta only).
"""
# ruff: noqa: T201
import argparse
import sys
from pathlib import Path

import kd_native001 as kd
import kd_ui003 as previous

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/kd-ui004'
DATABASE = 'tp_tanphat_kdui004_20261107'
PORT = 18489
MODULE = 'tp_kd_workspace'
SOURCE = BASE / 'source/custom_addons'


def bind():
    previous.BASE = BASE
    previous.DATABASE = DATABASE
    previous.PORT = PORT
    previous.SOURCE = SOURCE
    previous.BASELINE_VIEWS = BASE / 'baseline_views'
    return previous.bind()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'test', 'upgrade', 'start', 'stop', 'drift', 'backup',
                                            'apply', 'rollback'])
    parser.add_argument('--modules', default=MODULE)
    parser.add_argument('--tags', default='/tp_kd_workspace')
    args = parser.parse_args()
    native = bind()
    if args.command == 'prepare':
        previous.prepare(native)
        print('KD-UI-004 READY:', DATABASE, PORT)
    elif args.command == 'test':
        return kd.tests(args.modules, args.tags)
    elif args.command == 'upgrade':
        return previous.upgrade(native)
    elif args.command in ('start', 'stop'):
        native.runtime(args.command)
    elif args.command == 'drift':
        kd.stabilize.dev_drift()
    elif args.command == 'backup':
        previous.backup(native)
    elif args.command == 'apply':
        owner = native.read(BASE / 'owner.json')
        native.require(owner.get('pre_apply_backup'), 'Run `backup` right before `apply`.')
        previous.previous.apply(native)
    else:
        previous.previous.rollback(native)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
