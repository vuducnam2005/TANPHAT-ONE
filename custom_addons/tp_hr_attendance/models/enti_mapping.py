"""Employee mapping between ENTI external records and Odoo HR employees (ENTI-LIVE-001, DEC-044).

Odoo HR is the single source of truth for employee profiles, internal codes,
departments, and permissions. ENTI is only an external identity and attendance feed.

ENTI-ATTENDANCE-002: automatic matching only accepts an exact (Unicode/whitespace-normalised) full name that is
unique in the company, or an exact name plus the same employee code; anything else waits for an HR manager, who
is recorded as the confirmer. One Odoo employee can never be linked to two ENTI keys of the same source. A poll
writes a mapping only when ENTI metadata or the match result changed.
"""
import unicodedata
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

SEEN_REFRESH = timedelta(hours=1)


def _norm(name):
    """Exact-name key: Unicode NFC, collapsed whitespace, lower case (no accent stripping, no fuzzy match)."""
    return " ".join(unicodedata.normalize("NFC", name or "").split()).lower()


MAPPING_STATES = [
    ("mapped", "Đã khớp"),
    ("suggested", "Chờ xác nhận"),
    ("unmapped", "Chưa đối chiếu"),
]


class AttendanceEntiMapping(models.Model):
    _name = "tp.hr.attendance.enti.mapping"
    _description = "Đối chiếu nhân viên ENTI - Odoo"
    _order = "state desc, ten_nv, id"
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
    key_nv = fields.Char(
        "Khóa nhân viên ENTI (UUID)",
        required=True,
        index=True,
        help="Định danh duy nhất của nhân viên bên ENTI.",
    )
    ma_nv = fields.Char("Mã NV bên ENTI", index=True)
    ten_nv = fields.Char("Họ tên bên ENTI", required=True, index=True)
    key_bp = fields.Char("Khóa bộ phận ENTI")
    ten_bp = fields.Char("Bộ phận bên ENTI")

    employee_id = fields.Many2one(
        "hr.employee",
        "Nhân viên Odoo",
        check_company=True,
        index=True,
        help="Hồ sơ nhân viên chính thức trong Odoo HR.",
    )
    employee_code = fields.Char(
        "Mã nhân viên Odoo",
        related="employee_id.tp_employee_code",
        readonly=True,
    )
    employee_department = fields.Char(
        "Phòng ban Odoo",
        related="employee_id.department_id.name",
        readonly=True,
    )

    state = fields.Selection(
        MAPPING_STATES,
        "Trạng thái đối chiếu",
        default="unmapped",
        required=True,
        index=True,
    )
    match_reason = fields.Char("Căn cứ đối chiếu / Lý do", readonly=True)
    last_seen_at = fields.Datetime("Lần thấy gần nhất", readonly=True)
    active = fields.Boolean("Đang theo dõi", default=True)

    image_record_id = fields.Many2one(
        "tp.hr.attendance.enti.employee.image",
        "Bản ghi ảnh ENTI",
        compute="_compute_image_fields",
    )
    has_enti_image = fields.Boolean("Có ảnh ENTI", compute="_compute_image_fields")
    enti_image_128 = fields.Image("Ảnh ENTI", compute="_compute_image_fields")
    enti_image_1920 = fields.Image("Ảnh ENTI (gốc)", compute="_compute_image_fields")
    odoo_image_128 = fields.Image(
        "Ảnh hiện tại trong Odoo",
        related="employee_id.image_128",
        readonly=True,
    )
    odoo_image_1920 = fields.Image(
        "Ảnh hiện tại trong Odoo (gốc)",
        related="employee_id.image_1920",
        readonly=True,
    )
    image_state = fields.Selection(
        [
            ("pending", "Chờ đồng bộ / Chưa đối chiếu"),
            ("downloaded", "Đã đồng bộ"),
            ("unchanged", "Không thay đổi"),
            ("failed", "Lỗi tải ảnh"),
            ("no_image", "Chưa có ảnh"),
        ],
        "Trạng thái ảnh",
        compute="_compute_image_fields",
    )
    image_status_label = fields.Char("Đồng bộ ảnh", compute="_compute_image_fields")
    image_synced_at = fields.Datetime("Thời điểm đồng bộ ảnh", compute="_compute_image_fields")
    image_error = fields.Text("Thông báo / Lỗi ảnh", compute="_compute_image_fields")

    _key_unique = models.Constraint(
        "UNIQUE(source_id, key_nv)",
        "Khóa nhân viên ENTI đã tồn tại trong nguồn này.",
    )
    _employee_unique = models.UniqueIndex(
        "(source_id, employee_id) WHERE state = 'mapped' AND employee_id IS NOT NULL AND active",
        "Một nhân viên Odoo chỉ được gắn với một mã chấm công ENTI trong cùng nguồn.",
    )

    @api.depends("source_id", "key_nv", "state", "employee_id")
    def _compute_image_fields(self):
        ImageModel = self.env["tp.hr.attendance.enti.employee.image"].sudo()
        source_ids = self.mapped("source_id").ids
        keys = [k for k in self.mapped("key_nv") if k]
        by_pair = {}
        if source_ids and keys:
            for img in ImageModel.search([("source_id", "in", source_ids), ("key_nv", "in", keys)]):
                by_pair[(img.source_id.id, img.key_nv)] = img
        for rec in self:
            img = by_pair.get((rec.source_id.id, rec.key_nv))
            rec.image_record_id = img.id if img else False
            rec.enti_image_128 = img.enti_image_128 if img else False
            rec.enti_image_1920 = img.enti_image_1920 if img else False
            rec.has_enti_image = bool(img and img.with_context(bin_size=True).enti_image_1920)
            rec.image_state = img.state if img else False
            if rec.state != "mapped" or not rec.employee_id:
                rec.image_status_label = "Chưa đối chiếu"
            elif img:
                rec.image_status_label = img.status_label
            else:
                rec.image_status_label = "Chưa đồng bộ"
            rec.image_synced_at = img.downloaded_at or img.last_seen_at if img else False
            rec.image_error = img.error_message if img else False

    def _check_hr_manager(self):
        from .enti_image import can_manage_enti_images
        if not can_manage_enti_images(self.env, self.company_id[:1] if self else self.env.company):
            raise AccessError(self.env._("Chỉ Quản lý nhân sự hoặc Admin mới được đối chiếu nhân viên."))

    @api.model_create_multi
    def create(self, vals_list):
        self._check_hr_manager()
        return super().create(vals_list)

    def write(self, vals):
        self._check_hr_manager()
        return super().write(vals)

    def action_confirm_mapping(self):
        """Confirm suggestion or manual mapping; the confirming manager is recorded as the evidence owner."""
        self._check_hr_manager()
        reason = self.env.context.get("tp_mapping_reason")
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.employee_id:
                raise UserError(self.env._("Vui lòng chọn nhân viên Odoo trước khi xác nhận."))
            clash = self.search([
                ("source_id", "=", rec.source_id.id),
                ("employee_id", "=", rec.employee_id.id),
                ("state", "=", "mapped"),
                ("id", "!=", rec.id),
            ], limit=1)
            if clash:
                raise UserError(self.env._(
                    "%(employee)s đã gắn với mã ENTI %(code)s (%(name)s). Gỡ đối chiếu đó trước khi gắn mã khác.",
                    employee=rec.employee_id.name, code=clash.ma_nv or clash.key_nv, name=clash.ten_nv,
                ))
            rec.write({
                "state": "mapped",
                "match_reason": reason or self.env._(
                    "%(user)s xác nhận đối chiếu ngày %(day)s.", user=self.env.user.name, day=today.strftime("%d/%m/%Y"),
                ),
            })
            # Trigger retroactive projection of stored ENTI days for this employee
            changed = self.env["tp.hr.attendance.enti.day"]._tp_project_for_mapping(rec)
            if changed:
                rec.source_id._tp_enti_notify(dates=changed.mapped("work_date"))
            self.env["tp.hr.attendance.enti.employee.image"]._tp_on_mapping_changed(rec, apply_if_pending=True)

    def action_reject_mapping(self):
        """Reject suggested mapping and move back to unmapped."""
        self._check_hr_manager()
        for rec in self:
            rec.write({
                "employee_id": False,
                "state": "unmapped",
                "match_reason": "Bị từ chối đối chiếu tự động; chờ đối chiếu thủ công.",
            })
            self.env["tp.hr.attendance.enti.employee.image"]._tp_on_mapping_changed(rec, apply_if_pending=False)

    def action_apply_enti_image(self):
        """Manually update the mapped Odoo employee's profile image from ENTI."""
        self.ensure_one()
        self._check_hr_manager()
        if self.state != "mapped" or not self.employee_id:
            raise UserError(self.env._("Chỉ cho phép cập nhật ảnh sau khi nhân viên đã được đối chiếu chính xác."))
        if not self.image_record_id:
            raise UserError(self.env._("Chưa có dữ liệu ảnh ENTI cho nhân viên này. Vui lòng chạy Đồng bộ ảnh hồ sơ trước."))
        return self.image_record_id.action_apply_to_employee()

    def action_open_image_compare(self):
        """Open form view with side-by-side ENTI and Odoo image comparison."""
        self.ensure_one()
        self._check_hr_manager()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Xem trước & Đối chiếu ảnh ENTI - Odoo"),
            "res_model": "tp.hr.attendance.enti.mapping",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_auto_match(self):
        """Re-run matching algorithm for records in self."""
        self._check_hr_manager()
        for rec in self:
            if rec.state == "mapped" and rec.employee_id:
                continue
            rec._match_and_apply()

    @api.model
    def _tp_name_index(self, company):
        """{normalised full name: [employee ids]} of the company's active employees."""
        index = {}
        for employee in self.env["hr.employee"].sudo().search([("company_id", "=", company.id)]):
            index.setdefault(_norm(employee.name), []).append(employee.id)
        return index

    @api.model
    def _tp_match(self, source, key_nv, ten_nv, ma_nv, index=None):
        """(employee, state, reason) for one ENTI identity. Never matches on a similar name."""
        Employee = self.env["hr.employee"].sudo()
        norm = _norm(ten_nv)
        if not norm:
            return Employee, "unmapped", "ENTI không trả họ tên cho mã này; cần quản lý nhân sự đối chiếu thủ công."
        if index is None:
            index = self._tp_name_index(source.company_id)
        matches = Employee.browse(index.get(norm, []))
        if not matches:
            return Employee, "unmapped", (
                f"Không có nhân viên Odoo nào trùng chính xác họ tên “{ten_nv}” (mã ENTI {ma_nv or '—'}); "
                "cần quản lý nhân sự đối chiếu."
            )
        taken = set(self.sudo().search([
            ("source_id", "=", source.id),
            ("state", "=", "mapped"),
            ("employee_id", "in", matches.ids),
            ("key_nv", "!=", key_nv),
        ]).employee_id.ids)
        free = matches.filtered(lambda e: e.id not in taken)
        if len(matches) == 1:
            if free:
                return free, "mapped", f"Khớp chính xác họ tên 1-1 trong Odoo HR ({free.name})."
            return Employee, "suggested", (
                f"Họ tên trùng “{matches.name}” nhưng nhân viên này đã gắn với một mã ENTI khác; cần quản lý nhân sự kiểm tra."
            )
        # HR-EMPLOYEE-CODE-003: ENTI maNV and the internal TP code are separate
        # number spaces (ENTI TP032 may belong to internal TP065), so a code that
        # looks the same never picks one of several same-name employees.
        return Employee, "suggested", (
            f"Có {len(matches)} nhân viên Odoo trùng họ tên “{ten_nv}”; cần quản lý nhân sự xác nhận đúng người."
        )

    def _match_and_apply(self, index=None):
        """Match one record against hr.employee in company; writes only when the result changed."""
        self.ensure_one()
        employee, state, reason = self._tp_match(self.source_id, self.key_nv, self.ten_nv, self.ma_nv, index)
        vals = {}
        # An employee picked by HR on a pending record stays until HR confirms or rejects it.
        if self.employee_id != employee and (state == "mapped" or not self.employee_id):
            vals["employee_id"] = employee.id or False
        if self.state != state:
            vals["state"] = state
        if self.match_reason != reason:
            vals["match_reason"] = reason
        if vals:
            self.sudo().write(vals)
            if state == "mapped" and employee:
                self.env["tp.hr.attendance.enti.day"]._tp_project_for_mapping(self)
            self.env["tp.hr.attendance.enti.employee.image"]._tp_on_mapping_changed(
                self,
                apply_if_pending=bool(state == "mapped" and employee),
            )
        return bool(vals)

    @api.model
    def tp_suggest_mapping(self, source, enti_employee, index=None, existing=None):
        """Analyze one ENTI employee object and propose or create mapping.

        enti_employee contains: keyNV, maNV, tenNV/hoVaTen, keyBP/keyBoPhan, tenBP/tenBoPhan.
        Rules:
        - NEVER alter hr.employee codes or names.
        - NEVER match solely on fuzzy name.
        - Exact unique name -> mapped; several same-name candidates -> suggested
          (the ENTI code is never compared with the internal TP code).
        - Otherwise -> unmapped, with the reason shown to HR.
        """
        key_nv = (enti_employee.get("keyNV") or "").strip()
        if not key_nv:
            return None

        meta = {
            "ma_nv": (enti_employee.get("maNV") or "").strip(),
            "ten_nv": (enti_employee.get("tenNV") or enti_employee.get("hoVaTen") or "").strip(),
            "key_bp": (enti_employee.get("keyBP") or enti_employee.get("keyBoPhan") or "").strip(),
            "ten_bp": (enti_employee.get("tenBP") or enti_employee.get("tenBoPhan") or "").strip(),
        }
        now = fields.Datetime.now()

        record = existing if existing is not None else self.search(
            [("source_id", "=", source.id), ("key_nv", "=", key_nv)], limit=1,
        )
        if record:
            vals = {name: value for name, value in meta.items() if value and value != (record[name] or "")}
            if not record.last_seen_at or now - record.last_seen_at >= SEEN_REFRESH:
                vals["last_seen_at"] = now
            if vals:
                record.sudo().write(vals)
            if record.state != "mapped" or not record.employee_id:
                record._match_and_apply(index)
            return record

        meta["ten_nv"] = meta["ten_nv"] or f"(ENTI {meta['ma_nv'] or key_nv[:8]})"
        employee, state, reason = self._tp_match(source, key_nv, meta["ten_nv"], meta["ma_nv"], index)
        record = self.sudo().create(dict(
            meta,
            source_id=source.id,
            key_nv=key_nv,
            employee_id=employee.id or False,
            state=state,
            match_reason=reason,
            last_seen_at=now,
        ))
        if state == "mapped" and employee:
            self.env["tp.hr.attendance.enti.day"]._tp_project_for_mapping(record)
        return record
