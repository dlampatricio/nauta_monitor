import json
import os

try:
    import tomllib
except ImportError:  # Python 3.9/3.10
    import tomli as tomllib

from nauta_monitor.security import credentials


def test_credentials_save_uses_private_toml_and_never_echoes_secret(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    secret = 'password with "quotes", $dollars, and \\slashes'
    monkeypatch.setattr(
        "sys.stdin",
        __import__("io").StringIO(json.dumps({"username": "nauta@example.cu", "password": secret})),
    )

    assert credentials.main(["save"]) == 0
    response = json.loads(capsys.readouterr().out)
    path = credentials.config_path()
    if os.name == "posix":
        assert path.stat().st_mode & 0o777 == 0o600
        assert path.parent.stat().st_mode & 0o777 == 0o700
    assert secret not in response["message"]

    config = tomllib.loads(path.read_text())
    assert config["nauta"] == {
        "username": "nauta@example.cu",
        "password": secret,
    }
    assert "speedtest" not in config
    assert "alerts" not in config
    assert credentials.status() == 0
    assert json.loads(capsys.readouterr().out)["credentials_state"] == "configured"


def test_credentials_update_preserves_existing_account_settings(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    path = credentials.config_path()
    path.parent.mkdir(parents=True)
    path.write_text(
        "# Existing user settings must survive credential changes.\n"
        '[nauta]\nusername = "old"\npassword = "old-pass"  # Keep this note.\ncup_per_hour = 15\n'
        "saldo_interval = 900\nspeedtest_interval = 0\n"
        '[alerts]\nmin_balance_hours = 8\non_alert = "notify-send nauta"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.stdin",
        __import__("io").StringIO(json.dumps({"username": "new", "password": "new-pass"})),
    )

    assert credentials.main(["save"]) == 0
    text = path.read_text()
    config = tomllib.loads(text)
    assert "# Existing user settings must survive credential changes." in text
    assert "# Keep this note." in text
    assert config["nauta"] == {
        "username": "new",
        "password": "new-pass",
        "cup_per_hour": 15,
        "saldo_interval": 900,
        "speedtest_interval": 0,
    }
    assert config["alerts"]["min_balance_hours"] == 8
    assert config["alerts"]["on_alert"] == "notify-send nauta"

    capsys.readouterr()
    assert credentials.main(["remove"]) == 0
    assert json.loads(capsys.readouterr().out)["message"] == "Credenciales eliminadas."
    cleared = tomllib.loads(path.read_text())
    assert cleared["nauta"]["username"] == ""
    assert cleared["nauta"]["password"] == ""
    assert cleared["nauta"]["cup_per_hour"] == 15


def test_credentials_directory_follows_each_platform_convention(tmp_path, monkeypatch):
    monkeypatch.setattr(credentials.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    assert credentials.config_path() == tmp_path / "xdg/nauta-monitor/config.toml"

    monkeypatch.setattr(credentials.sys, "platform", "darwin")
    monkeypatch.delenv("XDG_CONFIG_HOME")
    monkeypatch.setattr(credentials.Path, "home", lambda: tmp_path)
    assert credentials.config_path() == tmp_path / "Library/Application Support/nauta-monitor/config.toml"

    monkeypatch.setattr(credentials.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    assert credentials.config_path() == tmp_path / "roaming/nauta-monitor/config.toml"
