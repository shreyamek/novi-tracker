import pytest
from novi import storage


def test_read_json_missing_returns_default(me):
    assert storage.read_json("tracker.json", []) == []


def test_write_json_is_atomic_and_utf8(me):
    storage.write_json("tracker.json", [{"company": "Zoë Café"}])
    assert "Zoë" in (me / "tracker.json").read_text(encoding="utf-8")
    assert not list(me.glob("*.tmp"))


def test_write_refuses_to_clobber_corrupt_file(me):
    p = me / "tracker.json"
    p.write_bytes(b"{not json")
    with pytest.raises(storage.StorageError):
        storage.write_json("tracker.json", [])
    assert p.read_bytes() == b"{not json"


def test_read_corrupt_raises(me):
    (me / "x.json").write_text("[", encoding="utf-8")
    with pytest.raises(storage.StorageError):
        storage.read_json("x.json", [])
