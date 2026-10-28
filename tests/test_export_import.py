import json
import sqlite3
import zipfile

import pytest

from tests.conftest import tiny_png
from zettelapp.core import export as ex
from zettelapp.core.graph import force_layout, subgraph
from zettelapp.core.importer import import_path
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
