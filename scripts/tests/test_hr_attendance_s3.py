"""Execute the actual guard methods with in-memory collaborators; never opens an Odoo DB.

This complements, and does not replace, the ORM/HTTP regression suite in the addon.
"""
import ast
import math
import unittest
from datetime import date, time
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / 'custom_addons/tp_hr_attendance/models'


class Denied(Exception):
    pass


def method(file, cls, name, **symbols):
    tree = ast.parse((MODELS / file).read_text(encoding='utf-8-sig'))
    nodes = tree.body if cls is None else next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == cls).body
    node = next(node for node in nodes if isinstance(node, ast.FunctionDef) and node.name == name)
    node.decorator_list = []
    namespace = {'AccessError': Denied, 'UserError': Denied, 'ValidationError': Denied, 'math': math, **symbols}
    exec(compile(ast.Module(body=[node], type_ignores=[]), file, 'exec'), namespace)
    return namespace[name]


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.env = NS(user=1, _=lambda text, **kwargs: text)
        self.record = NS(env=self.env, ensure_one=lambda: None, check_access=Mock(),
                         _tp_lock_rows=Mock(), _tp_check_reviewer=Mock(), state='approved')

    def test_clock_boundaries(self):
        clock = method('attendance_correction.py', None, 'float_clock', time=time)
        self.assertEqual(clock(0), time(0))
        self.assertEqual(clock(23 + 59 / 60), time(23, 59))
        self.assertIsNone(clock(-1))
        self.assertIsNone(clock(24))

    def test_approval_retry_stops_after_lock_before_writes(self):
        approve = method('attendance_correction.py', 'AttendanceCorrection', 'action_approve')
        with self.assertRaises(Denied):
            approve(self.record)
        self.record.check_access.assert_called_once_with('read')
        self.record._tp_lock_rows.assert_called_once()
        self.record._tp_check_reviewer.assert_not_called()

    def test_unreadable_request_stops_before_lock(self):
        self.record.check_access.side_effect = Denied()
        approve = method('attendance_correction.py', 'AttendanceCorrection', 'action_approve')
        with self.assertRaises(Denied):
            approve(self.record)
        self.record._tp_lock_rows.assert_not_called()

    def test_no_self_approval_even_with_assignment(self):
        self.record.sudo = lambda: NS(employee_id=NS(user_id=1))
        checker = method('attendance_correction.py', 'AttendanceCorrection', '_tp_check_reviewer')
        with self.assertRaises(Denied):
            checker(self.record)

    def test_review_capability_is_checked_for_foreign_owner(self):
        require = Mock(side_effect=Denied())
        self.record.sudo = lambda: NS(employee_id=NS(user_id=2))
        self.record.company_id, self.record.department_id = 11, 22
        checker = method('attendance_correction.py', 'AttendanceCorrection', '_tp_check_reviewer', require=require)
        with self.assertRaises(Denied):
            checker(self.record)
        require.assert_called_once_with(self.env, 'review', 11, 22)

    def test_return_requires_reason(self):
        self.record.state = 'submitted'
        return_request = method('attendance_correction.py', 'AttendanceCorrection', 'action_return')
        with self.assertRaises(Denied):
            return_request(self.record, '  ')
        self.record._tp_check_reviewer.assert_called_once()

    def test_lock_refuses_pending_requests(self):
        self.record._tp_take_lock = Mock()
        self.record.state, self.record.pending_count = 'open', 1
        lock = method('attendance_config.py', 'AttendancePeriod', '_tp_lock')
        with self.assertRaises(Denied):
            lock(self.record)
        self.record._tp_take_lock.assert_called_once()

    def test_lock_requires_note_for_issues(self):
        self.record._tp_take_lock = Mock()
        self.record.state, self.record.pending_count = 'open', 0
        self.record.missing_count, self.record.review_count = 2, 1
        lock = method('attendance_config.py', 'AttendancePeriod', '_tp_lock')
        with self.assertRaises(Denied):
            lock(self.record, '  ')

    def test_unlock_requires_reason(self):
        self.record._tp_take_lock = Mock()
        self.record.state = 'locked'
        unlock = method('attendance_config.py', 'AttendancePeriod', '_tp_unlock')
        with self.assertRaises(Denied):
            unlock(self.record, '  ')

    def test_own_company_cannot_be_forged(self):
        self.env.company, self.env.companies = 1, [1]
        own = method('attendance_correction.py', 'AttendanceCorrection', '_tp_own_employee')
        with self.assertRaises(Denied):
            own(self.record, 2)

    def test_cross_company_capability_denied_before_assignment_query(self):
        self.env.companies = [1]
        can = method('attendance_common.py', None, 'can')
        self.assertFalse(can(self.env, 'review', 2))

    def test_locked_period_mutex_order_matches_approval(self):
        execute = Mock()
        self.env.cr = NS(execute=execute)
        self.record.company_id, self.record.id = NS(id=7), 8
        self.record.invalidate_recordset = Mock()
        lock = method('attendance_config.py', 'AttendancePeriod', '_tp_take_lock', require=Mock(), ADVISORY_KEY=123)
        lock(self.record)
        sql = [args.args[0] for args in execute.call_args_list]
        self.assertIn('pg_advisory_xact_lock', sql[0])
        self.assertIn('FOR UPDATE', sql[1])

    def test_attachment_public_and_reparent_guards(self):
        write = method('attendance_correction.py', 'AttendanceEvidence', 'write')
        self.record.sudo = lambda: NS(filtered=lambda fn: [NS(res_model='tp.hr.attendance.correction')])
        for values in ({'public': True}, {'access_token': 'forged'}, {'res_id': 99}, {'res_model': 'res.partner'}):
            with self.subTest(values=values), self.assertRaises(Denied):
                write(self.record, values)

    def test_validation_rejects_reversed_and_future_times(self):
        clock = method('attendance_correction.py', None, 'float_clock', time=time)
        validate = method('attendance_correction.py', 'AttendanceCorrection', '_tp_validate',
                          float_clock=clock, local_today=lambda tz: date(2026, 11, 9), DEFAULT_TZ='Asia/Ho_Chi_Minh')
        records = [NS(requested_in=17, requested_out=8, work_date=date(2026, 11, 9))]

        class Rows(list):
            env = self.env
        with self.assertRaises(Denied):
            validate(Rows(records))
        records[0].requested_in, records[0].requested_out, records[0].work_date = 8, 17, date(2026, 11, 10)
        with self.assertRaises(Denied):
            validate(Rows(records))


if __name__ == '__main__':
    unittest.main()
