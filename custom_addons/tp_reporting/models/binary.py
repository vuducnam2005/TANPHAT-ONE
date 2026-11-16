"""Check report audience before Odoo's signed-token shortcut can elevate a stream."""
from odoo import _, models
from odoo.exceptions import AccessError

REPORT_PARENTS = frozenset({'tp.report.document', 'tp.report.line', 'tp.report.value'})


class ReportingBinary(models.AbstractModel):
    _inherit = 'ir.binary'

    def _find_record(self, xmlid=None, res_model='ir.attachment', res_id=None, access_token=None, field=None):
        record = (self.env.ref(xmlid, raise_if_not_found=False) if xmlid else
                  self.env[res_model].browse(res_id).exists() if res_id and res_model in self.env else None)
        if record and record._name == 'ir.attachment':
            # Read routing metadata only under sudo; all content permissions use caller rights.
            metadata = record.sudo()
            if metadata.res_model in REPORT_PARENTS and metadata.res_id:
                if metadata.public or metadata.access_token:
                    raise AccessError(_('Minh chứng báo cáo không được công khai hoặc chia sẻ bằng token.'))
                target = self.env[metadata.res_model].sudo(False).browse(metadata.res_id).exists()
                if not target:
                    raise AccessError(_('Không có quyền truy cập minh chứng báo cáo.'))
                target.check_access('read')
                record.sudo(False).check_access('read')
        elif record and record._name in REPORT_PARENTS:
            record.sudo(False).check_access('read')
        return super()._find_record(xmlid, res_model, res_id, access_token, field)
