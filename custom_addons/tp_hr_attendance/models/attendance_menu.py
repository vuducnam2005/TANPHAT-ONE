"""Menu visibility for HR-ATTENDANCE-001: the import entry follows the real import capability."""
from odoo import models

from .attendance_common import can


class IrUiMenuAttendance(models.Model):
    _inherit = 'ir.ui.menu'

    def _visible_menu_ids(self, debug=False):
        ids = set(super()._visible_menu_ids(debug))
        menu = self.env.ref('tp_hr_attendance.menu_import', raise_if_not_found=False)
        if menu and menu.id in ids:
            # Officers see the processing group; only import assignments (or HR manager) see Nhập dữ liệu.
            if not any(can(self.env, 'import', company) for company in self.env.user.company_ids):
                ids.discard(menu.id)
        return ids
