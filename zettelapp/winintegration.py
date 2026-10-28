"""Windows shell integration (no-ops on other platforms).

- AppUserModelID so the taskbar groups windows and shows the app icon;
- dark/light window frames that match the app theme;
- the per-user zettelapp:// URL protocol, which lets links on Anki cards
  open the matching note. Registration lives under HKCU (no admin rights) and
  the handler only accepts zettelapp://note/<id> (see core.security).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from zettelapp import APP_NAME, APP_USER_MODEL_ID, URL_SCHEME

IS_WINDOWS = sys.platform == "win32"
_PROTOCOL_KEY = rf"Software\Classes\{URL_SCHEME}"


def set_app_user_model_id() -> None:
    if IS_WINDOWS:
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
        except (AttributeError, OSError):
            pass


def set_window_frame_dark(win_id: int, dark: bool) -> None:
    """Ask DWM to draw the title bar in dark or light mode (Windows 10 2004+)."""
    if not IS_WINDOWS:
        return
    import ctypes
    from ctypes import wintypes
    value = ctypes.c_int(1 if dark else 0)
    for attribute in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (and its pre-20H1 id)
        try:
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    wintypes.HWND(win_id), attribute, ctypes.byref(value), ctypes.sizeof(value)) == 0:
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
    if not IS_WINDOWS:
        return
    import winreg
    command = launch_command()
    icon_source = sys.executable if getattr(sys, "frozen", False) else command.split('"')[1]
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _PROTOCOL_KEY) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"URL:{APP_NAME} note link")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _PROTOCOL_KEY + r"\DefaultIcon") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{icon_source}",0')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _PROTOCOL_KEY + r"\shell\open\command") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)


def unregister_url_protocol() -> None:
    if not IS_WINDOWS:
        return
    import winreg
    for sub in (r"\shell\open\command", r"\shell\open", r"\shell", r"\DefaultIcon", ""):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, _PROTOCOL_KEY + sub)
        except OSError:
            pass


def registered_command() -> str | None:
    if not IS_WINDOWS:
        return None
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _PROTOCOL_KEY + r"\shell\open\command") as key:
            return winreg.QueryValueEx(key, "")[0]
    except OSError:
        return None


def reveal_in_explorer(path: str | Path) -> None:
    """Open File Explorer with *path* selected (or open the folder)."""
    path = Path(path)
    if IS_WINDOWS:
        if path.is_file():
            subprocess.Popen(["explorer", "/select,", str(path)])  # noqa: S603,S607 - fixed program, list args
        else:
            os.startfile(str(path if path.is_dir() else path.parent))  # noqa: S606
    else:  # pragma: no cover
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path if path.is_dir() else path.parent)))
