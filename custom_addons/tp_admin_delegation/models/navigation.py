"""Expose only audited native entry points; every destination keeps its backend scope."""
from copy import deepcopy

from odoo import api, models

_ENTRIES = (
    ('tp_hr_workspace.menu_hr', 'tp_hr_workspace.action_employees', 'hr.employee'),
    ('tp_kd_workspace.menu_kd', 'tp_kd_workspace.action_projects', 'project.project'),
    ('tp_reporting.menu_root', 'tp_reporting.action_personal', 'tp.report.document'),
    ('tp_equipment.menu_root', 'tp_equipment.action_equipment', 'maintenance.equipment'),
)
_LEAVES = (
    'tp_hr_workspace.menu_employees', 'tp_kd_workspace.menu_projects',
    'tp_reporting.menu_personal', 'tp_equipment.menu_equipment_all',
    'tp_admin_delegation.menu_delegated_hr_create',
)


class DelegationSession(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        result['tp_admin_delegation'] = True
        return result


class DelegationMenus(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def load_menus(self, debug):
        baseline = super().load_menus(debug)
        if not self.env.user._tp_has_admin_delegation():
            return baseline
        result = deepcopy(baseline)
        result.setdefault('root', {'id': False, 'name': 'root', 'children': []})

        def add(menu, app, action=None):
            if menu.id not in result:
                chosen = action or menu.action
                result[menu.id] = {
                    'id': menu.id, 'name': menu.name, 'app_id': app,
                    'action_model': chosen._name if chosen else False,
                    'action_id': chosen.id if chosen else False,
                    'action_path': chosen.path if chosen else False,
                    'web_icon': menu.web_icon, 'web_icon_data': False,
                    'web_icon_data_mimetype': False,
                    'xmlid': menu.get_external_id().get(menu.id, ''), 'children': [],
                }
            elif action:
                result[menu.id].update(action_model=action._name, action_id=action.id, action_path=action.path)
            return result[menu.id]

        for xmlid, action_xmlid, model in _ENTRIES:
            if not self.env[model].has_access('read'):
                continue
            menu = self.env.ref(xmlid).sudo()
            action = self.env.ref(action_xmlid).sudo()
            add(menu, menu.id, action)
            if menu.id not in result['root']['children']:
                result['root']['children'].append(menu.id)
        for xmlid in _LEAVES:
            leaf = self.env.ref(xmlid).sudo()
            ancestors = [leaf]
            parent = leaf.parent_id
            while parent:
                ancestors.append(parent)
                parent = parent.parent_id
            app = ancestors[-1]
            if app.id not in result:
                continue
            for child in reversed(ancestors[:-1]):
                add(child, app.id)
                children = result[child.parent_id.id]['children']
                if child.id not in children:
                    children.append(child.id)
        return result
