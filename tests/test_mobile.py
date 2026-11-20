"""Tests for the Qt-free mobile facade used by the Android shell."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from zettelapp import androidintegration, mobile, paths


@pytest.fixture()
def private_dirs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Keep every facade location inside tmp: shell dirs + Documents override."""
    base, cache = tmp_path / "files", tmp_path / "cache"
    monkeypatch.setattr(paths, "_ANDROID_BASE", base)
    monkeypatch.setattr(paths, "_ANDROID_CACHE", cache)
    monkeypatch.setattr(mobile, "documents_dir", lambda: base / "Documents")
    monkeypatch.setattr(mobile, "local_data_dir", lambda: base)
    yield base, cache
    mobile.close_vault()


def test_bootstrap_registers_dirs_and_activity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen: dict = {}

    def fake_set_dirs(base, cache):
        seen["base"], seen["cache"] = base, cache

    monkeypatch.setattr(paths, "set_android_dirs", fake_set_dirs)
    androidintegration.bootstrap(str(tmp_path / "f"), str(tmp_path / "c"), activity="act")
    assert seen["base"] == str(tmp_path / "f")
    assert seen["cache"] == str(tmp_path / "c")
    assert androidintegration._activity == "act"
    androidintegration.set_activity(None)


def test_open_vault_creates_and_persists_choice(private_dirs) -> None:
    base, _cache = private_dirs
    opened = mobile.open_default_vault()
    assert opened["notes"] == 0
    # Documents on the private base is not mounted, so the vault is app-private.
    assert str(base) in opened["path"]
    # The choice is remembered for the next start.
    saved = json.loads((base / "mobile-vault.json").read_text())
    assert saved["vault"] == opened["path"]


def test_note_round_trip(private_dirs) -> None:
    created = mobile.create_note("First", "# Hello\n\nBody text.")
    assert created["title"] == "First"

    notes = mobile.list_notes()
    assert [n["id"] for n in notes] == [created["id"]]

    saved = mobile.save_note(created["id"], "First (edited)", "Updated.")
    assert saved["title"] == "First (edited)"

    note = mobile.read_note(created["id"])
    assert note["body"] == "Updated."
    assert "error" not in note

    assert mobile.read_note("no-such-id")["error"] == "not_found"
    assert mobile.save_note("no-such-id", "t", "b")["error"] == "not_found"

    status = mobile.status()
    assert status["notes"] == 1
    assert status["app"] == "ZettelApp"


def test_list_notes_orders_by_recency(private_dirs) -> None:
    first = mobile.create_note("First")
    second = mobile.create_note("Second")
    # created first → older; save it last to make it the most recent
    mobile.save_note(first["id"], "First", "touched later")
    mobile.save_note(second["id"], "Second", "")
    mobile.save_note(first["id"], "First", "touched last")
    titles = [n["title"] for n in mobile.list_notes()]
    assert titles == ["First", "Second"]
