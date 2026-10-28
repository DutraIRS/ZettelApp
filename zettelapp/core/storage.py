"""The vault: a folder holding a SQLite database and an assets directory.

All SQL uses bound parameters. Text that reaches the full-text index is
turned into quoted tokens, so user input never forms query syntax.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import sqlite3
import uuid
from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import date, datetime, timedelta
from pathlib import Path

from zettelapp.core.models import (
    DEFAULT_LINK_TYPES,
    Flashcard,
    Link,
    LinkType,
    Note,
    ReviewState,
    sanitize_mindmap,
    utc_now,
)
from zettelapp.core.security import (
    MAX_IMAGE_BYTES,
    UnsafeInputError,
    is_valid_asset_name,
    is_valid_note_id,
    normalize_source_url,
    sniff_image_type,
)
from zettelapp.core.textutil import (
    extract_hashtags,
    extract_inline_cards,
    find_wikilinks,
    fold,
    normalize_tag,
    slugify_type,
)

SCHEMA_VERSION = 2  # 2: tags.source tells tags added by hand from #tags written in the text
MAX_TITLE = 500
MAX_BODY = 5_000_000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    image TEXT NOT NULL DEFAULT '',
    mindmap TEXT,
    created TEXT NOT NULL,
    modified TEXT NOT NULL,
    deleted INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS tags (
    note_id TEXT NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    PRIMARY KEY (note_id, tag)
);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
CREATE TABLE IF NOT EXISTS link_types (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    inverse_label TEXT NOT NULL,
    color TEXT NOT NULL,
    directed INTEGER NOT NULL DEFAULT 1,
    builtin INTEGER NOT NULL DEFAULT 0,
    position INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS links (
    src TEXT NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    dst TEXT NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    type TEXT NOT NULL DEFAULT 'related',
    origin TEXT NOT NULL DEFAULT 'manual',
    created TEXT NOT NULL,
    PRIMARY KEY (src, dst, type)
);
CREATE INDEX IF NOT EXISTS idx_links_dst ON links(dst);
CREATE TABLE IF NOT EXISTS assets (
    name TEXT PRIMARY KEY,
    original_name TEXT NOT NULL,
    size INTEGER NOT NULL,
    created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id TEXT NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    front TEXT NOT NULL,
    back TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL DEFAULT 'basic',
    source TEXT NOT NULL DEFAULT 'manual',
    anki_note_id INTEGER
);
CREATE INDEX IF NOT EXISTS idx_cards_note ON flashcards(note_id);
CREATE TABLE IF NOT EXISTS reviews (
    card_id INTEGER PRIMARY KEY REFERENCES flashcards(id) ON DELETE CASCADE,
    ease REAL NOT NULL,
    interval INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    lapses INTEGER NOT NULL,
    due TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS suggestion_feedback (
    a TEXT NOT NULL,
    b TEXT NOT NULL,
    label INTEGER NOT NULL,
    created TEXT NOT NULL,
    PRIMARY KEY (a, b)
);
"""

_FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    note_id UNINDEXED, title, body, tags,
    tokenize = 'unicode61 remove_diacritics 2'
);
"""


class VaultError(RuntimeError):
    pass


def _pair(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a <= b else (b, a)


class Vault:
    DB_NAME = "zettel.db"
    ASSETS_DIR = "assets"

    def __init__(self, folder: Path, conn: sqlite3.Connection, readonly: bool = False):
        self.folder = folder
        self.conn = conn
        self.readonly = readonly
        self.generation = 0
        self.listeners: list[Callable[[str], None]] = []
        self.has_fts = False
        self._transaction_depth = 0
        self._pending_changes: set[str] = set()
        self._rollback_paths: set[Path] = set()

    # --- lifecycle --------------------------------------------------------

    @classmethod
    def open(cls, folder: str | Path, create: bool = True, readonly: bool = False) -> Vault:
        folder = Path(folder).resolve()
        db_path = folder / cls.DB_NAME
        if not db_path.exists():
            if readonly or not create:
                raise VaultError(f"No vault found in {folder}")
            folder.mkdir(parents=True, exist_ok=True)
        if readonly:
            conn = sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True)
        else:
            conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        vault = cls(folder, conn, readonly)
        if not readonly:
            # Rollback journal + full sync: safest choice for folders that are
            # synchronised by OneDrive or similar tools.
            conn.execute("PRAGMA journal_mode = DELETE")
            conn.execute("PRAGMA synchronous = FULL")
            vault._migrate()
            (folder / cls.ASSETS_DIR).mkdir(exist_ok=True)
        vault.has_fts = vault._table_exists("notes_fts")
        return vault

    @staticmethod
    def is_vault(folder: str | Path) -> bool:
        return (Path(folder) / Vault.DB_NAME).is_file()

    def close(self) -> None:
        self.conn.close()

    @property
    def name(self) -> str:
        return self.folder.name

    @property
    def assets_dir(self) -> Path:
        return self.folder / self.ASSETS_DIR

    def _table_exists(self, name: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?", (name,)
        ).fetchone()
        return row is not None

    def _migrate(self) -> None:
        # executescript() commits any open transaction first, so the idempotent
        # CREATE ... IF NOT EXISTS scripts run on their own; upgrades run in one transaction.
        self.conn.executescript(_SCHEMA)
        try:
            self.conn.executescript(_FTS_SCHEMA)
        except sqlite3.OperationalError:
            pass  # SQLite built without FTS5: search falls back to LIKE.
        with self.transaction():
            version = self.get_meta("schema_version")
            if version is None:
                self._set_meta("schema_version", str(SCHEMA_VERSION))
                self._set_meta("vault_id", uuid.uuid4().hex)
                self._set_meta("created", utc_now())
                for pos, lt in enumerate(DEFAULT_LINK_TYPES):
                    self._insert_link_type(lt, pos)
            elif int(version) > SCHEMA_VERSION:
                raise VaultError("This vault was created by a newer version of ZettelApp.")
            elif int(version) < 2:
                self._upgrade_to_v2()
                self._set_meta("schema_version", str(SCHEMA_VERSION))

    def _upgrade_to_v2(self) -> None:
        """Add tags.source and turn #tags already written in notes into tags."""
        columns = {r["name"] for r in self.conn.execute("PRAGMA table_info(tags)")}
        if "source" not in columns:
            self.conn.execute("ALTER TABLE tags ADD COLUMN source TEXT NOT NULL DEFAULT 'manual'")
        has_fts = self._table_exists("notes_fts")
        for row in self.conn.execute("SELECT id, body FROM notes WHERE body LIKE '%#%'").fetchall():
            self.conn.executemany(
                "INSERT OR IGNORE INTO tags (note_id, tag, source) VALUES (?, ?, 'inline')",
                [(row["id"], t) for t in extract_hashtags(row["body"])],
            )
            if has_fts:
                self.conn.execute(
                    "UPDATE notes_fts SET tags = (SELECT group_concat(tag, ' ') FROM tags "
                    "WHERE note_id = ?) WHERE note_id = ?",
                    (row["id"], row["id"]),
                )

    def get_meta(self, key: str) -> str | None:
        row = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def _set_meta(self, key: str, value: str) -> None:
        self.conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))

    @contextlib.contextmanager
    def transaction(self):
        """Commit a group of writes atomically, including nested Vault operations."""
        outermost = self._transaction_depth == 0
        if outermost:
            self.conn.execute("BEGIN")
            self._pending_changes.clear()
            self._rollback_paths.clear()
        self._transaction_depth += 1
        try:
            yield
        except BaseException:
            self._transaction_depth -= 1
            if outermost:
                self.conn.rollback()
                for path in self._rollback_paths:
                    path.unlink(missing_ok=True)
                self._pending_changes.clear()
                self._rollback_paths.clear()
            raise
        else:
            self._transaction_depth -= 1
            if outermost:
                try:
                    self.conn.commit()
                except BaseException:
                    self.conn.rollback()
                    for path in self._rollback_paths:
                        path.unlink(missing_ok=True)
                    self._pending_changes.clear()
                    self._rollback_paths.clear()
                    raise
                changes = tuple(sorted(self._pending_changes))
                self._pending_changes.clear()
                self._rollback_paths.clear()
                for kind in changes:
                    self._emit_changed(kind)

    @property
    def vault_id(self) -> str:
        return self.get_meta("vault_id") or "unknown"

    def _changed(self, kind: str) -> None:
        if self._transaction_depth:
            self._pending_changes.add(kind)
            return
        self._emit_changed(kind)

    def _emit_changed(self, kind: str) -> None:
        self.generation += 1
        for listener in list(self.listeners):
            listener(kind)

    # --- notes ------------------------------------------------------------

    def new_note_id(self, when: datetime | None = None) -> str:
        """Timestamp id (YYYYMMDDHHMMSS); on collision the next free second is used."""
        when = (when or datetime.now()).replace(microsecond=0)
        while True:
            candidate = when.strftime("%Y%m%d%H%M%S")
            if not self.conn.execute("SELECT 1 FROM notes WHERE id = ?", (candidate,)).fetchone():
                return candidate
            when += timedelta(seconds=1)

    def create_note(
        self,
        title: str = "",
        body: str = "",
        tags: Iterable[str] = (),
        url: str = "",
        note_id: str | None = None,
        created: str | None = None,
    ) -> Note:
        if note_id is not None and not is_valid_note_id(note_id):
            raise UnsafeInputError(f"Invalid note id: {note_id!r}")
        now = utc_now()
        note = Note(
            id=note_id or self.new_note_id(),
            title=title,
            body=body,
            url=url,
            tags=list(tags),
            created=created or now,
            modified=now,
        )
        with self.transaction():
            self.conn.execute(
                "INSERT INTO notes (id, created, modified) VALUES (?, ?, ?)",
                (note.id, note.created, note.modified),
            )
            self._write_note(note, touch=False)
        self._changed("notes")
        return note

    def save_note(
        self, note: Note, touch: bool = True, manual_tags: Iterable[str] | None = None
    ) -> Note:
        """Save *note*. #tags in its text become tags; *manual_tags*, when given, are the
        tags added by hand (the editor knows them), otherwise they are inferred."""
        with self.transaction():
            self._write_note(note, touch, manual_tags)
        self._changed("notes")
        return note

    def _write_note(
        self, note: Note, touch: bool, manual_tags: Iterable[str] | None = None
    ) -> None:
        note.title = (note.title or "")[:MAX_TITLE]
        note.body = (note.body or "")[:MAX_BODY]
        note.url = (normalize_source_url(note.url) or "") if note.url else ""
        note.image = note.image if is_valid_asset_name(note.image) else ""
        note.mindmap = sanitize_mindmap(note.mindmap, strict=True) if note.mindmap else None
        inline = set(extract_hashtags(note.body))
        if manual_tags is not None:
            manual = {t for t in (normalize_tag(x) for x in manual_tags) if t}
        else:
            # note.tags holds every tag when read back. A tag stays manual if it was added
            # by hand; one that came from (or is now in) the text stays derived from it, so
            # deleting #tag from the text removes the tag, like inline links and cards.
            source = {
                r["tag"]: r["source"]
                for r in self.conn.execute(
                    "SELECT tag, source FROM tags WHERE note_id = ?", (note.id,)
                )
            }
            manual = {
                t
                for t in (normalize_tag(x) for x in note.tags)
                if t and (source.get(t) == "manual" or (t not in source and t not in inline))
            }
        note.tags = sorted(manual | inline)
        if touch:
            note.modified = utc_now()
        row = self.conn.execute("SELECT title FROM notes WHERE id = ?", (note.id,)).fetchone()
        old_title = row["title"] if row else ""
        self.conn.execute(
            "UPDATE notes SET title = ?, body = ?, url = ?, image = ?, mindmap = ?, modified = ? WHERE id = ?",
            (
                note.title,
                note.body,
                note.url,
                note.image,
                json.dumps(note.mindmap, ensure_ascii=False) if note.mindmap else None,
                note.modified,
                note.id,
            ),
        )
        self.conn.execute("DELETE FROM tags WHERE note_id = ?", (note.id,))
        self.conn.executemany(
            "INSERT INTO tags (note_id, tag, source) VALUES (?, ?, ?)",
            [(note.id, t, "manual" if t in manual else "inline") for t in note.tags],
        )
        if self.has_fts:
            self.conn.execute("DELETE FROM notes_fts WHERE note_id = ?", (note.id,))
            self.conn.execute(
                "INSERT INTO notes_fts (note_id, title, body, tags) VALUES (?, ?, ?, ?)",
                (note.id, note.title, note.body, " ".join(note.tags)),
            )
        self._sync_inline_links(note)
        self._sync_inline_cards(note)
        if fold(old_title.strip()) != fold(note.title.strip()):
            self._resync_references({old_title.strip(), note.title.strip()} - {""}, note.id)

    def _resync_references(self, titles: set[str], skip: str) -> None:
        """Re-resolve [[Title]] links in other notes after a note is created or renamed."""
        for title in titles:
            pattern = (
                "%[[" + title.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            )
            rows = self.conn.execute(
                "SELECT id, body FROM notes WHERE deleted = 0 AND id != ? AND body LIKE ? ESCAPE '\\'",
                (skip, pattern),
            ).fetchall()
            for r in rows:
                self._sync_inline_links(Note(id=r["id"], body=r["body"]))

    def _row_to_note(self, row: sqlite3.Row, tags: list[str]) -> Note:
        mindmap = None
        if row["mindmap"]:
            try:
                mindmap = sanitize_mindmap(json.loads(row["mindmap"]))
            except (ValueError, TypeError):
                mindmap = None
        return Note(
            id=row["id"],
            title=row["title"],
            body=row["body"],
            url=row["url"],
            image=row["image"],
            tags=tags,
            mindmap=mindmap,
            created=row["created"],
            modified=row["modified"],
            deleted=bool(row["deleted"]),
        )

    def manual_tags(self, note_id: str) -> list[str]:
        """The note's tags that were added by hand rather than written as #tags in its text."""
        return [
            r["tag"]
            for r in self.conn.execute(
                "SELECT tag FROM tags WHERE note_id = ? AND source = 'manual' ORDER BY tag",
                (note_id,),
            )
        ]

    def get_note(self, note_id: str) -> Note | None:
        row = self.conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        if row is None:
            return None
        tags = [
            r["tag"]
            for r in self.conn.execute(
                "SELECT tag FROM tags WHERE note_id = ? ORDER BY tag", (note_id,)
            )
        ]
        return self._row_to_note(row, tags)

    def all_notes(self, include_deleted: bool = False) -> list[Note]:
        tags: dict[str, list[str]] = defaultdict(list)
        for r in self.conn.execute("SELECT note_id, tag FROM tags ORDER BY tag"):
            tags[r["note_id"]].append(r["tag"])
        sql = "SELECT * FROM notes" + ("" if include_deleted else " WHERE deleted = 0")
        return [
            self._row_to_note(r, tags.get(r["id"], []))
            for r in self.conn.execute(sql + " ORDER BY id")
        ]

    def notes_by_ids(self, ids: Iterable[str]) -> list[Note]:
        wanted = set(ids)
        return [n for n in self.all_notes(include_deleted=True) if n.id in wanted]

    def note_exists(self, note_id: str, include_deleted: bool = False) -> bool:
        sql = "SELECT 1 FROM notes WHERE id = ?" + ("" if include_deleted else " AND deleted = 0")
        return self.conn.execute(sql, (note_id,)).fetchone() is not None

    def count_notes(self, deleted: bool = False) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM notes WHERE deleted = ?", (int(deleted),)
        ).fetchone()[0]

    def titles(self) -> dict[str, str]:
        return {
            r["id"]: r["title"]
            for r in self.conn.execute("SELECT id, title FROM notes WHERE deleted = 0")
        }

    def resolve_title(self, target: str) -> str | None:
        """Note id for a wiki-link target given as an id or a title."""
        target = target.strip()
        if is_valid_note_id(target) and self.note_exists(target):
            return target
        wanted = fold(target)
        for r in self.conn.execute("SELECT id, title FROM notes WHERE deleted = 0 ORDER BY id"):
            if fold(r["title"].strip()) == wanted:
                return r["id"]
        return None

    def trash_note(self, note_id: str) -> None:
        with self.transaction():
            self.conn.execute(
                "UPDATE notes SET deleted = 1, modified = ? WHERE id = ?", (utc_now(), note_id)
            )
        self._changed("notes")

    def restore_note(self, note_id: str) -> None:
        with self.transaction():
            self.conn.execute(
                "UPDATE notes SET deleted = 0, modified = ? WHERE id = ?", (utc_now(), note_id)
            )
        self._changed("notes")

    def purge_note(self, note_id: str) -> None:
        with self.transaction():
            self.conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            self.conn.execute(
                "DELETE FROM suggestion_feedback WHERE a = ? OR b = ?", (note_id, note_id)
            )
            if self.has_fts:
                self.conn.execute("DELETE FROM notes_fts WHERE note_id = ?", (note_id,))
        self._changed("notes")

    def empty_trash(self) -> int:
        ids = [r["id"] for r in self.conn.execute("SELECT id FROM notes WHERE deleted = 1")]
        for note_id in ids:
            self.purge_note(note_id)
        return len(ids)

    # --- search -----------------------------------------------------------

    def search(self, query: str, include_deleted: bool = False) -> list[str]:
        """Ids of notes matching *query*; supports `tag:name` filters."""
        tag_filters = [normalize_tag(t) for t in re.findall(r"(?:^|\s)tag:(\S+)", query)]
        text = re.sub(r"(?:^|\s)tag:\S+", " ", query)
        tokens = re.findall(r"\w+", text)
        deleted_clause = "" if include_deleted else " AND n.deleted = 0"
        if not tokens:
            ids = [
                r["id"]
                for r in self.conn.execute(
                    "SELECT id FROM notes n WHERE 1 = 1"
                    + deleted_clause
                    + " ORDER BY modified DESC"
                )
            ]
        elif self.has_fts:
            match = " ".join(f'"{t}"*' for t in tokens)
            ids = [
                r["note_id"]
                for r in self.conn.execute(
                    "SELECT f.note_id FROM notes_fts f JOIN notes n ON n.id = f.note_id "
                    "WHERE notes_fts MATCH ?"
                    + deleted_clause
                    + " ORDER BY bm25(notes_fts, 0.0, 6.0, 1.0, 3.0) LIMIT 1000",
                    (match,),
                )
            ]
        else:
            sql = "SELECT id FROM notes n WHERE 1 = 1" + deleted_clause
            params: list[str] = []
            for t in tokens:
                like = "%" + t.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
                sql += " AND (n.title LIKE ? ESCAPE '\\' OR n.body LIKE ? ESCAPE '\\')"
                params += [like, like]
            ids = [r["id"] for r in self.conn.execute(sql + " ORDER BY modified DESC", params)]
        if tag_filters:
            tagged = self.notes_with_tags(tag_filters)
            ids = [i for i in ids if i in tagged]
        return ids

    # --- tags -------------------------------------------------------------

    def all_tags(self) -> list[tuple[str, int]]:
        return [
            (r["tag"], r["n"])
            for r in self.conn.execute(
                "SELECT t.tag, COUNT(*) AS n FROM tags t JOIN notes n ON n.id = t.note_id "
                "WHERE n.deleted = 0 GROUP BY t.tag ORDER BY t.tag"
            )
        ]

    def notes_with_tags(self, tags: Iterable[str], match_all: bool = True) -> set[str]:
        tags = [t for t in tags if t]
        if not tags:
            return set()
        sets = []
        for t in tags:
            # A tag also matches its nested children, e.g. "math" matches "math/algebra".
            sets.append(
                {
                    r["note_id"]
                    for r in self.conn.execute(
                        "SELECT note_id FROM tags WHERE tag = ? OR tag LIKE ? ESCAPE '\\'",
                        (t, t.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "/%"),
                    )
                }
            )
        return set.intersection(*sets) if match_all else set.union(*sets)

    # --- link types -------------------------------------------------------

    def _insert_link_type(self, lt: LinkType, position: int) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO link_types (id, label, inverse_label, color, directed, builtin, position) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                lt.id,
                lt.label,
                lt.inverse_label,
                lt.color,
                int(lt.directed),
                int(lt.builtin),
                position,
            ),
        )

    def link_types(self) -> list[LinkType]:
        return [
            LinkType(
                r["id"],
                r["label"],
                r["inverse_label"],
                r["color"],
                bool(r["directed"]),
                bool(r["builtin"]),
            )
            for r in self.conn.execute("SELECT * FROM link_types ORDER BY position, label")
        ]

    def link_type_map(self) -> dict[str, LinkType]:
        return {lt.id: lt for lt in self.link_types()}

    def save_link_type(self, lt: LinkType) -> LinkType:
        lt.id = slugify_type(lt.id or lt.label)
        if not lt.id:
            raise UnsafeInputError("A link type needs a name.")
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", lt.color or ""):
            lt.color = "#8A8A8A"
        lt.label = lt.label.strip()[:60] or lt.id
        lt.inverse_label = lt.inverse_label.strip()[:60] or lt.label
        existing = self.conn.execute(
            "SELECT builtin, position FROM link_types WHERE id = ?", (lt.id,)
        ).fetchone()
        position = (
            existing["position"]
            if existing
            else self.conn.execute(
                "SELECT COALESCE(MAX(position), 0) + 1 FROM link_types"
            ).fetchone()[0]
        )
        lt.builtin = bool(existing["builtin"]) if existing else False
        with self.transaction():
            self._insert_link_type(lt, position)
        self._changed("types")
        return lt

    def delete_link_type(self, type_id: str) -> None:
        if type_id == "related":
            raise VaultError("The default link type cannot be removed.")
        with self.transaction():
            # Re-type existing links; INSERT OR IGNORE avoids clashing with an existing "related" link.
            self.conn.execute(
                "INSERT OR IGNORE INTO links (src, dst, type, origin, created) "
                "SELECT src, dst, 'related', origin, created FROM links WHERE type = ?",
                (type_id,),
            )
            self.conn.execute("DELETE FROM links WHERE type = ?", (type_id,))
            self.conn.execute("DELETE FROM link_types WHERE id = ?", (type_id,))
        self._changed("types")

    def _valid_type(self, type_id: str | None) -> str:
        type_id = slugify_type(type_id or "related")
        row = self.conn.execute("SELECT 1 FROM link_types WHERE id = ?", (type_id,)).fetchone()
        return type_id if row else "related"

    # --- links ------------------------------------------------------------

    def add_link(
        self, src: str, dst: str, link_type: str = "related", origin: str = "manual"
    ) -> bool:
        if src == dst or not self.note_exists(src, True) or not self.note_exists(dst, True):
            return False
        link_type = self._valid_type(link_type)
        with self.transaction():
            cur = self.conn.execute(
                "INSERT OR IGNORE INTO links (src, dst, type, origin, created) VALUES (?, ?, ?, ?, ?)",
                (src, dst, link_type, origin, utc_now()),
            )
        self._changed("links")
        return cur.rowcount > 0

    def remove_link(self, src: str, dst: str, link_type: str | None = None) -> None:
        with self.transaction():
            if link_type is None:
                self.conn.execute("DELETE FROM links WHERE src = ? AND dst = ?", (src, dst))
            else:
                self.conn.execute(
                    "DELETE FROM links WHERE src = ? AND dst = ? AND type = ?",
                    (src, dst, link_type),
                )
        self._changed("links")

    def change_link_type(self, src: str, dst: str, old_type: str, new_type: str) -> None:
        new_type = self._valid_type(new_type)
        with self.transaction():
            self.conn.execute(
                "UPDATE OR IGNORE links SET type = ?, origin = 'manual' WHERE src = ? AND dst = ? AND type = ?",
                (new_type, src, dst, old_type),
            )
        self._changed("links")

    def reverse_link(self, src: str, dst: str, link_type: str) -> None:
        """Flip a link's direction (dst -> src), keeping its type."""
        with self.transaction():
            row = self.conn.execute(
                "SELECT origin FROM links WHERE src = ? AND dst = ? AND type = ?",
                (src, dst, link_type),
            ).fetchone()
            if row is None or row["origin"] == "inline":
                return  # links written in the text are reversed by editing the text
            self.conn.execute(
                "DELETE FROM links WHERE src = ? AND dst = ? AND type = ?", (src, dst, link_type)
            )
            self.conn.execute(
                "INSERT OR IGNORE INTO links (src, dst, type, origin, created) VALUES (?, ?, ?, 'manual', ?)",
                (dst, src, link_type, utc_now()),
            )
        self._changed("links")

    def _links(self, where: str, params: tuple) -> list[Link]:
        return [
            Link(r["src"], r["dst"], r["type"], r["origin"])
            for r in self.conn.execute(
                "SELECT l.* FROM links l JOIN notes a ON a.id = l.src JOIN notes b ON b.id = l.dst "
                "WHERE a.deleted = 0 AND b.deleted = 0" + where + " ORDER BY l.created",
                params,
            )
        ]

    def links_from(self, note_id: str) -> list[Link]:
        return self._links(" AND l.src = ?", (note_id,))

    def links_to(self, note_id: str) -> list[Link]:
        return self._links(" AND l.dst = ?", (note_id,))

    def all_links(self) -> list[Link]:
        return self._links("", ())

    def neighbors(self, note_id: str) -> set[str]:
        return {l.dst for l in self.links_from(note_id)} | {l.src for l in self.links_to(note_id)}

    def _sync_inline_links(self, note: Note) -> None:
        desired: set[tuple[str, str]] = set()
        wikilinks = find_wikilinks(note.body)
        if wikilinks:
            by_title: dict[str, str] = {}
            for r in self.conn.execute(
                "SELECT id, title FROM notes WHERE deleted = 0 ORDER BY id DESC"
            ):
                by_title[fold(r["title"].strip())] = r["id"]
            types = {r["id"] for r in self.conn.execute("SELECT id FROM link_types")}
            for wl in wikilinks:
                dst = (
                    wl.target
                    if is_valid_note_id(wl.target) and self.note_exists(wl.target, True)
                    else by_title.get(fold(wl.target))
                )
                if dst and dst != note.id:
                    desired.add(
                        (dst, wl.link_type if wl.link_type and wl.link_type in types else "related")
                    )
        existing = {
            (r["dst"], r["type"])
            for r in self.conn.execute(
                "SELECT dst, type FROM links WHERE src = ? AND origin = 'inline'", (note.id,)
            )
        }
        for dst, link_type in existing - desired:
            self.conn.execute(
                "DELETE FROM links WHERE src = ? AND dst = ? AND type = ? AND origin = 'inline'",
                (note.id, dst, link_type),
            )
        now = utc_now()
        for dst, link_type in desired - existing:
            self.conn.execute(
                "INSERT OR IGNORE INTO links (src, dst, type, origin, created) VALUES (?, ?, ?, 'inline', ?)",
                (note.id, dst, link_type, now),
            )

    # --- assets -----------------------------------------------------------

    def add_image(self, data: bytes, original_name: str = "") -> str:
        """Store image bytes content-addressed; returns the asset name."""
        if len(data) > MAX_IMAGE_BYTES:
            raise UnsafeInputError("Images larger than 25 MB are not supported.")
        ext = sniff_image_type(data)
        if ext is None:
            raise UnsafeInputError("Unsupported image format. Use PNG, JPEG, GIF, WebP or BMP.")
        name = hashlib.sha256(data).hexdigest()[:20] + "." + ext
        path = self.assets_dir / name
        with self.transaction():
            if not path.exists():
                tmp = path.with_suffix(path.suffix + ".tmp")
                tmp.write_bytes(data)
                os.replace(tmp, path)
                self._rollback_paths.add(path)
            self.conn.execute(
                "INSERT OR IGNORE INTO assets (name, original_name, size, created) VALUES (?, ?, ?, ?)",
                (name, Path(original_name).name[:200], len(data), utc_now()),
            )
        return name

    def add_image_file(self, path: str | Path) -> str:
        path = Path(path)
        if path.stat().st_size > MAX_IMAGE_BYTES:
            raise UnsafeInputError("Images larger than 25 MB are not supported.")
        return self.add_image(path.read_bytes(), path.name)

    def asset_path(self, name: str) -> Path | None:
        if not is_valid_asset_name(name):
            return None
        path = self.assets_dir / name
        return path if path.is_file() else None

    # --- flashcards -------------------------------------------------------

    @staticmethod
    def _row_to_card(r: sqlite3.Row) -> Flashcard:
        return Flashcard(
            r["id"], r["note_id"], r["front"], r["back"], r["kind"], r["source"], r["anki_note_id"]
        )

    def cards_for(self, note_id: str) -> list[Flashcard]:
        return [
            self._row_to_card(r)
            for r in self.conn.execute(
                "SELECT * FROM flashcards WHERE note_id = ? ORDER BY source DESC, id", (note_id,)
            )
        ]

    def cards_for_notes(self, note_ids: Iterable[str] | None = None) -> list[Flashcard]:
        rows = self.conn.execute(
            "SELECT c.* FROM flashcards c JOIN notes n ON n.id = c.note_id WHERE n.deleted = 0 ORDER BY c.note_id, c.id"
        )
        wanted = None if note_ids is None else set(note_ids)
        return [self._row_to_card(r) for r in rows if wanted is None or r["note_id"] in wanted]

    def card_counts(self) -> dict[str, int]:
        return {
            r["note_id"]: r["n"]
            for r in self.conn.execute(
                "SELECT note_id, COUNT(*) AS n FROM flashcards GROUP BY note_id"
            )
        }

    def save_card(self, card: Flashcard) -> Flashcard:
        card.kind = "cloze" if card.kind == "cloze" else "basic"
        with self.transaction():
            if card.id is None:
                cur = self.conn.execute(
                    "INSERT INTO flashcards (note_id, front, back, kind, source) VALUES (?, ?, ?, ?, ?)",
                    (card.note_id, card.front, card.back, card.kind, card.source),
                )
                card.id = cur.lastrowid
            else:
                self.conn.execute(
                    "UPDATE flashcards SET front = ?, back = ?, kind = ? WHERE id = ?",
                    (card.front, card.back, card.kind, card.id),
                )
        self._changed("cards")
        return card

    def delete_card(self, card_id: int) -> None:
        with self.transaction():
            self.conn.execute("DELETE FROM flashcards WHERE id = ?", (card_id,))
        self._changed("cards")

    def set_anki_note_id(self, card_id: int, anki_note_id: int | None) -> None:
        with self.transaction():
            self.conn.execute(
                "UPDATE flashcards SET anki_note_id = ? WHERE id = ?", (anki_note_id, card_id)
            )

    def _sync_inline_cards(self, note: Note) -> None:
        found = {(c.kind, c.front): c.back for c in extract_inline_cards(note.body)}
        existing = {
            (r["kind"], r["front"]): (r["id"], r["back"])
            for r in self.conn.execute(
                "SELECT id, kind, front, back FROM flashcards WHERE note_id = ? AND source = 'inline'",
                (note.id,),
            )
        }
        for key, (card_id, back) in existing.items():
            if key not in found:
                self.conn.execute("DELETE FROM flashcards WHERE id = ?", (card_id,))
            elif found[key] != back:
                self.conn.execute(
                    "UPDATE flashcards SET back = ? WHERE id = ?", (found[key], card_id)
                )
        for (kind, front), back in found.items():
            if (kind, front) not in existing:
                self.conn.execute(
                    "INSERT INTO flashcards (note_id, front, back, kind, source) VALUES (?, ?, ?, ?, 'inline')",
                    (note.id, front, back, kind),
                )

    # --- spaced repetition state -----------------------------------------

    def review_state(self, card_id: int) -> ReviewState:
        r = self.conn.execute("SELECT * FROM reviews WHERE card_id = ?", (card_id,)).fetchone()
        if r is None:
            return ReviewState(card_id)
        return ReviewState(card_id, r["ease"], r["interval"], r["reps"], r["lapses"], r["due"])

    def save_review(self, state: ReviewState) -> None:
        with self.transaction():
            self.conn.execute(
                "INSERT OR REPLACE INTO reviews (card_id, ease, interval, reps, lapses, due) VALUES (?, ?, ?, ?, ?, ?)",
                (state.card_id, state.ease, state.interval, state.reps, state.lapses, state.due),
            )
        self._changed("reviews")

    def due_cards(
        self, today: date | None = None, note_ids: Iterable[str] | None = None
    ) -> list[Flashcard]:
        today_s = (today or date.today()).isoformat()
        due_ids = {
            r["id"]
            for r in self.conn.execute(
                "SELECT c.id FROM flashcards c LEFT JOIN reviews r ON r.card_id = c.id "
                "WHERE r.card_id IS NULL OR r.due <= ?",
                (today_s,),
            )
        }
        return [c for c in self.cards_for_notes(note_ids) if c.id in due_ids]

    # --- link-suggestion feedback ----------------------------------------

    def record_feedback(self, a: str, b: str, label: int) -> None:
        a, b = _pair(a, b)
        with self.transaction():
            self.conn.execute(
                "INSERT OR REPLACE INTO suggestion_feedback (a, b, label, created) VALUES (?, ?, ?, ?)",
                (a, b, int(bool(label)), utc_now()),
            )
        self._changed("feedback")

    def feedback(self) -> dict[tuple[str, str], int]:
        return {
            (r["a"], r["b"]): r["label"]
            for r in self.conn.execute("SELECT a, b, label FROM suggestion_feedback")
        }

    def reset_feedback(self) -> None:
        with self.transaction():
            self.conn.execute("DELETE FROM suggestion_feedback")
        self._changed("feedback")

    # --- backups ----------------------------------------------------------

    def backup(self, dest_dir: Path, keep: int = 10) -> Path:
        """Write a consistent copy of the database and prune old copies."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"zettel-{datetime.now():%Y%m%d-%H%M%S}.db"
        out = sqlite3.connect(dest)
        try:
            self.conn.backup(out)
        finally:
            out.close()
        backups = sorted(dest_dir.glob("zettel-*.db"))
        for old in backups[:-keep] if keep > 0 else []:
            with contextlib.suppress(OSError):
                old.unlink()
        return dest

    @staticmethod
    def last_backup_date(dest_dir: Path) -> date | None:
        backups = sorted(dest_dir.glob("zettel-*.db"))
        if not backups:
            return None
        try:
            return datetime.strptime(backups[-1].stem[7:15], "%Y%m%d").date()
        except ValueError:
            return None
