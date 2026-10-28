"""Data and helpers shared by the 2D and 3D graph views."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
    QPolygonF,
)

from zettelapp.core.models import Link, LinkType
from zettelapp.ui import theme

MAX_GROUP_COLORS = 8  # categorical palette size; further groups fold into "Other"


@dataclass
class GraphData:
    ids: list[str]
    titles: dict[str, str]
    links: list[Link]
    degree: dict[str, int]
    group_of: dict[str, int | None] = field(default_factory=dict)  # note -> group index
    group_names: list[str] = field(default_factory=list)
    images: dict[str, Path] = field(default_factory=dict)
    types: dict[str, tuple[int, LinkType]] = field(default_factory=dict)
    focus: str | None = None

    def group_color(self, group: int | None) -> QColor:
        t = theme.current()
        if group is None or group >= MAX_GROUP_COLORS:
            return t.q("text_muted")
        return t.category(group)

    def group_label(self, group: int) -> str:
        return self.group_names[group] if group < len(self.group_names) else "Other"

    def link_color(self, link: Link) -> QColor:
        entry = self.types.get(link.type)
        return theme.current().entity(entry[1].color) if entry else theme.current().q("text_muted")

    def link_label(self, link: Link, seen_from: str) -> str:
        """How *link* reads from the note *seen_from*: "Supports" or "Supported by"."""
        entry = self.types.get(link.type)
        return entry[1].label_for(link.src == seen_from) if entry else link.type

    def neighbour_labels(self, focus: str) -> dict[str, str]:
        """For each note linked to *focus*, the types of all links between them, as one
        label ("Supports · Extended by"), so links between the same notes share a label."""
        out: dict[str, list[str]] = {}
        for link in self.links:
            if focus in (link.src, link.dst) and link.src != link.dst:
                other = link.dst if link.src == focus else link.src
                text = self.link_label(link, focus)
                if text not in out.setdefault(other, []):
                    out[other].append(text)
        return {other: " · ".join(texts) for other, texts in out.items()}

    def link_directed(self, link: Link) -> bool:
        entry = self.types.get(link.type)
        return bool(entry and entry[1].directed)

    def members(self) -> dict[int, list[str]]:
        out: dict[int, list[str]] = {}
        for node, g in self.group_of.items():
            if g is not None and g < MAX_GROUP_COLORS:
                out.setdefault(g, []).append(node)
        return out


def parallel_lanes(links: list[Link]) -> list[float]:
    """Each link's lane among the links joining the same two notes.

    A lone link gets 0 (drawn straight); two links get -0.5 and 0.5, three get -1, 0
    and 1, and so on, so links between the same notes fan out instead of overlapping.
    """
    pairs: dict[tuple[str, str], list[int]] = {}
    for i, link in enumerate(links):
        a, b = sorted((link.src, link.dst))
        pairs.setdefault((a, b), []).append(i)
    lanes = [0.0] * len(links)
    for members in pairs.values():
        for j, i in enumerate(members):
            lanes[i] = j - (len(members) - 1) / 2
    return lanes


LABEL_POSITION = 0.58  # labels sit a little past the middle, towards the neighbour


def label_point(focus: QPointF, other: QPointF) -> QPointF:
    """Where the label for the links between *focus* and *other* goes; going past the
    middle spreads the labels around a well-connected note."""
    return focus + (other - focus) * LABEL_POSITION


@dataclass
class EdgeShape:
    path: QPainterPath  # the link itself
    arrow: QPainterPath | None  # arrowhead at the target, for directed links


def edge_shape(
    link: Link, a: QPointF, b: QPointF, bend: float, target_radius: float, directed: bool
) -> EdgeShape:
    """A link from *a* to *b*, bowed sideways by *bend* pixels (0 = straight).

    The side is taken from the pair's canonical direction, so A→B and B→A in different
    lanes never coincide.
    """
    dx, dy = b.x() - a.x(), b.y() - a.y()
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    if link.src > link.dst:
        nx, ny = -nx, -ny
    path = QPainterPath(a)
    if bend:
        # A quadratic curve passes half-way to its control point at the middle, so the
        # curve's widest point is *bend* pixels from the straight line.
        mid = QPointF((a.x() + b.x()) / 2, (a.y() + b.y()) / 2)
        control = QPointF(mid.x() + nx * bend * 2, mid.y() + ny * bend * 2)
        path.quadTo(control, b)
        tx, ty = b.x() - control.x(), b.y() - control.y()
    else:
        path.lineTo(b)
        tx, ty = dx, dy
    arrow = None
    if directed and length > target_radius * 2 + 4:
        t_len = math.hypot(tx, ty) or 1.0
        ux, uy = tx / t_len, ty / t_len
        tip = QPointF(b.x() - ux * (target_radius + 3), b.y() - uy * (target_radius + 3))
        size = 7.0
        arrow = QPainterPath(
            QPointF(tip.x() - ux * size - uy * size * 0.55, tip.y() - uy * size + ux * size * 0.55)
        )
        arrow.lineTo(tip)
        arrow.lineTo(
            QPointF(tip.x() - ux * size + uy * size * 0.55, tip.y() - uy * size - ux * size * 0.55)
        )
    return EdgeShape(path, arrow)


def draw_edge_label(painter: QPainter, center: QPointF, text: str, font: QFont) -> None:
    """A link-type label on a pill of the surface colour, readable over other links."""
    t = theme.current()
    metrics = QFontMetricsF(font)
    width, height = metrics.horizontalAdvance(text) + 10, metrics.height() + 2
    rect = QRectF(center.x() - width / 2, center.y() - height / 2, width, height)
    background = QColor(t.q("surface"))
    background.setAlphaF(0.92)
    painter.setPen(QPen(t.q("border"), 1))
    painter.setBrush(background)
    painter.drawRoundedRect(rect, height / 2, height / 2)
    painter.setFont(font)
    painter.setPen(t.q("text_secondary"))  # text wears text tokens; the line carries the colour
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Andrew's monotone chain."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def padded_hull(points: list[tuple[float, float]], pad: float) -> QPainterPath:
    """A rounded region around *points* (convex hull grown by *pad*)."""
    hull = convex_hull(points)
    path = QPainterPath()
    if len(hull) == 1:
        path.addEllipse(QPointF(*hull[0]), pad, pad)
        return path
    path.addPolygon(QPolygonF([QPointF(x, y) for x, y in hull]))
    path.closeSubpath()
    stroker = QPainterPathStroker()
    stroker.setWidth(pad * 2)
    stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
    return stroker.createStroke(path).united(path).simplified()
