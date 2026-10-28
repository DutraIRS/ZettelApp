"""Draw the ZettelApp icon and write the .ico/.png files used by the app, installer and website.

Run with:  python tools/make_icon.py
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath, QPen

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "zettelapp" / "resources"
SITE = ROOT / "website" / "assets"
ICO_SIZES = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]

NODES = [(0.30, 0.36), (0.70, 0.30), (0.64, 0.71), (0.30, 0.68)]
EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]


def draw(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = float(size)
    inset = s * 0.04
    tile = QRectF(inset, inset, s - 2 * inset, s - 2 * inset)
    gradient = QLinearGradient(tile.topLeft(), tile.bottomRight())
    gradient.setColorAt(0.0, QColor("#3987e5"))
    gradient.setColorAt(1.0, QColor("#5a3fd0"))
    path = QPainterPath()
    path.addRoundedRect(tile, s * 0.22, s * 0.22)
    p.fillPath(path, gradient)
    # A subtle highlight on the upper half gives the tile some depth.
    shine = QLinearGradient(tile.topLeft(), QPointF(tile.left(), tile.center().y()))
    shine.setColorAt(0, QColor(255, 255, 255, 46))
    shine.setColorAt(1, QColor(255, 255, 255, 0))
    p.fillPath(path, shine)

    white = QColor("#ffffff")
    pen = QPen(white, max(1.0, s * 0.05), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    pts = [QPointF(tile.left() + x * tile.width(), tile.top() + y * tile.height()) for x, y in NODES]
    for a, b in EDGES:
        p.drawLine(pts[a], pts[b])
    p.setPen(Qt.PenStyle.NoPen)
    for i, pt in enumerate(pts):
        r = s * (0.105 if i == 1 else 0.085)
        p.setBrush(QColor("#ffd166") if i == 1 else white)
        p.drawEllipse(pt, r, r)
    p.end()
    return image


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
    print("Icons written to", RESOURCES, "and", SITE)


if __name__ == "__main__":
    main()
