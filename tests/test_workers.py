"""Background tasks deliver their results and are freed afterwards."""

import gc
import logging
import sys

from PySide6.QtCore import QEventLoop, QThreadPool, QTimer
from PySide6.QtWidgets import QApplication

from zettelapp.ui import workers


def _pump(times: int = 5) -> None:
    for _unused in range(times):
        loop = QEventLoop()
        QTimer.singleShot(20, loop.quit)
        loop.exec()


def test_finished_tasks_deliver_results_and_free_what_they_captured():
    QApplication.instance() or QApplication(["test"])
    payload = bytearray(1_000_000)  # stands for the notes a task works on
    references = sys.getrefcount(payload)
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
    assert sum(isinstance(o, workers._Task) for o in gc.get_objects()) < 10
