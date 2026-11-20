"""HR-EMPLOYEE-CODE-003: keep the attendance copies of the TP code current.

Attendance days and correction requests store the employee code shown in
lists, filters and exports. When the code changes through the audited
correction, only that copy is refreshed, matched by employee and company;
hours, units, lock state and closed periods are not touched, and the ENTI
identity (keyNV / maNV) and source mapping are left as they are.
"""
from odoo import models

from .attendance_common import internal

_CODE_COPIES = ('tp.hr.attendance.day', 'tp.hr.attendance.correction')


class HrEmployeeAttendanceCode(models.Model):
    _inherit = 'hr.employee'

    def write(self, vals):
        result = super().write(vals)
        if 'tp_employee_code' in vals:
            self._tp_sync_attendance_code()
        return result

    def _tp_sync_attendance_code(self):
        """Copy each employee's current code to its stored attendance rows."""
        changed = 0
        for employee in self.sudo().with_context(active_test=False):
            code = employee.tp_employee_code or False
            for model_name in _CODE_COPIES:
                stale = self.env[model_name].sudo().with_context(active_test=False).search([
                    ('employee_id', '=', employee.id), ('company_id', '=', employee.company_id.id),
                    ('employee_code', '!=', code)])
                if stale:
                    internal(stale).with_context(mail_notrack=True).write({'employee_code': code})
                    changed += len(stale)
        return changed
