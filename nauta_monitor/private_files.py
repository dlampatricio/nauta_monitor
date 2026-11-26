"""Atomic writers for per-user configuration and status files."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def write_private_text(path: str | Path, text: str) -> None:
    """Atomically replace a UTF-8 file with user-only permissions on POSIX."""
    target = Path(path)
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name == "posix":
        os.chmod(target.parent, 0o700)
    fd, name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent, text=True)
    temporary = Path(name)
    try:
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        if os.name == "posix":
            os.chmod(target, 0o600)
    finally:
        temporary.unlink(missing_ok=True)
