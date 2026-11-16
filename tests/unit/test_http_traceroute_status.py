"""Regression coverage for the bundled HTTP traceroute helper."""

import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

SCRIPT = Path(__file__).resolve().parents[2] / "owtf/data/tools/discovery/web/rev_proxy/HTTP-Traceroute.py"


def test_traceroute_handles_nonstandard_http_status():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(599, "Network Connect Timeout Error")
            self.end_headers()
            self.wfile.write(b"<title>proxy response</title>")

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "-t",
                "127.0.0.1",
                "-p",
                str(server.server_port),
                "-m",
                "GET",
                "-f",
                "1",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=10)

    assert result.returncode == 0, result.stderr
    assert "599 Network Connect Timeout Error" in result.stdout
