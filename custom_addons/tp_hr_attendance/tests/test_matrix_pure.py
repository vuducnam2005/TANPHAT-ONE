"""Pure (DB-free) unit tests for MATRIX-003 Excel parser v2 and A/B comparison classification."""
from datetime import date, timedelta
from io import BytesIO

from openpyxl import Workbook

from odoo.tests.common import BaseCase

from odoo.addons.tp_hr_attendance.models.attendance_compare import (
    cell_norm_signature,
    classify_day_comparison,
    classify_late_comparison,
)
from odoo.addons.tp_hr_attendance.models.attendance_parser import (
    PARSER_VERSION,
    AttendanceFormatError,
    parse_attendance,
)


def _build_matrix_xlsx(sheets):
    """Build synthetic machine-attendance .xlsx bytes covering headers, unit bands, cells, late & absent."""
    wb = Workbook()
    default_ws = wb.active
    for idx, spec in enumerate(sheets):
        ws = default_ws if idx == 0 else wb.create_sheet()
        ws.title = spec.get('title') or f'Sheet {idx + 1}'
        ws['A1'] = 'BẢNG CHẤM CÔNG'
        ws['A3'] = f"Từ ngày {spec['start'].strftime('%d/%m/%Y')} đến ngày {spec['end'].strftime('%d/%m/%Y')}"

        day_start_col = 7
        ws.cell(4, 1, 'STT')
        ws.cell(4, 2, 'Mã nhân viên')
        ws.cell(4, 3, 'Tên nhân viên')
        ws.cell(4, 4, 'ID')
        ws.cell(4, 5, 'Chức vụ')
        ws.cell(4, 6, 'Vào/Ra')

        days_count = (spec['end'] - spec['start']).days + 1
        weekdays = ('T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN')
        for offset in range(days_count):
            d = spec['start'] + timedelta(days=offset)
            col = day_start_col + offset
            ws.cell(4, col, d.day)
            ws.cell(5, col, weekdays[d.weekday()])

        late_col = day_start_col + days_count
        if spec.get('with_late', True):
            ws.cell(4, late_col, 'Đi muộn')
            ws.cell(5, late_col, 'Lần')
            ws.cell(5, late_col + 1, 'Phút')
        if spec.get('with_absent'):
            abs_col = late_col + (2 if spec.get('with_late', True) else 0)
            ws.cell(4, abs_col, 'Vắng mặt')

        row = 6
        for entry in spec['rows']:
            if entry.get('group'):
                ws.cell(row, 1, entry['group'])
                row += 1
                continue
            ws.cell(row, 1, entry['stt'])
            ws.cell(row, 2, entry['code'])
            ws.cell(row, 3, entry['name'])
            ws.cell(row, 4, entry.get('machine_id', entry['code']))
            ws.cell(row, 5, entry.get('job_title', ''))
            ws.cell(row, 6, 'Vào')
            ws.cell(row + 1, 6, 'Ra')
            for offset, pair in enumerate(entry.get('times', [])):
                col = day_start_col + offset
                if isinstance(pair, tuple):
                    if pair[0] is not None:
                        ws.cell(row, col, pair[0])
                    if pair[1] is not None:
                        ws.cell(row + 1, col, pair[1])
                elif pair is not None:
                    ws.cell(row, col, pair)
            if entry.get('merge_col_span'):
                for c_idx, val in entry['merge_col_span']:
                    ws.cell(row, c_idx, val)
                    ws.merge_cells(start_row=row, start_column=c_idx, end_row=row + 1, end_column=c_idx)
            if spec.get('with_late', True) and 'late' in entry:
                ws.cell(row, late_col, entry['late'][0])
                ws.cell(row, late_col + 1, entry['late'][1])
            if spec.get('with_absent') and 'absent' in entry:
                abs_col = late_col + (2 if spec.get('with_late', True) else 0)
                ws.cell(row, abs_col, entry['absent'])
            row += 2

        if spec.get('formula_cell'):
            r_idx, c_idx, expr = spec['formula_cell']
            ws.cell(r_idx, c_idx, expr)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestMatrixPureParser(BaseCase):
    def test_parser_v2_matrix_snapshot_and_codes(self):
        raw = _build_matrix_xlsx([
            {
                'title': 'Tuần 1',
                'start': date(2026, 10, 28),
                'end': date(2026, 11, 3),  # Month boundary crossing
                'with_absent': True,
                'rows': [
                    {'group': 'Khối Văn phòng'},
                    {
                        'stt': 1, 'code': 'TP001', 'machine_id': 1, 'name': 'Nguyễn Văn An',
                        'times': [('08:25', '17:10'), ('08:35', None), (None, '17:00'), ('CT', None), ('08:30 12:00', '13:00 17:30'), ('18:00', '08:00'), (None, None)],
                        'late': (1, 5),
                        'absent': 1,
                    },
                    {
                        'stt': 2, 'code': 'TP002', 'machine_id': 2, 'name': 'Trần Thị Trống',
                        'times': [(None, None)] * 7,
                        'late': (0, 0),
                        'absent': 7,
                    },
                ],
            },
            {
                'title': 'Tuần 2',
                'start': date(2026, 12, 29),
                'end': date(2027, 1, 4),  # Year boundary crossing
                'with_absent': False,
                'rows': [
                    {'stt': 1, 'code': 'TP001', 'machine_id': 1, 'name': 'Nguyễn Văn An', 'times': [('08:30', '17:00')] + [(None, None)] * 6, 'late': (0, 12)},
                ],
            },
        ])
        sheets = parse_attendance(raw)
        self.assertEqual(len(sheets), 2)

        s1 = sheets[0]
        self.assertEqual(s1.get('parser_version', PARSER_VERSION), PARSER_VERSION)
        self.assertEqual([c['date'] for c in s1['day_columns']], [
            date(2026, 10, 28), date(2026, 10, 29), date(2026, 10, 30), date(2026, 10, 31),
            date(2026, 11, 1), date(2026, 11, 2), date(2026, 11, 3),
        ])
        self.assertEqual(len(s1['people']), 2)  # Includes all-blank employee
        p1, p2 = s1['people']
        self.assertEqual(p1['raw_source_code'], 'TP001')
        self.assertEqual(p1['raw_machine_code'], '1')
        self.assertEqual(p1['machine_code'], '1')
        self.assertEqual(p1['group'], 'Khối Văn phòng')
        self.assertEqual(p1['absent_raw'], '1')
        self.assertEqual([c['kind'] for c in p1['cells']], [
            'pair', 'missing_out', 'missing_in', 'code', 'multi', 'reversed', 'empty',
        ])
        self.assertEqual(p2['name'], 'Trần Thị Trống')
        self.assertTrue(all(c['kind'] == 'empty' for c in p2['cells']))

        # Year crossing + inconsistent late (0 times, 12 minutes)
        s2 = sheets[1]
        self.assertEqual([c['date'] for c in s2['day_columns']], [
            date(2026, 12, 29), date(2026, 12, 30), date(2026, 12, 31),
            date(2027, 1, 1), date(2027, 1, 2), date(2027, 1, 3), date(2027, 1, 4),
        ])
        self.assertEqual(s2['people'][0]['late_state'], 'inconsistent')

    def test_parser_v2_long_periods_14_21_31_days_and_merged_symbol(self):
        for span in (14, 21, 31):
            start = date(2026, 3, 1)
            end = start + timedelta(days=span - 1)
            times = [('08:30', '17:00') if i % 2 == 0 else (None, None) for i in range(span)]
            raw = _build_matrix_xlsx([{
                'title': f'Ky {span}',
                'start': start,
                'end': end,
                'rows': [{'stt': 1, 'code': 'TP009', 'name': 'Lê Kiểm Thử', 'times': times, 'merge_col_span': [(8, 'NP')], 'late': (0, 0)}],
            }])
            sheets = parse_attendance(raw)
            sh = sheets[0]
            self.assertEqual(len(sh['day_columns']), span)
            self.assertEqual(sh['people'][0]['cells'][1]['kind'], 'merged')
            self.assertEqual(sh['people'][0]['cells'][1]['raw_in'], 'NP')

    def test_parser_v2_rejects_formula_without_cached_or_shifted_headers(self):
        raw_formula = _build_matrix_xlsx([{
            'title': 'Công thức',
            'start': date(2026, 11, 9),
            'end': date(2026, 11, 10),
            'rows': [{'stt': 1, 'code': 'TP001', 'name': 'Nguyễn Văn An', 'times': [('08:30', '17:00'), (None, None)]}],
            'formula_cell': (6, 7, '=SUM(A1:A2)'),
        }])
        sheets = parse_attendance(raw_formula)
        c0 = sheets[0]['people'][0]['cells'][0]
        self.assertEqual(c0['kind'], 'invalid')
        self.assertEqual(c0['norm_in'], '')

        # Also test shifted / missing headers rejection
        bad_wb = Workbook()
        bad_ws = bad_wb.active
        bad_ws['A1'] = 'NOT A REPORT'
        bad_buf = BytesIO()
        bad_wb.save(bad_buf)
        with self.assertRaises(AttendanceFormatError):
            parse_attendance(bad_buf.getvalue())

    def test_compare_pure_classification_matrix(self):
        p_a = {'kind': 'pair', 'norm_in': '08:30:00', 'norm_out': '17:05:00'}
        p_b_same = {'kind': 'pair', 'norm_in': '08:30:00', 'norm_out': '17:05:00'}
        p_b_diff = {'kind': 'pair', 'norm_in': '08:31:00', 'norm_out': '17:05:00'}
        miss_out = {'kind': 'missing_out', 'norm_in': '08:30:00', 'norm_out': ''}
        miss_in = {'kind': 'missing_in', 'norm_in': '', 'norm_out': '17:05:00'}
        empty_can = {'exists': False, 'kind': 'none', 'norm_in': '', 'norm_out': ''}

        self.assertEqual(cell_norm_signature(p_a), cell_norm_signature(p_b_same))
        self.assertEqual(classify_day_comparison('mapped', 'in_period', p_a, 'in_period', p_b_same, empty_can)[0], 'same')
        self.assertEqual(classify_day_comparison('mapped', 'in_period', p_a, 'in_period', p_b_diff, empty_can)[0], 'diff')

        # Never splice IN from A with OUT from B
        self.assertEqual(classify_day_comparison('mapped', 'in_period', miss_out, 'in_period', miss_in, empty_can)[0], 'diff')

        # Identical A & B differing from existing canonical data must NOT mark 'same'
        can_other = {'exists': True, 'kind': 'pair', 'norm_in': '08:30:00', 'norm_out': '18:00:00'}
        self.assertEqual(classify_day_comparison('mapped', 'in_period', p_a, 'in_period', p_b_same, can_other)[0], 'diff')

        # Blank vs Out-of-scope vs Not-in-file -> distinct explanations, classified 'only_a'
        g1, r1 = classify_day_comparison('mapped', 'in_period', p_a, 'out_of_scope', None, empty_can)
        g2, r2 = classify_day_comparison('mapped', 'in_period', p_a, 'blank_in_period', None, empty_can)
        g3, r3 = classify_day_comparison('mapped', 'in_period', p_a, 'not_in_file', None, empty_can)
        self.assertEqual((g1, g2, g3), ('only_a', 'only_a', 'only_a'))
        self.assertIn('ngoài phạm vi', r1.lower())
        self.assertIn('ô trống', r2.lower())
        self.assertIn('không có trong file', r3.lower())

        # Unmapped / name conflict -> unready
        self.assertEqual(classify_day_comparison('unmapped', 'in_period', p_a, 'in_period', p_b_same, empty_can)[0], 'unready')
        self.assertEqual(classify_day_comparison('name_conflict', 'in_period', p_a, 'in_period', p_b_same, empty_can)[0], 'unready')

        # Late totals comparison
        l_same = {'source_state': 'ok', 'count': 2, 'minutes': 15}
        l_diff = {'source_state': 'ok', 'count': 3, 'minutes': 25}
        l_bad = {'source_state': 'inconsistent', 'count': 0, 'minutes': 15}
        self.assertEqual(classify_late_comparison('mapped', l_same, l_same, {'exists': False})[0], 'same')
        self.assertEqual(classify_late_comparison('mapped', l_same, l_diff, {'exists': False})[0], 'diff')
        self.assertEqual(classify_late_comparison('mapped', l_same, None, {'exists': False})[0], 'only_a')
        self.assertEqual(classify_late_comparison('mapped', l_same, l_bad, {'exists': False})[0], 'unready')
