from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TpProjectAssignment(models.Model):
    _name = 'tp.project.assignment'
    _description = 'Tan Phat Project Assignment'
    _check_company_auto = True

    project_id = fields.Many2one('project.project', required=True, ondelete='cascade', index=True, check_company=True)
    company_id = fields.Many2one(related='project_id.company_id', store=True, index=True)
    user_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True)
    role = fields.Selection([('reader', 'Reader'), ('coordinator', 'Coordinator')], required=True, default='reader')
    active = fields.Boolean(default=True)

    _assignment_unique = models.Constraint(
        'UNIQUE(project_id, user_id, role)', 'This project assignment already exists.',
    )

    @api.constrains('project_id', 'user_id')
    def _check_assignment_scope(self):
        for assignment in self:
            if not assignment.project_id.tp_managed:
                raise ValidationError(self.env._('Assignments require a Tan Phat managed project.'))
            if not assignment.user_id.has_group('tp_core.group_user'):
                raise ValidationError(self.env._('The assignee must be a Tan Phat platform user.'))
            if assignment.company_id not in assignment.user_id.company_ids:
                raise ValidationError(self.env._('The assignee must have access to the project company.'))
