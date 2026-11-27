"""Real process checks shipped with the independent maintenance bundle."""

from __future__ import annotations

import http.client
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

SERVER = """
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sys, time
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self):
        if self.path == '/slow': time.sleep(2)
        self.send_response(503 if self.path == '/business' else 200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        try: self.wfile.write(b'{"business":"unchanged"}')
        except BrokenPipeError: pass
    def do_HEAD(self):
        self.send_response(200); self.end_headers()
    def do_POST(self):
        with Path(sys.argv[2]).open('a') as log: log.write('POST\\n')
        self.send_response(201); self.end_headers()
HTTPServer.allow_reuse_address = True
HTTPServer(('127.0.0.1', int(sys.argv[1])), Handler).serve_forever()
"""


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_port(port: int) -> None:
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise AssertionError(f"process did not listen on {port}")


def stop(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def verify(nginx: str, exporter: Callable[[Path, str, str, str, int | None], None]) -> None:
    executable = shutil.which(nginx)
    if executable is None:
        raise ValueError("Nginx is required: install nginx or pass --nginx /absolute/path")
    with tempfile.TemporaryDirectory(prefix="foundation-maintenance-") as temporary:
        root = Path(temporary)
        edge_port, app_port = free_port(), free_port()
        while edge_port == app_port:
            app_port = free_port()
        target = root / "edge"
        exporter(target, f"http://127.0.0.1:{app_port}", f"127.0.0.1:{edge_port}", "테스트 서비스", 37)
        proxy = target / "proxy.conf"
        proxy.write_text(proxy.read_text().replace("proxy_read_timeout 60s;", "proxy_read_timeout 1s;"))
        log = root / "writes.log"
        app = subprocess.Popen([sys.executable, "-c", SERVER, str(app_port), str(log)])
        edge: subprocess.Popen[bytes] | None = None

        def request(
            path: str = "/", method: str = "GET", accept: str = "text/html"
        ) -> tuple[int, dict[str, str], bytes]:
            connection = http.client.HTTPConnection("127.0.0.1", edge_port, timeout=5)
            try:
                connection.request(method, path, headers={"Accept": accept})
                response = connection.getresponse()
                return response.status, {k.lower(): v for k, v in response.getheaders()}, response.read()
            finally:
                connection.close()

        def unavailable(path: str = "/", method: str = "GET", html: bool = True) -> None:
            status, headers, body = request(path, method)
            assert status == 503, (path, method, status, body)
            assert headers["cache-control"] == "no-store", headers
            assert headers["retry-after"] == "37", headers
            assert headers["content-type"].startswith("text/html" if html else "application/problem+json"), (
                headers
            )
            assert b"nginx/" not in body and b"127.0.0.1" not in body
            if method == "HEAD":
                assert body == b""
            elif html:
                assert "잠시 이용할 수 없습니다" in body.decode()
                assert "<script" not in body.decode() and 'href="http' not in body.decode()
            else:
                assert json.loads(body)["code"] == "SERVICE_UNAVAILABLE"

        try:
            wait_port(app_port)
            command = [executable, "-p", str(target) + "/", "-e", "stderr", "-c", str(target / "nginx.conf")]
            subprocess.run([*command, "-t"], check=True)
            with (root / "nginx-output.log").open("wb") as output:
                edge = subprocess.Popen([*command, "-g", "daemon off;"], stdout=output, stderr=output)
            wait_port(edge_port)
            assert request()[0] == 200
            assert request("/business")[2] == b'{"business":"unchanged"}'
            assert request("/business")[0] == 503  # application error is not replaced
            assert request("/", "POST")[0] == 201
            assert log.read_text().splitlines() == ["POST"]
            unavailable("/slow")  # real upstream timeout
            stop(app)  # actual backend process down; proxy stays up
            unavailable()
            unavailable("/", "HEAD")
            unavailable("/", "POST", html=False)
            for path in [
                "/api/orders",
                "/api",
                "/actuator/health",
                "/readyz",
                "/race-rooms",
                "/%61pi/orders",
            ]:
                unavailable(path, html=False)
            assert request(accept="application/json")[1]["content-type"].startswith(
                "application/problem+json"
            )
            app = subprocess.Popen([sys.executable, "-c", SERVER, str(app_port), str(log)])
            wait_port(app_port)
            assert request()[0] == 200
            (target / "maintenance.flag").touch()
            unavailable()
            unavailable("/api/orders", html=False)
            unavailable("/", "POST", html=False)
            assert log.read_text().splitlines() == ["POST"], "maintenance must not send writes upstream"
            (target / "maintenance.flag").unlink()
            assert request()[0] == 200
            assert request("/__foundation_unavailable.html")[0] == 404, "fallback must be internal"
            # Omitted Retry-After stays omitted; no implicit recovery-time promise.
            other = root / "no-retry"
            exporter(other, f"http://127.0.0.1:{app_port}", f"127.0.0.1:{free_port()}", "service", None)
            assert "Retry-After" not in (other / "server.conf").read_text()
        except BaseException:
            if (target / "error.log").exists():
                print((target / "error.log").read_text()[-5000:], file=sys.stderr)
            raise
        finally:
            if edge is not None:
                stop(edge)
            stop(app)
    print(
        "PASS real Nginx: backend stop/recovery, timeout, planned mode, HTML/JSON, original methods, no write replay"
    )
