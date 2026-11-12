from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

_DOCUMENT_INTERNAL = object()


class GuardedContractBinary(fields.Binary):
    def __get__(self, record, owner=None):
        if record is not None and record:
            record._tp_check_document_read()
        return super().__get__(record, owner)


FINANCIAL_KINDS = ('signed_contract', 'amendment', 'base_evidence')


class TpContractDocument(models.Model):
    """Contract file whose record, attachment and filename share one access policy.

    Unclassified uploads default to the financial zone; signed contracts,
    amendments and BASE evidence always stay there.
    """

    _name = 'tp.contract.document'
    _description = 'Tan Phat Contract Document'
    _order = 'contract_id, id'

    contract_id = fields.Many2one('tp.contract', required=True, ondelete='restrict', index=True)
    revision_id = fields.Many2one('tp.contract.revision', ondelete='restrict', index=True)
    project_id = fields.Many2one(related='contract_id.project_id', store=True, index=True, precompute=True)
    company_id = fields.Many2one(related='contract_id.company_id', store=True, index=True, precompute=True)
    added_contract_version = fields.Integer(default=0, readonly=True, copy=False)
    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    document_kind = fields.Selection([
        ('signed_contract', 'Signed Contract'),
        ('amendment', 'Amendment'),
        ('base_evidence', 'BASE Evidence'),
        ('technical_scope', 'Technical Scope'),
        ('other', 'Other'),
    ], required=True)
    confidentiality = fields.Selection([
        ('financial', 'Financial'),
        ('general', 'General'),
    ], required=True, default='financial')
    file = GuardedContractBinary(attachment=True)
    file_name = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        documents = super(TpContractDocument, self.with_context(_tp_document_internal=_DOCUMENT_INTERNAL)).create(vals_list).with_env(self.env)
        documents.sudo().revision_id._tp_check_content_editable()
        return documents

    def _tp_check_document_read(self):
        if self.env.su:
            return
        if not self.env.user._is_internal():
            raise AccessError(self.env._('Contract documents cannot be shared publicly.'))
        self.check_access('read')
        for document in self:
            project = document.sudo().project_id.with_env(self.env)
            if not project.has_access('read'):
                raise AccessError(self.env._('The contract project is no longer accessible.'))
            if document.sudo().confidentiality == 'financial' and not self.env['tp.project.grant']._tp_has_capability(project, 'financial_read'):
                raise AccessError(self.env._('Financial document access has been revoked.'))

    def read(self, fields=None, load='_classic_read'):
        self._tp_check_document_read()
        return super().read(fields=fields, load=load)

    def export_data(self, fields_to_export):
        self._tp_check_document_read()
        return super().export_data(fields_to_export)

    def write(self, vals):
        self.check_access('write')
        self._tp_check_not_submitted()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_submitted(self):
        self._tp_check_not_submitted()

    def _tp_check_not_submitted(self):
        # A submission snapshot references the file by checksum; a later round
        # adds a new document instead of replacing the submitted one.
        for document in self.sudo():
            revision = document.revision_id
            if revision and (revision._tp_is_frozen() or any(
                submission.contract_version >= document.added_contract_version for submission in revision.submission_ids)):
                raise UserError(self.env._('Documents captured by a submission cannot be changed or deleted.'))

    @api.constrains('document_kind', 'confidentiality', 'revision_id', 'contract_id')
    def _check_classification(self):
        for document in self:
            if document.document_kind in FINANCIAL_KINDS and document.confidentiality != 'financial':
                raise ValidationError(self.env._('Signed contracts, amendments and BASE evidence are financial documents.'))
            if document.revision_id and document.revision_id.contract_id != document.contract_id:
                raise ValidationError(self.env._('The document revision must belong to the same contract.'))
