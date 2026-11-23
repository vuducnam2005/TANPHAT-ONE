"""Attendance correction requests: owner drafts, an admin approves or returns (HR-ATTENDANCE-001 S3).

Every submitted request, from any department, goes to the company's admins as resolved by
tp_admin_delegation: the Original Admin(s) (CHG-20261119-005) and, since CHG-20261119-012, delegated
Full Admins with a live grant in that company (full admin rights except granting/revoking admin
rights). HR managers, department heads and attendance assignments never approve by themselves.
Reason, evidence and review notes are private: only the requester, the admins and HR managers
(read-only, after submission) can read them. Every transition is a backend action that locks the row
first, so a retried or concurrent approval never applies twice.
"""
import hashlib
import json
import math
import re
from datetime import time

from psycopg2.errors import UniqueViolation

from odoo import api, fields, models
from odoo.exceptions import AccessError, ConcurrencyError, UserError, ValidationError

from .attendance_common import (
    DEFAULT_TZ,
    can,
    correction_admins,
    internal,
    is_internal,
    local_to_utc,
    local_today,
    require,
    require_correction_admin,
    utc_to_local,
)
from .attendance_import import ADVISORY_KEY

STATES = [
    ('draft', 'Nháp'), ('submitted', 'Chờ admin duyệt'), ('withdrawn', 'Đã thu hồi'),
    ('approved', 'Đã duyệt'), ('returned', 'Trả lại'), ('cancelled', 'Đã hủy'),
]
CORRECTION_BUS_TYPE = 'tp_hr_attendance/correction_updated'
OWNER_FIELDS = {'work_date', 'requested_in', 'requested_out', 'reason', 'evidence_file', 'evidence_name'}
# Derived on create from the session user's employee; client values are recomputed, never trusted.
DERIVED_FIELDS = {'employee_id', 'company_id', 'department_id', 'employee_code', 'employee_name'}
# Values the web client may echo back for a new record; anything else on a system field is refused.
NEUTRAL = {'state': 'draft', 'name': 'Mới', 'version': 1}
NO_REVIEWER = ('Chưa có admin (admin gốc hoặc admin được ủy quyền đang hiệu lực) khác bạn để nhận duyệt điều chỉnh công '
               'của công ty này. Vui lòng liên hệ quản trị hệ thống.')


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
    _one_create_token = models.UniqueIndex("(employee_id, split_part(create_token, ':', 1)) WHERE create_token IS NOT NULL")

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
    create_token = fields.Char(readonly=True, copy=False, groups='base.group_no_one')
    last_save_token = fields.Char(readonly=True, copy=False, groups='base.group_no_one')
    state = fields.Selection(STATES, 'Trạng thái', default='draft', required=True, readonly=True, index=True, copy=False)
    submitted_at = fields.Datetime('Gửi lúc', readonly=True, copy=False)
    withdrawn_by_id = fields.Many2one('res.users', 'Người thu hồi', readonly=True, copy=False)
    withdrawn_at = fields.Datetime('Thu hồi lúc', readonly=True, copy=False)
    withdraw_reason = fields.Text('Lý do thu hồi', readonly=True, copy=False)
    reviewer_id = fields.Many2one('res.users', 'Người xử lý', readonly=True, copy=False)
    reviewed_at = fields.Datetime('Xử lý lúc', readonly=True, copy=False)
    review_note = fields.Text('Ý kiến người xử lý', readonly=True, copy=False)
    reviewer_user_ids = fields.Many2many('res.users', 'tp_hr_att_correction_reviewer_rel', 'correction_id', 'user_id',
                                         'Admin nhận duyệt', readonly=True, copy=False)
    is_amendment = fields.Boolean('Đính chính kỳ đã chốt', readonly=True, copy=False)
    period_id = fields.Many2one('tp.hr.attendance.period', 'Kỳ đã đính chính', readonly=True, copy=False)
    day_id = fields.Many2one('tp.hr.attendance.day', 'Ngày công tổng hợp', readonly=True, copy=False, ondelete='set null')
    session_id = fields.Many2one('tp.hr.attendance.session', 'Phiên ghi nhận sau duyệt', readonly=True, copy=False, ondelete='set null')
    replaced_times = fields.Char('Giờ gốc được thay', readonly=True, copy=False)
    version = fields.Integer('Phiên bản', default=1, readonly=True, copy=False)

    tp_is_owner = fields.Boolean(compute='_compute_tp_flags')
    tp_can_review = fields.Boolean(compute='_compute_tp_flags')
    tp_can_withdraw = fields.Boolean(compute='_compute_tp_flags')
    tp_period_locked = fields.Boolean('Ngày thuộc kỳ đã chốt', compute='_compute_tp_flags')
    tp_has_reviewer = fields.Boolean(compute='_compute_tp_flags')

    @api.depends('state', 'work_date', 'employee_id', 'department_id', 'company_id')
    @api.depends_context('uid')
    def _compute_tp_flags(self):
        Period = self.env['tp.hr.attendance.period']
        admins = {}
        for record in self:
            company = record.company_id
            if company.id not in admins:
                admins[company.id] = self._tp_reviewers_for(company)
            owner = record.sudo().employee_id.user_id if record.employee_id else self.env.user
            locked = bool(record.work_date and company and Period._tp_is_locked(company.id, record.work_date))
            record.tp_is_owner = owner == self.env.user
            record.tp_period_locked = locked
            # Display hint only: _tp_check_reviewer re-checks the live admin right on every action.
            record.tp_can_review = bool(
                record.state == 'submitted' and owner != self.env.user
                and company in self.env.companies and self.env.user in admins[company.id]
                and (not locked or can(self.env, 'lock', company)))
            record.tp_can_withdraw = bool(owner == self.env.user and record.state == 'submitted' and not locked)
            record.tp_has_reviewer = bool(admins[company.id] - owner)

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
    def _tp_reviewers_for(self, company, department=None, owner=None):
        """Every department's requests go to the company's admins (Original + live delegated); never the requester.

        ``department`` is kept for callers but no longer narrows the list: department heads and
        attendance assignments do not approve. No admin = empty list (no substitute).
        """
        users = self.env['res.users']
        if not company:
            return users
        users = correction_admins(self.env, company)
        return users - owner if owner else users

    def _tp_sync_reviewers(self):
        """Stored recipient list = the company's admins now (Original + live delegated), never the requester."""
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

    def _tp_notify_bus(self, event):
        """Notify owner and company admins via bus without leaking private reason/evidence."""
        Bus = self.env['bus.bus'].sudo()
        for record in self.sudo():
            owner = record.employee_id.user_id
            admins = self._tp_reviewers_for(record.company_id, record.department_id, owner)
            recipients = (owner | admins).filtered(lambda u: u.active)
            payload = {
                'correction_id': record.id,
                'name': record.name or '',
                'state': record.state,
                'work_date': record.work_date.isoformat() if record.work_date else '',
                'event': event,
            }
            for user in recipients:
                Bus._sendone(user, CORRECTION_BUS_TYPE, payload)
            if event == 'approve' and record.work_date:
                group = self.env.ref('base.group_user', raise_if_not_found=False)
                if group:
                    Bus._sendone(group, 'tp_hr_attendance/updated', {
                        'at': fields.Datetime.now().isoformat(),
                        'dates': [record.work_date.isoformat()],
                    })

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
    @api.model
    def tp_save_and_submit(self, vals, correction_id=False, submit=True, operation_token=False):
        """Create or update owner's correction and optionally submit in one atomic transaction."""
        clean_vals = {k: v for k, v in dict(vals or {}).items() if k in OWNER_FIELDS}
        if operation_token and (not isinstance(operation_token, str) or not re.fullmatch(r'[0-9a-f]{16}', operation_token)):
            raise ValidationError(self.env._('Mã thao tác lưu không hợp lệ.'))
        for key in ('requested_in', 'requested_out'):
            if correction_id and key not in clean_vals:
                continue
            value = clean_vals.get(key)
            if isinstance(value, bool) or float_clock(value) is None:
                raise ValidationError(self.env._('Nhập đủ giờ vào và giờ ra hợp lệ (00:00–23:59).'))
        operation_key = False
        if operation_token:
            contents = json.dumps([bool(submit), clean_vals], sort_keys=True, default=str)
            operation_key = f'{operation_token}:{hashlib.sha256(contents.encode()).hexdigest()}'
        try:
            with self.env.cr.savepoint():
                if correction_id:
                    record = self.browse(int(correction_id)).exists()
                    if not record:
                        raise UserError(self.env._('Không tìm thấy đề nghị điều chỉnh công.'))
                    record.check_access('read')
                    record._tp_check_owner()
                    record._tp_lock_rows()
                    previous = record.sudo().last_save_token if operation_token else False
                    if not previous or not previous.startswith(f'{operation_token}:'):
                        previous = False
                        record.write(clean_vals)
                        if operation_key:
                            internal(record).write({'last_save_token': operation_key})
                else:
                    record = self.browse()
                    if operation_token:
                        employee = self._tp_own_employee()
                        record = self.sudo().search([
                            ('employee_id', '=', employee.id), ('create_token', '=like', f'{operation_token}:%'),
                        ], limit=1).with_env(self.env)
                    previous = False
                    if record:
                        record.check_access('read')
                        previous = record.sudo().create_token
                    else:
                        record = self.create(clean_vals)
                        if operation_key:
                            internal(record).write({'create_token': operation_key})
                if previous and previous != operation_key:
                    raise UserError(self.env._('Thao tác trước đã được ghi nhận. Tải lại để xem phiếu trước khi sửa hoặc gửi duyệt.'))
                if submit and not previous:
                    record.action_submit()
        except UniqueViolation as error:
            if error.diag.constraint_name == self._one_create_token.full_name(self):
                # Start with a fresh snapshot when the same creation token commits concurrently.
                message = 'Concurrent correction creation'
                raise ConcurrencyError(message) from error
            raise
        return {
            'id': record.id,
            'name': record.name,
            'state': record.state,
            'work_date': record.work_date.isoformat() if record.work_date else '',
        }

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
                raise UserError(self.env._('Ngày này đã có phiếu đang chờ duyệt; chờ kết quả hoặc thu hồi phiếu đó.'))
            day = self.env['tp.hr.attendance.day'].sudo().search(
                [('employee_id', '=', record.employee_id.id), ('work_date', '=', record.work_date)], limit=1)
            internal(record).write({
                'state': 'submitted', 'submitted_at': fields.Datetime.now(), 'version': record.version + 1,
                'current_in': day.in_time or False, 'current_out': day.out_time or False, 'day_id': day.id or False,
                'reviewer_user_ids': [(6, 0, reviewers.ids)], 'reviewer_id': False, 'reviewed_at': False, 'review_note': False,
            })
            record._tp_log('correction_submit', reviewers=reviewers.ids)
            record._tp_notify_bus('submit')
        return True

    def action_withdraw(self, reason=None):
        """Owner withdraws a submitted request before admin review; never allowed if approved or period locked."""
        self.check_access('read')
        self._tp_check_owner()
        self._tp_lock_rows()
        Period = self.env['tp.hr.attendance.period'].sudo()
        clean_reason = (reason or '').strip()
        for record in self:
            if record.state != 'submitted':
                raise UserError(self.env._('Chỉ thu hồi được phiếu %(name)s khi đang chờ admin duyệt.', name=record.name))
            if record.work_date and Period._tp_is_locked(record.company_id.id, record.work_date):
                raise UserError(self.env._('Không thể thu hồi đề nghị vì kỳ công đã chốt.'))
            internal(record).write({
                'state': 'withdrawn',
                'withdrawn_by_id': self.env.user.id,
                'withdrawn_at': fields.Datetime.now(),
                'withdraw_reason': clean_reason or False,
                'version': record.version + 1,
            })
            record._tp_log('correction_withdraw')
            record._tp_notify_bus('withdraw')
        return True

    def action_reopen_draft(self):
        """Owner reopens a withdrawn request back to draft for editing and resubmission."""
        self.check_access('read')
        self._tp_check_owner()
        self._tp_lock_rows()
        for record in self:
            if record.state != 'withdrawn':
                raise UserError(self.env._('Chỉ mở lại thành nháp được phiếu đã thu hồi.'))
            internal(record).write({'state': 'draft', 'version': record.version + 1})
            record._tp_log('correction_reopen')
            record._tp_notify_bus('reopen')
        return True

    def action_cancel(self):
        self.check_access('read')
        self._tp_check_owner()
        self._tp_lock_rows()
        for record in self:
            if record.state not in ('draft', 'returned'):
                raise UserError(self.env._('Phiếu %(name)s đang chờ duyệt hoặc đã xử lý; dùng Thu hồi đề nghị nếu muốn rút lại.', name=record.name))
            internal(record).write({'state': 'cancelled', 'version': record.version + 1})
            record._tp_log('correction_cancel')
            record._tp_notify_bus('cancel')
        return True

    def _tp_check_reviewer(self):
        self.ensure_one()
        self.check_access('read')
        if self.sudo().employee_id.user_id == self.env.user:
            raise AccessError(self.env._('Không tự duyệt hoặc trả đề nghị của chính mình.'))
        require_correction_admin(self.env, self.company_id)

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
        self._tp_notify_bus('return')
        return True

    def action_approve(self, note=None):
        """Apply the requested in/out as the day's session, keep the replaced punches inactive, log everything.

        Runs in one transaction behind the request row lock and the company import lock; a second
        approval (retry, double click, other reviewer) finds the state changed and is refused. Any
        error rolls the whole transaction back, so the request never shows Approved without the
        session/day rows it produced.
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
        self._tp_notify_bus('approve')
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

    def action_open_withdraw(self):
        self.ensure_one()
        self._tp_check_owner()
        return {
            'type': 'ir.actions.act_window', 'name': self.env._('Thu hồi đề nghị'),
            'res_model': 'tp.hr.attendance.withdraw.wizard', 'view_mode': 'form',
            'views': [[False, 'form']], 'target': 'new',
            'context': {'default_correction_id': self.id},
        }


class AttendanceWithdrawWizard(models.TransientModel):
    _name = 'tp.hr.attendance.withdraw.wizard'
    _description = 'Thu hồi đề nghị điều chỉnh công'

    correction_id = fields.Many2one('tp.hr.attendance.correction', 'Phiếu', required=True, readonly=True, ondelete='cascade')
    reason = fields.Text('Lý do thu hồi (không bắt buộc)')

    def action_confirm(self):
        self.ensure_one()
        self.correction_id.action_withdraw(reason=self.reason)
        return {
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': {'type': 'success', 'message': self.env._('Đã thu hồi'), 'sticky': False,
                       'next': {'type': 'ir.actions.act_window_close'}},
        }


class AttendanceReviewWizard(models.TransientModel):
    _name = 'tp.hr.attendance.review.wizard'
    _description = 'Duyệt / trả đề nghị điều chỉnh công'

    correction_id = fields.Many2one('tp.hr.attendance.correction', 'Phiếu', required=True, readonly=True, ondelete='cascade')
    decision = fields.Selection([('approve', 'Duyệt'), ('return', 'Trả lại')], 'Quyết định', required=True, readonly=True)
    note = fields.Text('Ý kiến / lý do')
    period_locked = fields.Boolean(related='correction_id.tp_period_locked')
    employee_name = fields.Char(related='correction_id.employee_name', string='Người đề nghị')
    work_date = fields.Date(related='correction_id.work_date', string='Ngày công')
    current_in = fields.Char(related='correction_id.current_in', string='Giờ vào đang ghi')
    current_out = fields.Char(related='correction_id.current_out', string='Giờ ra đang ghi')
    requested_in = fields.Float(related='correction_id.requested_in', string='Giờ vào đề nghị')
    requested_out = fields.Float(related='correction_id.requested_out', string='Giờ ra đề nghị')

    def action_confirm(self):
        """Run the existing transition; the notice reaches the browser only after the transaction commits."""
        self.ensure_one()
        request = self.correction_id
        if self.decision == 'approve':
            request.action_approve(note=self.note)
            message = self.env._('Đã duyệt %(name)s và lưu giờ vào/ra vào bảng công.', name=request.name)
        else:
            request.action_return(note=self.note)
            message = self.env._('Đã trả lại %(name)s cho người đề nghị bổ sung.', name=request.name)
        return {
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': {'type': 'success', 'message': message, 'sticky': False, 'next': {'type': 'ir.actions.act_window_close'}},
        }


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
