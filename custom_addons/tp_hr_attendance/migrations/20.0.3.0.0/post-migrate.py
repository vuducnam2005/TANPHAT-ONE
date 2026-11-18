"""HR-ATTENDANCE-MATRIX-003 (20.0.2.1.0): backfill batch codes, multi-source provenance and file snapshots."""
from odoo import SUPERUSER_ID, api

from odoo.addons.tp_hr_attendance.models.attendance_matrix import _tp_migrate_matrix_003


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    _tp_migrate_matrix_003(env)
