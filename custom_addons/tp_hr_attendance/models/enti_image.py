"""Employee profile image synchronization from ENTI to Odoo HR (ENTI-IMAGE-SYNC-001).

Stores per-employee ENTI image metadata in ``tp.hr.attendance.enti.employee.image``, validates and
normalizes downloaded/base64 images on the server (host allowlist, Content-Type ``image/*``, size limit,
magic bytes, Pillow re-encode stripping metadata/scripts), and updates ``hr.employee.image_1920`` plus
the linked account partner ``res.partner.image_1920`` ONLY for confirmed 1-1 mapped employees.

Never stores ``access_token``, ``refresh_token``, passwords or cookies in the database or logs.
Never rolls back or deletes attendance records when an image fails.
"""
import base64
import binascii
import hashlib
import json
import logging
from io import BytesIO
from urllib.parse import urlsplit, urlunsplit

from PIL import Image, ImageOps, UnidentifiedImageError

from odoo import api, fields, models
from odoo.exceptions import UserError

from .attendance_common import (
    can_manage_enti_images,
    check_enti_image_access,
    deny_direct,
    internal,
    is_internal,
)
from .enti_client import (
    DEFAULT_MAX_IMAGE_BYTES,
    EntiError,
)
from .enti_mapping import MAPPING_STATES
from odoo.addons.tp_hr_workspace.models.identity import _IDENTITY, image_kind

__all__ = [
    "AttendanceEntiEmployeeImage",
    "can_manage_enti_images",
    "check_enti_image_access",
    "detect_magic_mime",
    "parse_image_value",
    "redact_image_url",
    "sanitize_employee_metadata",
    "validate_and_normalize_image",
]

_logger = logging.getLogger(__name__)

PARAM_MAX_IMAGE_BYTES = "tp_hr_attendance.enti_max_image_bytes"
PARAM_PREFER_MANUAL_IMAGE = "tp_hr_attendance.enti_prefer_manual_image"
PARAM_ALLOWED_IMAGE_HOSTS = "tp_hr_attendance.enti_allowed_image_hosts"
MAX_DIMENSION = 1920

FORBIDDEN_META_KEYS = frozenset({
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "cookie",
    "cookies",
    "authorization",
    "auth",
})

IMAGE_STATES = [
    ("pending", "Chờ đồng bộ / Chưa đối chiếu"),
    ("downloaded", "Đã đồng bộ"),
    ("unchanged", "Không thay đổi"),
    ("failed", "Lỗi tải ảnh"),
    ("no_image", "Chưa có ảnh"),
]

IMAGE_SOURCES = [
    ("none", "Chưa có ảnh"),
    ("base64", "Base64 (API ENTI)"),
    ("url", "URL (API ENTI)"),
]


def detect_magic_mime(raw_bytes):
    """Inspect magic bytes of ``raw_bytes``; return real MIME type or ``None`` if not a valid image."""
    if not isinstance(raw_bytes, (bytes, bytearray)) or len(raw_bytes) < 8:
        return None
    header = bytes(raw_bytes[:16])
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    return None


def parse_image_value(raw_value, max_bytes=DEFAULT_MAX_IMAGE_BYTES):
    """Parse raw ENTI image value into ``(source_kind, ref_label, payload)``.

    - Empty value -> ``('none', '', None)``
    - HTTP/HTTPS or relative ``/...`` URL -> ``('url', url_str, None)``
    - Data URI ``data:<mime>;base64,<data>`` or raw Base64 -> ``('base64', ref_label, (decoded_bytes, declared_mime))``
    """
    text = str(raw_value or "").strip()
    if not text or text in ("null", "None", "-"):
        return "none", "", None

    max_bytes = max(1024, int(max_bytes or DEFAULT_MAX_IMAGE_BYTES))

    if text.startswith("data:"):
        if "," not in text:
            msg = "Chuỗi data URI ảnh không đúng định dạng."
            raise EntiError(msg)
        header, b64_part = text.split(",", 1)
        meta = header[5:].strip()
        parts = [p.strip().lower() for p in meta.split(";") if p.strip()]
        declared_mime = parts[0] if parts and "/" in parts[0] else ""
        if not declared_mime.startswith("image/"):
            raise EntiError(f"Content-Type trong data URI không hợp lệ ({declared_mime or 'trống'}); chỉ chấp nhận image/*.")
        if "base64" not in parts:
            msg = "Data URI ảnh phải được mã hóa base64."
            raise EntiError(msg)
        b64_clean = "".join(b64_part.split())
        # Base64 expands 3 bytes into 4 chars; reject early before allocating huge buffers.
        if len(b64_clean) > ((max_bytes + 3) * 4 // 3) + 64:
            raise EntiError(f"Dung lượng ảnh Base64 vượt quá giới hạn tối đa ({max_bytes} bytes).")
        try:
            raw_bytes = base64.b64decode(b64_clean, validate=True)
        except (binascii.Error, ValueError) as exc:
            msg = "Dữ liệu ảnh Base64 bị hỏng hoặc không hợp lệ."
            raise EntiError(msg) from exc
        if len(raw_bytes) > max_bytes:
            raise EntiError(f"Dung lượng ảnh ({len(raw_bytes)} bytes) vượt quá giới hạn tối đa ({max_bytes} bytes).")
        return "base64", f"data:{declared_mime};base64", (raw_bytes, declared_mime)

    lower = text.lower()
    if lower.startswith(("http://", "https://", "/")):
        return "url", text, None
    if "://" in lower or lower.startswith(("javascript:", "file:", "ftp:", "mailto:")):
        msg = "Giao thức nguồn ảnh không được phép; chỉ hỗ trợ HTTP/HTTPS hoặc Base64."
        raise EntiError(msg)

    b64_clean = "".join(text.split())
    if len(b64_clean) > ((max_bytes + 3) * 4 // 3) + 64:
        raise EntiError(f"Dung lượng ảnh Base64 vượt quá giới hạn tối đa ({max_bytes} bytes).")
    try:
        raw_bytes = base64.b64decode(b64_clean, validate=True)
    except (binascii.Error, ValueError) as exc:
        msg = "Nguồn ảnh không phải URL HTTP/HTTPS hay chuỗi Base64 hợp lệ."
        raise EntiError(msg) from exc
    if len(raw_bytes) > max_bytes:
        raise EntiError(f"Dung lượng ảnh ({len(raw_bytes)} bytes) vượt quá giới hạn tối đa ({max_bytes} bytes).")
    return "base64", "base64", (raw_bytes, None)


def validate_and_normalize_image(raw_bytes, declared_mime=None, max_bytes=DEFAULT_MAX_IMAGE_BYTES):
    """Verify Content-Type, size limit, magic bytes, and re-encode image into a clean JPEG/PNG."""
    if not raw_bytes:
        msg = "Dữ liệu ảnh trống."
        raise EntiError(msg)
    max_bytes = max(1024, int(max_bytes or DEFAULT_MAX_IMAGE_BYTES))
    if len(raw_bytes) > max_bytes:
        raise EntiError(f"Dung lượng ảnh ({len(raw_bytes)} bytes) vượt quá giới hạn tối đa ({max_bytes} bytes).")

    if declared_mime:
        clean_mime = declared_mime.split(";", 1)[0].strip().lower()
        if not clean_mime.startswith("image/"):
            raise EntiError(f"Content-Type không hợp lệ ({clean_mime}); chỉ chấp nhận image/*.")

    magic_mime = detect_magic_mime(raw_bytes)
    if not magic_mime:
        msg = "Tệp không có magic bytes của định dạng ảnh hợp lệ (JPEG, PNG, GIF, WEBP)."
        raise EntiError(msg)

    source_hash = hashlib.sha256(raw_bytes).hexdigest()
    try:
        with Image.open(BytesIO(raw_bytes)) as probe:
            probe.verify()
        with Image.open(BytesIO(raw_bytes)) as img:
            img.load()
            img = ImageOps.exif_transpose(img)
            if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
                img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
            has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
            out = BytesIO()
            if has_alpha:
                clean = img.convert("RGBA")
                clean.save(out, format="PNG", optimize=True)
                out_mime = "image/png"
            else:
                clean = img.convert("RGB")
                clean.save(out, format="JPEG", quality=90, optimize=True)
                out_mime = "image/jpeg"
            normalized_bytes = out.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        msg = "Không thể giải mã cấu trúc ảnh hợp lệ."
        raise EntiError(msg) from exc

    normalized_hash = hashlib.sha256(normalized_bytes).hexdigest()
    normalized_b64 = base64.b64encode(normalized_bytes).decode("ascii")
    return {
        "source_hash": source_hash,
        "normalized_bytes": normalized_bytes,
        "normalized_b64": normalized_b64,
        "normalized_hash": normalized_hash,
        "mime": out_mime,
        "magic_mime": magic_mime,
        "size": len(raw_bytes),
    }


def redact_image_url(url):
    """Strip userinfo, query parameters (tokens/signatures), and fragments before persisting URLs."""
    text = str(url or "").strip()
    if not text:
        return ""
    try:
        parts = urlsplit(text)
    except ValueError:
        return text.split("?", 1)[0].split("#", 1)[0]
    netloc = parts.netloc
    if "@" in netloc:
        netloc = netloc.rsplit("@", 1)[-1]
    return urlunsplit((parts.scheme, netloc, parts.path, "", ""))


def sanitize_employee_metadata(info, *, image_field="", image_source="none", image_hash="", image_mime="", image_size=0):
    """Build safe JSON metadata string without tokens, passwords, cookies, or raw base64 blobs."""
    if not isinstance(info, dict):
        return "{}"
    safe = {}
    for key, val in info.items():
        key_str = str(key)
        key_low = key_str.lower()
        if key_low in FORBIDDEN_META_KEYS or any(secret in key_low for secret in ("token", "password", "secret", "cookie")):
            continue
        if key_str.startswith("day") and key_str[3:].isdigit():
            continue
        if key_str == image_field or key_low in ("anh", "avatar", "avatarurl", "image", "imageurl", "photo", "photourl", "hinhanh"):
            if val:
                safe[key_str] = f"<{image_source}:{image_mime or 'unknown'}:{image_size}B:{image_hash[:12]}>"
            else:
                safe[key_str] = ""
            continue
        if isinstance(val, str) and val.lower().startswith(("http://", "https://")):
            safe[key_str] = redact_image_url(val)
        elif isinstance(val, (str, int, float, bool)) or val is None:
            safe[key_str] = val
        elif isinstance(val, dict):
            nested = {
                nk: nv for nk, nv in val.items()
                if str(nk).lower() not in FORBIDDEN_META_KEYS
                and not any(s in str(nk).lower() for s in ("token", "password", "secret", "cookie"))
                and (isinstance(nv, (str, int, float, bool)) or nv is None)
            }
            safe[key_str] = nested
    safe["_image_meta"] = {
        "field": image_field,
        "source": image_source,
        "hash": image_hash,
        "mime": image_mime,
        "size": image_size,
    }
    return json.dumps(safe, ensure_ascii=False, sort_keys=True)


def _raw_image_bytes(val):
    """Extract raw binary content from Odoo 20 Binary/BinaryValueAttachment, raw bytes, or base64 strings."""
    if not val:
        return b""
    if isinstance(val, (bytes, bytearray, memoryview)) or (hasattr(val, "__bytes__") and not isinstance(val, str)):
        raw = bytes(val)
    else:
        raw = str(val).encode("ascii")
    if detect_magic_mime(raw) or raw.lstrip().startswith((b"<?xml", b"<svg")):
        return raw
    try:
        return base64.b64decode(raw, validate=True)
    except Exception:  # noqa: BLE001
        return raw


class AttendanceEntiEmployeeImage(models.Model):
    _name = "tp.hr.attendance.enti.employee.image"
    _description = "Đồng bộ ảnh hồ sơ nhân viên ENTI"
    _order = "state asc, ten_nv asc, id asc"
    _check_company_auto = True

    source_id = fields.Many2one(
        "tp.hr.attendance.source",
        "Nguồn dữ liệu",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="source_id.company_id",
        store=True,
        string="Công ty",
        index=True,
    )
    mapping_id = fields.Many2one(
        "tp.hr.attendance.enti.mapping",
        "Bản ghi đối chiếu",
        ondelete="set null",
        index=True,
    )
    key_nv = fields.Char("Khóa nhân viên ENTI", required=True, index=True)
    ma_nv = fields.Char("Mã NV bên ENTI", index=True)
    ten_nv = fields.Char("Họ tên bên ENTI", index=True)
    ten_bp = fields.Char("Bộ phận bên ENTI")

    employee_id = fields.Many2one(
        "hr.employee",
        "Nhân viên Odoo",
        check_company=True,
        index=True,
        ondelete="set null",
    )
    employee_code = fields.Char(
        "Mã nhân viên Odoo",
        related="employee_id.tp_employee_code",
        readonly=True,
    )
    department_id = fields.Many2one(
        "hr.department",
        "Phòng ban",
        related="employee_id.department_id",
        store=True,
        readonly=True,
        index=True,
    )

    image_field = fields.Char("Trường ảnh ENTI", readonly=True)
    image_source = fields.Selection(IMAGE_SOURCES, "Loại nguồn ảnh", default="none", readonly=True)
    image_url = fields.Char(
        "URL / Nguồn ảnh ENTI",
        readonly=True,
        groups="base.group_no_one",
        help="Chỉ dành cho chẩn đoán kỹ thuật nội bộ; đã cắt bỏ tham số truy vấn/token.",
    )
    image_hash = fields.Char("Mã băm ảnh (SHA-256)", readonly=True, index=True)
    applied_odoo_hash = fields.Char("Mã băm ảnh đã lưu Odoo", readonly=True)
    image_mime = fields.Char("Định dạng MIME", readonly=True)
    image_size = fields.Integer("Dung lượng (bytes)", readonly=True)

    enti_image_1920 = fields.Image("Ảnh ENTI", max_width=1920, max_height=1920, attachment=True, readonly=True)
    enti_image_128 = fields.Image("Ảnh ENTI (nhỏ)", related="enti_image_1920", max_width=128, max_height=128, readonly=True)
    odoo_image_1920 = fields.Image("Ảnh hiện tại trong Odoo", related="employee_id.image_1920", readonly=True)
    odoo_image_128 = fields.Image("Ảnh Odoo (nhỏ)", related="employee_id.image_128", readonly=True)

    last_seen_at = fields.Datetime("Lần thấy gần nhất", readonly=True)
    downloaded_at = fields.Datetime("Thời điểm tải ảnh", readonly=True)
    mapping_state = fields.Selection(
        MAPPING_STATES,
        "Trạng thái đối chiếu",
        default="unmapped",
        readonly=True,
        index=True,
    )
    state = fields.Selection(
        IMAGE_STATES,
        "Trạng thái đồng bộ ảnh",
        default="pending",
        required=True,
        index=True,
    )
    status_label = fields.Char("Trạng thái hiển thị", compute="_compute_status_label")
    error_message = fields.Text("Chi tiết / Thông báo lỗi", readonly=True)
    raw_metadata_json = fields.Text(
        "Metadata hồ sơ ENTI (JSON)",
        readonly=True,
        groups="base.group_no_one",
    )

    _source_key_unique = models.Constraint(
        "UNIQUE(source_id, key_nv)",
        "Mỗi khóa nhân viên ENTI chỉ có một bản ghi đồng bộ ảnh trong cùng nguồn.",
    )
    _source_employee_unique = models.UniqueIndex(
        "(source_id, employee_id) WHERE employee_id IS NOT NULL",
        "Một nhân viên Odoo chỉ được gắn với một khóa nhân viên ENTI trong cùng nguồn.",
    )

    @api.depends("state", "mapping_state", "employee_id")
    def _compute_status_label(self):
        state_labels = {
            "pending": "Chờ đồng bộ",
            "downloaded": "Đã đồng bộ",
            "unchanged": "Không thay đổi",
            "failed": "Lỗi tải ảnh",
            "no_image": "Chưa có ảnh",
        }
        for rec in self:
            if rec.mapping_state != "mapped" or not rec.employee_id:
                rec.status_label = "Chưa đối chiếu"
            else:
                rec.status_label = state_labels.get(rec.state, rec.state or "")

    def _check_access_guard(self):
        if not self.env.su and not is_internal(self):
            deny_direct(self)

    @api.model_create_multi
    def create(self, vals_list):
        self._check_access_guard()
        return super().create(vals_list)

    def write(self, vals):
        self._check_access_guard()
        return super().write(vals)

    def unlink(self):
        self._check_access_guard()
        return super().unlink()

    def _tp_apply_image_to_employee(self, employee, normalized_b64, normalized_hash, *, prefer_manual=False, force=False):
        """Write normalized base64 image to ``hr.employee.image_1920`` and linked ``res.partner.image_1920``.

        Returns ``(applied: bool, status_state: str, note: str)``.
        Respects ``prefer_manual`` (do not overwrite a manually uploaded Odoo photo unless ``force=True``).
        """
        self.ensure_one()
        emp = employee.sudo().with_context(bin_size=False)
        kind = image_kind(emp)
        current_raw = _raw_image_bytes(emp.image_1920)
        current_hash = hashlib.sha256(current_raw).hexdigest() if current_raw else ""

        if kind == "photo" and current_hash == normalized_hash:
            # Ensure linked partner avatar also matches
            self._tp_sync_partner_avatar(emp, normalized_b64, normalized_hash)
            return False, "unchanged", "Ảnh hồ sơ trong Odoo đã khớp với ảnh ENTI."

        is_manual_photo = (
            kind == "photo"
            and bool(current_hash)
            and current_hash != (self.applied_odoo_hash or "")
            and current_hash != normalized_hash
        )
        if is_manual_photo and prefer_manual and not force:
            return False, "unchanged", "Giữ nguyên ảnh thủ công hiện có trong Odoo (đang bật Ưu tiên ảnh thủ công)."

        # Write to hr.employee and sync linked partner avatar
        self._tp_write_employee_and_partner_image(emp, normalized_b64, normalized_hash)
        return True, "downloaded", "Đã cập nhật ảnh hồ sơ nhân viên từ ENTI."

    def _tp_write_employee_and_partner_image(self, emp_sudo, normalized_b64, normalized_hash):
        """Safely write ``image_1920`` to ``hr.employee`` and linked account ``res.partner``."""
        try:
            emp_sudo.write({"image_1920": normalized_b64})
        except UserError:
            # Fallback when work_contact_id != user_id.partner_id in synthetic fixtures
            emp_sudo.with_context(_tp_identity=_IDENTITY).write({"image_1920": normalized_b64})
        self._tp_sync_partner_avatar(emp_sudo, normalized_b64, normalized_hash)

    def _tp_sync_partner_avatar(self, emp_sudo, normalized_b64, normalized_hash):
        user = emp_sudo.user_id.sudo() if emp_sudo.user_id else False
        partner = user.partner_id.sudo().with_context(bin_size=False) if user and user.partner_id else False
        if not partner:
            return
        # Only sync if this partner uniquely belongs to this employee/user
        linked_emps = self.env["hr.employee"].sudo().with_context(active_test=False).search([
            ("user_id", "=", user.id),
        ])
        if len(linked_emps) > 1 or len(partner.with_context(active_test=False).user_ids) > 1:
            return
        partner_raw = _raw_image_bytes(partner.image_1920)
        partner_hash = hashlib.sha256(partner_raw).hexdigest() if partner_raw else ""
        if partner_hash != normalized_hash:
            partner.with_context(_tp_identity=_IDENTITY).write({"image_1920": normalized_b64})

    def action_apply_to_employee(self):
        """Manual action for HR/Admin to apply the stored ENTI image of a mapped employee to Odoo."""
        self.ensure_one()
        check_enti_image_access(self.env, self.company_id)
        mapping = self.mapping_id or self.env["tp.hr.attendance.enti.mapping"].sudo().search([
            ("source_id", "=", self.source_id.id),
            ("key_nv", "=", self.key_nv),
        ], limit=1)
        if not mapping or mapping.state != "mapped" or not mapping.employee_id:
            raise UserError(self.env._("Chỉ cho phép cập nhật ảnh sau khi nhân viên đã được đối chiếu chính xác."))
        b64_img = self.with_context(bin_size=False).enti_image_1920
        if not b64_img:
            raise UserError(self.env._("Nhân viên này chưa có ảnh hợp lệ từ ENTI để cập nhật."))
        raw = _raw_image_bytes(b64_img)
        norm = validate_and_normalize_image(raw)
        clash = self.sudo().search([
            ("source_id", "=", self.source_id.id),
            ("employee_id", "=", mapping.employee_id.id),
            ("id", "!=", self.id),
        ], limit=1)
        if clash:
            raise UserError(self.env._(
                "Nhân viên %(emp)s đã gắn với khóa ảnh ENTI khác (%(code)s).",
                emp=mapping.employee_id.name,
                code=clash.ma_nv or clash.key_nv,
            ))
        self._tp_write_employee_and_partner_image(
            mapping.employee_id.sudo().with_context(bin_size=False),
            norm["normalized_b64"],
            norm["normalized_hash"],
        )
        now = fields.Datetime.now()
        internal(self.sudo()).write({
            "mapping_id": mapping.id,
            "employee_id": mapping.employee_id.id,
            "mapping_state": "mapped",
            "state": "downloaded",
            "applied_odoo_hash": norm["normalized_hash"],
            "downloaded_at": now,
            "error_message": False,
        })
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Đã cập nhật ảnh hồ sơ",
                "message": f"Đã cập nhật ảnh ENTI cho nhân viên {mapping.employee_id.name}.",
                "type": "success",
                "sticky": False,
            },
        }

    @api.model
    def _tp_on_mapping_changed(self, mapping, *, apply_if_pending=False):
        """Synchronize linked image record when an ENTI mapping changes state or employee."""
        if not mapping:
            return
        for rec in mapping:
            img_rec = self.sudo().search([
                ("source_id", "=", rec.source_id.id),
                ("key_nv", "=", rec.key_nv),
            ], limit=1)
            if not img_rec:
                continue
            is_mapped = rec.state == "mapped" and bool(rec.employee_id)
            target_emp_id = rec.employee_id.id if is_mapped else False
            if target_emp_id:
                clash = self.sudo().search([
                    ("source_id", "=", rec.source_id.id),
                    ("employee_id", "=", target_emp_id),
                    ("id", "!=", img_rec.id),
                ], limit=1)
                if clash:
                    internal(img_rec).write({
                        "mapping_id": rec.id,
                        "employee_id": False,
                        "mapping_state": rec.state,
                        "state": "failed",
                        "error_message": (
                            f"Xung đột đối chiếu: nhân viên {rec.employee_id.name} đã gắn với khóa ENTI khác "
                            f"({clash.ma_nv or clash.key_nv})."
                        ),
                    })
                    continue
            vals = {
                "mapping_id": rec.id,
                "employee_id": target_emp_id,
                "mapping_state": rec.state,
            }
            if not is_mapped and img_rec.state in ("downloaded", "unchanged"):
                vals["state"] = "pending" if img_rec.with_context(bin_size=True).enti_image_1920 else "no_image"
            if is_mapped and apply_if_pending and img_rec.state == "pending":
                b64_img = img_rec.with_context(bin_size=False).enti_image_1920
                if b64_img:
                    try:
                        with self.env.cr.savepoint():
                            raw = _raw_image_bytes(b64_img)
                            norm = validate_and_normalize_image(raw)
                            prefer_manual = bool(getattr(rec.source_id, "prefer_manual_image", False))
                            applied, new_state, note = img_rec._tp_apply_image_to_employee(
                                rec.employee_id,
                                norm["normalized_b64"],
                                norm["normalized_hash"],
                                prefer_manual=prefer_manual,
                            )
                            vals["state"] = new_state
                            vals["error_message"] = False if applied else note
                            if applied:
                                vals["applied_odoo_hash"] = norm["normalized_hash"]
                                vals["downloaded_at"] = fields.Datetime.now()
                    except Exception as exc:  # noqa: BLE001
                        vals["state"] = "failed"
                        vals["error_message"] = str(exc)[:240]
            internal(img_rec).write(vals)
