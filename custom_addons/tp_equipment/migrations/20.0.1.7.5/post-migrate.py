# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
import uuid


def migrate(cr, version):
    """Backfill unique opaque tp_qr_token on any legacy maintenance.equipment rows missing it (F-A01-0001)."""
    if not version:
        return
    cr.execute(
        """
        SELECT id
          FROM maintenance_equipment
         WHERE tp_qr_token IS NULL OR BTRIM(tp_qr_token) = ''
         ORDER BY id
        """,
    )
    missing_ids = [row[0] for row in cr.fetchall()]
    for eq_id in missing_ids:
        cr.execute(
            "UPDATE maintenance_equipment SET tp_qr_token = %s WHERE id = %s",
            [uuid.uuid4().hex, eq_id],
        )
