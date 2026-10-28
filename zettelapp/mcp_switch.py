"""The MCP switch: MCP clients may use the vault only while ZettelApp is open and the
switch in its status bar is on. It is off every time ZettelApp starts.

The MCP server is a separate process, started by the MCP client (Claude Desktop, …),
so the app signals "on" with a named Windows event that it holds while the switch is
on. Windows destroys the event as soon as the switch goes off or the app exits, even
after a crash, so a stale "on" is impossible. The server checks for it before every
tool call. Elsewhere (development on other systems) a file with the app's process id
plays the same role.
"""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

EVENT_NAME = "Local\\ZettelApp.McpSwitchOn"  # per logon session
_SYNCHRONIZE = 0x00100000


def _kernel32():
    from ctypes import wintypes

    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateEventW.restype = wintypes.HANDLE
    k.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    k.OpenEventW.restype = wintypes.HANDLE
    k.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    return k


def _pid_file() -> Path:
    from zettelapp.paths import local_data_dir

    return local_data_dir() / "mcp-switch-on.pid"


class McpSwitch:
    """Held by the app; on() lets MCP clients in, off() shuts them out again."""

    def __init__(self) -> None:
        self._handle: int | None = None
        self._pid_path: Path | None = None

    @property
    def is_on(self) -> bool:
        return self._handle is not None or self._pid_path is not None

    def on(self) -> None:
        if self.is_on:
            return
        if sys.platform == "win32":
            handle = _kernel32().CreateEventW(None, True, False, EVENT_NAME)
            if not handle:
                raise OSError(ctypes.get_last_error(), "Could not switch MCP access on.")
            self._handle = handle
        else:
            path = _pid_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(os.getpid()), encoding="ascii")
            self._pid_path = path

    def off(self) -> None:
        if self._handle is not None:
            _kernel32().CloseHandle(self._handle)
            self._handle = None
        if self._pid_path is not None:
            self._pid_path.unlink(missing_ok=True)
            self._pid_path = None


def mcp_switched_on() -> bool:
    """True while ZettelApp is open with its MCP switch on. Fails closed."""
    try:
        if sys.platform == "win32":
            k = _kernel32()
            handle = k.OpenEventW(_SYNCHRONIZE, False, EVENT_NAME)
            if not handle:
                return False
            k.CloseHandle(handle)
            return True
        pid = int(_pid_file().read_text(encoding="ascii").strip())
        os.kill(pid, 0)  # raises if that process is gone
        return True
    except (OSError, ValueError):
        return False
