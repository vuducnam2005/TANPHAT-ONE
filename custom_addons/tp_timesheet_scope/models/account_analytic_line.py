from odoo import api, models
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _check_tp_target_values(self, values):
        if self.env.su:
            return
        task = self.env['project.task'].browse(values.get('task_id'))
        project = self.env['project.project'].browse(values.get('project_id'))
        if task:
            project |= task.sudo().project_id.sudo(False)
        for candidate in project:
            if candidate.sudo().tp_managed:
                candidate.check_access('read')
                if task:
                    task.check_access('read')

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(['project_id', 'task_id'])
        for values in vals_list:
            self._check_tp_target_values({**defaults, **values})
        records = super().create(vals_list)
        for line in records:
            self._check_tp_target_values({'project_id': line.project_id.id, 'task_id': line.task_id.id})
        return records

    def write(self, vals):
        self._check_tp_target_values(vals)
        result = super().write(vals)
        for line in self:
            self._check_tp_target_values({'project_id': line.project_id.id, 'task_id': line.task_id.id})
        return result

    @api.constrains('project_id', 'task_id')
    def _check_tp_timesheet_target_scope(self):
        # Odoo 20 runs constraints with sudo; access checks belong in create/write above.
        for line in self:
            project = line.project_id
            if project and project.sudo().tp_managed:
                if line.task_id:
                    if line.task_id.project_id != project:
                        raise ValidationError(self.env._('Giờ làm và công việc phải thuộc cùng dự án.'))
