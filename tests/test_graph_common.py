"""Geometry shared by the 2D and 3D graph: parallel links fan out and share one label."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6.QtGui")

from PySide6.QtCore import QPointF  # noqa: E402

from zettelapp.core.models import DEFAULT_LINK_TYPES, Link  # noqa: E402
from zettelapp.ui.graph_common import (  # noqa: E402
    GraphData,
    edge_shape,
    label_point,
    parallel_lanes,
)


def _link(src, dst, kind="related"):
    return Link(src, dst, kind)


def test_links_between_the_same_notes_get_separate_lanes():
    links = [
        _link("a", "b"),
        _link("a", "b", "supports"),
        _link("b", "a", "extends"),
        _link("a", "c"),
    ]
    assert parallel_lanes(links) == [-1.0, 0.0, 1.0, 0.0]
    assert parallel_lanes(links[:2]) == [-0.5, 0.5]


def test_opposite_links_in_different_lanes_bow_to_different_sides():
    a, b = QPointF(0, 0), QPointF(100, 0)
    there = edge_shape(_link("a", "b"), a, b, -10, 8, directed=True)
    back = edge_shape(_link("b", "a"), b, a, 10, 8, directed=True)
    top = there.path.boundingRect()
    bottom = back.path.boundingRect()
    assert top.top() < -9 and top.bottom() <= 0.5  # bows to one side ...
    assert bottom.bottom() > 9 and bottom.top() >= -0.5  # ... and the other to the other
    assert there.arrow is not None and back.arrow is not None
    straight = edge_shape(_link("a", "c"), a, b, 0, 8, directed=False)
    assert straight.arrow is None and straight.path.boundingRect().height() == 0


def test_neighbour_labels_read_from_the_focused_note():
    types = {lt.id: lt for lt in DEFAULT_LINK_TYPES}
    data = GraphData(
        ["a", "b", "c"],
        {},
        [_link("a", "b", "supports"), _link("b", "a", "supports"), _link("c", "a")],
        {},
        types=types,
    )
    assert data.neighbour_labels("a") == {"b": "Supports · Supported by", "c": "Related to"}
    assert data.neighbour_labels("b") == {"a": "Supported by · Supports"}
    point = label_point(QPointF(0, 0), QPointF(100, 0))
    assert 50 < point.x() < 70  # past the middle, towards the neighbour


@pytest.mark.parametrize("arrow", ["triangle", "open", "diamond", "circle", "bar"])
@pytest.mark.parametrize("bend", [0.0, 25.0])
def test_tips_touch_the_target_circle_and_follow_curves(arrow, bend):
    import math

    a, b, radius = QPointF(0, 0), QPointF(200, 0), 12
    shape = edge_shape(_link("a", "b"), a, b, bend, radius, directed=True, arrow=arrow)
    tip = shape.arrow.boundingRect()
    nearest = min(
        math.hypot(p.x() - b.x(), p.y() - b.y())
        for p in (shape.arrow.pointAtPercent(i / 50) for i in range(51))
    )
    assert radius + 2 < nearest < radius + 4  # just outside the note's circle
    assert shape.filled == (arrow in ("triangle", "diamond", "circle"))
    end = shape.path.currentPosition()
    assert math.hypot(end.x() - b.x(), end.y() - b.y()) >= radius + 2.5  # the line stops short
    if bend:
        # On a curve the tip turns with the curve: it sits below the straight line, on
        # the side the curve bows to, instead of on the chord.
        side = 1 if shape.path.boundingRect().bottom() > 1 else -1
        assert (tip.center().y() * side) > 0.5


def _styled_graph():
    from zettelapp.core.models import ARROW_TIPS, LINE_STYLES, LinkType

    types = {}
    for i, style in enumerate(LINE_STYLES):
        for j, tip in enumerate((None, *ARROW_TIPS)):
            lt = LinkType(f"t{i}{j}", f"T{i}{j}", f"R{i}{j}", "#2A78D6", tip is not None)
            lt.line_style, lt.arrow = style, tip or "triangle"
            types[lt.id] = lt
    ids = [f"n{i}" for i in range(8)]
    links = [
        Link(ids[k % 8], ids[(k * 3 + 1) % 8], type_id)
        for k, type_id in enumerate(types)
        if ids[k % 8] != ids[(k * 3 + 1) % 8]
    ]
    links += [Link("n0", "n1", type_id) for type_id in list(types)[:4]]  # curved lanes
    degree = {i: sum(i in (l.src, l.dst) for l in links) for i in ids}
    return GraphData(ids, {i: i.upper() for i in ids}, links, degree, types=types)


def test_both_graph_views_paint_every_line_style_and_tip():
    """Painting runs Python code; grabbing turns a painting error into a test failure."""
    import math

    from PySide6.QtWidgets import QApplication

    from zettelapp.ui.graph2d import Graph2DView
    from zettelapp.ui.graph3d import Graph3DView

    QApplication.instance() or QApplication(["test"])
    data = _styled_graph()
    flat = {i: (200 * math.cos(k), 200 * math.sin(k)) for k, i in enumerate(data.ids)}
    deep = {i: (*xy, 50.0 * (k % 3)) for k, (i, xy) in enumerate(flat.items())}
    view2d, view3d = Graph2DView(), Graph3DView()
    for view, positions in ((view2d, flat), (view3d, deep)):
        view.resize(640, 480)
        view.set_graph(data, positions, show_groups=True, show_labels=True)
        assert not view.grab().isNull()
        view.select(data.ids[0]) if view is view2d else view.focus_node(data.ids[0])
        assert not view.grab().isNull()
    assert not view2d.render_image().isNull()
