"""Tests for Android integration layer, path resolution, security, and secrets fallbacks."""

from __future__ import annotations

from pathlib import Path

import pytest

from zettelapp import androidintegration, paths
from zettelapp.core import anki, secrets, security


def test_android_integration_constants() -> None:
    assert isinstance(androidintegration.IS_ANDROID, bool)
    assert androidintegration.ANKIDROID_PACKAGE == "com.ichi2.anki"
    assert androidintegration.ANKIDROID_AUTHORITY == "com.ichi2.anki.flashcards"


def test_android_integration_url_protocol() -> None:
    command = androidintegration.launch_command()
    assert "zettelapp://note/" in command

    # Registration methods should execute without error
    androidintegration.register_url_protocol()
    androidintegration.unregister_url_protocol()

    if androidintegration.IS_ANDROID:
        assert androidintegration.registered_command() == command
    else:
        assert androidintegration.registered_command() is None


def test_android_integration_helpers(tmp_path: Path) -> None:
    # Reveal file manager should execute safely on non-Android or fallback
    androidintegration.reveal_in_file_manager(tmp_path)

    # AnkiDroid check fallback
    available = androidintegration.is_ankidroid_available()
    assert isinstance(available, bool)

    uri = androidintegration.get_ankidroid_content_uri()
    assert uri == "content://com.ichi2.anki.flashcards"

    # Zotero URL launcher fallback
    res = androidintegration.launch_zotero_url("zotero://select/items/12345678")
    assert isinstance(res, bool)


def test_paths_android_overrides(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths, "IS_ANDROID", True)
    monkeypatch.setenv("ANDROID_PRIVATE", str(tmp_path))
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))

    doc_dir = paths.documents_dir()
    assert doc_dir == tmp_path / "Documents" or doc_dir == Path("/storage/emulated/0/Documents")

    data_dir = paths.local_data_dir()
    assert data_dir == tmp_path / "ZettelApp"

    c_dir = paths.cache_dir()
    assert c_dir == tmp_path / "cache" / "ZettelApp"


def test_secrets_android_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(secrets, "IS_ANDROID", True)
    monkeypatch.setattr(secrets, "IS_WINDOWS", False)
    monkeypatch.setattr(secrets, "IS_LINUX", False)

    # secrets_available should be False, storing in memory securely
    assert not secrets.secrets_available()

    secrets.set_secret("test/key", "my_secret_token")
    assert secrets.get_secret("test/key") == "my_secret_token"
    secrets.delete_secret("test/key")
    assert secrets.get_secret("test/key") is None


def test_security_app_url_parsing() -> None:
    url = security.app_url("20261028120000")
    assert url == "zettelapp://note/20261028120000"
    assert security.parse_app_url(url) == "20261028120000"
    assert security.parse_app_url("zettelapp://invalid") is None


def test_anki_android_module_flag() -> None:
    assert hasattr(anki, "IS_ANDROID")
