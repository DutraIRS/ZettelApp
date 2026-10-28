"""The first-run adventure: offered once, solved by really using the app, remembered."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6.QtWidgets")


@pytest.fixture
def window(tmp_path, monkeypatch):
    monkeypatch.setenv("ZETTELAPP_SETTINGS_FILE", str(tmp_path / "settings.ini"))
    from PySide6.QtWidgets import QApplication

    from zettelapp.ui import theme
    from zettelapp.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication(["test"])
    theme.apply_theme(app, "light")
    w = MainWindow()
    w.resize(1280, 800)
    w.show()
    assert w.open_vault(tmp_path / "vault")
    w._create_welcome_notes()
    yield w
    from PySide6.QtCore import QThreadPool

    QThreadPool.globalInstance().waitForDone(20000)
    w.suggestions.pool.waitForDone(20000)
    w.close()


def pump(ms=300):
    from PySide6.QtCore import QEventLoop, QThreadPool, QTimer

    QThreadPool.globalInstance().waitForDone(20000)
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def chapter(window):
    return window.quest.chapter.key if window.quest.chapter else None


def follow_clue(window):
    """The chapter was solved: the card shows its clue; follow it to the next chapter."""
    card = window.quest.card
    assert card.title.text() == "Clue found!" and window.quest.chapter is None
    card.primary.click()


def edit(window, body=None):
    if body is not None:
        window.editor.body.setPlainText(body)
    window.editor._edited()
    window.editor.flush()
    pump(250)


def test_the_adventure_is_offered_on_the_first_run_only(tmp_path, monkeypatch, window):
    from zettelapp.ui import main_window

    monkeypatch.setattr(main_window, "default_vault_dir", lambda: tmp_path / "Documents")
    monkeypatch.setattr(main_window.settings, "get", _without_last_vault(main_window.settings))
    window.open_default_vault()  # a fresh default vault: starter notes and the offer
    assert window.editor.note.title == "Start here"
    pump(1200)
    card = window.quest.card
    assert window.quest.is_visible() and card.title.text() == "The Lost Prince of the Archive"
    assert card.primary.text() == "Begin the adventure" and card.secondary.text() == "Not now"
    card.secondary.click()  # Not now
    assert not window.quest.is_visible() and window.quest.state() == "declined"
    assert "Help ▸ The Lost Prince of the Archive" in window.statusBar().currentMessage()

    window.quest.start_up(first_run=True)  # never offered twice
    window.quest.start_up(first_run=False)
    pump(1200)
    assert not window.quest.is_visible()


def _without_last_vault(module):
    real = module.get

    def get(key, default=None):
        return "" if key == module.LAST_VAULT else real(key, default)

    return get


def test_an_existing_vault_is_not_interrupted(window):
    window.quest.start_up(first_run=False)
    pump(1200)
    assert window.quest.card is None and window.quest.state() == ""


def test_each_chapter_is_solved_by_doing_it(window):
    from conftest import tiny_png
    from PySide6.QtWidgets import QApplication

    from zettelapp.ui.quest import CHAPTER_KEYS

    quest = window.quest
    focus = QApplication.focusWidget()
    quest.offer()
    quest.card.primary.click()  # Begin the adventure
    assert QApplication.focusWidget() is focus  # the card never takes focus
    assert chapter(window) == "journal" and quest.state() == "active"
    assert quest.spotlight.isVisible() and quest.spotlight.rect_now is not None

    window.new_note()  # an untitled note is not enough
    pump(250)
    assert chapter(window) == "journal"
    window.editor.title.setText("The missing prince")
    edit(window)
    follow_clue(window)

    assert chapter(window) == "thread"
    edit(window, "Zetto went missing. [[Start here]]")
    follow_clue(window)

    assert chapter(window) == "marks"
    window.editor.tags.input.setText("clue")
    window.editor.tags._commit()
    edit(window)
    follow_clue(window)

    assert chapter(window) == "reason"
    edit(window, "Zetto went missing. [[Start here]]\n\nsupports:: [[One idea per note]]")
    follow_clue(window)

    assert chapter(window) == "whispers"
    other = window.vault.resolve_title("Mind maps")
    window.side.rejectSuggestion.emit(other)  # dismissing teaches the model too
    pump(250)
    follow_clue(window)

    assert chapter(window) == "map"
    window.show_page(1)
    pump(250)
    follow_clue(window)

    assert chapter(window) == "plan"
    window.show_page(0)
    window.editor.show_mindmap()
    window.editor.mindmap.add_child()  # the root alone is not an idea yet
    window.editor.mindmap.add_child()
    edit(window)
    follow_clue(window)

    assert chapter(window) == "evidence"
    window.editor.tabs.setCurrentIndex(0)
    window.editor.body._insert_image_bytes(tiny_png(), "ada.png")
    edit(window)
    follow_clue(window)

    assert chapter(window) == "riddle"
    window.show_page(3)
    window.review.start_due()
    window.review._reveal()
    window.review._grade("good")
    pump(250)
    follow_clue(window)

    assert chapter(window) == "tower"
    window.show_page(2)
    pump(300)
    assert quest.state() == "finished" and quest.chapter is None
    assert quest.clues() == CHAPTER_KEYS
    assert quest.card.title.text() == "The prince is free!"
    assert quest.card.kicker.text() == "You found 10 clues of 10"
    assert not quest.spotlight.isVisible()
    quest.card.primary.click()
    assert not quest.is_visible()


def test_what_the_reader_does_while_reading_a_clue_counts(window):
    quest = window.quest
    quest.begin()
    window.new_note()
    window.editor.title.setText("Journal")
    edit(window)
    edit(window, "[[Start here]]")  # done before following the clue
    follow_clue(window)
    pump(250)
    assert quest.card.title.text() == "Clue found!"  # chapter 2 solved at once
    assert quest.clues() == ["journal", "thread"]


def test_progress_is_remembered_paused_and_resumed(window):
    from zettelapp.ui.main_window import MainWindow

    quest = window.quest
    quest.begin()
    quest.skip()
    assert chapter(window) == "thread" and quest.clues() == []  # skipped, not found
    quest.card.close_button.click()  # ✕ pauses
    assert not quest.is_visible() and quest.state() == "paused"
    assert "Resume it any time" in window.statusBar().currentMessage()
    edit(window, "Linked while paused: [[One idea per note]]")  # doesn't count
    quest.menu_action.trigger()  # Help ▸ The Lost Prince of the Archive
    assert quest.is_visible() and chapter(window) == "thread"
    assert quest.restart_action.isEnabled()

    # ZettelApp closes with the adventure open, and starts again later.
    second = MainWindow()
    second.show()
    assert second.open_vault(window.vault.folder)
    second.quest.start_up(first_run=False)
    pump(1200)
    assert second.quest.is_visible() and second.quest.chapter.key == "thread"
    assert second.quest.card.dots.states[:3] == ["skipped", "current", "todo"]
    second.quest.restart_action.trigger()  # back to the prologue
    assert second.quest.card.primary.text() == "Begin the adventure"
    second.quest.card.primary.click()
    assert second.quest.chapter.key == "journal" and second.quest.clues() == []
    second.close()


def test_the_card_keeps_clear_of_the_control_it_points_at(window):
    quest = window.quest
    quest.begin()
    for _unused in range(4):
        quest.skip()
    assert chapter(window) == "whispers"
    window.open_note(window.vault.resolve_title("Tags gather notes"))
    window.suggestions.pool.waitForDone(20000)
    pump(500)
    target = quest.spotlight.rect_now
    assert target is not None and target.left() > window.width() / 2  # the side panel
    assert not quest.card.geometry().intersects(target)


def test_the_card_paints_with_and_without_illustrations(window, tmp_path, monkeypatch):
    from conftest import tiny_png

    from zettelapp.ui import quest_card

    monkeypatch.setattr(quest_card, "resource_path", lambda *p: tmp_path.joinpath("resources", *p))
    quest = window.quest
    quest.offer()
    assert quest.card.hero.pixmap is None  # missing illustrations use a tinted glyph
    assert not quest.card.grab().isNull()
    (tmp_path / "resources" / "quest").mkdir(parents=True)
    (tmp_path / "resources" / "quest" / "journal.png").write_bytes(tiny_png((200, 120, 40)))
    quest.begin()
    quest.card.hint_button.click()
    assert quest.card.hint.isVisible() and quest.card.hero.pixmap is not None
    image = quest.card.grab().toImage()
    assert image.pixelColor(image.width() // 2, 40).name() == "#c87828"  # the picture fills
    pump(200)
    window.grab()  # the spotlight paints over the window
    quest.skip()
    assert quest.card.hero.pixmap is None
    window.grab()


def test_bundled_quest_illustrations_are_complete():
    from PySide6.QtGui import QImage

    from zettelapp.paths import resource_path
    from zettelapp.ui.quest import CHAPTERS

    names = ["prologue", *(chapter.key for chapter in CHAPTERS), "finale"]
    assert len(names) == 12
    for name in names:
        path = resource_path("quest", f"{name}.png")
        image = QImage(str(path))
        assert not image.isNull(), name
        assert (image.width(), image.height()) == (1200, 400), name
        assert path.stat().st_size < 400_000, name
