"""HTTP routes for Today. Every route answers with the full Today payload so the UI can redraw from one response.

Bad input raises ValueError (the server turns it into a 400).
"""
from __future__ import annotations

from datetime import date

from novi import prefs, storage

from . import habits, todos

GRID_WEEKS = 53


def _guard(fn):
    def wrapped(body):
        try:
            return fn(body)
        except storage.StorageError as e:
            raise ValueError(str(e)) from e
    return wrapped


def _need(body, *keys):
    if not isinstance(body, dict):
        raise ValueError("expected a JSON object")
    for k in keys:
        if k not in body:
            raise ValueError(f"missing field: {k}")
    return body


def _flag(value, name: str) -> bool:
    # A JSON string such as "false" is truthy in Python, so only a real true/false is accepted.
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be true or false")
    return value


def _name() -> str | None:
    # Optional: only shown in the greeting when me/preferences.json has a non-empty "name".
    name = prefs.load().get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return None


def _payload() -> dict:
    today = date.today()
    defined = habits.defined()
    return {
        "date": today.isoformat(),
        "name": _name(),
        "todos": todos.list_all(),
        "habits": defined,
        "ticks": habits.done_on(today),
        "streaks": {h["key"]: habits.streak(h["key"], today) for h in defined},
        "grid": habits.grid(GRID_WEEKS, today),
    }


@_guard
def get_today(body):
    return _payload()


@_guard
def todo_add(body):
    todos.add(_need(body, "text")["text"])
    return _payload()


@_guard
def todo_toggle(body):
    todos.toggle(_need(body, "id")["id"])
    return _payload()


@_guard
def todo_move(body):
    b = _need(body, "id", "to")
    todos.move(b["id"], b["to"])
    return _payload()


@_guard
def todo_today(body):
    b = _need(body, "id", "today")
    todos.set_today(b["id"], _flag(b["today"], "today"))
    return _payload()


@_guard
def todo_delete(body):
    todos.delete(_need(body, "id")["id"])
    return _payload()


@_guard
def habits_define(body):
    habits.define(_need(body, "habits")["habits"])
    return _payload()


@_guard
def habits_log(body):
    b = _need(body, "key", "done")
    day = b.get("date") or date.today().isoformat()
    habits.log(day, b["key"], _flag(b["done"], "done"))
    return _payload()


ROUTES = {
    "GET /api/today": get_today,
    "POST /api/todo/add": todo_add,
    "POST /api/todo/toggle": todo_toggle,
    "POST /api/todo/move": todo_move,
    "POST /api/todo/today": todo_today,
    "POST /api/todo/delete": todo_delete,
    "POST /api/habits/define": habits_define,
    "POST /api/habits/log": habits_log,
}
