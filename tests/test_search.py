"""Hybrid search, adaptive ranking and semantic search (with stand-ins for the language model)."""

import hashlib
import io
import json
import sys
import types
import urllib.error

import numpy as np
import pytest

from zettelapp.core import embeddings
from zettelapp.core.adaptive import FeedbackModel
from zettelapp.core.embeddings import (
    MAX_CHUNKS,
    MIN_SIMILARITY,
    MODEL_FILES,
    Embedder,
    ModelError,
    VectorIndex,
    chunk_text,
    clear_index,
    download_model,
    model_installed,
    remove_all,
    semantic_scores,
    storage_bytes,
    sync_index,
)
from zettelapp.core.search import fuzzy_scores, hybrid_search, ontology_scores, rank
from zettelapp.core.storage import Vault, split_query
from zettelapp.core.textutil import snippet_around

WEIGHTS = {"fuzzy": 0.25, "lexical": 0.45, "semantic": 0.20, "ontology": 0.10}


@pytest.fixture
def library(vault):
    vault.create_note(
        "Bayesian inference", "Posterior probability and priors.", tags=["math/probability"]
    )
    vault.create_note("Grocery list", "bread, cheese, wine", tags=["daily"])
    vault.create_note("Camus - L'Étranger", "Aujourd'hui, maman est morte.", tags=["books/french"])
    return vault


def titles(vault, results):
    return [vault.get_note(r.note_id).title for r in results]


def search(vault, query, **kwargs):
    return hybrid_search(vault, query, vault.all_notes(), WEIGHTS, **kwargs)


# --- query parsing ---------------------------------------------------------------


def test_split_query_separates_words_and_tag_filters():
    assert split_query("memory tag:Psychology recall") == ("memory recall", ["psychology"])
    assert split_query("tag:a tag:b") == ("", ["a", "b"])


# --- fuzzy -----------------------------------------------------------------------


def test_fuzzy_tolerates_typos_and_accents(library):
    notes = library.all_notes()
    assert len(fuzzy_scores("Bayesan infrence", notes)) == 1
    assert len(fuzzy_scores("etranger", notes)) == 1


def test_fuzzy_ignores_very_short_text(library):
    assert fuzzy_scores("ba", library.all_notes()) == {}


def test_fuzzy_needs_every_word(vault):
    both = vault.create_note("Quantum mechanics")
    vault.create_note("Quantum computing")
    vault.create_note("Classical mechanics")
    assert list(fuzzy_scores("quantom mechanics", vault.all_notes())) == [both.id]


def test_fuzzy_does_not_confuse_short_words(vault):
    for title in ("Math", "Path", "Cat", "At home", "Bat"):
        vault.create_note(title)
    found = {vault.get_note(i).title for i in fuzzy_scores("math", vault.all_notes())}
    assert found == {"Math"}
    found = {vault.get_note(i).title for i in fuzzy_scores("cat", vault.all_notes())}
    assert found == {"Cat"}


# --- the hybrid ranking ------------------------------------------------------------


def test_rank_merges_signals_and_puts_the_best_first():
    results = rank(
        {"fuzzy": {"a": 0.8, "b": 0.4}, "lexical": {"a": 0.9, "c": 0.7}, "semantic": {}}, WEIGHTS
    )
    assert [r.note_id for r in results] == ["a", "c", "b"]
    assert results[0].signals == {"fuzzy": 1.0, "lexical": 1.0}
    assert results == rank(
        {"fuzzy": {"a": 0.8, "b": 0.4}, "lexical": {"a": 0.9, "c": 0.7}, "semantic": {}}, WEIGHTS
    )


def test_a_search_finds_text_and_titles_with_typos(library):
    assert titles(library, search(library, "priors")) == ["Bayesian inference"]
    assert titles(library, search(library, "Bayesan")) == ["Bayesian inference"]


def test_search_works_without_the_full_text_index(library):
    library.has_fts = False
    assert titles(library, search(library, "cheese")) == ["Grocery list"]


def test_tag_filters_bind_every_signal(vault):
    tagged = vault.create_note("Algebra", tags=["math"])
    vault.create_note("Math", "not tagged")
    semantic = {n.id: 0.9 for n in vault.all_notes()}
    assert [r.note_id for r in search(vault, "tag:math", semantic=semantic)] == [tagged.id]
    assert [r.note_id for r in search(vault, "math tag:math", semantic=semantic)] == [tagged.id]


def test_only_the_notes_being_searched_are_returned(vault):
    live = vault.create_note("Cat", "feline")
    trashed = vault.create_note("Cat in the trash", "feline")
    vault.trash_note(trashed.id)
    assert [r.note_id for r in search(vault, "cat")] == [live.id]
    in_trash = [n for n in vault.all_notes(include_deleted=True) if n.deleted]
    results = hybrid_search(vault, "feline", in_trash, WEIGHTS, include_deleted=True)
    assert [r.note_id for r in results] == [trashed.id]


def test_a_weight_of_zero_turns_a_signal_off(library):
    only_fuzzy = {"fuzzy": 1.0, "lexical": 0.0, "semantic": 0.0, "ontology": 0.0}
    assert hybrid_search(library, "priors", library.all_notes(), only_fuzzy) == []


def test_all_weights_at_zero_leave_plain_full_text_search(library):
    nothing = dict.fromkeys(WEIGHTS, 0.0)
    results = hybrid_search(library, "priors", library.all_notes(), nothing)
    assert titles(library, results) == ["Bayesian inference"]


def test_semantic_scores_add_notes_with_no_word_in_common(library):
    grocery = library.search("cheese")[0]
    results = search(library, "shopping", semantic={grocery: 0.86})
    assert [r.note_id for r in results] == [grocery]
    assert set(results[0].signals) == {"semantic"}


def test_words_common_to_many_notes_do_not_hide_tagged_ones(vault):
    with vault.transaction():
        for i in range(1100):
            vault.create_note(f"Common {i}", "shared word")
        tagged = vault.create_note("Old tagged note", "shared word", tags=["rare"])
    assert vault.search("shared tag:rare") == [tagged.id]
    assert len(vault.search("shared")) == 1101


# --- the ontology -------------------------------------------------------------------


def test_searching_for_a_parent_finds_notes_filed_under_its_children(vault):
    note = vault.create_note("Priors", tags=["bayes"])
    vault.add_tag_relationship("statistics", "bayes", "parent")
    assert set(ontology_scores(vault, "statistics")) == {note.id}
    assert [r.note_id for r in search(vault, "statistics")] == [note.id]


def test_related_tags_count_only_when_asked(vault):
    note = vault.create_note("Chance", tags=["probability"])
    vault.add_tag_relationship("statistics", "probability", "related")
    assert ontology_scores(vault, "statistics") == {}
    assert set(ontology_scores(vault, "statistics", include_related=True)) == {note.id}


def test_tag_names_are_not_matched_loosely(vault):
    vault.create_note("Walk", tags=["path"])
    assert ontology_scores(vault, "math") == {}


# --- snippets ------------------------------------------------------------------------


def test_snippet_moves_to_the_search_word_only_when_it_would_be_cut_off():
    body = "lorem ipsum " * 30 + "needle here " + "dolor sit " * 30
    moved = snippet_around(body, "needle", 160)
    assert "needle" in moved and moved.startswith("…")
    assert snippet_around("needle at the start. " + body, "needle", 160).startswith("needle")
    assert snippet_around(body, "absent", 160).startswith("lorem")
    assert snippet_around(body, "", 160).startswith("lorem")


# --- adaptive ranking ------------------------------------------------------------------


def test_feedback_moves_weight_to_the_signals_of_relevant_results():
    model = FeedbackModel()
    for _unused in range(10):
        model.update({"semantic": 0.9, "lexical": 0.1}, relevant=True)
        model.update({"semantic": 0.1, "lexical": 0.9}, relevant=False)
    weights = model.adjust(WEIGHTS)
    assert weights["semantic"] / weights["lexical"] > WEIGHTS["semantic"] / WEIGHTS["lexical"]


def test_no_feedback_changes_nothing():
    assert FeedbackModel().adjust(WEIGHTS) == pytest.approx(WEIGHTS)


def test_feedback_cannot_move_a_weight_without_limit():
    model = FeedbackModel()
    for _unused in range(10_000):
        model.update({"lexical": 1.0}, relevant=True)
    assert model.adjust({"lexical": 1.0})["lexical"] <= 4.0
    assert model.adjust({"fuzzy": 1.0})["fuzzy"] >= 0.25


def test_feedback_survives_saving_and_bad_saved_data_means_nothing_learned():
    model = FeedbackModel()
    model.update({"fuzzy": 0.5, "unknown": 9.0}, relevant=False)
    assert FeedbackModel.from_json(model.to_json()) == model
    for damaged in ("", "not json", "[]", '{"relevant": 3}', '{"relevant": {"fuzzy": "x"}}'):
        assert FeedbackModel.from_json(damaged) == FeedbackModel()


def test_only_totals_are_saved(library):
    model = FeedbackModel()
    model.update(search(library, "priors")[0].signals, relevant=True)
    saved = json.loads(model.to_json())
    assert set(saved) == {"relevant", "irrelevant"}
    assert "Bayesian" not in model.to_json() and library.all_notes()[0].id not in model.to_json()


# --- semantic search: chunks and vectors ---------------------------------------------------


def unit(*values):
    vector = np.array(values, dtype=np.float32)
    return vector / np.linalg.norm(vector)


def test_chunk_text_splits_long_notes_and_stops_at_the_limit():
    assert chunk_text("hello") == ["hello"]
    assert chunk_text("   ") == []
    chunks = chunk_text("x" * 3000)
    assert len(chunks) > 1 and len(chunks[0]) == embeddings.CHUNK_CHARS
    assert len(chunk_text("x" * 5_000_000)) == MAX_CHUNKS


def test_vector_index_keeps_only_close_notes(tmp_path):
    index = VectorIndex(tmp_path, "vault")
    index.replace("close", "h1", [unit(1.0, 0.0), unit(0.0, 1.0)])
    index.replace("near", "h2", [unit(1.0, 0.1)])
    index.replace("far", "h3", [unit(0.0, 1.0)])
    assert index.hashes() == {"close": "h1", "near": "h2", "far": "h3"}
    hits = index.search(unit(1.0, 0.0))
    assert list(hits) == ["close", "near"]  # best chunk counts; "far" is below the floor
    assert hits["close"] == pytest.approx(1.0)
    assert all(score >= MIN_SIMILARITY for score in hits.values())
    index.remove(["near"])
    assert set(index.hashes()) == {"close", "far"}
    index.close()


def test_a_weak_best_match_is_no_match(tmp_path):
    index = VectorIndex(tmp_path, "vault")
    index.replace("weak", "h", [unit(1.0, 1.0)])
    assert index.search(unit(1.0, 0.0)) == {}  # cosine 0.71: unrelated texts score this much
    index.close()


def test_only_hits_close_to_the_best_one_count(tmp_path):
    index = VectorIndex(tmp_path, "vault")
    index.replace("best", "h", [unit(1.0, 0.0)])
    index.replace("second", "h", [unit(1.0, 0.5)])  # cosine 0.89, above the floor
    assert list(index.search(unit(1.0, 0.0))) == ["best"]
    index.close()


def test_each_vault_has_its_own_vectors_and_its_id_cannot_escape(tmp_path):
    # Note ids are timestamps, so two vaults can both have a note with the same id.
    first, second = VectorIndex(tmp_path, "one"), VectorIndex(tmp_path, "two")
    first.replace("20260101120000", "h1", [unit(1.0, 0.0)])
    second.replace("20260101120000", "h2", [unit(0.0, 1.0)])
    assert first.hashes() == {"20260101120000": "h1"}
    assert second.hashes() == {"20260101120000": "h2"}
    first.close()
    second.close()
    evil = VectorIndex(tmp_path / "root", "..\\..\\evil")
    evil.close()
    assert [p.parent.name for p in (tmp_path / "root").rglob("*.sqlite")] == ["index"]
    assert not list(tmp_path.glob("evil*"))


class StubEmbedder:
    """A stand-in for the language model: a text's vector comes from its hash."""

    def __init__(self):
        self.texts = []

    def embed(self, text, prefix):
        self.texts.append(prefix + text)
        digest = hashlib.sha256(text.encode()).digest()
        vector = np.array(list(digest[:8]), dtype=np.float32) + 1
        return vector / np.linalg.norm(vector)


def sync(root, vault, embedder, cancelled=lambda: False, progress=None):
    sync_index(root, vault.folder, lambda: embedder, progress or (lambda *_a: None), cancelled)


def test_indexing_covers_new_and_edited_notes_and_forgets_the_rest(vault, tmp_path):
    root = tmp_path / "search"
    first = vault.create_note("First", "one")
    second = vault.create_note("Second", "two")
    trashed = vault.create_note("Trashed", "three")
    embedder = StubEmbedder()
    seen = []
    sync(root, vault, embedder, progress=lambda done, total: seen.append((done, total)))
    assert len(embedder.texts) == 3 and all(t.startswith("passage: ") for t in embedder.texts)
    assert seen == [(1, 3), (2, 3), (3, 3)]

    embedder.texts.clear()
    sync(root, vault, embedder)
    assert embedder.texts == []  # nothing changed, nothing to do

    second.body = "two, edited"
    vault.save_note(second)
    vault.trash_note(trashed.id)
    sync(root, vault, embedder)
    assert len(embedder.texts) == 1 and "two, edited" in embedder.texts[0]
    index = VectorIndex(root, vault.vault_id)
    assert set(index.hashes()) == {first.id, second.id}
    index.close()


def test_indexing_can_stop_midway_and_continue_later(vault, tmp_path):
    root = tmp_path / "search"
    for i in range(3):
        vault.create_note(f"Note {i}", "text")
    embedder = StubEmbedder()
    sync(root, vault, embedder, cancelled=lambda: len(embedder.texts) >= 1)
    assert len(embedder.texts) == 1
    sync(root, vault, embedder)
    assert len(embedder.texts) == 3


def test_semantic_scores_read_the_vault_index(vault, tmp_path):
    root = tmp_path / "search"
    note = vault.create_note("Only note", "text")
    embedder = StubEmbedder()
    sync(root, vault, embedder)
    query = f"{note.display_title}\n\n{note.body}"  # the same text gives the same vector
    assert list(semantic_scores(root, vault.vault_id, embedder, query)) == [note.id]
    assert embedder.texts[-1] == "query: " + query
    clear_index(root, vault.vault_id)
    assert semantic_scores(root, vault.vault_id, embedder, query) == {}


def test_a_damaged_index_can_be_cleared(vault, tmp_path):
    root = tmp_path / "search"
    VectorIndex(root, "vault").close()
    (index_file,) = (root / "index").glob("*.sqlite")
    index_file.write_bytes(b"this is not a database" * 100)
    clear_index(root, "vault")
    index = VectorIndex(root, "vault")
    assert index.hashes() == {}
    index.close()


def test_indexing_does_not_load_the_model_when_nothing_changed(vault, tmp_path):
    root = tmp_path / "search"
    vault.create_note("Note", "text")
    embedder = StubEmbedder()
    sync(root, vault, embedder)

    def must_not_load():
        raise AssertionError("the model was loaded for nothing")

    sync_index(root, vault.folder, must_not_load, lambda *_a: None, lambda: False)


def test_embedder_gives_the_model_every_input_and_a_unit_vector(tmp_path, monkeypatch):
    """The real model refuses to run unless it gets all three inputs."""
    seen = {}

    class Session:
        def __init__(self, path, sess_options, providers):
            seen.update(path=path, threads=sess_options.intra_op_num_threads)

        def run(self, _outputs, feed):
            seen["feed"] = feed
            return [np.full((1, feed["input_ids"].shape[1], 4), 3.0, dtype=np.float32)]

    class Options:
        intra_op_num_threads = inter_op_num_threads = 0

    class Tokenizer:
        @classmethod
        def from_file(cls, path):
            seen["tokenizer"] = path
            return cls()

        def enable_truncation(self, length):
            seen["truncation"] = length

        def encode(self, text):
            seen["text"] = text
            return types.SimpleNamespace(ids=[5, 6, 7])

    monkeypatch.setitem(
        sys.modules,
        "onnxruntime",
        types.SimpleNamespace(SessionOptions=Options, InferenceSession=Session),
    )
    monkeypatch.setitem(sys.modules, "tokenizers", types.SimpleNamespace(Tokenizer=Tokenizer))

    vector = Embedder(tmp_path, threads=3).embed("hello", "query: ")

    assert seen["text"] == "query: hello" and seen["threads"] == 3
    assert seen["truncation"] == embeddings.MAX_TOKENS
    assert set(seen["feed"]) == {"input_ids", "attention_mask", "token_type_ids"}
    assert seen["feed"]["input_ids"].tolist() == [[5, 6, 7]]
    assert seen["feed"]["attention_mask"].tolist() == [[1, 1, 1]]
    assert seen["feed"]["token_type_ids"].tolist() == [[0, 0, 0]]
    assert np.linalg.norm(vector) == pytest.approx(1.0)


# --- semantic search: the download ------------------------------------------------------------


@pytest.fixture
def small_model(monkeypatch):
    """Two tiny files stand for the model; returns what the server hands out."""
    served = {"model.bin": b"weights" * 1000, "tok.json": b"{}"}
    monkeypatch.setattr(
        embeddings,
        "MODEL_FILES",
        {
            "model.onnx": ("model.bin", len(served["model.bin"]), _sha(served["model.bin"])),
            "tokenizer.json": ("tok.json", len(served["tok.json"]), _sha(served["tok.json"])),
        },
    )
    monkeypatch.setattr(embeddings, "MODEL_BYTES", sum(map(len, served.values())))
    requests = []

    def urlopen(request, timeout):
        requests.append(request)
        return io.BytesIO(served[request.full_url.rsplit("/", 1)[1]])

    monkeypatch.setattr(embeddings.urllib.request, "urlopen", urlopen)
    served["requests"] = requests
    return served


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _no_progress(_done, _total):
    pass


def test_download_installs_the_verified_model(tmp_path, small_model):
    assert not model_installed(tmp_path)
    seen = []
    download_model(tmp_path, lambda done, total: seen.append((done, total)), lambda: False)
    assert model_installed(tmp_path)
    assert (tmp_path / "model" / "model.onnx").read_bytes() == small_model["model.bin"]
    assert seen[-1][0] == seen[-1][1]
    assert not list(tmp_path.rglob("*.part"))
    assert all(r.full_url.startswith("https://") for r in small_model["requests"])


def test_download_refuses_a_damaged_file(tmp_path, small_model):
    small_model["model.bin"] = b"X" * len(small_model["model.bin"])
    with pytest.raises(ModelError, match="damaged"):
        download_model(tmp_path, _no_progress, lambda: False)
    assert not model_installed(tmp_path)
    assert not list(tmp_path.rglob("*.part")) and not list(tmp_path.rglob("model.onnx"))


def test_download_does_not_store_more_than_the_expected_size(tmp_path, small_model):
    expected = len(small_model["model.bin"])
    small_model["model.bin"] = small_model["model.bin"] * 100
    with pytest.raises(ModelError):
        download_model(tmp_path, _no_progress, lambda: False)
    assert not list(tmp_path.rglob("model.onnx")) and expected


def test_download_can_be_cancelled_and_resumed(tmp_path, small_model):
    with pytest.raises(ModelError, match="cancelled"):
        download_model(tmp_path, _no_progress, lambda: True)
    assert not model_installed(tmp_path) and not list(tmp_path.rglob("*.part"))
    download_model(tmp_path, _no_progress, lambda: False)
    assert model_installed(tmp_path)
    small_model["requests"].clear()
    download_model(tmp_path, _no_progress, lambda: False)
    assert small_model["requests"] == []  # what is already there is not fetched again


def test_a_network_failure_leaves_nothing_behind(tmp_path, small_model, monkeypatch):
    def fail(request, timeout):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(embeddings.urllib.request, "urlopen", fail)
    with pytest.raises(ModelError, match="offline"):
        download_model(tmp_path, _no_progress, lambda: False)
    assert not model_installed(tmp_path) and not list(tmp_path.rglob("*.part"))


def test_the_model_is_pinned_to_exact_files():
    assert "/resolve/614241f" in embeddings._MODEL_URL
    for _remote, size, digest in MODEL_FILES.values():
        assert size > 0 and len(digest) == 64


def test_removing_the_data_deletes_model_and_vectors(tmp_path, small_model):
    root = tmp_path / "search"
    download_model(root, _no_progress, lambda: False)
    VectorIndex(root, "vault").close()
    assert storage_bytes(root) > 0
    remove_all(root)
    assert not root.exists() and storage_bytes(root) == 0
    assert not model_installed(root)


def test_opening_a_vault_read_only_for_indexing_leaves_it_writable(vault, tmp_path):
    vault.create_note("Note", "text")
    sync(tmp_path / "search", vault, StubEmbedder())
    assert vault.create_note("Another", "text") and Vault.is_vault(vault.folder)
