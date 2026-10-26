from tools import update_check


def test_me_path_detected():
    assert update_check.touches_me(["app/novi/claims.py", "me/profile.md"])
    assert update_check.touches_me(["me\\tracker.json"])
    assert update_check.touches_me(["me"])


def test_app_path_not_flagged():
    assert not update_check.touches_me(["app/novi/claims.py", "tools/render_pdf.py", "mev/notes.md", "docs/me/x.md"])
    assert not update_check.touches_me([])
