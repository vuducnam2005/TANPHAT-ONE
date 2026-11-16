# ruff: noqa: I001
# Model extensions load in dependency order; company scope must wrap them last.
from . import common
from . import equipment
from . import move
from . import receipt
from . import pdf
from . import hr_employee
from . import wizard
from . import repair
from . import proposal
from . import inventory
from . import import_batch
from . import dashboard
from . import reports
from . import quick_action
from . import company_scope
