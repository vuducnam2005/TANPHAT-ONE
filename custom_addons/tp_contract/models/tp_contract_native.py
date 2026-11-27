"""Narrow native UI adapters. All business writes stay in CTR-002a workflow."""
import base64
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from lxml import etree

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, RedirectWarning, UserError
from odoo.tools import float_repr

from .tp_contract import CONTRACT_TYPES
from .tp_contract_line import TAX_BASES
from .tp_contract_revision import REVIEW_STATES
from .tp_contract_workflow import DECIMAL_PATTERN, MAX_AMOUNT_DIGITS
from odoo.addons.tp_contract.exceptions import ContractWorkflowError

ERRORS = {
    'forbidden': 'Bạn chưa được cấp quyền cho thao tác này trong phạm vi hợp đồng.',
    'not_found': 'Không tìm thấy hồ sơ, hoặc hồ sơ nằm ngoài phạm vi được phân công.',
    'stale_version': 'Hồ sơ vừa được cập nhật ở nơi khác. Tải lại bản mới nhất rồi thực hiện lại; thay đổi chưa được lưu.',
    'invalid_state': 'Trạng thái bản hợp đồng đã thay đổi. Tải lại để xem trạng thái hiện tại.',
    'duplicate_code': 'Số hợp đồng này đã được dùng trong công ty.',
    'idempotency_conflict': 'Thao tác trùng với một yêu cầu khác. Vui lòng thử lại.',
    'not_assigned_reviewer': 'Chỉ người rà soát được giao cho lần trình này mới trả lại được.',
    'reviewer_ineligible': 'Người rà soát đã chọn không còn đủ quyền rà soát hợp đồng này.',
    'scope_incomplete': 'Dự án chưa có phòng ban chủ trì nên chưa tạo được hợp đồng.',
    'header_locked': 'Thông tin chung chỉ sửa được ở bản gốc.',
    'fix_summary_required': 'Cần mô tả nội dung đã sửa so với lần bị trả lại.',
    'reason_required': 'Cần nhập lý do.',
    'issue_note_required': 'Mỗi ý kiến cần có nội dung.',
    'unknown_scope_key': 'Ý kiến tham chiếu dòng phạm vi không có trong lần trình.',
    'code_required': 'Cần nhập số hợp đồng.',
    'name_required': 'Cần nhập tên.',
    'unknown_currency': 'Đơn vị tiền tệ không có hoặc chưa được kích hoạt.',
    'unknown_partner': 'Đối tác không có hoặc thuộc công ty khác.',
    'amount_value_required': 'Giá trị đã xác nhận cần có số tiền.',
    'amount_value_not_allowed': 'Giá trị chưa xác nhận thì để trống số tiền.',
    'amount_negative': 'Giá trị dòng phạm vi không được âm.',
    'amount_too_large': 'Số tiền có quá nhiều chữ số.',
    'amount_precision': 'Số tiền có nhiều chữ số thập phân hơn đơn vị tiền tệ cho phép.',
    'invalid_request': 'Dữ liệu gửi lên chưa hợp lệ.',
}
PROBLEMS = {
    'no_lines': 'bản nháp chưa có dòng phạm vi',
    'amounts_not_confirmed': 'còn dòng chưa xác nhận giá trị',
    'tax_basis_mixed': 'các dòng khác cơ sở thuế',
}
IMMUTABLE = {'contract_id', 'revision_id', 'project_id', 'company_id', 'expected_version', 'key', 'mode',
             'state', 'result_revision_id', 'operation'}


def revision_action(revision):
    revision.check_access('read')
    # The web client caches reads for an action/context. A completed transition
    # must reload its new version, even when returning to the very same revision.
    action = revision.env['ir.actions.actions']._for_xml_id('tp_contract.action_tp_contract_revisions')
    context = {key: value for key, value in revision.env.context.items()
               if not key.startswith(('default_', 'search_default_'))}
    context['tp_native_version'] = revision.contract_id.aggregate_version
    context.setdefault('tp_kd_leaf', 'tp_kd_workspace.menu_contracts')
    action.update({
        'name': 'TP Contracts',
        'res_id': revision.id,
        'view_mode': 'form',
        'views': [(False, 'form')],
        'target': 'current',
        'context': context,
    })
    return action


class NativeMixin(models.AbstractModel):
    _name = 'tp.contract.native.mixin'
    _description = 'Native contract workflow adapter'

    contract_id = fields.Many2one('tp.contract', readonly=True, string='Hợp đồng')
    revision_id = fields.Many2one('tp.contract.revision', readonly=True, string='Bản hợp đồng')
    project_id = fields.Many2one('project.project', required=True, string='Dự án')
    company_id = fields.Many2one('res.company', required=True, readonly=True, string='Công ty')
    expected_version = fields.Integer(readonly=True, string='Phiên bản đối chiếu')
    key = fields.Char(readonly=True, copy=False, string='Khóa thao tác')
    state = fields.Selection([('draft', 'Nháp'), ('done', 'Hoàn tất')], default='draft', readonly=True, string='Trạng thái')
    result_revision_id = fields.Many2one('tp.contract.revision', readonly=True, copy=False, string='Bản kết quả')

    @api.model
    def _tp_defaults(self, values):
        """Only load metadata, with the caller's access; never copy existing money."""
        vals = dict(values)
        contract_id = vals.get('contract_id')
        revision_id = vals.get('revision_id')
        if contract_id:
            contract = self.env['tp.contract'].search([('id', '=', contract_id)], limit=1)
            if not contract:
                raise AccessError(ERRORS['not_found'])
            revision = self.env['tp.contract.revision']
            if revision_id:
                revision = revision.search([('id', '=', revision_id), ('contract_id', '=', contract.id)], limit=1)
                if not revision:
                    raise AccessError(ERRORS['not_found'])
            elif self._name not in ('tp.contract.native.amendment',):
                raise AccessError(ERRORS['not_found'])
            vals.update(project_id=contract.project_id.id, company_id=contract.company_id.id)
            vals.setdefault('expected_version', contract.aggregate_version)
            if self._name == 'tp.contract.native.draft':
                vals['mode'] = 'edit'
                for name in ('code', 'name', 'contract_type', 'partner_id', 'currency_id'):
                    value = contract[name]
                    vals.setdefault(name, value.id if contract._fields[name].type == 'many2one' else value)
                vals.setdefault('revision_name', revision.name)
                vals.setdefault('revision_reference', revision.reference)
                vals.setdefault('line_ids', [Command.create({'scope_key': line.scope_key, 'name': line.name})
                                             for line in revision.line_ids])
        else:
            if self._name != 'tp.contract.native.draft' or revision_id:
                raise AccessError(ERRORS['not_found'])
            project = self.env['project.project'].search([
                ('id', '=', vals.get('project_id')), ('tp_managed', '=', True),
            ], limit=1)
            if not project:
                raise AccessError(ERRORS['not_found'])
            vals.update(mode='create', company_id=project.company_id.id)
        return vals

    @api.model
    def default_get(self, names):
        # Ignore all defaults for amount inputs, even if supplied in a crafted context.
        clean = {k: v for k, v in self.env.context.items() if not k.startswith('default_amount')}
        values = super(NativeMixin, self.with_context(clean)).default_get(names)
        if values.get('contract_id'):
            for name in ('code', 'name', 'contract_type', 'partner_id', 'currency_id'):
                values.pop(name, None)
            values = self._tp_defaults(values)
        return {k: v for k, v in values.items() if k in names and k != 'amount_input_ids'}

    @api.model_create_multi
    def create(self, vals_list):
        clean = {k: v for k, v in self.env.context.items() if not k.startswith('default_amount')}
        prepared = []
        for supplied in vals_list:
            values = super(NativeMixin, self.with_context(clean)).default_get(list(self._fields))
            values.pop('amount_input_ids', None)
            values.update(supplied)
            if values.get('contract_id'):
                for name in ('code', 'name', 'contract_type', 'partner_id', 'currency_id'):
                    if name not in supplied:
                        values.pop(name, None)
            values = self._tp_defaults(values)
            values.update(key='native-' + uuid4().hex, state='draft', result_revision_id=False)
            prepared.append(values)
        return super(NativeMixin, self.with_context(clean)).create(prepared)

    def write(self, vals):
        self.check_access('write')
        if IMMUTABLE & vals.keys():
            raise UserError(self.env._('Đích và kết quả thao tác do máy chủ quản lý. Hãy mở hộp nhập mới.'))
        if any(wizard.state == 'done' for wizard in self):
            raise UserError(self.env._('Thao tác đã hoàn tất. Hãy tải lại hồ sơ.'))
        return super().write(vals)

    def copy(self, default=None):
        self.check_access('read')
        raise UserError(self.env._('Hãy mở hộp nhập mới thay vì sao chép thao tác.'))

    def _tp_check_target(self):
        self.ensure_one()
        if self.contract_id:
            contract = self.env['tp.contract'].search([('id', '=', self.contract_id.id)], limit=1)
            if (not contract or contract.project_id != self.project_id or contract.company_id != self.company_id
                    or (self.revision_id and self.revision_id.contract_id != contract)):
                raise AccessError(ERRORS['not_found'])
        elif (self._name != 'tp.contract.native.draft' or self.mode != 'create' or self.revision_id
              or not self.project_id.has_access('read') or not self.project_id.tp_managed
              or self.company_id != self.project_id.company_id):
            raise AccessError(ERRORS['not_found'])

    def _tp_amount_display_allowed(self):
        self.ensure_one()
        if not self.project_id or not self.project_id.has_access('read'):
            return False
        department = self.contract_id.department_id if self.contract_id else self.project_id.tp_department_id
        return 'financial_read' in self.env['tp.contract.workflow']._tp_capabilities(self.project_id, department)

    def _tp_error(self, error):
        message = ERRORS.get(error.code, 'Chưa thực hiện được thao tác. Kiểm tra dữ liệu và quyền trong hồ sơ.')
        if error.code == 'submission_incomplete':
            message = 'Chưa trình rà soát được: ' + '; '.join(
                PROBLEMS.get(p, 'cần kiểm tra dữ liệu') for p in (error.details or {}).get('problems', [])
            ) + '.'
        if error.status in (403, 404):
            raise AccessError(message) from error
        if error.code in ('stale_version', 'invalid_state'):
            raise RedirectWarning(message, revision_action(self.revision_id), 'Tải lại hồ sơ') from error
        raise UserError(message) from error

    def action_confirm(self):
        self.ensure_one()
        if self.env.su:
            raise AccessError(ERRORS['forbidden'])
        self.check_access('write')
        if self.create_uid.id != self.env.uid:
            raise AccessError(ERRORS['forbidden'])
        if self.state == 'done':
            return revision_action(self.result_revision_id)
        self._tp_check_target()
        try:
            # Includes cleanup and completion: no partial workflow on a later validation error.
            with self.env.cr.savepoint():
                action, payload = self._tp_payload()
                result = self.env['tp.contract.workflow']._tp_run(
                    action, payload, key=self.key, contract_id=self.contract_id.id,
                    revision_id=self.revision_id.id, request_id=self.key,
                    intervention_reason=(self.reason or None) if self._name == 'tp.contract.native.draft' and self.mode == 'edit' else None,
                )
                if self._name == 'tp.contract.native.draft':
                    self.amount_input_ids.unlink()
                super().write({'state': 'done', 'result_revision_id': result['revision'].id})
                return revision_action(result['revision'])
        except ContractWorkflowError as error:
            self._tp_error(error)


class NativeDraft(models.TransientModel):
    _name = 'tp.contract.native.draft'
    _inherit = 'tp.contract.native.mixin'
    _description = 'Create or edit contract draft'

    mode = fields.Selection([('create', 'Tạo mới'), ('edit', 'Chỉnh sửa')], readonly=True, default='create', string='Chế độ')
    code = fields.Char(string='Số hợp đồng')
    name = fields.Char(string='Tên hợp đồng')
    contract_type = fields.Selection(CONTRACT_TYPES, default='owner', string='Loại hợp đồng')
    partner_id = fields.Many2one('res.partner', string='Đối tác')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, string='Tiền tệ')
    revision_name = fields.Char(string='Tên bản hợp đồng')
    revision_reference = fields.Char(string='Số văn bản')
    line_ids = fields.One2many('tp.contract.native.draft.line', 'wizard_id', string='Dòng phạm vi')
    amount_input_ids = fields.One2many('tp.contract.native.amount.input', 'wizard_id', string='Giá trị mới')
    allowed_project_ids = fields.Many2many('project.project', compute='_compute_permissions')
    can_edit_header = fields.Boolean(compute='_compute_permissions')
    can_edit_money = fields.Boolean(compute='_compute_permissions')
    reason = fields.Text(string="Lý do can thiệp nháp")
    needs_intervention_reason = fields.Boolean(compute="_compute_permissions")

    @api.depends('project_id', 'contract_id', 'revision_id', 'mode')
    @api.depends_context('uid')
    def _compute_permissions(self):
        workflow = self.env['tp.contract.workflow']
        projects = self.env['project.project'].search([('tp_managed', '=', True)])
        allowed = projects.filtered(lambda p: 'contract_draft_edit' in workflow._tp_capabilities(p, p.tp_department_id))
        for wizard in self:
            wizard.allowed_project_ids = allowed
            wizard.needs_intervention_reason = bool(wizard.revision_id and
                self.env['tp.kd.department.role']._is_head(project=wizard.project_id) and
                workflow._tp_business_owner(wizard.revision_id) != self.env.user)
            wizard.can_edit_header = wizard.mode == 'create' or wizard.revision_id.revision_kind == 'original'
            department = wizard.contract_id.department_id if wizard.contract_id else wizard.project_id.tp_department_id
            held = workflow._tp_capabilities(wizard.project_id, department) if wizard.project_id else set()
            wizard.can_edit_money = {'financial_read', 'financial_draft_edit'} <= held

    def _tp_payload(self):
        Amount = self.env['tp.contract.native.amount.input']
        visible = self.amount_input_ids
        # Deliberate count-only sudo: detect values hidden by revocation; never read their contents.
        if Amount.sudo().search_count([('wizard_id', '=', self.id)]) != len(visible):
            raise ContractWorkflowError(403, 'forbidden', ERRORS['forbidden'])
        lines = [{'scope_key': line.scope_key or '', 'name': line.name or ''} for line in self.line_ids]
        by_key = {line['scope_key']: line for line in lines}
        seen = set()
        for entry in visible:
            if entry.scope_key not in by_key or entry.scope_key in seen:
                raise UserError(self.env._('Mỗi giá trị mới phải thuộc một mã phạm vi duy nhất trong hộp nhập.'))
            seen.add(entry.scope_key)
            raw = entry.value.strip() if entry.value else None
            if raw is not None:
                if not DECIMAL_PATTERN.fullmatch(raw):
                    raise UserError(self.env._('Số tiền phải là chuỗi thập phân hợp lệ, dùng dấu chấm cho phần thập phân.'))
                value = Decimal(raw)
                try:
                    valid = (value >= 0 and value.adjusted() + 1 + self.currency_id.decimal_places <= MAX_AMOUNT_DIGITS
                             and value == value.quantize(Decimal(1).scaleb(-self.currency_id.decimal_places)))
                except InvalidOperation:
                    valid = False
                if not valid:
                    raise UserError(self.env._('Số tiền không được âm, vượt giới hạn chữ số hoặc sai độ chính xác tiền tệ.'))
            by_key[entry.scope_key]['amount'] = {'state': entry.amount_state, 'value': raw, 'tax_basis': entry.tax_basis}
        header = {'code': self.code or '', 'name': self.name or '', 'contract_type': self.contract_type,
                  'currency': self.currency_id.name or '', 'partner_id': self.partner_id.id or None}
        revision = {'name': self.revision_name or self.name or '', 'reference': self.revision_reference or None}
        if self.mode == 'create':
            return 'create_contract', header | {'project_id': self.project_id.id, 'revision': revision, 'lines': lines}
        changed = {}
        for name in ('code', 'name', 'contract_type', 'partner_id', 'currency_id'):
            if self[name] != self.contract_id[name]:
                key = 'currency' if name == 'currency_id' else name
                changed[key] = header[key]
        payload = {'expected_version': self.expected_version, 'revision': revision, 'lines': lines}
        if changed:
            payload['contract'] = changed
        return 'edit_draft', payload


class NativeAmendment(models.TransientModel):
    _name = 'tp.contract.native.amendment'
    _inherit = 'tp.contract.native.mixin'
    _description = 'Create draft amendment'

    name = fields.Char(string='Tên phụ lục')
    reference = fields.Char(string='Số văn bản')

    def _tp_payload(self):
        return 'create_amendment', {'expected_version': self.expected_version, 'name': self.name or '',
                                    'reference': self.reference or None}


class NativeSubmit(models.TransientModel):
    _name = 'tp.contract.native.submit'
    _inherit = 'tp.contract.native.mixin'
    _description = 'Submit contract for review'

    reviewer_id = fields.Many2one('res.users', string='Người rà soát')
    eligible_reviewer_ids = fields.Many2many('res.users', compute='_compute_review')
    fix_summary = fields.Text(string='Nội dung đã sửa')
    is_resubmit = fields.Boolean(compute='_compute_review')
    last_return_reason = fields.Text(compute='_compute_review', string='Lý do trả lại gần nhất')
    last_return_issues = fields.Text(compute='_compute_review', string='Ý kiến cần xử lý')

    @api.depends('contract_id', 'revision_id')
    @api.depends_context('uid')
    def _compute_review(self):
        workflow = self.env['tp.contract.workflow']
        for wizard in self:
            department = wizard.contract_id.department_id
            held = workflow._tp_capabilities(wizard.contract_id.project_id, department)
            wizard.eligible_reviewer_ids = (workflow._tp_eligible_reviewers(wizard.contract_id, wizard.revision_id)
                                           if 'contract_submit' in held else self.env['res.users'])
            previous = wizard.revision_id.submission_ids.sorted('sequence')[-1:]
            wizard.is_resubmit = bool(previous)
            wizard.last_return_reason = previous.return_reason
            wizard.last_return_issues = '\n'.join(f"{i.get('scope_key', '')}: {i.get('note', '')}"
                                                   for i in previous.return_issues or [])

    def _tp_payload(self):
        return 'submit_review', {'expected_version': self.expected_version, 'reviewer_id': self.reviewer_id.id,
                                 'fix_summary': self.fix_summary or None}


class NativeReturn(models.TransientModel):
    _name = 'tp.contract.native.return'
    _inherit = 'tp.contract.native.mixin'
    _description = 'Return contract for revision'

    operation = fields.Selection([
        ('return_review', 'Trả lại'), ('take_review', 'Nhận rà soát'), ('assign_owner', 'Phân công'),
        ('document_add', 'Thêm tài liệu nháp'), ('document_remove', 'Gỡ tài liệu nháp'),
    ], default='return_review', required=True, readonly=True)
    owner_id = fields.Many2one('res.users', string='Người phụ trách mới')
    eligible_owner_ids = fields.Many2many('res.users', compute='_compute_owners')
    document_id = fields.Many2one('tp.contract.document', string='Tài liệu cần gỡ')
    document_name = fields.Char(string='Tên tài liệu')
    document_kind = fields.Selection([('technical_scope', 'Phạm vi kỹ thuật'), ('other', 'Căn cứ khác')],
                                     default='other', string='Loại tài liệu')
    confidentiality = fields.Selection([('financial', 'Tài chính'), ('general', 'Thông thường')],
                                       default='financial', string='Phân loại')
    file = fields.Binary(string='Tệp')
    file_name = fields.Char(string='Tên tệp')
    reason = fields.Text(string='Lý do / ý kiến')

    @api.depends('contract_id')
    @api.depends_context('uid')
    def _compute_owners(self):
        workflow = self.env['tp.contract.workflow']
        for wizard in self:
            project, department = wizard.contract_id.project_id, wizard.contract_id.department_id
            candidates = self.env['tp.project.assignment'].sudo().search([
                ('project_id', '=', project.id), ('active', '=', True)]).user_id
            candidates |= self.env['tp.kd.department.role']._head_users(project) if project else self.env['res.users']
            wizard.eligible_owner_ids = candidates.filtered(lambda user: user.active and
                'contract_draft_edit' in workflow._tp_capabilities(project, department, user))
    issue_ids = fields.One2many('tp.contract.native.return.issue', 'wizard_id', string='Ý kiến theo dòng')
    available_scope_keys = fields.Char(compute='_compute_keys', string='Mã phạm vi trong lần trình')

    def _compute_keys(self):
        for wizard in self:
            pending = wizard.revision_id.submission_ids.filtered(lambda s: s.outcome == 'pending')
            wizard.available_scope_keys = ', '.join(i['scope_key'] for i in (pending.metadata_snapshot or {}).get('lines', []))

    def _tp_payload(self):
        if self.operation != 'return_review':
            payload = {'expected_version': self.expected_version, 'reason': self.reason or None}
            if self.operation == 'assign_owner':
                payload['owner_id'] = self.owner_id.id
            elif self.operation == 'document_remove':
                payload['document_id'] = self.document_id.id
            elif self.operation == 'document_add':
                payload.update(name=self.document_name or None, document_kind=self.document_kind,
                               confidentiality=self.confidentiality, file_name=self.file_name or None,
                               file=base64.b64encode(bytes(self.file)).decode() if self.file else None)
            return self.operation, payload
        return 'return_review', {'expected_version': self.expected_version, 'reason': self.reason or None,
                                 'issues': [{'scope_key': issue.scope_key or None, 'note': issue.note or None}
                                            for issue in self.issue_ids]}


class NativeRework(models.TransientModel):
    _name = 'tp.contract.native.rework'
    _inherit = 'tp.contract.native.mixin'
    _description = 'Begin contract rework'

    reason = fields.Text(string='Lý do bắt đầu chỉnh sửa')

    def _tp_payload(self):
        return 'begin_rework', {'expected_version': self.expected_version, 'reason': self.reason or None}


class NativeChildMixin(models.AbstractModel):
    _name = 'tp.contract.native.child.mixin'
    _description = 'Owned native input row'

    def write(self, vals):
        self.check_access('write')
        if 'wizard_id' in vals:
            raise UserError(self.env._('Dòng nhập không thể chuyển sang hộp nhập khác.'))
        return super().write(vals)

    def copy(self, default=None):
        self.check_access('read')
        raise UserError(self.env._('Dòng nhập không thể sao chép.'))


class NativeDraftLine(models.TransientModel):
    _name = 'tp.contract.native.draft.line'
    _inherit = 'tp.contract.native.child.mixin'
    _description = 'Draft scope metadata input'
    _order = 'id'

    wizard_id = fields.Many2one('tp.contract.native.draft', required=True, ondelete='cascade')
    scope_key = fields.Char(required=True, string='Mã phạm vi')
    name = fields.Char(required=True, string='Nội dung')
    current_amount_text = fields.Char(compute='_compute_current_amount', compute_sudo=False, string='Giá trị hiện tại')

    @api.depends('wizard_id.project_id', 'wizard_id.revision_id', 'scope_key')
    @api.depends_context('uid')
    def _compute_current_amount(self):
        for wizard in self.wizard_id:
            lines = self.filtered(lambda line: line.wizard_id == wizard)
            lines.current_amount_text = False
            if not wizard._tp_amount_display_allowed() or not wizard.revision_id:
                continue
            amounts = self.env['tp.contract.line.amount'].search([('revision_id', '=', wizard.revision_id.id)])
            by_key = {amount.line_id.scope_key: amount for amount in amounts}
            for line in lines:
                amount = by_key.get(line.scope_key)
                if amount:
                    line.current_amount_text = (float_repr(amount.amount, wizard.currency_id.decimal_places)
                                                if amount.amount_state == 'confirmed' else 'Chưa xác nhận')


class NativeAmountInput(models.TransientModel):
    _name = 'tp.contract.native.amount.input'
    _inherit = 'tp.contract.native.child.mixin'
    _description = 'New financial input, never a baseline copy'

    wizard_id = fields.Many2one('tp.contract.native.draft', required=True, ondelete='cascade')
    scope_key = fields.Char(required=True, string='Mã phạm vi')
    amount_state = fields.Selection([('unconfirmed', 'Chưa xác nhận'), ('confirmed', 'Đã xác nhận')],
                                    required=True, default='unconfirmed', string='Xác nhận giá trị')
    value = fields.Char(string='Số tiền mới')
    tax_basis = fields.Selection(TAX_BASES, required=True, default='unknown', string='Cơ sở thuế')

    @api.model
    def default_get(self, names):
        return super(NativeAmountInput, self.with_context({
            k: v for k, v in self.env.context.items() if k not in ('default_value', 'default_amount_state', 'default_tax_basis')
        })).default_get(names)


class NativeReturnIssue(models.TransientModel):
    _name = 'tp.contract.native.return.issue'
    _inherit = 'tp.contract.native.child.mixin'
    _description = 'Return review issue input'

    wizard_id = fields.Many2one('tp.contract.native.return', required=True, ondelete='cascade')
    scope_key = fields.Char(string='Mã phạm vi')
    note = fields.Text(string='Nội dung ý kiến')


class ContractNativeViews(models.Model):
    _inherit = 'tp.contract'

    tp_latest_review_state = fields.Selection(REVIEW_STATES, compute='_compute_native')
    tp_available_actions = fields.Char(compute='_compute_native')
    tp_can_create_amendment = fields.Boolean(compute='_compute_native')
    tp_document_count = fields.Integer(compute='_compute_native')

    @api.depends_context('uid')
    def _compute_native(self):
        for contract in self:
            latest = contract.revision_ids.sorted('sequence')[-1:]
            actions, _held = self.env['tp.contract.workflow']._tp_available_actions(contract, native=True)
            contract.tp_latest_review_state = latest.review_state
            contract.tp_available_actions = ','.join(actions)
            contract.tp_can_create_amendment = 'create_amendment' in actions
            contract.tp_document_count = self.env['tp.contract.document'].search_count([('contract_id', '=', contract.id)])

    @api.model
    def get_kd_ui_permissions(self):
        projects = self.env['project.project'].search([('tp_managed', '=', True)])
        workflow = self.env['tp.contract.workflow']
        can_create = any('contract_draft_edit' in workflow._tp_capabilities(p, p.tp_department_id) for p in projects)
        return {'can_create_contract': can_create, 'create': can_create}

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options=options)
        list_view = (res.get('views') or {}).get('list')
        if list_view and list_view.get('arch'):
            can_create = self.get_kd_ui_permissions()['can_create_contract']
            doc = etree.fromstring(list_view['arch'])
            changed = False
            for btn in doc.xpath(".//header/button[@type='action']"):
                btn.set('invisible', '0' if can_create else '1')
                changed = True
            if changed:
                list_view['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    def action_tp_open_documents(self):
        self.ensure_one()
        self.check_access('read')
        action = self.env['ir.actions.actions']._for_xml_id('tp_contract.action_tp_contract_documents')
        ctx = {k: v for k, v in self.env.context.items() if not k.startswith(('default_', 'search_default_'))}
        ctx['tp_kd_leaf'] = 'tp_kd_workspace.menu_contracts'
        action.update({
            'name': 'Tài liệu hợp đồng',
            'domain': [('contract_id', '=', self.id)],
            'context': ctx,
        })
        return action

    def action_tp_open_audit(self):
        self.ensure_one()
        self.check_access('read')
        action = self.env['ir.actions.actions']._for_xml_id('tp_contract.action_tp_contract_audits')
        ctx = {k: v for k, v in self.env.context.items() if not k.startswith(('default_', 'search_default_'))}
        ctx['tp_kd_leaf'] = 'tp_kd_workspace.menu_contracts'
        action.update({
            'name': 'Lịch sử hợp đồng',
            'domain': [('contract_id', '=', self.id)],
            'context': ctx,
        })
        return action


class RevisionNativeViews(models.Model):
    _inherit = 'tp.contract.revision'

    tp_contract_version = fields.Integer(related='contract_id.aggregate_version', compute_sudo=False)
    tp_available_actions = fields.Char(compute='_compute_native_actions')
    tp_can_edit_draft = fields.Boolean(compute='_compute_native_actions')
    tp_can_submit_review = fields.Boolean(compute='_compute_native_actions')
    tp_can_return_review = fields.Boolean(compute='_compute_native_actions')
    tp_can_begin_rework = fields.Boolean(compute='_compute_native_actions')
    tp_can_take_review = fields.Boolean(compute='_compute_native_actions')
    tp_can_assign_owner = fields.Boolean(compute='_compute_native_actions')
    tp_can_document_add = fields.Boolean(compute='_compute_native_actions')
    tp_can_document_remove = fields.Boolean(compute='_compute_native_actions')
    tp_is_resubmit = fields.Boolean(compute='_compute_native_actions')
    tp_amount_summary_text = fields.Char(compute='_compute_summary', compute_sudo=False)
    tp_financial_read_granted = fields.Boolean(related='project_id.tp_financial_read_granted', compute_sudo=False)

    @api.depends_context('uid')
    def _compute_native_actions(self):
        for revision in self:
            actions, _held = self.env['tp.contract.workflow']._tp_available_actions(revision.contract_id, revision, native=True)
            revision.tp_available_actions = ','.join(actions)
            revision.tp_is_resubmit = bool(revision.submission_ids)
            for action in ('edit_draft', 'submit_review', 'return_review', 'begin_rework',
                           'take_review', 'assign_owner', 'document_add', 'document_remove'):
                revision['tp_can_' + action] = action in actions

    @api.depends_context('uid')
    def _compute_summary(self):
        labels = {'incomplete': 'Chưa đủ giá trị đã xác nhận', 'mixed_basis': 'Khác cơ sở thuế, không cộng tổng',
                  'empty': 'Chưa có dòng phạm vi'}
        for revision in self:
            revision.tp_amount_summary_text = False
            if revision.project_id.tp_financial_read_granted:
                summary = revision._amount_summary()
                revision.tp_amount_summary_text = (f"{summary['value']} {summary['currency'].name}"
                                                   if summary['status'] == 'confirmed' else labels[summary['status']])

    def action_tp_open_amounts(self):
        self.ensure_one()
        self.check_access('read')
        action = self.env['ir.actions.actions']._for_xml_id('tp_contract.action_tp_contract_line_amounts')
        ctx = {k: v for k, v in self.env.context.items() if not k.startswith(('default_', 'search_default_'))}
        ctx['tp_kd_leaf'] = 'tp_kd_workspace.menu_contracts'
        action.update({
            'name': 'Số tiền theo dòng',
            'domain': [('revision_id', '=', self.id)],
            'context': ctx,
        })
        return action


class SubmissionNativeViews(models.Model):
    _inherit = 'tp.contract.submission'

    tp_return_issues_text = fields.Text(compute='_compute_issues_text', string='Ý kiến theo dòng')

    def _compute_issues_text(self):
        for submission in self:
            submission.tp_return_issues_text = '\n'.join(
                f"{issue.get('scope_key') or 'Chung'}: {issue.get('note') or ''}"
                for issue in submission.return_issues or []
            )
