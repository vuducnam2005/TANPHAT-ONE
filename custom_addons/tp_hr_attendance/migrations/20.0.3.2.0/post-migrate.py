"""CHG-20261119-005 (20.0.3.2.0): submitted corrections now route to the Original Admin only.

Recompute the stored reviewer list (read rule) of every non-draft request so it holds the company's
Original Admin(s) instead of former review assignees. States, hours, sessions and days are untouched.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['tp.hr.attendance.correction']._tp_refresh_reviewers()
