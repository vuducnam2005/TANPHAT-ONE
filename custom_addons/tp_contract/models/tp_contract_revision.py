from decimal import Decimal

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_repr

from .tp_contract import WORKFLOW_CONTEXT

REVIEW_STATES = [
    ('draft', 'Draft'),
    ('in_review', 'In Review'),
    ('returned', 'Returned'),
    ('review_complete', 'Review Complete'),
    ('cancelled', 'Cancelled'),
]


class TpContractRevision(models.Model):
    """Full snapshot of a contract scope after the original or an amendment.

    Review, signature and effectivity are separate layers; BASE results are
    recorded on ``tp.approval.reference`` and never imply signature or effect.
    """

    _name = 'tp.contract.revision'
    _description = 'Tan Phat Contract Revision'
    _order = 'contract_id, sequence'

    contract_id = fields.Many2one('tp.contract', required=True, ondelete='restrict', index=True)
    project_id = fields.Many2one(related='contract_id.project_id', store=True, index=True, precompute=True)
    company_id = fields.Many2one(related='contract_id.company_id', store=True, index=True, precompute=True)
    sequence = fields.Integer(required=True, help='0 is the original contract; amendments and corrections follow.')
    revision_kind = fields.Selection([
        ('original', 'Original'),
        ('amendment', 'Amendment'),
        ('correction', 'Correction'),
    ], required=True)
    name = fields.Char(required=True)
    reference = fields.Char(string='Document Number')
    previous_revision_id = fields.Many2one('tp.contract.revision', ondelete='restrict', index=True)
    signed_date = fields.Date()
    effective_date = fields.Date()
    recorded_at = fields.Datetime(required=True, default=fields.Datetime.now)
    review_state = fields.Selection(REVIEW_STATES, required=True, default='draft')
    signature_status = fields.Selection([
        ('unsigned', 'Not Signed'),
        ('signed_recorded', 'Signature Recorded'),
    ], required=True, default='unsigned')
    signature_authority_status = fields.Selection([
        ('pending', 'Authority Pending'),
        ('confirmed', 'Authority Confirmed'),
    ], required=True, default='pending')
    effectivity_status = fields.Selection([
        ('not_effective', 'Not Effective'),
        ('effective_recorded', 'Effectivity Recorded'),
    ], required=True, default='not_effective')
    legacy_unverified = fields.Boolean()
    line_ids = fields.One2many('tp.contract.line', 'revision_id', string='Scope Lines')
    approval_reference_ids = fields.One2many('tp.approval.reference', 'revision_id', string='BASE References')
    submission_ids = fields.One2many('tp.contract.submission', 'revision_id', string='Review Submissions')

    _sequence_unique = models.Constraint(
        'UNIQUE(contract_id, sequence)', 'Each revision sequence must be unique within its contract.',
    )
    _sequence_kind = models.Constraint(
        "CHECK(sequence >= 0 AND ((sequence = 0) = (revision_kind = 'original')))",
        'Sequence 0 is reserved for, and required by, the original contract.',
    )
    _previous_required = models.Constraint(
        "CHECK((revision_kind = 'original') = (previous_revision_id IS NULL))",
        'Amendments and corrections must reference the previous revision; the original must not.',
    )
    _signature_evidence = models.Constraint(
        "CHECK(signature_status = 'unsigned' OR signed_date IS NOT NULL)",
        'A recorded signature requires a signed date.',
    )
    _effectivity_evidence = models.Constraint(
        "CHECK(effectivity_status = 'not_effective' OR (signature_status = 'signed_recorded' "
        "AND effective_date IS NOT NULL AND review_state != 'cancelled'))",
        'Recorded effectivity requires a recorded signature, an effective date and a non-cancelled revision.',
    )

    @api.constrains('previous_revision_id', 'contract_id', 'sequence')
    def _check_previous_revision(self):
        for revision in self:
            previous = revision.previous_revision_id
            if previous and (previous.contract_id != revision.contract_id or previous.sequence >= revision.sequence):
                raise ValidationError(self.env._('The previous revision must belong to the same contract and come earlier.'))

    @api.ondelete(at_uninstall=False)
    def _unlink_only_drafts(self):
        if any(
            revision.review_state != 'draft' or revision.signature_status != 'unsigned' or revision.submission_ids
            for revision in self
        ):
            raise UserError(self.env._('Submitted or signed revisions keep their history and cannot be deleted.'))

    def write(self, vals):
        self._tp_check_protected_write(vals)
        return super().write(vals)

    def _tp_check_protected_write(self, vals):
        frozen = any(revision._tp_is_frozen() for revision in self)
        if not frozen and not {'review_state', 'contract_id'} & set(vals):
            return
        self.check_access('write')
        if 'contract_id' in vals and any(revision.contract_id.id != vals['contract_id'] for revision in self):
            raise UserError(self.env._('A revision cannot move to another contract.'))
        if 'review_state' in vals and not self.env.context.get(WORKFLOW_CONTEXT):
            raise UserError(self.env._('Review states change only through workflow actions.'))
        if frozen and set(vals) - {'review_state'}:
            raise UserError(self.env._('Submitted revision content cannot be changed.'))

    def _tp_is_frozen(self):
        """Whether the content is locked by a review submission.

        Content stays locked while in review or returned; it opens again only
        when rework moves the revision back to draft. Submission snapshots keep
        their own copy, so later edits never change what was reviewed.
        """
        self.ensure_one()
        return self.review_state in ('in_review', 'returned') or (
            self.review_state != 'draft' and bool(self.sudo().submission_ids)
        )

    def _tp_check_content_editable(self):
        if any(revision._tp_is_frozen() for revision in self):
            raise UserError(self.env._('Submitted revision content cannot be changed.'))

    def _amount_summary(self):
        """Return the snapshot total from line amounts readable by the current user.

        The total exists only when every line has a confirmed amount on one tax
        basis; unconfirmed or missing amounts make it ``None``, never zero.
        Callers check the financial.read grant before exposing the result.
        """
        self.ensure_one()
        currency = self.contract_id.currency_id
        amounts = {
            amount.line_id.id: amount
            for amount in self.env['tp.contract.line.amount'].search([('revision_id', '=', self.id)])
        }
        total = Decimal(0)
        bases = set()
        status = 'confirmed' if self.line_ids else 'empty'
        for line in self.line_ids:
            amount = amounts.get(line.id)
            if not amount or amount.amount_state != 'confirmed':
                status = 'incomplete'
                continue
            bases.add(amount.tax_basis)
            total += Decimal(float_repr(currency.round(amount.amount), currency.decimal_places))
        if status == 'confirmed' and len(bases) > 1:
            status = 'mixed_basis'
        return {
            'value': total if status == 'confirmed' else None,
            'status': status,
            'tax_basis': bases.pop() if len(bases) == 1 else ('mixed' if bases else 'unknown'),
            'currency': currency,
        }
