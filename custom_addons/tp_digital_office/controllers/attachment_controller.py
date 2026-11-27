# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""ACL-checked upload & download controller for tp.announcement and tp.meeting.minute."""
import base64

from odoo import Command, http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.http.stream import content_disposition


class TpDigitalOfficeAttachmentController(http.Controller):
    MAX_BYTES = 20 * 1024 * 1024

    @http.route(
        '/tp_digital_office/attachment/<string:res_model>/<int:res_id>/upload',
        type='http', auth='user', methods=['POST'], csrf=True,
    )
    def upload_attachment(self, res_model, res_id, file=None, **kw):
        if res_model not in ('tp.announcement', 'tp.meeting.minute'):
            return request.make_json_response({'ok': False, 'error': 'Model không hợp lệ.'}, status=400)
        rec = request.env[res_model].browse(res_id).exists()
        if not rec or not rec._tp_can_manage():
            return request.make_json_response({'ok': False, 'error': 'Không có quyền đính kèm tệp.'}, status=403)
        if not file:
            return request.make_json_response({'ok': False, 'error': 'Chưa chọn tệp.'}, status=400)

        raw = file.read()
        if len(raw) > self.MAX_BYTES:
            return request.make_json_response({'ok': False, 'error': 'Dung lượng tệp vượt quá 20 MB.'}, status=400)

        att = request.env['ir.attachment'].sudo().create({
            'name': file.filename or 'tai-lieu-dinh-kem',
            'datas': base64.b64encode(raw),
            'mimetype': file.content_type or 'application/octet-stream',
            'res_model': res_model,
            'res_id': rec.id,
            'public': False,
        })
        ctx_key = '_tp_announcement_internal' if res_model == 'tp.announcement' else '_tp_minute_internal_write'
        rec.with_context(**{ctx_key: True}).write({'attachment_ids': [Command.link(att.id)]})
        return request.make_json_response({
            'ok': True,
            'attachment': {
                'id': att.id,
                'name': att.name,
                'file_size': att.file_size or len(raw),
                'download_url': f'/tp_digital_office/attachment/{res_model}/{rec.id}/{att.id}',
            },
        })

    @http.route(
        '/tp_digital_office/attachment/<string:res_model>/<int:res_id>/<int:att_id>',
        type='http', auth='user', methods=['GET'],
    )
    def download_attachment(self, res_model, res_id, att_id, **kw):
        if res_model not in ('tp.announcement', 'tp.meeting.minute'):
            return request.not_found()
        rec = request.env[res_model].browse(res_id).exists()
        if not rec:
            return request.not_found()
        try:
            if res_model == 'tp.announcement':
                if not rec._tp_is_user_in_audience():
                    return request.not_found()
            else:
                rec.check_access('read')
        except AccessError:
            return request.not_found()

        att = request.env['ir.attachment'].sudo().browse(att_id).exists()
        if not att or att.res_model != res_model or att.res_id != rec.id:
            return request.not_found()
        raw = base64.b64decode(att.datas or b'')
        headers = [
            ('Content-Type', att.mimetype or 'application/octet-stream'),
            ('Content-Length', str(len(raw))),
            ('Content-Disposition', content_disposition(att.name or f'tai-lieu-{att.id}')),
            ('X-Content-Type-Options', 'nosniff'),
        ]
        return request.make_response(raw, headers=headers)
