import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .code_format import (
    CODE_MAX,
    CODE_MIN,
    LEGACY_OFFSET,
    code_aliases,
    code_number,
    format_code,
    identity_number,
    legacy_number,
)
from .roster_parser import employee_code, source_code

_ROSTER_WRITE = object()
# Internal permissions (HR-CORRECTION-008). Sentinel objects cannot be sent
# through JSON-RPC, so a client context can never unlock these paths.
_TP_DELETE = object()
_TP_CODE_CORRECTION = object()

# HR-EMPLOYEE-CODE-003: codes are TP + exactly three digits (TP001-TP999).
# Manual creation and roster import share one number space; roster codes are
# the verified source number (source 60 -> TP060). ``CODE_MIN``, ``CODE_MAX``
# and ``code_number`` stay importable here for the historical migrations.
_CODE_LOCK = 761102
_COMPANY_LOCK = 761101
CODE_FORMAT_REQUEST = 'HR-EMPLOYEE-CODE-003'


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
            if employee.tp_employee_code and code_number(employee.tp_employee_code) is None:
                raise ValidationError(self.env._('Mã nhân viên phải có dạng TP + đúng 3 chữ số (TP001–TP999).'))

    # ------------------------------------------------------------------
    # Employee code allocation (TP + number, never employee.id)
    # ------------------------------------------------------------------
    @api.model
    def _tp_code_sequence(self):
        return self.env.ref('tp_organization.seq_employee_code').sudo()

    @api.model
    def _tp_code_floor(self):
        """Highest issued code number + 1 (may exceed ``CODE_MAX`` when exhausted).

        Counted numerically over every company, archived employees and codes
        recorded by deletions or corrections, in the current form (TPnnn) and
        the former form (TP1nnnn = nnnn - 10000), so a deleted, archived or
        converted number is never issued again.
        """
        self.env.cr.execute("""
            SELECT max(n) FROM (
                SELECT CASE WHEN code ~ '^TP[0-9]{3}$' THEN substring(code FROM 3)::int
                            WHEN code ~ '^TP1[0-9]{4}$' THEN substring(code FROM 3)::int - %s END AS n
                  FROM (SELECT tp_employee_code AS code FROM hr_employee
                        UNION ALL SELECT employee_code FROM tp_hr_employee_audit
                        UNION ALL SELECT new_code FROM tp_hr_employee_audit) all_codes
            ) numbers WHERE n BETWEEN %s AND %s
        """, [LEGACY_OFFSET, CODE_MIN, CODE_MAX])
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

    def _tp_code_exhausted(self):
        return UserError(self.env._('Đã dùng hết dải mã %(min)s–%(max)s. Không tự cấp mã 4 chữ số; liên hệ quản trị trước khi tạo hồ sơ mới.',
                                    min=format_code(CODE_MIN), max=format_code(CODE_MAX)))

    @api.model
    def _tp_allocate_code(self, company_id):
        """Return the next free ``TPnnn`` code for a manual employee.

        One transaction lock serializes manual creation and roster import; the
        PostgreSQL sequence is not transactional, so two concurrent requests
        never receive the same number. The floor protects against a sequence
        that is behind the issued codes; a value outside TP001-TP999 (such as
        the former TP1nnnn band) is reset to the floor. When the range is used
        up the creation stops with a message instead of issuing TP1000.
        """
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [_CODE_LOCK])
        floor = self._tp_code_floor()
        if floor > CODE_MAX:
            raise self._tp_code_exhausted()
        sequence = self._tp_code_sequence()
        Employee = self.sudo().with_context(active_test=False)

        def take():
            return int(sequence.next_by_id()[len(sequence.prefix or ''):])

        number = take()
        if not floor <= number <= CODE_MAX:
            self._tp_reset_code_sequence(floor)
            number = take()
        while number <= CODE_MAX and (
                Employee.search_count([('company_id', '=', company_id), ('tp_employee_code', 'in', code_aliases(format_code(number)))])
                or self._tp_code_retired(format_code(number))):
            number = take()
        if number > CODE_MAX:
            raise self._tp_code_exhausted()
        return format_code(number)

    @api.model
    def _tp_code_retired(self, code, employee_ref=None):
        """Whether the identity of ``code`` belongs to a deleted or corrected profile.

        Both spellings count (TP070 is retired by a deleted TP10070). A format
        conversion that kept the same number (TP10060 -> TP060) does not retire
        it, and neither do the audit rows of ``employee_ref`` itself.
        """
        number = identity_number(code)
        if number is None:
            return False
        self.env.cr.execute('SELECT employee_ref, action, new_code FROM tp_hr_employee_audit WHERE employee_code IN %s',
                            [tuple(code_aliases(code))])
        return any(ref != employee_ref and not (action == 'code_correction' and identity_number(new_code) == number)
                   for ref, action, new_code in self.env.cr.fetchall())

    @api.model
    def _tp_check_code_not_retired(self, code):
        """A code of a deleted or corrected profile is never issued again."""
        if self._tp_code_retired(code):
            raise ValidationError(self.env._('Mã %(code)s thuộc hồ sơ đã xóa hoặc đã đổi mã; mã TP không được cấp lại.', code=code))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if set(vals) & {'tp_source_code', 'tp_source_department', 'tp_source_title', 'tp_source_snapshot', 'tp_import_batch_id'} and self.env.context.get('_tp_roster_write') is not _ROSTER_WRITE:
                raise AccessError(self.env._('Thông tin nguồn chỉ được ghi qua nhập danh sách nhân sự đã rà soát.'))
            company_id = vals.get('company_id', self.env.company.id)
            # One PostgreSQL advisory transaction lock also serializes import/manual creation.
            self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [_COMPANY_LOCK, company_id])
            if not vals.get('tp_employee_code'):
                vals['tp_employee_code'] = self._tp_allocate_code(company_id)
            else:
                self._tp_check_code_not_retired(vals['tp_employee_code'])
        employees = super().create(vals_list)
        explicit = [number for number in map(code_number, employees.mapped('tp_employee_code')) if number]
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
    # Code format conversion TP1nnnn -> TPnnn (HR-EMPLOYEE-CODE-003)
    # ------------------------------------------------------------------
    @api.model
    def _tp_code_format_plan(self, employees=None):
        """Read-only mapping of ``employees`` (default: all, active and archived).

        A former code TP1nnnn (TP10001-TP10999) becomes TPnnn (nnnn - 10000);
        a three-digit code is kept. Each row has the employee id, company,
        old/new code, source number, ``status`` (keep/convert/conflict) and
        the blocking ``issue``. Duplicates are checked against every employee
        of the company (current and target codes), retired numbers against the
        deletion/correction log and roster rows against their verified source
        number. A conflict is reported, never solved by another number.
        """
        everyone = self.sudo().with_context(active_test=False).search([], order='id')
        employees = everyone if employees is None else employees.sudo().with_context(active_test=False).sorted('id')

        def target(employee):
            code = employee.tp_employee_code or ''
            if code_number(code) is not None:
                return code
            number = legacy_number(code)
            return format_code(number) if number is not None else None

        targets = {employee.id: target(employee) for employee in everyone | employees}
        holders = {}
        for employee in everyone | employees:
            for code in {employee.tp_employee_code, targets[employee.id]} - {False, None, ''}:
                holders.setdefault((employee.company_id.id, code), set()).add(employee.id)
        rows = []
        for employee in employees:
            old, new = employee.tp_employee_code or '', targets[employee.id]
            issue = ''
            if not old:
                issue = 'thiếu mã nhân viên'
            elif new is None:
                issue = 'mã ngoài quy tắc (chỉ chuyển TP10001–TP10999 hoặc giữ TP001–TP999); không cắt số cuối'
            else:
                others = holders.get((employee.company_id.id, new), set()) - {employee.id}
                if others:
                    issue = 'trùng mã %s với hồ sơ ID %s cùng công ty' % (new, ', '.join(map(str, sorted(others))))
                elif new != old and self._tp_code_retired(new, employee_ref=employee.id):
                    issue = 'số %s thuộc hồ sơ đã xóa hoặc đã đổi mã; không cấp lại' % new
            if not issue and employee.tp_source_code:
                try:
                    expected = employee_code(employee.tp_source_code)
                except ValueError:
                    expected = None
                if expected != new:
                    issue = 'mã nguồn %s không cho ra mã %s' % (employee.tp_source_code, new)
            rows.append({'id': employee.id, 'name': employee.name, 'company_id': employee.company_id.id,
                         'company': employee.company_id.name, 'active': employee.active, 'old': old, 'new': new or '',
                         'source': employee.tp_source_code or '', 'issue': issue,
                         'status': 'conflict' if issue else ('keep' if new == old else 'convert')})
        return rows

    @api.model
    def _tp_code_format_digest(self, rows):
        return hashlib.sha256(json.dumps([[row['id'], row['old'], row['new'], row['status']] for row in rows]).encode()).hexdigest()

    @api.model
    def _tp_code_format_apply(self, reason, employees=None):
        """Convert the codes of a valid plan; trusted backend use only.

        Runs under the company and code locks with the employee rows locked,
        re-checks the plan, aborts on any conflict before writing, changes only
        ``tp_employee_code`` (same record, id, account and links), writes one
        audit row and one chatter note per change without notifications and
        moves the sequence to the next free three-digit number. Running it
        again changes nothing.
        """
        if not self.env.su:
            raise AccessError(self.env._('Chuyển định dạng mã nhân viên chỉ chạy qua migration có kiểm soát.'))
        if not (reason or '').strip():
            raise UserError(self.env._('Cần lý do để chuyển định dạng mã nhân viên.'))
        for company_id in sorted(self.env['res.company'].sudo().with_context(active_test=False).search([]).ids):
            self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [_COMPANY_LOCK, company_id])
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [_CODE_LOCK])
        self.env.cr.execute('SELECT id FROM hr_employee ORDER BY id FOR UPDATE')
        self.env.invalidate_all()
        rows = self._tp_code_format_plan(employees)
        conflicts = [row for row in rows if row['status'] == 'conflict']
        if conflicts:
            lines = '\n'.join('• ID %(id)s %(name)s (%(company)s): %(old)s — %(issue)s' % dict(row, old=row['old'] or '-')
                              for row in conflicts[:50])
            raise UserError(self.env._('Chưa chuyển mã nhân viên: mapping còn %(count)s vấn đề cần đối chiếu (không tự cấp số khác).\n%(lines)s',
                                       count=len(conflicts), lines=lines))
        digest = self._tp_code_format_digest(rows)
        changes = [row for row in rows if row['status'] == 'convert']
        Employee = self.sudo().with_context(active_test=False, mail_notrack=True, _tp_code_correction=_TP_CODE_CORRECTION)
        audit = []
        for row in changes:
            employee = Employee.browse(row['id'])
            employee.write({'tp_employee_code': row['new']})
            employee._message_log(body=self.env._('Đổi mã nhân viên %(old)s → %(new)s theo quy tắc TP + 3 chữ số (%(request)s). ID hồ sơ, tài khoản và liên kết giữ nguyên.',
                                                  old=row['old'], new=row['new'], request=CODE_FORMAT_REQUEST))
            audit.append({'action': 'code_correction', 'employee_ref': row['id'], 'employee_name': row['name'],
                          'employee_code': row['old'], 'new_code': row['new'], 'source_code': row['source'] or False,
                          'company_id': row['company_id'], 'reason': reason, 'request_id': f'{CODE_FORMAT_REQUEST}:{digest[:16]}',
                          'snapshot': {'request': CODE_FORMAT_REQUEST, 'rule': 'TP1nnnn -> TPnnn (nnnn - 10000)',
                                       'plan_digest': digest, 'active': row['active']}})
        if audit:
            self.env['tp.hr.employee.audit']._tp_record(audit)
        sequence = self._tp_code_sequence()
        if sequence.padding != 3:
            sequence.write({'padding': 3})
        floor = self._tp_code_floor()
        if not floor <= self._tp_sequence_next(sequence) <= CODE_MAX:
            self._tp_reset_code_sequence(floor)
        return {'digest': digest, 'changed': [(row['id'], row['old'], row['new']) for row in changes],
                'kept': sum(row['status'] == 'keep' for row in rows), 'next': self._tp_sequence_next(sequence)}

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
