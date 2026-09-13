from nauta_monitor.config import ConfigError, load_config


def test_defaults_with_env(monkeypatch, tmp_path):
    monkeypatch.setenv("NAUTA_USERNAME", "user")
    monkeypatch.setenv("NAUTA_PASS", "pass")
    monkeypatch.chdir(tmp_path)
    config = load_config()
    assert config.username == "user"
    assert config.password == "pass"
    assert config.cup_per_hour == 12.5
    assert config.saldo_interval == 3600
    assert config.speedtest_interval == 1800
    assert config.speedtest.base_url == "http://speedtest.cd.etecsa.cu/"
    assert config.alerts.min_balance_hours == 24.0


def test_missing_credentials_allowed_with_env_cache(monkeypatch, tmp_path):
    monkeypatch.delenv("NAUTA_USERNAME", raising=False)
    monkeypatch.delenv("NAUTA_PASS", raising=False)
    monkeypatch.chdir(tmp_path)
    config = load_config()
    assert config.username is None
    assert config.password is None


def test_user_toml_overrides(tmp_path):
    (tmp_path / "config.toml").write_text(
        "[nauta]\n"
        "username = 'user2'\n"
        "password = 'pass2'\n"
        "cup_per_hour = 15.0\n"
        "[speedtest]\n"
        "download_chunks = 50\n"
        "[alerts]\n"
        "min_balance_hours = 6.0\n"
        "on_alert = 'echo ALERT'\n",
        encoding="utf-8",
    )
    config = load_config(tmp_path / "config.toml")
    assert config.username == "user2"
    assert config.password == "pass2"
    assert config.cup_per_hour == 15.0
    assert config.speedtest.download_chunks == 50
    assert config.alerts.min_balance_hours == 6.0
    assert config.alerts.on_alert == "echo ALERT"