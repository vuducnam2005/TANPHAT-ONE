"""Narrow, journalled department operations; ordinary grants keep their policy."""
import hashlib
import json
import uuid

from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Domain
from odoo.tools import SQL
from odoo.tools.misc import formatLang

from .native_content_security import attachment_parent_ids
from .workspace import _INTERNAL


def head_candidates(env, company, department):
    teams = env['crm.team'].sudo().search([('company_id', '=', company.id),
        ('kd_department_id', '=', department.id), ('active', '=', True)])
    roles = env['tp.kd.department.role'].sudo().search([
        ('company_id', '=', company.id), ('department_id', '=', department.id)])
    users = teams.member_ids | roles.user_id.filtered(lambda u:
        env['tp.kd.department.role']._is_head(company=company, department=department, user=u))
    return users.filtered(lambda u: u.active and company in u.company_ids and u._is_internal())


def head_event(env, operation, reason, before, after, *, project=None, lead=None):
    company = project.company_id if project else lead.company_id
    department = project.tp_department_id if project else lead.team_id.kd_department_id
    return env['tp.kd.head.event'].sudo().with_context(_kd_internal=_INTERNAL).create({
        'project_id': project.id if project else False, 'lead_id': lead.id if lead else False,
        'company_id': company.id, 'department_id': department.id, 'actor_id': env.uid,
        'operation': operation, 'reason': reason, 'before_values': before, 'after_values': after,
    })


class HeadEvent(models.Model):
    _name = 'tp.kd.head.event'
    _description = 'Department management immutable journal'
    _order = 'id desc'
    project_id = fields.Many2one('project.project', ondelete='restrict')
    lead_id = fields.Many2one('crm.lead', ondelete='restrict')
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict')
    department_id = fields.Many2one('hr.department', required=True, ondelete='restrict')
    actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    operation = fields.Char(required=True)
    reason = fields.Text(required=True)
    before_values = fields.Json()
    after_values = fields.Json()
    kd_accessible = fields.Boolean(compute='_compute_accessible', search='_search_accessible')

    @api.depends_context('uid')
    def _compute_accessible(self):
        for rec in self:
            rec.kd_accessible = self.env['tp.kd.department.role']._is_head(
                company=rec.company_id, department=rec.department_id)

    def _search_accessible(self, operator, value):
        if operator != 'in' or set(value) != {True}:
            return NotImplemented
        roles = self.env['tp.kd.department.role']._roles()
        return Domain.OR([Domain('company_id', '=', r.company_id.id)
            & Domain('department_id', '=', r.department_id.id) for r in roles])

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('_kd_internal') is not _INTERNAL:
            raise AccessError(self.env._('Nhật ký chỉ do thao tác máy chủ tạo.'))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._('Không sửa nhật ký quản lý.'))

    def unlink(self):
        raise AccessError(self.env._('Không xóa nhật ký quản lý.'))


class HeadCommand(models.TransientModel):
    _name = 'tp.kd.head.command'
    _description = 'Scoped department management command'
    operation = fields.Selection([('project_create', 'Tạo dự án KH-KD'),
        ('project_assign', 'Phân công chủ trì dự án'), ('lead_assign', 'Phân công hồ sơ dự án'),
        ('lead_document_add', 'Thêm tài liệu CRM'), ('lead_document_remove', 'Lưu trữ tài liệu CRM'),
        ('lead_comment', 'Ghi trao đổi CRM'),
        ('partner', 'Danh mục đối tác nghiệp vụ')], required=True, readonly=True)
    project_id = fields.Many2one('project.project', readonly=True)
    lead_id = fields.Many2one('crm.lead', readonly=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', required=True)
    name = fields.Char(string='Tên')
    code = fields.Char(string='Mã dự án')
    scope = fields.Text(string='Phạm vi / đầu ra')
    owner_id = fields.Many2one('res.users', string='Người phụ trách')
    eligible_owner_ids = fields.Many2many('res.users', compute='_compute_eligible_owners')
    partner_id = fields.Many2one('res.partner', string='Bên ký / đối tác')
    investor_id = fields.Many2one('res.partner', string='Chủ đầu tư')
    deadline = fields.Date(string='Mốc bàn giao')
    reason = fields.Text(required=True, string='Căn cứ / lý do')
    expected_version = fields.Integer(readonly=True)
    request_key = fields.Char(readonly=True, default=lambda self: str(uuid.uuid4()))
    result_payload_hash = fields.Char(readonly=True)
    result_project_id = fields.Many2one('project.project', readonly=True)
    result_partner_id = fields.Many2one('res.partner', readonly=True)
    email = fields.Char()
    phone = fields.Char()
    file = fields.Binary(attachment=False, string='Tệp đính kèm')
    file_name = fields.Char(string='Tên tệp')
    document_id = fields.Many2one('ir.attachment', string='Tài liệu cần lưu trữ')
    eligible_document_ids = fields.Many2many('ir.attachment', compute='_compute_eligible_documents')

    @api.depends('lead_id', 'lead_id.kd_head_version', 'operation')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_eligible_documents(self):
        for command in self:
            command.eligible_document_ids = command.lead_id._head_documents()

    def _eligible_owners(self):
        self.ensure_one()
        candidates = head_candidates(self.env, self.company_id, self.department_id)
        if self.operation == 'project_create':
            return candidates.filtered(lambda user: self.env['tp.kd.department.role']._is_head(
                company=self.company_id, department=self.department_id, user=user))
        project = self.lead_id.tp_project_id if self.lead_id else self.project_id
        if project:
            return candidates.filtered(project._tp_scope_allowed)
        team = self.lead_id.team_id
        return candidates.filtered(lambda user: team in self.env['crm.lead'].with_user(user)._kd_preproject_teams())

    @api.depends('company_id', 'department_id', 'project_id', 'lead_id', 'operation')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_eligible_owners(self):
        for command in self:
            command.eligible_owner_ids = command._eligible_owners()

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        protected = {'expected_version', 'request_key', 'result_project_id', 'result_partner_id', 'result_payload_hash'}
        if any('default_' + field in self.env.context for field in protected):
            raise AccessError(self.env._('Không truyền phiên bản hoặc kết quả qua context.'))
        defaults = self.default_get(['operation', 'project_id', 'lead_id', 'company_id', 'department_id'])
        for supplied in vals_list:
            vals = {**defaults, **supplied}
            if set(supplied) & protected:
                raise AccessError(self.env._('Phiên bản và kết quả do máy chủ quản lý.'))
            operation = vals.get('operation')
            if operation not in ('project_create', 'project_assign', 'lead_assign', 'partner',
                'lead_document_add', 'lead_document_remove', 'lead_comment'):
                raise ValidationError(self.env._('Chọn thao tác quản lý hợp lệ.'))
            if ((operation == 'project_create' and (vals.get('project_id') or vals.get('lead_id')))
                    or (operation.startswith('lead_') and (not vals.get('lead_id') or vals.get('project_id')))
                    or (operation in ('project_assign', 'partner') and (not vals.get('project_id') or vals.get('lead_id')))):
                raise AccessError(self.env._('Đích không khớp loại thao tác quản lý.'))
            p = self.env['project.project'].browse(vals.get('project_id'))
            lead = self.env['crm.lead'].browse(vals.get('lead_id'))
            if lead:
                lead.check_access('read')
                p = lead.tp_project_id
                vals.update(company_id=lead.company_id.id,
                    department_id=(p.tp_department_id if p else lead.team_id.kd_department_id).id,
                    expected_version=lead.kd_head_version)
            elif p:
                p.check_access('read')
                vals.update(company_id=p.company_id.id, department_id=p.tp_department_id.id,
                    expected_version=p.kd_version)
            else:
                vals.setdefault('company_id', self.env.company.id)
            company = self.env['res.company'].browse(vals.get('company_id'))
            department = self.env['hr.department'].browse(vals.get('department_id'))
            if (not company.exists() or not department.exists()
                    or department.sudo().company_id != company
                    or not self.env['tp.kd.department.role']._is_head(company=company, department=department)):
                raise AccessError(self.env._('Cần vai trò HEAD đang hiệu lực đúng phòng/công ty.'))
            prepared.append(vals)
        return super().create(prepared)

    def write(self, vals):
        if set(vals) & {'operation', 'project_id', 'lead_id', 'company_id', 'department_id',
            'expected_version', 'request_key', 'result_project_id', 'result_partner_id', 'result_payload_hash'}:
            raise AccessError(self.env._('Không thay đích hoặc phiên bản của thao tác.'))
        return super().write(vals)

    def action_confirm(self):
        self.ensure_one()
        self.check_access('read')
        role = self.env['tp.kd.department.role']
        if not role._is_head(company=self.company_id, department=self.department_id):
            raise AccessError(self.env._('Vai trò HEAD đã hết hiệu lực hoặc ngoài phòng.'))
        if not (self.reason or '').strip():
            raise UserError(self.env._('Cần căn cứ / lý do.'))
        # A wizard cannot be double-confirmed concurrently into two new records.
        self.env.cr.execute(SQL('SELECT id FROM tp_kd_head_command WHERE id=%s FOR UPDATE', self.id))
        self.invalidate_recordset()
        if not role._is_head(company=self.company_id, department=self.department_id):
            raise AccessError(self.env._('Vai trò HEAD đã hết hiệu lực.'))
        payload = {key: (self[key].id if self._fields[key].type == 'many2one' else self[key])
            for key in ('operation', 'project_id', 'lead_id', 'company_id', 'department_id',
                'expected_version', 'name', 'code', 'scope', 'owner_id', 'partner_id',
                'investor_id', 'deadline', 'reason', 'email', 'phone', 'file_name', 'document_id')}
        payload['file_sha256'] = hashlib.sha256(bytes(self.file)).hexdigest() if self.file else None
        payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        if self.result_payload_hash:
            if self.result_payload_hash != payload_hash:
                raise UserError(self.env._('Thao tác đã dùng với nội dung khác. Mở thao tác mới.'))
            if self.result_project_id:
                self.result_project_id.check_access('read')
                return self.result_project_id.action_kd_governance()
            return {'type': 'ir.actions.act_window_close'}
        p, lead = self.project_id, self.lead_id
        if self.operation == 'project_create':
            if self.result_project_id:
                self.result_project_id.check_access('read')
                return self.result_project_id.action_kd_governance()
            if not (self.name or '').strip() or not (self.code or '').strip():
                raise ValidationError(self.env._('Cần mã và tên dự án.'))
            if self.owner_id and self.owner_id not in self._eligible_owners():
                raise AccessError(self.env._('Chủ trì dự án mới phải có vai trò HEAD trong phòng; phân công nghiệp vụ không tự cấp quyền bảo mật.'))
            for partner in self.partner_id | self.investor_id:
                partner.check_access('read')
                if partner.company_id and partner.company_id != self.company_id:
                    raise AccessError(self.env._('Đối tác ngoài công ty.'))
            p = self.env['project.project'].sudo().with_context(tracking_disable=True,
                mail_create_nosubscribe=True, mail_create_nolog=True).create({
                    'name': self.name.strip(), 'tp_code': self.code.strip().upper(), 'tp_managed': True,
                    'company_id': self.company_id.id, 'tp_department_id': self.department_id.id,
                    'user_id': (self.owner_id or self.env.user).id, 'partner_id': self.partner_id.id,
                    'kd_investor_id': self.investor_id.id, 'kd_scope': self.scope,
                    'kd_deadline': self.deadline, 'privacy_visibility': 'followers',
                }).with_env(self.env)
            head_event(self.env, 'project_create', self.reason, None,
                {'name': p.name, 'code': p.tp_code, 'owner': p.user_id.id}, project=p)
            super().write({'result_project_id': p.id, 'result_payload_hash': payload_hash})
            return p.action_kd_governance()
        if self.operation == 'project_assign':
            p.check_access('read')
            if not p._tp_head_allowed() or self.owner_id not in self._eligible_owners():
                raise AccessError(self.env._('Chủ trì phải thuộc phòng dự án được giao.'))
            self.env.cr.execute(SQL('SELECT id FROM project_project WHERE id=%s FOR UPDATE', p.id))
            p.invalidate_recordset()
            if (not p._tp_head_allowed() or p.company_id != self.company_id
                    or p.tp_department_id != self.department_id):
                raise AccessError(self.env._('Phạm vi dự án đã đổi. Mở lại thao tác.'))
            if p.kd_version != self.expected_version:
                raise UserError(self.env._('Dự án đã đổi. Mở lại thao tác.'))
            before = {'owner': p.user_id.id, 'version': p.kd_version}
            p.sudo().with_context(_kd_internal=_INTERNAL).write({'user_id': self.owner_id.id,
                'kd_version': p.kd_version + 1})
            head_event(self.env, 'project_assign', self.reason, before,
                {'owner': p.user_id.id, 'version': p.kd_version}, project=p)
        elif self.operation == 'lead_assign':
            lead.check_access('read')
            lead._kd_lock_bid()
            p = lead.tp_project_id
            if (lead.company_id != self.company_id
                    or (p.tp_department_id if p else lead.team_id.kd_department_id) != self.department_id):
                raise AccessError(self.env._('Phạm vi hồ sơ đã đổi. Mở lại thao tác.'))
            if not lead._kd_head() or self.owner_id not in self._eligible_owners():
                raise AccessError(self.env._('Người nhận phải thuộc phòng hồ sơ.'))
            if lead.kd_bid_state == 'submitted' or lead.kd_head_version != self.expected_version:
                raise UserError(self.env._('Hồ sơ đã gửi hoặc đã đổi phiên bản.'))
            before = {'owner': lead.user_id.id, 'version': lead.kd_head_version}
            lead.sudo().with_context(_kd_internal=_INTERNAL).write({'user_id': self.owner_id.id,
                'kd_head_version': lead.kd_head_version + 1})
            head_event(self.env, 'lead_assign', self.reason, before,
                {'owner': lead.user_id.id, 'version': lead.kd_head_version}, project=p, lead=lead)
        elif self.operation in ('lead_document_add', 'lead_document_remove', 'lead_comment'):
            lead.check_access('read')
            lead._kd_lock_bid()
            p = lead.tp_project_id
            if (not lead._kd_head() or lead.company_id != self.company_id
                    or (p.tp_department_id if p else lead.team_id.kd_department_id) != self.department_id):
                raise AccessError(self.env._('Hồ sơ ngoài quyền HEAD hiện hành.'))
            if lead.kd_bid_state == 'submitted' or lead.kd_head_version != self.expected_version:
                raise UserError(self.env._('Hồ sơ đã gửi hoặc phiên bản đã đổi.'))
            before = {'version': lead.kd_head_version}
            after = {'version': lead.kd_head_version + 1}
            attachment_model = self.env['ir.attachment'].sudo().with_context(_kd_internal=_INTERNAL)
            if self.operation == 'lead_document_add':
                if not self.file or not (self.file_name or '').strip() or self.file.size > 20_000_000:
                    raise UserError(self.env._('Chọn tệp có tên, tối đa 20 MB.'))
                attachment = attachment_model.create({'res_model': 'crm.lead', 'res_id': lead.id,
                    'name': self.file_name.strip(), 'raw': self.file, 'type': 'binary',
                    'public': False, 'access_token': False})
                after.update(document=attachment.id, checksum=attachment.checksum, file_name=attachment.name)
            elif self.operation == 'lead_document_remove':
                attachment = self.document_id
                attachment.check_access('read')
                if (attachment_parent_ids(self.env, attachment.res_model, attachment.res_id) != [lead.id]
                        or attachment.kd_head_archived):
                    raise AccessError(self.env._('Chọn tài liệu đang hoạt động của đúng hồ sơ.'))
                before.update(document=attachment.id, checksum=attachment.checksum, file_name=attachment.name)
                attachment.sudo().with_context(_kd_internal=_INTERNAL).write({'kd_head_archived': True})
                after.update(document=attachment.id, archived=True)
            else:
                if not (self.scope or '').strip():
                    raise UserError(self.env._('Nhập nội dung trao đổi.'))
                message = self.env['mail.message'].sudo().with_context(_kd_internal=_INTERNAL).create({
                    'model': 'crm.lead', 'res_id': lead.id, 'body': Markup('<p>%s</p>') % escape(self.scope),
                    'message_type': 'comment', 'subtype_id': self.env.ref('mail.mt_note').id,
                    'author_id': self.env.user.partner_id.id})
                after.update(message=message.id, body=self.scope)
            lead.sudo().with_context(_kd_internal=_INTERNAL).write({'kd_head_version': lead.kd_head_version + 1})
            head_event(self.env, self.operation, self.reason, before, after, project=p, lead=lead)
        elif self.operation == 'partner':
            p.check_access('read')
            if not p._tp_head_allowed():
                raise AccessError(self.env._('Đối tác phải được mở từ dự án trong phòng.'))
            self.env.cr.execute(SQL('SELECT id FROM project_project WHERE id=%s FOR UPDATE', p.id))
            p.invalidate_recordset()
            if (not p._tp_head_allowed() or p.company_id != self.company_id
                    or p.tp_department_id != self.department_id):
                raise AccessError(self.env._('Phạm vi dự án đã đổi. Mở lại thao tác.'))
            if not (self.name or '').strip():
                raise ValidationError(self.env._('Cần tên đối tác.'))
            partner = self.partner_id
            if partner:
                partner.check_access('read')
                relations = self.env['tp.project.participation'].sudo().with_context(active_test=False).search([('partner_id', '=', partner.id)])
                projects = self.env['project.project'].sudo().with_context(active_test=False).search([
                    '|', ('partner_id', '=', partner.id), ('kd_investor_id', '=', partner.id)])
                contracts = self.env['tp.contract'].sudo().with_context(active_test=False).search([('partner_id', '=', partner.id)])
                leads = self.env['crm.lead'].sudo().with_context(active_test=False).search([('partner_id', '=', partner.id)])
                external_project = any(not project._tp_head_allowed() for project in (
                    projects | relations.project_id | contracts.project_id).with_env(self.env))
                external_lead = any(not record._kd_head() for record in leads.with_env(self.env))
                if partner not in p.partner_id | p.kd_investor_id | p.kd_participation_ids.partner_id or any(
                    (external_project, external_lead, partner.company_id and partner.company_id != self.company_id)):
                    raise AccessError(self.env._('Đối tác dùng ngoài phòng cần chủ danh mục xử lý.'))
                before = {k: partner[k] for k in ('name', 'email', 'phone')}
                partner.sudo().write({'name': self.name, 'email': self.email, 'phone': self.phone})
            else:
                before = None
                partner = self.env['res.partner'].sudo().create({'name': self.name,
                    'email': self.email, 'phone': self.phone, 'company_id': self.company_id.id})
            head_event(self.env, 'partner', self.reason, before,
                {'partner': partner.id, 'name': partner.name, 'email': partner.email, 'phone': partner.phone}, project=p)
            super().write({'result_partner_id': partner.id})
        super().write({'result_payload_hash': payload_hash})
        return {'type': 'ir.actions.act_window_close'}


class Project(models.Model):
    _inherit = 'project.project'

    @api.model
    def get_kd_ui_permissions(self):
        self.check_access('read')
        return {'head_create': bool(self.env['tp.kd.department.role']._roles())}

    @api.model
    def action_kd_head_new_project(self):
        roles = self.env['tp.kd.department.role']._roles()
        if not roles:
            raise AccessError(self.env._('Cần vai trò HEAD để tạo dự án.'))
        return {'type': 'ir.actions.act_window', 'res_model': 'tp.kd.head.command',
            'views': [(self.env.ref('tp_kd_workspace.head_command_form').id, 'form')], 'target': 'new',
            'context': {'default_operation': 'project_create', 'default_company_id': roles[0].company_id.id,
                'default_department_id': roles[0].department_id.id}, 'name': 'Tạo dự án KH-KD'}

    def _kd_head_dialog(self, operation):
        self.ensure_one()
        wizard = self.env['tp.kd.head.command'].create({'operation': operation,
            'project_id': self.id, 'reason': ' '})
        return {'type': 'ir.actions.act_window', 'res_model': wizard._name, 'res_id': wizard.id,
            'views': [(self.env.ref('tp_kd_workspace.head_command_form').id, 'form')], 'target': 'new'}

    def action_kd_head_assign(self):
        return self._kd_head_dialog('project_assign')

    def action_kd_head_partner(self):
        return self._kd_head_dialog('partner')


class Opportunity(models.Model):
    _inherit = 'crm.lead'
    kd_head_version = fields.Integer(default=1, readonly=True, copy=False)
    kd_intervention_reason = fields.Char(store=False, string='Lý do can thiệp nháp')
    kd_is_head = fields.Boolean(compute='_compute_head')
    kd_head_document_ids = fields.Many2many('ir.attachment', compute='_compute_head_content', string='Tài liệu')
    kd_head_message_ids = fields.Many2many('mail.message', compute='_compute_head_content', string='Trao đổi')

    def _head_documents(self):
        if not self or not self._kd_head():
            return self.env['ir.attachment']
        self.check_access('read')
        messages = self.env['mail.message'].search([('model', '=', 'crm.lead'), ('res_id', '=', self.id)])
        return self.env['ir.attachment'].search(Domain('kd_head_archived', '=', False) & (
            (Domain('res_model', '=', 'crm.lead') & Domain('res_id', '=', self.id))
            | (Domain('res_model', '=', 'mail.message') & Domain('res_id', 'in', messages.ids))))

    @api.depends('kd_head_version')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_head_content(self):
        for lead in self:
            lead.kd_head_document_ids = lead._head_documents()
            lead.kd_head_message_ids = self.env['mail.message'].search([
                ('model', '=', 'crm.lead'), ('res_id', '=', lead.id), ('message_type', '=', 'comment'),
            ]) if lead.id and lead._kd_head() else self.env['mail.message']

    def _kd_head(self):
        self.ensure_one()
        return (self.env['tp.kd.department.role']._is_head(project=self.tp_project_id)
            if self.tp_project_id else self.company_id in self.env.companies
            and self.company_id == self.team_id.company_id
            and self.team_id.id in self.env['tp.kd.department.role']._team_ids()
            and self.env['tp.kd.department.role']._is_head(
                company=self.company_id, department=self.team_id.kd_department_id))

    @api.depends_context('uid')
    def _compute_head(self):
        for rec in self:
            rec.kd_is_head = rec._kd_head()

    @api.model
    def _kd_project_scope(self):
        return (super()._kd_project_scope() | self.env['project.project'].browse(
            self.env['tp.kd.department.role']._project_ids()))

    @api.model
    def _kd_preproject_teams(self, capability='prepare'):
        return super()._kd_preproject_teams(capability) | self.env['crm.team'].browse(
            self.env['tp.kd.department.role']._team_ids())

    def _search_kd_accessible(self, operator, value):
        base = super()._search_kd_accessible(operator, value)
        if base is NotImplemented:
            return base
        result = base | (Domain('tp_project_id', '=', False) & self._kd_head_preproject_domain())
        if self.env['tp.kd.department.role']._roles():
            teams = self._kd_preproject_teams()
            valid_teams = Domain.OR([Domain('team_id', '=', t.id) & Domain('company_id', '=', t.company_id.id)
                for t in teams])
            result &= Domain('tp_project_id', '!=', False) | valid_teams
        return result

    def _compute_kd_accessible(self):
        super()._compute_kd_accessible()
        for rec in self:
            rec.kd_accessible = rec.kd_accessible or rec._kd_head()
            if self.env['tp.kd.department.role']._roles() and not rec.tp_project_id and rec.company_id != rec.team_id.company_id:
                rec.kd_accessible = False

    def _kd_allowed(self, capability='prepare'):
        return self._kd_head() or super()._kd_allowed(capability)

    def _compute_kd_can_prepare(self):
        super()._compute_kd_can_prepare()
        for rec in self:
            if rec._kd_head():
                rec.kd_can_edit = rec.kd_bid_state != 'submitted'
                rec.kd_can_prepare = rec.kd_bid_state == 'identified'
                rec.kd_can_submit = rec.kd_bid_state == 'preparation'
                rec.kd_can_read_money = True
                rec.kd_can_edit_money = rec.kd_can_edit

    def _compute_kd_money_display(self):
        for rec in self:
            rec.kd_money_display = (formatLang(self.env, rec.expected_revenue,
                currency_obj=rec.company_currency) if rec._kd_head() or (
                    rec.tp_project_id and rec.tp_project_id.id in rec._kd_financial_projects())
                else self.env._('Không có quyền xem tiền'))

    @api.model
    def _kd_financial_domain(self):
        return Domain('tp_project_id', 'in', self._kd_financial_projects()) | (
            Domain('tp_project_id', '=', False)
            & self._kd_head_preproject_domain())

    @api.model
    def _kd_head_preproject_domain(self):
        teams = self.env['crm.team'].sudo().browse(self.env['tp.kd.department.role']._team_ids())
        return Domain.OR([Domain('team_id', '=', team.id) & Domain('company_id', '=', team.company_id.id)
            for team in teams])

    def _kd_require_money(self, edit=False):
        remaining = self.filtered(lambda rec: not rec._kd_head())
        if remaining:
            super(Opportunity, remaining)._kd_require_money(edit)

    def _has_field_access(self, field, operation):
        if field.name in {'expected_revenue', 'prorated_revenue', 'recurring_revenue',
            'recurring_revenue_monthly', 'recurring_revenue_monthly_prorated', 'recurring_revenue_prorated'} and self.env['tp.kd.department.role']._roles():
            return True
        return super()._has_field_access(field, operation)

    @api.model
    def get_kd_ui_permissions(self):
        result = super().get_kd_ui_permissions()
        result['create'] = result['create'] or bool(self.env['tp.kd.department.role']._roles())
        return result

    def _head_snapshot(self):
        self.ensure_one()
        return {key: (self[key].id if self._fields[key].type == 'many2one' else self[key])
            for key in ('name', 'user_id', 'team_id', 'tp_project_id', 'kd_scope', 'kd_source',
                'kd_checklist', 'kd_deadline', 'kd_route', 'kd_receipt', 'expected_revenue',
                'kd_bid_state', 'kd_head_version')}

    @api.model_create_multi
    def create(self, vals_list):
        cleaned = []
        if not self.env.su:
            for supplied in vals_list:
                vals = {**self.default_get(['company_id', 'tp_project_id', 'team_id', 'user_id']), **supplied}
                p = self.env['project.project'].browse(vals.get('tp_project_id'))
                team = self.env['crm.team'].browse(vals.get('team_id'))
                company = p.company_id if p else self.env['res.company'].browse(vals.get('company_id') or self.env.company.id)
                department = p.tp_department_id if p else team.kd_department_id
                if self.env['tp.kd.department.role']._is_head(project=p, company=company, department=department):
                    owner = self.env['res.users'].sudo().browse(vals.get('user_id', self.env.uid)).exists()
                    eligible = bool(owner and (p._tp_scope_allowed(user=owner) if p else
                        owner in head_candidates(self.env, company, department)
                        and team in self.with_user(owner)._kd_preproject_teams()))
                    if not owner or not owner.active or not owner._is_internal() or company not in owner.company_ids or not eligible:
                        raise AccessError(self.env._('Người phụ trách phải thuộc phòng được giao.'))
                if supplied.get('kd_head_version', 1) != 1 or supplied.get('kd_intervention_reason'):
                    raise AccessError(self.env._('Phiên bản do máy chủ quản lý.'))
        for supplied in vals_list:
            cleaned.append({k: v for k, v in supplied.items() if k not in {'kd_head_version', 'kd_intervention_reason'}})
        model = self.with_context(mail_auto_subscribe_no_notify=True) if self.env['tp.kd.department.role']._roles() else self
        return super(Opportunity, model).create(cleaned).with_env(self.env)

    def write(self, vals):
        if self.env.su:
            return super().write(vals)
        heads = self.filtered(lambda rec: rec._kd_head())
        if not heads:
            if set(vals) & {'kd_head_version', 'kd_intervention_reason'}:
                raise AccessError(self.env._('Không có quyền can thiệp HEAD.'))
            return super().write(vals)
        if len(heads) != len(self) or len(self) != 1:
            raise AccessError(self.env._('Can thiệp từng hồ sơ trong đúng phòng.'))
        self._kd_lock_bid()
        values = dict(vals)
        version = values.pop('kd_head_version', None)
        reason = (values.pop('kd_intervention_reason', None) or '').strip()
        internal = self.env.context.get('_kd_internal') is _INTERNAL
        if not internal and (version != self.kd_head_version or not reason):
            raise UserError(self.env._('Cần lý do và phiên bản đang mở. Tải lại nếu hồ sơ đã thay đổi.'))
        before = self._head_snapshot()
        result = super().write(values)
        # This internal write cannot be requested using a JSON/context flag.
        super(Opportunity, self.sudo()).write({'kd_head_version': before['kd_head_version'] + 1})
        head_event(self.env, 'lead_update', reason or 'Thao tác workflow hồ sơ dự án',
            json.loads(json.dumps(before, default=str)), json.loads(json.dumps(self._head_snapshot(), default=str)),
            project=self.tp_project_id, lead=self)
        return result

    def action_kd_head_assign(self):
        self.ensure_one()
        wizard = self.env['tp.kd.head.command'].create({'operation': 'lead_assign',
            'lead_id': self.id, 'reason': ' '})
        return {'type': 'ir.actions.act_window', 'res_model': wizard._name, 'res_id': wizard.id,
            'views': [(self.env.ref('tp_kd_workspace.head_command_form').id, 'form')], 'target': 'new'}

    def _head_content_dialog(self, operation):
        self.ensure_one()
        if not self._kd_head() or self.kd_bid_state == 'submitted':
            raise AccessError(self.env._('Tài liệu và trao đổi chỉ thay qua nháp HEAD đúng phòng.'))
        wizard = self.env['tp.kd.head.command'].create({'operation': operation,
            'lead_id': self.id, 'reason': ' '})
        return {'type': 'ir.actions.act_window', 'res_model': wizard._name, 'res_id': wizard.id,
            'views': [(self.env.ref('tp_kd_workspace.head_command_form').id, 'form')], 'target': 'new'}

    def action_kd_head_document_add(self):
        return self._head_content_dialog('lead_document_add')

    def action_kd_head_document_remove(self):
        return self._head_content_dialog('lead_document_remove')

    def action_kd_head_comment(self):
        return self._head_content_dialog('lead_comment')


class OpportunityMoneyEdit(models.TransientModel):
    _inherit = 'tp.kd.opportunity.money'
    reason = fields.Char(string='Lý do cập nhật')
    expected_head_version = fields.Integer(readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        values = []
        for vals in vals_list:
            if 'expected_head_version' in vals:
                raise AccessError(self.env._('Phiên bản do máy chủ xác định.'))
            lead = self.env['crm.lead'].browse(vals.get('lead_id'))
            lead.check_access('read')
            values.append(dict(vals, expected_head_version=lead.kd_head_version))
        return super().create(values)

    def write(self, vals):
        if set(vals) & {'expected_head_version', 'lead_id'}:
            raise AccessError(self.env._('Không đổi đích hoặc phiên bản.'))
        return super().write(vals)

    def action_confirm(self):
        self.ensure_one()
        self.check_access('read')
        lead = self.lead_id
        if not lead._kd_head():
            return super().action_confirm()
        lead.write({'expected_revenue': self.amount, 'kd_head_version': self.expected_head_version,
            'kd_intervention_reason': self.reason})
        return {'type': 'ir.actions.act_window_close'}


class BidPackage(models.Model):
    _inherit = 'tp.bid.package'
    version = fields.Integer(default=1, readonly=True, copy=False)
    intervention_reason = fields.Char(store=False, string='Lý do cập nhật')
    can_head_intervene = fields.Boolean(compute='_compute_head_intervention')

    @api.depends('project_id')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_head_intervention(self):
        for package in self:
            package.can_head_intervene = bool(package.project_id and package.project_id._tp_head_allowed())

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            defaults = self.default_get(['project_id', 'owner_id', 'version'])
            for supplied in vals_list:
                vals = {**defaults, **supplied}
                if vals.get('version', 1) != 1:
                    raise AccessError(self.env._('Phiên bản ban đầu do máy chủ quản lý.'))
                project = self.env['project.project'].browse(vals.get('project_id'))
                if project and project._tp_head_allowed():
                    owner = self.env['res.users'].sudo().browse(vals.get('owner_id')).exists()
                    if (not owner or not owner._is_internal() or not project._tp_scope_allowed(user=owner)):
                        raise AccessError(self.env._('Người phụ trách gói phải còn quyền trong dự án được giao.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.su or self.env.context.get('_kd_internal') is _INTERNAL:
            return super().write(vals)
        heads = self.filtered(lambda r: r.project_id._tp_head_allowed())
        if not heads:
            if set(vals) & {'version', 'intervention_reason'}:
                raise AccessError(self.env._('Phiên bản cập nhật gói do máy chủ quản lý.'))
            self.env.flush_all()
            for record in self.sorted('id'):
                self.env.cr.execute(SQL('SELECT id FROM tp_bid_package WHERE id=%s FOR UPDATE', record.id))
                record.invalidate_recordset()
                super(BidPackage, record).write(vals)
                super(BidPackage, record.sudo()).write({'version': record.version + 1})
            return True
        self.ensure_one()
        values = dict(vals)
        version = values.pop('version', None)
        reason = (values.pop('intervention_reason', '') or '').strip()
        self.env.cr.execute(SQL('SELECT id FROM tp_bid_package WHERE id=%s FOR UPDATE', self.id))
        self.invalidate_recordset()
        if not self.project_id._tp_head_allowed():
            raise AccessError(self.env._('Quyền HEAD đã thay đổi. Tải lại trước khi cập nhật.'))
        if version != self.version or not reason:
            raise UserError(self.env._('Cần phiên bản đang mở và lý do cập nhật gói thầu.'))
        snapshot_fields = ('code', 'name', 'scope', 'deadline', 'inviter_id', 'owner_id', 'project_id', 'stage', 'outcome', 'version')
        before = {k: self[k].id if self._fields[k].type == 'many2one' else str(self[k]) for k in snapshot_fields}
        result = super().write(values)
        super(BidPackage, self.sudo()).write({'version': self.version + 1})
        after = {k: self[k].id if self._fields[k].type == 'many2one' else str(self[k]) for k in snapshot_fields}
        head_event(self.env, 'bid_update', reason, {'package': self.id, **before},
            {'package': self.id, **after}, project=self.project_id)
        return result


def require_content_command(env, ids):
    if env.context.get('_kd_internal') is _INTERNAL or not ids:
        return
    leads = env['crm.lead'].sudo(False).browse(ids)
    if any(lead._kd_head() for lead in leads):
        raise AccessError(env._('HEAD dùng Thêm tài liệu, Lưu trữ tài liệu hoặc Ghi trao đổi để lưu lý do và phiên bản.'))


class Attachment(models.Model):
    _inherit = 'ir.attachment'
    kd_head_archived = fields.Boolean(default=False, readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(['res_model', 'res_id'])
        for supplied in vals_list:
            vals = {**defaults, **supplied}
            require_content_command(self.env, attachment_parent_ids(self.env, vals.get('res_model'), vals.get('res_id')))
            if vals.get('kd_head_archived') and self.env.context.get('_kd_internal') is not _INTERNAL:
                raise AccessError(self.env._('Lưu trữ tài liệu qua thao tác có lịch sử.'))
        return super().create(vals_list)

    def write(self, vals):
        for attachment in self.sudo():
            require_content_command(self.env, attachment_parent_ids(self.env, attachment.res_model, attachment.res_id))
            require_content_command(self.env, attachment_parent_ids(self.env,
                vals.get('res_model', attachment.res_model), vals.get('res_id', attachment.res_id)))
        if 'kd_head_archived' in vals and self.env.context.get('_kd_internal') is not _INTERNAL:
            raise AccessError(self.env._('Lưu trữ tài liệu qua thao tác có lịch sử.'))
        return super().write(vals)

    def unlink(self):
        for attachment in self.sudo():
            require_content_command(self.env, attachment_parent_ids(self.env, attachment.res_model, attachment.res_id))
        return super().unlink()

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, *, active_test=True, bypass_access=False):
        if not self.env.su and self.env.context.get('active_test', True) and active_test:
            domain = Domain(domain) & Domain('kd_head_archived', '=', False)
        return super()._search(domain, offset, limit, order, active_test=active_test, bypass_access=bypass_access)


class Message(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(['model', 'res_id'])
        for supplied in vals_list:
            vals = {**defaults, **supplied}
            if vals.get('model') == 'crm.lead':
                require_content_command(self.env, [vals.get('res_id')] if vals.get('res_id') else [])
        return super().create(vals_list)

    def write(self, vals):
        for message in self.sudo():
            if message.model == 'crm.lead':
                require_content_command(self.env, [message.res_id])
            if vals.get('model', message.model) == 'crm.lead':
                require_content_command(self.env, [vals.get('res_id', message.res_id)])
        return super().write(vals)

    def unlink(self):
        for message in self.sudo().filtered(lambda m: m.model == 'crm.lead'):
            require_content_command(self.env, [message.res_id])
        return super().unlink()
