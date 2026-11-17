"""Equipment authority follows all holders and sources.

Company-common stock is never another department: a live delegate only sees the free machines
(in stock, no holder, fit to hand over) to pick one for another department. The handover itself
is the audited adapter in equipment_handover.py; files, chatter and edits of stock stay baseline.
"""
from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.fields import Domain

from odoo.addons.tp_equipment.models.common import GENERIC_DENIED, TP_EQUIPMENT_MODELS
from odoo.addons.tp_equipment.models.quick_action import free_domain

_POST = object()
# Set only by equipment_handover.py after its own checks under lock; JSON-RPC cannot forge it.
_HANDOVER = object()
HANDOVER_KEY = '_tp_delegated_handover'

EDITABLE_MODELS = frozenset({
    'maintenance.equipment', 'maintenance.request', 'tp.equipment.software', 'tp.equipment.meter',
})
PROPOSAL_MODELS = frozenset({
    'tp.equipment.proposal', 'tp.equipment.proposal.line', 'tp.equipment.proposal.review',
})
READ_MODELS = EDITABLE_MODELS | PROPOSAL_MODELS | {
    'tp.equipment.move', 'tp.equipment.move.line', 'maintenance.equipment.category',
    'tp.equipment.location', 'maintenance.stage',
}
DELEGATED_LABEL = ('Quản trị được ủy quyền: thiết bị và đề xuất có nguồn ở phòng khác; kho dùng chung chỉ '
                   'xem máy rảnh để gán/đổi cho phòng khác. Nhập nguồn và phòng của bạn giữ quyền như cũ.')
STOCK_DENIED = 'Kho dùng chung chỉ mở để chọn máy gán/đổi cho phòng khác; việc khác cần Quản trị chính.'
EQUIPMENT_SCOPE_FIELDS = frozenset({
    'company_id', 'tp_custody', 'tp_employee_id', 'tp_holder_department_id', 'tp_location_id',
    'tp_vendor_id', 'tp_parent_id', 'tp_child_ids', 'tp_replaces_id', 'employee_id', 'department_id',
    'owner_user_id', 'technician_user_id', 'equipment_assign_to',
})


def _employee_department(employee):
    return employee.with_context(version_id=False)._get_version().department_id


def _held_departments(equipment, seen=None):
    """Resolve current physical custody without the caller's historical-version context."""
    seen = set() if seen is None else seen
    if not equipment or equipment.id in seen:
        return None
    seen.add(equipment.id)
    department = equipment.env['hr.department']
    if equipment.tp_custody in ('employee', 'loan') and equipment.tp_employee_id:
        if equipment.tp_employee_id.company_id != equipment.company_id:
            return None
        department = _employee_department(equipment.tp_employee_id)
    elif equipment.tp_custody == 'department':
        department = equipment.tp_holder_department_id
    # Location, stock, vendor, unknown and unassigned records need a separate mandate.
    if not department or department.company_id != equipment.company_id:
        return None
    for source in equipment.tp_parent_id | equipment.tp_replaces_id:
        other = _held_departments(source, seen)
        if other is None or source.company_id != equipment.company_id:
            return None
        department |= other
    return department


def _equipment_ids(env):
    ids = []
    actor = env.user
    for company in env.companies:
        if not actor._tp_has_admin_delegation(company):
            continue
        own, complete = actor._tp_delegation_scope(company)
        if not complete:
            continue
        # Office equipment is a small register. Read routing metadata only, under sudo.
        records = env['maintenance.equipment'].sudo().with_context(active_test=False, version_id=False).search([
            ('company_id', '=', company.id), ('tp_custody', 'in', ['employee', 'loan', 'department']),
        ])
        for equipment in records:
            departments = _held_departments(equipment)
            if departments and not (departments & own):
                ids.append(equipment.id)
    return ids


def _free_stock_ids(env):
    """Free company-common stock a delegate may pick for another department (read only)."""
    ids = []
    actor = env.user
    for company in env.companies:
        if not actor._tp_has_admin_delegation(company):
            continue
        own, complete = actor._tp_delegation_scope(company)
        if not complete:
            continue
        machines = env['maintenance.equipment'].sudo().with_context(version_id=False).search(
            Domain(free_domain(env)) & Domain('company_id', '=', company.id))
        for machine in machines:
            # A replacement bought for a holder keeps that holder's source.
            if machine.tp_replaces_id:
                departments = _held_departments(machine.tp_replaces_id)
                if not departments or departments & own:
                    continue
            ids.append(machine.id)
    return ids


def free_stock_domain(env, model):
    """Picker rows only; equipment_domain (files, chatter, history, edits) never includes stock."""
    if model not in ('maintenance.equipment', 'maintenance.equipment.category'):
        return Domain.FALSE
    ids = _free_stock_ids(env)
    if model == 'maintenance.equipment':
        return Domain('id', 'in', ids)
    return Domain('id', 'in', env['maintenance.equipment'].sudo().browse(ids).category_id.ids)


def _move_ids(env, equipment_ids):
    allowed = set(equipment_ids)
    result = []
    for move in env['tp.equipment.move'].sudo().search([('company_id', 'in', env.companies.ids)]):
        # These parents may carry requester, aggregate or earlier transfer sources
        # which are not proven by the current equipment holder.
        if move.proposal_line_id or move.inventory_id or move.reversal_of_id or move.reversed_by_id:
            continue
        if move.maintenance_request_id and not move.maintenance_request_id.with_env(env).has_access('read'):
            continue
        if not move.line_ids or any(line.equipment_id.id not in allowed for line in move.line_ids):
            continue
        departments = env['hr.department'].sudo().browse()
        valid = True
        for line in move.line_ids:
            for prefix in ('from', 'to'):
                custody = line[prefix + '_custody']
                employee = line[prefix + '_employee_id']
                department = line[prefix + '_department_id']
                if custody in ('employee', 'loan') and employee:
                    current = _employee_department(employee)
                    historical = employee.with_context(version_id=False)._get_version(move.date).department_id
                    # HR may overwrite a same-day version. Without a frozen
                    # department on the move, its original scope is unprovable.
                    valid &= bool(department and current and historical and employee.company_id == move.company_id)
                    department |= current | historical
                elif custody != 'department':
                    valid = False
                valid &= bool(department and department.company_id == move.company_id)
                departments |= department
        for employee in move.target_employee_id:
            department = _employee_department(employee)
            valid &= bool(department and employee.company_id == move.company_id)
            departments |= department
        departments |= move.target_department_id
        if valid and env.user._tp_delegated_other_department(move.company_id, departments):
            result.append(move.id)
    return result


def _proposal_ids(env, equipment_ids):
    """Requester, recipients and old devices must all be proven outside sources."""
    allowed = set(equipment_ids)
    actor = env.user
    result = []
    for company in env.companies:
        if not actor._tp_has_admin_delegation(company):
            continue
        own, complete = actor._tp_delegation_scope(company)
        if not complete:
            continue
        proposals = env['tp.equipment.proposal'].sudo().with_context(active_test=False, version_id=False)
        for proposal in proposals.search([('company_id', '=', company.id)]):
            # A request the actor wrote, records or needs keeps the baseline.
            if env.uid in (proposal.create_uid.id, proposal.responsible_id.id,
                           proposal.requester_employee_id.user_id.id):
                continue
            departments = proposal.requester_department_id
            valid = bool(departments)
            for employee in proposal.requester_employee_id | proposal.line_ids.target_employee_id:
                current = _employee_department(employee)
                valid &= bool(current and employee.company_id == company)
                departments |= current
            departments |= proposal.line_ids.target_department_id
            valid &= all(not line.equipment_id or line.equipment_id.id in allowed for line in proposal.line_ids)
            if (valid and not (departments & own)
                    and all(department.company_id == company for department in departments)):
                result.append(proposal.id)
    return result


def equipment_domain(env, model, operation='read'):
    if model not in READ_MODELS or (operation != 'read' and model not in EDITABLE_MODELS):
        return Domain.FALSE
    ids = _equipment_ids(env)
    if model in PROPOSAL_MODELS:
        return Domain('id' if model == 'tp.equipment.proposal' else 'proposal_id', 'in', _proposal_ids(env, ids))
    if model == 'maintenance.equipment':
        return Domain('id', 'in', ids)
    if model in ('tp.equipment.software', 'tp.equipment.meter'):
        return Domain('equipment_id', 'in', ids)
    if model == 'maintenance.request':
        domain = Domain('equipment_id', 'in', ids)
        # A reporter or a proposal can introduce another department's private source.
        domain &= (Domain('tp_reporter_employee_id', '=', False) | Domain(
            'tp_reporter_employee_id', 'in', env['hr.employee'].sudo().search(
                env.user._tp_delegation_domain('company_id', 'current_version_id.department_id')).ids))
        return domain & Domain('tp_proposal_line_id', '=', False)
    if model in ('tp.equipment.move', 'tp.equipment.move.line'):
        return Domain('id' if model == 'tp.equipment.move' else 'move_id', 'in', _move_ids(env, ids))
    equipment = env['maintenance.equipment'].sudo().browse(ids)
    if model == 'maintenance.equipment.category':
        return Domain('id', 'in', equipment.category_id.ids)
    if model == 'tp.equipment.location':
        return Domain('id', 'in', equipment.tp_location_id.ids)
    return Domain('id', 'in', env['maintenance.request'].sudo().search(
        equipment_domain(env, 'maintenance.request')).stage_id.ids)


def _lock_sources(env, equipment, reporters):
    """Fence routing changes before a delegated mutation consumes their scope."""
    equipment = equipment.sudo().with_context(active_test=False, version_id=False)
    pending, found = equipment, equipment.browse()
    while pending:
        found |= pending
        pending = (pending.tp_parent_id | pending.tp_replaces_id) - found
    if found:
        env.cr.execute('SELECT id FROM maintenance_equipment WHERE id IN %s ORDER BY id FOR SHARE', [tuple(found.ids)])
        found.invalidate_recordset()
    employees = (found.tp_employee_id | reporters.sudo()).with_context(active_test=False, version_id=False)
    if employees:
        env.cr.execute('SELECT id FROM hr_employee WHERE id IN %s ORDER BY id FOR SHARE', [tuple(employees.ids)])
        env.cr.execute('SELECT id FROM hr_version WHERE employee_id IN %s ORDER BY id FOR SHARE', [tuple(employees.ids)])
        versions = env['hr.version'].sudo().browse([row[0] for row in env.cr.fetchall()])
        versions.invalidate_recordset()
        employees.invalidate_recordset()
    departments = found.tp_holder_department_id
    for employee in employees:
        departments |= _employee_department(employee)
    if departments:
        env.cr.execute('SELECT id FROM hr_department WHERE id IN %s ORDER BY id FOR SHARE', [tuple(departments.ids)])
        departments.invalidate_recordset()
    companies = found.company_id | employees.company_id | departments.company_id
    if companies:
        env.cr.execute('SELECT id FROM res_company WHERE id IN %s ORDER BY id FOR SHARE', [tuple(companies.ids)])
        companies.invalidate_recordset()


class EquipmentScope(models.AbstractModel):
    _name = 'tp.admin.equipment.scope.mixin'
    _description = 'Audited equipment sources for delegated administration'

    def _access_domain(self, operation):
        domain = super()._access_domain(operation) | equipment_domain(self.env, self._name, operation)
        if operation == 'read':
            domain |= free_stock_domain(self.env, self._name)
        return domain

    def _tp_delegated_handover(self):
        return self.env.su and self.env.context.get(HANDOVER_KEY) is _HANDOVER

    def _tp_equipment_delegate_check(self):
        if not self.env.user._tp_has_admin_delegation():
            raise AccessError(GENERIC_DENIED)
        if self._name not in READ_MODELS:
            raise AccessError(GENERIC_DENIED)
        self.sudo(False).check_access('read')
        if self._name == 'maintenance.equipment' and set(self.ids) - set(_equipment_ids(self.env)):
            # Labels, register, moves and other record actions never treat free stock as held.
            raise AccessError(self.env._(STOCK_DENIED))

    def _tp_lock_equipment_sources(self, vals_list=None):
        equipment = self.env['maintenance.equipment']
        reporters = self.env['hr.employee']
        if self._name == 'maintenance.equipment':
            equipment = self
        elif self._name in EDITABLE_MODELS:
            equipment = self.sudo().equipment_id
            if self._name == 'maintenance.request':
                reporters = self.sudo().tp_reporter_employee_id
        if vals_list:
            defaults = self.default_get(['equipment_id', 'tp_reporter_employee_id'] if self._name == 'maintenance.request'
                                        else ['equipment_id'])
            for supplied in vals_list:
                values = {**defaults, **supplied}
                equipment |= equipment.browse(values.get('equipment_id'))
                reporters |= reporters.browse(values.get('tp_reporter_employee_id'))
        _lock_sources(self.env, equipment, reporters)
        return equipment.sudo(False)

    @api.model_create_multi
    def create(self, vals_list):
        if self._tp_delegated_handover():
            return super().create(vals_list)
        delegated = self.env.user._tp_has_admin_delegation(lock=True)
        if not delegated:
            return super().create(vals_list)
        if self._name not in EDITABLE_MODELS or self._name == 'maintenance.equipment':
            raise AccessError(self.env._('Đăng ký thiết bị và kho dùng chung cần Quản trị chính.'))
        equipment = self._tp_lock_equipment_sources(vals_list)
        equipment.check_access('write')
        if self._name == 'maintenance.request':
            # hr_maintenance defaults this to the actor, then computes an owner.
            # The physical reporter has a separate, source-checked TP field.
            vals_list = [dict(vals, employee_id=False, owner_user_id=False, user_ids=[(6, 0, [])]) for vals in vals_list]
        with self.env.cr.savepoint():
            records = super().create(vals_list)
            records.sudo(False).check_access('create')
            return records

    def write(self, vals):
        if self._tp_delegated_handover() or not self.env.user._tp_has_admin_delegation(lock=True):
            return super().write(vals)
        self._tp_lock_equipment_sources()
        self.sudo(False).check_access('write')
        if ((self._name == 'maintenance.equipment' and set(vals) & EQUIPMENT_SCOPE_FIELDS)
                or (self._name in ('tp.equipment.software', 'tp.equipment.meter') and 'equipment_id' in vals)
                or (self._name == 'maintenance.request' and set(vals) & {
                    'company_id', 'equipment_id', 'tp_reporter_employee_id', 'tp_proposal_line_id',
                    'employee_id', 'owner_user_id', 'user_ids',
                })):
            raise AccessError(self.env._('Thay nguồn, người giữ hoặc phòng của thiết bị cần Quản trị chính.'))
        with self.env.cr.savepoint():
            result = super().write(vals)
            self.sudo(False).check_access('write')
            return result

    def unlink(self):
        if self.env.user._tp_has_admin_delegation(lock=True):
            self._tp_lock_equipment_sources()
            self.sudo(False).check_access('unlink')
        return super().unlink()

    def _tp_equipment_post_context(self, kwargs):
        # The handover adapter posts the native move note under its own checks.
        if self._tp_delegated_handover() or not self.env.user._tp_has_admin_delegation(lock=True):
            return self
        self._tp_lock_equipment_sources()
        self.sudo(False).check_access('write')
        if (self._name not in EDITABLE_MODELS or kwargs.get('attachments') or kwargs.get('attachment_ids')
                or kwargs.get('author_guest_id')
                or kwargs.get('author_id', self.env.user.partner_id.id) != self.env.user.partner_id.id
                or kwargs.get('message_type', 'notification') not in ('comment', 'notification')):
            raise AccessError(self.env._('Chỉ ghi trao đổi theo danh tính hiện tại, không thêm tệp qua ủy quyền.'))
        # Native recipient filtering stays in tp_equipment. The sentinel opens
        # creation only inside this parent-checked mail.thread path.
        return self.with_context(_tp_equipment_post=_POST)


class Equipment(models.Model):
    _name = 'maintenance.equipment'
    _inherit = ['maintenance.equipment', 'tp.admin.equipment.scope.mixin']

    tp_employee_image_128 = fields.Image(groups='base.group_system,base.group_user')
    tp_employee_job_title = fields.Char(groups='base.group_system,base.group_user')
    tp_employee_code = fields.Char(groups='base.group_system,base.group_user')

    def message_post(self, **kwargs):
        return super(Equipment, self._tp_equipment_post_context(kwargs)).message_post(**kwargs)


class Repair(models.Model):
    _name = 'maintenance.request'
    _inherit = ['maintenance.request', 'tp.admin.equipment.scope.mixin']

    def message_post(self, **kwargs):
        return super(Repair, self._tp_equipment_post_context(kwargs)).message_post(**kwargs)


class Software(models.Model):
    _name = 'tp.equipment.software'
    _inherit = ['tp.equipment.software', 'tp.admin.equipment.scope.mixin']

    evidence_ref = fields.Char(groups='base.group_system,base.group_user')

    def message_post(self, **kwargs):
        return super(Software, self._tp_equipment_post_context(kwargs)).message_post(**kwargs)


class Meter(models.Model):
    _name = 'tp.equipment.meter'
    _inherit = ['tp.equipment.meter', 'tp.admin.equipment.scope.mixin']

    def message_post(self, **kwargs):
        return super(Meter, self._tp_equipment_post_context(kwargs)).message_post(**kwargs)


class Move(models.Model):
    _name = 'tp.equipment.move'
    _inherit = ['tp.equipment.move', 'tp.admin.equipment.scope.mixin']


class MoveLine(models.Model):
    _name = 'tp.equipment.move.line'
    _inherit = ['tp.equipment.move.line', 'tp.admin.equipment.scope.mixin']


class Category(models.Model):
    _name = 'maintenance.equipment.category'
    _inherit = ['maintenance.equipment.category', 'tp.admin.equipment.scope.mixin']


class Location(models.Model):
    _name = 'tp.equipment.location'
    _inherit = ['tp.equipment.location', 'tp.admin.equipment.scope.mixin']


class Stage(models.Model):
    _name = 'maintenance.stage'
    _inherit = ['maintenance.stage', 'tp.admin.equipment.scope.mixin']


class Proposal(models.Model):
    _name = 'tp.equipment.proposal'
    _inherit = ['tp.equipment.proposal', 'tp.admin.equipment.scope.mixin']


class ProposalLine(models.Model):
    _name = 'tp.equipment.proposal.line'
    _inherit = ['tp.equipment.proposal.line', 'tp.admin.equipment.scope.mixin']


class ProposalReview(models.Model):
    _name = 'tp.equipment.proposal.review'
    _inherit = ['tp.equipment.proposal.review', 'tp.admin.equipment.scope.mixin']


class EquipmentDashboard(models.AbstractModel):
    _inherit = 'tp.equipment.dashboard'

    def _tp_equipment_delegate_check(self):
        # Overview counts run with the caller's own scoped record access.
        self.env['maintenance.equipment']._tp_equipment_delegate_check()

    @api.model
    def get_dashboard(self, filters=None):
        result = super().get_dashboard(filters)
        user = self.env.user
        if user._tp_has_admin_delegation():
            own = user._tp_delegation_departments()
            result['options']['departments'] = [
                row for row in result['options']['departments'] if row['id'] not in own.ids]
            result['delegated_scope'] = DELEGATED_LABEL
        return result


def _equipment_parent(env, model, record_id):
    if model == 'mail.message' and record_id:
        message = env['mail.message'].sudo().browse(record_id).exists()
        model, record_id = message.model, message.res_id
    return env[model].sudo(False).browse(record_id).exists() if model in TP_EQUIPMENT_MODELS and record_id else None


class EquipmentAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        if operation != 'read' or not self.env.user._tp_has_admin_delegation():
            return baseline
        parts = [Domain([('res_model', '=', model), ('res_id', 'in', self.env[model].sudo().search(
            equipment_domain(self.env, model)).ids)]) for model in READ_MODELS]
        return baseline | Domain.OR(parts)

    def _tp_equipment_file_check(self, mutation=False):
        for metadata in self.sudo():
            parent = _equipment_parent(self.env, metadata.res_model, metadata.res_id)
            if parent is not None:
                if not parent:
                    raise AccessError(GENERIC_DENIED)
                if metadata.public:
                    raise AccessError(self.env._('Tệp thiết bị riêng tư không được công khai.'))
                parent.check_access('write' if mutation else 'read')

    def read(self, fields=None, load='_classic_read'):
        self._tp_equipment_file_check()
        return super().read(fields, load)

    def export_data(self, fields_to_export):
        self._tp_equipment_file_check()
        return super().export_data(fields_to_export)

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(['res_model', 'res_id'])
        for supplied in vals_list:
            values = {**defaults, **supplied}
            parent = _equipment_parent(self.env, values.get('res_model'), values.get('res_id'))
            if parent is not None and self.env.user._tp_has_admin_delegation(lock=True):
                raise AccessError(self.env._('Thêm hoặc chuyển tệp thiết bị cần Quản trị chính.'))
        return super().create(vals_list)

    def write(self, vals):
        self._tp_equipment_file_check(mutation=True)
        if set(vals) & {'res_model', 'res_id'}:
            for metadata in self.sudo():
                parent = _equipment_parent(self.env, vals.get('res_model', metadata.res_model), vals.get('res_id', metadata.res_id))
                if parent is not None:
                    parent.check_access('write')
        return super().write(vals)

    def unlink(self):
        self._tp_equipment_file_check(mutation=True)
        return super().unlink()


class EquipmentMessage(models.Model):
    _inherit = 'mail.message'

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        posting = operation == 'create' and self.env.context.get('_tp_equipment_post') is _POST
        if (operation != 'read' and not posting) or not self.env.user._tp_has_admin_delegation():
            return baseline
        models_to_open = EDITABLE_MODELS if posting else READ_MODELS
        parts = [Domain([('model', '=', model), ('res_id', 'in', self.env[model].sudo().search(
            equipment_domain(self.env, model, 'write' if posting else 'read')).ids)])
                 for model in models_to_open]
        return baseline | Domain.OR(parts)

    def _get_with_access(self, mode='read', **kwargs):
        for message in self.sudo():
            parent = _equipment_parent(self.env, message.model, message.res_id)
            if parent is not None:
                if not parent:
                    raise AccessError(GENERIC_DENIED)
                parent.check_access('read' if mode == 'read' else 'write')
        return super()._get_with_access(mode=mode, **kwargs)


class EquipmentBinary(models.AbstractModel):
    _inherit = 'ir.binary'

    def _find_record(self, xmlid=None, res_model='ir.attachment', res_id=None, access_token=None, field=None):
        record = (self.env.ref(xmlid, raise_if_not_found=False) if xmlid else
                  self.env[res_model].browse(res_id).exists() if res_id and res_model in self.env else None)
        if record and record._name == 'ir.attachment':
            record._tp_equipment_file_check()
        elif record and record._name in TP_EQUIPMENT_MODELS:
            record.sudo(False).check_access('read')
        return super()._find_record(xmlid, res_model, res_id, access_token, field)
