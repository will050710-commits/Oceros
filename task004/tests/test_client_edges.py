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
