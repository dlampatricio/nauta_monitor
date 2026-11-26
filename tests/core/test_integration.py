from __future__ import annotations

import http.server
import threading
from pathlib import Path

import pytest

from nauta_monitor.client import PortalInitError, SecurePortalClient

ASSETS = Path(__file__).parent / "assets"


class PortalHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args: str) -> None:
        pass

    def do_GET(self) -> None:
        if self.path == "/":
            body = (ASSETS / "login_page.html").read_text(encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        if self.path == "/EtecsaQueryServlet":
            body = (ASSETS / "user_info_connect.html").read_text(encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
        else:
            self.send_error(404)


@pytest.fixture(scope="module")
def portal_server():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), PortalHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_full_portal_flow(portal_server):
    client = SecurePortalClient(base_url=portal_server, timeout=10)
    portal = client.init_session()
    assert portal.csrf_hw == "1fe3ee0634195096337177a0994723fb"
    assert portal.wlan_user_ip == "10.190.20.96"
    account = client.query_account("user", "pass", portal)
    assert account.account_status == "Activa"
    assert account.credit == 37.82
    assert len(account.last_sessions) == 3


def test_init_error_when_portal_unreachable():
    client = SecurePortalClient(base_url="http://127.0.0.1:1", timeout=5)
    with pytest.raises(PortalInitError):
        client.init_session()