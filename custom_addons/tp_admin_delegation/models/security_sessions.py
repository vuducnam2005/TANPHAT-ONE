"""Apply DEC-062 to native session revocation, including sudo within RPC."""
from odoo import api, models
from odoo.exceptions import AccessError
from odoo.http import request

from .guards import (
    _MFA_COUNTER,
    _is_trusted_original_or_cli,
    _lock_account_targets,
    account_actor_uid,
    account_target_kind,
    assert_can_manage_account_targets,
)


def check_session_targets(records):
    _lock_account_targets(records.env, records)
    if _is_trusted_original_or_cli(records.env):
        return
    actor = account_actor_uid(records.env)
    caller = records.env['res.users'].with_user(actor).browse(actor)
    for target in records.sudo():
        if target.id == actor:
            continue
        if account_target_kind(target) != 'employee' or not caller._tp_has_live_admin_grant():
            raise AccessError(records.env._('Không được thay đổi phiên của Quản trị gốc hoặc admin ủy quyền khác.'))


class ProtectedUserSessions(models.Model):
    _inherit = 'res.users'

    def _tp_account_role_label(self):
        self.ensure_one()
        if self.has_group('tp_admin_delegation.group_original_admin'):
            return 'original_admin', 'Quản trị gốc'
        if self._tp_has_live_admin_grant():
            return 'granted_admin', 'Quản trị viên ủy quyền'
        if self.has_group('hr.group_hr_manager'):
            return 'hr_manager', 'Quản lý nhân sự'
        return super()._tp_account_role_label()

    def _check_credentials(self, credential, env):
        if (request and not request.session.uid and self.ids == [request.session.get('pre_uid')]
                and credential.get('type') == 'totp'):
            return super(ProtectedUserSessions, self.with_context(_tp_native_mfa=_MFA_COUNTER))._check_credentials(credential, env)
        return super()._check_credentials(credential, env)

    def _action_revoke_all_devices(self):
        check_session_targets(self)
        return super()._action_revoke_all_devices()


class ProtectedSessions(models.Model):
    _inherit = 'res.session'

    def _revoke(self):
        check_session_targets(self.sudo().user_id.with_env(self.env))
        revoking_current = bool(self.filtered('is_current'))
        winner_snapshot = None
        if revoking_current and request and getattr(request, 'session', None):
            sess = request.session
            winner_snapshot = (
                sess.get('tp_session_uid') or self.env.uid,
                sess.get('tp_session_gen'),
                sess.get('tp_session_nonce'),
            )
        res = super()._revoke()
        if winner_snapshot:
            from odoo.addons.tp_web_login.models.session_guard import compare_and_clear_winner_in_cr
            compare_and_clear_winner_in_cr(self.env.cr, *winner_snapshot)
        return res


class ProtectedPasskeys(models.Model):
    _inherit = 'auth.passkey.key'

    def _tp_check_owner_boundary(self, vals=None):
        targets = self.sudo().create_uid
        if vals and vals.get('create_uid'):
            targets |= self.env['res.users'].browse(vals['create_uid'])
        assert_can_manage_account_targets(self.env, targets, allow_self=True)

    @api.model_create_multi
    def create(self, vals_list):
        targets = self.env['res.users'].browse([vals.get('create_uid', self.env.uid) for vals in vals_list])
        assert_can_manage_account_targets(self.env, targets, allow_self=True)
        return super().create(vals_list)

    @api.model
    def _start_registration(self):
        options = super()._start_registration()
        options['rp']['name'] = 'TANPHAT ONE'
        return options

    def write(self, vals):
        self._tp_check_owner_boundary(vals)
        return super().write(vals)

    def unlink(self):
        self._tp_check_owner_boundary()
        return super().unlink()
