from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def append_sample(path: str | Path, sample: dict) -> None:
    sample = {"timestamp": datetime.now().isoformat(timespec="seconds"), **sample}
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(sample, ensure_ascii=False) + "\n")


def load_recent(path: str | Path, limit: int = 50) -> list[dict]:
    samples = []
    if not Path(path).exists():
        return samples
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                samples.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return samples[-limit:][::-1]