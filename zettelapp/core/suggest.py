"""Link suggestions with a Naive Bayes classifier over similarity features.

For a note *q* and a candidate *c* we compute several similarity features
(semantic, lexical and string-distance based). Each feature is discretised
into bins, and the classifier estimates

    P(link | f1..fn)  ∝  P(link) * Π P(fi | link)

Training data comes from the vault itself: existing links are positive
examples, randomly sampled unlinked pairs are negatives, and suggestions the
user dismissed are extra negatives. The per-bin counts start from Dirichlet
pseudo-counts that encode a weak prior belief ("higher similarity makes a
link more likely"), so suggestions work in a new vault and sharpen as the
vault grows.

Two refinements keep the estimates honest:
- [[wiki links]] are removed from the text before features are computed;
  otherwise an inline link puts the target's title into the text and the
  model learns to recognise existing links instead of related ideas;
- the per-feature evidence is weighted (0.6) because several features are
  correlated (TF-IDF and LSA; the three string distances), which makes plain
  Naive Bayes overconfident (cf. feature-weighted Naive Bayes).
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np

from zettelapp.core.similarity import (
    SemanticIndex,
    jaccard,
    jaro_winkler_similarity,
    levenshtein_similarity,
)
from zettelapp.core.textutil import (
    STOPWORDS,
    WIKILINK_RE,
    WORD_RE,
    fold,
    normalize,
    strip_markdown,
    tokenize,
)
from zettelapp.i18n import N_


@dataclass(frozen=True)
class Feature:
    key: str
    label: str
    binary: bool = False


# Labels are translated where they are shown.
FEATURES: tuple[Feature, ...] = (
    Feature("semantic", N_("Semantic similarity (LSA)")),
    Feature("tfidf", N_("Shared keywords (TF-IDF cosine)")),
    Feature("title_lev", N_("Title similarity (Levenshtein)")),
    Feature("title_jw", N_("Title similarity (Jaro-Winkler)")),
    Feature("body_lev", N_("Text similarity (Levenshtein)")),
    Feature("tags", N_("Shared tags (Jaccard)")),
    Feature("mention", N_("Title mentioned in the text"), binary=True),
    Feature("neighbors", N_("Shared links (Jaccard)")),
)
FEATURE_KEYS = tuple(f.key for f in FEATURES)
_IDX = {k: i for i, k in enumerate(FEATURE_KEYS)}

BODY_PREFIX = 400  # characters compared with Levenshtein


class NaiveBayesLinkModel:
    """Binned (categorical) Naive Bayes with Dirichlet priors."""

    def __init__(
        self,
        bins: int = 8,
        prior_strength: float = 10.0,
        enabled: Iterable[str] | None = None,
        features: Sequence[Feature] = FEATURES,
        evidence_weight: float = 0.6,
    ):
        self.features = tuple(features)
        self.bins = bins
        self.prior_strength = prior_strength
        self.evidence_weight = evidence_weight
        keys = set(enabled) if enabled is not None else {f.key for f in self.features}
        self.enabled = np.array([f.key in keys for f in self.features])
        self.n_pos = 0.0
        self.n_neg = 0.0
        self.fit(np.zeros((0, len(self.features))), np.zeros(0))

    def _prior_counts(self) -> np.ndarray:
        b = np.arange(self.bins, dtype=float)
        pos = b + 1.0
        neg = (self.bins - b) ** 2
        prior = np.empty((2, len(self.features), self.bins))
        for i, f in enumerate(self.features):
            if f.binary:
                p = np.full(self.bins, 1e-3)
                n = np.full(self.bins, 1e-3)
                p[0], p[-1] = 0.6, 0.4
                n[0], n[-1] = 0.97, 0.03
            else:
                p, n = pos.copy(), neg.copy()
            prior[1, i] = p / p.sum()
            prior[0, i] = n / n.sum()
        return prior * self.prior_strength

    def binize(self, x: np.ndarray) -> np.ndarray:
        x = np.nan_to_num(np.asarray(x, dtype=float), nan=0.0)
        bins = np.clip((x * self.bins).astype(int), 0, self.bins - 1)
        for i, f in enumerate(self.features):
            if f.binary:
                bins[..., i] = np.where(x[..., i] >= 0.5, self.bins - 1, 0)
        return bins

    def fit(
        self, x: np.ndarray, y: np.ndarray, weights: np.ndarray | None = None
    ) -> NaiveBayesLinkModel:
        x = np.asarray(x, dtype=float).reshape(-1, len(self.features))
        y = np.asarray(y).astype(int)
        w = np.ones(len(y)) if weights is None else np.asarray(weights, dtype=float)
        self.counts = self._prior_counts()
        bins = self.binize(x)
        missing = np.isnan(x)
        for c in (0, 1):
            rows = y == c
            for i in range(len(self.features)):
                ok = rows & ~missing[:, i]
                np.add.at(self.counts[c, i], bins[ok, i], w[ok])
        self.n_pos = float(w[y == 1].sum())
        self.n_neg = float(w[y == 0].sum())
        # Pseudo-counts 1:3 mirror the negative sampling ratio used in training.
        self.class_counts = np.array([3.0 + self.n_neg, 1.0 + self.n_pos])
        self.log_probs = np.log(self.counts / self.counts.sum(axis=2, keepdims=True))
        return self

    @property
    def log_prior_odds(self) -> float:
        return math.log(self.class_counts[1] / self.class_counts[0])

    def log_ratios(self, x: np.ndarray) -> np.ndarray:
        """Per-feature log P(f|link) - log P(f|no link); 0 for missing/disabled features."""
        x = np.atleast_2d(np.asarray(x, dtype=float))
        bins = self.binize(x)
        feat = np.arange(len(self.features))
        ratios = self.log_probs[1, feat, bins] - self.log_probs[0, feat, bins]
        ratios[np.isnan(x)] = 0.0
        ratios[:, ~self.enabled] = 0.0
        return ratios * self.evidence_weight

    def predict_log_odds(self, x: np.ndarray) -> np.ndarray:
        return self.log_prior_odds + self.log_ratios(x).sum(axis=1)

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-self.predict_log_odds(x)))

    def importance(self) -> dict[str, float]:
        """Symmetric KL divergence between the class-conditional distributions."""
        p, q = np.exp(self.log_probs[1]), np.exp(self.log_probs[0])
        kl = ((p - q) * (self.log_probs[1] - self.log_probs[0])).sum(axis=1)
        return {f.key: float(v) if on else 0.0 for f, v, on in zip(self.features, kl, self.enabled)}


@dataclass(frozen=True)
class NoteData:
    id: str
    title: str
    body: str
    tags: frozenset[str] = frozenset()


@dataclass
class _Prepared:
    title: str
    body_prefix: str
    words: str
    title_words: str
    tokens: list[str]
    tags: frozenset[str]


@dataclass
class Suggestion:
    note_id: str
    title: str
    probability: float
    contributions: list[tuple[str, float]] = field(default_factory=list)
    features: dict[str, float] = field(default_factory=dict)


def _prepare(note: NoteData) -> _Prepared:
    plain = strip_markdown(
        WIKILINK_RE.sub(" ", note.body)
    )  # see module docstring: avoids label leakage
    words = WORD_RE.findall(fold(plain))
    title_words = WORD_RE.findall(fold(note.title))
    tag_tokens = [part for t in note.tags for part in t.split("/")]
    return _Prepared(
        title=normalize(note.title),
        body_prefix=normalize(plain)[:BODY_PREFIX],
        words=" " + " ".join(words) + " ",
        title_words=" ".join(title_words) if any(w not in STOPWORDS for w in title_words) else "",
        tokens=tokenize(note.title) * 2 + tokenize(plain) + tag_tokens,
        tags=note.tags,
    )


def _mentions(a: _Prepared, b: _Prepared) -> float:
    def inside(title: str, words: str) -> bool:
        return len(title) >= 4 and f" {title} " in words

    return 1.0 if inside(a.title_words, b.words) or inside(b.title_words, a.words) else 0.0


class LinkSuggester:
    def __init__(
        self,
        bins: int = 8,
        prior_strength: float = 10.0,
        enabled: Iterable[str] | None = None,
        negatives_per_positive: int = 3,
        max_positive_pairs: int = 600,
        prefilter: int = 150,
        seed: int = 13,
    ):
        self.model = NaiveBayesLinkModel(bins, prior_strength, enabled)
        self.negatives_per_positive = negatives_per_positive
        self.max_positive_pairs = max_positive_pairs
        self.prefilter = prefilter
        self.seed = seed
        self.notes: dict[str, NoteData] = {}
        self.prepared: dict[str, _Prepared] = {}
        self.index: SemanticIndex | None = None
        self.adjacency: dict[str, set[str]] = defaultdict(set)
        self.linked: set[tuple[str, str]] = set()
        self.rejected: set[tuple[str, str]] = set()
        self._cache: dict[str, tuple[str, str, frozenset[str], _Prepared]] = {}

    # --- corpus and training ---------------------------------------------

    def rebuild(
        self,
        notes: Sequence[NoteData],
        links: Iterable[tuple[str, str]],
        feedback: Mapping[tuple[str, str], int] | None = None,
    ) -> None:
        self.notes = {n.id: n for n in notes}
        prepared = {}
        for n in notes:
            cached = self._cache.get(n.id)
            if cached and cached[:3] == (n.title, n.body, n.tags):
                prepared[n.id] = cached[3]
            else:
                prepared[n.id] = _prepare(n)
                self._cache[n.id] = (n.title, n.body, n.tags, prepared[n.id])
        for stale in set(self._cache) - set(self.notes):
            del self._cache[stale]
        self.prepared = prepared
        self.index = SemanticIndex({i: p.tokens for i, p in prepared.items()})
        self.adjacency = defaultdict(set)
        self.linked = set()
        for a, b in links:
            if a in self.notes and b in self.notes and a != b:
                self.adjacency[a].add(b)
                self.adjacency[b].add(a)
                self.linked.add(_pair(a, b))
        feedback = feedback or {}
        self.rejected = {p for p, label in feedback.items() if not label}
        accepted = {
            p
            for p, label in feedback.items()
            if label and p[0] in self.notes and p[1] in self.notes
        }
        self._train(accepted)

    def _train(self, accepted: set[tuple[str, str]]) -> None:
        rng = random.Random(self.seed)
        positives = sorted(self.linked | accepted)
        if len(positives) > self.max_positive_pairs:
            positives = rng.sample(positives, self.max_positive_pairs)
        negatives = [p for p in sorted(self.rejected) if p[0] in self.notes and p[1] in self.notes]
        ids = sorted(self.notes)
        wanted = max(20, self.negatives_per_positive * len(positives)) if len(ids) > 2 else 0
        seen = set(negatives)
        attempts = 0
        sampled: list[tuple[str, str]] = []
        while len(sampled) < wanted and attempts < wanted * 20:
            attempts += 1
            a, b = rng.sample(ids, 2)
            pair = _pair(a, b)
            if pair in self.linked or pair in seen or pair in accepted:
                continue
            seen.add(pair)
            sampled.append(pair)
        pairs = positives + negatives + sampled
        if not pairs:
            self.model.fit(np.zeros((0, len(FEATURES))), np.zeros(0))
            return
        x = np.array([self._pair_features(a, b, training=True) for a, b in pairs])
        y = np.array([1] * len(positives) + [0] * (len(negatives) + len(sampled)))
        w = np.array([1.0] * len(positives) + [2.0] * len(negatives) + [1.0] * len(sampled))
        self.model.fit(x, y, w)

    def _pair_features(self, a: str, b: str, training: bool = False) -> np.ndarray:
        pa, pb = self.prepared[a], self.prepared[b]
        assert self.index is not None  # built in refit() before any pair is scored
        i, j = self.index.position[a], self.index.position[b]
        f = np.full(len(FEATURES), np.nan)
        f[_IDX["tfidf"]] = self.index.pair_cosine(i, j)
        lsa = self.index.pair_lsa(i, j)
        f[_IDX["semantic"]] = f[_IDX["tfidf"]] if lsa is None else lsa
        f[_IDX["title_lev"]] = levenshtein_similarity(pa.title, pb.title)
        f[_IDX["title_jw"]] = jaro_winkler_similarity(pa.title, pb.title)
        f[_IDX["body_lev"]] = levenshtein_similarity(pa.body_prefix, pb.body_prefix)
        f[_IDX["tags"]] = jaccard(set(pa.tags), set(pb.tags))
        f[_IDX["mention"]] = _mentions(pa, pb)
        na, nb = self.adjacency.get(a, set()), self.adjacency.get(b, set())
        if training:  # do not let the link being predicted leak into the feature
            na, nb = na - {b}, nb - {a}
        f[_IDX["neighbors"]] = jaccard(na, nb)
        return f

    # --- prediction -------------------------------------------------------

    def suggest(
        self,
        note: NoteData,
        limit: int = 8,
        min_probability: float = 0.3,
        exclude: Iterable[str] = (),
    ) -> list[Suggestion]:
        if self.index is None or not self.notes:
            return []
        q = _prepare(note)
        if not q.tokens and not q.title:
            return []
        excluded = set(exclude) | {note.id} | self.adjacency.get(note.id, set())
        excluded |= {b if a == note.id else a for a, b in self.rejected if note.id in (a, b)}
        candidates = [i for i in self.index.ids if i not in excluded]
        if not candidates:
            return []
        pos = np.array([self.index.position[c] for c in candidates])
        vec = self.index.vectorize(q.tokens)
        tfidf = self.index.cosine_all(vec)[pos]
        lsa_all = self.index.lsa_all(vec)
        lsa = tfidf if lsa_all is None else lsa_all[pos]

        x = np.full((len(candidates), len(FEATURES)), np.nan)
        x[:, _IDX["tfidf"]] = tfidf
        x[:, _IDX["semantic"]] = lsa
        neighbors = self.adjacency.get(note.id, set())
        for row, cid in enumerate(candidates):
            p = self.prepared[cid]
            x[row, _IDX["title_lev"]] = levenshtein_similarity(q.title, p.title)
            x[row, _IDX["title_jw"]] = jaro_winkler_similarity(q.title, p.title)
            x[row, _IDX["tags"]] = jaccard(set(q.tags), set(p.tags))
            x[row, _IDX["mention"]] = _mentions(q, p)
            x[row, _IDX["neighbors"]] = jaccard(neighbors, self.adjacency.get(cid, set()))

        # Two-stage ranking: the costly body Levenshtein only for the best candidates.
        partial = self.model.predict_log_odds(x)
        top = np.argsort(-partial)[: self.prefilter]
        for row in top:
            x[row, _IDX["body_lev"]] = levenshtein_similarity(
                q.body_prefix, self.prepared[candidates[row]].body_prefix
            )
        x_top = x[top]
        ratios = self.model.log_ratios(x_top)
        probs = 1.0 / (1.0 + np.exp(-(self.model.log_prior_odds + ratios.sum(axis=1))))
        order = np.argsort(-probs)
        out = []
        for k in order[:limit]:
            if probs[k] < min_probability:
                break
            cid = candidates[top[k]]
            contributions = sorted(
                (
                    (f.label, float(r))
                    for f, r, on in zip(FEATURES, ratios[k], self.model.enabled)
                    if on
                ),
                key=lambda item: -abs(item[1]),
            )
            out.append(
                Suggestion(
                    note_id=cid,
                    title=self.notes[cid].title or "Untitled",
                    probability=float(probs[k]),
                    contributions=contributions,
                    features={f.key: float(v) for f, v in zip(FEATURES, x_top[k])},
                )
            )
        return out

    def report(self) -> dict:
        return {
            "positives": self.model.n_pos,
            "negatives": self.model.n_neg,
            "notes": len(self.notes),
            "importance": self.model.importance(),
        }


def _pair(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a <= b else (b, a)
