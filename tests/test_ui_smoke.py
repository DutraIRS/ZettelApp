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
