"""Single active web/PWA session per account with PostgreSQL winner serialization (AUTH-SESSION-001 / DEC-057)."""
import contextlib
import logging
import secrets
import time
from urllib.parse import quote

from odoo import api, models
from odoo.http import request
from odoo.http.session import (
    CheckIdentityException,
    SessionExpiredException,
    logout,
    session_store,
)
from odoo.modules.registry import Registry
from odoo.tools import config, consteq, hmac
from odoo.tools.misc import submap

from odoo.addons.bus.websocket import wsrequest

_logger = logging.getLogger(__name__)

AUTH_SESSION_LOCK_NS = 761157
SESSION_REPLACED_REASON = 'session_replaced'
SESSION_CUTOVER_REASON = 'session_cutover'

SESSION_REPLACED_TITLE = 'Tài khoản của bạn đang được đăng nhập ở nơi khác.'
SESSION_REPLACED_DETAIL = 'Phiên làm việc trên thiết bị này đã kết thúc. Vui lòng đăng nhập lại để tiếp tục.'
SESSION_REPLACED_MESSAGE = f'{SESSION_REPLACED_TITLE} {SESSION_REPLACED_DETAIL}'

SESSION_CUTOVER_TITLE = 'Hệ thống vừa cập nhật phiên đăng nhập.'
SESSION_CUTOVER_DETAIL = 'Phiên làm việc hiện tại cần được làm mới. Vui lòng đăng nhập lại để tiếp tục.'
SESSION_CUTOVER_MESSAGE = f'{SESSION_CUTOVER_TITLE} {SESSION_CUTOVER_DETAIL}'

_SESSION_KEYS = ('tp_session_uid', 'tp_session_gen', 'tp_session_nonce', 'tp_ended_reason', 'tp_ended_at')


class TpSessionReplacedException(SessionExpiredException):
    """Raised when an authenticated browser session has been superseded by a newer login."""

    tp_reason = SESSION_REPLACED_REASON

    def __init__(self, message=SESSION_REPLACED_MESSAGE):
        super().__init__(message)
        self.context = {'tp_session_reason': SESSION_REPLACED_REASON}


class TpSessionCutoverException(SessionExpiredException):
    """Raised once for pre-deploy legacy browser sessions without a server session generation."""

    tp_reason = SESSION_CUTOVER_REASON

    def __init__(self, message=SESSION_CUTOVER_MESSAGE):
        super().__init__(message)
        self.context = {'tp_session_reason': SESSION_CUTOVER_REASON}


def compute_session_tag(env, uid: int, gen: int) -> str:
    """Return a non-secret one-way tag identifying (db, uid, generation) for UI/bus matching."""
    return hmac(env(su=True), 'tp_session_bus_channel', f'{int(uid)}:{int(gen)}')[:32]


def compute_session_bus_channel(env, uid: int, gen: int) -> str:
    """Return the unguessable server-subscribed bus channel for one session generation."""
    return f'tp_session_guard:{compute_session_tag(env, uid, gen)}'


def ensure_active_session_table(cr) -> None:
    cr.execute(
        """
        CREATE TABLE IF NOT EXISTS tp_user_active_session (
            user_id INTEGER PRIMARY KEY REFERENCES res_users(id) ON DELETE CASCADE,
            session_gen BIGINT NOT NULL DEFAULT 0,
            session_nonce VARCHAR(86),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
        )
        """,
    )


def verify_session_winner_in_cr(
    cr,
    uid: int,
    sess_uid,
    sess_gen,
    sess_nonce,
    *,
    acquire_shared_lock: bool = False,
    allow_test_synthetic: bool = False,
    winner_cursor_factory=None,
) -> None:
    """Verify against PostgreSQL that (sess_uid, sess_gen, sess_nonce) is the live winner for uid."""
    if not sess_nonce or not sess_gen or sess_uid != uid:
        if allow_test_synthetic:
            return
        raise TpSessionCutoverException()

    try:
        gen_int = int(sess_gen)
    except (TypeError, ValueError) as exc:
        raise TpSessionCutoverException() from exc

    if gen_int <= 0 or not isinstance(sess_nonce, str):
        raise TpSessionCutoverException()

    if acquire_shared_lock and not getattr(cr, 'readonly', False):
        cr.execute('SELECT pg_advisory_xact_lock_shared(%s, %s)', [AUTH_SESSION_LOCK_NS, int(uid)])

    # Odoo uses REPEATABLE READ: an advisory lock does not refresh the request
    # snapshot. Read the winner on a fresh primary cursor AFTER taking the lock.
    # The request's shared lock remains held until its business transaction ends,
    # so a new login cannot commit between this check and the business commit.
    with winner_cursor_factory() if winner_cursor_factory else contextlib.nullcontext(cr) as winner_cr:
        winner_cr.execute(
            'SELECT session_gen, session_nonce FROM tp_user_active_session WHERE user_id = %s',
            [int(uid)],
        )
        row = winner_cr.fetchone()
    if not row:
        raise TpSessionCutoverException()

    db_gen, db_nonce = int(row[0] or 0), row[1]
    if db_gen != gen_int:
        raise TpSessionReplacedException()
    if not db_nonce:
        # Same generation explicitly logged out; not replaced by another login.
        msg = 'session has logged out'
        raise SessionExpiredException(msg)
    if not consteq(str(db_nonce), sess_nonce):
        raise TpSessionReplacedException()


def compare_and_clear_winner_in_cr(cr, uid: int, sess_gen, sess_nonce) -> bool:
    """Atomically clear session_nonce ONLY if (uid, sess_gen, sess_nonce) is still the live winner."""
    if not uid or not sess_gen or not sess_nonce or not isinstance(sess_nonce, str):
        return False
    try:
        gen_int = int(sess_gen)
    except (TypeError, ValueError):
        return False
    if gen_int <= 0:
        return False
    cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [AUTH_SESSION_LOCK_NS, int(uid)])
    cr.execute(
        """
        UPDATE tp_user_active_session
           SET session_nonce = NULL,
               updated_at = (now() AT TIME ZONE 'utc')
         WHERE user_id = %s
           AND session_gen = %s
           AND session_nonce = %s
        """,
        [int(uid), gen_int, sess_nonce],
    )
    return cr.rowcount > 0


class ResUsersSingleSession(models.Model):
    _inherit = 'res.users'

    def init(self):
        super().init()
        ensure_active_session_table(self.env.cr)

    @api.model
    def _tp_session_tag(self, uid: int, gen: int) -> str:
        return compute_session_tag(self.env, uid, gen)

    @api.model
    def _tp_session_bus_channel(self, uid: int, gen: int) -> str:
        return compute_session_bus_channel(self.env, uid, gen)

    def _tp_register_winning_session(self, session) -> tuple[int, str]:
        """Serialize login per user, persist new winner in PostgreSQL, and notify replaced session on commit."""
        self.ensure_one()
        uid = int(self.id)
        prev_sess_uid = session.get('tp_session_uid')
        prev_sess_gen = session.get('tp_session_gen')
        prev_sess_nonce = session.get('tp_session_nonce')

        lock_uids = sorted({uid} | ({int(prev_sess_uid)} if isinstance(prev_sess_uid, int) and prev_sess_uid > 0 else set()))
        for lock_uid in lock_uids:
            self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [AUTH_SESSION_LOCK_NS, lock_uid])

        # A successful native login may switch users in an existing cookie. The
        # final-login hook now owns both exclusive locks and the winner update;
        # do not revalidate the deliberately retired identity before this commit.
        self.env.cr.precommit.data.pop('tp_auth_precommit_winner', None)

        if isinstance(prev_sess_uid, int) and prev_sess_uid > 0 and prev_sess_uid != uid:
            compare_and_clear_winner_in_cr(self.env.cr, prev_sess_uid, prev_sess_gen, prev_sess_nonce)

        self.env.cr.execute(
            'SELECT session_gen, session_nonce FROM tp_user_active_session WHERE user_id = %s FOR UPDATE',
            [uid],
        )
        row = self.env.cr.fetchone()
        db_prev_gen, db_prev_nonce = (int(row[0] or 0), row[1]) if row else (0, None)

        # Re-submitting login from the exact same winning browser profile keeps the same generation
        # so sibling tabs sharing this cookie are never disrupted.
        if (
            prev_sess_uid == uid
            and prev_sess_nonce
            and db_prev_nonce
            and int(prev_sess_gen or 0) == db_prev_gen
            and consteq(str(prev_sess_nonce), str(db_prev_nonce))
        ):
            session.pop('tp_ended_reason', None)
            session.pop('tp_ended_at', None)
            return db_prev_gen, str(db_prev_nonce)

        snapshot = {key: session.get(key) for key in _SESSION_KEYS}
        had_uid_before = snapshot.get('tp_session_uid') == uid and bool(snapshot.get('tp_session_nonce'))

        new_nonce = secrets.token_urlsafe(32)
        self.env.cr.execute(
            """
            INSERT INTO tp_user_active_session (user_id, session_gen, session_nonce, updated_at)
            VALUES (%s, 1, %s, (now() AT TIME ZONE 'utc'))
            ON CONFLICT (user_id) DO UPDATE
               SET session_gen = tp_user_active_session.session_gen + 1,
                   session_nonce = EXCLUDED.session_nonce,
                   updated_at = (now() AT TIME ZONE 'utc')
            RETURNING session_gen
            """,
            [uid, new_nonce],
        )
        new_gen = int(self.env.cr.fetchone()[0])

        session['tp_session_uid'] = uid
        session['tp_session_gen'] = new_gen
        session['tp_session_nonce'] = new_nonce
        session.pop('tp_ended_reason', None)
        session.pop('tp_ended_at', None)

        @self.env.cr.postrollback.add
        def _restore_session_on_login_rollback():
            if not had_uid_before:
                logout(session, keep_db=True)
            for key, val in snapshot.items():
                if val is None:
                    session.pop(key, None)
                else:
                    session[key] = val

        if db_prev_gen > 0 and db_prev_nonce:
            replaced_tag = self._tp_session_tag(uid, db_prev_gen)
            replaced_channel = f'tp_session_guard:{replaced_tag}'
            self.env['bus.bus']._sendone(
                replaced_channel,
                'tp.auth/session_replaced',
                {
                    'reason': SESSION_REPLACED_REASON,
                    'replaced_tag': replaced_tag,
                },
            )

        return new_gen, new_nonce

    def _after_session_login(self):
        super()._after_session_login()
        if not request or getattr(request, 'session', None) is None:
            return
        self._tp_register_winning_session(request.session)


class IrHttpSingleSession(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _tp_allow_test_synthetic_session(cls, session) -> bool:
        return bool(
            config['test_enable']
            and session.get('_trace_disable')
            and not session.get('tp_session_nonce')
            and not session.get('tp_test_enforce_single_session'),
        )

    @classmethod
    def _tp_terminate_stale_session(cls, session, reason: str | None = None) -> None:
        """Clear authenticated state from a stale session file without touching the DB winner."""
        logout(session, keep_db=True)
        if reason in (SESSION_REPLACED_REASON, SESSION_CUTOVER_REASON):
            session['tp_ended_reason'] = reason
            session['tp_ended_at'] = int(time.time())
            # Keep the same SID file carrying the tombstone so sibling tabs sharing this cookie
            # receive the exact replaced/cutover reason before final re-login rotation.
            session.should_rotate = False
        with contextlib.suppress(Exception):
            if session.can_save and session.sid:
                session_store().save(session)

    @classmethod
    def _tp_verify_session_winner(cls, env, session, *, acquire_shared_lock: bool = False) -> None:
        uid = session.uid
        if uid is None:
            return
        allow_synth = cls._tp_allow_test_synthetic_session(session)
        verify_session_winner_in_cr(
            env.cr,
            int(uid),
            session.get('tp_session_uid'),
            session.get('tp_session_gen'),
            session.get('tp_session_nonce'),
            acquire_shared_lock=acquire_shared_lock,
            allow_test_synthetic=allow_synth,
            winner_cursor_factory=(lambda: Registry(env.cr.dbname).cursor(readonly=True)) if not allow_synth else None,
        )
        if (
            not allow_synth
            and not env.cr.readonly
            and 'tp_auth_precommit_winner' not in env.cr.precommit.data
        ):
            bound = (
                int(uid),
                session.get('tp_session_uid'),
                session.get('tp_session_gen'),
                session.get('tp_session_nonce'),
            )
            env.cr.precommit.data['tp_auth_precommit_winner'] = bound

            @env.cr.precommit.add
            def _verify_winner_before_commit():
                bound_session = env.cr.precommit.data.pop('tp_auth_precommit_winner', None)
                if bound_session is None:
                    return
                b_uid, b_sess_uid, b_gen, b_nonce = bound_session
                verify_session_winner_in_cr(
                    env.cr,
                    b_uid,
                    b_sess_uid,
                    b_gen,
                    b_nonce,
                    acquire_shared_lock=True,
                    allow_test_synthetic=False,
                    winner_cursor_factory=Registry(env.cr.dbname).cursor,
                )

    @classmethod
    def _authenticate_explicit(cls, routing: dict):
        sess = request.session
        had_uid = sess.uid is not None
        prior_ended_reason = (
            sess.get('tp_ended_reason')
            if not had_uid and sess.get('tp_ended_reason') in (SESSION_REPLACED_REASON, SESSION_CUTOVER_REASON)
            else None
        )
        try:
            super()._authenticate_explicit(routing)
        except SessionExpiredException as exc:
            if had_uid and sess.uid is None:
                sess.pop('tp_ended_reason', None)
                sess.pop('tp_ended_at', None)
                raise
            if prior_ended_reason and not isinstance(exc, CheckIdentityException):
                replaced_exc = (
                    TpSessionReplacedException()
                    if prior_ended_reason == SESSION_REPLACED_REASON
                    else TpSessionCutoverException()
                )
                raise replaced_exc from exc
            raise

        if had_uid and sess.uid is not None:
            safe_context = submap(request.env.context, ('lang', 'tz', 'website_id'))
            try:
                cls._tp_verify_session_winner(
                    request.env,
                    sess,
                    acquire_shared_lock=not request.env.cr.readonly,
                )
            except (TpSessionReplacedException, TpSessionCutoverException) as exc:
                cls._tp_terminate_stale_session(sess, exc.tp_reason)
                safe_context.update(sess.context)
                request.env = api.Environment(request.env.cr, None, safe_context)
                request.env.transaction.default_env = request.env
                try:
                    getattr(cls, f"_auth_method_{routing['auth']}")(routing)
                except SessionExpiredException as auth_exc:
                    raise exc from auth_exc
            except SessionExpiredException as exc:
                cls._tp_terminate_stale_session(sess, None)
                safe_context.update(sess.context)
                request.env = api.Environment(request.env.cr, None, safe_context)
                request.env.transaction.default_env = request.env
                try:
                    getattr(cls, f"_auth_method_{routing['auth']}")(routing)
                except SessionExpiredException as auth_exc:
                    raise auth_exc from exc

    @classmethod
    def _tp_relogin_url(cls, env) -> str:
        branded = 'tp_branding' in env.registry._init_modules
        login_path = '/dang-nhap' if branded else '/web/login'
        home_path = '/app/trang-chu' if branded else '/odoo/tp-home'
        return f'{login_path}?redirect={quote(home_path, safe="")}'

    def session_info(self):
        info = super().session_info()
        sess = request.session
        if sess.uid and sess.get('tp_session_uid') == sess.uid and sess.get('tp_session_gen'):
            info['tp_session_tag'] = compute_session_tag(self.env, sess.uid, sess.get('tp_session_gen'))
        else:
            info['tp_session_tag'] = None
        info['tp_relogin_url'] = self._tp_relogin_url(self.env)
        return info


class IrWebsocketSingleSession(models.AbstractModel):
    _inherit = 'ir.websocket'

    def _build_bus_channel_list(self, channels):
        channels = super()._build_bus_channel_list(channels)
        req = request or wsrequest
        if (
            req
            and req.session.uid
            and req.session.get('tp_session_uid') == req.session.uid
            and req.session.get('tp_session_gen')
        ):
            channels.append(
                compute_session_bus_channel(self.env, req.session.uid, req.session.get('tp_session_gen')),
            )
        return channels

    @classmethod
    def _authenticate(cls):
        had_uid = wsrequest.session.uid is not None
        super()._authenticate()
        if had_uid and wsrequest.session.uid is not None:
            try:
                wsrequest.env['ir.http']._tp_verify_session_winner(
                    wsrequest.env,
                    wsrequest.session,
                    acquire_shared_lock=False,
                )
            except (TpSessionReplacedException, TpSessionCutoverException) as exc:
                wsrequest.env['ir.http']._tp_terminate_stale_session(wsrequest.session, exc.tp_reason)
                raise
            except SessionExpiredException:
                wsrequest.env['ir.http']._tp_terminate_stale_session(wsrequest.session, None)
                raise
