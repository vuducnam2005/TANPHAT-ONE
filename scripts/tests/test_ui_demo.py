"""Guard tests for scripts/ui_demo.py without touching PostgreSQL or a running Odoo."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

MODULE = Path(__file__).resolve().parents[1] / 'ui_demo.py'
SPEC = importlib.util.spec_from_file_location('ui_demo', MODULE)
demo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(demo)


class UiDemoGuardTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        for name, value in (('BASE', self.base), ('CONFIG', self.base / 'odoo.conf'), ('OWNER', self.base / 'owner.json'),
                            ('CREDENTIALS', self.base / 'credentials.json'), ('PID_FILE', self.base / 'odoo.pid')):
            patcher = patch.object(demo, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def owner(self, **values):
        owner = {'workspace': str(demo.ROOT), 'token': 'own-token', 'databases': [demo.DEMO_DB], **values}
        demo.OWNER.write_text(json.dumps(owner), encoding='utf-8')
        return owner

    def test_refuses_dev_test_and_unprefixed_databases(self):
        for name in ('tp_tanphat_dev', 'tp_tanphat_test', 'tp_tanphat_restore', 'postgres', 'template1', 'demo', 'tp_demo'):
            with self.subTest(db=name), self.assertRaisesRegex(RuntimeError, 'Refusing'):
                demo.check_database(name)
        self.assertEqual(demo.check_database(demo.DEMO_DB), demo.DEMO_DB)
        self.assertEqual(demo.check_database(demo.TEST_DB), demo.TEST_DB)

    def test_refuses_a_runtime_folder_of_another_workspace(self):
        self.owner(workspace='D:/other-checkout')
        with self.assertRaisesRegex(RuntimeError, 'another workspace'):
            demo.read_owner()

    def test_refuses_existing_database_not_created_by_the_tool(self):
        owner = self.owner(databases=[])
        with patch.object(demo, 'database_exists', return_value=True), \
                patch.object(demo, 'database_token') as token, self.assertRaisesRegex(RuntimeError, 'not created by the demo tool'):
            demo.check_ownership({}, owner, demo.DEMO_DB)
        token.assert_not_called()

    def test_refuses_database_with_another_owner_token(self):
        owner = self.owner()
        with patch.object(demo, 'database_exists', return_value=True), \
                patch.object(demo, 'database_token', return_value='foreign-token'), \
                self.assertRaisesRegex(RuntimeError, 'another owner token'):
            demo.check_ownership({}, owner, demo.DEMO_DB)

    def test_accepts_own_database_and_reports_missing_one(self):
        owner = self.owner()
        with patch.object(demo, 'database_exists', return_value=True), patch.object(demo, 'database_token', return_value='own-token'):
            self.assertTrue(demo.check_ownership({}, owner, demo.DEMO_DB))
        with patch.object(demo, 'database_exists', return_value=True), patch.object(demo, 'database_token', return_value=None):
            self.assertTrue(demo.check_ownership({}, owner, demo.DEMO_DB))
        with patch.object(demo, 'database_exists', return_value=False):
            self.assertFalse(demo.check_ownership({}, owner, demo.DEMO_DB))

    def test_refuses_to_start_on_a_busy_port(self):
        with patch.object(demo.dev, 'is_listening', return_value=True), patch.object(demo.subprocess, 'Popen') as popen, \
                self.assertRaisesRegex(RuntimeError, 'did not start'):
            demo.start_server()
        popen.assert_not_called()
        self.assertFalse(demo.PID_FILE.exists())

    def test_stop_never_touches_a_foreign_process(self):
        demo.PID_FILE.write_text('4242', encoding='ascii')
        foreign = MagicMock()
        foreign.cmdline.return_value = ['python', 'C:/elsewhere/odoo-bin', '-c', 'C:/elsewhere/odoo.conf']
        with patch('psutil.Process', return_value=foreign), self.assertRaisesRegex(RuntimeError, 'another process'):
            demo.stop_server()
        foreign.terminate.assert_not_called()
        self.assertTrue(demo.PID_FILE.exists())

    def test_stop_terminates_only_its_own_process(self):
        demo.PID_FILE.write_text('4343', encoding='ascii')
        own = MagicMock()
        own.cmdline.return_value = ['python', str(demo.ROOT / 'odoo-bin'), '-c', str(demo.CONFIG)]
        own.children.return_value = []
        with patch('psutil.Process', return_value=own), patch('psutil.wait_procs', return_value=([own], [])):
            demo.stop_server()
        own.terminate.assert_called_once_with()
        self.assertFalse(demo.PID_FILE.exists())

    def test_stop_without_pid_file_is_a_no_op(self):
        with patch('psutil.Process') as process:
            demo.stop_server()
        process.assert_not_called()

    def test_credentials_are_generated_once_and_reused(self):
        first = demo.credentials()
        self.assertEqual(set(first), {'admin', 'db_manager', 'demo.lanhdao', 'demo.kysu'})
        self.assertEqual(demo.credentials(), first)
        self.assertEqual(len(set(first.values())), 4)


if __name__ == '__main__':
    unittest.main()
