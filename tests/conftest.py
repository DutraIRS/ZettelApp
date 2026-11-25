import struct
import sys
import zlib

import pytest

from zettelapp.core.storage import Vault


@pytest.fixture(autouse=True)
def _own_local_data(tmp_path_factory, monkeypatch):
    """Point the app's data folders at temporary ones (%LOCALAPPDATA% on Windows,
    $XDG_DATA_HOME and $XDG_CACHE_HOME on Linux), so tests never write backups,
    search indexes or caches into the real ZettelApp folder, or find a language
    model downloaded there."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path_factory.mktemp("local")))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path_factory.mktemp("data")))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path_factory.mktemp("cache")))


def _delete_top_level_widgets() -> None:
    """Close and delete every top-level widget now. Pytest runs no event loop, so a bare
    deleteLater() never happens on its own: without this, every window an earlier test made
    stays alive and each app-wide restyle (apply_theme) walks all of them."""
    qtwidgets = sys.modules.get("PySide6.QtWidgets")
    if qtwidgets is None:
        return
    app = qtwidgets.QApplication.instance()
    if app is None:
        return
    from PySide6.QtCore import QEvent, Qt, QThreadPool

    # Only windows nobody owns. Popups belong to something that deletes them itself (a combo
    # box's list, a button's menu, a completer's list, which has no parent), and deleting one
    # under its owner crashes when the owner goes.
    windows = [
        widget
        for widget in app.topLevelWidgets()
        if widget.parent() is None and widget.windowType() != Qt.WindowType.Popup
    ]
    if not windows:
        return
    # Let background work finish and hand its results over while its receivers still exist:
    # a result delivered after its service was deleted raises "Signal source has been deleted"
    # in whichever test happens to be running.
    for widget in windows:
        for pool in widget.findChildren(QThreadPool):
            pool.waitForDone(20000)
    QThreadPool.globalInstance().waitForDone(20000)
    app.processEvents()
    for widget in windows:
        widget.close()
        widget.deleteLater()
    app.sendPostedEvents(None, QEvent.Type.DeferredDelete)


@pytest.fixture(autouse=True)
def _tidy_widgets_after_each_test():
    """Leave no window behind for the next test (runs after the test's own fixtures)."""
    yield
    _delete_top_level_widgets()


@pytest.fixture(autouse=True, scope="session")
def _tidy_qt_at_exit():
    """Let go of every widget and queued event before Python shuts down, so Qt does not crash
    while the interpreter exits after a long run (it did on Windows, with all tests green)."""
    yield
    qtwidgets = sys.modules.get("PySide6.QtWidgets")
    if qtwidgets is None:
        return
    import gc

    app = qtwidgets.QApplication.instance()
    if app is not None:
        for widget in app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        for _ in range(3):
            app.processEvents()
            app.sendPostedEvents(None, 0)  # 0 = QEvent.DeferredDelete
    gc.collect()


@pytest.fixture
def vault(tmp_path):
    v = Vault.open(tmp_path / "vault")
    yield v
    v.close()


def tiny_png(color=(15, 108, 189)) -> bytes:
    """A valid 1x1 PNG."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        )

    raw = b"\x00" + bytes(color)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


@pytest.fixture
def sample(vault):
    """A small Zettelkasten about learning."""
    a = vault.create_note(
        "Spaced repetition",
        "Reviewing material at increasing intervals improves "
        "long-term memory retention. See [[Forgetting curve]].\n\nQ: Who described the "
        "forgetting curve?\nA: Hermann Ebbinghaus",
        tags=["learning", "memory"],
    )
    b = vault.create_note(
        "Forgetting curve",
        "Memory retention decays exponentially over time unless "
        "the material is reviewed. Ebbinghaus measured it.",
        tags=["memory"],
    )
    c = vault.create_note(
        "Active recall",
        "Testing yourself (retrieval practice) strengthens memory "
        "more than rereading. {{c1::Retrieval practice}} is also called active recall.",
        tags=["learning"],
    )
    d = vault.create_note(
        "Sourdough bread",
        "Flour, water, salt and a starter. Long fermentation develops flavour.",
        tags=["cooking"],
    )
    e = vault.create_note(
        "Interleaving",
        "Mixing different topics during practice improves learning and "
        "memory transfer compared with blocked practice.",
        tags=["learning"],
    )
    vault.add_link(c.id, a.id, "supports")
    vault.add_link(e.id, a.id, "related")
    return {"a": a, "b": b, "c": c, "d": d, "e": e}
