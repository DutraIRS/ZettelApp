"""Bold and italics in the editor and preview, and picking a note after [[."""

# ruff: noqa: F811  (the `window` fixture is imported, then used as a test argument)

import os

import pytest

from zettelapp.core.textutil import emphasis_spans

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _spans(line):
    return [(line[s:e], "bold" if bold else "italic") for s, e, bold in emphasis_spans(line)]


def test_bold_inside_italics_nests_like_the_preview():
    line = "*Pedro está aqui. **Ele** diz que quer falar **contigo**.*"
    assert _spans(line) == [("**Ele**", "bold"), ("**contigo**", "bold"), (line, "italic")]
    assert _spans("***both***") == [("**both**", "bold"), ("***both***", "italic")]
    assert _spans("**a *b* c**") == [("*b*", "italic"), ("**a *b* c**", "bold")]


@pytest.mark.parametrize(
    "line",
    ["snake_case_name", "2 * 3 * 4", "* a list item", "**Ele **", "\\*not\\*", "`*code*`"],
)
def test_text_that_is_not_emphasis_stays_plain(line):
    assert emphasis_spans(line) == []


def test_links_formulas_and_code_keep_their_asterisks():
    line = "[[Note *x*]] $a*b*c$ [*t*](http://a/*b*) `*c*` *y*"
    assert _spans(line) == [("*t*", "italic"), ("*y*", "italic")]
    # CommonMark's rule of three: the ** in the middle is plain text.
    assert _spans("*foo**bar*") == [("*foo**bar*", "italic")]


# --- the editor -------------------------------------------------------------------------


@pytest.fixture
def editor():
    from PySide6.QtWidgets import QApplication

    from zettelapp.ui.markdown_editor import MarkdownEditor

    QApplication.instance() or QApplication(["test"])
    ed = MarkdownEditor(lambda data, name: "x.png")
    ed.resize(500, 300)
    ed.show()
    yield ed
    ed.close()
    ed.deleteLater()


def _format_at(ed, pos):
    from PySide6.QtGui import QTextCharFormat

    block = ed.document().findBlock(pos)
    for r in block.layout().formats():
        if r.start <= pos - block.position() < r.start + r.length:
            return QTextCharFormat(r.format)  # a copy: the range is gone after the loop
    return None


def test_the_editor_shows_bold_inside_italics_as_bold_italic(editor):
    from zettelapp.ui import theme

    line = "*Pedro está aqui. **Ele** diz que quer falar **contigo**.*"
    editor.setPlainText(line)
    plain, bold = _format_at(editor, line.index("Pedro")), _format_at(editor, line.index("Ele"))
    assert plain.fontItalic() and plain.fontWeight() < 600
    assert bold.fontItalic() and bold.fontWeight() >= 600
    # Segoe UI Variable has no bold italic face; italics use a family that has one.
    assert bold.fontFamilies() == theme.ITALIC_FONTS


def test_italics_inside_a_heading_keep_the_heading_size(editor):
    editor.setPlainText("# A *big* title")
    title, word = _format_at(editor, 2), _format_at(editor, 5)
    assert word.fontItalic() and word.fontPointSize() == title.fontPointSize() > 11


def _select(ed, text, part):
    from PySide6.QtGui import QTextCursor

    ed.setPlainText(text)
    cursor = ed.textCursor()
    cursor.setPosition(text.index(part))
    cursor.setPosition(text.index(part) + len(part), QTextCursor.MoveMode.KeepAnchor)
    ed.setTextCursor(cursor)


def _selected(ed):
    return ed.textCursor().selectedText().replace(" ", "\n")


def test_bold_leaves_spaces_outside_and_keeps_the_text_selected(editor):
    _select(editor, "Pedro está aqui.", "está ")
    editor.toggle_emphasis("**")
    assert editor.toPlainText() == "Pedro **está** aqui."
    assert _selected(editor) == "está"
    editor.toggle_emphasis("*")  # bold and italics combine
    assert editor.toPlainText() == "Pedro ***está*** aqui."


@pytest.mark.parametrize("part", ["está", "**está**", "*está**"])
def test_pressing_bold_again_takes_it_off(editor, part):
    _select(editor, "Pedro **está** aqui.", part)
    editor.toggle_emphasis("**")
    assert editor.toPlainText() == "Pedro está aqui."
    assert _selected(editor) == "está"


def test_italics_come_off_bold_italics_and_leave_the_bold(editor):
    _select(editor, "a ***b*** c", "b")
    editor.toggle_emphasis("*")
    assert editor.toPlainText() == "a **b** c"
    editor.toggle_emphasis("**")
    assert editor.toPlainText() == "a b c"


def test_each_line_is_formatted_without_its_list_or_heading_marks(editor):
    text = "- [ ] task\n## Heading\n> quote\nQ: question\n\n1. item"
    _select(editor, text, text)
    editor.toggle_emphasis("**")
    assert editor.toPlainText() == (
        "- [ ] **task**\n## **Heading**\n> **quote**\nQ: **question**\n\n1. **item**"
    )
    editor.toggle_emphasis("**")
    assert editor.toPlainText() == text


def test_a_word_inside_snake_case_gets_italics_instead_of_losing_its_underscores(editor):
    _select(editor, "snake_case_name", "case")
    editor.toggle_emphasis("*")
    assert editor.toPlainText() == "snake_*case*_name"


def test_bold_without_a_selection_inserts_markers_and_a_second_press_removes_them(editor):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor.setPlainText("ab")
    cursor = editor.textCursor()
    cursor.setPosition(1)
    editor.setTextCursor(cursor)
    QTest.keyClick(editor, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
    assert (editor.toPlainText(), editor.textCursor().position()) == ("a****b", 3)
    QTest.keyClick(editor, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier)
    assert (editor.toPlainText(), editor.textCursor().position()) == ("ab", 1)


def test_one_undo_takes_back_a_whole_format(editor):
    _select(editor, "one\ntwo", "one\ntwo")
    editor.toggle_emphasis("**")
    editor.undo()
    assert editor.toPlainText() == "one\ntwo"


# --- [[ completion ------------------------------------------------------------------------


def _suggestions(ed):
    model = ed.matches_model
    return [model.index(i, 0).data() for i in range(model.rowCount())]


def test_the_best_match_comes_first_and_is_highlighted(editor):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor.set_titles(["Pronomes subjetivos", "Substantivos", "Ação", "Sub"])
    editor.setFocus()
    QTest.keyClicks(editor, "Veja [[sub")
    popup = editor.completer.popup()
    assert popup.isVisible()
    assert _suggestions(editor) == ["Sub", "Substantivos", "Pronomes subjetivos"]
    assert popup.currentIndex().data() == "Sub"
    QTest.keyClick(popup, Qt.Key.Key_Down)
    QTest.keyClick(popup, Qt.Key.Key_Return)
    assert editor.toPlainText() == "Veja [[Substantivos]]"
    assert not popup.isVisible()


def test_completion_ignores_accents(editor):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    editor.set_titles(["Ação", "Outra"])
    editor.setFocus()
    QTest.keyClicks(editor, "[[acao")
    QTest.keyClick(editor.completer.popup(), Qt.Key.Key_Tab)
    assert editor.toPlainText() == "[[Ação]]"


def test_an_autosave_does_not_reset_the_note_being_picked(window):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    for title in ("Substantivos", "Pronomes", "Subjuntivo"):
        window.vault.create_note(title, "text")
    note = window.vault.create_note("Gramática", "")
    window.open_note(note.id)
    window._refresh_after_save()
    body = window.editor.body
    body.setFocus()
    QTest.keyClicks(body, "[[Sub")
    popup = body.completer.popup()
    QTest.keyClick(popup, Qt.Key.Key_Down)
    assert popup.currentIndex().data() == "Substantivos"
    window.editor.flush()  # what the autosave timer does; it refreshes the titles
    assert popup.isVisible() and popup.currentIndex().data() == "Substantivos"
    QTest.keyClick(popup, Qt.Key.Key_Return)
    assert body.toPlainText() == "[[Substantivos]]"


# --- preview and toolbar ------------------------------------------------------------------


def test_the_preview_draws_bold_inside_italics_in_a_font_with_bold_italics():
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication

    from zettelapp.core.render import NoteRenderer
    from zettelapp.ui import theme
    from zettelapp.ui.preview import NotePreview

    QApplication.instance() or QApplication(["test"])
    preview = NotePreview(lambda name: None)
    preview.set_renderer(NoteRenderer(lambda target: None))
    preview.show_markdown("*Pedro está aqui. **Ele** diz.*")
    block = preview.document().begin()
    formats = {}
    it = block.begin()
    while not it.atEnd():
        formats[it.fragment().text()] = it.fragment().charFormat()
        it += 1
    bold = formats["Ele"]
    assert bold.fontItalic() and bold.fontWeight() == QFont.Weight.Bold.value
    assert bold.fontFamilies() == theme.ITALIC_FONTS


def test_bold_and_italic_buttons_use_the_letters_windows_uses_in_each_language():
    from zettelapp.i18n import LANGUAGES
    from zettelapp.ui import icons

    assert icons.format_glyphs("en") == ("bold", "italic")
    assert icons.format_glyphs("pt_BR") == ("bold_n", "italic")  # N de negrito
    assert icons.format_glyphs("de") == ("bold_f", "italic_k")
    for code in LANGUAGES:
        assert all(name in icons.GLYPHS for name in icons.format_glyphs(code))


from tests.test_ui_smoke import window  # noqa: E402, F401


@pytest.mark.parametrize(
    ("line", "part", "marker", "result"),
    [
        # The ending of an italic word, taken out of the italics (_ can't close mid-word).
        ("(ex.: _homo novos_ / x)", "os", "*", "(ex.: *homo nov*os / x)"),
        ("_homo novos_", "homo", "*", "homo *novos*"),
        ("*a b c*", "b", "*", "*a* b *c*"),
        ("**bold words here**", "words", "**", "**bold** words **here**"),
    ],
)
def test_the_button_takes_emphasis_off_part_of_a_longer_stretch(editor, line, part, marker, result):
    from zettelapp.core.render import NoteRenderer

    _select(editor, line, part)
    editor.toggle_emphasis(marker)
    assert editor.toPlainText() == result
    assert _selected(editor) == part
    html = NoteRenderer(lambda _t: None).render(result)
    assert f"<em>{part}" not in html and f"<strong>{part}" not in html
    editor.toggle_emphasis(marker)  # and back on, around that part
    assert part in editor.toPlainText()


def test_italics_inside_italics_come_off_instead_of_nesting(editor):
    _select(editor, "_homo nov*os*_", "os")
    editor.toggle_emphasis("*")
    assert editor.toPlainText() == "_homo novos_"


def test_alt_click_adds_carets_that_type_delete_and_move_together(editor):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QTextCursor
    from PySide6.QtTest import QTest

    editor.setPlainText("cat\ncat\ncat")
    editor.setFocus()

    def click(line, alt=True):
        block = editor.document().findBlockByNumber(line)
        cursor = QTextCursor(block)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        point = editor.cursorRect(cursor).center()
        modifier = Qt.KeyboardModifier.AltModifier if alt else Qt.KeyboardModifier.NoModifier
        QTest.mouseClick(editor.viewport(), Qt.MouseButton.LeftButton, modifier, point)

    click(0, alt=False)
    click(1)
    click(2)
    assert len(editor.extra_cursors) == 2
    QTest.keyClicks(editor, "s!")
    assert editor.toPlainText() == "cats!\ncats!\ncats!"
    QTest.keyClick(editor, Qt.Key.Key_Backspace)
    QTest.keyClick(editor, Qt.Key.Key_Home)
    QTest.keyClicks(editor, "a ")
    assert editor.toPlainText() == "a cats\na cats\na cats"
    editor.undo()  # one undo per keystroke, at every caret
    assert editor.toPlainText() == "a cats\na cats\na cats".replace("a ", "a", 3)
    QTest.keyClick(editor, Qt.Key.Key_Escape)
    assert editor.extra_cursors == []
    QTest.keyClicks(editor, "x")
    assert editor.toPlainText().count("x") == 1


def test_alt_shift_click_adds_and_removes_carets(editor):
    # Many Linux window managers (Xfce, KDE before Plasma 6) take Alt+click to move windows,
    # so Alt+Shift+click (the JetBrains convention) does the same everywhere.
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QTextCursor
    from PySide6.QtTest import QTest

    editor.setPlainText("one\ntwo")
    editor.setFocus()
    alt_shift = Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier

    def point(line):
        cursor = QTextCursor(editor.document().findBlockByNumber(line))
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        return editor.cursorRect(cursor).center()

    QTest.mouseClick(
        editor.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point(0)
    )
    QTest.mouseClick(editor.viewport(), Qt.MouseButton.LeftButton, alt_shift, point(1))
    assert len(editor.extra_cursors) == 1
    assert not editor.textCursor().hasSelection()  # not a Shift+click selection
    QTest.keyClicks(editor, "!")
    assert editor.toPlainText() == "one!\ntwo!"
    QTest.mouseClick(editor.viewport(), Qt.MouseButton.LeftButton, alt_shift, point(0))
    assert editor.extra_cursors == []  # again on the other caret takes it away


def test_find_bar_counts_steps_and_replaces(editor):
    from PySide6.QtWidgets import QApplication

    from zettelapp.ui.findbar import FindBar

    editor.setPlainText("Rosa rosa ROSA\nrosae")
    bar = FindBar(editor)
    bar.show()
    bar.find.setText("rosa")
    QApplication.processEvents()
    assert len(bar.matches()) == 4  # case doesn't matter, and part of a word counts
    assert bar.count.text() == "1 of 4"
    bar.next()
    assert bar.count.text() == "2 of 4"
    bar.previous()
    bar.previous()  # wraps around
    assert bar.count.text() == "4 of 4"
    bar.case.setChecked(True)
    assert len(bar.matches()) == 2
    bar.replacement.setText("lupa")
    assert bar.replace_all() == 2
    assert editor.toPlainText() == "Rosa lupa ROSA\nlupae"
    editor.undo()  # one undo takes back every replacement
    assert editor.toPlainText() == "Rosa rosa ROSA\nrosae"
    bar.close_bar()
    assert bar.isHidden()


def test_tab_goes_from_the_search_straight_to_the_replacement(editor):
    from PySide6.QtWidgets import QApplication

    from zettelapp.ui.findbar import FindBar

    bar = FindBar(editor)
    bar.open(replace=True)
    QApplication.processEvents()
    assert bar.find.nextInFocusChain() is bar.replacement


def test_alt_click_on_the_caret_just_added_takes_it_away(editor):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QTextCursor
    from PySide6.QtTest import QTest

    editor.setPlainText("one\ntwo")
    editor.setFocus()
    cursor = QTextCursor(editor.document().findBlockByNumber(1))
    point = editor.cursorRect(cursor).center()
    alt = Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier
    QTest.mouseClick(editor.viewport(), Qt.MouseButton.LeftButton, alt, point)
    assert len(editor.extra_cursors) == 1
    QTest.mouseClick(editor.viewport(), Qt.MouseButton.LeftButton, alt, point)
    assert editor.extra_cursors == [] and editor.textCursor().position() == 0
