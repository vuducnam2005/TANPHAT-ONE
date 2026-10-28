from odoo import api, fields, models
from odoo.exceptions import UserError

from .tp_contract import WORKFLOW_CONTEXT

# Fields a workflow action may fill once after the submission is created.
RETURN_FIELDS = frozenset({'outcome', 'returned_by_id', 'returned_at', 'return_reason', 'return_issues'})
REWORK_FIELDS = frozenset({'rework_started_by_id', 'rework_started_at', 'rework_reason'})


class TpContractSubmission(models.Model):
    """Immutable review submission of a draft revision.

    The metadata snapshot carries no money; amounts and financial documents
    live in ``tp.contract.submission.amount`` under the financial.read domain.
    Only the return outcome and the start of rework are recorded later, once.
    """

    _name = 'tp.contract.submission'
    _description = 'Tan Phat Contract Review Submission'
    _order = 'revision_id, sequence'

    revision_id = fields.Many2one('tp.contract.revision', required=True, ondelete='restrict', index=True)
    contract_id = fields.Many2one(related='revision_id.contract_id', store=True, index=True, precompute=True)
    project_id = fields.Many2one(related='revision_id.project_id', store=True, index=True, precompute=True)
    company_id = fields.Many2one(related='revision_id.company_id', store=True, index=True, precompute=True)
    sequence = fields.Integer(required=True, help='1 is the first submission (S1) of the revision.')
    previous_submission_id = fields.Many2one('tp.contract.submission', ondelete='restrict', index=True)
    submitted_by_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    submitted_at = fields.Datetime(required=True)
    reviewer_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True)
    contract_version = fields.Integer(required=True, help='Aggregate contract version captured by this submission.')
    fix_summary = fields.Text(help='What changed since the previous returned submission.')
    metadata_snapshot = fields.Json(required=True)
    metadata_sha256 = fields.Char(required=True)
    payload_sha256 = fields.Char(
        required=True, help='Hash over the metadata hash and the salted financial hash; reveals no amount.',
    )
    outcome = fields.Selection([
        ('pending', 'Pending Review'),
        ('returned', 'Returned'),
    ], required=True, default='pending')
    returned_by_id = fields.Many2one('res.users', ondelete='restrict')
    returned_at = fields.Datetime()
    return_reason = fields.Text()
    return_issues = fields.Json()
    rework_started_by_id = fields.Many2one('res.users', ondelete='restrict')
    rework_started_at = fields.Datetime()
    rework_reason = fields.Text()

    _sequence_unique = models.Constraint(
        'UNIQUE(revision_id, sequence)', 'Each submission sequence is unique within its revision.',
    )
    _one_pending = models.UniqueIndex(
        "(revision_id) WHERE (outcome = 'pending')", 'A revision has at most one submission under review.',
    )
    _return_evidence = models.Constraint(
        "CHECK(outcome = 'pending' OR (returned_by_id IS NOT NULL AND returned_at IS NOT NULL "
        "AND length(btrim(COALESCE(return_reason, ''))) > 0))",
        'A returned submission requires the reviewer, the time and a reason.',
    )
    _rework_after_return = models.Constraint(
        "CHECK(rework_started_at IS NULL OR (outcome = 'returned' AND length(btrim(COALESCE(rework_reason, ''))) > 0))",
        'Rework starts only after a return and requires a reason.',
    )

    def write(self, vals):
        self.check_access('write')
        if not self.env.context.get(WORKFLOW_CONTEXT):
            raise UserError(self.env._('Review submissions change only through workflow actions.'))
        keys = set(vals)
        for submission in self:
            if keys <= RETURN_FIELDS and submission.outcome == 'pending' and vals.get('outcome') == 'returned':
                continue
            if keys <= REWORK_FIELDS and submission.outcome == 'returned' and not submission.rework_started_at:
                continue
            raise UserError(self.env._('A review submission is immutable once recorded.'))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_never(self):
        raise UserError(self.env._('Review submissions keep the review history and cannot be deleted.'))


class TpContractSubmissionAmount(models.Model):
    """Financial part of a submission snapshot, readable only with financial.read."""

    _name = 'tp.contract.submission.amount'
    _description = 'Tan Phat Contract Submission Amounts'

    submission_id = fields.Many2one('tp.contract.submission', required=True, ondelete='restrict', index=True)
    revision_id = fields.Many2one(related='submission_id.revision_id', store=True, index=True, precompute=True)
    project_id = fields.Many2one(related='submission_id.project_id', store=True, index=True, precompute=True)
    company_id = fields.Many2one(related='submission_id.company_id', store=True, index=True, precompute=True)
    financial_snapshot = fields.Json(required=True)
    salt = fields.Char(required=True)
    financial_sha256 = fields.Char(required=True)

    _submission_unique = models.Constraint('UNIQUE(submission_id)', 'A submission has one financial snapshot.')

    def write(self, vals):
        self.check_access('write')
        raise UserError(self.env._('A submission financial snapshot is immutable.'))

    @api.ondelete(at_uninstall=False)
    def _unlink_never(self):
        raise UserError(self.env._('A submission financial snapshot cannot be deleted.'))
