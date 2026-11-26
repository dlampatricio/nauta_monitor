"""Contrato de estado compacto y de solo lectura para integraciones locales."""

from __future__ import annotations

import json
import math
from pathlib import Path

from nauta_monitor.private_files import write_private_text


def write_snapshot(path: str | Path, snapshot: dict) -> None:
    """Publica el snapshot mediante reemplazo atómico, sin escrituras parciales."""
    payload = json.dumps(snapshot, ensure_ascii=False, allow_nan=False)
    write_private_text(path, payload + "\n")


def read_snapshot(path: str | Path) -> dict | None:
    """Lee una versión conocida del snapshot e ignora datos inválidos o ajenos."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
        if len(raw) > 4096:
            return None
        data = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        return None
    if data.get("result") not in ("ok", "error"):
        return None
    last_success = data.get("last_success_at")
    last_attempt = data.get("last_attempt_at")
    if type(last_attempt) is not int or last_attempt <= 0:
        return None
    if last_success is not None and (
        type(last_success) is not int or last_success <= 0 or last_success > last_attempt
    ):
        return None
    credit = data.get("credit_cup")
    hours = data.get("hours")
    for value in (credit, hours):
        if value is not None and (
            type(value) not in (int, float) or not math.isfinite(value) or value < 0
        ):
            return None
    if data.get("account_status") is not None and (
        not isinstance(data["account_status"], str) or len(data["account_status"]) > 256
    ):
        return None
    if type(data.get("stale_after_seconds")) is not int or data["stale_after_seconds"] < 1:
        return None
    if last_success is None:
        if data.get("result") != "error" or credit is not None or hours is not None:
            return None
    elif credit is None:
        return None
    return data
