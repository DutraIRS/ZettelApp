"""Vector drawings for every icon, used where the Windows icon fonts are absent.

On Linux (and anywhere without *Segoe Fluent Icons* / *Segoe MDL2 Assets*),
each glyph is drawn with QPainter primitives in a 24x24 box, stroke-based in
the Fluent line style. This keeps the whole icon set available on any desktop,
in any sandbox, at any DPI, always in the theme's colour — no icon theme or
font is needed. Letter glyphs (Bold/Italic) use the UI font's own letters,
like Word does.
"""

from __future__ import annotations

from math import cos, radians, sin

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF

# Each icon is a list of primitives in a 24x24 box:
#   ("l", points)                polyline, stroked
#   ("c", cx, cy, r)             circle, stroked
#   ("cf", cx, cy, r)            filled circle
#   ("r", x, y, w, h)            rounded rectangle, stroked
#   ("rf", x, y, w, h)           filled rounded rectangle
#   ("a", x, y, w, h, a1, a2)    arc (degrees, counter-clockwise from 3 o'clock)
#   ("t", char, weight, italic)  a letter of the UI font, centred
#   ("tri", points)              filled triangle
SHAPES: dict[str, list] = {}


def _gear_spokes() -> list[list[list[float]]]:
    """Eight spokes around the centre, each a two-point polyline."""
    spokes = []
    for step in range(8):
        angle = step * 45.0
        x1 = 12 + 5.9 * cos(radians(angle))
        y1 = 12 - 5.9 * sin(radians(angle))
        x2 = 12 + 8.4 * cos(radians(angle))
        y2 = 12 - 8.4 * sin(radians(angle))
        spokes.append([[round(x1, 2), round(y1, 2)], [round(x2, 2), round(y2, 2)]])
    return spokes


_TRASH = [
    ("l", [(9, 5), (15, 5)]),
    ("l", [(5, 7.5), (19, 7.5)]),
    ("l", [(7.5, 7.5), (7.5, 19), (16.5, 19), (16.5, 7.5)]),
    ("l", [(10.5, 10.5), (10.5, 16.5)]),
    ("l", [(13.5, 10.5), (13.5, 16.5)]),
]
_REFRESH = [
    ("a", 5, 5, 14, 14, 40, 290),
    ("l", [(19.3, 3.9), (19.5, 8.6), (15.2, 8.2)]),
]
SHAPES.update(
    {
        "add": [("l", [(12, 5), (12, 19)]), ("l", [(5, 12), (19, 12)])],
        "cancel": [("l", [(6.5, 6.5), (17.5, 17.5)]), ("l", [(17.5, 6.5), (6.5, 17.5)])],
        "settings": [("c", 12, 12, 3.6), *(("l", s) for s in _gear_spokes())],
        "search": [("c", 10.5, 10.5, 5.5), ("l", [(14.6, 14.6), (20, 20)])],
        "delete": _TRASH,
        "trash": _TRASH,
        "save": [
            ("l", [(5, 5), (14.5, 5), (19, 9.5), (19, 19), (5, 19), (5, 5)]),
            ("r", 8.5, 13, 7, 6),
            ("r", 12.5, 5.8, 4, 3.4),
        ],
        "edit": [
            ("l", [(3, 21), (6.75, 21), (17.8, 9.9), (14.1, 6.2), (3, 17.2), (3, 21)]),
            ("l", [(16.2, 3.9), (20.1, 7.8)]),
        ],
        "link": [
            ("a", 5, 11, 8, 8, 90, 180),
            ("a", 11, 5, 8, 8, 270, 180),
            ("l", [(9.5, 14.5), (14.5, 9.5)]),
        ],
        "tag": [
            ("l", [(11, 3.5), (20.5, 13), (12.8, 20.7), (3.5, 11.4), (3.5, 3.5), (11, 3.5)]),
            ("cf", 7.2, 7.2, 1.3),
        ],
        "image": [
            ("r", 3.5, 4.5, 17, 15),
            ("cf", 8.3, 9, 1.5),
            ("l", [(5.5, 16.5), (10, 12), (13.5, 15.5), (16, 13), (18.5, 15.8)]),
        ],
        "share": [
            ("cf", 6, 12, 2),
            ("cf", 17.5, 6, 2),
            ("cf", 17.5, 18, 2),
            ("l", [(7.8, 11), (15.7, 7.1)]),
            ("l", [(7.8, 13), (15.7, 16.9)]),
        ],
        "export": [
            ("l", [(4, 14.5), (4, 19.5), (20, 19.5), (20, 14.5)]),
            ("l", [(12, 13.5), (12, 4)]),
            ("l", [(8.5, 7.5), (12, 4), (15.5, 7.5)]),
        ],
        "import": [
            ("l", [(4, 14.5), (4, 19.5), (20, 19.5), (20, 14.5)]),
            ("l", [(12, 4), (12, 13.5)]),
            ("l", [(8.5, 10), (12, 13.5), (15.5, 10)]),
        ],
        "help": [("t", "?", 700, False)],
        "info": [("c", 12, 12, 8.3), ("cf", 12, 8, 1.3), ("l", [(12, 11.3), (12, 16.3)])],
        "notes": [
            ("r", 6.5, 3.5, 11, 17),
            ("l", [(9.2, 8), (14.8, 8)]),
            ("l", [(9.2, 11.5), (14.8, 11.5)]),
            ("l", [(9.2, 15), (12.8, 15)]),
        ],
        "review": [("c", 12, 12, 8.3), ("l", [(8, 12.2), (10.9, 15.1), (16.2, 9.4)])],
        "folder": [
            (
                "l",
                [
                    (3.5, 18.5),
                    (3.5, 6),
                    (9.5, 6),
                    (11.5, 8.5),
                    (20.5, 8.5),
                    (20.5, 18.5),
                    (3.5, 18.5),
                ],
            )
        ],
        "open": [
            ("l", [(3.5, 18.5), (3.5, 6), (9.5, 6), (11.5, 8.5), (17, 8.5)]),
            ("l", [(12, 17.5), (12, 11.5)]),
            ("l", [(9.5, 14), (12, 11.5), (14.5, 14)]),
        ],
        "refresh": _REFRESH,
        "check": [("l", [(5, 12.5), (10, 17.5), (19, 7)])],
        "document": [
            ("l", [(6.5, 20.5), (6.5, 3.5), (14, 3.5), (17.5, 7), (17.5, 20.5), (6.5, 20.5)]),
            ("l", [(14, 3.5), (14, 7), (17.5, 7)]),
        ],
        "globe": [
            ("c", 12, 12, 8.3),
            ("a", 8, 3.7, 8, 16.6, 0, 360),
            ("l", [(3.7, 12), (20.3, 12)]),
            ("a", 4.3, 5.8, 15.4, 4, 20, 140),
            ("a", 4.3, 14.2, 15.4, 4, 200, 140),
        ],
        "lightbulb": [
            ("c", 12, 10, 5.4),
            ("l", [(10.3, 15.5), (13.7, 15.5)]),
            ("l", [(9.5, 17.7), (14.5, 17.7)]),
            ("l", [(10.2, 19.8), (13.8, 19.8)]),
        ],
        "zoom_in": [
            ("c", 10.5, 10.5, 5.5),
            ("l", [(10.5, 8), (10.5, 13)]),
            ("l", [(8, 10.5), (13, 10.5)]),
            ("l", [(14.6, 14.6), (20, 20)]),
        ],
        "zoom_out": [
            ("c", 10.5, 10.5, 5.5),
            ("l", [(8, 10.5), (13, 10.5)]),
            ("l", [(14.6, 14.6), (20, 20)]),
        ],
        "fit": [
            ("l", [(4, 9), (4, 4), (9, 4)]),
            ("l", [(15, 4), (20, 4), (20, 9)]),
            ("l", [(20, 15), (20, 20), (15, 20)]),
            ("l", [(9, 20), (4, 20), (4, 15)]),
        ],
        "sync": [
            ("a", 5, 6, 14, 12, -150, 130),
            ("l", [(19.4, 4.2), (19.2, 8.9), (14.9, 8.3)]),
            ("a", 5, 6, 14, 12, 30, 130),
            ("l", [(4.6, 19.8), (4.8, 15.1), (9.1, 15.7)]),
        ],
        "more": [("cf", 5, 12, 1.6), ("cf", 12, 12, 1.6), ("cf", 19, 12, 1.6)],
        "undo": [
            ("a", 5.5, 6.5, 13, 12, 180, 180),
            ("l", [(4.6, 8.2), (4.9, 4.2), (9, 4.6)]),
        ],
        "history": [
            ("c", 12, 12.5, 7.5),
            ("l", [(12, 8.5), (12, 12.5), (15.2, 14.3)]),
            ("l", [(3.6, 10.8), (3.6, 6.8), (7.6, 6.4)]),
        ],
        "chat": [
            (
                "l",
                [(4, 5), (20, 5), (20, 15.5), (12, 15.5), (8, 19.3), (8, 15.5), (4, 15.5), (4, 5)],
            )
        ],
        "view": [
            ("a", 4, 6, 16, 12, 0, 180),
            ("a", 4, 6, 16, 12, 180, 180),
            ("cf", 12, 12, 2.6),
        ],
        "filter": [
            ("l", [(4, 5.5), (20, 5.5), (14, 12.5), (14, 18.8), (10, 16.5), (10, 12.5), (4, 5.5)])
        ],
        "accept": [
            ("l", [(4.5, 11.5), (9.5, 16.5), (19.5, 6)]),
            ("l", [(7, 19.5), (17, 19.5)]),
        ],
        "clear": [("l", [(7, 7), (17, 17)]), ("l", [(17, 7), (7, 17)])],
    }
)

SHAPES.update(
    {
        "bullets": [
            ("cf", 5, 7, 1.4),
            ("cf", 5, 12, 1.4),
            ("cf", 5, 17, 1.4),
            ("l", [(9, 7), (19, 7)]),
            ("l", [(9, 12), (19, 12)]),
            ("l", [(9, 17), (19, 17)]),
        ],
        "bold": [("t", "B", 700, False)],
        "italic": [("t", "I", 400, True)],
        "heading": [("t", "H", 700, False)],
        "code": [
            ("l", [(8.5, 7.5), (4.5, 12), (8.5, 16.5)]),
            ("l", [(15.5, 7.5), (19.5, 12), (15.5, 16.5)]),
            ("l", [(13.4, 6), (10.6, 18)]),
        ],
        "key": [
            ("c", 8, 12, 3.6),
            ("cf", 8, 12, 1.2),
            ("l", [(11.6, 12), (20, 12)]),
            ("l", [(16.8, 12), (16.8, 15)]),
            ("l", [(19.6, 12), (19.6, 14.6)]),
        ],
        "shield": [
            (
                "l",
                [(12, 3.5), (19.5, 6.4), (19.5, 12), (12, 20.5), (4.5, 12), (4.5, 6.4), (12, 3.5)],
            ),
            ("l", [(8.8, 11.6), (11.2, 14), (15.4, 9.6)]),
        ],
        "cube": [
            (
                "l",
                [
                    (12, 3.5),
                    (19.5, 7.8),
                    (19.5, 16.2),
                    (12, 20.5),
                    (4.5, 16.2),
                    (4.5, 7.8),
                    (12, 3.5),
                ],
            ),
            ("l", [(4.5, 7.8), (12, 12), (19.5, 7.8)]),
            ("l", [(12, 12), (12, 20.5)]),
        ],
        "send": [
            ("l", [(3.5, 12), (20.5, 4), (14.9, 20), (11.4, 13.9), (3.5, 12)]),
            ("l", [(11.4, 13.9), (20.5, 4)]),
        ],
        "copy": [("r", 8.5, 8.5, 11, 11), ("l", [(15.5, 4.5), (4.5, 4.5), (4.5, 15.5)])],
        "insights": [
            ("l", [(6, 18.5), (6, 12.5)]),
            ("l", [(12, 18.5), (12, 5.5)]),
            ("l", [(18, 18.5), (18, 9.5)]),
            ("l", [(4, 20.5), (20, 20.5)]),
        ],
        "group": [("c", 9, 9.5, 4.6), ("c", 15, 14.5, 4.6)],
        "pin": [
            ("l", [(12, 20.5), (7, 13.5), (7, 9), (12, 3.8), (17, 9), (17, 13.5), (12, 20.5)]),
            ("cf", 12, 9.3, 1.5),
        ],
        "back": [("l", [(14.5, 5), (7.5, 12), (14.5, 19)])],
        "rotate": [
            ("a", 5, 5, 14, 14, 20, 290),
            ("l", [(17.6, 4.3), (18.9, 8.6), (14.7, 9.5)]),
        ],
        "relationship": [
            ("cf", 6, 18, 2.4),
            ("cf", 18, 6, 2.4),
            ("l", [(7.7, 16.3), (16.3, 7.7)]),
        ],
        "graph": [
            ("cf", 12, 12, 1.9),
            ("cf", 5.5, 5.5, 2),
            ("cf", 19, 6.5, 2),
            ("cf", 6, 18.5, 2),
            ("cf", 18.5, 18, 2),
            ("l", [(12, 12), (5.5, 5.5)]),
            ("l", [(12, 12), (19, 6.5)]),
            ("l", [(12, 12), (6, 18.5)]),
            ("l", [(12, 12), (18.5, 18)]),
        ],
        "cluster": [("c", 9, 9.5, 4.2), ("c", 15, 9.5, 4.2), ("c", 12, 14.5, 4.2)],
    }
)

SHAPES.update(
    {
        "cards": [("r", 8.5, 8, 12, 12), ("l", [(6, 8), (6, 17.5), (18.5, 17.5)])],
        "server": [
            ("r", 4, 4.5, 16, 5.5),
            ("r", 4, 14, 16, 5.5),
            ("cf", 6.6, 7.2, 1),
            ("cf", 6.6, 16.8, 1),
            ("l", [(13, 7.2), (17, 7.2)]),
            ("l", [(13, 16.8), (17, 16.8)]),
        ],
        "star": [
            (
                "l",
                [
                    (12, 3.9),
                    (14.4, 9.1),
                    (20.1, 9.6),
                    (15.8, 13.4),
                    (17.1, 19),
                    (12, 16.1),
                    (6.9, 19),
                    (8.2, 13.4),
                    (3.9, 9.6),
                    (9.6, 9.1),
                    (12, 3.9),
                ],
            )
        ],
        "flag": [("l", [(6, 3.5), (6, 20.5)]), ("l", [(6, 4.5), (18.5, 8), (6, 11.5), (6, 4.5)])],
        "archive": [
            ("r", 4, 4.5, 16, 4.5),
            ("l", [(5.5, 9), (5.5, 19.5), (18.5, 19.5), (18.5, 9)]),
            ("l", [(9.5, 13), (14.5, 13)]),
        ],
        "restore": [
            ("a", 5, 5.5, 14, 13, 240, 200),
            ("l", [(7, 3.9), (6.8, 8.6), (11.1, 8.9)]),
            ("l", [(9, 14.5), (11.5, 17), (15, 13)]),
        ],
        "play": [("tri", [(8.5, 5.5), (18.5, 12), (8.5, 18.5)])],
        "stop": [("rf", 7.5, 7.5, 9, 9)],
        "mindmap": [
            ("cf", 12, 5.5, 2),
            ("cf", 6, 18, 2),
            ("cf", 12, 18, 2),
            ("cf", 18, 18, 2),
            ("l", [(12, 5.5), (6, 18)]),
            ("l", [(12, 5.5), (12, 18)]),
            ("l", [(12, 5.5), (18, 18)]),
        ],
        "library": [
            ("r", 4.5, 4.5, 3.5, 15),
            ("r", 10, 4.5, 3.5, 15),
            ("l", [(15.8, 5.2), (19.3, 5.9), (17.6, 20.4), (14.1, 19.7), (15.8, 5.2)]),
        ],
        "open_external": [
            ("l", [(4.5, 8), (4.5, 19.5), (16, 19.5), (16, 13)]),
            ("l", [(12, 12), (20, 4)]),
            ("l", [(15.8, 4), (20, 4), (20, 8.2)]),
        ],
        "chevron_down": [("l", [(6, 9.5), (12, 15.5), (18, 9.5)])],
        "chevron_up": [("l", [(6, 14.5), (12, 8.5), (18, 14.5)])],
        "heart": [
            ("c", 8.8, 9.7, 3.9),
            ("c", 15.2, 9.7, 3.9),
            ("tri", [(5.2, 11.2), (18.8, 11.2), (12, 19.3)]),
        ],
        "heart_fill": [
            ("cf", 8.8, 9.7, 3.9),
            ("cf", 15.2, 9.7, 3.9),
            ("tri", [(5.2, 11.2), (18.8, 11.2), (12, 19.3)]),
        ],
        "checklist": [
            ("r", 4.5, 5, 4.2, 4.2),
            ("r", 4.5, 14.8, 4.2, 4.2),
            ("l", [(11.5, 7.1), (19.5, 7.1)]),
            ("l", [(11.5, 16.9), (19.5, 16.9)]),
        ],
        "alarm": [
            ("c", 12, 13, 7.2),
            ("l", [(12, 9.5), (12, 13), (14.8, 14.5)]),
            ("l", [(5.2, 5.4), (7.8, 7.6)]),
            ("l", [(18.8, 5.4), (16.2, 7.6)]),
        ],
        "formula": [("t", "∑", 400, False)],
        "sort": [
            ("l", [(8, 5), (8, 18)]),
            ("l", [(5, 15), (8, 18), (11, 15)]),
            ("l", [(16, 19), (16, 6)]),
            ("l", [(13, 9), (16, 6), (19, 9)]),
        ],
        "bold_n": [("t", "N", 700, False)],
        "bold_g": [("t", "G", 700, False)],
        "bold_f": [("t", "F", 700, False)],
        "bold_ru": [("t", "Ж", 700, False)],
        "bold_ko": [("t", "가", 700, False)],
        "italic_k": [("t", "K", 400, True)],
        "italic_c": [("t", "C", 400, True)],
        "italic_ru": [("t", "К", 400, True)],
        "italic_ko": [("t", "가", 400, True)],
    }
)


def draw(name: str, painter: QPainter, size: int, color: QColor) -> bool:
    """Draw icon *name* into *painter* filling *size* pixels. False if unknown."""
    shapes = SHAPES.get(name)
    if not shapes:
        return False
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size / 24.0, size / 24.0)
    pen = QPen(
        color, 1.9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin
    )
    painter.setPen(pen)
    for shape in shapes:
        kind = shape[0]
        if kind == "l":
            painter.drawPolyline(_polygon(shape[1]))
        elif kind == "c":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(*_circle(shape)))
        elif kind in ("cf", "rf", "tri"):
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            if kind == "cf":
                painter.drawEllipse(QRectF(*_circle(shape)))
            elif kind == "rf":
                painter.drawRoundedRect(QRectF(*shape[1:]), 1.2, 1.2)
            else:
                painter.drawPolygon(_polygon(shape[1]))
            painter.setPen(pen)
        elif kind == "r":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(*shape[1:]), 1.6, 1.6)
        elif kind == "a":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(QRectF(*shape[1:5]), int(shape[5] * 16), int(shape[6] * 16))
        elif kind == "t":
            _letter(painter, shape[1], shape[2], shape[3])
    painter.restore()
    return True


def has_fallback(name: str) -> bool:
    """True when *name* can be drawn without the Windows icon fonts."""
    return name in SHAPES


def _circle(shape: tuple) -> tuple[float, float, float, float]:
    cx, cy, r = shape[1], shape[2], shape[3]
    return (cx - r, cy - r, 2 * r, 2 * r)


def _polygon(points: list[float]) -> QPolygonF:
    return QPolygonF([QPointF(x, y) for x, y in points])


def _letter(painter: QPainter, char: str, weight: int, italic: bool) -> None:
    font = QFont()
    font.setWeight(QFont.Weight(weight))
    font.setItalic(italic)
    font.setPixelSize(15)
    painter.setFont(font)
    painter.drawText(QRectF(2, 2, 20, 20), Qt.AlignmentFlag.AlignCenter, char)
