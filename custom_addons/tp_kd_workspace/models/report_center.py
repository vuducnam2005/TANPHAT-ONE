# ruff: noqa: E501, PLC0415
import base64
import io
from collections import defaultdict
from datetime import date, datetime, timedelta

import xlsxwriter

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .workspace import child_context, kd_leaf

PAGE_SIZES = (10, 20, 50, 100)
TAX_SHORT = {
    "before_tax": "trước thuế",
    "after_tax": "sau thuế",
    "unspecified": "chưa tách thuế",
}

REPORT_CATALOG = (
    {
        "key": "R01",
        "code": "R01",
        "title": "Dự án và hợp đồng",
        "short_title": "Dự án & Hợp đồng",
        "subtitle": "Theo dõi hợp đồng gốc, phụ lục, đính chính, hiệu lực và giá trị theo cơ sở thuế",
        "question": "Mỗi dự án có bao nhiêu hợp đồng/phiên bản, trạng thái hiệu lực và giá trị hợp đồng hiệu lực (tách khỏi bản gốc và phụ lục) là bao nhiêu?",
        "date_field_label": "Ngày hiệu lực / ngày ký phiên bản (effective_date / signed_date)",
        "basis_note": "Chỉ cộng giá trị tại phiên bản hiệu lực hiện hành (_effective_revision) có trạng thái tiền đã xác nhận, cùng tiền tệ và cơ sở thuế. Không cộng gộp các phiên bản (original/amendment/correction) và không tính bản nháp/đang rà soát/trả lại vào giá trị hiệu lực.",
        "unverified_note": "Giá trị quyết toán cuối cùng và doanh thu kế toán ghi sổ chưa có chứng từ xác minh trong phân hệ KH-KD.",
    },
    {
        "key": "R02",
        "code": "R02",
        "title": "Hồ sơ dự án và hồ sơ thầu",
        "short_title": "Hồ sơ dự án & Hồ sơ thầu",
        "subtitle": "Tổng hợp hồ sơ dự án theo bước chuẩn bị, dự án/tiền dự án, hạn nộp và người phụ trách",
        "question": "Các hồ sơ dự án và hồ sơ thầu (bao gồm cả hồ sơ dự án tiền dự án chưa gắn mã dự án) đang ở bước nào và hạn nộp ra sao?",
        "date_field_label": "Hạn nộp hồ sơ thầu (kd_deadline)",
        "basis_note": "Bao gồm cả hồ sơ dự án gắn dự án và hồ sơ dự án tiền dự án (tp_project_id = False) trong phạm vi quyền. Trạng thái 'Đã khai báo nộp — chưa xác minh' chỉ phản ánh khai báo nội bộ.",
        "unverified_note": "Chưa có căn cứ xác minh kết quả trúng/trượt thầu chính thức, tỷ lệ thắng thầu hoặc doanh thu thực tế từ hồ sơ dự án.",
    },
    {
        "key": "R03",
        "code": "R03",
        "title": "Kế hoạch, sản lượng, nghiệm thu và đề nghị thanh toán",
        "short_title": "Kế hoạch · Sản lượng · Nghiệm thu · Thanh toán",
        "subtitle": "Đối chiếu 4 giai đoạn độc lập theo kỳ, dự án và chiều thu/chi",
        "question": "Trong kỳ báo cáo, kế hoạch sản lượng, sản lượng thực hiện, nghiệm thu và đề nghị thu/chi của từng dự án đạt mức nào?",
        "date_field_label": "Kỳ kế hoạch/sản lượng (period_from–period_to), ngày nghiệm thu (acceptance_date), ngày đề nghị (request_date)",
        "basis_note": "Tách riêng 5 cột chỉ tiêu tiền: Kế hoạch sản lượng, Sản lượng thực hiện, Nghiệm thu, Đề nghị thu và Đề nghị chi. Tuyệt đối không cộng gộp các giai đoạn với nhau và không cộng Đề nghị thu với Đề nghị chi.",
        "unverified_note": "Tiền thực thu/thực chi ngân hàng, công nợ kế toán và doanh thu ghi sổ kế toán chưa có chứng từ hạch toán xác minh.",
    },
    {
        "key": "R04",
        "code": "R04",
        "title": "Giao khoán và thầu phụ",
        "short_title": "Giao khoán & Thầu phụ",
        "subtitle": "Phân tách giao khoán nội bộ/thầu phụ, cấp 1 (gốc) và cấp 2 (phân bổ con), cảnh báo vượt trần",
        "question": "Cơ cấu giao khoán nội bộ và thầu phụ theo dự án như thế nào, và có giao khoán cấp 1 nào bị phân bổ cấp 2 vượt trần?",
        "date_field_label": "Hạn thực hiện / rà soát giao khoán (date_due)",
        "basis_note": "Tổng giá trị giao khoán toàn báo cáo chỉ cộng các hồ sơ Cấp 1 (parent_id = False) đã xác nhận tiền cùng tiền tệ và cơ sở thuế. Giá trị phân bổ Cấp 2 được thống kê ở cột đối chiếu riêng, không cộng trùng Cấp 1 + Cấp 2.",
        "unverified_note": "Giá trị quyết toán thầu phụ cuối cùng và số tiền đã chi trả thực tế chưa có chứng từ kế toán xác minh.",
    },
    {
        "key": "R05",
        "code": "R05",
        "title": "Tình trạng xử lý và trách nhiệm hồ sơ",
        "short_title": "Tình trạng & Trách nhiệm",
        "subtitle": "Đối chiếu hồ sơ nháp, chờ rà soát, bị trả lại, quá hạn trên 10 nguồn nghiệp vụ KH-KD",
        "question": "Hồ sơ đang tồn đọng ở bước nào, ai phụ trách/rà soát, và phần 'Việc của tôi' khác gì với toàn phạm vi đang lọc?",
        "date_field_label": "Hạn xử lý hồ sơ (date_due / kd_deadline / date_deadline / effective_date)",
        "basis_note": "Mỗi hồ sơ định danh chỉ tính 1 lần vào Tổng số hồ sơ (không cộng trùng hồ sơ vừa đang rà soát vừa quá hạn). Tách rõ số liệu toàn phạm vi lọc và trách nhiệm trực tiếp của người đang đăng nhập.",
        "unverified_note": "Định mức thời gian xử lý chuẩn (SLA pháp lý ngoài hệ thống) chưa áp dụng tự động.",
    },
    {
        "key": "R06",
        "code": "R06",
        "title": "Năng lực, chứng chỉ và nghĩa vụ hồ sơ",
        "short_title": "Năng lực · Chứng chỉ · Nghĩa vụ",
        "subtitle": "Theo dõi thời hạn chứng chỉ (ngưỡng 30 ngày minh họa), lượt gắn hồ sơ dự án thầu và checklist nghĩa vụ",
        "question": "Những chứng chỉ nào hết hạn/sắp hết hạn, đang gắn vào bao nhiêu hồ sơ dự án thầu, và các nghĩa vụ bảo lãnh/pháp lý đã tập hợp đủ chưa?",
        "date_field_label": "Ngày hết hạn chứng chỉ (valid_to) / Hạn nghĩa vụ hồ sơ (date_due)",
        "basis_note": "Mỗi chứng chỉ chỉ tính 1 lần trong tổng số chứng chỉ định danh dù gắn vào nhiều hồ sơ dự án thầu; số hồ sơ dự án sử dụng được thống kê ở chỉ tiêu riêng. Chứng chỉ nhân sự tuân thủ quy tắc bảo mật theo người phụ trách/rà soát.",
        "unverified_note": "Trạng thái 'Còn hạn — chưa xác minh' và 'Đã kiểm tra nội bộ' là kết quả rà soát nội bộ, chưa thay thế xác thực pháp lý bên ngoài. Ngưỡng 30 ngày là ngưỡng cảnh báo minh họa.",
    },
)

CATALOG_BY_KEY = {item["key"]: item for item in REPORT_CATALOG}

REVIEW_STATE_LABELS = {
    "draft": ("Nháp", "neutral"),
    "in_review": ("Đang rà soát", "info"),
    "returned": ("Bị trả lại", "danger"),
    "review_complete": ("Hoàn tất rà soát", "success"),
    "cancelled": ("Đã hủy", "neutral"),
}

LIFECYCLE_LABELS = {
    "not_effective": ("Chưa hiệu lực", "neutral"),
    "effective": ("Đang hiệu lực", "success"),
    "suspended": ("Tạm dừng", "warning"),
    "execution_completed": ("Hoàn thành thực hiện", "success"),
    "liquidated": ("Đã thanh lý", "neutral"),
    "terminated": ("Đã chấm dứt", "neutral"),
}

SIGNATURE_LABELS = {
    "unsigned": ("Chưa ký", "neutral"),
    "signed_recorded": ("Đã ghi nhận bản ký", "info"),
}

AUTHORITY_LABELS = {
    "pending": ("Chờ xác nhận thẩm quyền", "warning"),
    "confirmed": ("Đã xác nhận thẩm quyền", "info"),
}

BID_STATE_LABELS = {
    "identified": ("Đã nhận diện", "info"),
    "preparation": ("Đang chuẩn bị", "progress"),
    "submitted": ("Đã khai báo nộp — chưa xác minh", "warning"),
}

RECONCILIATION_LABELS = {
    "unreconciled": ("Chưa đối chiếu", "warning"),
    "needs_evidence": ("Cần bổ sung chứng từ", "warning"),
    "pending": ("Chờ đối chiếu kế toán", "warning"),
    "missing_documents": ("Thiếu hồ sơ", "warning"),
    "internal_checked": ("Đã kiểm tra nội bộ — chưa ghi nhận thu/chi", "info"),
}

CHECKLIST_LABELS = {
    "missing": ("Chưa có hồ sơ", "warning"),
    "collecting": ("Đang tập hợp", "progress"),
    "internal_checked": ("Đã kiểm tra nội bộ — chưa xác minh pháp lý", "success"),
}

OBLIGATION_KIND_LABELS = {
    "contract_docs": "Hồ sơ hợp đồng / bàn giao",
    "retention": "Căn cứ giữ lại — chưa xác nhận",
    "warranty": "Hồ sơ bảo hành",
    "reconciliation": "Căn cứ công nợ — chưa xác nhận",
}

R05_SOURCES = (
    {"key": "allocation", "model": "tp.allocation", "label": "Giao khoán", "project": "project_id", "base": []},
    {"key": "production", "model": "tp.production", "label": "Sản lượng tự khai", "project": "project_id", "base": []},
    {"key": "acceptance", "model": "tp.acceptance", "label": "Hồ sơ nghiệm thu nội bộ", "project": "project_id", "base": []},
    {"key": "payment", "model": "tp.payment.request", "label": "Đề nghị thanh toán", "project": "project_id", "base": []},
    {"key": "plan", "model": "tp.periodic.plan", "label": "Kế hoạch định kỳ", "project": "project_id", "base": []},
    {"key": "credential", "model": "tp.credential", "label": "Năng lực / chứng chỉ", "project": "project_id", "base": []},
    {"key": "obligation", "model": "tp.obligation", "label": "Nghĩa vụ / hồ sơ thiếu", "project": "project_id", "base": []},
    {"key": "opportunity", "model": "crm.lead", "label": "Hồ sơ dự án / hồ sơ thầu", "project": "tp_project_id", "base": [("type", "=", "opportunity"), ("kd_accessible", "=", True)]},
    {"key": "task", "model": "project.task", "label": "Công việc / WBS", "project": "project_id", "base": []},
    {"key": "contract", "model": "tp.contract.revision", "label": "Phiên bản hợp đồng", "project": "project_id", "base": []},
)

TASK_STATE_LABELS = {
    "01_in_progress": ("Đang thực hiện", "progress"),
    "02_changes_requested": ("Yêu cầu chỉnh sửa", "warning"),
    "03_approved": ("Đã duyệt", "success"),
    "04_waiting_normal": ("Chờ xử lý", "info"),
    "1_done": ("Hoàn thành", "success"),
    "1_canceled": ("Đã hủy", "neutral"),
}


def _fmt_vn_number(val, decimals=0):
    if val is None:
        return "—"
    if decimals == 0 and float(val).is_integer():
        return f"{round(val):,}".replace(",", ".")
    formatted = f"{float(val):,.{decimals}f}"
    parts = formatted.split(".")
    parts[0] = parts[0].replace(",", ".")
    return ",".join(parts)


def _fmt_money(amount, currency_name, tax_basis=None):
    num_str = _fmt_vn_number(amount, 0 if float(amount).is_integer() else 2)
    suffix = f" ({TAX_SHORT.get(tax_basis, tax_basis)})" if tax_basis else ""
    return f"{num_str} {currency_name}{suffix}"


def _fmt_date(d):
    if not d:
        return "—"
    if isinstance(d, str):
        parts = d[:10].split("-")
        if len(parts) == 3:
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
        return d
    return d.strftime("%d/%m/%Y")


def _sanitize_excel_text(value):
    """Prevent CSV/Excel formula injection for strings starting with =, +, -, @, tab, CR, LF."""
    if value is None:
        return ""
    text = str(value)
    if text and (text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n"))):
        return "'" + text
    return text


class MoneyAccumulator:
    """Safely accumulate confirmed amounts separated by (currency_name, tax_basis)."""

    def __init__(self):
        self.buckets = defaultdict(float)
        self.confirmed_count = 0
        self.unconfirmed_count = 0
        self.mixed_count = 0
        self.forbidden_count = 0
        self.empty_count = 0

    def add_Cell(self, cell):
        if not cell or cell.get("state") == "not_applicable":
            return
        st = cell.get("state")
        if st == "forbidden":
            self.forbidden_count += 1
        elif st == "confirmed":
            key = (cell.get("currency") or "VND", cell.get("tax_basis") or "unspecified")
            self.buckets[key] += float(cell.get("amount") or 0.0)
            self.confirmed_count += 1
        elif st == "mixed_basis":
            self.mixed_count += 1
        elif st in ("unconfirmed", "incomplete"):
            self.unconfirmed_count += 1
        else:
            self.empty_count += 1

    def format_summary(self, empty_label="Chưa có khoản xác nhận"):
        if self.buckets:
            parts = [
                _fmt_money(amt, cur, basis if basis != "unspecified" else None)
                for (cur, basis), amt in sorted(self.buckets.items())
            ]
            text = " · ".join(parts)
            excluded = self.unconfirmed_count + self.mixed_count + self.forbidden_count
            if excluded:
                text += f" (loại {excluded} dòng chưa đủ điều kiện)"
            return text
        if self.forbidden_count and not (self.unconfirmed_count or self.mixed_count or self.empty_count):
            return "Không có quyền xem tiền"
        if self.unconfirmed_count or self.mixed_count:
            return "Chưa xác nhận / khác cơ sở thuế"
        if self.forbidden_count:
            return "Không có quyền xem tiền"
        return empty_label

    def to_dict(self, empty_label="Chưa có khoản xác nhận"):
        items = [
            {
                "currency": cur,
                "tax_basis": basis,
                "tax_label": TAX_SHORT.get(basis, basis),
                "amount": amt,
                "display": _fmt_money(amt, cur, basis if basis != "unspecified" else None),
            }
            for (cur, basis), amt in sorted(self.buckets.items())
        ]
        # Excel numeric value only when there is a single homogeneous (currency, tax_basis) bucket
        single_amount = items[0]["amount"] if len(items) == 1 else None
        return {
            "state": "confirmed" if items else (
                "forbidden" if self.forbidden_count and not (self.unconfirmed_count or self.mixed_count)
                else ("unconfirmed" if (self.unconfirmed_count or self.mixed_count) else "empty")
            ),
            "display": self.format_summary(empty_label=empty_label),
            "items": items,
            "single_amount": single_amount,
            "confirmed_count": self.confirmed_count,
            "unconfirmed_count": self.unconfirmed_count,
            "mixed_count": self.mixed_count,
            "forbidden_count": self.forbidden_count,
        }


class KdReportCenter(models.TransientModel):
    _name = "tp.kd.report.center"
    _description = "Trung tâm Báo cáo KH-KD"

    name = fields.Char(default="Báo cáo KH-KD")

    def _check_kd_access(self):
        if not self.env.user.has_group("tp_core.group_user"):
            raise AccessError(_("Bạn không có quyền truy cập Trung tâm Báo cáo KH-KD."))
        self.check_access("read")

    def _project_label(self, project):
        if not project:
            return "Chưa gắn dự án (tiền dự án)"
        return f"[{project.tp_code}] {project.name}" if project.tp_code else project.name

    def _accessible_projects(self):
        Project = self.env["project.project"]
        if not Project.has_access("read"):
            return Project.browse()
        return Project.search([], order="tp_code, name, id")

    def _financial_project_ids(self, projects):
        if not projects:
            return set()
        Grant = self.env["tp.project.grant"]
        Assign = self.env["tp.project.assignment"]
        assigned_pids = set(
            Assign.sudo().search([
                ("project_id", "in", projects.ids),
                ("user_id", "=", self.env.uid),
                ("active", "=", True),
            ]).mapped("project_id").ids,
        )
        allowed = set()
        for proj in projects:
            if (proj.id in assigned_pids or proj._tp_head_allowed()) and Grant._tp_has_capability(proj, "financial_read", user=self.env.user):
                allowed.add(proj.id)
        return allowed

    def _resolve_period(self, filters, today):
        filters = filters or {}
        preset = str(filters.get("period_preset") or "").strip()
        d_from_raw = str(filters.get("date_from") or "").strip()
        d_to_raw = str(filters.get("date_to") or "").strip()

        if preset == "this_month":
            d_from = today.replace(day=1)
            next_month = (d_from.replace(day=28) + timedelta(days=4)).replace(day=1)
            d_to = next_month - timedelta(days=1)
            preset_label = f"Tháng này ({_fmt_date(d_from)} – {_fmt_date(d_to)})"
        elif preset == "this_quarter":
            q_Index = (today.month - 1) // 3
            m_start = q_Index * 3 + 1
            d_from = date(today.year, m_start, 1)
            if m_start + 3 > 12:
                d_to = date(today.year, 12, 31)
            else:
                d_to = date(today.year, m_start + 3, 1) - timedelta(days=1)
            preset_label = f"Quý {q_Index + 1}/{today.year} ({_fmt_date(d_from)} – {_fmt_date(d_to)})"
        elif preset == "this_year":
            d_from = date(today.year, 1, 1)
            d_to = date(today.year, 12, 31)
            preset_label = f"Năm {today.year} ({_fmt_date(d_from)} – {_fmt_date(d_to)})"
        else:
            d_from = fields.Date.to_date(d_from_raw) if d_from_raw else None
            d_to = fields.Date.to_date(d_to_raw) if d_to_raw else None
            if d_from or d_to:
                preset = "custom"
                preset_label = f"Tùy chọn ({_fmt_date(d_from) if d_from else '...'} – {_fmt_date(d_to) if d_to else '...'})"
            else:
                preset = ""
                preset_label = "Tất cả kỳ"

        if d_from and d_to and d_from > d_to:
            raise ValidationError(_("Khoảng ngày không hợp lệ: 'Từ ngày' không được lớn hơn 'Đến ngày'."))
        return {
            "period_preset": preset,
            "period_label": preset_label,
            "date_from": str(d_from) if d_from else "",
            "date_to": str(d_to) if d_to else "",
            "d_from": d_from,
            "d_to": d_to,
        }

    def _parse_project_filter(self, filters, accessible_projects, allow_unassigned=False):
        raw = (filters or {}).get("project_id")
        if raw in (None, "", False, "all"):
            return {"mode": "all", "project_id": "", "label": "Tất cả dự án trong quyền"}
        if str(raw) == "unassigned":
            if not allow_unassigned:
                raise ValidationError(_("Báo cáo này không áp dụng lọc 'Chưa gắn dự án'."))
            return {"mode": "unassigned", "project_id": "unassigned", "label": "Chưa gắn dự án (tiền dự án)"}
        try:
            pid = int(raw)
        except (TypeError, ValueError) as err:
            raise ValidationError(_("Dự án lọc không hợp lệ.")) from err
        proj = accessible_projects.filtered(lambda p: p.id == pid)
        if not proj:
            raise AccessError(_("Bạn không có quyền xem dự án được chọn hoặc dự án không tồn tại."))
        return {"mode": "project", "project_id": pid, "project": proj[0], "label": self._project_label(proj[0])}

    def _parse_owner_filter(self, filters):
        raw = (filters or {}).get("owner_id")
        if raw in (None, "", False, "all"):
            return {"owner_id": "", "label": "Tất cả người phụ trách / rà soát"}
        try:
            uid = int(raw)
        except (TypeError, ValueError) as err:
            raise ValidationError(_("Người phụ trách không hợp lệ.")) from err
        user = self.env["res.users"].sudo().browse(uid).exists()
        if not user:
            raise ValidationError(_("Người phụ trách không tồn tại."))
        return {"owner_id": uid, "label": user.name}

    @staticmethod
    def _to_date(val):
        if not val:
            return None
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val
        if isinstance(val, str):
            try:
                return fields.Date.to_date(val[:10])
            except (ValueError, TypeError):
                return None
        return None

    def _date_in_range(self, target_date, d_from, d_to):
        d = self._to_date(target_date)
        df = self._to_date(d_from)
        dt = self._to_date(d_to)
        if not df and not dt:
            return True, False
        if not d:
            return False, True
        if df and d < df:
            return False, False
        if dt and d > dt:
            return False, False
        return True, False

    def _period_overlaps(self, p_from, p_to, d_from, d_to):
        pf = self._to_date(p_from)
        pt = self._to_date(p_to)
        df = self._to_date(d_from)
        dt = self._to_date(d_to)
        if not df and not dt:
            return True, False
        if not pf and not pt:
            return False, True
        start = pf or pt
        end = pt or pf
        if df and end < df:
            return False, False
        if dt and start > dt:
            return False, False
        return True, False

    def _revision_money_cell(self, rev, money_allowed):
        if not money_allowed:
            return {
                "state": "forbidden",
                "display": "Không có quyền xem tiền",
                "amount": None,
                "currency": None,
                "tax_basis": None,
                "tone": "neutral",
            }
        if not rev:
            return {
                "state": "empty",
                "display": "Chưa có phiên bản",
                "amount": None,
                "currency": None,
                "tax_basis": None,
                "tone": "neutral",
            }
        summary = rev._amount_summary()
        st = summary.get("status")
        if st == "confirmed":
            cur = summary["currency"].name if summary.get("currency") else "VND"
            basis = summary.get("tax_basis") or "unspecified"
            amt = float(summary.get("value") or 0.0)
            return {
                "state": "confirmed",
                "display": _fmt_money(amt, cur, basis),
                "amount": amt,
                "currency": cur,
                "tax_basis": basis,
                "tone": "info",
            }
        if st == "mixed_basis":
            return {
                "state": "mixed_basis",
                "display": "Khác cơ sở thuế (không cộng gộp)",
                "amount": None,
                "currency": None,
                "tax_basis": None,
                "tone": "warning",
            }
        if st == "incomplete":
            return {
                "state": "unconfirmed",
                "display": "Chưa xác nhận đủ dòng tiền",
                "amount": None,
                "currency": None,
                "tax_basis": None,
                "tone": "warning",
            }
        return {
            "state": "empty",
            "display": "Chưa kê khai tiền",
            "amount": None,
            "currency": None,
            "tax_basis": None,
            "tone": "neutral",
        }

    def _typed_money_cell(self, record, money_allowed, is_plan=False):
        if not money_allowed:
            return {
                "state": "forbidden",
                "display": "Không có quyền xem tiền",
                "amount": None,
                "currency": None,
                "tax_basis": None,
                "tone": "neutral",
            }
        if is_plan:
            prod_lines = record.amount_ids.filtered(lambda a: a.measure == "production")
            if not prod_lines:
                return {
                    "state": "empty",
                    "display": "Chưa kê khai chỉ tiêu sản lượng",
                    "amount": None,
                    "currency": None,
                    "tax_basis": None,
                    "tone": "neutral",
                }
            if any(a.amount_state != "confirmed" for a in prod_lines):
                return {
                    "state": "unconfirmed",
                    "display": "Chưa xác nhận tiền kế hoạch",
                    "amount": None,
                    "currency": None,
                    "tax_basis": None,
                    "tone": "warning",
                }
            currencies = set(prod_lines.mapped("currency_id.name"))
            bases = set(prod_lines.mapped("tax_basis"))
            if len(currencies) > 1 or len(bases) > 1:
                return {
                    "state": "mixed_basis",
                    "display": "Khác cơ sở thuế / tiền tệ",
                    "amount": None,
                    "currency": None,
                    "tax_basis": None,
                    "tone": "warning",
                }
            cur = next(iter(currencies)) if currencies else "VND"
            basis = next(iter(bases)) if bases else "unspecified"
            amt = sum(float(a.value or 0.0) for a in prod_lines)
            return {
                "state": "confirmed",
                "display": _fmt_money(amt, cur, basis),
                "amount": amt,
                "currency": cur,
                "tax_basis": basis,
                "tone": "info",
            }

        amt_rec = record.amount_ids[:1]
        if not amt_rec:
            return {
                "state": "empty",
                "display": "Chưa kê khai tiền",
                "amount": None,
                "currency": None,
                "tax_basis": None,
                "tone": "neutral",
            }
        if amt_rec.amount_state != "confirmed":
            return {
                "state": "unconfirmed",
                "display": "Chưa xác nhận tiền",
                "amount": None,
                "currency": None,
                "tax_basis": amt_rec.tax_basis,
                "tone": "warning",
            }
        cur = amt_rec.currency_id.name or "VND"
        basis = amt_rec.tax_basis or "unspecified"
        val = float(amt_rec.value or 0.0)
        return {
            "state": "confirmed",
            "display": _fmt_money(val, cur, basis),
            "amount": val,
            "currency": cur,
            "tax_basis": basis,
            "tone": "info",
        }

    def _na_money_cell(self, label="—"):
        return {
            "state": "not_applicable",
            "display": label,
            "amount": None,
            "currency": None,
            "tax_basis": None,
            "tone": "neutral",
        }

    # ------------------------------------------------------------------
    # R01: Dự án và hợp đồng
    # ------------------------------------------------------------------
    def _build_r01(self, filters, accessible_projects, fin_pids, period, proj_filter, owner_filter):
        Contract = self.env["tp.contract"]
        if not Contract.has_access("read"):
            raise AccessError(_("Bạn không có quyền đọc hồ sơ Hợp đồng."))

        status_filter = str((filters or {}).get("status") or "").strip()
        sub_filter = str((filters or {}).get("sub_filter") or "").strip()

        proj_domain = [("id", "in", accessible_projects.ids)]
        if proj_filter["mode"] == "project":
            proj_domain.append(("id", "=", proj_filter["project_id"]))
        scoped_projects = self.env["project.project"].search(proj_domain, order="tp_code, name, id")

        contract_domain = [("project_id", "in", scoped_projects.ids)]
        if sub_filter == "revenue":
            contract_domain.append(("contract_type", "in", ("owner", "general_contractor")))
        elif sub_filter == "cost":
            contract_domain.append(("contract_type", "=", "subcontractor"))
        elif sub_filter in ("owner", "general_contractor", "subcontractor"):
            contract_domain.append(("contract_type", "=", sub_filter))
        contracts = Contract.search(contract_domain, order="code, id")

        owners_map = {}
        rows = []
        missing_date_count = 0
        orig_acc = MoneyAccumulator()
        eff_acc = MoneyAccumulator()
        amend_acc = MoneyAccumulator()

        for proj in scoped_projects:
            if proj.user_id:
                owners_map[proj.user_id.id] = proj.user_id.name

        today = fields.Date.context_today(self)
        for c in contracts:
            revs = c.revision_ids.sorted(lambda r: (r.sequence, r.id))
            for r in revs:
                for sub in r.submission_ids:
                    if sub.submitted_by_id:
                        owners_map[sub.submitted_by_id.id] = sub.submitted_by_id.name
                    reviewer = sub.assigned_reviewer_id or sub.reviewer_id
                    if reviewer:
                        owners_map[reviewer.id] = reviewer.name
                owner = self.env["tp.contract.workflow"]._tp_business_owner(r)
                if owner:
                    owners_map[owner.id] = owner.name

            orig_rev = revs.filtered(lambda r: r.revision_kind == "original")[:1] or revs[:1]
            eff_candidates, _w = c._effective_revision(period["d_to"] or today)
            eff_rev = eff_candidates[:1]
            latest_rev = revs[-1:] if revs else self.env["tp.contract.revision"]
            amend_revs = revs.filtered(lambda r: r.revision_kind == "amendment" and r.review_state != "cancelled")
            corr_revs = revs.filtered(lambda r: r.revision_kind == "correction" and r.review_state != "cancelled")

            latest_sub = revs.submission_ids[-1:] if revs else self.env["tp.contract.submission"]
            owner_user = ((latest_sub.submitted_by_id if latest_sub else False) or
                          (self.env["tp.contract.workflow"]._tp_business_owner(latest_rev) if latest_rev else False) or c.project_id.user_id)
            reviewer_user = (latest_sub.assigned_reviewer_id or latest_sub.reviewer_id) if latest_sub else self.env["res.users"]

            if owner_filter["owner_id"]:
                uid = owner_filter["owner_id"]
                if owner_user.id != uid and reviewer_user.id != uid and c.project_id.user_id.id != uid:
                    continue

            ref_date = (
                (eff_rev.effective_date if eff_rev else None)
                or (latest_rev.effective_date if latest_rev else None)
                or (latest_rev.signed_date if latest_rev else None)
            )
            in_range, is_missing_date = self._date_in_range(ref_date, period["d_from"], period["d_to"])
            if not in_range:
                if is_missing_date:
                    missing_date_count += 1
                continue

            rev_state = latest_rev.review_state if latest_rev else "draft"
            life_state = c.lifecycle_state or "not_effective"
            if status_filter:
                if status_filter.startswith("review:"):
                    if rev_state != status_filter.split(":", 1)[1]:
                        continue
                elif status_filter.startswith("life:"):
                    if life_state != status_filter.split(":", 1)[1]:
                        continue
                elif status_filter != life_state and status_filter != rev_state:
                    continue

            money_allowed = c.project_id.id in fin_pids
            orig_cell = self._revision_money_cell(orig_rev, money_allowed)
            if eff_rev:
                eff_cell = self._revision_money_cell(eff_rev, money_allowed)
            elif not money_allowed:
                eff_cell = self._revision_money_cell(None, False)
            else:
                eff_cell = {
                    "state": "empty",
                    "display": "Chưa có phiên bản hiệu lực",
                    "amount": None,
                    "currency": None,
                    "tax_basis": None,
                    "tone": "neutral",
                }

            latest_Amend = amend_revs[-1:] if amend_revs else self.env["tp.contract.revision"]
            if latest_Amend:
                amend_cell = self._revision_money_cell(latest_Amend, money_allowed)
            elif not money_allowed:
                amend_cell = self._revision_money_cell(None, False)
            else:
                amend_cell = self._na_money_cell("Chưa có phụ lục")

            orig_acc.add_Cell(orig_cell)
            if eff_rev:
                eff_acc.add_Cell(eff_cell)
            elif not money_allowed:
                eff_acc.forbidden_count += 1
            if latest_Amend:
                amend_acc.add_Cell(amend_cell)

            rev_lbl, rev_tone = REVIEW_STATE_LABELS.get(rev_state, (rev_state, "neutral"))
            life_lbl, life_tone = LIFECYCLE_LABELS.get(life_state, (life_state, "neutral"))
            sig_state = latest_rev.signature_status if latest_rev else "unsigned"
            sig_lbl, sig_tone = SIGNATURE_LABELS.get(sig_state, (sig_state, "neutral"))
            auth_state = latest_rev.signature_authority_status if latest_rev else "pending"
            auth_lbl, _auth_tone = AUTHORITY_LABELS.get(auth_state, (auth_state, "neutral"))

            CONTRACT_TYPE_LABELS = {
                "owner": "Chủ đầu tư (Đầu ra)",
                "general_contractor": "Tổng thầu (Đầu ra)",
                "subcontractor": "Thầu phụ (Đầu vào)",
            }
            ctype_label = CONTRACT_TYPE_LABELS.get(c.contract_type, c.contract_type or "—")
            rows.append({
                "id": f"contract:{c.id}",
                "res_model": "tp.contract",
                "res_id": c.id,
                "code": c.code or "",
                "name": c.name or "",
                "project_id": c.project_id.id,
                "project_label": self._project_label(c.project_id),
                "contract_type": c.contract_type,
                "contract_type_label": ctype_label,
                "partner_label": c.partner_id.name or "—",
                "owner_id": owner_user.id or 0,
                "owner_label": owner_user.name or "—",
                "reviewer_label": reviewer_user.name or "—",
                "rev_breakdown": f"Gốc: {1 if orig_rev else 0} · Phụ lục: {len(amend_revs)} · Đính chính: {len(corr_revs)}",
                "original_count": 1 if orig_rev else 0,
                "amendment_count": len(amend_revs),
                "correction_count": len(corr_revs),
                "review_state": rev_state,
                "review_badge": {"label": rev_lbl, "tone": rev_tone},
                "signature_badge": {"label": f"{sig_lbl} ({auth_lbl})", "tone": sig_tone},
                "lifecycle_state": life_state,
                "lifecycle_badge": {"label": life_lbl, "tone": life_tone},
                "effective_date": str(ref_date) if ref_date else "",
                "effective_date_display": _fmt_date(ref_date),
                "original_money": orig_cell,
                "amendment_money": amend_cell,
                "effective_money": eff_cell,
                "drill": {"kind": "record", "payload": {"model": "tp.contract", "res_id": c.id}},
            })

        eff_count = sum(1 for r in rows if r["lifecycle_state"] in ("effective", "execution_completed"))
        in_work_count = sum(1 for r in rows if r["review_state"] in ("draft", "in_review", "returned"))
        total_amendments = sum(r["amendment_count"] for r in rows)
        total_corrections = sum(r["correction_count"] for r in rows)

        summary_cards = [
            {
                "key": "projects",
                "label": "Dự án trong phạm vi",
                "value": _fmt_vn_number(len(scoped_projects)),
                "unit": "dự án",
                "note": "Dự án được phân công trong phạm vi lọc",
                "tone": "info",
            },
            {
                "key": "contracts",
                "label": "Tổng số hợp đồng",
                "value": _fmt_vn_number(len(rows)),
                "unit": "hợp đồng",
                "note": f"{total_amendments} phụ lục · {total_corrections} đính chính (không cộng trùng)",
                "tone": "info",
            },
            {
                "key": "effective",
                "label": "Đã ghi nhận hiệu lực",
                "value": _fmt_vn_number(eff_count),
                "unit": "hợp đồng",
                "note": "Chỉ tính bản đã ghi nhận hiệu lực",
                "tone": "done",
            },
            {
                "key": "in_work",
                "label": "Phiên bản đang xử lý",
                "value": _fmt_vn_number(in_work_count),
                "unit": "hợp đồng",
                "note": "Nháp, đang rà soát hoặc bị trả lại",
                "tone": "warn" if in_work_count else "neutral",
            },
            {
                "key": "effective_money",
                "label": "Tổng giá trị HĐ hiệu lực",
                "value": "Không có quyền xem tiền" if not fin_pids else eff_acc.format_summary("Chưa có HĐ hiệu lực xác nhận"),
                "unit": "",
                "note": "Chỉ tính _effective_revision đã xác nhận tiền",
                "tone": "done" if eff_acc.buckets else "neutral",
            },
            {
                "key": "original_money",
                "label": "Tổng giá trị HĐ gốc (Original)",
                "value": "Không có quyền xem tiền" if not fin_pids else orig_acc.format_summary("Chưa có bản gốc xác nhận"),
                "unit": "",
                "note": "Tách riêng phiên bản gốc (sequence = 0)",
                "tone": "info" if orig_acc.buckets else "neutral",
            },
        ]

        life_counts = defaultdict(int)
        for r in rows:
            life_counts[r["lifecycle_state"]] += 1
        chart_items = []
        for st_key, (st_lbl, st_tone) in LIFECYCLE_LABELS.items():
            cnt = life_counts.get(st_key, 0)
            if cnt or st_key in ("not_effective", "effective", "execution_completed"):
                pct = round(cnt * 100.0 / len(rows), 1) if rows else 0.0
                chart_items.append({
                    "key": st_key,
                    "label": st_lbl,
                    "value": cnt,
                    "display": f"{cnt} hợp đồng ({pct}%)",
                    "tone": st_tone,
                    "percent": pct,
                    "filter_status": f"life:{st_key}",
                })

        columns = [
            {"key": "code", "label": "Mã HĐ", "align": "center", "kind": "code", "optional": False, "default_visible": True, "sortable": True},
            {"key": "name", "label": "Tên hợp đồng", "align": "left", "kind": "link", "optional": False, "default_visible": True, "sortable": True},
            {"key": "project_label", "label": "Dự án", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "contract_type_label", "label": "Loại HĐ", "align": "center", "kind": "text", "optional": True, "default_visible": True, "sortable": True},
            {"key": "partner_label", "label": "Đối tác", "align": "left", "kind": "text", "optional": True, "default_visible": False, "sortable": True},
            {"key": "owner_label", "label": "Người trình / Phụ trách", "align": "left", "kind": "text", "optional": True, "default_visible": True, "sortable": True},
            {"key": "rev_breakdown", "label": "Cơ cấu phiên bản", "align": "center", "kind": "text", "optional": False, "default_visible": True, "sortable": False},
            {"key": "review_badge", "label": "Rà soát (bản mới nhất)", "align": "center", "kind": "badge", "optional": False, "default_visible": True, "sortable": False},
            {"key": "signature_badge", "label": "Ký kết & Thẩm quyền", "align": "center", "kind": "badge", "optional": True, "default_visible": True, "sortable": False},
            {"key": "lifecycle_badge", "label": "Vòng đời hiệu lực", "align": "center", "kind": "badge", "optional": False, "default_visible": True, "sortable": False},
            {"key": "effective_date_display", "label": "Ngày hiệu lực / ký", "align": "center", "kind": "date", "optional": True, "default_visible": True, "sortable": True},
            {"key": "original_money", "label": "Giá trị bản gốc (Original)", "align": "right", "kind": "money", "optional": False, "default_visible": True, "sortable": False},
            {"key": "amendment_money", "label": "Phụ lục mới nhất (Amendment)", "align": "right", "kind": "money", "optional": True, "default_visible": True, "sortable": False},
            {"key": "effective_money", "label": "Giá trị hiệu lực hiện hành", "align": "right", "kind": "money", "optional": False, "default_visible": True, "sortable": False},
        ]

        totals_row = {
            "label": f"Tổng cộng ({len(rows)} hợp đồng — tách riêng từng loại phiên bản, không cộng gộp)",
            "cells": {
                "rev_breakdown": f"Gốc: {sum(r['original_count'] for r in rows)} · PL: {total_amendments} · ĐC: {total_corrections}",
                "original_money": {"display": "Không có quyền xem tiền", "amount": None, "state": "forbidden", "items": []} if not fin_pids else orig_acc.to_dict("Chưa có bản gốc xác nhận"),
                "amendment_money": {"display": "Không có quyền xem tiền", "amount": None, "state": "forbidden", "items": []} if not fin_pids else amend_acc.to_dict("Chưa có phụ lục xác nhận"),
                "effective_money": {"display": "Không có quyền xem tiền", "amount": None, "state": "forbidden", "items": []} if not fin_pids else eff_acc.to_dict("Chưa có HĐ hiệu lực xác nhận"),
            },
        }

        return {
            "rows": rows,
            "owners_map": owners_map,
            "summary_cards": summary_cards,
            "chart": {
                "kind": "donut",
                "title": "Cơ cấu hợp đồng theo trạng thái vòng đời hiệu lực",
                "subtitle": "Cùng mẫu số là tổng số hợp đồng trong phạm vi lọc. Bấm một trạng thái để lọc nhanh.",
                "unit": "hợp đồng",
                "total": len(rows),
                "items": chart_items,
            },
            "columns": columns,
            "totals_row": totals_row,
            "money_keys": ("original_money", "amendment_money", "effective_money"),
            "default_group_by": "project",
            "group_by_options": [
                {"value": "project", "label": "Theo Dự án"},
                {"value": "lifecycle_state", "label": "Theo Trạng thái hiệu lực"},
                {"value": "review_state", "label": "Theo Trạng thái rà soát"},
                {"value": "contract_type", "label": "Theo Loại hợp đồng (Đầu ra / Đầu vào)"},
            ],
            "default_sort_by": "code",
            "sort_options": [
                {"value": "code", "label": "Mã hợp đồng"},
                {"value": "name", "label": "Tên hợp đồng"},
                {"value": "project_label", "label": "Dự án"},
                {"value": "effective_date", "label": "Ngày hiệu lực / ký"},
                {"value": "owner_label", "label": "Người phụ trách"},
            ],
            "statuses": [
                {"value": "life:effective", "label": "Vòng đời: Đang hiệu lực"},
                {"value": "life:not_effective", "label": "Vòng đời: Chưa hiệu lực"},
                {"value": "life:execution_completed", "label": "Vòng đời: Hoàn thành thực hiện"},
                {"value": "review:draft", "label": "Rà soát: Nháp"},
                {"value": "review:in_review", "label": "Rà soát: Đang rà soát"},
                {"value": "review:returned", "label": "Rà soát: Bị trả lại"},
                {"value": "review:review_complete", "label": "Rà soát: Hoàn tất rà soát"},
            ],
            "sub_filter_title": "Loại hợp đồng",
            "sub_filters": [
                {"value": "revenue", "label": "Hợp đồng doanh thu (Đầu ra)"},
                {"value": "cost", "label": "Hợp đồng chi phí (Đầu vào)"},
            ],
            "exclusion_info": {
                "no_money_permission_count": eff_acc.forbidden_count,
                "unconfirmed_money_count": eff_acc.unconfirmed_count + orig_acc.unconfirmed_count,
                "mixed_basis_count": eff_acc.mixed_count + orig_acc.mixed_count,
                "missing_date_count": missing_date_count,
            },
        }

    # ------------------------------------------------------------------
    # R02: Hồ sơ dự án và hồ sơ thầu
    # ------------------------------------------------------------------
    def _build_r02(self, filters, accessible_projects, fin_pids, period, proj_filter, owner_filter, today):
        Lead = self.env["crm.lead"]
        if not Lead.has_access("read"):
            raise AccessError(_("Bạn không có quyền đọc Hồ sơ dự án và Hồ sơ thầu."))

        status_filter = str((filters or {}).get("status") or "").strip()
        sub_filter = str((filters or {}).get("sub_filter") or "").strip()

        domain = [("type", "=", "opportunity"), ("kd_accessible", "=", True)]
        if proj_filter["mode"] == "unassigned" or sub_filter == "unassigned_project":
            domain.append(("tp_project_id", "=", False))
        elif proj_filter["mode"] == "project":
            domain.append(("tp_project_id", "=", proj_filter["project_id"]))

        if sub_filter in ("bid", "direct"):
            domain.append(("kd_route", "=", sub_filter))
        if status_filter in BID_STATE_LABELS:
            domain.append(("kd_bid_state", "=", status_filter))

        leads = Lead.search(domain, order="kd_deadline asc, id desc")

        owners_map = {}
        rows = []
        missing_date_count = 0
        money_acc = MoneyAccumulator()
        pre_project_count = 0
        overdue_count = 0

        for lead in leads:
            if lead.user_id:
                owners_map[lead.user_id.id] = lead.user_id.name
            if owner_filter["owner_id"] and lead.user_id.id != owner_filter["owner_id"]:
                continue

            in_range, is_missing_date = self._date_in_range(lead.kd_deadline, period["d_from"], period["d_to"])
            if not in_range:
                if is_missing_date:
                    missing_date_count += 1
                continue

            is_pre = not bool(lead.tp_project_id)
            if is_pre:
                pre_project_count += 1

            bstate = lead.kd_bid_state or "identified"
            blbl, btone = BID_STATE_LABELS.get(bstate, (bstate, "neutral"))
            is_overdue = bool(lead.kd_deadline and lead.kd_deadline < today and bstate != "submitted")
            if is_overdue:
                overdue_count += 1

            can_money = lead._kd_money_read_allowed()
            if not can_money:
                m_cell = {
                    "state": "forbidden",
                    "display": "Không có quyền xem tiền",
                    "amount": None,
                    "currency": None,
                    "tax_basis": None,
                    "tone": "neutral",
                }
            else:
                val = float(lead.expected_revenue or 0.0)
                cur = lead.company_currency.name if lead.company_currency else "VND"
                if val > 0:
                    m_cell = {
                        "state": "confirmed",
                        "display": f"{_fmt_vn_number(val)} {cur} (dự kiến)",
                        "amount": val,
                        "currency": cur,
                        "tax_basis": "unspecified",
                        "tone": "info",
                    }
                else:
                    m_cell = {
                        "state": "empty",
                        "display": "Chưa khai báo giá trị dự kiến",
                        "amount": None,
                        "currency": cur,
                        "tax_basis": "unspecified",
                        "tone": "neutral",
                    }
            money_acc.add_Cell(m_cell)

            route_label = "Đấu thầu" if lead.kd_route == "bid" else ("Đàm phán trực tiếp" if lead.kd_route == "direct" else "Chưa phân loại")
            rows.append({
                "id": f"lead:{lead.id}",
                "res_model": "crm.lead",
                "res_id": lead.id,
                "code": f"CH-{lead.id:04d}",
                "name": lead.name or "",
                "project_id": lead.tp_project_id.id if lead.tp_project_id else 0,
                "project_label": self._project_label(lead.tp_project_id),
                "partner_label": lead.partner_id.name or "—",
                "owner_id": lead.user_id.id or 0,
                "owner_label": lead.user_id.name or "—",
                "kd_route": lead.kd_route or "",
                "kd_route_label": route_label,
                "kd_bid_state": bstate,
                "bid_state_badge": {"label": blbl, "tone": btone},
                "kd_deadline": str(lead.kd_deadline) if lead.kd_deadline else "",
                "kd_deadline_display": _fmt_date(lead.kd_deadline),
                "is_overdue": is_overdue,
                "kd_receipt": lead.kd_receipt or "Chưa có biên nhận",
                "credential_count": len(lead.kd_credential_ids),
                "expected_money": m_cell,
                "drill": {"kind": "record", "payload": {"model": "crm.lead", "res_id": lead.id}},
            })

        state_counts = defaultdict(int)
        for r in rows:
            state_counts[r["kd_bid_state"]] += 1

        summary_cards = [
            {
                "key": "total_leads",
                "label": "Tổng số hồ sơ dự án / hồ sơ thầu",
                "value": _fmt_vn_number(len(rows)),
                "unit": "hồ sơ dự án",
                "note": f"Gắn dự án: {len(rows) - pre_project_count} · Tiền dự án: {pre_project_count}",
                "tone": "info",
            },
            {
                "key": "identified",
                "label": "Đã nhận diện",
                "value": _fmt_vn_number(state_counts["identified"]),
                "unit": "hồ sơ dự án",
                "note": "Mới tiếp nhận thông tin nguồn",
                "tone": "info",
            },
            {
                "key": "preparation",
                "label": "Đang chuẩn bị hồ sơ",
                "value": _fmt_vn_number(state_counts["preparation"]),
                "unit": "hồ sơ dự án",
                "note": "Đang lập phạm vi, checklist và năng lực",
                "tone": "review",
            },
            {
                "key": "submitted",
                "label": "Đã khai báo nộp — chưa xác minh",
                "value": _fmt_vn_number(state_counts["submitted"]),
                "unit": "hồ sơ dự án",
                "note": "Khai báo nội bộ, chưa tính thắng thầu",
                "tone": "warn",
            },
            {
                "key": "overdue",
                "label": "Quá hạn nộp (chưa nộp)",
                "value": _fmt_vn_number(overdue_count),
                "unit": "hồ sơ dự án",
                "note": f"Hạn nộp trước {_fmt_date(today)}",
                "tone": "returned" if overdue_count else "neutral",
            },
            {
                "key": "expected_money",
                "label": "Tổng giá trị dự kiến (có quyền xem)",
                "value": money_acc.format_summary("Chưa có giá trị dự kiến"),
                "unit": "",
                "note": "Chỉ tính hồ sơ dự án gắn dự án có quyền xem tiền",
                "tone": "info" if money_acc.buckets else "neutral",
            },
        ]

        chart_items = []
        for st_key, (st_lbl, st_tone) in BID_STATE_LABELS.items():
            cnt = state_counts.get(st_key, 0)
            pct = round(cnt * 100.0 / len(rows), 1) if rows else 0.0
            chart_items.append({
                "key": st_key,
                "label": st_lbl,
                "value": cnt,
                "display": f"{cnt} hồ sơ dự án ({pct}%)",
                "tone": st_tone,
                "percent": pct,
                "filter_status": st_key,
            })

        columns = [
            {"key": "code", "label": "Mã tham chiếu", "align": "center", "kind": "code", "optional": False, "default_visible": True, "sortable": True},
            {"key": "name", "label": "Tên hồ sơ dự án / Gói thầu", "align": "left", "kind": "link", "optional": False, "default_visible": True, "sortable": True},
            {"key": "project_label", "label": "Dự án / Tiền dự án", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "partner_label", "label": "Chủ đầu tư / Đối tác", "align": "left", "kind": "text", "optional": True, "default_visible": True, "sortable": True},
            {"key": "owner_label", "label": "Người phụ trách", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "kd_route_label", "label": "Hình thức tiếp cận", "align": "center", "kind": "text", "optional": True, "default_visible": True, "sortable": True},
            {"key": "bid_state_badge", "label": "Trạng thái hồ sơ thầu", "align": "center", "kind": "badge", "optional": False, "default_visible": True, "sortable": False},
            {"key": "kd_deadline_display", "label": "Hạn nộp hồ sơ", "align": "center", "kind": "date", "optional": False, "default_visible": True, "sortable": True},
            {"key": "kd_receipt", "label": "Ghi nhận biên nhận (nội bộ)", "align": "left", "kind": "text", "optional": True, "default_visible": False, "sortable": False},
            {"key": "credential_count", "label": "Chứng chỉ gắn kèm", "align": "right", "kind": "number", "optional": True, "default_visible": True, "sortable": True},
            {"key": "expected_money", "label": "Giá trị dự kiến (chưa xác minh)", "align": "right", "kind": "money", "optional": False, "default_visible": True, "sortable": False},
        ]

        totals_row = {
            "label": f"Tổng cộng ({len(rows)} hồ sơ dự án — gồm {pre_project_count} hồ sơ dự án tiền dự án)",
            "cells": {
                "credential_count": _fmt_vn_number(sum(r["credential_count"] for r in rows)),
                "expected_money": money_acc.to_dict("Chưa có giá trị dự kiến"),
            },
        }

        return {
            "rows": rows,
            "owners_map": owners_map,
            "summary_cards": summary_cards,
            "chart": {
                "kind": "donut",
                "title": "Cơ cấu hồ sơ dự án thầu theo bước chuẩn bị",
                "subtitle": "Cùng mẫu số là tổng số hồ sơ dự án trong phạm vi lọc. 'Đã khai báo nộp — chưa xác minh' không đồng nghĩa trúng thầu.",
                "unit": "hồ sơ dự án",
                "total": len(rows),
                "items": chart_items,
            },
            "columns": columns,
            "totals_row": totals_row,
            "money_keys": ("expected_money",),
            "default_group_by": "kd_bid_state",
            "group_by_options": [
                {"value": "kd_bid_state", "label": "Theo Trạng thái hồ sơ thầu"},
                {"value": "project", "label": "Theo Dự án / Tiền dự án"},
                {"value": "owner", "label": "Theo Người phụ trách"},
                {"value": "kd_route", "label": "Theo Hình thức tiếp cận"},
            ],
            "default_sort_by": "kd_deadline",
            "sort_options": [
                {"value": "kd_deadline", "label": "Hạn nộp hồ sơ"},
                {"value": "code", "label": "Mã tham chiếu"},
                {"value": "name", "label": "Tên hồ sơ dự án"},
                {"value": "project_label", "label": "Dự án"},
                {"value": "owner_label", "label": "Người phụ trách"},
                {"value": "credential_count", "label": "Số chứng chỉ gắn kèm"},
            ],
            "statuses": [
                {"value": "identified", "label": "Đã nhận diện"},
                {"value": "preparation", "label": "Đang chuẩn bị"},
                {"value": "submitted", "label": "Đã khai báo nộp — chưa xác minh"},
            ],
            "sub_filter_title": "Phân loại tiếp cận",
            "sub_filters": [
                {"value": "bid", "label": "Đấu thầu rộng rãi / hạn chế"},
                {"value": "direct", "label": "Đàm phán trực tiếp"},
                {"value": "unassigned_project", "label": "Chưa gắn dự án (tiền dự án)"},
            ],
            "exclusion_info": {
                "no_money_permission_count": money_acc.forbidden_count,
                "unconfirmed_money_count": money_acc.unconfirmed_count,
                "mixed_basis_count": money_acc.mixed_count,
                "missing_date_count": missing_date_count,
            },
        }

    # ------------------------------------------------------------------
    # R03: Kế hoạch, sản lượng, nghiệm thu và đề nghị thanh toán
    # ------------------------------------------------------------------
    def _build_r03(self, filters, accessible_projects, fin_pids, period, proj_filter, owner_filter):
        status_filter = str((filters or {}).get("status") or "").strip()
        sub_filter = str((filters or {}).get("sub_filter") or "").strip()

        proj_ids = [proj_filter["project_id"]] if proj_filter["mode"] == "project" else accessible_projects.ids
        base_domain = [("project_id", "in", proj_ids)]
        if status_filter in REVIEW_STATE_LABELS:
            base_domain.append(("state", "=", status_filter))

        owners_map = {}
        rows = []
        missing_date_count = 0

        plan_acc = MoneyAccumulator()
        prod_acc = MoneyAccumulator()
        acc_acc = MoneyAccumulator()
        pay_in_acc = MoneyAccumulator()
        pay_out_acc = MoneyAccumulator()

        stage_defs = [
            ("plan", "tp.periodic.plan", "1. Kế hoạch kỳ"),
            ("production", "tp.production", "2. Sản lượng thực hiện"),
            ("acceptance", "tp.acceptance", "3. Nghiệm thu"),
            ("payment_receipt", "tp.payment.request", "4a. Đề nghị thu"),
            ("payment_disbursement", "tp.payment.request", "4b. Đề nghị chi"),
        ]

        for stage_key, model_name, stage_label in stage_defs:
            if sub_filter and sub_filter != stage_key:
                continue
            Model = self.env[model_name]
            if not Model.has_access("read"):
                continue
            dom = list(base_domain)
            if stage_key == "payment_receipt":
                dom.append(("direction", "=", "receipt"))
            elif stage_key == "payment_disbursement":
                dom.append(("direction", "=", "disbursement"))

            records = Model.search(dom, order="code, id")
            for rec in records:
                if rec.owner_id:
                    owners_map[rec.owner_id.id] = rec.owner_id.name
                if rec.reviewer_id:
                    owners_map[rec.reviewer_id.id] = rec.reviewer_id.name
                if owner_filter["owner_id"] and rec.owner_id.id != owner_filter["owner_id"] and rec.reviewer_id.id != owner_filter["owner_id"]:
                    continue

                if stage_key in ("plan", "production"):
                    in_range, is_missing = self._period_overlaps(rec.period_from, rec.period_to, period["d_from"], period["d_to"])
                    date_str = str(rec.period_to or rec.period_from or "")
                    date_disp = f"{_fmt_date(rec.period_from)} → {_fmt_date(rec.period_to)}"
                elif stage_key == "acceptance":
                    in_range, is_missing = self._date_in_range(rec.date, period["d_from"], period["d_to"])
                    date_str = str(rec.date or "")
                    date_disp = _fmt_date(rec.date)
                else:
                    in_range, is_missing = self._date_in_range(rec.date, period["d_from"], period["d_to"])
                    date_str = str(rec.date or "")
                    date_disp = _fmt_date(rec.date)

                if not in_range:
                    if is_missing:
                        missing_date_count += 1
                    continue

                money_allowed = rec.project_id.id in fin_pids
                cell = self._typed_money_cell(rec, money_allowed, is_plan=(stage_key == "plan"))

                plan_cell = self._na_money_cell()
                prod_cell = self._na_money_cell()
                acc_cell = self._na_money_cell()
                pin_cell = self._na_money_cell()
                pout_cell = self._na_money_cell()
                qty_disp = "—"
                comp_note = "—"

                if stage_key == "plan":
                    plan_cell = cell
                    plan_acc.add_Cell(cell)
                    if not money_allowed:
                        comp_note = "Không có quyền xem tiền"
                    else:
                        prod_line = rec.amount_ids.filtered(lambda a: a.measure == "production")[:1]
                        rev_line = rec.amount_ids.filtered(lambda a: a.measure == "revenue")[:1]
                        if prod_line:
                            if prod_line.source_status == "comparable" and (prod_line.value or 0) > 0:
                                ratio = round(float(prod_line.source_value or 0.0) * 100.0 / float(prod_line.value), 1)
                                comp_note = f"Đạt {ratio}% KH sản lượng ({_fmt_vn_number(prod_line.source_value)} / {_fmt_vn_number(prod_line.value)})"
                            elif prod_line.source_status == "no_data":
                                comp_note = "Chưa có sản lượng đang rà soát trong kỳ"
                            else:
                                comp_note = "Chưa cùng cơ sở thuế/tiền tệ hoặc chưa xác nhận"
                        elif rev_line:
                            comp_note = "Chỉ tiêu doanh thu: chưa có chứng từ ghi sổ"
                elif stage_key == "production":
                    prod_cell = cell
                    prod_acc.add_Cell(cell)
                    qty_disp = f"{_fmt_vn_number(rec.quantity, 2)} {rec.unit or ''}".strip()
                    comp_note = f"Phạm vi: {rec.scope or '—'}"
                elif stage_key == "acceptance":
                    acc_cell = cell
                    acc_acc.add_Cell(cell)
                    comp_note = f"Đợt: {rec.round_code or '—'}"
                elif stage_key == "payment_receipt":
                    pin_cell = cell
                    pay_in_acc.add_Cell(cell)
                    basis_lbl = "Theo nghiệm thu" if rec.payment_basis == "acceptance" else "Tạm ứng"
                    comp_note = f"Đề nghị thu ({basis_lbl}) — chưa phải thực thu"
                else:
                    pout_cell = cell
                    pay_out_acc.add_Cell(cell)
                    basis_lbl = "Theo nghiệm thu" if rec.payment_basis == "acceptance" else "Tạm ứng"
                    comp_note = f"Đề nghị chi ({basis_lbl}) — chưa phải thực chi"

                st_lbl, st_tone = REVIEW_STATE_LABELS.get(rec.state, (rec.state, "neutral"))
                rec_state = getattr(rec, "reconciliation_state", "unreconciled") or "unreconciled"
                rec_lbl, rec_tone = RECONCILIATION_LABELS.get(rec_state, (rec_state, "warning"))
                contract_lbl = rec.contract_id.code if getattr(rec, "contract_id", False) else "—"

                rows.append({
                    "id": f"{stage_key}:{rec.id}",
                    "res_model": model_name,
                    "res_id": rec.id,
                    "stage_key": stage_key,
                    "stage_label": stage_label,
                    "code": rec.code or "",
                    "name": rec.name or "",
                    "project_id": rec.project_id.id,
                    "project_label": self._project_label(rec.project_id),
                    "contract_label": contract_lbl,
                    "period_or_date": date_str,
                    "period_or_date_display": date_disp,
                    "owner_id": rec.owner_id.id or 0,
                    "owner_label": rec.owner_id.name or "—",
                    "state": rec.state,
                    "state_badge": {"label": st_lbl, "tone": st_tone},
                    "reconciliation_badge": {"label": rec_lbl, "tone": rec_tone},
                    "quantity_display": qty_disp,
                    "plan_money": plan_cell,
                    "production_money": prod_cell,
                    "acceptance_money": acc_cell,
                    "payment_receipt_money": pin_cell,
                    "payment_disbursement_money": pout_cell,
                    "comparison_note": comp_note,
                    "drill": {"kind": "record", "payload": {"model": model_name, "res_id": rec.id}},
                })

        stage_counts = defaultdict(int)
        for r in rows:
            stage_counts[r["stage_key"]] += 1

        summary_cards = [
            {
                "key": "plan_money",
                "label": "1. Kế hoạch sản lượng (đã xác nhận)",
                "value": plan_acc.format_summary("Chưa có KH xác nhận"),
                "unit": "",
                "note": f"{stage_counts['plan']} hồ sơ kế hoạch kỳ",
                "tone": "info" if plan_acc.buckets else "neutral",
            },
            {
                "key": "prod_money",
                "label": "2. Sản lượng thực hiện (đã xác nhận)",
                "value": prod_acc.format_summary("Chưa có SL xác nhận"),
                "unit": "",
                "note": f"{stage_counts['production']} hồ sơ sản lượng",
                "tone": "review" if prod_acc.buckets else "neutral",
            },
            {
                "key": "acc_money",
                "label": "3. Giá trị nghiệm thu (đã xác nhận)",
                "value": acc_acc.format_summary("Chưa có NT xác nhận"),
                "unit": "",
                "note": f"{stage_counts['acceptance']} hồ sơ nghiệm thu",
                "tone": "done" if acc_acc.buckets else "neutral",
            },
            {
                "key": "pay_in_money",
                "label": "4a. Đề nghị thu (đã xác nhận)",
                "value": pay_in_acc.format_summary("Chưa có ĐN thu xác nhận"),
                "unit": "",
                "note": f"{stage_counts['payment_receipt']} hồ sơ đề nghị thu",
                "tone": "done" if pay_in_acc.buckets else "neutral",
            },
            {
                "key": "pay_out_money",
                "label": "4b. Đề nghị chi (đã xác nhận)",
                "value": pay_out_acc.format_summary("Chưa có ĐN chi xác nhận"),
                "unit": "",
                "note": f"{stage_counts['payment_disbursement']} hồ sơ đề nghị chi",
                "tone": "warn" if pay_out_acc.buckets else "neutral",
            },
            {
                "key": "actual_cash",
                "label": "5. Thực thu / Thực chi kế toán",
                "value": "Chưa có chứng từ hạch toán",
                "unit": "",
                "note": "Không suy diễn từ đề nghị thanh toán",
                "tone": "neutral",
            },
        ]

        max_cnt = max([stage_counts.get(s[0], 0) for s in stage_defs] + [1])
        chart_items = []
        tones_map = {
            "plan": "info",
            "production": "review",
            "acceptance": "done",
            "payment_receipt": "done",
            "payment_disbursement": "warn",
        }
        for stage_key, _model_name, stage_label in stage_defs:
            cnt = stage_counts.get(stage_key, 0)
            pct = round(cnt * 100.0 / max_cnt, 1) if max_cnt else 0.0
            chart_items.append({
                "key": stage_key,
                "label": stage_label,
                "value": cnt,
                "display": f"{cnt} hồ sơ",
                "tone": tones_map.get(stage_key, "info"),
                "percent": pct,
                "filter_sub": stage_key,
            })

        columns = [
            {"key": "code", "label": "Mã hồ sơ", "align": "center", "kind": "code", "optional": False, "default_visible": True, "sortable": True},
            {"key": "stage_label", "label": "Giai đoạn nghiệp vụ", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "name", "label": "Nội dung hồ sơ / Kỳ", "align": "left", "kind": "link", "optional": False, "default_visible": True, "sortable": True},
            {"key": "project_label", "label": "Dự án", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "contract_label", "label": "Mã HĐ", "align": "center", "kind": "code", "optional": True, "default_visible": True, "sortable": True},
            {"key": "period_or_date_display", "label": "Kỳ / Ngày ghi nhận", "align": "center", "kind": "date", "optional": False, "default_visible": True, "sortable": True},
            {"key": "owner_label", "label": "Người phụ trách", "align": "left", "kind": "text", "optional": True, "default_visible": True, "sortable": True},
            {"key": "state_badge", "label": "Trạng thái rà soát", "align": "center", "kind": "badge", "optional": False, "default_visible": True, "sortable": False},
            {"key": "reconciliation_badge", "label": "Đối chiếu", "align": "center", "kind": "badge", "optional": True, "default_visible": False, "sortable": False},
            {"key": "quantity_display", "label": "Khối lượng (SL)", "align": "right", "kind": "text", "optional": True, "default_visible": True, "sortable": False},
            {"key": "plan_money", "label": "Giá trị Kế hoạch", "align": "right", "kind": "money", "optional": False, "default_visible": True, "sortable": False},
            {"key": "production_money", "label": "Giá trị Sản lượng", "align": "right", "kind": "money", "optional": False, "default_visible": True, "sortable": False},
            {"key": "acceptance_money", "label": "Giá trị Nghiệm thu", "align": "right", "kind": "money", "optional": False, "default_visible": True, "sortable": False},
            {"key": "payment_receipt_money", "label": "Đề nghị thu", "align": "right", "kind": "money", "optional": False, "default_visible": True, "sortable": False},
            {"key": "payment_disbursement_money", "label": "Đề nghị chi", "align": "right", "kind": "money", "optional": False, "default_visible": True, "sortable": False},
            {"key": "comparison_note", "label": "Ghi chú đối chiếu / Tỷ lệ", "align": "left", "kind": "text", "optional": True, "default_visible": True, "sortable": False},
        ]

        totals_row = {
            "label": f"Tổng theo từng giai đoạn độc lập ({len(rows)} hồ sơ — không cộng gộp xuyên giai đoạn)",
            "cells": {
                "plan_money": plan_acc.to_dict("—"),
                "production_money": prod_acc.to_dict("—"),
                "acceptance_money": acc_acc.to_dict("—"),
                "payment_receipt_money": pay_in_acc.to_dict("—"),
                "payment_disbursement_money": pay_out_acc.to_dict("—"),
            },
        }

        all_accs = (plan_acc, prod_acc, acc_acc, pay_in_acc, pay_out_acc)
        return {
            "rows": rows,
            "owners_map": owners_map,
            "summary_cards": summary_cards,
            "chart": {
                "kind": "bars",
                "title": "Số lượng hồ sơ theo từng giai đoạn nghiệp vụ",
                "subtitle": "Các giai đoạn có bản chất nghiệp vụ khác nhau nên được so sánh song song, không cộng gộp thành một tổng tiền.",
                "unit": "hồ sơ",
                "total": len(rows),
                "items": chart_items,
            },
            "columns": columns,
            "totals_row": totals_row,
            "money_keys": (
                "plan_money",
                "production_money",
                "acceptance_money",
                "payment_receipt_money",
                "payment_disbursement_money",
            ),
            "default_group_by": "project",
            "group_by_options": [
                {"value": "project", "label": "Theo Dự án (đối chiếu 5 cột giai đoạn)"},
                {"value": "stage_key", "label": "Theo Giai đoạn nghiệp vụ"},
                {"value": "state", "label": "Theo Trạng thái rà soát"},
                {"value": "owner", "label": "Theo Người phụ trách"},
            ],
            "default_sort_by": "period_or_date",
            "sort_options": [
                {"value": "period_or_date", "label": "Kỳ / Ngày ghi nhận"},
                {"value": "code", "label": "Mã hồ sơ"},
                {"value": "stage_label", "label": "Giai đoạn"},
                {"value": "project_label", "label": "Dự án"},
                {"value": "owner_label", "label": "Người phụ trách"},
            ],
            "statuses": [
                {"value": "draft", "label": "Nháp"},
                {"value": "in_review", "label": "Đang rà soát"},
                {"value": "returned", "label": "Bị trả lại"},
            ],
            "sub_filter_title": "Giai đoạn nghiệp vụ",
            "sub_filters": [
                {"value": "plan", "label": "1. Kế hoạch kỳ"},
                {"value": "production", "label": "2. Sản lượng thực hiện"},
                {"value": "acceptance", "label": "3. Nghiệm thu"},
                {"value": "payment_receipt", "label": "4a. Đề nghị thu"},
                {"value": "payment_disbursement", "label": "4b. Đề nghị chi"},
            ],
            "exclusion_info": {
                "no_money_permission_count": sum(a.forbidden_count for a in all_accs),
                "unconfirmed_money_count": sum(a.unconfirmed_count for a in all_accs),
                "mixed_basis_count": sum(a.mixed_count for a in all_accs),
                "missing_date_count": missing_date_count,
            },
        }

    # ------------------------------------------------------------------
    # R04: Giao khoán và thầu phụ
    # ------------------------------------------------------------------
    def _build_r04(self, filters, accessible_projects, fin_pids, period, proj_filter, owner_filter):
        Allocation = self.env["tp.allocation"]
        if not Allocation.has_access("read"):
            raise AccessError(_("Bạn không có quyền đọc hồ sơ Giao khoán."))

        status_filter = str((filters or {}).get("status") or "").strip()
        sub_filter = str((filters or {}).get("sub_filter") or "").strip()

        proj_ids = [proj_filter["project_id"]] if proj_filter["mode"] == "project" else accessible_projects.ids
        domain = [("project_id", "in", proj_ids)]
        if status_filter in REVIEW_STATE_LABELS:
            domain.append(("state", "=", status_filter))

        if sub_filter in ("internal", "subcontract"):
            domain.append(("allocation_kind", "=", sub_filter))
        elif sub_filter == "1":
            domain.append(("parent_id", "=", False))
        elif sub_filter == "2":
            domain.append(("parent_id", "!=", False))

        allocations = Allocation.search(domain, order="code, id")
        owners_map = {}
        rows = []
        missing_date_count = 0

        level1_acc = MoneyAccumulator()
        level2_acc = MoneyAccumulator()
        level1_count = 0
        level2_count = 0
        overrun_count = 0

        for rec in allocations:
            if rec.owner_id:
                owners_map[rec.owner_id.id] = rec.owner_id.name
            if rec.reviewer_id:
                owners_map[rec.reviewer_id.id] = rec.reviewer_id.name
            if owner_filter["owner_id"] and rec.owner_id.id != owner_filter["owner_id"] and rec.reviewer_id.id != owner_filter["owner_id"]:
                continue

            in_range, is_missing = self._date_in_range(rec.date_due, period["d_from"], period["d_to"])
            if not in_range:
                if is_missing:
                    missing_date_count += 1
                continue

            is_l1 = not bool(rec.parent_id)
            level_val = "1" if is_l1 else "2"
            has_overrun = bool(rec.overrun_warning and "vượt khoán cha" in rec.overrun_warning)
            if status_filter == "overrun" and not has_overrun:
                continue

            if is_l1:
                level1_count += 1
            else:
                level2_count += 1
            if has_overrun:
                overrun_count += 1

            money_allowed = rec.project_id.id in fin_pids
            cell = self._typed_money_cell(rec, money_allowed)
            if is_l1:
                l1_cell = cell
                l2_cell = self._na_money_cell("— (Hồ sơ cấp 1)")
                level1_acc.add_Cell(cell)
            else:
                l1_cell = self._na_money_cell("— (Phân bổ cấp 2)")
                l2_cell = cell
                level2_acc.add_Cell(cell)

            if is_l1:
                c_cnt = len(rec.child_ids)
                if not c_cnt:
                    child_note = "Chưa có phân bổ cấp 2"
                elif has_overrun:
                    child_note = f"{c_cnt} dòng cấp 2 · CẢNH BÁO VƯỢT TRẦN CẤP 1"
                else:
                    child_note = f"{c_cnt} dòng cấp 2 · Trong trần"
            else:
                child_note = f"Thuộc cấp 1: {rec.parent_id.code or rec.parent_id.name}"

            st_lbl, st_tone = REVIEW_STATE_LABELS.get(rec.state, (rec.state, "neutral"))
            kind_lbl = "Giao khoán nội bộ" if rec.allocation_kind == "internal" else "Thầu phụ"
            level_lbl = "Cấp 1 (Giao khoán gốc)" if is_l1 else "Cấp 2 (Phân bổ chi tiết)"
            unit_or_partner = (
                rec.recipient_department_id.name
                if rec.allocation_kind == "internal" and rec.recipient_department_id
                else (rec.partner_id.name if rec.partner_id else "—")
            )

            rows.append({
                "id": f"allocation:{rec.id}",
                "res_model": "tp.allocation",
                "res_id": rec.id,
                "code": rec.code or "",
                "name": rec.name or "",
                "project_id": rec.project_id.id,
                "project_label": self._project_label(rec.project_id),
                "contract_label": rec.contract_id.code if rec.contract_id else "—",
                "allocation_kind": rec.allocation_kind,
                "allocation_kind_label": kind_lbl,
                "level": level_val,
                "level_label": level_lbl,
                "recipient_label": unit_or_partner,
                "owner_id": rec.owner_id.id or 0,
                "owner_label": rec.owner_id.name or "—",
                "state": rec.state,
                "state_badge": {"label": st_lbl, "tone": st_tone},
                "overrun_warning": has_overrun,
                "overrun_badge": {
                    "label": "Vượt trần cấp 1" if has_overrun else "Bình thường",
                    "tone": "danger" if has_overrun else "neutral",
                },
                "date_due": str(rec.date_due) if rec.date_due else "",
                "date_due_display": _fmt_date(rec.date_due),
                "level1_money": l1_cell,
                "level2_money": l2_cell,
                "children_note": child_note,
                "drill": {"kind": "record", "payload": {"model": "tp.allocation", "res_id": rec.id}},
            })

        internal_cnt = sum(1 for r in rows if r["allocation_kind"] == "internal")
        sub_cnt = sum(1 for r in rows if r["allocation_kind"] == "subcontract")

        summary_cards = [
            {
                "key": "total_alloc",
                "label": "Tổng hồ sơ giao khoán / thầu phụ",
                "value": _fmt_vn_number(len(rows)),
                "unit": "hồ sơ",
                "note": f"Cấp 1 (gốc): {level1_count} · Cấp 2 (con): {level2_count}",
                "tone": "info",
            },
            {
                "key": "kind_split",
                "label": "Nội bộ / Thầu phụ",
                "value": f"{internal_cnt} / {sub_cnt}",
                "unit": "hồ sơ",
                "note": "Nội bộ phòng ban vs Thầu phụ bên ngoài",
                "tone": "info",
            },
            {
                "key": "level1_money",
                "label": "Tổng giá trị Giao khoán Cấp 1 (Gốc)",
                "value": level1_acc.format_summary("Chưa có GK cấp 1 xác nhận"),
                "unit": "",
                "note": "Chỉ cộng Cấp 1 đã xác nhận (không cộng trùng Cấp 2)",
                "tone": "done" if level1_acc.buckets else "neutral",
            },
            {
                "key": "level2_money",
                "label": "Tổng phân bổ Cấp 2 (Đối chiếu)",
                "value": level2_acc.format_summary("Chưa có phân bổ cấp 2 xác nhận"),
                "unit": "",
                "note": "Thống kê riêng để đối chiếu với trần Cấp 1",
                "tone": "review" if level2_acc.buckets else "neutral",
            },
            {
                "key": "overrun",
                "label": "Cảnh báo vượt trần Cấp 1",
                "value": _fmt_vn_number(overrun_count),
                "unit": "hồ sơ",
                "note": "Tổng Cấp 2 xác nhận lớn hơn trần Cấp 1",
                "tone": "returned" if overrun_count else "neutral",
            },
        ]

        chart_items = [
            {
                "key": "internal",
                "label": "Giao khoán nội bộ",
                "value": internal_cnt,
                "display": f"{internal_cnt} hồ sơ ({round(internal_cnt * 100.0 / len(rows), 1) if rows else 0.0}%)",
                "tone": "info",
                "percent": round(internal_cnt * 100.0 / len(rows), 1) if rows else 0.0,
                "filter_sub": "internal",
            },
            {
                "key": "subcontract",
                "label": "Thầu phụ bên ngoài",
                "value": sub_cnt,
                "display": f"{sub_cnt} hồ sơ ({round(sub_cnt * 100.0 / len(rows), 1) if rows else 0.0}%)",
                "tone": "review",
                "percent": round(sub_cnt * 100.0 / len(rows), 1) if rows else 0.0,
                "filter_sub": "subcontract",
            },
        ]

        columns = [
            {"key": "code", "label": "Mã GK", "align": "center", "kind": "code", "optional": False, "default_visible": True, "sortable": True},
            {"key": "name", "label": "Nội dung giao khoán / Thầu phụ", "align": "left", "kind": "link", "optional": False, "default_visible": True, "sortable": True},
            {"key": "project_label", "label": "Dự án", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "contract_label", "label": "Mã HĐ", "align": "center", "kind": "code", "optional": True, "default_visible": True, "sortable": True},
            {"key": "allocation_kind_label", "label": "Loại hình", "align": "center", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "level_label", "label": "Cấp phân bổ", "align": "center", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "recipient_label", "label": "Đơn vị nhận / Thầu phụ", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "owner_label", "label": "Người phụ trách", "align": "left", "kind": "text", "optional": True, "default_visible": True, "sortable": True},
            {"key": "state_badge", "label": "Trạng thái rà soát", "align": "center", "kind": "badge", "optional": False, "default_visible": True, "sortable": False},
            {"key": "overrun_badge", "label": "Kiểm soát trần", "align": "center", "kind": "badge", "optional": False, "default_visible": True, "sortable": False},
            {"key": "date_due_display", "label": "Hạn thực hiện", "align": "center", "kind": "date", "optional": True, "default_visible": True, "sortable": True},
            {"key": "level1_money", "label": "Giá trị Cấp 1 (Giao khoán gốc)", "align": "right", "kind": "money", "optional": False, "default_visible": True, "sortable": False},
            {"key": "level2_money", "label": "Giá trị Cấp 2 (Phân bổ con)", "align": "right", "kind": "money", "optional": False, "default_visible": True, "sortable": False},
            {"key": "children_note", "label": "Quan hệ Cha / Con & Đối chiếu", "align": "left", "kind": "text", "optional": True, "default_visible": True, "sortable": False},
        ]

        totals_row = {
            "label": f"Tổng cộng ({level1_count} hồ sơ Cấp 1 · {level2_count} hồ sơ Cấp 2 — tách riêng 2 cột, tuyệt đối không cộng gộp Cha + Con)",
            "cells": {
                "level1_money": level1_acc.to_dict("Chưa có GK cấp 1 xác nhận"),
                "level2_money": level2_acc.to_dict("Chưa có phân bổ cấp 2 xác nhận"),
            },
        }

        return {
            "rows": rows,
            "owners_map": owners_map,
            "summary_cards": summary_cards,
            "chart": {
                "kind": "donut",
                "title": "Cơ cấu hồ sơ theo loại hình Giao khoán nội bộ và Thầu phụ",
                "subtitle": "Cùng mẫu số là tổng số hồ sơ giao khoán trong phạm vi lọc.",
                "unit": "hồ sơ",
                "total": len(rows),
                "items": chart_items,
            },
            "columns": columns,
            "totals_row": totals_row,
            "money_keys": ("level1_money", "level2_money"),
            "default_group_by": "project",
            "group_by_options": [
                {"value": "project", "label": "Theo Dự án"},
                {"value": "allocation_kind", "label": "Theo Loại hình (Nội bộ / Thầu phụ)"},
                {"value": "level", "label": "Theo Cấp giao khoán (Cấp 1 / Cấp 2)"},
                {"value": "state", "label": "Theo Trạng thái rà soát"},
            ],
            "default_sort_by": "code",
            "sort_options": [
                {"value": "code", "label": "Mã giao khoán"},
                {"value": "name", "label": "Nội dung"},
                {"value": "project_label", "label": "Dự án"},
                {"value": "level", "label": "Cấp phân bổ"},
                {"value": "date_due", "label": "Hạn thực hiện"},
            ],
            "statuses": [
                {"value": "draft", "label": "Nháp"},
                {"value": "in_review", "label": "Đang rà soát"},
                {"value": "returned", "label": "Bị trả lại"},
                {"value": "overrun", "label": "Cảnh báo vượt trần Cấp 1"},
            ],
            "sub_filter_title": "Loại hình / Cấp",
            "sub_filters": [
                {"value": "internal", "label": "Giao khoán nội bộ"},
                {"value": "subcontract", "label": "Thầu phụ bên ngoài"},
                {"value": "1", "label": "Chỉ hồ sơ Cấp 1 (Gốc)"},
                {"value": "2", "label": "Chỉ hồ sơ Cấp 2 (Phân bổ con)"},
            ],
            "exclusion_info": {
                "no_money_permission_count": level1_acc.forbidden_count + level2_acc.forbidden_count,
                "unconfirmed_money_count": level1_acc.unconfirmed_count + level2_acc.unconfirmed_count,
                "mixed_basis_count": level1_acc.mixed_count + level2_acc.mixed_count,
                "missing_date_count": missing_date_count,
            },
        }

    # ------------------------------------------------------------------
    # R05: Tình trạng xử lý và trách nhiệm hồ sơ
    # ------------------------------------------------------------------
    def _build_r05(self, filters, accessible_projects, period, proj_filter, owner_filter, today):
        status_filter = str((filters or {}).get("status") or "").strip()
        sub_filter = str((filters or {}).get("sub_filter") or "").strip()
        soon = today + timedelta(days=3)
        uid = self.env.uid

        owners_map = {}
        rows = []
        missing_date_count = 0
        blocked_sources = []

        for src in R05_SOURCES:
            s_key = src["key"]
            if sub_filter and sub_filter.startswith("src:") and sub_filter.split(":", 1)[1] != s_key:
                continue
            model_name = src["model"]
            Model = self.env[model_name]
            if not Model.has_access("read"):
                blocked_sources.append(src["label"])
                continue

            dom = list(src["base"])
            p_field = src["project"]
            if proj_filter["mode"] == "unassigned":
                if s_key == "opportunity":
                    dom.append((p_field, "=", False))
                else:
                    continue
            elif proj_filter["mode"] == "project":
                dom.append((p_field, "=", proj_filter["project_id"]))
            else:
                if s_key != "opportunity":
                    dom.append((p_field, "in", accessible_projects.ids))

            records = Model.search(dom, order="id desc")
            for rec in records:
                if s_key == "contract":
                    proj = rec.contract_id.project_id
                    code = f"{rec.contract_id.code or 'HD'}-R{rec.sequence}"
                    name = rec.name or rec.contract_id.name or code
                    latest_sub = rec.submission_ids[-1:] if rec.submission_ids else self.env["tp.contract.submission"]
                    owner_users = latest_sub.submitted_by_id or self.env["tp.contract.workflow"]._tp_business_owner(rec) or rec.contract_id.project_id.user_id
                    reviewer_user = latest_sub.assigned_reviewer_id or latest_sub.reviewer_id or self.env["res.users"]
                    due_date = rec.effective_date or (rec.create_date.date() if rec.create_date else None)
                    raw_state = rec.review_state or "draft"
                    st_lbl, st_tone = REVIEW_STATE_LABELS.get(raw_state, (raw_state, "neutral"))
                    bucket = raw_state if raw_state in ("draft", "in_review", "returned") else "completed"
                elif s_key == "opportunity":
                    proj = rec.tp_project_id
                    code = f"CH-{rec.id:04d}"
                    name = rec.name or code
                    owner_users = rec.user_id
                    reviewer_user = self.env["res.users"]
                    due_date = rec.kd_deadline
                    raw_state = rec.kd_bid_state or "identified"
                    st_lbl, st_tone = BID_STATE_LABELS.get(raw_state, (raw_state, "neutral"))
                    bucket = "draft" if raw_state in ("identified", "preparation") else "completed"
                elif s_key == "task":
                    proj = rec.project_id
                    code = f"CV-{rec.id:04d}"
                    name = rec.name or code
                    owner_users = rec.user_ids
                    reviewer_user = self.env["res.users"]
                    due_date = rec.date_deadline
                    raw_state = rec.state or "01_in_progress"
                    st_lbl, st_tone = TASK_STATE_LABELS.get(raw_state, (raw_state, "neutral"))
                    if raw_state == "04_waiting_normal":
                        bucket = "in_review"
                    elif raw_state == "02_changes_requested":
                        bucket = "returned"
                    elif raw_state == "01_in_progress":
                        bucket = "draft"
                    else:
                        bucket = "completed"
                else:
                    proj = rec.project_id
                    code = rec.code or f"{s_key.upper()}-{rec.id}"
                    name = rec.name or code
                    owner_users = rec.owner_id
                    reviewer_user = rec.reviewer_id
                    due_date = rec.date_due
                    raw_state = rec.state or "draft"
                    st_lbl, st_tone = REVIEW_STATE_LABELS.get(raw_state, (raw_state, "neutral"))
                    bucket = raw_state if raw_state in ("draft", "in_review", "returned") else "completed"

                for u in owner_users:
                    owners_map[u.id] = u.name
                if reviewer_user:
                    owners_map[reviewer_user.id] = reviewer_user.name

                if owner_filter["owner_id"]:
                    f_uid = owner_filter["owner_id"]
                    if f_uid not in owner_users.ids and reviewer_user.id != f_uid:
                        continue

                due_d = self._to_date(due_date)
                in_range, is_missing = self._date_in_range(due_d, period["d_from"], period["d_to"])
                if not in_range:
                    if is_missing:
                        missing_date_count += 1
                    continue

                is_open_item = bucket in ("draft", "in_review", "returned")
                is_overdue = bool(due_d and due_d < today and is_open_item)
                is_due_soon = bool(due_d and today <= due_d <= soon and is_open_item)

                if is_overdue:
                    sla_key = "overdue"
                    sla_badge = {"label": "Quá hạn xử lý", "tone": "danger"}
                elif is_due_soon:
                    sla_key = "due_soon"
                    sla_badge = {"label": "Đến hạn ≤ 3 ngày", "tone": "warning"}
                elif due_d:
                    sla_key = "on_time"
                    sla_badge = {"label": "Trong hạn", "tone": "info"}
                else:
                    sla_key = "no_due"
                    sla_badge = {"label": "Chưa đặt hạn", "tone": "neutral"}

                if s_key == "contract":
                    is_my_review = bool(
                        bucket == "in_review"
                        and any(s.outcome == "pending" and (s.assigned_reviewer_id or s.reviewer_id).id == uid for s in rec.submission_ids),
                    )
                    is_my_returned = bool(
                        bucket == "returned"
                        and any(s.outcome == "returned" and s.submitted_by_id.id == uid and not s.rework_started_at for s in rec.submission_ids),
                    )
                elif s_key in ("opportunity", "task"):
                    is_my_review = False
                    is_my_returned = False
                else:
                    kd_dom = getattr(rec, "_kd_domain", "")
                    is_my_review = bool(
                        bucket == "in_review"
                        and reviewer_user.id == uid
                        and self.env["tp.kd.grant"]._has(proj, kd_dom, "review"),
                    )
                    is_my_returned = bool(bucket == "returned" and uid in owner_users.ids)

                is_my_owner = uid in owner_users.ids
                is_my_overdue = bool(is_overdue and is_my_owner)
                is_my_due = bool(is_due_soon and is_my_owner)
                is_mine_action = is_my_review or is_my_returned or is_my_overdue or is_my_due

                if is_my_review:
                    my_role_label = "Chờ bạn rà soát"
                elif is_my_returned:
                    my_role_label = "Hồ sơ của bạn bị trả lại"
                elif is_my_overdue:
                    my_role_label = "Bạn phụ trách (quá hạn)"
                elif is_my_owner:
                    my_role_label = "Bạn phụ trách"
                else:
                    my_role_label = "Trong phạm vi xem"

                if status_filter:
                    if status_filter in ("draft", "in_review", "returned", "completed") and bucket != status_filter:
                        continue
                    if status_filter == "overdue" and not is_overdue:
                        continue
                    if status_filter == "due_soon" and not is_due_soon:
                        continue

                if sub_filter == "mine_all" and not is_mine_action:
                    continue
                if sub_filter == "mine_review" and not is_my_review:
                    continue
                if sub_filter == "mine_returned" and not is_my_returned:
                    continue
                if sub_filter == "mine_overdue" and not is_my_overdue:
                    continue

                owner_names = ", ".join(owner_users.mapped("name")) if owner_users else "—"
                rows.append({
                    "id": f"{s_key}:{rec.id}",
                    "res_model": model_name,
                    "res_id": rec.id,
                    "source_key": s_key,
                    "source_label": src["label"],
                    "code": code,
                    "name": name,
                    "project_id": proj.id if proj else 0,
                    "project_label": self._project_label(proj),
                    "owner_id": owner_users[:1].id if owner_users else 0,
                    "owner_label": owner_names,
                    "reviewer_label": reviewer_user.name or "—",
                    "bucket": bucket,
                    "native_state_badge": {"label": st_lbl, "tone": st_tone},
                    "sla_key": sla_key,
                    "sla_badge": sla_badge,
                    "due_date": str(due_date) if due_date else "",
                    "due_date_display": _fmt_date(due_date),
                    "is_overdue": is_overdue,
                    "is_due_soon": is_due_soon,
                    "is_mine_action": is_mine_action,
                    "is_my_review": is_my_review,
                    "is_my_returned": is_my_returned,
                    "my_responsibility_label": my_role_label,
                    "drill": {"kind": "record", "payload": {"model": model_name, "res_id": rec.id}},
                })

        cnt_draft = sum(1 for r in rows if r["bucket"] == "draft")
        cnt_review = sum(1 for r in rows if r["bucket"] == "in_review")
        cnt_returned = sum(1 for r in rows if r["bucket"] == "returned")
        cnt_overdue = sum(1 for r in rows if r["is_overdue"])
        cnt_due_soon = sum(1 for r in rows if r["is_due_soon"])
        cnt_mine = sum(1 for r in rows if r["is_mine_action"])

        summary_cards = [
            {
                "key": "distinct_total",
                "label": "Tổng hồ sơ định danh (không trùng)",
                "value": _fmt_vn_number(len(rows)),
                "unit": "hồ sơ",
                "note": "Mỗi bản ghi chỉ tính 1 lần duy nhất",
                "tone": "info",
            },
            {
                "key": "draft",
                "label": "Nháp / Đang chuẩn bị",
                "value": _fmt_vn_number(cnt_draft),
                "unit": "hồ sơ",
                "note": "Đang soạn thảo hoặc thực hiện",
                "tone": "draft",
            },
            {
                "key": "in_review",
                "label": "Đang chờ rà soát",
                "value": _fmt_vn_number(cnt_review),
                "unit": "hồ sơ",
                "note": f"Trong đó chờ bạn rà soát: {sum(1 for r in rows if r['is_my_review'])}",
                "tone": "review",
            },
            {
                "key": "returned",
                "label": "Bị trả lại / Cần sửa",
                "value": _fmt_vn_number(cnt_returned),
                "unit": "hồ sơ",
                "note": f"Trong đó của bạn: {sum(1 for r in rows if r['is_my_returned'])}",
                "tone": "returned" if cnt_returned else "neutral",
            },
            {
                "key": "overdue",
                "label": "Quá hạn xử lý",
                "value": _fmt_vn_number(cnt_overdue),
                "unit": "hồ sơ",
                "note": f"Đến hạn ≤ 3 ngày: {cnt_due_soon} hồ sơ",
                "tone": "warn" if (cnt_overdue or cnt_due_soon) else "neutral",
            },
            {
                "key": "mine",
                "label": "Việc của tôi (cần xử lý)",
                "value": _fmt_vn_number(cnt_mine),
                "unit": "hồ sơ",
                "note": "Chờ bạn duyệt, bị trả lại hoặc quá hạn/đến hạn",
                "tone": "review" if cnt_mine else "done",
            },
        ]

        src_counts = defaultdict(int)
        for r in rows:
            src_counts[r["source_key"]] += 1
        max_src = max(list(src_counts.values()) + [1])
        chart_items = []
        for src in R05_SOURCES:
            cnt = src_counts.get(src["key"], 0)
            pct = round(cnt * 100.0 / max_src, 1) if max_src else 0.0
            chart_items.append({
                "key": src["key"],
                "label": src["label"],
                "value": cnt,
                "display": f"{cnt} hồ sơ",
                "tone": "review" if cnt else "neutral",
                "percent": pct,
                "filter_sub": f"src:{src['key']}",
            })

        columns = [
            {"key": "code", "label": "Mã hồ sơ", "align": "center", "kind": "code", "optional": False, "default_visible": True, "sortable": True},
            {"key": "source_label", "label": "Loại hồ sơ nghiệp vụ", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "name", "label": "Tên hồ sơ / Nội dung", "align": "left", "kind": "link", "optional": False, "default_visible": True, "sortable": True},
            {"key": "project_label", "label": "Dự án", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "owner_label", "label": "Người phụ trách / Trình", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "reviewer_label", "label": "Người rà soát", "align": "left", "kind": "text", "optional": True, "default_visible": True, "sortable": True},
            {"key": "native_state_badge", "label": "Trạng thái hồ sơ", "align": "center", "kind": "badge", "optional": False, "default_visible": True, "sortable": False},
            {"key": "sla_badge", "label": "Tình trạng hạn", "align": "center", "kind": "badge", "optional": False, "default_visible": True, "sortable": False},
            {"key": "due_date_display", "label": "Hạn xử lý / Ngày mốc", "align": "center", "kind": "date", "optional": False, "default_visible": True, "sortable": True},
            {"key": "my_responsibility_label", "label": "Trách nhiệm với bạn", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
        ]

        totals_row = {
            "label": f"Tổng cộng: {len(rows)} hồ sơ định danh (Nháp: {cnt_draft} · Đang rà soát: {cnt_review} · Trả lại: {cnt_returned} · Quá hạn: {cnt_overdue} — không cộng trùng)",
            "cells": {
                "my_responsibility_label": f"Việc của bạn: {cnt_mine} hồ sơ",
            },
        }

        sub_filters = [
            {"value": "mine_all", "label": "Việc của tôi — tất cả cần xử lý"},
            {"value": "mine_review", "label": "Việc của tôi — chờ tôi rà soát"},
            {"value": "mine_returned", "label": "Việc của tôi — bị trả lại"},
            {"value": "mine_overdue", "label": "Việc của tôi — quá hạn"},
        ] + [{"value": f"src:{s['key']}", "label": f"Nguồn: {s['label']}"} for s in R05_SOURCES]

        return {
            "rows": rows,
            "owners_map": owners_map,
            "summary_cards": summary_cards,
            "chart": {
                "kind": "bars",
                "title": "Số lượng hồ sơ theo 10 nguồn nghiệp vụ KH-KD",
                "subtitle": "Bấm một nguồn để lọc riêng loại hồ sơ đó.",
                "unit": "hồ sơ",
                "total": len(rows),
                "items": chart_items,
            },
            "columns": columns,
            "totals_row": totals_row,
            "money_keys": (),
            "default_group_by": "source_key",
            "group_by_options": [
                {"value": "source_key", "label": "Theo Loại hồ sơ nghiệp vụ"},
                {"value": "owner", "label": "Theo Người phụ trách"},
                {"value": "bucket", "label": "Theo Bước xử lý"},
                {"value": "sla_key", "label": "Theo Tình trạng hạn"},
                {"value": "project", "label": "Theo Dự án"},
            ],
            "default_sort_by": "due_date",
            "sort_options": [
                {"value": "due_date", "label": "Hạn xử lý"},
                {"value": "code", "label": "Mã hồ sơ"},
                {"value": "source_label", "label": "Loại hồ sơ"},
                {"value": "project_label", "label": "Dự án"},
                {"value": "owner_label", "label": "Người phụ trách"},
            ],
            "statuses": [
                {"value": "draft", "label": "Nháp / Đang chuẩn bị"},
                {"value": "in_review", "label": "Đang chờ rà soát"},
                {"value": "returned", "label": "Bị trả lại / Yêu cầu sửa"},
                {"value": "overdue", "label": "Quá hạn xử lý"},
                {"value": "due_soon", "label": "Đến hạn trong 3 ngày"},
                {"value": "completed", "label": "Đã hoàn tất / Đã nộp"},
            ],
            "sub_filter_title": "Phạm vi trách nhiệm / Nguồn",
            "sub_filters": sub_filters,
            "exclusion_info": {
                "no_money_permission_count": 0,
                "unconfirmed_money_count": 0,
                "mixed_basis_count": 0,
                "missing_date_count": missing_date_count,
                "blocked_sources": blocked_sources,
            },
        }

    # ------------------------------------------------------------------
    # R06: Năng lực, chứng chỉ và nghĩa vụ hồ sơ
    # ------------------------------------------------------------------
    def _build_r06(self, filters, accessible_projects, fin_pids, period, proj_filter, owner_filter, today):
        status_filter = str((filters or {}).get("status") or "").strip()
        sub_filter = str((filters or {}).get("sub_filter") or "").strip()
        soon_30 = today + timedelta(days=30)

        proj_ids = [proj_filter["project_id"]] if proj_filter["mode"] == "project" else accessible_projects.ids
        base_dom = [("project_id", "in", proj_ids)]

        owners_map = {}
        rows = []
        missing_date_count = 0

        distinct_cred_count = 0
        cred_usage_links_total = 0
        cred_expired_count = 0
        cred_expiring_count = 0
        ob_count = 0
        ob_missing_count = 0

        # Map credential -> linked accessible opportunities (without inflating distinct credential count)
        cred_leads_map = defaultdict(list)
        Lead = self.env["crm.lead"]
        if Lead.has_access("read"):
            for lead in Lead.sudo().search([("type", "=", "opportunity"), ("kd_accessible", "=", True), ("kd_credential_link_ids", "!=", False)]):
                for cred in lead.kd_credential_link_ids:
                    cred_leads_map[cred.id].append(lead.name or f"CH-{lead.id}")

        if sub_filter in ("", "credential", "org_credential", "person_credential"):
            Credential = self.env["tp.credential"]
            if Credential.has_access("read"):
                c_dom = list(base_dom)
                if sub_filter == "org_credential":
                    c_dom.append(("subject_kind", "=", "organization"))
                elif sub_filter == "person_credential":
                    c_dom.append(("subject_kind", "=", "person"))
                for cred in Credential.search(c_dom, order="valid_to asc, code asc, id asc"):
                    if cred.subject_kind == "person" and not self.env.is_admin():
                        if self.env.uid not in (cred.owner_id.id, cred.reviewer_id.id) and not cred.project_id._tp_head_allowed():
                            continue

                    if cred.owner_id:
                        owners_map[cred.owner_id.id] = cred.owner_id.name
                    if cred.reviewer_id:
                        owners_map[cred.reviewer_id.id] = cred.reviewer_id.name
                    if owner_filter["owner_id"] and cred.owner_id.id != owner_filter["owner_id"] and cred.reviewer_id.id != owner_filter["owner_id"]:
                        continue

                    valid_to_d = self._to_date(cred.valid_to)
                    in_range, is_missing = self._date_in_range(valid_to_d, period["d_from"], period["d_to"])
                    if not in_range:
                        if is_missing:
                            missing_date_count += 1
                        continue

                    if not valid_to_d:
                        bucket = "no_expiry"
                        b_badge = {"label": "Chưa khai báo ngày hết hạn", "tone": "neutral"}
                    elif valid_to_d < today:
                        bucket = "expired"
                        b_badge = {"label": "Hết hạn (< hôm nay · ngưỡng 30 ngày minh họa)", "tone": "danger"}
                    elif valid_to_d <= soon_30:
                        bucket = "expiring_30d"
                        b_badge = {"label": "Sắp hết hạn (≤ 30 ngày · ngưỡng minh họa)", "tone": "warning"}
                    else:
                        bucket = "valid_gt_30d"
                        b_badge = {"label": "Còn hạn (> 30 ngày) — chưa xác minh", "tone": "info"}

                    if status_filter and status_filter != bucket and status_filter != f"review:{cred.state}":
                        continue

                    distinct_cred_count += 1
                    if bucket == "expired":
                        cred_expired_count += 1
                    elif bucket == "expiring_30d":
                        cred_expiring_count += 1

                    linked_names = cred_leads_map.get(cred.id, [])
                    u_cnt = len(linked_names)
                    cred_usage_links_total += u_cnt
                    usage_disp = f"{u_cnt} hồ sơ dự án ({', '.join(linked_names[:2])}{'...' if u_cnt > 2 else ''})" if u_cnt else "Chưa gắn hồ sơ dự án thầu"

                    st_lbl, st_tone = REVIEW_STATE_LABELS.get(cred.state, (cred.state, "neutral"))
                    subj_lbl = "Chứng chỉ Tổ chức" if cred.subject_kind == "organization" else "Chứng chỉ Nhân sự (hạn chế quyền xem)"

                    rows.append({
                        "id": f"credential:{cred.id}",
                        "res_model": "tp.credential",
                        "res_id": cred.id,
                        "record_kind": "credential",
                        "record_kind_label": "Hồ sơ năng lực / Chứng chỉ",
                        "sub_type_label": f"{subj_lbl} · {cred.credential_kind or '—'}",
                        "code": cred.code or "",
                        "name": cred.name or "",
                        "project_id": cred.project_id.id,
                        "project_label": self._project_label(cred.project_id),
                        "owner_id": cred.owner_id.id or 0,
                        "owner_label": cred.owner_id.name or "—",
                        "state": cred.state,
                        "state_badge": {"label": st_lbl, "tone": st_tone},
                        "status_bucket": bucket,
                        "status_bucket_badge": b_badge,
                        "target_date": str(cred.valid_to) if cred.valid_to else "",
                        "target_date_display": _fmt_date(cred.valid_to),
                        "usage_count": u_cnt,
                        "usage_display": usage_disp,
                        "drill": {"kind": "record", "payload": {"model": "tp.credential", "res_id": cred.id}},
                    })

        if sub_filter in ("", "obligation"):
            Obligation = self.env["tp.obligation"]
            if Obligation.has_access("read"):
                for ob in Obligation.search(base_dom, order="date_due asc, code asc, id asc"):
                    if ob.owner_id:
                        owners_map[ob.owner_id.id] = ob.owner_id.name
                    if ob.reviewer_id:
                        owners_map[ob.reviewer_id.id] = ob.reviewer_id.name
                    if owner_filter["owner_id"] and ob.owner_id.id != owner_filter["owner_id"] and ob.reviewer_id.id != owner_filter["owner_id"]:
                        continue

                    ref_d = ob.date_due
                    in_range, is_missing = self._date_in_range(ref_d, period["d_from"], period["d_to"])
                    if not in_range:
                        if is_missing:
                            missing_date_count += 1
                        continue

                    chk = ob.checklist_status or "missing"
                    chk_lbl, chk_tone = CHECKLIST_LABELS.get(chk, (chk, "warning"))
                    bucket = f"chk_{chk}"

                    if status_filter and status_filter != bucket and status_filter != chk and status_filter != f"review:{ob.state}":
                        continue

                    ob_count += 1
                    if chk == "missing":
                        ob_missing_count += 1

                    st_lbl, st_tone = REVIEW_STATE_LABELS.get(ob.state, (ob.state, "neutral"))
                    kind_lbl = OBLIGATION_KIND_LABELS.get(ob.obligation_kind, ob.obligation_kind or "Nghĩa vụ")

                    rows.append({
                        "id": f"obligation:{ob.id}",
                        "res_model": "tp.obligation",
                        "res_id": ob.id,
                        "record_kind": "obligation",
                        "record_kind_label": "Nghĩa vụ hồ sơ / Checklist",
                        "sub_type_label": kind_lbl,
                        "code": ob.code or "",
                        "name": ob.name or "",
                        "project_id": ob.project_id.id,
                        "project_label": self._project_label(ob.project_id),
                        "owner_id": ob.owner_id.id or 0,
                        "owner_label": ob.owner_id.name or "—",
                        "state": ob.state,
                        "state_badge": {"label": st_lbl, "tone": st_tone},
                        "status_bucket": bucket,
                        "status_bucket_badge": {"label": chk_lbl, "tone": chk_tone},
                        "target_date": str(ref_d) if ref_d else "",
                        "target_date_display": _fmt_date(ref_d),
                        "usage_count": 0,
                        "usage_display": f"HĐ: {ob.contract_id.code}" if ob.contract_id else "Theo dự án",
                        "drill": {"kind": "record", "payload": {"model": "tp.obligation", "res_id": ob.id}},
                    })

        summary_cards = [
            {
                "key": "distinct_creds",
                "label": "Chứng chỉ / Năng lực (định danh)",
                "value": _fmt_vn_number(distinct_cred_count),
                "unit": "chứng chỉ",
                "note": f"Gắn vào {cred_usage_links_total} lượt hồ sơ dự án thầu (không cộng trùng)",
                "tone": "info",
            },
            {
                "key": "cred_expired",
                "label": "Chứng chỉ hết hạn (< hôm nay)",
                "value": _fmt_vn_number(cred_expired_count),
                "unit": "chứng chỉ",
                "note": "Ngưỡng 30 ngày minh họa",
                "tone": "returned" if cred_expired_count else "neutral",
            },
            {
                "key": "cred_expiring",
                "label": "Chứng chỉ sắp hết hạn (≤ 30 ngày)",
                "value": _fmt_vn_number(cred_expiring_count),
                "unit": "chứng chỉ",
                "note": f"Từ {_fmt_date(today)} đến {_fmt_date(soon_30)}",
                "tone": "warn" if cred_expiring_count else "neutral",
            },
            {
                "key": "obligations",
                "label": "Tổng nghĩa vụ hồ sơ / checklist",
                "value": _fmt_vn_number(ob_count),
                "unit": "nghĩa vụ",
                "note": f"Chưa có hồ sơ: {ob_missing_count} nghĩa vụ",
                "tone": "warn" if ob_missing_count else "info",
            },
            {
                "key": "ob_missing",
                "label": "Nghĩa vụ còn thiếu hồ sơ",
                "value": _fmt_vn_number(ob_missing_count),
                "unit": "nghĩa vụ",
                "note": "Cần tập hợp bổ sung theo danh mục",
                "tone": "warn" if ob_missing_count else "done",
            },
        ]

        bucket_counts = defaultdict(int)
        for r in rows:
            bucket_counts[r["status_bucket"]] += 1
        max_b = max(list(bucket_counts.values()) + [1])
        chart_defs = [
            ("expired", "Chứng chỉ: Hết hạn (< hôm nay)", "returned"),
            ("expiring_30d", "Chứng chỉ: Sắp hết hạn (≤ 30 ngày)", "warn"),
            ("valid_gt_30d", "Chứng chỉ: Còn hạn (> 30 ngày) — chưa xác minh", "info"),
            ("chk_missing", "Nghĩa vụ: Chưa có hồ sơ", "warn"),
            ("chk_collecting", "Nghĩa vụ: Đang tập hợp", "review"),
            ("chk_internal_checked", "Nghĩa vụ: Đã kiểm tra nội bộ", "done"),
        ]
        chart_items = []
        for b_key, b_lbl, b_tone in chart_defs:
            cnt = bucket_counts.get(b_key, 0)
            pct = round(cnt * 100.0 / max_b, 1) if max_b else 0.0
            chart_items.append({
                "key": b_key,
                "label": b_lbl,
                "value": cnt,
                "display": f"{cnt} bản ghi",
                "tone": b_tone,
                "percent": pct,
                "filter_status": b_key,
            })

        columns = [
            {"key": "code", "label": "Mã hồ sơ", "align": "center", "kind": "code", "optional": False, "default_visible": True, "sortable": True},
            {"key": "record_kind_label", "label": "Nhóm hồ sơ", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "sub_type_label", "label": "Phân loại chi tiết", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "name", "label": "Tên chứng chỉ / Nghĩa vụ", "align": "left", "kind": "link", "optional": False, "default_visible": True, "sortable": True},
            {"key": "project_label", "label": "Dự án", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": True},
            {"key": "owner_label", "label": "Người phụ trách", "align": "left", "kind": "text", "optional": True, "default_visible": True, "sortable": True},
            {"key": "state_badge", "label": "Rà soát nội bộ", "align": "center", "kind": "badge", "optional": True, "default_visible": True, "sortable": False},
            {"key": "status_bucket_badge", "label": "Thời hạn / Checklist", "align": "center", "kind": "badge", "optional": False, "default_visible": True, "sortable": False},
            {"key": "target_date_display", "label": "Ngày hết hạn / Hạn nộp", "align": "center", "kind": "date", "optional": False, "default_visible": True, "sortable": True},
            {"key": "usage_display", "label": "Hồ sơ dự án thầu sử dụng / Hợp đồng", "align": "left", "kind": "text", "optional": False, "default_visible": True, "sortable": False},
        ]

        totals_row = {
            "label": f"Tổng cộng ({distinct_cred_count} chứng chỉ định danh · {ob_count} nghĩa vụ hồ sơ — không cộng trùng chứng chỉ theo số hồ sơ dự án gắn kèm)",
            "cells": {
                "usage_display": f"{cred_usage_links_total} lượt gắn hồ sơ dự án thầu",
            },
        }

        return {
            "rows": rows,
            "owners_map": owners_map,
            "summary_cards": summary_cards,
            "chart": {
                "kind": "bars",
                "title": "Phân bổ theo thời hạn chứng chỉ (ngưỡng 30 ngày minh họa) và checklist nghĩa vụ",
                "subtitle": "Chứng chỉ và nghĩa vụ có đơn vị khác nhau nên hiển thị thanh so sánh số lượng theo từng nhóm trạng thái.",
                "unit": "bản ghi",
                "total": len(rows),
                "items": chart_items,
            },
            "columns": columns,
            "totals_row": totals_row,
            "money_keys": (),
            "default_group_by": "record_kind",
            "group_by_options": [
                {"value": "record_kind", "label": "Theo Nhóm hồ sơ (Chứng chỉ vs Nghĩa vụ)"},
                {"value": "status_bucket", "label": "Theo Thời hạn / Checklist"},
                {"value": "project", "label": "Theo Dự án"},
                {"value": "owner", "label": "Theo Người phụ trách"},
            ],
            "default_sort_by": "target_date",
            "sort_options": [
                {"value": "target_date", "label": "Ngày hết hạn / Hạn nộp"},
                {"value": "code", "label": "Mã hồ sơ"},
                {"value": "name", "label": "Tên hồ sơ"},
                {"value": "project_label", "label": "Dự án"},
                {"value": "usage_count", "label": "Số hồ sơ dự án thầu sử dụng"},
            ],
            "statuses": [
                {"value": "expired", "label": "Chứng chỉ: Hết hạn (< hôm nay)"},
                {"value": "expiring_30d", "label": "Chứng chỉ: Sắp hết hạn (≤ 30 ngày)"},
                {"value": "valid_gt_30d", "label": "Chứng chỉ: Còn hạn (> 30 ngày)"},
                {"value": "chk_missing", "label": "Nghĩa vụ: Chưa có hồ sơ"},
                {"value": "chk_collecting", "label": "Nghĩa vụ: Đang tập hợp"},
                {"value": "chk_internal_checked", "label": "Nghĩa vụ: Đã kiểm tra nội bộ"},
            ],
            "sub_filter_title": "Loại bản ghi",
            "sub_filters": [
                {"value": "credential", "label": "Chỉ Hồ sơ năng lực / Chứng chỉ"},
                {"value": "org_credential", "label": "Chứng chỉ Tổ chức"},
                {"value": "person_credential", "label": "Chứng chỉ Nhân sự"},
                {"value": "obligation", "label": "Chỉ Nghĩa vụ hồ sơ / Bảo lãnh"},
            ],
            "exclusion_info": {
                "no_money_permission_count": 0,
                "unconfirmed_money_count": 0,
                "mixed_basis_count": 0,
                "missing_date_count": missing_date_count,
            },
        }

    # ------------------------------------------------------------------
    # Search, Sort, Group, Pagination, Drill-down & Excel Export
    # ------------------------------------------------------------------
    def _row_group_identity(self, report_key, row, group_by):
        if group_by == "project":
            return str(row.get("project_id") or 0), row.get("project_label") or "Chưa gắn dự án"
        if group_by == "owner":
            return str(row.get("owner_id") or 0), row.get("owner_label") or "—"
        if report_key == "R01":
            if group_by == "lifecycle_state":
                return row["lifecycle_state"], row["lifecycle_badge"]["label"]
            if group_by == "review_state":
                return row["review_state"], row["review_badge"]["label"]
            if group_by == "contract_type":
                return row["contract_type"], row["contract_type_label"]
        elif report_key == "R02":
            if group_by == "kd_bid_state":
                return row["kd_bid_state"], row["bid_state_badge"]["label"]
            if group_by == "kd_route":
                return row["kd_route"], row["kd_route_label"]
        elif report_key == "R03":
            if group_by == "stage_key":
                return row["stage_key"], row["stage_label"]
            if group_by == "state":
                return row["state"], row["state_badge"]["label"]
        elif report_key == "R04":
            if group_by == "allocation_kind":
                return row["allocation_kind"], row["allocation_kind_label"]
            if group_by == "level":
                return row["level"], row["level_label"]
            if group_by == "state":
                return row["state"], row["state_badge"]["label"]
        elif report_key == "R05":
            if group_by == "source_key":
                return row["source_key"], row["source_label"]
            if group_by == "bucket":
                return row["bucket"], row["native_state_badge"]["label"]
            if group_by == "sla_key":
                return row["sla_key"], row["sla_badge"]["label"]
        elif report_key == "R06":
            if group_by == "record_kind":
                return row["record_kind"], row["record_kind_label"]
            if group_by == "status_bucket":
                return row["status_bucket"], row["status_bucket_badge"]["label"]
        return "all", "Tất cả bản ghi"

    def _build_groups(self, report_key, rows, group_by, money_keys, columns):
        money_labels = {col["key"]: col["label"] for col in columns if col["key"] in money_keys}
        grouped = {}
        order_keys = []
        for r in rows:
            g_key, g_label = self._row_group_identity(report_key, r, group_by)
            if g_key not in grouped:
                grouped[g_key] = {
                    "key": g_key,
                    "label": g_label,
                    "count": 0,
                    "accs": {mk: MoneyAccumulator() for mk in money_keys},
                    "extra_counts": defaultdict(int),
                }
                order_keys.append(g_key)
            g = grouped[g_key]
            g["count"] += 1
            for mk in money_keys:
                g["accs"][mk].add_Cell(r.get(mk))
            if report_key == "R01":
                g["extra_counts"]["effective"] += 1 if r.get("lifecycle_state") in ("effective", "execution_completed") else 0
                g["extra_counts"]["amendments"] += int(r.get("amendment_count") or 0)
            elif report_key == "R04":
                g["extra_counts"]["l1"] += 1 if r.get("level") == "1" else 0
                g["extra_counts"]["l2"] += 1 if r.get("level") == "2" else 0
            elif report_key == "R05":
                g["extra_counts"]["overdue"] += 1 if r.get("is_overdue") else 0
                g["extra_counts"]["mine"] += 1 if r.get("is_mine_action") else 0
            elif report_key == "R06":
                g["extra_counts"]["cred"] += 1 if r.get("record_kind") == "credential" else 0
                g["extra_counts"]["ob"] += 1 if r.get("record_kind") == "obligation" else 0
                g["extra_counts"]["usage"] += int(r.get("usage_count") or 0)

        out = []
        for g_key in order_keys:
            g = grouped[g_key]
            metrics = []
            if report_key == "R01":
                metrics.append({"label": "Hiệu lực", "value": f"{g['extra_counts']['effective']} HĐ"})
                metrics.append({"label": "Phụ lục", "value": f"{g['extra_counts']['amendments']} bản"})
            elif report_key == "R04":
                metrics.append({"label": "Cấp 1 (gốc)", "value": f"{g['extra_counts']['l1']} hồ sơ"})
                metrics.append({"label": "Cấp 2 (con)", "value": f"{g['extra_counts']['l2']} hồ sơ"})
            elif report_key == "R05":
                metrics.append({"label": "Quá hạn", "value": f"{g['extra_counts']['overdue']} hồ sơ"})
                metrics.append({"label": "Việc của bạn", "value": f"{g['extra_counts']['mine']} hồ sơ"})
            elif report_key == "R06":
                metrics.append({"label": "Chứng chỉ / Nghĩa vụ", "value": f"{g['extra_counts']['cred']} CC · {g['extra_counts']['ob']} NV"})
                metrics.append({"label": "Lượt gắn CH thầu", "value": f"{g['extra_counts']['usage']} lượt"})

            money_cells = {}
            for mk in money_keys:
                acc_dict = g["accs"][mk].to_dict("—")
                money_cells[mk] = acc_dict
                metrics.append({"label": money_labels.get(mk, mk), "value": acc_dict["display"]})

            out.append({
                "key": g_key,
                "label": g["label"],
                "count": g["count"],
                "metrics": metrics,
                "money_cells": money_cells,
            })
        return out

    def _filter_rows_by_search(self, rows, search_text):
        q = (search_text or "").strip().lower()
        if not q:
            return rows
        matched = []
        for r in rows:
            haystack = " ".join([
                str(r.get("code") or ""),
                str(r.get("name") or ""),
                str(r.get("project_label") or ""),
                str(r.get("owner_label") or ""),
                str(r.get("partner_label") or ""),
                str(r.get("recipient_label") or ""),
                str(r.get("source_label") or ""),
                str(r.get("stage_label") or ""),
                str(r.get("sub_type_label") or ""),
            ]).lower()
            if q in haystack:
                matched.append(r)
        return matched

    def _sort_rows(self, rows, sort_by, sort_dir):
        reverse = str(sort_dir or "asc").lower() == "desc"

        def _sort_key(r):
            val = r.get(sort_by)
            if isinstance(val, dict):
                val = val.get("label") or val.get("display") or ""
            if isinstance(val, (int, float)):
                return (0, float(val), str(r.get("code") or ""))
            s = str(val or "")
            # Empty dates/strings go last on ascending sort
            if not s or s == "—":
                return (1 if not reverse else -1, "", str(r.get("code") or ""))
            return (0, s.lower(), str(r.get("code") or ""))

        return sorted(rows, key=_sort_key, reverse=reverse)

    def _compute_full_report(
        self,
        report_key="R01",
        filters=None,
        group_by=None,
        sort_by=None,
        sort_dir="asc",
        search="",
    ):
        self._check_kd_access()
        report_key = str(report_key or "R01").strip().upper()
        if report_key not in CATALOG_BY_KEY:
            raise ValidationError(_("Nhóm báo cáo không hợp lệ: %s") % report_key)

        filters = filters or {}
        if not isinstance(filters, dict):
            raise ValidationError(_("Bộ lọc báo cáo phải là đối tượng hợp lệ."))

        today = fields.Date.context_today(self)
        now = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        accessible_projects = self._accessible_projects()
        fin_pids = self._financial_project_ids(accessible_projects)
        allow_unassigned = report_key in ("R02", "R05")

        period = self._resolve_period(filters, today)
        proj_filter = self._parse_project_filter(filters, accessible_projects, allow_unassigned=allow_unassigned)
        owner_filter = self._parse_owner_filter(filters)

        if report_key == "R01":
            built = self._build_r01(filters, accessible_projects, fin_pids, period, proj_filter, owner_filter)
        elif report_key == "R02":
            built = self._build_r02(filters, accessible_projects, fin_pids, period, proj_filter, owner_filter, today)
        elif report_key == "R03":
            built = self._build_r03(filters, accessible_projects, fin_pids, period, proj_filter, owner_filter)
        elif report_key == "R04":
            built = self._build_r04(filters, accessible_projects, fin_pids, period, proj_filter, owner_filter)
        elif report_key == "R05":
            built = self._build_r05(filters, accessible_projects, period, proj_filter, owner_filter, today)
        else:
            built = self._build_r06(filters, accessible_projects, fin_pids, period, proj_filter, owner_filter, today)

        valid_groups = {g["value"]: g["label"] for g in built["group_by_options"]}
        resolved_group_by = group_by if group_by in valid_groups else built["default_group_by"]

        valid_sorts = {s["value"]: s["label"] for s in built["sort_options"]}
        resolved_sort_by = sort_by if sort_by in valid_sorts else built["default_sort_by"]
        resolved_sort_dir = "desc" if str(sort_dir or "asc").lower() == "desc" else "asc"

        filtered_rows = self._filter_rows_by_search(built["rows"], search)
        sorted_rows = self._sort_rows(filtered_rows, resolved_sort_by, resolved_sort_dir)
        groups = self._build_groups(
            report_key,
            sorted_rows,
            resolved_group_by,
            built["money_keys"],
            built["columns"],
        )

        # If search narrowed rows, recompute totals_row money cells on the exact filtered rows
        if (search or "").strip() and built["money_keys"]:
            re_accs = {mk: MoneyAccumulator() for mk in built["money_keys"]}
            for r in sorted_rows:
                for mk in built["money_keys"]:
                    re_accs[mk].add_Cell(r.get(mk))
            for mk, acc in re_accs.items():
                built["totals_row"]["cells"][mk] = acc.to_dict("—")

        status_val = str(filters.get("status") or "").strip()
        status_map = {s["value"]: s["label"] for s in built["statuses"]}
        sub_val = str(filters.get("sub_filter") or "").strip()
        sub_map = {s["value"]: s["label"] for s in built["sub_filters"]}

        applied_filters = {
            "period_preset": period["period_preset"],
            "period_label": period["period_label"],
            "date_from": period["date_from"],
            "date_to": period["date_to"],
            "project_id": proj_filter["project_id"],
            "project_label": proj_filter["label"],
            "owner_id": owner_filter["owner_id"],
            "owner_label": owner_filter["label"],
            "status": status_val if status_val in status_map else "",
            "status_label": status_map.get(status_val, "Tất cả trạng thái"),
            "sub_filter": sub_val if sub_val in sub_map else "",
            "sub_filter_label": sub_map.get(sub_val, "Tất cả phân loại"),
            "group_by": resolved_group_by,
            "group_by_label": valid_groups.get(resolved_group_by, ""),
            "sort_by": resolved_sort_by,
            "sort_by_label": valid_sorts.get(resolved_sort_by, ""),
            "sort_dir": resolved_sort_dir,
            "search": (search or "").strip(),
        }

        chips = [{"key": "period", "label": f"Kỳ: {applied_filters['period_label']}"}]
        if applied_filters["project_id"]:
            chips.append({"key": "project", "label": f"Dự án: {applied_filters['project_label']}"})
        if applied_filters["owner_id"]:
            chips.append({"key": "owner", "label": f"Phụ trách: {applied_filters['owner_label']}"})
        if applied_filters["status"]:
            chips.append({"key": "status", "label": f"Trạng thái: {applied_filters['status_label']}"})
        if applied_filters["sub_filter"]:
            chips.append({"key": "sub_filter", "label": f"{built['sub_filter_title']}: {applied_filters['sub_filter_label']}"})
        if applied_filters["search"]:
            chips.append({"key": "search", "label": f"Từ khóa: \"{applied_filters['search']}\""})

        owners_options = [
            {"id": uid, "label": uname}
            for uid, uname in sorted(built["owners_map"].items(), key=lambda item: item[1].lower())
        ]
        if owner_filter["owner_id"] and owner_filter["owner_id"] not in built["owners_map"]:
            owners_options.append({"id": owner_filter["owner_id"], "label": owner_filter["label"]})

        ex_info = built["exclusion_info"]
        ex_notes = []
        if ex_info.get("no_money_permission_count"):
            ex_notes.append(f"{ex_info['no_money_permission_count']} khoản ẩn tiền do không có quyền tài chính dự án")
        if ex_info.get("unconfirmed_money_count"):
            ex_notes.append(f"{ex_info['unconfirmed_money_count']} khoản chưa xác nhận tiền không cộng vào tổng")
        if ex_info.get("mixed_basis_count"):
            ex_notes.append(f"{ex_info['mixed_basis_count']} khoản khác cơ sở thuế không cộng gộp")
        if ex_info.get("missing_date_count"):
            ex_notes.append(f"{ex_info['missing_date_count']} bản ghi chưa có ngày mốc không thuộc khoảng ngày lọc")
        if ex_info.get("blocked_sources"):
            ex_notes.append(f"Nguồn chưa có quyền xem: {', '.join(ex_info['blocked_sources'])}")
        ex_info["note"] = " · ".join(ex_notes) if ex_notes else "Tất cả khoản đủ điều kiện trong phạm vi đã được đối chiếu."

        return {
            "report_key": report_key,
            "report_meta": CATALOG_BY_KEY[report_key],
            "catalog": list(REPORT_CATALOG),
            "updated_at": now.strftime("%H:%M:%S %d/%m/%Y"),
            "today": str(today),
            "user_name": self.env.user.name,
            "can_view_money": bool(fin_pids),
            "financial_project_count": len(fin_pids),
            "accessible_project_count": len(accessible_projects),
            "options": {
                "projects": [{"id": p.id, "label": self._project_label(p)} for p in accessible_projects],
                "allow_unassigned_project": allow_unassigned,
                "owners": owners_options,
                "statuses": built["statuses"],
                "sub_filter_title": built["sub_filter_title"],
                "sub_filters": built["sub_filters"],
                "group_by_options": built["group_by_options"],
                "sort_options": built["sort_options"],
                "page_sizes": list(PAGE_SIZES),
            },
            "applied_filters": applied_filters,
            "applied_chips": chips,
            "summary_cards": built["summary_cards"],
            "exclusion_info": ex_info,
            "chart": built["chart"],
            "columns": built["columns"],
            "money_keys": list(built["money_keys"]),
            "groups": groups,
            "all_rows": sorted_rows,
            "totals_row": built["totals_row"],
        }

    @api.model
    def get_kd_report(
        self,
        report_key="R01",
        filters=None,
        group_by=None,
        sort_by=None,
        sort_dir="asc",
        page=1,
        page_size=100,
        search="",
    ):
        try:
            page_size = int(page_size or 100)
        except (TypeError, ValueError) as err:
            raise ValidationError(_("Số dòng mỗi trang không hợp lệ.")) from err
        if page_size not in PAGE_SIZES:
            raise ValidationError(_("Số dòng mỗi trang phải thuộc (10, 20, 50, 100)."))
        try:
            page = max(1, int(page or 1))
        except (TypeError, ValueError) as err:
            raise ValidationError(_("Số trang không hợp lệ.")) from err

        full = self._compute_full_report(
            report_key=report_key,
            filters=filters,
            group_by=group_by,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=search,
        )
        all_rows = full.pop("all_rows")
        total_rows = len(all_rows)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        if page > total_pages:
            page = total_pages
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)
        page_rows = all_rows[start_idx:end_idx]

        full["rows"] = page_rows
        full["pagination"] = {
            "page": page,
            "page_size": page_size,
            "total_rows": total_rows,
            "total_pages": total_pages,
            "start_row": (start_idx + 1) if total_rows else 0,
            "end_row": end_idx,
        }
        return full

    @api.model
    def action_kd_report_open(self, kind, payload=None):
        """Return a read-only/validated native Odoo action for drilling down from Report Center."""
        self._check_kd_access()
        payload = payload or {}
        if not isinstance(payload, dict):
            raise ValidationError(_("Tham số mở hồ sơ nguồn không hợp lệ."))

        if kind == "record":
            model_name = str(payload.get("model") or "").strip()
            allowed_models = {
                "project.project",
                "tp.contract",
                "tp.contract.revision",
                "crm.lead",
                "project.task",
                "tp.allocation",
                "tp.production",
                "tp.acceptance",
                "tp.payment.request",
                "tp.periodic.plan",
                "tp.credential",
                "tp.obligation",
            }
            if model_name not in allowed_models:
                raise ValidationError(_("Model hồ sơ nguồn không được phép mở từ báo cáo."))
            try:
                res_id = int(payload.get("res_id") or 0)
            except (TypeError, ValueError) as err:
                raise ValidationError(_("Mã bản ghi nguồn không hợp lệ.")) from err
            rec = self.env[model_name].browse(res_id).exists()
            if not rec:
                raise AccessError(_("Hồ sơ nguồn không tồn tại hoặc bạn không có quyền xem."))
            rec.check_access("read")
            if model_name == "tp.credential" and rec.subject_kind == "person" and not self.env.is_admin():
                if self.env.uid not in (rec.owner_id.id, rec.reviewer_id.id) and not rec.project_id._tp_head_allowed():
                    raise AccessError(_("Chứng chỉ cá nhân chỉ người phụ trách hoặc người rà soát mới có quyền xem."))
            custom_form_map = {
                "project.project": "tp_kd_workspace.project_governance_form",
                "tp.contract": "tp_contract.view_contract_form",
                "tp.contract.revision": "tp_contract.view_revision_form",
                "crm.lead": "tp_kd_workspace.opportunity_form",
                "project.task": "tp_kd_workspace.kd_task_form",
                "tp.allocation": "tp_kd_workspace.allocation_form",
                "tp.production": "tp_kd_workspace.production_form",
                "tp.acceptance": "tp_kd_workspace.acceptance_form",
                "tp.payment.request": "tp_kd_workspace.payment_form",
                "tp.periodic.plan": "tp_kd_workspace.plan_form",
                "tp.credential": "tp_kd_workspace.credential_form",
                "tp.obligation": "tp_kd_workspace.obligation_form",
            }
            view_xmlid = custom_form_map.get(model_name)
            view_ref = self.env.ref(view_xmlid, raise_if_not_found=False) if view_xmlid else False
            ctx = {**child_context(self.env), **kd_leaf(model_name)}
            if view_xmlid:
                ctx["form_view_ref"] = view_xmlid
            return {
                "type": "ir.actions.act_window",
                "name": rec.display_name,
                "res_model": model_name,
                "res_id": rec.id,
                "views": [(view_ref.id if view_ref else False, "form")],
                "view_mode": "form",
                "target": "current",
                "context": ctx,
            }

        if kind == "list":
            report_key = str(payload.get("report_key") or "R01").strip().upper()
            action_map = {
                "R01": "tp_contract.action_tp_contracts_list",
                "R02": "tp_kd_workspace.action_opportunities",
                "R03": "tp_kd_workspace.action_productions",
                "R04": "tp_kd_workspace.action_allocations",
                "R05": "tp_kd_workspace.action_tasks",
                "R06": "tp_kd_workspace.action_credentials",
            }
            xmlid = payload.get("action_xmlid") or action_map.get(report_key, "tp_kd_workspace.action_projects")
            allowed_xmlids = {
                "tp_kd_workspace.action_projects",
                "tp_kd_workspace.action_opportunities",
                "tp_kd_workspace.action_tasks",
                "tp_contract.action_tp_contracts_list",
                "tp_kd_workspace.action_allocations",
                "tp_kd_workspace.action_productions",
                "tp_kd_workspace.action_acceptances",
                "tp_kd_workspace.action_payments",
                "tp_kd_workspace.action_plans",
                "tp_kd_workspace.action_credentials",
                "tp_kd_workspace.action_obligations",
            }
            if xmlid not in allowed_xmlids:
                raise ValidationError(_("Danh sách nguồn không hợp lệ."))
            action = self.env["ir.actions.actions"]._for_xml_id(xmlid)
            self.env[action["res_model"]].check_access("read")
            return action

        raise ValidationError(_("Loại điều hướng báo cáo không hợp lệ."))

    def _build_xlsx_download(
        self,
        report_key="R01",
        filters=None,
        group_by=None,
        sort_by=None,
        sort_dir="asc",
        search="",
    ):
        full = self._compute_full_report(
            report_key=report_key,
            filters=filters,
            group_by=group_by,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=search,
        )
        all_rows = full["all_rows"]
        cols = full["columns"]
        meta = full["report_meta"]
        applied = full["applied_filters"]

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet(f"{meta['code']}_BaoCao")

        fmt_title = workbook.add_format({"bold": True, "font_size": 14, "font_color": "#1F2937"})
        fmt_sub = workbook.add_format({"italic": True, "font_size": 10, "font_color": "#4B5563"})
        fmt_meta_lbl = workbook.add_format({"bold": True, "font_size": 10, "bg_color": "#F4F6F8", "border": 1})
        fmt_meta_val = workbook.add_format({"font_size": 10, "border": 1})
        fmt_sec = workbook.add_format({"bold": True, "font_size": 11, "font_color": "#255F85"})
        fmt_th = workbook.add_format({
            "bold": True,
            "font_size": 10,
            "bg_color": "#EEF3F8",
            "font_color": "#1F2937",
            "border": 1,
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
        })
        fmt_td_left = workbook.add_format({"font_size": 10, "border": 1, "align": "left", "valign": "vcenter"})
        fmt_td_center = workbook.add_format({"font_size": 10, "border": 1, "align": "center", "valign": "vcenter"})
        fmt_td_right = workbook.add_format({"font_size": 10, "border": 1, "align": "right", "valign": "vcenter"})
        fmt_td_num = workbook.add_format({"font_size": 10, "border": 1, "align": "right", "valign": "vcenter", "num_format": "#,##0"})
        fmt_tfoot_lbl = workbook.add_format({"bold": True, "font_size": 10, "bg_color": "#F4F6F8", "border": 1})
        fmt_tfoot_val = workbook.add_format({"bold": True, "font_size": 10, "bg_color": "#F4F6F8", "border": 1, "align": "right"})

        # 1. Header metadata block
        sheet.write_string(0, 0, _sanitize_excel_text(f"TANPHAT ONE — BÁO CÁO KH-KD · {meta['code']}: {meta['title'].upper()}"), fmt_title)
        sheet.write_string(1, 0, _sanitize_excel_text(meta["question"]), fmt_sub)

        meta_rows = [
            ("Thời điểm xuất", full["updated_at"], "Người xuất báo cáo", _sanitize_excel_text(full["user_name"])),
            ("Kỳ báo cáo", _sanitize_excel_text(applied["period_label"]), "Dự án lọc", _sanitize_excel_text(applied["project_label"])),
            ("Người phụ trách", _sanitize_excel_text(applied["owner_label"]), "Trạng thái / Phân loại", _sanitize_excel_text(f"{applied['status_label']} · {applied['sub_filter_label']}")),
            ("Nhóm dữ liệu theo", _sanitize_excel_text(applied["group_by_label"]), "Sắp xếp / Từ khóa", _sanitize_excel_text(f"{applied['sort_by_label']} ({applied['sort_dir']}) · {applied['search'] or 'Không lọc từ khóa'}")),
            ("Quy tắc cộng tổng", _sanitize_excel_text(meta["basis_note"]), "Ghi chú loại trừ", _sanitize_excel_text(full["exclusion_info"]["note"])),
        ]
        fin_cnt = int(full.get("financial_project_count") or 0)
        acc_cnt = int(full.get("accessible_project_count") or 0)
        if not full.get("can_view_money"):
            meta_rows.append(("Quyền hạn số tiền", "Không có quyền xem tiền", "Lưu ý bảo mật", "Báo cáo xuất không bao gồm giá trị tiền tài chính"))
        elif acc_cnt and fin_cnt < acc_cnt:
            meta_rows.append(("Quyền hạn số tiền", f"Có quyền xem tiền theo phạm vi ({fin_cnt}/{acc_cnt} dự án)", "Lưu ý bảo mật", "Chỉ hiển thị và cộng tổng các khoản thuộc dự án được cấp quyền tài chính"))
        else:
            meta_rows.append(("Quyền hạn số tiền", f"Có quyền xem tiền ({fin_cnt} dự án trong quyền)", "Lưu ý bảo mật", "Chỉ cộng tổng các khoản đã xác nhận cùng đơn vị tiền tệ và cơ sở thuế"))
        r_idx = 3
        for m_row in meta_rows:
            sheet.write_string(r_idx, 0, m_row[0], fmt_meta_lbl)
            sheet.write_string(r_idx, 1, m_row[1], fmt_meta_val)
            sheet.write_string(r_idx, 2, m_row[2], fmt_meta_lbl)
            sheet.write_string(r_idx, 3, m_row[3], fmt_meta_val)
            r_idx += 1

        # 2. Summary cards section
        r_idx += 1
        sheet.write_string(r_idx, 0, "I. CHỈ TIÊU TỔNG HỢP TOÀN PHẠM VI LỌC", fmt_sec)
        r_idx += 1
        sheet.write_string(r_idx, 0, "Chỉ tiêu", fmt_th)
        sheet.write_string(r_idx, 1, "Giá trị tổng hợp", fmt_th)
        sheet.write_string(r_idx, 2, "Đơn vị", fmt_th)
        sheet.write_string(r_idx, 3, "Ghi chú nghiệp vụ", fmt_th)
        r_idx += 1
        for card in full["summary_cards"]:
            sheet.write_string(r_idx, 0, _sanitize_excel_text(card["label"]), fmt_td_left)
            sheet.write_string(r_idx, 1, _sanitize_excel_text(card["value"]), fmt_td_right)
            sheet.write_string(r_idx, 2, _sanitize_excel_text(card.get("unit") or ""), fmt_td_center)
            sheet.write_string(r_idx, 3, _sanitize_excel_text(card.get("note") or ""), fmt_td_left)
            r_idx += 1

        # 3. Group summary section
        r_idx += 1
        sheet.write_string(r_idx, 0, f"II. TỔNG HỢP THEO NHÓM ({applied['group_by_label'].upper()})", fmt_sec)
        r_idx += 1
        sheet.write_string(r_idx, 0, "Nhóm dữ liệu", fmt_th)
        sheet.write_string(r_idx, 1, "Số lượng bản ghi", fmt_th)
        sheet.write_string(r_idx, 2, "Chi tiết chỉ tiêu theo nhóm", fmt_th)
        r_idx += 1
        for grp in full["groups"]:
            sheet.write_string(r_idx, 0, _sanitize_excel_text(grp["label"]), fmt_td_left)
            sheet.write_number(r_idx, 1, int(grp["count"]), fmt_td_num)
            m_str = " · ".join(f"{m['label']}: {m['value']}" for m in grp["metrics"])
            sheet.write_string(r_idx, 2, _sanitize_excel_text(m_str), fmt_td_left)
            r_idx += 1

        # 4. Full detail table (ALL filtered rows, not just current page)
        r_idx += 1
        sheet.write_string(r_idx, 0, f"III. BẢNG CHI TIẾT ĐẦY ĐỦ ({len(all_rows)} DÒNG KẾT QUẢ)", fmt_sec)
        r_idx += 1
        detail_header_row = r_idx
        for c_idx, col in enumerate(cols):
            sheet.write_string(r_idx, c_idx, _sanitize_excel_text(col["label"]), fmt_th)
            sheet.set_column(c_idx, c_idx, 22 if col["kind"] in ("link", "text", "money") else 16)
        r_idx += 1

        for row in all_rows:
            for c_idx, col in enumerate(cols):
                key = col["key"]
                kind = col["kind"]
                val = row.get(key)
                if kind == "money":
                    cell_obj = val if isinstance(val, dict) else {}
                    if cell_obj.get("state") == "confirmed" and isinstance(cell_obj.get("amount"), (int, float)):
                        sheet.write_number(r_idx, c_idx, float(cell_obj["amount"]), fmt_td_num)
                    else:
                        disp = cell_obj.get("display") if isinstance(cell_obj, dict) else str(val or "—")
                        sheet.write_string(r_idx, c_idx, _sanitize_excel_text(disp), fmt_td_right)
                elif kind == "number" and isinstance(val, (int, float)):
                    sheet.write_number(r_idx, c_idx, float(val), fmt_td_num)
                elif kind == "badge":
                    lbl = val.get("label") if isinstance(val, dict) else str(val or "—")
                    sheet.write_string(r_idx, c_idx, _sanitize_excel_text(lbl), fmt_td_center)
                else:
                    fmt = fmt_td_center if col["align"] == "center" else (fmt_td_right if col["align"] == "right" else fmt_td_left)
                    sheet.write_string(r_idx, c_idx, _sanitize_excel_text(val if val is not None else "—"), fmt)
            r_idx += 1

        # 5. Totals footer row
        t_cells = full["totals_row"].get("cells", {})
        sheet.write_string(r_idx, 0, _sanitize_excel_text(full["totals_row"]["label"]), fmt_tfoot_lbl)
        for c_idx in range(1, len(cols)):
            col = cols[c_idx]
            key = col["key"]
            t_val = t_cells.get(key)
            if isinstance(t_val, dict):
                if t_val.get("single_amount") is not None and t_val.get("state") == "confirmed":
                    sheet.write_number(r_idx, c_idx, float(t_val["single_amount"]), fmt_tfoot_val)
                else:
                    sheet.write_string(r_idx, c_idx, _sanitize_excel_text(t_val.get("display") or "—"), fmt_tfoot_val)
            elif t_val is not None:
                sheet.write_string(r_idx, c_idx, _sanitize_excel_text(t_val), fmt_tfoot_val)
            else:
                sheet.write_string(r_idx, c_idx, "", fmt_tfoot_val)

        workbook.close()
        xlsx_bytes = output.getvalue()
        today_str = full["today"].replace("-", "")
        filename = f"TANPHAT_KD_{meta['code']}_{today_str}.xlsx"
        return {
            "filename": filename,
            "content": xlsx_bytes,
            "row_count": len(all_rows),
            "detail_header_row": detail_header_row + 1,
            "report_key": full["report_key"],
        }

    @api.model
    def export_kd_report_xlsx(
        self,
        report_key="R01",
        filters=None,
        group_by=None,
        sort_by=None,
        sort_dir="asc",
        search="",
    ):
        res = self._build_xlsx_download(
            report_key=report_key,
            filters=filters,
            group_by=group_by,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=search,
        )
        return {
            "filename": res["filename"],
            "content_base64": base64.b64encode(res["content"]).decode("ascii"),
            "row_count": res["row_count"],
            "report_key": res["report_key"],
        }
