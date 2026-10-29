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
