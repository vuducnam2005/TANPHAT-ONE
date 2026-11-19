from io import BytesIO

from openpyxl import load_workbook

from odoo import Command
from odoo.exceptions import AccessError, ValidationError

from .test_hr_workspace import BaseHrWorkspace


class TestEmployeeExport(BaseHrWorkspace):
    def test_saved_department_and_employee_order(self):
        second = self.env['hr.department'].create({'name': 'A new unit', 'company_id': self.company.id, 'tp_sequence': -10})
        extra = self.env['hr.employee'].with_company(self.company).create({
            'name': '=literal()', 'department_id': second.id, 'company_id': self.company.id,
            'mobile_phone': '0900123456',
        })
        first, following = self.employees[:2]
        first.tp_reorder_in_department(following.id, self.department.id, before_id=first.id)
        options = {'scope': 'all'}
        expected = [extra.id, following.id, first.id, self.employees[2].id]
        records = self.report()._employee_export_records(options)[0]
        self.assertEqual(records.ids, expected)
        before = records.read(['sequence', 'write_date'])
        workbook = load_workbook(BytesIO(self.report()._build_xlsx(options=options)))
        flat = workbook['Dữ liệu chi tiết']
        self.assertEqual([flat.cell(row, 3).value for row in range(7, 11)], records.mapped('name'))
        main_names = [row[2] for row in workbook['Danh sách nhân viên'].values if type(row[0]) is int]
        self.assertEqual(main_names, records.mapped('name'))
        headers = [cell.value for cell in flat[6]]
        phone_col = headers.index('Số điện thoại') + 1
        self.assertEqual(flat.cell(7, phone_col).value, '0900123456')
        self.assertEqual(flat.cell(7, phone_col).data_type, 's')
        self.assertEqual(flat['C7'].data_type, 's')
        self.assertEqual(flat.auto_filter.ref.split(':')[0], 'A6')
        self.assertFalse(any(cell.data_type == 'f' for row in flat for cell in row))
        self.assertEqual(records.read(['sequence', 'write_date']), before)
        second.tp_sequence = self.department.tp_sequence + 100
        self.env.flush_all()
        second.invalidate_recordset(['tp_sequence'])
        reordered = self.report()._employee_export_records(options)[0]
        self.assertEqual(reordered.ids, expected[1:] + expected[:1])
        workbook = load_workbook(BytesIO(self.report()._build_xlsx(options=options)))
        names = [row[2] for row in workbook['Danh sách nhân viên'].values if type(row[0]) is int]
        self.assertEqual(names, reordered.mapped('name'))
        self.assertEqual([row[2] for row in list(workbook['Dữ liệu chi tiết'].values)[6:]], names)
        self.assertEqual(records.read(['sequence', 'write_date']), before)

    def test_applied_domain_selection_and_scope(self):
        report = self.report()
        options = {'domain': ['|', ('name', '=', self.employees[0].name), ('id', '=', self.employees[1].id)]}
        self.assertEqual(report.get_employee_export_summary(options)['count'], 2)
        selected = {**options, 'scope': 'selected', 'selected_ids': [self.employees[0].id, 9999999]}
        self.assertEqual(report.get_employee_export_summary(selected)['count'], 1)
        selected['selection_all'] = True
        self.assertEqual(report.get_employee_export_summary(selected)['count'], 2)
        self.assertEqual(report.get_employee_export_summary({'scope': 'all'})['count'], 3)
        self.assertEqual(report.get_employee_export_summary({'domain': [('company_id', '=', self.other.id)]})['count'], 0)
        for options in ({'scope': 'bad'}, {'domain': ['|']}, {'selected_ids': [True], 'scope': 'selected'},
                        {'domain': [('user_id.password', '!=', False)]}):
            with self.subTest(options=options), self.assertRaises(ValidationError):
                report.get_employee_export_summary(options)
        with self.assertRaises(AccessError):
            self.report(self.staff)._build_xlsx(options={'scope': 'all'})
        with self.assertRaises(AccessError):
            report.get_employee_export_summary({'domain': [('wage', '>', 0)]})

    def test_contracts_keep_employee_cardinality_and_dates(self):
        employee = self.employees[0]
        doc = self.env['tp.hr.contract.document'].create({
            'name': 'Synthetic paper', 'employee_id': employee.id, 'kind': 'outsourced',
            'service_start': '2026-01-01', 'service_end': '2026-12-31', 'number': '001',
        })
        self.env['tp.hr.contract.document'].create({
            'name': 'Second synthetic paper', 'employee_id': employee.id, 'kind': 'outsourced',
        })
        workbook = load_workbook(BytesIO(self.report()._build_xlsx(options={'scope': 'all'})))
        self.assertEqual(workbook['Dữ liệu chi tiết'].max_row, 9)
        sheet = workbook['Hợp đồng lao động']
        headers = [cell.value for cell in sheet[6]]
        start = sheet.cell(7, headers.index('Ngày bắt đầu thuê khoán') + 1)
        self.assertEqual(start.value.date(), doc.service_start)
        self.assertEqual(start.number_format, 'dd/mm/yyyy')
        self.assertEqual(sheet.cell(7, headers.index('Số hợp đồng') + 1).value, '001')
        self.assertEqual(sheet.max_row, 8)

    def test_directory_user_cannot_export_after_group_change(self):
        self.staff.write({'group_ids': [Command.set([self.env.ref('base.group_user').id])]})
        with self.assertRaises(AccessError):
            self.report(self.staff).get_employee_export_summary({'scope': 'all'})
