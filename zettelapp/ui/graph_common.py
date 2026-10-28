"""Data and helpers shared by the 2D and 3D graph views."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainterPath, QPainterPathStroker, QPolygonF

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

    def members(self) -> dict[int, list[str]]:
        out: dict[int, list[str]] = {}
        for node, g in self.group_of.items():
            if g is not None and g < MAX_GROUP_COLORS:
                out.setdefault(g, []).append(node)
        return out


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
