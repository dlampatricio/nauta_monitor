import json
from datetime import datetime
from io import StringIO

from rich.console import Console

from nauta_monitor import cli
from nauta_monitor.client import QueryError
from nauta_monitor.config import Config
from nauta_monitor.parser import AccountInfo
from nauta_monitor.snapshot import read_snapshot


def test_watch_snapshot_startup_zero_failure_and_recovery(tmp_path, monkeypatch):
    markup = '<img src="https://example.invalid/tracker">'
    replies = iter([
        QueryError("private portal error"),
        AccountInfo(account_status=markup, credit=0),
        AccountInfo(account_status="Respuesta sin saldo"),
        QueryError("private portal error again"),
        AccountInfo(account_status="Activa", credit=25),
    ])

    class Portal:
        def init_session(self):
            return None

        def query_account(self, username, password, portal):
            reply = next(replies)
            if isinstance(reply, Exception):
                raise reply
            return reply

    history = tmp_path / "history.jsonl"
    snapshot = tmp_path / "status.json"
    state = cli.WatchState()
    config = Config(username="private username", password="private password")
    now = 1000
    monkeypatch.setattr(cli, "SecurePortalClient", Portal)
    monkeypatch.setattr(cli.time, "time", lambda: now)

    def update():
        cli._update(
            config, state, str(history), Console(file=StringIO()), True,
            snapshot_path=str(snapshot), saldo_interval=120,
        )
        raw = snapshot.read_text()
        assert "private" not in raw
        return json.loads(raw)

    assert update() == {
        "version": 1,
        "credit_cup": None,
        "hours": None,
        "account_status": None,
        "last_success_at": None,
        "last_attempt_at": 1000,
        "result": "error",
        "stale_after_seconds": 180,
    }
    assert not history.exists()

    now += 120
    zero = update()
    assert zero["credit_cup"] == zero["hours"] == 0
    assert zero["account_status"] == markup
    assert zero["last_attempt_at"] == zero["last_success_at"] == now
    assert zero["result"] == "ok"
    first_history = history.read_text()

    for _ in range(2):
        now += 120
        assert update() == {**zero, "last_attempt_at": now, "result": "error"}
        assert history.read_text() == first_history

    now += 120
    recovered = update()
    assert recovered["result"] == "ok"
    assert recovered["hours"] == 2
    assert recovered["last_attempt_at"] == recovered["last_success_at"] == now
    assert len(history.read_text().splitlines()) == 2
    assert [hours for _, hours in state.history] == [0, 2]


def test_snapshot_write_failure_does_not_block_history(tmp_path, monkeypatch):
    def refresh(config, state):
        state.account = AccountInfo(credit=12.5)
        state.hours = 1
        state.last_saldo_success_at = int(datetime.now().timestamp())
        return True

    monkeypatch.setattr(cli, "_refresh_saldo", refresh)
    history = tmp_path / "history.jsonl"
    cli._update(
        Config(username="u", password="p"), cli.WatchState(), str(history),
        Console(file=StringIO()), True, snapshot_path=str(tmp_path), saldo_interval=120,
    )
    assert json.loads(history.read_text())["hours"] == 1
    assert list(tmp_path.iterdir()) == [history]


def test_snapshot_reader_rejects_malformed_or_unbounded_data(tmp_path):
    path = tmp_path / "status.json"
    valid = {
        "version": 1,
        "credit_cup": 25.0,
        "hours": 2.0,
        "account_status": "Activa",
        "last_success_at": 1000,
        "last_attempt_at": 1000,
        "result": "ok",
        "stale_after_seconds": 180,
    }
    path.write_text(json.dumps(valid))
    assert read_snapshot(path) == valid

    for invalid in (
        {**valid, "version": True},
        {**valid, "last_attempt_at": True},
        {**valid, "credit_cup": float("nan")},
        {**valid, "account_status": "x" * 257},
        {**valid, "stale_after_seconds": 0},
        {**valid, "last_success_at": None},
    ):
        path.write_text(json.dumps(invalid))
        assert read_snapshot(path) is None

    path.write_text("x" * 4097)
    assert read_snapshot(path) is None


def test_watch_keeps_last_successful_snapshot_across_restart(tmp_path, monkeypatch):
    snapshot = tmp_path / "status.json"
    snapshot.write_text(json.dumps({
        "version": 1,
        "credit_cup": 50,
        "hours": 4,
        "account_status": "Activa",
        "last_success_at": 1000,
        "last_attempt_at": 1000,
        "result": "ok",
        "stale_after_seconds": 180,
    }))

    class Portal:
        def init_session(self):
            return None

        def query_account(self, username, password, portal):
            raise QueryError("offline")

    monkeypatch.setattr(cli, "SecurePortalClient", Portal)
    monkeypatch.setattr(cli.time, "time", lambda: 2000)
    monkeypatch.setattr(cli.time, "sleep", lambda _: (_ for _ in ()).throw(KeyboardInterrupt()))
    config = Config(username="u", password="p", speedtest_interval=0)
    args = cli.build_parser().parse_args(["watch", "--no-speedtest", "--snapshot", str(snapshot)])

    assert cli.command_watch(config, args) == cli._EXIT_OK
    result = json.loads(snapshot.read_text())
    assert result["result"] == "error"
    assert result["credit_cup"] == 50
    assert result["hours"] == 4
    assert result["last_success_at"] == 1000
    assert result["last_attempt_at"] == 2000
