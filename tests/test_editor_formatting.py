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
