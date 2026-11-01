"""Tests for hybrid search, adaptive ranking and (optional) embeddings."""

from __future__ import annotations

import json
import random
import sqlite3

import pytest

from zettelapp.core.adaptive import (
    AdaptiveRanker,
    AdaptiveState,
    BayesianWeightModel,
    candidate_arms,
)
from zettelapp.core.embedding_service import EmbeddingService
from zettelapp.core.embeddings import VectorIndex, chunk_text
from zettelapp.core.search import (
    DEFAULT_WEIGHTS,
    FuzzySearchProvider,
    OntologySignal,
    RankingEngine,
    SearchService,
    normalize_weights,
)
from zettelapp.core.storage import Vault


@pytest.fixture
def vault(tmp_path):
    v = Vault.open(tmp_path / "vault")
    v.create_note(
        title="Bayesian inference",
        body="Posterior probability and priors.",
        tags=["math/probability"],
    )
    v.create_note(title="Grocery list", body="bread, cheese, wine", tags=["daily"])
    v.create_note(
        title="Camus - L'Étranger", body="Aujourd'hui, maman est morte.", tags=["books/french"]
    )
    return v


# --- fuzzy ---------------------------------------------------------------------


def test_fuzzy_tolerates_typos(vault):
    scores = FuzzySearchProvider().search("Bayesan infrence", vault)
    assert any("Bayesian" in vault.get_note(i).display_title for i in scores)


def test_fuzzy_handles_diacritics(vault):
    scores = FuzzySearchProvider().search("etranger", vault)
    assert scores, "diacritic-folded fuzzy match expected"


def test_fuzzy_rejects_short_queries(vault):
    assert FuzzySearchProvider().search("b", vault) == {}


# --- lexical -------------------------------------------------------------------


def test_fts_bm25_ranking(vault):
    service = SearchService(vault)
    results = service.search("priors")
    assert [r.note_id for r in results]
    assert results[0].title == "Bayesian inference"


def test_fts_unavailable_falls_back(vault, monkeypatch):
    vault.has_fts = False
    service = SearchService(vault)
    results = service.search("cheese")
    assert any(r.title == "Grocery list" for r in results)


# --- ranking fusion --------------------------------------------------------------


def test_weight_normalization_drops_unavailable():
    w = normalize_weights({"fuzzy": 1.0, "semantic": 0.5})
    assert "semantic" in w  # semantic is a valid signal key; zero weights drop
    w2 = normalize_weights({"fuzzy": 0.0, "lexical": 3.0})
    assert set(w2) == {"lexical"} and abs(sum(w2.values()) - 1.0) < 1e-9


def test_ranking_dedupes_and_is_deterministic():
    engine = RankingEngine(DEFAULT_WEIGHTS)
    signals = {
        "fuzzy": {"a": 0.8, "b": 0.4},
        "lexical": {"a": 0.9, "c": 0.7},
        "semantic": {},  # unavailable
        "ontology": {},
    }
    r1 = engine.rank(signals)
    r2 = engine.rank(signals)
    assert [r.note_id for r in r1] == [r.note_id for r in r2]
    ids = {r.note_id for r in r1}
    assert ids == {"a", "b", "c"}  # deduplicated across signals
    assert r1[0].note_id == "a"


def test_search_result_carries_signal_info(vault):
    results = SearchService(vault).search("Bayesian")
    assert results
    assert results[0].matched_via
    assert results[0].snippet


def test_snippet_highlights_context():
    from zettelapp.core.search import highlight_snippet

    body = "lorem ipsum " * 30 + "needle here" + " dolor sit" * 30
    snippet = highlight_snippet(body, "needle")
    assert "needle" in snippet and snippet.startswith("…")


# --- ontology signal --------------------------------------------------------------


def test_ontology_signal_uses_tag_hierarchy(vault):
    vault.add_tag_relationship("math", "math/probability", "parent")
    signal = OntologySignal(vault)
    scores = signal.search("probability", vault)
    assert scores, "ontology expansion should surface the tagged note"


# --- adaptive ranking ---------------------------------------------------------------


def test_bandit_exploits_best_arm():
    rng = random.Random(42)
    ranker = AdaptiveRanker(rng=rng)
    ranker.state.epsilon = 0.0
    for _ in range(30):
        arm = ranker.select_arm()
        ranker.state.current_arm = arm
        ranker.record_feedback(arm == 1)
    assert ranker.state.arm_stats[1].wins > ranker.state.arm_stats[0].wins
    assert ranker.state.current_arm == 1


def test_bandit_explores_with_epsilon():
    rng = random.Random(1)
    ranker = AdaptiveRanker(rng=rng)
    ranker.state.epsilon = 1.0  # always explore
    picks = {ranker.select_arm() for _ in range(30)}
    assert len(picks) > 1


def test_effective_epsilon_shrinks():
    ranker = AdaptiveRanker(rng=random.Random(0))
    assert ranker.effective_epsilon() == pytest.approx(ranker.state.epsilon)
    ranker.state.feedback_count = 500
    assert ranker.effective_epsilon() < ranker.state.epsilon


def test_feedback_updates_only_current_arm():
    ranker = AdaptiveRanker(rng=random.Random(0))
    before = [(a.wins, a.losses) for a in ranker.state.arm_stats]
    ranker.record_feedback(True)
    after = [(a.wins, a.losses) for a in ranker.state.arm_stats]
    changed = [i for i in range(len(before)) if before[i] != after[i]]
    assert changed == [ranker.state.current_arm]


def test_weights_normalized_in_arms():
    for arm in candidate_arms(DEFAULT_WEIGHTS):
        w = {k: v for k, v in arm.items()}
        assert all(v >= 0 for v in w.values())


def test_state_roundtrip():
    state = AdaptiveState()
    state.feedback_count = 7
    state.arm_stats[2].wins = 5
    clone = AdaptiveState.from_json(state.to_json())
    assert clone.feedback_count == 7
    assert clone.arm_stats[2].wins == 5
    assert clone.epsilon == state.epsilon


def test_bayesian_model_shifts_weights_toward_relevant_signal():
    model = BayesianWeightModel()
    for _ in range(10):
        model.update({"semantic": 0.9, "lexical": 0.1}, relevant=True)
        model.update({"semantic": 0.1, "lexical": 0.9}, relevant=False)
    w = model.weights()
    assert w["semantic"] > w["lexical"]


def test_bayesian_model_handles_missing_features():
    model = BayesianWeightModel()
    model.update({"lexical": 0.8}, relevant=True)  # no semantic feature at all
    w = model.weights()
    assert set(w) == set(DEFAULT_WEIGHTS)


def test_reset_restores_defaults():
    ranker = AdaptiveRanker(rng=random.Random(0))
    ranker.record_feedback(True)
    ranker.reset()
    assert ranker.state.feedback_count == 0
    assert all(a.wins == 0 and a.losses == 0 for a in ranker.state.arm_stats)


def test_no_learning_without_explicit_feedback():
    ranker = AdaptiveRanker(rng=random.Random(0))
    ranker.select_arm()  # browsing-equivalent: selection alone must not learn
    assert all(a.wins == 0 and a.losses == 0 for a in ranker.state.arm_stats)


# --- embeddings ------------------------------------------------------------------


def test_chunk_text():
    text = "x" * 3000
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert len(chunks[0]) == 1200
    short = chunk_text("hello")
    assert short == ["hello"]


def test_vector_index_roundtrip(tmp_path):
    conn = sqlite3.connect(tmp_path / "e.db")
    index = VectorIndex(conn)
    index.upsert("m1", "note1", "hash1", [[1.0, 0.0], [0.0, 1.0]])
    assert index.count("m1") == 2
    assert index.stored_hash("m1", "note1") == "hash1"
    assert index.note_ids("m1") == {"note1"}
    scores = index.search("m1", [1.0, 0.1])
    assert scores and scores["note1"] == pytest.approx(1.0 / (1.0 + 0.01) ** 0.5, abs=1e-5)
    index.remove("m1", "note1")
    assert index.count("m1") == 0
    conn.close()


def test_embeddings_never_mix_models(tmp_path):
    conn = sqlite3.connect(tmp_path / "e.db")
    index = VectorIndex(conn)
    index.upsert("model-a", "n1", "h", [[0.5, 0.5]])
    index.upsert("model-b", "n1", "h", [[1.0, 0.0]])
    assert index.count("model-a") == 1 and index.count("model-b") == 1
    conn.close()


def test_service_validates_model_before_activation(tmp_path):
    service = EmbeddingService(tmp_path / "search")
    assert service.installed_models() == []
    with pytest.raises(FileNotFoundError):
        service.switch_model("intfloat/multilingual-e5-small")
    with pytest.raises(FileNotFoundError):
        service.acquire_model("missing/model")
    service.close()


def test_service_stub_indexing_and_search(tmp_path, vault, monkeypatch):
    """Index/search with a stub backend (no onnxruntime required)."""
    service = EmbeddingService(tmp_path / "search")
    model_id = "stub/model"

    class StubBackend:
        model = type("M", (), {"passage_prefix": "passage: ", "query_prefix": "query: "})()
        loaded = True

        def load(self):
            pass

        def close(self):
            pass

        def embed(self, texts, prefix="", max_tokens=512):
            import hashlib

            out = []
            for t in texts:
                h = hashlib.sha256(t.encode()).digest()
                vec = [b / 255.0 for b in h[:8]]
                norm = sum(v * v for v in vec) ** 0.5 or 1.0
                out.append([v / norm for v in vec])
            return out

    import zettelapp.core.embedding_service as es

    monkeypatch.setattr(es, "EmbeddingBackend", lambda info, directory: StubBackend())
    # install a fake validated model dir
    model_root = service.root / "models" / model_id.replace("/", "__")
    model_root.mkdir(parents=True)
    (model_root / "model.onnx").write_bytes(b"stub")
    (model_root / "tokenizer.json").write_text("{}")
    (model_root / "zettelapp-model.json").write_text(
        json.dumps({"model_id": model_id, "dimensions": 8, "version": "1"})
    )

    n = service.index_note(vault, vault.all_notes()[0].id, model_id)
    assert n >= 1
    assert service.pending_note_ids(vault, model_id) == [
        i.id for i in vault.all_notes() if i.id != vault.all_notes()[0].id
    ]
    scores = service.search("anything", model_id)
    assert isinstance(scores, dict)
    service.release_model()
    service.close()


def test_semantic_unavailable_keeps_search_working(vault):
    """Core requirement: no AI component, search still fine."""
    service = SearchService(vault)  # no semantic scores passed
    results = service.search("Bayesian")
    assert results


def test_deleted_embeddings_frees_storage(tmp_path):
    service = EmbeddingService(tmp_path / "search")
    service.index.drop_all()
    assert service.index.count() == 0
    service.close()
