"""Editor and window behaviour added in 1.1: drops, checklists, title image, alarms, toolbar."""

# ruff: noqa: F811  (the `window` fixture is imported, then used as a test argument)

import os
from datetime import UTC, datetime, timedelta

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6.QtWidgets")

from tests.conftest import tiny_png  # noqa: E402
from tests.test_ui_smoke import pump, window  # noqa: E402, F401


def _new_note(window, body=""):
    note = window.vault.create_note("Subject", body)
    window.open_note(note.id)
    return note


def test_split_view_is_the_default(window):
    assert window.editor.mode_group.checkedId() == 1


def test_reading_view_is_read_only_and_remembered(window):
    from zettelapp import settings
    from zettelapp.ui.editor import READING, SPLIT

    note = _new_note(window, "Some text.")
    editor = window.editor
    editor.set_view_mode(READING)
    assert editor.text_pane.isHidden() and not editor.preview.isHidden()
    assert editor.title.isReadOnly() and editor.url.isReadOnly()
    assert not any(b.isEnabled() for b in editor.fmt_buttons)
    assert editor.url.isHidden()  # an empty source link is left out
    assert settings.get(settings.EDITOR_VIEW_MODE) == READING
    blank = window.vault.create_note("", "")
    window.open_note(blank.id)  # a new note opens for writing, without forgetting the choice
    assert editor.mode_group.checkedId() == SPLIT and not editor.title.isReadOnly()
    assert settings.get(settings.EDITOR_VIEW_MODE) == READING
    blank.title = "Named now"
    window.vault.save_note(blank)
    window.open_note(blank.id)  # the same note again, now titled: still being written
    assert editor.mode_group.checkedId() == SPLIT
    window.open_note(note.id)  # another note: back to reading
    assert editor.mode_group.checkedId() == READING
    window.open_note(blank.id)
    editor.set_view_mode(SPLIT)  # chosen by hand: kept
    window.open_note(note.id)
    assert editor.mode_group.checkedId() == SPLIT


def test_the_text_folds_away_with_its_tab(window):
    from zettelapp.ui.editor import EDIT, READING, SPLIT

    _new_note(window, "Some text.")
    pump(50)
    editor = window.editor
    assert editor.text_tab.isVisible()
    editor.text_tab.click()
    assert editor.mode_group.checkedId() == READING
    assert editor.text_tab.toolTip().startswith("Show the text")
    editor.text_tab.click()
    assert editor.mode_group.checkedId() == SPLIT
    editor.set_view_mode(EDIT)  # no preview to fold the text against
    assert not editor.text_sash.isVisible() and not editor.text_tab.isVisible()


def test_trash_button_sits_before_bold_and_not_in_the_more_menu(window):
    from PySide6.QtWidgets import QToolButton

    buttons = window.editor.findChildren(QToolButton)
    tips = [b.toolTip() for b in buttons]
    assert tips.index("Move note to Trash") < tips.index("Bold (Ctrl+B)")
    assert "Move to Trash" not in [a.text() for a in window.editor.more_menu.actions()]


def test_file_link_button_is_left_of_the_globe(window):
    from PySide6.QtWidgets import QToolButton

    tips = [b.toolTip() for b in window.editor.findChildren(QToolButton)]
    assert tips.index("Link to a file") < tips.index("Insert web link")


def test_dropping_an_image_file_inserts_it(window, tmp_path):
    from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
    from PySide6.QtGui import QDropEvent

    _new_note(window)
    picture = tmp_path / "dropped.png"
    picture.write_bytes(tiny_png())
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(picture))])
    body = window.editor.body
    assert body.canInsertFromMimeData(mime) is True
    body.dropEvent(
        QDropEvent(
            QPointF(5, 5),
            Qt.DropAction.CopyAction,
            mime,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )
    assert "![dropped](asset:" in body.toPlainText()


def test_checklist_toggles_from_the_preview_and_continues_on_enter(window):
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent

    _new_note(window, "- [ ] one\n- [x] two")
    editor = window.editor
    editor._toggle_task(0)
    editor._toggle_task(1)
    assert editor.body.toPlainText() == "- [x] one\n- [ ] two"
    editor.body.undo()  # Ctrl+Z takes a tick back, one box at a time
    assert editor.body.toPlainText() == "- [x] one\n- [x] two"
    editor.body.undo()
    assert editor.body.toPlainText() == "- [ ] one\n- [x] two"
    editor.body.setPlainText("- [ ] a")
    editor.body.moveCursor(editor.body.textCursor().MoveOperation.End)
    editor.body.keyPressEvent(
        QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
    )
    assert editor.body.toPlainText() == "- [ ] a\n- [ ] "


def test_title_image_can_be_chosen_and_removed(window):
    note = _new_note(window)
    first = window.vault.add_image(tiny_png((200, 0, 0)), "a.png")
    second = window.vault.add_image(tiny_png((0, 200, 0)), "b.png")
    editor = window.editor
    editor.note.image = first
    actions = dict(editor._image_actions(second))
    assert "Use as title image" in actions
    actions["Use as title image"]()
    assert editor.note.image == second
    assert "Remove title image" in dict(editor._image_actions(second))
    dict(editor._image_actions(second))["Remove title image"]()
    assert editor.note.image == ""
    editor.flush()
    assert window.vault.get_note(note.id).image == ""


def test_deleting_the_title_image_from_the_body_clears_it(window):
    note = _new_note(window)
    asset = window.vault.add_image(tiny_png((200, 0, 0)), "a.png")
    editor = window.editor
    editor.body.setPlainText(f"before ![a](asset:{asset}) after")
    editor.note.image = asset
    editor.flush()
    assert window.vault.get_note(note.id).image == asset

    editor.body.setPlainText("before  after")  # the image markdown is gone
    editor.flush()
    assert editor.note.image == ""
    assert window.vault.get_note(note.id).image == ""
    assert not editor.picture.isVisible()


def test_deleting_an_unrelated_image_keeps_the_title_image(window):
    note = _new_note(window)
    kept = window.vault.add_image(tiny_png((200, 0, 0)), "a.png")
    other = window.vault.add_image(tiny_png((0, 200, 0)), "b.png")
    editor = window.editor
    editor.body.setPlainText(f"![a](asset:{kept}) ![b](asset:{other})")
    editor.note.image = kept
    editor.flush()

    editor.body.setPlainText(f"![a](asset:{kept})")  # only the other image is removed
    editor.flush()
    assert editor.note.image == kept
    assert window.vault.get_note(note.id).image == kept


def test_note_list_rows_carry_the_thumbnail_and_alarm(window):
    note = window.vault.create_note("Pic", "text")
    note.image = window.vault.add_image(tiny_png(), "p.png")
    note.alarm = (datetime.now(UTC) + timedelta(days=2)).isoformat(timespec="seconds")
    window.vault.save_note(note)
    window.list.refresh()
    row = next(r for r in window.list.model.rows if r["id"] == note.id)
    assert row["image"] and row["image"].endswith(".png")
    assert row["alarm"] is True
    window.list.grab()


def test_due_alarms_notify_once_and_overdue_ones_fire_at_once(window, monkeypatch):
    note = window.vault.create_note("Wake up", "body")
    note.alarm = (datetime.now(UTC) - timedelta(minutes=5)).isoformat(timespec="seconds")
    window.vault.save_note(note)
    fired = []
    monkeypatch.setattr(window, "_notify_alarm", lambda n: fired.append(n.id))
    window.check_alarms()
    window.check_alarms()
    assert fired == [note.id]


def test_alarm_dialog_round_trip(window):
    from zettelapp.ui.dialogs import AlarmDialog

    dialog = AlarmDialog(window)
    dialog.has_time.setChecked(False)
    value = dialog.value()
    assert (value.hour, value.minute) == (AlarmDialog.DEFAULT_HOUR, 0)
    assert datetime.fromisoformat(dialog.iso()).utcoffset() == timedelta(0)
    again = AlarmDialog(window, dialog.iso())
    assert again.value() == value


def test_formula_dialog_builds_markdown_and_flags_errors(window):
    from zettelapp.ui.dialogs import FormulaDialog

    dialog = FormulaDialog(window)
    dialog.edit.setPlainText(r"\frac{a}{b}")
    assert dialog.markdown() == r"$\frac{a}{b}$"
    dialog.block.setChecked(True)
    assert dialog.markdown() == r"$$\frac{a}{b}$$"
    dialog.edit.setPlainText(r"\notacommand")
    assert dialog.problem.text()


def test_menu_checks_are_drawn(window):
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QMenu

    menu = QMenu()
    action = QAction("On", menu)
    action.setCheckable(True)
    action.setChecked(True)
    menu.addAction(action)
    menu.show()
    pump(100)
    image = menu.grab().toImage()
    white = sum(
        1
        for x in range(image.width())
        for y in range(image.height())
        if image.pixelColor(x, y).lightness() > 240 and x < 34
    )
    assert white > 4  # the tick is white on the accent square, not just a painted box
    menu.close()


def _select_rows(window, *ids):
    from PySide6.QtCore import QItemSelectionModel

    view, rows = window.list.view, [r["id"] for r in window.list.model.rows]
    view.clearSelection()
    for note_id in ids:
        view.selectionModel().select(
            window.list.model.index(rows.index(note_id)), QItemSelectionModel.SelectionFlag.Select
        )


def test_several_notes_can_be_selected_trashed_restored_and_deleted(window, monkeypatch):
    from PySide6.QtWidgets import QListView, QMessageBox

    a, b, c = (window.vault.create_note(t, "text") for t in ("A", "B", "C"))
    window.list.refresh()
    assert window.list.view.selectionMode() == QListView.SelectionMode.ExtendedSelection
    _select_rows(window, a.id, c.id)
    assert set(window.list.selected_ids()) == {a.id, c.id}

    window.list.trashRequested.emit(window.list.selected_ids())
    assert window.vault.get_note(a.id).deleted and window.vault.get_note(c.id).deleted
    assert not window.vault.get_note(b.id).deleted
    window.restore_notes([a.id, c.id])
    assert not window.vault.get_note(a.id).deleted

    window.trash_notes([a.id, c.id])
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Yes)
    window.purge_notes([a.id, c.id])
    assert window.vault.get_note(a.id) is None and window.vault.get_note(c.id) is None


def test_duplicating_copies_text_tags_links_and_hand_written_cards(window):
    from zettelapp.core.models import Flashcard

    target = window.vault.create_note("Target", "x")
    note = window.vault.create_note("Idea", "See [[Target]] #inline", tags=["manual"])
    window.vault.add_link(note.id, target.id, "supports")
    window.vault.save_card(Flashcard(None, note.id, "Q?", "A."))
    window.list.refresh()

    window.duplicate_notes([note.id])
    copies = [n for n in window.vault.all_notes() if n.title == "Idea (copy)"]
    assert len(copies) == 1
    copy = copies[0]
    assert copy.body == note.body and set(copy.tags) == {"manual", "inline"}
    assert {(l.dst, l.type) for l in window.vault.links_from(copy.id)} >= {(target.id, "supports")}
    assert [c.front for c in window.vault.cards_for(copy.id) if c.source == "manual"] == ["Q?"]
    assert window.current_note_id() == copy.id  # the copy is opened


def test_shift_arrows_extend_the_selection_and_delete_trashes_it(window):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    for title in ("A", "B", "C"):
        window.vault.create_note(title, "text")
    window.list.refresh()
    view = window.list.view
    view.setFocus()
    view.setCurrentIndex(window.list.model.index(0))
    QTest.keyClick(view, Qt.Key.Key_Down, Qt.KeyboardModifier.ShiftModifier)
    chosen = window.list.selected_ids()
    assert len(chosen) == 2
    QTest.keyClick(view, Qt.Key.Key_Delete)
    assert all(window.vault.get_note(i).deleted for i in chosen)
    assert len(window.list.model.rows) == 1


def test_a_note_time_without_a_zone_does_not_crash_the_editor():
    from PySide6.QtWidgets import QApplication

    from zettelapp.ui.editor import friendly_time

    QApplication.instance() or QApplication(["test"])
    assert "2024" in friendly_time("2024-01-01T12:00:00")
    assert "2024" in friendly_time("2024-01-01T12:00:00+00:00")


def test_file_dialogs_reopen_the_last_folder_used(window, monkeypatch, tmp_path):
    from PySide6.QtWidgets import QFileDialog

    from zettelapp.paths import documents_dir

    picture = tmp_path / "pics" / "a.png"
    picture.parent.mkdir()
    picture.write_bytes(tiny_png())
    _new_note(window)
    asked = []

    def fake_open(parent, caption, folder="", *_args):
        asked.append(folder)
        return str(picture), ""

    monkeypatch.setattr(QFileDialog, "getOpenFileName", fake_open)
    window.editor.insert_image()  # first time: Documents, not the working folder
    window.editor.insert_file_link()  # then the folder of the last file chosen
    assert asked == [str(documents_dir()), str(picture.parent)]


def test_replaced_suggestion_rows_are_hidden_at_once(window):
    # Rows are deleted later; while a modal dialog runs that can be long after they were
    # replaced, and visible ones were drawn under the new rows.
    from zettelapp.core.suggest import Suggestion

    side = window.side
    side.set_suggestions([Suggestion(window.vault.create_note("A").id, "A", 0.9)])
    old = [side.suggestions.itemAt(i).widget() for i in range(side.suggestions.count())]
    side.set_suggestions([Suggestion(window.vault.create_note("B").id, "B", 0.8)])
    assert old and all(w.isHidden() for w in old)


def test_file_dialogs_open_the_last_folder_or_documents_never_the_working_folder(
    window, tmp_path, monkeypatch
):
    from pathlib import Path

    from zettelapp.ui import widgets

    monkeypatch.chdir(tmp_path)  # like the install folder, when started from a shortcut
    first = Path(widgets.dialog_start("Graph.png"))
    assert first.name == "Graph.png" and first.parent != tmp_path
    chosen = tmp_path / "exports"
    chosen.mkdir()
    widgets.remember_folder(str(chosen / "Graph.png"))
    assert Path(widgets.dialog_start("Map.svg")) == chosen / "Map.svg"
    assert Path(widgets.dialog_start()) == chosen


def test_every_menu_item_has_its_own_access_key(window):
    from PySide6.QtGui import QAction

    from zettelapp.ui.main_window import _access_key, unique_access_keys

    actions = [QAction(t) for t in ("&Save", "&Search", "Cu&t", "&Trash", "Save &&&Quit")]
    unique_access_keys(actions)
    assert [a.text() for a in actions] == ["&Save", "S&earch", "Cu&t", "T&rash", "Save &&&Quit"]

    menus = [a.menu() for a in window.menuBar().actions() if a.menu() is not None]
    for menu in menus:
        keys = [_access_key(a.text()) for a in menu.actions() if a.text()]
        letters = [k[1] for k in keys if k is not None]
        assert len(letters) == len(set(letters)), menu.title()


def test_a_message_on_screen_follows_a_theme_switch(window):
    from zettelapp.ui import theme

    window._set_theme("light")
    window.info.show_message("Saved", "success")
    light = theme.current().surface
    window._set_theme("dark")
    assert theme.current().surface in window.info.styleSheet()
    assert light not in window.info.styleSheet()


def test_an_alarm_or_a_link_brings_a_maximised_window_back_maximised(window):
    from PySide6.QtCore import Qt

    window.setWindowState(Qt.WindowState.WindowMaximized | Qt.WindowState.WindowMinimized)
    window.bring_forward()
    assert window.windowState() & Qt.WindowState.WindowMaximized
    assert not window.windowState() & Qt.WindowState.WindowMinimized


def test_the_main_window_passes_theme_changes_on(window):
    from PySide6.QtCore import QEvent
    from PySide6.QtWidgets import QApplication

    calls = []
    window.desktopThemeChanged.connect(lambda: calls.append(1))
    QApplication.sendEvent(window, QEvent(QEvent.Type.ThemeChange))
    assert calls == [1]


def test_the_store_package_uses_its_mcp_alias_and_skips_the_update_check(window, monkeypatch):
    from zettelapp import settings, winintegration
    from zettelapp.ui import main_window, settings_dialog

    assert winintegration.is_packaged() is False  # tests never run from a package
    monkeypatch.setattr(winintegration, "is_packaged", lambda: True)
    command, args, env = settings_dialog.mcp_command(None, False)
    assert command.endswith(r"WindowsApps\zettelapp-mcp.exe") or command.endswith(
        "WindowsApps/zettelapp-mcp.exe"
    )
    asked = []
    monkeypatch.setattr(main_window, "run_task", lambda *a, **k: asked.append(a))
    settings.put(settings.UPDATE_CHECK, True)
    window.check_for_updates()
    assert asked == []  # the Store updates it


def test_the_editor_text_size_applies_from_the_start(tmp_path, monkeypatch):
    """Options ▸ Editor text size reached the text and the preview only once Options was saved."""
    monkeypatch.setenv("ZETTELAPP_SETTINGS_FILE", str(tmp_path / "settings.ini"))
    from PySide6.QtWidgets import QApplication

    from zettelapp import settings
    from zettelapp.ui.main_window import MainWindow

    QApplication.instance() or QApplication(["test"])
    settings.put(settings.EDITOR_FONT_SIZE, 16)
    w = MainWindow()
    try:
        assert w.editor.body.font().pointSizeF() == 16
        assert w.editor.preview.font().pointSizeF() == 16
    finally:
        w.close()
        w.deleteLater()


def test_closing_the_vault_drops_a_pending_reorder(window, monkeypatch):
    """Ordered by closeness, opening a note reorders the list a moment later; closing the vault
    in that moment let the reorder read the closed database."""
    import sys

    errors = []
    monkeypatch.setattr(sys, "excepthook", lambda *exc: errors.append(exc))
    window.list.sort_key = "meaning"
    first = _new_note(window, "One idea.")
    other = window.vault.create_note("Other", "Another idea.")
    window.open_note(other.id)
    assert first.id != other.id
    window.close_vault()
    pump(500)
    assert errors == []


def test_the_first_window_fits_the_screen():
    """With no saved geometry the window took 1440 x 900 whatever the screen: on a laptop's
    1366 x 768 it ran off the bottom, and Xfce doesn't pull it back."""
    from PySide6.QtCore import QSize

    from zettelapp.ui.main_window import first_window_size

    minimum = QSize(980, 640)
    assert first_window_size(QSize(2560, 1400), minimum) == QSize(1440, 900)
    laptop = first_window_size(QSize(1366, 740), minimum)
    assert laptop.width() <= 1366 - 40 and laptop.height() <= 740 - 60
    assert first_window_size(QSize(800, 560), minimum) == minimum  # never below the minimum
