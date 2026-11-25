# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""J3: Approved Leave / Business Trip -> Attendance Summary Bridge (Mandatory Case #12) & Disabled-by-default Field Checkin Schema."""
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.tp_hr_attendance.models.attendance_logic import dates_between


class TpAttendanceDayLeaveBridge(models.Model):
    _inherit = 'tp.hr.attendance.day'

    @api.model
    def _tp_approved_request_days(self, company, employee_ids, start, end):
        """Return dict {(employee_id, date): handler_kind} for approved HR_LEAVE / HR_BUSINESS_TRIP in tp.request."""
        if not employee_ids or 'tp.request' not in self.env:
            return {}
        reqs = self.env['tp.request'].sudo().search([
            ('company_id', '=', company.id),
            ('requester_employee_id', 'in', list(employee_ids)),
            ('handler_kind', 'in', ('leave_request', 'business_trip')),
            ('approval_state', '=', 'approved'),
            ('leave_date_from', '<=', end),
            ('leave_date_to', '>=', start),
        ])
        mapping = {}
        for req in reqs:
            emp_id = req.requester_employee_id.id
            d_first = max(req.leave_date_from, start)
            d_last = min(req.leave_date_to, end)
            for d in dates_between(d_first, d_last):
                mapping[(emp_id, d)] = req.handler_kind
        return mapping

    @api.model
    def _tp_leave_days(self, company, employee_ids, start, end):
        base_set = super()._tp_leave_days(company, employee_ids, start, end)
        req_map = self._tp_approved_request_days(company, employee_ids, start, end)
        combined = set(base_set or set()) | set(req_map.keys())
        return combined

    @api.model
    def _tp_presence(self, company, employee_ids, start, end, today):
        """Integrate approved leave/business-trip requests WITHOUT mutating raw punches.

        Mandatory Case #12:
        - If a day has NO machine punch and has an approved leave/trip -> state='leave' (never fabricates check-in/out!).
        - If a day has BOTH raw machine punch AND an approved leave/trip -> flags state='review', tp_leave_conflict=True
          ('Cần kiểm tra') while keeping raw in/out clock times 100% intact!
        """
        result, has_leave = super()._tp_presence(company, employee_ids, start, end, today)
        if not employee_ids:
            return result, True
        req_map = self._tp_approved_request_days(company, employee_ids, start, end)
        for key, kind in req_map.items():
            cell = result.get(key)
            if not cell or key[1] > today:
                continue
            has_real_punch = bool(cell.get('in') or cell.get('out') or cell.get('punches'))
            if has_real_punch:
                # Conflict: employee has both machine punch AND approved leave/trip -> flag 'review' without touching punches!
                cell['state'] = 'review'
                cell['tp_leave_conflict'] = True
                cell['tp_request_basis'] = kind
                cell['label'] = 'Cần kiểm tra (trùng giờ máy & đơn nghỉ/công tác)'
            else:
                cell['state'] = 'leave'
                cell['tp_leave_conflict'] = False
                cell['tp_request_basis'] = kind
                cell['label'] = 'Công tác đã duyệt' if kind == 'business_trip' else 'Nghỉ đã xác nhận'
        return result, True


class TpFieldCheckin(models.Model):
    """Prepared schema for optional Field GPS/Selfie check-in (strictly disabled until company policy enables it)."""
    _name = 'tp.field.checkin'
    _description = 'Chấm công hiện trường GPS/Selfie (chờ kích hoạt theo quy chế)'
    _order = 'checkin_at desc, id desc'

    company_id = fields.Many2one('res.company', required=True, default=lambda s: s.env.company, index=True)
    employee_id = fields.Many2one('hr.employee', required=True, ondelete='restrict', index=True)
    project_id = fields.Many2one('project.project', string='Dự án hiện trường', ondelete='set null')
    checkin_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    latitude = fields.Float(digits=(10, 7), readonly=True)
    longitude = fields.Float(digits=(10, 7), readonly=True)
    selfie_attachment_id = fields.Many2one(
        'ir.attachment',
        ondelete='restrict',
        readonly=True,
        help='Tách biệt hoàn toàn khỏi ảnh đại diện hồ sơ nhân sự (image_1920) và sinh trắc học.',
    )
    note = fields.Char(readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        enabled = self.env['ir.config_parameter'].sudo().get_str('tp_attendance.field_gps_enabled') == '1'
        if not enabled:
            raise UserError(_(
                'Chức năng thu thập GPS/Selfie hiện trường đang tắt mặc định cho đến khi công ty ban hành quy chế bảo mật dữ liệu vị trí & thời hạn lưu trữ.'
            ))
        return super().create(vals_list)
