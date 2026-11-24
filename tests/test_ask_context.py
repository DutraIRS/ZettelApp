"""Ask your notes: sending the open note's neighbours, and reviewing the notes before sending."""

# ruff: noqa: F811  (the `window` fixture is imported, then used as a test argument)

import os

import pytest

from zettelapp.core.graph import hop_distances
from zettelapp.core.llm import MAX_CONTEXT_CHARS, scope_context
from zettelapp.core.models import Link, Note

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _link(src, dst):
    return Link(src=src, dst=dst, type="related", origin="manual")


def test_hop_distances_follow_links_both_ways_up_to_the_depth():
    links = [_link("a", "b"), _link("c", "b"), _link("c", "d"), _link("x", "y")]
    assert hop_distances(["a"], links, 2) == {"a": 0, "b": 1, "c": 2}
    assert hop_distances(["a"], links, 3) == {"a": 0, "b": 1, "c": 2, "d": 3}
    assert hop_distances(["a"], links, 0) == {"a": 0}


def test_every_note_in_scope_goes_nearest_first_then_by_relevance():
    notes = [
        Note(id="far", title="Far", body="spaced repetition everywhere"),
        Note(id="near-a", title="Near A", body="cooking"),
        Note(id="near-b", title="Near B", body="spaced repetition"),
        Note(id="open", title="Open", body="the open note"),
    ]
    distances = {"open": 0, "near-a": 1, "near-b": 1, "far": 2}
    sent = scope_context(notes, "spaced repetition", distances)
    assert [n.id for n in sent] == ["open", "near-b", "near-a", "far"]
    # without distances (another scope), the most relevant first, but all of them
    assert [n.id for n in scope_context(notes, "spaced repetition")][-2:] != ["far", "near-b"]
    assert len(scope_context(notes, "spaced repetition")) == 4


def test_every_note_in_scope_still_fits_the_size_cap():
    notes = [Note(id=f"n{i}", title=f"N{i}", body="x" * 9000) for i in range(20)]
    sent = scope_context(notes, "x")
    assert sum(len(n.body) for n in sent) <= MAX_CONTEXT_CHARS
    assert 0 < len(sent) < 20


pytest.importorskip("PySide6.QtWidgets")

from tests.test_ui_smoke import window  # noqa: E402, F401


def test_ask_sends_the_neighbours_and_only_the_notes_kept_in_review(window, monkeypatch):
    from zettelapp import settings
    from zettelapp.ui import ask_page

    vault = window.vault
    hub = vault.create_note(title="Hub", body="spaced repetition")
    one = vault.create_note(title="One hop", body="intervals")
    two = vault.create_note(title="Two hops", body="memory")
    vault.create_note(title="Elsewhere", body="spaced repetition again")
    vault.add_link(hub.id, one.id, "related", "manual")
    vault.add_link(one.id, two.id, "related", "manual")
    window.list.refresh()
    window.open_note(hub.id)

    settings.put(settings.LLM_PRIVACY_ACK, True)
    monkeypatch.setattr(ask_page.apikeys, "active_secret", lambda provider: "key")
    started = []

    class Thread:
        def __init__(self, make_stream, parent=None):
            self.chunk = self.failed = self.finished_ok = self.cancelled = self.finished = self
            started.append(make_stream)

        def connect(self, slot):
            pass

        def start(self):
            pass

    monkeypatch.setattr(ask_page, "StreamThread", Thread)
    reviewed = []

    def review(parent, context, provider):
        reviewed.append([n.title for n in context])
        return [n.id for n in context if n.title != "One hop"]

    monkeypatch.setattr(ask_page, "review_context", review)
    page = window.ask
    page.scope.set_mode("subgraph")
    page.scope.depth_spin.setValue(2)
    page.send_mode.setCurrentIndex(page.send_mode.findData("all"))
    assert page.limit.isHidden()  # every note in scope: no number of notes to pick
    page.review.setChecked(True)
    page.question.setPlainText("How do these connect?")
    page.ask()
    assert reviewed == [["Hub", "One hop", "Two hops"]]  # the neighbours, nearest first
    assert [n.title for n in page.sources] == ["Hub", "Two hops"]
    assert len(started) == 1
    assert settings.get(settings.LLM_CONTEXT_MODE) == "all"
    assert settings.get(settings.LLM_REVIEW_CONTEXT)

    monkeypatch.setattr(ask_page, "review_context", lambda *args: None)  # Cancel in the review
    page.ask()
    assert len(started) == 1  # nothing sent


def test_the_review_dialog_returns_the_ticked_notes_and_needs_at_least_one(window):
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox

    from zettelapp.core.llm import ContextNote
    from zettelapp.ui.ask_page import review_context

    context = [ContextNote(i, f"Note {i}", [], "text") for i in ("a", "b", "c")]
    seen = {}

    def answer():
        dialog = next(
            w for w in QApplication.topLevelWidgets() if isinstance(w, QDialog) and w.isVisible()
        )
        send = next(
            b for b in dialog.findChildren(QDialogButtonBox)[0].buttons() if b.text() == "Send"
        )
        for i in range(3):
            dialog.notes.item(i).setCheckState(Qt.CheckState.Unchecked)
        seen["none ticked"] = send.isEnabled()
        dialog.notes.item(2).setCheckState(Qt.CheckState.Checked)
        dialog.notes.item(0).setCheckState(Qt.CheckState.Checked)
        send.click()

    QTimer.singleShot(0, answer)
    assert review_context(window, context, "Anthropic") == ["a", "c"]
    assert seen["none ticked"] is False
