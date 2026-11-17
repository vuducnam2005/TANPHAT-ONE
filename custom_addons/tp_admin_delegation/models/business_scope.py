"""Explicit native business scopes; baseline rights remain live and unchanged."""
from odoo import api, models
from odoo.exceptions import AccessError
from odoo.fields import Domain

from .guards import deny_authority, lock_scope_users
from odoo.addons.tp_contract.models.tp_contract_workflow import CAPABILITY_KEYS


def other_domain(env, company_field, department_fields):
    parts = []
    user = env.user
    for company in env.companies:
        if not user._tp_has_admin_delegation(company):
            continue
        protected, complete = user._tp_delegation_scope(company)
        # Unknown work identity cannot define which department to protect.
        if not complete:
            continue
        part = Domain(company_field, '=', company.id)
        for field in department_fields:
            part &= (Domain(field, '!=', False) & Domain(field, 'not in', protected.ids)
                     & Domain(field + '.company_id', '=', company.id))
        parts.append(part)
    return Domain.OR(parts)


def other_project(project, department=None, user=None, lock=False):
    project.ensure_one()
    source = project.sudo()
    target = user or project.env.user
    if not target._tp_has_admin_delegation(source.company_id):
        return False
    lock = lock and not project.env.cr.readonly
    if lock:
        project.env.cr.execute('SELECT id FROM project_project WHERE id=%s FOR SHARE', [project.id])
        project.env.cr.execute('SELECT id FROM tp_contract WHERE project_id=%s ORDER BY id FOR SHARE', [project.id])
        project.env.cr.execute('SELECT id FROM crm_lead WHERE tp_project_id=%s ORDER BY id FOR SHARE', [project.id])
        project.env.cr.execute('''SELECT id FROM crm_team WHERE id IN
            (SELECT team_id FROM crm_lead WHERE tp_project_id=%s) ORDER BY id FOR SHARE''', [project.id])
    departments = source.tp_department_id
    if department:
        departments |= department.sudo()
    if not (source.tp_managed and departments and target._tp_delegated_other_department(
            source.company_id, departments, lock=lock)):
        return False
    projects = project.env['project.project'].with_user(target)
    return bool(projects.sudo().search_count(Domain('id', '=', project.id) & projects._tp_delegated_domain(), limit=1))


class Project(models.Model):
    _inherit = 'project.project'

    @api.model
    def _tp_delegated_domain(self):
        domain = Domain('tp_managed', '=', True) & other_domain(self.env, 'company_id', ['tp_department_id'])
        if domain.is_false():
            return domain
        # A parent opened by delegation must never widen an own/unknown-source child
        # through a native ('project_id', 'access', 'read') rule.
        for company in self.env.companies:
            own, complete = self.env.user._tp_delegation_scope(company)
            if not complete:
                continue
            contracts = self.env['tp.contract'].sudo().with_context(active_test=False)._search([
                ('company_id', '=', company.id), '|', ('department_id', '=', False),
                ('department_id', 'in', own.ids),
            ])
            leads = self.env['crm.lead'].sudo().with_context(active_test=False)._search([
                ('company_id', '=', company.id), ('tp_project_id', '!=', False),
                '|', ('team_id.kd_department_id', '=', False), ('team_id.kd_department_id', 'in', own.ids),
            ])
            domain &= ~Domain('id', 'in', contracts.subselect(contracts.table.project_id))
            domain &= ~Domain('id', 'in', leads.subselect(leads.table.tp_project_id))
        return domain

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        return baseline | self._tp_delegated_domain() if operation == 'read' else baseline

    def write(self, vals):
        if set(vals) & {'company_id', 'tp_department_id', 'tp_managed'}:
            deny_authority(self.env)
            actors = self.env['res.users']
            for model in ('tp.project.assignment', 'tp.project.grant', 'tp.kd.grant'):
                actors |= self.env[model].sudo().with_context(active_test=False).search([
                    ('project_id', 'in', self.ids),
                ]).user_id
            lock_scope_users(self.env, actors)
        return super().write(vals)

    def _tp_granted_project_ids(self, capability):
        return super()._tp_granted_project_ids(capability) | set(self.sudo().search(self._tp_delegated_domain()).ids)


class Task(models.Model):
    _inherit = 'project.task'

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        if operation == 'read':
            return baseline | Domain('project_id', 'any', self.env['project.project']._tp_delegated_domain())
        return baseline


class ProjectCapability(models.Model):
    _inherit = 'tp.project.grant'

    def _tp_has_capability(self, project, capability, department=None, user=None):
        return super()._tp_has_capability(project, capability, department, user) or (
            capability in CAPABILITY_KEYS and other_project(project, department, user, lock=True))


class KdCapability(models.Model):
    _inherit = 'tp.kd.grant'

    def _has(self, project, domain, capability, user=None):
        return super()._has(project, domain, capability, user) or bool(
            domain in self._fields['domain'].get_values(self.env)
            and capability in self._fields['capability'].get_values(self.env)
            and other_project(project, user=user, lock=True))


class ContractWorkflow(models.AbstractModel):
    _inherit = 'tp.contract.workflow'

    def _tp_can_use_workflow(self):
        return super()._tp_can_use_workflow() or self.env.user._tp_has_admin_delegation()

    def _tp_capabilities(self, project, department, user=None):
        baseline = super()._tp_capabilities(project, department, user)
        return set(CAPABILITY_KEYS) if other_project(project, department, user, lock=True) else baseline


class ProjectScope(models.AbstractModel):
    _name = 'tp.admin.project.scope.mixin'
    _description = 'Audited project sources for delegated administration'
    _tp_admin_department_paths = ('project_id.tp_department_id',)

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        if operation == 'read':
            return baseline | (other_domain(self.env, 'project_id.company_id', self._tp_admin_department_paths)
                               & Domain('project_id', 'any', self.env['project.project']._tp_delegated_domain()))
        return baseline


class Contract(models.Model):
    _name = 'tp.contract'
    _inherit = ['tp.contract', 'tp.admin.project.scope.mixin']
    _tp_admin_department_paths = ('project_id.tp_department_id', 'department_id')


class ContractRevision(models.Model):
    _name = 'tp.contract.revision'
    _inherit = ['tp.contract.revision', 'tp.admin.project.scope.mixin']
    _tp_admin_department_paths = ('project_id.tp_department_id', 'contract_id.department_id')


class ContractLine(models.Model):
    _name = 'tp.contract.line'
    _inherit = ['tp.contract.line', 'tp.admin.project.scope.mixin']
    _tp_admin_department_paths = ('project_id.tp_department_id', 'revision_id.contract_id.department_id')


class ContractAmount(models.Model):
    _name = 'tp.contract.line.amount'
    _inherit = ['tp.contract.line.amount', 'tp.admin.project.scope.mixin']
    _tp_admin_department_paths = ('project_id.tp_department_id', 'revision_id.contract_id.department_id')


class ContractDocument(models.Model):
    _name = 'tp.contract.document'
    _inherit = ['tp.contract.document', 'tp.admin.project.scope.mixin']
    _tp_admin_department_paths = ('project_id.tp_department_id', 'contract_id.department_id')


class ContractSubmission(models.Model):
    _name = 'tp.contract.submission'
    _inherit = ['tp.contract.submission', 'tp.admin.project.scope.mixin']
    _tp_admin_department_paths = ('project_id.tp_department_id', 'contract_id.department_id')


class ContractSubmissionAmount(models.Model):
    _name = 'tp.contract.submission.amount'
    _inherit = ['tp.contract.submission.amount', 'tp.admin.project.scope.mixin']
    _tp_admin_department_paths = ('project_id.tp_department_id', 'submission_id.contract_id.department_id')


class ContractAudit(models.Model):
    _name = 'tp.contract.audit'
    _inherit = ['tp.contract.audit', 'tp.admin.project.scope.mixin']
    _tp_admin_department_paths = ('project_id.tp_department_id', 'department_id')


class ContractNative(models.AbstractModel):
    _inherit = 'tp.contract.native.mixin'

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        delegated = other_domain(self.env, 'company_id', ['project_id.tp_department_id'])
        return baseline | (delegated & Domain('create_uid', '=', self.env.uid))


class ContractNativeLine(models.TransientModel):
    _inherit = 'tp.contract.native.draft.line'

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        return baseline | (other_domain(self.env, 'wizard_id.company_id', ['wizard_id.project_id.tp_department_id'])
                           & Domain('wizard_id.create_uid', '=', self.env.uid))


class ContractNativeAmount(models.TransientModel):
    _inherit = 'tp.contract.native.amount.input'

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        return baseline | (other_domain(self.env, 'wizard_id.company_id', ['wizard_id.project_id.tp_department_id'])
                           & Domain('wizard_id.create_uid', '=', self.env.uid))


class ContractNativeIssue(models.TransientModel):
    _inherit = 'tp.contract.native.return.issue'

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        return baseline | (other_domain(self.env, 'wizard_id.company_id', ['wizard_id.project_id.tp_department_id'])
                           & Domain('wizard_id.create_uid', '=', self.env.uid))


class ProjectCommand(models.TransientModel):
    _inherit = 'tp.project.command'

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        return baseline | (other_domain(self.env, 'project_id.company_id', ['project_id.tp_department_id'])
                           & Domain('create_uid', '=', self.env.uid))


class TaskCommand(models.TransientModel):
    _inherit = 'tp.task.command'

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        return baseline | (other_domain(self.env, 'project_id.company_id', ['project_id.tp_department_id'])
                           & Domain('create_uid', '=', self.env.uid))


class Bid(models.Model):
    _name = 'tp.bid.package'
    _inherit = ['tp.bid.package', 'tp.admin.project.scope.mixin']


class BidAmount(models.Model):
    _name = 'tp.bid.package.amount'
    _inherit = ['tp.bid.package.amount', 'tp.admin.project.scope.mixin']


class Participation(models.Model):
    _name = 'tp.project.participation'
    _inherit = ['tp.project.participation', 'tp.admin.project.scope.mixin']


class Opportunity(models.Model):
    _inherit = 'crm.lead'

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        if operation == 'read':
            return baseline | (Domain('tp_project_id', '!=', False) & other_domain(
                self.env, 'company_id', ['tp_project_id.tp_department_id', 'team_id.kd_department_id']))
        return baseline


class ReportScope(models.AbstractModel):
    _inherit = 'tp.report.scope.mixin'

    def _tp_delegated_report_domain(self):
        domain = other_domain(self.env, 'company_id', ['department_id'])
        # Reports may embed snapshots/children or project results. Those shared
        # sources retain baseline until each dependency can be proven separately.
        if self._name == 'tp.report.document':
            domain &= (Domain('level', '=', 'personal') & Domain('dependency_ids', '=', False)
                       & Domain('owner_id', '!=', self.env.uid) & Domain('project_id', '=', False)
                       & Domain('snapshot_ids', '=', False)
                       & Domain('value_ids', '=', False)
                       & ~Domain('line_ids', 'any', Domain('project_id', '!=', False)
                                 | Domain('plan_id', '!=', False) | Domain('task_id', '!=', False)
                                 | Domain('origin_line_id', '!=', False) | Domain('rollup_source', '=', True)))
        elif self._name == 'tp.report.plan':
            domain &= (Domain('parent_id', '=', False) & Domain('child_ids', '=', False)
                       & Domain('project_id', '=', False) & Domain('task_id', '=', False))
        elif self._name == 'tp.report.line':
            domain &= Domain('document_id', 'any', self.env['tp.report.document']._tp_delegated_report_domain())
        else:
            return Domain.FALSE
        permitted = []
        for company in self.env.companies:
            own, complete = self.env.user._tp_delegation_scope(company)
            if not complete:
                continue
            known = self.env['hr.employee'].sudo()._search([
                ('company_id', '=', company.id), ('current_version_id.department_id', '!=', False),
                ('current_version_id.department_id', 'not in', own.ids),
            ])
            blocked = self.env['hr.employee'].sudo().with_context(active_test=False)._search([
                ('company_id', '=', company.id), '|', ('current_version_id.department_id', '=', False),
                ('current_version_id.department_id', 'in', own.ids),
            ])
            permitted.append(Domain('company_id', '=', company.id)
                             & Domain('owner_id', 'in', known.subselect(known.table.user_id))
                             & ~Domain('owner_id', 'in', blocked.subselect(blocked.table.user_id)))
        domain &= Domain.OR(permitted)
        return domain

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        if operation == 'read' and self._name in {
            'tp.report.document', 'tp.report.plan', 'tp.report.line',
        }:
            return baseline | self._tp_delegated_report_domain()
        return baseline

    def write(self, vals):
        if set(vals) & {'company_id', 'department_id', 'owner_id', 'document_id', 'plan_id', 'parent_id'}:
            for record in self:
                source = record.sudo()
                if self.env.user._tp_delegated_other_department(source.company_id, source.department_id, lock=True):
                    raise AccessError(self.env._('Chuyển nguồn hoặc phạm vi báo cáo cần quản trị chính.'))
        return super().write(vals)
