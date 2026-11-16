"""Strict own-employee contract attachment download endpoint for self-service profile."""
import base64
from urllib.parse import quote

from odoo.http import Controller, request, route


class HrMyProfileController(Controller):
    @route('/tp_hr/my_contract/<int:doc_id>/<string:field_name>', type='http', auth='user', methods=['GET'])
    def download_my_contract_file(self, doc_id, field_name, **_params):
        if field_name not in ('file', 'appendix'):
            return request.make_response('Yêu cầu không hợp lệ.', status=400)
        employee = request.env.user._tp_main_employee()
        if not employee:
            return request.make_response('Không có hồ sơ nhân sự gắn với tài khoản.', status=403)
        doc = request.env['tp.hr.contract.document'].sudo().browse(doc_id).exists()
        if not doc or doc.employee_id.id != employee.id:
            return request.make_response('Không có quyền truy cập tệp hợp đồng của nhân viên khác.', status=403)
        binary_val = doc.with_context(bin_size=False)[field_name]
        if not binary_val:
            return request.make_response('Không tìm thấy tệp đính kèm.', status=404)
        content = binary_val.content if hasattr(binary_val, 'content') else base64.b64decode(binary_val)
        if not content:
            return request.make_response('Không tìm thấy tệp đính kèm.', status=404)
        raw_name = (doc.filename if field_name == 'file' else doc.appendix_filename) or f'{field_name}-{doc.id}.bin'
        ascii_name = ''.join(ch if 32 <= ord(ch) < 127 and ch not in '"\\/' else '_' for ch in raw_name) or 'document.bin'
        encoded_name = quote(raw_name)
        return request.make_response(content, headers=[
            ('Content-Type', 'application/octet-stream'),
            ('Content-Disposition', f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded_name}"),
            ('Cache-Control', 'no-store'),
            ('X-Content-Type-Options', 'nosniff'),
        ])
