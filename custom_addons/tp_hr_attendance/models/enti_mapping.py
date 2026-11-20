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

    _key_unique = models.Constraint(
        "UNIQUE(source_id, key_nv)",
        "Khóa nhân viên ENTI đã tồn tại trong nguồn này.",
    )
    _employee_unique = models.UniqueIndex(
        "(source_id, employee_id) WHERE state = 'mapped' AND employee_id IS NOT NULL AND active",
        "Một nhân viên Odoo chỉ được gắn với một mã chấm công ENTI trong cùng nguồn.",
    )

    def _check_hr_manager(self):
        if not self.env.user.has_group("hr.group_hr_manager") and not self.env.su:
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

    def action_reject_mapping(self):
        """Reject suggested mapping and move back to unmapped."""
        self._check_hr_manager()
        for rec in self:
            rec.write({
                "employee_id": False,
                "state": "unmapped",
                "match_reason": "Bị từ chối đối chiếu tự động; chờ đối chiếu thủ công.",
            })

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
