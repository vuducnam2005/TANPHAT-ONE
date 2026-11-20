"""HR-CONFIG-MENU-CLEANUP: physically remove deprecated HR config menus.

Keeps only 'Nhãn nhân viên' (tp_hr_workspace.menu_categories) under
Cấu hình HR (tp_hr_workspace.menu_group_config).
Unlinks:
- tp_hr_workspace.menu_skill_types
- tp_hr_workspace.menu_resume_types
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {'active_test': False})
    for xmlid in (
        'tp_hr_workspace.menu_skill_types',
        'tp_hr_workspace.menu_resume_types',
    ):
        menu = env.ref(xmlid, raise_if_not_found=False)
        if menu:
            _logger.info('Unlinking deprecated menu %s (id=%s)', xmlid, menu.id)
            menu.unlink()
        imd = env['ir.model.data'].search([
            ('module', '=', 'tp_hr_workspace'),
            ('name', '=', xmlid.split('.')[1]),
        ])
        if imd:
            _logger.info('Unlinking ir.model.data for %s', xmlid)
            imd.unlink()
