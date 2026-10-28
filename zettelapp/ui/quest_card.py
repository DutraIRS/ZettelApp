"""The adventure's widgets: a teaching-tip card and a spotlight on the control to use.

Like the update notice, the card is a child of the main window that never takes focus
or blocks anything; it sits in a lower corner, moving to the other one when it would
cover the control it points at. The spotlight is a click-through overlay that draws a
gently pulsing outline around that control, then settles into a still one.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import (
    QElapsedTimer,
    QEvent,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QSize,
    Qt,
    QTimer,
)
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRegion,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from zettelapp.paths import resource_path
from zettelapp.ui import icons, theme
from zettelapp.ui.widgets import accent_button, label, link_button, tool_button

CARD_WIDTH = 384
HERO_HEIGHT = 128  # illustrations are 3:1 (1200 x 400 px)
MARGIN = 16
RADIUS = 8.0

# A target is a widget, or a widget and a rectangle inside it (such as one tab of a tab bar).
Target = QWidget | tuple[QWidget, QRect]


def target_rect(window: QWidget, target: Target | None) -> QRect | None:
    """The target's rectangle in *window* coordinates, or None when it can't be seen."""
    if target is None:
        return None
    widget, rect = target if isinstance(target, tuple) else (target, target.rect())
    try:
        if not widget.isVisible() or widget.window() is not window.window():
            return None
        top_left = widget.mapTo(window, rect.topLeft())
    except RuntimeError:  # the widget was deleted (a suggestion row, for instance)
        return None
    found = QRect(top_left, rect.size()).intersected(window.rect())
    return found if found.width() > 2 and found.height() > 2 else None


def quest_pixmap(name: str) -> QPixmap | None:
    """A bundled illustration, or None when the file is missing or unreadable."""
    path = resource_path("quest", name)
    if not path.is_file():
        return None
    px = QPixmap(str(path))
    return None if px.isNull() else px


class Illustration(QWidget):
    """The card's hero image; draws a tinted glyph when the picture isn't there."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(HERO_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.pixmap: QPixmap | None = None
        self.glyph = "flag"

    def set_image(self, name: str, glyph: str) -> None:
        self.pixmap = quest_pixmap(name)
        self.glyph = glyph
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        t = theme.current()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = QRectF(self.rect())
        clip = QPainterPath()  # rounded top corners, square bottom, inside the card's border
        clip.moveTo(rect.left(), rect.bottom())
        clip.lineTo(rect.left(), rect.top() + RADIUS - 1)
        clip.quadTo(rect.left(), rect.top(), rect.left() + RADIUS - 1, rect.top())
        clip.lineTo(rect.right() - RADIUS + 1, rect.top())
        clip.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + RADIUS - 1)
        clip.lineTo(rect.right(), rect.bottom())
        clip.closeSubpath()
        painter.setClipPath(clip)
        if self.pixmap is not None:
            source = QRectF(self.pixmap.rect())
            scale = max(rect.width() / source.width(), rect.height() / source.height())
            w, h = rect.width() / scale, rect.height() / scale
            crop = QRectF(source.center().x() - w / 2, source.center().y() - h / 2, w, h)
            painter.drawPixmap(rect, self.pixmap, crop)  # fill, centred, cropping the rest
            return
        accent = t.q("accent")
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        start, end = QColor(accent), QColor(accent)
        start.setAlpha(70 if t.dark else 46)
        end.setAlpha(18 if t.dark else 12)
        gradient.setColorAt(0, start)
        gradient.setColorAt(1, end)
        painter.fillRect(rect, t.q("surface"))
        painter.fillRect(rect, gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        dot = QColor(accent)
        dot.setAlpha(40)
        painter.setBrush(dot)
        for i, (x, y, r) in enumerate(
            ((0.12, 0.3, 3), (0.2, 0.72, 2), (0.82, 0.25, 2.5), (0.9, 0.7, 3.5), (0.7, 0.85, 2))
        ):
            painter.drawEllipse(QPointF(rect.width() * x, rect.height() * y), r + i % 2, r + i % 2)
        disc = QColor(t.surface)
        disc.setAlpha(230)
        painter.setBrush(disc)
        center = rect.center()
        painter.drawEllipse(center, 40, 40)
        size = 40
        icon = icons.icon(self.glyph, t.accent, size).pixmap(size, size)
        painter.drawPixmap(QPointF(center.x() - size / 2, center.y() - size / 2), icon)


class ProgressDots(QWidget):
    """One dot per chapter: found (filled), skipped (hollow), current (ringed), to come."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.states: list[str] = []
        self.setFixedHeight(12)

    def set_states(self, states: list[str]) -> None:
        self.states = states
        self.setFixedWidth(max(0, len(states) * 12 - 4))
        self.setVisible(bool(states))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        t = theme.current()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for i, state in enumerate(self.states):
            center = QPointF(4 + i * 12, self.height() / 2)
            if state == "found":
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(t.q("accent"))
                painter.drawEllipse(center, 4, 4)
            elif state == "current":
                painter.setPen(QPen(t.q("accent"), 1.6))
                painter.setBrush(t.q("accent_subtle"))
                painter.drawEllipse(center, 4, 4)
            elif state == "skipped":
                painter.setPen(QPen(t.q("text_muted"), 1.2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, 3.4, 3.4)
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(t.q("border_strong"))
                painter.drawEllipse(center, 2.5, 2.5)


@dataclass
class CardContent:
    image: str
    glyph: str
    kicker: str
    title: str
    story: str
    task: str = ""
    hint: str = ""
    progress: list[str] | None = None
    primary: tuple[str, Callable[[], None]] | None = None
    secondary: tuple[str, Callable[[], None]] | None = None
    hint_label: str = ""


class QuestCard(QFrame):
    """A teaching tip in a lower corner of the main window (see the module docstring)."""

    def __init__(self, window: QMainWindow, on_close: Callable[[], None], close_tip: str):
        super().__init__(window)
        self.window = window
        self.avoid: QRect | None = None
        self.setObjectName("Toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 70))
        self.setGraphicsEffect(shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)
        self.hero = Illustration()
        outer.addWidget(self.hero)
        body = QVBoxLayout()
        body.setContentsMargins(16, 10, 8, 14)
        body.setSpacing(6)
        top = QHBoxLayout()
        top.setSpacing(8)
        self.kicker = label("", "caption")
        top.addWidget(self.kicker)
        self.dots = ProgressDots()
        top.addWidget(self.dots, 0, Qt.AlignmentFlag.AlignVCenter)
        top.addStretch(1)
        self.close_button = tool_button("cancel", close_tip, on_close)
        top.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignTop)
        body.addLayout(top)
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 8, 0)
        text.setSpacing(6)
        self.title = label("", "heading", wrap=True)
        text.addWidget(self.title)
        self.story = label("", "secondary", wrap=True)
        text.addWidget(self.story)
        self.task_box = QFrame()
        self.task_box.setObjectName("QuestTask")
        task_row = QHBoxLayout(self.task_box)
        task_row.setContentsMargins(10, 8, 10, 8)
        task_row.setSpacing(8)
        self.task_icon = QLabel()
        task_row.addWidget(self.task_icon, 0, Qt.AlignmentFlag.AlignTop)
        self.task = label("", None, wrap=True)
        task_row.addWidget(self.task, 1)
        text.addWidget(self.task_box)
        self.hint = label("", "caption", wrap=True)
        text.addWidget(self.hint)
        buttons = QHBoxLayout()
        buttons.setSpacing(4)
        self.primary = accent_button("")
        buttons.addWidget(self.primary)
        self.hint_button = link_button("", self._show_hint)
        buttons.addWidget(self.hint_button)
        buttons.addStretch(1)
        self.secondary = link_button("")
        buttons.addWidget(self.secondary)
        text.addSpacing(2)
        text.addLayout(buttons)
        body.addLayout(text)
        outer.addLayout(body)
        for w in (self.title, self.story, self.task, self.hint, self.kicker):
            w.setTextFormat(Qt.TextFormat.PlainText)
        self._primary_slot: Callable[[], None] | None = None
        self._secondary_slot: Callable[[], None] | None = None
        self.primary.clicked.connect(lambda: self._primary_slot and self._primary_slot())
        self.secondary.clicked.connect(lambda: self._secondary_slot and self._secondary_slot())
        for button in self.findChildren(QAbstractButton):
            button.setFocusPolicy(Qt.FocusPolicy.TabFocus)  # clicking never steals focus
        self.setFixedWidth(CARD_WIDTH)
        self.restyle()

    def restyle(self) -> None:
        t = theme.current()
        self.task_box.setStyleSheet(
            f"QFrame#QuestTask {{ background: {t.surface_alt}; border: 1px solid {t.border};"
            f" border-left: 3px solid {t.accent}; border-radius: 6px; }}"
        )
        self.task_icon.setPixmap(icons.icon("flag", t.accent, 16).pixmap(16, 16))

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.StyleChange:  # the theme changed
            self.restyle()

    def set_content(self, c: CardContent) -> None:
        self.hero.set_image(c.image, c.glyph)
        self.kicker.setText(c.kicker)
        self.dots.set_states(c.progress or [])
        self.title.setText(c.title)
        self.setAccessibleName(c.title)
        self.story.setText(c.story)
        self.story.setVisible(bool(c.story))
        self.task.setText(c.task)
        self.task_box.setVisible(bool(c.task))
        self.hint.setText(c.hint)
        self.hint.setVisible(False)
        self.hint_button.setText(c.hint_label)
        self.hint_button.setVisible(bool(c.hint and c.hint_label))
        for button, action, attr in (
            (self.primary, c.primary, "_primary_slot"),
            (self.secondary, c.secondary, "_secondary_slot"),
        ):
            button.setVisible(action is not None)
            button.setText(action[0] if action else "")
            setattr(self, attr, action[1] if action else None)
        self.restyle()
        self._fit()

    def _show_hint(self) -> None:
        self.hint.setVisible(True)
        self.hint_button.setVisible(False)
        self._fit()

    def _fit(self) -> None:
        self.layout().activate()
        self.setFixedHeight(self.layout().totalHeightForWidth(CARD_WIDTH))
        self.reposition()

    def reposition(self, avoid: QRect | None = None) -> None:
        """Sit in the trailing lower corner unless that covers *avoid* (the target)."""
        if avoid is not None:
            self.avoid = avoid
        w = self.window
        bar = w.statusBar()
        bottom = w.height() - (bar.height() if bar.isVisible() else 0) - MARGIN
        size = QSize(self.width(), self.height())
        left_edge, right_edge = 0, w.width()
        nav = getattr(w, "nav", None)
        if nav is not None and nav.isVisible():
            rail = QRect(nav.mapTo(w, QPoint(0, 0)), nav.size())
            if rail.center().x() < w.width() / 2:
                left_edge = rail.right() + 1
            else:
                right_edge = rail.left()
        others = [
            f.geometry()
            for f in w.findChildren(QFrame, "Toast", Qt.FindChildOption.FindDirectChildrenOnly)
            if f is not self and f.isVisible()
        ]

        def place(x: int) -> QRect:
            rect = QRect(QPoint(x, bottom - size.height()), size)
            for other in others:  # stack above another notice in the same corner
                if rect.intersects(other):
                    rect.moveBottom(other.top() - 8)
            top = w.menuBar().height() + 8 if w.menuBar().isVisible() else 8
            if rect.top() < top:
                rect.moveTop(top)
            return rect

        trailing = place(right_edge - size.width() - MARGIN)
        leading = place(left_edge + MARGIN)
        candidates = [trailing, leading]
        if w.layoutDirection() == Qt.LayoutDirection.RightToLeft:
            candidates.reverse()
        if self.avoid is not None:

            def overlap(rect: QRect) -> int:
                common = rect.intersected(self.avoid)
                return common.width() * common.height() if not common.isEmpty() else 0

            candidates.sort(key=overlap)  # stable: the preferred corner wins a tie
        self.move(candidates[0].topLeft())
        self.raise_()


class Spotlight(QWidget):
    """A click-through overlay outlining the control the current task needs."""

    PULSE_MS = 1300
    PULSES = 4

    def __init__(self, window: QMainWindow):
        super().__init__(window)
        self.window = window
        self.resolve: Callable[[], Target | None] = lambda: None
        self.rect_now: QRect | None = None
        self.clock = QElapsedTimer()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.timer = QTimer(self, interval=33, timeout=self.tick)
        self.setGeometry(window.rect())
        self.hide()

    def point_at(self, resolve: Callable[[], Target | None]) -> None:
        self.resolve = resolve
        self.setGeometry(self.window.rect())
        self.show()
        self.raise_()
        self.clock.start()
        self.timer.setInterval(33)
        self.timer.start()
        self.tick()

    def stop(self) -> None:
        self.timer.stop()
        self.resolve = lambda: None
        self._invalidate(self.rect_now)
        self.rect_now = None
        self.hide()

    def pulsing(self) -> bool:
        return self.clock.isValid() and self.clock.elapsed() < self.PULSE_MS * self.PULSES

    def tick(self) -> None:
        rect = target_rect(self.window, self.resolve())  # the overlay covers the window
        if rect != self.rect_now:
            self._invalidate(self.rect_now)
            self.rect_now = rect
            self.target_moved(rect)
        self._invalidate(rect)
        if not self.pulsing() and self.timer.interval() != 250:
            self.timer.setInterval(250)  # settled: only follow the target around

    def target_moved(self, rect: QRect | None) -> None:
        """Called when the outlined area changes; the quest moves its card out of the way."""

    def _invalidate(self, rect: QRect | None) -> None:
        if rect is None:
            return
        outer = rect.adjusted(-20, -20, 20, 20)
        inner = rect.adjusted(6, 6, -6, -6)
        region = QRegion(outer)
        if inner.isValid() and not inner.isEmpty():
            region = region.subtracted(QRegion(inner))
        self.update(region)

    def paintEvent(self, event) -> None:  # noqa: N802
        if self.rect_now is None:
            return
        t = theme.current()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        ring = QRectF(self.rect_now).adjusted(-4, -4, 4, 4)
        accent = t.q("accent")
        if self.pulsing():
            phase = (self.clock.elapsed() % self.PULSE_MS) / self.PULSE_MS
            ease = 1 - (1 - phase) ** 3
            glow = QColor(accent)
            glow.setAlphaF(0.55 * (1 - ease))
            painter.setPen(QPen(glow, 2 + 4 * (1 - ease)))
            grow = 12 * ease
            painter.drawRoundedRect(ring.adjusted(-grow, -grow, grow, grow), 8 + grow, 8 + grow)
        halo = QColor(accent)
        halo.setAlphaF(0.22)
        painter.setPen(QPen(halo, 6))
        painter.drawRoundedRect(ring, 8, 8)
        painter.setPen(QPen(accent, 2))
        painter.drawRoundedRect(ring, 8, 8)
