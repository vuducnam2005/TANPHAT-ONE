"""Reviewed admin adapter for existing live KH-KD responsibilities."""
import hashlib
import json

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, UserError

_ROLE_PREVIEW = object()
_ACCESS_LABELS = {
    'reader': 'Đọc theo phân công', 'coordinator': 'Điều phối dự án',
    'prepare': 'Lập và sửa hồ sơ',
    'financial_read': 'Đọc thông tin tài chính', 'financial_draft_edit': 'Sửa số liệu tài chính nháp',
    'contract_draft_edit': 'Sửa bản nháp hợp đồng', 'contract_submit': 'Trình duyệt hợp đồng',
    'contract_review_commercial': 'Rà soát thương mại hợp đồng',
    'read': 'Đọc hồ sơ', 'draft_edit': 'Sửa hồ sơ nháp', 'submit': 'Trình duyệt hồ sơ',
    'review': 'Rà soát hồ sơ', 'approve': 'Duyệt hồ sơ', 'cancel': 'Hủy hồ sơ',
}


class DepartmentHead(models.Model):
    _inherit = 'tp.kd.department.role'

    # Reserve the seat until explicit revocation, including expired or locked users.
    _unique_department_head = models.UniqueIndex(
        '(company_id, department_id) WHERE active IS TRUE',
        'Phòng ban đã có trưởng phòng. Vui lòng hạ cấp trưởng phòng hiện tại trước khi bổ nhiệm nhân viên khác.',
    )


class EmployeeRole(models.Model):
    _inherit = 'hr.employee'

    tp_business_role = fields.Char(compute='_compute_business_role', string='Vai trò nghiệp vụ')
    tp_role_supported = fields.Boolean(compute='_compute_business_role')
    tp_role_scope = fields.Char(compute='_compute_business_role', string='Phạm vi quyền')
    tp_extra_access = fields.Text(compute='_compute_business_role', string='Quyền cấp riêng', groups='base.group_system')

    def _tp_role_supported(self):
        self.ensure_one()
        # Explicit CRM scope configuration; department names and HR jobs never grant access.
        return bool(self.department_id and self.env['crm.team'].sudo().search_count([
            ('company_id', '=', self.company_id.id), ('kd_department_id', '=', self.department_id.id), ('active', '=', True),
        ]))

    def _tp_access_snapshot(self):
        self.ensure_one()
        user = self.user_id.sudo()
        result = {'user': user.id, 'employee': self.id, 'company': self.company_id.id,
                  'department': self.department_id.id, 'job': self.job_id.id,
                  'groups': sorted(user.group_ids.ids), 'active': user.active,
                  'implied_groups': sorted(user.group_ids.all_implied_ids.ids),
                  'companies': sorted(user.company_ids.ids)}
        for model, keys in (
            ('tp.kd.department.role', ['company_id', 'department_id', 'active', 'date_start', 'date_end', 'write_date']),
            ('tp.project.assignment', ['project_id', 'role', 'active', 'write_date']),
            ('tp.project.grant', ['project_id', 'department_id', 'capability', 'active', 'date_end', 'write_date']),
            ('tp.kd.grant', ['project_id', 'department_id', 'domain', 'capability', 'active', 'date_end', 'write_date']),
        ):
            result[model] = self.env[model].sudo().with_context(active_test=False).search(
                [('user_id', '=', user.id)], order='id').read(keys)
        return result

    def _tp_extra_summary(self, snapshot):
        lines = []
        groups = self.env['res.groups'].sudo().browse(snapshot['groups'])
        lines.append('Nhóm trực tiếp: ' + ', '.join(groups.mapped('name')))
        lines.append('Nhóm hiệu lực (gồm kế thừa): ' + ', '.join(self.env['res.groups'].sudo().browse(snapshot['implied_groups']).mapped('name')))
        for model in ('tp.project.assignment', 'tp.project.grant', 'tp.kd.grant'):
            for row in snapshot[model]:
                if row['active']:
                    label = row.get('capability') or row.get('role')
                    kind = 'Phân công' if model == 'tp.project.assignment' else 'Quyền cấp riêng'
                    scope = ''
                    if row.get('domain'):
                        scope = dict(self.env[model]._fields['domain']._description_selection(self.env)).get(row['domain'], 'Nghiệp vụ bổ sung')
                    if row.get('department_id'):
                        scope += (' / ' if scope else '') + row['department_id'][1]
                    lines.append(f"{kind} #{row['id']}: {row['project_id'][1]} — {_ACCESS_LABELS.get(label, 'Quyền nghiệp vụ bổ sung')}"
                                 + (f'; phạm vi {scope}' if scope else '')
                                 + (f"; hết hạn {row['date_end']}" if row.get('date_end') else ''))
        return '\n'.join(lines)

    @api.depends('user_id', 'department_id', 'company_id', 'job_id')
    def _compute_business_role(self):
        for employee in self:
            supported = employee._tp_role_supported()
            employee.tp_role_supported = supported
            head = employee.user_id and self.env['tp.kd.department.role']._is_head(
                user=employee.user_id, company=employee.company_id, department=employee.department_id)
            employee.tp_business_role = ('Trưởng phòng / Trưởng ban KH-KD' if head else 'Nhân viên KH-KD') if supported else 'Chưa triển khai bộ vai trò cho phòng ban'
            if not employee.user_id:
                employee.tp_business_role = 'Chưa cấp vai trò — chưa có tài khoản'
            elif supported and not head and not employee.user_id.has_group('tp_kd_workspace.group_scoped_staff'):
                employee.tp_business_role = 'Chưa cấp vai trò nghiệp vụ KH-KD'
            employee.tp_role_scope = (f'{employee.company_id.name} / {employee.department_id.name}'
                                      + (' — toàn nghiệp vụ theo quyền trưởng phòng' if head else ' — theo phân công và quyền cấp riêng')) if supported else 'Không cấp quyền quản lý thay thế'
            employee.tp_extra_access = employee._tp_extra_summary(employee._tp_access_snapshot()) if employee.user_id and self.env.user.has_group('base.group_system') else False

    def action_change_business_role(self):
        self._tp_account_admin(existing=True)
        if not self._tp_role_supported():
            raise UserError(self.env._('Phòng ban chưa có bộ vai trò nghiệp vụ được triển khai.'))
        return {'type': 'ir.actions.act_window', 'name': 'Bổ nhiệm / hạ quyền KH-KD',
                'res_model': 'tp.hr.role.wizard', 'view_mode': 'form', 'target': 'new',
                'context': {'default_employee_id': self.id}}

    def action_change_position(self):
        self._tp_account_admin()
        return {'type': 'ir.actions.act_window', 'name': 'Đổi chức vụ',
                'res_model': 'tp.hr.role.wizard', 'view_mode': 'form', 'target': 'new',
                'context': {'default_employee_id': self.id, 'default_change_kind': 'job', 'dialog_size': 'medium'}}


class RoleWizard(models.TransientModel):
    _name = 'tp.hr.role.wizard'
    _description = 'Thay đổi vai trò nghiệp vụ nhân viên'

    employee_id = fields.Many2one('hr.employee', required=True, readonly=True, string='Nhân viên')
    company_id = fields.Many2one(related='employee_id.company_id')
    department_id = fields.Many2one(related='employee_id.department_id', string='Phòng ban')
    current_job_id = fields.Many2one(related='employee_id.job_id', string='Chức vụ hiện tại')
    change_kind = fields.Selection([('job', 'Đổi chức vụ trong hồ sơ'), ('role', 'Bổ nhiệm / hạ quyền KH-KD')],
                                   required=True, default='role', string='Bạn muốn thay đổi gì?')
    role_available = fields.Boolean(compute='_compute_role_available')
    account_exists = fields.Boolean(compute='_compute_role_available')
    scope = fields.Char(related='employee_id.tp_role_scope', string='Phạm vi')
    current_role = fields.Char(related='employee_id.tp_business_role', string='Vai trò hiện tại')
    new_role = fields.Selection([('head', 'Bổ nhiệm Trưởng phòng / Trưởng ban KH-KD'),
                                 ('staff', 'Chuyển về Nhân viên KH-KD')], string='Thao tác phân quyền')
    reason = fields.Text(required=True, string='Lý do')
    update_job = fields.Boolean(string='Đổi cả chức vụ ghi trong hồ sơ')
    job_id = fields.Many2one('hr.job', string='Chức vụ mới')
    preview = fields.Text(readonly=True, string='Thêm / thu hồi / giữ lại')
    expected_digest = fields.Char(readonly=True)

    @api.depends('employee_id', 'employee_id.user_id', 'employee_id.department_id')
    def _compute_role_available(self):
        for wizard in self:
            wizard.account_exists = bool(wizard.employee_id.user_id)
            wizard.role_available = bool(wizard.account_exists and wizard.employee_id._tp_role_supported())

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.pop('expected_digest', None)
            vals.pop('preview', None)
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) & {'expected_digest', 'preview'} and self.env.context.get('_tp_role_preview') is not _ROLE_PREVIEW:
            raise AccessError(self.env._('Bản xem trước quyền phải do máy chủ tạo.'))
        return super().write(vals)

    def _action(self):
        return {'type': 'ir.actions.act_window', 'name': 'Đổi chức vụ / Bổ nhiệm và hạ quyền', 'res_model': self._name,
                'res_id': self.id, 'view_mode': 'form', 'target': 'new', 'context': {'dialog_size': 'medium'}}

    def _validate(self):
        self.ensure_one()
        employee = self.employee_id._tp_account_admin(existing=self.change_kind == 'role')
        if self.change_kind == 'role' and employee.version_id != employee.current_version_id:
            raise UserError(self.env._('Phân quyền phải dùng hồ sơ hiện hành, không dùng phiên bản lịch sử hoặc tương lai.'))
        if self.change_kind == 'role' and not employee._tp_role_supported():
            raise UserError(self.env._('Phòng ban chưa triển khai bộ vai trò nghiệp vụ.'))
        if not (self.reason or '').strip():
            raise UserError(self.env._('Vui lòng nhập lý do thay đổi.'))
        if self.change_kind == 'role' and not self.new_role:
            raise UserError(self.env._('Chọn Bổ nhiệm trưởng phòng hoặc Chuyển về nhân viên.'))
        if self.change_kind == 'role' and self.new_role == 'head':
            incumbent = self.env['tp.kd.department.role'].sudo().search([
                ('company_id', '=', employee.company_id.id), ('department_id', '=', employee.department_id.id),
                ('active', '=', True), ('user_id', '!=', employee.user_id.id),
            ], limit=1)
            if incumbent:
                raise UserError(self.env._('Phòng %(department)s đã có trưởng phòng là %(name)s. Vui lòng hạ cấp trưởng phòng hiện tại trước khi bổ nhiệm nhân viên khác.',
                                          department=employee.department_id.name, name=incumbent.user_id.name))
        if self.change_kind == 'job' or self.update_job:
            if not self.job_id or not self.job_id.active or (self.job_id.company_id and self.job_id.company_id != employee.company_id):
                raise UserError(self.env._('Chọn chức vụ đang sử dụng trong đúng công ty.'))
            if self.job_id.department_id and self.job_id.department_id != employee.department_id:
                raise UserError(self.env._('Chức vụ mới thuộc phòng ban khác. Vui lòng chọn chức vụ phù hợp.'))
            if self.change_kind == 'job' and self.job_id == employee.job_id:
                raise UserError(self.env._('Chức vụ mới trùng chức vụ hiện tại. Vui lòng chọn chức vụ khác.'))
        return employee

    def _snapshot(self, employee):
        if self.change_kind == 'job':
            return {'employee': employee.id, 'company': employee.company_id.id,
                    'department': employee.department_id.id, 'job': employee.job_id.id,
                    'version': employee.current_version_id.id}
        snapshot = employee._tp_access_snapshot()
        snapshot['department_heads'] = employee.env['tp.kd.department.role'].sudo().search([
            ('company_id', '=', employee.company_id.id), ('department_id', '=', employee.department_id.id),
            ('active', '=', True),
        ], order='id').read(['user_id', 'write_date'])
        return snapshot

    def _digest(self, snapshot):
        data = [snapshot, self.change_kind, self.new_role, self.reason, self.update_job, self.job_id.id]
        return hashlib.sha256(json.dumps(data, default=str, sort_keys=True).encode()).hexdigest()

    def action_preview(self):
        employee = self._validate()
        snapshot = self._snapshot(employee)
        if self.change_kind == 'job':
            text = self.env._('CHỨC VỤ: %(old)s → %(new)s.\nQuyền sử dụng hệ thống: giữ nguyên.\nLý do: %(reason)s',
                              old=employee.job_id.name or 'Chưa khai báo', new=self.job_id.name, reason=self.reason.strip())
            self.with_context(_tp_role_preview=_ROLE_PREVIEW).write({'expected_digest': self._digest(snapshot), 'preview': text})
            return self._action()
        text = ('THÊM: vai trò trưởng phòng trong phạm vi phòng ban; nhóm nhân viên KH-KD theo phạm vi (không cấp quản trị hệ thống, nhân sự, ký hoặc thanh toán).'
                if self.new_role == 'head' else
                'THU HỒI: vai trò trưởng phòng của phòng ban, bao gồm quyền đọc tài chính, quản lý và tệp phát sinh từ vai trò này.')
        text += '\nTHU HỒI NHÓM: không có (quyền trưởng phòng được tính từ vai trò; giữ các nhóm hiện có).'
        if self.new_role == 'staff':
            text += '\nTHÊM: nhóm nhân viên KH-KD theo phạm vi nếu chưa có; không tự cấp phân công hoặc quyền đọc tài chính.'
        text += '\nGIỮ: quyền cấp riêng được liệt kê dưới đây; không thay toàn bộ nhóm.\n' + employee._tp_extra_summary(snapshot)
        text += '\nChức vụ trong hồ sơ: ' + (f'{employee.job_id.name or "Chưa khai báo"} → {self.job_id.name}' if self.update_job else 'Giữ nguyên; không tự cấp quyền theo chức vụ.')
        self.with_context(_tp_role_preview=_ROLE_PREVIEW).write({'expected_digest': self._digest(snapshot), 'preview': text})
        return self._action()

    def action_apply(self):
        employee = self._validate()
        self.env.cr.execute('SELECT id FROM hr_employee WHERE id=%s FOR UPDATE', [employee.id])
        self.env.cr.execute('SELECT id FROM resource_resource WHERE id=%s FOR UPDATE', [employee.resource_id.id])
        if employee.user_id:
            self.env.cr.execute('SELECT id FROM res_users WHERE id=%s FOR UPDATE', [employee.user_id.id])
        # Serialize provisioning against separate grant/group writers while verifying the snapshot.
        if self.change_kind == 'role':
            self.env.cr.execute('LOCK TABLE tp_kd_department_role, tp_project_assignment, tp_project_grant, '
                                'tp_kd_grant, res_groups_users_rel, res_groups_implied_rel IN SHARE ROW EXCLUSIVE MODE')
        else:
            self.env.cr.execute('SELECT id FROM hr_version WHERE id=%s FOR UPDATE', [employee.current_version_id.id])
        self.env.invalidate_all()
        employee = self._validate()
        before = self._snapshot(employee)
        if not self.expected_digest or self.expected_digest != self._digest(before):
            raise UserError(self.env._('Dữ liệu hoặc lựa chọn đã thay đổi. Hãy bấm Xem trước thay đổi lại.'))
        # Locks stop new writers, but REPEATABLE READ can still hide a writer
        # committed before the locks. Compare with a fresh, read-only snapshot.
        with self.env.registry.cursor() as current_cr:
            current_cr.execute('SET TRANSACTION READ ONLY')
            current_env = api.Environment(current_cr, self.env.uid, dict(self.env.context))
            current = current_env['hr.employee'].browse(employee.id).exists()
            # A new uncommitted employee cannot be changed by another session.
            if current and self._digest(self._snapshot(current)) != self._digest(before):
                raise UserError(self.env._('Thông tin vừa thay đổi từ phiên khác. Hãy xem trước lại thay đổi.'))
        if self.change_kind == 'job':
            with self.env.cr.savepoint():
                old = employee.job_id.name or 'Chưa khai báo'
                employee.write({'job_id': self.job_id.id})
                employee.message_post(body=self.env._('Đổi chức vụ: %(old)s → %(new)s. Người thực hiện: %(actor)s. Lý do: %(reason)s. Quyền sử dụng hệ thống giữ nguyên.',
                                                     old=old, new=self.job_id.name, actor=self.env.user.name, reason=self.reason.strip()))
            return {'type': 'ir.actions.act_window_close'}
        user = employee.user_id
        roles = self.env['tp.kd.department.role'].sudo().search([
            ('user_id', '=', user.id), ('active', '=', True),
        ])
        if roles.filtered(lambda r: r.company_id != employee.company_id or r.department_id != employee.department_id):
            raise UserError(self.env._('Tài khoản còn vai trò trưởng phòng ngoài phòng ban hoặc công ty này. Cần xử lý riêng trước.'))
        if self.new_role == 'staff':
            conflicts = []
            allowed = self.env.ref('tp_kd_workspace.group_scoped_staff').all_implied_ids
            extra_groups = user.group_ids.all_implied_ids - allowed
            privileged = extra_groups.filtered(lambda g: any(
                access.model_id.model.startswith(('tp.', 'project.', 'crm.', 'hr.'))
                and any(op in access.operation for op in 'cud') for access in g.access_ids))
            if privileged:
                conflicts.append('nhóm quản lý bổ sung: ' + ', '.join(privileged.mapped('name')))
            for xmlid in ('tp_core.group_manager', 'project.group_project_manager', 'sales_team.group_sale_manager',
                          'hr.group_hr_manager', 'account.group_account_manager'):
                if user.has_group(xmlid):
                    conflicts.append(self.env.ref(xmlid).name)
            if any(r['active'] and r['role'] != 'reader' for r in before['tp.project.assignment']):
                conflicts.append('phân công điều phối dự án')
            today = str(fields.Date.context_today(self))
            for model in ('tp.project.grant', 'tp.kd.grant'):
                if any(r['active'] and (not r['date_end'] or str(r['date_end']) >= today)
                       and r['capability'] != 'financial_read' for r in before[model]):
                    conflicts.append('quyền quản lý dự án cấp riêng' if model == 'tp.project.grant' else 'quyền nghiệp vụ KH-KD cấp riêng')
            if conflicts:
                raise UserError(self.env._('Chưa thể hạ đầy đủ: còn quyền quản lý cấp riêng (%s). Xử lý nguồn quyền này trước.', ', '.join(conflicts)))
        with self.env.cr.savepoint():
            user.write({'group_ids': [Command.link(self.env.ref('tp_kd_workspace.group_scoped_staff').id)]})
            if self.new_role == 'head':
                if not roles:
                    self.env['tp.kd.department.role'].sudo().create({
                        'user_id': user.id, 'company_id': employee.company_id.id,
                        'department_id': employee.department_id.id, 'reason': self.reason.strip(),
                        'provisioned_by_id': self.env.uid,
                    })
                else:
                    roles.write({'date_start': fields.Date.context_today(self), 'date_end': False, 'reason': self.reason.strip()})
            else:
                roles.write({'active': False, 'reason': self.reason.strip()})
            if self.update_job:
                employee.write({'job_id': self.job_id.id})
            user.write({'tp_lock_revision': user.sudo().tp_lock_revision + 1})
            self.env['tp.kd.department.role']._invalidate_scope()
            after = employee._tp_access_snapshot()
            reason = self.reason.strip()
            self.env['tp.hr.employee.audit']._tp_record([{
                'action': 'role_change',
                'employee_ref': employee.id,
                'employee_name': employee.name,
                'employee_code': employee.tp_employee_code,
                'company_id': employee.company_id.id,
                'reason': reason,
                'snapshot': {'before': before, 'after': after, 'new_role': self.new_role},
            }])
            employee.message_post(body=self.env._('Thay đổi vai trò: %(role)s. Người thực hiện: %(actor)s. Lý do: %(reason)s. Quyền cấp riêng giữ theo bản xem trước.',
                                                 role=dict(self._fields['new_role'].selection)[self.new_role], actor=self.env.user.name, reason=reason))
            # Same existing append-only audit stream; sudo retains uid of the real admin.
            for role in roles or self.env['tp.kd.department.role'].sudo().search([('user_id', '=', user.id), ('active', '=', True)]):
                self.env['tp.kd.department.role.event'].sudo().create({
                    'role_id': role.id, 'actor_id': self.env.uid, 'reason': reason,
                    'before': json.dumps(before, default=str, ensure_ascii=False),
                    'after': json.dumps(after, default=str, ensure_ascii=False),
                })
        return {'type': 'ir.actions.act_window_close'}
