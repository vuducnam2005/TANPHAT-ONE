from odoo import api, models
from odoo.exceptions import AccessError

from .tp_contract_document import _DOCUMENT_INTERNAL

# Attachment fields that carry or relink the stored binary.
CONTENT_FIELDS = frozenset({'datas', 'raw', 'db_datas', 'store_fname', 'checksum', 'res_model', 'res_id', 'res_field'})


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _tp_document_parent(self, mutate=False):
        for attachment in self.sudo():
            if attachment.res_model == 'tp.contract.document' and attachment.res_id:
                document = self.env['tp.contract.document'].sudo(False).browse(attachment.res_id).exists()
                document._tp_check_document_read()
                if mutate and self.env.context.get('_tp_document_internal') is not _DOCUMENT_INTERNAL:
                    raise AccessError(self.env._('Contract evidence changes through a versioned draft command.'))

    def read(self, fields=None, load='_classic_read'):
        self._tp_document_parent()
        return super().read(fields=fields, load=load)

    def export_data(self, fields_to_export):
        self._tp_document_parent()
        return super().export_data(fields_to_export)

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(['res_model', 'res_id', 'public', 'access_token'])
        for supplied in vals_list:
            values = {**defaults, **supplied}
            if values.get('res_model') == 'tp.contract.document' and values.get('res_id'):
                if (self.env.context.get('_tp_document_internal') is not _DOCUMENT_INTERNAL
                        or values.get('public') or values.get('access_token')):
                    raise AccessError(self.env._('No direct or public contract evidence upload.'))
        return super().create(vals_list)

    def write(self, vals):
        self._tp_document_parent(mutate=True)
        if vals.get('res_model') == 'tp.contract.document':
            raise AccessError(self.env._('Do not relink a contract document attachment.'))
        if CONTENT_FIELDS & set(vals):
            self._tp_check_contract_documents()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_submitted_contract_document(self):
        self._tp_document_parent(mutate=True)
        self._tp_check_contract_documents()

    def _tp_check_contract_documents(self):
        # The document guard alone would not stop direct attachment edits.
        document_ids = [
            attachment.res_id for attachment in self.sudo()
            if attachment.res_model == 'tp.contract.document' and attachment.res_id
        ]
        if document_ids:
            self.env['tp.contract.document'].sudo().browse(document_ids).exists()._tp_check_not_submitted()


class ContractBinary(models.AbstractModel):
    _inherit = 'ir.binary'

    def _find_record(self, xmlid=None, res_model='ir.attachment', res_id=None, access_token=None, field=None):
        record = (self.env.ref(xmlid, False) if xmlid else
                  self.env[res_model].browse(res_id).exists() if res_id and res_model in self.env else None)
        if record and record._name == 'ir.attachment':
            record._tp_document_parent()
        elif record and record._name == 'tp.contract.document':
            record.sudo(False)._tp_check_document_read()
        return super()._find_record(xmlid, res_model, res_id, access_token, field)
