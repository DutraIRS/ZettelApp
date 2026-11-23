"""Folding side panels: a sash on the panel's edge and a tab that hides or shows the panel.

Adapted from Euterpes' text ribbon. The sash is a six-pixel strip standing on the splitter
handle between a side panel (the note list or the links panel) and the editor: solid, with a
resize cursor and a highlighted hover. Dragging it resizes the panel; a double-click hides or
shows it. Halfway down, a tab pops out of the sash into the editor: a rounded rectangle in the
accent colour, square where it grows out of the sash, with grip dots on the wall and a chevron
pointing where the panel will go. A click (or Space when it has the keyboard focus) folds the
panel away or brings it back; dragging the tab resizes like the sash. With the panel hidden the
sash and the tab stay at the editor's edge, to bring it back. Everything follows the layout
direction, so in Arabic the note list folds to the right.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QPoint, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSplitter, QToolButton, QWidget

from zettelapp.i18n import _
from zettelapp.ui import theme

SASH_WIDTH = 6
GRIP_DOT = 3
GRIP_GAP = 4
GRIP_DOTS = 3
TAB_REACH = 10
TAB_HEIGHT = 32
TAB_RADIUS = 6
TAB_BOTTOM = 12  # the tab's gap above the bottom of the panes
DRAG_START = 4  # how far a press on the tab must move sideways before it resizes


class PanelFold:
    """The state shared by a panel's sash and tab: which pane folds, and where it sits."""

    def __init__(self, splitter: QSplitter, panel: QWidget, editor: QWidget):
        self.splitter = splitter
        self.panel = panel
        self.editor = editor

    def panel_on_left(self) -> bool:
        """Whether the panel sits left of the editor on screen (mirrored in right-to-left)."""
        before = self.splitter.indexOf(self.panel) < self.splitter.indexOf(self.editor)
        return before != (self.splitter.layoutDirection() == Qt.LayoutDirection.RightToLeft)

    def shown(self) -> bool:
        return not self.panel.isHidden()

    def edge(self, parent: QWidget) -> int:
        """The x, in *parent*, of the line between the panel and the editor."""
        left = self.panel_on_left()
        if self.shown():
            x = self.panel.width() if left else 0
            return self.panel.mapTo(parent, QPoint(x, 0)).x()
        x = 0 if left else self.editor.width()
        return self.editor.mapTo(parent, QPoint(x, 0)).x()

    def resize_to(self, x: int, parent: QWidget) -> None:
        """Make the panel reach from its outer edge to *x* (in *parent*), within its limits."""
        if not self.shown():
            return
        left = self.panel_on_left()
        outer = self.panel.mapTo(parent, QPoint(0 if left else self.panel.width(), 0)).x()
        sizes = self.splitter.sizes()
        i, j = self.splitter.indexOf(self.panel), self.splitter.indexOf(self.editor)
        pair = sizes[i] + sizes[j]
        width = abs(x - outer)
        width = max(self.panel.minimumWidth(), min(width, pair - self.editor.minimumWidth()))
        sizes[i], sizes[j] = width, pair - width
        self.splitter.setSizes(sizes)


class PanelSash(QWidget):
    """A solid resize strip on the line between a side panel and the editor."""

    def __init__(self, fold: PanelFold, toggle: Callable[[], None], parent: QWidget):
        super().__init__(parent)
        self.fold = fold
        self.toggle = toggle
        self._hover = False
        self.setFixedWidth(SASH_WIDTH)
        self.setCursor(Qt.CursorShape.SplitHCursor)
        text = _("Drag to resize, double-click to hide or show")
        self.setToolTip(text)
        self.setAccessibleName(text)
        fold.splitter.splitterMoved.connect(lambda *_args: self.place())
        for widget in (fold.splitter, fold.panel, fold.editor):
            widget.installEventFilter(self)

    def place(self) -> None:
        """Stand on the line between the panel and the editor, as tall as the splitter."""
        parent = self.parentWidget()
        splitter = self.fold.splitter
        top = splitter.mapTo(parent, QPoint(0, 0)).y()
        x = self.fold.edge(parent) - SASH_WIDTH // 2
        self.setGeometry(x, top, SASH_WIDTH, max(splitter.height(), 1))
        self.setVisible(splitter.isVisible())
        self.raise_()

    def eventFilter(self, watched, event) -> bool:  # noqa: N802 - Qt API
        if event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Move,
            QEvent.Type.Show,
            QEvent.Type.Hide,
            QEvent.Type.LayoutDirectionChange,
        ):
            self.place()
        return False

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        t = theme.current()
        painter.fillRect(self.rect(), QColor(t.accent if self._hover else t.border))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(t.on_accent if self._hover else t.text_muted))
        top = (self.height() - (GRIP_DOTS - 1) * GRIP_GAP) / 2
        for dot in range(GRIP_DOTS):
            point = QPointF(self.width() / 2, top + dot * GRIP_GAP)
            painter.drawEllipse(point, GRIP_DOT / 2, GRIP_DOT / 2)
        painter.end()

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt API
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt API
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.buttons() & Qt.MouseButton.LeftButton:
            point = self.mapToParent(event.position().toPoint())
            self.fold.resize_to(point.x(), self.parentWidget())

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()


class CollapseButton(QToolButton):
    """The tab on the sash: a click folds the panel away or brings it back, a drag resizes."""

    def __init__(self, fold: PanelFold, sash: PanelSash, tips: tuple[str, str], parent: QWidget):
        super().__init__(parent)
        self.fold = fold
        self.sash = sash
        self.tips = tips  # (when shown: hide it, when hidden: show it)
        self._hover = False
        self._pressed_at: QPointF | None = None
        self._dragging = False
        self.setFixedSize(QSize(SASH_WIDTH + TAB_REACH, TAB_HEIGHT))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        sash.installEventFilter(self)
        self.refresh()

    def refresh(self) -> None:
        """Turn the chevron, tooltip and accessible name the way the panel will go."""
        tip = self.tips[0] if self.fold.shown() else self.tips[1]
        self.setToolTip(tip)
        self.setAccessibleName(tip)
        self.place()
        self.update()

    def place(self) -> None:
        """Pop out of the sash near the bottom, into the editor."""
        sash = self.sash
        if not sash.isVisible():
            self.setVisible(False)
            return
        y = sash.y() + max(sash.height() - self.height() - TAB_BOTTOM, 0)
        x = sash.x() if self.fold.panel_on_left() else sash.x() + SASH_WIDTH - self.width()
        self.setGeometry(x, y, self.width(), self.height())
        self.setVisible(True)
        self.raise_()

    def eventFilter(self, watched, event) -> bool:  # noqa: N802 - Qt API
        if watched is self.sash and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Move,
            QEvent.Type.Show,
            QEvent.Type.Hide,
        ):
            self.place()
        return False

    # Painting ---------------------------------------------------------------------------

    def tab_path(self) -> QPainterPath:
        """Square on the wall (the sash's side), rounded where the tab stands free."""
        left = self.fold.panel_on_left()
        path = QPainterPath()
        x = -TAB_RADIUS if left else 0.0
        path.addRoundedRect(
            QRectF(x, 0.0, self.width() + TAB_RADIUS, self.height()), TAB_RADIUS, TAB_RADIUS
        )
        wall = QPainterPath()
        wall.addRect(QRectF(0.0, 0.0, self.width(), self.height()))
        return path.intersected(wall)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = theme.current()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(t.accent_hover if self._hover else t.accent))
        painter.drawPath(self.tab_path())
        ink = QColor(t.on_accent)
        painter.setBrush(ink)
        left = self.fold.panel_on_left()
        wall_x = SASH_WIDTH / 2 if left else self.width() - SASH_WIDTH / 2
        middle = self.height() / 2
        for dot in range(GRIP_DOTS):
            y = middle + (dot - (GRIP_DOTS - 1) / 2) * GRIP_GAP
            painter.drawEllipse(QPointF(wall_x, y), GRIP_DOT / 2, GRIP_DOT / 2)
        reach_x = SASH_WIDTH + TAB_REACH / 2 if left else TAB_REACH / 2
        # The chevron points where the panel goes: towards its side to hide it, away to show.
        towards_panel = self.fold.shown()
        pointing_left = left == towards_panel
        self._chevron(painter, ink, reach_x, middle, pointing_left)
        if self.hasFocus():
            focus = QPen(QColor(t.text), 1.0, Qt.PenStyle.DotLine)
            painter.setPen(focus)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5))
        painter.end()

    @staticmethod
    def _chevron(painter: QPainter, ink: QColor, x: float, y: float, left: bool) -> None:
        spread = 2.8
        lean = spread * 0.8 * (-1 if left else 1)
        path = QPainterPath()
        path.moveTo(x - lean, y - spread * 1.4)
        path.lineTo(x + lean, y)
        path.lineTo(x - lean, y + spread * 1.4)
        pen = QPen(ink, 2.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt API
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt API
        self._hover = False
        self.update()
        super().leaveEvent(event)

    # A click, or a drag ---------------------------------------------------------------

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt API
        self._pressed_at = event.position()
        self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt API
        held = event.buttons() & Qt.MouseButton.LeftButton
        if self._pressed_at is not None and held and self.fold.shown():
            moved = abs(event.position().x() - self._pressed_at.x())
            if not self._dragging and moved > DRAG_START:
                self._dragging = True
                self.setDown(False)  # no click when this press lets go
            if self._dragging:
                wall = (
                    SASH_WIDTH / 2 if self.fold.panel_on_left() else self.width() - SASH_WIDTH / 2
                )
                offset = round(self._pressed_at.x() - wall)  # keep where the tab was held
                point = self.mapToParent(event.position().toPoint()) - QPoint(offset, 0)
                self.fold.resize_to(point.x(), self.parentWidget())
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt API
        self._pressed_at, self._dragging = None, False
        super().mouseReleaseEvent(event)
