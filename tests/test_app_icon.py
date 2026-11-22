"""The scalable app icon (icon.svg) must stay the same picture as the PNG and ICO files."""

from pathlib import Path

import pytest

pytest.importorskip("PySide6.QtSvg")

from tools import make_icon  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SVG_FILES = [
    ROOT / "zettelapp" / "resources" / "icon.svg",
    ROOT / "website" / "assets" / "icon.svg",
]


@pytest.fixture
def qapp():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(["test"])


def _pixels(image) -> bytes:
    from PySide6.QtGui import QImage

    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    return bytes(image.constBits())


def _render(size: int):
    from PySide6.QtCore import QByteArray, QRectF, Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    renderer = QSvgRenderer(QByteArray(SVG_FILES[0].read_bytes()))
    assert renderer.isValid()
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return image


@pytest.mark.parametrize("path", SVG_FILES, ids=lambda p: p.parent.name)
def test_svg_icon_is_up_to_date(path):
    """Run `python tools/make_icon.py` after changing the icon."""
    assert path.read_text(encoding="utf-8") == make_icon.svg(512)


def test_svg_icon_is_pixel_identical_to_the_png(qapp):
    from PySide6.QtGui import QImage

    png = QImage(str(ROOT / "website" / "assets" / "icon-512.png"))
    assert png.size().width() == 512
    assert _pixels(_render(512)) == _pixels(png)


@pytest.mark.parametrize("size", [64, 256, 1024])
def test_svg_icon_scales_like_the_drawn_icon(qapp, size):
    """At other sizes only anti-aliasing rounding may differ: one level on a few edge pixels."""
    rendered, drawn = _pixels(_render(size)), _pixels(make_icon.draw(size))
    differences = [abs(a - b) for a, b in zip(rendered, drawn) if a != b]
    assert max(differences, default=0) <= 1
    assert len(differences) <= size // 16
