"""Menu presentation and workspace RPC share the same server-side scope."""
from copy import deepcopy

from odoo import api, models
from odoo.exceptions import AccessError


class WorkspaceUser(models.Model):
    _inherit = 'res.users'

    def _tp_main_employee(self):
        self.ensure_one()
        return self.env['hr.employee'].sudo().search([
            ('user_id', '=', self.id), ('company_id', '=', self.env.company.id), ('active', '=', True),
        ], limit=1).with_context(version_id=False)

    def _tp_can_kd_workspace(self):
        self.ensure_one()
        if self.has_group('base.group_system') or self.has_group('tp_core.group_manager'):
            return True
        if self.env['tp.kd.department.role']._roles(user=self):
            return True
        if not self.has_group('tp_kd_workspace.group_scoped_staff'):
            return False
        employee = self._tp_main_employee()
        department = employee.current_version_id.department_id
        primary = bool(department and self.env['crm.team'].sudo().search_count([
            ('kd_department_id', '=', department.id), ('company_id', '=', self.env.company.id), ('active', '=', True),
        ]))
        # An explicit HEAD or reviewed cross-department assignment is independent of HR.
        return primary or bool(
            self.env['tp.project.assignment'].sudo().search_count([
                ('user_id', '=', self.id), ('company_id', '=', self.env.company.id), ('active', '=', True),
                ('tp_cross_department', '=', True),
            ]))

    @api.model
    def get_tp_department_workspace(self):
        """Only the caller's work identity; no HR private fields or arbitrary user IDs."""
        employee = self.env.user._tp_main_employee()
        department = employee.current_version_id.department_id
        return {'id': department.id, 'name': department.name if department else 'Chưa có phòng ban',
                'status': 'Đang phát triển', 'kd': self.env.user._tp_can_kd_workspace()}


class WorkspaceMenus(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def _visible_menu_ids(self, debug=False):
        ids = set(super()._visible_menu_ids(debug))
        user = self.env.user
        if user.has_group('base.group_system'):
            placeholder = self.env.ref('tp_hr_workspace.menu_department_workspace', raise_if_not_found=False)
            return ids - set(placeholder.ids)
        kd = self.env.ref('tp_kd_workspace.menu_kd', raise_if_not_found=False)
        if kd and not user._tp_can_kd_workspace():
            ids -= set(self.sudo().search([('id', 'child_of', kd.id)]).ids)
        employee = user._tp_main_employee()
        department = employee.current_version_id.department_id
        primary_kd = department and self.env['crm.team'].sudo().search_count([
            ('kd_department_id', '=', department.id), ('company_id', '=', self.env.company.id), ('active', '=', True),
        ])
        if not department or primary_kd:
            ids -= set(self.env.ref('tp_hr_workspace.menu_department_workspace', raise_if_not_found=False).ids)
        return ids

    @api.model
    def load_menus(self, debug):
        result = deepcopy(super().load_menus(debug))
        placeholder = self.env.ref('tp_hr_workspace.menu_department_workspace', raise_if_not_found=False)
        if placeholder and placeholder.id in result:
            result[placeholder.id]['name'] = self.env.user._tp_main_employee().current_version_id.department_id.name or 'Phòng ban của tôi'
        return result


class KdOverviewScope(models.TransientModel):
    _inherit = 'tp.kd.overview'

    @api.model
    def _kd_filter(self, filters):
        if not self.env.user._tp_can_kd_workspace():
            raise AccessError(self.env._('Workspace KH-KD không còn trong phạm vi được cấp. Hãy đăng nhập lại để cập nhật phòng ban.'))
        return super()._kd_filter(filters)

    def _domain(self, *args, **kwargs):
        if not self.env.user._tp_can_kd_workspace():
            raise AccessError(self.env._('Bạn chưa được cấp workspace KH-KD.'))
        return super()._domain(*args, **kwargs)


class KdReportScope(models.TransientModel):
    _inherit = 'tp.kd.report.center'

    @api.model
    def _check_kd_access(self):
        if not self.env.user._tp_can_kd_workspace():
            raise AccessError(self.env._('Bạn chưa được cấp workspace KH-KD hoặc quyền đã bị thu hồi.'))
        return super()._check_kd_access()
