"""Actual install/upgrade policy preservation on a second owned, neutralized clone."""
# ruff: noqa: T201, PLC0415
import shutil
import subprocess
import sys
from contextlib import closing

import ui_shell_auth001 as task
from psycopg2 import sql


def main():
    native = task.bind()
    native.target_config('clone')
    database = 'tp_tanphat_shellauth001_policy_20261109'
    folder = task.BASE / 'policy'
    native.require(not folder.exists(), 'Reuse the owned policy evidence; do not overwrite.')
    folder.mkdir()
    native.write(folder / 'owner.json', {'database': database, 'workspace': str(task.ROOT), 'no_http': True})
    with closing(native.connect('postgres', admin=True)) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM pg_database WHERE datname=%s', (database,))
            native.require(not cur.fetchone(), 'Policy database already exists; refusing reuse.')
            cur.execute(sql.SQL("CREATE DATABASE {} OWNER tp_odoo TEMPLATE template0 ENCODING 'UTF8'").format(sql.Identifier(database)))
    snapshot = task.Path(native.read(task.BASE / 'owner.json')['snapshot'])
    pg_env = native.backup.pg_environment(native.read(task.ROOT / '.local/dev-secrets.json')['pg_app'])
    native.backup.run([native.dev.pg_bin() / 'pg_restore.exe', '-h', '127.0.0.1', '-p', '55432', '-U', 'tp_odoo',
                      '-d', database, '--no-owner', '--no-privileges', '--exit-on-error', snapshot / 'database.dump'], env=pg_env)
    shutil.copytree(snapshot / 'filestore', folder / 'data/filestore' / database)
    cfg = native.options(task.BASE / 'clone.conf')
    cfg['options'].update(db_name=database, dbfilter='^' + database + '$', data_dir=str(folder / 'data'), http_port='19190')
    config = folder / 'odoo.conf'
    with config.open('w', encoding='utf-8') as output:
        cfg.write(output)

    def run(label, extra, code=None):
        log = folder / f'{label}.log'
        command = [sys.executable, '-X', 'utf8', str(task.ROOT / 'odoo-bin')]
        if code:
            command.append('shell')
        command += ['-c', str(config), '-d', database, '--no-http', '--logfile', str(log), *extra]
        done = subprocess.run(command, input=code, text=True, encoding='utf-8', cwd=task.ROOT,
                              capture_output=True, check=False)
        (folder / f'{label}.console.log').write_text(done.stdout + done.stderr, encoding='utf-8')
        lines = log.read_text(encoding='utf-8', errors='replace').splitlines()
        native.require(done.returncode == 0 and not any(' ERROR ' in line or ' CRITICAL ' in line for line in lines),
                       f'Policy verification {label} failed; inspect private log.')

    keys = ('auth_signup.invitation_scope', 'auth_signup.reset_password')
    run('neutralize-absent', [], f"""
p=env['ir.config_parameter'].sudo()
env['ir.cron'].search([]).write({{'active':False}})
env['ir.mail_server'].search([]).write({{'active':False}})
p.set_str('database.is_neutralized','True')
p.search([('key','in',{keys!r})]).unlink()
env.cr.commit()
""")
    run('install-absent', ['-i', 'tp_web_login', '--stop-after-init'])
    run('verify-absent-set-disabled', [], f"""
p=env['ir.config_parameter'].sudo()
assert not p.search_count([('key','in',{keys!r})]), 'Absent policy keys were created by install'
p.set_str('auth_signup.invitation_scope','b2b')
p.set_bool('auth_signup.reset_password',False)
env.cr.commit()
""")
    with native.connect(database) as conn, conn.cursor() as cur:
        cur.execute('SELECT key,value FROM ir_config_parameter WHERE key IN %s ORDER BY key', (keys,))
        before = cur.fetchall()
    run('upgrade-disabled', ['-u', 'tp_web_login', '--stop-after-init'])
    with native.connect(database) as conn, conn.cursor() as cur:
        cur.execute('SELECT key,value FROM ir_config_parameter WHERE key IN %s ORDER BY key', (keys,))
        native.require(cur.fetchall() == before, 'Upgrade changed disabled policy.')
    native.write(task.BASE / 'policy-result.json', {'ok': True, 'database': database, 'absent_install_preserved': True,
                 'disabled_upgrade_preserved': True, 'email_jobs_neutralized': True})
    print('POLICY PASS: absent keys survive install; configured disabled values survive upgrade; owned neutralized DB.')


if __name__ == '__main__':
    main()
