from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    tp_project_id = fields.Many2one(
        'project.project', string='Dự án thực hiện', check_company=True,
        ondelete='restrict', copy=False, index=True,
        domain="[('tp_managed', '=', True), ('company_id', '=', company_id)]",
    )

    def _check_tp_link_target_access(self, vals):
        if vals.get('tp_project_id'):
            self.env['project.project'].browse(vals['tp_project_id']).check_access('read')

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(['tp_project_id'])
        for vals in vals_list:
            self._check_tp_link_target_access({**defaults, **vals})
        return super().create(vals_list)

    def write(self, vals):
        self._check_tp_link_target_access(vals)
        return super().write(vals)

    @api.constrains('tp_project_id', 'partner_id', 'company_id')
    def _check_tp_project_link(self):
        for lead in self.filtered('tp_project_id'):
            project = lead.tp_project_id
            if (not project.tp_managed or lead.company_id != project.company_id
                    or not lead.partner_id or lead.partner_id.commercial_partner_id != project.partner_id.commercial_partner_id):
                raise ValidationError(self.env._('Cơ hội và dự án phải cùng công ty, khách hàng và phạm vi TP Projects.'))


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.constrains('partner_id', 'company_id', 'tp_managed')
    def _check_tp_crm_consistency(self):
        # Integrity check only: do not disclose inaccessible CRM names/counts in errors.
        linked = self.env['crm.lead'].sudo().search([('tp_project_id', 'in', self.ids)])
        for lead in linked:
            project = lead.tp_project_id
            if (not project.tp_managed or lead.company_id != project.company_id
                    or not lead.partner_id or lead.partner_id.commercial_partner_id != project.partner_id.commercial_partner_id):
                raise ValidationError(self.env._('Thay đổi này không còn khớp với cơ hội đã liên kết.'))
