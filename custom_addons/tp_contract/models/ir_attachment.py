from odoo import api, models

# Attachment fields that carry or relink the stored binary.
CONTENT_FIELDS = frozenset({'datas', 'raw', 'db_datas', 'store_fname', 'checksum', 'res_model', 'res_id', 'res_field'})


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def write(self, vals):
        if CONTENT_FIELDS & set(vals):
            self._tp_check_contract_documents()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_submitted_contract_document(self):
        self._tp_check_contract_documents()

    def _tp_check_contract_documents(self):
        # The document guard alone would not stop direct attachment edits.
        document_ids = [
            attachment.res_id for attachment in self.sudo()
            if attachment.res_model == 'tp.contract.document' and attachment.res_id
        ]
        if document_ids:
            self.env['tp.contract.document'].sudo().browse(document_ids).exists()._tp_check_not_submitted()
