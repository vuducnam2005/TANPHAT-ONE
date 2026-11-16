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

    @api.model
    def _tp_check_code_not_retired(self, code):
        """A code of a deleted or corrected profile is never issued again."""
        self.env.cr.execute('SELECT 1 FROM tp_hr_employee_audit WHERE employee_code=%s LIMIT 1', [code])
        if self.env.cr.fetchone():
            raise ValidationError(self.env._('Mã %(code)s thuộc hồ sơ đã xóa hoặc đã đổi mã; mã TP không được cấp lại.', code=code))

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
            else:
                self._tp_check_code_not_retired(vals['tp_employee_code'])
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
    # References (kept for the 20.0.2.1.0 migration report)
    # ------------------------------------------------------------------
    def _tp_reference_counts(self):
        """Stored references to these employees from other records.

        Returns ``{employee_id: [(label, count), ...]}``; the employee's own
        versions/resource and transient rows are not references.
        """
        result = {employee_id: [] for employee_id in self.ids}
        if not self.ids:
            return result
        doomed = self._tp_doomed()
        targets = {model_name: list(rows) for model_name, rows in doomed.items() if rows}
        for model_name, field_name, counts in self._tp_stored_references(targets, self._tp_doomed_exclusions(doomed)):
            for target, rows in counts.items():
                for record_id, count in rows.items():
                    result[doomed[target][record_id]].append((self._tp_label(model_name, field_name), count))
        return result

    def unlink(self):
        # HR-DELETE-010: only the audited permanent deletion (admin password
        # re-verified, plan checked under lock) passes this Python sentinel.
        if self.env.context.get('_tp_employee_delete') is not _TP_DELETE:
            raise UserError(self.env._('Không xóa trực tiếp hồ sơ nhân viên. Quản trị dùng "Xóa vĩnh viễn nhân viên" (xác minh lại mật khẩu) hoặc "Lưu trữ" để giữ lịch sử.'))
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
