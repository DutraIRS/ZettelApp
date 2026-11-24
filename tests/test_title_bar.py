"""The window's own title bar (Windows): what each point of the window does, and its buttons."""

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QMainWindow, QMenuBar, QWidget

from zettelapp.ui import title_bar
from zettelapp.ui.title_bar import EDGE, TitleBar, WindowFrame

CAPTION, CLIENT, LEFT, TOP, BOTTOM_RIGHT = 2, 1, 10, 12, 17


@pytest.fixture
def window():
    app = QApplication.instance() or QApplication(["test"])
    shown = QMainWindow()
    menus = QMenuBar()
    menus.addMenu("&File")
    menus.addMenu("&Edit")
    bar = TitleBar(shown, menus)
    shown.setMenuWidget(bar)
    shown.setCentralWidget(QWidget())
    shown.setWindowTitle("Notes - ZettelApp")
    frame = WindowFrame(shown, bar)
    shown.resize(900, 600)
    shown.show()
    app.processEvents()
    yield shown, bar, frame
    shown.close()
    shown.deleteLater()


def _centre(window, widget):
    return widget.mapTo(window, widget.rect().center())


def test_the_empty_row_drags_the_window_and_its_menus_and_buttons_are_pressed(window):
    shown, bar, frame = window
    assert frame.hit_at(QPoint(shown.width() // 2, bar.height() // 2)) == CAPTION
    file_menu = bar.menus.actionGeometry(bar.menus.actions()[0]).center()
    assert frame.hit_at(bar.menus.mapTo(shown, file_menu)) == CLIENT
    for button in bar.buttons.values():
        assert frame.hit_at(_centre(shown, button)) == CLIENT
    assert frame.hit_at(QPoint(shown.width() // 2, bar.height() + 50)) == CLIENT


def test_the_edges_resize_the_window(window):
    shown, _bar, frame = window
    assert frame.hit_at(QPoint(1, 300)) == LEFT
    assert frame.hit_at(QPoint(400, 1)) == TOP
    assert frame.hit_at(QPoint(shown.width() - 1, shown.height() - 1)) == BOTTOM_RIGHT
    assert frame.hit_at(QPoint(EDGE + 2, 300)) == CLIENT


def test_the_row_shows_the_title_and_the_window_s_state(window):
    shown, bar, _frame = window
    assert bar._title.text() == "Notes - ZettelApp"
    shown.setWindowTitle("Ideas - ZettelApp")
    assert bar._title.text() == "Ideas - ZettelApp"
    assert bar.buttons["maximise"].toolTip() == "Maximise"
    shown.showMaximized()
    QApplication.processEvents()
    bar.sync()
    assert bar.buttons["maximise"].toolTip() == "Restore Down"


def test_only_windows_own_platform_gets_the_row(monkeypatch):
    QApplication.instance() or QApplication(["test"])
    # tests run offscreen, so the main window keeps Qt's menu bar (and menuBar() stays safe)
    assert not title_bar.wanted()
    monkeypatch.setattr(title_bar.sys, "platform", "linux")
    monkeypatch.setattr(title_bar.QGuiApplication, "platformName", lambda: "windows")
    assert not title_bar.wanted()
    monkeypatch.setattr(title_bar.sys, "platform", "win32")
    assert title_bar.wanted()


def test_the_menus_keep_their_width_right_to_left():
    from PySide6.QtCore import QEventLoop, Qt, QTimer

    app = QApplication.instance() or QApplication(["test"])
    menus = title_bar.MenuBar()
    for text in ("&File", "&Edit", "&View", "&Insert", "&Tools", "&Help"):
        menus.addMenu(text)
    shown = QMainWindow()
    shown.setMenuWidget(TitleBar(shown, menus))
    shown.setCentralWidget(QWidget())
    shown.resize(1000, 600)
    shown.show()
    try:
        app.processEvents()
        # left to right, the sum of the items is exactly Qt's own answer
        assert menus.natural_width() == QMenuBar.sizeHint(menus).width()
        shown.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        loop = QEventLoop()
        QTimer.singleShot(300, loop.quit)  # Qt's own hint shrinks over a few layout passes
        loop.exec()
        assert menus.width() >= menus.natural_width()  # all six menus, no » overflow
    finally:
        shown.close()
        shown.deleteLater()


def test_close_turns_red_on_hover_and_the_others_take_the_theme_s_hover(window):
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QEnterEvent, QHoverEvent

    from zettelapp.ui import theme

    shown, bar, _frame = window
    theme.apply_theme(QApplication.instance(), "dark")

    def hovered(button):
        centre = QPointF(button.rect().center())
        where = QPointF(button.mapToGlobal(button.rect().center()))
        QApplication.sendEvent(button, QEnterEvent(centre, centre, where))
        for kind in (QEvent.Type.HoverEnter, QEvent.Type.HoverMove):
            QApplication.sendEvent(button, QHoverEvent(kind, centre, where, QPointF(-1, -1)))
        button.setAttribute(Qt.WidgetAttribute.WA_UnderMouse, True)
        button.repaint()
        corner = button.mapTo(shown, button.rect().topLeft())
        return shown.grab().toImage().pixelColor(corner.x() + 3, corner.y() + 3).name()

    assert hovered(bar.buttons["close"]) == "#c42b1c"
    assert hovered(bar.buttons["minimise"]) not in ("#c42b1c", theme.current().sidebar)
