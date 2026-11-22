"""Alarm notifications through the desktop's notification service (Linux)."""

# ruff: noqa: F811  (the `window` fixture is imported, then used as a test argument)

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6.QtWidgets")

from tests.test_ui_smoke import window  # noqa: E402, F401


def test_notifier_sends_a_typed_gdbus_call(monkeypatch):
    from zettelapp.ui.notifications import DesktopNotifier

    started = []
    monkeypatch.setattr(
        "zettelapp.ui.notifications.QProcess.start", lambda self: started.append(self.arguments())
    )
    monkeypatch.setattr(DesktopNotifier, "_listen", lambda self: None)
    notifier = DesktopNotifier(lambda key: None, "/icon.png")
    notifier.gdbus = "/usr/bin/gdbus"
    assert notifier.notify('Say "hi"', "line\nbreak", "20260101120000", "Open note", lambda: None)
    args = started[0]
    assert args[args.index("--method") + 1] == "org.freedesktop.Notifications.Notify"
    # GVariant text: strings quoted and escaped, the id a plain 0 typed by gdbus as uint32.
    assert args[-8:] == [
        '"ZettelApp"',
        "0",
        '"/icon.png"',
        '"Say \\"hi\\""',
        '"line\\nbreak"',
        '["default", "Open note"]',
        '{"desktop-entry": <"io.github.dutairs.zettelapp">}',
        "15000",
    ]


def test_notifier_without_gdbus_declines():
    from zettelapp.ui.notifications import DesktopNotifier

    notifier = DesktopNotifier(lambda key: None)
    notifier.gdbus = None
    assert not notifier.notify("t", "b", "k", "Open note", lambda: None)


def test_clicking_a_notification_calls_back_once():
    from zettelapp.ui.notifications import DesktopNotifier

    clicked = []
    notifier = DesktopNotifier(clicked.append)
    notifier._keys[5] = "20260101120000"
    notifier._invoked(9, "default")  # another app's notification
    notifier._invoked(5, "default")
    notifier._invoked(5, "default")
    assert clicked == ["20260101120000"]
    notifier._keys[6] = "x"
    notifier._closed(6, 1)
    notifier._invoked(6, "default")
    assert clicked == ["20260101120000"]


def test_alarm_uses_the_notification_service_on_linux(window, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    note = window.vault.create_note("Call Ana", "about the **project**")
    other = window.vault.create_note("Other")
    notifier = window._desktop_notifier()
    sent = []
    monkeypatch.setattr(notifier, "notify", lambda *args: sent.append(args[:3]) or True)
    window._notify_alarm(note)
    assert sent == [("Call Ana", "about the project", note.id)]
    window.open_note(other.id)
    notifier._keys[7] = note.id
    notifier._invoked(7, "default")
    assert window.current_note_id() == note.id


def test_alarm_falls_back_to_the_tray_without_gdbus(window, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    note = window.vault.create_note("Tray", "")
    window._desktop_notifier().gdbus = None
    shown = []
    monkeypatch.setattr(window, "_tray_message", lambda *args: shown.append(args))
    window._notify_alarm(note)
    assert shown and shown[0][0] == note.id


def test_ask_page_says_when_keys_are_memory_only(window, monkeypatch):
    from zettelapp.core import secrets

    monkeypatch.setattr(secrets, "secrets_available", lambda: False)
    window.ask.refresh()
    assert "No system keyring" in window.ask.privacy.text()
    assert "kept in the system keyring" not in window.ask.privacy.text()
    monkeypatch.setattr(secrets, "secrets_available", lambda: True)
    window.ask.refresh()
    assert "kept in the system keyring" in window.ask.privacy.text()
