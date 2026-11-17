"""Menu visibility for HR-ATTENDANCE-001: processing entries follow the real capability, not a job title."""
from odoo import models

from .attendance_common import HR_MANAGER, can

# menu xmlid -> capability. HR manager always sees review/periods (read-only oversight); actions still check assignments.
GATED = {
    'tp_hr_attendance.menu_import': 'import',
    'tp_hr_attendance.menu_review': 'review',
    'tp_hr_attendance.menu_periods': 'lock',
}


class IrUiMenuAttendance(models.Model):
    _inherit = 'ir.ui.menu'

    def _visible_menu_ids(self, debug=False):
        ids = set(super()._visible_menu_ids(debug))
        manager = self.env.user.has_group(HR_MANAGER)
        companies = self.env.user.company_ids
        for xmlid, capability in GATED.items():
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if not menu or menu.id not in ids:
                continue
            if capability != 'import' and manager:
                continue
            if capability == 'import':
                allowed = any(can(self.env, 'import', company) for company in companies)
            else:
                # Department-scoped reviewers are enough to show the queue; lock needs a company-wide assignment.
                allowed = bool(self.env['tp.hr.attendance.assignment'].sudo().search_count([
                    ('user_id', '=', self.env.uid), ('active', '=', True), (f'can_{capability}', '=', True),
                    ('company_id', 'in', companies.ids)]))
            if not allowed:
                ids.discard(menu.id)
        return ids
