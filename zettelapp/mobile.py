"""Qt-free facade over the core, for the Android shell (Chaquopy calls this).

The Android front door is a native Kotlin/Compose screen backed by the same
core the desktop app uses: storage, models, rendering and security. This
module keeps the surface small and JSON-friendly (dicts, lists, str, int,
bool), because Chaquopy maps exactly those between Python and Kotlin.

Heavy optional features that need wheels which do not exist on Android yet
(numpy/scikit search, onnxruntime embeddings, PySide6) stay desktop-only and
are simply absent from this facade.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

from zettelapp import APP_NAME, __version__
from zettelapp.core.models import Link, Note
from zettelapp.core.storage import Vault
from zettelapp.core.textutil import cloze_back, cloze_front
from zettelapp.paths import documents_dir, local_data_dir

_vault: Vault | None = None
_PREF_NAME = "mobile-vault.json"
log = logging.getLogger(__name__)


def _pref_path() -> Path:
    return local_data_dir() / _PREF_NAME


def _saved_vault_path() -> Path | None:
    try:
        data = json.loads(_pref_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    path = data.get("vault") if isinstance(data, dict) else None
    return Path(path) if path else None


def _remember_vault(folder: Path) -> None:
    try:
        path = _pref_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"vault": str(folder)}), encoding="utf-8")
    except OSError:
        pass  # a lost preference only costs the vault choice on the next start


def _candidates() -> list[Path]:
    folders = [documents_dir() / APP_NAME]
    saved = _saved_vault_path()
    if saved:
        folders.insert(0, saved)
    return folders


def _ensure_vault() -> Vault:
    global _vault
    if _vault is not None:
        return _vault
    errors: list[str] = []
    for folder in _candidates():
        try:
            fresh = not Vault.is_vault(folder)
            _vault = Vault.open(folder, create=True)
            if fresh:  # like the desktop app: only a vault being created, not an emptied one
                _seed_new_vault(_vault)
            _remember_vault(folder)
            return _vault
        except (OSError, RuntimeError, sqlite3.Error) as exc:
            errors.append(f"{folder}: {exc}")
    raise RuntimeError("No writable vault location found (" + "; ".join(errors) + ")")


def _seed_new_vault(vault: Vault) -> None:
    """Fill a new vault with the starter notes, in the interface language."""
    try:
        from zettelapp.core.starter import create_starter_notes

        create_starter_notes(vault)
    except Exception:  # the vault works without them; never block opening it
        log.exception("Could not write the starter notes")


def open_default_vault() -> dict:
    """Open (creating if needed) the default or last-used vault. JSON-friendly."""
    vault = _ensure_vault()
    return {"path": str(vault.folder), "notes": vault.count_notes()}


def _summary(note: Note) -> dict:
    return {
        "id": note.id,
        "title": note.title,
        "modified": note.modified,
        "tags": note.tags,
    }


def list_notes(limit: int = 500) -> list[dict]:
    """Most recently modified notes, for the list screen."""
    notes = [n for n in _ensure_vault().all_notes() if not n.deleted]
    notes.sort(key=lambda n: n.modified or n.created, reverse=True)
    return [_summary(n) for n in notes[: max(1, limit)]]


def read_note(note_id: str) -> dict:
    note = _ensure_vault().get_note(note_id)
    if note is None:
        return {"error": "not_found", "id": note_id}
    return {
        "id": note.id,
        "title": note.title,
        "body": note.body,
        "tags": note.tags,
        "url": note.url,
        "created": note.created,
        "modified": note.modified,
    }


def save_note(note_id: str, title: str, body: str, tags: list[str] | None = None) -> dict:
    vault = _ensure_vault()
    note = vault.get_note(note_id)
    if note is None:
        return {"error": "not_found", "id": note_id}
    note.title = title
    note.body = body
    if tags is not None:
        saved = vault.save_note(note, manual_tags=tags)
    else:
        saved = vault.save_note(note)
    return _summary(saved)


def create_note(title: str = "", body: str = "") -> dict:
    note = _ensure_vault().create_note(title=title, body=body)
    return _summary(note)


def trash_note(note_id: str) -> dict:
    _ensure_vault().trash_note(note_id)
    return {"ok": True}


def trashed_notes() -> list[dict]:
    """Notes in the trash, for a trash screen."""
    notes = [n for n in _ensure_vault().all_notes(include_deleted=True) if n.deleted]
    notes.sort(key=lambda n: n.modified or n.created, reverse=True)
    return [_summary(n) for n in notes]


def restore_note(note_id: str) -> dict:
    _ensure_vault().restore_note(note_id)
    return {"ok": True}


def empty_trash() -> dict:
    removed = _ensure_vault().empty_trash()
    return {"removed": removed}


def search_notes(query: str) -> list[dict]:
    """Notes matching a query (supports `tag:name` filters), for search-as-you-type."""
    vault = _ensure_vault()
    if not query.strip():
        return list_notes()
    ids = vault.search(query)
    found = vault.notes_by_ids(ids)
    found.sort(key=lambda n: n.modified or n.created, reverse=True)
    return [_summary(n) for n in found]


def all_tags() -> list[dict]:
    return [{"tag": tag, "count": count} for tag, count in _ensure_vault().all_tags()]


def note_details(note_id: str) -> dict:
    """Links, backlinks and flashcards attached to a note. JSON-friendly."""
    vault = _ensure_vault()
    note = vault.get_note(note_id)
    if note is None:
        return {"error": "not_found", "id": note_id}
    titles = vault.titles()
    type_map = {lt.id: lt for lt in vault.link_types()}

    def link_dict(link, outgoing: bool) -> dict:
        lt = type_map.get(link.type)
        other = link.dst if outgoing else link.src
        return {
            "id": other,
            "title": titles.get(other, other),
            "type": link.type,
            "label": lt.label_for(outgoing) if lt else link.type,
            "color": lt.color if lt else "#898781",
        }

    cards = vault.cards_for(note_id)
    outgoing = vault.links_from(note_id)
    # Both notes naming each other with an undirected type is one link: list it once.
    mutual = {
        (l.dst, l.type) for l in outgoing if l.type in type_map and not type_map[l.type].directed
    }
    incoming = [l for l in vault.links_to(note_id) if (l.src, l.type) not in mutual]
    return {
        "links": [link_dict(l, True) for l in outgoing],
        "backlinks": [link_dict(l, False) for l in incoming],
        "cards": [{"id": c.id, "front": c.front, "back": c.back} for c in cards],
    }


def add_link(src: str, dst: str, link_type: str = "related") -> dict:
    _ensure_vault().add_link(src, dst, link_type)
    return {"ok": True}


def remove_link(src: str, dst: str, link_type: str | None = None) -> dict:
    _ensure_vault().remove_link(src, dst, link_type)
    return {"ok": True}


def link_types() -> list[dict]:
    return [
        {
            "id": lt.id,
            "label": lt.label,
            "color": lt.color,
            "directed": lt.directed,
        }
        for lt in _ensure_vault().link_types()
    ]


def insights() -> dict:
    """Stats for the Insights dashboard. JSON-friendly."""
    from datetime import date

    vault = _ensure_vault()
    notes = [n for n in vault.all_notes() if not n.deleted]
    links = vault.all_links()
    tags = vault.all_tags()
    card_total = sum(vault.card_counts().values())
    due_count = len(vault.due_cards())
    linked_ids = set()
    for l in links:
        linked_ids.add(l.src)
        linked_ids.add(l.dst)
    unlinked = sum(1 for n in notes if n.id not in linked_ids)

    today = date.today()
    months: list[dict] = []
    for back in range(11, -1, -1):
        m = today.month - back
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        label = date(y, m, 1).strftime("%b")
        count = sum(1 for n in notes if (n.created or "")[:7] == f"{y:04d}-{m:02d}")
        months.append({"label": label, "count": count})

    type_counts: dict[str, int] = {}
    for l in links:
        type_counts[l.type] = type_counts.get(l.type, 0) + 1
    type_map = {lt.id: lt for lt in vault.link_types()}
    by_type = [
        {
            "type": t,
            "label": type_map[t].label if t in type_map else t,
            "color": type_map[t].color if t in type_map else "#898781",
            "count": c,
        }
        for t, c in sorted(type_counts.items(), key=lambda kv: -kv[1])
    ]

    return {
        "notes": len(notes),
        "links": len(links),
        "tags": len(tags),
        "unlinked": unlinked,
        "cards": card_total,
        "due": due_count,
        "months": months,
        "top_tags": [{"tag": t, "count": c} for t, c in tags[:9]],
        "links_by_type": by_type,
    }


def review_deck() -> dict:
    """Cards due for review today, with their note titles."""
    vault = _ensure_vault()
    titles = vault.titles()
    due = vault.due_cards()
    return {
        "due": len(due),
        "total": sum(vault.card_counts().values()),
        "cards": [
            {
                "id": c.id,
                "note_id": c.note_id,
                "note_title": titles.get(c.note_id, c.note_id),
                # A cloze shows its blanks on the front and the filled-in text on the back
                # (plain text: the review screen doesn't render Markdown).
                "front": cloze_front(c.front) if c.kind == "cloze" else c.front,
                "back": cloze_back(c.front) if c.kind == "cloze" else c.back,
                "kind": c.kind,
            }
            for c in due
        ],
    }


def grade_card(card_id: int, grade: int) -> dict:
    """Record a review; grade: 0 = again, 1 = good, 2 = easy. Simple SM-2 style."""
    from datetime import date, timedelta

    vault = _ensure_vault()
    state = vault.review_state(card_id)
    state.reps += 1
    if grade == 0:
        state.lapses += 1
        state.ease = max(1.3, state.ease - 0.2)
        state.interval = 1
    else:
        if state.interval == 0:
            state.interval = 1 if grade == 1 else 3
        elif state.interval == 1:
            state.interval = 6
        else:
            state.interval = round(state.interval * state.ease)
            if grade == 2:
                state.interval = round(state.interval * 1.3)
        state.ease = min(3.0, state.ease + 0.1)
    state.due = (date.today() + timedelta(days=state.interval)).isoformat()
    vault.save_review(state)
    return {"interval": state.interval, "due": state.due}


def status() -> dict:
    vault = _vault
    return {
        "app": APP_NAME,
        "version": __version__,
        "vault": str(vault.folder) if vault else "",
        "notes": vault.count_notes() if vault else 0,
    }


def close_vault() -> None:
    """Release the vault (called when the shell pauses or for tests)."""
    global _vault
    if _vault is not None:
        _vault.close()
        _vault = None


def get_graph() -> dict:
    vault = _ensure_vault()
    notes = [
        {"id": n.id, "title": n.title, "tags": n.tags} for n in vault.all_notes() if not n.deleted
    ]
    undirected = {lt.id for lt in vault.link_types() if not lt.directed}
    edges = [
        {"src": l.src, "dst": l.dst, "type": l.type}
        for l in _merge_reciprocal(vault.all_links(), undirected)
    ]
    return {"notes": notes, "edges": edges}


def _merge_reciprocal(links: list[Link], undirected: set[str]) -> list[Link]:
    """Each undirected link once (core.graph has the same, but imports numpy)."""
    seen: set[tuple[str, frozenset[str]]] = set()
    out = []
    for link in links:
        key = (link.type, frozenset((link.src, link.dst)))
        if link.type in undirected:
            if key in seen:
                continue
            seen.add(key)
        out.append(link)
    return out


def get_quest_info() -> dict:
    return {
        "title": "The Lost Prince of the Archive",
        "description": "An optional adventure that teaches ZettelApp. Explore notes, links, tags, and the knowledge graph.",
        "chapters": [
            {
                "num": 1,
                "title": "Welcome to ZettelApp",
                "clue": "Open the Welcome note and follow the first link.",
            },
            {
                "num": 2,
                "title": "One idea per note",
                "clue": "Create a new atomic note about your own idea.",
            },
            {
                "num": 3,
                "title": "Link with a reason",
                "clue": "Write a typed link connecting your notes.",
            },
            {
                "num": 4,
                "title": "Tags gather notes",
                "clue": "Add a tag like #idea to group your notes.",
            },
            {
                "num": 5,
                "title": "The graph and Insights",
                "clue": "Explore the knowledge graph view.",
            },
        ],
    }
