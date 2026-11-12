"""KD-ACCOUNT-001: owned clone and existing verified backup/apply workflow."""
# ruff: noqa: T201
import argparse
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import kd_ui005 as previous

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/kd-account001'
SOURCE = BASE / 'source/custom_addons'
MODULE = 'tp_kd_workspace'


def bind():
    previous.BASE = BASE
    previous.DATABASE = 'tp_tanphat_kdaccount001_20261108'
    previous.PORT = 19089
    previous.SOURCE = SOURCE
    return previous.bind()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'start', 'stop', 'test', 'backup',
                                           'preserve', 'extended', 'seal', 'apply', 'rollback'])
    parser.add_argument('--label', default='before')
    args = parser.parse_args()
    native = bind()
    if args.command == 'prepare':
        previous.previous.prepare(native)
        shutil.copytree(ROOT / 'custom_addons' / MODULE, BASE / 'baseline_addon')
    elif args.command in ('start', 'stop'):
        native.runtime(args.command)
    elif args.command == 'test':
        result = previous.kd.tests(MODULE, '/tp_kd_workspace')
        if result == 0:
            native.write(BASE / 'tested-source.json', previous.hashes())
        return result
    elif args.command == 'preserve':
        previous.preservation(native, args.label)
    elif args.command == 'extended':
        previous.extended_preservation(native, args.label)
    elif args.command == 'backup':
        previous.previous.backup(native)
    elif args.command == 'seal':
        native.require(native.read(BASE / 'tested-source.json') == previous.hashes(), 'Source changed since tests.')
        browser = native.read(BASE / 'clone-browser.json')
        native.require(browser.get('passed') and not browser['failures'] and not browser['errors'], 'Browser failed.')
        native.require(browser['source_hashes'] == previous.hashes(), 'Browser tested different source.')
        native.write(BASE / 'sealed-source.json', previous.hashes())
        print('SEALED: exact Odoo and browser tested source.')
    elif args.command == 'apply':
        backup = Path(native.read(BASE / 'owner.json')['pre_apply_backup'])
        native.require(backup.resolve().is_relative_to(BASE.resolve()), 'Foreign backup.')
        native.require(0 <= datetime.now(UTC).timestamp() - (backup / 'manifest.json').stat().st_mtime < 900,
                       'Fresh verified backup required.')
        native.require(native.read(BASE / 'sealed-source.json') == previous.hashes(), 'Source changed since seal.')
        tree_hashes = previous.previous.previous.tree_hashes
        native.require(tree_hashes(BASE / 'baseline_addon') == tree_hashes(ROOT / 'custom_addons' / MODULE),
                       'Main addon changed since snapshot.')
        previous.previous.previous.apply(native)
    else:
        # Existing rollback restores only this addon from the owned source snapshot.
        target = (ROOT / 'custom_addons' / MODULE).resolve()
        native.require(target == Path('C:/TANPHAT ONE/custom_addons/tp_kd_workspace').resolve()
                       and target.is_relative_to((ROOT / 'custom_addons').resolve()), 'Unsafe rollback target.')
        previous.previous.previous.rollback(native)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
