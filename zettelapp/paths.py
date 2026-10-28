"""Standard Windows locations for user data.

Follows Windows conventions:
- notes (user documents) live in the Documents known folder, which may be
  redirected to OneDrive, so it is resolved through SHGetKnownFolderPath;
- logs, backups and caches are machine-local, under %LOCALAPPDATA%;
- preferences are stored by QSettings in the registry (HKCU\\Software).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from zettelapp import APP_NAME


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
    return _known_folder_documents() or Path.home() / "Documents"


def local_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) if base else Path.home() / "AppData" / "Local"
    return root / APP_NAME


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
