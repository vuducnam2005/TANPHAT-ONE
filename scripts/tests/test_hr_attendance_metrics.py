"""Pure dashboard arithmetic tests without a database."""
import csv
import importlib.util
import io
import unittest
from pathlib import Path

path = Path(__file__).resolve().parents[2] / 'custom_addons/tp_hr_attendance/models/attendance_metrics.py'
spec = importlib.util.spec_from_file_location('attendance_metrics', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestMetrics(unittest.TestCase):
    def data(self, cells):
        rows = [{'id': 1, 'name': 'Synthetic', 'code': 'S1', 'department': 'Dept', 'cells': cells}]
        dates = [{'date': cell['date']} for cell in cells]
        return module.metrics(rows, dates, '2026-11-17')

    def test_future_is_excluded_from_every_total(self):
        result = self.data([{'date': '2026-11-17', 'state': 'ok', 'hours': 8, 'day_id': 1},
                            {'date': '2026-11-18', 'state': 'ok', 'hours': 9, 'day_id': 2}])
        self.assertEqual((result['total'], result['hours'], result['unconfirmed']), (1, 8, 1))
        self.assertEqual(len(result['daily']), 1)
        self.assertEqual(len(result['cells']), 1)

    def test_counts_partition_and_daily_totals_match(self):
        result = self.data([{'date': '2026-11-01', 'state': key} for key in module.STATES])
        self.assertEqual(result['total'], 5)
        self.assertEqual(sum(result['daily'][0]['counts'].values()), 5)
        self.assertEqual(sum(result['departments_chart'][0]['counts'].values()), 5)

    def test_unknown_units_are_null_but_confirmed_zero_is_zero(self):
        cell = {'date': '2026-11-01', 'state': 'ok', 'day_id': 1, 'units_state': 'unconfirmed'}
        self.assertIsNone(self.data([cell])['units'])
        cell.update(units_state='confirmed', units_value=0)
        self.assertEqual(self.data([cell])['units'], 0)

    def test_own_csv_whitelist_filters_and_formula_guard(self):
        row = {'date': '2026-11-09', 'state': 'ok', 'lock': 'open', 'label': 'Đủ dữ liệu',
               'day_id': 1, 'hours': 0, 'units': '0,00', 'in_time': '=1+1',
               'requests': [{'reason': 'PRIVATE'}], 'sessions': [{'source_label': 'Nhập từ báo cáo máy'}]}
        content = module.own_csv([row], 'ok', 'open')
        self.assertTrue(content.startswith('\ufeff'))
        records = list(csv.reader(io.StringIO(content.lstrip('\ufeff'))))
        self.assertEqual(len(records[1]), 8)
        self.assertEqual(records[1][1], "'=1+1")
        self.assertEqual(records[1][3], '0')
        self.assertNotIn('PRIVATE', content)
        self.assertEqual(len(list(csv.reader(io.StringIO(module.own_csv([row], 'missing'))))), 1)
        self.assertEqual(len(list(csv.reader(io.StringIO(module.own_csv([row], lock='locked'))))), 1)

    def test_empty(self):
        result = module.metrics([], [], '2026-11-17')
        self.assertEqual(result['total'], 0)
        self.assertIsNone(result['units'])


if __name__ == '__main__':
    unittest.main()
