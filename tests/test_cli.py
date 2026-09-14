from io import StringIO

import pytest
from rich.console import Console

from nauta_monitor.cli import (
    WatchState,
    _bar,
    _pulse,
    _sparkline,
    _watch_line,
    _watch_panel,
    build_parser,
)
from nauta_monitor.config import Config
from nauta_monitor.parser import AccountInfo
from nauta_monitor.speedtest import SpeedResult


def test_watch_line_initial():
    line = _watch_line(WatchState())
    assert "Iniciando..." in line


def test_watch_line_with_account():
    account = AccountInfo(account_status="Activa", credit=37.82)
    state = WatchState(account=account, hours=3.0256)
    line = _watch_line(state)
    assert "estado=Activa" in line
    assert "credito=37.82 CUP" in line
    assert "horas=3.03" in line


def test_watch_line_with_none_credit():
    state = WatchState(account=AccountInfo(), hours=None)
    line = _watch_line(state)
    assert "credito=N/A" in line
    assert "horas=N/A" in line


def test_watch_line_with_speed():
    account = AccountInfo(account_status="Activa", credit=37.82)
    speed = SpeedResult(download_mbps=35.5, upload_mbps=12.2, ping_ms=40.0)
    state = WatchState(account=account, hours=3.0, speed=speed)
    line = _watch_line(state)
    assert "desc=35.50 Mbps" in line
    assert "sub=12.20 Mbps" in line
    assert "ping=40.0 ms" in line


def test_watch_panel_renders():
    state = WatchState(account=AccountInfo(account_status="Activa", credit=37.82), hours=3.0)
    config = Config(username="u", password="p")
    out = StringIO()
    Console(file=out, force_terminal=False, width=80).print(
        _watch_panel(state, config, 3600, 1800)
    )
    assert "Nauta Hogar" in out.getvalue()
    assert "Horas" in out.getvalue()
    assert "3 h" in out.getvalue()
    assert "Crédito" in out.getvalue()


def test_watch_panel_minimal_rows():
    state = WatchState(account=AccountInfo(account_status="Activa", credit=37.82), hours=3.0)
    config = Config(username="u", password="p")
    out = StringIO()
    Console(file=out, force_terminal=False, width=80).print(
        _watch_panel(state, config, 3600, 0)
    )
    text = out.getvalue()
    assert "Expiración" not in text
    assert "Estado" not in text


def test_watch_panel_spinner_while_running():
    state = WatchState(account=AccountInfo(credit=37.82), hours=3.0, speedtest_running=True)
    config = Config(username="u", password="p")
    out = StringIO()
    Console(file=out, force_terminal=False, width=80).print(
        _watch_panel(state, config, 3600, 1800)
    )
    assert "Midiendo velocidad" in out.getvalue()


def test_pulse_alternates():
    assert _pulse(0.0) == "◉"
    assert _pulse(1.0) == "○"
    assert _pulse(2.0) == "◉"


def test_sparkline_flat():
    assert _sparkline([5.0, 5.0, 5.0]) == "▅▅▅"


def test_sparkline_trend():
    spark = _sparkline([1.0, 2.0, 3.0, 4.0])
    assert spark[0] in "▁▂▃"
    assert spark[-1] in "▆▇█"


def test_sparkline_wraps_width():
    values = list(range(30))
    assert len(_sparkline(values, width=16)) == 16


def test_bar():
    assert _bar(10, 10) == "▓" * 12
    assert _bar(0, 10) == "░" * 12
    assert _bar(5, 10) == "▓" * 6 + "░" * 6
    assert _bar(None, 10) == "░" * 12


def test_parser_defaults_to_watch():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.command is None


def test_parser_once_hidden_but_available():
    parser = build_parser()
    args = parser.parse_args(["once", "--json"])
    assert args.command == "once"
    assert args.json is True


def test_parser_history_removed():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["history"])