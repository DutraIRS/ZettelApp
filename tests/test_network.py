"""Network measures for Insights: degrees, power law, betweenness, PageRank and clustering."""

import random

import pytest

from zettelapp.core.models import Link
from zettelapp.core.network import (
    betweenness,
    clustering,
    components,
    fit_power_law,
    neighbours,
    network_stats,
    pagerank,
)


def _graph(edges, extra=()):
    ids = sorted({n for e in edges for n in e} | set(extra))
    links = [Link(src=a, dst=b, type="related", origin="manual") for a, b in edges]
    return ids, links


def test_links_count_once_whichever_way_and_self_links_not_at_all():
    ids, links = _graph([("a", "b"), ("b", "a"), ("a", "a"), ("b", "c")], extra=["lone"])
    adj = neighbours(ids, links)
    assert adj == {"a": {"b"}, "b": {"a", "c"}, "c": {"b"}, "lone": set()}


def test_a_star_s_centre_is_on_every_path_and_ranks_first():
    ids, links = _graph([("hub", leaf) for leaf in "abcd"])
    adj = neighbours(ids, links)
    between = betweenness(adj)
    assert between["hub"] == pytest.approx(1.0) and between["a"] == 0
    rank = pagerank(adj)
    assert sum(rank.values()) == pytest.approx(1.0)
    assert max(rank, key=rank.get) == "hub"
    assert clustering(adj) == (0.0, 0.0)  # no triangles


def test_a_triangle_is_fully_clustered_and_a_path_s_middle_carries_it():
    triangle = neighbours(*_graph([("a", "b"), ("b", "c"), ("c", "a")]))
    assert clustering(triangle) == (1.0, 1.0)
    path = neighbours(*_graph([("a", "b"), ("b", "c")]))
    assert betweenness(path)["b"] == pytest.approx(1.0)


def test_sampled_betweenness_still_finds_the_bridge():
    # two cliques of 20 joined through one note: every path between them crosses it and the two
    # notes it joins, whichever sources are sampled
    edges = [(f"l{i}", f"l{j}") for i in range(20) for j in range(i)]
    edges += [(f"r{i}", f"r{j}") for i in range(20) for j in range(i)]
    edges += [("l0", "bridge"), ("bridge", "r0")]
    between = betweenness(neighbours(*_graph(edges)), sample=10)
    assert set(sorted(between, key=between.get)[-3:]) == {"l0", "bridge", "r0"}


def test_components_are_counted_largest_first():
    ids, links = _graph([("a", "b"), ("b", "c"), ("x", "y")], extra=["lone"])
    assert components(neighbours(ids, links)) == [3, 2, 1]


def test_the_power_law_exponent_is_recovered_from_its_samples():
    rng = random.Random(1)
    # discrete power law with alpha 2.5 by inverse transform (continuous, then rounded down)
    degrees = [int((1 - rng.random()) ** (-1 / 1.5)) for _ in range(3000)]
    fit = fit_power_law(degrees)
    assert fit is not None and fit.alpha == pytest.approx(2.5, abs=0.15)
    assert fit.ks < 0.05


def test_too_few_linked_notes_or_degrees_give_no_exponent():
    assert fit_power_law([1, 2, 2, 3, 0, 0]) is None
    assert fit_power_law([1] * 15 + [2] * 11 + [3] * 3) is None  # a small vault: no tail to fit
    assert fit_power_law([2] * 80 + [3] * 40) is None  # many notes, but only two degrees


def test_network_stats_bring_it_together():
    ids, links = _graph([("a", "b"), ("b", "c"), ("c", "a"), ("c", "d")], extra=["e"])
    stats = network_stats(ids, links)
    assert stats.degrees == {"a": 2, "b": 2, "c": 3, "d": 1, "e": 0}
    assert stats.distribution == {0: 1, 1: 1, 2: 2, 3: 1}
    assert stats.components == [4, 1]
    assert max(stats.betweenness, key=stats.betweenness.get) == "c"
    assert stats.power_law is None  # five notes are too few


def test_insights_shows_the_network(tmp_path, monkeypatch):
    pytest.importorskip("PySide6.QtWidgets")
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from tests.test_ui_smoke import pump
    from tools.demo_vault import build_demo

    monkeypatch.setenv("ZETTELAPP_SETTINGS_FILE", str(tmp_path / "settings.ini"))
    from PySide6.QtWidgets import QApplication

    from zettelapp.ui.main_window import MainWindow

    QApplication.instance() or QApplication(["test"])
    window = MainWindow()
    try:
        assert window.open_vault(tmp_path / "vault")
        build_demo(window.vault)
        window.show_page(2)
        window.insights.refresh()
        pump(400)
        page = window.insights
        assert page.tiles["parts"].value.text().replace(",", "").isdigit()
        assert page.tiles["power"].value.text() == "–"  # a demo vault is too small to fit
        assert page.degrees_chart.rows and page.between_chart.rows and page.rank_chart.rows
        assert all(0 <= value <= 1 for _label, value, *_rest in page.rank_chart.rows)
    finally:
        window.close()
        window.deleteLater()
