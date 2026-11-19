"""Employee mapping between ENTI external records and Odoo HR employees (ENTI-LIVE-001, DEC-044).

Odoo HR is the single source of truth for employee profiles, internal codes,
departments, and permissions. ENTI is only an external identity and attendance feed.
"""
import unicodedata

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

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
        """Confirm suggestion or manual mapping."""
        self._check_hr_manager()
        for rec in self:
            if not rec.employee_id:
                raise UserError(self.env._("Vui lòng chọn nhân viên Odoo trước khi xác nhận."))
            rec.write({
                "state": "mapped",
                "match_reason": rec.match_reason or "Người quản lý xác nhận đối chiếu thủ công.",
            })
            # Trigger retroactive projection of stored ENTI days for this employee
            self.env["tp.hr.attendance.enti.day"]._tp_project_for_mapping(rec)

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

    def _match_and_apply(self):
        """Match one record against hr.employee in company."""
        self.ensure_one()
        source = self.source_id
        company = source.company_id
        ten_nv = (self.ten_nv or "").strip()
        ma_nv = (self.ma_nv or "").strip()
        Employee = self.env["hr.employee"].sudo()

        matched_emp = False
        state = "unmapped"
        reason = "Chưa tìm thấy nhân viên phù hợp trong Odoo HR."

        norm_name = unicodedata.normalize("NFC", ten_nv).lower() if ten_nv else ""
        if norm_name:
            all_emps = Employee.search([("company_id", "=", company.id)])
            name_matches = all_emps.filtered(
                lambda e: unicodedata.normalize("NFC", (e.name or "").strip()).lower() == norm_name
            )
            if len(name_matches) == 1:
                matched_emp = name_matches[0]
                state = "mapped"
                reason = f"Khớp chính xác họ tên 1-1 trong Odoo HR ({matched_emp.name})."
            elif len(name_matches) > 1:
                by_code = name_matches.filtered(lambda e: e.tp_employee_code == ma_nv)
                if by_code:
                    matched_emp = by_code[0]
                    state = "mapped"
                    reason = f"Khớp chính xác họ tên và mã nhân viên ({matched_emp.name})."
                else:
                    state = "suggested"
                    reason = f"Có {len(name_matches)} nhân viên trùng họ tên trong Odoo. Chờ người quản lý xác nhận."

        self.sudo().write({
            "employee_id": matched_emp.id if matched_emp else False,
            "state": state,
            "match_reason": reason,
        })
        if state == "mapped" and matched_emp:
            self.env["tp.hr.attendance.enti.day"]._tp_project_for_mapping(self)

    @api.model
    def tp_suggest_mapping(self, source, enti_employee):
        """Analyze one ENTI employee object and propose or create mapping.

        enti_employee contains: keyNV, maNV, tenNV/hoVaTen, keyBP/keyBoPhan, tenBP/tenBoPhan.
        Rules:
        - NEVER alter hr.employee codes or names.
        - NEVER match solely on fuzzy name.
        - Match exact name + code correlation -> suggested or mapped.
        - Match exact name -> suggested or mapped.
        - Otherwise -> unmapped.
        """
        key_nv = (enti_employee.get("keyNV") or "").strip()
        if not key_nv:
            return None

        ma_nv = (enti_employee.get("maNV") or "").strip()
        ten_nv = (enti_employee.get("tenNV") or enti_employee.get("hoVaTen") or "").strip()
        key_bp = (enti_employee.get("keyBP") or enti_employee.get("keyBoPhan") or "").strip()
        ten_bp = (enti_employee.get("tenBP") or enti_employee.get("tenBoPhan") or "").strip()
        now = fields.Datetime.now()

        existing = self.search([("source_id", "=", source.id), ("key_nv", "=", key_nv)], limit=1)
        if existing:
            # Update observation metadata
            existing.sudo().write({
                "ma_nv": ma_nv or existing.ma_nv,
                "ten_nv": ten_nv or existing.ten_nv,
                "key_bp": key_bp or existing.key_bp,
                "ten_bp": ten_bp or existing.ten_bp,
                "last_seen_at": now,
            })
            if existing.state != "mapped" or not existing.employee_id:
                existing._match_and_apply()
            return existing

        # Find matching employee in Odoo
        Employee = self.env["hr.employee"].sudo()
        company = source.company_id
        matched_emp = False
        state = "unmapped"
        reason = "Chưa tìm thấy nhân viên phù hợp trong Odoo HR."

        norm_name = unicodedata.normalize("NFC", ten_nv).lower() if ten_nv else ""
        if norm_name:
            all_emps = Employee.search([("company_id", "=", company.id)])
            name_matches = all_emps.filtered(
                lambda e: unicodedata.normalize("NFC", (e.name or "").strip()).lower() == norm_name
            )
            if len(name_matches) == 1:
                matched_emp = name_matches[0]
                state = "mapped"
                reason = f"Khớp chính xác họ tên 1-1 trong Odoo HR ({matched_emp.name})."
            elif len(name_matches) > 1:
                by_code = name_matches.filtered(lambda e: e.tp_employee_code == ma_nv)
                if by_code:
                    matched_emp = by_code[0]
                    state = "mapped"
                    reason = f"Khớp chính xác họ tên và mã nhân viên ({matched_emp.name})."
                else:
                    state = "suggested"
                    reason = f"Có {len(name_matches)} nhân viên trùng họ tên trong Odoo. Chờ người quản lý xác nhận."

        vals = {
            "source_id": source.id,
            "key_nv": key_nv,
            "ma_nv": ma_nv,
            "ten_nv": ten_nv,
            "key_bp": key_bp,
            "ten_bp": ten_bp,
            "employee_id": matched_emp.id if matched_emp else False,
            "state": state,
            "match_reason": reason,
            "last_seen_at": now,
        }
        res = self.sudo().create(vals)
        if state == "mapped" and matched_emp:
            self.env["tp.hr.attendance.enti.day"]._tp_project_for_mapping(res)
        return res
        return self.sudo().create(vals)
