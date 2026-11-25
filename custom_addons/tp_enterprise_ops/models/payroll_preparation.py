# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""J4: Payroll Input Reconciliation Table (Attendance + Leave + Field Trips + Internal Allocations), strictly gated by Policy Approval & Payroll RBAC (Case #17)."""
from datetime import date
import calendar

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

from odoo.addons.tp_request.models.request_common import is_live_admin_user


def _check_payroll_access(env, company=None):
    user = env.user
    company = company or env.company
    if is_live_admin_user(user, company=company):
        return True
    if user.has_group('hr.group_hr_manager') or user.has_group('tp_hr_workspace.group_tp_hr_manager'):
        return True
    raise AccessError(_('Dữ liệu đối soát đầu vào tiền lương được bảo mật nghiêm ngặt; bạn không có thẩm quyền truy cập.'))


class TpPayrollPolicy(models.Model):
    _name = 'tp.payroll.policy'
    _description = 'Quy chế & Tham số Tính lương (Chờ phê duyệt chính thức)'
    _order = 'id desc'

    company_id = fields.Many2one('res.company', required=True, default=lambda s: s.env.company, index=True)
    name = fields.Char(required=True, default='Quy chế Tiền lương TANPHAT ONE')
    state = fields.Selection(
        [
            ('pending_approval', 'Chờ phê duyệt quy chế công ty (chưa tính lương thực trả)'),
            ('approved', 'Đã phê duyệt chính thức'),
        ],
        default='pending_approval',
        required=True,
    )
    pending_questions_note = fields.Text(
        default=(
            '1. Bậc lương cơ bản / phụ cấp trách nhiệm / phụ cấp hiện trường.\n'
            '2. Tỷ lệ trích nộp BHXH, BHYT, BHTN và trần đóng theo quy định hiện hành.\n'
            '3. Quy tắc quy đổi công thiếu giờ / đi muộn và cơ chế quyết toán khoán nội bộ.'
        ),
        readonly=True,
    )


class TpPayrollInputSheet(models.Model):
    _name = 'tp.payroll.input.sheet'
    _description = 'Bảng đối soát dữ liệu đầu vào tiền lương theo kỳ (chưa giả lập công thức lương)'
    _order = 'period_month desc, id desc'

    company_id = fields.Many2one('res.company', required=True, default=lambda s: s.env.company, index=True)
    period_month = fields.Char(string='Kỳ tháng (YYYY-MM)', required=True, index=True)
    state = fields.Selection(
        [
            ('reconciling_inputs', 'Đang đối soát dữ liệu đầu vào (Chờ quy chế lương)'),
            ('inputs_locked', 'Đã khóa đầu vào đối soát'),
        ],
        default='reconciling_inputs',
        required=True,
    )
    line_ids = fields.One2many('tp.payroll.input.line', 'sheet_id', string='Dòng đối soát nhân sự')

    _month_company_uniq = models.Constraint(
        'UNIQUE(company_id, period_month)',
        'Mỗi tháng chỉ có một bảng đối soát đầu vào lương trong công ty.',
    )

    @api.model
    def tp_generate_input_reconciliation(self, period_month):
        """Collect real attendance days + approved leave/business trips without inventing salary/tax numbers."""
        _check_payroll_access(self.env)
        company = self.env.company
        try:
            yr, mo = (int(x) for x in (period_month or '').strip().split('-'))
            d_start = date(yr, mo, 1)
            d_end = date(yr, mo, calendar.monthrange(yr, mo)[1])
        except Exception:
            raise UserError(_('Kỳ tháng phải theo định dạng YYYY-MM (ví dụ: 2026-11).'))

        sheet = self.sudo().search([('company_id', '=', company.id), ('period_month', '=', period_month)], limit=1)
        if not sheet:
            sheet = self.sudo().create({'company_id': company.id, 'period_month': period_month})

        emps = self.env['hr.employee'].sudo().search([('company_id', '=', company.id), ('active', '=', True)], order='name')
        Day = self.env['tp.hr.attendance.day'].sudo()
        Req = self.env['tp.request'].sudo()

        existing_by_emp = {ln.employee_id.id: ln for ln in sheet.line_ids}
        for emp in emps:
            days = Day.search([
                ('company_id', '=', company.id),
                ('employee_id', '=', emp.id),
                ('work_date', '>=', d_start),
                ('work_date', '<=', d_end),
            ])
            confirmed_units = round(sum(d.units for d in days if d.units_state == 'confirmed'), 2)
            recorded_days = len(days.filtered(lambda d: d.in_time and d.out_time))

            leave_reqs = Req.search([
                ('company_id', '=', company.id),
                ('requester_employee_id', '=', emp.id),
                ('handler_kind', '=', 'leave_request'),
                ('approval_state', '=', 'approved'),
                ('leave_date_from', '<=', d_end),
                ('leave_date_to', '>=', d_start),
            ])
            trip_reqs = Req.search([
                ('company_id', '=', company.id),
                ('requester_employee_id', '=', emp.id),
                ('handler_kind', '=', 'business_trip'),
                ('approval_state', '=', 'approved'),
                ('leave_date_from', '<=', d_end),
                ('leave_date_to', '>=', d_start),
            ])
            vals = {
                'recorded_punch_days': recorded_days,
                'confirmed_work_units': confirmed_units,
                'approved_leave_days': sum(leave_reqs.mapped('leave_days_count')),
                'approved_trip_days': sum(trip_reqs.mapped('leave_days_count')),
                'net_pay_status': 'Chờ phê duyệt quy chế lương — Không giả lập số tiền',
            }
            if emp.id in existing_by_emp:
                existing_by_emp[emp.id].write(vals)
            else:
                self.env['tp.payroll.input.line'].sudo().create({
                    **vals,
                    'sheet_id': sheet.id,
                    'employee_id': emp.id,
                })
        return {'sheet_id': sheet.id, 'line_count': len(sheet.line_ids)}

    def action_compute_live_salary(self):
        """Explicitly block live net-pay calculation until official Payroll Policy is approved."""
        self.ensure_one()
        _check_payroll_access(self.env, company=self.company_id)
        approved_policy = self.env['tp.payroll.policy'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'approved'),
        ], limit=1)
        if not approved_policy:
            raise UserError(_(
                'Chưa thể tính lương thực trả: Quy chế tiền lương, tỷ lệ BHXH và thuế TNCN của công ty đang ở trạng thái Chờ phê duyệt. '
                'Hệ thống chỉ đối soát dữ liệu đầu vào (ngày công, nghỉ phép, công tác) và không tự bịa công thức tài chính.'
            ))
        return True


class TpPayrollInputLine(models.Model):
    _name = 'tp.payroll.input.line'
    _description = 'Dòng đối soát đầu vào tiền lương từng nhân viên'
    _order = 'id asc'

    sheet_id = fields.Many2one('tp.payroll.input.sheet', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='sheet_id.company_id', store=True, index=True)
    employee_id = fields.Many2one('hr.employee', required=True, ondelete='restrict', index=True)
    recorded_punch_days = fields.Integer(string='Số ngày đủ vào/ra')
    confirmed_work_units = fields.Float(string='Tổng công xác nhận')
    approved_leave_days = fields.Float(string='Ngày nghỉ phép đã duyệt')
    approved_trip_days = fields.Float(string='Ngày công tác đã duyệt')
    net_pay_status = fields.Char(
        string='Lương thực lĩnh',
        default='Chờ phê duyệt quy chế lương — Không giả lập số tiền',
        readonly=True,
    )
