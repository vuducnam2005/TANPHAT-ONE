"""PDF output without wkhtmltopdf: handover record and QR label sheet (reportlab + bundled Roboto).

The handover PDF never draws a signature, stamp or "signed" mark: signature boxes stay empty and
the footer says so. Every value is escaped before it reaches a reportlab Paragraph.
"""

from io import BytesIO

from markupsafe import escape
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.fonts import addMapping
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from odoo import _, fields, models
from odoo.tools.misc import file_path

from .common import TECH_STATE, check_admin
from .move import MOVE_STATES, MOVE_TYPES, TITLES

FONT = "TpEqRoboto"
FONT_BOLD = "TpEqRobotoBold"


def _register_fonts():

    names = pdfmetrics.getRegisteredFontNames()
    if FONT not in names:
        pdfmetrics.registerFont(TTFont(FONT, file_path("web/static/fonts/google/Roboto/Roboto-Regular.ttf")))
    if FONT_BOLD not in names:
        pdfmetrics.registerFont(TTFont(FONT_BOLD, file_path("web/static/fonts/google/Roboto/Roboto-Bold.ttf")))
    addMapping(FONT, 0, 0, FONT)
    addMapping(FONT, 1, 0, FONT_BOLD)


def _t(value):
    """Escaped text for reportlab mini-markup."""
    return str(escape(value or ""))


class TpEquipmentPdf(models.AbstractModel):
    _name = "tp.equipment.pdf"
    _description = "Kho thiết bị — xuất PDF"

    # ------------------------------------------------------------------ handover
    def _tp_parties(self, move):
        Move = self.env["tp.equipment.move"]
        company = move.company_id.name
        stock = _("Kho thiết bị văn phòng – %s", company)
        lines = move.line_ids
        froms = {
            Move._tp_holder_text(line.from_custody, line.from_employee_id, line.from_department_id, line.from_location_id,
                                 line.from_partner_id)
            for line in lines if line.from_custody
        }
        source = froms.pop() if len(froms) == 1 else (_("Theo từng dòng thiết bị") if froms else stock)
        target_custody = move._tp_target_custody()
        target = Move._tp_holder_text(target_custody, move.target_employee_id, move.target_department_id,
                                      move.target_location_id, move.target_partner_id) if target_custody else ""
        kind = move.move_type
        if kind in ("assign", "loan"):
            return (_("BÊN GIAO"), stock), (_("BÊN NHẬN"), target)
        if kind == "transfer":
            return (_("BÊN GIAO"), source), (_("BÊN NHẬN"), target)
        if kind in ("return", "loan_return", "repair_return"):
            return (_("BÊN GIAO"), source), (_("BÊN NHẬN"), stock)
        if kind == "send_repair":
            return (_("BÊN GIAO"), source), (_("ĐƠN VỊ SỬA CHỮA"), target)
        if kind == "rental_return":
            partner = move.target_partner_id.display_name or ", ".join(
                lines.equipment_id.tp_owner_partner_id.mapped("display_name")) or _("Bên cho thuê")
            return (_("BÊN TRẢ"), company), (_("BÊN NHẬN"), partner)
        return (_("NGƯỜI LẬP PHIẾU"), move.responsible_id.name or ""), (_("XÁC NHẬN CỦA ĐƠN VỊ"), company)

    def _tp_handover_pdf(self, move):
        check_admin(self.env)
        move.ensure_one()
        _register_fonts()

        base = ParagraphStyle("base", fontName=FONT, fontSize=10, leading=13.5)
        small = ParagraphStyle("small", parent=base, fontSize=8.5, leading=11)
        center = ParagraphStyle("center", parent=base, alignment=TA_CENTER)
        bold_center = ParagraphStyle("bold_center", parent=center, fontName=FONT_BOLD)
        title = ParagraphStyle("title", parent=bold_center, fontSize=15, leading=20, spaceBefore=6, spaceAfter=2)
        cell = ParagraphStyle("cell", parent=base, fontSize=9, leading=11.5)
        cell_bold = ParagraphStyle("cell_bold", parent=cell, fontName=FONT_BOLD)

        company = move.company_id
        story = []
        header = Table([[
            Paragraph(f"<b>{_t(company.name.upper())}</b><br/>{_t(company.street or '')}", small),
            Paragraph("<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br/>Độc lập – Tự do – Hạnh phúc",
                      ParagraphStyle("nat", parent=small, alignment=TA_CENTER)),
        ]], colWidths=[85 * mm, 95 * mm])
        header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        story += [header, Spacer(1, 6 * mm)]
        story.append(Paragraph(_t(TITLES.get(move.move_type, "BIÊN BẢN THIẾT BỊ")), title))
        date = (move.date_done and fields.Datetime.context_timestamp(move, move.date_done).date()) or move.date
        story.append(Paragraph(_t(_("Số: %(name)s – Ngày %(d)s tháng %(m)s năm %(y)s", name=move.name,
                                    d=f"{date.day:02d}", m=f"{date.month:02d}", y=date.year)), center))
        if move.state != "done":
            story.append(Paragraph(_t(_("Bản in khi phiếu đang “%s”: chưa phải biên bản hoàn tất.",
                                        dict(MOVE_STATES)[move.state])),
                                   ParagraphStyle("warn", parent=center, textColor=colors.HexColor("#9a5b00"))))
        if move.reversed_by_id:
            story.append(Paragraph(_t(_("Phiếu đã được đảo bởi %s.", move.reversed_by_id.name)),
                                   ParagraphStyle("rev", parent=center, textColor=colors.HexColor("#a12a2a"))))
        story.append(Spacer(1, 5 * mm))

        (left_label, left_value), (right_label, right_value) = self._tp_parties(move)
        info = [
            [Paragraph(f"<b>{_t(left_label)}:</b> {_t(left_value)}", base)],
            [Paragraph(f"<b>{_t(right_label)}:</b> {_t(right_value)}", base)],
        ]
        employee = move.target_employee_id.sudo()
        if employee and move.move_type in ("assign", "transfer", "loan"):
            job = employee.job_title or employee.job_id.name or ""
            if job:
                info.append([Paragraph(f"<b>{_t(_('Chức danh bên nhận'))}:</b> {_t(job)}", base)])
        if move.move_type == "loan" and move.expected_return_date:
            info.append([Paragraph(f"<b>{_t(_('Hẹn trả'))}:</b> {move.expected_return_date.strftime('%d/%m/%Y')}", base)])
        info.append([Paragraph(f"<b>{_t(_('Loại phiếu'))}:</b> {_t(dict(MOVE_TYPES)[move.move_type])}", base)])
        info_table = Table(info, colWidths=[180 * mm])
        info_table.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
        story += [info_table, Spacer(1, 4 * mm)]

        states = dict(TECH_STATE)
        rows = [[Paragraph(_t(h), cell_bold) for h in (
            _("STT"), _("Mã thiết bị"), _("Tên thiết bị"), _("Hãng / Model / Serial"), _("Cấu hình / phụ kiện"),
            _("Tình trạng"))]]
        for index, line in enumerate(move.line_ids, start=1):
            equipment = line.equipment_id
            ident = " / ".join(filter(None, [equipment.tp_brand, equipment.model,
                                             equipment.serial_no and f"S/N {equipment.serial_no}"]))
            config = "; ".join(filter(None, [equipment.tp_cpu, equipment.tp_ram, equipment.tp_storage,
                                              line.accessories and _("Kèm: %s", line.accessories)]))
            state = line.condition or line.from_technical_state or equipment.tp_technical_state
            rows.append([
                Paragraph(str(index), cell), Paragraph(_t(equipment.tp_code), cell), Paragraph(_t(equipment.name), cell),
                Paragraph(_t(ident), cell), Paragraph(_t(config), cell),
                Paragraph(_t(states.get(state, "")) + (f"<br/>{_t(line.note)}" if line.note else ""), cell),
            ])
        table = Table(rows, colWidths=[12 * mm, 24 * mm, 39 * mm, 39 * mm, 42 * mm, 24 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#5b6b7c")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef4")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story += [table, Spacer(1, 4 * mm)]
        if (move.reason or "").strip():
            story.append(Paragraph(f"<b>{_t(_('Lý do / ghi chú'))}:</b> {_t(move.reason).replace(chr(10), '<br/>')}",
                                   base))
        if move.reversal_of_id:
            story.append(Paragraph(_t(_("Phiếu này đảo phiếu %s.", move.reversal_of_id.name)), base))
        story.append(Paragraph(_t(_("Hai bên đã kiểm tra số lượng, tình trạng thiết bị như trên. Biên bản lập thành "
                                    "02 bản, mỗi bên giữ 01 bản.")), base))
        story.append(Spacer(1, 8 * mm))
        signature = Table([
            [Paragraph(_t(left_label), bold_center), Paragraph(_t(right_label), bold_center)],
            [Paragraph(_t(_("(Ký, ghi rõ họ tên)")), center), Paragraph(_t(_("(Ký, ghi rõ họ tên)")), center)],
            ["", ""],
        ], colWidths=[90 * mm, 90 * mm], rowHeights=[None, None, 28 * mm])
        story.append(KeepTogether([signature]))

        generated = fields.Datetime.context_timestamp(move, fields.Datetime.now()).strftime("%d/%m/%Y %H:%M")
        footer_text = _("In từ TANPHAT ONE – phiếu %(name)s lúc %(at)s. Hệ thống không tạo chữ ký: các bên ký trực "
                        "tiếp trên bản in.", name=move.name, at=generated)

        def on_page(canvas, doc):
            canvas.saveState()
            canvas.setFont(FONT, 7.5)
            canvas.setFillColor(colors.HexColor("#5b6b7c"))
            canvas.drawString(15 * mm, 10 * mm, footer_text)
            canvas.drawRightString(195 * mm, 10 * mm, _("Trang %s", doc.page))
            canvas.restoreState()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=14 * mm,
                                bottomMargin=18 * mm, title=move.name, author=company.name, creator="TANPHAT ONE")
        doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
        return buffer.getvalue()

    # ------------------------------------------------------------------ labels
    def _tp_labels_pdf(self, equipments):
        check_admin(self.env)
        _register_fonts()

        buffer = BytesIO()
        page_w, page_h = A4
        cols, rows = 3, 8
        label_w, label_h = 70 * mm, 37 * mm
        margin_x = (page_w - cols * label_w) / 2
        margin_y = (page_h - rows * label_h) / 2
        qr_size = 30 * mm
        c = pdf_canvas.Canvas(buffer, pagesize=A4)
        c.setTitle(_("Nhãn QR thiết bị"))
        c.setCreator("TANPHAT ONE")
        company = self.env.company.name or ""
        base = equipments[:1].get_base_url() if equipments else ""

        def fit(text, font, size, width):
            text = text or ""
            while text and c.stringWidth(text, font, size) > width:
                text = text[:-2] + "…" if len(text) > 2 else ""
            return text

        for index, equipment in enumerate(equipments):
            slot = index % (cols * rows)
            if index and slot == 0:
                c.showPage()
            col, row = slot % cols, slot // cols
            x = margin_x + col * label_w
            y = page_h - margin_y - (row + 1) * label_h
            c.setStrokeColor(colors.HexColor("#c9d3dd"))
            c.setLineWidth(0.3)
            c.rect(x + 1 * mm, y + 1 * mm, label_w - 2 * mm, label_h - 2 * mm)
            widget = QrCodeWidget(f"{base}/tp_equipment/qr/{equipment.sudo().tp_qr_token}")
            widget.barLevel = "M"
            bx1, by1, bx2, by2 = widget.getBounds()
            drawing = Drawing(qr_size, qr_size, transform=[qr_size / (bx2 - bx1), 0, 0, qr_size / (by2 - by1), 0, 0])
            drawing.add(widget)
            renderPDF.draw(drawing, c, x + 3 * mm, y + (label_h - qr_size) / 2)
            text_x = x + 3 * mm + qr_size + 2 * mm
            text_w = label_w - (text_x - x) - 3 * mm
            c.setFillColor(colors.HexColor("#5b6b7c"))
            c.setFont(FONT, 6.5)
            c.drawString(text_x, y + label_h - 8 * mm, fit(company.upper(), FONT, 6.5, text_w))
            c.setFillColor(colors.black)
            c.setFont(FONT_BOLD, 12)
            c.drawString(text_x, y + label_h - 14 * mm, fit(equipment.tp_code, FONT_BOLD, 12, text_w))
            c.setFont(FONT, 8)
            name = equipment.name or ""
            first = fit(name, FONT, 8, text_w)
            c.drawString(text_x, y + label_h - 19 * mm, first)
            if len(first) < len(name) and first.endswith("…"):
                rest = name[len(first) - 1:].lstrip()
                c.drawString(text_x, y + label_h - 23 * mm, fit(rest, FONT, 8, text_w))
            c.setFillColor(colors.HexColor("#5b6b7c"))
            c.setFont(FONT, 6.5)
            c.drawString(text_x, y + 5 * mm, fit(equipment.category_id.name, FONT, 6.5, text_w))
        if not equipments:
            c.setFont(FONT, 11)
            c.drawString(20 * mm, page_h - 30 * mm, _("Không có thiết bị nào để in nhãn."))
        c.save()
        return buffer.getvalue()
