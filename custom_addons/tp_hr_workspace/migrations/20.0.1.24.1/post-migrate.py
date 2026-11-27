# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    removed = env["hr.employee"]._tp_cleanup_audit_unsaved_orphans()
    if removed:
        _logger.info("tp_hr_workspace 20.0.1.24.1: cleaned up F-0002 unsaved test orphans: %s", removed)
