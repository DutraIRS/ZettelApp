"""Diffusion: a note's influence spreading by link distance or by similarity-weighted links."""

import numpy as np
import pytest

from zettelapp.core.diffusion import (
    MIN_WEIGHT,
    distance_frames,
    similarity_weights,
    weighted_frames,
)
from zettelapp.core.models import Link


def _chain(*ids: str) -> list[Link]:
    return [Link(a, b, "related") for a, b in zip(ids, ids[1:], strict=False)]


def test_link_distance_reaches_one_more_link_per_step_and_fades_evenly_with_distance():
    links = _chain("a", "b", "c", "d") + [Link("x", "y", "related")]
    frames = distance_frames("b", links)
    assert [sorted(f) for f in frames] == [["b"], ["a", "b", "c"], ["a", "b", "c", "d"]]
    assert frames[-1] == pytest.approx({"b": 1.0, "a": 2 / 3, "c": 2 / 3, "d": 1 / 3})
    assert "x" not in frames[-1]  # not connected: never reached


def test_link_distance_follows_links_in_both_directions():
    links = [Link("a", "b", "supports"), Link("c", "b", "supports")]
    assert distance_frames("a", links)[-1] == pytest.approx({"a": 1.0, "b": 2 / 3, "c": 1 / 3})


def test_a_note_without_links_is_a_single_frame():
    assert distance_frames("lone", _chain("a", "b")) == [{"lone": 1.0}]
    assert weighted_frames("lone", {}) == [{"lone": 1.0}]


def test_similarity_weights_are_cosines_with_a_floor_and_one_per_pair():
    vectors = {"a": np.array([1.0, 0.0]), "b": np.array([1.0, 1.0]), "c": np.array([0.0, 1.0])}
    links = [Link("a", "b", "supports"), Link("b", "a", "related"), Link("a", "c", "related")]
    links.append(Link("a", "missing", "related"))
    links.append(Link("a", "a", "related"))  # a self-link carries nothing
    w = similarity_weights(links, vectors)
    assert w[frozenset("ab")] == pytest.approx(2**-0.5)
    assert w[frozenset("ac")] == MIN_WEIGHT  # orthogonal
    assert w[frozenset(("a", "missing"))] == MIN_WEIGHT
    assert len(w) == 3


def test_weighted_diffusion_favours_the_more_similar_neighbour_and_settles():
    weights = {frozenset("sa"): 0.9, frozenset("sb"): 0.1, frozenset("bc"): 0.9}
    frames = weighted_frames("s", weights)
    assert frames[0] == {"s": 1.0}
    assert set(frames[1]) == {"s", "a", "b"}  # one step: the neighbours only
    last = frames[-1]
    assert last["s"] == 1.0  # the source stays the strongest
    assert last["a"] > last["b"]
    assert set(last) == {"s", "a", "b", "c"}
    assert all(0 < v <= 1 for f in frames for v in f.values())
    assert len(frames) < 41  # settled before the step limit


def test_weighted_diffusion_matches_personalised_pagerank():
    weights = {frozenset("sa"): 0.5, frozenset("ab"): 1.0, frozenset("sb"): 0.2}
    last = weighted_frames("s", weights, max_steps=500, tolerance=1e-12)[-1]
    nodes = ["s", "a", "b"]
    w = np.zeros((3, 3))
    for pair, value in weights.items():
        i, j = (nodes.index(n) for n in pair)
        w[i, j] = w[j, i] = value
    p = w / w.sum(axis=1, keepdims=True)
    e = np.array([1.0, 0.0, 0.0])
    damping = 0.85 / 1.15  # restart 0.15, half of the influence staying put each step
    x = np.linalg.solve(np.eye(3) - damping * p.T, (1 - damping) * e)
    x = np.sqrt(x / x.max())  # frames are on a square-root scale
    assert [last[n] for n in nodes] == pytest.approx(list(x), rel=1e-6)


def test_a_loop_has_five_frames_from_the_first_to_the_last():
    from zettelapp.core.diffusion import sample_frames

    frames = [{"s": 1.0, "n": i / 10} for i in range(11)]
    loop = sample_frames(frames)
    assert len(loop) == 5 and loop[0] is frames[0] and loop[-1] is frames[-1]
    assert [f["n"] for f in loop] == [0.0, 0.2, 0.5, 0.8, 1.0]
    short = sample_frames(distance_frames("a", _chain("a", "b")))  # two frames
    assert len(short) == 5 and short[0] == {"a": 1.0} and short[-1] == {"a": 1.0, "b": 0.5}
    assert sample_frames([{"a": 1.0}]) == [{"a": 1.0}] * 5
    assert sample_frames([]) == []


def test_diffusion_colours_run_along_a_warm_ramp_and_unreached_notes_go_grey():
    pytest.importorskip("PySide6.QtGui")
    from PySide6.QtGui import QColor

    from zettelapp.ui import theme
    from zettelapp.ui.graph_common import HEAT_LIGHT, GraphData

    data = GraphData(["a", "b", "c", "d"], {}, [], {}, group_of={"a": 0})
    assert data.node_color("a") == data.group_color(0)  # no diffusion: the group's colour
    assert data.heat_of("a") is None
    data.heat = {"a": 1.0, "b": 0.5, "c": 0.2}
    full, half, faint, unreached = (data.node_color(n) for n in "abcd")
    assert data.heat_of("d") == 0.0
    if not theme.current().dark:
        assert full == QColor(HEAT_LIGHT[1])
    # The ramp's steps are far apart (the gradient reads at a glance) and in order.
    lightness = [c.lightnessF() for c in (full, half, faint)]
    assert lightness == sorted(lightness, reverse=theme.current().dark)
    assert abs(lightness[0] - lightness[2]) > 0.25
    assert unreached.hsvSaturationF() < 0.15 < faint.hsvSaturationF()  # grey vs warm
