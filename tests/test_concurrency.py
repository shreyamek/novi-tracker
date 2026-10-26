"""Concurrent writes must not lose updates (ThreadingHTTPServer serves requests in parallel)."""
import threading
import time

import pytest

from novi import storage
from novi.features.today import todos
from novi.features.tracker import model


@pytest.fixture
def slow_reads(monkeypatch):
    """Widen the read-modify-write window so a missing lock reliably loses updates."""
    real_read = storage.read_json

    def slow(name, default):
        value = real_read(name, default)
        time.sleep(0.01)
        return value

    monkeypatch.setattr(storage, "read_json", slow)


def _run_concurrently(fn, count=20):
    errors = []
    barrier = threading.Barrier(count)

    def worker(i):
        try:
            barrier.wait()
            fn(i)
        except Exception as e:  # pragma: no cover - surfaced by the assertion below
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []


def test_concurrent_todo_adds_all_kept(me, slow_reads):
    _run_concurrently(lambda i: todos.add(f"task number {i:02d}"))
    texts = {t["text"] for t in todos.list_all()}
    assert texts == {f"task number {i:02d}" for i in range(20)}


def test_concurrent_tracker_adds_all_kept(me, slow_reads):
    def add_role(i):
        model.add({"company": f"Company {i:02d}", "role": "Analyst"})

    _run_concurrently(add_role)
    companies = {a["company"] for a in model.list_all()}
    assert companies == {f"Company {i:02d}" for i in range(20)}
