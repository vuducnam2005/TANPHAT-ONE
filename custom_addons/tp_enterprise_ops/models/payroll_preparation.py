# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""J4: Payroll Input Reconciliation Table (Attendance + Leave + Field Trips + Internal Allocations), strictly gated by Policy Approval & Payroll RBAC (Case #17)."""
import calendar
from datetime import date

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
    def _tp_parse_period_month(self, period_month):
        parts = (period_month or '').strip().split('-')
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            raise UserError(_('Kỳ tháng phải theo định dạng YYYY-MM (ví dụ: 2026-11).'))
        yr, mo = int(parts[0]), int(parts[1])
        if mo < 1 or mo > 12 or yr < 2000 or yr > 2100:
            raise UserError(_('Kỳ tháng phải theo định dạng YYYY-MM (ví dụ: 2026-11).'))
        d_start = date(yr, mo, 1)
        d_end = date(yr, mo, calendar.monthrange(yr, mo)[1])
        return f'{yr:04d}-{mo:02d}', d_start, d_end

    @api.model
    def _tp_employee_order_key(self, emp):
        dept = emp.department_id
        dept_seq = getattr(dept, 'tp_sequence', 0) if dept else 0
        return (not bool(dept), dept_seq, dept.id or 0, emp.sequence or 0, emp.id or 0)

    @api.model
    def tp_get_input_reconciliation(self, period_month):
        """Read-only fetch for Payroll Input Reconciliation — NEVER creates, updates, or unlinks DB rows."""
        _check_payroll_access(self.env)
        company = self.env.company
        norm_month, _d_start, _d_end = self._tp_parse_period_month(period_month)

        policy = self.env['tp.payroll.policy'].sudo().search([('company_id', '=', company.id)], limit=1)
        default_note = self.env['tp.payroll.policy']._fields['pending_questions_note'].default(self.env['tp.payroll.policy'])
        policy_note = policy.pending_questions_note if policy else default_note

        dept_order = 'tp_sequence, id' if 'tp_sequence' in self.env['hr.department']._fields else 'name, id'
        depts = self.env['hr.department'].sudo().search(
            [('company_id', 'in', [False, company.id])],
            order=dept_order,
        )
        dept_list = [{'id': d.id, 'name': d.name} for d in depts]

        sheet = self.sudo().search([('company_id', '=', company.id), ('period_month', '=', norm_month)], limit=1)
        if not sheet:
            return {
                'exists': False,
                'sheet_id': 0,
                'period_month': norm_month,
                'state': False,
                'policy_note': policy_note,
                'departments': dept_list,
                'lines': [],
            }

        sorted_lines = sheet.line_ids.sorted(key=lambda ln: self._tp_employee_order_key(ln.employee_id))
        lines_data = []
        for ln in sorted_lines:
            emp = ln.employee_id
            dept = emp.department_id
            has_diff = abs((ln.confirmed_work_units or 0.0) - float(ln.recorded_punch_days or 0)) > 0.01
            lines_data.append({
                'id': ln.id,
                'employee_id': [emp.id, emp.name or ''],
                'employee_code': getattr(emp, 'tp_employee_code', '') or '',
                'employee_name': emp.name or '',
                'department_id': dept.id if dept else 0,
                'department_name': dept.name if dept else 'Chưa khai báo phòng ban',
                'recorded_punch_days': ln.recorded_punch_days,
                'confirmed_work_units': ln.confirmed_work_units,
                'approved_leave_days': ln.approved_leave_days,
                'approved_trip_days': ln.approved_trip_days,
                'has_discrepancy': has_diff,
                'net_pay_status': ln.net_pay_status,
            })

        return {
            'exists': True,
            'sheet_id': sheet.id,
            'period_month': norm_month,
            'state': sheet.state,
            'policy_note': policy_note,
            'departments': dept_list,
            'lines': lines_data,
        }

    @api.model
    def tp_generate_input_reconciliation(self, period_month):
        """Collect real attendance days + approved leave/business trips without inventing salary/tax numbers."""
        _check_payroll_access(self.env)
        company = self.env.company
        norm_month, d_start, d_end = self._tp_parse_period_month(period_month)

        sheet = self.sudo().search([('company_id', '=', company.id), ('period_month', '=', norm_month)], limit=1)
        if not sheet:
            sheet = self.sudo().create({'company_id': company.id, 'period_month': norm_month})
        elif sheet.state == 'inputs_locked':
            raise UserError(_('Bảng đối soát kỳ %(period)s đã khóa đầu vào, không thể tổng hợp đè.', period=norm_month))

        emps = self.env['hr.employee'].sudo().search(
            [('company_id', '=', company.id), ('active', '=', True)],
            order='sequence, id',
        ).sorted(key=self._tp_employee_order_key)
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
                'Hệ thống chỉ đối soát dữ liệu đầu vào (ngày công, nghỉ phép, công tác) và không tự bịa công thức tài chính.',
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
