"""Background tasks deliver their results and are freed afterwards."""

import gc
import logging
import sys

import pytest
from PySide6.QtCore import QEventLoop, QThreadPool, QTimer
from PySide6.QtWidgets import QApplication

from zettelapp.core.suggest import NoteData
from zettelapp.ui import workers
from zettelapp.ui.workers import SemanticService


def _pump(times: int = 5) -> None:
    for _unused in range(times):
        loop = QEventLoop()
        QTimer.singleShot(20, loop.quit)
        loop.exec()


def test_finished_tasks_deliver_results_and_free_what_they_captured():
    QApplication.instance() or QApplication(["test"])
    payload = bytearray(1_000_000)  # stands for the notes a task works on
    references = sys.getrefcount(payload)
    gc.collect()
    tasks_before = sum(isinstance(o, workers._Task) for o in gc.get_objects())
    results, errors = [], []

    def work(i, data):
        if i % 5 == 0:
            raise ValueError("boom")
        return i

    # pytest keeps logged tracebacks, whose frames would keep the failed tasks alive here.
    logging.disable(logging.ERROR)
    try:
        for i in range(100):
            workers.run_task(work, i, payload, on_done=results.append, on_error=errors.append)
        QThreadPool.globalInstance().waitForDone(30000)
        _pump()
    finally:
        logging.disable(logging.NOTSET)
    gc.collect()

    assert sorted(results) == [i for i in range(100) if i % 5]
    assert errors == ["boom"] * 20
    assert not workers._alive
    assert sys.getrefcount(payload) == references  # no finished task still holds it
    # Every task used to stay in memory for good (and everything it captured with it).
    tasks_after = sum(isinstance(o, workers._Task) for o in gc.get_objects())
    assert tasks_after - tasks_before < 10  # earlier tests' tasks may still be winding down


def _pending_suggestion(vault, sample, monkeypatch):
    callbacks = []
    monkeypatch.setattr(
        workers, "run_task", lambda *args, **kwargs: callbacks.append(kwargs["on_done"])
    )
    service = workers.SuggestionService()
    delivered = []
    service.ready.connect(lambda note_id, items: delivered.append((note_id, items)))
    note = sample["a"]
    service.request(vault, NoteData(note.id, note.title, note.body, frozenset(note.tags)), 5, 0.2)
    return service, callbacks[0], delivered


def test_invalidating_suggestions_discards_an_in_flight_result(vault, sample, monkeypatch):
    service, finish, delivered = _pending_suggestion(vault, sample, monkeypatch)

    service.invalidate()
    finish([])

    assert delivered == []


def test_reconfiguring_suggestions_discards_an_in_flight_result(vault, sample, monkeypatch):
    service, finish, delivered = _pending_suggestion(vault, sample, monkeypatch)

    service.configure(["tfidf"], 2.0)
    finish([])

    assert delivered == []


class _Model:
    loads = 0

    def __init__(self, _root, _threads):
        type(self).loads += 1

    def embed(self, text, _prefix):
        import numpy as np

        return np.array([1.0, 0.0], dtype=np.float32)


@pytest.fixture
def service(tmp_path, monkeypatch):
    QApplication.instance() or QApplication(["test"])
    _Model.loads = 0
    monkeypatch.setattr(workers, "Embedder", _Model)
    service = SemanticService(tmp_path / "search")
    yield service
    service.shutdown()


def _wait(service, condition=lambda: True):
    for _unused in range(100):
        service.pool.waitForDone(5000)
        _pump(1)
        if condition():
            return
    raise AssertionError("the background work did not finish")


def test_semantic_search_loads_the_model_once_and_answers(service, vault):
    answers = []
    service.scored.connect(lambda words, scores: answers.append((words, scores)))
    note = vault.create_note("Note", "text")
    service.sync(vault.folder)
    _wait(service, lambda: service._indexing_stop is None)
    service.search(vault.vault_id, "anything")
    service.search(vault.vault_id, "else")
    _wait(service, lambda: len(answers) == 2)
    assert sorted(words for words, _scores in answers) == ["anything", "else"]
    assert all(scores == {note.id: pytest.approx(1.0)} for _words, scores in answers)
    assert _Model.loads == 1


def test_the_model_is_released_when_idle_but_not_while_at_work(service, vault):
    vault.create_note("Note", "text")
    service.search(vault.vault_id, "words")
    _wait(service, lambda: service._running == 0)
    assert service._embedder is not None
    service._running = 1
    service.release()
    assert service._embedder is not None and service._idle.isActive()
    service._running = 0
    service.release()
    assert service._embedder is None
    service.search(vault.vault_id, "words")
    _wait(service, lambda: service._running == 0)
    assert _Model.loads == 2


def test_asking_to_index_during_a_pass_means_one_more_pass(service, vault, monkeypatch):
    calls = []
    monkeypatch.setattr(workers, "sync_index", lambda root, folder, *_rest: calls.append(folder))
    service.sync(vault.folder)
    service.sync(vault.folder)
    service.sync(vault.folder)
    _wait(service, lambda: len(calls) == 2 and service._indexing_stop is None)
    assert calls == [vault.folder, vault.folder]


def test_a_failure_in_the_background_is_reported_and_clears_the_state(service, vault, monkeypatch):
    def fail(*_args):
        raise OSError("no disk")

    errors = []
    service.failed.connect(errors.append)
    monkeypatch.setattr(workers, "sync_index", fail)
    logging.disable(logging.ERROR)
    try:
        service.sync(vault.folder)
        _wait(service, lambda: service._indexing_stop is None)
    finally:
        logging.disable(logging.NOTSET)
    assert errors == ["no disk"]
    assert service._running == 0


def test_downloads_report_how_they_end_and_can_be_cancelled(service, monkeypatch):
    def fake_download(root, progress, cancelled):
        progress(1, 2)
        if cancelled():
            raise RuntimeError("stopped")

    ended, progress = [], []
    service.downloaded.connect(ended.append)
    service.downloading.connect(lambda done, total: progress.append((done, total)))
    monkeypatch.setattr(workers, "download_model", fake_download)
    service.download()
    assert service.is_downloading
    _wait(service, lambda: ended)
    assert ended == [""] and progress == [(1, 2)] and not service.is_downloading

    logging.disable(logging.ERROR)
    try:
        service.download()
        service.cancel_download()
        _wait(service, lambda: len(ended) == 2)
    finally:
        logging.disable(logging.NOTSET)
    assert ended[1] in ("", "stopped")  # it may have finished before the cancel arrived


def test_rebuilding_indexes_the_vault_again_from_scratch(service, vault):
    vault.create_note("Note", "text")
    service.sync(vault.folder)
    _wait(service, lambda: service._indexing_stop is None)
    done = []
    service.indexing.connect(lambda finished, total: done.append((finished, total)))
    service.rebuild(vault.folder, vault.vault_id)
    _wait(service, lambda: done and service._indexing_stop is None)
    assert done == [(1, 1)]


def test_removing_the_data_stops_the_work_and_deletes_it(service, vault):
    vault.create_note("Note", "text")
    service.sync(vault.folder)
    _wait(service, lambda: service._indexing_stop is None)
    assert service.root.exists()
    service.remove_data()
    assert not service.root.exists() and service._embedder is None
