"""Applications stored in me/tracker.json. Every write goes through storage, which refuses to overwrite a corrupt file."""
from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date

from novi import storage

FILE = "tracker.json"
STATUSES = ("Pending", "Queued", "Applied", "Interviewing", "Offer", "Rejected")
TEXT_LIMIT = 500


class Duplicate(ValueError):
    pass


@dataclass
class Application:
    id: str
    company: str
    role: str
    status: str = "Pending"
    link: str = ""
    location: str = ""
    pay: str = ""
    score: float | None = None
    score_why: str = ""
    notes: list = field(default_factory=list)
    docs: list = field(default_factory=list)
    posted: str = ""
    applied: str = ""
    added: str = ""


FIELDS = [f for f in Application.__dataclass_fields__ if f not in ("id", "added", "notes")]


def _today() -> str:
    return date.today().isoformat()


def _text(value, name: str, limit: int = TEXT_LIMIT) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{name} must be text")
    value = value.strip()
    if len(value) > limit:
        raise ValueError(f"{name} is too long (max {limit} characters)")
    return value


def _docs(value) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(d, str) for d in value):
        raise ValueError("docs must be a list of text entries")
    return [d.strip() for d in value if d.strip()]


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _norm_link(s: str) -> str:
    return _norm(s).rstrip("/")


def _iso_date(value: str, name: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"{name} must look like YYYY-MM-DD")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as e:
        raise ValueError(f"{name} is not a real date") from e


def _score(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        s = float(value)
    except (TypeError, ValueError) as e:
        raise ValueError("score must be a number from 0 to 10") from e
    if not 0 <= s <= 10:
        raise ValueError("score must be a number from 0 to 10")
    return s


def list_all() -> list[dict]:
    return storage.read_json(FILE, [])


def _save(apps: list[dict]) -> None:
    storage.write_json(FILE, apps)


def _find(apps: list[dict], app_id: str) -> dict:
    for a in apps:
        if a.get("id") == app_id:
            return a
    raise ValueError("no role with that id")


@storage.locked()
def add(app: dict) -> dict:
    company = _text(app.get("company"), "company")
    role = _text(app.get("role"), "role")
    if not company or not role:
        raise ValueError("company and role are required")
    status = app.get("status") or "Pending"
    if status not in STATUSES:
        raise ValueError(f"status must be one of: {', '.join(STATUSES)}")
    link = _text(app.get("link"), "link")

    apps = list_all()
    key = (_norm(company), _norm(role))
    for other in apps:
        if link and other.get("link") and _norm_link(other["link"]) == _norm_link(link):
            raise Duplicate(f"{other['company']} ({other['role']}) is already tracked with this link")
        if (_norm(other.get("company", "")), _norm(other.get("role", ""))) == key:
            raise Duplicate(f"{other['company']} ({other['role']}) is already tracked")

    record = Application(id=uuid.uuid4().hex[:12], company=company, role=role, status=status, added=_today())
    for name in FIELDS:
        if name in ("company", "role", "status"):
            continue
        if name == "score":
            record.score = _score(app.get("score"))
        elif name in ("posted", "applied"):
            v = _text(app.get(name), name, 20)
            setattr(record, name, _iso_date(v, name) if v else "")
        elif name == "docs":
            record.docs = _docs(app.get("docs"))
        else:
            setattr(record, name, _text(app.get(name), name))
    note = _text(app.get("notes"), "notes", 2000)
    if note:
        record.notes = [{"date": _today(), "text": note}]
    if status == "Applied":
        record.applied = record.applied or _today()
    row = asdict(record)
    apps.append(row)
    _save(apps)
    return row


@storage.locked()
def set_status(app_id: str, status: str, date_: str | None = None) -> dict:
    if status not in STATUSES:
        raise ValueError(f"status must be one of: {', '.join(STATUSES)}")
    apps = list_all()
    row = _find(apps, app_id)
    row["status"] = status
    if status == "Applied":
        row["applied"] = _iso_date(date_, "applied date") if date_ else _today()
    _save(apps)
    return row


@storage.locked()
def add_note(app_id: str, text: str) -> dict:
    text = _text(text, "note", 2000)
    if not text:
        raise ValueError("note is empty")
    apps = list_all()
    row = _find(apps, app_id)
    row.setdefault("notes", []).append({"date": _today(), "text": text})
    _save(apps)
    return row
