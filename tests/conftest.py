import pytest


@pytest.fixture
def me(tmp_path, monkeypatch):
    """An empty, throwaway me/ folder."""
    monkeypatch.setenv("NOVI_ME", str(tmp_path))
    return tmp_path
