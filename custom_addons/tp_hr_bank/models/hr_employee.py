from odoo import api, models


class HrEmployeeBankSelfService(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def _tp_self_service_fields(self):
        # res.users.tp_save_my_bank_account / tp_remove_my_bank_account link or unlink only the
        # caller's own, ownership-checked accounts. The field domain and res.partner.bank's
        # _allow_sudo_commands=False still refuse a link to an account the user cannot read.
        return super()._tp_self_service_fields() | {'bank_account_ids'}
