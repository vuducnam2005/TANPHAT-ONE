"""HR-CORRECTION-008: delete mistaken manual entries or archive used records."""
from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def action_tp_delete_mistaken(self):
        """Open the guarded deletion dialog for the selected employees (admin)."""
        employees = self.with_context(active_test=False)
        employees._tp_check_delete_admin()
        wizard = self.env['tp.hr.employee.delete.wizard'].create({'employee_ids': [(6, 0, employees.ids)]})
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Xóa hồ sơ nhập nhầm'),
            'res_model': 'tp.hr.employee.delete.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'views': [(self.env.ref('tp_hr_workspace.employee_delete_wizard_form').id, 'form')],
            'target': 'new',
            'context': {'dialog_size': 'medium'},
        }

    def action_unlink_wizard(self):
        # hr_timesheet binds a generic "Delete" action; route it to the guarded flow.
        return self.action_tp_delete_mistaken()


class EmployeeDeleteWizard(models.TransientModel):
    _name = 'tp.hr.employee.delete.wizard'
    _description = 'Xóa hồ sơ nhân viên nhập nhầm'

    employee_ids = fields.Many2many('hr.employee', string='Hồ sơ đã chọn', readonly=True, context={'active_test': False})
    employee_count = fields.Integer(string='Số hồ sơ', compute='_compute_check')
    eligible = fields.Boolean(compute='_compute_check')
    can_archive = fields.Boolean(compute='_compute_check')
    summary = fields.Html(string='Hồ sơ', compute='_compute_check', sanitize=False)
    reason = fields.Text(string='Lý do xóa')

    @api.depends('employee_ids')
    def _compute_check(self):
        for wizard in self:
            employees = wizard.employee_ids.with_context(active_test=False)
            blockers = employees._tp_deletion_blockers()
            rows = []
            for employee in employees.sudo():
                reasons = blockers.get(employee.id)
                status = (Markup('<ul class="mb-0 ps-3">%s</ul>') % Markup().join(Markup('<li>%s</li>') % reason for reason in reasons)
                          if reasons else escape(self.env._('Đủ điều kiện xóa')))
                rows.append(Markup('<tr class="%s"><td>%s</td><td class="text-nowrap">%s</td><td>%s</td></tr>') % (
                    'o_tp_blocked' if reasons else 'o_tp_eligible', employee.name, employee.tp_employee_code or '-', status))
            wizard.employee_count = len(employees)
            wizard.eligible = bool(employees) and not blockers
            wizard.can_archive = bool(employees.filtered('active'))
            wizard.summary = Markup(
                '<table class="table table-sm o_tp_hr_delete_table mb-0"><thead><tr><th>%s</th><th>%s</th><th>%s</th></tr></thead><tbody>%s</tbody></table>',
            ) % (self.env._('Họ và tên'), self.env._('Mã nhân viên'), self.env._('Kiểm tra'), Markup().join(rows))

    def action_confirm_delete(self):
        self.ensure_one()
        employees = self.employee_ids.with_context(active_test=False)
        if not (self.reason or '').strip():
            raise UserError(self.env._('Vui lòng nhập lý do xóa hồ sơ nhập nhầm.'))
        count = employees._tp_delete_mistaken(self.reason)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': self.env._('Đã xóa vĩnh viễn %(count)s hồ sơ nhập nhầm. Nhật ký đã được ghi.', count=count),
                # The deleted record cannot be reopened: return to the employee list.
                'next': dict(self.env['ir.actions.act_window']._for_xml_id('tp_hr_workspace.action_employees'), target='main'),
            },
        }

    def action_archive_instead(self):
        self.ensure_one()
        employees = self.employee_ids.with_context(active_test=False)
        employees._tp_check_delete_admin()
        active = employees.filtered('active')
        if not active:
            raise UserError(self.env._('Các hồ sơ đã chọn đều đã được lưu trữ.'))
        active.action_archive()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': self.env._('Đã lưu trữ %(count)s hồ sơ. Tài khoản cá nhân (nếu có) không thay đổi; khóa tài khoản ở mục Tài khoản & phân quyền khi cần.', count=len(active)),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
