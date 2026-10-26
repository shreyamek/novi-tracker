"""HTTP routes for the tracker. Bad input raises ValueError (the server turns it into a 400)."""
from __future__ import annotations

from novi import storage

from . import model


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


@_guard
def get_tracker(body):
    return {"roles": model.list_all(), "statuses": list(model.STATUSES)}


@_guard
def add_role(body):
    return model.add(_need(body))


@_guard
def set_status(body):
    b = _need(body, "id", "status")
    return model.set_status(b["id"], b["status"], b.get("date"))


@_guard
def add_note(body):
    b = _need(body, "id", "text")
    return model.add_note(b["id"], b["text"])


ROUTES = {
    "GET /api/tracker": get_tracker,
    "POST /api/tracker/add": add_role,
    "POST /api/tracker/status": set_status,
    "POST /api/tracker/note": add_note,
}
