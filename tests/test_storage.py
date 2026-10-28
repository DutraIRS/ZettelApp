import pytest

from tests.conftest import tiny_png
from zettelapp.core.models import MAX_MINDMAP_DEPTH, LinkType, new_mindmap_node
from zettelapp.core.security import UnsafeInputError
from zettelapp.core.storage import Vault


def test_create_and_reload(tmp_path):
    v = Vault.open(tmp_path / "v")
    n = v.create_note("Hello", "World", tags=["Greeting", " greeting ", "#Misc"], url="example.com")
    v.close()
    v = Vault.open(tmp_path / "v")
    loaded = v.get_note(n.id)
    assert loaded.title == "Hello"
    assert loaded.tags == ["greeting", "misc"]
    assert loaded.url == "https://example.com"
    assert len(n.id) == 14 and n.id.isdigit()
    v.close()


def test_ids_are_unique_timestamps(vault):
    ids = {vault.create_note(str(i)).id for i in range(5)}
    assert len(ids) == 5
    assert all(len(i) == 14 for i in ids)


def test_unsafe_url_is_dropped(vault):
    n = vault.create_note("x", url="javascript:alert(1)")
    assert vault.get_note(n.id).url == ""


def test_inline_typed_links_and_cards(vault):
    target = vault.create_note("Target note")
    other = vault.create_note("Other")
    n = vault.create_note(
        "Source",
        f"See [[Target note]] and supports:: [[{other.id}|alias]].\n\n"
        "Q: What?\nA: That.\n\n{{c1::Cloze}} text",
    )
    links = {(l.dst, l.type, l.origin) for l in vault.links_from(n.id)}
    assert links == {(target.id, "related", "inline"), (other.id, "supports", "inline")}
    cards = vault.cards_for(n.id)
    assert {(c.kind, c.front) for c in cards} == {
        ("basic", "What?"),
        ("cloze", "{{c1::Cloze}} text"),
    }
    n.body = "No more links"
    vault.save_note(n)
    assert vault.links_from(n.id) == []
    assert vault.cards_for(n.id) == []


def test_manual_link_survives_inline_removal(vault):
    a, b = vault.create_note("A"), vault.create_note("B")
    vault.add_link(a.id, b.id)
    a.body = "[[B]]"
    vault.save_note(a)
    a.body = ""
    vault.save_note(a)
    assert [(l.dst, l.origin) for l in vault.links_from(a.id)] == [(b.id, "manual")]


def test_search_with_fts_and_tags(sample, vault):
    assert sample["b"].id in vault.search("forget")
    assert vault.search("tag:cooking") == [sample["d"].id]
    assert sample["d"].id not in vault.search("memory tag:learning")
    assert vault.search('"); DROP TABLE notes; --') == []
    assert vault.count_notes() == 5


def test_trash_restore_and_purge(sample, vault):
    vault.trash_note(sample["a"].id)
    assert sample["a"].id not in {n.id for n in vault.all_notes()}
    assert vault.links_to(sample["a"].id) == []
    vault.restore_note(sample["a"].id)
    assert len(vault.links_to(sample["a"].id)) == 2
    vault.trash_note(sample["d"].id)
    assert vault.empty_trash() == 1
    assert vault.get_note(sample["d"].id) is None


def test_link_types(vault):
    a, b = vault.create_note("A"), vault.create_note("B")
    lt = vault.save_link_type(LinkType("", "Inspired by", "Inspired", "#123456"))
    assert lt.id == "inspired_by"
    vault.add_link(a.id, b.id, "inspired_by")
    vault.add_link(a.id, b.id, "nonexistent")  # falls back to "related"
    assert {l.type for l in vault.links_from(a.id)} == {"inspired_by", "related"}
    vault.delete_link_type("inspired_by")
    assert {l.type for l in vault.links_from(a.id)} == {"related"}


def test_reverse_directed_link(vault):
    a, b = vault.create_note("A"), vault.create_note("B")
    vault.add_link(a.id, b.id, "supports")
    vault.reverse_link(a.id, b.id, "supports")
    assert [(l.src, l.dst, l.type) for l in vault.all_links()] == [(b.id, a.id, "supports")]
    types = vault.link_type_map()
    assert types["supports"].directed and not types["related"].directed
    assert types["supports"].label_for(outgoing=False) == "Supported by"


def test_images_are_validated(vault):
    name = vault.add_image(tiny_png(), "pic.png")
    assert vault.asset_path(name).is_file()
    assert vault.add_image(tiny_png(), "again.png") == name  # content-addressed
    with pytest.raises(UnsafeInputError):
        vault.add_image(b"<svg onload='alert(1)'/>", "evil.svg")
    assert vault.asset_path("../zettel.db") is None


def test_saving_an_overdeep_mindmap_preserves_the_previous_tree(vault):
    note = vault.create_note("Map")
    note.mindmap = new_mindmap_node("Saved root")
    vault.save_note(note)

    root = new_mindmap_node("Too deep")
    current = root
    for depth in range(MAX_MINDMAP_DEPTH + 1):
        child = new_mindmap_node(str(depth))
        current["children"].append(child)
        current = child
    note.mindmap = root

    with pytest.raises(UnsafeInputError, match="deeper"):
        vault.save_note(note)

    assert vault.get_note(note.id).mindmap["text"] == "Saved root"


def test_backup(vault, tmp_path, sample):
    dest = tmp_path / "backups"
    for _ in range(3):
        vault.backup(dest, keep=2)
    copies = list(dest.glob("zettel-*.db"))
    assert 1 <= len(copies) <= 2
    restored = Vault.open(tmp_path / "check", create=True)
    restored.close()


def test_hashtags_in_the_text_become_tags(vault):
    note = vault.create_note("Tags", "About #learning and #Memory/long-term.", tags=["manual"])
    assert note.tags == ["learning", "manual", "memory/long-term"]
    assert vault.manual_tags(note.id) == ["manual"]
    assert vault.search("tag:learning") == [note.id]
    # Deleting the #tag from the text removes it, even when a caller passes every tag back.
    loaded = vault.get_note(note.id)
    loaded.body = "Only #learning now."
    vault.save_note(loaded)
    assert vault.get_note(note.id).tags == ["learning", "manual"]
    assert vault.manual_tags(note.id) == ["manual"]


def test_hashtags_ignore_code_links_and_headings():
    from zettelapp.core.textutil import extract_hashtags

    text = (
        "# Heading\n#real tag, `#code`, [[Note#Section]], [[#Heading]], [x](#anchor), "
        "https://example.com/#frag, &#123; and\n```\n#fenced\n```\n#trailing- #a/b/ #1st"
    )
    assert extract_hashtags(text) == ["a/b", "real", "trailing"]


def test_upgrade_from_schema_1_derives_tags_from_text(tmp_path):
    import sqlite3

    folder = tmp_path / "old"
    v = Vault.open(folder)
    note = v.create_note("Old", "An old note about #history.", tags=["kept"])
    v.close()
    conn = sqlite3.connect(folder / Vault.DB_NAME)  # rewind to schema 1: no tags.source
    conn.execute("DELETE FROM tags WHERE source = 'inline'")
    conn.execute("ALTER TABLE tags DROP COLUMN source")
    conn.execute("UPDATE meta SET value = '1' WHERE key = 'schema_version'")
    conn.commit()
    conn.close()
    v = Vault.open(folder)
    try:
        assert v.get_meta("schema_version") == "2"
        assert v.get_note(note.id).tags == ["history", "kept"]
        assert v.manual_tags(note.id) == ["kept"]
        assert v.search("tag:history") == [note.id]
    finally:
        v.close()


def test_editor_says_which_tags_were_added_by_hand(vault):
    note = vault.create_note("Both", "Text with #idea", tags=["idea"])
    assert vault.manual_tags(note.id) == []  # given and written in the text: derived
    vault.save_note(note, manual_tags=["idea"])  # pinned in the tag box
    assert vault.manual_tags(note.id) == ["idea"]
    note.body = "No tag in the text any more"
    vault.save_note(note, manual_tags=["idea"])
    assert vault.get_note(note.id).tags == ["idea"]  # a pinned tag outlives the text
    vault.save_note(note, manual_tags=[])
    assert vault.get_note(note.id).tags == []
