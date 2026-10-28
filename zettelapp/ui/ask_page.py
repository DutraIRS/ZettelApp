"""Ask your notes: retrieval-augmented answers from an LLM provider, with citations."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
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
from zettelapp.core.llm import LLMSettings, retrieve_context, stream_answer
from zettelapp.core.render import NoteRenderer
from zettelapp.core.secrets import get_secret
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
        head.addWidget(label("Ask your notes", "title"), 1)
        self.provider_label = label("", "secondary")
        head.addWidget(self.provider_label)
        head.addWidget(link_button("Change…", self.configureRequested.emit))
        layout.addLayout(head)

        ask = Card()
        self.question = QPlainTextEdit()
        self.question.setPlaceholderText(
            "Ask a question about your notes, e.g. “How does spaced repetition relate "
            "to active recall?”  (Ctrl+Enter to ask)"
        )
        self.question.setAccessibleName("Question")
        self.question.setFixedHeight(84)
        ask.body.addWidget(self.question)
        row = QHBoxLayout()
        row.addWidget(label("Search in", "secondary"))
        self.scope = ScopePicker()
        row.addWidget(self.scope, 1)
        self.limit = QSpinBox()
        self.limit.setRange(1, 40)
        self.limit.setValue(settings.get(settings.LLM_CONTEXT_NOTES))
        self.limit.setSuffix(" notes")
        self.limit.setToolTip("How many of the most relevant notes to send with the question")
        row.addWidget(self.limit)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setIcon(icons.icon("stop"))
        self.stop_button.clicked.connect(self.stop)
        self.stop_button.setVisible(False)
        row.addWidget(self.stop_button)
        self.ask_button = accent_button("Ask", self.ask, "send")
        row.addWidget(self.ask_button)
        ask.body.addLayout(row)
        layout.addWidget(ask)

        body = QHBoxLayout()
        body.setSpacing(12)
        answer_card = Card()
        answer_head = QHBoxLayout()
        answer_head.addWidget(label("Answer", "section"), 1)
        self.copy_button = link_button("Copy", self.copy_answer)
        self.save_button = link_button("Save as note", self.save_as_note)
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
        sources_card.body.addWidget(label("Sources sent", "section"))
        self.sources_list = QListWidget()
        self.sources_list.setAccessibleName("Notes sent with the question")
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
        has_key = not info.requires_key or bool(get_secret(info.secret_name))
        model = cfg.effective_model()
        self.provider_label.setText(
            f"{info.label} · {model}" + ("" if has_key else " · no API key")
        )
        self.privacy.setText(
            f"Only your question and the notes listed above are sent to {info.label}. "
            f"The model gets no tools and cannot change your notes. Your API key is kept in "
            f"Windows Credential Manager."
        )
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
        vault = self.window.vault
        titles = vault.titles()
        return NoteRenderer(
            vault.resolve_title,
            lambda i: titles.get(i) or "Untitled",
            link_types=vault.link_type_map(),
            allow_new_note_links=False,
        )

    def ask(self) -> None:
        vault = self.window.vault
        question = self.question.toPlainText().strip()
        if vault is None or not question or self.stream_thread is not None:
            return
        cfg = current_llm_settings()
        info = cfg.info
        key = get_secret(info.secret_name)
        if info.requires_key and not key:
            if (
                QMessageBox.question(
                    self,
                    "Connect an AI provider",
                    f"Add your {info.label} API key in Options to ask questions about your notes. "
                    "Open Options now?",
                )
                == QMessageBox.StandardButton.Yes
            ):
                self.configureRequested.emit()
            return
        if not settings.get(settings.LLM_PRIVACY_ACK):
            box = QMessageBox(
                QMessageBox.Icon.Information,
                "Before you ask",
                f"Your question and the most relevant notes (up to {self.limit.value()}) will be sent to "
                f"{info.label} using your API key. Nothing else leaves this computer.",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                self,
            )
            dont = QCheckBox("Don't show this again")
            box.setCheckBox(dont)
            if box.exec() != QMessageBox.StandardButton.Ok:
                return
            if dont.isChecked():
                settings.put(settings.LLM_PRIVACY_ACK, True)
        settings.put(settings.LLM_CONTEXT_NOTES, self.limit.value())
        ids = self.window.resolve_scope(*self.scope.value())
        notes = [n for n in vault.all_notes() if n.id in ids]
        mode = self.scope.value()[0]
        focus = (
            [self.window.current_note_id()]
            if mode == "subgraph" and self.window.current_note_id()
            else []
        )
        context = retrieve_context(notes, question, self.limit.value(), focus_ids=focus)
        self.sources = context
        self.sources_list.clear()
        for note in context:
            item = QListWidgetItem(icons.icon("document"), note.title or "Untitled")
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            self.sources_list.addItem(item)
        self.question_text = question
        self.answer_text = ""
        self.answer.set_renderer(self._renderer())
        self.answer.show_markdown("*Thinking…*")
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self._set_idle(False)
        self.status.emit(f"Asking {info.label} ({len(context)} notes sent)…")
        thread = StreamThread(lambda: stream_answer(cfg, key, question, context), self)
        thread.chunk.connect(self._chunk)
        thread.failed.connect(self._failed)
        thread.finished_ok.connect(self._done)
        thread.cancelled.connect(self._cancelled)
        thread.finished.connect(self._cleanup)
        self.stream_thread = thread
        thread.start()

    def _chunk(self, text: str) -> None:
        self.answer_text += text
        if not self._render_timer.isActive():
            self._render_timer.start()

    def _render(self) -> None:
        self.answer.show_markdown(self.answer_text or "*Thinking…*")

    def _done(self) -> None:
        self._render()
        self.status.emit("Answer complete.")
        self.copy_button.setEnabled(bool(self.answer_text))
        self.save_button.setEnabled(bool(self.answer_text))

    def _failed(self, message: str) -> None:
        self.answer.show_markdown(f"**Could not get an answer.**\n\n{message}")
        self.status.emit("")

    def _cancelled(self) -> None:
        self._render()
        self.status.emit("Stopped.")
        self.copy_button.setEnabled(bool(self.answer_text))
        self.save_button.setEnabled(bool(self.answer_text))

    def _cleanup(self) -> None:
        self.stream_thread = None
        self._set_idle(True)

    def stop(self) -> None:
        if self.stream_thread is not None:
            self.stream_thread.cancel()
            self.status.emit("Stopped.")

    def copy_answer(self) -> None:
        QGuiApplication.clipboard().setText(self.answer_text)
        self.status.emit("Answer copied.")

    def save_as_note(self) -> None:
        vault = self.window.vault
        if vault is None or not self.answer_text:
            return

        def alias(title: str) -> str:
            return "".join(c for c in (title or "Untitled") if c not in "[]|")

        sources = "\n".join(f"- cites:: [[{n.id}|{alias(n.title)}]]" for n in self.sources)
        body = f"{self.answer_text.strip()}\n\n## Sources\n\n{sources}\n"
        note = vault.create_note(title=self.question_text[:120], body=body, tags=["ai-answer"])
        self.window.open_note(note.id)
