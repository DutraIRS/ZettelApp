import pytest

from zettelapp.core.models import LinkType
from zettelapp.core.security import UnsafeInputError
from zettelapp.core.storage import Vault
from tests.conftest import tiny_png


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
    n = vault.create_note("Source", f"See [[Target note]] and supports:: [[{other.id}|alias]].\n\n"
                                    "Q: What?\nA: That.\n\n{{c1::Cloze}} text")
    links = {(l.dst, l.type, l.origin) for l in vault.links_from(n.id)}
    assert links == {(target.id, "related", "inline"), (other.id, "supports", "inline")}
    cards = vault.cards_for(n.id)
    assert {(c.kind, c.front) for c in cards} == {("basic", "What?"), ("cloze", "{{c1::Cloze}} text")}
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


def test_backup(vault, tmp_path, sample):
    dest = tmp_path / "backups"
    for _ in range(3):
        vault.backup(dest, keep=2)
    copies = list(dest.glob("zettel-*.db"))
    assert 1 <= len(copies) <= 2
    restored = Vault.open(tmp_path / "check", create=True)
    restored.close()
