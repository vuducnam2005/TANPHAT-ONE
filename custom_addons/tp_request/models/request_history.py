# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Immutable system audit trail for tp.request (cannot be edited or deleted from UI/RPC)."""
from odoo import _, api, fields, models
from odoo.exceptions import AccessError

from .request_common import HISTORY_ACTIONS, INTERNAL, is_internal


class TpRequestHistory(models.Model):
    _name = 'tp.request.history'
    _description = 'Lịch sử xử lý đề nghị (bất biến)'
    _order = 'created_at desc, id desc'

    request_id = fields.Many2one('tp.request', string='Hồ sơ đề nghị', required=True, ondelete='cascade', index=True, readonly=True)
    company_id = fields.Many2one(related='request_id.company_id', store=True, index=True, readonly=True)
    created_at = fields.Datetime(string='Thời điểm', default=fields.Datetime.now, required=True, readonly=True, index=True)
    actor_id = fields.Many2one('res.users', string='Người thao tác', required=True, readonly=True, ondelete='restrict')
    actor_name = fields.Char(string='Tên người thao tác', required=True, readonly=True)
    action = fields.Selection(HISTORY_ACTIONS, string='Hành động', required=True, readonly=True, index=True)
    state_before = fields.Char(string='Trạng thái trước', readonly=True)
    state_after = fields.Char(string='Trạng thái sau', readonly=True)
    step_name = fields.Char(string='Bước duyệt / thực hiện', readonly=True)
    note = fields.Text(string='Ý kiến / lý do', readonly=True)
    request_version = fields.Integer(string='Phiên bản hồ sơ', required=True, default=1, readonly=True)
    result_ref = fields.Char(string='Liên kết kết quả nghiệp vụ', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if not is_internal(self):
            raise AccessError(_('Lịch sử hệ thống chỉ được ghi nhận tự động từ thao tác nghiệp vụ.'))
        for vals in vals_list:
            if not vals.get('actor_name') and vals.get('actor_id'):
                actor = self.env['res.users'].sudo().browse(vals['actor_id'])
                vals['actor_name'] = actor.name or ''
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(_('Lịch sử hệ thống không thể chỉnh sửa.'))

    def unlink(self):
        if self.env.su and self.env.context.get('_tp_request_cascade_draft') is INTERNAL:
            return super().unlink()
        raise AccessError(_('Lịch sử hệ thống không thể xóa.'))
