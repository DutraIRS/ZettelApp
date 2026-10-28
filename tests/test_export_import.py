import json
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


def _styled_type(vault):
    from zettelapp.core.models import LinkType

    return vault.save_link_type(
        LinkType("", "Inspired by", "Inspires", "#123456", line_style="long_dash", arrow="bar")
    )


def test_link_styles_survive_an_archive_roundtrip(vault, sample, tmp_path):
    _styled_type(vault)
    contradicts = vault.link_type_map()["contradicts"]
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
