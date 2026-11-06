"""Construct unit-test objects; never treat these invented values as runtime evidence."""
from task004.config import Config


def artifact_fixture():
    config = Config(n_ctx=1)
    stamp = "2026-11-07T00:00:00+00:00"
    record = {
        "schema_version": 1, "task_id": "TASK-004", "run_id": "0" * 32,
        "evidence_label": "SYNTHETIC", "status": "PASS", "reason_code": "OK",
        "started_at_utc": stamp, "finished_at_utc": stamp,
        "metrics": {"run_elapsed_s": 1, "request_latency_s": 1, "ttft_s": None,
                    "prefill_tokens_s": None, "decode_tokens_s": None, "synthetic_output_tokens": 1},
        "resources": {"rss_peak_bytes": 1, "commit_peak_bytes": None,
                      "rss_source": "UNIT_TEST_FIXTURE", "commit_source": None,
                      "commit_unavailable_reason": "UNIT_TEST_FIXTURE", "sample_interval_s": .1,
                      "samples": 1, "incomplete_samples": 0, "measurement_scope": "UNIT_TEST_FIXTURE",
                      "sampling_limitation": "Not a measurement"},
    }
    preflight = {"ready": True, "checks": [], "available_ram_bytes": None, "free_disk_bytes": None,
                 "system_commit": {"total_bytes": None, "limit_bytes": None, "available_bytes": None,
                                   "source": None, "unavailable_reason": "UNIT_TEST_FIXTURE"},
                 "observed_at_utc": stamp, "platform": "UNIT_TEST_FIXTURE", "measurement_scope": "CURRENT_HOST"}
    return config, record, preflight
