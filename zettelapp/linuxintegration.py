"""Linux desktop integration (no-ops elsewhere).

- the per-user ``zettelapp://`` URL protocol, which lets links on Anki cards
  open the matching note. A user-local desktop file registers the handler
  (what a system package's .desktop file does automatically), and the handler
  only accepts zettelapp://note/<id> (see core.security);
- revealing files in the file manager, selecting them, through the
  org.freedesktop.FileManager1 D-Bus service (a plain folder opens otherwise).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from zettelapp import APP_NAME, URL_SCHEME

IS_LINUX = sys.platform.startswith("linux")

DESKTOP_FILE_CONTENT = """[Desktop Entry]
Type=Application
Version=1.0
Name=ZettelApp
GenericName=Zettelkasten
Comment=A Zettelkasten that helps you connect ideas
Exec={exec} %u
Terminal=false
NoDisplay=true
Categories=Office;ProjectManagement;
MimeType=x-scheme-handler/{scheme};
StartupWMClass=ZettelApp
"""


def _applications_dirs() -> list[Path]:
    """Where desktop entries may live, user-local first."""
    data_dirs = [os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")]
    data_dirs += os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    return [Path(d) / "applications" for d in data_dirs if d]


def desktop_file_path() -> Path:
    """The user-local desktop entry this registration writes."""
    return _applications_dirs()[0] / f"{APP_NAME.lower()}.desktop"


def _exec_argument(arg: str) -> str:
    """*arg* quoted for a desktop entry's Exec key: double quotes with \\ " ` $ escaped, %
    doubled, then backslashes doubled again because the key is itself an escaped string."""
    quoted = '"' + re.sub(r'([\\"`$])', r"\\\1", arg).replace("%", "%%") + '"'
    return quoted.replace("\\", "\\\\")


def launch_command() -> str:
    """Command a desktop entry should run for zettelapp:// links."""
    executable = _exec_argument(str(Path(sys.executable)))
    if getattr(sys, "frozen", False):
        return executable
    return f"{executable} -m {APP_NAME.lower()}"


def register_url_protocol() -> None:
    """Install a user-local desktop entry and make it the zettelapp:// handler."""
    if not IS_LINUX:
        return
    path = desktop_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        DESKTOP_FILE_CONTENT.format(exec=launch_command(), scheme=URL_SCHEME), encoding="utf-8"
    )
    _set_mime_handler(path.name)
    _update_desktop_database(path.parent)


def unregister_url_protocol() -> None:
    """Remove the user-local desktop entry, if it is ours."""
    if not IS_LINUX:
        return
    path = desktop_file_path()
    if path.exists() and f"x-scheme-handler/{URL_SCHEME}" in path.read_text(encoding="utf-8"):
        path.unlink(missing_ok=True)
        _update_desktop_database(path.parent)


def registered_command() -> str | None:
    """The Exec line of the desktop entry handling zettelapp:// links, if any."""
    if not IS_LINUX:
        return None
    for directory in _applications_dirs():
        for name in (
            f"{APP_NAME.lower()}.desktop",
            "io.github.dutrairs.zettelapp.desktop",
            "com.dutrairs.ZettelApp.desktop",
        ):
            entry = directory / name
            if not entry.is_file():
                continue
            text = entry.read_text(encoding="utf-8", errors="replace")
            if f"x-scheme-handler/{URL_SCHEME}" not in text:
                continue
            for line in text.splitlines():
                if line.startswith("Exec="):
                    return line.removeprefix("Exec=").strip()
    return None


def reveal_in_file_manager(path: str | Path) -> None:
    """Show *path* in the file manager: a file selected in its folder, a folder opened (as
    Explorer does on Windows)."""
    path = Path(path)
    if not IS_LINUX:  # pragma: no cover - Windows has its own implementation
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        return
    if not path.is_dir() and path.exists() and _file_manager_show_items(path):
        return
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices

    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path if path.is_dir() else path.parent)))


def _file_manager_show_items(target: str | Path) -> bool:
    """Select *target* through org.freedesktop.FileManager1, the standard "show and select"
    service, when a file manager provides it: already running, or started on demand by D-Bus,
    which is how Thunar, Nautilus, Dolphin and Nemo install it."""
    try:
        from PySide6.QtCore import QUrl
        from PySide6.QtDBus import QDBus, QDBusConnection, QDBusMessage
    except ImportError:  # pragma: no cover - QtDBus ships with PySide6-Essentials
        return False

    connection = QDBusConnection.sessionBus()
    if not connection.isConnected():
        return False
    service = "org.freedesktop.FileManager1"

    def ask_bus(method: str, *args):
        message = QDBusMessage.createMethodCall(
            "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", method
        )
        message.setArguments(list(args))
        reply = connection.call(message, QDBus.CallMode.Block, 2000)
        if reply.type() != QDBusMessage.MessageType.ReplyMessage or not reply.arguments():
            return None
        return reply.arguments()[0]

    if ask_bus("NameHasOwner", service) is not True and service not in (
        ask_bus("ListActivatableNames") or []
    ):
        return False
    message = QDBusMessage.createMethodCall(
        service, "/org/freedesktop/FileManager1", "org.freedesktop.FileManager1", "ShowItems"
    )
    uri = bytes(QUrl.fromLocalFile(str(Path(target).absolute())).toEncoded()).decode("ascii")
    message.setArguments([[uri], ""])
    connection.asyncCall(message)  # fire and forget: a file manager is opening
    return True


def _set_mime_handler(entry_name: str) -> None:
    try:
        subprocess.run(  # noqa: S603 - fixed argument list
            ["xdg-mime", "default", entry_name, f"x-scheme-handler/{URL_SCHEME}"],  # noqa: S607
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass  # the desktop file alone is enough for most desktops


def _update_desktop_database(directory: Path) -> None:
    try:
        subprocess.run(  # noqa: S603 - fixed argument list
            ["update-desktop-database", str(directory)],  # noqa: S607
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass  # optional; desktops re-scan their application folders anyway
