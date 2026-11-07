"""Linux review regression: valid loopback response at a socket fd above 1023.

Usage: python high-fd-regression.py --client CLIENT_PY --config-root REPO
       --target-label baseline-or-candidate
The same assertion passes accepted source and fails the supplied candidate.
"""
import argparse
import importlib.util
import json
import platform
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


parser = argparse.ArgumentParser()
parser.add_argument("--client", required=True)
parser.add_argument("--config-root", required=True)
parser.add_argument("--target-label", required=True)
args = parser.parse_args()
sys.path.insert(0, args.config_root)
from task004.config import Config

spec = importlib.util.spec_from_file_location("review_client", args.client)
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)
body = json.dumps({
    "id": "synthetic", "choices": [{"text": "SYNTHETIC_OK"}],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    "evidence_label": "SYNTHETIC",
}).encode()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except OSError:
            pass


class HighFdRegression(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux review probe")
    def test_valid_response_succeeds_above_fd_setsize(self):
        import resource
        if resource.getrlimit(resource.RLIMIT_NOFILE)[0] < 1100:
            self.skipTest("open-file soft limit is too low for this probe")
        held = []
        server = thread = None
        try:
            for _ in range(1050):
                held.append(open("/dev/null", "rb"))
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            self.assertGreaterEqual(server.fileno(), 1024)
            print("server_socket_fd=" + str(server.fileno()), flush=True)
            thread = threading.Thread(
                target=lambda: server.serve_forever(poll_interval=.01))
            thread.start()
            try:
                result = client.request_synthetic(
                    f"http://127.0.0.1:{server.server_port}",
                    Config(n_ctx=1, timeout_s=2))
            except client.ClientError as exc:
                self.fail("VALID_HIGH_FD_RESPONSE_FAILED code=" + exc.code)
            self.assertEqual(result["synthetic_output_tokens"], 1)
            self.assertFalse(any(t.name == "task004-http"
                                 for t in threading.enumerate()))
        finally:
            if server is not None:
                if thread is not None:
                    server.shutdown()
                server.server_close()
            if thread is not None:
                thread.join(timeout=2)
            for item in held:
                item.close()


if __name__ == "__main__":
    print(json.dumps({"platform": platform.system(),
                      "python_version": platform.python_version(),
                      "target_label": args.target_label}), flush=True)
    unittest.main(argv=[sys.argv[0]], verbosity=2)
