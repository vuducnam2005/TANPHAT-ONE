"""Test backup corruption/path boundaries without touching a running database."""
import hashlib
import importlib.util
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / 'backup_restore.py'
SPEC = importlib.util.spec_from_file_location('backup_restore', MODULE)
ops = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ops)


class BackupBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.folder = self.root / 'backups/example'
        self.folder.mkdir(parents=True)
        patcher = patch.object(ops, 'BASE', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def complete_backup(self):
        hashes = {}
        for name in ('database.dump', 'source.tar.gz', 'snapshot.json', 'private/odoo.conf', 'private/dev-secrets.json'):
            path = self.folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'private test payload')
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        (self.folder / 'manifest.json').write_text(json.dumps({
            'schema_version': 1, 'complete': True, 'source_database': ops.SOURCE_DB, 'sha256': hashes,
        }), encoding='utf-8')

    def test_rejects_traversal_absolute_windows_ads_and_sibling_paths(self):
        for value in ('../escape', '/absolute', 'C:/private', 'file:stream', '..\\escape', 'a/../../escape'):
            with self.subTest(path=value), self.assertRaises(ValueError):
                ops.beneath(self.root, value)
        self.assertEqual(ops.beneath(self.root, 'nested/file'), self.root / 'nested/file')

    def test_unrelated_backup_root_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'inside ops-001'):
            ops.verify_backup(self.root.parent / (self.root.name + '-sibling'))

    def test_valid_backup_and_tampered_payload(self):
        self.complete_backup()
        ops.verify_backup(self.folder)
        (self.folder / 'database.dump').write_bytes(b'corrupted dump')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            ops.verify_backup(self.folder)

    def test_missing_or_unmanifested_file_is_rejected(self):
        self.complete_backup()
        (self.folder / 'private/unrecorded.txt').write_text('extra', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Unexpected/missing'):
            ops.verify_backup(self.folder)
        (self.folder / 'private/unrecorded.txt').unlink()
        (self.folder / 'database.dump').unlink()
        with self.assertRaisesRegex(ValueError, 'Unexpected/missing'):
            ops.verify_backup(self.folder)

    def test_incomplete_backup_cannot_restore(self):
        (self.folder / 'manifest.json').write_text('{"complete": false}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            ops.verify_backup(self.folder)

    def make_tar(self, member):
        archive = self.root / 'source.tar.gz'
        with tarfile.open(archive, 'w:gz') as output:
            output.addfile(member, io.BytesIO(b'x') if member.isfile() else None)
        return archive

    def test_archive_traversal_fails_before_extraction(self):
        member = tarfile.TarInfo('../escaped')
        member.size = 1
        with self.assertRaises(ValueError):
            ops.extract_source(self.make_tar(member), self.root / 'source')
        self.assertFalse((self.root / 'escaped').exists())

    def test_archive_link_is_rejected(self):
        member = tarfile.TarInfo('linked')
        member.type = tarfile.SYMTYPE
        member.linkname = '/outside'
        with self.assertRaisesRegex(ValueError, 'link or special'):
            ops.extract_source(self.make_tar(member), self.root / 'source')

    def test_regular_source_archive_restores(self):
        member = tarfile.TarInfo('odoo/example.py')
        member.size = 1
        target = self.root / 'source'
        ops.extract_source(self.make_tar(member), target)
        self.assertEqual((target / 'odoo/example.py').read_bytes(), b'x')

    def test_failed_original_runtime_check_cannot_publish_success(self):
        report = {'restored_checks_passed': True, 'isolated_services_stopped': True}
        with patch.object(ops, 'verify_original_runtime', side_effect=ValueError('Original DB differs')):
            with self.assertRaisesRegex(ValueError, 'Original DB differs'):
                ops.finalize_report(self.root, report, self.folder, {})
        saved = json.loads((self.root / 'report.json').read_text())
        self.assertFalse(saved['passed'])

    def test_unfinished_cleanup_blocks_success_without_accessing_dev(self):
        report = {'restored_checks_passed': True, 'isolated_services_stopped': False}
        with patch.object(ops, 'verify_original_runtime') as original_check:
            with self.assertRaisesRegex(ValueError, 'cleanup'):
                ops.finalize_report(self.root, report, self.folder, {})
        original_check.assert_not_called()
        self.assertFalse(json.loads((self.root / 'report.json').read_text())['passed'])


if __name__ == '__main__':
    unittest.main()
