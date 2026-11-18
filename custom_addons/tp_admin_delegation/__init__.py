from . import models


def _post_init_admin_full(env):
    env['tp.admin.delegation']._migrate_admin_full_001()
