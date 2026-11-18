"""Idempotent upgrade migration for ADMIN-FULL-001 (DEC-053 / DEC-054)."""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['tp.admin.delegation']._migrate_admin_full_001()
