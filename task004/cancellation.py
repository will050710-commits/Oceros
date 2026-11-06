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
