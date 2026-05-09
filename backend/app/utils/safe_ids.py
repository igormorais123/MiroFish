"""Validacao de IDs usados como nomes de diretorio em storage local."""

from __future__ import annotations

import os
import re
from pathlib import Path


_SAFE_STORAGE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$")


def validate_storage_id(value: str, label: str = "id") -> str:
    """Valida um identificador antes de usa-lo como filho de diretorio."""
    if not isinstance(value, str):
        raise ValueError(f"{label} invalido")

    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} invalido")

    if os.path.isabs(cleaned) or "/" in cleaned or "\\" in cleaned:
        raise ValueError(f"{label} invalido")

    if cleaned in {".", ".."} or ".." in Path(cleaned).parts:
        raise ValueError(f"{label} invalido")

    if not _SAFE_STORAGE_ID_RE.fullmatch(cleaned):
        raise ValueError(f"{label} invalido")

    return cleaned


def safe_storage_child(base_dir: str | os.PathLike[str], child_id: str, label: str = "id") -> str:
    """Resolve um diretorio filho garantindo que ele permanece dentro da base."""
    safe_id = validate_storage_id(child_id, label)
    base = Path(base_dir).resolve()
    target = (base / safe_id).resolve()
    if target.parent != base:
        raise ValueError(f"{label} invalido")
    return str(target)
