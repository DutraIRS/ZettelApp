"""Read-only rendering of a note (or an AI answer) with safe resource loading."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFontInfo, QImage, QTextDocument
from PySide6.QtWidgets import QTextBrowser

from zettelapp.core.render import (
    ASSET_SCHEME,
    MATH_DISPLAY_SCHEME,
    MATH_SCHEME,
    NEW_NOTE_SCHEME,
    NOTE_SCHEME,
    TASK_SCHEME,
    NoteRenderer,
    new_note_title,
)
from zettelapp.core.security import (
    is_openable_url,
    is_valid_asset_name,
    is_valid_note_id,
    local_file_path,
)
from zettelapp.i18n import _
from zettelapp.ui import mathrender, theme


def math_href(latex: str, display: bool) -> str:
    """The image address the preview draws a formula from (see NotePreview.loadResource)."""
    return (MATH_DISPLAY_SCHEME if display else MATH_SCHEME) + mathrender.encode(latex)


READING_LINE = 34  # the reading column's width, in multiples of the font's pixel size (~70 letters)
MARGIN = 8  # px around the text beside the editor, in Review and in Ask
READING_MARGIN = 24  # px at least, either side of the reading column


def preview_css(px: int = 14) -> str:
    """The preview's style for a body font *px* pixels high: one spacing step for every block.

    Paragraphs, lists, quotes and code all leave one step below them; a heading leaves two
    above (it starts a section) and half a step below (it belongs to what follows).
    """
    t = theme.current()
    italic = ", ".join(f"'{family}'" for family in theme.ITALIC_FONTS)
    step = round(px * 0.75)
    block = f"margin: 0 0 {step}px 0;"
    return f"""
body {{ color: {t.text}; font-size: {px}px; }}
h1 {{ font-size: {round(px * 1.6)}px; font-weight: 600; margin: {step * 2}px 0 {step // 2}px 0; }}
h2 {{ font-size: {round(px * 1.3)}px; font-weight: 600; margin: {step * 2}px 0 {step // 2}px 0; }}
h3, h4, h5, h6 {{ font-size: {round(px * 1.1)}px; font-weight: 600;
    margin: {round(step * 1.5)}px 0 {step // 2}px 0; }}
p {{ {block} line-height: 150%; }}
p.picture {{ line-height: 100%; }}
ul, ol {{ {block} }}
li {{ margin: 0 0 {step // 3}px 0; line-height: 150%; }}
em, i {{ font-family: {italic}; }}
a {{ color: {t.link}; text-decoration: none; }}
a.new-note {{ color: {t.text_muted}; text-decoration: underline; }}
a.file {{ color: {t.link}; text-decoration: underline; }}
a.task {{ color: {t.link}; text-decoration: none; font-size: {round(px * 1.25)}px; }}
a.broken {{ color: {t.text_muted}; }}
code {{ font-family: 'Cascadia Code', Consolas, monospace; background-color: {t.window}; }}
pre {{ font-family: 'Cascadia Code', Consolas, monospace; background-color: {t.window};
    padding: 8px; {block} }}
blockquote {{ color: {t.text_secondary}; margin: 0 0 {step}px {step * 2}px; }}
table {{ {block} }}
th {{ font-weight: 600; text-align: left; }}
td, th {{ padding: 3px 8px; border: 1px solid {t.border}; }}
.missing-image {{ color: {t.text_muted}; }}
"""


class NotePreview(QTextBrowser):
    noteRequested = Signal(str)
    newNoteRequested = Signal(str)
    fileRequested = Signal(str)  # a local path to show in the file manager
    taskToggled = Signal(int)  # the position of a checklist box among all boxes in the note
    hovered = Signal(str)

    def __init__(self, asset_path: Callable[[str], Path | None], parent=None):
        super().__init__(parent)
        self.setObjectName("Preview")
        self.asset_path = asset_path
        self.renderer: NoteRenderer | None = None
        # Given an asset name, the (text, callback) actions to offer on right-click.
        self.image_actions: Callable[[str], list[tuple[str, Callable[[], None]]]] | None = None
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.anchorClicked.connect(self._on_anchor)
        self.highlighted.connect(self._on_hover)
        self.reading = False
        self.document().setDocumentMargin(MARGIN)

    def set_font_size(self, size: float) -> None:
        """Read in the editor's font size (points); shown from the next render."""
        self.setFont(theme.ui_font(size))

    def set_reading(self, reading: bool) -> None:
        """Lay the note out as a centred column of comfortable width, to read it."""
        self.reading = reading
        self._place_column()

    def _place_column(self) -> None:
        width = self.viewport().width()
        side = MARGIN
        if self.reading:
            line = READING_LINE * QFontInfo(self.font()).pixelSize()
            side = max(READING_MARGIN, (width - line) // 2)
        root = self.document().rootFrame()
        frame = root.frameFormat()
        if (frame.leftMargin(), frame.rightMargin()) != (side, side):
            frame.setLeftMargin(side)
            frame.setRightMargin(side)
            frame.setTopMargin(READING_MARGIN if self.reading else MARGIN)
            root.setFrameFormat(frame)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        self._place_column()

    def set_renderer(self, renderer: NoteRenderer) -> None:
        self.renderer = renderer

    def show_markdown(self, text: str) -> None:
        if self.renderer is None:
            return
        scroll = self.verticalScrollBar().value()
        self.document().setDefaultStyleSheet(preview_css(QFontInfo(self.font()).pixelSize()))
        self.setHtml(self.renderer.render(text))
        self._place_column()
        self.verticalScrollBar().setValue(scroll)

    def contextMenuEvent(self, event) -> None:  # noqa: N802 - Qt API
        menu = self.createStandardContextMenu(event.pos())
        name = (
            self.document().documentLayout().imageAt(QPointF(event.pos() + self._scroll_offset()))
        )
        asset = name[len(ASSET_SCHEME) :] if name.startswith(ASSET_SCHEME) else ""
        if asset and self.image_actions:
            menu.addSeparator()
            for text, callback in self.image_actions(asset):
                menu.addAction(text, callback)
        menu.exec(event.globalPos())

    def _scroll_offset(self) -> QPoint:
        return QPoint(self.horizontalScrollBar().value(), self.verticalScrollBar().value())

    def _math_image(self, text: str) -> QImage | None:
        display = text.startswith(MATH_DISPLAY_SCHEME)
        latex = mathrender.decode(text[len(MATH_DISPLAY_SCHEME if display else MATH_SCHEME) :])
        if not latex:
            return None
        size = QFontInfo(self.font()).pixelSize()
        color = theme.current().text
        ratio = max(1.0, self.devicePixelRatioF())
        return mathrender.render(
            latex, size * (1.15 if display else 1.0), color, display, ratio
        ).image

    def loadResource(self, kind: int, url: QUrl):  # noqa: N802 - Qt API
        # Only images from the vault's assets folder, and formulas drawn here, are loaded.
        if kind == QTextDocument.ResourceType.ImageResource.value:
            text = url.toString()
            if text.startswith((MATH_SCHEME, MATH_DISPLAY_SCHEME)):
                return self._math_image(text)
            if text.startswith(ASSET_SCHEME) and is_valid_asset_name(text[len(ASSET_SCHEME) :]):
                path = self.asset_path(text[len(ASSET_SCHEME) :])
                if path is not None:
                    image = QImage(str(path))
                    max_width = max(200, self.viewport().width() - 24)
                    if image.width() > max_width:
                        image = image.scaledToWidth(
                            max_width, Qt.TransformationMode.SmoothTransformation
                        )
                    return image
        return None

    def _on_hover(self, url: QUrl) -> None:
        href = url.toString()
        if href.startswith(TASK_SCHEME):
            return
        path = local_file_path(href)
        self.hovered.emit(_("Show in file manager: {path}").format(path=path) if path else href)

    def _on_anchor(self, url: QUrl) -> None:
        href = url.toString()
        path = local_file_path(href)
        if href.startswith(TASK_SCHEME):
            index = href[len(TASK_SCHEME) :]
            if index.isdigit():
                self.taskToggled.emit(int(index))
        elif path:  # shown in the file manager, never opened or run
            self.fileRequested.emit(path)
        elif href.startswith(NOTE_SCHEME) and is_valid_note_id(href[len(NOTE_SCHEME) :]):
            self.noteRequested.emit(href[len(NOTE_SCHEME) :])
        elif href.startswith(NEW_NOTE_SCHEME):
            title = new_note_title(href)
            if title:
                self.newNoteRequested.emit(title)
        elif is_openable_url(href):  # web pages, e-mail and Zotero items only
            QDesktopServices.openUrl(QUrl(href))
