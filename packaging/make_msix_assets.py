"""Draw the MSIX package's logos (tiles, taskbar, Store) from the app icon.

Run with:  python packaging/make_msix_assets.py <folder>
Writes the scale and target-size variants Windows picks from; MakePri indexes them.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from make_icon import draw  # noqa: E402

# name -> (width, height, share of the shorter side the icon fills)
LOGOS = {
    "Square44x44Logo": (44, 44, 1.0),
    "Square150x150Logo": (150, 150, 0.66),
    "Wide310x150Logo": (310, 150, 0.66),
    "StoreLogo": (50, 50, 1.0),
}
SCALES = (100, 125, 150, 200, 400)
TARGET_SIZES = (16, 20, 24, 30, 32, 36, 40, 48, 60, 64, 72, 80, 96, 256)  # taskbar, Start, Explorer


def logo(width: int, height: int, share: float) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    side = round(min(width, height) * share)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.drawImage(QRect((width - side) // 2, (height - side) // 2, side, side), draw(side))
    painter.end()
    return image


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    QGuiApplication.instance() or QGuiApplication(["msix-assets"])
    for name, (width, height, share) in LOGOS.items():
        for scale in SCALES:
            image = logo(round(width * scale / 100), round(height * scale / 100), share)
            image.save(str(out / f"{name}.scale-{scale}.png"))
    for size in TARGET_SIZES:  # unplated: drawn straight on the taskbar, without a tile behind
        image = logo(size, size, 1.0)
        image.save(str(out / f"Square44x44Logo.targetsize-{size}.png"))
        image.save(str(out / f"Square44x44Logo.targetsize-{size}_altform-unplated.png"))
        image.save(str(out / f"Square44x44Logo.targetsize-{size}_altform-lightunplated.png"))
    print(f"MSIX logos written to {out}")


if __name__ == "__main__":
    main()
