"""String distances and a TF-IDF / LSA semantic index.

RapidFuzz is used when it is installed; the pure-Python fallbacks give the
same results (Levenshtein uses Hyyrö's bit-parallel algorithm, so it stays
usable on long strings).
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence

import numpy as np

try:  # pragma: no cover - exercised implicitly
    from rapidfuzz.distance import JaroWinkler as _RFJaroWinkler
    from rapidfuzz.distance import Levenshtein as _RFLevenshtein
except ImportError:  # pragma: no cover
    _RFLevenshtein = None
    _RFJaroWinkler = None


# --- edit distances ---------------------------------------------------------

def _levenshtein_bitparallel(text: str, pattern: str) -> int:
    if not pattern:
        return len(text)
    if not text:
        return len(pattern)
    m = len(pattern)
    full = (1 << m) - 1
    last = 1 << (m - 1)
    peq: dict[str, int] = {}
    bit = 1
    for ch in pattern:
        peq[ch] = peq.get(ch, 0) | bit
        bit <<= 1
    vp, vn, dist = full, 0, m
    for ch in text:
        x = peq.get(ch, 0) | vn
        d0 = (((x & vp) + vp) ^ vp) | x
        hp = vn | (~(d0 | vp) & full)
        hn = d0 & vp
        if hp & last:
            dist += 1
        elif hn & last:
            dist -= 1
        hp = ((hp << 1) | 1) & full
        hn = (hn << 1) & full
        vp = hn | (~(d0 | hp) & full)
        vn = hp & d0
    return dist


def levenshtein_distance(a: str, b: str) -> int:
    if _RFLevenshtein is not None:
        return _RFLevenshtein.distance(a, b)
    if len(a) < len(b):
        a, b = b, a
    return _levenshtein_bitparallel(a, b)


def levenshtein_similarity(a: str, b: str) -> float:
    """1 - distance / max(len); 0.0 when either string is empty."""
    if not a or not b:
        return 0.0
    return 1.0 - levenshtein_distance(a, b) / max(len(a), len(b))


def _jaro_winkler_python(a: str, b: str, prefix_weight: float = 0.1) -> float:
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if not la or not lb:
        return 0.0
    window = max(max(la, lb) // 2 - 1, 0)
    a_flags = [False] * la
    b_flags = [False] * lb
    matches = 0
    for i, ch in enumerate(a):
        lo, hi = max(0, i - window), min(i + window + 1, lb)
        for j in range(lo, hi):
            if not b_flags[j] and b[j] == ch:
                a_flags[i] = b_flags[j] = True
                matches += 1
                break
    if not matches:
        return 0.0
    transpositions, j = 0, 0
    for i in range(la):
        if a_flags[i]:
            while not b_flags[j]:
                j += 1
            if a[i] != b[j]:
                transpositions += 1
            j += 1
    t = transpositions / 2
    jaro = (matches / la + matches / lb + (matches - t) / matches) / 3
    if jaro <= 0.7:  # Winkler's boost threshold
        return jaro
    prefix = 0
    for ca, cb in zip(a[:4], b[:4]):
        if ca != cb:
            break
        prefix += 1
    return jaro + prefix * prefix_weight * (1 - jaro)


def jaro_winkler_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if _RFJaroWinkler is not None:
        return _RFJaroWinkler.similarity(a, b)
    return _jaro_winkler_python(a, b)


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# --- TF-IDF and latent semantic analysis -----------------------------------

class SemanticIndex:
    """TF-IDF vectors plus an LSA embedding (truncated SVD) of a corpus.

    LSA projects documents into a low-rank "concept" space where notes that use
    related vocabulary end up close even if they share few exact words.
    """

    def __init__(self, docs: Mapping[str, Sequence[str]], lsa_dims: int = 64, seed: int = 7):
        self.ids = list(docs)
        self.position = {doc_id: i for i, doc_id in enumerate(self.ids)}
        n = len(self.ids)
        df: Counter[str] = Counter()
        for tokens in docs.values():
            df.update(set(tokens))
        self.vocab = {term: i for i, term in enumerate(sorted(df))}
        self.idf = np.array([math.log((1 + n) / (1 + df[t])) + 1.0 for t in sorted(df)], dtype=np.float64)
        self.vectors: list[dict[int, float]] = [self.vectorize(docs[doc_id]) for doc_id in self.ids]
        self.postings: dict[int, list[tuple[int, float]]] = {}
        for i, vec in enumerate(self.vectors):
            for term, weight in vec.items():
                self.postings.setdefault(term, []).append((i, weight))
        self.components: np.ndarray | None = None  # (dims, vocab) projection
        self.embeddings: np.ndarray | None = None  # (n, dims), unit rows
        self._fit_lsa(lsa_dims, seed)

    def __len__(self) -> int:
        return len(self.ids)

    def vectorize(self, tokens: Sequence[str]) -> dict[int, float]:
        counts = Counter(t for t in tokens if t in self.vocab)
        vec = {self.vocab[t]: (1.0 + math.log(c)) * self.idf[self.vocab[t]] for t, c in counts.items()}
        norm = math.sqrt(sum(w * w for w in vec.values()))
        return {k: w / norm for k, w in vec.items()} if norm else {}

    def cosine_all(self, vec: Mapping[int, float]) -> np.ndarray:
        """TF-IDF cosine similarity between *vec* and every document."""
        scores = np.zeros(len(self.ids))
        for term, weight in vec.items():
            for i, w in self.postings.get(term, ()):
                scores[i] += weight * w
        return np.clip(scores, 0.0, 1.0)

    def _sparse_rows(self):
        rows, cols, vals = [], [], []
        for i, vec in enumerate(self.vectors):
            for term, w in vec.items():
                rows.append(i)
                cols.append(term)
                vals.append(w)
        return np.array(rows, dtype=np.int64), np.array(cols, dtype=np.int64), np.array(vals, dtype=np.float64)

    def _fit_lsa(self, dims: int, seed: int) -> None:
        n, v = len(self.ids), len(self.vocab)
        k = min(dims, n - 1, v - 1)
        if k < 2:
            return
        rows, cols, vals = self._sparse_rows()
        chunk = 65536  # bounds the temporary (chunk x r) array

        def x_dot(m: np.ndarray) -> np.ndarray:  # X @ m, X is (n, v)
            out = np.zeros((n, m.shape[1]))
            for s in range(0, len(vals), chunk):
                np.add.at(out, rows[s:s + chunk], vals[s:s + chunk, None] * m[cols[s:s + chunk]])
            return out

        def xt_dot(m: np.ndarray) -> np.ndarray:  # X.T @ m
            out = np.zeros((v, m.shape[1]))
            for s in range(0, len(vals), chunk):
                np.add.at(out, cols[s:s + chunk], vals[s:s + chunk, None] * m[rows[s:s + chunk]])
            return out

        # Randomised truncated SVD (Halko, Martinsson & Tropp 2011).
        rng = np.random.default_rng(seed)
        r = min(k + 10, n, v)
        q, _ = np.linalg.qr(x_dot(rng.standard_normal((v, r))))
        for _ in range(2):  # power iterations sharpen the spectrum
            q, _ = np.linalg.qr(xt_dot(q))
            q, _ = np.linalg.qr(x_dot(q))
        b = xt_dot(q).T  # (r, v) = Q^T X
        _, s, vt = np.linalg.svd(b, full_matrices=False)
        keep = s[:k] > 1e-10
        if keep.sum() < 2:
            return
        self.components = vt[:k][keep]
        emb = x_dot(self.components.T)
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        self.embeddings = np.divide(emb, norms, out=np.zeros_like(emb), where=norms > 0)

    def embed(self, vec: Mapping[int, float]) -> np.ndarray | None:
        if self.components is None:
            return None
        e = np.zeros(self.components.shape[0])
        for term, w in vec.items():
            e += w * self.components[:, term]
        norm = np.linalg.norm(e)
        return e / norm if norm else e

    def lsa_all(self, vec: Mapping[int, float]) -> np.ndarray | None:
        """LSA cosine similarity between *vec* and every document (None if unavailable)."""
        e = self.embed(vec)
        if e is None or self.embeddings is None:
            return None
        return np.clip(self.embeddings @ e, 0.0, 1.0)

    def pair_cosine(self, i: int, j: int) -> float:
        a, b = self.vectors[i], self.vectors[j]
        if len(a) > len(b):
            a, b = b, a
        return min(1.0, sum(w * b.get(t, 0.0) for t, w in a.items()))

    def pair_lsa(self, i: int, j: int) -> float | None:
        if self.embeddings is None:
            return None
        return float(max(0.0, min(1.0, self.embeddings[i] @ self.embeddings[j])))
