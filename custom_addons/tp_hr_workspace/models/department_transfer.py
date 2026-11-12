"""Immediate, reviewed department moves reuse the HR role command and live grants."""
import hashlib
import json

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, UserError

from .hr_role import _ACCESS_LABELS, _ROLE_PREVIEW

_TRANSFER = object()


class Assignment(models.Model):
    _inherit = 'tp.project.assignment'

    tp_cross_department = fields.Boolean(copy=False, default=False, string='Kiêm nhiệm đã xác nhận')
    tp_cross_department_reason = fields.Text(copy=False, groups='base.group_system')

    def write(self, vals):
        if set(vals) & {'tp_cross_department', 'tp_cross_department_reason'} and not self.env.su:
            raise AccessError(self.env._('Kiêm nhiệm phải được admin xác nhận trong bước chuyển phòng.'))
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and any(v.get('tp_cross_department') for v in vals_list):
            raise AccessError(self.env._('Kiêm nhiệm phải được admin xác nhận.'))
        return super().create(vals_list)


class TransferEmployee(models.Model):
    _inherit = 'hr.employee'

    def action_transfer_department(self):
        self._tp_account_admin(existing=bool(self.user_id))
        if self.version_id != self.current_version_id:
            raise UserError(self.env._('Hãy mở phiên bản hiện hành để chuyển phòng ban.'))
        return {'type': 'ir.actions.act_window', 'res_model': 'tp.hr.role.wizard', 'view_mode': 'form',
                'target': 'new', 'name': 'Chuyển phòng ban',
                'context': {'default_employee_id': self.id, 'default_change_kind': 'transfer'}}

    def write(self, vals):
        if self.env.context.get('_tp_transfer') is not _TRANSFER:
            for employee in self:
                current = employee.current_version_id
                if 'department_id' in vals and employee.version_id == current and current.department_id.id != (vals['department_id'] or False):
                    raise AccessError(self.env._('Dùng Chuyển phòng ban để xem trước và cập nhật quyền cùng hồ sơ.'))
                if vals.get('current_version_id') and self.env['hr.version'].browse(vals['current_version_id']).department_id != current.department_id:
                    raise AccessError(self.env._('Phiên bản khác phòng ban cần luồng Chuyển phòng ban.'))
                if vals.get('current_version_id') and self.env['hr.version'].browse(vals['current_version_id']).employee_id != employee:
                    raise AccessError(self.env._('Không được dùng phiên bản hiện hành của nhân viên khác.'))
                if vals.get('version_id') and self.env['hr.version'].browse(vals['version_id']).employee_id != employee:
                    raise AccessError(self.env._('Không được ghép phiên bản của nhân viên khác.'))
        return super().write(vals)


class TransferVersion(models.Model):
    _inherit = 'hr.version'

    def write(self, vals):
        if self.env.context.get('_tp_transfer') is not _TRANSFER:
            for version in self:
                if 'employee_id' in vals and vals['employee_id'] != version.employee_id.id:
                    target_employee = self.env['hr.employee'].browse(vals['employee_id']).exists()
                    # Native creates the delegated version before its new employee row.
                    if version.employee_id or not target_employee or target_employee.with_context(active_test=False).version_ids:
                        raise AccessError(self.env._('Không được chuyển lịch sử công tác sang nhân viên khác.'))
                current = version.employee_id.current_version_id
                if not current:
                    continue
                if 'company_id' in vals and vals['company_id'] != version.employee_id.company_id.id:
                    raise AccessError(self.env._('Chuyển công ty không thuộc luồng chuyển phòng ban.'))
                changed = 'department_id' in vals and (vals['department_id'] or False) != version.department_id.id
                if changed and version.date_version >= current.date_version:
                    raise AccessError(self.env._('Phòng ban hiện hành hoặc tương lai chỉ đổi qua Chuyển phòng ban.'))
                if set(vals) & {'date_version', 'active', 'employee_id'} and version.department_id != current.department_id:
                    raise AccessError(self.env._('Không được kích hoạt hoặc chuyển lịch sử khác phòng ban thành scope hiện hành.'))
                if set(vals) & {'date_version', 'active', 'employee_id'} and version == current and any(
                    v.active and v != version and v.department_id != current.department_id for v in version.employee_id.version_ids
                ):
                    raise AccessError(self.env._('Không được đổi thứ tự hoặc vô hiệu phiên bản hiện hành làm hồi phục scope phòng ban lịch sử.'))
        return super().write(vals)

    def unlink(self):
        if any(v.employee_id.user_id for v in self):
            raise AccessError(self.env._('Giữ lịch sử công tác của danh tính đã cấp tài khoản; không xóa phiên bản.'))
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('_tp_transfer') is not _TRANSFER:
            for vals in vals_list:
                employee = self.env['hr.employee'].browse(vals.get('employee_id')).exists()
                if employee and vals.get('company_id') and vals['company_id'] != employee.company_id.id:
                    raise AccessError(self.env._('Phiên bản công tác phải thuộc công ty của nhân viên.'))
                current = employee.current_version_id
                if current and (vals.get('department_id') or False) != current.department_id.id:
                    day = fields.Date.to_date(vals.get('date_version') or fields.Date.context_today(self))
                    if day >= current.date_version:
                        raise AccessError(self.env._('Không tạo điều chuyển hiện hành hoặc hẹn ngày ngoài luồng chuyển phòng.'))
        return super().create(vals_list)


class TransferWizard(models.TransientModel):
    _inherit = 'tp.hr.role.wizard'

    change_kind = fields.Selection(selection_add=[('transfer', 'Chuyển phòng ban')], ondelete={'transfer': 'cascade'})
    target_department_id = fields.Many2one('hr.department', string='Phòng ban đích')
    target_role = fields.Selection([('staff', 'Nhân viên'), ('head', 'Trưởng phòng / Trưởng ban KH-KD')], default='staff', string='Vai trò tại phòng đích')
    target_role_supported = fields.Boolean(compute='_compute_target_role')
    keep_cross_department = fields.Boolean(default=False, string='Giữ kiêm nhiệm đã đối chiếu')
    acknowledge_handover = fields.Boolean(default=False, string='Đã xử lý bàn giao')

    def _action(self):
        action = super()._action()
        if self.change_kind == 'transfer':
            action['name'] = 'Chuyển phòng ban'
        return action

    @api.depends('target_department_id')
    def _compute_target_role(self):
        for wizard in self:
            wizard.target_role_supported = bool(wizard.env['crm.team'].sudo().search_count([
                ('kd_department_id', '=', wizard.target_department_id.id), ('company_id', '=', wizard.company_id.id), ('active', '=', True),
            ])) if wizard.target_department_id else False

    def _transfer_validate(self):
        self.ensure_one()
        employee = self.employee_id.with_context(version_id=False)._tp_account_admin(existing=bool(self.employee_id.user_id))
        target = self.target_department_id
        target.check_access('read')
        if not target or not target.active or target.company_id != employee.company_id or target == employee.current_version_id.department_id:
            raise UserError(self.env._('Chọn phòng ban đích đang hoạt động, cùng công ty và khác phòng hiện tại.'))
        if not (self.reason or '').strip() or self.target_role not in ('staff', 'head'):
            raise UserError(self.env._('Chọn vai trò và nhập lý do chuyển phòng.'))
        if employee.version_ids.filtered(lambda v: v.active and v.date_version > fields.Date.context_today(employee)
                                          and v.department_id != target):
            raise UserError(self.env._('Có phiên bản tương lai thuộc phòng khác. Cần HR đối chiếu phiên bản tương lai trước khi chuyển có hiệu lực ngay.'))
        if self.target_role == 'head':
            if not employee.user_id or not self.target_role_supported:
                raise UserError(self.env._('Bổ nhiệm HEAD cần tài khoản và bộ vai trò KH-KD tại phòng đích.'))
            incumbent = self.env['tp.kd.department.role'].sudo().search([
                ('company_id', '=', employee.company_id.id), ('department_id', '=', target.id), ('active', '=', True),
            ], limit=1)
            if incumbent:
                raise UserError(self.env._('Phòng đích đã có trưởng phòng: %s. Không thể bổ nhiệm người thứ hai.', incumbent.user_id.name))
        if self.update_job and (not self.job_id or not self.job_id.active or self.job_id.company_id not in (employee.company_id, self.env['res.company'])
                                or self.job_id.department_id not in (target, self.env['hr.department'])):
            raise UserError(self.env._('Chọn chức vụ đang hoạt động thuộc phòng đích hoặc danh mục chung.'))
        if employee.user_id:
            allowed = self.env.ref('tp_kd_workspace.group_scoped_staff').all_implied_ids
            extras = employee.user_id.sudo().group_ids.all_implied_ids - allowed
            privileged = extras.filtered(lambda g: any(
                a.model_id.model.startswith(('tp.', 'project.', 'crm.', 'hr.', 'account.')) and any(op in a.operation for op in 'cud')
                for a in g.access_ids))
            if privileged:
                raise UserError(self.env._('Còn nhóm quyền quản lý cấp riêng cần xử lý trước khi chuyển: %s.', ', '.join(privileged.mapped('name'))))
            if self.env['tp.kd.department.role'].sudo().search_count([
                ('user_id', '=', employee.user_id.id), ('active', '=', True), ('company_id', '!=', employee.company_id.id),
            ]):
                raise UserError(self.env._('Còn vai trò HEAD khác công ty; cần xử lý scope đó trước.'))
            if employee.user_id.company_ids != employee.company_id:
                raise UserError(self.env._('Tài khoản đa công ty cần đối chiếu quyền toàn công ty trước khi chuyển phòng.'))
        return employee

    def _transfer_sources(self, employee):
        user = employee.user_id
        empty = [('id', '=', 0)]
        scope = [('user_id', '=', user.id), ('active', '=', True), ('company_id', '=', employee.company_id.id)] if user else empty
        assignments = self.env['tp.project.assignment'].sudo().search(scope)
        grants = self.env['tp.project.grant'].sudo().search(scope)
        kd_grants = self.env['tp.kd.grant'].sudo().search(scope)
        roles = self.env['tp.kd.department.role'].sudo().search(scope)
        members = self.env['crm.team.member'].sudo().search(scope)
        return assignments, grants, kd_grants, roles, members

    def _transfer_work(self, employee):
        if not employee.user_id:
            return {}
        user = employee.user_id
        result = {}
        for model, field in [('project.task', 'user_ids'), ('crm.lead', 'user_id'), ('tp.contract.revision', 'business_owner_id'),
                             ('tp.contract.submission', 'assigned_reviewer_id')]:
            records = self.env[model].sudo().with_context(active_test=False).search([(field, 'in', user.ids), ('company_id', '=', employee.company_id.id)])
            if 'active' in records._fields:
                records = records.filtered('active')
            if model == 'project.task':
                records = records.filtered(lambda r: r.state not in ('1_done', '1_canceled'))
            if model == 'crm.lead':
                records = records.filtered(lambda r: not r.stage_id.is_won)
            if model == 'tp.contract.revision':
                records = records.filtered(lambda r: r.review_state in ('draft', 'in_review', 'returned'))
            if model == 'tp.contract.submission':
                records = records.filtered(lambda r: r.outcome == 'pending')
            result[model] = [{'id': r.id, 'name': r.display_name, 'write_date': r.write_date} for r in records]
        for model in ('tp.allocation', 'tp.production', 'tp.acceptance', 'tp.payment.request', 'tp.periodic.plan', 'tp.credential', 'tp.obligation'):
            records = self.env[model].sudo().search([
                '|', ('owner_id', '=', user.id), ('reviewer_id', '=', user.id), ('company_id', '=', employee.company_id.id),
                ('state', 'in', ['draft', 'in_review', 'returned']),
            ])
            result[model] = [{'id': r.id, 'name': r.display_name, 'write_date': r.write_date} for r in records]
        return result

    def _transfer_snapshot(self, employee):
        env = employee.env
        sources = env[self._name].browse(self.id)._transfer_sources(employee)
        snapshot = employee._tp_access_snapshot() if employee.user_id else {'employee': employee.id}
        snapshot.update(version=employee.current_version_id.id, department=employee.current_version_id.department_id.id,
                        job=employee.current_version_id.job_id.id,
                        versions=employee.version_ids.read(['department_id', 'date_version', 'active', 'write_date']),
                        teams=sources[4].read(['crm_team_id', 'active', 'write_date']),
                        target_department=env['hr.department'].browse(self.target_department_id.id).read(['active', 'company_id', 'write_date']),
                        target_teams=env['crm.team'].sudo().search([('kd_department_id', '=', self.target_department_id.id)]).read(['active', 'company_id', 'write_date']),
                        target_job=env['hr.job'].browse(self.job_id.id).read(['active', 'department_id', 'company_id', 'write_date']),
                        work=env[self._name].browse(self.id)._transfer_work(employee),
                        target_heads=env['tp.kd.department.role'].sudo().search([
                            ('company_id', '=', employee.company_id.id), ('department_id', '=', self.target_department_id.id), ('active', '=', True),
                        ]).read(['user_id', 'write_date']))
        return snapshot

    def _transfer_digest(self, snapshot):
        values = [snapshot, self.target_department_id.id, self.target_role, self.reason, self.update_job,
                  self.job_id.id, self.keep_cross_department, self.acknowledge_handover]
        return hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode()).hexdigest()

    def action_preview(self):
        if self.change_kind != 'transfer':
            return super().action_preview()
        employee = self._transfer_validate()
        snapshot = self._transfer_snapshot(employee)
        sources = self._transfer_sources(employee)
        text = f'PHÒNG BAN: {employee.current_version_id.department_id.name or "Chưa khai báo"} → {self.target_department_id.name}.\n'
        text += f'Tài khoản: {employee.user_id.login if employee.user_id else "Chưa có tài khoản — không tự tạo"}.\n'
        text += 'THU HỒI: mọi HEAD cũ, quyền quản lý/tiền/tệp từ HEAD; không giữ chức trưởng phòng tự động.\n'
        role_label = dict(self._fields['target_role']._description_selection(self.env))[self.target_role]
        text += f'Bỏ workspace chính: {employee.current_version_id.department_id.name or "Chưa khai báo"}; thêm workspace chính: {self.target_department_id.name}.\n'
        text += f'Vai trò tại phòng đích: {role_label}. '
        text += ('KH-KD theo phân công; không tự cấp tiền/toàn dự án.\n' if self.target_role_supported else 'Đang phát triển; không cấp bộ quyền KH-KD.\n')
        text += ('GIỮ KIÊM NHIỆM đã chọn rõ: ' if self.keep_cross_department else 'KẾT THÚC (giữ bản ghi lịch sử): ')
        for label, records in zip(('Phân công dự án', 'Quyền dự án', 'Quyền nghiệp vụ', 'Thành viên đội CRM'), sources[:3] + sources[4:]):
            details = []
            for record in records:
                scope = record.crm_team_id.display_name if record._name == 'crm.team.member' else record.project_id.display_name
                capability = _ACCESS_LABELS.get(record.capability, record.capability) if 'capability' in record._fields else ''
                details.append(f'#{record.id} {scope}' + (f' — {capability}' if capability else ''))
            text += f'\n{label}: ' + ('; '.join(details) or 'Không có')
        text += '\nHEAD thu hồi: ' + ', '.join(f'#{r.id} {r.department_id.name}' for r in sources[3])
        if employee.user_id:
            text += '\n' + employee._tp_extra_summary(snapshot)
        text += '\nCẦN BÀN GIAO (giữ nguyên người phụ trách và người duyệt):'
        pending = []
        labels = {'project.task': 'Công việc', 'crm.lead': 'Hồ sơ dự án', 'tp.contract.revision': 'Phiên bản hợp đồng',
                  'tp.contract.submission': 'Vòng duyệt hợp đồng', 'tp.allocation': 'Giao khoán', 'tp.production': 'Sản lượng',
                  'tp.acceptance': 'Nghiệm thu', 'tp.payment.request': 'Đề nghị thanh toán', 'tp.periodic.plan': 'Kế hoạch',
                  'tp.credential': 'Hồ sơ năng lực', 'tp.obligation': 'Nghĩa vụ'}
        for model, records in snapshot['work'].items():
            if records:
                pending.append(labels[model] + ': ' + '; '.join(f'#{r["id"]} {r["name"]}' for r in records))
        text += '\n' + ('\n'.join(pending) or 'Không có công việc đang chờ.')
        old_job = employee.current_version_id.job_id
        text += '\nChức vụ: ' + (self.job_id.name if self.update_job else ('Bỏ chức vụ thuộc phòng cũ' if old_job.department_id and old_job.department_id != self.target_department_id else 'Giữ chức vụ chung'))
        text += '\nPhiên đăng nhập hiện có sẽ kết thúc; đăng nhập lại để nhận menu/phòng mới. Lý do: ' + self.reason.strip()
        self.with_context(_tp_role_preview=_ROLE_PREVIEW).write({'preview': text, 'expected_digest': self._transfer_digest(snapshot)})
        return self._action()

    def action_apply(self):
        if self.change_kind != 'transfer':
            return super().action_apply()
        employee = self._transfer_validate()
        self.env.cr.execute('SELECT pg_advisory_xact_lock(761101, %s)', [employee.company_id.id])
        self.env.cr.execute('SELECT id FROM hr_employee WHERE id=%s FOR UPDATE', [employee.id])
        self.env.cr.execute('SELECT id FROM resource_resource WHERE id=%s FOR UPDATE', [employee.resource_id.id])
        if employee.user_id:
            self.env.cr.execute('SELECT id FROM res_users WHERE id=%s FOR UPDATE', [employee.user_id.id])
        self.env.cr.execute('LOCK TABLE hr_version, tp_kd_department_role, tp_project_assignment, tp_project_grant, '
                            'tp_kd_grant, crm_team_member, crm_team, hr_department, hr_job, res_groups_users_rel, res_groups_implied_rel, '
                            'project_task, crm_lead, tp_contract_revision, tp_contract_submission, tp_allocation, tp_production, '
                            'tp_acceptance, tp_payment_request, tp_periodic_plan, tp_credential, tp_obligation IN SHARE ROW EXCLUSIVE MODE')
        self.env.invalidate_all()
        employee = self._transfer_validate()
        before = self._transfer_snapshot(employee)
        if not self.expected_digest or self.expected_digest != self._transfer_digest(before):
            raise UserError(self.env._('Dữ liệu/quyền/lựa chọn đã thay đổi. Hãy xem trước chuyển phòng lại.'))
        with self.env.registry.cursor() as current_cr:
            current_cr.execute('SET TRANSACTION READ ONLY')
            current_env = api.Environment(current_cr, self.env.uid, dict(self.env.context))
            current = current_env['hr.employee'].browse(employee.id).exists()
            if current and self._transfer_digest(self._transfer_snapshot(current)) != self._transfer_digest(before):
                raise UserError(self.env._('Phiên khác vừa cập nhật dữ liệu. Hãy xem trước lại.'))
        if any(before['work'].values()) and not self.acknowledge_handover:
            raise UserError(self.env._('Còn công việc phụ trách. Xử lý bàn giao bên ngoài hoặc xác nhận đã xử lý các mục trong bản xem trước.'))
        assignments, grants, kd_grants, roles, members = self._transfer_sources(employee)
        with self.env.cr.savepoint():
            reason = self.reason.strip()
            roles.write({'active': False, 'reason': reason})
            if self.keep_cross_department:
                assignments.write({'tp_cross_department': True, 'tp_cross_department_reason': reason})
            else:
                assignments.write({'active': False})
                grants.write({'active': False})
                kd_grants.write({'active': False})
                members.write({'active': False})
            # Create today's native version; an existing version today is updated in place.
            current = employee.current_version_id
            job = self.job_id if self.update_job else current.job_id
            if job.department_id and job.department_id != self.target_department_id:
                job = self.env['hr.job']
            values = {'department_id': self.target_department_id.id, 'job_id': job.id}
            employee = employee.with_context(_tp_transfer=_TRANSFER, version_id=False)
            today = fields.Date.context_today(employee)
            if current.date_version == today:
                current.with_context(_tp_transfer=_TRANSFER).write(values)
            else:
                employee.create_version({'date_version': today, **values})
            employee._compute_current_version_id()
            user = employee.user_id
            if user:
                scoped = self.env.ref('tp_kd_workspace.group_scoped_staff')
                if self.target_role_supported or (self.keep_cross_department and assignments):
                    user.sudo().write({'group_ids': [Command.link(scoped.id)]})
                else:
                    user.sudo().write({'group_ids': [Command.unlink(scoped.id)]})
                if self.target_role == 'head':
                    self.env['tp.kd.department.role'].sudo().create({'user_id': user.id, 'company_id': employee.company_id.id,
                        'department_id': self.target_department_id.id, 'reason': reason, 'provisioned_by_id': self.env.uid})
                user.sudo().write({'tp_lock_revision': user.sudo().tp_lock_revision + 1})
            self.env['tp.kd.department.role']._invalidate_scope()
            self.env.transaction.invalidate_ormcache()
            employee.message_post(body=json.dumps({'action': 'department_transfer', 'actor': self.env.uid,
                'reason': reason, 'preview': self.preview, 'before': before, 'after': self._transfer_snapshot(employee)}, default=str, ensure_ascii=False))
            self.with_context(_tp_role_preview=_ROLE_PREVIEW).write({'expected_digest': False})
        return {'type': 'ir.actions.act_window_close'}
