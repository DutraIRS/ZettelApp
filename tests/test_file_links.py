"""Links to local files: shown in File Explorer, never opened, never on a network path."""

import os

import pytest

from zettelapp.core.render import NoteRenderer
from zettelapp.core.security import file_url, local_file_path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("file:///C:/Users/me/My%20Files/report.pdf", r"C:\Users\me\My Files\report.pdf"),
        ("file://C:/Data/a.txt", r"C:\Data\a.txt"),
        ("file://localhost/D:/x.txt", r"D:\x.txt"),
        (r"C:\Data\..\Docs\b.docx", r"C:\Docs\b.docx"),
        ("c:/data/c.csv", r"c:\data\c.csv"),
    ],
)
def test_local_drive_paths_are_accepted(target, expected):
    assert local_file_path(target) == expected


@pytest.mark.parametrize(
    "target",
    [
        r"\\server\share\secret.docx",  # network (UNC) paths could leak credentials
        "file://server/share/secret.docx",
        "file://///server/share/secret.docx",
        r"\\?\C:\device\path",
        "//server/share",
        "relative\\path.txt",
        "https://example.com/a.pdf",
        "file:///C:/a.txt?x=1",
        "file:///C:/bad%00name.txt",
        "",
        None,
    ],
)
def test_network_device_and_other_paths_are_refused(target):
    assert local_file_path(target) is None


def test_file_url_round_trips():
    path = r"C:\Users\me\My Files\notes #1.txt"
    url = file_url(path)
    assert url.startswith("file:///C:/") and " " not in url and "#" not in url
    assert local_file_path(url) == path


def test_file_links_are_clickable_only_in_the_app():
    text = (
        "[report](file:///C:/Docs/report.pdf), [spaced](<C:\\My Docs\\plan.txt>) "
        "and [share](file://server/share/x.txt)"
    )
    app = NoteRenderer(lambda t: None, allow_file_links=True).render(text)
    assert 'href="file:///C:/Docs/report.pdf" class="file"' in app
    assert 'href="file:///C:/My%20Docs/plan.txt" class="file"' in app
    assert app.count('class="broken"') == 1 and "file://server" not in app  # the network path
    exported = NoteRenderer(lambda t: None).render(text)  # websites, Anki cards
    assert "file:" not in exported and exported.count('class="broken"') == 3


def _window(tmp_path, monkeypatch):
    monkeypatch.setenv("ZETTELAPP_SETTINGS_FILE", str(tmp_path / "settings.ini"))
    from PySide6.QtWidgets import QApplication

    from zettelapp.ui import theme
    from zettelapp.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication(["test"])
    theme.apply_theme(app, "light")
    window = MainWindow()
    window.show()
    assert window.open_vault(tmp_path / "vault")
    return window


def test_clicking_a_file_link_shows_it_in_explorer(tmp_path, monkeypatch):
    pytest.importorskip("PySide6.QtWidgets")
    from PySide6.QtCore import QMimeData, Qt, QUrl
    from PySide6.QtGui import QTextCursor
    from PySide6.QtTest import QTest

    from zettelapp import winintegration

    shown = []
    monkeypatch.setattr(winintegration, "reveal_in_explorer", lambda p: shown.append(str(p)))
    document = tmp_path / "My Files" / "report.pdf"
    document.parent.mkdir()
    document.write_bytes(b"%PDF-1.7")
    window = _window(tmp_path, monkeypatch)
    try:
        note = window.vault.create_note("Files", f"See [report]({file_url(str(document))}) now.")
        window.list.refresh()
        window.open_note(note.id)
        body = window.editor.body

        cursor = QTextCursor(body.document())
        cursor.setPosition(body.toPlainText().index("report") + 2)
        point = body.cursorRect(cursor).center()
        assert "File Explorer" in body._link_tip(*body.link_at(point))
        QTest.mouseClick(
            body.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, point
        )
        assert shown == [str(document)]

        window.editor.preview._on_anchor(QUrl(file_url(str(document))))  # a click in the preview
        assert shown == [str(document)] * 2
        window.reveal_file(r"\\server\share\report.pdf")  # refused before any lookup
        assert len(shown) == 2

        other = tmp_path / "data.csv"
        other.write_text("a,b", encoding="utf-8")
        body.moveCursor(QTextCursor.MoveOperation.End)
        drop = QMimeData()
        drop.setUrls([QUrl.fromLocalFile(str(other))])
        body.insertFromMimeData(drop)  # dropping a non-image file links it where it is
        assert f"[data.csv]({file_url(str(other))})" in body.toPlainText()
    finally:
        window.close()
