import json
import re

from markupsafe import escape

from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition

from odoo.addons.tp_equipment.models.common import GENERIC_DENIED, is_admin

TOKEN_RE = re.compile(r"^[0-9a-f]{32}$")


def _page(title, message, status):
    body = (
        "<!DOCTYPE html><html lang='vi'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{escape(title)}</title>"
        "<style>body{font-family:system-ui,Segoe UI,Arial,sans-serif;background:#f4f6f9;color:#17324d;margin:0;"
        "display:flex;min-height:100vh;align-items:center;justify-content:center;padding:16px}"
        "main{background:#fff;border:1px solid #d8e0e8;border-radius:12px;max-width:440px;padding:24px}"
        "h1{font-size:20px;margin:0 0 8px}p{margin:0 0 16px;line-height:1.5}"
        "a{display:inline-block;min-height:44px;line-height:44px;padding:0 16px;border-radius:8px;"
        "background:#17324d;color:#fff;text-decoration:none}</style></head><body><main>"
        f"<h1>{escape(title)}</h1><p>{escape(message)}</p><a href='/odoo'>Về trang chủ</a></main></body></html>"
    )
    return request.make_response(body, headers=[("Content-Type", "text/html; charset=utf-8"),
                                                ("Cache-Control", "no-store"),
                                                ("X-Robots-Tag", "noindex")], status=status)


class TpEquipmentQr(http.Controller):
    """QR labels carry an opaque random token, never the code, serial, holder or IP."""

    @http.route("/tp_equipment/qr/<string:token>", type="http", auth="user", methods=["GET"], readonly=True)
    def open_by_qr(self, token, **kwargs):
        if not is_admin(request.env):
            # Same answer whether the token exists or not: no existence oracle for non-admins.
            return _page("Không có quyền truy cập", GENERIC_DENIED, 403)
        token = (token or "").strip().lower()
        equipment = request.env["maintenance.equipment"]
        if TOKEN_RE.match(token):
            equipment = equipment.with_context(active_test=False).search([("tp_qr_token", "=", token)], limit=1)
        if not equipment:
            return _page("Mã QR không hợp lệ",
                         "Nhãn này không khớp thiết bị nào hoặc đã được cấp lại. Tra cứu theo mã thiết bị trong "
                         "Kho thiết bị văn phòng.", 404)
        return request.redirect(f"/odoo/kho-thiet-bi/{equipment.id}")


def _pdf(content, filename):
    return request.make_response(content, headers=[
        ("Content-Type", "application/pdf"),
        ("Content-Length", str(len(content))),
        ("Content-Disposition", content_disposition(filename, "inline")),
        ("Cache-Control", "no-store"),
        ("X-Robots-Tag", "noindex"),
    ])


class TpEquipmentPdfController(http.Controller):
    """Handover record and QR labels: admin only, same answer for missing and forbidden ids."""

    @http.route("/tp_equipment/move/<int:move_id>/handover.pdf", type="http", auth="user", methods=["GET"],
                readonly=True)
    def move_handover(self, move_id, **kwargs):
        if not is_admin(request.env):
            return _page("Không có quyền truy cập", GENERIC_DENIED, 403)
        move = request.env["tp.equipment.move"].browse(move_id).exists()
        if not move or move.state not in ("pending", "done"):
            return _page("Không có biên bản", "Phiếu không tồn tại hoặc chưa được xác nhận.", 404)
        content = request.env["tp.equipment.pdf"]._tp_handover_pdf(move)
        return _pdf(content, f"{move.name}.pdf")

    @http.route("/tp_equipment/labels.pdf", type="http", auth="user", methods=["GET"], readonly=True)
    def labels(self, ids="", **kwargs):
        if not is_admin(request.env):
            return _page("Không có quyền truy cập", GENERIC_DENIED, 403)
        try:
            id_list = [int(part) for part in (ids or "").split(",") if part.strip()][:240]
        except ValueError:
            id_list = []
        equipments = request.env["maintenance.equipment"].with_context(active_test=False).browse(id_list).exists()
        equipments = equipments.filtered(lambda e: e.tp_lifecycle != "draft")
        if not equipments:
            return _page("Không có nhãn để in", "Chọn thiết bị đã đăng ký vào kho rồi in nhãn QR.", 404)
        content = request.env["tp.equipment.pdf"]._tp_labels_pdf(equipments)
        return _pdf(content, "nhan-qr-thiet-bi.pdf")


def _xlsx(content, filename):
    return request.make_response(content, headers=[
        ("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("Content-Disposition", content_disposition(filename)),
        ("Cache-Control", "no-store"), ("X-Robots-Tag", "noindex"),
    ])


class TpEquipmentExcelController(http.Controller):
    @http.route(["/tp_equipment/export.xlsx", "/tp_equipment/equipment.xlsx"], type="http", auth="user",
                methods=["GET", "POST"], readonly=True)
    def export(self, model="maintenance.equipment", domain="[]", **kwargs):
        if not is_admin(request.env):
            return _page("Không có quyền truy cập", GENERIC_DENIED, 403)
        try:
            parsed = json.loads(domain)
            if not isinstance(parsed, list):
                return _page("Bộ lọc không hợp lệ", "Mở lại danh sách và xuất theo bộ lọc đã áp dụng.", 400)
        except (ValueError, TypeError):
            return _page("Bộ lọc không hợp lệ", "Mở lại danh sách và xuất theo bộ lọc đã áp dụng.", 400)
        content = request.env["tp.equipment.reports"]._xlsx(model, parsed)
        return _xlsx(content, "bao-cao-thiet-bi.xlsx")

    @http.route("/tp_equipment/proposal/<int:proposal_id>/summary.xlsx", type="http", auth="user",
                methods=["GET"], readonly=True)
    def proposal_summary(self, proposal_id, **kwargs):
        if not is_admin(request.env):
            return _page("Không có quyền truy cập", GENERIC_DENIED, 403)
        proposal = request.env["tp.equipment.proposal"].browse(proposal_id).exists()
        if not proposal:
            return _page("Không có đề xuất", "Đề xuất không tồn tại trong phạm vi được phép.", 404)
        proposal.check_access("read")
        content = request.env["tp.equipment.reports"]._xlsx("tp.equipment.proposal", [("id", "=", proposal.id)], summary=True)
        return _xlsx(content, f"{proposal.name}.xlsx")
