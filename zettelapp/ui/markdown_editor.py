"""Markdown editing: syntax highlighting, [[ completion, image paste and drop."""

from __future__ import annotations

import re
from collections.abc import Callable

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QStringListModel, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import QCompleter, QPlainTextEdit

from zettelapp.ui import theme

_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")


def _fmt(
    color: str | None = None,
    bold: bool = False,
    italic: bool = False,
    size: float | None = None,
    background: str | None = None,
    underline: bool = False,
) -> QTextCharFormat:
    f = QTextCharFormat()
    if color:
        f.setForeground(QColor(color) if color.startswith("#") else theme.current().q(color))
    if bold:
        f.setFontWeight(QFont.Weight.DemiBold)
    if italic:
        f.setFontItalic(True)
    if size:
        f.setFontPointSize(size)
    if background:
        f.setBackground(theme.current().q(background))
    if underline:
        f.setFontUnderline(True)
    return f


class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, document, base_size: float):
        super().__init__(document)
        self.base_size = base_size
        self.rebuild()

    def rebuild(self) -> None:
        s = self.base_size
        self.rules = [
            (re.compile(r"^#{1}\s.*$"), _fmt("text", bold=True, size=s * 1.6)),
            (re.compile(r"^#{2}\s.*$"), _fmt("text", bold=True, size=s * 1.35)),
            (re.compile(r"^#{3,6}\s.*$"), _fmt("text", bold=True, size=s * 1.15)),
            (re.compile(r"^\s*(?:[-*+]|\d+[.)])\s"), _fmt("accent", bold=True)),
            (re.compile(r"^>.*$"), _fmt("text_secondary", italic=True)),
            (re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__"), _fmt(bold=True)),
            (
                re.compile(r"(?<![*\w])\*[^*\n]+\*(?!\*)|(?<![_\w])_[^_\n]+_(?!_)"),
                _fmt(italic=True),
            ),
            (re.compile(r"`[^`\n]+`"), _fmt("text_secondary", background="hover")),
            (re.compile(r"!?\[[^\]\n]*\]\([^)\n]*\)"), _fmt("accent")),
            (
                re.compile(r"(?:[A-Za-z][\w-]{0,30}::[ \t]*)?\[\[[^\]\n]+\]\]"),
                _fmt("accent", underline=True),
            ),
            (re.compile(r"\{\{c\d+::.*?\}\}"), _fmt(bold=True, background="accent_subtle")),
            (re.compile(r"^\s*(?:Q|A|Question|Answer)\s*:", re.I), _fmt("accent", bold=True)),
            (re.compile(r"(?<![\w#&/])#[^\W\d_][\w/-]*"), _fmt("text_secondary", bold=True)),
        ]
        self.code_format = _fmt("text_secondary", background="hover")
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:  # noqa: N802 - Qt API
        in_code = self.previousBlockState() == 1
        if text.lstrip().startswith("```"):
            self.setFormat(0, len(text), self.code_format)
            self.setCurrentBlockState(0 if in_code else 1)
            return
        if in_code:
            self.setFormat(0, len(text), self.code_format)
            self.setCurrentBlockState(1)
            return
        self.setCurrentBlockState(0)
        for pattern, fmt in self.rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


class MarkdownEditor(QPlainTextEdit):
    """Plain-text Markdown editor.

    *store_image* receives (bytes, original name) and returns an asset name; it
    validates the data, so pasted or dropped files can never inject anything
    but a real raster image into the vault.
    """

    imageError = Signal(str)

    def __init__(self, store_image: Callable[[bytes, str], str], parent=None):
        super().__init__(parent)
        self.setObjectName("BodyEdit")
        self.store_image = store_image
        self.setAccessibleName("Note text")
        self.setPlaceholderText(
            "Start writing… Use [[ to link a note, #tags, Q:/A: or {{c1::cloze}} for flashcards."
        )
        self.setTabChangesFocus(False)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setViewportMargins(0, 0, 0, 0)
        self.document().setDocumentMargin(4)
        size = 11.0
        font = theme.ui_font(size)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.highlighter = MarkdownHighlighter(self.document(), size)
        self.titles_model = QStringListModel(self)
        self.completer = QCompleter(self.titles_model, self)
        self.completer.setWidget(self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.activated.connect(self._insert_completion)
        self.textChanged.connect(self._maybe_complete)

    def set_font_size(self, size: float) -> None:
        self.setFont(theme.ui_font(size))
        self.highlighter.base_size = size
        self.highlighter.rebuild()

    def set_titles(self, titles: list[str]) -> None:
        self.titles_model.setStringList(sorted({t for t in titles if t.strip()}, key=str.casefold))

    # --- [[ completion ------------------------------------------------------

    def _link_prefix(self) -> str | None:
        cursor = self.textCursor()
        block = cursor.block().text()[: cursor.positionInBlock()]
        start = block.rfind("[[")
        if start < 0 or "]]" in block[start:]:
            return None
        prefix = block[start + 2 :]
        return prefix if len(prefix) <= 80 and "\n" not in prefix else None

    def _maybe_complete(self) -> None:
        prefix = self._link_prefix()
        popup = self.completer.popup()
        if prefix is None:
            popup.hide()
            return
        self.completer.setCompletionPrefix(prefix)
        if self.completer.completionCount() == 0:
            popup.hide()
            return
        rect = self.cursorRect()
        rect.setWidth(max(280, popup.sizeHintForColumn(0) + 30))
        self.completer.complete(rect)

    def _insert_completion(self, title: str) -> None:
        prefix = self._link_prefix() or ""
        cursor = self.textCursor()
        cursor.movePosition(
            QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, len(prefix)
        )
        cursor.insertText(title + "]]")
        self.setTextCursor(cursor)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if self.completer.popup().isVisible() and event.key() in (
            Qt.Key.Key_Enter,
            Qt.Key.Key_Return,
            Qt.Key.Key_Escape,
            Qt.Key.Key_Tab,
        ):
            event.ignore()
            return
        if event.matches(QKeySequence.StandardKey.Bold):
            self.wrap_selection("**")
            return
        if event.matches(QKeySequence.StandardKey.Italic):
            self.wrap_selection("*")
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not event.modifiers():
            self._continue_list()
            return
        super().keyPressEvent(event)

    def _continue_list(self) -> None:
        cursor = self.textCursor()
        line = cursor.block().text()
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if not m:
            cursor.insertText("\n")
            return
        if not m.group(3).strip():  # empty item ends the list
            cursor.movePosition(
                QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor
            )
            cursor.removeSelectedText()
            cursor.insertText("\n")
            return
        marker = m.group(2)
        if marker[0].isdigit():
            marker = f"{int(marker[:-1]) + 1}{marker[-1]}"
        cursor.insertText(f"\n{m.group(1)}{marker} ")

    # --- formatting helpers ---------------------------------------------------

    def wrap_selection(self, before: str, after: str | None = None) -> None:
        after = before if after is None else after
        cursor = self.textCursor()
        text = cursor.selectedText()
        cursor.insertText(f"{before}{text}{after}")
        if not text:
            cursor.movePosition(QTextCursor.MoveOperation.Left, n=len(after))
            self.setTextCursor(cursor)

    def prefix_lines(self, prefix: str) -> None:
        cursor = self.textCursor()
        start, end = sorted((cursor.selectionStart(), cursor.selectionEnd()))
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.beginEditBlock()
        while True:
            cursor.insertText(prefix)
            end += len(prefix)
            if (
                not cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
                or cursor.position() > end
            ):
                break
        cursor.endEditBlock()

    def insert_block(self, text: str) -> None:
        cursor = self.textCursor()
        if cursor.positionInBlock() > 0:
            text = "\n" + text
        cursor.insertText(text)
        self.setTextCursor(cursor)
        self.setFocus()

    # --- images -----------------------------------------------------------------

    def canInsertFromMimeData(self, source) -> bool:  # noqa: N802
        return (
            source.hasImage() or self._image_urls(source) or super().canInsertFromMimeData(source)
        )

    def insertFromMimeData(self, source) -> None:  # noqa: N802
        urls = self._image_urls(source)
        if urls:
            for path in urls:
                self._insert_image_file(path)
            return
        if source.hasImage():
            image = source.imageData()
            data = QByteArray()
            buffer = QBuffer(data)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, "PNG")
            self._insert_image_bytes(bytes(data), "pasted.png")
            return
        super().insertFromMimeData(source)

    @staticmethod
    def _image_urls(source) -> list[str]:
        if not source.hasUrls():
            return []
        return [
            u.toLocalFile()
            for u in source.urls()
            if u.isLocalFile() and u.toLocalFile().lower().endswith(_IMAGE_SUFFIXES)
        ]

    def _insert_image_file(self, path: str) -> None:
        try:
            with open(path, "rb") as fh:
                data = fh.read(25 * 1024 * 1024 + 1)
        except OSError as exc:
            self.imageError.emit(str(exc))
            return
        self._insert_image_bytes(data, path.replace("\\", "/").rsplit("/", 1)[-1])

    def _insert_image_bytes(self, data: bytes, name: str) -> None:
        try:
            asset = self.store_image(data, name)
        except ValueError as exc:  # UnsafeInputError is a ValueError
            self.imageError.emit(str(exc))
            return
        alt = re.sub(r"[\[\]]", "", name.rsplit(".", 1)[0])[:60]
        self.insert_block(f"![{alt}](asset:{asset})\n")
