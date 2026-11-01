"""Optional local semantic search: models, vector index and lazy inference.

Every heavy dependency (onnxruntime, tokenizers, numpy beyond what the core
already uses) is imported lazily. With semantic search disabled or the model
uninstalled, importing this module costs nothing beyond this file.
"""

from __future__ import annotations

import json
import sqlite3
import struct
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODEL_ID = "intfloat/multilingual-e5-small"
DEFAULT_QUERY_PREFIX = "query: "
DEFAULT_PASSAGE_PREFIX = "passage: "
DEFAULT_DIMENSIONS = 384
CHUNK_CHARS = 1200
CHUNK_OVERLAP = 200


@dataclass
class EmbeddingModelInfo:
    model_id: str
    version: str
    dimensions: int
    languages: str
    size_mb: float
    query_prefix: str = DEFAULT_QUERY_PREFIX
    passage_prefix: str = DEFAULT_PASSAGE_PREFIX

    def display_name(self) -> str:
        return self.model_id.split("/")[-1]


def supported_models() -> list[EmbeddingModelInfo]:
    """Models ZettelApp knows how to drive (downloaded or imported)."""
    return [
        EmbeddingModelInfo(
            model_id=DEFAULT_MODEL_ID,
            version="1",
            dimensions=DEFAULT_DIMENSIONS,
            languages="en, pt, es, fr, it (multilingual)",
            size_mb=118.0,
        )
    ]


def model_dir(root: Path, model_id: str) -> Path:
    return root / "models" / model_id.replace("/", "__")


def validate_model_dir(directory: Path) -> EmbeddingModelInfo | None:
    """Check a model directory has the files the ONNX worker needs."""
    if not (directory / "model.onnx").is_file():
        return None
    meta_path = directory / "zettelapp-model.json"
    if not meta_path.is_file():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        dims = int(meta["dimensions"])
    except (ValueError, KeyError):
        return None
    if not (directory / "tokenizer.json").is_file():
        return None
    return EmbeddingModelInfo(
        model_id=str(meta.get("model_id", directory.name.replace("__", "/"))),
        version=str(meta.get("version", "1")),
        dimensions=dims,
        languages=str(meta.get("languages", "")),
        size_mb=round((directory / "model.onnx").stat().st_size / 1e6, 1),
    )


def chunk_text(text: str, chunk_chars: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP):
    """Split long notes into overlapping character chunks."""
    text = text.strip()
    if len(text) <= chunk_chars:
        return [text] if text else []
    step = chunk_chars - overlap
    return [text[i : i + chunk_chars] for i in range(0, len(text), step)]


# --- vector storage -----------------------------------------------------------


class VectorIndex:
    """Chunk embeddings per model, stored as BLOBs in SQLite (exact search)."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._migrate()

    def _migrate(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                model_id TEXT NOT NULL,
                note_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                dimensions INTEGER NOT NULL,
                vector BLOB NOT NULL,
                PRIMARY KEY (model_id, note_id, chunk_index)
            );
            CREATE INDEX IF NOT EXISTS idx_embeddings_note
                ON embeddings(model_id, note_id);
            """
        )
        self.conn.commit()

    @staticmethod
    def encode(vector) -> bytes:
        return struct.pack(f"{len(vector)}f", *vector)

    @staticmethod
    def decode(blob: bytes) -> list[float]:
        n = len(blob) // 4
        return list(struct.unpack(f"{n}f", blob))

    def stored_hash(self, model_id: str, note_id: str) -> str | None:
        row = self.conn.execute(
            "SELECT content_hash FROM embeddings WHERE model_id = ? AND note_id = ? "
            "ORDER BY chunk_index LIMIT 1",
            (model_id, note_id),
        ).fetchone()
        return row[0] if row else None

    def upsert(self, model_id: str, note_id: str, content_hash: str, vectors) -> None:
        self.remove(model_id, note_id)
        rows = [
            (
                model_id,
                note_id,
                i,
                content_hash,
                len(v),
                self.encode(v),
            )
            for i, v in enumerate(vectors)
        ]
        self.conn.executemany("INSERT INTO embeddings VALUES (?, ?, ?, ?, ?, ?)", rows)
        self.conn.commit()

    def remove(self, model_id: str, note_id: str) -> None:
        self.conn.execute(
            "DELETE FROM embeddings WHERE model_id = ? AND note_id = ?", (model_id, note_id)
        )
        self.conn.commit()

    def drop_model(self, model_id: str) -> None:
        self.conn.execute("DELETE FROM embeddings WHERE model_id = ?", (model_id,))
        self.conn.commit()

    def drop_all(self) -> None:
        self.conn.execute("DELETE FROM embeddings")
        self.conn.commit()

    def note_ids(self, model_id: str) -> set[str]:
        return {
            r[0]
            for r in self.conn.execute(
                "SELECT DISTINCT note_id FROM embeddings WHERE model_id = ?", (model_id,)
            )
        }

    def count(self, model_id: str | None = None) -> int:
        if model_id:
            row = self.conn.execute(
                "SELECT COUNT(*) FROM embeddings WHERE model_id = ?", (model_id,)
            ).fetchone()
        else:
            row = self.conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()
        return int(row[0])

    def search(self, model_id: str, query_vector, top_k: int = 50) -> dict[str, float]:
        """Exact cosine similarity (vectors are stored pre-normalized)."""
        import numpy as np

        best: dict[str, float] = {}
        rows = self.conn.execute(
            "SELECT note_id, vector FROM embeddings WHERE model_id = ?", (model_id,)
        ).fetchall()
        if not rows:
            return {}
        matrix = np.array([self.decode(r[1]) for r in rows], dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1)
        norms[norms == 0] = 1.0
        matrix = matrix / norms[:, None]
        q = np.asarray(query_vector, dtype=np.float32)
        q = q / (np.linalg.norm(q) or 1.0)
        sims = matrix @ q
        for (note_id, _blob), sim in zip(rows, sims):
            score = float(sim)
            if score > best.get(note_id, -1.0):
                best[note_id] = score
        top = sorted(best.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
        return dict(top)


# --- embedding backend --------------------------------------------------------


class EmbeddingBackend:
    """Runs an ONNX embedding model; heavy imports happen on load()."""

    def __init__(self, model: EmbeddingModelInfo, directory: Path, threads: int = 2):
        self.model = model
        self.directory = directory
        self.threads = threads
        self._session = None
        self._tokenizer = None

    def load(self) -> None:
        import onnxruntime as ort
        from tokenizers import Tokenizer

        so = ort.SessionOptions()
        so.intra_op_num_threads = self.threads
        so.inter_op_num_threads = 1
        self._session = ort.InferenceSession(
            str(self.directory / "model.onnx"),
            sess_options=so,
            providers=["CPUExecutionProvider"],
        )
        self._tokenizer = Tokenizer.from_file(str(self.directory / "tokenizer.json"))

    def close(self) -> None:
        self._session = None
        self._tokenizer = None

    @property
    def loaded(self) -> bool:
        return self._session is not None

    def embed(self, texts: list[str], prefix: str, max_tokens: int = 512):
        """Embed texts, L2-normalize; mean-pools token embeddings."""
        import numpy as np

        if self._session is None:
            raise RuntimeError("Model not loaded")
        encoded = [self._tokenizer.encode(prefix + t) for t in texts]
        max_len = min(max(max(e.ids) and len(e.ids) for e in encoded), max_tokens)
        input_ids = np.zeros((len(encoded), max_len), dtype=np.int64)
        attention = np.zeros((len(encoded), max_len), dtype=np.int64)
        for i, enc in enumerate(encoded):
            ids = enc.ids[:max_len]
            input_ids[i, : len(ids)] = ids
            attention[i, : len(ids)] = 1
        out = self._session.run(None, {"input_ids": input_ids, "attention_mask": attention})[0]
        mask = attention[:, :, None].astype(np.float32)
        summed = (out.astype(np.float32) * mask).sum(axis=1)
        counts = np.clip(mask.sum(axis=1), 1e-9, None)
        vectors = summed / counts
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms
