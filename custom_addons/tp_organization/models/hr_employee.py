import re

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .roster_parser import employee_code, source_code

_ROSTER_WRITE = object()
# Internal permissions (HR-CORRECTION-008). Sentinel objects cannot be sent
# through JSON-RPC, so a client context can never unlock these paths.
_TP_DELETE = object()
_TP_CODE_CORRECTION = object()

# TP codes issued by the manual sequence live in one numeric band; roster
# codes TP{10000 + source} share it (source 60 -> TP10060).
CODE_MIN, CODE_MAX = 10001, 19999
_CODE_LOCK = 761102
_CODE_RE = re.compile(r'TP([1-9][0-9]*)')
_SIDECAR_REFERENCES = {('hr.version', 'employee_id'), ('hr.employee', 'resource_id'), ('hr.version', 'resource_id')}
_USER_MESSAGE_TYPES = ('comment', 'email', 'email_outgoing')


def code_number(code):
    """Return the integer of a ``TP<n>`` code, or ``None`` for other values."""
    match = _CODE_RE.fullmatch(code or '')
    return int(match.group(1)) if match else None


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    tp_employee_code = fields.Char(string='TP Employee Code', copy=False, index=True, tracking=True)
    tp_source_code = fields.Char(string='Source Code', copy=False, index=True, groups='hr.group_hr_user')
    tp_source_department = fields.Char(string='Source Department', groups='hr.group_hr_user')
    tp_source_title = fields.Char(string='Source Title', groups='hr.group_hr_user')
    tp_source_snapshot = fields.Json(string='Source Snapshot', copy=False, groups='hr.group_hr_user')
    tp_import_batch_id = fields.Many2one('tp.hr.import.batch', string='Import Batch', copy=False, ondelete='restrict', groups='hr.group_hr_user')

    _tp_code_unique = models.Constraint('UNIQUE(company_id, tp_employee_code)', 'Employee TP code is already used, including archived records.')
    _tp_source_unique = models.Constraint('UNIQUE(company_id, tp_source_code)', 'Source identity is already used in this company.')

    @api.constrains('tp_employee_code')
    def _check_tp_employee_code(self):
        for employee in self:
            if employee.tp_employee_code and (code_number(employee.tp_employee_code) or 0) < CODE_MIN:
                raise ValidationError(self.env._('Mã nhân viên phải có dạng TP10001 (TP và số từ 10001).'))

    # ------------------------------------------------------------------
    # Employee code allocation (TP + number, never employee.id)
    # ------------------------------------------------------------------
    @api.model
    def _tp_code_sequence(self):
        return self.env.ref('tp_organization.seq_employee_code').sudo()

    @api.model
    def _tp_code_floor(self):
        """Highest valid issued number of the TP band + 1.

        Counted numerically (never by string order) over every company,
        archived employees and codes recorded by deletions or corrections, so
        a deleted or archived code is never issued again.
        """
        self.env.cr.execute("""
            SELECT max(n) FROM (
                SELECT substring(tp_employee_code FROM 3)::bigint AS n FROM hr_employee
                 WHERE tp_employee_code ~ '^TP[1-9][0-9]{4}$'
                UNION ALL
                SELECT substring(code FROM 3)::bigint FROM (
                    SELECT employee_code AS code FROM tp_hr_employee_audit
                    UNION ALL SELECT new_code FROM tp_hr_employee_audit) audit_codes
                 WHERE code ~ '^TP[1-9][0-9]{4}$'
            ) codes WHERE n BETWEEN %s AND %s
        """, [CODE_MIN, CODE_MAX])
        return max((self.env.cr.fetchone()[0] or 0) + 1, CODE_MIN)

    @api.model
    def _tp_sequence_next(self, sequence):
        """Next value the PostgreSQL sequence would return, without consuming it."""
        if sequence.implementation != 'standard':
            return sequence.number_next
        self.env.cr.execute('SELECT last_value, is_called FROM ir_sequence_%03d' % sequence.id)
        last_value, is_called = self.env.cr.fetchone()
        return last_value + sequence.number_increment if is_called else last_value

    @api.model
    def _tp_bump_code_sequence(self, number):
        """Move the code sequence forward to ``number`` (never backward)."""
        sequence = self._tp_code_sequence()
        if self._tp_sequence_next(sequence) < number:
            if sequence.implementation == 'standard':
                self.env.cr.execute('SELECT setval(%s, %s, false)', ['ir_sequence_%03d' % sequence.id, number])
            else:
                sequence.write({'number_next': number})

    @api.model
    def _tp_reset_code_sequence(self, number):
        """Set the next sequence value to ``number`` (used when it left the TP band)."""
        sequence = self._tp_code_sequence()
        if sequence.implementation == 'standard':
            self.env.cr.execute('SELECT setval(%s, %s, false)', ['ir_sequence_%03d' % sequence.id, number])
            self.env.cr.execute('UPDATE ir_sequence SET number_next=%s WHERE id=%s', [number, sequence.id])
            sequence.invalidate_recordset(['number_next'])
        else:
            sequence.write({'number_next': number})

    @api.model
    def _tp_allocate_code(self, company_id):
        """Return the next free ``TP<n>`` code for a manual employee.

        One transaction lock serializes manual creation and roster import; the
        PostgreSQL sequence is not transactional, so two concurrent requests
        never receive the same number. The floor protects against a sequence
        that is behind the issued codes; a value outside the band (such as the
        former start at 20000) is reset to the floor.
        """
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [_CODE_LOCK])
        floor = self._tp_code_floor()
        if floor > CODE_MAX:
            raise UserError(self.env._('Đã dùng hết dải mã TP%(min)s–TP%(max)s. Liên hệ quản trị trước khi tạo hồ sơ mới.', min=CODE_MIN, max=CODE_MAX))
        sequence = self._tp_code_sequence()
        Employee = self.sudo().with_context(active_test=False)

        def take():
            return int(sequence.next_by_id()[len(sequence.prefix or ''):])

        number = take()
        if number < floor or number > CODE_MAX:
            self._tp_reset_code_sequence(floor)
            number = take()
        while Employee.search_count([('company_id', '=', company_id), ('tp_employee_code', '=', f'TP{number}')]):
            number = take()
        if number > CODE_MAX:
            raise UserError(self.env._('Đã dùng hết dải mã TP%(min)s–TP%(max)s. Liên hệ quản trị trước khi tạo hồ sơ mới.', min=CODE_MIN, max=CODE_MAX))
        return f'TP{number}'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if set(vals) & {'tp_source_code', 'tp_source_department', 'tp_source_title', 'tp_source_snapshot', 'tp_import_batch_id'} and self.env.context.get('_tp_roster_write') is not _ROSTER_WRITE:
                raise AccessError(self.env._('Thông tin nguồn chỉ được ghi qua nhập danh sách nhân sự đã rà soát.'))
            company_id = vals.get('company_id', self.env.company.id)
            # One PostgreSQL advisory transaction lock also serializes import/manual creation.
            self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [761101, company_id])
            if not vals.get('tp_employee_code'):
                vals['tp_employee_code'] = self._tp_allocate_code(company_id)
        employees = super().create(vals_list)
        explicit = [code_number(code) for code in employees.mapped('tp_employee_code')]
        explicit = [number for number in explicit if number and number <= CODE_MAX]
        if explicit:
            # Imported or explicit codes raise the high-water mark so that a later
            # manual creation (even from a stale snapshot) never reuses them.
            self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [_CODE_LOCK])
            self._tp_bump_code_sequence(max(explicit) + 1)
        return employees

    def write(self, vals):
        if set(vals) & {'name', 'department_id', 'active'}:
            for company_id in sorted(set(self.mapped('company_id').ids)):
                self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [761101, company_id])
            self.invalidate_recordset()
        if set(vals) & {'tp_source_code', 'tp_source_department', 'tp_source_title', 'tp_source_snapshot', 'tp_import_batch_id'} and self.env.context.get('_tp_roster_write') is not _ROSTER_WRITE:
            raise AccessError(self.env._('Thông tin nguồn chỉ được cập nhật qua nhập danh sách nhân sự đã rà soát.'))
        if not self.env.su and 'active' in vals and not self.env.user.has_group('hr.group_hr_manager'):
            raise AccessError(self.env._('Chỉ quản lý nhân sự được lưu trữ hoặc khôi phục hồ sơ nhân viên.'))
        # An issued code changes only through the audited correction (HR-CORRECTION-008).
        correction = self.env.su and self.env.context.get('_tp_code_correction') is _TP_CODE_CORRECTION
        for key in ('tp_employee_code', 'tp_source_code'):
            if key in vals and not (correction and key == 'tp_employee_code'):
                if any(employee[key] and vals[key] != employee[key] for employee in self.sudo()):
                    raise UserError(self.env._('Mã nhân viên/mã nguồn đã cấp không được sửa trực tiếp. Việc sửa mã phải qua migration có đối chiếu và nhật ký.'))
        return super().write(vals)

    @api.constrains('tp_source_code', 'tp_employee_code')
    def _check_tp_source_code(self):
        for employee in self:
            if employee.tp_source_code:
                try:
                    valid = source_code(employee.tp_source_code) == employee.tp_source_code and employee_code(employee.tp_source_code) == employee.tp_employee_code
                except ValueError:
                    valid = False
                if not valid:
                    raise ValidationError(self.env._('Mã nguồn phải là số nguyên dương và khớp với mã nhân viên TP.'))

    # ------------------------------------------------------------------
    # Deleting a mistaken entry (admin) vs archiving (everything else)
    # ------------------------------------------------------------------
    def _tp_reference_counts(self):
        """Stored references to these employees from other records.

        Returns ``{employee_id: [(label, count), ...]}``. Records created with
        the employee itself (its versions and resource) are not references;
        wizard rows (transient models) are ignored.
        """
        result = {employee_id: [] for employee_id in self.ids}
        if not self.ids:
            return result
        cr = self.env.cr
        Fields = self.env['ir.model.fields'].sudo()
        targets = {'hr.employee': ('employee', self.ids)}
        resource_ids = self.sudo().with_context(active_test=False).mapped('resource_id').ids
        if resource_ids:
            targets['resource.resource'] = ('resource', resource_ids)
        resource_owner = {employee.resource_id.id: employee.id for employee in self.sudo().with_context(active_test=False)}
        own_relations = {field.relation for field in self._fields.values() if field.type == 'many2many' and field.store}
        for target, (kind, ids) in targets.items():
            for field_info in Fields.search([('relation', '=', target), ('ttype', 'in', ('many2one', 'many2many')), ('store', '=', True)]):
                model = self.env.get(field_info.model)
                field = model is not None and model._fields.get(field_info.name)
                if not field or not field.store or model._transient or model._abstract or not model._auto:
                    continue
                if (field_info.model, field_info.name) in _SIDECAR_REFERENCES:
                    continue
                if field.type == 'many2one':
                    query = f'SELECT "{field.name}", count(*) FROM "{model._table}" WHERE "{field.name}" IN %s'
                    if field_info.model == 'hr.employee':
                        query += ' AND id NOT IN %s'
                        cr.execute(query + ' GROUP BY 1', [tuple(ids), tuple(self.ids)])
                    else:
                        cr.execute(query + ' GROUP BY 1', [tuple(ids)])
                else:
                    if field.relation in own_relations or not field.relation:
                        continue
                    cr.execute(f'SELECT "{field.column2}", count(*) FROM "{field.relation}" WHERE "{field.column2}" IN %s GROUP BY 1', [tuple(ids)])
                label = f'{self.env["ir.model"]._get(field_info.model).name} – {field_info.field_description}'
                for record_id, count in cr.fetchall():
                    employee_id = record_id if kind == 'employee' else resource_owner.get(record_id)
                    if employee_id in result:
                        result[employee_id].append((label, count))
        return result

    def _tp_deletion_blockers(self):
        """Return ``{employee_id: [reason, ...]}`` for records that are not mistaken entries.

        Only an unused manual entry may be deleted: created by hand (not from
        the roster), without a personal account, business role or reference
        from other records, without real work history (later versions),
        posted notes/emails, planned activities or attached documents.
        """
        employees = self.sudo().with_context(active_test=False)
        blockers = {employee.id: [] for employee in employees}
        if not employees:
            return blockers
        cr = self.env.cr
        ids = tuple(employees.ids)
        for employee in employees:
            reasons = blockers[employee.id]
            if employee.tp_source_code or employee.tp_import_batch_id:
                reasons.append(self.env._('Hồ sơ được nhập từ danh sách nhân sự (mã nguồn %(roster_code)s).', roster_code=employee.tp_source_code or '-'))
            if employee.user_id:
                reasons.append(self.env._('Đã cấp tài khoản cá nhân %(login)s.', login=employee.user_id.login))
            if len(employee.version_ids) > 1:
                reasons.append(self.env._('Đã có lịch sử công tác (%(count)s phiên bản hồ sơ).', count=len(employee.version_ids)))
        cr.execute("SELECT res_id, count(*) FROM mail_message WHERE model='hr.employee' AND res_id IN %s AND message_type IN %s GROUP BY 1", [ids, _USER_MESSAGE_TYPES])
        for employee_id, count in cr.fetchall():
            blockers[employee_id].append(self.env._('Có %(count)s ghi chú hoặc trao đổi trong lịch sử hồ sơ.', count=count))
        cr.execute("SELECT res_id, count(*) FROM mail_activity WHERE res_model='hr.employee' AND res_id IN %s GROUP BY 1", [ids])
        for employee_id, count in cr.fetchall():
            blockers[employee_id].append(self.env._('Có %(count)s hoạt động đang lên lịch.', count=count))
        cr.execute("SELECT res_id, count(*) FROM ir_attachment WHERE res_model='hr.employee' AND res_id IN %s AND res_field IS NULL GROUP BY 1", [ids])
        for employee_id, count in cr.fetchall():
            blockers[employee_id].append(self.env._('Có %(count)s tài liệu đính kèm.', count=count))
        for employee_id, references in employees._tp_reference_counts().items():
            for label, count in references:
                blockers[employee_id].append(self.env._('Đang được dùng trong %(label)s (%(count)s bản ghi).', label=label, count=count))
        return {employee_id: reasons for employee_id, reasons in blockers.items() if reasons}

    def _tp_check_delete_admin(self):
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(self.env._('Chỉ quản trị hệ thống được xóa hồ sơ nhập nhầm. Hãy lưu trữ hồ sơ nếu cần ẩn khỏi danh sách.'))
        foreign = self.sudo().with_context(active_test=False).filtered(lambda employee: employee.company_id != self.env.company)
        if foreign:
            raise AccessError(self.env._('Chỉ xóa hồ sơ thuộc công ty đang làm việc (%(company)s).', company=self.env.company.name))

    def _tp_format_blockers(self, blockers):
        lines = []
        for employee in self.sudo().with_context(active_test=False):
            if employee.id in blockers:
                lines.append(f'• {employee.name} ({employee.tp_employee_code or "-"}): ' + ' '.join(blockers[employee.id]))
        return self.env._('Không xóa được vì có hồ sơ đang được sử dụng. Không hồ sơ nào bị xóa.\n%(details)s\nHãy dùng "Lưu trữ nhân viên" để giữ lịch sử.', details='\n'.join(lines))

    def _tp_delete_mistaken(self, reason):
        """Permanently delete unused manual entries, all or nothing, with an audit."""
        self._tp_check_delete_admin()
        reason = (reason or '').strip()
        if not reason:
            raise UserError(self.env._('Vui lòng nhập lý do xóa hồ sơ nhập nhầm.'))
        employees = self.with_context(active_test=False)
        for company_id in sorted(set(employees.sudo().mapped('company_id').ids)):
            self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [761101, company_id])
        self.env.cr.execute('SELECT id FROM hr_employee WHERE id IN %s FOR UPDATE', [tuple(employees.ids)])
        employees.invalidate_recordset()
        blockers = employees._tp_deletion_blockers()
        if blockers:
            raise UserError(employees._tp_format_blockers(blockers))
        audit_vals = []
        for employee in employees.sudo():
            audit_vals.append({
                'action': 'delete',
                'employee_ref': employee.id,
                'employee_name': employee.name,
                'employee_code': employee.tp_employee_code,
                'company_id': employee.company_id.id,
                'reason': reason,
                'snapshot': {
                    'department': employee.department_id.display_name or '',
                    'job': employee.job_id.display_name or '',
                    'work_contact_id': employee.work_contact_id.id,
                    'resource_id': employee.resource_id.id,
                    'version_ids': employee.version_ids.ids,
                    'create_date': str(employee.create_date),
                    'create_uid': employee.create_uid.id,
                },
            })
        self.env['tp.hr.employee.audit']._tp_record(audit_vals)
        employees.with_context(_tp_employee_delete=_TP_DELETE).unlink()
        return len(audit_vals)

    def unlink(self):
        if self.env.context.get('_tp_employee_delete') is not _TP_DELETE:
            raise UserError(self.env._('Không xóa trực tiếp hồ sơ nhân viên. Quản trị dùng "Xóa hồ sơ nhập nhầm" để kiểm tra điều kiện; hồ sơ đã sử dụng thì lưu trữ để giữ lịch sử.'))
        blockers = self._tp_deletion_blockers()
        if blockers:
            raise UserError(self._tp_format_blockers(blockers))
        return super().unlink()

    @api.model
    def load_demo_data(self):
        raise UserError(self.env._('TANPHAT ONE không nạp dữ liệu nhân sự mẫu. Dùng chức năng nhập danh sách nhân sự có kiểm soát.'))


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    tp_employee_code = fields.Char(string='TP Employee Code', readonly=True)


class HrVersion(models.Model):
    _inherit = 'hr.version'

    def write(self, vals):
        if 'department_id' in vals:
            for company_id in sorted(set(self.mapped('company_id').ids)):
                self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [761101, company_id])
        return super().write(vals)

    tp_personal_defaults_confirmed = fields.Boolean(string='Đã xác nhận tình trạng gia đình', default=False, groups='hr.group_hr_user')
    tp_wage_confirmed = fields.Boolean(string='Đã xác nhận mức lương', default=False, groups='hr.group_hr_manager')


class ResourceResource(models.Model):
    _inherit = 'resource.resource'

    def write(self, vals):
        if set(vals) & {'active', 'name'}:
            employees = self.env['hr.employee'].sudo().with_context(active_test=False).search([('resource_id', 'in', self.ids)])
            if employees and 'active' in vals and not self.env.su and not self.env.user.has_group('hr.group_hr_manager'):
                raise AccessError(self.env._('Chỉ quản lý nhân sự được lưu trữ hoặc khôi phục hồ sơ nhân viên.'))
            for company_id in sorted(set(employees.mapped('company_id').ids)):
                self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [761101, company_id])
        return super().write(vals)
