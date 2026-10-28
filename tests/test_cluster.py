import numpy as np

from zettelapp.core.cluster import agglomerative, cluster_notes, kmeans, silhouette
from zettelapp.core.graph import force_layout
from zettelapp.core.models import Note


def blobs(seed=0):
    rng = np.random.default_rng(seed)
    centres = np.array([[5, 0, 0], [0, 5, 0], [0, 0, 5]], dtype=float)
    x = np.vstack([c + rng.normal(0, 0.3, (30, 3)) for c in centres])
    return x, np.repeat([0, 1, 2], 30)


def same_partition(a, b):
    pairs_a = {(i, j) for i in range(len(a)) for j in range(i) if a[i] == a[j]}
    pairs_b = {(i, j) for i in range(len(b)) for j in range(i) if b[i] == b[j]}
    return pairs_a == pairs_b


def test_kmeans_recovers_blobs():
    x, truth = blobs()
    labels, centers, inertia = kmeans(x, 3)
    assert same_partition(labels, truth)
    assert centers.shape == (3, 3) and inertia > 0


def test_agglomerative_recovers_blobs():
    x, truth = blobs(1)
    assert same_partition(agglomerative(x, 3), truth)
    assert len(set(agglomerative(x, 1).tolist())) == 1


def test_silhouette_prefers_true_k():
    x, truth = blobs(2)
    assert silhouette(x, truth) > silhouette(x, kmeans(x, 2)[0])


def test_cluster_notes_names_clusters():
    topics = {
        "memory": "memory recall retention review spaced repetition forgetting",
        "bread": "bread flour dough yeast oven baking crust",
        "space": "planet orbit star galaxy telescope astronomy",
    }
    notes = []
    for t, words in topics.items():
        w = words.split()
        for i in range(6):
            notes.append(
                Note(
                    id=f"2026010100{len(notes):04d}",
                    title=f"{t} {i}",
                    body=" ".join(w[i % len(w) :] + w[: i % len(w)]),
                )
            )
    result = cluster_notes(notes, "kmeans")
    assert result.k == 3
    by_cluster = {}
    for n in notes:
        by_cluster.setdefault(result.label_of()[n.id], set()).add(n.title.split()[0])
    assert all(len(v) == 1 for v in by_cluster.values())
    assert any("bread" in kw or "dough" in kw for kw in result.keywords.values())
    hier = cluster_notes(notes, "hierarchical", k=3)
    assert len(set(hier.labels.tolist())) == 3


def test_group_layout_pulls_groups_together():
    nodes = [str(i) for i in range(40)]
    groups = {n: int(n) % 2 for n in nodes}
    pos = force_layout(nodes, [], groups=groups, group_strength=1.0, seed=3)
    xy = np.array([pos[n] for n in nodes])
    g = np.array([groups[n] for n in nodes])
    within = np.mean(
        [np.linalg.norm(xy[g == c] - xy[g == c].mean(0), axis=1).mean() for c in (0, 1)]
    )
    between = np.linalg.norm(xy[g == 0].mean(0) - xy[g == 1].mean(0))
    assert between > within * 0.5
    pos3 = force_layout(nodes, [("0", "1")], dims=3)
    assert len(pos3["0"]) == 3
