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
    pixels = preview.fontInfo().pixelSize()
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
