"""Export the whole collection or any subset (subgraph, tag, selection).

Formats: ZettelApp archive, JSON, Markdown (Obsidian-compatible), static
website, GraphML, Graphviz DOT and Anki decks. Files are written to a
temporary name first and moved into place only when complete.
"""

from __future__ import annotations

import contextlib
import html
import json
import os
import re
import zipfile
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from zettelapp import __version__
from zettelapp.core.anki import anki_renderer, build_payloads, write_apkg
from zettelapp.core.graph import force_layout
from zettelapp.core.models import Flashcard, Link, LinkType, Note
from zettelapp.core.render import NoteRenderer, mindmap_to_freemind, mindmap_to_html
from zettelapp.core.security import is_openable_url, safe_filename
from zettelapp.core.storage import Vault
from zettelapp.core.textutil import WIKILINK_RE, fold, snippet

ASSET_REF_RE = re.compile(r"asset:([0-9a-f]{20}\.(?:png|jpg|gif|webp|bmp))")
ARCHIVE_FORMAT = "zettelapp"
ARCHIVE_VERSION = 1


@dataclass(frozen=True)
class ExportFormat:
    key: str
    label: str
    extension: str
    description: str

    @property
    def file_filter(self) -> str:
        return f"{self.label} (*{self.extension})"


FORMATS = [
    ExportFormat("archive", "ZettelApp archive", ".zip",
                 "Everything, including images. Re-import it into ZettelApp on any computer."),
    ExportFormat("markdown", "Markdown files", ".zip",
                 "One .md file per note with front matter and [[wiki links]]. Opens in Obsidian and other editors."),
    ExportFormat("html", "Website", ".zip",
                 "A self-contained static website with a graph overview. No scripts; open index.html."),
    ExportFormat("json", "JSON", ".json", "Structured data for scripts and other tools (images not included)."),
    ExportFormat("graphml", "GraphML", ".graphml", "The link graph for Gephi, yEd, Cytoscape or NetworkX."),
    ExportFormat("dot", "Graphviz DOT", ".dot", "The link graph as a Graphviz diagram."),
    ExportFormat("anki", "Anki deck", ".apkg", "The flashcards of the exported notes, ready to import into Anki."),
]
FORMATS_BY_KEY = {f.key: f for f in FORMATS}


@dataclass
class Bundle:
    vault_name: str
    vault_id: str
    notes: list[Note]
    links: list[Link]
    link_types: list[LinkType]
    cards: list[Flashcard]
    assets: list[str]

    @property
    def note_map(self) -> dict[str, Note]:
        return {n.id: n for n in self.notes}


@dataclass
class ExportResult:
    path: Path
    notes: int
    links: int
    cards: int
    assets: int


def collect(vault: Vault, note_ids: Iterable[str]) -> Bundle:
    ids = set(note_ids)
    notes = sorted((n for n in vault.all_notes() if n.id in ids), key=lambda n: fold(n.display_title))
    links = [l for l in vault.all_links() if l.src in ids and l.dst in ids]
    cards = vault.cards_for_notes(ids)
    refs: set[str] = set()
    for n in notes:
        refs.update(ASSET_REF_RE.findall(n.body))
        if n.image:
            refs.add(n.image)
    for c in cards:
        refs.update(ASSET_REF_RE.findall(c.front + c.back))
    assets = sorted(r for r in refs if vault.asset_path(r) is not None)
    return Bundle(vault.name, vault.vault_id, notes, links, vault.link_types(), cards, assets)


@contextlib.contextmanager
def atomic_output(dest: Path) -> Iterator[Path]:
    dest = Path(dest)
    tmp = dest.with_name(dest.name + ".part")
    try:
        yield tmp
        os.replace(tmp, dest)
    finally:
        with contextlib.suppress(FileNotFoundError):
            tmp.unlink()


def export(vault: Vault, fmt: str, note_ids: Iterable[str], dest: str | Path, *,
           title: str | None = None, deck_name: str = "ZettelApp") -> ExportResult:
    bundle = collect(vault, note_ids)
    dest = Path(dest)
    title = title or vault.name
    writers = {
        "archive": lambda p: _write_archive(bundle, vault, p),
        "json": lambda p: p.write_text(json.dumps(bundle_to_dict(bundle), ensure_ascii=False, indent=2),
                                       encoding="utf-8"),
        "markdown": lambda p: _write_markdown(bundle, vault, p),
        "html": lambda p: _write_site(bundle, vault, p, title),
        "graphml": lambda p: _write_graphml(bundle, p),
        "dot": lambda p: p.write_text(_dot(bundle, title), encoding="utf-8"),
        "anki": lambda p: _write_anki(bundle, vault, p, deck_name),
    }
    if fmt not in writers:
        raise ValueError(f"Unknown export format: {fmt}")
    with atomic_output(dest) as tmp:
        writers[fmt](tmp)
    return ExportResult(dest, len(bundle.notes), len(bundle.links), len(bundle.cards), len(bundle.assets))


# --- JSON / archive ---------------------------------------------------------

def bundle_to_dict(bundle: Bundle) -> dict:
    return {
        "format": ARCHIVE_FORMAT,
        "version": ARCHIVE_VERSION,
        "app_version": __version__,
        "exported": datetime.now().astimezone().isoformat(timespec="seconds"),
        "vault": bundle.vault_name,
        "notes": [{
            "id": n.id, "title": n.title, "body": n.body, "url": n.url, "image": n.image, "tags": n.tags,
            "mindmap": n.mindmap, "created": n.created, "modified": n.modified,
        } for n in bundle.notes],
        "links": [{"src": l.src, "dst": l.dst, "type": l.type, "origin": l.origin} for l in bundle.links],
        "link_types": [{"id": t.id, "label": t.label, "inverse_label": t.inverse_label, "color": t.color,
                        "directed": t.directed} for t in bundle.link_types],
        "flashcards": [{"note_id": c.note_id, "front": c.front, "back": c.back, "kind": c.kind,
                        "source": c.source} for c in bundle.cards],
        "assets": bundle.assets,
    }


def _write_archive(bundle: Bundle, vault: Vault, path: Path) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(bundle_to_dict(bundle), ensure_ascii=False, indent=1))
        for name in bundle.assets:
            zf.write(vault.asset_path(name), f"assets/{name}")


# --- Markdown -----------------------------------------------------------------

def _unique_stems(notes: list[Note]) -> dict[str, str]:
    stems: dict[str, str] = {}
    used: set[str] = set()
    for n in notes:
        stem = safe_filename(n.display_title, default=n.id)
        if fold(stem) in used:  # Windows file names are case-insensitive
            stem = f"{stem} ({n.id})"
        used.add(fold(stem))
        stems[n.id] = stem
    return stems


def _resolver(notes: list[Note]):
    ids = {n.id for n in notes}
    by_title: dict[str, str] = {}
    for n in sorted(notes, key=lambda n: n.id, reverse=True):
        by_title[fold(n.title.strip())] = n.id

    def resolve(target: str) -> str | None:
        target = target.strip()
        return target if target in ids else by_title.get(fold(target))
    return resolve


def _markdown_for(note: Note, bundle: Bundle, stems: dict[str, str], resolve, types: dict[str, LinkType]) -> str:
    def rewrite(m: re.Match) -> str:
        dst = resolve(m.group("target"))
        if dst is None or dst not in stems:
            return m.group(0)
        prefix = f"{m.group('type')}:: " if m.group("type") else ""
        alias = m.group("alias")
        if alias is None and fold(stems[dst]) != fold(m.group("target")):
            alias = bundle.note_map[dst].display_title
        return f"{prefix}[[{stems[dst]}{'|' + alias if alias else ''}]]"

    body = WIKILINK_RE.sub(rewrite, note.body)
    body = ASSET_REF_RE.sub(lambda m: "assets/" + m.group(1), body)

    outgoing = [l for l in bundle.links if l.src == note.id]
    grouped: dict[str, list[str]] = defaultdict(list)
    for l in outgoing:
        grouped[l.type].append(f"[[{stems[l.dst]}]]")
    meta = {"id": note.id, "title": note.title, "tags": note.tags}
    if note.url:
        meta["url"] = note.url
    if note.image:
        meta["image"] = "assets/" + note.image
    meta["created"] = note.created
    meta["modified"] = note.modified
    if grouped:
        meta["links"] = dict(grouped)
    if note.mindmap:
        meta["mindmap"] = note.mindmap
    # JSON values are valid YAML, which keeps the front matter unambiguous.
    front = "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in meta.items())
    parts = [f"---\n{front}\n---\n", body.rstrip() + "\n"]

    manual = [l for l in outgoing if l.origin != "inline"]
    if manual:
        lines = [f"- {l.type}:: [[{stems[l.dst]}]]" for l in manual]
        parts.append("\n## Links\n\n" + "\n".join(lines) + "\n")
    cards = [c for c in bundle.cards if c.note_id == note.id and c.source == "manual"]
    if cards:
        blocks = [c.front if c.kind == "cloze" else f"Q: {c.front}\nA: {c.back}" for c in cards]
        parts.append("\n## Flashcards\n\n" + "\n\n".join(blocks) + "\n")
    return "".join(parts)


def _write_markdown(bundle: Bundle, vault: Vault, path: Path) -> None:
    stems = _unique_stems(bundle.notes)
    resolve = _resolver(bundle.notes)
    types = {t.id: t for t in bundle.link_types}
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for note in bundle.notes:
            zf.writestr(f"{stems[note.id]}.md", _markdown_for(note, bundle, stems, resolve, types))
        for name in bundle.assets:
            zf.write(vault.asset_path(name), f"assets/{name}")


# --- static website ---------------------------------------------------------

_CSP = ("default-src 'none'; img-src 'self'; style-src 'self'; base-uri 'none'; "
        "form-action 'none'; frame-ancestors 'none'")

SITE_CSS = """
:root { --bg: #f7f7f8; --surface: #fff; --text: #1b1b1b; --muted: #5f6368; --border: #e3e3e6;
        --accent: #0f6cbd; --chip: #eef3fb; color-scheme: light dark; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #1c1c1e; --surface: #262628; --text: #f2f2f2; --muted: #a8a8ad; --border: #3a3a3d;
          --accent: #62b3ff; --chip: #23364d; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
       font: 16px/1.6 "Segoe UI Variable Text", "Segoe UI", system-ui, sans-serif; }
a { color: var(--accent); text-decoration: none; } a:hover { text-decoration: underline; }
header.top { padding: 14px 24px; border-bottom: 1px solid var(--border); background: var(--surface); }
header.top a { font-weight: 600; color: var(--text); }
main { max-width: 860px; margin: 0 auto; padding: 32px 20px 64px; }
h1 { font-size: 2rem; line-height: 1.25; margin: 0 0 6px; }
.meta { color: var(--muted); font-size: .9rem; margin: 0 0 14px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0 18px; padding: 0; list-style: none; }
.chips a { background: var(--chip); padding: 2px 10px; border-radius: 999px; font-size: .85rem; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 20px 24px; }
article img, .hero { max-width: 100%; border-radius: 8px; }
.hero { display: block; max-height: 340px; margin: 6px 0 18px; }
pre { background: rgba(127,127,127,.12); padding: 12px; border-radius: 8px; overflow-x: auto; }
code { font-family: "Cascadia Code", Consolas, monospace; font-size: .9em; }
blockquote { margin: 0; padding-left: 14px; border-left: 3px solid var(--border); color: var(--muted); }
table { border-collapse: collapse; } td, th { border: 1px solid var(--border); padding: 4px 10px; }
a.broken, a.new-note { color: var(--muted); pointer-events: none; }
section { margin-top: 28px; } h2 { font-size: 1.15rem; margin: 0 0 10px; }
.links { list-style: none; padding: 0; margin: 0; }
.links li { padding: 6px 0; border-bottom: 1px solid var(--border); }
.links .type { display: inline-block; min-width: 9em; color: var(--muted); font-size: .9rem; }
details { border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; margin-bottom: 8px;
          background: var(--surface); }
summary { cursor: pointer; font-weight: 600; }
ul.mindmap, ul.mindmap ul { list-style: none; padding-left: 18px; border-left: 2px solid var(--border); }
ul.mindmap { padding-left: 0; border: none; }
.graph { width: 100%; height: auto; background: var(--surface); border: 1px solid var(--border);
         border-radius: 10px; }
.graph line { stroke-opacity: .55; }
.graph circle { fill: var(--accent); stroke: var(--surface); stroke-width: 2; }
.graph text { fill: var(--muted); font-size: 11px; }
.notes { list-style: none; padding: 0; display: grid; gap: 10px; }
.notes li a { display: block; padding: 12px 16px; background: var(--surface); border: 1px solid var(--border);
              border-radius: 10px; color: var(--text); }
.notes li a:hover { border-color: var(--accent); text-decoration: none; }
.notes .snippet { color: var(--muted); font-size: .9rem; display: block; }
footer { text-align: center; color: var(--muted); font-size: .85rem; padding: 24px; }
"""


def _page(title: str, body: str, root: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{_CSP}">
<meta name="referrer" content="no-referrer">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{root}style.css">
</head>
<body>
{body}
<footer>Exported from ZettelApp {html.escape(__version__)}</footer>
</body>
</html>
"""


def _fmt_date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).astimezone().strftime("%d %b %Y")
    except ValueError:
        return iso


def _svg_graph(bundle: Bundle, types: dict[str, LinkType]) -> str:
    notes = bundle.notes[:1500]
    if not notes:
        return ""
    ids = [n.id for n in notes]
    pos = force_layout(ids, [(l.src, l.dst) for l in bundle.links], size=1000.0)
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    pad = 60.0
    min_x, min_y = min(xs) - pad, min(ys) - pad
    width, height = max(xs) - min_x + pad, max(ys) - min_y + pad
    degree: dict[str, int] = defaultdict(int)
    for l in bundle.links:
        degree[l.src] += 1
        degree[l.dst] += 1
    labelled = set(sorted(ids, key=lambda i: -degree[i])[:60])
    out = [f'<svg class="graph" viewBox="{min_x:.0f} {min_y:.0f} {width:.0f} {height:.0f}" '
           f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Graph of notes">']
    for l in bundle.links:
        if l.src in pos and l.dst in pos:
            (x1, y1), (x2, y2) = pos[l.src], pos[l.dst]
            color = types[l.type].color if l.type in types else "#8a8a8a"
            out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                       f'stroke="{color}" stroke-width="1.5"/>')
    titles = {n.id: n.display_title for n in notes}
    for node_id in ids:
        x, y = pos[node_id]
        r = 5 + min(10, degree[node_id] ** 0.5 * 2)
        label = html.escape(titles[node_id])
        out.append(f'<a href="notes/{node_id}.html"><circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}">'
                   f'<title>{label}</title></circle>')
        if node_id in labelled:
            out.append(f'<text x="{x:.1f}" y="{y + r + 13:.1f}" text-anchor="middle">{label[:40]}</text>')
        out.append("</a>")
    out.append("</svg>")
    return "".join(out)


def _write_site(bundle: Bundle, vault: Vault, path: Path, title: str) -> None:
    notes = bundle.note_map
    types = {t.id: t for t in bundle.link_types}
    resolve = _resolver(bundle.notes)
    renderer = NoteRenderer(
        resolve, title_of=lambda i: notes[i].display_title if i in notes else i,
        note_href=lambda i: f"{i}.html" if i in notes else None,
        asset_href=lambda name: f"../assets/{name}" if name in bundle.assets else None,
        link_types=types, allow_new_note_links=False)
    tag_index: dict[str, list[Note]] = defaultdict(list)
    for n in bundle.notes:
        for t in n.tags:
            tag_index[t].append(n)

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("style.css", SITE_CSS)
        for name in bundle.assets:
            zf.write(vault.asset_path(name), f"assets/{name}")
        for n in bundle.notes:
            zf.writestr(f"notes/{n.id}.html", _note_page(n, bundle, renderer, types, title))
        items = "".join(
            f'<li><a href="notes/{n.id}.html"><strong>{html.escape(n.display_title)}</strong>'
            f'<span class="snippet">{html.escape(snippet(n.body, 160))}</span></a></li>'
            for n in bundle.notes)
        tags = "".join(
            f'<li><a href="#tag-{html.escape(t, quote=True)}">#{html.escape(t)} ({len(v)})</a></li>'
            for t, v in sorted(tag_index.items()))
        tag_sections = "".join(
            f'<section id="tag-{html.escape(t, quote=True)}"><h2>#{html.escape(t)}</h2><ul class="links">'
            + "".join(f'<li><a href="notes/{n.id}.html">{html.escape(n.display_title)}</a></li>' for n in v)
            + "</ul></section>" for t, v in sorted(tag_index.items()))
        body = (f'<main><h1>{html.escape(title)}</h1>'
                f'<p class="meta">{len(bundle.notes)} notes · {len(bundle.links)} links · exported '
                f'{datetime.now():%d %b %Y}</p>{_svg_graph(bundle, types)}'
                + (f'<section><h2>Tags</h2><ul class="chips">{tags}</ul></section>' if tags else "")
                + f'<section><h2>All notes</h2><ul class="notes">{items}</ul></section>{tag_sections}</main>')
        zf.writestr("index.html", _page(title, body, ""))


def _note_page(n: Note, bundle: Bundle, renderer: NoteRenderer, types: dict[str, LinkType], site: str) -> str:
    notes = bundle.note_map
    esc = html.escape
    parts = [f'<header class="top"><a href="../index.html">← {esc(site)}</a></header><main>',
             f"<h1>{esc(n.display_title)}</h1>",
             f'<p class="meta">{esc(n.id)} · created {_fmt_date(n.created)} · edited {_fmt_date(n.modified)}</p>']
    if n.tags:
        parts.append('<ul class="chips">' + "".join(
            f'<li><a href="../index.html#tag-{esc(t, quote=True)}">#{esc(t)}</a></li>' for t in n.tags) + "</ul>")
    if n.image and n.image in bundle.assets:
        parts.append(f'<img class="hero" src="../assets/{n.image}" alt="">')
    if n.url and is_openable_url(n.url):
        parts.append(f'<p>🔗 <a href="{esc(n.url, quote=True)}" rel="noopener noreferrer">{esc(n.url)}</a></p>')
    parts.append(f'<article class="card">{renderer.render(n.body)}</article>')
    if n.mindmap:
        parts.append("<section><h2>Mind map</h2>"
                     + mindmap_to_html(n.mindmap, lambda i: f"{i}.html" if i in notes else None) + "</section>")
    rows = []
    for l in bundle.links:
        if n.id not in (l.src, l.dst):
            continue
        outgoing = l.src == n.id
        other = notes[l.dst if outgoing else l.src]
        lt = types.get(l.type)
        label = lt.label_for(outgoing) if lt else l.type
        rows.append(f'<li><span class="type">{esc(label)}</span>'
                    f'<a href="{other.id}.html">{esc(other.display_title)}</a></li>')
    if rows:
        parts.append(f'<section><h2>Links</h2><ul class="links">{"".join(rows)}</ul></section>')
    cards = [c for c in bundle.cards if c.note_id == n.id]
    if cards:
        parts.append("<section><h2>Flashcards</h2>" + "".join(
            f"<details><summary>{esc(c.front if c.kind == 'basic' else 'Cloze')}</summary>"
            f"{renderer.render(c.back if c.kind == 'basic' else c.front)}</details>" for c in cards) + "</section>")
    parts.append("</main>")
    return _page(f"{n.display_title} · {site}", "".join(parts), "../")


# --- graph formats ------------------------------------------------------------

def _write_graphml(bundle: Bundle, path: Path) -> None:
    ns = "http://graphml.graphdrawing.org/xmlns"
    ET.register_namespace("", ns)
    root = ET.Element(f"{{{ns}}}graphml")
    keys = [("title", "node"), ("tags", "node"), ("url", "node"), ("created", "node"), ("modified", "node"),
            ("type", "edge"), ("label", "edge")]
    for name, scope in keys:
        ET.SubElement(root, f"{{{ns}}}key", id=f"{scope}_{name}", attrib={
            "for": scope, "attr.name": name, "attr.type": "string"})
    graph = ET.SubElement(root, f"{{{ns}}}graph", id="zettelkasten", edgedefault="directed")
    for n in bundle.notes:
        node = ET.SubElement(graph, f"{{{ns}}}node", id=n.id)
        for name, value in (("title", n.display_title), ("tags", " ".join(n.tags)), ("url", n.url),
                            ("created", n.created), ("modified", n.modified)):
            ET.SubElement(node, f"{{{ns}}}data", key=f"node_{name}").text = value
    types = {t.id: t for t in bundle.link_types}
    for i, l in enumerate(bundle.links):
        lt = types.get(l.type)
        edge = ET.SubElement(graph, f"{{{ns}}}edge", id=f"e{i}", source=l.src, target=l.dst,
                             directed="true" if (lt is None or lt.directed) else "false")
        ET.SubElement(edge, f"{{{ns}}}data", key="edge_type").text = l.type
        ET.SubElement(edge, f"{{{ns}}}data", key="edge_label").text = lt.label if lt else l.type
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def _dot_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _dot(bundle: Bundle, title: str) -> str:
    types = {t.id: t for t in bundle.link_types}
    lines = [f"digraph {_dot_str(title)} {{",
             '  graph [overlap=false, splines=true, fontname="Segoe UI"];',
             '  node [shape=box, style="rounded,filled", fillcolor="#eef3fb", color="#0f6cbd", fontname="Segoe UI"];',
             '  edge [fontname="Segoe UI", fontsize=9];']
    for n in bundle.notes:
        lines.append(f"  {_dot_str(n.id)} [label={_dot_str(n.display_title)}];")
    for l in bundle.links:
        lt = types.get(l.type)
        attrs = [f"color={_dot_str(lt.color if lt else '#8a8a8a')}", f"label={_dot_str(lt.label if lt else l.type)}"]
        if lt is not None and not lt.directed:
            attrs.append("dir=none")
        lines.append(f"  {_dot_str(l.src)} -> {_dot_str(l.dst)} [{', '.join(attrs)}];")
    lines.append("}")
    return "\n".join(lines) + "\n"


# --- Anki -------------------------------------------------------------------

def _write_anki(bundle: Bundle, vault: Vault, path: Path, deck_name: str) -> None:
    notes = bundle.note_map
    renderer = anki_renderer(_resolver(bundle.notes), lambda i: notes[i].display_title if i in notes else i)
    payloads = build_payloads(bundle.cards, notes, bundle.vault_id, renderer)
    write_apkg(payloads, path, deck_name, vault.asset_path, bundle.vault_id)


def export_mindmap(mindmap: dict, dest: str | Path) -> None:
    with atomic_output(Path(dest)) as tmp:
        tmp.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + mindmap_to_freemind(mindmap), encoding="utf-8")
