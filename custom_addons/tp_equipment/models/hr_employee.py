from odoo import _, fields, models

from .common import check_admin, is_admin


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # Admin-only bridge: the same employee record as HR, never a copy. HR officers do not see it.
    tp_equipment_ids = fields.One2many(
        "maintenance.equipment", "tp_employee_id", "Thiết bị đang giữ", groups="base.group_system",
        domain=[("tp_lifecycle", "!=", "retired")])
    tp_equipment_count = fields.Integer(
        "Số thiết bị đang giữ", compute="_compute_tp_equipment", groups="base.group_system")
    tp_equipment_warning = fields.Char(
        "Cảnh báo thiết bị", compute="_compute_tp_equipment", groups="base.group_system")

    def _compute_tp_equipment(self):
        if not is_admin(self.env):
            for employee in self:
                employee.tp_equipment_count = 0
                employee.tp_equipment_warning = False
            return
        Equipment = self.env["maintenance.equipment"].with_context(active_test=False)
        counts = dict(Equipment._read_group(
            [("tp_employee_id", "in", self.ids), ("tp_lifecycle", "=", "active"),
             ("tp_custody", "in", ("employee", "loan"))],
            ["tp_employee_id"], ["__count"]))
        for employee in self:
            count = counts.get(employee, 0)
            employee.tp_equipment_count = count
            warning = False
            if count and not employee.active:
                warning = _("Nhân viên đã nghỉ / lưu trữ nhưng còn giữ %s thiết bị: lập phiếu thu hồi.", count)
            elif count and employee.sudo().departure_date:
                warning = _("Nhân viên có ngày nghỉ việc và còn giữ %s thiết bị: lập phiếu thu hồi trước ngày nghỉ.",
                            count)
            employee.tp_equipment_warning = warning

    def action_tp_open_equipment(self):
        check_admin(self.env)
        self.ensure_one()
        # All records linked to this HR employee (any lifecycle), not only the active users scope.
        action = self.env["ir.actions.act_window"]._for_xml_id("tp_equipment.action_equipment_all_records")
        action.update({
            "name": _("Thiết bị của %s", self.name),
            "domain": [("tp_employee_id", "=", self.id)],
            "context": {"tp_filter_profile": "equipment", "tp_eq_leaf": "tp_equipment.menu_equipment_records",
                        "active_test": False},
        })
        return action
