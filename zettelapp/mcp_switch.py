"""The MCP switch: MCP clients may use the vault only while ZettelApp is open and the
switch in its status bar is on. It is off every time ZettelApp starts.

The MCP server is a separate process, started by the MCP client (Claude Desktop, …),
so the app signals "on" with a named Windows event that it holds while the switch is
on. Windows destroys the event as soon as the switch goes off or the app exits, even
after a crash, so a stale "on" is impossible. The server checks for it before every
tool call.

Linux has no named events; the app holds an exclusive lock (flock) on a private file
instead, in the user's runtime folder. The kernel releases the lock when the app closes
it or exits in any way, kill -9 included, so the switch can't be left on either. The
server only tries a non-blocking lock: if it gets one, nobody holds the switch.
"""

from __future__ import annotations

import ctypes
import errno
import os
import sys
import time
from pathlib import Path

EVENT_NAME = "Local\\ZettelApp.McpSwitchOn"  # per logon session
_SYNCHRONIZE = 0x00100000
LOCK_ATTEMPTS = 50  # a server's probe holds the lock for microseconds; retry for up to 0.5 s


def _kernel32():
    from ctypes import wintypes

    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateEventW.restype = wintypes.HANDLE
    k.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    k.OpenEventW.restype = wintypes.HANDLE
    k.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    return k


def _lock_file() -> Path:
    from zettelapp.paths import runtime_dir

    return runtime_dir() / "mcp-switch.lock"


def _open_lock_file(create: bool) -> int:
    flags = os.O_CLOEXEC | os.O_NOFOLLOW  # never inherited by programs the app starts
    if create:
        path = _lock_file()
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        return os.open(path, flags | os.O_RDWR | os.O_CREAT, 0o600)
    return os.open(_lock_file(), flags | os.O_RDONLY)


class McpSwitch:
    """Held by the app; on() lets MCP clients in, off() shuts them out again."""

    def __init__(self) -> None:
        self._handle: int | None = None
        self._lock_fd: int | None = None

    @property
    def is_on(self) -> bool:
        return self._handle is not None or self._lock_fd is not None

    def on(self) -> None:
        if self.is_on:
            return
        if sys.platform == "win32":
            handle = _kernel32().CreateEventW(None, True, False, EVENT_NAME)
            if not handle:
                raise OSError(ctypes.get_last_error(), "Could not switch MCP access on.")
            self._handle = handle
            return
        import fcntl

        fd = _open_lock_file(create=True)
        try:
            for _attempt in range(LOCK_ATTEMPTS):
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    time.sleep(0.01)  # a server is looking, or another ZettelApp holds it
            else:
                raise OSError(errno.EWOULDBLOCK, "Could not switch MCP access on.")
        except OSError:
            os.close(fd)
            raise
        self._lock_fd = fd

    def off(self) -> None:
        if self._handle is not None:
            _kernel32().CloseHandle(self._handle)
            self._handle = None
        if self._lock_fd is not None:
            os.close(self._lock_fd)  # closing releases the lock
            self._lock_fd = None


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
        import fcntl

        fd = _open_lock_file(create=False)  # no file: never switched on
        try:
            fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return True  # the app holds the lock
        finally:
            os.close(fd)  # also releases the probe's own lock
        return False
    except (OSError, ValueError):
        return False
