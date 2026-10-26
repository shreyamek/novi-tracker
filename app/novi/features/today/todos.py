"""To-dos stored in me/todos.json. The list order is the display order."""
from __future__ import annotations

import uuid

from novi import storage

FILE = "todos.json"
TEXT_LIMIT = 200


def list_all() -> list[dict]:
    return storage.read_json(FILE, [])


def _save(items: list[dict]) -> None:
    storage.write_json(FILE, items)


def _find(items: list[dict], todo_id: str) -> int:
    for i, t in enumerate(items):
        if t.get("id") == todo_id:
            return i
    raise ValueError("no to-do with that id")


@storage.locked()
def add(text: str) -> dict:
    text = (text or "").strip() if isinstance(text, str) else None
    if not text:
        raise ValueError("to-do text is empty")
    if len(text) > TEXT_LIMIT:
        raise ValueError(f"to-do is too long (max {TEXT_LIMIT} characters)")
    items = list_all()
    row = {"id": uuid.uuid4().hex[:12], "text": text, "done": False, "today": False}
    items.append(row)
    _save(items)
    return row


@storage.locked()
def toggle(todo_id: str) -> dict:
    items = list_all()
    row = items[_find(items, todo_id)]
    row["done"] = not row.get("done", False)
    _save(items)
    return row


@storage.locked()
def set_today(todo_id: str, flag: bool) -> dict:
    items = list_all()
    row = items[_find(items, todo_id)]
    row["today"] = bool(flag)
    _save(items)
    return row


@storage.locked()
def move(todo_id: str, to_index: int) -> None:
    items = list_all()
    i = _find(items, todo_id)
    if not isinstance(to_index, int) or isinstance(to_index, bool) or not 0 <= to_index < len(items):
        raise ValueError("to_index is out of range")
    row = items.pop(i)
    items.insert(to_index, row)
    _save(items)


@storage.locked()
def delete(todo_id: str) -> None:
    items = list_all()
    del items[_find(items, todo_id)]
    _save(items)
