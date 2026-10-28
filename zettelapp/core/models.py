"""Plain data objects shared between storage, the engine and the UI."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from zettelapp.i18n import N_


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


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


# How a link type is drawn. Dashes are a second cue besides colour (for colour-blind
# readers and print), so the built-in types don't share one style.
LINE_STYLES = ("solid", "dashed", "dotted", "dash_dot", "dash_dot_dot", "long_dash")
# What each style looks like: dash and gap lengths in line widths, measured with round
# caps (so 0 is a round dot). Every renderer draws the same pattern.
DASH_PATTERNS: dict[str, tuple[float, ...]] = {
    "solid": (),
    "dashed": (4, 2.5),
    "dotted": (0, 2.5),
    "dash_dot": (4, 2.5, 0, 2.5),
    "dash_dot_dot": (4, 2.5, 0, 2.5, 0, 2.5),
    "long_dash": (9, 3),
}
# The tip at the target end of a directed link; undirected links have none.
ARROW_TIPS = ("triangle", "open", "diamond", "circle", "bar")
# Before schema 3 a type's dash followed its place in the list, cycling through these,
# and every arrow was open.
LEGACY_LINE_STYLES = ("solid", "dashed", "dotted", "dash_dot", "dash_dot_dot")
LEGACY_ARROW = "open"


@dataclass
class LinkType:
    id: str
    label: str
    inverse_label: str
    color: str
    directed: bool = True
    builtin: bool = False
    line_style: str = "solid"
    arrow: str = "triangle"

    def label_for(self, outgoing: bool) -> str:
        return self.label if outgoing or not self.directed else self.inverse_label

    @property
    def tip(self) -> str | None:
        """The arrow tip drawn at the target, or None for an undirected type."""
        return self.arrow if self.directed else None


def stroke_dashes(line_style: str) -> list[float]:
    """The style's pattern as a pen with round caps takes it, in line widths: each cap
    adds half a width to both ends of a dash, so dashes are drawn shorter and gaps longer.
    Empty for a solid line."""
    pattern = DASH_PATTERNS.get(line_style, ())
    return [max(v - 1, 0.01) if i % 2 == 0 else v + 1 for i, v in enumerate(pattern)]


def least_used_line_style(types: list[LinkType]) -> str:
    """A line style for a new link type: the one the fewest existing types use."""
    used = [t.line_style for t in types]
    return min(LINE_STYLES, key=used.count)


# Names are stored in the vault when it is created, in the interface language.
DEFAULT_LINK_TYPES = [
    LinkType(
        "related", N_("Related to"), N_("Related to"), "#898781", directed=False, builtin=True
    ),
    LinkType(
        "supports",
        N_("Supports"),
        N_("Supported by"),
        "#008300",
        builtin=True,
        line_style="dashed",
    ),
    LinkType(
        "contradicts",
        N_("Contradicts"),
        N_("Contradicts"),
        "#E34948",
        directed=False,
        builtin=True,
        line_style="dotted",
    ),
    LinkType(
        "extends",
        N_("Extends"),
        N_("Extended by"),
        "#2A78D6",
        builtin=True,
        line_style="dash_dot",
    ),
    LinkType(
        "example",
        N_("Example of"),
        N_("Has example"),
        "#EDA100",
        builtin=True,
        line_style="dash_dot_dot",
        arrow="circle",
    ),
    LinkType(
        "part_of",
        N_("Part of"),
        N_("Contains"),
        "#6250D6",
        builtin=True,
        line_style="long_dash",
        arrow="diamond",
    ),
    LinkType("cites", N_("Cites"), N_("Cited by"), "#1BAF7A", builtin=True, arrow="open"),
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


def sanitize_mindmap(data: Any, *, strict: bool = False) -> dict[str, Any] | None:
    """Return a clean copy of a mind map tree, or None if it is unusable."""
    from zettelapp.core.security import UnsafeInputError, is_valid_note_id

    count = 0

    def invalid(message: str) -> None:
        if strict:
            raise UnsafeInputError(message)

    def clean(node: Any, depth: int) -> dict[str, Any] | None:
        nonlocal count
        if not isinstance(node, dict):
            invalid("A mind map node must be an object.")
            return None
        if depth > MAX_MINDMAP_DEPTH:
            invalid(f"A mind map cannot be deeper than {MAX_MINDMAP_DEPTH} levels.")
            return None
        if count >= MAX_MINDMAP_NODES:
            invalid(f"A mind map cannot contain more than {MAX_MINDMAP_NODES} nodes.")
            return None
        count += 1
        out = new_mindmap_node(str(node.get("text", ""))[:500])
        if isinstance(node.get("id"), str) and node["id"].isalnum() and len(node["id"]) <= 32:
            out["id"] = node["id"]
        if is_valid_note_id(node.get("note")):
            out["note"] = node["note"]
        children = node.get("children") or []
        if not isinstance(children, list):
            invalid("A mind map node's children must be a list.")
            return None
        for child in children:
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
