from nauta_monitor.cli import WatchState, _watch_line
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