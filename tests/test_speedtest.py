from __future__ import annotations

import http.server
import json
import re
import threading

import pytest

from nauta_monitor.speedtest import FastClient, SpeedtestError

CHUNK = 64 * 1024
SIZE = 100 * 1024 * 1024
RANGE_RE = re.compile(r"bytes=(\d+)-(\d*)")


class FastHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args: str) -> None:
        pass

    def _base(self) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def _json(self, payload: object) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.startswith("/netflix/speedtest/v2"):
            self._json(
                {
                    "client": {"ip": "1.2.3.4", "asn": "1", "location": {"city": "Habana"}},
                    "targets": [
                        {
                            "url": f"{self._base()}/speedtest",
                            "location": {"city": "Miami"},
                        }
                    ],
                }
            )
        elif self.path.startswith("/oca/speedtest"):
            self._json([{"url": f"{self._base()}/upload"}])
        elif self.path.startswith("/speedtest"):
            match = RANGE_RE.search(self.headers.get("Range", ""))
            start = int(match.group(1)) if match else 0
            length = 1 if match and match.group(2) == "0" else CHUNK
            end = start + length - 1
            self.send_response(206)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Range", f"bytes {start}-{end}/{SIZE}")
            self.send_header("Content-Length", str(length))
            self.end_headers()
            self.wfile.write(b"a" * length)
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if not self.path.startswith("/upload"):
            self.send_error(404)
            return
        # fast.com exige Content-Length: el modo chunked devuelve 406.
        length = self.headers.get("Content-Length")
        if length is None:
            self.send_error(406)
            return
        self.rfile.read(int(length))
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")


@pytest.fixture(scope="module")
def fast_server():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FastHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def get_client(url: str) -> FastClient:
    return FastClient(api_url=url, connections=2, max_duration=3, max_mb=5)


def test_fast_client_run(fast_server):
    result = get_client(fast_server).run()
    assert result.ping_ms is not None and result.ping_ms >= 0
    assert result.jitter_ms is not None and result.jitter_ms >= 0
    assert result.download_mbps > 0
    assert result.upload_mbps > 0
    assert result.ip == "1.2.3.4"
    assert result.server == "fast.com (Miami)"


def test_fast_client_error_on_unreachable():
    with pytest.raises(SpeedtestError):
        get_client("http://127.0.0.1:1").run()
