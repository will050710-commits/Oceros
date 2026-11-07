"""Bounded synthetic request, with total deadline and cancellation."""
import http.client
import io
import json
import queue
import select
import socket
import threading
import time
from urllib.parse import urlsplit

POLL_INTERVAL_S = 0.05


class ClientError(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class _CancellableSocketIO(io.RawIOBase):
    def __init__(self, sock, socket_lock, closing, cancel_event, deadline):
        super().__init__()
        self._sock = sock
        self._socket_lock = socket_lock
        self._closing = closing
        self._cancel_event = cancel_event
        self._deadline = deadline

    def readable(self):
        return True

    def fileno(self):
        return self._sock.fileno()

    def readinto(self, b):
        if self.closed:
            raise ValueError("I/O operation on closed file.")
        while True:
            if self._closing.is_set() or (self._cancel_event is not None and self._cancel_event.is_set()):
                raise ClientError("CANCELLED")
            remaining = self._deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("timed out")
            readable, _, _ = select.select([self._sock], [], [], min(POLL_INTERVAL_S, remaining))
            if self._closing.is_set() or (self._cancel_event is not None and self._cancel_event.is_set()):
                raise ClientError("CANCELLED")
            if self._deadline - time.monotonic() <= 0:
                raise TimeoutError("timed out")
            if readable:
                try:
                    return self._sock.recv_into(b)
                except (BlockingIOError, InterruptedError):
                    continue

    def close(self):
        try:
            if self._sock is not None:
                with self._socket_lock:
                    self._sock.close()
        finally:
            super().close()


class _BufferedSocketProxy:
    def __init__(self, raw_stream):
        self._raw_stream = raw_stream

    def makefile(self, mode):
        return io.BufferedReader(self._raw_stream)


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
    start = time.monotonic()
    deadline = start + config.timeout_s
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=config.timeout_s)
    results = queue.Queue(maxsize=1)
    closing = threading.Event()
    socket_lock = threading.Lock()
    connected_socket = [None]
    body = json.dumps({"prompt": "SYNTHETIC_INPUT", "max_tokens": config.max_new_tokens,
                       "temperature": 0, "seed": 1729, "n": 1, "thinking": False}).encode()

    def open_response(raw_sock, *args, **kwargs):
        conn.sock = None
        raw_sock.setblocking(False)
        stream = _CancellableSocketIO(raw_sock, socket_lock, closing, cancel_event, deadline)
        return http.client.HTTPResponse(_BufferedSocketProxy(stream), *args, **kwargs)

    def perform():
        response = None
        try:
            conn.connect()
            connected_socket[0] = conn.sock
            if closing.is_set() or (cancel_event is not None and cancel_event.is_set()):
                raise ClientError("CANCELLED")
            conn.response_class = open_response
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
            if connected_socket[0] is not None:
                with socket_lock:
                    connected_socket[0].close()
            conn.close()

    worker = threading.Thread(target=perform, daemon=True, name="task004-http")
    worker.start()
    primary = None
    try:
        while True:
            if cancel_event is not None and cancel_event.is_set():
                raise ClientError("CANCELLED")
            remaining = deadline - time.monotonic()
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
        with socket_lock:
            sock = connected_socket[0]
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
        worker.join(timeout=.5)
        if worker.is_alive() and primary is None:
            raise ClientError("CLIENT_CLEANUP_FAILED")
