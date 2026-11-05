"""Versioned synthetic artifacts; persist only explicitly selected fields."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import uuid

import psutil

from .config import parse_config
from .schema import validate_artifact


STATUS_REASONS = {
    "PASS": {"OK"},
    "FAIL": {"HTTP_ERROR", "INVALID_JSON", "INVALID_RESPONSE", "CONNECTION_ERROR",
             "RESPONSE_TOO_LARGE", "CLIENT_ERROR", "SERVER_ERROR", "SERVER_EXITED",
             "INTERNAL_ERROR", "CLEANUP_FAILED", "MEMORY_SAMPLING_FAILED", "CLIENT_CLEANUP_FAILED"},
    "TIMEOUT": {"TIMEOUT", "STARTUP_TIMEOUT"},
    "CANCELLED": {"CANCELLED"},
    "PREFLIGHT_FAILED": {"PREFLIGHT_FAILED"},
}
RECORD_KEYS = {"schema_version", "run_id", "task_id", "evidence_label", "status",
               "reason_code", "started_at_utc", "finished_at_utc", "metrics", "resources"}
METRICS = {"run_elapsed_s", "request_latency_s", "ttft_s", "prefill_tokens_s",
           "decode_tokens_s", "synthetic_output_tokens"}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def validate_record(record):
    validate_artifact(record, "run")
    if set(record) != RECORD_KEYS:
        raise ValueError("RECORD_FIELDS_INVALID")
    if record["schema_version"] != 1 or record["task_id"] != "TASK-004" or record["evidence_label"] != "SYNTHETIC":
        raise ValueError("RECORD_IDENTITY_INVALID")
    if record["reason_code"] not in STATUS_REASONS.get(record["status"], set()):
        raise ValueError("RECORD_STATUS_INVALID")
    if uuid.UUID(record["run_id"]).hex != record["run_id"]:
        raise ValueError("RECORD_RUN_ID_INVALID")
    for key in ("started_at_utc", "finished_at_utc"):
        stamp = datetime.fromisoformat(record[key])
        if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError("RECORD_TIMESTAMP_INVALID")
    if set(record["metrics"]) != METRICS:
        raise ValueError("RECORD_METRICS_INVALID")
    for value in record["metrics"].values():
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
            raise ValueError("RECORD_METRICS_INVALID")
    if any(record["metrics"][name] is not None for name in ("ttft_s", "prefill_tokens_s", "decode_tokens_s")):
        raise ValueError("MOCK_PHASE_METRICS_UNAVAILABLE")
    if record["status"] == "PASS" and (record["metrics"]["request_latency_s"] is None or record["metrics"]["synthetic_output_tokens"] != 1):
        raise ValueError("PASS_REQUIRES_REQUEST_EVIDENCE")


def source_provenance():
    root = Path(__file__).parent / "references"
    index_path = root / "provenance.json"
    if not index_path.exists():
        return {"status": "UNVERIFIED", "sources": []}
    index = json.loads(index_path.read_text(encoding="utf-8"))
    result = []
    for item in index["sources"]:
        name = item["file"]
        if Path(name).name != name:
            raise ValueError("INVALID_PROVENANCE_PATH")
        path = root / name
        actual = sha256(path.read_bytes()) if path.is_file() else None
        result.append({"file": name, "expected_sha256": item["sha256"], "actual_sha256": actual,
                       "integrity": "MATCH" if actual == item["sha256"] else "UNVERIFIED"})
    return {"status": "MATCH" if all(x["integrity"] == "MATCH" for x in result) and result else "UNVERIFIED",
            "sources": result}


def write_artifacts(output_dir, config, record, preflight):
    validate_record(record)
    safe_config = parse_config(config.to_dict()).to_dict()
    run_dir = Path(output_dir) / record["run_id"]
    run_dir.mkdir(parents=True, exist_ok=False)
    jsonl = (json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode()
    manifest = {
        "schema_version": 1, "task_id": "TASK-004", "run_id": record["run_id"],
        "evidence_label": "SYNTHETIC", "status": record["status"],
        "config": safe_config, "config_sha256": sha256(encoded(safe_config)),
        "runtime": {"kind": "mock", "python_version": platform.python_version(),
                    "psutil_version": psutil.__version__, "os": platform.system(),
                    "phase_timers_supported": False, "streaming_supported": False},
        "decoding": {"temperature": 0, "seed": 1729, "n": 1, "thinking": False},
        "preflight": preflight, "input_provenance": source_provenance(),
        "hardware_reference": None, "dataset_manifest_hash": None,
        "benchmark_status": "NOT_RUN", "external_model_api_calls": 0,
        "metric_unavailability": {
            "ttft_s": "Non-streaming synthetic fixture; no content-token event",
            "prefill_tokens_s": "No model or runtime prefill phase timer",
            "decode_tokens_s": "No real decode phase; one synthetic output token",
        },
        "results": {"file": "runs.jsonl", "sha256": sha256(jsonl), "records": 1},
    }
    validate_artifact(manifest, "manifest")
    (run_dir / "runs.jsonl").write_bytes(jsonl)
    (run_dir / "manifest.json").write_bytes(encoded(manifest))
    return run_dir
