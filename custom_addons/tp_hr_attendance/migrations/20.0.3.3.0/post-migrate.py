"""CHG-20261119-012 (20.0.3.3.0): delegated Full Admins with a live grant also handle corrections.

Recompute the stored recipient list of every non-draft request so it holds the company's admins
(Original Admin(s) + delegated Full Admins with a live grant in that company). Read access for those
admins comes from base.group_system; the old recipient-list read row is dropped by the module update,
so a revoked admin loses access at once. States, hours, sessions and days are untouched.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['tp.hr.attendance.correction']._tp_refresh_reviewers()
