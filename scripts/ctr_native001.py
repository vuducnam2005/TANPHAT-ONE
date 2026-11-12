"""Synthetic browser fixtures for UI-CTR-NATIVE-001a, on the verified owned clone only."""
# This CLI keeps credentials in the existing private operation folder.
# ruff: noqa: T201, PLC0415
import json
import secrets

import native_stabilize001 as stabilize


def seed(env):
    from odoo import Command
    from odoo.tools import BinaryBytes

    stabilize.native.isolate_mail(env)
    ns = 'tp_ctr_native001'
    root = stabilize.BASE / 'ctr-native001'
    root.mkdir(exist_ok=True)
    credential_path = root / 'credentials.json'
    credentials = json.loads(credential_path.read_text()) if credential_path.exists() else {}

    def bind(key, record):
        env['ir.model.data'].create({'module': ns, 'name': key, 'model': record._name, 'res_id': record.id})
        return record

    def get(key, model, values):
        return env.ref(f'{ns}.{key}', raise_if_not_found=False) or bind(key, env[model].create(values))

    company = env.company
    department = get('department', 'hr.department', {'name': 'Kế hoạch hợp đồng — dữ liệu giả', 'company_id': company.id})
    currency = env.ref('base.VND')
    currency.active = True
    project = get('project', 'project.project', {
        'name': 'Cầu An Bình — kiểm thử UI Contracts', 'tp_code': 'CTR-NATIVE-TEST-001', 'tp_managed': True,
        'company_id': company.id, 'tp_department_id': department.id, 'privacy_visibility': 'employees',
    })
    capabilities = {
        'editor': ('contract_draft_edit', 'contract_submit', 'financial_read', 'financial_draft_edit'),
        'reviewer': ('contract_review_commercial', 'financial_read'),
        'metadata': ('contract_draft_edit',), 'reader': (), 'outsider': (),
    }
    users = {}
    for role, caps in capabilities.items():
        credential = credentials.setdefault(role, {'login': f'ctr_native001_{role}', 'password': secrets.token_urlsafe(24)})
        user = get('user_' + role, 'res.users', {
            'name': f'Kiểm thử hợp đồng — {role}', 'login': credential['login'], 'password': credential['password'],
            'company_id': company.id, 'company_ids': [Command.set(company.ids)],
            'group_ids': [Command.set([env.ref('tp_core.group_user').id])],
            'lang': 'vi_VN', 'tz': 'Asia/Ho_Chi_Minh',
        })
        users[role] = user
        if role != 'outsider':
            get('assignment_' + role, 'tp.project.assignment', {'project_id': project.id, 'user_id': user.id})
        for cap in caps:
            values = {'project_id': project.id, 'user_id': user.id, 'capability': cap, 'reason': 'Synthetic UI-CTR-NATIVE-001a fixture'}
            if cap != 'financial_read':
                values['department_id'] = department.id
            get(f'grant_{role}_{cap}', 'tp.project.grant', values)
    contract = env.ref(f'{ns}.contract', raise_if_not_found=False)
    if not contract:
        result = env['tp.contract.workflow'].with_user(users['editor'])._tp_run('create_contract', {
            'project_id': project.id, 'code': 'HD-NATIVE-MAU-001', 'name': 'Hợp đồng khảo sát cầu An Bình (giả lập)',
            'contract_type': 'owner', 'currency': 'VND', 'revision': {'name': 'Bản gốc — kiểm thử'},
            'lines': [{'scope_key': 'KS', 'name': 'Khảo sát địa hình',
                       'amount': {'state': 'confirmed', 'value': '7654321', 'tax_basis': 'excluding_tax'}}],
        }, key='native-fixture-' + secrets.token_hex(16))
        contract = bind('contract', result['contract'])
        bind('revision', result['revision'])
        for key, confidentiality in [('general', 'general'), ('financial', 'financial')]:
            bind('document_' + key, env['tp.contract.document'].create({
                'contract_id': contract.id, 'revision_id': result['revision'].id,
                'name': f'Hồ sơ {key} — giả lập', 'document_kind': 'technical_scope' if key == 'general' else 'signed_contract',
                'confidentiality': confidentiality, 'file_name': f'{key}-synthetic.txt', 'file': BinaryBytes(b'Synthetic fixture only'),
            }))
    stabilize.native.isolate_mail(env)
    # Committed only after the ownership guard in native.orm('clone', ...) passed.
    env.cr.commit()
    credential_path.write_text(json.dumps(credentials, indent=2), encoding='utf-8')
    evidence = {'database': stabilize.DATABASE, 'port': stabilize.PORT, 'project_id': project.id,
                'contract_id': contract.id, 'revision_id': env.ref(f'{ns}.revision').id,
                'documents': {key: env.ref(f'{ns}.document_{key}').id for key in ('general', 'financial')},
                'users': {k: v.id for k, v in users.items()},
                'list_action': env.ref('tp_contract.action_tp_contracts').id,
                'credentials': str(credential_path.relative_to(stabilize.ROOT))}
    (root / 'fixture.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print(json.dumps(evidence))


if __name__ == '__main__':
    stabilize.bind()
    stabilize.native.orm('clone', seed)
