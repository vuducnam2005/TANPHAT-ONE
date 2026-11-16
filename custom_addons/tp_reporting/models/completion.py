"""Period composition and web content commands, without modifying business sources."""
import calendar
import json
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.tp_reporting.models.reporting import _INTERNAL


def dated_facts(payloads, start, end):
    facts = {}
    for payload in payloads:
        for fact in payload.get('lines', []):
            if not str(start) <= fact.get('work_date', '') <= str(end):
                continue
            key = (fact.get('contribution_key'), fact.get('work_date'), fact.get('unit'))
            if key in facts and facts[key].get('quantity') != fact.get('quantity'):
                raise ValidationError(_('Nguồn cùng ngày/đơn vị có kết quả khác nhau; cần đối chiếu.'))
            facts[key] = fact
    return list(facts.values())


class DocumentCompletion(models.Model):
    _inherit = 'tp.report.document'

    section_content_ids = fields.One2many('tp.report.section.content', 'document_id')

    @api.constrains('template_id', 'level', 'period_type')
    def _check_template_kind(self):
        for document in self:
            template = document.template_id
            if template and (template.level != document.level or
                             (template.period_type and template.period_type != document.period_type)):
                raise ValidationError(_('Mẫu phải đúng cấp báo cáo và loại kỳ.'))

    def action_aggregate(self, expected_version=None):
        self.ensure_one()
        if self.level != 'personal':
            return super().action_aggregate(expected_version=expected_version)
        self._locked(expected_version)
        if self.owner_id != self.env.user or self.state not in ('draft', 'returned') or self.period_type not in ('month', 'quarter'):
            raise AccessError(_('Chỉ người lập tổng hợp báo cáo cá nhân tháng/quý đang nháp.'))
        obligation = self.env['tp.report.obligation'].search_count([
            ('owner_id', '=', self.owner_id.id), ('company_id', '=', self.company_id.id),
            ('period_type', '=', self.period_type), ('date_start', '=', self.date_start),
            ('date_end', '=', self.date_end), ('state', '!=', 'exempt'),
        ], limit=1)
        if not obligation:
            raise ValidationError(_('Cá nhân tháng/quý cần nghĩa vụ hoặc yêu cầu được phân công đúng kỳ.'))
        children = self.search([
            ('id', '!=', self.id), ('owner_id', '=', self.owner_id.id), ('company_id', '=', self.company_id.id),
            ('level', '=', 'personal'), ('period_type', 'in', ['week'] if self.period_type == 'month' else ['week', 'month']),
            ('date_start', '<=', self.date_end), ('date_end', '>=', self.date_start),
            ('state', 'in', ['submitted', 'in_review', 'finalized']),
        ])
        snapshots = children.mapped('current_snapshot_id')
        snapshots.check_access('read')
        if not snapshots:
            raise UserError(_('Chưa có bản đã gửi/chốt trong kỳ để tổng hợp.'))
        facts = dated_facts([json.loads(snapshot.payload) for snapshot in snapshots], self.date_start, self.date_end)
        # Manually entered rows are not silently destroyed by a refresh.
        if self.line_ids.filtered(lambda line: not line.rollup_source):
            raise UserError(_('Bản nháp có dòng nhập riêng; đối chiếu và bỏ dòng riêng trước khi tổng hợp.'))
        self.line_ids.with_context(tp_reporting_draft_batch=_INTERNAL).unlink()
        for fact in facts:
            values = {key: value for key, value in fact.items()
                      if key in self.env['tp.report.line']._fields and key not in ('id', 'document_id', 'line_id')}
            values['collaborator_ids'] = [fields.Command.set(values.get('collaborator_ids', []))]
            values.update({'document_id': self.id, 'rollup_source': True})
            if 'quantity_known' in self.env['tp.report.line']._fields:
                values['quantity_known'] = fact.get('quantity') is not None
                values['quantity'] = fact.get('quantity') or 0
            self.env['tp.report.line'].with_context(tp_reporting_provenance=_INTERNAL, tp_reporting_draft_batch=_INTERNAL).create(values)
        self._internal_write({'dependency_ids': [fields.Command.set(snapshots.ids)], 'version': self.version + 1})
        return True

    def action_prepare_sections(self):
        self.ensure_one()
        self._locked()
        if self.owner_id != self.env.user or self.state not in ('draft', 'returned'):
            raise AccessError(_('Chỉ người lập chuẩn bị nội dung mẫu trên nháp.'))
        existing = self.section_content_ids.mapped('section_id')
        for section in self.template_id.section_ids - existing:
            if section.audience == 'general':
                self.env['tp.report.section.content'].create({'document_id': self.id, 'section_id': section.id})
        return True

    def action_submit(self, expected_version=None, request_key=None):
        self.ensure_one()
        self._locked()
        if any(entry.section_id.template_id != self.template_id for entry in self.section_content_ids):
            raise ValidationError(_('Có nội dung từ mẫu cũ; đối chiếu và bỏ phần không thuộc mẫu hiện hành.'))
        required = self.template_id.section_ids.filtered(lambda section: section.required and section.audience == 'general')
        for section in required:
            content = self.section_content_ids.filtered(lambda entry: entry.section_id == section)
            built_in_results = section == self.env.ref('tp_reporting.section_personal_results', raise_if_not_found=False)
            if not any(entry.content and entry.content.strip() for entry in content) and not (built_in_results and (self.summary or self.line_ids)):
                raise ValidationError(_('Cần nhập phần bắt buộc: %s') % section.name)
        return super().action_submit(expected_version=expected_version, request_key=request_key)

    def _snapshot_payload(self):
        payload = super()._snapshot_payload()
        payload['section_contents'] = [entry._snapshot_content() for entry in self.section_content_ids
                                       if entry.section_id.audience == 'general']
        return payload


class SectionContent(models.Model):
    _name = 'tp.report.section.content'
    _description = 'Nội dung từng phần mẫu báo cáo'
    _rec_name = 'section_id'
    _order = 'sequence,id'

    document_id = fields.Many2one('tp.report.document', required=True, ondelete='cascade')
    section_id = fields.Many2one('tp.report.section', required=True, ondelete='restrict')
    sequence = fields.Integer(related='section_id.sequence')
    content = fields.Text(string='Nội dung')
    design_stage = fields.Selection([('prefs', 'PreFS — tiền khả thi'), ('fs', 'FS — khả thi'),
                                    ('tkkt', 'TKKT — kỹ thuật'), ('bvtc', 'BVTC — bản vẽ thi công'),
                                    ('gstg', 'GSTG — giám sát tác giả')])
    package_reference = fields.Char(string='Gói / đoạn / hạng mục')
    submission_reference = fields.Char(string='Hồ sơ trình / lần trình')
    quality_review = fields.Text(string='KCS / thẩm tra')
    missing_inputs = fields.Text(string='Đầu vào / phụ thuộc còn thiếu')
    business_source_kind = fields.Selection([('opportunity', 'Cơ hội / đấu thầu'), ('contract', 'Hợp đồng'),
                                             ('allocation', 'Giao khoán'), ('production', 'Sản lượng'),
                                             ('acceptance', 'Nghiệm thu'), ('payment_request', 'Đề nghị thanh toán')])
    source_reference = fields.Char(string='Tham chiếu nguồn trong phạm vi')
    source_note = fields.Char(default='Nguồn tham chiếu thủ công; chưa tích hợp tự động, không xác nhận số tiền.', readonly=True)
    document_state = fields.Selection(related='document_id.state')
    document_version = fields.Integer(related='document_id.version')
    _section_unique = models.Constraint('UNIQUE(document_id,section_id)', 'Mỗi phần chỉ có một nội dung trong bản nháp.')

    def _check_editor(self):
        for entry in self:
            doc = entry.document_id
            doc.check_access('write')
            if doc.owner_id != self.env.user or doc.state not in ('draft', 'returned'):
                raise AccessError(_('Chỉ người lập sửa nội dung mẫu trên nháp.'))
            if entry.section_id.template_id != doc.template_id or entry.section_id.audience != 'general':
                raise ValidationError(_('Phần phải thuộc mẫu hiện hành và audience thông thường.'))

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            values.pop('source_note', None)
        documents = self.env['tp.report.document'].browse(list({
            values.get('document_id', self.env.context.get('default_document_id')) for values in vals_list
        } - {None, False}))
        for document in documents.sorted('id'):
            document._locked(self.env.context.get('tp_reporting_expected_version'))
        records = super().create(vals_list)
        records._check_editor()
        if self.env.context.get('tp_reporting_draft_batch') is not _INTERNAL:
            for document in documents:
                document._internal_write({'version': document.version + 1})
        return records

    def write(self, vals):
        self._check_editor()
        if {'document_id', 'section_id', 'source_note'} & vals.keys():
            raise AccessError(_('Không đổi nguồn/đối tượng của phần đã tạo.'))
        batch = self.env.context.get('tp_reporting_draft_batch') is _INTERNAL
        if not batch:
            if not self.env.su and self.env.context.get('tp_reporting_expected_version') is None:
                raise UserError(_('Thiếu phiên bản nội dung; mở lại biểu mẫu và lưu.'))
            for doc in self.mapped('document_id'):
                doc._locked(self.env.context.get('tp_reporting_expected_version'))
            self._check_editor()
        result = super().write(vals)
        if not batch:
            for doc in self.mapped('document_id'):
                doc._internal_write({'version': doc.version + 1})
        return result

    def unlink(self):
        self._check_editor()
        documents = self.mapped('document_id')
        for doc in documents.sorted('id'):
            doc._locked(self.env.context.get('tp_reporting_expected_version'))
        self._check_editor()
        result = super().unlink()
        if self.env.context.get('tp_reporting_draft_batch') is not _INTERNAL:
            for document in documents:
                document._internal_write({'version': document.version + 1})
        return result

    def _snapshot_content(self):
        self.ensure_one()
        return {name: self[name] for name in ('content', 'design_stage', 'package_reference',
                                             'submission_reference', 'quality_review', 'missing_inputs',
                                             'business_source_kind', 'source_reference')} | {
            'section_id': self.section_id.id, 'section_name': self.section_id.name,
            'section_description': self.section_id.description,
        }


class PlanCompletion(models.Model):
    _inherit = 'tp.report.plan'

    def action_copy_structure(self):
        self.ensure_one()
        self.check_access('read')
        self._require('plan')
        return {'type': 'ir.actions.act_window', 'res_model': 'tp.report.copy.plan', 'view_mode': 'form',
                'target': 'new', 'context': {'default_source_id': self.id}}


class CopyPlan(models.TransientModel):
    _name = 'tp.report.copy.plan'
    _description = 'Sao chép cơ cấu sang kỳ mới'

    source_id = fields.Many2one('tp.report.plan', required=True, readonly=True)
    target_start = fields.Date(required=True)
    target_parent_id = fields.Many2one('tp.report.plan', string='Mục tiêu cha kỳ mới')
    result_id = fields.Many2one('tp.report.plan', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if any(values.get('result_id') for values in vals_list) or self.env.context.get('default_result_id'):
            raise AccessError(_('Kết quả sao chép do máy chủ xác định.'))
        return super().create(vals_list)

    def write(self, vals):
        if 'result_id' in vals:
            raise AccessError(_('Kết quả sao chép do máy chủ xác định.'))
        return super().write(vals)

    def action_copy(self):
        self.ensure_one()
        self.check_access('write')
        self.env.cr.execute('SELECT id FROM tp_report_copy_plan WHERE id=%s FOR UPDATE', [self.id])
        self.invalidate_recordset()
        if self.result_id:
            self.result_id.check_access('read')
            return {'type': 'ir.actions.act_window', 'res_model': 'tp.report.plan', 'res_id': self.result_id.id, 'view_mode': 'form'}
        source = self.source_id
        source.check_access('read')
        source._require('plan')
        if source.period_type not in ('quarter', 'month'):
            raise ValidationError(_('Sao chép cơ cấu bắt đầu từ quý hoặc tháng.'))
        start = self.target_start
        if start.day != 1 or (source.period_type == 'quarter' and start.month not in (1, 4, 7, 10)):
            raise ValidationError(_('Ngày đầu kỳ mới không hợp lệ.'))
        if source.period_type == 'month' and not self.target_parent_id:
            raise ValidationError(_('Chọn mục tiêu quý cha cho tháng mới.'))
        if start == source.date_start:
            raise ValidationError(_('Chọn kỳ khác kỳ nguồn.'))
        month_shift = (start.year - source.date_start.year) * 12 + start.month - source.date_start.month

        def copy_node(node, parent):
            node.check_access('read')
            new_start = node.date_start + relativedelta(months=month_shift)
            if node.period_type == 'week':
                new_start -= timedelta(days=new_start.weekday())
                new_end = new_start + timedelta(days=6)
            else:
                end_month = new_start + relativedelta(months=2 if node.period_type == 'quarter' else 0)
                new_end = end_month.replace(day=calendar.monthrange(end_month.year, end_month.month)[1])
            values = {'name': '%s / %s' % (node.name, new_start), 'period_type': node.period_type,
                      'date_start': new_start, 'date_end': new_end, 'company_id': node.company_id.id,
                      'department_id': node.department_id.id, 'owner_id': node.owner_id.id,
                      'parent_id': parent.id if parent else False, 'kind': node.kind, 'target': node.target,
                      'unit': node.unit, 'output': node.output, 'expected_output': node.expected_output,
                      'priority': node.priority, 'task_id': node.task_id.id, 'project_id': node.project_id.id,
                      'collaborator_ids': [fields.Command.set(node.collaborator_ids.ids)],
                      'work_deadline': False}
            copied = self.env['tp.report.plan'].create(values)
            for child in node.child_ids:
                copy_node(child, copied)
            return copied

        root = copy_node(source, self.target_parent_id)
        super().write({'result_id': root.id})
        return {'type': 'ir.actions.act_window', 'res_model': root._name, 'res_id': root.id, 'view_mode': 'form'}


class LineCompletion(models.Model):
    _inherit = 'tp.report.line'

    rollup_source = fields.Boolean(default=False, readonly=True)
    origin_line_id = fields.Many2one('tp.report.line', readonly=True, ondelete='restrict')
    carry_reason = fields.Text(readonly=True)
    is_emergent = fields.Boolean(string='Việc phát sinh')
    emergence_reason = fields.Text(string='Lý do phát sinh')
    assigned_by_id = fields.Many2one('res.users', string='Người giao việc phát sinh')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('tp_reporting_provenance') is not _INTERNAL:
            protected = {'rollup_source', 'origin_line_id', 'carry_reason', 'stable_key'}
            if any(protected & values.keys() for values in vals_list) or any(self.env.context.get('default_' + key) for key in protected):
                raise AccessError(_('Nguồn chuyển tiếp/tổng hợp và ID ổn định chỉ tạo qua action.'))
        return super().create(vals_list)

    def write(self, vals):
        if {'rollup_source', 'origin_line_id', 'carry_reason'} & vals.keys():
            raise AccessError(_('Không sửa nguồn chuyển tiếp/tổng hợp sau khi tạo.'))
        return super().write(vals)

    @api.constrains('is_emergent', 'emergence_reason', 'assigned_by_id', 'origin_line_id', 'stable_key')
    def _check_provenance(self):
        for line in self:
            if line.is_emergent and (not (line.emergence_reason or '').strip() or not line.assigned_by_id):
                raise ValidationError(_('Việc phát sinh cần lý do và người giao.'))
            if line.origin_line_id:
                origin = line.origin_line_id
                origin.check_access('read')
                if origin.owner_id != line.owner_id or origin.company_id != line.company_id or origin.stable_key != line.stable_key or not line.carry_reason:
                    raise ValidationError(_('Chuyển tiếp phải giữ nguồn, owner, công ty, ID ổn định và lý do.'))

    def _fact(self):
        fact = super()._fact()
        fact.update({'is_emergent': self.is_emergent, 'emergence_reason': self.emergence_reason,
                     'assigned_by_id': self.assigned_by_id.id, 'origin_line_id': self.origin_line_id.id,
                     'carry_reason': self.carry_reason})
        return fact

    def action_carry_forward(self):
        self.ensure_one()
        self.check_access('read')
        if self.owner_id != self.env.user or self.work_status == 'done':
            raise AccessError(_('Chỉ người phụ trách chuyển tiếp đầu việc chưa hoàn thành của mình.'))
        return {'type': 'ir.actions.act_window', 'res_model': 'tp.report.carry.work', 'view_mode': 'form',
                'target': 'new', 'context': {'default_line_id': self.id}}


class CarryWork(models.TransientModel):
    _name = 'tp.report.carry.work'
    _description = 'Chuyển đầu việc tồn sang kỳ sau'

    line_id = fields.Many2one('tp.report.line', required=True, readonly=True)
    target_document_id = fields.Many2one('tp.report.document', required=True)
    target_version = fields.Integer(related='target_document_id.version', readonly=True)
    work_date = fields.Date(required=True)
    reason = fields.Text(required=True)

    def action_carry(self):
        self.ensure_one()
        source, target = self.line_id, self.target_document_id
        source.check_access('read')
        if not self.env.su and self.env.context.get('tp_reporting_expected_version') is None:
            raise UserError(_('Thiếu phiên bản báo cáo đích; mở lại popup chuyển tiếp.'))
        target._locked()
        if source.owner_id != self.env.user or target.owner_id != self.env.user or source.company_id != target.company_id or target.state not in ('draft', 'returned') or target.level != 'personal':
            raise AccessError(_('Chuyển tiếp trong hai báo cáo của chính mình, cùng công ty và nháp đích.'))
        if source.work_status == 'done' or target.date_start <= source.document_id.date_start or not target.date_start <= self.work_date <= target.date_end or not self.reason.strip():
            raise ValidationError(_('Chọn kỳ sau, ngày đúng kỳ và lý do; việc đã xong không chuyển tiếp.'))
        existing = self.env['tp.report.line'].search([('document_id', '=', target.id), ('stable_key', '=', source.stable_key)], limit=1)
        if existing:
            if existing.origin_line_id != source or existing.work_date != self.work_date or existing.carry_reason != self.reason:
                raise ValidationError(_('Đầu việc đã chuyển tiếp với ngày/lý do khác; mở dòng hiện có để đối chiếu.'))
            return {'type': 'ir.actions.act_window', 'res_model': existing._name, 'res_id': existing.id, 'view_mode': 'form'}
        if self.env.context.get('tp_reporting_expected_version') != target.version and not self.env.su:
            raise UserError(_('Báo cáo đích đã thay đổi. Mở lại popup chuyển tiếp.'))
        line = self.env['tp.report.line'].with_context(tp_reporting_provenance=_INTERNAL, tp_reporting_draft_batch=_INTERNAL).create({
            'document_id': target.id, 'name': source.name, 'work_date': self.work_date,
            'unit': source.unit, 'quantity': 0, 'quantity_known': False,
            'planned_quantity_known': False, 'contribution_key': source.contribution_key,
            'stable_key': source.stable_key, 'task_id': source.task_id.id, 'project_id': source.project_id.id,
            'expected_output': source.expected_output, 'work_deadline': source.work_deadline,
            'priority': source.priority, 'collaborator_ids': [fields.Command.set(source.collaborator_ids.ids)],
            'origin_line_id': source.id, 'carry_reason': self.reason, 'work_status': 'todo',
        })
        target._internal_write({'version': target.version + 1})
        return {'type': 'ir.actions.act_window', 'res_model': line._name, 'res_id': line.id, 'view_mode': 'form'}
