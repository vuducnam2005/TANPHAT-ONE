"""Synthetic MFA/passkey actor, owned clone only; no dev writes."""
# ruff: noqa: T201
import base64
import secrets

import ui_shell_auth001 as task


def main():
    native = task.bind()
    native.target_config('clone')
    destination = task.BASE / 'fixture.json'
    native.require(not destination.exists(), 'Reuse the existing synthetic fixture.')

    def create(env):
        login = 'shellauth001.synthetic'
        native.require(not env['res.users'].search_count([('login', '=', login)]), 'Foreign fixture actor exists.')
        password = secrets.token_urlsafe(32)
        secret = base64.b32encode(secrets.token_bytes(20)).decode()
        actor = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Kiểm thử xác thực', 'login': login, 'password': password,
            'group_ids': [(6, 0, [env.ref('base.group_user').id])],
            'lang': 'vi_VN', 'tz': 'Asia/Ho_Chi_Minh',
        })
        actor.totp_secret = secret
        env.cr.commit()
        return {'login': login, 'password': password, 'totp_secret': secret, 'uid': actor.id,
                'database': task.DB, 'origin': f'http://127.0.0.1:{task.PORT}'}

    native.write(destination, native.orm('clone', create))
    print('Synthetic MFA actor created only on owned clone; private fixture saved.')


if __name__ == '__main__':
    main()
