import subprocess
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().parents[1] / "tools" / "check_personal_data.py"


def run(repo, files):
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    for name, text in files.items():
        p = repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    subprocess.run(["git", "add", "-A", "-f"], cwd=repo, check=True)
    return subprocess.run([sys.executable, str(GUARD)], cwd=repo, capture_output=True, text=True)


def test_guard_flags_email_and_phone_in_tracked_file(tmp_path):
    r = run(tmp_path, {"notes.md": "reach me at jane.doe@gmail.com or (972) 555-0147"})
    assert r.returncode == 1
    assert "notes.md" in r.stdout


def test_guard_flags_tracked_me_files(tmp_path):
    r = run(tmp_path, {"me/profile.md": "hello"})
    assert r.returncode == 1


def test_guard_passes_on_fake_alex_example(tmp_path):
    r = run(tmp_path, {"tests/fixtures/alex.md": "Alex Example alex@example.com 555-0100"})
    assert r.returncode == 0, r.stdout


def test_guard_flags_tracked_resume_at_repo_root(tmp_path):
    r = run(tmp_path, {"resume.pdf": "%PDF-1.4 fake"})
    assert r.returncode == 1
    assert "resume.pdf" in r.stdout


def test_guard_flags_tracked_word_documents(tmp_path):
    r = run(tmp_path, {"cv.docx": "x", "old.doc": "x", "notes.rtf": "x"})
    assert r.returncode == 1
    assert "cv.docx" in r.stdout and "old.doc" in r.stdout and "notes.rtf" in r.stdout


def test_guard_passes_on_fixture_pdf(tmp_path):
    r = run(tmp_path, {"tests/fixtures/sample.pdf": "%PDF-1.4 fake"})
    assert r.returncode == 0, r.stdout
