"""Diagnostic breadcrumb for browser-side passkey failures.

Native auth_passkey swallows browser WebAuthn errors, so a failed ceremony
leaves no trace on the server. The client reports only whitelisted enums:
no credential, challenge, cookie, user id or free text is accepted or logged.
"""
import logging
import re

from odoo import http

_logger = logging.getLogger(__name__)

PHASES = frozenset({'login', 'register', 'identity'})
KINDS = frozenset({
    'not_allowed', 'aborted', 'domain', 'duplicate', 'capability', 'authenticator',
    'unsupported', 'network', 'server', 'unknown',
})
_TOKEN = re.compile(r'^[A-Za-z_]{1,64}$')


class PasskeyDiagnostics(http.Controller):

    @http.route('/tp_web_login/passkey/client-event', type='jsonrpc', auth='public', methods=['POST'])
    def passkey_client_event(self, phase=None, kind=None, name=None, code=None):
        if phase not in PHASES or kind not in KINDS:
            return False
        name = name if isinstance(name, str) and _TOKEN.match(name) else '-'
        code = code if isinstance(code, str) and _TOKEN.match(code) else '-'
        _logger.info("Passkey browser %s did not complete: kind=%s name=%s code=%s", phase, kind, name, code)
        return True
