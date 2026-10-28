import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

from .tp_contract import WORKFLOW_CONTEXT

_logger = logging.getLogger(__name__)

WORKFLOW_ACTIONS = [
    ('create_contract', 'Create Contract Draft'),
    ('create_amendment', 'Create Amendment Draft'),
    ('edit_draft', 'Edit Draft'),
    ('submit_review', 'Submit for Review'),
    ('resubmit_review', 'Resubmit for Review'),
    ('return_review', 'Return for Rework'),
    ('begin_rework', 'Begin Rework'),
]


class TpContractAudit(models.Model):
    """Append-only history of contract workflow actions. It never stores amounts."""

    _name = 'tp.contract.audit'
    _description = 'Tan Phat Contract Workflow Audit'
    _order = 'id'

    event_id = fields.Char(required=True, index=True, copy=False)
    action = fields.Selection(WORKFLOW_ACTIONS, required=True)
    actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    acted_at = fields.Datetime(required=True)
    request_id = fields.Char()
    contract_id = fields.Many2one('tp.contract', required=True, ondelete='restrict', index=True)
    revision_id = fields.Many2one('tp.contract.revision', ondelete='restrict', index=True)
    submission_id = fields.Many2one('tp.contract.submission', ondelete='restrict')
    project_id = fields.Many2one(related='contract_id.project_id', store=True, index=True, precompute=True)
    company_id = fields.Many2one(related='contract_id.company_id', store=True, index=True, precompute=True)
    department_id = fields.Many2one('hr.department', ondelete='restrict')
    state_before = fields.Char()
    state_after = fields.Char()
    version_before = fields.Integer()
    version_after = fields.Integer(required=True)
    payload_sha256 = fields.Char()
    reason = fields.Text()

    _event_unique = models.Constraint('UNIQUE(event_id)', 'Audit event IDs are unique.')

    def write(self, vals):
        self.check_access('write')
        raise UserError(self.env._('The contract audit trail is append-only.'))

    @api.ondelete(at_uninstall=False)
    def _unlink_never(self):
        raise UserError(self.env._('The contract audit trail is append-only.'))


class TpContractOutbox(models.Model):
    """Notification event per recipient, written in the action transaction.

    Delivery runs after commit and is retried; ``(event_id, recipient_id)`` is
    unique so a retried action or delivery never notifies twice. The in-app
    channel is this record itself: the recipient reads it under the access rule.
    """

    _name = 'tp.contract.outbox'
    _description = 'Tan Phat Contract Notification Outbox'
    _order = 'id'

    event_id = fields.Char(required=True, index=True)
    audit_id = fields.Many2one('tp.contract.audit', required=True, ondelete='restrict')
    event_type = fields.Selection(WORKFLOW_ACTIONS, required=True)
    recipient_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True)
    contract_id = fields.Many2one('tp.contract', required=True, ondelete='restrict', index=True)
    revision_id = fields.Many2one('tp.contract.revision', ondelete='restrict')
    project_id = fields.Many2one(related='contract_id.project_id', store=True, index=True, precompute=True)
    company_id = fields.Many2one(related='contract_id.company_id', store=True, index=True, precompute=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
    ], required=True, default='pending', index=True)
    attempt_count = fields.Integer(default=0)
    last_error = fields.Char()
    delivered_at = fields.Datetime()

    _event_recipient_unique = models.Constraint(
        'UNIQUE(event_id, recipient_id)', 'An event is queued once per recipient.',
    )

    def write(self, vals):
        self.check_access('write')
        if not self.env.context.get(WORKFLOW_CONTEXT) or set(vals) - {'state', 'attempt_count', 'last_error', 'delivered_at'}:
            raise UserError(self.env._('Only the delivery worker updates notification delivery.'))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_never(self):
        raise UserError(self.env._('Notification events are kept for delivery history.'))

    @api.model
    def _tp_deliver_pending(self, limit=100):
        """Deliver pending events; a failing event stays pending for the next run."""
        events = self.sudo().with_context(**{WORKFLOW_CONTEXT: True}).search([('state', '=', 'pending')], limit=limit)
        for event in events:
            try:
                with self.env.cr.savepoint():
                    event._tp_send()
                    event.write({'state': 'delivered', 'delivered_at': fields.Datetime.now(), 'last_error': False})
            except Exception as error:  # noqa: BLE001 - any channel failure is retried later
                _logger.warning('Contract notification %s for user %s not delivered: %s', event.event_id, event.recipient_id.id, error)
                event.write({'attempt_count': event.attempt_count + 1, 'last_error': str(error)[:200]})
        return len(events)

    def _tp_send(self):
        """Send through external channels. None is configured yet (CTR-002a);
        the outbox row is the in-app inbox entry."""
        self.ensure_one()


class TpContractIdempotency(models.Model):
    """Result of a workflow request per actor, action and client key.

    The fingerprint is an HMAC of the canonical payload including
    ``expected_version``; only IDs are stored, never amounts.
    """

    _name = 'tp.contract.idempotency'
    _description = 'Tan Phat Contract Workflow Idempotency Key'

    user_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True)
    action = fields.Char(required=True)
    key = fields.Char(required=True)
    object_ref = fields.Char(required=True, help='Scope object the key was used on, e.g. contract:12/revision:30.')
    fingerprint = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict')
    project_id = fields.Many2one('project.project', required=True, ondelete='restrict')
    required_capabilities = fields.Char(help='Capabilities rechecked before a replay returns the result.')
    result_contract_id = fields.Many2one('tp.contract', ondelete='restrict')
    result_revision_id = fields.Many2one('tp.contract.revision', ondelete='restrict')
    result_submission_id = fields.Many2one('tp.contract.submission', ondelete='restrict')

    _key_unique = models.Constraint('UNIQUE(user_id, action, key)', 'An idempotency key is used once per action.')

    def write(self, vals):
        self.check_access('write')
        allowed = {'required_capabilities', 'result_contract_id', 'result_revision_id', 'result_submission_id'}
        if not self.env.context.get(WORKFLOW_CONTEXT) or set(vals) - allowed or any(self.mapped('result_contract_id')):
            raise UserError(self.env._('An idempotency result is recorded once.'))
        return super().write(vals)
