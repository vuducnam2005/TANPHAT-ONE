"""Two independent PostgreSQL transactions, synthetic users only on the existing test DB."""
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

from odoo import SUPERUSER_ID, Command, api
from odoo.exceptions import ValidationError
from odoo.modules.registry import Registry
from odoo.tools import config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    config.parse_config(['-c', str(Path(args.config).resolve()), '--no-http', '--max-cron-threads=0'], setup_logging=True)
    assert config['db_name'] == ['tp_tanphat_test'] or config['db_name'] == 'tp_tanphat_test'
    registry = Registry('tp_tanphat_test')
    prefix = 'rename.race.' + uuid4().hex
    ids, partner_ids = [], []
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        actor_id = env.ref('base.user_admin').id
        group_ids = env.ref('base.group_user').ids
        company_id = env.company.id
        for i in range(2):
            user = env['res.users'].with_context(no_reset_password=True).create({
                'name': 'Synthetic Rename Race', 'login': prefix + '.' + str(i),
                'company_id': company_id, 'company_ids': [Command.set([company_id])],
                'group_ids': [Command.set(group_ids)],
            })
            ids.append(user.id)
            partner_ids.append(user.partner_id.id)
        cr.commit()

    def run_pair(target, create=False):
        barrier = Barrier(2)

        def worker(index):
            with registry.cursor() as cr:
                env = api.Environment(cr, actor_id, {'allowed_company_ids': [company_id]})
                barrier.wait(timeout=20)
                try:
                    if create and index == 1:
                        user = env['res.users'].with_context(no_reset_password=True).create({
                            'name': 'Synthetic Rename Race Created', 'login': target,
                            'company_id': company_id, 'company_ids': [Command.set([company_id])],
                        })
                        result = ('success', user.id, user.partner_id.id)
                    else:
                        env['res.users'].browse(ids[index]).write({'login': target})
                        result = ('success', ids[index], 0)
                    cr.commit()
                    return result
                except Exception as error:
                    cr.rollback()
                    # Core create may expose the native constraint as IntegrityError.
                    if isinstance(error, ValidationError) or getattr(error, 'pgcode', None) == '23505':
                        return ('duplicate', 0, 0)
                    raise

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, [0, 1]))
        assert sorted(r[0] for r in results) == ['duplicate', 'success'], results
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            winners = env['res.users'].with_context(active_test=False).search([('login', '=', target)])
            assert len(winners) == 1
            for status, uid, partner_id in results:
                if status == 'success' and uid not in ids:
                    ids.append(uid)
                    partner_ids.append(partner_id)
        return results

    try:
        run_pair(prefix + '.rename')
        run_pair(prefix + '.create', create=True)
        sys.stdout.write('LOGIN_RENAME_RACE_PASS: rename+rename and create+rename each have exactly one winner\n')
    finally:
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            users = env['res.users'].with_context(active_test=False).browse(ids).exists()
            assert all(u.login.startswith(prefix) for u in users)
            users.unlink()
            env['res.partner'].browse(partner_ids).exists().unlink()
            assert not env['res.users'].with_context(active_test=False).search_count([('login', '=like', prefix + '%')])
            cr.commit()


if __name__ == '__main__':
    main()
