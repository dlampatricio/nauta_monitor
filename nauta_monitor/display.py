from __future__ import annotations

from rich.console import Console
from rich.table import Table

from nauta_monitor.calc import format_hours
from nauta_monitor.parser import AccountInfo
from nauta_monitor.speedtest import SpeedResult

console = Console()


def _speed_line(speed: SpeedResult | None) -> str:
    if speed is None:
        return "No medida todavía"
    parts = []
    if speed.download_mbps is not None:
        parts.append(f"Descarga: {speed.download_mbps:.2f} Mbps")
    if speed.upload_mbps is not None:
        parts.append(f"Subida: {speed.upload_mbps:.2f} Mbps")
    if speed.ping_ms is not None:
        parts.append(f"Ping: {speed.ping_ms:.1f} ms")
    return " | ".join(parts) if parts else "Sin datos"


def render_account(account: AccountInfo, hours: float, speed: SpeedResult | None = None) -> Table:
    table = Table(title="Nauta Hogar")
    table.add_column("Métrica", style="bold")
    table.add_column("Valor")
    table.add_row("Crédito", f"{account.credit:.2f} CUP" if account.credit is not None else "—")
    table.add_row("Horas", format_hours(hours))
    if speed is not None:
        table.add_row("Velocidad", _speed_line(speed))
    return table


def render_sessions(account: AccountInfo) -> Table:
    table = Table(title="Ultimas sesiones")
    table.add_column("Desde")
    table.add_column("Hasta")
    table.add_column("Tiempo")
    for session in account.last_sessions:
        start = session.start.strftime("%Y/%m/%d %H:%M:%S") if session.start else "—"
        end = session.end.strftime("%Y/%m/%d %H:%M:%S") if session.end else "—"
        duration = (
            f"{session.duration // 3600:02d}:{(session.duration % 3600) // 60:02d}:"
            f"{session.duration % 60:02d}"
            if session.duration is not None
            else "—"
        )
        table.add_row(start, end, duration)
    return table