# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""ACL-checked Project Dossier file download & upload routes (Mandatory Case #14 — zero ID enumeration leak)."""
import base64

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request
from odoo.http.stream import content_disposition


class TpProjectDossierController(http.Controller):
    @http.route('/tp/dossier/download/<int:version_id>', type='http', auth='user', methods=['GET'])
    def download_dossier_version(self, version_id, **kw):
        ver = request.env['tp.project.dossier.version'].sudo().browse(version_id).exists()
        if not ver:
            return request.not_found()
        dossier = request.env['tp.project.dossier'].browse(ver.dossier_id.id)
        try:
            dossier.check_access('read')
            dossier._tp_check_project_read()
        except AccessError:
            # Return 404/403 without leaking dossier existence or filename
            return request.make_response('Forbidden: Outside project scope.', status=403)

        att = ver.attachment_id.sudo()
        raw = base64.b64decode(att.datas or b'')
        headers = [
            ('Content-Type', att.mimetype or 'application/octet-stream'),
            ('Content-Length', str(len(raw))),
            ('Content-Disposition', content_disposition(ver.file_name or 'ho-so.pdf')),
            ('X-Content-Type-Options', 'nosniff'),
        ]
        return request.make_response(raw, headers=headers)

    @http.route('/tp/dossier/<int:dossier_id>/upload', type='http', auth='user', methods=['POST'], csrf=True)
    def upload_dossier_version(self, dossier_id, file=None, change_note='', **kw):
        dossier = request.env['tp.project.dossier'].browse(dossier_id).exists()
        if not dossier:
            return request.make_json_response({'ok': False, 'error': 'Không tìm thấy hồ sơ dự án.'}, status=404)
        if not file:
            return request.make_json_response({'ok': False, 'error': 'Vui lòng chọn tệp tải lên.'}, status=400)
        try:
            raw = file.read()
            if len(raw) > 50 * 1024 * 1024:
                return request.make_json_response({'ok': False, 'error': 'Tệp vượt quá 50 MB.'}, status=400)
            res = dossier.action_upload_new_version(
                file_name=file.filename or 'ho-so.pdf',
                datas_b64=base64.b64encode(raw).decode('ascii'),
                mimetype=file.content_type or 'application/pdf',
                change_note=change_note,
            )
            return request.make_json_response({'ok': True, **res})
        except (AccessError, UserError) as exc:
            return request.make_json_response({'ok': False, 'error': str(exc)}, status=403)
