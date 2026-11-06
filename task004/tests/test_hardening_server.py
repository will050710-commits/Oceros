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
