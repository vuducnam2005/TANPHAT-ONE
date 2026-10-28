from odoo import fields, models


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    tp_code = fields.Char(string='Tan Phat Code', copy=False, index=True)

    _tp_company_code_unique = models.Constraint(
        'UNIQUE(company_id, tp_code)', 'The department code must be unique within its company.',
    )
