"""Safe source-level unit tests: no Odoo registry, actors or database writes."""
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

SOURCE = Path(__file__).resolve().parents[1] / 'models' / 'employee_order.py'
tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
namespace = {'AccessError': PermissionError, 'ValidationError': ValueError, 'SUPERUSER_ID': 1}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == 'compute_reordered_department_ids':
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), namespace)
    if isinstance(node, ast.ClassDef) and node.name == 'HrEmployeeOrder':
        for method in node.body:
            if isinstance(method, ast.FunctionDef) and method.name in {
                '_tp_parse_positive_id', '_tp_lock_employee_order', '_tp_can_reorder_employees', 'write',
                'tp_reorder_in_department',
            }:
                method.decorator_list = []
                exec(compile(ast.Module(body=[method], type_ignores=[]), str(SOURCE), 'exec'), namespace)
reorder = namespace['compute_reordered_department_ids']


class EmployeeOrderTests(unittest.TestCase):
    def test_full_department_not_page_is_reordered(self):
        self.assertEqual(reorder([1, 2, 3, 4, 5], 5, before_id=2), [1, 5, 2, 3, 4])
        self.assertEqual(reorder([1, 2, 3, 4, 5], 1, after_id=4), [2, 3, 4, 1, 5])
        self.assertEqual(reorder([1, 2, 3], 3, after_id=1, before_id=2), [1, 3, 2])

    def test_stale_and_cross_department_anchors_rejected(self):
        for args in ({}, {'before_id': 9}, {'after_id': 9}, {'before_id': 2},
                     {'after_id': 1, 'before_id': 4}, {'after_id': 4, 'before_id': 1}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                reorder([1, 2, 3, 4], 2, **args)
        with self.assertRaises(ValueError):
            reorder([1, 2], 99, before_id=1)

    def test_id_boundary(self):
        fake = SimpleNamespace(env=SimpleNamespace(_=lambda message, *args: message))
        parse = namespace['_tp_parse_positive_id']
        for invalid in (True, -1, 1.2, '1.0', '01', [], {}, 'bad'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse(fake, invalid, 'ID')
        self.assertEqual(parse(fake, ' 12 ', 'ID'), 12)
        self.assertIsNone(parse(fake, False, 'ID', allow_empty=True))

    def test_lock_has_mvcc_write_and_stable_company_order(self):
        calls = []
        fake = SimpleNamespace(env=SimpleNamespace(cr=SimpleNamespace(execute=lambda *args: calls.append(args))))
        namespace['ADVISORY_LOCK_NS_EMP_ORDER'] = 761101
        namespace['_tp_lock_employee_order'](fake, [3, 1, 3])
        self.assertEqual(calls, [
            ('SELECT pg_advisory_xact_lock(%s, %s)', (761101, 1)),
            ('UPDATE res_company SET id = id WHERE id = %s', (1,)),
            ('SELECT pg_advisory_xact_lock(%s, %s)', (761101, 3)),
            ('UPDATE res_company SET id = id WHERE id = %s', (3,)),
        ])

    def test_sequence_rpc_context_cannot_forge_internal_token(self):
        namespace['_TP_REORDER'] = object()
        for context in ({}, {'_tp_employee_reorder': True}, {'_tp_employee_reorder': 'internal'}):
            fake = SimpleNamespace(env=SimpleNamespace(context=context, _=lambda message: message))
            with self.subTest(context=context), self.assertRaises(PermissionError):
                namespace['write'](fake, {'sequence': 999})

    def test_capability_requires_internal_actor_and_write_acl(self):
        for groups, can_write, active, share, expected in [
            (set(), True, True, False, False),
            ({'hr.group_hr_user'}, False, True, False, False),
            ({'hr.group_hr_user'}, True, True, False, True),
            ({'base.group_system'}, True, True, False, True),
            ({'hr.group_hr_user'}, True, False, False, False),
            ({'hr.group_hr_user'}, True, True, True, False),
        ]:
            user = SimpleNamespace(active=active, share=share, has_group=lambda group: group in groups)

            class Env:
                su = False
                uid = 99

                def __getitem__(self, model):
                    return SimpleNamespace(has_access=lambda mode: can_write)
            env = Env()
            env.user = user
            self.assertEqual(namespace['_tp_can_reorder_employees'](SimpleNamespace(env=env)), expected)


class MockEmployeeSet:
    """Small ORM boundary fake; the action and placement algorithm are real source."""
    def __init__(self, state, ids=(), context=None, elevated=False):
        self.state = state
        self.ids = list(ids)
        self.context = context or {}
        self.elevated = elevated
        self.env = state.env

    def __bool__(self):
        return bool(self.ids)

    def __getattr__(self, name):
        row = self.state.rows[self.ids[0]]
        if name == 'company_id':
            return SimpleNamespace(id=row['company'])
        if name == 'current_version_id':
            return SimpleNamespace(department_id=SimpleNamespace(id=row['department']))
        return row[name]

    def sudo(self):
        return MockEmployeeSet(self.state, self.ids, self.context, elevated=True)

    def with_context(self, **context):
        return MockEmployeeSet(self.state, self.ids, {**self.context, **context}, self.elevated)

    def browse(self, employee_id):
        return MockEmployeeSet(self.state, [employee_id], self.context, self.elevated)

    def exists(self):
        return MockEmployeeSet(self.state, [eid for eid in self.ids if eid in self.state.rows],
                               self.context, self.elevated)

    def check_access(self, mode):
        self.state.checks.append((mode, tuple(self.ids)))
        if not self.elevated and any(eid in self.state.denied.get(mode, set()) for eid in self.ids):
            raise PermissionError(mode)

    def search(self, domain):
        company, dept, _active = [item[2] for item in domain]
        self.state.search_contexts.append(self.context)
        return MockEmployeeSet(self.state, [eid for eid, row in self.state.rows.items()
            if row['company'] == company and row['department'] == dept and row['active']
            and eid not in self.state.denied.get('read', set())], self.context)

    def write(self, values):
        self.check_access('write')
        if self.context.get('_tp_employee_reorder') is not namespace['_TP_REORDER']:
            msg = 'token'
            raise PermissionError(msg)
        self.state.writes.append((self.ids[0], dict(values)))
        self.state.rows[self.ids[0]].update(values)

    def _tp_can_reorder_employees(self):
        return self.state.capability

    def _tp_parse_positive_id(self, *args, **kwargs):
        return namespace['_tp_parse_positive_id'](self, *args, **kwargs)

    def _tp_lock_employee_order(self, companies):
        self.state.locks.append(companies)


class ReorderActionTests(unittest.TestCase):
    def setUp(self):
        self.state = SimpleNamespace(
            rows={eid: dict(company=1, department=10, active=True, sequence=eid * 10)
                  for eid in range(1, 6)},
            denied={}, capability=True, writes=[], checks=[], locks=[], search_contexts=[],
        )
        self.sql_rows = []

        def execute(sql, params):
            company, dept = params
            self.sql_rows = sorted(((eid, row['sequence']) for eid, row in self.state.rows.items()
                if row['company'] == company and row['department'] == dept and row['active']),
                key=lambda pair: (pair[1], pair[0]))
        self.state.env = SimpleNamespace(
            companies=SimpleNamespace(ids=[1]), _=lambda message, *args: message,
            flush_all=lambda: None, invalidate_all=lambda: None,
            cr=SimpleNamespace(execute=execute, fetchall=lambda: self.sql_rows),
        )
        self.model = MockEmployeeSet(self.state, context={'version_id': 900})

    def action(self, employee=5, department=10, **anchors):
        return namespace['tp_reorder_in_department'](self.model, employee, department, **anchors)

    def test_readonly_actor_rejected_before_any_lock_or_write(self):
        self.state.capability = False
        with self.assertRaises(PermissionError):
            self.action(before_id=2)
        self.assertEqual(self.state.locks, [])
        self.assertEqual(self.state.writes, [])

    def test_partial_page_reorders_full_department_sequence_only(self):
        # Client only supplies moved/anchor IDs; employees 3 and 4 are unseen on its page.
        result = self.action(before_id=2)
        self.assertEqual(result['ordered_ids'], [1, 5, 2, 3, 4])
        self.assertEqual(self.state.writes, [(5, {'sequence': 20}), (2, {'sequence': 30}),
                                           (3, {'sequence': 40}), (4, {'sequence': 50})])
        self.assertIn(('write', (1, 2, 3, 4, 5)), self.state.checks)
        self.assertEqual(self.state.search_contexts[0]['version_id'], False)

    def test_cross_department_and_company_anchors_rejected_without_write(self):
        for changes in ({'department': 20}, {'company': 2}):
            with self.subTest(changes=changes):
                self.state.rows[2].update(company=1, department=10)
                self.state.rows[2].update(changes)
                with self.assertRaises(ValueError):
                    self.action(before_id=2)
                self.assertEqual(self.state.writes, [])

    def test_moved_employee_wrong_department_or_company_rejected(self):
        with self.assertRaises(ValueError):
            self.action(department=20, before_id=2)
        self.state.rows[5]['company'] = 2
        with self.assertRaises(PermissionError):
            self.action(before_id=2)
        self.assertEqual(self.state.writes, [])

    def test_every_affected_record_needs_read_and_write_access(self):
        for mode in ('read', 'write'):
            with self.subTest(mode=mode):
                self.state.denied = {mode: {3}}
                with self.assertRaises(PermissionError):
                    self.action(before_id=2)
                self.assertEqual(self.state.writes, [])

    def test_stale_anchors_or_archived_reference_rejected(self):
        with self.assertRaises(ValueError):
            self.action(after_id=1, before_id=4)
        self.state.rows[2]['active'] = False
        with self.assertRaises(ValueError):
            self.action(before_id=2)
        self.assertEqual(self.state.writes, [])


if __name__ == '__main__':
    unittest.main()
