"""Read-only rendering of a note (or an AI answer) with safe resource loading."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QImage, QTextDocument
from PySide6.QtWidgets import QTextBrowser

from zettelapp.core.render import (
    ASSET_SCHEME,
    NEW_NOTE_SCHEME,
    NOTE_SCHEME,
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
from zettelapp.ui import theme


def preview_css() -> str:
    t = theme.current()
    return f"""
body {{ color: {t.text}; }}
h1 {{ font-size: 20pt; font-weight: 600; margin: 14px 0 6px 0; }}
h2 {{ font-size: 15pt; font-weight: 600; margin: 14px 0 6px 0; }}
h3, h4, h5, h6 {{ font-size: 12pt; font-weight: 600; margin: 12px 0 4px 0; }}
p {{ margin: 0 0 9px 0; line-height: 150%; }}
a {{ color: {t.accent}; text-decoration: none; }}
a.new-note {{ color: {t.text_muted}; text-decoration: underline; }}
a.file {{ color: {t.accent}; text-decoration: underline; }}
a.broken {{ color: {t.text_muted}; }}
code {{ font-family: 'Cascadia Code', Consolas, monospace; background-color: {t.window}; }}
pre {{ font-family: 'Cascadia Code', Consolas, monospace; background-color: {t.window}; padding: 8px; }}
blockquote {{ color: {t.text_secondary}; margin-left: 12px; }}
th {{ font-weight: 600; text-align: left; }}
td, th {{ padding: 3px 8px; border: 1px solid {t.border}; }}
.missing-image {{ color: {t.text_muted}; }}
"""


class NotePreview(QTextBrowser):
    noteRequested = Signal(str)
    newNoteRequested = Signal(str)
    fileRequested = Signal(str)  # a local path to show in File Explorer
    hovered = Signal(str)

    def __init__(self, asset_path: Callable[[str], Path | None], parent=None):
        super().__init__(parent)
        self.setObjectName("Preview")
        self.asset_path = asset_path
        self.renderer: NoteRenderer | None = None
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.anchorClicked.connect(self._on_anchor)
        self.highlighted.connect(self._on_hover)
        self.document().setDocumentMargin(4)

    def set_renderer(self, renderer: NoteRenderer) -> None:
        self.renderer = renderer

    def show_markdown(self, text: str) -> None:
        if self.renderer is None:
            return
        scroll = self.verticalScrollBar().value()
        self.document().setDefaultStyleSheet(preview_css())
        self.setHtml(self.renderer.render(text))
        self.verticalScrollBar().setValue(scroll)

    def loadResource(self, kind: int, url: QUrl):  # noqa: N802 - Qt API
        # Only images from the vault's assets folder are ever loaded.
        if kind == QTextDocument.ResourceType.ImageResource.value:
            text = url.toString()
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
        path = local_file_path(href)
        self.hovered.emit(_("Show in File Explorer: {path}").format(path=path) if path else href)

    def _on_anchor(self, url: QUrl) -> None:
        href = url.toString()
        path = local_file_path(href)
        if path:  # shown in File Explorer, never opened or run
            self.fileRequested.emit(path)
        elif href.startswith(NOTE_SCHEME) and is_valid_note_id(href[len(NOTE_SCHEME) :]):
            self.noteRequested.emit(href[len(NOTE_SCHEME) :])
        elif href.startswith(NEW_NOTE_SCHEME):
            title = new_note_title(href)
            if title:
                self.newNoteRequested.emit(title)
        elif is_openable_url(href):  # web pages, e-mail and Zotero items only
            QDesktopServices.openUrl(QUrl(href))
