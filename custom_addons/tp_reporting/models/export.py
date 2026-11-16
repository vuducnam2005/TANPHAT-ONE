"""Private exports are generated in the requesting user's transaction, never cached."""
import io
import json
import os
import re
import zipfile
from urllib.parse import urlencode
from xml.sax.saxutils import escape

import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

LINE_COLUMNS = [
    ('name', 'Công việc'), ('expected_output', 'Đầu ra dự kiến'),
    ('work_deadline', 'Hạn công việc'), ('priority', 'Mức ưu tiên'),
    ('work_status', 'Trạng thái công việc'), ('collaborator_ids', 'ID người phối hợp'),
    ('work_date', 'Ngày'), ('planned_quantity', 'Kế hoạch'),
    ('quantity', 'Thực hiện'), ('variance', 'Chênh lệch'),
    ('unit', 'Đơn vị'), ('result', 'Kết quả'), ('cause', 'Nguyên nhân'),
    ('next_action', 'Việc tiếp theo'), ('project_id', 'ID dự án'),
    ('task_id', 'ID công việc'), ('plan_id', 'ID kế hoạch'),
    ('contribution_key', 'Khóa đóng góp'), ('stable_key', 'ID đầu việc ổn định'),
    ('deviation_reason', 'Lý do lệch kế hoạch'),
    ('is_emergent', 'Việc phát sinh'), ('emergence_reason', 'Lý do phát sinh'),
    ('assigned_by_id', 'ID người giao'), ('origin_line_id', 'ID dòng nguồn chuyển tiếp'),
    ('carry_reason', 'Lý do chuyển tiếp'),
]


def text(value):
    if value is None or value is False:
        return 'Chưa xác nhận'
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def xml_text(value):
    return escape(re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', str(value)))


def safe_cell(value):
    value = text(value)
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value


def document_sections(payload):
    """One presentation source for Word and PDF; no live-source recalculation."""
    yield payload.get('name', 'Báo cáo')
    yield 'NHÁP — chưa gửi/chốt' if payload.get('_draft') else 'BẢN LƯU — phiên bản đã gửi/chốt'
    for key, label in [('company', 'Công ty'), ('department', 'Phòng ban'),
                       ('owner', 'Người chịu trách nhiệm'), ('level', 'Phạm vi'), ('period_type', 'Loại kỳ'),
                       ('date_start', 'Từ ngày'), ('date_end', 'Đến ngày'),
                       ('version', 'Phiên bản'), ('coverage', 'Mức bao phủ'),
                       ('coverage_reason', 'Lý do thiếu báo cáo'), ('_exported_at', 'Ngày xuất')]:
        value = payload.get(key)
        if key == 'level':
            value = {'personal': 'Cá nhân', 'department': 'Phòng ban', 'company': 'Công ty'}.get(value, value)
        elif key == 'period_type':
            value = {'week': 'Tuần', 'month': 'Tháng', 'quarter': 'Quý', 'cumulative': 'Lũy kế'}.get(value, value)
        yield f'{label}: {text(value)}'
    for key, label in [('summary', 'Tóm tắt'), ('obstacles', 'Vướng mắc'),
                       ('recommendations', 'Kiến nghị'), ('next_plan', 'Kế hoạch tiếp theo')]:
        yield label
        yield text(payload.get(key))
    yield 'Kế hoạch — thực hiện — chênh lệch / kết quả'
    for line in payload.get('lines', []):
        yield ' | '.join(f'{label}: {text(line.get(key))}' for key, label in LINE_COLUMNS)
    yield 'Nguồn / phiên bản phụ thuộc'
    for dependency in payload.get('dependencies', []):
        yield 'Báo cáo #%s • phiên bản %s • bản lưu #%s' % (dependency.get('document_id'), dependency.get('version'), dependency.get('id'))
    if not payload.get('dependencies'):
        yield 'Chưa có bản nguồn phụ thuộc.'
    yield 'Mẫu báo cáo / phiên bản'
    template = payload.get('template', {})
    yield '%s • phiên bản %s' % (template.get('name') or 'Chưa chọn mẫu', template.get('version', '—'))
    for section in payload.get('section_contents', []):
        yield section.get('section_name', 'Nội dung theo mẫu')
        yield text(section.get('content'))
        for key, label in [('design_stage', 'Bước thiết kế'), ('package_reference', 'Gói / đoạn / hạng mục'),
                           ('submission_reference', 'Hồ sơ trình / lần trình'), ('quality_review', 'KCS / thẩm tra'),
                           ('missing_inputs', 'Đầu vào còn thiếu'), ('business_source_kind', 'Loại nguồn KH-KD'),
                           ('source_reference', 'Tham chiếu nguồn')]:
            if section.get(key):
                yield f'{label}: {text(section[key])}'
    yield 'Nhận xét đã công bố / phản hồi'
    for review in payload.get('_reviews', []):
        yield 'Phiên bản %s • %s • %s%s' % (
            review.get('version'), review.get('actor') or 'Người dùng #%s' % review.get('actor_id'),
            review.get('created_at'), ' • đầu việc %s' % review['line_key'] if review.get('line_key') else '')
        yield review.get('comment', '')
        assessment = {'satisfactory': 'Đáp ứng', 'needs_change': 'Cần bổ sung', 'note': 'Ý kiến'}.get(review.get('assessment'), '')
        yield 'Đánh giá: %s%s%s' % (assessment, ' • phản hồi #%s' % review['parent_id'] if review.get('parent_id') else '',
                                    ' • đính chính #%s' % review['correction_of_id'] if review.get('correction_of_id') else '')
    yield payload.get('_finance_notice', 'Số tài chính không thuộc nội dung bản xuất này.')
    for value in payload.get('_finance', []):
        yield '%s: %s %s • %s • %s' % (value.get('name'), text(value.get('amount')), value.get('currency'),
                                        value.get('status'), value.get('tax_basis'))
        yield 'Nguồn: %s • ngày %s • người cung cấp #%s • người xác nhận #%s • phạm vi %s' % (
            value.get('source_reference'), value.get('source_date'), value.get('provider_id'),
            value.get('confirmer_id') or 'Chưa xác nhận', value.get('coverage_key'))


def make_docx(payloads):
    paragraphs = []
    for index, payload in enumerate(payloads):
        if index:
            paragraphs.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        for paragraph_index, paragraph in enumerate(document_sections(payload)):
            for line in str(paragraph).splitlines() or ['']:
                formatting = '<w:rPr><w:b/><w:sz w:val="32"/></w:rPr>' if paragraph_index == 0 else ''
                paragraphs.append('<w:p><w:r>' + formatting + '<w:t xml:space="preserve">'
                                  + xml_text(line) + '</w:t></w:r></w:p>')
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?>'
                         '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                         '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                         '<Default Extension="xml" ContentType="application/xml"/>'
                         '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                         '</Types>')
        archive.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?>'
                         '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                         '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                         '</Relationships>')
        archive.writestr('word/document.xml', '<?xml version="1.0" encoding="UTF-8"?>'
                         '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                         '<w:body>' + ''.join(paragraphs)
                         + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
                         '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/>'
                         '</w:sectPr></w:body></w:document>')
    return output.getvalue()


def make_pdf(payloads):
    font_name = 'TPReporting'
    if font_name not in pdfmetrics.getRegisteredFontNames():
        paths = [os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts', 'arial.ttf'),
                 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
        font_path = next((path for path in paths if os.path.isfile(path)), None)
        if not font_path:
            raise UserError(_('Cần font Unicode Arial hoặc DejaVu Sans để xuất PDF tiếng Việt.'))
        pdfmetrics.registerFont(TTFont(font_name, font_path))
    output = io.BytesIO()
    style = ParagraphStyle('TPReport', parent=getSampleStyleSheet()['BodyText'],
                           fontName=font_name, fontSize=10, leading=15, textColor=colors.HexColor('#17324D'))
    story = []
    for payload in payloads:
        for paragraph in document_sections(payload):
            story.extend([Paragraph(xml_text(paragraph).replace('\n', '<br/>'), style), Spacer(1, 7)])
    if not story:
        story.append(Paragraph('Không có báo cáo trong bộ lọc.', style))
    SimpleDocTemplate(output, title='TANPHAT ONE — Báo cáo',
                      leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=42).build(story)
    return output.getvalue()


class ReportingExport(models.AbstractModel):
    _name = 'tp.reporting.export'
    _description = 'Xuất báo cáo riêng tư'

    def _payload(self, document, snapshot_id=None):
        document.check_access('read')
        draft = document.state in ('draft', 'returned') and not snapshot_id
        snapshot = document.current_snapshot_id
        if snapshot_id:
            snapshot = self.env['tp.report.snapshot'].browse(snapshot_id).exists()
            snapshot.check_access('read')
            if not snapshot or snapshot.document_id != document:
                raise AccessError(_('Phiên bản không thuộc báo cáo được yêu cầu.'))
        if draft:
            payload = document._snapshot_payload()
        elif snapshot:
            snapshot.check_access('read')
            payload = json.loads(snapshot.payload)
        else:
            raise UserError(_('Báo cáo chưa có phiên bản lưu hợp lệ.'))
        payload = dict(payload)
        # Never include caller-injected or general JSON financial content.
        payload.pop('_finance', None)
        payload['_draft'] = draft
        payload['_exported_at'] = str(fields.Datetime.now())
        review_snapshots = payload.get('review_snapshot_ids', [])
        review_snapshots = [value for value in review_snapshots if type(value) is int]
        if not draft and snapshot:
            review_snapshots.append(snapshot.id)
        reviews = self.env['tp.report.review'].search([
            ('document_id', '=', document.id), ('snapshot_id', 'in', review_snapshots),
            ('audience', '=', 'published'),
        ], order='id') if review_snapshots else self.env['tp.report.review']
        reviews.check_access('read')
        payload['_reviews'] = [{
            'id': review.id, 'line_key': review.line_key, 'version': review.version,
            'actor_id': review.actor_id.id, 'actor': review.actor_id.name, 'comment': review.comment,
            'assessment': review.assessment, 'parent_id': review.parent_id.id,
            'correction_of_id': review.correction_of_id.id,
            'created_at': str(review.create_date),
        } for review in reviews]
        payload['_finance_notice'] = 'Số tài chính được bảo vệ riêng; không kèm trong bản xuất này.'
        if document._has_capability('finance_read'):
            domain = [('document_id', '=', document.id)]
            if not draft:
                domain.append(('snapshot_ids', 'in', snapshot.ids))
            values = self.env['tp.report.value'].search(domain, order='id')
            values.check_access('read')
            payload['_finance'] = [{
                'name': value.name, 'metric_id': value.metric_id.id,
                'amount': value.amount if value.status in ('confirmed', 'estimated', 'pending', 'no_activity') else None,
                'currency': value.currency_id.name, 'tax_basis': value.tax_basis,
                'status': value.status, 'source_reference': value.source_reference,
                'source_date': str(value.source_date or ''), 'provider_id': value.provider_id.id,
                'confirmer_id': value.confirmer_id.id, 'coverage_key': value.coverage_key,
            } for value in values]
            payload['_finance_notice'] = 'Nguồn tài chính riêng; chỉ số Đã xác nhận được dùng làm số chính thức. Không cộng khác tiền/cơ sở thuế.'
        return payload

    def _documents(self, selected, domain):
        if not isinstance(domain, list) or (selected is not None and
                (not selected or any(type(value) is not int or value <= 0 for value in selected))):
            raise ValidationError(_('Phạm vi xuất báo cáo không hợp lệ.'))
        documents = self.env['tp.report.document']
        documents.check_access('read')
        if selected is not None:
            records = documents.browse(list(dict.fromkeys(selected))).exists()
            if len(records) != len(set(selected)):
                raise AccessError(_('Có báo cáo không còn tồn tại hoặc không được phép xuất.'))
            records.check_access('read')
            yield from records.sorted('id')
            return
        # Keyset pagination avoids silently dropping records beyond the current UI page.
        last_id = 0
        while True:
            records = documents.search(domain + [('id', '>', last_id)], order='id', limit=500)
            if not records:
                break
            records.check_access('read')
            yield from records
            last_id = records[-1].id

    def _build(self, format, selected=None, domain=None, snapshot_id=None):
        domain = [] if domain is None else domain
        if format not in ('xlsx', 'docx', 'pdf'):
            raise ValidationError(_('Định dạng báo cáo không hợp lệ.'))
        if snapshot_id and (not selected or len(selected) != 1):
            raise ValidationError(_('Chọn đúng một báo cáo để xuất phiên bản lịch sử.'))
        documents = list(self._documents(selected, domain))
        payloads = [self._payload(document, snapshot_id) for document in documents]
        if format == 'xlsx':
            content = self._xlsx(payloads)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif format == 'docx':
            content = make_docx(payloads)
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            content = make_pdf(payloads)
            mimetype = 'application/pdf'
        # No permanent file or bearer URL: download rights are checked on every request.
        for document, payload in zip(documents, payloads, strict=True):
            document.check_access('read')
            if '_finance' in payload:
                document._require('finance_read')
        return {'content': content, 'mimetype': mimetype, 'filename': f'TANPHAT-ONE-bao-cao.{format}'}

    def _xlsx(self, payloads):
        output = io.BytesIO()
        book = xlsxwriter.Workbook(output, {'in_memory': True, 'strings_to_formulas': False,
                                           'strings_to_urls': False})
        header = book.add_format({'bold': True, 'bg_color': '#17324D', 'font_color': '#FFFFFF', 'text_wrap': True})
        wrap = book.add_format({'text_wrap': True, 'valign': 'top'})
        specs = [
            ('Tóm tắt', [('name', 'Báo cáo'), ('company', 'Công ty'), ('department', 'Phòng ban'),
                         ('owner', 'Người chịu trách nhiệm'), ('level', 'Phạm vi'), ('date_start', 'Từ ngày'),
                         ('date_end', 'Đến ngày'), ('version', 'Phiên bản'), ('_draft', 'Nháp'),
                         ('summary', 'Tóm tắt'), ('coverage', 'Mức bao phủ'),
                         ('coverage_reason', 'Lý do thiếu báo cáo'), ('_exported_at', 'Ngày xuất')], payloads),
            ('Kế hoạch - Kết quả', [('report', 'Báo cáo')] + LINE_COLUMNS,
             [dict(line, report=payload.get('name')) for payload in payloads for line in payload.get('lines', [])]),
            ('Vướng mắc - Kiến nghị', [('name', 'Báo cáo'), ('obstacles', 'Vướng mắc'),
                                      ('recommendations', 'Kiến nghị'), ('next_plan', 'Kế hoạch tiếp theo')], payloads),
            ('Nguồn - Phiên bản', [('name', 'Báo cáo'), ('version', 'Phiên bản'),
                                  ('dependencies', 'Nguồn phụ thuộc'), ('template', 'Mẫu'),
                                  ('_finance_notice', 'Số tài chính')], payloads),
        ]
        specs.append(('Nhận xét - Phản hồi', [
            ('report', 'Báo cáo'), ('id', 'ID nhận xét'), ('line_key', 'Đầu việc'),
            ('version', 'Phiên bản'), ('actor_id', 'ID người nhận xét'), ('comment', 'Nội dung công bố'),
            ('assessment', 'Đánh giá'), ('parent_id', 'Phản hồi nhận xét'),
            ('correction_of_id', 'Đính chính nhận xét'), ('created_at', 'Thời gian'),
        ], [dict(review, report=payload.get('name')) for payload in payloads
            for review in payload.get('_reviews', [])]))
        specs.append(('Nội dung theo mẫu', [
            ('report', 'Báo cáo'), ('section_name', 'Phần mẫu'), ('content', 'Nội dung'),
            ('design_stage', 'Bước thiết kế'), ('package_reference', 'Gói / đoạn / hạng mục'),
            ('submission_reference', 'Hồ sơ / lần trình'), ('quality_review', 'KCS / thẩm tra'),
            ('missing_inputs', 'Đầu vào còn thiếu'), ('business_source_kind', 'Loại nguồn KH-KD'),
            ('source_reference', 'Tham chiếu nguồn'),
        ], [dict(section, report=payload.get('name')) for payload in payloads
            for section in payload.get('section_contents', [])]))
        finance = [dict(value, report=payload.get('name')) for payload in payloads
                   for value in payload.get('_finance', [])]
        if any('_finance' in payload for payload in payloads):
            specs.append(('Nguồn tài chính', [
                ('report', 'Báo cáo'), ('name', 'Chỉ tiêu'), ('metric_id', 'ID định nghĩa'),
                ('amount', 'Giá trị nguồn'), ('currency', 'Tiền tệ'), ('tax_basis', 'Cơ sở thuế'),
                ('status', 'Trạng thái xác nhận'), ('source_reference', 'Nguồn'),
                ('source_date', 'Ngày nguồn'), ('provider_id', 'ID người cung cấp'),
                ('confirmer_id', 'ID người xác nhận'), ('coverage_key', 'Phạm vi chống trùng'),
            ], finance))
        for title, columns, rows in specs:
            sheet = book.add_worksheet(title)
            sheet.freeze_panes(1, 0)
            sheet.set_column(0, len(columns) - 1, 25, wrap)
            for column, (field_key, label) in enumerate(columns):
                sheet.write_string(0, column, label, header)
            for index, row in enumerate(rows, 1):
                if index >= 1048576:
                    raise UserError(_('Vượt giới hạn dòng Excel; chia bộ lọc thành nhiều lần xuất.'))
                for column, (key, field_label) in enumerate(columns):
                    value = row.get(key)
                    if type(value) in (int, float):
                        sheet.write_number(index, column, value)
                    elif key == '_draft':
                        sheet.write_string(index, column, 'NHÁP' if value else 'Bản lưu')
                    else:
                        cell = safe_cell(value)
                        if len(cell) > 32767:
                            raise UserError(_('Nội dung ô vượt giới hạn Excel; dùng Word/PDF để giữ đủ nội dung.'))
                        sheet.write_string(index, column, cell)
            sheet.autofilter(0, 0, len(rows), len(columns) - 1)
        book.close()
        return output.getvalue()


class ReportDocument(models.Model):
    _inherit = 'tp.report.document'

    def _export_action(self, format):
        self.check_access('read')
        return {'type': 'ir.actions.act_url', 'target': 'download',
                'url': '/tp_reporting/export?' + urlencode({'format': format, 'ids': ','.join(map(str, self.ids))})}

    def action_export_xlsx(self):
        return self._export_action('xlsx')

    def action_export_docx(self):
        return self._export_action('docx')

    def action_export_pdf(self):
        return self._export_action('pdf')


class ReportSnapshot(models.Model):
    _inherit = 'tp.report.snapshot'

    def _export_snapshot_action(self, format):
        self.ensure_one()
        self.check_access('read')
        self.document_id.check_access('read')
        return {'type': 'ir.actions.act_url', 'target': 'download', 'url': '/tp_reporting/export?' + urlencode({
            'format': format, 'ids': self.document_id.id, 'snapshot_id': self.id,
        })}

    def action_export_xlsx(self):
        return self._export_snapshot_action('xlsx')

    def action_export_docx(self):
        return self._export_snapshot_action('docx')

    def action_export_pdf(self):
        return self._export_snapshot_action('pdf')
