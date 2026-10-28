import numpy as np

from zettelapp.core.suggest import FEATURES, LinkSuggester, NaiveBayesLinkModel, NoteData


def note_data(n):
    return NoteData(n.id, n.title, n.body, frozenset(n.tags))


def build(vault):
    s = LinkSuggester()
    s.rebuild(
        [note_data(n) for n in vault.all_notes()],
        [(l.src, l.dst) for l in vault.all_links()],
        vault.feedback(),
    )
    return s


def test_prior_model_prefers_similar_pairs():
    model = NaiveBayesLinkModel()
    high = np.full((1, len(FEATURES)), 0.9)
    low = np.full((1, len(FEATURES)), 0.02)
    assert model.predict_proba(high)[0] > 0.9 > model.predict_proba(low)[0]


def test_model_learns_from_data():
    rng = np.random.default_rng(0)
    pos = rng.uniform(0.5, 1.0, (200, len(FEATURES)))
    neg = rng.uniform(0.0, 0.4, (600, len(FEATURES)))
    model = NaiveBayesLinkModel().fit(np.vstack([pos, neg]), np.array([1] * 200 + [0] * 600))
    assert model.predict_proba(pos[:20]).min() > 0.9
    assert model.predict_proba(neg[:20]).max() < 0.1
    assert all(v > 0 for v in model.importance().values())


def test_missing_and_disabled_features_are_neutral():
    model = NaiveBayesLinkModel(enabled=["tfidf"])
    x = np.full((1, len(FEATURES)), np.nan)
    assert model.log_ratios(x).sum() == 0.0
    x[0, 0] = 0.95  # "semantic" is disabled
    assert model.log_ratios(x).sum() == 0.0


def test_suggestions_rank_related_notes_first(vault, sample):
    s = build(vault)
    new = vault.create_note(
        "Memory retention",
        "How retention of memory decays and how review and spaced repetition help.",
        tags=["memory"],
    )
    results = s.suggest(note_data(new), limit=4, min_probability=0.0)
    ids = [r.note_id for r in results]
    assert sample["d"].id not in ids[:2]  # the bread recipe is not a good link
    assert ids[0] in {sample["a"].id, sample["b"].id}
    top = results[0]
    assert 0.0 <= top.probability <= 1.0
    assert top.contributions and set(top.features) == {f.key for f in FEATURES}


def test_rejections_are_respected(vault, sample):
    vault.record_feedback(sample["b"].id, sample["e"].id, 0)
    s = build(vault)
    results = s.suggest(note_data(sample["e"]), limit=10, min_probability=0.0)
    assert sample["b"].id not in {r.note_id for r in results}
    assert sample["a"].id not in {r.note_id for r in results}  # already linked


def test_empty_note_has_no_suggestions(vault, sample):
    s = build(vault)
    assert s.suggest(NoteData("x", "", ""), min_probability=0.0) == []


def test_inline_links_do_not_leak_into_features():
    from zettelapp.core.suggest import _prepare

    p = _prepare(NoteData("1", "A note", "See [[Forgetting curve]] and supports:: [[Other idea]]"))
    assert "forgetting" not in p.words and "forgetting" not in p.tokens
    assert "supports" not in p.tokens
