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
            ], cwd=Path(__file__).resolve().parent.parent, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=os.name == "posix")
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
