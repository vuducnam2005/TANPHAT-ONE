from odoo import api, fields, models
from odoo.exceptions import ValidationError

TAX_BASES = [
    ('unknown', 'Unknown'),
    ('excluding_tax', 'Excluding Tax'),
    ('including_tax', 'Including Tax'),
]


class TpContractLine(models.Model):
    """Scope line of one revision snapshot. It carries no money fields."""

    _name = 'tp.contract.line'
    _description = 'Tan Phat Contract Scope Line'
    _check_company_auto = True
    _order = 'revision_id, sequence, id'

    revision_id = fields.Many2one('tp.contract.revision', required=True, ondelete='cascade', index=True)
    contract_id = fields.Many2one(related='revision_id.contract_id', store=True, index=True, precompute=True)
    project_id = fields.Many2one(related='revision_id.project_id', store=True, index=True, precompute=True)
    company_id = fields.Many2one(related='revision_id.company_id', store=True, index=True, precompute=True)
    sequence = fields.Integer(default=10)
    scope_key = fields.Char(required=True, help='Stable key of the scope item across revisions of the contract.')
    name = fields.Char(required=True)
    work_item_id = fields.Many2one('tp.work.item', ondelete='restrict', check_company=True)
    change_kind = fields.Selection([
        ('original', 'Original'),
        ('unchanged', 'Carried Over'),
        ('amended', 'Amended'),
        ('added', 'Added'),
    ], required=True, default='original')
    previous_line_id = fields.Many2one('tp.contract.line', ondelete='restrict', index=True)

    _scope_key_unique = models.Constraint(
        'UNIQUE(revision_id, scope_key)', 'A scope key appears once per revision.',
    )

    @api.constrains('previous_line_id', 'revision_id', 'change_kind', 'scope_key')
    def _check_line_provenance(self):
        for line in self:
            previous = line.previous_line_id
            needs_previous = line.change_kind in ('unchanged', 'amended')
            if needs_previous != bool(previous):
                raise ValidationError(self.env._('Carried over and amended lines must reference the previous revision line; others must not.'))
            if line.change_kind == 'original' and line.revision_id.revision_kind != 'original':
                raise ValidationError(self.env._('Only the original revision holds original lines.'))
            if previous and (
                previous.revision_id != line.revision_id.previous_revision_id or previous.scope_key != line.scope_key
            ):
                raise ValidationError(self.env._('A line must reference the same scope key in the previous revision.'))


class TpContractLineAmount(models.Model):
    """Protected amount of a scope line, readable only with a project financial.read grant."""

    _name = 'tp.contract.line.amount'
    _description = 'Tan Phat Contract Line Amount'
    _order = 'line_id'

    line_id = fields.Many2one('tp.contract.line', required=True, ondelete='cascade', index=True)
    revision_id = fields.Many2one(related='line_id.revision_id', store=True, index=True, precompute=True)
    project_id = fields.Many2one(related='line_id.project_id', store=True, index=True, precompute=True)
    company_id = fields.Many2one(related='line_id.company_id', store=True, index=True, precompute=True)
    currency_id = fields.Many2one(related='line_id.contract_id.currency_id', store=True, precompute=True)
    amount_state = fields.Selection([
        ('unconfirmed', 'Not Confirmed'),
        ('confirmed', 'Confirmed'),
    ], required=True, default='unconfirmed')
    amount = fields.Monetary(help='Line total of the revision snapshot. Meaningful only when confirmed.')
    tax_basis = fields.Selection(TAX_BASES, required=True, default='unknown')

    _line_unique = models.Constraint('UNIQUE(line_id)', 'A scope line has one amount record.')
    _unconfirmed_is_empty = models.Constraint(
        "CHECK(amount_state = 'confirmed' OR COALESCE(amount, 0) = 0)",
        'An unconfirmed amount must not carry a value.',
    )
    _non_negative = models.Constraint(
        'CHECK(COALESCE(amount, 0) >= 0)', 'Snapshot line amounts cannot be negative.',
    )
