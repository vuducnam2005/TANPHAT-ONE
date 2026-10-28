from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.fields import Domain


class ProjectProject(models.Model):
    _inherit = 'project.project'

    tp_managed = fields.Boolean(string='Tan Phat Managed', default=False, index=True, copy=False)
    tp_code = fields.Char(string='Project Code', index=True, copy=False)
    tp_department_id = fields.Many2one('hr.department', string='Lead Department', check_company=True)
    tp_assignment_ids = fields.One2many('tp.project.assignment', 'project_id', string='Project Assignments')
    tp_financial_read_granted = fields.Boolean(
        string='Financial Read Granted', compute='_compute_tp_financial_read_granted',
        search='_search_tp_financial_read_granted',
        help='Whether the current user holds an active financial.read grant on this project.',
    )

    _tp_code_company_unique = models.Constraint(
        'UNIQUE(company_id, tp_code)', 'The project code must be unique within its company.',
    )
    _tp_managed_identity = models.Constraint(
        "CHECK(NOT tp_managed OR (company_id IS NOT NULL AND tp_code IS NOT NULL AND length(btrim(tp_code)) > 0))",
        'A Tan Phat project requires a company and a project code.',
    )

    @api.depends_context('uid')
    def _compute_tp_financial_read_granted(self):
        granted = self._tp_granted_project_ids('financial_read')
        for project in self:
            project.tp_financial_read_granted = project.id in granted

    def _search_tp_financial_read_granted(self, operator, value):
        if operator != 'in':
            return NotImplemented
        grants = self.env['tp.project.grant'].sudo()._search(
            self.env['tp.project.grant']._active_grant_domain('financial_read', self.env.uid),
        )
        return Domain('id', 'in', grants.subselect(grants.table.project_id))

    def _tp_granted_project_ids(self, capability):
        grants = self.env['tp.project.grant'].sudo().search_fetch(
            self.env['tp.project.grant']._active_grant_domain(capability, self.env.uid), ['project_id'],
        )
        return set(grants.project_id.ids)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and not self.env.user.has_group('tp_core.group_manager'):
            if any(vals.get('tp_managed') or any(vals.get(key) for key in ('tp_code', 'tp_department_id', 'tp_assignment_ids')) for vals in vals_list):
                raise AccessError(self.env._('Only platform managers can configure Tan Phat projects.'))
        for vals in vals_list:
            if vals.get('tp_code'):
                vals['tp_code'] = vals['tp_code'].strip().upper()
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su and not self.env.user.has_group('tp_core.group_manager'):
            if vals.get('tp_managed') or any(self.mapped('tp_managed')) or set(vals) & {'tp_code', 'tp_department_id', 'tp_assignment_ids'}:
                raise AccessError(self.env._('Only platform managers can configure Tan Phat projects.'))
        if vals.get('tp_code'):
            vals = dict(vals, tp_code=vals['tp_code'].strip().upper())
        return super().write(vals)
