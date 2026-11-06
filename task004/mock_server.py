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
