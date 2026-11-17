"""Attendance correction requests: owner drafts, assigned reviewer approves or returns (HR-ATTENDANCE-001 S3).

Reason, evidence and review notes are private: only the requester, the reviewers assigned to the
request's company/department and HR managers (after submission) can read them. Every transition is a
backend action that locks the row first, so a retried or concurrent approval never applies twice.
"""
import math
from datetime import time

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .attendance_common import (
    DEFAULT_TZ,
    can,
    internal,
    is_internal,
    local_to_utc,
    local_today,
    require,
    utc_to_local,
)
from .attendance_import import ADVISORY_KEY

STATES = [
    ('draft', 'Nháp'), ('submitted', 'Chờ duyệt'), ('approved', 'Đã duyệt'),
    ('returned', 'Trả lại'), ('cancelled', 'Đã hủy'),
]
OWNER_FIELDS = {'work_date', 'requested_in', 'requested_out', 'reason', 'evidence_file', 'evidence_name'}
# Derived on create from the session user's employee; client values are recomputed, never trusted.
DERIVED_FIELDS = {'employee_id', 'company_id', 'department_id', 'employee_code', 'employee_name'}
# Values the web client may echo back for a new record; anything else on a system field is refused.
NEUTRAL = {'state': 'draft', 'name': 'Mới', 'version': 1}
NO_REVIEWER = ('Chưa có người được phân công duyệt điều chỉnh công cho phòng của bạn. Phiếu vẫn được lưu nháp; '
               'HR cấu hình tại Nhân sự → Cấu hình → Phân công xử lý công (đánh dấu "Duyệt / trả điều chỉnh").')


def float_clock(value):
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 or value >= 24:
        return None
    minutes = round((value or 0.0) * 60)
    hours, minutes = divmod(minutes, 60)
    if not 0 <= hours < 24:
        return None
    return time(hours, minutes)


def clock_label(value):
    clock = float_clock(value)
    return clock.strftime('%H:%M') if clock else ''


def _neutral(key, value):
    if not value:
        return True
    if isinstance(value, list) and all(isinstance(cmd, (list, tuple)) and cmd and cmd[0] in (5, 6) and not cmd[-1] for cmd in value):
        return True
    return value == NEUTRAL.get(key)


class AttendanceCorrection(models.Model):
    _name = 'tp.hr.attendance.correction'
    _description = 'Đề nghị điều chỉnh công'
    _order = 'id desc'
    _check_company_auto = True
    _one_pending_day = models.UniqueIndex("(employee_id, work_date) WHERE state = 'submitted'", 'Ngày này đã có đề nghị chờ duyệt.')

    name = fields.Char('Mã phiếu', readonly=True, copy=False, default='Mới')
    employee_id = fields.Many2one('hr.employee', 'Nhân viên', required=True, readonly=True, index=True, ondelete='restrict',
                                  default=lambda self: self._tp_own_employee())
    company_id = fields.Many2one('res.company', 'Công ty', required=True, readonly=True, index=True,
                                 default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', 'Phòng', readonly=True, index=True,
                                    default=lambda self: self._tp_own_employee().department_id)
    employee_code = fields.Char('Mã TP', readonly=True, default=lambda self: self._tp_own_employee().tp_employee_code)
    employee_name = fields.Char('Người đề nghị', readonly=True, default=lambda self: self._tp_own_employee().name)
    work_date = fields.Date('Ngày công', required=True, index=True)
    requested_in = fields.Float('Giờ vào đúng', required=True)
    requested_out = fields.Float('Giờ ra đúng', required=True)
    current_in = fields.Char('Giờ vào đang ghi', readonly=True, copy=False)
    current_out = fields.Char('Giờ ra đang ghi', readonly=True, copy=False)
    reason = fields.Text('Giải trình', copy=False)
    evidence_file = fields.Binary('Minh chứng', attachment=True, copy=False)
    evidence_name = fields.Char('Tên tệp minh chứng', copy=False)
    state = fields.Selection(STATES, 'Trạng thái', default='draft', required=True, readonly=True, index=True, copy=False)
    submitted_at = fields.Datetime('Gửi lúc', readonly=True, copy=False)
    reviewer_id = fields.Many2one('res.users', 'Người xử lý', readonly=True, copy=False)
    reviewed_at = fields.Datetime('Xử lý lúc', readonly=True, copy=False)
    review_note = fields.Text('Ý kiến người xử lý', readonly=True, copy=False)
    reviewer_user_ids = fields.Many2many('res.users', 'tp_hr_att_correction_reviewer_rel', 'correction_id', 'user_id',
                                         'Người được phân công duyệt', readonly=True, copy=False)
    is_amendment = fields.Boolean('Đính chính kỳ đã chốt', readonly=True, copy=False)
    period_id = fields.Many2one('tp.hr.attendance.period', 'Kỳ đã đính chính', readonly=True, copy=False)
    day_id = fields.Many2one('tp.hr.attendance.day', 'Ngày công tổng hợp', readonly=True, copy=False, ondelete='set null')
    session_id = fields.Many2one('tp.hr.attendance.session', 'Phiên ghi nhận sau duyệt', readonly=True, copy=False, ondelete='set null')
    replaced_times = fields.Char('Giờ gốc được thay', readonly=True, copy=False)
    version = fields.Integer('Phiên bản', default=1, readonly=True, copy=False)

    tp_is_owner = fields.Boolean(compute='_compute_tp_flags')
    tp_can_review = fields.Boolean(compute='_compute_tp_flags')
    tp_period_locked = fields.Boolean('Ngày thuộc kỳ đã chốt', compute='_compute_tp_flags')
    tp_has_reviewer = fields.Boolean(compute='_compute_tp_flags')

    @api.depends('state', 'work_date', 'employee_id', 'department_id', 'company_id')
    @api.depends_context('uid')
    def _compute_tp_flags(self):
        Period = self.env['tp.hr.attendance.period']
        for record in self:
            owner = record.sudo().employee_id.user_id if record.employee_id else self.env.user
            locked = bool(record.work_date and record.company_id and Period._tp_is_locked(record.company_id.id, record.work_date))
            record.tp_is_owner = owner == self.env.user
            record.tp_period_locked = locked
            record.tp_can_review = bool(
                record.state == 'submitted' and owner != self.env.user
                and can(self.env, 'review', record.company_id, record.department_id)
                and (not locked or can(self.env, 'lock', record.company_id)))
            record.tp_has_reviewer = bool(self._tp_reviewers_for(record.company_id, record.department_id, owner))

    @api.depends('name', 'employee_name', 'work_date')
    def _compute_display_name(self):
        for record in self:
            day = record.work_date.strftime('%d/%m/%Y') if record.work_date else ''
            record.display_name = ' · '.join(part for part in (record.name, record.employee_name, day) if part)

    # ------------------------------------------------------------ helpers
    @api.model
    def _tp_own_employee(self, company=None):
        company = company or self.env.company
        if company not in self.env.companies:
            raise AccessError(self.env._('Công ty nằm ngoài phiên đăng nhập hiện tại.'))
        return self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid), ('company_id', '=', company.id)], limit=1)

    @api.model
    def _tp_reviewers_for(self, company, department, owner=None):
        """Reviewers come only from active assignments with review rights covering the department."""
        users = self.env['res.users']
        if not company:
            return users
        for assignment in self.env['tp.hr.attendance.assignment'].sudo().search(
                [('company_id', '=', company.id), ('can_review', '=', True), ('active', '=', True)]):
            if not assignment.department_ids or (department and department in assignment.department_ids):
                if assignment.user_id.active and company in assignment.user_id.company_ids:
                    users |= assignment.user_id
        return users - owner if owner else users

    def _tp_sync_reviewers(self):
        """Stored reviewer list (read rule) = reviewers assigned now + whoever already handled the request."""
        for record in internal(self):
            if record.state == 'draft':
                wanted = record.env['res.users']
            else:
                wanted = self._tp_reviewers_for(record.company_id, record.department_id, record.employee_id.user_id)
            if set(wanted.ids) != set(record.reviewer_user_ids.ids):
                record.write({'reviewer_user_ids': [(6, 0, wanted.ids)]})

    @api.model
    def _tp_refresh_reviewers(self, companies=None):
        domain = [('state', '!=', 'draft')]
        if companies:
            domain.append(('company_id', 'in', companies.ids))
        internal(self).search(domain)._tp_sync_reviewers()

    def _tp_lock_rows(self):
        if self.ids:
            self.env.cr.execute('SELECT id FROM tp_hr_attendance_correction WHERE id IN %s FOR UPDATE', [tuple(self.ids)])
        self.invalidate_recordset()

    def _tp_check_owner(self):
        for record in self:
            if record.sudo().employee_id.user_id != self.env.user:
                raise AccessError(self.env._('Chỉ người đề nghị được thao tác trên phiếu của mình.'))

    def _tp_validate(self):
        today = local_today(DEFAULT_TZ)
        for record in self:
            start, end = float_clock(record.requested_in), float_clock(record.requested_out)
            if start is None or end is None:
                raise ValidationError(self.env._('Giờ vào/ra phải nằm trong ngày (00:00–23:59).'))
            if end <= start:
                raise ValidationError(self.env._('Giờ ra phải sau giờ vào trong cùng ngày công.'))
            if record.work_date and record.work_date > today:
                raise ValidationError(self.env._('Không đề nghị điều chỉnh cho ngày chưa đến.'))

    def _tp_log(self, action, **detail):
        # Times and actors only: the reason, evidence and review note stay on the private request.
        Log = self.env['tp.hr.attendance.log']
        for record in self:
            Log._tp_log(record, action, dict({
                'request': record.name, 'work_date': record.work_date, 'requested_in': clock_label(record.requested_in),
                'requested_out': clock_label(record.requested_out), 'state': record.state, 'version': record.version}, **detail))

    # --------------------------------------------------------------- CRUD
    @api.model_create_multi
    def create(self, vals_list):
        if not is_internal(self):
            for vals in vals_list:
                for key in set(vals) - OWNER_FIELDS - DERIVED_FIELDS:
                    if not _neutral(key, vals.pop(key)):
                        raise AccessError(self.env._('Trạng thái và kết quả duyệt chỉ đổi qua nút Gửi duyệt / Duyệt / Trả lại / Hủy.'))
                company = self.env['res.company'].browse(vals['company_id']) if vals.get('company_id') else self.env.company
                employee = self._tp_own_employee(company)
                if not employee:
                    raise UserError(self.env._('Tài khoản chưa gắn hồ sơ nhân viên trong công ty này; cần admin/HR gắn hồ sơ, không tự ghép theo tên.'))
                if vals.get('employee_id') and vals['employee_id'] != employee.id:
                    raise AccessError(self.env._('Chỉ được tạo đề nghị điều chỉnh công cho chính mình.'))
                vals.update(employee_id=employee.id, company_id=employee.company_id.id, department_id=employee.department_id.id,
                            employee_code=employee.tp_employee_code, employee_name=employee.name)
        records = super().create(vals_list)
        records._tp_validate()
        for record in records:
            internal(record).write({'name': f'ĐC{record.id:05d}'})
        records._tp_log('correction_create')
        return records

    def write(self, vals):
        if is_internal(self):
            return super().write(vals)
        self.check_access('write')
        self._tp_lock_rows()
        if set(vals) - OWNER_FIELDS:
            raise AccessError(self.env._('Trạng thái và kết quả duyệt chỉ đổi qua nút Gửi duyệt / Duyệt / Trả lại / Hủy.'))
        self._tp_check_owner()
        if any(record.state not in ('draft', 'returned') for record in self):
            raise UserError(self.env._('Phiếu đã gửi hoặc đã xử lý nên không sửa được; hủy phiếu và tạo phiếu mới nếu cần.'))
        result = super().write(vals)
        self._tp_validate()
        return result

    def unlink(self):
        self.check_access('unlink')
        self._tp_lock_rows()
        self._tp_check_owner()
        if any(record.state != 'draft' for record in self):
            raise UserError(self.env._('Chỉ xóa được phiếu nháp; phiếu đã gửi giữ lịch sử, dùng Hủy phiếu.'))
        self._tp_log('correction_unlink')
        return super().unlink()

    def copy(self, default=None):
        raise UserError(self.env._('Tạo phiếu mới thay vì nhân bản phiếu điều chỉnh.'))

    def export_data(self, fields_to_export):
        # Reviewers and HR handle requests on screen; exports stay with the requester's own rows.
        if any(record.sudo().employee_id.user_id != self.env.user for record in self):
            raise AccessError(self.env._('Chỉ được xuất đề nghị điều chỉnh của chính mình.'))
        return super().export_data(fields_to_export)

    # -------------------------------------------------------- transitions
    def action_submit(self):
        self.check_access('read')
        self._tp_check_owner()
        self._tp_lock_rows()
        for record in self:
            self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [ADVISORY_KEY, record.company_id.id])
            if record.state not in ('draft', 'returned'):
                raise UserError(self.env._('Phiếu %(name)s đã gửi hoặc đã xử lý.', name=record.name))
            record._tp_validate()
            if not (record.reason or '').strip():
                raise UserError(self.env._('Nhập giải trình trước khi gửi duyệt.'))
            reviewers = self._tp_reviewers_for(record.company_id, record.department_id, self.env.user)
            if not reviewers:
                raise UserError(self.env._(NO_REVIEWER))
            if self.sudo().search_count([('id', '!=', record.id), ('employee_id', '=', record.employee_id.id),
                                         ('work_date', '=', record.work_date), ('state', '=', 'submitted')]):
                raise UserError(self.env._('Ngày này đã có phiếu đang chờ duyệt; chờ kết quả hoặc hủy phiếu đó.'))
            day = self.env['tp.hr.attendance.day'].sudo().search(
                [('employee_id', '=', record.employee_id.id), ('work_date', '=', record.work_date)], limit=1)
            internal(record).write({
                'state': 'submitted', 'submitted_at': fields.Datetime.now(), 'version': record.version + 1,
                'current_in': day.in_time or False, 'current_out': day.out_time or False, 'day_id': day.id or False,
                'reviewer_user_ids': [(6, 0, reviewers.ids)], 'reviewer_id': False, 'reviewed_at': False, 'review_note': False,
            })
            record._tp_log('correction_submit', reviewers=reviewers.ids)
        return True

    def action_cancel(self):
        self.check_access('read')
        self._tp_check_owner()
        self._tp_lock_rows()
        for record in self:
            if record.state not in ('draft', 'submitted', 'returned'):
                raise UserError(self.env._('Phiếu %(name)s đã xử lý xong, không hủy được.', name=record.name))
            internal(record).write({'state': 'cancelled', 'version': record.version + 1})
            record._tp_log('correction_cancel')
        return True

    def _tp_check_reviewer(self):
        self.ensure_one()
        self.check_access('read')
        if self.sudo().employee_id.user_id == self.env.user:
            raise AccessError(self.env._('Không tự duyệt hoặc trả đề nghị của chính mình.'))
        require(self.env, 'review', self.company_id, self.department_id)

    def action_return(self, note=None):
        self.ensure_one()
        self.check_access('read')
        self._tp_lock_rows()
        if self.state != 'submitted':
            raise UserError(self.env._('Phiếu không còn chờ duyệt (đã được xử lý trước đó).'))
        self._tp_check_reviewer()
        if not (note or '').strip():
            raise UserError(self.env._('Nhập lý do trả lại để người đề nghị bổ sung.'))
        internal(self).write({'state': 'returned', 'reviewer_id': self.env.user.id, 'reviewed_at': fields.Datetime.now(),
                              'review_note': note.strip(), 'version': self.version + 1})
        self._tp_sync_reviewers()
        self._tp_log('correction_return')
        return True

    def action_approve(self, note=None):
        """Apply the requested in/out as the day's session, keep the replaced punches inactive, log everything.

        Runs in one transaction behind the request row lock and the company import lock; a second
        approval (retry, double click, other reviewer) finds the state changed and is refused.
        """
        self.ensure_one()
        self.check_access('read')
        self._tp_lock_rows()
        if self.state != 'submitted':
            raise UserError(self.env._('Phiếu không còn chờ duyệt (đã được xử lý trước đó).'))
        self._tp_check_reviewer()
        self._tp_validate()
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [ADVISORY_KEY, self.company_id.id])
        period = self.env['tp.hr.attendance.period'].sudo().search([
            ('company_id', '=', self.company_id.id), ('state', '=', 'locked'),
            ('date_from', '<=', self.work_date), ('date_to', '>=', self.work_date)], limit=1)
        note = (note or '').strip()
        if period:
            require(self.env, 'lock', self.company_id)
            if not note:
                raise UserError(self.env._('Ngày thuộc kỳ đã chốt: nhập lý do đính chính trước khi duyệt.'))
        check_in = local_to_utc(self.work_date, float_clock(self.requested_in), DEFAULT_TZ)
        check_out = local_to_utc(self.work_date, float_clock(self.requested_out), DEFAULT_TZ)
        Session = internal(self.env['tp.hr.attendance.session']).with_context(active_test=False)
        existing = Session.search([('employee_id', '=', self.employee_id.id), ('work_date', '=', self.work_date)], order='check_in')
        same = existing.filtered(lambda session: session.check_in == check_in and session.check_out == check_out)[:1]
        replaced = existing.filtered(lambda session: session.active and session != same)
        sources = dict(Session._fields['source'].selection)
        original = [{'in': utc_to_local(session.check_in).strftime('%H:%M'), 'out': utc_to_local(session.check_out).strftime('%H:%M'),
                     'source': session.source, 'session': session.id} for session in replaced]
        if replaced:
            replaced.write({'active': False, 'superseded_by_id': self.id})
        if same:
            if not same.active:
                same.write({'active': True, 'superseded_by_id': False})
            session = same
        else:
            session = Session.create({
                'employee_id': self.employee_id.id, 'company_id': self.company_id.id, 'work_date': self.work_date,
                'check_in': check_in, 'check_out': check_out, 'source': 'correction', 'correction_id': self.id,
            })
        issues = self.env['tp.hr.attendance.line'].sudo().search([
            ('employee_id', '=', self.employee_id.id), ('work_date', '=', self.work_date), ('issue_open', '=', True)])
        internal(issues).write({'issue_open': False,
                                'resolution': self.env._('Đã xử lý theo đề nghị điều chỉnh %(name)s.', name=self.name)})
        day = self.env['tp.hr.attendance.day']._tp_refresh(self.company_id, {(self.employee_id.id, self.work_date)}, allow_locked=bool(period))
        vals = {
            'state': 'approved', 'reviewer_id': self.env.user.id, 'reviewed_at': fields.Datetime.now(), 'review_note': note or False,
            'version': self.version + 1, 'session_id': session.id, 'day_id': day[:1].id or False,
            'replaced_times': '; '.join(f"{item['in']}–{item['out']} ({sources.get(item['source'], item['source'])})" for item in original) or False,
        }
        if period:
            internal(period).write({'version': period.version + 1})
            vals.update(is_amendment=True, period_id=period.id)
            self.env['tp.hr.attendance.log']._tp_log(period, 'period_amend', {
                'request': self.name, 'employee_id': self.employee_id.id, 'work_date': self.work_date,
                'version': period.version, 'original': original,
                'new': {'in': clock_label(self.requested_in), 'out': clock_label(self.requested_out)}})
        internal(self).write(vals)
        self._tp_sync_reviewers()
        self._tp_log('correction_approve', original=original, issues_closed=len(issues), amendment=bool(period))
        return True

    # ------------------------------------------------------------ dialogs
    def _tp_wizard(self, decision):
        self.ensure_one()
        self._tp_check_reviewer()
        title = self.env._('Duyệt đề nghị') if decision == 'approve' else self.env._('Trả lại đề nghị')
        return {
            'type': 'ir.actions.act_window', 'name': title, 'res_model': 'tp.hr.attendance.review.wizard', 'view_mode': 'form',
            'views': [[False, 'form']], 'target': 'new',
            'context': {'default_correction_id': self.id, 'default_decision': decision},
        }

    def action_open_approve(self):
        return self._tp_wizard('approve')

    def action_open_return(self):
        return self._tp_wizard('return')


class AttendanceReviewWizard(models.TransientModel):
    _name = 'tp.hr.attendance.review.wizard'
    _description = 'Duyệt / trả đề nghị điều chỉnh công'

    correction_id = fields.Many2one('tp.hr.attendance.correction', 'Phiếu', required=True, readonly=True, ondelete='cascade')
    decision = fields.Selection([('approve', 'Duyệt'), ('return', 'Trả lại')], 'Quyết định', required=True, readonly=True)
    note = fields.Text('Ý kiến / lý do')
    period_locked = fields.Boolean(related='correction_id.tp_period_locked')

    def action_confirm(self):
        self.ensure_one()
        if self.decision == 'approve':
            self.correction_id.action_approve(note=self.note)
        else:
            self.correction_id.action_return(note=self.note)
        return {'type': 'ir.actions.act_window_close'}


class AttendancePeriodWizard(models.TransientModel):
    _name = 'tp.hr.attendance.period.wizard'
    _description = 'Chốt / mở kỳ công'

    period_id = fields.Many2one('tp.hr.attendance.period', 'Kỳ công', required=True, readonly=True, ondelete='cascade')
    operation = fields.Selection([('lock', 'Chốt kỳ'), ('unlock', 'Mở lại kỳ')], 'Thao tác', required=True, readonly=True)
    reason = fields.Text('Lý do / ghi chú')
    day_count = fields.Integer(related='period_id.day_count')
    ok_count = fields.Integer(related='period_id.ok_count')
    missing_count = fields.Integer(related='period_id.missing_count')
    review_count = fields.Integer(related='period_id.review_count')
    pending_count = fields.Integer(related='period_id.pending_count')

    def action_confirm(self):
        self.ensure_one()
        if self.operation == 'lock':
            self.period_id._tp_lock(self.reason)
        else:
            self.period_id._tp_unlock(self.reason)
        return {'type': 'ir.actions.act_window_close'}


class AttendanceEvidence(models.Model):
    _inherit = 'ir.attachment'

    def _tp_check_evidence_edit(self, request_ids):
        requests = self.env['tp.hr.attendance.correction'].browse(request_ids)
        requests.check_access('read')
        requests._tp_check_owner()
        requests._tp_lock_rows()
        if any(record.state not in ('draft', 'returned') for record in requests):
            raise AccessError(self.env._('Minh chứng chỉ sửa khi phiếu nháp hoặc được trả lại.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('res_model') == 'tp.hr.attendance.correction' and (vals.get('public') or vals.get('access_token')):
                raise AccessError(self.env._('Minh chứng điều chỉnh công chỉ xem theo quyền phiếu, không chia sẻ công khai.'))
            if vals.get('res_model') == 'tp.hr.attendance.correction' and vals.get('res_id'):
                self._tp_check_evidence_edit([vals['res_id']])
        return super().create(vals_list)

    def write(self, vals):
        protected = self.sudo().filtered(lambda a: a.res_model == 'tp.hr.attendance.correction')
        if protected and (vals.get('public') or vals.get('access_token') or set(vals) & {'res_model', 'res_id', 'res_field'}):
            raise AccessError(self.env._('Không công khai hoặc chuyển minh chứng điều chỉnh sang nguồn khác.'))
        if protected:
            self._tp_check_evidence_edit(protected.mapped('res_id'))
        if vals.get('res_model') == 'tp.hr.attendance.correction' and vals.get('res_id'):
            self._tp_check_evidence_edit([vals['res_id']])
        if vals.get('res_model') == 'tp.hr.attendance.correction' and (vals.get('public') or vals.get('access_token') or any(a.public or a.access_token for a in self.sudo())):
            raise AccessError(self.env._('Minh chứng điều chỉnh công không được công khai hoặc có token.'))
        return super().write(vals)

    def unlink(self):
        protected = self.sudo().filtered(lambda a: a.res_model == 'tp.hr.attendance.correction')
        if protected:
            self._tp_check_evidence_edit(protected.mapped('res_id'))
        return super().unlink()

    def generate_access_token(self):
        if any(a.res_model == 'tp.hr.attendance.correction' for a in self.sudo()):
            raise AccessError(self.env._('Minh chứng điều chỉnh công không được tạo token chia sẻ.'))
        return super().generate_access_token()
