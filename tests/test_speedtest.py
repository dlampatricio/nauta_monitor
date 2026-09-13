from __future__ import annotations

import http.server
import threading

import pytest

from nauta_monitor.speedtest import LibreSpeedClient, SpeedtestError

CHUNK = 1024 * 1024  # 1 MiB


class SpeedHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args: str) -> None:
        pass

    def do_GET(self) -> None:
        if self.path.startswith("/garbage.php"):
            n = 1
            query = self.path.split("?", 1)[-1]
            try:
                n = int(query.split("ckSize=")[1])
            except (IndexError, ValueError):
                n = 1
            n = max(1, min(n, 10))
            total = n * CHUNK
            self.download_seen = total
            self.send_response(200)
            self.send_header("Content-Length", str(total))
            self.end_headers()
            for _ in range(n):
                self.wfile.write(b"a" * CHUNK)
        elif self.path.startswith("/empty.php"):
            self.send_response(200)
            self.send_header("Content-Length", "4")
            self.end_headers()
            self.wfile.write(b"ping")
        elif self.path.startswith("/getIP.php"):
            self.send_response(200)
            self.send_header("Content-Length", "7")
            self.end_headers()
            self.wfile.write(b"1.2.3.4")
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path.startswith("/empty.php"):
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            self.upload_seen = length
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_error(404)


@pytest.fixture(scope="module")
def speed_server():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), SpeedHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def get_client(url: str) -> LibreSpeedClient:
    return LibreSpeedClient(
        base_url=url,
        dl_url="garbage.php",
        ul_url="empty.php",
        ping_url="empty.php",
        get_ip_url="getIP.php",
        download_chunks=2,
        upload_kib=64,
        concurrent=1,
        max_duration=3.0,
    )


def test_speedtest_run(speed_server):
    result = get_client(speed_server).run()
    assert result.ping_ms is not None and result.ping_ms >= 0
    assert result.download_mbps > 0
    assert result.upload_mbps > 0
    assert result.ip == "1.2.3.4"
    assert speed_server is not None


def test_speedtest_error_on_unreachable():
    with pytest.raises(SpeedtestError):
        get_client("http://127.0.0.1:1").run()