# Base models must be registered before their extensions.
from . import catalog, reporting  # noqa: I001
from . import binary, completion, dashboard, export, navigation, personal_web, selection
