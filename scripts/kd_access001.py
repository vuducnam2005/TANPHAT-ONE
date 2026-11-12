"""KD-ACCESS-001: exact, private, ORM-only dev account delta after clone rehearsal.

No application code changes or module upgrades. CRM access is withheld because
its current prepare capability cannot enforce owner-only drafting/no submission.
"""
# ruff: noqa: T201, PLC0415, S603
import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import kd_ui002 as runtime
import kd_ui003 as backup_runtime

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/kd-access001'
DATABASE = 'tp_tanphat_kdaccess001_20261108'
PORT = 18989
SOURCE = BASE / 'source/custom_addons'
DOMAINS = ['allocation', 'production', 'acceptance', 'payment', 'plan', 'credential', 'obligation']
POLICY = {
    'head': (['financial_read', 'contract_review_commercial'], DOMAINS, ['review']),
    'deputy': (['financial_read', 'financial_draft_edit', 'contract_draft_edit', 'contract_submit',
                'contract_review_commercial'], DOMAINS, ['prepare', 'submit', 'review']),
    'project_lead': (['financial_read', 'financial_draft_edit', 'contract_draft_edit', 'contract_submit',
                      'contract_review_commercial'], DOMAINS, ['prepare', 'submit', 'review']),
    'planning': (['financial_read', 'financial_draft_edit'], ['allocation', 'production', 'plan', 'credential'],
                 ['prepare', 'submit']),
    'support': ([], ['credential'], ['prepare']),
}
REASON = 'KD-ACCESS-001: direct user request, dev demonstration only; not Q2/pilot authorization. Technical operator: superuser.'


def bind():
    runtime.BASE, runtime.DATABASE, runtime.PORT, runtime.SOURCE = BASE, DATABASE, PORT, SOURCE
    backup_runtime.BASE = BASE
    return runtime.bind()


def private(native):
    native.private_root()
    if os.name == 'nt':
        sid = subprocess.check_output(['whoami', '/user', '/fo', 'csv', '/nh'], text=True).strip().split(',')[1].strip('"')
        subprocess.run(['icacls', str(BASE), '/inheritance:r', '/grant:r', f'*{sid}:(OI)(CI)F',
                        '*S-1-5-18:(OI)(CI)F', '*S-1-5-32-544:(OI)(CI)F'], check=True, capture_output=True)


def hashes():
    return runtime.tree_hashes(SOURCE)


def mapping(native):
    result = native.read(BASE / 'staff-map.json')
    native.require(result['task'] == 'KD-ACCESS-001', 'Wrong task mapping.')
    staff = result['staff']
    native.require({s['alias'] for s in staff} == set(POLICY) and len(staff) == 5, 'Need five unique aliases.')
    native.require(len({s['proposed_login'] for s in staff}) == 5, 'Duplicate login.')
    return staff


def projects(env, native):
    registry = env['tp.kd.dataset'].search([('name', '=', 'KD_NATIVE_001_REALISTIC_V1')])
    native.require(len(registry) == 1 and registry.namespace == 'tp_kd_native001_realistic_v1', 'Dataset identity differs.')
    entries = registry.entry_ids.filtered(lambda e: e.model == 'project.project' and e.category == 'projects' and e.status == 'present')
    records = env['project.project'].browse(entries.mapped('res_id')).exists()
    native.require(len(records) == 8 and len(entries) == 8 and all(entries.mapped('owned')), 'Expected eight owned registry projects.')
    for entry in entries:
        native.require(env.ref(entry.external_id).id == entry.res_id, 'Registry/XMLID mismatch.')
    expected = {code for s in mapping(native) for code in s['project_codes']}
    native.require(set(records.mapped('tp_code')) == expected and len(records.company_id) == 1
                   and len(records.tp_department_id) == 1 and all(records.mapped('tp_managed')),
                   'Registry company/department/code mismatch.')
    return {p.tp_code: p for p in records}


def credentials(native, target):
    path = BASE / f'{target}-credentials.json'
    if path.exists():
        return native.read(path)
    native.require(not (BASE / f'{target}-delta.json').exists(), 'Existing account credentials missing; no reset or replacement.')
    result = {s['alias']: {'login': s['proposed_login'] if target == 'dev' else 'kd_access001_' + s['alias'],
                           'password': secrets.token_urlsafe(27)} for s in mapping(native)}
    native.write(path, result)
    return result


def identity(env):
    return {'database': env.cr.dbname, 'uuid': env['ir.config_parameter'].get_str('database.uuid')}


def account_digest(env, ids=None):
    from psycopg2 import sql
    result = {}
    for table in ['res_users', 'res_groups_users_rel', 'res_company_users_rel', 'tp_project_assignment',
                  'tp_project_grant', 'tp_kd_grant']:
        query = sql.SQL('SELECT * FROM {} ORDER BY 1').format(sql.Identifier(table))
        env.cr.execute(query)
        rows = env.cr.fetchall()
        names = [d[0] for d in env.cr.description]
        if ids:
            key = 'id' if table == 'res_users' else 'uid' if 'uid' in names else 'user_id'
            if key in names:
                rows = [r for r in rows if r[names.index(key)] in ids]
        result[table] = hashlib.sha256(repr(sorted(rows, key=repr)).encode()).hexdigest()
    return result


def provision(env, native, target, commit=False):
    from odoo import Command
    native.isolate_mail(env)
    all_projects = projects(env, native)
    credential = credentials(native, target)
    marker_path = BASE / f'{target}-delta.json'
    old = native.read(marker_path) if marker_path.exists() else None
    if old:
        native.require(old['identity'] == identity(env), 'Provenance identity mismatch.')
        for alias, row in old['users'].items():
            user = env['res.users'].browse(row['id']).exists()
            native.require(user and user.login == credential[alias]['login'] and user.partner_id.id == row['partner_id'],
                           'Account provenance mismatch; never adopt/reset.')
            native.require(user.active and user.company_ids.ids == [row['company_id']], 'Existing account scope/active drift.')
            group = env.ref('tp_kd_workspace.group_scoped_staff')
            if group not in user.group_ids:
                native.require(target == 'clone', 'Existing dev group drift; explicit review required.')
                user.group_ids = [Command.set(group.ids)]
                row['groups'] = user.all_group_ids.ids
        for model, key in [('tp.project.assignment', 'assignments'), ('tp.project.grant', 'project_grants'), ('tp.kd.grant', 'kd_grants')]:
            records = env[model].with_context(active_test=False).browse(old[key]).exists()
            native.require(len(records) == len(old[key]) and all(records.mapped('active')), 'Existing delta revoked/missing; no silent repair.')
        if commit:
            native.write(marker_path, old)
            env.cr.commit()
        return old
    users_model = env['res.users'].with_context(active_test=False)
    native.require(not users_model.search_count([('login', 'in', [c['login'] for c in credential.values()])]),
                   'Login conflict, no account adoption/reset allowed.')
    old_ids = users_model.search([]).ids
    before = account_digest(env, old_ids)
    delta = {'task': 'KD-ACCESS-001', 'identity': identity(env), 'reason': REASON, 'old_user_ids': old_ids,
             'old_accounts_before': before, 'users': {}, 'assignments': [], 'project_grants': [], 'kd_grants': [],
             'source_hashes': hashes(), 'created_at': datetime.now(UTC).isoformat()}
    for staff in mapping(native):
        alias = staff['alias']
        scope = [all_projects[c] for c in staff['project_codes']]
        company, department = scope[0].company_id, scope[0].tp_department_id
        user = users_model.with_context(tracking_disable=True, mail_create_nolog=True, mail_create_nosubscribe=True,
                                       no_reset_password=True).create({
            'name': staff['display_name'] if target == 'dev' else 'KD access test — ' + alias,
            **credential[alias], 'active': True, 'company_id': company.id, 'company_ids': [Command.set(company.ids)],
            'group_ids': [Command.set(env.ref('tp_kd_workspace.group_scoped_staff').ids)], 'lang': 'vi_VN',
            'tz': 'Asia/Ho_Chi_Minh', 'email': False, 'action_id': env.ref('tp_web_home.action_home').id,
            'odoobot_state': 'disabled',
        })
        delta['users'][alias] = {'id': user.id, 'partner_id': user.partner_id.id, 'login': user.login,
                                  'company_id': company.id, 'department_id': department.id,
                                  'projects': [p.id for p in scope], 'codes': staff['project_codes'],
                                  'groups': user.all_group_ids.ids}
        delta['users'][alias]['onboarding_tasks'] = env['project.task'].search([
            ('user_ids', 'in', user.ids), ('project_id', '=', False)]).ids
        delta['users'][alias]['personal_stages'] = env['project.task.type'].search([('user_id', '=', user.id)]).ids
        for project in scope:
            a = env['tp.project.assignment'].create({'project_id': project.id, 'user_id': user.id, 'role': 'reader'})
            delta['assignments'].append(a.id)
            caps, domains, actions = POLICY[alias]
            for cap in caps:
                g = env['tp.project.grant'].create({'project_id': project.id, 'user_id': user.id, 'capability': cap,
                    'department_id': False if cap == 'financial_read' else department.id,
                    'reason': REASON, 'granted_by_id': env.ref('base.user_root').id})
                delta['project_grants'].append(g.id)
            for domain in domains:
                for action in actions:
                    g = env['tp.kd.grant'].create({'project_id': project.id, 'user_id': user.id,
                        'department_id': department.id, 'domain': domain, 'capability': action, 'reason': REASON})
                    delta['kd_grants'].append(g.id)
    after = account_digest(env, old_ids)
    native.require(after == before, 'Existing account metadata changed in: ' + ', '.join(t for t in before if before[t] != after[t]))
    if commit:
        # Write provenance before commit; if commit fails, retain it for diagnosis, never reset accounts.
        native.write(marker_path, delta)
        env.cr.commit()
    return delta


def audit(env, native, target, delta, *, crm_scope=False, check_historical=True):
    from odoo.exceptions import AccessDenied, AccessError, UserError
    from odoo.service.model import call_kw
    checks = []

    def check(name, value):
        native.require(bool(value), name)
        checks.append(name)

    def denied(name, fn):
        try:
            with env.cr.savepoint():
                fn()
        except (AccessDenied, AccessError, UserError):
            checks.append(name)
            return
        raise AssertionError(name + ': unexpectedly permitted')

    all_projects = projects(env, native)
    all_ids = [p.id for p in all_projects.values()]
    for alias, row in delta['users'].items():
        user = env['res.users'].browse(row['id'])
        actor = env(user=user, su=False)
        ids = row['projects']
        check(alias + ' exact managed project scope', set(actor['project.project'].search([]).ids) == set(ids))
        check(alias + ' project relation scope', {r[0] for r in actor['project.project'].name_search('')} == set(ids))
        check(alias + ' own company', user.company_ids.ids == [row['company_id']])
        check(alias + ' language/timezone', user.lang == 'vi_VN' and user.tz == 'Asia/Ho_Chi_Minh')
        check(alias + ' internal', user.has_group('base.group_user') and not user.share)
        for group in ['base.group_system', 'tp_core.group_manager', 'project.group_project_manager',
                      'sales_team.group_sale_salesman_all_leads', 'sales_team.group_sale_salesman',
                      'account.group_account_user', 'hr.group_hr_user']:
            check(alias + ' absent ' + group, not user.has_group(group))
        if crm_scope:
            check(alias + ' CRM available', actor['crm.lead'].has_access('read'))
            leads = call_kw(actor['crm.lead'], 'search_read', [], {'fields': ['name', 'tp_project_id']})
            check(alias + ' CRM project scope', all(not r['tp_project_id'] or r['tp_project_id'][0] in ids for r in leads))
            if alias == 'support':
                denied(alias + ' CRM money RPC denied', lambda: call_kw(actor['crm.lead'], 'search_read', [], {'fields': ['expected_revenue']}))
        else:
            check(alias + ' CRM denied', not actor['crm.lead'].has_access('read'))
            denied(alias + ' CRM direct RPC', lambda: call_kw(actor['crm.lead'], 'search_read', [], {'fields': ['name', 'expected_revenue']}))
        denied(alias + ' grant management', lambda: actor['tp.kd.grant'].create({
            'project_id': ids[0], 'department_id': row['department_id'], 'user_id': user.id,
            'domain': 'payment', 'capability': 'prepare', 'reason': 'forged'}))
        caps, domains, actions = POLICY[alias]
        for pid in all_ids:
            project = env['project.project'].browse(pid)
            for cap in ['financial_read', 'financial_draft_edit', 'contract_draft_edit', 'contract_submit', 'contract_review_commercial']:
                expected = pid in ids and cap in caps
                check(f'{alias} project {pid} {cap}', actor['tp.project.grant']._tp_has_capability(
                    project, cap, project.tp_department_id if cap != 'financial_read' else None) == expected)
            for domain in DOMAINS + ['opportunity']:
                for action in ['prepare', 'submit', 'review']:
                    expected = pid in ids and domain in domains and action in actions
                    if crm_scope and domain == 'opportunity':
                        expected = pid in ids and (action == 'prepare' or (action == 'submit' and alias != 'support'))
                    check(f'{alias} project {pid} {domain}/{action}', actor['tp.kd.grant']._has(project, domain, action) == expected)
        for model in ['tp.contract', 'tp.contract.revision', 'tp.allocation', 'tp.production', 'tp.acceptance',
                      'tp.payment.request', 'tp.periodic.plan', 'tp.credential', 'tp.obligation']:
            records = actor[model].search([])
            check(alias + ' records ' + model, set(records.project_id.ids) <= set(ids))
            grouped = actor[model].read_group([], ['project_id'], ['__count'])
            check(alias + ' group ' + model, all(r[0] in ids for r in grouped if r[0]))
            outside = env[model].search([('project_id', 'not in', ids)], limit=1)
            if outside:
                denied(alias + ' direct read ' + model, lambda m=outside: m.with_user(user).read(['name']))
                denied(alias + ' export ' + model, lambda m=outside: m.with_user(user).export_data(['name']))
        payload = actor['tp.kd.overview'].get_kd_dashboard()
        check(alias + ' dashboard available', bool(payload))
        if alias == 'support':
            for model in ['tp.contract.line.amount', 'tp.contract.submission.amount', 'tp.allocation.amount',
                          'tp.production.amount', 'tp.acceptance.amount', 'tp.payment.request.amount',
                          'tp.periodic.plan.amount', 'tp.allocation.event.amount']:
                check('support no money search ' + model, not actor[model].search_count([]))
                record = env[model].search([], limit=1)
                if record:
                    field = 'value' if 'value' in record._fields else 'financial_snapshot' if 'financial_snapshot' in record._fields else 'amount'
                    denied('support no money read ' + model, lambda r=record, f=field: r.with_user(user).read([f]))
                    denied('support no money export ' + model, lambda r=record, f=field: r.with_user(user).export_data([f]))
            docs = actor['tp.contract.document'].search([])
            check('support financial document hidden', not docs.filtered(lambda d: d.confidentiality != 'general'))
    if check_historical:
        current = account_digest(env, delta['old_user_ids'])
        check('old accounts/groups/passwords preserved', all(current[t] == delta['old_accounts_before'][t] for t in current))
    return checks


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'start', 'stop', 'provision', 'audit', 'backup', 'test', 'rehearse', 'seal', 'apply-security', 'rollback', 'preserve', 'normalize-timezone', 'file-fixture', 'file-lifecycle'])
    parser.add_argument('--target', choices=['clone', 'dev'], default='clone')
    parser.add_argument('--label', default='before')
    args = parser.parse_args()
    native = bind()
    private(native)
    if args.command == 'prepare':
        runtime.prepare(native)
    elif args.command == 'file-lifecycle':
        native.require(args.target == 'clone', 'File lifecycle is clone-only.')
        delta = native.read(BASE / 'clone-delta.json')
        fixture = native.read(BASE / 'file-fixture.json')

        def set_phase(env, phase):
            uid = delta['users']['head']['id']
            grant = env['tp.project.grant'].search([('id', 'in', delta['project_grants']), ('user_id', '=', uid),
                ('project_id', '=', fixture['project_id']), ('capability', '=', 'financial_read')])
            assignment = env['tp.project.assignment'].with_context(active_test=False).search([
                ('id', 'in', delta['assignments']), ('user_id', '=', uid), ('project_id', '=', fixture['project_id'])])
            # Include an inactive exact-owned grant when restoring after the revoke phase.
            if not grant:
                grant = env['tp.project.grant'].with_context(active_test=False).search([
                    ('id', 'in', delta['project_grants']), ('user_id', '=', uid),
                    ('project_id', '=', fixture['project_id']), ('capability', '=', 'financial_read')])
            native.require(len(grant) == len(assignment) == 1, 'File fixture exact rights mismatch.')
            grant.write({'active': phase != 'revoked', 'date_end': '2000-01-01' if phase == 'expired' else False})
            assignment.active = phase != 'unassigned'
            env.cr.commit()
        try:
            for phase in ['normal', 'revoked', 'expired', 'unassigned']:
                native.orm('clone', lambda env: set_phase(env, phase))
                completed = subprocess.run(['node', str(ROOT / 'scripts/kd_access001_files.cjs'), phase], cwd=ROOT, check=False)
                native.require(completed.returncode == 0, 'HTTP file phase failed: ' + phase)
        finally:
            native.orm('clone', lambda env: set_phase(env, 'normal'))
    elif args.command == 'file-fixture':
        from odoo.tools.binary import BinaryBytes
        native.require(args.target == 'clone', 'Financial file fixture is clone-only.')
        path = BASE / 'file-fixture.json'
        native.require(not path.exists(), 'Fixture exists; reuse exact journal.')

        def fixture(env):
            project = projects(env, native)['KD26-ANP']
            contract = env['tp.contract'].search([('project_id', '=', project.id)], limit=1)
            native.require(contract, 'Need owned synthetic contract.')
            content = b'KD_ACCESS001_SYNTHETIC_FINANCIAL_987654321'
            doc = env['tp.contract.document'].create({'contract_id': contract.id, 'name': 'Synthetic private financial probe',
                'document_kind': 'other', 'confidentiality': 'financial', 'file_name': 'synthetic-financial.txt',
                'file': BinaryBytes(content)})
            attachment = env['ir.attachment'].search([('res_model', '=', doc._name), ('res_id', '=', doc.id), ('res_field', '=', 'file')])
            result = {'document_id': doc.id, 'attachment_ids': attachment.ids, 'project_id': project.id,
                      'content_sha256': hashlib.sha256(content).hexdigest()}
            native.write(path, result)
            env.cr.commit()
            return result
        result = native.orm('clone', fixture)
        print(json.dumps({'clone_financial_document': result['document_id'], 'attachments': len(result['attachment_ids'])}))
    elif args.command in ['start', 'stop']:
        native.runtime(args.command)
    elif args.command == 'backup':
        backup_runtime.backup(native)
    elif args.command == 'normalize-timezone':
        delta = native.read(BASE / f'{args.target}-delta.json')

        def normalize(env):
            native.require(delta['identity'] == identity(env), 'Account environment mismatch.')
            for row in delta['users'].values():
                user = env['res.users'].browse(row['id'])
                native.require(user.login == row['login'] and user.partner_id.id == row['partner_id'] and
                               user.tz in ['Asia/Saigon', 'Asia/Ho_Chi_Minh'], 'Account/timezone drift.')
                # Odoo adopts the browser's equivalent Asia/Saigon alias at the first login.
                user.tz = 'Asia/Ho_Chi_Minh'
            env.cr.commit()
        native.orm(args.target, normalize)
        print('Five owned account timezones normalized after first native login; passwords untouched.')
    elif args.command == 'preserve':
        from collections import Counter
        from contextlib import closing
        native.target_config('dev')
        with closing(native.connect('tp_tanphat_dev')) as connection, connection.cursor() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND "
                           "(tablename LIKE 'tp\\_%%' ESCAPE '\\' OR tablename LIKE 'project\\_%%' ESCAPE '\\' "
                           "OR tablename IN ('crm_lead','res_users','res_partner','res_company','hr_employee','hr_department',"
                           "'account_move','account_payment','hr_expense','res_groups_users_rel','res_company_users_rel'))")
            runtime.PRESERVED = sorted(r[0] for r in cursor.fetchall())
        result = runtime.rowset(native, 'tp_tanphat_dev')
        native.write(BASE / f'preservation-{args.label}.json', result)
        if args.label != 'before':
            before = native.read(BASE / 'preservation-before.json')
            report = runtime.compare(before, result)
            allowed = {'res_users': 5, 'res_partner': 5, 'res_groups_users_rel': 5, 'res_company_users_rel': 5,
                       'tp_project_assignment': 22, 'tp_project_grant': 64, 'tp_kd_grant': 258,
                       'project_task': 5, 'project_task_type': 35, 'project_task_user_rel': 5}
            native.write(BASE / f'preservation-{args.label}-diff.json', report)
            native.require(all(not v['missing_or_changed'] and v['added'] == allowed.get(t, 0)
                               for t, v in report.items()), 'Unexpected business/account delta; inspect private diff.')
        print(json.dumps({'label': args.label, 'tables': len(result), 'rows': sum(sum(Counter(v['hashes']).values()) for v in result.values()), 'verified': True}))
    elif args.command == 'seal':
        from datetime import timedelta
        logs = sorted((BASE / 'odoo-tests').glob('*.json'))
        native.require(logs and native.read(logs[-1])['ok'], 'No green clone Odoo result.')
        # The source has not been edited since this test started. This also supports interrupted runs.
        stamp = datetime.strptime(logs[-1].stem, '%Y%m%dT%H%M%S%fZ').replace(tzinfo=UTC)
        cutoff = (stamp + timedelta(seconds=1)).timestamp()
        native.require(all(p.stat().st_mtime <= cutoff for p in SOURCE.rglob('*') if p.is_file()
                           and '__pycache__' not in p.parts and p.suffix != '.pyc'), 'Source edited after test start.')
        for label in ['clone-audit', 'clone-rehearsal', 'clone-browser']:
            report = native.read(BASE / (label + '.json'))
            native.require(report['passed'] and not report.get('failures') and not report.get('errors'), label + ' failed.')
            if 'source_hashes' in report:
                native.require(report['source_hashes'] == hashes(), label + ' source differs.')
        native.write(BASE / 'tested-source.json', hashes())
        print('SEALED: clone source, Odoo, role audit, rollback rehearsal and five browser sessions passed.')
    elif args.command == 'apply-security':
        import zipfile
        native.require(native.read(BASE / 'tested-source.json') == hashes(), 'Source seal mismatch.')
        owner = native.read(BASE / 'owner.json')
        backup = Path(owner['pre_apply_backup'])
        native.require(backup.resolve().is_relative_to(BASE.resolve()) and
                       datetime.now(UTC).timestamp() - (backup / 'manifest.json').stat().st_mtime < 900,
                       'Fresh verified backup required.')
        # Check main source against this task snapshot; do not overwrite intervening edits.
        with zipfile.ZipFile(Path(owner['snapshot']) / 'maintained-source.zip') as archive:
            baseline = {name.removeprefix('custom_addons/'): hashlib.sha256(archive.read(name)).hexdigest()
                        for name in archive.namelist() if name.startswith('custom_addons/')}
        native.require(runtime.tree_hashes(ROOT / 'custom_addons') == baseline, 'Main addon drift since task snapshot.')
        runtime.apply(native)
        native.require(runtime.tree_hashes(ROOT / 'custom_addons') == hashes(), 'Applied source mismatch.')
    elif args.command == 'rollback':
        # Preserve accounts/audit, revoke this task's exact IDs only. No unlink or whole-DB restore.
        delta = native.read(BASE / f'{args.target}-delta.json')

        def revoke(env):
            native.require(delta['identity'] == identity(env), 'Rollback identity mismatch.')
            for model, key in [('tp.project.assignment', 'assignments'), ('tp.project.grant', 'project_grants'), ('tp.kd.grant', 'kd_grants')]:
                records = env[model].browse(delta[key]).exists()
                native.require(set(records.user_id.ids) <= {u['id'] for u in delta['users'].values()}, 'Foreign grant in delta.')
                records.write({'active': False})
            for row in delta['users'].values():
                user = env['res.users'].browse(row['id'])
                native.require(user.login == row['login'] and user.partner_id.id == row['partner_id'], 'Foreign user in rollback.')
                user.active = False
            env.cr.commit()
        native.orm(args.target, revoke)
        print('ROLLED BACK: exact task users archived and grants/assignments revoked; history preserved.')
    elif args.command == 'test':
        result = runtime.kd.tests('tp_kd_workspace,tp_contract', '/tp_kd_workspace,/tp_contract')
        if result == 0:
            native.write(BASE / 'tested-source.json', hashes())
        return result
    elif args.command == 'rehearse':
        from kd_access001_checks import rehearse
        native.require(args.target == 'clone', 'Mutation rehearsal is clone-only.')
        delta = native.read(BASE / 'clone-delta.json')

        def probe(env):
            before = account_digest(env)
            initial = provision(env, native, 'clone')
            native.require(initial == delta and account_digest(env) == before, 'Idempotency/password preservation failed.')
            checks = rehearse(env, native, delta)
            env.cr.rollback()
            native.require(account_digest(env) == before, 'Rollback rowsets differ.')
            return checks + ['provision rerun/password unchanged', 'mutation and rollback probes fully rolled back']
        checks = native.orm('clone', probe)
        native.write(BASE / 'clone-rehearsal.json', {'passed': len(checks), 'checks': checks, 'source_hashes': hashes()})
        print(json.dumps({'passed': len(checks), 'rolled_back': True}))
    elif args.command == 'provision':
        if args.target == 'dev':
            report = native.read(BASE / 'clone-audit.json')
            browser = native.read(BASE / 'clone-browser.json')
            rehearsal = native.read(BASE / 'clone-rehearsal.json')
            owner = native.read(BASE / 'owner.json')
            backup = Path(owner['pre_apply_backup'])
            native.require(report['passed'] and browser['passed'] and rehearsal['passed'] and
                           report['source_hashes'] == hashes() == rehearsal['source_hashes'] == native.read(BASE / 'tested-source.json'),
                           'Clone gate/source mismatch.')
            native.require(runtime.tree_hashes(ROOT / 'custom_addons') == hashes(), 'Dev source differs from tested clone.')
            if not (BASE / 'dev-delta.json').exists():
                native.require(backup.resolve().is_relative_to(BASE.resolve()) and
                               datetime.now(UTC).timestamp() - (backup / 'manifest.json').stat().st_mtime < 900,
                               'Fresh verified backup required.')

        def apply_accounts(env):
            rerun = (BASE / f'{args.target}-delta.json').exists()
            before = account_digest(env) if rerun else None
            result = provision(env, native, args.target, commit=True)
            if rerun:
                native.require(account_digest(env) == before, 'Rerun changed accounts/passwords/rights.')
                native.write(BASE / f'{args.target}-idempotency.json', {'passed': True, 'accounts_passwords_rights_unchanged': True})
            return result
        delta = native.orm(args.target, apply_accounts)
        print(json.dumps({'target': args.target, 'users': len(delta['users']), 'assignments': len(delta['assignments']),
                          'project_grants': len(delta['project_grants']), 'kd_grants': len(delta['kd_grants'])}))
    else:
        delta = native.read(BASE / f'{args.target}-delta.json')
        checks = native.orm(args.target, lambda env: audit(env, native, args.target, delta))
        result = {'target': args.target, 'passed': len(checks), 'checks': checks, 'source_hashes': hashes()}
        native.write(BASE / f'{args.target}-audit.json', result)
        print(json.dumps({'target': args.target, 'passed': len(checks)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
