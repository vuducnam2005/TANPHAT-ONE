"""Menu visibility for HR-ATTENDANCE-001: processing entries follow the real capability, not a job title."""
from odoo import models

from .attendance_common import HR_MANAGER, can, is_correction_admin

# menu xmlid -> capability. HR manager always sees review/periods (read-only oversight); actions still check rights.
# "review" = the correction queue: only admins approve (Original + live delegated, CHG-20261119-012); assignments do not open it.
GATED = {
    'tp_hr_attendance.menu_import': 'import',
    'tp_hr_attendance.menu_sources': 'import',
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
            elif capability == 'review':
                allowed = any(is_correction_admin(self.env, company) for company in companies)
            else:
                # Lock needs an active lock assignment in one of the user's companies.
                allowed = bool(self.env['tp.hr.attendance.assignment'].sudo().search_count([
                    ('user_id', '=', self.env.uid), ('active', '=', True), (f'can_{capability}', '=', True),
                    ('company_id', 'in', companies.ids)]))
            if not allowed:
                ids.discard(menu.id)
        # The admin folder disappears when gating left it without a visible entry.
        folder = self.env.ref('tp_hr_attendance.menu_group_attendance_admin', raise_if_not_found=False)
        if folder and folder.id in ids:
            children = self.sudo().with_context(active_test=True).search([('parent_id', '=', folder.id)]).ids
            if not ids & set(children):
                ids.discard(folder.id)
        return frozenset(ids)
