from . import controllers, models
from .models.employee_order import backfill_employee_department_sequence


def post_init_hook(env):
    backfill_employee_department_sequence(env.cr)
