"""Scoped CRM uses project assignments or an explicitly assigned native team/owner."""
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.fields import Domain
from odoo.tools import SQL
from odoo.tools.misc import formatLang

from .workspace import _INTERNAL

EDITABLE = frozenset({'name', 'type', 'partner_id', 'company_id', 'tp_project_id', 'user_id', 'team_id',
    'kd_source', 'kd_scope', 'kd_checklist', 'kd_deadline', 'kd_route', 'kd_receipt', 'kd_credential_ids',
    'expected_revenue', 'recurring_revenue', 'recurring_plan', 'kd_package_id'})


class OpportunityMoney(fields.Monetary):
    # The descriptor also checks cached/related reads, after a live revocation.
    def __get__(self, record, owner=None):
        if record is not None and record and not record.env.su and record._kd_scoped():
            record._kd_require_money()
        return super().__get__(record, owner)

    def to_sql(self, table):
        model = table._model
        if not model.env.su and model._kd_scoped():
            ids = model._kd_financial_projects()
            if not ids and not model.env['tp.kd.department.role']._team_ids():
                raise AccessError(model.env._("Bạn không có quyền xem hoặc truy vấn tiền hồ sơ dự án."))
            # Applies to domain, NOT, order, aggregate, related joins and export fetches alike.
            if table._query is None:
                raise AccessError(model.env._("Truy vấn tiền cần phạm vi được kiểm quyền."))
            teams = model.env['crm.team'].sudo().browse(model.env['tp.kd.department.role']._team_ids())
            preproject = SQL(' OR ').join(SQL('(%s=%s AND %s=%s)',
                SQL.identifier(table._alias, 'team_id'), team.id,
                SQL.identifier(table._alias, 'company_id'), team.company_id.id) for team in teams) if teams else SQL('FALSE')
            table._query.add_where(SQL('(%s IN %s OR (%s IS NULL AND (%s)))',
                SQL.identifier(table._alias, 'tp_project_id'), tuple(ids) or (0,),
                SQL.identifier(table._alias, 'tp_project_id'), preproject))
        return super().to_sql(table)


class Team(models.Model):
    _inherit = 'crm.team'
    kd_department_id = fields.Many2one('hr.department', check_company=True, string='Đơn vị KH-KD')

    def write(self, vals):
        result = super().write(vals)
        if set(vals) & {'member_ids', 'crm_team_member_ids', 'kd_department_id', 'company_id', 'active'}:
            self.env['crm.lead']._kd_invalidate_security()
        return result


class Opportunity(models.Model):
    _inherit = 'crm.lead'

    expected_revenue = OpportunityMoney(prefetch=False)
    prorated_revenue = OpportunityMoney(prefetch=False)
    recurring_revenue = OpportunityMoney(prefetch=False)
    recurring_revenue_monthly = OpportunityMoney(prefetch=False)
    recurring_revenue_monthly_prorated = OpportunityMoney(prefetch=False)
    recurring_revenue_prorated = OpportunityMoney(prefetch=False)
    kd_accessible = fields.Boolean(compute='_compute_kd_accessible', search='_search_kd_accessible')
    kd_can_submit = fields.Boolean(compute='_compute_kd_can_prepare')
    kd_can_edit = fields.Boolean(compute='_compute_kd_can_prepare')
    kd_can_read_money = fields.Boolean(compute='_compute_kd_can_prepare')
    kd_can_edit_money = fields.Boolean(compute='_compute_kd_can_prepare')
    kd_money_display = fields.Char(compute='_compute_kd_money_display', string='Giá trị hồ sơ dự án dự kiến')

    @api.depends_context('uid')
    @api.depends('tp_project_id', 'expected_revenue')
    def _compute_kd_money_display(self):
        for lead in self:
            lead.kd_money_display = (formatLang(self.env, lead.expected_revenue, currency_obj=lead.company_currency)
                if lead.tp_project_id and lead.tp_project_id.id in lead._kd_financial_projects()
                else self.env._('Không có quyền xem tiền'))

    @api.model
    def _kd_scoped(self):
        return self.env.user.has_group('tp_kd_workspace.group_scoped_staff')

    @api.model
    def _kd_invalidate_security(self):
        self.invalidate_model(['kd_accessible', 'kd_can_prepare', 'kd_can_submit', 'kd_can_edit',
                              'kd_can_read_money', 'kd_can_edit_money', 'kd_money_display'])
        self.env['ir.attachment'].invalidate_model(['kd_crm_accessible'])
        self.env['mail.message'].invalidate_model(['kd_crm_accessible'])
        self.env.transaction.invalidate_access_cache()

    def _read_format(self, fnames, load='_classic_read'):
        # Capabilities/date expiry are evaluated again on each native/RPC read.
        self.invalidate_recordset([n for n in fnames if n.startswith('kd_can_') or n == 'kd_money_display'])
        return super()._read_format(fnames, load=load)

    @api.model
    def _kd_project_scope(self):
        # Security metadata only; no business record is read with sudo.
        assignments = self.env['tp.project.assignment'].sudo().search([
            ('user_id', '=', self.env.uid), ('active', '=', True),
            ('project_id.company_id', 'in', self.env.companies.ids)])
        return assignments.project_id.with_env(self.env).filtered(lambda p: p.has_access('read'))

    @api.model
    def _kd_preproject_teams(self, capability='prepare'):
        projects = self._kd_project_scope()
        departments = projects.filtered(lambda p: self.env['tp.kd.grant']._has(p, 'opportunity', capability)).tp_department_id
        return self.env['crm.team'].search([('company_id', 'in', self.env.companies.ids),
            ('kd_department_id', 'in', departments.ids), ('member_ids', 'in', self.env.uid), ('active', '=', True)])

    def _search_kd_accessible(self, operator, value):
        if operator != 'in' or set(value) != {True}:
            return NotImplemented
        projects = self._kd_project_scope()
        teams = self._kd_preproject_teams()
        return (Domain('tp_project_id', 'in', projects.ids)
                | (Domain('tp_project_id', '=', False) & Domain('user_id', '=', self.env.uid)
                   & Domain('team_id', 'in', teams.ids))) & Domain('company_id', 'in', self.env.companies.ids)

    @api.depends_context('uid')
    @api.depends('tp_project_id', 'company_id', 'team_id', 'user_id')
    def _compute_kd_accessible(self):
        projects, teams = self._kd_project_scope().ids, self._kd_preproject_teams().ids
        for lead in self:
            lead.kd_accessible = lead.company_id in self.env.companies and (
                lead.tp_project_id.id in projects if lead.tp_project_id else
                lead.user_id == self.env.user and lead.team_id.id in teams)

    def _kd_allowed(self, capability='prepare'):
        self.ensure_one()
        if self.company_id not in self.env.companies or self.user_id != self.env.user:
            return False
        if self.tp_project_id:
            return self.env['tp.kd.grant']._has(self.tp_project_id, 'opportunity', capability)
        return bool(self.team_id and self.team_id in self._kd_preproject_teams(capability))

    def _kd_require(self, capability='prepare'):
        self.check_access('write')
        if not self.env.su and any(not r._kd_allowed(capability) for r in self):
            raise AccessError(self.env._('Cần quyền riêng và phải là người phụ trách hồ sơ dự án trong phạm vi được giao.'))

    @api.depends_context('uid')
    @api.depends('tp_project_id', 'team_id', 'user_id', 'company_id', 'kd_bid_state')
    def _compute_kd_can_prepare(self):
        for lead in self:
            own = bool(lead.user_id == self.env.user)
            lead.kd_can_edit = own and lead.kd_bid_state != 'submitted' and lead._kd_allowed('prepare')
            lead.kd_can_prepare = lead.kd_can_edit and lead.kd_bid_state == 'identified'
            lead.kd_can_submit = own and lead.kd_bid_state == 'preparation' and lead._kd_allowed('submit')
            lead.kd_can_read_money = bool(lead.tp_project_id and lead.tp_project_id.id in lead._kd_financial_projects())
            lead.kd_can_edit_money = lead.kd_can_edit and lead.tp_project_id.id in lead._kd_financial_projects(edit=True)

    @api.model
    def get_kd_ui_permissions(self):
        self.check_access('read')
        return {'create': any(self.env['tp.kd.grant']._has(p, 'opportunity', 'prepare') for p in self._kd_project_scope())}

    @api.model
    def _kd_financial_projects(self, edit=False):
        grant = self.env['tp.project.grant']
        return self._kd_project_scope().filtered(lambda p: grant._tp_has_capability(p, 'financial_read')
            and (not edit or grant._tp_has_capability(p, 'financial_draft_edit', p.tp_department_id))).ids

    def _kd_require_money(self, edit=False):
        allowed = self._kd_financial_projects(edit)
        if any(not r.tp_project_id or r.tp_project_id.id not in allowed for r in self):
            raise AccessError(self.env._('Bạn không có quyền tiền hồ sơ dự án trong phạm vi này.'))

    def _has_field_access(self, field, operation):
        if isinstance(field, OpportunityMoney) and not self.env.su and self._kd_scoped() and not self._kd_financial_projects(operation == 'write'):
            return False
        return super()._has_field_access(field, operation)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.su or not self._kd_scoped():
            return super().create(vals_list)
        names = ['company_id', 'tp_project_id', 'user_id', 'team_id', 'kd_bid_state', 'active']
        defaults = self.default_get(names)
        result = []
        for values in vals_list:
            vals = {**defaults, **values}
            if set(values) - EDITABLE - {'kd_bid_state', 'active'} or any(
                k.startswith('default_') and k[8:] not in EDITABLE | {'kd_bid_state', 'active'} for k in self.env.context):
                raise AccessError(self.env._('Chỉ tạo các trường hồ sơ được phép; không truyền mặc định quản trị.'))
            vals.setdefault('company_id', self.env.company.id)
            vals.setdefault('user_id', self.env.uid)
            project = self.env['project.project'].browse(vals.get('tp_project_id'))
            team = self.env['crm.team'].sudo().browse(vals.get('team_id'))
            head = self.env['tp.kd.department.role']._is_head(project=project) if project else (
                team.id in self.env['tp.kd.department.role']._team_ids() and team.company_id.id == vals.get('company_id'))
            if (vals.get('user_id') != self.env.uid and not head) or vals.get('company_id') not in self.env.companies.ids:
                raise AccessError(self.env._('Không tạo hồ sơ dự án thay owner hoặc ngoài công ty.'))
            if project:
                if project.company_id.id != vals['company_id'] or not self.env['tp.kd.grant']._has(project, 'opportunity', 'prepare'):
                    raise AccessError(self.env._('Dự án ngoài quyền lập hồ sơ dự án.'))
            elif vals.get('team_id') not in self._kd_preproject_teams().ids:
                raise AccessError(self.env._('Hồ sơ dự án trước dự án cần nhóm KH-KD và owner được giao.'))
            if any(k.startswith('default_') and k[8:] in self._fields and isinstance(self._fields[k[8:]], OpportunityMoney)
                   for k in self.env.context):
                raise AccessError(self.env._('Không truyền mặc định tiền qua context.'))
            money = {k for k in vals if isinstance(self._fields.get(k), OpportunityMoney)}
            if money and not head and (not project or project.id not in self._kd_financial_projects(edit=True)):
                raise AccessError(self.env._('Chưa có quyền sửa tiền nháp.'))
            if vals.get('kd_bid_state', 'identified') != 'identified' or vals.get('active', True) is False:
                raise UserError(self.env._('Tạo hồ sơ dự án đang tìm hiểu, không truyền trạng thái/ẩn hồ sơ.'))
            result.append(vals)
        return super().create(result)

    def write(self, vals):
        if not self:
            return super().write(vals)
        if not self.env.su and self._kd_scoped():
            self.check_access('write')
            for lead in self.sorted('id'):
                lead._kd_lock_bid()
            internal = self.env.context.get('_kd_internal') is _INTERNAL
            self._kd_require('submit' if internal and vals.get('kd_bid_state') == 'submitted' else 'prepare')
            if not internal and set(vals) - EDITABLE - {'kd_bid_state', 'active'}:
                raise AccessError(self.env._('Trường này không thuộc quyền chuẩn bị hồ sơ.'))
            if any(r.kd_bid_state == 'submitted' for r in self):
                raise UserError(self.env._('Hồ sơ đã khai báo nộp được giữ nguyên căn cứ và phạm vi.'))
            for name in ('tp_project_id', 'company_id', 'user_id', 'team_id'):
                if name in vals and any((r[name].id or False) != (vals[name] or False) for r in self):
                    raise AccessError(self.env._('Chuyển owner/nhóm/công ty/dự án cần thao tác phân công riêng.'))
            if 'active' in vals:
                raise AccessError(self.env._('Không ẩn hoặc lưu trữ hồ sơ qua quyền chuẩn bị.'))
            if any(isinstance(self._fields.get(k), OpportunityMoney) for k in vals):
                self._kd_require_money(edit=True)
        return super().write(vals)

    def _kd_lock_bid(self):
        self.ensure_one()
        self.env.flush_all()
        self.env.cr.execute(SQL('SELECT id FROM crm_lead WHERE id=%s FOR UPDATE', self.id))
        self.invalidate_recordset()

    def action_kd_edit_money(self):
        self.ensure_one()
        self._kd_require()
        self._kd_require_money(edit=True)
        if self.kd_bid_state == 'submitted':
            raise UserError(self.env._('Hồ sơ đã nộp không được sửa tiền.'))
        wizard = self.env['tp.kd.opportunity.money'].create({'lead_id': self.id, 'amount': self.expected_revenue})
        return {'type': 'ir.actions.act_window', 'name': 'Giá trị hồ sơ dự án dự kiến', 'res_model': wizard._name,
                'res_id': wizard.id, 'views': [(False, 'form')], 'target': 'new'}

    def action_kd_prepare(self):
        self._kd_require()
        self._kd_lock_bid()
        return super().action_kd_prepare()

    def action_kd_record_submission(self):
        self._kd_require('submit')
        self._kd_lock_bid()
        return super().action_kd_record_submission()

    def copy(self, default=None):
        if not self.env.su and self._kd_scoped():
            raise UserError(self.env._('Tạo hồ sơ dự án mới, không sao chép phạm vi/căn cứ/tiền.'))
        return super().copy(default)

    def unlink(self):
        if not self.env.su and self._kd_scoped():
            raise AccessError(self.env._('Không xóa hồ sơ qua quyền chuẩn bị.'))
        return super().unlink()

    def _get_rainbowman_message(self):
        if not self.env.su and self._kd_scoped():
            return False
        return super()._get_rainbowman_message()

    def get_rainbowman_message(self):
        if not self.env.su and self._kd_scoped():
            return False
        return super().get_rainbowman_message()


def crm_file_domain(model):
    leads = model.env['crm.lead']
    if not leads.has_access('read'):
        return Domain.FALSE
    return Domain('res_id', 'in', leads._search(leads._kd_financial_domain()))


class OpportunityMoneyEdit(models.TransientModel):
    _name = 'tp.kd.opportunity.money'
    _description = 'Sửa giá trị hồ sơ dự án dự kiến theo quyền hiện hành'
    lead_id = fields.Many2one('crm.lead', required=True, readonly=True, ondelete='cascade')
    currency_id = fields.Many2one(related='lead_id.company_currency')
    amount = fields.Monetary(required=True, string='Giá trị dự kiến')

    def action_confirm(self):
        self.ensure_one()
        self.check_access('read')
        self.lead_id._kd_lock_bid()
        self.lead_id.write({'expected_revenue': self.amount})
        return {'type': 'ir.actions.act_window_close'}


class ProjectGrant(models.Model):
    _inherit = 'tp.project.grant'

    def _invalidate_grant_access(self):
        super()._invalidate_grant_access()
        self.env['crm.lead']._kd_invalidate_security()


class Assignment(models.Model):
    _inherit = 'tp.project.assignment'

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        self.env['crm.lead']._kd_invalidate_security()
        return result

    def write(self, vals):
        result = super().write(vals)
        self.env['crm.lead']._kd_invalidate_security()
        return result

    def unlink(self):
        result = super().unlink()
        self.env['crm.lead']._kd_invalidate_security()
        return result


class Attachment(models.Model):
    _inherit = 'ir.attachment'
    kd_crm_accessible = fields.Boolean(compute='_compute_kd_crm_accessible', search='_search_kd_crm_accessible')

    def _kd_check_crm_mutation(self):
        if not self.env.su and self.env.user.has_group('tp_kd_workspace.group_scoped_staff'):
            ids = self.sudo().filtered(lambda a: a.res_model == 'crm.lead' and a.res_id).mapped('res_id')
            leads = self.env['crm.lead'].browse(ids)
            leads._kd_require()
            for lead in leads.sorted('id'):
                lead._kd_lock_bid()
            leads._kd_require()
            leads._kd_require_money()
            if any(r.kd_bid_state == 'submitted' for r in leads):
                raise UserError(self.env._('Không thay file căn cứ của hồ sơ đã nộp.'))

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and self.env.user.has_group('tp_kd_workspace.group_scoped_staff'):
            defaults = self.default_get(['res_model', 'res_id'])
            for values in vals_list:
                vals = {**defaults, **values}
                if vals.get('res_model') == 'crm.lead' and vals.get('res_id'):
                    lead = self.env['crm.lead'].browse(vals['res_id'])
                    lead._kd_require()
                    lead._kd_lock_bid()
                    lead._kd_require()
                    lead._kd_require_money()
                    if lead.kd_bid_state == 'submitted' or vals.get('public') or vals.get('access_token'):
                        raise AccessError(self.env._('Không tạo file công khai hoặc sửa căn cứ sau nộp.'))
        return super().create(vals_list)

    def write(self, vals):
        self._kd_check_crm_mutation()
        if not self.env.su and self.env.user.has_group('tp_kd_workspace.group_scoped_staff'):
            crm = vals.get('res_model') == 'crm.lead' or any(a.res_model == 'crm.lead' for a in self.sudo())
            if crm and set(vals) & {'res_model', 'res_id', 'res_field', 'public', 'access_token'}:
                raise AccessError(self.env._('Không đổi phân loại/liên kết/chia sẻ file qua quyền chuẩn bị.'))
        return super().write(vals)

    def unlink(self):
        self._kd_check_crm_mutation()
        return super().unlink()

    @api.depends_context('uid')
    @api.depends('res_model', 'res_id')
    def _compute_kd_crm_accessible(self):
        leads = self.env['crm.lead']
        allowed = leads.search(leads._kd_financial_domain()).ids if leads.has_access('read') else []
        for attachment in self:
            attachment.kd_crm_accessible = attachment.res_model != 'crm.lead' or attachment.res_id in allowed

    def _search_kd_crm_accessible(self, operator, value):
        if operator != 'in' or set(value) != {True}:
            return NotImplemented
        return Domain('res_model', '!=', 'crm.lead') | crm_file_domain(self)


class Message(models.Model):
    _inherit = 'mail.message'
    kd_crm_accessible = fields.Boolean(compute='_compute_kd_crm_accessible', search='_search_kd_crm_accessible')

    @api.depends_context('uid')
    @api.depends('model', 'res_id')
    def _compute_kd_crm_accessible(self):
        leads = self.env['crm.lead']
        allowed = leads.search(leads._kd_financial_domain()).ids if leads.has_access('read') else []
        for message in self:
            message.kd_crm_accessible = message.model != 'crm.lead' or message.res_id in allowed

    def _search_kd_crm_accessible(self, operator, value):
        if operator != 'in' or set(value) != {True}:
            return NotImplemented
        return Domain('model', '!=', 'crm.lead') | crm_file_domain(self)


class Binary(models.AbstractModel):
    _inherit = 'ir.binary'

    def _find_record(self, xmlid=None, res_model='ir.attachment', res_id=None, access_token=None, field=None):
        if not self.env.su and self.env.user.has_group('tp_kd_workspace.group_scoped_staff'):
            record = self.env.ref(xmlid, False) if xmlid else (
                self.env[res_model].browse(res_id).exists() if res_id is not None and res_model in self.env else None)
            if record is not None and record and record._name == 'ir.attachment':
                attachment = record.sudo()
                if attachment.res_model == 'crm.lead':
                    # A shared/public token must not bypass a scoped actor's current parent rights.
                    record.check_access('read')
        return super()._find_record(xmlid, res_model, res_id, access_token, field)
