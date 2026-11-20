"""Standard per-platform locations for user data.

Windows follows its own conventions:
- notes (user documents) live in the Documents known folder, which may be
  redirected to OneDrive, so it is resolved through SHGetKnownFolderPath;
- logs, backups and caches are machine-local, under %LOCALAPPDATA%;
- preferences are stored by QSettings in the registry (HKCU\\Software).

Linux follows the XDG base directories:
- notes live in ~/Documents (or xdg-user-dir DOCUMENT, which follows the
  desktop's localisation and redirections);
- logs, backups and the semantic search model live under
  $XDG_DATA_HOME/ZettelApp (default ~/.local/share/ZettelApp);
- the small UI cache lives under $XDG_CACHE_HOME/ZettelApp (default
  ~/.cache/ZettelApp);
- preferences are stored by QSettings as ~/.config/ZettelApp/ZettelApp.conf.

Android keeps everything app-private (scoped storage):
- notes default to Documents/ZettelApp on shared storage when it is visible,
  otherwise under the app's private files directory;
- logs, backups and preferences live under the app's private data directory,
  which the Android shell hands over at startup (Chaquopy: files dir);
- the small UI cache lives under the app's private cache directory.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from zettelapp import APP_NAME

IS_WINDOWS = sys.platform == "win32"
IS_ANDROID = sys.platform == "android" or hasattr(sys, "getandroidapilevel")

# The Android shell registers its private directories at startup (Python inside
# Chaquopy cannot discover them on its own); they override the env fallbacks.
_ANDROID_BASE: Path | None = None
_ANDROID_CACHE: Path | None = None


def set_android_dirs(base: str | Path | None, cache: str | Path | None) -> None:
    """Register the app's private data and cache directories (Android shell)."""
    global _ANDROID_BASE, _ANDROID_CACHE
    _ANDROID_BASE = Path(base) if base else None
    _ANDROID_CACHE = Path(cache) if cache else None


def _android_base() -> Path:
    """The app's private storage root, as handed over by the shell or env."""
    if _ANDROID_BASE:
        return _ANDROID_BASE
    for var in ("ANDROID_PRIVATE", "ANDROID_ARGUMENT"):
        value = os.environ.get(var)
        if value:
            return Path(value)
    return Path.home()


def _android_documents() -> Path | None:
    """The shared Documents folder, when its view is mounted on the device."""
    shared = Path("/storage/emulated/0/Documents")
    return shared if shared.is_dir() else None


def _known_folder_documents() -> Path | None:
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    # FOLDERID_Documents {FDD39AD0-238F-46AF-ADB4-6C85480369C7}
    folder_id = GUID(
        0xFDD39AD0,
        0x238F,
        0x46AF,
        (ctypes.c_ubyte * 8)(0xAD, 0xB4, 0x6C, 0x85, 0x48, 0x03, 0x69, 0xC7),
    )
    path_ptr = ctypes.c_wchar_p()
    try:
        result = ctypes.windll.shell32.SHGetKnownFolderPath(
            ctypes.byref(folder_id), 0, None, ctypes.byref(path_ptr)
        )
        if result != 0 or not path_ptr.value:
            return None
        return Path(path_ptr.value)
    except OSError:
        return None
    finally:
        if path_ptr:
            ctypes.windll.ole32.CoTaskMemFree(path_ptr)


def documents_dir() -> Path:
    if IS_ANDROID:
        return _android_documents() or _android_base() / "Documents"
    if IS_WINDOWS:
        return _known_folder_documents() or Path.home() / "Documents"
    return _xdg_documents() or Path.home() / "Documents"


def _xdg_documents() -> Path | None:
    """The desktop's Documents folder (localised or redirected), via xdg-user-dir."""
    try:
        result = subprocess.run(  # noqa: S603 - fixed argument list
            ["xdg-user-dir", "DOCUMENT"],  # noqa: S607 - always on PATH on Linux desktops
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    path = result.stdout.strip()
    # xdg-user-dir answers the fallback ~ itself when unset; treat that as "no answer"
    # so a redirected folder is preferred but the default is built by the caller.
    if not path or path == str(Path.home() / "Documents"):
        return None
    return Path(path)


def local_data_dir() -> Path:
    """Machine-local data: logs, backups, the semantic search model."""
    if IS_ANDROID:
        return _android_base() / APP_NAME
    if IS_WINDOWS:
        base = os.environ.get("LOCALAPPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Local"
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        root = Path(base)
    return root / APP_NAME


def cache_dir() -> Path:
    """Non-essential files the app can rebuild (theme indicator images)."""
    if IS_ANDROID:
        base = _ANDROID_CACHE or Path(os.environ.get("CACHE_DIR") or str(_android_base() / "cache"))
        return base / APP_NAME
    if IS_WINDOWS:
        return local_data_dir() / "Cache"
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / APP_NAME


def default_vault_dir() -> Path:
    return documents_dir() / APP_NAME


def logs_dir() -> Path:
    return local_data_dir() / "Logs"


def backups_dir() -> Path:
    return local_data_dir() / "Backups"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def resource_path(*parts: str) -> Path:
    """Path to a bundled resource, both from source and in a PyInstaller build."""
    base = getattr(sys, "_MEIPASS", None)
    root = Path(base) / "zettelapp" if base else Path(__file__).resolve().parent
    return root.joinpath("resources", *parts)
