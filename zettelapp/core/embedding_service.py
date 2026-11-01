"""Embedding orchestration: lazy backend, incremental indexing, model switching.

The EmbeddingService never loads a model unless semantic search is enabled and
a query/indexing pass actually needs it. It owns a separate SQLite file (not
the vault's zettel.db) so embedding storage can be deleted independently.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from zettelapp.core.embeddings import (
    DEFAULT_MODEL_ID,
    EmbeddingBackend,
    EmbeddingModelInfo,
    VectorIndex,
    chunk_text,
    model_dir,
    supported_models,
    validate_model_dir,
)
from zettelapp.core.storage import Vault


def _content_hash(title: str, body: str) -> str:
    return hashlib.sha256(f"{title}\x00{body}".encode()).hexdigest()


class EmbeddingService:
    """Owns the vector store and the (optional, lazily loaded) backend."""

    DB_NAME = "embeddings.db"

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.root / self.DB_NAME)
        self.index = VectorIndex(self.conn)
        self._backend: EmbeddingBackend | None = None
        self._backend_model: str | None = None

    def close(self) -> None:
        self.release_model()
        self.conn.close()

    # --- models -----------------------------------------------------------

    @staticmethod
    def catalog() -> list[EmbeddingModelInfo]:
        return supported_models()

    def installed_models(self) -> list[EmbeddingModelInfo]:
        out = []
        models_root = self.root / "models"
        if models_root.is_dir():
            for directory in sorted(models_root.iterdir()):
                info = validate_model_dir(directory)
                if info:
                    out.append(info)
        return out

    def is_model_installed(self, model_id: str) -> bool:
        return validate_model_dir(model_dir(self.root, model_id)) is not None

    def validate_model(self, model_id: str) -> EmbeddingModelInfo | None:
        """Downloaded/imported models must be validated before activation."""
        return validate_model_dir(model_dir(self.root, model_id))

    def index_exists(self, model_id: str) -> bool:
        return self.index.count(model_id) > 0

    # --- backend lifecycle --------------------------------------------------

    def acquire_model(self, model_id: str) -> EmbeddingBackend:
        if self._backend is None or self._backend_model != model_id:
            info = self.validate_model(model_id)
            if info is None:
                raise FileNotFoundError(f"Embedding model not installed: {model_id}")
            self.release_model()
            self._backend = EmbeddingBackend(info, model_dir(self.root, model_id))
            self._backend.load()
            self._backend_model = model_id
        return self._backend

    def release_model(self) -> None:
        """Drop the loaded session so RAM is reclaimed when idle."""
        if self._backend is not None:
            self._backend.close()
        self._backend = None
        self._backend_model = None

    # --- indexing ------------------------------------------------------------

    def pending_note_ids(self, vault: Vault, model_id: str) -> list[str]:
        indexed = self.index.note_ids(model_id)
        out = []
        for note in vault.all_notes():
            h = _content_hash(note.display_title, note.body)
            if note.id not in indexed or self.index.stored_hash(model_id, note.id) != h:
                out.append(note.id)
        return out

    def index_note(self, vault: Vault, note_id: str, model_id: str) -> int:
        """(Re)embed one note; returns the number of chunks stored."""
        note = vault.get_note(note_id)
        if note is None:
            return 0
        backend = self.acquire_model(model_id)
        chunks = chunk_text(f"{note.display_title}\n\n{note.body}")
        if not chunks:
            return 0
        vectors = backend.embed(chunks, prefix=backend.model.passage_prefix)
        self.index.upsert(model_id, note_id, _content_hash(note.display_title, note.body), vectors)
        return len(vectors)

    def remove_note(self, note_id: str) -> None:
        self.conn.execute("DELETE FROM embeddings WHERE note_id = ?", (note_id,))
        self.conn.commit()

    def rebuild(self, vault: Vault, model_id: str, progress=None) -> int:
        self.index.drop_model(model_id)
        total = 0
        for note_id in self.pending_note_ids(vault, model_id):
            total += self.index_note(vault, note_id, model_id)
            if progress:
                progress()
        return total

    # --- retrieval -----------------------------------------------------------

    def search(self, query: str, model_id: str, top_k: int = 50) -> dict[str, float]:
        backend = self.acquire_model(model_id)
        vector = backend.embed([query], prefix=backend.model.query_prefix)[0]
        return self.index.search(model_id, vector, top_k=top_k)

    def switch_model(self, model_id: str) -> bool:
        """Validate + reuse or mark for rebuild. Never mixes model indexes."""
        info = self.validate_model(model_id)
        if info is None:
            raise FileNotFoundError(f"Embedding model not installed: {model_id}")
        self.release_model()
        return self.index_exists(model_id)

    def delete_embeddings(self, model_id: str | None = None) -> None:
        self.index.drop_model(model_id) if model_id else self.index.drop_all()

    def storage_bytes(self) -> int:
        db = self.root / self.DB_NAME
        return db.stat().st_size if db.exists() else 0


DEFAULT_EMBEDDING_MODEL = DEFAULT_MODEL_ID
