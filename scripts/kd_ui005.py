"""KD-UI-005: isolated clone, verified backup and UI-only apply/rollback.

Reuses the guarded KD-UI-003 snapshot/restore chain; never owns another clone or PostgreSQL.
Application edits are made in .local/kd-ui005/source/custom_addons until the clone gates pass.
"""
# ruff: noqa: T201, PLC0415
import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import kd_native001 as kd
import kd_ui003 as previous

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/kd-ui005'
DATABASE = 'tp_tanphat_kdui005_20261107'
PORT = 18789
SOURCE = BASE / 'source/custom_addons'
MODULE = 'tp_kd_workspace'


def bind():
    previous.BASE = BASE
    previous.DATABASE = DATABASE
    previous.PORT = PORT
    previous.SOURCE = SOURCE
    previous.BASELINE_VIEWS = BASE / 'baseline_views'
    return previous.bind()


def hashes():
    return previous.previous.tree_hashes(SOURCE / MODULE)


def inventory(native, target, label):
    def read(env):
        views = {}
        for name in ('opportunity_list', 'opportunity_form', 'kd_project_list', 'project_form'):
            view = env.ref(f'tp_kd_workspace.{name}')
            arch = env[view.model].get_view(view.id, view.type)['arch']
            folder = BASE / f'arch-{label}'
            folder.mkdir(exist_ok=True)
            (folder / f'{name}.xml').write_text(arch, encoding='utf-8')
            views[name] = {'id': view.id, 'model': view.model, 'type': view.type}
        return views
    result = native.orm(target, read)
    native.write(BASE / f'inventory-{label}.json', result)
    print(json.dumps(result))


def preservation(native, label):
    # Include security, private credential links and Home Action/session-independent user settings.
    extra = ['ir_access', 'ir_ui_menu', 'tp_crm_credential_rel', 'res_company',
             'ir_act_window_group_rel', 'ir_ui_view_group_rel', 'ir_model_fields_group_rel']
    for table in extra:
        if table not in previous.previous.PRESERVED:
            previous.previous.PRESERVED.append(table)
    result = previous.previous.rowset(native, 'tp_tanphat_dev')
    native.write(BASE / f'preservation-{label}.json', result)
    before = BASE / 'preservation-before.json'
    if label != 'before':
        report = previous.previous.compare(native.read(before), result)
        changed = {k: v for k, v in report.items() if v['missing_or_changed'] or v['added']}
        native.write(BASE / f'preservation-{label}-diff.json', report)
        native.require(not changed, 'Dev records/security changed; inspect preservation evidence.')
    print(json.dumps({'label': label, 'tables': len(result),
                      'rows': sum(sum(v['hashes'].values()) for v in result.values())}))


def fixture(native):
    """Owned clone only: synthetic long names, public/private links, no dev/user edits."""
    native.target_config('clone')
    marker = BASE / 'fixture.json'
    native.require(not marker.exists(), 'Reuse existing fixture; no duplicate seed.')

    def create(env):
        credentials = native.read(ROOT / '.local/kd-native001/dataset/dev/credentials.json')
        users = {key: env['res.users'].search([('login', '=', value['login'])], limit=1)
                 for key, value in credentials.items()}
        editor = users['editor']
        department = env['tp.kd.grant'].search([('user_id', '=', editor.id)], limit=1).project_id.tp_department_id
        partner = env['res.partner'].create({'name': 'BP005 — Ban quản lý dự án cầu đường ' + 'Tân Phát kết nối hạ tầng vùng ven biển ' * 7})
        project = env['project.project'].create({
            'name': 'BP005 — Tư vấn khảo sát thiết kế công trình cầu và tuyến kết nối ' + 'khu vực đô thị ven biển Tân Phát ' * 7,
            'tp_code': 'BP005-A', 'tp_managed': True, 'company_id': env.company.id,
            'tp_department_id': department.id, 'partner_id': partner.id,
            'user_id': users['planner'].id, 'privacy_visibility': 'employees',
            'kd_scope': 'Phạm vi giả lập BP005; không phải hồ sơ thật.', 'kd_deadline': '2026-12-31',
        })
        for user in users.values():
            env['tp.project.assignment'].create({'project_id': project.id, 'user_id': user.id})
        for domain in ('credential', 'opportunity'):
            for key, caps in [('editor', ['prepare', 'submit']), ('reviewer', ['prepare', 'review']), ('metadata', ['review'])]:
                for cap in caps:
                    env['tp.kd.grant'].create({'project_id': project.id, 'department_id': department.id,
                        'user_id': users[key].id, 'domain': domain, 'capability': cap, 'reason': 'BP005 clone fixture only'})
        credential_ids = []
        for code, owner, reviewer in [('BP005-V', 'editor', 'reviewer'), ('BP005-P', 'reviewer', 'metadata')]:
            credential_ids.append(env['tp.credential'].create({
                'code': code, 'name': code + ' hồ sơ năng lực tổng hợp', 'project_id': project.id,
                'scope': 'Giả lập BP005', 'owner_id': users[owner].id, 'reviewer_id': users[reviewer].id,
                'subject_id': partner.id, 'subject_kind': 'person' if code == 'BP005-P' else 'organization',
                'credential_kind': 'Khảo sát',
                'valid_from': '2026-01-01', 'valid_to': '2027-01-01', 'source_note': 'Dữ liệu giả, chưa xác minh',
            }).id)
        lead = env['crm.lead'].create({'name': 'BP005 — Cơ hội kiểm tra liên kết riêng tư', 'type': 'opportunity',
            'tp_project_id': project.id, 'partner_id': partner.id, 'company_id': env.company.id,
            'user_id': editor.id, 'kd_credential_link_ids': [(6, 0, credential_ids)]})
        result = {'project': project.id, 'partner': partner.id, 'lead': lead.id,
                  'visible_credential': credential_ids[0], 'private_credential': credential_ids[1]}
        env.cr.commit()
        return result
    native.write(marker, native.orm('clone', create))
    print('FIXTURE: synthetic records created on owned clone only; ids in private fixture.json.')


def extended_preservation(native, label):
    """Read-only hashes for nonasset attachments, installed module names and remaining groups."""
    import hashlib
    from collections import Counter

    from psycopg2 import sql

    result = {}
    with native.connect('tp_tanphat_dev') as connection, connection.cursor() as cursor:
        for table in ('ir_attachment', 'res_groups', 'res_groups_implied_rel', 'res_company_users_rel',
                      'ir_ui_menu_group_rel', 'ir_act_server_group_rel'):
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' "
                           'AND table_name=%s', (table,))
            columns = sorted({r[0] for r in cursor.fetchall()} - {'write_date', 'write_uid'})
            native.require(bool(columns), f'Missing preserved table {table}.')
            condition = sql.SQL(" WHERE COALESCE(url, '') NOT LIKE '/web/assets/%'") if table == 'ir_attachment' else sql.SQL('')
            cursor.execute(sql.SQL('SELECT {} FROM {}{}').format(
                sql.SQL(',').join(map(sql.Identifier, columns)), sql.Identifier(table), condition))
            result[table] = {'columns': columns, 'hashes': dict(Counter(
                hashlib.sha256(repr(row).encode()).hexdigest() for row in cursor.fetchall()))}
        cursor.execute("SELECT name FROM ir_module_module WHERE state='installed' ORDER BY name")
        result['installed_modules'] = [r[0] for r in cursor.fetchall()]
        connection.rollback()
    native.write(BASE / f'extended-{label}.json', result)
    if label != 'before':
        native.require(native.read(BASE / 'extended-before.json') == result, 'Attachments/modules/groups changed.')
    print(json.dumps({'label': label, 'nonasset_attachments': sum(result['ir_attachment']['hashes'].values()),
                      'installed_modules': len(result['installed_modules']), 'groups_tables': 5}))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'test', 'upgrade', 'start', 'stop', 'backup',
                                            'apply', 'rollback', 'inventory', 'preserve', 'extended', 'seal', 'fixture'])
    parser.add_argument('--modules', default=MODULE)
    parser.add_argument('--tags', default='/tp_kd_workspace,/tp_contract')
    parser.add_argument('--target', choices=['clone', 'dev'], default='clone')
    parser.add_argument('--label', default='before')
    args = parser.parse_args()
    native = bind()
    if args.command == 'prepare':
        previous.prepare(native)
    elif args.command == 'test':
        result = kd.tests(args.modules, args.tags)
        if result == 0:
            native.write(BASE / 'tested-source.json', hashes())
        return result
    elif args.command == 'upgrade':
        return previous.upgrade(native)
    elif args.command in ('start', 'stop'):
        native.runtime(args.command)
    elif args.command == 'inventory':
        inventory(native, args.target, args.label)
    elif args.command == 'preserve':
        preservation(native, args.label)
    elif args.command == 'extended':
        extended_preservation(native, args.label)
    elif args.command == 'fixture':
        fixture(native)
    elif args.command == 'backup':
        previous.backup(native)
    elif args.command == 'seal':
        native.require(native.read(BASE / 'tested-source.json') == hashes(), 'Source changed since Odoo tests.')
        scope = native.read(BASE / 'scope-probes.json')
        native.require(scope.get('passed') == 3 and scope.get('rolled_back'), 'Scope probes must pass on clone.')
        for name in ('result-all.json', 'result-s.json', 'hoot-result.json', 'regression-result.json'):
            result = native.read(BASE / 'shots/clone-after' / name)
            native.require(not result.get('failure') and not result.get('errors') and result.get('passed'),
                           f'Browser gate failed: {name}')
            native.require(result.get('source_hashes') == hashes(), f'Source changed since {name}.')
        native.write(BASE / 'sealed-source.json', hashes())
        print('SEALED: Odoo + browser + HOOT passed for these source hashes.')
    elif args.command == 'apply':
        owner = native.read(BASE / 'owner.json')
        backup = Path(owner['pre_apply_backup'])
        native.require(backup.resolve().is_relative_to(BASE.resolve()), 'Foreign backup.')
        age = datetime.now(UTC).timestamp() - (backup / 'manifest.json').stat().st_mtime
        native.require(0 <= age < 900, 'Fresh backup required (<15 minutes).')
        native.require(native.read(BASE / 'sealed-source.json') == hashes(), 'Source changed after test gates.')
        baseline_hash = previous.previous.tree_hashes(BASE / 'baseline_addon')
        current_hash = previous.previous.tree_hashes(ROOT / 'custom_addons' / MODULE)
        native.require(current_hash == baseline_hash, 'Main addon changed since snapshot; do not overwrite.')
        previous.previous.apply(native)
    else:
        target = (ROOT / 'custom_addons' / MODULE).resolve()
        native.require(target == Path('C:/TANPHAT ONE/custom_addons/tp_kd_workspace').resolve()
                       and target.is_relative_to((ROOT / 'custom_addons').resolve()), 'Unsafe rollback target.')
        previous.previous.rollback(native)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
