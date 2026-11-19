import json

from odoo.exceptions import AccessError, ValidationError
from odoo.http import Controller, request, route


class HrExportController(Controller):
    @route('/tp_hr/export', type='http', auth='user', methods=['GET', 'POST'])
    def export_hr(self, department_id='', job_id='', status='active', employment_kind='', missing_basic='', **_params):
        try:
            if 'options' in _params:
                if not isinstance(_params['options'], str) or len(_params['options']) > 1_000_000:
                    return request.make_response('Phạm vi xuất không hợp lệ.', status=400)
                content = request.env['tp.hr.workspace']._build_xlsx(options=json.loads(_params['options']))
            else:
                content = request.env['tp.hr.workspace']._build_xlsx({
                    'department_id': department_id, 'job_id': job_id, 'status': status,
                    'employment_kind': employment_kind, 'missing_basic': missing_basic,
                })
        except AccessError:
            return request.make_response('Không có quyền xem báo cáo HR.', status=403)
        except (ValidationError, ValueError, TypeError):
            return request.make_response('Bộ lọc HR không hợp lệ.', status=400)
        return request.make_response(content, headers=[
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', 'attachment; filename="TANPHAT-ONE-Danh-sach-nhan-vien.xlsx"'),
            ('Cache-Control', 'no-store'), ('X-Content-Type-Options', 'nosniff'),
        ])
