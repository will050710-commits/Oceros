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
