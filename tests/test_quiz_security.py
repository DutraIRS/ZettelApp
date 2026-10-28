from datetime import date

import pytest

from zettelapp.core.models import ReviewState, sanitize_mindmap
from zettelapp.core.quiz import build_quiz, grade_typed, schedule
from zettelapp.core.security import (
    UnsafeInputError,
    normalize_web_url,
    parse_app_url,
    safe_filename,
    safe_member_path,
    sniff_image_type,
)
from zettelapp.core.textutil import extract_inline_cards, find_wikilinks


def test_sm2_progression():
    s = ReviewState(1)
    today = date(2026, 1, 1)
    s = schedule(s, "good", today)
    assert (s.interval, s.reps, s.due) == (1, 1, "2026-01-02")
    s = schedule(s, "good", today)
    assert s.interval == 6
    s = schedule(s, "easy", today)
    assert s.interval > 15
    s = schedule(s, "again", today)
    assert (s.interval, s.reps, s.lapses) == (1, 0, 1)
    assert s.ease >= 1.3


def test_typed_grading():
    assert grade_typed("Hermann Ebbinghaus", "Hermann Ebbinghaus")[1] == "correct"
    assert grade_typed("hermann ebinghaus", "Hermann Ebbinghaus")[1] == "correct"
    assert grade_typed("Ebbing", "Hermann Ebbinghaus")[1] == "wrong"
    assert grade_typed("", "x")[1] == "wrong"


def test_quiz_modes(vault, sample):
    notes = {n.id: n for n in vault.all_notes()}
    cards = vault.cards_for_notes()
    assert len(build_quiz("flashcards", notes, cards, seed=1)) == 2
    choice = build_quiz("choice", notes, cards, seed=1)
    assert all(0 <= q.correct < len(q.choices) for q in choice)
    typed = build_quiz("typed", notes, cards, seed=1)
    assert any(q.answer == "Retrieval practice" for q in typed)
    named = build_quiz("notes", notes, cards, seed=1)
    assert named and all(q.choices[q.correct] == q.note_title for q in named)
    assert all(
        "▁▁▁" in q.prompt or q.note_title.split()[0].lower() not in q.prompt.lower() for q in named
    )


def test_wikilink_and_card_parsing():
    links = find_wikilinks("a [[One]] supports:: [[Two|2]] [[Three#Section]] `[[code]]`")
    assert [(l.target, l.link_type, l.alias) for l in links][:3] == [
        ("One", None, None),
        ("Two", "supports", "2"),
        ("Three", None, None),
    ]
    cards = extract_inline_cards(
        "Q: Multi\nline?\nA: Yes\nand more\n\n```\nQ: not a card\nA: no\n```"
    )
    assert [(c.front, c.back) for c in cards] == [("Multi\nline?", "Yes\nand more")]


@pytest.mark.parametrize(
    "url,expected",
    [
        ("example.com", "https://example.com"),
        ("https://example.com/a?b=c", "https://example.com/a?b=c"),
        ("me@example.com", "mailto:me@example.com"),
        ("javascript:alert(1)", None),
        ("file:///C:/Windows", None),
        ("http://", None),
        ("ms-settings:display", None),
    ],
)
def test_url_normalization(url, expected):
    assert normalize_web_url(url) == expected


def test_protocol_urls():
    assert parse_app_url("zettelapp://note/20261027120000") == "20261027120000"
    assert parse_app_url("zettelapp://note/../../etc") is None
    assert parse_app_url("zettelapp://run/calc") is None
    assert parse_app_url("https://note/20261027120000") is None


def test_filenames_and_paths():
    assert safe_filename("CON") == "untitled"
    assert safe_filename('a<b>:"c"/d\\e|f?*') == "a-b---c--d-e-f--"
    assert safe_filename("  trailing. ") == "trailing"
    for bad in ("../x", "/abs", "C:/x", "a/../../b"):
        with pytest.raises(UnsafeInputError):
            safe_member_path(bad)
    assert str(safe_member_path("assets/x.png")) == "assets/x.png"


def test_image_sniffing():
    assert sniff_image_type(b"\x89PNG\r\n\x1a\n....") == "png"
    assert sniff_image_type(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "webp"
    assert sniff_image_type(b"<svg></svg>") is None
    assert sniff_image_type(b"MZ\x90\x00") is None


def test_mindmap_sanitizing():
    deep = {"text": "x", "children": []}
    node = deep
    for _ in range(100):
        child = {"text": "y", "children": []}
        node["children"].append(child)
        node = child
    clean = sanitize_mindmap(deep)
    depth, node = 0, clean
    while node["children"]:
        node = node["children"][0]
        depth += 1
    assert depth == 40
    assert sanitize_mindmap("not a dict") is None
    assert "note" not in sanitize_mindmap({"text": "a", "note": "../evil"})
