"""Evidence gates must detect false-success warnings and wrong regressions."""
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from task004.tools import validate_hardening as runner


class ReviewRunnerTests(unittest.TestCase):
    def test_finalizer_warning_rejected_even_with_success_exit(self):
        result = subprocess.run([sys.executable, '-W', 'error::ResourceWarning', '-c',
                                 'import socket,gc; s=socket.socket(); del s; gc.collect()'],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertIn('ResourceWarning', result.stderr)
        self.assertTrue(runner.log_diagnostics(result.stdout + result.stderr))

    def test_diagnostic_filter_distinguishes_expected_tracebacks(self):
        for marker in ('Exception ignored', 'ResourceWarning', 'Traceback'):
            self.assertIn(marker, runner.log_diagnostics(marker))
        self.assertEqual(runner.log_diagnostics('Traceback', allow_expected_traceback=True), [])
        self.assertTrue(runner.log_diagnostics('Exception ignored ResourceWarning', allow_expected_traceback=True))

    def test_assertion_failure_must_be_the_expected_defect(self):
        prefix = 'FAIL: test_a1_killed_cli_leaves_no_mock_or_owned_scratch (module.Class)\nTraceback\n'
        self.assertFalse(runner.expected_defect_failures(prefix + 'AssertionError: unrelated crash'))
        self.assertTrue(runner.expected_defect_failures(prefix + 'AssertionError: mock survived harness SIGKILL'))
        self.assertFalse(runner.expected_defect_failures(prefix + 'ImportError: mock survived harness SIGKILL'))
        for operand in ('config_accepts', 'schema_accepts'):
            block = ('FAIL: test_a4_config_and_manifest_numerical_boundaries_match (module.Class)\n'
                     f'self.assertEqual({operand}, expected)\nAssertionError: True != False')
            self.assertTrue(runner.expected_defect_failures(block))

    def test_archive_extraction_accepts_canonicalized_symlink_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'real').mkdir()
            try:
                (root/'alias').symlink_to(root/'real', target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest('symlink creation unavailable')
            raw = io.BytesIO()
            with tarfile.open(fileobj=raw, mode='w') as archive:
                info = tarfile.TarInfo('source.txt')
                info.size = 2
                archive.addfile(info, io.BytesIO(b'ok'))
            destination = runner.extract_archive(raw.getvalue(), root/'alias'/'baseline')
            self.assertEqual(destination, (root/'real'/'baseline').resolve())
            self.assertEqual((destination/'source.txt').read_bytes(), b'ok')

    def test_scope_uses_actual_platform_without_claiming_readiness(self):
        for system in ('Linux', 'Windows', 'Darwin'):
            with patch.object(runner.platform, 'system', return_value=system):
                label = runner.verification_scope()
            self.assertTrue(label.startswith(system + '-executed'))
            self.assertNotIn('verified', label)

    def test_fingerprints_cover_data_consumed_by_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(runner, 'ROOT', Path(tmp)):
            task = Path(tmp)/'task004'
            (task/'references').mkdir(parents=True)
            for name in ('mock_config.json', 'requirements.txt', 'setup.sh', 'references/provenance.json', 'references/card.md'):
                path = task/name
                path.write_text('original')
                before = runner.fingerprints()
                self.assertIn(str(path.relative_to(tmp)), before)
                path.write_text('changed')
                self.assertNotEqual(before, runner.fingerprints())

    def test_metadata_and_diagnostic_paths_hide_known_local_prefixes(self):
        locations = {r'C:\Users\private-user\work': '<checkout>', '/Users/private-user': '<home>'}
        for raw in (r'C:\Users\private-user\work\task004\cli.py', r'C:\\Users\\private-user\\work\\task004\\cli.py', '/Users/private-user/venv/bin/python'):
            sanitized = runner.normalize_paths(raw, locations)
            self.assertNotIn('private-user', sanitized)
        self.assertEqual(runner.normalize_paths('AssertionError: preserved', locations), 'AssertionError: preserved')
