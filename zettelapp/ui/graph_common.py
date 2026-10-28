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
from zettelapp.ui.link_style import ARROW_SIZE, tip_shape

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
    types: dict[str, LinkType] = field(default_factory=dict)
    focus: str | None = None

    def group_color(self, group: int | None) -> QColor:
        t = theme.current()
        if group is None or group >= MAX_GROUP_COLORS:
            return t.q("text_muted")
        return t.category(group)

    def group_label(self, group: int) -> str:
        return self.group_names[group] if group < len(self.group_names) else "Other"

    def link_color(self, link: Link) -> QColor:
        lt = self.types.get(link.type)
        return theme.current().entity(lt.color) if lt else theme.current().q("text_muted")

    def link_style(self, link: Link) -> str:
        lt = self.types.get(link.type)
        return lt.line_style if lt else "solid"

    def link_tip(self, link: Link) -> str | None:
        """The arrow tip of a directed link's type; None for undirected links."""
        lt = self.types.get(link.type)
        return lt.tip if lt else None

    def link_label(self, link: Link, seen_from: str) -> str:
        """How *link* reads from the note *seen_from*: "Supports" or "Supported by"."""
        lt = self.types.get(link.type)
        return lt.label_for(link.src == seen_from) if lt else link.type

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
        lt = self.types.get(link.type)
        return bool(lt and lt.directed)

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
    path: QPainterPath  # the link itself, ending where its arrow tip begins
    arrow: QPainterPath | None  # the tip at the target, for directed links
    filled: bool = False  # whether the tip is a filled shape (triangle, diamond, circle)


def _distance_param(point, target: QPointF, distance: float) -> float:
    """The curve parameter t (0-1) where *point(t)* is *distance* from *target*, the
    curve's end; the distance shrinks towards the end, so bisection finds it."""
    lo, hi = 0.0, 1.0
    for _step in range(24):
        mid = (lo + hi) / 2
        p = point(mid)
        if math.hypot(p.x() - target.x(), p.y() - target.y()) > distance:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def edge_shape(
    link: Link,
    a: QPointF,
    b: QPointF,
    bend: float,
    target_radius: float,
    directed: bool,
    arrow: str = "triangle",
    size: float = ARROW_SIZE,
) -> EdgeShape:
    """A link from *a* to *b*, bowed sideways by *bend* pixels (0 = straight), with an
    *arrow* tip just outside the target's circle when *directed*.

    The side is taken from the pair's canonical direction, so A→B and B→A in different
    lanes never coincide. On a curve the tip sits on the curve and follows its direction
    where it meets the circle, and the line stops where a filled tip begins.
    """
    dx, dy = b.x() - a.x(), b.y() - a.y()
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    if link.src > link.dst:
        nx, ny = -nx, -ny
    # A quadratic curve passes half-way to its control point at the middle, so the
    # curve's widest point is *bend* pixels from the straight line.
    mid = QPointF((a.x() + b.x()) / 2, (a.y() + b.y()) / 2)
    control = QPointF(mid.x() + nx * bend * 2, mid.y() + ny * bend * 2)

    def point(t: float) -> QPointF:
        s = 1 - t
        return a * (s * s) + control * (2 * s * t) + b * (t * t)

    def path_to(t: float) -> QPainterPath:
        path = QPainterPath(a)
        if bend:  # the first part of the curve, up to t (de Casteljau)
            path.quadTo(a + (control - a) * t, point(t))
        else:
            path.lineTo(point(t))
        return path

    if not directed or length <= target_radius * 2 + 4:
        return EdgeShape(path_to(1.0), None)
    gap = target_radius + 3
    tip_point = point(_distance_param(point, b, gap))
    behind = point(_distance_param(point, b, gap + size))  # aim along the curve's end
    tx, ty = tip_point.x() - behind.x(), tip_point.y() - behind.y()
    t_len = math.hypot(tx, ty) or 1.0
    tip = tip_shape(tip_point, tx / t_len, ty / t_len, arrow, size)
    end = (
        _distance_param(point, b, gap + tip.length)
        if tip.length
        else _distance_param(point, b, gap)
    )
    return EdgeShape(path_to(end), tip.path, tip.filled)


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
