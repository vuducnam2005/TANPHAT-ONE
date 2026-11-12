"""No DB, no Odoo process: the clone test runner must fail closed on anything but a verified pass."""
import json
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_stabilize001 as task

DB = task.DATABASE
TAGS = '/tp_dashboard_privacy,/tp_web_home'
START = datetime(2026, 11, 5, 12, 0, 0, tzinfo=UTC)


def stamp(base, seconds=0):
    return (base + timedelta(seconds=seconds)).strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]


def started(module, name, base=START, db=DB):
    return f'{stamp(base, 5)} 4242 INFO {db} odoo.addons.{module}.tests.test_x: Starting TestX.{name} ...'


def summary(base=START, failed=0, errors=0, total=3, db=DB):
    level = 'ERROR' if failed or errors else 'WARNING' if not total else 'INFO'
    return (f'{stamp(base, 9)} 4242 {level} {db} odoo.tests.result: {failed} failed, {errors} error(s) '
            f"of {total} tests when loading database '{db}'")


def passing_log(base=START, **summary_values):
    """Shape of a real clone run: one summary, one "Starting" line per test, a harmless warning."""
    return '\n'.join([
        f'{stamp(base, 1)} 4242 INFO ? odoo: Odoo version 20.0',
        f'{stamp(base, 2)} 4242 WARNING {DB} odoo.addons.mail.controllers.attachment: markdown2 is not installed',
        started('tp_dashboard_privacy', 'test_a', base),
        started('tp_dashboard_privacy', 'test_b', base),
        started('tp_web_home', 'test_c', base),
        summary(base, **summary_values),
    ])


class EvaluateTestRun(unittest.TestCase):
    def verdict(self, text, returncode=0, **options):
        return task.evaluate_test_run(returncode, text, database=DB, tags=options.pop('tags', TAGS),
                                      started_at=options.pop('started_at', START), **options)

    def assertFails(self, verdict, problem):
        self.assertFalse(verdict['ok'], verdict)
        self.assertIn(problem, verdict['problems'])

    def test_verified_pass(self):
        verdict = self.verdict(passing_log())
        self.assertTrue(verdict['ok'], verdict['problems'])
        self.assertEqual((verdict['total'], verdict['failed'], verdict['errors']), (3, 0, 0))
        self.assertEqual(verdict['per_module'], {'tp_dashboard_privacy': 2, 'tp_web_home': 1})

    def test_process_failure_with_clean_log(self):
        self.assertFails(self.verdict(passing_log(), returncode=1), 'process_exit_nonzero')

    def test_failed_and_errored_summaries(self):
        self.assertFails(self.verdict(passing_log(failed=1)), 'tests_failed')
        self.assertFails(self.verdict(passing_log(errors=1)), 'tests_errored')

    def test_zero_tests(self):
        verdict = self.verdict('\n'.join([f'{stamp(START, 1)} 4242 INFO ? odoo: Odoo version 20.0', summary(total=0)]))
        self.assertFails(verdict, 'no_tests')
        self.assertIn('no_tests_for_tag:tp_web_home', verdict['problems'])

    def test_missing_summary_and_missing_log(self):
        self.assertFails(self.verdict('\n'.join(passing_log().splitlines()[:-1])), 'summary_missing')
        self.assertFails(self.verdict(''), 'summary_missing')

    def test_stale_log_from_an_earlier_run(self):
        self.assertFails(self.verdict(passing_log(), started_at=START + timedelta(minutes=5)), 'stale_log_lines')

    def test_appended_log_with_two_runs(self):
        later = START + timedelta(minutes=1)
        self.assertFails(self.verdict(passing_log() + '\n' + passing_log(later)), 'summary_multiple')

    def test_wrong_database(self):
        self.assertFails(self.verdict(passing_log().replace(f"database '{DB}'", "database 'tp_tanphat_dev'")),
                         'summary_wrong_database')
        log = passing_log().replace(f'INFO {DB} odoo.addons.tp_web_home', 'INFO tp_tanphat_dev odoo.addons.tp_web_home')
        self.assertFails(self.verdict(log), 'test_line_wrong_database')

    def test_tagged_module_without_tests(self):
        log = passing_log(total=2).replace(started('tp_web_home', 'test_c') + '\n', '')
        self.assertFails(self.verdict(log), 'no_tests_for_tag:tp_web_home')

    def test_started_lines_must_match_total(self):
        self.assertFails(self.verdict(passing_log(total=4)), 'started_count_mismatch')

    def test_expected_count_is_optional_and_exact(self):
        self.assertTrue(self.verdict(passing_log(), expect_tests=3)['ok'])
        self.assertFails(self.verdict(passing_log(), expect_tests=29), 'unexpected_test_count')

    def test_error_lines_fail_even_with_clean_summary(self):
        self.assertFails(self.verdict(passing_log().replace('WARNING', 'ERROR', 1)), 'error_log_lines')

    def test_tag_parsing(self):
        self.assertEqual(task.tag_modules('-/tp_web_home,/tp_contract:TestX.test_y,post_install,/tp_project[1]'),
                         (['tp_contract', 'tp_project'], ['post_install']))
        self.assertFails(self.verdict(passing_log(), tags='-/tp_web_home'), 'no_positive_tags')


class OdooTestsCommand(unittest.TestCase):
    """The command itself: identity checks, a fresh log per run and the process exit status."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        patchers = [patch.object(task, 'ROOT', root), patch.object(task, 'BASE', root / 'op'),
                    patch.object(task.native.dev, 'is_listening', return_value=False)]
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        task.BASE.mkdir()
        self.cfg = task.BASE / 'clone.conf'
        self.cfg.write_text(f'[options]\ndb_name = {DB}\nhttp_port = {task.PORT}\n', encoding='utf-8')
        self.owner()
        target = patch.object(task.native, 'target_config', return_value=(self.cfg, DB))
        target.start()
        self.addCleanup(target.stop)
        self.commands = []

    def owner(self, **values):
        (task.BASE / 'owner.json').write_text(json.dumps({'workspace': str(task.ROOT), 'database': DB,
                                                         'http_port': task.PORT, **values}), encoding='utf-8')

    def fake_odoo(self, make_log, returncode=0):
        """Stand-in for odoo-bin: writes the log it is pointed at, stamped at the time it runs."""
        def run(command, **_kwargs):
            self.commands.append(command)
            text = make_log(datetime.now(UTC))
            if text is not None:
                Path(command[command.index('--logfile') + 1]).write_text(text, encoding='utf-8')
            return SimpleNamespace(returncode=returncode)
        return patch.object(task.subprocess, 'run', side_effect=run)

    def run_command(self, make_log, returncode=0):
        with self.fake_odoo(make_log, returncode), patch('builtins.print'):
            return task.odoo_tests('tp_dashboard_privacy,tp_web_home', TAGS)

    def test_pass_returns_zero_and_records_its_own_log(self):
        self.assertEqual(self.run_command(passing_log), 0)
        command = self.commands[0]
        self.assertEqual(command[command.index('-d') + 1], DB)
        self.assertEqual(command[command.index('--test-tags') + 1], TAGS)
        verdicts = list((task.BASE / 'odoo-tests').glob('run-*.json'))
        self.assertEqual(len(verdicts), 1)
        verdict = json.loads(verdicts[0].read_text(encoding='utf-8'))
        self.assertTrue(verdict['ok'], verdict['problems'])
        self.assertEqual(Path(command[command.index('--logfile') + 1]).name, Path(verdict['log']).name)

    def test_failures_return_nonzero(self):
        cases = {
            'process': (passing_log, 1),
            'failed': (lambda now: passing_log(now, failed=1), 0),
            'zero': (lambda now: summary(now, total=0), 0),
            'missing_summary': (lambda now: '\n'.join(passing_log(now).splitlines()[:-1]), 0),
            'missing_log': (lambda _now: None, 0),
            'stale': (lambda now: passing_log(now - timedelta(hours=1)), 0),
        }
        for name, (make_log, returncode) in cases.items():
            with self.subTest(name):
                self.assertEqual(self.run_command(make_log, returncode), 1)

    def test_main_propagates_nonzero_exit(self):
        with patch.object(task, 'odoo_tests', return_value=1), patch.object(sys, 'argv', ['x', 'odoo-tests']), \
                patch.object(task, 'bind'), self.assertRaises(SystemExit) as raised:
            task.main()
        self.assertEqual(raised.exception.code, 1)

    def test_wrong_target_is_refused_before_running(self):
        for values in ({'http_port': 18069}, {'database': 'tp_tanphat_dev'}):
            with self.subTest(values=values):
                self.owner(**values)
                with self.fake_odoo(passing_log), self.assertRaises(ValueError):
                    task.odoo_tests('tp_web_home', '/tp_web_home')
        self.owner()
        with patch.object(task.native, 'target_config', return_value=(self.cfg, 'tp_tanphat_dev')), \
                self.fake_odoo(passing_log), self.assertRaises(ValueError):
            task.odoo_tests('tp_web_home', '/tp_web_home')
        self.assertEqual(self.commands, [])

    def test_existing_run_log_is_never_reused(self):
        runs = task.BASE / 'odoo-tests'
        runs.mkdir()
        (runs / f"run-{START.strftime('%Y%m%dT%H%M%S%fZ')}.log").write_text(passing_log(), encoding='utf-8')
        clock = SimpleNamespace(now=lambda _tz=None: START)
        with patch.object(task, 'datetime', clock), self.fake_odoo(passing_log), \
                self.assertRaisesRegex(ValueError, 'reuse'):
            task.odoo_tests('tp_web_home', '/tp_web_home')
        self.assertEqual(self.commands, [])


if __name__ == '__main__':
    unittest.main()
