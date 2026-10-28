from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain

CAPABILITIES = [
    ('financial_read', 'financial.read'),
    ('financial_draft_edit', 'financial.draft_edit'),
    ('contract_draft_edit', 'contract.draft_edit'),
    ('contract_submit', 'contract.submit'),
    ('contract_review_commercial', 'contract.review_commercial'),
]
# Contract workflow capabilities (CTR-002a) are scoped to project + department;
# financial.read keeps the project-wide scope defined by CTR-001.
DEPARTMENT_SCOPED = frozenset({
    'financial_draft_edit', 'contract_draft_edit', 'contract_submit', 'contract_review_commercial',
})


class TpProjectGrant(models.Model):
    """Per-project capability grant, evaluated by access domains at query time.

    No user group may create or change grants yet: who issues them is still an
    open business question (BIZ-001 Q2), so grants are managed by superuser
    operations only. Workflow capabilities exist for synthetic test actors
    (DEC-020) and are never inferred from a job title.
    """

    _name = 'tp.project.grant'
    _description = 'Tan Phat Project Capability Grant'
    _check_company_auto = True
    _order = 'project_id, user_id, capability'

    project_id = fields.Many2one('project.project', required=True, ondelete='restrict', index=True, check_company=True)
    company_id = fields.Many2one(related='project_id.company_id', store=True, index=True)
    user_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True)
    capability = fields.Selection(CAPABILITIES, required=True)
    department_id = fields.Many2one(
        'hr.department', ondelete='restrict', index=True, check_company=True,
        help='Department scope; required by contract workflow capabilities and empty for financial.read.',
    )
    reason = fields.Text(required=True)
    granted_by_id = fields.Many2one('res.users', required=True, ondelete='restrict', default=lambda self: self.env.user)
    date_end = fields.Date(string='Valid Until')
    active = fields.Boolean(default=True)

    _active_grant_unique = models.UniqueIndex(
        '(project_id, user_id, capability) WHERE (active IS TRUE)',
        'An active grant for this capability already exists on the project.',
    )
    _reason_present = models.Constraint(
        'CHECK(length(btrim(reason)) > 0)', 'A grant requires a reason.',
    )

    @api.constrains('project_id', 'user_id', 'granted_by_id', 'capability', 'department_id')
    def _check_grant_scope(self):
        for grant in self:
            if (grant.capability in DEPARTMENT_SCOPED) != bool(grant.department_id):
                raise ValidationError(self.env._('Contract workflow grants require a department; financial.read grants must not have one.'))
            if not grant.project_id.tp_managed:
                raise ValidationError(self.env._('Grants require a Tan Phat managed project.'))
            if not grant.user_id.has_group('tp_core.group_user'):
                raise ValidationError(self.env._('The grantee must be a Tan Phat platform user.'))
            if grant.company_id not in grant.user_id.company_ids:
                raise ValidationError(self.env._('The grantee must have access to the project company.'))
            if grant.user_id == grant.granted_by_id and not self.env.su:
                raise ValidationError(self.env._('A user cannot grant a capability to themselves.'))

    @api.model_create_multi
    def create(self, vals_list):
        grants = super().create(vals_list)
        self._invalidate_grant_access()
        return grants

    def write(self, vals):
        result = super().write(vals)
        self._invalidate_grant_access()
        return result

    def unlink(self):
        result = super().unlink()
        self._invalidate_grant_access()
        return result

    def _invalidate_grant_access(self):
        # Access domains read grants at query time; drop cached decisions so a
        # revocation applies to the very next read, even in this transaction.
        self.env.flush_all()
        self.env['project.project'].invalidate_model(['tp_financial_read_granted'])
        self.env.transaction.invalidate_access_cache()

    @api.model
    def _tp_has_capability(self, project, capability, department=None, user=None):
        """Whether ``user`` (default: current user) holds an active ``capability`` grant.

        Department-scoped capabilities match only a grant of the same department,
        so the same capability name in another department never applies.
        """
        domain = self._active_grant_domain(capability, (user or self.env.user).id) & Domain('project_id', '=', project.id)
        if capability in DEPARTMENT_SCOPED:
            if not department:
                return False
            domain &= Domain('department_id', '=', department.id)
        return bool(self.sudo().search_count(domain, limit=1))

    @api.model
    def _active_grant_domain(self, capability, user_id):
        today = fields.Date.context_today(self)
        return Domain([
            ('user_id', '=', user_id),
            ('capability', '=', capability),
            ('active', '=', True),
        ]) & (Domain('date_end', '=', False) | Domain('date_end', '>=', today))
