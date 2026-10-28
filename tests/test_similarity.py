import random

import pytest

from zettelapp.core import similarity
from zettelapp.core.similarity import (
    SemanticIndex,
    _jaro_winkler_python,
    _levenshtein_bitparallel,
    jaccard,
    jaro_winkler_similarity,
    levenshtein_distance,
    levenshtein_similarity,
)


def naive_levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


@pytest.mark.parametrize("a,b,d", [("kitten", "sitting", 3), ("", "abc", 3), ("flaw", "lawn", 2),
                                   ("same", "same", 0), ("informação", "informacao", 2)])
def test_levenshtein_known_values(a, b, d):
    assert levenshtein_distance(a, b) == d
    assert _levenshtein_bitparallel(a, b) == d


def test_bitparallel_matches_dynamic_programming():
    rng = random.Random(3)
    for _ in range(400):
        a = "".join(rng.choice("abcde ") for _ in range(rng.randint(0, 90)))
        b = "".join(rng.choice("abcde ") for _ in range(rng.randint(0, 90)))
        assert _levenshtein_bitparallel(a, b) == naive_levenshtein(a, b)


def test_similarity_bounds():
    assert levenshtein_similarity("", "x") == 0.0
    assert levenshtein_similarity("abc", "abc") == 1.0
    assert jaccard(set(), {1}) == 0.0
    assert jaccard({1, 2}, {2, 3}) == pytest.approx(1 / 3)


def test_jaro_winkler_reference_values():
    assert _jaro_winkler_python("MARTHA", "MARHTA") == pytest.approx(0.9611, abs=1e-4)
    assert _jaro_winkler_python("DIXON", "DICKSONX") == pytest.approx(0.8133, abs=1e-4)
    assert jaro_winkler_similarity("MARTHA", "MARHTA") == pytest.approx(0.9611, abs=1e-4)


def test_fallbacks_agree_with_rapidfuzz(monkeypatch):
    pairs = [("zettelkasten", "zettel"), ("note taking", "taking notes"), ("graph", "giraffe")]
    fast = [(levenshtein_distance(a, b), jaro_winkler_similarity(a, b)) for a, b in pairs]
    monkeypatch.setattr(similarity, "_RFLevenshtein", None)
    monkeypatch.setattr(similarity, "_RFJaroWinkler", None)
    slow = [(levenshtein_distance(a, b), jaro_winkler_similarity(a, b)) for a, b in pairs]
    for (d1, j1), (d2, j2) in zip(fast, slow):
        assert d1 == d2
        assert j1 == pytest.approx(j2, abs=1e-9)


def test_semantic_index_ranks_related_documents():
    docs = {
        "a": "memory retention review spaced repetition".split(),
        "b": "memory forgetting curve retention".split(),
        "c": "bread flour water salt starter".split(),
        "d": "recall testing memory retrieval".split(),
        "e": "oven bake bread crust".split(),
    }
    index = SemanticIndex(docs, lsa_dims=3)
    q = index.vectorize("memory retention".split())
    cos = index.cosine_all(q)
    assert cos[index.position["a"]] > cos[index.position["c"]]
    lsa = index.lsa_all(q)
    assert lsa is not None
    assert lsa[index.position["b"]] > lsa[index.position["e"]]
    assert 0.0 <= index.pair_cosine(0, 1) <= 1.0
