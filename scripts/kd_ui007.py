"""KD-UI-007: reuse the owned clone/backup/apply chain; evidence remains under .local."""
# ruff: noqa: T201, PLC0415
import argparse
import json
import sys
from pathlib import Path

import kd_ui005 as previous

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/kd-ui007'
SOURCE = BASE / 'source/custom_addons'
MODULE = 'tp_kd_workspace'


def bind():
    previous.BASE = BASE
    previous.DATABASE = 'tp_tanphat_kdui007_20261107'
    previous.PORT = 18889
    previous.SOURCE = SOURCE
    return previous.bind()


def inventory(native, label):
    def read(env):
        from lxml import etree
        result = []
        models = [
            'crm.lead', 'project.project', 'project.task', 'tp.contract', 'tp.contract.revision',
            'tp.contract.line', 'tp.contract.document', 'tp.contract.line.amount', 'tp.contract.audit',
            'tp.contract.submission', 'tp.approval.reference', 'tp.allocation', 'tp.production',
            'tp.acceptance', 'tp.payment.request', 'tp.periodic.plan', 'tp.credential', 'tp.obligation',
            'tp.contract.native.draft', 'tp.contract.native.amendment', 'tp.contract.native.return']
        views = env['ir.ui.view'].search([('model', 'in', models), ('type', 'in', ['list', 'form']),
            ('mode', '=', 'primary')])
        for view in views:
            xmlid = view.get_external_id().get(view.id, '')
            if not xmlid.startswith(('tp_kd_workspace.', 'tp_contract.', 'tp_project.')):
                continue
            # The manager-only assignment notebook is absent from an unqualified superuser arch.
            credentials = native.read(ROOT / '.local/kd-native001/dataset/dev/credentials.json')
            planner = env['res.users'].search([('login', '=', credentials['planner']['login'])], limit=1)
            editor = env['res.users'].search([('login', '=', credentials['editor']['login'])], limit=1)
            actor = planner if view.model == 'project.project' else editor
            arch = env[view.model].with_user(actor).get_view(view.id, view.type)['arch']
            folder = BASE / f'arch-{label}'
            folder.mkdir(exist_ok=True)
            (folder / f'{xmlid}.xml').write_text(arch, encoding='utf-8')
            tree = etree.fromstring(arch.encode())
            tables = []
            for table in tree.iter('list', 'table'):
                parent = table.getparent()
                relation = parent.get('name') if parent is not None and parent.tag == 'field' else ''
                ancestors = [node.get('name') for node in table.iterancestors('field') if node.get('name')]
                relation_path = '.'.join(reversed(ancestors))
                table_model = view.model
                for name in reversed(ancestors):
                    table_model = env[table_model]._fields[name].comodel_name
                metadata = env[table_model].with_user(actor).fields_get(
                    attributes=['type', 'searchable', 'string', 'selection'])
                tables.append({'relation': relation_path or relation, 'fields': [f.get('name') for f in table.findall('field')],
                               'editable': table.get('editable'), 'widget': parent.get('widget') if relation else '',
                               'js_class': table.get('js_class'), 'table_model': table_model,
                               'metadata': {f.get('name'): metadata.get(f.get('name'), {}) for f in table.findall('field')}})
            result.append({'xmlid': xmlid, 'model': view.model, 'type': view.type, 'tables': tables})
        return result
    result = native.orm('clone', read)
    native.write(BASE / f'inventory-{label}.json', result)
    print(json.dumps({'views': len(result), 'tables': sum(len(v['tables']) for v in result)}))


def fixture(native):
    native.target_config('clone')
    native.require(not (BASE / 'fixture.json').exists(), 'Fixture already created; reuse it.')

    def create(env):
        creds = native.read(ROOT / '.local/kd-native001/dataset/dev/credentials.json')
        users = {key: env['res.users'].search([('login', '=', value['login'])], limit=1)
                 for key, value in creds.items()}
        grant = env['tp.kd.grant'].search([('user_id', '=', users['editor'].id),
                                          ('domain', '=', 'allocation'), ('capability', '=', 'prepare')], limit=1)
        project = grant.project_id
        contract = env['tp.contract'].search([('project_id', '=', project.id)], limit=1)
        leads = env['crm.lead'].create([{
            'name': f'UI007-PAGE-{i:03d} — kiểm phân trang', 'type': 'opportunity',
            'tp_project_id': project.id, 'company_id': project.company_id.id, 'user_id': users['editor'].id,
            'partner_id': project.partner_id.id, 'kd_route': 'bid',
        } for i in range(118)])
        allocation = env['tp.allocation'].create({
            'code': 'UI007-PARENT', 'name': 'UI007 — Quan hệ 18 dòng kiểm phân trang',
            'project_id': project.id, 'owner_id': users['editor'].id, 'reviewer_id': users['reviewer'].id,
            'scope': 'Giả lập test-only, không dữ liệu thật', 'allocation_kind': 'internal',
            'contract_id': contract.id,
            'recipient_department_id': project.tp_department_id.id,
        })
        children = env['tp.allocation'].create([{
            'code': f'UI007-CHILD-{i:02d}', 'name': f'UI007 — Khoán con {i:02d}',
            'project_id': project.id, 'owner_id': users['editor'].id, 'reviewer_id': users['reviewer'].id,
            'scope': 'Giả lập test-only', 'allocation_kind': 'internal', 'parent_id': allocation.id,
            'contract_id': contract.id,
            'recipient_department_id': project.tp_department_id.id,
        } for i in range(18)])
        result = {'leads': leads.ids, 'project': project.id, 'allocation': allocation.id, 'children': children.ids}
        env.cr.commit()
        return result
    native.write(BASE / 'fixture.json', native.orm('clone', create))
    print('FIXTURE: 118 opportunities and 18 related rows on owned clone only.')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'start', 'stop', 'upgrade', 'test', 'inventory',
                                           'preserve', 'extended', 'backup', 'seal', 'apply', 'rollback', 'fixture'])
    parser.add_argument('--label', default='before')
    args = parser.parse_args()
    native = bind()
    if args.command == 'prepare':
        previous.previous.prepare(native)
    elif args.command in ('start', 'stop'):
        native.runtime(args.command)
    elif args.command == 'upgrade':
        return previous.previous.upgrade(native)
    elif args.command == 'test':
        result = previous.kd.tests('tp_kd_workspace,tp_contract', '/tp_kd_workspace,/tp_contract')
        if result == 0:
            native.write(BASE / 'tested-source.json', previous.hashes())
        return result
    elif args.command == 'inventory':
        inventory(native, args.label)
    elif args.command == 'fixture':
        fixture(native)
    elif args.command == 'preserve':
        previous.preservation(native, args.label)
    elif args.command == 'extended':
        previous.extended_preservation(native, args.label)
    elif args.command == 'backup':
        previous.previous.backup(native)
    elif args.command == 'seal':
        native.require(native.read(BASE / 'tested-source.json') == previous.hashes(), 'Source changed since tests.')
        for filename in ('browser-result.json', 'hoot-result.json', 'regression-result.json', 'zoom-result.json'):
            result = native.read(BASE / filename)
            native.require(result.get('passed') and not result.get('failures') and not result.get('errors'), filename)
            native.require(result['source_hashes'] == previous.hashes(), 'Browser tested different source.')
        native.write(BASE / 'sealed-source.json', previous.hashes())
        print('SEALED: exact source passed Odoo, HOOT, browser and regression.')
    elif args.command == 'apply':
        from datetime import UTC, datetime
        owner = native.read(BASE / 'owner.json')
        backup = Path(owner['pre_apply_backup'])
        native.require(backup.resolve().is_relative_to(BASE.resolve()), 'Foreign backup.')
        native.require(0 <= datetime.now(UTC).timestamp() - (backup / 'manifest.json').stat().st_mtime < 900,
                       'Fresh verified backup required.')
        native.require(native.read(BASE / 'sealed-source.json') == previous.hashes(), 'Source differs from seal.')
        native.require(previous.previous.previous.tree_hashes(BASE / 'baseline_addon') ==
                       previous.previous.previous.tree_hashes(ROOT / 'custom_addons' / MODULE),
                       'Main addon changed since snapshot.')
        previous.previous.previous.apply(native)
    else:
        target = (ROOT / 'custom_addons' / MODULE).resolve()
        native.require(target == Path('C:/TANPHAT ONE/custom_addons/tp_kd_workspace').resolve(), 'Unsafe rollback.')
        previous.previous.previous.rollback(native)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
