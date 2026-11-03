"""Optional semantic search: a downloaded language model, the vectors it makes and their search.

Nothing here runs until the user downloads the model and turns the feature on. onnxruntime and
tokenizers are imported only to load the model, which takes a few hundred MB of memory, so the
app keeps it only while it is in use. Each vault's vectors live in their own file beside the
model, never in the vault, so they can be deleted at any time and are not synced with it.
"""

from __future__ import annotations

import hashlib
import http.client
import os
import shutil
import sqlite3
import urllib.request
from collections.abc import Callable, Iterable
from contextlib import closing
from pathlib import Path

import numpy as np

from zettelapp import __version__
from zettelapp.core.models import Note
from zettelapp.core.storage import Vault
from zettelapp.i18n import _

_MODEL_URL = (
    "https://huggingface.co/intfloat/multilingual-e5-small/resolve/"
    "614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/"
)
# Name on disk: name in that revision of the model's repository, size in bytes, SHA-256.
MODEL_FILES = {
    "model.onnx": (
        "model_qint8_avx512_vnni.onnx",
        118_346_824,
        "dd476dd0c2514e9b9be83aeb3853fac0763e0bdf4a71645407587d77c48a2d88",
    ),
    "tokenizer.json": (
        "tokenizer.json",
        17_082_730,
        "0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39",
    ),
}
MODEL_BYTES = sum(size for _name, size, _digest in MODEL_FILES.values())
# This model is trained to tell what is searched for from what is searched in.
QUERY_PREFIX = "query: "
PASSAGE_PREFIX = "passage: "
MAX_TOKENS = 512
CHUNK_CHARS = 1200
CHUNK_OVERLAP = 200
MAX_CHUNKS = 50  # a very long note is represented by its beginning
# The cosine similarity of even unrelated texts is high with this model (0.75 or so), so only
# scores above the floor and close to the best one count as hits, and these few at most.
MIN_SIMILARITY = 0.82
BEST_MARGIN = 0.03
MAX_HITS = 30

Cancelled = Callable[[], bool]
Progress = Callable[[int, int], None]


class ModelError(RuntimeError):
    pass


# --- the model's files --------------------------------------------------------


def model_installed(root: Path) -> bool:
    try:
        return all(
            (root / "model" / name).stat().st_size == size
            for name, (_remote, size, _digest) in MODEL_FILES.items()
        )
    except OSError:
        return False


def _download_file(
    name: str, done: int, folder: Path, progress: Progress, cancelled: Cancelled
) -> int:
    remote, size, digest = MODEL_FILES[name]
    target = folder / name
    if target.is_file() and target.stat().st_size == size:
        return done + size
    part = target.with_name(name + ".part")
    sha = hashlib.sha256()
    request = urllib.request.Request(
        _MODEL_URL + remote, headers={"User-Agent": f"ZettelApp/{__version__}"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response, part.open("wb") as out:
            received = 0
            while chunk := response.read(1024 * 1024):
                if cancelled():
                    raise ModelError(_("The download was cancelled."))
                received += len(chunk)
                if received > size:
                    break
                out.write(chunk)
                sha.update(chunk)
                progress(done + received, MODEL_BYTES)
        if sha.hexdigest() != digest:  # the file's own check, wherever it was redirected to
            raise ModelError(_("The downloaded model is damaged. Please try again."))
        os.replace(part, target)
    except (OSError, http.client.HTTPException) as exc:
        reason = getattr(exc, "reason", exc)
        raise ModelError(_("Could not download the language model: {error}").format(error=reason))
    finally:
        part.unlink(missing_ok=True)
    return done + size


def download_model(root: Path, progress: Progress, cancelled: Cancelled) -> None:
    """Fetch the model over HTTPS. Only complete files that match their pinned SHA-256 get
    their final names, so a failed download can never leave a model that seems installed."""
    folder = root / "model"
    folder.mkdir(parents=True, exist_ok=True)
    done = 0
    for name in MODEL_FILES:
        done = _download_file(name, done, folder, progress, cancelled)


def remove_all(root: Path) -> None:
    """Delete the model and every vault's vectors."""
    shutil.rmtree(root, ignore_errors=True)


def storage_bytes(root: Path) -> int:
    return sum(f.stat().st_size for f in root.rglob("*") if f.is_file()) if root.is_dir() else 0


class Embedder:
    """The loaded model: turns a text into a vector. Safe to use from several threads."""

    def __init__(self, root: Path, threads: int = 2):
        import onnxruntime
        from tokenizers import Tokenizer

        options = onnxruntime.SessionOptions()
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        self._session = onnxruntime.InferenceSession(
            str(root / "model" / "model.onnx"),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        self._tokenizer = Tokenizer.from_file(str(root / "model" / "tokenizer.json"))
        self._tokenizer.enable_truncation(MAX_TOKENS)

    def embed(self, text: str, prefix: str) -> np.ndarray:
        """The text's unit-length vector: the mean of its tokens' vectors."""
        ids = np.array([self._tokenizer.encode(prefix + text).ids], dtype=np.int64)
        tokens = self._session.run(
            None,
            {
                "input_ids": ids,
                "attention_mask": np.ones_like(ids),
                "token_type_ids": np.zeros_like(ids),
            },
        )[0][0]
        vector = tokens.mean(axis=0)
        return vector / (np.linalg.norm(vector) or 1.0)


# --- the vectors --------------------------------------------------------------


def _index_path(root: Path, vault_id: str) -> Path:
    # Note ids are only timestamps, so vaults need separate files. The id comes from the
    # vault's own file: hashing it keeps a crafted one from pointing outside this folder.
    name = hashlib.sha256(vault_id.encode()).hexdigest()[:32]
    return root / "index" / f"{name}.sqlite"


class VectorIndex:
    """One vault's chunk vectors. Open and close it in the thread that uses it."""

    def __init__(self, root: Path, vault_id: str):
        path = _index_path(root, vault_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA journal_mode = WAL")  # a search can read during indexing
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS chunks (note_id TEXT NOT NULL, chunk INTEGER NOT NULL, "
            "hash TEXT NOT NULL, vector BLOB NOT NULL, PRIMARY KEY (note_id, chunk))"
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def hashes(self) -> dict[str, str]:
        return dict(self.conn.execute("SELECT note_id, hash FROM chunks WHERE chunk = 0"))

    def replace(self, note_id: str, digest: str, vectors: Iterable[np.ndarray]) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM chunks WHERE note_id = ?", (note_id,))
            self.conn.executemany(
                "INSERT INTO chunks VALUES (?, ?, ?, ?)",
                [
                    (note_id, chunk, digest, vector.astype(np.float32).tobytes())
                    for chunk, vector in enumerate(vectors)
                ],
            )

    def remove(self, note_ids: Iterable[str]) -> None:
        with self.conn:
            self.conn.executemany("DELETE FROM chunks WHERE note_id = ?", [(i,) for i in note_ids])

    def search(self, query: np.ndarray) -> dict[str, float]:
        """The notes closest in meaning; vectors are unit length, so a product is a cosine."""
        rows = self.conn.execute("SELECT note_id, vector FROM chunks").fetchall()
        if not rows:
            return {}
        matrix = np.frombuffer(b"".join(r[1] for r in rows), dtype=np.float32)
        similarities = matrix.reshape(len(rows), -1) @ query
        best: dict[str, float] = {}
        for (note_id, _vector), similarity in zip(rows, similarities.tolist(), strict=True):
            best[note_id] = max(best.get(note_id, -1.0), similarity)
        cutoff = max(MIN_SIMILARITY, max(best.values()) - BEST_MARGIN)
        hits = sorted(((s, i) for i, s in best.items() if s >= cutoff), reverse=True)[:MAX_HITS]
        return {note_id: similarity for similarity, note_id in hits}


def chunk_text(text: str) -> list[str]:
    """Split a long text into overlapping pieces that fit the model."""
    text = text.strip()
    step = CHUNK_CHARS - CHUNK_OVERLAP
    return [text[i : i + CHUNK_CHARS] for i in range(0, len(text), step)][:MAX_CHUNKS]


def _note_text(note: Note) -> str:
    return f"{note.display_title}\n\n{note.body}"


def _digest(note: Note) -> str:
    return hashlib.sha256(_note_text(note).encode()).hexdigest()


def sync_index(
    root: Path,
    folder: Path,
    embedder: Callable[[], Embedder],
    progress: Progress,
    cancelled: Cancelled,
) -> None:
    """Bring a vault's vectors up to date: embed new and edited notes and forget those that are
    gone or in the Trash. It reads the vault over a read-only connection of its own, so it can
    run in a background thread, and it can stop between any two pieces of text."""
    vault = Vault.open(folder, readonly=True)
    try:
        vault_id, notes = vault.vault_id, vault.all_notes()
    finally:
        vault.close()
    with closing(VectorIndex(root, vault_id)) as index:
        stored = index.hashes()
        wanted = {n.id: _digest(n) for n in notes}
        index.remove(set(stored) - set(wanted))
        pending = [n for n in notes if stored.get(n.id) != wanted[n.id]]
        for done, note in enumerate(pending, start=1):
            vectors = []
            for chunk in chunk_text(_note_text(note)):
                if cancelled():
                    return
                vectors.append(embedder().embed(chunk, PASSAGE_PREFIX))
            index.replace(note.id, wanted[note.id], vectors)
            progress(done, len(pending))


def semantic_scores(root: Path, vault_id: str, embedder: Embedder, query: str) -> dict[str, float]:
    vector = embedder.embed(query, QUERY_PREFIX)
    with closing(VectorIndex(root, vault_id)) as index:
        return index.search(vector)


def clear_index(root: Path, vault_id: str) -> None:
    """Delete a vault's vectors. It also gets rid of an index file that has been damaged."""
    path = _index_path(root, vault_id)
    for file in path.parent.glob(path.name + "*"):  # with its write-ahead log, if any
        file.unlink(missing_ok=True)
