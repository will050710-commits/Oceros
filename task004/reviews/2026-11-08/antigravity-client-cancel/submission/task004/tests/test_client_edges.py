from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import threading
import time
import unittest
from unittest.mock import patch

from task004.client import ClientError, request_synthetic
from task004.config import Config

SYNTHETIC_OK_BYTES = json.dumps({
    "id": "synthetic",
    "choices": [{"text": "SYNTHETIC_OK"}],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    "evidence_label": "SYNTHETIC",
}).encode()


@contextmanager
def body_fixture(mode, stall_s=3.0, delay_s=0.15, step_s=0.07):
    stop = threading.Event()
    phase_ready = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            try:
                if mode == "header_stall":
                    phase_ready.set()
                    stop.wait(stall_s)
                    return
                if mode == "partial_header_stall":
                    self.wfile.write(b"HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n")
                    self.wfile.flush()
                    phase_ready.set()
                    stop.wait(stall_s)
                    return
                if mode == "delayed_valid":
                    phase_ready.set()
                    if stop.wait(delay_s):
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(SYNTHETIC_OK_BYTES)))
                    self.end_headers()
                    if stop.wait(delay_s):
                        return
                    self.wfile.write(SYNTHETIC_OK_BYTES)
                    self.wfile.flush()
                    return
                if mode == "chunked_writes":
                    phase_ready.set()
                    header_block = (
                        f"HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n"
                        f"Content-Length: {len(SYNTHETIC_OK_BYTES)}\r\n\r\n"
                    ).encode("ascii")
                    mid_header = len(header_block) // 2
                    for part in (
                        header_block[:10],
                        header_block[10:mid_header],
                        header_block[mid_header:],
                        SYNTHETIC_OK_BYTES[:15],
                        SYNTHETIC_OK_BYTES[15:45],
                        SYNTHETIC_OK_BYTES[45:],
                    ):
                        if stop.wait(step_s):
                            return
                        self.wfile.write(part)
                        self.wfile.flush()
                    return
                self.send_response(200)
                self.send_header("Content-Length", "100000" if mode == "oversize" else "1000")
                self.end_headers()
                if mode == "partial_body_stall":
                    self.wfile.write(b'{"id":"syn')
                    self.wfile.flush()
                    phase_ready.set()
                    stop.wait(stall_s)
                    return
                phase_ready.set()
                if mode == "oversize":
                    self.wfile.write(b"x" * 100000)
                elif mode == "trickle":
                    while not stop.wait(.01):
                        self.wfile.write(b"x")
                        self.wfile.flush()
                else:
                    stop.wait(stall_s)
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.01), daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", phase_ready
    finally:
        stop.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class ClientEdgeTests(unittest.TestCase):
    def assert_worker_stopped(self):
        self.assertFalse(any(t.name == "task004-http" for t in threading.enumerate()))

    def wait_for_workers_cleanup(self):
        deadline = time.monotonic() + 2
        while any(t.name == "task004-http" for t in threading.enumerate()) and time.monotonic() < deadline:
            time.sleep(.01)

    def test_timeout_during_http10_body_read(self):
        for mode in ("stall", "trickle"):
            with self.subTest(mode=mode), body_fixture(mode) as (url, _):
                try:
                    start = time.monotonic()
                    with self.assertRaises(ClientError) as caught:
                        request_synthetic(url, Config(n_ctx=1, timeout_s=.15))
                    self.assertEqual(caught.exception.code, "TIMEOUT")
                    self.assertLess(time.monotonic() - start, 1)
                    self.assert_worker_stopped()
                finally:
                    self.wait_for_workers_cleanup()

    def test_cancel_during_http10_body_read(self):
        with body_fixture("stall") as (url, headers_sent):
            cancel = threading.Event()
            def cancel_after_headers():
                headers_sent.wait(timeout=1)
                cancel.set()
            trigger = threading.Thread(target=cancel_after_headers)
            trigger.start()
            try:
                with self.assertRaises(ClientError) as caught:
                    request_synthetic(url, Config(n_ctx=1), cancel)
                trigger.join(timeout=1)
                self.assertEqual(caught.exception.code, "CANCELLED")
                self.assert_worker_stopped()
            finally:
                trigger.join(timeout=1)
                self.wait_for_workers_cleanup()

    def test_cancel_during_header_and_trickle_reads(self):
        for mode in ("header_stall", "partial_header_stall", "partial_body_stall", "trickle"):
            with self.subTest(mode=mode), body_fixture(mode) as (url, phase_ready):
                cancel = threading.Event()
                def trigger_cancel():
                    phase_ready.wait(timeout=1)
                    time.sleep(.02)
                    cancel.set()
                trigger = threading.Thread(target=trigger_cancel)
                trigger.start()
                try:
                    start = time.monotonic()
                    with self.assertRaises(ClientError) as caught:
                        request_synthetic(url, Config(n_ctx=1, timeout_s=5), cancel)
                    self.assertEqual(caught.exception.code, "CANCELLED")
                    self.assertLess(time.monotonic() - start, 1)
                    self.assert_worker_stopped()
                finally:
                    trigger.join(timeout=1)
                    self.wait_for_workers_cleanup()

    def test_timeout_during_header_stall_and_partial_headers(self):
        for mode in ("header_stall", "partial_header_stall", "partial_body_stall"):
            with self.subTest(mode=mode), body_fixture(mode) as (url, _):
                try:
                    start = time.monotonic()
                    with self.assertRaises(ClientError) as caught:
                        request_synthetic(url, Config(n_ctx=1, timeout_s=.15))
                    self.assertEqual(caught.exception.code, "TIMEOUT")
                    self.assertLess(time.monotonic() - start, 1)
                    self.assert_worker_stopped()
                finally:
                    self.wait_for_workers_cleanup()

    def test_delayed_and_partial_valid_response_succeeds(self):
        for mode in ("delayed_valid", "chunked_writes"):
            with self.subTest(mode=mode), body_fixture(mode, delay_s=.15, step_s=.07) as (url, _):
                try:
                    try:
                        metrics = request_synthetic(url, Config(n_ctx=1, timeout_s=2.0))
                    except ClientError as exc:
                        self.fail(f"valid delayed response raised ClientError({exc.code!r})")
                    self.assertEqual(metrics["synthetic_output_tokens"], 1)
                    self.assertGreaterEqual(metrics["request_latency_s"], .25)
                    self.assert_worker_stopped()
                finally:
                    self.wait_for_workers_cleanup()

    def test_cancel_stops_worker_when_shutdown_does_not_wake_read(self):
        """Cross-platform simulation: socket.shutdown is a no-op during stalled body read."""
        shutdown_calls = []
        with body_fixture("stall") as (url, headers_sent):
            cancel = threading.Event()
            def cancel_after_headers():
                headers_sent.wait(timeout=1)
                time.sleep(.02)
                cancel.set()
            trigger = threading.Thread(target=cancel_after_headers)
            trigger.start()
            try:
                with patch.object(socket.socket, "shutdown", lambda sock, how: shutdown_calls.append(how)):
                    start = time.monotonic()
                    with self.assertRaises(ClientError) as caught:
                        request_synthetic(url, Config(n_ctx=1, timeout_s=5), cancel)
                self.assertEqual(caught.exception.code, "CANCELLED")
                self.assertLess(time.monotonic() - start, 1)
                self.assertTrue(shutdown_calls)
                self.assert_worker_stopped()
            finally:
                trigger.join(timeout=1)
                self.wait_for_workers_cleanup()

    def test_response_size_is_bounded(self):
        with body_fixture("oversize") as (url, _):
            try:
                with self.assertRaises(ClientError) as caught:
                    request_synthetic(url, Config(n_ctx=1))
                self.assertEqual(caught.exception.code, "RESPONSE_TOO_LARGE")
                self.assert_worker_stopped()
            finally:
                self.wait_for_workers_cleanup()
