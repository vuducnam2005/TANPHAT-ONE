# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Equipment & IT execution integration with tp_equipment (Section XII).

- Normal employees never receive Warehouse/Equipment admin rights; they only read safe
  metadata about equipment currently assigned to themselves via tp_my_equipment_options().
- Post-approval execution strictly reuses tp_equipment workflows:
  * equipment_assign -> checks free_domain + _tp_assign_problem under lock -> tp.equipment.move (assign) + action_done.
  * equipment_swap -> locks old & new equipment -> return/loan_return (with explicit actual old condition) + assign in 1 transaction.
  * equipment_repair -> creates & links real maintenance.request.
  * equipment_purchase -> creates & links tp.equipment.proposal (NEVER auto-creates stock assets on approval).
- Existing historical tp.equipment.proposal records remain untouched.
"""
from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, UserError

from odoo.addons.tp_equipment.models.common import INTERNAL as EQ_INTERNAL
from odoo.addons.tp_equipment.models.common import TECH_STATE, check_admin as eq_check_admin, lock_records as eq_lock_records
from odoo.addons.tp_equipment.models.quick_action import free_domain as eq_free_domain

from .request_common import OLD_EQUIP_CONDITIONS, internal, is_live_admin_user


class TpRequestEquipmentBridge(models.Model):
    _inherit = 'tp.request'

    @api.model
    def tp_my_equipment_options(self):
        """Return ONLY active equipment currently assigned to the caller's own employee record."""
        emp = self._tp_own_employee(self.env.user, self.env.company)
        if not emp:
            return []
        equipments = self.env['maintenance.equipment'].sudo().search([
            ('tp_employee_id', '=', emp.id),
            ('tp_custody', 'in', ('employee', 'loan')),
            ('tp_lifecycle', '=', 'active'),
            ('company_id', '=', self.env.company.id),
        ], order='tp_code, id')
        tech_labels = dict(TECH_STATE)
        return [{
            'id': eq.id,
            'code': eq.tp_code or '',
            'name': eq.name or '',
            'display_name': eq.display_name,
            'category_name': eq.category_id.name if eq.category_id else '',
            'brand_model': ' · '.join(p for p in (eq.tp_brand, eq.model) if p),
            'technical_state': eq.tp_technical_state,
            'technical_state_label': tech_labels.get(eq.tp_technical_state, ''),
        } for eq in equipments]

    @api.model
    def tp_equipment_categories(self):
        """Return active equipment category names (safe catalog metadata for employee requests)."""
        cats = self.env['maintenance.equipment.category'].sudo().search([('active', '=', True)], order='tp_sequence, name')
        return [{'id': c.id, 'name': c.name} for c in cats]

    def tp_eligible_stock_equipment(self):
        """Return stock equipment eligible for assign/swap right now (Equipment admin only)."""
        self.ensure_one()
        if not is_live_admin_user(self.env.user, company=self.company_id):
            raise AccessError(_('Chỉ quản trị thiết bị mới được xem danh sách thiết bị tồn kho đủ điều kiện cấp phát.'))
        eq_check_admin(self.env)
        domain = eq_free_domain(self.env) + [('company_id', '=', self.company_id.id)]
        if self.equipment_category_id:
            # Prefer matching category first, still return all eligible in company sorted with matching category first
            pass
        machines = self.env['maintenance.equipment'].search(domain, order='tp_code, id')
        tech_labels = dict(TECH_STATE)
        rows = []
        for eq in machines:
            if eq._tp_assign_problem():
                continue
            rows.append({
                'id': eq.id,
                'code': eq.tp_code or '',
                'name': eq.name or '',
                'display_name': eq.display_name,
                'category_id': eq.category_id.id or False,
                'category_name': eq.category_id.name if eq.category_id else '',
                'short_config': eq.tp_short_config or '',
                'technical_state': eq.tp_technical_state,
                'technical_state_label': tech_labels.get(eq.tp_technical_state, ''),
                'is_unverified': eq._tp_is_unverified(),
                'matches_category': bool(self.equipment_category_id and eq.category_id == self.equipment_category_id),
            })
        rows.sort(key=lambda r: (not r['matches_category'], r['code'], r['id']))
        return rows

    def action_create_equipment_repair(self, expected_version=None):
        """Executor action for approved equipment_repair: creates real maintenance.request & starts execution."""
        self.ensure_one()
        self.check_access('read')
        if expected_version is not None and self.version != int(expected_version):
            raise UserError(_('Hồ sơ đã thay đổi. Vui lòng tải lại.'))
        self._tp_check_executor()
        if self.handler_kind != 'equipment_repair':
            raise UserError(_('Thao tác này chỉ áp dụng cho đề nghị sửa chữa / báo hỏng thiết bị.'))
        if not is_live_admin_user(self.env.user, company=self.company_id, lock=True):
            raise AccessError(_('Cần quyền Quản trị Kho thiết bị để tạo phiếu sửa chữa thực tế.'))
        eq_check_admin(self.env)
        if self.equipment_repair_id:
            return {'repair_id': self.equipment_repair_id.id, 'repair_code': self.equipment_repair_id.tp_code or self.equipment_repair_id.name}
        if not self.equipment_id:
            raise UserError(_('Hồ sơ chưa chọn thiết bị cần sửa chữa.'))

        repair = self.env['maintenance.request'].create({
            'name': _('Sửa chữa theo %(code)s — %(eq)s', code=self.code, eq=self.equipment_id.display_name),
            'equipment_id': self.equipment_id.id,
            'company_id': self.company_id.id,
            'tp_kind': 'fault',
            'tp_reporter_employee_id': self.requester_employee_id.id or False,
            'tp_symptom': (self.equipment_issue_detail or self.description or self.title),
            'maintenance_type': 'corrective',
        })
        old_exec = self.execution_state
        internal(self).write({
            'equipment_repair_id': repair.id,
            'execution_state': 'in_progress',
            'assigned_executor_id': self.env.uid,
            'execution_started_at': self.execution_started_at or fields.Datetime.now(),
            'version': self.version + 1,
        })
        self._tp_record_history(
            'link_result',
            state_before=old_exec,
            state_after='in_progress',
            step_name=_('Tạo phiếu sửa chữa'),
            note=_('Đã tạo phiếu sửa chữa thiết bị %s', repair.tp_code or repair.name),
            result_ref=repair.tp_code or repair.name,
        )
        return {'repair_id': repair.id, 'repair_code': repair.tp_code or repair.name}

    def action_create_equipment_proposal(self, expected_version=None):
        """Executor action for approved equipment_purchase: creates tp.equipment.proposal (NOT stock asset!)."""
        self.ensure_one()
        self.check_access('read')
        if expected_version is not None and self.version != int(expected_version):
            raise UserError(_('Hồ sơ đã thay đổi. Vui lòng tải lại.'))
        self._tp_check_executor()
        if self.handler_kind != 'equipment_purchase':
            raise UserError(_('Thao tác này chỉ áp dụng cho đề nghị mua bổ sung thiết bị.'))
        if not is_live_admin_user(self.env.user, company=self.company_id, lock=True):
            raise AccessError(_('Cần quyền Quản trị Kho thiết bị để lập đề xuất mua sắm.'))
        eq_check_admin(self.env)
        if self.equipment_proposal_id:
            return {'proposal_id': self.equipment_proposal_id.id, 'proposal_code': self.equipment_proposal_id.name}

        desc = (self.equipment_category_id.name if self.equipment_category_id else self.title)
        proposal = self.env['tp.equipment.proposal'].create({
            'title': _('%(title)s (theo %(code)s)', title=self.title, code=self.code),
            'company_id': self.company_id.id,
            'requester_employee_id': self.requester_employee_id.id or False,
            'requester_department_id': self.department_id.id or False,
            'note': _('Lập từ hồ sơ Đề nghị & Phê duyệt %s. Duyệt mua không tự tạo tài sản nhập kho.', self.code),
            'source_ref': f'tp.request:{self.code}',
            'line_ids': [Command.create({
                'kind': 'purchase',
                'description': desc,
                'category_id': self.equipment_category_id.id or False,
                'desired_config': self.equipment_desired_spec or self.description or False,
                'quantity': max(self.equipment_quantity or 1, 1),
            })],
        })
        old_exec = self.execution_state
        internal(self).write({
            'equipment_proposal_id': proposal.id,
            'execution_state': 'in_progress',
            'assigned_executor_id': self.env.uid,
            'execution_started_at': self.execution_started_at or fields.Datetime.now(),
            'version': self.version + 1,
        })
        self._tp_record_history(
            'link_result',
            state_before=old_exec,
            state_after='in_progress',
            step_name=_('Lập đề xuất mua sắm'),
            note=_('Đã tạo đề xuất mua sắm %s trong Kho thiết bị (chờ quy trình mua & nhập kho).', proposal.name),
            result_ref=proposal.name,
        )
        return {'proposal_id': proposal.id, 'proposal_code': proposal.name}

    def _tp_execute_equipment_completion(self, result_note, extra):
        """Run authoritative tp_equipment workflow on completion inside the same DB transaction."""
        self.ensure_one()
        kind = self.handler_kind

        if kind == 'equipment_assign':
            if not is_live_admin_user(self.env.user, company=self.company_id, lock=True):
                raise AccessError(_('Cần quyền Quản trị Kho thiết bị để xác nhận cấp phát máy thực tế.'))
            eq_check_admin(self.env)
            if not self.requester_employee_id:
                raise UserError(_('Người gửi chưa liên kết hồ sơ nhân viên trong HR nên chưa thể bàn giao thiết bị.'))
            target_id = int(extra.get('fulfilled_equipment_id') or 0)
            if not target_id:
                raise UserError(_('Vui lòng chọn thiết bị thực tế đủ điều kiện trong kho trước khi hoàn thành cấp phát.'))
            machine = self.env['maintenance.equipment'].browse(target_id).exists()
            if not machine:
                raise UserError(_('Thiết bị được chọn không tồn tại.'))

            # Lock equipment row and re-verify eligibility right at confirmation time (prevents double-assign!)
            eq_lock_records(machine)
            problem = machine._tp_assign_problem()
            if problem:
                raise UserError(problem)
            if machine.company_id != self.company_id:
                raise UserError(_('Thiết bị không cùng công ty với hồ sơ đề nghị.'))

            move = self.env['tp.equipment.move'].with_context(tp_equipment_move_internal=EQ_INTERNAL).create({
                'move_type': 'assign',
                'company_id': self.company_id.id,
                'target_custody': 'employee',
                'target_employee_id': self.requester_employee_id.id,
                'reason': _('Cấp phát theo đề nghị %(code)s — %(title)s. %(note)s',
                            code=self.code, title=self.title, note=result_note),
                'idempotency_key': f'tpreq:{self.id}:assign:{machine.id}',
                'line_ids': [Command.create({'equipment_id': machine.id})],
            })
            move.action_done()
            internal(self).write({
                'fulfilled_equipment_id': machine.id,
                'equipment_move_ids': [Command.link(move.id)],
            })
            return f'{move.name} ({machine.display_name})'

        if kind == 'equipment_swap':
            if not is_live_admin_user(self.env.user, company=self.company_id, lock=True):
                raise AccessError(_('Cần quyền Quản trị Kho thiết bị để xác nhận thu hồi và đổi thiết bị.'))
            eq_check_admin(self.env)
            if not self.requester_employee_id:
                raise UserError(_('Người gửi chưa liên kết hồ sơ nhân viên trong HR.'))
            old_machine = self.equipment_id
            if not old_machine:
                raise UserError(_('Hồ sơ đổi máy chưa xác định thiết bị cũ đang dùng.'))
            new_id = int(extra.get('fulfilled_equipment_id') or 0)
            if not new_id:
                raise UserError(_('Vui lòng chọn thiết bị mới trong kho để đổi.'))
            old_condition = (extra.get('old_equipment_condition') or '').strip()
            if old_condition not in dict(OLD_EQUIP_CONDITIONS):
                raise UserError(_('Bắt buộc xác nhận tình trạng thực tế của thiết bị cũ khi thu hồi (Tốt / Hạn chế / Hỏng).'))
            new_machine = self.env['maintenance.equipment'].browse(new_id).exists()
            if not new_machine:
                raise UserError(_('Thiết bị mới được chọn không tồn tại.'))
            if new_machine == old_machine:
                raise UserError(_('Thiết bị mới phải khác thiết bị cũ đang sử dụng.'))

            # Lock both machines in deterministic ID order (FOR UPDATE NOWAIT)
            eq_lock_records(old_machine | new_machine)
            if old_machine.tp_lifecycle != 'active' or old_machine.tp_custody not in ('employee', 'loan') or old_machine.tp_employee_id != self.requester_employee_id:
                raise UserError(_('Thiết bị cũ “%s” không còn do người đề nghị đang sử dụng. Vui lòng kiểm tra lại.', old_machine.display_name))
            problem = new_machine._tp_assign_problem()
            if problem:
                raise UserError(problem)

            MoveInternal = self.env['tp.equipment.move'].with_context(tp_equipment_move_internal=EQ_INTERNAL)
            ret_type = 'loan_return' if old_machine.tp_custody == 'loan' else 'return'
            ret_move = MoveInternal.create({
                'move_type': ret_type,
                'company_id': self.company_id.id,
                'reason': _('Thu hồi máy cũ khi đổi theo đề nghị %(code)s. %(note)s', code=self.code, note=result_note),
                'idempotency_key': f'tpreq:{self.id}:swap-ret:{old_machine.id}',
                'line_ids': [Command.create({'equipment_id': old_machine.id, 'condition': old_condition})],
            })
            assign_move = MoveInternal.create({
                'move_type': 'assign',
                'company_id': self.company_id.id,
                'target_custody': 'employee',
                'target_employee_id': self.requester_employee_id.id,
                'reason': _('Bàn giao máy mới khi đổi theo đề nghị %(code)s (thay %(old)s). %(note)s',
                            code=self.code, old=old_machine.display_name, note=result_note),
                'idempotency_key': f'tpreq:{self.id}:swap-assign:{new_machine.id}',
                'line_ids': [Command.create({'equipment_id': new_machine.id})],
            })
            # Return leg first, then assign leg in same atomic transaction
            ret_move.action_done()
            assign_move.action_done()
            internal(self).write({
                'fulfilled_equipment_id': new_machine.id,
                'old_equipment_condition': old_condition,
                'equipment_move_ids': [Command.link(ret_move.id), Command.link(assign_move.id)],
            })
            return f'{ret_move.name} + {assign_move.name} ({new_machine.display_name})'

        if kind == 'equipment_repair':
            if self.equipment_repair_id:
                return self.equipment_repair_id.sudo().tp_code or self.equipment_repair_id.sudo().name
            return self.equipment_name_snap or ''

        if kind == 'equipment_purchase':
            # Never auto-creates maintenance.equipment in stock!
            if self.equipment_proposal_id:
                return self.equipment_proposal_id.sudo().name
            return ''

        return ''
