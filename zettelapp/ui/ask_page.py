"""Ask your notes: retrieval-augmented answers from an LLM provider, with citations."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from zettelapp import settings
from zettelapp.core import apikeys, secrets
from zettelapp.core.graph import hop_distances
from zettelapp.core.llm import (
    ContextNote,
    LLMSettings,
    pack_context,
    retrieve_context,
    scope_context,
    stream_answer,
)
from zettelapp.core.render import NoteRenderer
from zettelapp.i18n import _
from zettelapp.ui import icons
from zettelapp.ui.preview import NotePreview
from zettelapp.ui.widgets import Card, ScopePicker, accent_button, label, link_button
from zettelapp.ui.workers import StreamThread


def current_llm_settings() -> LLMSettings:
    return LLMSettings(
        provider=settings.get(settings.LLM_PROVIDER) or "anthropic",
        model=settings.get(settings.LLM_MODEL, "") or "",
        base_url=settings.get(settings.LLM_BASE_URL, "") or "",
        effort=settings.get(settings.LLM_EFFORT),
    )


def review_context(parent: QWidget, context: list[ContextNote], provider: str) -> list[str] | None:
    """Ask which of the notes about to be sent may go: the ids kept, in order, or None when
    the question is not to be sent after all."""
    dialog = QDialog(parent)
    dialog.setWindowTitle(_("Review before sending"))
    dialog.resize(460, 520)
    layout = QVBoxLayout(dialog)
    layout.addWidget(
        label(
            _(
                "These notes will be sent to {provider} with your question. Untick any to leave "
                "out."
            ).format(provider=provider),
            wrap=True,
        )
    )
    notes = QListWidget()
    notes.setAccessibleName(_("Notes to send"))
    for note in context:
        item = QListWidgetItem(note.title or _("Untitled"))
        item.setData(Qt.ItemDataRole.UserRole, note.id)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked)
        notes.addItem(item)
    layout.addWidget(notes, 1)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
    send = buttons.addButton(_("Send"), QDialogButtonBox.ButtonRole.AcceptRole)
    send.setProperty("accent", True)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.notes = notes  # for tests

    def kept() -> list[str]:
        return [
            notes.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(notes.count())
            if notes.item(i).checkState() == Qt.CheckState.Checked
        ]

    notes.itemChanged.connect(lambda _item: send.setEnabled(bool(kept())))
    send.setEnabled(bool(context))
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return kept()


class AskPage(QWidget):
    openNote = Signal(str)
    configureRequested = Signal()
    status = Signal(str)

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setObjectName("Page")
        self.stream_thread: StreamThread | None = None
        self.answer_text = ""
        self.question_text = ""
        self.sources: list = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)
        head = QHBoxLayout()
        head.addWidget(label(_("Ask your notes"), "title"), 1)
        self.provider_label = label("", "secondary")
        head.addWidget(self.provider_label)
        head.addWidget(link_button(_("Change…"), self.configureRequested.emit))
        layout.addLayout(head)

        ask = Card()
        self.question = QPlainTextEdit()
        self.question.setPlaceholderText(
            _(
                "Ask a question about your notes, e.g. “How does spaced repetition relate "
                "to active recall?”  (Ctrl+Enter to ask)"
            )
        )
        self.question.setAccessibleName(_("Question"))
        self.question.setFixedHeight(84)
        ask.body.addWidget(self.question)
        row = QHBoxLayout()
        row.addWidget(label(_("Search in"), "secondary"))
        self.scope = ScopePicker()
        row.addWidget(self.scope, 1)
        ask.body.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(label(_("Send"), "secondary"))
        self.send_mode = QComboBox()
        self.send_mode.setAccessibleName(_("Notes to send"))
        self.send_mode.addItem(_("The most relevant notes"), "relevant")
        self.send_mode.addItem(_("Every note in the scope, nearest first"), "all")
        self.send_mode.setToolTip(
            _(
                "With the current note and linked notes, every note in the scope means its "
                "neighbours up to the depth chosen, the nearest first"
            )
        )
        self.send_mode.setCurrentIndex(
            max(0, self.send_mode.findData(settings.get(settings.LLM_CONTEXT_MODE)))
        )
        row.addWidget(self.send_mode)
        self.limit = QSpinBox()
        self.limit.setRange(1, 40)
        self.limit.setValue(settings.get(settings.LLM_CONTEXT_NOTES))
        self.limit.setSuffix(" notes")
        self.limit.setToolTip(_("How many of the most relevant notes to send with the question"))
        row.addWidget(self.limit)
        self.review = QCheckBox(_("Review before sending"))
        self.review.setToolTip(_("See the notes about to be sent, and untick any to leave out"))
        self.review.setChecked(settings.get(settings.LLM_REVIEW_CONTEXT))
        row.addWidget(self.review)
        row.addStretch(1)
        self.send_mode.currentIndexChanged.connect(
            lambda: self.limit.setVisible(self.send_mode.currentData() == "relevant")
        )
        self.limit.setVisible(self.send_mode.currentData() == "relevant")
        self.stop_button = QPushButton(_("Stop"))
        self.stop_button.setIcon(icons.icon("stop"))
        self.stop_button.clicked.connect(self.stop)
        self.stop_button.setVisible(False)
        row.addWidget(self.stop_button)
        self.ask_button = accent_button(_("Ask"), self.ask, "send")
        row.addWidget(self.ask_button)
        ask.body.addLayout(row)
        layout.addWidget(ask)

        body = QHBoxLayout()
        body.setSpacing(12)
        answer_card = Card()
        answer_head = QHBoxLayout()
        answer_head.addWidget(label(_("Answer"), "section"), 1)
        self.copy_button = link_button(_("Copy"), self.copy_answer)
        self.save_button = link_button(_("Save as note"), self.save_as_note)
        answer_head.addWidget(self.copy_button)
        answer_head.addWidget(self.save_button)
        answer_card.body.addLayout(answer_head)
        self.answer = NotePreview(
            lambda name: self.window.vault.asset_path(name) if self.window.vault else None
        )
        self.answer.noteRequested.connect(self.openNote)
        answer_card.body.addWidget(self.answer, 1)
        body.addWidget(answer_card, 3)
        sources_card = Card()
        sources_card.setFixedWidth(300)
        sources_card.body.addWidget(label(_("Sources sent"), "section"))
        self.sources_list = QListWidget()
        self.sources_list.setAccessibleName(_("Notes sent with the question"))
        self.sources_list.setWordWrap(True)
        self.sources_list.itemClicked.connect(
            lambda item: self.openNote.emit(item.data(Qt.ItemDataRole.UserRole))
        )
        sources_card.body.addWidget(self.sources_list, 1)
        self.privacy = label("", "caption", wrap=True)
        sources_card.body.addWidget(self.privacy)
        body.addWidget(sources_card)
        layout.addLayout(body, 1)

        self._render_timer = QTimer(self, singleShot=True, interval=90, timeout=self._render)
        QShortcut(QKeySequence("Ctrl+Return"), self.question, self.ask)
        QShortcut(QKeySequence("Ctrl+Enter"), self.question, self.ask)
        self._set_idle(True)
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh()

    def refresh(self) -> None:
        cfg = current_llm_settings()
        info = cfg.info
        try:
            has_key = not info.requires_key or apikeys.has_key(info.id)
        except OSError:  # a keyring that fails (locked, timed out): shown as no key, never a crash
            has_key = False
        model = cfg.effective_model()
        self.provider_label.setText(
            f"{info.label} · {model}" + ("" if has_key else " · " + _("no API key"))
        )
        if secrets.secrets_available():
            privacy = _(
                "Only your question and the notes listed above are sent to {label}. The model gets no tools and cannot change your notes. Your API key is kept in the system keyring."
            )
        else:  # Linux without a Secret Service: keys live in memory only
            privacy = (
                _(
                    "Only your question and the notes listed above are sent to {label}. The model gets no tools and cannot change your notes."
                )
                + " "
                + _("No system keyring was found, so keys are kept only until ZettelApp closes.")
            )
        self.privacy.setText(privacy.format(label=info.label))
        if self.window.vault:
            self.scope.set_tags(self.window.vault.all_tags())

    def focus_with_scope(self, mode: str) -> None:
        self.scope.set_mode(mode)
        self.question.setFocus()

    def _set_idle(self, idle: bool) -> None:
        self.ask_button.setVisible(idle)
        self.stop_button.setVisible(not idle)
        self.question.setReadOnly(not idle)

    def _renderer(self) -> NoteRenderer:
        return self.window.reading_renderer()

    def ask(self) -> None:
        vault = self.window.vault
        question = self.question.toPlainText().strip()
        if vault is None or not question or self.stream_thread is not None:
            return
        cfg = current_llm_settings()
        info = cfg.info
        try:
            key = apikeys.active_secret(info.id)
        except OSError as exc:  # the keyring answered with an error (locked, refused, timed out)
            QMessageBox.warning(self, _("Connect an AI provider"), str(exc))
            return
        if info.requires_key and not key:
            if (
                QMessageBox.question(
                    self,
                    _("Connect an AI provider"),
                    _(
                        "Add your {label} API key in Options to ask questions about your notes. Open Options now?"
                    ).format(label=info.label),
                )
                == QMessageBox.StandardButton.Yes
            ):
                self.configureRequested.emit()
            return
        if not settings.get(settings.LLM_PRIVACY_ACK):
            sent = (
                _(
                    "Your question and the most relevant notes (up to {limit}) will be sent to "
                    "{provider} using your API key. Nothing else leaves this computer."
                )
                if self.send_mode.currentData() == "relevant"
                else _(
                    "Your question and the notes in the chosen scope will be sent to {provider} "
                    "using your API key. Nothing else leaves this computer."
                )
            )
            box = QMessageBox(
                QMessageBox.Icon.Information,
                _("Before you ask"),
                sent.format(limit=self.limit.value(), provider=info.label),
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                self,
            )
            dont = QCheckBox(_("Don't show this again"))
            box.setCheckBox(dont)
            if box.exec() != QMessageBox.StandardButton.Ok:
                return
            if dont.isChecked():
                settings.put(settings.LLM_PRIVACY_ACK, True)
        settings.put(settings.LLM_CONTEXT_NOTES, self.limit.value())
        settings.put(settings.LLM_CONTEXT_MODE, self.send_mode.currentData())
        settings.put(settings.LLM_REVIEW_CONTEXT, self.review.isChecked())
        mode, depth, tag = self.scope.value()
        ids = self.window.resolve_scope(mode, depth, tag)
        notes = [n for n in vault.all_notes() if n.id in ids]
        current = self.window.current_note_id()
        focus = [current] if mode == "subgraph" and current else []
        if self.send_mode.currentData() == "all":
            distances = hop_distances(focus, vault.all_links(), depth) if focus else None
            context = scope_context(notes, question, distances)
        else:
            context = retrieve_context(notes, question, self.limit.value(), focus_ids=focus)
        if self.review.isChecked():
            kept = review_context(self, context, info.label)
            if not kept:
                return
            context = pack_context(notes, kept)  # left-out notes may leave room for cut ones
        self.show_sources(context)
        self.question_text = question
        self.answer_text = ""
        self.answer.set_renderer(self._renderer())
        self.answer.show_markdown("*Thinking…*")
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self._set_idle(False)
        self.status.emit(
            _("Asking {label} ({len} notes sent)…").format(label=info.label, len=len(context))
        )
        thread = StreamThread(lambda: stream_answer(cfg, key, question, context), self)
        thread.chunk.connect(self._chunk)
        thread.failed.connect(self._failed)
        thread.finished_ok.connect(self._done)
        thread.cancelled.connect(self._cancelled)
        thread.finished.connect(self._cleanup)
        self.stream_thread = thread
        thread.start()

    def show_sources(self, notes: list) -> None:
        self.sources = notes
        self.sources_list.clear()
        for note in notes:
            item = QListWidgetItem(icons.icon("document"), note.title or "Untitled")
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            self.sources_list.addItem(item)

    def _chunk(self, text: str) -> None:
        self.answer_text += text
        if not self._render_timer.isActive():
            self._render_timer.start()

    def _render(self) -> None:
        self.answer.show_markdown(self.answer_text or "*Thinking…*")

    def _done(self) -> None:
        self._render()
        self.status.emit(_("Answer complete."))
        self.copy_button.setEnabled(bool(self.answer_text))
        self.save_button.setEnabled(bool(self.answer_text))

    def _failed(self, message: str) -> None:
        self.answer.show_markdown("**" + _("Could not get an answer.") + f"**\n\n{message}")
        self.status.emit("")

    def _cancelled(self) -> None:
        self._render()
        self.status.emit(_("Stopped."))
        self.copy_button.setEnabled(bool(self.answer_text))
        self.save_button.setEnabled(bool(self.answer_text))

    def _cleanup(self) -> None:
        self.stream_thread = None
        self._set_idle(True)

    def stop(self) -> None:
        if self.stream_thread is not None:
            self.stream_thread.cancel()
            self.status.emit(_("Stopped."))

    def copy_answer(self) -> None:
        QGuiApplication.clipboard().setText(self.answer_text)
        self.status.emit(_("Answer copied."))

    def save_as_note(self) -> None:
        vault = self.window.vault
        if vault is None or not self.answer_text:
            return

        def alias(title: str) -> str:
            return "".join(c for c in (title or _("Untitled")) if c not in "[]|")

        sources = "\n".join(f"- cites:: [[{n.id}|{alias(n.title)}]]" for n in self.sources)
        body = f"{self.answer_text.strip()}\n\n## {_('Sources')}\n\n{sources}\n"
        note = vault.create_note(title=self.question_text[:120], body=body, tags=["ai-answer"])
        self.window.open_note(note.id)
