"""Network measures of the note graph: degree distribution, centrality and clustering.

The graph is read as undirected and simple: a link in either direction joins two notes once, and
a note linking itself is not counted. Everything here is plain Python, so it runs on
the desktop and on Android alike.
"""

from __future__ import annotations

import math
import random
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field

from zettelapp.core.models import Link

BETWEENNESS_SAMPLE = 300  # sources for betweenness in bigger vaults (Brandes with pivots)
MIN_TAIL = 50  # notes in a power-law tail below which no exponent is given
MIN_DEGREES = 4  # distinct degrees a tail needs: two or three values fit any exponent


@dataclass
class PowerLaw:
    """A discrete power law P(k) ∝ k^-alpha fitted to the degrees from *k_min* on."""

    alpha: float
    k_min: int
    tail: int  # notes with degree ≥ k_min
    ks: float  # Kolmogorov-Smirnov distance between the data and the fit (0 is a perfect fit)


@dataclass
class NetworkStats:
    degrees: dict[str, int]  # every note, linked or not
    distribution: dict[int, int]  # degree -> number of notes
    power_law: PowerLaw | None
    betweenness: dict[str, float]  # 0..1, the share of shortest paths through each note
    pagerank: dict[str, float]  # sums to 1
    clustering: float  # the average local clustering coefficient of notes with 2+ neighbours
    transitivity: float  # 3 × triangles / connected triples
    components: list[int] = field(
        default_factory=list
    )  # sizes of the connected parts, largest first


def neighbours(note_ids: Iterable[str], links: Iterable[Link]) -> dict[str, set[str]]:
    """Each note's neighbours in the undirected, simple graph."""
    adj: dict[str, set[str]] = {i: set() for i in note_ids}
    for link in links:
        if link.src == link.dst or link.src not in adj or link.dst not in adj:
            continue
        adj[link.src].add(link.dst)
        adj[link.dst].add(link.src)
    return adj


def degree_distribution(adj: dict[str, set[str]]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for nbs in adj.values():
        counts[len(nbs)] = counts.get(len(nbs), 0) + 1
    return dict(sorted(counts.items()))


def _hurwitz_zeta(alpha: float, k_min: int, terms: int = 2000) -> float:
    """∑ (k)^-alpha for k ≥ k_min: the normaliser of a discrete power law."""
    total = sum((k_min + i) ** -alpha for i in range(terms))
    # the rest of the sum, by the integral from k_min + terms - 1/2 on
    tail_start = k_min + terms - 0.5
    return total + tail_start ** (1 - alpha) / (alpha - 1)


def fit_power_law(degrees: Iterable[int]) -> PowerLaw | None:
    """Fit P(k) ∝ k^-alpha by maximum likelihood, choosing k_min where the fit is closest (the
    smallest Kolmogorov-Smirnov distance), after Clauset, Shalizi and Newman (2009). None when
    the tail is too short to say anything."""
    data = sorted(k for k in degrees if k > 0)
    best: PowerLaw | None = None
    for k_min in sorted(set(data)):
        tail = [k for k in data if k >= k_min]
        if len(tail) < MIN_TAIL or len(set(tail)) < MIN_DEGREES:
            break
        logs = sum(math.log(k / (k_min - 0.5)) for k in tail)
        if logs <= 0:
            continue
        alpha = 1 + len(tail) / logs  # the discrete approximation of the MLE
        if not 1.05 < alpha < 6:
            continue
        zeta = _hurwitz_zeta(alpha, k_min)
        ks, below, seen = 0.0, 0.0, 0
        counts: dict[int, int] = {}
        for k in tail:
            counts[k] = counts.get(k, 0) + 1
        for k in range(k_min, tail[-1] + 1):
            below += k**-alpha / zeta  # the fitted CDF at k
            seen += counts.get(k, 0)
            ks = max(ks, abs(seen / len(tail) - below))
        if best is None or ks < best.ks:
            best = PowerLaw(alpha, k_min, len(tail), ks)
    return best


def betweenness(
    adj: dict[str, set[str]], sample: int = BETWEENNESS_SAMPLE, seed: int = 7
) -> dict[str, float]:
    """Brandes' betweenness centrality, normalised to 0..1. In graphs with more than *sample*
    notes, the paths from *sample* random notes stand in for all of them."""
    nodes = list(adj)
    n = len(nodes)
    score = dict.fromkeys(nodes, 0.0)
    if n < 3:
        return score
    sources = nodes if n <= sample else random.Random(seed).sample(nodes, sample)
    for s in sources:
        order: list[str] = []
        preds: dict[str, list[str]] = {}
        sigma = {s: 1.0}
        dist = {s: 0}
        queue = deque([s])
        while queue:
            v = queue.popleft()
            order.append(v)
            for w in adj[v]:
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] = sigma.get(w, 0.0) + sigma[v]
                    preds.setdefault(w, []).append(v)
        delta = dict.fromkeys(order, 0.0)
        for w in reversed(order):
            for v in preds.get(w, ()):
                delta[v] += sigma[v] / sigma[w] * (1 + delta[w])
            if w != s:
                score[w] += delta[w]
    scale = (n / len(sources)) / ((n - 1) * (n - 2))  # undirected: each path counted twice
    return {v: score[v] * scale for v in nodes}


def pagerank(
    adj: dict[str, set[str]], damping: float = 0.85, iterations: int = 100
) -> dict[str, float]:
    """PageRank by power iteration; a note with no links spreads its share over every note."""
    nodes = list(adj)
    n = len(nodes)
    if not n:
        return {}
    rank = dict.fromkeys(nodes, 1 / n)
    for _ in range(iterations):
        lost = sum(rank[v] for v in nodes if not adj[v])
        new = dict.fromkeys(nodes, (1 - damping) / n + damping * lost / n)
        for v in nodes:
            if adj[v]:
                share = damping * rank[v] / len(adj[v])
                for w in adj[v]:
                    new[w] += share
        change = sum(abs(new[v] - rank[v]) for v in nodes)
        rank = new
        if change < 1e-10:
            break
    return rank


def clustering(adj: dict[str, set[str]]) -> tuple[float, float]:
    """The average local clustering coefficient (over notes with two or more neighbours) and the
    transitivity (the share of connected triples that close into a triangle)."""
    local, triangles, triples = [], 0, 0
    for v, nbs in adj.items():
        k = len(nbs)
        if k < 2:
            continue
        closed = sum(1 for a in nbs for b in adj[a] if b in nbs) // 2
        local.append(closed / (k * (k - 1) / 2))
        triangles += closed
        triples += k * (k - 1) // 2
    average = sum(local) / len(local) if local else 0.0
    return average, (triangles / triples if triples else 0.0)


def components(adj: dict[str, set[str]]) -> list[int]:
    seen: set[str] = set()
    sizes = []
    for start in adj:
        if start in seen:
            continue
        seen.add(start)
        queue, size = deque([start]), 0
        while queue:
            v = queue.popleft()
            size += 1
            for w in adj[v]:
                if w not in seen:
                    seen.add(w)
                    queue.append(w)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def network_stats(note_ids: Iterable[str], links: Iterable[Link]) -> NetworkStats:
    adj = neighbours(note_ids, links)
    degrees = {v: len(nbs) for v, nbs in adj.items()}
    average, transitivity = clustering(adj)
    return NetworkStats(
        degrees=degrees,
        distribution=degree_distribution(adj),
        power_law=fit_power_law(degrees.values()),
        betweenness=betweenness(adj),
        pagerank=pagerank(adj),
        clustering=average,
        transitivity=transitivity,
        components=components(adj),
    )
