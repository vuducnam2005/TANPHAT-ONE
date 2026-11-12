"""KD-ACCESS-002 owned clone, exact source/rights delta and private evidence."""
# ruff: noqa: T201, PLC0415
import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import kd_access001 as accounts
import ui_shell_auth001 as shell

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.local/kd-access002'
SOURCE = BASE / 'source/custom_addons'
DB = 'tp_tanphat_kdaccess002_20261109'
PORT = 19289
MODULES = ('tp_kd_workspace', 'tp_web_home')


def bind():
    shell.BASE, shell.SOURCE, shell.DB, shell.PORT, shell.MODULES = BASE, SOURCE, DB, PORT, MODULES
    return shell.bind()


def original(native):
    return native.read(ROOT / '.local/kd-access001/dev-delta.json')


def inventory(env, native, target):
    delta = original(native)
    result = {'database': env.cr.dbname, 'users': {}, 'other_kd_accounts': []}
    ids = []
    for alias, row in delta['users'].items():
        user = env['res.users'].browse(row['id'])
        native.require(user.login == row['login'] and user.partner_id.id == row['partner_id'], 'Account identity drift.')
        ids.append(user.id)
        result['users'][alias] = {
            'id': user.id, 'company': user.company_ids.ids, 'department': row['department_id'],
            'groups': user.group_ids.ids, 'active': user.active,
            'assignments': env['tp.project.assignment'].search_count([('user_id', '=', user.id), ('active', '=', True)]),
            'project_grants': env['tp.project.grant'].search_count([('user_id', '=', user.id), ('active', '=', True)]),
            'kd_grants': env['tp.kd.grant'].search_count([('user_id', '=', user.id), ('active', '=', True)]),
            'opportunity_grants': env['tp.kd.grant'].search_count([('user_id', '=', user.id), ('domain', '=', 'opportunity'), ('active', '=', True)]),
            'crm_read': env['crm.lead'].with_user(user).has_access('read'),
        }
    candidates = env['tp.project.assignment'].with_context(active_test=False).search([
        ('project_id', 'in', list({p for r in delta['users'].values() for p in r['projects']}))]).user_id
    for user in candidates - env['res.users'].browse(ids):
        result['other_kd_accounts'].append({'id': user.id, 'active': user.active,
                                         'kind': 'existing_test_or_operator_unmapped_no_change'})
    native.write(BASE / f'{target}-inventory.json', result)
    return {a: {k: v for k, v in r.items() if k not in ('id', 'company', 'department', 'groups')}
            for a, r in result['users'].items()}


def grant_delta(env, native, target, commit=False):
    from odoo import Command
    old = original(native)
    journal = BASE / f'{target}-delta.json'
    previous = native.read(journal) if journal.exists() else None
    identity = {'database': env.cr.dbname, 'uuid': env['ir.config_parameter'].get_str('database.uuid')}
    if previous:
        native.require(previous['identity'] == identity, 'Delta identity mismatch.')
        expected = {(r['id'], pid, r['department_id'], cap)
                    for alias, r in old['users'].items() for pid in r['projects']
                    for cap in (['prepare'] if alias == 'support' else ['prepare', 'submit'])}
        actual = set()
        for rid in previous['grants']:
            rec = env['tp.kd.grant'].browse(rid)
            native.require(rec.exists() and rec.active and rec.domain == 'opportunity'
                           and not rec.date_end and rec.reason == previous['reason'], 'Delta rights drift.')
            actual.add((rec.user_id.id, rec.project_id.id, rec.department_id.id, rec.capability))
        native.require(actual == expected and len(actual) == len(previous['grants']), 'Delta scope/capability drift.')
        team = env['crm.team'].browse(previous['team_id'])
        rows = list(old['users'].values())
        native.require(team.exists() and team.active and team.company_id.id == rows[0]['company_id']
                       and team.kd_department_id.id == rows[0]['department_id']
                       and set(team.member_ids.ids) == {r['id'] for r in rows}, 'Native team drift.')
        return previous
    result = {'identity': identity, 'grants': [], 'reason': 'KD-ACCESS-002: explicit user request; dev scope only, not Q2/pilot.', 'users': old['users']}
    rows = list(old['users'].values())
    native.require(len({r['department_id'] for r in rows}) == len({r['company_id'] for r in rows}) == 1, 'Team scope differs.')
    team = env['crm.team'].create({'name': 'KH-KD — Cơ hội được giao', 'company_id': rows[0]['company_id'],
        'kd_department_id': rows[0]['department_id'], 'member_ids': [Command.set([r['id'] for r in rows])]})
    result['team_id'] = team.id
    for alias, row in old['users'].items():
        user = env['res.users'].browse(row['id'])
        native.require(user.login == row['login'] and user.active and user.partner_id.id == row['partner_id'], 'Account drift.')
        for pid in row['projects']:
            project = env['project.project'].browse(pid)
            native.require(env['tp.project.assignment'].search_count([
                ('project_id', '=', pid), ('user_id', '=', user.id), ('active', '=', True)]) == 1
                and project.tp_department_id.id == row['department_id'], 'Scope drift.')
            for cap in (['prepare'] if alias == 'support' else ['prepare', 'submit']):
                native.require(not env['tp.kd.grant'].search_count([('project_id', '=', pid), ('user_id', '=', user.id),
                               ('domain', '=', 'opportunity'), ('capability', '=', cap), ('active', '=', True)]), 'Unjournaled existing opportunity right.')
                grant = env['tp.kd.grant'].create({'project_id': pid, 'department_id': row['department_id'],
                    'user_id': user.id, 'domain': 'opportunity', 'capability': cap, 'reason': result['reason']})
                result['grants'].append(grant.id)
    if commit:
        # Journal is durable before commit; a failed transaction must be reconciled, never blindly repeated.
        native.write(journal, result)
        env.cr.commit()
    return result


def reverse_rights(env, native, target):
    journal = grant_delta(env, native, target)
    native.require(journal['identity'] == {'database': env.cr.dbname, 'uuid': env['ir.config_parameter'].get_str('database.uuid')}, 'Rollback DB identity mismatch.')
    grants = env['tp.kd.grant'].browse(journal['grants']).exists()
    native.require(len(grants) == len(journal['grants']) and all(g.reason == journal['reason'] and g.domain == 'opportunity' for g in grants), 'Foreign rollback grant.')
    grants.active = False
    team = env['crm.team'].browse(journal['team_id'])
    native.require(set(team.member_ids.ids) == {r['id'] for r in journal['users'].values()}, 'Foreign team rollback.')
    members = env['crm.team.member'].search([('crm_team_id', '=', team.id), ('active', '=', True)])
    native.require(len(members) == 5 and set(members.user_id.ids) == {r['id'] for r in journal['users'].values()},
                   'Foreign team membership rollback.')
    members.active = False
    team.active = False


def preservation(native, label):
    """Original business/security rows stay exact; only journaled grants/team/export additions are allowed."""
    from psycopg2 import sql
    with native.connect('tp_tanphat_dev') as conn, conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND (tablename LIKE 'tp\\_%%' ESCAPE '\\' OR tablename LIKE 'project\\_%%' ESCAPE '\\' OR tablename LIKE 'crm\\_%%' ESCAPE '\\' OR tablename LIKE 'account\\_%%' ESCAPE '\\' OR tablename LIKE 'hr\\_%%' ESCAPE '\\' OR tablename LIKE 'auth\\_%%' ESCAPE '\\' OR tablename IN ('res_users','res_partner','res_company','res_groups','res_groups_implied_rel','res_groups_users_rel','res_company_users_rel','res_users_apikeys'))")
        tables = sorted(r[0] for r in cur.fetchall())
        result = {'tables': {}}
        baseline = native.read(BASE / 'preserve-dev-before.json') if label != 'before' else None
        for table in tables:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY column_name", (table,))
            cols = [r[0] for r in cur.fetchall() if r[0] not in ('write_uid', 'write_date')]
            if baseline and table in baseline['tables']:
                cols = baseline['tables'][table]['columns']
            cur.execute(sql.SQL('SELECT {} FROM {}').format(sql.SQL(',').join(map(sql.Identifier, cols)), sql.Identifier(table)))
            rows = [hashlib.sha256(repr(r).encode()).hexdigest() for r in cur.fetchall()]
            result['tables'][table] = {'columns': cols, 'rows': sorted(rows)}
        cur.execute('SELECT key,value FROM ir_config_parameter ORDER BY key')
        result['config'] = cur.fetchall()
        cur.execute("SELECT name,state,latest_version FROM ir_module_module ORDER BY name")
        result['modules'] = cur.fetchall()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='ir_attachment' ORDER BY column_name")
        attachment_columns = [r[0] for r in cur.fetchall() if r[0] not in ('write_uid', 'write_date')]
        cur.execute(sql.SQL("SELECT {} FROM ir_attachment WHERE COALESCE(url,'') NOT LIKE '/web/assets/%' ORDER BY id").format(
            sql.SQL(',').join(map(sql.Identifier, attachment_columns))))
        result['attachments'] = [hashlib.sha256(repr(r).encode()).hexdigest() for r in cur.fetchall()]
        result['blobs'] = native.backup.attachment_inventory(conn, ROOT / '.local/odoo/filestore/tp_tanphat_dev')
    native.write(BASE / f'preserve-dev-{label}.json', result)
    result = native.read(BASE / f'preserve-dev-{label}.json')
    if not baseline:
        print('PRIVATE BASELINE:', len(tables), 'business/security tables, auth/config/modules/attachments/blob checksums.')
        return
    from collections import Counter
    changes = {}
    for table, old in baseline['tables'].items():
        old_rows = old['rows']
        if table == 'res_users':
            # Native team membership computes sale_team_id for exactly the five mapped users.
            journal = native.read(BASE / 'dev-delta.json')
            mapped = {r['id'] for r in journal['users'].values()}
            restored = native.read(BASE / 'backup-restore-result.json')['database']
            cols = old['columns']
            with native.connect(restored) as conn, conn.cursor() as cur:
                cur.execute(sql.SQL('SELECT {} FROM res_users').format(sql.SQL(',').join(map(sql.Identifier, cols))))
                rows = [list(r) for r in cur.fetchall()]
            for row in rows:
                if row[cols.index('id')] in mapped:
                    native.require(row[cols.index('sale_team_id')] is None, 'Unexpected previous sales team; reconcile exact user delta.')
                    row[cols.index('sale_team_id')] = journal['team_id']
            old_rows = [hashlib.sha256(repr(tuple(r)).encode()).hexdigest() for r in rows]
        new = result['tables'].get(table, {'rows': []})
        missing, added = Counter(old_rows) - Counter(new['rows']), Counter(new['rows']) - Counter(old_rows)
        if missing or added:
            changes[table] = {'missing_or_changed': sum(missing.values()), 'added': sum(added.values())}
    allowed = {'tp_kd_grant': 42, 'crm_team': 1, 'crm_team_member': 5,
               'res_groups_users_rel': 5, 'res_groups_implied_rel': 1}
    report = {'ok': all(not r['missing_or_changed'] and r['added'] == allowed.get(t, 0) for t, r in changes.items()),
              'changes': changes, 'config_equal': baseline['config'] == result['config'],
              'attachments_equal': baseline['attachments'] == result['attachments'], 'original_blobs_valid': True,
              'tables': len(baseline['tables']), 'rows': sum(len(v['rows']) for v in baseline['tables'].values())}
    report['native_user_delta'] = {'sale_team_id': 'None -> journaled native team for exactly five users; all other saved columns exact'}
    for blob in baseline['blobs']:
        file = ROOT / '.local/odoo/filestore/tp_tanphat_dev' / blob['store_fname']
        if not file.exists() or native.backup.digest(file, 'sha1') != blob['sha1']:
            report['original_blobs_valid'] = False
    module_changes = {a[0]: [a[1:], b[1:]] for a, b in zip(baseline['modules'], result['modules'], strict=True) if a != b}
    report['module_changes'] = module_changes
    report['ok'] = report['ok'] and all(report[k] for k in ('config_equal', 'attachments_equal', 'original_blobs_valid')) and set(module_changes) <= set(MODULES)
    native.write(BASE / f'preservation-{label}-result.json', report)
    print(json.dumps(report))
    native.require(report['ok'], 'Unexpected preservation delta. Inspect private evidence; never overwrite concurrent writers.')


def rollback(native, target):
    """Revoke only journaled rights, restore exact changed files, and upgrade the two addons."""
    import zipfile
    folder = SOURCE if target == 'clone' else ROOT / 'custom_addons'
    sealed = native.read(BASE / 'sealed-all-source.json')
    native.require(shell.prior.previous.tree_hashes(folder) == sealed, 'Concurrent source changes: reconcile before rollback.')
    owner = native.read(BASE / 'owner.json')
    with zipfile.ZipFile(Path(owner['snapshot']) / 'maintained-source.zip') as archive:
        old = {name.removeprefix('custom_addons/'): archive.read(name)
               for name in archive.namelist() if name.startswith('custom_addons/')}
    native.dev.stop_server() if target == 'dev' else native.runtime('stop')

    def revoke(env):
        from odoo import Command
        reverse_rights(env, native, target)
        native.require(b'base.group_allow_export' not in old['tp_kd_workspace/security/staff_scope.xml'],
                       'Baseline already had export; reconcile rollback implication first.')
        env.ref('tp_kd_workspace.group_scoped_staff').implied_ids = [
            Command.unlink(env.ref('base.group_allow_export').id)]
        env.cr.commit()
    native.orm(target, revoke)
    changed = {name for name, digest in sealed.items()
               if name not in old or hashlib.sha256(old[name]).hexdigest() != digest}
    for name in sorted(changed):
        dest = (folder / name).resolve()
        native.require(dest.is_relative_to(folder.resolve()), 'Unsafe rollback file.')
        if name in old:
            dest.write_bytes(old[name])
        else:
            dest.unlink()
    shell.run_odoo(native, target)
    native.write(BASE / f'{target}-rollback-result.json', {'ok': True, 'files': sorted(changed),
                 'rights_revoked': 42, 'team_archived': True, 'database_restored': False})
    native.dev.start_server() if target == 'dev' else native.runtime('start')
    print('EXACT source/rights rollback completed; original data/accounts not restored or deleted.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['prepare', 'inventory', 'probe-before', 'upgrade', 'test', 'start', 'stop', 'grant', 'backup', 'preserve', 'audit', 'rehearse', 'fixture', 'phase', 'delta-rehearse', 'seal', 'apply', 'rollback'])
    p.add_argument('--target', choices=['clone', 'dev'], default='clone')
    p.add_argument('--label', default='before')
    p.add_argument('--focused', action='store_true')
    args = p.parse_args()
    native = bind()
    if args.command == 'prepare':
        shell.prior.previous.prepare(native)
        native.write(BASE / 'baseline-source.json', shell.hashes(ROOT / 'custom_addons'))
        accounts.BASE = BASE
        accounts.private(native)
    elif args.command == 'inventory':
        print(json.dumps(native.orm(args.target, lambda env: inventory(env, native, args.target))))
    elif args.command == 'probe-before':
        def probe(env):
            from odoo import Command
            row = original(native)['users']['support']
            user = env['res.users'].browse(row['id'])
            denied = not env['crm.lead'].with_user(user).has_access('read')
            # Reproduce on synthetic clone record; temporary salesman only demonstrates the backend gap, rolled back.
            user.group_ids = [Command.link(env.ref('sales_team.group_sale_salesman_all_leads').id)]
            proj = env['project.project'].browse(row['projects'][0])
            env['tp.kd.grant'].create({'project_id': proj.id, 'department_id': proj.tp_department_id.id,
                'user_id': user.id, 'domain': 'opportunity', 'capability': 'prepare', 'reason': 'Clone-only failing security reproduction'})
            lead = env['crm.lead'].create({'name': 'KD002 synthetic before', 'type': 'opportunity', 'company_id': proj.company_id.id,
                'partner_id': proj.partner_id.id, 'tp_project_id': proj.id, 'user_id': user.id,
                'kd_source': 'synthetic', 'kd_scope': 'synthetic', 'kd_checklist': 'synthetic', 'kd_deadline': '2030-01-01',
                'kd_receipt': 'synthetic', 'expected_revenue': 7654321})
            actor = lead.with_user(user)
            actor.action_kd_prepare()
            actor.action_kd_record_submission()
            result = {'baseline_crm_denied': denied, 'prepare_only_can_submit_gap': actor.kd_bid_state == 'submitted',
                      'support_can_read_native_money_gap': actor.read(['expected_revenue'])[0]['expected_revenue'] == 7654321}
            env.cr.rollback()
            native.write(BASE / 'before-gap-reproduction.json', result)
            return result
        native.require(args.target == 'clone', 'Clone-only probe.')
        print(json.dumps(native.orm('clone', probe)))
    elif args.command in ('start', 'stop'):
        native.runtime(args.command)
    elif args.command in ('upgrade', 'test'):
        native.require(args.target == 'clone', 'Dev only via sealed apply.')
        if args.command == 'test':
            tested_hashes = shell.hashes()
            code = shell.prior.kd.tests('tp_kd_workspace' if args.focused else 'tp_kd_workspace,tp_contract,tp_crm_project_bridge,tp_project,tp_web_home',
                '/tp_kd_workspace:TestOpportunityAccess' if args.focused else '/tp_kd_workspace,/tp_contract,/tp_crm_project_bridge,/tp_project,/tp_web_home')
            native.require(code == 0, 'Odoo tests failed; inspect private log.')
            native.require(tested_hashes == shell.hashes(), 'Source changed during tests; rerun final source.')
            native.write(BASE / ('focused-tests.json' if args.focused else 'final-tests.json'), {'ok': True, 'source_hashes': tested_hashes})
        else:
            shell.run_odoo(native, 'clone')
    elif args.command == 'grant':
        result = native.orm(args.target, lambda env: grant_delta(env, native, args.target, commit=True))
        print(json.dumps({'target': args.target, 'new_opportunity_grants': len(result['grants']), 'accounts_preserved': 5}))
    elif args.command == 'audit':
        checks = native.orm(args.target, lambda env: accounts.audit(env, native, args.target, original(native), crm_scope=True, check_historical=False))
        native.write(BASE / f'{args.target}-audit.json', {'ok': True, 'passed': len(checks), 'checks': checks, 'source_hashes': shell.hashes(SOURCE if args.target == 'clone' else ROOT / 'custom_addons')})
        print(json.dumps({'target': args.target, 'passed': len(checks)}))
    elif args.command == 'rehearse':
        from kd_access001_checks import rehearse
        native.require(args.target == 'clone', 'Mutation rehearsal only on clone.')

        def run(env):
            before = accounts.account_digest(env)
            checks = rehearse(env, native, original(native))
            env.cr.rollback()
            native.require(accounts.account_digest(env) == before, 'Rehearsal rollback changed account/rights rowsets.')
            checks.append('account and rights rowsets identical after rollback')
            return checks
        checks = native.orm('clone', run)
        native.write(BASE / 'clone-rehearsal.json', {'ok': True, 'passed': len(checks), 'checks': checks, 'source_hashes': shell.hashes()})
        print(json.dumps({'passed': len(checks), 'rolled_back': True}))
    elif args.command == 'fixture':
        native.require(args.target == 'clone' and not (BASE / 'fixture.json').exists(), 'New fixture only on owned clone.')

        def fixture(env):
            result = {}
            for alias, row in original(native)['users'].items():
                project = env['project.project'].browse(row['projects'][0])
                lead = env['crm.lead'].with_user(row['id']).create({'name': 'KD002 Synthetic ' + alias, 'type': 'opportunity',
                    'company_id': project.company_id.id, 'partner_id': project.partner_id.id, 'tp_project_id': project.id,
                    'user_id': row['id'], 'kd_source': 'Synthetic acceptance', 'kd_scope': 'Synthetic acceptance',
                    'kd_checklist': 'Synthetic acceptance', 'kd_deadline': '2030-01-01', 'kd_receipt': 'Synthetic unverified receipt'})
                attachment = env['ir.attachment'].create({'name': 'Synthetic CRM file', 'res_model': 'crm.lead',
                    'res_id': lead.id, 'raw': b'KD002_SYNTHETIC_FINANCIAL_7654321', 'type': 'binary'})
                result[alias] = {'lead_id': lead.id, 'attachment_id': attachment.id}
            native.write(BASE / 'fixture.json', result)
            env.cr.commit()
        native.orm('clone', fixture)
        print('FIVE SYNTHETIC CRM RECORDS + FILES READY (clone only).')
    elif args.command == 'phase':
        native.require(args.target == 'clone' and args.label in ('normal', 'revoked', 'expired', 'unassigned'), 'Owned lifecycle only.')

        def phase(env):
            row = original(native)['users']['head']
            lead = env['crm.lead'].browse(native.read(BASE / 'fixture.json')['head']['lead_id'])
            grant = env['tp.project.grant'].with_context(active_test=False).search([
                ('user_id', '=', row['id']), ('project_id', '=', lead.tp_project_id.id), ('capability', '=', 'financial_read')])
            assignment = env['tp.project.assignment'].with_context(active_test=False).search([
                ('user_id', '=', row['id']), ('project_id', '=', lead.tp_project_id.id)])
            native.require(len(grant) == len(assignment) == 1, 'Lifecycle rights mismatch.')
            file = BASE / 'lifecycle-baseline.json'
            if not file.exists():
                native.write(file, {'grant_id': grant.id, 'assignment_id': assignment.id, 'grant_active': grant.active,
                    'date_end': str(grant.date_end) if grant.date_end else False, 'assignment_active': assignment.active})
            saved = native.read(file)
            native.require(saved['grant_id'] == grant.id and saved['assignment_id'] == assignment.id, 'Lifecycle identity drift.')
            grant.write({'active': saved['grant_active'] if args.label != 'revoked' else False,
                         'date_end': '2000-01-01' if args.label == 'expired' else saved['date_end']})
            assignment.active = saved['assignment_active'] if args.label != 'unassigned' else False
            env.cr.commit()
        native.orm('clone', phase)
        print('Owned clone lifecycle phase:', args.label)
    elif args.command == 'backup':
        shell.prior.backup(native)
        shell.verify_backup(native)
    elif args.command == 'preserve':
        native.require(args.target == 'dev', 'Dev preservation only.')
        preservation(native, args.label)
    elif args.command == 'rollback':
        rollback(native, args.target)
    elif args.command == 'delta-rehearse':
        native.require(args.target == 'clone', 'Clone-only rights rollback rehearsal.')

        def exercise(env):
            before = accounts.account_digest(env)
            initial = grant_delta(env, native, 'clone')
            native.require(accounts.account_digest(env) == before and initial == grant_delta(env, native, 'clone'), 'Rerun changed rights/accounts/passwords.')
            reverse_rights(env, native, 'clone')
            native.require(not any(env['tp.kd.grant'].browse(initial['grants']).mapped('active')), 'Rollback did not revoke exact new rights.')
            native.require(not env['crm.team'].browse(initial['team_id']).active, 'Rollback team still active.')
            native.require(not any(env['res.users'].browse([r['id'] for r in initial['users'].values()]).mapped('sale_team_id')),
                           'Native default team remained after membership rollback.')
            env.cr.rollback()
            native.require(accounts.account_digest(env) == before, 'Rollback rehearsal changed original rows.')
        native.orm('clone', exercise)
        native.write(BASE / 'delta-rehearsal.json', {'ok': True, 'idempotent': True, 'exact_rollback': True,
                     'native_memberships_and_default_team_reversed': True, 'original_accounts_passwords_rights_preserved': True})
        print('IDEMPOTENCY + EXACT RIGHTS ROLLBACK PASS; original account/password/rights rows preserved.')
    elif args.command == 'seal':
        tests = sorted((BASE / 'odoo-tests').glob('*.json'))
        native.require(tests and native.read(tests[-1])['ok'], 'Green regression required.')
        for filename in ('final-tests.json', 'clone-audit.json', 'clone-rehearsal.json', 'clone-browser.json', 'native-flows.json', 'hoot-result.json', 'delta-rehearsal.json', 'full-rollback-rehearsal.json'):
            report = native.read(BASE / filename)
            native.require(report.get('ok') and not report.get('errors') and not report.get('failures'), filename + ' failed.')
            if 'source_hashes' in report:
                native.require(report['source_hashes'] == shell.hashes(), filename + ' source differs.')
        native.write(BASE / 'sealed-source.json', shell.hashes())
        native.write(BASE / 'sealed-all-source.json', shell.prior.previous.tree_hashes(SOURCE))
        print('SEALED tested clone source + role/mutation/browser/rollback evidence.')
    elif args.command == 'apply':
        import zipfile
        native.require(args.target == 'dev', 'Explicit --target dev required.')
        owner = native.read(BASE / 'owner.json')
        backup = Path(owner['pre_apply_backup'])
        restored = native.read(BASE / 'backup-restore-result.json')
        native.require(restored['ok'] and restored['backup'] == str(backup) and owner['rehearsal_passed'], 'Fresh restored backup required.')
        native.require(0 <= datetime.now(UTC).timestamp() - (backup / 'manifest.json').stat().st_mtime < 900, 'Backup is stale.')
        native.require(native.read(BASE / 'sealed-source.json') == shell.hashes(), 'Source changed after seal.')
        with zipfile.ZipFile(Path(owner['snapshot']) / 'maintained-source.zip') as archive:
            baseline = {n.removeprefix('custom_addons/'): hashlib.sha256(archive.read(n)).hexdigest()
                        for n in archive.namelist() if n.startswith('custom_addons/')}
        native.require(shell.prior.previous.tree_hashes(ROOT / 'custom_addons') == baseline, 'Concurrent main source change.')
        native.dev.stop_server()
        native.require(not native.dev.is_listening(18069), 'Dev still listening.')
        preservation(native, 'before')
        backup_baseline = native.read(backup / 'baseline.json')
        with native.connect('tp_tanphat_dev') as connection:
            live = native.backup.table_inventory(connection)
        preserved = set(native.read(BASE / 'preserve-dev-before.json')['tables']) | {'ir_attachment', 'ir_config_parameter'}
        native.require(all(live.get(t) == backup_baseline['tables'].get(t) for t in preserved),
                       'Dev data changed after backup; create and verify a fresh backup before applying.')

        with native.connect('tp_tanphat_dev') as connection, connection.cursor() as cursor:
            cursor.execute("SELECT rel.uid FROM res_groups_users_rel rel JOIN ir_model_data d ON d.res_id=rel.gid "
                           "AND d.model='res.groups' WHERE d.module='tp_kd_workspace' AND d.name='group_scoped_staff'")
            native.require({r[0] for r in cursor.fetchall()} == {r['id'] for r in original(native)['users'].values()},
                           'Unexpected scoped staff accounts; export implication would widen the delta.')
        changed = {p for p, h in native.read(BASE / 'sealed-all-source.json').items() if baseline.get(p) != h}
        native.require(all(p.split('/')[0] in MODULES or p in (
            'tp_contract/tests/test_contract_workflow.py', 'tp_crm_project_bridge/tests/test_crm_project_link.py') for p in changed), 'Unrelated source delta.')
        for name in sorted(changed):
            dest = (ROOT / 'custom_addons' / name).resolve()
            native.require(dest.is_relative_to((ROOT / 'custom_addons').resolve()), 'Unsafe source path.')
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE / name, dest)
        native.require(shell.prior.previous.tree_hashes(ROOT / 'custom_addons') == native.read(BASE / 'sealed-all-source.json'), 'Dev source differs from clone.')
        shell.run_odoo(native, 'dev')
        result = native.orm('dev', lambda env: grant_delta(env, native, 'dev', commit=True))
        native.write(BASE / 'apply-result.json', {'ok': True, 'files': sorted(changed), 'new_grants': len(result['grants']), 'team_id': result['team_id']})
        preservation(native, 'after-apply')
        native.dev.start_server()
        print('EXACT DEV DELTA APPLIED; read-only smoke/preservation still required.')


if __name__ == '__main__':
    main()
