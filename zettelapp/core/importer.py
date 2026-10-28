"""Import ZettelApp archives/JSON and Markdown folders (e.g. Obsidian vaults).

Imported files are untrusted: archive paths are validated (no zip-slip),
sizes are bounded, every field is type-checked, and images are re-verified
by content before they are stored. Each import runs in one vault transaction,
so an import that fails leaves the vault unchanged.
"""

from __future__ import annotations

import json
import re
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import yaml

from zettelapp.core.models import (
    ARROW_TIPS,
    LINE_STYLES,
    MAX_MINDMAP_DEPTH,
    MAX_MINDMAP_NODES,
    Flashcard,
    LinkType,
    Note,
    least_used_line_style,
    sanitize_mindmap,
)
from zettelapp.core.security import (
    MAX_IMAGE_BYTES,
    UnsafeInputError,
    check_zip,
    is_valid_asset_name,
    is_valid_note_id,
    resolve_inside,
    safe_member_path,
)
from zettelapp.core.storage import MAX_BODY, MAX_TITLE, Vault
from zettelapp.core.textutil import WIKILINK_RE, fold, normalize_tag
from zettelapp.i18n import _

MAX_JSON_BYTES = 300 * 1024 * 1024
MAX_MARKDOWN_FILES = 20_000
MAX_MARKDOWN_BYTES = 5 * 1024 * 1024

_FRONT_MATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
_HEADING_RE = re.compile(r"^#\s+(.+)$", re.M)
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(<?([^)>\s]+)>?(?:\s+\"[^\"]*\")?\)")
_EMBED_RE = re.compile(r"!\[\[([^\]|]+?\.(?:png|jpe?g|gif|webp|bmp))(?:\|[^\]]*)?\]\]", re.I)
_ASSET_REF_RE = re.compile(r"asset:([0-9a-f]{20}\.(?:png|jpg|gif|webp|bmp))")


@dataclass
class ImportResult:
    notes: int = 0
    links: int = 0
    cards: int = 0
    images: int = 0
    skipped: int = 0
    warnings: list[str] = field(default_factory=list)

    def warn(self, message: str) -> None:
        if len(self.warnings) < 50:
            self.warnings.append(message)


def import_path(vault: Vault, path: str | Path) -> ImportResult:
    path = Path(path)
    if path.is_dir():
        return import_markdown_folder(vault, path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        if path.stat().st_size > MAX_JSON_BYTES:
            raise UnsafeInputError("The file is too large to import.")
        return import_data(vault, json.loads(path.read_text(encoding="utf-8")))
    if suffix == ".md":
        result = ImportResult()
        with vault.transaction():
            _import_markdown_files(vault, path.parent, [path], result)
        return result
    if suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            check_zip(zf)
            names = zf.namelist()
            if "manifest.json" in names:
                return _import_archive(vault, zf)
            if any(n.lower().endswith(".md") for n in names):
                with tempfile.TemporaryDirectory(prefix="zettelapp-import-") as tmp:
                    _extract(zf, Path(tmp))
                    return import_markdown_folder(vault, Path(tmp))
        raise UnsafeInputError(
            "This archive contains neither a ZettelApp export nor Markdown files."
        )
    raise UnsafeInputError(f"Unsupported file type: {suffix or path.name}")


def _extract(zf: zipfile.ZipFile, dest: Path) -> None:
    for info in zf.infolist():
        if info.is_dir():
            continue
        member = safe_member_path(info.filename)
        target = resolve_inside(dest, str(member))
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info) as src, open(target, "wb") as out:
            out.write(src.read(info.file_size + 1)[: info.file_size])


# --- ZettelApp archive / JSON -----------------------------------------------


def _import_archive(vault: Vault, zf: zipfile.ZipFile) -> ImportResult:
    info = zf.getinfo("manifest.json")
    if info.file_size > MAX_JSON_BYTES:
        raise UnsafeInputError("The archive manifest is too large.")
    data = json.loads(zf.read(info).decode("utf-8"))
    _validate_import_data(data)
    asset_map: dict[str, str] = {}
    result = ImportResult()
    with vault.transaction():
        for name in data.get("assets", []):
            if not is_valid_asset_name(name):
                continue
            try:
                member = zf.getinfo(f"assets/{name}")
            except KeyError:
                result.warn(f"Missing image {name}")
                continue
            if member.file_size > MAX_IMAGE_BYTES:
                result.warn(f"Skipped oversized image {name}")
                continue
            try:
                asset_map[name] = vault.add_image(zf.read(member), name)
                result.images += 1
            except UnsafeInputError as exc:
                result.warn(f"Skipped image {name}: {exc}")
        return _import_data(vault, data, asset_map, result)


def _str(value, limit: int) -> str:
    return value[:limit] if isinstance(value, str) else ""


def _timestamp(value) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if isinstance(value, date):  # YAML turns bare dates into date objects
        return (
            datetime(value.year, value.month, value.day).astimezone().isoformat(timespec="seconds")
        )
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat(timespec="seconds")
    except ValueError:
        return None


def _validate_mindmap(data) -> None:
    count = 0
    stack = [(data, 0)]
    while stack:
        node, depth = stack.pop()
        if not isinstance(node, dict):
            raise UnsafeInputError("A mind map node must be an object.")
        if depth > MAX_MINDMAP_DEPTH:
            raise UnsafeInputError(f"A mind map cannot be deeper than {MAX_MINDMAP_DEPTH} levels.")
        count += 1
        if count > MAX_MINDMAP_NODES:
            raise UnsafeInputError(
                f"A mind map cannot contain more than {MAX_MINDMAP_NODES} nodes."
            )
        children = node.get("children", [])
        if children is None:
            children = []
        if not isinstance(children, list):
            raise UnsafeInputError("A mind map node's children must be a list.")
        stack.extend((child, depth + 1) for child in children)


def _validate_link_style(raw: dict) -> None:
    """A link type's line style and arrow tip may be missing (older exports) but not
    unknown."""
    name = str(raw.get("id"))[:40]
    for key, allowed, message in (
        ("line_style", LINE_STYLES, _("Link type “{name}” has an unknown line style: {value}")),
        ("arrow", ARROW_TIPS, _("Link type “{name}” has an unknown arrow tip: {value}")),
    ):
        value = raw.get(key)
        if value is not None and (not isinstance(value, str) or value not in allowed):
            raise UnsafeInputError(message.format(name=name, value=str(value)[:40]))


def _validate_import_data(data) -> None:
    if not isinstance(data, dict) or data.get("format") != "zettelapp":
        raise UnsafeInputError("This is not a ZettelApp export.")
    if not isinstance(data.get("version"), int) or data["version"] > 1:
        raise UnsafeInputError("This export was made by a newer version of ZettelApp.")
    for field_name in ("link_types", "notes", "links", "flashcards", "assets"):
        value = data.get(field_name)
        if value is not None and not isinstance(value, list):
            raise UnsafeInputError(f"The export field {field_name!r} must be a list.")
    for raw in data.get("link_types") or []:
        if isinstance(raw, dict):
            _validate_link_style(raw)
    for raw in data.get("notes") or []:
        if not isinstance(raw, dict):
            continue
        mindmap = raw.get("mindmap")
        if mindmap is not None:
            _validate_mindmap(mindmap)


def import_data(
    vault: Vault, data, asset_map: dict[str, str] | None = None, result: ImportResult | None = None
) -> ImportResult:
    _validate_import_data(data)
    with vault.transaction():
        return _import_data(vault, data, asset_map, result)


def _import_data(
    vault: Vault, data, asset_map: dict[str, str] | None = None, result: ImportResult | None = None
) -> ImportResult:
    result = result or ImportResult()
    asset_map = asset_map or {}

    existing_types = vault.link_type_map()
    for raw in data.get("link_types") or []:
        if (
            isinstance(raw, dict)
            and isinstance(raw.get("id"), str)
            and raw["id"] not in existing_types
        ):
            # Exports before link styles have none: such a type gets the least used line.
            line_style = raw.get("line_style") or least_used_line_style(vault.link_types())
            vault.save_link_type(
                LinkType(
                    raw["id"],
                    _str(raw.get("label"), 60),
                    _str(raw.get("inverse_label"), 60),
                    _str(raw.get("color"), 7),
                    bool(raw.get("directed", True)),
                    line_style=line_style,
                    arrow=raw.get("arrow") or "triangle",
                )
            )

    raw_notes = [n for n in (data.get("notes") or []) if isinstance(n, dict)]
    id_map: dict[str, str] = {}
    pending: list[tuple[Note, dict]] = []
    for raw in raw_notes:
        old_id = raw.get("id")
        title, body = _str(raw.get("title"), MAX_TITLE), _str(raw.get("body"), MAX_BODY)
        if is_valid_note_id(old_id):
            current = vault.get_note(old_id)
            if current is not None and current.title == title and current.body == body:
                id_map[old_id] = old_id
                result.skipped += 1
                continue
            new_id = old_id if current is None else None
        else:
            new_id = None
        note = vault.create_note(
            title=title, note_id=new_id, created=_timestamp(raw.get("created"))
        )
        if is_valid_note_id(old_id):
            id_map[old_id] = note.id
        pending.append((note, raw))

    def remap_body(body: str) -> str:
        body = _ASSET_REF_RE.sub(lambda m: "asset:" + asset_map.get(m.group(1), m.group(1)), body)

        def relink(m: re.Match) -> str:
            target = m.group("target").strip()
            if target in id_map and id_map[target] != target:
                return m.group(0).replace(target, id_map[target], 1)
            return m.group(0)

        return WIKILINK_RE.sub(relink, body)

    for note, raw in pending:
        note.body = remap_body(_str(raw.get("body"), MAX_BODY))
        note.url = _str(raw.get("url"), 2048)
        image = raw.get("image")
        note.image = asset_map.get(image, image) if isinstance(image, str) else ""
        note.tags = [t for t in (raw.get("tags") or []) if isinstance(t, str)][:200]
        note.mindmap = sanitize_mindmap(raw.get("mindmap")) if raw.get("mindmap") else None
        vault.save_note(note, touch=False)
        result.notes += 1

    for raw in data.get("links") or []:
        if not isinstance(raw, dict) or raw.get("origin") == "inline":
            continue  # inline links are re-created from the note text
        raw_src, raw_dst = raw.get("src"), raw.get("dst")
        src = id_map.get(raw_src) if isinstance(raw_src, str) else None
        dst = id_map.get(raw_dst) if isinstance(raw_dst, str) else None
        if (
            src
            and dst
            and vault.add_link(src, dst, _str(raw.get("type"), 40) or "related", "manual")
        ):
            result.links += 1

    for raw in data.get("flashcards") or []:
        if not isinstance(raw, dict) or raw.get("source") == "inline":
            continue
        raw_note_id = raw.get("note_id")
        note_id = id_map.get(raw_note_id) if isinstance(raw_note_id, str) else None
        front = _str(raw.get("front"), 20_000)
        if note_id and front:
            vault.save_card(
                Flashcard(
                    None,
                    note_id,
                    remap_body(front),
                    remap_body(_str(raw.get("back"), 20_000)),
                    "cloze" if raw.get("kind") == "cloze" else "basic",
                )
            )
            result.cards += 1
    return result


# --- Markdown folders -------------------------------------------------------------


def import_markdown_folder(vault: Vault, folder: Path) -> ImportResult:
    result = ImportResult()
    files = []
    for path in sorted(folder.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(folder).parts):
            continue  # skip .obsidian, .trash and other hidden folders
        files.append(path)
        if len(files) > MAX_MARKDOWN_FILES:
            raise UnsafeInputError("The folder contains too many Markdown files.")
    with vault.transaction():
        _import_markdown_files(vault, folder, files, result)
    return result


def _parse_front_matter(text: str) -> tuple[dict, str]:
    m = _FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return {}, text
    return (meta if isinstance(meta, dict) else {}), text[m.end() :]


def _import_markdown_files(
    vault: Vault, root: Path, files: list[Path], result: ImportResult
) -> None:
    images_by_name: dict[str, Path] = {}
    for p in root.rglob("*"):
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp") and p.is_file():
            images_by_name.setdefault(p.name.lower(), p)

    parsed = []
    for path in files:
        if path.stat().st_size > MAX_MARKDOWN_BYTES:
            result.warn(f"Skipped {path.name}: file too large")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        meta, body = _parse_front_matter(text)
        title = meta.get("title") if isinstance(meta.get("title"), str) else None
        if not title:
            heading = _HEADING_RE.search(body)
            title = heading.group(1).strip() if heading else path.stem
        parsed.append((path, meta, body, title[:MAX_TITLE]))

    # Map file stems (how Obsidian links) and titles to the new notes.
    created: dict[str, Note] = {}
    for path, meta, body, title in parsed:
        wanted = meta.get("id") if isinstance(meta.get("id"), str) else None
        note_id = (
            wanted if is_valid_note_id(wanted) and not vault.note_exists(wanted, True) else None
        )
        when = datetime.fromtimestamp(path.stat().st_mtime)
        if note_id is None:
            note_id = vault.new_note_id(when)
        created[str(path)] = vault.create_note(
            title=title,
            note_id=note_id,
            created=_timestamp(meta.get("created"))
            or when.astimezone().isoformat(timespec="seconds"),
        )
    stems = {fold(Path(p).stem): n for p, n in created.items()}

    def image_ref(source: Path, target: str) -> str | None:
        target = target.split("#")[0].split("?")[0]
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
            return None  # remote or other-scheme images are not imported
        candidates = []
        try:
            candidates.append(resolve_inside(root, str((source.parent / target).relative_to(root))))
        except (UnsafeInputError, ValueError):
            pass
        found = images_by_name.get(Path(target).name.lower())
        if found:
            candidates.append(found)
        for c in candidates:
            if c.is_file():
                try:
                    name = vault.add_image_file(c)
                    result.images += 1
                    return name
                except (UnsafeInputError, OSError) as exc:
                    result.warn(f"Skipped image {c.name}: {exc}")
                    return None
        return None

    for path, meta, body, title in parsed:
        note = created[str(path)]

        def relink(m: re.Match) -> str:
            target = m.group("target").strip()
            linked = stems.get(
                fold(Path(target).stem if target.lower().endswith(".md") else target)
            )
            if linked is None:
                return m.group(0)
            prefix = f"{m.group('type')}:: " if m.group("type") else ""
            alias = m.group("alias") or (target if fold(target) != fold(linked.title) else None)
            return f"{prefix}[[{linked.title or linked.id}{'|' + alias if alias else ''}]]"

        def embed(m: re.Match) -> str:
            name = image_ref(path, m.group(1))
            return f"![]({'asset:' + name})" if name else m.group(0)

        def md_image(m: re.Match) -> str:
            name = image_ref(path, m.group(2))
            return f"![{m.group(1)}](asset:{name})" if name else m.group(0)

        body = _EMBED_RE.sub(embed, body)
        body = _MD_IMAGE_RE.sub(md_image, body)
        body = WIKILINK_RE.sub(relink, body)

        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = re.split(r"[,\s]+", tags)
        tags = [normalize_tag(str(t)) for t in tags if isinstance(t, (str, int))]
        note.body = body.strip() + "\n"  # #tags in the text become tags when the note is saved
        note.tags = [t for t in tags if t][:200]
        url = meta.get("url") or meta.get("source")
        note.url = url if isinstance(url, str) else ""
        image = meta.get("image")
        if isinstance(image, str):
            note.image = image_ref(path, image) or ""
        note.mindmap = (
            sanitize_mindmap(meta.get("mindmap")) if isinstance(meta.get("mindmap"), dict) else None
        )
        vault.save_note(note, touch=False)
        result.notes += 1
        result.links += len(vault.links_from(note.id))
