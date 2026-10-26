"""Habits the person defines (me/habits.json), their daily ticks (me/days/YYYY-MM-DD.json), streaks and the grid.

Nothing here is hard-coded: with no habits defined, every function returns an empty or zero result.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta

from novi import storage

HABITS_FILE = "habits.json"
KEY_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
LABEL_LIMIT = 60
HINT_LIMIT = 120


def defined() -> list[dict]:
    return storage.read_json(HABITS_FILE, [])


def _keys() -> set[str]:
    return {h["key"] for h in defined()}


@storage.locked()
def define(habits: list[dict]) -> list[dict]:
    if not isinstance(habits, list):
        raise ValueError("habits must be a list")
    clean: list[dict] = []
    seen: set[str] = set()
    for h in habits:
        if not isinstance(h, dict):
            raise ValueError("each habit must be an object with key, label and hint")
        key = h.get("key")
        if not isinstance(key, str) or not KEY_RE.fullmatch(key):
            raise ValueError(f"habit key {key!r} must be lowercase letters, digits and hyphens (for example 'gym' or 'wake-up')")
        if key in seen:
            raise ValueError(f"habit key {key!r} is listed twice")
        seen.add(key)
        label = str(h.get("label") or "").strip()
        if not label or len(label) > LABEL_LIMIT:
            raise ValueError(f"habit {key!r} needs a label of 1 to {LABEL_LIMIT} characters")
        hint = str(h.get("hint") or "").strip()
        if len(hint) > HINT_LIMIT:
            raise ValueError(f"habit {key!r} hint is too long (max {HINT_LIMIT} characters)")
        clean.append({"key": key, "label": label, "hint": hint})
    storage.write_json(HABITS_FILE, clean)
    return clean


def _check_date(day: str) -> date:
    if not isinstance(day, str) or not DATE_RE.fullmatch(day):
        raise ValueError("date must look like YYYY-MM-DD")
    try:
        return date.fromisoformat(day)
    except ValueError as e:
        raise ValueError("date is not a real date") from e


def _day_file(day: date) -> str:
    return f"days/{day.isoformat()}.json"


def done_on(day: date) -> list[str]:
    """Ticks for one day. A corrupt day file counts as not done here; warnings() reports it."""
    try:
        rec = storage.read_json(_day_file(day), None)
    except storage.StorageError:
        return []
    return list(rec.get("done", [])) if rec else []


def warnings() -> list[str]:
    """One line per day file under me/days/ that is not valid JSON. The files are never rewritten here."""
    folder = storage.me_dir() / "days"
    if not folder.is_dir():
        return []
    out = []
    for path in sorted(folder.glob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            out.append(f"days/{path.name} is not valid JSON")
    return out


@storage.locked()
def log(day: str, key: str, done: bool) -> None:
    d = _check_date(day)
    if key not in _keys():
        raise ValueError(f"no habit called {key!r} is defined")
    ticks = done_on(d)
    if done and key not in ticks:
        ticks.append(key)
    if not done and key in ticks:
        ticks.remove(key)
    storage.write_json(_day_file(d), {"date": d.isoformat(), "done": ticks})


def streak(key: str, today: date) -> int:
    """Consecutive done days. If today is not ticked yet, the streak counts from yesterday."""
    start = today if key in done_on(today) else today - timedelta(days=1)
    count = 0
    day = start
    while key in done_on(day):
        count += 1
        day -= timedelta(days=1)
    return count


def grid(weeks: int, today: date) -> list[dict]:
    """One entry per day from the Monday `weeks` weeks back through today. Empty if no habits are defined."""
    if not defined():
        return []
    first_week = today - timedelta(days=today.weekday()) - timedelta(weeks=max(weeks, 1) - 1)
    out = []
    day = first_week
    while day <= today:
        out.append({"date": day.isoformat(), "done": done_on(day)})
        day += timedelta(days=1)
    return out
