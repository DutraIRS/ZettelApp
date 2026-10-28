"""Plain data objects shared between storage, the engine and the UI."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Note:
    id: str
    title: str = ""
    body: str = ""
    url: str = ""
    image: str = ""  # asset file name shown as the note's picture (optional)
    tags: list[str] = field(default_factory=list)
    mindmap: dict[str, Any] | None = None
    created: str = ""
    modified: str = ""
    deleted: bool = False

    @property
    def display_title(self) -> str:
        return self.title.strip() or "Untitled"


@dataclass(frozen=True)
class Link:
    src: str
    dst: str
    type: str = "related"
    origin: str = "manual"  # manual | inline | suggestion


@dataclass
class LinkType:
    id: str
    label: str
    inverse_label: str
    color: str
    directed: bool = True
    builtin: bool = False

    def label_for(self, outgoing: bool) -> str:
        return self.label if outgoing or not self.directed else self.inverse_label


DEFAULT_LINK_TYPES = [
    LinkType("related", "Related to", "Related to", "#898781", directed=False, builtin=True),
    LinkType("supports", "Supports", "Supported by", "#008300", builtin=True),
    LinkType("contradicts", "Contradicts", "Contradicts", "#E34948", directed=False, builtin=True),
    LinkType("extends", "Extends", "Extended by", "#2A78D6", builtin=True),
    LinkType("example", "Example of", "Has example", "#EDA100", builtin=True),
    LinkType("part_of", "Part of", "Contains", "#6250D6", builtin=True),
    LinkType("cites", "Cites", "Cited by", "#1BAF7A", builtin=True),
]


@dataclass
class Flashcard:
    id: int | None
    note_id: str
    front: str
    back: str = ""
    kind: str = "basic"  # basic | cloze
    source: str = "manual"  # manual | inline
    anki_note_id: int | None = None


@dataclass
class ReviewState:
    card_id: int
    ease: float = 2.5
    interval: int = 0
    reps: int = 0
    lapses: int = 0
    due: str = ""  # ISO date; empty means new


# --- mind maps --------------------------------------------------------------

MAX_MINDMAP_NODES = 2000
MAX_MINDMAP_DEPTH = 40


def new_mindmap_node(text: str = "", note: str | None = None) -> dict[str, Any]:
    node: dict[str, Any] = {"id": uuid.uuid4().hex[:12], "text": text, "children": []}
    if note:
        node["note"] = note
    return node


def sanitize_mindmap(data: Any) -> dict[str, Any] | None:
    """Return a clean copy of a mind map tree, or None if it is unusable."""
    from zettelapp.core.security import is_valid_note_id

    count = 0

    def clean(node: Any, depth: int) -> dict[str, Any] | None:
        nonlocal count
        if not isinstance(node, dict) or depth > MAX_MINDMAP_DEPTH or count >= MAX_MINDMAP_NODES:
            return None
        count += 1
        out = new_mindmap_node(str(node.get("text", ""))[:500])
        if isinstance(node.get("id"), str) and node["id"].isalnum() and len(node["id"]) <= 32:
            out["id"] = node["id"]
        if is_valid_note_id(node.get("note")):
            out["note"] = node["note"]
        for child in node.get("children") or []:
            c = clean(child, depth + 1)
            if c is not None:
                out["children"].append(c)
        return out

    return clean(data, 0)


def mindmap_nodes(root: dict[str, Any]):
    """Depth-first iteration yielding (node, depth)."""
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        yield node, depth
        for child in reversed(node.get("children", [])):
            stack.append((child, depth + 1))
