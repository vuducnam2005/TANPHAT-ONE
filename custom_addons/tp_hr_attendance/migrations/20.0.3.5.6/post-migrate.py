"""HR-ATTENDANCE-CONFIG-MENU-CLEANUP: physically remove deprecated attendance config menus.

Following DEC-063 and native attendance administration unification,
these standalone configuration submenus under Cấu hình HR are removed completely:
- tp_hr_attendance.menu_rules (Quy tắc công)
- tp_hr_attendance.menu_codes (Mã máy chấm công)
- tp_hr_attendance.menu_assignments (Phân công xử lý công)
- tp_hr_attendance.menu_logs (Nhật ký chấm công)
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {'active_test': False})
    for xmlid in (
        'tp_hr_attendance.menu_rules',
        'tp_hr_attendance.menu_codes',
        'tp_hr_attendance.menu_assignments',
        'tp_hr_attendance.menu_logs',
    ):
        menu = env.ref(xmlid, raise_if_not_found=False)
        if menu:
            _logger.info('Unlinking deprecated attendance menu %s (id=%s)', xmlid, menu.id)
            menu.unlink()
        imd = env['ir.model.data'].search([
            ('module', '=', 'tp_hr_attendance'),
            ('name', '=', xmlid.split('.')[1]),
        ])
        if imd:
            _logger.info('Unlinking ir.model.data for %s', xmlid)
            imd.unlink()
