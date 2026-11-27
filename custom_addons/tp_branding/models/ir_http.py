# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Expose dynamic XML ID <-> Action ID route map in session_info (SYSTEM-URL-001)."""

from odoo import models

from odoo.addons.tp_branding.brand_routes import get_all_action_xml_ids


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def _tp_get_url_route_map(self):
        """Query actual numeric action IDs for all registered XML IDs in this DB."""
        xml_ids = get_all_action_xml_ids()
        if not xml_ids:
            return {'xml_to_id': {}, 'id_to_xml': {}}

        clauses = []
        params = []
        for xid in xml_ids:
            if '.' in xid:
                mod, name = xid.split('.', 1)
                clauses.append("(module = %s AND name = %s)")
                params.extend([mod, name])

        if not clauses:
            return {'xml_to_id': {}, 'id_to_xml': {}}

        query = f"""
            SELECT module || '.' || name, res_id
            FROM ir_model_data
            WHERE {' OR '.join(clauses)}
        """
        self.env.cr.execute(query, tuple(params))
        rows = self.env.cr.fetchall()

        xml_to_id = {r[0]: r[1] for r in rows}
        id_to_xml = {r[1]: r[0] for r in rows}
        return {
            'xml_to_id': xml_to_id,
            'id_to_xml': id_to_xml,
        }

    def session_info(self):
        res = super().session_info()
        try:
            res['tp_action_routes'] = self._tp_get_url_route_map()
        except Exception:  # noqa: BLE001
            res['tp_action_routes'] = {'xml_to_id': {}, 'id_to_xml': {}}
        return res
