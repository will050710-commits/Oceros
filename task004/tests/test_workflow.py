import contextlib
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import psutil

from task004.cli import main, run_dry_run
from task004.client import ClientError, request_synthetic
from task004.config import Config
from task004.interfaces import real_model_adapter
from task004.record import encoded, validate_record
from task004.sampler import ResourceSampler
from task004.schema import validate_artifact
from task004.server import ManagedMockServer


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)
        self.config = Config(n_ctx=4096, sample_interval_s=.1)

    def run_case(self, config=None, event=None):
        record, folder = run_dry_run(config or self.config, self.out, event)
        validate_record(record)
        manifest = json.loads((folder / "manifest.json").read_text())
        validate_artifact(manifest, "manifest")
        data = (folder / "runs.jsonl").read_bytes()
        self.assertEqual(manifest["results"]["sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(manifest["config_sha256"], hashlib.sha256(encoded(manifest["config"])).hexdigest())
        self.assertEqual(len(data.splitlines()), 1)
        self.assertEqual(json.loads(data), record)
        self.assertEqual(manifest["evidence_label"], "SYNTHETIC")
        self.assertEqual(manifest["benchmark_status"], "NOT_RUN")
        self.assertIsNone(manifest["dataset_manifest_hash"])
        return record, manifest, folder

    def test_success_artifact_integrity_and_missing_metrics(self):
        record, manifest, _ = self.run_case()
        self.assertEqual(record["status"], "PASS")
        self.assertEqual(manifest["input_provenance"]["status"], "MATCH")
        self.assertGreater(record["resources"]["rss_peak_bytes"], 0)
        self.assertGreater(record["resources"]["samples"], 0)
        for field in ("ttft_s", "prefill_tokens_s", "decode_tokens_s"):
            self.assertIsNone(record["metrics"][field])
        if os.name != "nt":
            self.assertIsNone(record["resources"]["commit_peak_bytes"])

    def test_fault_results(self):
        for scenario, reason in (("malformed_json", "INVALID_JSON"), ("http_error", "HTTP_ERROR"), ("disconnect", "CONNECTION_ERROR")):
            with self.subTest(scenario=scenario):
                record, _, _ = self.run_case(replace(self.config, mock_scenario=scenario))
                self.assertEqual((record["status"], record["reason_code"]), ("FAIL", reason))

    def test_timeout_is_bounded_and_threads_finish(self):
        start = time.monotonic()
        record, _, _ = self.run_case(replace(self.config, mock_scenario="slow", timeout_s=.1))
        self.assertEqual((record["status"], record["reason_code"]), ("TIMEOUT", "TIMEOUT"))
        self.assertLess(time.monotonic() - start, 4)
        self.assertFalse(any(t.name in ("task004-http", "task004-sampler") for t in threading.enumerate()))

    def test_health_timeout_writes_evidence(self):
        record, _, _ = self.run_case(replace(self.config, mock_scenario="health_failure", startup_timeout_s=.2))
        self.assertEqual(record["reason_code"], "STARTUP_TIMEOUT")
        self.assertIsNone(record["resources"])

    def test_cancel_in_flight(self):
        event = threading.Event()
        timer = threading.Timer(.4, event.set)
        timer.start()
        self.addCleanup(timer.cancel)
        record, _, _ = self.run_case(replace(self.config, mock_scenario="slow"), event)
        self.assertEqual(record["status"], "CANCELLED")

    def test_cancel_before_launch(self):
        event = threading.Event()
        event.set()
        with patch.object(ManagedMockServer, "start") as start:
            record, _, _ = self.run_case(event=event)
        start.assert_not_called()
        self.assertEqual(record["status"], "CANCELLED")

    def test_preflight_failure_prevents_spawn(self):
        with patch.object(ManagedMockServer, "start") as start:
            record, _, _ = self.run_case(replace(self.config, min_available_ram_bytes=2**63))
        start.assert_not_called()
        self.assertEqual(record["status"], "PREFLIGHT_FAILED")

    def test_no_raw_content_or_environment_in_logs(self):
        marker = "SECRET_MUST_NOT_APPEAR_729313"
        with patch.dict(os.environ, {"TASK004_TEST_SECRET": marker}):
            _, _, folder = self.run_case()
        text = "".join(p.read_text() for p in folder.iterdir())
        for forbidden in (marker, "SYNTHETIC_INPUT", "SYNTHETIC_OK", "TASK004_TEST_SECRET"):
            self.assertNotIn(forbidden, text)

    def test_cli_errors_do_not_echo_config_secrets(self):
        config = self.out / "secret.json"
        config.write_text('{"n_ctx":4096,"api_key":"SECRET_MUST_NOT_APPEAR"}')
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            status = main(["dry-run", "--config", str(config)])
        self.assertEqual(status, 2)
        self.assertNotIn("SECRET_MUST_NOT_APPEAR", capture.getvalue())

    def test_repeated_runs_keep_both_artifacts(self):
        _, _, first = self.run_case()
        before = (first / "manifest.json").read_bytes()
        _, _, second = self.run_case()
        self.assertNotEqual(first, second)
        self.assertEqual((first / "manifest.json").read_bytes(), before)

    def test_record_rejects_wrong_label_or_fabricated_metrics(self):
        record, _, _ = self.run_case()
        record["evidence_label"] = "VERIFIED"
        with self.assertRaises(ValueError):
            validate_record(record)
        record["evidence_label"] = "SYNTHETIC"
        record["metrics"]["ttft_s"] = .1
        with self.assertRaises(ValueError):
            validate_record(record)

    def test_real_adapter_disabled(self):
        with self.assertRaises(NotImplementedError):
            real_model_adapter()

    def test_nested_schema_rejects_unrecognized_log_fields(self):
        record, manifest, _ = self.run_case()
        record["resources"]["raw_response"] = "not allowed"
        with self.assertRaises(ValueError):
            validate_record(record)
        manifest["preflight"]["environment"] = {"secret": "not allowed"}
        with self.assertRaises(ValueError):
            validate_artifact(manifest, "manifest")

    def test_cleanup_failure_is_recorded(self):
        from task004.server import ServerError
        original = ManagedMockServer.stop
        def stop_then_report_failure(server):
            original(server)
            raise ServerError("CLEANUP_FAILED")
        with patch.object(ManagedMockServer, "stop", stop_then_report_failure):
            record, _, _ = self.run_case()
        self.assertEqual((record["status"], record["reason_code"]), ("FAIL", "CLEANUP_FAILED"))

    def test_nonloopback_endpoint_rejected_before_connection(self):
        for url in ("https://example.com", "http://localhost:80", "http://127.0.0.1:80/redirect", "http://user:password@127.0.0.1:80"):
            with self.subTest(url=url), patch("task004.client.http.client.HTTPConnection") as connection:
                with self.assertRaises(ClientError) as caught:
                    request_synthetic(url, self.config)
                self.assertEqual(caught.exception.code, "NON_LOOPBACK_ENDPOINT")
                connection.assert_not_called()

    def test_connection_failure(self):
        with ManagedMockServer(self.config) as server:
            url = server.url
        with self.assertRaises(ClientError) as caught:
            request_synthetic(url, self.config)
        self.assertEqual(caught.exception.code, "CONNECTION_ERROR")

    def test_sampler_real_memory_allocation(self):
        process = subprocess.Popen([sys.executable, "-c", "import time; data=bytearray(16000000); print('ready',flush=True); time.sleep(10)"], stdout=subprocess.PIPE)
        self.addCleanup(lambda: process.poll() is None and process.kill())
        self.addCleanup(process.stdout.close)
        try:
            self.assertEqual(process.stdout.readline().strip(), b"ready")
            sampler = ResourceSampler(process.pid, .01).start()
            sampler.stop()
            self.assertGreater(sampler.rss_peak_bytes, 16_000_000)
        finally:
            process.terminate()
            process.wait(timeout=3)

    def test_cli_subprocess_exit_codes(self):
        for scenario, expected in (("success", 0), ("http_error", 1), ("slow", 124)):
            config = self.out / f"{scenario}.json"
            config.write_text(json.dumps(replace(self.config, mock_scenario=scenario, timeout_s=.1).to_dict()))
            command = [sys.executable, "-m", "task004.cli", "dry-run", "--config", str(config), "--output-dir", str(self.out / "cli")]
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            for marker in ("Traceback", "ResourceWarning", "Exception ignored"):
                self.assertNotIn(marker, result.stderr)
            self.assertEqual(json.loads(result.stdout)["evidence_label"], "SYNTHETIC")


if __name__ == "__main__":
    unittest.main()
