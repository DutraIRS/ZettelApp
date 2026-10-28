"""Small reusable widgets."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QComboBox,
    QCompleter,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetItem,
)

from zettelapp.core.textutil import normalize_tag
from zettelapp.ui import icons, theme


class ToggleSwitch(QAbstractButton):
    """A Windows 11 style on/off switch (checkable; Space toggles it)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(40, 22)

    def paintEvent(self, event) -> None:  # noqa: N802
        t = theme.current()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = 18.0
        track = QRectF(2, (self.height() - h) / 2, h * 2, h)
        on = self.isChecked()
        if self.hasFocus():
            painter.setPen(QPen(t.q("text"), 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(track.adjusted(-2, -2, 2, 2), h / 2 + 2, h / 2 + 2)
        painter.setPen(Qt.PenStyle.NoPen if on else QPen(t.q("text_secondary"), 1))
        painter.setBrush(t.q("accent") if on else Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(track.adjusted(0.5, 0.5, -0.5, -0.5), h / 2, h / 2)
        radius = (5.5 if self.underMouse() else 4.5) if self.isEnabled() else 4.0
        x = track.right() - h / 2 if on else track.left() + h / 2
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(t.q("on_accent") if on else t.q("text_secondary"))
        painter.drawEllipse(QPointF(x, track.center().y()), radius, radius)


def label(text: str = "", role: str | None = None, wrap: bool = False) -> QLabel:
    w = QLabel(text)
    if role:
        w.setProperty("role", role)
    w.setWordWrap(wrap)
    return w


def tool_button(
    icon_name: str,
    tooltip: str,
    on_click: Callable | None = None,
    checkable: bool = False,
    text: str = "",
) -> QToolButton:
    b = QToolButton()
    b.setIcon(icons.icon(icon_name))
    b.setIconSize(QSize(16, 16))
    b.setToolTip(tooltip)
    b.setAccessibleName(tooltip.split(" (")[0])
    b.setCheckable(checkable)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if text:
        b.setText(text)
        b.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
    if on_click:
        b.clicked.connect(on_click)
    return b


def accent_button(
    text: str, on_click: Callable | None = None, icon_name: str | None = None
) -> QPushButton:
    b = QPushButton(text)
    b.setProperty("accent", True)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if icon_name:
        b.setIcon(icons.icon(icon_name, theme.current().on_accent))
    if on_click:
        b.clicked.connect(on_click)
    return b


def link_button(text: str, on_click: Callable | None = None) -> QPushButton:
    b = QPushButton(text)
    b.setProperty("flat", True)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if on_click:
        b.clicked.connect(on_click)
    return b


class Card(QFrame):
    def __init__(self, parent: QWidget | None = None, margins: int = 16, spacing: int = 10):
        super().__init__(parent)
        self.setObjectName("Card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(margins, margins, margins, margins)
        self.body.setSpacing(spacing)


class FlowLayout(QLayout):
    """Lays children out left-to-right, wrapping like text."""

    def __init__(self, parent: QWidget | None = None, spacing: int = 6):
        super().__init__(parent)
        self._items: list = []
        self._spacing = spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item) -> None:  # noqa: N802 - Qt API
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):  # noqa: N802
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index: int):  # noqa: N802
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def insertWidget(self, index: int, widget: QWidget) -> None:  # noqa: N802
        self.addChildWidget(widget)
        self._items.insert(index, QWidgetItem(widget))
        self.invalidate()

    def expandingDirections(self):  # noqa: N802
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:  # noqa: N802
        return True

    def heightForWidth(self, width: int) -> int:  # noqa: N802
        return self._layout(QRect(0, 0, width, 0), dry=True)

    def setGeometry(self, rect: QRect) -> None:  # noqa: N802
        super().setGeometry(rect)
        self._layout(rect, dry=False)

    def sizeHint(self) -> QSize:  # noqa: N802
        return self.minimumSize()

    def minimumSize(self) -> QSize:  # noqa: N802
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        return size

    def _layout(self, rect: QRect, dry: bool) -> int:
        x, y, line = rect.x(), rect.y(), 0
        for item in self._items:
            hint = item.sizeHint()
            if x + hint.width() > rect.right() and line > 0:
                x, y = rect.x(), y + line + self._spacing
                line = 0
            if not dry:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + self._spacing
            line = max(line, hint.height())
        return y + line - rect.y()


class TagEditor(QWidget):
    """Tag chips plus an inline field with completion. Emits the new tag list.

    Tags written as #tag in the note text are shown as outlined chips that can't be
    removed here: they come and go with the text.
    """

    tagsChanged = Signal(list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._tags: list[str] = []
        self._inline: list[str] = []
        self.flow = FlowLayout(self)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Add tag")
        self.input.setAccessibleName("Add tag")
        self.input.setFixedWidth(120)
        self.input.setStyleSheet(
            "QLineEdit { border: none; background: transparent; padding: 2px 4px; }"
        )
        self.input.returnPressed.connect(self._commit)
        self.completer = QCompleter([])
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.input.setCompleter(self.completer)
        self.completer.activated.connect(lambda _: QTimer.singleShot(0, self._commit))
        self.flow.addWidget(self.input)

    def set_known_tags(self, tags: list[str]) -> None:
        self.completer.model().setStringList(tags)  # QCompleter(list) owns a QStringListModel

    def set_tags(self, tags: list[str], inline: list[str] | None = None) -> None:
        self._tags = list(tags)
        self._inline = [t for t in inline or [] if t not in self._tags]
        self._rebuild()

    def set_inline_tags(self, inline: list[str]) -> None:
        inline = [t for t in inline if t not in self._tags]
        if inline != self._inline:
            self._inline = inline
            self._rebuild()

    def tags(self) -> list[str]:
        """The tags added here (not the ones written in the text)."""
        return list(self._tags)

    def _rebuild(self) -> None:
        while self.flow.count() > 1:
            item = self.flow.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, tag in enumerate(self._tags):
            chip = QToolButton()
            chip.setObjectName("Chip")
            chip.setText(f"#{tag}  ✕")
            chip.setToolTip(f"Remove tag “{tag}”")
            chip.setAccessibleName(f"Tag {tag}, press to remove")
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.clicked.connect(lambda _=False, t=tag: self._remove(t))
            self.flow.insertWidget(i, chip)
        for i, tag in enumerate(self._inline, start=len(self._tags)):
            chip = QToolButton()
            chip.setObjectName("Chip")
            chip.setProperty("inline", True)
            chip.setText(f"#{tag}")
            chip.setToolTip(f"Written in the note text. Delete “#{tag}” there to remove this tag.")
            chip.setAccessibleName(f"Tag {tag}, from the note text")
            chip.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.flow.insertWidget(i, chip)
        self.updateGeometry()

    def _commit(self) -> None:
        tag = normalize_tag(self.input.text())
        self.input.clear()
        if tag and tag not in self._tags:
            self._tags.append(tag)
            self._inline = [t for t in self._inline if t != tag]
            self._rebuild()
            self.tagsChanged.emit(self.tags())

    def _remove(self, tag: str) -> None:
        if tag in self._tags:
            self._tags.remove(tag)
            self._rebuild()
            self.tagsChanged.emit(self.tags())


class SearchBox(QLineEdit):
    def __init__(self, placeholder: str = "Search", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Search")
        self.setPlaceholderText(placeholder)
        self.setAccessibleName(placeholder)
        self.setClearButtonEnabled(True)
        self.addAction(
            QAction(icons.icon("search", theme.current().text_muted, 16), "", self),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.setStyleSheet("QLineEdit#Search { padding-left: 4px; }")


class ElidedLabel(QLabel):
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        painter.setPen(self.palette().color(self.foregroundRole()))
        text = metrics.elidedText(self.text(), Qt.TextElideMode.ElideRight, self.width())
        painter.drawText(self.rect(), int(self.alignment()), text)


class InfoBar(QFrame):
    """A dismissible message strip (the Windows "InfoBar" pattern)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setVisible(False)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 6, 6, 6)
        self.icon = QLabel()
        self.text = QLabel()
        self.text.setWordWrap(True)
        self.action = link_button("")
        self.close_button = tool_button("cancel", "Dismiss", self.hide)
        row.addWidget(self.icon)
        row.addWidget(self.text, 1)
        row.addWidget(self.action)
        row.addWidget(self.close_button)
        self._timer = QTimer(self, singleShot=True, timeout=self.hide)
        self._callback: Callable | None = None
        self.action.clicked.connect(self._run)

    def show_message(
        self,
        text: str,
        kind: str = "info",
        action: str | None = None,
        callback: Callable | None = None,
        timeout_ms: int = 8000,
    ) -> None:
        t = theme.current()
        color = {"info": t.accent, "success": t.success, "error": t.danger}.get(kind, t.accent)
        self.setStyleSheet(
            f"InfoBar {{ background: {t.surface}; border: 1px solid {t.border};"
            f" border-left: 4px solid {color}; border-radius: 6px; }}"
        )
        glyph = {"info": "info", "success": "check", "error": "info"}[kind]
        self.icon.setPixmap(icons.icon(glyph, color).pixmap(18, 18))
        self.text.setText(text)
        self.action.setVisible(bool(action))
        self.action.setText(action or "")
        self._callback = callback
        self.show()
        self._timer.stop()
        if timeout_ms:
            self._timer.start(timeout_ms)

    def _run(self) -> None:
        if self._callback:
            self._callback()
        self.hide()


class ScopePicker(QWidget):
    """Choose a set of notes: the whole vault, a note's neighbourhood or a tag."""

    changed = Signal()

    def __init__(self, parent: QWidget | None = None, allow_current: bool = True):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        self.mode = QComboBox()
        self.mode.setAccessibleName("Scope")
        self.mode.addItem("Entire collection", "all")
        if allow_current:
            self.mode.addItem("Current note and linked notes", "subgraph")
        self.mode.addItem("Notes with tag", "tag")
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 6)
        self.depth_spin.setValue(2)
        self.depth_spin.setPrefix("Depth ")
        self.depth_spin.setToolTip("How many links away from the current note to include")
        self.tag = QComboBox()
        self.tag.setAccessibleName("Tag")
        self.tag.setMinimumWidth(140)
        row.addWidget(self.mode)
        row.addWidget(self.depth_spin)
        row.addWidget(self.tag)
        row.addStretch(1)
        self.mode.currentIndexChanged.connect(self._update)
        self.depth_spin.valueChanged.connect(self.changed)
        self.tag.currentIndexChanged.connect(self.changed)
        self._update()

    def set_tags(self, tags: list[tuple[str, int]]) -> None:
        current = self.tag.currentData()
        self.tag.blockSignals(True)
        self.tag.clear()
        for name, count in tags:
            self.tag.addItem(f"#{name} ({count})", name)
        index = self.tag.findData(current)
        self.tag.setCurrentIndex(max(0, index))
        self.tag.blockSignals(False)

    def set_mode(self, mode: str) -> None:
        index = self.mode.findData(mode)
        if index >= 0:
            self.mode.setCurrentIndex(index)

    def _update(self) -> None:
        mode = self.mode.currentData()
        self.depth_spin.setVisible(mode == "subgraph")
        self.tag.setVisible(mode == "tag")
        self.changed.emit()

    def value(self) -> tuple[str, int, str | None]:
        return self.mode.currentData(), self.depth_spin.value(), self.tag.currentData()
