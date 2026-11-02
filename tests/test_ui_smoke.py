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
    w.deleteLater()


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
    from zettelapp.ui.dialogs import (
        AboutDialog,
        ExportDialog,
        LinkPickerDialog,
        ShortcutsDialog,
    )
    from zettelapp.ui.settings_dialog import PAGES, OptionsDialog

    window.vault.create_note("One", "text")
    AboutDialog(window).close()
    ShortcutsDialog(window).close()
    LinkPickerDialog(window.vault, set(), window).close()
    ExportDialog(window.vault, None, window.resolve_scope, window).close()
    options = OptionsDialog(window)
    assert options.pages.count() == options.nav.count() == len(PAGES)
    options.close()


def test_the_tag_options_menu_opens_the_ontology_and_toggles_related_tags(window, monkeypatch):
    from zettelapp.ui import main_window
    from zettelapp.ui.dialogs import TagOntologyDialog

    opened = []
    monkeypatch.setattr(main_window, "run_dialog", opened.append)
    panel = window.list
    related, manage = panel.tag_options.menu().actions()
    manage.trigger()
    assert isinstance(opened[0], TagOntologyDialog)
    opened[0].deleteLater()

    window.vault.create_note("Near", tags=["near"])
    window.vault.add_tag_relationship("start", "near", "related")
    panel.refresh_tags()
    assert panel.tag_filter.findData("start") < 0  # finds nothing yet
    related.setChecked(True)
    assert panel.tag_filter.findData("start") > 0
    panel.tag_filter.setCurrentIndex(panel.tag_filter.findData("start"))
    assert [row["title"] for row in panel.model.rows] == ["Near"]


def test_a_semantic_weight_of_zero_does_not_run_the_model(window):
    from zettelapp import settings

    settings.put(settings.SEARCH_SEMANTIC_ENABLED, True)
    settings.put(settings.SEARCH_SEMANTIC_WEIGHT, 0.0)
    asked = []
    window.list.semanticRequested.connect(asked.append)
    window.list.search.setText("words")
    window.list.refresh()
    assert asked == []


def test_tag_ontology_dialog_edits_relationships(window):
    from zettelapp.ui.dialogs import TagOntologyDialog

    window.vault.create_note("Child", tags=["child"])
    dialog = TagOntologyDialog(window.vault, window)
    dialog.source.setEditText("parent")
    dialog.target.setEditText("child")
    dialog._add()
    assert window.vault.tag_graph().descendants("parent") == {"child"}
    assert dialog.relationships.count() == 1
    dialog.relationships.setCurrentRow(0)
    dialog._remove()
    assert not window.vault.tag_relationships()
    dialog.close()


def test_note_list_search_respects_tag_filters_and_the_trash(window):
    vault, panel = window.vault, window.list
    vault.create_note("Math", "not tagged")
    vault.create_note("Algebra", "groups", tags=["math"])
    gone = vault.create_note("Math in the trash", "gone")
    vault.trash_note(gone.id)
    panel.refresh_tags()

    def titles(text):
        panel.search.setText(text)
        panel.refresh()
        return {row["title"] for row in panel.model.rows}

    assert titles("tag:math") == {"Algebra"}
    assert titles("math") == {"Math", "Algebra"}
    assert titles("zzz") == set()
    panel.trash_button.setChecked(True)
    panel.toggle_trash()
    assert titles("math") == {"Math in the trash"}


def test_search_results_show_the_part_of_the_note_that_matches(window):
    window.vault.create_note("Long", "lorem ipsum " * 40 + "needle at last " + "dolor " * 40)
    panel = window.list
    panel.search.setText("needle")
    panel.refresh()
    assert "needle" in panel.model.rows[0]["snippet"]
    panel.search.setText("")
    panel.refresh()
    assert panel.model.rows[0]["snippet"].startswith("lorem")


def test_adaptive_feedback_is_offered_only_when_on_and_changes_the_ranking(window):
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from zettelapp import settings

    vault, panel = window.vault, window.list
    vault.create_note("Note about chess", "chess")
    panel.search.setText("chess")
    panel.refresh()
    position = panel.view.visualRect(panel.model.index(0)).center()

    def menu_entries() -> list[str]:
        entries = []

        def read_and_close():
            menu = QApplication.activePopupWidget()
            entries.extend(action.text() for action in menu.actions())
            menu.close()

        QTimer.singleShot(50, read_and_close)
        panel._menu(position)
        return entries

    assert "Relevant result" not in menu_entries()
    settings.put(settings.SEARCH_ADAPTIVE_ENABLED, True)
    assert {"Relevant result", "Not a relevant result"} <= set(menu_entries())

    note_id = panel.model.rows[0]["id"]
    panel._record_feedback(note_id, True)
    saved = settings.get(settings.SEARCH_ADAPTIVE_STATE)
    assert note_id not in saved and "chess" not in saved
    assert '"lexical": 1.0' in saved


def test_semantic_scores_arrive_later_and_outdated_ones_are_ignored(window):
    from zettelapp import settings

    vault, panel = window.vault, window.list
    settings.put(settings.SEARCH_SEMANTIC_ENABLED, True)
    grocery = vault.create_note("Grocery list", "bread and cheese")
    vault.create_note("Unrelated", "nothing to see")
    asked = []
    panel.semanticRequested.connect(asked.append)

    panel.search.setText("shopping")
    panel.refresh()
    panel.refresh()
    assert asked == ["shopping"]  # the same words aren't asked for again
    assert panel.model.rows == []

    panel.set_semantic_scores("older words", {grocery.id: 0.9})
    assert panel.model.rows == []
    panel.set_semantic_scores("shopping", {grocery.id: 0.9})
    assert [row["title"] for row in panel.model.rows] == ["Grocery list"]

    settings.put(settings.SEARCH_SEMANTIC_ENABLED, False)
    panel.refresh()
    assert panel.model.rows == []


def test_a_new_vault_never_uses_the_previous_ones_semantic_scores(window, tmp_path):
    from zettelapp import settings

    settings.put(settings.SEARCH_SEMANTIC_ENABLED, True)
    panel = window.list
    note = window.vault.create_note("Note", "text")
    panel.search.setText("shopping")
    panel.refresh()
    panel.set_semantic_scores("shopping", {note.id: 0.9})
    assert window.open_vault(tmp_path / "second")
    assert panel._semantic_scores == {} and panel.model.rows == []


def test_notes_changing_schedule_indexing_only_when_semantic_search_is_on(window, monkeypatch):
    from zettelapp import settings
    from zettelapp.ui import main_window

    synced = []
    monkeypatch.setattr(window.semantic, "sync", synced.append)
    window.vault.create_note("Note", "text")
    assert window.semantic_timer.isActive()
    window._sync_semantic_index()
    assert synced == []  # off by default: nothing runs, nothing loads

    monkeypatch.setattr(main_window, "model_installed", lambda _root: True)
    settings.put(settings.SEARCH_SEMANTIC_ENABLED, True)
    window._sync_semantic_index()
    assert synced == [window.vault.folder]
    settings.put(settings.SEARCH_SEMANTIC_INDEXING, False)
    window._sync_semantic_index()
    assert len(synced) == 1


def test_semantic_search_is_not_used_without_the_model(window, monkeypatch):
    from zettelapp import settings

    settings.put(settings.SEARCH_SEMANTIC_ENABLED, True)
    asked = []
    monkeypatch.setattr(window.semantic, "search", lambda *args: asked.append(args))
    window.list.search.setText("words")
    window.list.refresh()
    assert asked == []


def test_options_offer_the_model_download_only_with_consent(window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from zettelapp.ui.settings_dialog import OptionsDialog

    started = []
    monkeypatch.setattr(window.semantic, "download", lambda: started.append(True))
    options = OptionsDialog(window, "Search")
    assert options.semantic_download.isVisibleTo(options)
    assert not options.semantic_on.isVisibleTo(options)
    assert not options.semantic_remove.isVisibleTo(options)

    monkeypatch.setattr(QMessageBox, "question", lambda *_a, **_k: QMessageBox.StandardButton.No)
    options.semantic_download.click()
    assert started == []
    monkeypatch.setattr(QMessageBox, "question", lambda *_a, **_k: QMessageBox.StandardButton.Yes)
    options.semantic_download.click()
    assert started == [True]
    options.close()


def test_options_with_the_model_installed_can_remove_it(window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from zettelapp import settings
    from zettelapp.ui import settings_dialog

    monkeypatch.setattr(settings_dialog, "model_installed", lambda _root: True)
    removed = []
    monkeypatch.setattr(window.semantic, "remove_data", lambda: removed.append(True))
    monkeypatch.setattr(QMessageBox, "question", lambda *_a, **_k: QMessageBox.StandardButton.Yes)
    settings.put(settings.SEARCH_SEMANTIC_ENABLED, True)
    options = settings_dialog.OptionsDialog(window, "Search")
    assert options.semantic_on.isVisibleTo(options) and options.semantic_on.isChecked()
    assert not options.semantic_download.isVisibleTo(options)
    monkeypatch.setattr(settings_dialog, "model_installed", lambda _root: False)
    options.semantic_remove.click()
    assert removed == [True]
    assert not settings.get(settings.SEARCH_SEMANTIC_ENABLED)
    assert not options.semantic_on.isChecked() and not options.semantic_on.isVisibleTo(options)
    options.close()


def test_options_save_the_search_settings(window):
    from zettelapp import settings
    from zettelapp.ui.settings_dialog import OptionsDialog

    options = OptionsDialog(window, "Search")
    options.w_fuzzy.setValue(0.5)
    options.semantic_threads.setValue(3)
    options.adaptive_on.setChecked(True)
    assert options.apply()
    assert settings.search_weights()["fuzzy"] == 0.5
    assert settings.get(settings.SEARCH_SEMANTIC_THREADS) == 3
    assert settings.get(settings.SEARCH_ADAPTIVE_ENABLED)
    assert window.semantic.threads == 3
    options.close()


def test_the_search_page_rebuilds_the_full_text_index(window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from zettelapp.ui.settings_dialog import OptionsDialog

    monkeypatch.setattr(QMessageBox, "information", lambda *_a, **_k: None)
    note = window.vault.create_note("Findable", "needle")
    with window.vault.transaction():
        window.vault.conn.execute("DELETE FROM notes_fts")
    options = OptionsDialog(window, "Search")
    options.rebuild_fts.click()
    assert window.vault.search("needle") == [note.id]
    options.close()


def test_finished_dialogs_are_freed(window):
    from PySide6.QtCore import QCoreApplication, QEvent, QTimer
    from PySide6.QtWidgets import QDialog

    from zettelapp.ui.dialogs import ShortcutsDialog
    from zettelapp.ui.widgets import run_dialog

    before = len(window.findChildren(QDialog))
    dialog = ShortcutsDialog(window)
    QTimer.singleShot(0, dialog.accept)
    assert run_dialog(dialog) == QDialog.DialogCode.Accepted
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    pump(20)
    assert len(window.findChildren(QDialog)) == before


def test_graph_starts_over_when_the_data_changes_during_a_layout(window, monkeypatch):
    from zettelapp.ui import graph_page

    window.vault.create_note("One", "text")
    pending = []
    monkeypatch.setattr(
        graph_page, "run_task", lambda *_args, **kwargs: pending.append(kwargs["on_done"])
    )
    window.show_page(1)
    assert len(pending) == 1 and window.graph.info.text() == "Computing layout…"
    window.graph.invalidate()
    assert len(pending) == 2  # asked again, so the page doesn't stay on "Computing layout…"


def test_suggestions_are_asked_for_again_when_another_program_changed_the_vault(window):
    window.vault.create_note("One", "text")
    window.suggest_timer.stop()
    window._data_version = -1
    window._check_external_changes()
    assert window.suggest_timer.isActive()


def test_options_page_edits_link_types_and_their_styles(window, monkeypatch):
    from zettelapp.ui.settings_dialog import OptionsDialog

    vault = window.vault
    dialog = OptionsDialog(window, "Link types")
    ids = [lt.id for lt in dialog._types]
    dialog.types_list.setCurrentRow(ids.index("supports"))
    assert not dialog.remove_type_button.isEnabled()  # built-in: restyle, don't remove
    dialog.type_name.setText("Backs")
    dialog.type_name.textEdited.emit("Backs")
    dialog.type_line.setCurrentIndex(dialog.type_line.findData("long_dash"))
    dialog.type_arrow.setCurrentIndex(dialog.type_arrow.findData("diamond"))
    dialog.grab()  # paints the preview and the combo pictures

    dialog._add_type()
    assert dialog.remove_type_button.isEnabled()
    dialog.type_name.setText("Inspired by")
    dialog.type_name.textEdited.emit("Inspired by")
    dialog.type_directed.setChecked(False)
    assert not dialog.type_arrow.isEnabled() and not dialog.type_reverse.isEnabled()
    dialog.type_line.setCurrentIndex(dialog.type_line.findData("dotted"))
    assert dialog.apply()

    types = vault.link_type_map()
    backs, inspired = types["supports"], types["inspired_by"]
    assert (backs.label, backs.line_style, backs.arrow, backs.builtin) == (
        "Backs",
        "long_dash",
        "diamond",
        True,
    )
    assert (inspired.line_style, inspired.directed, inspired.tip) == ("dotted", False, None)
    assert dialog._types[-1].id == "inspired_by"  # applying twice doesn't add it again
    assert dialog.apply() and len(vault.link_types()) == len(ids) + 1

    dialog._remove_type()  # the new type is still selected
    warnings = []
    monkeypatch.setattr(
        "zettelapp.ui.settings_dialog.QMessageBox.warning", lambda *a: warnings.append(a[2])
    )
    dialog._add_type()
    dialog.type_name.setText("")
    dialog.type_name.textEdited.emit("")
    assert not dialog.apply() and warnings  # a new type needs a name
    dialog._remove_type()
    assert dialog.apply()
    assert "inspired_by" not in vault.link_type_map()
    dialog.close()


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


def test_mindmap_from_links_stays_within_the_node_limit(window, monkeypatch):
    from zettelapp.core.models import mindmap_nodes

    monkeypatch.setattr("zettelapp.core.models.MAX_MINDMAP_NODES", 7)
    vault = window.vault
    hub = vault.create_note("Hub")
    neighbours = []
    for i in range(3):
        note = vault.create_note(f"Linked {i}")
        vault.add_link(hub.id, note.id, "related")
        neighbours.append(note.id)
        for j in range(4):
            vault.add_link(note.id, vault.create_note(f"Further {i}.{j}").id, "related")
    window.list.refresh()
    window.open_note(hub.id)

    window.editor.mindmap_from_links()
    window.editor.flush()  # saving refuses a map with more nodes than the limit

    nodes = list(mindmap_nodes(vault.get_note(hub.id).mindmap))
    assert len(nodes) == 7  # the root, one link type, 3 linked notes and 2 of their links
    assert sorted(node["note"] for node, depth in nodes if depth == 2) == sorted(neighbours)
    assert window.statusBar().currentMessage().startswith("Left out 10 links")


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


def test_a_new_vault_opens_on_the_start_here_hub(window):
    window._create_welcome_notes()
    note = window.editor.note
    assert note.title == "Welcome to ZettelApp"
    assert window.list.current_id() == note.id
    assert len(window.vault.links_from(note.id)) == 10  # the hub lists every starter note
    assert (
        "Welcome to ZettelApp" in window.editor.body.titles_model.stringList()
    )  # [[ completes titles


@pytest.mark.parametrize("dialog", ["new_vault_dialog", "open_vault_dialog"])
def test_dialog_created_vaults_start_with_the_tour(window, tmp_path, monkeypatch, dialog):
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    folder = tmp_path / dialog
    folder.mkdir()
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *_args: str(folder))
    monkeypatch.setattr(QMessageBox, "question", lambda *_args: QMessageBox.StandardButton.Yes)
    starts = []
    monkeypatch.setattr(window.quest, "start_up", lambda *a: starts.append(a))

    getattr(window, dialog)()

    assert window.vault.count_notes() == 11
    assert window.editor.note.title == "Welcome to ZettelApp"
    assert len(starts) == 1


def test_failed_default_vault_open_does_not_start_the_quest(window, tmp_path, monkeypatch):
    from zettelapp.ui import main_window

    monkeypatch.setattr(main_window, "default_vault_dir", lambda: tmp_path / "unopenable")
    monkeypatch.setattr(main_window.settings, "get", lambda *_args: "")
    monkeypatch.setattr(window, "open_vault", lambda _folder: False)
    starts = []
    monkeypatch.setattr(window.quest, "start_up", lambda *a: starts.append(a))

    window.open_default_vault()

    assert starts == []


def test_mcp_switch_starts_off_and_closing_the_app_turns_it_off(window, monkeypatch, tmp_path):
    from zettelapp import mcp_switch

    monkeypatch.setattr(mcp_switch, "EVENT_NAME", rf"Local\ZettelApp.UiTest.{os.getpid()}")
    monkeypatch.setattr(mcp_switch, "_pid_file", lambda: tmp_path / "mcp-switch-on.pid")
    assert not window.mcp_toggle.isChecked() and not mcp_switch.mcp_switched_on()
    assert window.mcp_label.text() == "MCP off"
    window.mcp_toggle.click()
    assert mcp_switch.mcp_switched_on() and window.mcp_label.text() == "MCP on"
    window.mcp_toggle.click()
    assert not mcp_switch.mcp_switched_on()
    window.mcp_toggle.click()
    window.close()  # closing ZettelApp cuts agents off
    assert not mcp_switch.mcp_switched_on() and not window.mcp_toggle.isChecked()


def test_update_notice_is_quiet_and_shown_once_per_version(window, monkeypatch):
    from PySide6.QtWidgets import QApplication

    from zettelapp import settings

    focus = QApplication.focusWidget()
    window._show_update_notice("999.0.0")
    notice = window.update_notice
    assert notice.isVisible() and QApplication.focusWidget() is focus  # never steals focus
    corner = notice.geometry()
    assert corner.right() < window.width() and corner.bottom() < window.statusBar().y()
    assert corner.left() > window.width() / 2  # lower right
    assert settings.get(settings.UPDATE_NOTIFIED) == "999.0.0"
    notice.close()
    window._show_update_notice("999.0.0")  # already announced: nothing new
    assert window.update_notice is notice

    window._show_update_notice("999.1.0")
    window.update_notice._silence()  # "Don't check for updates"
    assert settings.get(settings.UPDATE_CHECK) is False
    calls = []
    monkeypatch.setattr("zettelapp.ui.main_window.run_task", lambda *a, **k: calls.append(a))
    window.check_for_updates()
    assert calls == []  # silenced for good


def test_every_screen_paints_with_data(window):
    """Painting runs Python code (charts, graph labels, chips, switches). Grabbing each
    screen with real data makes any error in it fail here instead of in front of users."""
    from tools.demo_vault import build_demo
    from zettelapp.ui.settings_dialog import PAGES, OptionsDialog

    ids = build_demo(window.vault)
    window.list.refresh()
    window.open_note(ids["Spaced repetition"])
    window.editor.set_view_mode(1)
    for tab in range(3):  # note, mind map, flashcards
        window.editor.tabs.setCurrentIndex(tab)
        pump(50)
        window.grab()
    window.editor.tabs.setCurrentIndex(0)
    for page in range(5):  # notes, graph, insights, review, ask
        window.show_page(page)
        pump(300)
        window.grab()
    window.show_page(1)
    window.graph.view2d.select(ids["Spaced repetition"])  # labelled, fanned-out links
    window.grab()
    window.graph.dim_group.button(1).click()
    window.graph.view3d.focus_node(ids["Spaced repetition"])
    pump(200)
    window.grab()
    window.mcp_toggle.click()
    window._show_update_notice("999.0.0")
    window.grab()
    window.mcp_toggle.click()
    dialog = OptionsDialog(window)
    dialog.show()
    for row in range(len(PAGES)):
        dialog.nav.setCurrentRow(row)
        dialog.grab()
    dialog.close()
