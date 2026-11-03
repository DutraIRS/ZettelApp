import pytest

from tests.conftest import tiny_png
from zettelapp.core.models import (
    ARROW_TIPS,
    DEFAULT_LINK_TYPES,
    LINE_STYLES,
    MAX_MINDMAP_DEPTH,
    LinkType,
    new_mindmap_node,
)
from zettelapp.core.security import UnsafeInputError
from zettelapp.core.storage import SCHEMA_VERSION, Vault, VaultError


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


def test_tag_ontology_supports_multiple_parents_and_expands_search(vault):
    note = vault.create_note("Bayesian", tags=["bayesian-inference"])
    vault.add_tag_relationship("mathematics", "bayesian-inference", "parent")
    vault.add_tag_relationship("statistics", "bayesian-inference", "parent")

    assert vault.tag_graph().descendants("mathematics") == {"bayesian-inference"}
    assert vault.search("tag:mathematics") == vault.search("tag:statistics") == [note.id]


def test_tag_ontology_synonyms_and_opt_in_related_search(vault):
    synonym_note = vault.create_note("Bayesian", tags=["bayes"])
    related_note = vault.create_note("Probability", tags=["probability"])
    vault.add_tag_relationship("bayesian", "bayes", "synonym")
    vault.add_tag_relationship("bayesian", "probability", "related")

    assert vault.search("tag:bayesian") == [synonym_note.id]
    assert set(vault.search("tag:bayesian", include_related_tags=True)) == {
        synonym_note.id,
        related_note.id,
    }


def test_tag_ontology_rejects_hierarchical_cycles(vault):
    vault.add_tag_relationship("a", "b", "parent")
    with pytest.raises(VaultError, match="cycle"):
        vault.add_tag_relationship("b", "a", "parent")


def test_tag_ontology_reaches_nested_tags_and_chains(vault):
    nested = vault.create_note("Nested", tags=["bayes/priors"])
    chained = vault.create_note("Chained", tags=["alias-of-child"])
    vault.add_tag_relationship("bayesian", "bayes", "synonym")
    vault.add_tag_relationship("stats", "bayesian", "parent")
    vault.add_tag_relationship("bayesian", "child", "parent")
    vault.add_tag_relationship("child", "alias-of-child", "synonym")

    assert vault.notes_with_tags(["stats"]) == {nested.id, chained.id}
    assert vault.notes_with_tags(["child"]) == {chained.id}


def test_related_tags_are_one_step_away(vault):
    near = vault.create_note("Near", tags=["near"])
    vault.create_note("Far", tags=["far"])
    vault.add_tag_relationship("start", "near", "related")
    vault.add_tag_relationship("near", "far", "related")

    assert vault.notes_with_tags(["start"]) == set()
    assert vault.notes_with_tags(["start"], include_related=True) == {near.id}


def test_tag_relationships_have_no_duplicates_and_can_be_removed_either_way(vault):
    vault.add_tag_relationship("b", "a", "synonym")
    vault.add_tag_relationship("a", "b", "synonym")
    assert [(r.source, r.target) for r in vault.tag_relationships()] == [("a", "b")]
    vault.remove_tag_relationship("b", "a", "synonym")
    assert vault.tag_relationships() == []


@pytest.mark.parametrize(
    "source, target, relation",
    [("same", "same", "parent"), ("", "tag", "parent"), ("a", "b", "unknown")],
)
def test_bad_tag_relationships_are_refused(vault, source, target, relation):
    with pytest.raises(VaultError):
        vault.add_tag_relationship(source, target, relation)
    assert vault.tag_relationships() == []


def test_tag_filter_counts_what_the_filter_shows(vault):
    live = vault.create_note("Live", tags=["math/algebra"])
    gone = vault.create_note("Gone", tags=["math/algebra"])
    vault.trash_note(gone.id)
    vault.create_note("Only trash", tags=["unused"])
    vault.trash_note(vault.search("tag:unused")[0])
    vault.create_note("Other", tags=["bayes"])
    vault.add_tag_relationship("sciences", "math/algebra", "parent")
    vault.add_tag_relationship("empty-concept", "nothing-here", "parent")

    assert vault.tag_filter_counts() == [
        ("bayes", 1),
        ("math/algebra", 1),
        ("sciences", 1),
    ]
    assert vault.notes_with_tags(["sciences"]) >= {live.id}


def test_refreshing_tag_counts_needs_few_queries_however_large_the_ontology(vault):
    vault.create_note("Note", tags=["tag0"])
    with vault.transaction():
        for i in range(200):
            vault.add_tag_relationship(f"tag{i}", f"tag{i + 1}", "parent")
    queries = []
    vault.conn.set_trace_callback(queries.append)
    vault.tag_filter_counts()
    vault.conn.set_trace_callback(None)
    assert len(queries) < 10  # used to be thousands: a filter over them froze the app


def test_rebuilding_the_search_index_restores_it(vault):
    note = vault.create_note("Findable", "needle", tags=["tagged"])
    with vault.transaction():
        vault.conn.execute("DELETE FROM notes_fts")
    assert vault.search("needle") == []
    vault.rebuild_search_index()
    assert vault.search("needle") == vault.search("findable") == vault.search("tagged") == [note.id]


def test_search_finds_words_inside_chinese_japanese_and_korean_text(vault):
    chinese = vault.create_note("知识管理系统", "笔记")
    japanese = vault.create_note("メモ", "知識を整理するノート")
    korean = vault.create_note("연결된 노트를 작성", "내용")
    assert vault.search("管理") == [chinese.id]
    assert vault.search("整理") == [japanese.id]
    assert vault.search("노트") == [korean.id]
    tagged = vault.create_note("Tagged only", "text", tags=["数学"])
    assert vault.search("数学") == [tagged.id]


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


def test_link_types_keep_their_style(vault):
    lt = vault.save_link_type(
        LinkType("", "Inspired by", "Inspired", "#123456", line_style="long_dash", arrow="bar")
    )
    saved = vault.link_type_map()["inspired_by"]
    assert (saved.line_style, saved.arrow, saved.tip) == ("long_dash", "bar", "bar")
    lt.line_style, lt.arrow, lt.directed = "wavy", "star", False  # unknown values aren't stored
    vault.save_link_type(lt)
    saved = vault.link_type_map()["inspired_by"]
    assert (saved.line_style, saved.arrow, saved.tip) == ("solid", "triangle", None)


def test_built_in_link_types_differ_and_can_be_restyled_but_not_removed(vault):
    types = vault.link_types()
    assert [t.id for t in types] == [t.id for t in DEFAULT_LINK_TYPES]
    assert len({t.line_style for t in types}) >= 5  # dashes are a second cue besides colour
    assert all(t.line_style in LINE_STYLES and t.arrow in ARROW_TIPS for t in types)
    supports = vault.link_type_map()["supports"]
    supports.label, supports.line_style, supports.arrow = "Backs", "dotted", "diamond"
    vault.save_link_type(supports)
    restyled = vault.link_type_map()["supports"]
    assert (restyled.label, restyled.line_style, restyled.arrow) == ("Backs", "dotted", "diamond")
    assert restyled.builtin
    for type_id in ("related", "supports", "cites"):
        with pytest.raises(VaultError):
            vault.delete_link_type(type_id)
    assert len(vault.link_types()) == len(DEFAULT_LINK_TYPES)


def _rewind_to_schema_2(folder):
    import sqlite3

    conn = sqlite3.connect(folder / Vault.DB_NAME)
    conn.execute("ALTER TABLE link_types DROP COLUMN line_style")
    conn.execute("ALTER TABLE link_types DROP COLUMN arrow")
    conn.execute("UPDATE meta SET value = '2' WHERE key = 'schema_version'")
    conn.commit()
    conn.close()


def test_upgrade_from_schema_2_keeps_how_links_looked(tmp_path):
    folder = tmp_path / "old"
    v = Vault.open(folder)
    v.save_link_type(LinkType("", "Inspired by", "Inspired", "#123456"))
    v.close()
    _rewind_to_schema_2(folder)
    v = Vault.open(folder)
    try:
        assert v.get_meta("schema_version") == "5"
        looks = {t.id: (t.line_style, t.arrow) for t in v.link_types()}
        # Schema 2 took the dash from the type's place in the list and drew open arrows.
        assert looks == {
            "related": ("solid", "open"),
            "supports": ("dashed", "open"),
            "contradicts": ("dotted", "open"),
            "extends": ("dash_dot", "open"),
            "example": ("dash_dot_dot", "open"),
            "part_of": ("solid", "open"),
            "cites": ("dashed", "open"),
            "inspired_by": ("dotted", "open"),
        }
    finally:
        v.close()


def test_failed_upgrade_leaves_the_vault_at_schema_2(tmp_path, monkeypatch):
    import sqlite3

    folder = tmp_path / "old"
    Vault.open(folder).close()
    _rewind_to_schema_2(folder)

    def fail(self, key, value):
        raise sqlite3.OperationalError("disk full")

    connections = []
    connect = sqlite3.connect

    class TrackedConnection(sqlite3.Connection):
        was_closed = False

        def close(self):
            self.was_closed = True
            super().close()

    def tracked_connect(*args, **kwargs):
        connection = connect(*args, factory=TrackedConnection, **kwargs)
        connections.append(connection)
        return connection

    monkeypatch.setattr(sqlite3, "connect", tracked_connect)
    monkeypatch.setattr(Vault, "_set_meta", fail)
    with pytest.raises(sqlite3.OperationalError):
        Vault.open(folder)
    assert connections[-1].was_closed
    monkeypatch.undo()
    conn = sqlite3.connect(folder / Vault.DB_NAME)
    columns = {r[1] for r in conn.execute("PRAGMA table_info(link_types)")}
    version = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0]
    conn.close()
    assert version == "2" and not {"line_style", "arrow"} & columns  # all or nothing
    v = Vault.open(folder)  # the next start upgrades it
    assert v.link_type_map()["supports"].line_style == "dashed"
    v.close()


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
        assert v.get_meta("schema_version") == str(SCHEMA_VERSION)
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
