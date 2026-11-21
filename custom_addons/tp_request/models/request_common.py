# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Shared constants, concurrency locks, live-admin checks and helpers for tp_request."""
import re
import unicodedata
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from psycopg2 import errors as pg_errors

from odoo import _
from odoo.exceptions import AccessError, UserError
from odoo.tools import SQL

DEFAULT_TZ = 'Asia/Ho_Chi_Minh'
INTERNAL = object()
BRIDGE_INTERNAL = object()
CONTEXT_KEY = '_tp_request_internal'
BRIDGE_KEY = '_tp_request_bridge'

HANDLER_KINDS = [
    ('attendance_correction', 'Điều chỉnh công'),
    ('equipment_assign', 'Cấp thiết bị'),
    ('equipment_swap', 'Đổi thiết bị'),
    ('equipment_purchase', 'Mua bổ sung thiết bị'),
    ('equipment_repair', 'Sửa chữa / báo hỏng thiết bị'),
    ('it_support', 'Hỗ trợ IT'),
    ('general', 'Đề nghị nội bộ chung'),
]

APPROVAL_STATES = [
    ('draft', 'Nháp'),
    ('pending', 'Chờ duyệt'),
    ('returned', 'Trả lại bổ sung'),
    ('approved', 'Đã duyệt'),
    ('rejected', 'Từ chối'),
    ('withdrawn', 'Đã rút / hủy'),
]

EXECUTION_STATES = [
    ('not_applicable', 'Không yêu cầu thực hiện'),
    ('waiting_approval', 'Chờ duyệt xong'),
    ('pending', 'Chờ thực hiện'),
    ('in_progress', 'Đang thực hiện'),
    ('done', 'Hoàn thành'),
    ('cancelled', 'Không thể thực hiện'),
]

PRIORITIES = [
    ('normal', 'Bình thường'),
    ('high', 'Cao'),
    ('urgent', 'Khẩn cấp'),
]

SUBMITTER_SCOPES = [
    ('all_internal', 'Toàn bộ nhân viên nội bộ'),
    ('departments', 'Theo phòng ban được chọn'),
    ('users', 'Theo người dùng cụ thể'),
]

APPROVER_RULES = [
    ('specific_users', 'Người dùng cụ thể'),
    ('direct_manager', 'Quản lý trực tiếp (hồ sơ nhân sự)'),
    ('department_manager', 'Trưởng phòng (danh mục phòng ban)'),
    ('project_lead', 'Chủ trì dự án (phân công dự án)'),
    ('admin_group', 'Nhóm Quản trị hệ thống (Admin gốc & ủy quyền)'),
]

APPROVAL_POLICIES = [
    ('any_one', 'Một người duyệt là đủ'),
]

EXECUTOR_MODES = [
    ('none', 'Không có bước thực hiện sau duyệt'),
    ('admin_group', 'Quản trị hệ thống / phụ trách Kho & IT'),
    ('specific_users', 'Người thực hiện cụ thể'),
    ('department_members', 'Thành viên phòng ban thực hiện'),
]

IT_CATEGORIES = [
    ('account', 'Tài khoản / phân quyền'),
    ('software', 'Phần mềm / cài đặt'),
    ('network', 'Mạng / VPN / máy in'),
    ('hardware', 'Phần cứng / thiết bị'),
    ('other', 'Hỗ trợ IT khác'),
]

IT_IMPACTS = [
    ('self', 'Ảnh hưởng cá nhân'),
    ('team', 'Ảnh hưởng nhóm / phòng ban'),
    ('company', 'Ảnh hưởng toàn công ty'),
]

OLD_EQUIP_CONDITIONS = [
    ('good', 'Tốt — tái sử dụng được'),
    ('limited', 'Hạn chế — cần kiểm tra'),
    ('broken', 'Hỏng — cần sửa chữa / xử lý'),
]

STEP_STATES = [
    ('waiting', 'Chờ lượt'),
    ('pending', 'Đang chờ duyệt'),
    ('approved', 'Đã chấp thuận'),
    ('returned', 'Đã trả lại'),
    ('rejected', 'Đã từ chối'),
    ('skipped', 'Đã dừng / hủy'),
]

HISTORY_ACTIONS = [
    ('create', 'Tạo đề nghị'),
    ('update', 'Cập nhật nội dung'),
    ('submit', 'Gửi phê duyệt'),
    ('resubmit', 'Gửi lại sau bổ sung'),
    ('approve_step', 'Chấp thuận bước duyệt'),
    ('approve_final', 'Hoàn tất phê duyệt'),
    ('return', 'Trả lại bổ sung'),
    ('reject', 'Từ chối'),
    ('withdraw', 'Rút / hủy đề nghị'),
    ('transfer_approver', 'Chuyển giao người duyệt'),
    ('assign_executor', 'Nhận / phân công thực hiện'),
    ('start_execution', 'Bắt đầu thực hiện'),
    ('update_progress', 'Cập nhật tiến độ thực hiện'),
    ('complete_execution', 'Hoàn thành thực hiện'),
    ('cancel_execution', 'Hủy / không thể thực hiện'),
    ('link_result', 'Liên kết hồ sơ nghiệp vụ'),
]


def internal(records):
    return records.sudo().with_context(**{CONTEXT_KEY: INTERNAL})


def is_internal(records):
    return records.env.context.get(CONTEXT_KEY) is INTERNAL


def is_bridge(records):
    return records.env.context.get(BRIDGE_KEY) is BRIDGE_INTERNAL


def fold_text(value):
    text = unicodedata.normalize('NFD', str(value or '')).replace('đ', 'd').replace('Đ', 'D')
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    return re.sub(r'\s+', ' ', text).strip().lower()


def lock_rows(records, nowait=True):
    """Acquire PostgreSQL row lock in deterministic ID order and refresh ORM cache."""
    if not records or not records.ids:
        return
    if records.env.cr.readonly:
        return
    clause = 'FOR UPDATE NOWAIT' if nowait else 'FOR UPDATE'
    try:
        with records.env.cr.savepoint(flush=False):
            records.env.cr.execute(
                SQL(f'SELECT id FROM %s WHERE id IN %s ORDER BY id {clause}',
                    SQL.identifier(records._table), tuple(sorted(records.ids))),
            )
    except pg_errors.LockNotAvailable:
        raise UserError(_('Hồ sơ đang được xử lý bởi thao tác khác. Vui lòng thử lại sau ít giây.')) from None
    records.invalidate_recordset()


def _delegation_ready(env):
    Users = env['res.users']
    return bool(
        env.ref('tp_admin_delegation.group_original_admin', raise_if_not_found=False)
        and all(hasattr(Users, fn) for fn in ('_tp_is_original_admin', '_tp_has_live_admin_grant', '_tp_admin_lock'))
    )


def is_live_admin_user(user, company=None, lock=False):
    """True only for Original Admin or a Delegated Full Admin with a live grant in company (DEC-054/061/062)."""
    if not user:
        return False
    user = user.sudo().with_context(active_test=False)
    if not user.active or user.share or not user.has_group('base.group_system'):
        return False
    if company and company not in user.company_ids:
        return False
    if not _delegation_ready(user.env):
        return False
    if lock and not user.env.cr.readonly:
        user._tp_admin_lock()
        user.invalidate_recordset(['active', 'share', 'company_ids', 'group_ids', 'all_group_ids'])
        if not user.active or user.share or not user.has_group('base.group_system'):
            return False
    if user._tp_is_original_admin():
        return True
    if company:
        return bool(user._tp_has_live_admin_grant(company=company))
    return bool(user._tp_has_live_admin_grant())


def live_admin_users(env, company=None):
    """Return active internal Original Admins + live Delegated Full Admins for company."""
    if not _delegation_ready(env):
        return env['res.users']
    sys_group = env.ref('base.group_system', raise_if_not_found=False)
    if not sys_group:
        return env['res.users']
    domain = [
        ('active', '=', True),
        ('share', '=', False),
        ('all_group_ids', 'in', sys_group.id),
    ]
    if company:
        domain.append(('company_ids', 'in', company.id))
    candidates = env['res.users'].sudo().with_context(active_test=False).search(domain, order='id')
    valid_ids = [u.id for u in candidates if is_live_admin_user(u, company=company)]
    return env['res.users'].browse(valid_ids)


def is_request_manager(env, company=None, user=None, lock=False):
    """True for live admins or active internal users explicitly holding group_request_manager."""
    if env.su and not user:
        return True
    target = (user or env.user).sudo().with_context(active_test=False)
    if not target.active or target.share:
        return False
    if company and company not in target.company_ids:
        return False
    if is_live_admin_user(target, company=company, lock=lock):
        return True
    return bool(target.has_group('tp_request.group_request_manager'))


def require_request_manager(env, company=None):
    if not is_request_manager(env, company=company, lock=True):
        raise AccessError(_('Chỉ Quản trị Đề nghị & Phê duyệt mới có quyền thực hiện thao tác cấu hình này.'))


def active_internal_users(users, company=None):
    """Filter a res.users recordset to active, non-share users with access to company."""
    if not users:
        return users
    checked = users.sudo().with_context(active_test=False)
    valid_ids = []
    for u in checked:
        if not u.active or u.share or not u.has_group('base.group_user'):
            continue
        if company and company not in u.company_ids:
            continue
        valid_ids.append(u.id)
    return users.env['res.users'].browse(valid_ids)


def add_working_hours(start_dt, hours, tz_name=DEFAULT_TZ):
    """Compute a deadline by adding working hours (Mon-Fri 08:30-17:30, 12:00-13:00 lunch = 8h/day).

    Returns naive UTC datetime, always >= start_dt.
    """
    if not start_dt or not hours or hours <= 0:
        return False
    tz = ZoneInfo(tz_name or DEFAULT_TZ)
    current = start_dt.replace(tzinfo=UTC).astimezone(tz)
    remaining = float(hours) * 60.0  # minutes

    def next_window_start(dt_local):
        cur = dt_local
        for _ in range(30):
            if cur.weekday() >= 5:  # Sat/Sun -> Monday 08:30
                cur = datetime.combine(cur.date() + timedelta(days=7 - cur.weekday()), time(8, 30), tzinfo=tz)
                continue
            t = cur.time()
            if t < time(8, 30):
                return datetime.combine(cur.date(), time(8, 30), tzinfo=tz)
            if time(8, 30) <= t < time(12, 0):
                return cur
            if time(12, 0) <= t < time(13, 0):
                return datetime.combine(cur.date(), time(13, 0), tzinfo=tz)
            if time(13, 0) <= t < time(17, 30):
                return cur
            cur = datetime.combine(cur.date() + timedelta(days=1), time(8, 30), tzinfo=tz)
        return cur

    for _ in range(2000):
        if remaining <= 0.001:
            break
        current = next_window_start(current)
        window_end = (
            datetime.combine(current.date(), time(12, 0), tzinfo=tz)
            if current.time() < time(12, 0)
            else datetime.combine(current.date(), time(17, 30), tzinfo=tz)
        )
        avail = (window_end - current).total_seconds() / 60.0
        if remaining <= avail:
            current = current + timedelta(minutes=remaining)
            remaining = 0.0
            break
        remaining -= avail
        current = window_end
    return current.astimezone(UTC).replace(tzinfo=None)


def format_dt_local(dt_value, tz_name=DEFAULT_TZ):
    if not dt_value:
        return ''
    tz = ZoneInfo(tz_name or DEFAULT_TZ)
    return dt_value.replace(tzinfo=UTC).astimezone(tz).strftime('%d/%m/%Y %H:%M')


def format_date_vn(d_value):
    if not d_value:
        return ''
    return d_value.strftime('%d/%m/%Y')
