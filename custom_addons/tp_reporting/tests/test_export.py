import base64
import io
import zipfile
from xml.etree import ElementTree as ET

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools.misc import limited_field_access_token

from odoo.addons.tp_reporting.models.export import make_docx, make_pdf, safe_cell, text


@tagged('post_install', '-at_install')
class TestReportingExport(TransactionCase):
    def test_text_missing_zero_and_injection(self):
        self.assertEqual(text(0), '0')
        self.assertEqual(text(None), 'Chưa xác nhận')
        self.assertEqual(safe_cell(' =HYPERLINK("bad")'), '\' =HYPERLINK("bad")')
        self.assertEqual(safe_cell('Báo cáo'), 'Báo cáo')

    def test_docx_is_unicode_ooxml_and_escapes_content(self):
        payload = {'name': 'Báo cáo <Thiết kế> & tiến độ', '_draft': True,
                   'lines': [{'name': 'Cầu đường', 'quantity': 0}], 'version': 2}
        with zipfile.ZipFile(io.BytesIO(make_docx([payload]))) as archive:
            document = archive.read('word/document.xml')
            root = ET.fromstring(document)
            content = ''.join(root.itertext())
            self.assertIn('Báo cáo <Thiết kế> & tiến độ', content)
            self.assertIn('NHÁP', content)
            self.assertIn('Thực hiện: 0', content)
            for filename in ('[Content_Types].xml', '_rels/.rels'):
                ET.fromstring(archive.read(filename))

    def test_xlsx_no_formula_and_no_truncation_at_ui_page(self):
        service = self.env['tp.reporting.export']
        payload = {'name': '=1+1', '_draft': True,
                   'lines': [{'name': f'Dòng {index}', 'quantity': index} for index in range(123)]}
        with zipfile.ZipFile(io.BytesIO(service._xlsx([payload]))) as archive:
            summary = archive.read('xl/worksheets/sheet1.xml').decode()
            lines = archive.read('xl/worksheets/sheet2.xml').decode()
            self.assertNotIn('<f>', summary)
            self.assertIn('r="124"', lines)
            self.assertIn('autoFilter', lines)

    def test_finance_sheet_only_for_authorized_payload(self):
        service = self.env['tp.reporting.export']
        general = {'name': 'Báo cáo'}
        with zipfile.ZipFile(io.BytesIO(service._xlsx([general]))) as archive:
            self.assertNotIn('xl/worksheets/sheet7.xml', archive.namelist())
        authorized = dict(general, _finance=[{'name': 'Nguồn', 'amount': 0, 'status': 'confirmed'}])
        with zipfile.ZipFile(io.BytesIO(service._xlsx([authorized]))) as archive:
            self.assertIn('xl/worksheets/sheet7.xml', archive.namelist())
            self.assertIn('<v>0</v>', archive.read('xl/worksheets/sheet7.xml').decode())

    def test_pdf_unicode_content_generates(self):
        content = make_pdf([{'name': 'Báo cáo tiếng Việt — Thiết kế', '_draft': True}])
        self.assertTrue(content.startswith(b'%PDF-'))

    def test_export_rejects_format_and_malformed_selection(self):
        with self.assertRaises(ValidationError):
            self.env['tp.reporting.export']._build('html')
        with self.assertRaises(ValidationError):
            list(self.env['tp.reporting.export']._documents([True], []))

    def test_limited_binary_token_does_not_bypass_current_report_rights(self):
        group = self.env.ref('tp_reporting.group_reporting_user')
        author, outside = self.env['res.users'].create([{
            'name': role, 'login': 'export-binary-' + role, 'company_id': self.env.company.id,
            'company_ids': [Command.set(self.env.company.ids)], 'group_ids': [Command.set(group.ids)],
        } for role in ('author', 'outside')])
        document = self.env['tp.report.document'].with_user(author).create({
            'name': 'Synthetic binary evidence', 'owner_id': author.id, 'company_id': self.env.company.id,
            'period_type': 'week', 'date_start': '2026-12-07', 'date_end': '2026-12-13',
        })
        attachment = self.env['ir.attachment'].with_user(author).create({
            'name': 'synthetic.txt', 'res_model': document._name, 'res_id': document.id,
            'datas': base64.b64encode(b'SYNTHETIC PRIVATE EVIDENCE'), 'public': False,
        })
        token = limited_field_access_token(attachment, 'raw', scope='binary')
        with self.assertRaises(AccessError):
            self.env['ir.binary'].with_user(outside)._find_record(res_id=attachment.id, access_token=token, field='raw')
        permitted = self.env['ir.binary'].with_user(author)._find_record(res_id=attachment.id, access_token=token, field='raw')
        self.assertEqual(permitted.id, attachment.id)

    def test_reporting_attachment_public_flag_rejected_even_with_token(self):
        group = self.env.ref('tp_reporting.group_reporting_user')
        author = self.env['res.users'].create({'name': 'public-evidence-author', 'login': 'export-public-author',
            'company_id': self.env.company.id, 'company_ids': [Command.set(self.env.company.ids)], 'group_ids': [Command.set(group.ids)]})
        document = self.env['tp.report.document'].with_user(author).create({'name': 'Synthetic report',
            'owner_id': author.id, 'company_id': self.env.company.id, 'period_type': 'week',
            'date_start': '2026-12-07', 'date_end': '2026-12-13'})
        values = {'name': 'public.txt', 'res_model': document._name, 'res_id': document.id,
                  'datas': base64.b64encode(b'SYNTHETIC'), 'public': True}
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env['ir.attachment'].with_user(author).create(values)
        attachment = self.env['ir.attachment'].with_user(author).create(dict(values, public=False))
        # A legacy misconfigured row must remain unreadable despite a valid signed token.
        attachment.flush_recordset(['public'])
        self.env.cr.execute('UPDATE ir_attachment SET public=true WHERE id=%s', [attachment.id])
        attachment.invalidate_recordset(['public'])
        token = limited_field_access_token(attachment, 'raw', scope='binary')
        with self.assertRaises(AccessError):
            self.env['ir.binary'].with_user(author)._find_record(res_id=attachment.id, access_token=token, field='raw')
