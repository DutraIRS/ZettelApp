"""Hybrid search: fuzzy, lexical (FTS5/BM25) and fused ranking.

The ontology layer (tag_relationships, expand_tag) lives in storage; search
consumes it through vault.expand_tag only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from rapidfuzz import fuzz

from zettelapp.core.storage import Vault

SIGNALS = ("fuzzy", "lexical", "semantic", "ontology")

DEFAULT_WEIGHTS = {"fuzzy": 0.25, "lexical": 0.45, "semantic": 0.20, "ontology": 0.10}
DEFAULT_FUZZY_THRESHOLD = 70.0


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """Drop unavailable signals and renormalize so the weights sum to 1."""
    usable = {k: float(v) for k, v in weights.items() if k in SIGNALS and v > 0}
    total = sum(usable.values())
    if total <= 0:
        n = len(usable) or 1
        return {k: 1.0 / n for k in usable}
    return {k: v / total for k, v in usable.items()}


@dataclass
class SearchResult:
    note_id: str
    title: str
    snippet: str
    score: float
    signals: dict[str, float]
    matched_via: tuple[str, ...]


def _tokens(query: str) -> list[str]:
    return re.findall(r"\w+", query, flags=re.UNICODE)


class FuzzySearchProvider:
    """Approximate matching over note titles and tags (indexed candidates)."""

    def __init__(self, threshold: float = DEFAULT_FUZZY_THRESHOLD):
        self.threshold = threshold

    def search(self, query: str, vault: Vault, limit: int = 200) -> dict[str, float]:
        token = query.strip()
        if len(token) < 2:
            return {}
        folded = token.casefold()
        scores: dict[str, float] = {}
        for note in vault.all_notes():
            best = 0.0
            for candidate in (note.display_title, *note.tags):
                if not candidate:
                    continue
                score = max(
                    fuzz.ratio(folded, candidate.casefold()),
                    fuzz.partial_ratio(folded, candidate.casefold()),
                )
                best = max(best, score)
            if best >= self.threshold:
                scores[note.id] = best / 100.0
        if len(scores) > limit:
            top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:limit]
            scores = dict(top)
        return scores


class FullTextSearchProvider:
    """BM25 retrieval through the existing notes_fts index (LIKE fallback)."""

    def search(self, query: str, vault: Vault) -> dict[str, float]:
        ids = vault.search(query)
        if not ids:
            return {}
        rank = 1.0
        scores: dict[str, float] = {}
        for note_id in ids:
            scores[note_id] = rank
            rank = max(0.05, rank * 0.995)
        return scores


class OntologySignal:
    """Scores notes whose tags are ontology-close to the query terms."""

    def __init__(self, vault: Vault):
        self.vault = vault

    def tag_matches(self, query: str, include_related: bool = False) -> dict[str, float]:
        """Tag-name similarity per query token, expanded by the ontology."""
        tokens = _tokens(query)
        if not tokens:
            return {}
        names = self.vault.all_tag_names()
        out: dict[str, float] = {}
        for token in tokens:
            folded = token.casefold()
            best_name, best = "", 0.0
            for name in names:
                score = fuzz.partial_ratio(folded, name.casefold())
                if score > best:
                    best_name, best = name, score
            if best < 70.0 or not best_name:
                continue
            expanded = self.vault.expand_tag(best_name, include_related=include_related)
            for tag in expanded:
                out[tag] = max(out.get(tag, 0.0), best / 100.0)
        return out

    def search(self, query: str, vault: Vault) -> dict[str, float]:
        tag_scores = self.tag_matches(query)
        if not tag_scores:
            return {}
        scores: dict[str, float] = {}
        for tag, tag_score in tag_scores.items():
            for note_id in vault.notes_with_tags([tag]):
                scores[note_id] = max(scores.get(note_id, 0.0), tag_score)
        return scores


class RankingEngine:
    """Weighted fusion of normalized signal scores (deterministic by default)."""

    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = normalize_weights(weights or DEFAULT_WEIGHTS)

    def rank(self, signal_scores: dict[str, dict[str, float]]) -> list[SearchResult]:
        weights = normalize_weights(self.weights)
        fused: dict[str, dict[str, float]] = {}
        for signal, scores in signal_scores.items():
            if signal not in weights:
                continue
            peak = max(scores.values(), default=0.0)
            if peak <= 0:
                continue
            for note_id, score in scores.items():
                fused.setdefault(note_id, {})[signal] = score / peak
        results = []
        for note_id, signals in fused.items():
            score = sum(weights[s] * v for s, v in signals.items())
            results.append(
                SearchResult(
                    note_id=note_id,
                    title="",
                    snippet="",
                    score=score,
                    signals=signals,
                    matched_via=tuple(sorted(s for s in weights if s in signals)),
                )
            )
        results.sort(key=lambda r: (-r.score, r.note_id))
        return results


class SearchService:
    """Facade wiring providers, optional semantic scores and the ranker."""

    def __init__(self, vault: Vault, weights: dict[str, float] | None = None):
        self.vault = vault
        self.fuzzy = FuzzySearchProvider()
        self.full_text = FullTextSearchProvider()
        self.ontology = OntologySignal(vault)
        self.ranker = RankingEngine(weights)

    def search(
        self,
        query: str,
        semantic_scores: dict[str, float] | None = None,
        include_related_tags: bool = False,
    ) -> list[SearchResult]:
        signals: dict[str, dict[str, float]] = {
            "fuzzy": self.fuzzy.search(query, self.vault),
            "lexical": self.full_text.search(query, self.vault),
            "ontology": self.ontology.search(query, self.vault),
        }
        if semantic_scores:
            signals["semantic"] = semantic_scores
        results = self.ranker.rank(signals)
        notes = {n.id: n for n in self.vault.all_notes(include_deleted=True)}
        for r in results:
            note = notes.get(r.note_id)
            if note is None:
                continue
            r.title = note.display_title
            r.snippet = highlight_snippet(note.body, query)
        return results


def highlight_snippet(body: str, query: str, length: int = 160) -> str:
    """Contextual snippet centred on the first query token match."""
    tokens = _tokens(query)
    text = body.replace("\n", " ").strip()
    if not tokens:
        return text[:length]
    lowered = text.casefold()
    pos = min(
        (p for p in (lowered.find(t.casefold()) for t in tokens) if p >= 0),
        default=-1,
    )
    if pos < 0:
        return text[:length]
    start = max(0, pos - length // 3)
    out = text[start : start + length]
    return ("…" if start else "") + out + ("…" if start + length < len(text) else "")
