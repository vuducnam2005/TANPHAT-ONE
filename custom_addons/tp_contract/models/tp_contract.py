from odoo import api, fields, models
from odoo.exceptions import ValidationError

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
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('code'):
            vals = dict(vals, code=vals['code'].strip().upper())
        return super().write(vals)

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
