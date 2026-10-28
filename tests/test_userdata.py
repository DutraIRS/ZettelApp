"""Deleting the user's data on uninstall: settings, API keys, logs and backups, never notes."""

import os

from zettelapp import app, settings
from zettelapp.core import secrets


def test_remove_user_data_keeps_notes(tmp_path, monkeypatch, vault):
    # A private prefix and settings file: the real API keys and settings stay untouched.
    monkeypatch.setattr(secrets, "PREFIX", f"ZettelAppTest-{os.getpid()}/")
    monkeypatch.setenv("ZETTELAPP_SETTINGS_FILE", str(tmp_path / "settings.ini"))
    local = tmp_path / "LocalAppData" / "ZettelApp"
    (local / "Logs").mkdir(parents=True)
    (local / "Logs" / "zettelapp.log").write_text("log", encoding="utf-8")
    (local / "Backups").mkdir()
    monkeypatch.setattr("zettelapp.paths.local_data_dir", lambda: local)

    settings.put(settings.THEME, "dark")
    secrets.set_secret("llm/anthropic", "sk-test-value")
    secrets.set_secret("llm/openai", "sk-test-other")
    note = vault.create_note("Keep me", "My notes survive the uninstaller.")

    assert app.main(["ZettelApp.exe", "--remove-user-data"]) == 0
    assert settings.get(settings.THEME) == settings.DEFAULTS[settings.THEME]
    assert secrets.get_secret("llm/anthropic") is None
    assert secrets.get_secret("llm/openai") is None
    assert not local.exists()
    assert vault.get_note(note.id).title == "Keep me"  # the vault folder is never touched
