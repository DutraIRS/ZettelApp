"""Markdown editing: syntax highlighting, [[ completion, Ctrl+click links, image paste and drop."""

from __future__ import annotations

import ntpath
import re
from collections.abc import Callable

from PySide6.QtCore import (
    QBuffer,
    QByteArray,
    QEvent,
    QIODevice,
    QPoint,
    QStringListModel,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QCursor,
    QFont,
    QKeySequence,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import QCompleter, QPlainTextEdit, QToolTip

from zettelapp.core.security import file_url, local_file_path
from zettelapp.core.textutil import (
    HASHTAG_RE,
    MATH_RE,
    emphasis_spans,
    find_wikilinks,
    fold,
    normalize_tag,
)
from zettelapp.i18n import _
from zettelapp.ui import theme

_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
MAX_COMPLETIONS = 100
_ASSET_IMAGE_RE = re.compile(r"!\[[^\]\n]*\]\(asset:([^)\s]+)\)")


def referenced_assets(text: str) -> set[str]:
    """Every asset name a ![image](asset:…) in *text* points at."""
    return set(_ASSET_IMAGE_RE.findall(text))


# Quote, list, checklist, heading and flashcard marks, which bold and italics leave outside.
_LINE_MARKS_RE = re.compile(
    r"[ \t]*(?:>[ \t]?)*"
    r"(?:(?:[-*+]|\d+[.)])[ \t]+(?:\[[ xX]\][ \t]+)?|#{1,6}[ \t]+)?"
    r"(?:(?:Q|A|Question|Answer)[ \t]*:[ \t]*)?",
    re.I,
)


def _emphasis_around(text: str, a: int, b: int, size: int) -> tuple[int, int] | None:
    """If text[a:b] is already bold (*size* 2) or italic (1), where its text starts and ends
    inside the markers; they may sit outside the selection, inside it or across its edges."""
    spans = emphasis_spans(text)
    selected = text[a:b]
    for ch in "*_":
        out_left = a - len(text[:a].rstrip(ch))
        in_left = len(selected) - len(selected.lstrip(ch))
        in_right = len(selected) - len(selected.rstrip(ch))
        out_right = len(text[b:]) - len(text[b:].lstrip(ch))
        start, end = a + in_left, b - in_right
        if start >= end:
            continue
        count = min(out_left + in_left, in_right + out_right)
        if count >= 2 if size == 2 else count % 2 == 1:  # ** is bold, * italic, *** both
            if any(a - out_left <= s < start and end < e <= b + out_right for s, e, _b in spans):
                return start, end
    return None


_MD_LINK_RE = re.compile(r"(?<!!)\[[^\]\n]*\]\((?:<([^>\n]+)>|([^)\s]+))(?:\s+\"[^\"\n]*\")?\)")
_URL_RE = re.compile(r"\b(?:https?://|mailto:|file:///)[^\s<>()\[\]]*[^\s<>()\[\].,;:!?'\"]")
_PATH_RE = re.compile(r"(?<![\w/\\])[A-Za-z]:\\[^\s<>\"|?*]*[^\s<>\"|?*.,;:!']")  # C:\no\spaces


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
        f.setFontFamilies(theme.ITALIC_FONTS)
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
            (re.compile(r"^\s*(?:[-*+]|\d+[.)])\s(?:\[[ xX]\]\s)?"), _fmt("accent", bold=True)),
            (MATH_RE, _fmt("accent")),
            (re.compile(r"^>.*$"), _fmt("text_secondary", italic=True)),
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
        self._emphasis(text)

    def _emphasis(self, text: str) -> None:
        """Bold and italics are added to what the rules above set, so they nest
        (*a **b** c*) and also show in headings, quotes and links."""
        style = [0] * len(text)  # 1 bold, 2 italic
        for start, end, bold in emphasis_spans(text):
            for i in range(start, end):
                style[i] |= 1 if bold else 2
        i = 0
        while i < len(text):
            if not style[i]:
                i += 1
                continue
            base, j = self.format(i), i + 1
            while j < len(text) and style[j] == style[i] and self.format(j) == base:
                j += 1
            fmt = QTextCharFormat(base)
            if style[i] & 1 and fmt.fontWeight() < QFont.Weight.DemiBold.value:
                fmt.setFontWeight(QFont.Weight.DemiBold)
            if style[i] & 2:
                fmt.setFontItalic(True)
                fmt.setFontFamilies(theme.ITALIC_FONTS)
            self.setFormat(i, j - i, fmt)
            i = j


class MarkdownEditor(QPlainTextEdit):
    """Plain-text Markdown editor.

    *store_image* receives (bytes, original name) and returns an asset name; it
    validates the data, so pasted or dropped files can never inject anything
    but a real raster image into the vault.

    Ctrl+click follows a [[note link]], a web or Zotero link or a #tag, like links in
    Word or VS Code; a plain click keeps placing the caret so links stay editable.
    *resolve_note* maps a link target to a note id (None when there is no such note).
    """

    imageError = Signal(str)
    fileLinkError = Signal(str)
    linkActivated = Signal(str, str)  # kind ("note", "url" or "tag"), target

    def __init__(self, store_image: Callable[[bytes, str], str], parent=None):
        super().__init__(parent)
        self.setObjectName("BodyEdit")
        self.store_image = store_image
        self.resolve_note: Callable[[str], str | None] | None = None
        # Given an asset name, the (text, callback) actions to offer when right-clicking an image.
        self.image_actions: Callable[[str], list[tuple[str, Callable[[], None]]]] | None = None
        self._pressed_link: tuple[str, str] | None = None
        self.viewport().setMouseTracking(True)
        self.setAccessibleName(_("Note text"))
        self.setPlaceholderText(
            _("Start writing… Use [[ to link a note, #tags, Q:/A: or {{c1::cloze}} for flashcards.")
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
        self.titles: list[tuple[str, str]] = []  # (title, folded title), sorted
        # The popup lists only what _maybe_complete puts here, so refreshing the titles after
        # an autosave can't reset it while someone is picking a note.
        self.matches_model = QStringListModel(self)
        self.completer = QCompleter(self.matches_model, self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self.completer.activated.connect(self._insert_completion)
        self.textChanged.connect(self._maybe_complete)

    def set_font_size(self, size: float) -> None:
        self.setFont(theme.ui_font(size))
        self.highlighter.base_size = size
        self.highlighter.rebuild()

    def set_titles(self, titles: list[str]) -> None:
        names = sorted({t for t in titles if t.strip()}, key=str.casefold)
        self.titles = [(t, fold(t)) for t in names]

    # --- [[ completion ------------------------------------------------------

    def _link_prefix(self) -> str | None:
        cursor = self.textCursor()
        block = cursor.block().text()[: cursor.positionInBlock()]
        start = block.rfind("[[")
        if start < 0 or "]]" in block[start:]:
            return None
        prefix = block[start + 2 :]
        return prefix if len(prefix) <= 80 and "\n" not in prefix else None

    def _matches(self, typed: str) -> list[str]:
        """Titles containing *typed*, ignoring case and accents: those that start with it
        first, then those with a word that does."""
        key = fold(typed).strip()
        ranked = []
        for title, folded in self.titles:
            at = folded.find(key)
            if at == 0:
                ranked.append((0, title))
            elif at > 0:
                word = any(w.startswith(key) for w in re.split(r"[\W_]+", folded))
                ranked.append((1 if word else 2, title))
        ranked.sort(key=lambda r: r[0])  # stable: alphabetical within each group
        return [title for _rank, title in ranked[:MAX_COMPLETIONS]]

    def _maybe_complete(self) -> None:
        prefix = self._link_prefix()
        popup = self.completer.popup()
        matches = self._matches(prefix) if prefix is not None else []
        if not matches:
            popup.hide()
            return
        self.matches_model.setStringList(matches)
        rect = self.cursorRect()
        rect.setWidth(max(280, popup.sizeHintForColumn(0) + 30))
        self.completer.complete(rect)
        # The best match starts highlighted, so Enter or Tab takes it.
        popup.setCurrentIndex(self.matches_model.index(0, 0))

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
            self.toggle_emphasis("**")
            return
        if event.matches(QKeySequence.StandardKey.Italic):
            self.toggle_emphasis("*")
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not event.modifiers():
            self._continue_list()
            return
        if event.key() == Qt.Key.Key_Control:
            self._update_link_cursor(Qt.KeyboardModifier.ControlModifier)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Control:
            self._update_link_cursor(Qt.KeyboardModifier.NoModifier)
        super().keyReleaseEvent(event)

    # --- Ctrl+click links -------------------------------------------------------

    def link_at(self, pos: QPoint) -> tuple[str, str] | None:
        """The link under a viewport position: ("note", title), ("url", href) or ("tag", tag)."""
        cursor = self.cursorForPosition(pos)
        rect = self.cursorRect(cursor)
        if not rect.top() <= pos.y() <= rect.bottom():
            return None  # below the last line
        text = cursor.block().text()
        col = cursor.positionInBlock()
        if rect.center().x() > pos.x():
            col -= 1  # the caret snaps to the nearest gap; the character left of it is hovered
        if not 0 <= col < len(text):
            return None
        for wl in find_wikilinks(text):
            if wl.start <= col < wl.end:
                return "note", wl.target
        for m in _MD_LINK_RE.finditer(text):
            if m.start() <= col < m.end():
                return "url", m.group(1) or m.group(2)
        for pattern in (_URL_RE, _PATH_RE):
            for m in pattern.finditer(text):
                if m.start() <= col < m.end():
                    return "url", m.group(0)
        for m in HASHTAG_RE.finditer(text):
            if m.start() <= col < m.end():
                return "tag", normalize_tag(m.group(1))
        return None

    def _link_tip(self, kind: str, target: str) -> str:
        if kind == "note":
            if self.resolve_note is not None and self.resolve_note(target) is None:
                return _("No note called “{title}” yet. Ctrl+click to create it.").format(
                    title=target
                )
            return _("Ctrl+click to open “{title}”").format(title=target)
        if kind == "tag":
            return _("Ctrl+click to list the notes tagged #{tag}").format(tag=target)
        path = local_file_path(target)
        if path:
            return _("Ctrl+click to show {name} in File Explorer").format(
                name=ntpath.basename(path) or path
            )
        return _("Ctrl+click to open {link}").format(link=target)

    def _update_link_cursor(self, modifiers) -> None:
        pos = self.viewport().mapFromGlobal(QCursor.pos())
        over = (
            bool(modifiers & Qt.KeyboardModifier.ControlModifier)
            and self.viewport().rect().contains(pos)
            and self.link_at(pos) is not None
        )
        self.viewport().setCursor(
            Qt.CursorShape.PointingHandCursor if over else Qt.CursorShape.IBeamCursor
        )

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if (
            event.button() == Qt.MouseButton.LeftButton
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self._pressed_link = self.link_at(event.position().toPoint())
            if self._pressed_link is not None:
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        link, self._pressed_link = self._pressed_link, None
        if link is not None:
            if link == self.link_at(event.position().toPoint()):
                self.linkActivated.emit(*link)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        super().mouseMoveEvent(event)
        if not event.buttons():
            self._update_link_cursor(event.modifiers())

    def viewportEvent(self, event) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.ToolTip:
            link = self.link_at(event.pos())
            if link is None:
                QToolTip.hideText()
            else:
                QToolTip.showText(event.globalPos(), self._link_tip(*link), self.viewport())
            return True
        return super().viewportEvent(event)

    def _continue_list(self) -> None:
        cursor = self.textCursor()
        line = cursor.block().text()
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(\[[ xX]\]\s+)?(.*)$", line)
        if not m:
            cursor.insertText("\n")
            return
        if not m.group(4).strip():  # empty item ends the list
            cursor.movePosition(
                QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor
            )
            cursor.removeSelectedText()
            cursor.insertText("\n")
            return
        marker = m.group(2)
        if marker[0].isdigit():
            marker = f"{int(marker[:-1]) + 1}{marker[-1]}"
        box = "[ ] " if m.group(3) else ""  # a new checklist item starts unchecked
        cursor.insertText(f"\n{m.group(1)}{marker} {box}")

    # --- images in the text -----------------------------------------------------

    def asset_at(self, pos: QPoint) -> str | None:
        """The asset name of the ![image](asset:…) under a viewport position, if any."""
        cursor = self.cursorForPosition(pos)
        text, col = cursor.block().text(), cursor.positionInBlock()
        for m in _ASSET_IMAGE_RE.finditer(text):
            if m.start() <= col <= m.end():
                return m.group(1)
        return None

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        menu = self.createStandardContextMenu(event.pos())
        asset = self.asset_at(event.pos())
        if asset and self.image_actions:
            menu.addSeparator()
            for text, callback in self.image_actions(asset):
                menu.addAction(text, callback)
        menu.exec(event.globalPos())

    # --- formatting helpers ---------------------------------------------------

    def toggle_emphasis(self, marker: str) -> None:
        """Make the selected text bold (marker "**") or italic ("*"), or plain again if it
        already is, like the buttons in a word processor. Each line is formatted on its own,
        since Markdown can't carry bold across lines; spaces and list, heading or quote marks
        at the edges stay outside the markers, or the Markdown wouldn't work. The text stays
        selected, so bold and italics can be combined."""
        cursor = self.textCursor()
        start, end = cursor.selectionStart(), cursor.selectionEnd()
        size = len(marker)
        if start == end:
            text, col = cursor.block().text(), cursor.positionInBlock()
            if col >= size and text[col - size : col + size] == marker * 2:
                cursor.movePosition(QTextCursor.MoveOperation.Left, n=size)
                cursor.movePosition(
                    QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 2 * size
                )
                cursor.removeSelectedText()  # pressed twice: take the empty markers back out
            else:
                cursor.insertText(marker * 2)
                cursor.movePosition(QTextCursor.MoveOperation.Left, n=size)
            self.setTextCursor(cursor)
            return
        parts = []  # (block, start, end in the block, how the markers sit there)
        block = self.document().findBlock(start)
        while block.isValid() and block.position() <= end:
            text = block.text()
            a = max(start - block.position(), len(_LINE_MARKS_RE.match(text).group(0)))
            b = min(end - block.position(), len(text))
            while a < b and text[a].isspace():
                a += 1
            while b > a and text[b - 1].isspace():
                b -= 1
            if a < b:
                parts.append((block, a, b, _emphasis_around(text, a, b, size)))
            block = block.next()
        if not parts:
            return
        remove = all(found is not None for *_unused, found in parts)
        selected = []
        cursor.beginEditBlock()
        for block, a, b, found in reversed(parts):  # later lines first: positions stay valid
            at = block.position()
            if remove:
                text_start, text_end = found
                for pos in (text_end, text_start - size):  # the markers nearest the text
                    cursor.setPosition(at + pos)
                    cursor.setPosition(at + pos + size, QTextCursor.MoveMode.KeepAnchor)
                    cursor.removeSelectedText()
                selected.append((block, text_start - size, text_end - size))
            elif found is None:
                cursor.setPosition(at + b)
                cursor.insertText(marker)
                cursor.setPosition(at + a)
                cursor.insertText(marker)
                selected.append((block, a + size, b + size))
            else:
                selected.append((block, *found))
        cursor.endEditBlock()
        last, first = selected[0], selected[-1]
        cursor.setPosition(first[0].position() + first[1])
        cursor.setPosition(last[0].position() + last[2], QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(cursor)

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
        # Must be a real bool: handing Qt a list makes it reject every dropped file.
        return bool(
            source.hasImage() or self._local_files(source) or super().canInsertFromMimeData(source)
        )

    def insertFromMimeData(self, source) -> None:  # noqa: N802
        files = self._local_files(source)
        if files:  # images are copied into the vault; other files are linked where they are
            for path in files:
                if path.lower().endswith(_IMAGE_SUFFIXES):
                    self._insert_image_file(path)
                else:
                    self.insert_file_link(path)
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
    def _local_files(source) -> list[str]:
        if not source.hasUrls():
            return []
        return [u.toLocalFile() for u in source.urls() if u.isLocalFile() and u.toLocalFile()]

    def insert_file_link(self, path: str) -> bool:
        """Insert [name](file:///…) for a file on a local drive; False if it can't be linked."""
        local = local_file_path(path)
        if local is None:
            self.fileLinkError.emit(_("Only files on this computer's drives can be linked."))
            return False
        name = re.sub(r"[\[\]]", "", ntpath.basename(local))[:120] or local
        self.textCursor().insertText(f"[{name}]({file_url(local)})")
        self.setFocus()
        return True

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
