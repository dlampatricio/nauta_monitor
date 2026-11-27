import json
import subprocess
import sys

import pytest
from nauta_monitor.platform.linux import systemd_service

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux/systemd integration tests")

def test_service_unit_uses_absolute_monitor_path_and_private_snapshot(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(
        systemd_service.shutil,
        "which",
        lambda _: "/opt/nauta app/bin/nauta-monitor",
    )
    calls = []

    def systemctl(*args):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(systemd_service, "_systemctl", systemctl)
    assert systemd_service._install_service() == 0
    unit = (tmp_path / "config/systemd/user/nauta-monitor.service").read_text()
    assert '"/opt/nauta app/bin/nauta-monitor"' in unit
    assert str(tmp_path / "config/nauta-monitor/config.toml") in unit
    assert f'ReadWritePaths="{tmp_path / "state/nauta-monitor"}"' in unit
    assert f'"--history" "{tmp_path / "state/nauta-monitor/history.jsonl"}"' in unit
    assert f'"--snapshot" "{tmp_path / "state/nauta-monitor/status.json"}"' in unit
    assert "ProtectHome=read-only" in unit
    assert (tmp_path / "state/nauta-monitor").stat().st_mode & 0o777 == 0o700
    assert calls == [
        ("daemon-reload",),
        ("enable", systemd_service.SERVICE_NAME),
        ("restart", systemd_service.SERVICE_NAME),
    ]


def test_service_status_reports_a_locale_neutral_state(monkeypatch, capsys):
    monkeypatch.setattr(
        systemd_service,
        "_systemctl",
        lambda *args: subprocess.CompletedProcess(
            args, 0, "LoadState=not-found\nActiveState=inactive\nSubState=dead\n", ""
        ),
    )
    assert systemd_service.main(["status"]) == 0
    assert json.loads(capsys.readouterr().out)["service_state"] == "not-installed"


def test_start_installs_the_service_when_missing(monkeypatch, capsys):
    calls = []

    def systemctl(*args):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "not-found\n", "")

    monkeypatch.setattr(systemd_service, "_systemctl", systemctl)
    monkeypatch.setattr(systemd_service.sys, "platform", "linux")
    monkeypatch.setattr(systemd_service, "_install_service", lambda: 0)
    assert systemd_service.main(["start"]) == 0
    assert calls == [("show", systemd_service.SERVICE_NAME, "--property=LoadState", "--value")]


def test_uninstall_disables_service_before_removing_unit(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    unit = tmp_path / "systemd/user/nauta-monitor.service"
    unit.parent.mkdir(parents=True)
    unit.write_text("[Service]\n")
    calls = []

    def systemctl(*args):
        calls.append(args)
        output = "loaded\n" if args[0] == "show" else ""
        return subprocess.CompletedProcess(args, 0, output, "")

    monkeypatch.setattr(systemd_service, "_systemctl", systemctl)
    assert systemd_service.main(["uninstall"]) == 0
    assert not unit.exists()
    assert calls == [
        ("show", systemd_service.SERVICE_NAME, "--property=LoadState", "--value"),
        ("disable", "--now", systemd_service.SERVICE_NAME),
        ("daemon-reload",),
    ]
