"""Cooperative HTTP/session controller hooks for AUTH-SESSION-001."""
import contextlib

import odoo.modules.registry
from odoo import SUPERUSER_ID, api, http
from odoo.http import request

from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.auth_totp.controllers.home import Home as TotpHome
from odoo.addons.tp_web_login.models.session_guard import (
    SESSION_CUTOVER_REASON,
    SESSION_REPLACED_REASON,
    compare_and_clear_winner_in_cr,
)
from odoo.addons.web.controllers.session import Session as WebSession


def _clear_current_session_winner_if_matching() -> None:
    """Compare-and-clear the caller's winner in PostgreSQL without affecting any newer login."""
    sess = getattr(request, 'session', None)
    if sess is None:
        return
    uid = sess.get('tp_session_uid') or sess.uid
    gen = sess.get('tp_session_gen')
    nonce = sess.get('tp_session_nonce')
    dbname = getattr(request, 'db', None) or sess.db
    sess.pop('tp_ended_reason', None)
    sess.pop('tp_ended_at', None)
    sess.pop('tp_login_notice', None)
    if not (dbname and uid and gen and nonce):
        return
    with contextlib.suppress(Exception):
        if request.env and not request.env.cr.closed and not request.env.cr.readonly:
            compare_and_clear_winner_in_cr(request.env.cr, int(uid), gen, nonce)
        else:
            with odoo.modules.registry.Registry(dbname).cursor() as cr:
                compare_and_clear_winner_in_cr(cr, int(uid), gen, nonce)


class TpLoginSessionController(WebSession):

    @http.route()
    def destroy(self):
        _clear_current_session_winner_if_matching()
        return super().destroy()

    @http.route()
    def logout(self, redirect='/odoo'):
        _clear_current_session_winner_if_matching()
        return super().logout(redirect=redirect)


class TpLoginHomeController(AuthSignupHome, TotpHome):

    @http.route()
    def web_client(self, s_action=None, **kw):
        if not request.session.uid and request.session.get('tp_ended_reason') in (
            SESSION_REPLACED_REASON,
            SESSION_CUTOVER_REASON,
        ):
            reason = request.session.pop('tp_ended_reason', None)
            request.session.pop('tp_ended_at', None)
            request.session['tp_login_notice'] = reason
            return request.redirect_query('/web/login', query={'redirect': '/odoo/tp-home'}, code=303)
        return super().web_client(s_action=s_action, **kw)

    @http.route()
    def web_login(self, redirect=None, **kw):
        response = super().web_login(redirect=redirect, **kw)
        qcontext = getattr(response, 'qcontext', None)
        if request.httprequest.method == 'GET' and isinstance(qcontext, dict):
            notice = request.session.pop('tp_login_notice', None)
            if notice in (SESSION_REPLACED_REASON, SESSION_CUTOVER_REASON):
                qcontext['tp_login_notice'] = notice
        return response

    @http.route()
    def switch_to_admin(self):
        response = super().switch_to_admin()
        if request.session.uid:
            if not request.env.cr.readonly:
                request.env['res.users'].browse(request.session.uid)._tp_register_winning_session(request.session)
            else:
                with odoo.modules.registry.Registry(request.db).cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    env['res.users'].browse(request.session.uid)._tp_register_winning_session(request.session)
        return response
