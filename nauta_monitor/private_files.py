"""Escritura atómica de archivos de configuración y estado del usuario."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def write_private_text(path: str | Path, text: str) -> None:
    """Reemplaza un archivo UTF-8 de forma atómica y con permisos privados."""
    target = Path(path)
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
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
