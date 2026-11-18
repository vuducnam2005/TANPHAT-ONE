from odoo.addons.tp_hr_workspace.models.employee_order import backfill_employee_department_sequence


def migrate(cr, version):
    if not version:
        return
    backfill_employee_department_sequence(cr)
