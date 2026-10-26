import json
from datetime import date

import pytest
from novi import storage
from novi.features.tracker import model


def base(**kw):
    app = {"company": "Acme Corp", "role": "Data Analyst", "link": "https://example.com/jobs/1"}
    app.update(kw)
    return app


def test_add_rejects_duplicate_link(me):
    model.add(base())
    with pytest.raises(model.Duplicate):
        model.add(base(company="Other Co", role="Engineer", link="https://example.com/jobs/1"))


def test_add_rejects_duplicate_company_role_case_insensitive(me):
    model.add(base(link="https://example.com/a"))
    with pytest.raises(model.Duplicate):
        model.add(base(company="  ACME corp ", role="data analyst", link="https://example.com/b"))
    assert len(model.list_all()) == 1


def test_duplicate_is_a_value_error(me):
    assert issubclass(model.Duplicate, ValueError)


def test_set_status_rejects_unknown_status(me):
    a = model.add(base())
    with pytest.raises(ValueError):
        model.set_status(a["id"], "applied")
    with pytest.raises(ValueError):
        model.set_status(a["id"], "Ghosted")
    assert model.list_all()[0]["status"] == "Pending"


def test_applied_requires_date_defaults_today(me):
    a = model.add(base())
    updated = model.set_status(a["id"], "Applied")
    assert updated["status"] == "Applied"
    assert updated["applied"] == date.today().isoformat()


def test_applied_stores_given_date(me):
    a = model.add(base())
    updated = model.set_status(a["id"], "Applied", "2026-10-20")
    assert updated["applied"] == "2026-10-20"


def test_set_status_unknown_id_is_value_error(me):
    with pytest.raises(ValueError):
        model.set_status("nope", "Queued")


def test_add_note_appends(me):
    a = model.add(base())
    model.add_note(a["id"], "Recruiter replied")
    model.add_note(a["id"], "Second note")
    notes = model.list_all()[0]["notes"]
    assert [n["text"] for n in notes] == ["Recruiter replied", "Second note"]


def test_add_note_rejects_empty(me):
    a = model.add(base())
    with pytest.raises(ValueError):
        model.add_note(a["id"], "   ")


def test_add_rejects_bad_score(me):
    with pytest.raises(ValueError):
        model.add(base(score=11))


def test_corrupt_tracker_json_not_overwritten(me):
    p = me / "tracker.json"
    p.write_bytes(b"[{broken")
    with pytest.raises(storage.StorageError):
        model.add(base())
    assert p.read_bytes() == b"[{broken"


def test_empty_me_returns_empty_list(me):
    assert model.list_all() == []


def test_add_accepts_empty_docs_and_text_notes(me):
    row = model.add(base(docs=[], notes="why it fits"))
    stored = model.list_all()[0]
    assert stored["docs"] == []
    assert stored["notes"] == [{"date": date.today().isoformat(), "text": "why it fits"}]
    assert row["notes"] == stored["notes"]


def test_add_stores_docs_list_of_strings(me):
    model.add(base(docs=["resume.pdf", "cover_letter.pdf"]))
    assert model.list_all()[0]["docs"] == ["resume.pdf", "cover_letter.pdf"]


def test_add_rejects_docs_that_are_not_a_list_of_strings(me):
    with pytest.raises(ValueError):
        model.add(base(docs="resume.pdf"))
    with pytest.raises(ValueError):
        model.add(base(docs=[1, 2]))
    assert model.list_all() == []


def test_add_empty_notes_string_stores_no_notes(me):
    model.add(base(notes="   "))
    assert model.list_all()[0]["notes"] == []
