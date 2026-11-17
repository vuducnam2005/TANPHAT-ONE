"""Read-only HR directory for every internal employee (HR-DIRECTORY-READONLY-001).

The directory is the native ``hr.employee.public`` projection (SQL view, read ACL
for ``base.group_user`` only). Nothing here grants an HR group: the TP HR entry,
the viewer label and the export guard follow the caller's real groups.
"""
from odoo import api, models
from odoo.exceptions import AccessError

HR_GROUP = 'hr.group_hr_user'


def is_hr_officer(env):
    return env.su or env.user.has_group(HR_GROUP)


class HrWorkspaceDirectory(models.AbstractModel):
    _inherit = 'tp.hr.workspace'

    @api.model
    def _tp_entry_action(self):
        """TP HR entry: HR keeps the overview, everybody else lands on the directory."""
        xmlid = 'tp_hr_workspace.action_overview' if is_hr_officer(self.env) else 'tp_hr_workspace.action_directory'
        return self.env['ir.actions.actions']._for_xml_id(xmlid)


class HrEmployeePublicDirectory(models.Model):
    _inherit = 'hr.employee.public'

    def export_data(self, fields_to_export):
        # Colleagues may be viewed, not bulk-exported (native button and direct RPC alike).
        if not is_hr_officer(self.env):
            raise AccessError(self.env._('Danh bạ nhân viên chỉ xem; chỉ nhân sự được giao mới được xuất danh sách.'))
        return super().export_data(fields_to_export)


class IrUiMenuDirectory(models.Model):
    _inherit = 'ir.ui.menu'

    def _visible_menu_ids(self, debug=False):
        ids = set(super()._visible_menu_ids(debug))
        if self.env.user.has_group(HR_GROUP):
            # HR already has the full employee list; the read-only entry is for everybody else.
            ids -= set(self.env.ref('tp_hr_workspace.menu_directory', raise_if_not_found=False).ids)
        return ids


class IrHttpDirectory(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        if self.env.user._is_internal():
            result['tp_hr_readonly'] = not self.env.user.has_group(HR_GROUP)
        return result
