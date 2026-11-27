import json

from odoo import _
from odoo.exceptions import AccessError, ValidationError
from odoo.http import Controller, request, route
from odoo.http.stream import content_disposition


class KdReportExportController(Controller):
    @route("/tp_kd/report/export", type="http", auth="user", methods=["POST", "GET"], csrf=False)
    def export_kd_report(self, **params):
        if not request.env.user.has_group("tp_core.group_user"):
            raise AccessError(_("Bạn không có quyền truy cập Trung tâm Báo cáo KH-KD."))
        request.env["tp.kd.report.center"].check_access("read")

        report_key = params.get("report_key") or "R01"
        raw_filters = params.get("filters") or "{}"
        if isinstance(raw_filters, str):
            try:
                filters = json.loads(raw_filters) if raw_filters.strip() else {}
            except ValueError as err:
                raise ValidationError(_("Bộ lọc xuất báo cáo không hợp lệ.")) from err
        elif isinstance(raw_filters, dict):
            filters = raw_filters
        else:
            filters = {}

        group_by = params.get("group_by") or None
        sort_by = params.get("sort_by") or None
        sort_dir = params.get("sort_dir") or "asc"
        search = params.get("search") or ""

        payload = request.env["tp.kd.report.center"]._build_xlsx_download(
            report_key=report_key,
            filters=filters,
            group_by=group_by,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=search,
        )
        headers = [
            ("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("Content-Disposition", content_disposition(payload["filename"])),
            ("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0"),
            ("Pragma", "no-cache"),
            ("X-Content-Type-Options", "nosniff"),
        ]
        return request.make_response(payload["content"], headers=headers)
