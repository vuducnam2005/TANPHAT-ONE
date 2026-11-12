from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

from odoo.addons.web.controllers.action import Action


class WorkspaceAction(Action):
    @http.route()
    def load(self, action_id, context=None):
        # Native action/load uses sudo; check the real session actor before that boundary.
        if isinstance(action_id, str) and '.' in action_id:
            record = request.env.ref(action_id, raise_if_not_found=False)
        elif str(action_id).isdigit():
            record = request.env['ir.actions.actions'].browse(int(action_id))
        else:
            record = request.env['ir.actions.actions'].sudo().search([('path', '=', action_id)], limit=1)
        if record:
            binding = request.env['ir.model.data'].sudo().search_count([
                ('module', '=', 'tp_kd_workspace'), ('model', 'like', 'ir.actions.%'), ('res_id', '=', record.id),
            ])
            if binding and not request.env.user._tp_can_kd_workspace():
                raise AccessError(request.env._('Workspace KH-KD đã bị thu hồi. Vui lòng tải lại hoặc đăng nhập lại.'))
        return super().load(action_id, context=context)
