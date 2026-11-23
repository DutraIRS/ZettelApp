"""Find and replace inside the open note (Ctrl+F / Ctrl+H in the note text)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from zettelapp.i18n import _
from zettelapp.ui import theme
from zettelapp.ui.widgets import SearchBox, label, tool_button

MAX_HIGHLIGHTS = 2000  # beyond this, matches are counted but not all painted


class FindBar(QWidget):
    """A slim bar above the note text: find with every match highlighted, step through them,
    and replace one or all. Enter goes to the next match, Shift+Enter to the previous one,
    Esc closes the bar."""

    def __init__(self, editor: QPlainTextEdit, parent: QWidget | None = None):
        super().__init__(parent)
        self.editor = editor
        self.setObjectName("FindBar")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 4)
        outer.setSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(4)
        self.find = SearchBox(_("Find in note"))
        self.find.textChanged.connect(self._query_changed)
        self.find.returnPressed.connect(self.next)
        row.addWidget(self.find, 1)
        self.count = label("", "caption")
        self.count.setMinimumWidth(70)
        self.count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.count)
        self.case = QToolButton()
        self.case.setText("Aa")
        self.case.setCheckable(True)
        self.case.setToolTip(_("Match case"))
        self.case.setAccessibleName(_("Match case"))
        self.case.toggled.connect(lambda _on: self._query_changed())
        row.addWidget(self.case)
        previous = tool_button("chevron_up", _("Previous match (Shift+Enter)"), self.previous)
        row.addWidget(previous)
        following = tool_button("chevron_down", _("Next match (Enter)"), self.next)
        row.addWidget(following)
        self.replace_toggle = tool_button(
            "sync", _("Replace (Ctrl+H)"), lambda: self._show_replace(not self._replacing), True
        )
        row.addWidget(self.replace_toggle)
        close = tool_button("cancel", _("Close (Esc)"), self.close_bar)
        row.addWidget(close)
        outer.addLayout(row)

        self.replace_row = QWidget()
        replace = QHBoxLayout(self.replace_row)
        replace.setContentsMargins(0, 0, 0, 0)
        replace.setSpacing(4)
        self.replacement = QLineEdit()
        self.replacement.setPlaceholderText(_("Replace with"))
        self.replacement.setAccessibleName(_("Replace with"))
        self.replacement.setClearButtonEnabled(True)
        self.replacement.returnPressed.connect(self.replace_one)
        replace.addWidget(self.replacement, 1)
        self.replace_button = QPushButton(_("Replace"))
        self.replace_button.clicked.connect(self.replace_one)
        replace.addWidget(self.replace_button)
        self.replace_all_button = QPushButton(_("Replace all"))
        self.replace_all_button.clicked.connect(self.replace_all)
        replace.addWidget(self.replace_all_button)
        outer.addWidget(self.replace_row)
        # Tab goes from the search straight to its replacement, as in other editors.
        chain = (
            self.find,
            self.replacement,
            self.replace_button,
            self.replace_all_button,
            self.case,
            previous,
            following,
            self.replace_toggle,
            close,
        )
        for first, second in zip(chain, chain[1:], strict=False):
            QWidget.setTabOrder(first, second)

        for widget in (self.find, self.replacement):
            QShortcut(
                QKeySequence(Qt.Key.Key_Escape),
                widget,
                self.close_bar,
                context=Qt.ShortcutContext.WidgetShortcut,
            )
        QShortcut(
            QKeySequence("Shift+Return"),
            self.find,
            self.previous,
            context=Qt.ShortcutContext.WidgetShortcut,
        )
        self._replacing = False
        self._show_replace(False)
        self.editor.textChanged.connect(self._text_changed)
        self.hide()

    # --- opening and closing ---------------------------------------------------

    def open(self, replace: bool = False) -> None:
        """Show the bar with the selected word (if any) as the search, and focus it."""
        selected = self.editor.textCursor().selectedText()
        if selected and " " not in selected:  # a selection within one line
            self.find.setText(selected)
        self._show_replace(replace or self._replacing)
        self.show()
        field = self.replacement if replace and self.find.text() else self.find
        field.setFocus()
        field.selectAll()
        self._query_changed()

    def close_bar(self) -> None:
        self.hide()
        self._highlight([])
        self.editor.setFocus()

    def _show_replace(self, on: bool) -> None:
        self._replacing = on
        self.replace_row.setVisible(on)
        self.replace_toggle.setChecked(on)
        if on and self.isVisible():
            self.replacement.setFocus()

    # --- finding ----------------------------------------------------------------

    def _flags(self, backward: bool = False) -> QTextDocument.FindFlag:
        flags = QTextDocument.FindFlag(0)
        if self.case.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward
        return flags

    def matches(self) -> list[QTextCursor]:
        """Every match in the note, in order."""
        text = self.find.text()
        doc = self.editor.document()
        found: list[QTextCursor] = []
        if not text:
            return found
        cursor = doc.find(text, 0, self._flags())
        while not cursor.isNull():
            found.append(cursor)
            if cursor.selectionEnd() == cursor.selectionStart():
                break
            cursor = doc.find(text, cursor.selectionEnd(), self._flags())
        return found

    def _is_match(self, cursor: QTextCursor) -> bool:
        text, selected = self.find.text(), cursor.selectedText()
        if not text or not selected:
            return False
        return selected == text if self.case.isChecked() else selected.lower() == text.lower()

    def _query_changed(self, *_args) -> None:
        if not self.isVisible():
            return
        cursor = self.editor.textCursor()
        start = min(cursor.selectionStart(), cursor.position())
        found = self.editor.document().find(self.find.text(), start, self._flags())
        if self.find.text() and found.isNull():
            found = self.editor.document().find(self.find.text(), 0, self._flags())
        if not found.isNull():
            self.editor.setTextCursor(found)
        self._refresh()

    def _go(self, backward: bool) -> None:
        text = self.find.text()
        if not text:
            return
        doc, cursor = self.editor.document(), self.editor.textCursor()
        found = doc.find(text, cursor, self._flags(backward))
        if found.isNull():  # wrap around
            edge = QTextCursor(doc)
            edge.movePosition(
                QTextCursor.MoveOperation.End if backward else QTextCursor.MoveOperation.Start
            )
            found = doc.find(text, edge, self._flags(backward))
        if not found.isNull():
            self.editor.setTextCursor(found)
            self.editor.ensureCursorVisible()
        self._refresh()

    def next(self) -> None:
        self._go(False)

    def previous(self) -> None:
        self._go(True)

    # --- replacing --------------------------------------------------------------

    def replace_one(self) -> None:
        cursor = self.editor.textCursor()
        if self._is_match(cursor):
            cursor.insertText(self.replacement.text())
            self.editor.setTextCursor(cursor)
        self.next()

    def replace_all(self) -> int:
        found = self.matches()
        if not found:
            return 0
        edit = QTextCursor(self.editor.document())
        edit.beginEditBlock()  # one undo takes them all back
        for cursor in reversed(found):  # from the end, so earlier positions stay valid
            cursor.insertText(self.replacement.text())
        edit.endEditBlock()
        self._refresh()
        self.count.setText(_("{n} replaced").format(n=len(found)))
        return len(found)

    # --- highlighting -----------------------------------------------------------

    def _text_changed(self) -> None:
        if self.isVisible():
            self._refresh()

    def _refresh(self) -> None:
        found = self.matches() if self.isVisible() else []
        current = self.editor.textCursor()
        index = next(
            (
                i
                for i, c in enumerate(found)
                if (c.selectionStart(), c.selectionEnd())
                == (current.selectionStart(), current.selectionEnd())
            ),
            None,
        )
        if not self.find.text():
            self.count.setText("")
        elif not found:
            self.count.setText(_("No results"))
        elif index is None:
            self.count.setText(str(len(found)))
        else:
            self.count.setText(_("{i} of {n}").format(i=index + 1, n=len(found)))
        self._highlight(found[:MAX_HIGHLIGHTS])

    def _highlight(self, found: list[QTextCursor]) -> None:
        colour = QColor(theme.current().highlight)
        colour.setAlphaF(0.28)
        selections = []
        for cursor in found:
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format.setBackground(colour)
            selections.append(selection)
        set_layer = getattr(self.editor, "set_selection_layer", None)
        if set_layer is not None:
            set_layer("find", selections)
        else:
            self.editor.setExtraSelections(selections)
