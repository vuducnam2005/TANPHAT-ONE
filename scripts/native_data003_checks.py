"""Live actor assertions and rollback probes for the owned DATA003 environment."""
# ruff: noqa: T201, PLC0415, EM101, TRY301
import argparse
import json
import math
import sys

import native_data003 as task
import requests


class RollbackProbe(Exception):
    pass


def checks(env, target):
    from odoo import fields
    from odoo.exceptions import AccessError, UserError

    actors = {k: env['res.users'].browse(v) for k, v in task.read(task.BASE / f'actors-{target}-apply.json')['actors'].items()}
    fixtures = task.inventory(env)
    outcomes = []
    gaps = []

    def check(label, condition):
        task.require(condition, label)
        outcomes.append(label)

    def denied(label, callback):
        try:
            with env.cr.savepoint():
                callback()
                raise RollbackProbe()
        except (AccessError, UserError):
            outcomes.append(label)
            return True
        except RollbackProbe:
            gaps.append({'check': label, 'actual': 'allowed', 'expected': 'denied'})
            return False
        return False

    projects = env['project.project'].browse([r['id'] for r in fixtures['bindings'] if r['model'] == 'project.project'])
    tasks = env['project.task'].browse([r['id'] for r in fixtures['bindings'] if r['model'] == 'project.task' and r['fields'].get('project_id')])
    timesheets = env['account.analytic.line'].browse([r['id'] for r in fixtures['bindings'] if r['model'] == 'account.analytic.line'])
    expenses = env['hr.expense'].browse([r['id'] for r in fixtures['bindings'] if r['model'] == 'hr.expense'])
    invoices = env['account.move'].browse([r['id'] for r in fixtures['bindings'] if r['model'] == 'account.move'])
    check('188 original XML IDs resolve', len(fixtures['bindings']) == 188)
    check('canonical project/task/timesheet/expense/invoice IDs retained',
          len(projects) == 4 and len(tasks) == 28 and len(timesheets) == 20 and len(expenses) == 6 and len(invoices) == 4)
    check('all projects remain managed', all(projects.mapped('tp_managed')))
    check('84 existing hours retained; preparation project has zero', sum(timesheets.mapped('unit_amount')) == 84
          and not timesheets.filtered(lambda line: line.project_id.tp_code == 'DA-2026-004'))
    check('expense identity/total retained', sum(expenses.mapped('total_amount')) == 7160000)
    check('invoice identity/total/draft retained', sum(invoices.mapped('amount_total')) == 801000000
          and set(invoices.mapped('state')) == {'draft'})
    for line in timesheets:
        check(f'timesheet {line.id} employee/user/task/project/analytic match',
              line.user_id == line.employee_id.user_id and line.task_id.project_id == line.project_id
              and line.user_id in line.task_id.user_ids and line.account_id == line.project_id.account_id)
    for expense in expenses:
        check(f'expense {expense.id} independent approver and project analytic',
              expense.manager_id != expense.employee_id.user_id and bool(expense.manager_id)
              and any(str(project.account_id.id) in expense.analytic_distribution for project in projects))
    for key, user in actors.items():
        check(key + ' has one employee, correct company, no system/platform-manager bypass',
              len(user.employee_ids) == 1 and user.company_id == env.company and not user.has_group('base.group_system')
              and not user.has_group('tp_core.group_manager'))
        visible = env['hr.expense'].with_user(user).search([('id', 'in', expenses.ids)])
        dashboard = env['hr.expense'].with_user(user).get_expense_dashboard([('id', 'in', expenses.ids)])
        descendants = env['hr.employee'].search([('id', 'child_of', user.employee_ids.ids)])
        expected = {state: sum(visible.filtered(lambda e, s=state: e.employee_id in descendants and e.state == s).mapped('total_amount'))
                    for state in ('draft', 'submitted', 'approved')}
        check(key + ' expense dashboard matches actor/domain/hierarchy',
              all(dashboard[state]['amount'] == amount for state, amount in expected.items()))
    check('admin legitimately has zero personal expense totals', all(x['amount'] == 0
          for x in env['hr.expense'].with_user(env.ref('base.user_admin')).get_expense_dashboard().values()))
    long = actors['long']
    work = tasks.filtered(lambda item: long in item.user_ids and item.project_id.tp_code == 'DA-2026-001')[:1]
    check('employee reads assigned managed task', bool(work.with_user(long).read(['name'])))
    denied('managed-task progress write remains blocked (RFC TASK-001)', lambda: work.with_user(long).write({'state': '1_done'}))
    try:
        with env.cr.savepoint():
            record = env['account.analytic.line'].with_user(long).create({
                'name': 'DATA003 rollback-only valid actor hours', 'task_id': work.id,
                'project_id': work.project_id.id, 'unit_amount': 0.5, 'date': fields.Date.context_today(work),
                'employee_id': long.employee_id.id,
            })
            check('employee can enter own valid hours without sudo', record.user_id == long)
            raise RollbackProbe()
    except AccessError as exc:
        gaps.append({'check': 'own valid timesheet create', 'actual': str(exc), 'expected': 'allowed in S1'})
    except RollbackProbe:
        pass
    outside = actors['khang']
    protected = projects.filtered(lambda project: project.tp_code == 'DA-2026-001')
    denied('outsider cannot read project', lambda: protected.with_user(outside).read(['name']))
    denied('outsider cannot read task', lambda: work.with_user(outside).read(['name']))
    denied('outsider cannot create a cross-scope timesheet (RFC TIME-001)', lambda:
           env['account.analytic.line'].with_user(outside).create({
               'name': 'DATA003 rollback-only cross-scope negative', 'project_id': protected.id,
               'task_id': work.id, 'unit_amount': 0.5, 'employee_id': outside.employee_id.id}))
    denied('outsider cannot read another employee expense', lambda: expenses[:1].with_user(outside).read(['name', 'total_amount']))
    denied('outsider cannot read invoice amount', lambda: invoices[:1].with_user(outside).read(['amount_total']))
    for key in ('long', 'khoa', 'khang'):
        denied(key + ' cannot read finance dashboard/cache/export source', lambda k=key:
               env.ref(task.OLD_NS[3] + '.dashboard_finance_draft').with_user(actors[k]).read(['spreadsheet_data']))
    check('accountant can read four draft invoices', len(invoices.with_user(actors['bao']).read(['amount_total'])) == 4)
    check('accountant can read six expenses', len(expenses.with_user(actors['bao']).read(['total_amount'])) == 6)
    check('accountant can read finance dashboard', bool(env.ref(task.OLD_NS[3] + '.dashboard_finance_draft').with_user(actors['bao']).read(['spreadsheet_data'])))
    denied('finance public share is forbidden even for authorized accountant', lambda:
           env['spreadsheet.dashboard.share'].with_user(actors['bao']).action_get_share_url({
               'dashboard_id': env.ref(task.OLD_NS[3] + '.dashboard_finance_draft').id, 'name': 'Rollback-only share'}))
    todos = env['project.task'].browse([r['id'] for r in fixtures['bindings'] if r['model'] == 'project.task' and not r['fields'].get('project_id')])
    denied('outsider cannot read admin personal To-do', lambda: todos[:1].with_user(outside).read(['name']))
    channel = env.ref(task.OLD_NS[3] + '.channel_survey_design')
    denied('outsider cannot read private group', lambda: channel.with_user(outside).read(['name']))
    message = env['mail.message'].search([('model', '=', 'discuss.channel'), ('res_id', '=', channel.id)], limit=1)
    denied('outsider cannot read private group message', lambda: message.with_user(outside).read(['body']))
    event = env.ref(task.OLD_NS[3] + '.event_02')
    original_name = event.name
    event.invalidate_recordset(['name', 'description', 'partner_ids'])
    masked = event.with_user(outside).read(['name', 'description'])[0]
    check('private calendar exposes Busy without details', masked['name'] != original_name and not masked['description'])
    event.invalidate_recordset(['name', 'description', 'partner_ids'])
    check('employee participates in assigned event', long.partner_id in event.partner_ids)
    own_expense = expenses.filtered(lambda e: e.employee_id.user_id == actors['khoa'])[:1]
    denied('native self-approval denied', lambda: own_expense.with_user(actors['khoa']).action_approve())
    denied('unrelated employee approval denied', lambda: own_expense.with_user(outside).action_approve())
    if target == 'clone':
        import odoo
        odoo.tools.config['smtp_server'] = '127.0.0.1'
        odoo.tools.config['smtp_port'] = 9
        try:
            with env.cr.savepoint():
                review = own_expense.with_user(actors['nam'])
                review.action_refuse()
                wizard = env['hr.expense.refuse.wizard'].with_user(actors['nam']).create({
                    'reason': 'Diễn tập giả lập: bổ sung chứng từ', 'expense_ids': [(6, 0, own_expense.ids)]})
                wizard.action_refuse()
                check('native refusal with actor/reason', own_expense.state == 'refused')
                own_expense.invalidate_recordset(['can_reset', 'is_editable', 'can_approve'])
                own_expense.with_user(actors['nam']).action_reset()
                own_expense.with_user(actors['khoa']).write({'name': own_expense.name + ' — bổ sung chứng từ (diễn tập)'})
                own_expense.with_user(actors['khoa']).action_submit()
                check('native correction and resubmission', own_expense.state == 'submitted')
                raise RollbackProbe()
        except RollbackProbe:
            pass
        # Prove a dashboard source is live, using only an uncommitted clone mutation.
        try:
            with env.cr.savepoint():
                employee_line = timesheets.filtered(lambda line: line.user_id == long)[:1]
                before = sum(env['account.analytic.line'].with_user(long).search([('id', 'in', timesheets.ids)]).mapped('unit_amount'))
                employee_line.with_user(long).write({'unit_amount': employee_line.unit_amount + 0.5})
                after = sum(env['account.analytic.line'].with_user(long).search([('id', 'in', timesheets.ids)]).mapped('unit_amount'))
                check('dashboard live source changes by exact clone delta', math.isclose(after, before + 0.5, abs_tol=1e-6))
                raise RollbackProbe()
        except RollbackProbe:
            pass
    env.cr.rollback()
    return {'target': target, 'assertions_passed': len(outcomes), 'checks': outcomes, 'gaps': gaps}


def http_checks(target):
    config, database = task.target_config(target)
    base = 'http://127.0.0.1:' + task.options(config)['options']['http_port']
    credentials = task.read(task.BASE / 'actor-secrets.json')
    results = []
    for key, value in credentials.items():
        session = requests.Session()
        result = session.post(base + '/web/session/authenticate', json={
            'jsonrpc': '2.0', 'method': 'call', 'params': {'db': database, **value}}, timeout=30).json()
        task.require(result.get('result', {}).get('uid'), key + ' login failed')
        results.append({'actor': key, 'login_uid': result['result']['uid']})
        session.close()
    return results


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=['clone', 'dev'], default='clone')
    parser.add_argument('--http', action='store_true')
    args = parser.parse_args()
    result = {'http_logins': http_checks(args.target)} if args.http else task.orm(args.target, lambda env: checks(env, args.target))
    task.write(task.BASE / f'checks-{args.target}{"-http" if args.http else ""}.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
