"""Arrow tips at each end of a link: a different start tip for directed types, the same tips at
both ends for undirected ones, in the graph, the samples and the exports."""

import os

import pytest

from zettelapp.core.models import Link, LinkType

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_directed_types_can_start_with_another_tip_and_undirected_ones_are_symmetric():
    directed = LinkType("cites", "Cites", "Cited by", "#123456", start_arrow="circle")
    assert (directed.start_tip, directed.tip) == ("circle", "triangle")
    plain = LinkType("rel", "Related", "Related", "#123456", directed=False)
    assert (plain.start_tip, plain.tip) == (None, None)  # as before: no tips
    both = LinkType("rel", "Related", "Related", "#123456", directed=False, start_arrow="bar")
    assert (both.start_tip, both.tip) == ("bar", "bar")


def test_exports_carry_both_tips():
    from zettelapp.core.export import _svg_link

    lt = LinkType("cites", "Cites", "Cited by", "#123456", start_arrow="diamond")
    svg = _svg_link(0, 0, 200, 0, lt, 1.5, 10)
    assert svg.count("<path") == 2
    assert _svg_link(0, 0, 200, 0, LinkType("c", "C", "C", "#123456"), 1.5, 10).count("<path") == 1


def test_the_graph_draws_a_tip_at_each_end_and_the_line_between_them():
    pytest.importorskip("PySide6.QtWidgets")
    from PySide6.QtCore import QPointF
    from PySide6.QtWidgets import QApplication

    from zettelapp.ui.graph_common import edge_shape

    QApplication.instance() or QApplication(["test"])
    link = Link(src="a", dst="b", type="cites", origin="manual")
    a, b = QPointF(0, 0), QPointF(200, 0)
    one = edge_shape(link, a, b, 0, 10, True, "triangle")
    assert one.arrow is not None and one.start is None
    both = edge_shape(link, a, b, 0, 10, True, "triangle", start_arrow="circle", source_radius=10)
    assert both.arrow is not None and both.start is not None and both.start_filled
    line = both.path.boundingRect()
    assert line.left() > 10 and line.right() < 190  # clear of both notes and both tips
    sym = edge_shape(link, a, b, 30, 10, False, "triangle", start_arrow="open", source_radius=10)
    assert sym.arrow is None and sym.start is not None  # undirected tips come in as start tips
