# TASK-004 current source snapshot

Generated from the validated source; this document does not execute code. SHA-256 per file can be checked against validation.json.

## task004/__init__.py

SHA-256: `8bf7aeb48749ed799265f3f26bdd6d7092e959400abb889e3a7701c1253d4b3b`

```python
"""TASK-004 synthetic runtime harness. No real model execution."""

__version__ = "0.1.0"

```

## task004/cancellation.py

SHA-256: `9889fc4670100c0b33014e6e770925b501b2e37e2f75edaecdf9d87668f7ebc6`

```python
"""Monotonic cancellation flag safe for reentrant Python signal handlers.

No locks, callbacks or reset operations occur in set(). This is not a general
Event replacement: it intentionally supports only set/is_set/polling wait.
"""
import time


class CancellationFlag:
    def __init__(self):
        self._cancelled = False

    def set(self):
        self._cancelled = True

    def is_set(self):
        return self._cancelled

    def wait(self, timeout=None):
        deadline = None if timeout is None else time.monotonic() + max(0, timeout)
        while not self._cancelled:
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                return self._cancelled
            time.sleep(.01 if remaining is None else min(.01, remaining))
        return True

```

## task004/cli.py

SHA-256: `7abb66960e5265369202acae7985d8258217fe099256a67c2dd15d797d29539c`

```python
"""Run from the checkout root: python -m task004.cli --help."""
import argparse
import json
from pathlib import Path
import signal
import platform
import time
import uuid

from .client import ClientError, request_synthetic
from .cancellation import CancellationFlag
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
    # A failed initialization can still produce an honest artifact, with no invented readings.
    preflight = {
        "ready": False, "checks": [], "available_ram_bytes": None, "free_disk_bytes": None,
        "system_commit": {"total_bytes": None, "limit_bytes": None, "available_bytes": None,
                          "source": None, "unavailable_reason": "PREFLIGHT_NOT_COMPLETED"},
        "observed_at_utc": utc_now(), "platform": platform.system(), "measurement_scope": "CURRENT_HOST",
    }
    server = None
    sampler = None
    try:
        if cancel_event is not None and cancel_event.is_set():
            raise ClientError("CANCELLED")
        preflight = check_preflight(config, Path(output_dir))
        if not preflight["ready"]:
            record.update(status="PREFLIGHT_FAILED", reason_code="PREFLIGHT_FAILED")
        else:
            server = ManagedMockServer(config)
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
                if server is not None:
                    server.stop()
            except Exception:
                # Cleanup integrity takes precedence over request cancellation/timeout.
                record.update(status="FAIL", reason_code="CLEANUP_FAILED")
    record["finished_at_utc"] = utc_now()
    record["metrics"]["run_elapsed_s"] = time.monotonic() - start
    return record, write_artifacts(output_dir, config, record, preflight)


def _main(argv=None):
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
        print(json.dumps({"status": "PASS", "runtime": "mock", "scope": "CONFIG_ONLY"}))
        return 0
    if args.command == "preflight":
        result = check_preflight(config, Path(args.output_dir))
        print(json.dumps(result, sort_keys=True))
        return 0 if result["ready"] else 3
    # Signals request cancellation; repeated signals must not interrupt cleanup or writes.
    cancel = CancellationFlag()
    previous = {}
    try:
        for name in ("SIGINT", "SIGTERM", "SIGHUP", "SIGBREAK"):
            number = getattr(signal, name, None)
            if number is not None:
                old = signal.getsignal(number)
                # Preserve nohup/inherited ignores and handlers Python cannot restore.
                if old == signal.SIG_IGN or old is None:
                    continue
                signal.signal(number, lambda *_: cancel.set())
                previous[number] = old
        record, _ = run_dry_run(config, Path(args.output_dir), cancel)
        print(json.dumps({key: record[key] for key in ("run_id", "status", "reason_code", "evidence_label")}))
        return {"PASS": 0, "PREFLIGHT_FAILED": 3, "CANCELLED": 130, "TIMEOUT": 124}.get(record["status"], 1)
    except OSError:
        print(json.dumps({"status": "FAIL", "reason_code": "ARTIFACT_WRITE_FAILED"}))
        return 1
    except ValueError:
        print(json.dumps({"status": "FAIL", "reason_code": "INTERNAL_ERROR"}))
        return 1
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


def main(argv=None):
    try:
        return _main(argv)
    except Exception:
        # Last-resort boundary: no exception text or malformed input in CLI output.
        print(json.dumps({"status": "FAIL", "reason_code": "INTERNAL_ERROR"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

```

## task004/client.py

SHA-256: `c6a84a93bf95dc336bbc27b2d021e4943e2d192ba1b78de4d91eb7a9062567bc`

```python
"""Bounded synthetic request, with total deadline and cancellation."""
import http.client
import json
import queue
import socket
import threading
import time
from urllib.parse import urlsplit


class ClientError(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def request_synthetic(url, config, cancel_event=None):
    parsed = urlsplit(url)
    if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or
            parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
        raise ClientError("NON_LOOPBACK_ENDPOINT")
    try:
        port = parsed.port
    except ValueError:
        raise ClientError("NON_LOOPBACK_ENDPOINT") from None
    if not port:
        raise ClientError("NON_LOOPBACK_ENDPOINT")
    if cancel_event is not None and cancel_event.is_set():
        raise ClientError("CANCELLED")
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=config.timeout_s)
    results = queue.Queue(maxsize=1)
    closing = threading.Event()
    connected_socket = [None]
    body = json.dumps({"prompt": "SYNTHETIC_INPUT", "max_tokens": config.max_new_tokens,
                       "temperature": 0, "seed": 1729, "n": 1, "thinking": False}).encode()

    def perform():
        response = None
        try:
            conn.connect()
            connected_socket[0] = conn.sock
            if closing.is_set():
                raise ClientError("CANCELLED")
            conn.request("POST", "/v1/completions", body, {"Content-Type": "application/json"})
            response = conn.getresponse()
            if response.status != 200:
                raise ClientError("HTTP_ERROR")
            data = response.read(65537)
            if len(data) > 65536:
                raise ClientError("RESPONSE_TOO_LARGE")
            try:
                parsed_body = json.loads(data)
            except (ValueError, UnicodeError):
                raise ClientError("INVALID_JSON") from None
            # A synthetic fixture must never be accepted as a model result.
            expected = {"id": "synthetic", "choices": [{"text": "SYNTHETIC_OK"}],
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                        "evidence_label": "SYNTHETIC"}
            if parsed_body != expected:
                raise ClientError("INVALID_RESPONSE")
            results.put(None)
        except ClientError as exc:
            results.put(exc)
        except (TimeoutError, socket.timeout):
            results.put(ClientError("TIMEOUT"))
        except (OSError, http.client.HTTPException):
            results.put(ClientError("CONNECTION_ERROR"))
        except Exception:
            results.put(ClientError("CLIENT_ERROR"))
        finally:
            if response is not None:
                response.close()
            conn.close()

    start = time.monotonic()
    worker = threading.Thread(target=perform, daemon=True, name="task004-http")
    worker.start()
    primary = None
    try:
        while True:
            if cancel_event is not None and cancel_event.is_set():
                raise ClientError("CANCELLED")
            remaining = config.timeout_s - (time.monotonic() - start)
            if remaining <= 0:
                raise ClientError("TIMEOUT")
            try:
                error = results.get(timeout=min(.02, remaining))
            except queue.Empty:
                continue
            if error is not None:
                raise error
            return {"request_latency_s": time.monotonic() - start, "synthetic_output_tokens": 1}
    except BaseException as exc:
        primary = exc
        raise
    finally:
        closing.set()
        sock = connected_socket[0]
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        worker.join(timeout=.5)
        if worker.is_alive() and primary is None:
            raise ClientError("CLIENT_CLEANUP_FAILED")

```

## task004/config.py

SHA-256: `431ae1d477dda327481f6b725afb9732c8c784bceaf449005269667bd83ee595`

```python
"""Strict configuration for the synthetic-only TASK-004 harness."""

from dataclasses import asdict, dataclass, fields
import json
import math
from pathlib import Path


MAX_TIMEOUT_S = 3600
MAX_SAMPLE_INTERVAL_S = 60


class ConfigError(ValueError):
    """Configuration is invalid; messages never include supplied values."""


def _integer(name, value, minimum, maximum=None):
    if type(value) is not int or value < minimum:
        raise ConfigError(f"{name} must be an integer >= {minimum}")
    if maximum is not None and value > maximum:
        raise ConfigError(f"{name} must be <= {maximum}")


def _number(name, value, minimum, inclusive=False, maximum=None):
    if type(value) not in (int, float):
        raise ConfigError(f"{name} must be a finite number")
    try:
        valid = math.isfinite(value)
    except (OverflowError, TypeError):
        valid = False
    if not valid or (value < minimum if inclusive else value <= minimum):
        relation = ">=" if inclusive else ">"
        raise ConfigError(f"{name} must be finite and {relation} {minimum}")
    if maximum is not None and value > maximum:
        raise ConfigError(f"{name} must be <= {maximum}")


@dataclass(frozen=True)
class Config:
    n_ctx: int
    runtime: str = "mock"
    thinking: bool = False
    max_new_tokens: int = 96
    timeout_s: float = 5.0
    startup_timeout_s: float = 5.0
    sample_interval_s: float = 0.05
    min_available_ram_bytes: int = 67_108_864
    min_free_disk_bytes: int = 10_485_760
    image_long_edge_px: int | None = None
    max_image_tokens: int | None = None
    mock_scenario: str = "success"
    mock_delay_s: float = 0.0

    def __post_init__(self):
        if self.runtime != "mock":
            raise ConfigError("runtime must be mock; real model execution is disabled")
        if self.thinking is not False:
            raise ConfigError("thinking must be false")
        _integer("n_ctx", self.n_ctx, 1)
        _integer("max_new_tokens", self.max_new_tokens, 1, 96)
        _number("timeout_s", self.timeout_s, 0, maximum=MAX_TIMEOUT_S)
        _number("startup_timeout_s", self.startup_timeout_s, 0, maximum=MAX_TIMEOUT_S)
        _number("sample_interval_s", self.sample_interval_s, 0.01, inclusive=True,
                maximum=MAX_SAMPLE_INTERVAL_S)
        _integer("min_available_ram_bytes", self.min_available_ram_bytes, 0)
        _integer("min_free_disk_bytes", self.min_free_disk_bytes, 0)
        _number("mock_delay_s", self.mock_delay_s, 0, inclusive=True, maximum=MAX_TIMEOUT_S)
        if (self.image_long_edge_px is None) != (self.max_image_tokens is None):
            raise ConfigError("image_long_edge_px and max_image_tokens must be set together")
        if self.image_long_edge_px is not None:
            _integer("image_long_edge_px", self.image_long_edge_px, 1, 768)
            _integer("max_image_tokens", self.max_image_tokens, 1)
        if self.mock_scenario not in (
            "success", "malformed_json", "http_error", "disconnect", "slow", "health_failure"
        ):
            raise ConfigError("unsupported mock_scenario")

    def to_dict(self):
        return asdict(self)


def parse_config(data):
    """Validate even programmatically constructed configs; no coercion/default context."""
    if not isinstance(data, dict):
        raise ConfigError("configuration must be a JSON object")
    allowed = {field.name for field in fields(Config)}
    if any(key not in allowed for key in data):
        raise ConfigError("unknown configuration keys")
    if "n_ctx" not in data:
        raise ConfigError("n_ctx is required")
    return Config(**data)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError("duplicate JSON object keys")
        result[key] = value
    return result


def _invalid_constant(_value):
    raise ConfigError("nonfinite JSON numbers are not permitted")


def load_config(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
    except ConfigError:
        raise
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        raise ConfigError("configuration could not be read as UTF-8 JSON") from error
    return parse_config(data)

```

## task004/interfaces.py

SHA-256: `dcb15b6d9e1fb1975a80aed9b9543ab1a79e38909c580c75c4963179ca42d5a4`

```python
"""Future interfaces only: no dataset, model adapter or KL implementation."""
from typing import Protocol


class PilotProvider(Protocol):
    def load_p60(self):
        """Future licensed/provenanced 40 Vietnamese + 20 English MCQs."""
        ...


class TopKLogprobProvider(Protocol):
    def top_k(self, token_ids: list[int], k: int):
        """Future token/logprob samples; not full-vocabulary KL."""
        ...


def real_model_adapter(*args, **kwargs):
    raise NotImplementedError("REAL_MODEL_EXECUTION_DISABLED")

```

## task004/mock_server.py

SHA-256: `aeae9bfde6a87319ea0151e281c073c3b2798c99f657e801622ba85545d0744c`

```python
"""Loopback-only, synthetic HTTP fixture; invoked by ManagedMockServer."""
import argparse
import json
import math
import os
import shutil
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import psutil


def _remove_scratch(scratch_dir):
    # Only the private directory convention created by ManagedMockServer is eligible.
    # Never follow a replacement directory symlink or delete an arbitrary port parent.
    scratch_dir = Path(scratch_dir)
    if scratch_dir.name.startswith("task004-mock-") and not scratch_dir.is_symlink():
        shutil.rmtree(scratch_dir, ignore_errors=True)


def _exit_with_parent(parent, max_lifetime_s, scratch_dir):
    deadline = time.monotonic() + max_lifetime_s
    while True:
        time.sleep(.25)
        try:
            gone = not parent.is_running() or parent.status() == psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            gone = True
        except psutil.Error:
            gone = False
        if gone or time.monotonic() >= deadline:
            if gone:
                _remove_scratch(scratch_dir)
            os._exit(3)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, body):
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if self.path != "/health":
            self.reply(404, b'{}')
        elif self.server.scenario == "health_failure":
            self.reply(503, b'{"status":"unavailable"}')
        else:
            self.reply(200, b'{"status":"ok"}')

    def do_POST(self):
        if self.path != "/v1/completions":
            self.reply(404, b'{}')
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 4096:
                raise ValueError
            self.connection.settimeout(1)
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict) or payload.get("prompt") != "SYNTHETIC_INPUT":
                raise ValueError
        except (ValueError, OSError):
            self.reply(400, b'{}')
            return
        scenario = self.server.scenario
        if scenario == "disconnect":
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        if scenario == "slow" or self.server.delay_s:
            time.sleep(max(self.server.delay_s, 2 if scenario == "slow" else 0))
        if scenario == "malformed_json":
            self.reply(200, b'{invalid')
        elif scenario == "http_error":
            self.reply(500, b'{"error":"synthetic_error"}')
        else:
            self.reply(200, json.dumps({
                "id": "synthetic", "choices": [{"text": "SYNTHETIC_OK"}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "evidence_label": "SYNTHETIC",
            }).encode())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port-file", required=True)
    parser.add_argument("--scenario", choices=("success", "malformed_json", "http_error", "disconnect", "slow", "health_failure"), default="success")
    parser.add_argument("--delay", type=float, default=0)
    parser.add_argument("--parent-pid", required=True, type=int)
    parser.add_argument("--max-lifetime-s", type=float, default=3600.0)
    args = parser.parse_args()
    if not math.isfinite(args.max_lifetime_s) or args.max_lifetime_s <= 0:
        parser.error("max lifetime must be positive and finite")
    scratch_dir = Path(args.port_file).parent
    try:
        parent = psutil.Process(args.parent_pid)
    except psutil.Error:
        _remove_scratch(scratch_dir)
        os._exit(3)
    threading.Thread(target=_exit_with_parent, daemon=True,
                     args=(parent, args.max_lifetime_s, scratch_dir)).start()
    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        server.daemon_threads = True
        server.scenario = args.scenario
        server.delay_s = args.delay
        Path(args.port_file).write_text(str(server.server_port), encoding="ascii")
        server.serve_forever(poll_interval=0.05)


if __name__ == "__main__":
    main()

```

## task004/preflight.py

SHA-256: `c4c8ae7eda54785d3e74804ca9478d76746d9c132f3e9c579ea3c6f45f9439c0`

```python
"""Read-only host checks. These observations describe this host, not a laptop."""

import ctypes
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import shutil

import psutil

from .config import Config


def windows_system_commit():
    """Return Windows system commit, never substitute RSS, VMS or swap on Linux."""
    result = {
        "total_bytes": None,
        "limit_bytes": None,
        "available_bytes": None,
        "source": "GetPerformanceInfo" if os.name == "nt" else None,
        "unavailable_reason": None,
    }
    if os.name != "nt":
        result["unavailable_reason"] = "WINDOWS_ONLY"
        return result

    from ctypes import wintypes

    class PerformanceInformation(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("CommitTotal", ctypes.c_size_t),
            ("CommitLimit", ctypes.c_size_t),
            ("CommitPeak", ctypes.c_size_t),
            ("PhysicalTotal", ctypes.c_size_t),
            ("PhysicalAvailable", ctypes.c_size_t),
            ("SystemCache", ctypes.c_size_t),
            ("KernelTotal", ctypes.c_size_t),
            ("KernelPaged", ctypes.c_size_t),
            ("KernelNonpaged", ctypes.c_size_t),
            ("PageSize", ctypes.c_size_t),
            ("HandleCount", wintypes.DWORD),
            ("ProcessCount", wintypes.DWORD),
            ("ThreadCount", wintypes.DWORD),
        ]

    try:
        api = ctypes.WinDLL("psapi", use_last_error=True).GetPerformanceInfo
        api.argtypes = [ctypes.POINTER(PerformanceInformation), wintypes.DWORD]
        api.restype = wintypes.BOOL
        info = PerformanceInformation()
        info.cb = ctypes.sizeof(info)
        if not api(ctypes.byref(info), info.cb) or not info.PageSize:
            result["unavailable_reason"] = "GET_PERFORMANCE_INFO_FAILED"
            return result
        result["total_bytes"] = info.CommitTotal * info.PageSize
        result["limit_bytes"] = info.CommitLimit * info.PageSize
        result["available_bytes"] = max(0, result["limit_bytes"] - result["total_bytes"])
    except (OSError, AttributeError):
        result["unavailable_reason"] = "GET_PERFORMANCE_INFO_UNAVAILABLE"
    return result


def check_preflight(config: Config, output_dir: Path):
    """Check thresholds inclusively; never create directories or touch outputs."""
    # Frozen config has already enforced the mock-only contract.
    checks = []
    available_ram = None
    free_disk = None
    try:
        available_ram = psutil.virtual_memory().available
        checks.append({
            "name": "available_ram", "passed": available_ram >= config.min_available_ram_bytes,
            "measured_bytes": available_ram, "required_bytes": config.min_available_ram_bytes,
            "source": "psutil.virtual_memory.available", "unavailable_reason": None,
        })
    except (OSError, psutil.Error):
        checks.append({"name": "available_ram", "passed": False,
                       "measured_bytes": None, "required_bytes": config.min_available_ram_bytes,
                       "source": "psutil.virtual_memory.available", "unavailable_reason": "RAM_READ_FAILED"})

    try:
        target = Path(output_dir).absolute()
        ancestor = target
        while not ancestor.exists() and ancestor != ancestor.parent:
            ancestor = ancestor.parent
        output_is_directory = ancestor.is_dir()
        checks.append({"name": "output_path", "passed": output_is_directory})
        # A pre-existing file is not accepted as an output directory or ancestor.
        if output_is_directory:
            free_disk = shutil.disk_usage(ancestor).free
        checks.append({
            "name": "free_disk", "passed": free_disk is not None and free_disk >= config.min_free_disk_bytes,
            "measured_bytes": free_disk, "required_bytes": config.min_free_disk_bytes,
            "source": "shutil.disk_usage.free",
            "unavailable_reason": None if free_disk is not None else "OUTPUT_PATH_NOT_DIRECTORY",
        })
    except OSError:
        checks.append({"name": "free_disk", "passed": False,
                       "measured_bytes": None, "required_bytes": config.min_free_disk_bytes,
                       "source": "shutil.disk_usage.free", "unavailable_reason": "DISK_READ_FAILED"})

    return {
        "ready": all(check["passed"] for check in checks),
        "checks": checks,
        "available_ram_bytes": available_ram,
        "free_disk_bytes": free_disk,
        "system_commit": windows_system_commit(),
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.system(),
        "measurement_scope": "CURRENT_HOST",
    }

```

## task004/record.py

SHA-256: `d855732e0c87c62bee74cc37f7f2ef095eabe854745432a0c90150ade4bc22cd`

```python
"""Versioned synthetic artifacts; persist only explicitly selected fields."""
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import uuid

import psutil

from .config import parse_config
from .schema import validate_artifact


STATUS_REASONS = {
    "PASS": {"OK"},
    "FAIL": {"HTTP_ERROR", "INVALID_JSON", "INVALID_RESPONSE", "CONNECTION_ERROR",
             "RESPONSE_TOO_LARGE", "CLIENT_ERROR", "SERVER_ERROR", "SERVER_EXITED",
             "INTERNAL_ERROR", "CLEANUP_FAILED", "MEMORY_SAMPLING_FAILED", "CLIENT_CLEANUP_FAILED",
             "NON_LOOPBACK_ENDPOINT", "SERVER_NOT_STARTED", "SERVER_ALREADY_STARTED"},
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
    if record["status"] == "PASS":
        resources = record["resources"]
        if (resources is None or type(resources["samples"]) is not int or resources["samples"] <= 0
                or type(resources["rss_peak_bytes"]) is not int or resources["rss_peak_bytes"] <= 0):
            raise ValueError("PASS_REQUIRES_RESOURCE_EVIDENCE")


def _validate_provenance_index(index):
    """Malformed metadata is a safe ValueError, never a KeyError/TypeError leak."""
    if (type(index) is not dict or set(index) - {"scope", "sources"}
            or "sources" not in index or type(index["sources"]) is not list
            or ("scope" in index and type(index["scope"]) is not str)):
        raise ValueError("INVALID_PROVENANCE_INDEX")
    names = set()
    for item in index["sources"]:
        if type(item) is not dict or set(item) != {"file", "bytes", "sha256"}:
            raise ValueError("INVALID_PROVENANCE_ENTRY")
        name = item["file"]
        if (type(name) is not str or not name or name in (".", "..")
                or any(char in name for char in ("/", "\\", ":", "\x00"))
                or Path(name).name != name or name in names):
            raise ValueError("INVALID_PROVENANCE_PATH")
        if (type(item["bytes"]) is not int or item["bytes"] < 0
                or type(item["sha256"]) is not str
                or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None):
            raise ValueError("INVALID_PROVENANCE_ENTRY")
        names.add(name)


def source_provenance():
    root = Path(__file__).parent / "references"
    index_path = root / "provenance.json"
    if not index_path.exists():
        return {"status": "UNVERIFIED", "sources": []}
    index = json.loads(index_path.read_text(encoding="utf-8"))
    _validate_provenance_index(index)
    result = []
    for item in index["sources"]:
        name = item["file"]
        path = root / name
        if path.is_symlink():
            raise ValueError("INVALID_PROVENANCE_PATH")
        actual = sha256(path.read_bytes()) if path.is_file() else None
        result.append({"file": name, "expected_sha256": item["sha256"], "actual_sha256": actual,
                       "integrity": "MATCH" if actual == item["sha256"] else "UNVERIFIED"})
    return {"status": "MATCH" if all(x["integrity"] == "MATCH" for x in result) and result else "UNVERIFIED",
            "sources": result}


def _write_synced(path, data):
    with path.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def write_artifacts(output_dir, config, record, preflight):
    validate_record(record)
    safe_config = parse_config(config.to_dict()).to_dict()
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
    manifest_bytes = encoded(manifest)
    root = Path(output_dir)
    run_dir = root / record["run_id"]
    staging = root / f".{record['run_id']}.tmp"
    root.mkdir(parents=True, exist_ok=True)
    if run_dir.exists() or run_dir.is_symlink():
        raise FileExistsError(record["run_id"])
    staging.mkdir()
    try:
        _write_synced(staging / "runs.jsonl", jsonl)
        _write_synced(staging / "manifest.json", manifest_bytes)
        os.rename(staging, run_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return run_dir

```

## task004/sampler.py

SHA-256: `d381b082c355fd3dc8124b9a01293e95eff234a35b34bdb9344c9b8250beeaff`

```python
"""Sample simultaneous process-tree memory; unavailable commit is never VMS."""
import threading

import psutil


class ResourceSampler:
    def __init__(self, pid, interval_s=.1):
        self.process = psutil.Process(pid)
        self.interval_s = interval_s
        self.rss_peak_bytes = None
        self.commit_peak_bytes = None
        self.samples = 0
        self.incomplete_samples = 0
        self._stop = threading.Event()
        self._thread = None

    def sample(self):
        try:
            tree = [self.process] + self.process.children(recursive=True)
            infos = [p.memory_info() for p in tree]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.incomplete_samples += 1
            return
        rss = sum(m.rss for m in infos)
        self.rss_peak_bytes = max(self.rss_peak_bytes or 0, rss)
        if all(hasattr(m, "private") for m in infos):
            commit = sum(m.private for m in infos)
            self.commit_peak_bytes = max(self.commit_peak_bytes or 0, commit)
        self.samples += 1

    def _run(self):
        while not self._stop.wait(self.interval_s):
            self.sample()

    def start(self):
        self.sample()
        self._thread = threading.Thread(target=self._run, daemon=True, name="task004-sampler")
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1)
        self.sample()

    def metrics(self):
        if self.commit_peak_bytes is not None:
            commit_unavailable_reason = None
        elif self.samples == 0:
            commit_unavailable_reason = "No valid process memory samples"
        else:
            commit_unavailable_reason = "Windows private bytes unavailable on this platform"
        return {
            "rss_peak_bytes": self.rss_peak_bytes,
            "commit_peak_bytes": self.commit_peak_bytes,
            "rss_source": "psutil simultaneous process-tree RSS samples",
            "commit_source": "psutil Windows private bytes" if self.commit_peak_bytes is not None else None,
            "commit_unavailable_reason": commit_unavailable_reason,
            "sample_interval_s": self.interval_s, "samples": self.samples,
            "incomplete_samples": self.incomplete_samples,
            "measurement_scope": "mock server and descendants after health readiness; excludes harness and startup",
            "sampling_limitation": "Sampling can miss peaks between observations",
        }

```

## task004/schema.py

SHA-256: `e2ac7a601981169ee8aac26fc0118a1a3e2d2148e461408f08ef4112e66f8d2f`

```python
"""Validate the small JSON Schema keyword subset used by our bundled schemas.

No remote references, coercion, optional packages or network resolution.
"""
import json
import math
from pathlib import Path
import re


ANNOTATIONS = {"$schema", "title", "description"}
KEYWORDS = {"const", "enum", "type", "required", "properties", "additionalProperties",
            "items", "pattern", "minimum", "maximum", "exclusiveMinimum"}
TYPES = {"null", "object", "array", "string", "boolean", "integer", "number"}


def check_schema(schema):
    """Reject unsupported or malformed contracts instead of silently ignoring them."""
    if type(schema) is not dict:
        raise ValueError("SCHEMA_DEFINITION_INVALID")
    if set(schema) - KEYWORDS - ANNOTATIONS:
        raise ValueError("SCHEMA_UNSUPPORTED_KEYWORD")
    kinds = schema.get("type", [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    if (type(kinds) is not list or any(type(kind) is not str or kind not in TYPES for kind in kinds)
            or ("type" in schema and not kinds)):
        raise ValueError("SCHEMA_DEFINITION_INVALID")
    if "enum" in schema and (type(schema["enum"]) is not list or not schema["enum"]):
        raise ValueError("SCHEMA_DEFINITION_INVALID")
    required = schema.get("required", [])
    if type(required) is not list or any(type(key) is not str for key in required):
        raise ValueError("SCHEMA_DEFINITION_INVALID")
    if "additionalProperties" in schema and type(schema["additionalProperties"]) is not bool:
        raise ValueError("SCHEMA_DEFINITION_INVALID")
    for bound in ("minimum", "maximum", "exclusiveMinimum"):
        if bound in schema:
            value = schema[bound]
            if not (type(value) is int or (type(value) is float and math.isfinite(value))):
                raise ValueError("SCHEMA_DEFINITION_INVALID")
    if "pattern" in schema:
        try:
            if type(schema["pattern"]) is not str:
                raise ValueError("SCHEMA_DEFINITION_INVALID")
            re.compile(schema["pattern"])
        except re.error:
            raise ValueError("SCHEMA_DEFINITION_INVALID") from None
    properties = schema.get("properties", {})
    if type(properties) is not dict or any(type(key) is not str for key in properties):
        raise ValueError("SCHEMA_DEFINITION_INVALID")
    for child in properties.values():
        check_schema(child)
    if "items" in schema:
        check_schema(schema["items"])


def validate(value, schema):
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        raise ValueError("SCHEMA_CONST")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError("SCHEMA_ENUM")
    kinds = schema.get("type", [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    checks = {"null": value is None, "object": type(value) is dict, "array": type(value) is list,
              "string": type(value) is str, "boolean": type(value) is bool,
              "integer": type(value) is int,
              "number": type(value) is int or (type(value) is float and math.isfinite(value))}
    if kinds and not any(checks[kind] for kind in kinds):
        raise ValueError("SCHEMA_TYPE")
    if type(value) is dict:
        if not set(schema.get("required", [])).issubset(value):
            raise ValueError("SCHEMA_REQUIRED")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            raise ValueError("SCHEMA_UNKNOWN_FIELD")
        for key, child in value.items():
            if key in properties:
                validate(child, properties[key])
    if type(value) is list:
        for item in value:
            validate(item, schema.get("items", {}))
    if type(value) is str and "pattern" in schema and not re.fullmatch(schema["pattern"], value):
        raise ValueError("SCHEMA_PATTERN")
    if type(value) in (int, float):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError("SCHEMA_MINIMUM")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValueError("SCHEMA_MAXIMUM")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            raise ValueError("SCHEMA_EXCLUSIVE_MINIMUM")


def validate_artifact(value, name):
    if name not in ("run", "manifest"):
        raise ValueError("SCHEMA_NAME")
    schema = json.loads((Path(__file__).parent / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
    check_schema(schema)
    validate(value, schema)

```

## task004/server.py

SHA-256: `237cdc8a3276434b86d74c3da4b5de178610e5a5f22e69506750b29b8e41bbf9`

```python
"""Own and reliably stop a fixed mock subprocess and its descendants."""
import http.client
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import psutil


class ServerError(RuntimeError):
    def __init__(self, code="SERVER_ERROR"):
        self.code = code
        super().__init__(code)


class ServerTimeout(ServerError):
    def __init__(self):
        super().__init__("STARTUP_TIMEOUT")


def _child_env():
    """The fixed mock needs locale/temp/platform paths, never harness secrets."""
    return {key: os.environ[key] for key in
            ("PATH", "SYSTEMROOT", "TEMP", "TMP", "LANG", "LC_ALL") if key in os.environ}


def _active(process):
    try:
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False


def _active_group_members(pgid):
    """Only inspect identities/status in an explicitly owned POSIX session group."""
    members = []
    for process in psutil.process_iter():
        try:
            if os.getpgid(process.pid) == pgid and _active(process):
                members.append(process)
        except ProcessLookupError:
            pass
    return members


def _wait_group(pgid, timeout):
    deadline = time.monotonic() + timeout
    while _active_group_members(pgid):
        if time.monotonic() >= deadline:
            return False
        time.sleep(.01)
    return True


def _signal_group(pgid, sig):
    try:
        os.killpg(pgid, sig)
    except ProcessLookupError:
        pass


def stop_owned_process(process, *, owned_pgid=None):
    """Stop an owned Popen. Group cleanup requires explicit new-session ownership.

    ``owned_pgid`` is only supplied for a Popen created with start_new_session=True.
    It must equal that Popen's original PID. The private session prevents unrelated
    processes joining its group; ownership is retained after the leader exits.
    Windows and callers without this ownership use the live psutil process tree.
    """
    if process is None:
        return
    try:
        if owned_pgid is not None:
            if os.name != "posix" or type(owned_pgid) is not int or owned_pgid != process.pid:
                raise ServerError("CLEANUP_FAILED")
            if getattr(process, "_task004_cleaned_pgid", None) == owned_pgid:
                return
            # A still-living root must actually lead the session/group we own.
            if process.poll() is None:
                try:
                    if os.getpgid(process.pid) != owned_pgid or os.getsid(process.pid) != owned_pgid:
                        raise ServerError("CLEANUP_FAILED")
                except ProcessLookupError:
                    pass
            if _active_group_members(owned_pgid):
                _signal_group(owned_pgid, signal.SIGTERM)
                if not _wait_group(owned_pgid, 1):
                    _signal_group(owned_pgid, signal.SIGKILL)
                    if not _wait_group(owned_pgid, 1):
                        raise ServerError("CLEANUP_FAILED")
        else:
            targets = []
            if process.poll() is None:
                try:
                    parent = psutil.Process(process.pid)
                    targets = parent.children(recursive=True) + [parent]
                except psutil.NoSuchProcess:
                    pass
            for target in targets:
                try:
                    target.terminate()
                except psutil.NoSuchProcess:
                    pass
            _, alive = psutil.wait_procs(targets, timeout=1)
            for target in alive:
                try:
                    if _active(target):
                        target.kill()
                except psutil.NoSuchProcess:
                    pass
            _, alive = psutil.wait_procs(alive, timeout=1)
            if any(_active(target) for target in alive):
                raise ServerError("CLEANUP_FAILED")
        process.wait(timeout=1)
        if owned_pgid is not None:
            # Idempotency must not signal a later process group reusing this number.
            process._task004_cleaned_pgid = owned_pgid
    except (psutil.Error, OSError, subprocess.TimeoutExpired):
        raise ServerError("CLEANUP_FAILED") from None


class ManagedMockServer:
    def __init__(self, config):
        self.config = config
        self.process = None
        self._directory = None
        self._owned_pgid = None
        self.port = None

    @property
    def pid(self):
        return self.process.pid if self.process else None

    @property
    def url(self):
        if self.port is None:
            raise ServerError("SERVER_NOT_STARTED")
        return f"http://127.0.0.1:{self.port}"

    def start(self, cancel_event=None):
        if self.process is not None:
            raise ServerError("SERVER_ALREADY_STARTED")
        self._directory = tempfile.TemporaryDirectory(prefix="task004-mock-")
        port_file = Path(self._directory.name) / "port"
        try:
            self.process = subprocess.Popen([
                sys.executable, "-m", "task004.mock_server", "--port-file", str(port_file),
                "--scenario", self.config.mock_scenario, "--delay", str(self.config.mock_delay_s),
                "--parent-pid", str(os.getpid()),
                "--max-lifetime-s", str(self.config.startup_timeout_s + self.config.timeout_s + 30),
            ], cwd=Path(__file__).resolve().parent.parent, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=os.name == "posix", env=_child_env())
            if os.name == "posix":
                self._owned_pgid = self.process.pid
            deadline = time.monotonic() + self.config.startup_timeout_s
            while time.monotonic() < deadline:
                if cancel_event is not None and cancel_event.is_set():
                    raise ServerError("CANCELLED")
                if self.process.poll() is not None:
                    raise ServerError("SERVER_EXITED")
                try:
                    port = int(port_file.read_text(encoding="ascii"))
                    if not 1 <= port <= 65535:
                        raise ValueError
                    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=min(.1, max(.001, deadline-time.monotonic())))
                    try:
                        conn.request("GET", "/health")
                        response = conn.getresponse()
                        data = response.read(1025)
                        if response.status == 200 and json.loads(data) == {"status": "ok"}:
                            self.port = port
                            return self
                    finally:
                        conn.close()
                except (OSError, ValueError, http.client.HTTPException):
                    pass
                time.sleep(.01)
            raise ServerTimeout()
        except BaseException:
            self.stop()
            raise

    def stop(self):
        try:
            stop_owned_process(self.process, owned_pgid=self._owned_pgid)
        finally:
            if self._directory is not None:
                self._directory.cleanup()
                self._directory = None

    def __enter__(self):
        return self.start()

    def __exit__(self, *args):
        self.stop()

```

## task004/schemas/manifest.schema.json

SHA-256: `b7bd24d34858c6d9c67fc30146f528bdff1a677ae5a9ff0dbf47b029f8955cc7`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TASK-004 manifest v1",
  "type": "object",
  "properties": {
    "schema_version": {
      "const": 1
    },
    "task_id": {
      "const": "TASK-004"
    },
    "run_id": {
      "type": "string",
      "pattern": "^[0-9a-f]{32}$"
    },
    "evidence_label": {
      "const": "SYNTHETIC"
    },
    "status": {
      "enum": [
        "PASS",
        "FAIL",
        "TIMEOUT",
        "CANCELLED",
        "PREFLIGHT_FAILED"
      ]
    },
    "config": {
      "type": "object",
      "properties": {
        "n_ctx": {
          "type": "integer",
          "minimum": 1
        },
        "runtime": {
          "const": "mock"
        },
        "thinking": {
          "const": false
        },
        "max_new_tokens": {
          "type": "integer",
          "minimum": 1,
          "maximum": 96
        },
        "timeout_s": {
          "type": "number",
          "exclusiveMinimum": 0,
          "maximum": 3600
        },
        "startup_timeout_s": {
          "type": "number",
          "exclusiveMinimum": 0,
          "maximum": 3600
        },
        "sample_interval_s": {
          "type": "number",
          "minimum": 0.01,
          "maximum": 60
        },
        "min_available_ram_bytes": {
          "type": "integer",
          "minimum": 0
        },
        "min_free_disk_bytes": {
          "type": "integer",
          "minimum": 0
        },
        "image_long_edge_px": {
          "type": [
            "integer",
            "null"
          ],
          "minimum": 1,
          "maximum": 768
        },
        "max_image_tokens": {
          "type": [
            "integer",
            "null"
          ],
          "minimum": 1
        },
        "mock_scenario": {
          "enum": [
            "success",
            "malformed_json",
            "http_error",
            "disconnect",
            "slow",
            "health_failure"
          ]
        },
        "mock_delay_s": {
          "type": "number",
          "minimum": 0,
          "maximum": 3600
        }
      },
      "required": [
        "n_ctx",
        "runtime",
        "thinking",
        "max_new_tokens",
        "timeout_s",
        "startup_timeout_s",
        "sample_interval_s",
        "min_available_ram_bytes",
        "min_free_disk_bytes",
        "image_long_edge_px",
        "max_image_tokens",
        "mock_scenario",
        "mock_delay_s"
      ],
      "additionalProperties": false
    },
    "config_sha256": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$"
    },
    "runtime": {
      "type": "object",
      "properties": {
        "kind": {
          "const": "mock"
        },
        "python_version": {
          "type": "string"
        },
        "psutil_version": {
          "type": "string"
        },
        "os": {
          "type": "string"
        },
        "phase_timers_supported": {
          "const": false
        },
        "streaming_supported": {
          "const": false
        }
      },
      "required": [
        "kind",
        "python_version",
        "psutil_version",
        "os",
        "phase_timers_supported",
        "streaming_supported"
      ],
      "additionalProperties": false
    },
    "decoding": {
      "type": "object",
      "properties": {
        "temperature": {
          "const": 0
        },
        "seed": {
          "const": 1729
        },
        "n": {
          "const": 1
        },
        "thinking": {
          "const": false
        }
      },
      "required": [
        "temperature",
        "seed",
        "n",
        "thinking"
      ],
      "additionalProperties": false
    },
    "preflight": {
      "type": "object",
      "properties": {
        "ready": {
          "type": "boolean"
        },
        "checks": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {
                "enum": [
                  "available_ram",
                  "free_disk",
                  "output_path"
                ]
              },
              "passed": {
                "type": "boolean"
              },
              "measured_bytes": {
                "type": [
                  "integer",
                  "null"
                ],
                "minimum": 0
              },
              "required_bytes": {
                "type": "integer",
                "minimum": 0
              },
              "source": {
                "type": "string"
              },
              "unavailable_reason": {
                "type": [
                  "string",
                  "null"
                ]
              }
            },
            "required": [
              "name",
              "passed"
            ],
            "additionalProperties": false
          }
        },
        "available_ram_bytes": {
          "type": [
            "integer",
            "null"
          ],
          "minimum": 0
        },
        "free_disk_bytes": {
          "type": [
            "integer",
            "null"
          ],
          "minimum": 0
        },
        "system_commit": {
          "type": "object",
          "properties": {
            "total_bytes": {
              "type": [
                "integer",
                "null"
              ],
              "minimum": 0
            },
            "limit_bytes": {
              "type": [
                "integer",
                "null"
              ],
              "minimum": 0
            },
            "available_bytes": {
              "type": [
                "integer",
                "null"
              ],
              "minimum": 0
            },
            "source": {
              "type": [
                "string",
                "null"
              ]
            },
            "unavailable_reason": {
              "type": [
                "string",
                "null"
              ]
            }
          },
          "required": [
            "total_bytes",
            "limit_bytes",
            "available_bytes",
            "source",
            "unavailable_reason"
          ],
          "additionalProperties": false
        },
        "observed_at_utc": {
          "type": "string"
        },
        "platform": {
          "type": "string"
        },
        "measurement_scope": {
          "const": "CURRENT_HOST"
        }
      },
      "required": [
        "ready",
        "checks",
        "available_ram_bytes",
        "free_disk_bytes",
        "system_commit",
        "observed_at_utc",
        "platform",
        "measurement_scope"
      ],
      "additionalProperties": false
    },
    "input_provenance": {
      "type": "object",
      "properties": {
        "status": {
          "enum": [
            "MATCH",
            "UNVERIFIED"
          ]
        },
        "sources": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "file": {
                "type": "string"
              },
              "expected_sha256": {
                "type": "string",
                "pattern": "^[0-9a-f]{64}$"
              },
              "actual_sha256": {
                "type": [
                  "string",
                  "null"
                ],
                "pattern": "^[0-9a-f]{64}$"
              },
              "integrity": {
                "enum": [
                  "MATCH",
                  "UNVERIFIED"
                ]
              }
            },
            "required": [
              "file",
              "expected_sha256",
              "actual_sha256",
              "integrity"
            ],
            "additionalProperties": false
          }
        }
      },
      "required": [
        "status",
        "sources"
      ],
      "additionalProperties": false
    },
    "hardware_reference": {
      "type": "null"
    },
    "dataset_manifest_hash": {
      "type": "null"
    },
    "benchmark_status": {
      "const": "NOT_RUN"
    },
    "external_model_api_calls": {
      "const": 0
    },
    "metric_unavailability": {
      "type": "object",
      "properties": {
        "ttft_s": {
          "type": "string"
        },
        "prefill_tokens_s": {
          "type": "string"
        },
        "decode_tokens_s": {
          "type": "string"
        }
      },
      "required": [
        "ttft_s",
        "prefill_tokens_s",
        "decode_tokens_s"
      ],
      "additionalProperties": false
    },
    "results": {
      "type": "object",
      "properties": {
        "file": {
          "const": "runs.jsonl"
        },
        "sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "records": {
          "const": 1
        }
      },
      "required": [
        "file",
        "sha256",
        "records"
      ],
      "additionalProperties": false
    }
  },
  "required": [
    "schema_version",
    "task_id",
    "run_id",
    "evidence_label",
    "status",
    "config",
    "config_sha256",
    "runtime",
    "decoding",
    "preflight",
    "input_provenance",
    "hardware_reference",
    "dataset_manifest_hash",
    "benchmark_status",
    "external_model_api_calls",
    "metric_unavailability",
    "results"
  ],
  "additionalProperties": false
}

```

## task004/schemas/run.schema.json

SHA-256: `424b6dc32dc7a87d47e445acffb5e1d281346c7a27e3926c197b66893b0cb700`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TASK-004 run v1",
  "type": "object",
  "properties": {
    "schema_version": {
      "const": 1
    },
    "task_id": {
      "const": "TASK-004"
    },
    "run_id": {
      "type": "string",
      "pattern": "^[0-9a-f]{32}$"
    },
    "evidence_label": {
      "const": "SYNTHETIC"
    },
    "status": {
      "enum": [
        "PASS",
        "FAIL",
        "TIMEOUT",
        "CANCELLED",
        "PREFLIGHT_FAILED"
      ]
    },
    "reason_code": {
      "type": "string",
      "enum": [
        "CANCELLED",
        "CLEANUP_FAILED",
        "CLIENT_CLEANUP_FAILED",
        "CLIENT_ERROR",
        "CONNECTION_ERROR",
        "HTTP_ERROR",
        "INTERNAL_ERROR",
        "INVALID_JSON",
        "INVALID_RESPONSE",
        "MEMORY_SAMPLING_FAILED",
        "NON_LOOPBACK_ENDPOINT",
        "OK",
        "PREFLIGHT_FAILED",
        "RESPONSE_TOO_LARGE",
        "SERVER_ALREADY_STARTED",
        "SERVER_ERROR",
        "SERVER_EXITED",
        "SERVER_NOT_STARTED",
        "STARTUP_TIMEOUT",
        "TIMEOUT"
      ]
    },
    "started_at_utc": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\\.[0-9]{1,6})?\\+00:00$"
    },
    "finished_at_utc": {
      "type": "string",
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\\.[0-9]{1,6})?\\+00:00$"
    },
    "metrics": {
      "type": "object",
      "properties": {
        "run_elapsed_s": {
          "type": [
            "number",
            "null"
          ],
          "minimum": 0
        },
        "request_latency_s": {
          "type": [
            "number",
            "null"
          ],
          "minimum": 0
        },
        "ttft_s": {
          "type": [
            "number",
            "null"
          ],
          "minimum": 0
        },
        "prefill_tokens_s": {
          "type": [
            "number",
            "null"
          ],
          "minimum": 0
        },
        "decode_tokens_s": {
          "type": [
            "number",
            "null"
          ],
          "minimum": 0
        },
        "synthetic_output_tokens": {
          "type": [
            "integer",
            "null"
          ],
          "minimum": 0
        }
      },
      "required": [
        "run_elapsed_s",
        "request_latency_s",
        "ttft_s",
        "prefill_tokens_s",
        "decode_tokens_s",
        "synthetic_output_tokens"
      ],
      "additionalProperties": false
    },
    "resources": {
      "type": [
        "object",
        "null"
      ],
      "properties": {
        "rss_peak_bytes": {
          "type": [
            "integer",
            "null"
          ],
          "minimum": 0
        },
        "commit_peak_bytes": {
          "type": [
            "integer",
            "null"
          ],
          "minimum": 0
        },
        "rss_source": {
          "type": "string"
        },
        "commit_source": {
          "type": [
            "string",
            "null"
          ]
        },
        "commit_unavailable_reason": {
          "type": [
            "string",
            "null"
          ]
        },
        "sample_interval_s": {
          "type": "number",
          "minimum": 0
        },
        "samples": {
          "type": "integer",
          "minimum": 0
        },
        "incomplete_samples": {
          "type": "integer",
          "minimum": 0
        },
        "measurement_scope": {
          "type": "string"
        },
        "sampling_limitation": {
          "type": "string"
        }
      },
      "required": [
        "rss_peak_bytes",
        "commit_peak_bytes",
        "rss_source",
        "commit_source",
        "commit_unavailable_reason",
        "sample_interval_s",
        "samples",
        "incomplete_samples",
        "measurement_scope",
        "sampling_limitation"
      ],
      "additionalProperties": false
    }
  },
  "required": [
    "schema_version",
    "task_id",
    "run_id",
    "evidence_label",
    "status",
    "reason_code",
    "started_at_utc",
    "finished_at_utc",
    "metrics",
    "resources"
  ],
  "additionalProperties": false
}

```

## task004/tests/__init__.py

SHA-256: `0f47a9863abe5b1695c35105b210435f83247a14a1f5031a29b1f416f39d3f7b`

```python
"""Standard-library unittest suite."""

```

## task004/tests/fixtures.py

SHA-256: `316d5684935de6c0f3cd18e13810efccaf599b1cda8bcaeb12574e9539b103ee`

```python
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

```

## task004/tests/test_client_edges.py

SHA-256: `d34be69ab00f1083aa87e1622e85ad5e74596be811b2ac4a98e4e73ce70b7406`

```python
from contextlib import contextmanager
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
import unittest

from task004.client import ClientError, request_synthetic
from task004.config import Config


@contextmanager
def body_fixture(mode):
    stop = threading.Event()
    headers_sent = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(200)
            self.send_header("Content-Length", "100000" if mode == "oversize" else "1000")
            self.end_headers()
            headers_sent.set()
            try:
                if mode == "oversize":
                    self.wfile.write(b"x" * 100000)
                elif mode == "trickle":
                    while not stop.wait(.01):
                        self.wfile.write(b"x")
                        self.wfile.flush()
                else:
                    stop.wait(3)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.01), daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", headers_sent
    finally:
        stop.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


class ClientEdgeTests(unittest.TestCase):
    def assert_worker_stopped(self):
        self.assertFalse(any(t.name == "task004-http" for t in threading.enumerate()))

    def test_timeout_during_http10_body_read(self):
        for mode in ("stall", "trickle"):
            with self.subTest(mode=mode), body_fixture(mode) as (url, _):
                start = time.monotonic()
                with self.assertRaises(ClientError) as caught:
                    request_synthetic(url, Config(n_ctx=1, timeout_s=.15))
                self.assertEqual(caught.exception.code, "TIMEOUT")
                self.assertLess(time.monotonic() - start, 1)
                self.assert_worker_stopped()

    def test_cancel_during_http10_body_read(self):
        with body_fixture("stall") as (url, headers_sent):
            cancel = threading.Event()
            def cancel_after_headers():
                headers_sent.wait(timeout=1)
                cancel.set()
            trigger = threading.Thread(target=cancel_after_headers)
            trigger.start()
            with self.assertRaises(ClientError) as caught:
                request_synthetic(url, Config(n_ctx=1), cancel)
            trigger.join(timeout=1)
            self.assertEqual(caught.exception.code, "CANCELLED")
            self.assert_worker_stopped()

    def test_response_size_is_bounded(self):
        with body_fixture("oversize") as (url, _):
            with self.assertRaises(ClientError) as caught:
                request_synthetic(url, Config(n_ctx=1))
            self.assertEqual(caught.exception.code, "RESPONSE_TOO_LARGE")
            self.assert_worker_stopped()

```

## task004/tests/test_config_preflight.py

SHA-256: `d53a571b7abbe5af70976be00471fdb7bd845151f09cc6579bf0d42c75fbfcd9`

```python
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from task004.config import Config, ConfigError, load_config, parse_config
from task004.preflight import check_preflight, windows_system_commit


class ConfigTests(unittest.TestCase):
    def test_context_is_required(self):
        with self.assertRaises(ConfigError):
            parse_config({})

    def test_defaults_and_round_trip(self):
        config = parse_config({"n_ctx": 512})
        self.assertEqual(config.runtime, "mock")
        self.assertFalse(config.thinking)
        self.assertEqual(parse_config(config.to_dict()), config)

    def test_direct_constructor_validates(self):
        with self.assertRaises(ConfigError):
            Config(n_ctx=512, runtime="llama.cpp")

    def test_boolean_does_not_count_as_integer(self):
        for key in ("n_ctx", "max_new_tokens", "min_available_ram_bytes", "min_free_disk_bytes"):
            with self.subTest(key=key), self.assertRaises(ConfigError):
                parse_config({"n_ctx": 512, key: True})

    def test_nonpositive_context_rejected(self):
        for value in (0, -1, "512", 1.5, None):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                parse_config({"n_ctx": value})

    def test_non_thinking_enforced(self):
        for value in (True, 0, "false", None):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                parse_config({"n_ctx": 512, "thinking": value})

    def test_token_cap_boundaries(self):
        for value in (1, 95, 96):
            self.assertEqual(parse_config({"n_ctx": 512, "max_new_tokens": value}).max_new_tokens, value)
        for value in (0, 97):
            with self.assertRaises(ConfigError):
                parse_config({"n_ctx": 512, "max_new_tokens": value})

    def test_unknown_keys_and_external_runtime_rejected(self):
        for data in ({"url": "https://example.com"}, {"command": "anything"}, {"runtime": "real"}):
            with self.subTest(data=data), self.assertRaises(ConfigError):
                parse_config({"n_ctx": 512, **data})

    def test_config_must_be_object(self):
        for value in ([], None, True, 1):
            with self.assertRaises(ConfigError):
                parse_config(value)

    def test_timeout_and_interval_validation(self):
        for key in ("timeout_s", "startup_timeout_s", "sample_interval_s"):
            for value in (True, 0, -1, float("nan"), float("inf"), "5", 10 ** 400):
                with self.subTest(key=key, value=str(value)), self.assertRaises(ConfigError):
                    parse_config({"n_ctx": 512, key: value})
        with self.assertRaises(ConfigError):
            parse_config({"n_ctx": 512, "sample_interval_s": 0.009})
        self.assertEqual(Config(n_ctx=512, sample_interval_s=0.01).sample_interval_s, 0.01)

    def test_resource_thresholds_must_be_nonnegative(self):
        for key in ("min_available_ram_bytes", "min_free_disk_bytes"):
            self.assertEqual(getattr(parse_config({"n_ctx": 512, key: 0}), key), 0)
            with self.assertRaises(ConfigError):
                parse_config({"n_ctx": 512, key: -1})

    def test_image_requires_explicit_token_budget(self):
        for data in ({"image_long_edge_px": 768}, {"max_image_tokens": 64}):
            with self.assertRaises(ConfigError):
                parse_config({"n_ctx": 512, **data})

    def test_image_dimension_boundaries(self):
        for size in (1, 767, 768):
            config = Config(n_ctx=512, image_long_edge_px=size, max_image_tokens=64)
            self.assertEqual(config.image_long_edge_px, size)
        for size in (0, 769, 1024, True):
            with self.assertRaises(ConfigError):
                Config(n_ctx=512, image_long_edge_px=size, max_image_tokens=64)
        for tokens in (0, -1, True):
            with self.assertRaises(ConfigError):
                Config(n_ctx=512, image_long_edge_px=768, max_image_tokens=tokens)

    def test_mock_scenario_and_delay(self):
        self.assertEqual(Config(n_ctx=1, mock_scenario="slow", mock_delay_s=0).mock_delay_s, 0)
        for value in (-1, True, float("nan")):
            with self.assertRaises(ConfigError):
                Config(n_ctx=1, mock_delay_s=value)
        with self.assertRaises(ConfigError):
            Config(n_ctx=1, mock_scenario="arbitrary-command")

    def test_json_load_and_reject_duplicate_or_nonfinite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"n_ctx": 512}), encoding="utf-8")
            self.assertEqual(load_config(path).n_ctx, 512)
            for text in ('{"n_ctx":1,"n_ctx":2}', '{"n_ctx":NaN}', '{"n_ctx":Infinity}', '{broken'):
                path.write_text(text, encoding="utf-8")
                with self.subTest(text=text), self.assertRaises(ConfigError):
                    load_config(path)

    def test_invalid_utf8_and_missing_file_are_safe_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            with self.assertRaises(ConfigError):
                load_config(path)
            path.write_bytes(b"\xff")
            with self.assertRaises(ConfigError):
                load_config(path)

    def test_integer_over_python_digit_limit_is_config_error(self):
        import sys

        limit = sys.get_int_max_str_digits()
        if not limit:
            self.skipTest("interpreter integer digit limit is disabled")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"n_ctx":' + ('9' * (limit + 1)) + '}', encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(path)


class PreflightTests(unittest.TestCase):
    def measure(self, ram, disk, directory):
        config = Config(n_ctx=512, min_available_ram_bytes=100, min_free_disk_bytes=200)
        with patch("task004.preflight.psutil.virtual_memory", return_value=SimpleNamespace(available=ram)), \
             patch("task004.preflight.shutil.disk_usage", return_value=SimpleNamespace(free=disk)):
            return check_preflight(config, Path(directory))

    def test_ram_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(self.measure(99, 200, directory)["ready"])
            self.assertTrue(self.measure(100, 200, directory)["ready"])
            self.assertTrue(self.measure(101, 200, directory)["ready"])

    def test_disk_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(self.measure(100, 199, directory)["ready"])
            self.assertTrue(self.measure(100, 200, directory)["ready"])
            self.assertTrue(self.measure(100, 201, directory)["ready"])

    def test_nested_missing_directory_uses_ancestor_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "nested" / "output"
            self.assertTrue(self.measure(100, 200, target)["ready"])
            self.assertFalse(target.parent.exists())

    def test_existing_file_blocks_output(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "output"
            target.write_text("user data")
            self.assertFalse(self.measure(100, 200, target)["ready"])
            self.assertFalse(self.measure(100, 200, target / "child")["ready"])
            self.assertEqual(target.read_text(), "user data")

    def test_ram_failure_is_not_zero_or_success(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch("task004.preflight.psutil.virtual_memory", side_effect=OSError("sensitive content")):
            report = check_preflight(Config(n_ctx=1), Path(directory))
            self.assertFalse(report["ready"])
            self.assertIsNone(report["available_ram_bytes"])
            self.assertNotIn("sensitive content", json.dumps(report))

    def test_disk_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch("task004.preflight.shutil.disk_usage", side_effect=OSError("sensitive content")):
            report = check_preflight(Config(n_ctx=1), Path(directory))
            self.assertFalse(report["ready"])
            self.assertIsNone(report["free_disk_bytes"])
            self.assertNotIn("sensitive content", json.dumps(report))

    def test_linux_commit_is_explicitly_unavailable(self):
        with patch("task004.preflight.os.name", "posix"):
            result = windows_system_commit()
        self.assertIsNone(result["total_bytes"])
        self.assertIsNone(result["limit_bytes"])
        self.assertIsNone(result["available_bytes"])
        self.assertEqual(result["unavailable_reason"], "WINDOWS_ONLY")

    def test_report_identifies_host_and_measurement_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.measure(100, 200, directory)
        self.assertEqual(result["measurement_scope"], "CURRENT_HOST")
        self.assertEqual(result["available_ram_bytes"], 100)
        self.assertEqual(result["free_disk_bytes"], 200)
        self.assertTrue(result["observed_at_utc"].endswith("+00:00"))


if __name__ == "__main__":
    unittest.main()

```

## task004/tests/test_hardening_client.py

SHA-256: `ee885e408c56f331cd93f03afd8fb200b852f72e47bdc9857ce768dc8a6c2553`

```python
"""B1 primary error retention, A5 guard is in test_workflow, B4 metric reasons."""
import errno
import os
import select
import socket
import sys
import threading
import time
import unittest
from unittest.mock import patch

from task004.client import ClientError, request_synthetic
from task004.config import Config
from task004.sampler import ResourceSampler


class ClientHardeningTests(unittest.TestCase):
    def assert_http_workers_stopped(self):
        deadline = time.monotonic() + 2
        while any(thread.name == "task004-http" for thread in threading.enumerate()):
            if time.monotonic() >= deadline:
                self.fail("request worker did not stop after fixture cleanup")
            time.sleep(.01)

    def blocked_connection(self):
        release = threading.Event()
        entered = threading.Event()

        class Connection:
            sock = None

            def __init__(self, *args, **kwargs):
                pass

            def connect(self):
                entered.set()
                release.wait(timeout=3)

            def close(self):
                pass

        return Connection, release, entered

    def test_cancel_keeps_primary_when_connect_cleanup_stalls(self):
        connection, release, entered = self.blocked_connection()
        cancel = threading.Event()
        def trigger():
            entered.wait(timeout=1)
            cancel.set()
        trigger_thread = threading.Thread(target=trigger)
        trigger_thread.start()
        try:
            with patch("task004.client.http.client.HTTPConnection", connection):
                with self.assertRaises(ClientError) as caught:
                    request_synthetic("http://127.0.0.1:1234", Config(n_ctx=1), cancel)
                self.assertEqual(caught.exception.code, "CANCELLED")
        finally:
            release.set()
            trigger_thread.join(timeout=2)
            self.assert_http_workers_stopped()

    def test_keyboard_interrupt_keeps_primary_when_cleanup_stalls(self):
        connection, release, _ = self.blocked_connection()
        try:
            with patch("task004.client.http.client.HTTPConnection", connection), \
                    patch("task004.client.queue.Queue.get", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    request_synthetic("http://127.0.0.1:1234", Config(n_ctx=1))
        finally:
            release.set()
            self.assert_http_workers_stopped()

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux backlog behavior only")
    def test_cancel_keeps_primary_for_real_blocked_connect(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(0)
        fillers = []
        cancel = threading.Event()
        timer = None
        try:
            for _ in range(6):
                filler = socket.socket()
                fillers.append(filler)
                filler.setblocking(False)
                result = filler.connect_ex(listener.getsockname())
                self.assertIn(result, (0, errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EALREADY))
            # Independently prove this OS blocks a fresh connect before testing cancellation.
            probe = socket.socket()
            fillers.append(probe)
            probe.setblocking(False)
            result = probe.connect_ex(listener.getsockname())
            _, writable, _ = select.select([], [probe], [], .05)
            if result == 0 or writable:
                self.skipTest("this OS did not block connect after filling listen(0)")
            timer = threading.Timer(.1, cancel.set)
            timer.start()
            start = time.monotonic()
            with self.assertRaises(ClientError) as caught:
                request_synthetic(f"http://127.0.0.1:{listener.getsockname()[1]}", Config(n_ctx=1, timeout_s=1), cancel)
            self.assertEqual(caught.exception.code, "CANCELLED")
            self.assertLess(time.monotonic() - start, 1)
        finally:
            if timer is not None:
                timer.cancel()
                timer.join(timeout=1)
            for filler in fillers:
                filler.close()
            listener.close()
            self.assert_http_workers_stopped()

    def test_no_valid_samples_is_distinct_from_unsupported_platform(self):
        sampler = ResourceSampler(os.getpid())
        self.assertEqual(sampler.metrics()["commit_unavailable_reason"], "No valid process memory samples")
        with patch.object(sampler.process, "children", return_value=[]):
            sampler.sample()
        if sampler.commit_peak_bytes is None:
            self.assertEqual(sampler.metrics()["commit_unavailable_reason"], "Windows private bytes unavailable on this platform")
        else:
            self.assertIsNone(sampler.metrics()["commit_unavailable_reason"])


if __name__ == "__main__":
    unittest.main()

```

## task004/tests/test_hardening_record.py

SHA-256: `6207bbf7ac189f31e12c247e4d7ec4afa57aab8d896c1fe3a2925d0ffc54e46d`

```python
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

```

## task004/tests/test_hardening_schema.py

SHA-256: `d1a9653a9e535485941e2077cd38a474cb7265ddeac1d3323a7dd58c0e82853b`

```python
"""A3/A4 regressions for bounded config and explicit schema contracts."""
import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from task004.cli import main
from task004.config import Config, ConfigError, parse_config
from task004.record import STATUS_REASONS
from task004.schema import validate, validate_artifact


ROOT = Path(__file__).resolve().parents[1]
BASELINE_EVIDENCE = ROOT / "evidence" / "dry-run" / "e1979d42784948cfbeb13b44cbc6044a"


def schema(name):
    return json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text())


class ConfigBoundsTests(unittest.TestCase):
    def test_a3_timeout_and_sampling_upper_bounds(self):
        for key, upper in (("timeout_s", 3600), ("startup_timeout_s", 3600),
                           ("mock_delay_s", 3600), ("sample_interval_s", 60)):
            with self.subTest(key=key, value=upper):
                self.assertEqual(getattr(parse_config({"n_ctx": 1, key: upper}), key), upper)
            for value in (upper + .001, 1e10, 1e300):
                with self.subTest(key=key, value=value), self.assertRaises(ConfigError):
                    parse_config({"n_ctx": 1, key: value})

    def test_a3_validate_config_rejects_extreme_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            for key in ("timeout_s", "startup_timeout_s", "mock_delay_s", "sample_interval_s"):
                for value in (1e10, 1e300):
                    config_path.write_text(json.dumps({"n_ctx": 1, key: value}))
                    capture = io.StringIO()
                    with self.subTest(key=key, value=value), contextlib.redirect_stdout(capture):
                        result = main(["validate-config", "--config", str(config_path)])
                        self.assertEqual(result, 2)
                        self.assertEqual(json.loads(capture.getvalue())["status"], "CONFIG_ERROR")


class SchemaContractTests(unittest.TestCase):
    def test_a4_config_and_manifest_numerical_boundaries_match(self):
        config_schema = schema("manifest")["properties"]["config"]
        # Expected outcomes are explicit, so simultaneous weakening is detected.
        boundaries = {
            "n_ctx": [(0, False), (1, True), (2, True)],
            "max_new_tokens": [(0, False), (1, True), (2, True), (95, True), (96, True), (97, False)],
            "timeout_s": [(-.001, False), (0, False), (.001, True), (3599.999, True), (3600, True), (3600.001, False)],
            "startup_timeout_s": [(-.001, False), (0, False), (.001, True), (3599.999, True), (3600, True), (3600.001, False)],
            "sample_interval_s": [(.009, False), (.01, True), (.011, True), (59.999, True), (60, True), (60.001, False)],
            "mock_delay_s": [(-.001, False), (0, True), (.001, True), (3599.999, True), (3600, True), (3600.001, False)],
            "min_available_ram_bytes": [(-1, False), (0, True), (1, True)],
            "min_free_disk_bytes": [(-1, False), (0, True), (1, True)],
            "image_long_edge_px": [(0, False), (1, True), (2, True), (767, True), (768, True), (769, False)],
            "max_image_tokens": [(0, False), (1, True), (2, True)],
        }
        for key, cases in boundaries.items():
            for value, expected in cases:
                with self.subTest(key=key, value=value):
                    data = Config(n_ctx=1).to_dict()
                    if key in ("image_long_edge_px", "max_image_tokens"):
                        data.update(image_long_edge_px=64, max_image_tokens=16)
                    data[key] = value
                    try:
                        parse_config(data)
                        config_accepts = True
                    except ConfigError:
                        config_accepts = False
                    try:
                        validate(data, config_schema)
                        schema_accepts = True
                    except ValueError:
                        schema_accepts = False
                    self.assertEqual(config_accepts, expected)
                    self.assertEqual(schema_accepts, expected)

    def test_a4_every_pattern_is_anchored(self):
        def inspect(node):
            if "pattern" in node:
                self.assertTrue(node["pattern"].startswith("^"), node["pattern"])
                self.assertTrue(node["pattern"].endswith("$"), node["pattern"])
            for child in node.get("properties", {}).values():
                inspect(child)
            if "items" in node:
                inspect(node["items"])
        inspect(schema("run"))
        inspect(schema("manifest"))

    def test_a4_reason_enum_matches_status_reasons(self):
        actual = schema("run")["properties"]["reason_code"].get("enum", [])
        self.assertEqual(set(actual), set().union(*STATUS_REASONS.values()))
        self.assertEqual(len(actual), len(set(actual)))

    def test_a4_unsupported_keywords_fail_at_every_depth(self):
        from task004.schema import check_schema
        for invalid in (
            {"format": "date-time"},
            {"properties": {"child": {"format": "date-time"}}},
            {"items": {"properties": {"child": {"not": {}}}}},
            {"properties": {"array": {"items": {"allOf": []}}}},
        ):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "SCHEMA_UNSUPPORTED_KEYWORD"):
                check_schema(invalid)
        for name in ("run", "manifest"):
            check_schema(schema(name))

    def test_a4_validate_artifact_checks_schema_before_value(self):
        invalid = {"type": "object", "properties": {"ignored": {"format": "anything"}}}
        with patch("task004.schema.Path.read_text", return_value=json.dumps(invalid)):
            with self.assertRaisesRegex(ValueError, "SCHEMA_UNSUPPORTED_KEYWORD"):
                validate_artifact({}, "manifest")

    def test_a4_maximum_and_exclusive_minimum_enforced(self):
        contract = {"type": "number", "exclusiveMinimum": 0, "maximum": 1}
        validate(.001, contract)
        validate(1, contract)
        for value in (-.001, 0, 1.001):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate(value, contract)

    def test_a4_run_schema_rejects_bad_reason_time_token_and_id(self):
        baseline = json.loads((BASELINE_EVIDENCE / "runs.jsonl").read_text())
        invalid_cases = [
            ("reason_code", "UNREGISTERED"),
            ("started_at_utc", "not-a-timestamp"),
            ("finished_at_utc", "2026-11-06T00:00:00+07:00"),
            ("run_id", "ZZ" + baseline["run_id"] + "ZZ"),
        ]
        for key, value in invalid_cases:
            broken = deepcopy(baseline)
            broken[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_artifact(broken, "run")
        broken = deepcopy(baseline)
        broken["metrics"]["synthetic_output_tokens"] = 1.5
        with self.assertRaises(ValueError):
            validate_artifact(broken, "run")

    def test_a4_existing_committed_evidence_remains_valid(self):
        manifest = json.loads((BASELINE_EVIDENCE / "manifest.json").read_text())
        run = json.loads((BASELINE_EVIDENCE / "runs.jsonl").read_text())
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(run["schema_version"], 1)
        validate_artifact(manifest, "manifest")
        validate_artifact(run, "run")

    def test_a4_malformed_supported_keyword_forms_fail_closed(self):
        from task004.schema import check_schema
        for malformed in ({"type": "bogus"}, {"type": []}, {"properties": []},
                          {"required": "name"}, {"items": []}, {"maximum": True},
                          {"additionalProperties": {"type": "string"}}, {"enum": []}):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                check_schema(malformed)


if __name__ == "__main__":
    unittest.main()

```

## task004/tests/test_hardening_server.py

SHA-256: `89c3ac9bf1cffda818da7420766d302a5a41d2ad486f236e70b306a4d8bb3a9e`

```python
"""A1/B2/B3 regressions; process guarantees are Linux-verified only."""
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import psutil

from task004.config import Config
from task004.server import ManagedMockServer, stop_owned_process


def active(process):
    try:
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False


def reap_owned(process, children):
    # Discover before killing the CLI; preserve identity objects if it already died.
    try:
        if process.poll() is None:
            children.extend(psutil.Process(process.pid).children(recursive=True))
    except psutil.NoSuchProcess:
        pass
    for child in children:
        try:
            if active(child):
                child.kill()
        except psutil.NoSuchProcess:
            pass
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)


class ServerHardeningTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "POSIX SIGKILL integration; Windows unverified")
    def test_a1_killed_cli_leaves_no_mock_or_owned_scratch(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        directory = Path(temp.name)
        config = directory / "config.json"
        config.write_text(json.dumps(Config(n_ctx=512, mock_scenario="slow",
                                           mock_delay_s=30, timeout_s=20).to_dict()))
        cli = subprocess.Popen([sys.executable, "-m", "task004.cli", "dry-run",
                                "--config", str(config), "--output-dir", str(directory / "runs")],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
        children = []
        self.addCleanup(reap_owned, cli, children)
        scratch = None
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and cli.poll() is None:
            for child in psutil.Process(cli.pid).children():
                try:
                    command = child.cmdline()
                    if "task004.mock_server" in command:
                        if child not in children:
                            children.append(child)
                        port_file = Path(command[command.index("--port-file") + 1])
                        if port_file.exists():
                            scratch = port_file.parent
                            break
                except psutil.NoSuchProcess:
                    pass
            if scratch is not None:
                break
            time.sleep(.01)
        self.assertIsNotNone(scratch, "mock did not initialize before harness kill")
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        self.assertTrue(children)
        cli.send_signal(signal.SIGKILL)
        cli.wait(timeout=3)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if not any(active(child) for child in children) and not scratch.exists():
                break
            time.sleep(.025)
        self.assertFalse(any(active(child) for child in children), "mock survived harness SIGKILL")
        self.assertFalse(scratch.exists(), "owned scratch survived harness SIGKILL")

    def test_a1_mock_maximum_lifetime_exits(self):
        with tempfile.TemporaryDirectory(prefix="task004-mock-") as scratch:
            child = subprocess.Popen([sys.executable, "-m", "task004.mock_server", "--port-file",
                                      str(Path(scratch) / "port"), "--parent-pid", str(os.getpid()),
                                      "--max-lifetime-s", ".1"], stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
            self.addCleanup(reap_owned, child, [])
            self.assertEqual(child.wait(timeout=5), 3)

    def test_a1_missing_parent_exits_immediately_and_cleans_scratch(self):
        parent = subprocess.Popen([sys.executable, "-c", "pass"])
        parent.wait(timeout=5)
        with tempfile.TemporaryDirectory(prefix="task004-mock-") as scratch:
            child = subprocess.Popen([sys.executable, "-m", "task004.mock_server", "--port-file",
                                      str(Path(scratch) / "port"), "--parent-pid", str(parent.pid)],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.addCleanup(reap_owned, child, [])
            self.assertEqual(child.wait(timeout=3), 3)
            self.assertFalse(Path(scratch).exists())

    @unittest.skipUnless(os.name == "posix", "POSIX owned groups; Windows unverified")
    def test_b2_empty_owned_group_is_not_signalled(self):
        root = subprocess.Popen([sys.executable, "-c", "pass"], start_new_session=True)
        self.addCleanup(reap_owned, root, [])
        root.wait(timeout=5)
        with patch("task004.server.os.killpg") as killpg:
            stop_owned_process(root, owned_pgid=root.pid)
        killpg.assert_not_called()

    @unittest.skipUnless(sys.platform.startswith("linux"), "child environ read verified on Linux only")
    def test_b3_mock_does_not_inherit_harness_secret(self):
        with patch.dict(os.environ, {"TASK004_FAKE_TOKEN": "synthetic-secret-marker"}):
            with ManagedMockServer(Config(n_ctx=512)) as server:
                child_environment = psutil.Process(server.pid).environ()
                self.assertNotIn("TASK004_FAKE_TOKEN", child_environment)
                self.assertTrue(set(child_environment).issubset({"PATH", "SYSTEMROOT", "TEMP", "TMP", "LANG", "LC_ALL"}))


if __name__ == "__main__":
    unittest.main()

```

## task004/tests/test_review_cli.py

SHA-256: `d791cb63c72a2f4d4c0abd27d8fd26d6669d4492b13c05ac212d8f3f0a7dd913`

```python
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

```

## task004/tests/test_review_record.py

SHA-256: `3b93cf29fecd3963e84b370bb0b76dfd9de2e7b9ac0ece68725005f08c30b4b3`

```python
import ast
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from task004.record import STATUS_REASONS, source_provenance, validate_record
from task004.tests.fixtures import artifact_fixture


class ReviewRecordTests(unittest.TestCase):
    def test_malformed_provenance_is_always_safe_valueerror(self):
        valid = {'file': 'card.md', 'bytes': 1, 'sha256': '0'*64}
        cases = [None, [], {}, {'sources': None}, {'sources': [None]}, {'sources': [{}]},
                 {'sources': [{**valid, 'file': ['bad']}]}, {'sources': [{**valid, 'sha256': None}]},
                 {'sources': [{**valid, 'bytes': True}]}, {'sources': [{**valid, 'file': '../bad'}]},
                 {'sources': [{**valid, 'file': r'..\bad'}]}, {'sources': [valid, valid]}]
        for index in cases:
            with self.subTest(index=index), patch('task004.record.Path.read_text', return_value=json.dumps(index)):
                with self.assertRaises(ValueError):
                    source_provenance()

    def test_all_literal_client_and_server_errors_are_registered(self):
        root = Path(__file__).resolve().parents[1]
        codes = set()
        for name in ('client.py', 'server.py'):
            for node in ast.walk(ast.parse((root/name).read_text())):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id in ('ClientError', 'ServerError') and node.args
                        and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                    codes.add(node.args[0].value)
        self.assertGreater(len(codes), 10)
        self.assertEqual(codes - set().union(*STATUS_REASONS.values()), set())

    def test_pass_requires_positive_resource_evidence(self):
        _, record, _ = artifact_fixture()
        validate_record(record)
        for resources in (None, {**record['resources'], 'samples': 0}, {**record['resources'], 'rss_peak_bytes': None},
                          {**record['resources'], 'rss_peak_bytes': 0}, {**record['resources'], 'samples': True}):
            with self.subTest(resources=resources):
                broken = deepcopy(record)
                broken['resources'] = resources
                with self.assertRaises(ValueError):
                    validate_record(broken)

```

## task004/tests/test_review_runner.py

SHA-256: `689e1fba47eb1accab63d0461b23aaea11d6a395baa561e89a42da96f16117e8`

```python
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

```

## task004/tests/test_server.py

SHA-256: `a1b11cef6ef9a262e0c1e9c439ab4d2c4053dd05139d2eec915d6ec292ee4228`

```python
"""Functional subprocess/HTTP lifecycle checks; only terminate owned fixtures."""

import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

import psutil

from task004.config import Config
from task004.server import ManagedMockServer, ServerError, ServerTimeout, stop_owned_process


def is_active(pid):
    try:
        process = psutil.Process(pid)
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False


class ServerTests(unittest.TestCase):
    def test_success_startup_answers_health_and_context_stops(self):
        server = ManagedMockServer(Config(n_ctx=512))
        with server:
            self.assertTrue(is_active(server.pid))
            self.assertTrue(server.url.startswith("http://127.0.0.1:"))
            self.assertGreater(server.port, 0)
            conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=2)
            try:
                conn.request("GET", "/health")
                response = conn.getresponse()
                self.assertEqual(response.status, 200)
                self.assertEqual(json.loads(response.read()), {"status": "ok"})
            finally:
                conn.close()
            directory = Path(server._directory.name)
            self.assertTrue(directory.exists())
        self.assertIsNotNone(server.process.poll())
        self.assertFalse(is_active(server.pid))
        self.assertFalse(directory.exists())

    def test_health_failure_reaches_deadline_and_cleans_process(self):
        server = ManagedMockServer(Config(n_ctx=512, mock_scenario="health_failure", startup_timeout_s=0.3))
        self.addCleanup(server.stop)
        started = time.monotonic()
        with self.assertRaises(ServerTimeout) as caught:
            server.start()
        self.assertEqual(caught.exception.code, "STARTUP_TIMEOUT")
        self.assertLess(time.monotonic() - started, 4)
        self.assertIsNotNone(server.process)
        self.assertIsNotNone(server.process.poll())
        self.assertFalse(is_active(server.pid))
        self.assertIsNone(server._directory)

    def test_keyboard_interrupt_propagates_after_cleanup(self):
        server = ManagedMockServer(Config(n_ctx=512))
        self.addCleanup(server.stop)
        with self.assertRaises(KeyboardInterrupt):
            with server:
                self.assertTrue(is_active(server.pid))
                raise KeyboardInterrupt
        self.assertFalse(is_active(server.pid))
        self.assertIsNone(server._directory)

    def test_startup_cancel_after_spawn_stops_child(self):
        server = ManagedMockServer(Config(n_ctx=512, mock_scenario="health_failure", startup_timeout_s=3))
        self.addCleanup(server.stop)
        cancelled = threading.Event()
        observed_spawn = threading.Event()

        def cancel_when_spawned():
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if server.process is not None and server.process.poll() is None:
                    observed_spawn.set()
                    break
                time.sleep(0.005)
            cancelled.set()

        worker = threading.Thread(target=cancel_when_spawned)
        worker.start()
        try:
            with self.assertRaises(ServerError) as caught:
                server.start(cancel_event=cancelled)
            self.assertEqual(caught.exception.code, "CANCELLED")
            self.assertTrue(observed_spawn.is_set())
            self.assertIsNotNone(server.process.poll())
            self.assertFalse(is_active(server.pid))
            self.assertIsNone(server._directory)
        finally:
            cancelled.set()
            worker.join(timeout=4)
        self.assertFalse(worker.is_alive())

    def test_cancel_set_before_start_leaves_no_live_child(self):
        server = ManagedMockServer(Config(n_ctx=512))
        self.addCleanup(server.stop)
        cancelled = threading.Event()
        cancelled.set()
        with self.assertRaises(ServerError) as caught:
            server.start(cancel_event=cancelled)
        self.assertEqual(caught.exception.code, "CANCELLED")
        if server.process is not None:
            self.assertIsNotNone(server.process.poll())
            self.assertFalse(is_active(server.pid))
        self.assertIsNone(server._directory)

    def test_stop_is_idempotent_before_and_after_start(self):
        server = ManagedMockServer(Config(n_ctx=512))
        server.stop()
        server.start()
        self.addCleanup(server.stop)
        server.stop()
        server.stop()
        self.assertFalse(is_active(server.pid))
        self.assertIsNone(server._directory)
        stop_owned_process(None)

    def test_second_start_rejected_without_replacing_live_process(self):
        with ManagedMockServer(Config(n_ctx=512)) as server:
            pid = server.pid
            with self.assertRaises(ServerError) as caught:
                server.start()
            self.assertEqual(caught.exception.code, "SERVER_ALREADY_STARTED")
            self.assertEqual(server.pid, pid)
            self.assertTrue(is_active(pid))

    def test_url_unavailable_before_start(self):
        with self.assertRaises(ServerError) as caught:
            _ = ManagedMockServer(Config(n_ctx=512)).url
        self.assertEqual(caught.exception.code, "SERVER_NOT_STARTED")

    def test_cleanup_access_denied_is_safe_error(self):
        process = Mock(pid=123)
        process.poll.return_value = None
        with patch("task004.server.psutil.Process", side_effect=psutil.AccessDenied(123, "sensitive name")):
            with self.assertRaises(ServerError) as caught:
                stop_owned_process(process)
        self.assertEqual(caught.exception.code, "CLEANUP_FAILED")
        self.assertNotIn("sensitive", str(caught.exception))

    @unittest.skipUnless(os.name == "posix", "POSIX session isolation; Windows live-tree fallback")
    def test_exited_session_parent_descendant_cleanup_and_unrelated_survival(self):
        parent_code = (
            "import subprocess,sys;from pathlib import Path;"
            "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);"
            "Path(sys.argv[1]).write_text(str(child.pid))"
        )
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "owned-child"
            unrelated = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(60)"],
                                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL)
            self.addCleanup(stop_owned_process, unrelated)
            parent = subprocess.Popen([sys.executable, "-c", parent_code, str(marker)],
                                      stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL, start_new_session=True)
            self.addCleanup(stop_owned_process, parent, owned_pgid=parent.pid)
            self.assertEqual(parent.wait(timeout=5), 0)
            child_pid = int(marker.read_text())
            self.assertTrue(is_active(child_pid))
            self.assertEqual(os.getpgid(child_pid), parent.pid)
            stop_owned_process(parent, owned_pgid=parent.pid)
            self.assertFalse(is_active(child_pid))
            self.assertTrue(is_active(unrelated.pid))
            # A second stop must not send a signal to a potentially recycled PGID.
            with patch("task004.server.os.killpg") as killpg:
                stop_owned_process(parent, owned_pgid=parent.pid)
                killpg.assert_not_called()

    @unittest.skipUnless(os.name == "posix", "POSIX process groups only")
    def test_group_cleanup_requires_matching_owner(self):
        process = Mock(pid=123)
        with patch("task004.server.os.killpg") as killpg:
            with self.assertRaises(ServerError) as caught:
                stop_owned_process(process, owned_pgid=456)
            killpg.assert_not_called()
        self.assertEqual(caught.exception.code, "CLEANUP_FAILED")

    @unittest.skipUnless(os.name == "posix", "POSIX group SIGKILL escalation only")
    def test_exited_parent_term_resistant_child_is_force_killed(self):
        child_code = (
            "import os,signal,sys,time;from pathlib import Path;"
            "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
            "Path(sys.argv[1]).write_text(str(os.getpid()));time.sleep(60)"
        )
        parent_code = "import subprocess,sys;subprocess.Popen([sys.executable,'-c',sys.argv[1],sys.argv[2]])"
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "term-resistant-child"
            parent = subprocess.Popen([sys.executable, "-c", parent_code, child_code, str(marker)],
                                      stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL, start_new_session=True)
            self.addCleanup(stop_owned_process, parent, owned_pgid=parent.pid)
            self.assertEqual(parent.wait(timeout=5), 0)
            deadline = time.monotonic() + 5
            child_pid = None
            while time.monotonic() < deadline:
                try:
                    child_pid = int(marker.read_text())
                    break
                except (OSError, ValueError):
                    time.sleep(.01)
            self.assertIsNotNone(child_pid)
            self.assertTrue(is_active(child_pid))
            stop_owned_process(parent, owned_pgid=parent.pid)
            self.assertFalse(is_active(child_pid))

    def test_owned_descendants_stopped_without_touching_unrelated_process(self):
        # The child publishes both identities only after the grandchild exists.
        # All processes are spawned here; no global process-name matching.
        child_code = (
            "import json,os,subprocess,sys,time;from pathlib import Path;"
            "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);"
            "Path(sys.argv[1]).write_text(json.dumps([os.getpid(),child.pid]));"
            "time.sleep(60)"
        )
        parent_code = (
            "import subprocess,sys,time;"
            "subprocess.Popen([sys.executable,'-c',sys.argv[1],sys.argv[2]]);"
            "time.sleep(60)"
        )
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "owned-pids.json"
            unrelated = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(60)"],
                                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL)
            self.addCleanup(stop_owned_process, unrelated)
            parent = subprocess.Popen([sys.executable, "-c", parent_code, child_code, str(marker)],
                                      stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL)
            self.addCleanup(stop_owned_process, parent)
            deadline = time.monotonic() + 5
            descendant_pids = None
            while time.monotonic() < deadline:
                try:
                    descendant_pids = json.loads(marker.read_text())
                    break
                except (OSError, ValueError):
                    time.sleep(0.01)
            self.assertIsNotNone(descendant_pids, "owned descendant fixture failed to initialize")
            for pid in descendant_pids:
                self.assertTrue(is_active(pid))
            stop_owned_process(parent)
            self.assertIsNotNone(parent.poll())
            for pid in descendant_pids:
                self.assertFalse(is_active(pid), "owned descendant still active after cleanup")
            self.assertIsNone(unrelated.poll())
            self.assertTrue(is_active(unrelated.pid))


if __name__ == "__main__":
    unittest.main()

```

## task004/tests/test_workflow.py

SHA-256: `a5c66432ed8747b5445ab48be508896f2f37d68f0d7daffeea3bac2d8f4a899e`

```python
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

```

## task004/tools/validate_hardening.py

SHA-256: `c92c72742be2d22b4653fa5f2370e33d9f3d93b431de9d23d43eaf6aa168cec6`

```python
"""Generate review evidence from actual subprocesses; never edit prior evidence.

Run from repo root: python task004/tools/validate_hardening.py --output <new-directory>
Requires authorized loopback sockets. Copies baseline/mutant into temporary directories,
never mutates the working source and never makes Git worktrees.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

import psutil

BASELINE = '2cb916803cef6c2c52f03107fddeb866c407ae27'
REVIEW_BASELINE = '07eb03cd0f01d16feef6f090cd5ed74c4c075eeb'
ROOT = Path(__file__).resolve().parents[2]
TARGETS = {
    'A1': ['task004.tests.test_hardening_server.ServerHardeningTests.test_a1_killed_cli_leaves_no_mock_or_owned_scratch'],
    'A2': ['task004.tests.test_hardening_record.AtomicArtifactTests.test_second_write_failure_cleans_staging_for_baseexceptions'],
    'A3': ['task004.tests.test_hardening_schema.ConfigBoundsTests'],
    'A4': ['task004.tests.test_hardening_schema.SchemaContractTests.test_a4_config_and_manifest_numerical_boundaries_match',
           'task004.tests.test_hardening_schema.SchemaContractTests.test_a4_reason_enum_matches_status_reasons',
           'task004.tests.test_hardening_schema.SchemaContractTests.test_a4_validate_artifact_checks_schema_before_value'],
    'A5': ['task004.tests.test_workflow.WorkflowTests.test_nonloopback_endpoint_rejected_before_connection'],
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def fingerprints():
    files = list((ROOT/'task004').glob('*.py'))
    for sub, pattern in [('tests', '*.py'), ('schemas', '*.json'), ('tools', '*.py')]:
        files.extend((ROOT/'task004'/sub).glob(pattern))
    files.extend((ROOT/'task004/references').rglob('*'))
    files.extend(ROOT/'task004'/name for name in ('mock_config.json', 'requirements.txt', 'setup.sh'))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files) if p.is_file()}


def verification_scope():
    return f"{platform.system()}-executed mock tests; readiness requires result review"


def normalize_paths(text, locations):
    # Retain diagnostics; redact only known local prefixes, including repr-escaped paths.
    for path, label in sorted(locations.items(), key=lambda item: len(str(item[0])), reverse=True):
        path = str(path)
        for spelling in (path.replace('\\', '\\\\'), path.replace('\\', '/'), path):
            text = text.replace(spelling, label)
    return text


def extract_archive(data, destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for member in tar.getmembers():
            target = (destination/member.name).resolve()
            if not target.is_relative_to(destination) or member.issym() or member.islnk():
                raise ValueError('unexpected baseline archive member')
        tar.extractall(destination, filter='data')
    return destination


DEFECT_ASSERTIONS = {
    'test_a1_killed_cli_leaves_no_mock_or_owned_scratch': ('mock survived harness SIGKILL',),
    'test_second_write_failure_cleans_staging_for_baseexceptions': ('partial artifact survived injected failure',),
    'test_a3_timeout_and_sampling_upper_bounds': ('ConfigError not raised',),
    'test_a3_validate_config_rejects_extreme_values': ('2', 'self.assertEqual(result, 2)'),
    'test_a4_config_and_manifest_numerical_boundaries_match': ('accepts, expected)', 'AssertionError: True != False'),
    'test_a4_reason_enum_matches_status_reasons': ('self.assertEqual(set(actual), set().union(*STATUS_REASONS.values()))',),
    'test_a4_validate_artifact_checks_schema_before_value': ('ValueError not raised',),
    'test_nonloopback_endpoint_rejected_before_connection': ('NON_LOOPBACK_ENDPOINT',),
    'test_nested_signal_cannot_deadlock_handler': ('nested signal deadlocked cancellation handler',),
    'test_inherited_ignore_is_preserved': ('inherited ignored SIGHUP requested cancellation',),
}


def expected_defect_failures(text):
    blocks = re.findall(r'^FAIL: (.*?)(?=^={10,}|^Ran |\Z)', text, re.MULTILINE | re.DOTALL)
    if not blocks:
        return False
    for block in blocks:
        method = block.split()[0]
        if method not in DEFECT_ASSERTIONS or 'AssertionError:' not in block:
            return False
        if not all(fragment in block for fragment in DEFECT_ASSERTIONS[method]):
            return False
    return True


def log_diagnostics(text, allow_expected_traceback=False):
    markers = ('Exception ignored', 'ResourceWarning') if allow_expected_traceback else ('Exception ignored', 'ResourceWarning', 'Traceback')
    return [marker for marker in markers if marker in text]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    summary = {'baseline_revision': BASELINE, 'review_baseline_revision': REVIEW_BASELINE, 'started_at_utc': utc(),
               'python': platform.python_version(), 'psutil': psutil.__version__,
               'platform': platform.system(), 'verification_scope': verification_scope(),
               'log_policy': 'Known local path prefixes normalized; diagnostic text preserved. Successful runs reject Exception ignored, ResourceWarning and Traceback.',
               'source_sha256': fingerprints(), 'runs': [], 'windows': 'UNVERIFIED', 'model': 'NOT_RUN'}
    failures = []
    locations = {ROOT: '<checkout>', Path(sys.prefix): '<python-env>', Path(sys.base_prefix): '<python-base>', Path.home(): '<home>', Path(tempfile.gettempdir()): '<temp>'}
    child_env = dict(os.environ, PYTHONWARNINGS='error::ResourceWarning')

    def run(label, cwd, args, expected_failure=False):
        command = [sys.executable, '-W', 'error::ResourceWarning', '-m', 'unittest', *args]
        start = time.monotonic()
        result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180, env=child_env)
        text = normalize_paths(result.stdout.decode('utf-8', errors='replace'), locations)
        (output/f'{label}.log').write_text(text)
        count = re.search(r'Ran (\d+) tests? in ([0-9.]+)s', text)
        entry = {'label': label, 'command': ['<python>', *command[1:]], 'cwd': normalize_paths(str(cwd), locations), 'returncode': result.returncode,
                 'elapsed_s': time.monotonic()-start, 'tests_run': int(count[1]) if count else None,
                 'failures': int(re.search(r'failures=(\d+)', text)[1]) if re.search(r'failures=(\d+)', text) else 0,
                 'errors': int(re.search(r'errors=(\d+)', text)[1]) if re.search(r'errors=(\d+)', text) else 0,
                 'skipped': int(re.search(r'skipped=(\d+)', text)[1]) if re.search(r'skipped=(\d+)', text) else 0,
                 'expected_failure': expected_failure, 'log': f'{label}.log'}
        # Baseline/mutation evidence must be assertion failures, not missing imports.
        entry['diagnostic_markers'] = log_diagnostics(text, allow_expected_traceback=expected_failure)
        entry['defect_assertions_match'] = expected_defect_failures(text) if expected_failure else None
        ok = (entry['tests_run'] and entry['skipped'] == 0 and entry['errors'] == 0 and not entry['diagnostic_markers']
              and ((result.returncode != 0 and entry['failures'] > 0 and entry['defect_assertions_match']) if expected_failure else result.returncode == 0))
        entry['expectation_met'] = bool(ok)
        summary['runs'].append(entry)
        if not ok:
            failures.append(label)
        print(label, 'expected result' if ok else 'UNEXPECTED', 'tests=', entry['tests_run'], flush=True)

    try:
        with tempfile.TemporaryDirectory(prefix='task004-regression-') as tmp:
            temp_root = Path(tmp).resolve()
            baseline = temp_root/'baseline'
            locations[baseline] = '<baseline>'
            archive = subprocess.check_output(['git', 'archive', BASELINE], cwd=ROOT)
            extract_archive(archive, baseline)
            for name in ['test_hardening_server.py', 'test_hardening_record.py', 'test_hardening_schema.py', 'test_workflow.py', 'fixtures.py']:
                shutil.copy2(ROOT/'task004/tests'/name, baseline/'task004/tests'/name)
            for requirement, targets in TARGETS.items():
                # A5 hardens a TEST; the production guard already exists at baseline.
                # Its defect is demonstrated by the baseline test accepting a mutant.
                run(f'baseline-{requirement}', baseline, ['-v', *targets], expected_failure=requirement != 'A5')
                run(f'fixed-{requirement}', ROOT, ['-v', *targets])
            review = temp_root/'review-baseline'
            locations[review] = '<review-baseline>'
            extract_archive(subprocess.check_output(['git', 'archive', REVIEW_BASELINE], cwd=ROOT), review)
            shutil.copy2(ROOT/'task004/tests/test_review_cli.py', review/'task004/tests/test_review_cli.py')
            for name in ('test_nested_signal_cannot_deadlock_handler', 'test_inherited_ignore_is_preserved'):
                target = 'task004.tests.test_review_cli.ReviewCliTests.' + name
                run('review-baseline-' + name, review, ['-v', target], expected_failure=True)
                run('fixed-review-' + name, ROOT, ['-v', target])
            mutant = temp_root/'mutant'
            locations[mutant] = '<mutant>'
            shutil.copytree(ROOT/'task004', mutant/'task004', ignore=shutil.ignore_patterns('__pycache__', 'runs', 'hardening-*'))
            path = mutant/'task004/client.py'
            source = path.read_text()
            function = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == 'request_synthetic')
            guard = next(node for node in function.body if isinstance(node, ast.If) and 'parsed.scheme' in ast.get_source_segment(source, node))
            lines = source.splitlines(keepends=True)
            removed = ''.join(lines[guard.lineno-1:guard.end_lineno])
            del lines[guard.lineno-1:guard.end_lineno]
            path.write_text(''.join(lines))
            (output/'mutation-A5-removed-guard.txt').write_text(removed)
            run('mutation-A5', mutant, ['-v', *TARGETS['A5']], expected_failure=True)
            baseline_client = baseline/'task004/client.py'
            old_source = baseline_client.read_text()
            old_function = next(n for n in ast.parse(old_source).body if isinstance(n, ast.FunctionDef) and n.name == 'request_synthetic')
            old_guard = next(n for n in old_function.body if isinstance(n, ast.If) and 'parsed.scheme' in ast.get_source_segment(old_source, n))
            old_lines = old_source.splitlines(keepends=True)
            del old_lines[old_guard.lineno-1:old_guard.end_lineno]
            baseline_client.write_text(''.join(old_lines))
            old_test = subprocess.check_output(['git', 'show', BASELINE + ':task004/tests/test_workflow.py'], cwd=ROOT)
            (baseline/'task004/tests/test_workflow.py').write_bytes(old_test)
            run('baseline-mutant-A5-undetected', baseline, ['-v', *TARGETS['A5']])
        # Required consecutive full-suite runs, with no intervening code edits.
        for index in range(1, 4):
            run(f'suite-{index}', ROOT, ['discover', '-s', 'task004/tests', '-v'])
        dry_command = [sys.executable, '-m', 'task004.cli', 'dry-run', '--output-dir', str(output/'dry-run')]
        dry = subprocess.run(dry_command, cwd=ROOT, capture_output=True, text=True, timeout=30, env=child_env)
        (output/'dry-run.stdout.log').write_text(normalize_paths(dry.stdout, locations))
        (output/'dry-run.stderr.log').write_text(normalize_paths(dry.stderr, locations))
        summary['dry_run'] = {'command': ['<python>', *[normalize_paths(arg, locations) for arg in dry_command[1:]]], 'returncode': dry.returncode, 'result': json.loads(dry.stdout), 'diagnostic_markers': log_diagnostics(dry.stdout + dry.stderr)}
        if dry.returncode or summary['dry_run']['result']['status'] != 'PASS' or summary['dry_run']['diagnostic_markers']:
            failures.append('dry-run')
        if fingerprints() != summary['source_sha256']:
            failures.append('source_changed_during_validation')
    except BaseException:
        failures.append('runner_interrupted_or_failed')
        raise
    finally:
        summary['finished_at_utc'] = utc()
        summary['failed_expectations'] = failures
        summary['status'] = 'PASS' if not failures and 'dry_run' in summary else 'FAIL'
        (output/'validation.json').write_text(json.dumps(summary, indent=2)+'\n')
    return 0 if summary['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())

```
