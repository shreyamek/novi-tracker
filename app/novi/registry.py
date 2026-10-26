"""Features register themselves here: a name, API routes and a tab for the UI."""
from __future__ import annotations

from typing import Callable

_FEATURES: list[dict] = []


def clear() -> None:
    _FEATURES.clear()


def register(name: str, routes: dict[str, Callable], tab: dict) -> None:
    """routes maps 'GET /api/x' or 'POST /api/x' to a function(body: dict | None) -> Any (JSON-serialisable)."""
    _FEATURES.append({"name": name, "routes": routes, "tab": tab})


def features() -> list[dict]:
    return list(_FEATURES)
