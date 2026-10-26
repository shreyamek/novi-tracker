"""Deterministic checks for /refresh: hard filters (reasons to reject) and duplicate detection."""
from __future__ import annotations

import re
from typing import Any


def _norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def _norm_link(link: Any) -> str:
    return _norm(link).rstrip("/")


def _city(location: str) -> str:
    return _norm(location.split(",")[0])


def hard_filters(posting: dict[str, Any], prefs: dict[str, Any]) -> list[str]:
    """Reasons to reject the posting. An empty list means it passes."""
    reasons: list[str] = []

    if posting.get("open", True) is False:
        reasons.append("posting is closed")

    pay_max = posting.get("pay_max")
    pay_floor = prefs.get("pay_floor")
    if pay_max is not None and pay_floor is not None and pay_max < pay_floor:
        reasons.append(f"pay tops out at {pay_max}, below your floor of {pay_floor}")

    text = _norm(posting.get("title")) + " " + _norm(posting.get("description"))
    for word in prefs.get("dealbreakers") or []:
        if _norm(word) and _norm(word) in text:
            reasons.append(f"dealbreaker: '{word}'")

    remote = posting.get("remote")
    locations = prefs.get("locations") or []
    if remote in ("onsite", "hybrid") and not prefs.get("relocate") and locations:
        place = _norm(posting.get("location"))
        if not any(_city(loc) and _city(loc) in place for loc in locations):
            reasons.append(f"{remote} in {posting.get('location') or 'an unknown place'}, not one of your locations")

    if prefs.get("sponsorship_needed") and posting.get("sponsorship_offered") is False:
        reasons.append("needs sponsorship and the employer does not offer it")

    return reasons


def dedupe(posting: dict[str, Any], existing: list[dict[str, Any]]) -> bool:
    """True if the posting duplicates an existing entry by link or by company and role."""
    link = _norm_link(posting.get("link"))
    key = (_norm(posting.get("company")), _norm(posting.get("title")))
    for e in existing:
        if link and _norm_link(e.get("link")) == link:
            return True
        if key == (_norm(e.get("company")), _norm(e.get("role"))):
            return True
    return False
