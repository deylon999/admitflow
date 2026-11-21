"""Existing invocations must reach the organized tools without changing cwd or exit codes."""
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from scripts import weekly_report
from scripts.reports import weekly_report as report_implementation

ROOT = Path(__file__).resolve().parents[2]


class CliCompatibilityTest(unittest.TestCase):
    def cli(self, *args, cwd=ROOT):
        return subprocess.run(
            [sys.executable, *args], cwd=cwd, capture_output=True, text=True, timeout=20,
        )

    def test_existing_module_import_uses_the_implementation(self):
        self.assertIs(weekly_report, report_implementation)

    def test_legacy_and_canonical_help_from_another_directory(self):
        with TemporaryDirectory() as directory:
            for category, filename in (
                ('data', 'build_accreditation_registry.py'),
                ('ops', 'ops_check.py'),
                ('reports', 'weekly_report.py'),
            ):
                with self.subTest(filename=filename):
                    old = self.cli(ROOT / 'scripts' / filename, '--help', cwd=directory)
                    new = self.cli(ROOT / 'scripts' / category / filename, '--help', cwd=directory)
                    self.assertEqual(old.returncode, 0, old.stderr)
                    self.assertIn('usage:', old.stdout)
                    self.assertEqual((new.returncode, new.stdout, new.stderr),
                                     (old.returncode, old.stdout, old.stderr))

    def test_module_and_legacy_path_keep_argument_error_exit_code(self):
        for args in (
            ('scripts/weekly_report.py',),
            ('-m', 'scripts.weekly_report'),
            ('-m', 'scripts.reports.weekly_report'),
        ):
            with self.subTest(args=args):
                result = self.cli(*args, '--format', 'md')
                self.assertEqual(result.returncode, 2)
                self.assertIn('--week', result.stderr)

    def test_public_postgres_help_supports_script_and_module(self):
        for args in (('scripts/test_postgres.py',), ('-m', 'scripts.test_postgres')):
            with self.subTest(args=args):
                result = self.cli(*args, '--help')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('--python', result.stdout)


if __name__ == '__main__':
    unittest.main()
