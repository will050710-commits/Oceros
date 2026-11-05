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
        return {
            "rss_peak_bytes": self.rss_peak_bytes,
            "commit_peak_bytes": self.commit_peak_bytes,
            "rss_source": "psutil simultaneous process-tree RSS samples",
            "commit_source": "psutil Windows private bytes" if self.commit_peak_bytes is not None else None,
            "commit_unavailable_reason": None if self.commit_peak_bytes is not None else "Windows private bytes unavailable on this platform",
            "sample_interval_s": self.interval_s, "samples": self.samples,
            "incomplete_samples": self.incomplete_samples,
            "measurement_scope": "mock server and descendants after health readiness; excludes harness and startup",
            "sampling_limitation": "Sampling can miss peaks between observations",
        }
