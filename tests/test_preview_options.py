"""Options ▸ General ▸ Preview and Reading view: line breaks, alignment and spacing."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtGui import QTextBlockFormat  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from zettelapp import settings  # noqa: E402
from zettelapp.core.render import NoteRenderer  # noqa: E402

TEXT = "One line\nthe next line\n\n- an item\n\n$$x^2$$"


@pytest.fixture
def preview(tmp_path, monkeypatch):
    monkeypatch.setenv("ZETTELAPP_SETTINGS_FILE", str(tmp_path / "settings.ini"))
    QApplication.instance() or QApplication(["test"])
    from zettelapp.ui.preview import NotePreview, math_href

    shown = NotePreview(lambda name: None)
    shown.set_renderer(NoteRenderer(lambda target: None, math_href=math_href))
    yield shown
    shown.deleteLater()


def _blocks(preview):
    block, found = preview.document().begin(), []
    while block.isValid():
        found.append((block.text(), block.blockFormat()))
        block = block.next()
    return found


def test_the_defaults_keep_line_breaks_and_the_text_at_the_start(preview):
    preview.show_markdown(TEXT)
    first = _blocks(preview)[0]
    assert first[0] == "One line the next line"  # a line break inside the paragraph
    assert first[1].alignment() & 0xF in (0x1, 0x0)  # start (left), not justified
    assert first[1].lineHeight() == 125


def test_lines_can_join_and_paragraphs_be_justified_and_spaced(preview):
    settings.put(settings.PREVIEW_LINE_BREAKS, False)
    settings.put(settings.PREVIEW_ALIGN, "justify")
    settings.put(settings.PREVIEW_LINE_SPACING, 160)
    settings.put(settings.PREVIEW_PARAGRAPH_SPACING, 100)
    preview.show_markdown(TEXT)
    blocks = _blocks(preview)
    text, fmt = blocks[0]
    assert text == "One line the next line"  # standard Markdown: one paragraph
    assert int(fmt.alignment()) & 0x8  # justified
    assert fmt.lineHeight() == 160
    assert fmt.lineHeightType() == QTextBlockFormat.LineHeightTypes.ProportionalHeight.value
    pixels = preview.pixel_size()
    assert fmt.bottomMargin() == round(pixels * 1.0)
    item = next(f for t, f in blocks if t == "an item")
    assert int(item.alignment()) & 0x8
    formula = blocks[-1][1]  # a formula alone in its paragraph stays centred
    assert int(formula.alignment()) & 0x4


def test_justified_leaves_centred_paragraphs_alone():
    from zettelapp.ui.preview import justified

    html = '<p>a</p><p align="center" class="picture">b</p><ul><li>c</li></ul>'
    assert justified(html) == (
        '<p align="justify">a</p><p align="center" class="picture">b</p>'
        '<ul><li align="justify">c</li></ul>'
    )


def test_a_wide_picture_fits_the_reading_column(tmp_path, monkeypatch):
    """Pictures were scaled to the viewport, not to the text's column: in Reading view a wide one
    stuck out of the column and the preview scrolled sideways."""
    monkeypatch.setenv("ZETTELAPP_SETTINGS_FILE", str(tmp_path / "settings.ini"))
    QApplication.instance() or QApplication(["test"])
    from PySide6.QtGui import QColor, QImage

    from zettelapp.ui.preview import NotePreview, math_href

    name = "0123456789abcdef0123.png"
    picture = QImage(1600, 400, QImage.Format.Format_RGB32)
    picture.fill(QColor("#2a6fdb"))
    picture.save(str(tmp_path / name))
    shown = NotePreview(lambda asset: tmp_path / asset if asset == name else None)
    shown.set_renderer(NoteRenderer(lambda target: None, math_href=math_href))
    shown.resize(560, 500)
    shown.show()
    for reading in (True, False):
        shown.set_reading(reading)
        shown.show_markdown(f"Text.\n\n![wide](asset:{name})\n")
        shown.document().adjustSize()
        assert shown.document().idealWidth() <= shown.viewport().width()
        assert shown.horizontalScrollBar().maximum() == 0
    shown.deleteLater()


def test_pictures_follow_the_columns_width(tmp_path, monkeypatch):
    """A picture kept the size it was loaded at: switching to Reading view (whose column is wider)
    or resizing the window left it sized for the old layout."""
    monkeypatch.setenv("ZETTELAPP_SETTINGS_FILE", str(tmp_path / "settings.ini"))
    QApplication.instance() or QApplication(["test"])
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QColor, QImage, QTextDocument
    from PySide6.QtTest import QTest

    from zettelapp.ui.preview import NotePreview, math_href

    name = "0123456789abcdef0123.png"
    picture = QImage(1600, 400, QImage.Format.Format_RGB32)
    picture.fill(QColor("#2a6fdb"))
    picture.save(str(tmp_path / name))
    shown = NotePreview(lambda asset: tmp_path / asset if asset == name else None)
    shown.set_renderer(NoteRenderer(lambda target: None, math_href=math_href))
    shown.resize(300, 400)
    shown.show()
    shown.show_markdown(f"![wide](asset:{name})\n")
    shown.document().adjustSize()

    def width():
        url = QUrl(f"asset:{name}")
        return (
            shown.document().resource(QTextDocument.ResourceType.ImageResource.value, url).width()
        )

    assert width() == shown.column_width()
    shown.resize(800, 400)
    QTest.qWait(300)
    shown.document().adjustSize()
    assert width() == shown.column_width() > 600
    shown.deleteLater()
