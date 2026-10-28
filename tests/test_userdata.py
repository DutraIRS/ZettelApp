"""Deleting the user's data on uninstall: settings, API keys, logs, backups and the vaults."""

import os

from tests.conftest import tiny_png
from zettelapp import app, settings
from zettelapp.core import secrets
from zettelapp.core.storage import Vault


def _isolate(tmp_path, monkeypatch):
    # A private prefix and settings file: the real API keys and settings stay untouched.
    monkeypatch.setattr(secrets, "PREFIX", f"ZettelAppTest-{os.getpid()}/")
    monkeypatch.setenv("ZETTELAPP_SETTINGS_FILE", str(tmp_path / "settings.ini"))
    local = tmp_path / "LocalAppData" / "ZettelApp"
    (local / "Logs").mkdir(parents=True)
    (local / "Logs" / "zettelapp.log").write_text("log", encoding="utf-8")
    (local / "Backups").mkdir()
    monkeypatch.setattr("zettelapp.paths.local_data_dir", lambda: local)
    monkeypatch.setattr(
        "zettelapp.paths.default_vault_dir", lambda: tmp_path / "nowhere" / "ZettelApp"
    )
    return local


def test_remove_user_data_deletes_settings_keys_and_vaults(tmp_path, monkeypatch):
    local = _isolate(tmp_path, monkeypatch)
    folder = tmp_path / "Documents" / "ZettelApp"
    vault = Vault.open(folder)
    vault.create_note("Gone", "Removed with the uninstaller.")
    vault.close()
    other = tmp_path / "Elsewhere" / "Work"
    Vault.open(other).close()

    settings.put(settings.THEME, "dark")
    settings.put(settings.LAST_VAULT, str(folder))
    settings.put(settings.RECENT_VAULTS, [str(folder), str(other)])
    secrets.set_secret("llm/anthropic", "sk-test-value")
    secrets.set_secret("llm/openai", "sk-test-other")

    assert app.main(["ZettelApp.exe", "--remove-user-data"]) == 0
    assert settings.get(settings.THEME) == settings.DEFAULTS[settings.THEME]
    assert secrets.get_secret("llm/anthropic") is None
    assert secrets.get_secret("llm/openai") is None
    assert not local.exists()
    assert not folder.exists()  # database and images gone, so the empty folder goes too
    assert not other.exists()


def test_remove_user_data_keeps_files_it_did_not_create(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    folder = tmp_path / "Documents" / "ZettelApp"
    Vault.open(folder).close()
    (folder / "my-thesis.docx").write_text("mine", encoding="utf-8")
    settings.put(settings.LAST_VAULT, str(folder))

    assert app.main(["ZettelApp.exe", "--remove-user-data"]) == 0
    assert not Vault.is_vault(folder)
    assert (folder / "my-thesis.docx").read_text(encoding="utf-8") == "mine"


def test_remove_user_data_keeps_the_users_own_files_in_the_assets_folder(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    folder = tmp_path / "Documents"
    (folder / "assets").mkdir(parents=True)
    (folder / "assets" / "logo.png").write_text("mine", encoding="utf-8")
    vault = Vault.open(folder)  # a vault made in a folder that already had an assets folder
    image = vault.add_image(tiny_png(), "pic.png")
    vault.close()
    settings.put(settings.LAST_VAULT, str(folder))

    assert app.main(["ZettelApp.exe", "--remove-user-data"]) == 0
    assert not Vault.is_vault(folder)
    assert not (folder / "assets" / image).exists()
    assert (folder / "assets" / "logo.png").read_text(encoding="utf-8") == "mine"


def test_remove_user_data_ignores_folders_that_are_not_vaults(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    folder = tmp_path / "Documents"
    folder.mkdir()
    (folder / "photo.jpg").write_text("x", encoding="utf-8")
    (folder / "assets").mkdir()
    (folder / "assets" / "keep.txt").write_text("x", encoding="utf-8")
    settings.put(settings.LAST_VAULT, str(folder))

    assert app.main(["ZettelApp.exe", "--remove-user-data"]) == 0
    assert (folder / "assets" / "keep.txt").exists()
    assert (folder / "photo.jpg").exists()
