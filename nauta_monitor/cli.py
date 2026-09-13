from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import threading
import time
from contextlib import nullcontext
from dataclasses import dataclass, field
from datetime import datetime

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from nauta_monitor import __version__
from nauta_monitor.calc import format_hours, hours_from_credit
from nauta_monitor.client import PortalError, SecurePortalClient
from nauta_monitor.config import Config, ConfigError, load_config
from nauta_monitor.display import console, print_history, render_account, render_sessions
from nauta_monitor.history import append_sample, load_recent
from nauta_monitor.parser import AccountInfo, parse_account_info
from nauta_monitor.speedtest import LibreSpeedClient, SpeedResult, SpeedtestError

_EXIT_OK = 0
_EXIT_ERROR = 1
_EXIT_CONFIG = 2


@dataclass
class WatchState:
    account: AccountInfo | None = None
    hours: float | None = None
    speed: SpeedResult | None = None
    last_saldo_at: float = 0.0
    last_speedtest_at: float = 0.0
    status: str = "Iniciando..."
    alerted: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nauta-monitor",
        description="Monitor de cuenta Nauta Hogar: saldo, horas restantes y velocidad real.",
    )
    parser.add_argument("--version", action="version", version=f"nauta-monitor {__version__}")
    parser.add_argument(
        "--config", default=None, help="Ruta al archivo de configuración (por defecto: config.toml)."
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Muestra el HTML crudo de la consulta para depurar."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    once = subparsers.add_parser("once", help="Ejecuta una única consulta y sale.")
    once.add_argument("--json", action="store_true", help="Imprime el resultado en JSON (para scripts).")
    once.add_argument("--no-speedtest", action="store_true", help="Omite la prueba de velocidad.")
    once.add_argument("--no-history", action="store_true", help="No guarda la muestra en el historial.")

    watch = subparsers.add_parser("watch", help="Bucle continuo con panel en vivo.")
    watch.add_argument("--interval", type=int, default=None, help="Segundos entre consultas de saldo.")
    watch.add_argument(
        "--speedtest-interval", type=int, default=None, help="Segundos entre pruebas de velocidad."
    )
    watch.add_argument("--no-speedtest", action="store_true", help="Desactiva las pruebas de velocidad.")
    watch.add_argument("--history", default=None, help="Ruta del archivo de historial.")

    history = subparsers.add_parser("history", help="Muestra últimas muestras guardadas.")
    history.add_argument("--limit", type=int, default=20, help="Número de muestras a mostrar (por defecto: 20).")
    history.add_argument("--history", default=None, help="Ruta del archivo de historial.")

    return parser


def _account_to_dict(account: AccountInfo, hours: float | None, speed: SpeedResult | None) -> dict:
    return {
        "account_status": account.account_status,
        "credit_cup": account.credit,
        "hours": hours,
        "expiration_date": account.expiration_date,
        "access_areas": account.access_areas,
        "last_sessions": [
            {
                "start": session.start.isoformat() if session.start else None,
                "end": session.end.isoformat() if session.end else None,
                "duration_seconds": session.duration,
            }
            for session in account.last_sessions
        ],
        "speed": {
            "download_mbps": speed.download_mbps if speed else None,
            "upload_mbps": speed.upload_mbps if speed else None,
            "ping_ms": speed.ping_ms if speed else None,
            "jitter_ms": speed.jitter_ms if speed else None,
            "server": speed.server if speed else None,
            "ip": speed.ip if speed else None,
        },
    }


def _speed_text(speed: SpeedResult | None) -> str:
    if speed is None:
        return "Midiendo..."
    parts = []
    if speed.download_mbps is not None:
        parts.append(f"Desc. {speed.download_mbps:.2f} Mbps")
    if speed.upload_mbps is not None:
        parts.append(f"Sub. {speed.upload_mbps:.2f} Mbps")
    if speed.ping_ms is not None:
        parts.append(f"Ping {speed.ping_ms:.1f} ms")
    return " | ".join(parts)


def _run_speedtest(config: Config) -> SpeedResult:
    s = config.speedtest
    client = LibreSpeedClient(
        base_url=s.base_url,
        dl_url=s.dl_url,
        ul_url=s.ul_url,
        ping_url=s.ping_url,
        get_ip_url=s.get_ip_url,
        download_chunks=s.download_chunks,
        upload_kib=s.upload_kib,
        concurrent=s.concurrent,
        max_duration=s.max_duration,
    )
    return client.run()


def _sample_dict(config: Config, state: WatchState) -> dict:
    return {
        "username": config.username,
        "account_status": state.account.account_status if state.account else None,
        "credit": state.account.credit if state.account else None,
        "hours": state.hours,
        "download_mbps": state.speed.download_mbps if state.speed else None,
        "upload_mbps": state.speed.upload_mbps if state.speed else None,
        "ping_ms": state.speed.ping_ms if state.speed else None,
    }


def command_once(config: Config, args: argparse.Namespace) -> int:
    client = SecurePortalClient()
    try:
        portal = client.init_session()
        raw = client.query_account_raw(config.username, config.password, portal)
    except PortalError as exc:
        console.print(f"[red]{exc}[/red]")
        return _EXIT_ERROR
    if args.verbose:
        console.print(f"[dim]--- HTML ---\n{raw}\n--- (fin) ---[/dim]")

    account = parse_account_info(raw)
    hours = hours_from_credit(account.credit, config.cup_per_hour)
    speed = None
    if not args.no_speedtest and config.speedtest_interval > 0:
        try:
            speed = _run_speedtest(config)
        except SpeedtestError as exc:
            console.print(f"[yellow]Speedtest: {exc}[/yellow]")

    if args.json:
        console.print_json(json.dumps(_account_to_dict(account, hours, speed)))
    else:
        console.print(render_account(account, hours, speed))
        if account.last_sessions:
            console.print()
            console.print(render_sessions(account))

    if not args.no_history:
        state = WatchState(account=account, hours=hours, speed=speed)
        append_sample(config.history_path, _sample_dict(config, state))
    return _EXIT_OK


def _refresh_saldo(config: Config, state: WatchState) -> None:
    client = SecurePortalClient()
    try:
        portal = client.init_session()
        account = client.query_account(config.username, config.password, portal)
        state.account = account
        state.hours = hours_from_credit(account.credit, config.cup_per_hour)
        state.status = "Saldo actualizado"
    except PortalError as exc:
        state.status = f"Error al consultar saldo: {exc}"


def _refresh_speedtest(config: Config, state: WatchState, on_done=None) -> None:
    try:
        state.speed = _run_speedtest(config)
        state.status = "Speedtest completado"
    except SpeedtestError as exc:
        state.status = f"Speedtest falló: {exc}"
    if on_done is not None:
        on_done(state)


def _check_alert(config: Config, state: WatchState, out: Console = console) -> None:
    if state.hours is None:
        return
    low = state.hours <= config.alerts.min_balance_hours
    if low and not state.alerted:
        state.alerted = True
        message = f"Nauta: quedan {format_hours(state.hours)} ({state.hours:.1f} h)"
        out.print(f"[bold red]{message}[/bold red]")
        if config.alerts.on_alert:
            try:
                subprocess.Popen(shlex.split(config.alerts.on_alert))
            except OSError:
                pass
    elif not low:
        state.alerted = False


def _countdown(now: float, last: float, interval: int) -> int:
    return max(0, int(interval - (now - last)))


def _watch_line(state: WatchState) -> str:
    parts = [f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"]
    if state.account is not None:
        parts.append(f"estado={state.account.account_status or 'desconocido'}")
        parts.append(
            f"credito={state.account.credit:.2f} CUP"
            if state.account.credit is not None
            else "credito=N/A"
        )
        parts.append(f"horas={state.hours:.2f}" if state.hours is not None else "horas=N/A")
    speed = state.speed
    if speed is not None:
        if speed.download_mbps is not None:
            parts.append(f"desc={speed.download_mbps:.2f} Mbps")
        if speed.upload_mbps is not None:
            parts.append(f"sub={speed.upload_mbps:.2f} Mbps")
        if speed.ping_ms is not None:
            parts.append(f"ping={speed.ping_ms:.1f} ms")
    if state.status:
        parts.append(state.status)
    return " ".join(parts)


def _watch_panel(state: WatchState, config: Config, saldo_interval: int, speedtest_interval: int) -> Panel:
    now = time.time()
    saldo_in = _countdown(now, state.last_saldo_at, saldo_interval)
    parts = [f"Saldo en {saldo_in // 60:02d}:{saldo_in % 60:02d}"]
    if speedtest_interval > 0:
        speed_in = _countdown(now, state.last_speedtest_at, speedtest_interval)
        parts.append(f"Velocidad en {speed_in // 60:02d}:{speed_in % 60:02d}")
    status = f"{state.status} | {' | '.join(parts)}"

    if state.account is None:
        return Panel(status, title="Nauta Hogar Monitor", expand=False)

    table = Table(show_header=False, box=None)
    table.add_column(style="bold", no_wrap=True)
    table.add_column()
    account = state.account
    table.add_row("Estado", account.account_status or "—")
    table.add_row("Crédito", f"{account.credit:.2f} CUP" if account.credit is not None else "—")
    table.add_row(
        "Horas restantes",
        f"{state.hours:.1f} h ({format_hours(state.hours)})" if state.hours is not None else "—",
    )
    table.add_row("Expiración", account.expiration_date or "—")
    table.add_row("Velocidad", _speed_text(state.speed))
    table.add_row("Estado", status)
    return Panel(table, title="Nauta Hogar Monitor", expand=False)


def command_watch(config: Config, args: argparse.Namespace) -> int:
    saldo_interval = args.interval if args.interval else config.saldo_interval
    speedtest_interval = 0 if args.no_speedtest else config.speedtest_interval
    if args.speedtest_interval is not None:
        speedtest_interval = args.speedtest_interval

    interactive = sys.stdout.isatty()
    out = console if interactive else Console(color_system=None)
    on_done = (lambda state: out.print(_watch_line(state))) if not interactive else None

    state = WatchState()
    _refresh_saldo(config, state)
    if state.account is not None:
        append_sample(config.history_path, _sample_dict(config, state))
        _check_alert(config, state, out=out)
    if not interactive:
        out.print(_watch_line(state))
    state.last_saldo_at = time.time()
    if speedtest_interval > 0:
        threading.Thread(
            target=_refresh_speedtest, args=(config, state), kwargs={"on_done": on_done}, daemon=True
        ).start()
    state.last_speedtest_at = time.time()

    live_ctx = (
        Live(
            lambda: _watch_panel(state, config, saldo_interval, speedtest_interval),
            console=console,
            refresh_per_second=1,
            screen=True,
        )
        if interactive
        else nullcontext()
    )

    try:
        with live_ctx:
            while True:
                now = time.time()
                if now - state.last_saldo_at >= saldo_interval:
                    state.last_saldo_at = now
                    _refresh_saldo(config, state)
                    if state.account is not None:
                        append_sample(config.history_path, _sample_dict(config, state))
                        _check_alert(config, state, out=out)
                    if not interactive:
                        out.print(_watch_line(state))
                if speedtest_interval > 0 and now - state.last_speedtest_at >= speedtest_interval:
                    state.last_speedtest_at = now
                    threading.Thread(
                        target=_refresh_speedtest,
                        args=(config, state),
                        kwargs={"on_done": on_done},
                        daemon=True,
                    ).start()
                time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitor detenido.[/yellow]")
    return _EXIT_OK


def command_history(config: Config, args: argparse.Namespace) -> int:
    history_path = args.history or config.history_path
    entries = load_recent(history_path, limit=args.limit)
    if not entries:
        console.print("No hay muestras guardadas todavía.")
        return _EXIT_OK
    print_history(entries)
    return _EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        console.print(f"[red]{exc}[/red]")
        return _EXIT_CONFIG

    if args.command == "history":
        return command_history(config, args)

    if not config.username or not config.password:
        console.print(
            "[red]Faltan credenciales. Defínelas en el archivo de configuración "
            "o con las variables de entorno NAUTA_USERNAME / NAUTA_PASS.[/red]"
        )
        return _EXIT_CONFIG

    if args.command == "once":
        return command_once(config, args)
    if args.command == "watch":
        return command_watch(config, args)
    return _EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())