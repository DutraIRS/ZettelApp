"""Drives the real main window offscreen: pages, editing, suggestions, graph and dialogs."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6.QtWidgets")


@pytest.fixture
def window(tmp_path, monkeypatch):
    monkeypatch.setenv("ZETTELAPP_SETTINGS_FILE", str(tmp_path / "settings.ini"))
    from PySide6.QtWidgets import QApplication

    from zettelapp.ui import theme
    from zettelapp.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication(["test"])
    theme.apply_theme(app, "light")
    w = MainWindow()
    w.show()
    assert w.open_vault(tmp_path / "vault")
    yield w
    from PySide6.QtCore import QThreadPool

    QThreadPool.globalInstance().waitForDone(20000)
    w.suggestions.pool.waitForDone(20000)
    w.close()


def pump(ms=300):
    from PySide6.QtCore import QEventLoop, QThreadPool, QTimer

    QThreadPool.globalInstance().waitForDone(20000)
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def test_full_workflow(window):
    from tools.demo_vault import build_demo

    ids = build_demo(window.vault)
    window.list.refresh()
    window.open_note(ids["Atomic notes"])
    window.suggestions.pool.waitForDone(20000)
    pump()
    assert window.editor.note.title == "Atomic notes"
    assert window.side.suggestions.count() > 0  # Naive Bayes suggestions arrived

    window.new_note()
    window.editor.title.setText("Retrieval and spacing")
    window.editor.body.setPlainText(
        "Testing yourself at spaced intervals. supports:: [[Spaced repetition]]"
    )
    window.editor._edited()
    window.editor.flush()
    note_id = window.current_note_id()
    assert {l.type for l in window.vault.links_from(note_id)} == {"supports"}

    for page in range(5):
        window.show_page(page)
        pump(200)
    window.show_page(1)
    pump(300)
    assert window.graph.view2d.data.ids  # the layout finished and was drawn
    window.graph.color_by.setCurrentIndex(2)  # hierarchical clusters
    window.graph.dim_group.button(1).click()  # 3D
    pump(300)
    assert len(window.graph.view3d.points) == len(window.graph.view3d.data.ids) > 0

    window.trash_note(note_id)
    assert window.vault.get_note(note_id).deleted
    window.restore_note(note_id)


def test_dialogs_construct(window):
    from zettelapp.ui.dialogs import AboutDialog, ExportDialog, LinkPickerDialog, ShortcutsDialog
    from zettelapp.ui.settings_dialog import OptionsDialog

    window.vault.create_note("One", "text")
    AboutDialog(window).close()
    ShortcutsDialog(window).close()
    LinkPickerDialog(window.vault, set(), window).close()
    ExportDialog(window.vault, None, window.resolve_scope, window).close()
    options = OptionsDialog(window)
    assert options.pages.count() == options.nav.count() == 9
    options.close()


def test_mindmap_editor_blocks_children_beyond_the_storage_limit(window):
    from zettelapp.core.models import MAX_MINDMAP_DEPTH, mindmap_nodes, new_mindmap_node
    from zettelapp.ui.mindmap import MindMapView

    root = new_mindmap_node("Root")
    current = root
    for depth in range(MAX_MINDMAP_DEPTH):
        child = new_mindmap_node(str(depth))
        current["children"].append(child)
        current = child
    view = MindMapView(window)
    view.set_mindmap(root)
    view.select(current["id"])
    before = list(mindmap_nodes(view.root))

    view.add_child()

    assert list(mindmap_nodes(view.root)) == before


@pytest.mark.parametrize("servers", [None, [], "invalid"])
def test_mcp_config_rejects_invalid_server_collections(servers):
    from zettelapp.ui.settings_dialog import _merge_mcp_entry

    config = {"mcpServers": servers}
    with pytest.raises(ValueError, match="mcpServers"):
        _merge_mcp_entry(config, {"command": "zettelapp-mcp"})

    assert config == {"mcpServers": servers}


def test_zotero_pdf_lookup_is_dispatched_off_the_gui_thread(window, monkeypatch):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QListWidgetItem

    from zettelapp.core.zotero import ZoteroItem
    from zettelapp.ui import zotero_dialog

    tasks = []
    monkeypatch.setattr(
        zotero_dialog,
        "run_task",
        lambda fn, *args, **kwargs: tasks.append((fn, args, kwargs)),
    )
    dialog = zotero_dialog.ZoteroDialog(window)
    item = QListWidgetItem("Paper")
    item.setData(Qt.ItemDataRole.UserRole, ZoteroItem("ABCD1234", "Paper"))
    dialog.results.addItem(item)
    dialog.results.setCurrentItem(item)
    accepted = []
    monkeypatch.setattr(dialog, "accept", lambda: accepted.append(True))

    dialog._finish("note")

    assert len(tasks) == 2
    assert tasks[-1][0] == dialog.client.pdf_attachment
    assert accepted == []
    tasks[-1][2]["on_done"]("PDF12345")
    assert dialog.pdf_key == "PDF12345"
    assert accepted == [True]


def test_review_start_button_click_starts_review(window):
    from zettelapp.ui.widgets import accent_button

    window.vault.create_note("N", "Q: q\nA: a")
    # find the Start review button wired to start_due on the Review page
    button = next(
        w for w in window.review.findChildren(type(accent_button(""))) if w.text() == "Start review"
    )
    button.click()  # Qt passes checked: bool; start_due must not receive it
    assert window.review.stack.currentIndex() == 1  # quiz started, no TypeError raised


def _point_in(body, text):
    """Viewport position of a character inside *text* in the editor."""
    from PySide6.QtGui import QTextCursor

    cursor = QTextCursor(body.document())
    cursor.setPosition(body.toPlainText().index(text) + 2)
    return body.cursorRect(cursor).center()


def test_ctrl_click_follows_links_and_tags(window):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    target = window.vault.create_note("Target note", "Hello")
    source = window.vault.create_note("Source", "See [[Target note]] and #idea here.")
    window.list.refresh()
    window.open_note(source.id)
    body = window.editor.body
    pump()
    assert body.link_at(_point_in(body, "Target note")) == ("note", "Target note")
    assert body.link_at(_point_in(body, "#idea")) == ("tag", "idea")
    assert body.link_at(_point_in(body, "See")) is None
    assert "Ctrl+click to open" in body._link_tip("note", "Target note")
    assert "create it" in body._link_tip("note", "Missing note")

    QTest.mouseClick(body.viewport(), Qt.MouseButton.LeftButton, pos=_point_in(body, "Target"))
    assert window.current_note_id() == source.id  # a plain click only places the caret
    QTest.mouseClick(
        body.viewport(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ControlModifier,
        _point_in(body, "Target"),
    )
    assert window.current_note_id() == target.id

    window.open_note(source.id)
    QTest.mouseClick(
        body.viewport(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ControlModifier,
        _point_in(body, "#idea"),
    )
    assert window.list.tag_filter.currentData() == "idea"


def test_hashtags_typed_in_the_text_show_as_tag_chips(window):
    from PySide6.QtWidgets import QToolButton

    note = window.vault.create_note("Tagged", "Plain text", tags=["manual"])
    window.list.refresh()
    window.open_note(note.id)
    window.editor.body.setPlainText("Now with #idea")
    window.editor._refresh_inline_tags()
    pump(50)
    chips = {
        c.text(): bool(c.property("inline"))
        for c in window.editor.tags.findChildren(QToolButton, "Chip")
    }
    assert chips == {"#manual  ✕": False, "#idea": True}
    window.editor.flush()
    assert window.vault.get_note(note.id).tags == ["idea", "manual"]
    assert window.vault.manual_tags(note.id) == ["manual"]

