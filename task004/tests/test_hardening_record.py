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

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "task004/evidence/dry-run/e1979d42784948cfbeb13b44cbc6044a"


class AtomicArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "out"
        self.manifest = json.loads((FIXTURE / "manifest.json").read_text())
        self.record = json.loads((FIXTURE / "runs.jsonl").read_text())
        self.config = parse_config(self.manifest["config"])

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
                self.assertEqual(list(self.root.iterdir()), [])

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
            process = subprocess.Popen([sys.executable, "-m", "task004.cli", "dry-run", "--config", str(cfg), "--output-dir", str(out)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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
                    if children:
                        break
                    time.sleep(.01)
                self.assertTrue(children, "mock child did not start")
                time.sleep(.1)
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
                self.assertNotIn("Traceback", stderr)
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
