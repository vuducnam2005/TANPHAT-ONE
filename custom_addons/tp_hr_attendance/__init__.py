from . import models


def post_init_hook(env):
    models.attendance_matrix._tp_migrate_matrix_003(env)
