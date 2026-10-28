"""Icons drawn from the Windows icon fonts (Segoe Fluent Icons / MDL2 Assets).

Using the system icon fonts keeps the app consistent with Windows itself and
lets icons follow the theme colour at any DPI.
"""

from __future__ import annotations

from functools import cache

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPixmap

from zettelapp.ui import theme

GLYPHS = {
    "add": 0xE710, "cancel": 0xE711, "settings": 0xE713, "search": 0xE721, "delete": 0xE74D,
    "save": 0xE74E, "edit": 0xE70F, "link": 0xE71B, "tag": 0xE8EC, "image": 0xE8B9, "share": 0xE72D,
    "export": 0xEDE1, "import": 0xE8B5, "help": 0xE897, "info": 0xE946, "notes": 0xE70B,
    "review": 0xE7BE, "folder": 0xE8B7, "open": 0xE838, "refresh": 0xE72C, "check": 0xE73E,
    "document": 0xE8A5, "globe": 0xE774, "lightbulb": 0xEA80, "zoom_in": 0xE8A3, "zoom_out": 0xE71F,
    "fit": 0xE740, "sync": 0xE895, "more": 0xE712, "undo": 0xE7A7, "history": 0xE81C, "chat": 0xE8BD,
    "view": 0xE890, "filter": 0xE71C, "accept": 0xE8FB, "clear": 0xE894, "bullets": 0xE8FD,
    "bold": 0xE8DD, "italic": 0xE8DB, "heading": 0xE8D2, "code": 0xE943, "key": 0xE192,
    "shield": 0xEA18, "cube": 0xF158, "send": 0xE724, "copy": 0xE8C8, "insights": 0xEAFC,
    "group": 0xE902, "pin": 0xE718, "back": 0xE72B, "rotate": 0xE7AD, "relationship": 0xF003,
    "graph": 0xF22C, "cluster": 0xF0B9, "cards": 0xEADF, "server": 0xE968, "star": 0xE734,
    "flag": 0xE7C1, "archive": 0xE7B8, "trash": 0xE74D, "restore": 0xE777, "play": 0xE768,
    "stop": 0xE71A, "mindmap": 0xEBD2, "library": 0xE8F1, "open_external": 0xE8A7,
    "chevron_down": 0xE70D, "chevron_up": 0xE70E,
}


@cache
def _icon_family() -> str | None:
    families = set(QFontDatabase.families())
    for name in ("Segoe Fluent Icons", "Segoe MDL2 Assets"):
        if name in families:
            return name
    return None


def clear_cache() -> None:
    _pixmap.cache_clear()


@cache
def _pixmap(name: str, color: str, size: int, ratio: float) -> QPixmap:
    px = QPixmap(QSize(round(size * ratio), round(size * ratio)))
    px.setDevicePixelRatio(ratio)
    px.fill(Qt.GlobalColor.transparent)
    family = _icon_family()
    if family is None or name not in GLYPHS:
        return px
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    font = QFont(family)
    font.setPixelSize(round(size * 0.8))
    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, chr(GLYPHS[name]))
    painter.end()
    return px


def icon(name: str, color: str | None = None, size: int = 20) -> QIcon:
    t = theme.current()
    result = QIcon()
    for ratio in (1.0, 1.25, 1.5, 2.0):
        result.addPixmap(_pixmap(name, color or t.text, size, ratio), QIcon.Mode.Normal)
        result.addPixmap(_pixmap(name, t.text_muted, size, ratio), QIcon.Mode.Disabled)
        if color is None:
            result.addPixmap(_pixmap(name, t.text, size, ratio), QIcon.Mode.Active)
            result.addPixmap(_pixmap(name, t.accent, size, ratio), QIcon.Mode.Selected)
    return result


def glyph(name: str) -> str:
    return chr(GLYPHS.get(name, 0x20))


def glyph_font(pixel_size: int = 16) -> QFont:
    font = QFont(_icon_family() or "")
    font.setPixelSize(pixel_size)
    return font
