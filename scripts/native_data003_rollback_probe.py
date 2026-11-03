"""Clone-only failure injection: native correction + migration rollback, complete rowsets."""
# ruff: noqa: T201, EM101
import json
import sys

import native_data003 as task


def probe(env):
    task.require(env.cr.dbname == task.DATABASE, 'Rollback probe is clone-only.')
    task.isolate_mail(env)
    # No cron/browser writes may overlap this evidence.
    before = task.backup.table_inventory(env.cr._cnx)
    user = env.ref(task.OLD_NS[0] + '.user_son')
    user.write({'lang': 'en_US'})
    try:
        task.migrate(env, 'clone', 'fail-test')
    except RuntimeError as error:
        task.require(str(error) == 'DATA003_INJECTED_FAILURE', 'Unexpected failure.')
        env.cr.rollback()
        env.invalidate_all()
    else:
        raise AssertionError('Bootstrap failure was not injected.')
    task.require(task.backup.table_inventory(env.cr._cnx) == before, 'Bootstrap rollback rowsets differ.')
    expense = env.ref(task.OLD_NS[0] + '.expense_00')
    manager = env.ref(task.OLD_NS[0] + '.user_nam')
    task.require(expense.state == 'submitted', 'Expected submitted owned expense.')
    wizard = env['hr.expense.refuse.wizard'].with_user(manager).create({
        'reason': 'Diễn tập rollback DATA003, không lưu', 'expense_ids': [(6, 0, expense.ids)],
    })
    wizard.action_refuse()
    expense.with_user(manager).action_reset()
    env['ir.config_parameter'].search([('key', '=', task.NEW_NS + f'.action_{expense.id}_action_submit')]).unlink()
    try:
        task.native_actions(env, 'clone', 'fail-test')
    except RuntimeError as error:
        task.require(str(error) == 'DATA003_NATIVE_INJECTED_FAILURE', 'Unexpected failure.')
        env.cr.rollback()
        env.invalidate_all()
    else:
        raise AssertionError('Native action failure was not injected.')
    after = task.backup.table_inventory(env.cr._cnx)
    task.require(after == before, 'Native failure rollback rowsets differ.')
    return {'target': 'clone', 'bootstrap_injected_failure': True, 'native_submit_injected_failure': True,
            'rowsets_identical': len(before), 'sequences_outside_transaction': True,
            'transport': 'refused loopback SMTP, no external delivery', 'passed': True}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    result = task.orm('clone', probe)
    task.write(task.BASE / 'rollback-probe.json', result)
    print(json.dumps(result))
