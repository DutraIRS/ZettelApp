"""Alarms on Windows: a toast whose click opens the note through its zettelapp:// link."""

import base64
import sys

import pytest

from zettelapp import winintegration

TEXT = winintegration.ToastText(open="Open note", dismiss="Dismiss", caption="ZettelApp · Alarm")


def test_the_toast_opens_the_note_link_and_escapes_text(tmp_path):
    icon = tmp_path / "icon-256.png"
    xml = winintegration.toast_xml('Tom & "Jerry" <1>', "a < b", "zettelapp://note/1", TEXT, icon)
    assert 'activationType="protocol"' in xml and 'launch="zettelapp://note/1"' in xml
    assert 'scenario="reminder"' in xml  # stays on screen until clicked or dismissed
    assert 'Tom &amp; "Jerry" &lt;1&gt;' in xml and "a &lt; b" in xml
    assert 'content="Open note" activationType="protocol" arguments="zettelapp://note/1"' in xml
    assert 'content="Dismiss" activationType="system" arguments="dismiss"' in xml
    assert 'placement="attribution">ZettelApp · Alarm<' in xml
    assert f'placement="appLogoOverride" hint-crop="none" src="{icon.as_uri()}"' in xml
    assert "appLogoOverride" not in winintegration.toast_xml("t", "b", "u", TEXT)


def test_no_toast_without_an_app_id_or_registered_links(monkeypatch):
    monkeypatch.setattr(winintegration, "IS_WINDOWS", True)
    started = []
    monkeypatch.setattr(winintegration.subprocess, "Popen", lambda *a, **k: started.append(a))
    monkeypatch.setattr(winintegration, "_toast_app_id", lambda: None)
    monkeypatch.setattr(winintegration, "_links_open_the_app", lambda: True)
    assert not winintegration.show_toast("t", "b", "20260101000000", TEXT)
    monkeypatch.setattr(winintegration, "_toast_app_id", lambda: "ZettelApp.Desktop")
    monkeypatch.setattr(winintegration, "_links_open_the_app", lambda: False)
    assert not winintegration.show_toast("t", "b", "20260101000000", TEXT)
    assert started == []  # the caller shows the tray balloon instead


def test_the_toast_is_sent_by_windows_powershell(monkeypatch):
    monkeypatch.setattr(winintegration, "IS_WINDOWS", True)
    monkeypatch.setattr(winintegration, "_toast_app_id", lambda: "ZettelApp.Desktop")
    monkeypatch.setattr(winintegration, "_links_open_the_app", lambda: True)
    monkeypatch.setenv("SystemRoot", r"C:\Windows")
    started = []
    monkeypatch.setattr(winintegration.subprocess, "Popen", lambda args, **k: started.append(args))
    assert winintegration.show_toast("It's time", "Body", "20260101000000", TEXT)
    (args,) = started
    # Path joins with "/" off Windows (this test also runs on Linux): ignore the separator style
    assert (
        args[0]
        .lower()
        .replace("/", "\\")
        .endswith(r"system32\windowspowershell\v1.0\powershell.exe")
    )
    script = base64.b64decode(args[-1]).decode("utf-16-le")
    assert script == winintegration.toast_script(
        winintegration.toast_xml("It's time", "Body", "zettelapp://note/20260101000000", TEXT),
        "ZettelApp.Desktop",
    )


# PowerShell ends a single-quoted string at any of these, not only the ASCII apostrophe
QUOTES = "'‘’‚‛"


def _decoded_strings(script: str) -> list[str]:
    import re

    return [
        base64.b64decode(data).decode("utf-8")
        for data in re.findall(r"FromBase64String\('([A-Za-z0-9+/=]*)'\)", script)
    ]


def test_note_text_never_reaches_the_toast_script_as_code():
    title = "Meeting’+(Start-Process notepad)+’ " + QUOTES
    xml = winintegration.toast_xml(title, "Don’t " + QUOTES, "zettelapp://note/1", TEXT)
    script = winintegration.toast_script(xml, "App‘Id")
    assert not any(q in script for q in QUOTES[1:])  # no typographic quote at all
    assert "Start-Process" not in script and "Meeting" not in script
    # the only single quotes are the script's own, around fixed words and base64 data
    assert _decoded_strings(script) == [xml, "App‘Id"]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows PowerShell")
def test_powershell_reads_the_data_back_unchanged(tmp_path):
    import subprocess

    marker = tmp_path / "ran"
    value = f"x’+(New-Item '{marker}')+’ " + QUOTES + " Don’t"
    script = winintegration.toast_script(value, "id")
    # run only the decoding: print what LoadXml would have been given
    decode = script.split("$xml.LoadXml(", 1)[1].split(");$toast", 1)[0]
    out = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-EncodedCommand",
            base64.b64encode(
                f"[Console]::OutputEncoding = [Text.Encoding]::UTF8; {decode}".encode("utf-16-le")
            ).decode("ascii"),
        ],
        capture_output=True,
        timeout=60,
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.decode("utf-8").strip() == value
    assert not marker.exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows API")
def test_an_ordinary_process_has_no_package_family():
    assert winintegration._package_family_name() is None


def test_the_alarm_uses_the_toast_before_the_balloon(monkeypatch, tmp_path):
    monkeypatch.setenv("ZETTELAPP_SETTINGS_FILE", str(tmp_path / "settings.ini"))
    from PySide6.QtWidgets import QApplication

    from zettelapp.ui.main_window import MainWindow

    QApplication.instance() or QApplication(["test"])
    shown = []
    monkeypatch.setattr(winintegration, "show_toast", lambda *a: shown.append(a) or True)
    from zettelapp import i18n

    monkeypatch.setattr(i18n, "_language", "en")
    w = MainWindow()
    try:
        w._tray_message("20260101000000", "Title", "Body")
        ((title, body, note_id, text, icon),) = shown
        assert (title, body, note_id) == ("Title", "Body", "20260101000000")
        assert text == TEXT and icon is not None and icon.name == "icon-256.png"
        assert w._tray is None  # no balloon
    finally:
        w.close()
        w.deleteLater()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows registry")
def test_registering_links_also_lets_the_portable_copy_show_toasts(monkeypatch):
    import winreg

    monkeypatch.setattr(winintegration, "_PROTOCOL_KEY", r"Software\Classes\zettelapp-test-proto")
    monkeypatch.setattr(winintegration, "_APP_ID_KEY", r"Software\Classes\AppUserModelId\ZA.Test")
    monkeypatch.setattr(winintegration, "is_packaged", lambda: False)
    monkeypatch.setenv("APPDATA", "C:\nowhere")  # no Start menu shortcut
    monkeypatch.setenv("PROGRAMDATA", "C:\nowhere")
    assert winintegration._toast_app_id() is None
    winintegration.register_url_protocol()
    try:
        assert winintegration._toast_app_id() == "ZettelApp.Desktop"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, winintegration._APP_ID_KEY) as key:
            assert winreg.QueryValueEx(key, "DisplayName")[0] == "ZettelApp"
            assert winreg.QueryValueEx(key, "IconUri")[0].endswith("icon-256.png")
    finally:
        winintegration.unregister_url_protocol()
    assert winintegration._toast_app_id() is None
