"""Round-two signal reentrancy, inherited policy and safe CLI failures."""
import contextlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import psutil

from task004 import cli
from task004.client import ClientError
from task004.config import Config
from task004.record import validate_record

ROOT = Path(__file__).resolve().parents[2]


class ReviewCliTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "POSIX signal test only")
    def test_nested_signal_cannot_deadlock_handler(self):
        # Trace the exact assignment inside Event.set's lock on the old implementation.
        # A second signal at that bytecode must finish; subprocess timeout bounds regression.
        script = '''
import linecache, os, signal, sys
from unittest.mock import patch
from task004.cli import main
triggered = False
def fake(config, output, cancel):
    def trace(frame, event, arg):
        global triggered
        line = linecache.getline(frame.f_code.co_filename, frame.f_lineno)
        if event == 'line' and frame.f_locals.get('self') is cancel and not triggered and ('_flag = True' in line or '_cancelled = True' in line):
            triggered = True
            os.kill(os.getpid(), signal.SIGTERM)
        return trace
    sys.settrace(trace)
    try:
        os.kill(os.getpid(), signal.SIGTERM)
    finally:
        sys.settrace(None)
    assert triggered and cancel.is_set()
    return {'run_id': '0'*32, 'status': 'CANCELLED', 'reason_code': 'CANCELLED', 'evidence_label': 'SYNTHETIC'}, None
with patch('task004.cli.run_dry_run', fake):
    assert main(['dry-run']) == 130
'''
        try:
            result = subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                                    capture_output=True, text=True, timeout=3)
        except subprocess.TimeoutExpired:
            self.fail("nested signal deadlocked cancellation handler")
        self.assertEqual(result.returncode, 0, result.stderr)
        for marker in ("Traceback", "ResourceWarning", "Exception ignored"):
            self.assertNotIn(marker, result.stderr)

    @unittest.skipUnless(hasattr(signal, "SIGHUP"), "SIGHUP unavailable")
    def test_inherited_ignore_is_preserved(self):
        old = signal.signal(signal.SIGHUP, signal.SIG_IGN)
        self.addCleanup(signal.signal, signal.SIGHUP, old)
        def fake(config, output, cancel):
            os.kill(os.getpid(), signal.SIGHUP)
            self.assertFalse(cancel.is_set(), "inherited ignored SIGHUP requested cancellation")
            self.assertEqual(signal.getsignal(signal.SIGHUP), signal.SIG_IGN)
            return {"run_id": "0"*32, "status": "PASS", "reason_code": "OK", "evidence_label": "SYNTHETIC"}, None
        with patch("task004.cli.run_dry_run", fake), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["dry-run"]), 0)
        self.assertEqual(signal.getsignal(signal.SIGHUP), signal.SIG_IGN)

    def test_unknown_previous_handler_is_never_replaced(self):
        with patch("task004.cli.signal.getsignal", return_value=None), patch("task004.cli.signal.signal") as install, \
                patch("task004.cli.run_dry_run", return_value=({"run_id": "0"*32, "status": "PASS", "reason_code": "OK", "evidence_label": "SYNTHETIC"}, None)), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["dry-run"]), 0)
        install.assert_not_called()

    def test_flag_wait_is_monotonic_without_threading_locks(self):
        from task004.cancellation import CancellationFlag
        flag = CancellationFlag()
        self.assertFalse(flag.wait(0))
        with patch("task004.cancellation.time.sleep", side_effect=lambda _: flag.set()):
            self.assertTrue(flag.wait(.1))
        flag.set()
        self.assertTrue(flag.wait(0))

    def test_initialization_exceptions_still_write_failed_artifact(self):
        for target in ("check_preflight", "ManagedMockServer"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                with patch("task004.cli." + target, side_effect=RuntimeError("PRIVATE_MARKER")):
                    record, folder = cli.run_dry_run(Config(n_ctx=1), Path(tmp))
                self.assertEqual(record["status"], "FAIL")
                self.assertEqual(record["reason_code"], "INTERNAL_ERROR")
                validate_record(json.loads((folder/"runs.jsonl").read_text()))
                self.assertNotIn("PRIVATE_MARKER", (folder/"manifest.json").read_text())

    def test_cleanup_failures_explicitly_override_cancel_and_timeout(self):
        for primary in ("CANCELLED", "TIMEOUT"):
            for failing in ("server", "sampler"):
                with self.subTest(primary=primary, failing=failing), tempfile.TemporaryDirectory() as tmp:
                    server = cli.ManagedMockServer
                    sampler = cli.ResourceSampler
                    original_stop = server.stop if failing == "server" else sampler.stop
                    def fail_after_stop(obj):
                        original_stop(obj)
                        raise psutil.AccessDenied()
                    target = "task004.cli.ManagedMockServer.stop" if failing == "server" else "task004.cli.ResourceSampler.stop"
                    with patch("task004.cli.request_synthetic", side_effect=ClientError(primary)), patch(target, fail_after_stop):
                        record, folder = cli.run_dry_run(Config(n_ctx=1), Path(tmp))
                    self.assertEqual(record["status"], "FAIL")
                    self.assertEqual(record["reason_code"], "CLEANUP_FAILED" if failing == "server" else "MEMORY_SAMPLING_FAILED")
                    validate_record(json.loads((folder/"runs.jsonl").read_text()))

    def test_last_resort_cli_boundary_does_not_expose_exception(self):
        for command in ("dry-run", "preflight"):
            capture = io.StringIO()
            with patch("task004.cli.check_preflight", side_effect=TypeError("PRIVATE_MARKER")), \
                    patch("task004.cli.write_artifacts", side_effect=KeyError("PRIVATE_MARKER")), \
                    contextlib.redirect_stdout(capture):
                self.assertEqual(cli.main([command]), 1)
            self.assertEqual(json.loads(capture.getvalue())["reason_code"], "INTERNAL_ERROR")
            self.assertNotIn("PRIVATE_MARKER", capture.getvalue())
