"""A2: real signal delivery and transactional artifact regressions."""
import contextlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import psutil

from task004.cli import main
from task004.config import parse_config
from task004.record import validate_record, write_artifacts
from task004.schema import validate_artifact
from task004.tests.fixtures import artifact_fixture
from task004 import record as record_module
from task004.server import ManagedMockServer

ROOT = Path(__file__).resolve().parents[2]


class AtomicArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "out"
        self.config, self.record, preflight = artifact_fixture()
        self.manifest = {"preflight": preflight}

    def write(self):
        return write_artifacts(self.root, self.config, self.record, self.manifest["preflight"])

    def test_second_write_failure_cleans_staging_for_baseexceptions(self):
        original = Path.open
        for exception in (OSError("injected"), KeyboardInterrupt()):
            with self.subTest(exception=type(exception).__name__):
                # Independent paths even when the baseline leaves a partial run behind.
                self.root = Path(self.tmp.name) / type(exception).__name__
                def faulty(path, *args, **kwargs):
                    mode = args[0] if args else kwargs.get("mode", "r")
                    if path.name == "manifest.json" and mode == "wb":
                        raise exception
                    return original(path, *args, **kwargs)
                with patch.object(Path, "open", faulty), self.assertRaises(type(exception)):
                    self.write()
                self.assertEqual(list(self.root.iterdir()), [], "partial artifact survived injected failure")

    def test_every_write_sync_and_rename_failure_removes_staging(self):
        for failure_point in ("runs.jsonl", "manifest.json", "fsync-1", "fsync-2", "rename"):
            for error in (OSError("injected"), KeyboardInterrupt()):
                with self.subTest(point=failure_point, error=type(error).__name__):
                    self.root = Path(self.tmp.name) / (failure_point + type(error).__name__)
                    original_open, original_sync = Path.open, os.fsync
                    calls = 0
                    def faulty_open(path, *args, **kwargs):
                        if path.name == failure_point and (args[0] if args else kwargs.get('mode')) == 'wb':
                            raise error
                        return original_open(path, *args, **kwargs)
                    def faulty_sync(fd):
                        nonlocal calls
                        calls += 1
                        if failure_point == f'fsync-{calls}':
                            raise error
                        return original_sync(fd)
                    with patch.object(Path, 'open', faulty_open), patch('task004.record.os.fsync', faulty_sync), \
                            patch('task004.record.os.rename', side_effect=error) if failure_point == 'rename' else contextlib.nullcontext():
                        with self.assertRaises(type(error)):
                            self.write()
                    self.assertEqual(list(self.root.iterdir()), [])

    @unittest.skipUnless(os.name == 'posix', 'POSIX phase signals; Windows UNVERIFIED')
    def test_signals_during_cleanup_and_write_finish_committed_result(self):
        for phase in ('cleanup', 'write'):
            with self.subTest(phase=phase):
                config_path = Path(self.tmp.name) / 'config.json'
                config_path.write_text(json.dumps(self.config.to_dict()))
                output = Path(self.tmp.name) / phase
                original = ManagedMockServer.stop if phase == 'cleanup' else record_module._write_synced
                delivered = []
                def interrupted(*args, **kwargs):
                    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGTERM):
                        os.kill(os.getpid(), sig)
                        delivered.append(sig)
                    return original(*args, **kwargs)
                target = 'task004.cli.ManagedMockServer.stop' if phase == 'cleanup' else 'task004.record._write_synced'
                captured = io.StringIO()
                with patch(target, interrupted), contextlib.redirect_stdout(captured):
                    code = main(['dry-run', '--config', str(config_path), '--output-dir', str(output)])
                self.assertTrue(delivered)
                self.assertEqual(code, 0)
                self.assertEqual(json.loads(captured.getvalue())['status'], 'PASS')
                folders = list(output.iterdir())
                self.assertEqual(len(folders), 1)
                self.assertEqual({p.name for p in folders[0].iterdir()}, {'manifest.json', 'runs.jsonl'})
                validate_record(json.loads((folders[0]/'runs.jsonl').read_text()))

    def test_final_directory_invisible_until_both_synced_files_ready(self):
        original = Path.open
        seen = []
        def observing(path, *args, **kwargs):
            if args and args[0] == "wb":
                seen.append(path.name)
                self.assertFalse((self.root / self.record["run_id"]).exists())
                self.assertEqual(path.parent.name, f".{self.record['run_id']}.tmp")
            return original(path, *args, **kwargs)
        with patch.object(Path, "open", observing), patch("task004.record.os.fsync", wraps=os.fsync) as sync:
            folder = self.write()
        self.assertEqual(sync.call_count, 2)
        self.assertEqual(seen, ["runs.jsonl", "manifest.json"])
        self.assertEqual(list(self.root.iterdir()), [folder])
        validate_record(json.loads((folder / "runs.jsonl").read_text()))

    def test_invalid_manifest_has_no_partial_run(self):
        self.manifest["preflight"]["unexpected"] = "bad"
        with self.assertRaises(ValueError):
            self.write()
        self.assertFalse(self.root.exists())

    def test_existing_run_not_overwritten(self):
        folder = self.write()
        before = {p.name: p.read_bytes() for p in folder.iterdir()}
        with self.assertRaises(FileExistsError):
            self.write()
        self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})
        self.assertEqual(list(self.root.iterdir()), [folder])

    def test_main_valueerror_safe_and_signal_handlers_restored(self):
        config = Path(self.tmp.name) / "config.json"
        config.write_text(json.dumps(self.config.to_dict()))
        old = {getattr(signal, name): signal.getsignal(getattr(signal, name))
               for name in ("SIGINT", "SIGTERM", "SIGHUP", "SIGBREAK") if hasattr(signal, name)}
        captured = io.StringIO()
        with patch("task004.cli.write_artifacts", side_effect=ValueError("PRIVATE_MARKER")), contextlib.redirect_stdout(captured):
            code = main(["dry-run", "--config", str(config), "--output-dir", str(self.root)])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(captured.getvalue())["reason_code"], "INTERNAL_ERROR")
        self.assertNotIn("PRIVATE_MARKER", captured.getvalue())
        self.assertEqual(old, {number: signal.getsignal(number) for number in old})

    def test_validate_config_scope(self):
        config = Path(self.tmp.name) / "config.json"
        config.write_text(json.dumps(self.config.to_dict()))
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            self.assertEqual(main(["validate-config", "--config", str(config)]), 0)
        self.assertEqual(json.loads(captured.getvalue())["scope"], "CONFIG_ONLY")


@unittest.skipUnless(os.name == "posix", "POSIX signal integration; Windows UNVERIFIED")
class SignalArtifactTests(unittest.TestCase):
    def run_signal_case(self, sig, gap=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = root / "config.json"
            cfg.write_text(json.dumps({"n_ctx": 1, "mock_scenario": "slow", "mock_delay_s": 10, "timeout_s": 15}))
            out = root / "out"
            ready = root / "request-phase"
            script = '''
from pathlib import Path
import sys
from task004 import cli
marker = Path(sys.argv.pop(1))
original = cli.request_synthetic
def observed_request(*args, **kwargs):
    marker.write_text('request-phase', encoding='ascii')
    return original(*args, **kwargs)
cli.request_synthetic = observed_request
raise SystemExit(cli.main())
'''
            process = subprocess.Popen([sys.executable, "-c", script, str(ready), "dry-run", "--config", str(cfg), "--output-dir", str(out)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            children = []
            cleaned = False
            def cleanup():
                nonlocal cleaned
                if cleaned:
                    return
                cleaned = True
                if process.poll() is None:
                    try:
                        children.extend(psutil.Process(process.pid).children(recursive=True))
                    except psutil.NoSuchProcess:
                        pass
                    process.kill()
                process.wait(timeout=5)
                for child in children:
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass
                psutil.wait_procs(children, timeout=1)
                process.stdout.close()
                process.stderr.close()
            self.addCleanup(cleanup)
            try:
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline and process.poll() is None:
                    children = psutil.Process(process.pid).children(recursive=True)
                    if children and ready.exists():
                        break
                    time.sleep(.01)
                self.assertTrue(children, "mock child did not start")
                self.assertTrue(ready.exists(), "CLI did not reach request phase")
                for index in range(1 if gap is None else 3):
                    if index and gap:
                        time.sleep(gap)
                    if process.poll() is not None:
                        break
                    try:
                        process.send_signal(sig)
                    except ProcessLookupError:
                        break
                stdout, stderr = process.communicate(timeout=8)
                self.assertEqual(process.returncode, 130, stderr)
                result = json.loads(stdout)
                self.assertEqual(result["status"], "CANCELLED")
                self.assertEqual(result["evidence_label"], "SYNTHETIC")
                for marker in ("Traceback", "ResourceWarning", "Exception ignored"):
                    self.assertNotIn(marker, stderr)
                folders = list(out.iterdir())
                self.assertEqual(len(folders), 1)
                folder = folders[0]
                self.assertEqual({p.name for p in folder.iterdir()}, {"manifest.json", "runs.jsonl"})
                validate_record(json.loads((folder / "runs.jsonl").read_text()))
                validate_artifact(json.loads((folder / "manifest.json").read_text()), "manifest")
                for child in children:
                    self.assertFalse(child.is_running() and child.status() != psutil.STATUS_ZOMBIE)
            finally:
                cleanup()

    def test_single_signals_produce_complete_cancelled_artifacts(self):
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            with self.subTest(signal=sig):
                self.run_signal_case(sig)

    def test_burst_signals_do_not_interrupt_cleanup_or_artifacts(self):
        for sig in (signal.SIGINT, signal.SIGTERM):
            for gap in (0, .001, .003):
                with self.subTest(signal=sig, gap=gap):
                    self.run_signal_case(sig, gap)
