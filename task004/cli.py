"""Run from the checkout root: python -m task004.cli --help."""
import argparse
import json
from pathlib import Path
import signal
import time
import uuid

from .client import ClientError, request_synthetic
from .config import ConfigError, load_config
from .preflight import check_preflight
from .record import utc_now, write_artifacts
from .sampler import ResourceSampler
from .server import ManagedMockServer, ServerError, ServerTimeout


def run_dry_run(config, output_dir, cancel_event=None):
    start = time.monotonic()
    record = {
        "schema_version": 1, "task_id": "TASK-004", "run_id": uuid.uuid4().hex,
        "evidence_label": "SYNTHETIC", "started_at_utc": utc_now(),
        "finished_at_utc": None, "status": "FAIL", "reason_code": "INTERNAL_ERROR",
        "metrics": {"run_elapsed_s": None, "request_latency_s": None, "ttft_s": None,
                    "prefill_tokens_s": None, "decode_tokens_s": None, "synthetic_output_tokens": None},
        "resources": None,
    }
    preflight = check_preflight(config, Path(output_dir))
    server = ManagedMockServer(config)
    sampler = None
    try:
        if cancel_event is not None and cancel_event.is_set():
            raise ClientError("CANCELLED")
        if not preflight["ready"]:
            record.update(status="PREFLIGHT_FAILED", reason_code="PREFLIGHT_FAILED")
        else:
            server.start(cancel_event)
            sampler = ResourceSampler(server.pid, config.sample_interval_s).start()
            metrics = request_synthetic(server.url, config, cancel_event)
            record["metrics"].update(metrics)
            record.update(status="PASS", reason_code="OK")
    except ServerTimeout:
        record.update(status="TIMEOUT", reason_code="STARTUP_TIMEOUT")
    except ClientError as error:
        status = {"TIMEOUT": "TIMEOUT", "CANCELLED": "CANCELLED"}.get(error.code, "FAIL")
        record.update(status=status, reason_code=error.code)
    except ServerError as error:
        record.update(status="CANCELLED" if error.code == "CANCELLED" else "FAIL", reason_code=error.code)
    except KeyboardInterrupt:
        record.update(status="CANCELLED", reason_code="CANCELLED")
    except Exception:
        record.update(status="FAIL", reason_code="INTERNAL_ERROR")
    finally:
        try:
            if sampler is not None:
                sampler.stop()
                record["resources"] = sampler.metrics()
                if record["status"] == "PASS" and not sampler.samples:
                    record.update(status="FAIL", reason_code="MEMORY_SAMPLING_FAILED")
        except Exception:
            record.update(status="FAIL", reason_code="MEMORY_SAMPLING_FAILED")
        finally:
            try:
                server.stop()
            except (ServerError, OSError):
                record.update(status="FAIL", reason_code="CLEANUP_FAILED")
    record["finished_at_utc"] = utc_now()
    record["metrics"]["run_elapsed_s"] = time.monotonic() - start
    return record, write_artifacts(output_dir, config, record, preflight)


def main(argv=None):
    parser = argparse.ArgumentParser(description="TASK-004 synthetic-only harness")
    parser.add_argument("command", choices=("validate-config", "preflight", "dry-run"))
    parser.add_argument("--config", default="task004/mock_config.json")
    parser.add_argument("--output-dir", default="task004/runs")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError:
        print(json.dumps({"status": "CONFIG_ERROR", "reason_code": "INVALID_CONFIG"}))
        return 2
    if args.command == "validate-config":
        print(json.dumps({"status": "PASS", "runtime": "mock"}))
        return 0
    if args.command == "preflight":
        result = check_preflight(config, Path(args.output_dir))
        print(json.dumps(result, sort_keys=True))
        return 0 if result["ready"] else 3
    # SIGTERM follows the same cleanup path as cancellation; restore the caller's handler.
    previous = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        record, _ = run_dry_run(config, Path(args.output_dir))
        print(json.dumps({key: record[key] for key in ("run_id", "status", "reason_code", "evidence_label")}))
        return {"PASS": 0, "PREFLIGHT_FAILED": 3, "CANCELLED": 130, "TIMEOUT": 124}.get(record["status"], 1)
    except OSError:
        print(json.dumps({"status": "FAIL", "reason_code": "ARTIFACT_WRITE_FAILED"}))
        return 1
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    raise SystemExit(main())
