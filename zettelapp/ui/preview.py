"""Read-only rendering of a note (or an AI answer) with safe resource loading."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFontInfo, QImage, QTextDocument
from PySide6.QtWidgets import QTextBrowser

from zettelapp import settings
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


def preview_css(px: int = 14, line_spacing: int = 125, paragraph_spacing: int = 75) -> str:
    """The preview's style for a body font *px* pixels high: one spacing step for every block.

    Paragraphs, lists, quotes and code all leave one step below them; a heading leaves two
    above (it starts a section) and half a step below (it belongs to what follows). The step
    is *paragraph_spacing* percent of the text size, and lines are *line_spacing* percent apart.
    """
    t = theme.current()
    italic = ", ".join(f"'{family}'" for family in theme.ITALIC_FONTS)
    step = round(px * paragraph_spacing / 100)
    block = f"margin: 0 0 {step}px 0;"
    lines = f"line-height: {line_spacing}%;"
    return f"""
body {{ color: {t.text}; font-size: {px}px; }}
h1 {{ font-size: {round(px * 1.6)}px; font-weight: 600; margin: {step * 2}px 0 {step // 2}px 0; }}
h2 {{ font-size: {round(px * 1.3)}px; font-weight: 600; margin: {step * 2}px 0 {step // 2}px 0; }}
h3, h4, h5, h6 {{ font-size: {round(px * 1.1)}px; font-weight: 600;
    margin: {round(step * 1.5)}px 0 {step // 2}px 0; }}
p {{ {block} {lines} }}
p.picture {{ line-height: 100%; }}
ul, ol {{ {block} }}
li {{ margin: 0 0 {step // 3}px 0; {lines} }}
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


def justified(html: str) -> str:
    """*html* with its paragraphs and list items justified. Qt's style sheets don't know
    text-align: justify, only the align attribute; a centred formula keeps its own."""
    return re.sub(r"<(p|li)>", r'<\1 align="justify">', html)


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
        self._text: str | None = None  # the Markdown shown, to lay pictures out again
        self._pictures_for: int | None = None  # the column width the pictures were sized for
        # Pictures are sized when loaded; when the column's width changes (the window resized,
        # Reading view's wider column) they are loaded again for the new width.
        self._resize_pictures = QTimer(self, singleShot=True, interval=120)
        self._resize_pictures.timeout.connect(self._rerender)

    def set_font_size(self, size: float) -> None:
        """Read in the editor's font size (points); shown from the next render."""
        self.setFont(theme.ui_font(size))

    def set_reading(self, reading: bool) -> None:
        """Lay the note out as a centred column of comfortable width, to read it."""
        self.reading = reading
        self._place_column()

    def _side(self) -> int:
        """The space either side of the text: the reading column's margins, or MARGIN."""
        if not self.reading:
            return MARGIN
        line = READING_LINE * QFontInfo(self.font()).pixelSize()
        return max(READING_MARGIN, (self.viewport().width() - line) // 2)

    def column_width(self) -> int:
        """The width the text is laid out in, between the side margins, with room kept for the
        vertical scroll bar so that it showing up doesn't change the width."""
        width = self.viewport().width()
        bar = self.verticalScrollBar()
        if not bar.isVisible():
            width -= bar.sizeHint().width()
        margin = round(self.document().documentMargin())
        return width - 2 * (self._side() + margin)

    def _place_column(self) -> None:
        side = self._side()
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
        if self._pictures_for is not None and self.column_width() != self._pictures_for:
            self._resize_pictures.start()

    def _rerender(self) -> None:
        if self._text is not None and self.column_width() != self._pictures_for:
            self.show_markdown(self._text)

    def set_renderer(self, renderer: NoteRenderer) -> None:
        self.renderer = renderer

    def show_markdown(self, text: str) -> None:
        if self.renderer is None:
            return
        scroll = self.verticalScrollBar().value()
        self._text = text
        self._pictures_for = None
        self.document().setDefaultStyleSheet(
            preview_css(
                QFontInfo(self.font()).pixelSize(),
                settings.get(settings.PREVIEW_LINE_SPACING),
                settings.get(settings.PREVIEW_PARAGRAPH_SPACING),
            )
        )
        self.renderer.set_line_breaks(settings.get(settings.PREVIEW_LINE_BREAKS))
        html = self.renderer.render(text)
        if settings.get(settings.PREVIEW_ALIGN) == "justify":
            html = justified(html)
        self.setHtml(html)
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
                    # A picture fits the text's column: wider, it stuck out of the reading
                    # column and the view scrolled sideways.
                    self._pictures_for = self.column_width()
                    max_width = max(64, self._pictures_for)
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
