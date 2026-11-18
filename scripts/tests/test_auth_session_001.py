"""Pure-Python unit tests for AUTH-SESSION-001 single active web session invariants."""
from __future__ import annotations

import pathlib
import sys
import unittest
from contextlib import contextmanager

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import odoo.addons  # noqa: E402

for _addon_dir in (ROOT / "addons", ROOT / "custom_addons"):
    if str(_addon_dir) not in odoo.addons.__path__:
        odoo.addons.__path__.append(str(_addon_dir))

from odoo.http.session import SessionExpiredException  # noqa: E402

from odoo.addons.tp_web_login.models.session_guard import (  # noqa: E402
    AUTH_SESSION_LOCK_NS,
    SESSION_CUTOVER_REASON,
    SESSION_REPLACED_DETAIL,
    SESSION_REPLACED_REASON,
    SESSION_REPLACED_TITLE,
    TpSessionCutoverException,
    TpSessionReplacedException,
    compare_and_clear_winner_in_cr,
    verify_session_winner_in_cr,
)


class FakeCursor:
    """Deterministic in-memory stand-in for PostgreSQL cursor SQL executed by session_guard."""

    def __init__(self, *, readonly: bool = False):
        self.readonly = readonly
        self.rows: dict[int, tuple[int, str | None]] = {}
        self.locks: list[tuple[str, int, int]] = []
        self._last_fetch: tuple | None = None
        self.rowcount = 0

    def execute(self, query, params=None):
        sql = " ".join(str(query).split())
        params = list(params or [])
        self._last_fetch = None
        self.rowcount = 0
        if "pg_advisory_xact_lock_shared" in sql:
            self.locks.append(("shared", int(params[0]), int(params[1])))
        elif "pg_advisory_xact_lock" in sql:
            self.locks.append(("exclusive", int(params[0]), int(params[1])))
        elif sql.startswith("SELECT session_gen, session_nonce FROM tp_user_active_session"):
            uid = int(params[0])
            self._last_fetch = self.rows.get(uid)
            self.rowcount = 1 if self._last_fetch is not None else 0
        elif sql.startswith("UPDATE tp_user_active_session SET session_nonce = NULL"):
            uid, gen, nonce = int(params[0]), int(params[1]), str(params[2])
            cur = self.rows.get(uid)
            if cur and cur[0] == gen and cur[1] == nonce:
                self.rows[uid] = (gen, None)
                self.rowcount = 1
        else:
            raise AssertionError(f"Unexpected SQL: {sql}")

    def fetchone(self):
        return self._last_fetch


class TestAuthSession001(unittest.TestCase):

    def test_repeatable_read_snapshot_cannot_authorize_revoked_request(self):
        """Request snapshot predates B's commit: fresh winner must reject A."""
        request_cr = FakeCursor()
        request_cr.rows[7] = (3, "old-a")
        primary_cr = FakeCursor()
        primary_cr.rows[7] = (4, "new-b")

        @contextmanager
        def fresh_primary_cursor():
            # Serialize against login before opening the independent snapshot.
            self.assertEqual(request_cr.locks, [("shared", AUTH_SESSION_LOCK_NS, 7)])
            yield primary_cr

        with self.assertRaises(TpSessionReplacedException):
            verify_session_winner_in_cr(
                request_cr, 7, 7, 3, "old-a", acquire_shared_lock=True,
                winner_cursor_factory=fresh_primary_cursor,
            )
        self.assertEqual(request_cr.rows[7], (3, "old-a"))

    def test_readonly_route_checks_fresh_primary_instead_of_stale_replica(self):
        request_cr = FakeCursor(readonly=True)
        request_cr.rows[7] = (3, "old-a")
        primary_cr = FakeCursor()
        primary_cr.rows[7] = (4, "new-b")

        @contextmanager
        def fresh_primary_cursor():
            yield primary_cr

        with self.assertRaises(TpSessionReplacedException):
            verify_session_winner_in_cr(
                request_cr, 7, 7, 3, "old-a", acquire_shared_lock=True,
                winner_cursor_factory=fresh_primary_cursor,
            )
        self.assertEqual(request_cr.locks, [])

    def test_mandatory_vietnamese_copy_and_exception_context(self):
        exc_rep = TpSessionReplacedException()
        self.assertIsInstance(exc_rep, SessionExpiredException)
        self.assertEqual(exc_rep.tp_reason, SESSION_REPLACED_REASON)
        self.assertEqual(exc_rep.context, {"tp_session_reason": SESSION_REPLACED_REASON})
        self.assertIn(SESSION_REPLACED_TITLE, str(exc_rep))
        self.assertIn(SESSION_REPLACED_DETAIL, str(exc_rep))

        exc_cut = TpSessionCutoverException()
        self.assertIsInstance(exc_cut, SessionExpiredException)
        self.assertEqual(exc_cut.tp_reason, SESSION_CUTOVER_REASON)
        self.assertEqual(exc_cut.context, {"tp_session_reason": SESSION_CUTOVER_REASON})
        self.assertNotIn("đăng nhập ở nơi khác", str(exc_cut))

    def test_legacy_session_without_nonce_raises_cutover_not_replaced(self):
        cr = FakeCursor()
        cr.rows[42] = (1, "winner-nonce")
        with self.assertRaises(TpSessionCutoverException):
            verify_session_winner_in_cr(cr, 42, None, None, None)
        with self.assertRaises(TpSessionCutoverException):
            verify_session_winner_in_cr(cr, 42, 99, 1, "winner-nonce")
        # Synthetic test-harness session allowed only when explicitly flagged
        verify_session_winner_in_cr(cr, 42, None, None, None, allow_test_synthetic=True)

    def test_matching_winner_succeeds_and_acquires_shared_lock_on_mutating_cursor(self):
        cr = FakeCursor(readonly=False)
        cr.rows[7] = (3, "nonce-v3")
        verify_session_winner_in_cr(cr, 7, 7, 3, "nonce-v3", acquire_shared_lock=True)
        self.assertEqual(cr.locks, [("shared", AUTH_SESSION_LOCK_NS, 7)])

        ro_cr = FakeCursor(readonly=True)
        ro_cr.rows[7] = (3, "nonce-v3")
        verify_session_winner_in_cr(ro_cr, 7, 7, 3, "nonce-v3", acquire_shared_lock=True)
        self.assertEqual(ro_cr.locks, [])

    def test_newer_generation_or_mismatched_nonce_raises_session_replaced(self):
        cr = FakeCursor()
        cr.rows[7] = (4, "nonce-b")
        with self.assertRaises(TpSessionReplacedException):
            verify_session_winner_in_cr(cr, 7, 7, 3, "nonce-a")
        with self.assertRaises(TpSessionReplacedException):
            verify_session_winner_in_cr(cr, 7, 7, 4, "nonce-a")

    def test_compare_and_clear_old_logout_never_clears_newer_winner(self):
        cr = FakeCursor()
        cr.rows[15] = (2, "nonce-device-b")
        # Stale Device A (gen=1) logs out after Device B (gen=2) won
        cleared_a = compare_and_clear_winner_in_cr(cr, 15, 1, "nonce-device-a")
        self.assertFalse(cleared_a)
        self.assertEqual(cr.rows[15], (2, "nonce-device-b"))
        verify_session_winner_in_cr(cr, 15, 15, 2, "nonce-device-b")

        # Device B itself logs out -> clears nonce, keeps generation=2
        cleared_b = compare_and_clear_winner_in_cr(cr, 15, 2, "nonce-device-b")
        self.assertTrue(cleared_b)
        self.assertEqual(cr.rows[15], (2, None))

        # Device A still gets session_replaced (because gen 1 != 2), while a stale copy of B gets plain expired
        with self.assertRaises(TpSessionReplacedException):
            verify_session_winner_in_cr(cr, 15, 15, 1, "nonce-device-a")
        with self.assertRaises(SessionExpiredException) as ctx:
            verify_session_winner_in_cr(cr, 15, 15, 2, "nonce-device-b")
        self.assertNotIsInstance(ctx.exception, TpSessionReplacedException)

    def test_frontend_bundle_contains_required_copy_and_single_relogin_button(self):
        xml_text = (ROOT / "custom_addons/tp_web_login/static/src/xml/session_guard.xml").read_text(encoding="utf-8")
        js_text = (ROOT / "custom_addons/tp_web_login/static/src/js/session_guard.js").read_text(encoding="utf-8")
        self.assertIn("Đăng nhập lại", xml_text)
        self.assertIn(SESSION_REPLACED_TITLE, js_text)
        self.assertIn(SESSION_REPLACED_DETAIL, js_text)
        self.assertIn("ConnectionLostError", js_text)
        self.assertIn("CLEAR-CACHES", js_text)


if __name__ == "__main__":
    unittest.main()
