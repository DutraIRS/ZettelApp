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
from pathlib import Path

from zettelapp import APP_NAME, __version__
from zettelapp.core.models import Note
from zettelapp.core.storage import Vault
from zettelapp.paths import documents_dir, local_data_dir

_vault: Vault | None = None
_PREF_NAME = "mobile-vault.json"


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
            _vault = Vault.open(folder, create=True)
            _remember_vault(folder)
            return _vault
        except (OSError, RuntimeError) as exc:
            errors.append(f"{folder}: {exc}")
    raise RuntimeError("No writable vault location found (" + "; ".join(errors) + ")")


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
        "created": note.created,
        "modified": note.modified,
    }


def save_note(note_id: str, title: str, body: str) -> dict:
    vault = _ensure_vault()
    note = vault.get_note(note_id)
    if note is None:
        return {"error": "not_found", "id": note_id}
    note.title = title
    note.body = body
    saved = vault.save_note(note)
    return _summary(saved)


def create_note(title: str = "", body: str = "") -> dict:
    note = _ensure_vault().create_note(title=title, body=body)
    return _summary(note)


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
