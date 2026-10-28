"""Graph helpers: neighbourhood subgraphs and a force-directed layout."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Hashable, Iterable, Mapping, Sequence

import numpy as np

from zettelapp.core.models import Link


def adjacency(links: Iterable[Link], types: set[str] | None = None) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = defaultdict(set)
    for link in links:
        if types is None or link.type in types:
            adj[link.src].add(link.dst)
            adj[link.dst].add(link.src)
    return adj


def subgraph(
    seeds: Iterable[str], links: Iterable[Link], depth: int, types: set[str] | None = None
) -> set[str]:
    """Notes within *depth* links of any seed, following links in both directions."""
    adj = adjacency(links, types)
    seen = set(seeds)
    queue = deque((s, 0) for s in seen)
    while queue:
        node, d = queue.popleft()
        if d >= depth:
            continue
        for nb in adj.get(node, ()):
            if nb not in seen:
                seen.add(nb)
                queue.append((nb, d + 1))
    return seen


def force_layout(
    nodes: Sequence[str],
    edges: Iterable[tuple[str, str]],
    size: float = 1000.0,
    iterations: int | None = None,
    seed: int = 1,
    dims: int = 2,
    initial: Mapping[str, Sequence[float]] | None = None,
    groups: Mapping[str, Hashable] | None = None,
    group_strength: float = 0.0,
    gravity: float = 1.0,
) -> dict[str, tuple[float, ...]]:
    """Fruchterman-Reingold layout in 2D or 3D.

    *groups* maps nodes to a group key (a tag or a cluster); with a positive
    *group_strength*, nodes are also pulled towards their group's centre so
    groups form visible islands.
    """
    n = len(nodes)
    if n == 0:
        return {}
    if n == 1:
        return {nodes[0]: (0.0,) * dims}
    index = {node: i for i, node in enumerate(nodes)}
    rng = np.random.default_rng(seed)
    pos = rng.uniform(-size / 2, size / 2, (n, dims)).astype(np.float32)
    if initial:
        for node, xy in initial.items():
            if node in index and len(xy) == dims:
                pos[index[node]] = xy
    pairs = np.array(
        [(index[a], index[b]) for a, b in edges if a in index and b in index and a != b],
        dtype=np.int64,
    ).reshape(-1, 2)
    group_of = None
    if groups and group_strength > 0:
        keys = {
            g: i for i, g in enumerate(sorted({str(g) for g in groups.values() if g is not None}))
        }
        group_of = np.array(
            [
                keys.get(str(groups.get(node))) if groups.get(node) is not None else -1
                for node in nodes
            ]
        )
        grouped = group_of >= 0
    if iterations is None:
        iterations = 300 if n <= 300 else max(60, 90_000 // n)
    k = size / np.sqrt(n) if dims == 2 else size / np.cbrt(n) * 0.6
    temperature = size / 8
    cooling = temperature / (iterations + 1)
    for _ in range(iterations):
        delta = pos[:, None, :] - pos[None, :, :]
        dist = np.sqrt((delta**2).sum(axis=2))
        np.fill_diagonal(dist, 1.0)
        dist = np.maximum(dist, 0.01)
        force = (k * k) / dist
        np.fill_diagonal(force, 0.0)
        disp = (delta * (force / dist)[:, :, None]).sum(axis=1)
        if len(pairs):
            d = pos[pairs[:, 0]] - pos[pairs[:, 1]]
            length = np.maximum(np.sqrt((d**2).sum(axis=1)), 0.01)
            pull = d * (length / k)[:, None]
            np.add.at(disp, pairs[:, 0], -pull)
            np.add.at(disp, pairs[:, 1], pull)
        if group_of is not None and grouped.any():
            g = group_of[grouped]
            centres = np.zeros((g.max() + 1, dims), dtype=np.float32)
            np.add.at(centres, g, pos[grouped])
            centres /= np.maximum(np.bincount(g), 1)[:, None]
            offset = centres[g] - pos[grouped]
            length = np.sqrt((offset**2).sum(axis=1))[:, None]
            disp[grouped] += offset * (length / k) * group_strength
        # Gravity balances repulsion around radius ~size/2 and keeps separate components close.
        disp -= pos * (gravity * n * k * k / (size / 2) ** 2)
        length = np.maximum(np.sqrt((disp**2).sum(axis=1)), 0.01)
        pos += disp / length[:, None] * np.minimum(length, temperature)[:, None]
        temperature = max(temperature - cooling, size / 400)
    pos -= pos.mean(axis=0)
    return {node: tuple(float(v) for v in pos[i]) for node, i in index.items()}
