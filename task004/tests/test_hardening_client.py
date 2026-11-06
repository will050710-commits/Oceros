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
