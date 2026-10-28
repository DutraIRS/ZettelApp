"""Markdown rendering shared by the preview, the HTML export and Anki cards.

Safety model: raw HTML in notes is never rendered (it is shown as text), link
targets are limited to notes, http(s)/mailto URLs, Zotero items and (in the app
only) files on a local drive, and images may only come from the vault's own
assets folder, so viewing a note never loads anything from the network or from
elsewhere on disk.
"""

from __future__ import annotations

import html
import re
from collections.abc import Callable
from urllib.parse import quote, unquote
from xml.etree import ElementTree as ET

from markdown_it import MarkdownIt

from zettelapp.core.models import LinkType, mindmap_nodes
from zettelapp.core.security import (
    file_url,
    is_safe_web_url,
    is_valid_asset_name,
    is_valid_note_id,
    is_zotero_url,
    local_file_path,
)
from zettelapp.core.textutil import CLOZE_RE, WIKILINK_RE

NOTE_SCHEME = "zettel:"
NEW_NOTE_SCHEME = "zettel-new:"
ASSET_SCHEME = "asset:"

_CODE_SPLIT = re.compile(r"(```[\s\S]*?(?:```|$)|`[^`\n]*`)")
_MD_ESCAPE = re.compile(r"([\\`*_\[\]<>()#!|])")
_QA_PREFIX = re.compile(r"^(\s*)(Q|A|Question|Answer)\s*:", re.I | re.M)


def _escape_md(text: str) -> str:
    return _MD_ESCAPE.sub(r"\\\1", text)


class NoteRenderer:
    """Render note Markdown to an HTML fragment.

    *resolve* maps a wiki-link target (title or id) to a note id. *note_href*
    and *asset_href* produce the final URLs, which lets the same renderer serve
    the in-app preview (zettel:/asset: URLs) and exported web pages. Links to local
    files are only made clickable with *allow_file_links* (the app's own preview);
    exports and Anki cards show them as plain text.
    """

    def __init__(
        self,
        resolve: Callable[[str], str | None],
        title_of: Callable[[str], str] = lambda note_id: note_id,
        note_href: Callable[[str], str | None] = lambda note_id: NOTE_SCHEME + note_id,
        asset_href: Callable[[str], str | None] = lambda name: ASSET_SCHEME + name,
        link_types: dict[str, LinkType] | None = None,
        allow_new_note_links: bool = True,
        keep_cloze: bool = False,
        allow_file_links: bool = False,
    ):
        self.resolve = resolve
        self.keep_cloze = keep_cloze
        self.title_of = title_of
        self.note_href = note_href
        self.asset_href = asset_href
        self.link_types = link_types or {}
        self.allow_new_note_links = allow_new_note_links
        self.allow_file_links = allow_file_links
        self.md = MarkdownIt("commonmark", {"html": False, "breaks": True, "typographer": False})
        self.md.enable(["table", "strikethrough"])
        # markdown-it drops file: links outright; let them through to _target_href,
        # which decides what every link may point to.
        validate = self.md.validateLink
        self.md.validateLink = lambda url: url[:5].lower() == "file:" or validate(url)
        # markdown-it binds rule functions to its renderer, so pass plain functions.
        self.md.add_render_rule("link_open", lambda r, *args: self._render_link_open(r, *args))
        self.md.add_render_rule("image", lambda r, *args: self._render_image(r, *args))

    # --- pre-processing -----------------------------------------------------

    def _wikilink(self, m: re.Match) -> str:
        target = m.group("target").strip()
        note_id = self.resolve(target)
        text = m.group("alias") or (self.title_of(note_id) if note_id else target) or target
        prefix = ""
        if m.group("type"):
            lt = self.link_types.get(m.group("type").lower().replace("-", "_"))
            prefix = f"*{_escape_md(lt.label if lt else m.group('type'))}:* "
        if note_id:
            return f"{prefix}[{_escape_md(text)}]({NOTE_SCHEME}{note_id})"
        if self.allow_new_note_links:
            return f"{prefix}[{_escape_md(text)}]({NEW_NOTE_SCHEME}{quote(target, safe='')})"
        return prefix + _escape_md(text)

    def _prepare(self, text: str) -> str:
        parts = _CODE_SPLIT.split(text or "")
        for i in range(0, len(parts), 2):  # even indexes are outside code
            segment = WIKILINK_RE.sub(self._wikilink, parts[i])
            if not self.keep_cloze:
                segment = CLOZE_RE.sub(lambda m: f"**{m.group(2)}**", segment)
            parts[i] = _QA_PREFIX.sub(lambda m: f"{m.group(1)}**{m.group(2)}:**", segment)
        return "".join(parts)

    # --- render rules ---------------------------------------------------------

    def _target_href(self, href: str) -> str | None:
        if href.startswith(NOTE_SCHEME):
            note_id = href[len(NOTE_SCHEME) :]
            return self.note_href(note_id) if is_valid_note_id(note_id) else None
        if href.startswith(NEW_NOTE_SCHEME):
            return href if self.allow_new_note_links else None
        if is_safe_web_url(href) or is_zotero_url(href):
            return href
        path = local_file_path(href) or local_file_path(unquote(href))  # file:/// or C:\…
        return file_url(path) if path and self.allow_file_links else None

    def _render_link_open(self, renderer, tokens, idx, options, env):
        token = tokens[idx]
        href = self._target_href(token.attrGet("href") or "")
        token.attrs = {}
        if href is None:
            token.attrSet("href", "#")
            token.attrSet("class", "broken")
        else:
            token.attrSet("href", href)
            if is_safe_web_url(href):
                token.attrSet("class", "external")
                token.attrSet("rel", "noopener noreferrer")
            elif is_zotero_url(href):
                token.attrSet("class", "zotero")
            elif href.startswith("file:"):
                token.attrSet("class", "file")
            elif href.startswith(NEW_NOTE_SCHEME):
                token.attrSet("class", "new-note")
            else:
                token.attrSet("class", "internal")
        return renderer.renderToken(tokens, idx, options, env)

    def _render_image(self, renderer, tokens, idx, options, env):
        token = tokens[idx]
        alt = renderer.renderInlineAsText(token.children or [], options, env)
        src = token.attrGet("src") or ""
        name = src[len(ASSET_SCHEME) :] if src.startswith(ASSET_SCHEME) else ""
        url = self.asset_href(name) if is_valid_asset_name(name) else None
        if url is None:
            return f'<span class="missing-image">[{html.escape(alt or "image")}]</span>'
        return f'<img src="{html.escape(url, quote=True)}" alt="{html.escape(alt, quote=True)}">'

    def render(self, text: str) -> str:
        return self.md.render(self._prepare(text))


def new_note_title(href: str) -> str | None:
    if not href.startswith(NEW_NOTE_SCHEME):
        return None
    return unquote(href[len(NEW_NOTE_SCHEME) :])[:200] or None


# --- mind maps ------------------------------------------------------------


def mindmap_to_markdown(root: dict) -> str:
    lines = []
    for node, depth in mindmap_nodes(root):
        text = node.get("text") or "…"
        if node.get("note"):
            text = f"[[{node['note']}|{text}]]"
        lines.append("  " * depth + "- " + text)
    return "\n".join(lines)


def mindmap_to_html(root: dict, note_href: Callable[[str], str | None] = lambda _: None) -> str:
    def render(node: dict) -> str:
        text = html.escape(node.get("text") or "…")
        href = note_href(node["note"]) if node.get("note") else None
        label = f'<a href="{html.escape(href, quote=True)}">{text}</a>' if href else text
        children = "".join(render(c) for c in node.get("children", []))
        return f"<li>{label}" + (f"<ul>{children}</ul>" if children else "") + "</li>"

    return f'<ul class="mindmap">{render(root)}</ul>'


def mindmap_to_freemind(root: dict) -> str:
    """FreeMind 1.0 (.mm) XML, readable by FreeMind, Freeplane, XMind and others."""

    def build(parent: ET.Element, node: dict) -> None:
        el = ET.SubElement(
            parent, "node", TEXT=node.get("text") or "", ID="ID_" + node.get("id", "x")
        )
        for child in node.get("children", []):
            build(el, child)

    doc = ET.Element("map", version="1.0.1")
    build(doc, root)
    return ET.tostring(doc, encoding="unicode")
