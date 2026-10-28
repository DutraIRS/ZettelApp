"""How link types look: line patterns, arrow tips and small pictures of both.

The graph, the side panel, the legend and Options all draw links with these helpers, so
a link type looks the same everywhere.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

from zettelapp.core.models import LinkType, stroke_dashes
from zettelapp.i18n import N_
from zettelapp.ui import theme

LINE_STYLE_NAMES = {
    "solid": N_("Solid"),
    "dashed": N_("Dashed"),
    "dotted": N_("Dotted"),
    "dash_dot": N_("Dash-dot"),
    "dash_dot_dot": N_("Dash-dot-dot"),
    "long_dash": N_("Long dash"),
}
ARROW_TIP_NAMES = {
    "triangle": N_("Filled triangle"),
    "open": N_("Open arrow"),
    "diamond": N_("Diamond"),
    "circle": N_("Circle"),
    "bar": N_("Bar"),
}
FILLED_TIPS = frozenset({"triangle", "diamond", "circle"})
ARROW_SIZE = 7.0  # length of a triangle tip, in the same units as the line
LIST_ICON = QSize(36, 16)  # wide enough to show a whole dash pattern
MENU_ICON = QSize(16, 16)


def link_pen(color: QColor, width: float, line_style: str, scale: float = 1.0) -> QPen:
    """A pen for links of *line_style*; *scale* shortens dashes for small pictures."""
    pen = QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    dashes = stroke_dashes(line_style, scale)
    if dashes:
        pen.setDashPattern(dashes)
    return pen


@dataclass
class Tip:
    path: QPainterPath
    filled: bool
    length: float  # how far back from its point the tip reaches; the line stops there


def tip_shape(point: QPointF, ux: float, uy: float, arrow: str, size: float = ARROW_SIZE) -> Tip:
    """An arrow tip with its point at *point*, facing along the unit vector (ux, uy)."""

    def at(back: float, side: float) -> QPointF:  # *back* along the link, *side* across it
        return QPointF(point.x() - ux * back - uy * side, point.y() - uy * back + ux * side)

    path = QPainterPath()
    if arrow == "open":
        path.moveTo(at(size, size * 0.55))
        path.lineTo(point)
        path.lineTo(at(size, -size * 0.55))
        return Tip(path, False, 0.0)
    if arrow == "bar":
        path.moveTo(at(0, size * 0.65))
        path.lineTo(at(0, -size * 0.65))
        return Tip(path, False, 0.0)
    if arrow == "circle":
        radius = size * 0.45
        path.addEllipse(at(radius, 0), radius, radius)
        return Tip(path, True, radius * 2)
    if arrow == "diamond":
        corners = [
            point,
            at(size * 0.8, size * 0.5),
            at(size * 1.6, 0),
            at(size * 0.8, -size * 0.5),
        ]
        length = size * 1.6
    else:  # filled triangle
        corners = [point, at(size, size * 0.55), at(size, -size * 0.55)]
        length = size
    path.moveTo(corners[0])
    for corner in corners[1:]:
        path.lineTo(corner)
    path.closeSubpath()
    return Tip(path, True, length)


def tip_pen(color: QColor, width: float, filled: bool) -> QPen:
    """Tips are drawn solid, whatever the line style; a thin outline rounds filled ones."""
    pen = QPen(color, min(width, 1.2) if filled else width, Qt.PenStyle.SolidLine)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def draw_tip(painter: QPainter, tip: QPainterPath, color: QColor, width: float, filled: bool):
    painter.setPen(tip_pen(color, width, filled))
    painter.setBrush(color if filled else Qt.BrushStyle.NoBrush)
    painter.drawPath(tip)
    painter.setBrush(Qt.BrushStyle.NoBrush)


def draw_sample(
    painter: QPainter,
    start: QPointF,
    end: QPointF,
    color: QColor,
    line_style: str,
    arrow: str | None,
    width: float = 1.8,
    size: float = ARROW_SIZE,
    scale: float = 1.0,
) -> None:
    """A straight link from *start* to *end* with its tip (if any) touching *end*."""
    dx, dy = end.x() - start.x(), end.y() - start.y()
    length = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / length, dy / length
    tip = tip_shape(end, ux, uy, arrow, size) if arrow else None
    stop = tip.length if tip else 0.0
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(link_pen(color, width, line_style, scale))
    painter.drawLine(start, QPointF(end.x() - ux * stop, end.y() - uy * stop))
    if tip is not None:
        draw_tip(painter, tip.path, color, width, tip.filled)


def sample_icon(
    color: QColor, line_style: str, arrow: str | None, size: QSize = LIST_ICON
) -> QIcon:
    """A small picture of a line, drawn at twice the size for sharp high-DPI screens."""
    w, h = size.width(), size.height()
    px = QPixmap(w * 2, h * 2)
    px.setDevicePixelRatio(2)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    y = h / 2
    small = w < 30  # menus: a shorter pattern still shows its rhythm
    draw_sample(
        p,
        QPointF(2, y),
        QPointF(w - 2, y),
        color,
        line_style,
        arrow,
        width=1.6 if small else 1.8,
        size=min(ARROW_SIZE, h * 0.42) * (0.8 if small else 1.0),
        scale=0.55 if small else 1.0,
    )
    p.end()
    return QIcon(px)


def type_color(lt: LinkType) -> QColor:
    return theme.current().entity(lt.color)


def type_icon(lt: LinkType, size: QSize = LIST_ICON) -> QIcon:
    """The link type's colour, line style and (if directed) arrow tip."""
    return sample_icon(type_color(lt), lt.line_style, lt.tip, size)
