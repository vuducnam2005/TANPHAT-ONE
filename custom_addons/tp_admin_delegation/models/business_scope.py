"""Full System Administrators use native platform/KH-KD rights across all departments (DEC-053).

Also ensures that a Granted Full Admin who retains their employee `tp_kd_workspace.group_scoped_staff`
group is never restricted by `_kd_scoped()` on CRM records/money/attachments while holding `base.group_system`.
"""
from odoo import api, models
from odoo.fields import Domain


def other_domain(env, company_field, department_fields):
    return Domain.FALSE


def other_project(project, department=None, user=None, lock=False):
    return False


class Project(models.Model):
    _inherit = 'project.project'

    @api.model
    def _tp_delegated_domain(self):
        return Domain.FALSE


class Opportunity(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def _kd_scoped(self):
        if self.env.user.has_group('base.group_system'):
            return False
        return super()._kd_scoped()
