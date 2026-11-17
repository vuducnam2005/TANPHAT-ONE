"""Delegated Gán / Đổi máy / Trả về kho (ADMIN-DELEGATE-002 slice 3).

A live delegate may hand a free company-common machine to a person of another department, swap
that person's machine for a free one, or return machines held outside the delegate's protected
departments. Each confirmation locks the machines (stable id order, NOWAIT) and every holder,
recipient, version, department and company, re-checks all of them, then runs the existing
one-RPC handover of tp_equipment in the same transaction: a swap returns A *and* assigns B or
changes nothing. Own, unknown, mixed and other-company sources keep the baseline (main
administrator only). Stock is never treated as another department.
"""
import hashlib
import json

from psycopg2 import errors as pg_errors

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.fields import Domain
from odoo.tools import SQL, clean_context

from .equipment_scope import (
    _HANDOVER,
    HANDOVER_KEY,
    _employee_department,
    _held_departments,
    _lock_sources,
)
from odoo.addons.tp_equipment.models.common import GENERIC_DENIED, is_admin
from odoo.addons.tp_equipment.models.quick_action import (
    CHANGED_MSG,
    TAKEN_MSG,
    _command_ids,
    _positive_id,
)

OWN_RECIPIENT = 'Người nhận thuộc phòng của bạn hoặc chưa rõ phòng: việc này cần Quản trị chính.'
OWN_SOURCE = '%s đang ở phòng của bạn hoặc chưa xác định nguồn: việc này cần Quản trị chính.'
UNKNOWN_SCOPE = 'Phòng nghiệp vụ của bạn chưa xác định: gán/đổi/trả thiết bị cần Quản trị chính.'


def _delegate(env):
    """A live delegate acting with their own rights (main administrators keep the native path)."""
    return not is_admin(env) and env.user._tp_has_admin_delegation()


class HandoverEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    def action_tp_open_detail(self):
        if len(self) != 1 or not _delegate(self.env):
            return super().action_tp_open_detail()
        # "Xem" on a free stock row opens the record the picker already shows; actions stay checked.
        self.check_access('read')
        return super(HandoverEquipment, self.sudo()).action_tp_open_detail()

    def _tp_quick_open(self, mode, **defaults):
        if not _delegate(self.env):
            return super()._tp_quick_open(mode, **defaults)
        # Opening the popup saves nothing; returned or swapped machines must be held outside.
        if mode == 'assign':
            self.check_access('read')
        else:
            self._tp_equipment_delegate_check()
            self.check_access('write')
        return super(HandoverEquipment, self.sudo())._tp_quick_open(mode, **defaults)

    @api.model
    def tp_quick_action(self, payload):
        if not _delegate(self.env):
            return super().tp_quick_action(payload)
        return self.with_context(clean_context(self.env.context))._tp_delegated_quick(payload)

    def _tp_delegated_quick(self, payload):
        user = self.env.user
        if not user._tp_has_admin_delegation(lock=True):
            raise AccessError(GENERIC_DENIED)
        data = self._tp_quick_normalize(payload)
        key = data.pop('request_key')
        digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        previous = self.env['tp.equipment.move'].sudo().search([('tp_request_key', '=', key)], order='id')
        if previous:
            # A replay returns the actor's own result; another request is never read through it.
            if any(move.tp_request_hash != digest or move.create_uid != user for move in previous):
                raise UserError(self.env._('%s (mã yêu cầu đã dùng cho nội dung khác).', CHANGED_MSG))
            return self.sudo()._tp_quick_result(data, previous)

        mode = data['mode']
        machines = self.sudo().with_context(active_test=False, version_id=False)
        if mode == 'assign':
            olds, targets = machines.browse(), machines.browse(data['equipment_ids'])
        elif mode == 'swap':
            olds = machines.browse(data['old_equipment_id'] or [])
            targets = machines.browse(data['new_equipment_id'] or [])
        else:
            olds, targets = machines.browse(data['equipment_ids']), machines.browse()
        machines = olds | targets
        if not machines:
            raise UserError(self.env._('Chọn thiết bị cần thao tác.'))
        if len(machines.exists()) != len(machines):
            raise UserError(self.env._('%s (thiết bị không còn tồn tại).', CHANGED_MSG))
        employee = self.env['hr.employee'].sudo().with_context(active_test=False, version_id=False).browse(
            data['employee_id'] or [])
        if employee and not employee.exists():
            raise UserError(self.env._('%s (người sử dụng không còn tồn tại).', CHANGED_MSG))
        if mode in ('assign', 'swap') and not employee:
            raise UserError(self.env._('Chọn người sử dụng.'))

        # Same row lock as the native path: two people picking one machine serialize here.
        try:
            with self.env.cr.savepoint(flush=False):
                self.env.cr.execute(SQL(
                    'SELECT id FROM maintenance_equipment WHERE id IN %s ORDER BY id FOR UPDATE NOWAIT',
                    tuple(machines.ids)))
        except pg_errors.LockNotAvailable:
            raise UserError(self.env._('Thiết bị đang được xử lý ở thao tác khác. Thử lại sau ít giây.')) from None
        machines.invalidate_recordset()
        _lock_sources(self.env, machines, employee)
        company = self._tp_delegated_handover_check(employee, olds, targets)

        runner = self.sudo().with_context(allowed_company_ids=company.ids, **{HANDOVER_KEY: _HANDOVER})
        with self.env.cr.savepoint():
            result = runner._tp_quick_run(payload)
            machines.invalidate_recordset()
            if (any(machine.tp_custody != 'employee' or machine.tp_employee_id != employee for machine in targets)
                    or any(machine.tp_custody != 'stock' or machine.tp_employee_id for machine in olds)):
                raise UserError(CHANGED_MSG)
        return result

    def _tp_delegated_handover_check(self, employee, olds, targets):
        """Every source and target again after the locks; returns the single company."""
        user = self.env.user
        company = (olds | targets).company_id
        if len(company) != 1 or (employee and employee.company_id != company):
            raise UserError(self.env._('Thiết bị và người sử dụng phải thuộc cùng một công ty.'))
        if company not in self.env.companies or not user._tp_has_admin_delegation(company):
            raise AccessError(GENERIC_DENIED)
        own, complete = user._tp_delegation_scope(company)
        if not complete:
            raise AccessError(self.env._(UNKNOWN_SCOPE))
        if employee:
            department = _employee_department(employee)
            if not department or department.company_id != company or department & own or employee.user_id == user:
                raise AccessError(self.env._(OWN_RECIPIENT))
        for machine in olds:
            departments = _held_departments(machine)
            if not departments or departments & own:
                raise AccessError(self.env._(OWN_SOURCE, machine.display_name))
        for machine in targets:
            # Only an unheld machine leaves stock; a replacement keeps its holder's source.
            if machine.tp_custody != 'stock' or machine.tp_employee_id:
                raise UserError('%s (%s).' % (TAKEN_MSG, machine.display_name))
            if machine.tp_replaces_id:
                departments = _held_departments(machine.tp_replaces_id)
                if not departments or departments & own:
                    raise AccessError(self.env._(OWN_SOURCE, machine.display_name))
        return company


class HandoverPopup(models.TransientModel):
    _inherit = 'tp.equipment.quick.action'

    employee_id = fields.Many2one(domain=lambda self: self._tp_recipient_domain())

    @api.model
    def _tp_recipient_domain(self):
        domain = [('company_id', 'in', self.env.companies.ids)]
        if _delegate(self.env):
            own = self.env.user._tp_delegation_departments()
            domain += [('department_id', '!=', False), ('department_id', 'not in', own.ids)]
        return domain

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        if not _delegate(self.env):
            return baseline
        # The popup only collects a choice; a delegate uses their own popups.
        return baseline | Domain('create_uid', '=', self.env.uid)

    @api.model
    def default_get(self, fields_list):
        if not _delegate(self.env):
            return super().default_get(fields_list)
        context = self.env.context
        ids = set(_command_ids(context.get('default_assign_equipment_ids'))
                  + _command_ids(context.get('default_return_equipment_ids')))
        for name in ('default_old_equipment_id', 'default_new_equipment_id'):
            if _positive_id(context.get(name)):
                ids.add(context[name])
        # Version stamps only for machines the caller can already see.
        self.env['maintenance.equipment'].browse(sorted(ids)).check_access('read')
        return super(HandoverPopup, self.sudo()).default_get(fields_list)

    def action_confirm(self):
        if not _delegate(self.env):
            return super().action_confirm()
        self.ensure_one()
        self.check_access('write')
        # The full choice is sent: a machine taken meanwhile must fail, never silently drop out.
        result = self.env['maintenance.equipment'].tp_quick_action(self.sudo()._tp_payload())
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'type': 'success', 'title': result['title'], 'message': result['message'],
                       'sticky': False, 'next': {'type': 'ir.actions.act_window_close'}},
        }
