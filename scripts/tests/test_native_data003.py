"""No DB writes: operation guard regression tests before running the data migrator."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_data003 as task
import native_data003_preserve as preserve


class NativeData003Guards(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.patcher = patch.object(task, 'BASE', self.base)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def owner(self, **values):
        task.write(self.base / 'owner.json', {'workspace': str(task.ROOT), 'database': task.DATABASE,
                                            'source_uuid': 'source', 'rehearsal_passed': True, 'token': 'owned', **values})

    def test_dev_refuses_unrehearsed_and_other_workspace(self):
        for values in ({'rehearsal_passed': False}, {'workspace': 'D:/foreign'}, {'source_uuid': 'foreign'}):
            with self.subTest(values=values), patch.object(task, 'preflight', return_value='source'):
                self.owner(**values)
                with self.assertRaisesRegex(ValueError, 'rehearsal'):
                    task.target_config('dev')

    def test_clone_refuses_foreign_workspace_before_connect(self):
        self.owner(workspace='D:/foreign')
        with patch.object(task, 'preflight', return_value='source'), patch.object(task, 'connect') as connection:
            with self.assertRaisesRegex(ValueError, 'Foreign clone'):
                task.target_config('clone')
            connection.assert_not_called()

    def test_clone_refuses_foreign_db_token(self):
        self.owner()
        config = self.base / 'clone.conf'
        config.write_text('[options]\ndb_name=' + task.DATABASE, encoding='utf-8')
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value.fetchone.return_value = ['foreign']
        with patch.object(task, 'preflight', return_value='source'), patch.object(task, 'connect', return_value=connection):
            with self.assertRaisesRegex(ValueError, 'ownership mismatch'):
                task.target_config('clone')

    def test_corrupt_snapshot_refuses_before_database_creation(self):
        folder = self.base / 'snapshot'
        folder.mkdir()
        (folder / 'database.dump').write_bytes(b'changed')
        task.write(folder / 'manifest.json', {'database.dump': 'bad-checksum'})
        self.owner(snapshot=str(folder))
        with patch.object(task, 'private_root'), patch.object(task, 'preflight'), patch.object(task, 'connect') as connection:
            with self.assertRaisesRegex(ValueError, 'checksum'):
                task.clone()
            connection.assert_not_called()

    def test_reused_pid_is_not_terminated(self):
        self.owner(pid=999)
        process = MagicMock()
        process.cmdline.return_value = ['foreign.exe']
        with patch.object(task, 'target_config', return_value=(self.base / 'clone.conf', task.DATABASE)), \
                patch.object(task.psutil, 'pid_exists', return_value=True), patch.object(task.psutil, 'Process', return_value=process):
            with self.assertRaisesRegex(ValueError, 'foreign process'):
                task.runtime('stop')
            process.terminate.assert_not_called()

    def test_preservation_detects_shared_secret_and_role_change(self):
        before = {'files': {'config': 'original'}, 'cluster': {'roles': ['original']}, 'tables': {}}
        for after in ({**before, 'files': {'config': 'changed'}}, {**before, 'cluster': {'roles': ['changed']}}):
            with self.assertRaises(ValueError):
                preserve.compare(before, after)

    def test_hash_report_identifies_exact_changed_field(self):
        before = {'files': {}, 'cluster': {}, 'tables': {'res_users': {'2': {'password': 'same', 'lang': 'old'}}}}
        after = json.loads(json.dumps(before))
        after['tables']['res_users']['2']['lang'] = 'new'
        diff = preserve.compare(before, after)
        self.assertEqual(diff['changed_tables']['res_users']['updated'], {'2': ['lang']})

    def test_journal_preserves_original_before_and_final_after(self):
        first = {'model': 'res.users', 'id': 23, 'field': 'group_ids', 'before': [1], 'after': [1, 2]}
        second = {**first, 'before': [1, 2], 'after': [1, 2, 3]}
        merged = task.merge_journal([first, second], lambda *_: [1, 2, 3])
        self.assertEqual(merged, [{**first, 'after': [1, 2, 3]}])
        self.assertEqual(first['after'], [1, 2])

    def test_mail_isolation_refuses_configured_transport(self):
        env = MagicMock()
        env.__getitem__.return_value.search_count.return_value = 1
        with self.assertRaisesRegex(ValueError, 'SMTP server'):
            task.isolate_mail(env)


if __name__ == '__main__':
    unittest.main()
