import copy
import json
from pathlib import Path

from novi import prefs

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "alex_example" / "preferences.json"
TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "preferences.json"


def test_validate_rejects_bad_tailoring_level():
    d = copy.deepcopy(prefs.DEFAULTS)
    d["tailoring"] = "ruthless"
    errors = prefs.validate(d)
    assert any("tailoring" in e for e in errors)


def test_validate_rejects_bad_apply_mode():
    d = copy.deepcopy(prefs.DEFAULTS)
    d["apply_mode"] = "auto_submit"
    errors = prefs.validate(d)
    assert any("apply_mode" in e for e in errors)


def test_validate_rejects_bad_remote_and_wrong_types():
    d = copy.deepcopy(prefs.DEFAULTS)
    d["remote"] = "sometimes"
    d["relocate"] = "yes"
    d["target_roles"] = "data analyst"
    errors = prefs.validate(d)
    assert any("remote" in e for e in errors)
    assert any("relocate" in e for e in errors)
    assert any("target_roles" in e for e in errors)


def test_defaults_when_missing(me):
    p = prefs.load()
    assert p["tailoring"] == "standard"
    assert p["apply_mode"] == "off"
    assert p["fill_demographics"] is False
    assert p["fit_threshold"] == 8.0
    assert p["remote"] == "any"
    assert p["relocate"] is False
    assert p["pay_floor"] is None
    assert prefs.validate(p) == []


def test_load_reads_saved_file_and_fills_missing_keys(me):
    (me / "preferences.json").write_text(json.dumps({"field": "data", "tailoring": "light"}), encoding="utf-8")
    p = prefs.load()
    assert p["field"] == "data"
    assert p["tailoring"] == "light"
    assert p["apply_mode"] == "off"


def test_fixture_prefs_valid():
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert prefs.validate(d) == []


def test_template_prefs_valid():
    d = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    assert prefs.validate(d) == []
