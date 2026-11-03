"""Read Evernote exports (.enex): each note's title, text, tags, dates, source and pictures.

An .enex file is XML; each note's text is itself a small HTML document (ENML) that refers to its
pictures and attachments by the MD5 of their data. The file is read note by note, so a large
export never has to fit in memory, and it is untrusted like any import: entity declarations are
refused outright, and pictures are verified by content when they are stored.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

from zettelapp.core.security import UnsafeInputError, is_openable_url
from zettelapp.i18n import _

MAX_NOTES = 20_000


@dataclass
class Resource:
    data: bytes
    mime: str
    name: str


@dataclass
class EnexNote:
    title: str
    content: str  # ENML
    created: str | None
    updated: str | None
    tags: list[str] = field(default_factory=list)
    url: str = ""
    resources: dict[str, Resource] = field(default_factory=dict)  # MD5 hex -> resource


def _text(element: ET.Element, tag: str) -> str:
    found = element.find(tag)
    return (found.text or "").strip() if found is not None else ""


def _timestamp(value: str) -> str | None:
    """Evernote writes times as 20240131T120000Z."""
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z", value)
    return f"{m[1]}-{m[2]}-{m[3]}T{m[4]}:{m[5]}:{m[6]}+00:00" if m else None


def read_enex(path: Path) -> Iterator[EnexNote]:
    with path.open("rb") as head:
        if b"<!ENTITY" in head.read(64 * 1024):
            raise UnsafeInputError(
                _("This file declares XML entities, which an Evernote export never does.")
            )
    count = 0
    try:
        for _event, element in ET.iterparse(path, events=("end",)):
            if element.tag != "note":
                continue
            count += 1
            if count > MAX_NOTES:
                raise UnsafeInputError(_("The file contains too many notes."))
            resources = {}
            for res in element.findall("resource"):
                data_el = res.find("data")
                try:
                    data = (
                        base64.b64decode(data_el.text or "", validate=False)
                        if data_el is not None
                        else b""
                    )
                except (binascii.Error, ValueError):
                    continue
                attrs = res.find("resource-attributes")
                name = _text(attrs, "file-name") if attrs is not None else ""
                resources[hashlib.md5(data).hexdigest()] = Resource(data, _text(res, "mime"), name)
            attributes = element.find("note-attributes")
            yield EnexNote(
                title=_text(element, "title"),
                content=element.findtext("content") or "",
                created=_timestamp(_text(element, "created")),
                updated=_timestamp(_text(element, "updated")),
                tags=[t.text.strip() for t in element.findall("tag") if t.text and t.text.strip()],
                url=_text(attributes, "source-url") if attributes is not None else "",
                resources=resources,
            )
            element.clear()  # the note is done: free it, pictures included
    except ET.ParseError as exc:
        raise UnsafeInputError(
            _("This is not a readable Evernote export: {error}").format(error=exc)
        ) from exc


class _MarkdownWriter(HTMLParser):
    """ENML to Markdown: the structure people write in notes, not every detail of layout."""

    def __init__(self, media):
        super().__init__(convert_charrefs=True)
        self.media = media  # MD5 hex, MIME type -> Markdown for that picture or attachment
        self.out: list[str] = []
        self.lists: list[list] = []  # [kind, next number]
        self.links: list[tuple[str | None, int]] = []  # safe href, where its text starts
        self.pre = 0
        self.skip = 0  # inside <en-crypt>, <script> or <style>

    def _newline(self, blank: bool = False) -> None:
        text = "".join(self.out)
        if not text:
            return
        wanted = "\n\n" if blank else "\n"
        tail = len(text) - len(text.rstrip("\n"))
        if tail < len(wanted):
            self.out.append(wanted[tail:])

    def handle_starttag(self, tag: str, attrs) -> None:
        a = dict(attrs)
        if tag in ("en-crypt", "script", "style"):
            self.skip += 1
            if tag == "en-crypt":
                self.out.append(_("[encrypted text]"))
            return
        if self.skip:
            return
        if tag in ("p", "blockquote", "table", "ul", "ol", "pre") or re.fullmatch(r"h[1-6]", tag):
            self._newline(blank=not self.lists)
        elif tag in ("div", "br", "tr"):
            self._newline()
        if re.fullmatch(r"h[1-6]", tag):
            self.out.append("#" * int(tag[1]) + " ")
        elif tag in ("b", "strong"):
            self.out.append("**")
        elif tag in ("i", "em"):
            self.out.append("*")
        elif tag in ("s", "strike", "del"):
            self.out.append("~~")
        elif tag == "code" and not self.pre:
            self.out.append("`")
        elif tag == "pre":
            self.pre += 1
            self.out.append("```\n")
        elif tag == "blockquote":
            self.out.append("> ")
        elif tag in ("ul", "ol"):
            self.lists.append([tag, 1])
        elif tag == "li":
            self._newline()
            kind = self.lists[-1] if self.lists else ["ul", 1]
            indent = "  " * max(0, len(self.lists) - 1)
            if kind[0] == "ol":
                self.out.append(f"{indent}{kind[1]}. ")
                kind[1] += 1
            else:
                self.out.append(f"{indent}- ")
        elif tag in ("td", "th"):
            self.out.append(" | ")
        elif tag == "hr":
            self._newline(blank=True)
            self.out.append("---")
            self._newline(blank=True)
        elif tag == "a":
            href = a.get("href") or ""
            self.links.append((href if is_openable_url(href) else None, len(self.out)))
            self.out.append("[")
        elif tag == "en-todo":
            self._newline()
            self.out.append("- [x] " if a.get("checked") == "true" else "- [ ] ")
        elif tag == "en-media":
            self.out.append(self.media(a.get("hash", ""), a.get("type", "")))

    def handle_endtag(self, tag: str) -> None:
        if tag in ("en-crypt", "script", "style"):
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag in ("b", "strong"):
            self.out.append("**")
        elif tag in ("i", "em"):
            self.out.append("*")
        elif tag in ("s", "strike", "del"):
            self.out.append("~~")
        elif tag == "code" and not self.pre:
            self.out.append("`")
        elif tag == "pre":
            self.pre = max(0, self.pre - 1)
            self._newline()
            self.out.append("```")
            self._newline(blank=True)
        elif tag == "a" and self.links:
            href, start = self.links.pop()
            text = "".join(self.out[start + 1 :]).strip()
            if href and text:
                self.out.append(f"]({href})")
            elif text:  # an address ZettelApp won't open: keep the text alone
                self.out[start] = ""
            else:  # no text: show the address itself, if it is safe
                self.out[start] = href or ""
        elif tag in ("ul", "ol"):
            if self.lists:
                self.lists.pop()
            self._newline(blank=not self.lists)
        elif tag in ("p", "blockquote", "table") or re.fullmatch(r"h[1-6]", tag):
            self._newline(blank=True)

    def handle_startendtag(self, tag: str, attrs) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        self.out.append(data if self.pre else re.sub(r"\s+", " ", data))

    def markdown(self) -> str:
        text = "".join(self.out)
        lines = [line.rstrip() for line in text.splitlines()]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def enml_to_markdown(enml: str, media) -> str:
    """Markdown for a note's ENML. *media(hash, mime)* gives the text for each picture or
    attachment it refers to."""
    writer = _MarkdownWriter(media)
    writer.feed(re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>", "", enml))
    writer.close()
    return writer.markdown()
