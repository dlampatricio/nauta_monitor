import json
from pathlib import Path

from nauta_monitor.history import append_sample, load_recent


def _sample() -> dict:
    return {
        "username": "user",
        "account_status": "Activa",
        "credit": 37.82,
        "hours": 3.0,
        "download_mbps": 34.5,
        "upload_mbps": 12.2,
        "ping_ms": 45.0,
    }


def test_append_and_load(tmp_path):
    path = tmp_path / "history.jsonl"
    append_sample(str(path), _sample())
    append_sample(str(path), _sample())
    entries = load_recent(str(path), limit=10)
    assert len(entries) == 2
    assert entries[0]["hours"] == 3.0
    assert all("timestamp" in entry for entry in entries)


def test_load_recent_order_and_limit(tmp_path):
    path = tmp_path / "history.jsonl"
    for i in range(5):
        sample = _sample()
        sample["hours"] = float(i)
        append_sample(str(path), sample)
    entries = load_recent(str(path), limit=3)
    assert [entry["hours"] for entry in entries] == [4.0, 3.0, 2.0]


def test_load_missing_file(tmp_path):
    assert load_recent(str(tmp_path / "nope.jsonl"), limit=10) == []