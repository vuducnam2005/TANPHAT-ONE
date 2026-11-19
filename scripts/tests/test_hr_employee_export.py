"""Workbook and export-boundary regression without connecting to any database."""
import ast
import io
import unittest
from datetime import date, datetime
from itertools import groupby
from math import ceil
from pathlib import Path
from types import SimpleNamespace

import xlsxwriter
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'custom_addons/tp_hr_workspace/models/hr_workspace.py'


class Rows(list):
    @property
    def ids(self):
        return [record.id for record in self]

    def sorted(self, key):
        return Rows(sorted(self, key=key))


class Department(str):
    __slots__ = ()

    @property
    def name(self):
        return str(self)


def exporter_class():
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    nodes = [node for node in tree.body if isinstance(node, ast.Assign | ast.FunctionDef)]
    methods = next(node for node in tree.body if isinstance(node, ast.ClassDef)).body
    methods = [method for method in methods if isinstance(method, ast.FunctionDef)]
    for method in methods:
        method.decorator_list = []
    nodes.append(ast.ClassDef(name='Exporter', bases=[], keywords=[], body=methods, decorator_list=[]))
    fields = SimpleNamespace(Datetime=SimpleNamespace(now=lambda: datetime(2026, 11, 19, 9), context_timestamp=lambda _self, value: value))
    namespace = {'io': io, 'xlsxwriter': xlsxwriter, 'date': date, 'datetime': datetime,
                 'groupby': groupby, 'ceil': ceil, 'fields': fields, 'AccessError': PermissionError, 'ValidationError': ValueError}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(SOURCE), 'exec'), namespace)
    return namespace['Exporter']


class EmployeeExportTests(unittest.TestCase):
    def setUp(self):
        self.report = exporter_class()()
        company = SimpleNamespace(name='Công ty minh họa')
        self.report.env = SimpleNamespace(
            context={}, user=SimpleNamespace(tz='Asia/Ho_Chi_Minh'),
            companies=SimpleNamespace(mapped=lambda _name: [company.name]),
            _=lambda message: message,
        )
        self.report.with_context = lambda **_kwargs: self.report
        self.report._write_export_contracts = lambda *_args: None
        self.fields = {name: SimpleNamespace(type=kind) for name, kind in (
            ('tp_employee_code', 'char'), ('name', 'char'), ('department_id', 'many2one'),
            ('job_id', 'many2one'), ('tp_employment_kind', 'selection'), ('mobile_phone', 'char'),
            ('work_email', 'char'), ('tp_user_login', 'char'), ('tp_account_status', 'selection'),
            ('active', 'boolean'), ('birthday', 'date'), ('children', 'integer'), ('additional_note', 'text'),
        )}
        self.rows = Rows([
            SimpleNamespace(id=7, department_id=Department('Phòng Kế hoạch Kinh doanh')),
            SimpleNamespace(id=3, department_id=Department('Phòng Kế hoạch Kinh doanh')),
            SimpleNamespace(id=2, department_id=Department('Phòng Thiết kế')),
        ])
        self.rows._fields = self.fields
        self.rows._has_field_access = lambda field, _operation: field is not self.fields['additional_note']
        self.report._employee_export_records = lambda _options: (self.rows, 'filtered', 'Tìm kiếm nâng cao đã áp dụng')
        self.report._export_cell_value = lambda employee, name: {
            'tp_employee_code': '000' + str(employee.id), 'name': '=LITERAL()' if employee.id == 7 else 'Nhân viên minh họa ' + str(employee.id),
            'department_id': employee.department_id, 'job_id': 'Kỹ sư', 'tp_employment_kind': 'Dài hạn',
            'mobile_phone': '0900123456', 'work_email': 'minhhoa@example.invalid', 'tp_user_login': 'minhhoa',
            'tp_account_status': {7: 'Mở', 3: 'Khóa', 2: 'Chưa có tài khoản'}[employee.id],
            'active': 'Đang quản lý', 'birthday': date(1990, 1, 2), 'children': 0,
        }[name]
        self.report._export_cell_value_original = exporter_class()._export_cell_value

    def workbook(self):
        return load_workbook(io.BytesIO(self.report._build_xlsx(options={})))

    def test_order_cardinality_literal_types_and_permissions(self):
        book = self.workbook()
        self.assertEqual(book.sheetnames, ['Danh sách nhân viên', 'Dữ liệu chi tiết'])
        main, detail = book.worksheets
        main_data = [row for row in main.values if type(row[0]) is int]
        detail_data = list(detail.values)[6:]
        self.assertEqual([row[1:3] for row in main_data], [row[1:3] for row in detail_data])
        self.assertEqual([row[1] for row in detail_data], ['0007', '0003', '0002'])
        self.assertEqual(detail['C7'].value, '=LITERAL()')
        self.assertEqual(detail['C7'].data_type, 's')
        self.assertEqual(detail['G7'].value, '0900123456')
        self.assertEqual(detail['G7'].data_type, 's')
        headers = list(detail.values)[5]
        self.assertNotIn('Ghi chú', headers)
        self.assertEqual(detail.cell(7, headers.index('Số con phụ thuộc') + 1).value, 0)
        birth = detail.cell(7, headers.index('Ngày sinh') + 1)
        self.assertEqual(birth.value.date(), date(1990, 1, 2))
        self.assertEqual(birth.number_format, 'dd/mm/yyyy')
        self.assertEqual(main.freeze_panes, 'D7')
        self.assertEqual(detail.auto_filter.ref, 'A6:M9')
        self.assertTrue(all(merge.max_row < 6 for merge in detail.merged_cells.ranges))
        self.assertTrue(main.sheet_properties.pageSetUpPr.fitToPage)
        self.assertIn(main.page_setup.fitToWidth, (None, 1))  # OOXML defaults to one page.
        self.assertEqual(detail.page_setup.scale, 85)

    def test_no_employee_pagination_limit_in_workbook(self):
        self.rows.extend(SimpleNamespace(id=7, department_id=Department('Phòng Thiết kế')) for _ in range(120))
        book = self.workbook()
        self.assertEqual(book['Dữ liệu chi tiết'].max_row - 6, 123)
        self.assertEqual(sum(type(row[0]) is int for row in book.worksheets[0].values), 123)

    def test_empty_scope_is_still_a_valid_filterable_workbook(self):
        self.rows.clear()
        book = self.workbook()
        self.assertEqual(book['Dữ liệu chi tiết'].auto_filter.ref, 'A6:M6')
        self.assertIn('Không có nhân viên', book.worksheets[0]['A7'].value)

    def test_export_denies_directory_user_before_query(self):
        report = exporter_class()()
        report.env = SimpleNamespace(user=SimpleNamespace(has_group=lambda _group: False), _=lambda message: message)
        with self.assertRaises(PermissionError):
            report._employee_export_records({'scope': 'all'})

    def test_saved_department_order_and_employee_reorder_with_id_ties(self):
        key = exporter_class()._employee_export_records.__globals__['employee_export_order_key']
        a = SimpleNamespace(id=20, tp_sequence=10)
        b = SimpleNamespace(id=10, tp_sequence=20)
        rows = [SimpleNamespace(id=1, sequence=20, department_id=a),
                SimpleNamespace(id=4, sequence=10, department_id=a),
                SimpleNamespace(id=3, sequence=10, department_id=a),
                SimpleNamespace(id=2, sequence=10, department_id=b)]
        self.assertEqual([e.id for e in sorted(rows, key=key)], [3, 4, 1, 2])
        rows[0].sequence = 5
        self.assertEqual([e.id for e in sorted(rows, key=key)], [1, 3, 4, 2])
        b.tp_sequence = 1
        self.assertEqual([e.id for e in sorted(rows, key=key)], [2, 1, 3, 4])


if __name__ == '__main__':
    unittest.main()
