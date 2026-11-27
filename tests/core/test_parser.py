from pathlib import Path

from nauta_monitor.client import SecurePortalClient
from nauta_monitor.parser import (
    parse_account_info,
    parse_credit,
    parse_datetime,
    parse_duration,
    find_error,
)

ASSETS = Path(__file__).parent / "assets"


def test_parse_credit():
    assert parse_credit("37.82 CUP") == 37.82
    assert parse_credit("$59,02 CUP") == 59.02
    assert parse_credit("No especificada") is None
    assert parse_credit("") is None


def test_parse_datetime():
    parsed = parse_datetime("2022/05/21 07:07:17")
    assert parsed is not None
    assert (parsed.year, parsed.month, parsed.day) == (2022, 5, 21)
    assert (parsed.hour, parsed.minute, parsed.second) == (7, 7, 17)
    assert parse_datetime("nada") is None


def test_parse_duration():
    assert parse_duration("00:08:25") == 505
    assert parse_duration("01:02:03") == 3723
    assert parse_duration(None) is None


def test_parse_account_info_fixture():
    html = (ASSETS / "user_info_connect.html").read_text(encoding="utf-8")
    info = parse_account_info(html)
    assert info.account_status == "Activa"
    assert info.credit == 37.82
    assert len(info.last_sessions) == 3
    first = info.last_sessions[0]
    assert first.duration == 505
    assert first.start is not None
    assert first.end is not None


def test_find_error():
    assert find_error('<script>alert("Usuario o contraseña incorrectos")</script>') == (
        "Usuario o contraseña incorrectos"
    )
    assert find_error("<html><body>ok</body></html>") is None


def test_extract_form_fixture():
    html = (ASSETS / "login_page.html").read_text(encoding="utf-8")
    form = SecurePortalClient._extract_form(html)
    assert form is not None
    assert form["CSRFHW"] == "1fe3ee0634195096337177a0994723fb"
    assert form["wlanuserip"] == "10.190.20.96"