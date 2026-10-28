from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

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
    file = fields.Binary(attachment=True)
    file_name = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        documents = super().create(vals_list)
        documents.sudo().revision_id._tp_check_content_editable()
        return documents

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
        if any(document.revision_id and document.revision_id.submission_ids for document in self.sudo()):
            raise UserError(self.env._('Documents of a submitted revision cannot be changed or deleted.'))

    @api.constrains('document_kind', 'confidentiality', 'revision_id', 'contract_id')
    def _check_classification(self):
        for document in self:
            if document.document_kind in FINANCIAL_KINDS and document.confidentiality != 'financial':
                raise ValidationError(self.env._('Signed contracts, amendments and BASE evidence are financial documents.'))
            if document.revision_id and document.revision_id.contract_id != document.contract_id:
                raise ValidationError(self.env._('The document revision must belong to the same contract.'))
