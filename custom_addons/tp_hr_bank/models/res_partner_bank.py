from odoo import api, fields, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    tp_bank_id = fields.Many2one('tp.bank', string='Ngân hàng', ondelete='restrict', index='btree_not_null')

    @api.model
    def _tp_bank_vals(self, vals):
        """Keep the standard bank name / identifier fields in step with the chosen catalogue bank.

        ``bank_bic`` carries the NAPAS BIN, as the Vietnamese localisation (VietQR) expects.
        """
        if not vals.get('tp_bank_id'):
            return vals
        bank = self.env['tp.bank'].sudo().with_context(active_test=False).browse(vals['tp_bank_id']).exists()
        if bank:
            vals = dict(vals, bank_name=bank.short_name, bank_bic=bank.bin or bank.swift or False)
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._tp_bank_vals(vals) for vals in vals_list])

    def write(self, vals):
        return super().write(self._tp_bank_vals(vals))

    @api.onchange('tp_bank_id')
    def _onchange_tp_bank_id(self):
        if self.tp_bank_id:
            self.bank_name = self.tp_bank_id.short_name
            self.bank_bic = self.tp_bank_id.bin or self.tp_bank_id.swift or False
