"""Diffusion: how one note's influence spreads through the network, frame by frame.

Two measures, both following links in either direction:

- **Link distance**: the influence moves one link per step and fades evenly with distance:
  with notes up to *n* links away, one *d* links away holds (n + 1 - d) / (n + 1) of it.
  The last frame is every note the source can reach.
- **Links weighted by similarity**: a random walk with restart. At each step the influence
  flows along links in proportion to how similar the linked notes are (cosine similarity of
  their embeddings), while a share goes back to the source. It settles on the source's
  personalised PageRank (damping (1 - restart) / (1 + restart), as half of the influence
  stays put at each step): notes that are close *and* alike end up with the most.

Every frame maps note ids to a value in (0, 1], the strongest note being 1, ready to be
drawn on a colour ramp (the random walk's on a square-root scale, so the notes with a small
share still show).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping

import numpy as np

from zettelapp.core.graph import hop_distances
from zettelapp.core.models import Link

Frame = dict[str, float]
MIN_WEIGHT = 0.05  # a link between unrelated notes still carries a little
MIN_SHOWN = 1e-3  # values below this (relative to the strongest) are left out of a frame


def distance_frames(source: str, links: Iterable[Link]) -> list[Frame]:
    """One frame per step: the notes within *t* links of *source*, fading evenly with
    their distance."""
    links = list(links)
    distance = hop_distances([source], links, depth=len(links) + 1)
    last = max(distance.values())
    return [
        {node: (last + 1 - d) / (last + 1) for node, d in distance.items() if d <= t}
        for t in range(last + 1)
    ]


def similarity_weights(
    links: Iterable[Link], vectors: Mapping[str, np.ndarray]
) -> dict[frozenset[str], float]:
    """Each linked pair of notes with the cosine similarity of their vectors, at least
    MIN_WEIGHT (also for a note without a vector)."""
    weights: dict[frozenset[str], float] = {}
    for link in links:
        if link.src == link.dst:
            continue
        pair = frozenset((link.src, link.dst))
        if pair in weights:
            continue
        a, b = vectors.get(link.src), vectors.get(link.dst)
        cosine = 0.0
        if a is not None and b is not None:
            norm = float(np.linalg.norm(a) * np.linalg.norm(b))
            if norm > 0:
                cosine = float(np.dot(a, b)) / norm
        weights[pair] = max(MIN_WEIGHT, cosine)
    return weights


def weighted_frames(
    source: str,
    weights: Mapping[frozenset[str], float],
    restart: float = 0.15,
    max_steps: int = 40,
    tolerance: float = 1e-4,
) -> list[Frame]:
    """A random walk with restart from *source* over the weighted, undirected links: the
    first frame is the source alone, then one frame per step until the values settle."""
    neighbours: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for pair, w in weights.items():
        a, b = tuple(pair)
        neighbours[a].append((b, w))
        neighbours[b].append((a, w))
    total = {node: sum(w for _n, w in nbs) for node, nbs in neighbours.items()}
    x: dict[str, float] = {source: 1.0}
    frames = [_shown(x)]
    for _step in range(max_steps):
        # A lazy walk: half of each note's influence stays put, so it spreads smoothly
        # instead of swinging back and forth between neighbours.
        nxt: dict[str, float] = defaultdict(float)
        nxt[source] += restart
        for node, mass in x.items():
            moving = (1 - restart) * mass
            nxt[node] += moving / 2
            if not total.get(node):
                nxt[source] += moving / 2  # nowhere to go: back to the source
                continue
            for other, w in neighbours[node]:
                nxt[other] += moving / 2 * w / total[node]
        change = sum(abs(nxt.get(n, 0.0) - x.get(n, 0.0)) for n in set(nxt) | set(x))
        if change < tolerance:
            break
        x = dict(nxt)
        frames.append(_shown(x))
    return frames


def sample_frames(frames: list[Frame], count: int = 5) -> list[Frame]:
    """*count* frames spread evenly from the first to the last (a short loop to animate);
    fewer frames are padded by repeating the last one."""
    if not frames:
        return []
    if len(frames) == 1:
        return frames * count
    picks = [round(i * (len(frames) - 1) / (count - 1)) for i in range(count)]
    return [frames[i] for i in picks]


def _shown(x: Mapping[str, float]) -> Frame:
    top = max(x.values(), default=0.0)
    if top <= 0:
        return {}
    return {node: (v / top) ** 0.5 for node, v in x.items() if v / top >= MIN_SHOWN}
