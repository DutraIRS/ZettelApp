"""Shell integration (Windows-specific here, Linux in linuxintegration.py).

- AppUserModelID so the Windows taskbar groups windows and shows the app icon;
- dark/light window frames that match the app theme;
- the per-user zettelapp:// URL protocol, which lets links on Anki cards
  open the matching note. On Windows registration lives under HKCU (no admin
  rights); on Linux it is a user-local desktop file (see linuxintegration).
  The registration only accepts zettelapp://note/<id> (see core.security).
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from zettelapp import APP_NAME, APP_USER_MODEL_ID, URL_SCHEME, linuxintegration

IS_WINDOWS = sys.platform == "win32"
IS_LINUX = linuxintegration.IS_LINUX
_PROTOCOL_KEY = rf"Software\Classes\{URL_SCHEME}"
# Lets Windows show toasts for an app without a Start menu shortcut (the portable copy).
_APP_ID_KEY = rf"Software\Classes\AppUserModelId\{APP_USER_MODEL_ID}"


def set_app_user_model_id() -> None:
    if IS_WINDOWS:
        import ctypes

        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
        except (AttributeError, OSError):
            pass


def is_packaged() -> bool:
    """True when running from an MSIX package (the Microsoft Store build): Windows then
    registers zettelapp:// links from the package's manifest, and the Store updates the app."""
    if not IS_WINDOWS:
        return False
    import ctypes
    from ctypes import wintypes

    length = wintypes.UINT(0)
    try:
        # ERROR_INSUFFICIENT_BUFFER (122) means there is a package name to fetch;
        # APPMODEL_ERROR_NO_PACKAGE (15700) means an ordinary process.
        result = ctypes.windll.kernel32.GetCurrentPackageFullName(ctypes.byref(length), None)
    except (AttributeError, OSError):
        return False
    return result == 122


def _package_family_name() -> str | None:
    import ctypes
    from ctypes import wintypes

    length = wintypes.UINT(256)
    buffer = ctypes.create_unicode_buffer(length.value)
    try:
        result = ctypes.windll.kernel32.GetCurrentPackageFamilyName(ctypes.byref(length), buffer)
    except (AttributeError, OSError):
        return None
    return buffer.value if result == 0 else None


def _toast_app_id() -> str | None:
    """The AppUserModelID Windows shows a toast under, or None when there is none to use.

    The package has its own; the installed app's comes from its Start menu shortcut (an
    unpackaged app needs one, or Windows drops its toasts); the portable copy registers it with
    the zettelapp:// links (register_url_protocol)."""
    if is_packaged():
        family = _package_family_name()
        return f"{family}!{APP_NAME}" if family else None
    for base in (os.environ.get("APPDATA"), os.environ.get("PROGRAMDATA")):
        if (
            base
            and (Path(base) / "Microsoft/Windows/Start Menu/Programs" / f"{APP_NAME}.lnk").exists()
        ):
            return APP_USER_MODEL_ID
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _APP_ID_KEY):
            return APP_USER_MODEL_ID
    except OSError:
        return None


def _links_open_the_app() -> bool:
    """Whether zettelapp:// links are handled, by the package or a registration."""
    if is_packaged():
        return True
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf"{URL_SCHEME}\shell\open\command"):
            return True
    except OSError:
        return False


@dataclass(frozen=True)
class ToastText:
    """The words on an alarm toast, in the interface language."""

    open: str  # the button that opens the note
    dismiss: str  # the button that closes the toast
    caption: str  # the small line under the text, e.g. "ZettelApp · Alarm"


def toast_xml(title: str, body: str, url: str, text: ToastText, icon: Path | None = None) -> str:
    """A reminder toast like Windows' own: the app's icon, the note's title and text, a caption,
    and side-by-side Open note / Dismiss buttons. A click on the toast or on Open note opens
    *url* (a zettelapp://note/<id> link); it stays on screen until one or the other."""
    from xml.sax.saxutils import escape, quoteattr

    logo = (
        f'<image placement="appLogoOverride" hint-crop="none" src={quoteattr(icon.as_uri())}/>'
        if icon is not None
        else ""
    )
    return (
        f'<toast activationType="protocol" scenario="reminder" launch={quoteattr(url)}>'
        '<visual><binding template="ToastGeneric">'
        f"<text>{escape(title)}</text><text>{escape(body)}</text>"
        f'<text placement="attribution">{escape(text.caption)}</text>{logo}'
        "</binding></visual>"
        "<actions>"
        f'<action content={quoteattr(text.open)} activationType="protocol" arguments={quoteattr(url)}/>'
        f'<action content={quoteattr(text.dismiss)} activationType="system" arguments="dismiss"/>'
        "</actions>"
        '<audio src="ms-winsoundevent:Notification.Reminder"/>'
        "</toast>"
    )


def show_toast(
    title: str, body: str, note_id: str, text: ToastText, icon: Path | None = None
) -> bool:
    """Show a Windows toast for an alarm; clicking it opens the note through its zettelapp://
    link, which brings the running window forward (see MainWindow.handle_message).

    Qt's tray balloon isn't used where this works: Windows 11 shows it as a toast too, but a
    click on it never reaches the app (it shows the desktop instead). False when a toast can't
    be shown or clicked through (no app id, links not registered), so the caller falls back
    to the balloon. The toast goes through Windows' own notification API, from PowerShell."""
    if not IS_WINDOWS:
        return False
    app_id = _toast_app_id()
    if app_id is None or not _links_open_the_app():
        return False
    import base64

    xml = toast_xml(title, body, f"{URL_SCHEME}://note/{note_id}", text, icon)

    def quoted(text: str) -> str:  # a PowerShell single-quoted string
        return "'" + text.replace("'", "''") + "'"

    script = (
        "$ErrorActionPreference = 'Stop';"
        "[void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications,"
        " ContentType = WindowsRuntime];"
        "[void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime];"
        "$xml = New-Object Windows.Data.Xml.Dom.XmlDocument;"
        f"$xml.LoadXml({quoted(xml)});"
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml);"
        f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier({quoted(app_id)})"
        ".Show($toast)"
    )
    root = os.environ.get("SystemRoot", r"C:\Windows")
    powershell = Path(root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    try:
        subprocess.Popen(
            [
                str(powershell),
                "-NoProfile",
                "-NonInteractive",
                "-WindowStyle",
                "Hidden",
                "-EncodedCommand",
                base64.b64encode(script.encode("utf-16-le")).decode("ascii"),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError:
        return False
    return True


def mcp_alias() -> Path:
    """Where the packaged app's execution alias for the MCP server lives: files inside
    WindowsApps can't be started by their path, the alias can."""
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return base / "Microsoft" / "WindowsApps" / "zettelapp-mcp.exe"


def set_window_frame_dark(win_id: int, dark: bool) -> None:
    """Ask DWM to draw the title bar in dark or light mode (Windows 10 2004+)."""
    if not IS_WINDOWS:
        return
    import ctypes
    from ctypes import wintypes

    value = ctypes.c_int(1 if dark else 0)
    for attribute in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (and its pre-20H1 id)
        try:
            if (
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    wintypes.HWND(win_id), attribute, ctypes.byref(value), ctypes.sizeof(value)
                )
                == 0
            ):
                return
        except (AttributeError, OSError):
            return


def allow_foreground_switch() -> None:
    """Let the already-running instance bring itself to the front."""
    if IS_WINDOWS:
        import ctypes

        try:
            ctypes.windll.user32.AllowSetForegroundWindow(-1)  # ASFW_ANY
        except (AttributeError, OSError):
            pass


def launch_command() -> str:
    """Command line Windows should run for zettelapp:// links."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" "%1"'
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    exe = pythonw if pythonw.exists() else Path(sys.executable)
    return f'"{exe}" -m zettelapp "%1"'


def register_url_protocol() -> None:
    if IS_WINDOWS:
        import winreg

        command = launch_command()
        icon_source = sys.executable if getattr(sys, "frozen", False) else command.split('"')[1]
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _PROTOCOL_KEY) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"URL:{APP_NAME} note link")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _PROTOCOL_KEY + r"\DefaultIcon") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{icon_source}",0')
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER, _PROTOCOL_KEY + r"\shell\open\command"
        ) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
        # The app's name and icon for its alarm toasts, which open notes through these links.
        from zettelapp.paths import resource_path

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _APP_ID_KEY) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            icon = resource_path("icon-256.png")
            if icon.exists():
                winreg.SetValueEx(key, "IconUri", 0, winreg.REG_SZ, str(icon))
    else:
        linuxintegration.register_url_protocol()


def unregister_url_protocol() -> None:
    if IS_WINDOWS:
        import winreg

        for sub in (r"\shell\open\command", r"\shell\open", r"\shell", r"\DefaultIcon", ""):
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, _PROTOCOL_KEY + sub)
            except OSError:
                pass
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, _APP_ID_KEY)
        except OSError:
            pass
    else:
        linuxintegration.unregister_url_protocol()


def registered_command() -> str | None:
    if IS_WINDOWS:
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, _PROTOCOL_KEY + r"\shell\open\command"
            ) as key:
                return winreg.QueryValueEx(key, "")[0]
        except OSError:
            return None
    return linuxintegration.registered_command()


def reveal_in_explorer(path: str | Path) -> None:
    """Open the file manager with *path* selected (or open the folder)."""
    path = Path(path)
    if IS_WINDOWS:
        if path.is_file():
            # Full path: a bare "explorer" would be looked up in the current folder first.
            explorer = Path(os.environ.get("WINDIR", r"C:\Windows")) / "explorer.exe"
            subprocess.Popen([str(explorer), "/select,", str(path)])  # noqa: S603 - list args
        else:
            os.startfile(str(path if path.is_dir() else path.parent))  # noqa: S606
    else:
        linuxintegration.reveal_in_file_manager(path)
