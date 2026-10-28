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
    types = {lt.id: (i, lt) for i, lt in enumerate(DEFAULT_LINK_TYPES)}
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
