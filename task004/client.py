"""Bounded synthetic request, with total deadline and cancellation."""
import http.client
import json
import queue
import socket
import threading
import time
from urllib.parse import urlsplit


class ClientError(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


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
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=config.timeout_s)
    results = queue.Queue(maxsize=1)
    closing = threading.Event()
    connected_socket = [None]
    body = json.dumps({"prompt": "SYNTHETIC_INPUT", "max_tokens": config.max_new_tokens,
                       "temperature": 0, "seed": 1729, "n": 1, "thinking": False}).encode()

    def perform():
        response = None
        try:
            conn.connect()
            connected_socket[0] = conn.sock
            if closing.is_set():
                raise ClientError("CANCELLED")
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
            conn.close()

    start = time.monotonic()
    worker = threading.Thread(target=perform, daemon=True, name="task004-http")
    worker.start()
    try:
        while True:
            if cancel_event is not None and cancel_event.is_set():
                raise ClientError("CANCELLED")
            remaining = config.timeout_s - (time.monotonic() - start)
            if remaining <= 0:
                raise ClientError("TIMEOUT")
            try:
                error = results.get(timeout=min(.02, remaining))
            except queue.Empty:
                continue
            if error is not None:
                raise error
            return {"request_latency_s": time.monotonic() - start, "synthetic_output_tokens": 1}
    finally:
        closing.set()
        sock = connected_socket[0]
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        worker.join(timeout=.5)
        if worker.is_alive():
            raise ClientError("CLIENT_CLEANUP_FAILED")
