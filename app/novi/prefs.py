"""The person's preferences (me/preferences.json). Missing keys fall back to DEFAULTS."""
from __future__ import annotations

from typing import Any

from novi import storage

REMOTE_VALUES = ("remote", "hybrid", "onsite", "any")
TAILORING_LEVELS = ("light", "standard", "aggressive")
APPLY_MODES = ("off", "prepare")

DEFAULTS: dict[str, Any] = {
    "target_roles": [],
    "field": "",
    "level": "",
    "locations": [],
    "remote": "any",
    "relocate": False,
    "pay_floor": None,
    "dealbreakers": [],
    "start_date": "",
    "work_auth": "",
    "sponsorship_needed": False,
    "tailoring": "standard",
    "apply_mode": "off",
    "fill_demographics": False,
    "fit_threshold": 8.0,
    "search_goals": "",
}

_STR_LISTS = ("target_roles", "locations", "dealbreakers")
_STRINGS = ("field", "level", "start_date", "work_auth", "search_goals")
_BOOLS = ("relocate", "sponsorship_needed", "fill_demographics")


def load() -> dict[str, Any]:
    """Saved preferences merged over the defaults. A missing file gives the defaults."""
    saved = storage.read_json("preferences.json", {})
    if not isinstance(saved, dict):
        raise storage.StorageError("preferences.json must hold a JSON object.")
    return {**DEFAULTS, **saved}


def validate(d: dict[str, Any]) -> list[str]:
    """Human-readable problems with a preferences dict. An empty list means valid."""
    errors: list[str] = []
    for key in _STR_LISTS:
        if key in d and not (isinstance(d[key], list) and all(isinstance(x, str) for x in d[key])):
            errors.append(f"{key} must be a list of strings")
    for key in _STRINGS:
        if key in d and not isinstance(d[key], str):
            errors.append(f"{key} must be a string")
    for key in _BOOLS:
        if key in d and not isinstance(d[key], bool):
            errors.append(f"{key} must be true or false")
    if "remote" in d and d["remote"] not in REMOTE_VALUES:
        errors.append(f"remote must be one of {', '.join(REMOTE_VALUES)}")
    if "tailoring" in d and d["tailoring"] not in TAILORING_LEVELS:
        errors.append(f"tailoring must be one of {', '.join(TAILORING_LEVELS)}")
    if "apply_mode" in d and d["apply_mode"] not in APPLY_MODES:
        errors.append(f"apply_mode must be one of {', '.join(APPLY_MODES)}")
    if "pay_floor" in d:
        pf = d["pay_floor"]
        if pf is not None and (not isinstance(pf, int) or isinstance(pf, bool)):
            errors.append("pay_floor must be a whole number or null")
    if "fit_threshold" in d:
        ft = d["fit_threshold"]
        if not isinstance(ft, (int, float)) or isinstance(ft, bool) or not 0 <= ft <= 10:
            errors.append("fit_threshold must be a number from 0 to 10")
    return errors
