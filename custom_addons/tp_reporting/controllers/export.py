import json

from odoo import _
from odoo.exceptions import ValidationError
from odoo.http import Controller, request, route
from odoo.http.stream import content_disposition


class ReportingExport(Controller):
    @route('/tp_reporting/export', type='http', auth='user', methods=['GET', 'POST'])
    def export_report(self, format='xlsx', ids='', domain='[]', snapshot_id='', **kwargs):
        try:
            selected = [int(value) for value in ids.split(',') if value] if ids else None
            applied_domain = json.loads(domain)
            snapshot = int(snapshot_id) if snapshot_id else None
        except (ValueError, TypeError) as error:
            raise ValidationError(_('Bộ lọc xuất báo cáo không hợp lệ.')) from error
        payload = request.env['tp.reporting.export']._build(
            format, selected, applied_domain, snapshot,
        )
        return request.make_response(payload['content'], headers=[
            ('Content-Type', payload['mimetype']),
            ('Content-Disposition', content_disposition(payload['filename'])),
            ('Cache-Control', 'private, no-store, no-cache, must-revalidate, max-age=0'),
            ('Pragma', 'no-cache'),
            ('X-Content-Type-Options', 'nosniff'),
        ])
