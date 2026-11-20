"""HR-EMPLOYEE-CODE-003: refresh the stored employee code copies in attendance.

tp_organization 20.0.2.3.0 converts TP1nnnn -> TPnnn before this module is
loaded, so its write cannot refresh the copies kept on attendance days and
correction requests. This copies each employee's current code to those rows
(by employee and company), closed periods included, and nothing else: hours,
units, states, ENTI identities and source mappings stay unchanged.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {'active_test': False})
    changed = env['hr.employee'].search([])._tp_sync_attendance_code()
    _logger.info('HR-EMPLOYEE-CODE-003 attendance code copies refreshed: %s rows', changed)
