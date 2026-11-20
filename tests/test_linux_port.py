"""The Linux port: XDG paths, the Secret Service keyring, painted icons and desktop integration.

Windows-specific behaviour keeps its own tests; these cover the POSIX side of
every platform dispatch added by the port.
"""

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_linux = pytest.mark.skipif(sys.platform != "linux", reason="Linux-specific behaviour")


# --- XDG base directories ---------------------------------------------------------------


@_linux
def test_data_and_cache_follow_the_xdg_base_directories(tmp_path, monkeypatch):
    from zettelapp import paths

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    assert paths.local_data_dir() == tmp_path / "data" / "ZettelApp"
    assert paths.cache_dir() == tmp_path / "cache" / "ZettelApp"
    assert paths.logs_dir() == tmp_path / "data" / "ZettelApp" / "Logs"
    assert paths.backups_dir() == tmp_path / "data" / "ZettelApp" / "Backups"


@_linux
def test_xdg_defaults_apply_when_the_environment_is_unset(monkeypatch):
    from zettelapp import paths

    monkeypatch.setenv("XDG_DATA_HOME", "")
    monkeypatch.setenv("XDG_CACHE_HOME", "")
    assert paths.local_data_dir() == Path.home() / ".local" / "share" / "ZettelApp"
    assert paths.cache_dir() == Path.home() / ".cache" / "ZettelApp"


@_linux
def test_documents_dir_prefers_the_desktops_redirected_folder(monkeypatch):
    from zettelapp import paths

    calls = []

    def fake_run(argv, **_):
        calls.append(argv)
        return type("Result", (), {"stdout": "/srv/onedrive/Documents\n"})()

    monkeypatch.setattr(paths.subprocess, "run", fake_run)
    assert paths.documents_dir() == Path("/srv/onedrive/Documents")
    assert calls == [["xdg-user-dir", "DOCUMENT"]]


@_linux
def test_documents_dir_falls_back_to_home_documents(monkeypatch):
    from zettelapp import paths

    def no_tool(argv, **_):
        raise FileNotFoundError

    monkeypatch.setattr(paths.subprocess, "run", no_tool)
    assert paths.documents_dir() == Path.home() / "Documents"

    # a plain answer equals the fallback: treat it as "not redirected"
    monkeypatch.setattr(
        paths.subprocess,
        "run",
        lambda argv, **_: type("Result", (), {"stdout": str(Path.home() / "Documents") + "\n"})(),
    )
    assert paths.documents_dir() == Path.home() / "Documents"


# --- the Secret Service keyring ----------------------------------------------------------


@_linux
def test_secrets_fall_back_to_memory_without_a_keyring(monkeypatch):
    from zettelapp.core import secrets

    monkeypatch.setattr(secrets, "secrets_available", lambda: False)
    monkeypatch.setattr(secrets, "PREFIX", "ZettelAppTest-mem/")
    secrets.set_secret("llm/anthropic", "k1")
    assert secrets.get_secret("llm/anthropic") == "k1"
    secrets.set_secret("llm/anthropic", "k2")  # overwrite
    assert secrets.get_secret("llm/anthropic") == "k2"
    secrets.delete_secret("llm/anthropic")
    assert secrets.get_secret("llm/anthropic") is None
    secrets.set_secret("llm/openai", "k3")
    assert secrets.delete_all() == 1
    assert secrets.get_secret("llm/openai") is None


@_linux
def test_secrets_round_trip_through_the_system_keyring(monkeypatch):
    from zettelapp.core import secrets

    if not secrets.secrets_available():
        pytest.skip("no Secret Service provider on this machine")
    monkeypatch.setattr(secrets, "PREFIX", f"ZettelAppTest-{os.getpid()}/")
    secrets.set_secret("llm/anthropic", "first")
    secrets.set_secret("llm/anthropic", "second")  # upsert, not a duplicate
    assert secrets.get_secret("llm/anthropic") == "second"
    secrets.delete_secret("llm/anthropic")
    assert secrets.get_secret("llm/anthropic") is None
    secrets.set_secret("misc/a", "1")
    secrets.set_secret("misc/b", "2")
    assert secrets.delete_all() == 2
    assert secrets.get_secret("misc/a") is None
    assert secrets.get_secret("misc/b") is None


# --- POSIX file-link security ------------------------------------------------------------


@_linux
@pytest.mark.parametrize(
    "target",
    [
        "//server/share/doc.txt",  # looking a network path up can leak credentials
        "file://server/share/doc.txt",
        "file://///server/share/doc.txt",
        "relative/path.txt",
        "file:///a.txt?x=1",
        "file:///bad%00name.txt",
        "https://example.com/a.pdf",
        "",
        None,
    ],
)
def test_posix_file_links_stay_local(target):
    from zettelapp.core.security import local_file_path

    assert local_file_path(target) is None


@_linux
def test_posix_file_url_escapes_spaces_and_fragments():
    from zettelapp.core.security import file_url, local_file_path

    path = "/home/me/My Files/notes #1.txt"
    url = file_url(path)
    assert url == "file:///home/me/My%20Files/notes%20%231.txt"
    assert local_file_path(url) == path


# --- painted icons (no Segoe fonts on Linux) ----------------------------------------------


def test_every_icon_has_a_painted_fallback():
    from zettelapp.ui import icons, iconshapes

    missing = [name for name in icons.GLYPHS if not iconshapes.has_fallback(name)]
    assert missing == []


def test_every_painted_icon_draws_cleanly():
    from PySide6.QtGui import QColor, QPainter, QPixmap
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication(["test"])
    from zettelapp.ui import iconshapes

    pixmap = QPixmap(24, 24)
    painter = QPainter(pixmap)
    try:
        for name in iconshapes.SHAPES:
            assert iconshapes.draw(name, painter, 24, QColor("#111111")), name
        assert not iconshapes.draw("no-such-icon", painter, 24, QColor("#111111"))
    finally:
        painter.end()


@_linux
def test_format_buttons_carry_real_glyph_names_in_every_language():
    from zettelapp.ui import icons

    for language in ("pt_BR", "es", "fr", "de", "it", "ru", "ko", "en"):
        bold, italic = icons.format_glyphs(language)
        assert bold in icons.GLYPHS and italic in icons.GLYPHS


@_linux
def test_text_glyphs_stay_empty_where_the_icon_font_is_missing():
    from zettelapp.ui import icons

    if icons._icon_family() is not None:
        pytest.skip("a Windows icon font is installed")
    assert icons.glyph("bold") == ""
