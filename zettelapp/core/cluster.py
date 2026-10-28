"""Clustering notes by meaning: k-means and hierarchical (average linkage).

Notes are embedded with LSA (see SemanticIndex), so clusters group notes
that talk about related things even when they are not linked. Each cluster
is named by the terms that distinguish it from the rest of the vault.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from zettelapp.core.models import Note
from zettelapp.core.similarity import SemanticIndex
from zettelapp.core.textutil import tokenize

MAX_HIERARCHICAL = 4000  # the distance matrix is n x n


@dataclass
class Clustering:
    ids: list[str]
    labels: np.ndarray  # cluster number per note, 0 = largest cluster
    keywords: dict[int, list[str]]
    method: str
    k: int
    silhouette: float | None = None

    def label_of(self) -> dict[str, int]:
        return {note_id: int(c) for note_id, c in zip(self.ids, self.labels)}


def embed_notes(notes: Sequence[Note], dims: int = 48) -> tuple[SemanticIndex, np.ndarray]:
    index = SemanticIndex(
        {n.id: tokenize(n.title) * 2 + tokenize(n.body) + list(n.tags) for n in notes},
        lsa_dims=dims,
    )
    if index.embeddings is not None:
        return index, index.embeddings
    # Too few notes for LSA: fall back to dense, normalised TF-IDF vectors.
    x = np.zeros((len(index), max(1, len(index.vocab))))
    for i, vec in enumerate(index.vectors):
        for term, w in vec.items():
            x[i, term] = w
    return index, x


def _kmeans_pp(x: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    centers = [x[rng.integers(len(x))]]
    d2 = ((x - centers[0]) ** 2).sum(axis=1)
    for _ in range(1, k):
        total = d2.sum()
        idx = rng.choice(len(x), p=d2 / total) if total > 0 else rng.integers(len(x))
        centers.append(x[idx])
        d2 = np.minimum(d2, ((x - x[idx]) ** 2).sum(axis=1))
    return np.array(centers)


def kmeans(
    x: np.ndarray, k: int, n_init: int = 6, max_iter: int = 100, seed: int = 0
) -> tuple[np.ndarray, np.ndarray, float]:
    """Lloyd's algorithm with k-means++ seeding; returns (labels, centers, inertia)."""
    n = len(x)
    k = max(1, min(k, n))
    rng = np.random.default_rng(seed)
    sq = (x**2).sum(axis=1)
    best: tuple[np.ndarray, np.ndarray, float] | None = None
    for _ in range(n_init):
        centers = _kmeans_pp(x, k, rng)
        labels = np.zeros(n, dtype=int)
        for _ in range(max_iter):
            dist = sq[:, None] - 2 * x @ centers.T + (centers**2).sum(axis=1)[None, :]
            labels = dist.argmin(axis=1)
            new = centers.copy()
            for j in range(k):
                members = labels == j
                new[j] = x[members].mean(axis=0) if members.any() else x[rng.integers(n)]
            if np.allclose(new, centers):
                break
            centers = new
        dist = sq[:, None] - 2 * x @ centers.T + (centers**2).sum(axis=1)[None, :]
        inertia = float(np.maximum(dist[np.arange(n), labels], 0).sum())
        if best is None or inertia < best[2]:
            best = (labels, centers, inertia)
    assert best is not None  # n_init >= 1
    return best


def agglomerative(x: np.ndarray, k: int) -> np.ndarray:
    """Average-linkage clustering on cosine distance (nearest-neighbour chain, O(n^2))."""
    n = len(x)
    if k >= n:
        return np.arange(n)
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    unit = np.divide(x, norms, out=np.zeros_like(x), where=norms > 0)
    d = 1.0 - np.clip(unit @ unit.T, -1.0, 1.0)
    np.fill_diagonal(d, np.inf)
    size = np.ones(n)
    active = np.ones(n, dtype=bool)
    merges: list[tuple[float, int, int]] = []
    chain: list[int] = []
    remaining = n
    while remaining > 1:
        if not chain:
            chain.append(int(np.flatnonzero(active)[0]))
        a = chain[-1]
        row = d[a]
        b = int(np.argmin(row))
        if len(chain) > 1 and row[chain[-2]] <= row[b]:
            b = chain[-2]
        if len(chain) > 1 and b == chain[-2]:
            chain.pop()
            chain.pop()
            merges.append((float(d[a, b]), a, b))
            merged = (size[a] * d[a] + size[b] * d[b]) / (size[a] + size[b])  # Lance-Williams
            merged[a] = np.inf
            d[a, :] = merged
            d[:, a] = merged
            d[b, :] = np.inf
            d[:, b] = np.inf
            size[a] += size[b]
            active[b] = False
            remaining -= 1
        else:
            chain.append(b)
    # Average linkage is reducible, so sorting the chain's merges gives the dendrogram.
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for _, a, b in sorted(merges)[: n - k]:
        parent[find(b)] = find(a)
    roots = [find(i) for i in range(n)]
    _, labels = np.unique(roots, return_inverse=True)
    return labels


def silhouette(x: np.ndarray, labels: np.ndarray, sample: int = 1500, seed: int = 0) -> float:
    """Mean silhouette coefficient on cosine distance (sampled for large vaults)."""
    n = len(x)
    if len(set(labels.tolist())) < 2 or n < 3:
        return 0.0
    rng = np.random.default_rng(seed)
    idx = rng.choice(n, size=min(sample, n), replace=False)
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    unit = np.divide(x, norms, out=np.zeros_like(x), where=norms > 0)
    d = 1.0 - unit[idx] @ unit.T
    scores = []
    for row, i in enumerate(idx):
        own = labels == labels[i]
        if own.sum() <= 1:
            scores.append(0.0)
            continue
        a = d[row, own].sum() / (own.sum() - 1)
        b = min(d[row, labels == c].mean() for c in set(labels.tolist()) if c != labels[i])
        scores.append((b - a) / max(a, b) if max(a, b) > 0 else 0.0)
    return float(np.mean(scores))


def _relabel_by_size(labels: np.ndarray) -> np.ndarray:
    values, counts = np.unique(labels, return_counts=True)
    order = values[np.argsort(-counts, kind="stable")]
    mapping = {int(old): new for new, old in enumerate(order)}
    return np.array([mapping[int(v)] for v in labels])


def _keywords(index: SemanticIndex, labels: np.ndarray, top: int = 4) -> dict[int, list[str]]:
    terms = {i: t for t, i in index.vocab.items()}
    total: dict[int, float] = {}
    for vec in index.vectors:
        for t, w in vec.items():
            total[t] = total.get(t, 0.0) + w
    n = max(1, len(index.vectors))
    out = {}
    for c in sorted(set(labels.tolist())):
        members = np.flatnonzero(labels == c)
        inside: dict[int, float] = {}
        for i in members:
            for t, w in index.vectors[i].items():
                inside[t] = inside.get(t, 0.0) + w
        m = len(members)
        # Distinctiveness: mean weight inside the cluster minus mean weight elsewhere.
        score = {t: w / m - (total[t] - w) / max(1, n - m) for t, w in inside.items()}
        out[c] = [terms[t] for t, _ in sorted(score.items(), key=lambda kv: -kv[1])[:top]]
    return out


def cluster_notes(
    notes: Sequence[Note], method: str = "kmeans", k: int | None = None, seed: int = 0
) -> Clustering | None:
    """Cluster notes; *k* None picks the k with the best silhouette score."""
    if len(notes) < 3:
        return None
    index, x = embed_notes(notes)
    if method == "hierarchical" and len(notes) > MAX_HIERARCHICAL:
        method = "kmeans"

    def run(kk: int) -> np.ndarray:
        if method == "hierarchical":
            return agglomerative(x, kk)
        return kmeans(x, kk, seed=seed)[0]

    best_score = None
    if k is None:
        best_labels: np.ndarray | None = None
        best_score = -2.0
        # sqrt(n/2) is the classic rule of thumb; search a little around it.
        k_max = max(2, min(12, round(math.sqrt(len(notes) / 2)) + 2, len(notes) - 1))
        for kk in range(2, k_max + 1):
            labels = run(kk)
            score = silhouette(x, labels, seed=seed)
            if score > best_score + 1e-9:
                best_labels, best_score, k = labels, score, kk
        assert best_labels is not None and k is not None  # the loop runs at least once
        labels = best_labels
    else:
        k = max(1, min(k, len(notes)))
        labels = run(k)
    labels = _relabel_by_size(labels)
    return Clustering(list(index.ids), labels, _keywords(index, labels), method, int(k), best_score)
