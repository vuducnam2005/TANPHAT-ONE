from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# Context key set only by tp.contract.workflow when it writes guarded fields.
WORKFLOW_CONTEXT = 'tp_contract_workflow'
# Contract fields captured by review snapshots.
HEADER_FIELDS = frozenset({'code', 'name', 'partner_id', 'contract_type', 'currency_id'})

CONTRACT_TYPES = [
    ('owner', 'With Project Owner'),
    ('general_contractor', 'With General Contractor'),
    ('subcontractor', 'With Subcontractor'),
]
LIFECYCLE_STATES = [
    ('not_effective', 'Not Effective'),
    ('effective', 'Effective'),
    ('suspended', 'Suspended'),
    ('execution_completed', 'Execution Completed'),
    ('liquidated', 'Liquidated'),
    ('terminated', 'Terminated'),
]


class TpContract(models.Model):
    """External legal contract metadata. Amounts live in protected financial models."""

    _name = 'tp.contract'
    _description = 'Tan Phat Contract'
    _check_company_auto = True
    _order = 'code, id'

    code = fields.Char(required=True, index=True, copy=False)
    name = fields.Char(required=True)
    project_id = fields.Many2one('project.project', required=True, ondelete='restrict', index=True, check_company=True)
    company_id = fields.Many2one(related='project_id.company_id', store=True, index=True, precompute=True)
    partner_id = fields.Many2one('res.partner', string='Counterparty', ondelete='restrict', check_company=True)
    contract_type = fields.Selection(CONTRACT_TYPES, required=True)
    currency_id = fields.Many2one('res.currency', required=True, default=lambda self: self.env.company.currency_id)
    lifecycle_state = fields.Selection(LIFECYCLE_STATES, required=True, default='not_effective')
    department_id = fields.Many2one(
        'hr.department', ondelete='restrict', index=True, check_company=True,
        help='Department scope of contract workflow grants, copied from the project lead department at creation.',
    )
    aggregate_version = fields.Integer(
        required=True, default=1, copy=False,
        help='Raised by every workflow mutation of the contract or its children; writers send it back as expected_version.',
    )
    legacy_unverified = fields.Boolean(help='Historical record kept without verified legal or approval evidence.')
    revision_ids = fields.One2many('tp.contract.revision', 'contract_id', string='Revisions')
    active = fields.Boolean(default=True)

    _code_company_unique = models.Constraint(
        'UNIQUE(company_id, code)', 'The contract code must be unique within its company.',
    )
    _code_present = models.Constraint(
        'CHECK(length(btrim(code)) > 0)', 'A contract requires a code.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code'):
                vals['code'] = vals['code'].strip().upper()
            if not vals.get('department_id') and vals.get('project_id'):
                vals['department_id'] = self.env['project.project'].browse(vals['project_id']).sudo().tp_department_id.id
        return super().create(vals_list)

    def write(self, vals):
        self._tp_check_protected_write(vals)
        if vals.get('code'):
            vals = dict(vals, code=vals['code'].strip().upper())
        return super().write(vals)

    def _tp_check_protected_write(self, vals):
        # Scope fields never move a contract out of its grants; the version only
        # changes inside workflow actions; the header is part of every review
        # snapshot. Access is checked first so callers without write rights
        # still get the access error.
        if not {'project_id', 'department_id', 'aggregate_version', *HEADER_FIELDS} & set(vals):
            return
        self.check_access('write')
        if HEADER_FIELDS & set(vals) and any(revision._tp_is_frozen() for revision in self.sudo().revision_ids):
            raise UserError(self.env._('The contract header cannot change while a revision is under review.'))
        for contract in self:
            if 'project_id' in vals and vals['project_id'] != contract.project_id.id:
                raise UserError(self.env._('A contract cannot move to another project.'))
            if 'department_id' in vals and contract.department_id and vals['department_id'] != contract.department_id.id:
                raise UserError(self.env._('The department scope of a contract cannot be changed.'))
        if 'aggregate_version' in vals and not self.env.context.get(WORKFLOW_CONTEXT):
            raise UserError(self.env._('The contract version changes only through workflow actions.'))

    @api.constrains('project_id')
    def _check_managed_project(self):
        for contract in self:
            if not contract.project_id.tp_managed:
                raise ValidationError(self.env._('Contracts require a Tan Phat managed project.'))

    @api.constrains('lifecycle_state', 'revision_ids')
    def _check_lifecycle_evidence(self):
        for contract in self:
            if contract.lifecycle_state != 'not_effective' and not contract.revision_ids.filtered(
                lambda revision: revision.effectivity_status == 'effective_recorded',
            ):
                raise ValidationError(self.env._('A contract lifecycle beyond "not effective" requires a revision with recorded effectivity.'))

    def _effective_revision(self, as_of):
        """Return ``(revision, warnings)`` for the snapshot in force on ``as_of``.

        Only revisions with recorded effectivity count; BASE approval never makes
        a revision effective. Two candidates on the same date are reported as a
        conflict instead of picking the highest ID.
        """
        self.ensure_one()
        Revision = self.env['tp.contract.revision']
        recorded = self.revision_ids.filtered(
            lambda revision: revision.effectivity_status == 'effective_recorded' and revision.review_state != 'cancelled',
        )
        current = recorded.filtered(lambda revision: revision.effective_date <= as_of)
        warnings = []
        if recorded - current:
            warnings.append('future_revision_recorded')
        if not current:
            warnings.append('no_effective_revision')
            return Revision, warnings
        latest_date = max(current.mapped('effective_date'))
        candidates = current.filtered(lambda revision: revision.effective_date == latest_date)
        if len(candidates) > 1:
            warnings.append('effective_date_conflict')
            return Revision, warnings
        return candidates, warnings
