"""Icons and fonts where the Windows icon fonts and Segoe UI are missing (Linux).

Icons come from the desktop's symbolic icon theme or the bundled Fluent UI System Icons; the UI
font is the desktop's own. These tests force the non-Windows path, so they run anywhere.
"""

import os
import re
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6.QtSvg")

from PySide6.QtCore import QRectF, QSize, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QFontInfo, QIcon, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from zettelapp.paths import resource_path  # noqa: E402
from zettelapp.ui import icons, theme  # noqa: E402

_linux = pytest.mark.skipif(sys.platform != "linux", reason="Linux-specific behaviour")
GREY = '<path fill="#2e3436" d="M2 7h12v2H2z"/>'
RAINBOW = '<path fill="#ff0000" d="M2 2h12v6H2z"/><path fill="#00c000" d="M2 8h12v6H2z"/>'


@pytest.fixture
def app():
    return QApplication.instance() or QApplication(["test"])


@pytest.fixture
def no_icon_font(app, monkeypatch):
    """The Linux situation: no Segoe Fluent Icons / MDL2 Assets, and no icon theme."""
    monkeypatch.setattr(icons, "_icon_family", lambda: None)
    previous = QIcon.themeName()
    QIcon.setThemeName("")
    icons.clear_cache()
    yield
    QIcon.setThemeName(previous)
    icons.clear_cache()


def _drawn_in(image: QImage, colour: str) -> bool:
    """True when the image shows something, and everything it shows is *colour*."""
    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    want = QColor(colour)
    seen = False
    for y in range(image.height()):
        for x in range(image.width()):
            pixel = image.pixelColor(x, y)
            if pixel.alpha() < 160:
                continue
            seen = True
            channels = zip(pixel.getRgb()[:3], want.getRgb()[:3], strict=True)
            if any(abs(a - b) > 3 for a, b in channels):
                return False
    return seen


# --- the bundled Fluent UI System Icons --------------------------------------------------


def _small(file: str) -> str:
    return file.replace("_20_", "_16_", 1)


def test_every_glyph_has_a_bundled_fluent_icon():
    assert set(icons.FLUENT) == set(icons.GLYPHS)
    for name, file in icons.FLUENT.items():
        for stem, side in ((file, 20), (_small(file), 16)):
            path = resource_path("icons", "fluent", f"{stem}.svg")
            if side == 16 and not path.exists():
                continue  # no 16 px design: the 20 px one is scaled down
            assert path.is_file(), name
            svg = path.read_text(encoding="utf-8")
            pattern = rf'<svg [^>]*viewBox="0 0 {side} {side}">(<path [^>]+/>)+</svg>\n'
            assert re.fullmatch(pattern, svg), stem


def test_the_icon_folder_holds_exactly_the_icons_in_use_and_their_licence():
    folder = resource_path("icons", "fluent")
    files = {p.name for p in folder.iterdir()}
    used = {f"{f}.svg" for f in icons.FLUENT.values()}
    assert used <= files
    assert files - used <= {f"{_small(f)}.svg" for f in icons.FLUENT.values()} | {"LICENSE.txt"}
    assert len(files - used) > 0.9 * len(used)  # nearly every icon has its 16 px design
    licence = (folder / "LICENSE.txt").read_text(encoding="utf-8")
    assert "MIT License" in licence and "Microsoft Corporation" in licence


def test_bold_and_italic_use_the_fluent_letters_of_each_language():
    for language in ("pt_BR", "es", "fr", "de", "it", "ru", "ko"):
        bold, italic = icons.format_glyphs(language)
        assert icons.FLUENT[bold].startswith("text_bold_20_regular")
        assert icons.FLUENT[italic].startswith("text_italic_20_regular")
    assert icons.FLUENT["bold_n"] != icons.FLUENT["bold"]  # N de negrito, not a B


@pytest.mark.usefixtures("no_icon_font")
def test_fluent_icons_draw_in_the_requested_colour_at_every_ratio():
    for name in icons.GLYPHS:
        for ratio in (1.0, 1.25, 1.5, 2.0):
            pixmap = icons._pixmap(name, "#c42b1c", 20, ratio)
            assert pixmap.width() == round(20 * ratio), name
            assert _drawn_in(pixmap.toImage(), "#c42b1c"), (name, ratio)


@pytest.mark.usefixtures("no_icon_font")
def test_icons_keep_their_modes_and_add_a_sharp_16_px_size():
    t = theme.current()
    result = icons.icon("add")
    assert {QSize(16, 16), QSize(20, 20)} <= set(result.availableSizes())
    for mode, colour in (
        (QIcon.Mode.Normal, t.text),
        (QIcon.Mode.Disabled, t.text_muted),
        (QIcon.Mode.Active, t.text),
        (QIcon.Mode.Selected, t.accent),
    ):
        image = result.pixmap(QSize(20, 20), 1.0, mode).toImage()
        assert _drawn_in(image, colour), mode
    tinted = icons.icon("add", "#0f7b0f").pixmap(QSize(16, 16), 2.0).toImage()
    assert tinted.width() == 32
    assert _drawn_in(tinted, "#0f7b0f")


@pytest.mark.usefixtures("no_icon_font")
def test_fluent_icons_fill_the_box_like_the_windows_glyphs():
    """The font draws glyphs at 0.8 x the icon size: a 20 px icon keeps a 2 px margin."""
    for size, design in ((20, "add_20_regular"), (16, "add_16_regular")):
        assert icons._source("add", "", size < icons.SMALL)[0].stem == design
        image = icons._pixmap("add", "#000000", size, 1.0).toImage()
        columns = [
            x for x in range(size) if any(image.pixelColor(x, y).alpha() > 128 for y in range(size))
        ]
        margin = size // 10
        assert columns[0] >= margin and columns[-1] <= size - 1 - margin, size


# --- the desktop's symbolic icons ---------------------------------------------------------


def _theme(root, name, icons_by_file, inherits=""):
    folder = root / name
    (folder / "symbolic" / "actions").mkdir(parents=True)
    (folder / "index.theme").write_text(
        f"[Icon Theme]\nName={name}\nInherits={inherits}\nDirectories=symbolic/actions\n\n"
        "[symbolic/actions]\nContext=Actions\nSize=16\nType=Scalable\n",
        encoding="utf-8",
    )
    for file, body in icons_by_file.items():
        (folder / "symbolic" / "actions" / file).write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">{body}</svg>',
            encoding="utf-8",
        )
    return folder / "symbolic" / "actions"


@pytest.fixture
def icon_themes(tmp_path, monkeypatch, no_icon_font):
    root = tmp_path / "share" / "icons"
    monkeypatch.setenv("XDG_DATA_DIRS", str(tmp_path / "share"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(QIcon, "themeSearchPaths", staticmethod(lambda: [":/icons"]))
    folders = {
        "ZtSymbolic": _theme(
            root, "ZtSymbolic", {"list-add-symbolic.svg": GREY}, inherits="ZtParent"
        ),
        "ZtParent": _theme(
            root,
            "ZtParent",
            {"edit-find-symbolic.svg": GREY, "user-trash-symbolic.svg": GREY},
            inherits="ZtSymbolic,hicolor",  # a loop, and the shared fallback theme
        ),
        "hicolor": _theme(root, "hicolor", {"edit-copy-symbolic.svg": GREY}),
        "ZtColour": _theme(root, "ZtColour", {"list-add-symbolic.svg": RAINBOW}),
        "ZtPlain": _theme(root, "ZtPlain", {"list-add.svg": GREY, "edit-find.svg": GREY}),
    }
    icons.clear_cache()
    return folders


def _is_fluent(source):
    return source is not None and source[0].parent == resource_path("icons", "fluent")


def test_the_themes_symbolic_icons_come_first(icon_themes):
    add = icons._source("add", "ZtSymbolic")
    assert add == (icon_themes["ZtSymbolic"] / "list-add-symbolic.svg", icons.GLYPH_SCALE)
    # inherited themes count, in order
    assert icons._source("search", "ZtSymbolic")[0].parent == icon_themes["ZtParent"]
    assert icons._source("delete", "ZtSymbolic")[0].name == "user-trash-symbolic.svg"
    # hicolor is where applications drop their own icons: not a design to follow
    assert _is_fluent(icons._source("copy", "ZtSymbolic"))
    # no symbolic icon of that meaning: the Fluent one
    assert _is_fluent(icons._source("tag", "ZtSymbolic"))


def test_full_colour_and_non_symbolic_icons_fall_through_to_fluent(icon_themes):
    assert _is_fluent(icons._source("add", "ZtColour"))
    assert _is_fluent(icons._source("add", "ZtPlain"))  # list-add without -symbolic
    assert _is_fluent(icons._source("search", "ZtPlain"))
    assert _is_fluent(icons._source("add", "NoSuchTheme"))
    assert _is_fluent(icons._source("add", ""))


def test_symbolic_icons_are_tinted_like_the_glyphs(icon_themes):
    QIcon.setThemeName("ZtSymbolic")
    icons.clear_cache()
    image = icons.icon("add", "#0f7b0f").pixmap(QSize(20, 20), 1.5).toImage()
    assert _drawn_in(image, "#0f7b0f")
    # drawn in the middle 0.8 of the box, like the glyphs
    rows = [y for y in range(30) if any(image.pixelColor(x, y).alpha() > 128 for x in range(30))]
    columns = [x for x in range(30) if any(image.pixelColor(x, y).alpha() > 128 for y in range(30))]
    assert columns[0] >= 3 and columns[-1] <= 26 and rows  # 0.8 x 30 px, centred


def test_the_16_px_design_wins_whatever_the_order_of_the_themes_folders(icon_themes, tmp_path):
    """Breeze lists actions/32 before places/16, and both have folder-symbolic: the 16 px design
    is the one drawn at icon sizes, as the icon theme spec's size matching would pick it."""
    folder = tmp_path / "share" / "icons" / "ZtSizes"
    sections = {"actions/32": "Size=32\nType=Fixed", "places/16": "Size=16\nType=Fixed"}
    sections["actions/16@2x"] = "Size=16\nScale=2\nType=Fixed"
    sections["odd/8"] = "Size=eight"  # a broken entry is searched last, not an error
    index = "[Icon Theme]\nName=ZtSizes\nDirectories=odd/8,actions/32,places/16\n"
    index += "ScaledDirectories=actions/16@2x\n"
    for subdir, keys in sections.items():
        (folder / subdir).mkdir(parents=True)
        (folder / subdir / "folder-symbolic.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">{GREY}</svg>',
            encoding="utf-8",
        )
        index += f"\n[{subdir}]\n{keys}\n"
    (folder / "index.theme").write_text(index, encoding="utf-8")
    icons.clear_cache()
    assert icons._source("folder", "ZtSizes")[0] == folder / "places" / "16" / "folder-symbolic.svg"
    order = [p.relative_to(folder).as_posix() for p in icons._theme_index("ZtSizes")[0]]
    assert order == ["places/16", "actions/16@2x", "actions/32", "odd/8"]


def test_an_icon_linked_to_one_of_another_meaning_is_not_used(icon_themes):
    """Breeze's checkbox-checked-symbolic links to its pencil: the checklist button would show
    the Edit icon. A link between two names of one meaning (trash, delete) is fine."""
    folder = icon_themes["ZtSymbolic"]
    for real in ("document-edit-symbolic.svg", "edit-delete-symbolic.svg"):
        (folder / real).write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">{GREY}</svg>',
            encoding="utf-8",
        )
    try:
        (folder / "checkbox-checked-symbolic.svg").symlink_to("document-edit-symbolic.svg")
    except OSError:
        pytest.skip("no symbolic links here")
    (folder / "user-trash-symbolic.svg").symlink_to("edit-delete-symbolic.svg")
    icons.clear_cache()
    assert icons._source("edit", "ZtSymbolic")[0] == folder / "document-edit-symbolic.svg"
    assert _is_fluent(icons._source("checklist", "ZtSymbolic"))
    assert icons._source("trash", "ZtSymbolic")[0] == folder / "user-trash-symbolic.svg"


# --- icons painted into views (no text glyph on Linux) -------------------------------------


@pytest.mark.usefixtures("no_icon_font")
def test_paint_draws_the_icon_where_the_text_glyph_is_missing():
    assert icons.glyph("link") == ""
    image = QImage(64, 64, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.scale(2, 2)  # a zoomed view: the icon is drawn for that scale
    icons.paint(painter, "link", QRectF(0, 0, 32, 32), QColor("#005fb8"), 12)
    painter.end()
    assert _drawn_in(image, "#005fb8")
    # a 12 px glyph fills 15 px of a 0.8 icon box: 30 device pixels at twice the size, centred
    drawn = [x for x in range(64) if any(image.pixelColor(x, y).alpha() > 128 for y in range(64))]
    assert 17 <= drawn[0] and drawn[-1] <= 47 and drawn[-1] - drawn[0] > 20


@pytest.mark.usefixtures("no_icon_font")
def test_mind_map_nodes_linked_to_a_note_show_the_link_icon(monkeypatch):
    from zettelapp.ui import mindmap

    view = mindmap.MindMapView()
    view.set_mindmap(
        {
            "id": "r",
            "text": "Root",
            "children": [
                {"id": "a", "text": "Linked", "note": "20260101000000", "children": []},
                {"id": "b", "text": "Plain", "children": []},
            ],
        }
    )

    def paint_node(node_id: str) -> tuple[QImage, QRectF]:
        item = view.node_items[node_id]
        image = QImage(int(item.rect.width()), int(item.rect.height()), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        painter.translate(-item.rect.left(), -item.rect.top())
        item.paint(painter, None)
        painter.end()
        return image, item.rect

    calls = []
    real_paint = icons.paint
    monkeypatch.setattr(
        icons, "paint", lambda *args: (calls.append(args[1:]), real_paint(*args))[1]
    )
    image, rect = paint_node("a")
    assert [c[0] for c in calls] == ["link"]
    # the icon sits at the node's right end, after the text, in the text colour
    area = image.copy(int(rect.width()) - 28, 0, 16, image.height())
    dark = [
        (x, y)
        for y in range(area.height())
        for x in range(area.width())
        if area.pixelColor(x, y).lightness() < 140 and area.pixelColor(x, y).saturation() < 40
    ]
    assert len(dark) > 10
    calls.clear()
    paint_node("b")
    assert calls == []


# --- fonts --------------------------------------------------------------------------------


def test_the_desktops_fonts_come_first_with_the_fallbacks_after():
    ui, code = theme.desktop_font_lists("xcb", "Cantarell", "Hack")
    assert ui[0] == "Cantarell" and ui.count("Cantarell") == 1
    assert ui[1:] == [f for f in theme._FALLBACK_FONTS[0] if f != "Cantarell"]
    assert code[0] == "Hack" and code[1:] == list(theme._FALLBACK_FONTS[1])
    # no desktop (tests, screenshots): the fallback lists as they are
    assert theme.desktop_font_lists("offscreen", "Sans Serif", "DejaVu Sans Mono") == (
        list(theme._FALLBACK_FONTS[0]),
        list(theme._FALLBACK_FONTS[1]),
    )


@_linux
def test_linux_adopts_the_font_the_desktop_reports(app, monkeypatch):
    from PySide6.QtGui import QFontDatabase, QGuiApplication

    reported = {
        QFontDatabase.SystemFont.GeneralFont: QFont("Liberation Sans", 11),
        QFontDatabase.SystemFont.FixedFont: QFont("Liberation Mono", 10),
    }
    monkeypatch.setattr(QGuiApplication, "platformName", staticmethod(lambda: "xcb"))
    monkeypatch.setattr(QFontDatabase, "systemFont", staticmethod(lambda kind: reported[kind]))
    saved = list(theme.UI_FONTS), list(theme.CODE_FONTS)
    try:
        theme.adopt_desktop_fonts()
        assert theme.UI_FONTS[0] == "Liberation Sans"
        assert theme.ITALIC_FONTS is theme.UI_FONTS  # italics in the same family
        assert theme.ui_font(10).pointSizeF() == 10  # the app's own sizes, not the desktop's
        if "Liberation Mono" in QFontDatabase.families():
            assert theme.CODE_FONTS[0] == "Liberation Mono"
            assert QFont.substitutes("monospace")[0] == "liberation mono"
    finally:
        theme.UI_FONTS[:], theme.CODE_FONTS[:] = saved
        QFont.removeSubstitutions("monospace")
        QFont.insertSubstitutions("monospace", theme.CODE_FONTS)


@_linux
def test_code_in_the_preview_uses_a_monospace_font(app):
    from PySide6.QtGui import QTextDocument

    from zettelapp.ui.preview import preview_css

    theme.apply_theme(app, "light")
    if not any(QFontInfo(QFont(f)).fixedPitch() for f in theme.CODE_FONTS):
        pytest.skip("no monospace font installed")
    doc = QTextDocument()
    doc.setDefaultStyleSheet(preview_css())
    doc.setHtml("<p>text <code>code</code></p><pre>block</pre>")
    fonts = {}
    block = doc.begin()
    while block.isValid():
        it = block.begin()
        while not it.atEnd():
            fragment = it.fragment()
            fonts[fragment.text().strip()] = QFontInfo(fragment.charFormat().font())
            it += 1
        block = block.next()
    assert fonts["code"].fixedPitch() and fonts["block"].fixedPitch()
    assert not fonts["text"].fixedPitch()


@_linux
def test_formulas_use_a_serif_and_a_maths_font_installed_on_linux(app):
    from zettelapp.ui import mathrender

    installed = set(QFontDatabase_families())
    if not installed & set(mathrender.FAMILIES):
        pytest.skip("none of the maths fonts is installed")
    font = mathrender.Style(16.0).font()
    assert QFontInfo(font).family() in mathrender.FAMILIES
    tt = mathrender.Style(16.0, "tt").font()
    assert QFontInfo(tt).fixedPitch() or not any(
        QFontInfo(QFont(f)).fixedPitch() for f in theme.CODE_FONTS
    )
    rendered = mathrender.render(r"\sum_{i=1}^{n} x_i \to \int_0^\infty f(x)\,dx \leq \alpha")
    assert rendered.ok and rendered.image.width() > 40


def test_graphviz_exports_fall_back_to_sans_serif_without_segoe_ui(vault, sample, monkeypatch):
    from zettelapp.core import export

    bundle = export.collect(vault, {n.id for n in vault.all_notes()})
    font = 'fontname="Segoe UI,sans-serif"'
    if sys.platform != "win32":  # an SVG viewer would draw a missing Segoe UI in serif
        assert export._dot(bundle, "Test").count(font) == 3
    monkeypatch.setattr(export, "_DOT_FONT", "Segoe UI")  # Windows: the export it always gave
    header = export._dot(bundle, "Test").splitlines()[1:4]
    assert header == [
        '  graph [overlap=false, splines=true, fontname="Segoe UI"];',
        '  node [shape=box, style="rounded,filled", fillcolor="#eef3fb", color="#0f6cbd", '
        'fontname="Segoe UI"];',
        '  edge [fontname="Segoe UI", fontsize=9];',
    ]


def QFontDatabase_families():  # noqa: N802 - reads like the Qt call it wraps
    from PySide6.QtGui import QFontDatabase

    return QFontDatabase.families()


def test_link_is_always_the_bundled_chain():
    """GNOME's insert-link-symbolic is not a chain; the link icon never comes from the theme."""
    from zettelapp.ui import icons

    assert "link" not in icons.NATIVE
    assert icons.FLUENT["link"] == "link_20_regular"
