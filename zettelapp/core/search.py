"""Hybrid search for the note list: full text, typo-tolerant titles and tags, the tag ontology
and, when switched on, the meaning of the text, fused into one ranking.

`tag:` filters and the set of notes being searched (the Trash or the rest) bind every signal.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from rapidfuzz import fuzz, process

from zettelapp.core.models import Note
from zettelapp.core.storage import Vault, split_query
from zettelapp.core.textutil import tokenize

SIGNALS = ("fuzzy", "lexical", "semantic", "ontology")
MIN_FUZZY_LENGTH = 3
# How alike two whole words must be: a typo finds the word meant ("quantom" finds "quantum"),
# but one wrong letter in a short word finds nothing ("math" must not find "path").
FUZZY_CUTOFF = 85.0


@dataclass(frozen=True)
class SearchResult:
    note_id: str
    score: float
    signals: dict[str, float]  # each signal's share of the score, from 0 to 1


def _long_words(text: str) -> list[str]:
    return [word for word in tokenize(text) if len(word) >= MIN_FUZZY_LENGTH]


def fuzzy_scores(text: str, notes: Iterable[Note]) -> dict[str, float]:
    """Notes with every word of the text, or nearly, in their title or tags."""
    words = _long_words(text)
    if not words:
        return {}
    vocabulary: dict[str, set[str]] = defaultdict(set)
    for note in notes:
        for word in tokenize(" ".join((note.display_title, *note.tags))):
            vocabulary[word].add(note.id)
    known = list(vocabulary)
    found: dict[str, float] = {}
    for position, word in enumerate(words):
        near: dict[str, float] = {}
        for match, score, _index in process.extract(
            word, known, scorer=fuzz.ratio, score_cutoff=FUZZY_CUTOFF, limit=None
        ):
            for note_id in vocabulary[match]:
                near[note_id] = max(near.get(note_id, 0.0), score / 100)
        found = near if position == 0 else {i: found[i] + s for i, s in near.items() if i in found}
    return {note_id: total / len(words) for note_id, total in found.items()}


def lexical_scores(ranked_ids: list[str]) -> dict[str, float]:
    """BM25 values can't be compared between queries, so a hit scores by its place in the list."""
    return {note_id: max(0.05, 0.995**place) for place, note_id in enumerate(ranked_ids)}


def ontology_scores(vault: Vault, text: str, include_related: bool = False) -> dict[str, float]:
    """Notes filed under a tag that a word of the text names, or that the tag ontology links
    to one: searching for a parent finds its children's notes, whatever they are called."""
    words = _long_words(text)
    names = vault.all_tag_names()
    if not words or not names:
        return {}
    notes = vault.notes_by_tag()
    graph = vault.tag_graph()
    scores: dict[str, float] = {}
    for name in names:
        parts = tokenize(name)
        best = [
            process.extractOne(word, parts, scorer=fuzz.ratio, score_cutoff=FUZZY_CUTOFF)
            for word in words
        ]
        match = max((b[1] for b in best if b), default=0.0)
        if not match:
            continue
        for tag in graph.expand(name, include_related):
            for note_id in notes.get(tag, ()):
                scores[note_id] = max(scores.get(note_id, 0.0), match / 100)
    return scores


def rank(signals: dict[str, dict[str, float]], weights: dict[str, float]) -> list[SearchResult]:
    """Fuse the signals' scores, each scaled so that its best hit counts 1; best first."""
    fused: dict[str, dict[str, float]] = {}
    for signal, scores in signals.items():
        peak = max(scores.values(), default=0.0)
        for note_id, score in scores.items():
            fused.setdefault(note_id, {})[signal] = score / peak
    results = [
        SearchResult(note_id, sum(weights[s] * v for s, v in parts.items()), parts)
        for note_id, parts in fused.items()
    ]
    results.sort(key=lambda r: (-r.score, r.note_id))
    return results


def hybrid_search(
    vault: Vault,
    query: str,
    notes: Iterable[Note],
    weights: dict[str, float],
    semantic: dict[str, float] | None = None,
    include_related: bool = False,
    include_deleted: bool = False,
) -> list[SearchResult]:
    """Rank *notes* for a query. A signal with no weight is off and finds nothing, unless all
    of them are off: then plain full-text search still works."""
    weights = {s: w for s, w in weights.items() if s in SIGNALS and w > 0} or {"lexical": 1.0}
    text, tags = split_query(query)
    allowed = {n.id: n for n in notes}
    if tags:
        tagged = vault.notes_with_tags(tags, include_related=include_related)
        allowed = {i: n for i, n in allowed.items() if i in tagged}
    found: dict[str, dict[str, float]] = {}
    if "lexical" in weights:
        ids = vault.search(query, include_deleted, include_related)
        found["lexical"] = lexical_scores([i for i in ids if i in allowed])
    if "fuzzy" in weights:
        found["fuzzy"] = fuzzy_scores(text, allowed.values())
    if "ontology" in weights:
        found["ontology"] = ontology_scores(vault, text, include_related)
    if semantic and "semantic" in weights:
        found["semantic"] = semantic
    return rank(
        {s: {i: v for i, v in scores.items() if i in allowed} for s, scores in found.items()},
        weights,
    )
