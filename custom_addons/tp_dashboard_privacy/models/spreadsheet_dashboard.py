from werkzeug.exceptions import Forbidden

from odoo import api, fields, models
from odoo.exceptions import AccessError


class SpreadsheetDashboard(models.Model):
    _inherit = 'spreadsheet.dashboard'

    tp_internal_only = fields.Boolean(
        string='Chỉ truy cập nội bộ', copy=False,
        groups='spreadsheet_dashboard.group_dashboard_manager',
        help='Chặn bản sao chia sẻ bằng đường dẫn công khai. Quyền đọc dữ liệu nguồn vẫn theo người xem.',
    )


class SpreadsheetDashboardShare(models.Model):
    _inherit = 'spreadsheet.dashboard.share'

    def _check_tp_share_dashboard(self, dashboard_id):
        dashboard = self.env['spreadsheet.dashboard'].browse(dashboard_id)
        dashboard.check_access('read')
        if dashboard.sudo().tp_internal_only:
            raise AccessError(self.env._('Bảng tổng hợp này chỉ cho phép truy cập bằng tài khoản nội bộ được cấp quyền.'))

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(['dashboard_id'])
        for vals in vals_list:
            self._check_tp_share_dashboard(vals.get('dashboard_id') or defaults.get('dashboard_id'))
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('dashboard_id'):
            self._check_tp_share_dashboard(vals['dashboard_id'])
        return super().write(vals)

    def _check_dashboard_access(self, access_token):
        if self.dashboard_id.sudo().tp_internal_only:
            raise Forbidden()
        return super()._check_dashboard_access(access_token)
