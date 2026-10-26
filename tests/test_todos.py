import pytest
from novi.features.today import todos


def texts():
    return [t["text"] for t in todos.list_all()]


def test_add_and_list_in_order(me):
    todos.add("first")
    todos.add("second")
    assert texts() == ["first", "second"]


def test_add_rejects_blank(me):
    with pytest.raises(ValueError):
        todos.add("   ")


def test_move_reorders(me):
    a = todos.add("a")
    todos.add("b")
    c = todos.add("c")
    todos.move(c["id"], 0)
    assert texts() == ["c", "a", "b"]
    todos.move(c["id"], 2)
    assert texts() == ["a", "b", "c"]


def test_move_rejects_out_of_range(me):
    a = todos.add("a")
    with pytest.raises(ValueError):
        todos.move(a["id"], 5)


def test_today_tag_toggle(me):
    a = todos.add("urgent thing")
    assert a["today"] is False
    todos.set_today(a["id"], True)
    assert todos.list_all()[0]["today"] is True
    todos.set_today(a["id"], False)
    assert todos.list_all()[0]["today"] is False


def test_toggle_flips_done(me):
    a = todos.add("a")
    todos.toggle(a["id"])
    assert todos.list_all()[0]["done"] is True
    todos.toggle(a["id"])
    assert todos.list_all()[0]["done"] is False


def test_delete_removes(me):
    a = todos.add("a")
    todos.add("b")
    todos.delete(a["id"])
    assert texts() == ["b"]


def test_unknown_id_is_value_error(me):
    with pytest.raises(ValueError):
        todos.toggle("nope")


def test_todo_today_flag_must_be_a_real_bool(me):
    from novi.features.today import api

    todos.add("Call the recruiter")
    tid = todos.list_all()[0]["id"]
    for bad in ("false", "true", 0, 1, None):
        with pytest.raises(ValueError):
            api.todo_today({"id": tid, "today": bad})
    assert todos.list_all()[0]["today"] is False
