import json
from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import BinaryBytes

from odoo.addons.tp_hr_workspace.models.department_transfer import _TRANSFER
from odoo.addons.tp_organization.models.hr_employee import _ROSTER_WRITE


@tagged('post_install', '-at_install')
class TestHrEmploymentContract(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({'name': 'Synthetic EMP014'})
        cls.other = cls.env['res.company'].create({'name': 'Synthetic EMP014 Other'})
        cls.env.ref('base.user_admin').write({'company_ids': [Command.link(cls.company.id), Command.link(cls.other.id)]})
        cls.hr = cls.env['res.users'].create({'name': 'Synthetic EMP014 HR', 'login': 'emp014.test.hr',
            'company_id': cls.company.id, 'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref('hr.group_hr_user').id])]})
        cls.staff = cls.env['res.users'].create({'name': 'Synthetic EMP014 KD', 'login': 'emp014.test.kd',
            'company_id': cls.company.id, 'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref('tp_kd_workspace.group_scoped_staff').id])]})
        cls.employee = cls.env['hr.employee'].with_company(cls.company).create({
            'name': '=SYNTHETIC EMP014()', 'company_id': cls.company.id, 'date_version': '2026-01-01'})

    def scoped(self, record, actor=None):
        return record.with_user(actor or self.hr).with_context(allowed_company_ids=self.company.ids)

    def document(self, **vals):
        return self.scoped(self.env['tp.hr.contract.document']).create({
            'name': 'Synthetic contract evidence', 'employee_id': self.employee.id, 'kind': 'labor', **vals})

    def test_kinds_unknown_and_native_version_source(self):
        employee = self.scoped(self.employee)
        self.assertFalse(employee.tp_employment_kind)
        for kind in ('short_term', 'long_term', 'outsourced', False):
            employee.tp_employment_kind = kind
            self.assertEqual(employee.version_id.tp_employment_kind, kind)
        employee.tp_employment_kind = 'short_term'
        future = employee.create_version({'date_version': '2099-01-01', 'tp_employment_kind': 'long_term'})
        self.assertEqual(employee.tp_employment_kind, 'short_term')
        self.assertEqual(employee.with_context(version_id=future.id).tp_employment_kind, 'long_term')
        self.assertEqual(employee.current_version_id.tp_employment_kind, 'short_term')
        with self.assertRaises(AccessError):
            self.scoped(self.employee, self.staff).read(['tp_employment_kind'])

    def test_document_is_shared_across_versions_and_view_is_readonly(self):
        employee = self.scoped(self.employee)
        employee.write({'contract_date_start': '2026-01-01', 'contract_date_end': '2099-12-31'})
        doc = self.document()
        employee.tp_contract_document_id = doc
        future = employee.create_version({'date_version': '2099-01-01'})
        self.assertEqual(future.tp_contract_document_id, doc)
        self.assertEqual(len(doc.version_ids), 2)
        count = len(employee.version_ids)
        action = future.action_open_version()
        self.assertEqual(action['context']['version_id'], future.id)
        self.assertEqual(len(employee.version_ids), count)
        self.assertEqual(self.scoped(self.env['tp.hr.contract.document']).search_count([('employee_id', '=', employee.id)]), 1)
        past = employee.create_version({'date_version': '2025-01-01', 'tp_employment_kind': 'short_term'})
        self.assertFalse(past.tp_contract_document_id)
        self.assertFalse(past.contract_date_start)
        self.assertEqual(employee.tp_contract_document_id, doc)
        self.assertEqual(employee.tp_employment_kind, False)

    def test_native_and_service_dates_are_validated(self):
        employee = self.scoped(self.employee)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            employee.write({'contract_date_start': '2026-02-01', 'contract_date_end': '2026-01-01'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.document(kind='outsourced', service_start='2026-02-01', service_end='2026-01-01')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.document(service_start='2026-01-01')
        doc = self.document(kind='outsourced', service_start='2026-01-01', service_end='2026-03-01')
        employee.write({'tp_employment_kind': 'outsourced', 'tp_contract_document_id': doc.id})
        self.assertFalse(employee.contract_date_start)
        self.assertFalse(employee.contract_date_end)
        self.assertFalse(doc.signed_date)

    def test_document_rpc_export_file_and_company_guards(self):
        doc = self.document(file=BinaryBytes(b'SYNTHETIC PRIVATE CONTRACT'), filename='synthetic.txt')
        self.assertEqual(bytes(doc.file), b'SYNTHETIC PRIVATE CONTRACT')
        self.env.flush_all()
        attachment = self.env['ir.attachment'].search([('res_model', '=', doc._name), ('res_id', '=', doc.id), ('res_field', '=', 'file')])
        self.assertTrue(attachment)
        for call in (lambda: self.scoped(doc, self.staff).read(['name', 'file']),
                     lambda: self.scoped(doc, self.staff).export_data(['name']),
                     lambda: self.scoped(attachment, self.staff).read(['raw']),
                     lambda: self.scoped(self.employee, self.staff).action_tp_contract_documents(),
                     lambda: self.scoped(doc, self.staff).write({'note': 'Forbidden'}),
                     lambda: self.scoped(attachment).write({'public': True}),
                     lambda: self.scoped(attachment).generate_access_token(),
                     lambda: self.scoped(self.employee).read(['wage'])):
            with self.assertRaises(AccessError), self.cr.savepoint():
                call()
        other_employee = self.env['hr.employee'].with_company(self.other).create({'name': 'Synthetic outside', 'company_id': self.other.id})
        other_doc = self.env['tp.hr.contract.document'].create({'name': 'Outside secret', 'employee_id': other_employee.id, 'kind': 'labor'})
        with self.assertRaises(AccessError):
            self.scoped(other_doc).read(['name'])
        with self.assertRaises((AccessError, ValidationError)), self.cr.savepoint():
            self.scoped(self.employee).tp_contract_document_id = other_doc
        with self.assertRaises(ValidationError):
            doc.write({'employee_id': other_employee.id})

    def test_contract_evidence_blocks_employee_deletion(self):
        self.document()
        plan = self.employee._tp_delete_plan()
        self.assertTrue(plan['employees'][self.employee.id]['block'])
        self.assertIn('Hồ sơ hợp đồng', str(plan['employees'][self.employee.id]['block']))

    def test_add_document_action_defaults_and_atomic_version_link(self):
        employee = self.scoped(self.employee)
        action = employee.action_tp_add_contract_document()
        model = self.scoped(self.env['tp.hr.contract.document']).with_context(**action['context'])
        defaults = model.default_get(['employee_id', 'kind', 'version_ids'])
        self.assertEqual(defaults['employee_id'], employee.id)
        self.assertNotIn('version_ids', defaults)
        doc = model.create({'employee_id': employee.id, 'kind': 'labor', 'name': 'Synthetic dialog save'})
        self.assertEqual(employee.version_id.tp_contract_document_id, doc)
        other = self.env['hr.employee'].with_company(self.company).create({'name': 'Synthetic wrong version'})
        before = model.search_count([])
        with self.assertRaises(ValidationError), self.cr.savepoint():
            model.with_context(tp_contract_version_id=other.version_id.id).create({
                'employee_id': employee.id, 'kind': 'labor', 'name': 'Synthetic forged link'})
        self.assertEqual(model.search_count([]), before)
        self.assertEqual(employee.version_id.tp_contract_document_id, doc)

    def test_employee_write_rules_apply_to_version_and_document_defaults(self):
        doc = self.document()
        self.env['ir.access'].create({'name': 'Synthetic EMP014 deny employee edits',
            'model_id': self.env['ir.model']._get_id('hr.employee'), 'operation': 'u', 'domain': "[('id', '=', -1)]"})
        for call in (
            lambda: self.scoped(self.employee.version_id).write({'tp_employment_kind': 'long_term'}),
            lambda: self.scoped(self.env['hr.version']).with_context(default_employee_id=self.employee.id).create({
                'date_version': '2098-01-01', 'tp_employment_kind': 'long_term'}),
            lambda: self.scoped(doc).write({'note': 'Forbidden'}),
            lambda: self.scoped(self.env['tp.hr.contract.document']).with_context(default_employee_id=self.employee.id).create({'name': 'Forbidden', 'kind': 'labor'}),
        ):
            with self.assertRaises(AccessError), self.cr.savepoint():
                call()

    def test_missing_domain_overview_and_xlsx_are_consistent(self):
        employee = self.scoped(self.employee)
        department = self.env['hr.department'].create({'name': 'Synthetic unit', 'company_id': self.company.id})
        # Source title counts as job information even without a canonical job.
        self.employee.with_context(_tp_roster_write=_ROSTER_WRITE, _tp_transfer=_TRANSFER).write({'department_id': department.id, 'tp_source_title': 'Synthetic imported role'})
        self.assertFalse(employee.tp_missing_basic)
        report = self.scoped(self.env['tp.hr.workspace'])
        self.assertEqual(report.get_overview()['missing_basic'], 0)
        self.assertEqual(report.get_overview({'missing_basic': True})['total'], 0)
        self.employee.with_context(_tp_roster_write=_ROSTER_WRITE).write({'tp_source_title': False})
        self.assertEqual(employee.tp_missing_basic, 'Thiếu thông tin chức vụ')
        self.assertEqual(report.get_overview()['missing_basic'], 1)
        employee.tp_employment_kind = 'short_term'
        self.assertEqual(report.get_overview({'employment_kind': 'short_term'})['total'], 1)
        self.assertEqual(report.get_overview({'employment_kind': 'unknown'})['total'], 0)
        employee.tp_employment_kind = False
        book = load_workbook(BytesIO(report._build_xlsx({'employment_kind': 'unknown', 'missing_basic': True})))
        sheet = book['Danh sách nhân viên']
        self.assertEqual(sheet['B6'].data_type, 's')
        headers = [c.value for c in sheet[5]]
        self.assertEqual(sheet.cell(6, headers.index('Loại hình lao động') + 1).value, 'Chưa khai báo')
        self.assertEqual(sheet.cell(6, headers.index('Cần bổ sung') + 1).value, employee.tp_missing_basic)
        self.assertTrue(sheet.auto_filter.ref)
        self.assertNotIn('wage', str(list(sheet.values)))
        book.close()

    def test_legacy_identity_summary_preserves_original_and_user_notes(self):
        employee = self.employee
        evidence = {'employee': employee.id, 'code': employee.tp_employee_code, 'resource': employee.resource_id.id,
                    'user': 1, 'partner': 1, 'work_contact': 1, 'name': employee.name, 'user_name': 'Synthetic',
                    'employee_image': 'f' * 64, 'user_image': 'e' * 64}
        message = employee.message_post(body='Đối chiếu danh tính theo ID: ' + json.dumps(evidence) + '. Lý do: Synthetic reason')
        original = message.body
        self.assertIn('Synthetic reason', message._tp_hr_identity_summary())
        self.assertNotIn('employee_image', message._tp_hr_identity_summary())
        self.assertEqual(message.body, original)
        note = employee.message_post(body='Đối chiếu danh tính theo ID: user note, not JSON')
        self.assertEqual(note._tp_hr_identity_summary(), note.body)
        self.assertEqual(message.create_date.date(), date.today())
        tracking = employee.message_post(body='<b>As of</b><div>None → <b>Được mời</b> <i>(User Status)</i></div>',
                                         body_is_html=True, message_type='tracking')
        display = tracking._tp_hr_display_body()
        self.assertIn('Có hiệu lực từ', display)
        self.assertIn('Chưa thiết lập', display)
        self.assertIn('Được mời', display)
        self.assertNotIn('User Status', display)
        self.assertIn('None', tracking.body)
