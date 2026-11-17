"""XLSX reports use ORM domains/rights; text is never interpreted as a formula."""
import io
from datetime import date, datetime

import xlsxwriter

from odoo import _, fields, models
from odoo.exceptions import UserError

from .common import check_admin

REPORTS = {
    "maintenance.equipment": ("Sổ thiết bị", ["tp_code", "name", "category_id", "tp_asset_class", "tp_lifecycle",
        "tp_availability", "tp_technical_state", "tp_condition_note", "tp_verification", "tp_ownership",
        "tp_employee_id", "tp_employee_code", "tp_current_department_id", "tp_location_id", "serial_no", "tp_purchase_date", "tp_warranty_end",
        "tp_currency_id", "tp_purchase_value", "tp_source_ref"]),
    "maintenance.request": ("Sửa chữa", ["tp_code", "name", "equipment_id", "tp_kind", "tp_state", "tp_report_date",
        "tp_deadline", "tp_vendor_id", "tp_result", "tp_state_after", "tp_cost_known", "tp_currency_id", "tp_cost"]),
    "tp.equipment.move": ("Bàn giao thu hồi", ["name", "date", "move_type", "state", "target_employee_id",
        "target_department_id", "target_location_id", "target_partner_id", "expected_return_date", "line_count", "reason"]),
    "tp.equipment.move.line": ("Lịch sử bàn giao", ["move_id", "equipment_id", "state", "from_custody", "to_custody",
        "from_employee_id", "to_employee_id", "from_location_id", "to_location_id", "note"]),
    "tp.equipment.receipt": ("Phiếu nhập", ["name", "date", "source", "supplier_id", "document_ref", "state", "line_count", "note"]),
    "tp.equipment.proposal": ("Đề xuất", ["name", "title", "date", "review_state", "approval_state", "progress",
        "requester_employee_id", "requester_department_id", "currency_id", "amount_total", "approval_ref"]),
    "tp.equipment.inventory": ("Kiểm kê", ["name", "date", "state", "snapshot_date", "closed_date", "note"]),
    "tp.equipment.inventory.line": ("Dòng kiểm kê", ["inventory_id", "equipment_id", "count_state", "result",
        "expected_text", "actual_text", "expected_state", "actual_state", "note"]),
    "tp.equipment.import.batch": ("Nhập dữ liệu", ["name", "kind", "state", "file_name", "file_hash", "applied_date", "note"]),
}


def safe_text(value):
    text = str(value or "")
    return "'" + text if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text


class EquipmentReports(models.AbstractModel):
    _name = "tp.equipment.reports"
    _description = "Xuất báo cáo thiết bị"

    def _xlsx(self, model_name, domain, *, summary=False):
        if model_name not in REPORTS or not isinstance(domain, list):
            raise UserError(_("Báo cáo không hợp lệ."))
        check_admin(self.env, self.env[model_name])
        title, names = REPORTS[model_name]
        records = self.env[model_name].with_context(active_test=False).search(domain)
        records.check_access("read")
        if len(records) > 100000:
            raise UserError(_("Báo cáo vượt 100.000 dòng. Thu hẹp bộ lọc trước khi xuất."))
        output = io.BytesIO()
        book = xlsxwriter.Workbook(output, {"in_memory": True, "strings_to_formulas": False, "strings_to_urls": False})
        header = book.add_format({"bold": True, "bg_color": "#17324D", "font_color": "#FFFFFF", "text_wrap": True})
        date_fmt = book.add_format({"num_format": "dd/mm/yyyy"})
        datetime_fmt = book.add_format({"num_format": "dd/mm/yyyy hh:mm"})
        money_formats = {}

        def write_sheet(sheet_title, rows, field_names):
            sheet = book.add_worksheet(sheet_title[:31])
            sheet.freeze_panes(1, 0)
            sheet.set_column(0, len(field_names) - 1, 23)
            for col, name in enumerate(field_names):
                sheet.write_string(0, col, safe_text(rows._fields[name].string), header)
            for index, record in enumerate(rows, 1):
                for col, name in enumerate(field_names):
                    field = record._fields[name]
                    value = record[name]
                    if field.type == "monetary":
                        known = True
                        if name == "tp_purchase_value":
                            known = record.tp_purchase_value_known
                        elif name == "tp_cost":
                            known = record.tp_cost_known in ("known", "free")
                        elif name == "estimate_amount":
                            known = record.estimate_amount_known
                        elif name == "amount_total":
                            known = record.amount_total_known
                        if known:
                            currency = record[field.currency_field]
                            digits = currency.decimal_places
                            if digits not in money_formats:
                                money_formats[digits] = book.add_format({"num_format": "#,##0" + ("." + "0" * digits if digits else "")})
                            sheet.write_number(index, col, currency.round(value), money_formats[digits])
                        continue
                    if field.type == "datetime" and value:
                        local = fields.Datetime.context_timestamp(record, value).replace(tzinfo=None)
                        sheet.write_datetime(index, col, local, datetime_fmt)
                    elif isinstance(value, (datetime, date)):
                        sheet.write_datetime(index, col, value, date_fmt)
                    elif field.type in ("integer", "float"):
                        sheet.write_number(index, col, value)
                    elif field.type == "selection":
                        sheet.write_string(index, col, safe_text(dict(field._description_selection(record.env)).get(value, "")))
                    elif field.type == "many2one":
                        sheet.write_string(index, col, safe_text(value.display_name if value else ""))
                    else:
                        sheet.write_string(index, col, safe_text(value))
            sheet.autofilter(0, 0, max(len(rows), 1), len(field_names) - 1)

        write_sheet(title, records, names)
        if summary:
            for proposal in records:
                write_sheet(f"Dòng {proposal.name}", proposal.line_ids,
                            ["description", "kind", "equipment_id", "quantity", "uom_text", "estimate_amount",
                             "tax_note", "received_qty", "reserved_qty", "remaining_qty", "progress", "source_ref"])
        book.close()
        return output.getvalue()
