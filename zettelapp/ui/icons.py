"""Icons drawn from the Windows icon fonts (Segoe Fluent Icons / MDL2 Assets), or, where those
fonts are absent (Linux), from the desktop's own symbolic icons and the Fluent UI System Icons.

Using the system icon fonts keeps the app consistent with Windows itself and lets icons follow
the theme colour at any DPI. Without them, each icon comes from, in order:

1. the desktop's icon theme (or a theme it inherits), when it has a monochrome *symbolic* icon
   whose meaning truly matches: NATIVE lists exact freedesktop icon names only, so full-colour
   themes such as Tango, which would clash with the Fluent look, fall through;
2. the Fluent UI System Icon that matches the Segoe glyph (FLUENT), bundled in
   resources/icons/fluent by tools/fetch_icons.py (MIT licence, see THIRD_PARTY_NOTICES.md).

Both are drawn in the requested colour, so they follow light and dark mode like the glyphs.
"""

from __future__ import annotations

import configparser
import math
import os
from functools import cache, lru_cache
from pathlib import Path

from PySide6.QtCore import QByteArray, QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from zettelapp.paths import resource_path
from zettelapp.ui import theme

GLYPHS = {
    "add": 0xE710,
    "cancel": 0xE711,
    "settings": 0xE713,
    "search": 0xE721,
    "delete": 0xE74D,
    "save": 0xE74E,
    "edit": 0xE70F,
    "link": 0xE71B,
    "tag": 0xE8EC,
    "image": 0xE8B9,
    "share": 0xE72D,
    "export": 0xEDE1,
    "import": 0xE8B5,
    "help": 0xE897,
    "info": 0xE946,
    "notes": 0xE70B,
    "review": 0xE7BE,
    "folder": 0xE8B7,
    "open": 0xE838,
    "refresh": 0xE72C,
    "check": 0xE73E,
    "document": 0xE8A5,
    "globe": 0xE774,
    "lightbulb": 0xEA80,
    "zoom_in": 0xE8A3,
    "zoom_out": 0xE71F,
    "fit": 0xE740,
    "sync": 0xE895,
    "more": 0xE712,
    "undo": 0xE7A7,
    "history": 0xE81C,
    "chat": 0xE8BD,
    "view": 0xE890,
    "filter": 0xE71C,
    "accept": 0xE8FB,
    "clear": 0xE894,
    "bullets": 0xE8FD,
    "bold": 0xE8DD,
    "italic": 0xE8DB,
    "heading": 0xE8D2,
    "code": 0xE943,
    "key": 0xE192,
    "shield": 0xEA18,
    "cube": 0xF158,
    "send": 0xE724,
    "copy": 0xE8C8,
    "insights": 0xEAFC,
    "group": 0xE902,
    "pin": 0xE718,
    "back": 0xE72B,
    "rotate": 0xE7AD,
    "relationship": 0xF003,
    "graph": 0xF22C,
    "cluster": 0xF0B9,
    "cards": 0xEADF,
    "server": 0xE968,
    "star": 0xE734,
    "flag": 0xE7C1,
    "archive": 0xE7B8,
    "trash": 0xE74D,
    "restore": 0xE777,
    "play": 0xE768,
    "stop": 0xE71A,
    "mindmap": 0xEBD2,
    "library": 0xE8F1,
    "open_external": 0xE8A7,
    "chevron_down": 0xE70D,
    "chevron_up": 0xE70E,
    "heart": 0xEB51,
    "heart_fill": 0xEB52,
    "checklist": 0xE73A,
    "alarm": 0xE121,
    "formula": 0xE8EF,
    "sort": 0xE8CB,
    # Word and WordPad label Bold and Italic with each language's own letter (N for negrito,
    # G for gras, F for fett, Ж for жирный…), and the Windows icon fonts have them.
    "bold_n": 0xE1B7,
    "bold_g": 0xE1B1,
    "bold_f": 0xE1B3,
    "bold_ru": 0xE1B9,
    "bold_ko": 0xE1BD,
    "italic_k": 0xE1B4,
    "italic_c": 0xE1B0,
    "italic_ru": 0xE1EA,
    "italic_ko": 0xE1BC,
}

# The Fluent UI System Icon drawn for each glyph where the Windows icon fonts are missing: the
# one that matches the Segoe Fluent Icons glyph at that code point (same picture, same meaning).
# Values are file names in resources/icons/fluent; ".<locale>" marks the language-specific letter
# variants of Text Bold / Text Italic. tools/fetch_icons.py downloads exactly these files.
FLUENT = {
    "add": "add_20_regular",
    "cancel": "dismiss_20_regular",
    "settings": "settings_20_regular",
    "search": "search_20_regular",
    "delete": "delete_20_regular",
    "save": "save_20_regular",
    "edit": "edit_20_regular",
    "link": "link_20_regular",
    "tag": "tag_20_regular",
    "image": "image_multiple_20_regular",
    "share": "share_20_regular",
    "export": "arrow_export_ltr_20_regular",
    "import": "arrow_import_20_regular",
    "help": "question_20_regular",
    "info": "info_20_regular",
    "notes": "note_20_regular",
    "review": "hat_graduation_20_regular",
    "folder": "folder_20_regular",
    "open": "folder_open_20_regular",
    "refresh": "arrow_clockwise_20_regular",
    "check": "checkmark_20_regular",
    "document": "document_20_regular",
    "globe": "globe_20_regular",
    "lightbulb": "lightbulb_20_regular",
    "zoom_in": "zoom_in_20_regular",
    "zoom_out": "zoom_out_20_regular",
    "fit": "arrow_maximize_20_regular",
    "sync": "arrow_sync_20_regular",
    "more": "more_horizontal_20_regular",
    "undo": "arrow_undo_20_regular",
    "history": "history_20_regular",
    "chat": "chat_20_regular",
    "view": "eye_20_regular",
    "filter": "filter_20_regular",
    "accept": "checkmark_20_regular",
    "clear": "dismiss_20_regular",
    "bullets": "text_bullet_list_ltr_20_regular",
    "bold": "text_bold_20_regular",
    "italic": "text_italic_20_regular",
    "heading": "text_font_20_regular",
    "code": "braces_20_regular",
    "key": "key_20_regular",
    "shield": "shield_20_regular",
    "cube": "cube_20_regular",
    "send": "send_20_regular",
    "copy": "copy_20_regular",
    "insights": "arrow_trending_20_regular",
    "group": "people_community_20_regular",
    "pin": "pin_20_regular",
    "back": "arrow_left_20_regular",
    "rotate": "arrow_rotate_clockwise_20_regular",
    "relationship": "organization_horizontal_20_regular",
    "graph": "iot_20_regular",
    "cluster": "connected_20_regular",
    "cards": "clipboard_task_list_ltr_20_regular",
    "server": "server_20_regular",
    "star": "star_20_regular",
    "flag": "flag_20_regular",
    "archive": "archive_20_regular",
    "trash": "delete_20_regular",
    "restore": "arrow_counterclockwise_20_regular",
    "play": "play_20_regular",
    "stop": "stop_20_regular",
    "mindmap": "cube_20_regular",  # Segoe's AdjustHologram: this cube, with dots at its corners
    "library": "library_20_regular",
    "open_external": "open_20_regular",
    "chevron_down": "chevron_down_20_regular",
    "chevron_up": "chevron_up_20_regular",
    "heart": "heart_20_regular",
    "heart_fill": "heart_20_filled",
    "checklist": "checkbox_checked_20_regular",
    "alarm": "clock_20_regular",
    "formula": "calculator_20_regular",
    "sort": "arrow_sort_20_regular",
    "bold_n": "text_bold_20_regular.pt",
    "bold_g": "text_bold_20_regular.fr",
    "bold_f": "text_bold_20_regular.de",
    "bold_ru": "text_bold_20_regular.ru",
    "bold_ko": "text_bold_20_regular.ko",
    "italic_k": "text_italic_20_regular.de",
    "italic_c": "text_italic_20_regular.it",
    "italic_ru": "text_italic_20_regular.ru",
    "italic_ko": "text_italic_20_regular.ko",
}

# Symbolic icons of the desktop's icon theme (freedesktop icon naming spec) used instead of the
# Fluent icon when the theme has one. Only exact names whose meaning truly matches; tried in order.
NATIVE = {
    "add": ("list-add-symbolic",),
    "cancel": ("window-close-symbolic",),
    "clear": ("edit-clear-symbolic",),
    "settings": ("emblem-system-symbolic", "preferences-system-symbolic"),
    "search": ("edit-find-symbolic",),
    "delete": ("user-trash-symbolic", "edit-delete-symbolic"),
    "trash": ("user-trash-symbolic",),
    "save": ("document-save-symbolic",),
    "edit": ("document-edit-symbolic",),
    # No "link": Adwaita's insert-link-symbolic is a bar and an arrow, not a chain, so the
    # suggestion buttons and mind-map markers keep the Fluent chain on every desktop.
    "image": ("image-x-generic-symbolic",),
    "help": ("help-contents-symbolic",),
    "folder": ("folder-symbolic",),
    "open": ("document-open-symbolic",),
    "refresh": ("view-refresh-symbolic",),
    "check": ("object-select-symbolic",),
    "accept": ("object-select-symbolic",),
    "document": ("text-x-generic-symbolic",),
    "zoom_in": ("zoom-in-symbolic",),
    "zoom_out": ("zoom-out-symbolic",),
    "fit": ("zoom-fit-best-symbolic",),
    "more": ("view-more-horizontal-symbolic",),
    "undo": ("edit-undo-symbolic",),
    "history": ("document-open-recent-symbolic",),
    "view": ("view-reveal-symbolic",),
    "bullets": ("view-list-bullet-symbolic",),
    "key": ("dialog-password-symbolic",),
    "copy": ("edit-copy-symbolic",),
    "pin": ("view-pin-symbolic",),
    "back": ("go-previous-symbolic",),
    "server": ("network-server-symbolic",),
    "play": ("media-playback-start-symbolic",),
    "stop": ("media-playback-stop-symbolic",),
    "chevron_down": ("pan-down-symbolic",),
    "chevron_up": ("pan-up-symbolic",),
    "checklist": ("checkbox-checked-symbolic",),
    "alarm": ("alarm-symbolic",),
}

# The glyphs fill 0.8 of the icon box (the font is drawn at 0.8 x the icon size). The Fluent
# icons keep that margin themselves (2 px of 20), so they are drawn over the whole box; the
# 16 px symbolic icons of icon themes have almost none, so they get a 0.8 box. Icons smaller
# than SMALL use the 16 px Fluent design, whose 1 px strokes stay sharp at that size.
GLYPH_SCALE = 0.8
SMALL = 18

_FORMAT_GLYPHS = {
    "pt_BR": ("bold_n", "italic"),
    "es": ("bold_n", "italic_k"),
    "fr": ("bold_g", "italic"),
    "de": ("bold_f", "italic_k"),
    "it": ("bold_g", "italic_c"),
    "ru": ("bold_ru", "italic_ru"),
    "ko": ("bold_ko", "italic_ko"),
}


def format_glyphs(language: str) -> tuple[str, str]:
    """The glyphs for the Bold and Italic buttons in *language*; B and I where Windows uses them."""
    return _FORMAT_GLYPHS.get(language, ("bold", "italic"))


@cache
def _icon_family() -> str | None:
    families = set(QFontDatabase.families())
    for name in ("Segoe Fluent Icons", "Segoe MDL2 Assets"):
        if name in families:
            return name
    return None


def clear_cache() -> None:
    _pixmap.cache_clear()
    _tinted.cache_clear()
    _source.cache_clear()
    _theme_index.cache_clear()


# --- the desktop's icon theme ----------------------------------------------------------------


def _icon_folders() -> list[Path]:
    """Folders holding icon themes: Qt's search path and the XDG data directories."""
    home = Path.home()
    data_home = os.environ.get("XDG_DATA_HOME") or str(home / ".local" / "share")
    data_dirs = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
    candidates = [p for p in QIcon.themeSearchPaths() if not p.startswith(":")]
    candidates += [str(Path(data_home) / "icons"), str(home / ".icons")]
    candidates += [str(Path(d) / "icons") for d in data_dirs.split(os.pathsep) if d]
    folders: list[Path] = []
    for candidate in candidates:
        folder = Path(candidate)
        if folder.is_dir() and folder not in folders:
            folders.append(folder)
    return folders


def _size_distance(parser: configparser.ConfigParser, subdir: str) -> tuple[int, int]:
    """How far the icons in *subdir* are from the 16 px design that symbolic icons are drawn
    at (the icon theme spec's directory size distance), then their scale: a theme's 16 px
    folder is searched before its 32 px one, whatever the order of its Directories key."""
    entry = parser[subdir] if parser.has_section(subdir) else {}
    try:
        size = int(entry.get("Size", "0"))
        scale = int(entry.get("Scale", "1"))
        low, high = int(entry.get("MinSize", size)), int(entry.get("MaxSize", size))
    except ValueError:
        return 1 << 16, 1
    if entry.get("Type", "Threshold") == "Scalable" and low <= 16 <= high:
        return 0, scale
    return abs(size - 16), scale


@cache
def _theme_index(name: str) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    """The folders of icon theme *name*, closest to 16 px first, and the themes it inherits,
    from its index.theme."""
    roots = [folder / name for folder in _icon_folders() if (folder / name).is_dir()]
    for root in roots:
        index = root / "index.theme"
        if not index.is_file():
            continue
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str  # type: ignore[assignment,method-assign]
        try:
            parser.read(index, encoding="utf-8")
            section = parser["Icon Theme"]
        except (configparser.Error, KeyError, UnicodeDecodeError, OSError):
            return (), ()
        subdirs = [
            d.strip()
            for key in ("Directories", "ScaledDirectories")
            for d in section.get(key, "").split(",")
            if d.strip()
        ]
        subdirs.sort(key=lambda d: _size_distance(parser, d))
        inherits = tuple(t.strip() for t in section.get("Inherits", "").split(",") if t.strip())
        folders = tuple(r / d for d in subdirs for r in roots if (r / d).is_dir())
        return folders, inherits
    return (), ()


def _theme_chain(name: str) -> list[str]:
    """*name* and every theme it inherits, depth first. hicolor, the shared fallback that
    applications install their own icons into, has no design of its own and is left out."""
    chain: list[str] = []

    def visit(theme_name: str) -> None:
        if theme_name in chain or theme_name == "hicolor" or len(chain) > 16:
            return
        chain.append(theme_name)
        for parent in _theme_index(theme_name)[1]:
            visit(parent)

    visit(name)
    return chain


def _is_monochrome(path: Path) -> bool:
    """True when the icon has no colour of its own (symbolic icons are drawn in one grey)."""
    image = _render(path, 24, None)
    opaque = colourful = 0
    for y in range(image.height()):
        for x in range(image.width()):
            pixel = image.pixelColor(x, y)
            if pixel.alpha() < 128:
                continue
            opaque += 1
            if pixel.hsvSaturationF() > 0.35 and pixel.valueF() > 0.25:
                colourful += 1
    return opaque > 0 and colourful <= opaque // 10


def _alias_of_another_icon(name: str, path: Path) -> bool:
    """True when *path* links to the theme's icon of another meaning: Breeze's
    checkbox-checked-symbolic, for one, is a link to its pencil, document-edit."""
    target = path.resolve().stem.removesuffix("-symbolic")
    return any(
        FLUENT[other] != FLUENT[name] and f"{target}-symbolic" in names
        for other, names in NATIVE.items()
    )


def _native_file(name: str, theme_name: str) -> Path | None:
    """The theme's symbolic icon for glyph *name*, if it has one that qualifies."""
    if not theme_name or name not in NATIVE:
        return None
    for theme_name_ in _theme_chain(theme_name):
        folders = _theme_index(theme_name_)[0]
        for icon_name in NATIVE[name]:
            found = [f / f"{icon_name}.svg" for f in folders if (f / f"{icon_name}.svg").is_file()]
            if not found:  # a theme without scalable icons: its largest picture
                pngs = [f / f"{icon_name}.png" for f in folders]
                found = sorted(
                    (p for p in pngs if p.is_file()), key=lambda p: -QImage(str(p)).width()
                )
            for path in found:
                if _is_monochrome(path) and not _alias_of_another_icon(name, path):
                    return path
    return None


# --- drawing ---------------------------------------------------------------------------------


@cache
def _source(name: str, theme_name: str, small: bool = False) -> tuple[Path, float] | None:
    """The picture drawn for *name* and the share of the icon box it fills."""
    native = _native_file(name, theme_name)
    if native is not None:
        return native, GLYPH_SCALE
    if name not in FLUENT:
        return None
    stems = [FLUENT[name]]
    if small:
        stems.insert(0, FLUENT[name].replace("_20_", "_16_", 1))
    for stem in stems:
        path = resource_path("icons", "fluent", f"{stem}.svg")
        if path.is_file():
            return path, 1.0
    return None


def _render(path: Path, pixels: int, color: QColor | None, fill: float = 1.0) -> QImage:
    """*path* drawn in a transparent square of *pixels*, recoloured to *color* if given."""
    image = QImage(pixels, pixels, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    try:
        _draw(painter, path, QRectF(0, 0, pixels, pixels), color, fill)
    finally:
        painter.end()
    return image


@cache
def _svg_data(path: Path) -> QByteArray:
    return QByteArray(path.read_bytes())


@lru_cache(maxsize=256)
def _tinted(path: Path, fill: float, color: str, pixels: int) -> QImage:
    return _render(path, pixels, QColor(color), fill)


def _draw(painter: QPainter, path: Path, box: QRectF, color: QColor | None, fill: float) -> None:
    """Draw *path* centred in *box* over *fill* of its size, then tint it with *color*.

    Painting is in logical pixels, so the vector drawing stays sharp at any device-pixel ratio.
    """
    side = box.width() * fill
    target = QRectF(
        box.center().x() - side / 2, box.center().y() - side / 2, side, side
    ).intersected(box)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    if path.suffix == ".svg":
        renderer = QSvgRenderer(_svg_data(path))
        renderer.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        renderer.render(painter, target)
    else:
        painter.drawImage(target, QImage(str(path)))
    if color is not None:
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(box, color)


@cache
def _pixmap(name: str, color: str, size: int, ratio: float, theme_name: str = "") -> QPixmap:
    px = QPixmap(QSize(round(size * ratio), round(size * ratio)))
    px.setDevicePixelRatio(ratio)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    try:
        family = _icon_family()
        if family is None:
            # No Windows icon font (Linux, some sandboxes): the theme's or the Fluent icon.
            source = _source(name, theme_name, size < SMALL)
            if source is not None:
                _draw(painter, source[0], QRectF(0, 0, size, size), QColor(color), source[1])
            return px
        if name not in GLYPHS:
            return px
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        font = QFont(family)
        font.setPixelSize(round(size * 0.8))
        painter.setFont(font)
        painter.setPen(QColor(color))
        painter.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, chr(GLYPHS[name]))
        return px
    finally:
        # Always detach the painter: the pixmap is cached and must never be
        # destroyed while still being painted (corrupts the heap otherwise).
        painter.end()


def icon(name: str, color: str | None = None, size: int = 20) -> QIcon:
    t = theme.current()
    result = QIcon()
    sizes = [size]
    theme_name = ""
    if _icon_family() is None:
        theme_name = QIcon.themeName()
        if size > 16:
            # Tool buttons, menus and tabs show icons at 16 px: draw that size too rather
            # than shrinking the larger picture, which would blur the thin strokes.
            sizes.append(16)
    for s in sizes:
        for ratio in (1.0, 1.25, 1.5, 2.0):
            result.addPixmap(
                _pixmap(name, color or t.text, s, ratio, theme_name), QIcon.Mode.Normal
            )
            result.addPixmap(_pixmap(name, t.text_muted, s, ratio, theme_name), QIcon.Mode.Disabled)
            if color is None:
                result.addPixmap(_pixmap(name, t.text, s, ratio, theme_name), QIcon.Mode.Active)
                result.addPixmap(_pixmap(name, t.accent, s, ratio, theme_name), QIcon.Mode.Selected)
    return result


def paint(painter: QPainter, name: str, rect: QRectF, color: QColor, pixel_size: int) -> None:
    """Draw icon *name* centred in *rect* at the size of a *pixel_size* glyph.

    With the Windows icon fonts this draws the glyph as text; elsewhere it draws the icon,
    rendered for the painter's current scale, so it stays sharp in a zoomed view too.
    """
    family = _icon_family()
    painter.save()
    try:
        if family is not None:
            painter.setFont(glyph_font(pixel_size))
            painter.setPen(color)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, glyph(name))
            return
        side = pixel_size / GLYPH_SCALE
        source = _source(name, QIcon.themeName(), side < SMALL)
        if source is None:
            return
        t = painter.combinedTransform()
        device = painter.device()
        ratio = device.devicePixelRatioF() if device is not None else 1.0
        pixels = max(1, math.ceil(side * math.hypot(t.m11(), t.m12()) * ratio))
        image = _tinted(source[0], source[1], QColor(color).name(QColor.NameFormat.HexArgb), pixels)
        centre = rect.center()
        target = QRectF(centre.x() - side / 2, centre.y() - side / 2, side, side)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(target, image)
    finally:
        painter.restore()


def glyph(name: str) -> str:
    """The character of *name* in the icon font, or "" where there is none (Linux)."""
    if _icon_family() is None:
        return ""  # icons come from the theme or the bundled Fluent icons instead (see paint)
    return chr(GLYPHS.get(name, 0x20))


def glyph_font(pixel_size: int = 16) -> QFont:
    font = QFont(_icon_family() or "")
    font.setPixelSize(pixel_size)
    return font
