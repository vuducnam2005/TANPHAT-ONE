"""CHG-20261119-023 (20.0.3.4.0): ENTI-LIVE-001 - Live ENTI attendance sync & constraint migration.

Drop tp_hr_attendance_source_live_off so live_enabled=True can be set safely.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    cr.execute("ALTER TABLE tp_hr_attendance_source DROP CONSTRAINT IF EXISTS tp_hr_attendance_source_live_off;")
    cr.execute("DELETE FROM ir_model_constraint WHERE name = 'tp_hr_attendance_source_live_off';")
