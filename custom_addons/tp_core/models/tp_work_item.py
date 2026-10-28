from odoo import fields, models


class TpWorkItem(models.Model):
    _name = 'tp.work.item'
    _description = 'Tan Phat Work Item Catalog'
    _order = 'code, id'

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    _company_code_unique = models.Constraint(
        'UNIQUE(company_id, code)', 'The work item code must be unique within its company.',
    )
    _code_present = models.Constraint('CHECK(length(btrim(code)) > 0)', 'A work item code is required.')
