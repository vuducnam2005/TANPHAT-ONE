"""Backfill responsibility only when a single explicit creation actor exists."""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    audits = env['tp.contract.audit'].search([
        ('action', 'in', ['create_contract', 'create_amendment']), ('revision_id', '!=', False)])
    for revision in audits.revision_id.filtered(lambda row: not row.business_owner_id):
        actors = audits.filtered(lambda event: event.revision_id == revision).actor_id
        if len(actors) == 1:
            # Existing creation evidence supplies the actor; unrelated legacy rows stay unknown.
            cr.execute("UPDATE tp_contract_revision SET business_owner_id=%s WHERE id=%s AND business_owner_id IS NULL",
                       [actors.id, revision.id])
