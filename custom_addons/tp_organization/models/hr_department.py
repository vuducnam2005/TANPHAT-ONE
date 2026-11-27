from odoo import fields, models


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    tp_code = fields.Char(string='Mã phòng ban Tân Phát', copy=False, index=True)

    _tp_company_code_unique = models.Constraint(
        'UNIQUE(company_id, tp_code)', 'Mã phòng ban phải là duy nhất trong cùng một công ty.',
    )
