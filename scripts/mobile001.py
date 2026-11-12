"""MOBILE-001: owned clone runtime, hash preservation and narrow dev rollout for the responsive UI batch."""
# ruff: noqa: T201, EM101
import argparse
import json
import subprocess
import sys
from pathlib import Path

import native_data003 as native
import native_data003_preserve as preserve

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/mobile001'
CLONE_BASE = ROOT / '.local/dash-ui001'
CLONE_DB = 'tp_tanphat_dashui001_20261104'
CLONE_PORT = 18159
MODULES = 'tp_web_home,tp_dashboard_privacy'
# Dev already runs tp_dashboard_privacy 20.0.1.1.0 (DASH-UI-001); its MOBILE-001 change is static only (restart rebuilds assets).
DEV_MODULES = 'tp_web_home'
# Rows that a narrow -u of the two UI addons plus browser sessions may touch; everything else must stay identical.
ALLOWED = {'ir_attachment', 'ir_ui_view', 'ir_model_data', 'ir_module_module', 'ir_module_module_dependency',
           'bus_bus', 'ir_cron_trigger', 'orm_signaling_registry', 'res_users_log', 'res_device_log', 'mail_presence',
           'ir_asset', 'ir_translation', 'orm_signaling_default', 'orm_signaling_stable', 'orm_signaling_templates',
           'ir_ui_menu', 'ir_act_client', 'ir_actions'}
# XML reload by -u tp_web_home rewrites its own Home menu/action/menu icon with identical values: write_date only.
WRITE_DATE_ONLY = {'ir_ui_menu', 'ir_act_client', 'ir_actions'}
ASSET_NAMES = {'web.assets_web.min.css', 'web.assets_web.min.js', 'web.assets_web_print.min.css',
               'spreadsheet.o_spreadsheet.min.js', 'web.assets_web_dark.min.css'}


def capture(label):
    BASE.mkdir(parents=True, exist_ok=True)
    current = preserve.capture()
    native.write(BASE / f'preserve-{label}.json', current)
    print('PRESERVATION SNAPSHOT:', label, len(current['tables']), 'tables; hash-only private report.')
    return current


def review(before_label, after_label):
    before = native.read(BASE / f'preserve-{before_label}.json')
    after = native.read(BASE / f'preserve-{after_label}.json')
    diff = preserve.compare(before, after)
    findings = []
    for table, delta in diff['changed_tables'].items():
        native.require(table in ALLOWED, 'Unexpected changed table: ' + table)
        native.require(not delta.get('relation_changed'), 'Unexpected relation rewrite in ' + table)
        if table == 'ir_attachment':
            asset_digests = {preserve.digest(name) for name in ASSET_NAMES}
            for rid in delta['deleted']:
                native.require(before['tables'][table][rid].get('name') in asset_digests, 'Deleted attachment is not a regenerated asset.')
            for rid in delta['created']:
                native.require(after['tables'][table][rid].get('name') in asset_digests, 'Unexpected new attachment.')
            native.require(all(fields == ['write_date'] for fields in delta['updated'].values()),
                           'Existing attachment content/metadata mutated.')
        elif table in WRITE_DATE_ONLY:
            native.require(not delta['created'] and not delta['deleted'], 'Menu/action inventory changed in ' + table)
            native.require(all(fields == ['write_date'] for fields in delta['updated'].values()), 'Menu/action values changed in ' + table)
        elif table == 'ir_module_module':
            native.require(not delta['created'] and not delta['deleted'], 'Module inventory changed.')
        findings.append({'table': table, 'created': len(delta.get('created', [])), 'deleted': len(delta.get('deleted', [])),
                         'updated': len(delta.get('updated', {}))})
    result = {'passed': True, 'unchanged_tables': diff['unchanged_tables'], 'changed': findings,
              'config_credentials_cluster_roles_unchanged': diff['config_credentials_cluster_roles_unchanged']}
    native.write(BASE / f'preserve-review-{before_label}-{after_label}.json', {**result, 'diff': diff})
    print(json.dumps(result))


def clone_tests():
    """Upgrade only the two UI addons on the owned clone and run their Odoo tests (clone must be stopped)."""
    native.require(not native.dev.is_listening(CLONE_PORT), 'Stop the owned clone before upgrading it.')
    log = BASE / 'clone-odoo-tests.log'
    with (BASE / 'clone-odoo-tests-console.log').open('ab') as output:
        subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'odoo-bin'), '-c', str(CLONE_BASE / 'clone.conf'),
                        '-d', CLONE_DB, '-u', MODULES, '--test-enable', '--test-tags', '/tp_web_home,/tp_dashboard_privacy',
                        '--stop-after-init', '--no-http', '--logfile', str(log)], cwd=ROOT,
                       stdout=output, stderr=subprocess.STDOUT, check=True)
    print('CLONE UPGRADE+TESTS finished; read', log.name)


def upgrade_dev():
    native.target_config('dev')
    native.require((BASE / 'preserve-dev-before.json').exists(), 'Capture dev-before preservation first.')
    for name in ('flows-clone/results.json', 'survey-after-clone/survey.json'):
        native.require((BASE / name).exists(), 'Clone evidence missing: ' + name)
    native.require(native.read(BASE / 'flows-clone/results.json')['passed'], 'Passing clone flows required.')
    running = native.dev.is_listening(18069)
    native.require(running, 'Expected existing dev Odoo.')
    try:
        native.dev.stop_server()  # Not dev.py stop: that also stops PostgreSQL.
        native.require(native.dev.is_listening(55432), 'PostgreSQL must remain running.')
        with (BASE / 'dev-upgrade-console.log').open('ab') as output:
            subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'odoo-bin'), '-c', str(ROOT / '.local/odoo.conf'),
                            '-d', 'tp_tanphat_dev', '-u', DEV_MODULES, '--stop-after-init', '--no-http',
                            '--logfile', str(BASE / 'dev-upgrade.log')], cwd=ROOT,
                           stdout=output, stderr=subprocess.STDOUT, check=True)
    finally:
        if running and not native.dev.is_listening(18069):
            native.dev.start_server()
    print('UPGRADE PASS: -u tp_web_home only; dev18069 restarted, PostgreSQL kept running; no seed.')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    native.BASE = CLONE_BASE
    native.DATABASE = CLONE_DB
    native.PORT = CLONE_PORT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['capture', 'review', 'clone-start', 'clone-stop', 'clone-tests', 'upgrade-dev'])
    parser.add_argument('--label')
    parser.add_argument('--before')
    args = parser.parse_args()
    if args.command == 'capture':
        capture(args.label)
    elif args.command == 'review':
        review(args.before, args.label)
    elif args.command == 'clone-start':
        native.runtime('start')
    elif args.command == 'clone-stop':
        native.runtime('stop')
    elif args.command == 'clone-tests':
        clone_tests()
    else:
        upgrade_dev()


if __name__ == '__main__':
    main()
