# Part of TANPHAT ONE. Global OdooBot Silencer and Neutralizer.

from odoo import api, models
from odoo.fields import Domain


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def _message_fetch(self, domain=None, *, thread=None, **kwargs):
        """Globally exclude messages authored by OdooBot from chatter and thread queries."""
        odoobot_id = self.env['ir.model.data']._xmlid_to_res_id('base.partner_root')
        if odoobot_id:
            domain = Domain(True if domain is None else domain) & Domain('author_id', '!=', odoobot_id)
        return super()._message_fetch(domain, thread=thread, **kwargs)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault('odoobot_state', 'disabled')
        return super().create(vals_list)

    def _on_webclient_bootstrap(self):
        users_to_disable = self.filtered(lambda u: u.odoobot_state != 'disabled')
        if users_to_disable:
            users_to_disable.sudo().write({'odoobot_state': 'disabled'})
        return super()._on_webclient_bootstrap()

    def _init_odoobot(self):
        """Do not initialize any OdooBot chat or tour for any user."""
        return False


class MailBot(models.AbstractModel):
    _inherit = 'mail.bot'

    def _apply_logic(self, channel, message, command=None):
        """Completely neutralize mail bot logic."""
        return


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    @api.model
    def _get_or_create_chat(self, partners_to, pin=False):
        """Block creation of 1-on-1 direct chats with OdooBot."""
        odoobot_id = self.env['ir.model.data']._xmlid_to_res_id('base.partner_root')
        partner_ids = [p.id if hasattr(p, 'id') else p for p in partners_to]
        if odoobot_id and odoobot_id in partner_ids:
            return self.browse()
        return super()._get_or_create_chat(partners_to, pin=pin)
