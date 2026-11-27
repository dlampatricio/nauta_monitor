from datetime import date, datetime, timedelta
from io import StringIO

import pytest
from rich.console import Console
from rich.text import Text

from nauta_monitor.cli import (
    WatchState,
    _consumption_by_day,
    _consumption_rate,
    _days_left,
    _watch_line,
    _watch_panel,
    _watch_settings,
    _week_chart,
    build_parser,
)
from nauta_monitor.config import Config
from nauta_monitor.parser import AccountInfo
from nauta_monitor.speedtest import SpeedResult


def _render(state: WatchState) -> str:
    out = StringIO()
    Console(file=out, force_terminal=False, width=120).print(_watch_panel(state))
    return out.getvalue()


def _epoch(year, month, day, hour=0, minute=0):
    return datetime(year, month, day, hour, minute).timestamp()


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


def test_watch_panel_basic_rows():
    state = WatchState(account=AccountInfo(account_status="Activa", credit=37.82), hours=3.0)
    text = _render(state)
    assert "Nauta" in text
    assert "Crédito" in text
    assert "Horas" in text
    assert "3 h" in text
    assert "Aún sin historial suficiente" in text


def test_watch_panel_no_legacy_gadgets():
    state = WatchState(account=AccountInfo(credit=37.82), hours=3.0)
    state.history = [
        (_epoch(2026, 9, 7, 8), 25.0),
        (_epoch(2026, 9, 7, 9), 24.0),
        (_epoch(2026, 9, 7, 10), 23.0),
        (_epoch(2026, 9, 8, 8), 21.0),
        (_epoch(2026, 9, 8, 9), 20.0),
        (_epoch(2026, 9, 9, 8), 18.0),
        (_epoch(2026, 9, 9, 9), 17.0),
    ]
    state.speed = SpeedResult(download_mbps=1.08, upload_mbps=0.36, ping_ms=62.3)
    text = _render(state)
    assert "Expiración" not in text
    assert "Saldo en" not in text
    assert "Velocidad en" not in text
    assert "◉" not in text
    assert "▓" not in text
    assert "▁" not in text
    assert "Consumo" in text


def test_watch_panel_velocity_only_arrows():
    state = WatchState(
        account=AccountInfo(credit=37.82),
        hours=3.0,
        speed=SpeedResult(download_mbps=1.08, upload_mbps=0.36, ping_ms=62.3),
    )
    text = _render(state)
    assert "↓ 1.08" in text
    assert "↑ 0.36" in text
    assert "62" not in text


def test_watch_panel_measuring_static():
    state = WatchState(account=AccountInfo(credit=37.82), hours=3.0, speedtest_running=True)
    text = _render(state)
    assert "Midiendo velocidad" in text


def test_consumption_by_day_aggregates_and_skips_gaps():
    history = [
        (_epoch(2026, 9, 7, 8), 30.0),
        (_epoch(2026, 9, 7, 9), 29.5),   # +0.5 (lunes)
        (_epoch(2026, 9, 7, 10), 29.0),  # +0.5 (lunes)
        (_epoch(2026, 9, 9, 8), 20.0),   # salto >2h: se ignora
        (_epoch(2026, 9, 9, 9), 19.5),   # +0.5 (miércoles)
    ]
    by_day = _consumption_by_day(history)
    assert by_day[date(2026, 9, 7)] == pytest.approx(1.0)
    assert by_day.get(date(2026, 9, 8)) is None
    assert by_day[date(2026, 9, 9)] == pytest.approx(0.5)


def test_consumption_by_day_ignores_topups():
    history = [
        (_epoch(2026, 9, 7, 8), 5.0),
        (_epoch(2026, 9, 7, 9), 25.0),  # recarga: horas suben -> sin gasto
    ]
    by_day = _consumption_by_day(history)
    assert by_day == {}


def test_consumption_rate_none_with_single_day():
    assert _consumption_rate({date(2026, 9, 7): 1.0}) is None
    assert _consumption_rate({}) is None


def test_consumption_rate_average_over_week():
    by_day = {
        date(2026, 9, 7): 2.0,
        date(2026, 9, 8): 3.0,
        date(2026, 9, 9): 2.0,
    }
    assert _consumption_rate(by_day) == pytest.approx(1.0)  # 7h / 7 días


def test_days_left():
    assert "≈ 6 días" in _days_left(17.6, 2.8)[0]
    assert "≈ 1 día" in _days_left(1.5, 2.0)[0]
    assert "fin ~" not in _days_left(17.6, 2.8)[0]
    assert _days_left(10.0, None)[0] == "Aún sin historial suficiente"
    assert _days_left(None, 2.0)[0] == "Aún sin historial suficiente"
    assert _days_left(10.0, 0.0)[0] == "Sin consumo reciente"


def test_watch_panel_has_no_status_footer():
    state = WatchState(account=AccountInfo(credit=37.82), hours=3.0)
    text = _render(state)
    assert "Actualizado:" not in text
    assert "Saldo actualizado" not in text


def test_watch_panel_end_date_not_duplicated():
    state = WatchState(account=AccountInfo(credit=960.4), hours=100.0)
    state.history = [
        (_epoch(2026, 9, 7, 8), 30.0),
        (_epoch(2026, 9, 7, 9), 29.0),
        (_epoch(2026, 9, 8, 8), 20.0),
        (_epoch(2026, 9, 8, 9), 19.0),
    ]
    rate = _consumption_rate(_consumption_by_day(state.history))
    _, end_date = _days_left(state.hours, rate)
    assert end_date is not None
    assert _render(state).count(end_date) == 1


def test_watch_panel_shows_speed_error():
    state = WatchState(
        account=AccountInfo(credit=37.82),
        hours=3.0,
        speed_error="No se pudo contactar con fast.com (https://api.fast.com): timeout",
    )
    text = _render(state)
    assert "⚠" in text
    assert "Sin conexión a fast.com" in text


def test_week_chart_has_seven_days():
    by_day = {datetime.now().date(): 4.1}
    lines = _week_chart(by_day)
    assert len(lines) == 7
    plain = [Text.from_markup(line).plain for line in lines]
    labels = [line.split()[0] for line in plain]
    assert set(labels) == {"Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"}
    peak_line = plain[-1]
    assert "4.1" in peak_line
    assert "█" in peak_line


def test_parser_defaults_to_watch():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.command is None
    # Sin subcomando se ejecuta `watch`: su namespace debe estar completo.
    assert args.interval is None
    assert args.speedtest_interval is None
    assert args.no_speedtest is False
    assert args.history is None


def test_parser_status_options():
    parser = build_parser()
    args = parser.parse_args(["status", "--json"])
    assert args.command == "status"
    assert args.json is True


def test_parser_removed_commands():
    parser = build_parser()
    for command in ("once", "history"):
        with pytest.raises(SystemExit):
            parser.parse_args([command])


def test_watch_settings_use_config_by_default():
    config = Config(
        username="u",
        password="p",
        saldo_interval=3600,
        speedtest_interval=1800,
        history_path="history.jsonl",
    )
    args = build_parser().parse_args([])
    assert _watch_settings(config, args) == (3600, 1800, "history.jsonl")


def test_watch_settings_flags_override_config():
    config = Config(username="u", password="p")
    args = build_parser().parse_args(
        ["watch", "--interval", "60", "--speedtest-interval", "120", "--history", "h.jsonl"]
    )
    assert _watch_settings(config, args) == (60, 120, "h.jsonl")

    args = build_parser().parse_args(["watch", "--no-speedtest"])
    assert _watch_settings(config, args) == (config.saldo_interval, 0, config.history_path)
