"""Folding the note list and the links panel away: tabs, sashes, the View menu, saved state."""

# ruff: noqa: F811  (the `window` fixture is imported, then used as a test argument)

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6.QtWidgets")

from tests.test_ui_smoke import pump, window  # noqa: E402, F401


def test_tabs_and_menu_fold_each_panel_and_the_choice_is_remembered(window):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    from zettelapp import settings

    fold, sash, tab = window.folds["list"]
    assert fold.shown() and tab.isVisible() and sash.isVisible()
    QTest.mouseClick(tab, Qt.MouseButton.LeftButton)  # the tab folds the list away
    assert window.list.isHidden() and settings.get(settings.NOTE_LIST_HIDDEN)
    assert not window.fold_actions["list"].isChecked()
    assert tab.isVisible()  # still there, to bring the list back
    QTest.mouseDClick(sash, Qt.MouseButton.LeftButton)  # so does a double-click on the sash
    assert not window.list.isHidden() and not settings.get(settings.NOTE_LIST_HIDDEN)
    window.fold_actions["links"].trigger()  # View ▸ Links Panel
    assert window.side.isHidden() and settings.get(settings.LINKS_PANEL_HIDDEN)
    assert window.fold_actions["links"].shortcut().toString() == "Ctrl+Shift+K"
    assert window.fold_actions["list"].shortcut().toString() == "Ctrl+Shift+L"

    from zettelapp.ui.main_window import MainWindow

    again = MainWindow()  # the next start keeps the links panel folded
    try:
        assert again.side.isHidden() and not again.list.isHidden()
        assert not again.fold_actions["links"].isChecked()
    finally:
        again.close()
        again.deleteLater()


def test_finding_notes_brings_the_note_list_back(window):
    window.toggle_panel("list", False)
    window._focus_search()
    assert not window.list.isHidden()


def test_chevrons_point_where_the_panel_goes_also_right_to_left(window):
    from PySide6.QtCore import Qt

    list_fold, links_fold = window.folds["list"][0], window.folds["links"][0]
    assert list_fold.panel_on_left() and not links_fold.panel_on_left()
    window.splitter.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # Arabic
    try:
        assert not list_fold.panel_on_left() and links_fold.panel_on_left()
        pump(50)
        sash, tab = window.folds["list"][1:]
        tab.place()
        # The list now sits right of the editor: its tab pops out leftwards into the editor.
        assert tab.geometry().right() <= sash.geometry().right() + 1
        assert tab.geometry().left() < sash.geometry().left()
        tab.grab()  # paints in either direction
    finally:
        window.splitter.setLayoutDirection(Qt.LayoutDirection.LeftToRight)


def test_dragging_resizes_within_the_panels_limits(window):
    window.resize(1400, 900)
    pump(50)
    fold, sash, _tab = window.folds["list"]
    page = sash.parentWidget()
    left = window.list.mapTo(page, window.list.rect().topLeft()).x()
    fold.resize_to(left + 400, page)
    assert abs(window.list.width() - 400) <= 2
    fold.resize_to(left + 10, page)  # never narrower than the list allows
    assert window.list.width() >= window.list.minimumWidth()
    sash.place()
    assert abs(sash.geometry().center().x() - fold.edge(page)) <= 3
