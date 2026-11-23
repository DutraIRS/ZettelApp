"""Desktop notifications on Linux (org.freedesktop.Notifications).

Windows shows alarms as a toast from the notification-area icon. Many Linux desktops have no
tray (GNOME by default), so there the notification goes straight to the desktop's
notification service, which every desktop provides; clicking it opens the note, as the
toast does on Windows.

PySide6 can't send a D-Bus uint32 (Notify's replaces_id), so the call goes through
``gdbus``, which types the arguments from the service's own description. The click comes
back as the service's ActionInvoked signal, received through QtDBus.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from collections.abc import Callable

from PySide6.QtCore import SLOT, QObject, QProcess, QTimer, Slot

from zettelapp import DESKTOP_ID

SERVICE = "org.freedesktop.Notifications"
PATH = "/org/freedesktop/Notifications"
DESKTOP_ENTRY = DESKTOP_ID  # lets the desktop show our icon and name
TIMEOUT_MS = 15000


def use_activation_token(token: object) -> bool:
    """Hand a Wayland activation token to Qt, which uses it once on the next activateWindow():
    GNOME and KWin only bring a window forward that presents one. It comes from the launch
    that asked for the window, or from the notification that was clicked."""
    if not (
        sys.platform.startswith("linux")
        and isinstance(token, str)
        and 0 < len(token) <= 512
        and token.isprintable()
    ):
        return False
    os.environ["XDG_ACTIVATION_TOKEN"] = token
    return True


def _text(value: str) -> str:
    """*value* as a GVariant text-format string (JSON's escapes are a subset of GVariant's)."""
    return json.dumps(value, ensure_ascii=False)


class DesktopNotifier(QObject):
    """Show notifications whose click calls back with a key (a note id)."""

    def __init__(self, on_click: Callable[[str], None], icon: str = "", parent=None):
        super().__init__(parent)
        self.on_click = on_click
        self.icon = icon
        self.gdbus = shutil.which("gdbus")
        self._keys: dict[int, str] = {}  # notification id -> key
        self._tokens: dict[int, str] = {}  # notification id -> activation token of its click
        self._listening = False

    def available(self) -> bool:
        return self.gdbus is not None

    def notify(
        self, title: str, body: str, key: str, action: str, on_error: Callable[[], None]
    ) -> bool:
        """Ask the desktop to show a notification; False if it can't be asked at all.
        *on_error* runs later if the desktop has no notification service."""
        if self.gdbus is None:
            return False
        self._listen()
        process = QProcess(self)
        process.setProgram(self.gdbus)
        process.setArguments(
            [
                "call",
                "--session",
                "--dest",
                SERVICE,
                "--object-path",
                PATH,
                "--method",
                f"{SERVICE}.Notify",
                _text("ZettelApp"),
                "0",
                _text(self.icon),
                _text(title),
                _text(body),
                f"[{_text('default')}, {_text(action)}]",
                f"{{{_text('desktop-entry')}: <{_text(DESKTOP_ENTRY)}>}}",
                str(TIMEOUT_MS),
            ]
        )
        timer = QTimer(process, singleShot=True, interval=10000, timeout=process.kill)

        def finished(code: int, _status) -> None:
            timer.stop()
            output = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
            match = re.search(r"uint32 (\d+)", output)
            if code == 0 and match:
                self._keys[int(match.group(1))] = key
            else:
                on_error()
            process.deleteLater()

        process.finished.connect(finished)
        process.errorOccurred.connect(
            lambda error: (
                (on_error(), process.deleteLater())
                if error == QProcess.ProcessError.FailedToStart
                else None
            )
        )
        timer.start()
        process.start()
        return True

    def _listen(self) -> None:
        if self._listening:
            return
        from PySide6.QtDBus import QDBusConnection

        bus = QDBusConnection.sessionBus()
        # The desktop sends the click's activation token just before ActionInvoked (GNOME,
        # Plasma); without it the window can't come to the front.
        bus.connect(SERVICE, PATH, SERVICE, "ActivationToken", self, SLOT("_token(uint,QString)"))
        bus.connect(SERVICE, PATH, SERVICE, "ActionInvoked", self, SLOT("_invoked(uint,QString)"))
        bus.connect(SERVICE, PATH, SERVICE, "NotificationClosed", self, SLOT("_closed(uint,uint)"))
        self._listening = True

    @Slot("uint", "QString")
    def _token(self, notification_id: int, token: str) -> None:
        if notification_id in self._keys:
            self._tokens[notification_id] = token

    @Slot("uint", "QString")
    def _invoked(self, notification_id: int, action: str) -> None:
        key = self._keys.pop(notification_id, None)
        token = self._tokens.pop(notification_id, None)
        if key is not None and action == "default":
            use_activation_token(token)
            self.on_click(key)

    @Slot("uint", "uint")
    def _closed(self, notification_id: int, _reason: int) -> None:
        self._keys.pop(notification_id, None)
        self._tokens.pop(notification_id, None)
