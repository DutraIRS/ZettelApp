"""The Lost Prince of the Archive: an optional adventure that teaches ZettelApp.

Ten chapters each point at one feature. The app notices when the reader has really used
it (a note created, a link written, the graph opened, a card reviewed…) by comparing a
snapshot of the vault or window taken when the chapter began with the state after each
change, so there is never an "I did it" button. Solving a chapter reveals the clue that
leads to the next one. Progress lives in settings: the adventure is offered once, when
the first vault is created, and can be resumed or restarted from the Help menu.

Text is translated when shown; the story is kept in short pieces for translators.
Illustrations are optional files in resources/quest (see docs/quest-images.md); without
them the card draws a tinted glyph.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QTabBar, QToolButton

from zettelapp import settings
from zettelapp.core.starter import QUEST_TITLE
from zettelapp.core.starter import TITLES as STARTER_TITLES
from zettelapp.i18n import N_, _, n_
from zettelapp.ui import icons
from zettelapp.ui.quest_card import CardContent, QuestCard, Spotlight, Target

if TYPE_CHECKING:
    from zettelapp.ui.main_window import MainWindow

OFFER_DELAY_MS = 900

# Pages of the main window's stack, in navigation order.
NOTES_PAGE, GRAPH_PAGE, INSIGHTS_PAGE, REVIEW_PAGE = 0, 1, 2, 3

_MEDIA_RE = re.compile(r"\]\(\s*<?((?:asset|file):[^)>\s]+)")


# --- what the app looks like now (snapshots compared before and after) ------------------


def _titled_notes(w: MainWindow) -> set[str]:
    return {n.id for n in w.vault.all_notes() if n.title.strip()}


def _links(w: MainWindow) -> set[tuple[str, str, str]]:
    return {(link.src, link.dst, link.type) for link in w.vault.all_links()}


def _typed_links(w: MainWindow) -> set[tuple[str, str, str]]:
    return {key for key in _links(w) if key[2] != "related"}


def _tags(w: MainWindow) -> set[tuple[str, str]]:
    return {(n.id, tag) for n in w.vault.all_notes() for tag in n.tags}


def _feedback(w: MainWindow) -> set[tuple[tuple[str, str], int]]:
    return set(w.vault.feedback().items())


def _mindmap_sizes(w: MainWindow) -> dict[str, int]:
    def size(node: dict) -> int:
        return 1 + sum(size(child) for child in node.get("children", []))

    return {n.id: size(n.mindmap) for n in w.vault.all_notes() if n.mindmap}


def _media(w: MainWindow) -> set[tuple[str, str]]:
    found = set()
    for note in w.vault.all_notes():
        found.update((note.id, target) for target in _MEDIA_RE.findall(note.body))
        if note.image:
            found.add((note.id, "picture:" + note.image))
    return found


def _reviews(w: MainWindow) -> set[tuple]:
    rows = w.vault.conn.execute("SELECT card_id, reps, lapses, interval, due FROM reviews")
    return {tuple(row) for row in rows}


def _new(before: set, now: set) -> bool:
    return bool(now - before)


def _mindmap_grew(before: dict[str, int], now: dict[str, int]) -> bool:
    return any(size >= 2 and size > before.get(note, 0) for note, size in now.items())


def _page(index: int) -> Callable[[MainWindow], bool]:
    return lambda w: w.pages.currentIndex() == index


def _shown(_before: bool, now: bool) -> bool:
    return now


# --- where to point -------------------------------------------------------------------------


def _in_note(inner: Callable[[MainWindow], Target | None]) -> Callable[[MainWindow], Target]:
    """Point at *inner* inside the open note, or at how to get there first."""

    def resolve(w: MainWindow) -> Target:
        if w.pages.currentIndex() != NOTES_PAGE:
            return w.nav.buttons[NOTES_PAGE]
        if w.editor.note is None:
            return w.list.view if w.list.model.rows else w.list.new_button
        return inner(w) or w.editor

    return resolve


def _nav(index: int) -> Callable[[MainWindow], Target]:
    return lambda w: w.nav.buttons[index]


def _suggestion_target(w: MainWindow) -> Target | None:
    from zettelapp.ui.side_panel import _SuggestionRow

    for row in w.side.findChildren(_SuggestionRow):
        for button in row.findChildren(QToolButton):
            if button.popupMode() == QToolButton.ToolButtonPopupMode.MenuButtonPopup:
                return button  # the first suggestion's Link button
    return w.side


def _mindmap_target(w: MainWindow) -> Target | None:
    tabs = w.editor.tabs
    if tabs.currentIndex() != 1:
        bar: QTabBar = tabs.tabBar()
        return bar, bar.tabRect(1)
    buttons = tabs.widget(1).findChildren(QToolButton)
    return buttons[0] if buttons else w.editor.mindmap  # Add idea comes first


def _review_target(w: MainWindow) -> Target:
    review = w.review
    if w.pages.currentIndex() != REVIEW_PAGE:
        return w.nav.buttons[REVIEW_PAGE]
    if review.stack.currentIndex() == 1:
        if review.show_button.isVisible():
            return review.show_button
        visible = [b for b in review.grade_buttons if b.isVisible()]
        return visible[2] if len(visible) > 2 else (visible[0] if visible else review)
    return review.due_count.parentWidget()  # the "Due today" card with Start review


# --- the story ------------------------------------------------------------------------------


@dataclass(frozen=True)
class Chapter:
    key: str  # also the illustration's file name: resources/quest/<key>.png
    glyph: str  # shown when the illustration is missing
    title: str
    story: tuple[str, ...]
    task: str
    hint: str
    clue: tuple[str, ...]
    probe: Callable[[MainWindow], Any]
    solved: Callable[[Any, Any], bool]
    target: Callable[[MainWindow], Target | None]


CHAPTERS: list[Chapter] = [
    Chapter(
        "journal",
        "edit",
        N_("The Archivist's Journal"),
        (
            N_(
                "“Rule one of the Archive,” says Quill: “what isn't written down is lost to the Fog.”"
            ),
            N_("“Start a journal of your search.”"),
        ),
        N_("Create a new note and give it a title, for example “The missing prince”."),
        N_(
            "Click New above the note list, or press Ctrl+N. The title goes at the top of the note."
        ),
        (
            N_(
                "Ink spreads across your note and forms words that aren't yours: “Follow the silver threads. — A.”"
            ),
        ),
        _titled_notes,
        _new,
        lambda w: w.list.new_button if w.pages.currentIndex() == NOTES_PAGE else _nav(0)(w),
    ),
    Chapter(
        "thread",
        "link",
        N_("The Silver Thread"),
        (
            N_("Silver threads are links: they tie one note to another."),
            N_("The Fog can't swallow a note that is tied to others."),
        ),
        N_("Link a note to another one: in its text, type [[ and pick a title, such as {example}."),
        N_(
            "Type two square brackets, a few letters of a title, then press Enter. Ctrl+K picks a note from a list."
        ),
        (
            N_(
                "The thread pulls tight. You follow it into the stacks, where every shelf bears a mark."
            ),
            N_("One mark is scratched in silver: a #."),
        ),
        _links,
        _new,
        _in_note(lambda w: w.editor.body),
    ),
    Chapter(
        "marks",
        "tag",
        N_("Marks on the Shelves"),
        (
            N_("Archivists mark their notes so they can gather them later."),
            N_("Zetto marked every note he wrote."),
        ),
        N_("Give a note a tag."),
        N_(
            "Click Add tag under the title, type a word and press Enter. Or write a word with # in front of it in the text."
        ),
        (
            N_("Your mark glows, and the shelf slides aside."),
            N_("Behind it is a card in Zetto's hand: “A thread is strongest when it says why.”"),
        ),
        _tags,
        _new,
        _in_note(lambda w: w.editor.tags.input),
    ),
    Chapter(
        "reason",
        "relationship",
        N_("Threads That Say Why"),
        (
            N_("A plain thread only says that two notes are related."),
            N_(
                "Zetto's threads said how: one note supports another, extends it, or is part of it."
            ),
        ),
        N_("Make a typed link: write a link type and two colons before a link, like {example}."),
        N_(
            "The types are supports, contradicts, extends, example, part_of and cites. Add link… in the side panel lets you choose one too."
        ),
        (
            N_("Your thread hums with meaning."),
            N_("All around you, the shelves begin to whisper the names of notes…"),
        ),
        _typed_links,
        _new,
        _in_note(lambda w: w.editor.body),
    ),
    Chapter(
        "whispers",
        "lightbulb",
        N_("The Whispering Shelves"),
        (
            N_(
                "The Archive knows which notes belong together, and whispers them to those who listen."
            ),
            N_("It learns from every answer you give."),
        ),
        N_(
            "Under Suggested links on the right, click Link to accept a suggestion, or ✕ to dismiss one."
        ),
        N_(
            "Suggestions need a note with a few sentences. If none appear, open another note or write a little more."
        ),
        (N_("The whispers fade, all but one: “Climb to the Map Room and see the Archive whole.”"),),
        _feedback,
        _new,
        _in_note(_suggestion_target),
    ),
    Chapter(
        "map",
        "graph",
        N_("The Map Room"),
        (
            N_("From the Map Room you can see the whole Archive at once."),
            N_("Every note is a star, and every link a line between two stars."),
        ),
        N_("Open the Graph."),
        N_("Click Graph in the bar on the left, or press Ctrl+2."),
        (
            N_(
                "Near your notes, a tiny drawing flickers on the map: a branching tree in Zetto's hand."
            ),
            N_("It's his plan!"),
        ),
        _page(GRAPH_PAGE),
        _shown,
        _nav(GRAPH_PAGE),
    ),
    Chapter(
        "plan",
        "mindmap",
        N_("Zetto's Branching Plan"),
        (
            N_(
                "Zetto sketched his plans as mind maps: one idea in the middle, branches all around."
            ),
            N_("Add a branch of your own."),
        ),
        N_("Open a note's Mind map tab and add an idea."),
        N_(
            "Click Mind map above the note text, then Add idea. In the map, Tab adds a child idea and Enter a sibling."
        ),
        (
            N_(
                "Your new branch points east, to the gallery where Zetto pinned his evidence to the walls."
            ),
        ),
        _mindmap_sizes,
        _mindmap_grew,
        _in_note(_mindmap_target),
    ),
    Chapter(
        "evidence",
        "image",
        N_("Evidence on the Wall"),
        (
            N_("Pictures, documents and sources are evidence."),
            N_("Pin them to your notes, and the Fog can't take them."),
        ),
        N_("Add a picture to a note, or link a file."),
        N_(
            "Copy an image and press Ctrl+V in the text, or use Insert image or Link to a file on the toolbar above the note."
        ),
        (
            N_("Behind your evidence, a stone door appears, carved with a riddle."),
            N_("It opens only for those who remember."),
        ),
        _media,
        _new,
        _in_note(lambda w: w.editor.body),
    ),
    Chapter(
        "riddle",
        "review",
        N_("The Riddle Door"),
        (
            N_("Forgetting is the Fog's only weapon."),
            N_("Flashcards turn it back: every answer you recall makes a memory stronger."),
        ),
        N_(
            "Review a flashcard: open Review, click Start review, show the answer and grade yourself."
        ),
        N_(
            "Space shows the answer, and keys 1 to 4 grade it. Nothing due? Write a Q: line and an A: line in a note first."
        ),
        (N_("The door swings open onto a spiral stair. At the top shines the Tower of Insight."),),
        _reviews,
        _new,
        _review_target,
    ),
    Chapter(
        "tower",
        "insights",
        N_("The Tower of Insight"),
        (
            N_("From the tower, the whole Archive can be counted: every note, link and tag."),
            N_("What is counted can't hide in the Fog."),
        ),
        N_("Open Insights."),
        N_("Click Insights in the bar on the left, or press Ctrl+3."),
        (),
        _page(INSIGHTS_PAGE),
        _shown,
        _nav(INSIGHTS_PAGE),
    ),
]
CHAPTER_KEYS = [c.key for c in CHAPTERS]

PROLOGUE = (
    N_(
        "The Fog of Forgetting has crept into the Great Archive. Whatever isn't written down and linked fades into grey."
    ),
    N_("Prince Zetto, keeper of the Archive, went in after it and hasn't come back."),
    N_(
        "His owl, Quill, lands on your desk: “Only a fox's nose can find him. Each clue hides in a corner of this app. Will you help?”"
    ),
)
FINALE = (
    N_(
        "Counted, linked and remembered, your Archive leaves the Fog nowhere to hide. It thins and fades, and Prince Zetto steps out of the mist."
    ),
    N_(
        "“You found me by following links,” he smiles. “Write one idea per note, link it with a reason, and the Fog will never return.”"
    ),
    N_(
        "Beyond the Archive's walls, Ask answers questions from your notes with an AI of your choice, and MCP lets AI agents read them."
    ),
)


def _example(key: str) -> str:
    """A [[link]] to a starter note, in the reader's language, for the tasks' examples."""
    title = _(STARTER_TITLES["atomic" if key == "reason" else "hub"])
    return f"supports:: [[{title}]]" if key == "reason" else f"[[{title}]]"


def _lines(pieces: tuple[str, ...]) -> str:
    return "\n".join(_(piece) for piece in pieces)


class Quest(QObject):
    """Runs the adventure: shows the card, watches the app and remembers progress."""

    def __init__(self, window: MainWindow):
        super().__init__(window)
        self.window = window
        self.card: QuestCard | None = None
        self.spotlight = Spotlight(window)
        self.spotlight.target_moved = self._target_moved
        self.chapter: Chapter | None = None  # the chapter being played, if any
        self.baseline: Any = None
        self._vault = None
        self.menu_action: QAction | None = None
        self.restart_action: QAction | None = None
        self.check_timer = QTimer(self, singleShot=True, interval=150, timeout=self.check)
        window.pages.currentChanged.connect(lambda *_args: self.check_timer.start())
        window.installEventFilter(self)

    # --- state ------------------------------------------------------------------------

    @staticmethod
    def state() -> str:
        return settings.get(settings.QUEST_STATE) or ""

    def _set_state(self, state: str) -> None:
        settings.put(settings.QUEST_STATE, state)
        if self.menu_action is not None:
            self._update_menu()

    @staticmethod
    def clues() -> list[str]:
        return [k for k in settings.get_list(settings.QUEST_CLUES) if k in CHAPTER_KEYS]

    def current_index(self) -> int:
        key = settings.get(settings.QUEST_CHAPTER) or ""
        return CHAPTER_KEYS.index(key) if key in CHAPTER_KEYS else 0

    def _progress(self, current: int) -> list[str]:
        """A state per chapter for the dots; *current* is the chapter being played."""
        found = set(self.clues())
        return [
            "found"
            if key in found
            else "current"
            if i == current
            else "skipped"
            if i < current
            else "todo"
            for i, key in enumerate(CHAPTER_KEYS)
        ]

    # --- entry points ------------------------------------------------------------------

    def start_up(self, first_run: bool) -> None:
        """Called once the start-up vault is open: offer the adventure on the very first
        run, or bring back an adventure that was in progress when ZettelApp closed."""
        if first_run and not self.state():
            QTimer.singleShot(OFFER_DELAY_MS, self.offer)
        elif self.state() == "active":
            QTimer.singleShot(OFFER_DELAY_MS, self.resume)

    def attach(self, vault) -> None:
        """Watch *vault* (called whenever a vault is opened)."""
        self._vault = vault
        vault.listeners.append(lambda _kind: self.check_timer.start())
        if self.chapter is not None:
            self._begin(CHAPTER_KEYS.index(self.chapter.key))

    def offer(self) -> None:
        """The prologue, with "Begin the adventure" and "Not now"."""
        self._leave_chapter()
        self._show(
            CardContent(
                image="prologue.png",
                glyph="flag",
                kicker=_("An optional adventure · about 10 minutes"),
                title=_(QUEST_TITLE),
                story=_lines(PROLOGUE),
                primary=(_("Begin the adventure"), self.begin),
                secondary=(_("Not now"), self.decline),
            ),
            on_close=self.decline,
        )

    def begin(self) -> None:
        settings.put(settings.QUEST_CLUES, [])
        settings.put(settings.QUEST_CHAPTER, CHAPTER_KEYS[0])
        self._set_state("active")
        self._begin(0)

    def resume(self) -> None:
        if self.window.vault is None:
            return
        self._set_state("active")
        self._begin(self.current_index())

    def decline(self) -> None:
        if not self.state():
            self._set_state("declined")
        self.hide()
        self._status(_("You can start the adventure any time from Help ▸ {title}."))

    def pause(self) -> None:
        """✕ on a chapter: hide the card and keep the progress."""
        self._set_state("paused")
        self.hide()
        self._status(_("The adventure is paused. Resume it any time from Help ▸ {title}."))

    def skip(self) -> None:
        """Move on to the next chapter without solving this one."""
        if self.chapter is not None:
            self._advance(CHAPTER_KEYS.index(self.chapter.key), solved=False)

    def play_from_menu(self) -> None:
        if self.state() in ("active", "paused"):
            self.resume()
        else:
            self.offer()

    def restart(self) -> None:
        settings.put(settings.QUEST_CLUES, [])
        settings.put(settings.QUEST_CHAPTER, CHAPTER_KEYS[0])
        self.offer()

    def hide(self) -> None:
        self._leave_chapter()
        if self.card is not None:
            self.card.hide()

    def is_visible(self) -> bool:
        return self.card is not None and self.card.isVisible()

    # --- chapters ------------------------------------------------------------------------

    def _begin(self, index: int) -> None:
        chapter = CHAPTERS[index]
        self.chapter = chapter
        self.baseline = self._probe(chapter)
        self._show_chapter(index)
        self.spotlight.point_at(lambda: self._target(chapter))
        self.check_timer.start()  # it may be solved already (an eager reader)

    def _show_chapter(self, index: int) -> None:
        chapter = CHAPTERS[index]
        self._show(
            CardContent(
                image=f"{chapter.key}.png",
                glyph=chapter.glyph,
                kicker=_("Chapter {n} of {total}").format(n=index + 1, total=len(CHAPTERS)),
                title=_(chapter.title),
                story=_lines(chapter.story),
                task=_(chapter.task).format(example=_example(chapter.key)),
                hint=_(chapter.hint),
                hint_label=_("Need a hint?"),
                progress=self._progress(index),
                secondary=(_("Skip this step"), self.skip),
            ),
            on_close=self.pause,
        )

    def _leave_chapter(self) -> None:
        self.chapter = None
        self.baseline = None
        self.spotlight.stop()

    def _probe(self, chapter: Chapter) -> Any:
        if self.window.vault is None:
            return None
        try:
            return chapter.probe(self.window)
        except Exception:  # noqa: BLE001 - the adventure must never break the app
            return None

    def check(self) -> None:
        """Has the reader done what the current chapter asks?"""
        chapter = self.chapter
        if chapter is None or not self.is_visible():
            return
        now = self._probe(chapter)
        if self.baseline is None:
            self.baseline = now
            return
        try:
            solved = now is not None and chapter.solved(self.baseline, now)
        except Exception:  # noqa: BLE001 - the adventure must never break the app
            solved = False
        if solved:
            self._advance(CHAPTER_KEYS.index(chapter.key), solved=True)

    def _advance(self, index: int, solved: bool) -> None:
        chapter = CHAPTERS[index]
        self._leave_chapter()
        if solved:
            settings.put(settings.QUEST_CLUES, [*self.clues(), chapter.key])
        if index + 1 >= len(CHAPTERS):
            self._set_state("finished")
            self._finale()
            return
        nxt = index + 1
        settings.put(settings.QUEST_CHAPTER, CHAPTER_KEYS[nxt])
        if not solved:
            self._begin(nxt)
            return
        # The clue: the next chapter's snapshot is taken now, so what the reader does
        # while reading counts.
        upcoming = CHAPTERS[nxt]
        baseline = self._probe(upcoming)
        self._show(
            CardContent(
                image=f"{chapter.key}.png",
                glyph="star",
                kicker=_("Chapter {n} of {total}").format(n=index + 1, total=len(CHAPTERS)),
                title=_("Clue found!"),
                story=_lines(chapter.clue),
                progress=self._progress(index),
                primary=(_("Follow the clue"), lambda: self._continue(nxt, baseline)),
            ),
            on_close=self.pause,
        )

    def _continue(self, index: int, baseline: Any) -> None:
        self._begin(index)
        if baseline is not None:
            self.baseline = baseline
            self.check()

    def _finale(self) -> None:
        found = len(self.clues())
        self._show(
            CardContent(
                image="finale.png",
                glyph="heart",
                kicker=n_(
                    "You found {n} clue of {total}", "You found {n} clues of {total}", found
                ).format(n=found, total=len(CHAPTERS)),
                title=_("The prince is free!"),
                story=_lines(FINALE),
                progress=self._progress(len(CHAPTERS)),
                primary=(_("The end"), self.hide),
            ),
            on_close=self.hide,
        )

    # --- the card --------------------------------------------------------------------------

    def _show(self, content: CardContent, on_close: Callable[[], None]) -> None:
        if self.card is None:
            self.card = QuestCard(self.window, lambda: self._on_close(), _("Close"))
        self._close_action = on_close
        self.card.set_content(content)
        self.card.show()
        self.card.reposition(self.spotlight.rect_now)

    def _on_close(self) -> None:
        self._close_action()

    def _target(self, chapter: Chapter) -> Target | None:
        try:
            return chapter.target(self.window)
        except Exception:  # noqa: BLE001
            return None

    def _target_moved(self, rect) -> None:
        if self.is_visible():
            self.card.reposition(rect)

    def _status(self, text: str) -> None:
        self.window.statusBar().showMessage(text.format(title=_(QUEST_TITLE)), 10000)

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if watched is self.window and event.type() == QEvent.Type.Resize:
            self.spotlight.setGeometry(self.window.rect())
            if self.is_visible():
                self.card.reposition()
        return False

    # --- menu ----------------------------------------------------------------------------------

    def add_menu_actions(self, menu: QMenu) -> None:
        """Help ▸ <the adventure> (begin or resume) and Restart the Adventure."""
        title = _(QUEST_TITLE).replace("&", "&&")
        self.menu_action = QAction(icons.icon("flag"), title, menu)
        self.menu_action.triggered.connect(lambda *_args: self.play_from_menu())
        self.restart_action = QAction(_("Restart the Adventure"), menu)
        self.restart_action.triggered.connect(lambda *_args: self.restart())
        menu.addAction(self.menu_action)
        menu.addAction(self.restart_action)
        menu.aboutToShow.connect(self._update_menu)
        self._update_menu()

    def _update_menu(self) -> None:
        playing = self.state() in ("active", "paused")
        self.menu_action.setStatusTip(
            _("Resume the adventure where you left it")
            if playing
            else _("A short adventure through ZettelApp's features")
        )
        self.restart_action.setEnabled(playing or self.state() == "finished")
