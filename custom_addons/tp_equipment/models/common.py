"""Shared rules of the office-equipment module (EQUIP-001).

Only an active internal user with ``base.group_system`` manages equipment. There is no
equipment-manager substitute group: every guard below asks the same question.
"""
import re
import unicodedata

from psycopg2 import errors as pg_errors

from odoo import _, api, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import SQL

ADMIN_GROUP = "base.group_system"
# Internal workflow authority cannot be manufactured by a JSON-RPC context flag.
INTERNAL = object()

# Every model whose records, chatter, followers, activities or files belong to this module.
# Keep in sync with security/ir.access.csv (restriction rows for mail/attachment models).
TP_EQUIPMENT_MODELS = (
    "maintenance.equipment",
    "maintenance.request",
    "maintenance.equipment.category",
    "tp.equipment.location",
    "tp.equipment.software",
    "tp.equipment.meter",
    "tp.equipment.move",
    "tp.equipment.move.line",
    "tp.equipment.receipt",
    "tp.equipment.receipt.line",
    "tp.equipment.proposal",
    "tp.equipment.proposal.line",
    "tp.equipment.proposal.review",
    "tp.equipment.proposal.approval",
    "tp.equipment.inventory",
    "tp.equipment.inventory.line",
    "tp.equipment.import.batch",
    "tp.equipment.import.line",
    "tp.equipment.import.column",
    "tp.equipment.import.alias",
    "tp.equipment.reason.wizard",
    "tp.equipment.inventory.adjust",
    "tp.equipment.move.reverse",
    "tp.equipment.quick.action",
)

GENERIC_DENIED = "Bạn không có quyền truy cập Kho thiết bị văn phòng. Liên hệ quản trị hệ thống nếu cần."

ASSET_CLASS = [
    ("device", "Thiết bị"),
    ("component", "Linh kiện / phụ kiện"),
    ("service", "Dịch vụ / đường truyền"),
]
OWNERSHIP = [
    ("company", "Công ty"),
    ("rented", "Thuê"),
    ("personal", "Cá nhân tự trang bị"),
    ("third_party", "Đơn vị / bên khác"),
    ("unknown", "Chưa xác định"),
]
LIFECYCLE = [
    ("draft", "Nháp"),
    ("active", "Đang quản lý"),
    ("retired", "Ngừng quản lý"),
]
RETIRE_REASON = [
    ("scrapped", "Thanh lý / hủy"),
    ("lost", "Mất"),
    ("rental_returned", "Đã trả bên cho thuê"),
    ("returned_owner", "Đã trả chủ sở hữu"),
    ("other", "Lý do khác"),
]
CUSTODY = [
    ("stock", "Trong kho"),
    ("employee", "Nhân viên giữ"),
    ("department", "Phòng ban dùng chung"),
    ("location", "Đặt tại vị trí"),
    ("loan", "Đang cho mượn"),
    ("vendor", "Tại nhà cung cấp / sửa ngoài"),
    ("none", "Không còn quản lý"),
]
TECH_STATE = [
    ("unverified", "Chưa xác minh"),
    ("good", "Tốt"),
    ("limited", "Hạn chế"),
    ("broken", "Hỏng"),
]
VERIFICATION = [
    ("source", "Chưa kiểm tra thực tế"),
    ("verified", "Đã xác minh thực tế"),
]
AVAILABILITY = [
    ("draft", "Chưa đăng ký"),
    ("available", "Sẵn sàng cấp phát"),
    ("check", "Cần kiểm tra trước khi cấp"),
    ("reserved", "Đang chờ bàn giao"),
    ("in_use", "Đang sử dụng"),
    ("repair", "Đang sửa chữa"),
    ("blocked", "Không cấp được (hỏng)"),
    ("retired", "Ngừng quản lý"),
]
WARRANTY_BASIS = [
    ("unknown", "Chưa xác định"),
    ("none", "Không bảo hành"),
    ("date", "Theo ngày hết hạn"),
    ("duration", "Theo thời hạn (tháng)"),
    ("meter", "Theo số đếm"),
    ("date_or_meter", "Thời hạn hoặc số đếm (điều kiện đến trước)"),
]
WARRANTY_STATE = [
    ("none", "Không áp dụng"),
    ("unknown", "Chưa xác định"),
    ("active", "Còn bảo hành"),
    ("expiring", "Sắp hết bảo hành"),
    ("expired", "Hết bảo hành"),
]
HOLDING_CUSTODY = ("employee", "department", "location", "loan")


def fold_text(value):
    """Lower-case text without Vietnamese tone/diacritic marks, for lenient *search only*.

    "Thùy", "Thuỳ" and "Thúy" all fold to "thuy" and "Đ" to "d". Never use it to link or
    confirm an identity: matching a person stays an explicit admin decision.
    """
    text = unicodedata.normalize("NFD", str(value or "")).replace("đ", "d").replace("Đ", "D")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text).strip().lower()


def is_admin(env):
    """Active internal user with system rights (superuser included for install/cron)."""
    if env.su:
        return True
    user = env.user
    return bool(user.active and not user.share and user.has_group(ADMIN_GROUP))


def check_admin(env, records=None):
    if is_admin(env):
        return
    # Delegation is checked on an audited source model, never on the environment alone.
    if records is not None and hasattr(records, "_tp_equipment_delegate_check"):
        records._tp_equipment_delegate_check()
        return
    raise AccessError(GENERIC_DENIED)


def lock_records(records):
    """Serialize state transitions and refresh their preconditions after acquiring the lock."""
    check_admin(records.env, records)
    records.check_access("write")
    if not records:
        return
    try:
        with records.env.cr.savepoint(flush=False):
            records.env.cr.execute(SQL("SELECT id FROM %s WHERE id IN %s ORDER BY id FOR UPDATE NOWAIT",
                                      SQL.identifier(records._table), tuple(records.ids)))
    except pg_errors.LockNotAvailable:
        raise UserError(_("Hồ sơ đang được xử lý ở thao tác khác. Thử lại sau ít giây.")) from None
    records.invalidate_recordset()


def admin_partner_ids(env, partner_ids):
    """Keep only partners linked to an active system administrator.

    External partners and non-admin users are never followers or recipients of equipment
    records, so chatter, inbox notifications and e-mails cannot leak equipment data.
    """
    if not partner_ids:
        return []
    ids = [pid for pid in partner_ids if isinstance(pid, int)]
    if not ids:
        return []
    admin_group = env.ref(ADMIN_GROUP)
    users = env["res.users"].sudo().search([
        ("partner_id", "in", ids),
        ("active", "=", True),
        ("share", "=", False),
        ("all_group_ids", "in", admin_group.ids),
    ])
    allowed = set(users.partner_id.ids)
    return [pid for pid in ids if pid in allowed]


def admin_user_domain(env):
    return [("share", "=", False), ("all_group_ids", "in", env.ref(ADMIN_GROUP).ids)]


class TpEquipmentSecureMixin(models.AbstractModel):
    """Chatter + guards for the module's own models (not used for native maintenance models)."""

    _name = "tp.equipment.secure.mixin"
    _description = "Kho thiết bị — bảo vệ chatter và quyền"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def _make_access_error_message(self, operation, domain):
        if not is_admin(self.env):
            return AccessError(GENERIC_DENIED)
        return super()._make_access_error_message(operation, domain)

    def _message_subscribe(self, partner_ids=None, subtype_ids=None, customer_ids=None):
        partner_ids = admin_partner_ids(self.env, partner_ids)
        if customer_ids:
            customer_ids = [pid for pid in customer_ids if pid in partner_ids]
        return super()._message_subscribe(partner_ids, subtype_ids, customer_ids=customer_ids)

    def message_post(self, **kwargs):
        if kwargs.get("partner_ids"):
            kwargs["partner_ids"] = admin_partner_ids(self.env, list(kwargs["partner_ids"]))
        if kwargs.get("partner_cc_ids"):
            kwargs["partner_cc_ids"] = admin_partner_ids(self.env, list(kwargs["partner_cc_ids"]))
        kwargs.pop("outgoing_email_to", None)
        return super().message_post(**kwargs)

    def _notify_get_recipients(self, message, **kwargs):
        recipients = super()._notify_get_recipients(message, **kwargs)
        allowed = set(admin_partner_ids(self.env, [r["id"] for r in recipients]))
        return [r for r in recipients if r["id"] in allowed]

    def _message_get_suggested_recipients(self, *args, **kwargs):
        return []


def guard_native_mail(cls):
    """Add the same guards to a native model extension class (maintenance.*)."""

    def _make_access_error_message(self, operation, domain):
        if not is_admin(self.env):
            return AccessError(GENERIC_DENIED)
        return super(cls, self)._make_access_error_message(operation, domain)

    def _message_subscribe(self, partner_ids=None, subtype_ids=None, customer_ids=None):
        partner_ids = admin_partner_ids(self.env, partner_ids)
        if customer_ids:
            customer_ids = [pid for pid in customer_ids if pid in partner_ids]
        return super(cls, self)._message_subscribe(partner_ids, subtype_ids, customer_ids=customer_ids)

    def message_post(self, **kwargs):
        if kwargs.get("partner_ids"):
            kwargs["partner_ids"] = admin_partner_ids(self.env, list(kwargs["partner_ids"]))
        if kwargs.get("partner_cc_ids"):
            kwargs["partner_cc_ids"] = admin_partner_ids(self.env, list(kwargs["partner_cc_ids"]))
        kwargs.pop("outgoing_email_to", None)
        return super(cls, self).message_post(**kwargs)

    def _notify_get_recipients(self, message, **kwargs):
        recipients = super(cls, self)._notify_get_recipients(message, **kwargs)
        allowed = set(admin_partner_ids(self.env, [r["id"] for r in recipients]))
        return [r for r in recipients if r["id"] in allowed]

    def _message_get_suggested_recipients(self, *args, **kwargs):
        return []

    for name, func in {
        "_make_access_error_message": _make_access_error_message,
        "_message_subscribe": _message_subscribe,
        "message_post": message_post,
        "_notify_get_recipients": _notify_get_recipients,
        "_message_get_suggested_recipients": _message_get_suggested_recipients,
    }.items():
        if name not in cls.__dict__:
            setattr(cls, name, func)
    return cls


class MailActivity(models.Model):
    _inherit = "mail.activity"

    @api.constrains("res_model", "user_id")
    def _check_tp_equipment_assignee(self):
        for activity in self.sudo():
            if activity.res_model in TP_EQUIPMENT_MODELS and activity.user_id:
                user = activity.user_id
                if user.share or not user.active or not user.has_group(ADMIN_GROUP):
                    raise UserError(_("Việc cần làm của Kho thiết bị văn phòng chỉ giao cho quản trị hệ thống."))


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.constrains("res_model", "public")
    def _check_tp_equipment_private(self):
        for attachment in self.sudo():
            if attachment.res_model in TP_EQUIPMENT_MODELS and attachment.public:
                raise UserError(_("Tệp của Kho thiết bị văn phòng không được công khai."))
