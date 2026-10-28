"""Zotero integration: search the local library, cite items, make literature notes.

Uses the read-only local API of Zotero 7+ (http://127.0.0.1:23119/api/), which
the user enables in Zotero ▸ Settings ▸ Advanced ▸ "Allow other applications
on this computer to communicate with Zotero". Requests never leave this
computer. Links into Zotero use the zotero:// scheme and are restricted to
"select item" and "open PDF" (see core.security.is_zotero_url).
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

from zettelapp.core.security import ZOTERO_KEY_RE, is_zotero_url
from zettelapp.core.textutil import normalize_tag

DEFAULT_PORT = 23119
MAX_RESPONSE = 10 * 1024 * 1024


class ZoteroError(RuntimeError):
    pass


def select_url(key: str, group_id: int | None = None) -> str:
    library = f"groups/{int(group_id)}" if group_id else "library"
    url = f"zotero://select/{library}/items/{key}"
    if not is_zotero_url(url):
        raise ValueError(f"Invalid Zotero item key: {key!r}")
    return url


def pdf_url(key: str, page: int | None = None, group_id: int | None = None) -> str:
    library = f"groups/{int(group_id)}" if group_id else "library"
    url = f"zotero://open-pdf/{library}/items/{key}" + (f"?page={int(page)}" if page else "")
    if not is_zotero_url(url):
        raise ValueError(f"Invalid Zotero item key: {key!r}")
    return url


@dataclass
class ZoteroItem:
    key: str
    title: str
    item_type: str = ""
    creators: list[str] = field(default_factory=list)  # "Lastname, F." or institution names
    year: str = ""
    publication: str = ""
    doi: str = ""
    url: str = ""
    abstract: str = ""
    tags: list[str] = field(default_factory=list)
    group_id: int | None = None

    @property
    def select_url(self) -> str:
        return select_url(self.key, self.group_id)

    def short_citation(self) -> str:
        """Author–year citation such as "Ebbinghaus (1885)" or "Smith et al. (2020)"."""
        surnames = [c.split(",")[0] for c in self.creators]
        if not surnames:
            who = self.title[:40] or "Untitled"
        elif len(surnames) == 1:
            who = surnames[0]
        elif len(surnames) == 2:
            who = f"{surnames[0]} & {surnames[1]}"
        else:
            who = f"{surnames[0]} et al."
        return f"{who} ({self.year or 'n.d.'})"

    def reference(self) -> str:
        """A compact, APA-like reference line (plain text)."""
        authors = ", ".join(self.creators[:6]) + (", et al." if len(self.creators) > 6 else "")
        parts = [
            f"{authors} ({self.year or 'n.d.'})." if authors else f"({self.year or 'n.d.'}).",
            f"{self.title}.",
        ]
        if self.publication:
            parts.append(f"{self.publication}.")
        if self.doi:
            parts.append(f"https://doi.org/{self.doi}")
        elif self.url:
            parts.append(self.url)
        return " ".join(parts)


def _creator_name(raw: dict) -> str | None:
    if not isinstance(raw, dict):
        return None
    if isinstance(raw.get("name"), str):
        return raw["name"].strip()[:120] or None
    last = raw.get("lastName") if isinstance(raw.get("lastName"), str) else ""
    first = raw.get("firstName") if isinstance(raw.get("firstName"), str) else ""
    if not last:
        return first.strip()[:120] or None
    initials = " ".join(f"{p[0]}." for p in re.split(r"[\s-]+", first) if p)
    return f"{last.strip()}, {initials}".strip(", ")[:120]


def parse_item(raw: dict) -> ZoteroItem | None:
    """Build a ZoteroItem from Web API v3 JSON, validating every field."""
    if not isinstance(raw, dict):
        return None
    data = raw.get("data") if isinstance(raw.get("data"), dict) else raw
    key = data.get("key") or raw.get("key")
    if not isinstance(key, str) or not ZOTERO_KEY_RE.fullmatch(key):
        return None
    if data.get("itemType") in ("attachment", "note", "annotation"):
        return None

    def text(name: str, limit: int = 500) -> str:
        value = data.get(name)
        return value.strip()[:limit] if isinstance(value, str) else ""

    creators = [
        n
        for n in (
            _creator_name(c)
            for c in data.get("creators") or []
            if isinstance(c, dict)
            and c.get("creatorType", "author") in ("author", "editor", "contributor")
        )
        if n
    ]
    meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
    parsed = meta.get("parsedDate") if isinstance(meta.get("parsedDate"), str) else ""
    year = (
        parsed[:4]
        if parsed[:4].isdigit()
        else (re.search(r"\b(1[5-9]|20)\d{2}\b", text("date")) or [""])[0]
    )
    library = raw.get("library") if isinstance(raw.get("library"), dict) else {}
    group_id = (
        library.get("id")
        if library.get("type") == "group" and isinstance(library.get("id"), int)
        else None
    )
    url = text("url", 2048)
    doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:)", "", text("DOI", 200), flags=re.I)
    tags = [
        normalize_tag(t["tag"])
        for t in data.get("tags") or []
        if isinstance(t, dict) and isinstance(t.get("tag"), str)
    ]
    return ZoteroItem(
        key=key,
        title=text("title", 500) or "Untitled",
        item_type=text("itemType", 60),
        creators=creators[:30],
        year=year,
        publication=text("publicationTitle") or text("bookTitle") or text("publisher"),
        doi=doi if re.fullmatch(r"10\.\d{4,9}/\S+", doi) else "",
        url=url if url.lower().startswith(("http://", "https://")) else "",
        abstract=text("abstractNote", 4000),
        tags=[t for t in tags if t][:50],
        group_id=group_id,
    )


class ZoteroClient:
    """Read-only client for Zotero's local API on this computer."""

    def __init__(self, port: int = DEFAULT_PORT, timeout: float = 6.0):
        if not 1 <= int(port) <= 65535:
            raise ValueError("Invalid port")
        self.base = f"http://127.0.0.1:{int(port)}/api/users/0"
        self.timeout = timeout
        self._opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({})
        )  # never use a proxy

    def _get(self, path: str, params: dict | None = None):
        url = self.base + path + ("?" + urllib.parse.urlencode(params) if params else "")
        request = urllib.request.Request(
            url, headers={"Accept": "application/json", "Zotero-API-Version": "3"}
        )
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                body = response.read(MAX_RESPONSE + 1)
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                raise ZoteroError(
                    "Zotero refused the request. In Zotero, open Settings ▸ Advanced and turn on "
                    "“Allow other applications on this computer to communicate with Zotero”."
                ) from exc
            if exc.code == 404:
                raise ZoteroError(
                    "This Zotero version has no local API. Update to Zotero 7 or later."
                ) from exc
            raise ZoteroError(f"Zotero answered with an error ({exc.code}).") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise ZoteroError(
                "Could not reach Zotero. Make sure Zotero 7 or later is running."
            ) from exc
        if len(body) > MAX_RESPONSE:
            raise ZoteroError("Zotero sent too much data.")
        try:
            return json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise ZoteroError("Zotero sent an unexpected response.") from exc

    def search(self, query: str, limit: int = 25) -> list[ZoteroItem]:
        params = {"limit": max(1, min(int(limit), 100)), "qmode": "titleCreatorYear"}
        if query.strip():
            params["q"] = query.strip()[:200]
        else:
            params.update({"sort": "dateModified", "direction": "desc"})
        data = self._get("/items/top", params)
        if not isinstance(data, list):
            raise ZoteroError("Zotero sent an unexpected response.")
        return [item for item in (parse_item(raw) for raw in data) if item is not None]

    def pdf_attachment(self, key: str) -> str | None:
        """Key of the first PDF attached to *key* (open-pdf links need the attachment's key)."""
        if not ZOTERO_KEY_RE.fullmatch(key or ""):
            return None
        children = self._get(f"/items/{key}/children")
        for child in children if isinstance(children, list) else []:
            data = child.get("data") if isinstance(child, dict) else None
            if (
                isinstance(data, dict)
                and data.get("contentType") == "application/pdf"
                and isinstance(data.get("key"), str)
                and ZOTERO_KEY_RE.fullmatch(data["key"])
            ):
                return data["key"]
        return None


def citation_markdown(item: ZoteroItem) -> str:
    """Inline citation that opens the item in Zotero."""
    label = re.sub(r"[\[\]]", "", item.short_citation())
    return f"[{label}]({item.select_url})"


def literature_note(
    item: ZoteroItem, pdf_key: str | None = None
) -> tuple[str, str, list[str], str]:
    """(title, body, tags, source link) for a new literature note about *item*."""
    lines = [f"**Reference:** {item.reference()}", ""]
    links = [f"[Open in Zotero]({item.select_url})"]
    if pdf_key:
        links.append(f"[Open PDF]({pdf_url(pdf_key, group_id=item.group_id)})")
    if item.doi:
        links.append(f"[DOI](https://doi.org/{urllib.parse.quote(item.doi, safe='/')})")
    lines += [" · ".join(links), ""]
    if item.abstract:
        lines += ["> " + item.abstract.replace("\n", "\n> "), ""]
    lines += ["## Key ideas", "", "- ", "", "## My thoughts", "", ""]
    tags = ["literature"] + [t for t in item.tags if t != "literature"]
    return item.title, "\n".join(lines), tags, item.select_url
