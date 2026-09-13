from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


class ConfigError(Exception):
    pass


@dataclass
class SpeedConfig:
    base_url: str = "http://speedtest.cd.etecsa.cu/"
    dl_url: str = "garbage.php"
    ul_url: str = "empty.php"
    ping_url: str = "empty.php"
    get_ip_url: str = "getIP.php"
    download_chunks: int = 200
    upload_kib: int = 1024
    concurrent: int = 3
    max_duration: float = 20.0


@dataclass
class AlertsConfig:
    min_balance_hours: float = 24.0
    on_alert: str | None = None


@dataclass
class Config:
    username: str
    password: str
    cup_per_hour: float = 12.5
    saldo_interval: int = 3600
    speedtest_interval: int = 1800
    history_path: str = "history.jsonl"
    speedtest: SpeedConfig = field(default_factory=SpeedConfig)
    alerts: AlertsConfig = field(default_factory=AlertsConfig)


def _merge(defaults: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    for key, value in user.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path | None = None) -> Config:
    path = Path(path) if path else Path("config.toml")
    defaults: dict[str, Any] = {
        "nauta": {"cup_per_hour": 12.5, "saldo_interval": 3600, "speedtest_interval": 1800},
        "speedtest": {
            "base_url": "http://speedtest.cd.etecsa.cu/",
            "dl_url": "garbage.php",
            "ul_url": "empty.php",
            "ping_url": "empty.php",
            "get_ip_url": "getIP.php",
            "download_chunks": 200,
            "upload_kib": 1024,
            "concurrent": 3,
            "max_duration": 20.0,
        },
        "alerts": {"min_balance_hours": 24.0, "on_alert": None},
    }
    if path.exists():
        user: dict[str, Any] = tomllib.loads(path.read_text(encoding="utf-8"))
    else:
        user = {}
    merged = _merge(defaults, user)

    nauta = merged["nauta"]
    username = nauta.get("username") or os.environ.get("NAUTA_USERNAME")
    password = nauta.get("password") or os.environ.get("NAUTA_PASS")

    speedtest = merged["speedtest"]
    alerts = merged["alerts"]
    return Config(
        username=username,
        password=password,
        cup_per_hour=float(nauta.get("cup_per_hour", 12.5)),
        saldo_interval=int(nauta.get("saldo_interval", 3600)),
        speedtest_interval=int(nauta.get("speedtest_interval", 1800)),
        history_path=str(nauta.get("history_path", "history.jsonl")),
        speedtest=SpeedConfig(
            base_url=speedtest.get("base_url", "http://speedtest.cd.etecsa.cu/"),
            dl_url=speedtest.get("dl_url", "garbage.php"),
            ul_url=speedtest.get("ul_url", "empty.php"),
            ping_url=speedtest.get("ping_url", "empty.php"),
            get_ip_url=speedtest.get("get_ip_url", "getIP.php"),
            download_chunks=int(speedtest.get("download_chunks", 200)),
            upload_kib=int(speedtest.get("upload_kib", 1024)),
            concurrent=int(speedtest.get("concurrent", 3)),
            max_duration=float(speedtest.get("max_duration", 20.0)),
        ),
        alerts=AlertsConfig(
            min_balance_hours=float(alerts.get("min_balance_hours", 24.0)),
            on_alert=alerts.get("on_alert"),
        ),
    )