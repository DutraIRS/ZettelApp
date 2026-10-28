"""The notes a new vault starts with."""

import pytest

from zettelapp import i18n
from zettelapp.core.starter import HUB, TITLES, create_starter_notes
from zettelapp.core.textutil import find_wikilinks


@pytest.fixture
def starter(vault):
    return create_starter_notes(vault)


def test_the_hub_links_every_note_in_reading_order(vault, starter):
    hub = vault.get_note(starter[HUB])
    targets = [vault.resolve_title(wl.target) for wl in find_wikilinks(hub.body)]
    assert targets == [starter[key] for key in TITLES if key != HUB]
    assert {l.type for l in vault.links_from(hub.id)} == {"related"}


def test_every_link_resolves_and_every_note_is_connected(vault, starter):
    for note in vault.all_notes():
        for wl in find_wikilinks(note.body):
            assert vault.resolve_title(wl.target), (note.title, wl.target)
        assert vault.neighbors(note.id), note.title
    assert vault.count_notes() == len(TITLES)


def test_typed_links_say_how_notes_relate(vault, starter):
    typed = {(l.src, l.type, l.dst) for l in vault.all_links() if l.type != "related"}
    assert typed == {
        (starter["atomic"], "part_of", starter["zettelkasten"]),
        (starter["linking"], "part_of", starter["zettelkasten"]),
        (starter["mindmaps"], "extends", starter["atomic"]),
        (starter["suggestions"], "extends", starter["linking"]),
    }
    pairs = [frozenset((l.src, l.dst)) for l in vault.all_links()]
    assert len(pairs) == len(set(pairs))  # one link per pair keeps the graph readable


def test_tags_flashcards_and_mind_map(vault, starter):
    assert dict(vault.all_tags()) == {
        "ai": 1,
        "idea": 1,
        "memory": 1,
        "thinking": 3,
        "writing": 3,
        "zettelkasten": 4,
    }
    assert vault.manual_tags(starter["tags"]) == ["writing"]  # #idea comes from the text
    cards = vault.cards_for(starter["flashcards"])
    assert [(c.kind, c.source) for c in cards] == [("basic", "inline"), ("cloze", "inline")]
    assert cards[0].back == "One idea, in your own words."
    assert len(vault.due_cards()) == 2
    assert len(vault.get_note(starter["mindmaps"]).mindmap["children"]) == 4


def test_starter_notes_are_written_in_the_interface_language(vault, monkeypatch):
    monkeypatch.setattr(
        i18n,
        "_catalog",
        {
            "Welcome to ZettelApp": "Comece aqui",
            "One idea per note": "Uma ideia por nota",
            "What is a Zettelkasten?": "O que é um Zettelkasten?",
            "Next: {link}": "Próxima: {link}",
            "writing": "Escrita",
            "What should a single note contain?": "O que uma nota deve conter?",
            "Mind maps": "Mapas #mentais",  # a title that a [[link]] can't name
        },
    )
    ids = create_starter_notes(vault)
    hub = vault.get_note(ids[HUB])
    assert hub.title == "Comece aqui"
    assert "1. [[O que é um Zettelkasten?]]" in hub.body
    assert f"[[{ids['mindmaps']}|Mapas  mentais]]" in hub.body  # linked by id instead
    assert ids["mindmaps"] in vault.neighbors(ids[HUB])
    assert "Próxima: [[Link with a reason]]" in vault.get_note(ids["atomic"]).body
    assert "escrita" in dict(vault.all_tags())
    assert vault.cards_for(ids["flashcards"])[0].front == "O que uma nota deve conter?"
