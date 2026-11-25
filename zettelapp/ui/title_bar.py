"""On Windows, the window's top row in the program's own colours, as GitHub Desktop has it.

Windows draws a title bar in its own colours (the accent colour, when the user chose that) above
the menus. Instead, the menus share one row with the program's icon, the window's title and the
window's buttons, drawn in the theme's colours. The window keeps the native frame's behaviour:
it snaps, resizes from every edge, casts its shadow, animates and maximises on a double click,
because Windows is told that the whole window is client area (``WM_NCCALCSIZE``) and where its
caption and edges are (``WM_NCHITTEST``). Elsewhere the desktop draws its own title bar.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from typing import Any

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QSizePolicy,
    QStyle,
    QStyleOption,
    QToolButton,
    QWidget,
)

from zettelapp.i18n import _
from zettelapp.ui import icons

HEIGHT = 32
"""The row's height in pixels, as Windows' own caption."""
BUTTON_WIDTH = 46
"""A window button's width, as Windows draws them."""
EDGE = 6
"""How far in from the window's edge a press resizes it, in pixels."""

GLYPHS = {"minimise": "", "maximise": "", "restore": "", "close": ""}
"""The window buttons in Segoe Fluent Icons; without that font, plain characters."""
PLAIN = {"minimise": "–", "maximise": "□", "restore": "❐", "close": "✕"}

_WM_NCCALCSIZE = 0x0083
_WM_NCHITTEST = 0x0084
_HTCLIENT, _HTCAPTION = 1, 2
_HITS = {  # (left, right, top, bottom) -> what Windows does there
    (True, False, False, False): 10,
    (False, True, False, False): 11,
    (False, False, True, False): 12,
    (True, False, True, False): 13,
    (False, True, True, False): 14,
    (False, False, False, True): 15,
    (True, False, False, True): 16,
    (False, True, False, True): 17,
}
_GWL_STYLE = -16
_WS_FRAME = 0x00040000 | 0x00C00000 | 0x00080000 | 0x00020000 | 0x00010000
"""Thick frame, caption, system menu, minimise and maximise boxes: snapping and animations."""
_SWP_REFRESH = 0x0020 | 0x0001 | 0x0002 | 0x0004 | 0x0010
"""Frame changed; no move, size, z-order or activation."""
_SM_CXSIZEFRAME, _SM_CXPADDEDBORDER = 32, 92


def wanted() -> bool:
    """Whether to draw the window's own title bar: on Windows' own platform, not offscreen."""
    return sys.platform == "win32" and QGuiApplication.platformName() == "windows"


class MenuBar(QMenuBar):
    """The title bar's menus, the same width whichever way the interface reads.

    Right to left, QMenuBar measures its mirrored items against the width it already has, so
    its size hint is whatever width it was given: in a row it shrinks to the » overflow button.
    Here the width is the sum of the items, as Qt works it out left to right."""

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt's name
        hint = super().sizeHint()
        if not self.isRightToLeft():
            return hint
        return QSize(self.natural_width(), hint.height())

    def natural_width(self) -> int:
        """The width the menus need: margins and panel either side, then each item and its gap."""
        option = QStyleOption()
        option.initFrom(self)
        style = self.style()

        def metric(name: QStyle.PixelMetric) -> int:
            return style.pixelMetric(name, option, self)

        spacing = metric(QStyle.PixelMetric.PM_MenuBarItemSpacing)
        items = sum(
            self.actionGeometry(action).width() + spacing
            for action in self.actions()
            if action.isVisible()
        )
        sides = metric(QStyle.PixelMetric.PM_MenuBarHMargin)
        sides += metric(QStyle.PixelMetric.PM_MenuBarPanelWidth)
        return items + 2 * sides


class TitleBar(QWidget):
    """The top row: the program's icon, the menus, the window's title and the window's buttons."""

    def __init__(self, window: QMainWindow, menus: QMenuBar) -> None:
        """Make the row around a window's menus."""
        super().__init__(window)
        self.setObjectName("TitleBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(HEIGHT)
        self._window = window
        self.menus = menus
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 0, 0, 0)
        row.setSpacing(4)
        self._icon = QLabel()
        self._icon.setPixmap(window.windowIcon().pixmap(16, 16))
        self._title = QLabel(window.windowTitle())
        self._title.setObjectName("TitleText")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        for label in (self._icon, self._title):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        row.addWidget(self._icon, 0, Qt.AlignmentFlag.AlignVCenter)
        # Centred: the menu bar is shorter than the row, and a row lays it out at the top.
        row.addWidget(menus, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self._title, 1)
        self.buttons: dict[str, QToolButton] = {}
        for name, slot in (
            ("minimise", window.showMinimized),
            ("maximise", self._toggle_maximised),
            ("close", window.close),
        ):
            button = QToolButton()
            button.setObjectName(f"TitleButton_{name}")
            button.setFixedSize(BUTTON_WIDTH, HEIGHT)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.clicked.connect(slot)
            row.addWidget(button)
            self.buttons[name] = button
        family = icons.font_family()
        if family is not None:
            font = QFont(family)
            font.setPixelSize(10)
            for button in self.buttons.values():
                button.setFont(font)
        window.windowTitleChanged.connect(self._title.setText)
        window.windowIconChanged.connect(lambda icon: self._icon.setPixmap(icon.pixmap(16, 16)))
        self.sync()

    def _glyph(self, name: str) -> str:
        return (GLYPHS if icons.font_family() is not None else PLAIN)[name]

    def _toggle_maximised(self) -> None:
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def sync(self) -> None:
        """Show the window's state: Maximise, or Restore once maximised."""
        maximised = self._window.isMaximized()
        self.buttons["minimise"].setText(self._glyph("minimise"))
        self.buttons["minimise"].setToolTip(_("Minimise"))
        self.buttons["maximise"].setText(self._glyph("restore" if maximised else "maximise"))
        self.buttons["maximise"].setToolTip(_("Restore Down") if maximised else _("Maximise"))
        self.buttons["close"].setText(self._glyph("close"))
        self.buttons["close"].setToolTip(_("Close"))

    def is_caption(self, point: QPoint) -> bool:
        """Whether a point of the row (in its own pixels) drags the window: not a menu or button."""
        child = self.childAt(point)
        if child is None or child in (self._icon, self._title):
            return True
        if child is self.menus:
            return self.menus.actionAt(self.menus.mapFrom(self, point)) is None
        return False


class _Rect(ctypes.Structure):
    _fields_ = (("left", ctypes.c_long), ("top", ctypes.c_long))
    _fields_ += (("right", ctypes.c_long), ("bottom", ctypes.c_long))


class _Margins(ctypes.Structure):
    _fields_ = tuple((name, ctypes.c_int) for name in ("left", "right", "top", "bottom"))


class WindowFrame:
    """Keeps the native frame's behaviour for a window whose title bar is :class:`TitleBar`."""

    def __init__(self, window: QMainWindow, bar: TitleBar) -> None:
        """Take over a window's title bar; call before it is first shown."""
        self._window = window
        self._bar = bar
        self._styled = False
        window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

    def restyle(self) -> None:
        """Give the native window back its frame's styles and shadow, once it exists."""
        if self._styled:
            return
        self._styled = True
        user32 = ctypes.windll.user32
        hwnd = int(self._window.winId())
        style = user32.GetWindowLongPtrW(hwnd, _GWL_STYLE)
        user32.SetWindowLongPtrW(hwnd, _GWL_STYLE, style | _WS_FRAME)
        margins = _Margins(0, 0, 0, 1)  # a sliver of frame inside the window keeps the shadow
        ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))
        user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, _SWP_REFRESH)

    def handle(self, message: Any) -> int | None:
        """Answer a Windows message about the frame, or None to let Qt handle it."""
        if not self._styled:  # the native window is still being made: Qt's frame for now
            return None
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == _WM_NCCALCSIZE and msg.wParam:
            self._fit_maximised(msg.hWnd, msg.lParam)
            return 0  # the whole window is client area: no Windows title bar
        if msg.message == _WM_NCHITTEST:
            return self._hit(msg.hWnd, msg.lParam)
        return None

    def _fit_maximised(self, hwnd: int, address: int) -> None:
        """A maximised window overhangs the screen by its frame: keep its content on screen."""
        user32 = ctypes.windll.user32
        if not user32.IsZoomed(hwnd):
            return
        dpi = user32.GetDpiForWindow(hwnd)
        frame = user32.GetSystemMetricsForDpi(_SM_CXSIZEFRAME, dpi)
        frame += user32.GetSystemMetricsForDpi(_SM_CXPADDEDBORDER, dpi)
        rect = _Rect.from_address(address)  # the first rectangle of NCCALCSIZE_PARAMS
        rect.left += frame
        rect.top += frame
        rect.right -= frame
        rect.bottom -= frame

    def _hit(self, hwnd: int, position: int) -> int:
        """Where a screen point falls: an edge to resize by, the caption, or the window."""
        x = ctypes.c_short(position & 0xFFFF).value
        y = ctypes.c_short((position >> 16) & 0xFFFF).value
        rect = _Rect()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        ratio = self._window.devicePixelRatioF()
        point = QPoint(round((x - rect.left) / ratio), round((y - rect.top) / ratio))
        return self.hit_at(point)

    def hit_at(self, point: QPoint) -> int:
        """What Windows should do at a point of the window, in its own pixels."""
        window = self._window
        if not window.isMaximized():
            edges = (
                point.x() < EDGE,
                point.x() >= window.width() - EDGE,
                point.y() < EDGE,
                point.y() >= window.height() - EDGE,
            )
            if any(edges):
                return _HITS.get(edges, _HTCLIENT)
        inside = self._bar.mapFrom(window, point)
        if 0 <= inside.y() < self._bar.height() and self._bar.is_caption(inside):
            return _HTCAPTION
        return _HTCLIENT
