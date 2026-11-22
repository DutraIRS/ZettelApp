"""The Linux port: XDG paths, the Secret Service keyring, icons and desktop integration.

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
def test_sockets_and_locks_live_in_the_private_runtime_folder(tmp_path, monkeypatch):
    from zettelapp import paths

    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.delenv("FLATPAK_ID", raising=False)
    assert paths.runtime_dir() == tmp_path / "ZettelApp"
    # Flatpak shares only the app's own part of the runtime folder between its instances.
    monkeypatch.setenv("FLATPAK_ID", "io.github.dutairs.zettelapp")
    assert paths.runtime_dir() == tmp_path / "app" / "io.github.dutairs.zettelapp" / "ZettelApp"
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "missing"))
    assert paths.runtime_dir() == paths.local_data_dir()


@_linux
def test_documents_dir_prefers_the_desktops_redirected_folder(monkeypatch):
    from zettelapp import paths

    calls = []

    def fake_run(argv, **_):
        calls.append(argv)
        return type("Result", (), {"stdout": "/srv/onedrive/Documents\n"})()

    monkeypatch.setattr(paths.subprocess, "run", fake_run)
    assert paths.documents_dir() == Path("/srv/onedrive/Documents")
    assert calls == [["xdg-user-dir", "DOCUMENTS"]]  # DOCUMENT (singular) always answers ~


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

    # unset, xdg-user-dir answers the home folder itself: notes must not land straight in ~
    monkeypatch.setattr(
        paths.subprocess,
        "run",
        lambda argv, **_: type("Result", (), {"stdout": str(Path.home()) + "\n"})(),
    )
    assert paths.documents_dir() == Path.home() / "Documents"


@_linux
def test_documents_dir_asks_the_real_xdg_user_dir(tmp_path, monkeypatch):
    """A Portuguese desktop: user-dirs.dirs names ~/Documentos."""
    import shutil

    from zettelapp import paths

    if not shutil.which("xdg-user-dir"):
        pytest.skip("xdg-user-dir is not installed")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
    (tmp_path / ".config").mkdir()
    (tmp_path / ".config" / "user-dirs.dirs").write_text('XDG_DOCUMENTS_DIR="$HOME/Documentos"\n')
    assert paths.default_vault_dir() == tmp_path / "Documentos" / "ZettelApp"


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


def _private_keyring_only() -> None:
    """The keyring tests write to the default collection, so they run only when asked to, on a
    throwaway keyring, and never on the user's own session bus. To run them (Linux, from the
    repository folder):

        mkdir -p /tmp/zk/rt && chmod 700 /tmp/zk/rt
        env HOME=/tmp/zk XDG_DATA_HOME=/tmp/zk/data XDG_RUNTIME_DIR=/tmp/zk/rt dbus-run-session -- \
          sh -c 'echo -n test | gnome-keyring-daemon --unlock --components=secrets --daemonize;
                 ZETTELAPP_TEST_PRIVATE_KEYRING=1 python -m pytest tests/test_linux_port.py'
    """
    if os.environ.get("ZETTELAPP_TEST_PRIVATE_KEYRING") != "1":
        pytest.skip("needs a throwaway keyring: see _private_keyring_only()")
    bus = os.environ.get("DBUS_SESSION_BUS_ADDRESS", "")
    runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    if not bus or f"path={runtime}/bus" in bus or f"path=/run/user/{os.getuid()}/bus" in bus:
        pytest.skip("refusing to use the keyring of the user's own session bus")


@_linux
def test_secrets_round_trip_through_the_system_keyring(monkeypatch):
    from zettelapp.core import secrets

    _private_keyring_only()
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


@_linux
def test_every_libsecret_call_declares_its_argument_types():
    """Without argtypes ctypes passes a pointer as a 32-bit int: deleting a key crashed when
    the schema lay above 4 GB (allocated by a thread, or by a PIE Python)."""
    import re

    from zettelapp.core import secrets

    if secrets._lib is None:
        pytest.skip("libsecret is not installed")
    called = set(re.findall(r"_lib\.(\w+)\(", Path(secrets.__file__).read_text(encoding="utf-8")))
    assert "secret_password_clear_sync" in called
    for name in sorted(called):
        assert getattr(secrets._lib, name).argtypes is not None, name


@_linux
def test_secrets_work_from_another_thread(monkeypatch):
    """Memory a worker thread allocates lies above 4 GB, as in the packaged app."""
    import threading

    from zettelapp.core import secrets

    _private_keyring_only()
    if not secrets.secrets_available():
        pytest.skip("no Secret Service provider on this machine")
    monkeypatch.setattr(secrets, "PREFIX", f"ZettelAppTest-{os.getpid()}/")
    seen = []

    def work() -> None:
        secrets.set_secret("thread/key", "value")
        seen.append(secrets.get_secret("thread/key"))
        secrets.delete_secret("thread/key")
        seen.append(secrets.get_secret("thread/key"))

    worker = threading.Thread(target=work)
    worker.start()
    worker.join(30)
    assert seen == ["value", None]


# --- the desktop's accent colour and light/dark setting ---------------------------------


def _contrast(a: str, b: str) -> float:
    def luminance(color: str) -> float:
        from PySide6.QtGui import QColor

        q = QColor(color)
        channels = [
            c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in q.getRgbF()[:3]
        ]
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


@pytest.fixture
def desktop(monkeypatch, tmp_path):
    """A desktop session (not offscreen) whose tools answer what the test puts in *answers*;
    the portal (gdbus) and gsettings answer nothing unless told to."""
    from PySide6.QtWidgets import QApplication

    from zettelapp.ui import theme

    QApplication.instance() or QApplication(["test"])
    monkeypatch.setattr(theme, "_NO_DESKTOP", set())
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    answers: dict[str, str] = {}
    asked: list[str] = []

    def run(argv):
        asked.append(argv[0])
        return answers.get(argv[0])

    monkeypatch.setattr(theme, "_run_quietly", run)
    return type("Desktop", (), {"answers": answers, "asked": asked, "config": tmp_path})


@_linux
def test_xfce_keeps_the_windows_accent_whatever_gnome_and_kde_left_behind(desktop, monkeypatch):
    from zettelapp.ui import theme

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "XFCE")
    desktop.answers["gsettings"] = "'purple'\n"  # GNOME's key exists, but Xfce doesn't use it
    (desktop.config / "kdeglobals").write_text("[General]\nAccentColor=233,84,32\n")
    assert theme.build_theme("light").accent == "#005fb8"
    assert theme.build_theme("dark").accent == "#60cdff"
    assert "gsettings" not in desktop.asked


@_linux
def test_gnome_accent_comes_from_the_portal_then_gsettings(desktop, monkeypatch):
    from PySide6.QtGui import QColor

    from zettelapp.ui import theme

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "ubuntu:GNOME")
    desktop.answers["gsettings"] = "'purple'\n"
    purple = QColor(theme.build_theme("light").accent)
    assert abs(purple.hslHue() - QColor("#9141ac").hslHue()) <= 6
    desktop.answers["gdbus"] = "(<(0.2274, 0.5803, 0.2901)>,)\n"  # the portal's green wins
    green = QColor(theme.build_theme("light").accent)
    assert abs(green.hslHue() - QColor("#3a944a").hslHue()) <= 6


@_linux
def test_kde_accent_comes_from_kdeglobals(desktop, monkeypatch):
    from PySide6.QtGui import QColor

    from zettelapp.ui import theme

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    desktop.answers["gsettings"] = "'purple'\n"  # not KDE's
    kdeglobals = desktop.config / "kdeglobals"
    kdeglobals.write_text(
        "[Colors:Header][Inactive]\nBackgroundNormal=32,35,38\n"
        "[Colors:Selection]\nBackgroundNormal=61,174,233\n"
        "[General]\nAccentColor=233,84,32\n"
    )
    chosen = QColor(theme.build_theme("light").accent)
    assert abs(chosen.hslHue() - QColor(233, 84, 32).hslHue()) <= 6
    kdeglobals.write_text("[Colors:Selection]\nBackgroundNormal=61,174,233\n")
    scheme = QColor(theme.build_theme("dark").accent)  # no accent chosen: the colour scheme's
    assert abs(scheme.hslHue() - QColor(61, 174, 233).hslHue()) <= 6
    assert "gsettings" not in desktop.asked


@_linux
@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ("(<(0.2, 0.5, 0.9)>,)\n", "#3380e6"),
        ("(<(1.0, 0.0, 0.0)>,)\n", "#ff0000"),
        ("(<(-1.0, -1.0, -1.0)>,)\n", None),  # out of range: no accent colour set
        ("", None),
        (None, None),
    ],
)
def test_portal_accent_reply_is_parsed(desktop, reply, expected):
    from zettelapp.ui import theme

    if reply is not None:
        desktop.answers["gdbus"] = reply
    assert theme._portal_accent() == expected


@_linux
@pytest.mark.parametrize(
    "name", ["blue", "teal", "green", "yellow", "orange", "red", "pink", "purple", "slate"]
)
def test_desktop_accents_are_shaded_for_contrast_like_windows(name):
    """White text on the light theme's accent and black text on the dark theme's, as with
    the Windows accents (#005fb8 and #60cdff)."""
    from zettelapp.ui import theme

    color = theme._GNOME_ACCENTS[name]
    assert _contrast(theme._accent_shade(color, dark=False), "#ffffff") >= 4.5
    assert _contrast(theme._accent_shade(color, dark=True), "#000000") >= 7.0
    assert _contrast(theme._accent_shade(color, dark=True), "#202020") >= 4.5


@_linux
def test_no_accent_lookup_without_a_desktop(monkeypatch):
    """Offscreen (tests, screenshots, the self-test) there is no desktop to ask."""
    from PySide6.QtWidgets import QApplication

    from zettelapp.ui import theme

    QApplication.instance() or QApplication(["test"])
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    monkeypatch.setattr(theme, "_run_quietly", lambda argv: pytest.fail(f"asked {argv[0]}"))
    assert theme._linux_accent(False) is None


@_linux
def test_dark_mode_follows_qt_not_gnomes_color_scheme(desktop, monkeypatch):
    from zettelapp.ui import theme

    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "XFCE")
    desktop.answers["gsettings"] = "'prefer-dark'\n"
    assert theme.build_theme("system").dark is theme.system_prefers_dark()


# --- the zettelapp:// handler ---------------------------------------------------------------


@_linux
def test_url_handler_command_quotes_paths_with_spaces(monkeypatch):
    """The portable app unpacked in "My Apps": the Exec key must name the real program."""
    import re

    from zettelapp import linuxintegration

    monkeypatch.setattr(linuxintegration.sys, "frozen", True, raising=False)
    monkeypatch.setattr(linuxintegration.sys, "executable", "/home/me/My Apps/ZettelApp/zettelapp")
    assert linuxintegration.launch_command() == '"/home/me/My Apps/ZettelApp/zettelapp"'
    tricky = '/opt/a"b$c%d\\e/zettelapp'
    monkeypatch.setattr(linuxintegration.sys, "executable", tricky)
    value = linuxintegration.launch_command()
    # Undo the desktop entry's two levels of escaping as a desktop would: the string's
    # backslashes, then the quoted argument's (\\ " ` $), and %%.
    string = value.replace("\\\\", "\\")
    assert string.startswith('"') and string.endswith('"')
    assert re.sub(r"\\(.)", r"\1", string[1:-1]).replace("%%", "%") == tricky


# --- show in folder -----------------------------------------------------------------------


@_linux
def test_show_in_folder_selects_a_file_and_opens_a_folder(monkeypatch, tmp_path):
    """Like Explorer on Windows; a file manager that isn't running yet is started by D-Bus."""
    from PySide6.QtGui import QDesktopServices

    from zettelapp import linuxintegration

    note = tmp_path / "Notas de reunião" / "Ata #1 café.txt"
    note.parent.mkdir()
    note.write_text("x", encoding="utf-8")
    selected, opened = [], []
    monkeypatch.setattr(
        linuxintegration, "_file_manager_show_items", lambda p: selected.append(p) or True
    )
    monkeypatch.setattr(
        QDesktopServices, "openUrl", staticmethod(lambda url: opened.append(url.toLocalFile()))
    )
    linuxintegration.reveal_in_file_manager(note)
    linuxintegration.reveal_in_file_manager(note.parent)
    assert selected == [note] and opened == [str(note.parent)]

    # No org.freedesktop.FileManager1 on the bus: the file's folder opens instead.
    monkeypatch.setattr(linuxintegration, "_file_manager_show_items", lambda p: False)
    linuxintegration.reveal_in_file_manager(note)
    assert opened == [str(note.parent), str(note.parent)]


@_linux
def test_show_in_folder_needs_no_running_file_manager():
    """The D-Bus classes it uses exist (PySide6 has no QDBusCall), and without a session bus
    it reports "not shown" instead of failing."""
    from PySide6.QtDBus import QDBus, QDBusConnection, QDBusMessage  # noqa: F401

    from zettelapp import linuxintegration

    if os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        pytest.skip("a session bus is present")
    assert linuxintegration._file_manager_show_items(Path("/tmp")) is False


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


# --- icons without the Segoe fonts (more in test_icons_and_fonts.py) ----------------------


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


@_linux
def test_settings_logs_backups_and_cache_are_private(tmp_path, monkeypatch):
    import logging
    import stat

    from zettelapp import app, paths

    for name in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME"):
        monkeypatch.setenv(name, str(tmp_path / name))
    old_folder = tmp_path / "XDG_CACHE_HOME" / "ZettelApp"
    old_folder.mkdir(parents=True, mode=0o775)  # left by an earlier version
    old_umask = os.umask(0o002)
    root = logging.getLogger()
    handlers = list(root.handlers)
    try:
        app.configure_logging()
    finally:
        os.umask(old_umask)
        for handler in root.handlers[len(handlers) :]:
            handler.close()
            root.removeHandler(handler)
    for folder in (paths.config_dir(), paths.local_data_dir(), paths.cache_dir()):
        assert stat.S_IMODE(folder.stat().st_mode) == 0o700, folder
    log_file = paths.logs_dir() / "zettelapp.log"
    assert stat.S_IMODE(log_file.stat().st_mode) == 0o600
