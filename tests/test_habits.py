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


@pytest.mark.parametrize("bad", ["false", "true", 0, 1, None, "1"])
def test_log_done_must_be_a_real_bool(me, bad):
    define("gym")
    with pytest.raises(ValueError):
        api.habits_log({"key": "gym", "done": bad, "date": "2026-10-25"})
    assert habits.done_on(TODAY) == []


def test_log_done_true_and_false_still_work(me):
    define("gym")
    api.habits_log({"key": "gym", "done": True, "date": "2026-10-25"})
    assert habits.done_on(TODAY) == ["gym"]
    api.habits_log({"key": "gym", "done": False, "date": "2026-10-25"})
    assert habits.done_on(TODAY) == []


def test_post_done_string_returns_400_and_does_not_tick(me):
    import http.client
    import json
    import threading
    from http.server import ThreadingHTTPServer

    from novi import registry
    from novi.server import make_handler

    define("gym")
    registry.clear()
    registry.register("today", api.ROUTES, {"label": "Today"})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(me))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", httpd.server_address[1], timeout=5)
        payload = json.dumps({"key": "gym", "done": "false", "date": "2026-10-25"}).encode("utf-8")
        conn.request("POST", "/api/habits/log", body=payload, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        status = resp.status
        resp.read()
        conn.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
        registry.clear()
    assert status == 400
    assert habits.done_on(TODAY) == []


def test_corrupt_day_file_skipped_and_reported(me):
    from datetime import date as _date

    define("gym")
    (me / "days").mkdir(exist_ok=True)
    bad = me / "days" / "2026-10-20.json"
    bad.write_text("{not json", encoding="utf-8")
    for d in ("2026-10-19", "2026-10-21", "2026-10-22"):
        api.habits_log({"key": "gym", "done": True, "date": d})

    # the corrupt day counts as not done; the days around it still count
    assert habits.done_on(_date(2026, 10, 20)) == []
    assert habits.streak("gym", _date(2026, 10, 22)) == 2
    grid = {g["date"]: g["done"] for g in habits.grid(53, _date(2026, 10, 22))}
    assert grid["2026-10-19"] == ["gym"] and grid["2026-10-21"] == ["gym"]
    assert grid["2026-10-20"] == []

    assert habits.warnings() == ["days/2026-10-20.json is not valid JSON"]
    # never overwritten, even by a write to that same day
    before = bad.read_bytes()
    with pytest.raises(ValueError):
        api.habits_log({"key": "gym", "done": True, "date": "2026-10-20"})
    assert bad.read_bytes() == before


def test_get_today_returns_200_with_warning_and_other_days(me):
    import http.client
    import json as _json
    import threading
    from datetime import date as _date
    from http.server import ThreadingHTTPServer

    from novi import registry
    from novi.server import make_handler

    define("gym")
    (me / "days").mkdir(exist_ok=True)
    (me / "days" / "2026-10-20.json").write_text("[oops", encoding="utf-8")
    today = _date.today().isoformat()
    api.habits_log({"key": "gym", "done": True, "date": today})

    registry.clear()
    registry.register("today", api.ROUTES, {"label": "Today"})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(me))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", httpd.server_address[1], timeout=5)
        conn.request("GET", "/api/today")
        resp = conn.getresponse()
        body = _json.loads(resp.read())
        assert resp.status == 200
        assert body["warnings"] == ["days/2026-10-20.json is not valid JSON"]
        assert body["ticks"] == ["gym"]
        assert body["streaks"]["gym"] == 1
    finally:
        httpd.shutdown()
        httpd.server_close()
        registry.clear()
