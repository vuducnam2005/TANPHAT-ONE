from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .tp_contract_line import TAX_BASES


class TpApprovalReference(models.Model):
    """Declared BASE result for one contract revision.

    Recording a decision does not verify it, and a verified approval is still
    neither a signature nor legal effect.
    """

    _name = 'tp.approval.reference'
    _description = 'Tan Phat BASE Approval Reference'
    _order = 'revision_id, recorded_at, id'

    revision_id = fields.Many2one('tp.contract.revision', required=True, ondelete='restrict', index=True)
    contract_id = fields.Many2one(related='revision_id.contract_id', store=True, index=True, precompute=True)
    project_id = fields.Many2one(related='revision_id.project_id', store=True, index=True, precompute=True)
    company_id = fields.Many2one(related='revision_id.company_id', store=True, index=True, precompute=True)
    purpose = fields.Selection([('revision_approval', 'Revision Approval')], required=True, default='revision_approval')
    reference_kind = fields.Selection([
        ('base_id', 'BASE ID'),
        ('manual', 'Manual Reference'),
    ], required=True)
    base_reference = fields.Char(string='BASE Task/Approval ID')
    source_url = fields.Char()
    provenance = fields.Char(help='How a manual reference was obtained when no BASE ID exists.')
    decision = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], required=True, default='pending')
    decided_by_name = fields.Char(string='Decided By (BASE)')
    decided_at = fields.Datetime()
    decision_reason = fields.Text()
    evidence_sha256 = fields.Char(string='Evidence SHA-256')
    submitted_document_sha256 = fields.Char(string='Submitted Document SHA-256')
    recorded_by_id = fields.Many2one('res.users', required=True, ondelete='restrict', default=lambda self: self.env.user)
    recorded_at = fields.Datetime(required=True, default=fields.Datetime.now)
    verification_state = fields.Selection([
        ('pending', 'Verification Pending'),
        ('verified', 'Verified'),
        ('disputed', 'Disputed'),
    ], required=True, default='pending')
    verified_by_id = fields.Many2one('res.users', ondelete='restrict')
    verified_at = fields.Datetime()
    authority_status = fields.Selection([
        ('unconfirmed', 'Authority Unconfirmed'),
        ('confirmed', 'Authority Confirmed'),
    ], required=True, default='unconfirmed')
    authority_source = fields.Char()
    previous_reference_id = fields.Many2one('tp.approval.reference', ondelete='restrict', index=True)

    _base_id_present = models.Constraint(
        "CHECK(reference_kind != 'base_id' OR btrim(COALESCE(base_reference, '')) != '')",
        'A BASE ID reference requires the BASE identifier.',
    )
    _manual_provenance = models.Constraint(
        "CHECK(reference_kind != 'manual' OR btrim(COALESCE(provenance, '')) != '')",
        'A manual reference requires its provenance.',
    )
    _https_source = models.Constraint(
        "CHECK(source_url IS NULL OR source_url LIKE 'https://%')", 'The source URL must use HTTPS.',
    )
    _decision_recorded = models.Constraint(
        "CHECK(decision = 'pending' OR (decided_at IS NOT NULL AND btrim(COALESCE(decided_by_name, '')) != ''))",
        'A recorded decision requires who decided on BASE and when.',
    )
    _decision_reason = models.Constraint(
        "CHECK(decision NOT IN ('rejected', 'cancelled') OR btrim(COALESCE(decision_reason, '')) != '')",
        'Rejected or cancelled decisions require a reason.',
    )
    _verification_actor = models.Constraint(
        "CHECK(verification_state = 'pending' OR (verified_by_id IS NOT NULL AND verified_at IS NOT NULL))",
        'Verified or disputed evidence requires who checked it and when.',
    )
    _authority_source = models.Constraint(
        "CHECK(authority_status = 'unconfirmed' OR btrim(COALESCE(authority_source, '')) != '')",
        'Confirmed authority requires its source.',
    )
    _evidence_hash = models.Constraint(
        "CHECK(evidence_sha256 IS NULL OR evidence_sha256 ~ '^[0-9a-f]{64}$')",
        'The evidence hash must be a lowercase SHA-256 hex digest.',
    )
    _submitted_hash = models.Constraint(
        "CHECK(submitted_document_sha256 IS NULL OR submitted_document_sha256 ~ '^[0-9a-f]{64}$')",
        'The submitted document hash must be a lowercase SHA-256 hex digest.',
    )

    @api.constrains('previous_reference_id', 'revision_id')
    def _check_previous_reference(self):
        for reference in self:
            previous = reference.previous_reference_id
            if previous and (previous == reference or previous.contract_id != reference.contract_id):
                raise ValidationError(self.env._('A correction must reference an earlier BASE reference of the same contract.'))

    def _is_verified_result(self):
        """A declared result counts as verified only with checked evidence and confirmed authority."""
        self.ensure_one()
        return (
            self.decision != 'pending'
            and self.verification_state == 'verified'
            and self.authority_status == 'confirmed'
        )


class TpApprovalReferenceAmount(models.Model):
    """Protected approved amount declared on a BASE reference."""

    _name = 'tp.approval.reference.amount'
    _description = 'Tan Phat BASE Approved Amount'
    _order = 'reference_id'

    reference_id = fields.Many2one('tp.approval.reference', required=True, ondelete='cascade', index=True)
    project_id = fields.Many2one(related='reference_id.project_id', store=True, index=True, precompute=True)
    company_id = fields.Many2one(related='reference_id.company_id', store=True, index=True, precompute=True)
    currency_id = fields.Many2one(related='reference_id.contract_id.currency_id', store=True, precompute=True)
    amount_state = fields.Selection([
        ('unconfirmed', 'Not Confirmed'),
        ('confirmed', 'Confirmed'),
    ], required=True, default='unconfirmed')
    amount = fields.Monetary()
    tax_basis = fields.Selection(TAX_BASES, required=True, default='unknown')

    _reference_unique = models.Constraint('UNIQUE(reference_id)', 'A BASE reference has one approved amount record.')
    _unconfirmed_is_empty = models.Constraint(
        "CHECK(amount_state = 'confirmed' OR COALESCE(amount, 0) = 0)",
        'An unconfirmed amount must not carry a value.',
    )
    _non_negative = models.Constraint(
        'CHECK(COALESCE(amount, 0) >= 0)', 'Approved amounts cannot be negative.',
    )
