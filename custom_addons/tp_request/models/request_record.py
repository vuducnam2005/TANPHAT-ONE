# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Core request record, frozen sequential approval steps, attachment guard and UI RPCs."""
from datetime import datetime, timedelta
from markupsafe import Markup, escape

from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Domain

from .request_common import (
    APPROVAL_POLICIES,
    APPROVAL_STATES,
    APPROVER_RULES,
    BRIDGE_INTERNAL,
    BRIDGE_KEY,
    DEFAULT_TZ,
    EXECUTION_STATES,
    EXECUTOR_MODES,
    HANDLER_KINDS,
    INTERNAL,
    IT_CATEGORIES,
    IT_IMPACTS,
    OLD_EQUIP_CONDITIONS,
    PRIORITIES,
    STEP_STATES,
    SUBMITTER_SCOPES,
    active_internal_users,
    add_working_hours,
    fold_text,
    format_date_vn,
    format_dt_local,
    internal,
    is_bridge,
    is_internal,
    is_live_admin_user,
    is_request_manager,
    lock_rows,
    require_request_manager,
)

OWNER_EDITABLE_FIELDS = frozenset({
    'title',
    'description',
    'priority',
    'needed_date',
    'project_id',
    'follower_user_ids',
    'equipment_id',
    'equipment_category_id',
    'equipment_quantity',
    'equipment_desired_spec',
    'equipment_issue_detail',
    'it_category',
    'it_device_id',
    'it_urgency_impact',
    'att_work_date',
    'att_requested_in',
    'att_requested_out',
    'attachment_ids',
})

SYSTEM_GUARDED_FIELDS = frozenset({
    'code',
    'requester_user_id',
    'requester_employee_id',
    'department_id',
    'company_id',
    'requester_name_snap',
    'requester_code_snap',
    'department_name_snap',
    'equipment_name_snap',
    'approval_state',
    'execution_state',
    'version',
    'type_config_version',
    'submitted_at',
    'approved_at',
    'due_at',
    'current_step_id',
    'current_approver_ids',
    'all_approver_ids',
    'executor_user_ids',
    'assigned_executor_id',
    'execution_due_at',
    'execution_started_at',
    'execution_done_at',
    'execution_result',
    'execution_cancel_reason',
    'return_reason',
    'reject_reason',
    'withdraw_reason',
    'attendance_correction_id',
    'fulfilled_equipment_id',
    'old_equipment_condition',
    'equipment_move_ids',
    'equipment_repair_id',
    'equipment_proposal_id',
    'step_ids',
    'history_ids',
    'overdue_notified_at',
})

STATE_LABELS = dict(APPROVAL_STATES)
EXEC_LABELS = dict(EXECUTION_STATES)
PRIORITY_LABELS = dict(PRIORITIES)
HANDLER_LABELS = dict(HANDLER_KINDS)


def _clock_str(val):
    if val is None or val is False:
        return ''
    try:
        total_min = round(float(val) * 60)
        h, m = divmod(total_min, 60)
        if 0 <= h < 24:
            return f'{h:02d}:{m:02d}'
    except (TypeError, ValueError):
        pass
    return ''


def _parse_clock_to_float(val):
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)
    text = str(val or '').strip()
    if not text:
        return None
    if ':' in text:
        parts = text.split(':')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            h, m = int(parts[0]), int(parts[1])
            if 0 <= h < 24 and 0 <= m < 60:
                return h + m / 60.0
        return None
    try:
        num = float(text)
        return num if 0 <= num < 24 else None
    except ValueError:
        return None


class TpRequest(models.Model):
    _name = 'tp.request'
    _description = 'Hồ sơ Yêu cầu phê duyệt'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'submitted_at desc, id desc'
    _rec_name = 'code'
    _check_company_auto = True

    # ------------------------------------------------------------------ Identity
    code = fields.Char(string='Mã đề nghị', readonly=True, copy=False, index=True, default='Mới')
    title = fields.Char(string='Tiêu đề', required=True, index=True)
    type_id = fields.Many2one('tp.request.type', string='Loại đề nghị', required=True, ondelete='restrict', index=True)
    handler_kind = fields.Selection(related='type_id.handler_kind', store=True, index=True, string='Nhóm nghiệp vụ')
    type_config_version = fields.Integer(string='Phiên bản cấu hình áp dụng', default=1, readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, readonly=True, index=True,
                                 default=lambda self: self.env.company)

    # ------------------------------------------------------------------ Requester & snapshots
    requester_user_id = fields.Many2one('res.users', string='Người gửi', required=True, readonly=True, index=True,
                                        default=lambda self: self.env.user, ondelete='restrict')
    requester_employee_id = fields.Many2one('hr.employee', string='Hồ sơ nhân viên', readonly=True, index=True,
                                            ondelete='restrict')
    department_id = fields.Many2one('hr.department', string='Phòng ban', readonly=True, index=True,
                                    ondelete='set null')
    requester_name_snap = fields.Char(string='Người gửi (lúc gửi)', readonly=True, copy=False)
    requester_code_snap = fields.Char(string='Mã nhân viên (lúc gửi)', readonly=True, copy=False)
    department_name_snap = fields.Char(string='Phòng ban (lúc gửi)', readonly=True, copy=False)

    # ------------------------------------------------------------------ General content
    description = fields.Text(string='Nội dung / lý do')
    priority = fields.Selection(PRIORITIES, string='Độ ưu tiên', required=True, default='normal', index=True)
    needed_date = fields.Date(string='Ngày cần đáp ứng')
    project_id = fields.Many2one('project.project', string='Dự án liên quan', ondelete='set null', index=True)
    follower_user_ids = fields.Many2many(
        'res.users', 'tp_request_follower_rel', 'request_id', 'user_id',
        string='Người theo dõi', domain=[('share', '=', False), ('active', '=', True)],
    )
    attachment_ids = fields.Many2many(
        'ir.attachment', 'tp_request_attachment_rel', 'request_id', 'attachment_id',
        string='Tệp đính kèm', copy=False,
    )

    # ------------------------------------------------------------------ Lifecycle (2 separate layers)
    approval_state = fields.Selection(APPROVAL_STATES, string='Trạng thái phê duyệt', required=True,
                                      default='draft', readonly=True, index=True, copy=False)
    execution_state = fields.Selection(EXECUTION_STATES, string='Trạng thái thực hiện', required=True,
                                       default='not_applicable', readonly=True, index=True, copy=False)
    version = fields.Integer(string='Phiên bản hồ sơ', required=True, default=1, readonly=True, copy=False)
    submitted_at = fields.Datetime(string='Thời điểm gửi', readonly=True, index=True, copy=False)
    approved_at = fields.Datetime(string='Thời điểm hoàn tất duyệt', readonly=True, copy=False)
    due_at = fields.Datetime(string='Hạn xử lý bước hiện tại', readonly=True, index=True, copy=False)
    is_overdue = fields.Boolean(string='Quá hạn', compute='_compute_is_overdue', search='_search_is_overdue')
    overdue_notified_at = fields.Datetime(string='Đã nhắc quá hạn lúc', readonly=True, copy=False)

    # ------------------------------------------------------------------ Approval route & execution
    step_ids = fields.One2many('tp.request.step', 'request_id', string='Tuyến duyệt hồ sơ', readonly=True, copy=False)
    current_step_id = fields.Many2one('tp.request.step', string='Bước duyệt hiện tại', readonly=True, copy=False,
                                      ondelete='set null')
    current_step_name = fields.Char(related='current_step_id.name', store=True, string='Tên bước hiện tại')
    current_approver_ids = fields.Many2many(
        'res.users', 'tp_request_cur_approver_rel', 'request_id', 'user_id',
        string='Người đang đến lượt duyệt', readonly=True, copy=False,
    )
    all_approver_ids = fields.Many2many(
        'res.users', 'tp_request_all_approver_rel', 'request_id', 'user_id',
        string='Tất cả người trong tuyến duyệt', readonly=True, copy=False,
    )
    executor_user_ids = fields.Many2many(
        'res.users', 'tp_request_executor_rel', 'request_id', 'user_id',
        string='Người được phép thực hiện', readonly=True, copy=False,
    )
    assigned_executor_id = fields.Many2one('res.users', string='Người nhận thực hiện', readonly=True, copy=False,
                                           ondelete='restrict')
    execution_due_at = fields.Datetime(string='Hạn thực hiện', readonly=True, copy=False)
    execution_started_at = fields.Datetime(string='Bắt đầu thực hiện lúc', readonly=True, copy=False)
    execution_done_at = fields.Datetime(string='Hoàn thành thực hiện lúc', readonly=True, copy=False)
    execution_result = fields.Text(string='Kết quả thực hiện', readonly=True, copy=False)
    execution_cancel_reason = fields.Text(string='Lý do không thể thực hiện', readonly=True, copy=False)

    return_reason = fields.Text(string='Lý do trả lại gần nhất', readonly=True, copy=False)
    reject_reason = fields.Text(string='Lý do từ chối', readonly=True, copy=False)
    withdraw_reason = fields.Text(string='Lý do rút / hủy', readonly=True, copy=False)
    source_request_id = fields.Many2one('tp.request', string='Tạo mới từ hồ sơ cũ', readonly=True, copy=False,
                                        ondelete='set null')

    # ------------------------------------------------------------------ Attendance integration (1-1)
    attendance_correction_id = fields.Many2one(
        'tp.hr.attendance.correction', string='Phiếu điều chỉnh công gốc', readonly=True, copy=False,
        ondelete='restrict', index='btree_not_null',
    )
    att_work_date = fields.Date(string='Ngày công cần điều chỉnh')
    att_requested_in = fields.Float(string='Giờ vào đề nghị')
    att_requested_out = fields.Float(string='Giờ ra đề nghị')
    att_current_in = fields.Char(string='Giờ vào đang ghi', readonly=True, copy=False)
    att_current_out = fields.Char(string='Giờ ra đang ghi', readonly=True, copy=False)

    # ------------------------------------------------------------------ Equipment & IT fields
    equipment_id = fields.Many2one('maintenance.equipment', string='Thiết bị đang dùng liên quan', ondelete='restrict')
    equipment_name_snap = fields.Char(string='Thiết bị (lúc gửi)', readonly=True, copy=False)
    equipment_category_id = fields.Many2one('maintenance.equipment.category', string='Loại thiết bị', ondelete='set null')
    equipment_quantity = fields.Integer(string='Số lượng đề nghị', default=1)
    equipment_desired_spec = fields.Text(string='Cấu hình / yêu cầu mong muốn')
    equipment_issue_detail = fields.Text(string='Mô tả hiện tượng / lỗi')

    fulfilled_equipment_id = fields.Many2one('maintenance.equipment', string='Thiết bị đã cấp / đổi sang',
                                             readonly=True, copy=False, ondelete='restrict')
    old_equipment_condition = fields.Selection(OLD_EQUIP_CONDITIONS, string='Tình trạng máy cũ khi thu hồi',
                                               readonly=True, copy=False)
    equipment_move_ids = fields.Many2many('tp.equipment.move', 'tp_request_equip_move_rel', 'request_id', 'move_id',
                                          string='Phiếu bàn giao / thu hồi liên kết', readonly=True, copy=False)
    equipment_repair_id = fields.Many2one('maintenance.request', string='Phiếu sửa chữa liên kết',
                                          readonly=True, copy=False, ondelete='set null')
    equipment_proposal_id = fields.Many2one('tp.equipment.proposal', string='Đề xuất mua sắm thiết bị liên kết',
                                            readonly=True, copy=False, ondelete='set null')

    it_category = fields.Selection(IT_CATEGORIES, string='Nhóm hỗ trợ IT')
    it_device_id = fields.Many2one('maintenance.equipment', string='Thiết bị gặp sự cố IT', ondelete='set null')
    it_urgency_impact = fields.Selection(IT_IMPACTS, string='Mức độ ảnh hưởng', default='self')

    # ------------------------------------------------------------------ Immutable audit history
    history_ids = fields.One2many('tp.request.history', 'request_id', string='Lịch sử hệ thống', readonly=True)

    _code_unique = models.UniqueIndex("(code) WHERE code IS NOT NULL AND code != 'Mới'", 'Mã đề nghị đã tồn tại.')
    _att_correction_unique = models.UniqueIndex(
        '(attendance_correction_id) WHERE attendance_correction_id IS NOT NULL',
        'Mỗi phiếu điều chỉnh công chỉ gắn với một hồ sơ đề nghị.',
    )

    # ------------------------------------------------------------------ Mail override (internal only, no external email)
    def _notify_thread_by_email(self, message, recipients_data, msg_vals=False, **kwargs):
        """Never send unsolicited external email/Zalo; internal Odoo inbox + bus only (Section XIV)."""
        return True

    # ------------------------------------------------------------------ Computes
    @api.depends('approval_state', 'due_at', 'execution_state', 'execution_due_at')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for rec in self:
            over_app = bool(rec.approval_state == 'pending' and rec.due_at and rec.due_at < now)
            over_exec = bool(
                rec.approval_state == 'approved'
                and rec.execution_state in ('pending', 'in_progress')
                and rec.execution_due_at
                and rec.execution_due_at < now
            )
            rec.is_overdue = over_app or over_exec

    def _search_is_overdue(self, operator, value):
        now = fields.Datetime.now()
        over_dom = [
            '|',
            '&', ('approval_state', '=', 'pending'), ('due_at', '<', now),
            '&', ('approval_state', '=', 'approved'),
            '&', ('execution_state', 'in', ('pending', 'in_progress')), ('execution_due_at', '<', now),
        ]
        if operator in ('in', 'not in'):
            vals = {bool(v) for v in (value or [])}
            if vals == {True, False}:
                return Domain.TRUE if operator == 'in' else Domain.FALSE
            if not vals:
                return Domain.FALSE if operator == 'in' else Domain.TRUE
            want_true = (True in vals) if operator == 'in' else (True not in vals)
        else:
            want_true = (operator == '=' and bool(value)) or (operator == '!=' and not bool(value))
        return over_dom if want_true else ['!'] + over_dom

    # ------------------------------------------------------------------ Helpers
    @api.model
    def _tp_own_employee(self, user=None, company=None):
        user = user or self.env.user
        company = company or self.env.company
        return self.env['hr.employee'].sudo().search([
            ('user_id', '=', user.id),
            ('company_id', '=', company.id),
        ], limit=1)

    def _tp_record_history(self, action, state_before='', state_after='', step_name='', note='', result_ref='', actor=None):
        actor = actor or self.env.user
        rows = []
        for rec in self:
            rows.append({
                'request_id': rec.id,
                'actor_id': actor.id,
                'actor_name': actor.sudo().name or '',
                'action': action,
                'state_before': state_before or '',
                'state_after': state_after or '',
                'step_name': step_name or '',
                'note': (note or '').strip() or False,
                'request_version': rec.version,
                'result_ref': result_ref or False,
            })
        if rows:
            internal(self.env['tp.request.history']).create(rows)

    def _tp_notify_internal(self, recipients, subject, body_text, event_type='updated'):
        """Send internal Odoo inbox notification + realtime bus ping without external email."""
        self.ensure_one()
        users = active_internal_users(recipients, company=self.company_id)
        if not users:
            return
        url = f'/app/de-nghi/ho-so/{self.id}'
        html_body = Markup(
            '<p><strong>%s</strong> — <a href="%s">%s: %s</a></p><p>%s</p>'
        ) % (escape(subject), escape(url), escape(self.code), escape(self.title), escape(body_text))
        internal(self).with_context(
            mail_notify_noemail=True,
            mail_post_autofollow=False,
        ).message_post(
            body=html_body,
            subject=subject,
            partner_ids=users.mapped('partner_id').ids,
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        bus = self.env['bus.bus'].sudo()
        for user in users:
            bus._sendone(user, 'tp_request/updated', {
                'request_id': self.id,
                'code': self.code,
                'event': event_type,
                'approval_state': self.approval_state,
                'execution_state': self.execution_state,
            })

    def _tp_validate_linked_objects(self, vals, rtype=None):
        """Ensure non-admin users cannot link projects/equipment outside their real scope."""
        if self.env.su or is_internal(self) or is_bridge(self):
            return
        if vals.get('project_id'):
            proj = self.env['project.project'].browse(vals['project_id']).exists()
            if not proj:
                raise ValidationError(_('Dự án được chọn không tồn tại.'))
            proj.check_access('read')
        own_emp = self._tp_own_employee(self.env.user, self.env.company)
        for eq_field in ('equipment_id', 'it_device_id'):
            eq_id = vals.get(eq_field)
            if eq_id:
                eq = self.env['maintenance.equipment'].sudo().browse(eq_id).exists()
                if not eq or eq.tp_lifecycle != 'active':
                    raise ValidationError(_('Thiết bị được chọn không hợp lệ hoặc đã ngừng quản lý.'))
                if not is_live_admin_user(self.env.user, company=self.env.company):
                    if not own_emp or eq.tp_employee_id != own_emp or eq.tp_custody not in ('employee', 'loan'):
                        raise AccessError(_('Bạn chỉ được chọn thiết bị hiện đang được bàn giao cho chính mình.'))

    # ------------------------------------------------------------------ CRUD Guards
    @api.model_create_multi
    def create(self, vals_list):
        if not is_internal(self) and not is_bridge(self):
            for vals in vals_list:
                forbidden = SYSTEM_GUARDED_FIELDS & set(vals)
                if forbidden:
                    raise AccessError(_(
                        'Không được ghi trực tiếp thông tin hệ thống hoặc trạng thái phê duyệt (%s).',
                        ', '.join(sorted(forbidden)),
                    ))
                rtype = self.env['tp.request.type'].browse(vals.get('type_id')).exists()
                if not rtype or not rtype.active:
                    raise UserError(_('Loại đề nghị không tồn tại hoặc đã ngừng sử dụng.'))
                company = self.env.company
                emp = self._tp_own_employee(self.env.user, company)
                if not rtype._tp_user_can_submit(self.env.user, employee=emp):
                    raise AccessError(_('Tài khoản của bạn không thuộc phạm vi được gửi loại đề nghị “%s”.', rtype.name))
                self._tp_validate_linked_objects(vals, rtype=rtype)
                vals.update({
                    'company_id': company.id,
                    'requester_user_id': self.env.uid,
                    'requester_employee_id': emp.id if emp else False,
                    'department_id': emp.department_id.id if emp and emp.department_id else False,
                    'requester_name_snap': emp.name if emp else self.env.user.name,
                    'requester_code_snap': emp.tp_employee_code if emp else '',
                    'department_name_snap': emp.department_id.name if emp and emp.department_id else '',
                    'approval_state': 'draft',
                    'execution_state': 'waiting_approval' if rtype.requires_execution else 'not_applicable',
                    'version': 1,
                    'type_config_version': rtype.config_version,
                })
                if not vals.get('priority'):
                    vals['priority'] = rtype.default_priority or 'normal'
                if vals.get('equipment_id'):
                    eq = self.env['maintenance.equipment'].sudo().browse(vals['equipment_id'])
                    vals['equipment_name_snap'] = eq.display_name
        for vals in vals_list:
            if not vals.get('code') or vals['code'] == 'Mới':
                vals['code'] = self.env['ir.sequence'].sudo().next_by_code('tp.request') or 'DN-0000'
        records = super().create(vals_list)
        if not is_bridge(self):
            records._tp_record_history(
                'create', state_before='', state_after='draft',
                note=records[0].title if len(records) == 1 else '',
            )
        return records

    def write(self, vals):
        if is_internal(self) or is_bridge(self):
            return super().write(vals)
        self.check_access('write')
        self._tp_lock_with_corrections()
        forbidden = set(vals) - OWNER_EDITABLE_FIELDS
        if forbidden:
            raise AccessError(_(
                'Không được sửa trực tiếp trường hệ thống / trạng thái (%s). Dùng các nút thao tác nghiệp vụ.',
                ', '.join(sorted(forbidden)),
            ))
        for rec in self:
            if rec.requester_user_id != self.env.user:
                raise AccessError(_('Chỉ người gửi mới được sửa nội dung đề nghị của mình.'))
            if rec.approval_state not in ('draft', 'returned'):
                raise UserError(_(
                    'Hồ sơ %(code)s đang ở trạng thái “%(state)s”, không thể sửa nội dung.',
                    code=rec.code, state=STATE_LABELS.get(rec.approval_state, rec.approval_state),
                ))
        self._tp_validate_linked_objects(vals)
        vals = dict(vals)
        if 'equipment_id' in vals:
            eq = self.env['maintenance.equipment'].sudo().browse(vals['equipment_id']) if vals['equipment_id'] else False
            vals['equipment_name_snap'] = eq.display_name if eq else False
        return super().write(vals)

    def unlink(self):
        if is_internal(self) or is_bridge(self):
            return super(TpRequest, self.with_context(_tp_request_cascade_draft=INTERNAL)).unlink()
        self.check_access('unlink')
        self._tp_lock_with_corrections()
        for rec in self:
            if rec.requester_user_id != self.env.user:
                raise AccessError(_('Chỉ người lập được xóa bản nháp của mình.'))
            if rec.approval_state != 'draft' or rec.version > 1:
                raise UserError(_('Không được xóa hồ sơ đã gửi để bảo toàn lịch sử; hãy dùng chức năng Rút đề nghị.'))
        return super(TpRequest, self.with_context(_tp_request_cascade_draft=INTERNAL)).unlink()

    def copy(self, default=None):
        raise UserError(_('Dùng chức năng "Tạo hồ sơ mới từ bản cũ" thay vì nhân bản trực tiếp.'))

    # ------------------------------------------------------------------ Validation helper
    def _tp_collect_validation_errors(self):
        """Return list of {id, label, location, message} for missing/invalid required fields."""
        self.ensure_one()
        errors = []
        rtype = self.type_id
        if not (self.title or '').strip():
            errors.append({'id': 'req_title', 'label': 'Tiêu đề đề nghị', 'location': 'Thông tin chung',
                           'message': 'Vui lòng nhập Tiêu đề đề nghị.'})
        if rtype.require_reason and not (self.description or '').strip():
            errors.append({'id': 'req_description', 'label': 'Nội dung / lý do', 'location': 'Thông tin chung',
                           'message': 'Vui lòng nhập Nội dung / lý do.'})
        if rtype.require_needed_date and not self.needed_date:
            errors.append({'id': 'req_needed_date', 'label': 'Ngày cần đáp ứng', 'location': 'Thông tin chung',
                           'message': 'Vui lòng chọn Ngày cần đáp ứng.'})
        if rtype.require_attachment and not self.attachment_ids:
            errors.append({'id': 'req_attachments', 'label': 'Tệp đính kèm', 'location': 'Tệp đính kèm',
                           'message': 'Loại đề nghị này yêu cầu đính kèm ít nhất một tệp minh chứng.'})

        kind = rtype.handler_kind
        if kind == 'attendance_correction':
            if not self.att_work_date:
                errors.append({'id': 'req_att_work_date', 'label': 'Ngày công', 'location': 'Điều chỉnh công',
                               'message': 'Vui lòng chọn Ngày công cần điều chỉnh.'})
            if not self.att_requested_in and self.att_requested_in != 0:
                errors.append({'id': 'req_att_in', 'label': 'Giờ vào đúng', 'location': 'Điều chỉnh công',
                               'message': 'Vui lòng nhập Giờ vào đúng.'})
            if not self.att_requested_out:
                errors.append({'id': 'req_att_out', 'label': 'Giờ ra đúng', 'location': 'Điều chỉnh công',
                               'message': 'Vui lòng nhập Giờ ra đúng.'})
            elif self.att_requested_out <= (self.att_requested_in or 0):
                errors.append({'id': 'req_att_out', 'label': 'Giờ ra đúng', 'location': 'Điều chỉnh công',
                               'message': 'Giờ ra phải sau giờ vào trong cùng ngày công.'})
        elif kind == 'equipment_assign':
            if not self.equipment_category_id and not (self.equipment_desired_spec or '').strip():
                errors.append({'id': 'req_equip_category', 'label': 'Loại thiết bị cần cấp', 'location': 'Chi tiết thiết bị',
                               'message': 'Vui lòng chọn Loại thiết bị hoặc mô tả nhu cầu thiết bị cần cấp.'})
        elif kind == 'equipment_swap':
            if not self.equipment_id:
                errors.append({'id': 'req_equipment_id', 'label': 'Thiết bị đang dùng cần đổi', 'location': 'Chi tiết thiết bị',
                               'message': 'Vui lòng chọn Thiết bị đang sử dụng cần đổi.'})
        elif kind == 'equipment_repair':
            if not self.equipment_id:
                errors.append({'id': 'req_equipment_id', 'label': 'Thiết bị báo hỏng / sửa chữa', 'location': 'Chi tiết thiết bị',
                               'message': 'Vui lòng chọn Thiết bị đang sử dụng gặp sự cố.'})
            if not (self.equipment_issue_detail or '').strip() and not (self.description or '').strip():
                errors.append({'id': 'req_equip_issue', 'label': 'Mô tả hiện tượng / lỗi', 'location': 'Chi tiết thiết bị',
                               'message': 'Vui lòng mô tả hiện tượng hỏng hoặc yêu cầu sửa chữa.'})
        elif kind == 'equipment_purchase':
            if not self.equipment_category_id and not (self.equipment_desired_spec or '').strip():
                errors.append({'id': 'req_equip_category', 'label': 'Loại thiết bị đề xuất mua', 'location': 'Chi tiết mua sắm',
                               'message': 'Vui lòng chọn Loại thiết bị hoặc ghi cấu hình đề xuất mua.'})
            if not self.equipment_quantity or self.equipment_quantity < 1:
                errors.append({'id': 'req_equip_qty', 'label': 'Số lượng', 'location': 'Chi tiết mua sắm',
                               'message': 'Số lượng đề xuất mua phải lớn hơn hoặc bằng 1.'})
        elif kind == 'it_support':
            if not self.it_category:
                errors.append({'id': 'req_it_category', 'label': 'Nhóm hỗ trợ IT', 'location': 'Chi tiết hỗ trợ IT',
                               'message': 'Vui lòng chọn Nhóm hỗ trợ IT.'})
        return errors

    # ------------------------------------------------------------------ Workflow Actions
    def _tp_lock_with_corrections(self):
        # Native attendance actions lock the correction before updating this projection.
        lock_rows(self.mapped('attendance_correction_id'))
        lock_rows(self)

    def action_submit(self, expected_version=None):
        """Submit draft or resubmit returned request. Blocks if required fields or approvers missing."""
        self.ensure_one()
        self.check_access('read')
        self._tp_lock_with_corrections()
        if self.requester_user_id != self.env.user:
            raise AccessError(_('Chỉ người lập đề nghị mới được gửi phê duyệt.'))
        if expected_version is not None and self.version != int(expected_version):
            raise UserError(_('Hồ sơ đã được cập nhật ở phiên bản mới hơn. Vui lòng tải lại trước khi gửi.'))
        if self.approval_state not in ('draft', 'returned'):
            raise UserError(_('Chỉ gửi được hồ sơ đang ở trạng thái Nháp hoặc Trả lại bổ sung.'))
        if not self.type_id.active:
            raise UserError(_('Loại đề nghị “%s” đã ngừng sử dụng, không thể gửi mới.', self.type_id.name))

        # Attendance correction delegates authoritatively to tp.hr.attendance.correction
        if self.handler_kind == 'attendance_correction' and self.attendance_correction_id:
            self.attendance_correction_id.action_submit()
            self.invalidate_recordset()
            return True

        errors = self._tp_collect_validation_errors()
        if errors:
            raise ValidationError('\n'.join(f'• {e["label"]}: {e["message"]}' for e in errors))

        preview = self.type_id._tp_resolve_route_preview(
            requester_user=self.requester_user_id,
            company=self.company_id,
            employee=self.requester_employee_id,
            project=self.project_id,
        )
        if not preview['can_submit']:
            raise UserError(_(
                'Chưa thể gửi đề nghị do tuyến duyệt chưa đủ cấu hình:\n%s\n'
                'Hồ sơ vẫn được lưu nháp. Vui lòng liên hệ Quản trị hoàn thiện cấu hình.',
                '\n'.join(f'• {m}' for m in preview['missing_reasons']),
            ))

        now = fields.Datetime.now()
        old_state = self.approval_state
        is_resubmit = old_state == 'returned'
        new_version = self.version + 1

        # Mark any open steps from previous version as skipped (never reuse old decisions for new content)
        prev_steps = self.step_ids.filtered(lambda s: s.state in ('waiting', 'pending'))
        if prev_steps:
            internal(prev_steps).write({'state': 'skipped'})

        Step = internal(self.env['tp.request.step'])
        created_steps = Step.browse()
        all_approver_ids = set(self.all_approver_ids.ids)
        for idx, sdata in enumerate(preview['steps']):
            step_state = 'pending' if idx == 0 else 'waiting'
            step_due = add_working_hours(now, sdata['sla_hours']) if idx == 0 else False
            step_rec = Step.create({
                'request_id': self.id,
                'sequence': sdata['sequence'],
                'name': sdata['name'],
                'approver_rule': sdata['approver_rule'],
                'approval_policy': sdata['approval_policy'],
                'eligible_user_ids': [Command.set(sdata['approver_ids'])],
                'state': step_state,
                'sla_hours': sdata['sla_hours'],
                'due_at': step_due,
                'request_version': new_version,
                'can_return': sdata['can_return'],
                'can_reject': sdata['can_reject'],
            })
            created_steps |= step_rec
            all_approver_ids.update(sdata['approver_ids'])

        first_step = created_steps[:1]
        emp = self.requester_employee_id.sudo()
        internal(self).write({
            'approval_state': 'pending',
            'execution_state': 'waiting_approval' if self.type_id.requires_execution else 'not_applicable',
            'version': new_version,
            'type_config_version': preview['config_version'],
            'submitted_at': now,
            'due_at': first_step.due_at,
            'overdue_notified_at': False,
            'current_step_id': first_step.id,
            'current_approver_ids': [Command.set(first_step.eligible_user_ids.ids)],
            'all_approver_ids': [Command.set(sorted(all_approver_ids))],
            'executor_user_ids': [Command.set(preview['executor_ids'])] if preview['requires_execution'] else [Command.clear()],
            'requester_name_snap': emp.name if emp else self.requester_user_id.sudo().name,
            'requester_code_snap': emp.tp_employee_code if emp else '',
            'department_name_snap': emp.department_id.name if emp and emp.department_id else '',
            'equipment_name_snap': self.equipment_id.sudo().display_name if self.equipment_id else self.equipment_name_snap,
            'return_reason': False,
        })

        self._tp_record_history(
            'resubmit' if is_resubmit else 'submit',
            state_before=old_state,
            state_after='pending',
            step_name=first_step.name,
            note=_('Gửi lại đề nghị phiên bản %s', new_version) if is_resubmit else _('Gửi đề nghị chờ duyệt'),
        )
        self._tp_notify_internal(
            first_step.eligible_user_ids,
            _('Đề nghị cần bạn duyệt'),
            _('%(user)s vừa gửi đề nghị "%(title)s" — bước hiện tại: %(step)s.',
              user=self.requester_name_snap or self.requester_user_id.sudo().name,
              title=self.title, step=first_step.name),
            event_type='pending_approval',
        )
        return True

    def _tp_check_current_approver(self):
        """Re-check live approval right on current step (never sudo, never self-approve)."""
        self.ensure_one()
        if self.approval_state != 'pending' or not self.current_step_id or self.current_step_id.state != 'pending':
            raise UserError(_('Hồ sơ không còn ở bước chờ duyệt hoặc đã được xử lý trước đó.'))
        if self.requester_user_id == self.env.user:
            raise AccessError(_('Không được tự phê duyệt đề nghị của chính mình.'))
        step = self.current_step_id
        user = self.env.user
        if user not in step.eligible_user_ids:
            raise AccessError(_('Chưa đến lượt bạn duyệt hoặc bạn không nằm trong danh sách người duyệt bước hiện tại.'))
        if not user.active or user.share or self.company_id not in user.company_ids:
            raise AccessError(_('Tài khoản của bạn không còn đủ điều kiện phê duyệt trong công ty này.'))
        if step.approver_rule == 'admin_group':
            if not is_live_admin_user(user, company=self.company_id, lock=True):
                raise AccessError(_('Quyền Quản trị của bạn không còn hiệu lực nên không thể phê duyệt bước này.'))
        elif step.approver_rule == 'department_manager':
            dept = self.department_id.sudo()
            if not (dept and dept.manager_id and dept.manager_id.user_id == user):
                # Allow if explicitly transferred via admin transfer (eligible_user_ids updated)
                if not step.transferred:
                    raise AccessError(_('Bạn không còn là Trưởng phòng phụ trách bước duyệt này.'))
        return step

    def action_approve_step(self, note='', expected_version=None):
        """Approve current pending step atomically; advances to next step or finalizes approval."""
        self.ensure_one()
        self.check_access('read')
        self._tp_lock_with_corrections()
        if expected_version is not None and self.version != int(expected_version):
            raise UserError(_('Hồ sơ đã thay đổi trước thao tác này. Vui lòng tải lại để xem trạng thái mới nhất.'))

        if self.handler_kind == 'attendance_correction' and self.attendance_correction_id:
            self.attendance_correction_id.action_approve(note=note)
            self.invalidate_recordset()
            return {'status': 'approved', 'next_label': _('Đã duyệt và cập nhật bảng công')}

        step = self._tp_check_current_approver()
        now = fields.Datetime.now()
        clean_note = (note or '').strip()
        new_version = self.version + 1

        internal(step).write({
            'state': 'approved',
            'decided_by_id': self.env.uid,
            'decided_at': now,
            'decision_note': clean_note or False,
        })

        next_step = self.step_ids.filtered(
            lambda s: s.request_version == step.request_version and s.state == 'waiting'
        ).sorted(lambda s: (s.sequence, s.id))[:1]

        if next_step:
            next_due = add_working_hours(now, next_step.sla_hours or self.type_id.sla_hours or 24.0)
            internal(next_step).write({'state': 'pending', 'due_at': next_due})
            internal(self).write({
                'version': new_version,
                'current_step_id': next_step.id,
                'current_approver_ids': [Command.set(next_step.eligible_user_ids.ids)],
                'due_at': next_due,
                'overdue_notified_at': False,
            })
            self._tp_record_history(
                'approve_step',
                state_before='pending',
                state_after='pending',
                step_name=step.name,
                note=clean_note or _('Đã chấp thuận, chuyển sang bước: %s', next_step.name),
            )
            self._tp_notify_internal(
                next_step.eligible_user_ids,
                _('Đề nghị đến lượt bạn duyệt'),
                _('Bước "%(prev)s" đã được duyệt. Đề nghị "%(title)s" chuyển sang bước "%(nxt)s".',
                  prev=step.name, title=self.title, nxt=next_step.name),
                event_type='pending_approval',
            )
            return {
                'status': 'next_step',
                'next_label': _('Đã chấp thuận. Hồ sơ đã chuyển sang bước: %s', next_step.name),
            }

        # Final approval reached!
        exec_required = self.type_id.requires_execution
        executors = self.executor_user_ids or self.type_id._tp_resolve_executors(company=self.company_id)
        exec_due = add_working_hours(now, self.type_id.sla_hours or 24.0) if exec_required else False
        internal(self).write({
            'approval_state': 'approved',
            'execution_state': 'pending' if exec_required else 'not_applicable',
            'version': new_version,
            'approved_at': now,
            'due_at': False,
            'overdue_notified_at': False,
            'current_step_id': False,
            'current_approver_ids': [Command.clear()],
            'executor_user_ids': [Command.set(executors.ids)] if exec_required else [Command.clear()],
            'execution_due_at': exec_due,
        })
        self._tp_record_history(
            'approve_final',
            state_before='pending',
            state_after='approved',
            step_name=step.name,
            note=clean_note or _('Hoàn tất phê duyệt đề nghị'),
        )
        self._tp_notify_internal(
            self.requester_user_id | self.follower_user_ids,
            _('Đề nghị đã được phê duyệt'),
            _('Đề nghị "%(title)s" đã được %(actor)s chấp thuận%(extra)s.',
              title=self.title, actor=self.env.user.name,
              extra=' và chuyển sang bộ phận thực hiện' if exec_required else ''),
            event_type='approved',
        )
        if exec_required and executors:
            self._tp_notify_internal(
                executors,
                _('Có đề nghị đã duyệt cần thực hiện'),
                _('Đề nghị "%(title)s" của %(req)s đã được phê duyệt và chờ thực hiện.',
                  title=self.title, req=self.requester_name_snap or self.requester_user_id.sudo().name),
                event_type='pending_execution',
            )
        return {
            'status': 'approved',
            'next_label': (
                _('Đã phê duyệt hoàn tất. Hồ sơ đã chuyển sang hàng đợi "Cần thực hiện".')
                if exec_required
                else _('Đã phê duyệt hoàn tất đề nghị.')
            ),
        }

    def action_return(self, reason, expected_version=None):
        """Return request to requester for revision; mandatory reason."""
        self.ensure_one()
        self.check_access('read')
        self._tp_lock_with_corrections()
        if expected_version is not None and self.version != int(expected_version):
            raise UserError(_('Hồ sơ đã thay đổi trước thao tác này. Vui lòng tải lại.'))
        clean_reason = (reason or '').strip()
        if not clean_reason:
            raise UserError(_('Bắt buộc nhập lý do trả lại để người gửi bổ sung thông tin.'))

        if self.handler_kind == 'attendance_correction' and self.attendance_correction_id:
            self.attendance_correction_id.action_return(note=clean_reason)
            self.invalidate_recordset()
            return True

        step = self._tp_check_current_approver()
        if not step.can_return:
            raise UserError(_('Bước duyệt này không hỗ trợ thao tác trả lại bổ sung.'))
        now = fields.Datetime.now()
        internal(step).write({
            'state': 'returned',
            'decided_by_id': self.env.uid,
            'decided_at': now,
            'decision_note': clean_reason,
        })
        waiting = self.step_ids.filtered(lambda s: s.state == 'waiting')
        if waiting:
            internal(waiting).write({'state': 'skipped'})
        internal(self).write({
            'approval_state': 'returned',
            'version': self.version + 1,
            'due_at': False,
            'overdue_notified_at': False,
            'current_step_id': False,
            'current_approver_ids': [Command.clear()],
            'return_reason': clean_reason,
        })
        self._tp_record_history(
            'return', state_before='pending', state_after='returned',
            step_name=step.name, note=clean_reason,
        )
        self._tp_notify_internal(
            self.requester_user_id,
            _('Đề nghị bị trả lại cần bổ sung'),
            _('%(actor)s đã trả lại đề nghị "%(title)s". Lý do: %(reason)s',
              actor=self.env.user.name, title=self.title, reason=clean_reason),
            event_type='returned',
        )
        return True

    def action_reject(self, reason, expected_version=None):
        """Reject request definitively; mandatory reason."""
        self.ensure_one()
        self.check_access('read')
        lock_rows(self)
        if expected_version is not None and self.version != int(expected_version):
            raise UserError(_('Hồ sơ đã thay đổi trước thao tác này. Vui lòng tải lại.'))
        clean_reason = (reason or '').strip()
        if not clean_reason:
            raise UserError(_('Bắt buộc nhập lý do từ chối đề nghị.'))
        if self.handler_kind == 'attendance_correction':
            raise UserError(_('Đề nghị điều chỉnh công sử dụng thao tác "Trả lại bổ sung" thay vì từ chối.'))

        step = self._tp_check_current_approver()
        if not step.can_reject or not self.type_id.allow_reject:
            raise UserError(_('Loại đề nghị này không hỗ trợ thao tác từ chối ở bước hiện tại.'))
        now = fields.Datetime.now()
        internal(step).write({
            'state': 'rejected',
            'decided_by_id': self.env.uid,
            'decided_at': now,
            'decision_note': clean_reason,
        })
        waiting = self.step_ids.filtered(lambda s: s.state == 'waiting')
        if waiting:
            internal(waiting).write({'state': 'skipped'})
        internal(self).write({
            'approval_state': 'rejected',
            'execution_state': 'not_applicable',
            'version': self.version + 1,
            'due_at': False,
            'overdue_notified_at': False,
            'current_step_id': False,
            'current_approver_ids': [Command.clear()],
            'reject_reason': clean_reason,
        })
        self._tp_record_history(
            'reject', state_before='pending', state_after='rejected',
            step_name=step.name, note=clean_reason,
        )
        self._tp_notify_internal(
            self.requester_user_id | self.follower_user_ids,
            _('Đề nghị đã bị từ chối'),
            _('%(actor)s đã từ chối đề nghị "%(title)s". Lý do: %(reason)s',
              actor=self.env.user.name, title=self.title, reason=clean_reason),
            event_type='rejected',
        )
        return True

    def action_withdraw(self, reason='', expected_version=None):
        """Withdraw request when permitted; never revokes already-executed business results."""
        self.ensure_one()
        self.check_access('read')
        self._tp_lock_with_corrections()
        if expected_version is not None and self.version != int(expected_version):
            raise UserError(_('Hồ sơ đã thay đổi. Vui lòng tải lại.'))
        if self.requester_user_id != self.env.user:
            raise AccessError(_('Chỉ người gửi đề nghị mới được rút / hủy hồ sơ của mình.'))
        if not self.type_id.allow_withdraw:
            raise UserError(_('Loại đề nghị này không cho phép rút hồ sơ.'))
        if self.approval_state not in ('draft', 'pending', 'returned'):
            raise UserError(_('Hồ sơ đã có quyết định cuối cùng hoặc đã chuyển thực hiện nên không thể rút.'))

        if self.handler_kind == 'attendance_correction' and self.attendance_correction_id:
            if self.attendance_correction_id.state == 'submitted':
                self.attendance_correction_id.action_withdraw(reason=reason)
            else:
                self.attendance_correction_id.action_cancel()
            self.invalidate_recordset()
            return True

        old_state = self.approval_state
        prev_approvers = self.current_approver_ids
        open_steps = self.step_ids.filtered(lambda s: s.state in ('waiting', 'pending'))
        if open_steps:
            internal(open_steps).write({'state': 'skipped'})
        clean_reason = (reason or '').strip()
        internal(self).write({
            'approval_state': 'withdrawn',
            'execution_state': 'not_applicable',
            'version': self.version + 1,
            'due_at': False,
            'overdue_notified_at': False,
            'current_step_id': False,
            'current_approver_ids': [Command.clear()],
            'withdraw_reason': clean_reason or False,
        })
        self._tp_record_history(
            'withdraw', state_before=old_state, state_after='withdrawn',
            note=clean_reason or _('Người gửi tự rút đề nghị'),
        )
        if prev_approvers:
            self._tp_notify_internal(
                prev_approvers,
                _('Đề nghị đã được người gửi rút lại'),
                _('%(req)s đã rút đề nghị "%(title)s".',
                  req=self.requester_name_snap or self.requester_user_id.sudo().name, title=self.title),
                event_type='withdrawn',
            )
        return True

    def action_transfer_approver(self, new_user_ids, reason, expected_version=None):
        """Authorized manager transfers current pending approval step with full audit log."""
        self.ensure_one()
        require_request_manager(self.env, company=self.company_id)
        lock_rows(self)
        if expected_version is not None and self.version != int(expected_version):
            raise UserError(_('Hồ sơ đã thay đổi. Vui lòng tải lại.'))
        if self.approval_state != 'pending' or not self.current_step_id:
            raise UserError(_('Chỉ chuyển giao người duyệt khi hồ sơ đang ở trạng thái Chờ duyệt.'))
        if self.handler_kind == 'attendance_correction':
            raise UserError(_('Điều chỉnh công tuân theo quy tắc Admin gốc/ủy quyền (DEC-061), không chuyển giao người duyệt thủ công.'))
        clean_reason = (reason or '').strip()
        if not clean_reason:
            raise UserError(_('Nhập lý do chuyển giao người duyệt.'))
        candidates = active_internal_users(self.env['res.users'].browse(new_user_ids or []), company=self.company_id)
        candidates = candidates - self.requester_user_id
        if not candidates:
            raise UserError(_('Chọn ít nhất một người duyệt hợp lệ khác người gửi.'))

        step = self.current_step_id
        old_names = ', '.join(step.eligible_user_ids.sudo().mapped('name'))
        new_names = ', '.join(candidates.sudo().mapped('name'))
        internal(step).write({
            'eligible_user_ids': [Command.set(candidates.ids)],
            'transferred': True,
        })
        all_ids = set(self.all_approver_ids.ids) | set(candidates.ids)
        internal(self).write({
            'version': self.version + 1,
            'current_approver_ids': [Command.set(candidates.ids)],
            'all_approver_ids': [Command.set(sorted(all_ids))],
        })
        self._tp_record_history(
            'transfer_approver', state_before='pending', state_after='pending',
            step_name=step.name,
            note=_('Chuyển từ [%(old)s] sang [%(new)s]. Lý do: %(reason)s',
                   old=old_names or '—', new=new_names, reason=clean_reason),
        )
        self._tp_notify_internal(
            candidates,
            _('Bạn được chuyển giao duyệt đề nghị'),
            _('%(actor)s đã chuyển giao bước "%(step)s" của đề nghị "%(title)s" cho bạn. Lý do: %(reason)s',
              actor=self.env.user.name, step=step.name, title=self.title, reason=clean_reason),
            event_type='transferred',
        )
        return True

    def action_clone_from_rejected(self):
        """Create a fresh draft from a rejected or withdrawn request (preserves original history)."""
        self.ensure_one()
        self.check_access('read')
        if self.requester_user_id != self.env.user:
            raise AccessError(_('Chỉ người gửi mới có thể tạo bản đề nghị mới từ hồ sơ này.'))
        if self.approval_state not in ('rejected', 'withdrawn'):
            raise UserError(_('Chỉ tạo bản mới từ hồ sơ đã bị từ chối hoặc đã rút.'))
        if not self.type_id.active:
            raise UserError(_('Loại đề nghị này đã ngừng sử dụng.'))
        vals = {
            'title': self.title,
            'type_id': self.type_id.id,
            'description': self.description,
            'priority': self.priority,
            'needed_date': self.needed_date,
            'project_id': self.project_id.id or False,
            'equipment_id': self.equipment_id.id or False,
            'equipment_category_id': self.equipment_category_id.id or False,
            'equipment_quantity': self.equipment_quantity,
            'equipment_desired_spec': self.equipment_desired_spec,
            'equipment_issue_detail': self.equipment_issue_detail,
            'it_category': self.it_category,
            'it_device_id': self.it_device_id.id or False,
            'it_urgency_impact': self.it_urgency_impact,
        }
        new_req = self.create(vals)
        internal(new_req).write({'source_request_id': self.id})
        new_req._tp_record_history(
            'create', state_before='', state_after='draft',
            note=_('Tạo mới từ hồ sơ cũ %s', self.code),
        )
        return new_req.id

    # ------------------------------------------------------------------ Post-Approval Execution
    def _tp_check_executor(self):
        self.ensure_one()
        if self.approval_state != 'approved':
            raise UserError(_('Hồ sơ chưa được phê duyệt hoàn tất nên chưa thể thực hiện.'))
        if self.execution_state not in ('pending', 'in_progress'):
            raise UserError(_('Hồ sơ không còn ở trạng thái chờ hoặc đang thực hiện.'))
        user = self.env.user
        allowed = (
            user in self.executor_user_ids
            or self.assigned_executor_id == user
            or (self.type_id.executor_mode == 'admin_group' and is_live_admin_user(user, company=self.company_id, lock=True))
        )
        if not allowed:
            raise AccessError(_('Bạn không thuộc danh sách người thực hiện được phân công cho hồ sơ này.'))
        return user

    def action_start_execution(self, note='', expected_version=None):
        self.ensure_one()
        self.check_access('read')
        lock_rows(self)
        if expected_version is not None and self.version != int(expected_version):
            raise UserError(_('Hồ sơ đã thay đổi. Vui lòng tải lại.'))
        user = self._tp_check_executor()
        if self.execution_state == 'in_progress' and self.assigned_executor_id == user:
            return True
        old_exec = self.execution_state
        internal(self).write({
            'execution_state': 'in_progress',
            'assigned_executor_id': user.id,
            'execution_started_at': self.execution_started_at or fields.Datetime.now(),
            'version': self.version + 1,
        })
        self._tp_record_history(
            'start_execution',
            state_before=old_exec,
            state_after='in_progress',
            step_name=_('Thực hiện sau duyệt'),
            note=(note or '').strip() or _('Nhận việc và bắt đầu thực hiện'),
        )
        self._tp_notify_internal(
            self.requester_user_id,
            _('Đề nghị đang được thực hiện'),
            _('%(actor)s đã tiếp nhận và đang thực hiện đề nghị "%(title)s".',
              actor=user.name, title=self.title),
            event_type='execution_started',
        )
        return True

    def action_update_execution_progress(self, note, expected_version=None):
        self.ensure_one()
        self.check_access('read')
        lock_rows(self)
        if expected_version is not None and self.version != int(expected_version):
            raise UserError(_('Hồ sơ đã thay đổi. Vui lòng tải lại.'))
        user = self._tp_check_executor()
        clean_note = (note or '').strip()
        if not clean_note:
            raise UserError(_('Nhập nội dung cập nhật tiến độ thực hiện.'))
        old_exec = self.execution_state
        vals = {'version': self.version + 1}
        if self.execution_state == 'pending':
            vals.update({
                'execution_state': 'in_progress',
                'assigned_executor_id': user.id,
                'execution_started_at': fields.Datetime.now(),
            })
        internal(self).write(vals)
        self._tp_record_history(
            'update_progress',
            state_before=old_exec,
            state_after=self.execution_state,
            step_name=_('Cập nhật thực hiện'),
            note=clean_note,
        )
        return True

    def action_complete_execution(self, result_note, expected_version=None, extra_payload=None):
        """Mark execution done (with real equipment workflow execution if equipment type!)."""
        self.ensure_one()
        self.check_access('read')
        lock_rows(self)
        if expected_version is not None and self.version != int(expected_version):
            raise UserError(_('Hồ sơ đã thay đổi. Vui lòng tải lại.'))
        user = self._tp_check_executor()
        clean_result = (result_note or '').strip()
        if not clean_result:
            raise UserError(_('Nhập kết quả thực hiện trước khi xác nhận hoàn thành.'))

        extra = extra_payload or {}
        result_ref = ''
        # Dispatch real equipment execution inside the same atomic transaction
        if self.handler_kind in ('equipment_assign', 'equipment_swap', 'equipment_repair', 'equipment_purchase'):
            result_ref = self._tp_execute_equipment_completion(clean_result, extra)

        old_exec = self.execution_state
        internal(self).write({
            'execution_state': 'done',
            'assigned_executor_id': self.assigned_executor_id.id or user.id,
            'execution_started_at': self.execution_started_at or fields.Datetime.now(),
            'execution_done_at': fields.Datetime.now(),
            'execution_result': clean_result,
            'overdue_notified_at': False,
            'version': self.version + 1,
        })
        self._tp_record_history(
            'complete_execution',
            state_before=old_exec,
            state_after='done',
            step_name=_('Hoàn thành thực hiện'),
            note=clean_result,
            result_ref=result_ref,
        )
        self._tp_notify_internal(
            self.requester_user_id | self.follower_user_ids,
            _('Đề nghị đã hoàn thành thực hiện'),
            _('%(actor)s đã hoàn thành thực hiện đề nghị "%(title)s". Kết quả: %(res)s',
              actor=user.name, title=self.title, res=clean_result),
            event_type='execution_done',
        )
        return {'status': 'done', 'result_ref': result_ref}

    def action_cancel_execution(self, reason, expected_version=None):
        self.ensure_one()
        self.check_access('read')
        lock_rows(self)
        if expected_version is not None and self.version != int(expected_version):
            raise UserError(_('Hồ sơ đã thay đổi. Vui lòng tải lại.'))
        user = self._tp_check_executor()
        clean_reason = (reason or '').strip()
        if not clean_reason:
            raise UserError(_('Bắt buộc nhập lý do không thể thực hiện / hủy thực hiện.'))
        old_exec = self.execution_state
        internal(self).write({
            'execution_state': 'cancelled',
            'assigned_executor_id': self.assigned_executor_id.id or user.id,
            'execution_done_at': fields.Datetime.now(),
            'execution_cancel_reason': clean_reason,
            'overdue_notified_at': False,
            'version': self.version + 1,
        })
        self._tp_record_history(
            'cancel_execution',
            state_before=old_exec,
            state_after='cancelled',
            step_name=_('Hủy thực hiện'),
            note=clean_reason,
        )
        self._tp_notify_internal(
            self.requester_user_id | self.follower_user_ids,
            _('Đề nghị không thể thực hiện'),
            _('%(actor)s đã ghi nhận không thể thực hiện đề nghị "%(title)s". Lý do: %(reason)s',
              actor=user.name, title=self.title, reason=clean_reason),
            event_type='execution_cancelled',
        )
        return True

    # ------------------------------------------------------------------ Overdue Cron (flag + notify only, NEVER auto-approve)
    @api.model
    def _cron_notify_overdue(self):
        now = fields.Datetime.now()
        cutoff = now - timedelta(hours=12)
        overdue_approvals = self.sudo().search([
            ('approval_state', '=', 'pending'),
            ('due_at', '<', now),
            '|', ('overdue_notified_at', '=', False), ('overdue_notified_at', '<', cutoff),
        ], limit=100)
        for req in overdue_approvals:
            recipients = req.current_approver_ids
            if recipients:
                req._tp_notify_internal(
                    recipients,
                    _('Đề nghị quá hạn phê duyệt'),
                    _('Đề nghị "%(title)s" tại bước "%(step)s" đã quá hạn xử lý (%(due)s).',
                      title=req.title, step=req.current_step_name or '', due=format_dt_local(req.due_at)),
                    event_type='overdue',
                )
            internal(req).write({'overdue_notified_at': now})

        overdue_exec = self.sudo().search([
            ('approval_state', '=', 'approved'),
            ('execution_state', 'in', ('pending', 'in_progress')),
            ('execution_due_at', '<', now),
            '|', ('overdue_notified_at', '=', False), ('overdue_notified_at', '<', cutoff),
        ], limit=100)
        for req in overdue_exec:
            recipients = req.assigned_executor_id or req.executor_user_ids
            if recipients:
                req._tp_notify_internal(
                    recipients,
                    _('Đề nghị quá hạn thực hiện'),
                    _('Đề nghị "%(title)s" đã quá hạn thực hiện (%(due)s).',
                      title=req.title, due=format_dt_local(req.execution_due_at)),
                    event_type='overdue',
                )
            internal(req).write({'overdue_notified_at': now})
        return True

    # ------------------------------------------------------------------ Scope & Filtering helpers
    @api.model
    def _tp_mode_domain(self, mode):
        uid = self.env.uid
        if mode == 'mine':
            return [('requester_user_id', '=', uid)]
        if mode == 'to_approve':
            return [
                ('approval_state', '=', 'pending'),
                ('current_approver_ids', 'in', [uid]),
                ('requester_user_id', '!=', uid),
            ]
        if mode == 'to_execute':
            return [
                ('approval_state', '=', 'approved'),
                ('execution_state', 'in', ('pending', 'in_progress')),
                '|', ('executor_user_ids', 'in', [uid]), ('assigned_executor_id', '=', uid),
            ]
        if mode == 'watching':
            return [
                ('approval_state', '!=', 'draft'),
                '|', ('follower_user_ids', 'in', [uid]),
                '|', ('all_approver_ids', 'in', [uid]),
                '|', ('executor_user_ids', 'in', [uid]), ('assigned_executor_id', '=', uid),
            ]
        if mode == 'admin_all':
            require_request_manager(self.env)
            return ['|', ('requester_user_id', '=', uid), ('approval_state', '!=', 'draft')]
        # overview / all accessible
        return []

    @api.model
    def _tp_build_filter_domain(self, mode, params=None):
        params = params or {}
        dom = list(self._tp_mode_domain(mode))

        # Tab / state filter
        tab = (params.get('tab') or '').strip()
        if tab and tab != 'all':
            if tab in dict(APPROVAL_STATES):
                dom.append(('approval_state', '=', tab))
            elif tab == 'exec_pending':
                dom.extend([('approval_state', '=', 'approved'), ('execution_state', '=', 'pending')])
            elif tab == 'exec_in_progress':
                dom.extend([('approval_state', '=', 'approved'), ('execution_state', '=', 'in_progress')])
            elif tab == 'exec_done':
                dom.extend([('approval_state', '=', 'approved'), ('execution_state', '=', 'done')])
            elif tab == 'overdue':
                dom.append(('is_overdue', '=', True))

        # Type filter
        type_id = params.get('type_id')
        if type_id:
            try:
                dom.append(('type_id', '=', int(type_id)))
            except (TypeError, ValueError):
                pass

        # Approval state dropdown
        approval_state = (params.get('approval_state') or '').strip()
        if approval_state in dict(APPROVAL_STATES):
            dom.append(('approval_state', '=', approval_state))

        # Execution state dropdown
        exec_state = (params.get('execution_state') or '').strip()
        if exec_state in dict(EXECUTION_STATES):
            dom.append(('execution_state', '=', exec_state))

        # Priority
        priority = (params.get('priority') or '').strip()
        if priority in dict(PRIORITIES):
            dom.append(('priority', '=', priority))

        # Department
        dept_id = params.get('department_id')
        if dept_id:
            try:
                dom.append(('department_id', '=', int(dept_id)))
            except (TypeError, ValueError):
                pass

        # Requester
        req_uid = params.get('requester_user_id')
        if req_uid:
            try:
                dom.append(('requester_user_id', '=', int(req_uid)))
            except (TypeError, ValueError):
                pass

        # Overdue flag
        if params.get('overdue_only'):
            dom.append(('is_overdue', '=', True))

        # Date range (submitted_at or create_date in local timezone half-open interval)
        date_from = (params.get('date_from') or '').strip()
        date_to = (params.get('date_to') or '').strip()
        if date_from and date_to and date_from > date_to:
            raise UserError(_('Ngày bắt đầu không được lớn hơn ngày kết thúc.'))
        if date_from:
            dom.append(('create_date', '>=', f'{date_from} 00:00:00'))
        if date_to:
            dom.append(('create_date', '<=', f'{date_to} 23:59:59'))

        # Search text (code, title, requester name/code — Vietnamese tone-insensitive via folded match)
        search_text = (params.get('search') or '').strip()
        if search_text:
            needle = fold_text(search_text)
            candidates = self.search_fetch(dom, ['code', 'title', 'requester_name_snap', 'requester_code_snap'])
            matched_ids = [
                r.id for r in candidates
                if any(needle in fold_text(v) for v in (r.code, r.title, r.requester_name_snap, r.requester_code_snap))
            ]
            dom.append(('id', 'in', matched_ids))

        return dom

    def _tp_serialize_row(self):
        self.ensure_one()
        now = fields.Datetime.now()
        due = self.execution_due_at if (self.approval_state == 'approved' and self.execution_state in ('pending', 'in_progress')) else self.due_at
        overdue = bool(
            (self.approval_state == 'pending' and self.due_at and self.due_at < now)
            or (self.approval_state == 'approved' and self.execution_state in ('pending', 'in_progress')
                and self.execution_due_at and self.execution_due_at < now)
        )
        return {
            'id': self.id,
            'code': self.code,
            'title': self.title,
            'type_id': self.type_id.id,
            'type_code': self.type_id.code,
            'type_name': self.type_id.name,
            'type_icon': self.type_id.icon,
            'type_color': self.type_id.color,
            'handler_kind': self.handler_kind,
            'requester_user_id': self.requester_user_id.id,
            'requester_name': self.requester_name_snap or self.requester_user_id.sudo().name,
            'requester_code': self.requester_code_snap or '',
            'department_id': self.department_id.id or False,
            'department_name': self.department_name_snap or (self.department_id.sudo().name if self.department_id else ''),
            'priority': self.priority,
            'priority_label': PRIORITY_LABELS.get(self.priority, self.priority),
            'approval_state': self.approval_state,
            'approval_state_label': STATE_LABELS.get(self.approval_state, self.approval_state),
            'execution_state': self.execution_state,
            'execution_state_label': EXEC_LABELS.get(self.execution_state, self.execution_state),
            'requires_execution': bool(self.type_id.requires_execution),
            'current_step_name': self.current_step_name or '',
            'current_approvers': [u.name for u in self.current_approver_ids.sudo()],
            'submitted_at': format_dt_local(self.submitted_at),
            'created_at': format_dt_local(self.create_date),
            'due_at': format_dt_local(due),
            'needed_date': format_date_vn(self.needed_date),
            'is_overdue': overdue,
            'version': self.version,
            'url': f'/app/de-nghi/ho-so/{self.id}',
        }

    # ------------------------------------------------------------------ Public RPCs for OWL UI
    @api.model
    def tp_sidebar_counts(self):
        """Role-scoped live counts for sidebar badges and dashboard."""
        uid = self.env.uid
        return {
            'to_approve': self.search_count(self._tp_mode_domain('to_approve')),
            'to_execute': self.search_count(self._tp_mode_domain('to_execute')),
            'mine_pending': self.search_count([('requester_user_id', '=', uid), ('approval_state', '=', 'pending')]),
            'mine_returned': self.search_count([('requester_user_id', '=', uid), ('approval_state', '=', 'returned')]),
            'overdue': self.search_count([
                ('is_overdue', '=', True),
                '|', ('requester_user_id', '=', uid),
                '|', ('current_approver_ids', 'in', [uid]),
                '|', ('executor_user_ids', 'in', [uid]), ('assigned_executor_id', '=', uid),
            ]),
            'is_manager': is_request_manager(self.env),
        }

    @api.model
    def tp_dashboard_data(self, params=None):
        """Overview KPI cards, real Chart.js datasets, and immediate action queue."""
        params = params or {}
        uid = self.env.uid
        counts = self.tp_sidebar_counts()

        # Scope for charts: all accessible requests matching optional period/type filter
        chart_dom = self._tp_build_filter_domain('overview', params)
        records = self.search(chart_dom, order='submitted_at desc, id desc')
        total = len(records)

        # Donut: approval status breakdown (real data only)
        state_order = ['pending', 'returned', 'approved', 'rejected', 'draft', 'withdrawn']
        state_colors = {
            'pending': '#2563EB',
            'returned': '#D97706',
            'approved': '#059669',
            'rejected': '#DC2626',
            'draft': '#94A3B8',
            'withdrawn': '#64748B',
        }
        status_chart = []
        for st in state_order:
            cnt = sum(1 for r in records if r.approval_state == st)
            if cnt > 0:
                status_chart.append({
                    'key': st,
                    'label': STATE_LABELS[st],
                    'count': cnt,
                    'percent': round(cnt * 100.0 / total, 1) if total else 0.0,
                    'color': state_colors[st],
                })

        # Bar: count by request type (real data only)
        type_buckets = {}
        for r in records:
            tid = r.type_id.id
            if tid not in type_buckets:
                type_buckets[tid] = {
                    'type_id': tid,
                    'code': r.type_id.code,
                    'label': r.type_id.name,
                    'color': r.type_id.color or '#2563EB',
                    'count': 0,
                }
            type_buckets[tid]['count'] += 1
        type_chart = sorted(type_buckets.values(), key=lambda x: (-x['count'], x['label']))

        # Immediate action queue: items waiting for me to approve, execute, or revise
        queue_dom = [
            '|', '&', ('approval_state', '=', 'pending'), '&', ('current_approver_ids', 'in', [uid]), ('requester_user_id', '!=', uid),
            '|', '&', ('approval_state', '=', 'approved'), '&', ('execution_state', 'in', ('pending', 'in_progress')),
                 '|', ('executor_user_ids', 'in', [uid]), ('assigned_executor_id', '=', uid),
            '&', ('requester_user_id', '=', uid), ('approval_state', '=', 'returned'),
        ]
        queue_records = self.search(queue_dom, order='due_at asc, id desc', limit=50)
        queue_records = queue_records.sorted(key=lambda r: (not r.is_overdue, r.due_at or datetime.max, -r.id))[:20]
        queue_rows = []
        for rec in queue_records:
            row = rec._tp_serialize_row()
            if rec.approval_state == 'pending' and uid in rec.current_approver_ids.ids and rec.requester_user_id.id != uid:
                row['queue_role'] = 'approve'
                row['queue_role_label'] = 'Cần tôi duyệt'
            elif rec.approval_state == 'approved' and rec.execution_state in ('pending', 'in_progress'):
                row['queue_role'] = 'execute'
                row['queue_role_label'] = 'Cần thực hiện'
            else:
                row['queue_role'] = 'revise'
                row['queue_role_label'] = 'Cần bổ sung'
            queue_rows.append(row)

        types = self.env['tp.request.type'].search([('active', '=', True)], order='sequence, id')
        return {
            'counts': counts,
            'total_accessible': total,
            'status_chart': status_chart,
            'type_chart': type_chart,
            'queue': queue_rows,
            'type_options': [{'id': t.id, 'name': t.name, 'code': t.code} for t in types],
        }

    @api.model
    def tp_list_data(self, mode='mine', params=None):
        """Server-side filtered, paginated list with consistent total & scope-safe filter options."""
        params = params or {}
        dom = self._tp_build_filter_domain(mode, params)
        total = self.search_count(dom)

        page_size = int(params.get('page_size') or 100)
        if page_size not in (10, 20, 50, 100):
            page_size = 100
        page = max(int(params.get('page') or 1), 1)
        max_page = max((total + page_size - 1) // page_size, 1)
        if page > max_page:
            page = max_page
        offset = (page - 1) * page_size

        order = 'due_at asc, submitted_at desc, id desc' if mode in ('to_approve', 'to_execute') else 'submitted_at desc, id desc'
        rows = [r._tp_serialize_row() for r in self.search(dom, order=order, offset=offset, limit=page_size)]

        # Tab counters within mode's mandatory scope (ignoring current tab filter)
        base_dom = self._tp_mode_domain(mode)
        tab_counts = {'all': self.search_count(base_dom)}
        if mode == 'mine':
            for st in ('draft', 'pending', 'returned', 'approved', 'rejected', 'withdrawn'):
                tab_counts[st] = self.search_count(base_dom + [('approval_state', '=', st)])
        elif mode == 'to_approve':
            tab_counts['overdue'] = self.search_count(base_dom + [('is_overdue', '=', True)])
        elif mode == 'to_execute':
            tab_counts['exec_pending'] = self.search_count(base_dom + [('execution_state', '=', 'pending')])
            tab_counts['exec_in_progress'] = self.search_count(base_dom + [('execution_state', '=', 'in_progress')])
            tab_counts['overdue'] = self.search_count(base_dom + [('is_overdue', '=', True)])
        else:
            for st in ('pending', 'returned', 'approved', 'rejected'):
                tab_counts[st] = self.search_count(base_dom + [('approval_state', '=', st)])
            tab_counts['overdue'] = self.search_count(base_dom + [('is_overdue', '=', True)])

        # Scope-safe filter options derived ONLY from accessible rows in this mode (no sudo data leak!)
        scope_recs = self.search_fetch(base_dom, ['type_id', 'department_id', 'requester_user_id'])
        type_ids = sorted(set(scope_recs.mapped('type_id').ids))
        dept_ids = sorted(set(scope_recs.mapped('department_id').ids))
        req_uids = sorted(set(scope_recs.mapped('requester_user_id').ids))

        all_types = self.env['tp.request.type'].search([], order='sequence, id')
        type_opts = [{'id': t.id, 'name': t.name} for t in all_types if (t.active or t.id in type_ids)]
        dept_opts = [{'id': d.id, 'name': d.name} for d in self.env['hr.department'].sudo().browse(dept_ids).sorted('name')]
        req_opts = [{'id': u.id, 'name': u.name} for u in self.env['res.users'].sudo().browse(req_uids).sorted('name')]

        return {
            'mode': mode,
            'rows': rows,
            'total': total,
            'page': page,
            'page_size': page_size,
            'max_page': max_page,
            'tab_counts': tab_counts,
            'options': {
                'types': type_opts,
                'departments': dept_opts,
                'requesters': req_opts,
                'priorities': [{'key': k, 'label': v} for k, v in PRIORITIES],
                'approval_states': [{'key': k, 'label': v} for k, v in APPROVAL_STATES],
                'execution_states': [{'key': k, 'label': v} for k, v in EXECUTION_STATES],
            },
            'is_manager': is_request_manager(self.env),
        }

    @api.model
    def tp_create_bootstrap(self):
        """Bootstrap data for the 'Tạo đề nghị' flow (types, employee info, own devices, projects)."""
        user = self.env.user
        company = self.env.company
        emp = self._tp_own_employee(user, company)

        types = self.env['tp.request.type'].search([('active', '=', True)], order='sequence, id')
        type_cards = []
        for t in types:
            if not t._tp_user_can_submit(user, employee=emp):
                continue
            preview = t._tp_resolve_route_preview(requester_user=user, company=company, employee=emp)
            type_cards.append({
                'id': t.id,
                'code': t.code,
                'name': t.name,
                'description': t.description or '',
                'guidance': t.guidance or '',
                'icon': t.icon or 'assignment',
                'color': t.color or '#2563EB',
                'handler_kind': t.handler_kind,
                'require_reason': t.require_reason,
                'require_attachment': t.require_attachment,
                'allow_attachment': t.allow_attachment,
                'max_attachments': t.max_attachments,
                'require_needed_date': t.require_needed_date,
                'show_project_field': t.show_project_field,
                'default_priority': t.default_priority,
                'requires_execution': t.requires_execution,
                'can_submit_now': preview['can_submit'],
                'missing_reasons': preview['missing_reasons'],
            })

        # Accessible projects ONLY (respecting tp_project / kd record rules, NO sudo!)
        projects = self.env['project.project'].search([('tp_managed', '=', True)], order='name', limit=200)
        project_opts = [{'id': p.id, 'name': f'{p.tp_code} · {p.name}' if p.tp_code else p.name} for p in projects]

        # Active internal colleagues in same company for followers picker (name + dept only, no private HR fields)
        company_emps = self.env['hr.employee'].sudo().search([
            ('company_id', '=', company.id),
            ('active', '=', True),
            ('user_id', '!=', False),
            ('user_id.active', '=', True),
            ('user_id.share', '=', False),
        ], order='name')
        follower_opts = []
        seen_uids = set()
        for ce in company_emps:
            if ce.user_id.id != user.id and ce.user_id.id not in seen_uids:
                seen_uids.add(ce.user_id.id)
                follower_opts.append({
                    'id': ce.user_id.id,
                    'name': ce.name,
                    'department': ce.department_id.name if ce.department_id else '',
                })

        return {
            'requester': {
                'user_id': user.id,
                'name': emp.name if emp else user.name,
                'employee_id': emp.id if emp else False,
                'employee_code': emp.tp_employee_code if emp else '',
                'department_name': emp.department_id.name if emp and emp.department_id else 'Chưa gắn phòng ban',
                'has_employee': bool(emp),
            },
            'types': type_cards,
            'my_equipment': self.tp_my_equipment_options(),
            'equipment_categories': self.tp_equipment_categories(),
            'projects': project_opts,
            'followers': follower_opts,
            'priorities': [{'key': k, 'label': v} for k, v in PRIORITIES],
            'it_categories': [{'key': k, 'label': v} for k, v in IT_CATEGORIES],
            'it_impacts': [{'key': k, 'label': v} for k, v in IT_IMPACTS],
        }

    @api.model
    def tp_preview_route(self, type_id, project_id=False):
        rtype = self.env['tp.request.type'].browse(int(type_id or 0)).exists()
        if not rtype:
            raise UserError(_('Loại đề nghị không tồn tại.'))
        proj = False
        if project_id:
            proj = self.env['project.project'].browse(int(project_id)).exists()
            if proj:
                proj.check_access('read')
        return rtype._tp_resolve_route_preview(
            requester_user=self.env.user,
            company=self.env.company,
            employee=self._tp_own_employee(self.env.user, self.env.company),
            project=proj,
        )

    @api.model
    def tp_save_request(self, payload, submit=False):
        """Create or update a draft/returned request from OWL UI, returning structured field errors if any."""
        payload = payload or {}
        req_id = payload.get('id')
        rtype = self.env['tp.request.type'].browse(int(payload.get('type_id') or 0)).exists()
        if req_id:
            rec = self.browse(int(req_id)).exists()
            if not rec:
                raise UserError(_('Không tìm thấy hồ sơ đề nghị.'))
            rec.check_access('write')
            rtype = rec.type_id
        else:
            rec = self.browse()
            if not rtype or not rtype.active:
                return {'ok': False, 'field_errors': [
                    {'id': 'req_type', 'label': 'Loại đề nghị', 'location': 'Chọn loại đề nghị',
                     'message': 'Vui lòng chọn loại đề nghị hợp lệ.'}
                ]}

        # Parse attendance clocks cleanly
        att_in = _parse_clock_to_float(payload.get('att_requested_in'))
        att_out = _parse_clock_to_float(payload.get('att_requested_out'))

        # Pre-validate required fields for nice inline UX (always re-checked on submit too)
        field_errors = []
        title = (payload.get('title') or '').strip()
        description = (payload.get('description') or '').strip()
        if not title:
            field_errors.append({'id': 'req_title', 'label': 'Tiêu đề đề nghị', 'location': 'Thông tin chung',
                                 'message': 'Vui lòng nhập Tiêu đề đề nghị.'})
        if submit:
            if rtype.require_reason and not description:
                field_errors.append({'id': 'req_description', 'label': 'Nội dung / lý do', 'location': 'Thông tin chung',
                                     'message': 'Vui lòng nhập Nội dung / lý do.'})
            if rtype.require_needed_date and not payload.get('needed_date'):
                field_errors.append({'id': 'req_needed_date', 'label': 'Ngày cần đáp ứng', 'location': 'Thông tin chung',
                                     'message': 'Vui lòng chọn Ngày cần đáp ứng.'})
            if rtype.handler_kind == 'attendance_correction':
                if not payload.get('att_work_date'):
                    field_errors.append({'id': 'req_att_work_date', 'label': 'Ngày công', 'location': 'Điều chỉnh công',
                                         'message': 'Vui lòng chọn Ngày công cần điều chỉnh.'})
                if att_in is None:
                    field_errors.append({'id': 'req_att_in', 'label': 'Giờ vào đúng', 'location': 'Điều chỉnh công',
                                         'message': 'Vui lòng nhập Giờ vào đúng theo định dạng HH:MM.'})
                if att_out is None:
                    field_errors.append({'id': 'req_att_out', 'label': 'Giờ ra đúng', 'location': 'Điều chỉnh công',
                                         'message': 'Vui lòng nhập Giờ ra đúng theo định dạng HH:MM.'})
                elif att_in is not None and att_out <= att_in:
                    field_errors.append({'id': 'req_att_out', 'label': 'Giờ ra đúng', 'location': 'Điều chỉnh công',
                                         'message': 'Giờ ra phải sau giờ vào trong cùng ngày công.'})
            elif rtype.handler_kind == 'equipment_assign':
                if not payload.get('equipment_category_id') and not (payload.get('equipment_desired_spec') or '').strip():
                    field_errors.append({'id': 'req_equip_category', 'label': 'Loại thiết bị cần cấp', 'location': 'Chi tiết thiết bị',
                                         'message': 'Vui lòng chọn Loại thiết bị hoặc nhập cấu hình mong muốn.'})
            elif rtype.handler_kind == 'equipment_swap':
                if not payload.get('equipment_id'):
                    field_errors.append({'id': 'req_equipment_id', 'label': 'Thiết bị đang dùng cần đổi', 'location': 'Chi tiết thiết bị',
                                         'message': 'Vui lòng chọn Thiết bị đang sử dụng cần đổi.'})
            elif rtype.handler_kind == 'equipment_repair':
                if not payload.get('equipment_id'):
                    field_errors.append({'id': 'req_equipment_id', 'label': 'Thiết bị báo hỏng / sửa chữa', 'location': 'Chi tiết thiết bị',
                                         'message': 'Vui lòng chọn Thiết bị gặp sự cố.'})
                if not (payload.get('equipment_issue_detail') or '').strip() and not description:
                    field_errors.append({'id': 'req_equip_issue', 'label': 'Mô tả hiện tượng / lỗi', 'location': 'Chi tiết thiết bị',
                                         'message': 'Vui lòng mô tả hiện tượng hỏng hoặc yêu cầu sửa chữa.'})
            elif rtype.handler_kind == 'equipment_purchase':
                if not payload.get('equipment_category_id') and not (payload.get('equipment_desired_spec') or '').strip():
                    field_errors.append({'id': 'req_equip_category', 'label': 'Loại thiết bị đề xuất mua', 'location': 'Chi tiết mua sắm',
                                         'message': 'Vui lòng chọn Loại thiết bị hoặc ghi cấu hình đề xuất mua.'})
                try:
                    qty = int(payload.get('equipment_quantity') or 0)
                except (TypeError, ValueError):
                    qty = 0
                if qty < 1:
                    field_errors.append({'id': 'req_equip_qty', 'label': 'Số lượng', 'location': 'Chi tiết mua sắm',
                                         'message': 'Vui lòng nhập Số lượng lớn hơn hoặc bằng 1.'})
            elif rtype.handler_kind == 'it_support':
                if not payload.get('it_category'):
                    field_errors.append({'id': 'req_it_category', 'label': 'Nhóm hỗ trợ IT', 'location': 'Chi tiết hỗ trợ IT',
                                         'message': 'Vui lòng chọn Nhóm hỗ trợ IT.'})

        if field_errors:
            return {'ok': False, 'field_errors': field_errors}

        # Special 1-1 bridge for Attendance Correction (single authoritative tp.hr.attendance.correction record!)
        if rtype.handler_kind == 'attendance_correction':
            if not payload.get('att_work_date') or att_in is None or att_out is None:
                return {'ok': False, 'field_errors': [
                    {'id': 'req_att_work_date', 'label': 'Ngày công & giờ vào/ra', 'location': 'Điều chỉnh công',
                     'message': 'Vui lòng nhập đầy đủ Ngày công, Giờ vào và Giờ ra hợp lệ trước khi lưu.'}
                ]}
            rec = self._tp_save_attendance_request(rec, rtype, payload, att_in, att_out, submit=submit)
            return {'ok': True, 'id': rec.id, 'code': rec.code, 'approval_state': rec.approval_state}

        vals = {
            'title': title,
            'description': description or False,
            'priority': payload.get('priority') or rtype.default_priority or 'normal',
            'needed_date': payload.get('needed_date') or False,
            'project_id': int(payload['project_id']) if payload.get('project_id') else False,
            'equipment_id': int(payload['equipment_id']) if payload.get('equipment_id') else False,
            'equipment_category_id': int(payload['equipment_category_id']) if payload.get('equipment_category_id') else False,
            'equipment_quantity': int(payload.get('equipment_quantity') or 1),
            'equipment_desired_spec': (payload.get('equipment_desired_spec') or '').strip() or False,
            'equipment_issue_detail': (payload.get('equipment_issue_detail') or '').strip() or False,
            'it_category': payload.get('it_category') or False,
            'it_device_id': int(payload['it_device_id']) if payload.get('it_device_id') else False,
            'it_urgency_impact': payload.get('it_urgency_impact') or 'self',
        }
        if 'follower_user_ids' in payload:
            fids = [int(x) for x in (payload.get('follower_user_ids') or []) if str(x).isdigit()]
            valid_followers = active_internal_users(self.env['res.users'].browse(fids), company=self.env.company)
            vals['follower_user_ids'] = [Command.set(valid_followers.ids)]

        if rec:
            rec.write(vals)
        else:
            vals['type_id'] = rtype.id
            rec = self.create(vals)

        # Attach any uploaded draft attachment IDs owned by caller
        att_ids = [int(x) for x in (payload.get('attachment_ids') or []) if str(x).isdigit()]
        if att_ids:
            atts = self.env['ir.attachment'].browse(att_ids).exists()
            for att in atts:
                if att.create_uid == self.env.user and (
                    (att.res_model == 'tp.request' and att.res_id == rec.id) or not att.res_model
                ):
                    att.sudo().write({'res_model': 'tp.request', 'res_id': rec.id, 'public': False, 'access_token': False})
            internal(rec).write({'attachment_ids': [Command.link(a.id) for a in atts if a.res_model == 'tp.request' and a.res_id == rec.id]})

        if submit:
            rec.action_submit(expected_version=rec.version)
        return {'ok': True, 'id': rec.id, 'code': rec.code, 'approval_state': rec.approval_state}

    @api.model
    def tp_detail_data(self, request_id):
        """Full authorized detail payload for /app/de-nghi/ho-so/<id>."""
        rec = self.browse(int(request_id or 0)).exists()
        if not rec:
            raise UserError(_('Không tìm thấy hồ sơ đề nghị hoặc bạn không có quyền xem.'))
        rec.check_access('read')

        uid = self.env.uid
        user = self.env.user
        is_owner = rec.requester_user_id.id == uid
        is_mgr = is_request_manager(self.env, company=rec.company_id)

        # Live approver check (for UI action buttons; backend still re-checks under lock!)
        can_approve = False
        can_return = False
        can_reject = False
        if rec.approval_state == 'pending' and not is_owner and rec.current_step_id and rec.current_step_id.state == 'pending':
            step = rec.current_step_id
            if uid in step.eligible_user_ids.ids:
                if step.approver_rule != 'admin_group' or is_live_admin_user(user, company=rec.company_id):
                    can_approve = True
                    can_return = bool(step.can_return)
                    can_reject = bool(step.can_reject and rec.type_id.allow_reject and rec.handler_kind != 'attendance_correction')

        # Attendance correction period lock check for approver UI
        att_period_locked = False
        att_can_lock = False
        if rec.handler_kind == 'attendance_correction' and rec.attendance_correction_id:
            corr = rec.attendance_correction_id
            att_period_locked = bool(corr.tp_period_locked)
            att_can_lock = bool(corr.tp_can_review)
            can_approve = bool(corr.tp_can_review)
            can_return = bool(rec.approval_state == 'pending' and not is_owner and is_live_admin_user(user, company=rec.company_id))
            can_reject = False

        can_edit = bool(is_owner and rec.approval_state in ('draft', 'returned'))
        can_submit = can_edit
        can_withdraw = bool(is_owner and rec.type_id.allow_withdraw and rec.approval_state in ('draft', 'pending', 'returned'))
        can_clone = bool(is_owner and rec.approval_state in ('rejected', 'withdrawn') and rec.type_id.active)
        can_transfer = bool(is_mgr and rec.approval_state == 'pending' and rec.handler_kind != 'attendance_correction')

        can_execute = False
        if rec.approval_state == 'approved' and rec.execution_state in ('pending', 'in_progress'):
            if (uid in rec.executor_user_ids.ids or rec.assigned_executor_id.id == uid
                    or (rec.type_id.executor_mode == 'admin_group' and is_live_admin_user(user, company=rec.company_id))):
                can_execute = True

        # Route preview when draft/returned so requester sees exact route & any missing approvers
        route_preview = None
        if can_edit:
            route_preview = rec.type_id._tp_resolve_route_preview(
                requester_user=rec.requester_user_id,
                company=rec.company_id,
                employee=rec.requester_employee_id,
                project=rec.project_id,
            )

        # Sequential steps (latest active version first, plus archived versions if resubmitted)
        steps = []
        for s in rec.step_ids.sorted(lambda x: (x.request_version, x.sequence, x.id)):
            steps.append({
                'id': s.id,
                'sequence': s.sequence,
                'name': s.name,
                'state': s.state,
                'state_label': dict(STEP_STATES).get(s.state, s.state),
                'approver_rule': s.approver_rule,
                'approver_rule_label': dict(APPROVER_RULES).get(s.approver_rule, s.approver_rule),
                'approval_policy_label': dict(APPROVAL_POLICIES).get(s.approval_policy, ''),
                'eligible_users': [{'id': u.id, 'name': u.name} for u in s.eligible_user_ids.sudo()],
                'decided_by': s.decided_by_id.sudo().name if s.decided_by_id else '',
                'decided_at': format_dt_local(s.decided_at),
                'decision_note': s.decision_note or '',
                'due_at': format_dt_local(s.due_at),
                'request_version': s.request_version,
                'transferred': s.transferred,
            })

        # Attachments (private, verified against res_model/res_id)
        attachments = []
        for att in rec.attachment_ids.sudo():
            if att.res_model == 'tp.request' and att.res_id == rec.id:
                attachments.append({
                    'id': att.id,
                    'name': att.name,
                    'mimetype': att.mimetype or 'application/octet-stream',
                    'file_size': att.file_size or 0,
                    'created_at': format_dt_local(att.create_date),
                    'uploader': att.create_uid.name if att.create_uid else '',
                    'download_url': f'/tp_request/attachment/{att.id}',
                    'can_delete': bool(can_edit and att.create_uid.id == uid),
                })

        # Separate Discussion comments (plain comments, never system state changes)
        comment_subtype = self.env.ref('mail.mt_comment', raise_if_not_found=False)
        comments = []
        if comment_subtype:
            msgs = self.env['mail.message'].sudo().search([
                ('model', '=', 'tp.request'),
                ('res_id', '=', rec.id),
                ('message_type', '=', 'comment'),
                ('subtype_id', '=', comment_subtype.id),
            ], order='date asc, id asc', limit=200)
            for m in msgs:
                comments.append({
                    'id': m.id,
                    'author': m.author_id.name if m.author_id else 'Hệ thống',
                    'author_user_id': m.create_uid.id if m.create_uid else False,
                    'date': format_dt_local(m.date),
                    'body': m.body or '',
                })

        # Immutable system audit history
        history = [{
            'id': h.id,
            'created_at': format_dt_local(h.created_at),
            'actor_name': h.actor_name,
            'action': h.action,
            'action_label': dict(h._fields['action'].selection).get(h.action, h.action),
            'state_before': STATE_LABELS.get(h.state_before, EXEC_LABELS.get(h.state_before, h.state_before)),
            'state_after': STATE_LABELS.get(h.state_after, EXEC_LABELS.get(h.state_after, h.state_after)),
            'step_name': h.step_name or '',
            'note': h.note or '',
            'request_version': h.request_version,
            'result_ref': h.result_ref or '',
        } for h in rec.history_ids]

        # Linked business records (only show clickable internal URL if caller has real module access!)
        is_eq_admin = is_live_admin_user(user, company=rec.company_id)
        linked_records = []
        if rec.attendance_correction_id:
            corr = rec.attendance_correction_id.sudo()
            linked_records.append({
                'kind': 'attendance',
                'label': f'Phiếu điều chỉnh công {corr.name}',
                'status': dict(corr._fields['state'].selection).get(corr.state, corr.state),
                'url': f'/app/cham-cong/dieu-chinh/{corr.id}' if (is_owner or is_eq_admin or user.has_group('hr.group_hr_manager')) else '',
            })
        for mv in rec.equipment_move_ids.sudo():
            linked_records.append({
                'kind': 'equipment_move',
                'label': f'Phiếu thiết bị {mv.name} ({dict(mv._fields["move_type"].selection).get(mv.move_type, mv.move_type)})',
                'status': dict(mv._fields['state'].selection).get(mv.state, mv.state),
                'url': f'/app/thiet-bi/phieu-ban-giao/{mv.id}' if is_eq_admin else '',
            })
        if rec.equipment_repair_id:
            rep = rec.equipment_repair_id.sudo()
            linked_records.append({
                'kind': 'equipment_repair',
                'label': f'Phiếu sửa chữa {rep.tp_code or rep.name}',
                'status': dict(rep._fields['tp_state'].selection).get(rep.tp_state, rep.tp_state),
                'url': f'/app/thiet-bi/sua-chua/{rep.id}' if is_eq_admin else '',
            })
        if rec.equipment_proposal_id:
            prop = rec.equipment_proposal_id.sudo()
            linked_records.append({
                'kind': 'equipment_proposal',
                'label': f'Đề xuất mua sắm {prop.name}',
                'status': dict(prop._fields['review_state'].selection).get(prop.review_state, prop.review_state),
                'url': f'/app/thiet-bi/de-xuat/{prop.id}' if is_eq_admin else '',
            })

        # Eligible stock equipment ONLY for authorized equipment executor
        eligible_stock = []
        if can_execute and is_eq_admin and rec.handler_kind in ('equipment_assign', 'equipment_swap'):
            eligible_stock = rec.tp_eligible_stock_equipment()

        # Transfer candidates for manager
        transfer_candidates = []
        if can_transfer:
            cands = self.env['res.users'].sudo().search([
                ('active', '=', True), ('share', '=', False),
                ('company_ids', 'in', rec.company_id.id),
                ('id', '!=', rec.requester_user_id.id),
            ], order='name')
            transfer_candidates = [{'id': u.id, 'name': u.name} for u in cands if u.has_group('base.group_user')]

        emp_sudo = rec.requester_employee_id.sudo()
        # Project name only if caller has project read access (no leakage to unauthorized followers!)
        project_display = ''
        if rec.project_id:
            try:
                rec.project_id.check_access('read')
                p = rec.project_id
                project_display = f'{p.tp_code} · {p.name}' if p.tp_code else p.name
            except AccessError:
                project_display = 'Dự án nội bộ (giới hạn quyền xem)'

        return {
            'id': rec.id,
            'code': rec.code,
            'title': rec.title,
            'type_id': rec.type_id.id,
            'type_code': rec.type_id.code,
            'type_name': rec.type_id.name,
            'type_icon': rec.type_id.icon,
            'type_color': rec.type_id.color,
            'type_guidance': rec.type_id.guidance or '',
            'handler_kind': rec.handler_kind,
            'type_config_version': rec.type_config_version,
            'version': rec.version,
            'description': rec.description or '',
            'priority': rec.priority,
            'priority_label': PRIORITY_LABELS.get(rec.priority, rec.priority),
            'needed_date': rec.needed_date.isoformat() if rec.needed_date else '',
            'needed_date_display': format_date_vn(rec.needed_date),
            'project_id': rec.project_id.id or False,
            'project_display': project_display,
            'requester': {
                'user_id': rec.requester_user_id.id,
                'name': rec.requester_name_snap or rec.requester_user_id.sudo().name,
                'employee_code': rec.requester_code_snap or '',
                'department_name': rec.department_name_snap or (rec.department_id.sudo().name if rec.department_id else ''),
                'avatar_url': f'/web/image/hr.employee/{emp_sudo.id}/avatar_128' if emp_sudo else f'/web/image/res.users/{rec.requester_user_id.id}/avatar_128',
            },
            'approval_state': rec.approval_state,
            'approval_state_label': STATE_LABELS.get(rec.approval_state, rec.approval_state),
            'execution_state': rec.execution_state,
            'execution_state_label': EXEC_LABELS.get(rec.execution_state, rec.execution_state),
            'requires_execution': bool(rec.type_id.requires_execution),
            'submitted_at': format_dt_local(rec.submitted_at),
            'approved_at': format_dt_local(rec.approved_at),
            'created_at': format_dt_local(rec.create_date),
            'due_at': format_dt_local(rec.due_at),
            'execution_due_at': format_dt_local(rec.execution_due_at),
            'execution_started_at': format_dt_local(rec.execution_started_at),
            'execution_done_at': format_dt_local(rec.execution_done_at),
            'is_overdue': rec.is_overdue,
            'current_step_name': rec.current_step_name or '',
            'current_approvers': [{'id': u.id, 'name': u.name} for u in rec.current_approver_ids.sudo()],
            'executors': [{'id': u.id, 'name': u.name} for u in rec.executor_user_ids.sudo()],
            'assigned_executor': rec.assigned_executor_id.sudo().name if rec.assigned_executor_id else '',
            'followers': [{'id': u.id, 'name': u.name} for u in rec.follower_user_ids.sudo()],
            'return_reason': rec.return_reason or '',
            'reject_reason': rec.reject_reason or '',
            'withdraw_reason': rec.withdraw_reason or '',
            'execution_result': rec.execution_result or '',
            'execution_cancel_reason': rec.execution_cancel_reason or '',
            'source_request_code': rec.source_request_id.code if rec.source_request_id else '',
            'source_request_id': rec.source_request_id.id or False,
            # Domain fields
            'attendance': {
                'work_date': rec.att_work_date.isoformat() if rec.att_work_date else '',
                'work_date_display': format_date_vn(rec.att_work_date),
                'requested_in': _clock_str(rec.att_requested_in),
                'requested_out': _clock_str(rec.att_requested_out),
                'current_in': rec.att_current_in or '—',
                'current_out': rec.att_current_out or '—',
                'period_locked': att_period_locked,
                'can_lock_amend': att_can_lock,
                'correction_code': rec.attendance_correction_id.sudo().name if rec.attendance_correction_id else '',
            },
            'equipment': {
                'equipment_id': rec.equipment_id.id or False,
                'equipment_name': rec.equipment_name_snap or (rec.equipment_id.sudo().display_name if rec.equipment_id else ''),
                'category_id': rec.equipment_category_id.id or False,
                'category_name': rec.equipment_category_id.sudo().name if rec.equipment_category_id else '',
                'quantity': rec.equipment_quantity,
                'desired_spec': rec.equipment_desired_spec or '',
                'issue_detail': rec.equipment_issue_detail or '',
                'fulfilled_equipment_name': rec.fulfilled_equipment_id.sudo().display_name if rec.fulfilled_equipment_id else '',
                'old_equipment_condition_label': dict(OLD_EQUIP_CONDITIONS).get(rec.old_equipment_condition, ''),
                'eligible_stock': eligible_stock,
                'old_conditions': [{'key': k, 'label': v} for k, v in OLD_EQUIP_CONDITIONS],
                'has_repair': bool(rec.equipment_repair_id),
                'has_proposal': bool(rec.equipment_proposal_id),
            },
            'it_support': {
                'category': rec.it_category or '',
                'category_label': dict(IT_CATEGORIES).get(rec.it_category, ''),
                'device_id': rec.it_device_id.id or False,
                'device_name': rec.it_device_id.sudo().display_name if rec.it_device_id else '',
                'impact': rec.it_urgency_impact or 'self',
                'impact_label': dict(IT_IMPACTS).get(rec.it_urgency_impact, ''),
            },
            'steps': steps,
            'route_preview': route_preview,
            'attachments': attachments,
            'comments': comments,
            'history': history,
            'linked_records': linked_records,
            'transfer_candidates': transfer_candidates,
            'permissions': {
                'is_owner': is_owner,
                'is_manager': is_mgr,
                'can_edit': can_edit,
                'can_submit': can_submit,
                'can_withdraw': can_withdraw,
                'can_approve': can_approve,
                'can_return': can_return,
                'can_reject': can_reject,
                'can_execute': can_execute,
                'can_clone': can_clone,
                'can_transfer': can_transfer,
                'can_upload_attachment': bool(can_edit or can_execute),
                'is_equipment_admin': is_eq_admin,
            },
        }

    @api.model
    def tp_post_comment(self, request_id, body):
        """Post a plain discussion comment. Comments NEVER change approval or execution state."""
        rec = self.browse(int(request_id or 0)).exists()
        if not rec:
            raise UserError(_('Không tìm thấy hồ sơ đề nghị.'))
        rec.check_access('read')
        text = (body or '').strip()
        if not text:
            raise UserError(_('Nhập nội dung trao đổi trước khi gửi.'))
        recipients = (rec.requester_user_id | rec.current_approver_ids | rec.assigned_executor_id | rec.follower_user_ids) - self.env.user
        recipients = active_internal_users(recipients, company=rec.company_id)
        rec.with_context(mail_notify_noemail=True, mail_post_autofollow=False).message_post(
            body=Markup('<p>%s</p>') % escape(text),
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            partner_ids=recipients.mapped('partner_id').ids,
        )
        return True

    # ------------------------------------------------------------------ Admin Console RPCs
    @api.model
    def tp_admin_data(self):
        require_request_manager(self.env)
        company = self.env.company
        types = self.env['tp.request.type'].with_context(active_test=False).search([], order='sequence, id')
        rows = []
        for t in types:
            warnings = t._tp_static_config_warnings(company=company)
            rows.append({
                'id': t.id,
                'code': t.code,
                'name': t.name,
                'description': t.description or '',
                'guidance': t.guidance or '',
                'icon': t.icon or 'assignment',
                'color': t.color or '#2563EB',
                'sequence': t.sequence,
                'active': t.active,
                'config_version': t.config_version,
                'handler_kind': t.handler_kind,
                'handler_label': HANDLER_LABELS.get(t.handler_kind, t.handler_kind),
                'submitter_scope': t.submitter_scope,
                'allowed_department_ids': t.allowed_department_ids.ids,
                'allowed_user_ids': t.allowed_user_ids.ids,
                'require_reason': t.require_reason,
                'require_attachment': t.require_attachment,
                'allow_attachment': t.allow_attachment,
                'max_attachments': t.max_attachments,
                'require_needed_date': t.require_needed_date,
                'show_project_field': t.show_project_field,
                'allow_reject': t.allow_reject,
                'allow_return': t.allow_return,
                'allow_withdraw': t.allow_withdraw,
                'sla_hours': t.sla_hours,
                'default_priority': t.default_priority,
                'requires_execution': t.requires_execution,
                'executor_mode': t.executor_mode,
                'executor_user_ids': t.executor_user_ids.ids,
                'executor_department_id': t.executor_department_id.id or False,
                'request_count': t.request_count,
                'is_config_ready': not bool(warnings),
                'warnings': warnings,
                'steps': [{
                    'id': s.id,
                    'sequence': s.sequence,
                    'name': s.name,
                    'approver_rule': s.approver_rule,
                    'approver_user_ids': s.approver_user_ids.ids,
                    'approval_policy': s.approval_policy,
                    'sla_hours': s.sla_hours,
                    'can_return': s.can_return,
                    'can_reject': s.can_reject,
                } for s in t.step_ids.sorted(lambda x: (x.sequence, x.id))],
            })

        users = self.env['res.users'].sudo().search([
            ('active', '=', True), ('share', '=', False), ('company_ids', 'in', company.id),
        ], order='name')
        user_opts = [{'id': u.id, 'name': u.name} for u in users if u.has_group('base.group_user')]
        depts = self.env['hr.department'].sudo().search([('company_id', '=', company.id), ('active', '=', True)], order='name')
        dept_opts = [{'id': d.id, 'name': d.name, 'manager_name': d.manager_id.name if d.manager_id else ''} for d in depts]

        return {
            'types': rows,
            'users': user_opts,
            'departments': dept_opts,
            'handler_kinds': [{'key': k, 'label': v} for k, v in HANDLER_KINDS],
            'submitter_scopes': [{'key': k, 'label': v} for k, v in SUBMITTER_SCOPES],
            'approver_rules': [{'key': k, 'label': v} for k, v in APPROVER_RULES],
            'executor_modes': [{'key': k, 'label': v} for k, v in EXECUTOR_MODES],
            'priorities': [{'key': k, 'label': v} for k, v in PRIORITIES],
        }

    @api.model
    def tp_admin_save_type(self, payload):
        require_request_manager(self.env)
        payload = payload or {}
        type_id = payload.get('id')
        code = (payload.get('code') or '').strip().upper()
        name = (payload.get('name') or '').strip()
        if not code or not name:
            raise ValidationError(_('Vui lòng nhập đầy đủ Mã loại và Tên loại đề nghị.'))

        steps_payload = payload.get('steps') or []
        step_cmds = [Command.clear()]
        for idx, s in enumerate(steps_payload, start=1):
            sname = (s.get('name') or '').strip()
            if not sname:
                raise ValidationError(_('Bước duyệt %s chưa có tên.', idx))
            uids = [int(x) for x in (s.get('approver_user_ids') or []) if str(x).isdigit()]
            step_cmds.append(Command.create({
                'sequence': int(s.get('sequence') or idx * 10),
                'name': sname,
                'approver_rule': s.get('approver_rule') or 'specific_users',
                'approver_user_ids': [Command.set(uids)],
                'approval_policy': 'any_one',
                'sla_hours': float(s.get('sla_hours') or 24.0),
                'can_return': bool(s.get('can_return', True)),
                'can_reject': bool(s.get('can_reject', True)),
            }))

        vals = {
            'code': code,
            'name': name,
            'description': (payload.get('description') or '').strip() or False,
            'guidance': (payload.get('guidance') or '').strip() or False,
            'icon': (payload.get('icon') or 'assignment').strip(),
            'color': (payload.get('color') or '#2563EB').strip(),
            'sequence': int(payload.get('sequence') or 50),
            'handler_kind': payload.get('handler_kind') or 'general',
            'submitter_scope': payload.get('submitter_scope') or 'all_internal',
            'allowed_department_ids': [Command.set([int(x) for x in (payload.get('allowed_department_ids') or []) if str(x).isdigit()])],
            'allowed_user_ids': [Command.set([int(x) for x in (payload.get('allowed_user_ids') or []) if str(x).isdigit()])],
            'require_reason': bool(payload.get('require_reason', True)),
            'require_attachment': bool(payload.get('require_attachment', False)),
            'allow_attachment': bool(payload.get('allow_attachment', True)),
            'max_attachments': int(payload.get('max_attachments') or 10),
            'require_needed_date': bool(payload.get('require_needed_date', False)),
            'show_project_field': bool(payload.get('show_project_field', False)),
            'allow_reject': bool(payload.get('allow_reject', True)),
            'allow_return': bool(payload.get('allow_return', True)),
            'allow_withdraw': bool(payload.get('allow_withdraw', True)),
            'sla_hours': float(payload.get('sla_hours') or 24.0),
            'default_priority': payload.get('default_priority') or 'normal',
            'requires_execution': bool(payload.get('requires_execution', False)),
            'executor_mode': payload.get('executor_mode') or ('admin_group' if payload.get('requires_execution') else 'none'),
            'executor_user_ids': [Command.set([int(x) for x in (payload.get('executor_user_ids') or []) if str(x).isdigit()])],
            'executor_department_id': int(payload['executor_department_id']) if payload.get('executor_department_id') else False,
            'step_ids': step_cmds,
        }
        TypeModel = self.env['tp.request.type'].with_context(active_test=False)
        if type_id:
            rec = TypeModel.browse(int(type_id)).exists()
            if not rec:
                raise UserError(_('Không tìm thấy loại đề nghị.'))
            rec.write(vals)
        else:
            rec = TypeModel.create(vals)
        return {'ok': True, 'id': rec.id, 'config_version': rec.config_version}

    @api.model
    def tp_admin_toggle_type(self, type_id, active):
        require_request_manager(self.env)
        rec = self.env['tp.request.type'].with_context(active_test=False).browse(int(type_id or 0)).exists()
        if not rec:
            raise UserError(_('Không tìm thấy loại đề nghị.'))
        rec.write({'active': bool(active)})
        return {'ok': True, 'active': rec.active}


class TpRequestStep(models.Model):
    _name = 'tp.request.step'
    _description = 'Bước duyệt thực tế của hồ sơ đề nghị'
    _order = 'request_id, request_version, sequence, id'

    request_id = fields.Many2one('tp.request', string='Hồ sơ đề nghị', required=True, ondelete='cascade', index=True, readonly=True)
    company_id = fields.Many2one(related='request_id.company_id', store=True, index=True, readonly=True)
    sequence = fields.Integer(string='Thứ tự', required=True, readonly=True)
    name = fields.Char(string='Tên bước duyệt', required=True, readonly=True)
    approver_rule = fields.Selection(APPROVER_RULES, string='Quy tắc', readonly=True)
    approval_policy = fields.Selection(APPROVAL_POLICIES, string='Cơ chế duyệt', default='any_one', readonly=True)
    eligible_user_ids = fields.Many2many(
        'res.users', 'tp_req_inst_step_user_rel', 'step_id', 'user_id',
        string='Người được phép duyệt', readonly=True,
    )
    state = fields.Selection(STEP_STATES, string='Trạng thái bước', default='waiting', required=True, readonly=True, index=True)
    sla_hours = fields.Float(string='Hạn (giờ)', readonly=True)
    due_at = fields.Datetime(string='Hạn xử lý', readonly=True)
    decided_by_id = fields.Many2one('res.users', string='Người đã quyết định', readonly=True, ondelete='restrict')
    decided_at = fields.Datetime(string='Thời điểm quyết định', readonly=True)
    decision_note = fields.Text(string='Nhận xét / lý do', readonly=True)
    request_version = fields.Integer(string='Phiên bản hồ sơ', default=1, readonly=True)
    can_return = fields.Boolean(default=True, readonly=True)
    can_reject = fields.Boolean(default=True, readonly=True)
    transferred = fields.Boolean(string='Đã chuyển giao', default=False, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if not is_internal(self) and not is_bridge(self):
            raise AccessError(_('Bước duyệt chỉ được tạo tự động khi gửi hồ sơ đề nghị.'))
        return super().create(vals_list)

    def write(self, vals):
        if not is_internal(self) and not is_bridge(self):
            raise AccessError(_('Bước duyệt chỉ thay đổi qua thao tác phê duyệt / chuyển giao hợp lệ.'))
        return super().write(vals)

    def unlink(self):
        if self.env.su and self.env.context.get('_tp_request_cascade_draft') is INTERNAL:
            return super().unlink()
        raise AccessError(_('Không được xóa bước duyệt của hồ sơ.'))


class TpRequestAttachmentGuard(models.Model):
    _inherit = 'ir.attachment'

    def _tp_check_request_attachment_write(self, request_ids):
        reqs = self.env['tp.request'].browse(request_ids)
        reqs.check_access('read')
        uid = self.env.uid
        for rec in reqs:
            is_owner_edit = rec.requester_user_id.id == uid and rec.approval_state in ('draft', 'returned')
            is_exec_edit = (
                rec.approval_state == 'approved'
                and rec.execution_state in ('pending', 'in_progress')
                and (uid in rec.executor_user_ids.ids or rec.assigned_executor_id.id == uid
                     or (rec.type_id.executor_mode == 'admin_group' and is_live_admin_user(self.env.user, company=rec.company_id)))
            )
            if not (is_owner_edit or is_exec_edit):
                raise AccessError(_('Chỉ người gửi (khi Nháp/Trả lại) hoặc người thực hiện (khi đang xử lý) mới được cập nhật tệp đính kèm.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('res_model') == 'tp.request':
                if vals.get('public') or vals.get('access_token'):
                    raise AccessError(_('Tệp đính kèm đề nghị không được chia sẻ công khai hoặc tạo token.'))
                if vals.get('res_id') and not self.env.su:
                    self._tp_check_request_attachment_write([vals['res_id']])
        return super().create(vals_list)

    def write(self, vals):
        protected = self.sudo().filtered(lambda a: a.res_model == 'tp.request')
        if protected and (vals.get('public') or vals.get('access_token') or (set(vals) & {'res_model', 'res_id', 'res_field'} and not self.env.su)):
            raise AccessError(_('Không được công khai hoặc chuyển tệp đính kèm của hồ sơ đề nghị sang nguồn khác.'))
        if protected and not self.env.su:
            self._tp_check_request_attachment_write([a.res_id for a in protected if a.res_id])
        return super().write(vals)

    def unlink(self):
        protected = self.sudo().filtered(lambda a: a.res_model == 'tp.request')
        if protected and not self.env.su:
            self._tp_check_request_attachment_write([a.res_id for a in protected if a.res_id])
        return super().unlink()

    def generate_access_token(self):
        if any(a.res_model == 'tp.request' for a in self.sudo()):
            raise AccessError(_('Tệp đính kèm đề nghị không được tạo token chia sẻ công khai.'))
        return super().generate_access_token()
