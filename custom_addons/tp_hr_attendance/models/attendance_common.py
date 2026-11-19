"""Shared constants and helpers for TP attendance (HR-ATTENDANCE-001)."""
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from odoo.exceptions import AccessError

from .attendance_parser import fold

DEFAULT_TZ = 'Asia/Ho_Chi_Minh'
HR_MANAGER = 'hr.group_hr_manager'
HR_USER = 'hr.group_hr_user'
OFFICER = 'tp_hr_attendance.group_attendance_officer'
# Soft reference: tp_hr_attendance does not depend on tp_admin_delegation; missing group = nobody approves.
ORIGINAL_ADMIN = 'tp_admin_delegation.group_original_admin'
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
    department scope (empty = whole company) covers every given department. Since
    CHG-20261119-005 a review assignment only widens shared exports; approving or returning a
    correction belongs to the Original Admin (``require_original_admin``).
    """
    if company not in env.companies:
        return False
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


def original_admins(env, company=None):
    """Active Original Admins (tp_admin_delegation, DEC-054) who handle every attendance correction.

    Resolved only through the delegation module's own check: delegated Full Admins, HR managers,
    department heads and attendance assignments never qualify. When the delegation module is not
    installed nobody qualifies, so approval fails closed instead of falling back to another role.
    """
    Users = env['res.users'].sudo().with_context(active_test=False)
    group = env.ref(ORIGINAL_ADMIN, raise_if_not_found=False)
    if not group or not hasattr(Users, '_tp_is_original_admin'):
        return env['res.users']
    domain = [('all_group_ids', 'in', group.id), ('active', '=', True), ('share', '=', False)]
    if company:
        domain.append(('company_ids', 'in', company.id))
    users = Users.search(domain).filtered(lambda user: user._tp_is_original_admin())
    return env['res.users'].browse(users.ids)


def is_original_admin(env, company=None):
    """True when the session user is an Original Admin with ``company`` open in the session."""
    if company is not None and company not in env.companies:
        return False
    return env.user in original_admins(env, company)


def require_original_admin(env, company):
    if not is_original_admin(env, company):
        raise AccessError(env._('Chỉ admin chính (admin gốc) được duyệt hoặc trả đề nghị điều chỉnh công. '
                                'Admin được ủy quyền, trưởng phòng và người được phân công không có quyền này.'))


def require(env, capability, company, departments=None):
    if not can(env, capability, company, departments):
        labels = {'import': 'nhập dữ liệu công', 'review': 'duyệt điều chỉnh công', 'lock': 'chốt kỳ công'}
        raise AccessError(env._('Bạn chưa được phân công %(task)s trong phạm vi này.', task=labels.get(capability, capability)))
