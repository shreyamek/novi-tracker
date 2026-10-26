"""Reads and writes the person's own data in me/ (git-ignored). Atomic writes; never clobbers a corrupt file."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class StorageError(Exception):
    pass


def me_dir() -> Path:
    env = os.environ.get("NOVI_ME")
    p = Path(env) if env else Path(__file__).resolve().parents[2] / "me"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise StorageError(f"{path.name} is not valid JSON ({e}). Fix or move it; Novi will not overwrite it.") from e


def read_json(name: str, default: Any) -> Any:
    path = me_dir() / name
    return _load(path) if path.exists() else default


def write_json(name: str, data: Any) -> None:
    path = me_dir() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _load(path)  # raises StorageError if the existing file is corrupt
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
