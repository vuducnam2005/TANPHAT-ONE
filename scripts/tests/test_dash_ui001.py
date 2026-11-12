"""Guarded dashboard apply: preserve drift instead of overwriting user work."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dash_ui001 as task
from dashboard_templates import render_connected


class DashboardApplyGuards(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.base = Path(self.folder.name)
        self.patcher = patch.object(task, 'BASE', self.base)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.current = {'settings': {'legacy': True}}
        self.old = {'id': 6, 'xmlid': 'fixture.dashboard_finance_draft', 'data': self.current,
                    'name': 'Existing', 'users': [2, 29], 'groups': [], 'companies': [1], 'internal': True}
        self.target = {'settings': {'tpDashboard': {'kind': 'finance'}}}
        (self.base / 'inspect-dev.json').write_text(json.dumps({'bindings': [], 'dashboards': [self.old]}), encoding='utf-8')
        self.env = MagicMock()
        self.record = MagicMock()
        self.record.id = 6
        self.record.name = 'Existing'
        self.record.spreadsheet_data = json.dumps(self.current)
        self.record.allowed_user_ids = SimpleNamespace(ids=[2, 29])
        self.record.group_ids = SimpleNamespace(ids=[])
        self.record.company_ids = SimpleNamespace(ids=[1])
        self.record.tp_internal_only = True
        self.env.ref.return_value = self.record

    def apply(self, mode='apply'):
        with patch.object(task, 'render_connected', return_value={'dashboard_finance_draft': self.target}):
            task.apply(self.env, 'dev', mode)

    def test_preserve_user_spreadsheet_drift(self):
        self.record.spreadsheet_data = '{"settings":{"user_edit":true}}'
        with self.assertRaisesRegex(ValueError, 'User spreadsheet drift'):
            self.apply()
        self.env.cr.commit.assert_not_called()
        self.record.with_user.assert_not_called()

    def test_access_drift_refuses_and_preserves(self):
        self.record.allowed_user_ids.ids = [2, 29, 40]
        with self.assertRaisesRegex(ValueError, 'access drift'):
            self.apply()
        self.record.with_user.assert_not_called()

    def test_reapply_is_noop(self):
        self.record.spreadsheet_data = json.dumps(self.target)
        self.record.name = 'Tổng quan hóa đơn và chi phí'
        self.apply('verify')
        self.record.with_user.assert_not_called()
        self.env.cr.rollback.assert_called_once()

    def test_verify_never_fixes_missing_apply(self):
        with self.assertRaisesRegex(ValueError, 'not applied'):
            self.apply('verify')
        self.env.cr.commit.assert_not_called()

    def test_template_ids_resolve_without_money_snapshots(self):
        rows = [{'xmlid': 'fixture.project_' + key, 'model': 'project.project', 'id': i}
                for i, key in enumerate(('cau', 'duong', 'nut', 'venbien'), start=8)]
        rows += [{'xmlid': 'fixture.invoice', 'model': 'account.move', 'id': 4},
                 {'xmlid': 'fixture.expense', 'model': 'hr.expense', 'id': 7}]
        data = render_connected(copy.deepcopy(rows))
        for sheet in data.values():
            self.assertEqual(sheet['settings']['tpDashboard']['project_ids'], [8, 9, 10, 11])
            self.assertNotIn('IFERROR', json.dumps(sheet))
            self.assertNotIn('__PROJECT_IDS__', json.dumps(sheet))


if __name__ == '__main__':
    unittest.main()
