from datetime import date

import pytest
from novi import storage
from novi.features.today import api, habits

TODAY = date(2026, 10, 25)


def define(*keys):
    habits.define([{"key": k, "label": k.title(), "hint": ""} for k in keys])


def log_days(key, *days):
    for d in days:
        habits.log(d, key, True)


def test_streak_counts_consecutive_days_ending_yesterday_when_today_unticked(me):
    define("gym")
    log_days("gym", "2026-10-22", "2026-10-23", "2026-10-24")
    assert habits.streak("gym", TODAY) == 3


def test_streak_includes_today_when_ticked(me):
    define("gym")
    log_days("gym", "2026-10-22", "2026-10-23", "2026-10-24", "2026-10-25")
    assert habits.streak("gym", TODAY) == 4


def test_streak_breaks_on_gap(me):
    define("gym")
    log_days("gym", "2026-10-21", "2026-10-23", "2026-10-24")
    assert habits.streak("gym", TODAY) == 2


def test_streak_zero_when_yesterday_missed_and_today_unticked(me):
    define("gym")
    log_days("gym", "2026-10-22", "2026-10-23")
    assert habits.streak("gym", TODAY) == 0


def test_unticked_day_is_recorded_as_not_done(me):
    define("gym")
    log_days("gym", "2026-10-24")
    habits.log("2026-10-24", "gym", False)
    assert habits.streak("gym", TODAY) == 0


def test_no_habits_defined_returns_empty_grid_and_zero_streaks(me):
    habits.define([])
    assert habits.grid(53, TODAY) == []
    assert habits.streak("anything", TODAY) == 0
    payload = api.get_today(None)
    assert payload["habits"] == []
    assert payload["grid"] == []
    assert payload["streaks"] == {}
    assert payload["todos"] == []


def test_grid_one_entry_per_day_with_done_keys(me):
    define("gym", "read")
    log_days("gym", "2026-10-24")
    habits.log("2026-10-24", "read", True)
    grid = habits.grid(2, TODAY)
    assert grid[-1] == {"date": "2026-10-25", "done": []}
    day = next(g for g in grid if g["date"] == "2026-10-24")
    assert sorted(day["done"]) == ["gym", "read"]
    assert all(set(g) == {"date", "done"} for g in grid)
    assert len({g["date"] for g in grid}) == len(grid)


@pytest.mark.parametrize("bad", ["Gym", "my habit", "a_b", "-x", "x-", "", "gym!", "../gym", "gym/x", "ünï"])
def test_habit_keys_validated_slug_only(me, bad):
    with pytest.raises(ValueError):
        habits.define([{"key": bad, "label": "X", "hint": ""}])
    assert storage.read_json("habits.json", []) == []


@pytest.mark.parametrize("good", ["gym", "read-2", "9am", "wake-up", "a"])
def test_habit_keys_accept_slugs(me, good):
    habits.define([{"key": good, "label": "X", "hint": ""}])
    assert habits.defined()[0]["key"] == good


def test_duplicate_habit_keys_rejected(me):
    with pytest.raises(ValueError):
        habits.define([{"key": "gym", "label": "A", "hint": ""}, {"key": "gym", "label": "B", "hint": ""}])


def test_log_rejects_undefined_key_and_bad_date(me):
    define("gym")
    with pytest.raises(ValueError):
        habits.log("2026-10-25", "read", True)
    with pytest.raises(ValueError):
        habits.log("../2026-10-25", "gym", True)
    with pytest.raises(ValueError):
        habits.log("2026-02-30", "gym", True)


def test_log_writes_day_file(me):
    define("gym")
    habits.log("2026-10-25", "gym", True)
    assert storage.read_json("days/2026-10-25.json", {}) == {"date": "2026-10-25", "done": ["gym"]}
