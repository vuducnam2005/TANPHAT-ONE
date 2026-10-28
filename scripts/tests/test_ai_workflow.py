"""Exercise handoff failures in isolated temporary workspaces, without Git/DB."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / 'ai_workflow.py'
SPEC = importlib.util.spec_from_file_location('ai_workflow', MODULE_PATH)
workflow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workflow)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.write('docs/PROJECT_STATUS.md', 'Initial status\n')
        self.write('docs/CHANGELOG.md', '# Changes\n')
        self.write('frontend/src/main.tsx', 'initial')

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def record(self, change_id='CHG-20261028-001'):
        workflow.start(self.root)
        self.write('docs/PROJECT_STATUS.md', f'Last change: `{change_id}`\nReady\n')
        self.write('docs/CHANGELOG.md', f'# Changes\n## {change_id} — test\nValidated\n')
        workflow.finish(self.root, change_id, ['isolated test'])

    def test_code_only_edit_fails_after_recorded_baseline(self):
        self.record()
        self.write('frontend/src/main.tsx', 'changed')
        with self.assertRaisesRegex(ValueError, 'code changed'):
            workflow.check(self.root)

    def test_added_and_removed_files_invalidate_handoff(self):
        self.record()
        self.write('custom_addons/tp_new/__manifest__.py', '{}')
        with self.assertRaises(ValueError):
            workflow.check(self.root)
        (self.root / 'custom_addons/tp_new/__manifest__.py').unlink()
        workflow.check(self.root)
        (self.root / 'frontend/src/main.tsx').unlink()
        with self.assertRaises(ValueError):
            workflow.check(self.root)

    def test_finish_requires_both_records_updated(self):
        workflow.start(self.root)
        self.write('docs/PROJECT_STATUS.md', 'Last change: `CHG-20261028-001`\n')
        with self.assertRaisesRegex(ValueError, 'both handoff records'):
            workflow.finish(self.root, 'CHG-20261028-001', ['not run: documentation only'])

    def test_resume_preserves_original_checkpoint(self):
        workflow.start(self.root)
        original = (self.root / workflow.CHECKPOINT_FILE).read_bytes()
        self.write('frontend/src/main.tsx', 'changed')
        workflow.start(self.root)
        self.assertEqual(original, (self.root / workflow.CHECKPOINT_FILE).read_bytes())

    def test_documentation_only_changes_also_require_handoff(self):
        self.record()
        self.write('docs/PROJECT_STATUS.md', 'Unrecorded new status')
        with self.assertRaisesRegex(ValueError, 'records changed'):
            workflow.check(self.root)

    def test_unique_change_id_and_status_marker_are_required(self):
        workflow.start(self.root)
        self.write('docs/PROJECT_STATUS.md', 'Last change: `CHG-20261028-002`\n')
        self.write('docs/CHANGELOG.md', '## CHG-20261028-001 test\n')
        with self.assertRaisesRegex(ValueError, 'current change ID'):
            workflow.finish(self.root, 'CHG-20261028-001', ['test'])
        self.write('docs/PROJECT_STATUS.md', 'Last change: `CHG-20261028-001`\n')
        self.write('docs/CHANGELOG.md', '## CHG-20261028-001 first\n## CHG-20261028-001 second\n')
        with self.assertRaisesRegex(ValueError, 'uniquely'):
            workflow.finish(self.root, 'CHG-20261028-001', ['test'])

    def test_runtime_and_upstream_are_outside_application_gate(self):
        self.record()
        self.write('.local/dev-secrets.json', 'not read by checker')
        self.write('odoo/not-application-code.py', '# upstream')
        self.write('frontend/src/__pycache__/cached.py', '# cache')
        workflow.check(self.root)

    def test_clean_record_passes_without_git_or_database(self):
        self.record()
        workflow.check(self.root)
        self.assertFalse((self.root / workflow.CHECKPOINT_FILE).exists())

    def test_line_endings_do_not_create_a_false_code_change(self):
        self.write('frontend/src/main.tsx', 'first\nsecond\n')
        self.record()
        (self.root / 'frontend/src/main.tsx').write_bytes(b'first\r\nsecond\r\n')
        workflow.check(self.root)

    def test_policy_changes_require_a_new_handoff(self):
        self.record()
        self.write('AGENTS.md', 'A revised instruction')
        with self.assertRaisesRegex(ValueError, 'records changed'):
            workflow.check(self.root)

    def test_an_unfinished_session_is_not_reported_as_clean(self):
        self.record()
        workflow.start(self.root)
        with self.assertRaisesRegex(ValueError, 'unfinished'):
            workflow.check(self.root)


if __name__ == '__main__':
    unittest.main()
