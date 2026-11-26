"""Optional Linux/systemd user-service backend; the monitor itself is portable."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from nauta_monitor.security.credentials import config_path
from nauta_monitor.private_files import write_private_text


SERVICE_NAME = "nauta-monitor.service"


def _emit(message: str, *, error: bool = False, service_state: str | None = None) -> int:
    result = {"ok": not error, "message": message}
    if service_state is not None:
        result["service_state"] = service_state
    print(json.dumps(result, ensure_ascii=False))
    return 1 if error else 0


def _systemctl(*arguments: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["systemctl", "--user", *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(["systemctl", *arguments], 1, "", str(exc))


def _install_service() -> int:
    if sys.platform != "linux":
        return _emit("El servicio integrado requiere Linux con systemd de usuario.", error=True)
    executable_name = shutil.which("nauta-monitor")
    if not executable_name:
        return _emit("No se encontró nauta-monitor en PATH. Instala primero el entorno de la aplicación.", error=True)
    executable = Path(executable_name).resolve()
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    unit_path = config_home / "systemd" / "user" / SERVICE_NAME
    config = config_path()
    snapshot = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "nauta-monitor" / "status.json"
    try:
        snapshot.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(snapshot.parent, 0o700)
    except OSError:
        return _emit("No se pudo preparar el directorio privado de estado.", error=True)

    def quote(value: str) -> str:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%") + '"'

    command = " ".join(quote(arg) for arg in (
        str(executable), "--config", str(config), "watch",
        "--no-speedtest", "--snapshot", str(snapshot),
    ))
    unit = (
        "[Unit]\nDescription=Nauta Hogar balance monitor\n"
        "After=network-online.target\nWants=network-online.target\n\n"
        "[Service]\nType=simple\n"
        f"ExecStart={command}\n"
        "Restart=on-failure\nRestartSec=15\n"
        "UMask=0077\nNoNewPrivileges=true\n"
        "ProtectSystem=strict\nProtectHome=read-only\n"
        f"ReadWritePaths={quote(str(snapshot.parent))}\n\n"
        "[Install]\nWantedBy=default.target\n"
    )
    try:
        write_private_text(unit_path, unit)
    except OSError:
        return _emit("No se pudo instalar el servicio de usuario.", error=True)
    if _systemctl("daemon-reload").returncode:
        return _emit("systemd no pudo recargar el servicio de Nauta.", error=True)
    if _systemctl("enable", SERVICE_NAME).returncode:
        return _emit("No se pudo habilitar el servicio de usuario.", error=True)
    if _systemctl("restart", SERVICE_NAME).returncode:
        return _emit("No se pudo iniciar el servicio. Revisa que las credenciales sean válidas.", error=True)
    return _emit("Servicio instalado e iniciado.")


def _uninstall_service() -> int:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    unit_path = config_home / "systemd" / "user" / SERVICE_NAME
    loaded = _systemctl("show", SERVICE_NAME, "--property=LoadState", "--value")
    if loaded.returncode:
        return _emit("No está disponible systemd de usuario; no se modificó la configuración.", error=True)
    if loaded.stdout.strip() not in ("", "not-found"):
        result = _systemctl("disable", "--now", SERVICE_NAME)
        if result.returncode:
            return _emit("No se pudo detener ni deshabilitar el servicio.", error=True)
    try:
        unit_path.unlink(missing_ok=True)
    except OSError:
        return _emit("No se pudo quitar el archivo de servicio.", error=True)
    result = _systemctl("daemon-reload")
    if result.returncode:
        return _emit("systemd no pudo actualizar la lista de servicios.", error=True)
    return _emit("Servicio detenido y desinstalado.")


def _service_action(action: str) -> int:
    if sys.platform != "linux":
        return _emit("El control integrado del monitor requiere Linux con systemd de usuario.", error=True)
    if action == "install":
        return _install_service()
    if action == "uninstall":
        return _uninstall_service()
    if action in ("start", "stop"):
        loaded = _systemctl("show", SERVICE_NAME, "--property=LoadState", "--value")
        if loaded.returncode:
            return _emit("No está disponible systemd de usuario.", error=True)
        if loaded.stdout.strip() in ("", "not-found"):
            if action == "start":
                return _install_service()
            return _emit("Monitor detenido.")
    if action == "status":
        result = _systemctl("show", SERVICE_NAME, "--property=LoadState,ActiveState,SubState")
        if result.returncode:
            return _emit("No user service manager is available.", service_state="unknown")
        fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        state = fields.get("ActiveState", "unknown")
        if fields.get("LoadState") == "not-found":
            state = "not-installed"
        return _emit(f"User service is {state} ({fields.get('SubState', 'unknown')}).", service_state=state)
    action_args = {"start": ("start",), "stop": ("stop",), "restart": ("restart",)}
    result = _systemctl(*action_args[action], SERVICE_NAME)
    if result.returncode:
        return _emit(f"No se pudo ejecutar {action} para el monitor.", error=True)
    return _emit({"start": "Monitor iniciado.", "stop": "Monitor detenido.", "restart": "Monitor reiniciado."}[action])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nauta-monitor-service")
    parser.add_argument("action", choices=("install", "start", "stop", "restart", "status", "uninstall"))
    args = parser.parse_args(argv)
    return _service_action(args.action)


if __name__ == "__main__":
    raise SystemExit(main())
