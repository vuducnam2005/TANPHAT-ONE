import calendar
import hashlib
import json
import uuid
from datetime import timedelta

from markupsafe import escape

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Domain

_INTERNAL = object()
PERIODS = [('week', 'Tuần'), ('month', 'Tháng'), ('quarter', 'Quý'), ('cumulative', 'Lũy kế')]
# Standard work-status codes; 'partial' (initial completion) never counts as done.
WORK_STATUS = [('todo', 'Chưa làm'), ('in_progress', 'Đang làm'), ('partial', 'Hoàn thành bước đầu'), ('late', 'Chậm tiến độ'), ('paused', 'Tạm hoãn'), ('blocked', 'Vướng mắc'), ('done', 'Hoàn thành')]
# Comment kind is separate from the configurable rating level (tp.report.rating).
REVIEW_KINDS = [('note', 'Nhận xét'), ('needs_change', 'Yêu cầu bổ sung'), ('satisfactory', 'Ghi nhận đạt')]
CAPABILITIES = [('read', 'Xem báo cáo'), ('plan', 'Lập/giao kế hoạch'), ('plan_issue', 'Ban hành kế hoạch'), ('review', 'Rà soát/trả lại'), ('finalize', 'Chốt/điều chỉnh báo cáo'), ('consolidate', 'Tổng hợp/nghĩa vụ'), ('direct', 'Giao chỉ đạo'), ('finance_read', 'Xem số tài chính'), ('finance_enter', 'Cung cấp số tài chính'), ('finance_confirm', 'Xác nhận số tài chính'), ('coverage_exception', 'Ngoại lệ thiếu bao phủ')]


class ReportUsers(models.Model):
    _inherit = 'res.users'

    def _tp_report_domain(self, finance=False, report=False, companies=None):
        self.ensure_one()
        selected = list(companies) if companies is not None else self.env.companies.ids
        today = fields.Date.context_today(self)
        assignments = self.env['tp.report.assignment'].with_context(allowed_company_ids=selected).search([
            ('company_id', 'in', selected),
            ('user_id', '=', self.id), ('active', '=', True), ('date_start', '<=', today),
            '|', ('date_end', '=', False), ('date_end', '>=', today),
            ('capability', 'in', ['finance_read', 'finance_enter', 'finance_confirm'] if finance else ['read', 'review', 'finalize', 'consolidate', 'plan', 'plan_issue', 'direct', 'coverage_exception']),
        ])
        parts = [] if finance else [[('owner_id', '=', self.id), ('company_id', 'in', selected)]]
        for assignment in assignments:
            part = [('company_id', '=', assignment.company_id.id)]
            if finance and assignment.capability == 'finance_enter':
                part.append(('provider_id', '=', self.id))
            if finance and assignment.capability == 'finance_confirm':
                part.append(('status', '=', 'pending'))
            if report and assignment.level != 'all':
                part.append(('level' if report is True else report + '.level', '=', assignment.level))
            if report and assignment.department_id:
                part.append(('level' if report is True else report + '.level', '!=', 'company'))
            if assignment.department_id:
                part.append(('department_id', '=', assignment.department_id.id))
            if assignment.subject_id:
                part.append(('owner_id', '=', assignment.subject_id.id))
            parts.append(part)
        return list(Domain.AND([[('company_id', 'in', selected)], Domain.OR(parts)])) if parts else [('id', '=', 0)]


class Assignment(models.Model):
    _name = 'tp.report.assignment'
    _description = 'Phân quyền báo cáo có phạm vi'
    name = fields.Char(required=True)
    user_id = fields.Many2one('res.users', required=True)
    capability = fields.Selection(CAPABILITIES, required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department')
    subject_id = fields.Many2one('res.users')
    date_start = fields.Date(required=True, default=fields.Date.context_today)
    date_end = fields.Date()
    active = fields.Boolean(default=True)
    reason = fields.Text(required=True)
    level = fields.Selection([('all', 'Tất cả cấp được giao'), ('personal', 'Cá nhân'), ('department', 'Phòng'), ('company', 'Công ty')], default='all', required=True)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and any(vals.get('user_id') == self.env.uid for vals in vals_list):
            raise AccessError(_('Không tự cấp quyền nghiệp vụ cho mình.'))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su and (any(rec.user_id == self.env.user for rec in self) or vals.get('user_id') == self.env.uid):
            raise AccessError(_('Không tự thay đổi quyền nghiệp vụ của mình.'))
        return super().write(vals)

    @api.constrains('date_start', 'date_end', 'department_id', 'company_id')
    def _validate_scope(self):
        for rec in self:
            if rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(_('Hiệu lực không hợp lệ.'))
            if rec.department_id.company_id and rec.department_id.company_id != rec.company_id:
                raise ValidationError(_('Phòng ban khác công ty.'))


class ScopeMixin(models.AbstractModel):
    _name = 'tp.report.scope.mixin'
    _description = 'Phạm vi báo cáo'
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)
    department_id = fields.Many2one('hr.department', index=True)
    owner_id = fields.Many2one('res.users', required=True, default=lambda self: self.env.user, index=True)

    def _has_capability(self, capability):
        self.ensure_one()
        if self.company_id not in self.env.companies:
            return False
        if capability.startswith('finance') and not self.env.user.has_group('tp_reporting.group_reporting_finance'):
            return False
        today = fields.Date.context_today(self)
        domain = [
            ('user_id', '=', self.env.uid), ('active', '=', True), ('capability', '=', capability),
            ('company_id', '=', self.company_id.id), ('date_start', '<=', today),
            '|', ('date_end', '=', False), ('date_end', '>=', today),
            '|', ('department_id', '=', False), ('department_id', '=', self.department_id.id),
            '|', ('subject_id', '=', False), ('subject_id', '=', self.owner_id.id),
        ]
        if self._name == 'tp.report.document':
            domain += [('level', 'in', ['all', self.level])]
            if self.level == 'company':
                domain += [('department_id', '=', False)]
        return bool(self.env['tp.report.assignment'].search_count(domain))

    def _require(self, capability):
        self.check_access('read')
        for rec in self:
            if not rec._has_capability(capability):
                raise AccessError(_('Bạn không có quyền %s trong phạm vi này.') % capability)

    @api.constrains('company_id', 'department_id', 'owner_id')
    def _check_scope(self):
        if self._name in ('tp.report.line', 'tp.report.value', 'tp.report.review'):
            return
        for rec in self:
            self.env.cr.execute('SELECT 1 FROM res_company_users_rel WHERE user_id=%s AND cid=%s', [rec.owner_id.id, rec.company_id.id])
            if not self.env.cr.fetchone() or (rec.department_id.company_id and rec.department_id.company_id != rec.company_id):
                raise ValidationError(_('Đối tượng/phòng phải thuộc công ty báo cáo.'))


class WorkflowMixin(models.AbstractModel):
    _name = 'tp.report.workflow.mixin'
    _inherit = 'tp.report.scope.mixin'
    _description = 'Workflow báo cáo có phiên bản'
    name = fields.Char(required=True)
    period_type = fields.Selection(PERIODS, required=True, default='week', index=True)
    date_start = fields.Date(required=True, index=True)
    date_end = fields.Date(required=True, index=True)
    deadline = fields.Datetime()
    project_id = fields.Many2one('project.project')
    version = fields.Integer(default=1, readonly=True)
    reason = fields.Text()
    event_ids = fields.One2many('tp.report.event', 'document_id')

    @api.constrains('date_start', 'date_end', 'period_type')
    def _check_period(self):
        for rec in self:
            start, end = rec.date_start, rec.date_end
            valid = start <= end
            if rec.period_type == 'week':
                valid = valid and (end - start).days == 6 and start.weekday() == 0
            elif rec.period_type == 'month':
                valid = valid and start.day == 1 and end == start.replace(day=calendar.monthrange(start.year, start.month)[1])
            elif rec.period_type == 'quarter':
                month = start.month + 2
                valid = valid and start.day == 1 and start.month in (1, 4, 7, 10) and end == start.replace(month=month, day=calendar.monthrange(start.year, month)[1])
            if not valid:
                raise ValidationError(_('Khoảng ngày không đúng loại kỳ.'))

    @api.constrains('project_id')
    def _check_source(self):
        for rec in self:
            if rec.project_id:
                rec.project_id.check_access('read')
                if rec.project_id.company_id and rec.project_id.company_id != rec.company_id:
                    raise ValidationError(_('Dự án khác công ty.'))

    def _reason_dialog(self, action):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'res_model': 'tp.report.reason', 'view_mode': 'form', 'target': 'new', 'context': {'default_resource_model': self._name, 'default_resource_id': self.id, 'default_action': action, 'default_expected_version': self.version}}

    def _locked(self, expected_version=None):
        self.ensure_one()
        self.check_access('write')
        self.env.cr.execute('SELECT id FROM "%s" WHERE id=%%s FOR UPDATE' % self._table, [self.id])
        self.invalidate_recordset()
        if expected_version is not None and expected_version != self.version:
            raise UserError(_('Bản ghi đã thay đổi. Vui lòng tải lại.'))

    def _internal_write(self, values):
        return self.with_context(tp_reporting_internal=_INTERNAL).write(values)

    def _transition(self, action, states, target, capability=None, expected_version=None, request_key=None, reason=None):
        self.ensure_one()
        self._locked(self.env.context.get('tp_reporting_expected_version'))
        payload = hashlib.sha256(json.dumps([action, expected_version, reason], sort_keys=True).encode()).hexdigest()
        events = self.env['tp.report.event']
        if request_key:
            old = events.search([('resource_model', '=', self._name), ('resource_id', '=', self.id), ('request_key', '=', request_key)], limit=1)
            if old:
                if old.payload_hash != payload or old.actor_id != self.env.user:
                    raise UserError(_('Mã yêu cầu đã dùng với nội dung khác.'))
                return False
        if expected_version is not None and expected_version != self.version:
            raise UserError(_('Bản ghi đã thay đổi. Vui lòng tải lại.'))
        if self.state not in states:
            raise UserError(_('Trạng thái không cho phép thao tác này.'))
        if capability:
            self._require(capability)
            if self._name == 'tp.report.document' and capability == 'review' and self.reviewer_id != self.env.user:
                raise AccessError(_('Chỉ người rà soát được phân công thực hiện.'))
            if self._name == 'tp.report.document' and self.level == 'personal' and self.owner_id == self.env.user:
                raise AccessError(_('Không tự rà/chốt báo cáo cá nhân.'))
        elif self.owner_id != self.env.user:
            raise AccessError(_('Chỉ người lập được gửi báo cáo.'))
        if action in ('return', 'revise') and not (reason or self.reason or '').strip():
            raise ValidationError(_('Cần nhập lý do.'))
        self._internal_write({'state': target, 'version': self.version + 1, 'reason': reason or self.reason})
        events.with_context(tp_reporting_internal=_INTERNAL).create({
            'name': action, 'resource_model': self._name, 'resource_id': self.id,
            'document_id': self.id if self._name == 'tp.report.document' else False,
            'plan_id': self.id if self._name == 'tp.report.plan' else False,
            'company_id': self.company_id.id, 'department_id': self.department_id.id, 'owner_id': self.owner_id.id,
            'actor_id': self.env.uid, 'version': self.version, 'reason': reason or self.reason,
            'request_key': request_key or False, 'payload_hash': payload,
        })
        if self._name == 'tp.report.document':
            recipient = self.reviewer_id if action == 'submit' else self.owner_id if action in ('return', 'finalize') else self.env['res.users']
            if recipient:
                self.env['bus.bus']._sendone(recipient, 'simple_notification', {'title': _('Báo cáo có cập nhật'), 'message': _('Mở Trung tâm Báo cáo để xem việc cần xử lý.'), 'sticky': True})
        return True

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('tp_reporting_internal') is not _INTERNAL:
            for vals in vals_list:
                if any(key in vals or self.env.context.get('default_' + key) for key in ('current_snapshot_id', 'dependency_ids', 'baseline', 'baseline_history', 'snapshot_ids', 'event_ids')) or vals.get('state', 'draft') != 'draft' or vals.get('version', 1) != 1:
                    raise AccessError(_('Trạng thái chỉ thay đổi qua workflow.'))
        records = super().create(vals_list)
        for rec in records:
            if rec._name == 'tp.report.plan':
                if not (rec.owner_id == self.env.user and rec.period_type == 'week' and rec.proposed):
                    rec._require('plan')
            elif rec.owner_id != self.env.user or rec.level != 'personal':
                rec._require('consolidate')
        return records

    def write(self, vals):
        external = self.env.context.get('tp_reporting_internal') is not _INTERNAL
        if external:
            if not self.env.su and self.env.context.get('tp_reporting_expected_version') is None:
                raise UserError(_('Thiếu phiên bản cập nhật; mở lại biểu mẫu và lưu.'))
            for rec in self:
                rec._locked(self.env.context.get('tp_reporting_expected_version'))
            if {'state', 'version', 'current_snapshot_id', 'dependency_ids', 'baseline', 'baseline_history', 'identity_key'} & vals.keys():
                raise AccessError(_('Không được ghi trực tiếp trạng thái/phiên bản.'))
            for rec in self:
                if rec.state not in ('draft', 'returned'):
                    raise AccessError(_('Bản đã trình/ban hành không sửa trực tiếp.'))
                if rec._name == 'tp.report.plan':
                    if not (rec.owner_id == self.env.user and rec.period_type == 'week' and rec.proposed):
                        rec._require('plan')
                elif rec.owner_id != self.env.user:
                    raise AccessError(_('Không sửa báo cáo người khác.'))
                if {'company_id', 'department_id', 'owner_id', 'level', 'date_start', 'date_end', 'period_type'} & vals.keys():
                    raise AccessError(_('Không đổi đối tượng/phạm vi của hồ sơ đã tạo.'))
        result = super(WorkflowMixin, self.with_context(tp_reporting_draft_batch=_INTERNAL)).write(vals)
        if external:
            for rec in self:
                rec._internal_write({'version': rec.version + 1})
        return result

    def unlink(self):
        for rec in self:
            if rec.state != 'draft' or rec.owner_id != self.env.user:
                raise AccessError(_('Chỉ xóa nháp của mình.'))
        return super().unlink()


class Plan(models.Model):
    _name = 'tp.report.plan'
    _inherit = 'tp.report.workflow.mixin'
    _description = 'Mục tiêu và kế hoạch'
    _order = 'date_start desc, id desc'
    state = fields.Selection([('draft', 'Nháp'), ('submitted', 'Đã trình'), ('returned', 'Trả lại'), ('issued', 'Ban hành')], default='draft', required=True, index=True)
    parent_id = fields.Many2one('tp.report.plan', ondelete='restrict', index=True)
    child_ids = fields.One2many('tp.report.plan', 'parent_id')
    kind = fields.Selection([('quantitative', 'Định lượng'), ('qualitative', 'Định tính')], default='quantitative', required=True)
    target = fields.Float()
    unit = fields.Char()
    output = fields.Text()
    task_id = fields.Many2one('project.task')
    allocated = fields.Float(compute='_compute_allocated')
    remaining = fields.Float(compute='_compute_allocated')
    baseline = fields.Json(readonly=True)
    revision_reason = fields.Text()
    baseline_history = fields.Json(readonly=True)
    baseline_target = fields.Float(compute='_compute_baseline_display')
    baseline_output = fields.Text(compute='_compute_baseline_display')
    baseline_version = fields.Integer(compute='_compute_baseline_display')

    @api.depends('baseline')
    def _compute_baseline_display(self):
        for rec in self:
            data = rec.baseline or {}
            rec.baseline_target = data.get('target', 0)
            rec.baseline_output = data.get('output', '')
            rec.baseline_version = data.get('version', 0)
    event_ids = fields.One2many('tp.report.event', 'plan_id')

    @api.depends('target', 'child_ids.target')
    def _compute_allocated(self):
        for rec in self:
            rec.allocated = sum(rec.child_ids.mapped('target'))
            rec.remaining = rec.target - rec.allocated

    @api.constrains('parent_id', 'period_type', 'company_id', 'date_start', 'date_end', 'unit', 'target')
    def _check_parent(self):
        for rec in self:
            if rec.target < 0:
                raise ValidationError(_('Mục tiêu không âm.'))
            parent = rec.parent_id
            if not parent:
                if rec.period_type != 'quarter':
                    raise ValidationError(_('Tháng/tuần phải có kế hoạch cha.'))
                continue
            if not rec._has_valid_parent(parent):
                raise ValidationError(_('Cha phải đúng công ty, cấp kỳ, phạm vi, đơn vị và khoảng ngày.'))
            chain = parent
            while chain:
                if chain == rec:
                    raise ValidationError(_('Không tạo chu trình kế hoạch.'))
                chain = chain.parent_id

    @api.constrains('task_id', 'project_id')
    def _check_plan_task(self):
        for rec in self:
            if rec.task_id:
                rec.task_id.check_access('read')
                if rec.task_id.project_id and rec.project_id != rec.task_id.project_id:
                    raise ValidationError(_('Task phải thuộc dự án được chọn.'))

    def _has_valid_parent(self, parent):
        level = {'month': 'quarter', 'week': 'month'}
        # A calendar week may cross month boundaries; contributions stay dated in its parent month.
        dates = self.date_start <= parent.date_end and self.date_end >= parent.date_start if self.period_type == 'week' else parent.date_start <= self.date_start <= self.date_end <= parent.date_end
        return parent.company_id == self.company_id and level.get(self.period_type) == parent.period_type and dates and (not parent.department_id or parent.department_id == self.department_id) and self.unit == parent.unit

    def action_submit(self, expected_version=None, request_key=None):
        return self._transition('submit', ('draft', 'returned'), 'submitted', None if self.proposed and self.owner_id == self.env.user else 'plan', expected_version, request_key)

    def action_return(self, reason=None, expected_version=None, request_key=None):
        if not reason:
            return self._reason_dialog('return')
        return self._transition('return', ('submitted',), 'returned', 'plan', expected_version, request_key, reason)

    def action_issue(self, expected_version=None, request_key=None):
        self.ensure_one()
        self._locked()
        if self.parent_id:
            self.parent_id._locked()
            if self.parent_id.state != 'issued':
                raise ValidationError(_('Cần ban hành kế hoạch cha trước.'))
            if sum(self.parent_id.child_ids.filtered(lambda p: p.state == 'issued' or p == self).mapped('target')) > self.parent_id.target:
                raise ValidationError(_('Phân bổ vượt mục tiêu cha.'))
        if sum(self.child_ids.filtered(lambda p: p.state == 'issued').mapped('target')) > self.target:
            raise ValidationError(_('Mục tiêu điều chỉnh thấp hơn phần đã phân bổ.'))
        if self.kind == 'qualitative' and not self.output:
            raise ValidationError(_('Mục tiêu định tính cần đầu ra/tiêu chí.'))
        changed = self._transition('issue', ('submitted',), 'issued', 'plan_issue', expected_version, request_key)
        if changed:
            baseline = {'name': self.name, 'target': self.target, 'unit': self.unit, 'output': self.output, 'version': self.version}
            self._internal_write({'baseline': self.baseline or baseline, 'baseline_history': (self.baseline_history or []) + [baseline]})
        return changed

    def action_revise(self, reason=None, expected_version=None, request_key=None):
        if not reason:
            return self._reason_dialog('revise')
        return self._transition('revise', ('issued',), 'draft', 'plan_issue', expected_version, request_key, reason)

    def action_create_month(self):
        self.ensure_one()
        self._require('plan')
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'view_mode': 'form', 'target': 'current', 'context': {'default_parent_id': self.id, 'default_period_type': 'month', 'default_department_id': self.department_id.id, 'default_unit': self.unit, 'default_company_id': self.company_id.id}}

    def action_create_week(self):
        result = self.action_create_month()
        result['context']['default_period_type'] = 'week'
        return result

    def action_copy_structure(self):
        self.ensure_one()
        self._require('plan')
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'view_mode': 'form', 'target': 'current', 'context': {'default_name': self.name, 'default_target': self.target, 'default_unit': self.unit, 'default_output': self.output, 'default_period_type': self.period_type}}


class Document(models.Model):
    _name = 'tp.report.document'
    _inherit = 'tp.report.workflow.mixin'
    _description = 'Hồ sơ báo cáo'
    _order = 'date_start desc, id desc'
    state = fields.Selection([('draft', 'Nháp'), ('submitted', 'Đã gửi'), ('in_review', 'Đang rà'), ('returned', 'Trả lại'), ('finalized', 'Đã chốt')], default='draft', required=True, index=True)
    level = fields.Selection([('personal', 'Cá nhân'), ('department', 'Phòng ban'), ('company', 'Công ty')], required=True, default='personal', index=True)
    template_id = fields.Many2one('tp.report.template')
    line_ids = fields.One2many('tp.report.line', 'document_id')
    snapshot_ids = fields.One2many('tp.report.snapshot', 'document_id')
    current_snapshot_id = fields.Many2one('tp.report.snapshot', readonly=True, ondelete='restrict')
    dependency_ids = fields.Many2many('tp.report.snapshot', 'tp_report_document_dependency_rel', 'document_id', 'snapshot_id', readonly=True)
    obligation_ids = fields.One2many('tp.report.obligation', 'document_id')
    value_ids = fields.One2many('tp.report.value', 'document_id', groups='tp_reporting.group_reporting_finance')
    summary = fields.Text()
    obstacles = fields.Text()
    recommendations = fields.Text()
    next_plan = fields.Text()
    coverage = fields.Char(compute='_compute_coverage')
    coverage_reason = fields.Text()
    identity_key = fields.Char(required=True, readonly=True, index=True)
    _identity_unique = models.Constraint('UNIQUE(identity_key)', 'Đã có hồ sơ chính cho đối tượng và kỳ này.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            owner = self.env['res.users'].browse(vals.get('owner_id', self.env.uid))
            vals.setdefault('department_id', owner.employee_id.department_id.id)
            level = vals.get('level', 'personal')
            if level == 'company':
                vals['department_id'] = False
            company = vals.get('company_id', self.env.company.id)
            subject = owner.id if level == 'personal' else vals.get('department_id', 0) if level == 'department' else company
            vals['identity_key'] = '%s:%s:%s:%s:%s:%s' % (company, level, subject, vals.get('period_type', 'week'), vals.get('date_start'), vals.get('date_end'))
        return super().create(vals_list)

    @api.constrains('level', 'department_id')
    def _check_department(self):
        for rec in self:
            if rec.level == 'department' and not rec.department_id:
                raise ValidationError(_('Báo cáo phòng cần phòng ban.'))

    def _compute_coverage(self):
        for rec in self:
            obligations = rec._coverage_obligations()
            required = obligations.filtered(lambda o: o.state != 'exempt')
            submitted = required._submission_ids()
            rec.coverage = '%s/%s' % (len(submitted), len(required))

    def _coverage_obligations(self):
        self.ensure_one()
        domain = [('company_id', '=', self.company_id.id), ('date_start', '>=', self.date_start), ('date_end', '<=', self.date_end)]
        if self.level != 'company':
            domain.append(('department_id', '=', self.department_id.id))
        return self.env['tp.report.obligation'].search(domain)

    def _snapshot_payload(self):
        self.ensure_one()
        return {
            'name': self.name, 'level': self.level, 'period_type': self.period_type,
            'date_start': str(self.date_start), 'date_end': str(self.date_end), 'version': self.version,
            'company_id': self.company_id.id, 'company': self.company_id.name,
            'department_id': self.department_id.id, 'department': self.department_id.name,
            'owner_id': self.owner_id.id, 'owner': self.owner_id.name,
            'summary': self.summary or '', 'obstacles': self.obstacles or '', 'recommendations': self.recommendations or '', 'next_plan': self.next_plan or '',
            'template': {'name': self.template_id.name or '', 'version': self.template_id.version, 'sections': [{'name': s.name, 'required': s.required, 'description': s.description or ''} for s in self.template_id.section_ids if s.audience == 'general']},
            'lines': [line._fact() for line in self.line_ids],
            'dependencies': [{'id': s.id, 'document_id': s.document_id.id, 'version': s.version} for s in self.dependency_ids],
            'coverage': self.coverage, 'coverage_reason': self.coverage_reason or '',
        }

    def _take_snapshot(self, kind):
        self.ensure_one()
        snapshot = self.env['tp.report.snapshot'].with_context(tp_reporting_internal=_INTERNAL).create({
            'name': '%s / v%s' % (self.name, self.version), 'document_id': self.id,
            'company_id': self.company_id.id, 'department_id': self.department_id.id, 'owner_id': self.owner_id.id,
            'version': self.version, 'kind': kind, 'payload': json.dumps(self._snapshot_payload(), ensure_ascii=False),
            'dependency_ids': [fields.Command.set(self.dependency_ids.ids)],
        })
        self._internal_write({'current_snapshot_id': snapshot.id})
        # Finance remains in a separately secured immutable relation, never general payload.
        # Freeze only the relation, without reading restricted finance data.
        self.env.cr.execute('INSERT INTO tp_report_value_snapshot_rel (value_id,snapshot_id) SELECT id,%s FROM tp_report_value WHERE document_id=%s ON CONFLICT DO NOTHING', [snapshot.id, self.id])
        self.env['tp.report.value'].invalidate_model(['snapshot_ids'])
        return snapshot

    def action_submit(self, expected_version=None, request_key=None):
        self.ensure_one()
        self._locked()
        if not self.summary and not self.line_ids:
            raise ValidationError(_('Cần nội dung báo cáo hoặc dòng kết quả.'))
        changed = self._transition('submit', ('draft', 'returned'), 'submitted', expected_version=expected_version, request_key=request_key)
        if changed:
            self._take_snapshot('submitted')
        return changed

    def action_review(self, expected_version=None, request_key=None):
        return self._transition('review', ('submitted',), 'in_review', 'review', expected_version, request_key)

    def action_return(self, reason=None, expected_version=None, request_key=None):
        if not reason:
            return self._reason_dialog('return')
        return self._transition('return', ('submitted', 'in_review'), 'returned', 'review', expected_version, request_key, reason)

    def action_finalize(self, expected_version=None, request_key=None):
        self.ensure_one()
        self._locked()
        if self.level != 'personal':
            required = self._coverage_obligations().filtered(lambda o: o.state != 'exempt')
            if len(required._submission_ids()) < len(required):
                self._require('coverage_exception')
                if not self.coverage_reason:
                    raise ValidationError(_('Bao phủ chưa đủ: cần lý do ngoại lệ.'))
        changed = self._transition('finalize', ('submitted', 'in_review'), 'finalized', 'finalize', expected_version, request_key)
        if changed:
            self._take_snapshot('finalized')
        return changed

    def action_revise(self, reason=None, expected_version=None, request_key=None):
        if not reason:
            return self._reason_dialog('revise')
        return self._transition('revise', ('finalized',), 'draft', 'finalize', expected_version, request_key, reason)

    def action_aggregate(self, expected_version=None):
        self.ensure_one()
        self._locked(expected_version)
        self._require('consolidate')
        if self.state not in ('draft', 'returned') or self.level == 'personal':
            raise UserError(_('Chỉ tổng hợp nháp phòng/công ty.'))
        domain = [('company_id', '=', self.company_id.id), ('level', '=', 'department' if self.level == 'company' else 'personal'), ('date_start', '<=', self.date_end), ('date_end', '>=', self.date_start), ('state', '=', 'finalized' if self.level == 'company' else 'submitted')]
        if self.level == 'department':
            domain[-1] = ('state', 'in', ['submitted', 'in_review', 'finalized'])
            domain.append(('department_id', '=', self.department_id.id))
        children = self.search(domain)
        snapshots = children.mapped('current_snapshot_id')
        facts = {}
        for snapshot in snapshots:
            for fact in json.loads(snapshot.payload).get('lines', []):
                if not str(self.date_start) <= fact.get('work_date', '') <= str(self.date_end):
                    continue
                key = (fact['contribution_key'], fact['work_date'], fact['unit'])
                if key in facts and facts[key]['quantity'] != fact['quantity']:
                    raise ValidationError(_('Nguồn chồng lấn khác số lượng; cần đối chiếu trước tổng hợp.'))
                facts[key] = fact
        self.line_ids.with_context(tp_reporting_draft_batch=_INTERNAL).unlink()
        for fact in facts.values():
            allowed = {key: value for key, value in fact.items() if key in self.env['tp.report.line']._fields and key not in ('id', 'document_id')}
            if 'collaborator_ids' in allowed:
                allowed['collaborator_ids'] = [fields.Command.set(allowed['collaborator_ids'])]
            allowed.pop('origin_line_id', None)
            allowed.pop('carry_reason', None)
            self.env['tp.report.line'].with_context(tp_reporting_draft_batch=_INTERNAL, tp_reporting_provenance=_INTERNAL).create(dict(allowed, document_id=self.id))
        self._internal_write({'dependency_ids': [fields.Command.set(snapshots.ids)], 'version': self.version + 1})
        return True


class Line(models.Model):
    _name = 'tp.report.line'
    _description = 'Dòng kết quả báo cáo'
    _inherit = 'tp.report.scope.mixin'
    document_id = fields.Many2one('tp.report.document', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='document_id.company_id', store=True)
    department_id = fields.Many2one(related='document_id.department_id', store=True)
    owner_id = fields.Many2one(related='document_id.owner_id', store=True)
    name = fields.Char(required=True)
    plan_id = fields.Many2one('tp.report.plan')
    project_id = fields.Many2one('project.project')
    task_id = fields.Many2one('project.task')
    work_date = fields.Date(required=True)
    quantity = fields.Float()
    quantity_known = fields.Boolean(default=False, string='Khối lượng đã xác định')
    planned_quantity = fields.Float()
    planned_quantity_known = fields.Boolean(default=False, string='Phần kế hoạch đã phân bổ')
    unit = fields.Char()
    contribution_key = fields.Char(required=True, help='ID đầu ra/nguồn ổn định; cùng nguồn/ngày/đơn vị chỉ được tính một lần.')
    result = fields.Text()
    cause = fields.Text()
    next_action = fields.Text()
    evidence_ids = fields.Many2many('ir.attachment', 'tp_report_line_attachment_rel')
    _fact_unique = models.Constraint('UNIQUE(document_id,contribution_key,work_date,unit)', 'Dòng nguồn bị trùng trong báo cáo.')

    def _fact(self):
        self.ensure_one()
        fact = {key: (str(self[key]) if key == 'work_date' else self[key].id if key.endswith('_id') else self[key]) for key in ('name', 'plan_id', 'project_id', 'task_id', 'work_date', 'quantity', 'unit', 'contribution_key', 'result', 'cause', 'next_action')}
        fact['quantity'] = self.quantity if self.quantity_known else None
        fact['quantity_known'] = self.quantity_known
        fact['planned_quantity'] = self.planned_quantity if self.planned_quantity_known else None
        fact['planned_quantity_known'] = self.planned_quantity_known
        fact['variance'] = self.quantity - self.planned_quantity if self.quantity_known and self.planned_quantity_known else None
        return fact

    def _check_draft(self):
        documents = self.mapped('document_id')
        documents.check_access('write')
        if documents and self.env.context.get('tp_reporting_draft_batch') is not _INTERNAL:
            self.env.cr.execute('SELECT id FROM tp_report_document WHERE id=ANY(%s) ORDER BY id FOR UPDATE', [documents.ids])
            documents.invalidate_recordset()
        for rec in self:
            doc = rec.document_id
            if doc.state not in ('draft', 'returned') or doc.owner_id != self.env.user:
                raise AccessError(_('Chỉ người lập sửa dòng báo cáo nháp.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'quantity' in vals:
                vals.setdefault('quantity_known', True)
        records = super().create(vals_list)
        records._check_draft()
        if self.env.context.get('tp_reporting_draft_batch') is not _INTERNAL:
            for doc in records.mapped('document_id'):
                doc._internal_write({'version': doc.version + 1})
        return records

    def write(self, vals):
        self._check_draft()
        if 'quantity' in vals:
            vals.setdefault('quantity_known', True)
        batch = self.env.context.get('tp_reporting_draft_batch') is _INTERNAL
        if not batch:
            if not self.env.su and self.env.context.get('tp_reporting_expected_version') is None:
                raise UserError(_('Thiếu phiên bản cập nhật dòng; mở lại biểu mẫu.'))
            for doc in self.mapped('document_id'):
                doc._locked(self.env.context.get('tp_reporting_expected_version'))
        if 'document_id' in vals:
            raise AccessError(_('Không chuyển dòng sang báo cáo khác.'))
        result = super().write(vals)
        if not batch:
            for doc in self.mapped('document_id'):
                doc._internal_write({'version': doc.version + 1})
        return result

    def unlink(self):
        self._check_draft()
        documents = self.mapped('document_id')
        batch = self.env.context.get('tp_reporting_draft_batch') is _INTERNAL
        if not batch and not self.env.su:
            expected = self.env.context.get('tp_reporting_expected_version')
            if expected is None:
                raise UserError(_('Thiếu phiên bản xóa dòng; mở lại biểu mẫu.'))
            for doc in documents:
                doc._locked(expected)
        result = super().unlink()
        if not batch:
            for doc in documents:
                doc._internal_write({'version': doc.version + 1})
        return result

    @api.constrains('work_date', 'document_id', 'plan_id', 'task_id', 'project_id', 'evidence_ids')
    def _validate_fact(self):
        for rec in self:
            doc = rec.document_id
            if not doc.date_start <= rec.work_date <= doc.date_end:
                raise ValidationError(_('Ngày kết quả phải nằm trong kỳ.'))
            if rec.plan_id:
                rec.plan_id.check_access('read')
                parent = rec.plan_id.parent_id if rec.plan_id.period_type == 'week' else rec.plan_id
                if rec.plan_id.company_id != doc.company_id or not parent.date_start <= rec.work_date <= parent.date_end or rec.unit != rec.plan_id.unit:
                    raise ValidationError(_('Kết quả phải đúng phạm vi/ngày/đơn vị kế hoạch.'))
            for source in (rec.project_id, rec.task_id, rec.evidence_ids):
                if source:
                    source.check_access('read')
            for attachment in rec.evidence_ids:
                if not attachment.res_id and attachment.create_uid == self.env.user and not attachment.public and not attachment.access_token:
                    attachment.with_context(tp_reporting_internal=_INTERNAL).write({'res_model': 'tp.report.line', 'res_id': rec.id})
                if attachment.public or attachment.access_token or attachment.res_model not in ('tp.report.line', 'tp.report.document') or attachment.res_id not in (rec.id, doc.id):
                    raise ValidationError(_('Minh chứng phải là tệp riêng tư của dòng/báo cáo này, không dùng tệp public/token/nguồn ngoài.'))


class Snapshot(models.Model):
    _name = 'tp.report.snapshot'
    _inherit = 'tp.report.scope.mixin'
    _description = 'Phiên bản báo cáo bất biến'
    name = fields.Char(required=True)
    document_id = fields.Many2one('tp.report.document', required=True, ondelete='restrict')
    version = fields.Integer(required=True)
    kind = fields.Selection([('submitted', 'Đã gửi'), ('finalized', 'Đã chốt')], required=True)
    payload = fields.Text(required=True)
    dependency_ids = fields.Many2many('tp.report.snapshot', 'tp_report_snapshot_dependency_rel', 'snapshot_id', 'dependency_id')
    _version_unique = models.Constraint('UNIQUE(document_id,version)', 'Phiên bản đã tồn tại.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('tp_reporting_internal') is not _INTERNAL:
            raise AccessError(_('Snapshot chỉ tạo qua workflow.'))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(_('Không sửa snapshot.'))

    def unlink(self):
        raise AccessError(_('Không xóa snapshot.'))


class Event(models.Model):
    _name = 'tp.report.event'
    _inherit = 'tp.report.scope.mixin'
    _description = 'Lịch sử báo cáo'
    _order = 'id desc'
    name = fields.Char(required=True)
    resource_model = fields.Char(required=True)
    resource_id = fields.Integer(required=True)
    document_id = fields.Many2one('tp.report.document', ondelete='restrict')
    plan_id = fields.Many2one('tp.report.plan', ondelete='restrict')
    actor_id = fields.Many2one('res.users', required=True)
    version = fields.Integer()
    reason = fields.Text()
    request_key = fields.Char(index=True)
    payload_hash = fields.Char()
    _request_unique = models.Constraint('UNIQUE(resource_model,resource_id,request_key)', 'Yêu cầu đã được xử lý.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('tp_reporting_internal') is not _INTERNAL:
            raise AccessError(_('Lịch sử chỉ tạo qua workflow.'))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(_('Lịch sử bất biến.'))

    def unlink(self):
        raise AccessError(_('Lịch sử bất biến.'))


class Template(models.Model):
    _name = 'tp.report.template'
    _description = 'Mẫu báo cáo'
    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    version = fields.Integer(default=1, required=True)
    level = fields.Selection([('personal', 'Cá nhân'), ('department', 'Phòng'), ('company', 'Công ty')], required=True)
    period_type = fields.Selection(PERIODS)
    active = fields.Boolean(default=True)
    section_ids = fields.One2many('tp.report.section', 'template_id')
    _code_version_unique = models.Constraint('UNIQUE(code,version)', 'Mã và phiên bản mẫu đã tồn tại.')


class Section(models.Model):
    _name = 'tp.report.section'
    _description = 'Phần mẫu báo cáo'
    _order = 'sequence,id'
    name = fields.Char(required=True)
    template_id = fields.Many2one('tp.report.template', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    required = fields.Boolean()
    audience = fields.Selection([('general', 'Thông thường'), ('finance', 'Tài chính')], default='general', required=True)
    description = fields.Text()


class Obligation(models.Model):
    _name = 'tp.report.obligation'
    _inherit = 'tp.report.scope.mixin'
    _description = 'Nghĩa vụ nộp báo cáo'
    name = fields.Char(required=True)
    period_type = fields.Selection(PERIODS, required=True)
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    deadline = fields.Datetime()
    extended_deadline = fields.Datetime()
    state = fields.Selection([('required', 'Phải nộp'), ('exempt', 'Được miễn')], default='required', required=True)
    reason = fields.Text()
    document_id = fields.Many2one('tp.report.document', ondelete='restrict')
    status = fields.Selection([('required', 'Chưa nộp'), ('submitted', 'Đã nộp'), ('late', 'Quá hạn'), ('exempt', 'Miễn')], compute='_compute_status', search='_search_status')
    _obligation_unique = models.Constraint('UNIQUE(company_id,owner_id,period_type,date_start,date_end)', 'Nghĩa vụ đã tồn tại.')

    def _submission_ids(self):
        self.check_access('read')
        if not self:
            return set()
        self.env.cr.execute('SELECT o.id FROM tp_report_obligation o JOIN tp_report_document d ON d.id=o.document_id WHERE o.id=ANY(%s) AND d.current_snapshot_id IS NOT NULL', [self.ids])
        return {row[0] for row in self.env.cr.fetchall()}

    def _has_submission(self):
        self.ensure_one()
        return self.id in self._submission_ids()

    @api.depends('state', 'document_id.current_snapshot_id', 'deadline', 'extended_deadline')
    def _compute_status(self):
        now = fields.Datetime.now()
        submissions = self._submission_ids()
        for rec in self:
            due = rec.extended_deadline or rec.deadline
            rec.status = 'exempt' if rec.state == 'exempt' else 'submitted' if rec.id in submissions else 'late' if due and due < now else 'required'

    @api.model
    def _search_status(self, operator, value):
        if operator not in ('=', '!=', 'in', 'not in'):
            raise UserError(_('Toán tử không hỗ trợ.'))
        values = value if isinstance(value, list) else [value]
        ids = self.search([]).filtered(lambda rec: rec.status in values).ids
        return [('id', 'not in' if operator in ('!=', 'not in') else 'in', ids)]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._require('consolidate')
        return records

    def write(self, vals):
        self._require('consolidate')
        if any(key in vals for key in ('state', 'extended_deadline')) and not vals.get('reason') and not all(self.mapped('reason')):
            raise ValidationError(_('Miễn/gia hạn cần lý do.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(_('Không xóa nghĩa vụ; miễn có lý do để giữ mẫu số lịch sử.'))

    def action_exempt(self):
        return self.write({'state': 'exempt'})

    def action_extend(self):
        self._require('consolidate')
        for rec in self:
            if not rec.extended_deadline or not rec.reason:
                raise ValidationError(_('Nhập hạn gia hạn và lý do.'))
        return True

    def action_create_report(self):
        self.ensure_one()
        if self.owner_id != self.env.user:
            raise AccessError(_('Chỉ tạo báo cáo của mình.'))
        self.check_access('read')
        self.env.cr.execute('SELECT id FROM tp_report_obligation WHERE id=%s FOR UPDATE', [self.id])
        self.invalidate_recordset()
        if self.document_id:
            report = self.document_id
        else:
            report = self.env['tp.report.document'].create({'name': self.name, 'owner_id': self.owner_id.id, 'company_id': self.company_id.id, 'department_id': self.department_id.id, 'period_type': self.period_type, 'date_start': self.date_start, 'date_end': self.date_end, 'deadline': self.extended_deadline or self.deadline})
            choices = report.get_reviewer_choices()
            if len(choices) == 1:
                report.with_context(tp_reporting_expected_version=report.version).write({'reviewer_id': choices[0]['id']})
            # Link is derived from the immutable identity, not supplied by the caller.
            super().write({'document_id': report.id})
        return {'type': 'ir.actions.act_window', 'res_model': 'tp.report.document', 'res_id': report.id, 'view_mode': 'form'}

    @api.constrains('document_id', 'date_start', 'date_end', 'owner_id')
    def _check_document(self):
        for rec in self:
            doc = rec.document_id
            if rec.date_start > rec.date_end or (doc and (doc.owner_id != rec.owner_id or doc.company_id != rec.company_id or doc.date_start != rec.date_start or doc.date_end != rec.date_end or doc.period_type != rec.period_type)):
                raise ValidationError(_('Báo cáo không khớp nghĩa vụ.'))


class Schedule(models.Model):
    _name = 'tp.report.schedule'
    _description = 'Lịch báo cáo — cấu hình kỹ thuật'
    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department')
    period_type = fields.Selection(PERIODS, default='week', required=True)
    timezone = fields.Char(default='Asia/Saigon', required=True)
    deadline_days = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    reminders_enabled = fields.Boolean(default=False)
    date_start = fields.Date()
    date_end = fields.Date()
    user_ids = fields.Many2many('res.users')

    def action_remind(self):
        for rec in self:
            if not rec.reminders_enabled:
                raise UserError(_('Lịch chưa bật nhắc trong ứng dụng.'))
            obligations = self.env['tp.report.obligation'].search([('company_id', '=', rec.company_id.id), ('owner_id', 'in', rec.user_ids.ids), ('date_start', '=', rec.date_start), ('date_end', '=', rec.date_end), ('state', '=', 'required')])
            obligations._require('consolidate')
            submissions = obligations._submission_ids()
            for obligation in obligations.filtered(lambda item: item.id not in submissions):
                self.env['bus.bus']._sendone(obligation.owner_id, 'simple_notification', {'title': _('Nhắc hạn báo cáo'), 'message': _('Bạn có nghĩa vụ báo cáo cần xử lý. Mở Báo cáo → Báo cáo của tôi.'), 'sticky': True})
        return True

    def action_generate_obligations(self):
        for rec in self:
            if not rec.date_start or not rec.date_end:
                raise ValidationError(_('Chọn khoảng kỳ trước khi tạo nghĩa vụ.'))
            for user in rec.user_ids:
                scope = self.env['tp.report.obligation'].new({'company_id': rec.company_id.id, 'department_id': rec.department_id.id, 'owner_id': user.id})
                scope._require('consolidate')
                domain = [('company_id', '=', rec.company_id.id), ('owner_id', '=', user.id), ('period_type', '=', rec.period_type), ('date_start', '=', rec.date_start), ('date_end', '=', rec.date_end)]
                if not self.env['tp.report.obligation'].search_count(domain):
                    self.env['tp.report.obligation'].create({'name': '%s / %s' % (rec.name, user.name), 'company_id': rec.company_id.id, 'department_id': rec.department_id.id, 'owner_id': user.id, 'period_type': rec.period_type, 'date_start': rec.date_start, 'date_end': rec.date_end, 'deadline': fields.Datetime.to_datetime(rec.date_end) + timedelta(days=rec.deadline_days, hours=10)})
        return True


class Metric(models.Model):
    _name = 'tp.report.metric'
    _description = 'Chỉ tiêu tài chính — định nghĩa riêng'
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    unit = fields.Char(required=True)
    method = fields.Selection([('flow', 'Phát sinh'), ('stock', 'Tại thời điểm'), ('milestone', 'Mốc')], default='flow', required=True)
    currency_id = fields.Many2one('res.currency', required=True, default=lambda self: self.env.company.currency_id)
    tax_basis = fields.Selection([('before', 'Trước thuế'), ('after', 'Sau thuế'), ('na', 'Không áp dụng')], default='na', required=True)
    active = fields.Boolean(default=True)
    definition = fields.Text(required=True)
    _metric_unique = models.Constraint('UNIQUE(code)', 'Mã chỉ tiêu đã tồn tại.')

    def write(self, vals):
        for rec in self:
            self.env.cr.execute('SELECT 1 FROM tp_report_value v JOIN tp_report_value_snapshot_rel r ON r.value_id=v.id WHERE v.metric_id=%s LIMIT 1', [rec.id])
            if self.env.cr.fetchone():
                raise AccessError(_('Định nghĩa đã dùng trong snapshot bất biến; tạo mã chỉ tiêu mới.'))
        return super().write(vals)


class Value(models.Model):
    _name = 'tp.report.value'
    _inherit = 'tp.report.scope.mixin'
    _description = 'Giá trị tài chính có nguồn — quyền tách biệt'
    name = fields.Char(required=True)
    document_id = fields.Many2one('tp.report.document', required=True, ondelete='restrict')
    company_id = fields.Many2one(related='document_id.company_id', store=True)
    department_id = fields.Many2one(related='document_id.department_id', store=True)
    owner_id = fields.Many2one(related='document_id.owner_id', store=True)
    metric_id = fields.Many2one('tp.report.metric', required=True)
    amount = fields.Monetary(currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', required=True, default=lambda self: self.env.company.currency_id)
    tax_basis = fields.Selection([('before', 'Trước thuế'), ('after', 'Sau thuế'), ('na', 'Không áp dụng')], default='na', required=True)
    status = fields.Selection([('missing', 'Chưa có nguồn'), ('estimated', 'Ước lượng'), ('pending', 'Chờ xác nhận'), ('confirmed', 'Đã xác nhận'), ('not_applicable', 'Không áp dụng'), ('no_activity', 'Không phát sinh')], default='missing', required=True)
    source_reference = fields.Char()
    source_date = fields.Date()
    provider_id = fields.Many2one('res.users', required=True, default=lambda self: self.env.user)
    confirmer_id = fields.Many2one('res.users', readonly=True)
    coverage_key = fields.Char(required=True)
    snapshot_ids = fields.Many2many('tp.report.snapshot', 'tp_report_value_snapshot_rel', 'value_id', 'snapshot_id', readonly=True)
    evidence_ids = fields.Many2many('ir.attachment', 'tp_report_value_attachment_rel')
    _value_unique = models.Constraint('UNIQUE(document_id,metric_id,coverage_key,currency_id,tax_basis)', 'Nguồn chỉ tiêu chồng lấn; cần đối chiếu.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('status', self.env.context.get('default_status')) == 'confirmed' or vals.get('confirmer_id') or vals.get('snapshot_ids') or self.env.context.get('default_confirmer_id') or self.env.context.get('default_snapshot_ids'):
                raise AccessError(_('Xác nhận phải qua action.'))
        records = super().create(vals_list)
        records._require('finance_enter')
        for rec in records:
            if rec.document_id.state not in ('draft', 'returned') or rec.provider_id != self.env.user:
                raise AccessError(_('Chỉ nhập nguồn của mình trên nháp.'))
        return records

    def write(self, vals):
        if self.env.context.get('tp_reporting_internal') is not _INTERNAL:
            self._require('finance_enter')
            if {'status', 'confirmer_id', 'snapshot_ids', 'document_id', 'provider_id'} & vals.keys():
                if set(vals) != {'status'} or vals['status'] == 'confirmed':
                    raise AccessError(_('Không ghi trực tiếp xác nhận/phạm vi.'))
            if any(rec.snapshot_ids or rec.status == 'confirmed' or rec.document_id.state not in ('draft', 'returned') for rec in self):
                raise AccessError(_('Nguồn đã gửi/xác nhận bất biến; tạo nguồn kỳ/revision mới.'))
        return super().write(vals)

    def unlink(self):
        self._require('finance_enter')
        if any(rec.snapshot_ids or rec.status == 'confirmed' for rec in self):
            raise AccessError(_('Không xóa số đã xác nhận/gửi.'))
        return super().unlink()

    def action_confirm(self):
        for rec in self:
            rec.check_access('write')
            rec._require('finance_confirm')
            self.env.cr.execute('SELECT state FROM tp_report_document WHERE id=%s FOR UPDATE', [rec.document_id.id])
            state = self.env.cr.fetchone()[0]
            if rec.snapshot_ids or state not in ('draft', 'returned'):
                raise AccessError(_('Không xác nhận lại nguồn đã gửi.'))
            if rec.provider_id == self.env.user:
                raise AccessError(_('Không tự xác nhận số mình cung cấp.'))
            if not rec.source_reference or not rec.source_date or not rec.evidence_ids:
                raise ValidationError(_('Cần nguồn, ngày nguồn và minh chứng.'))
            rec.evidence_ids.check_access('read')
            if any(att.public or att.access_token or att.res_model != 'tp.report.value' or att.res_id != rec.id for att in rec.evidence_ids):
                raise ValidationError(_('Minh chứng tài chính phải riêng tư và thuộc đúng báo cáo/giá trị.'))
            if rec.currency_id != rec.metric_id.currency_id or rec.tax_basis != rec.metric_id.tax_basis:
                raise ValidationError(_('Đơn vị tiền/cơ sở thuế không khớp định nghĩa.'))
            self.env.cr.execute('SELECT id FROM tp_report_metric WHERE id=%s FOR UPDATE', [rec.metric_id.id])
            self.env.cr.execute('''SELECT 1 FROM tp_report_value v JOIN tp_report_document d ON d.id=v.document_id JOIN tp_report_document current_doc ON current_doc.id=%s WHERE v.id!=%s AND v.status='confirmed' AND v.company_id=%s AND v.metric_id=%s AND v.coverage_key=%s AND d.date_start<=current_doc.date_end AND d.date_end>=current_doc.date_start LIMIT 1''', [rec.document_id.id, rec.id, rec.company_id.id, rec.metric_id.id, rec.coverage_key])
            if self.env.cr.fetchone():
                raise ValidationError(_('Nguồn bao phủ đã được xác nhận ở báo cáo giao kỳ; cần đối chiếu nguồn.'))
            if rec.status != 'pending':
                raise ValidationError(_('Chỉ xác nhận nguồn đang chờ.'))
            rec.with_context(tp_reporting_internal=_INTERNAL).write({'status': 'confirmed', 'confirmer_id': self.env.uid})
        return True


class Directive(models.Model):
    _name = 'tp.report.directive'
    _inherit = 'tp.report.scope.mixin'
    _description = 'Chỉ đạo và việc cần xử lý'
    name = fields.Char(required=True)
    document_id = fields.Many2one('tp.report.document', required=True, ondelete='restrict')
    deadline = fields.Datetime()
    state = fields.Selection([('open', 'Mới'), ('in_progress', 'Đang xử lý'), ('done', 'Hoàn thành')], default='open', required=True)
    description = fields.Text()
    task_id = fields.Many2one('project.task', readonly=True)
    project_id = fields.Many2one('project.project')
    reason = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('state', 'open') != 'open' or vals.get('task_id'):
                raise AccessError(_('Tạo chỉ đạo ở trạng thái mới.'))
        records = super().create(vals_list)
        for rec in records:
            rec.document_id._require('direct')
            if rec.company_id != rec.document_id.company_id:
                raise ValidationError(_('Chỉ đạo phải cùng công ty báo cáo.'))
        return records

    def write(self, vals):
        for rec in self:
            if rec.owner_id != self.env.user:
                rec.document_id._require('direct')
            if self.env.context.get('tp_reporting_internal') is not _INTERNAL and {'state', 'task_id', 'company_id', 'department_id', 'owner_id', 'document_id'} & vals.keys():
                raise AccessError(_('Dùng action để cập nhật việc.'))
        return super().write(vals)

    def action_start(self):
        for rec in self:
            if rec.owner_id != self.env.user or rec.state != 'open':
                raise AccessError(_('Chỉ người nhận bắt đầu việc mới.'))
        return self.with_context(tp_reporting_internal=_INTERNAL).write({'state': 'in_progress'})

    def action_done(self):
        for rec in self:
            if rec.owner_id != self.env.user or rec.state != 'in_progress':
                raise AccessError(_('Chỉ người nhận hoàn thành việc đang xử lý.'))
        return self.with_context(tp_reporting_internal=_INTERNAL).write({'state': 'done'})

    def action_create_task(self):
        self.ensure_one()
        self.document_id._require('direct')
        if not self.project_id:
            raise ValidationError(_('Chọn dự án hoặc theo dõi chỉ đạo ngay tại đây.'))
        self.project_id.check_access('read')
        self.env.cr.execute('SELECT id FROM tp_report_directive WHERE id=%s FOR UPDATE', [self.id])
        self.invalidate_recordset()
        if not self.task_id:
            task = self.env['project.task'].create({'name': self.name, 'project_id': self.project_id.id, 'user_ids': [fields.Command.set(self.owner_id.ids)], 'description': self.description})
            self.with_context(tp_reporting_internal=_INTERNAL).write({'task_id': task.id})
        return {'type': 'ir.actions.act_window', 'res_model': 'project.task', 'res_id': self.task_id.id, 'view_mode': 'form'}


class ReportReason(models.TransientModel):
    _name = 'tp.report.reason'
    _description = 'Lý do trả lại/điều chỉnh'
    resource_model = fields.Selection([('tp.report.plan', 'Kế hoạch'), ('tp.report.document', 'Báo cáo')], required=True)
    resource_id = fields.Integer(required=True)
    action = fields.Selection([('return', 'Trả lại'), ('revise', 'Điều chỉnh')], required=True)
    reason = fields.Text(required=True)
    expected_version = fields.Integer(required=True)

    def action_apply(self):
        self.ensure_one()
        target = self.env[self.resource_model].browse(self.resource_id).exists()
        if not target:
            raise UserError(_('Bản ghi không còn tồn tại.'))
        getattr(target, 'action_' + self.action)(reason=self.reason, expected_version=self.expected_version, request_key='reason-%s' % self.id)
        return {'type': 'ir.actions.act_window_close'}


class PlanActual(models.Model):
    _inherit = 'tp.report.plan'

    def _report_actual(self, date_start=None, date_end=None):
        self.ensure_one()
        self.check_access('read')
        plans = self.search([('id', 'child_of', self.id)]) if self._parent_store else self
        if not self._parent_store:
            frontier = self.child_ids
            while frontier:
                plans |= frontier
                frontier = frontier.mapped('child_ids') - plans
        start, end = str(date_start or self.date_start), str(date_end or self.date_end)
        documents = self.env['tp.report.document'].search([('level', '=', 'personal'), ('state', 'in', ['submitted', 'in_review', 'finalized']), ('company_id', '=', self.company_id.id), ('date_start', '<=', date_end or self.date_end), ('date_end', '>=', date_start or self.date_start)])
        facts = {}
        for snapshot in documents.mapped('current_snapshot_id'):
            for fact in json.loads(snapshot.payload).get('lines', []):
                if fact.get('plan_id') in plans.ids and start <= fact.get('work_date', '') <= end and fact.get('unit') == self.unit and fact.get('quantity') is not None:
                    key = (fact.get('contribution_key'), fact.get('work_date'), fact.get('unit'))
                    if key in facts and facts[key] != fact.get('quantity', 0):
                        raise ValidationError(_('Nguồn chồng lấn có kết quả khác nhau.'))
                    facts[key] = fact.get('quantity', 0)
        return [{'unit': self.unit, 'quantity': sum(facts.values())}] if facts else []


class SnapshotPreview(models.Model):
    _inherit = 'tp.report.snapshot'
    preview_html = fields.Html(compute='_compute_preview')

    @api.depends('payload')
    def _compute_preview(self):
        for rec in self:
            payload = json.loads(rec.payload)
            blocks = ['<h2>%s</h2>' % escape(payload.get('name', '')), '<p>%s — %s</p>' % (escape(payload.get('date_start', '')), escape(payload.get('date_end', '')))]
            for title, key in [('Tóm tắt', 'summary'), ('Vướng mắc', 'obstacles'), ('Kiến nghị', 'recommendations'), ('Kỳ sau', 'next_plan')]:
                blocks.append('<h3>%s</h3><p>%s</p>' % (title, escape(payload.get(key) or '—')))
            blocks.append('<table class="table"><thead><tr><th>Công việc</th><th>Đầu ra dự kiến</th><th>Ngày</th><th>Kết quả thực tế</th><th>Trạng thái việc</th><th>Khối lượng</th><th>Đơn vị</th></tr></thead><tbody>')
            for line in payload.get('lines', []):
                blocks.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % tuple(escape(str(line.get(key) if line.get(key) is not None else '—')) for key in ('name', 'expected_output', 'work_date', 'result', 'work_status', 'quantity', 'unit')))
            blocks.append('</tbody></table>')
            rec.preview_html = ''.join(blocks)


class PlanPersonal(models.Model):
    _inherit = 'tp.report.plan'
    expected_output = fields.Text()
    work_deadline = fields.Date()
    collaborator_ids = fields.Many2many('res.users', 'tp_report_plan_collaborator_rel')
    work_status = fields.Selection(WORK_STATUS, default='todo', required=True)
    proposed = fields.Boolean(default=False, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        # Employees may propose their own weekly allocation, never issue a baseline.
        for vals in vals_list:
            if vals.get('owner_id', self.env.uid) == self.env.uid and vals.get('period_type') == 'week':
                vals['proposed'] = True
        return super().create(vals_list)


class DocumentPersonal(models.Model):
    _inherit = 'tp.report.document'
    reviewer_id = fields.Many2one('res.users', string='Người rà soát')
    comparison_html = fields.Html(compute='_compute_comparison')

    def _compute_comparison(self):
        for rec in self:
            snapshots = rec.snapshot_ids.sorted('version', reverse=True)[:2]
            if len(snapshots) < 2:
                rec.comparison_html = '<p>Chưa có hai phiên bản để so sánh.</p>'
                continue
            snapshots.check_access('read')
            current, previous = [json.loads(item.payload) for item in snapshots]
            blocks = ['<h3>Phiên bản %s → %s</h3>' % (snapshots[1].version, snapshots[0].version)]
            for key, title in [('summary', 'Tóm tắt'), ('obstacles', 'Vướng mắc'), ('recommendations', 'Kiến nghị'), ('next_plan', 'Kỳ sau')]:
                if current.get(key) != previous.get(key):
                    blocks.append('<h4>%s</h4><p>Trước: %s</p><p>Sau: %s</p>' % (title, escape(previous.get(key) or '—'), escape(current.get(key) or '—')))
            old = {line.get('stable_key') or line.get('contribution_key'): line for line in previous.get('lines', [])}
            new = {line.get('stable_key') or line.get('contribution_key'): line for line in current.get('lines', [])}
            for key in sorted(set(old) | set(new)):
                if old.get(key) != new.get(key):
                    label = 'Thêm' if key not in old else 'Bỏ' if key not in new else 'Thay đổi'
                    line = new.get(key) or old[key]
                    blocks.append('<h4>%s: %s</h4>' % (label, escape(line.get('name') or '')))
                    for field in ('expected_output', 'result', 'quantity', 'work_status', 'cause', 'next_action'):
                        a, b = old.get(key, {}).get(field), new.get(key, {}).get(field)
                        if a != b:
                            blocks.append('<p>%s: %s → %s</p>' % (escape(field), escape(str(a) if a is not None else '—'), escape(str(b) if b is not None else '—')))
            rec.comparison_html = ''.join(blocks)

    def action_compare_versions(self):
        self.ensure_one()
        self.check_access('read')
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id, 'views': [(self.env.ref('tp_reporting.document_comparison_form').id, 'form')], 'target': 'new', 'context': {'form_view_initial_mode': 'readonly'}}
    review_ids = fields.One2many('tp.report.review', 'document_id')

    def get_reviewer_options(self):
        return self.get_reviewer_choices()

    def get_reviewer_choices(self):
        self.ensure_one()
        self.check_access('read')
        if self.owner_id != self.env.user or self.state not in ('draft', 'returned') or self.company_id not in self.env.companies:
            raise AccessError(_('Chỉ người lập chọn người rà trong bản nháp.'))
        today = fields.Date.context_today(self)
        self.env.cr.execute('''SELECT DISTINCT u.id,p.name FROM tp_report_assignment a JOIN res_users u ON u.id=a.user_id JOIN res_partner p ON p.id=u.partner_id JOIN res_company_users_rel c ON c.user_id=u.id AND c.cid=a.company_id WHERE a.capability='review' AND a.active=true AND u.active=true AND u.id!=%s AND a.company_id=%s AND a.date_start<=%s AND (a.date_end IS NULL OR a.date_end>=%s) AND (a.department_id IS NULL OR a.department_id=%s) AND (a.subject_id IS NULL OR a.subject_id=%s) AND a.level IN ('all',%s) ORDER BY p.name,u.id''', [self.owner_id.id, self.company_id.id, today, today, self.department_id.id or None, self.owner_id.id, self.level])
        return [{'id': row[0], 'display_name': row[1]} for row in self.env.cr.fetchall()]

    def action_preview(self):
        self.ensure_one()
        self.check_access('read')
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id, 'views': [(self.env.ref('tp_reporting.document_preview_form').id, 'form')], 'target': 'new', 'context': {'form_view_initial_mode': 'readonly'}}

    def _reviewer_valid(self):
        self.ensure_one()
        if not self.reviewer_id or self.reviewer_id == self.owner_id:
            return False
        # Authorization lookup returns existence only, not another user's assignment data.
        self.env.cr.execute('''SELECT 1 FROM tp_report_assignment WHERE user_id=%s AND capability='review' AND active=true AND company_id=%s AND date_start<=%s AND (date_end IS NULL OR date_end>=%s) AND (department_id IS NULL OR department_id=%s) AND (subject_id IS NULL OR subject_id=%s) AND level IN ('all',%s) AND EXISTS (SELECT 1 FROM res_users WHERE id=user_id AND active=true) LIMIT 1''', [self.reviewer_id.id, self.company_id.id, fields.Date.context_today(self), fields.Date.context_today(self), self.department_id.id or None, self.owner_id.id, self.level])
        valid = bool(self.env.cr.fetchone())
        self.env.cr.execute('SELECT 1 FROM res_company_users_rel WHERE user_id=%s AND cid=%s', [self.reviewer_id.id, self.company_id.id])
        return valid and bool(self.env.cr.fetchone())

    def action_submit(self, expected_version=None, request_key=None):
        if not self._reviewer_valid():
            raise ValidationError(_('Cần phân công người rà soát hợp lệ trong phạm vi/hiệu lực. Liên hệ người cấu hình Báo cáo.'))
        return super().action_submit(expected_version=expected_version, request_key=request_key)

    def _snapshot_payload(self):
        payload = super()._snapshot_payload()
        payload['reviewer_id'] = self.reviewer_id.id
        payload['reviewer'] = self.reviewer_id.name or ''
        payload['review_snapshot_ids'] = [self.current_snapshot_id.id] if self.state == 'finalized' and self.current_snapshot_id else []
        return payload

    def action_load_plans(self):
        self.ensure_one()
        self._locked()
        if self.owner_id != self.env.user or self.state not in ('draft', 'returned'):
            raise AccessError(_('Chỉ người lập tải việc vào nháp.'))
        plans = self.env['tp.report.plan'].search([('owner_id', '=', self.owner_id.id), ('company_id', '=', self.company_id.id), ('state', '=', 'issued'), ('period_type', '=', 'week'), ('date_start', '<=', self.date_end), ('date_end', '>=', self.date_start)])
        for plan in plans - self.line_ids.mapped('plan_id'):
            date = max(plan.date_start, self.date_start, plan.parent_id.date_start)
            if date > min(plan.date_end, self.date_end, plan.parent_id.date_end):
                continue
            self.env['tp.report.line'].with_context(tp_reporting_provenance=_INTERNAL).create({'document_id': self.id, 'name': plan.name, 'plan_id': plan.id, 'project_id': plan.project_id.id, 'task_id': plan.task_id.id, 'work_date': date, 'unit': plan.unit, 'contribution_key': 'plan-%s' % plan.id, 'stable_key': 'plan-%s' % plan.id, 'expected_output': plan.expected_output or plan.output, 'planned_quantity': plan.target, 'planned_quantity_known': plan.kind == 'quantitative', 'work_deadline': plan.work_deadline, 'priority_id': plan.priority_id.id, 'collaborator_ids': [fields.Command.set(plan.collaborator_ids.ids)]})
        self._internal_write({'version': self.version + 1})
        return True


class LinePersonal(models.Model):
    _inherit = 'tp.report.line'
    expected_output = fields.Text()
    work_deadline = fields.Date()
    collaborator_ids = fields.Many2many('res.users', 'tp_report_line_collaborator_rel')
    work_status = fields.Selection(WORK_STATUS, default='todo', required=True)
    deviation_reason = fields.Text()
    stable_key = fields.Char(required=True, default=lambda self: uuid.uuid4().hex)
    review_ids = fields.One2many('tp.report.review', 'line_id')
    document_version = fields.Integer(related='document_id.version', readonly=True)
    document_state = fields.Selection(related='document_id.state', readonly=True)

    def _fact(self):
        fact = super()._fact()
        fact.update({key: self[key] for key in ('expected_output', 'work_status', 'deviation_reason', 'stable_key')})
        fact['work_deadline'] = str(self.work_deadline) if self.work_deadline else None
        fact['collaborator_ids'] = self.collaborator_ids.ids
        fact['line_id'] = self.id
        return fact

    def write(self, vals):
        if {'review_ids', 'stable_key'} & vals.keys():
            raise AccessError(_('Nhận xét tạo riêng theo quyền, không sửa qua dòng.'))
        return super().write(vals)


class Review(models.Model):
    _name = 'tp.report.review'
    _rec_name = 'comment'
    _inherit = 'tp.report.scope.mixin'
    _description = 'Nhận xét, phản hồi và đính chính bất biến'
    _order = 'id desc'
    document_id = fields.Many2one('tp.report.document', required=True, ondelete='restrict')
    company_id = fields.Many2one(related='document_id.company_id', store=True)
    department_id = fields.Many2one(related='document_id.department_id', store=True)
    owner_id = fields.Many2one(related='document_id.owner_id', store=True)
    snapshot_id = fields.Many2one('tp.report.snapshot', required=True, ondelete='restrict', readonly=True)
    line_id = fields.Many2one('tp.report.line', ondelete='restrict')
    line_key = fields.Char(readonly=True)
    version = fields.Integer(readonly=True)
    actor_id = fields.Many2one('res.users', readonly=True)
    comment = fields.Text(required=True)
    assessment = fields.Selection(REVIEW_KINDS, string='Loại nhận xét', default='note', required=True)
    audience = fields.Selection([('published', 'Công bố cho tác giả'), ('internal', 'Nội bộ người rà')], default='published', required=True)
    parent_id = fields.Many2one('tp.report.review', ondelete='restrict')
    correction_of_id = fields.Many2one('tp.report.review', ondelete='restrict')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            doc = self.env['tp.report.document'].browse(vals['document_id'])
            doc._locked()
            if {'actor_id', 'version', 'snapshot_id', 'line_key'} & vals.keys():
                raise AccessError(_('Actor/phiên bản nhận xét do máy chủ xác định.'))
            parent = self.browse(vals.get('parent_id')).exists()
            correction = self.browse(vals.get('correction_of_id')).exists()
            if parent:
                parent.check_access('read')
                if parent.document_id != doc or parent.audience != 'published' or doc.owner_id != self.env.user or vals.get('audience', 'published') != 'published' or vals.get('assessment', 'note') != 'note':
                    raise AccessError(_('Chỉ phản hồi nhận xét công bố của báo cáo mình.'))
            else:
                doc._require('review')
                if doc.owner_id == self.env.user or doc.reviewer_id != self.env.user or doc.state not in ('submitted', 'in_review', 'finalized'):
                    raise AccessError(_('Chỉ người rà được phân công nhận xét bản đã gửi.'))
            if correction:
                correction.check_access('read')
                if correction.document_id != doc or correction.actor_id != self.env.user or correction.audience != vals.get('audience', 'published'):
                    raise AccessError(_('Chỉ đính chính nhận xét của mình, giữ audience.'))
            if parent and not vals.get('line_id'):
                vals['line_id'] = parent.line_id.id
            snapshot = parent.snapshot_id if parent else correction.snapshot_id if correction else doc.current_snapshot_id
            if not snapshot:
                raise ValidationError(_('Chưa có phiên bản đã gửi.'))
            line = self.env['tp.report.line'].browse(vals.get('line_id')).exists()
            if line and (line.document_id != doc or line.id not in [fact.get('line_id') for fact in json.loads(snapshot.payload).get('lines', [])]):
                raise ValidationError(_('Dòng không thuộc đúng phiên bản nhận xét.'))
            vals.update({'actor_id': self.env.uid, 'snapshot_id': snapshot.id, 'version': snapshot.version, 'line_key': line.stable_key if line else False})
        records = super().create(vals_list)
        # Return-with-lines markers rely on the single return notification instead.
        quiet = self.env.context.get('tp_reporting_quiet') is _INTERNAL
        for rec in records.filtered(lambda item: item.audience == 'published' and not quiet):
            recipient = rec.document_id.reviewer_id if rec.parent_id else rec.owner_id
            self.env['bus.bus']._sendone(recipient, 'simple_notification', {'title': _('Nhận xét báo cáo'), 'message': _('Có nhận xét/phản hồi mới. Mở Trung tâm Báo cáo để xem.'), 'sticky': True})
        return records

    def write(self, vals):
        raise AccessError(_('Nhận xét bất biến; tạo đính chính hoặc phản hồi.'))

    def unlink(self):
        raise AccessError(_('Không xóa nhận xét.'))


class AttachmentReporting(models.Model):
    _inherit = 'ir.attachment'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('res_model') in ('tp.report.document', 'tp.report.line', 'tp.report.value', 'tp.report.directive') and (vals.get('public') or vals.get('access_token')):
                raise AccessError(_('Minh chứng báo cáo không dùng public hoặc token.'))
        records = super().create(vals_list)
        records._tp_report_check()
        return records

    def _tp_report_check(self, mutation=False):
        for attachment in self:
            if attachment.res_model not in ('tp.report.document', 'tp.report.line', 'tp.report.value', 'tp.report.directive') or not attachment.res_id:
                continue
            target = self.env[attachment.res_model].browse(attachment.res_id).exists()
            if not target:
                raise AccessError(_('Nguồn minh chứng không còn tồn tại.'))
            target.check_access('write' if mutation else 'read')
            if attachment.res_model == 'tp.report.directive':
                if mutation and target.state == 'done':
                    raise AccessError(_('Minh chứng chỉ đạo đã hoàn thành bất biến.'))
                continue
            doc = target if attachment.res_model == 'tp.report.document' else target.document_id
            if mutation and (doc.snapshot_ids or doc.state not in ('draft', 'returned')):
                raise AccessError(_('Minh chứng đã gửi bất biến; tải tệp mới cho bản điều chỉnh.'))

    def write(self, vals):
        self._tp_report_check(mutation=True)
        if self.env.context.get('tp_reporting_internal') is not _INTERNAL and {'public', 'access_token', 'res_model', 'res_id'} & vals.keys() and any(rec.res_model in ('tp.report.document', 'tp.report.line', 'tp.report.value', 'tp.report.directive') for rec in self):
            raise AccessError(_('Không đổi audience/nguồn của minh chứng báo cáo.'))
        return super().write(vals)

    def unlink(self):
        self._tp_report_check(mutation=True)
        return super().unlink()

    def _can_return_content(self, field_name=None, access_token=None):
        self._tp_report_check()
        return super()._can_return_content(field_name, access_token)


class DirectiveCommands(models.Model):
    _inherit = 'tp.report.directive'
    line_id = fields.Many2one('tp.report.line', ondelete='restrict')
    snapshot_id = fields.Many2one('tp.report.snapshot', readonly=True, ondelete='restrict')
    version = fields.Integer(default=1, readonly=True)
    request_key = fields.Char(required=True, default=lambda self: uuid.uuid4().hex, readonly=True)
    request_hash = fields.Char(readonly=True)
    issuer_id = fields.Many2one('res.users', readonly=True)
    result = fields.Text()
    evidence_ids = fields.Many2many('ir.attachment', 'tp_report_directive_attachment_rel')
    history = fields.Json(readonly=True)
    history_html = fields.Html(compute='_compute_history_html')

    @api.depends('history')
    def _compute_history_html(self):
        for rec in self:
            rec.history_html = '<ul>' + ''.join('<li>%s · %s · v%s · %s</li>' % (escape(event.get('at', '')), escape(event.get('action', '')), escape(str(event.get('version', ''))), escape(event.get('result') or '')) for event in rec.history or []) + '</ul>'

    @api.constrains('evidence_ids')
    def _check_directive_evidence(self):
        for rec in self:
            rec.evidence_ids.check_access('read')
            for attachment in rec.evidence_ids:
                if not attachment.res_id and attachment.create_uid == self.env.user and not attachment.public and not attachment.access_token:
                    attachment.with_context(tp_reporting_internal=_INTERNAL).write({'res_model': 'tp.report.directive', 'res_id': rec.id})
                if attachment.public or attachment.access_token or attachment.res_model != 'tp.report.directive' or attachment.res_id != rec.id:
                    raise ValidationError(_('Minh chứng chỉ đạo phải riêng tư và thuộc chỉ đạo này.'))

    _directive_request_unique = models.Constraint('UNIQUE(issuer_id,request_key)', 'Yêu cầu chỉ đạo đã tồn tại.')

    @api.model_create_multi
    def create(self, vals_list):
        records = self.browse()
        for values in vals_list:
            vals = dict(values)
            if {'issuer_id', 'version', 'history', 'request_hash', 'snapshot_id'} & vals.keys():
                raise AccessError(_('Phiên bản/actor chỉ đạo do máy chủ xác định.'))
            doc = self.env['tp.report.document'].browse(vals['document_id'])
            doc._locked()
            doc._require('direct')
            key = vals.get('request_key') or uuid.uuid4().hex
            digest = hashlib.sha256(json.dumps({name: vals.get(name) for name in ('name', 'document_id', 'owner_id', 'deadline', 'description', 'line_id', 'project_id')}, sort_keys=True, default=str).encode()).hexdigest()
            old = self.search([('issuer_id', '=', self.env.uid), ('request_key', '=', key)], limit=1)
            if old:
                if old.request_hash != digest:
                    raise UserError(_('Mã yêu cầu chỉ đạo đã dùng với nội dung khác.'))
                records |= old
                continue
            line = self.env['tp.report.line'].browse(vals.get('line_id')).exists()
            if line and line.document_id != doc:
                raise ValidationError(_('Dòng chỉ đạo không thuộc báo cáo nguồn.'))
            vals.update({'issuer_id': self.env.uid, 'request_key': key, 'request_hash': digest, 'snapshot_id': doc.current_snapshot_id.id, 'history': [{'action': 'create', 'actor': self.env.uid, 'at': str(fields.Datetime.now()), 'version': 1}]})
            record = super().create([vals])
            self.env['bus.bus']._sendone(record.owner_id, 'simple_notification', {'title': _('Việc được giao'), 'message': _('Bạn có chỉ đạo mới trong Trung tâm Báo cáo.'), 'sticky': True})
            records |= record
        return records

    def _directive_command(self, target, expected_version=None, request_key=None):
        self.ensure_one()
        self.check_access('write')
        self.env.cr.execute('SELECT id FROM tp_report_directive WHERE id=%s FOR UPDATE', [self.id])
        self.invalidate_recordset()
        if self.owner_id != self.env.user:
            raise AccessError(_('Chỉ người nhận xử lý chỉ đạo.'))
        history = self.history or []
        expected = expected_version if expected_version is not None else self.env.context.get('tp_reporting_expected_version')
        digest = hashlib.sha256(json.dumps([target, expected, self.result or ''], sort_keys=True).encode()).hexdigest()
        if request_key and any(event.get('request_key') == request_key for event in history):
            if any(event.get('request_key') == request_key and event.get('request_hash') != digest for event in history):
                raise UserError(_('Mã yêu cầu đã dùng với nội dung khác.'))
            return True
        if expected is not None and expected != self.version:
            raise UserError(_('Chỉ đạo đã đổi; vui lòng tải lại.'))
        if (self.state, target) not in [('open', 'in_progress'), ('in_progress', 'done')]:
            raise UserError(_('Trạng thái chỉ đạo không cho phép thao tác.'))
        if target == 'done' and not self.result:
            raise ValidationError(_('Nhập kết quả xử lý trước khi hoàn thành.'))
        self.evidence_ids.check_access('read')
        version = self.version + 1
        self.with_context(tp_reporting_internal=_INTERNAL).write({'state': target, 'version': version, 'history': history + [{'action': target, 'actor': self.env.uid, 'at': str(fields.Datetime.now()), 'version': version, 'request_key': request_key, 'request_hash': digest, 'result': self.result or ''}]})
        self.env['bus.bus']._sendone(self.issuer_id, 'simple_notification', {'title': _('Chỉ đạo có cập nhật'), 'message': _('Mở Trung tâm Báo cáo để xem kết quả xử lý.'), 'sticky': True})
        return True

    def action_start(self, expected_version=None, request_key=None):
        return self._directive_command('in_progress', expected_version, request_key)

    def action_done(self, expected_version=None, request_key=None):
        return self._directive_command('done', expected_version, request_key)

    def write(self, vals):
        if self.env.context.get('tp_reporting_internal') is not _INTERNAL:
            if {'issuer_id', 'version', 'history', 'request_key', 'request_hash', 'snapshot_id', 'line_id'} & vals.keys():
                raise AccessError(_('Không sửa nguồn/lịch sử chỉ đạo.'))
            expected = self.env.context.get('tp_reporting_expected_version')
            if not self.env.su and expected is None:
                raise UserError(_('Thiếu phiên bản chỉ đạo. Mở lại biểu mẫu.'))
            for rec in self:
                self.env.cr.execute('SELECT id FROM tp_report_directive WHERE id=%s FOR UPDATE', [rec.id])
                rec.invalidate_recordset()
                if expected is not None and rec.version != expected:
                    raise UserError(_('Chỉ đạo đã thay đổi.'))
                if rec.state == 'done':
                    raise AccessError(_('Chỉ đạo đã hoàn thành không sửa kết quả.'))
            result = super().write(vals)
            for rec in self:
                rec.with_context(tp_reporting_internal=_INTERNAL).write({'version': rec.version + 1})
            return result
        return super().write(vals)


class ReportActionVisibility(models.Model):
    _inherit = 'tp.report.document'
    can_submit = fields.Boolean(compute='_compute_actions')
    can_review = fields.Boolean(compute='_compute_actions')
    can_finalize = fields.Boolean(compute='_compute_actions')
    can_consolidate = fields.Boolean(compute='_compute_actions')

    def _compute_actions(self):
        for rec in self:
            rec.can_submit = rec.owner_id == self.env.user
            independent = rec.level != 'personal' or rec.owner_id != self.env.user
            rec.can_review = independent and rec.reviewer_id == self.env.user and rec._has_capability('review')
            rec.can_finalize = independent and rec._has_capability('finalize')
            rec.can_consolidate = rec.owner_id == self.env.user and (rec.level == 'personal' or rec._has_capability('consolidate'))


class PlanActionVisibility(models.Model):
    _inherit = 'tp.report.plan'
    can_submit = fields.Boolean(compute='_compute_actions')
    can_manage_plan = fields.Boolean(compute='_compute_actions')
    can_issue = fields.Boolean(compute='_compute_actions')

    def _compute_actions(self):
        for rec in self:
            rec.can_manage_plan = rec._has_capability('plan')
            rec.can_submit = rec.can_manage_plan or (rec.owner_id == self.env.user and rec.proposed)
            rec.can_issue = rec._has_capability('plan_issue')
