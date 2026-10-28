"""Background work. SQLite connections are bound to the GUI thread, so tasks
receive plain data snapshots and never touch the vault themselves."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QThread, QThreadPool, Signal

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
        self.setAutoDelete(False)  # Python owns the task (see run_task)
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
    # Release the task only after its (queued) result reached the GUI thread;
    # releasing it earlier would drop the result.
    task.signals.done.connect(lambda *_: _alive.discard(task))
    task.signals.failed.connect(lambda *_: _alive.discard(task))
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

    def invalidate(self) -> None:
        self._signature = None

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
