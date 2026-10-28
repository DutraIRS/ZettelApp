"""Review: spaced repetition, quizzes, and Anki (sync and .apkg export)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from zettelapp import settings
from zettelapp.core.anki import AnkiConnect, anki_renderer, build_payloads
from zettelapp.core.quiz import MODES, Question, build_quiz, grade_typed, schedule
from zettelapp.core.render import NoteRenderer
from zettelapp.i18n import _, n_
from zettelapp.ui import icons, theme
from zettelapp.ui.preview import NotePreview
from zettelapp.ui.widgets import Card, ScopePicker, accent_button, label, link_button
from zettelapp.ui.workers import run_task


class ReviewPage(QWidget):
    openNote = Signal(str)
    status = Signal(str)

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.setObjectName("Page")
        self.questions: list[Question] = []
        self.position = 0
        self.score = 0
        self.mode = "flashcards"
        self.stack = QStackedWidget()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 18, 24, 24)
        outer.addWidget(self.stack)
        self.stack.addWidget(self._build_home())
        self.stack.addWidget(self._build_session())
        self.stack.addWidget(self._build_summary())

    # --- home ---------------------------------------------------------------

    def _build_home(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(label(_("Review"), "title"))
        row = QHBoxLayout()
        row.setSpacing(14)

        due = Card()
        due.body.addWidget(label(_("Due today"), "secondary"))
        self.due_count = label("0", "hero")
        due.body.addWidget(self.due_count)
        self.due_detail = label("", "caption")
        due.body.addWidget(self.due_detail)
        due.body.addStretch(1)
        due.body.addWidget(accent_button(_("Start review"), lambda: self.start_due(), "play"))
        row.addWidget(due, 1)

        quiz = Card()
        quiz.body.addWidget(label(_("Practice quiz"), "section"))
        quiz.body.addWidget(label(_("Choose notes and a question style."), "caption"))
        self.scope = ScopePicker()
        quiz.body.addWidget(self.scope)
        line = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.setAccessibleName(_("Quiz type"))
        for key, text in ((k, _(v)) for k, v in MODES.items()):
            self.mode_combo.addItem(text, key)
        self.count = QSpinBox()
        self.count.setRange(3, 100)
        self.count.setValue(15)
        self.count.setSuffix(" questions")
        line.addWidget(self.mode_combo, 1)
        line.addWidget(self.count)
        quiz.body.addLayout(line)
        quiz.body.addStretch(1)
        quiz.body.addWidget(accent_button(_("Start quiz"), self.start_quiz, "review"))
        row.addWidget(quiz, 2)
        layout.addLayout(row)

        anki = Card()
        head = QHBoxLayout()
        head.addWidget(label(_("Anki"), "section"), 1)
        self.anki_state = label("", "caption")
        head.addWidget(self.anki_state)
        head.addWidget(link_button(_("Check connection"), self.check_anki))
        anki.body.addLayout(head)
        anki.body.addWidget(
            label(
                _(
                    "Sync the flashcards in the chosen scope to Anki through the AnkiConnect add-on (code 2055492159), or "
                    "export a deck file. Each card links back to its note with a zettelapp:// link, and syncing again "
                    "updates cards instead of duplicating them."
                ),
                "caption",
                wrap=True,
            )
        )
        deck_row = QHBoxLayout()
        deck_row.addWidget(label(_("Deck"), "secondary"))
        self.deck = QLineEdit(settings.get(settings.ANKI_DECK))
        self.deck.setAccessibleName(_("Anki deck name"))
        deck_row.addWidget(self.deck, 1)
        sync = QPushButton(_("Sync to Anki"))
        sync.setIcon(icons.icon("sync"))
        sync.clicked.connect(self.sync_anki)
        deck_row.addWidget(sync)
        export = QPushButton(_("Export deck (.apkg)…"))
        export.setIcon(icons.icon("export"))
        export.clicked.connect(lambda: self.window.export_dialog("all", fmt="anki"))
        deck_row.addWidget(export)
        anki.body.addLayout(deck_row)
        layout.addWidget(anki)
        layout.addStretch(1)
        return page

    def refresh(self) -> None:
        vault = self.window.vault
        if vault is None:
            return
        due = vault.due_cards()
        total = len(vault.cards_for_notes())
        self.due_count.setText(str(len(due)))
        self.due_detail.setText(
            n_("of {n} flashcard", "of {n} flashcards", total).format(n=total)
            if total
            else _(
                "No flashcards yet. Add some from a note's Flashcards tab, or write Q:/A: in a note."
            )
        )
        self.scope.set_tags(vault.all_tags())

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh()

    # --- session --------------------------------------------------------------

    def _build_session(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        top = QHBoxLayout()
        top.addWidget(link_button(_("‹ End session"), self.finish))
        top.addStretch(1)
        self.progress = label("", "secondary")
        top.addWidget(self.progress)
        layout.addLayout(top)
        card = Card(margins=28)
        self.prompt = NotePreview(self._asset_path)
        self.prompt.document().setDefaultFont(theme.ui_font(15))
        self.prompt.setMinimumHeight(110)
        self.prompt.setMaximumHeight(280)
        self.prompt.noteRequested.connect(self.openNote)
        card.body.addWidget(self.prompt)
        self.answer = NotePreview(self._asset_path)
        self.answer.document().setDefaultFont(theme.ui_font(12))
        self.answer.setMaximumHeight(260)
        self.answer.noteRequested.connect(self.openNote)
        card.body.addWidget(self.answer)
        self.source = link_button("")
        self.source.clicked.connect(
            lambda: self.openNote.emit(self.questions[self.position].note_id)
        )
        card.body.addWidget(self.source, 0, Qt.AlignmentFlag.AlignLeft)
        self.feedback = label("", "section")
        card.body.addWidget(self.feedback)
        self.typed = QLineEdit()
        self.typed.setPlaceholderText(_("Type your answer and press Enter"))
        self.typed.returnPressed.connect(self._check_typed)
        card.body.addWidget(self.typed)
        self.choices_row = QVBoxLayout()
        card.body.addLayout(self.choices_row)
        card.body.addStretch(1)
        layout.addWidget(card, 1)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.show_button = accent_button(_("Show answer  (Space)"), self._reveal)
        buttons.addWidget(self.show_button)
        self.grade_buttons = []
        for i, (grade, text) in enumerate(
            (("again", "Again"), ("hard", "Hard"), ("good", "Good"), ("easy", "Easy")), 1
        ):
            b = QPushButton(f"{text}  ({i})")
            b.clicked.connect(lambda _unused=False, g=grade: self._grade(g))
            if grade == "good":
                b.setProperty("accent", True)
            self.grade_buttons.append(b)
            buttons.addWidget(b)
        self.next_button = accent_button(_("Next  (Enter)"), self._next)
        buttons.addWidget(self.next_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        QShortcut(QKeySequence(Qt.Key.Key_Space), page, self._space)
        for i in range(1, 5):
            QShortcut(QKeySequence(str(i)), page, lambda n=i: self._number(n))
        return page

    def _build_summary(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addStretch(1)
        self.summary_title = label("", "title")
        self.summary_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_text = label("", "secondary")
        self.summary_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.summary_title)
        layout.addWidget(self.summary_text)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(
            accent_button(
                _("Back to Review"), lambda: (self.stack.setCurrentIndex(0), self.refresh())
            )
        )
        row.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(2)
        return page

    def _asset_path(self, name: str):
        return self.window.vault.asset_path(name) if self.window.vault else None

    def _renderer(self) -> NoteRenderer:
        vault = self.window.vault
        titles = vault.titles()
        return NoteRenderer(
            vault.resolve_title,
            lambda i: titles.get(i) or "Untitled",
            link_types=vault.link_type_map(),
            allow_new_note_links=False,
        )

    def start_due(self, note_ids: set[str] | None = None) -> None:
        vault = self.window.vault
        notes = {n.id: n for n in vault.all_notes()}
        cards = vault.due_cards(note_ids=note_ids)
        self._start(build_quiz("flashcards", notes, cards, count=500), "flashcards")

    def start_quiz(self) -> None:
        vault = self.window.vault
        ids = self.window.resolve_scope(*self.scope.value())
        notes = {n.id: n for n in vault.all_notes() if n.id in ids}
        mode = self.mode_combo.currentData()
        cards = vault.cards_for_notes(ids)
        self._start(build_quiz(mode, notes, cards, count=self.count.value()), mode)

    def quiz_notes(self, note_ids: set[str]) -> None:
        """Start a quiz on a given set of notes (e.g. a note's neighbourhood)."""
        vault = self.window.vault
        notes = {n.id: n for n in vault.all_notes() if n.id in note_ids}
        cards = vault.cards_for_notes(note_ids)
        mode = "choice" if cards else "notes"
        self._start(build_quiz(mode, notes, cards, count=20), mode)

    def _start(self, questions: list[Question], mode: str) -> None:
        if not questions:
            QMessageBox.information(
                self,
                _("Nothing to review"),
                {
                    "flashcards": _(
                        "No flashcards are due. Great job! Add more from a note's Flashcards tab."
                    ),
                    "notes": _(
                        "“Name that note” needs at least two notes with a title and some text."
                    ),
                }.get(
                    mode,
                    _(
                        "There are no flashcards in this selection. Add flashcards to notes "
                        "first, or choose “Name that note”."
                    ),
                ),
            )
            return
        renderer = self._renderer()
        self.prompt.set_renderer(renderer)
        self.answer.set_renderer(renderer)
        self.questions, self.position, self.score, self.mode = questions, 0, 0, mode
        self.stack.setCurrentIndex(1)
        self._show()

    def _show(self) -> None:
        q = self.questions[self.position]
        self.progress.setText(f"{self.position + 1} / {len(self.questions)}")
        self.prompt.show_markdown(q.prompt)
        self.answer.setVisible(False)
        self.feedback.setText("")
        self.source.setText(_("From: {note_title}").format(note_title=q.note_title))
        self.source.setVisible(False)
        self.typed.setVisible(q.kind == "typed")
        self.typed.clear()
        self.typed.setEnabled(True)
        if q.kind == "typed":
            self.typed.setFocus()
        while self.choices_row.count():
            w = self.choices_row.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.choice_buttons = []
        for i, choice in enumerate(q.choices):
            b = QPushButton(f"{i + 1}.  {choice}")
            b.setStyleSheet("QPushButton { text-align: left; padding: 9px 14px; }")
            b.clicked.connect(lambda _unused=False, n=i: self._choose(n))
            self.choices_row.addWidget(b)
            self.choice_buttons.append(b)
        self.show_button.setVisible(q.kind == "flashcard")
        for b in self.grade_buttons:
            b.setVisible(False)
        self.next_button.setVisible(False)

    def _reveal(self) -> None:
        q = self.questions[self.position]
        self.answer.show_markdown(q.answer)
        self.answer.setVisible(True)
        self.source.setVisible(True)
        self.show_button.setVisible(False)
        if q.kind == "flashcard":
            state = self.window.vault.review_state(q.card_id)
            for b, grade in zip(self.grade_buttons, ("again", "hard", "good", "easy")):
                days = schedule(state, grade).interval
                b.setToolTip(
                    n_("Next review in {n} day", "Next review in {n} days", days).format(n=days)
                )
                b.setVisible(True)
        else:
            self.next_button.setVisible(True)
            self.next_button.setFocus()

    def _grade(self, grade: str) -> None:
        q = self.questions[self.position]
        vault = self.window.vault
        vault.save_review(schedule(vault.review_state(q.card_id), grade))
        self.score += grade != "again"
        self._next()

    def _choose(self, index: int) -> None:
        q = self.questions[self.position]
        if self.next_button.isVisible():
            return
        t = theme.current()
        correct = index == q.correct
        self.score += correct
        for i, b in enumerate(self.choice_buttons):
            if i == q.correct:
                b.setStyleSheet(
                    f"QPushButton {{ text-align: left; padding: 9px 14px; border: 2px solid {t.success}; }}"
                )
            elif i == index:
                b.setStyleSheet(
                    f"QPushButton {{ text-align: left; padding: 9px 14px; border: 2px solid {t.danger}; }}"
                )
        self.feedback.setText(
            _("✓ Correct") if correct else _("✗ Not quite. The correct answer is highlighted.")
        )
        self._reveal()

    def _check_typed(self) -> None:
        q = self.questions[self.position]
        if not self.typed.isEnabled():
            self._next()
            return
        similarity, verdict = grade_typed(self.typed.text(), q.answer)
        self.typed.setEnabled(False)
        self.score += verdict == "correct"
        self.feedback.setText(
            {
                "correct": _("✓ Correct. Answer: {answer}"),
                "close": _("≈ Almost ({similarity} similar). Answer: {answer}"),
                "wrong": _("✗ Not quite. Answer: {answer}"),
            }[verdict].format(answer=q.answer, similarity=f"{similarity:.0%}")
        )
        self._reveal()

    def _next(self) -> None:
        self.position += 1
        if self.position >= len(self.questions):
            self.finish()
        else:
            self._show()

    def finish(self) -> None:
        answered = min(self.position, len(self.questions))
        self.summary_title.setText(
            _("Session complete") if answered >= len(self.questions) else _("Session ended")
        )
        if not answered:
            summary = _("No questions answered.")
        elif self.mode == "flashcards":
            summary = n_("{score} of {n} remembered", "{score} of {n} remembered", answered)
        else:
            summary = n_("{score} of {n} correct", "{score} of {n} correct", answered)
        self.summary_text.setText(summary.format(score=self.score, n=answered))
        self.stack.setCurrentIndex(2)

    def _space(self) -> None:
        if self.stack.currentIndex() == 1 and self.show_button.isVisible():
            self._reveal()

    def _number(self, n: int) -> None:
        if self.stack.currentIndex() != 1:
            return
        if any(b.isVisible() for b in self.grade_buttons):
            self._grade(("again", "hard", "good", "easy")[n - 1])
        elif self.choice_buttons and n <= len(self.choice_buttons):
            self._choose(n - 1)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.next_button.isVisible():
            self._next()
            return
        super().keyPressEvent(event)

    # --- Anki -------------------------------------------------------------

    def check_anki(self) -> None:
        port = settings.get(settings.ANKI_PORT)
        self.anki_state.setText(_("Checking…"))

        def done(version) -> None:
            self.anki_state.setText(_("Connected (AnkiConnect v{version})").format(version=version))

        def failed(message: str) -> None:
            self.anki_state.setText(_("Not connected"))
            QMessageBox.information(self, _("Anki"), message)

        run_task(lambda: AnkiConnect(port).version(), on_done=done, on_error=failed)

    def sync_anki(self) -> None:
        vault = self.window.vault
        ids = self.window.resolve_scope(*self.scope.value())
        cards = vault.cards_for_notes(ids)
        if not cards:
            QMessageBox.information(
                self, _("Anki"), _("There are no flashcards in the chosen scope.")
            )
            return
        deck = self.deck.text().strip() or "ZettelApp"
        settings.put(settings.ANKI_DECK, deck)
        notes = {n.id: n for n in vault.all_notes()}
        renderer = anki_renderer(
            vault.resolve_title, lambda i: notes[i].display_title if i in notes else i
        )
        payloads = build_payloads(cards, notes, vault.vault_id, renderer)
        media = {name: vault.asset_path(name) for p in payloads for name in p.media}
        remembered: list[tuple[int, int | None]] = []
        port = settings.get(settings.ANKI_PORT)
        self.status.emit(_("Syncing {len} cards to Anki…").format(len=len(payloads)))

        def work():
            return AnkiConnect(port).sync(
                payloads, deck, media.get, lambda c, a: remembered.append((c, a))
            )

        def done(report) -> None:
            for card_id, anki_id in remembered:
                vault.set_anki_note_id(card_id, anki_id)
            text = _("Anki sync finished: {added} added, {updated} updated").format(
                added=report.added, updated=report.updated
            )
            if report.failed:
                text += _(", {failed} failed").format(failed=report.failed)
                QMessageBox.warning(self, _("Anki"), text + ".\n\n" + "\n".join(report.errors[:8]))
            self.status.emit(text + ".")
            self.anki_state.setText(_("Connected"))

        def failed(message: str) -> None:
            self.status.emit("")
            QMessageBox.warning(self, _("Anki"), message)

        run_task(work, on_done=done, on_error=failed)
