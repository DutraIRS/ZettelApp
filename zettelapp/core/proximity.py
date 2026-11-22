"""How close notes are to one note: by meaning (LSA) or by links."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Sequence

import numpy as np

from zettelapp.core.cluster import embed_notes
from zettelapp.core.graph import adjacency
from zettelapp.core.models import Link, Note


class MeaningIndex:
    """LSA embeddings of a set of notes, built once and asked about any of them."""

    def __init__(self, notes: Sequence[Note]):
        self.position = {n.id: i for i, n in enumerate(notes)}
        self.vectors = embed_notes(notes)[1] if len(notes) >= 2 else np.zeros((len(notes), 1))
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        self.vectors = np.divide(
            self.vectors, norms, out=np.zeros_like(self.vectors), where=norms > 0
        )

    def closeness(self, note_id: str) -> dict[str, float]:
        """Cosine similarity of every note to *note_id* (empty if it isn't indexed)."""
        row = self.position.get(note_id)
        if row is None:
            return {}
        scores = self.vectors @ self.vectors[row]
        return {i: float(scores[p]) for i, p in self.position.items()}


def link_closeness(note_id: str, links: Iterable[Link]) -> dict[str, float]:
    """Notes reachable from *note_id* through links (either direction), scored so that
    fewer links away is higher: 1 for the note itself, 1/2 one link away, 1/3 two away..."""
    adj = adjacency(links)
    distance = {note_id: 0}
    queue = deque([note_id])
    while queue:
        here = queue.popleft()
        for other in adj.get(here, ()):
            if other not in distance:
                distance[other] = distance[here] + 1
                queue.append(other)
    return {i: 1.0 / (d + 1) for i, d in distance.items()}
