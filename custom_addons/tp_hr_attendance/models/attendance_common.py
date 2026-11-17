"""Shared constants and helpers for TP attendance (HR-ATTENDANCE-001)."""
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from odoo.exceptions import AccessError

from .attendance_parser import fold

DEFAULT_TZ = 'Asia/Ho_Chi_Minh'
HR_MANAGER = 'hr.group_hr_manager'
HR_USER = 'hr.group_hr_user'
OFFICER = 'tp_hr_attendance.group_attendance_officer'
# Only server code holding this sentinel may write imported punches, day summaries and the audit log.
INTERNAL = object()
CONTEXT_KEY = '_tp_attendance_internal'
DATA_STATES = [('ok', 'Đủ dữ liệu'), ('missing', 'Thiếu giờ vào/ra'), ('review', 'Cần kiểm tra')]
UNITS_STATES = [
    ('unconfirmed', 'Chưa xác nhận'), ('pending', 'Chờ đủ dữ liệu'),
    ('off_schedule', 'Ngoài lịch làm việc'), ('confirmed', 'Đã tính theo quy tắc'),
]
LOCK_STATES = [('open', 'Đang mở'), ('locked', 'Đã chốt')]
__all__ = ['fold']


def internal(records):
    return records.sudo().with_context(**{CONTEXT_KEY: INTERNAL})


def is_internal(records):
    return records.env.context.get(CONTEXT_KEY) is INTERNAL


def deny_direct(records):
    if not is_internal(records):
        raise AccessError(records.env._('Dữ liệu công chỉ được cập nhật qua nhập dữ liệu, duyệt điều chỉnh hoặc chốt kỳ.'))


def local_to_utc(work_date, clock, tz=DEFAULT_TZ):
    local = datetime.combine(work_date, clock).replace(tzinfo=ZoneInfo(tz or DEFAULT_TZ))
    return local.astimezone(UTC).replace(tzinfo=None)


def utc_to_local(value, tz=DEFAULT_TZ):
    if not value:
        return None
    return value.replace(tzinfo=UTC).astimezone(ZoneInfo(tz or DEFAULT_TZ)).replace(tzinfo=None)


def local_today(tz=DEFAULT_TZ):
    return datetime.now(ZoneInfo(tz or DEFAULT_TZ)).date()


def assignments(env, company=None, capability=None, user=None):
    user = user or env.user
    domain = [('user_id', '=', user.id), ('active', '=', True)]
    if company:
        domain.append(('company_id', '=', company.id))
    if capability:
        domain.append((f'can_{capability}', '=', True))
    return env['tp.hr.attendance.assignment'].sudo().search(domain)


def can(env, capability, company, departments=None):
    """Return True when the current user holds ``capability`` (import/review/lock) for ``company``.

    Import and configuration need HR manager rights or a company-wide import assignment.
    Review and lock never follow from a job title or group: only an active assignment whose
    department scope (empty = whole company) covers every given department.
    """
    if capability == 'import' and env.user.has_group(HR_MANAGER):
        return True
    for assignment in assignments(env, company, capability):
        if not assignment.department_ids:
            return True
        if capability != 'import' and departments is not None:
            wanted = set(departments.ids) if hasattr(departments, 'ids') else set(departments)
            if wanted and wanted <= set(assignment.department_ids.ids):
                return True
    return False


def require(env, capability, company, departments=None):
    if not can(env, capability, company, departments):
        labels = {'import': 'nhập dữ liệu công', 'review': 'duyệt điều chỉnh công', 'lock': 'chốt kỳ công'}
        raise AccessError(env._('Bạn chưa được phân công %(task)s trong phạm vi này.', task=labels.get(capability, capability)))
