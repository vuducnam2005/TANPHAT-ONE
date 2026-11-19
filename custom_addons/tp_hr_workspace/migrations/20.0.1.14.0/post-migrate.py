"""Preserve the prior native department order when introducing saved ordering."""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    # name was the previous hr.department._order; this initialization runs once.
    departments = api.Environment(cr, SUPERUSER_ID, {})['hr.department'].with_context(active_test=False)
    for position, department in enumerate(departments.search([], order='name, id'), 1):
        cr.execute('UPDATE hr_department SET tp_sequence = %s WHERE id = %s', (position * 10, department.id))
