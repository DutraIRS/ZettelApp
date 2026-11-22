"""Draw the ZettelApp icon and write the .ico/.png/.svg files used by the app, installer and website.

The SVG describes the same shapes, gradients and colours that draw() paints, so it scales to any
size: rendered by Qt at 512 px it is pixel-identical to icon-512.png (tests/test_app_icon.py).

Run with:  python tools/make_icon.py
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "zettelapp" / "resources"
SITE = ROOT / "website" / "assets"
ICO_SIZES = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]

NODES = [(0.30, 0.36), (0.70, 0.30), (0.64, 0.71), (0.30, 0.68)]
EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]

# Proportions of the icon size, and colours, shared by draw() and svg().
INSET = 0.04  # margin around the tile
CORNER = 0.22  # corner radius of the tile
STROKE = 0.05  # width of the links
NODE = 0.085  # radius of a note
HUB = 0.105  # radius of the highlighted note (NODES[1])
TILE_START, TILE_END = "#3987e5", "#5a3fd0"  # tile gradient, top left to bottom right
SHINE_ALPHA = 46  # white highlight over the upper half of the tile, fading out
WHITE, HUB_COLOUR = "#ffffff", "#ffd166"


def draw(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = float(size)
    inset = s * INSET
    tile = QRectF(inset, inset, s - 2 * inset, s - 2 * inset)
    gradient = QLinearGradient(tile.topLeft(), tile.bottomRight())
    gradient.setColorAt(0.0, QColor(TILE_START))
    gradient.setColorAt(1.0, QColor(TILE_END))
    path = QPainterPath()
    path.addRoundedRect(tile, s * CORNER, s * CORNER)
    p.fillPath(path, gradient)
    # A subtle highlight on the upper half gives the tile some depth.
    shine = QLinearGradient(tile.topLeft(), QPointF(tile.left(), tile.center().y()))
    shine.setColorAt(0, QColor(255, 255, 255, SHINE_ALPHA))
    shine.setColorAt(1, QColor(255, 255, 255, 0))
    p.fillPath(path, shine)

    white = QColor(WHITE)
    pen = QPen(white, max(1.0, s * STROKE), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    pts = [
        QPointF(tile.left() + x * tile.width(), tile.top() + y * tile.height()) for x, y in NODES
    ]
    for a, b in EDGES:
        p.drawLine(pts[a], pts[b])
    p.setPen(Qt.PenStyle.NoPen)
    for i, pt in enumerate(pts):
        r = s * (HUB if i == 1 else NODE)
        p.setBrush(QColor(HUB_COLOUR) if i == 1 else white)
        p.drawEllipse(pt, r, r)
    p.end()
    return image


def _num(value: float) -> str:
    """A coordinate for SVG: up to six decimals, no trailing zeros."""
    return f"{value:.6f}".rstrip("0").rstrip(".")


def svg(size: int = 512) -> str:
    """The icon as an SVG document with a size x size view box.

    Element for element it mirrors draw(): the same rounded tile and gradients, the links as
    separate round-capped lines (so their anti-aliased ends blend exactly as drawLine's do)
    and the notes on top, in the same order.
    """
    s = float(size)
    inset = s * INSET
    side = s - 2 * inset
    corner = _num(s * CORNER)
    pts = [(inset + x * side, inset + y * side) for x, y in NODES]
    tile = (
        f'x="{_num(inset)}" y="{_num(inset)}" width="{_num(side)}" height="{_num(side)}" '
        f'rx="{corner}" ry="{corner}"'
    )
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">',
        "<title>ZettelApp</title>",
        "<defs>",
        f'<linearGradient id="tile" gradientUnits="userSpaceOnUse" x1="{_num(inset)}" '
        f'y1="{_num(inset)}" x2="{_num(inset + side)}" y2="{_num(inset + side)}">'
        f'<stop offset="0" stop-color="{TILE_START}"/><stop offset="1" stop-color="{TILE_END}"/>'
        "</linearGradient>",
        f'<linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="{_num(inset)}" '
        f'y1="{_num(inset)}" x2="{_num(inset)}" y2="{_num(inset + side / 2)}">'
        f'<stop offset="0" stop-color="{WHITE}" stop-opacity="{_num(SHINE_ALPHA / 255)}"/>'
        f'<stop offset="1" stop-color="{WHITE}" stop-opacity="0"/></linearGradient>',
        "</defs>",
        f'<rect {tile} fill="url(#tile)"/>',
        f'<rect {tile} fill="url(#shine)"/>',
        f'<g stroke="{WHITE}" stroke-width="{_num(s * STROKE)}" stroke-linecap="round">',
    ]
    for a, b in EDGES:
        (x1, y1), (x2, y2) = pts[a], pts[b]
        lines.append(f'<line x1="{_num(x1)}" y1="{_num(y1)}" x2="{_num(x2)}" y2="{_num(y2)}"/>')
    lines.append("</g>")
    for i, (x, y) in enumerate(pts):
        r, colour = (s * HUB, HUB_COLOUR) if i == 1 else (s * NODE, WHITE)
        lines.append(f'<circle cx="{_num(x)}" cy="{_num(y)}" r="{_num(r)}" fill="{colour}"/>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def png_bytes(image: QImage) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(data)


def write_ico(path: Path, sizes: list[int]) -> None:
    images = [png_bytes(draw(size)) for size in sizes]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries, payload = b"", b""
    for size, data in zip(sizes, images):
        dim = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset + len(payload))
        payload += data
    path.write_bytes(header + entries + payload)


def main() -> None:
    QGuiApplication(sys.argv)
    RESOURCES.mkdir(parents=True, exist_ok=True)
    SITE.mkdir(parents=True, exist_ok=True)
    write_ico(RESOURCES / "icon.ico", ICO_SIZES)
    draw(256).save(str(RESOURCES / "icon-256.png"))
    draw(512).save(str(SITE / "icon-512.png"))
    draw(64).save(str(SITE / "favicon.png"))
    for folder in (RESOURCES, SITE):
        (folder / "icon.svg").write_text(svg(512), encoding="utf-8", newline="\n")
    print("Icons written to", RESOURCES, "and", SITE)


if __name__ == "__main__":
    main()
