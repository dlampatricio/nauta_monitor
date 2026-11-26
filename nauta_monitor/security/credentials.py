"""Portable user-level credential management, separate from service control."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from nauta_monitor.private_files import write_private_text

def config_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "nauta-monitor" / "config.toml"


def _emit(
    message: str,
    *,
    error: bool = False,
    credentials_state: str | None = None,
) -> int:
    result = {"ok": not error, "message": message}
    if credentials_state is not None:
        result["credentials_state"] = credentials_state
    print(json.dumps(result, ensure_ascii=False))
    return 1 if error else 0


def _toml_module():
    try:
        import tomllib
    except ImportError:  # pragma: no cover - Python 3.9/3.10
        import tomli as tomllib
    return tomllib


def _inline_comment(line: str, start: int) -> str:
    quote: str | None = None
    escaped = False
    for index in range(start, len(line)):
        char = line[index]
        if quote == '"':
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quote = None
        elif quote == "'":
            if char == "'":
                quote = None
        elif char in ('"', "'"):
            quote = char
        elif char == "#":
            whitespace_start = index
            while whitespace_start > start and line[whitespace_start - 1] in (" ", "\t"):
                whitespace_start -= 1
            return line[whitespace_start:]
    return ""


def _update_credentials(
    username: str | None = None,
    password: str | None = None,
    *,
    success_message: str | None = "Credenciales guardadas en un archivo privado.",
) -> int:
    path = config_path()
    if not path.exists() and username is None and password is None:
        return 0
    try:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        data = _toml_module().loads(text)
    except (OSError, ValueError):
        return _emit("La configuración existente no es válida; no se sobrescribió.", error=True)
    if not isinstance(data.get("nauta", {}), dict):
        return _emit("La sección [nauta] existente no es válida.", error=True)

    lines = text.splitlines(keepends=True)
    section = next((i for i, line in enumerate(lines) if line.strip() == "[nauta]"), None)
    if section is None:
        if text and not text.endswith("\n"):
            text += "\n"
        text += "\n[nauta]\n"
        lines = text.splitlines(keepends=True)
        section = len(lines) - 1
    section_end = next(
        (i for i in range(section + 1, len(lines)) if lines[i].lstrip().startswith("[")),
        len(lines),
    )

    replacements = {
        key: json.dumps(value, ensure_ascii=False)
        for key, value in (("username", username), ("password", password))
        if value is not None
    }
    found: set[str] = set()
    for index in range(section + 1, section_end):
        match = re.match(r"^(\s*)(username|password)(\s*=\s*).*$", lines[index])
        if not match:
            continue
        key = match.group(2)
        if key in replacements:
            comment = _inline_comment(lines[index], match.end(3))
            spacing = " " if comment and not comment.startswith((" ", "\t")) else ""
            ending = "\r\n" if lines[index].endswith("\r\n") else "\n"
            lines[index] = (
                f"{match.group(1)}{key}{match.group(3)}{replacements[key]}"
                f"{spacing}{comment or ending}"
            )
        else:
            lines[index] = ""
        found.add(key)
    additions = [
        f"{key} = {value}\n"
        for key, value in replacements.items()
        if value is not None and key not in found
    ]
    lines[section + 1:section + 1] = additions
    updated = "".join(lines)
    try:
        _toml_module().loads(updated)
    except ValueError:
        return _emit("No se pudo actualizar [nauta] de forma segura.", error=True)
    try:
        write_private_text(path, updated)
    except OSError:
        return _emit("No se pudo guardar la configuración privada.", error=True)
    return _emit(success_message) if success_message is not None else 0


def save_from_stdin() -> int:
    try:
        line = sys.stdin.readline(4097)
        if len(line) > 4096:
            return _emit("La solicitud de credenciales excede el tamaño permitido.", error=True)
        data = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _emit("No se recibieron credenciales válidas.", error=True)
    if not isinstance(data, dict):
        return _emit("No se recibieron credenciales válidas.", error=True)
    username, password = data.get("username"), data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return _emit("Completa usuario y contraseña.", error=True)
    username, password = username.strip(), password
    if not username or not password or len(username) > 254 or len(password) > 1024:
        return _emit("Completa usuario y contraseña (máximo 1024 caracteres).", error=True)
    return _update_credentials(username, password)


def status() -> int:
    path = config_path()
    if not path.is_file():
        return _emit("No hay credenciales configuradas.", credentials_state="not-configured")
    try:
        data = _toml_module().loads(path.read_text(encoding="utf-8"))
        ready = bool(data.get("nauta", {}).get("username") and data.get("nauta", {}).get("password"))
    except (OSError, ValueError, TypeError, AttributeError):
        ready = False
    return _emit(
        "Credenciales configuradas." if ready else "La configuración necesita revisión.",
        credentials_state="configured" if ready else "invalid",
    )


def remove() -> int:
    result = _update_credentials(username="", password="", success_message=None)
    if result:
        return result
    # Empty TOML strings mean unset to the app's legacy configuration loader.
    return _emit("Credenciales eliminadas.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nauta-monitor-credentials")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("save")
    commands.add_parser("remove")
    args = parser.parse_args(argv)
    if args.command == "status":
        return status()
    if args.command == "save":
        return save_from_stdin()
    return remove()


if __name__ == "__main__":
    raise SystemExit(main())
