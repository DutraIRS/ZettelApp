"""Background work. SQLite connections are bound to the GUI thread, so tasks
receive plain data snapshots and never touch the vault themselves."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThread, QThreadPool, QTimer, Signal

from zettelapp.core.embeddings import (
    Embedder,
    clear_index,
    download_model,
    remove_all,
    semantic_scores,
    sync_index,
)
from zettelapp.core.storage import Vault
from zettelapp.core.suggest import LinkSuggester, NoteData, Suggestion

log = logging.getLogger(__name__)


class _Signals(QObject):
    done = Signal(object)
    failed = Signal(str)


_alive: set = set()


class _Task(QRunnable):
    def __init__(self, fn: Callable, args: tuple, kwargs: dict):
        super().__init__()
        # The pool deletes the task after run() (Qt's default). With autoDelete off, PySide's
        # pool keeps a reference to every task it ever ran, so none of them was ever freed.
        self.fn, self.args, self.kwargs = fn, args, kwargs
        self.signals = _Signals()

    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as exc:  # noqa: BLE001 - reported to the UI
            log.exception("Background task failed")
            self.signals.failed.emit(str(exc) or exc.__class__.__name__)
        else:
            self.signals.done.emit(result)


def run_task(
    fn: Callable,
    *args,
    on_done: Callable | None = None,
    on_error: Callable | None = None,
    pool: QThreadPool | None = None,
    **kwargs,
) -> None:
    task = _Task(fn, args, kwargs)
    if on_done:
        task.signals.done.connect(on_done)
    if on_error:
        task.signals.failed.connect(on_error)

    def release(*_args) -> None:
        # Runs after on_done/on_error, once the (queued) result reached the GUI thread;
        # releasing the task earlier would drop the result. The signal connections hold
        # this function, which holds the task: a cycle through Qt that Python's garbage
        # collector can't see. Disconnecting breaks it, freeing the task (whose C++ part
        # the pool has already deleted) and everything its function captured.
        _alive.discard(task)
        task.fn = task.args = task.kwargs = None
        signals = task.signals
        signals.done.disconnect()
        signals.failed.disconnect()
        signals.deleteLater()

    task.signals.done.connect(release)
    task.signals.failed.connect(release)
    _alive.add(task)
    (pool or QThreadPool.globalInstance()).start(task)


class SuggestionService(QObject):
    """Runs the Naive Bayes link suggester off the GUI thread.

    The corpus (index + trained model) is rebuilt when the set of notes,
    links or feedback changes, and at most once a minute for text edits.
    """

    ready = Signal(str, list)  # note id, suggestions
    failed = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)  # serialise access to the suggester
        self.suggester = LinkSuggester()
        self._lock = threading.Lock()
        self._signature: tuple | None = None
        self._generation = -1
        self._built_at = 0.0
        self._request = 0
        self.settings: dict = {}

    def configure(self, enabled_features: list[str] | None, prior_strength: float) -> None:
        with self._lock:
            self.suggester = LinkSuggester(prior_strength=prior_strength, enabled=enabled_features)
            self._signature = None
            self._request += 1  # discard work started with the previous configuration

    def invalidate(self) -> None:
        self._signature = None
        self._request += 1  # pending results belong to the previous vault or settings

    def request(self, vault: Vault, note: NoteData, limit: int, min_probability: float) -> None:
        self._request += 1
        request_id = self._request
        links = [(l.src, l.dst) for l in vault.all_links()]
        feedback = vault.feedback()
        notes_count = vault.count_notes()
        signature = (notes_count, hash(tuple(sorted(links))), hash(tuple(sorted(feedback.items()))))
        stale = signature != self._signature or (
            vault.generation != self._generation and time.monotonic() - self._built_at > 60
        )
        corpus = None
        if stale:
            corpus = [NoteData(n.id, n.title, n.body, frozenset(n.tags)) for n in vault.all_notes()]
            self._signature = signature
            self._generation = vault.generation
            self._built_at = time.monotonic()

        def work() -> list[Suggestion]:
            with self._lock:
                if corpus is not None:
                    self.suggester.rebuild(corpus, links, feedback)
                return self.suggester.suggest(note, limit=limit, min_probability=min_probability)

        def done(result: list[Suggestion]) -> None:
            if request_id == self._request:  # ignore answers to outdated requests
                self.ready.emit(note.id, result)

        run_task(work, on_done=done, on_error=self.failed.emit, pool=self.pool)

    def report(self) -> dict:
        with self._lock:
            return self.suggester.report()


class SemanticService(QObject):
    """Semantic search off the GUI thread. The language model takes a few hundred MB of memory,
    so it loads on first use and is let go of soon after the last one."""

    IDLE_MS = 120_000

    scored = Signal(str, dict)  # the search words; note id -> similarity
    indexing = Signal(int, int)  # notes done, notes to do
    downloading = Signal(int, int)  # bytes done, bytes to do
    downloaded = Signal(str)  # the download ended: empty, or what went wrong
    failed = Signal(str)

    def __init__(self, root: Path, parent: QObject | None = None):
        super().__init__(parent)
        self.root = root
        self.threads = 2
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(3)  # a search needn't wait for indexing or for a download
        self._model_lock = threading.Lock()
        self._embedder: Embedder | None = None
        self._running = 0
        self._indexing_stop: threading.Event | None = None
        self._index_again: Path | None = None
        self._download_stop: threading.Event | None = None
        self._idle = QTimer(self, singleShot=True, interval=self.IDLE_MS, timeout=self.release)

    @property
    def is_downloading(self) -> bool:
        return self._download_stop is not None

    def _model(self) -> Embedder:  # called from worker threads
        with self._model_lock:
            if self._embedder is None:
                self._embedder = Embedder(self.root, self.threads)
            return self._embedder

    def _run(self, work: Callable, on_done: Callable, on_error: Callable) -> None:
        def finished(handler: Callable, result) -> None:
            self._running -= 1
            self._idle.start()
            handler(result)

        self._running += 1
        run_task(
            work,
            on_done=lambda result: finished(on_done, result),
            on_error=lambda message: finished(on_error, message),
            pool=self.pool,
        )

    def release(self) -> None:
        """Let go of the model, unless it is at work."""
        if self._running:
            self._idle.start()
            return
        with self._model_lock:
            self._embedder = None

    def search(self, vault_id: str, words: str) -> None:
        self._run(
            lambda: semantic_scores(self.root, vault_id, self._model(), words),
            lambda scores: self.scored.emit(words, scores),
            self.failed.emit,
        )

    def sync(self, folder: Path) -> None:
        """Bring a vault's index up to date. One pass runs at a time; asking during a pass
        means one more after it, for what changed in the meantime."""
        if self._indexing_stop is not None:
            self._index_again = folder
            return
        stop = self._indexing_stop = threading.Event()

        def finished(error: str | None) -> None:
            self._indexing_stop = None
            again, self._index_again = self._index_again, None
            if error:
                self.failed.emit(error)
            elif again:
                self.sync(again)

        self._run(
            lambda: sync_index(self.root, folder, self._model, self.indexing.emit, stop.is_set),
            finished,
            finished,
        )

    def rebuild(self, folder: Path, vault_id: str) -> None:
        """Index a vault from scratch."""
        self.cancel_sync()
        self.pool.waitForDone(5000)  # at most a moment: it stops between pieces of text
        clear_index(self.root, vault_id)
        self.sync(folder)

    def cancel_sync(self) -> None:
        self._index_again = None
        if self._indexing_stop is not None:
            self._indexing_stop.set()

    def download(self) -> None:
        if self.is_downloading:
            return
        stop = self._download_stop = threading.Event()

        def finished(error: str | None) -> None:
            self._download_stop = None
            self.downloaded.emit(error or "")

        self._run(
            lambda: download_model(self.root, self.downloading.emit, stop.is_set),
            finished,
            finished,
        )

    def cancel_download(self) -> None:
        if self._download_stop is not None:
            self._download_stop.set()

    def shutdown(self, wait_ms: int = 5000) -> None:
        """Stop everything in the background and free the model."""
        self.cancel_sync()
        self.cancel_download()
        self.pool.waitForDone(wait_ms)
        self._idle.stop()
        with self._model_lock:
            self._embedder = None

    def remove_data(self) -> None:
        """Delete the model and every vault's vectors."""
        self.shutdown()
        remove_all(self.root)


class StreamThread(QThread):
    """Consumes a generator of text chunks (an LLM answer) in a thread."""

    chunk = Signal(str)
    failed = Signal(str)
    finished_ok = Signal()
    cancelled = Signal()

    def __init__(self, make_stream: Callable, parent: QObject | None = None):
        super().__init__(parent)
        self.make_stream = make_stream
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    def run(self) -> None:
        stream = None
        try:
            stream = self.make_stream()
            for text in stream:
                if self._cancel.is_set():
                    break
                self.chunk.emit(text)
        except Exception as exc:  # noqa: BLE001 - shown to the user
            if not self._cancel.is_set():
                log.warning("Streaming failed: %s", exc.__class__.__name__)
                self.failed.emit(str(exc) or exc.__class__.__name__)
                return
        finally:
            if stream is not None and hasattr(stream, "close"):
                stream.close()
        if self._cancel.is_set():
            self.cancelled.emit()
        else:
            self.finished_ok.emit()
