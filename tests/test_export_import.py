import json
import os
import sqlite3
import zipfile

import pytest

from tests.conftest import tiny_png
from zettelapp.core import export as ex
from zettelapp.core.graph import force_layout, subgraph
from zettelapp.core.importer import import_data, import_path
from zettelapp.core.render import NoteRenderer
from zettelapp.core.security import UnsafeInputError
from zettelapp.core.storage import Vault


def test_subgraph_depth(vault, sample):
    links = vault.all_links()
    assert subgraph([sample["c"].id], links, 1) == {sample["c"].id, sample["a"].id}
    # depth 2: c -> a -> (b via inline link, e)
    assert subgraph([sample["c"].id], links, 2) == {sample[k].id for k in "abce"}


def test_layout_is_finite(vault, sample):
    pos = force_layout(
        [n.id for n in vault.all_notes()], [(l.src, l.dst) for l in vault.all_links()]
    )
    assert len(pos) == 5
    assert all(abs(x) < 1e5 and abs(y) < 1e5 for x, y in pos.values())


@pytest.mark.parametrize("fmt", [f.key for f in ex.FORMATS])
def test_every_format_exports(vault, sample, tmp_path, fmt):
    ids = {n.id for n in vault.all_notes()}
    dest = tmp_path / f"out{ex.FORMATS_BY_KEY[fmt].extension}"
    result = ex.export(vault, fmt, ids, dest)
    assert dest.is_file() and dest.stat().st_size > 0
    assert result.notes == 5
    assert not list(tmp_path.glob("*.part"))


def test_archive_roundtrip(vault, sample, tmp_path):
    img = vault.add_image(tiny_png(), "p.png")
    a = sample["a"]
    a.body += f"\n\n![pic](asset:{img})"
    a.image = img
    a.mindmap = {"text": "Root", "children": [{"text": "Child", "children": []}]}
    vault.save_note(a)
    dest = tmp_path / "archive.zip"
    ex.export(vault, "archive", {a.id, sample["b"].id, sample["c"].id}, dest)

    other = Vault.open(tmp_path / "other")
    result = import_path(other, dest)
    assert result.notes == 3 and result.images == 1
    copy = other.get_note(a.id)
    assert copy.image == img and copy.mindmap["children"][0]["text"] == "Child"
    assert {l.type for l in other.links_to(a.id)} == {"supports"}
    assert other.links_from(a.id)[0].dst == sample["b"].id  # inline link re-created
    again = import_path(other, dest)  # identical notes are skipped, not duplicated
    assert again.skipped == 3 and other.count_notes() == 3
    other.close()


def test_the_tag_ontology_survives_an_archive_roundtrip(vault, tmp_path):
    note = vault.create_note("Priors", tags=["bayes"])
    vault.add_tag_relationship("statistics", "bayes", "parent")
    vault.add_tag_relationship("mathematics", "statistics", "parent")
    vault.add_tag_relationship("bayes", "bayesian", "synonym")
    dest = tmp_path / "archive.zip"
    ex.export(vault, "archive", {note.id}, dest)

    other = Vault.open(tmp_path / "other")
    import_path(other, dest)
    assert other.tag_relationships() == vault.tag_relationships()
    assert other.notes_with_tags(["mathematics"]) == {note.id}
    import_path(other, dest)  # importing twice changes nothing
    assert other.tag_relationships() == vault.tag_relationships()
    other.close()


def test_exporting_a_few_notes_does_not_reveal_other_tags_in_the_ontology(vault, tmp_path):
    shared = vault.create_note("Shared", tags=["public"])
    vault.create_note("Private", tags=["secret-project"])
    vault.add_tag_relationship("topics", "public", "parent")
    vault.add_tag_relationship("topics", "secret-project", "parent")
    vault.add_tag_relationship("secret-project", "secret-alias", "synonym")
    data = ex.bundle_to_dict(ex.collect(vault, {shared.id}))
    assert data["tag_relationships"] == [{"source": "topics", "target": "public", "type": "parent"}]


def test_bad_tag_relationships_in_an_export_are_skipped_with_a_warning(vault):
    result = import_data(
        vault,
        {
            "format": "zettelapp",
            "version": 1,
            "tag_relationships": [
                "junk",
                {"source": "a", "target": "b", "type": "parent"},
                {"source": "b", "target": "a", "type": "parent"},  # a cycle
                {"source": "a", "target": "c", "type": "unknown"},
                {"source": 3, "target": None, "type": "related"},
            ],
        },
    )
    assert [(r.source, r.target) for r in vault.tag_relationships()] == [("a", "b")]
    assert len(result.warnings) == 3


def test_an_export_field_for_tag_relationships_must_be_a_list(vault):
    with pytest.raises(UnsafeInputError):
        import_data(vault, {"format": "zettelapp", "version": 1, "tag_relationships": "x"})


def test_an_archive_larger_than_any_single_image_can_still_be_imported(vault, tmp_path):
    notes = [
        {"id": f"2026010112{i:04d}", "title": f"N{i}", "body": os.urandom(250_000).hex()}
        for i in range(70)
    ]
    dest = tmp_path / "large.zip"
    manifest = json.dumps({"format": "zettelapp", "version": 1, "notes": notes})
    assert len(manifest) > 32 * 1024**2
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        zf.writestr("manifest.json", manifest)
    assert import_path(vault, dest).notes == 70


def _styled_type(vault):
    from zettelapp.core.models import LinkType

    return vault.save_link_type(
        LinkType("", "Inspired by", "Inspires", "#123456", line_style="long_dash", arrow="bar")
    )


def test_link_styles_survive_an_archive_roundtrip(vault, sample, tmp_path):
    _styled_type(vault)
    types = vault.link_type_map()
    contradicts = types["contradicts"]
    supports = types["supports"]
    supports.color = "#112233"
    supports.line_style = "long_dash"
    supports.arrow = "bar"
    vault.save_link_type(supports)
    vault.add_link(sample["a"].id, sample["b"].id, "inspired_by")
    dest = tmp_path / "archive.zip"
    ex.export(vault, "archive", {n.id for n in vault.all_notes()}, dest)
    with zipfile.ZipFile(dest) as zf:
        manifest = json.loads(zf.read("manifest.json"))
    saved = {t["id"]: t for t in manifest["link_types"]}
    assert (
        saved["inspired_by"]["line_style"] == "long_dash" and saved["inspired_by"]["arrow"] == "bar"
    )

    other = Vault.open(tmp_path / "other")
    import_path(other, dest)
    copy = other.link_type_map()
    assert (copy["inspired_by"].line_style, copy["inspired_by"].arrow) == ("long_dash", "bar")
    assert (copy["supports"].color, copy["supports"].line_style, copy["supports"].arrow) == (
        "#112233",
        "long_dash",
        "bar",
    )
    assert copy["contradicts"].line_style == contradicts.line_style
    assert {l.type for l in other.links_from(sample["a"].id)} >= {"inspired_by"}
    other.close()


def test_old_exports_without_link_styles_still_import(vault):
    data = {
        "format": "zettelapp",
        "version": 1,
        "link_types": [
            {
                "id": "inspired_by",
                "label": "Inspired by",
                "inverse_label": "Inspires",
                "color": "#123456",
                "directed": True,
            },
            {
                "id": "see_also",
                "label": "See also",
                "inverse_label": "See also",
                "color": "#654321",
                "directed": False,
            },
        ],
    }
    import_data(vault, data)
    types = vault.link_type_map()
    assert types["inspired_by"].arrow == "triangle"
    # Missing line styles are filled in with the least used ones, so the types differ.
    assert types["inspired_by"].line_style != types["see_also"].line_style


@pytest.mark.parametrize(
    "field, value",
    [("line_style", "wavy"), ("line_style", 3), ("arrow", "star"), ("arrow", ["bar"])],
)
def test_unknown_link_styles_are_rejected(vault, field, value):
    lt = {"id": "odd", "label": "Odd", "inverse_label": "Odd", "color": "#123456", field: value}
    data = {"format": "zettelapp", "version": 1, "link_types": [lt], "notes": [{"title": "N"}]}
    before = vault.count_notes()
    with pytest.raises(UnsafeInputError, match="Odd|odd"):
        import_data(vault, data)
    assert "odd" not in vault.link_type_map() and vault.count_notes() == before


def test_graph_exports_carry_link_styles(vault, sample, tmp_path):
    _styled_type(vault)
    vault.add_link(sample["a"].id, sample["b"].id, "inspired_by")
    vault.add_link(sample["a"].id, sample["d"].id, "contradicts")
    ids = {n.id for n in vault.all_notes()}
    dot = ex._dot(ex.collect(vault, ids), "Test")
    assert "style=dashed, arrowhead=tee" in dot  # long dash: Graphviz only has dashed
    assert "style=dotted, dir=none" in dot  # contradicts is undirected
    assert "style=dashed, arrowhead=normal" in dot  # supports
    dest = tmp_path / "graph.graphml"
    ex.export(vault, "graphml", ids, dest)
    xml = dest.read_text(encoding="utf-8")
    assert 'attr.name="line_style"' in xml and 'attr.name="arrow"' in xml
    assert '<data key="edge_line_style">long_dash</data>' in xml
    assert '<data key="edge_arrow">bar</data>' in xml
    assert '<data key="edge_arrow">none</data>' in xml
    site = tmp_path / "site.zip"
    ex.export(vault, "html", ids, site)
    with zipfile.ZipFile(site) as zf:
        index = zf.read("index.html").decode("utf-8")
        page = zf.read(f"notes/{sample['a'].id}.html").decode("utf-8")
    assert "stroke-dasharray" in index and 'class="link"' in index
    assert '<svg class="style"' in page and "#123456" in page


def test_markdown_roundtrip(vault, sample, tmp_path):
    dest = tmp_path / "md.zip"
    ex.export(vault, "markdown", {n.id for n in vault.all_notes()}, dest)
    with zipfile.ZipFile(dest) as zf:
        text = zf.read("Active recall.md").decode("utf-8")
    assert text.startswith("---\nid: ")
    assert "supports:: [[Spaced repetition]]" in text
    other = Vault.open(tmp_path / "md-import")
    result = import_path(other, dest)
    assert result.notes == 5
    recall = other.resolve_title("Active recall")
    assert {l.type for l in other.links_from(recall)} == {"supports"}
    other.close()


def test_html_export_is_script_free(vault, sample, tmp_path):
    sample[
        "d"
    ].body = "<script>alert(1)</script> [x](javascript:alert(2)) ![img](https://evil.example/x.png)"
    vault.save_note(sample["d"])
    dest = tmp_path / "site.zip"
    ex.export(vault, "html", {n.id for n in vault.all_notes()}, dest)
    with zipfile.ZipFile(dest) as zf:
        page = zf.read(f"notes/{sample['d'].id}.html").decode("utf-8")
        index = zf.read("index.html").decode("utf-8")
    assert "<script" not in page and 'href="javascript' not in page and "evil.example" not in page
    assert "Content-Security-Policy" in page and "<svg" in index


def test_anki_package_contains_cards(vault, sample, tmp_path):
    dest = tmp_path / "deck.apkg"
    result = ex.export(vault, "anki", {n.id for n in vault.all_notes()}, dest)
    assert result.cards == 2
    with zipfile.ZipFile(dest) as zf:
        db = tmp_path / "collection.anki2"
        db.write_bytes(zf.read("collection.anki2"))
    conn = sqlite3.connect(db)
    fields = [r[0] for r in conn.execute("SELECT flds FROM notes")]
    conn.close()
    assert len(fields) == 2
    assert any("zettelapp://note/" in f for f in fields)
    assert any("{{c1::Retrieval practice}}" in f for f in fields)


def test_renderer_blocks_unsafe_content(vault, sample):
    r = NoteRenderer(vault.resolve_title, lambda i: vault.get_note(i).title)
    out = r.render(
        "<img src=x onerror=alert(1)> [a](javascript:alert(1)) [b](file:///C:/x) "
        "[[Forgetting curve]] [[Missing]] ![x](C:/secret.png) [ok](https://example.com)"
    )
    assert "<img" not in out
    assert 'href="javascript' not in out and 'href="file' not in out
    assert f'href="zettel:{sample["b"].id}"' in out
    assert 'href="zettel-new:Missing"' in out
    assert 'href="https://example.com"' in out


def test_malicious_archives_are_rejected(vault, tmp_path):
    evil = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil, "w") as zf:
        zf.writestr("../../escape.md", "# Escape")
    with pytest.raises(UnsafeInputError):
        import_path(vault, evil)
    bomb = tmp_path / "bomb.zip"
    with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("big.md", "0" * 5_000_000)
    with pytest.raises(UnsafeInputError):
        import_path(vault, bomb)
    bad = tmp_path / "bad.json"
    bad.write_text(
        json.dumps(
            {
                "format": "zettelapp",
                "version": 1,
                "notes": [{"id": "../../x", "title": 5, "body": None, "tags": "notalist"}],
            }
        )
    )
    result = import_path(vault, bad)
    assert result.notes == 1 and vault.all_notes()[0].title == ""


def test_malformed_import_is_rejected_without_partial_changes(vault, tmp_path):
    before = vault.count_notes()
    source = tmp_path / "malformed.json"
    source.write_text(
        json.dumps(
            {
                "format": "zettelapp",
                "version": 1,
                "notes": [
                    {"id": "20260101000000", "title": "Valid first note"},
                    {
                        "id": "20260101000001",
                        "title": "Malformed second note",
                        "mindmap": {"text": "Root", "children": 1},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(UnsafeInputError, match="mind map"):
        import_path(vault, source)

    assert vault.count_notes() == before
    assert vault.get_note("20260101000000") is None


def test_import_rolls_back_when_a_database_write_fails(vault, monkeypatch):
    before = vault.count_notes()
    original_save = vault.save_note

    def fail_on_second_note(note, touch=True):
        if note.id == "20260101000003":
            raise RuntimeError("simulated write failure")
        return original_save(note, touch)

    monkeypatch.setattr(vault, "save_note", fail_on_second_note)
    data = {
        "format": "zettelapp",
        "version": 1,
        "notes": [
            {"id": "20260101000002", "title": "First", "body": "first body"},
            {"id": "20260101000003", "title": "Second", "body": "second body"},
        ],
    }

    with pytest.raises(RuntimeError, match="simulated write failure"):
        import_data(vault, data)

    assert vault.count_notes() == before
    assert vault.get_note("20260101000002") is None
    assert vault.get_note("20260101000003") is None


def test_archive_failure_rolls_back_imported_assets(vault, monkeypatch, tmp_path):
    original_save = vault.save_note

    def fail_save(note, touch=True):
        raise RuntimeError("simulated archive failure")

    monkeypatch.setattr(vault, "save_note", fail_save)
    asset_name = "a" * 20 + ".png"
    archive = tmp_path / "failing-archive.zip"
    manifest = {
        "format": "zettelapp",
        "version": 1,
        "assets": [asset_name],
        "notes": [{"id": "20260101000004", "title": "Note", "image": asset_name}],
    }
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr(f"assets/{asset_name}", tiny_png())

    with pytest.raises(RuntimeError, match="simulated archive failure"):
        import_path(vault, archive)

    monkeypatch.setattr(vault, "save_note", original_save)
    assert vault.get_note("20260101000004") is None
    assert not any(vault.assets_dir.iterdir())


@pytest.mark.parametrize("zipped", [False, True])
def test_markdown_import_failure_rolls_back_notes_links_and_images(
    vault, monkeypatch, tmp_path, zipped
):
    folder = tmp_path / "markdown"
    folder.mkdir()
    (folder / "pic.png").write_bytes(tiny_png())
    (folder / "a.md").write_text("# First\n\nSee [[b]].\n\n![[pic.png]]\n", encoding="utf-8")
    (folder / "b.md").write_text("# Second\n\nBack to [[a]].\n", encoding="utf-8")
    source = folder
    if zipped:
        source = tmp_path / "markdown.zip"
        with zipfile.ZipFile(source, "w") as zf:
            for path in folder.iterdir():
                zf.write(path, path.name)
    original_save = vault.save_note
    written = {}

    def fail_on_second_save(note, touch=True):
        if written:
            raise RuntimeError("simulated Markdown import failure")
        original_save(note, touch)
        written.update(links=len(vault.all_links()), images=len(list(vault.assets_dir.iterdir())))
        return note

    monkeypatch.setattr(vault, "save_note", fail_on_second_save)
    events = []
    vault.listeners.append(events.append)

    with pytest.raises(RuntimeError, match="simulated Markdown import failure"):
        import_path(vault, source)

    assert written == {"links": 1, "images": 1}  # the first note was saved before the failure
    assert vault.all_notes(include_deleted=True) == []
    assert vault.all_links() == []
    assert not any(vault.assets_dir.iterdir())
    assert events == []


def test_single_markdown_file_failure_rolls_back(vault, monkeypatch, tmp_path):
    (tmp_path / "pic.png").write_bytes(tiny_png())
    source = tmp_path / "note.md"
    source.write_text("# Note\n\n![[pic.png]]\n", encoding="utf-8")

    def fail_save(note, touch=True):
        raise RuntimeError("simulated Markdown import failure")

    monkeypatch.setattr(vault, "save_note", fail_save)

    with pytest.raises(RuntimeError, match="simulated Markdown import failure"):
        import_path(vault, source)

    assert vault.all_notes(include_deleted=True) == []
    assert not any(vault.assets_dir.iterdir())


def test_markdown_import_skips_a_bad_image_and_keeps_the_rest(vault, tmp_path):
    folder = tmp_path / "markdown"
    folder.mkdir()
    (folder / "fake.png").write_text("not an image", encoding="utf-8")
    (folder / "a.md").write_text("# First\n\n![[fake.png]]\n", encoding="utf-8")

    result = import_path(vault, folder)

    assert result.notes == 1 and result.images == 0
    assert len(result.warnings) == 1 and "fake.png" in result.warnings[0]
    assert vault.resolve_title("First") is not None
    assert not any(vault.assets_dir.iterdir())


ENEX = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export4.dtd">
<en-export>
<note>
<title>Trip planning</title>
<content><![CDATA[<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note><h2>Packing</h2><div><en-todo checked="true"/>Passport</div><div><en-todo/>Charger</div>
<ul><li>One <b>bold</b> item</li><li>Another <a href="https://example.com/x">link</a></li></ul>
<div>Map: <en-media hash="{img}" type="image/png"/></div>
<div>Ticket: <en-media hash="{pdf}" type="application/pdf"/></div>
<div><a href="javascript:alert(1)">bad</a></div>
<en-crypt>secret</en-crypt></en-note>]]></content>
<created>20240131T120000Z</created>
<tag>travel</tag><tag>Summer 2024</tag>
<note-attributes><source-url>https://example.com/source</source-url></note-attributes>
<resource><data encoding="base64">{img_data}</data><mime>image/png</mime>
<resource-attributes><file-name>map.png</file-name></resource-attributes></resource>
<resource><data encoding="base64">{pdf_data}</data><mime>application/pdf</mime>
<resource-attributes><file-name>ticket.pdf</file-name></resource-attributes></resource>
</note>
<note><title>Second</title><content><![CDATA[<en-note>Plain text</en-note>]]></content></note>
</en-export>
"""


def _enex(tmp_path, text=None):
    import base64
    import hashlib

    png, pdf = tiny_png(), b"%PDF-1.4 fake"
    path = tmp_path / "export.enex"
    path.write_text(
        text
        or ENEX.replace("{img}", hashlib.md5(png).hexdigest())
        .replace("{pdf}", hashlib.md5(pdf).hexdigest())
        .replace("{img_data}", base64.b64encode(png).decode())
        .replace("{pdf_data}", base64.b64encode(pdf).decode()),
        encoding="utf-8",
    )
    return path


def test_an_evernote_export_imports_text_tags_pictures_and_checklists(vault, tmp_path):
    result = import_path(vault, _enex(tmp_path))
    assert result.notes == 2 and result.images == 1
    assert any("ticket.pdf" in w or "attachment" in w for w in result.warnings)
    note = next(n for n in vault.all_notes() if n.title == "Trip planning")
    assert "## Packing" in note.body
    assert "- [x] Passport" in note.body and "- [ ] Charger" in note.body
    assert "- One **bold** item" in note.body
    assert "[link](https://example.com/x)" in note.body
    assert "![](asset:" in note.body and "*ticket.pdf*" in note.body
    assert "javascript" not in note.body and "secret" not in note.body
    assert sorted(note.tags) == ["summer-2024", "travel"]
    assert note.url == "https://example.com/source"
    assert note.created.startswith("2024-01-31T12:00:00")


def test_an_evernote_export_with_entity_declarations_is_refused(vault, tmp_path):
    bomb = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><en-export></en-export>'
    with pytest.raises(UnsafeInputError):
        import_path(vault, _enex(tmp_path, bomb))
    assert vault.count_notes() == 0


def test_a_broken_evernote_export_changes_nothing(vault, tmp_path):
    with pytest.raises(UnsafeInputError):
        import_path(vault, _enex(tmp_path, "<en-export><note><title>A</title>"))
    assert vault.count_notes() == 0


def test_markdown_links_note_embeds_aliases_and_notion_names_become_note_links(vault, tmp_path):
    folder = tmp_path / "export"
    (folder / "sub").mkdir(parents=True)
    notion = "Reading list 0123456789abcdef0123456789abcdef"
    (folder / f"{notion}.md").write_text("Books to read.\n", encoding="utf-8")
    (folder / "sub" / "Target.md").write_text(
        "---\naliases: [Goal]\n---\nThe target.\n", encoding="utf-8"
    )
    (folder / "Source.md").write_text(
        "See [the list](Reading%20list%200123456789abcdef0123456789abcdef.md), "
        "[target](sub/Target.md), [[Goal]] and ![[Target]]. Missing: [x](Nowhere.md).\n",
        encoding="utf-8",
    )
    import_path(vault, folder)
    titles = {n.title: n for n in vault.all_notes()}
    assert "Reading list" in titles  # Notion's ID is not part of the title
    body = titles["Source"].body
    assert "[[Reading list|the list]]" in body
    assert "[[Target]]" in body and "![[" not in body
    assert "[[Target|Goal]]" in body
    assert "[x](Nowhere.md)" in body  # a link to nothing that was imported stays as it was
    linked = {vault.get_note(l.dst).title for l in vault.links_from(titles["Source"].id)}
    assert linked == {"Reading list", "Target"}
