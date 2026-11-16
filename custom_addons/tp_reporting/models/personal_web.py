"""Personal web reporting: shared catalogs, issue follow-up and two-way review on the web.

Employees draft, save, send and resubmit; reviewers comment per line or generally,
rate with a configurable level, return or finalize. No external workbook is needed.
"""
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .catalog import COLORS
from .reporting import _INTERNAL

REVIEW_FLAGS = [('none', 'Chưa nhận xét'), ('note', 'Có nhận xét'), ('ok', 'Ghi nhận đạt'),
                ('needs_change', 'Cần bổ sung'), ('replied', 'Đã phản hồi'), ('resubmitted', 'Đã sửa, chờ rà lại')]


def _default_priority(self):
    return self.env['tp.report.priority']._default_record()


class PlanPriority(models.Model):
    _inherit = 'tp.report.plan'
    priority_id = fields.Many2one('tp.report.priority', string='Mức ưu tiên', required=True, ondelete='restrict',
                                  default=_default_priority)
    priority_color = fields.Selection(related='priority_id.color')


class LineWeb(models.Model):
    _inherit = 'tp.report.line'
    priority_id = fields.Many2one('tp.report.priority', string='Mức ưu tiên', required=True, ondelete='restrict',
                                  default=_default_priority)
    priority_color = fields.Selection(related='priority_id.color')
    support_needed = fields.Text(string='Hỗ trợ cần cấp trên')
    issue_owner_id = fields.Many2one('res.users', string='Người xử lý vướng mắc', ondelete='restrict')
    issue_deadline = fields.Date(string='Hạn xử lý vướng mắc')
    review_flag = fields.Selection(REVIEW_FLAGS, compute='_compute_review_state', string='Nhận xét')
    review_count = fields.Integer(compute='_compute_review_state', string='Số nhận xét')
    latest_review = fields.Char(compute='_compute_review_state', string='Nhận xét mới nhất')
    manager_rating_id = fields.Many2one('tp.report.rating', compute='_compute_review_state', string='Đánh giá quản lý')
    manager_rating_color = fields.Selection(COLORS, compute='_compute_review_state')
    can_comment = fields.Boolean(compute='_compute_can_comment')

    @api.depends('review_ids', 'document_id.state', 'document_id.current_snapshot_id')
    @api.depends_context('uid')
    def _compute_review_state(self):
        # Search under the caller so record rules keep internal reviewer notes hidden from authors.
        line_ids = [rec._origin.id for rec in self if rec._origin.id]
        reviews = self.env['tp.report.review'].search([('line_id', 'in', line_ids)], order='id desc') if line_ids else []
        by_line = {}
        for review in reviews:
            by_line.setdefault(review.line_id.id, []).append(review)
        for rec in self:
            items = by_line.get(rec._origin.id, [])
            top = [item for item in items if not item.parent_id]
            latest = items[0] if items else False
            rated = next((item for item in top if item.rating_id), False)
            rec.review_count = len(items)
            rec.latest_review = (latest.comment or '')[:120] if latest else False
            rec.manager_rating_id = rated.rating_id if rated else False
            rec.manager_rating_color = rated.rating_id.color if rated else False
            rec.review_flag = rec._review_flag(top, items)

    def _review_flag(self, top, items):
        if not top:
            return 'none'
        head = top[0]
        if head.assessment != 'needs_change':
            return 'ok' if head.assessment == 'satisfactory' else 'note'
        doc = self.document_id
        stale = bool(doc.current_snapshot_id and head.snapshot_id != doc.current_snapshot_id)
        if doc.state in ('draft', 'returned'):
            return 'needs_change'
        if doc.state == 'finalized':
            return 'note' if stale else 'needs_change'
        if stale:
            return 'resubmitted'
        return 'replied' if any(item.parent_id == head for item in items) else 'needs_change'

    @api.depends('document_id.state', 'document_id.reviewer_id')
    @api.depends_context('uid')
    def _compute_can_comment(self):
        for rec in self:
            doc = rec.document_id
            rec.can_comment = bool(doc.reviewer_id == self.env.user and doc.owner_id != self.env.user
                                   and doc.state in ('submitted', 'in_review', 'finalized') and doc.current_snapshot_id)

    def _fact(self):
        fact = super()._fact()
        fact.update({
            'priority_id': self.priority_id.id, 'priority': self.priority_id.name or None,
            'support_needed': self.support_needed, 'issue_owner_id': self.issue_owner_id.id,
            'issue_deadline': str(self.issue_deadline) if self.issue_deadline else None,
        })
        return fact

    def action_comment(self):
        self.ensure_one()
        return self.document_id._review_dialog(line=self)


class DocumentWeb(models.Model):
    _inherit = 'tp.report.document'
    return_reason = fields.Text(compute='_compute_web_state', string='Lý do trả lại')
    needs_change_count = fields.Integer(compute='_compute_web_state', string='Đầu việc cần bổ sung')
    snapshot_count = fields.Integer(compute='_compute_web_state', string='Số lần gửi')
    submitted_at = fields.Datetime(compute='_compute_web_state', string='Gửi lúc')
    can_comment = fields.Boolean(compute='_compute_web_state')

    @api.depends('state', 'version', 'line_ids', 'snapshot_ids', 'event_ids')
    @api.depends_context('uid')
    def _compute_web_state(self):
        for rec in self:
            events = rec.event_ids.sorted('id', reverse=True)
            returned = events.filtered(lambda event: event.name == 'return')[:1]
            submitted = events.filtered(lambda event: event.name == 'submit')[:1]
            rec.return_reason = returned.reason if returned and rec.state == 'returned' else False
            rec.needs_change_count = len(rec.line_ids.filtered(lambda line: line.review_flag == 'needs_change'))
            rec.snapshot_count = len(rec.snapshot_ids.filtered(lambda snap: snap.kind == 'submitted'))
            rec.submitted_at = submitted.create_date if submitted else False
            rec.can_comment = bool(rec.reviewer_id == self.env.user and rec.owner_id != self.env.user
                                   and rec.state in ('submitted', 'in_review', 'finalized') and rec.current_snapshot_id)

    def _review_dialog(self, line=None):
        self.ensure_one()
        self.check_access('read')
        if self.reviewer_id != self.env.user or self.owner_id == self.env.user or self.state not in ('submitted', 'in_review', 'finalized'):
            raise AccessError(_('Chỉ người rà được phân công nhận xét bản đã gửi.'))
        context = {'default_document_id': self.id, 'default_audience': 'published', 'default_assessment': 'note'}
        if line:
            context['default_line_id'] = line.id
        return {'type': 'ir.actions.act_window', 'name': _('Nhận xét đầu việc') if line else _('Nhận xét chung'),
                'res_model': 'tp.report.review', 'view_mode': 'form', 'target': 'new',
                'views': [(self.env.ref('tp_reporting.review_comment_form').id, 'form')], 'context': context}

    def action_comment(self):
        return self._review_dialog()

    def action_save_draft(self):
        # The form saves before this button runs; this only confirms what was stored.
        self.ensure_one()
        self.check_access('read')
        if self.owner_id != self.env.user or self.state not in ('draft', 'returned'):
            raise AccessError(_('Chỉ người lập lưu nháp của mình.'))
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
            'type': 'success', 'title': _('Đã lưu nháp'),
            'message': _('Phiên bản %s đã lưu. Báo cáo chưa gửi; bấm Xem trước rồi Gửi báo cáo khi xong.') % self.version}}


class ObligationWeb(models.Model):
    _inherit = 'tp.report.obligation'

    def action_create_report(self):
        created = not self.document_id
        action = super().action_create_report()
        report = self.document_id
        if created and report and report.level == 'personal' and report.period_type == 'week' and report.state == 'draft':
            # "Lập báo cáo" brings issued week work of this period into the new draft.
            report.action_load_plans()
        return action


class ReviewWeb(models.Model):
    _inherit = 'tp.report.review'
    rating_id = fields.Many2one('tp.report.rating', string='Mức đánh giá', ondelete='restrict')
    rating_color = fields.Selection(related='rating_id.color')
    parent_comment = fields.Text(related='parent_id.comment', string='Nhận xét được phản hồi')
    parent_actor_id = fields.Many2one(related='parent_id.actor_id', string='Người nhận xét')
    reply_ids = fields.One2many('tp.report.review', 'parent_id', string='Phản hồi')
    can_reply = fields.Boolean(compute='_compute_can_act')
    can_correct = fields.Boolean(compute='_compute_can_act')

    @api.depends('parent_id', 'audience', 'actor_id', 'document_id.owner_id', 'document_id.reviewer_id')
    @api.depends_context('uid')
    def _compute_can_act(self):
        for rec in self:
            doc = rec.document_id
            rec.can_reply = bool(not rec.parent_id and rec.audience == 'published' and doc.owner_id == self.env.user)
            rec.can_correct = bool(not rec.parent_id and rec.actor_id == self.env.user and doc.reviewer_id == self.env.user)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('parent_id') and vals.get('rating_id'):
                raise AccessError(_('Phản hồi của người lập không mang mức đánh giá.'))
        return super().create(vals_list)

    def action_reply(self):
        self.ensure_one()
        self.check_access('read')
        if not self.can_reply:
            raise AccessError(_('Chỉ người lập phản hồi nhận xét đã công bố.'))
        return {'type': 'ir.actions.act_window', 'name': _('Phản hồi nhận xét'), 'res_model': self._name,
                'view_mode': 'form', 'target': 'new',
                'views': [(self.env.ref('tp_reporting.review_reply_form').id, 'form')],
                'context': {'default_parent_id': self.id, 'default_document_id': self.document_id.id,
                            'default_line_id': self.line_id.id, 'default_audience': 'published',
                            'default_assessment': 'note'}}

    def action_correct(self):
        self.ensure_one()
        self.check_access('read')
        if not self.can_correct:
            raise AccessError(_('Chỉ đính chính nhận xét của mình.'))
        return {'type': 'ir.actions.act_window', 'name': _('Đính chính nhận xét'), 'res_model': self._name,
                'view_mode': 'form', 'target': 'new',
                'views': [(self.env.ref('tp_reporting.review_comment_form').id, 'form')],
                'context': {'default_correction_of_id': self.id, 'default_document_id': self.document_id.id,
                            'default_line_id': self.line_id.id, 'default_audience': self.audience,
                            'default_assessment': self.assessment, 'default_rating_id': self.rating_id.id,
                            'default_comment': self.comment}}


class ReasonLines(models.TransientModel):
    _inherit = 'tp.report.reason'
    line_ids = fields.Many2many('tp.report.line', string='Đầu việc cần bổ sung')

    def action_apply(self):
        self.ensure_one()
        if self.resource_model == 'tp.report.document' and self.action == 'return' and self.line_ids:
            doc = self.env['tp.report.document'].browse(self.resource_id).exists()
            if not doc:
                raise UserError(_('Bản ghi không còn tồn tại.'))
            if self.line_ids.document_id != doc:
                raise ValidationError(_('Đầu việc cần bổ sung phải thuộc báo cáo đang trả lại.'))
            replay = self.env['tp.report.event'].search_count([
                ('resource_model', '=', doc._name), ('resource_id', '=', doc.id),
                ('request_key', '=', 'reason-%s' % self.id)])
            if not replay:
                if self.expected_version != doc.version:
                    raise UserError(_('Bản ghi đã thay đổi. Vui lòng tải lại.'))
                # Line markers are ordinary immutable reviews; the transition notifies the author once.
                self.env['tp.report.review'].with_context(tp_reporting_quiet=_INTERNAL).create([{
                    'document_id': doc.id, 'line_id': line.id, 'comment': self.reason,
                    'assessment': 'needs_change', 'audience': 'published'} for line in self.line_ids])
        return super().action_apply()
